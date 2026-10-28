import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public class ShorCircuitComponents {

    enum GateType {
        HADAMARD,
        CONTROLLED_PHASE,
        SWAP,
        INVERSE_CONTROLLED_PHASE
    }

    record Gate(
            GateType type,
            int firstQubit,
            int secondQubit,
            double angle
    ) {}

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

        Complex scale(double value) {
            return new Complex(real * value, imaginary * value);
        }

        double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        double distance(Complex other) {
            return Math.hypot(
                    real - other.real,
                    imaginary - other.imaginary
            );
        }
    }

    static final class QuantumCircuitException extends RuntimeException {
        QuantumCircuitException(String message) {
            super(message);
        }
    }

    static final class QuantumCircuit {
        private final int qubits;
        private final List<Gate> gates = new ArrayList<>();

        QuantumCircuit(int qubits) {
            if (qubits <= 0) {
                throw new QuantumCircuitException(
                        "circuit requires at least one qubit"
                );
            }

            this.qubits = qubits;
        }

        private void validateQubit(int qubit) {
            if (qubit < 0 || qubit >= qubits) {
                throw new QuantumCircuitException(
                        "invalid qubit index: " + qubit
                );
            }
        }

        void addHadamard(int qubit) {
            validateQubit(qubit);
            gates.add(new Gate(
                    GateType.HADAMARD,
                    qubit,
                    -1,
                    0.0
            ));
        }

        void addControlledPhase(
                int control,
                int target,
                double angle
        ) {
            validateQubit(control);
            validateQubit(target);

            if (control == target) {
                throw new QuantumCircuitException(
                        "controlled phase requires two qubits"
                );
            }

            gates.add(new Gate(
                    GateType.CONTROLLED_PHASE,
                    control,
                    target,
                    angle
            ));
        }

        void addSwap(int first, int second) {
            validateQubit(first);
            validateQubit(second);

            if (first == second) {
                throw new QuantumCircuitException(
                        "SWAP requires distinct qubits"
                );
            }

            gates.add(new Gate(
                    GateType.SWAP,
                    first,
                    second,
                    0.0
            ));
        }

        void addQft(List<Integer> selected) {
            Set<Integer> unique = new HashSet<>(selected);

            if (selected.isEmpty() ||
                    unique.size() != selected.size()) {
                throw new QuantumCircuitException(
                        "QFT requires a non-empty unique qubit list"
                );
            }

            for (int targetIndex = 0;
                 targetIndex < selected.size();
                 targetIndex++) {

                int target = selected.get(targetIndex);
                addHadamard(target);

                for (int controlIndex = targetIndex + 1;
                     controlIndex < selected.size();
                     controlIndex++) {

                    int control = selected.get(controlIndex);
                    double angle = Math.PI /
                            Math.pow(
                                    2.0,
                                    controlIndex - targetIndex
                            );

                    addControlledPhase(
                            control,
                            target,
                            angle
                    );
                }
            }

            for (int i = 0; i < selected.size() / 2; i++) {
                addSwap(
                        selected.get(i),
                        selected.get(selected.size() - 1 - i)
                );
            }
        }

        List<Gate> gates() {
            return Collections.unmodifiableList(gates);
        }

        String describe() {
            StringBuilder builder = new StringBuilder();

            builder.append("Circuit: ")
                    .append(qubits)
                    .append(" qubits, ")
                    .append(gates.size())
                    .append(" gates\n");

            for (int i = 0; i < gates.size(); i++) {
                Gate gate = gates.get(i);

                builder.append(String.format(
                        "%03d: %s(%d",
                        i + 1,
                        gate.type(),
                        gate.firstQubit()
                ));

                if (gate.secondQubit() >= 0) {
                    builder.append(",")
                            .append(gate.secondQubit());
                }

                builder.append(")");

                if (gate.type() == GateType.CONTROLLED_PHASE) {
                    builder.append(String.format(
                            " angle=%.8f",
                            gate.angle()
                    ));
                }

                builder.append("\n");
            }

            return builder.toString();
        }
    }

    interface PhasePolicy {
        PhaseMeasurement select(List<PhaseMeasurement> measurements);
    }

    record PhaseMeasurement(
            long measurement,
            double measuredPhase,
            double idealPhase
    ) {}

    static final class NearestNonZeroPhasePolicy
            implements PhasePolicy {

        @Override
        public PhaseMeasurement select(
                List<PhaseMeasurement> measurements
        ) {
            return measurements.stream()
                    .filter(item -> item.measurement() > 0)
                    .findFirst()
                    .orElseThrow(() ->
                            new QuantumCircuitException(
                                    "no non-zero phase measurement"
                            )
                    );
        }
    }

    record ShorResult(
            String status,
            BigInteger base,
            BigInteger modulus,
            BigInteger period,
            long measurement,
            double phase,
            Set<BigInteger> factors
    ) {}

    static final class ShorPeriodService {
        private final PhasePolicy phasePolicy;

        ShorPeriodService(PhasePolicy phasePolicy) {
            this.phasePolicy = Objects.requireNonNull(
                    phasePolicy,
                    "phase policy"
            );
        }

        ShorResult execute(
                BigInteger base,
                BigInteger modulus,
                int countingQubits
        ) {
            validateInputs(base, modulus, countingQubits);

            if (modulus.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
                return new ShorResult(
                        "TRIVIAL_FACTOR",
                        base,
                        modulus,
                        BigInteger.ZERO,
                        0,
                        0.0,
                        Set.of(BigInteger.TWO)
                );
            }

            BigInteger commonFactor =
                    base.gcd(modulus);

            if (commonFactor.compareTo(BigInteger.ONE) > 0) {
                return new ShorResult(
                        "TRIVIAL_FACTOR",
                        base,
                        modulus,
                        BigInteger.ZERO,
                        0,
                        0.0,
                        Set.of(commonFactor)
                );
            }

            BigInteger period =
                    modularOrder(base, modulus);

            if (period == null) {
                return new ShorResult(
                        "PERIOD_NOT_FOUND",
                        base,
                        modulus,
                        BigInteger.ZERO,
                        0,
                        0.0,
                        Set.of()
                );
            }

            List<PhaseMeasurement> measurements =
                    buildIdealPhaseMeasurements(
                            period,
                            countingQubits
                    );

            PhaseMeasurement selected =
                    phasePolicy.select(measurements);

            BigInteger candidatePeriod =
                    approximatePeriod(
                            selected,
                            countingQubits,
                            modulus.longValueExact()
                    );

            Set<BigInteger> factors =
                    deriveFactors(
                            base,
                            modulus,
                            candidatePeriod
                    );

            return new ShorResult(
                    "COMPLETE",
                    base,
                    modulus,
                    period,
                    selected.measurement(),
                    selected.measuredPhase(),
                    factors
            );
        }

        private void validateInputs(
                BigInteger base,
                BigInteger modulus,
                int countingQubits
        ) {
            if (modulus.compareTo(BigInteger.ONE) <= 0) {
                throw new QuantumCircuitException(
                        "modulus must exceed one"
                );
            }

            if (base.compareTo(BigInteger.ONE) <= 0 ||
                    base.compareTo(modulus) >= 0) {
                throw new QuantumCircuitException(
                        "base must satisfy 1 < base < modulus"
                );
            }

            if (countingQubits <= 0 || countingQubits >= 31) {
                throw new QuantumCircuitException(
                        "counting qubits must be between 1 and 30"
                );
            }
        }

        private BigInteger modularOrder(
                BigInteger base,
                BigInteger modulus
        ) {
            if (!base.gcd(modulus).equals(BigInteger.ONE)) {
                throw new QuantumCircuitException(
                        "base is not invertible modulo modulus"
                );
            }

            BigInteger value = BigInteger.ONE;

            for (BigInteger r = BigInteger.ONE;
                 r.compareTo(modulus) <= 0;
                 r = r.add(BigInteger.ONE)) {

                value = value.multiply(base)
                        .mod(modulus);

                if (value.equals(BigInteger.ONE)) {
                    return r;
                }
            }

            return null;
        }

        private List<PhaseMeasurement> buildIdealPhaseMeasurements(
                BigInteger period,
                int countingQubits
        ) {
            long q = 1L << countingQubits;
            int periodAsInt = period.intValueExact();

            List<PhaseMeasurement> result =
                    new ArrayList<>();

            for (int s = 0; s < periodAsInt; s++) {
                double idealPhase =
                        (double) s / periodAsInt;

                long measurement = Math.round(
                        q * idealPhase
                ) % q;

                result.add(new PhaseMeasurement(
                        measurement,
                        (double) measurement / q,
                        idealPhase
                ));
            }

            return result;
        }

        private BigInteger approximatePeriod(
                PhaseMeasurement measurement,
                int countingQubits,
                long maximumDenominator
        ) {
            long q = 1L << countingQubits;
            double observed =
                    (double) measurement.measurement() / q;

            double bestError = Double.POSITIVE_INFINITY;
            long bestDenominator = 1;

            /*
             * This bounded rational search models the classical continued-
             * fraction reconstruction stage without requiring floating-point
             * continued-fraction libraries.
             */
            for (long denominator = 1;
                 denominator <= maximumDenominator;
                 denominator++) {

                long numerator = Math.round(
                        observed * denominator
                );

                if (numerator == 0) {
                    continue;
                }

                double candidate =
                        (double) numerator / denominator;

                double error =
                        Math.abs(observed - candidate);

                if (error < bestError) {
                    bestError = error;
                    bestDenominator = denominator;
                }
            }

            return BigInteger.valueOf(bestDenominator);
        }

        private Set<BigInteger> deriveFactors(
                BigInteger base,
                BigInteger modulus,
                BigInteger candidatePeriod
        ) {
            if (!candidatePeriod.testBit(0)) {
                BigInteger x = base.modPow(
                        candidatePeriod.divide(BigInteger.TWO),
                        modulus
                );

                if (!x.equals(BigInteger.ONE) &&
                        !x.equals(modulus.subtract(BigInteger.ONE))) {

                    BigInteger left =
                            x.subtract(BigInteger.ONE)
                                    .gcd(modulus);

                    BigInteger right =
                            x.add(BigInteger.ONE)
                                    .gcd(modulus);

                    Set<BigInteger> factors = new HashSet<>();

                    if (left.compareTo(BigInteger.ONE) > 0 &&
                            left.compareTo(modulus) < 0) {
                        factors.add(left);
                    }

                    if (right.compareTo(BigInteger.ONE) > 0 &&
                            right.compareTo(modulus) < 0) {
                        factors.add(right);
                    }

                    return Set.copyOf(factors);
                }
            }

            return Set.of();
        }
    }

    private static void demonstrateQft() {
        System.out.println("=== QFT ===");

        List<Complex> state = List.of(
                new Complex(0.5, 0.0),
                new Complex(0.5, 0.0),
                new Complex(0.0, 0.0),
                new Complex(0.0, 0.0)
        );

        List<Complex> transformed =
                qft(state);

        List<Complex> restored =
                inverseQft(transformed);

        for (int i = 0; i < transformed.size(); i++) {
            System.out.printf(
                    "|%2s> amplitude=(%.6f, %.6f) probability=%.6f%n",
                    Integer.toBinaryString(i)
                            .replace(" ", ""),
                    transformed.get(i).real(),
                    transformed.get(i).imaginary(),
                    transformed.get(i).magnitudeSquared()
            );
        }

        double error = 0.0;

        for (int i = 0; i < state.size(); i++) {
            error = Math.max(
                    error,
                    restored.get(i).distance(state.get(i))
            );
        }

        System.out.printf(
                "Inverse-QFT reconstruction error: %.3e%n",
                error
        );
    }

    private static List<Complex> qft(
            List<Complex> input
    ) {
        int n = input.size();

        if (n == 0 || (n & (n - 1)) != 0) {
            throw new QuantumCircuitException(
                    "state dimension must be a power of two"
            );
        }

        List<Complex> output = new ArrayList<>();
        double normalization = 1.0 / Math.sqrt(n);

        for (int k = 0; k < n; k++) {
            Complex total = new Complex(0, 0);

            for (int x = 0; x < n; x++) {
                double angle =
                        2.0 * Math.PI * k * x / n;

                Complex root = new Complex(
                        Math.cos(angle),
                        Math.sin(angle)
                );

                total = total.add(
                        input.get(x).multiply(root)
                );
            }

            output.add(total.scale(normalization));
        }

        return output;
    }

    private static List<Complex> inverseQft(
            List<Complex> input
    ) {
        int n = input.size();

        if (n == 0 || (n & (n - 1)) != 0) {
            throw new QuantumCircuitException(
                    "state dimension must be a power of two"
            );
        }

        List<Complex> output = new ArrayList<>();
        double normalization = 1.0 / Math.sqrt(n);

        for (int x = 0; x < n; x++) {
            Complex total = new Complex(0, 0);

            for (int k = 0; k < n; k++) {
                double angle =
                        -2.0 * Math.PI * x * k / n;

                Complex root = new Complex(
                        Math.cos(angle),
                        Math.sin(angle)
                );

                total = total.add(
                        input.get(k).multiply(root)
                );
            }

            output.add(total.scale(normalization));
        }

        return output;
    }

    private static void demonstrateCircuit() {
        System.out.println("\n=== QFT circuit ===");

        QuantumCircuit circuit =
                new QuantumCircuit(4);

        circuit.addQft(
                List.of(0, 1, 2, 3)
        );

        System.out.print(circuit.describe());
    }

    private static void demonstrateShor() {
        System.out.println(
                "\n=== Phase estimation and period finding ==="
        );

        ShorPeriodService service =
                new ShorPeriodService(
                        new NearestNonZeroPhasePolicy()
                );

        ShorResult result =
                service.execute(
                        BigInteger.valueOf(2),
                        BigInteger.valueOf(15),
                        8
                );

        System.out.println("status: " + result.status());
        System.out.println("base: " + result.base());
        System.out.println("modulus: " + result.modulus());
        System.out.println("period: " + result.period());
        System.out.println("measurement: " + result.measurement());
        System.out.println("phase: " + result.phase());
        System.out.println("factors: " + result.factors());

        if (!result.period().equals(BigInteger.valueOf(4)) ||
                !result.factors().equals(
                        Set.of(
                                BigInteger.valueOf(3),
                                BigInteger.valueOf(5)
                        )
                )) {
            throw new QuantumCircuitException(
                    "unexpected Shor-model result"
            );
        }
    }

    private static void demonstrateFailureModes() {
        System.out.println("\n=== Failure modes ===");

        try {
            new QuantumCircuit(0);
        } catch (QuantumCircuitException error) {
            System.out.println(
                    "Rejected invalid circuit: " +
                    error.getMessage()
            );
        }

        ShorPeriodService service =
                new ShorPeriodService(
                        new NearestNonZeroPhasePolicy()
                );

        ShorResult earlyFactor =
                service.execute(
                        BigInteger.valueOf(6),
                        BigInteger.valueOf(15),
                        8
                );

        System.out.println(
                "Early GCD factor: " +
                earlyFactor.factors()
        );
    }

    public static void main(String[] args) {
        try {
            demonstrateQft();
            demonstrateCircuit();
            demonstrateShor();
            demonstrateFailureModes();

            System.out.println("\n=== Complexity ===");
            System.out.println(
                    "Direct state-vector QFT: O(N^2)."
            );
            System.out.println(
                    "QFT circuit decomposition: O(q^2) gates."
            );
            System.out.println(
                    "BigInteger modular exponentiation uses repeated squaring."
            );
            System.out.println(
                    "Real Shor execution obtains the period from quantum "
                    + "phase estimation rather than classical enumeration."
            );
        } catch (RuntimeException error) {
            System.err.println(
                    "Execution failed: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
