#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Hybrid Quantum-Classical Machine Learning
 *
 * C++17 implementation:
 * - State-vector quantum simulation
 * - Quantum kernel computation
 * - Classical kernel classifier
 * - Quantum feature encoding
 * - Gram matrix construction
 * - Kernel ridge regression
 * - Numerical validation
 * - Classification metrics
 *
 * Complexity:
 * State-vector gate: O(2^n)
 * State storage: O(2^n)
 * Gram matrix: O(N^2 * 2^n) approximately
 * Kernel solver: O(N^3)
 */

namespace hybrid {

using Complex = std::complex<double>;
using Vector = std::vector<double>;
using Matrix = std::vector<Vector>;

constexpr double PI = 3.14159265358979323846;
constexpr double EPS = 1e-10;


class ValidationError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};


class QuantumError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};


void validateFinite(double value, const std::string& name) {
    if (!std::isfinite(value)) {
        throw ValidationError(name + " must be finite");
    }
}


void validateVector(const Vector& values, std::size_t expected) {
    if (values.size() != expected) {
        throw ValidationError("Incorrect vector dimension");
    }

    for (double value : values) {
        validateFinite(value, "Vector element");
    }
}


// ---------------------------------------------------------
// Quantum state-vector engine
// ---------------------------------------------------------

class QuantumRegister {
private:
    std::size_t qubits_;
    std::size_t dimension_;
    std::vector<Complex> state_;

    void validateQubit(std::size_t qubit) const {
        if (qubit >= qubits_) {
            throw QuantumError("Qubit index out of range");
        }
    }

    void applyGate(
        std::size_t qubit,
        const std::array<std::array<Complex, 2>, 2>& gate
    ) {
        validateQubit(qubit);

        const std::size_t mask = std::size_t{1} << qubit;

        for (std::size_t index = 0; index < dimension_; ++index) {
            if (index & mask) {
                continue;
            }

            const std::size_t paired = index | mask;

            const Complex a = state_[index];
            const Complex b = state_[paired];

            state_[index] =
                gate[0][0] * a + gate[0][1] * b;

            state_[paired] =
                gate[1][0] * a + gate[1][1] * b;
        }
    }

public:
    explicit QuantumRegister(std::size_t qubits)
        : qubits_(qubits),
          dimension_(std::size_t{1} << qubits),
          state_(dimension_, Complex{0.0, 0.0}) {

        if (qubits < 1 || qubits > 12) {
            throw ValidationError("Qubits must be between 1 and 12");
        }

        state_[0] = Complex{1.0, 0.0};
    }

    std::size_t qubits() const {
        return qubits_;
    }

    void hadamard(std::size_t qubit) {
        const double c = 1.0 / std::sqrt(2.0);

        applyGate(qubit, {{
            {Complex{c, 0}, Complex{c, 0}},
            {Complex{c, 0}, Complex{-c, 0}}
        }});
    }

    void ry(std::size_t qubit, double theta) {
        validateFinite(theta, "Rotation angle");

        const double c = std::cos(theta / 2);
        const double s = std::sin(theta / 2);

        applyGate(qubit, {{
            {Complex{c, 0}, Complex{-s, 0}},
            {Complex{s, 0}, Complex{c, 0}}
        }});
    }

    void rz(std::size_t qubit, double theta) {
        validateFinite(theta, "Rotation angle");

        const double c = std::cos(theta / 2);
        const double s = std::sin(theta / 2);

        applyGate(qubit, {{
            {Complex{c, -s}, Complex{0, 0}},
            {Complex{0, 0}, Complex{c, s}}
        }});
    }

    void cnot(std::size_t control, std::size_t target) {
        validateQubit(control);
        validateQubit(target);

        if (control == target) {
            throw QuantumError("Control and target must differ");
        }

        const std::size_t cm = std::size_t{1} << control;
        const std::size_t tm = std::size_t{1} << target;

        for (std::size_t index = 0; index < dimension_; ++index) {
            if ((index & cm) && !(index & tm)) {
                std::swap(
                    state_[index],
                    state_[index | tm]
                );
            }
        }
    }

