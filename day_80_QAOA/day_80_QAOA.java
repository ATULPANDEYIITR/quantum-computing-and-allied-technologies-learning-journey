import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;

/**
 * Quantum Approximate Optimization Algorithm (QAOA)
 *
 * Enterprise-oriented Max-Cut experiment management system.
 *
 * Java 17 features:
 * - Records and immutable domain types.
 * - Explicit experiment state transitions.
 * - Circuit simulation and parameter validation.
 * - Reviewable optimization history.
 * - Concurrent experiment orchestration.
 * - Typed experiment outcomes.
 * - Measurement probability reporting.
 *
 * Dependencies: Java 17 standard library.
 */
public class QAOAEnterprise {

    private static final double EPSILON = 1e-10;
    private static final int MAX_QUBITS = 18;

    enum ExperimentStatus {
        CREATED,
        QUEUED,
        RUNNING,
        COMPLETED,
        FAILED,
        CANCELLED
    }

    enum OptimizationStrategy {
        COORDINATE_SEARCH
    }

    static class QAOAException extends RuntimeException {
        QAOAException(String message) {
            super(message);
        }

        QAOAException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    record Edge(int source, int target, double weight) {
        Edge {
            if (source < 0 || target < 0 || source == target) {
                throw new IllegalArgumentException("Invalid edge endpoints.");
            }

            if (!Double.isFinite(weight) || weight <= 0) {
                throw new IllegalArgumentException("Invalid edge weight.");
            }
        }
    }

    static final class Graph {
        private final int vertexCount;
        private final List<Edge> edges;

        Graph(int vertexCount, List<Edge> edges) {
            if (vertexCount < 1 || vertexCount > MAX_QUBITS) {
                throw new IllegalArgumentException("Unsupported graph size.");
            }

            Set<String> uniqueEdges = new HashSet<>();

            for (Edge edge : edges) {
                Objects.requireNonNull(edge);

                if (
                    edge.source() >= vertexCount ||
                    edge.target() >= vertexCount
                ) {
                    throw new IllegalArgumentException("Invalid edge.");
                }

                int a = Math.min(edge.source(), edge.target());
                int b = Math.max(edge.source(), edge.target());

                if (!uniqueEdges.add(a + ":" + b)) {
                    throw new IllegalArgumentException("Duplicate edge.");
                }
            }

            this.vertexCount = vertexCount;
            this.edges = List.copyOf(edges);
        }

        int vertexCount() {
            return vertexCount;
        }

        List<Edge> edges() {
            return edges;
        }

        double cutValue(long state) {
            double result = 0;

            for (Edge edge : edges) {
                boolean a = ((state >> edge.source()) & 1L) == 1L;
                boolean b = ((state >> edge.target()) & 1L) == 1L;

                if (a != b) {
                    result += edge.weight();
                }
            }

            return result;
        }

        String bitstring(long state) {
            StringBuilder result = new StringBuilder();

            for (int i = vertexCount - 1; i >= 0; i--) {
                result.append((state >> i) & 1L);
            }

            return result.toString();
        }

        record Optimum(double value, List<String> solutions) {
            Optimum {
                solutions = List.copyOf(solutions);
            }
        }

        Optimum findOptimum() {
            long dimension = 1L << vertexCount;

            double best = Double.NEGATIVE_INFINITY;
            List<String> solutions = new ArrayList<>();

            for (long state = 0; state < dimension; state++) {
                double value = cutValue(state);

                if (value > best + EPSILON) {
                    best = value;
                    solutions.clear();
                    solutions.add(bitstring(state));
                } else if (Math.abs(value - best) <= EPSILON) {
                    solutions.add(bitstring(state));
                }
            }

            return new Optimum(best, solutions);
        }
    }

    record Complex(double real, double imaginary) {

