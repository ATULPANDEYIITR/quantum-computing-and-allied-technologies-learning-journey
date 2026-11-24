#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Quantum Kernel Governance and Computation Engine
 *
 * Implements a state-vector feature map and a quantum fidelity
 * kernel, followed by kernel ridge classification.
 *
 * C++17, standard library only.
 */

namespace quantum {

using Complex = std::complex<double>;
using Vector = std::vector<double>;
using State = std::vector<Complex>;
using Matrix = std::vector<std::vector<double>>;

constexpr double EPS = 1e-10;

class QuantumException : public std::runtime_error {
public:
    explicit QuantumException(const std::string& message)
        : std::runtime_error(message) {}
};

enum class GateType {
    HADAMARD,
    RX,
    RZ,
    CZ
};

enum class KernelStatus {
    VALID,
    INVALID_SYMMETRY,
    INVALID_DIAGONAL,
    NOT_POSITIVE_SEMIDEFINITE
};

struct CircuitConfig {
    std::size_t qubits = 2;
    double rotationScale = 2.0;
    bool entanglement = true;

    void validate() const {
        if (qubits < 1 || qubits > 12) {
            throw QuantumException("Qubit count must be between 1 and 12.");
        }

        if (!std::isfinite(rotationScale)) {
            throw QuantumException("Rotation scale must be finite.");
        }
    }
};

struct Sample {
    Vector features;
    int label;

    void validate(std::size_t dimensions) const {
        if (features.size() != dimensions) {
            throw QuantumException("Invalid feature dimension.");
        }

        if (label != -1 && label != 1) {
            throw QuantumException("Labels must be -1 or +1.");
        }

        for (double value : features) {
            if (!std::isfinite(value)) {
                throw QuantumException("Non-finite feature detected.");
            }
        }
    }
};

class Circuit {
private:
    CircuitConfig config_;
    std::size_t dimension_;

    void validateQubit(std::size_t qubit) const {
        if (qubit >= config_.qubits) {
            throw QuantumException("Qubit index out of range.");
        }
    }

    State initialState() const {
        State state(dimension_, Complex(0.0, 0.0));
        state[0] = Complex(1.0, 0.0);
        return state;
    }

    void hadamard(State& state, std::size_t qubit) const {
        validateQubit(qubit);

        const std::size_t mask = std::size_t(1) << qubit;
        const double factor = 1.0 / std::sqrt(2.0);

        for (std::size_t i = 0; i < dimension_; ++i) {
            if ((i & mask) == 0) {
                const std::size_t partner = i | mask;

                const Complex a = state[i];
                const Complex b = state[partner];

                state[i] = (a + b) * factor;
                state[partner] = (a - b) * factor;
            }
        }
    }

    void rz(
        State& state,
        std::size_t qubit,
        double angle
    ) const {
        validateQubit(qubit);

        const std::size_t mask = std::size_t(1) << qubit;
        const double half = angle / 2.0;

        const Complex phaseZero(
            std::cos(-half), std::sin(-half)
        );

        const Complex phaseOne(
            std::cos(half), std::sin(half)
        );

        for (std::size_t i = 0; i < dimension_; ++i) {
            state[i] *= (i & mask) ? phaseOne : phaseZero;
        }
    }

    void rx(
        State& state,
        std::size_t qubit,
        double angle
    ) const {
        validateQubit(qubit);

        const std::size_t mask = std::size_t(1) << qubit;
        const double c = std::cos(angle / 2.0);
        const double s = std::sin(angle / 2.0);

        const Complex imaginary(0.0, 1.0);

        for (std::size_t i = 0; i < dimension_; ++i) {
            if ((i & mask) == 0) {
                const std::size_t partner = i | mask;

                const Complex a = state[i];
                const Complex b = state[partner];

                state[i] = c * a - imaginary * s * b;
                state[partner] = c * b - imaginary * s * a;
            }
        }
    }

