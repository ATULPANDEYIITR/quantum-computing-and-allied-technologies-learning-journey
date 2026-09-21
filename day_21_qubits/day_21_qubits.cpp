/*
 * Qubits: C++17 Industry-Style Case Study
 *
 * Case study:
 * A compact quantum state-vector engine is used to model a small
 * quantum communication experiment inspired by BB84 and to demonstrate
 * the underlying qubit mechanisms.
 *
 * The implementation intentionally uses only the C++ standard library.
 *
 * Demonstrated concepts:
 * - Qubit state vectors
 * - Complex probability amplitudes
 * - Normalization
 * - Quantum gates
 * - Hadamard superposition
 * - Pauli operations
 * - Arbitrary single-qubit rotations
 * - Multi-qubit tensor-product state spaces
 * - CNOT
 * - Entanglement
 * - Computational-basis measurement
 * - Measurement statistics
 * - Circuit abstraction
 * - Validation and failure handling
 * - Noise simulation
 * - BB84-style basis reconciliation
 * - Complexity and memory considerations
 *
 * Compile:
 *   g++ -std=c++17 -O2 qubits.cpp -o qubits
 *
 * Run:
 *   ./qubits
 */

#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Complex = std::complex<double>;
using StateVector = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double EPSILON = 1e-10;
constexpr double PI = 3.141592653589793238462643383279502884;

// ---------------------------------------------------------------------------
// Mathematical utilities
// ---------------------------------------------------------------------------

double stateNorm(const StateVector& state) {
    double squaredNorm = 0.0;

    for (const Complex& amplitude : state) {
        squaredNorm += std::norm(amplitude);
    }

    return std::sqrt(squaredNorm);
}

void validateNormalized(const StateVector& state) {
    const double norm = stateNorm(state);

    if (std::abs(norm - 1.0) > EPSILON) {
        throw std::runtime_error(
            "Quantum state is not normalized."
        );
    }
}

StateVector normalize(StateVector state) {
    const double norm = stateNorm(state);

    if (norm < EPSILON) {
        throw std::invalid_argument(
            "The zero vector cannot represent a quantum state."
        );
    }

    for (Complex& amplitude : state) {
        amplitude /= norm;
    }

    return state;
}

