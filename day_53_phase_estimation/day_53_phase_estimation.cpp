#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Quantum Phase Estimation governance-style case study:
 *
 * This program models a phase-estimation experiment as a small numerical
 * engine. It deliberately uses a direct state-vector representation so the
 * relationship between controlled powers, phase accumulation, inverse QFT,
 * and measurement is explicit.
 *
 * For U|psi> = exp(2*pi*i*theta)|psi>, the measured integer y estimates
 * theta by y / 2^m.
 *
 * Compile:
 *   g++ -std=c++17 -O2 qpe.cpp -o qpe
 */

namespace qpe {

constexpr double PI = 3.141592653589793238462643383279502884;
constexpr double EPSILON = 1e-12;

using Complex = std::complex<double>;
using State = std::vector<Complex>;

struct EstimationResult {
    double theta{};
    unsigned qubits{};
    std::vector<double> probabilities;
    unsigned most_likely{};
    double estimate{};
};

void validate_theta(double theta) {
    if (!std::isfinite(theta) || theta < 0.0 || theta >= 1.0) {
        throw std::invalid_argument(
            "theta must be finite and satisfy 0 <= theta < 1"
        );
    }
}

void validate_qubits(unsigned qubits) {
    if (qubits == 0 || qubits > 20) {
        throw std::invalid_argument(
            "qubits must be between 1 and 20"
        );
    }
}

double state_norm(const State& state) {
    double sum = 0.0;

    for (const Complex& amplitude : state) {
        sum += std::norm(amplitude);
    }

    return std::sqrt(sum);
}

void normalize(State& state) {
    const double norm = state_norm(state);

    if (norm < EPSILON) {
        throw std::runtime_error("cannot normalize zero state");
    }

    for (Complex& amplitude : state) {
        amplitude /= norm;
    }
}

State create_plus_register(unsigned qubits) {
    validate_qubits(qubits);

    const std::size_t dimension = std::size_t{1} << qubits;
    const double amplitude = 1.0 / std::sqrt(
        static_cast<double>(dimension)
    );

    State state(dimension, Complex(amplitude, 0.0));
    return state;
}

State apply_controlled_phase_power(
    const State& state,
    double theta,
    unsigned control_qubit
) {
    validate_theta(theta);

    if (control_qubit >= 63) {
        throw std::invalid_argument("control qubit is too large");
    }

    const double exponent =
        theta * static_cast<double>(std::uint64_t{1} << control_qubit);

    const Complex phase = std::polar(1.0, 2.0 * PI * exponent);

    State result = state;

    for (std::size_t basis = 0; basis < state.size(); ++basis) {
        const bool control_is_one =
            ((basis >> control_qubit) & std::size_t{1}) != 0;

        if (control_is_one) {
            result[basis] *= phase;
        }
    }

    return result;
}

State inverse_qft(const State& state) {
    const std::size_t dimension = state.size();

    if (dimension == 0 ||
        (dimension & (dimension - 1)) != 0) {
        throw std::invalid_argument(
            "inverse QFT requires a power-of-two state dimension"
        );
    }

    State transformed(dimension, Complex(0.0, 0.0));
    const double scale = 1.0 / std::sqrt(
        static_cast<double>(dimension)
    );

    /*
     * Direct O(N^2) inverse QFT is used for clarity. Hardware implementations
     * use a decomposed QFT circuit with O(m^2) elementary gates.
     */
    for (std::size_t y = 0; y < dimension; ++y) {
        Complex total(0.0, 0.0);

        for (std::size_t x = 0; x < dimension; ++x) {
            const double angle =
                -2.0 * PI *
                static_cast<double>(x * y) /
                static_cast<double>(dimension);

            total += state[x] * std::polar(1.0, angle);
        }

        transformed[y] = total * scale;
    }

    normalize(transformed);
    return transformed;
}

std::vector<double> probabilities(const State& state) {
    std::vector<double> result;
    result.reserve(state.size());

    double total = 0.0;

    for (const Complex& amplitude : state) {
        const double probability = std::norm(amplitude);
        result.push_back(probability);
        total += probability;
    }

    if (total < EPSILON) {
        throw std::runtime_error("state has zero probability mass");
    }

    for (double& probability : result) {
        probability /= total;
    }

    return result;
}

unsigned most_likely(const std::vector<double>& values) {
    if (values.empty()) {
        throw std::invalid_argument("probability distribution is empty");
    }

    return static_cast<unsigned>(
        std::distance(
            values.begin(),
            std::max_element(values.begin(), values.end())
        )
    );
}

std::vector<unsigned> sample_measurements(
    const std::vector<double>& probability,
    unsigned samples,
    unsigned seed
) {
    if (samples == 0) {
        throw std::invalid_argument("sample count must be positive");
    }

    std::mt19937 generator(seed);
    std::discrete_distribution<unsigned> distribution(
        probability.begin(),
        probability.end()
    );

    std::vector<unsigned> measurements;
    measurements.reserve(samples);

    for (unsigned i = 0; i < samples; ++i) {
        measurements.push_back(distribution(generator));
    }

    return measurements;
}

EstimationResult estimate_phase(
    double theta,
    unsigned qubits
) {
    validate_theta(theta);
    validate_qubits(qubits);

    /*
     * The target eigenstate is |1>. Since the target state is already an
     * eigenstate, only the counting register has to be numerically simulated.
     */
    State state = create_plus_register(qubits);

    for (unsigned control = 0; control < qubits; ++control) {
        state = apply_controlled_phase_power(
            state,
            theta,
            control
        );
    }

    state = inverse_qft(state);

    std::vector<double> probability = probabilities(state);

    const unsigned result = most_likely(probability);
    const double scale =
        static_cast<double>(std::size_t{1} << qubits);

    return {
        theta,
        qubits,
        probability,
        result,
        static_cast<double>(result) / scale
    };
}

void print_distribution(
    const EstimationResult& result,
    double threshold = 1e-4
) {
    const double scale =
        static_cast<double>(std::size_t{1} << result.qubits);

    std::cout << "\nProbability distribution\n";

    for (std::size_t index = 0;
         index < result.probabilities.size();
         ++index) {

        if (result.probabilities[index] >= threshold) {
            std::cout
                << "  y=" << std::setw(3) << index
                << " phase=" << std::fixed
                << std::setprecision(8)
                << static_cast<double>(index) / scale
                << " probability="
                << result.probabilities[index]
                << '\n';
        }
    }
}

void print_measurement_histogram(
    const EstimationResult& result,
    unsigned samples,
    unsigned seed
) {
    const auto measurements =
        sample_measurements(
            result.probabilities,
            samples,
            seed
        );

    std::vector<unsigned> counts(
        result.probabilities.size(),
        0
    );

    for (unsigned value : measurements) {
        ++counts[value];
    }

    const double scale =
        static_cast<double>(std::size_t{1} << result.qubits);

    std::cout << "\nMeasurement histogram\n";

    for (std::size_t index = 0;
         index < counts.size();
         ++index) {

        if (counts[index] > 0) {
            std::cout
                << "  y=" << std::setw(3) << index
                << " phase="
                << std::fixed << std::setprecision(8)
                << static_cast<double>(index) / scale
                << " count="
                << counts[index]
                << '\n';
        }
    }
}

void demonstrate_precision() {
    const double theta = 0.3125;

    std::cout << "\nPrecision as counting-register size changes\n";

    for (unsigned qubits : {3u, 4u, 5u, 6u}) {
        const EstimationResult result =
            estimate_phase(theta, qubits);

        std::cout
            << "qubits=" << qubits
            << " estimate="
            << std::fixed << std::setprecision(8)
            << result.estimate
            << " error="
            << std::abs(theta - result.estimate)
            << '\n';
    }
}

void demonstrate_validation() {
    std::cout << "\nValidation and failure handling\n";

    try {
        estimate_phase(1.0, 4);
    } catch (const std::exception& error) {
        std::cout
            << "Rejected phase: "
            << error.what()
            << '\n';
    }

    try {
        estimate_phase(0.25, 0);
    } catch (const std::exception& error) {
        std::cout
            << "Rejected qubit count: "
            << error.what()
            << '\n';
    }
}

} // namespace qpe