    void cz(
        State& state,
        std::size_t first,
        std::size_t second
    ) const {
        validateQubit(first);
        validateQubit(second);

        if (first == second) {
            throw QuantumException("CZ requires distinct qubits.");
        }

        const std::size_t a = std::size_t(1) << first;
        const std::size_t b = std::size_t(1) << second;

        for (std::size_t i = 0; i < dimension_; ++i) {
            if ((i & a) && (i & b)) {
                state[i] = -state[i];
            }
        }
    }

public:
    explicit Circuit(CircuitConfig config)
        : config_(config),
          dimension_(std::size_t(1) << config.qubits) {
        config_.validate();
    }

    std::size_t qubits() const {
        return config_.qubits;
    }

    State encode(const Vector& features) const {
        if (features.size() != config_.qubits) {
            throw QuantumException("Incorrect feature dimensions.");
        }

        for (double value : features) {
            if (!std::isfinite(value)) {
                throw QuantumException("Invalid feature value.");
            }
        }

        State state = initialState();

        for (std::size_t q = 0; q < config_.qubits; ++q) {
            hadamard(state, q);
        }

        for (std::size_t q = 0; q < config_.qubits; ++q) {
            const double angle = config_.rotationScale * features[q];

            rz(state, q, angle);
            rx(state, q, angle);
        }

        if (config_.entanglement) {
            for (std::size_t q = 0; q + 1 < config_.qubits; ++q) {
                cz(state, q, q + 1);
            }
        }

        const double norm = std::inner_product(
            state.begin(),
            state.end(),
            state.begin(),
            0.0,
            std::plus<double>(),
            [](const Complex& a, const Complex& b) {
                return std::norm(a);
            }
        );

        if (std::abs(norm - 1.0) > 1e-9) {
            throw QuantumException("Quantum state normalization failed.");
        }

        return state;
    }
};

class FidelityKernel {
private:
    Circuit circuit_;

    using Key = std::pair<Vector, Vector>;

    std::map<Vector, State> stateCache_;
    std::map<Key, double> kernelCache_;

public:
    explicit FidelityKernel(const CircuitConfig& config)
        : circuit_(config) {}

    const State& state(const Vector& features) {
        auto it = stateCache_.find(features);

        if (it == stateCache_.end()) {
            State encoded = circuit_.encode(features);

            it = stateCache_.emplace(
                features,
                std::move(encoded)
            ).first;
        }

        return it->second;
    }

    double evaluate(const Vector& first, const Vector& second) {
        Vector x = first;
        Vector z = second;

        if (x.size() != circuit_.qubits() ||
            z.size() != circuit_.qubits()) {
            throw QuantumException("Kernel feature dimensions differ.");
        }

        Key key = x <= z
            ? Key{x, z}
            : Key{z, x};

        auto cached = kernelCache_.find(key);

        if (cached != kernelCache_.end()) {
            return cached->second;
        }

        const State& a = state(x);
        const State& b = state(z);

        Complex overlap(0.0, 0.0);

        for (std::size_t i = 0; i < a.size(); ++i) {
            overlap += std::conj(a[i]) * b[i];
        }

        const double fidelity = std::clamp(
            std::norm(overlap), 0.0, 1.0
        );

        kernelCache_.emplace(key, fidelity);

        return fidelity;
    }

    Matrix matrix(const std::vector<Sample>& samples) {
        if (samples.empty()) {
            throw QuantumException("Dataset cannot be empty.");
        }

        const std::size_t n = samples.size();

        Matrix result(n, Vector(n, 0.0));

        for (std::size_t i = 0; i < n; ++i) {
            samples[i].validate(circuit_.qubits());

            result[i][i] = 1.0;

            for (std::size_t j = i + 1; j < n; ++j) {
                const double value = evaluate(
                    samples[i].features,
                    samples[j].features
                );

                result[i][j] = value;
                result[j][i] = value;
            }
        }

        return result;
    }

