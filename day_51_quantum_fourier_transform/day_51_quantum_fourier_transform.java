import java.util.Arrays;
import java.util.Random;

/*
 * Quantum Fourier Transform fundamentals.
 *
 * This Java 17 program models QFT as an enterprise-style numerical service.
 * Domain types make the important invariants explicit: a quantum register
 * has a power-of-two dimension, normalized amplitudes, and reversible
 * Fourier transformations.
 *
 * The implementation intentionally uses immutable records for complex
 * numbers and a service class for transformation policies.
 */

public class QuantumFourierTransform {

    private static final double PI = Math.PI;
    private static final double EPSILON = 1e-10;

    public record Complex(double real, double imaginary) {

        public Complex {
            if (!Double.isFinite(real) ||
                !Double.isFinite(imaginary)) {
                throw new IllegalArgumentException(
                    "Complex components must be finite."
                );
            }
        }

        public Complex add(Complex other) {
            return new Complex(
                real + other.real,
                imaginary + other.imaginary
            );
        }

        public Complex multiply(Complex other) {
            return new Complex(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        public Complex conjugate() {
            return new Complex(real, -imaginary);
        }

        public Complex scale(double factor) {
            return new Complex(
                real * factor,
                imaginary * factor
            );
        }

        public double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        public double magnitude() {
            return Math.sqrt(magnitudeSquared());
        }

        public static Complex polar(double radius, double angle) {
            return new Complex(
                radius * Math.cos(angle),
                radius * Math.sin(angle)
            );
        }

        @Override
        public String toString() {
            double r = Math.abs(real) < 5e-12 ? 0.0 : real;
            double i = Math.abs(imaginary) < 5e-12
                ? 0.0
                : imaginary;

            if (i == 0.0) {
                return String.format("%.5f", r);
            }

            if (r == 0.0) {
                return String.format("%.5fi", i);
            }

            return String.format(
                "%.5f %s %.5fi",
                r,
                i >= 0 ? "+" : "-",
                Math.abs(i)
            );
        }
    }

    public record QuantumState(Complex[] amplitudes) {

        public QuantumState {
            if (amplitudes == null || amplitudes.length == 0) {
                throw new IllegalArgumentException(
                    "A quantum state cannot be empty."
                );
            }

            if (!isPowerOfTwo(amplitudes.length)) {
                throw new IllegalArgumentException(
                    "Quantum-state dimension must be a power of two."
                );
            }

            amplitudes = amplitudes.clone();

            for (Complex amplitude : amplitudes) {
                if (amplitude == null) {
                    throw new IllegalArgumentException(
                        "State cannot contain null amplitudes."
                    );
                }
            }

            double normSquared = Arrays.stream(amplitudes)
                .mapToDouble(Complex::magnitudeSquared)
                .sum();

            if (Math.abs(normSquared - 1.0) > EPSILON) {
                throw new IllegalArgumentException(
                    "Quantum state must be normalized."
                );
            }
        }

        @Override
        public Complex[] amplitudes() {
            return amplitudes.clone();
        }

        public double[] probabilities() {
            return Arrays.stream(amplitudes)
                .mapToDouble(Complex::magnitudeSquared)
                .toArray();
        }
    }

    public enum TransformDirection {
        FORWARD(1.0),
        INVERSE(-1.0);

        private final double phaseSign;

        TransformDirection(double phaseSign) {
            this.phaseSign = phaseSign;
        }

        public double phaseSign() {
            return phaseSign;
        }
    }

    public static final class QftService {

        public QuantumState transform(
            QuantumState input,
            TransformDirection direction
        ) {
            if (input == null || direction == null) {
                throw new IllegalArgumentException(
                    "Input state and direction are required."
                );
            }

            Complex[] state = input.amplitudes();
            int n = state.length;
            double scale = 1.0 / Math.sqrt(n);

            Complex[] output = new Complex[n];

            for (int k = 0; k < n; k++) {
                Complex accumulator = new Complex(0, 0);

                for (int j = 0; j < n; j++) {
                    double angle =
                        direction.phaseSign()
                        * 2.0
                        * PI
                        * j
                        * k
                        / n;

                    Complex phase = Complex.polar(1.0, angle);

                    accumulator = accumulator.add(
                        state[j].multiply(phase)
                    );
                }

                output[k] = accumulator.scale(scale);
            }

            return new QuantumState(output);
        }

        public double unitarityError(int qubits) {
            if (qubits < 1 || qubits > 12) {
                throw new IllegalArgumentException(
                    "Qubit count must be between 1 and 12 for matrix verification."
                );
            }

            int n = 1 << qubits;
            Complex[][] matrix = new Complex[n][n];

            for (int row = 0; row < n; row++) {
                for (int column = 0; column < n; column++) {
                    double angle =
                        2.0 * PI * row * column / n;

                    matrix[row][column] =
                        Complex.polar(1.0 / Math.sqrt(n), angle);
                }
            }

            double maximumError = 0.0;

            for (int row = 0; row < n; row++) {
                for (int column = 0; column < n; column++) {
                    Complex inner = new Complex(0, 0);

                    for (int k = 0; k < n; k++) {
                        inner = inner.add(
                            matrix[row][k]
                                .conjugate()
                                .multiply(matrix[column][k])
                        );
                    }

                    Complex expected =
                        row == column
                            ? new Complex(1, 0)
                            : new Complex(0, 0);

                    maximumError = Math.max(
                        maximumError,
                        inner.add(expected.scale(-1)).magnitude()
                    );
                }
            }

            return maximumError;
        }
    }

    public static QuantumState normalized(Complex... values) {
        if (values.length == 0) {
            throw new IllegalArgumentException(
                "Cannot normalize an empty vector."
            );
        }

        double norm = Math.sqrt(
            Arrays.stream(values)
                .mapToDouble(Complex::magnitudeSquared)
                .sum()
        );

        if (norm <= EPSILON) {
            throw new IllegalArgumentException(
                "Cannot normalize the zero vector."
            );
        }

        Complex[] normalized = Arrays.stream(values)
            .map(value -> value.scale(1.0 / norm))
            .toArray(Complex[]::new);

        return new QuantumState(normalized);
    }

    public static QuantumState basisState(
        int qubits,
        int index
    ) {
        if (qubits < 1 || qubits > 20) {
            throw new IllegalArgumentException(
                "Qubit count must be between 1 and 20."
            );
        }

        int dimension = 1 << qubits;

        if (index < 0 || index >= dimension) {
            throw new IllegalArgumentException(
                "Basis-state index is outside the register."
            );
        }

        Complex[] amplitudes = new Complex[dimension];

        Arrays.fill(
            amplitudes,
            new Complex(0, 0)
        );

        amplitudes[index] = new Complex(1, 0);

        return new QuantumState(amplitudes);
    }

    public static double maximumError(
        QuantumState first,
        QuantumState second
    ) {
        Complex[] a = first.amplitudes();
        Complex[] b = second.amplitudes();

        if (a.length != b.length) {
            throw new IllegalArgumentException(
                "States must have equal dimensions."
            );
        }

        double maximum = 0.0;

        for (int i = 0; i < a.length; i++) {
            maximum = Math.max(
                maximum,
                a[i].add(b[i].scale(-1)).magnitude()
            );
        }

        return maximum;
    }

    public static int sampleMeasurement(
        QuantumState state,
        Random random
    ) {
        if (random == null) {
            throw new IllegalArgumentException(
                "Random source is required."
            );
        }

        double target = random.nextDouble();
        double cumulative = 0.0;
        double[] probabilities = state.probabilities();

        for (int i = 0; i < probabilities.length; i++) {
            cumulative += probabilities[i];

            if (target < cumulative) {
                return i;
            }
        }

        return probabilities.length - 1;
    }

    public static int[] measure(
        QuantumState state,
        int shots,
        Random random
    ) {
        if (shots <= 0) {
            throw new IllegalArgumentException(
                "Shots must be positive."
            );
        }

        int[] counts = new int[state.amplitudes().length];

        for (int shot = 0; shot < shots; shot++) {
            counts[sampleMeasurement(state, random)]++;
        }

        return counts;
    }

    private static boolean isPowerOfTwo(int value) {
        return value > 0 && (value & (value - 1)) == 0;
    }

    private static void printState(
        String title,
        QuantumState state
    ) {
        System.out.println(title);

        Complex[] amplitudes = state.amplitudes();
        int width = Integer.numberOfTrailingZeros(
            Integer.highestOneBit(amplitudes.length)
        );

        for (int index = 0; index < amplitudes.length; index++) {
            String binary = String.format(
                "%" + width + "s",
                Integer.toBinaryString(index)
            ).replace(' ', '0');

            System.out.printf(
                "  |%s>: %s%n",
                binary,
                amplitudes[index]
            );
        }
    }

    public static void main(String[] args) {
        try {
            System.out.println(
                "Quantum Fourier Transform fundamentals"
            );
            System.out.println(
                "======================================"
            );

            QftService service = new QftService();

            double unitaryError =
                service.unitarityError(3);

            System.out.printf(
                "3-qubit QFT matrix unitarity error: %.3e%n%n",
                unitaryError
            );

            if (unitaryError > 1e-9) {
                throw new IllegalStateException(
                    "QFT matrix failed unitarity verification."
                );
            }

            QuantumState basis =
                basisState(3, 1);

            QuantumState transformed =
                service.transform(
                    basis,
                    TransformDirection.FORWARD
                );

            printState(
                "QFT(|001>):",
                transformed
            );

            System.out.println(
                "Measurement probabilities:"
            );

            double[] probabilities =
                transformed.probabilities();

            for (int index = 0;
                 index < probabilities.length;
                 index++) {
                System.out.printf(
                    "  %d: %.6f%n",
                    index,
                    probabilities[index]
                );
            }

            QuantumState periodic =
                normalized(
                    new Complex(1, 0),
                    new Complex(0, 0),
                    new Complex(0, 0),
                    new Complex(0, 0),
                    new Complex(1, 0),
                    new Complex(0, 0),
                    new Complex(0, 0),
                    new Complex(0, 0)
                );

            QuantumState periodicTransform =
                service.transform(
                    periodic,
                    TransformDirection.FORWARD
                );

            printState(
                "\nQFT of periodic input:",
                periodicTransform
            );

            QuantumState original =
                normalized(
                    new Complex(1, 1),
                    new Complex(2, -1),
                    new Complex(-1, 0.5),
                    new Complex(0.25, -2)
                );

            QuantumState forward =
                service.transform(
                    original,
                    TransformDirection.FORWARD
                );

            QuantumState recovered =
                service.transform(
                    forward,
                    TransformDirection.INVERSE
                );

            double reconstructionError =
                maximumError(
                    original,
                    recovered
                );

            System.out.printf(
                "\nInverse-QFT reconstruction error: %.3e%n",
                reconstructionError
            );

            if (reconstructionError > 1e-9) {
                throw new IllegalStateException(
                    "Inverse QFT failed verification."
                );
            }

            int[] counts = measure(
                periodic,
                2000,
                new Random(42)
            );

            System.out.println(
                "\nMeasurement counts from periodic input:"
            );

            for (int index = 0;
                 index < counts.length;
                 index++) {
                System.out.printf(
                    "  %d: %d%n",
                    index,
                    counts[index]
                );
            }

            System.out.println(
                "\nAll QFT checks completed successfully."
            );
        }
        catch (RuntimeException error) {
            System.err.println(
                "Execution failed: "
                + error.getMessage()
            );
            System.exit(1);
        }
    }
}
