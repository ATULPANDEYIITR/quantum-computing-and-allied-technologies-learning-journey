import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/*
 * QUANTUM DATA ENCODING
 *
 * Enterprise-oriented quantum feature encoding system.
 *
 * Supports:
 * - Computational basis encoding
 * - RY angle encoding
 * - Amplitude encoding
 * - State normalization
 * - Resource governance
 * - Asynchronous encoding jobs
 * - Measurement probability calculations
 * - Audit records
 *
 * Requires Java 17.
 */

public class QuantumDataEncoding {

    enum EncodingType {
        BASIS,
        ANGLE,
        AMPLITUDE
    }

    enum JobStatus {
        SUBMITTED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    static class EncodingException extends RuntimeException {
        EncodingException(String message) {
            super(message);
        }
    }

    record EncodingRequest(
        String requestId,
        EncodingType type,
        List<Double> features,
        double minimum,
        double maximum
    ) {
        EncodingRequest {
            if (requestId == null || requestId.isBlank()) {
                throw new EncodingException("Request identifier is required.");
            }

            Objects.requireNonNull(type, "Encoding type is required.");
            Objects.requireNonNull(features, "Feature collection is required.");

            features = List.copyOf(features);

            if (features.isEmpty()) {
                throw new EncodingException("Feature collection is empty.");
            }

            if (!Double.isFinite(minimum) ||
                !Double.isFinite(maximum) ||
                maximum <= minimum) {
                throw new EncodingException("Invalid feature range.");
            }

            for (Double feature : features) {
                if (feature == null || !Double.isFinite(feature)) {
                    throw new EncodingException(
                        "Features must contain finite numerical values."
                    );
                }
            }
        }
    }

    record ResourcePolicy(
        int maximumQubits,
        long maximumStateBytes,
        boolean amplitudeEncodingEnabled
    ) {
        ResourcePolicy {
            if (maximumQubits < 0 || maximumQubits > 30) {
                throw new EncodingException("Invalid maximum qubit count.");
            }

            if (maximumStateBytes <= 0) {
                throw new EncodingException("Memory limit must be positive.");
            }
        }
    }

    record QuantumState(
        EncodingType type,
        int qubits,
        List<Double> amplitudes,
        Map<String, Object> metadata
    ) {
        QuantumState {
            Objects.requireNonNull(type);
            amplitudes = List.copyOf(amplitudes);
            metadata = Collections.unmodifiableMap(
                new HashMap<>(metadata)
            );

            if (qubits < 0 || qubits > 30) {
                throw new EncodingException("Invalid qubit count.");
            }

            if (amplitudes.size() != (1L << qubits)) {
                throw new EncodingException("State dimension mismatch.");
            }

            double norm = amplitudes.stream()
                .mapToDouble(value -> value * value)
                .sum();

            if (Math.abs(norm - 1.0) > 1e-9) {
                throw new EncodingException("State is not normalized.");
            }
        }

        List<Double> probabilities() {
            return amplitudes.stream()
                .map(value -> value * value)
                .toList();
        }

        Map<Integer, Double> nonZeroProbabilities() {
            Map<Integer, Double> result = new HashMap<>();

            List<Double> probabilities = probabilities();

            for (int i = 0; i < probabilities.size(); i++) {
                if (probabilities.get(i) > 1e-12) {
                    result.put(i, probabilities.get(i));
                }
            }

            return Collections.unmodifiableMap(result);
        }
    }

    record JobResult(
        String requestId,
        JobStatus status,
        QuantumState state,
        String errorMessage
    ) {}

    interface EncodingStrategy {
        QuantumState encode(EncodingRequest request);
    }

    static final class EncodingAlgorithms {

        private EncodingAlgorithms() {}

        static int requiredQubits(int dimension) {
            if (dimension <= 0) {
                throw new EncodingException("Dimension must be positive.");
            }

            return dimension == 1
                ? 0
                : Integer.SIZE - Integer.numberOfLeadingZeros(dimension - 1);
        }

        static QuantumState basis(EncodingRequest request) {
            List<Double> features = request.features();

            int index = 0;

            for (double value : features) {
                if (value != 0.0 && value != 1.0) {
                    throw new EncodingException(
                        "Basis encoding accepts only binary features."
                    );
                }

                index = (index << 1) | (int) value;
            }

            int qubits = features.size();

            if (qubits > 30) {
                throw new EncodingException(
                    "Basis state exceeds implementation limits."
                );
            }

            double[] amplitudes = new double[1 << qubits];
            amplitudes[index] = 1.0;

            Map<String, Object> metadata = new HashMap<>();
            metadata.put("basisIndex", index);
            metadata.put("bitstring", features.stream()
                .map(value -> Integer.toString((int) value))
                .reduce("", String::concat));

            return createState(
                EncodingType.BASIS,
                qubits,
                amplitudes,
                metadata
            );
        }

