/*
 * Quantum Generative Models
 * C++17 Quantum Born Machine and Generative Learning Engine.
 *
 * Implements:
 * - Complex statevector simulation
 * - Parameterized rotation circuits
 * - Entanglement through CNOT
 * - Born probability distributions
 * - SPSA optimization
 * - Measurement sampling
 * - Distribution evaluation
 * - Experiment governance
 *
 * Compile:
 * g++ -std=c++17 -O2 quantum_generative.cpp -o quantum_generative
 */

#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace qgm {

constexpr double EPSILON = 1e-12;
constexpr double PI = 3.14159265358979323846;

enum class ExperimentStatus {
    Created,
    Training,
    Completed,
    Failed
};

std::string statusName(ExperimentStatus status) {
    switch (status) {
        case ExperimentStatus::Created: return "CREATED";
        case ExperimentStatus::Training: return "TRAINING";
        case ExperimentStatus::Completed: return "COMPLETED";
        case ExperimentStatus::Failed: return "FAILED";
    }

    return "UNKNOWN";
}

struct ModelConfig {
    std::size_t qubits = 2;
    double learningRate = 0.08;
    std::size_t iterations = 300;
    std::size_t shots = 5000;
    unsigned int seed = 42;

    void validate() const {
        if (qubits < 1 || qubits > 12) {
            throw std::invalid_argument("Qubit count must be 1-12.");
        }

        if (!std::isfinite(learningRate) || learningRate <= 0) {
            throw std::invalid_argument("Invalid learning rate.");
        }

        if (iterations == 0 || shots == 0) {
            throw std::invalid_argument(
                "Iterations and shots must be positive."
            );
        }
    }
};

struct TrainingRecord {
    std::size_t iteration;
    double loss;
    double learningRate;
};

struct Evaluation {
    double klDivergence;
    double totalVariation;
    double entropy;
    std::vector<double> probabilities;
};

class QuantumCircuit {
private:
    std::size_t qubits_;
    std::size_t dimension_;

    void applyRY(
        std::vector<std::complex<double>>& state,
        std::size_t qubit,
        double theta
    ) const {
        if (qubit >= qubits_) {
            throw std::invalid_argument("Invalid qubit index.");
        }

        const std::size_t mask =
            std::size_t(1) << (qubits_ - 1 - qubit);

        const double c = std::cos(theta / 2.0);
        const double s = std::sin(theta / 2.0);

        for (std::size_t i = 0; i < dimension_; ++i) {
            if (i & mask) continue;

            const std::size_t j = i | mask;

            const auto a = state[i];
            const auto b = state[j];

            state[i] = c * a - s * b;
            state[j] = s * a + c * b;
        }
    }

    void applyCNOT(
        std::vector<std::complex<double>>& state,
        std::size_t control,
        std::size_t target
    ) const {
        if (control >= qubits_ ||
            target >= qubits_ ||
            control == target) {
            throw std::invalid_argument("Invalid CNOT gate.");
        }

        const std::size_t controlMask =
            std::size_t(1) << (qubits_ - 1 - control);

        const std::size_t targetMask =
            std::size_t(1) << (qubits_ - 1 - target);

        for (std::size_t i = 0; i < dimension_; ++i) {
            if ((i & controlMask) && !(i & targetMask)) {
                std::swap(state[i], state[i | targetMask]);
            }
        }
    }

public:
    explicit QuantumCircuit(std::size_t qubits)
        : qubits_(qubits),
          dimension_(std::size_t(1) << qubits) {
        if (qubits < 1 || qubits > 12) {
            throw std::invalid_argument("Unsupported qubit count.");
        }
    }

    std::size_t qubits() const {
        return qubits_;
    }

    std::size_t dimension() const {
        return dimension_;
    }

    std::vector<double> execute(
        const std::vector<double>& parameters
    ) const {
        if (parameters.size() != 2 * qubits_) {
            throw std::invalid_argument(
                "Incorrect parameter count."
            );
        }

        for (double parameter : parameters) {
            if (!std::isfinite(parameter)) {
                throw std::invalid_argument(
                    "Non-finite circuit parameter."
                );
            }
        }

        std::vector<std::complex<double>> state(
            dimension_, {0.0, 0.0}
        );

        state[0] = {1.0, 0.0};

        for (std::size_t q = 0; q < qubits_; ++q) {
            applyRY(state, q, parameters[q]);
        }

        for (std::size_t q = 0; q + 1 < qubits_; ++q) {
            applyCNOT(state, q, q + 1);
        }

        for (std::size_t q = 0; q < qubits_; ++q) {
            applyRY(state, q, parameters[qubits_ + q]);
        }

        std::vector<double> probabilities(dimension_);

        for (std::size_t i = 0; i < dimension_; ++i) {
            probabilities[i] = std::norm(state[i]);
        }

        const double total = std::accumulate(
            probabilities.begin(),
            probabilities.end(),
            0.0
        );

        if (!std::isfinite(total) || total <= EPSILON) {
            throw std::runtime_error("State normalization failed.");
        }

        for (double& probability : probabilities) {
            probability /= total;
        }

        return probabilities;
    }
};

