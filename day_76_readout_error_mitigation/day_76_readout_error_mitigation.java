import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;

/**
 * Readout Error Mitigation
 *
 * Enterprise-oriented measurement correction system.
 *
 * Capabilities:
 * - Immutable calibration records.
 * - Assignment matrix construction.
 * - Multi-qubit tensor products.
 * - Measurement validation.
 * - Constrained probability estimation.
 * - Calibration version management.
 * - Reviewable audit events.
 * - Asynchronous experiment processing.
 * - Drift monitoring.
 *
 * Java 17, standard library only.
 */
public class ReadoutErrorMitigation {

    enum CalibrationState {
        UNCALIBRATED,
        ACTIVE,
        STALE,
        INVALID
    }

    enum ExperimentState {
        RECEIVED,
        VALIDATED,
        CORRECTED,
        FAILED
    }

    record Calibration(
        int qubit,
        int shots,
        double p00,
        double p11
    ) {
        Calibration {
            if (qubit < 0 || shots <= 0) {
                throw new IllegalArgumentException(
                    "Invalid calibration metadata."
                );
            }

            validateProbability(p00, "P(0|0)");
            validateProbability(p11, "P(1|1)");
        }

        double[][] assignmentMatrix() {
            return new double[][] {
                {p00, 1.0 - p11},
                {1.0 - p00, p11}
            };
        }
    }

    record MitigationPolicy(
        double regularization,
        double tolerance,
        int maxIterations,
        int minimumCalibrationShots,
        double driftThreshold
    ) {
        MitigationPolicy {
            if (
                regularization < 0 ||
                tolerance <= 0 ||
                maxIterations <= 0 ||
                minimumCalibrationShots <= 0 ||
                driftThreshold <= 0 ||
                driftThreshold > 1
            ) {
                throw new IllegalArgumentException(
                    "Invalid mitigation policy."
                );
            }
        }

        static MitigationPolicy standard() {
            return new MitigationPolicy(
                1e-8, 1e-10, 10000, 1000, 0.03
            );
        }
    }

    record MitigationResult(
        List<Double> raw,
        List<Double> corrected,
        double residual,
        int iterations,
        boolean converged,
        int calibrationVersion
    ) {}

    record AuditEvent(
        String event,
        String detail,
        long timestamp
    ) {}

    static class CalibrationException extends RuntimeException {
        CalibrationException(String message) {
            super(message);
        }
    }

    static class ExperimentException extends RuntimeException {
        ExperimentException(String message) {
            super(message);
        }
    }

    static class MatrixOps {

        static double[][] transpose(double[][] matrix) {
            double[][] result = new double[
                matrix[0].length
            ][matrix.length];

            for (int i = 0; i < matrix.length; i++) {
                for (int j = 0; j < matrix[i].length; j++) {
                    result[j][i] = matrix[i][j];
                }
            }

            return result;
        }

        static double[][] multiply(
            double[][] a,
            double[][] b
        ) {
            if (a[0].length != b.length) {
                throw new IllegalArgumentException(
                    "Matrix dimensions do not match."
                );
            }

            double[][] result = new double[
                a.length
            ][b[0].length];

            for (int i = 0; i < a.length; i++) {
                for (int k = 0; k < b.length; k++) {
                    for (int j = 0; j < b[0].length; j++) {
                        result[i][j] += a[i][k] * b[k][j];
                    }
                }
            }

            return result;
        }

        static double[] multiply(
            double[][] matrix,
            double[] vector
        ) {
            double[] result = new double[matrix.length];

            for (int i = 0; i < matrix.length; i++) {
                for (int j = 0; j < vector.length; j++) {
                    result[i] += matrix[i][j] * vector[j];
                }
            }

            return result;
        }

        static double[][] tensorProduct(
            double[][] a,
            double[][] b
        ) {
            double[][] result = new double[
                a.length * b.length
            ][a[0].length * b[0].length];

            for (int i = 0; i < a.length; i++) {
                for (int j = 0; j < b.length; j++) {
                    for (int k = 0; k < a[0].length; k++) {
                        for (int l = 0; l < b[0].length; l++) {
                            result[i * b.length + j][
                                k * b[0].length + l
                            ] = a[i][k] * b[j][l];
                        }
                    }
                }
            }

            return result;
        }

