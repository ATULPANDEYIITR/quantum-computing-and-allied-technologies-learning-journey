import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * Quantum Decoherence Monitoring System.
 *
 * Enterprise-oriented experiment management for:
 * T1 energy relaxation, T2 coherence decay,
 * pure dephasing, environmental conditions,
 * measurements and experiment validation.
 */
public class DecoherenceMonitor {

    enum Environment {
        ISOLATED,
        THERMAL,
        MAGNETIC_NOISE,
        ELECTRIC_NOISE,
        VIBRATIONAL,
        MIXED
    }

    enum ExperimentStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    record Parameters(
        double t1,
        double t2,
        double temperature,
        double equilibriumPopulation,
        Environment environment
    ) {
        Parameters {
            Objects.requireNonNull(environment);

            if (!Double.isFinite(t1) || t1 <= 0) {
                throw new IllegalArgumentException("Invalid T1.");
            }

            if (!Double.isFinite(t2) || t2 <= 0) {
                throw new IllegalArgumentException("Invalid T2.");
            }

            if (t2 > 2 * t1) {
                throw new IllegalArgumentException(
                    "Physical condition T2 <= 2*T1 violated."
                );
            }

            if (!Double.isFinite(temperature) || temperature < 0) {
                throw new IllegalArgumentException("Invalid temperature.");
            }

            if (
                !Double.isFinite(equilibriumPopulation) ||
                equilibriumPopulation < 0 ||
                equilibriumPopulation > 1
            ) {
                throw new IllegalArgumentException(
                    "Invalid equilibrium population."
                );
            }
        }

        double pureDephasingTime() {
            double inverse =
                1.0 / t2 - 1.0 / (2.0 * t1);

            return inverse <= 1e-15
                ? Double.POSITIVE_INFINITY
                : 1.0 / inverse;
        }
    }

    record QuantumState(double x, double y, double z) {

        QuantumState {
            if (
                !Double.isFinite(x) ||
                !Double.isFinite(y) ||
                !Double.isFinite(z)
            ) {
                throw new IllegalArgumentException(
                    "Bloch coordinates must be finite."
                );
            }

            double radiusSquared =
                x * x + y * y + z * z;

            if (radiusSquared > 1.0 + 1e-9) {
                throw new IllegalArgumentException(
                    "State outside Bloch sphere."
                );
            }
        }

        double coherence() {
            return Math.hypot(x, y);
        }

        double purity() {
            return (
                1.0 + x * x + y * y + z * z
            ) / 2.0;
        }

        double excitedProbability() {
            return (1.0 - z) / 2.0;
        }

        double groundProbability() {
            return (1.0 + z) / 2.0;
        }
    }

    record Observation(
        double time,
        QuantumState state,
        double coherence,
        double purity,
        double excitedProbability
    ) {}

    record ExperimentReport(
        String experimentId,
        Environment environment,
        double t1,
        double t2,
        double tPhi,
        int observationCount,
        double finalCoherence,
        double finalPurity,
        ExperimentStatus status
    ) {}

    interface ExperimentPolicy {
        void validate(
            Parameters parameters,
            QuantumState initial,
            double duration,
            int steps
        );
    }

    static class StandardExperimentPolicy
        implements ExperimentPolicy {

        @Override
        public void validate(
            Parameters parameters,
            QuantumState initial,
            double duration,
            int steps
        ) {
            Objects.requireNonNull(parameters);
            Objects.requireNonNull(initial);

            if (!Double.isFinite(duration) || duration < 0) {
                throw new IllegalArgumentException(
                    "Invalid duration."
                );
            }

            if (steps < 1 || steps > 1_000_000) {
                throw new IllegalArgumentException(
                    "Steps must be between 1 and 1000000."
                );
            }
        }
    }