    double expectationZ(std::size_t qubit) const {
        validateQubit(qubit);

        const std::size_t mask = std::size_t{1} << qubit;

        double result = 0.0;

        for (std::size_t index = 0; index < dimension_; ++index) {
            const double probability = std::norm(state_[index]);

            result += (index & mask)
                ? -probability
                : probability;
        }

        return result;
    }

    const std::vector<Complex>& state() const {
        return state_;
    }

    void validateNormalization() const {
        double norm = 0.0;

        for (const auto& amplitude : state_) {
            norm += std::norm(amplitude);
        }

        if (std::abs(norm - 1.0) > 1e-8) {
            throw QuantumError("Quantum state is not normalized");
        }
    }
};


// ---------------------------------------------------------
// Quantum feature encoding
// ---------------------------------------------------------

class QuantumFeatureMap {
private:
    std::size_t qubits_;

public:
    explicit QuantumFeatureMap(std::size_t qubits)
        : qubits_(qubits) {

        if (qubits < 1 || qubits > 12) {
            throw ValidationError("Invalid qubit count");
        }
    }

    std::vector<Complex> encode(const Vector& features) const {
        validateVector(features, qubits_);

        QuantumRegister circuit(qubits_);

        for (std::size_t i = 0; i < qubits_; ++i) {
            circuit.hadamard(i);
            circuit.ry(i, features[i]);
            circuit.rz(i, features[i] * features[i]);
        }

        for (std::size_t i = 0; i + 1 < qubits_; ++i) {
            circuit.cnot(i, i + 1);
        }

        circuit.validateNormalization();

        return circuit.state();
    }
};


// ---------------------------------------------------------
// Quantum kernel
// ---------------------------------------------------------

class QuantumKernel {
private:
    QuantumFeatureMap featureMap_;

public:
    explicit QuantumKernel(std::size_t qubits)
        : featureMap_(qubits) {}

    double compute(
        const Vector& first,
        const Vector& second
    ) const {

        const auto stateA = featureMap_.encode(first);
        const auto stateB = featureMap_.encode(second);

        if (stateA.size() != stateB.size()) {
            throw QuantumError("Quantum state dimensions differ");
        }

        // Fidelity kernel: |<phi(x)|phi(y)>|^2.
        Complex innerProduct{0.0, 0.0};

        for (std::size_t i = 0; i < stateA.size(); ++i) {
            innerProduct += std::conj(stateA[i]) * stateB[i];
        }

        const double kernel = std::norm(innerProduct);

        return std::clamp(kernel, 0.0, 1.0);
    }
};


// ---------------------------------------------------------
// Dataset
// ---------------------------------------------------------

struct Sample {
    Vector features;
    int label;
};


std::vector<Sample> generateDataset(
    std::size_t count,
    unsigned int seed = 42
) {
    if (count < 20) {
        throw ValidationError("Dataset must contain at least 20 samples");
    }

    std::mt19937 generator(seed);
    std::uniform_real_distribution<double> distribution(-PI, PI);

    std::vector<Sample> dataset;
    dataset.reserve(count);

    for (std::size_t i = 0; i < count; ++i) {
        const double x = distribution(generator);
        const double y = distribution(generator);

        const int label =
            std::sin(x) * std::cos(y) > 0.0 ? 1 : 0;

        dataset.push_back({{x, y}, label});
    }

    std::shuffle(
        dataset.begin(),
        dataset.end(),
        generator
    );

    return dataset;
}


// ---------------------------------------------------------
// Kernel Gram matrix
// ---------------------------------------------------------

Matrix buildGramMatrix(
    const std::vector<Sample>& dataset,
    const QuantumKernel& kernel
) {
    const std::size_t n = dataset.size();

    Matrix gram(n, Vector(n, 0.0));

    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i; j < n; ++j) {

            const double value = kernel.compute(
                dataset[i].features,
                dataset[j].features
            );

            gram[i][j] = value;
            gram[j][i] = value;
        }
    }

    return gram;
}


