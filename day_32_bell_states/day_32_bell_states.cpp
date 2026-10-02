/*
 * Bell States: Generate and Measure Bell Pairs
 *
 * C++17 case study:
 * A laboratory-style Bell-pair experiment manager prepares entangled pairs,
 * applies configurable measurement bases, records shot outcomes, evaluates
 * correlations, identifies the prepared Bell state, and reports the effect
 * of stochastic bit-flip noise.
 *
 * The program intentionally uses the C++ standard library only.
 */

#include <array>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>

namespace bell_lab {

constexpr double PI = 3.14159265358979323846;
constexpr double SQRT_HALF = 0.70710678118654752440;

using Complex = std::complex<double>;
using State = std::array<Complex, 4>;
using Matrix2 = std::array<std::array<Complex, 2>, 2>;
using Matrix4 = std::array<std::array<Complex, 4>, 4>;

enum class BellState {
    PhiPlus,
    PhiMinus,
    PsiPlus,
    PsiMinus
};

enum class Basis {
    Z,
    X
};

struct MeasurementCounts {
    std::array<std::size_t, 4> counts{0, 0, 0, 0};

    std::size_t total() const {
        return counts[0] + counts[1] + counts[2] + counts[3];
    }
};

struct ExperimentConfig {
    BellState target;
    std::size_t shots;
    double bit_flip_probability;
    std::uint64_t seed;
};

struct ExperimentResult {
    MeasurementCounts z_measurements;
    MeasurementCounts x_measurements;
    double z_correlation;
    double x_correlation;
    BellState identified_state;
};

const std::array<std::string, 4> BASIS_LABELS = {
    "00", "01", "10", "11"
};


// ---------------------------------------------------------------------------
// Complex state-vector operations
// ---------------------------------------------------------------------------

double norm(const State& state) {
    double total = 0.0;

    for (const auto& amplitude : state) {
        total += std::norm(amplitude);
    }

    return std::sqrt(total);
}

State normalize(State state) {
    const double state_norm = norm(state);

    if (state_norm == 0.0) {
        throw std::invalid_argument("Cannot normalize a zero state.");
    }

    for (auto& amplitude : state) {
        amplitude /= state_norm;
    }

    return state;
}

State apply_single_qubit_gate(
    const State& state,
    const Matrix2& gate,
    int qubit
) {
    if (qubit != 0 && qubit != 1) {
        throw std::invalid_argument("Qubit index must be 0 or 1.");
    }

    State result{
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0}
    };

    /*
     * Basis ordering is |00>, |01>, |10>, |11>.
     * Bit position 1 represents qubit 0 and bit position 0 represents
     * qubit 1. This keeps the printed state ordering intuitive.
     */
    for (int index = 0; index < 4; ++index) {
        const int bit = (index >> (1 - qubit)) & 1;

        for (int output_bit = 0; output_bit <= 1; ++output_bit) {
            int source_index = index;

            if (output_bit != bit) {
                source_index ^= (1 << (1 - qubit));
            }

            result[source_index] += gate[output_bit][bit] * state[index];
        }
    }

    return normalize(result);
}

State apply_two_qubit_gate(
    const State& state,
    const Matrix4& gate
) {
    State result{
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0}
    };

    for (std::size_t row = 0; row < 4; ++row) {
        for (std::size_t column = 0; column < 4; ++column) {
            result[row] += gate[row][column] * state[column];
        }
    }

    return normalize(result);
}


// ---------------------------------------------------------------------------
// Gates used by Bell-state circuits
// ---------------------------------------------------------------------------

const Matrix2 HADAMARD = {{
    {{
        Complex{SQRT_HALF, 0.0},
        Complex{SQRT_HALF, 0.0}
    }},
    {{
        Complex{SQRT_HALF, 0.0},
        Complex{-SQRT_HALF, 0.0}
    }}
}};

const Matrix2 PAULI_X = {{
    {{
        Complex{0.0, 0.0},
        Complex{1.0, 0.0}
    }},
    {{
        Complex{1.0, 0.0},
        Complex{0.0, 0.0}
    }}
}};

