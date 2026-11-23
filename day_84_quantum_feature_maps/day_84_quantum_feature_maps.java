import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.stream.IntStream;

/*
 * Quantum Feature Maps
 *
 * Enterprise-oriented quantum feature encoding and evaluation.
 *
 * Capabilities:
 * - Immutable classical feature records
 * - Feature normalization
 * - Angle, ZZ and IQP-inspired feature maps
 * - Complex statevector simulation
 * - Quantum kernel evaluation
 * - Measurement sampling
 * - Experiment lifecycle management
 * - Validation and audit reporting
 *
 * Runtime: Java 17
 */

public class QuantumFeatureMapEnterprise {

    private static final double EPSILON = 1e-9;
    private static final int MAX_QUBITS = 20;

    enum EncodingType {
        ANGLE,
        ZZ,
        IQP
    }

    enum ExperimentStatus {
        CREATED,
        VALIDATED,
        ENCODING,
        COMPLETED,
        FAILED
    }

    static class FeatureMapException extends RuntimeException {
        FeatureMapException(String message) {
            super(message);
        }
    }

    record FeatureVector(List<Double> values) {

        FeatureVector {
            Objects.requireNonNull(values);

            values = List.copyOf(values);

            if (values.isEmpty()) {
                throw new FeatureMapException(
                    "Feature vector cannot be empty."
                );
            }

            for (double value : values) {
                if (!Double.isFinite(value)) {
                    throw new FeatureMapException(
                        "Feature values must be finite."
                    );
                }
            }
        }

        int dimensions() {
            return values.size();
        }

        FeatureVector normalize(double lower, double upper) {
            if (!Double.isFinite(lower) ||
                !Double.isFinite(upper) ||
                lower >= upper) {
                throw new FeatureMapException(
                    "Invalid normalization interval."
                );
            }

            double minimum = values.stream()
                .mapToDouble(Double::doubleValue)
                .min()
                .orElseThrow();

            double maximum = values.stream()
                .mapToDouble(Double::doubleValue)
                .max()
                .orElseThrow();

            List<Double> normalized = values.stream()
                .map(value -> {
                    if (minimum == maximum) {
                        return (lower + upper) / 2;
                    }

                    return lower +
                        (value - minimum) *
                        (upper - lower) /
                        (maximum - minimum);
                })
                .toList();

            return new FeatureVector(normalized);
        }
    }

    record FeatureMapPolicy(
        EncodingType encoding,
        int repetitions,
        double entanglementStrength,
        int maximumQubits
    ) {
        FeatureMapPolicy {
            Objects.requireNonNull(encoding);

            if (repetitions < 1) {
                throw new FeatureMapException(
                    "Repetitions must be positive."
                );
            }

            if (!Double.isFinite(entanglementStrength)) {
                throw new FeatureMapException(
                    "Invalid entanglement strength."
                );
            }

            if (maximumQubits < 1 ||
                maximumQubits > MAX_QUBITS) {
                throw new FeatureMapException(
                    "Invalid simulation limit."
                );
            }
        }
    }

    record ComplexValue(double real, double imaginary) {

