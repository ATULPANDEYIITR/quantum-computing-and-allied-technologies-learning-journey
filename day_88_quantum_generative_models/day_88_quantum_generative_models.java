/*
 * Quantum Generative Models
 * Enterprise Quantum Generative Learning Framework.
 *
 * Java 17
 *
 * Implements:
 * - Quantum circuit statevector execution
 * - Born machine probability generation
 * - Parameter optimization through SPSA
 * - Measurement sampling
 * - Experiment lifecycle management
 * - Validation and policy-based evaluation
 *
 * Compile:
 * javac QuantumGenerativeLearning.java
 *
 * Run:
 * java QuantumGenerativeLearning
 */

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.Random;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.IntStream;

public class QuantumGenerativeLearning {

    private static final double EPSILON = 1e-12;
    private static final double PI = Math.PI;

    enum ExperimentStatus {
        CREATED,
        VALIDATED,
        TRAINING,
        COMPLETED,
        FAILED
    }

    enum Metric {
        KL_DIVERGENCE,
        TOTAL_VARIATION,
        GENERATED_ENTROPY
    }

    record ModelConfig(
        int qubits,
        double learningRate,
        int iterations,
        int shots,
        long seed
    ) {
        ModelConfig {
            if (qubits < 1 || qubits > 12) {
                throw new IllegalArgumentException(
                    "Qubits must be between 1 and 12."
                );
            }

            if (!Double.isFinite(learningRate) ||
                learningRate <= 0) {
                throw new IllegalArgumentException(
                    "Invalid learning rate."
                );
            }

            if (iterations <= 0 || shots <= 0) {
                throw new IllegalArgumentException(
                    "Iterations and shots must be positive."
                );
            }
        }

        int dimension() {
            return 1 << qubits;
        }
    }

    record TrainingRecord(
        int iteration,
        double loss,
        double learningRate
    ) {}

    record Evaluation(
        double klDivergence,
        double totalVariation,
        double entropy,
        List<Double> probabilities
    ) {}

    record ExperimentReport(
        UUID experimentId,
        ExperimentStatus status,
        double initialLoss,
        double finalLoss,
        Evaluation evaluation,
        List<TrainingRecord> history,
        Map<String, Integer> samples
    ) {}

    interface EvaluationPolicy {
        double evaluate(
            List<Double> target,
            List<Double> generated
        );
    }

    static class QuantumLearningException extends RuntimeException {
        QuantumLearningException(String message) {
            super(message);
        }
    }

    static class ProbabilityDistribution {
        private final List<Double> values;

        ProbabilityDistribution(List<Double> raw) {
            Objects.requireNonNull(raw);

            if (raw.isEmpty()) {
                throw new IllegalArgumentException(
                    "Empty distribution."
                );
            }

            double total = 0.0;

            for (double value : raw) {
                if (!Double.isFinite(value) || value < 0) {
                    throw new IllegalArgumentException(
                        "Invalid probability."
                    );
                }

                total += value;
            }

            if (total <= EPSILON) {
                throw new IllegalArgumentException(
                    "Zero probability mass."
                );
            }

            List<Double> normalized = new ArrayList<>();

            for (double value : raw) {
                normalized.add(value / total);
            }

            this.values = List.copyOf(normalized);
        }

        List<Double> values() {
            return values;
        }

        int size() {
            return values.size();
        }
    }

    static class QuantumCircuit {
        private final int qubits;
        private final int dimension;

        QuantumCircuit(int qubits) {
            if (qubits < 1 || qubits > 12) {
                throw new IllegalArgumentException(
                    "Unsupported qubit count."
                );
            }

            this.qubits = qubits;
            this.dimension = 1 << qubits;
        }

        private void applyRY(
            double[] real,
            double[] imaginary,
            int qubit,
            double theta
        ) {
            int mask = 1 << (qubits - 1 - qubit);

            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);

            for (int i = 0; i < dimension; i++) {
                if ((i & mask) != 0) continue;

                int j = i | mask;

                double ar = real[i];
                double ai = imaginary[i];

                double br = real[j];
                double bi = imaginary[j];

                real[i] = c * ar - s * br;
                imaginary[i] = c * ai - s * bi;

                real[j] = s * ar + c * br;
                imaginary[j] = s * ai + c * bi;
            }
        }

        private void applyCNOT(
            double[] real,
            double[] imaginary,
            int control,
            int target
        ) {
            if (control == target ||
                control < 0 || target < 0 ||
                control >= qubits || target >= qubits) {
                throw new IllegalArgumentException(
                    "Invalid CNOT gate."
                );
            }

            int controlMask = 1 << (qubits - 1 - control);
            int targetMask = 1 << (qubits - 1 - target);

            for (int i = 0; i < dimension; i++) {
                if ((i & controlMask) != 0 &&
                    (i & targetMask) == 0) {

                    int j = i | targetMask;

                    double temp = real[i];
                    real[i] = real[j];
                    real[j] = temp;

                    temp = imaginary[i];
                    imaginary[i] = imaginary[j];
                    imaginary[j] = temp;
                }
            }
        }

