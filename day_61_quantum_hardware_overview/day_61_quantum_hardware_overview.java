import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class QuantumHardwareEnterprise {

    enum QubitTechnology {
        SUPERCONDUCTING,
        TRAPPED_ION,
        NEUTRAL_ATOM,
        PHOTONIC,
        SPIN
    }

    enum ProcessorState {
        OFFLINE,
        INITIALIZING,
        READY,
        RUNNING,
        FAULT
    }

    enum SubsystemType {
        CRYOGENICS,
        VACUUM,
        OPTICAL_CONTROL,
        MICROWAVE_CONTROL,
        READOUT,
        CLASSICAL_CONTROL
    }

    record Qubit(
            int id,
            QubitTechnology technology,
            double frequencyGHz,
            double coherenceUs,
            double gateFidelity,
            double readoutFidelity) {

        Qubit {
            if (id < 0) {
                throw new IllegalArgumentException("Qubit ID cannot be negative");
            }
            Objects.requireNonNull(technology, "Technology is required");

            if (frequencyGHz < 0 ||
                    coherenceUs <= 0 ||
                    gateFidelity <= 0 ||
                    gateFidelity > 1 ||
                    readoutFidelity <= 0 ||
                    readoutFidelity > 1) {
                throw new IllegalArgumentException("Invalid qubit parameters");
            }
        }
    }

    record HardwareSubsystem(
            SubsystemType type,
            List<String> components,
            List<String> constraints) {

        HardwareSubsystem {
            Objects.requireNonNull(type);
            components = List.copyOf(components);
            constraints = List.copyOf(constraints);

            if (components.isEmpty()) {
                throw new IllegalArgumentException("Subsystem requires components");
            }
        }
    }

    record GateProfile(
            String name,
            double durationNs,
            double errorRate) {

        GateProfile {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Gate name is required");
            }
            if (durationNs <= 0 || errorRate < 0 || errorRate >= 1) {
                throw new IllegalArgumentException("Invalid gate profile");
            }
        }
    }

    record EnvironmentalState(
            double temperatureK,
            double pressurePa,
            boolean readoutAvailable) {

        EnvironmentalState {
            if (temperatureK < 0 || pressurePa < 0) {
                throw new IllegalArgumentException(
                        "Environmental measurements cannot be negative");
            }
        }
    }

    record ExperimentRequest(
            String requester,
            int circuitDepth,
            boolean requiresTwoQubitGates) {

        ExperimentRequest {
            if (requester == null || requester.isBlank()) {
                throw new IllegalArgumentException("Requester is required");
            }
            if (circuitDepth <= 0) {
                throw new IllegalArgumentException("Circuit depth must be positive");
            }
        }
    }

    record ExperimentDecision(
            boolean accepted,
            String reason,
            double estimatedExecutionUs,
            double estimatedError) {
    }

    static final class HardwareException extends Exception {
        HardwareException(String message) {
            super(message);
        }
    }

    interface HardwarePolicy {
        void validate(
                QuantumProcessor processor,
                ExperimentRequest request)
                throws HardwareException;
    }

    static final class DefaultHardwarePolicy implements HardwarePolicy {
        @Override
        public void validate(
                QuantumProcessor processor,
                ExperimentRequest request)
                throws HardwareException {

            if (processor.state() != ProcessorState.READY) {
                throw new HardwareException("Processor is not ready");
            }

            if (request.circuitDepth() > 10_000) {
                throw new HardwareException(
                        "Circuit exceeds enterprise execution depth limit");
            }

            if (request.requiresTwoQubitGates() &&
                    processor.twoQubitGate() == null) {
                throw new HardwareException(
                        "Two-qubit operations are unavailable");
            }
        }
    }

    static final class QuantumProcessor {
        private final String name;
        private final QubitTechnology technology;
        private final Map<Integer, Qubit> qubits;
        private final List<HardwareSubsystem> subsystems;
        private final List<GateProfile> gates;
        private ProcessorState state;
        private EnvironmentalState environment;

        QuantumProcessor(
                String name,
                QubitTechnology technology,
                List<Qubit> qubits,
                List<HardwareSubsystem> subsystems,
                List<GateProfile> gates) {

            this.name = Objects.requireNonNull(name);
            this.technology = Objects.requireNonNull(technology);
            this.qubits = new HashMap<>();
            this.subsystems = List.copyOf(subsystems);
            this.gates = List.copyOf(gates);
            this.state = ProcessorState.OFFLINE;

            for (Qubit qubit : qubits) {
                if (qubit.technology() != technology) {
                    throw new IllegalArgumentException(
                            "Qubit technology conflicts with processor");
                }
                if (this.qubits.putIfAbsent(qubit.id(), qubit) != null) {
                    throw new IllegalArgumentException("Duplicate qubit ID");
                }
            }

            if (this.qubits.isEmpty()) {
                throw new IllegalArgumentException("No qubits configured");
            }
        }

        String name() {
            return name;
        }

        ProcessorState state() {
            return state;
        }

        GateProfile twoQubitGate() {
            return gates.stream()
                    .filter(g -> g.name().toLowerCase().contains("two-qubit"))
                    .findFirst()
                    .orElse(null);
        }

        void initialize(EnvironmentalState environment)
                throws HardwareException {

            if (state != ProcessorState.OFFLINE) {
                throw new HardwareException(
                        "Processor initialization is not allowed from " + state);
            }

            this.environment = environment;
            state = ProcessorState.INITIALIZING;

            if (technology == QubitTechnology.SUPERCONDUCTING &&
                    environment.temperatureK() > 0.1) {
                state = ProcessorState.FAULT;
                throw new HardwareException(
                        "Cryogenic temperature is outside operating range");
            }

            if (!environment.readoutAvailable()) {
                state = ProcessorState.FAULT;
                throw new HardwareException("Readout subsystem unavailable");
            }

            state = ProcessorState.READY;
        }

        double averageCoherenceUs() {
            return qubits.values().stream()
                    .mapToDouble(Qubit::coherenceUs)
                    .average()
                    .orElseThrow();
        }

        double averageGateDurationNs() {
            return gates.stream()
                    .mapToDouble(GateProfile::durationNs)
                    .average()
                    .orElseThrow();
        }

        double averageGateError() {
            return gates.stream()
                    .mapToDouble(GateProfile::errorRate)
                    .average()
                    .orElseThrow();
        }

        ExperimentDecision evaluate(
                ExperimentRequest request,
                HardwarePolicy policy) {

            try {
                policy.validate(this, request);

                double executionUs =
                        request.circuitDepth() *
                        averageGateDurationNs() / 1000.0;

                if (executionUs > averageCoherenceUs()) {
                    return new ExperimentDecision(
                            false,
                            "Estimated execution exceeds average coherence budget",
                            executionUs,
                            0.0);
                }

                double error =
                        1.0 - Math.pow(
                                1.0 - averageGateError(),
                                request.circuitDepth());

                return new ExperimentDecision(
                        true,
                        "Experiment satisfies current hardware policy",
                        executionUs,
                        error);

            } catch (HardwareException error) {
                return new ExperimentDecision(
                        false,
                        error.getMessage(),
                        0.0,
                        0.0);
            }
        }

        void start(ExperimentRequest request, HardwarePolicy policy)
                throws HardwareException {

            ExperimentDecision decision = evaluate(request, policy);

            if (!decision.accepted()) {
                throw new HardwareException(decision.reason());
            }

            state = ProcessorState.RUNNING;

            System.out.printf(
                    "Running %s for %s%nExecution: %.2f us%nEstimated error: %.4f%n",
                    name,
                    request.requester(),
                    decision.estimatedExecutionUs(),
                    decision.estimatedError());

            state = ProcessorState.READY;
        }

        Map<SubsystemType, Integer> componentCounts() {
            Map<SubsystemType, Integer> counts =
                    new EnumMap<>(SubsystemType.class);

            for (HardwareSubsystem subsystem : subsystems) {
                counts.merge(
                        subsystem.type(),
                        subsystem.components().size(),
                        Integer::sum);
            }

            return Collections.unmodifiableMap(counts);
        }
    }

    static QuantumProcessor createProcessor() {
        List<Qubit> qubits = new ArrayList<>();

        for (int id = 0; id < 8; id++) {
            qubits.add(new Qubit(
                    id,
                    QubitTechnology.SUPERCONDUCTING,
                    5.0 + id * 0.03,
                    85.0 - id * 2,
                    0.999 - id * 0.00002,
                    0.985));
        }

        List<HardwareSubsystem> subsystems = List.of(
                new HardwareSubsystem(
                        SubsystemType.CRYOGENICS,
                        List.of(
                                "dilution refrigerator",
                                "mixing chamber",
                                "thermal shielding"),
                        List.of(
                                "thermal load",
                                "vibration",
                                "cooling capacity")),

                new HardwareSubsystem(
                        SubsystemType.MICROWAVE_CONTROL,
                        List.of(
                                "microwave source",
                                "attenuators",
                                "IQ mixer",
                                "filters"),
                        List.of(
                                "phase noise",
                                "crosstalk",
                                "pulse distortion")),

                new HardwareSubsystem(
                        SubsystemType.READOUT,
                        List.of(
                                "readout resonators",
                                "quantum-limited amplifier",
                                "digitizer"),
                        List.of(
                                "noise",
                                "gain stability",
                                "measurement latency")),

                new HardwareSubsystem(
                        SubsystemType.CLASSICAL_CONTROL,
                        List.of(
                                "FPGA controller",
                                "clock source",
                                "control software"),
                        List.of(
                                "latency",
                                "clock synchronization"))
        );

        List<GateProfile> gates = List.of(
                new GateProfile(
                        "single-qubit gate",
                        25.0,
                        0.0009),
                new GateProfile(
                        "two-qubit gate",
                        220.0,
                        0.008),
                new GateProfile(
                        "measurement",
                        700.0,
                        0.015));

        return new QuantumProcessor(
                "Enterprise Cryogenic Processor",
                QubitTechnology.SUPERCONDUCTING,
                qubits,
                subsystems,
                gates);
    }

    public static void main(String[] args) {
        QuantumProcessor processor = createProcessor();

        try {
            processor.initialize(
                    new EnvironmentalState(
                            0.015,
                            1e-7,
                            true));

            HardwarePolicy policy = new DefaultHardwarePolicy();

            System.out.println("Processor: " + processor.name());
            System.out.println("State: " + processor.state());
            System.out.println(
                    "Average coherence: " +
                    processor.averageCoherenceUs() +
                    " us");
            System.out.println(
                    "Subsystem component counts: " +
                    processor.componentCounts());

            List<ExperimentRequest> requests = List.of(
                    new ExperimentRequest(
                            "research-team",
                            100,
                            true),
                    new ExperimentRequest(
                            "verification-team",
                            10_001,
                            false)
            );

            for (ExperimentRequest request : requests) {
                ExperimentDecision decision =
                        processor.evaluate(request, policy);

                System.out.printf(
                        "%nRequest from %s%nAccepted: %s%nReason: %s%n",
                        request.requester(),
                        decision.accepted(),
                        decision.reason());

                if (decision.accepted()) {
                    processor.start(request, policy);
                }
            }

        } catch (HardwareException error) {
            System.err.println(
                    "Hardware workflow failure: " + error.getMessage());
        }
    }
}
