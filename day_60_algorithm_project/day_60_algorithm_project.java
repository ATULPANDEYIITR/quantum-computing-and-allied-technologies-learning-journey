import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.SplittableRandom;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * Enterprise-style quantum experiment service.
 *
 * Algorithms:
 * - Deutsch-Jozsa
 * - Bernstein-Vazirani
 * - Grover search
 * - Quantum Phase Estimation for a one-qubit diagonal unitary
 *
 * The simulator uses dense state vectors and little-endian qubit indexing.
 */
public class QuantumWorkbench {

    private static final int MAX_REGISTER_QUBITS = 12;
    private static final int MAX_SHOTS = 50_000;

    enum Algorithm {
        DEUTSCH_JOZSA,
        BERNSTEIN_VAZIRANI,
        GROVER,
        PHASE_ESTIMATION
    }

    static final class PolicyViolationException extends RuntimeException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    record ExperimentRequest(
        Algorithm algorithm,
        int qubits,
        int shots,
        long seed,
        String secret,
        Set<Integer> markedStates,
        String oracle,
        double phase
    ) {
        ExperimentRequest {
            Objects.requireNonNull(algorithm, "Algorithm is required.");
            markedStates = markedStates == null ? Set.of() : Set.copyOf(markedStates);
            secret = secret == null ? "" : secret;
            oracle = oracle == null ? "" : oracle;
        }
    }

    record ExperimentResult(
        String experimentId,
        Algorithm algorithm,
        Map<String, Long> histogram,
        String interpretation,
        double successMetric,
        Instant completedAt
    ) {
        ExperimentResult {
            Objects.requireNonNull(experimentId);
            Objects.requireNonNull(algorithm);
            histogram = Map.copyOf(histogram);
            Objects.requireNonNull(interpretation);
            Objects.requireNonNull(completedAt);

            if (!Double.isFinite(successMetric) ||
                successMetric < 0.0 || successMetric > 1.0) {
                throw new IllegalArgumentException("Success metric must lie in [0, 1].");
            }
        }
    }

    interface QuantumBackend {
        ExperimentResult execute(ExperimentRequest request);
    }

    interface ExperimentPolicy {
        void validate(ExperimentRequest request);
    }

    static final class DefaultExperimentPolicy implements ExperimentPolicy {
        @Override
        public void validate(ExperimentRequest request) {
            Objects.requireNonNull(request, "Experiment request is required.");

            if (request.qubits() < 1 ||
                request.qubits() > MAX_REGISTER_QUBITS) {
                throw new PolicyViolationException("Qubit count exceeds service limits.");
            }

            if (request.shots() < 1 || request.shots() > MAX_SHOTS) {
                throw new PolicyViolationException("Shot count exceeds service limits.");
            }

            int dimension = 1 << request.qubits();

            switch (request.algorithm()) {
                case DEUTSCH_JOZSA -> {
                    if (!Set.of(
                        "constant-zero",
                        "constant-one",
                        "balanced-parity"
                    ).contains(request.oracle())) {
                        throw new PolicyViolationException(
                            "Invalid Deutsch-Jozsa oracle."
                        );
                    }
                }
                case BERNSTEIN_VAZIRANI -> {
                    if (request.secret().length() != request.qubits() ||
                        !request.secret().matches("[01]+")) {
                        throw new PolicyViolationException(
                            "Secret must be a bit string matching the register size."
                        );
                    }
                }
                case GROVER -> {
                    if (request.markedStates().isEmpty()) {
                        throw new PolicyViolationException(
                            "Grover search requires at least one marked state."
                        );
                    }

                    for (int marked : request.markedStates()) {
                        if (marked < 0 || marked >= dimension) {
                            throw new PolicyViolationException(
                                "Marked state is outside the search space."
                            );
                        }
                    }
                }
                case PHASE_ESTIMATION -> {
                    if (request.qubits() >= MAX_REGISTER_QUBITS) {
                        throw new PolicyViolationException(
                            "Phase estimation requires one extra target qubit."
                        );
                    }

                    if (!Double.isFinite(request.phase()) ||
                        request.phase() < 0.0 || request.phase() >= 1.0) {
                        throw new PolicyViolationException(
                            "Phase must be finite and lie in [0, 1)."
                        );
                    }
                }
            }
        }
    }

