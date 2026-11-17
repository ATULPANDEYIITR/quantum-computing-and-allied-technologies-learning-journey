#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Variational Quantum Eigensolver
 * C++17 implementation.
 *
 * Includes:
 * - Pauli Hamiltonian domain model
 * - Statevector representation
 * - Variational Ry circuit
 * - Parameter-shift gradient
 * - Finite-shot measurement
 * - Gradient-descent optimizer
 * - Convergence monitoring
 * - Experiment reporting
 */

namespace vqe {

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 1e-10;

enum class Pauli {
    Identity,
    X,
    Y,
    Z
};

enum class ExperimentStatus {
    Created,
    Running,
    Completed,
    Failed
};

std::string toString(Pauli pauli) {
    switch (pauli) {
        case Pauli::Identity: return "I";
        case Pauli::X: return "X";
        case Pauli::Y: return "Y";
        case Pauli::Z: return "Z";
    }

    throw std::invalid_argument("Unknown Pauli operator.");
}

std::string toString(ExperimentStatus status) {
    switch (status) {
        case ExperimentStatus::Created: return "CREATED";
        case ExperimentStatus::Running: return "RUNNING";
        case ExperimentStatus::Completed: return "COMPLETED";
        case ExperimentStatus::Failed: return "FAILED";
    }

    return "UNKNOWN";
}

struct Complex {
    double real = 0.0;
    double imag = 0.0;

    double norm() const {
        return real * real + imag * imag;
    }
};

struct Statevector {
    Complex alpha;
    Complex beta;

    void validate() const {
        const double probability = alpha.norm() + beta.norm();

        if (std::abs(probability - 1.0) > 1e-8) {
            throw std::runtime_error(
                "Quantum state is not normalized."
            );
        }
    }
};

struct PauliTerm {
    double coefficient;
    Pauli observable;

    PauliTerm(double c, Pauli p)
        : coefficient(c), observable(p) {

        if (!std::isfinite(c)) {
            throw std::invalid_argument(
                "Hamiltonian coefficient must be finite."
            );
        }
    }
};

struct ExperimentConfig {
    double learningRate = 0.15;
    double tolerance = 1e-10;
    int maxIterations = 300;
    int shots = 0;
    double initialTheta = 0.5;
    unsigned int seed = 42;

    void validate() const {
        if (learningRate <= 0.0 ||
            !std::isfinite(learningRate)) {
            throw std::invalid_argument(
                "Learning rate must be positive."
            );
        }

        if (maxIterations <= 0) {
            throw std::invalid_argument(
                "Iteration count must be positive."
            );
        }

        if (tolerance <= 0.0 || shots < 0) {
            throw std::invalid_argument(
                "Invalid optimization configuration."
            );
        }
    }
};

struct IterationRecord {
    int iteration;
    double theta;
    double energy;
    double gradient;
};

class QuantumCircuit {
public:
    static Statevector ry(double theta) {
        if (!std::isfinite(theta)) {
            throw std::invalid_argument(
                "Circuit parameter must be finite."
            );
        }

        Statevector state{
            {std::cos(theta / 2.0), 0.0},
            {std::sin(theta / 2.0), 0.0}
        };

        state.validate();
        return state;
    }
};

class PauliMeasurement {
public:
    static double expectation(
        const Statevector& state,
        Pauli observable
    ) {
        state.validate();

        const double a = state.alpha.real;
        const double b = state.beta.real;

        switch (observable) {
            case Pauli::Identity:
                return 1.0;

            case Pauli::X:
                return 2.0 * (
                    a * b +
                    state.alpha.imag * state.beta.imag
                );

            case Pauli::Y:
                return 2.0 * (
                    state.alpha.imag * b -
                    a * state.beta.imag
                );

            case Pauli::Z:
                return state.alpha.norm() -
                       state.beta.norm();
        }

        throw std::invalid_argument(
            "Unsupported observable."
        );
    }
};

class Hamiltonian {
private:
    std::vector<PauliTerm> terms;

public:
    explicit Hamiltonian(std::vector<PauliTerm> input)
        : terms(std::move(input)) {

        if (terms.empty()) {
            throw std::invalid_argument(
                "Hamiltonian cannot be empty."
            );
        }
    }

    const std::vector<PauliTerm>& getTerms() const {
        return terms;
    }

    double expectation(const Statevector& state) const {
        double energy = 0.0;

        for (const auto& term : terms) {
            energy += term.coefficient *
                PauliMeasurement::expectation(
                    state,
                    term.observable
                );
        }

        return energy;
    }

    double exactGroundEnergy() const {
        double identity = 0.0;
        double x = 0.0;
        double y = 0.0;
        double z = 0.0;

        for (const auto& term : terms) {
            switch (term.observable) {
                case Pauli::Identity:
                    identity += term.coefficient;
                    break;
                case Pauli::X:
                    x += term.coefficient;
                    break;
                case Pauli::Y:
                    y += term.coefficient;
                    break;
                case Pauli::Z:
                    z += term.coefficient;
                    break;
            }
        }

        return identity - std::sqrt(
            x * x + y * y + z * z
        );
    }
};

class MeasurementService {
private:
    std::mt19937 generator;

public:
    explicit MeasurementService(unsigned int seed)
        : generator(seed) {}

