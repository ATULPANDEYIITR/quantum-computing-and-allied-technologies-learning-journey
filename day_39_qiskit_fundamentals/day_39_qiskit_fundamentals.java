import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

/*
 * Qiskit Fundamentals: Installation and First Circuit
 *
 * Enterprise scenario:
 * A quantum application team needs a repeatable circuit-validation service
 * before submitting workloads to Qiskit Aer or a hardware provider.
 *
 * This program uses Java 17 standard-library features to model immutable
 * circuit operations, validate state transitions, simulate statevectors,
 * and verify measurement distributions. It is not a Qiskit Java SDK.
 *
 * Compile and execute:
 *   javac FirstCircuit.java
 *   java FirstCircuit
 *
 * Install the actual Qiskit Python packages separately:
 *   python -m pip install qiskit qiskit-aer
 */

public class FirstCircuit {
    private static final double TOLERANCE = 1e-9;

    private enum Gate {
        HADAMARD,
        PAULI_X,
        CONTROLLED_X
    }

    private record Operation(Gate gate, int control, int target) {
        Operation {
            Objects.requireNonNull(gate, "gate");

            if (control < 0 || target < 0) {
                throw new IllegalArgumentException("Qubit indices cannot be negative.");
            }

            if (gate == Gate.CONTROLLED_X && control == target) {
                throw new IllegalArgumentException(
                    "Controlled-X requires different control and target qubits."
                );
            }
        }
    }

    private record MeasurementResult(int shots, Map<String, Integer> counts) {
        MeasurementResult {
            if (shots <= 0) {
                throw new IllegalArgumentException("Shot count must be positive.");
            }

            counts = Map.copyOf(counts);

            int total = counts.values().stream()
                .mapToInt(Integer::intValue)
                .sum();

            if (total != shots) {
                throw new IllegalArgumentException(
                    "Measurement counts must sum to the shot count."
                );
            }

            if (counts.values().stream().anyMatch(count -> count < 0)) {
                throw new IllegalArgumentException(
                    "Measurement counts cannot be negative."
                );
            }
        }

        double probability(String outcome) {
            return counts.getOrDefault(outcome, 0) / (double) shots;
        }
    }

    private static final class Circuit {
        private final int qubitCount;
        private final List<Operation> operations = new ArrayList<>();

        Circuit(int qubitCount) {
            if (qubitCount < 1 || qubitCount > 12) {
                throw new IllegalArgumentException(
                    "Circuit width must be between 1 and 12 qubits."
                );
            }

            this.qubitCount = qubitCount;
        }

        Circuit h(int target) {
            validateQubit(target);
            operations.add(new Operation(Gate.HADAMARD, target, target));
            return this;
        }

        Circuit x(int target) {
            validateQubit(target);
            operations.add(new Operation(Gate.PAULI_X, target, target));
            return this;
        }

        Circuit cx(int control, int target) {
            validateQubit(control);
            validateQubit(target);
            operations.add(new Operation(Gate.CONTROLLED_X, control, target));
            return this;
        }

        private void validateQubit(int qubit) {
            if (qubit < 0 || qubit >= qubitCount) {
                throw new IndexOutOfBoundsException(
                    "Qubit " + qubit + " is outside circuit width " + qubitCount
                );
            }
        }

        List<Operation> operations() {
            return List.copyOf(operations);
        }

        double[] probabilities() {
            double[] real = new double[1 << qubitCount];
            double[] imaginary = new double[1 << qubitCount];
            real[0] = 1.0;

            for (Operation operation : operations) {
                switch (operation.gate()) {
                    case HADAMARD ->
                        applyHadamard(real, imaginary, operation.target());
                    case PAULI_X ->
                        applyX(real, imaginary, operation.target());
                    case CONTROLLED_X ->
                        applyControlledX(
                            real,
                            imaginary,
                            operation.control(),
                            operation.target()
                        );
                }
            }

            double norm = 0.0;
            double[] probabilities = new double[real.length];

            for (int index = 0; index < real.length; index++) {
                probabilities[index] =
                    real[index] * real[index] + imaginary[index] * imaginary[index];
                norm += probabilities[index];
            }

            if (Math.abs(norm - 1.0) > TOLERANCE) {
                throw new IllegalStateException(
                    "Statevector normalization failed: " + norm
                );
            }

            return probabilities;
        }

        private static void applyHadamard(
            double[] real,
            double[] imaginary,
            int target
        ) {
            int mask = 1 << target;
            double factor = 1.0 / Math.sqrt(2.0);

            for (int index = 0; index < real.length; index++) {
                if ((index & mask) != 0) {
                    continue;
                }

                int paired = index | mask;

                double realZero = real[index];
                double imaginaryZero = imaginary[index];
                double realOne = real[paired];
                double imaginaryOne = imaginary[paired];

                real[index] = (realZero + realOne) * factor;
                imaginary[index] = (imaginaryZero + imaginaryOne) * factor;
                real[paired] = (realZero - realOne) * factor;
                imaginary[paired] = (imaginaryZero - imaginaryOne) * factor;
            }
        }