        static double[] projectSimplex(double[] values) {
            double[] sorted = values.clone();

            Arrays.sort(sorted);
            reverse(sorted);

            double cumulative = 0;
            double theta = 0;

            for (int i = 0; i < sorted.length; i++) {
                cumulative += sorted[i];

                double candidate =
                    (cumulative - 1.0) / (i + 1);

                if (sorted[i] > candidate) {
                    theta = candidate;
                }
            }

            double[] result = new double[values.length];

            for (int i = 0; i < values.length; i++) {
                result[i] = Math.max(0, values[i] - theta);
            }

            return result;
        }

        static void reverse(double[] values) {
            for (int i = 0, j = values.length - 1; i < j; i++, j--) {
                double temp = values[i];
                values[i] = values[j];
                values[j] = temp;
            }
        }

        static double norm(double[] values) {
            double sum = 0;

            for (double value : values) {
                sum += value * value;
            }

            return Math.sqrt(sum);
        }

        static double[] subtract(double[] a, double[] b) {
            double[] result = new double[a.length];

            for (int i = 0; i < a.length; i++) {
                result[i] = a[i] - b[i];
            }

            return result;
        }
    }

    static void validateProbability(double value, String name) {
        if (
            !Double.isFinite(value) ||
            value < 0 ||
            value > 1
        ) {
            throw new IllegalArgumentException(
                name + " must be between zero and one."
            );
        }
    }

    interface CalibrationRepository {
        void save(List<Calibration> calibrations, int version);
        List<Calibration> load();
    }

    static class InMemoryCalibrationRepository
        implements CalibrationRepository {

        private List<Calibration> stored = List.of();
        private int version;

        @Override
        public synchronized void save(
            List<Calibration> calibrations,
            int version
        ) {
            this.stored = List.copyOf(calibrations);
            this.version = version;
        }

        @Override
        public synchronized List<Calibration> load() {
            return stored;
        }

        public synchronized int version() {
            return version;
        }
    }

    static class ReadoutMitigationService {

        private final MitigationPolicy policy;
        private final CalibrationRepository repository;
        private final List<AuditEvent> audit =
            new CopyOnWriteArrayList<>();

        private volatile List<Calibration> calibrations = List.of();
        private volatile double[][] assignment;
        private volatile int version = 0;
        private volatile CalibrationState state =
            CalibrationState.UNCALIBRATED;

        ReadoutMitigationService(
            MitigationPolicy policy,
            CalibrationRepository repository
        ) {
            this.policy = Objects.requireNonNull(policy);
            this.repository = Objects.requireNonNull(repository);
        }

        private void log(String event, String detail) {
            audit.add(new AuditEvent(
                event,
                detail,
                System.currentTimeMillis()
            ));
        }

        public synchronized void calibrate(
            List<Calibration> newCalibrations
        ) {
            if (
                newCalibrations == null ||
                newCalibrations.isEmpty()
            ) {
                throw new CalibrationException(
                    "Calibration cannot be empty."
                );
            }

            List<Calibration> candidate =
                new ArrayList<>(newCalibrations);

            candidate.sort(
                Comparator.comparingInt(Calibration::qubit)
            );

            for (int i = 0; i < candidate.size(); i++) {
                Calibration calibration = candidate.get(i);

                if (calibration.qubit() != i) {
                    throw new CalibrationException(
                        "Missing or duplicate qubit calibration."
                    );
                }

                if (
                    calibration.shots() <
                    policy.minimumCalibrationShots()
                ) {
                    throw new CalibrationException(
                        "Insufficient calibration shots for qubit " + i
                    );
                }
            }

            double[][] candidateMatrix = {{1.0}};

            for (Calibration calibration : candidate) {
                candidateMatrix = MatrixOps.tensorProduct(
                    candidateMatrix,
                    calibration.assignmentMatrix()
                );
            }

            // Atomic state replacement after successful validation.
            repository.save(candidate, version + 1);
            calibrations = List.copyOf(candidate);
            assignment = candidateMatrix;
            version++;
            state = CalibrationState.ACTIVE;

            log(
                "CALIBRATION_ACTIVATED",
                "Version " + version + ", qubits " + candidate.size()
            );
        }