const Matrix2 PAULI_Z = {{
    {{
        Complex{1.0, 0.0},
        Complex{0.0, 0.0}
    }},
    {{
        Complex{0.0, 0.0},
        Complex{-1.0, 0.0}
    }}
}};

const Matrix4 CNOT_GATE = {{
    {{
        Complex{1.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0}
    }},
    {{
        Complex{0.0, 0.0},
        Complex{1.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0}
    }},
    {{
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{1.0, 0.0}
    }},
    {{
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{1.0, 0.0},
        Complex{0.0, 0.0}
    }}
};


// ---------------------------------------------------------------------------
// Bell-state preparation
// ---------------------------------------------------------------------------

State initial_state() {
    return State{
        Complex{1.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0}
    };
}

std::string bell_name(BellState state) {
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

    throw std::invalid_argument("Unknown Bell-state enum value.");
}

State generate_bell_pair(BellState target) {
    /*
     * The shared Bell-generation core is:
     *
     * |00> --H--●--
     *           |
     * |00> -----X--
     *
     * which creates Phi+.
     *
     * Local Pauli operations transform Phi+ into the other Bell states.
     */
    State state = initial_state();

    state = apply_single_qubit_gate(state, HADAMARD, 0);
    state = apply_two_qubit_gate(state, CNOT_GATE);

    switch (target) {
        case BellState::PhiPlus:
            return state;

        case BellState::PhiMinus:
            return apply_single_qubit_gate(state, PAULI_Z, 0);

        case BellState::PsiPlus:
            return apply_single_qubit_gate(state, PAULI_X, 1);

        case BellState::PsiMinus:
            state = apply_single_qubit_gate(state, PAULI_X, 1);
            return apply_single_qubit_gate(state, PAULI_Z, 0);
    }

    throw std::invalid_argument("Unsupported Bell state.");
}


// ---------------------------------------------------------------------------
// Measurement engine
// ---------------------------------------------------------------------------

std::map<std::string, double> probabilities(const State& state) {
    std::map<std::string, double> result;

    for (std::size_t index = 0; index < 4; ++index) {
        result[BASIS_LABELS[index]] = std::norm(state[index]);
    }

    return result;
}

int sample_index(
    const State& state,
    std::mt19937_64& generator
) {
    const auto probability_map = probabilities(state);

    std::uniform_real_distribution<double> distribution(0.0, 1.0);
    const double random_value = distribution(generator);

    double cumulative = 0.0;
    int index = 3;

    for (int candidate = 0; candidate < 4; ++candidate) {
        cumulative += probability_map.at(BASIS_LABELS[candidate]);

        if (random_value <= cumulative) {
            index = candidate;
            break;
        }
    }

    return index;
}

State computational_basis_state(int index) {
    if (index < 0 || index > 3) {
        throw std::invalid_argument("Measurement index must be 0 through 3.");
    }

    State collapsed{
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0},
        Complex{0.0, 0.0}
    };

    collapsed[index] = Complex{1.0, 0.0};
    return collapsed;
}

int measure(
    State state,
    Basis basis,
    std::mt19937_64& generator
) {
    /*
     * X-basis measurement is implemented through basis rotation:
     * H maps |+> and |-> onto computational |0> and |1>.
     *
     * A real hardware implementation may expose basis-specific measurement
     * operations directly, but the mathematical effect is equivalent.
     */
    if (basis == Basis::X) {
        state = apply_single_qubit_gate(state, HADAMARD, 0);
        state = apply_single_qubit_gate(state, HADAMARD, 1);
    }

    return sample_index(state, generator);
}

MeasurementCounts run_measurements(
    BellState target,
    Basis basis,
    std::size_t shots,
    double bit_flip_probability,
    std::mt19937_64& generator
) {
    if (shots == 0) {
        throw std::invalid_argument("The number of shots must be positive.");
    }

    if (
        bit_flip_probability < 0.0 ||
        bit_flip_probability > 1.0
    ) {
        throw std::invalid_argument(
            "Bit-flip probability must be between zero and one."
        );
    }

    MeasurementCounts result;
    std::bernoulli_distribution bit_flip(bit_flip_probability);

    for (std::size_t shot = 0; shot < shots; ++shot) {
        State pair = generate_bell_pair(target);
        int measurement = measure(pair, basis, generator);

        /*
         * Noise is injected after the ideal quantum measurement as a simple
         * detector/channel model. This is intentionally distinct from a full
         * density-matrix noise simulation.
         */
        if (bit_flip(generator)) {
            measurement ^= 2;
        }

        if (bit_flip(generator)) {
            measurement ^= 1;
        }

        ++result.counts[measurement];
    }

    return result;
}


