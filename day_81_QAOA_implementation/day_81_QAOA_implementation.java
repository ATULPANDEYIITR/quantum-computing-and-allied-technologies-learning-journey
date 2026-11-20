import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Enterprise-oriented QAOA MaxCut implementation.
 *
 * Java 17
 * Exact statevector simulation
 * Single-layer QAOA (p = 1)
 * Exhaustive parameter-grid optimization
 */
public class QAOAMaxCut {

    private static final double PI = Math.PI;
    private static final double NORMALIZATION_TOLERANCE = 1e-9;

    enum ExperimentStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum ReviewStatus {
        VALID,
        INVALID
    }

    record Edge(int source, int target, double weight) {

        Edge {
            if (source < 0 || target < 0 || source == target) {
                throw new IllegalArgumentException(
                    "Invalid edge endpoints."
                );
            }

            if (!Double.isFinite(weight) || weight <= 0) {
                throw new IllegalArgumentException(
                    "Edge weight must be positive and finite."
                );
            }
        }
    }

    record QAOAParameters(double gamma, double beta) {

        QAOAParameters {
            if (!Double.isFinite(gamma) ||
                !Double.isFinite(beta)) {
                throw new IllegalArgumentException(
                    "Parameters must be finite."
                );
            }
        }
    }

    record OptimizationResult(
        QAOAParameters parameters,
        double expectedCut,
        String observedPartition,
        double observedCut,
        double classicalOptimum,
        double approximationRatio,
        long evaluations
    ) {}

    static final class OptimizationException
        extends RuntimeException {

        OptimizationException(String message) {
            super(message);
        }
    }

    static final class WeightedGraph {

        private final int vertexCount;
        private final List<Edge> edges;

        WeightedGraph(int vertexCount, List<Edge> edges) {
            if (vertexCount < 2 || vertexCount > 20) {
                throw new IllegalArgumentException(
                    "Vertex count must be between 2 and 20."
                );
            }

            Objects.requireNonNull(edges);

            if (edges.isEmpty()) {
                throw new IllegalArgumentException(
                    "Graph must contain at least one edge."
                );
            }

            this.vertexCount = vertexCount;
            this.edges = List.copyOf(edges);

            for (Edge edge : this.edges) {
                if (edge.source() >= vertexCount ||
                    edge.target() >= vertexCount) {
                    throw new IllegalArgumentException(
                        "Edge endpoint exceeds graph size."
                    );
                }
            }
        }

        int vertexCount() {
            return vertexCount;
        }

        List<Edge> edges() {
            return edges;
        }

        double cutValue(long mask) {
            double result = 0.0;

            for (Edge edge : edges) {
                long a = (mask >>> edge.source()) & 1L;
                long b = (mask >>> edge.target()) & 1L;

                if (a != b) {
                    result += edge.weight();
                }
            }

            return result;
        }

        String formatPartition(long mask) {
            StringBuilder builder = new StringBuilder();

            for (int i = 0; i < vertexCount; i++) {
                builder.append(
                    ((mask >>> i) & 1L) == 1L ? '1' : '0'
                );
            }

            return builder.toString();
        }

        double classicalOptimum() {
            long limit = 1L << vertexCount;
            double best = Double.NEGATIVE_INFINITY;

            // One representative from each complementary pair.
            for (long mask = 0; mask < limit / 2; mask++) {
                best = Math.max(best, cutValue(mask));
            }

            return best;
        }
    }

    static final class ComplexState {

        private final double[] real;
        private final double[] imaginary;

        ComplexState(int dimension) {
            real = new double[dimension];
            imaginary = new double[dimension];
        }

        int size() {
            return real.length;
        }

        double probability(int index) {
            return real[index] * real[index]
                + imaginary[index] * imaginary[index];
        }

        double norm() {
            double result = 0.0;

            for (int i = 0; i < size(); i++) {
                result += probability(i);
            }

            return result;
        }
    }

    static final class QuantumCircuitSimulator {

        private final WeightedGraph graph;
        private final int n;
        private final int dimension;

        QuantumCircuitSimulator(WeightedGraph graph) {
            this.graph = graph;
            this.n = graph.vertexCount();
            this.dimension = 1 << n;
        }

        private ComplexState initialize() {
            ComplexState state = new ComplexState(dimension);
            double amplitude = 1.0 / Math.sqrt(dimension);

            for (int i = 0; i < dimension; i++) {
                state.real[i] = amplitude;
            }

            return state;
        }

        private void applyCostLayer(
            ComplexState state,
            double gamma
        ) {
            for (int i = 0; i < dimension; i++) {
                double cost = graph.cutValue(i);
                double angle = -gamma * cost;

                double oldReal = state.real[i];
                double oldImaginary = state.imaginary[i];

                state.real[i] =
                    oldReal * Math.cos(angle)
                    - oldImaginary * Math.sin(angle);

                state.imaginary[i] =
                    oldReal * Math.sin(angle)
                    + oldImaginary * Math.cos(angle);
            }
        }

        private void applyMixerLayer(
            ComplexState state,
            double beta
        ) {
            double cosine = Math.cos(beta);
            double sine = Math.sin(beta);

            for (int qubit = 0; qubit < n; qubit++) {
                int mask = 1 << qubit;

                for (int i = 0; i < dimension; i++) {
                    if ((i & mask) != 0) {
                        continue;
                    }

                    int j = i | mask;

                    double ar = state.real[i];
                    double ai = state.imaginary[i];
                    double br = state.real[j];
                    double bi = state.imaginary[j];

                    // Exact two-amplitude X-rotation.
                    state.real[i] = cosine * ar + sine * bi;
                    state.imaginary[i] =
                        cosine * ai - sine * br;

                    state.real[j] = cosine * br + sine * ai;
                    state.imaginary[j] =
                        cosine * bi - sine * ar;
                }
            }
        }

