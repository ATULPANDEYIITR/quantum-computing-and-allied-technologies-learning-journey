import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/*
 * Variational Quantum Eigensolver
 * Java 17 enterprise-oriented implementation.
 *
 * Features:
 * - Immutable domain records
 * - Hamiltonian modeling
 * - Quantum circuit abstraction
 * - Parameter-shift differentiation
 * - Measurement simulation
 * - Optimization policy
 * - Experiment lifecycle
 * - Audit history
 * - Report persistence
 */

public class VQEApplication {

    private static final double PI = Math.PI;

    enum Pauli {
        I, X, Y, Z
    }

    enum ExperimentStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    static class VQEException extends RuntimeException {
        VQEException(String message) {
            super(message);
        }

        VQEException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    record PauliTerm(double coefficient, Pauli operator) {
        PauliTerm {
            if (!Double.isFinite(coefficient)) {
                throw new IllegalArgumentException(
                    "Coefficient must be finite."
                );
            }

            Objects.requireNonNull(operator);
        }
    }

    record Complex(double real, double imaginary) {
        double norm() {
            return real * real + imaginary * imaginary;
        }
    }

    record QuantumState(Complex alpha, Complex beta) {
        QuantumState {
            Objects.requireNonNull(alpha);
            Objects.requireNonNull(beta);

            double probability = alpha.norm() + beta.norm();

            if (Math.abs(probability - 1.0) > 1e-8) {
                throw new IllegalArgumentException(
                    "Quantum state must be normalized."
                );
            }
        }
    }

    record OptimizationConfig(
        double learningRate,
        double tolerance,
        int maximumIterations,
        double initialParameter,
        int measurementShots,
        long seed
    ) {
        OptimizationConfig {
            if (!Double.isFinite(learningRate) ||
                learningRate <= 0) {
                throw new IllegalArgumentException(
                    "Learning rate must be positive."
                );
            }

            if (tolerance <= 0 ||
                !Double.isFinite(tolerance)) {
                throw new IllegalArgumentException(
                    "Invalid tolerance."
                );
            }

            if (maximumIterations <= 0 ||
                measurementShots < 0) {
                throw new IllegalArgumentException(
                    "Invalid optimization configuration."
                );
            }
        }
    }

    record IterationResult(
        int iteration,
        double parameter,
        double energy,
        double gradient
    ) {}

    record ExperimentReport(
        UUID experimentId,
        ExperimentStatus status,
        double optimizedParameter,
        double finalEnergy,
        double exactGroundEnergy,
        double absoluteError,
        int iterations,
        int shots
    ) {}

    interface QuantumAnsatz {
        QuantumState prepare(double parameter);
    }

    interface OptimizationPolicy {
        boolean shouldStop(
            double gradient,
            int iteration
        );
    }

    static class RyAnsatz implements QuantumAnsatz {

        @Override
        public QuantumState prepare(double theta) {
            if (!Double.isFinite(theta)) {
                throw new VQEException(
                    "Invalid circuit parameter."
                );
            }

            return new QuantumState(
                new Complex(Math.cos(theta / 2), 0),
                new Complex(Math.sin(theta / 2), 0)
            );
        }
    }

    static class GradientConvergencePolicy
        implements OptimizationPolicy {

        private final double tolerance;

        GradientConvergencePolicy(double tolerance) {
            this.tolerance = tolerance;
        }

        @Override
        public boolean shouldStop(
            double gradient,
            int iteration
        ) {
            return Math.abs(gradient) < tolerance;
        }
    }

    static class Hamiltonian {
        private final List<PauliTerm> terms;

        Hamiltonian(List<PauliTerm> terms) {
            if (terms == null || terms.isEmpty()) {
                throw new IllegalArgumentException(
                    "Hamiltonian requires terms."
                );
            }

            this.terms = List.copyOf(terms);
        }

        List<PauliTerm> terms() {
            return terms;
        }

        double expectation(QuantumState state) {
            double energy = 0;

            for (PauliTerm term : terms) {
                energy += term.coefficient() *
                    PauliMeasurement.expectation(
                        state,
                        term.operator()
                    );
            }

            return energy;
        }