    static final class StateVector {
        private final int qubits;
        private final int dimension;
        private final double[] real;
        private final double[] imaginary;

        StateVector(int qubits) {
            this(qubits, 0);
        }

        StateVector(int qubits, int initialBasis) {
            if (qubits < 1 || qubits > MAX_REGISTER_QUBITS) {
                throw new IllegalArgumentException("Invalid state-vector size.");
            }

            this.qubits = qubits;
            this.dimension = 1 << qubits;

            if (initialBasis < 0 || initialBasis >= dimension) {
                throw new IllegalArgumentException("Initial basis state is invalid.");
            }

            this.real = new double[dimension];
            this.imaginary = new double[dimension];
            this.real[initialBasis] = 1.0;
        }

        void hadamard(int qubit) {
            validateQubit(qubit);
            int stride = 1 << qubit;
            double scale = 1.0 / Math.sqrt(2.0);

            for (int block = 0; block < dimension; block += stride * 2) {
                for (int offset = 0; offset < stride; offset++) {
                    int left = block + offset;
                    int right = left + stride;

                    double aReal = real[left];
                    double aImaginary = imaginary[left];
                    double bReal = real[right];
                    double bImaginary = imaginary[right];

                    real[left] = (aReal + bReal) * scale;
                    imaginary[left] = (aImaginary + bImaginary) * scale;
                    real[right] = (aReal - bReal) * scale;
                    imaginary[right] = (aImaginary - bImaginary) * scale;
                }
            }
        }

        void phaseOracle(java.util.function.IntPredicate predicate) {
            Objects.requireNonNull(predicate);

            for (int basis = 0; basis < dimension; basis++) {
                if (predicate.test(basis)) {
                    real[basis] = -real[basis];
                    imaginary[basis] = -imaginary[basis];
                }
            }
        }

        void controlledPhase(int control, int target, double angle) {
            validateQubit(control);
            validateQubit(target);

            if (control == target || !Double.isFinite(angle)) {
                throw new IllegalArgumentException("Invalid controlled phase gate.");
            }

            int controlMask = 1 << control;
            int targetMask = 1 << target;
            double reducedAngle = Math.IEEEremainder(angle, 2.0 * Math.PI);
            double cosine = Math.cos(reducedAngle);
            double sine = Math.sin(reducedAngle);

            for (int basis = 0; basis < dimension; basis++) {
                if ((basis & controlMask) != 0 && (basis & targetMask) != 0) {
                    double oldReal = real[basis];
                    double oldImaginary = imaginary[basis];

                    real[basis] = oldReal * cosine - oldImaginary * sine;
                    imaginary[basis] = oldReal * sine + oldImaginary * cosine;
                }
            }
        }

        void diffuse() {
            double meanReal = 0.0;
            double meanImaginary = 0.0;

            for (int basis = 0; basis < dimension; basis++) {
                meanReal += real[basis];
                meanImaginary += imaginary[basis];
            }

            meanReal /= dimension;
            meanImaginary /= dimension;

            for (int basis = 0; basis < dimension; basis++) {
                real[basis] = 2.0 * meanReal - real[basis];
                imaginary[basis] = 2.0 * meanImaginary - imaginary[basis];
            }
        }