        ComplexState execute(QAOAParameters parameters) {
            ComplexState state = initialize();

            applyCostLayer(state, parameters.gamma());
            applyMixerLayer(state, parameters.beta());

            if (Math.abs(state.norm() - 1.0)
                > NORMALIZATION_TOLERANCE) {
                throw new OptimizationException(
                    "State normalization failed."
                );
            }

            return state;
        }

        double expectedCut(ComplexState state) {
            double result = 0.0;

            for (int i = 0; i < dimension; i++) {
                result += state.probability(i)
                    * graph.cutValue(i);
            }

            return result;
        }

        long mostProbableState(ComplexState state) {
            long best = 0;
            double bestProbability = -1.0;

            for (int i = 0; i < dimension; i++) {
                double probability = state.probability(i);

                if (probability > bestProbability) {
                    bestProbability = probability;
                    best = i;
                }
            }

            return best;
        }
    }

    interface ParameterOptimizer {
        OptimizationResult optimize();
    }

    static final class GridSearchOptimizer
        implements ParameterOptimizer {

        private final QuantumCircuitSimulator simulator;
        private final WeightedGraph graph;
        private final int gammaSteps;
        private final int betaSteps;

        private ExperimentStatus status =
            ExperimentStatus.CREATED;

        GridSearchOptimizer(
            QuantumCircuitSimulator simulator,
            WeightedGraph graph,
            int gammaSteps,
            int betaSteps
        ) {
            this.simulator = simulator;
            this.graph = graph;

            if (gammaSteps < 2 || betaSteps < 2) {
                throw new IllegalArgumentException(
                    "Grid resolution must be at least two."
                );
            }

            this.gammaSteps = gammaSteps;
            this.betaSteps = betaSteps;
        }

        @Override
        public OptimizationResult optimize() {
            if (status != ExperimentStatus.CREATED) {
                throw new IllegalStateException(
                    "Experiment cannot be restarted."
                );
            }

            status = ExperimentStatus.RUNNING;

            try {
                double bestExpected =
                    Double.NEGATIVE_INFINITY;

                QAOAParameters bestParameters =
                    new QAOAParameters(0.0, 0.0);

                ComplexState bestState = null;
                long evaluations = 0;

                for (int i = 0; i < gammaSteps; i++) {
                    double gamma =
                        2.0 * PI * i / gammaSteps;

                    for (int j = 0; j < betaSteps; j++) {
                        double beta =
                            PI * j / betaSteps;

                        QAOAParameters parameters =
                            new QAOAParameters(gamma, beta);

                        ComplexState state =
                            simulator.execute(parameters);

                        double expected =
                            simulator.expectedCut(state);

                        evaluations++;

                        if (expected > bestExpected) {
                            bestExpected = expected;
                            bestParameters = parameters;
                            bestState = state;
                        }
                    }
                }

                if (bestState == null) {
                    throw new OptimizationException(
                        "No valid candidate was evaluated."
                    );
                }

                long observed =
                    simulator.mostProbableState(bestState);

                double classical = graph.classicalOptimum();

                double ratio = classical > 0
                    ? bestExpected / classical
                    : 0.0;

                OptimizationResult result =
                    new OptimizationResult(
                        bestParameters,
                        bestExpected,
                        graph.formatPartition(observed),
                        graph.cutValue(observed),
                        classical,
                        ratio,
                        evaluations
                    );

                status = ExperimentStatus.COMPLETED;
                return result;

            } catch (RuntimeException exception) {
                status = ExperimentStatus.FAILED;
                throw exception;
            }
        }

        ExperimentStatus status() {
            return status;
        }
    }

    public static void main(String[] args) {
        try {
            WeightedGraph graph = new WeightedGraph(
                6,
                List.of(
                    new Edge(0, 1, 1.0),
                    new Edge(0, 2, 1.0),
                    new Edge(1, 2, 1.0),
                    new Edge(1, 3, 1.0),
                    new Edge(2, 4, 1.0),
                    new Edge(3, 4, 1.0),
                    new Edge(3, 5, 1.0),
                    new Edge(4, 5, 1.0),
                    new Edge(0, 5, 1.0)
                )
            );

            QuantumCircuitSimulator simulator =
                new QuantumCircuitSimulator(graph);

            ParameterOptimizer optimizer =
                new GridSearchOptimizer(
                    simulator,
                    graph,
                    40,
                    40
                );

            OptimizationResult result =
                optimizer.optimize();

            System.out.println("ENTERPRISE QAOA MAX-CUT ENGINE");
            System.out.println("==============================");
            System.out.println("Vertices: " + graph.vertexCount());
            System.out.println("Edges: " + graph.edges().size());
            System.out.println("Circuit depth: 1");

            System.out.printf(
                "Gamma: %.6f%n",
                result.parameters().gamma()
            );

            System.out.printf(
                "Beta: %.6f%n",
                result.parameters().beta()
            );

            System.out.printf(
                "Expected cut: %.6f%n",
                result.expectedCut()
            );

            System.out.println(
                "Observed partition: "
                    + result.observedPartition()
            );

            System.out.printf(
                "Observed cut: %.6f%n",
                result.observedCut()
            );

            System.out.printf(
                "Classical optimum: %.6f%n",
                result.classicalOptimum()
            );

            System.out.printf(
                "Approximation ratio: %.4f%n",
                result.approximationRatio()
            );

            System.out.println(
                "Evaluations: " + result.evaluations()
            );

            System.out.println("Status: COMPLETED");

        } catch (RuntimeException exception) {
            System.err.println(
                "QAOA experiment failed: "
                    + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
