import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Majorana-Based Topological Quantum Computing
 *
 * Java 17 enterprise-oriented simulation.
 *
 * Features:
 * - Majorana operator algebra
 * - Fermion parity and Ising fusion channels
 * - Non-Abelian braid operations
 * - Fixed-parity computational state
 * - Immutable experiment configuration
 * - Policy-based experiment validation
 * - State transitions and audit history
 * - Braid-group and unitarity verification
 *
 * This is a mathematical model, not a physical device simulator.
 */
public class MajoranaQuantumEnterprise {

    private static final double EPSILON = 1e-9;

    enum FusionChannel {
        VACUUM("1"),
        FERMION("psi");

        private final String symbol;

        FusionChannel(String symbol) {
            this.symbol = symbol;
        }

        public String symbol() {
            return symbol;
        }
    }

    enum ExperimentStatus {
        CREATED,
        VALIDATING,
        REJECTED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum EventType {
        VALIDATION,
        BRAID,
        REJECTION,
        COMPLETION,
        FAILURE
    }

    static class QuantumException extends RuntimeException {
        QuantumException(String message) {
            super(message);
        }
    }

    static class ValidationException extends QuantumException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class PolicyException extends QuantumException {
        PolicyException(String message) {
            super(message);
        }
    }

    record Complex(double real, double imaginary) {

        Complex {
            if (!Double.isFinite(real) ||
                !Double.isFinite(imaginary)) {
                throw new ValidationException(
                    "Complex amplitude must be finite."
                );
            }
        }

        Complex add(Complex other) {
            return new Complex(
                real + other.real,
                imaginary + other.imaginary
            );
        }

