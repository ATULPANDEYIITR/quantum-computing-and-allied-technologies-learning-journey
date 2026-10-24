import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Enterprise-style quantum search service using a small state-vector simulator.
 *
 * Compile: javac GroverSearch.java
 * Run:     java GroverSearch
 */
public class GroverSearch {

    private static final int MAX_QUBITS = 20;

    enum SearchState {
        CREATED,
        VALIDATED,
        EXECUTING,
        COMPLETED,
        FAILED
    }

    record SearchRequest(int qubits, List<Integer> markedStates) {
        SearchRequest {
            if (qubits < 1 || qubits > MAX_QUBITS) {
                throw new IllegalArgumentException(
                    "Qubit count must be between 1 and " + MAX_QUBITS
                );
            }
            if (markedStates == null || markedStates.isEmpty()) {
                throw new IllegalArgumentException(
                    "At least one marked state is required."
                );
            }

            // Defensive copying prevents callers from changing a request
            // while a search service is processing it.
            markedStates = List.copyOf(markedStates);
        }
    }

    record SearchPolicy(int maximumIterations, double minimumSuccessProbability) {
        SearchPolicy {
            if (maximumIterations < 0) {
                throw new IllegalArgumentException(
                    "Maximum iterations cannot be negative."
                );
            }
            if (!Double.isFinite(minimumSuccessProbability)
                    || minimumSuccessProbability < 0.0
                    || minimumSuccessProbability > 1.0) {
                throw new IllegalArgumentException(
                    "Probability threshold must be between zero and one."
                );
            }
        }
    }

    record SearchResult(
        int qubits,
        List<Integer> markedStates,
        int iterations,
        List<Double> probabilities,
        double successProbability,
        int mostProbableState,
        SearchState state
    ) {
        SearchResult {
            markedStates = List.copyOf(markedStates);
            probabilities = List.copyOf(probabilities);
        }
    }

    interface SearchAudit {
        void record(SearchState state, String detail);
    }

    static final class ConsoleAudit implements SearchAudit {
        @Override
        public void record(SearchState state, String detail) {
            System.out.printf("[%s] %s%n", state, detail);
        }
    }

    static final class SearchService {
        private final SearchPolicy policy;
        private final SearchAudit audit;

        SearchService(SearchPolicy policy, SearchAudit audit) {
            this.policy = policy;
            this.audit = audit;
        }

        int optimalIterations(int qubits, int markedCount) {
            int size = 1 << qubits;

            if (markedCount == size) {
                return 0;
            }

            double theta = Math.asin(
                Math.sqrt((double) markedCount / size)
            );
            return Math.max(
                0,
                (int) Math.floor(Math.PI / (4.0 * theta) - 0.5)
            );
        }

        SearchResult execute(SearchRequest request) {
            SearchState state = SearchState.CREATED;

            try {
                state = SearchState.VALIDATED;
                validateMarkedStates(request);
                audit.record(state, "Request and search domain validated.");

                int size = 1 << request.qubits();
                int iterations = optimalIterations(
                    request.qubits(), request.markedStates().size()
                );

                if (iterations > policy.maximumIterations()) {
                    throw new IllegalStateException(
                        "Optimal iteration count exceeds service policy."
                    );
                }

                state = SearchState.EXECUTING;
                audit.record(state, "Executing Grover iterations: " + iterations);

                double[] amplitudes = new double[size];
                Arrays.fill(amplitudes, 1.0 / Math.sqrt(size));
                Set<Integer> marked = new HashSet<>(request.markedStates());

                for (int step = 0; step < iterations; step++) {
                    // Phase inversion is the oracle's only state change.
                    for (int target : marked) {
                        amplitudes[target] = -amplitudes[target];
                    }

                    double sum = 0.0;
                    for (double amplitude : amplitudes) {
                        sum += amplitude;
                    }

                    double twiceMean = 2.0 * sum / size;
                    for (int index = 0; index < size; index++) {
                        amplitudes[index] = twiceMean - amplitudes[index];
                    }
                }

                List<Double> probabilities = new ArrayList<>(size);
                double successProbability = 0.0;
                double norm = 0.0;
                int mostProbableState = 0;

                for (int index = 0; index < size; index++) {
                    double probability = amplitudes[index] * amplitudes[index];
                    probabilities.add(probability);
                    norm += probability;

                    if (marked.contains(index)) {
                        successProbability += probability;
                    }

                    if (probability > probabilities.get(mostProbableState)) {
                        mostProbableState = index;
                    }
                }

                if (Math.abs(norm - 1.0) > 1e-10) {
                    throw new ArithmeticException(
                        "State normalization failed."
                    );
                }

                if (successProbability < policy.minimumSuccessProbability()) {
                    audit.record(
                        SearchState.FAILED,
                        "Computed success probability is below policy threshold."
                    );
                    throw new IllegalStateException(
                        "Search result does not meet the configured probability threshold."
                    );
                }

                state = SearchState.COMPLETED;
                audit.record(state, "Search completed and validated.");

                return new SearchResult(
                    request.qubits(),
                    request.markedStates(),
                    iterations,
                    probabilities,
                    successProbability,
                    mostProbableState,
                    state
                );
            } catch (RuntimeException exception) {
                if (state != SearchState.FAILED) {
                    audit.record(SearchState.FAILED, exception.getMessage());
                }
                throw exception;
            }
        }

        private void validateMarkedStates(SearchRequest request) {
            int size = 1 << request.qubits();

            for (Integer target : request.markedStates()) {
                if (target == null || target < 0 || target >= size) {
                    throw new IllegalArgumentException(
                        "Marked states must be non-null and within the domain."
                    );
                }
            }

            if (new HashSet<>(request.markedStates()).size()
                    != request.markedStates().size()) {
                throw new IllegalArgumentException(
                    "Marked states must be unique."
                );
            }
        }
    }

    public static void main(String[] args) {
        SearchPolicy policy = new SearchPolicy(100, 0.90);
        SearchService service = new SearchService(policy, new ConsoleAudit());

        SearchRequest request = new SearchRequest(4, List.of(5));
        SearchResult result = service.execute(request);

        System.out.printf("%nSuccess probability: %.6f%n",
            result.successProbability());
        System.out.println("Most probable state: " + result.mostProbableState());
        System.out.println("Iterations: " + result.iterations());

        System.out.println("\nProbability distribution:");
        for (int state = 0; state < result.probabilities().size(); state++) {
            System.out.printf("%4d -> %.6f%n",
                state, result.probabilities().get(state));
        }

        if (result.mostProbableState() != 5) {
            throw new AssertionError("Unexpected most probable state.");
        }

        SearchResult allMarked = service.execute(
            new SearchRequest(2, List.of(0, 1, 2, 3))
        );
        if (allMarked.iterations() != 0
                || Math.abs(allMarked.successProbability() - 1.0) > 1e-10) {
            throw new AssertionError("All-marked case failed.");
        }

        try {
            service.execute(new SearchRequest(2, List.of(4)));
            throw new AssertionError("Invalid target should have been rejected.");
        } catch (IllegalArgumentException expected) {
            System.out.println("\nInvalid-domain request rejected correctly.");
        }
    }
}
