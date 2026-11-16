#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Variational Quantum Circuit Governance and Optimization Engine
 *
 * C++17 implementation of:
 * - Parameterized quantum circuits
 * - State-vector simulation
 * - RX, RY, RZ and CNOT gates
 * - Hamiltonian evaluation
 * - Parameter-shift gradients
 * - Gradient-descent optimization
 * - Measurement sampling
 * - Numerical validation
 *
 * No external libraries.
 */

using Complex = complex<double>;
using StateVector = vector<Complex>;

// ============================================================
// 1. Domain types
// ============================================================

enum class GateType {
    RX,
    RY,
    RZ,
    CNOT
};

enum class OptimizationStatus {
    CREATED,
    RUNNING,
    COMPLETED,
    FAILED
};

struct CircuitConfig {
    int qubits = 2;
    int layers = 2;
    int seed = 42;

    void validate() const {
        if (qubits < 1 || qubits > 12) {
            throw invalid_argument("Qubit count must be 1-12.");
        }

        if (layers < 1 || layers > 20) {
            throw invalid_argument("Layer count must be 1-20.");
        }
    }
};

struct Gate {
    GateType type;
    int target;
    int control = -1;
    int parameterIndex = -1;
};

struct OptimizationResult {
    double initialEnergy = 0.0;
    double finalEnergy = 0.0;
    vector<double> parameters;
    vector<double> history;
    int iterations = 0;
    bool converged = false;
};

// ============================================================
// 2. Quantum state-vector simulator
// ============================================================

class QuantumRegister {

private:
    int qubits;
    int dimension;
    StateVector amplitudes;

public:

    explicit QuantumRegister(int numberOfQubits)
        : qubits(numberOfQubits),
          dimension(1 << numberOfQubits),
          amplitudes(dimension, Complex(0.0, 0.0)) {

        if (qubits < 1 || qubits > 12) {
            throw invalid_argument("Unsupported qubit count.");
        }

        amplitudes[0] = Complex(1.0, 0.0);
    }

    int size() const {
        return qubits;
    }

    const StateVector& getAmplitudes() const {
        return amplitudes;
    }

    void applySingleQubitGate(
        int qubit,
        const Complex& m00,
        const Complex& m01,
        const Complex& m10,
        const Complex& m11
    ) {
        if (qubit < 0 || qubit >= qubits) {
            throw out_of_range("Invalid qubit.");
        }

        const int mask = 1 << qubit;

        for (int index = 0; index < dimension; ++index) {
            if (index & mask) {
                continue;
            }

            const int partner = index | mask;

            Complex a = amplitudes[index];
            Complex b = amplitudes[partner];

            amplitudes[index] = m00 * a + m01 * b;
            amplitudes[partner] = m10 * a + m11 * b;
        }
    }

    void applyRX(int qubit, double theta) {
        const double c = cos(theta / 2.0);
        const double s = sin(theta / 2.0);

        const Complex imaginary(0.0, -1.0);

        applySingleQubitGate(
            qubit,
            c,
            imaginary * s,
            imaginary * s,
            c
        );
    }

    void applyRY(int qubit, double theta) {
        const double c = cos(theta / 2.0);
        const double s = sin(theta / 2.0);

        applySingleQubitGate(
            qubit,
            c,
            -s,
            s,
            c
        );
    }

    void applyRZ(int qubit, double theta) {
        const Complex first(
            cos(theta / 2.0),
            -sin(theta / 2.0)
        );

        const Complex second(
            cos(theta / 2.0),
            sin(theta / 2.0)
        );

        applySingleQubitGate(
            qubit,
            first,
            Complex(0.0, 0.0),
            Complex(0.0, 0.0),
            second
        );
    }

    void applyCNOT(int control, int target) {
        if (control < 0 || control >= qubits ||
            target < 0 || target >= qubits ||
            control == target) {
            throw invalid_argument("Invalid CNOT configuration.");
        }

        const int controlMask = 1 << control;
        const int targetMask = 1 << target;

        for (int index = 0; index < dimension; ++index) {
            if ((index & controlMask) &&
                !(index & targetMask)) {

                const int partner = index | targetMask;

                swap(
                    amplitudes[index],
                    amplitudes[partner]
                );
            }
        }
    }