        void inverseQftOnLowRegister(int registerQubits) {
            if (registerQubits < 1 || registerQubits > qubits) {
                throw new IllegalArgumentException("Invalid inverse-QFT register.");
            }

            int size = 1 << registerQubits;
            double scale = 1.0 / Math.sqrt(size);

            // The transformed register occupies the low-order basis bits.
            for (int block = 0; block < dimension; block += size) {
                double[] sourceReal = new double[size];
                double[] sourceImaginary = new double[size];

                System.arraycopy(real, block, sourceReal, 0, size);
                System.arraycopy(imaginary, block, sourceImaginary, 0, size);

                for (int output = 0; output < size; output++) {
                    double sumReal = 0.0;
                    double sumImaginary = 0.0;

                    for (int input = 0; input < size; input++) {
                        double angle = -2.0 * Math.PI * input * output / size;
                        double cosine = Math.cos(angle);
                        double sine = Math.sin(angle);

                        sumReal += sourceReal[input] * cosine -
                                   sourceImaginary[input] * sine;
                        sumImaginary += sourceReal[input] * sine +
                                        sourceImaginary[input] * cosine;
                    }

                    real[block + output] = sumReal * scale;
                    imaginary[block + output] = sumImaginary * scale;
                }
            }
        }

        double probability(int basis) {
            return real[basis] * real[basis] +
                   imaginary[basis] * imaginary[basis];
        }

        int sample(int measuredRegisterQubits, SplittableRandom random) {
            if (measuredRegisterQubits < 1 ||
                measuredRegisterQubits > qubits) {
                throw new IllegalArgumentException("Invalid measurement register.");
            }

            int registerSize = 1 << measuredRegisterQubits;
            int mask = registerSize - 1;
            double[] probabilities = new double[registerSize];

            for (int basis = 0; basis < dimension; basis++) {
                probabilities[basis & mask] += probability(basis);
            }

            double threshold = random.nextDouble();
            double cumulative = 0.0;

            for (int outcome = 0; outcome < registerSize; outcome++) {
                cumulative += probabilities[outcome];
                if (threshold < cumulative) {
                    return outcome;
                }
            }

            return registerSize - 1;
        }

        double probabilityOf(java.util.function.IntPredicate predicate) {
            double total = 0.0;

            for (int basis = 0; basis < dimension; basis++) {
                if (predicate.test(basis)) {
                    total += probability(basis);
                }
            }

            return total;
        }

        private void validateQubit(int qubit) {
            if (qubit < 0 || qubit >= qubits) {
                throw new IllegalArgumentException("Invalid qubit index.");
            }
        }
    }

    static final class StateVectorBackend implements QuantumBackend {
        @Override
        public ExperimentResult execute(ExperimentRequest request) {
            SplittableRandom random = new SplittableRandom(request.seed());

            return switch (request.algorithm()) {
                case DEUTSCH_JOZSA -> runDeutschJozsa(request, random);
                case BERNSTEIN_VAZIRANI -> runBernsteinVazirani(request, random);
                case GROVER -> runGrover(request, random);
                case PHASE_ESTIMATION -> runPhaseEstimation(request, random);
            };
        }

        private ExperimentResult runDeutschJozsa(
            ExperimentRequest request,
            SplittableRandom random
        ) {
            StateVector state = new StateVector(request.qubits());
            applyHadamards(state, request.qubits());

            switch (request.oracle()) {
                case "constant-zero" -> {
                    // The zero oracle applies no phase change.
                }
                case "constant-one" -> state.phaseOracle(basis -> true);
                case "balanced-parity" -> state.phaseOracle(
                    basis -> Integer.bitCount(basis & 1) % 2 == 1
                );
                default -> throw new PolicyViolationException("Invalid oracle.");
            }

            applyHadamards(state, request.qubits());

            Map<String, Long> histogram = sampleHistogram(
                state, request.qubits(), request.shots(), random
            );

            String zero = "0".repeat(request.qubits());
            long zeroCount = histogram.getOrDefault(zero, 0L);
            boolean balanced = zeroCount < request.shots();

            double confidence = balanced
                ? (double) (request.shots() - zeroCount) / request.shots()
                : (double) zeroCount / request.shots();

            return result(
                request,
                histogram,
                balanced ? "balanced" : "constant",
                confidence
            );
        }

