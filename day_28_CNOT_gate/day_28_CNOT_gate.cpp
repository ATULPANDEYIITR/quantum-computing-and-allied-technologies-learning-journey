/*
 * CNOT Gate: Entanglement and Computation
 * =======================================
 *
 * C++17 case study:
 * Quantum Entanglement Communication Node
 *
 * The program models a small quantum communication system using:
 *
 *   1. Complex amplitudes
 *   2. State vectors
 *   3. Single-qubit gates
 *   4. Two-qubit CNOT
 *   5. Bell-state generation
 *   6. Measurement probabilities
 *   7. Bell-basis decoding
 *   8. Superdense coding
 *   9. Quantum teleportation state evolution
 *  10. Reversible logic
 *  11. Validation and error handling
 *  12. Complexity and memory considerations
 *
 * Compile:
 *   g++ -std=c++17 -O2 cnot_entanglement.cpp -o cnot_entanglement
 *
 * Run:
 *   ./cnot_entanglement
 */

#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Complex = std::complex<double>;
using State = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double EPSILON = 1e-10;
constexpr double PI = 3.14159265358979323846;


// ============================================================================
// 1. LINEAR ALGEBRA
// ============================================================================

double norm(const State& state) {
    double squaredNorm = 0.0;

    for (const auto& amplitude : state) {
        squaredNorm += std::norm(amplitude);
    }

    return std::sqrt(squaredNorm);
}

State normalize(State state) {
    const double stateNorm = norm(state);

    if (stateNorm <= EPSILON) {
        throw std::invalid_argument(
            "The zero vector cannot represent a quantum state."
        );
    }

    for (auto& amplitude : state) {
        amplitude /= stateNorm;
    }

    return state;
}

Complex innerProduct(const State& left, const State& right) {
    if (left.size() != right.size()) {
        throw std::invalid_argument(
            "Inner-product dimensions do not match."
        );
    }

    Complex result{0.0, 0.0};

    for (std::size_t index = 0; index < left.size(); ++index) {
        result += std::conj(left[index]) * right[index];
    }

    return result;
}

State matrixVectorMultiply(
    const Matrix& matrix,
    const State& vector
) {
    if (matrix.empty()) {
        throw std::invalid_argument("Matrix cannot be empty.");
    }

    const std::size_t width = matrix.front().size();

    if (width != vector.size()) {
        throw std::invalid_argument(
            "Matrix and vector dimensions do not match."
        );
    }

    State result(matrix.size(), Complex{0.0, 0.0});

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        if (matrix[row].size() != width) {
            throw std::invalid_argument(
                "Matrix rows must have equal sizes."
            );
        }

        for (std::size_t column = 0; column < width; ++column) {
            result[row] += matrix[row][column] * vector[column];
        }
    }

    return result;
}

