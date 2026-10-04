/*
 * Superdense Coding: enterprise-oriented quantum communication model.
 *
 * Java 17+.
 *
 * The domain model separates:
 *   - entanglement as a pre-shared communication resource,
 *   - Alice's encoding decision,
 *   - quantum-channel transmission,
 *   - Bob's Bell-basis decoding,
 *   - measurement,
 *   - and channel reliability.
 *
 * No external dependencies are required.
 */

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class SuperdenseCoding {

    private static final double SQRT_TWO_INVERSE = 1.0 / Math.sqrt(2.0);
    private static final double EPSILON = 1e-10;

    enum Message {
        ZERO_ZERO("00"),
        ZERO_ONE("01"),
        ONE_ZERO("10"),
        ONE_ONE("11");

        private final String bits;

        Message(String bits) {
            this.bits = bits;
        }

        public String bits() {
            return bits;
        }

        public static Message fromBits(String bits) {
            for (Message message : values()) {
                if (message.bits.equals(bits)) {
                    return message;
                }
            }
            throw new IllegalArgumentException(
                "Message must be 00, 01, 10, or 11."
            );
        }
    }

    enum Gate {
        IDENTITY,
        PAULI_X,
        PAULI_Z,
        PAULI_ZX
    }

    record Complex(double real, double imaginary) {
        Complex add(Complex other) {
            return new Complex(
                real + other.real,
                imaginary + other.imaginary
            );
        }

        Complex multiply(Complex other) {
            return new Complex(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        Complex scale(double scalar) {
            return new Complex(real * scalar, imaginary * scalar);
        }

        double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        @Override
        public String toString() {
            if (Math.abs(imaginary) < EPSILON) {
                return String.format("%.4f", real);
            }

            if (Math.abs(real) < EPSILON) {
                return String.format("%.4fi", imaginary);
            }

            return String.format(
                "%.4f %s %.4fi",
                real,
                imaginary >= 0 ? "+" : "-",
                Math.abs(imaginary)
            );
        }
    }

    static final class QuantumState {
        private final Complex[] amplitudes;

        QuantumState(Complex[] amplitudes) {
            this.amplitudes = amplitudes.clone();
        }

        static QuantumState basisState(String bits) {
            if (!bits.matches("[01]{2}")) {
                throw new IllegalArgumentException(
                    "A two-qubit basis state requires two binary digits."
                );
            }

            Complex[] state = zeroVector(4);
            state[Integer.parseInt(bits, 2)] = new Complex(1, 0);
            return new QuantumState(state);
        }

        static Complex[] zeroVector(int size) {
            Complex[] result = new Complex[size];

            for (int i = 0; i < size; i++) {
                result[i] = new Complex(0, 0);
            }

            return result;
        }

        double norm() {
            double total = 0;

            for (Complex amplitude : amplitudes) {
                total += amplitude.magnitudeSquared();
            }

            return Math.sqrt(total);
        }

        QuantumState normalize() {
            double stateNorm = norm();

            if (stateNorm < EPSILON) {
                throw new IllegalStateException(
                    "A zero quantum state cannot be normalized."
                );
            }

            Complex[] normalized = new Complex[amplitudes.length];

            for (int i = 0; i < amplitudes.length; i++) {
                normalized[i] = amplitudes[i].scale(1.0 / stateNorm);
            }

            return new QuantumState(normalized);
        }

        Complex[] amplitudes() {
            return amplitudes.clone();
        }

        double[] probabilities() {
            if (Math.abs(norm() - 1.0) > 1e-9) {
                throw new IllegalStateException(
                    "Measurement requires a normalized state."
                );
            }

            double[] probabilities = new double[amplitudes.length];

            for (int i = 0; i < amplitudes.length; i++) {
                probabilities[i] = amplitudes[i].magnitudeSquared();
            }

            return probabilities;
        }

        String describe() {
            String[] labels = {"00", "01", "10", "11"};
            List<String> terms = new ArrayList<>();

            for (int i = 0; i < amplitudes.length; i++) {
                if (amplitudes[i].magnitudeSquared() > EPSILON) {
                    terms.add("(" + amplitudes[i] + ")|" + labels[i] + ">");
                }
            }

            return terms.isEmpty() ? "0" : String.join(" + ", terms);
        }
    }

    static final class Matrix {
        private final Complex[][] values;

        Matrix(double[][] realValues) {
            values = new Complex[realValues.length][];

            for (int i = 0; i < realValues.length; i++) {
                values[i] = new Complex[realValues[i].length];

                for (int j = 0; j < realValues[i].length; j++) {
                    values[i][j] = new Complex(realValues[i][j], 0);
                }
            }
        }

        Matrix(Complex[][] values) {
            this.values = new Complex[values.length][];

            for (int i = 0; i < values.length; i++) {
                this.values[i] = values[i].clone();
            }
        }
    }

    static final Matrix I = new Matrix(new double[][] {
        {1, 0},
        {0, 1}
    });

    static final Matrix X = new Matrix(new double[][] {
        {0, 1},
        {1, 0}
    });

    static final Matrix Z = new Matrix(new double[][] {
        {1, 0},
        {0, -1}
    });

    static final Matrix H = new Matrix(new double[][] {
        {SQRT_TWO_INVERSE, SQRT_TWO_INVERSE},
        {SQRT_TWO_INVERSE, -SQRT_TWO_INVERSE}
    });

    static final Matrix CNOT = new Matrix(new double[][] {
        {1, 0, 0, 0},
        {0, 1, 0, 0},
        {0, 0, 0, 1},
        {0, 0, 1, 0}
    });

    static QuantumState apply(Matrix matrix, QuantumState state) {
        Complex[][] values = matrix.values;
        Complex[] input = state.amplitudes();

        if (values.length == 0 || values[0].length != input.length) {
            throw new IllegalArgumentException(
                "Matrix and state dimensions do not match."
            );
        }

        Complex[] result = QuantumState.zeroVector(values.length);

        for (int row = 0; row < values.length; row++) {
            for (int column = 0; column < input.length; column++) {
                result[row] = result[row].add(
                    values[row][column].multiply(input[column])
                );
            }
        }

        return new QuantumState(result);
    }

    static Matrix tensor(Matrix left, Matrix right) {
        Complex[][] result = new Complex[
            left.values.length * right.values.length
        ][
            left.values[0].length * right.values[0].length
        ];

        for (int i = 0; i < left.values.length; i++) {
            for (int j = 0; j < left.values[0].length; j++) {
                for (int k = 0; k < right.values.length; k++) {
                    for (int l = 0; l < right.values[0].length; l++) {
                        result[
                            i * right.values.length + k
                        ][
                            j * right.values[0].length + l
                        ] = left.values[i][j].multiply(right.values[k][l]);
                    }
                }
            }
        }

        return new Matrix(result);
    }

    static Matrix multiply(Matrix left, Matrix right) {
        if (left.values[0].length != right.values.length) {
            throw new IllegalArgumentException(
                "Matrix dimensions cannot be multiplied."
            );
        }

        Complex[][] result = new Complex[
            left.values.length
        ][
            right.values[0].length
        ];

        for (int i = 0; i < result.length; i++) {
            for (int j = 0; j < result[0].length; j++) {
                result[i][j] = new Complex(0, 0);

                for (int k = 0; k < right.values.length; k++) {
                    result[i][j] = result[i][j].add(
                        left.values[i][k].multiply(right.values[k][j])
                    );
                }
            }
        }

        return new Matrix(result);
    }

    static QuantumState singleQubitGate(
        QuantumState state,
        Matrix gate,
        int qubit
    ) {
        Matrix expanded;

        if (qubit == 0) {
            expanded = tensor(gate, I);
        } else if (qubit == 1) {
            expanded = tensor(I, gate);
        } else {
            throw new IllegalArgumentException(
                "Qubit index must be 0 or 1."
            );
        }

        return apply(expanded, state).normalize();
    }

    static QuantumState createBellPair() {
        QuantumState state = QuantumState.basisState("00");
        state = singleQubitGate(state, H, 0);
        state = apply(CNOT, state).normalize();
        return state;
    }

    static Gate gateFor(Message message) {
        return switch (message) {
            case ZERO_ZERO -> Gate.IDENTITY;
            case ZERO_ONE -> Gate.PAULI_X;
            case ONE_ZERO -> Gate.PAULI_Z;
            case ONE_ONE -> Gate.PAULI_ZX;
        };
    }

    static Matrix matrixFor(Gate gate) {
        return switch (gate) {
            case IDENTITY -> I;
            case PAULI_X -> X;
            case PAULI_Z -> Z;
            case PAULI_ZX -> multiply(Z, X);
        };
    }

    static QuantumState encode(
        QuantumState sharedPair,
        Message message
    ) {
        return singleQubitGate(
            sharedPair,
            matrixFor(gateFor(message)),
            0
        );
    }

    static QuantumState decode(QuantumState encoded) {
        QuantumState state = apply(CNOT, encoded).normalize();
        return singleQubitGate(state, H, 0);
    }

    static String measure(
        QuantumState state,
        Random random
    ) {
        double[] probabilities = state.probabilities();
        double sample = random.nextDouble();
        double cumulative = 0;

        for (int i = 0; i < probabilities.length; i++) {
            cumulative += probabilities[i];

            if (sample <= cumulative) {
                return String.format("%2s", Integer.toBinaryString(i))
                    .replace(' ', '0');
            }
        }

        return "11";
    }

    static final class QuantumChannel {
        private final double errorProbability;
        private final Random random;

        QuantumChannel(double errorProbability, Random random) {
            if (errorProbability < 0 || errorProbability > 1) {
                throw new IllegalArgumentException(
                    "Channel error probability must be between 0 and 1."
                );
            }

            this.errorProbability = errorProbability;
            this.random = random;
        }

        QuantumState transmit(QuantumState state) {
            if (random.nextDouble() >= errorProbability) {
                return state;
            }

            int error = random.nextInt(3);

            return switch (error) {
                case 0 -> singleQubitGate(state, X, 0);
                case 1 -> singleQubitGate(state, Z, 0);
                default -> singleQubitGate(
                    state,
                    multiply(X, Z),
                    0
                );
            };
        }
    }

    record Transmission(
        Message sent,
        Gate encodingGate,
        String receivedBits,
        boolean successful
    ) {}

    static final class CommunicationService {
        private final QuantumChannel channel;
        private final Random measurementRandom;

        CommunicationService(
            QuantumChannel channel,
            Random measurementRandom
        ) {
            this.channel = channel;
            this.measurementRandom = measurementRandom;
        }

        Transmission transmit(Message message) {
            QuantumState shared = createBellPair();
            QuantumState encoded = encode(shared, message);
            QuantumState received = channel.transmit(encoded);
            QuantumState decoded = decode(received);

            String measured = measure(decoded, measurementRandom);

            return new Transmission(
                message,
                gateFor(message),
                measured,
                measured.equals(message.bits())
            );
        }
    }

    static void printHeading(String title) {
        System.out.println("\n" + "=".repeat(78));
        System.out.println(title);
        System.out.println("=".repeat(78));
    }

    static void demonstrateIdealCommunication() {
        printHeading("Ideal enterprise communication service");

        CommunicationService service = new CommunicationService(
            new QuantumChannel(0.0, new Random(11)),
            new Random(12)
        );

        for (Message message : Message.values()) {
            Transmission transmission = service.transmit(message);

            System.out.printf(
                "sent=%s gate=%s received=%s successful=%s%n",
                message.bits(),
                transmission.encodingGate(),
                transmission.receivedBits(),
                transmission.successful()
            );
        }
    }

    static void demonstrateReliability() {
        printHeading("Channel reliability");

        for (double errorProbability : List.of(0.0, 0.05, 0.15, 0.30)) {
            int successes = 0;
            int trials = 1000;

            CommunicationService service = new CommunicationService(
                new QuantumChannel(
                    errorProbability,
                    new Random(100)
                ),
                new Random(200)
            );

            for (int i = 0; i < trials; i++) {
                Message message = Message.values()[i % Message.values().length];

                if (service.transmit(message).successful()) {
                    successes++;
                }
            }

            System.out.printf(
                "channel error=%.2f accuracy=%.3f%n",
                errorProbability,
                (double) successes / trials
            );
        }
    }

    static void demonstrateDomainValidation() {
        printHeading("Domain validation");

        try {
            Message.fromBits("101");
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Rejected invalid payload: " + error.getMessage()
            );
        }

        try {
            new QuantumChannel(1.5, new Random());
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Rejected invalid channel policy: " + error.getMessage()
            );
        }

        try {
            new QuantumState(
                new Complex[] {
                    new Complex(0, 0),
                    new Complex(0, 0)
                }
            ).normalize();
        } catch (IllegalStateException error) {
            System.out.println(
                "Rejected invalid quantum state: " + error.getMessage()
            );
        }
    }

    static void demonstrateResourceModel() {
        printHeading("Resource and security model");

        System.out.println(
            "The service begins with an entangled Bell pair shared between parties."
        );
        System.out.println(
            "The application payload has four possible values, representing two bits."
        );
        System.out.println(
            "Only Alice's qubit crosses the quantum communication channel."
        );
        System.out.println(
            "Bob performs a joint decoding operation after receiving Alice's qubit."
        );
        System.out.println(
            "An eavesdropper cannot replace the need for the physical channel by "
                + "merely observing the pre-shared entanglement."
        );
    }

    public static void main(String[] args) {
        demonstrateIdealCommunication();
        demonstrateReliability();
        demonstrateDomainValidation();
        demonstrateResourceModel();

        printHeading("Java model completed");
        System.out.println(
            "The enterprise model separates payload selection, quantum encoding, "
                + "channel behavior, decoding, measurement, and reliability."
        );
    }
}