        static QuantumState angle(EncodingRequest request) {
            List<Double> features = request.features();

            double[] state = {1.0};
            List<Double> angles = new ArrayList<>();

            for (double feature : features) {
                if (feature < request.minimum() ||
                    feature > request.maximum()) {
                    throw new EncodingException(
                        "Feature lies outside the permitted range."
                    );
                }

                double theta = Math.PI *
                    (feature - request.minimum()) /
                    (request.maximum() - request.minimum());

                angles.add(theta);

                double zero = Math.cos(theta / 2.0);
                double one = Math.sin(theta / 2.0);

                double[] expanded = new double[state.length * 2];

                for (int i = 0; i < state.length; i++) {
                    expanded[2 * i] = state[i] * zero;
                    expanded[2 * i + 1] = state[i] * one;
                }

                state = expanded;
            }

            Map<String, Object> metadata = new HashMap<>();
            metadata.put("anglesRadians", List.copyOf(angles));
            metadata.put("inputFeatures", features);

            return createState(
                EncodingType.ANGLE,
                features.size(),
                state,
                metadata
            );
        }

        static QuantumState amplitude(EncodingRequest request) {
            List<Double> features = request.features();

            if (features.size() > (1 << 30)) {
                throw new EncodingException("Input dimension is too large.");
            }

            double squaredNorm = features.stream()
                .mapToDouble(value -> value * value)
                .sum();

            if (!Double.isFinite(squaredNorm) || squaredNorm <= 0) {
                throw new EncodingException(
                    "Amplitude encoding requires a finite non-zero vector."
                );
            }

            double norm = Math.sqrt(squaredNorm);

            int qubits = requiredQubits(features.size());
            int dimension = 1 << qubits;

            double[] amplitudes = new double[dimension];

            for (int i = 0; i < features.size(); i++) {
                amplitudes[i] = features.get(i) / norm;
            }

            Map<String, Object> metadata = new HashMap<>();
            metadata.put("originalDimension", features.size());
            metadata.put("encodedDimension", dimension);
            metadata.put("originalNorm", norm);

            return createState(
                EncodingType.AMPLITUDE,
                qubits,
                amplitudes,
                metadata
            );
        }

        private static QuantumState createState(
            EncodingType type,
            int qubits,
            double[] values,
            Map<String, Object> metadata
        ) {
            List<Double> amplitudes = new ArrayList<>(values.length);

            for (double value : values) {
                amplitudes.add(value);
            }

            return new QuantumState(
                type,
                qubits,
                amplitudes,
                metadata
            );
        }
    }

    static final class EncodingStrategyRegistry {

        private final Map<EncodingType, EncodingStrategy> strategies =
            new EnumMap<>(EncodingType.class);

        EncodingStrategyRegistry() {
            strategies.put(
                EncodingType.BASIS,
                EncodingAlgorithms::basis
            );

            strategies.put(
                EncodingType.ANGLE,
                EncodingAlgorithms::angle
            );

            strategies.put(
                EncodingType.AMPLITUDE,
                EncodingAlgorithms::amplitude
            );
        }

        QuantumState execute(EncodingRequest request) {
            EncodingStrategy strategy = strategies.get(request.type());

            if (strategy == null) {
                throw new EncodingException(
                    "No strategy registered for encoding type."
                );
            }

            return strategy.encode(request);
        }
    }

    static final class ResourceGovernanceService {

        private final ResourcePolicy policy;

        ResourceGovernanceService(ResourcePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void validate(QuantumState state) {
            if (
                state.type() == EncodingType.AMPLITUDE &&
                !policy.amplitudeEncodingEnabled()
            ) {
                throw new EncodingException(
                    "Amplitude encoding is disabled by policy."
                );
            }

            if (state.qubits() > policy.maximumQubits()) {
                throw new EncodingException(
                    "Maximum qubit allocation exceeded."
                );
            }

            long requiredBytes = state.amplitudes().size() *
                Double.BYTES;

            if (requiredBytes > policy.maximumStateBytes()) {
                throw new EncodingException(
                    "State memory budget exceeded."
                );
            }
        }
    }

    static final class AuditService {