int main() {
    try {
        std::cout << "Quantum Phase Estimation\n";
        std::cout << "========================\n";

        const qpe::EstimationResult exact =
            qpe::estimate_phase(0.625, 4);

        std::cout << "\nExactly representable phase\n";
        std::cout
            << "Target:       "
            << std::fixed << std::setprecision(8)
            << exact.theta << '\n';

        std::cout
            << "Most likely:  "
            << exact.most_likely << '\n';

        std::cout
            << "Estimate:     "
            << exact.estimate << '\n';

        std::cout
            << "Absolute error: "
            << std::abs(exact.theta - exact.estimate)
            << '\n';

        qpe::print_distribution(exact);

        const qpe::EstimationResult approximate =
            qpe::estimate_phase(0.37, 5);

        std::cout << "\nNon-binary phase\n";
        std::cout
            << "Target:       "
            << approximate.theta << '\n';
        std::cout
            << "Estimate:     "
            << approximate.estimate << '\n';
        std::cout
            << "Absolute error: "
            << std::abs(
                approximate.theta -
                approximate.estimate
            )
            << '\n';

        qpe::print_distribution(approximate);
        qpe::print_measurement_histogram(
            approximate,
            2000,
            41
        );

        qpe::demonstrate_precision();
        qpe::demonstrate_validation();

        std::cout << "\nEngineering constraints\n";
        std::cout
            << "State-vector memory grows exponentially with "
               "the number of simulated qubits.\n";
        std::cout
            << "The direct inverse QFT is O(N^2), where N=2^m.\n";
        std::cout
            << "Floating-point rounding can accumulate for large "
               "simulated registers.\n";
        std::cout
            << "Real quantum hardware replaces the explicit state "
               "vector with physical amplitudes.\n";
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
