import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/*
 * QFT Implementation: Build QFT circuits.
 *
 * Enterprise-oriented domain model for constructing, validating, executing,
 * and auditing Quantum Fourier Transform circuits.
 *
 * The implementation uses an immutable gate record and explicit domain
 * policies. The execution engine operates on a state vector and supports
 * forward and inverse QFT execution.
 *
 * Qubit 0 is the least-significant bit.
 */
public class QFTImplementation {

    private static final double EPSILON = 1e-10;
    private static final double PI = Math.PI;

    enum GateType {
        HADAMARD,
        CONTROLLED_PHASE,
        SWAP
    }

    enum ExecutionStatus {
        ACCEPTED,
        REJECTED,
        COMPLETED
    }

    record Gate(
        GateType type,
        int target,
        int control,
        int second,
        double angle
    ) {
        Gate {
            if (type == null) {
                throw new IllegalArgumentException("Gate type is required.");
            }

            if (target < 0) {
                throw new IllegalArgumentException("Target qubit is invalid.");
            }

            if (type == GateType.CONTROLLED_PHASE) {
                if (control < 0 || control == target) {
                    throw new IllegalArgumentException(
                        "Controlled phase requires a distinct control qubit."
                    );
                }
            }

            if (type == GateType.SWAP && second < 0) {
                throw new IllegalArgumentException(
                    "SWAP requires two qubit positions."
                );
            }
        }
    }

    record ExecutionReport(
        ExecutionStatus status,
        int gateCount,
        int qubitCount,
        double normalizationError,
        String message
    ) {}

    static final class QuantumState {
        private final ComplexNumber[] amplitudes;

        QuantumState(ComplexNumber[] amplitudes) {
            if (amplitudes == null || amplitudes.length == 0) {
                throw new IllegalArgumentException(
                    "Quantum state cannot be empty."
                );
            }

            if (!isPowerOfTwo(amplitudes.length)) {
                throw new IllegalArgumentException(
                    "State dimension must be a power of two."
                );
            }

            double norm = 0.0;

            for (ComplexNumber amplitude : amplitudes) {
                norm += amplitude.magnitudeSquared();
            }

            if (norm < EPSILON) {
                throw new IllegalArgumentException(
                    "Quantum state cannot have zero norm."
                );
            }

            double scale = 1.0 / Math.sqrt(norm);
            this.amplitudes = new ComplexNumber[amplitudes.length];

            for (int i = 0; i < amplitudes.length; i++) {
                this.amplitudes[i] =
                    amplitudes[i].scale(scale);
            }
        }

        static QuantumState basis(int qubits, int index) {
            if (qubits < 1 || qubits > 20) {
                throw new IllegalArgumentException(
                    "Supported state size is 1 through 20 qubits."
                );
            }

            int dimension = 1 << qubits;

            if (index < 0 || index >= dimension) {
                throw new IllegalArgumentException(
                    "Basis index is outside the state space."
                );
            }

            ComplexNumber[] values =
                new ComplexNumber[dimension];

            Arrays.fill(values, ComplexNumber.ZERO);
            values[index] = ComplexNumber.ONE;

            return new QuantumState(values);
        }

        int qubits() {
            return Integer.numberOfTrailingZeros(
                Integer.highestOneBit(amplitudes.length)
            );
        }

        int dimension() {
            return amplitudes.length;
        }

        ComplexNumber[] copyAmplitudes() {
            return amplitudes.clone();
        }

        double normalizationError() {
            double norm = 0.0;

            for (ComplexNumber amplitude : amplitudes) {
                norm += amplitude.magnitudeSquared();
            }

            return Math.abs(norm - 1.0);
        }
    }

    record ComplexNumber(double real, double imaginary) {
        static final ComplexNumber ZERO =
            new ComplexNumber(0.0, 0.0);

        static final ComplexNumber ONE =
            new ComplexNumber(1.0, 0.0);

        ComplexNumber add(ComplexNumber other) {
            return new ComplexNumber(
                real + other.real,
                imaginary + other.imaginary
            );
        }

        ComplexNumber subtract(ComplexNumber other) {
            return new ComplexNumber(
                real - other.real,
                imaginary - other.imaginary
            );
        }

