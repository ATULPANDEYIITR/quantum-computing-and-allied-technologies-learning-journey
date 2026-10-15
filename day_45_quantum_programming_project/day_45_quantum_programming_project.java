import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

/*
 * Enterprise-oriented multi-qubit circuit model.
 *
 * The domain model separates circuit construction, gate validation, execution,
 * measurement sampling, and experiment policy. It uses Java 17 standard
 * library facilities and requires no external quantum SDK.
 *
 * Save as QuantumCircuit.java.
 * Compile: javac QuantumCircuit.java
 * Run: java QuantumCircuit
 */
public class QuantumCircuit {
    private static final double EPSILON = 1e-10;
    private static final int MAX_QUBITS = 20;

    public record Complex(double re, double im) {
        public Complex add(Complex other) {
            return new Complex(re + other.re, im + other.im);
        }

        public Complex multiply(Complex other) {
            return new Complex(
                re * other.re - im * other.im,
                re * other.im + im * other.re
            );
        }

        public Complex scale(double factor) {
            return new Complex(re * factor, im * factor);
        }

        public Complex conjugate() {
            return new Complex(re, -im);
        }

        public double magnitudeSquared() {
            return re * re + im * im;
        }

        public static Complex zero() {
            return new Complex(0, 0);
        }

        public static Complex one() {
            return new Complex(1, 0);
        }
    }

    public enum GateKind {
        HADAMARD, PAULI_X, PAULI_Z, ROTATION_Y, CONTROLLED_X, MULTI_CONTROLLED_X
    }

    public enum ExperimentStatus {
        DRAFT, VALIDATED, EXECUTED, REJECTED
    }

    public record GateOperation(
        GateKind kind,
        int target,
        List<Integer> controls,
        double angle
    ) {
        public GateOperation {
            Objects.requireNonNull(kind, "Gate kind is required.");
            controls = List.copyOf(controls);
            if (!Double.isFinite(angle)) {
                throw new IllegalArgumentException("Gate angle must be finite.");
            }
        }
    }

    public static final class CircuitPolicy {
        private final int maximumQubits;
        private final int maximumOperations;
        private final boolean requireEntanglingGate;

        public CircuitPolicy(
            int maximumQubits,
            int maximumOperations,
            boolean requireEntanglingGate
        ) {
            if (maximumQubits < 1 || maximumQubits > MAX_QUBITS) {
                throw new IllegalArgumentException("Invalid qubit policy limit.");
            }
            if (maximumOperations < 0) {
                throw new IllegalArgumentException("Operation limit cannot be negative.");
            }
            this.maximumQubits = maximumQubits;
            this.maximumOperations = maximumOperations;
            this.requireEntanglingGate = requireEntanglingGate;
        }

        public void validate(QuantumCircuit circuit) {
            if (circuit.qubitCount > maximumQubits) {
                throw new IllegalStateException("Circuit exceeds the qubit policy.");
            }
            if (circuit.operations.size() > maximumOperations) {
                throw new IllegalStateException("Circuit exceeds the gate budget.");
            }

            if (requireEntanglingGate &&
                circuit.operations.stream().noneMatch(
                    operation -> !operation.controls().isEmpty()
                )) {
                throw new IllegalStateException(
                    "This experiment requires a controlled operation."
                );
            }
        }
    }

    private final int qubitCount;
    private final int dimension;
    private final Random random;
    private final List<GateOperation> operations = new ArrayList<>();
    private Complex[] state;
    private ExperimentStatus status = ExperimentStatus.DRAFT;

    public QuantumCircuit(int qubitCount, long seed) {
        if (qubitCount < 1 || qubitCount > MAX_QUBITS) {
            throw new IllegalArgumentException(
                "Qubit count must be between 1 and " + MAX_QUBITS + "."
            );
        }

        this.qubitCount = qubitCount;
        this.dimension = 1 << qubitCount;
        this.random = new Random(seed);
        this.state = new Complex[dimension];
        for (int index = 0; index < dimension; index++) {
            state[index] = Complex.zero();
        }
        state[0] = Complex.one();
    }

    public int qubitCount() {
        return qubitCount;
    }

    public ExperimentStatus status() {
        return status;
    }

    public List<GateOperation> operations() {
        return Collections.unmodifiableList(operations);
    }