        List<Double> execute(double[] parameters) {
            if (parameters.length != 2 * qubits) {
                throw new IllegalArgumentException(
                    "Incorrect circuit parameter count."
                );
            }

            for (double parameter : parameters) {
                if (!Double.isFinite(parameter)) {
                    throw new IllegalArgumentException(
                        "Non-finite circuit parameter."
                    );
                }
            }

            double[] real = new double[dimension];
            double[] imaginary = new double[dimension];

            real[0] = 1.0;

            for (int q = 0; q < qubits; q++) {
                applyRY(real, imaginary, q, parameters[q]);
            }

            for (int q = 0; q < qubits - 1; q++) {
                applyCNOT(real, imaginary, q, q + 1);
            }

            for (int q = 0; q < qubits; q++) {
                applyRY(
                    real,
                    imaginary,
                    q,
                    parameters[qubits + q]
                );
            }

            List<Double> probabilities = new ArrayList<>();
            double total = 0.0;

            for (int i = 0; i < dimension; i++) {
                double probability =
                    real[i] * real[i] +
                    imaginary[i] * imaginary[i];

                probabilities.add(probability);
                total += probability;
            }

            if (!Double.isFinite(total) || total <= EPSILON) {
                throw new QuantumLearningException(
                    "State normalization failed."
                );
            }

            final double normalization = total;

            return probabilities.stream()
                .map(p -> p / normalization)
                .toList();
        }

