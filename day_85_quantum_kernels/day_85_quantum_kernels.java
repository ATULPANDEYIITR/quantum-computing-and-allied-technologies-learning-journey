import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/*
 * Quantum Kernel Enterprise Computation Service
 *
 * Java 17 implementation featuring:
 * - Immutable domain configuration.
 * - Quantum state-vector simulation.
 * - Quantum feature maps.
 * - Fidelity kernel evaluation.
 * - Kernel matrix management.
 * - Kernel ridge classification.
 * - Validation and model lifecycle management.
 * - Enterprise experiment and audit records.
 *
 * Dependencies: Java 17 standard library only.
 */

public class QuantumKernelEnterprise {

    private static final double EPSILON = 1e-10;

    public enum ExperimentStatus {
        CREATED,
        VALIDATED,
        TRAINING,
        COMPLETED,
        FAILED
    }

    public enum Gate {
        HADAMARD,
        RX,
        RZ,
        CZ
    }

    public static class QuantumException extends RuntimeException {
        public QuantumException(String message) {
            super(message);
        }
    }

    public static class ValidationException extends QuantumException {
        public ValidationException(String message) {
            super(message);
        }
    }

    public static class NumericalException extends QuantumException {
        public NumericalException(String message) {
            super(message);
        }
    }

    public record CircuitPolicy(
        int qubits,
        double rotationScale,
        boolean entanglement
    ) {
        public CircuitPolicy {
            if (qubits < 1 || qubits > 12) {
                throw new ValidationException(
                    "Qubits must be between 1 and 12."
                );
            }

            if (!Double.isFinite(rotationScale)) {
                throw new ValidationException(
                    "Invalid rotation scale."
                );
            }
        }
    }

    public record Sample(double[] features, int label) {

        public Sample {
            Objects.requireNonNull(features);

            features = features.clone();

            for (double value : features) {
                if (!Double.isFinite(value)) {
                    throw new ValidationException(
                        "Non-finite feature."
                    );
                }
            }

            if (label != -1 && label != 1) {
                throw new ValidationException(
                    "Label must be -1 or +1."
                );
            }
        }

        @Override
        public double[] features() {
            return features.clone();
        }

        public String key() {
            return Arrays.toString(features);
        }
    }

    public record ModelMetrics(
        int truePositive,
        int trueNegative,
        int falsePositive,
        int falseNegative,
        double accuracy
    ) {}

    public static final class ComplexState {
        private final double[] real;
        private final double[] imaginary;

        public ComplexState(int dimension) {
            real = new double[dimension];
            imaginary = new double[dimension];
            real[0] = 1.0;
        }

        private ComplexState(
            double[] real,
            double[] imaginary
        ) {
            this.real = real;
            this.imaginary = imaginary;
        }

        public int size() {
            return real.length;
        }

        public double norm() {
            double result = 0;

            for (int i = 0; i < real.length; i++) {
                result += real[i] * real[i]
                    + imaginary[i] * imaginary[i];
            }

            return result;
        }

        public static double fidelity(
            ComplexState first,
            ComplexState second
        ) {
            if (first.size() != second.size()) {
                throw new ValidationException(
                    "State dimensions differ."
                );
            }

            double overlapReal = 0;
            double overlapImaginary = 0;

            for (int i = 0; i < first.size(); i++) {
                overlapReal +=
                    first.real[i] * second.real[i]
                    + first.imaginary[i] * second.imaginary[i];

                overlapImaginary +=
                    first.real[i] * second.imaginary[i]
                    - first.imaginary[i] * second.real[i];
            }

            return Math.min(
                1.0,
                Math.max(
                    0.0,
                    overlapReal * overlapReal
                    + overlapImaginary * overlapImaginary
                )
            );
        }
    }

    public static final class QuantumFeatureMap {
        private final CircuitPolicy policy;
        private final int dimension;

        public QuantumFeatureMap(CircuitPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
            this.dimension = 1 << policy.qubits();
        }

        private void hadamard(
            double[] real,
            double[] imaginary,
            int qubit
        ) {
            int mask = 1 << qubit;
            double scale = 1.0 / Math.sqrt(2.0);

            for (int i = 0; i < dimension; i++) {
                if ((i & mask) == 0) {
                    int partner = i | mask;

                    double ar = real[i];
                    double ai = imaginary[i];

                    double br = real[partner];
                    double bi = imaginary[partner];

                    real[i] = (ar + br) * scale;
                    imaginary[i] = (ai + bi) * scale;

                    real[partner] = (ar - br) * scale;
                    imaginary[partner] = (ai - bi) * scale;
                }
            }
        }