Matrix identityMatrix(std::size_t dimension) {
    Matrix result(
        dimension,
        std::vector<Complex>(
            dimension,
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t i = 0; i < dimension; ++i) {
        result[i][i] = Complex{1.0, 0.0};
    }

    return result;
}

StateVector matrixVectorMultiply(
    const Matrix& matrix,
    const StateVector& state
) {
    if (matrix.size() != state.size()) {
        throw std::invalid_argument(
            "Matrix and vector dimensions do not match."
        );
    }

    StateVector result(
        state.size(),
        Complex{0.0, 0.0}
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        if (matrix[row].size() != state.size()) {
            throw std::invalid_argument(
                "Matrix must be square."
            );
        }

        for (std::size_t column = 0;
             column < state.size();
             ++column) {
            result[row] +=
                matrix[row][column] * state[column];
        }
    }

    return result;
}

Matrix conjugateTranspose(const Matrix& matrix) {
    Matrix result(
        matrix[0].size(),
        std::vector<Complex>(
            matrix.size(),
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0;
             column < matrix[row].size();
             ++column) {
            result[column][row] =
                std::conj(matrix[row][column]);
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

    if (left[0].size() != right.size()) {
        throw std::invalid_argument(
            "Matrix dimensions do not match."
        );
    }

    Matrix result(
        left.size(),
        std::vector<Complex>(
            right[0].size(),
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t i = 0; i < left.size(); ++i) {
        for (std::size_t k = 0;
             k < right.size();
             ++k) {
            for (std::size_t j = 0;
                 j < right[0].size();
                 ++j) {
                result[i][j] +=
                    left[i][k] * right[k][j];
            }
        }
    }

    return result;
}

bool isUnitary(const Matrix& matrix) {
    const Matrix product =
        matrixMultiply(
            conjugateTranspose(matrix),
            matrix
        );

    const Matrix identity =
        identityMatrix(matrix.size());

    for (std::size_t row = 0;
         row < matrix.size();
         ++row) {
        for (std::size_t column = 0;
             column < matrix.size();
             ++column) {
            if (std::abs(
                    product[row][column]
                    - identity[row][column]
                ) > EPSILON) {
                return false;
            }
        }
    }

    return true;
}

// ---------------------------------------------------------------------------
// Basic quantum states and gates
// ---------------------------------------------------------------------------

StateVector basisState(int bit) {
    if (bit == 0) {
        return {
            Complex{1.0, 0.0},
            Complex{0.0, 0.0}
        };
    }

    if (bit == 1) {
        return {
            Complex{0.0, 0.0},
            Complex{1.0, 0.0}
        };
    }

    throw std::invalid_argument(
        "Basis bit must be 0 or 1."
    );
}

StateVector computationalBasisState(
    const std::string& bits
) {
    if (bits.empty()) {
        throw std::invalid_argument(
            "Bit string cannot be empty."
        );
    }

    for (char bit : bits) {
        if (bit != '0' && bit != '1') {
            throw std::invalid_argument(
                "Bit string must contain only 0 and 1."
            );
        }
    }

    const std::size_t dimension =
        static_cast<std::size_t>(1) << bits.size();

    StateVector state(
        dimension,
        Complex{0.0, 0.0}
    );

    const std::size_t index =
        std::stoull(bits, nullptr, 2);

    state[index] = Complex{1.0, 0.0};

    return state;
}

Matrix pauliX() {
    return {
        {Complex{0.0, 0.0}, Complex{1.0, 0.0}},
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}}
    };
}

Matrix pauliY() {
    return {
        {Complex{0.0, 0.0}, Complex{0.0, -1.0}},
        {Complex{0.0, 1.0}, Complex{0.0, 0.0}}
    };
}

Matrix pauliZ() {
    return {
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{-1.0, 0.0}}
    };
}

Matrix hadamard() {
    const double inverseSqrtTwo =
        1.0 / std::sqrt(2.0);

    return {
        {
            Complex{inverseSqrtTwo, 0.0},
            Complex{inverseSqrtTwo, 0.0}
        },
        {
            Complex{inverseSqrtTwo, 0.0},
            Complex{-inverseSqrtTwo, 0.0}
        }
    };
}

Matrix phaseS() {
    return {
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{0.0, 1.0}}
    };
}

Matrix phaseT() {
    return {
        {
            Complex{1.0, 0.0},
            Complex{0.0, 0.0}
        },
        {
            Complex{0.0, 0.0},
            std::polar(1.0, PI / 4.0)
        }
    };
}

Matrix rotationX(double theta) {
    const double c = std::cos(theta / 2.0);
    const double s = std::sin(theta / 2.0);

    return {
        {
            Complex{c, 0.0},
            Complex{0.0, -s}
        },
        {
            Complex{0.0, -s},
            Complex{c, 0.0}
        }
    };
}

Matrix rotationY(double theta) {
    const double c = std::cos(theta / 2.0);
    const double s = std::sin(theta / 2.0);

    return {
        {
            Complex{c, 0.0},
            Complex{-s, 0.0}
        },
        {
            Complex{s, 0.0},
            Complex{c, 0.0}
        }
    };
}

Matrix rotationZ(double theta) {
    return {
        {
            std::polar(1.0, -theta / 2.0),
            Complex{0.0, 0.0}
        },
        {
            Complex{0.0, 0.0},
            std::polar(1.0, theta / 2.0)
        }
    };
}

StateVector applyGate(
    const StateVector& state,
    const Matrix& gate
) {
    if (!isUnitary(gate)) {
        throw std::invalid_argument(
            "Quantum evolution gate must be unitary."
        );
    }

    StateVector result =
        matrixVectorMultiply(gate, state);

    validateNormalized(result);

    return result;
}