    private Complex[][] matrix(GateKind kind, double angle) {
        return switch (kind) {
            case HADAMARD -> {
                double s = 1.0 / Math.sqrt(2.0);
                yield new Complex[][] {
                    {new Complex(s, 0), new Complex(s, 0)},
                    {new Complex(s, 0), new Complex(-s, 0)}
                };
            }
            case PAULI_X, CONTROLLED_X, MULTI_CONTROLLED_X -> new Complex[][] {
                {Complex.zero(), Complex.one()},
                {Complex.one(), Complex.zero()}
            };
            case PAULI_Z -> new Complex[][] {
                {Complex.one(), Complex.zero()},
                {Complex.zero(), new Complex(-1, 0)}
            };
            case ROTATION_Y -> new Complex[][] {
                {new Complex(Math.cos(angle / 2), 0),
                 new Complex(-Math.sin(angle / 2), 0)},
                {new Complex(Math.sin(angle / 2), 0),
                 new Complex(Math.cos(angle / 2), 0)}
            };
        };
    }

    private void validateOperation(GateOperation operation) {
        if (operation.target() < 0 || operation.target() >= qubitCount) {
            throw new IllegalArgumentException("Target qubit is out of range.");
        }

        EnumSet<GateKind> controlledKinds = EnumSet.of(
            GateKind.CONTROLLED_X,
            GateKind.MULTI_CONTROLLED_X
        );

        if (!controlledKinds.contains(operation.kind()) &&
            !operation.controls().isEmpty()) {
            throw new IllegalArgumentException(
                "This gate kind does not accept control qubits."
            );
        }

        if (controlledKinds.contains(operation.kind()) &&
            operation.controls().isEmpty()) {
            throw new IllegalArgumentException(
                "A controlled gate requires at least one control."
            );
        }

        if (operation.controls().stream().distinct().count()
            != operation.controls().size()) {
            throw new IllegalArgumentException("Duplicate control qubit.");
        }

        for (int control : operation.controls()) {
            if (control < 0 || control >= qubitCount ||
                control == operation.target()) {
                throw new IllegalArgumentException("Invalid control qubit.");
            }
        }

        if (operation.kind() == GateKind.CONTROLLED_X &&
            operation.controls().size() != 1) {
            throw new IllegalArgumentException(
                "Controlled-X requires exactly one control."
            );
        }
    }

    public void addGate(GateOperation operation) {
        if (status == ExperimentStatus.EXECUTED) {
            throw new IllegalStateException(
                "An executed circuit cannot be modified; create a new experiment."
            );
        }

        validateOperation(operation);

        if (operations.size() >= 100_000) {
            throw new IllegalStateException("Circuit operation budget exceeded.");
        }

        operations.add(operation);
        status = ExperimentStatus.DRAFT;
    }

    public void h(int target) {
        addGate(new GateOperation(GateKind.HADAMARD, target, List.of(), 0));
    }

    public void x(int target) {
        addGate(new GateOperation(GateKind.PAULI_X, target, List.of(), 0));
    }

    public void z(int target) {
        addGate(new GateOperation(GateKind.PAULI_Z, target, List.of(), 0));
    }

    public void ry(int target, double angle) {
        addGate(new GateOperation(GateKind.ROTATION_Y, target, List.of(), angle));
    }

    public void cx(int control, int target) {
        addGate(new GateOperation(
            GateKind.CONTROLLED_X, target, List.of(control), 0
        ));
    }

    public void mcx(List<Integer> controls, int target) {
        addGate(new GateOperation(
            GateKind.MULTI_CONTROLLED_X, target, controls, 0
        ));
    }

    public void validate(CircuitPolicy policy) {
        Objects.requireNonNull(policy, "Circuit policy is required.");
        try {
            policy.validate(this);
            status = ExperimentStatus.VALIDATED;
        } catch (RuntimeException exception) {
            status = ExperimentStatus.REJECTED;
            throw exception;
        }
    }

    public void execute() {
        if (status != ExperimentStatus.VALIDATED) {
            throw new IllegalStateException(
                "A circuit must pass policy validation before execution."
            );
        }

        for (GateOperation operation : operations) {
            apply(operation);
            assertNormalized();
        }
        status = ExperimentStatus.EXECUTED;
    }

