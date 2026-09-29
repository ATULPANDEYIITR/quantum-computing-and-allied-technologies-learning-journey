/*
 * SWAP and Controlled-SWAP (Fredkin) Gates
 * =========================================
 *
 * C++17 case study:
 *
 * A quantum-network routing simulator models a small quantum data-processing
 * system in which logical qubit states must be exchanged and conditionally
 * exchanged.
 *
 * The implementation demonstrates:
 *   - computational-basis states
 *   - complex amplitudes
 *   - state-vector simulation
 *   - SWAP
 *   - controlled-SWAP / Fredkin
 *   - measurement probabilities
 *   - circuit composition
 *   - validation and failure conditions
 *   - SWAP decomposition through CNOT
 *   - resource complexity
 *
 * Compile:
 *   g++ -std=c++17 -O2 swap_fredkin_case_study.cpp -o swap_fredkin
 *
 * Run:
 *   ./swap_fredkin
 */

#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <algorithm>

using Complex = std::complex<double>;
using StateVector = std::vector<Complex>;

constexpr double EPSILON = 1e-10;


// ============================================================================
// 1. State-vector fundamentals
// ============================================================================

class QuantumState {
private:
    std::size_t qubitCount_;
    StateVector amplitudes_;

public:
    QuantumState(std::size_t qubitCount, StateVector amplitudes)
        : qubitCount_(qubitCount),
          amplitudes_(std::move(amplitudes)) {
        if (qubitCount_ == 0) {
            throw std::invalid_argument(
                "A quantum state must contain at least one qubit."
            );
        }

        const std::size_t expectedDimension =
            std::size_t{1} << qubitCount_;

        if (amplitudes_.size() != expectedDimension) {
            throw std::invalid_argument(
                "State-vector dimension does not match qubit count."
            );
        }

        if (std::abs(norm()) < EPSILON) {
            throw std::invalid_argument(
                "The zero vector cannot represent a quantum state."
            );
        }

        normalize();
    }

    std::size_t qubitCount() const {
        return qubitCount_;
    }

    std::size_t dimension() const {
        return amplitudes_.size();
    }

    const StateVector& amplitudes() const {
        return amplitudes_;
    }

    double norm() const {
        double squaredNorm = 0.0;

        for (const Complex& amplitude : amplitudes_) {
            squaredNorm += std::norm(amplitude);
        }

        return std::sqrt(squaredNorm);
    }

    void normalize() {
        const double currentNorm = norm();

        if (currentNorm < EPSILON) {
            throw std::invalid_argument(
                "Cannot normalize a zero vector."
            );
        }

        for (Complex& amplitude : amplitudes_) {
            amplitude /= currentNorm;
        }
    }

    static QuantumState basisState(const std::string& bits) {
        if (bits.empty()) {
            throw std::invalid_argument(
                "Basis state cannot be empty."
            );
        }

        for (char bit : bits) {
            if (bit != '0' && bit != '1') {
                throw std::invalid_argument(
                    "Basis state must contain only 0 and 1."
                );
            }
        }

        const std::size_t qubitCount = bits.size();
        const std::size_t dimension =
            std::size_t{1} << qubitCount;

        StateVector amplitudes(
            dimension,
            Complex{0.0, 0.0}
        );

        std::size_t index = 0;

        for (char bit : bits) {
            index = (index << 1) + static_cast<std::size_t>(
                bit - '0'
            );
        }

        amplitudes[index] = Complex{1.0, 0.0};

        return QuantumState(
            qubitCount,
            std::move(amplitudes)
        );
    }

    static QuantumState uniformSuperposition(
        std::size_t qubitCount
    ) {
        if (qubitCount == 0) {
            throw std::invalid_argument(
                "Superposition requires at least one qubit."
            );
        }

        const std::size_t dimension =
            std::size_t{1} << qubitCount;

        const double amplitude =
            1.0 / std::sqrt(
                static_cast<double>(dimension)
            );

        StateVector amplitudes(
            dimension,
            Complex{amplitude, 0.0}
        );

        return QuantumState(
            qubitCount,
            std::move(amplitudes)
        );
    }