        ComplexValue multiply(ComplexValue other) {
            return new ComplexValue(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        ComplexValue scale(double factor) {
            return new ComplexValue(
                real * factor,
                imaginary * factor
            );
        }

        ComplexValue add(ComplexValue other) {
            return new ComplexValue(
                real + other.real,
                imaginary + other.imaginary
            );
        }

        ComplexValue conjugate() {
            return new ComplexValue(real, -imaginary);
        }

        double normSquared() {
            return real * real + imaginary * imaginary;
        }

        static ComplexValue phase(double angle) {
            return new ComplexValue(
                Math.cos(angle),
                Math.sin(angle)
            );
        }
    }

    static final class QuantumState {
        private final int qubits;
        private final ComplexValue[] amplitudes;

        QuantumState(int qubits, ComplexValue[] amplitudes) {
            this.qubits = qubits;
            this.amplitudes = amplitudes.clone();
            validate();
        }

        int qubits() {
            return qubits;
        }

        int dimension() {
            return amplitudes.length;
        }

        ComplexValue amplitude(int index) {
            return amplitudes[index];
        }

        double normSquared() {
            return IntStream.range(0, amplitudes.length)
                .mapToDouble(i -> amplitudes[i].normSquared())
                .sum();
        }

        void validate() {
            if (qubits < 1 ||
                amplitudes.length != (1 << qubits)) {
                throw new FeatureMapException(
                    "Invalid statevector dimensions."
                );
            }

            for (ComplexValue amplitude : amplitudes) {
                if (!Double.isFinite(amplitude.real()) ||
                    !Double.isFinite(amplitude.imaginary())) {
                    throw new FeatureMapException(
                        "Invalid state amplitude."
                    );
                }
            }

            if (Math.abs(normSquared() - 1) > EPSILON) {
                throw new FeatureMapException(
                    "State normalization failed."
                );
            }
        }

        double[] probabilities() {
            return IntStream.range(0, amplitudes.length)
                .mapToDouble(i -> amplitudes[i].normSquared())
                .toArray();
        }

        Map<String, Integer> sample(int shots, long seed) {
            if (shots < 1) {
                throw new FeatureMapException(
                    "Shots must be positive."
                );
            }

            Random random = new Random(seed);
            double[] probabilities = probabilities();

            Map<String, Integer> counts = new java.util.TreeMap<>();

            for (int shot = 0; shot < shots; shot++) {
                double target = random.nextDouble();
                double cumulative = 0;
                int outcome = probabilities.length - 1;

                for (int i = 0; i < probabilities.length; i++) {
                    cumulative += probabilities[i];

                    if (target < cumulative) {
                        outcome = i;
                        break;
                    }
                }

                String bitstring = String.format(
                    "%"+qubits+"s",
                    Integer.toBinaryString(outcome)
                ).replace(' ', '0');

                counts.merge(bitstring, 1, Integer::sum);
            }

            return Collections.unmodifiableMap(counts);
        }
    }

    static final class FeatureMapEncoder {

        private final FeatureMapPolicy policy;

        FeatureMapEncoder(FeatureMapPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        private void applyRY(
            ComplexValue[] state,
            int qubit,
            double theta
        ) {
            int mask = 1 << qubit;

            double cosine = Math.cos(theta / 2);
            double sine = Math.sin(theta / 2);

            for (int i = 0; i < state.length; i++) {
                if ((i & mask) != 0) {
                    continue;
                }

                int j = i | mask;

                ComplexValue zero = state[i];
                ComplexValue one = state[j];

                state[i] = zero.scale(cosine)
                    .add(one.scale(-sine));

                state[j] = zero.scale(sine)
                    .add(one.scale(cosine));
            }
        }

        private void applyRZ(
            ComplexValue[] state,
            int qubit,
            double theta
        ) {
            int mask = 1 << qubit;

            for (int i = 0; i < state.length; i++) {
                double sign = (i & mask) != 0 ? 1 : -1;

                state[i] = state[i].multiply(
                    ComplexValue.phase(sign * theta / 2)
                );
            }
        }

        private void applyZZ(
            ComplexValue[] state,
            int first,
            int second,
            double theta
        ) {
            if (first == second) {
                throw new FeatureMapException(
                    "ZZ gate requires distinct qubits."
                );
            }

            int firstMask = 1 << first;
            int secondMask = 1 << second;

            for (int i = 0; i < state.length; i++) {
                boolean different =
                    ((i & firstMask) != 0) !=
                    ((i & secondMask) != 0);

                double eigenvalue = different ? -1 : 1;

                state[i] = state[i].multiply(
                    ComplexValue.phase(
                        -theta * eigenvalue / 2
                    )
                );
            }
        }

        QuantumState encode(FeatureVector features) {
            int qubits = features.dimensions();

            if (qubits > policy.maximumQubits()) {
                throw new FeatureMapException(
                    "Feature dimension exceeds simulation policy."
                );
            }

            ComplexValue[] state = new ComplexValue[1 << qubits];

            for (int i = 0; i < state.length; i++) {
                state[i] = new ComplexValue(0, 0);
            }

            state[0] = new ComplexValue(1, 0);

            for (int layer = 0;
                 layer < policy.repetitions();
                 layer++) {

                for (int q = 0; q < qubits; q++) {
                    double value = features.values().get(q);

                    switch (policy.encoding()) {
                        case ANGLE ->
                            applyRY(state, q, value);

                        case ZZ -> {
                            applyRY(state, q, 2 * value);
                            applyRZ(state, q, value);
                        }

                        case IQP -> {
                            applyRY(state, q, value);
                            applyRZ(state, q, 2 * value);
                        }
                    }
                }

                if (policy.encoding() != EncodingType.ANGLE) {
                    for (int i = 0; i < qubits; i++) {
                        for (int j = i + 1; j < qubits; j++) {
                            double theta;

                            if (policy.encoding() == EncodingType.ZZ) {
                                theta =
                                    policy.entanglementStrength() *
                                    features.values().get(i) *
                                    features.values().get(j);
                            } else {
                                theta = 2 *
                                    features.values().get(i) *
                                    features.values().get(j);
                            }

                            applyZZ(state, i, j, theta);
                        }
                    }
                }
            }

            return new QuantumState(qubits, state);
        }
    }

    static final class QuantumKernelService {

        double evaluate(
            QuantumState first,
            QuantumState second
        ) {
            if (first.qubits() != second.qubits()) {
                throw new FeatureMapException(
                    "State dimensions must match."
                );
            }

            ComplexValue overlap = new ComplexValue(0, 0);

            for (int i = 0; i < first.dimension(); i++) {
                overlap = overlap.add(
                    first.amplitude(i).conjugate()
                        .multiply(second.amplitude(i))
                );
            }

            return Math.min(
                1,
                Math.max(0, overlap.normSquared())
            );
        }

        double[][] matrix(List<QuantumState> states) {
            int n = states.size();
            double[][] matrix = new double[n][n];

            for (int i = 0; i < n; i++) {
                for (int j = i; j < n; j++) {
                    double value = evaluate(
                        states.get(i),
                        states.get(j)
                    );

                    matrix[i][j] = value;
                    matrix[j][i] = value;
                }
            }

            return matrix;
        }
    }

    static final class ExperimentService {

        private final FeatureMapPolicy policy;
        private ExperimentStatus status =
            ExperimentStatus.CREATED;

        ExperimentService(FeatureMapPolicy policy) {
            this.policy = policy;
        }

        ExperimentStatus status() {
            return status;
        }

        List<QuantumState> execute(List<FeatureVector> dataset) {
            try {
                if (dataset == null || dataset.isEmpty()) {
                    throw new FeatureMapException(
                        "Dataset cannot be empty."
                    );
                }

                status = ExperimentStatus.VALIDATED;

                FeatureMapEncoder encoder =
                    new FeatureMapEncoder(policy);

                status = ExperimentStatus.ENCODING;

                List<QuantumState> states = new ArrayList<>();

                for (FeatureVector sample : dataset) {
                    states.add(encoder.encode(sample));
                }

                status = ExperimentStatus.COMPLETED;

                return List.copyOf(states);

            } catch (RuntimeException exception) {
                status = ExperimentStatus.FAILED;
                throw exception;
            }
        }
    }

    private static List<FeatureVector> createDataset() {
        return List.of(
            new FeatureVector(List.of(0.2, 0.4, 0.6)),
            new FeatureVector(List.of(0.3, 0.7, 0.5)),
            new FeatureVector(List.of(0.8, 0.2, 0.9)),
            new FeatureVector(List.of(0.9, 0.6, 0.1))
        );
    }

    private static void printMatrix(double[][] matrix) {
        for (double[] row : matrix) {
            for (double value : row) {
                System.out.printf("%12.6f", value);
            }
            System.out.println();
        }
    }

    public static void main(String[] args) {

        List<FeatureVector> rawDataset = createDataset();

        List<FeatureVector> normalizedDataset =
            rawDataset.stream()
                .map(vector -> vector.normalize(-Math.PI, Math.PI))
                .toList();

        QuantumKernelService kernelService =
            new QuantumKernelService();

        Map<EncodingType, double[][]> reports =
            new EnumMap<>(EncodingType.class);

        for (EncodingType encoding : EncodingType.values()) {

            System.out.println(
                "\nFeature map: " + encoding
            );

            FeatureMapPolicy policy = new FeatureMapPolicy(
                encoding,
                2,
                0.75,
                20
            );

            ExperimentService service =
                new ExperimentService(policy);

            List<QuantumState> states =
                service.execute(normalizedDataset);

            double[][] matrix = kernelService.matrix(states);

            reports.put(encoding, matrix);

            System.out.println(
                "Experiment status: " + service.status()
            );

            System.out.println(
                "Statevector dimension: " +
                states.get(0).dimension()
            );

            System.out.println(
                "Normalization: " +
                states.get(0).normSquared()
            );

            System.out.println("\nKernel matrix:");
            printMatrix(matrix);

            if (Math.abs(matrix[0][0] - 1) > EPSILON) {
                throw new FeatureMapException(
                    "Self-fidelity validation failed."
                );
            }

            System.out.println("\nMeasurement results:");

            System.out.println(
                states.get(0).sample(1000, 42)
            );
        }

        System.out.println("\nEncoding comparison:");

        for (var entry : reports.entrySet()) {
            System.out.printf(
                "%s -> K(0,1) = %.8f%n",
                entry.getKey(),
                entry.getValue()[0][1]
            );
        }

        System.out.println(
            "\nQuantum feature-map experiments completed."
        );
    }
}
