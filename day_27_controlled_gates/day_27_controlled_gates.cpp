/*
 * Controlled Gates: Controlled-X and Controlled Operations
 * =========================================================
 *
 * C++17 case study: a small reversible quantum-control simulator.
 *
 * Scenario
 * --------
 * A quantum information service needs to model a small register used by
 * a reversible computation pipeline. The pipeline must support:
 *
 *   - single-qubit gates,
 *   - controlled-X / CNOT,
 *   - general controlled single-qubit operations,
 *   - controlled phase operations,
 *   - Toffoli gates,
 *   - SWAP decomposition,
 *   - Bell-state preparation,
 *   - measurement,
 *   - validation and circuit inspection.
 *
 * The implementation uses only the C++ standard library.
 *
 * Compile:
 *   g++ -std=c++17 -O2 controlled_gates.cpp -o controlled_gates
 */

#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
#include <functional>
#include <sstream>
#include <map>

using Complex = std::complex<double>;
using State = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double EPSILON = 1e-10;


// ---------------------------------------------------------------------------
// 1. MATRIX HELPERS
// ---------------------------------------------------------------------------

Matrix makeMatrix(std::size_t rows, std::size_t columns) {
    return Matrix(
        rows,
        std::vector<Complex>(columns, Complex(0.0, 0.0))
    );
}

Matrix identityMatrix(std::size_t dimension) {
    Matrix result = makeMatrix(dimension, dimension);

    for (std::size_t i = 0; i < dimension; ++i) {
        result[i][i] = Complex(1.0, 0.0);
    }

    return result;
}

Matrix matrixMultiply(
    const Matrix& left,
    const Matrix& right
) {
    if (left.empty() || right.empty()) {
        throw std::invalid_argument("Matrices cannot be empty.");
    }

    if (left.front().size() != right.size()) {
        throw std::invalid_argument(
            "Matrix dimensions are incompatible."
        );
    }

    Matrix result = makeMatrix(
        left.size(),
        right.front().size()
    );

    for (std::size_t row = 0; row < left.size(); ++row) {
        for (std::size_t column = 0;
             column < right.front().size();
             ++column) {

            Complex value = 0.0;

            for (std::size_t k = 0; k < right.size(); ++k) {
                value += left[row][k] * right[k][column];
            }

            result[row][column] = value;
        }
    }

    return result;
}

State matrixVectorMultiply(
    const Matrix& matrix,
    const State& state
) {
    if (matrix.empty() || matrix.front().size() != state.size()) {
        throw std::invalid_argument(
            "Matrix and vector dimensions are incompatible."
        );
    }

    State result(matrix.size(), Complex(0.0, 0.0));

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0; column < state.size(); ++column) {
            result[row] += matrix[row][column] * state[column];
        }
    }

    return result;
}

Matrix conjugateTranspose(const Matrix& matrix) {
    if (matrix.empty()) {
        return {};
    }

    Matrix result = makeMatrix(
        matrix.front().size(),
        matrix.size()
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0;
             column < matrix.front().size();
             ++column) {

            result[column][row] = std::conj(matrix[row][column]);
        }
    }

    return result;
}

bool isUnitary(const Matrix& matrix) {
    if (matrix.empty() || matrix.size() != matrix.front().size()) {
        return false;
    }

    Matrix product = matrixMultiply(
        conjugateTranspose(matrix),
        matrix
    );

    for (std::size_t row = 0; row < product.size(); ++row) {
        for (std::size_t column = 0;
             column < product.size();
             ++column) {

            Complex expected =
                row == column
                    ? Complex(1.0, 0.0)
                    : Complex(0.0, 0.0);

            if (std::abs(product[row][column] - expected) > 1e-9) {
                return false;
            }
        }
    }

    return true;
}


// ---------------------------------------------------------------------------
// 2. QUANTUM GATES
// ---------------------------------------------------------------------------

Matrix pauliX() {
    Matrix result = makeMatrix(2, 2);

    result[0][1] = 1.0;
    result[1][0] = 1.0;

    return result;
}

Matrix pauliY() {
    Matrix result = makeMatrix(2, 2);

    result[0][1] = Complex(0.0, -1.0);
    result[1][0] = Complex(0.0, 1.0);

    return result;
}

