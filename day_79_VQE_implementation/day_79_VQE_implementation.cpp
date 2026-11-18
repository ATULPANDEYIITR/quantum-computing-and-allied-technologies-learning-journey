#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * C++17 Variational Quantum Eigensolver
 *
 * Application:
 * Molecular hydrogen ground-state energy estimation.
 *
 * Architecture:
 * Pauli Hamiltonian
 *     -> Statevector simulator
 *     -> Variational ansatz
 *     -> Energy evaluator
 *     -> Gradient optimizer
 *     -> Merge-free scientific result validation
 *
 * No external dependencies.
 */

using Complex = std::complex<double>;
using State = std::array<Complex, 4>;
using Parameters = std::array<double, 2>;

constexpr double PI = 3.14159265358979323846;
constexpr double TOLERANCE = 1e-9;

enum class Pauli {
    I, X, Y, Z
};

enum class ExperimentStatus {
    Created,
    Running,
    Completed,
    Failed
};

struct PauliTerm {
    double coefficient;
    std::array<Pauli, 2> operators;
};

struct IterationRecord {
    int iteration;
    double energy;
    double gradientNorm;
    Parameters parameters;
};

struct OptimizationResult {
    Parameters parameters;
    std::vector<IterationRecord> history;
    bool converged = false;
};

void validateFinite(double value, const std::string& name) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(name + " must be finite.");
    }
}

class MolecularHamiltonian {
private:
    std::vector<PauliTerm> terms;

    static Pauli parsePauli(char symbol) {
        switch (symbol) {
            case 'I': return Pauli::I;
            case 'X': return Pauli::X;
            case 'Y': return Pauli::Y;
            case 'Z': return Pauli::Z;
            default:
                throw std::invalid_argument("Invalid Pauli symbol.");
        }
    }

public:
    explicit MolecularHamiltonian(
        const std::vector<std::pair<double, std::string>>& input
    ) {
        if (input.empty()) {
            throw std::invalid_argument("Hamiltonian cannot be empty.");
        }

        for (const auto& entry : input) {
            validateFinite(entry.first, "Hamiltonian coefficient");

            if (entry.second.size() != 2) {
                throw std::invalid_argument(
                    "This implementation requires two-qubit operators."
                );
            }

            terms.push_back({
                entry.first,
                {
                    parsePauli(entry.second[0]),
                    parsePauli(entry.second[1])
                }
            });
        }
    }

    static Complex pauliElement(Pauli p, int row, int column) {
        switch (p) {
            case Pauli::I:
                return row == column ? Complex(1, 0) : Complex(0, 0);

            case Pauli::X:
                return row != column ? Complex(1, 0) : Complex(0, 0);

            case Pauli::Y:
                if (row == 0 && column == 1) return Complex(0, -1);
                if (row == 1 && column == 0) return Complex(0, 1);
                return Complex(0, 0);

            case Pauli::Z:
                return row == column
                    ? Complex(row == 0 ? 1 : -1, 0)
                    : Complex(0, 0);
        }

        throw std::logic_error("Unsupported Pauli operator.");
    }

    State applyPauli(
        const State& state,
        const std::array<Pauli, 2>& operators
    ) const {
        State result{};

        for (int row = 0; row < 4; ++row) {
            for (int column = 0; column < 4; ++column) {
                const int row0 = (row >> 1) & 1;
                const int row1 = row & 1;
                const int col0 = (column >> 1) & 1;
                const int col1 = column & 1;

                const Complex first = pauliElement(
                    operators[0], row0, col0
                );

                const Complex second = pauliElement(
                    operators[1], row1, col1
                );

                result[row] += first * second * state[column];
            }
        }

        return result;
    }

    double energy(const State& state) const {
        Complex total(0, 0);

        for (const auto& term : terms) {
            const State transformed = applyPauli(
                state,
                term.operators
            );

            Complex expectation(0, 0);

            for (int i = 0; i < 4; ++i) {
                expectation += std::conj(state[i]) * transformed[i];
            }

            total += term.coefficient * expectation;
        }

        if (std::abs(total.imag()) > 1e-8) {
            throw std::runtime_error(
                "Hamiltonian expectation is not real."
            );
        }

        return total.real();
    }

    std::array<std::array<double, 4>, 4> matrix() const {
        std::array<std::array<double, 4>, 4> result{};

        for (const auto& term : terms) {
            for (int row = 0; row < 4; ++row) {
                for (int column = 0; column < 4; ++column) {
                    const int r0 = (row >> 1) & 1;
                    const int r1 = row & 1;
                    const int c0 = (column >> 1) & 1;
                    const int c1 = column & 1;

                    const Complex value =
                        pauliElement(term.operators[0], r0, c0) *
                        pauliElement(term.operators[1], r1, c1);

                    if (std::abs(value.imag()) > 1e-10) {
                        throw std::runtime_error(
                            "Unexpected imaginary matrix element."
                        );
                    }

                    result[row][column] +=
                        term.coefficient * value.real();
                }
            }
        }

        return result;
    }