        private ExperimentResult runBernsteinVazirani(
            ExperimentRequest request,
            SplittableRandom random
        ) {
            int secretValue = Integer.parseInt(request.secret(), 2);
            StateVector state = new StateVector(request.qubits());
            applyHadamards(state, request.qubits());

            state.phaseOracle(
                basis -> Integer.bitCount(basis & secretValue) % 2 == 1
            );

            applyHadamards(state, request.qubits());

            Map<String, Long> histogram = sampleHistogram(
                state, request.qubits(), request.shots(), random
            );

            String expected = request.secret();
            long recovered = histogram.getOrDefault(expected, 0L);

            return result(
                request,
                histogram,
                recovered == request.shots()
                    ? "secret recovered"
                    : "measurement mismatch",
                (double) recovered / request.shots()
            );
        }

        private ExperimentResult runGrover(
            ExperimentRequest request,
            SplittableRandom random
        ) {
            StateVector state = new StateVector(request.qubits());
            applyHadamards(state, request.qubits());

            Set<Integer> marked = request.markedStates();
            int dimension = 1 << request.qubits();

            double theta = Math.asin(Math.sqrt(
                (double) marked.size() / dimension
            ));
            int iterations = Math.max(
                0,
                (int) Math.floor(Math.PI / (4.0 * theta) - 0.5)
            );

            for (int iteration = 0; iteration < iterations; iteration++) {
                state.phaseOracle(marked::contains);
                state.diffuse();
            }

            double theoreticalSuccess = state.probabilityOf(marked::contains);

            Map<String, Long> histogram = sampleHistogram(
                state, request.qubits(), request.shots(), random
            );

            long successfulShots = histogram.entrySet().stream()
                .filter(entry -> marked.contains(
                    Integer.parseInt(entry.getKey(), 2)
                ))
                .mapToLong(Map.Entry::getValue)
                .sum();

            return result(
                request,
                histogram,
                "Grover search; " + iterations + " iterations",
                theoreticalSuccess
            );
        }

        private ExperimentResult runPhaseEstimation(
            ExperimentRequest request,
            SplittableRandom random
        ) {
            int countingQubits = request.qubits();
            int targetQubit = countingQubits;

            // The target is |1>, an eigenstate of diag(1, exp(2*pi*i*phase)).
            StateVector state = new StateVector(
                countingQubits + 1,
                1 << targetQubit
            );

            for (int qubit = 0; qubit < countingQubits; qubit++) {
                state.hadamard(qubit);
            }

            for (int control = 0; control < countingQubits; control++) {
                double angle = 2.0 * Math.PI * request.phase() * (1 << control);
                state.controlledPhase(control, targetQubit, angle);
            }

            state.inverseQftOnLowRegister(countingQubits);

            Map<String, Long> histogram = new LinkedHashMap<>();

            for (int shot = 0; shot < request.shots(); shot++) {
                int outcome = state.sample(countingQubits, random);
                String bits = formatBits(outcome, countingQubits);
                histogram.merge(bits, 1L, Long::sum);
            }

            String mostFrequent = histogram.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .orElseThrow()
                .getKey();

            double estimatedPhase =
                Integer.parseInt(mostFrequent, 2) / (double) (1 << countingQubits);

            return result(
                request,
                histogram,
                String.format(
                    "estimated phase %.6f; absolute error %.6f",
                    estimatedPhase,
                    Math.abs(request.phase() - estimatedPhase)
                ),
                (double) histogram.get(mostFrequent) / request.shots()
            );
        }

        private static void applyHadamards(StateVector state, int qubits) {
            for (int qubit = 0; qubit < qubits; qubit++) {
                state.hadamard(qubit);
            }
        }