// ---------------------------------------------------------------------------
// Correlation and Bell-state identification
// ---------------------------------------------------------------------------

double correlation(const MeasurementCounts& counts) {
    if (counts.total() == 0) {
        throw std::invalid_argument(
            "Correlation requires at least one measurement."
        );
    }

    long long score = 0;

    for (int index = 0; index < 4; ++index) {
        const int first_bit = (index >> 1) & 1;
        const int second_bit = index & 1;

        if (first_bit == second_bit) {
            score += static_cast<long long>(counts.counts[index]);
        } else {
            score -= static_cast<long long>(counts.counts[index]);
        }
    }

    return static_cast<double>(score) /
           static_cast<double>(counts.total());
}

BellState identify_bell_state(
    const MeasurementCounts& z_counts,
    const MeasurementCounts& x_counts
) {
    /*
     * Ideal Bell-state signatures:
     *
     * Phi+ : Z same, X same
     * Phi- : Z same, X opposite
     * Psi+ : Z opposite, X same
     * Psi- : Z opposite, X opposite
     *
     * Finite sampling means the empirical correlations need not equal +/-1.
     * The sign of each correlation is used as the classifier.
     */
    const bool z_same = correlation(z_counts) >= 0.0;
    const bool x_same = correlation(x_counts) >= 0.0;

    if (z_same && x_same) {
        return BellState::PhiPlus;
    }

    if (z_same && !x_same) {
        return BellState::PhiMinus;
    }

    if (!z_same && x_same) {
        return BellState::PsiPlus;
    }

    return BellState::PsiMinus;
}


// ---------------------------------------------------------------------------
// Experiment orchestration
// ---------------------------------------------------------------------------

class BellLaboratory {
public:
    explicit BellLaboratory(std::uint64_t seed)
        : generator_(seed) {}

    ExperimentResult execute(const ExperimentConfig& config) {
        validate_config(config);

        /*
         * The same seeded generator is used for both bases, but every shot
         * receives a newly prepared Bell pair. Reusing a measured state would
         * incorrectly treat a collapsed pair as an independent sample.
         */
        MeasurementCounts z_counts = run_measurements(
            config.target,
            Basis::Z,
            config.shots,
            config.bit_flip_probability,
            generator_
        );

        MeasurementCounts x_counts = run_measurements(
            config.target,
            Basis::X,
            config.shots,
            config.bit_flip_probability,
            generator_
        );

        return ExperimentResult{
            z_counts,
            x_counts,
            correlation(z_counts),
            correlation(x_counts),
            identify_bell_state(z_counts, x_counts)
        };
    }

private:
    std::mt19937_64 generator_;

    static void validate_config(const ExperimentConfig& config) {
        if (config.shots == 0) {
            throw std::invalid_argument(
                "Experiment must contain at least one shot."
            );
        }

        if (
            config.bit_flip_probability < 0.0 ||
            config.bit_flip_probability > 1.0
        ) {
            throw std::invalid_argument(
                "Noise probability is outside [0, 1]."
            );
        }
    }
};


// ---------------------------------------------------------------------------
// Reporting
// ---------------------------------------------------------------------------

void print_counts(
    const std::string& basis_name,
    const MeasurementCounts& counts
) {
    std::cout << basis_name << " counts:\n";

    for (int index = 0; index < 4; ++index) {
        std::cout
            << "  |" << BASIS_LABELS[index] << "> : "
            << counts.counts[index]
            << '\n';
    }
}

