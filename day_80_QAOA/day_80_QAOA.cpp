#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

using namespace std;

using Complex = complex<double>;

constexpr double PI = 3.14159265358979323846;
constexpr double EPS = 1e-10;
constexpr int MAX_QUBITS = 20;

enum class ExperimentStatus {
    CREATED,
    INITIALIZED,
    OPTIMIZING,
    COMPLETED,
    FAILED
};

struct Edge {
    int u;
    int v;
    double weight;
};

struct Graph {
    int vertices;
    vector<Edge> edges;

    Graph(int n, vector<Edge> e)
        : vertices(n), edges(move(e)) {

        if (vertices < 1 || vertices > MAX_QUBITS) {
            throw invalid_argument("Invalid graph size.");
        }

        unordered_set<string> seen;

        for (const auto& edge : edges) {
            if (
                edge.u < 0 || edge.v < 0 ||
                edge.u >= vertices || edge.v >= vertices ||
                edge.u == edge.v
            ) {
                throw invalid_argument("Invalid edge.");
            }

            if (!isfinite(edge.weight) || edge.weight <= 0) {
                throw invalid_argument("Invalid edge weight.");
            }

            int a = min(edge.u, edge.v);
            int b = max(edge.u, edge.v);

            string key = to_string(a) + ":" + to_string(b);

            if (!seen.insert(key).second) {
                throw invalid_argument("Duplicate edge.");
            }
        }
    }

    double cutValue(uint64_t state) const {
        double result = 0;

        for (const auto& edge : edges) {
            bool a = (state >> edge.u) & 1ULL;
            bool b = (state >> edge.v) & 1ULL;

            if (a != b) {
                result += edge.weight;
            }
        }

        return result;
    }

    pair<double, vector<uint64_t>> optimum() const {
        double best = -numeric_limits<double>::infinity();
        vector<uint64_t> solutions;

        uint64_t total = 1ULL << vertices;

        for (uint64_t state = 0; state < total; ++state) {
            double value = cutValue(state);

            if (value > best + EPS) {
                best = value;
                solutions.clear();
                solutions.push_back(state);
            } else if (abs(value - best) <= EPS) {
                solutions.push_back(state);
            }
        }

        return {best, solutions};
    }

    string bitstring(uint64_t state) const {
        string result(vertices, '0');

        for (int i = 0; i < vertices; ++i) {
            if ((state >> i) & 1ULL) {
                result[vertices - 1 - i] = '1';
            }
        }

        return result;
    }
};

struct Parameters {
    vector<double> gamma;
    vector<double> beta;
};

struct OptimizationResult {
    Parameters parameters;
    double expectation = 0;
    int iterations = 0;
    vector<double> history;
};

class StateVector {
private:
    int qubits;
    uint64_t dimension;
    vector<Complex> amplitudes;

public:
    explicit StateVector(int n)
        : qubits(n),
          dimension(1ULL << n),
          amplitudes(dimension, Complex(0, 0)) {

        if (n < 1 || n > MAX_QUBITS) {
            throw invalid_argument("Unsupported qubit count.");
        }

        double amplitude = 1.0 / sqrt(
            static_cast<double>(dimension)
        );

        fill(
            amplitudes.begin(),
            amplitudes.end(),
            Complex(amplitude, 0)
        );
    }

    void applyCost(const Graph& graph, double gamma) {
        /*
         * U_C(gamma) = exp(-i * gamma * H_C).
         *
         * H_C is diagonal in the computational basis.
         * Each basis amplitude receives a phase determined
         * by the weighted cut value.
         */
        for (uint64_t state = 0; state < dimension; ++state) {
            double phase = -gamma * graph.cutValue(state);

            amplitudes[state] *= Complex(
                cos(phase),
                sin(phase)
            );
        }
    }

    void applyMixer(double beta) {
        /*
         * U_B(beta) = product_i exp(-i * beta * X_i).
         *
         * Each pair of amplitudes differing in one bit is
         * transformed by an RX(2*beta) operation.
         */
        const double c = cos(beta);
        const double s = sin(beta);

        for (int qubit = 0; qubit < qubits; ++qubit) {
            uint64_t mask = 1ULL << qubit;

            for (uint64_t state = 0; state < dimension; ++state) {
                if (state & mask) {
                    continue;
                }

                uint64_t partner = state | mask;

                Complex a = amplitudes[state];
                Complex b = amplitudes[partner];

                amplitudes[state] =
                    c * a - Complex(0, s) * b;

                amplitudes[partner] =
                    -Complex(0, s) * a + c * b;
            }
        }
    }

