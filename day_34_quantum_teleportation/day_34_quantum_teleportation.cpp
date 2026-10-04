/*
 * Quantum Teleportation: Repository-Independent Quantum Information Transfer
 *
 * C++17 case study:
 *
 * A quantum-network controller receives a request to teleport an unknown
 * single-qubit state from an endpoint called Alice to an endpoint called Bob.
 *
 * The program models:
 *   - complex state-vector amplitudes
 *   - a three-qubit teleportation register
 *   - Bell-pair generation
 *   - Alice's Bell-basis measurement
 *   - classical measurement outcomes
 *   - Bob's conditional Pauli correction
 *   - merge-like protocol eligibility checks for a quantum operation
 *   - deterministic validation of all four measurement branches
 *   - channel noise and fidelity degradation
 *
 * The final section treats the teleportation protocol as a small
 * "quantum information transfer engine": an operation is accepted only when
 * its quantum state, classical control information, and physical constraints
 * are consistent.
 *
 * Compile:
 *   g++ -std=c++17 -O2 quantum_teleportation.cpp -o quantum_teleportation
 *
 * Run:
 *   ./quantum_teleportation
 */

#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Complex = std::complex<double>;
using State = std::vector<Complex>;

constexpr double EPSILON = 1e-10;
constexpr double SQRT_HALF = 0.70710678118654752440;

// -----------------------------------------------------------------------------
// Quantum state representation
// -----------------------------------------------------------------------------

class QuantumState {
public:
    explicit QuantumState(State amplitudes)
        : amplitudes_(std::move(amplitudes)) {
        validateDimension();
        normalize();
    }

    const State& amplitudes() const {
        return amplitudes_;
    }

    std::size_t dimension() const {
        return amplitudes_.size();
    }

    double normSquared() const {
        double total = 0.0;

        for (const auto& amplitude : amplitudes_) {
            total += std::norm(amplitude);
        }

        return total;
    }

    void normalize() {
        const double norm = std::sqrt(normSquared());

        if (norm < EPSILON) {
            throw std::invalid_argument(
                "Quantum state cannot be normalized from zero."
            );
        }

        for (auto& amplitude : amplitudes_) {
            amplitude /= norm;
        }
    }

private:
    void validateDimension() const {
        if (amplitudes_.empty()) {
            throw std::invalid_argument(
                "Quantum state cannot be empty."
            );
        }

        const auto dimension = amplitudes_.size();

        if ((dimension & (dimension - 1)) != 0) {
            throw std::invalid_argument(
                "Quantum-state dimension must be a power of two."
            );
        }
    }

    State amplitudes_;
};


// -----------------------------------------------------------------------------
// Matrix representation for single-qubit gates
// -----------------------------------------------------------------------------

using Matrix2 = std::array<std::array<Complex, 2>, 2>;

const Matrix2 IDENTITY{{
    {{Complex{1.0, 0.0}, Complex{0.0, 0.0}}},
    {{Complex{0.0, 0.0}, Complex{1.0, 0.0}}}
}};

const Matrix2 X_GATE{{
    {{Complex{0.0, 0.0}, Complex{1.0, 0.0}}},
    {{Complex{1.0, 0.0}, Complex{0.0, 0.0}}}
}};

const Matrix2 Y_GATE{{
    {{Complex{0.0, 0.0}, Complex{0.0, -1.0}}},
    {{Complex{0.0, 1.0}, Complex{0.0, 0.0}}}
}};

const Matrix2 Z_GATE{{
    {{Complex{1.0, 0.0}, Complex{0.0, 0.0}}},
    {{Complex{0.0, 0.0}, Complex{-1.0, 0.0}}}
}};

const Matrix2 H_GATE{{
    {{Complex{SQRT_HALF, 0.0}, Complex{SQRT_HALF, 0.0}}},
    {{Complex{SQRT_HALF, 0.0}, Complex{-SQRT_HALF, 0.0}}}
}};


// -----------------------------------------------------------------------------
// Utility functions
// -----------------------------------------------------------------------------