        double exactGroundEnergy() {
            Map<Pauli, Double> coefficients =
                new EnumMap<>(Pauli.class);

            for (Pauli p : Pauli.values()) {
                coefficients.put(p, 0.0);
            }

            for (PauliTerm term : terms) {
                coefficients.merge(
                    term.operator(),
                    term.coefficient(),
                    Double::sum
                );
            }

            double x = coefficients.get(Pauli.X);
            double y = coefficients.get(Pauli.Y);
            double z = coefficients.get(Pauli.Z);
            double identity = coefficients.get(Pauli.I);

            return identity - Math.sqrt(
                x * x + y * y + z * z
            );
        }
    }

    static class PauliMeasurement {

        static double expectation(
            QuantumState state,
            Pauli observable
        ) {
            double a = state.alpha().real();
            double b = state.beta().real();

            return switch (observable) {
                case I -> 1.0;
                case X -> 2.0 * (
                    a * b +
                    state.alpha().imaginary() *
                    state.beta().imaginary()
                );
                case Y -> 2.0 * (
                    state.alpha().imaginary() * b -
                    a * state.beta().imaginary()
                );
                case Z -> state.alpha().norm() -
                    state.beta().norm();
            };
        }
    }

    static class ShotMeasurementService {

        private final java.util.Random random;

        ShotMeasurementService(long seed) {
            random = new java.util.Random(seed);
        }

        double measure(double expectation, int shots) {
            if (shots <= 0) {
                throw new IllegalArgumentException(
                    "Shot count must be positive."
                );
            }

            if (expectation < -1 || expectation > 1) {
                throw new IllegalArgumentException(
                    "Invalid observable expectation."
                );
            }

            double probability = (1 + expectation) / 2;
            int positive = 0;

            for (int i = 0; i < shots; i++) {
                if (random.nextDouble() < probability) {
                    positive++;
                }
            }

            return 2.0 * positive / shots - 1.0;
        }
    }

    static class ExperimentAudit {

        private final List<IterationResult> records =
            new ArrayList<>();

        void record(IterationResult result) {
            records.add(result);
        }

        List<IterationResult> records() {
            return List.copyOf(records);
        }

        int size() {
            return records.size();
        }
    }

    static class VQEService {

        private final UUID experimentId = UUID.randomUUID();
        private final Hamiltonian hamiltonian;
        private final OptimizationConfig config;
        private final QuantumAnsatz ansatz;
        private final OptimizationPolicy policy;
        private final ShotMeasurementService measurement;
        private final ExperimentAudit audit;

        private ExperimentStatus status =
            ExperimentStatus.CREATED;

        VQEService(
            Hamiltonian hamiltonian,
            OptimizationConfig config
        ) {
            this.hamiltonian = Objects.requireNonNull(
                hamiltonian
            );

            this.config = Objects.requireNonNull(config);
            this.ansatz = new RyAnsatz();

            this.policy = new GradientConvergencePolicy(
                config.tolerance()
            );

            this.measurement = new ShotMeasurementService(
                config.seed()
            );

            this.audit = new ExperimentAudit();
        }

        private double energy(double parameter, boolean noisy) {
            QuantumState state = ansatz.prepare(parameter);

            if (!noisy || config.measurementShots() == 0) {
                return hamiltonian.expectation(state);
            }

            double result = 0;

            for (PauliTerm term : hamiltonian.terms()) {
                double expected =
                    PauliMeasurement.expectation(
                        state,
                        term.operator()
                    );

                result += term.coefficient() *
                    measurement.measure(
                        expected,
                        config.measurementShots()
                    );
            }

            return result;
        }

        private double gradient(double parameter) {
            double shift = PI / 2;

            return (
                energy(parameter + shift, false) -
                energy(parameter - shift, false)
            ) / 2;
        }

        ExperimentReport execute() {
            if (status != ExperimentStatus.CREATED) {
                throw new VQEException(
                    "Experiment has already been started."
                );
            }

            status = ExperimentStatus.RUNNING;

            double parameter = config.initialParameter();

            try {
                for (
                    int iteration = 0;
                    iteration < config.maximumIterations();
                    iteration++
                ) {
                    double currentEnergy = energy(
                        parameter,
                        config.measurementShots() > 0
                    );

                    double derivative = gradient(parameter);

                    audit.record(new IterationResult(
                        iteration,
                        parameter,
                        currentEnergy,
                        derivative
                    ));

                    if (policy.shouldStop(
                        derivative,
                        iteration
                    )) {
                        break;
                    }

                    parameter -=
                        config.learningRate() * derivative;

                    parameter = Math.atan2(
                        Math.sin(parameter),
                        Math.cos(parameter)
                    );
                }

                status = ExperimentStatus.COMPLETED;

                double finalEnergy = energy(parameter, false);
                double exactEnergy =
                    hamiltonian.exactGroundEnergy();

                return new ExperimentReport(
                    experimentId,
                    status,
                    parameter,
                    finalEnergy,
                    exactEnergy,
                    Math.abs(finalEnergy - exactEnergy),
                    audit.size(),
                    config.measurementShots()
                );

            } catch (RuntimeException error) {
                status = ExperimentStatus.FAILED;

                throw new VQEException(
                    "Experiment failed: " + error.getMessage(),
                    error
                );
            }
        }