    double measure(double expectation, int shots) {
        if (shots <= 0) {
            throw std::invalid_argument(
                "Shots must be positive."
            );
        }

        if (expectation < -1.0 || expectation > 1.0) {
            throw std::invalid_argument(
                "Invalid measurement expectation."
            );
        }

        std::bernoulli_distribution distribution(
            (1.0 + expectation) / 2.0
        );

        int positive = 0;

        for (int i = 0; i < shots; ++i) {
            positive += distribution(generator) ? 1 : 0;
        }

        return 2.0 * positive / shots - 1.0;
    }
};

class VQEOptimizer {
private:
    const Hamiltonian& hamiltonian;
    ExperimentConfig config;
    MeasurementService measurement;
    ExperimentStatus status = ExperimentStatus::Created;
    std::vector<IterationRecord> history;

    double evaluate(double theta, bool noisy = false) {
        const Statevector state = QuantumCircuit::ry(theta);

        if (!noisy || config.shots == 0) {
            return hamiltonian.expectation(state);
        }

        double energy = 0.0;

        for (const auto& term : hamiltonian.getTerms()) {
            const double expected =
                PauliMeasurement::expectation(
                    state,
                    term.observable
                );

            energy += term.coefficient *
                measurement.measure(expected, config.shots);
        }

        return energy;
    }

    double gradient(double theta) {
        const double shift = PI / 2.0;

        return (
            evaluate(theta + shift) -
            evaluate(theta - shift)
        ) / 2.0;
    }

public:
    VQEOptimizer(
        const Hamiltonian& h,
        ExperimentConfig c
    )
        : hamiltonian(h),
          config(c),
          measurement(c.seed) {

        config.validate();
    }

    IterationRecord optimize() {
        if (status != ExperimentStatus::Created) {
            throw std::runtime_error(
                "Experiment cannot be executed twice."
            );
        }

        status = ExperimentStatus::Running;

        try {
            double theta = config.initialTheta;

            for (int i = 0;
                 i < config.maxIterations;
                 ++i) {

                const double energy = evaluate(
                    theta,
                    config.shots > 0
                );

                const double grad = gradient(theta);

                history.push_back({
                    i,
                    theta,
                    energy,
                    grad
                });

                if (std::abs(grad) < config.tolerance) {
                    break;
                }

                theta -= config.learningRate * grad;

                // Rotations are periodic modulo 2*pi.
                theta = std::remainder(theta, 2.0 * PI);
            }

            status = ExperimentStatus::Completed;

            return {
                static_cast<int>(history.size()),
                theta,
                evaluate(theta),
                gradient(theta)
            };

        } catch (...) {
            status = ExperimentStatus::Failed;
            throw;
        }
    }

    void printReport(const IterationRecord& result) const {
        if (status != ExperimentStatus::Completed) {
            throw std::runtime_error(
                "Cannot report an incomplete experiment."
            );
        }

        const double exact =
            hamiltonian.exactGroundEnergy();

        std::cout << std::fixed << std::setprecision(12);

        std::cout << "\nVARIATIONAL QUANTUM EIGENSOLVER\n";
        std::cout << "====================================\n";

        std::cout << "Status: "
                  << toString(status) << '\n';

        std::cout << "Iterations: "
                  << history.size() << '\n';

        std::cout << "Optimized parameter: "
                  << result.theta << '\n';

        std::cout << "Final energy: "
                  << result.energy << '\n';

        std::cout << "Exact ground energy: "
                  << exact << '\n';

        std::cout << "Absolute error: "
                  << std::abs(result.energy - exact) << '\n';

        std::cout << "Hamiltonian:\n";

        for (const auto& term : hamiltonian.getTerms()) {
            std::cout << "  "
                      << term.coefficient
                      << " * "
                      << toString(term.observable)
                      << '\n';
        }
    }

    const std::vector<IterationRecord>& getHistory() const {
        return history;
    }
};

void runTests() {
    const Statevector state = QuantumCircuit::ry(PI / 2.0);

    if (std::abs(
        PauliMeasurement::expectation(state, Pauli::X) - 1.0
    ) > EPSILON) {
        throw std::runtime_error("X expectation test failed.");
    }

    Hamiltonian h({
        {-1.0, Pauli::Z},
        {-0.5, Pauli::X}
    });

    if (std::abs(
        h.exactGroundEnergy() + std::sqrt(1.25)
    ) > EPSILON) {
        throw std::runtime_error("Ground-state test failed.");
    }
}

} // namespace vqe

int main() {
    try {
        vqe::runTests();

        vqe::Hamiltonian hamiltonian({
            {-1.0, vqe::Pauli::Z},
            {-0.5, vqe::Pauli::X}
        });

        vqe::ExperimentConfig config;
        config.learningRate = 0.15;
        config.maxIterations = 300;
        config.initialTheta = 0.5;
        config.shots = 0;

        vqe::VQEOptimizer optimizer(
            hamiltonian,
            config
        );

        const auto result = optimizer.optimize();

        optimizer.printReport(result);

        // Save optimization history for reproducibility.
        std::ofstream output("vqe_history.csv");

        if (!output) {
            throw std::runtime_error(
                "Cannot open output report."
            );
        }

        output << "iteration,theta,energy,gradient\n";

        output << std::setprecision(15);

        for (const auto& record : optimizer.getHistory()) {
            output << record.iteration << ','
                   << record.theta << ','
                   << record.energy << ','
                   << record.gradient << '\n';
        }

        output.close();

        if (!output) {
            throw std::runtime_error(
                "Failed while writing experiment history."
            );
        }

        std::cout << "\nHistory saved to vqe_history.csv\n";

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "VQE failure: "
                  << error.what() << '\n';

        return 1;
    }
}
