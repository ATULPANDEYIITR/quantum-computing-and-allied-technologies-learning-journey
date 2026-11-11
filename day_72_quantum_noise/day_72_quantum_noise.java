import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Quantum Noise Characterization and Governance.
 *
 * Enterprise-oriented implementation of:
 * - Noise channel registration
 * - Calibration management
 * - Amplitude damping
 * - Pure dephasing
 * - Depolarizing errors
 * - Bit and phase flips
 * - Coherent errors
 * - Thermal relaxation
 * - Measurement calibration
 * - Experiment validation and reporting
 *
 * Runtime: Java 17
 * Dependencies: Java standard library only.
 */

public class QuantumNoiseEnterprise {

    private static final double EPSILON = 1e-10;

    enum NoiseType {
        AMPLITUDE_DAMPING,
        PURE_DEPHASING,
        DEPOLARIZING,
        BIT_FLIP,
        PHASE_FLIP,
        COHERENT_Z,
        THERMAL_RELAXATION
    }

    enum ExperimentStatus {
        CREATED,
        VALIDATED,
        EXECUTED,
        FAILED
    }

    record BlochVector(double x, double y, double z) {

        BlochVector {
            if (
                !Double.isFinite(x) ||
                !Double.isFinite(y) ||
                !Double.isFinite(z)
            ) {
                throw new IllegalArgumentException(
                    "Bloch coordinates must be finite"
                );
            }

            if (magnitude(x, y, z) > 1.0 + EPSILON) {
                throw new IllegalArgumentException(
                    "State lies outside the physical Bloch sphere"
                );
            }
        }

        private static double magnitude(
            double x,
            double y,
            double z
        ) {
            return Math.sqrt(x * x + y * y + z * z);
        }

        double purity() {
            return (1.0 + x * x + y * y + z * z) / 2.0;
        }

        double fidelity(BlochVector target) {
            Objects.requireNonNull(target);

            double dot =
                x * target.x +
                y * target.y +
                z * target.z;

            return Math.max(
                0.0,
                Math.min(1.0, (1.0 + dot) / 2.0)
            );
        }
    }

    record NoiseParameters(
        double probability,
        double gamma,
        double angle,
        double excitedPopulation
    ) {

        NoiseParameters {
            checkProbability(probability, "probability");
            checkProbability(gamma, "gamma");
            checkProbability(
                excitedPopulation,
                "excitedPopulation"
            );

            if (!Double.isFinite(angle)) {
                throw new IllegalArgumentException(
                    "Angle must be finite"
                );
            }
        }
    }

    record CoherenceCalibration(
        double t1,
        double t2
    ) {

        CoherenceCalibration {
            if (
                !Double.isFinite(t1) ||
                !Double.isFinite(t2) ||
                t1 <= 0 ||
                t2 <= 0 ||
                t2 > 2 * t1
            ) {
                throw new IllegalArgumentException(
                    "Required physical relationship: 0 < T2 <= 2*T1"
                );
            }
        }

        double relaxationProbability(double duration) {
            validateDuration(duration);
            return 1.0 - Math.exp(-duration / t1);
        }

        double dephasingProbability(double duration) {
            validateDuration(duration);

            double inverseTphi = Math.max(
                0.0,
                1.0 / t2 - 1.0 / (2.0 * t1)
            );

            return (
                1.0 - Math.exp(-duration * inverseTphi)
            ) / 2.0;
        }
    }

    record ChannelResult(
        String channelId,
        NoiseType noiseType,
        BlochVector output,
        double purity
    ) {}

    record ExperimentReport(
        String experimentId,
        ExperimentStatus status,
        BlochVector initialState,
        BlochVector finalState,
        double fidelity,
        List<ChannelResult> channelResults
    ) {
        ExperimentReport {
            channelResults = List.copyOf(channelResults);
        }
    }

    interface QuantumChannel {
        String id();

        NoiseType type();

        BlochVector apply(BlochVector state);
    }

    private static void checkProbability(
        double value,
        String name
    ) {
        if (
            !Double.isFinite(value) ||
            value < 0.0 ||
            value > 1.0
        ) {
            throw new IllegalArgumentException(
                name + " must be in [0, 1]"
            );
        }
    }

    private static void validateDuration(double duration) {
        if (!Double.isFinite(duration) || duration < 0) {
            throw new IllegalArgumentException(
                "Duration must be nonnegative"
            );
        }
    }