    double exactGroundEnergy() const {
        // Symmetric Jacobi diagonalization for a real symmetric 4x4 matrix.
        auto a = matrix();

        constexpr int dimension = 4;
        constexpr int maximumSweeps = 1000;

        for (int sweep = 0; sweep < maximumSweeps; ++sweep) {
            int p = 0;
            int q = 1;
            double largest = 0.0;

            for (int i = 0; i < dimension; ++i) {
                for (int j = i + 1; j < dimension; ++j) {
                    if (std::abs(a[i][j]) > largest) {
                        largest = std::abs(a[i][j]);
                        p = i;
                        q = j;
                    }
                }
            }

            if (largest < 1e-14) {
                break;
            }

            const double angle = 0.5 * std::atan2(
                2.0 * a[p][q],
                a[q][q] - a[p][p]
            );

            const double c = std::cos(angle);
            const double s = std::sin(angle);

            const double app = a[p][p];
            const double aqq = a[q][q];
            const double apq = a[p][q];

            a[p][p] = c * c * app - 2 * s * c * apq + s * s * aqq;
            a[q][q] = s * s * app + 2 * s * c * apq + c * c * aqq;
            a[p][q] = 0;
            a[q][p] = 0;

            for (int k = 0; k < dimension; ++k) {
                if (k == p || k == q) continue;

                const double akp = a[k][p];
                const double akq = a[k][q];

                a[k][p] = c * akp - s * akq;
                a[p][k] = a[k][p];

                a[k][q] = s * akp + c * akq;
                a[q][k] = a[k][q];
            }
        }

        double minimum = a[0][0];

        for (int i = 1; i < dimension; ++i) {
            minimum = std::min(minimum, a[i][i]);
        }

        return minimum;
    }
};

class QuantumCircuit {
public:
    static State initialState() {
        State state{};
        state[0] = Complex(1, 0);
        return state;
    }

    static State applyRY(
        const State& state,
        double theta,
        int qubit
    ) {
        validateFinite(theta, "Rotation angle");

        if (qubit < 0 || qubit > 1) {
            throw std::out_of_range("Invalid qubit index.");
        }

        const double c = std::cos(theta / 2);
        const double s = std::sin(theta / 2);

        State output = state;

        for (int index = 0; index < 4; ++index) {
            const int bitPosition = 1 - qubit;

            if ((index & (1 << bitPosition)) != 0) {
                continue;
            }

            const int partner = index | (1 << bitPosition);

            output[index] = c * state[index] - s * state[partner];
            output[partner] = s * state[index] + c * state[partner];
        }

        return output;
    }

    static State applyCNOT(
        const State& state,
        int control,
        int target
    ) {
        if (control < 0 || control > 1 ||
            target < 0 || target > 1 ||
            control == target) {
            throw std::invalid_argument("Invalid CNOT configuration.");
        }

        State output{};

        for (int index = 0; index < 4; ++index) {
            int destination = index;

            if ((index & (1 << (1 - control))) != 0) {
                destination ^= 1 << (1 - target);
            }

            output[destination] = state[index];
        }

        return output;
    }

    static State prepare(const Parameters& parameters) {
        for (double parameter : parameters) {
            validateFinite(parameter, "Circuit parameter");
        }

        State state = initialState();

        state = applyRY(state, parameters[0], 0);
        state = applyRY(state, parameters[1], 1);
        state = applyCNOT(state, 0, 1);

        return state;
    }
};

class VariationalObjective {
private:
    const MolecularHamiltonian& hamiltonian;

public:
    explicit VariationalObjective(
        const MolecularHamiltonian& h
    ) : hamiltonian(h) {}

    double evaluate(const Parameters& parameters) const {
        return hamiltonian.energy(
            QuantumCircuit::prepare(parameters)
        );
    }

    Parameters gradient(const Parameters& parameters) const {
        Parameters result{};

        for (int i = 0; i < 2; ++i) {
            Parameters positive = parameters;
            Parameters negative = parameters;

            positive[i] += PI / 2;
            negative[i] -= PI / 2;

            result[i] = 0.5 * (
                evaluate(positive) - evaluate(negative)
            );
        }

        return result;
    }
};

class AdamOptimizer {
private:
    double learningRate;
    double beta1;
    double beta2;
    double epsilon;

public:
    explicit AdamOptimizer(
        double lr = 0.05,
        double b1 = 0.9,
        double b2 = 0.999,
        double eps = 1e-8
    ) : learningRate(lr), beta1(b1), beta2(b2), epsilon(eps) {
        if (lr <= 0 || b1 <= 0 || b1 >= 1 ||
            b2 <= 0 || b2 >= 1 || eps <= 0) {
            throw std::invalid_argument("Invalid Adam configuration.");
        }
    }