// ---------------------------------------------------------------------------
// Tensor products and selected-qubit operations
// ---------------------------------------------------------------------------

StateVector tensorProduct(
    const StateVector& left,
    const StateVector& right
) {
    StateVector result;
    result.reserve(
        left.size() * right.size()
    );

    for (const Complex& leftAmplitude : left) {
        for (const Complex& rightAmplitude : right) {
            result.push_back(
                leftAmplitude * rightAmplitude
            );
        }
    }

    return result;
}

StateVector applySingleQubitGate(
    const StateVector& state,
    const Matrix& gate,
    std::size_t targetQubit,
    std::size_t numberOfQubits
) {
    if (state.size() !=
        (static_cast<std::size_t>(1) << numberOfQubits)) {
        throw std::invalid_argument(
            "State dimension does not match qubit count."
        );
    }

    if (targetQubit >= numberOfQubits) {
        throw std::out_of_range(
            "Target qubit is out of range."
        );
    }

    if (gate.size() != 2 ||
        gate[0].size() != 2 ||
        gate[1].size() != 2) {
        throw std::invalid_argument(
            "Single-qubit gate must be 2x2."
        );
    }

    StateVector result(
        state.size(),
        Complex{0.0, 0.0}
    );

    // Big-endian convention:
    // qubit 0 is the leftmost bit.
    const std::size_t bitPosition =
        numberOfQubits - 1 - targetQubit;

    const std::size_t mask =
        static_cast<std::size_t>(1) << bitPosition;

    for (std::size_t index = 0;
         index < state.size();
         ++index) {
        if (index & mask) {
            continue;
        }

        const std::size_t partner =
            index | mask;

        const Complex first =
            state[index];

        const Complex second =
            state[partner];

        result[index] =
            gate[0][0] * first
            + gate[0][1] * second;

        result[partner] =
            gate[1][0] * first
            + gate[1][1] * second;
    }

    validateNormalized(result);

    return result;
}

StateVector applyCNOT(
    const StateVector& state,
    std::size_t controlQubit,
    std::size_t targetQubit,
    std::size_t numberOfQubits
) {
    if (controlQubit == targetQubit) {
        throw std::invalid_argument(
            "Control and target must be different."
        );
    }

    if (
        controlQubit >= numberOfQubits ||
        targetQubit >= numberOfQubits
    ) {
        throw std::out_of_range(
            "Control or target qubit is out of range."
        );
    }

    StateVector result(
        state.size(),
        Complex{0.0, 0.0}
    );

    const std::size_t controlPosition =
        numberOfQubits - 1 - controlQubit;

    const std::size_t targetPosition =
        numberOfQubits - 1 - targetQubit;

    const std::size_t controlMask =
        static_cast<std::size_t>(1)
        << controlPosition;

    const std::size_t targetMask =
        static_cast<std::size_t>(1)
        << targetPosition;

    for (std::size_t index = 0;
         index < state.size();
         ++index) {
        const std::size_t destination =
            index & controlMask
                ? index ^ targetMask
                : index;

        result[destination] +=
            state[index];
    }

    validateNormalized(result);

    return result;
}

// ---------------------------------------------------------------------------
// Measurement
// ---------------------------------------------------------------------------

std::string bitString(
    std::size_t value,
    std::size_t numberOfQubits
) {
    std::string result(
        numberOfQubits,
        '0'
    );

    for (std::size_t position = 0;
         position < numberOfQubits;
         ++position) {
        const std::size_t bitPosition =
            numberOfQubits - 1 - position;

        if (
            value
            & (static_cast<std::size_t>(1)
               << bitPosition)
        ) {
            result[position] = '1';
        }
    }

    return result;
}