Matrix pauliZ() {
    Matrix result = makeMatrix(2, 2);

    result[0][0] = 1.0;
    result[1][1] = -1.0;

    return result;
}

Matrix hadamard() {
    const double value = 1.0 / std::sqrt(2.0);

    Matrix result = makeMatrix(2, 2);

    result[0][0] = value;
    result[0][1] = value;
    result[1][0] = value;
    result[1][1] = -value;

    return result;
}

Matrix phaseGate(double theta) {
    Matrix result = makeMatrix(2, 2);

    result[0][0] = 1.0;
    result[1][1] = std::polar(1.0, theta);

    return result;
}


// ---------------------------------------------------------------------------
// 3. CONTROLLED MATRIX
// ---------------------------------------------------------------------------

Matrix controlledMatrix(const Matrix& operation) {
    if (
        operation.size() != 2 ||
        operation.front().size() != 2
    ) {
        throw std::invalid_argument(
            "Controlled operation must contain a 2x2 target matrix."
        );
    }

    Matrix result = makeMatrix(4, 4);

    /*
     * Controlled-U:
     *
     *          [ I  0 ]
     *      Uc = [ 0  U ]
     *
     * The upper block corresponds to control=0.
     * The lower block corresponds to control=1.
     */

    result[0][0] = 1.0;
    result[1][1] = 1.0;

    result[2][2] = operation[0][0];
    result[2][3] = operation[0][1];
    result[3][2] = operation[1][0];
    result[3][3] = operation[1][1];

    return result;
}


// ---------------------------------------------------------------------------
// 4. BASIS STATES AND STATE VALIDATION
// ---------------------------------------------------------------------------

std::size_t numberOfQubits(const State& state) {
    if (state.empty()) {
        throw std::invalid_argument("State cannot be empty.");
    }

    const double logarithm =
        std::log2(static_cast<double>(state.size()));

    const auto qubits =
        static_cast<std::size_t>(std::llround(logarithm));

    if ((static_cast<std::size_t>(1) << qubits) != state.size()) {
        throw std::invalid_argument(
            "State size must be a power of two."
        );
    }

    return qubits;
}

State basisState(const std::string& bits) {
    if (bits.empty()) {
        throw std::invalid_argument(
            "Basis-state string cannot be empty."
        );
    }

    for (char bit : bits) {
        if (bit != '0' && bit != '1') {
            throw std::invalid_argument(
                "Basis-state string must contain only 0 and 1."
            );
        }
    }

    const std::size_t dimension =
        static_cast<std::size_t>(1) << bits.size();

    State state(dimension, Complex(0.0, 0.0));

    const std::size_t index =
        static_cast<std::size_t>(std::stoull(bits, nullptr, 2));

    state[index] = Complex(1.0, 0.0);

    return state;
}

std::string basisLabel(
    std::size_t index,
    std::size_t qubits
) {
    std::string result(qubits, '0');

    for (std::size_t position = 0; position < qubits; ++position) {
        const std::size_t bitPosition = qubits - 1 - position;

        if (index & (static_cast<std::size_t>(1) << bitPosition)) {
            result[position] = '1';
        }
    }

    return result;
}

double stateNormSquared(const State& state) {
    double result = 0.0;

    for (const Complex& amplitude : state) {
        result += std::norm(amplitude);
    }

    return result;
}

double stateNorm(const State& state) {
    return std::sqrt(stateNormSquared(state));
}

void validateNormalizedState(const State& state) {
    const double totalProbability = stateNormSquared(state);

    if (std::abs(totalProbability - 1.0) > 1e-9) {
        throw std::invalid_argument(
            "State is not normalized."
        );
    }
}

State normalizeState(const State& state) {
    const double norm = stateNorm(state);

    if (norm < EPSILON) {
        throw std::invalid_argument(
            "Cannot normalize a zero vector."
        );
    }

    State result = state;

    for (Complex& amplitude : result) {
        amplitude /= norm;
    }

    return result;
}


// ---------------------------------------------------------------------------
// 5. OUTPUT HELPERS
// ---------------------------------------------------------------------------