        ExperimentAudit audit() {
            return audit;
        }
    }

    static class ReportRepository {

        static void save(
            ExperimentReport report,
            ExperimentAudit audit,
            Path destination
        ) {
            StringBuilder content = new StringBuilder();

            content.append("VQE EXPERIMENT REPORT\n");
            content.append("=====================\n");
            content.append("Experiment ID: ")
                .append(report.experimentId()).append('\n');

            content.append("Status: ")
                .append(report.status()).append('\n');

            content.append("Optimized parameter: ")
                .append(report.optimizedParameter()).append('\n');

            content.append("Final energy: ")
                .append(report.finalEnergy()).append('\n');

            content.append("Exact ground energy: ")
                .append(report.exactGroundEnergy()).append('\n');

            content.append("Absolute error: ")
                .append(report.absoluteError()).append('\n');

            content.append("Iterations: ")
                .append(report.iterations()).append('\n');

            content.append("Shots: ")
                .append(report.shots()).append('\n');

            content.append("\nITERATION HISTORY\n");

            for (IterationResult record : audit.records()) {
                content.append(record.iteration())
                    .append(',')
                    .append(record.parameter())
                    .append(',')
                    .append(record.energy())
                    .append(',')
                    .append(record.gradient())
                    .append('\n');
            }

            Path temporary = destination.resolveSibling(
                destination.getFileName() + ".tmp"
            );

            try {
                Files.writeString(
                    temporary,
                    content,
                    StandardOpenOption.CREATE_NEW,
                    StandardOpenOption.WRITE
                );

                try {
                    Files.move(
                        temporary,
                        destination,
                        java.nio.file.StandardCopyOption.ATOMIC_MOVE
                    );
                } catch (java.nio.file.AtomicMoveNotSupportedException e) {
                    Files.move(temporary, destination);
                }

            } catch (IOException error) {
                try {
                    Files.deleteIfExists(temporary);
                } catch (IOException ignored) {
                    // Preserve the original persistence exception.
                }

                throw new VQEException(
                    "Could not persist experiment report.",
                    error
                );
            }
        }
    }

    static void runTests() {
        RyAnsatz ansatz = new RyAnsatz();

        QuantumState state = ansatz.prepare(PI / 2);

        if (Math.abs(
            PauliMeasurement.expectation(state, Pauli.X) - 1
        ) > 1e-9) {
            throw new AssertionError("X measurement test failed.");
        }

        Hamiltonian hamiltonian = new Hamiltonian(
            List.of(
                new PauliTerm(-1.0, Pauli.Z),
                new PauliTerm(-0.5, Pauli.X)
            )
        );

        if (Math.abs(
            hamiltonian.exactGroundEnergy() +
            Math.sqrt(1.25)
        ) > 1e-9) {
            throw new AssertionError("Ground energy test failed.");
        }
    }

    public static void main(String[] args) {
        try {
            runTests();

            Hamiltonian hamiltonian = new Hamiltonian(
                List.of(
                    new PauliTerm(-1.0, Pauli.Z),
                    new PauliTerm(-0.5, Pauli.X)
                )
            );

            OptimizationConfig config =
                new OptimizationConfig(
                    0.15,
                    1e-10,
                    300,
                    0.5,
                    0,
                    42
                );

            VQEService service = new VQEService(
                hamiltonian,
                config
            );

            ExperimentReport report = service.execute();

            System.out.println("VARIATIONAL QUANTUM EIGENSOLVER");
            System.out.println("===============================");
            System.out.println(report);

            ReportRepository.save(
                report,
                service.audit(),
                Path.of("vqe_report.txt")
            );

            System.out.println("Report saved to vqe_report.txt");

        } catch (Exception error) {
            System.err.println(
                "VQE execution failed: " + error.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