        int dimension() {
            return dimension;
        }
    }

    static class BornMachine {
        private final ModelConfig config;
        private final QuantumCircuit circuit;
        private final Random random;

        private final double[] parameters;
        private final List<TrainingRecord> history =
            new ArrayList<>();

        BornMachine(ModelConfig config) {
            this.config = Objects.requireNonNull(config);
            this.circuit = new QuantumCircuit(config.qubits());
            this.random = new Random(config.seed());

            this.parameters = new double[2 * config.qubits()];

            for (int i = 0; i < parameters.length; i++) {
                parameters[i] = random.nextDouble() * 1.6 - 0.8;
            }
        }

        List<Double> probabilities() {
            return circuit.execute(parameters);
        }

        static double klDivergence(
            List<Double> target,
            List<Double> generated
        ) {
            if (target.size() != generated.size()) {
                throw new IllegalArgumentException(
                    "Distribution dimensions differ."
                );
            }

            double loss = 0.0;

            for (int i = 0; i < target.size(); i++) {
                double p = target.get(i);
                double q = generated.get(i);

                if (p > 0) {
                    loss += p * Math.log(
                        p / Math.max(q, EPSILON)
                    );
                }
            }

            return loss;
        }

        static double totalVariation(
            List<Double> target,
            List<Double> generated
        ) {
            double result = 0.0;

            for (int i = 0; i < target.size(); i++) {
                result += Math.abs(
                    target.get(i) - generated.get(i)
                );
            }

            return result / 2.0;
        }

        double loss(ProbabilityDistribution target) {
            return klDivergence(
                target.values(),
                probabilities()
            );
        }

        void train(ProbabilityDistribution target) {
            if (target.size() != circuit.dimension()) {
                throw new IllegalArgumentException(
                    "Target dimension must equal 2^qubits."
                );
            }

            history.clear();

            final double alpha = 0.602;
            final double gamma = 0.101;

            for (int iteration = 0;
                 iteration < config.iterations();
                 iteration++) {

                double ak = config.learningRate() /
                    Math.pow(iteration + 11, alpha);

                double ck = 0.12 /
                    Math.pow(iteration + 1, gamma);

                double[] original = parameters.clone();
                double[] delta = new double[parameters.length];

                for (int i = 0; i < delta.length; i++) {
                    delta[i] = random.nextBoolean() ? 1.0 : -1.0;
                }

                for (int i = 0; i < parameters.length; i++) {
                    parameters[i] = original[i] + ck * delta[i];
                }

                double plus = loss(target);

                for (int i = 0; i < parameters.length; i++) {
                    parameters[i] = original[i] - ck * delta[i];
                }

                double minus = loss(target);

                double gradientScale = (plus - minus) / (2 * ck);

                for (int i = 0; i < parameters.length; i++) {
                    double updated = original[i] -
                        ak * gradientScale / delta[i];

                    parameters[i] = normalizeAngle(updated);
                }

                double currentLoss = loss(target);

                if (!Double.isFinite(currentLoss)) {
                    throw new QuantumLearningException(
                        "Non-finite training loss."
                    );
                }

                history.add(new TrainingRecord(
                    iteration + 1,
                    currentLoss,
                    ak
                ));
            }
        }

        private double normalizeAngle(double angle) {
            double result = (angle + PI) % (2 * PI);

            if (result < 0) result += 2 * PI;

            return result - PI;
        }

        Map<String, Integer> sample(int shots) {
            if (shots <= 0) {
                throw new IllegalArgumentException(
                    "Shots must be positive."
                );
            }

            List<Double> probabilities = probabilities();

            double[] cumulative = new double[probabilities.size()];
            double total = 0.0;

            for (int i = 0; i < probabilities.size(); i++) {
                total += probabilities.get(i);
                cumulative[i] = total;
            }

            Map<String, Integer> counts = new LinkedHashMap<>();

            for (int i = 0; i < probabilities.size(); i++) {
                counts.put(
                    String.format(
                        "%" + config.qubits() + "s",
                        Integer.toBinaryString(i)
                    ).replace(' ', '0'),
                    0
                );
            }

            for (int shot = 0; shot < shots; shot++) {
                double value = random.nextDouble();

                int selected = probabilities.size() - 1;

                for (int i = 0; i < cumulative.length; i++) {
                    if (value <= cumulative[i]) {
                        selected = i;
                        break;
                    }
                }

                String key = String.format(
                    "%" + config.qubits() + "s",
                    Integer.toBinaryString(selected)
                ).replace(' ', '0');

                counts.merge(key, 1, Integer::sum);
            }

            return Map.copyOf(counts);
        }

        Evaluation evaluate(ProbabilityDistribution target) {
            List<Double> generated = probabilities();

            double kl = klDivergence(target.values(), generated);
            double tv = totalVariation(target.values(), generated);

            double entropy = generated.stream()
                .filter(p -> p > EPSILON)
                .mapToDouble(p -> -p * Math.log(p) / Math.log(2))
                .sum();

            return new Evaluation(
                kl,
                tv,
                entropy,
                List.copyOf(generated)
            );
        }

        List<TrainingRecord> history() {
            return List.copyOf(history);
        }
    }

    static class ExperimentService {
        private final UUID experimentId = UUID.randomUUID();
        private final BornMachine model;
        private ExperimentStatus status = ExperimentStatus.CREATED;

        ExperimentService(BornMachine model) {
            this.model = Objects.requireNonNull(model);
        }

        ExperimentReport execute(
            ProbabilityDistribution target
        ) {
            if (status != ExperimentStatus.CREATED) {
                throw new IllegalStateException(
                    "Invalid experiment state transition."
                );
            }

            try {
                status = ExperimentStatus.VALIDATED;

                double initialLoss = model.loss(target);

                status = ExperimentStatus.TRAINING;

                model.train(target);

                Evaluation evaluation = model.evaluate(target);

                status = ExperimentStatus.COMPLETED;

                return new ExperimentReport(
                    experimentId,
                    status,
                    initialLoss,
                    evaluation.klDivergence(),
                    evaluation,
                    model.history(),
                    model.sample(5000)
                );

            } catch (RuntimeException error) {
                status = ExperimentStatus.FAILED;
                throw error;
            }
        }

        ExperimentStatus status() {
            return status;
        }
    }

    static void runTests() {
        QuantumCircuit circuit = new QuantumCircuit(2);

        List<Double> state = circuit.execute(
            new double[]{0, 0, 0, 0}
        );

        if (Math.abs(state.get(0) - 1.0) > 1e-10) {
            throw new AssertionError("Zero-state test failed.");
        }

        ModelConfig config = new ModelConfig(
            2, 0.08, 20, 1000, 42
        );

        BornMachine model = new BornMachine(config);

        ProbabilityDistribution target =
            new ProbabilityDistribution(
                Arrays.asList(0.25, 0.25, 0.25, 0.25)
            );

        model.train(target);

        if (model.history().size() != 20) {
            throw new AssertionError("Training history failed.");
        }

        Map<String, Integer> samples = model.sample(1000);

        if (samples.values().stream()
            .mapToInt(Integer::intValue).sum() != 1000) {
            throw new AssertionError("Sampling test failed.");
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        try {
            ModelConfig config = new ModelConfig(
                2,
                0.08,
                300,
                5000,
                42
            );

            ProbabilityDistribution target =
                new ProbabilityDistribution(
                    Arrays.asList(0.40, 0.10, 0.10, 0.40)
                );

            BornMachine model = new BornMachine(config);

            ExperimentService service =
                new ExperimentService(model);

            ExperimentReport report = service.execute(target);

            System.out.println(
                "\nQUANTUM GENERATIVE LEARNING"
            );

            System.out.println("Experiment: " + report.experimentId());
            System.out.println("Status: " + report.status());

            System.out.printf(
                "Initial KL divergence: %.6f%n",
                report.initialLoss()
            );

            System.out.printf(
                "Final KL divergence: %.6f%n",
                report.finalLoss()
            );

            System.out.printf(
                "Total variation: %.6f%n",
                report.evaluation().totalVariation()
            );

            System.out.printf(
                "Generated entropy: %.6f%n",
                report.evaluation().entropy()
            );

            System.out.println("\nGenerated distribution:");

            for (int i = 0;
                 i < report.evaluation().probabilities().size();
                 i++) {

                System.out.printf(
                    "|%2s> : %.6f%n",
                    Integer.toBinaryString(i),
                    report.evaluation().probabilities().get(i)
                );
            }

            System.out.println("\nMeasurement samples:");
            System.out.println(report.samples());

            runTests();

        } catch (RuntimeException error) {
            System.err.println(
                "Quantum experiment failed: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
