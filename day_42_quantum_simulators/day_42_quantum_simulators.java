import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

/*
 * Enterprise-oriented quantum simulation service.
 *
 * The service distinguishes exact statevector results from shot-based
 * measurement records. Immutable records capture requests and results,
 * while policy validation prevents invalid simulation jobs.
 *
 * Compile and run:
 *   javac QuantumSimulationService.java
 *   java QuantumSimulationService
 *
 * Requires Java 17 or later.
 */
public final class QuantumSimulationService {

    private static final int MAX_QUBITS = 22;
    private static final double TOLERANCE = 1e-9;

    private QuantumSimulationService() {}

    public enum SimulationMode {
        STATEVECTOR,
        SHOT_BASED
    }

    public enum JobStatus {
        CREATED,
        VALIDATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    public static final class SimulationException extends RuntimeException {
        public SimulationException(String message) {
            super(message);
        }
    }

    public record Complex(double real, double imaginary) {
        public Complex {
            if (!Double.isFinite(real) || !Double.isFinite(imaginary)) {
                throw new SimulationException("Complex values must be finite.");
            }
        }

        public Complex add(Complex other) {
            return new Complex(real + other.real, imaginary + other.imaginary);
        }

        public Complex multiply(Complex other) {
            return new Complex(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        public Complex scale(double factor) {
            return new Complex(real * factor, imaginary * factor);
        }

        public Complex conjugate() {
            return new Complex(real, -imaginary);
        }

        public double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        @Override
        public String toString() {
            return String.format("%.6f%+.6fi", real, imaginary);
        }
    }

    public record Matrix2(
        Complex a00,
        Complex a01,
        Complex a10,
        Complex a11
    ) {
        public Matrix2 {
            Objects.requireNonNull(a00);
            Objects.requireNonNull(a01);
            Objects.requireNonNull(a10);
            Objects.requireNonNull(a11);

            Complex[] firstColumn = {a00, a10};
            Complex[] secondColumn = {a01, a11};

            for (int i = 0; i < 2; i++) {
                Complex inner = firstColumn[i].conjugate()
                    .multiply(secondColumn[i]);
                Complex other = firstColumn[1 - i].conjugate()
                    .multiply(secondColumn[1 - i]);

                Complex total = inner.add(other);
                double expected = i == 0 ? 1.0 : 0.0;

                // Column orthonormality is checked below with explicit
                // inner products to avoid accepting malformed gate matrices.
                if (!Double.isFinite(total.real())
                    || !Double.isFinite(total.imaginary())) {
                    throw new SimulationException("Invalid gate matrix.");
                }
            }

            Complex column00 = a00.conjugate().multiply(a00)
                .add(a10.conjugate().multiply(a10));
            Complex column11 = a01.conjugate().multiply(a01)
                .add(a11.conjugate().multiply(a11));
            Complex column01 = a00.conjugate().multiply(a01)
                .add(a10.conjugate().multiply(a11));

            if (Math.abs(column00.real() - 1.0) > TOLERANCE
                || Math.abs(column11.real() - 1.0) > TOLERANCE
                || Math.abs(column01.real()) > TOLERANCE
                || Math.abs(column01.imaginary()) > TOLERANCE
                || Math.abs(column00.imaginary()) > TOLERANCE
                || Math.abs(column11.imaginary()) > TOLERANCE) {
                throw new SimulationException("Gate matrix is not unitary.");
            }
        }

        public Complex[] apply(Complex first, Complex second) {
            return new Complex[] {
                a00.multiply(first).add(a01.multiply(second)),
                a10.multiply(first).add(a11.multiply(second))
            };
        }
    }

    public record Gate(
        String name,
        int target,
        Matrix2 matrix,
        Integer control
    ) {
        public Gate {
            if (name == null || name.isBlank()) {
                throw new SimulationException("Gate name is required.");
            }
            Objects.requireNonNull(matrix);
            if (control != null && control == target) {
                throw new SimulationException("Control and target must differ.");
            }
        }
    }

    public static final class Circuit {
        private final int qubits;
        private final List<Gate> gates = new ArrayList<>();
        private List<Integer> measuredQubits;

        public Circuit(int qubits) {
            if (qubits < 1 || qubits > MAX_QUBITS) {
                throw new SimulationException(
                    "Qubit count must be between 1 and " + MAX_QUBITS + "."
                );
            }
            this.qubits = qubits;
            this.measuredQubits = new ArrayList<>();
            for (int q = 0; q < qubits; q++) {
                measuredQubits.add(q);
            }
        }

        private void validateQubit(int qubit) {
            if (qubit < 0 || qubit >= qubits) {
                throw new SimulationException("Qubit index is out of range.");
            }
        }

        public Circuit addGate(Gate gate) {
            validateQubit(gate.target());
            if (gate.control() != null) {
                validateQubit(gate.control());
            }
            gates.add(gate);
            return this;
        }

        public Circuit h(int target) {
            double v = 1.0 / Math.sqrt(2.0);
            Matrix2 hadamard = new Matrix2(
                new Complex(v, 0), new Complex(v, 0),
                new Complex(v, 0), new Complex(-v, 0)
            );
            return addGate(new Gate("H", target, hadamard, null));
        }

        public Circuit x(int target) {
            Matrix2 x = new Matrix2(
                new Complex(0, 0), new Complex(1, 0),
                new Complex(1, 0), new Complex(0, 0)
            );
            return addGate(new Gate("X", target, x, null));
        }

        public Circuit phase(int target, double theta) {
            if (!Double.isFinite(theta)) {
                throw new SimulationException("Phase angle must be finite.");
            }
            Matrix2 phase = new Matrix2(
                new Complex(1, 0), new Complex(0, 0),
                new Complex(0, 0),
                new Complex(Math.cos(theta), Math.sin(theta))
            );
            return addGate(new Gate("P", target, phase, null));
        }

        public Circuit cx(int control, int target) {
            validateQubit(control);
            Matrix2 x = new Matrix2(
                new Complex(0, 0), new Complex(1, 0),
                new Complex(1, 0), new Complex(0, 0)
            );
            return addGate(new Gate("CX", target, x, control));
        }

        public Circuit measure(int... selected) {
            if (selected.length == 0) {
                throw new SimulationException("Select measurement qubits.");
            }
            List<Integer> values = new ArrayList<>();
            for (int qubit : selected) {
                validateQubit(qubit);
                if (values.contains(qubit)) {
                    throw new SimulationException(
                        "Measurement qubits must be unique."
                    );
                }
                values.add(qubit);
            }
            measuredQubits = List.copyOf(values);
            return this;
        }

        public int qubits() {
            return qubits;
        }

        public List<Gate> gates() {
            return Collections.unmodifiableList(gates);
        }

        public List<Integer> measuredQubits() {
            return measuredQubits;
        }
    }

    public record JobRequest(
        String jobId,
        SimulationMode mode,
        int shots,
        long seed
    ) {
        public JobRequest {
            if (jobId == null || jobId.isBlank()) {
                throw new SimulationException("Job identifier is required.");
            }
            Objects.requireNonNull(mode);
            if (mode == SimulationMode.STATEVECTOR && shots != 0) {
                throw new SimulationException(
                    "Statevector jobs must use shots=0."
                );
            }
            if (mode == SimulationMode.SHOT_BASED && (shots < 1 || shots > 10_000_000)) {
                throw new SimulationException(
                    "Shot-based jobs require between 1 and 10,000,000 shots."
                );
            }
        }
    }

    public record JobResult(
        String jobId,
        JobStatus status,
        SimulationMode mode,
        Map<String, Double> probabilities,
        Map<String, Integer> counts,
        int shots
    ) {}

    public static final class Simulator {
        private static final Matrix2 X = new Matrix2(
            new Complex(0, 0), new Complex(1, 0),
            new Complex(1, 0), new Complex(0, 0)
        );

        public Complex[] statevector(Circuit circuit) {
            Complex[] state = new Complex[1 << circuit.qubits()];
            for (int i = 0; i < state.length; i++) {
                state[i] = new Complex(0, 0);
            }
            state[0] = new Complex(1, 0);

            for (Gate gate : circuit.gates()) {
                state = applyGate(state, circuit.qubits(), gate);
            }

            double norm = 0;
            for (Complex amplitude : state) {
                norm += amplitude.magnitudeSquared();
            }
            if (Math.abs(norm - 1.0) > 1e-8) {
                throw new SimulationException("State normalization failed.");
            }
            return state;
        }

        private Complex[] applyGate(
            Complex[] state,
            int qubits,
            Gate gate
        ) {
            int targetMask = 1 << gate.target();
            int controlMask = gate.control() == null
                ? 0
                : 1 << gate.control();

            Complex[] result = state.clone();

            for (int index = 0; index < state.length; index++) {
                if ((index & targetMask) != 0) {
                    continue;
                }

                int partner = index | targetMask;
                if (controlMask != 0 && (index & controlMask) == 0) {
                    continue;
                }

                Complex[] updated = gate.matrix().apply(
                    state[index], state[partner]
                );
                result[index] = updated[0];
                result[partner] = updated[1];
            }
            return result;
        }

        public Map<String, Double> exactProbabilities(
            Circuit circuit,
            Complex[] state
        ) {
            if (state.length != (1 << circuit.qubits())) {
                throw new SimulationException("State dimension mismatch.");
            }

            Map<String, Double> result = new LinkedHashMap<>();
            int outcomeCount = 1 << circuit.measuredQubits().size();

            for (int outcome = 0; outcome < outcomeCount; outcome++) {
                result.put(bitString(outcome, circuit.measuredQubits().size()), 0.0);
            }

            for (int basis = 0; basis < state.length; basis++) {
                int outcome = 0;
                for (int bit = 0; bit < circuit.measuredQubits().size(); bit++) {
                    int qubit = circuit.measuredQubits().get(bit);
                    if ((basis & (1 << qubit)) != 0) {
                        outcome |= 1 << bit;
                    }
                }

                String key = bitString(
                    outcome, circuit.measuredQubits().size()
                );
                result.merge(
                    key, state[basis].magnitudeSquared(), Double::sum
                );
            }

            return Collections.unmodifiableMap(result);
        }

        public Map<String, Integer> runShots(
            Map<String, Double> probabilities,
            int shots,
            long seed
        ) {
            if (shots < 1) {
                throw new SimulationException("Shots must be positive.");
            }

            List<String> outcomes = new ArrayList<>(probabilities.keySet());
            double[] cumulative = new double[outcomes.size()];
            double running = 0.0;

            for (int i = 0; i < outcomes.size(); i++) {
                running += probabilities.get(outcomes.get(i));
                cumulative[i] = running;
            }
            cumulative[cumulative.length - 1] = 1.0;

            Random random = new Random(seed);
            Map<String, Integer> counts = new LinkedHashMap<>();

            for (String outcome : outcomes) {
                counts.put(outcome, 0);
            }

            for (int shot = 0; shot < shots; shot++) {
                double draw = random.nextDouble();
                int selected = 0;
                while (
                    selected < cumulative.length - 1 &&
                    draw >= cumulative[selected]
                ) {
                    selected++;
                }
                String outcome = outcomes.get(selected);
                counts.merge(outcome, 1, Integer::sum);
            }

            return Collections.unmodifiableMap(counts);
        }

        private String bitString(int value, int width) {
            String raw = Integer.toBinaryString(value);
            return "0".repeat(Math.max(0, width - raw.length())) + raw;
        }
    }

    public static final class SimulationService {
        private final Simulator simulator = new Simulator();

        public JobResult execute(Circuit circuit, JobRequest request) {
            JobStatus status = JobStatus.CREATED;

            try {
                Objects.requireNonNull(circuit);
                Objects.requireNonNull(request);
                status = JobStatus.VALIDATED;
                status = JobStatus.RUNNING;

                Complex[] state = simulator.statevector(circuit);
                Map<String, Double> exact =
                    simulator.exactProbabilities(circuit, state);

                if (request.mode() == SimulationMode.STATEVECTOR) {
                    return new JobResult(
                        request.jobId(),
                        JobStatus.COMPLETED,
                        request.mode(),
                        exact,
                        Map.of(),
                        0
                    );
                }

                Map<String, Integer> counts = simulator.runShots(
                    exact, request.shots(), request.seed()
                );

                return new JobResult(
                    request.jobId(),
                    JobStatus.COMPLETED,
                    request.mode(),
                    exact,
                    counts,
                    request.shots()
                );
            } catch (RuntimeException error) {
                // Production services would persist this failure with a
                // correlation ID and sanitized diagnostic information.
                return new JobResult(
                    request == null ? "unknown" : request.jobId(),
                    JobStatus.FAILED,
                    request == null ? SimulationMode.STATEVECTOR : request.mode(),
                    Map.of(),
                    Map.of(),
                    0
                );
            }
        }
    }

    private static String bitString(int value, int width) {
        String raw = Integer.toBinaryString(value);
        return "0".repeat(Math.max(0, width - raw.length())) + raw;
    }

    public static void main(String[] args) {
        Circuit bell = new Circuit(2).h(0).cx(0, 1).measure(0, 1);
        SimulationService service = new SimulationService();

        JobRequest exactRequest = new JobRequest(
            "bell-exact", SimulationMode.STATEVECTOR, 0, 17L
        );
        JobRequest shotRequest = new JobRequest(
            "bell-shots", SimulationMode.SHOT_BASED, 5000, 17L
        );

        JobResult exact = service.execute(bell, exactRequest);
        JobResult sampled = service.execute(bell, shotRequest);

        System.out.println("Exact statevector-derived probabilities:");
        exact.probabilities().forEach((key, value) ->
            System.out.printf("  %s: %.6f%n", key, value)
        );

        System.out.println("\nShot-based result:");
        sampled.counts().forEach((key, value) ->
            System.out.printf("  %s: %d%n", key, value)
        );

        System.out.println("\nJob states:");
        System.out.println(exact.jobId() + ": " + exact.status());
        System.out.println(sampled.jobId() + ": " + sampled.status());

        Circuit interference = new Circuit(1)
            .h(0)
            .phase(0, Math.PI)
            .h(0)
            .measure(0);

        JobResult phaseResult = service.execute(
            interference,
            new JobRequest("phase-test", SimulationMode.STATEVECTOR, 0, 0L)
        );

        System.out.println("\nPhase-interference probabilities:");
        phaseResult.probabilities().forEach((key, value) ->
            System.out.printf("  %s: %.6f%n", key, value)
        );
    }
}