    static std::string basisLabel(
        std::size_t index,
        std::size_t qubitCount
    ) {
        std::string result(qubitCount, '0');

        for (std::size_t q = 0; q < qubitCount; ++q) {
            const std::size_t shift =
                qubitCount - 1 - q;

            result[q] =
                ((index >> shift) & 1U) ? '1' : '0';
        }

        return result;
    }

    void print(
        const std::string& title,
        double threshold = EPSILON
    ) const {
        std::cout << "\n" << title << "\n";

        bool printed = false;

        for (std::size_t index = 0;
             index < amplitudes_.size();
             ++index) {

            if (std::abs(amplitudes_[index]) > threshold) {
                if (printed) {
                    std::cout << " + ";
                }

                std::cout
                    << "("
                    << std::fixed
                    << std::setprecision(4)
                    << amplitudes_[index]
                    << ")|"
                    << basisLabel(index, qubitCount_)
                    << ">";

                printed = true;
            }
        }

        if (!printed) {
            std::cout << "0";
        }

        std::cout << "\n";
    }

    std::vector<double> probabilities() const {
        std::vector<double> result;
        result.reserve(amplitudes_.size());

        for (const Complex& amplitude : amplitudes_) {
            result.push_back(std::norm(amplitude));
        }

        return result;
    }

    std::string measure(
        std::mt19937& generator
    ) const {
        std::vector<double> probability =
            probabilities();

        std::uniform_real_distribution<double> distribution(
            0.0,
            1.0
        );

        const double randomValue = distribution(generator);

        double cumulative = 0.0;

        for (std::size_t index = 0;
             index < probability.size();
             ++index) {

            cumulative += probability[index];

            if (randomValue <= cumulative) {
                return basisLabel(
                    index,
                    qubitCount_
                );
            }
        }

        return basisLabel(
            probability.size() - 1,
            qubitCount_
        );
    }
};


// ============================================================================
// 2. Qubit indexing and basis permutations
// ============================================================================

int getBit(
    std::size_t index,
    std::size_t qubitCount,
    std::size_t qubit
) {
    if (qubit >= qubitCount) {
        throw std::out_of_range(
            "Qubit index is outside the circuit."
        );
    }

    const std::size_t shift =
        qubitCount - 1 - qubit;

    return static_cast<int>(
        (index >> shift) & 1U
    );
}

std::size_t replaceBit(
    std::size_t index,
    std::size_t qubitCount,
    std::size_t qubit,
    int value
) {
    if (qubit >= qubitCount) {
        throw std::out_of_range(
            "Qubit index is outside the circuit."
        );
    }

    if (value != 0 && value != 1) {
        throw std::invalid_argument(
            "Qubit value must be zero or one."
        );
    }

    const std::size_t shift =
        qubitCount - 1 - qubit;

    const std::size_t mask =
        std::size_t{1} << shift;

    if (value == 1) {
        return index | mask;
    }

    return index & ~mask;
}

std::size_t swapBasisIndex(
    std::size_t index,
    std::size_t qubitCount,
    std::size_t first,
    std::size_t second
) {
    if (first >= qubitCount ||
        second >= qubitCount) {
        throw std::out_of_range(
            "SWAP qubit index is invalid."
        );
    }

    if (first == second) {
        return index;
    }

    const int firstValue =
        getBit(index, qubitCount, first);

    const int secondValue =
        getBit(index, qubitCount, second);

    if (firstValue == secondValue) {
        return index;
    }

    index = replaceBit(
        index,
        qubitCount,
        first,
        secondValue
    );

    index = replaceBit(
        index,
        qubitCount,
        second,
        firstValue
    );

    return index;
}


// ============================================================================
// 3. Generic permutation gate
// ============================================================================

template <typename Mapping>
QuantumState applyPermutation(
    const QuantumState& state,
    Mapping mapping
) {
    StateVector result(
        state.dimension(),
        Complex{0.0, 0.0}
    );

    const StateVector& input =
        state.amplitudes();

    for (std::size_t source = 0;
         source < input.size();
         ++source) {

        const std::size_t destination =
            mapping(source);

        if (destination >= result.size()) {
            throw std::runtime_error(
                "Gate mapping produced an invalid state index."
            );
        }

        result[destination] += input[source];
    }

    return QuantumState(
        state.qubitCount(),
        std::move(result)
    );
}