void print_state(const State& state) {
    const std::array<std::string, 4> labels{
        "|00>", "|01>", "|10>", "|11>"
    };

    bool first = true;

    for (std::size_t index = 0; index < 4; ++index) {
        if (std::abs(state[index]) < 1e-10) {
            continue;
        }

        if (!first) {
            std::cout << " + ";
        }

        std::cout
            << "("
            << std::fixed
            << std::setprecision(4)
            << state[index].real();

        if (std::abs(state[index].imag()) > 1e-10) {
            std::cout
                << (state[index].imag() >= 0.0 ? " + " : " - ")
                << std::abs(state[index].imag())
                << "i";
        }

        std::cout << ")" << labels[index];
        first = false;
    }

    if (first) {
        std::cout << "0";
    }

    std::cout << '\n';
}

void print_experiment(
    BellState expected,
    const ExperimentResult& result
) {
    std::cout << "\nTarget Bell state: "
              << bell_name(expected)
              << '\n';

    print_counts("Z-basis", result.z_measurements);
    std::cout
        << "Z correlation: "
        << std::fixed
        << std::setprecision(4)
        << result.z_correlation
        << '\n';

    print_counts("X-basis", result.x_measurements);
    std::cout
        << "X correlation: "
        << std::fixed
        << std::setprecision(4)
        << result.x_correlation
        << '\n';

    std::cout
        << "Identified Bell state: "
        << bell_name(result.identified_state)
        << '\n';
}


// ---------------------------------------------------------------------------
// Case-study workflow
// ---------------------------------------------------------------------------

void run_case_study() {
    std::cout << "BELL-PAIR LABORATORY CASE STUDY\n";
    std::cout << "============================================\n";

    const std::array<BellState, 4> all_states{
        BellState::PhiPlus,
        BellState::PhiMinus,
        BellState::PsiPlus,
        BellState::PsiMinus
    };

    std::cout << "\nPrepared state vectors:\n";

    for (const BellState state : all_states) {
        std::cout << '\n'
                  << bell_name(state)
                  << " = ";

        print_state(generate_bell_pair(state));
    }

    BellLaboratory laboratory(20261002);

    /*
     * A 10,000-shot experiment makes the empirical correlation close to its
     * ideal value while still exposing finite sampling behavior.
     */
    std::cout << "\nIdeal measurement experiments\n";
    std::cout << "-----------------------------\n";

    for (const BellState target : all_states) {
        ExperimentConfig config{
            target,
            10000,
            0.0,
            20261002
        };

        const ExperimentResult result = laboratory.execute(config);
        print_experiment(target, result);
        std::cout << '\n';
    }

    std::cout << "\nNoisy Phi+ experiment\n";
    std::cout << "---------------------\n";

    ExperimentConfig noisy_config{
        BellState::PhiPlus,
        10000,
        0.05,
        20261002
    };

    const ExperimentResult noisy_result =
        laboratory.execute(noisy_config);

    print_experiment(BellState::PhiPlus, noisy_result);
}


// ---------------------------------------------------------------------------
// Edge-case demonstrations
// ---------------------------------------------------------------------------

void run_validation_case_study() {
    std::cout << "\nValidation checks\n";
    std::cout << "-----------------\n";

    BellLaboratory laboratory(77);

    const std::vector<ExperimentConfig> invalid_configs{
        {
            BellState::PhiPlus,
            0,
            0.0,
            77
        },
        {
            BellState::PsiMinus,
            100,
            -0.1,
            77
        },
        {
            BellState::PsiPlus,
            100,
            1.1,
            77
        }
    };

    for (const auto& config : invalid_configs) {
        try {
            laboratory.execute(config);
            std::cout << "ERROR: invalid configuration accepted.\n";
        } catch (const std::invalid_argument& error) {
            std::cout
                << "Rejected configuration: "
                << error.what()
                << '\n';
        }
    }
}


// ---------------------------------------------------------------------------
// Program entry point
// ---------------------------------------------------------------------------

} // namespace bell_lab

int main() {
    try {
        bell_lab::run_case_study();
        bell_lab::run_validation_case_study();

        std::cout
            << "\nThe Bell-pair case study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal experiment error: "
            << error.what()
            << '\n';

        return 1;
    }
}