std::string formatComplex(Complex value) {
    const double real = std::abs(value.real()) < EPSILON
        ? 0.0
        : value.real();

    const double imaginary = std::abs(value.imag()) < EPSILON
        ? 0.0
        : value.imag();

    std::ostringstream output;
    output << std::fixed << std::setprecision(6);

    if (imaginary == 0.0) {
        output << real;
    } else if (real == 0.0) {
        output << imaginary << "i";
    } else {
        output << real
               << (imaginary >= 0.0 ? "+" : "")
               << imaginary
               << "i";
    }

    return output.str();
}

void printState(
    const State& state,
    const std::string& title
) {
    if (!title.empty()) {
        std::cout << "\n" << title << "\n";
    }

    const std::size_t qubits = numberOfQubits(state);
    bool printed = false;

    for (std::size_t index = 0; index < state.size(); ++index) {
        if (std::abs(state[index]) > EPSILON) {
            if (printed) {
                std::cout << " + ";
            }

            std::cout
                << "("
                << formatComplex(state[index])
                << ")|"
                << basisLabel(index, qubits)
                << ">";

            printed = true;
        }
    }

    if (!printed) {
        std::cout << "0";
    }

    std::cout << "\n";
}

void printMatrix(
    const Matrix& matrix,
    const std::string& title
) {
    if (!title.empty()) {
        std::cout << "\n" << title << "\n";
    }

    for (const auto& row : matrix) {
        std::cout << "[ ";

        for (const Complex& value : row) {
            std::cout << std::setw(14)
                      << formatComplex(value)
                      << " ";
        }

        std::cout << "]\n";
    }
}


// ---------------------------------------------------------------------------
// 6. DIRECT SINGLE-QUBIT OPERATION
// ---------------------------------------------------------------------------

State applySingleQubitGate(
    const State& state,
    const Matrix& operation,
    std::size_t targetQubit
) {
    const std::size_t qubits = numberOfQubits(state);

    if (operation.size() != 2 || operation.front().size() != 2) {
        throw std::invalid_argument(
            "Single-qubit operation must be 2x2."
        );
    }

    if (targetQubit >= qubits) {
        throw std::out_of_range(
            "Target qubit is outside the register."
        );
    }

    State result = state;

    /*
     * Each target qubit creates pairs of basis indices:
     *
     *     target=0
     *     target=1
     *
     * Applying the 2x2 matrix to each pair is equivalent to applying
     * the gate to the selected qubit of the complete register.
     */
    const std::size_t bitPosition =
        qubits - 1 - targetQubit;

    const std::size_t targetMask =
        static_cast<std::size_t>(1) << bitPosition;

    for (std::size_t baseIndex = 0;
         baseIndex < state.size();
         ++baseIndex) {

        if (baseIndex & targetMask) {
            continue;
        }

        const std::size_t zeroIndex = baseIndex;
        const std::size_t oneIndex =
            baseIndex | targetMask;

        const Complex zeroAmplitude =
            state[zeroIndex];

        const Complex oneAmplitude =
            state[oneIndex];

        result[zeroIndex] =
            operation[0][0] * zeroAmplitude
            + operation[0][1] * oneAmplitude;

        result[oneIndex] =
            operation[1][0] * zeroAmplitude
            + operation[1][1] * oneAmplitude;
    }

    return result;
}


// ---------------------------------------------------------------------------
// 7. GENERAL CONTROLLED OPERATION
// ---------------------------------------------------------------------------