// ============================================================================
// 4. SWAP
// ============================================================================

QuantumState swapGate(
    const QuantumState& state,
    std::size_t first,
    std::size_t second
) {
    return applyPermutation(
        state,
        [&](std::size_t index) {
            return swapBasisIndex(
                index,
                state.qubitCount(),
                first,
                second
            );
        }
    );
}


// ============================================================================
// 5. Controlled-SWAP / Fredkin
// ============================================================================

QuantumState controlledSwapGate(
    const QuantumState& state,
    std::size_t control,
    std::size_t first,
    std::size_t second
) {
    if (control == first ||
        control == second ||
        first == second) {
        throw std::invalid_argument(
            "Fredkin control and target qubits must be distinct."
        );
    }

    if (control >= state.qubitCount() ||
        first >= state.qubitCount() ||
        second >= state.qubitCount()) {
        throw std::out_of_range(
            "Fredkin qubit index is invalid."
        );
    }

    return applyPermutation(
        state,
        [&](std::size_t index) {
            if (
                getBit(
                    index,
                    state.qubitCount(),
                    control
                ) == 1
            ) {
                return swapBasisIndex(
                    index,
                    state.qubitCount(),
                    first,
                    second
                );
            }

            return index;
        }
    );
}


// ============================================================================
// 6. CNOT for gate decomposition
// ============================================================================

QuantumState cnotGate(
    const QuantumState& state,
    std::size_t control,
    std::size_t target
) {
    if (control == target) {
        throw std::invalid_argument(
            "CNOT control and target must differ."
        );
    }

    return applyPermutation(
        state,
        [&](std::size_t index) {
            if (
                getBit(
                    index,
                    state.qubitCount(),
                    control
                ) == 1
            ) {
                const int targetValue =
                    getBit(
                        index,
                        state.qubitCount(),
                        target
                    );

                return replaceBit(
                    index,
                    state.qubitCount(),
                    target,
                    1 - targetValue
                );
            }

            return index;
        }
    );
}

QuantumState swapViaCNOT(
    const QuantumState& state,
    std::size_t first,
    std::size_t second
) {
    QuantumState result =
        cnotGate(
            state,
            first,
            second
        );

    result =
        cnotGate(
            result,
            second,
            first
        );

    result =
        cnotGate(
            result,
            first,
            second
        );

    return result;
}


// ============================================================================
// 7. Circuit abstraction
// ============================================================================

enum class GateType {
    SWAP,
    CONTROLLED_SWAP
};

struct Operation {
    GateType type;
    std::vector<std::size_t> qubits;
};

class QuantumCircuit {
private:
    std::size_t qubitCount_;
    std::vector<Operation> operations_;

    void validateQubit(
        std::size_t qubit
    ) const {
        if (qubit >= qubitCount_) {
            throw std::out_of_range(
                "Qubit is outside the circuit."
            );
        }
    }

public:
    explicit QuantumCircuit(
        std::size_t qubitCount
    )
        : qubitCount_(qubitCount) {

        if (qubitCount == 0) {
            throw std::invalid_argument(
                "Circuit must contain at least one qubit."
            );
        }
    }

    void addSwap(
        std::size_t first,
        std::size_t second
    ) {
        validateQubit(first);
        validateQubit(second);

        operations_.push_back(
            Operation{
                GateType::SWAP,
                {first, second}
            }
        );
    }

    void addControlledSwap(
        std::size_t control,
        std::size_t first,
        std::size_t second
    ) {
        validateQubit(control);
        validateQubit(first);
        validateQubit(second);

        if (control == first ||
            control == second ||
            first == second) {
            throw std::invalid_argument(
                "Fredkin qubits must be distinct."
            );
        }

        operations_.push_back(
            Operation{
                GateType::CONTROLLED_SWAP,
                {
                    control,
                    first,
                    second
                }
            }
        );
    }