Matrix matrixMultiply(
    const Matrix& left,
    const Matrix& right
) {
    if (left.empty() || right.empty()) {
        throw std::invalid_argument(
            "Matrices cannot be empty."
        );
    }

    const std::size_t leftWidth = left.front().size();
    const std::size_t rightWidth = right.front().size();

    if (leftWidth != right.size()) {
        throw std::invalid_argument(
            "Matrix dimensions do not match."
        );
    }

    Matrix result(
        left.size(),
        std::vector<Complex>(
            rightWidth,
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t i = 0; i < left.size(); ++i) {
        if (left[i].size() != leftWidth) {
            throw std::invalid_argument(
                "Left matrix is not rectangular."
            );
        }

        for (std::size_t j = 0; j < rightWidth; ++j) {
            for (std::size_t k = 0; k < leftWidth; ++k) {
                result[i][j] += left[i][k] * right[k][j];
            }
        }
    }

    return result;
}

Matrix dagger(const Matrix& matrix) {
    if (matrix.empty()) {
        throw std::invalid_argument(
            "Cannot dagger an empty matrix."
        );
    }

    Matrix result(
        matrix.front().size(),
        std::vector<Complex>(
            matrix.size(),
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0;
             column < matrix[row].size();
             ++column) {
            result[column][row] = std::conj(matrix[row][column]);
        }
    }

    return result;
}

Matrix identityMatrix(std::size_t size) {
    Matrix identity(
        size,
        std::vector<Complex>(
            size,
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t index = 0; index < size; ++index) {
        identity[index][index] = Complex{1.0, 0.0};
    }

    return identity;
}

bool approximatelyEqual(
    Complex left,
    Complex right,
    double tolerance = EPSILON
) {
    return std::abs(left - right) <= tolerance;
}

bool matricesApproximatelyEqual(
    const Matrix& left,
    const Matrix& right,
    double tolerance = EPSILON
) {
    if (left.size() != right.size()) {
        return false;
    }

    for (std::size_t row = 0; row < left.size(); ++row) {
        if (left[row].size() != right[row].size()) {
            return false;
        }

        for (std::size_t column = 0;
             column < left[row].size();
             ++column) {
            if (!approximatelyEqual(
                    left[row][column],
                    right[row][column],
                    tolerance)) {
                return false;
            }
        }
    }

    return true;
}


// ============================================================================
// 2. TENSOR PRODUCTS AND BASIS STATES
// ============================================================================

State tensorProduct(
    const State& left,
    const State& right
) {
    State result;
    result.reserve(left.size() * right.size());

    for (const auto& leftAmplitude : left) {
        for (const auto& rightAmplitude : right) {
            result.push_back(
                leftAmplitude * rightAmplitude
            );
        }
    }

    return result;
}

Matrix tensorProduct(
    const Matrix& left,
    const Matrix& right
) {
    if (left.empty() || right.empty()) {
        throw std::invalid_argument(
            "Cannot tensor empty matrices."
        );
    }

    const std::size_t rows =
        left.size() * right.size();

    const std::size_t columns =
        left.front().size() * right.front().size();

    Matrix result(
        rows,
        std::vector<Complex>(
            columns,
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t i = 0; i < left.size(); ++i) {
        for (std::size_t j = 0; j < left.front().size(); ++j) {
            for (std::size_t k = 0; k < right.size(); ++k) {
                for (std::size_t l = 0;
                     l < right.front().size();
                     ++l) {
                    result[
                        i * right.size() + k
                    ][
                        j * right.front().size() + l
                    ] =
                        left[i][j] * right[k][l];
                }
            }
        }
    }

    return result;
}

State basisState(const std::string& bits) {
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

    const std::size_t dimension =
        static_cast<std::size_t>(1) << bits.size();

    State state(
        dimension,
        Complex{0.0, 0.0}
    );

    const std::size_t index =
        std::stoull(bits, nullptr, 2);

    state[index] = Complex{1.0, 0.0};

    return state;
}

std::string basisLabel(
    std::size_t index,
    std::size_t qubits
) {
    std::string bits(qubits, '0');

    for (std::size_t position = 0;
         position < qubits;
         ++position) {
        const std::size_t shift =
            qubits - position - 1;

        bits[position] =
            ((index >> shift) & 1U) ? '1' : '0';
    }

    return bits;
}

void printState(
    const State& state,
    const std::string& label
) {
    const double qubitsLog =
        std::log2(static_cast<double>(state.size()));

    if (
        std::abs(
            qubitsLog -
            std::round(qubitsLog)
        ) > EPSILON
    ) {
        throw std::invalid_argument(
            "State dimension must be a power of two."
        );
    }

    const std::size_t qubits =
        static_cast<std::size_t>(
            std::round(qubitsLog)
        );

    std::cout << label << ": ";

    bool printed = false;

    for (std::size_t index = 0;
         index < state.size();
         ++index) {
        if (std::abs(state[index]) > EPSILON) {
            if (printed) {
                std::cout << " + ";
            }

            std::cout
                << "("
                << std::fixed
                << std::setprecision(4)
                << state[index]
                << ")|"
                << basisLabel(index, qubits)
                << ">";

            printed = true;
        }
    }

    if (!printed) {
        std::cout << "0";
    }

    std::cout << '\n';
}


// ============================================================================
// 3. QUANTUM GATES
// ============================================================================

const Matrix I = {
    {Complex{1, 0}, Complex{0, 0}},
    {Complex{0, 0}, Complex{1, 0}}
};

const Matrix X = {
    {Complex{0, 0}, Complex{1, 0}},
    {Complex{1, 0}, Complex{0, 0}}
};

const Matrix Y = {
    {Complex{0, 0}, Complex{0, -1}},
    {Complex{0, 1}, Complex{0, 0}}
};

const Matrix Z = {
    {Complex{1, 0}, Complex{0, 0}},
    {Complex{0, 0}, Complex{-1, 0}}
};

const Matrix H = {
    {
        Complex{1.0 / std::sqrt(2.0), 0},
        Complex{1.0 / std::sqrt(2.0), 0}
    },
    {
        Complex{1.0 / std::sqrt(2.0), 0},
        Complex{-1.0 / std::sqrt(2.0), 0}
    }
};

/*
 * CNOT matrix in |00>, |01>, |10>, |11> ordering.
 *
 * Control is the left qubit.
 * Target is the right qubit.
 */
const Matrix CNOT = {
    {
        {1, 0}, {0, 0}, {0, 0}, {0, 0}
    },
    {
        {0, 0}, {1, 0}, {0, 0}, {0, 0}
    },
    {
        {0, 0}, {0, 0}, {0, 0}, {1, 0}
    },
    {
        {0, 0}, {0, 0}, {1, 0}, {0, 0}
    }
};


// ============================================================================
// 4. BASIC QUANTUM OPERATIONS
// ============================================================================

State applyGate(
    const Matrix& gate,
    const State& state
) {
    return matrixVectorMultiply(gate, state);
}

State zeroQubit() {
    return {
        Complex{1, 0},
        Complex{0, 0}
    };
}

State oneQubit() {
    return {
        Complex{0, 0},
        Complex{1, 0}
    };
}

State plusQubit() {
    return normalize({
        Complex{1, 0},
        Complex{1, 0}
    });
}

State minusQubit() {
    return normalize({
        Complex{1, 0},
        Complex{-1, 0}
    });
}

State applyOneQubitGateToTwoQubits(
    const State& state,
    const Matrix& gate,
    std::size_t qubit
) {
    if (state.size() != 4) {
        throw std::invalid_argument(
            "Expected a two-qubit state."
        );
    }

    if (qubit > 1) {
        throw std::invalid_argument(
            "Two-qubit system has qubits 0 and 1."
        );
    }

    Matrix operatorMatrix =
        qubit == 0
        ? tensorProduct(gate, I)
        : tensorProduct(I, gate);

    return applyGate(operatorMatrix, state);
}

State applyCNOT(
    const State& state
) {
    if (state.size() != 4) {
        throw std::invalid_argument(
            "CNOT requires two qubits."
        );
    }

    return applyGate(CNOT, state);
}


// ============================================================================
// 5. CLASSICAL CNOT BEHAVIOR
// ============================================================================

std::pair<int, int> classicalCNOT(
    int control,
    int target
) {
    if (
        (control != 0 && control != 1) ||
        (target != 0 && target != 1)
    ) {
        throw std::invalid_argument(
            "Classical CNOT inputs must be binary."
        );
    }

    return {
        control,
        target ^ control
    };
}

void demonstrateTruthTable() {
    std::cout << "\n=== CNOT truth table ===\n";

    for (int control : {0, 1}) {
        for (int target : {0, 1}) {
            auto output =
                classicalCNOT(control, target);

            std::cout
                << "|" << control << target << "> -> |"
                << output.first
                << output.second
                << ">\n";
        }
    }
}


// ============================================================================
// 6. BELL-STATE GENERATION
// ============================================================================

State bellPhiPlus() {
    /*
     * Start:
     *     |00>
     *
     * Apply H to qubit 0:
     *     (|00> + |10>) / sqrt(2)
     *
     * Apply CNOT:
     *     (|00> + |11>) / sqrt(2)
     */
    State state =
        tensorProduct(
            zeroQubit(),
            zeroQubit()
        );

    state =
        applyOneQubitGateToTwoQubits(
            state,
            H,
            0
        );

    state = applyCNOT(state);

    return state;
}

State bellPhiMinus() {
    State state =
        tensorProduct(
            zeroQubit(),
            zeroQubit()
        );

    state =
        applyOneQubitGateToTwoQubits(
            state,
            H,
            0
        );

    state =
        applyOneQubitGateToTwoQubits(
            state,
            Z,
            0
        );

    state = applyCNOT(state);

    return state;
}

State bellPsiPlus() {
    State state =
        tensorProduct(
            zeroQubit(),
            oneQubit()
        );

    state =
        applyOneQubitGateToTwoQubits(
            state,
            H,
            0
        );

    state = applyCNOT(state);

    return state;
}

State bellPsiMinus() {
    State state =
        tensorProduct(
            zeroQubit(),
            oneQubit()
        );

    state =
        applyOneQubitGateToTwoQubits(
            state,
            H,
            0
        );

    state =
        applyOneQubitGateToTwoQubits(
            state,
            Z,
            0
        );

    state = applyCNOT(state);

    return state;
}

void demonstrateBellStates() {
    std::cout << "\n=== Bell states ===\n";

    const std::array<std::pair<std::string, State>, 4>
        bellStates = {{
            {"Phi+", bellPhiPlus()},
            {"Phi-", bellPhiMinus()},
            {"Psi+", bellPsiPlus()},
            {"Psi-", bellPsiMinus()}
        }};

    for (const auto& [name, state] : bellStates) {
        printState(state, name);
        std::cout
            << "  norm = "
            << std::setprecision(8)
            << norm(state)
            << '\n';
    }
}


// ============================================================================
// 7. MEASUREMENT
// ============================================================================

std::vector<double> measurementProbabilities(
    const State& state
) {
    if (
        std::abs(norm(state) - 1.0) >
        EPSILON
    ) {
        throw std::invalid_argument(
            "Measurement requires a normalized state."
        );
    }

    std::vector<double> probabilities;
    probabilities.reserve(state.size());

    for (const auto& amplitude : state) {
        probabilities.push_back(
            std::norm(amplitude)
        );
    }

    return probabilities;
}

std::map<std::string, int> sampleMeasurements(
    const State& state,
    int shots,
    std::mt19937& generator
) {
    if (shots <= 0) {
        throw std::invalid_argument(
            "Number of shots must be positive."
        );
    }

    const auto probabilities =
        measurementProbabilities(state);

    std::discrete_distribution<std::size_t>
        distribution(
            probabilities.begin(),
            probabilities.end()
        );

    const std::size_t qubits =
        static_cast<std::size_t>(
            std::round(
                std::log2(
                    static_cast<double>(
                        state.size()
                    )
                )
            )
        );

    std::map<std::string, int> counts;

    for (int shot = 0; shot < shots; ++shot) {
        const std::size_t outcome =
            distribution(generator);

        counts[
            basisLabel(outcome, qubits)
        ]++;
    }

    return counts;
}

void demonstrateMeasurement() {
    std::cout << "\n=== Bell-state measurement ===\n";

    const State state = bellPhiPlus();

    const auto probabilities =
        measurementProbabilities(state);

    for (std::size_t index = 0;
         index < probabilities.size();
         ++index) {
        std::cout
            << "P(|"
            << basisLabel(index, 2)
            << ">) = "
            << std::fixed
            << std::setprecision(3)
            << probabilities[index]
            << '\n';
    }

    std::mt19937 generator(42);

    const auto counts =
        sampleMeasurements(
            state,
            2000,
            generator
        );

    std::cout << "2000 measurements:\n";

    for (const auto& [bits, count] : counts) {
        std::cout
            << "  "
            << bits
            << ": "
            << count
            << '\n';
    }
}


// ============================================================================
// 8. PURE-STATE ENTANGLEMENT TEST
// ============================================================================

bool isProductTwoQubitState(
    const State& state
) {
    if (state.size() != 4) {
        throw std::invalid_argument(
            "Expected a two-qubit state."
        );
    }

    /*
     * For:
     *
     * |psi> =
     * a|00> + b|01> + c|10> + d|11>
     *
     * the state is separable iff:
     *
     *     a*d - b*c = 0
     *
     * This determinant condition is specific to a pure two-qubit state.
     */
    const Complex determinant =
        state[0] * state[3] -
        state[1] * state[2];

    return std::abs(determinant) <= EPSILON;
}

void demonstrateEntanglementTest() {
    std::cout << "\n=== Product state versus Bell state ===\n";

    const State product =
        tensorProduct(
            plusQubit(),
            zeroQubit()
        );

    const State bell =
        bellPhiPlus();

    printState(product, "Product");
    std::cout
        << "Product state separable: "
        << std::boolalpha
        << isProductTwoQubitState(product)
        << '\n';

    printState(bell, "Bell");
    std::cout
        << "Bell state separable: "
        << std::boolalpha
        << isProductTwoQubitState(bell)
        << '\n';
}


// ============================================================================
// 9. REDUCED DENSITY MATRIX
// ============================================================================

Matrix partialTraceSecondQubit(
    const State& state
) {
    if (state.size() != 4) {
        throw std::invalid_argument(
            "Expected a two-qubit state."
        );
    }

    const Complex& a = state[0];
    const Complex& b = state[1];
    const Complex& c = state[2];
    const Complex& d = state[3];

    return {
        {
            std::norm(a) + std::norm(b),
            a * std::conj(c) +
            b * std::conj(d)
        },
        {
            c * std::conj(a) +
            d * std::conj(b),
            std::norm(c) + std::norm(d)
        }
    };
}

Complex matrixTrace(
    const Matrix& matrix
) {
    if (matrix.empty()) {
        throw std::invalid_argument(
            "Matrix cannot be empty."
        );
    }

    Complex trace{0.0, 0.0};

    for (std::size_t index = 0;
         index < matrix.size();
         ++index) {
        trace += matrix[index][index];
    }

    return trace;
}

double purity(
    const Matrix& densityMatrix
) {
    const Matrix squared =
        matrixMultiply(
            densityMatrix,
            densityMatrix
        );

    return matrixTrace(squared).real();
}

double entropyOfTwoByTwoDensityMatrix(
    const Matrix& densityMatrix
) {
    /*
     * For a valid 2x2 trace-one density matrix:
     *
     * lambda± =
     * (1 ± sqrt(1 - 4 det(rho))) / 2
     *
     * S(rho) =
     * -lambda+ log2(lambda+)
     * -lambda- log2(lambda-)
     */
    const Complex determinant =
        densityMatrix[0][0] *
        densityMatrix[1][1] -
        densityMatrix[0][1] *
        densityMatrix[1][0];

    double determinantValue =
        std::clamp(
            determinant.real(),
            0.0,
            0.25
        );

    const double discriminant =
        std::max(
            0.0,
            1.0 - 4.0 * determinantValue
        );

    const double root =
        std::sqrt(discriminant);

    const double lambda1 =
        (1.0 + root) / 2.0;

    const double lambda2 =
        (1.0 - root) / 2.0;

    double entropy = 0.0;

    for (double lambda : {lambda1, lambda2}) {
        if (lambda > EPSILON) {
            entropy -=
                lambda * std::log2(lambda);
        }
    }

    return entropy;
}

void demonstrateDensityMatrix() {
    std::cout
        << "\n=== Reduced state and entanglement entropy ===\n";

    const State product =
        tensorProduct(
            plusQubit(),
            zeroQubit()
        );

    const State bell =
        bellPhiPlus();

    const Matrix productReduced =
        partialTraceSecondQubit(product);

    const Matrix bellReduced =
        partialTraceSecondQubit(bell);

    std::cout
        << "Product reduced purity: "
        << purity(productReduced)
        << '\n';

    std::cout
        << "Bell reduced purity: "
        << purity(bellReduced)
        << '\n';

    std::cout
        << "Product reduced entropy: "
        << entropyOfTwoByTwoDensityMatrix(
            productReduced
        )
        << '\n';

    std::cout
        << "Bell reduced entropy: "
        << entropyOfTwoByTwoDensityMatrix(
            bellReduced
        )
        << '\n';
}


// ============================================================================
// 10. THREE-QUBIT OPERATIONS
// ============================================================================

State applySingleQubitGateToThreeQubits(
    const State& state,
    const Matrix& gate,
    std::size_t qubit
) {
    if (state.size() != 8) {
        throw std::invalid_argument(
            "Expected a three-qubit state."
        );
    }

    if (qubit > 2) {
        throw std::invalid_argument(
            "Qubit index must be 0, 1, or 2."
        );
    }

    State output(
        8,
        Complex{0.0, 0.0}
    );

    for (std::size_t index = 0;
         index < state.size();
         ++index) {
        const std::string bits =
            basisLabel(index, 3);

        const std::size_t inputBit =
            bits[qubit] - '0';

        for (std::size_t outputBit = 0;
             outputBit < 2;
             ++outputBit) {
            std::string newBits = bits;

            newBits[qubit] =
                static_cast<char>(
                    '0' + outputBit
                );

            const std::size_t newIndex =
                std::stoull(
                    newBits,
                    nullptr,
                    2
                );

            output[newIndex] +=
                gate[outputBit][inputBit] *
                state[index];
        }
    }

    return output;
}

State applyCNOTToThreeQubits(
    const State& state,
    std::size_t control,
    std::size_t target
) {
    if (state.size() != 8) {
        throw std::invalid_argument(
            "Expected a three-qubit state."
        );
    }

    if (control > 2 || target > 2) {
        throw std::invalid_argument(
            "Qubit indices must be 0, 1, or 2."
        );
    }

    if (control == target) {
        throw std::invalid_argument(
            "Control and target must differ."
        );
    }

    State output(
        8,
        Complex{0.0, 0.0}
    );

    for (std::size_t index = 0;
         index < state.size();
         ++index) {
        std::string bits =
            basisLabel(index, 3);

        if (bits[control] == '1') {
            bits[target] =
                bits[target] == '0'
                ? '1'
                : '0';
        }

        const std::size_t newIndex =
            std::stoull(
                bits,
                nullptr,
                2
            );

        output[newIndex] += state[index];
    }

    return output;
}


// ============================================================================
// 11. QUANTUM TELEPORTATION
// ============================================================================

void demonstrateTeleportation() {
    std::cout
        << "\n=== Quantum teleportation case study ===\n";

    /*
     * Problem:
     *
     * Alice possesses an unknown qubit:
     *
     *     |psi> = alpha|0> + beta|1>
     *
     * Bob is distant from Alice.
     *
     * The protocol uses:
     *   - one unknown qubit,
     *   - one shared Bell pair,
     *   - two classical bits,
     *   - conditional X/Z corrections.
     *
     * The unknown state is not copied. Alice's original state is consumed
     * by the measurement process. The information is transferred through
     * entanglement plus classical communication.
     */

    const Complex alpha{
        1.0 / std::sqrt(3.0),
        0.0
    };

    const Complex beta{
        0.0,
        std::sqrt(2.0 / 3.0)
    };

    /*
     * Initial:
     *
     * |psi> |0> |0>
     *
     * Qubit 0 = unknown state
     * Qubit 1 = Alice's Bell qubit
     * Qubit 2 = Bob's Bell qubit
     */
    State state =
        tensorProduct(
            tensorProduct(
                State{alpha, beta},
                zeroQubit()
            ),
            zeroQubit()
        );

    // Create the Bell pair on qubits 1 and 2.
    state =
        applySingleQubitGateToThreeQubits(
            state,
            H,
            1
        );

    state =
        applyCNOTToThreeQubits(
            state,
            1,
            2
        );

    // Alice's Bell-basis transformation.
    state =
        applyCNOTToThreeQubits(
            state,
            0,
            1
        );

    state =
        applySingleQubitGateToThreeQubits(
            state,
            H,
            0
        );

    printState(
        state,
        "State immediately before Alice's measurement"
    );

    std::cout
        << "Teleportation uses two classical measurement bits "
        << "to select Bob's correction.\n";
}


// ============================================================================
// 12. SUPERDENSE CODING
// ============================================================================

void demonstrateSuperdenseCoding() {
    std::cout
        << "\n=== Superdense coding ===\n";

    /*
     * Shared resource:
     *     |Phi+>
     *
     * Alice encodes two classical bits by applying:
     *
     *     00 -> I
     *     01 -> X
     *     10 -> Z
     *     11 -> XZ
     *
     * Bob then performs:
     *
     *     CNOT
     *     H
     *     measurement
     *
     * The Bell states are mapped back to computational-basis states.
     */

    const std::vector<
        std::pair<std::string, Matrix>
    > encodings = {
        {"00", I},
        {"01", X},
        {"10", Z},
        {
            "11",
            matrixMultiply(X, Z)
        }
    };

    for (const auto& [message, encoding] :
         encodings) {
        State state = bellPhiPlus();

        state =
            applyOneQubitGateToTwoQubits(
                state,
                encoding,
                0
            );

        state = applyCNOT(state);

        state =
            applyOneQubitGateToTwoQubits(
                state,
                H,
                0
            );

        const auto probabilities =
            measurementProbabilities(state);

        const auto maximum =
            std::max_element(
                probabilities.begin(),
                probabilities.end()
            );

        const std::size_t decodedIndex =
            static_cast<std::size_t>(
                std::distance(
                    probabilities.begin(),
                    maximum
                )
            );

        std::cout
            << "Message "
            << message
            << " decoded as "
            << basisLabel(decodedIndex, 2)
            << '\n';
    }
}


// ============================================================================
// 13. REVERSIBLE COMPUTATION
// ============================================================================

std::array<int, 3> reversibleAND(
    int a,
    int b,
    int target
) {
    if (
        (a != 0 && a != 1) ||
        (b != 0 && b != 1) ||
        (target != 0 && target != 1)
    ) {
        throw std::invalid_argument(
            "Reversible-logic inputs must be binary."
        );
    }

    /*
     * Toffoli-style transformation:
     *
     *     (a,b,t)
     *       |
     *       v
     * (a,b,t XOR (a AND b))
     *
     * It computes AND into a target while preserving a and b.
     */
    return {
        a,
        b,
        target ^ (a & b)
    };
}

void demonstrateReversibleLogic() {
    std::cout
        << "\n=== Reversible computation ===\n";

    for (int a : {0, 1}) {
        for (int b : {0, 1}) {
            const auto result =
                reversibleAND(a, b, 0);

            std::cout
                << "("
                << a << ","
                << b << ",0) -> ("
                << result[0] << ","
                << result[1] << ","
                << result[2] << ")\n";
        }
    }
}


// ============================================================================
// 14. NON-TRIVIAL QUANTUM COMMUNICATION NODE
// ============================================================================

class QuantumCommunicationNode {
private:
    std::string nodeName;
    State sharedState;

public:
    explicit QuantumCommunicationNode(
        std::string name
    )
        : nodeName(std::move(name)),
          sharedState(bellPhiPlus()) {}

    const std::string& name() const {
        return nodeName;
    }

    void printSharedResource() const {
        printState(
            sharedState,
            nodeName + " shared Bell resource"
        );
    }

    State encodeClassicalMessage(
        const std::string& message
    ) const {
        Matrix operation;

        if (message == "00") {
            operation = I;
        } else if (message == "01") {
            operation = X;
        } else if (message == "10") {
            operation = Z;
        } else if (message == "11") {
            operation = matrixMultiply(X, Z);
        } else {
            throw std::invalid_argument(
                "Message must be 00, 01, 10, or 11."
            );
        }

        return applyOneQubitGateToTwoQubits(
            sharedState,
            operation,
            0
        );
    }

    std::string decode(
        State encodedState
    ) const {
        /*
         * Bell-basis decoding:
         *
         * First CNOT transforms correlations into computational
         * basis information. H on the first qubit then completes
         * the Bell-basis transformation.
         */
        encodedState =
            applyCNOT(encodedState);

        encodedState =
            applyOneQubitGateToTwoQubits(
                encodedState,
                H,
                0
            );

        const auto probabilities =
            measurementProbabilities(
                encodedState
            );

        const auto maximum =
            std::max_element(
                probabilities.begin(),
                probabilities.end()
            );

        const std::size_t index =
            static_cast<std::size_t>(
                std::distance(
                    probabilities.begin(),
                    maximum
                )
            );

        return basisLabel(index, 2);
    }
};

void demonstrateCommunicationNode() {
    std::cout
        << "\n=== Quantum communication node ===\n";

    QuantumCommunicationNode node("EntanglementNode");

    node.printSharedResource();

    for (const std::string& message :
         {"00", "01", "10", "11"}) {
        State encoded =
            node.encodeClassicalMessage(message);

        const std::string decoded =
            node.decode(encoded);

        std::cout
            << "Input message: "
            << message
            << " | Decoded: "
            << decoded
            << '\n';
    }
}


// ============================================================================
// 15. MEMORY AND TIME COMPLEXITY
// ============================================================================

std::string humanBytes(
    std::size_t bytes
) {
    const std::array<std::string, 5> units = {
        "B",
        "KiB",
        "MiB",
        "GiB",
        "TiB"
    };

    double value =
        static_cast<double>(bytes);

    for (const auto& unit : units) {
        if (value < 1024.0 ||
            unit == units.back()) {
            std::ostringstream output;
            output << std::fixed
                   << std::setprecision(2)
                   << value
                   << " "
                   << unit;
            return output.str();
        }

        value /= 1024.0;
    }

    return "unrepresentable";
}

void demonstrateScaling() {
    std::cout
        << "\n=== State-vector scaling ===\n";

    /*
     * An n-qubit pure state requires 2^n complex amplitudes.
     *
     * A compact complex<double> uses commonly 16 bytes:
     *
     *     memory ~= 16 * 2^n bytes
     *
     * Real simulators also require temporary buffers, metadata,
     * gate operations, and numerical workspace.
     */
    for (std::size_t qubits :
         {1, 2, 10, 20, 30}) {
        const std::size_t amplitudes =
            static_cast<std::size_t>(1ULL << qubits);

        const std::size_t bytes =
            amplitudes * sizeof(Complex);

        std::cout
            << qubits
            << " qubits -> "
            << amplitudes
            << " amplitudes -> "
            << humanBytes(bytes)
            << " for the raw state vector\n";
    }

    std::cout
        << "A dense state-vector simulator has exponential "
        << "memory requirements.\n";
}


// ============================================================================
// 16. VALIDATION
// ============================================================================

void require(
    bool condition,
    const std::string& message
) {
    if (!condition) {
        throw std::runtime_error(
            "Test failure: " + message
        );
    }
}

void runTests() {
    std::cout << "\n=== Tests ===\n";

    // Classical truth table.
    require(
        classicalCNOT(0, 0) ==
            std::make_pair(0, 0),
        "CNOT 00"
    );

    require(
        classicalCNOT(0, 1) ==
            std::make_pair(0, 1),
        "CNOT 01"
    );

    require(
        classicalCNOT(1, 0) ==
            std::make_pair(1, 1),
        "CNOT 10"
    );

    require(
        classicalCNOT(1, 1) ==
            std::make_pair(1, 0),
        "CNOT 11"
    );

    // CNOT must be unitary.
    const Matrix unitary =
        matrixMultiply(
            dagger(CNOT),
            CNOT
        );

    require(
        matricesApproximatelyEqual(
            unitary,
            identityMatrix(4)
        ),
        "CNOT is unitary"
    );

    // CNOT is its own inverse.
    const Matrix inverse =
        matrixMultiply(CNOT, CNOT);

    require(
        matricesApproximatelyEqual(
            inverse,
            identityMatrix(4)
        ),
        "CNOT is self-inverse"
    );

    // Bell state must be normalized.
    const State bell =
        bellPhiPlus();

    require(
        std::abs(norm(bell) - 1.0) <= EPSILON,
        "Bell state normalization"
    );

    // Bell state must be entangled.
    require(
        !isProductTwoQubitState(bell),
        "Bell-state separability"
    );

    // Bell-state probabilities.
    const auto probabilities =
        measurementProbabilities(bell);

    require(
        std::abs(probabilities[0] - 0.5) <= EPSILON,
        "P(00)"
    );

    require(
        std::abs(probabilities[3] - 0.5) <= EPSILON,
        "P(11)"
    );

    require(
        probabilities[1] <= EPSILON,
        "P(01)"
    );

    require(
        probabilities[2] <= EPSILON,
        "P(10)"
    );

    // Entanglement entropy of a Bell pair is one bit.
    const Matrix reduced =
        partialTraceSecondQubit(bell);

    const double entropy =
        entropyOfTwoByTwoDensityMatrix(
            reduced
        );

    require(
        std::abs(entropy - 1.0) <= EPSILON,
        "Bell-state entanglement entropy"
    );

    std::cout
        << "All tests passed.\n";
}


// ============================================================================
// 17. EDGE-CASE TESTING
// ============================================================================

void demonstrateEdgeCases() {
    std::cout
        << "\n=== Edge cases and validation ===\n";

    try {
        basisState("012");
    } catch (const std::exception& error) {
        std::cout
            << "Invalid basis state -> "
            << error.what()
            << '\n';
    }

    try {
        applyCNOT({
            Complex{1, 0},
            Complex{0, 0}
        });
    } catch (const std::exception& error) {
        std::cout
            << "Invalid CNOT dimension -> "
            << error.what()
            << '\n';
    }

    try {
        measurementProbabilities({
            Complex{1, 0},
            Complex{1, 0}
        });
    } catch (const std::exception& error) {
        std::cout
            << "Unnormalized measurement -> "
            << error.what()
            << '\n';
    }

    try {
        classicalCNOT(2, 1);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid binary input -> "
            << error.what()
            << '\n';
    }
}


// ============================================================================
// 18. MAIN
// ============================================================================

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "CNOT GATE: ENTANGLEMENT AND COMPUTATION\n"
            << "============================================================\n";

        std::cout
            << "\nCore transformation:\n"
            << "CNOT |c,t> = |c, t XOR c>\n"
            << "The control is unchanged; the target flips when control=1.\n";

        demonstrateTruthTable();

        std::cout
            << "\n=== CNOT basis-state action ===\n";

        for (const std::string& bits :
             {"00", "01", "10", "11"}) {
            State input =
                basisState(bits);

            State output =
                applyCNOT(input);

            printState(
                input,
                "Input |" + bits + ">"
            );

            printState(
                output,
                "Output"
            );
        }

        std::cout
            << "\n=== Unitarity and reversibility ===\n";

        require(
            matricesApproximatelyEqual(
                matrixMultiply(
                    dagger(CNOT),
                    CNOT
                ),
                identityMatrix(4)
            ),
            "CNOT unitarity"
        );

        require(
            matricesApproximatelyEqual(
                matrixMultiply(
                    CNOT,
                    CNOT
                ),
                identityMatrix(4)
            ),
            "CNOT self-inverse"
        );

        std::cout
            << "CNOT†CNOT = I\n"
            << "CNOT² = I\n";

        demonstrateBellStates();
        demonstrateMeasurement();
        demonstrateEntanglementTest();
        demonstrateDensityMatrix();
        demonstrateTeleportation();
        demonstrateSuperdenseCoding();
        demonstrateReversibleLogic();
        demonstrateCommunicationNode();
        demonstrateScaling();
        demonstrateEdgeCases();
        runTests();

        std::cout
            << "\n=== Important equations ===\n"
            << "CNOT |c,t> = |c,t XOR c>\n"
            << "|Phi+> = (|00> + |11>) / sqrt(2)\n"
            << "P(x) = |amplitude_x|^2\n"
            << "U†U = I\n"
            << "CNOT² = I\n"
            << "n-qubit state-vector dimension = 2^n\n";

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
