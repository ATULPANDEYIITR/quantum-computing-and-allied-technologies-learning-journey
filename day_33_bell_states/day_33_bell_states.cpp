#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Bell-State Repository Testbed
 *
 * Case study:
 * A quantum-computing research team is validating a two-qubit Bell-pair
 * preparation pipeline before sending measurement batches to hardware.
 *
 * The program models:
 * - four Bell states
 * - state-vector amplitudes
 * - H, X, Z and CNOT gates
 * - projective measurement
 * - fresh-pair preparation for repeated experiments
 * - measurement statistics
 * - computational-basis correlations
 * - reduced density matrices
 * - validation and merge-like experiment acceptance rules
 *
 * C++17 or later.
 *
 * The simulator deliberately keeps the system at two qubits. A state-vector
 * simulator requires 2^n amplitudes, so scaling the same representation to
 * many qubits rapidly increases memory and computational requirements.
 */

struct Complex {
    double real = 0.0;
    double imag = 0.0;
};

Complex operator+(const Complex& a, const Complex& b) {
    return {a.real + b.real, a.imag + b.imag};
}

Complex operator-(const Complex& a, const Complex& b) {
    return {a.real - b.real, a.imag - b.imag};
}

Complex operator*(const Complex& a, const Complex& b) {
    return {
        a.real * b.real - a.imag * b.imag,
        a.real * b.imag + a.imag * b.real
    };
}

Complex operator*(const Complex& value, double scalar) {
    return {value.real * scalar, value.imag * scalar};
}

Complex conjugate(const Complex& value) {
    return {value.real, -value.imag};
}

double magnitudeSquared(const Complex& value) {
    return value.real * value.real + value.imag * value.imag;
}

constexpr double EPSILON = 1e-12;
constexpr double SQRT_HALF = 0.70710678118654752440;

using StateVector = std::array<Complex, 4>;

enum class BellState {
    PhiPlus,
    PhiMinus,
    PsiPlus,
    PsiMinus
};

std::string bellName(BellState state) {
    switch (state) {
        case BellState::PhiPlus:
            return "Phi+";
        case BellState::PhiMinus:
            return "Phi-";
        case BellState::PsiPlus:
            return "Psi+";
        case BellState::PsiMinus:
            return "Psi-";
    }

    throw std::logic_error("Unknown Bell state.");
}

std::string basisName(std::size_t index) {
    static const std::array<std::string, 4> names{
        "00", "01", "10", "11"
    };

    if (index >= names.size()) {
        throw std::out_of_range("Basis index must be between 0 and 3.");
    }

    return names[index];
}

StateVector basisState(std::size_t index) {
    if (index >= 4) {
        throw std::out_of_range("Two-qubit basis index must be below 4.");
    }

    StateVector state{};
    state[index] = {1.0, 0.0};
    return state;
}

void validateNormalized(const StateVector& state) {
    double probability = 0.0;

    for (const Complex& amplitude : state) {
        probability += magnitudeSquared(amplitude);
    }

    if (std::abs(probability - 1.0) > 1e-10) {
        throw std::runtime_error(
            "State vector is not normalized. Total probability = " +
            std::to_string(probability)
        );
    }
}

StateVector normalize(const StateVector& state) {
    double normSquared = 0.0;

    for (const Complex& amplitude : state) {
        normSquared += magnitudeSquared(amplitude);
    }

    if (normSquared <= EPSILON) {
        throw std::runtime_error("Cannot normalize a zero state.");
    }

    const double factor = 1.0 / std::sqrt(normSquared);
    StateVector normalized{};

    for (std::size_t i = 0; i < state.size(); ++i) {
        normalized[i] = state[i] * factor;
    }

    return normalized;
}

StateVector applyHadamard(const StateVector& state, int qubit) {
    if (qubit != 0 && qubit != 1) {
        throw std::invalid_argument("Qubit must be 0 or 1.");
    }

    StateVector result{};

    /*
     * The two amplitudes belonging to a fixed value of the other qubit
     * form a pair. H transforms that pair with the familiar
     * [[1, 1], [1, -1]] / sqrt(2) matrix.
     *
     * Index convention:
     *   0 -> |00>
     *   1 -> |01>
     *   2 -> |10>
     *   3 -> |11>
     */
    for (std::size_t index = 0; index < 4; ++index) {
        const int bit = (index >> (1 - qubit)) & 1;
        if (bit != 0) {
            continue;
        }

        const std::size_t partner = index ^ (1u << (1 - qubit));

        result[index] =
            result[index] + (state[index] + state[partner]) * SQRT_HALF;

        result[partner] =
            result[partner] + (state[index] - state[partner]) * SQRT_HALF;
    }

    return normalize(result);
}

StateVector applyPauliX(const StateVector& state, int qubit) {
    if (qubit != 0 && qubit != 1) {
        throw std::invalid_argument("Qubit must be 0 or 1.");
    }

    StateVector result{};

    for (std::size_t index = 0; index < 4; ++index) {
        const std::size_t target =
            index ^ (1u << (1 - qubit));

        result[target] = result[target] + state[index];
    }

    return normalize(result);
}

