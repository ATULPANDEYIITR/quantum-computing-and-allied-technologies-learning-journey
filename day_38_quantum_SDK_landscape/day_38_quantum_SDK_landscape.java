/*
 * QuantumSdkLandscape.java
 *
 * Enterprise-oriented quantum SDK landscape model.
 *
 * Compile:
 *   javac QuantumSdkLandscape.java
 *
 * Run:
 *   java QuantumSdkLandscape
 */

import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public class QuantumSdkLandscape {

    enum Workload {
        GENERAL_CIRCUIT,
        HARDWARE_COMPILATION,
        QML,
        CLOUD_EXECUTION,
        GPU_SIMULATION,
        RESOURCE_ESTIMATION,
        RESEARCH
    }

    record SdkProfile(
        String name,
        String organization,
        List<String> languages,
        Set<Workload> workloads,
        boolean differentiable,
        boolean compiler,
        boolean hardware,
        boolean cloud,
        boolean simulator,
        List<String> strengths,
        List<String> tradeoffs
    ) {
        SdkProfile {
            Objects.requireNonNull(name);
            Objects.requireNonNull(organization);
            languages = List.copyOf(languages);
            workloads = Set.copyOf(workloads);
            strengths = List.copyOf(strengths);
            tradeoffs = List.copyOf(tradeoffs);
        }
    }

    record WorkloadRequest(
        String name,
        Workload workload,
        boolean requiresDifferentiation,
        boolean requiresGpu,
        boolean requiresCloud,
        boolean requiresCompiler,
        boolean requiresResourceEstimation
    ) {}

    record Recommendation(
        SdkProfile sdk,
        int score,
        List<String> reasons
    ) {}

    enum GateType {
        H,
        RX,
        RY,
        CNOT
    }

    record Gate(
        GateType type,
        List<Integer> qubits,
        Double parameter
    ) {
        Gate {
            if (qubits.isEmpty()) {
                throw new IllegalArgumentException("A gate needs at least one qubit");
            }

            if (qubits.stream().distinct().count() != qubits.size()) {
                throw new IllegalArgumentException(
                    "A gate cannot target the same qubit more than once"
                );
            }

            qubits = List.copyOf(qubits);
        }
    }

    static final class QuantumCircuit {
        private final int qubitCount;
        private final List<Gate> gates = new ArrayList<>();

        QuantumCircuit(int qubitCount) {
            if (qubitCount <= 0) {
                throw new IllegalArgumentException(
                    "A circuit must contain at least one qubit"
                );
            }
            this.qubitCount = qubitCount;
        }

        QuantumCircuit add(
            GateType type,
            Double parameter,
            int... qubits
        ) {
            List<Integer> targets = new ArrayList<>();

            for (int qubit : qubits) {
                if (qubit < 0 || qubit >= qubitCount) {
                    throw new IllegalArgumentException(
                        "Qubit " + qubit + " does not exist"
                    );
                }
                targets.add(qubit);
            }

            gates.add(new Gate(type, targets, parameter));
            return this;
        }

        int depth() {
            int[] availability = new int[qubitCount];

            for (Gate gate : gates) {
                int layer = 0;

                for (int qubit : gate.qubits()) {
                    layer = Math.max(layer, availability[qubit]);
                }

                layer++;

                for (int qubit : gate.qubits()) {
                    availability[qubit] = layer;
                }
            }

            int result = 0;
            for (int layer : availability) {
                result = Math.max(result, layer);
            }

            return result;
        }

        long twoQubitGateCount() {
            return gates.stream()
                .filter(gate -> gate.qubits().size() == 2)
                .count();
        }

        long parameterizedGateCount() {
            return gates.stream()
                .filter(gate -> gate.parameter() != null)
                .count();
        }

        List<Gate> gates() {
            return List.copyOf(gates);
        }
    }

    static final class Repository {
        private final List<SdkProfile> profiles;

        Repository() {
            profiles = List.of(
                new SdkProfile(
                    "Qiskit",
                    "IBM",
                    List.of("Python"),
                    EnumSet.of(
                        Workload.GENERAL_CIRCUIT,
                        Workload.HARDWARE_COMPILATION,
                        Workload.CLOUD_EXECUTION,
                        Workload.RESEARCH
                    ),
                    false,
                    true,
                    true,
                    true,
                    true,
                    List.of(
                        "circuit construction",
                        "transpilation",
                        "IBM hardware integration",
                        "primitive-oriented execution"
                    ),
                    List.of(
                        "provider-specific APIs evolve separately from the core SDK",
                        "hardware performance depends strongly on transpilation"
                    )
                ),
                new SdkProfile(
                    "Cirq",
                    "Google Quantum AI",
                    List.of("Python"),
                    EnumSet.of(
                        Workload.GENERAL_CIRCUIT,
                        Workload.HARDWARE_COMPILATION,
                        Workload.RESEARCH
                    ),
                    false,
                    true,
                    true,
                    false,
                    true,
                    List.of(
                        "moment-oriented circuit representation",
                        "hardware-aware research",
                        "explicit qubit control"
                    ),
                    List.of(
                        "cloud orchestration is not its primary abstraction",
                        "Google hardware workflows may require additional components"
                    )
                ),
                new SdkProfile(
                    "PennyLane",
                    "Xanadu",
                    List.of("Python"),
                    EnumSet.of(
                        Workload.QML,
                        Workload.GENERAL_CIRCUIT,
                        Workload.RESEARCH
                    ),
                    true,
                    true,
                    true,
                    false,
                    true,
                    List.of(
                        "automatic differentiation",
                        "quantum machine learning",
                        "variational algorithms",
                        "hybrid optimization"
                    ),
                    List.of(
                        "gradient computation can require additional device executions",
                        "backend capabilities vary"
                    )
                ),
                new SdkProfile(
                    "pytket / TKET",
                    "Quantinuum",
                    List.of("Python API", "C++ compiler core"),
                    EnumSet.of(
                        Workload.HARDWARE_COMPILATION,
                        Workload.GENERAL_CIRCUIT,
                        Workload.RESEARCH
                    ),
                    false,
                    true,
                    true,
                    false,
                    true,
                    List.of(
                        "routing",
                        "placement",
                        "optimization",
                        "interoperability"
                    ),
                    List.of(
                        "primarily a compiler and circuit transformation layer",
                        "provider integrations can be separate extensions"
                    )
                ),
                new SdkProfile(
                    "Amazon Braket SDK",
                    "AWS",
                    List.of("Python"),
                    EnumSet.of(
                        Workload.CLOUD_EXECUTION,
                        Workload.GENERAL_CIRCUIT,
                        Workload.RESEARCH
                    ),
                    false,
                    false,
                    true,
                    true,
                    true,
                    List.of(
                        "multi-provider cloud access",
                        "hybrid jobs",
                        "AWS infrastructure integration"
                    ),
                    List.of(
                        "cloud execution introduces cost and region constraints",
                        "provider capabilities are not identical"
                    )
                ),
                new SdkProfile(
                    "CUDA-Q",
                    "NVIDIA",
                    List.of("C++", "Python"),
                    EnumSet.of(
                        Workload.GPU_SIMULATION,
                        Workload.HARDWARE_COMPILATION,
                        Workload.GENERAL_CIRCUIT,
                        Workload.RESEARCH
                    ),
                    false,
                    true,
                    true,
                    false,
                    true,
                    List.of(
                        "GPU-accelerated simulation",
                        "hybrid CPU/GPU/QPU workflows",
                        "multiple backends"
                    ),
                    List.of(
                        "accelerated infrastructure is needed to exploit its strongest advantages",
                        "backend capabilities vary"
                    )
                ),
                new SdkProfile(
                    "Microsoft QDK / Q#",
                    "Microsoft",
                    List.of("Q#", "Python"),
                    EnumSet.of(
                        Workload.RESOURCE_ESTIMATION,
                        Workload.CLOUD_EXECUTION,
                        Workload.GENERAL_CIRCUIT,
                        Workload.RESEARCH
                    ),
                    false,
                    true,
                    true,
                    true,
                    true,
                    List.of(
                        "Q# language",
                        "resource estimation",
                        "simulation",
                        "Azure Quantum integration"
                    ),
                    List.of(
                        "Q# uses a distinct language model",
                        "cloud execution requires target and workspace configuration"
                    )
                )
            );
        }

        List<SdkProfile> all() {
            return profiles;
        }

        Recommendation evaluate(
            SdkProfile sdk,
            WorkloadRequest request
        ) {
            int score = 0;
            List<String> reasons = new ArrayList<>();

            if (sdk.workloads().contains(request.workload())) {
                score += 4;
                reasons.add("workload alignment");
            }

            if (request.requiresDifferentiation()) {
                if (sdk.differentiable()) {
                    score += 6;
                    reasons.add("differentiable programming");
                } else {
                    score -= 3;
                }
            }

            if (request.requiresGpu()) {
                if (sdk.name().equals("CUDA-Q")) {
                    score += 7;
                    reasons.add("GPU-oriented simulation");
                }
            }

            if (request.requiresCloud()) {
                if (sdk.cloud()) {
                    score += 5;
                    reasons.add("managed cloud execution");
                } else {
                    score -= 1;
                }
            }

            if (request.requiresCompiler()) {
                if (sdk.compiler()) {
                    score += 5;
                    reasons.add("compiler-oriented architecture");
                } else {
                    score -= 2;
                }
            }

            if (request.requiresResourceEstimation()) {
                if (sdk.name().equals("Microsoft QDK / Q#")) {
                    score += 7;
                    reasons.add("resource-estimation capability");
                } else {
                    score -= 1;
                }
            }

            return new Recommendation(sdk, score, List.copyOf(reasons));
        }

        List<Recommendation> recommend(WorkloadRequest request) {
            return profiles.stream()
                .map(sdk -> evaluate(sdk, request))
                .sorted(
                    Comparator.comparingInt(Recommendation::score)
                        .reversed()
                        .thenComparing(r -> r.sdk().name())
                )
                .toList();
        }
    }

    static QuantumCircuit createBellCircuit() {
        return new QuantumCircuit(2)
            .add(GateType.H, null, 0)
            .add(GateType.CNOT, null, 0, 1);
    }

    static QuantumCircuit createVariationalCircuit(double theta) {
        return new QuantumCircuit(3)
            .add(GateType.RY, theta, 0)
            .add(GateType.RY, theta / 2.0, 1)
            .add(GateType.RY, -theta, 2)
            .add(GateType.CNOT, null, 0, 1)
            .add(GateType.CNOT, null, 1, 2);
    }

    static void printLandscape(Repository repository) {
        System.out.println("QUANTUM SDK LANDSCAPE");
        System.out.println("=".repeat(78));

        for (SdkProfile sdk : repository.all()) {
            System.out.println();
            System.out.println(sdk.name() + " | " + sdk.organization());
            System.out.println("Languages: " + String.join(", ", sdk.languages()));
            System.out.println("Differentiable: " + sdk.differentiable());
            System.out.println("Compiler: " + sdk.compiler());
            System.out.println("Hardware: " + sdk.hardware());
            System.out.println("Cloud: " + sdk.cloud());
            System.out.println("Simulator: " + sdk.simulator());

            System.out.println("Strengths:");
            sdk.strengths().forEach(item ->
                System.out.println("  - " + item)
            );

            System.out.println("Trade-offs:");
            sdk.tradeoffs().forEach(item ->
                System.out.println("  - " + item)
            );
        }
    }

    static void demonstrateCircuitModel() {
        System.out.println("\nCIRCUIT MODEL");
        System.out.println("=".repeat(78));

        QuantumCircuit bell = createBellCircuit();

        System.out.println("Bell circuit:");
        System.out.println("  gates = " + bell.gates().size());
        System.out.println("  depth = " + bell.depth());
        System.out.println("  two-qubit gates = " + bell.twoQubitGateCount());

        QuantumCircuit ansatz = createVariationalCircuit(Math.PI / 3.0);

        System.out.println("\nParameterized ansatz:");
        System.out.println("  gates = " + ansatz.gates().size());
        System.out.println("  depth = " + ansatz.depth());
        System.out.println("  parameterized gates = " + ansatz.parameterizedGateCount());
    }

    static void demonstrateRecommendations(Repository repository) {
        System.out.println("\nENTERPRISE WORKLOAD SELECTION");
        System.out.println("=".repeat(78));

        List<WorkloadRequest> requests = List.of(
            new WorkloadRequest(
                "Variational quantum model",
                Workload.QML,
                true,
                false,
                false,
                false,
                false
            ),
            new WorkloadRequest(
                "Architecture-aware compilation",
                Workload.HARDWARE_COMPILATION,
                false,
                false,
                false,
                true,
                false
            ),
            new WorkloadRequest(
                "Managed cloud experiment",
                Workload.CLOUD_EXECUTION,
                false,
                false,
                true,
                false,
                false
            ),
            new WorkloadRequest(
                "GPU simulation",
                Workload.GPU_SIMULATION,
                false,
                true,
                false,
                false,
                false
            ),
            new WorkloadRequest(
                "Resource estimation",
                Workload.RESOURCE_ESTIMATION,
                false,
                false,
                false,
                false,
                true
            )
        );

        for (WorkloadRequest request : requests) {
            System.out.println("\n" + request.name());

            repository.recommend(request)
                .stream()
                .limit(3)
                .forEach(recommendation ->
                    System.out.println(
                        "  " +
                        String.format(
                            "%-24s score=%2d  %s",
                            recommendation.sdk().name(),
                            recommendation.score(),
                            recommendation.reasons().isEmpty()
                                ? "general compatibility"
                                : recommendation.reasons().get(0)
                        )
                    )
                );
        }
    }

    static void demonstrateFailureHandling() {
        System.out.println("\nVALIDATION");
        System.out.println("=".repeat(78));

        try {
            new QuantumCircuit(2).add(GateType.CNOT, null, 0, 2);
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Invalid qubit rejected: " + error.getMessage()
            );
        }

        try {
            new QuantumCircuit(2).add(GateType.CNOT, null, 1, 1);
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Duplicate target rejected: " + error.getMessage()
            );
        }

        /*
         * Enterprise code should keep circuit validation separate from
         * provider authentication and execution policy. A circuit can be
         * structurally valid but still fail because a target backend does not
         * support its gates, topology, dynamic-circuit features, shot limits,
         * or execution mode.
         */
    }

    public static void main(String[] args) {
        Repository repository = new Repository();

        printLandscape(repository);
        demonstrateCircuitModel();
        demonstrateRecommendations(repository);
        demonstrateFailureHandling();
    }
}
