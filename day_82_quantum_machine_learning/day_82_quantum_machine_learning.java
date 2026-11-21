import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/*
 * Quantum Machine Learning
 *
 * Java 17 enterprise QML experiment governance platform.
 *
 * Features:
 * - QML algorithm taxonomy
 * - Immutable domain records
 * - Experiment registration
 * - Dataset governance
 * - Circuit validation
 * - Backend capability policies
 * - Hybrid execution lifecycle
 * - Approval and resource controls
 * - Evaluation metrics
 * - Audit events
 *
 * Requires Java 17.
 * No external dependencies.
 */

public class QuantumMachineLearning {

    // ========================================================
    // 1. ALGORITHM TAXONOMY
    // ========================================================

    enum AlgorithmFamily {
        VARIATIONAL_CLASSIFIER,
        QUANTUM_NEURAL_NETWORK,
        QUANTUM_KERNEL,
        QUANTUM_GENERATIVE,
        QUANTUM_REINFORCEMENT,
        VQE,
        QAOA,
        QUANTUM_INSPIRED
    }

    enum BackendType {
        STATEVECTOR,
        SHOT_BASED,
        NOISY_SIMULATOR,
        QUANTUM_HARDWARE
    }

    enum ExperimentStatus {
        CREATED,
        VALIDATED,
        APPROVED,
        QUEUED,
        RUNNING,
        COMPLETED,
        REJECTED,
        FAILED,
        CANCELLED
    }

    enum DataClassification {
        PUBLIC,
        INTERNAL,
        CONFIDENTIAL,
        RESTRICTED
    }

    enum WorkloadCategory {
        SUPERVISED_LEARNING,
        SIMILARITY_LEARNING,
        OPTIMIZATION,
        CHEMISTRY,
        GENERATIVE,
        REINFORCEMENT
    }

    // ========================================================
    // 2. CUSTOM EXCEPTIONS
    // ========================================================

    static class QMLException extends RuntimeException {
        QMLException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException extends QMLException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    static class InvalidTransitionException extends QMLException {
        InvalidTransitionException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 3. IMMUTABLE DOMAIN RECORDS
    // ========================================================

    record Dataset(
        String id,
        String name,
        int samples,
        int features,
        DataClassification classification,
        boolean consentVerified,
        boolean provenanceVerified
    ) {
        Dataset {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);
            Objects.requireNonNull(classification);

            if (id.isBlank() || name.isBlank()) {
                throw new QMLException("Dataset identity is required.");
            }

            if (samples < 1 || features < 1) {
                throw new QMLException("Invalid dataset dimensions.");
            }
        }
    }

    record CircuitDefinition(
        int qubits,
        int depth,
        int trainableParameters,
        boolean usesEntanglement,
        boolean usesMeasurements
    ) {
        CircuitDefinition {
            if (qubits < 1 || qubits > 1000) {
                throw new QMLException("Invalid qubit count.");
            }

            if (depth < 1 || trainableParameters < 0) {
                throw new QMLException("Invalid circuit configuration.");
            }
        }
    }

    record BackendCapability(
        String name,
        BackendType type,
        int maximumQubits,
        int maximumDepth,
        int maximumShots,
        double gateFidelity,
        double measurementFidelity,
        boolean supportsEntanglement,
        boolean enabled
    ) {
        BackendCapability {
            Objects.requireNonNull(name);
            Objects.requireNonNull(type);

            if (name.isBlank() || maximumQubits < 1 ||
                maximumDepth < 1 || maximumShots < 1) {
                throw new QMLException("Invalid backend capability.");
            }

            if (!Double.isFinite(gateFidelity) ||
                gateFidelity <= 0 || gateFidelity > 1) {
                throw new QMLException("Invalid gate fidelity.");
            }

            if (!Double.isFinite(measurementFidelity) ||
                measurementFidelity <= 0 ||
                measurementFidelity > 1) {
                throw new QMLException("Invalid measurement fidelity.");
            }
        }
    }

    record ExperimentMetrics(
        double accuracy,
        double precision,
        double recall,
        double trainingLoss,
        double standardError,
        int shots,
        Instant evaluatedAt
    ) {
        ExperimentMetrics {
            if (!validMetric(accuracy) ||
                !validMetric(precision) ||
                !validMetric(recall)) {
                throw new QMLException("Metrics must be between 0 and 1.");
            }

            if (!Double.isFinite(trainingLoss) || trainingLoss < 0 ||
                !Double.isFinite(standardError) || standardError < 0 ||
                shots < 1) {
                throw new QMLException("Invalid evaluation metrics.");
            }

            Objects.requireNonNull(evaluatedAt);
        }

        private static boolean validMetric(double value) {
            return Double.isFinite(value) &&
                value >= 0 && value <= 1;
        }
    }

