#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Qiskit Fundamentals: First-Circuit Simulation Case Study
 *
 * Scenario:
 * A quantum software team validates a two-qubit circuit before submitting
 * it to Qiskit Aer or a hardware backend. The validation engine represents
 * statevectors, applies gates, samples measurement outcomes, and checks
 * expected distributions.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic first_circuit.cpp -o first_circuit
 *
 * Qiskit itself is a Python library. This standalone C++ program models
 * the mathematics; it does not load Qiskit or communicate with hardware.
 */

using Amplitude = std::complex<double>;
using StateVector = std::vector<Amplitude>;
using Counts = std::map<std::string, std::size_t>;

class Circuit {
public:
    explicit Circuit(unsigned qubits) : qubit_count_(qubits) {
        if (qubits == 0 || qubits > 16) {
            throw std::invalid_argument(
                "The circuit must contain between 1 and 16 qubits."
            );
        }
        // Statevector storage grows as 2^n; the upper bound limits memory use.
    }

    unsigned qubit_count() const {
        return qubit_count_;
    }

    void h(unsigned target) {
        validate_qubit(target);
        operations_.push_back({Gate::Hadamard, target, target});
    }

    void x(unsigned target) {
        validate_qubit(target);
        operations_.push_back({Gate::PauliX, target, target});
    }

    void cx(unsigned control, unsigned target) {
        validate_qubit(control);
        validate_qubit(target);

        if (control == target) {
            throw std::invalid_argument(
                "A controlled-X gate requires distinct control and target qubits."
            );
        }

        operations_.push_back({Gate::ControlledX, control, target});
    }

    StateVector execute() const {
        const std::size_t dimension = std::size_t{1} << qubit_count_;
        StateVector state(dimension, Amplitude{0.0, 0.0});
        state[0] = Amplitude{1.0, 0.0};

        for (const Operation& operation : operations_) {
            switch (operation.gate) {
                case Gate::Hadamard:
                    apply_hadamard(state, operation.target);
                    break;
                case Gate::PauliX:
                    apply_x(state, operation.target);
                    break;
                case Gate::ControlledX:
                    apply_cx(state, operation.control, operation.target);
                    break;
            }
        }

        validate_state(state);
        return state;
    }

private:
    enum class Gate {
        Hadamard,
        PauliX,
        ControlledX
    };

    struct Operation {
        Gate gate;
        unsigned control;
        unsigned target;
    };

    unsigned qubit_count_;
    std::vector<Operation> operations_;

    void validate_qubit(unsigned qubit) const {
        if (qubit >= qubit_count_) {
            throw std::out_of_range("Qubit index exceeds circuit width.");
        }
    }

    static void apply_hadamard(StateVector& state, unsigned target) {
        const std::size_t mask = std::size_t{1} << target;
        const double factor = 1.0 / std::sqrt(2.0);

        for (std::size_t index = 0; index < state.size(); ++index) {
            if ((index & mask) != 0) {
                continue;
            }

            const std::size_t paired = index | mask;
            const Amplitude zero = state[index];
            const Amplitude one = state[paired];

            state[index] = (zero + one) * factor;
            state[paired] = (zero - one) * factor;
        }
    }

    static void apply_x(StateVector& state, unsigned target) {
        const std::size_t mask = std::size_t{1} << target;

        // Swap each pair only when the target bit changes from zero to one.
        for (std::size_t index = 0; index < state.size(); ++index) {
            if ((index & mask) == 0) {
                std::swap(state[index], state[index | mask]);
            }
        }
    }

    static void apply_cx(
        StateVector& state,
        unsigned control,
        unsigned target
    ) {
        const std::size_t control_mask = std::size_t{1} << control;
        const std::size_t target_mask = std::size_t{1} << target;

        // Controlled-X permutes amplitudes. The operation is its own inverse.
        for (std::size_t index = 0; index < state.size(); ++index) {
            if ((index & control_mask) == 0) {
                continue;
            }

            if ((index & target_mask) == 0) {
                std::swap(state[index], state[index | target_mask]);
            }
        }
    }

    static void validate_state(const StateVector& state) {
        double norm_squared = 0.0;

        for (const Amplitude& amplitude : state) {
            norm_squared += std::norm(amplitude);
        }

        if (std::abs(norm_squared - 1.0) > 1e-9) {
            throw std::runtime_error("Statevector normalization failed.");
        }
    }
};

