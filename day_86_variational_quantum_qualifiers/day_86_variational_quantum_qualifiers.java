import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.Objects;

/**
 * Variational Quantum Classifier.
 *
 * Enterprise-oriented quantum classification implementation.
 *
 * Components:
 * - Quantum state simulation
 * - Feature encoding
 * - Variational circuit
 * - Parameter-shift differentiation
 * - Binary cross-entropy
 * - Training service
 * - Model evaluation
 * - Immutable domain records
 * - Model lifecycle validation
 *
 * Java 17, no external dependencies.
 */
public class VariationalQuantumClassifier {

    private static final double PI = Math.PI;
    private static final double EPSILON = 1e-10;

    public enum Classification {
        NEGATIVE(0),
        POSITIVE(1);

        private final int value;

        Classification(int value) {
            this.value = value;
        }

        public int value() {
            return value;
        }

        public static Classification from(int value) {
            return switch (value) {
                case 0 -> NEGATIVE;
                case 1 -> POSITIVE;
                default -> throw new IllegalArgumentException(
                    "Classification must be binary."
                );
            };
        }
    }

    public enum ModelStatus {
        INITIALIZED,
        TRAINING,
        TRAINED,
        FAILED
    }

    public record Sample(
        List<Double> features,
        Classification label
    ) {
        public Sample {
            Objects.requireNonNull(features);
            Objects.requireNonNull(label);

            if (features.size() != 2) {
                throw new IllegalArgumentException(
                    "Exactly two features are required."
                );
            }

            features = List.copyOf(features);

            for (double feature : features) {
                if (!Double.isFinite(feature)) {
                    throw new IllegalArgumentException(
                        "Features must be finite."
                    );
                }
            }
        }

        public int target() {
            return label.value();
        }
    }

    public record TrainingPolicy(
        int epochs,
        double learningRate,
        int seed
    ) {
        public TrainingPolicy {
            if (epochs <= 0) {
                throw new IllegalArgumentException(
                    "Epochs must be positive."
                );
            }

            if (
                !Double.isFinite(learningRate) ||
                learningRate <= 0 ||
                learningRate > 1
            ) {
                throw new IllegalArgumentException(
                    "Learning rate must be in (0, 1]."
                );
            }
        }
    }

    public record Metrics(
        double accuracy,
        double loss,
        double precision,
        double recall,
        int truePositive,
        int falsePositive,
        int trueNegative,
        int falseNegative
    ) {}

    public record TrainingEvent(
        int epoch,
        double loss,
        ModelStatus status
    ) {}

    @FunctionalInterface
    public interface TrainingListener {
        void onTrainingEvent(TrainingEvent event);
    }

    public static final class QuantumState {

        private double[] amplitudes = {1.0, 0.0, 0.0, 0.0};

        public void reset() {
            amplitudes = new double[]{1.0, 0.0, 0.0, 0.0};
        }

        public void applyRY(int qubit, double theta) {
            if (
                qubit < 0 ||
                qubit > 1 ||
                !Double.isFinite(theta)
            ) {
                throw new IllegalArgumentException(
                    "Invalid RY operation."
                );
            }

            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);
            int mask = 1 << qubit;

            double[] next = amplitudes.clone();

            for (int i = 0; i < 4; i++) {
                if ((i & mask) != 0) {
                    continue;
                }

                int j = i | mask;

                double a = amplitudes[i];
                double b = amplitudes[j];

                next[i] = c * a - s * b;
                next[j] = s * a + c * b;
            }

            amplitudes = next;
        }

        public void applyCNOT(int control, int target) {
            if (
                control < 0 ||
                control > 1 ||
                target < 0 ||
                target > 1 ||
                control == target
            ) {
                throw new IllegalArgumentException(
                    "Invalid CNOT operation."
                );
            }

            double[] next = new double[4];

            for (int i = 0; i < 4; i++) {
                int destination = i;

                if ((i & (1 << control)) != 0) {
                    destination ^= 1 << target;
                }

                next[destination] = amplitudes[i];
            }

            amplitudes = next;
        }

        public double expectationZ0() {
            double result = 0;

            for (int i = 0; i < 4; i++) {
                double sign = (i & 1) == 0 ? 1 : -1;
                result += sign * amplitudes[i] * amplitudes[i];
            }

            return result;
        }