State applyControlledOperation(
    const State& state,
    std::size_t controlQubit,
    std::size_t targetQubit,
    const Matrix& operation
) {
    const std::size_t qubits = numberOfQubits(state);

    if (controlQubit >= qubits) {
        throw std::out_of_range(
            "Control qubit is outside the register."
        );
    }

    if (targetQubit >= qubits) {
        throw std::out_of_range(
            "Target qubit is outside the register."
        );
    }

    if (controlQubit == targetQubit) {
        throw std::invalid_argument(
            "Control and target must be different."
        );
    }

    if (operation.size() != 2 || operation.front().size() != 2) {
        throw std::invalid_argument(
            "Target operation must be 2x2."
        );
    }

    State result = state;

    const std::size_t controlPosition =
        qubits - 1 - controlQubit;

    const std::size_t targetPosition =
        qubits - 1 - targetQubit;

    const std::size_t controlMask =
        static_cast<std::size_t>(1) << controlPosition;

    const std::size_t targetMask =
        static_cast<std::size_t>(1) << targetPosition;

    for (std::size_t baseIndex = 0;
         baseIndex < state.size();
         ++baseIndex) {

        // Process each target pair only once.
        if (baseIndex & targetMask) {
            continue;
        }

        // Control=0 means the operation is identity on this branch.
        if ((baseIndex & controlMask) == 0) {
            continue;
        }

        const std::size_t zeroIndex = baseIndex;
        const std::size_t oneIndex =
            baseIndex | targetMask;

        const Complex zeroAmplitude =
            state[zeroIndex];

        const Complex oneAmplitude =
            state[oneIndex];

        result[zeroIndex] =
            operation[0][0] * zeroAmplitude
            + operation[0][1] * oneAmplitude;

        result[oneIndex] =
            operation[1][0] * zeroAmplitude
            + operation[1][1] * oneAmplitude;
    }

    return result;
}

State applyCX(
    const State& state,
    std::size_t controlQubit,
    std::size_t targetQubit
) {
    return applyControlledOperation(
        state,
        controlQubit,
        targetQubit,
        pauliX()
    );
}


// ---------------------------------------------------------------------------
// 8. TOFFOLI
// ---------------------------------------------------------------------------

State applyToffoli(
    const State& state,
    std::size_t firstControl,
    std::size_t secondControl,
    std::size_t target
) {
    const std::size_t qubits = numberOfQubits(state);

    if (
        firstControl == secondControl ||
        firstControl == target ||
        secondControl == target
    ) {
        throw std::invalid_argument(
            "Toffoli requires three distinct qubits."
        );
    }

    for (std::size_t qubit :
         {firstControl, secondControl, target}) {

        if (qubit >= qubits) {
            throw std::out_of_range(
                "Toffoli qubit is outside the register."
            );
        }
    }

    State result = state;

    const std::size_t firstMask =
        static_cast<std::size_t>(1)
        << (qubits - 1 - firstControl);

    const std::size_t secondMask =
        static_cast<std::size_t>(1)
        << (qubits - 1 - secondControl);

    const std::size_t targetMask =
        static_cast<std::size_t>(1)
        << (qubits - 1 - target);

    for (std::size_t baseIndex = 0;
         baseIndex < state.size();
         ++baseIndex) {

        if (baseIndex & targetMask) {
            continue;
        }

        const bool bothControlsAreOne =
            (baseIndex & firstMask) != 0
            && (baseIndex & secondMask) != 0;

        if (!bothControlsAreOne) {
            continue;
        }

        const std::size_t zeroIndex = baseIndex;
        const std::size_t oneIndex =
            baseIndex | targetMask;

        result[zeroIndex] = state[oneIndex];
        result[oneIndex] = state[zeroIndex];
    }

    return result;
}


// ---------------------------------------------------------------------------
// 9. SWAP USING THREE CX OPERATIONS
// ---------------------------------------------------------------------------

State swapUsingCX(
    const State& state,
    std::size_t firstQubit,
    std::size_t secondQubit
) {
    if (firstQubit == secondQubit) {
        throw std::invalid_argument(
            "SWAP requires two distinct qubits."
        );
    }

    State result = state;

    result = applyCX(
        result,
        firstQubit,
        secondQubit
    );

    result = applyCX(
        result,
        secondQubit,
        firstQubit
    );

    result = applyCX(
        result,
        firstQubit,
        secondQubit
    );

    return result;
}


// ---------------------------------------------------------------------------
// 10. MEASUREMENT
// ---------------------------------------------------------------------------

std::size_t measure(
    const State& state,
    std::mt19937& generator,
    State& collapsedState
) {
    validateNormalizedState(state);

    std::uniform_real_distribution<double> distribution(
        0.0,
        1.0
    );

    const double randomValue = distribution(generator);

    double cumulative = 0.0;

    for (std::size_t index = 0;
         index < state.size();
         ++index) {

        cumulative += std::norm(state[index]);

        if (randomValue <= cumulative) {
            collapsedState.assign(
                state.size(),
                Complex(0.0, 0.0)
            );

            collapsedState[index] =
                Complex(1.0, 0.0);

            return index;
        }
    }

    // Floating-point protection.
    const std::size_t finalIndex =
        state.size() - 1;

    collapsedState.assign(
        state.size(),
        Complex(0.0, 0.0)
    );

    collapsedState[finalIndex] =
        Complex(1.0, 0.0);

    return finalIndex;
}