    vector<double> probabilities() const {
        vector<double> result;

        result.reserve(dimension);

        for (const auto& amplitude : amplitudes) {
            result.push_back(norm(amplitude));
        }

        return result;
    }

    double expectationZ(int qubit) const {
        if (qubit < 0 || qubit >= qubits) {
            throw out_of_range("Invalid observable qubit.");
        }

        const int mask = 1 << qubit;
        double result = 0.0;

        for (int index = 0; index < dimension; ++index) {
            const double eigenvalue =
                (index & mask) ? -1.0 : 1.0;

            result += eigenvalue * norm(amplitudes[index]);
        }

        return result;
    }

    double expectationZZ(int first, int second) const {
        if (first < 0 || second < 0 ||
            first >= qubits || second >= qubits ||
            first == second) {
            throw invalid_argument("Invalid ZZ observable.");
        }

        const int firstMask = 1 << first;
        const int secondMask = 1 << second;

        double result = 0.0;

        for (int index = 0; index < dimension; ++index) {
            const double a =
                (index & firstMask) ? 1.0 : -1.0;

            const double b =
                (index & secondMask) ? 1.0 : -1.0;

            result += a * b * norm(amplitudes[index]);
        }

        return result;
    }

    double totalProbability() const {
        const auto values = probabilities();

        return accumulate(
            values.begin(),
            values.end(),
            0.0
        );
    }
};

// ============================================================
// 3. Circuit construction
// ============================================================

class VariationalCircuit {

private:
    CircuitConfig config;
    vector<Gate> gates;
    int parameterCount = 0;

    void build() {
        for (int layer = 0; layer < config.layers; ++layer) {

            for (int qubit = 0; qubit < config.qubits; ++qubit) {
                gates.push_back({
                    GateType::RY,
                    qubit,
                    -1,
                    parameterCount++
                });

                gates.push_back({
                    GateType::RZ,
                    qubit,
                    -1,
                    parameterCount++
                });
            }

            for (int qubit = 0;
                 qubit < config.qubits - 1;
                 ++qubit) {

                gates.push_back({
                    GateType::CNOT,
                    qubit + 1,
                    qubit,
                    -1
                });
            }

            if (config.qubits > 2) {
                gates.push_back({
                    GateType::CNOT,
                    0,
                    config.qubits - 1,
                    -1
                });
            }
        }
    }

public:

    explicit VariationalCircuit(CircuitConfig configuration)
        : config(configuration) {

        config.validate();
        build();
    }

    int getParameterCount() const {
        return parameterCount;
    }

    const CircuitConfig& getConfig() const {
        return config;
    }

    void validateParameters(
        const vector<double>& parameters
    ) const {

        if (static_cast<int>(parameters.size()) != parameterCount) {
            throw invalid_argument("Parameter count mismatch.");
        }

        for (double value : parameters) {
            if (!isfinite(value)) {
                throw invalid_argument("Non-finite parameter.");
            }
        }
    }

    QuantumRegister execute(
        const vector<double>& parameters
    ) const {

        validateParameters(parameters);

        QuantumRegister state(config.qubits);

        for (const Gate& gate : gates) {
            switch (gate.type) {

                case GateType::RX:
                    state.applyRX(
                        gate.target,
                        parameters[gate.parameterIndex]
                    );
                    break;

                case GateType::RY:
                    state.applyRY(
                        gate.target,
                        parameters[gate.parameterIndex]
                    );
                    break;

                case GateType::RZ:
                    state.applyRZ(
                        gate.target,
                        parameters[gate.parameterIndex]
                    );
                    break;

                case GateType::CNOT:
                    state.applyCNOT(
                        gate.control,
                        gate.target
                    );
                    break;
            }
        }

        return state;
    }

    /*
     * Hamiltonian:
     * H = -sum(Z_i) + 0.5 * Z_0 Z_1
     */
    double energy(
        const vector<double>& parameters
    ) const {

        QuantumRegister state = execute(parameters);

        double result = 0.0;

        for (int qubit = 0; qubit < config.qubits; ++qubit) {
            result -= state.expectationZ(qubit);
        }

        if (config.qubits > 1) {
            result += 0.5 * state.expectationZZ(0, 1);
        }

        return result;
    }
};

