import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/*
 * NISQ Era: Enterprise quantum experiment management.
 *
 * Java 17 implementation covering:
 * - Quantum device inventory
 * - Calibration management
 * - Circuit resource validation
 * - Device connectivity
 * - Noise-aware scheduling
 * - Coherence and error budgets
 * - Experiment lifecycle
 * - Immutable domain records
 * - Enterprise execution policies
 *
 * Compile:
 * javac NISQEnterprise.java
 *
 * Run:
 * java NISQEnterprise
 */

public class NISQEnterprise {

    enum GateType {
        H, X, Y, Z, S, T, CNOT, CZ
    }

    enum DeviceStatus {
        ONLINE, MAINTENANCE, OFFLINE
    }

    enum JobStatus {
        SUBMITTED, VALIDATING, APPROVED,
        REJECTED, RUNNING, COMPLETED,
        FAILED, CANCELLED
    }

    enum Decision {
        APPROVE, REJECT
    }

    static class NISQException extends RuntimeException {
        NISQException(String message) {
            super(message);
        }
    }

    static class InvalidCircuitException extends NISQException {
        InvalidCircuitException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException extends NISQException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    record Gate(
        GateType type,
        List<Integer> qubits
    ) {
        Gate {
            Objects.requireNonNull(type);
            qubits = List.copyOf(qubits);

            int expected =
                type == GateType.CNOT || type == GateType.CZ
                    ? 2 : 1;

            if (qubits.size() != expected) {
                throw new InvalidCircuitException(
                    "Invalid gate arity for " + type
                );
            }

            if (new HashSet<>(qubits).size() != qubits.size()) {
                throw new InvalidCircuitException(
                    "Gate contains duplicate qubits"
                );
            }
        }

        boolean isTwoQubit() {
            return qubits.size() == 2;
        }
    }

    record QuantumCircuit(
        String id,
        String name,
        int qubitCount,
        List<Gate> gates
    ) {
        QuantumCircuit {
            if (id == null || id.isBlank() ||
                name == null || name.isBlank()) {
                throw new InvalidCircuitException(
                    "Circuit identifiers are required"
                );
            }

            if (qubitCount < 1 || qubitCount > 100) {
                throw new InvalidCircuitException(
                    "Invalid qubit count"
                );
            }

            gates = List.copyOf(gates);

            if (gates.isEmpty()) {
                throw new InvalidCircuitException(
                    "Circuit cannot be empty"
                );
            }

            for (Gate gate : gates) {
                for (int qubit : gate.qubits()) {
                    if (qubit < 0 || qubit >= qubitCount) {
                        throw new InvalidCircuitException(
                            "Invalid qubit index: " + qubit
                        );
                    }
                }
            }
        }

        int depth() {
            int[] availability = new int[qubitCount];

            for (Gate gate : gates) {
                int layer = 1;

                for (int q : gate.qubits()) {
                    layer = Math.max(
                        layer,
                        availability[q] + 1
                    );
                }

                for (int q : gate.qubits()) {
                    availability[q] = layer;
                }
            }

            int maximum = 0;

            for (int value : availability) {
                maximum = Math.max(maximum, value);
            }

            return maximum;
        }

        long twoQubitGateCount() {
            return gates.stream()
                .filter(Gate::isTwoQubit)
                .count();
        }

        long singleQubitGateCount() {
            return gates.size() - twoQubitGateCount();
        }
    }

    record Calibration(
        double singleQubitError,
        double twoQubitError,
        double readoutError,
        double coherenceTimeMicros,
        double gateTimeMicros,
        long version,
        Instant calibratedAt
    ) {
        Calibration {
            validateProbability(
                singleQubitError,
                "Single-qubit error"
            );

            validateProbability(
                twoQubitError,
                "Two-qubit error"
            );

            validateProbability(
                readoutError,
                "Readout error"
            );

            if (coherenceTimeMicros <= 0 ||
                gateTimeMicros <= 0 ||
                version < 1) {
                throw new IllegalArgumentException(
                    "Invalid calibration metadata"
                );
            }

            Objects.requireNonNull(calibratedAt);
        }

        private static void validateProbability(
            double value,
            String label
        ) {
            if (!Double.isFinite(value) ||
                value < 0 || value > 1) {
                throw new IllegalArgumentException(
                    label + " must be between 0 and 1"
                );
            }
        }
    }

    record Device(
        String id,
        String name,
        int qubitCapacity,
        Set<String> connectivity,
        Calibration calibration,
        DeviceStatus status
    ) {
        Device {
            if (id == null || id.isBlank() ||
                name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Device identifiers are required"
                );
            }

            if (qubitCapacity < 1) {
                throw new IllegalArgumentException(
                    "Invalid device capacity"
                );
            }

            connectivity = Set.copyOf(connectivity);
            Objects.requireNonNull(calibration);
            Objects.requireNonNull(status);
        }

