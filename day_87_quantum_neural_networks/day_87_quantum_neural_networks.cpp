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
 * QUANTUM NEURAL NETWORKS: FUNDAMENTALS
 *
 * C++17 implementation of a variational quantum classifier.
 *
 * Demonstrates:
 * - State-vector quantum simulation
 * - Qubit representation
 * - Quantum rotation gates
 * - CNOT entanglement
 * - Classical feature encoding
 * - Parameterized quantum circuits
 * - Expectation-value measurement
 * - Parameter-shift optimization
 * - Classification and evaluation
 *
 * Complexity:
 * State-vector storage: O(2^n)
 * Single-qubit gate: O(2^n)
 * CNOT gate: O(2^n)
 *
 * No external dependencies.
 */

using Complex = std::complex<double>;

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 1e-9;

enum class GateType {
    RY,
    RZ,
    CNOT
};

struct Gate {
    GateType type;
    int first;
    int second;
    double angle;
};

struct Example {
    std::array<double, 2> features;
    int label;
};

struct Metrics {
    int epoch;
    double loss;
    double accuracy;
};

class QuantumException : public std::runtime_error {
public:
    explicit QuantumException(const std::string& message)
        : std::runtime_error(message) {}
};

class QuantumRegister {
private:
    int qubits;
    std::vector<Complex> state;

public:
    explicit QuantumRegister(int count) : qubits(count) {
        if (count < 1 || count > 20) {
            throw QuantumException("Qubit count must be between 1 and 20.");
        }

        state.resize(1ULL << count, Complex(0.0, 0.0));
        state[0] = Complex(1.0, 0.0);
    }

    int qubitCount() const {
        return qubits;
    }

    void validateQubit(int q) const {
        if (q < 0 || q >= qubits) {
            throw QuantumException("Invalid qubit index.");
        }
    }

    void applyRY(int q, double angle) {
        validateQubit(q);

        if (!std::isfinite(angle)) {
            throw QuantumException("Rotation angle must be finite.");
        }

        const double c = std::cos(angle / 2.0);
        const double s = std::sin(angle / 2.0);

        const std::size_t mask = 1ULL << q;

        for (std::size_t i = 0; i < state.size(); ++i) {
            if (i & mask) continue;

            const std::size_t j = i | mask;

            const Complex a = state[i];
            const Complex b = state[j];

            state[i] = c * a - s * b;
            state[j] = s * a + c * b;
        }
    }

    void applyRZ(int q, double angle) {
        validateQubit(q);

        if (!std::isfinite(angle)) {
            throw QuantumException("Rotation angle must be finite.");
        }

        const Complex phase0(
            std::cos(angle / 2.0),
            -std::sin(angle / 2.0)
        );

        const Complex phase1(
            std::cos(angle / 2.0),
            std::sin(angle / 2.0)
        );

        const std::size_t mask = 1ULL << q;

        for (std::size_t i = 0; i < state.size(); ++i) {
            state[i] *= (i & mask) ? phase1 : phase0;
        }
    }

    void applyCNOT(int control, int target) {
        validateQubit(control);
        validateQubit(target);

        if (control == target) {
            throw QuantumException("CNOT control and target must differ.");
        }

        const std::size_t controlMask = 1ULL << control;
        const std::size_t targetMask = 1ULL << target;

        for (std::size_t i = 0; i < state.size(); ++i) {
            if ((i & controlMask) && !(i & targetMask)) {
                const std::size_t j = i | targetMask;
                std::swap(state[i], state[j]);
            }
        }
    }

    void apply(const Gate& gate) {
        switch (gate.type) {
            case GateType::RY:
                applyRY(gate.first, gate.angle);
                break;

            case GateType::RZ:
                applyRZ(gate.first, gate.angle);
                break;

            case GateType::CNOT:
                applyCNOT(gate.first, gate.second);
                break;
        }
    }

    std::vector<double> probabilities() const {
        std::vector<double> result;
        result.reserve(state.size());

        for (const auto& amplitude : state) {
            result.push_back(std::norm(amplitude));
        }

        return result;
    }

    double expectationZ(int q) const {
        validateQubit(q);

        const std::size_t mask = 1ULL << q;

        double expectation = 0.0;

        for (std::size_t i = 0; i < state.size(); ++i) {
            const double sign = (i & mask) ? -1.0 : 1.0;
            expectation += sign * std::norm(state[i]);
        }

        return expectation;
    }