        private void rz(
            double[] real,
            double[] imaginary,
            int qubit,
            double angle
        ) {
            int mask = 1 << qubit;
            double half = angle / 2.0;

            for (int i = 0; i < dimension; i++) {
                double phase = (i & mask) != 0
                    ? half : -half;

                double cosine = Math.cos(phase);
                double sine = Math.sin(phase);

                double oldReal = real[i];
                double oldImaginary = imaginary[i];

                real[i] =
                    oldReal * cosine - oldImaginary * sine;

                imaginary[i] =
                    oldReal * sine + oldImaginary * cosine;
            }
        }

        private void rx(
            double[] real,
            double[] imaginary,
            int qubit,
            double angle
        ) {
            int mask = 1 << qubit;

            double cosine = Math.cos(angle / 2.0);
            double sine = Math.sin(angle / 2.0);

            for (int i = 0; i < dimension; i++) {
                if ((i & mask) == 0) {
                    int partner = i | mask;

                    double ar = real[i];
                    double ai = imaginary[i];

                    double br = real[partner];
                    double bi = imaginary[partner];

                    real[i] = cosine * ar + sine * bi;
                    imaginary[i] = cosine * ai - sine * br;

                    real[partner] = cosine * br + sine * ai;
                    imaginary[partner] = cosine * bi - sine * ar;
                }
            }
        }

        private void cz(
            double[] real,
            double[] imaginary,
            int first,
            int second
        ) {
            if (first == second) {
                throw new ValidationException(
                    "CZ requires distinct qubits."
                );
            }

            int firstMask = 1 << first;
            int secondMask = 1 << second;

            for (int i = 0; i < dimension; i++) {
                if ((i & firstMask) != 0
                    && (i & secondMask) != 0) {
                    real[i] = -real[i];
                    imaginary[i] = -imaginary[i];
                }
            }
        }

        public ComplexState encode(double[] input) {
            if (input.length != policy.qubits()) {
                throw new ValidationException(
                    "Incorrect feature dimensions."
                );
            }

            double[] features = input.clone();

            for (double value : features) {
                if (!Double.isFinite(value)) {
                    throw new ValidationException(
                        "Invalid feature value."
                    );
                }
            }

            double[] real = new double[dimension];
            double[] imaginary = new double[dimension];

            real[0] = 1.0;

            for (int q = 0; q < policy.qubits(); q++) {
                hadamard(real, imaginary, q);
            }

            for (int q = 0; q < policy.qubits(); q++) {
                double angle =
                    policy.rotationScale() * features[q];

                rz(real, imaginary, q, angle);
                rx(real, imaginary, q, angle);
            }

            if (policy.entanglement()) {
                for (int q = 0; q < policy.qubits() - 1; q++) {
                    cz(real, imaginary, q, q + 1);
                }
            }

            ComplexState state = new ComplexState(
                real,
                imaginary
            );

            if (Math.abs(state.norm() - 1.0) > 1e-9) {
                throw new NumericalException(
                    "State normalization failed."
                );
            }

            return state;
        }
    }

    public static final class FidelityKernelService {

        private final QuantumFeatureMap featureMap;

        private final Map<String, ComplexState> stateCache =
            new HashMap<>();

        private final Map<String, Double> kernelCache =
            new HashMap<>();

        public FidelityKernelService(QuantumFeatureMap featureMap) {
            this.featureMap = Objects.requireNonNull(featureMap);
        }

        private String key(double[] features) {
            return Arrays.toString(features);
        }

        private String pairKey(String first, String second) {
            return first.compareTo(second) <= 0
                ? first + "|" + second
                : second + "|" + first;
        }

        public synchronized ComplexState state(double[] features) {
            String key = key(features);

            return stateCache.computeIfAbsent(
                key,
                ignored -> featureMap.encode(features)
            );
        }

        public synchronized double evaluate(
            double[] first,
            double[] second
        ) {
            String x = key(first);
            String z = key(second);

            String pair = pairKey(x, z);

            return kernelCache.computeIfAbsent(
                pair,
                ignored -> ComplexState.fidelity(
                    state(first),
                    state(second)
                )
            );
        }

