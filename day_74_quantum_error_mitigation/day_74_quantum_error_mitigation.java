import java.util.*;
import java.util.stream.Collectors;

/*
 * Quantum Error Mitigation Enterprise Experiment Service.
 *
 * Java 17 implementation featuring:
 * - Immutable quantum domain records.
 * - Noise channel abstraction.
 * - Measurement sampling.
 * - Readout calibration.
 * - Zero-noise extrapolation.
 * - Experiment lifecycle management.
 * - Governance policies.
 * - Approval-based publication of experimental results.
 *
 * Compile: javac QuantumErrorMitigation.java
 * Run: java QuantumErrorMitigation
 */

public class QuantumErrorMitigation {

    enum NoiseType {
        BIT_FLIP,
        PHASE_FLIP,
        DEPOLARIZING
    }

    enum MitigationType {
        RAW,
        READOUT_CALIBRATION,
        ZERO_NOISE_EXTRAPOLATION
    }

    enum ExperimentStatus {
        CREATED,
        VALIDATING,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum Decision {
        ACCEPTED,
        REJECTED
    }

    static class QEMException extends RuntimeException {
        QEMException(String message) {
            super(message);
        }
    }

    static class ValidationException extends QEMException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class StateTransitionException extends QEMException {
        StateTransitionException(String message) {
            super(message);
        }
    }

    static void validateProbability(double value, String name) {
        if (!Double.isFinite(value) || value < 0 || value > 1) {
            throw new ValidationException(
                name + " must be between zero and one"
            );
        }
    }

    static void validatePositive(int value, String name) {
        if (value <= 0) {
            throw new ValidationException(
                name + " must be positive"
            );
        }
    }

    record QubitState(double probabilityZero, double probabilityOne) {
        QubitState {
            validateProbability(probabilityZero, "Probability zero");
            validateProbability(probabilityOne, "Probability one");

            if (Math.abs(probabilityZero + probabilityOne - 1) > 1e-9) {
                throw new ValidationException("State is not normalized");
            }
        }

        double expectationZ() {
            return probabilityZero - probabilityOne;
        }

        static QubitState zero() {
            return new QubitState(1, 0);
        }

        static QubitState plus() {
            return new QubitState(0.5, 0.5);
        }
    }

    interface QuantumChannel {
        double apply(double expectation, double scale);
        NoiseType type();
        double rate();
    }

    record NoiseModel(NoiseType type, double rate)
        implements QuantumChannel {

        NoiseModel {
            Objects.requireNonNull(type);
            validateProbability(rate, "Noise rate");
        }

        @Override
        public double apply(double expectation, double scale) {
            if (!Double.isFinite(scale) || scale <= 0) {
                throw new ValidationException("Invalid noise scale");
            }

            double p = rate * scale;

            if (p > 1) {
                throw new ValidationException("Scaled noise exceeds one");
            }

            return switch (type) {
                case BIT_FLIP -> expectation * (1 - 2 * p);
                case PHASE_FLIP -> expectation;
                case DEPOLARIZING -> expectation * (1 - 4 * p / 3);
            };
        }
    }

    record MeasurementResult(
        double estimate,
        double uncertainty,
        int shots,
        int positiveCount
    ) {}

    static class MeasurementService {
        private final Random random;

        MeasurementService(long seed) {
            this.random = new Random(seed);
        }

        MeasurementResult measure(
            double expectation,
            int shots,
            double readoutError
        ) {
            validatePositive(shots, "Shots");
            validateProbability(readoutError, "Readout error");

            double observed =
                expectation * (1 - 2 * readoutError);

            double pPlus = (1 + observed) / 2;
            int positive = 0;

            for (int i = 0; i < shots; i++) {
                if (random.nextDouble() < pPlus) {
                    positive++;
                }
            }

            double estimate = 2.0 * positive / shots - 1.0;

            double uncertainty = Math.sqrt(
                Math.max(0, 1 - estimate * estimate) / shots
            );

            return new MeasurementResult(
                estimate,
                uncertainty,
                shots,
                positive
            );
        }
    }

    record CalibrationMatrix(
        double error01,
        double error10
    ) {
        CalibrationMatrix {
            validateProbability(error01, "Error 01");
            validateProbability(error10, "Error 10");

            if (Math.abs(1 - error01 - error10) < 1e-12) {
                throw new ValidationException(
                    "Calibration matrix is singular"
                );
            }
        }

        double correctProbabilityOne(double observed) {
            validateProbability(observed, "Observed probability");

            double corrected =
                (observed - error01) /
                (1 - error01 - error10);

            return Math.max(0, Math.min(1, corrected));
        }

        double correctExpectation(double observedExpectation) {
            double p1 = (1 - observedExpectation) / 2;

            return 1 - 2 * correctProbabilityOne(p1);
        }
    }