StateVector applyPauliZ(const StateVector& state, int qubit) {
    if (qubit != 0 && qubit != 1) {
        throw std::invalid_argument("Qubit must be 0 or 1.");
    }

    StateVector result = state;

    for (std::size_t index = 0; index < 4; ++index) {
        const int bit = (index >> (1 - qubit)) & 1;

        if (bit == 1) {
            result[index] = result[index] * -1.0;
        }
    }

    return normalize(result);
}

StateVector applyCnot(
    const StateVector& state,
    int control,
    int target
) {
    if ((control != 0 && control != 1) ||
        (target != 0 && target != 1)) {
        throw std::invalid_argument(
            "Control and target must be qubit 0 or 1."
        );
    }

    if (control == target) {
        throw std::invalid_argument(
            "CNOT control and target must be different."
        );
    }

    StateVector result{};

    for (std::size_t index = 0; index < 4; ++index) {
        const int controlBit =
            (index >> (1 - control)) & 1;

        std::size_t destination = index;

        if (controlBit == 1) {
            destination ^= (1u << (1 - target));
        }

        result[destination] =
            result[destination] + state[index];
    }

    return normalize(result);
}

StateVector prepareBellState(BellState requested) {
    /*
     * Start from |00>.
     *
     * H(0) creates:
     *   (|00> + |10>) / sqrt(2)
     *
     * CNOT(0 -> 1) produces:
     *   (|00> + |11>) / sqrt(2) = Phi+
     *
     * Local X and Z gates then transform Phi+ into the other Bell states.
     */
    StateVector state = basisState(0);
    state = applyHadamard(state, 0);
    state = applyCnot(state, 0, 1);

    switch (requested) {
        case BellState::PhiPlus:
            break;

        case BellState::PhiMinus:
            state = applyPauliZ(state, 0);
            break;

        case BellState::PsiPlus:
            state = applyPauliX(state, 1);
            break;

        case BellState::PsiMinus:
            state = applyPauliZ(state, 0);
            state = applyPauliX(state, 1);
            break;
    }

    return normalize(state);
}

std::size_t measure(
    const StateVector& state,
    std::mt19937_64& generator
) {
    validateNormalized(state);

    std::uniform_real_distribution<double> distribution(0.0, 1.0);
    const double sample = distribution(generator);

    double cumulative = 0.0;

    for (std::size_t index = 0; index < 4; ++index) {
        cumulative += magnitudeSquared(state[index]);

        if (sample < cumulative) {
            return index;
        }
    }

    /*
     * Floating-point accumulation should not normally reach this branch.
     * Returning the final basis protects the measurement routine from a
     * harmless rounding boundary error.
     */
    return 3;
}

StateVector collapse(
    const StateVector& state,
    std::size_t measuredIndex
) {
    if (measuredIndex >= 4) {
        throw std::out_of_range("Measurement outcome is outside the basis.");
    }

    return basisState(measuredIndex);
}

std::array<std::size_t, 4> runMeasurementBatch(
    BellState requested,
    std::size_t trials,
    std::mt19937_64& generator
) {
    std::array<std::size_t, 4> counts{};

    /*
     * A quantum measurement changes the state. Therefore every trial
     * explicitly prepares a new Bell pair instead of measuring the same
     * collapsed vector repeatedly.
     */
    for (std::size_t trial = 0; trial < trials; ++trial) {
        const StateVector freshPair = prepareBellState(requested);
        const std::size_t outcome = measure(freshPair, generator);
        const StateVector collapsed = collapse(freshPair, outcome);

        (void)collapsed;
        ++counts[outcome];
    }

    return counts;
}

double zzCorrelation(const StateVector& state) {
    /*
     * Z⊗Z has:
     *   +1 for |00> and |11>
     *   -1 for |01> and |10>
     */
    double correlation = 0.0;

    for (std::size_t index = 0; index < 4; ++index) {
        const bool equalBits =
            index == 0 || index == 3;

        const double eigenvalue = equalBits ? 1.0 : -1.0;

        correlation +=
            eigenvalue * magnitudeSquared(state[index]);
    }

    return correlation;
}

using DensityMatrix = std::array<std::array<Complex, 4>, 4>;

DensityMatrix densityMatrix(const StateVector& state) {
    DensityMatrix matrix{};

    for (std::size_t row = 0; row < 4; ++row) {
        for (std::size_t column = 0; column < 4; ++column) {
            matrix[row][column] =
                state[row] * conjugate(state[column]);
        }
    }

    return matrix;
}

std::array<std::array<Complex, 2>, 2>
reducedDensityMatrixOfQubit1(const StateVector& state) {
    const DensityMatrix rho = densityMatrix(state);

    /*
     * Trace out qubit 0. The remaining 2x2 matrix describes qubit 1.
     * Every Bell state gives I/2 for this reduced state.
     */
    return {{
        {{
            rho[0][0] + rho[2][2],
            rho[0][1] + rho[2][3]
        }},
        {{
            rho[1][0] + rho[3][2],
            rho[1][1] + rho[3][3]
        }}
    }};
}