// ============================================================
// 4. Parameter-shift differentiation
// ============================================================

vector<double> calculateGradient(
    const VariationalCircuit& circuit,
    const vector<double>& parameters
) {
    circuit.validateParameters(parameters);

    vector<double> gradient(parameters.size());

    for (size_t index = 0; index < parameters.size(); ++index) {
        vector<double> plus = parameters;
        vector<double> minus = parameters;

        plus[index] += M_PI / 2.0;
        minus[index] -= M_PI / 2.0;

        gradient[index] = 0.5 * (
            circuit.energy(plus) -
            circuit.energy(minus)
        );
    }

    return gradient;
}

// ============================================================
// 5. Optimization engine
// ============================================================

class GradientOptimizer {

private:
    double learningRate;
    int maximumIterations;
    double tolerance;

public:

    GradientOptimizer(
        double rate = 0.08,
        int iterations = 150,
        double threshold = 1e-7
    )
        : learningRate(rate),
          maximumIterations(iterations),
          tolerance(threshold) {

        if (!isfinite(rate) || rate <= 0 ||
            iterations <= 0 ||
            threshold <= 0) {
            throw invalid_argument("Invalid optimizer settings.");
        }
    }

    OptimizationResult optimize(
        const VariationalCircuit& circuit,
        const vector<double>& initial
    ) const {

        circuit.validateParameters(initial);

        vector<double> parameters = initial;

        OptimizationResult result;

        result.initialEnergy = circuit.energy(parameters);
        result.history.push_back(result.initialEnergy);

        double rate = learningRate;

        for (int iteration = 1;
             iteration <= maximumIterations;
             ++iteration) {

            const vector<double> gradient =
                calculateGradient(circuit, parameters);

            double squaredNorm = 0.0;

            for (double value : gradient) {
                squaredNorm += value * value;
            }

            const double gradientNorm = sqrt(squaredNorm);

            if (gradientNorm < tolerance) {
                result.converged = true;
                break;
            }

            vector<double> candidate = parameters;

            for (size_t i = 0; i < parameters.size(); ++i) {
                candidate[i] -= rate * gradient[i];
            }

            const double candidateEnergy =
                circuit.energy(candidate);

            if (candidateEnergy >
                result.history.back() + 1e-10) {

                rate *= 0.5;

                if (rate < 1e-8) {
                    break;
                }

                continue;
            }

            parameters = move(candidate);

            result.history.push_back(candidateEnergy);
            result.iterations++;

            if (result.history.size() >= 2) {
                const size_t n = result.history.size();

                if (abs(
                    result.history[n - 1] -
                    result.history[n - 2]
                ) < tolerance) {

                    result.converged = true;
                    break;
                }
            }
        }

        result.parameters = parameters;
        result.finalEnergy = circuit.energy(parameters);

        return result;
    }
};

// ============================================================
// 6. Measurement sampling
// ============================================================

map<string, int> sampleMeasurements(
    const vector<double>& probabilities,
    int shots,
    unsigned int seed
) {
    if (shots <= 0 || probabilities.empty()) {
        throw invalid_argument("Invalid sampling configuration.");
    }

    const double total = accumulate(
        probabilities.begin(),
        probabilities.end(),
        0.0
    );

    if (abs(total - 1.0) > 1e-8) {
        throw runtime_error("Probability normalization failed.");
    }

    for (double probability : probabilities) {
        if (!isfinite(probability) || probability < 0) {
            throw runtime_error("Invalid probability.");
        }
    }

    mt19937 generator(seed);

    discrete_distribution<int> distribution(
        probabilities.begin(),
        probabilities.end()
    );

    map<string, int> counts;

    const int qubits = static_cast<int>(
        log2(probabilities.size())
    );

    for (int shot = 0; shot < shots; ++shot) {
        const int index = distribution(generator);

        string bitstring(qubits, '0');

        for (int bit = 0; bit < qubits; ++bit) {
            if (index & (1 << bit)) {
                bitstring[qubits - bit - 1] = '1';
            }
        }

        counts[bitstring]++;
    }

    return counts;
}

