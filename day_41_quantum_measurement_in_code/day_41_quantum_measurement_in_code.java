import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

/**
 * Enterprise-oriented quantum measurement analysis.
 *
 * Separates prepared-state probabilities, execution requests, immutable
 * measurement results, and quality-control decisions.
 *
 * Compile: javac QuantumMeasurement.java
 * Run: java QuantumMeasurement
 */
public class QuantumMeasurement {

    enum RunStatus {
        COMPLETED,
        REJECTED
    }

    static final class PreparedState {
        private final Map<String, Double> probabilities;

        PreparedState(Map<String, Double> probabilities) {
            if (probabilities == null || probabilities.isEmpty()) {
                throw new IllegalArgumentException("State distribution is empty.");
            }

            Map<String, Double> copy = new LinkedHashMap<>();
            int width = -1;
            double sum = 0.0;

            for (Map.Entry<String, Double> entry : probabilities.entrySet()) {
                String outcome = entry.getKey();
                Double probability = entry.getValue();

                if (outcome == null || !outcome.matches("[01]+")) {
                    throw new IllegalArgumentException(
                            "Outcomes must be binary strings.");
                }
                if (width == -1) {
                    width = outcome.length();
                } else if (width != outcome.length()) {
                    throw new IllegalArgumentException(
                            "All outcomes must have equal register width.");
                }
                if (probability == null || !Double.isFinite(probability)
                        || probability < 0.0) {
                    throw new IllegalArgumentException(
                            "Probabilities must be finite and non-negative.");
                }

                copy.put(outcome, probability);
                sum += probability;
            }

            if (Math.abs(sum - 1.0) > 1e-9) {
                throw new IllegalArgumentException(
                        "Probabilities must sum to one.");
            }

            Map<String, Double> normalized = new LinkedHashMap<>();
            for (Map.Entry<String, Double> entry : copy.entrySet()) {
                normalized.put(entry.getKey(), entry.getValue() / sum);
            }
            this.probabilities = Collections.unmodifiableMap(normalized);
        }

        Map<String, Double> probabilities() {
            return probabilities;
        }
    }

    static final class MeasurementRequest {
        private final String experimentName;
        private final int shots;
        private final long seed;

        MeasurementRequest(String experimentName, int shots, long seed) {
            if (experimentName == null || experimentName.isBlank()) {
                throw new IllegalArgumentException("Experiment name is required.");
            }
            if (shots <= 0) {
                throw new IllegalArgumentException("Shots must be positive.");
            }
            this.experimentName = experimentName;
            this.shots = shots;
            this.seed = seed;
        }
    }

    static final class MeasurementResult {
        private final UUID runId;
        private final String experimentName;
        private final int shots;
        private final RunStatus status;
        private final Map<String, Integer> counts;
        private final Map<String, Double> expected;
        private final Map<String, Double> observed;

        MeasurementResult(
                String experimentName,
                int shots,
                Map<String, Integer> counts,
                Map<String, Double> expected) {
            this.runId = UUID.randomUUID();
            this.experimentName = experimentName;
            this.shots = shots;
            this.status = RunStatus.COMPLETED;
            this.counts = Collections.unmodifiableMap(
                    new LinkedHashMap<>(counts));
            this.expected = Collections.unmodifiableMap(
                    new LinkedHashMap<>(expected));

            Map<String, Double> frequencies = new LinkedHashMap<>();
            int total = 0;
            for (int count : counts.values()) {
                if (count < 0) {
                    throw new IllegalArgumentException("Counts cannot be negative.");
                }
                total += count;
            }
            if (total != shots) {
                throw new IllegalArgumentException(
                        "Outcome counts must equal the shot count.");
            }

            for (Map.Entry<String, Integer> entry : counts.entrySet()) {
                frequencies.put(entry.getKey(),
                        entry.getValue() / (double) shots);
            }
            this.observed = Collections.unmodifiableMap(frequencies);
        }

        double standardError(String outcome) {
            double p = observed.get(outcome);
            return Math.sqrt(p * (1.0 - p) / shots);
        }

        double totalVariationDistance() {
            double distance = 0.0;
            for (String outcome : expected.keySet()) {
                distance += Math.abs(
                        observed.get(outcome) - expected.get(outcome));
            }
            return distance / 2.0;
        }

