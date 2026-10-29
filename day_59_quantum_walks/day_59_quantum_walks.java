import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class QuantumWalkGovernanceDemo {

    enum WalkModel {
        DISCRETE_COINED,
        CONTINUOUS_TIME
    }

    enum NodeRole {
        START,
        TARGET,
        INTERMEDIATE
    }

    record Node(int id, NodeRole role) {
        Node {
            if (id < 0) {
                throw new IllegalArgumentException("Node id cannot be negative.");
            }
            Objects.requireNonNull(role, "Node role is required.");
        }
    }

    record ProbabilityResult(
            List<Double> probabilities,
            double normalizationError
    ) {
        ProbabilityResult {
            probabilities = List.copyOf(probabilities);
        }

        boolean valid() {
            return normalizationError < 1e-9;
        }
    }

    static final class InvalidWalkException extends Exception {
        InvalidWalkException(String message) {
            super(message);
        }
    }

    static final class Graph {
        private final List<List<Integer>> adjacency;

        Graph(List<List<Integer>> adjacency) throws InvalidWalkException {
            if (adjacency == null || adjacency.isEmpty()) {
                throw new InvalidWalkException("Graph cannot be empty.");
            }

            int n = adjacency.size();

            for (List<Integer> row : adjacency) {
                if (row == null || row.size() != n) {
                    throw new InvalidWalkException(
                            "Adjacency matrix must be square."
                    );
                }

                for (Integer value : row) {
                    if (value == null || (value != 0 && value != 1)) {
                        throw new InvalidWalkException(
                                "Adjacency values must be 0 or 1."
                        );
                    }
                }
            }

            for (int i = 0; i < n; i++) {
                if (adjacency.get(i).get(i) != 0) {
                    throw new InvalidWalkException(
                            "Self-loops are not supported."
                    );
                }

                for (int j = 0; j < n; j++) {
                    if (!adjacency.get(i).get(j)
                            .equals(adjacency.get(j).get(i))) {
                        throw new InvalidWalkException(
                                "Graph must be undirected."
                        );
                    }
                }
            }

            this.adjacency = adjacency.stream()
                    .map(List::copyOf)
                    .toList();
        }

        int size() {
            return adjacency.size();
        }

        List<Integer> neighbors(int node) throws InvalidWalkException {
            validateNode(node);

            List<Integer> result = new ArrayList<>();
            for (int i = 0; i < size(); i++) {
                if (adjacency.get(node).get(i) == 1) {
                    result.add(i);
                }
            }
            return result;
        }

        int edge(int from, int to) {
            return adjacency.get(from).get(to);
        }

        void validateNode(int node) throws InvalidWalkException {
            if (node < 0 || node >= size()) {
                throw new InvalidWalkException(
                        "Node " + node + " is outside the graph."
                );
            }
        }
    }

    interface WalkPolicy {
        ProbabilityResult execute(
                Graph graph,
                int start,
                double time
        ) throws InvalidWalkException;
    }

    static final class ContinuousTimePolicy implements WalkPolicy {
        @Override
        public ProbabilityResult execute(
                Graph graph,
                int start,
                double time
        ) throws InvalidWalkException {
            graph.validateNode(start);

            if (!Double.isFinite(time) || time < 0) {
                throw new InvalidWalkException(
                        "Time must be finite and non-negative."
                );
            }

            int n = graph.size();
            double[] real = new double[n];
            double[] imaginary = new double[n];
            double[] resultReal = new double[n];
            double[] resultImaginary = new double[n];

            real[start] = 1.0;
            resultReal[start] = 1.0;

            for (int k = 1; k <= 100; k++) {
                double[] nextReal = new double[n];
                double[] nextImaginary = new double[n];

                for (int i = 0; i < n; i++) {
                    for (int j = 0; j < n; j++) {
                        if (graph.edge(i, j) == 1) {
                            nextReal[i] += real[j];
                            nextImaginary[i] += imaginary[j];
                        }
                    }
                }

                double factorReal = 0.0;
                double factorImaginary = -time / k;

                double maximum = 0.0;

                for (int i = 0; i < n; i++) {
                    double transformedReal =
                            factorReal * nextReal[i]
                                    - factorImaginary * nextImaginary[i];

                    double transformedImaginary =
                            factorReal * nextImaginary[i]
                                    + factorImaginary * nextReal[i];

                    real[i] = transformedReal;
                    imaginary[i] = transformedImaginary;

                    resultReal[i] += transformedReal;
                    resultImaginary[i] += transformedImaginary;

                    maximum = Math.max(
                            maximum,
                            Math.hypot(transformedReal, transformedImaginary)
                    );
                }

                if (maximum < 1e-14) {
                    break;
                }
            }

            double normSquared = 0.0;
            for (int i = 0; i < n; i++) {
                normSquared +=
                        resultReal[i] * resultReal[i]
                                + resultImaginary[i] * resultImaginary[i];
            }

            if (normSquared <= 1e-20) {
                throw new InvalidWalkException(
                        "Numerical state became invalid."
                );
            }

            double inverseNorm = 1.0 / Math.sqrt(normSquared);
            List<Double> probabilities = new ArrayList<>();

            for (int i = 0; i < n; i++) {
                double normalizedReal = resultReal[i] * inverseNorm;
                double normalizedImaginary = resultImaginary[i] * inverseNorm;
                probabilities.add(
                        normalizedReal * normalizedReal
                                + normalizedImaginary * normalizedImaginary
                );
            }

            double total = probabilities.stream()
                    .mapToDouble(Double::doubleValue)
                    .sum();

            return new ProbabilityResult(
                    probabilities,
                    Math.abs(total - 1.0)
            );
        }
    }

    static final class WalkService {
        private final Map<WalkModel, WalkPolicy> policies =
                new EnumMap<>(WalkModel.class);

        WalkService() {
            policies.put(
                    WalkModel.CONTINUOUS_TIME,
                    new ContinuousTimePolicy()
            );
        }

        ProbabilityResult evaluate(
                WalkModel model,
                Graph graph,
                int start,
                double time
        ) throws InvalidWalkException {
            WalkPolicy policy = policies.get(model);

            if (policy == null) {
                throw new InvalidWalkException(
                        "No policy is registered for " + model
                );
            }

            return policy.execute(graph, start, time);
        }
    }

    static final class RouteAnalysis {
        private final Graph graph;

        RouteAnalysis(Graph graph) {
            this.graph = graph;
        }

        Map<Integer, Double> rankTargets(
                ProbabilityResult result
        ) {
            Map<Integer, Double> ranked = new HashMap<>();

            for (int i = 0; i < result.probabilities().size(); i++) {
                ranked.put(i, result.probabilities().get(i));
            }

            return ranked.entrySet()
                    .stream()
                    .sorted(
                            Map.Entry.<Integer, Double>comparingByValue()
                                    .reversed()
                    )
                    .collect(
                            java.util.stream.Collectors.toMap(
                                    Map.Entry::getKey,
                                    Map.Entry::getValue,
                                    (left, right) -> left,
                                    java.util.LinkedHashMap::new
                            )
                    );
        }

        boolean reachable(int start, int target)
                throws InvalidWalkException {
            graph.validateNode(start);
            graph.validateNode(target);

            boolean[] visited = new boolean[graph.size()];
            List<Integer> queue = new ArrayList<>();
            queue.add(start);
            visited[start] = true;

            for (int cursor = 0; cursor < queue.size(); cursor++) {
                int current = queue.get(cursor);

                if (current == target) {
                    return true;
                }

                for (int neighbor : graph.neighbors(current)) {
                    if (!visited[neighbor]) {
                        visited[neighbor] = true;
                        queue.add(neighbor);
                    }
                }
            }

            return false;
        }
    }

    public static void main(String[] args) {
        try {
            Graph graph = new Graph(List.of(
                    List.of(0, 1, 0, 1),
                    List.of(1, 0, 1, 0),
                    List.of(0, 1, 0, 1),
                    List.of(1, 0, 1, 0)
            ));

            WalkService service = new WalkService();

            ProbabilityResult result = service.evaluate(
                    WalkModel.CONTINUOUS_TIME,
                    graph,
                    0,
                    1.5
            );

            if (!result.valid()) {
                throw new InvalidWalkException(
                        "Probability normalization check failed."
                );
            }

            System.out.println("Continuous-time quantum walk:");
            for (int i = 0; i < result.probabilities().size(); i++) {
                System.out.printf(
                        "  node %d: %.8f%n",
                        i,
                        result.probabilities().get(i)
                );
            }

            RouteAnalysis analysis = new RouteAnalysis(graph);

            System.out.println("\nProbability ranking:");
            analysis.rankTargets(result)
                    .forEach(
                            (node, probability) ->
                                    System.out.printf(
                                            "  node %d -> %.8f%n",
                                            node,
                                            probability
                                    )
                    );

            System.out.println(
                    "\nNode 2 reachable from node 0: "
                            + analysis.reachable(0, 2)
            );

            Graph disconnected = new Graph(List.of(
                    List.of(0, 1, 0),
                    List.of(1, 0, 0),
                    List.of(0, 0, 0)
            ));

            System.out.println(
                    "Disconnected node reachable: "
                            + new RouteAnalysis(disconnected).reachable(0, 2)
            );

            System.out.println(
                    "\nEnterprise workflow validation passed."
            );

        } catch (InvalidWalkException exception) {
            System.err.println(
                    "Quantum-walk workflow rejected: "
                            + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