static std::string bit_string(std::size_t index, unsigned width) {
    std::string result(width, '0');

    for (unsigned bit = 0; bit < width; ++bit) {
        if ((index & (std::size_t{1} << bit)) != 0) {
            result[width - bit - 1] = '1';
        }
    }

    return result;
}

static Counts measure(
    const StateVector& state,
    unsigned qubits,
    std::size_t shots,
    std::uint32_t seed
) {
    if (shots == 0) {
        throw std::invalid_argument("Shot count must be positive.");
    }

    double norm_squared = 0.0;
    std::vector<double> cumulative;
    cumulative.reserve(state.size());

    for (const Amplitude& amplitude : state) {
        norm_squared += std::norm(amplitude);
        cumulative.push_back(norm_squared);
    }

    if (std::abs(norm_squared - 1.0) > 1e-9) {
        throw std::invalid_argument("Cannot measure an unnormalized state.");
    }

    // The final cumulative value can differ slightly from one due to rounding.
    cumulative.back() = 1.0;

    std::mt19937 generator(seed);
    std::uniform_real_distribution<double> distribution(0.0, 1.0);
    Counts counts;

    for (std::size_t shot = 0; shot < shots; ++shot) {
        const double sample = distribution(generator);
        const auto found = std::upper_bound(
            cumulative.begin(), cumulative.end(), sample
        );

        const std::size_t index = found == cumulative.end()
            ? cumulative.size() - 1
            : static_cast<std::size_t>(found - cumulative.begin());

        ++counts[bit_string(index, qubits)];
    }

    return counts;
}

static void print_state(const StateVector& state, unsigned qubits) {
    std::cout << "Statevector amplitudes:\n";
    std::cout << std::fixed << std::setprecision(4);

    for (std::size_t index = 0; index < state.size(); ++index) {
        std::cout << "  |" << bit_string(index, qubits) << "> "
                  << state[index] << '\n';
    }
}

static void print_counts(const Counts& counts, std::size_t shots) {
    std::cout << "Measurement distribution (" << shots << " shots):\n";

    for (const auto& [outcome, count] : counts) {
        const double probability =
            static_cast<double>(count) / static_cast<double>(shots);

        std::cout << "  " << outcome << ": " << count
                  << " (" << std::setprecision(2)
                  << probability * 100.0 << "%)\n";
    }
}

static void verify_bell_distribution(const Counts& counts) {
    for (const auto& [outcome, count] : counts) {
        (void)count;

        if (outcome != "00" && outcome != "11") {
            throw std::runtime_error(
                "Bell-state circuit produced an unexpected outcome."
            );
        }
    }

    if (counts.empty()) {
        throw std::runtime_error("No Bell-state outcomes were recorded.");
    }
}

int main() {
    try {
        std::cout << "Quantum circuit validation engine\n";

        Circuit first_circuit(1);
        first_circuit.h(0);

        const StateVector superposition = first_circuit.execute();

        print_state(superposition, first_circuit.qubit_count());
        const Counts hadamard_counts = measure(
            superposition, 1, 4096, 42
        );
        print_counts(hadamard_counts, 4096);

        const std::size_t ones = hadamard_counts.count("1")
            ? hadamard_counts.at("1")
            : 0;

        const double observed_probability =
            static_cast<double>(ones) / 4096.0;

        if (std::abs(observed_probability - 0.5) > 0.06) {
            throw std::runtime_error(
                "Hadamard distribution exceeds the configured tolerance."
            );
        }

        std::cout << "\nDeterministic X-gate validation\n";
        Circuit deterministic(1);
        deterministic.x(0);
        const StateVector flipped = deterministic.execute();
        const Counts flipped_counts = measure(flipped, 1, 128, 42);
        print_counts(flipped_counts, 128);

        if (flipped_counts.size() != 1 ||
            flipped_counts.at("1") != 128) {
            throw std::runtime_error("X-gate validation failed.");
        }

        std::cout << "\nBell-state correlation test\n";
        Circuit bell(2);
        bell.h(0);
        bell.cx(0, 1);

        const StateVector bell_state = bell.execute();
        print_state(bell_state, 2);

        const Counts bell_counts = measure(bell_state, 2, 4096, 91);
        print_counts(bell_counts, 4096);
        verify_bell_distribution(bell_counts);

        try {
            Circuit invalid(1);
            invalid.cx(0, 0);
        } catch (const std::invalid_argument& error) {
            std::cout << "\nInvalid circuit rejected: "
                      << error.what() << '\n';
        }

        std::cout << "\nAll circuit validation checks passed.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Validation failure: " << error.what() << '\n';
        return 1;
    }
}