    record AuditEvent(
        String experimentId,
        String action,
        String actor,
        Instant timestamp,
        String detail
    ) {}

    // ========================================================
    // 4. ALGORITHM CATALOG
    // ========================================================

    static class AlgorithmCatalog {

        private static final Map<AlgorithmFamily, String> DESCRIPTIONS;

        static {
            Map<AlgorithmFamily, String> map =
                new EnumMap<>(AlgorithmFamily.class);

            map.put(
                AlgorithmFamily.VARIATIONAL_CLASSIFIER,
                "Parameterized circuits for supervised classification."
            );

            map.put(
                AlgorithmFamily.QUANTUM_NEURAL_NETWORK,
                "Quantum circuit components integrated with neural models."
            );

            map.put(
                AlgorithmFamily.QUANTUM_KERNEL,
                "Quantum feature maps and fidelity-based similarity."
            );

            map.put(
                AlgorithmFamily.QUANTUM_GENERATIVE,
                "Quantum models for generating probability distributions."
            );

            map.put(
                AlgorithmFamily.QUANTUM_REINFORCEMENT,
                "Quantum policy and value-function representations."
            );

            map.put(
                AlgorithmFamily.VQE,
                "Variational approximation of quantum ground-state energy."
            );

            map.put(
                AlgorithmFamily.QAOA,
                "Parameterized circuits for combinatorial optimization."
            );

            map.put(
                AlgorithmFamily.QUANTUM_INSPIRED,
                "Classical methods motivated by quantum techniques."
            );

            DESCRIPTIONS = Collections.unmodifiableMap(map);
        }

        static String description(AlgorithmFamily algorithm) {
            return DESCRIPTIONS.get(algorithm);
        }

        static void printCatalog() {
            DESCRIPTIONS.forEach((algorithm, description) ->
                System.out.println(algorithm + ": " + description)
            );
        }
    }

    // ========================================================
    // 5. EXPERIMENT AGGREGATE
    // ========================================================

    static class QMLExperiment {

        private final String id;
        private final String name;
        private final AlgorithmFamily algorithm;
        private final BackendType backend;
        private final Dataset dataset;
        private final CircuitDefinition circuit;
        private final int shots;
        private final double minimumFidelity;

        private ExperimentStatus status;
        private ExperimentMetrics metrics;
        private String failureReason;

        QMLExperiment(
            String name,
            AlgorithmFamily algorithm,
            BackendType backend,
            Dataset dataset,
            CircuitDefinition circuit,
            int shots,
            double minimumFidelity
        ) {
            if (name == null || name.isBlank()) {
                throw new QMLException("Experiment name is required.");
            }

            this.id = UUID.randomUUID().toString();
            this.name = name;
            this.algorithm = Objects.requireNonNull(algorithm);
            this.backend = Objects.requireNonNull(backend);
            this.dataset = Objects.requireNonNull(dataset);
            this.circuit = Objects.requireNonNull(circuit);

            if (shots < 1 || shots > 100_000_000) {
                throw new QMLException("Invalid shot count.");
            }

            if (!Double.isFinite(minimumFidelity) ||
                minimumFidelity < 0 || minimumFidelity > 1) {
                throw new QMLException("Invalid fidelity threshold.");
            }

            this.shots = shots;
            this.minimumFidelity = minimumFidelity;
            this.status = ExperimentStatus.CREATED;
        }

        String id() {
            return id;
        }

        String name() {
            return name;
        }

        AlgorithmFamily algorithm() {
            return algorithm;
        }

        BackendType backend() {
            return backend;
        }

        Dataset dataset() {
            return dataset;
        }

        CircuitDefinition circuit() {
            return circuit;
        }

        int shots() {
            return shots;
        }

        double minimumFidelity() {
            return minimumFidelity;
        }

        ExperimentStatus status() {
            return status;
        }

        ExperimentMetrics metrics() {
            return metrics;
        }

        String failureReason() {
            return failureReason;
        }