        public double[][] matrix(List<Sample> samples) {
            if (samples.isEmpty()) {
                throw new ValidationException(
                    "Training dataset cannot be empty."
                );
            }

            int n = samples.size();
            double[][] result = new double[n][n];

            for (int i = 0; i < n; i++) {
                result[i][i] = 1.0;

                for (int j = i + 1; j < n; j++) {
                    double value = evaluate(
                        samples.get(i).features(),
                        samples.get(j).features()
                    );

                    result[i][j] = value;
                    result[j][i] = value;
                }
            }

            return result;
        }

        public synchronized Map<String, Integer> cacheStatistics() {
            return Map.of(
                "states", stateCache.size(),
                "kernels", kernelCache.size()
            );
        }
    }

    public static final class MatrixSolver {

        public static double[] solve(
            double[][] matrix,
            double[] vector
        ) {
            int n = vector.length;

            if (matrix.length != n) {
                throw new ValidationException(
                    "Invalid matrix dimensions."
                );
            }

            double[][] a = new double[n][n + 1];

            for (int i = 0; i < n; i++) {
                if (matrix[i].length != n) {
                    throw new ValidationException(
                        "Matrix must be square."
                    );
                }

                System.arraycopy(
                    matrix[i], 0, a[i], 0, n
                );

                a[i][n] = vector[i];
            }

            for (int col = 0; col < n; col++) {
                int pivot = col;

                for (int row = col + 1; row < n; row++) {
                    if (Math.abs(a[row][col])
                        > Math.abs(a[pivot][col])) {
                        pivot = row;
                    }
                }

                if (Math.abs(a[pivot][col]) < EPSILON) {
                    throw new NumericalException(
                        "Singular kernel matrix."
                    );
                }

                double[] temporary = a[col];
                a[col] = a[pivot];
                a[pivot] = temporary;

                for (int row = col + 1; row < n; row++) {
                    double factor =
                        a[row][col] / a[col][col];

                    for (int j = col; j <= n; j++) {
                        a[row][j] -= factor * a[col][j];
                    }
                }
            }

            double[] solution = new double[n];

            for (int i = n - 1; i >= 0; i--) {
                double value = a[i][n];

                for (int j = i + 1; j < n; j++) {
                    value -= a[i][j] * solution[j];
                }

                solution[i] = value / a[i][i];
            }

            return solution;
        }
    }

    public static final class KernelRidgeService {

        private final FidelityKernelService kernel;
        private final double regularization;

        private List<Sample> trainingData = List.of();
        private double[] coefficients;
        private ExperimentStatus status = ExperimentStatus.CREATED;

        public KernelRidgeService(
            FidelityKernelService kernel,
            double regularization
        ) {
            this.kernel = Objects.requireNonNull(kernel);

            if (!Double.isFinite(regularization)
                || regularization <= 0) {
                throw new ValidationException(
                    "Regularization must be positive."
                );
            }

            this.regularization = regularization;
        }

        public synchronized void fit(List<Sample> samples) {
            if (status == ExperimentStatus.TRAINING) {
                throw new QuantumException(
                    "Training is already in progress."
                );
            }

            if (samples.size() < 2) {
                throw new ValidationException(
                    "At least two training samples are required."
                );
            }

            Set<String> observations = new HashSet<>();

            boolean positive = false;
            boolean negative = false;

            for (Sample sample : samples) {
                if (sample.features().length != 2) {
                    throw new ValidationException(
                        "This service requires two features."
                    );
                }

                if (!observations.add(sample.key())) {
                    throw new ValidationException(
                        "Duplicate training observations."
                    );
                }

                positive |= sample.label() == 1;
                negative |= sample.label() == -1;
            }

            if (!positive || !negative) {
                throw new ValidationException(
                    "Both target classes must be present."
                );
            }

            status = ExperimentStatus.VALIDATED;

            try {
                status = ExperimentStatus.TRAINING;

                double[][] gram = kernel.matrix(samples);
                double[] labels = new double[samples.size()];

                for (int i = 0; i < samples.size(); i++) {
                    gram[i][i] += regularization;
                    labels[i] = samples.get(i).label();
                }

                coefficients = MatrixSolver.solve(gram, labels);
                trainingData = List.copyOf(samples);

                status = ExperimentStatus.COMPLETED;

            } catch (RuntimeException exception) {
                status = ExperimentStatus.FAILED;
                throw exception;
            }
        }

