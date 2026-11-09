import java.util.*;
import java.util.stream.Collectors;

/**
 * Quantum Hardware Architecture Enterprise Evaluation System.
 *
 * Java 17
 * No third-party dependencies.
 *
 * Features:
 * - Immutable architecture records
 * - Architecture registry
 * - Configurable evaluation policies
 * - Application-specific decision rules
 * - Reviewable comparison results
 * - Validation and custom exceptions
 * - Explicit evidence maturity
 */

public class QuantumHardwareEnterprise {

    enum ArchitectureType {
        SUPERCONDUCTING,
        TRAPPED_ION,
        NEUTRAL_ATOM,
        PHOTONIC,
        SEMICONDUCTOR_SPIN,
        TOPOLOGICAL
    }

    enum EvidenceLevel {
        MATURE,
        ESTABLISHED,
        DEVELOPING,
        EXPERIMENTAL
    }

    enum Application {
        QUANTUM_SIMULATION,
        OPTIMIZATION,
        QUANTUM_NETWORKING,
        ERROR_CORRECTION_RESEARCH,
        GENERAL_PURPOSE
    }

    record Metrics(
        int gateSpeed,
        int coherence,
        int connectivity,
        int scalability,
        int engineeringMaturity,
        int controlIntegration,
        int errorCorrectionProgress
    ) {
        Metrics {
            int[] values = {
                gateSpeed,
                coherence,
                connectivity,
                scalability,
                engineeringMaturity,
                controlIntegration,
                errorCorrectionProgress
            };

            for (int value : values) {
                if (value < 1 || value > 5) {
                    throw new IllegalArgumentException(
                        "Metric scores must be between 1 and 5."
                    );
                }
            }
        }
    }