// ============================================================
// 7. Numerical tests
// ============================================================

void verifyBellState() {
    QuantumRegister state(2);

    state.applyRY(0, M_PI / 2.0);
    state.applyCNOT(0, 1);

    const vector<double> probabilities =
        state.probabilities();

    if (abs(probabilities[0] - 0.5) > 1e-9 ||
        abs(probabilities[3] - 0.5) > 1e-9) {

        throw runtime_error("Bell-state test failed.");
    }

    if (abs(state.expectationZZ(0, 1) - 1.0) > 1e-9) {
        throw runtime_error("ZZ expectation test failed.");
    }
}

void verifyGradient(
    const VariationalCircuit& circuit,
    const vector<double>& parameters
) {
    const vector<double> analytical =
        calculateGradient(circuit, parameters);

    const double epsilon = 1e-6;

    for (size_t i = 0; i < parameters.size(); ++i) {
        vector<double> plus = parameters;
        vector<double> minus = parameters;

        plus[i] += epsilon;
        minus[i] -= epsilon;

        const double numerical = (
            circuit.energy(plus) -
            circuit.energy(minus)
        ) / (2.0 * epsilon);

        if (abs(numerical - analytical[i]) > 1e-5) {
            throw runtime_error(
                "Gradient verification failed at parameter " +
                to_string(i)
            );
        }
    }
}

// ============================================================
// 8. Main application
// ============================================================

int main() {

    try {
        cout << fixed << setprecision(8);

        verifyBellState();

        CircuitConfig config;
        config.qubits = 2;
        config.layers = 2;

        VariationalCircuit circuit(config);

        mt19937 generator(config.seed);

        uniform_real_distribution<double> randomAngle(
            -0.5,
            0.5
        );

        vector<double> initialParameters(
            circuit.getParameterCount()
        );

        generate(
            initialParameters.begin(),
            initialParameters.end(),
            [&]() {
                return randomAngle(generator);
            }
        );

        verifyGradient(circuit, initialParameters);

        cout << "VARIATIONAL QUANTUM COMPUTATION\n";
        cout << "================================\n";

        cout << "Qubits: " << config.qubits << '\n';
        cout << "Layers: " << config.layers << '\n';
        cout << "Parameters: "
             << circuit.getParameterCount() << '\n';

        cout << "Initial energy: "
             << circuit.energy(initialParameters) << '\n';

        GradientOptimizer optimizer(0.08, 150);

        OptimizationResult result = optimizer.optimize(
            circuit,
            initialParameters
        );

        cout << "\nOPTIMIZATION RESULTS\n";

        cout << "Initial energy: "
             << result.initialEnergy << '\n';

        cout << "Final energy: "
             << result.finalEnergy << '\n';

        cout << "Iterations: "
             << result.iterations << '\n';

        cout << "Converged: "
             << boolalpha << result.converged << '\n';

        cout << "\nOPTIMIZED PARAMETERS\n";

        for (size_t i = 0; i < result.parameters.size(); ++i) {
            cout << "theta[" << i << "] = "
                 << result.parameters[i] << '\n';
        }

        QuantumRegister finalState = circuit.execute(
            result.parameters
        );

        cout << "\nFINAL STATE PROBABILITIES\n";

        const auto probabilities = finalState.probabilities();

        for (size_t i = 0; i < probabilities.size(); ++i) {
            cout << "State " << i << ": "
                 << probabilities[i] << '\n';
        }

        cout << "\nMEASUREMENT RESULTS\n";

        const auto counts = sampleMeasurements(
            probabilities,
            1000,
            42
        );

        for (const auto& [state, count] : counts) {
            cout << state << " : " << count << '\n';
        }

        if (abs(finalState.totalProbability() - 1.0) > 1e-9) {
            throw runtime_error("State normalization failed.");
        }

        cout << "\nAll tests passed.\n";

    } catch (const exception& error) {
        cerr << "Execution failure: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