std::pair<std::string, StateVector> measure(
    const StateVector& state,
    std::size_t numberOfQubits,
    std::mt19937_64& generator
) {
    validateNormalized(state);

    std::uniform_real_distribution<double>
        distribution(0.0, 1.0);

    const double randomValue =
        distribution(generator);

    double cumulative = 0.0;

    for (std::size_t index = 0;
         index < state.size();
         ++index) {
        cumulative +=
            std::norm(state[index]);

        if (
            randomValue <= cumulative ||
            index == state.size() - 1
        ) {
            StateVector collapsed(
                state.size(),
                Complex{0.0, 0.0}
            );

            collapsed[index] =
                Complex{1.0, 0.0};

            return {
                bitString(index, numberOfQubits),
                collapsed
            };
        }
    }

    throw std::runtime_error(
        "Measurement failed."
    );
}

std::map<std::string, std::size_t>
sampleMeasurements(
    const StateVector& state,
    std::size_t numberOfQubits,
    std::size_t shots,
    std::mt19937_64& generator
) {
    if (shots == 0) {
        throw std::invalid_argument(
            "Measurement shots must be positive."
        );
    }

    std::map<std::string, std::size_t> counts;

    for (std::size_t shot = 0;
         shot < shots;
         ++shot) {
        const auto result =
            measure(
                state,
                numberOfQubits,
                generator
            );

        ++counts[result.first];
    }

    return counts;
}

// ---------------------------------------------------------------------------
// Quantum circuit abstraction
// ---------------------------------------------------------------------------

struct Operation {
    std::string name;

    enum class Type {
        SingleQubit,
        CNOT
    };

    Type type;

    Matrix gate;
    std::size_t firstQubit = 0;
    std::size_t secondQubit = 0;
};

class QuantumCircuit {
private:
    std::size_t numberOfQubits;
    std::vector<Operation> operations;

public:
    explicit QuantumCircuit(
        std::size_t qubitCount
    )
        : numberOfQubits(qubitCount) {
        if (qubitCount == 0) {
            throw std::invalid_argument(
                "Circuit must contain at least one qubit."
            );
        }
    }

    void addGate(
        const std::string& name,
        const Matrix& gate,
        std::size_t targetQubit
    ) {
        if (targetQubit >= numberOfQubits) {
            throw std::out_of_range(
                "Target qubit is out of range."
            );
        }

        if (!isUnitary(gate)) {
            throw std::invalid_argument(
                "Circuit gates must be unitary."
            );
        }

        operations.push_back({
            name,
            Operation::Type::SingleQubit,
            gate,
            targetQubit,
            0
        });
    }

    void addCNOT(
        std::size_t controlQubit,
        std::size_t targetQubit
    ) {
        if (
            controlQubit >= numberOfQubits ||
            targetQubit >= numberOfQubits
        ) {
            throw std::out_of_range(
                "CNOT qubit is out of range."
            );
        }

        if (controlQubit == targetQubit) {
            throw std::invalid_argument(
                "CNOT control and target must differ."
            );
        }

        operations.push_back({
            "CNOT",
            Operation::Type::CNOT,
            {},
            controlQubit,
            targetQubit
        });
    }

    StateVector run() const {
        StateVector state =
            computationalBasisState(
                std::string(
                    numberOfQubits,
                    '0'
                )
            );

        for (const Operation& operation :
             operations) {
            if (
                operation.type ==
                Operation::Type::SingleQubit
            ) {
                state =
                    applySingleQubitGate(
                        state,
                        operation.gate,
                        operation.firstQubit,
                        numberOfQubits
                    );
            } else {
                state =
                    applyCNOT(
                        state,
                        operation.firstQubit,
                        operation.secondQubit,
                        numberOfQubits
                    );
            }
        }

        return state;
    }