    double expectation(const Graph& graph) const {
        double result = 0;

        for (uint64_t state = 0; state < dimension; ++state) {
            result += norm(amplitudes[state])
                    * graph.cutValue(state);
        }

        return result;
    }

    vector<double> probabilities() const {
        vector<double> result(dimension);

        transform(
            amplitudes.begin(),
            amplitudes.end(),
            result.begin(),
            [](const Complex& amplitude) {
                return norm(amplitude);
            }
        );

        return result;
    }

    void validate() const {
        double total = 0;

        for (const auto& amplitude : amplitudes) {
            total += norm(amplitude);
        }

        if (abs(total - 1.0) > 1e-8) {
            throw runtime_error("State normalization failure.");
        }
    }
};

class QAOACircuit {
private:
    const Graph& graph;
    int depth;

public:
    QAOACircuit(const Graph& g, int p)
        : graph(g), depth(p) {

        if (depth < 1 || depth > 10) {
            throw invalid_argument("Invalid QAOA depth.");
        }
    }

    void validate(const Parameters& parameters) const {
        if (
            static_cast<int>(parameters.gamma.size()) != depth ||
            static_cast<int>(parameters.beta.size()) != depth
        ) {
            throw invalid_argument("Incorrect parameter dimensions.");
        }

        for (double value : parameters.gamma) {
            if (!isfinite(value)) {
                throw invalid_argument("Invalid gamma parameter.");
            }
        }

        for (double value : parameters.beta) {
            if (!isfinite(value)) {
                throw invalid_argument("Invalid beta parameter.");
            }
        }
    }

    StateVector simulate(const Parameters& parameters) const {
        validate(parameters);

        StateVector state(graph.vertices);

        for (int layer = 0; layer < depth; ++layer) {
            state.applyCost(
                graph,
                parameters.gamma[layer]
            );

            state.applyMixer(
                parameters.beta[layer]
            );
        }

        state.validate();
        return state;
    }

    double expectation(const Parameters& parameters) const {
        StateVector state = simulate(parameters);
        return state.expectation(graph);
    }

    OptimizationResult optimize(
        int maxIterations,
        double stepSize,
        unsigned int seed
    ) const {

        if (maxIterations < 1 || stepSize <= 0) {
            throw invalid_argument("Invalid optimizer settings.");
        }

        mt19937 generator(seed);

        uniform_real_distribution<double> gammaDistribution(
            0, PI
        );

        uniform_real_distribution<double> betaDistribution(
            0, PI / 2
        );

        Parameters parameters;

        for (int i = 0; i < depth; ++i) {
            parameters.gamma.push_back(gammaDistribution(generator));
            parameters.beta.push_back(betaDistribution(generator));
        }

        double best = expectation(parameters);

        OptimizationResult result;
        result.history.push_back(best);

        for (int iteration = 0; iteration < maxIterations; ++iteration) {
            bool improved = false;

            for (int group = 0; group < 2; ++group) {
                auto& values = group == 0
                    ? parameters.gamma
                    : parameters.beta;

                double upper = group == 0 ? PI : PI / 2;

                for (int index = 0; index < depth; ++index) {
                    double original = values[index];
                    double candidateBest = original;
                    double localBest = best;

                    for (int direction : {-1, 1}) {
                        values[index] = clamp(
                            original + direction * stepSize,
                            0.0,
                            upper
                        );

                        double value = expectation(parameters);

                        if (value > localBest + EPS) {
                            localBest = value;
                            candidateBest = values[index];
                        }
                    }

                    values[index] = candidateBest;

                    if (localBest > best + EPS) {
                        best = localBest;
                        improved = true;
                    }
                }
            }

            result.history.push_back(best);

            if (!improved) {
                stepSize *= 0.5;
            }

            if (stepSize < 1e-5) {
                break;
            }
        }

        result.parameters = parameters;
        result.expectation = best;
        result.iterations =
            static_cast<int>(result.history.size()) - 1;

        return result;
    }
};

