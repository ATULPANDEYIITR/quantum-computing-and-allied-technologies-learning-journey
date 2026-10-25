#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

class GroverEngine {
public:
    struct Result {
        int qubits;
        std::size_t states;
        std::vector<std::size_t> marked;
        int iterations;
        double success_probability;
        std::size_t measured_state;
    };

    explicit GroverEngine(int qubits) : qubits_(qubits) {
        if (qubits < 1 || qubits > 20) {
            throw std::invalid_argument(
                "Qubits must be between 1 and 20."
            );
        }
        states_ = std::size_t{1} << qubits_;
        initialize();
    }

    static int optimal_iterations(
        std::size_t states,
        std::size_t marked_count
    ) {
        if (states == 0 || marked_count > states) {
            throw std::invalid_argument("Invalid search-space dimensions.");
        }
        if (marked_count == 0 || marked_count == states) {
            return 0;
        }

        const double theta = std::asin(
            std::sqrt(static_cast<double>(marked_count) / states)
        );
        return std::max(
            0,
            static_cast<int>(
                std::round(M_PI / (4.0 * theta) - 0.5)
            )
        );
    }

    Result search(std::vector<std::size_t> marked, int iterations = -1) {
        if (marked.empty()) {
            throw std::invalid_argument("At least one target is required.");
        }

        std::sort(marked.begin(), marked.end());
        if (std::adjacent_find(marked.begin(), marked.end()) != marked.end()) {
            throw std::invalid_argument("Duplicate marked states are invalid.");
        }
        if (marked.back() >= states_) {
            throw std::out_of_range("Marked state is outside the search space.");
        }

        if (iterations == -1) {
            iterations = optimal_iterations(states_, marked.size());
        }
        if (iterations < 0 || iterations > 100000) {
            throw std::invalid_argument("Invalid iteration count.");
        }

        initialize();
        for (int i = 0; i < iterations; ++i) {
            apply_oracle(marked);
            apply_diffusion();
        }

        const double probability = success_probability(marked);
        verify_normalization();

        return {
            qubits_,
            states_,
            std::move(marked),
            iterations,
            probability,
            measure()
        };
    }

private:
    int qubits_;
    std::size_t states_;
    std::vector<double> amplitudes_;

    void initialize() {
        amplitudes_.assign(states_, 1.0 / std::sqrt(states_));
    }

    // Oracle phase inversion represents the action of a phase oracle.
    void apply_oracle(const std::vector<std::size_t>& marked) {
        for (const auto state : marked) {
            amplitudes_[state] = -amplitudes_[state];
        }
    }

    // The diffusion operator reflects amplitudes about their mean.
    void apply_diffusion() {
        const double mean =
            std::accumulate(amplitudes_.begin(), amplitudes_.end(), 0.0)
            / static_cast<double>(states_);

        for (double& amplitude : amplitudes_) {
            amplitude = 2.0 * mean - amplitude;
        }
    }

    double success_probability(
        const std::vector<std::size_t>& marked
    ) const {
        double probability = 0.0;
        for (const auto state : marked) {
            probability += amplitudes_[state] * amplitudes_[state];
        }
        return probability;
    }

    void verify_normalization() const {
        const double norm = std::inner_product(
            amplitudes_.begin(), amplitudes_.end(),
            amplitudes_.begin(), 0.0
        );
        if (std::abs(norm - 1.0) > 1e-8) {
            throw std::runtime_error("Quantum state normalization failed.");
        }
    }

    std::size_t measure() const {
        // Deterministic midpoint sampling keeps the case study reproducible.
        const double threshold = 0.5;
        double cumulative = 0.0;
        for (std::size_t i = 0; i < states_; ++i) {
            cumulative += amplitudes_[i] * amplitudes_[i];
            if (cumulative >= threshold) {
                return i;
            }
        }
        return states_ - 1;
    }
};

int main() {
    try {
        const int qubits = 4;
        GroverEngine engine(qubits);
        const auto result = engine.search({11});

        std::cout << "Repository-independent quantum search case study\n";
        std::cout << "Qubits: " << result.qubits << '\n';
        std::cout << "Search-space size: " << result.states << '\n';
        std::cout << "Marked states:";
        for (const auto state : result.marked) {
            std::cout << ' ' << state;
        }
        std::cout << '\n';
        std::cout << "Iterations: " << result.iterations << '\n';
        std::cout << std::fixed << std::setprecision(6);
        std::cout << "Success probability: "
                  << result.success_probability << '\n';
        std::cout << "Measured state: " << result.measured_state << '\n';
        std::cout << "Measurement found target: "
                  << (std::binary_search(
                          result.marked.begin(), result.marked.end(),
                          result.measured_state
                      ) ? "yes" : "no")
                  << '\n';

        if (result.iterations != 3 ||
            result.success_probability < 0.96) {
            throw std::runtime_error("Expected amplification was not reached.");
        }

        bool rejected = false;
        try {
            engine.search({16});
        } catch (const std::out_of_range&) {
            rejected = true;
        }
        if (!rejected) {
            throw std::runtime_error("Invalid target was not rejected.");
        }

        std::cout << "Validation checks passed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