        private final Map<String, JobResult> auditRecords =
            new ConcurrentHashMap<>();

        void record(JobResult result) {
            auditRecords.put(result.requestId(), result);
        }

        JobResult find(String requestId) {
            return auditRecords.get(requestId);
        }

        int recordCount() {
            return auditRecords.size();
        }
    }

    static final class EncodingApplicationService
        implements AutoCloseable {

        private final EncodingStrategyRegistry registry;
        private final ResourceGovernanceService governance;
        private final AuditService audit;

        private final ExecutorService executor =
            Executors.newFixedThreadPool(3);

        EncodingApplicationService(
            EncodingStrategyRegistry registry,
            ResourceGovernanceService governance,
            AuditService audit
        ) {
            this.registry = registry;
            this.governance = governance;
            this.audit = audit;
        }

        CompletableFuture<JobResult> submit(EncodingRequest request) {
            return CompletableFuture.supplyAsync(() -> {
                try {
                    QuantumState state = registry.execute(request);

                    governance.validate(state);

                    JobResult result = new JobResult(
                        request.requestId(),
                        JobStatus.COMPLETED,
                        state,
                        null
                    );

                    audit.record(result);

                    return result;

                } catch (RuntimeException exception) {
                    JobResult failure = new JobResult(
                        request.requestId(),
                        JobStatus.FAILED,
                        null,
                        exception.getMessage()
                    );

                    audit.record(failure);

                    return failure;
                }
            }, executor);
        }

        @Override
        public void close() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    private static EncodingRequest request(
        String id,
        EncodingType type,
        List<Double> features
    ) {
        return new EncodingRequest(
            id,
            type,
            features,
            0.0,
            1.0
        );
    }

    private static void printResult(JobResult result) {
        System.out.println("\nRequest: " + result.requestId());
        System.out.println("Status: " + result.status());

        if (result.status() == JobStatus.FAILED) {
            System.out.println("Failure: " + result.errorMessage());
            return;
        }

        QuantumState state = result.state();

        System.out.println("Method: " + state.type());
        System.out.println("Qubits: " + state.qubits());
        System.out.println("State dimension: " + state.amplitudes().size());

        System.out.println("Amplitudes:");

        for (int i = 0; i < state.amplitudes().size(); i++) {
            if (Math.abs(state.amplitudes().get(i)) > 1e-10) {
                System.out.printf(
                    "  |%s> : %.6f%n",
                    Integer.toBinaryString(i)
                        .formatted(state.qubits()),
                    state.amplitudes().get(i)
                );
            }
        }

        System.out.println("Probabilities: " + state.probabilities());
    }

    public static void main(String[] args) {

        ResourcePolicy policy = new ResourcePolicy(
            12,
            64L * 1024 * 1024,
            true
        );

        ResourceGovernanceService governance =
            new ResourceGovernanceService(policy);

        AuditService audit = new AuditService();

        EncodingStrategyRegistry registry =
            new EncodingStrategyRegistry();

        try (EncodingApplicationService application =
            new EncodingApplicationService(registry, governance, audit)) {

            List<EncodingRequest> requests = List.of(
                request(
                    "BASIS-" + UUID.randomUUID(),
                    EncodingType.BASIS,
                    List.of(1.0, 0.0, 1.0, 1.0)
                ),
                request(
                    "ANGLE-" + UUID.randomUUID(),
                    EncodingType.ANGLE,
                    List.of(0.2, 0.5, 0.8)
                ),
                request(
                    "AMPLITUDE-" + UUID.randomUUID(),
                    EncodingType.AMPLITUDE,
                    List.of(3.0, 4.0, 0.0)
                ),
                request(
                    "INVALID-" + UUID.randomUUID(),
                    EncodingType.AMPLITUDE,
                    List.of(0.0, 0.0, 0.0)
                )
            );

            List<CompletableFuture<JobResult>> futures = requests.stream()
                .map(application::submit)
                .toList();

            CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0])
            ).join();

            futures.stream()
                .map(CompletableFuture::join)
                .forEach(QuantumDataEncoding::printResult);

            System.out.println("\nAUDIT REPORT");
            System.out.println("Recorded requests: " + audit.recordCount());

            long completed = futures.stream()
                .map(CompletableFuture::join)
                .filter(result -> result.status() == JobStatus.COMPLETED)
                .count();

            long failed = futures.size() - completed;

            System.out.println("Successful: " + completed);
            System.out.println("Failed: " + failed);
        }

        System.out.println("\nEnterprise encoding workflow completed.");
    }
}
