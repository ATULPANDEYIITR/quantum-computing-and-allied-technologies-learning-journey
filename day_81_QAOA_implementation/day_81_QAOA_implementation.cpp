#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;

constexpr double PI = 3.14159265358979323846;
using Complex = complex<double>;

enum class ExperimentStatus {
    Created,
    Running,
    Completed,
    Failed
};

struct Edge {
    int u;
    int v;
    double weight;
};

struct Parameters {
    double gamma = 0.0;
    double beta = 0.0;
};

struct Evaluation {
    Parameters parameters;
    double expectedCut = 0.0;
    vector<Complex> state;
};

struct OptimizationResult {
    Parameters parameters;
    double expectedCut;
    double observedCut;
    double classicalOptimum;
    double approximationRatio;
    uint64_t evaluations;
    string bestBitstring;
};

class Graph {
private:
    int vertices;
    vector<Edge> edges;

public:
    Graph(int count, vector<Edge> input)
        : vertices(count), edges(move(input)) {

        if (vertices < 2 || vertices > 20) {
            throw invalid_argument("Invalid vertex count.");
        }

        if (edges.empty()) {
            throw invalid_argument("Graph must contain edges.");
        }

        for (const auto& edge : edges) {
            if (edge.u < 0 || edge.v < 0 ||
                edge.u >= vertices || edge.v >= vertices ||
                edge.u == edge.v) {
                throw invalid_argument("Invalid edge endpoints.");
            }

            if (!isfinite(edge.weight) || edge.weight <= 0.0) {
                throw invalid_argument("Invalid edge weight.");
            }
        }
    }

    int size() const {
        return vertices;
    }

    const vector<Edge>& getEdges() const {
        return edges;
    }

    double cutValue(uint64_t mask) const {
        double result = 0.0;

        for (const auto& edge : edges) {
            bool a = (mask >> edge.u) & 1ULL;
            bool b = (mask >> edge.v) & 1ULL;

            if (a != b) {
                result += edge.weight;
            }
        }

        return result;
    }

    pair<double, uint64_t> classicalOptimum() const {
        double best = -numeric_limits<double>::infinity();
        uint64_t bestMask = 0;

        const uint64_t limit = 1ULL << vertices;

        // Complementary partitions have identical objective values.
        for (uint64_t mask = 0; mask < limit / 2; ++mask) {
            double value = cutValue(mask);

            if (value > best) {
                best = value;
                bestMask = mask;
            }
        }

        return {best, bestMask};
    }

    string bitstring(uint64_t mask) const {
        string result;

        for (int i = 0; i < vertices; ++i) {
            result += ((mask >> i) & 1ULL) ? '1' : '0';
        }

        return result;
    }
};

class StateVectorSimulator {
private:
    const Graph& graph;
    int n;
    size_t dimension;

    vector<Complex> initialState() const {
        double amplitude = 1.0 / sqrt(static_cast<double>(dimension));

        return vector<Complex>(dimension, Complex(amplitude, 0.0));
    }

    void applyCost(
        vector<Complex>& state,
        double gamma
    ) const {
        for (size_t index = 0; index < dimension; ++index) {
            double cost = graph.cutValue(index);

            state[index] *=
                exp(Complex(0.0, -gamma * cost));
        }
    }

    void applyMixer(
        vector<Complex>& state,
        double beta
    ) const {
        const double c = cos(beta);
        const Complex s(0.0, -sin(beta));

        // Each qubit mixer is applied to pairs of basis amplitudes.
        for (int qubit = 0; qubit < n; ++qubit) {
            size_t mask = 1ULL << qubit;

            for (size_t i = 0; i < dimension; ++i) {
                if (i & mask) {
                    continue;
                }

                size_t j = i | mask;

                Complex a = state[i];
                Complex b = state[j];

                state[i] = c * a + s * b;
                state[j] = s * a + c * b;
            }
        }
    }

public:
    explicit StateVectorSimulator(const Graph& input)
        : graph(input),
          n(input.size()),
          dimension(1ULL << n) {}

    vector<Complex> execute(
        double gamma,
        double beta
    ) const {
        if (!isfinite(gamma) || !isfinite(beta)) {
            throw invalid_argument("Non-finite QAOA parameters.");
        }

        auto state = initialState();

        applyCost(state, gamma);
        applyMixer(state, beta);

        return state;
    }

