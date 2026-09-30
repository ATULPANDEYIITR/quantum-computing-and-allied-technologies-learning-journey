/*
 * Quantum Circuits | Circuit Construction Fundamentals
 *
 * C++17 case study:
 * A repository-independent quantum-circuit construction and merge-style
 * execution engine for a small state-vector simulator.
 *
 * The program models a realistic circuit compiler boundary:
 * - a circuit is constructed from validated operations
 * - operations are represented as typed records
 * - a validation phase checks structural constraints
 * - a state-vector executor applies gates in program order
 * - measurement probabilities determine observable outcomes
 * - a simple optimization pass removes adjacent self-inverse gates
 *
 * Compile:
 *   g++ -std=c++17 -O2 quantum_circuit.cpp -o quantum_circuit
 *
 * Run:
 *   ./quantum_circuit
 */

#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Complex = std::complex<double>;
using Matrix2 = std::array<std::array<Complex, 2>, 2>;

constexpr double PI = 3.14159265358979323846;

struct Operation {
    enum class Kind {
        Single,
        Controlled
    };

    Kind kind;
    std::string name;
    int target;
    int control;
    Matrix2 matrix;
    double parameter;

    static Operation single(
        std::string name,
        int target,
        Matrix2 matrix,
        double parameter = 0.0
    ) {
        return {
            Kind::Single,
            std::move(name),
            target,
            -1,
            matrix,
            parameter
        };
    }

    static Operation controlled(
        std::string name,
        int control,
        int target,
        Matrix2 matrix
    ) {
        return {
            Kind::Controlled,
            std::move(name),
            target,
            control,
            matrix,
            0.0
        };
    }
};

Matrix2 identity() {
    return {{
        {{Complex(1.0, 0.0), Complex(0.0, 0.0)}},
        {{Complex(0.0, 0.0), Complex(1.0, 0.0)}}
    }};
}

Matrix2 pauliX() {
    return {{
        {{Complex(0.0), Complex(1.0)}},
        {{Complex(1.0), Complex(0.0)}}
    }};
}

Matrix2 pauliZ() {
    return {{
        {{Complex(1.0), Complex(0.0)}},
        {{Complex(0.0), Complex(-1.0)}}
    }};
}

Matrix2 hadamard() {
    const double s = 1.0 / std::sqrt(2.0);

    return {{
        {{Complex(s), Complex(s)}},
        {{Complex(s), Complex(-s)}}
    }};
}

Matrix2 rotationY(double theta) {
    const double c = std::cos(theta / 2.0);
    const double s = std::sin(theta / 2.0);

    return {{
        {{Complex(c), Complex(-s)}},
        {{Complex(s), Complex(c)}}
    }};
}

Matrix2 rotationZ(double theta) {
    return {{
        {
            Complex(std::cos(theta / 2.0), -std::sin(theta / 2.0)),
            Complex(0.0)
        },
        {
            Complex(0.0),
            Complex(std::cos(theta / 2.0), std::sin(theta / 2.0))
        }
    }};
}

std::string basisLabel(std::size_t index, int qubits) {
    std::string result(qubits, '0');

    for (int q = 0; q < qubits; ++q) {
        const int bit = (index >> (qubits - 1 - q)) & 1;
        result[q] = static_cast<char>('0' + bit);
    }

    return result;
}

class CircuitValidationError : public std::runtime_error {
public:
    explicit CircuitValidationError(const std::string& message)
        : std::runtime_error(message) {}
};

class QuantumCircuit {
private:
    int qubits_;
    std::string name_;
    std::vector<Operation> operations_;

    void validateQubit(int qubit) const {
        if (qubit < 0 || qubit >= qubits_) {
            throw CircuitValidationError(
                "Qubit index " + std::to_string(qubit) +
                " is outside the circuit."
            );
        }
    }

    void validateDistinct(int first, int second) const {
        validateQubit(first);
        validateQubit(second);

        if (first == second) {
            throw CircuitValidationError(
                "Controlled operation requires distinct control and target."
            );
        }
    }

public:
    explicit QuantumCircuit(int qubits, std::string name = "unnamed")
        : qubits_(qubits), name_(std::move(name)) {

        if (qubits <= 0) {
            throw CircuitValidationError(
                "A quantum circuit must contain at least one qubit."
            );
        }

        /*
         * A state vector requires 2^n complex amplitudes. Keeping the
         * educational case study below 13 qubits avoids accidental memory
         * consumption while preserving realistic exponential scaling.
         */
        if (qubits > 12) {
            throw CircuitValidationError(
                "This state-vector case study supports at most 12 qubits."
            );
        }
    }