    record NoiseObservation(double scale, double value) {
        NoiseObservation {
            if (!Double.isFinite(scale) || scale <= 0) {
                throw new ValidationException("Invalid scale");
            }

            if (!Double.isFinite(value)) {
                throw new ValidationException("Invalid observation");
            }
        }
    }

    static class ExtrapolationService {

        double extrapolate(List<NoiseObservation> observations) {
            if (observations.size() < 2) {
                throw new ValidationException(
                    "Two observations are required"
                );
            }

            List<NoiseObservation> sorted = observations.stream()
                .sorted(Comparator.comparingDouble(
                    NoiseObservation::scale
                ))
                .toList();

            NoiseObservation first = sorted.get(0);
            NoiseObservation second = sorted.get(1);

            double difference = second.scale() - first.scale();

            if (Math.abs(difference) < 1e-12) {
                throw new ValidationException(
                    "Noise scales must differ"
                );
            }

            return first.value() -
                first.scale() *
                (second.value() - first.value()) / difference;
        }
    }

    record Experiment(
        String id,
        String owner,
        QubitState state,
        QuantumChannel channel,
        int shots,
        double readoutError
    ) {
        Experiment {
            if (id == null || id.isBlank()) {
                throw new ValidationException("Experiment ID required");
            }

            if (owner == null || owner.isBlank()) {
                throw new ValidationException("Experiment owner required");
            }

            Objects.requireNonNull(state);
            Objects.requireNonNull(channel);

            validatePositive(shots, "Shots");
            validateProbability(readoutError, "Readout error");
        }
    }

    record ResultRecord(
        String experimentId,
        MitigationType method,
        double estimate,
        double uncertainty,
        double bias,
        int shots
    ) {
        ResultRecord {
            if (!Double.isFinite(estimate)) {
                throw new ValidationException("Invalid estimate");
            }

            if (!Double.isFinite(uncertainty) || uncertainty < 0) {
                throw new ValidationException("Invalid uncertainty");
            }

            if (shots <= 0) {
                throw new ValidationException("Invalid shot count");
            }
        }
    }

    record GovernancePolicy(
        double maximumNoise,
        int minimumShots,
        double maximumUncertainty,
        Set<MitigationType> permittedMethods
    ) {
        GovernancePolicy {
            validateProbability(maximumNoise, "Maximum noise");
            validatePositive(minimumShots, "Minimum shots");

            if (
                !Double.isFinite(maximumUncertainty) ||
                maximumUncertainty <= 0
            ) {
                throw new ValidationException(
                    "Invalid uncertainty threshold"
                );
            }

            permittedMethods = Set.copyOf(permittedMethods);

            if (permittedMethods.isEmpty()) {
                throw new ValidationException(
                    "At least one method must be permitted"
                );
            }
        }
    }

    record PolicyDecision(
        Decision decision,
        List<String> violations
    ) {}

    static class GovernanceService {

        PolicyDecision evaluate(
            Experiment experiment,
            ResultRecord result,
            GovernancePolicy policy
        ) {
            List<String> violations = new ArrayList<>();

            if (experiment.channel().rate() > policy.maximumNoise()) {
                violations.add("Noise threshold exceeded");
            }

            if (result.shots() < policy.minimumShots()) {
                violations.add("Insufficient measurement budget");
            }

            if (
                result.uncertainty() >
                policy.maximumUncertainty()
            ) {
                violations.add("Uncertainty threshold exceeded");
            }

            if (!policy.permittedMethods().contains(result.method())) {
                violations.add("Method not authorized");
            }

            return new PolicyDecision(
                violations.isEmpty()
                    ? Decision.ACCEPTED
                    : Decision.REJECTED,
                List.copyOf(violations)
            );
        }
    }

    static class ExperimentService {

        private ExperimentStatus status = ExperimentStatus.CREATED;

        private final MeasurementService measurementService;
        private final ExtrapolationService extrapolationService;

        ExperimentService(long seed) {
            measurementService = new MeasurementService(seed);
            extrapolationService = new ExtrapolationService();
        }

        private void transition(ExperimentStatus next) {
            Map<ExperimentStatus, Set<ExperimentStatus>> transitions =
                Map.of(
                    ExperimentStatus.CREATED,
                    Set.of(ExperimentStatus.VALIDATING),
                    ExperimentStatus.VALIDATING,
                    Set.of(
                        ExperimentStatus.RUNNING,
                        ExperimentStatus.FAILED
                    ),
                    ExperimentStatus.RUNNING,
                    Set.of(
                        ExperimentStatus.COMPLETED,
                        ExperimentStatus.FAILED
                    ),
                    ExperimentStatus.COMPLETED,
                    Set.of(),
                    ExperimentStatus.FAILED,
                    Set.of()
                );

            if (!transitions.get(status).contains(next)) {
                throw new StateTransitionException(
                    "Invalid transition: " + status + " -> " + next
                );
            }

            status = next;
        }