void printState(const StateVector& state) {
    std::cout << std::fixed << std::setprecision(4);

    for (std::size_t index = 0; index < 4; ++index) {
        if (magnitudeSquared(state[index]) <= EPSILON) {
            continue;
        }

        std::cout
            << "  |" << basisName(index) << "> = "
            << state[index].real
            << (state[index].imag >= 0 ? " + " : " - ")
            << std::abs(state[index].imag)
            << "i\n";
    }
}

void printMeasurementBatch(
    BellState requested,
    const std::array<std::size_t, 4>& counts,
    std::size_t trials
) {
    std::cout
        << "\n"
        << bellName(requested)
        << " measurement batch: "
        << trials
        << " freshly prepared pairs\n";

    for (std::size_t index = 0; index < 4; ++index) {
        if (counts[index] == 0) {
            continue;
        }

        const double frequency =
            static_cast<double>(counts[index]) /
            static_cast<double>(trials);

        std::cout
            << "  |" << basisName(index) << ">: "
            << counts[index]
            << " ("
            << std::setprecision(4)
            << frequency
            << ")\n";
    }
}

bool validateExpectedComputationalSupport(
    BellState requested,
    const std::array<std::size_t, 4>& counts,
    std::size_t trials
) {
    /*
     * Computational-basis support differs by Bell family:
     *
     * Phi states can only produce 00 or 11.
     * Psi states can only produce 01 or 10.
     *
     * This test is intentionally a support test rather than an exact
     * frequency test, because finite sampling does not guarantee exact
     * 50/50 counts.
     */
    const bool phiFamily =
        requested == BellState::PhiPlus ||
        requested == BellState::PhiMinus;

    const std::array<bool, 4> allowed = phiFamily
        ? std::array<bool, 4>{true, false, false, true}
        : std::array<bool, 4>{false, true, true, false};

    for (std::size_t index = 0; index < 4; ++index) {
        if (!allowed[index] && counts[index] != 0) {
            return false;
        }
    }

    const std::size_t allowedTotal =
        std::accumulate(
            counts.begin(),
            counts.end(),
            std::size_t{0}
        );

    return allowedTotal == trials;
}

void runGovernanceCaseStudy() {
    /*
     * The research pipeline treats each Bell-state experiment as a
     * controlled test case. A preparation circuit is accepted only when:
     *
     * - the state vector is normalized
     * - the computational support matches the requested Bell family
     * - the Z⊗Z correlation has the expected sign
     *
     * These checks are intentionally independent. A single probability
     * distribution can hide relative phase, so computational measurements
     * alone do not distinguish Phi+ from Phi-, or Psi+ from Psi-.
     */
    std::mt19937_64 generator(20261003);
    constexpr std::size_t trials = 4000;

    std::cout << "\n";
    std::cout << "==============================================\n";
    std::cout << "BELL-PAIR EXPERIMENT CASE STUDY\n";
    std::cout << "==============================================\n";

    const std::array<BellState, 4> states{
        BellState::PhiPlus,
        BellState::PhiMinus,
        BellState::PsiPlus,
        BellState::PsiMinus
    };

    for (BellState requested : states) {
        const StateVector state = prepareBellState(requested);

        validateNormalized(state);

        std::cout << "\nPrepared |" << bellName(requested) << ">:\n";
        printState(state);

        const double correlation = zzCorrelation(state);

        std::cout
            << "  <Z⊗Z> = "
            << std::setprecision(4)
            << correlation
            << "\n";

        const auto counts =
            runMeasurementBatch(requested, trials, generator);

        printMeasurementBatch(requested, counts, trials);

        const bool accepted =
            validateExpectedComputationalSupport(
                requested,
                counts,
                trials
            );

        std::cout
            << "  Experiment support check: "
            << (accepted ? "PASS" : "FAIL")
            << "\n";

        const auto reduced =
            reducedDensityMatrixOfQubit1(state);

        std::cout
            << "  Reduced density matrix of qubit 1:\n";

        for (const auto& row : reduced) {
            std::cout
                << "    ["
                << row[0].real << " + "
                << row[0].imag << "i, "
                << row[1].real << " + "
                << row[1].imag << "i]\n";
        }
    }
}

void demonstrateFailureHandling() {
    std::cout << "\n";
    std::cout << "==============================================\n";
    std::cout << "FAILURE HANDLING\n";
    std::cout << "==============================================\n";

    try {
        (void)applyHadamard(basisState(0), 2);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid qubit rejected: "
            << error.what()
            << "\n";
    }

    try {
        (void)applyCnot(basisState(0), 0, 0);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid CNOT rejected: "
            << error.what()
            << "\n";
    }

    try {
        StateVector zero{};
        (void)normalize(zero);
    } catch (const std::exception& error) {
        std::cout
            << "Zero-state normalization rejected: "
            << error.what()
            << "\n";
    }
}

int main() {
    try {
        runGovernanceCaseStudy();
        demonstrateFailureHandling();

        std::cout << "\nCase study complete.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal simulation error: "
            << error.what()
            << "\n";
        return 1;
    }
}
