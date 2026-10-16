#include <algorithm>
#include <cmath>
#include <complex>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using Complex = std::complex<double>;
using State = std::vector<Complex>;

constexpr double EPSILON = 1e-9;

class QuantumError : public std::runtime_error {
public:
    explicit QuantumError(const std::string& message)
        : std::runtime_error(message) {}
};

struct SearchReport {
    std::size_t qubits;
    std::size_t dimension;
    std::size_t marked_count;
    std::size_t iterations;
    std::size_t most_probable_state;
    double marked_probability;
};

class QuantumSearchEngine {
private:
    std::size_t qubits_;
    std::size_t dimension_;

    static std::size_t checkedDimension(std::size_t qubits) {
        // Bound the simulator before shifting or allocating an exponential
        // state vector. This implementation deliberately limits memory use.
        if (qubits == 0 || qubits > 20) {
            throw QuantumError("Supported qubit count is between 1 and 20.");
        }
        return std::size_t{1} << qubits;
    }

    static double probability(const Complex& amplitude) {
        return std::norm(amplitude);
    }

    static void validate(const State& state) {
        if (state.empty()) {
            throw QuantumError("State vector cannot be empty.");
        }

        double norm = 0.0;
        for (const auto& amplitude : state) {
            norm += probability(amplitude);
        }

        if (std::abs(norm - 1.0) > EPSILON) {
            throw QuantumError("State vector is not normalized.");
        }
    }

    State uniformState() const {
        const double amplitude = 1.0 / std::sqrt(
            static_cast<double>(dimension_)
        );
        return State(dimension_, Complex(amplitude, 0.0));
    }

    static void applyOracle(State& state, const std::set<std::size_t>& marked) {
        // A Boolean oracle is represented by a sign change on marked states.
        for (std::size_t index : marked) {
            state[index] = -state[index];
        }
    }

    static void applyDiffusion(State& state) {
        // Reflection about the mean amplifies amplitudes with the correct
        // relative phase after the oracle has marked target states.
        Complex mean{0.0, 0.0};
        for (const auto& amplitude : state) {
            mean += amplitude;
        }
        mean /= static_cast<double>(state.size());

        for (auto& amplitude : state) {
            amplitude = 2.0 * mean - amplitude;
        }
    }

public:
    explicit QuantumSearchEngine(std::size_t qubits)
        : qubits_(qubits), dimension_(checkedDimension(qubits)) {}

    SearchReport run(const std::set<std::size_t>& marked) const {
        if (marked.empty()) {
            throw QuantumError("At least one marked state is required.");
        }

        if (marked.size() >= dimension_) {
            throw QuantumError(
                "Marked states must be fewer than all search states."
            );
        }

        for (std::size_t index : marked) {
            if (index >= dimension_) {
                throw QuantumError("Marked state exceeds search-space bounds.");
            }
        }

        State state = uniformState();
        const double ratio = static_cast<double>(dimension_) /
                             static_cast<double>(marked.size());
        const std::size_t iterations = std::max<std::size_t>(
            1,
            static_cast<std::size_t>(
                std::llround((std::acos(-1.0) / 4.0) * std::sqrt(ratio))
            )
        );

        for (std::size_t iteration = 0; iteration < iterations; ++iteration) {
            applyOracle(state, marked);
            applyDiffusion(state);
        }

        validate(state);

        std::size_t best_index = 0;
        double best_probability = -1.0;
        double total_marked_probability = 0.0;

        for (std::size_t index = 0; index < dimension_; ++index) {
            const double current = probability(state[index]);
            if (current > best_probability) {
                best_probability = current;
                best_index = index;
            }
            if (marked.count(index) != 0) {
                total_marked_probability += current;
            }
        }

        return SearchReport{
            qubits_,
            dimension_,
            marked.size(),
            iterations,
            best_index,
            total_marked_probability
        };
    }

    static std::string bitString(std::size_t value, std::size_t width) {
        std::string result(width, '0');
        for (std::size_t bit = 0; bit < width; ++bit) {
            if ((value & (std::size_t{1} << bit)) != 0) {
                result[width - bit - 1] = '1';
            }
        }
        return result;
    }
};

class RepositoryFaultDiagnosis {
public:
    // The same algorithmic discipline applies to diagnosis: define a bounded
    // candidate space, encode an exact predicate, and distinguish search cost
    // from the cost of verifying a candidate.
    static bool isFaultyBuild(const std::string& build) {
        return build == "build-013" || build == "build-027";
    }

    static void run() {
        std::vector<std::string> builds;
        for (int number = 0; number < 32; ++number) {
            std::string id = "build-";
            if (number < 10) id += "00";
            else id += "0";
            id += std::to_string(number);
            builds.push_back(id);
        }

        std::vector<std::string> faulty;
        for (const auto& build : builds) {
            if (isFaultyBuild(build)) {
                faulty.push_back(build);
            }
        }

        std::cout << "\nClassical fault verification\n";
        std::cout << "Candidate builds: " << builds.size() << '\n';
        std::cout << "Exact predicate matches: " << faulty.size() << '\n';
        std::cout << "Verified faulty builds:";
        for (const auto& build : faulty) {
            std::cout << ' ' << build;
        }
        std::cout << "\nClassical worst-case predicate evaluations: "
                  << builds.size() << '\n';
        std::cout << "Quantum caveat: a classical list predicate cannot "
                     "automatically become a useful quantum oracle.\n";
    }
};

int main() {
    try {
        std::cout << "Quantum Search Governance Case Study\n";
        std::cout << "====================================\n";

        // Simulate a 256-candidate diagnostic space with one target.
        QuantumSearchEngine engine(8);
        const std::set<std::size_t> marked{173};
        const SearchReport report = engine.run(marked);

        std::cout << "Qubits: " << report.qubits << '\n';
        std::cout << "Search-space dimension: " << report.dimension << '\n';
        std::cout << "Marked candidates: " << report.marked_count << '\n';
        std::cout << "Grover iterations: " << report.iterations << '\n';
        std::cout << "Most probable state: "
                  << QuantumSearchEngine::bitString(
                         report.most_probable_state, report.qubits
                     )
                  << '\n';
        std::cout << std::fixed << std::setprecision(4);
        std::cout << "Probability of any marked state: "
                  << report.marked_probability << '\n';

        RepositoryFaultDiagnosis::run();

        std::cout << "\nComplexity and operational constraints\n";
        std::cout << "Grover query complexity: O(sqrt(N/M)) for M marked "
                     "states in N candidates.\n";
        std::cout << "Classical unstructured search: O(N/M) expected "
                     "queries under a random-order model.\n";
        std::cout << "State-vector memory: O(2^n); simulation time and "
                     "memory grow exponentially with qubit count.\n";
        std::cout << "A physical implementation must account for oracle "
                     "construction, gate errors, measurement shots, and "
                     "verification cost.\n";

        try {
            QuantumSearchEngine invalid_engine(0);
            (void)invalid_engine;
        } catch (const QuantumError& error) {
            std::cout << "Rejected invalid circuit: " << error.what() << '\n';
        }

        try {
            engine.run({});
        } catch (const QuantumError& error) {
            std::cout << "Rejected invalid oracle: " << error.what() << '\n';
        }

    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