class BornMachine {
private:
    ModelConfig config_;
    QuantumCircuit circuit_;
    std::vector<double> parameters_;
    std::mt19937 generator_;
    std::vector<TrainingRecord> history_;

    static double normalizeAngle(double value) {
        value = std::fmod(value + PI, 2.0 * PI);

        if (value < 0) value += 2.0 * PI;

        return value - PI;
    }

public:
    explicit BornMachine(const ModelConfig& config)
        : config_(config),
          circuit_(config.qubits),
          generator_(config.seed) {
        config_.validate();

        std::uniform_real_distribution<double> distribution(
            -0.8, 0.8
        );

        parameters_.resize(2 * config_.qubits);

        for (double& parameter : parameters_) {
            parameter = distribution(generator_);
        }
    }

    static std::vector<double> validateDistribution(
        const std::vector<double>& target
    ) {
        if (target.empty()) {
            throw std::invalid_argument("Empty target distribution.");
        }

        double total = 0.0;

        for (double probability : target) {
            if (!std::isfinite(probability) || probability < 0) {
                throw std::invalid_argument(
                    "Invalid target probability."
                );
            }

            total += probability;
        }

        if (total <= EPSILON) {
            throw std::invalid_argument("Zero probability mass.");
        }

        std::vector<double> normalized = target;

        for (double& probability : normalized) {
            probability /= total;
        }

        return normalized;
    }

    std::vector<double> probabilities() const {
        return circuit_.execute(parameters_);
    }

    static double klDivergence(
        const std::vector<double>& target,
        const std::vector<double>& generated
    ) {
        if (target.size() != generated.size()) {
            throw std::invalid_argument("Dimension mismatch.");
        }

        double result = 0.0;

        for (std::size_t i = 0; i < target.size(); ++i) {
            if (target[i] > 0) {
                result += target[i] * std::log(
                    target[i] /
                    std::max(generated[i], EPSILON)
                );
            }
        }

        return result;
    }

    static double totalVariation(
        const std::vector<double>& target,
        const std::vector<double>& generated
    ) {
        double distance = 0.0;

        for (std::size_t i = 0; i < target.size(); ++i) {
            distance += std::abs(
                target[i] - generated[i]
            );
        }

        return distance / 2.0;
    }

    double loss(const std::vector<double>& target) const {
        return klDivergence(target, probabilities());
    }

    void train(
        const std::vector<double>& rawTarget,
        std::size_t iterations
    ) {
        const auto target = validateDistribution(rawTarget);

        if (target.size() != circuit_.dimension()) {
            throw std::invalid_argument(
                "Target dimension must equal 2^qubits."
            );
        }

        if (iterations == 0) {
            throw std::invalid_argument("Iterations must be positive.");
        }

        history_.clear();

        constexpr double alpha = 0.602;
        constexpr double gamma = 0.101;
        constexpr double stability = 10.0;

        std::uniform_int_distribution<int> signDistribution(0, 1);

        for (std::size_t iteration = 0;
             iteration < iterations;
             ++iteration) {

            const double ak = config_.learningRate /
                std::pow(iteration + 1 + stability, alpha);

            const double ck = 0.12 /
                std::pow(iteration + 1, gamma);

            const auto original = parameters_;

            std::vector<double> delta(parameters_.size());

            for (double& value : delta) {
                value = signDistribution(generator_) == 0
                    ? -1.0 : 1.0;
            }

            for (std::size_t i = 0; i < parameters_.size(); ++i) {
                parameters_[i] = original[i] + ck * delta[i];
            }

            const double plus = loss(target);

            for (std::size_t i = 0; i < parameters_.size(); ++i) {
                parameters_[i] = original[i] - ck * delta[i];
            }

            const double minus = loss(target);

            const double gradientScale =
                (plus - minus) / (2.0 * ck);

            for (std::size_t i = 0; i < parameters_.size(); ++i) {
                parameters_[i] = normalizeAngle(
                    original[i] -
                    ak * gradientScale / delta[i]
                );
            }

            const double currentLoss = loss(target);

            if (!std::isfinite(currentLoss)) {
                throw std::runtime_error("Training diverged.");
            }

            history_.push_back({
                iteration + 1,
                currentLoss,
                ak
            });
        }
    }