    QuantumState run(
        const QuantumState& initial
    ) const {
        if (
            initial.qubitCount() != qubitCount_
        ) {
            throw std::invalid_argument(
                "Initial state does not match circuit width."
            );
        }

        QuantumState state = initial;

        for (const Operation& operation :
             operations_) {

            if (operation.type ==
                GateType::SWAP) {

                state = swapGate(
                    state,
                    operation.qubits[0],
                    operation.qubits[1]
                );
            } else {
                state = controlledSwapGate(
                    state,
                    operation.qubits[0],
                    operation.qubits[1],
                    operation.qubits[2]
                );
            }
        }

        return state;
    }

    void print() const {
        std::cout << "\nCircuit operations:\n";

        for (std::size_t i = 0;
             i < operations_.size();
             ++i) {

            const Operation& operation =
                operations_[i];

            std::cout
                << "  "
                << (i + 1)
                << ". ";

            if (
                operation.type ==
                GateType::SWAP
            ) {
                std::cout
                    << "SWAP("
                    << operation.qubits[0]
                    << ", "
                    << operation.qubits[1]
                    << ")";
            } else {
                std::cout
                    << "CSWAP("
                    << operation.qubits[0]
                    << ", "
                    << operation.qubits[1]
                    << ", "
                    << operation.qubits[2]
                    << ")";
            }

            std::cout << "\n";
        }
    }
};


// ============================================================================
// 8. State comparison
// ============================================================================

bool statesEqual(
    const QuantumState& first,
    const QuantumState& second
) {
    if (
        first.qubitCount() !=
        second.qubitCount()
    ) {
        return false;
    }

    const auto& firstAmplitudes =
        first.amplitudes();

    const auto& secondAmplitudes =
        second.amplitudes();

    for (std::size_t i = 0;
         i < firstAmplitudes.size();
         ++i) {

        if (
            std::abs(
                firstAmplitudes[i] -
                secondAmplitudes[i]
            ) > EPSILON
        ) {
            return false;
        }
    }

    return true;
}


// ============================================================================
// 9. Case-study helpers
// ============================================================================

void printBasisTruthTable() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "SWAP BASIS-STATE BEHAVIOR\n"
        << "============================================================\n";

    const std::vector<std::string> inputs = {
        "00",
        "01",
        "10",
        "11"
    };

    for (const auto& input : inputs) {
        QuantumState state =
            QuantumState::basisState(input);

        QuantumState result =
            swapGate(state, 0, 1);

        std::size_t destination = 0;

        const auto& amplitudes =
            result.amplitudes();

        for (std::size_t i = 0;
             i < amplitudes.size();
             ++i) {
            if (std::abs(amplitudes[i]) > EPSILON) {
                destination = i;
                break;
            }
        }

        std::cout
            << "|"
            << input
            << "> -> |"
            << QuantumState::basisLabel(
                destination,
                2
            )
            << ">\n";
    }
}

void printFredkinTruthTable() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "FREDKIN BASIS-STATE BEHAVIOR\n"
        << "============================================================\n";

    const std::vector<std::string> inputs = {
        "000",
        "001",
        "010",
        "011",
        "100",
        "101",
        "110",
        "111"
    };

    for (const auto& input : inputs) {
        QuantumState state =
            QuantumState::basisState(input);

        QuantumState result =
            controlledSwapGate(
                state,
                0,
                1,
                2
            );

        std::size_t destination = 0;

        for (
            std::size_t i = 0;
            i < result.amplitudes().size();
            ++i
        ) {
            if (
                std::abs(
                    result.amplitudes()[i]
                ) > EPSILON
            ) {
                destination = i;
                break;
            }
        }

        std::cout
            << "|"
            << input
            << "> -> |"
            << QuantumState::basisLabel(
                destination,
                3
            )
            << ">\n";
    }
}


// ============================================================================
// 10. Realistic case study: conditional quantum-network routing
// ============================================================================