struct Experiment {
    string id;
    ExperimentStatus status = ExperimentStatus::CREATED;
    OptimizationResult result;
    string failureReason;
};

class ExperimentManager {
private:
    const QAOACircuit& circuit;
    vector<Experiment> experiments;

public:
    explicit ExperimentManager(const QAOACircuit& qaoa)
        : circuit(qaoa) {}

    Experiment run(
        const string& id,
        int iterations,
        double step,
        unsigned int seed
    ) {

        Experiment experiment;
        experiment.id = id;

        try {
            experiment.status = ExperimentStatus::INITIALIZED;

            experiment.status = ExperimentStatus::OPTIMIZING;

            experiment.result = circuit.optimize(
                iterations,
                step,
                seed
            );

            experiment.status = ExperimentStatus::COMPLETED;

        } catch (const exception& error) {
            experiment.status = ExperimentStatus::FAILED;
            experiment.failureReason = error.what();
        }

        experiments.push_back(experiment);
        return experiment;
    }

    const vector<Experiment>& getExperiments() const {
        return experiments;
    }
};

void printResult(
    const Graph& graph,
    const OptimizationResult& result
) {
    cout << fixed << setprecision(6);

    cout << "\nOptimized parameters\n";

    for (size_t i = 0; i < result.parameters.gamma.size(); ++i) {
        cout << "Layer " << i + 1
             << ": gamma=" << result.parameters.gamma[i]
             << ", beta=" << result.parameters.beta[i]
             << '\n';
    }

    cout << "\nExpected cut: "
         << result.expectation << '\n';

    cout << "Optimization iterations: "
         << result.iterations << '\n';

    StateVector state(
        graph.vertices
    );

    for (size_t i = 0; i < result.parameters.gamma.size(); ++i) {
        state.applyCost(
            graph,
            result.parameters.gamma[i]
        );

        state.applyMixer(
            result.parameters.beta[i]
        );
    }

    auto probabilities = state.probabilities();

    vector<uint64_t> indices(probabilities.size());

    iota(indices.begin(), indices.end(), 0);

    sort(
        indices.begin(),
        indices.end(),
        [&](uint64_t a, uint64_t b) {
            return probabilities[a] > probabilities[b];
        }
    );

    cout << "\nMost probable measurement outcomes\n";

    for (int i = 0; i < min(8, static_cast<int>(indices.size())); ++i) {
        uint64_t index = indices[i];

        cout << graph.bitstring(index)
             << " probability=" << probabilities[index]
             << " cut=" << graph.cutValue(index)
             << '\n';
    }
}

int main() {
    try {
        Graph graph(
            4,
            {
                {0, 1, 1.0},
                {0, 2, 1.0},
                {1, 2, 1.0},
                {1, 3, 1.0},
                {2, 3, 1.0}
            }
        );

        auto [optimalValue, optimalSolutions] =
            graph.optimum();

        cout << "QAOA MAX-CUT GOVERNANCE ENGINE\n";
        cout << "Vertices: " << graph.vertices << '\n';
        cout << "Edges: " << graph.edges.size() << '\n';
        cout << "Classical optimum: " << optimalValue << '\n';

        cout << "Optimal bitstrings: ";

        for (auto solution : optimalSolutions) {
            cout << graph.bitstring(solution) << ' ';
        }

        cout << '\n';

        QAOACircuit circuit(graph, 1);

        ExperimentManager manager(circuit);

        Experiment experiment = manager.run(
            "MAXCUT-EXP-001",
            100,
            0.15,
            42
        );

        if (experiment.status == ExperimentStatus::FAILED) {
            throw runtime_error(experiment.failureReason);
        }

        printResult(graph, experiment.result);

        double ratio = optimalValue > EPS
            ? experiment.result.expectation / optimalValue
            : 1.0;

        cout << "\nApproximation ratio: " << ratio << '\n';

        cout << "Experiment status: COMPLETED\n";

        if (experiment.result.expectation > optimalValue + EPS) {
            throw runtime_error("Expectation exceeds classical optimum.");
        }

        cout << "Validation: PASSED\n";

    } catch (const exception& error) {
        cerr << "QAOA execution failed: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