        Complex multiply(Complex other) {
            return new Complex(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        Complex scale(double factor) {
            return new Complex(real * factor, imaginary * factor);
        }

        Complex subtract(Complex other) {
            return new Complex(
                real - other.real,
                imaginary - other.imaginary
            );
        }

        double probability() {
            return real * real + imaginary * imaginary;
        }
    }

    static final class StateVector {
        private final int qubitCount;
        private final int dimension;
        private final Complex[] amplitudes;

        StateVector(int qubitCount) {
            if (qubitCount < 1 || qubitCount > MAX_QUBITS) {
                throw new IllegalArgumentException("Unsupported qubit count.");
            }

            this.qubitCount = qubitCount;
            this.dimension = 1 << qubitCount;
            this.amplitudes = new Complex[dimension];

            double initial = 1.0 / Math.sqrt(dimension);

            for (int i = 0; i < dimension; i++) {
                amplitudes[i] = new Complex(initial, 0);
            }
        }

        void applyCost(Graph graph, double gamma) {
            for (int state = 0; state < dimension; state++) {
                double phase = -gamma * graph.cutValue(state);

                Complex rotation = new Complex(
                    Math.cos(phase),
                    Math.sin(phase)
                );

                amplitudes[state] = amplitudes[state].multiply(rotation);
            }
        }

        void applyMixer(double beta) {
            double cosine = Math.cos(beta);
            double sine = Math.sin(beta);

            for (int qubit = 0; qubit < qubitCount; qubit++) {
                int mask = 1 << qubit;

                for (int state = 0; state < dimension; state++) {
                    if ((state & mask) != 0) {
                        continue;
                    }

                    int partner = state | mask;

                    Complex a = amplitudes[state];
                    Complex b = amplitudes[partner];

                    amplitudes[state] = new Complex(
                        cosine * a.real() + sine * b.imaginary(),
                        cosine * a.imaginary() - sine * b.real()
                    );

                    amplitudes[partner] = new Complex(
                        cosine * b.real() + sine * a.imaginary(),
                        cosine * b.imaginary() - sine * a.real()
                    );
                }
            }
        }

        double expectation(Graph graph) {
            double result = 0;

            for (int state = 0; state < dimension; state++) {
                result += amplitudes[state].probability()
                    * graph.cutValue(state);
            }

            return result;
        }

        Map<String, Double> probabilityDistribution(Graph graph) {
            Map<String, Double> result = new java.util.LinkedHashMap<>();

            for (int state = 0; state < dimension; state++) {
                result.put(
                    graph.bitstring(state),
                    amplitudes[state].probability()
                );
            }

            return Collections.unmodifiableMap(result);
        }

        void validateNormalization() {
            double total = 0;

            for (Complex amplitude : amplitudes) {
                total += amplitude.probability();
            }

            if (Math.abs(total - 1.0) > 1e-8) {
                throw new QAOAException("State normalization failure.");
            }
        }
    }

    record CircuitParameters(
        List<Double> gamma,
        List<Double> beta
    ) {
        CircuitParameters {
            gamma = List.copyOf(gamma);
            beta = List.copyOf(beta);

            if (gamma.isEmpty() || gamma.size() != beta.size()) {
                throw new IllegalArgumentException(
                    "Invalid QAOA parameter dimensions."
                );
            }

            if (
                gamma.stream().anyMatch(v -> !Double.isFinite(v)) ||
                beta.stream().anyMatch(v -> !Double.isFinite(v))
            ) {
                throw new IllegalArgumentException(
                    "Parameters must be finite."
                );
            }
        }

        int depth() {
            return gamma.size();
        }
    }

    record OptimizationPolicy(
        int maximumIterations,
        double initialStep,
        OptimizationStrategy strategy
    ) {
        OptimizationPolicy {
            if (maximumIterations < 1) {
                throw new IllegalArgumentException("Invalid iteration count.");
            }

            if (!Double.isFinite(initialStep) || initialStep <= 0) {
                throw new IllegalArgumentException("Invalid step size.");
            }

            Objects.requireNonNull(strategy);
        }
    }

    record OptimizationResult(
        CircuitParameters parameters,
        double expectation,
        List<Double> history,
        int iterations
    ) {
        OptimizationResult {
            Objects.requireNonNull(parameters);
            history = List.copyOf(history);
        }
    }

    static final class QAOACircuit {
        private final Graph graph;
        private final int depth;

        QAOACircuit(Graph graph, int depth) {
            this.graph = Objects.requireNonNull(graph);

            if (depth < 1 || depth > 8) {
                throw new IllegalArgumentException("Invalid QAOA depth.");
            }

            this.depth = depth;
        }

        StateVector simulate(CircuitParameters parameters) {
            validateParameters(parameters);

            StateVector state = new StateVector(graph.vertexCount());

            for (int layer = 0; layer < depth; layer++) {
                state.applyCost(graph, parameters.gamma().get(layer));
                state.applyMixer(parameters.beta().get(layer));
            }

            state.validateNormalization();

            return state;
        }

        private void validateParameters(CircuitParameters parameters) {
            if (parameters.depth() != depth) {
                throw new IllegalArgumentException(
                    "Circuit depth and parameter depth differ."
                );
            }
        }

        double expectation(CircuitParameters parameters) {
            return simulate(parameters).expectation(graph);
        }

        OptimizationResult optimize(
            CircuitParameters initial,
            OptimizationPolicy policy
        ) {
            validateParameters(initial);

            List<Double> gamma = new ArrayList<>(initial.gamma());
            List<Double> beta = new ArrayList<>(initial.beta());

            double best = expectation(initial);
            double step = policy.initialStep();

            List<Double> history = new ArrayList<>();
            history.add(best);

            for (
                int iteration = 0;
                iteration < policy.maximumIterations();
                iteration++
            ) {
                boolean improved = false;

                for (int group = 0; group < 2; group++) {
                    List<Double> parameters =
                        group == 0 ? gamma : beta;

                    double upper = group == 0
                        ? Math.PI
                        : Math.PI / 2;

                    for (int index = 0; index < depth; index++) {
                        double original = parameters.get(index);
                        double localBest = best;
                        double selected = original;

                        for (int direction : new int[]{-1, 1}) {
                            double candidate = Math.max(
                                0,
                                Math.min(
                                    upper,
                                    original + direction * step
                                )
                            );

                            parameters.set(index, candidate);

                            CircuitParameters test =
                                new CircuitParameters(gamma, beta);

                            double value = expectation(test);

                            if (value > localBest + EPSILON) {
                                localBest = value;
                                selected = candidate;
                            }
                        }

                        parameters.set(index, selected);

                        if (localBest > best + EPSILON) {
                            best = localBest;
                            improved = true;
                        }
                    }
                }

                history.add(best);

                if (!improved) {
                    step *= 0.5;
                }

                if (step < 1e-5) {
                    break;
                }
            }

            return new OptimizationResult(
                new CircuitParameters(gamma, beta),
                best,
                history,
                history.size() - 1
            );
        }
    }

    record ExperimentRequest(
        String experimentName,
        CircuitParameters initialParameters,
        OptimizationPolicy policy
    ) {
        ExperimentRequest {
            if (
                experimentName == null ||
                experimentName.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Experiment name is required."
                );
            }

            Objects.requireNonNull(initialParameters);
            Objects.requireNonNull(policy);
        }
    }