        public void validateNormalization() {
            double norm = 0;

            for (double amplitude : amplitudes) {
                norm += amplitude * amplitude;
            }

            if (Math.abs(norm - 1.0) > 1e-8) {
                throw new IllegalStateException(
                    "Quantum state normalization failure."
                );
            }
        }
    }

    public static final class QuantumCircuit {

        public double execute(
            List<Double> features,
            double[] parameters
        ) {
            if (features.size() != 2 || parameters.length != 4) {
                throw new IllegalArgumentException(
                    "Invalid circuit dimensions."
                );
            }

            QuantumState state = new QuantumState();

            // Encode classical input data.
            state.applyRY(0, features.get(0));
            state.applyRY(1, features.get(1));

            // Entangling layer.
            state.applyCNOT(0, 1);

            // Trainable variational ansatz.
            state.applyRY(0, parameters[0]);
            state.applyRY(1, parameters[1]);

            state.applyCNOT(0, 1);

            state.applyRY(0, parameters[2]);
            state.applyRY(1, parameters[3]);

            state.validateNormalization();

            return state.expectationZ0();
        }
    }

    public static final class Dataset {

        private final List<Sample> samples;

        public Dataset(List<Sample> samples) {
            Objects.requireNonNull(samples);

            if (samples.size() < 2) {
                throw new IllegalArgumentException(
                    "Dataset requires at least two records."
                );
            }

            this.samples = List.copyOf(samples);

            boolean negative = false;
            boolean positive = false;

            for (Sample sample : this.samples) {
                Objects.requireNonNull(sample);

                if (sample.label() == Classification.NEGATIVE) {
                    negative = true;
                } else {
                    positive = true;
                }
            }

            if (!negative || !positive) {
                throw new IllegalArgumentException(
                    "Both binary classes are required."
                );
            }
        }

        public List<Sample> samples() {
            return samples;
        }

        public int size() {
            return samples.size();
        }
    }

    public static final class VQCModel {

        private final QuantumCircuit circuit = new QuantumCircuit();

        private double[] parameters;
        private ModelStatus status = ModelStatus.INITIALIZED;
        private final List<Double> trainingHistory = new ArrayList<>();

        public VQCModel(int seed) {
            Random random = new Random(seed);

            parameters = new double[4];

            for (int i = 0; i < parameters.length; i++) {
                parameters[i] = random.nextDouble() - 0.5;
            }
        }

        public ModelStatus status() {
            return status;
        }

        public double[] parameters() {
            return parameters.clone();
        }

        public List<Double> trainingHistory() {
            return Collections.unmodifiableList(
                trainingHistory
            );
        }

        public double expectation(List<Double> features) {
            return circuit.execute(features, parameters);
        }

        public double probability(List<Double> features) {
            return Math.max(
                EPSILON,
                Math.min(
                    1 - EPSILON,
                    (1 - expectation(features)) / 2
                )
            );
        }

        public Classification predict(List<Double> features) {
            return probability(features) >= 0.5
                ? Classification.POSITIVE
                : Classification.NEGATIVE;
        }

        public double[] calculateGradient(Sample sample) {
            double p = probability(sample.features());

            double lossDerivative =
                (p - sample.target()) / (p * (1 - p));

            double[] gradient = new double[4];

            for (int i = 0; i < 4; i++) {
                double[] plus = parameters.clone();
                double[] minus = parameters.clone();

                plus[i] += PI / 2;
                minus[i] -= PI / 2;

                double expPlus = circuit.execute(
                    sample.features(),
                    plus
                );

                double expMinus = circuit.execute(
                    sample.features(),
                    minus
                );

                double expectationDerivative =
                    (expPlus - expMinus) / 2;

                double probabilityDerivative =
                    -expectationDerivative / 2;

                gradient[i] =
                    lossDerivative * probabilityDerivative;
            }

            return gradient;
        }

        private static double crossEntropy(
            double probability,
            int target
        ) {
            double p = Math.max(
                EPSILON,
                Math.min(1 - EPSILON, probability)
            );

            return -(
                target * Math.log(p) +
                (1 - target) * Math.log(1 - p)
            );
        }

        public void optimize(
            Dataset dataset,
            TrainingPolicy policy,
            TrainingListener listener
        ) {
            if (status == ModelStatus.TRAINING) {
                throw new IllegalStateException(
                    "Concurrent model training is not permitted."
                );
            }

            Objects.requireNonNull(dataset);
            Objects.requireNonNull(policy);

            status = ModelStatus.TRAINING;

            try {
                for (int epoch = 0; epoch < policy.epochs(); epoch++) {
                    double[] accumulated = new double[4];
                    double totalLoss = 0;

                    for (Sample sample : dataset.samples()) {
                        double p = probability(sample.features());

                        totalLoss += crossEntropy(p, sample.target());

                        double[] gradient = calculateGradient(sample);

                        for (int i = 0; i < 4; i++) {
                            accumulated[i] += gradient[i];
                        }
                    }

                    double averageLoss =
                        totalLoss / dataset.size();

                    if (!Double.isFinite(averageLoss)) {
                        throw new ArithmeticException(
                            "Non-finite training loss."
                        );
                    }

                    double[] updated = parameters.clone();

                    for (int i = 0; i < 4; i++) {
                        updated[i] = Math.max(
                            -4 * PI,
                            Math.min(
                                4 * PI,
                                parameters[i] -
                                policy.learningRate() *
                                accumulated[i] /
                                dataset.size()
                            )
                        );
                    }

                    parameters = updated;
                    trainingHistory.add(averageLoss);

                    if (listener != null) {
                        listener.onTrainingEvent(
                            new TrainingEvent(
                                epoch,
                                averageLoss,
                                ModelStatus.TRAINING
                            )
                        );
                    }
                }

                status = ModelStatus.TRAINED;

            } catch (RuntimeException exception) {
                status = ModelStatus.FAILED;
                throw exception;
            }
        }
    }

    public static final class EvaluationService {

        public Metrics evaluate(VQCModel model, Dataset dataset) {
            Objects.requireNonNull(model);
            Objects.requireNonNull(dataset);

            if (model.status() != ModelStatus.TRAINED) {
                throw new IllegalStateException(
                    "Only trained models can be evaluated."
                );
            }

            int tp = 0;
            int fp = 0;
            int tn = 0;
            int fn = 0;

            double loss = 0;

            for (Sample sample : dataset.samples()) {
                double p = model.probability(sample.features());

                int predicted = p >= 0.5 ? 1 : 0;
                int actual = sample.target();

                loss += VQCModel.crossEntropy(p, actual);

                if (predicted == 1 && actual == 1) tp++;
                else if (predicted == 1) fp++;
                else if (actual == 0) tn++;
                else fn++;
            }

            int total = dataset.size();

            double accuracy = (double) (tp + tn) / total;

            double precision = tp + fp == 0
                ? 0
                : (double) tp / (tp + fp);

            double recall = tp + fn == 0
                ? 0
                : (double) tp / (tp + fn);

            return new Metrics(
                accuracy,
                loss / total,
                precision,
                recall,
                tp,
                fp,
                tn,
                fn
            );
        }
    }

    private static Dataset createTrainingDataset() {
        return new Dataset(List.of(
            new Sample(List.of(0.15, 0.20), Classification.NEGATIVE),
            new Sample(List.of(0.35, 0.25), Classification.NEGATIVE),
            new Sample(List.of(0.20, 0.55), Classification.NEGATIVE),
            new Sample(List.of(0.55, 0.30), Classification.NEGATIVE),
            new Sample(List.of(2.10, 2.00), Classification.POSITIVE),
            new Sample(List.of(2.40, 1.80), Classification.POSITIVE),
            new Sample(List.of(1.90, 2.45), Classification.POSITIVE),
            new Sample(List.of(2.65, 2.30), Classification.POSITIVE)
        ));
    }

    private static Dataset createTestingDataset() {
        return new Dataset(List.of(
            new Sample(List.of(0.40, 0.65), Classification.NEGATIVE),
            new Sample(List.of(2.20, 2.70), Classification.POSITIVE)
        ));
    }

    public static void main(String[] args) {

        System.out.println("VARIATIONAL QUANTUM CLASSIFIER");
        System.out.println("==============================");

        try {
            Dataset training = createTrainingDataset();
            Dataset testing = createTestingDataset();

            VQCModel model = new VQCModel(42);

            TrainingPolicy policy = new TrainingPolicy(
                120,
                0.08,
                42
            );

            model.optimize(
                training,
                policy,
                event -> {
                    if (event.epoch() % 20 == 0) {
                        System.out.printf(
                            "Epoch %03d | Loss: %.6f%n",
                            event.epoch(),
                            event.loss()
                        );
                    }
                }
            );

            EvaluationService evaluator =
                new EvaluationService();

            Metrics trainingMetrics =
                evaluator.evaluate(model, training);

            Metrics testingMetrics =
                evaluator.evaluate(model, testing);

            System.out.println("\nTraining metrics:");
            System.out.println(trainingMetrics);

            System.out.println("\nTesting metrics:");
            System.out.println(testingMetrics);

            System.out.println("\nPredictions:");

            for (Sample sample : testing.samples()) {
                System.out.printf(
                    "Input=%s Actual=%s Predicted=%s Probability=%.4f%n",
                    sample.features(),
                    sample.label(),
                    model.predict(sample.features()),
                    model.probability(sample.features())
                );
            }

            System.out.println("\nModel status: " + model.status());
            System.out.println(
                "Training epochs: " + model.trainingHistory().size()
            );

            System.out.println(
                "Quantum state and enterprise validation completed."
            );

        } catch (RuntimeException exception) {
            System.err.println(
                "Classification failure: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