        static String edge(int a, int b) {
            return Math.min(a, b) + ":" + Math.max(a, b);
        }

        boolean supports(QuantumCircuit circuit) {
            if (status != DeviceStatus.ONLINE ||
                circuit.qubitCount() > qubitCapacity) {
                return false;
            }

            return circuit.gates().stream().allMatch(gate -> {
                if (!gate.isTwoQubit()) {
                    return true;
                }

                return connectivity.contains(
                    edge(gate.qubits().get(0),
                         gate.qubits().get(1))
                );
            });
        }
    }

    record ApprovalPolicy(
        int minimumCalibrationVersion,
        double maximumGateError,
        double minimumSuccessProbability,
        double maximumCoherenceRatio,
        int maximumDepth,
        boolean requireOnlineDevice
    ) {
        ApprovalPolicy {
            if (minimumCalibrationVersion < 1 ||
                maximumGateError < 0 ||
                maximumGateError > 1 ||
                minimumSuccessProbability < 0 ||
                minimumSuccessProbability > 1 ||
                maximumCoherenceRatio <= 0 ||
                maximumDepth < 1) {
                throw new IllegalArgumentException(
                    "Invalid approval policy"
                );
            }
        }
    }

    record NoiseEstimate(
        double gateSuccessProbability,
        double readoutSuccessProbability,
        double coherencePenalty,
        double totalSuccessProbability,
        double durationMicros
    ) {}

    record Evaluation(
        Decision decision,
        List<String> violations,
        NoiseEstimate estimate,
        String deviceId
    ) {
        Evaluation {
            violations = List.copyOf(violations);
        }

        boolean approved() {
            return decision == Decision.APPROVE;
        }
    }

    static class DeviceInventory {
        private final Map<String, Device> devices =
            new ConcurrentHashMap<>();

        void register(Device device) {
            Device previous = devices.putIfAbsent(
                device.id(),
                device
            );

            if (previous != null) {
                throw new NISQException(
                    "Duplicate device registration: " + device.id()
                );
            }
        }

        Device get(String id) {
            Device device = devices.get(id);

            if (device == null) {
                throw new NISQException(
                    "Unknown quantum device: " + id
                );
            }

            return device;
        }

        List<Device> all() {
            return List.copyOf(devices.values());
        }
    }

    static class NoisePolicyService {
        private final ApprovalPolicy policy;

        NoisePolicyService(ApprovalPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        Evaluation evaluate(
            QuantumCircuit circuit,
            Device device
        ) {
            List<String> violations = new ArrayList<>();

            if (policy.requireOnlineDevice() &&
                device.status() != DeviceStatus.ONLINE) {
                violations.add("Device is not online");
            }

            if (circuit.qubitCount() > device.qubitCapacity()) {
                violations.add("Insufficient qubit capacity");
            }

            if (!device.supports(circuit)) {
                violations.add("Unsupported topology");
            }

            Calibration c = device.calibration();

            if (c.version() < policy.minimumCalibrationVersion()) {
                violations.add("Calibration is outdated");
            }

            if (c.singleQubitError() > policy.maximumGateError() ||
                c.twoQubitError() > policy.maximumGateError()) {
                violations.add("Gate error exceeds policy");
            }

            if (circuit.depth() > policy.maximumDepth()) {
                violations.add("Circuit depth exceeds policy");
            }

            double gateSuccess =
                Math.pow(
                    1 - c.singleQubitError(),
                    circuit.singleQubitGateCount()
                ) *
                Math.pow(
                    1 - c.twoQubitError(),
                    circuit.twoQubitGateCount()
                );

            double readoutSuccess = Math.pow(
                1 - c.readoutError(),
                circuit.qubitCount()
            );

            double duration =
                circuit.depth() * c.gateTimeMicros();

            double coherenceRatio =
                duration / c.coherenceTimeMicros();

            double coherencePenalty =
                Math.exp(-coherenceRatio);

            double totalSuccess =
                gateSuccess *
                readoutSuccess *
                coherencePenalty;

            NoiseEstimate estimate = new NoiseEstimate(
                gateSuccess,
                readoutSuccess,
                coherencePenalty,
                totalSuccess,
                duration
            );

            if (coherenceRatio > policy.maximumCoherenceRatio()) {
                violations.add("Coherence budget exceeded");
            }

            if (totalSuccess <
                policy.minimumSuccessProbability()) {
                violations.add("Estimated success below threshold");
            }

            return new Evaluation(
                violations.isEmpty()
                    ? Decision.APPROVE
                    : Decision.REJECT,
                violations,
                estimate,
                device.id()
            );
        }
    }