    static class ExperimentException extends Exception {
        ExperimentException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    static class ExperimentService {

        private final Parameters parameters;
        private final ExperimentPolicy policy;

        private ExperimentStatus status =
            ExperimentStatus.CREATED;

        private final List<Observation> observations =
            new ArrayList<>();

        ExperimentService(
            Parameters parameters,
            ExperimentPolicy policy
        ) {
            this.parameters = Objects.requireNonNull(parameters);
            this.policy = Objects.requireNonNull(policy);
        }

        private QuantumState evolve(
            QuantumState initial,
            double time
        ) {
            double transverseDecay =
                Math.exp(-time / parameters.t2());

            double longitudinalDecay =
                Math.exp(-time / parameters.t1());

            double equilibriumZ =
                1.0 - 2.0 * parameters.equilibriumPopulation();

            return new QuantumState(
                initial.x() * transverseDecay,
                initial.y() * transverseDecay,
                equilibriumZ +
                    (initial.z() - equilibriumZ) * longitudinalDecay
            );
        }

        ExperimentReport execute(
            String experimentId,
            QuantumState initial,
            double duration,
            int steps
        ) throws ExperimentException {

            if (status == ExperimentStatus.RUNNING) {
                throw new IllegalStateException(
                    "Experiment already running."
                );
            }

            if (
                status == ExperimentStatus.COMPLETED ||
                status == ExperimentStatus.FAILED
            ) {
                throw new IllegalStateException(
                    "A completed experiment cannot be restarted."
                );
            }

            try {
                policy.validate(
                    parameters,
                    initial,
                    duration,
                    steps
                );

                status = ExperimentStatus.RUNNING;

                for (int i = 0; i <= steps; i++) {
                    double time =
                        duration * i / steps;

                    QuantumState state =
                        evolve(initial, time);

                    observations.add(
                        new Observation(
                            time,
                            state,
                            state.coherence(),
                            state.purity(),
                            state.excitedProbability()
                        )
                    );
                }

                status = ExperimentStatus.COMPLETED;

                Observation last =
                    observations.get(observations.size() - 1);

                return new ExperimentReport(
                    experimentId,
                    parameters.environment(),
                    parameters.t1(),
                    parameters.t2(),
                    parameters.pureDephasingTime(),
                    observations.size(),
                    last.coherence(),
                    last.purity(),
                    status
                );

            } catch (RuntimeException exception) {
                status = ExperimentStatus.FAILED;

                throw new ExperimentException(
                    "Experiment execution failed.",
                    exception
                );
            }
        }

        List<Observation> observations() {
            return List.copyOf(observations);
        }

        ExperimentStatus status() {
            return status;
        }

        double estimateT2() {
            List<Observation> valid =
                observations.stream()
                    .filter(o -> o.coherence() > 1e-12)
                    .toList();

            if (valid.size() < 2) {
                throw new IllegalStateException(
                    "Insufficient observations."
                );
            }

            double meanX = valid.stream()
                .mapToDouble(Observation::time)
                .average()
                .orElseThrow();

            double meanY = valid.stream()
                .mapToDouble(o -> Math.log(o.coherence()))
                .average()
                .orElseThrow();

            double numerator = 0;
            double denominator = 0;

            for (Observation observation : valid) {
                double dx = observation.time() - meanX;
                double dy =
                    Math.log(observation.coherence()) - meanY;

                numerator += dx * dy;
                denominator += dx * dx;
            }

            if (denominator < 1e-12) {
                throw new IllegalStateException(
                    "Regression has no time variance."
                );
            }

            double slope = numerator / denominator;

            if (slope >= 0) {
                throw new IllegalStateException(
                    "No exponential decay detected."
                );
            }

            return -1.0 / slope;
        }

        void exportCSV(Path path) throws IOException {
            if (status != ExperimentStatus.COMPLETED) {
                throw new IllegalStateException(
                    "Only completed experiments can be exported."
                );
            }

            StringBuilder csv = new StringBuilder();

            csv.append(
                "time,x,y,z,coherence,purity,excited_probability\n"
            );

            for (Observation o : observations) {
                QuantumState s = o.state();

                csv.append(String.format(
                    java.util.Locale.ROOT,
                    "%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f%n",
                    o.time(),
                    s.x(),
                    s.y(),
                    s.z(),
                    o.coherence(),
                    o.purity(),
                    o.excitedProbability()
                ));
            }

            Files.writeString(
                path,
                csv.toString(),
                StandardCharsets.UTF_8
            );
        }
    }

    static List<ExperimentReport> compareEnvironments()
        throws ExperimentException {

        List<Parameters> configurations = List.of(
            new Parameters(
                100, 150, 0.020, 0,
                Environment.ISOLATED
            ),
            new Parameters(
                80, 60, 0.050, 0.02,
                Environment.THERMAL
            ),
            new Parameters(
                100, 25, 0.020, 0,
                Environment.MAGNETIC_NOISE
            ),
            new Parameters(
                70, 35, 0.030, 0.01,
                Environment.ELECTRIC_NOISE
            ),
            new Parameters(
                90, 20, 0.040, 0.02,
                Environment.MIXED
            )
        );

        List<ExperimentReport> reports =
            new ArrayList<>();

        for (int i = 0; i < configurations.size(); i++) {
            ExperimentService service =
                new ExperimentService(
                    configurations.get(i),
                    new StandardExperimentPolicy()
                );

            reports.add(
                service.execute(
                    "ENV-" + (i + 1),
                    new QuantumState(1, 0, 0),
                    200,
                    200
                )
            );
        }

        return List.copyOf(reports);
    }

    public static void main(String[] args) {
        try {
            Parameters parameters = new Parameters(
                100,
                60,
                0.020,
                0.01,
                Environment.MIXED
            );

            ExperimentService service =
                new ExperimentService(
                    parameters,
                    new StandardExperimentPolicy()
                );

            ExperimentReport report = service.execute(
                "QUBIT-EXPERIMENT-001",
                new QuantumState(1, 0, 0),
                300,
                300
            );

            System.out.println("QUANTUM DECOHERENCE MONITOR");
            System.out.println("--------------------------------");

            System.out.println(report);

            System.out.printf(
                "Estimated T2: %.6f%n",
                service.estimateT2()
            );

            System.out.println("\nENVIRONMENT COMPARISON");

            compareEnvironments().forEach(
                System.out::println
            );

            service.exportCSV(
                Path.of("decoherence_java_results.csv")
            );

            if (
                Math.abs(service.estimateT2() - 60.0) > 1e-6
            ) {
                throw new IllegalStateException(
                    "T2 estimation failed."
                );
            }

            System.out.println("\nExperiment completed successfully.");

        } catch (Exception exception) {
            System.err.println(
                "SYSTEM ERROR: " + exception.getMessage()
            );

            exception.printStackTrace();
            System.exit(1);
        }
    }
}