    std::size_t cachedStates() const {
        return stateCache_.size();
    }

    std::size_t cachedKernels() const {
        return kernelCache_.size();
    }
};

class LinearSolver {
public:
    static Vector solve(Matrix matrix, Vector rhs) {
        const std::size_t n = rhs.size();

        if (matrix.size() != n) {
            throw QuantumException("Invalid matrix dimensions.");
        }

        for (const auto& row : matrix) {
            if (row.size() != n) {
                throw QuantumException("Matrix must be square.");
            }
        }

        // Gaussian elimination with partial pivoting.
        for (std::size_t col = 0; col < n; ++col) {
            std::size_t pivot = col;

            for (std::size_t row = col + 1; row < n; ++row) {
                if (std::abs(matrix[row][col]) >
                    std::abs(matrix[pivot][col])) {
                    pivot = row;
                }
            }

            if (std::abs(matrix[pivot][col]) < EPS) {
                throw QuantumException("Singular kernel matrix.");
            }

            std::swap(matrix[col], matrix[pivot]);
            std::swap(rhs[col], rhs[pivot]);

            for (std::size_t row = col + 1; row < n; ++row) {
                const double factor =
                    matrix[row][col] / matrix[col][col];

                for (std::size_t j = col; j < n; ++j) {
                    matrix[row][j] -= factor * matrix[col][j];
                }

                rhs[row] -= factor * rhs[col];
            }
        }

        Vector solution(n, 0.0);

        for (int i = static_cast<int>(n) - 1; i >= 0; --i) {
            double value = rhs[i];

            for (std::size_t j = i + 1; j < n; ++j) {
                value -= matrix[i][j] * solution[j];
            }

            solution[i] = value / matrix[i][i];
        }

        return solution;
    }
};

class KernelClassifier {
private:
    FidelityKernel& kernel_;
    double regularization_;

    std::vector<Sample> training_;
    Vector coefficients_;
    bool fitted_ = false;

public:
    KernelClassifier(
        FidelityKernel& kernel,
        double regularization
    )
        : kernel_(kernel),
          regularization_(regularization) {
        if (!std::isfinite(regularization_) ||
            regularization_ <= 0) {
            throw QuantumException("Invalid regularization.");
        }
    }

    void fit(const std::vector<Sample>& samples) {
        if (samples.size() < 2) {
            throw QuantumException("At least two samples are required.");
        }

        bool positive = false;
        bool negative = false;

        for (const auto& sample : samples) {
            sample.validate(2);
            positive |= sample.label == 1;
            negative |= sample.label == -1;
        }

        if (!positive || !negative) {
            throw QuantumException("Both classes are required.");
        }

        std::map<Vector, bool> uniqueSamples;

        for (const auto& sample : samples) {
            if (!uniqueSamples.emplace(
                    sample.features, true
                ).second) {
                throw QuantumException("Duplicate training observation.");
            }
        }

        Matrix gram = kernel_.matrix(samples);
        Vector labels;

        for (std::size_t i = 0; i < samples.size(); ++i) {
            gram[i][i] += regularization_;
            labels.push_back(samples[i].label);
        }

        coefficients_ = LinearSolver::solve(
            std::move(gram),
            std::move(labels)
        );

        training_ = samples;
        fitted_ = true;
    }

    double decision(const Vector& features) {
        if (!fitted_) {
            throw QuantumException("Classifier is not fitted.");
        }

        double score = 0.0;

        for (std::size_t i = 0; i < training_.size(); ++i) {
            score += coefficients_[i] *
                kernel_.evaluate(training_[i].features, features);
        }

        return score;
    }

    int predict(const Vector& features) {
        return decision(features) >= 0.0 ? 1 : -1;
    }
};

struct Metrics {
    std::size_t truePositive = 0;
    std::size_t trueNegative = 0;
    std::size_t falsePositive = 0;
    std::size_t falseNegative = 0;