        void transition(ExperimentStatus next) {
            Map<ExperimentStatus, List<ExperimentStatus>> transitions =
                new EnumMap<>(ExperimentStatus.class);

            transitions.put(
                ExperimentStatus.CREATED,
                List.of(
                    ExperimentStatus.VALIDATED,
                    ExperimentStatus.REJECTED,
                    ExperimentStatus.CANCELLED
                )
            );

            transitions.put(
                ExperimentStatus.VALIDATED,
                List.of(
                    ExperimentStatus.APPROVED,
                    ExperimentStatus.REJECTED,
                    ExperimentStatus.CANCELLED
                )
            );

            transitions.put(
                ExperimentStatus.APPROVED,
                List.of(
                    ExperimentStatus.QUEUED,
                    ExperimentStatus.CANCELLED
                )
            );

            transitions.put(
                ExperimentStatus.QUEUED,
                List.of(
                    ExperimentStatus.RUNNING,
                    ExperimentStatus.CANCELLED
                )
            );

            transitions.put(
                ExperimentStatus.RUNNING,
                List.of(
                    ExperimentStatus.COMPLETED,
                    ExperimentStatus.FAILED,
                    ExperimentStatus.CANCELLED
                )
            );

            if (!transitions.getOrDefault(status, List.of()).contains(next)) {
                throw new InvalidTransitionException(
                    "Cannot transition from " + status + " to " + next
                );
            }

            status = next;
        }

        void complete(ExperimentMetrics metrics) {
            if (status != ExperimentStatus.RUNNING) {
                throw new InvalidTransitionException(
                    "Only running experiments can complete."
                );
            }

            this.metrics = Objects.requireNonNull(metrics);
            transition(ExperimentStatus.COMPLETED);
        }

        void fail(String reason) {
            if (status != ExperimentStatus.RUNNING) {
                throw new InvalidTransitionException(
                    "Only running experiments can fail."
                );
            }

            this.failureReason = reason;
            transition(ExperimentStatus.FAILED);
        }
    }

    // ========================================================
    // 6. DATA GOVERNANCE POLICY
    // ========================================================

    static class DatasetGovernancePolicy {

        void validate(Dataset dataset, BackendType backend) {
            if (!dataset.provenanceVerified()) {
                throw new PolicyViolationException(
                    "Dataset provenance is not verified."
                );
            }

            if (!dataset.consentVerified() &&
                dataset.classification() != DataClassification.PUBLIC) {
                throw new PolicyViolationException(
                    "Consent verification is required."
                );
            }

            if (
                dataset.classification() == DataClassification.RESTRICTED &&
                backend == BackendType.QUANTUM_HARDWARE
            ) {
                throw new PolicyViolationException(
                    "Restricted data cannot use the external hardware backend."
                );
            }
        }
    }

    // ========================================================
    // 7. BACKEND AND CIRCUIT POLICY
    // ========================================================

    static class CircuitPolicy {

        void validate(
            QMLExperiment experiment,
            BackendCapability capability
        ) {
            CircuitDefinition circuit = experiment.circuit();

            if (!capability.enabled()) {
                throw new PolicyViolationException(
                    "Backend is disabled."
                );
            }

            if (experiment.backend() != capability.type()) {
                throw new PolicyViolationException(
                    "Backend type mismatch."
                );
            }

            if (circuit.qubits() > capability.maximumQubits()) {
                throw new PolicyViolationException(
                    "Qubit capacity exceeded."
                );
            }

            if (circuit.depth() > capability.maximumDepth()) {
                throw new PolicyViolationException(
                    "Circuit depth exceeded."
                );
            }

            if (experiment.shots() > capability.maximumShots()) {
                throw new PolicyViolationException(
                    "Shot budget exceeded."
                );
            }

            if (circuit.usesEntanglement() &&
                !capability.supportsEntanglement()) {
                throw new PolicyViolationException(
                    "Backend does not support entanglement."
                );
            }

            double estimatedFidelity = Math.pow(
                capability.gateFidelity(),
                (double) circuit.depth() * circuit.qubits()
            ) * capability.measurementFidelity();

            if (estimatedFidelity < experiment.minimumFidelity()) {
                throw new PolicyViolationException(
                    "Estimated fidelity is below the required threshold."
                );
            }
        }
    }

    // ========================================================
    // 8. EXPERIMENT SERVICE
    // ========================================================

    static class ExperimentService {

        private final Map<String, QMLExperiment> experiments =
            new java.util.LinkedHashMap<>();

        private final List<AuditEvent> auditLog =
            new ArrayList<>();

        private final DatasetGovernancePolicy datasetPolicy;
        private final CircuitPolicy circuitPolicy;

        ExperimentService() {
            this.datasetPolicy = new DatasetGovernancePolicy();
            this.circuitPolicy = new CircuitPolicy();
        }

        void register(QMLExperiment experiment) {
            Objects.requireNonNull(experiment);

            if (experiments.putIfAbsent(
                experiment.id(), experiment
            ) != null) {
                throw new QMLException("Duplicate experiment.");
            }

            record(experiment, "REGISTERED", "SYSTEM", "Experiment created.");
        }