    record ExperimentReport(
        UUID id,
        String name,
        ExperimentStatus status,
        OptimizationResult result,
        double classicalOptimum,
        double approximationRatio,
        Map<String, Double> probabilities,
        String error
    ) {}

    static final class Experiment {
        private final UUID id = UUID.randomUUID();
        private final ExperimentRequest request;

        private final AtomicReference<ExperimentStatus> status =
            new AtomicReference<>(ExperimentStatus.CREATED);

        private OptimizationResult result;
        private String error;

        Experiment(ExperimentRequest request) {
            this.request = request;
        }

        void transition(
            ExperimentStatus expected,
            ExperimentStatus next
        ) {
            if (!status.compareAndSet(expected, next)) {
                throw new QAOAException(
                    "Invalid experiment state transition: "
                        + status.get() + " -> " + next
                );
            }
        }

        ExperimentStatus status() {
            return status.get();
        }
    }

    static final class ExperimentService implements AutoCloseable {
        private final Graph graph;
        private final QAOACircuit circuit;
        private final ExecutorService executor;

        private final Map<UUID, Experiment> experiments =
            new ConcurrentHashMap<>();

        ExperimentService(Graph graph, int workerCount, int depth) {
            if (workerCount < 1 || workerCount > 32) {
                throw new IllegalArgumentException("Invalid worker count.");
            }

            this.graph = graph;
            this.circuit = new QAOACircuit(graph, depth);

            this.executor = Executors.newFixedThreadPool(workerCount);
        }