        private static Map<String, Long> sampleHistogram(
            StateVector state,
            int qubits,
            int shots,
            SplittableRandom random
        ) {
            Map<String, Long> histogram = new LinkedHashMap<>();

            for (int shot = 0; shot < shots; shot++) {
                int outcome = state.sample(qubits, random);
                histogram.merge(formatBits(outcome, qubits), 1L, Long::sum);
            }

            return histogram;
        }

        private static ExperimentResult result(
            ExperimentRequest request,
            Map<String, Long> histogram,
            String interpretation,
            double metric
        ) {
            return new ExperimentResult(
                "QW-" + request.algorithm() + "-" + request.seed(),
                request.algorithm(),
                histogram,
                interpretation,
                Math.max(0.0, Math.min(1.0, metric)),
                Instant.now()
            );
        }
    }

    static final class ExperimentService implements AutoCloseable {
        private final QuantumBackend backend;
        private final ExperimentPolicy policy;
        private final ExecutorService executor;

        ExperimentService(
            QuantumBackend backend,
            ExperimentPolicy policy,
            int workerCount
        ) {
            this.backend = Objects.requireNonNull(backend);
            this.policy = Objects.requireNonNull(policy);

            if (workerCount < 1 || workerCount > 16) {
                throw new IllegalArgumentException("Worker count must be between 1 and 16.");
            }

            this.executor = Executors.newFixedThreadPool(workerCount);
        }

        CompletableFuture<ExperimentResult> submit(ExperimentRequest request) {
            // Validate before consuming a worker thread.
            policy.validate(request);
            return CompletableFuture.supplyAsync(
                () -> backend.execute(request),
                executor
            );
        }

        @Override
        public void close() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    static String formatBits(int value, int width) {
        return String.format("%" + width + "s", Integer.toBinaryString(value))
            .replace(' ', '0');
    }

    public static void main(String[] args) throws Exception {
        QuantumBackend backend = new StateVectorBackend();
        ExperimentPolicy policy = new DefaultExperimentPolicy();

        try (ExperimentService service = new ExperimentService(
            backend, policy, 3
        )) {
            var deutschJozsa = new ExperimentRequest(
                Algorithm.DEUTSCH_JOZSA,
                3,
                64,
                101L,
                "",
                Set.of(),
                "balanced-parity",
                0.0
            );

            var bernsteinVazirani = new ExperimentRequest(
                Algorithm.BERNSTEIN_VAZIRANI,
                4,
                64,
                102L,
                "1011",
                Set.of(),
                "",
                0.0
            );

            var grover = new ExperimentRequest(
                Algorithm.GROVER,
                3,
                2000,
                103L,
                "",
                Set.of(5),
                "",
                0.0
            );

            var phaseEstimation = new ExperimentRequest(
                Algorithm.PHASE_ESTIMATION,
                4,
                128,
                104L,
                "",
                Set.of(),
                "",
                5.0 / 16.0
            );

            var futures = new ArrayList<CompletableFuture<ExperimentResult>>();
            futures.add(service.submit(deutschJozsa));
            futures.add(service.submit(bernsteinVazirani));
            futures.add(service.submit(grover));
            futures.add(service.submit(phaseEstimation));

            for (CompletableFuture<ExperimentResult> future : futures) {
                ExperimentResult result = future.get();

                System.out.println("\n" + result.algorithm());
                System.out.println("Interpretation: " + result.interpretation());
                System.out.println("Success metric: " + result.successMetric());
                System.out.println("Histogram: " + result.histogram());
                System.out.println("Completed: " + result.completedAt());
            }
        }

        // Invalid requests are rejected by policy before backend execution.
        try {
            policy.validate(new ExperimentRequest(
                Algorithm.BERNSTEIN_VAZIRANI,
                4,
                100,
                105L,
                "10X1",
                Set.of(),
                "",
                0.0
            ));
            throw new IllegalStateException("Invalid secret was not rejected.");
        } catch (PolicyViolationException expected) {
            System.out.println("\nValidation correctly rejected an invalid secret.");
        }
    }
}