    static final class StandardNoiseChannel
            implements QuantumChannel {

        private final String id;
        private final NoiseType type;
        private final NoiseParameters parameters;

        StandardNoiseChannel(
            String id,
            NoiseType type,
            NoiseParameters parameters
        ) {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException(
                    "Channel ID is required"
                );
            }

            this.id = id;
            this.type = Objects.requireNonNull(type);
            this.parameters = Objects.requireNonNull(parameters);

            if (
                type == NoiseType.PURE_DEPHASING &&
                parameters.probability() > 0.5
            ) {
                throw new IllegalArgumentException(
                    "Pure dephasing probability cannot exceed 0.5"
                );
            }
        }

        @Override
        public String id() {
            return id;
        }

        @Override
        public NoiseType type() {
            return type;
        }

        @Override
        public BlochVector apply(BlochVector input) {
            double x = input.x();
            double y = input.y();
            double z = input.z();

            double p = parameters.probability();
            double g = parameters.gamma();

            return switch (type) {

                case AMPLITUDE_DAMPING -> {
                    double scale = Math.sqrt(1 - g);

                    yield new BlochVector(
                        scale * x,
                        scale * y,
                        g + (1 - g) * z
                    );
                }

                case PURE_DEPHASING -> {
                    double scale = 1 - 2 * p;

                    yield new BlochVector(
                        scale * x,
                        scale * y,
                        z
                    );
                }

                case DEPOLARIZING -> {
                    double scale = 1 - 4 * p / 3;

                    yield new BlochVector(
                        scale * x,
                        scale * y,
                        scale * z
                    );
                }

                case BIT_FLIP -> {
                    double scale = 1 - 2 * p;

                    yield new BlochVector(
                        x,
                        scale * y,
                        scale * z
                    );
                }

                case PHASE_FLIP -> {
                    double scale = 1 - 2 * p;

                    yield new BlochVector(
                        scale * x,
                        scale * y,
                        z
                    );
                }

                case COHERENT_Z -> {
                    double angle = parameters.angle();
                    double c = Math.cos(angle);
                    double s = Math.sin(angle);

                    yield new BlochVector(
                        c * x - s * y,
                        s * x + c * y,
                        z
                    );
                }

                case THERMAL_RELAXATION -> {
                    double q = parameters.excitedPopulation();
                    double scale = Math.sqrt(1 - g);
                    double equilibriumZ = 1 - 2 * q;

                    yield new BlochVector(
                        scale * x,
                        scale * y,
                        g * equilibriumZ + (1 - g) * z
                    );
                }
            };
        }
    }

    static final class NoiseExperiment {

        private final String experimentId;
        private final BlochVector initialState;
        private final BlochVector targetState;
        private final Map<String, QuantumChannel> channels =
            new LinkedHashMap<>();

        private ExperimentStatus status = ExperimentStatus.CREATED;

        NoiseExperiment(
            String experimentId,
            BlochVector initialState,
            BlochVector targetState
        ) {
            if (
                experimentId == null ||
                experimentId.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Experiment ID is required"
                );
            }

            this.experimentId = experimentId;
            this.initialState = Objects.requireNonNull(initialState);
            this.targetState = Objects.requireNonNull(targetState);
        }

        void registerChannel(QuantumChannel channel) {
            if (status != ExperimentStatus.CREATED) {
                throw new IllegalStateException(
                    "Channels cannot change after validation"
                );
            }

            Objects.requireNonNull(channel);

            if (channels.containsKey(channel.id())) {
                throw new IllegalArgumentException(
                    "Duplicate channel ID: " + channel.id()
                );
            }

            channels.put(channel.id(), channel);
        }

        void validate() {
            if (channels.isEmpty()) {
                throw new IllegalStateException(
                    "Experiment requires at least one channel"
                );
            }

            status = ExperimentStatus.VALIDATED;
        }

        ExperimentReport execute() {
            if (status != ExperimentStatus.VALIDATED) {
                throw new IllegalStateException(
                    "Experiment must be validated before execution"
                );
            }

            try {
                BlochVector state = initialState;
                List<ChannelResult> results = new ArrayList<>();

                for (QuantumChannel channel : channels.values()) {
                    state = channel.apply(state);

                    results.add(new ChannelResult(
                        channel.id(),
                        channel.type(),
                        state,
                        state.purity()
                    ));
                }

                status = ExperimentStatus.EXECUTED;

                return new ExperimentReport(
                    experimentId,
                    status,
                    initialState,
                    state,
                    state.fidelity(targetState),
                    results
                );

            } catch (RuntimeException exception) {
                status = ExperimentStatus.FAILED;
                throw exception;
            }
        }

        ExperimentStatus status() {
            return status;
        }
    }

    record ReadoutCalibration(
        double probabilityZeroReportedAsOne,
        double probabilityOneReportedAsZero
    ) {
        ReadoutCalibration {
            checkProbability(
                probabilityZeroReportedAsOne,
                "p01"
            );

            checkProbability(
                probabilityOneReportedAsZero,
                "p10"
            );
        }

        Map<String, Double> evaluate(BlochVector state) {
            double p0 = (1 + state.z()) / 2;
            double p1 = (1 - state.z()) / 2;

            double reportedZero =
                p0 * (1 - probabilityZeroReportedAsOne)
                + p1 * probabilityOneReportedAsZero;

            double reportedOne =
                p0 * probabilityZeroReportedAsOne
                + p1 * (1 - probabilityOneReportedAsZero);

            Map<String, Double> result = new LinkedHashMap<>();

            result.put("reported_zero", reportedZero);
            result.put("reported_one", reportedOne);

            return Collections.unmodifiableMap(result);
        }
    }

    static void printReport(ExperimentReport report) {
        System.out.println("\nEXPERIMENT: " + report.experimentId());
        System.out.println("Status: " + report.status());

        System.out.printf(
            "Initial state: (%.6f, %.6f, %.6f)%n",
            report.initialState().x(),
            report.initialState().y(),
            report.initialState().z()
        );

        System.out.printf(
            "Final state: (%.6f, %.6f, %.6f)%n",
            report.finalState().x(),
            report.finalState().y(),
            report.finalState().z()
        );

        System.out.printf(
            "Fidelity: %.6f%n",
            report.fidelity()
        );

        System.out.println("Channel execution:");

        for (ChannelResult result : report.channelResults()) {
            System.out.printf(
                "  %s | %s | Purity: %.6f%n",
                result.channelId(),
                result.noiseType(),
                result.purity()
            );
        }
    }

    public static void main(String[] args) {
        try {
            BlochVector initial = new BlochVector(1, 0, 0);
            BlochVector target = new BlochVector(1, 0, 0);

            CoherenceCalibration calibration =
                new CoherenceCalibration(
                    100e-6,
                    70e-6
                );

            double duration = 20e-6;

            double gamma =
                calibration.relaxationProbability(duration);

            double phase =
                calibration.dephasingProbability(duration);

            NoiseExperiment experiment = new NoiseExperiment(
                "QPU-CHARACTERIZATION-001",
                initial,
                target
            );

            experiment.registerChannel(
                new StandardNoiseChannel(
                    "relaxation-001",
                    NoiseType.AMPLITUDE_DAMPING,
                    new NoiseParameters(0, 0.15, 0, 0)
                )
            );

            experiment.registerChannel(
                new StandardNoiseChannel(
                    "dephasing-001",
                    NoiseType.PURE_DEPHASING,
                    new NoiseParameters(0.10, 0, 0, 0)
                )
            );

            experiment.registerChannel(
                new StandardNoiseChannel(
                    "gate-error-001",
                    NoiseType.COHERENT_Z,
                    new NoiseParameters(0, 0, 0.05, 0)
                )
            );

            experiment.validate();

            ExperimentReport report = experiment.execute();

            printReport(report);

            System.out.println("\nCOHERENCE CALIBRATION");

            System.out.printf("T1: %.3e seconds%n", calibration.t1());
            System.out.printf("T2: %.3e seconds%n", calibration.t2());
            System.out.printf("Gamma: %.6f%n", gamma);
            System.out.printf("Pure dephasing: %.6f%n", phase);

            ReadoutCalibration readout =
                new ReadoutCalibration(0.03, 0.05);

            System.out.println("\nREADOUT CALIBRATION");
            readout.evaluate(report.finalState())
                .forEach((key, value) ->
                    System.out.printf("%s: %.6f%n", key, value)
                );

            System.out.println("\nExperiment completed successfully.");

        } catch (RuntimeException exception) {
            System.err.println(
                "Experiment failed: " + exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