    double expectedCut(const vector<Complex>& state) const {
        if (state.size() != dimension) {
            throw invalid_argument("Invalid statevector dimension.");
        }

        double expectation = 0.0;
        double norm = 0.0;

        for (size_t i = 0; i < dimension; ++i) {
            double probability = norm(state[i]);
            norm += probability;
            expectation += probability * graph.cutValue(i);
        }

        if (abs(norm - 1.0) > 1e-9) {
            throw runtime_error("Quantum state normalization failed.");
        }

        return expectation;
    }

    pair<uint64_t, double> mostProbable(
        const vector<Complex>& state
    ) const {
        uint64_t bestMask = 0;
        double bestProbability = -1.0;

        for (uint64_t i = 0; i < dimension; ++i) {
            double probability = norm(state[i]);

            if (probability > bestProbability) {
                bestProbability = probability;
                bestMask = i;
            }
        }

        return {bestMask, bestProbability};
    }
};

class QAOAOptimizer {
private:
    const StateVectorSimulator& simulator;
    const Graph& graph;
    int gammaSteps;
    int betaSteps;
    ExperimentStatus status = ExperimentStatus::Created;

public:
    QAOAOptimizer(
        const StateVectorSimulator& sim,
        const Graph& input,
        int gammaResolution,
        int betaResolution
    )
        : simulator(sim),
          graph(input),
          gammaSteps(gammaResolution),
          betaSteps(betaResolution) {

        if (gammaSteps < 2 || betaSteps < 2) {
            throw invalid_argument("Invalid optimization resolution.");
        }
    }

    OptimizationResult optimize() {
        if (status != ExperimentStatus::Created) {
            throw logic_error("Experiment cannot be restarted.");
        }

        status = ExperimentStatus::Running;

        try {
            Evaluation best;
            best.expectedCut = -numeric_limits<double>::infinity();

            uint64_t evaluations = 0;

            for (int i = 0; i < gammaSteps; ++i) {
                double gamma = 2.0 * PI * i / gammaSteps;

                for (int j = 0; j < betaSteps; ++j) {
                    double beta = PI * j / betaSteps;

                    auto state = simulator.execute(gamma, beta);
                    double expected = simulator.expectedCut(state);

                    ++evaluations;

                    if (expected > best.expectedCut) {
                        best.parameters = {gamma, beta};
                        best.expectedCut = expected;
                        best.state = move(state);
                    }
                }
            }

            auto observed = simulator.mostProbable(best.state);
            auto classical = graph.classicalOptimum();

            double ratio = classical.first > 0.0
                ? best.expectedCut / classical.first
                : 0.0;

            status = ExperimentStatus::Completed;

            return {
                best.parameters,
                best.expectedCut,
                graph.cutValue(observed.first),
                classical.first,
                ratio,
                evaluations,
                graph.bitstring(observed.first)
            };

        } catch (...) {
            status = ExperimentStatus::Failed;
            throw;
        }
    }

    ExperimentStatus getStatus() const {
        return status;
    }
};

int main() {
    try {
        Graph graph(6, {
            {0, 1, 1.0},
            {0, 2, 1.0},
            {1, 2, 1.0},
            {1, 3, 1.0},
            {2, 4, 1.0},
            {3, 4, 1.0},
            {3, 5, 1.0},
            {4, 5, 1.0},
            {0, 5, 1.0}
        });

        StateVectorSimulator simulator(graph);

        QAOAOptimizer optimizer(
            simulator,
            graph,
            40,
            40
        );

        OptimizationResult result = optimizer.optimize();

        cout << fixed << setprecision(6);
        cout << "QAOA MAX-CUT GOVERNANCE ENGINE\n";
        cout << "==============================\n";
        cout << "Vertices: " << graph.size() << '\n';
        cout << "Edges: " << graph.getEdges().size() << '\n';
        cout << "Circuit depth p: 1\n";
        cout << "Gamma: " << result.parameters.gamma << '\n';
        cout << "Beta: " << result.parameters.beta << '\n';
        cout << "Expected cut: " << result.expectedCut << '\n';
        cout << "Observed bitstring: " << result.bestBitstring << '\n';
        cout << "Observed cut: " << result.observedCut << '\n';
        cout << "Classical optimum: " << result.classicalOptimum << '\n';
        cout << "Approximation ratio: "
             << result.approximationRatio << '\n';
        cout << "Evaluations: " << result.evaluations << '\n';

        cout << "Status: "
             << (optimizer.getStatus() == ExperimentStatus::Completed
                     ? "COMPLETED"
                     : "FAILED")
             << '\n';

    } catch (const exception& error) {
        cerr << "Optimization failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
