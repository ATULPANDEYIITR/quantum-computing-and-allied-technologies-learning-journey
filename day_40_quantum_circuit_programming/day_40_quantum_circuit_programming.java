import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Enterprise-style quantum experiment runner.
 * Compile with Java 17 or later: javac QuantumExperiment.java
 * Run with: java QuantumExperiment
 */
public class QuantumExperiment {
    private static final double TOLERANCE = 1e-9;

    record Complex(double re, double im) {
        Complex add(Complex other) {
            return new Complex(re + other.re, im + other.im);
        }

        Complex multiply(Complex other) {
            return new Complex(
                re * other.re - im * other.im,
                re * other.im + im * other.re
            );
        }

        Complex conjugate() {
            return new Complex(re, -im);
        }

        double magnitudeSquared() {
            return re * re + im * im;
        }

        Complex scale(double value) {
            return new Complex(re * value, im * value);
        }

        @Override
        public String toString() {
            return String.format("%.5f%+.5fi", re, im);
        }
    }

    enum GateType {
        HADAMARD, PAULI_X, PAULI_Z, ROTATION_Y, CONTROLLED_X
    }

    record GateOperation(
        GateType type,
        List<Integer> targets,
        List<Integer> controls,
        Complex[][] matrix
    ) {
        GateOperation {
            targets = List.copyOf(targets);
            controls = List.copyOf(controls);
            matrix = copyMatrix(matrix);
        }

        @Override
        public Complex[][] matrix() {
            return copyMatrix(matrix);
        }
    }

    static Complex[][] copyMatrix(Complex[][] source) {
        Complex[][] result = new Complex[source.length][];
        for (int i = 0; i < source.length; i++) {
            result[i] = source[i].clone();
        }
        return result;
    }

    static final Complex ZERO = new Complex(0, 0);
    static final Complex ONE = new Complex(1, 0);

    static Complex[][] matrix(Complex[][] rows) {
        Complex[][] result = copyMatrix(rows);
        validateUnitary(result);
        return result;
    }

    static void validateUnitary(Complex[][] gate) {
        if (gate.length == 0) {
            throw new IllegalArgumentException("Empty gate matrix");
        }

        for (Complex[] row : gate) {
            if (row.length != gate.length) {
                throw new IllegalArgumentException("Gate matrix must be square");
            }
        }

        for (int i = 0; i < gate.length; i++) {
            for (int j = 0; j < gate.length; j++) {
                Complex value = ZERO;
                for (int k = 0; k < gate.length; k++) {
                    value = value.add(gate[k][i].conjugate().multiply(gate[k][j]));
                }
                Complex expected = i == j ? ONE : ZERO;
                if (Math.hypot(value.re - expected.re, value.im - expected.im) > TOLERANCE) {
                    throw new IllegalArgumentException("Gate is not unitary");
                }
            }
        }
    }

    static final class Circuit {
        private final int qubits;
        private final List<GateOperation> operations = new ArrayList<>();
        private Complex[] state;
        private final Random random;
        private boolean collapsed;

        Circuit(int qubits, long seed) {
            if (qubits < 1 || qubits > 20) {
                throw new IllegalArgumentException("Qubits must be between 1 and 20");
            }
            this.qubits = qubits;
            this.random = new Random(seed);
            this.state = new Complex[1 << qubits];
            Arrays.fill(state, ZERO);
            state[0] = ONE;
        }

        private void checkQubit(int qubit) {
            if (qubit < 0 || qubit >= qubits) {
                throw new IndexOutOfBoundsException("Invalid qubit " + qubit);
            }
        }

        Circuit add(GateOperation operation) {
            if (collapsed) {
                throw new IllegalStateException("Circuit cannot be modified after measurement");
            }

            if (operation.targets().isEmpty() ||
                operation.targets().stream().distinct().count() != operation.targets().size() ||
                operation.controls().stream().distinct().count() != operation.controls().size()) {
                throw new IllegalArgumentException("Targets and controls must be unique");
            }

            for (int q : operation.targets()) checkQubit(q);
            for (int q : operation.controls()) checkQubit(q);

            if (operation.targets().stream().anyMatch(operation.controls()::contains)) {
                throw new IllegalArgumentException("Control cannot also be a target");
            }

            if (operation.matrix().length != (1 << operation.targets().size())) {
                throw new IllegalArgumentException("Matrix dimension does not match target count");
            }

            operations.add(operation);
            return this;
        }

        Circuit h(int q) {
            double s = 1 / Math.sqrt(2);
            return add(new GateOperation(
                GateType.HADAMARD, List.of(q), List.of(),
                matrix(new Complex[][] {{new Complex(s, 0), new Complex(s, 0)},
                                        {new Complex(s, 0), new Complex(-s, 0)}})
            ));
        }

        Circuit x(int q) {
            return add(new GateOperation(
                GateType.PAULI_X, List.of(q), List.of(),
                matrix(new Complex[][] {{ZERO, ONE}, {ONE, ZERO}})
            ));
        }

        Circuit z(int q) {
            return add(new GateOperation(
                GateType.PAULI_Z, List.of(q), List.of(),
                matrix(new Complex[][] {{ONE, ZERO}, {ZERO, new Complex(-1, 0)}})
            ));
        }

        Circuit ry(int q, double theta) {
            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);
            return add(new GateOperation(
                GateType.ROTATION_Y, List.of(q), List.of(),
                matrix(new Complex[][] {{new Complex(c, 0), new Complex(-s, 0)},
                                        {new Complex(s, 0), new Complex(c, 0)}})
            ));
        }