        void print() {
            System.out.printf(
                    "%nRun %s | %s | status=%s | shots=%d%n",
                    runId, experimentName, status, shots);
            System.out.printf(
                    "%-10s %12s %10s %12s %13s%n",
                    "Outcome", "Expected", "Count", "Observed", "Std. error");

            for (String outcome : expected.keySet()) {
                System.out.printf(
                        "%-10s %12.4f %10d %12.4f %13.4f%n",
                        outcome,
                        expected.get(outcome),
                        counts.get(outcome),
                        observed.get(outcome),
                        standardError(outcome));
            }

            System.out.printf(
                    "Total variation distance: %.4f%n",
                    totalVariationDistance());
        }
    }

    static final class MeasurementService {
        MeasurementResult execute(
                PreparedState state,
                MeasurementRequest request) {
            Random random = new Random(request.seed);
            Map<String, Integer> counts = new LinkedHashMap<>();

            for (String outcome : state.probabilities().keySet()) {
                counts.put(outcome, 0);
            }

            for (int shot = 0; shot < request.shots; shot++) {
                double draw = random.nextDouble();
                double cumulative = 0.0;
                String selected = null;

                for (Map.Entry<String, Double> entry
                        : state.probabilities().entrySet()) {
                    cumulative += entry.getValue();
                    if (draw < cumulative) {
                        selected = entry.getKey();
                        break;
                    }
                }

                // The final entry is a rounding-safe fallback.
                if (selected == null) {
                    selected = state.probabilities().keySet()
                            .stream()
                            .reduce((first, second) -> second)
                            .orElseThrow();
                }
                counts.compute(selected, (key, value) -> value + 1);
            }

            return new MeasurementResult(
                    request.experimentName,
                    request.shots,
                    counts,
                    state.probabilities());
        }
    }

    record QualityPolicy(double maximumTotalVariationDistance) {
        QualityPolicy {
            if (!Double.isFinite(maximumTotalVariationDistance)
                    || maximumTotalVariationDistance < 0.0
                    || maximumTotalVariationDistance > 1.0) {
                throw new IllegalArgumentException(
                        "Distance threshold must lie in [0, 1].");
            }
        }

        boolean accepts(MeasurementResult result) {
            return result.totalVariationDistance()
                    <= maximumTotalVariationDistance;
        }
    }

    public static void main(String[] args) {
        MeasurementService service = new MeasurementService();

        PreparedState balancedQubit = new PreparedState(Map.of(
                "0", 0.5,
                "1", 0.5
        ));
        MeasurementRequest calibrationRequest =
                new MeasurementRequest("balanced-qubit-calibration", 4000, 73);
        MeasurementResult calibration =
                service.execute(balancedQubit, calibrationRequest);
        calibration.print();

        // A Bell-state distribution contains only correlated outcomes.
        PreparedState bellState = new PreparedState(Map.of(
                "00", 0.5,
                "11", 0.5
        ));
        MeasurementResult bellResult = service.execute(
                bellState,
                new MeasurementRequest("bell-correlation-check", 3000, 81));
        bellResult.print();

        if (bellResult.counts.get("01") != 0
                || bellResult.counts.get("10") != 0) {
            throw new IllegalStateException(
                    "Impossible Bell-state outcome appeared.");
        }

        QualityPolicy policy = new QualityPolicy(0.04);
        System.out.printf(
                "%nCalibration decision: %s%n",
                policy.accepts(calibration) ? "ACCEPT" : "INVESTIGATE");

        try {
            new PreparedState(Map.of("0", 0.3, "1", 0.3));
            throw new IllegalStateException("Invalid state was accepted.");
        } catch (IllegalArgumentException expected) {
            System.out.println(
                    "State validation rejected an invalid distribution: "
                            + expected.getMessage());
        }

        try {
            new MeasurementRequest("invalid-run", 0, 1);
            throw new IllegalStateException("Zero shots were accepted.");
        } catch (IllegalArgumentException expected) {
            System.out.println(
                    "Request validation rejected zero shots: "
                            + expected.getMessage());
        }
    }
}