        QMLExperiment get(String id) {
            QMLExperiment experiment = experiments.get(id);

            if (experiment == null) {
                throw new QMLException("Experiment not found.");
            }

            return experiment;
        }

        void validate(
            String id,
            BackendCapability capability
        ) {
            QMLExperiment experiment = get(id);

            try {
                datasetPolicy.validate(
                    experiment.dataset(),
                    experiment.backend()
                );

                circuitPolicy.validate(experiment, capability);

                experiment.transition(ExperimentStatus.VALIDATED);

                record(
                    experiment,
                    "VALIDATED",
                    "GOVERNANCE_SERVICE",
                    "Dataset and circuit policies passed."
                );

            } catch (RuntimeException exception) {
                if (experiment.status() == ExperimentStatus.CREATED) {
                    experiment.transition(ExperimentStatus.REJECTED);
                }

                record(
                    experiment,
                    "REJECTED",
                    "GOVERNANCE_SERVICE",
                    exception.getMessage()
                );

                throw exception;
            }
        }

        void approve(String id, String approver) {
            QMLExperiment experiment = get(id);

            if (approver == null || approver.isBlank()) {
                throw new QMLException("Approver identity is required.");
            }

            experiment.transition(ExperimentStatus.APPROVED);

            record(
                experiment,
                "APPROVED",
                approver,
                "Experiment governance approval recorded."
            );
        }

        ExperimentMetrics execute(String id) {
            QMLExperiment experiment = get(id);

            experiment.transition(ExperimentStatus.QUEUED);
            record(experiment, "QUEUED", "EXECUTION_SERVICE", "Queued.");

            experiment.transition(ExperimentStatus.RUNNING);
            record(experiment, "RUNNING", "EXECUTION_SERVICE", "Started.");

            try {
                // Demonstration metrics from a deterministic workload.
                // These are illustrative outputs, not hardware measurements.
                double accuracy = 0.875;
                double precision = 0.857;
                double recall = 0.900;

                double loss = 0.231;
                double standardError = 1.0 /
                    Math.sqrt(experiment.shots());

                ExperimentMetrics metrics = new ExperimentMetrics(
                    accuracy,
                    precision,
                    recall,
                    loss,
                    standardError,
                    experiment.shots(),
                    Instant.now()
                );

                experiment.complete(metrics);

                record(
                    experiment,
                    "COMPLETED",
                    "EXECUTION_SERVICE",
                    "Evaluation metrics stored."
                );

                return metrics;

            } catch (RuntimeException exception) {
                experiment.fail(exception.getMessage());

                record(
                    experiment,
                    "FAILED",
                    "EXECUTION_SERVICE",
                    exception.getMessage()
                );

                throw exception;
            }
        }

        private void record(
            QMLExperiment experiment,
            String action,
            String actor,
            String detail
        ) {
            auditLog.add(new AuditEvent(
                experiment.id(),
                action,
                actor,
                Instant.now(),
                detail
            ));
        }

        List<AuditEvent> auditEvents() {
            return List.copyOf(auditLog);
        }

        List<QMLExperiment> allExperiments() {
            return List.copyOf(experiments.values());
        }
    }

    // ========================================================
    // 9. ALGORITHM SELECTION
    // ========================================================

    static AlgorithmFamily selectAlgorithm(
        WorkloadCategory category,
        int datasetSize,
        int availableQubits
    ) {
        if (datasetSize < 1 || availableQubits < 1) {
            throw new QMLException("Invalid workload constraints.");
        }

        return switch (category) {
            case SUPERVISED_LEARNING ->
                AlgorithmFamily.VARIATIONAL_CLASSIFIER;

            case SIMILARITY_LEARNING ->
                datasetSize <= 5000
                    ? AlgorithmFamily.QUANTUM_KERNEL
                    : AlgorithmFamily.QUANTUM_INSPIRED;

            case OPTIMIZATION ->
                availableQubits >= 2
                    ? AlgorithmFamily.QAOA
                    : AlgorithmFamily.QUANTUM_INSPIRED;

            case CHEMISTRY ->
                availableQubits >= 2
                    ? AlgorithmFamily.VQE
                    : AlgorithmFamily.QUANTUM_INSPIRED;

            case GENERATIVE ->
                AlgorithmFamily.QUANTUM_GENERATIVE;

            case REINFORCEMENT ->
                AlgorithmFamily.QUANTUM_REINFORCEMENT;
        };
    }