/*
 * Scenario
 * --------
 *
 * Imagine a three-channel quantum routing unit:
 *
 *   q0 = routing decision
 *   q1 = payload channel A
 *   q2 = payload channel B
 *
 * The routing rule is:
 *
 *   q0 = 0: preserve A and B
 *   q0 = 1: exchange A and B
 *
 * A classical controller could measure q0 first, but that would destroy
 * coherent control. The Fredkin gate instead performs the conditional
 * exchange without measuring the control.
 *
 * This is the central architectural value demonstrated by controlled-SWAP.
 */

class QuantumRouter {
private:
    std::size_t controlQubit_;
    std::size_t channelA_;
    std::size_t channelB_;

public:
    QuantumRouter(
        std::size_t controlQubit,
        std::size_t channelA,
        std::size_t channelB
    )
        : controlQubit_(controlQubit),
          channelA_(channelA),
          channelB_(channelB) {

        if (
            controlQubit_ == channelA_ ||
            controlQubit_ == channelB_ ||
            channelA_ == channelB_
        ) {
            throw std::invalid_argument(
                "Router requires three distinct qubits."
            );
        }
    }

    QuantumState route(
        const QuantumState& state
    ) const {
        return controlledSwapGate(
            state,
            controlQubit_,
            channelA_,
            channelB_
        );
    }
};

void demonstrateRouterCaseStudy() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "QUANTUM ROUTING CASE STUDY\n"
        << "============================================================\n";

    /*
     * The router receives a coherent routing decision:
     *
     *   (|0>|01> + |1>|01>) / sqrt(2)
     *
     * When the control is |0>, payload remains |01>.
     * When the control is |1>, payload becomes |10>.
     *
     * Therefore the output is:
     *
     *   (|001> + |110>) / sqrt(2)
     *
     * This is a coherent conditional exchange.
     */
    const double amplitude =
        1.0 / std::sqrt(2.0);

    StateVector input(8, Complex{0.0, 0.0});

    input[1] = Complex{amplitude, 0.0}; // |001>
    input[5] = Complex{amplitude, 0.0}; // |101>

    QuantumState state(
        3,
        std::move(input)
    );

    state.print(
        "Router input state"
    );

    QuantumRouter router(
        0,
        1,
        2
    );

    QuantumState output =
        router.route(state);

    output.print(
        "Router output state"
    );

    StateVector expectedAmplitudes(
        8,
        Complex{0.0, 0.0}
    );

    expectedAmplitudes[1] =
        Complex{amplitude, 0.0};

    expectedAmplitudes[6] =
        Complex{amplitude, 0.0};

    QuantumState expected(
        3,
        std::move(expectedAmplitudes)
    );

    std::cout
        << "Expected transformation verified: "
        << std::boolalpha
        << statesEqual(output, expected)
        << "\n";
}


// ============================================================================
// 11. Edge cases and error handling
// ============================================================================

void demonstrateValidation() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "VALIDATION AND FAILURE CONDITIONS\n"
        << "============================================================\n";

    try {
        QuantumState state =
            QuantumState::basisState("101");

        QuantumState result =
            swapGate(
                state,
                0,
                3
            );

        (void)result;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid qubit rejected: "
            << error.what()
            << "\n";
    }

    try {
        QuantumState state =
            QuantumState::basisState("101");

        QuantumState result =
            controlledSwapGate(
                state,
                0,
                0,
                2
            );

        (void)result;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid Fredkin topology rejected: "
            << error.what()
            << "\n";
    }

    try {
        QuantumState state =
            QuantumState::basisState("101");

        QuantumState result =
            controlledSwapGate(
                state,
                0,
                1,
                3
            );

        (void)result;
    } catch (const std::exception& error) {
        std::cout
            << "Out-of-range Fredkin target rejected: "
            << error.what()
            << "\n";
    }

    /*
     * SWAP(q,q) is mathematically the identity.
     * This is useful as a boundary condition when a circuit generator
     * accidentally produces the same source and destination.
     */
    QuantumState original =
        QuantumState::basisState("101");

    QuantumState sameQubit =
        swapGate(
            original,
            1,
            1
        );

    std::cout
        << "SWAP(q,q) is identity: "
        << std::boolalpha
        << statesEqual(
            original,
            sameQubit
        )
        << "\n";
}


// ============================================================================
// 12. Algebraic and performance properties
// ============================================================================