    void add(int actual, int predicted) {
        if (actual == 1 && predicted == 1) {
            ++truePositive;
        } else if (actual == -1 && predicted == -1) {
            ++trueNegative;
        } else if (actual == -1) {
            ++falsePositive;
        } else {
            ++falseNegative;
        }
    }

    double accuracy() const {
        const std::size_t total =
            truePositive + trueNegative +
            falsePositive + falseNegative;

        if (total == 0) return 0.0;

        return static_cast<double>(
            truePositive + trueNegative
        ) / total;
    }
};

} // namespace quantum

int main() {
    try {
        using namespace quantum;

        CircuitConfig config;
        config.qubits = 2;
        config.rotationScale = 2.0;
        config.entanglement = true;

        FidelityKernel kernel(config);
        KernelClassifier classifier(kernel, 0.15);

        std::vector<Sample> dataset;

        // Deterministic nonlinear classification scenario.
        for (int i = 0; i < 32; ++i) {
            const double x =
                -1.2 + 2.4 * static_cast<double>(i % 8) / 7.0;

            const double z =
                -1.2 + 2.4 * static_cast<double>(i / 8) / 3.0;

            const int label =
                std::sin(2 * x) * std::cos(2 * z) >= 0
                ? 1 : -1;

            dataset.push_back({{x, z}, label});
        }

        std::vector<Sample> training(
            dataset.begin(), dataset.begin() + 24
        );

        std::vector<Sample> testing(
            dataset.begin() + 24, dataset.end()
        );

        classifier.fit(training);

        Metrics metrics;

        for (const auto& sample : testing) {
            const int predicted =
                classifier.predict(sample.features);

            metrics.add(sample.label, predicted);

            std::cout
                << "Actual: " << std::setw(2) << sample.label
                << " Predicted: " << std::setw(2) << predicted
                << '\n';
        }

        Matrix gram = kernel.matrix(training);

        double symmetryError = 0.0;
        double diagonalError = 0.0;

        for (std::size_t i = 0; i < gram.size(); ++i) {
            diagonalError = std::max(
                diagonalError,
                std::abs(gram[i][i] - 1.0)
            );

            for (std::size_t j = 0; j < gram.size(); ++j) {
                symmetryError = std::max(
                    symmetryError,
                    std::abs(gram[i][j] - gram[j][i])
                );
            }
        }

        std::cout << "\nQUANTUM KERNEL ENGINE\n";
        std::cout << "=====================\n";
        std::cout << "Qubits: " << config.qubits << '\n';
        std::cout << "Training samples: " << training.size() << '\n';
        std::cout << "Testing samples: " << testing.size() << '\n';

        std::cout << std::fixed << std::setprecision(4);
        std::cout << "Accuracy: " << metrics.accuracy() << '\n';

        std::cout << "True positives: "
                  << metrics.truePositive << '\n';

        std::cout << "True negatives: "
                  << metrics.trueNegative << '\n';

        std::cout << "False positives: "
                  << metrics.falsePositive << '\n';

        std::cout << "False negatives: "
                  << metrics.falseNegative << '\n';

        std::cout << "Symmetry error: "
                  << symmetryError << '\n';

        std::cout << "Diagonal error: "
                  << diagonalError << '\n';

        std::cout << "Cached states: "
                  << kernel.cachedStates() << '\n';

        std::cout << "Cached kernel values: "
                  << kernel.cachedKernels() << '\n';

        if (symmetryError > 1e-9 || diagonalError > 1e-9) {
            throw QuantumException("Kernel validation failed.");
        }

        if (kernel.evaluate({0.2, -0.3}, {0.2, -0.3}) < 0.999999) {
            throw QuantumException("Self-fidelity validation failed.");
        }

        std::cout << "\nAll kernel validation checks passed.\n";

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }
}