    record Architecture(
        ArchitectureType type,
        String name,
        String physicalQubit,
        String operatingEnvironment,
        Metrics metrics,
        EvidenceLevel evidenceLevel,
        List<String> strengths,
        List<String> limitations
    ) {
        Architecture {
            Objects.requireNonNull(type);
            Objects.requireNonNull(metrics);
            Objects.requireNonNull(evidenceLevel);

            if (
                name == null || name.isBlank() ||
                physicalQubit == null || physicalQubit.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Architecture identity is required."
                );
            }

            strengths = List.copyOf(strengths);
            limitations = List.copyOf(limitations);

            if (strengths.isEmpty() || limitations.isEmpty()) {
                throw new IllegalArgumentException(
                    "Strengths and limitations cannot be empty."
                );
            }
        }
    }

    record Weights(
        double gateSpeed,
        double coherence,
        double connectivity,
        double scalability,
        double engineeringMaturity,
        double controlIntegration,
        double errorCorrectionProgress
    ) {
        Weights {
            double[] values = {
                gateSpeed,
                coherence,
                connectivity,
                scalability,
                engineeringMaturity,
                controlIntegration,
                errorCorrectionProgress
            };

            double total = 0;

            for (double value : values) {
                if (!Double.isFinite(value) || value < 0) {
                    throw new IllegalArgumentException(
                        "Weights must be finite and non-negative."
                    );
                }

                total += value;
            }

            if (Math.abs(total - 1.0) > 1e-9) {
                throw new IllegalArgumentException(
                    "Weights must sum to 1."
                );
            }
        }

        static Weights standard() {
            return new Weights(
                0.15, 0.15, 0.10, 0.20,
                0.15, 0.10, 0.15
            );
        }
    }

    record EvaluationResult(
        Architecture architecture,
        double score,
        String assessment
    ) {}

    record ComparisonResult(
        String first,
        String second,
        double firstScore,
        double secondScore,
        double difference
    ) {}

    static class ArchitectureException
            extends RuntimeException {

        ArchitectureException(String message) {
            super(message);
        }
    }

    interface EvaluationPolicy {
        double evaluate(Architecture architecture);
    }

    static class WeightedEvaluationPolicy
            implements EvaluationPolicy {

        private final Weights weights;

        WeightedEvaluationPolicy(Weights weights) {
            this.weights = Objects.requireNonNull(weights);
        }

        @Override
        public double evaluate(Architecture architecture) {
            Metrics m = architecture.metrics();

            double score =
                m.gateSpeed() * weights.gateSpeed() +
                m.coherence() * weights.coherence() +
                m.connectivity() * weights.connectivity() +
                m.scalability() * weights.scalability() +
                m.engineeringMaturity() *
                    weights.engineeringMaturity() +
                m.controlIntegration() *
                    weights.controlIntegration() +
                m.errorCorrectionProgress() *
                    weights.errorCorrectionProgress();

            return Math.round(score * 1000.0) / 1000.0;
        }
    }

    static class ArchitectureRegistry {

        private final Map<ArchitectureType, Architecture> records =
            new EnumMap<>(ArchitectureType.class);

        void register(Architecture architecture) {
            Architecture previous = records.putIfAbsent(
                architecture.type(),
                architecture
            );

            if (previous != null) {
                throw new ArchitectureException(
                    "Duplicate architecture: " + architecture.type()
                );
            }
        }

        Architecture get(ArchitectureType type) {
            Architecture architecture = records.get(type);

            if (architecture == null) {
                throw new ArchitectureException(
                    "Architecture not registered: " + type
                );
            }

            return architecture;
        }

        List<Architecture> all() {
            return List.copyOf(records.values());
        }
    }

    static class ApplicationPolicy {

        private static final Map<Application, Set<ArchitectureType>>
            PREFERRED_ARCHITECTURES = Map.of(
                Application.QUANTUM_NETWORKING,
                Set.of(
                    ArchitectureType.PHOTONIC,
                    ArchitectureType.TRAPPED_ION
                ),
                Application.QUANTUM_SIMULATION,
                Set.of(
                    ArchitectureType.NEUTRAL_ATOM,
                    ArchitectureType.SUPERCONDUCTING,
                    ArchitectureType.TRAPPED_ION
                ),
                Application.OPTIMIZATION,
                Set.of(
                    ArchitectureType.SUPERCONDUCTING,
                    ArchitectureType.NEUTRAL_ATOM
                ),
                Application.ERROR_CORRECTION_RESEARCH,
                Set.of(
                    ArchitectureType.SUPERCONDUCTING,
                    ArchitectureType.TRAPPED_ION,
                    ArchitectureType.NEUTRAL_ATOM
                ),
                Application.GENERAL_PURPOSE,
                Set.of(
                    ArchitectureType.SUPERCONDUCTING,
                    ArchitectureType.TRAPPED_ION,
                    ArchitectureType.NEUTRAL_ATOM
                )
            );

        boolean isCandidate(
            Architecture architecture,
            Application application
        ) {
            if (
                architecture.evidenceLevel() ==
                EvidenceLevel.EXPERIMENTAL
            ) {
                return false;
            }

            return PREFERRED_ARCHITECTURES
                .get(application)
                .contains(architecture.type());
        }

        String explain(
            Architecture architecture,
            Application application
        ) {
            if (architecture.evidenceLevel() == EvidenceLevel.EXPERIMENTAL) {
                return "Experimental evidence is insufficient for a production recommendation.";
            }

            return isCandidate(architecture, application)
                ? "Candidate for application-specific technical evaluation."
                : "Not selected by this application's initial screening policy.";
        }
    }

    static class EvaluationService {

        private final ArchitectureRegistry registry;
        private final EvaluationPolicy policy;
        private final ApplicationPolicy applicationPolicy;

        EvaluationService(
            ArchitectureRegistry registry,
            EvaluationPolicy policy,
            ApplicationPolicy applicationPolicy
        ) {
            this.registry = registry;
            this.policy = policy;
            this.applicationPolicy = applicationPolicy;
        }

        List<EvaluationResult> rank() {
            return registry.all()
                .stream()
                .map(architecture -> new EvaluationResult(
                    architecture,
                    policy.evaluate(architecture),
                    architecture.evidenceLevel().name()
                ))
                .sorted(
                    Comparator.comparingDouble(
                        EvaluationResult::score
                    ).reversed()
                )
                .toList();
        }

        ComparisonResult compare(
            ArchitectureType firstType,
            ArchitectureType secondType
        ) {
            Architecture first = registry.get(firstType);
            Architecture second = registry.get(secondType);

            double a = policy.evaluate(first);
            double b = policy.evaluate(second);

            return new ComparisonResult(
                first.name(),
                second.name(),
                a,
                b,
                Math.round((a - b) * 1000.0) / 1000.0
            );
        }

        List<String> evaluateApplication(Application application) {
            return registry.all()
                .stream()
                .map(architecture -> {
                    boolean candidate =
                        applicationPolicy.isCandidate(
                            architecture,
                            application
                        );

                    return architecture.name() +
                        " | Candidate: " + candidate +
                        " | " + applicationPolicy.explain(
                            architecture,
                            application
                        );
                })
                .collect(Collectors.toList());
        }
    }

    private static Architecture create(
        ArchitectureType type,
        String name,
        String qubit,
        String environment,
        Metrics metrics,
        EvidenceLevel evidence,
        List<String> strengths,
        List<String> limitations
    ) {
        return new Architecture(
            type,
            name,
            qubit,
            environment,
            metrics,
            evidence,
            strengths,
            limitations
        );
    }

    static ArchitectureRegistry buildRegistry() {
        ArchitectureRegistry registry = new ArchitectureRegistry();

        registry.register(create(
            ArchitectureType.SUPERCONDUCTING,
            "Superconducting",
            "Josephson-junction superconducting circuit",
            "Millikelvin dilution refrigerator",
            new Metrics(5, 2, 3, 4, 5, 4, 4),
            EvidenceLevel.MATURE,
            List.of(
                "Fast microwave gates",
                "Established fabrication ecosystem",
                "Strong control integration"
            ),
            List.of(
                "Cryogenic infrastructure",
                "Coherence limitations",
                "Calibration complexity"
            )
        ));

        registry.register(create(
            ArchitectureType.TRAPPED_ION,
            "Trapped Ion",
            "Electromagnetically confined atomic ion",
            "Ultra-high vacuum and laser systems",
            new Metrics(2, 5, 4, 3, 4, 3, 4),
            EvidenceLevel.ESTABLISHED,
            List.of(
                "Long coherence",
                "High-fidelity operations",
                "Flexible interactions"
            ),
            List.of(
                "Slower gates",
                "Optical engineering complexity"
            )
        ));

        registry.register(create(
            ArchitectureType.NEUTRAL_ATOM,
            "Neutral Atom",
            "Laser-trapped neutral atom",
            "Ultra-high vacuum and optical trapping",
            new Metrics(3, 4, 5, 5, 3, 3, 3),
            EvidenceLevel.DEVELOPING,
            List.of(
                "Large programmable atom arrays",
                "Flexible connectivity",
                "Potential scalability"
            ),
            List.of(
                "Atom loss",
                "Rydberg-state sensitivity",
                "Gate fidelity challenges"
            )
        ));

        registry.register(create(
            ArchitectureType.PHOTONIC,
            "Photonic",
            "Single photons and optical modes",
            "Optical systems",
            new Metrics(4, 4, 3, 4, 2, 3, 3),
            EvidenceLevel.DEVELOPING,
            List.of(
                "Networking compatibility",
                "Potential room-temperature operation"
            ),
            List.of(
                "Photon loss",
                "Detector requirements",
                "Probabilistic operations in many approaches"
            )
        ));

        registry.register(create(
            ArchitectureType.SEMICONDUCTOR_SPIN,
            "Semiconductor Spin",
            "Electron or nuclear spin",
            "Cryogenic solid-state device",
            new Metrics(4, 4, 2, 4, 2, 4, 2),
            EvidenceLevel.DEVELOPING,
            List.of(
                "Semiconductor fabrication compatibility",
                "Compact device potential",
                "Electronic integration"
            ),
            List.of(
                "Device variability",
                "Control complexity",
                "Connectivity limitations"
            )
        ));

        registry.register(create(
            ArchitectureType.TOPOLOGICAL,
            "Topological",
            "Proposed non-Abelian anyonic states",
            "Platform-dependent specialized conditions",
            new Metrics(2, 5, 2, 3, 1, 1, 1),
            EvidenceLevel.EXPERIMENTAL,
            List.of(
                "Potential protection against certain local errors"
            ),
            List.of(
                "Experimental realization remains difficult",
                "Usable topological qubits unproven",
                "Fault-tolerant operation unestablished"
            )
        ));

        return registry;
    }

    static void runTests(
        ArchitectureRegistry registry,
        EvaluationService service
    ) {
        if (registry.all().size() != 6) {
            throw new IllegalStateException(
                "Expected six architectures."
            );
        }

        if (service.rank().size() != 6) {
            throw new IllegalStateException(
                "Ranking count is incorrect."
            );
        }

        boolean invalidRejected = false;

        try {
            new Metrics(6, 2, 3, 4, 5, 4, 4);
        } catch (IllegalArgumentException exception) {
            invalidRejected = true;
        }

        if (!invalidRejected) {
            throw new IllegalStateException(
                "Invalid metric was accepted."
            );
        }

        System.out.println("All validation tests passed.");
    }

    public static void main(String[] args) {

        ArchitectureRegistry registry = buildRegistry();

        EvaluationService service = new EvaluationService(
            registry,
            new WeightedEvaluationPolicy(Weights.standard()),
            new ApplicationPolicy()
        );

        runTests(registry, service);

        System.out.println("\nQUANTUM HARDWARE EVALUATION");
        System.out.println(
            "Qualitative scores; not measured hardware benchmarks."
        );

        List<EvaluationResult> results = service.rank();

        int position = 1;

        for (EvaluationResult result : results) {
            Architecture architecture = result.architecture();

            System.out.println(
                "\n" + position++ + ". " + architecture.name()
            );

            System.out.println("Score: " + result.score() + "/5");
            System.out.println(
                "Physical qubit: " + architecture.physicalQubit()
            );
            System.out.println(
                "Environment: " + architecture.operatingEnvironment()
            );
            System.out.println(
                "Evidence: " + architecture.evidenceLevel()
            );

            System.out.println("Strengths: " + architecture.strengths());
            System.out.println(
                "Limitations: " + architecture.limitations()
            );
        }

        System.out.println("\nPAIRWISE COMPARISON");

        System.out.println(
            service.compare(
                ArchitectureType.SUPERCONDUCTING,
                ArchitectureType.TRAPPED_ION
            )
        );

        System.out.println("\nAPPLICATION SCREENING");

        service.evaluateApplication(
            Application.QUANTUM_SIMULATION
        ).forEach(System.out::println);
    }
}
