import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.function.IntUnaryOperator;

/*
 * Enterprise-oriented Deutsch-Jozsa computation service.
 *
 * A quantum diagnostic service receives a Boolean oracle specification,
 * validates its promise, executes the circuit, and returns a typed report.
 * The simulator uses Java 17 and no external quantum SDK.
 */
public class DeutschJozsaEnterprise {

    enum FunctionClass {
        CONSTANT,
        BALANCED
    }

    record OracleSpecification(
        String identifier,
        int inputWidth,
        IntUnaryOperator function
    ) {
        OracleSpecification {
            if (identifier == null || identifier.isBlank()) {
                throw new IllegalArgumentException(
                    "Oracle identifier is required."
                );
            }

            if (inputWidth < 1 || inputWidth > 20) {
                throw new IllegalArgumentException(
                    "Input width must be between 1 and 20."
                );
            }

            Objects.requireNonNull(function, "Oracle function is required.");
        }
    }

    record ComputationReport(
        String oracleIdentifier,
        FunctionClass expectedClass,
        FunctionClass inferredClass,
        double zeroStateProbability,
        int oracleQueries,
        List<Double> measurementProbabilities
    ) {
        ComputationReport {
            measurementProbabilities =
                List.copyOf(measurementProbabilities);
        }
    }

    static final class OracleValidationException
            extends IllegalArgumentException {
        OracleValidationException(String message) {
            super(message);
        }
    }

    static final class QuantumState {
        private final int qubits;
        private final double[] real;
        private final double[] imaginary;

        QuantumState(int qubits) {
            if (qubits < 1 || qubits > 20) {
                throw new IllegalArgumentException(
                    "Unsupported quantum register size."
                );
            }

            this.qubits = qubits;
            this.real = new double[1 << qubits];
            this.imaginary = new double[1 << qubits];
            this.real[0] = 1.0;
        }

        void hadamardAll() {
            int stride = 1;

            while (stride < real.length) {
                for (int base = 0; base < real.length;
                     base += 2 * stride) {
                    for (int offset = 0; offset < stride; offset++) {
                        int left = base + offset;
                        int right = left + stride;

                        double leftReal = real[left];
                        double leftImaginary = imaginary[left];
                        double rightReal = real[right];
                        double rightImaginary = imaginary[right];

                        real[left] = leftReal + rightReal;
                        imaginary[left] = leftImaginary + rightImaginary;
                        real[right] = leftReal - rightReal;
                        imaginary[right] = leftImaginary - rightImaginary;
                    }
                }

                stride *= 2;
            }

            double scale = 1.0 / Math.sqrt(real.length);

            for (int i = 0; i < real.length; i++) {
                real[i] *= scale;
                imaginary[i] *= scale;
            }
        }

        void applyPhaseOracle(OracleSpecification specification) {
            if (specification.inputWidth() != qubits) {
                throw new IllegalArgumentException(
                    "Oracle width does not match the quantum register."
                );
            }

            for (int x = 0; x < real.length; x++) {
                if (specification.function().applyAsInt(x) == 1) {
                    real[x] = -real[x];
                    imaginary[x] = -imaginary[x];
                }
            }
        }

        double[] probabilities() {
            double[] probabilities = new double[real.length];

            for (int i = 0; i < real.length; i++) {
                probabilities[i] =
                    real[i] * real[i] + imaginary[i] * imaginary[i];
            }

            return probabilities;
        }
    }

    static final class OracleRegistry {
        private OracleRegistry() {}

        static FunctionClass validate(OracleSpecification specification) {
            int dimension = 1 << specification.inputWidth();
            int ones = 0;

            for (int x = 0; x < dimension; x++) {
                int output = specification.function().applyAsInt(x);

                if (output != 0 && output != 1) {
                    throw new OracleValidationException(
                        "Oracle must return 0 or 1 at input " + x
                    );
                }

                ones += output;
            }

            if (ones == 0 || ones == dimension) {
                return FunctionClass.CONSTANT;
            }

            if (ones * 2 == dimension) {
                return FunctionClass.BALANCED;
            }

            throw new OracleValidationException(
                "Oracle violates the constant-or-balanced promise."
            );
        }
    }

    static final class ComputationService {
        ComputationReport execute(OracleSpecification specification) {
            FunctionClass expected =
                OracleRegistry.validate(specification);

            QuantumState state = new QuantumState(
                specification.inputWidth()
            );

            state.hadamardAll();
            state.applyPhaseOracle(specification);
            state.hadamardAll();

            double[] probabilities = state.probabilities();
            double zeroProbability = probabilities[0];

            FunctionClass inferred =
                Math.abs(zeroProbability - 1.0) < 1e-9
                    ? FunctionClass.CONSTANT
                    : FunctionClass.BALANCED;

            if (expected != inferred) {
                throw new IllegalStateException(
                    "Quantum computation did not match the promise."
                );
            }

            List<Double> results = new ArrayList<>(probabilities.length);
            for (double probability : probabilities) {
                results.add(probability);
            }

            return new ComputationReport(
                specification.identifier(),
                expected,
                inferred,
                zeroProbability,
                1,
                results
            );
        }
    }

    static OracleSpecification paritySpecification(
        String identifier,
        int width
    ) {
        int mask = (1 << width) - 1;

        return new OracleSpecification(
            identifier,
            width,
            x -> Integer.bitCount(x & mask) & 1
        );
    }

    private static void display(ComputationReport report) {
        System.out.println("\nOracle: " + report.oracleIdentifier());
        System.out.println("Expected classification: " + report.expectedClass());
        System.out.println("Circuit classification: " + report.inferredClass());
        System.out.printf(
            "Probability of |0...0>: %.6f%n",
            report.zeroStateProbability()
        );
        System.out.println("Oracle queries: " + report.oracleQueries());
    }

    public static void main(String[] args) {
        ComputationService service = new ComputationService();

        OracleSpecification calibration = new OracleSpecification(
            "constant-calibration",
            3,
            x -> 0
        );

        OracleSpecification parity = paritySpecification(
            "three-qubit-parity",
            3
        );

        display(service.execute(calibration));
        display(service.execute(parity));

        OracleSpecification invalid = new OracleSpecification(
            "invalid-single-mark",
            3,
            x -> x == 0 ? 1 : 0
        );

        try {
            service.execute(invalid);
            throw new IllegalStateException(
                "Invalid oracle was accepted."
            );
        } catch (OracleValidationException expected) {
            System.out.println(
                "\nRejected invalid oracle: " + expected.getMessage()
            );
        }

        System.out.println(
            "\nThe service models oracle validation separately from circuit "
            + "execution so invalid specifications cannot be mistaken for "
            + "valid quantum classifications."
        );
    }
}