        ComplexNumber multiply(ComplexNumber other) {
            return new ComplexNumber(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        ComplexNumber scale(double factor) {
            return new ComplexNumber(
                real * factor,
                imaginary * factor
            );
        }

        double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        double magnitude() {
            return Math.hypot(real, imaginary);
        }

        ComplexNumber conjugate() {
            return new ComplexNumber(real, -imaginary);
        }

        static ComplexNumber phase(double angle) {
            return new ComplexNumber(
                Math.cos(angle),
                Math.sin(angle)
            );
        }
    }

    static final class QFTPolicy {
        private final int maximumQubits;
        private final boolean requireNormalizedInput;

        QFTPolicy(int maximumQubits, boolean requireNormalizedInput) {
            if (maximumQubits < 1 || maximumQubits > 20) {
                throw new IllegalArgumentException(
                    "Maximum qubit policy must be between 1 and 20."
                );
            }

            this.maximumQubits = maximumQubits;
            this.requireNormalizedInput = requireNormalizedInput;
        }

        void validate(QuantumState state, int circuitQubits) {
            if (circuitQubits > maximumQubits) {
                throw new IllegalArgumentException(
                    "Circuit exceeds the configured simulation policy."
                );
            }

            if (state.qubits() != circuitQubits) {
                throw new IllegalArgumentException(
                    "State and circuit qubit counts do not match."
                );
            }

            if (requireNormalizedInput &&
                state.normalizationError() > EPSILON) {
                throw new IllegalArgumentException(
                    "Input state is not normalized."
                );
            }
        }
    }

    static final class QFTCircuit {
        private final int qubits;
        private final List<Gate> gates;

        QFTCircuit(int qubits) {
            if (qubits < 1 || qubits > 20) {
                throw new IllegalArgumentException(
                    "QFT circuit must contain 1 through 20 qubits."
                );
            }

            this.qubits = qubits;
            this.gates = Collections.unmodifiableList(build());
        }

        int qubits() {
            return qubits;
        }

        List<Gate> gates() {
            return gates;
        }

        private List<Gate> build() {
            List<Gate> result = new ArrayList<>();

            /*
             * Each Hadamard creates a local superposition. Controlled
             * rotations then encode progressively smaller phase increments.
             * Final swaps correct the reversed output ordering.
             */
            for (int target = 0; target < qubits; target++) {
                result.add(new Gate(
                    GateType.HADAMARD,
                    target,
                    -1,
                    -1,
                    0.0
                ));

                for (
                    int control = target + 1;
                    control < qubits;
                    control++
                ) {
                    int distance = control - target;

                    result.add(new Gate(
                        GateType.CONTROLLED_PHASE,
                        target,
                        control,
                        -1,
                        PI / Math.pow(2.0, distance)
                    ));
                }
            }

            for (int left = 0; left < qubits / 2; left++) {
                int right = qubits - 1 - left;

                result.add(new Gate(
                    GateType.SWAP,
                    left,
                    -1,
                    right,
                    0.0
                ));
            }

            return result;
        }

        QuantumState execute(
            QuantumState input,
            QFTPolicy policy
        ) {
            policy.validate(input, qubits);

            ComplexNumber[] values = input.copyAmplitudes();

            for (Gate gate : gates) {
                apply(values, gate);
            }

            return new QuantumState(values);
        }

        QuantumState executeInverse(
            QuantumState input,
            QFTPolicy policy
        ) {
            policy.validate(input, qubits);

            ComplexNumber[] values = input.copyAmplitudes();

            for (int index = gates.size() - 1;
                 index >= 0;
                 index--) {

                Gate gate = gates.get(index);

                if (gate.type() ==
                    GateType.CONTROLLED_PHASE) {

                    gate = new Gate(
                        gate.type(),
                        gate.target(),
                        gate.control(),
                        gate.second(),
                        -gate.angle()
                    );
                }

                apply(values, gate);
            }

            return new QuantumState(values);
        }

        private static void apply(
            ComplexNumber[] values,
            Gate gate
        ) {
            switch (gate.type()) {
                case HADAMARD ->
                    applyHadamard(values, gate.target());

                case CONTROLLED_PHASE ->
                    applyControlledPhase(
                        values,
                        gate.control(),
                        gate.target(),
                        gate.angle()
                    );

                case SWAP ->
                    applySwap(
                        values,
                        gate.target(),
                        gate.second()
                    );
            }
        }

        private static void applyHadamard(
            ComplexNumber[] values,
            int target
        ) {
            int mask = 1 << target;
            double scale = 1.0 / Math.sqrt(2.0);

            for (
                int base = 0;
                base < values.length;
                base += 2 * mask
            ) {
                for (int offset = 0;
                     offset < mask;
                     offset++) {

                    int first = base + offset;
                    int second = first + mask;

                    ComplexNumber a = values[first];
                    ComplexNumber b = values[second];

                    values[first] =
                        a.add(b).scale(scale);

                    values[second] =
                        a.subtract(b).scale(scale);
                }
            }
        }

        private static void applyControlledPhase(
            ComplexNumber[] values,
            int control,
            int target,
            double angle
        ) {
            if (control == target) {
                throw new IllegalArgumentException(
                    "Control and target must differ."
                );
            }

            int controlMask = 1 << control;
            int targetMask = 1 << target;

            ComplexNumber phase =
                ComplexNumber.phase(angle);

            for (int index = 0;
                 index < values.length;
                 index++) {

                if ((index & controlMask) != 0 &&
                    (index & targetMask) != 0) {

                    values[index] =
                        values[index].multiply(phase);
                }
            }
        }

        private static void applySwap(
            ComplexNumber[] values,
            int first,
            int second
        ) {
            if (first == second) {
                return;
            }

            int firstMask = 1 << first;
            int secondMask = 1 << second;

            for (int index = 0;
                 index < values.length;
                 index++) {

                boolean firstSet =
                    (index & firstMask) != 0;

                boolean secondSet =
                    (index & secondMask) != 0;

                if (firstSet != secondSet) {
                    int swapped =
                        index ^ firstMask ^ secondMask;

                    if (index < swapped) {
                        ComplexNumber temporary =
                            values[index];

                        values[index] =
                            values[swapped];

                        values[swapped] =
                            temporary;
                    }
                }
            }
        }
    }

    static final class MergeLikeCircuitAudit {
        /*
         * The name of this service is intentionally domain-neutral: it acts
         * as an execution audit, recording whether a circuit satisfied the
         * configured policy before and after execution.
         */
        ExecutionReport execute(
            QFTCircuit circuit,
            QuantumState state,
            QFTPolicy policy
        ) {
            try {
                policy.validate(state, circuit.qubits());

                return new ExecutionReport(
                    ExecutionStatus.ACCEPTED,
                    circuit.gates().size(),
                    circuit.qubits(),
                    state.normalizationError(),
                    "Circuit passed execution policy."
                );
            } catch (IllegalArgumentException error) {
                return new ExecutionReport(
                    ExecutionStatus.REJECTED,
                    circuit.gates().size(),
                    circuit.qubits(),
                    state.normalizationError(),
                    error.getMessage()
                );
            }
        }
    }

    static double maxDifference(
        ComplexNumber[] first,
        ComplexNumber[] second
    ) {
        if (first.length != second.length) {
            throw new IllegalArgumentException(
                "States must have equal dimensions."
            );
        }

        double maximum = 0.0;

        for (int i = 0; i < first.length; i++) {
            maximum = Math.max(
                maximum,
                first[i].subtract(second[i]).magnitude()
            );
        }

        return maximum;
    }

    static ComplexNumber[] directQFT(
        ComplexNumber[] input
    ) {
        int dimension = input.length;

        if (!isPowerOfTwo(dimension)) {
            throw new IllegalArgumentException(
                "QFT dimension must be a power of two."
            );
        }

        ComplexNumber[] result =
            new ComplexNumber[dimension];

        double scale = 1.0 / Math.sqrt(dimension);

        for (int k = 0; k < dimension; k++) {
            ComplexNumber total = ComplexNumber.ZERO;

            for (int x = 0; x < dimension; x++) {
                double angle =
                    2.0 * PI * x * k / dimension;

                total = total.add(
                    input[x].multiply(
                        ComplexNumber.phase(angle)
                    )
                );
            }

            result[k] = total.scale(scale);
        }

        return result;
    }

    static boolean isPowerOfTwo(int value) {
        return value > 0 &&
               (value & (value - 1)) == 0;
    }

    static void printState(QuantumState state) {
        for (int index = 0;
             index < state.dimension();
             index++) {

            ComplexNumber amplitude =
                state.amplitudes[index];

            if (amplitude.magnitude() <= 1e-8) {
                continue;
            }

            String bits =
                String.format(
                    Locale.ROOT,
                    "%" + state.qubits() + "s",
                    Integer.toBinaryString(index)
                ).replace(' ', '0');

            System.out.printf(
                Locale.ROOT,
                "|%s>: %.6f%+.6fi p=%.6f%n",
                bits,
                amplitude.real(),
                amplitude.imaginary(),
                amplitude.magnitudeSquared()
            );
        }
    }

    static void validate() {
        QFTPolicy policy =
            new QFTPolicy(8, true);

        for (int qubits = 1; qubits <= 5; qubits++) {
            QFTCircuit circuit =
                new QFTCircuit(qubits);

            int dimension = 1 << qubits;

            for (int index = 0;
                 index < dimension;
                 index++) {

                QuantumState input =
                    QuantumState.basis(qubits, index);

                QuantumState output =
                    circuit.execute(input, policy);

                ComplexNumber[] direct =
                    directQFT(input.amplitudes);

                if (maxDifference(
                    output.amplitudes,
                    direct
                ) > 1e-9) {
                    throw new IllegalStateException(
                        "Direct QFT validation failed."
                    );
                }

                QuantumState recovered =
                    circuit.executeInverse(
                        output,
                        policy
                    );

                if (maxDifference(
                    recovered.amplitudes,
                    input.amplitudes
                ) > 1e-9) {
                    throw new IllegalStateException(
                        "Inverse QFT validation failed."
                    );
                }
            }
        }
    }

    public static void main(String[] args) {
        try {
            validate();

            QFTPolicy policy =
                new QFTPolicy(8, true);

            QFTCircuit circuit =
                new QFTCircuit(3);

            QuantumState input =
                QuantumState.basis(3, 3);

            MergeLikeCircuitAudit audit =
                new MergeLikeCircuitAudit();

            ExecutionReport report =
                audit.execute(
                    circuit,
                    input,
                    policy
                );

            System.out.println("Execution audit:");
            System.out.println(report);
            System.out.println();

            System.out.println("QFT circuit gates:");

            for (int index = 0;
                 index < circuit.gates().size();
                 index++) {

                Gate gate = circuit.gates().get(index);

                System.out.printf(
                    Locale.ROOT,
                    "%02d. %s%n",
                    index + 1,
                    gate
                );
            }

            System.out.println("\nInput state:");
            printState(input);

            QuantumState output =
                circuit.execute(input, policy);

            System.out.println("\nQFT output:");
            printState(output);

            double referenceError =
                maxDifference(
                    output.amplitudes,
                    directQFT(input.amplitudes)
                );

            QuantumState recovered =
                circuit.executeInverse(
                    output,
                    policy
                );

            double recoveryError =
                maxDifference(
                    recovered.amplitudes,
                    input.amplitudes
                );

            System.out.printf(
                Locale.ROOT,
                "%nCircuit/direct error: %.3e%n",
                referenceError
            );

            System.out.printf(
                Locale.ROOT,
                "Inverse recovery error: %.3e%n",
                recoveryError
            );

            if (referenceError > 1e-9 ||
                recoveryError > 1e-9) {
                throw new IllegalStateException(
                    "QFT correctness checks failed."
                );
            }

            System.out.println(
                "\nComplexity: O(n * 2^n) gate-level state simulation."
            );
            System.out.println(
                "Memory: O(2^n) complex amplitudes."
            );
            System.out.println(
                "Direct reference transform: O(4^n)."
            );
        } catch (RuntimeException error) {
            System.err.println(
                "QFT execution rejected: " +
                error.getMessage()
            );
            System.exit(1);
        }
    }
}