    void validateNormalization() const {
        const double norm = std::accumulate(
            state.begin(),
            state.end(),
            0.0,
            [](double total, const Complex& amplitude) {
                return total + std::norm(amplitude);
            }
        );

        if (std::abs(norm - 1.0) > EPSILON) {
            throw QuantumException("Quantum state normalization failed.");
        }
    }
};

class QuantumCircuit {
private:
    std::vector<Gate> gates;

public:
    void addRY(int qubit, double angle) {
        gates.push_back({GateType::RY, qubit, -1, angle});
    }

    void addRZ(int qubit, double angle) {
        gates.push_back({GateType::RZ, qubit, -1, angle});
    }

    void addCNOT(int control, int target) {
        gates.push_back({GateType::CNOT, control, target, 0.0});
    }

    void execute(QuantumRegister& reg) const {
        for (const auto& gate : gates) {
            reg.apply(gate);
        }

        reg.validateNormalization();
    }

    std::size_t size() const {
        return gates.size();
    }
};

class VariationalQuantumClassifier {
private:
    static constexpr std::size_t PARAMETER_COUNT = 4;

    std::array<double, PARAMETER_COUNT> parameters;
    double learningRate;

    QuantumCircuit buildCircuit(
        const std::array<double, 2>& features,
        const std::array<double, PARAMETER_COUNT>& theta
    ) const {

        QuantumCircuit circuit;

        // Feature map.
        circuit.addRY(0, features[0]);
        circuit.addRY(1, features[1]);

        // Trainable quantum layers.
        circuit.addRY(0, theta[0]);
        circuit.addRY(1, theta[1]);
        circuit.addCNOT(0, 1);

        circuit.addRY(0, theta[2]);
        circuit.addRY(1, theta[3]);
        circuit.addCNOT(1, 0);

        return circuit;
    }

public:
    explicit VariationalQuantumClassifier(double rate = 0.05)
        : parameters{0.2, -0.3, 0.4, 0.1},
          learningRate(rate) {

        if (!std::isfinite(rate) || rate <= 0.0 || rate > 1.0) {
            throw QuantumException("Invalid learning rate.");
        }
    }

    double forward(
        const std::array<double, 2>& features,
        const std::array<double, PARAMETER_COUNT>& theta
    ) const {

        for (double x : features) {
            if (!std::isfinite(x)) {
                throw QuantumException("Features must be finite.");
            }
        }

        for (double p : theta) {
            if (!std::isfinite(p)) {
                throw QuantumException("Parameters must be finite.");
            }
        }

        QuantumRegister reg(2);

        auto circuit = buildCircuit(features, theta);
        circuit.execute(reg);

        return reg.expectationZ(0);
    }

    double predict(const std::array<double, 2>& features) const {
        return forward(features, parameters);
    }

    int classify(const std::array<double, 2>& features) const {
        return predict(features) >= 0.0 ? 1 : -1;
    }

    double loss(
        const std::vector<Example>& dataset,
        const std::array<double, PARAMETER_COUNT>& theta
    ) const {

        if (dataset.empty()) {
            throw QuantumException("Dataset cannot be empty.");
        }

        double total = 0.0;

        for (const auto& example : dataset) {
            if (example.label != -1 && example.label != 1) {
                throw QuantumException("Labels must be -1 or +1.");
            }

            const double prediction = forward(
                example.features,
                theta
            );

            const double difference = prediction - example.label;
            total += difference * difference;
        }

        return total / dataset.size();
    }

    std::array<double, PARAMETER_COUNT> gradient(
        const std::vector<Example>& dataset
    ) const {

        std::array<double, PARAMETER_COUNT> gradients{};
        constexpr double shift = PI / 2.0;

        /*
         * Each parameter occurs in one RY gate.
         * The parameter-shift rule is therefore applicable.
         */
        for (std::size_t i = 0; i < PARAMETER_COUNT; ++i) {
            auto plus = parameters;
            auto minus = parameters;

            plus[i] += shift;
            minus[i] -= shift;

            gradients[i] = (
                loss(dataset, plus) -
                loss(dataset, minus)
            ) / 2.0;
        }

        return gradients;
    }

    double accuracy(const std::vector<Example>& dataset) const {
        if (dataset.empty()) {
            throw QuantumException("Dataset cannot be empty.");
        }

        std::size_t correct = 0;

        for (const auto& example : dataset) {
            if (classify(example.features) == example.label) {
                ++correct;
            }
        }

        return static_cast<double>(correct) / dataset.size();
    }