        CompletableFuture<ExperimentReport> submit(
            ExperimentRequest request
        ) {
            Experiment experiment = new Experiment(request);

            if (request.initialParameters().depth() != circuit.depth) {
                throw new IllegalArgumentException(
                    "Parameter depth mismatch."
                );
            }

            experiments.put(experiment.id, experiment);

            experiment.transition(
                ExperimentStatus.CREATED,
                ExperimentStatus.QUEUED
            );

            return CompletableFuture.supplyAsync(() -> {
                try {
                    experiment.transition(
                        ExperimentStatus.QUEUED,
                        ExperimentStatus.RUNNING
                    );

                    experiment.result = circuit.optimize(
                        request.initialParameters(),
                        request.policy()
                    );

                    experiment.transition(
                        ExperimentStatus.RUNNING,
                        ExperimentStatus.COMPLETED
                    );

                    Graph.Optimum optimum = graph.findOptimum();

                    StateVector finalState = circuit.simulate(
                        experiment.result.parameters()
                    );

                    Map<String, Double> probabilities =
                        finalState.probabilityDistribution(graph);

                    double ratio = optimum.value() > EPSILON
                        ? experiment.result.expectation() / optimum.value()
                        : 1.0;

                    return new ExperimentReport(
                        experiment.id,
                        request.experimentName(),
                        experiment.status(),
                        experiment.result,
                        optimum.value(),
                        ratio,
                        probabilities,
                        null
                    );

                } catch (RuntimeException exception) {
                    experiment.error = exception.getMessage();

                    experiment.transition(
                        ExperimentStatus.RUNNING,
                        ExperimentStatus.FAILED
                    );

                    throw new QAOAException(
                        "Experiment failed: " + experiment.error,
                        exception
                    );
                }
            }, executor);
        }

        ExperimentStatus getStatus(UUID id) {
            Experiment experiment = experiments.get(id);

            if (experiment == null) {
                throw new QAOAException("Experiment not found.");
            }

            return experiment.status();
        }

        @Override
        public void close() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    public static void main(String[] args) {
        Graph graph = new Graph(
            4,
            List.of(
                new Edge(0, 1, 1),
                new Edge(0, 2, 1),
                new Edge(1, 2, 1),
                new Edge(1, 3, 1),
                new Edge(2, 3, 1)
            )
        );

        Graph.Optimum optimum = graph.findOptimum();

        System.out.println("QAOA ENTERPRISE EXPERIMENT SERVICE");
        System.out.println("Vertices: " + graph.vertexCount());
        System.out.println("Edges: " + graph.edges().size());
        System.out.println("Classical optimum: " + optimum.value());
        System.out.println("Optimal assignments: " + optimum.solutions());

        CircuitParameters initial = new CircuitParameters(
            List.of(0.7),
            List.of(0.3)
        );

        OptimizationPolicy policy = new OptimizationPolicy(
            100,
            0.15,
            OptimizationStrategy.COORDINATE_SEARCH
        );

        try (ExperimentService service =
                 new ExperimentService(graph, 2, 1)) {

            ExperimentRequest request = new ExperimentRequest(
                "Enterprise-MaxCut-001",
                initial,
                policy
            );

            ExperimentReport report = service.submit(request).join();

            System.out.println("\nExperiment report");
            System.out.println("ID: " + report.id());
            System.out.println("Status: " + report.status());

            System.out.printf(
                "Expected cut: %.6f%n",
                report.result().expectation()
            );

            System.out.printf(
                "Approximation ratio: %.6f%n",
                report.approximationRatio()
            );

            System.out.println(
                "Iterations: " + report.result().iterations()
            );

            System.out.println("\nMeasurement probabilities:");

            report.probabilities()
                .entrySet()
                .stream()
                .sorted(
                    Map.Entry.<String, Double>comparingByValue()
                        .reversed()
                )
                .limit(8)
                .forEach(entry ->
                    System.out.printf(
                        "%s : %.6f%n",
                        entry.getKey(),
                        entry.getValue()
                    )
                );

            if (
                report.result().expectation() >
                report.classicalOptimum() + EPSILON
            ) {
                throw new QAOAException(
                    "Expectation exceeds classical optimum."
                );
            }

            System.out.println("\nValidation: PASSED");
        }
    }
}