    int qubits() const {
        return qubits_;
    }

    const std::string& name() const {
        return name_;
    }

    QuantumCircuit& h(int target) {
        validateQubit(target);
        operations_.push_back(
            Operation::single("H", target, hadamard())
        );
        return *this;
    }

    QuantumCircuit& x(int target) {
        validateQubit(target);
        operations_.push_back(
            Operation::single("X", target, pauliX())
        );
        return *this;
    }

    QuantumCircuit& z(int target) {
        validateQubit(target);
        operations_.push_back(
            Operation::single("Z", target, pauliZ())
        );
        return *this;
    }

    QuantumCircuit& ry(int target, double theta) {
        validateQubit(target);

        if (!std::isfinite(theta)) {
            throw CircuitValidationError(
                "RY requires a finite rotation angle."
            );
        }

        operations_.push_back(
            Operation::single("RY", target, rotationY(theta), theta)
        );
        return *this;
    }

    QuantumCircuit& rz(int target, double theta) {
        validateQubit(target);

        if (!std::isfinite(theta)) {
            throw CircuitValidationError(
                "RZ requires a finite rotation angle."
            );
        }

        operations_.push_back(
            Operation::single("RZ", target, rotationZ(theta), theta)
        );
        return *this;
    }

    QuantumCircuit& cx(int control, int target) {
        validateDistinct(control, target);

        operations_.push_back(
            Operation::controlled("CX", control, target, pauliX())
        );
        return *this;
    }

    QuantumCircuit& cz(int control, int target) {
        validateDistinct(control, target);

        operations_.push_back(
            Operation::controlled("CZ", control, target, pauliZ())
        );
        return *this;
    }

    bool empty() const {
        return operations_.empty();
    }

    const std::vector<Operation>& operations() const {
        return operations_;
    }

    void printArchitecture() const {
        std::cout << "\nCircuit: " << name_
                  << " | qubits=" << qubits_
                  << " | operations=" << operations_.size()
                  << "\n";

        for (std::size_t i = 0; i < operations_.size(); ++i) {
            const Operation& op = operations_[i];

            std::cout << "  [" << i << "] " << op.name;

            if (op.kind == Operation::Kind::Single) {
                std::cout << " q" << op.target;
            } else {
                std::cout << " q" << op.control
                          << " -> q" << op.target;
            }

            if (op.name == "RY" || op.name == "RZ") {
                std::cout << " theta=" << std::fixed
                          << std::setprecision(6)
                          << op.parameter;
            }

            std::cout << '\n';
        }
    }

    /*
     * The optimization is deliberately conservative. X, H, Z and CX are
     * self-inverse, so applying the exact same operation twice consecutively
     * is equivalent to doing nothing. We only remove adjacent identical
     * operations and never reorder gates, which preserves circuit semantics.
     */
    void removeAdjacentSelfInversePairs() {
        std::vector<Operation> optimized;

        auto sameOperation = [](const Operation& a, const Operation& b) {
            return a.name == b.name &&
                   a.target == b.target &&
                   a.control == b.control &&
                   a.kind == b.kind;
        };

        for (const Operation& current : operations_) {
            if (!optimized.empty() &&
                sameOperation(optimized.back(), current) &&
                (
                    current.name == "X" ||
                    current.name == "H" ||
                    current.name == "Z" ||
                    current.name == "CX" ||
                    current.name == "CZ"
                )) {
                optimized.pop_back();
            } else {
                optimized.push_back(current);
            }
        }

        operations_ = std::move(optimized);
    }

    std::vector<Complex> execute() const {
        const std::size_t dimension =
            static_cast<std::size_t>(1ULL << qubits_);

        std::vector<Complex> state(dimension, Complex(0.0));
        state[0] = Complex(1.0);

        for (const Operation& op : operations_) {
            if (op.kind == Operation::Kind::Single) {
                applySingle(state, op.target, op.matrix);
            } else {
                applyControlled(
                    state,
                    op.control,
                    op.target,
                    op.matrix
                );
            }
        }

        return state;
    }

private:
    void applySingle(
        std::vector<Complex>& state,
        int target,
        const Matrix2& matrix
    ) const {
        const std::size_t targetBit =
            static_cast<std::size_t>(1ULL << (qubits_ - 1 - target));

        for (std::size_t index = 0; index < state.size(); ++index) {
            if ((index & targetBit) != 0) {
                continue;
            }

            const std::size_t zeroIndex = index;
            const std::size_t oneIndex = index | targetBit;

            const Complex a0 = state[zeroIndex];
            const Complex a1 = state[oneIndex];

            state[zeroIndex] =
                matrix[0][0] * a0 +
                matrix[0][1] * a1;

            state[oneIndex] =
                matrix[1][0] * a0 +
                matrix[1][1] * a1;
        }
    }