        public List<Double> estimate(
            Map<String, Integer> counts
        ) {
            if (state != CalibrationState.ACTIVE) {
                throw new CalibrationException(
                    "Active calibration required."
                );
            }

            if (counts == null || counts.isEmpty()) {
                throw new ExperimentException(
                    "Measurement counts are empty."
                );
            }

            int qubits = calibrations.size();
            int dimension = 1 << qubits;
            double[] probabilities = new double[dimension];
            long total = 0;

            for (var entry : counts.entrySet()) {
                String state = entry.getKey();
                int count = entry.getValue();

                if (
                    state.length() != qubits ||
                    !state.matches("[01]+") ||
                    count < 0
                ) {
                    throw new ExperimentException(
                        "Invalid measurement entry: " + state
                    );
                }

                int index = Integer.parseInt(state, 2);
                probabilities[index] += count;
                total += count;
            }

            if (total <= 0) {
                throw new ExperimentException(
                    "Measurement shots must be positive."
                );
            }

            for (int i = 0; i < dimension; i++) {
                probabilities[i] /= total;
            }

            return Arrays.stream(probabilities)
                .boxed()
                .toList();
        }

        public MitigationResult mitigate(
            Map<String, Integer> counts
        ) {
            List<Double> rawList = estimate(counts);

            double[] observed = rawList.stream()
                .mapToDouble(Double::doubleValue)
                .toArray();

            double[][] at = MatrixOps.transpose(assignment);
            double[][] ata = MatrixOps.multiply(at, assignment);

            for (int i = 0; i < ata.length; i++) {
                ata[i][i] += policy.regularization();
            }

            double[] atq = MatrixOps.multiply(at, observed);

            double lipschitz = 0;

            for (double[] row : ata) {
                double rowSum = 0;

                for (double value : row) {
                    rowSum += Math.abs(value);
                }

                lipschitz = Math.max(lipschitz, rowSum);
            }

            if (lipschitz <= 0) {
                throw new ExperimentException(
                    "Invalid optimization matrix."
                );
            }

            double rate = 1.0 / lipschitz;
            double[] estimate = observed.clone();

            boolean converged = false;
            int iteration = 0;

            for (
                iteration = 1;
                iteration <= policy.maxIterations();
                iteration++
            ) {
                double[] gradient =
                    MatrixOps.multiply(ata, estimate);

                for (int i = 0; i < gradient.length; i++) {
                    gradient[i] -= atq[i];
                }

                double[] candidate = estimate.clone();

                for (int i = 0; i < candidate.length; i++) {
                    candidate[i] -= rate * gradient[i];
                }

                candidate = MatrixOps.projectSimplex(candidate);

                double difference = 0;

                for (int i = 0; i < candidate.length; i++) {
                    difference = Math.max(
                        difference,
                        Math.abs(candidate[i] - estimate[i])
                    );
                }

                estimate = candidate;

                if (difference < policy.tolerance()) {
                    converged = true;
                    break;
                }
            }

            double[] predicted =
                MatrixOps.multiply(assignment, estimate);

            double residual = MatrixOps.norm(
                MatrixOps.subtract(predicted, observed)
            );

            List<Double> corrected = Arrays.stream(estimate)
                .boxed()
                .toList();

            MitigationResult result = new MitigationResult(
                rawList,
                corrected,
                residual,
                Math.min(iteration, policy.maxIterations()),
                converged,
                version
            );

            log(
                "EXPERIMENT_CORRECTED",
                "Residual=" + residual + ", converged=" + converged
            );

            return result;
        }

        public synchronized boolean detectDrift(
            Calibration updated
        ) {
            if (state != CalibrationState.ACTIVE) {
                throw new CalibrationException(
                    "Baseline calibration unavailable."
                );
            }

            Calibration baseline = calibrations.get(updated.qubit());

            double deviation = Math.max(
                Math.abs(updated.p00() - baseline.p00()),
                Math.abs(updated.p11() - baseline.p11())
            );

            boolean drifted =
                deviation > policy.driftThreshold();

            if (drifted) {
                state = CalibrationState.STALE;
                log(
                    "CALIBRATION_STALE",
                    "Qubit " + updated.qubit() +
                    ", deviation " + deviation
                );
            }

            return drifted;
        }

        public List<AuditEvent> auditTrail() {
            return List.copyOf(audit);
        }

        public CalibrationState calibrationState() {
            return state;
        }