// ---------------------------------------------------------------------------
// 11. CIRCUIT MODEL
// ---------------------------------------------------------------------------

struct GateOperation {
    std::string name;
    std::function<State(const State&)> operation;
};

class QuantumCircuit {
private:
    std::size_t qubits_;
    State state_;
    std::vector<GateOperation> operations_;

public:
    explicit QuantumCircuit(std::size_t qubits)
        : qubits_(qubits),
          state_(basisState(std::string(qubits, '0'))) {

        if (qubits == 0) {
            throw std::invalid_argument(
                "Circuit must contain at least one qubit."
            );
        }
    }

    void addSingleQubitGate(
        const std::string& name,
        const Matrix& operation,
        std::size_t target
    ) {
        operations_.push_back({
            name,
            [operation, target](const State& state) {
                return applySingleQubitGate(
                    state,
                    operation,
                    target
                );
            }
        });
    }

    void addControlledGate(
        const std::string& name,
        const Matrix& operation,
        std::size_t control,
        std::size_t target
    ) {
        operations_.push_back({
            name,
            [operation, control, target](const State& state) {
                return applyControlledOperation(
                    state,
                    control,
                    target,
                    operation
                );
            }
        });
    }

    State run() {
        for (const GateOperation& gate : operations_) {
            state_ = gate.operation(state_);
        }

        return state_;
    }

    void printCircuit() const {
        std::cout << "\nCircuit operations:\n";

        for (std::size_t index = 0;
             index < operations_.size();
             ++index) {

            std::cout
                << index + 1
                << ". "
                << operations_[index].name
                << "\n";
        }
    }

    const State& state() const {
        return state_;
    }
};


// ---------------------------------------------------------------------------
// 12. CASE STUDY A: BELL-STATE PREPARATION
// ---------------------------------------------------------------------------

State prepareBellState() {
    State state = basisState("00");

    state = applySingleQubitGate(
        state,
        hadamard(),
        0
    );

    state = applyCX(
        state,
        0,
        1
    );

    return state;
}

void demonstrateBellState() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nBELL STATE CASE STUDY\n"
              << std::string(72, '=')
              << "\n";

    const State state = prepareBellState();

    printState(
        state,
        "Prepared state"
    );

    std::cout << "\nMeasurement probabilities:\n";

    for (std::size_t index = 0;
         index < state.size();
         ++index) {

        const double probability =
            std::norm(state[index]);

        if (probability > EPSILON) {
            std::cout
                << "|"
                << basisLabel(index, 2)
                << "> : "
                << probability
                << "\n";
        }
    }

    std::cout
        << "\nThe CX gate transforms the |10> branch into |11> "
           "while leaving the |00> branch unchanged.\n";
}


// ---------------------------------------------------------------------------
// 13. CASE STUDY B: REVERSIBLE CONTROLLED DATA TRANSFORM
// ---------------------------------------------------------------------------

void demonstrateReversibleLogic() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nREVERSIBLE CONDITIONAL DATA TRANSFORM\n"
              << std::string(72, '=')
              << "\n";

    std::cout
        << "For computational-basis inputs, CX implements:\n"
        << "target_out = target XOR control\n\n";

    for (int control = 0; control <= 1; ++control) {
        for (int target = 0; target <= 1; ++target) {
            const int output = target ^ control;

            std::cout
                << "control="
                << control
                << ", target="
                << target
                << " -> target_out="
                << output
                << "\n";
        }
    }

    std::cout
        << "\nBecause XOR is reversible, CX is self-inverse.\n";
}


// ---------------------------------------------------------------------------
// 14. CASE STUDY C: CONTROLLED PHASE PROCESSING
// ---------------------------------------------------------------------------