        public double decision(double[] features) {
            if (status != ExperimentStatus.COMPLETED) {
                throw new QuantumException(
                    "Model is not ready for prediction."
                );
            }

            double score = 0;

            for (int i = 0; i < trainingData.size(); i++) {
                score += coefficients[i] *
                    kernel.evaluate(
                        trainingData.get(i).features(),
                        features
                    );
            }

            return score;
        }

        public int predict(double[] features) {
            return decision(features) >= 0 ? 1 : -1;
        }

        public ExperimentStatus status() {
            return status;
        }
    }

    public static ModelMetrics evaluate(
        List<Sample> testing,
        KernelRidgeService classifier
    ) {
        if (testing.isEmpty()) {
            throw new ValidationException(
                "Testing dataset cannot be empty."
            );
        }

        int tp = 0;
        int tn = 0;
        int fp = 0;
        int fn = 0;

        for (Sample sample : testing) {
            int predicted = classifier.predict(sample.features());

            if (sample.label() == 1 && predicted == 1) {
                tp++;
            } else if (sample.label() == -1 && predicted == -1) {
                tn++;
            } else if (sample.label() == -1) {
                fp++;
            } else {
                fn++;
            }
        }

        double accuracy = (double) (tp + tn) / testing.size();

        return new ModelMetrics(tp, tn, fp, fn, accuracy);
    }

    private static List<Sample> createDataset() {
        List<Sample> samples = new ArrayList<>();

        for (int i = 0; i < 32; i++) {
            double x = -1.2 + 2.4 * (i % 8) / 7.0;
            double z = -1.2 + 2.4 * (i / 8) / 3.0;

            int label =
                Math.sin(2 * x) * Math.cos(2 * z) >= 0
                ? 1 : -1;

            samples.add(new Sample(
                new double[]{x, z},
                label
            ));
        }

        return samples;
    }

    public static void main(String[] args) {
        try {
            long started = System.nanoTime();

            CircuitPolicy policy = new CircuitPolicy(
                2,
                2.0,
                true
            );

            QuantumFeatureMap featureMap =
                new QuantumFeatureMap(policy);

            FidelityKernelService kernel =
                new FidelityKernelService(featureMap);

            KernelRidgeService classifier =
                new KernelRidgeService(kernel, 0.15);

            List<Sample> dataset = createDataset();

            List<Sample> training =
                List.copyOf(dataset.subList(0, 24));

            List<Sample> testing =
                List.copyOf(dataset.subList(24, 32));

            classifier.fit(training);

            ModelMetrics metrics = evaluate(
                testing,
                classifier
            );

            System.out.println("QUANTUM KERNEL ENTERPRISE SERVICE");
            System.out.println("=================================");

            System.out.println("Qubits: " + policy.qubits());
            System.out.println("Training samples: " + training.size());
            System.out.println("Testing samples: " + testing.size());

            System.out.printf(
                "Accuracy: %.4f%n",
                metrics.accuracy()
            );

            System.out.println("True positives: " + metrics.truePositive());
            System.out.println("True negatives: " + metrics.trueNegative());
            System.out.println("False positives: " + metrics.falsePositive());
            System.out.println("False negatives: " + metrics.falseNegative());

            System.out.println(
                "Experiment status: " + classifier.status()
            );

            System.out.println(
                "Cache statistics: " + kernel.cacheStatistics()
            );

            System.out.printf(
                "Execution time: %.3f ms%n",
                (System.nanoTime() - started) / 1_000_000.0
            );

            double selfFidelity = kernel.evaluate(
                new double[]{0.25, -0.35},
                new double[]{0.25, -0.35}
            );

            if (Math.abs(selfFidelity - 1.0) > 1e-9) {
                throw new NumericalException(
                    "Self-fidelity check failed."
                );
            }

            if (classifier.status() != ExperimentStatus.COMPLETED) {
                throw new QuantumException(
                    "Experiment did not complete successfully."
                );
            }

            System.out.println("All enterprise validation checks passed.");

        } catch (RuntimeException exception) {
            System.err.println(
                "Experiment failure: " + exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