    OptimizationResult minimize(
        const VariationalObjective& objective,
        Parameters parameters,
        int maximumIterations,
        double tolerance
    ) const {
        if (maximumIterations <= 0 || tolerance <= 0) {
            throw std::invalid_argument("Invalid optimization limits.");
        }

        Parameters first{0, 0};
        Parameters second{0, 0};

        OptimizationResult result;
        result.parameters = parameters;

        double previousEnergy = objective.evaluate(parameters);

        for (int iteration = 1;
             iteration <= maximumIterations;
             ++iteration) {

            const Parameters gradient = objective.gradient(parameters);

            const double gradientNorm = std::hypot(
                gradient[0], gradient[1]
            );

            for (int i = 0; i < 2; ++i) {
                first[i] = beta1 * first[i] +
                    (1 - beta1) * gradient[i];

                second[i] = beta2 * second[i] +
                    (1 - beta2) * gradient[i] * gradient[i];

                const double m = first[i] /
                    (1 - std::pow(beta1, iteration));

                const double v = second[i] /
                    (1 - std::pow(beta2, iteration));

                parameters[i] -= learningRate * m /
                    (std::sqrt(v) + epsilon);

                parameters[i] = std::remainder(
                    parameters[i], 2 * PI
                );
            }

            const double currentEnergy = objective.evaluate(parameters);

            if (!std::isfinite(currentEnergy)) {
                throw std::runtime_error("Non-finite energy.");
            }

            result.history.push_back({
                iteration,
                currentEnergy,
                gradientNorm,
                parameters
            });

            if (gradientNorm < tolerance &&
                std::abs(currentEnergy - previousEnergy) < tolerance) {
                result.converged = true;
                break;
            }

            previousEnergy = currentEnergy;
        }

        result.parameters = parameters;

        return result;
    }
};

class RepositoryIndependentExperiment {
private:
    const MolecularHamiltonian& hamiltonian;
    ExperimentStatus status = ExperimentStatus::Created;

public:
    explicit RepositoryIndependentExperiment(
        const MolecularHamiltonian& h
    ) : hamiltonian(h) {}

    void run() {
        if (status != ExperimentStatus::Created) {
            throw std::logic_error("Experiment cannot be started twice.");
        }

        status = ExperimentStatus::Running;

        try {
            VariationalObjective objective(hamiltonian);
            AdamOptimizer optimizer;

            const Parameters initial{0.2, -0.4};

            OptimizationResult result = optimizer.minimize(
                objective,
                initial,
                2000,
                TOLERANCE
            );

            const double optimizedEnergy =
                objective.evaluate(result.parameters);

            const double exactEnergy =
                hamiltonian.exactGroundEnergy();

            const State finalState =
                QuantumCircuit::prepare(result.parameters);

            double probabilitySum = 0;

            for (const Complex& amplitude : finalState) {
                probabilitySum += std::norm(amplitude);
            }

            if (std::abs(probabilitySum - 1.0) > 1e-9) {
                throw std::runtime_error("State normalization failed.");
            }

            status = ExperimentStatus::Completed;

            std::cout << std::fixed << std::setprecision(12);

            std::cout << "\n========== C++17 VQE ==========\n";
            std::cout << "Molecule: H2\n";
            std::cout << "Optimized energy: " << optimizedEnergy << " Ha\n";
            std::cout << "Exact energy:     " << exactEnergy << " Ha\n";
            std::cout << "Absolute error:   "
                      << std::abs(optimizedEnergy - exactEnergy)
                      << " Ha\n";

            std::cout << "Parameters: "
                      << result.parameters[0] << ", "
                      << result.parameters[1] << "\n";

            std::cout << "Iterations: "
                      << result.history.size() << "\n";

            std::cout << "Converged: "
                      << std::boolalpha << result.converged << "\n";

            std::cout << "\nOptimization history:\n";

            const std::size_t step = std::max(
                std::size_t(1),
                result.history.size() / 10
            );

            for (std::size_t i = 0; i < result.history.size(); i += step) {
                const auto& record = result.history[i];

                std::cout << record.iteration
                          << " | " << record.energy
                          << " | gradient: " << record.gradientNorm
                          << "\n";
            }

        } catch (...) {
            status = ExperimentStatus::Failed;
            throw;
        }
    }

    ExperimentStatus getStatus() const {
        return status;
    }
};

int main() {
    try {
        MolecularHamiltonian hamiltonian({
            {-1.052373245772859, "II"},
            {0.39793742484318045, "ZI"},
            {-0.39793742484318045, "IZ"},
            {-0.01128010425623538, "ZZ"},
            {0.18093119978423156, "XX"}
        });

        const double exact = hamiltonian.exactGroundEnergy();

        if (!std::isfinite(exact)) {
            throw std::runtime_error("Exact diagonalization failed.");
        }

        RepositoryIndependentExperiment experiment(hamiltonian);
        experiment.run();

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "VQE failure: " << error.what() << "\n";
        return 1;
    }
}