        List<ResultRecord> execute(Experiment experiment) {
            transition(ExperimentStatus.VALIDATING);

            try {
                transition(ExperimentStatus.RUNNING);

                double ideal = experiment.state().expectationZ();

                double noisy = experiment.channel().apply(ideal, 1);

                MeasurementResult raw = measurementService.measure(
                    noisy,
                    experiment.shots(),
                    experiment.readoutError()
                );

                List<ResultRecord> results = new ArrayList<>();

                results.add(new ResultRecord(
                    experiment.id(),
                    MitigationType.RAW,
                    raw.estimate(),
                    raw.uncertainty(),
                    raw.estimate() - ideal,
                    raw.shots()
                ));

                CalibrationMatrix calibration =
                    new CalibrationMatrix(
                        experiment.readoutError(),
                        experiment.readoutError()
                    );

                double corrected = calibration.correctExpectation(
                    raw.estimate()
                );

                double correctedUncertainty =
                    raw.uncertainty() /
                    Math.abs(1 - 2 * experiment.readoutError());

                results.add(new ResultRecord(
                    experiment.id(),
                    MitigationType.READOUT_CALIBRATION,
                    corrected,
                    correctedUncertainty,
                    corrected - ideal,
                    experiment.shots()
                ));

                List<NoiseObservation> observations =
                    List.of(1.0, 1.5, 2.0)
                        .stream()
                        .map(scale -> new NoiseObservation(
                            scale,
                            experiment.channel().apply(ideal, scale)
                        ))
                        .toList();

                double zne =
                    extrapolationService.extrapolate(observations);

                results.add(new ResultRecord(
                    experiment.id(),
                    MitigationType.ZERO_NOISE_EXTRAPOLATION,
                    zne,
                    raw.uncertainty() * 1.5,
                    zne - ideal,
                    experiment.shots() * 3
                ));

                transition(ExperimentStatus.COMPLETED);

                return List.copyOf(results);

            } catch (RuntimeException error) {
                transition(ExperimentStatus.FAILED);
                throw error;
            }
        }

        ExperimentStatus status() {
            return status;
        }
    }

    static void printReport(
        Experiment experiment,
        List<ResultRecord> results,
        GovernancePolicy policy
    ) {
        GovernanceService governance = new GovernanceService();

        System.out.println("\nENTERPRISE QUANTUM EXPERIMENT REPORT");
        System.out.println(
            "Experiment: " + experiment.id()
        );

        System.out.printf(
            "%-30s %12s %12s %12s %-12s%n",
            "Mitigation method",
            "Estimate",
            "Uncertainty",
            "Bias",
            "Decision"
        );

        for (ResultRecord result : results) {
            PolicyDecision decision = governance.evaluate(
                experiment,
                result,
                policy
            );

            System.out.printf(
                "%-30s %12.6f %12.6f %12.6f %-12s%n",
                result.method(),
                result.estimate(),
                result.uncertainty(),
                result.bias(),
                decision.decision()
            );

            decision.violations().forEach(
                violation -> System.out.println("  - " + violation)
            );
        }
    }

    public static void main(String[] args) {
        try {
            Experiment experiment = new Experiment(
                "QEM-2026-001",
                "quantum-research-team",
                QubitState.zero(),
                new NoiseModel(NoiseType.BIT_FLIP, 0.08),
                30000,
                0.04
            );

            GovernancePolicy policy = new GovernancePolicy(
                0.20,
                1000,
                0.10,
                EnumSet.of(
                    MitigationType.RAW,
                    MitigationType.READOUT_CALIBRATION,
                    MitigationType.ZERO_NOISE_EXTRAPOLATION
                )
            );

            ExperimentService service = new ExperimentService(42);

            List<ResultRecord> results = service.execute(experiment);

            printReport(experiment, results, policy);

            System.out.println(
                "\nExperiment lifecycle: " + service.status()
            );

            try {
                new CalibrationMatrix(0.5, 0.5);
                throw new QEMException(
                    "Expected singular calibration rejection"
                );
            } catch (ValidationException expected) {
                System.out.println(
                    "Calibration validation: " + expected.getMessage()
                );
            }

        } catch (QEMException error) {
            System.err.println(
                "Experiment failed: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