    std::vector<Metrics> train(
        const std::vector<Example>& dataset,
        int epochs
    ) {

        if (dataset.empty() || epochs <= 0) {
            throw QuantumException("Invalid training configuration.");
        }

        std::vector<Metrics> history;

        for (int epoch = 1; epoch <= epochs; ++epoch) {
            const auto gradients = gradient(dataset);

            for (std::size_t i = 0; i < PARAMETER_COUNT; ++i) {
                parameters[i] -= learningRate * gradients[i];
            }

            const double currentLoss = loss(dataset, parameters);
            const double currentAccuracy = accuracy(dataset);

            history.push_back({
                epoch,
                currentLoss,
                currentAccuracy
            });

            if (currentLoss < 1e-7) {
                break;
            }
        }

        return history;
    }

    const auto& getParameters() const {
        return parameters;
    }
};

void demonstrateQuantumFundamentals() {
    std::cout << "\nQUANTUM NEURAL NETWORK FUNDAMENTALS\n";
    std::cout << "===================================\n";

    // Superposition.
    QuantumRegister singleQubit(1);
    singleQubit.applyRY(0, PI / 2.0);

    std::cout << "\n1. Superposition probabilities\n";

    for (double probability : singleQubit.probabilities()) {
        std::cout << std::fixed << std::setprecision(4)
                  << probability << " ";
    }

    std::cout << "\nPauli-Z expectation: "
              << singleQubit.expectationZ(0) << "\n";

    // Entanglement.
    QuantumRegister bell(2);
    bell.applyRY(0, PI / 2.0);
    bell.applyCNOT(0, 1);

    std::cout << "\n2. Bell-state probabilities\n";

    for (double probability : bell.probabilities()) {
        std::cout << probability << " ";
    }

    std::cout << "\n";

    // Classification dataset.
    const std::vector<Example> dataset = {
        {{{0.2, 0.3}}, 1},
        {{{0.3, 0.5}}, 1},
        {{{2.8, 2.5}}, -1},
        {{{2.5, 2.9}}, -1},
        {{{0.5, 0.2}}, 1},
        {{{2.9, 2.7}}, -1}
    };

    VariationalQuantumClassifier classifier(0.05);

    std::cout << "\n3. Variational quantum training\n";

    auto history = classifier.train(dataset, 100);

    for (const auto& metric : history) {
        if (metric.epoch % 10 == 0 ||
            metric.epoch == 1 ||
            metric.epoch == static_cast<int>(history.size())) {

            std::cout << "Epoch " << metric.epoch
                      << " | Loss: " << metric.loss
                      << " | Accuracy: " << metric.accuracy
                      << "\n";
        }
    }

    std::cout << "\n4. Learned parameters\n";

    for (double parameter : classifier.getParameters()) {
        std::cout << parameter << " ";
    }

    std::cout << "\n\n5. Predictions\n";

    for (const auto& example : dataset) {
        std::cout << "Features: "
                  << example.features[0] << ", "
                  << example.features[1]
                  << " | Expected: " << example.label
                  << " | Predicted: "
                  << classifier.classify(example.features)
                  << " | Expectation: "
                  << classifier.predict(example.features)
                  << "\n";
    }

    std::cout << "\nFinal accuracy: "
              << classifier.accuracy(dataset) * 100.0
              << "%\n";
}

void runTests() {
    QuantumRegister reg(1);
    reg.applyRY(0, PI / 2.0);

    if (std::abs(reg.expectationZ(0)) > EPSILON) {
        throw QuantumException("RY test failed.");
    }

    QuantumRegister bell(2);
    bell.applyRY(0, PI / 2.0);
    bell.applyCNOT(0, 1);

    const auto p = bell.probabilities();

    if (std::abs(p[0] - 0.5) > EPSILON ||
        std::abs(p[3] - 0.5) > EPSILON) {
        throw QuantumException("Bell-state test failed.");
    }

    try {
        QuantumRegister invalid(0);
        throw QuantumException("Invalid register accepted.");
    } catch (const QuantumException& error) {
        if (std::string(error.what()) == "Invalid register accepted.") {
            throw;
        }
    }

    std::cout << "All C++17 quantum tests passed.\n";
}

int main() {
    try {
        runTests();
        demonstrateQuantumFundamentals();
    } catch (const std::exception& error) {
        std::cerr << "Execution error: "
                  << error.what() << "\n";

        return 1;
    }

    return 0;
}