// ---------------------------------------------------------
// Linear system solver using Gaussian elimination
// ---------------------------------------------------------

Vector solveLinearSystem(Matrix matrix, Vector values) {
    const std::size_t n = matrix.size();

    if (n == 0 || values.size() != n) {
        throw ValidationError("Invalid linear system dimensions");
    }

    for (const auto& row : matrix) {
        if (row.size() != n) {
            throw ValidationError("Matrix must be square");
        }
    }

    // Partial pivoting improves numerical stability.
    for (std::size_t column = 0; column < n; ++column) {
        std::size_t pivot = column;

        for (std::size_t row = column + 1; row < n; ++row) {
            if (std::abs(matrix[row][column]) >
                std::abs(matrix[pivot][column])) {
                pivot = row;
            }
        }

        if (std::abs(matrix[pivot][column]) < EPS) {
            throw ValidationError("Singular or ill-conditioned matrix");
        }

        std::swap(matrix[pivot], matrix[column]);
        std::swap(values[pivot], values[column]);

        for (std::size_t row = column + 1; row < n; ++row) {
            const double factor =
                matrix[row][column] / matrix[column][column];

            for (std::size_t j = column; j < n; ++j) {
                matrix[row][j] -= factor * matrix[column][j];
            }

            values[row] -= factor * values[column];
        }
    }

    Vector solution(n, 0.0);

    for (int row = static_cast<int>(n) - 1; row >= 0; --row) {
        double sum = values[row];

        for (std::size_t column = row + 1; column < n; ++column) {
            sum -= matrix[row][column] * solution[column];
        }

        solution[row] = sum / matrix[row][row];
    }

    return solution;
}


// ---------------------------------------------------------
// Kernel ridge classifier
// ---------------------------------------------------------

class QuantumKernelClassifier {
private:
    QuantumKernel kernel_;
    std::vector<Sample> training_;
    Vector coefficients_;
    double regularization_;

public:
    QuantumKernelClassifier(
        std::size_t qubits,
        double regularization = 0.1
    )
        : kernel_(qubits),
          regularization_(regularization) {

        if (!std::isfinite(regularization) || regularization <= 0) {
            throw ValidationError("Regularization must be positive");
        }
    }

    void fit(const std::vector<Sample>& dataset) {
        if (dataset.empty()) {
            throw ValidationError("Training dataset cannot be empty");
        }

        training_ = dataset;

        const std::size_t n = training_.size();

        Matrix gram = buildGramMatrix(training_, kernel_);

        Vector targets(n);

        for (std::size_t i = 0; i < n; ++i) {
            if (training_[i].label != 0 &&
                training_[i].label != 1) {
                throw ValidationError("Labels must be binary");
            }

            targets[i] = training_[i].label == 1 ? 1.0 : -1.0;

            gram[i][i] += regularization_;
        }

        coefficients_ = solveLinearSystem(
            std::move(gram),
            std::move(targets)
        );
    }

    double decisionFunction(const Vector& features) const {
        if (training_.empty() || coefficients_.empty()) {
            throw ValidationError("Classifier has not been trained");
        }

        double result = 0.0;

        for (std::size_t i = 0; i < training_.size(); ++i) {
            result += coefficients_[i] * kernel_.compute(
                training_[i].features,
                features
            );
        }

        return result;
    }

    int predict(const Vector& features) const {
        return decisionFunction(features) >= 0.0 ? 1 : 0;
    }
};


// ---------------------------------------------------------
// Evaluation
// ---------------------------------------------------------

struct Metrics {
    double accuracy;
    double precision;
    double recall;
    double f1;
    int tp;
    int tn;
    int fp;
    int fn;
};


