#include <algorithm>
#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Complex = std::complex<double>;

class Graph {
public:
    explicit Graph(std::vector<std::vector<int>> adjacency)
        : adjacency_(std::move(adjacency)) {
        validate();
    }

    std::size_t size() const {
        return adjacency_.size();
    }

    const std::vector<std::vector<int>>& matrix() const {
        return adjacency_;
    }

    std::vector<int> neighbors(std::size_t vertex) const {
        validate_vertex(vertex);

        std::vector<int> result;
        for (std::size_t i = 0; i < size(); ++i) {
            if (adjacency_[vertex][i] == 1) {
                result.push_back(static_cast<int>(i));
            }
        }
        return result;
    }

    void validate_vertex(std::size_t vertex) const {
        if (vertex >= size()) {
            throw std::out_of_range("Vertex index is outside the graph.");
        }
    }

private:
    std::vector<std::vector<int>> adjacency_;

    void validate() const {
        if (adjacency_.empty()) {
            throw std::invalid_argument("Graph cannot be empty.");
        }

        const std::size_t n = adjacency_.size();

        for (const auto& row : adjacency_) {
            if (row.size() != n) {
                throw std::invalid_argument("Adjacency matrix must be square.");
            }
            for (int value : row) {
                if (value != 0 && value != 1) {
                    throw std::invalid_argument("Graph entries must be 0 or 1.");
                }
            }
        }

        for (std::size_t i = 0; i < n; ++i) {
            if (adjacency_[i][i] != 0) {
                throw std::invalid_argument("Self-loops are not supported.");
            }

            for (std::size_t j = 0; j < n; ++j) {
                if (adjacency_[i][j] != adjacency_[j][i]) {
                    throw std::invalid_argument("Graph must be undirected.");
                }
            }
        }
    }
};

class QuantumWalkEngine {
public:
    explicit QuantumWalkEngine(const Graph& graph) : graph_(graph) {}

    std::vector<double> continuous_time_walk(
        std::size_t start,
        double time
    ) const {
        graph_.validate_vertex(start);

        if (!std::isfinite(time) || time < 0.0) {
            throw std::invalid_argument("Time must be finite and non-negative.");
        }

        const std::size_t n = graph_.size();

        std::vector<Complex> result(n, Complex{0.0, 0.0});
        std::vector<Complex> term(n, Complex{0.0, 0.0});

        result[start] = Complex{1.0, 0.0};
        term[start] = Complex{1.0, 0.0};

        // U(t) = exp(-iAt). The Taylor expansion is appropriate here because
        // the case study deliberately uses small educational graphs.
        for (int k = 1; k <= 100; ++k) {
            std::vector<Complex> product(n, Complex{0.0, 0.0});

            for (std::size_t i = 0; i < n; ++i) {
                for (std::size_t j = 0; j < n; ++j) {
                    if (graph_.matrix()[i][j] == 1) {
                        product[i] += term[j];
                    }
                }
            }

            const Complex factor(0.0, -time / static_cast<double>(k));

            double maximum_term = 0.0;
            for (std::size_t i = 0; i < n; ++i) {
                term[i] = factor * product[i];
                result[i] += term[i];
                maximum_term = std::max(maximum_term, std::abs(term[i]));
            }

            if (maximum_term < 1e-14) {
                break;
            }
        }

        double norm_squared = 0.0;
        for (const auto& amplitude : result) {
            norm_squared += std::norm(amplitude);
        }

        if (norm_squared <= 1e-20) {
            throw std::runtime_error("Quantum state collapsed to zero numerically.");
        }

        const double inverse_norm = 1.0 / std::sqrt(norm_squared);
        std::vector<double> probabilities(n);

        for (std::size_t i = 0; i < n; ++i) {
            result[i] *= inverse_norm;
            probabilities[i] = std::norm(result[i]);
        }

        return probabilities;
    }

    std::vector<double> classical_walk(
        std::size_t start,
        int steps
    ) const {
        graph_.validate_vertex(start);

        if (steps < 0) {
            throw std::invalid_argument("Steps cannot be negative.");
        }

        const std::size_t n = graph_.size();
        std::vector<double> distribution(n, 0.0);
        distribution[start] = 1.0;

        for (int step = 0; step < steps; ++step) {
            std::vector<double> next(n, 0.0);

            for (std::size_t vertex = 0; vertex < n; ++vertex) {
                const auto adjacent = graph_.neighbors(vertex);

                if (adjacent.empty()) {
                    next[vertex] += distribution[vertex];
                    continue;
                }

                const double share =
                    distribution[vertex] / static_cast<double>(adjacent.size());

                for (int neighbor : adjacent) {
                    next[neighbor] += share;
                }
            }

            distribution.swap(next);
        }

        return distribution;
    }

private:
    const Graph& graph_;
};

class MergeSearchApplication {
public:
    explicit MergeSearchApplication(const Graph& graph)
        : engine_(graph) {}

    void evaluate_routes(std::size_t start, double time) const {
        const auto quantum = engine_.continuous_time_walk(start, time);

        std::cout << "Quantum-walk route probabilities at t="
                  << time << "\n";

        for (std::size_t vertex = 0; vertex < quantum.size(); ++vertex) {
            std::cout << "  node " << vertex
                      << ": " << std::fixed << std::setprecision(8)
                      << quantum[vertex] << "\n";
        }

        const double total =
            std::accumulate(quantum.begin(), quantum.end(), 0.0);

        if (std::abs(total - 1.0) > 1e-9) {
            throw std::runtime_error("Probability conservation failed.");
        }
    }

private:
    QuantumWalkEngine engine_;
};

int main() {
    try {
        Graph cycle({
            {0, 1, 0, 1},
            {1, 0, 1, 0},
            {0, 1, 0, 1},
            {1, 0, 1, 0}
        });

        QuantumWalkEngine engine(cycle);

        const auto classical = engine.classical_walk(0, 6);
        const auto quantum = engine.continuous_time_walk(0, 1.5);

        std::cout << "Classical random walk after six steps:\n";
        for (std::size_t i = 0; i < classical.size(); ++i) {
            std::cout << "  node " << i << ": "
                      << std::fixed << std::setprecision(8)
                      << classical[i] << "\n";
        }

        std::cout << "\nContinuous-time quantum walk:\n";
        for (std::size_t i = 0; i < quantum.size(); ++i) {
            std::cout << "  node " << i << ": "
                      << std::fixed << std::setprecision(8)
                      << quantum[i] << "\n";
        }

        const double quantum_total =
            std::accumulate(quantum.begin(), quantum.end(), 0.0);

        if (std::abs(quantum_total - 1.0) > 1e-9) {
            throw std::runtime_error("Quantum probability normalization failed.");
        }

        MergeSearchApplication application(cycle);
        std::cout << "\nApplication-oriented evaluation:\n";
        application.evaluate_routes(0, 1.5);

        // A disconnected component is an explicit reachability edge case.
        Graph disconnected({
            {0, 1, 0},
            {1, 0, 0},
            {0, 0, 0}
        });

        QuantumWalkEngine disconnected_engine(disconnected);
        const auto unreachable =
            disconnected_engine.continuous_time_walk(0, 2.0);

        if (unreachable[2] > 1e-12) {
            throw std::runtime_error(
                "Disconnected-node reachability invariant failed."
            );
        }

        std::cout << "\nDisconnected-node invariant passed.\n";
        std::cout << "The engine preserves normalization and graph reachability.\n";

    } catch (const std::exception& error) {
        std::cerr << "Execution failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