        Complex multiply(Complex other) {
            return new Complex(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        Complex conjugate() {
            return new Complex(real, -imaginary);
        }

        double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        Complex scale(double factor) {
            return new Complex(
                real * factor,
                imaginary * factor
            );
        }

        static Complex exponential(double angle) {
            return new Complex(
                Math.cos(angle),
                Math.sin(angle)
            );
        }
    }

    record BraidOperation(int generator, int orientation) {

        BraidOperation {
            if (generator != 1 && generator != 2) {
                throw new ValidationException(
                    "Only B1 and B2 are supported."
                );
            }

            if (orientation != -1 && orientation != 1) {
                throw new ValidationException(
                    "Invalid braid orientation."
                );
            }
        }

        String description() {
            return "B" + generator +
                (orientation == 1 ? "" : " inverse");
        }
    }

    record ExperimentalConditions(
        double energyGap,
        double temperature,
        double coherenceTime,
        double operationTime,
        double measurementError
    ) {

        ExperimentalConditions {
            if (!Double.isFinite(energyGap) ||
                !Double.isFinite(temperature) ||
                !Double.isFinite(coherenceTime) ||
                !Double.isFinite(operationTime) ||
                !Double.isFinite(measurementError)) {
                throw new ValidationException(
                    "Experimental values must be finite."
                );
            }

            if (energyGap < 0 ||
                temperature < 0 ||
                coherenceTime <= 0 ||
                operationTime <= 0 ||
                measurementError < 0 ||
                measurementError > 1) {
                throw new ValidationException(
                    "Invalid experimental conditions."
                );
            }
        }
    }

    record Policy(
        double minimumGap,
        double maximumMeasurementError,
        int maximumOperations
    ) {

        Policy {
            if (minimumGap <= 0 ||
                maximumMeasurementError < 0 ||
                maximumMeasurementError > 1 ||
                maximumOperations < 1) {
                throw new ValidationException(
                    "Invalid governance policy."
                );
            }
        }

        List<String> evaluate(
            ExperimentalConditions conditions,
            int operationCount
        ) {
            List<String> failures = new ArrayList<>();

            if (conditions.energyGap() < minimumGap) {
                failures.add("Energy gap below policy threshold.");
            }

            if (conditions.temperature() > conditions.energyGap()) {
                failures.add("Temperature exceeds energy-gap scale.");
            }

            if (conditions.operationTime() >=
                conditions.coherenceTime()) {
                failures.add("Coherence window exceeded.");
            }

            if (conditions.measurementError() >
                maximumMeasurementError) {
                failures.add("Parity measurement error exceeds policy.");
            }

            if (operationCount > maximumOperations) {
                failures.add("Operation limit exceeded.");
            }

            return Collections.unmodifiableList(failures);
        }
    }

    record AuditEvent(
        long sequence,
        EventType type,
        String description,
        Instant timestamp
    ) {}

    record ExperimentResult(
        String experimentId,
        ExperimentStatus status,
        List<Complex> initialState,
        List<Complex> finalState,
        int operationCount,
        double fidelity,
        List<String> failures,
        List<AuditEvent> audit
    ) {}

    static final class MajoranaAlgebra {

        private MajoranaAlgebra() {}

        static int anticommutator(int first, int second) {
            if (first < 1 || second < 1) {
                throw new ValidationException(
                    "Majorana indices must be positive."
                );
            }

            return first == second ? 2 : 0;
        }

        static int parity(int occupation) {
            if (occupation != 0 && occupation != 1) {
                throw new ValidationException(
                    "Occupation must be binary."
                );
            }

            return occupation == 0 ? 1 : -1;
        }

        static FusionChannel fusion(int occupation) {
            return occupation == 0
                ? FusionChannel.VACUUM
                : FusionChannel.FERMION;
        }
    }

    static final class QuantumState {

        private final List<Complex> amplitudes;

        QuantumState(List<Complex> amplitudes) {
            if (amplitudes == null || amplitudes.size() != 2) {
                throw new ValidationException(
                    "Expected two computational amplitudes."
                );
            }

            double norm = amplitudes.stream()
                .mapToDouble(Complex::magnitudeSquared)
                .sum();

            if (!Double.isFinite(norm) || norm <= EPSILON) {
                throw new ValidationException(
                    "Invalid state norm."
                );
            }

            double factor = 1.0 / Math.sqrt(norm);

            this.amplitudes = amplitudes.stream()
                .map(value -> value.scale(factor))
                .toList();
        }

        static QuantumState initial() {
            double value = 1.0 / Math.sqrt(2.0);

            return new QuantumState(
                List.of(
                    new Complex(value, 0),
                    new Complex(value, 0)
                )
            );
        }

        List<Complex> amplitudes() {
            return amplitudes;
        }

        double fidelity(QuantumState other) {
            Complex overlap = new Complex(0, 0);

            for (int i = 0; i < 2; i++) {
                overlap = overlap.add(
                    amplitudes.get(i)
                        .conjugate()
                        .multiply(other.amplitudes.get(i))
                );
            }

            return overlap.magnitudeSquared();
        }
    }

    static final class BraidEngine {

        private BraidEngine() {}

        static Complex[][] generator(
            int index,
            int orientation
        ) {
            if (index != 1 && index != 2) {
                throw new ValidationException(
                    "Invalid braid generator."
                );
            }

            if (orientation != -1 && orientation != 1) {
                throw new ValidationException(
                    "Invalid orientation."
                );
            }

            Complex phase = Complex.exponential(-Math.PI / 4.0);
            Complex inverse = phase.conjugate();

            Complex[][] first = {
                {phase, new Complex(0, 0)},
                {new Complex(0, 0), inverse}
            };

            Complex average = phase.add(inverse).scale(0.5);

            Complex difference = phase.add(
                inverse.scale(-1)
            ).scale(0.5);

            Complex[][] second = {
                {average, difference},
                {difference, average}
            };

            Complex[][] selected = index == 1 ? first : second;

            if (orientation == 1) {
                return copy(selected);
            }

            Complex[][] result = new Complex[2][2];

            for (int i = 0; i < 2; i++) {
                for (int j = 0; j < 2; j++) {
                    result[i][j] = selected[j][i].conjugate();
                }
            }

            return result;
        }

        private static Complex[][] copy(Complex[][] matrix) {
            Complex[][] result = new Complex[2][2];

            for (int i = 0; i < 2; i++) {
                System.arraycopy(matrix[i], 0, result[i], 0, 2);
            }

            return result;
        }

        static QuantumState apply(
            Complex[][] matrix,
            QuantumState state
        ) {
            List<Complex> output = new ArrayList<>();

            for (int i = 0; i < 2; i++) {
                Complex value = new Complex(0, 0);

                for (int j = 0; j < 2; j++) {
                    value = value.add(
                        matrix[i][j].multiply(
                            state.amplitudes().get(j)
                        )
                    );
                }

                output.add(value);
            }

            return new QuantumState(output);
        }

        static double unitarityError(Complex[][] matrix) {
            double maximum = 0;

            for (int i = 0; i < 2; i++) {
                for (int j = 0; j < 2; j++) {
                    Complex value = new Complex(0, 0);

                    for (int k = 0; k < 2; k++) {
                        value = value.add(
                            matrix[k][i].conjugate()
                                .multiply(matrix[k][j])
                        );
                    }

                    Complex expected = new Complex(
                        i == j ? 1 : 0,
                        0
                    );

                    maximum = Math.max(
                        maximum,
                        Math.sqrt(
                            value.add(expected.scale(-1))
                                .magnitudeSquared()
                        )
                    );
                }
            }

            return maximum;
        }

        static Complex[][] multiply(
            Complex[][] a,
            Complex[][] b
        ) {
            Complex[][] result = new Complex[2][2];

            for (int i = 0; i < 2; i++) {
                for (int j = 0; j < 2; j++) {
                    Complex value = new Complex(0, 0);

                    for (int k = 0; k < 2; k++) {
                        value = value.add(
                            a[i][k].multiply(b[k][j])
                        );
                    }

                    result[i][j] = value;
                }
            }

            return result;
        }

        static double braidRelationError() {
            Complex[][] b1 = generator(1, 1);
            Complex[][] b2 = generator(2, 1);

            Complex[][] left = multiply(
                multiply(b1, b2),
                b1
            );

            Complex[][] right = multiply(
                multiply(b2, b1),
                b2
            );

            double maximum = 0;

            for (int i = 0; i < 2; i++) {
                for (int j = 0; j < 2; j++) {
                    maximum = Math.max(
                        maximum,
                        Math.sqrt(
                            left[i][j]
                                .add(right[i][j].scale(-1))
                                .magnitudeSquared()
                        )
                    );
                }
            }

            return maximum;
        }
    }

    static final class ExperimentService {

        private final Policy policy;
        private final Map<String, ExperimentResult> registry =
            new HashMap<>();

        ExperimentService(Policy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        synchronized ExperimentResult execute(
            String experimentId,
            ExperimentalConditions conditions,
            List<BraidOperation> operations
        ) {
            if (experimentId == null || experimentId.isBlank()) {
                throw new ValidationException(
                    "Experiment ID is required."
                );
            }

            Objects.requireNonNull(conditions);
            Objects.requireNonNull(operations);

            if (registry.containsKey(experimentId)) {
                throw new ValidationException(
                    "Experiment ID already exists."
                );
            }

            QuantumState initial = QuantumState.initial();

            List<AuditEvent> audit = new ArrayList<>();

            audit.add(new AuditEvent(
                1,
                EventType.VALIDATION,
                "Experiment validation started.",
                Instant.now()
            ));

            List<String> failures = policy.evaluate(
                conditions,
                operations.size()
            );

            if (!failures.isEmpty()) {
                audit.add(new AuditEvent(
                    2,
                    EventType.REJECTION,
                    "Experiment rejected by operating policy.",
                    Instant.now()
                ));

                ExperimentResult rejected = new ExperimentResult(
                    experimentId,
                    ExperimentStatus.REJECTED,
                    initial.amplitudes(),
                    initial.amplitudes(),
                    0,
                    1.0,
                    failures,
                    List.copyOf(audit)
                );

                registry.put(experimentId, rejected);

                return rejected;
            }

            ExperimentStatus status = ExperimentStatus.RUNNING;
            QuantumState current = initial;

            try {
                int sequence = 1;

                for (BraidOperation operation : operations) {
                    current = BraidEngine.apply(
                        BraidEngine.generator(
                            operation.generator(),
                            operation.orientation()
                        ),
                        current
                    );

                    audit.add(new AuditEvent(
                        ++sequence,
                        EventType.BRAID,
                        operation.description(),
                        Instant.now()
                    ));
                }

                status = ExperimentStatus.COMPLETED;

                audit.add(new AuditEvent(
                    ++sequence,
                    EventType.COMPLETION,
                    "Experiment completed successfully.",
                    Instant.now()
                ));

                ExperimentResult completed = new ExperimentResult(
                    experimentId,
                    status,
                    initial.amplitudes(),
                    current.amplitudes(),
                    operations.size(),
                    initial.fidelity(current),
                    List.of(),
                    List.copyOf(audit)
                );

                registry.put(experimentId, completed);

                return completed;

            } catch (RuntimeException exception) {
                audit.add(new AuditEvent(
                    audit.size() + 1,
                    EventType.FAILURE,
                    exception.getMessage(),
                    Instant.now()
                ));

                ExperimentResult failed = new ExperimentResult(
                    experimentId,
                    ExperimentStatus.FAILED,
                    initial.amplitudes(),
                    current.amplitudes(),
                    audit.size() - 2,
                    initial.fidelity(current),
                    List.of(exception.getMessage()),
                    List.copyOf(audit)
                );

                registry.put(experimentId, failed);

                return failed;
            }
        }

        synchronized ExperimentResult find(String id) {
            return registry.get(id);
        }

        synchronized int experimentCount() {
            return registry.size();
        }
    }

    private static void runTests() {
        if (MajoranaAlgebra.anticommutator(1, 1) != 2 ||
            MajoranaAlgebra.anticommutator(1, 2) != 0) {
            throw new AssertionError("Majorana algebra failed.");
        }

        if (MajoranaAlgebra.parity(0) != 1 ||
            MajoranaAlgebra.parity(1) != -1) {
            throw new AssertionError("Parity test failed.");
        }

        if (BraidEngine.braidRelationError() > EPSILON) {
            throw new AssertionError("Braid relation failed.");
        }

        for (int index : List.of(1, 2)) {
            if (BraidEngine.unitarityError(
                BraidEngine.generator(index, 1)
            ) > EPSILON) {
                throw new AssertionError("Unitarity failed.");
            }
        }

        QuantumState initial = QuantumState.initial();

        QuantumState restored = BraidEngine.apply(
            BraidEngine.generator(1, -1),
            BraidEngine.apply(
                BraidEngine.generator(1, 1),
                initial
            )
        );

        if (initial.fidelity(restored) < 1 - EPSILON) {
            throw new AssertionError("Inverse braid failed.");
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        System.out.println(
            "MAJORANA-BASED TOPOLOGICAL QUANTUM COMPUTING"
        );

        System.out.println("\nMajorana algebra");

        System.out.println(
            "{gamma1, gamma1} = " +
            MajoranaAlgebra.anticommutator(1, 1)
        );

        System.out.println(
            "{gamma1, gamma2} = " +
            MajoranaAlgebra.anticommutator(1, 2)
        );

        System.out.println("\nFusion channels");

        for (int occupation : List.of(0, 1)) {
            System.out.println(
                MajoranaAlgebra.fusion(occupation).symbol() +
                " parity=" +
                MajoranaAlgebra.parity(occupation)
            );
        }

        Policy policy = new Policy(
            0.1,
            0.05,
            10000
        );

        ExperimentService service = new ExperimentService(policy);

        ExperimentalConditions conditions =
            new ExperimentalConditions(
                0.25,
                0.01,
                100,
                2,
                0.01
            );

        List<BraidOperation> sequence = List.of(
            new BraidOperation(1, 1),
            new BraidOperation(2, 1),
            new BraidOperation(1, 1),
            new BraidOperation(2, -1)
        );

        ExperimentResult result = service.execute(
            "JAVA-EXP-001",
            conditions,
            sequence
        );

        System.out.println("\nExperiment status: " + result.status());
        System.out.println("Operations: " + result.operationCount());
        System.out.println("Fidelity: " + result.fidelity());
        System.out.println("Final state: " + result.finalState());

        System.out.println(
            "Braid relation error: " +
            BraidEngine.braidRelationError()
        );

        ExperimentalConditions rejectedConditions =
            new ExperimentalConditions(
                0.01,
                0.01,
                10,
                20,
                0.1
            );

        ExperimentResult rejected = service.execute(
            "JAVA-EXP-002",
            rejectedConditions,
            sequence
        );

        System.out.println("\nRejected experiment: " + rejected.status());

        rejected.failures().forEach(
            failure -> System.out.println("- " + failure)
        );

        System.out.println(
            "\nRegistered experiments: " +
            service.experimentCount()
        );

        runTests();
    }
}