        public int version() {
            return version;
        }
    }

    static class ExperimentProcessor {

        private final ReadoutMitigationService service;
        private final ExecutorService executor;

        ExperimentProcessor(
            ReadoutMitigationService service,
            int workers
        ) {
            if (workers <= 0) {
                throw new IllegalArgumentException(
                    "Worker count must be positive."
                );
            }

            this.service = service;
            this.executor = Executors.newFixedThreadPool(workers);
        }

        CompletableFuture<MitigationResult> submit(
            Map<String, Integer> counts
        ) {
            Map<String, Integer> immutableCounts =
                Map.copyOf(counts);

            return CompletableFuture.supplyAsync(
                () -> service.mitigate(immutableCounts),
                executor
            );
        }

        void shutdown() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    static Map<String, Integer> simulate(
        double[] trueDistribution,
        double[][] assignment,
        int shots,
        long seed
    ) {
        if (shots <= 0 || trueDistribution.length != assignment.length) {
            throw new IllegalArgumentException(
                "Invalid simulation parameters."
            );
        }

        double[] observed =
            MatrixOps.multiply(assignment, trueDistribution);

        Random random = new Random(seed);
        Map<String, Integer> counts = new TreeMap<>();

        int qubits = Integer.numberOfTrailingZeros(
            observed.length
        );

        for (int i = 0; i < observed.length; i++) {
            counts.put(
                String.format("%" + qubits + "s",
                    Integer.toBinaryString(i)).replace(' ', '0'),
                0
            );
        }

        for (int shot = 0; shot < shots; shot++) {
            double value = random.nextDouble();
            double cumulative = 0;

            for (int i = 0; i < observed.length; i++) {
                cumulative += observed[i];

                if (value <= cumulative || i == observed.length - 1) {
                    String state = String.format(
                        "%" + qubits + "s",
                        Integer.toBinaryString(i)
                    ).replace(' ', '0');

                    counts.merge(state, 1, Integer::sum);
                    break;
                }
            }
        }

        return counts;
    }

    public static void main(String[] args) {
        InMemoryCalibrationRepository repository =
            new InMemoryCalibrationRepository();

        MitigationPolicy policy = MitigationPolicy.standard();

        ReadoutMitigationService service =
            new ReadoutMitigationService(policy, repository);

        service.calibrate(List.of(
            new Calibration(0, 10000, 0.94, 0.91),
            new Calibration(1, 10000, 0.96, 0.93)
        ));

        double[] expected = {0.70, 0.10, 0.15, 0.05};

        Map<String, Integer> counts = simulate(
            expected,
            service.assignment,
            50000,
            42
        );

        MitigationResult result = service.mitigate(counts);

        System.out.println("READOUT ERROR MITIGATION");
        System.out.println("========================");

        System.out.println("\nObserved distribution:");
        result.raw().forEach(System.out::println);

        System.out.println("\nCorrected distribution:");
        result.corrected().forEach(System.out::println);

        System.out.println("\nDiagnostics:");
        System.out.println("Calibration version: " + result.calibrationVersion());
        System.out.println("Residual: " + result.residual());
        System.out.println("Iterations: " + result.iterations());
        System.out.println("Converged: " + result.converged());

        double total = result.corrected().stream()
            .mapToDouble(Double::doubleValue)
            .sum();

        if (Math.abs(total - 1.0) > 1e-8) {
            throw new IllegalStateException(
                "Corrected probabilities are not normalized."
            );
        }

        if (result.corrected().stream().anyMatch(p -> p < 0)) {
            throw new IllegalStateException(
                "Negative corrected probability."
            );
        }

        System.out.println("\nProbability validation: PASSED");

        ExperimentProcessor processor =
            new ExperimentProcessor(service, 2);

        try {
            MitigationResult asynchronous = processor
                .submit(counts)
                .get(10, TimeUnit.SECONDS);

            System.out.println(
                "Asynchronous experiment residual: " +
                asynchronous.residual()
            );
        } catch (Exception exception) {
            System.err.println(
                "Experiment processing failed: " +
                exception.getMessage()
            );
        } finally {
            processor.shutdown();
        }

        System.out.println("\nAudit events:");

        for (AuditEvent event : service.auditTrail()) {
            System.out.println(
                event.event() + " | " + event.detail()
            );
        }
    }
}
