import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Enterprise-oriented quantum experiment model.
 *
 * The program models:
 * - immutable complex amplitudes
 * - validated quantum states
 * - quantum gates
 * - circuit operations
 * - measurement policies
 * - expectation values
 * - experiment execution and audit records
 *
 * Compile:
 *   javac QuantumExperiment.java
 *
 * Run:
 *   java QuantumExperiment
 */
public class QuantumExperiment {

    private static final double EPSILON = 1e-10;

    public record Complex(double real, double imaginary) {

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
            return new Complex(real * factor, imaginary * factor);
        }

        public double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        @Override
        public String toString() {
            if (Math.abs(imaginary) < EPSILON) {
                return String.format("%.6f", real);
            }

            if (Math.abs(real) < EPSILON) {
                return String.format("%.6fi", imaginary);
            }

            return String.format(
                "%.6f %s %.6fi",
                real,
                imaginary >= 0 ? "+" : "-",
                Math.abs(imaginary)
            );
        }
    }

    public record ExperimentConfig(
        String experimentName,
        int qubits,
        int shots,
        long seed
    ) {
        public ExperimentConfig {
            if (experimentName == null || experimentName.isBlank()) {
                throw new IllegalArgumentException(
                    "Experiment name is required."
                );
            }

            if (qubits < 1 || qubits > 18) {
                throw new IllegalArgumentException(
                    "Experiment size must be between 1 and 18 qubits."
                );
            }

            if (shots <= 0) {
                throw new IllegalArgumentException(
                    "Shot count must be positive."
                );
            }
        }
    }

    public enum GateType {
        HADAMARD,
        PAULI_X,
        PAULI_Y,
        PAULI_Z,
        CNOT
    }

    public record Operation(
        GateType gate,
        int target,
        Integer control
    ) {}

    public record ExperimentResult(
        String experimentName,
        Map<String, Integer> counts,
        double stateNorm
    ) {}

    public static final class Matrix {
        private final Complex[][] values;

        private Matrix(Complex[][] values) {
            this.values = values;
        }

        public static Matrix identity(int size) {
            Complex[][] values = new Complex[size][size];

            for (int row = 0; row < size; row++) {
                for (int column = 0; column < size; column++) {
                    values[row][column] =
                        new Complex(row == column ? 1 : 0, 0);
                }
            }

            return new Matrix(values);
        }

        public static Matrix x() {
            return new Matrix(
                new Complex[][] {
                    { new Complex(0, 0), new Complex(1, 0) },
                    { new Complex(1, 0), new Complex(0, 0) }
                }
            );
        }

        public static Matrix y() {
            return new Matrix(
                new Complex[][] {
                    { new Complex(0, 0), new Complex(0, -1) },
                    { new Complex(0, 1), new Complex(0, 0) }
                }
            );
        }

        public static Matrix z() {
            return new Matrix(
                new Complex[][] {
                    { new Complex(1, 0), new Complex(0, 0) },
                    { new Complex(0, 0), new Complex(-1, 0) }
                }
            );
        }

        public static Matrix hadamard() {
            double scale = 1 / Math.sqrt(2);

            return new Matrix(
                new Complex[][] {
                    {
                        new Complex(scale, 0),
                        new Complex(scale, 0)
                    },
                    {
                        new Complex(scale, 0),
                        new Complex(-scale, 0)
                    }
                }
            );
        }

        public Complex[][] values() {
            return values;
        }
    }

    public static final class QuantumState {
        private final Complex[] amplitudes;

        public QuantumState(Complex[] amplitudes) {
            if (amplitudes == null || amplitudes.length == 0) {
                throw new IllegalArgumentException(
                    "State cannot be empty."
                );
            }

            if ((amplitudes.length & (amplitudes.length - 1)) != 0) {
                throw new IllegalArgumentException(
                    "State dimension must be a power of two."
                );
            }

            this.amplitudes = amplitudes.clone();
            validateNormalization();
        }

        public static QuantumState basis(String bits) {
            if (!bits.matches("[01]+")) {
                throw new IllegalArgumentException(
                    "Basis state must contain only 0 and 1."
                );
            }

            Complex[] amplitudes =
                new Complex[1 << bits.length()];

            Arrays.fill(amplitudes, new Complex(0, 0));

            int index = Integer.parseInt(bits, 2);
            amplitudes[index] = new Complex(1, 0);

            return new QuantumState(amplitudes);
        }

        public static QuantumState normalized(Complex[] values) {
            double norm = norm(values);

            if (norm < EPSILON) {
                throw new IllegalArgumentException(
                    "Cannot normalize the zero vector."
                );
            }

            Complex[] normalized = new Complex[values.length];

            for (int index = 0; index < values.length; index++) {
                normalized[index] =
                    values[index].scale(1 / norm);
            }

            return new QuantumState(normalized);
        }

        public int qubits() {
            return Integer.numberOfTrailingZeros(
                Integer.highestOneBit(amplitudes.length)
            );
        }

        public Complex[] amplitudes() {
            return amplitudes.clone();
        }

        public double norm() {
            return norm(amplitudes);
        }

        private void validateNormalization() {
            if (Math.abs(norm(amplitudes) - 1.0) > EPSILON) {
                throw new IllegalArgumentException(
                    "Quantum state must have unit norm."
                );
            }
        }

        private static double norm(Complex[] state) {
            double sum = 0;

            for (Complex amplitude : state) {
                sum += amplitude.magnitudeSquared();
            }

            return Math.sqrt(sum);
        }

        public String format() {
            StringBuilder result = new StringBuilder();

            for (int index = 0; index < amplitudes.length; index++) {
                if (amplitudes[index].magnitudeSquared() > EPSILON) {
                    if (!result.isEmpty()) {
                        result.append(" + ");
                    }

                    String bits = Integer.toBinaryString(index)
                        .formatted("%" + qubits() + "s")
                        .replace(' ', '0');

                    result.append("(")
                        .append(amplitudes[index])
                        .append(")|")
                        .append(bits)
                        .append(">");
                }
            }

            return result.toString();
        }
    }

    public static final class QuantumCircuit {
        private final int qubits;
        private QuantumState state;
        private final List<Operation> operations =
            new ArrayList<>();

        public QuantumCircuit(int qubits) {
            if (qubits < 1 || qubits > 18) {
                throw new IllegalArgumentException(
                    "Circuit must contain between 1 and 18 qubits."
                );
            }

            this.qubits = qubits;
            this.state =
                QuantumState.basis("0".repeat(qubits));
        }

        public void applySingleQubit(
            Matrix gate,
            int target,
            GateType type
        ) {
            requireQubit(target);

            Matrix fullGate =
                expandSingleQubitGate(gate, target);

            state =
                new QuantumState(
                    multiply(fullGate.values(), state.amplitudes())
                );

            operations.add(
                new Operation(type, target, null)
            );
        }

        public void hadamard(int target) {
            applySingleQubit(
                Matrix.hadamard(),
                target,
                GateType.HADAMARD
            );
        }

        public void x(int target) {
            applySingleQubit(
                Matrix.x(),
                target,
                GateType.PAULI_X
            );
        }

        public void y(int target) {
            applySingleQubit(
                Matrix.y(),
                target,
                GateType.PAULI_Y
            );
        }

        public void z(int target) {
            applySingleQubit(
                Matrix.z(),
                target,
                GateType.PAULI_Z
            );
        }

        public void cnot(int control, int target) {
            requireQubit(control);
            requireQubit(target);

            if (control == target) {
                throw new IllegalArgumentException(
                    "CNOT control and target must differ."
                );
            }

            int dimension = 1 << qubits;
            Complex[][] operation =
                new Complex[dimension][dimension];

            for (int row = 0; row < dimension; row++) {
                Arrays.fill(
                    operation[row],
                    new Complex(0, 0)
                );
            }

            for (int column = 0; column < dimension; column++) {
                String bits = binary(column, qubits);
                String output = bits;

                if (bits.charAt(control) == '1') {
                    char[] characters = bits.toCharArray();

                    characters[target] =
                        characters[target] == '0'
                            ? '1'
                            : '0';

                    output = new String(characters);
                }

                int row = Integer.parseInt(output, 2);
                operation[row][column] =
                    new Complex(1, 0);
            }

            state =
                new QuantumState(
                    multiply(operation, state.amplitudes())
                );

            operations.add(
                new Operation(
                    GateType.CNOT,
                    target,
                    control
                )
            );
        }

        public QuantumState state() {
            return state;
        }

        public List<Operation> operations() {
            return List.copyOf(operations);
        }

        private Matrix expandSingleQubitGate(
            Matrix gate,
            int target
        ) {
            Matrix result = null;

            for (int position = 0; position < qubits; position++) {
                Matrix factor =
                    position == target
                        ? gate
                        : Matrix.identity(2);

                result = result == null
                    ? factor
                    : kron(result, factor);
            }

            return result;
        }

        private void requireQubit(int qubit) {
            if (qubit < 0 || qubit >= qubits) {
                throw new IndexOutOfBoundsException(
                    "Qubit index is outside the circuit."
                );
            }
        }
    }

    public static final class MeasurementService {
        private final Random random;

        public MeasurementService(long seed) {
            random = new Random(seed);
        }

        public Map<String, Integer> measure(
            QuantumState state,
            int shots
        ) {
            if (shots <= 0) {
                throw new IllegalArgumentException(
                    "Shots must be positive."
                );
            }

            double[] probabilities =
                new double[state.amplitudes().length];

            double cumulative = 0;

            for (int index = 0; index < probabilities.length; index++) {
                probabilities[index] =
                    state.amplitudes()[index]
                        .magnitudeSquared();

                cumulative += probabilities[index];
            }

            if (Math.abs(cumulative - 1) > EPSILON) {
                throw new IllegalStateException(
                    "Measurement probabilities are not normalized."
                );
            }

            Map<String, Integer> counts =
                new LinkedHashMap<>();

            for (int shot = 0; shot < shots; shot++) {
                double randomValue = random.nextDouble();
                double running = 0;
                int selected = probabilities.length - 1;

                for (int index = 0;
                     index < probabilities.length;
                     index++) {

                    running += probabilities[index];

                    if (randomValue <= running) {
                        selected = index;
                        break;
                    }
                }

                String bits =
                    binary(selected, state.qubits());

                counts.merge(bits, 1, Integer::sum);
            }

            return counts;
        }
    }

    public static final class GovernanceService {
        public ExperimentResult execute(
            ExperimentConfig config,
            QuantumCircuit circuit
        ) {
            if (circuit.state().qubits() != config.qubits()) {
                throw new IllegalArgumentException(
                    "Circuit size does not match experiment configuration."
                );
            }

            MeasurementService measurement =
                new MeasurementService(config.seed());

            Map<String, Integer> counts =
                measurement.measure(
                    circuit.state(),
                    config.shots()
                );

            return new ExperimentResult(
                config.experimentName(),
                counts,
                circuit.state().norm()
            );
        }
    }

    private static Complex[] multiply(
        Complex[][] matrix,
        Complex[] vector
    ) {
        if (matrix.length != vector.length) {
            throw new IllegalArgumentException(
                "Matrix and vector dimensions do not match."
            );
        }

        Complex[] result =
            new Complex[vector.length];

        for (int row = 0; row < matrix.length; row++) {
            Complex value = new Complex(0, 0);

            for (int column = 0;
                 column < vector.length;
                 column++) {

                value = value.add(
                    matrix[row][column]
                        .multiply(vector[column])
                );
            }

            result[row] = value;
        }

        return result;
    }

    private static Matrix kron(
        Matrix left,
        Matrix right
    ) {
        Complex[][] a = left.values();
        Complex[][] b = right.values();

        int rows = a.length * b.length;
        int columns = a[0].length * b[0].length;

        Complex[][] result =
            new Complex[rows][columns];

        for (int rowA = 0; rowA < a.length; rowA++) {
            for (int columnA = 0;
                 columnA < a[rowA].length;
                 columnA++) {

                for (int rowB = 0;
                     rowB < b.length;
                     rowB++) {

                    for (int columnB = 0;
                         columnB < b[rowB].length;
                         columnB++) {

                        result[
                            rowA * b.length + rowB
                        ][
                            columnA * b[rowB].length + columnB
                        ] =
                            a[rowA][columnA]
                                .multiply(
                                    b[rowB][columnB]
                                );
                    }
                }
            }
        }

        return new Matrix(result);
    }

    private static String binary(
        int value,
        int width
    ) {
        return String.format(
            "%" + width + "s",
            Integer.toBinaryString(value)
        ).replace(' ', '0');
    }

    private static Complex expectation(
        QuantumState state,
        Matrix operator
    ) {
        Complex[] transformed =
            multiply(
                operator.values(),
                state.amplitudes()
            );

        Complex result = new Complex(0, 0);

        for (int index = 0;
             index < transformed.length;
             index++) {

            result = result.add(
                state.amplitudes()[index]
                    .conjugate()
                    .multiply(transformed[index])
            );
        }

        return result;
    }

    public static void main(String[] args) {
        System.out.println(
            "Enterprise Quantum Experiment"
        );

        QuantumCircuit circuit =
            new QuantumCircuit(2);

        circuit.hadamard(0);
        circuit.cnot(0, 1);

        System.out.println(
            "State: " + circuit.state().format()
        );

        ExperimentConfig config =
            new ExperimentConfig(
                "Bell-state-correlation",
                2,
                1000,
                42L
            );

        GovernanceService service =
            new GovernanceService();

        ExperimentResult result =
            service.execute(config, circuit);

        System.out.println(
            "Experiment: " +
            result.experimentName()
        );

        System.out.println(
            "State norm: " +
            result.stateNorm()
        );

        System.out.println(
            "Measurement counts: " +
            result.counts()
        );

        Complex zExpectation =
            expectation(
                QuantumState.normalized(
                    new Complex[] {
                        new Complex(1, 0),
                        new Complex(1, 0)
                    }
                ),
                Matrix.z()
            );

        System.out.println(
            "<Z> for |+>: " +
            zExpectation
        );

        System.out.println(
            "Recorded operations: " +
            circuit.operations()
        );
    }
}