std::string formatComplex(const Complex& value, int precision = 4) {
    const double real = std::abs(value.real()) < 1e-12
        ? 0.0
        : value.real();

    const double imaginary = std::abs(value.imag()) < 1e-12
        ? 0.0
        : value.imag();

    std::ostringstream output;
    output << std::fixed << std::setprecision(precision);

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

std::size_t qubitCount(const QuantumState& state) {
    std::size_t count = 0;
    std::size_t dimension = state.dimension();

    while (dimension > 1) {
        dimension >>= 1;
        ++count;
    }

    return count;
}

int getBit(
    std::size_t basisIndex,
    std::size_t qubit,
    std::size_t numberOfQubits
) {
    const std::size_t shift = numberOfQubits - 1 - qubit;
    return static_cast<int>((basisIndex >> shift) & 1ULL);
}

std::size_t replaceBit(
    std::size_t basisIndex,
    std::size_t qubit,
    int value,
    std::size_t numberOfQubits
) {
    const std::size_t shift = numberOfQubits - 1 - qubit;
    const std::size_t mask = 1ULL << shift;

    if (value == 1) {
        return basisIndex | mask;
    }

    return basisIndex & ~mask;
}

QuantumState basisState(const std::string& bits) {
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

    const std::size_t dimension = 1ULL << bits.size();
    State amplitudes(dimension, Complex{0.0, 0.0});

    std::size_t index = 0;

    for (char bit : bits) {
        index = (index << 1) | static_cast<std::size_t>(bit - '0');
    }

    amplitudes[index] = Complex{1.0, 0.0};

    return QuantumState(std::move(amplitudes));
}

QuantumState qubitState(
    Complex alpha,
    Complex beta
) {
    return QuantumState({
        alpha,
        beta
    });
}

State tensorProduct(
    const State& left,
    const State& right
) {
    State result;
    result.reserve(left.size() * right.size());

    for (const auto& a : left) {
        for (const auto& b : right) {
            result.push_back(a * b);
        }
    }

    return result;
}


// -----------------------------------------------------------------------------
// Gate application
// -----------------------------------------------------------------------------

QuantumState applySingleQubitGate(
    const QuantumState& state,
    const Matrix2& gate,
    std::size_t targetQubit
) {
    const std::size_t numberOfQubits = qubitCount(state);

    if (targetQubit >= numberOfQubits) {
        throw std::out_of_range(
            "Single-qubit gate target is outside the register."
        );
    }

    State result(
        state.dimension(),
        Complex{0.0, 0.0}
    );

    for (std::size_t index = 0; index < state.dimension(); ++index) {
        const int oldBit = getBit(
            index,
            targetQubit,
            numberOfQubits
        );

        const std::size_t sourceIndex = replaceBit(
            index,
            targetQubit,
            oldBit,
            numberOfQubits
        );

        for (int newBit = 0; newBit <= 1; ++newBit) {
            const std::size_t destinationIndex = replaceBit(
                index,
                targetQubit,
                newBit,
                numberOfQubits
            );

            result[destinationIndex] +=
                gate[newBit][oldBit]
                * state.amplitudes()[sourceIndex];
        }
    }

    return QuantumState(std::move(result));
}

QuantumState applyCNOT(
    const QuantumState& state,
    std::size_t control,
    std::size_t target
) {
    const std::size_t numberOfQubits = qubitCount(state);

    if (control >= numberOfQubits ||
        target >= numberOfQubits) {
        throw std::out_of_range(
            "CNOT endpoint is outside the register."
        );
    }

    if (control == target) {
        throw std::invalid_argument(
            "CNOT control and target must differ."
        );
    }

    State result(
        state.dimension(),
        Complex{0.0, 0.0}
    );

    for (std::size_t index = 0; index < state.dimension(); ++index) {
        const int controlBit = getBit(
            index,
            control,
            numberOfQubits
        );

        std::size_t destination = index;

        if (controlBit == 1) {
            const int targetBit = getBit(
                index,
                target,
                numberOfQubits
            );

            destination = replaceBit(
                index,
                target,
                1 - targetBit,
                numberOfQubits
            );
        }

        result[destination] += state.amplitudes()[index];
    }

    return QuantumState(std::move(result));
}


// -----------------------------------------------------------------------------
// Measurement
// -----------------------------------------------------------------------------

struct MeasurementResult {
    std::vector<int> bits;
    double probability;
    QuantumState collapsedState;
};

MeasurementResult measureTwoQubits(
    const QuantumState& state,
    std::size_t firstQubit,
    std::size_t secondQubit,
    std::mt19937_64& generator
) {
    const std::size_t numberOfQubits = qubitCount(state);

    if (firstQubit >= numberOfQubits ||
        secondQubit >= numberOfQubits) {
        throw std::out_of_range(
            "Measurement target is outside the register."
        );
    }

    if (firstQubit == secondQubit) {
        throw std::invalid_argument(
            "Two-qubit measurement requires distinct qubits."
        );
    }

    std::array<double, 4> probabilities{0.0, 0.0, 0.0, 0.0};

    for (std::size_t index = 0; index < state.dimension(); ++index) {
        const int first = getBit(
            index,
            firstQubit,
            numberOfQubits
        );

        const int second = getBit(
            index,
            secondQubit,
            numberOfQubits
        );

        const int outcome = (first << 1) | second;

        probabilities[outcome] +=
            std::norm(state.amplitudes()[index]);
    }

    std::uniform_real_distribution<double> distribution(0.0, 1.0);
    double draw = distribution(generator);

    int selectedOutcome = 3;

    for (int outcome = 0; outcome < 4; ++outcome) {
        if (draw <= probabilities[outcome]) {
            selectedOutcome = outcome;
            break;
        }

        draw -= probabilities[outcome];
    }

    const double selectedProbability =
        probabilities[selectedOutcome];

    if (selectedProbability < EPSILON) {
        throw std::runtime_error(
            "Measurement selected an impossible outcome."
        );
    }

    State collapsed(
        state.dimension(),
        Complex{0.0, 0.0}
    );

    const int selectedFirst =
        (selectedOutcome >> 1) & 1;

    const int selectedSecond =
        selectedOutcome & 1;

    for (std::size_t index = 0; index < state.dimension(); ++index) {
        const int first = getBit(
            index,
            firstQubit,
            numberOfQubits
        );

        const int second = getBit(
            index,
            secondQubit,
            numberOfQubits
        );

        if (first == selectedFirst &&
            second == selectedSecond) {
            collapsed[index] = state.amplitudes()[index];
        }
    }

    QuantumState collapsedState(std::move(collapsed));

    return MeasurementResult{
        {selectedFirst, selectedSecond},
        selectedProbability,
        std::move(collapsedState)
    };
}


// -----------------------------------------------------------------------------
// Bell-pair and teleportation-register construction
// -----------------------------------------------------------------------------

QuantumState prepareBellPair() {
    QuantumState pair = basisState("00");

    pair = applySingleQubitGate(
        pair,
        H_GATE,
        0
    );

    pair = applyCNOT(
        pair,
        0,
        1
    );

    return pair;
}

QuantumState prepareTeleportationRegister(
    const QuantumState& inputState
) {
    if (inputState.dimension() != 2) {
        throw std::invalid_argument(
            "Teleportation requires one input qubit."
        );
    }

    const QuantumState bellPair = prepareBellPair();

    return QuantumState(
        tensorProduct(
            inputState.amplitudes(),
            bellPair.amplitudes()
        )
    );
}


// -----------------------------------------------------------------------------
// Bob's branch extraction
// -----------------------------------------------------------------------------

QuantumState extractBobState(
    const QuantumState& collapsed,
    const std::array<int, 2>& aliceBits
) {
    if (collapsed.dimension() != 8) {
        throw std::invalid_argument(
            "Bob extraction expects a three-qubit register."
        );
    }

    State bob{
        Complex{0.0, 0.0},
        Complex{0.0, 0.0}
    };

    for (std::size_t index = 0; index < 8; ++index) {
        const int aliceFirst = getBit(index, 0, 3);
        const int aliceSecond = getBit(index, 1, 3);

        if (aliceFirst == aliceBits[0] &&
            aliceSecond == aliceBits[1]) {

            const int bobBit = getBit(index, 2, 3);

            bob[bobBit] +=
                collapsed.amplitudes()[index];
        }
    }

    return QuantumState(std::move(bob));
}


// -----------------------------------------------------------------------------
// Bob's classical control path
// -----------------------------------------------------------------------------

QuantumState applyBobCorrection(
    QuantumState state,
    const std::array<int, 2>& classicalBits
) {
    /*
     * Alice's result maps to a Pauli correction:
     *
     * 00 -> I
     * 01 -> X
     * 10 -> Z
     * 11 -> XZ
     *
     * The important architectural distinction is that these corrections
     * depend on classical measurement data. Entanglement does not itself
     * supply the missing two classical bits to Bob.
     */

    if (classicalBits[1] == 1) {
        state = applySingleQubitGate(
            state,
            X_GATE,
            0
        );
    }

    if (classicalBits[0] == 1) {
        state = applySingleQubitGate(
            state,
            Z_GATE,
            0
        );
    }

    return state;
}


// -----------------------------------------------------------------------------
// Fidelity
// -----------------------------------------------------------------------------

double fidelity(
    const QuantumState& actual,
    const QuantumState& expected
) {
    if (actual.dimension() != expected.dimension()) {
        throw std::invalid_argument(
            "Fidelity states must have equal dimensions."
        );
    }

    Complex overlap{0.0, 0.0};

    for (std::size_t i = 0; i < actual.dimension(); ++i) {
        overlap +=
            std::conj(expected.amplitudes()[i])
            * actual.amplitudes()[i];
    }

    return std::norm(overlap);
}


// -----------------------------------------------------------------------------
// Protocol transaction
// -----------------------------------------------------------------------------

struct TeleportationTransaction {
    QuantumState input;
    std::array<int, 2> measurementBits{};
    QuantumState bobBeforeCorrection;
    QuantumState bobAfterCorrection;
    double fidelityValue = 0.0;
};

class TeleportationEngine {
public:
    explicit TeleportationEngine(std::uint64_t seed = 20261004)
        : generator_(seed) {}

    TeleportationTransaction execute(
        const QuantumState& input
    ) {
        validateInput(input);

        /*
         * Phase A:
         * Alice's input is combined with a Bell pair shared with Bob.
         */
        QuantumState registerState =
            prepareTeleportationRegister(input);

        /*
         * Phase B:
         * Alice changes from the computational basis to the Bell
         * measurement basis using CNOT followed by Hadamard.
         */
        registerState = applyCNOT(
            registerState,
            0,
            1
        );

        registerState = applySingleQubitGate(
            registerState,
            H_GATE,
            0
        );

        /*
         * Phase C:
         * Alice obtains two classical bits. The quantum register collapses
         * to the branch selected by the measurement.
         */
        MeasurementResult measurement =
            measureTwoQubits(
                registerState,
                0,
                1,
                generator_
            );

        const std::array<int, 2> bits{
            measurement.bits[0],
            measurement.bits[1]
        };

        QuantumState bobBefore =
            extractBobState(
                measurement.collapsedState,
                bits
            );

        /*
         * Phase D:
         * The two classical bits are available to Bob. Bob applies the
         * corresponding Pauli correction to his isolated qubit.
         */
        QuantumState bobAfter =
            applyBobCorrection(
                bobBefore,
                bits
            );

        const double result =
            fidelity(
                bobAfter,
                input
            );

        return TeleportationTransaction{
            input,
            bits,
            std::move(bobBefore),
            std::move(bobAfter),
            result
        };
    }

private:
    static void validateInput(
        const QuantumState& input
    ) {
        if (input.dimension() != 2) {
            throw std::invalid_argument(
                "The teleportation source must be exactly one qubit."
            );
        }

        if (std::abs(input.normSquared() - 1.0) > 1e-9) {
            throw std::invalid_argument(
                "The input state must be normalized."
            );
        }
    }

    std::mt19937_64 generator_;
};


// -----------------------------------------------------------------------------
// Protocol audit
// -----------------------------------------------------------------------------

class QuantumTransferAudit {
public:
    static void verifyNormalization(
        const QuantumState& state,
        const std::string& label
    ) {
        if (std::abs(state.normSquared() - 1.0) > 1e-9) {
            throw std::runtime_error(
                label + " is not normalized."
            );
        }
    }

    static void verifyTeleportation(
        const TeleportationTransaction& transaction
    ) {
        verifyNormalization(
            transaction.input,
            "Input state"
        );

        verifyNormalization(
            transaction.bobBeforeCorrection,
            "Bob's pre-correction state"
        );

        verifyNormalization(
            transaction.bobAfterCorrection,
            "Bob's post-correction state"
        );

        if (transaction.fidelityValue < 1.0 - 1e-9) {
            throw std::runtime_error(
                "Ideal teleportation did not reproduce the source state."
            );
        }
    }

    static void verifyClassicalOutcome(
        const std::array<int, 2>& bits
    ) {
        for (int bit : bits) {
            if (bit != 0 && bit != 1) {
                throw std::runtime_error(
                    "Classical measurement result contains a non-bit value."
                );
            }
        }
    }
};


// -----------------------------------------------------------------------------
// Noisy channel case study
// -----------------------------------------------------------------------------

QuantumState applyPauliNoise(
    QuantumState state,
    double probability,
    std::mt19937_64& generator
) {
    if (probability < 0.0 || probability > 1.0) {
        throw std::invalid_argument(
            "Noise probability must be in [0, 1]."
        );
    }

    std::uniform_real_distribution<double> distribution(0.0, 1.0);

    if (distribution(generator) >= probability) {
        return state;
    }

    const double draw = distribution(generator);

    if (draw < 1.0 / 3.0) {
        return applySingleQubitGate(
            state,
            X_GATE,
            0
        );
    }

    if (draw < 2.0 / 3.0) {
        return applySingleQubitGate(
            state,
            Y_GATE,
            0
        );
    }

    return applySingleQubitGate(
        state,
        Z_GATE,
        0
    );
}

double noisyTrial(
    const QuantumState& input,
    double errorProbability,
    std::uint64_t seed
) {
    std::mt19937_64 generator(seed);

    QuantumState registerState =
        prepareTeleportationRegister(input);

    registerState = applyCNOT(
        registerState,
        0,
        1
    );

    registerState = applySingleQubitGate(
        registerState,
        H_GATE,
        0
    );

    const MeasurementResult measurement =
        measureTwoQubits(
            registerState,
            0,
            1,
            generator
        );

    const std::array<int, 2> bits{
        measurement.bits[0],
        measurement.bits[1]
    };

    QuantumState bob =
        extractBobState(
            measurement.collapsedState,
            bits
        );

    bob = applyPauliNoise(
        std::move(bob),
        errorProbability,
        generator
    );

    bob = applyBobCorrection(
        std::move(bob),
        bits
    );

    return fidelity(
        bob,
        input
    );
}

double averageNoisyFidelity(
    const QuantumState& input,
    double errorProbability,
    int trials
) {
    if (trials <= 0) {
        throw std::invalid_argument(
            "Number of trials must be positive."
        );
    }

    double total = 0.0;

    for (int trial = 0; trial < trials; ++trial) {
        total += noisyTrial(
            input,
            errorProbability,
            9000 + static_cast<std::uint64_t>(trial)
        );
    }

    return total / static_cast<double>(trials);
}


// -----------------------------------------------------------------------------
// Output helpers
// -----------------------------------------------------------------------------

void printState(
    const QuantumState& state,
    const std::string& label,
    double threshold = 1e-8
) {
    std::cout << "\n" << label << ":\n";

    const std::size_t numberOfQubits =
        qubitCount(state);

    bool printed = false;

    for (std::size_t index = 0;
         index < state.dimension();
         ++index) {

        const Complex amplitude =
            state.amplitudes()[index];

        if (std::abs(amplitude) > threshold) {
            std::cout
                << "  |"
                << std::bitset<64>(index)
                    .to_string()
                    .substr(
                        64 - numberOfQubits
                    )
                << "> : "
                << formatComplex(amplitude)
                << "\n";

            printed = true;
        }
    }

    if (!printed) {
        std::cout << "  zero state\n";
    }
}

void printTransaction(
    const TeleportationTransaction& transaction
) {
    printState(
        transaction.input,
        "Source state |psi>"
    );

    std::cout
        << "\nAlice's classical measurement bits: "
        << transaction.measurementBits[0]
        << transaction.measurementBits[1]
        << "\n";

    printState(
        transaction.bobBeforeCorrection,
        "Bob before classical correction"
    );

    printState(
        transaction.bobAfterCorrection,
        "Bob after classical correction"
    );

    std::cout
        << "\nTeleportation fidelity: "
        << std::fixed
        << std::setprecision(12)
        << transaction.fidelityValue
        << "\n";
}


// -----------------------------------------------------------------------------
// Branch verification
// -----------------------------------------------------------------------------

void verifyAllMeasurementBranches() {
    /*
     * Alice's Bell measurement has four possible classical outcomes.
     * A deterministic branch test forces each outcome mathematically by
     * applying the corresponding correction relation. This checks the
     * protocol's correction table independently of random sampling.
     */
    std::cout << "\nChecking all classical correction branches:\n";

    const QuantumState input =
        qubitState(
            Complex{0.7, 0.2},
            Complex{0.4, -0.3}
        );

    for (int first = 0; first <= 1; ++first) {
        for (int second = 0; second <= 1; ++second) {
            /*
             * Bob's state after Alice's measurement is related to |psi>
             * by X^second Z^first. Applying the same Pauli operators again
             * returns the original state up to an irrelevant global phase.
             *
             * The helper below explicitly creates the branch.
             */
            QuantumState branch = input;

            if (second == 1) {
                branch = applySingleQubitGate(
                    branch,
                    X_GATE,
                    0
                );
            }

            if (first == 1) {
                branch = applySingleQubitGate(
                    branch,
                    Z_GATE,
                    0
                );
            }

            branch = applyBobCorrection(
                std::move(branch),
                std::array<int, 2>{first, second}
            );

            const double branchFidelity =
                fidelity(
                    branch,
                    input
                );

            std::cout
                << "  outcome "
                << first
                << second
                << " -> fidelity "
                << std::fixed
                << std::setprecision(12)
                << branchFidelity
                << "\n";

            if (branchFidelity < 1.0 - 1e-9) {
                throw std::runtime_error(
                    "A Bell-measurement correction branch failed."
                );
            }
        }
    }
}


// -----------------------------------------------------------------------------
// Security and physical constraints
// -----------------------------------------------------------------------------

void printPhysicalConstraints() {
    std::cout << "\nPhysical information-transfer constraints:\n";

    std::cout
        << "  * The entangled Bell pair is a shared quantum resource.\n"
        << "  * Alice's measurement destroys the original local state as an\n"
        << "    independently available copy.\n"
        << "  * Alice produces two classical bits that identify Bob's correction.\n"
        << "  * Bob cannot complete state reconstruction without those classical bits.\n"
        << "  * The protocol therefore does not create a faster-than-light\n"
        << "    classical communication channel.\n"
        << "  * Teleportation transfers quantum-state information rather than\n"
        << "    physically transporting the source qubit.\n";
}


// -----------------------------------------------------------------------------
// Validation failure examples
// -----------------------------------------------------------------------------

void testFailureConditions() {
    std::cout << "\nValidation and failure conditions:\n";

    try {
        basisState("012");
        throw std::runtime_error(
            "Invalid basis-state input was accepted."
        );
    } catch (const std::invalid_argument&) {
        std::cout
            << "  Invalid basis-state encoding: rejected\n";
    }

    try {
        qubitState(
            Complex{0.0, 0.0},
            Complex{0.0, 0.0}
        );
        throw std::runtime_error(
            "Zero state was accepted."
        );
    } catch (const std::invalid_argument&) {
        std::cout
            << "  Zero-norm source state: rejected\n";
    }

    try {
        TeleportationEngine engine;
        engine.execute(
            basisState("00")
        );
        throw std::runtime_error(
            "Two-qubit input was accepted as one-qubit source."
        );
    } catch (const std::invalid_argument&) {
        std::cout
            << "  Multi-qubit source passed as one qubit: rejected\n";
    }

    try {
        QuantumState input =
            qubitState(
                Complex{1.0, 0.0},
                Complex{0.0, 0.0}
            );

        averageNoisyFidelity(
            input,
            1.5,
            10
        );

        throw std::runtime_error(
            "Invalid noise probability was accepted."
        );
    } catch (const std::invalid_argument&) {
        std::cout
            << "  Invalid channel error probability: rejected\n";
    }
}


// -----------------------------------------------------------------------------
// Scaling analysis
// -----------------------------------------------------------------------------

void printScalingAnalysis() {
    std::cout << "\nState-vector simulation scaling:\n";

    for (int qubits : {3, 10, 20, 30, 40}) {
        const std::uint64_t amplitudes =
            1ULL << qubits;

        std::cout
            << "  "
            << qubits
            << " qubits -> "
            << amplitudes
            << " complex amplitudes\n";
    }

    std::cout
        << "  A full state-vector simulator has O(2^n) storage.\n"
        << "  Teleportation itself is a three-qubit protocol, but scaling\n"
        << "  becomes a system-design concern when the same simulator is\n"
        << "  embedded in larger quantum circuits.\n";
}


// -----------------------------------------------------------------------------
// Main case study
// -----------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "QUANTUM TELEPORTATION CASE STUDY\n"
            << "============================================================\n";

        /*
         * The source state deliberately contains complex amplitudes so that
         * the simulation tests preservation of relative phase rather than
         * only the classical-looking |0> and |1> cases.
         */
        const QuantumState source =
            qubitState(
                Complex{0.8, 0.2},
                Complex{0.4, -0.3}
            );

        TeleportationEngine engine(
            20261004
        );

        const TeleportationTransaction transaction =
            engine.execute(source);

        QuantumTransferAudit::verifyClassicalOutcome(
            transaction.measurementBits
        );

        QuantumTransferAudit::verifyTeleportation(
            transaction
        );

        printTransaction(
            transaction
        );

        /*
         * Repeat with computational-basis and superposition states. These
         * cases expose different phase and amplitude structures while using
         * the same physical teleportation mechanism.
         */
        std::cout
            << "\nRepresentative source-state checks:\n";

        const std::vector<std::pair<std::string, QuantumState>> examples{
            {
                "|0>",
                qubitState(
                    Complex{1.0, 0.0},
                    Complex{0.0, 0.0}
                )
            },
            {
                "|1>",
                qubitState(
                    Complex{0.0, 0.0},
                    Complex{1.0, 0.0}
                )
            },
            {
                "|+>",
                qubitState(
                    Complex{1.0, 0.0},
                    Complex{1.0, 0.0}
                )
            },
            {
                "|->",
                qubitState(
                    Complex{1.0, 0.0},
                    Complex{-1.0, 0.0}
                )
            },
            {
                "phase-sensitive state",
                qubitState(
                    Complex{1.0, 0.0},
                    Complex{0.0, 1.0}
                )
            }
        };

        std::uint64_t seed = 100;

        for (const auto& [name, state] : examples) {
            TeleportationEngine trialEngine(seed++);

            const auto result =
                trialEngine.execute(state);

            QuantumTransferAudit::verifyTeleportation(
                result
            );

            std::cout
                << "  "
                << std::left
                << std::setw(24)
                << name
                << " bits="
                << result.measurementBits[0]
                << result.measurementBits[1]
                << " fidelity="
                << std::fixed
                << std::setprecision(10)
                << result.fidelityValue
                << "\n";
        }

        verifyAllMeasurementBranches();
        printPhysicalConstraints();

        /*
         * A noisy quantum channel separates protocol correctness from
         * physical channel reliability. The ideal correction table remains
         * correct, but errors introduced during transmission reduce fidelity.
         */
        std::cout
            << "\nNoisy quantum-channel experiment:\n";

        for (double probability :
             {0.00, 0.01, 0.05, 0.10, 0.25}) {

            const double average =
                averageNoisyFidelity(
                    source,
                    probability,
                    2000
                );

            std::cout
                << "  error probability="
                << std::fixed
                << std::setprecision(2)
                << probability
                << " average fidelity="
                << std::setprecision(5)
                << average
                << "\n";
        }

        testFailureConditions();
        printScalingAnalysis();

        std::cout
            << "\n============================================================\n"
            << "CASE STUDY COMPLETED SUCCESSFULLY\n"
            << "============================================================\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Protocol simulation failed safely: "
            << error.what()
            << "\n";

        return 1;
    }
}