void demonstrateControlledPhase() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nCONTROLLED PHASE PROCESSING\n"
              << std::string(72, '=')
              << "\n";

    const Matrix phase =
        phaseGate(std::acos(-1.0) / 2.0);

    const Matrix controlledPhase =
        controlledMatrix(phase);

    printMatrix(
        controlledPhase,
        "Controlled phase matrix"
    );

    State state = basisState("11");

    state = matrixVectorMultiply(
        controlledPhase,
        state
    );

    printState(
        state,
        "Controlled phase applied to |11>"
    );

    std::cout
        << "\nThe computational probability remains unchanged by a "
           "pure phase on a basis state, but relative phase can affect "
           "later interference.\n";
}


// ---------------------------------------------------------------------------
// 15. CASE STUDY D: SWAP DECOMPOSITION
// ---------------------------------------------------------------------------

void demonstrateSwapDecomposition() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nSWAP FROM CONTROLLED-X OPERATIONS\n"
              << std::string(72, '=')
              << "\n";

    for (const std::string& bits :
         {"00", "01", "10", "11"}) {

        const State input = basisState(bits);

        const State output =
            swapUsingCX(input, 0, 1);

        std::size_t outputIndex = 0;

        for (std::size_t index = 0;
             index < output.size();
             ++index) {

            if (std::abs(output[index]) > EPSILON) {
                outputIndex = index;
                break;
            }
        }

        std::cout
            << "|"
            << bits
            << "> -> |"
            << basisLabel(outputIndex, 2)
            << ">\n";
    }

    std::cout
        << "\nDecomposition:\n"
        << "CX(q0,q1)\n"
        << "CX(q1,q0)\n"
        << "CX(q0,q1)\n";
}


// ---------------------------------------------------------------------------
// 16. CASE STUDY E: TOFFOLI
// ---------------------------------------------------------------------------

void demonstrateToffoli() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nTOFFOLI CASE STUDY\n"
              << std::string(72, '=')
              << "\n";

    std::cout
        << "The target flips only when both control qubits equal 1.\n\n";

    for (const std::string& bits :
         {
             "000", "001", "010", "011",
             "100", "101", "110", "111"
         }) {

        const State output =
            applyToffoli(
                basisState(bits),
                0,
                1,
                2
            );

        std::size_t outputIndex = 0;

        for (std::size_t index = 0;
             index < output.size();
             ++index) {

            if (std::abs(output[index]) > EPSILON) {
                outputIndex = index;
                break;
            }
        }

        std::cout
            << "|"
            << bits
            << "> -> |"
            << basisLabel(outputIndex, 3)
            << ">\n";
    }
}


// ---------------------------------------------------------------------------
// 17. CASE STUDY F: CIRCUIT ARCHITECTURE
// ---------------------------------------------------------------------------

void demonstrateCircuitArchitecture() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nCIRCUIT ARCHITECTURE\n"
              << std::string(72, '=')
              << "\n";

    QuantumCircuit circuit(2);

    circuit.addSingleQubitGate(
        "H(q0)",
        hadamard(),
        0
    );

    circuit.addControlledGate(
        "CX(q0 -> q1)",
        pauliX(),
        0,
        1
    );

    circuit.printCircuit();

    const State output = circuit.run();

    printState(
        output,
        "Circuit output"
    );
}


// ---------------------------------------------------------------------------
// 18. VALIDATION AND FAILURE CONDITIONS
// ---------------------------------------------------------------------------

void demonstrateValidation() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nVALIDATION AND FAILURE CONDITIONS\n"
              << std::string(72, '=')
              << "\n";

    struct Test {
        std::string description;
        std::function<void()> action;
    };

    const std::vector<Test> tests = {
        {
            "Control equals target",
            [] {
                applyCX(
                    basisState("00"),
                    0,
                    0
                );
            }
        },
        {
            "Control outside register",
            [] {
                applyCX(
                    basisState("00"),
                    2,
                    1
                );
            }
        },
        {
            "Target outside register",
            [] {
                applyCX(
                    basisState("00"),
                    0,
                    2
                );
            }
        },
        {
            "Invalid basis-state input",
            [] {
                basisState("012");
            }
        },
        {
            "Zero vector normalization",
            [] {
                normalizeState({
                    Complex(0.0),
                    Complex(0.0)
                });
            }
        }
    };

    for (const Test& test : tests) {
        try {
            test.action();

            std::cout
                << test.description
                << ": validation FAILED\n";
        }
        catch (const std::exception& error) {
            std::cout
                << test.description
                << ": correctly rejected -> "
                << error.what()
                << "\n";
        }
    }
}