    void describe() const {
        std::cout
            << "\nCircuit with "
            << numberOfQubits
            << " qubits:\n";

        for (
            std::size_t index = 0;
            index < operations.size();
            ++index
        ) {
            const Operation& operation =
                operations[index];

            std::cout
                << "  "
                << index + 1
                << ". "
                << operation.name;

            if (
                operation.type ==
                Operation::Type::SingleQubit
            ) {
                std::cout
                    << " q"
                    << operation.firstQubit;
            } else {
                std::cout
                    << " q"
                    << operation.firstQubit
                    << " -> q"
                    << operation.secondQubit;
            }

            std::cout << '\n';
        }
    }
};

// ---------------------------------------------------------------------------
// BB84-inspired communication model
// ---------------------------------------------------------------------------

struct QubitTransmission {
    int bit;
    int preparationBasis;
    int measurementBasis;
    int measurementResult;
};

StateVector prepareBB84State(
    int bit,
    int basis
) {
    if (bit != 0 && bit != 1) {
        throw std::invalid_argument(
            "Bit must be 0 or 1."
        );
    }

    if (basis != 0 && basis != 1) {
        throw std::invalid_argument(
            "Basis must be 0 or 1."
        );
    }

    StateVector state =
        basisState(bit);

    // Basis 0 = computational/Z basis.
    // Basis 1 = Hadamard/X basis.
    if (basis == 1) {
        state =
            applyGate(
                state,
                hadamard()
            );
    }

    return state;
}

int measureBB84State(
    const StateVector& transmittedState,
    int measurementBasis,
    std::mt19937_64& generator
) {
    if (
        measurementBasis != 0 &&
        measurementBasis != 1
    ) {
        throw std::invalid_argument(
            "Measurement basis must be 0 or 1."
        );
    }

    StateVector state =
        transmittedState;

    // To measure in the X basis using a Z-basis
    // measurement device, rotate with H first.
    if (measurementBasis == 1) {
        state =
            applyGate(
                state,
                hadamard()
            );
    }

    const auto result =
        measure(
            state,
            1,
            generator
        );

    return result.first == "1" ? 1 : 0;
}

std::vector<QubitTransmission>
simulateBB84(
    std::size_t transmissions,
    std::mt19937_64& generator
) {
    std::uniform_int_distribution<int>
        bitDistribution(0, 1);

    std::vector<QubitTransmission>
        records;

    records.reserve(transmissions);

    for (
        std::size_t index = 0;
        index < transmissions;
        ++index
    ) {
        const int aliceBit =
            bitDistribution(generator);

        const int aliceBasis =
            bitDistribution(generator);

        const int bobBasis =
            bitDistribution(generator);

        const StateVector state =
            prepareBB84State(
                aliceBit,
                aliceBasis
            );

        const int bobResult =
            measureBB84State(
                state,
                bobBasis,
                generator
            );

        records.push_back({
            aliceBit,
            aliceBasis,
            bobBasis,
            bobResult
        });
    }

    return records;
}

// ---------------------------------------------------------------------------
// Bit-flip noise model
// ---------------------------------------------------------------------------

StateVector applyBitFlipNoise(
    const StateVector& state,
    double probability,
    std::mt19937_64& generator
) {
    if (
        probability < 0.0 ||
        probability > 1.0
    ) {
        throw std::invalid_argument(
            "Noise probability must be between 0 and 1."
        );
    }

    std::uniform_real_distribution<double>
        distribution(0.0, 1.0);

    if (distribution(generator) < probability) {
        return applyGate(
            state,
            pauliX()
        );
    }

    return state;
}

// ---------------------------------------------------------------------------
// Reporting helpers
// ---------------------------------------------------------------------------

void printState(
    const StateVector& state,
    std::size_t numberOfQubits,
    const std::string& title
) {
    std::cout
        << "\n"
        << title
        << '\n';

    validateNormalized(state);

    for (
        std::size_t index = 0;
        index < state.size();
        ++index
    ) {
        const double probability =
            std::norm(state[index]);

        if (
            std::abs(state[index]) >
            EPSILON
        ) {
            std::cout
                << "  |"
                << bitString(
                    index,
                    numberOfQubits
                )
                << "> amplitude="
                << state[index]
                << " probability="
                << std::fixed
                << std::setprecision(6)
                << probability
                << '\n';
        }
    }
}