    static class DeviceSelectionService {
        private final DeviceInventory inventory;
        private final NoisePolicyService policyService;

        DeviceSelectionService(
            DeviceInventory inventory,
            NoisePolicyService policyService
        ) {
            this.inventory = inventory;
            this.policyService = policyService;
        }

        record Selection(Device device, Evaluation evaluation) {}

        Selection select(QuantumCircuit circuit) {
            List<Selection> eligible = inventory.all()
                .stream()
                .map(device -> new Selection(
                    device,
                    policyService.evaluate(circuit, device)
                ))
                .filter(selection ->
                    selection.evaluation().approved()
                )
                .sorted(
                    Comparator.comparingDouble(
                        (Selection s) ->
                            s.evaluation()
                                .estimate()
                                .totalSuccessProbability()
                    ).reversed()
                )
                .collect(Collectors.toList());

            if (eligible.isEmpty()) {
                throw new PolicyViolationException(
                    "No device meets experiment requirements"
                );
            }

            return eligible.get(0);
        }
    }

    static class ExperimentJob {
        private final String id;
        private final QuantumCircuit circuit;
        private final Device device;
        private final int shots;
        private final Evaluation evaluation;
        private final Instant createdAt;

        private JobStatus status;
        private String failureReason;

        ExperimentJob(
            QuantumCircuit circuit,
            Device device,
            int shots,
            Evaluation evaluation
        ) {
            if (shots < 1 || shots > 10_000_000) {
                throw new IllegalArgumentException(
                    "Shot count must be between 1 and 10,000,000"
                );
            }

            this.id = UUID.randomUUID().toString();
            this.circuit = circuit;
            this.device = device;
            this.shots = shots;
            this.evaluation = evaluation;
            this.createdAt = Instant.now();
            this.status = JobStatus.SUBMITTED;
        }

        synchronized void transition(JobStatus next) {
            Map<JobStatus, Set<JobStatus>> allowed = Map.of(
                JobStatus.SUBMITTED,
                Set.of(JobStatus.VALIDATING),
                JobStatus.VALIDATING,
                Set.of(JobStatus.APPROVED, JobStatus.REJECTED),
                JobStatus.APPROVED,
                Set.of(JobStatus.RUNNING, JobStatus.CANCELLED),
                JobStatus.RUNNING,
                Set.of(
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED
                ),
                JobStatus.COMPLETED, Set.of(),
                JobStatus.REJECTED, Set.of(),
                JobStatus.FAILED, Set.of(),
                JobStatus.CANCELLED, Set.of()
            );

            if (!allowed.get(status).contains(next)) {
                throw new NISQException(
                    "Invalid job transition: " +
                    status + " -> " + next
                );
            }

            status = next;
        }

        synchronized void fail(String reason) {
            if (status != JobStatus.RUNNING) {
                throw new NISQException(
                    "Only running jobs can fail"
                );
            }

            failureReason = reason;
            transition(JobStatus.FAILED);
        }

        String id() { return id; }
        JobStatus status() { return status; }
        int shots() { return shots; }
        QuantumCircuit circuit() { return circuit; }
        Device device() { return device; }
        Evaluation evaluation() { return evaluation; }
        Instant createdAt() { return createdAt; }
        String failureReason() { return failureReason; }
    }

    static class ExperimentService {
        private final DeviceSelectionService selectionService;
        private final Map<String, ExperimentJob> jobs =
            new ConcurrentHashMap<>();

        ExperimentService(DeviceSelectionService selectionService) {
            this.selectionService = selectionService;
        }

        ExperimentJob submit(
            QuantumCircuit circuit,
            int shots
        ) {
            if (jobs.size() >= 100_000) {
                throw new NISQException(
                    "Experiment registry capacity reached"
                );
            }

            DeviceSelectionService.Selection selection =
                selectionService.select(circuit);

            ExperimentJob job = new ExperimentJob(
                circuit,
                selection.device(),
                shots,
                selection.evaluation()
            );

            job.transition(JobStatus.VALIDATING);
            job.transition(JobStatus.APPROVED);

            ExperimentJob previous = jobs.putIfAbsent(
                job.id(),
                job
            );

            if (previous != null) {
                throw new NISQException(
                    "Experiment ID collision"
                );
            }

            return job;
        }

        void execute(ExperimentJob job) {
            job.transition(JobStatus.RUNNING);

            // This enterprise demonstration records an execution estimate.
            // It does not connect to a physical quantum processor.
            job.transition(JobStatus.COMPLETED);
        }

        List<ExperimentJob> completedJobs() {
            return jobs.values().stream()
                .filter(job ->
                    job.status() == JobStatus.COMPLETED
                )
                .toList();
        }