        private static void applyX(
            double[] real,
            double[] imaginary,
            int target
        ) {
            int mask = 1 << target;

            for (int index = 0; index < real.length; index++) {
                if ((index & mask) == 0) {
                    int paired = index | mask;
                    swap(real, index, paired);
                    swap(imaginary, index, paired);
                }
            }
        }

        private static void applyControlledX(
            double[] real,
            double[] imaginary,
            int control,
            int target
        ) {
            int controlMask = 1 << control;
            int targetMask = 1 << target;

            for (int index = 0; index < real.length; index++) {
                if ((index & controlMask) == 0 ||
                    (index & targetMask) != 0) {
                    continue;
                }

                int paired = index | targetMask;
                swap(real, index, paired);
                swap(imaginary, index, paired);
            }
        }

        private static void swap(double[] values, int left, int right) {
            double temporary = values[left];
            values[left] = values[right];
            values[right] = temporary;
        }
    }

    private static final class CircuitValidationService {
        MeasurementResult execute(Circuit circuit, int shots, long seed) {
            Objects.requireNonNull(circuit, "circuit");

            if (shots <= 0 || shots > 10_000_000) {
                throw new IllegalArgumentException(
                    "Shot count must be between 1 and 10,000,000."
                );
            }

            double[] probabilities = circuit.probabilities();
            Random random = new Random(seed);
            Map<String, Integer> counts = new LinkedHashMap<>();
            double[] cumulative = new double[probabilities.length];

            double running = 0.0;
            for (int index = 0; index < probabilities.length; index++) {
                running += probabilities[index];
                cumulative[index] = running;
            }

            cumulative[cumulative.length - 1] = 1.0;

            for (int shot = 0; shot < shots; shot++) {
                double sample = random.nextDouble();
                int index = Arrays.binarySearch(cumulative, sample);

                if (index < 0) {
                    index = -index - 1;
                } else {
                    while (index > 0 &&
                           cumulative[index - 1] >= sample) {
                        index--;
                    }
                }

                if (index >= cumulative.length) {
                    index = cumulative.length - 1;
                }

                String outcome = bitString(index, Integer.numberOfTrailingZeros(
                    Integer.highestOneBit(probabilities.length)
                ));

                counts.merge(outcome, 1, Integer::sum);
            }

            return new MeasurementResult(shots, counts);
        }
    }

    private static String bitString(int value, int width) {
        return String.format("%" + width + "s",
            Integer.toBinaryString(value)).replace(' ', '0');
    }

    private static void printResult(
        String label,
        Circuit circuit,
        MeasurementResult result
    ) {
        System.out.println("\n" + label);
        System.out.println("Operations: " + circuit.operations());
        System.out.println("Shots: " + result.shots());

        result.counts().entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .forEach(entry -> System.out.printf(
                "  %s: %d (%.2f%%)%n",
                entry.getKey(),
                entry.getValue(),
                100.0 * entry.getValue() / result.shots()
            ));
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new IllegalStateException(message);
        }
    }

    public static void main(String[] args) {
        CircuitValidationService service = new CircuitValidationService();

        Circuit hadamard = new Circuit(1).h(0);
        MeasurementResult hadamardResult = service.execute(hadamard, 4096, 42);
        printResult("Hadamard superposition", hadamard, hadamardResult);

        require(
            Math.abs(hadamardResult.probability("1") - 0.5) < 0.06,
            "Hadamard distribution is outside the accepted tolerance."
        );

        Circuit deterministic = new Circuit(1).x(0);
        MeasurementResult deterministicResult =
            service.execute(deterministic, 128, 42);
        printResult("Deterministic X gate", deterministic, deterministicResult);

        require(
            deterministicResult.counts().equals(Map.of("1", 128)),
            "The X gate must produce only the outcome 1."
        );

        Circuit bell = new Circuit(2).h(0).cx(0, 1);
        MeasurementResult bellResult = service.execute(bell, 4096, 17);
        printResult("Bell-state correlation", bell, bellResult);

        require(
            bellResult.counts().keySet().stream()
                .allMatch(outcome -> outcome.equals("00") || outcome.equals("11")),
            "Bell-state experiment produced an impossible outcome."
        );

        try {
            new Circuit(1).cx(0, 0);
            throw new IllegalStateException("Invalid CNOT was accepted.");
        } catch (IllegalArgumentException expected) {
            System.out.println("\nInvalid gate rejected: " + expected.getMessage());
        }

        System.out.println("\nCircuit validation completed successfully.");
    }
}