void demonstrateGateProperties() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "ALGEBRAIC PROPERTIES\n"
        << "============================================================\n";

    QuantumState state =
        QuantumState::uniformSuperposition(4);

    QuantumState swapOnce =
        swapGate(
            state,
            0,
            3
        );

    QuantumState swapTwice =
        swapGate(
            swapOnce,
            0,
            3
        );

    std::cout
        << "SWAP^2 = I: "
        << std::boolalpha
        << statesEqual(
            state,
            swapTwice
        )
        << "\n";

    QuantumState fredkinOnce =
        controlledSwapGate(
            state,
            0,
            1,
            2
        );

    QuantumState fredkinTwice =
        controlledSwapGate(
            fredkinOnce,
            0,
            1,
            2
        );

    std::cout
        << "Fredkin^2 = I: "
        << statesEqual(
            state,
            fredkinTwice
        )
        << "\n";

    std::cout
        << "Norm before: "
        << std::setprecision(12)
        << state.norm()
        << "\n";

    std::cout
        << "Norm after SWAP: "
        << swapOnce.norm()
        << "\n";

    std::cout
        << "Norm after Fredkin: "
        << fredkinOnce.norm()
        << "\n";
}

void demonstrateSwapDecomposition() {
    std::cout
        << "\n"
        << "============================================================\n"
        << "SWAP DECOMPOSITION INTO THREE CNOT GATES\n"
        << "============================================================\n";

    StateVector amplitudes = {
        Complex{1.0, 0.0},
        Complex{0.0, 2.0},
        Complex{1.0, -1.0},
        Complex{0.5, 0.0}
    };

    QuantumState state(
        2,
        std::move(amplitudes)
    );

    QuantumState direct =
        swapGate(
            state,
            0,
            1
        );

    QuantumState decomposed =
        swapViaCNOT(
            state,
            0,
            1
        );

    direct.print(
        "Direct SWAP"
    );

    decomposed.print(
        "Three-CNOT implementation"
    );

    std::cout
        << "Equivalent states: "
        << std::boolalpha
        << statesEqual(
            direct,
            decomposed
        )
        << "\n";
}


// ============================================================================
// 13. Main program
// ============================================================================

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "SWAP & CONTROLLED-SWAP MULTI-QUBIT CASE STUDY\n"
            << "============================================================\n";

        printBasisTruthTable();
        printFredkinTruthTable();
        demonstrateRouterCaseStudy();
        demonstrateSwapDecomposition();
        demonstrateGateProperties();
        demonstrateValidation();

        std::mt19937 generator(
            std::random_device{}()
        );

        QuantumState measurementState =
            QuantumState::uniformSuperposition(3);

        std::cout
            << "\n"
            << "============================================================\n"
            << "MEASUREMENT SAMPLE\n"
            << "============================================================\n";

        measurementState.print(
            "Uniform three-qubit state"
        );

        std::cout
            << "One sampled measurement result: |"
            << measurementState.measure(generator)
            << ">\n";

        std::cout
            << "\n"
            << "============================================================\n"
            << "MULTI-OPERATION CIRCUIT\n"
            << "============================================================\n";

        QuantumCircuit circuit(3);

        circuit.addSwap(0, 2);
        circuit.addControlledSwap(1, 0, 2);
        circuit.addSwap(0, 1);

        circuit.print();

        QuantumState initial =
            QuantumState::uniformSuperposition(3);

        QuantumState finalState =
            circuit.run(initial);

        finalState.print(
            "Circuit output"
        );

        std::cout
            << "\n"
            << "============================================================\n"
            << "RESOURCE CONSIDERATIONS\n"
            << "============================================================\n";

        std::cout
            << "For n qubits, a classical state-vector simulator stores 2^n "
            << "complex amplitudes.\n";

        std::cout
            << "Direct SWAP/Fredkin simulation visits O(2^n) amplitudes.\n";

        std::cout
            << "Memory consumption is therefore O(2^n), despite the "
            << "physical gates acting on only two or three qubits.\n";

        std::cout
            << "A real quantum processor does not classically materialize "
            << "the complete state vector.\n";

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