        Circuit cnot(int control, int target) {
            return add(new GateOperation(
                GateType.CONTROLLED_X, List.of(target), List.of(control),
                matrix(new Complex[][] {{ZERO, ONE}, {ONE, ZERO}})
            ));
        }

        void execute() {
            for (GateOperation operation : operations) {
                apply(operation);
            }

            double norm = 0;
            for (Complex amplitude : state) {
                norm += amplitude.magnitudeSquared();
            }

            if (Math.abs(norm - 1) > 1e-8) {
                throw new IllegalStateException("State normalization failed");
            }
        }

        private void apply(GateOperation operation) {
            int targetMask = operation.targets().stream().mapToInt(q -> 1 << q).reduce(0, (a, b) -> a | b);
            int controlMask = operation.controls().stream().mapToInt(q -> 1 << q).reduce(0, (a, b) -> a | b);
            int localDimension = 1 << operation.targets().size();
            Complex[][] gate = operation.matrix();
            Complex[] output = state.clone();

            for (int base = 0; base < state.length; base++) {
                if ((base & targetMask) != 0 || (base & controlMask) != controlMask) continue;

                int[] indices = new int[localDimension];
                for (int local = 0; local < localDimension; local++) {
                    int index = base;
                    for (int position = 0; position < operation.targets().size(); position++) {
                        if ((local & (1 << position)) != 0) {
                            index |= 1 << operation.targets().get(position);
                        }
                    }
                    indices[local] = index;
                }

                Complex[] old = new Complex[localDimension];
                for (int i = 0; i < localDimension; i++) old[i] = state[indices[i]];

                for (int row = 0; row < localDimension; row++) {
                    Complex value = ZERO;
                    for (int column = 0; column < localDimension; column++) {
                        value = value.add(gate[row][column].multiply(old[column]));
                    }
                    output[indices[row]] = value;
                }
            }
            state = output;
        }

        Map<String, Double> probabilities() {
            execute();
            Map<String, Double> result = new LinkedHashMap<>();
            for (int i = 0; i < state.length; i++) {
                double probability = state[i].magnitudeSquared();
                if (probability > 1e-12) {
                    result.put(bitString(i), probability);
                }
            }
            return result;
        }

        Map<String, Integer> sample(int shots) {
            if (shots <= 0) throw new IllegalArgumentException("Shots must be positive");
            execute();

            double[] cumulative = new double[state.length];
            double total = 0;
            for (int i = 0; i < state.length; i++) {
                total += state[i].magnitudeSquared();
                cumulative[i] = total;
            }

            Map<String, Integer> counts = new LinkedHashMap<>();
            for (int shot = 0; shot < shots; shot++) {
                double threshold = random.nextDouble() * total;
                int selected = state.length - 1;
                for (int i = 0; i < cumulative.length; i++) {
                    if (threshold < cumulative[i]) {
                        selected = i;
                        break;
                    }
                }
                counts.merge(bitString(selected), 1, Integer::sum);
            }
            return counts;
        }

        String measureAll() {
            execute();
            double threshold = random.nextDouble();
            double cumulative = 0;
            int selected = state.length - 1;

            for (int i = 0; i < state.length; i++) {
                cumulative += state[i].magnitudeSquared();
                if (threshold < cumulative) {
                    selected = i;
                    break;
                }
            }

            Arrays.fill(state, ZERO);
            state[selected] = ONE;
            collapsed = true;
            return bitString(selected);
        }

        private String bitString(int index) {
            StringBuilder bits = new StringBuilder(qubits);
            for (int q = 0; q < qubits; q++) {
                bits.append((index & (1 << q)) == 0 ? '0' : '1');
            }
            return bits.toString();
        }
    }

    record ExperimentPolicy(int maxQubits, int maxShots, double minimumProbability) {
        ExperimentPolicy {
            if (maxQubits < 1 || maxShots < 1 ||
                minimumProbability < 0 || minimumProbability > 1) {
                throw new IllegalArgumentException("Invalid experiment policy");
            }
        }

        void validate(Circuit circuit, int shots) {
            if (shots > maxShots) {
                throw new IllegalArgumentException("Shot count exceeds policy limit");
            }
            if (circuit.qubits > maxQubits) {
                throw new IllegalArgumentException("Circuit exceeds qubit limit");
            }
        }
    }

    public static void main(String[] args) {
        Circuit bell = new Circuit(2, 12345);
        bell.h(0).cnot(0, 1);

        ExperimentPolicy policy = new ExperimentPolicy(12, 100_000, 0.0);
        policy.validate(bell, 5000);

        System.out.println("Bell state probabilities: " + bell.probabilities());
        System.out.println("Bell state samples: " + bell.sample(5000));

        Circuit rotation = new Circuit(1, 99).ry(0, Math.PI / 3);
        System.out.println("Rotation probabilities: " + rotation.probabilities());

        double probabilityOne = rotation.probabilities().get("1");
        if (Math.abs(probabilityOne - 0.25) > TOLERANCE) {
            throw new AssertionError("Unexpected RY measurement probability");
        }

        Circuit interference = new Circuit(1, 9).h(0).z(0).h(0);
        Map<String, Double> interferenceResults = interference.probabilities();
        if (Math.abs(interferenceResults.getOrDefault("1", 0.0) - 1.0) > TOLERANCE) {
            throw new AssertionError("Interference check failed");
        }
        System.out.println("Interference result: " + interferenceResults);

        System.out.println("Measured rotation: " + rotation.measureAll());
        System.out.println("Quantum experiment checks passed.");
    }
}