    private void apply(GateOperation operation) {
        Complex[][] gate = matrix(operation.kind(), operation.angle());
        int targetMask = 1 << (qubitCount - operation.target() - 1);
        int controlMask = 0;

        for (int control : operation.controls()) {
            controlMask |= 1 << (qubitCount - control - 1);
        }

        Complex[] next = state.clone();

        for (int index = 0; index < dimension; index++) {
            if ((index & targetMask) != 0) {
                continue;
            }
            if ((index & controlMask) != controlMask) {
                continue;
            }

            int partner = index | targetMask;
            Complex a0 = state[index];
            Complex a1 = state[partner];

            next[index] = gate[0][0].multiply(a0)
                .add(gate[0][1].multiply(a1));
            next[partner] = gate[1][0].multiply(a0)
                .add(gate[1][1].multiply(a1));
        }

        state = next;
    }

    private void assertNormalized() {
        double norm = 0;
        for (Complex amplitude : state) {
            norm += amplitude.magnitudeSquared();
        }
        if (Math.abs(norm - 1.0) > 1e-8) {
            throw new IllegalStateException("State vector is not normalized.");
        }
    }

    public Map<String, Double> probabilities() {
        Map<String, Double> result = new LinkedHashMap<>();
        for (int index = 0; index < dimension; index++) {
            double probability = state[index].magnitudeSquared();
            if (probability > EPSILON) {
                result.put(
                    String.format("%" + qubitCount + "s",
                        Integer.toBinaryString(index)).replace(' ', '0'),
                    probability
                );
            }
        }
        return Collections.unmodifiableMap(result);
    }

    public Map<String, Integer> runShots(int shots) {
        if (status != ExperimentStatus.EXECUTED) {
            throw new IllegalStateException("Execute the circuit before sampling.");
        }
        if (shots < 1 || shots > 1_000_000) {
            throw new IllegalArgumentException("Invalid shot count.");
        }

        Map<String, Integer> counts = new LinkedHashMap<>();
        for (int shot = 0; shot < shots; shot++) {
            double draw = random.nextDouble();
            double cumulative = 0;

            for (int index = 0; index < dimension; index++) {
                cumulative += state[index].magnitudeSquared();
                if (draw < cumulative || index == dimension - 1) {
                    String bits = String.format(
                        "%" + qubitCount + "s", Integer.toBinaryString(index)
                    ).replace(' ', '0');
                    counts.merge(bits, 1, Integer::sum);
                    break;
                }
            }
        }
        return Collections.unmodifiableMap(counts);
    }

    public void printReport() {
        System.out.println("Experiment status: " + status);
        System.out.println("Qubits: " + qubitCount);
        System.out.println("Gate operations:");
        for (GateOperation operation : operations) {
            System.out.printf(
                "  %-20s target=q%d controls=%s angle=%.5f%n",
                operation.kind(), operation.target(),
                operation.controls(), operation.angle()
            );
        }
        System.out.println("Probabilities: " + probabilities());
    }

    private static void demonstrateBellState() {
        QuantumCircuit bell = new QuantumCircuit(2, 101);
        bell.h(0);
        bell.cx(0, 1);

        CircuitPolicy policy = new CircuitPolicy(5, 20, true);
        bell.validate(policy);
        bell.execute();

        Map<String, Double> probabilities = bell.probabilities();
        if (Math.abs(probabilities.getOrDefault("00", 0.0) - 0.5) > 1e-8 ||
            Math.abs(probabilities.getOrDefault("11", 0.0) - 0.5) > 1e-8) {
            throw new IllegalStateException("Bell-state assertion failed.");
        }

        bell.printReport();
        System.out.println("Shot counts: " + bell.runShots(2000));

        try {
            bell.h(0);
        } catch (IllegalStateException expected) {
            System.out.println("Immutable execution policy: " + expected.getMessage());
        }
    }

    private static void demonstratePolicyRejection() {
        QuantumCircuit circuit = new QuantumCircuit(4, 2026);
        circuit.h(0);

        try {
            circuit.validate(new CircuitPolicy(3, 10, true));
        } catch (IllegalStateException expected) {
            System.out.println("Rejected by experiment policy: " + expected.getMessage());
            System.out.println("Status after rejection: " + circuit.status());
        }
    }

    public static void main(String[] args) {
        demonstrateBellState();
        System.out.println();
        demonstratePolicyRejection();

        QuantumCircuit ghz = new QuantumCircuit(3, 303);
        ghz.h(0);
        ghz.cx(0, 1);
        ghz.cx(1, 2);
        ghz.validate(new CircuitPolicy(3, 10, true));
        ghz.execute();

        System.out.println();
        System.out.println("Three-qubit GHZ state:");
        ghz.printReport();
    }
}