    void applyControlled(
        std::vector<Complex>& state,
        int control,
        int target,
        const Matrix2& matrix
    ) const {
        const std::size_t controlBit =
            static_cast<std::size_t>(1ULL << (qubits_ - 1 - control));

        const std::size_t targetBit =
            static_cast<std::size_t>(1ULL << (qubits_ - 1 - target));

        for (std::size_t index = 0; index < state.size(); ++index) {
            if ((index & controlBit) == 0 ||
                (index & targetBit) != 0) {
                continue;
            }

            const std::size_t zeroIndex = index;
            const std::size_t oneIndex = index | targetBit;

            const Complex a0 = state[zeroIndex];
            const Complex a1 = state[oneIndex];

            state[zeroIndex] =
                matrix[0][0] * a0 +
                matrix[0][1] * a1;

            state[oneIndex] =
                matrix[1][0] * a0 +
                matrix[1][1] * a1;
        }
    }
};

std::map<std::string, double> probabilities(
    const std::vector<Complex>& state,
    int qubits
) {
    std::map<std::string, double> result;
    double total = 0.0;

    for (std::size_t index = 0; index < state.size(); ++index) {
        const double probability = std::norm(state[index]);
        result[basisLabel(index, qubits)] = probability;
        total += probability;
    }

    if (std::abs(total - 1.0) > 1e-9) {
        throw std::runtime_error(
            "State-vector normalization check failed."
        );
    }

    return result;
}

void printState(const std::vector<Complex>& state, int qubits) {
    std::cout << "Non-zero state amplitudes:\n";

    for (std::size_t index = 0; index < state.size(); ++index) {
        if (std::norm(state[index]) > 1e-10) {
            std::cout << "  |"
                      << basisLabel(index, qubits)
                      << "> = "
                      << std::fixed
                      << std::setprecision(5)
                      << state[index]
                      << '\n';
        }
    }
}

std::map<std::string, int> sample(
    const std::map<std::string, double>& distribution,
    int shots,
    std::uint64_t seed
) {
    if (shots <= 0) {
        throw std::invalid_argument("shots must be positive.");
    }

    std::vector<std::string> states;
    std::vector<double> weights;

    for (const auto& [state, probability] : distribution) {
        states.push_back(state);
        weights.push_back(probability);
    }

    std::mt19937_64 generator(seed);
    std::discrete_distribution<std::size_t> chooser(
        weights.begin(),
        weights.end()
    );

    std::map<std::string, int> counts;

    for (int shot = 0; shot < shots; ++shot) {
        ++counts[states[chooser(generator)]];
    }

    return counts;
}

void bellCaseStudy() {
    std::cout << "\n=== CASE STUDY: ENTANGLED TWO-QUBIT REGISTER ===\n";

    QuantumCircuit circuit(2, "bell-pair");

    /*
     * H creates equal amplitude for |0> and |1> on q0. CX then conditionally
     * flips q1 when q0 is |1>, producing the correlated state
     * (|00> + |11>) / sqrt(2).
     */
    circuit.h(0).cx(0, 1);

    circuit.printArchitecture();

    const auto state = circuit.execute();
    printState(state, circuit.qubits());

    const auto distribution =
        probabilities(state, circuit.qubits());

    std::cout << "Measurement distribution:\n";

    for (const auto& [basis, probability] : distribution) {
        if (probability > 1e-10) {
            std::cout << "  "
                      << basis
                      << " -> "
                      << std::setprecision(4)
                      << probability
                      << '\n';
        }
    }

    std::cout << "5000 simulated shots:\n";

    const auto counts = sample(distribution, 5000, 20260930);

    for (const auto& [basis, count] : counts) {
        std::cout << "  "
                  << basis
                  << ": "
                  << count
                  << '\n';
    }
}

void parameterizedCaseStudy() {
    std::cout << "\n=== CASE STUDY: PARAMETERIZED CIRCUIT ===\n";

    QuantumCircuit circuit(3, "parameterized-register");

    circuit
        .ry(0, PI / 4.0)
        .ry(1, PI / 3.0)
        .h(2)
        .cx(0, 1)
        .cz(1, 2)
        .rz(2, PI / 5.0);

    circuit.printArchitecture();

    const auto state = circuit.execute();
    const auto distribution =
        probabilities(state, circuit.qubits());

    std::cout << "Observable basis states:\n";

    for (const auto& [basis, probability] : distribution) {
        if (probability > 0.01) {
            std::cout << "  |"
                      << basis
                      << "> : "
                      << std::fixed
                      << std::setprecision(4)
                      << probability
                      << '\n';
        }
    }
}