// ---------------------------------------------------------------------------
// 19. UNITARITY VERIFICATION
// ---------------------------------------------------------------------------

void demonstrateUnitarity() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nUNITARITY VERIFICATION\n"
              << std::string(72, '=')
              << "\n";

    const Matrix x = pauliX();
    const Matrix y = pauliY();
    const Matrix z = pauliZ();
    const Matrix h = hadamard();

    const std::map<std::string, Matrix> gates = {
        {"X", x},
        {"Y", y},
        {"Z", z},
        {"H", h},
        {"CX", controlledMatrix(x)},
        {"CY", controlledMatrix(y)},
        {"CZ", controlledMatrix(z)}
    };

    for (const auto& [name, matrix] : gates) {
        std::cout
            << std::setw(3)
            << name
            << " -> unitary = "
            << std::boolalpha
            << isUnitary(matrix)
            << "\n";
    }
}


// ---------------------------------------------------------------------------
// 20. PERFORMANCE ANALYSIS
// ---------------------------------------------------------------------------

void demonstratePerformanceConsiderations() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nPERFORMANCE CONSIDERATIONS\n"
              << std::string(72, '=')
              << "\n";

    std::cout
        << "Qubits | State amplitudes\n";

    for (std::size_t qubits = 1;
         qubits <= 15;
         ++qubits) {

        const std::size_t amplitudes =
            static_cast<std::size_t>(1) << qubits;

        std::cout
            << std::setw(6)
            << qubits
            << " | "
            << amplitudes
            << "\n";
    }

    std::cout
        << "\nState-vector memory scales as O(2^n).\n";

    std::cout
        << "A full operator matrix requires O(4^n) complex entries "
           "for an n-qubit operator.\n";

    std::cout
        << "The direct controlled-operation implementation avoids "
           "constructing that full matrix and updates only affected "
           "amplitude pairs.\n";

    std::cout
        << "For production simulators, contiguous storage, optimized "
           "indexing, SIMD, parallelism, and specialized numerical "
           "kernels can become important.\n";
}


// ---------------------------------------------------------------------------
// 21. MEASUREMENT CASE STUDY
// ---------------------------------------------------------------------------

void demonstrateMeasurement() {
    std::cout << "\n"
              << std::string(72, '=')
              << "\nMEASUREMENT CASE STUDY\n"
              << std::string(72, '=')
              << "\n";

    const State state = prepareBellState();

    std::mt19937 generator(42);
    State collapsed;

    const std::size_t measuredIndex =
        measure(
            state,
            generator,
            collapsed
        );

    printState(
        state,
        "State before measurement"
    );

    std::cout
        << "Measured basis state: |"
        << basisLabel(measuredIndex, 2)
        << ">\n";

    printState(
        collapsed,
        "Collapsed state"
    );
}


// ---------------------------------------------------------------------------
// 22. COMPLETE PROGRAM
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << std::string(72, '=')
            << "\n"
            << "CONTROLLED GATES: CONTROLLED-X AND CONTROLLED OPERATIONS\n"
            << std::string(72, '=')
            << "\n";

        const Matrix cx =
            controlledMatrix(pauliX());

        printMatrix(
            cx,
            "Controlled-X matrix"
        );

        std::cout
            << "\nCX truth table:\n"
            << "00 -> 00\n"
            << "01 -> 01\n"
            << "10 -> 11\n"
            << "11 -> 10\n";

        demonstrateBellState();
        demonstrateReversibleLogic();
        demonstrateControlledPhase();
        demonstrateSwapDecomposition();
        demonstrateToffoli();
        demonstrateCircuitArchitecture();
        demonstrateValidation();
        demonstrateUnitarity();
        demonstratePerformanceConsiderations();
        demonstrateMeasurement();

        std::cout
            << "\n"
            << std::string(72, '=')
            << "\nPROGRAM COMPLETED\n"
            << std::string(72, '=')
            << "\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