void printHistogram(
    const std::map<std::string, std::size_t>&
        histogram
) {
    for (
        const auto& [outcome, count] :
        histogram
    ) {
        std::cout
            << "  "
            << outcome
            << ": "
            << count
            << '\n';
    }
}

// ---------------------------------------------------------------------------
// Case-study workflow
// ---------------------------------------------------------------------------

void demonstrateBellState(
    std::mt19937_64& generator
) {
    std::cout
        << "\n============================================================\n"
        << "CASE STUDY PART 1: ENTANGLED QUBIT PAIR\n"
        << "============================================================\n";

    QuantumCircuit bellCircuit(2);

    bellCircuit.addGate(
        "Hadamard",
        hadamard(),
        0
    );

    bellCircuit.addCNOT(
        0,
        1
    );

    bellCircuit.describe();

    const StateVector bellState =
        bellCircuit.run();

    printState(
        bellState,
        2,
        "Bell state"
    );

    const auto histogram =
        sampleMeasurements(
            bellState,
            2,
            2000,
            generator
        );

    std::cout
        << "\n2000-shot Bell-state measurement:\n";

    printHistogram(histogram);

    std::cout
        << "\nOnly 00 and 11 have ideal non-zero "
        << "computational-basis probability. "
        << "This is a direct demonstration of "
        << "strong measurement correlation.\n";
}

void demonstrateBB84CaseStudy(
    std::mt19937_64& generator
) {
    std::cout
        << "\n============================================================\n"
        << "CASE STUDY PART 2: QUANTUM COMMUNICATION\n"
        << "============================================================\n";

    constexpr std::size_t transmissions = 32;

    const auto records =
        simulateBB84(
            transmissions,
            generator
        );

    std::vector<int> aliceKey;
    std::vector<int> bobKey;

    std::cout
        << "\n"
        << "Idx  AliceBit  AliceBasis  BobBasis  BobResult  Sifted\n";

    for (
        std::size_t index = 0;
        index < records.size();
        ++index
    ) {
        const auto& record =
            records[index];

        const bool sifted =
            record.preparationBasis ==
            record.measurementBasis;

        std::cout
            << std::setw(3)
            << index
            << std::setw(10)
            << record.bit
            << std::setw(12)
            << record.preparationBasis
            << std::setw(10)
            << record.measurementBasis
            << std::setw(11)
            << record.measurementResult
            << std::setw(8)
            << (sifted ? "yes" : "no")
            << '\n';

        if (sifted) {
            aliceKey.push_back(record.bit);
            bobKey.push_back(
                record.measurementResult
            );
        }
    }

    std::size_t mismatches = 0;

    for (
        std::size_t index = 0;
        index < aliceKey.size();
        ++index
    ) {
        if (
            aliceKey[index] !=
            bobKey[index]
        ) {
            ++mismatches;
        }
    }

    std::cout
        << "\nSifted key length: "
        << aliceKey.size()
        << '\n';

    std::cout
        << "Sifted mismatches: "
        << mismatches
        << '\n';

    std::cout
        << "\nThe example demonstrates the physical "
        << "basis-selection mechanism. It is not a "
        << "production cryptographic protocol. "
        << "Real QKD systems require authentication, "
        << "security proofs, finite-key analysis, "
        << "error correction, privacy amplification, "
        << "careful optical/electronic modeling, and "
        << "hardware security controls.\n";
}

