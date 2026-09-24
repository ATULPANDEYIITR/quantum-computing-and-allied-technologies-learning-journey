#include <cmath>
#include <complex>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Hadamard Gate: Creating Superposition
 * =====================================
 *
 * Industry-style case study:
 *
 * A small quantum-circuit analysis engine is implemented using C++17.
 * The engine models a state-vector representation, supports single-qubit
 * Hadamard and Pauli-X gates, CNOT, measurement, validation, circuit
 * execution, probability inspection, and Bell-state preparation.
 *
 * The central problem is to represent and execute a circuit containing
 * quantum operations while preserving normalization and exposing the
 * resulting probability distribution.
 *
 * Qubit convention:
 *   qubit 0 is the least-significant bit of a computational-basis index.
 *
 * Examples:
 *   2-qubit index 0 -> |00>
 *   2-qubit index 1 -> |01>
 *   2-qubit index 2 -> |10>
 *   2-qubit index 3 -> |11>
 *
 * Compile:
 *   g++ -std=c++17 -O2 hadamard_case_study.cpp -o hadamard_case_study
 */

using Complex = std::complex<double>;

constexpr double PI = 3.14159265358979323846;
constexpr double SQRT_TWO = 1.41421356237309504880;
constexpr double H_SCALE = 1.0 / SQRT_TWO;
constexpr double EPSILON = 1e-10;