    std::vector<std::size_t> sample(std::size_t shots) {
        if (shots == 0) {
            throw std::invalid_argument("Shots must be positive.");
        }

        const auto distribution = probabilities();

        std::discrete_distribution<std::size_t> measurement(
            distribution.begin(),
            distribution.end()
        );

        std::vector<std::size_t> counts(
            circuit_.dimension(), 0
        );

        for (std::size_t i = 0; i < shots; ++i) {
            ++counts[measurement(generator_)];
        }

        return counts;
    }

    Evaluation evaluate(
        const std::vector<double>& rawTarget
    ) const {
        const auto target = validateDistribution(rawTarget);
        const auto generated = probabilities();

        if (target.size() != generated.size()) {
            throw std::invalid_argument("Dimension mismatch.");
        }

        double entropy = 0.0;

        for (double probability : generated) {
            if (probability > EPSILON) {
                entropy -= probability * std::log2(probability);
            }
        }

        return {
            klDivergence(target, generated),
            totalVariation(target, generated),
            entropy,
            generated
        };
    }

    const std::vector<TrainingRecord>& history() const {
        return history_;
    }

    const std::vector<double>& parameters() const {
        return parameters_;
    }

    const ModelConfig& config() const {
        return config_;
    }
};

class Experiment {
private:
    std::string id_;
    ExperimentStatus status_;
    BornMachine& model_;

public:
    Experiment(std::string id, BornMachine& model)
        : id_(std::move(id)),
          status_(ExperimentStatus::Created),
          model_(model) {
        if (id_.empty()) {
            throw std::invalid_argument("Experiment ID is required.");
        }
    }

    Evaluation execute(
        const std::vector<double>& target,
        std::size_t iterations
    ) {
        if (status_ != ExperimentStatus::Created) {
            throw std::logic_error(
                "Experiment has already been executed."
            );
        }

        try {
            status_ = ExperimentStatus::Training;

            model_.train(target, iterations);

            const Evaluation result = model_.evaluate(target);

            status_ = ExperimentStatus::Completed;

            return result;

        } catch (...) {
            status_ = ExperimentStatus::Failed;
            throw;
        }
    }

    ExperimentStatus status() const {
        return status_;
    }

    const std::string& id() const {
        return id_;
    }
};

void runTests() {
    QuantumCircuit circuit(2);

    const auto state = circuit.execute({
        0.0, 0.0, 0.0, 0.0
    });

    if (std::abs(state[0] - 1.0) > 1e-10) {
        throw std::runtime_error("Zero-state test failed.");
    }

    ModelConfig config;
    config.iterations = 20;

    BornMachine model(config);

    const std::vector<double> target = {
        0.25, 0.25, 0.25, 0.25
    };

    model.train(target, 20);

    if (model.history().size() != 20) {
        throw std::runtime_error("History test failed.");
    }

    const auto counts = model.sample(1000);

    const std::size_t total = std::accumulate(
        counts.begin(),
        counts.end(),
        std::size_t(0)
    );

    if (total != 1000) {
        throw std::runtime_error("Sampling test failed.");
    }

    std::cout << "All C++17 tests passed.\n";
}

void runExperiment() {
    ModelConfig config;

    BornMachine model(config);

    const std::vector<double> target = {
        0.40, 0.10, 0.10, 0.40
    };

    Experiment experiment("QGM-CPP-001", model);

    const Evaluation evaluation = experiment.execute(
        target,
        config.iterations
    );

    std::cout << "\nQUANTUM GENERATIVE LEARNING\n";
    std::cout << "Experiment: " << experiment.id() << '\n';
    std::cout << "Status: "
              << statusName(experiment.status()) << '\n';

    std::cout << std::fixed << std::setprecision(6);

    std::cout << "\nGenerated distribution:\n";

    for (std::size_t i = 0;
         i < evaluation.probabilities.size();
         ++i) {
        std::cout << "|" << std::bitset<2>(i)
                  << "> : "
                  << evaluation.probabilities[i]
                  << '\n';
    }

    std::cout << "\nKL divergence: "
              << evaluation.klDivergence << '\n';

    std::cout << "Total variation: "
              << evaluation.totalVariation << '\n';

    std::cout << "Generated entropy: "
              << evaluation.entropy << '\n';

    std::cout << "\nMeasurement counts:\n";

    const auto counts = model.sample(config.shots);

    for (std::size_t i = 0; i < counts.size(); ++i) {
        std::cout << "|" << std::bitset<2>(i)
                  << "> : " << counts[i] << '\n';
    }
}

} // namespace qgm

int main() {
    try {
        qgm::runExperiment();
        qgm::runTests();

    } catch (const std::exception& error) {
        std::cerr << "Execution error: "
                  << error.what() << '\n';

        return 1;
    }

    return 0;
}