        Map<JobStatus, Long> statusReport() {
            Map<JobStatus, Long> report =
                new HashMap<>();

            for (JobStatus status : JobStatus.values()) {
                report.put(status, 0L);
            }

            jobs.values().forEach(job ->
                report.merge(job.status(), 1L, Long::sum)
            );

            return Collections.unmodifiableMap(report);
        }
    }

    static Device createDevice(
        String id,
        String name,
        int qubits,
        Set<String> connectivity,
        double oneQubitError,
        double twoQubitError,
        double readoutError,
        double coherence
    ) {
        Calibration calibration = new Calibration(
            oneQubitError,
            twoQubitError,
            readoutError,
            coherence,
            0.05,
            3,
            Instant.now()
        );

        return new Device(
            id,
            name,
            qubits,
            connectivity,
            calibration,
            DeviceStatus.ONLINE
        );
    }

    static QuantumCircuit bellCircuit() {
        return new QuantumCircuit(
            "BELL-001",
            "Bell State Preparation",
            2,
            List.of(
                new Gate(GateType.H, List.of(0)),
                new Gate(GateType.CNOT, List.of(0, 1))
            )
        );
    }

    static QuantumCircuit ghzCircuit() {
        return new QuantumCircuit(
            "GHZ-001",
            "Four Qubit GHZ State",
            4,
            List.of(
                new Gate(GateType.H, List.of(0)),
                new Gate(GateType.CNOT, List.of(0, 1)),
                new Gate(GateType.CNOT, List.of(1, 2)),
                new Gate(GateType.CNOT, List.of(2, 3))
            )
        );
    }

    static void runTests(
        NoisePolicyService policyService,
        Device device
    ) {
        QuantumCircuit bell = bellCircuit();

        if (bell.depth() != 2) {
            throw new AssertionError("Depth test failed");
        }

        if (bell.twoQubitGateCount() != 1) {
            throw new AssertionError("Gate count test failed");
        }

        Evaluation result = policyService.evaluate(
            bell,
            device
        );

        if (!result.approved()) {
            throw new AssertionError(
                "Bell experiment should be approved: " +
                result.violations()
            );
        }

        try {
            new QuantumCircuit(
                "INVALID",
                "Invalid",
                2,
                List.of(new Gate(
                    GateType.CNOT,
                    List.of(0, 0)
                ))
            );

            throw new AssertionError(
                "Invalid circuit was accepted"
            );

        } catch (InvalidCircuitException expected) {
            // Validation works as intended.
        }

        System.out.println("Java 17 self-tests passed.");
    }

    public static void main(String[] args) {
        try {
            DeviceInventory inventory = new DeviceInventory();

            Device alpha = createDevice(
                "QPU-ALPHA",
                "Superconducting Alpha",
                5,
                Set.of("0:1", "1:2", "2:3", "3:4"),
                0.001,
                0.009,
                0.02,
                100
            );

            Device beta = createDevice(
                "QPU-BETA",
                "Superconducting Beta",
                8,
                Set.of(
                    "0:1", "1:2", "2:3",
                    "3:4", "4:5", "5:6", "6:7"
                ),
                0.002,
                0.015,
                0.03,
                150
            );

            inventory.register(alpha);
            inventory.register(beta);

            ApprovalPolicy approvalPolicy =
                new ApprovalPolicy(
                    2,
                    0.05,
                    0.50,
                    0.50,
                    100,
                    true
                );

            NoisePolicyService policyService =
                new NoisePolicyService(approvalPolicy);

            runTests(policyService, alpha);

            DeviceSelectionService selectionService =
                new DeviceSelectionService(
                    inventory,
                    policyService
                );

            ExperimentService experimentService =
                new ExperimentService(selectionService);

            List<QuantumCircuit> circuits = List.of(
                bellCircuit(),
                ghzCircuit()
            );

            for (QuantumCircuit circuit : circuits) {
                System.out.println(
                    "\nExperiment: " + circuit.name()
                );

                System.out.println(
                    "Qubits: " + circuit.qubitCount()
                );

                System.out.println(
                    "Depth: " + circuit.depth()
                );

                ExperimentJob job =
                    experimentService.submit(circuit, 5000);

                System.out.println("Job: " + job.id());
                System.out.println("Device: " + job.device().name());

                System.out.printf(
                    "Estimated success: %.4f%%%n",
                    job.evaluation()
                        .estimate()
                        .totalSuccessProbability() * 100
                );

                experimentService.execute(job);

                System.out.println(
                    "Final status: " + job.status()
                );
            }

            System.out.println(
                "\nEnterprise experiment report:"
            );

            experimentService.statusReport().forEach(
                (status, count) ->
                    System.out.println(status + ": " + count)
            );

        } catch (NISQException | IllegalArgumentException error) {
            System.err.println(
                "Experiment processing failed: " +
                error.getMessage()
            );

            System.exit(1);
        }
    }
}