void optimizationCaseStudy() {
    std::cout << "\n=== CASE STUDY: CONSERVATIVE CIRCUIT OPTIMIZATION ===\n";

    QuantumCircuit circuit(2, "optimization-example");

    circuit
        .h(0)
        .x(1)
        .x(1)
        .cx(0, 1)
        .cx(0, 1)
        .z(0);

    std::cout << "Before optimization:\n";
    circuit.printArchitecture();

    const auto before = circuit.execute();

    circuit.removeAdjacentSelfInversePairs();

    std::cout << "After optimization:\n";
    circuit.printArchitecture();

    const auto after = circuit.execute();

    if (before.size() != after.size()) {
        throw std::runtime_error(
            "Optimization changed state-vector dimensions."
        );
    }

    for (std::size_t i = 0; i < before.size(); ++i) {
        if (std::abs(before[i] - after[i]) > 1e-9) {
            throw std::runtime_error(
                "Optimization changed circuit semantics."
            );
        }
    }

    std::cout << "Semantic-equivalence check passed.\n";
}

void validationCaseStudy() {
    std::cout << "\n=== CASE STUDY: CONSTRUCTION VALIDATION ===\n";

    try {
        QuantumCircuit invalid(2, "invalid");
        invalid.cx(0, 0);
    } catch (const CircuitValidationError& error) {
        std::cout << "Rejected invalid CX: "
                  << error.what()
                  << '\n';
    }

    try {
        QuantumCircuit invalid(2, "invalid-rotation");
        invalid.ry(0, std::numeric_limits<double>::quiet_NaN());
    } catch (const CircuitValidationError& error) {
        std::cout << "Rejected invalid rotation: "
                  << error.what()
                  << '\n';
    }

    try {
        QuantumCircuit invalid(0, "empty-register");
    } catch (const CircuitValidationError& error) {
        std::cout << "Rejected invalid register: "
                  << error.what()
                  << '\n';
    }
}

void scalingAnalysis() {
    std::cout << "\n=== STATE-VECTOR SCALING ===\n";

    for (int qubits = 1; qubits <= 10; ++qubits) {
        const std::size_t amplitudes =
            static_cast<std::size_t>(1ULL << qubits);

        /*
         * std::complex<double> is commonly 16 bytes on mainstream platforms,
         * though the language standard does not require this exact size.
         */
        const std::size_t bytes =
            amplitudes * sizeof(Complex);

        std::cout
            << qubits
            << " qubits -> "
            << amplitudes
            << " amplitudes -> "
            << std::fixed
            << std::setprecision(2)
            << static_cast<double>(bytes) / 1024.0
            << " KiB assuming "
            << sizeof(Complex)
            << " bytes per amplitude\n";
    }
}

void runAssertions() {
    QuantumCircuit xCircuit(1, "x-test");
    xCircuit.x(0);

    const auto xDistribution =
        probabilities(xCircuit.execute(), 1);

    if (std::abs(xDistribution.at("1") - 1.0) > 1e-9) {
        throw std::runtime_error("X gate assertion failed.");
    }

    QuantumCircuit bell(2, "bell-test");
    bell.h(0).cx(0, 1);

    const auto bellDistribution =
        probabilities(bell.execute(), 2);

    if (std::abs(bellDistribution.at("00") - 0.5) > 1e-9 ||
        std::abs(bellDistribution.at("11") - 0.5) > 1e-9 ||
        bellDistribution.at("01") > 1e-9 ||
        bellDistribution.at("10") > 1e-9) {
        throw std::runtime_error("Bell-state assertion failed.");
    }

    std::cout << "C++ circuit assertions passed.\n";
}

int main() {
    try {
        std::cout
            << "QUANTUM CIRCUITS: CIRCUIT CONSTRUCTION FUNDAMENTALS\n"
            << "====================================================\n";

        runAssertions();
        bellCaseStudy();
        parameterizedCaseStudy();
        optimizationCaseStudy();
        validationCaseStudy();
        scalingAnalysis();

        std::cout << "\nCase study completed successfully.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal circuit error: "
            << error.what()
            << '\n';
        return 1;
    }
}
