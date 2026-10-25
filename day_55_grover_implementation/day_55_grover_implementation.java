import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;

public final class GroverEnterpriseSearch {

    public enum SearchStatus {
        CREATED,
        EXECUTED,
        FAILED
    }

    public record SearchPolicy(
            int maximumQubits,
            int maximumIterations,
            double normalizationTolerance) {

        public SearchPolicy {
            if (maximumQubits < 1 || maximumQubits > 20) {
                throw new IllegalArgumentException("Maximum qubits must be 1..20.");
            }
            if (maximumIterations < 0) {
                throw new IllegalArgumentException("Maximum iterations cannot be negative.");
            }
            if (!Double.isFinite(normalizationTolerance)
                    || normalizationTolerance <= 0
                    || normalizationTolerance > 0.01) {
                throw new IllegalArgumentException("Invalid normalization tolerance.");
            }
        }
    }

    public record SearchReport(
            int qubits,
            int stateCount,
            List<Integer> markedStates,
            int iterations,
            double successProbability,
            int measuredState,
            SearchStatus status) {

        public SearchReport {
            markedStates = List.copyOf(markedStates);
            Objects.requireNonNull(status, "status");
        }
    }

    public static final class SearchException extends RuntimeException {
        public SearchException(String message) {
            super(message);
        }
    }

    public static final class SearchService {
        private final SearchPolicy policy;

        public SearchService(SearchPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        public int optimalIterations(int stateCount, int markedCount) {
            if (stateCount < 1 || markedCount < 0 || markedCount > stateCount) {
                throw new IllegalArgumentException("Invalid search dimensions.");
            }
            if (markedCount == 0 || markedCount == stateCount) {
                return 0;
            }
            double theta = Math.asin(Math.sqrt(
                    (double) markedCount / stateCount));
            return Math.max(0, (int) Math.round(
                    Math.PI / (4.0 * theta) - 0.5));
        }

        public SearchReport execute(
                int qubits,
                Set<Integer> requestedTargets,
                Integer requestedIterations) {

            if (qubits < 1 || qubits > policy.maximumQubits()) {
                throw new IllegalArgumentException("Qubit count violates policy.");
            }
            Objects.requireNonNull(requestedTargets, "requestedTargets");
            if (requestedTargets.isEmpty()) {
                throw new IllegalArgumentException("At least one target is required.");
            }

            int stateCount = 1 << qubits;
            TreeSet<Integer> targets = new TreeSet<>(requestedTargets);
            if (targets.size() != requestedTargets.size()) {
                throw new IllegalArgumentException("Duplicate targets are invalid.");
            }
            if (targets.stream().anyMatch(
                    target -> target == null || target < 0 || target >= stateCount)) {
                throw new IllegalArgumentException("Target is outside the search space.");
            }

            int iterations = requestedIterations == null
                    ? optimalIterations(stateCount, targets.size())
                    : requestedIterations;

            if (iterations < 0 || iterations > policy.maximumIterations()) {
                throw new IllegalArgumentException("Iterations violate execution policy.");
            }

            double[] amplitudes = new double[stateCount];
            java.util.Arrays.fill(amplitudes, 1.0 / Math.sqrt(stateCount));

            for (int iteration = 0; iteration < iterations; iteration++) {
                // The oracle changes phase only for states satisfying the predicate.
                for (int target : targets) {
                    amplitudes[target] = -amplitudes[target];
                }

                // The diffusion operation performs an inversion about the mean.
                double mean = 0.0;
                for (double amplitude : amplitudes) {
                    mean += amplitude;
                }
                mean /= stateCount;

                for (int i = 0; i < stateCount; i++) {
                    amplitudes[i] = 2.0 * mean - amplitudes[i];
                }
            }

            double norm = 0.0;
            double successProbability = 0.0;
            for (int i = 0; i < stateCount; i++) {
                double probability = amplitudes[i] * amplitudes[i];
                norm += probability;
                if (targets.contains(i)) {
                    successProbability += probability;
                }
            }

            if (!Double.isFinite(norm)
                    || Math.abs(norm - 1.0) > policy.normalizationTolerance()) {
                throw new SearchException("State normalization check failed.");
            }

            int measuredState = sample(amplitudes);
            return new SearchReport(
                    qubits,
                    stateCount,
                    new ArrayList<>(targets),
                    iterations,
                    successProbability,
                    measuredState,
                    SearchStatus.EXECUTED);
        }

        private int sample(double[] amplitudes) {
            // Production systems use a quantum device or a trusted random sampler.
            double threshold = 0.5;
            double cumulative = 0.0;
            for (int i = 0; i < amplitudes.length; i++) {
                cumulative += amplitudes[i] * amplitudes[i];
                if (cumulative >= threshold) {
                    return i;
                }
            }
            return amplitudes.length - 1;
        }
    }

    public static void main(String[] args) {
        SearchPolicy policy = new SearchPolicy(20, 100000, 1e-8);
        SearchService service = new SearchService(policy);

        SearchReport report = service.execute(
                4, Set.of(11), null);

        System.out.println("Enterprise quantum-search execution");
        System.out.println("Status: " + report.status());
        System.out.println("Qubits: " + report.qubits());
        System.out.println("State count: " + report.stateCount());
        System.out.println("Marked states: " + report.markedStates());
        System.out.println("Iterations: " + report.iterations());
        System.out.printf("Success probability: %.6f%n",
                report.successProbability());
        System.out.println("Measured state: " + report.measuredState());

        if (report.iterations() != 3 || report.successProbability() < 0.96) {
            throw new SearchException("Search validation failed.");
        }

        boolean invalidTargetRejected = false;
        try {
            service.execute(4, Set.of(16), null);
        } catch (IllegalArgumentException exception) {
            invalidTargetRejected = true;
        }
        if (!invalidTargetRejected) {
            throw new SearchException("Invalid target was not rejected.");
        }

        System.out.println("Validation checks passed.");
    }
}