Metrics evaluate(
    const QuantumKernelClassifier& model,
    const std::vector<Sample>& dataset
) {
    if (dataset.empty()) {
        throw ValidationError("Evaluation dataset cannot be empty");
    }

    int tp = 0;
    int tn = 0;
    int fp = 0;
    int fn = 0;

    for (const auto& sample : dataset) {
        const int prediction = model.predict(sample.features);

        if (prediction == 1 && sample.label == 1) ++tp;
        else if (prediction == 0 && sample.label == 0) ++tn;
        else if (prediction == 1) ++fp;
        else ++fn;
    }

    const double precision =
        tp + fp ? static_cast<double>(tp) / (tp + fp) : 0.0;

    const double recall =
        tp + fn ? static_cast<double>(tp) / (tp + fn) : 0.0;

    const double f1 =
        precision + recall
        ? 2.0 * precision * recall / (precision + recall)
        : 0.0;

    return {
        static_cast<double>(tp + tn) / dataset.size(),
        precision,
        recall,
        f1,
        tp,
        tn,
        fp,
        fn
    };
}


// ---------------------------------------------------------
// Tests
// ---------------------------------------------------------

void runTests() {
    QuantumRegister circuit(2);

    circuit.hadamard(0);
    circuit.cnot(0, 1);

    circuit.validateNormalization();

    if (std::abs(circuit.expectationZ(0)) > 1e-8) {
        throw std::runtime_error("Bell-state test failed");
    }

    if (std::abs(circuit.expectationZ(1)) > 1e-8) {
        throw std::runtime_error("Entanglement test failed");
    }

    QuantumKernel kernel(2);

    const Vector sampleA{0.5, 0.7};
    const Vector sampleB{0.5, 0.7};

    const double similarity = kernel.compute(sampleA, sampleB);

    if (std::abs(similarity - 1.0) > 1e-8) {
        throw std::runtime_error("Kernel identity test failed");
    }

    const Vector solution = solveLinearSystem(
        {{2.0, 1.0}, {1.0, 3.0}},
        {5.0, 6.0}
    );

    if (std::abs(solution[0] - 1.8) > 1e-8 ||
        std::abs(solution[1] - 1.4) > 1e-8) {
        throw std::runtime_error("Linear solver test failed");
    }
}


// ---------------------------------------------------------
// Main
// ---------------------------------------------------------

} // namespace hybrid


int main() {
    using namespace hybrid;

    try {
        runTests();

        const auto dataset = generateDataset(100);

        const std::size_t split = 75;

        std::vector<Sample> training(
            dataset.begin(),
            dataset.begin() + split
        );

        std::vector<Sample> testing(
            dataset.begin() + split,
            dataset.end()
        );

        QuantumKernelClassifier classifier(
            2,
            0.1
        );

        classifier.fit(training);

        const Metrics metrics = evaluate(classifier, testing);

        std::cout << std::fixed << std::setprecision(4);

        std::cout << "HYBRID QUANTUM-CLASSICAL ML\n";
        std::cout << "---------------------------\n";

        std::cout << "Training samples: " << training.size() << '\n';
        std::cout << "Testing samples: " << testing.size() << '\n';

        std::cout << "Accuracy: " << metrics.accuracy << '\n';
        std::cout << "Precision: " << metrics.precision << '\n';
        std::cout << "Recall: " << metrics.recall << '\n';
        std::cout << "F1 score: " << metrics.f1 << '\n';

        std::cout << "\nConfusion matrix\n";
        std::cout << "TP: " << metrics.tp << '\n';
        std::cout << "TN: " << metrics.tn << '\n';
        std::cout << "FP: " << metrics.fp << '\n';
        std::cout << "FN: " << metrics.fn << '\n';

        std::cout << "\nExample prediction\n";

        const Vector example{0.8, 1.2};

        std::cout << "Prediction: "
                  << classifier.predict(example)
                  << '\n';

        std::cout << "Decision score: "
                  << classifier.decisionFunction(example)
                  << '\n';

        std::cout << "\nAll validation tests passed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Execution failed: "
                  << error.what() << '\n';

        return 1;
    }

    return 0;
}