    // ========================================================
    // 10. RESOURCE REPORTING
    // ========================================================

    record ResourceEstimate(
        long amplitudes,
        long approximateMemoryBytes,
        long approximateGateOperations,
        long measurementOperations
    ) {}

    static ResourceEstimate estimateResources(
        CircuitDefinition circuit,
        int shots
    ) {
        if (circuit.qubits() > 30) {
            throw new QMLException(
                "Exact statevector estimation limited to 30 qubits."
            );
        }

        long amplitudes = 1L << circuit.qubits();

        return new ResourceEstimate(
            amplitudes,
            amplitudes * 16L,
            (long) circuit.depth() * circuit.qubits(),
            (long) shots * circuit.qubits()
        );
    }

    // ========================================================
    // 11. APPLICATION ENTRY POINT
    // ========================================================

    public static void main(String[] args) {

        System.out.println("QUANTUM MACHINE LEARNING");
        System.out.println("ENTERPRISE EXPERIMENT GOVERNANCE\n");

        System.out.println("ALGORITHM CATALOG");

        AlgorithmCatalog.printCatalog();

        Dataset dataset = new Dataset(
            "DATASET-001",
            "Public Synthetic Classification Dataset",
            1000,
            4,
            DataClassification.PUBLIC,
            true,
            true
        );

        CircuitDefinition circuit = new CircuitDefinition(
            4,
            12,
            8,
            true,
            true
        );

        BackendCapability backend = new BackendCapability(
            "Approved Quantum Backend",
            BackendType.QUANTUM_HARDWARE,
            16,
            100,
            50000,
            0.999,
            0.995,
            true,
            true
        );

        QMLExperiment experiment = new QMLExperiment(
            "Hybrid QML Classification Experiment",
            AlgorithmFamily.VARIATIONAL_CLASSIFIER,
            BackendType.QUANTUM_HARDWARE,
            dataset,
            circuit,
            2048,
            0.80
        );

        ExperimentService service = new ExperimentService();

        service.register(experiment);

        System.out.println("\nEXPERIMENT VALIDATION");

        service.validate(experiment.id(), backend);

        System.out.println("Status: " + experiment.status());

        System.out.println("\nGOVERNANCE APPROVAL");

        service.approve(
            experiment.id(),
            "RESEARCH-GOVERNANCE-OFFICER"
        );

        System.out.println("Status: " + experiment.status());

        System.out.println("\nEXECUTION");

        ExperimentMetrics metrics = service.execute(
            experiment.id()
        );

        System.out.println("Accuracy: " + metrics.accuracy());
        System.out.println("Precision: " + metrics.precision());
        System.out.println("Recall: " + metrics.recall());
        System.out.println("Training loss: " + metrics.trainingLoss());
        System.out.println("Measurement standard error: "
            + metrics.standardError());

        System.out.println("\nRESOURCE ESTIMATION");

        ResourceEstimate resources = estimateResources(
            circuit,
            experiment.shots()
        );

        System.out.println(resources);

        System.out.println("\nALGORITHM SELECTION");

        AlgorithmFamily selected = selectAlgorithm(
            WorkloadCategory.SIMILARITY_LEARNING,
            1000,
            8
        );

        System.out.println("Selected: " + selected);

        System.out.println("\nEXPERIMENT REPORT");

        for (QMLExperiment item : service.allExperiments()) {
            System.out.println(
                item.id() + " | " +
                item.name() + " | " +
                item.algorithm() + " | " +
                item.status()
            );
        }

        System.out.println("\nAUDIT EVENTS");

        for (AuditEvent event : service.auditEvents()) {
            System.out.println(
                event.timestamp() + " | " +
                event.action() + " | " +
                event.actor() + " | " +
                event.detail()
            );
        }

        System.out.println("\nEXPECTED POLICY FAILURE TEST");

        Dataset restrictedDataset = new Dataset(
            "DATASET-002",
            "Restricted Research Dataset",
            500,
            4,
            DataClassification.RESTRICTED,
            true,
            true
        );

        QMLExperiment restrictedExperiment = new QMLExperiment(
            "Restricted Data Experiment",
            AlgorithmFamily.VARIATIONAL_CLASSIFIER,
            BackendType.QUANTUM_HARDWARE,
            restrictedDataset,
            circuit,
            1024,
            0.70
        );

        service.register(restrictedExperiment);

        try {
            service.validate(
                restrictedExperiment.id(),
                backend
            );
        } catch (PolicyViolationException exception) {
            System.out.println(
                "Correctly rejected: " + exception.getMessage()
            );
        }
    }
}