void demonstrateNoise(
    std::mt19937_64& generator
) {
    std::cout
        << "\n============================================================\n"
        << "CASE STUDY PART 3: NOISY QUANTUM CHANNEL\n"
        << "============================================================\n";

    constexpr std::size_t shots = 5000;
    constexpr double bitFlipProbability = 0.08;

    std::size_t observedFlips = 0;

    for (
        std::size_t shot = 0;
        shot < shots;
        ++shot
    ) {
        const StateVector transmitted =
            applyBitFlipNoise(
                basisState(0),
                bitFlipProbability,
                generator
            );

        if (
            std::norm(transmitted[1]) >
            0.5
        ) {
            ++observedFlips;
        }
    }

    const double observedRate =
        static_cast<double>(observedFlips)
        / static_cast<double>(shots);

    std::cout
        << "Configured bit-flip probability: "
        << bitFlipProbability
        << '\n';

    std::cout
        << "Observed flip rate: "
        << observedRate
        << '\n';

    std::cout
        << "\nThis simplified channel treats noise as a "
        << "random Pauli-X event. Actual devices exhibit "
        << "multiple error mechanisms, including "
        << "dephasing, relaxation, leakage, readout error, "
        << "gate error, and correlated noise.\n";
}

void demonstrateScaling() {
    std::cout
        << "\n============================================================\n"
        << "CASE STUDY PART 4: CLASSICAL SIMULATION SCALING\n"
        << "============================================================\n";

    for (
        std::size_t qubits :
        {1ULL, 2ULL, 4ULL, 8ULL, 12ULL, 16ULL, 20ULL}
    ) {
        const std::size_t amplitudes =
            static_cast<std::size_t>(1ULL << qubits);

        const std::size_t bytes =
            amplitudes * sizeof(Complex);

        const double megabytes =
            static_cast<double>(bytes)
            / (1024.0 * 1024.0);

        std::cout
            << std::setw(2)
            << qubits
            << " qubits -> "
            << std::setw(10)
            << amplitudes
            << " amplitudes -> approximately "
            << std::fixed
            << std::setprecision(2)
            << megabytes
            << " MiB for raw complex amplitudes\n";
    }

    std::cout
        << "\nA dense state-vector representation requires "
        << "2^n amplitudes for n qubits. This exponential "
        << "growth is a fundamental simulation constraint.\n";
}

void demonstrateValidation() {
    std::cout
        << "\n============================================================\n"
        << "VALIDATION AND FAILURE CONDITIONS\n"
        << "============================================================\n";

    try {
        basisState(3);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid basis state rejected: "
            << error.what()
            << '\n';
    }

    try {
        QuantumCircuit circuit(2);
        circuit.addCNOT(0, 0);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid CNOT rejected: "
            << error.what()
            << '\n';
    }

    try {
        applyBitFlipNoise(
            basisState(0),
            1.5,
            *new std::mt19937_64(1)
        );
    } catch (const std::exception& error) {
        std::cout
            << "Invalid noise probability rejected: "
            << error.what()
            << '\n';
    }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "QUBITS: C++ QUANTUM SYSTEM CASE STUDY\n"
            << "============================================================\n";

        std::mt19937_64 generator(20260921);

        // Verify common gates before using them.
        const std::vector<std::pair<
            std::string,
            Matrix
        >> gates = {
            {"X", pauliX()},
            {"Y", pauliY()},
            {"Z", pauliZ()},
            {"H", hadamard()},
            {"S", phaseS()},
            {"T", phaseT()},
            {"Rx", rotationX(PI / 3.0)},
            {"Ry", rotationY(PI / 3.0)},
            {"Rz", rotationZ(PI / 3.0)}
        };

        std::cout
            << "\nGate validation:\n";

        for (const auto& [name, gate] : gates) {
            std::cout
                << "  "
                << name
                << " -> unitary="
                << (isUnitary(gate) ? "true" : "false")
                << '\n';
        }

        demonstrateBellState(generator);
        demonstrateBB84CaseStudy(generator);
        demonstrateNoise(generator);
        demonstrateScaling();
        demonstrateValidation();

        std::cout
            << "\n============================================================\n"
            << "END OF C++ QUBIT CASE STUDY\n"
            << "============================================================\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