void printSection(const std::string& title) {
    std::cout << "\n" << std::string(78, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(78, '=') << "\n";
}

bool approximatelyEqual(double a, double b, double tolerance = EPSILON) {
    return std::abs(a - b) <= tolerance;
}

bool approximatelyEqual(
    const Complex& a,
    const Complex& b,
    double tolerance = EPSILON
) {
    return std::abs(a - b) <= tolerance;
}

std::string formatComplex(const Complex& value) {
    const double real = std::abs(value.real()) < EPSILON ? 0.0 : value.real();
    const double imaginary =
        std::abs(value.imag()) < EPSILON ? 0.0 : value.imag();

    std::ostringstream output;

    output << std::fixed << std::setprecision(4);

    if (approximatelyEqual(imaginary, 0.0)) {
        output << real;
        return output.str();
    }

    if (approximatelyEqual(real, 0.0)) {
        output << imaginary << "i";
        return output.str();
    }

    output << real;
    if (imaginary >= 0.0) {
        output << " + " << imaginary << "i";
    } else {
        output << " - " << std::abs(imaginary) << "i";
    }

    return output.str();
}

class QuantumRegister {
private:
    std::size_t qubitCount_;
    std::vector<Complex> amplitudes_;

    void validateQubit(std::size_t qubit) const {
        if (qubit >= qubitCount_) {
            throw std::out_of_range(
                "Qubit index " + std::to_string(qubit) +
                " is outside the register."
            );
        }
    }

    std::size_t stateCount() const {
        return amplitudes_.size();
    }

public:
    explicit QuantumRegister(std::size_t qubitCount)
        : qubitCount_(qubitCount),
          amplitudes_(std::size_t{1} << qubitCount, Complex{0.0, 0.0}) {

        if (qubitCount == 0) {
            throw std::invalid_argument(
                "A register must contain at least one qubit."
            );
        }

        /*
         * The state vector requires 2^n complex values.
         * Limiting the educational simulator prevents accidental memory
         * exhaustion. A production simulator would need a more sophisticated
         * memory-management strategy.
         */
        if (qubitCount > 20) {
            throw std::invalid_argument(
                "This educational simulator supports at most 20 qubits."
            );
        }

        amplitudes_[0] = Complex{1.0, 0.0};
    }

    std::size_t qubitCount() const {
        return qubitCount_;
    }

    std::string stateLabel(std::size_t index) const {
        std::string label(qubitCount_, '0');

        for (std::size_t qubit = 0; qubit < qubitCount_; ++qubit) {
            const bool bitIsOne = (index & (std::size_t{1} << qubit)) != 0;
            label[qubitCount_ - 1 - qubit] = bitIsOne ? '1' : '0';
        }

        return label;
    }

    double totalProbability() const {
        double total = 0.0;

        for (const Complex& amplitude : amplitudes_) {
            total += std::norm(amplitude);
        }

        return total;
    }

    void validateNormalization() const {
        if (!approximatelyEqual(totalProbability(), 1.0, 1e-8)) {
            throw std::runtime_error(
                "State-vector normalization invariant was violated."
            );
        }
    }

    const std::vector<Complex>& amplitudes() const {
        return amplitudes_;
    }

    void applyHadamard(std::size_t qubit) {
        validateQubit(qubit);

        /*
         * For every pair differing only in the target bit:
         *
         * a' = (a + b) / sqrt(2)
         * b' = (a - b) / sqrt(2)
         *
         * Each pair is processed exactly once.
         */
        const std::size_t mask = std::size_t{1} << qubit;
        std::vector<Complex> next = amplitudes_;

        for (std::size_t index = 0; index < stateCount(); ++index) {
            if ((index & mask) != 0) {
                continue;
            }

            const std::size_t pairedIndex = index | mask;
            const Complex a = amplitudes_[index];
            const Complex b = amplitudes_[pairedIndex];

            next[index] = (a + b) * H_SCALE;
            next[pairedIndex] = (a - b) * H_SCALE;
        }

        amplitudes_ = std::move(next);
        validateNormalization();
    }

    void applyPauliX(std::size_t qubit) {
        validateQubit(qubit);

        const std::size_t mask = std::size_t{1} << qubit;

        for (std::size_t index = 0; index < stateCount(); ++index) {
            if ((index & mask) != 0) {
                continue;
            }

            const std::size_t pairedIndex = index | mask;
            std::swap(amplitudes_[index], amplitudes_[pairedIndex]);
        }

        validateNormalization();
    }

    void applyPauliZ(std::size_t qubit) {
        validateQubit(qubit);

        const std::size_t mask = std::size_t{1} << qubit;

        for (std::size_t index = 0; index < stateCount(); ++index) {
            if ((index & mask) != 0) {
                amplitudes_[index] *= -1.0;
            }
        }

        validateNormalization();
    }

    void applyCNOT(std::size_t control, std::size_t target) {
        validateQubit(control);
        validateQubit(target);

        if (control == target) {
            throw std::invalid_argument(
                "CNOT control and target must be different."
            );
        }

        const std::size_t controlMask = std::size_t{1} << control;
        const std::size_t targetMask = std::size_t{1} << target;

        /*
         * A CNOT swaps target=0 and target=1 amplitudes only when
         * the control bit is 1.
         *
         * This is a permutation, so it preserves normalization exactly
         * apart from floating-point representation.
         */
        for (std::size_t index = 0; index < stateCount(); ++index) {
            const bool controlIsOne = (index & controlMask) != 0;
            const bool targetIsZero = (index & targetMask) == 0;

            if (controlIsOne && targetIsZero) {
                const std::size_t pairedIndex = index | targetMask;
                std::swap(amplitudes_[index], amplitudes_[pairedIndex]);
            }
        }

        validateNormalization();
    }

    std::string measure(std::mt19937_64& generator) {
        std::uniform_real_distribution<double> distribution(0.0, 1.0);
        const double randomValue = distribution(generator);

        double cumulative = 0.0;

        for (std::size_t index = 0; index < stateCount(); ++index) {
            cumulative += std::norm(amplitudes_[index]);

            if (randomValue < cumulative) {
                const std::string result = stateLabel(index);

                std::fill(
                    amplitudes_.begin(),
                    amplitudes_.end(),
                    Complex{0.0, 0.0}
                );

                amplitudes_[index] = Complex{1.0, 0.0};
                return result;
            }
        }

        /*
         * Floating-point rounding can make cumulative probability slightly
         * smaller than 1. Selecting the final state provides a safe fallback.
         */
        const std::size_t finalIndex = stateCount() - 1;

        std::fill(
            amplitudes_.begin(),
            amplitudes_.end(),
            Complex{0.0, 0.0}
        );

        amplitudes_[finalIndex] = Complex{1.0, 0.0};
        return stateLabel(finalIndex);
    }

    std::vector<std::pair<std::string, Complex>> nonZeroStates(
        double threshold = 1e-10
    ) const {
        std::vector<std::pair<std::string, Complex>> result;

        for (std::size_t index = 0; index < stateCount(); ++index) {
            if (std::abs(amplitudes_[index]) > threshold) {
                result.emplace_back(
                    stateLabel(index),
                    amplitudes_[index]
                );
            }
        }

        return result;
    }

    std::unordered_map<std::string, double> probabilities() const {
        std::unordered_map<std::string, double> result;

        for (std::size_t index = 0; index < stateCount(); ++index) {
            result[stateLabel(index)] = std::norm(amplitudes_[index]);
        }

        return result;
    }
};

enum class GateType {
    Hadamard,
    PauliX,
    PauliZ,
    CNOT
};

struct GateOperation {
    GateType type;
    std::size_t firstQubit;
    std::size_t secondQubit = 0;
};

class QuantumCircuit {
private:
    std::size_t qubitCount_;
    std::vector<GateOperation> operations_;

public:
    explicit QuantumCircuit(std::size_t qubitCount)
        : qubitCount_(qubitCount) {
        if (qubitCount == 0) {
            throw std::invalid_argument(
                "A circuit requires at least one qubit."
            );
        }
    }

    void addHadamard(std::size_t qubit) {
        operations_.push_back({
            GateType::Hadamard,
            qubit,
            0
        });
    }

    void addPauliX(std::size_t qubit) {
        operations_.push_back({
            GateType::PauliX,
            qubit,
            0
        });
    }

    void addPauliZ(std::size_t qubit) {
        operations_.push_back({
            GateType::PauliZ,
            qubit,
            0
        });
    }

    void addCNOT(std::size_t control, std::size_t target) {
        operations_.push_back({
            GateType::CNOT,
            control,
            target
        });
    }

    QuantumRegister execute() const {
        QuantumRegister registerState(qubitCount_);

        for (const GateOperation& operation : operations_) {
            switch (operation.type) {
                case GateType::Hadamard:
                    registerState.applyHadamard(operation.firstQubit);
                    break;

                case GateType::PauliX:
                    registerState.applyPauliX(operation.firstQubit);
                    break;

                case GateType::PauliZ:
                    registerState.applyPauliZ(operation.firstQubit);
                    break;

                case GateType::CNOT:
                    registerState.applyCNOT(
                        operation.firstQubit,
                        operation.secondQubit
                    );
                    break;
            }
        }

        return registerState;
    }

    std::size_t operationCount() const {
        return operations_.size();
    }
};

void printRegister(const QuantumRegister& registerState) {
    for (const auto& [label, amplitude] : registerState.nonZeroStates()) {
        std::cout
            << "|" << label << "> "
            << "amplitude=" << std::setw(18)
            << formatComplex(amplitude)
            << " probability="
            << std::fixed << std::setprecision(4)
            << std::norm(amplitude)
            << "\n";
    }
}

void demonstrateSingleQubit() {
    printSection("1. Single-qubit Hadamard transformation");

    QuantumRegister registerState(1);

    std::cout << "Initial state:\n";
    printRegister(registerState);

    registerState.applyHadamard(0);

    std::cout << "\nAfter H:\n";
    printRegister(registerState);

    const auto probabilities = registerState.probabilities();

    if (!approximatelyEqual(probabilities.at("0"), 0.5)) {
        throw std::runtime_error("H|0> probability of |0> is incorrect.");
    }

    if (!approximatelyEqual(probabilities.at("1"), 0.5)) {
        throw std::runtime_error("H|0> probability of |1> is incorrect.");
    }
}

void demonstrateInverse() {
    printSection("2. H^2 = I");

    QuantumRegister registerState(1);

    registerState.applyHadamard(0);
    registerState.applyHadamard(0);

    std::cout << "After H followed by H:\n";
    printRegister(registerState);

    const auto& amplitudes = registerState.amplitudes();

    if (!approximatelyEqual(amplitudes[0], Complex{1.0, 0.0})) {
        throw std::runtime_error("H^2 did not restore |0>.");
    }

    if (!approximatelyEqual(amplitudes[1], Complex{0.0, 0.0})) {
        throw std::runtime_error("H^2 produced an unexpected |1> amplitude.");
    }
}

void demonstrateTwoQubitSuperposition() {
    printSection("3. Two-qubit uniform superposition");

    QuantumRegister registerState(2);

    registerState.applyHadamard(0);
    registerState.applyHadamard(1);

    printRegister(registerState);

    std::cout
        << "\nThe four computational states have equal probability.\n";
}

void demonstrateBellCircuit() {
    printSection("4. Industry-style Bell-state circuit");

    /*
     * Problem:
     * Prepare a two-qubit correlated state that can be repeatedly measured.
     *
     * Circuit:
     *     q0: ---H---●---
     *                |
     *     q1: -------X---
     *
     * Starting from |00>, the result is:
     *
     *     (|00> + |11>) / sqrt(2)
     */
    QuantumCircuit bellCircuit(2);

    bellCircuit.addHadamard(0);
    bellCircuit.addCNOT(0, 1);

    QuantumRegister result = bellCircuit.execute();

    std::cout << "Circuit operations: "
              << bellCircuit.operationCount() << "\n\n";

    printRegister(result);

    const auto probabilities = result.probabilities();

    if (!approximatelyEqual(probabilities.at("00"), 0.5)) {
        throw std::runtime_error("Bell-state |00> probability is incorrect.");
    }

    if (!approximatelyEqual(probabilities.at("11"), 0.5)) {
        throw std::runtime_error("Bell-state |11> probability is incorrect.");
    }

    if (!approximatelyEqual(probabilities.at("01"), 0.0)) {
        throw std::runtime_error("Bell-state |01> should have zero probability.");
    }

    if (!approximatelyEqual(probabilities.at("10"), 0.0)) {
        throw std::runtime_error("Bell-state |10> should have zero probability.");
    }
}

void demonstrateMeasurementStatistics() {
    printSection("5. Bell-state measurement service");

    constexpr std::size_t shots = 10000;

    std::unordered_map<std::string, std::size_t> counts{
        {"00", 0},
        {"01", 0},
        {"10", 0},
        {"11", 0}
    };

    std::mt19937_64 generator(20260924);

    for (std::size_t shot = 0; shot < shots; ++shot) {
        QuantumCircuit bellCircuit(2);
        bellCircuit.addHadamard(0);
        bellCircuit.addCNOT(0, 1);

        QuantumRegister state = bellCircuit.execute();
        const std::string result = state.measure(generator);

        ++counts.at(result);
    }

    for (const auto& state : {"00", "01", "10", "11"}) {
        const double frequency =
            static_cast<double>(counts.at(state)) / shots;

        std::cout
            << state
            << ": " << counts.at(state)
            << " (" << std::fixed << std::setprecision(2)
            << frequency * 100.0 << "%)\n";
    }

    if (counts.at("01") != 0 || counts.at("10") != 0) {
        throw std::runtime_error(
            "An ideal Bell state produced an impossible cross outcome."
        );
    }
}

void demonstratePhase() {
    printSection("6. Relative phase and interference");

    QuantumRegister plusState(1);
    plusState.applyHadamard(0);

    std::cout << "|+>:\n";
    printRegister(plusState);

    QuantumRegister minusState(1);
    minusState.applyPauliX(0);
    minusState.applyHadamard(0);

    std::cout << "\nH|1> = |->:\n";
    printRegister(minusState);

    /*
     * Applying H again converts the phase difference into a computational
     * basis distinction:
     *
     * H|+> = |0>
     * H|-> = |1>
     */
    plusState.applyHadamard(0);
    minusState.applyHadamard(0);

    std::cout << "\nAfter the second H:\n";
    std::cout << "H|+>:\n";
    printRegister(plusState);

    std::cout << "H|->:\n";
    printRegister(minusState);
}

void demonstrateGateComposition() {
    printSection("7. Circuit composition and phase control");

    QuantumCircuit circuit(1);

    /*
     * |0>
     *  X
     * |1>
     *  H
     * |-> 
     *  Z
     * changes the sign structure
     *  H
     * returns information to the computational basis.
     */
    circuit.addPauliX(0);
    circuit.addHadamard(0);
    circuit.addPauliZ(0);
    circuit.addHadamard(0);

    QuantumRegister result = circuit.execute();

    printRegister(result);
}

void demonstrateFailureConditions() {
    printSection("8. Validation and failure conditions");

    try {
        QuantumRegister invalid(0);
        (void)invalid;
        std::cout << "Unexpected success.\n";
    } catch (const std::exception& error) {
        std::cout << "Invalid register rejected: "
                  << error.what() << "\n";
    }

    try {
        QuantumRegister registerState(2);
        registerState.applyHadamard(2);
        std::cout << "Unexpected success.\n";
    } catch (const std::exception& error) {
        std::cout << "Invalid qubit rejected: "
                  << error.what() << "\n";
    }

    try {
        QuantumRegister registerState(2);
        registerState.applyCNOT(0, 0);
        std::cout << "Unexpected success.\n";
    } catch (const std::exception& error) {
        std::cout << "Invalid CNOT rejected: "
                  << error.what() << "\n";
    }

    try {
        QuantumRegister tooLarge(21);
        (void)tooLarge;
        std::cout << "Unexpected success.\n";
    } catch (const std::exception& error) {
        std::cout << "Oversized simulation rejected: "
                  << error.what() << "\n";
    }
}

void demonstratePerformanceModel() {
    printSection("9. State-vector performance model");

    std::cout
        << "Number of qubits | State amplitudes | Approximate growth\n";

    for (std::size_t qubits = 1; qubits <= 12; ++qubits) {
        const std::size_t states = std::size_t{1} << qubits;

        std::cout
            << std::setw(16) << qubits
            << " | "
            << std::setw(16) << states
            << " | 2^" << qubits
            << "\n";
    }

    std::cout
        << "\nA dense state-vector representation requires O(2^n) memory.\n"
        << "A one-qubit gate update generally requires O(2^n) work.\n"
        << "CNOT is also O(2^n) in this representation.\n"
        << "The circuit description itself can be much smaller than the\n"
        << "classical memory required to explicitly simulate its state.\n";
}

void demonstrateMeasurementCollapse() {
    printSection("10. Measurement collapse");

    QuantumRegister state(1);
    state.applyHadamard(0);

    std::mt19937_64 generator(12345);

    std::cout << "Before measurement:\n";
    printRegister(state);

    const std::string result = state.measure(generator);

    std::cout << "\nMeasured outcome: |" << result << ">\n";
    std::cout << "After measurement:\n";
    printRegister(state);

    const auto probabilities = state.probabilities();

    if (!approximatelyEqual(probabilities.at(result), 1.0)) {
        throw std::runtime_error(
            "Measurement did not collapse the state correctly."
        );
    }
}

int main() {
    try {
        std::cout << "HADAMARD GATE — CREATING SUPERPOSITION\n";
        std::cout << "C++17 quantum-circuit case study\n";

        demonstrateSingleQubit();
        demonstrateInverse();
        demonstrateTwoQubitSuperposition();
        demonstrateBellCircuit();
        demonstrateMeasurementStatistics();
        demonstratePhase();
        demonstrateGateComposition();
        demonstrateFailureConditions();
        demonstratePerformanceModel();
        demonstrateMeasurementCollapse();

        printSection("11. Architectural invariants");

        std::cout
            << "State invariant: sum(|amplitude|^2) = 1.\n"
            << "Gate operations transform amplitudes without violating\n"
            << "normalization when represented by unitary transformations.\n"
            << "Measurement converts the probabilistic state into a basis\n"
            << "state and therefore changes the register.\n"
            << "Qubit ordering is explicitly controlled through bit masks.\n";

        std::cout
            << "\nAll case-study demonstrations completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "\nFatal execution error: "
            << error.what()
            << "\n";

        return 1;
    }
}
