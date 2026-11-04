import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

/**
 * Photonic Quantum Computing: Photons as Qubits
 *
 * Java 17 enterprise-oriented simulation.
 *
 * Models:
 * - Photon polarization states
 * - Complex amplitudes
 * - Unitary optical transformations
 * - Optical circuit execution
 * - Measurement
 * - Photon transmission and detection
 * - Loss accounting
 * - Beam splitters
 * - Hong-Ou-Mandel interference
 * - Experiment reporting
 *
 * Compile: javac PhotonicQuantumComputing.java
 * Run: java PhotonicQuantumComputing
 */

public class PhotonicQuantumComputing {

    private static final double EPSILON = 1e-9;

    public enum Polarization {
        HORIZONTAL,
        VERTICAL
    }

    public enum GateType {
        PAULI_X,
        PAULI_Z,
        HADAMARD,
        PHASE_SHIFT
    }

    public enum PhotonStatus {
        GENERATED,
        TRANSMITTED,
        LOST,
        DETECTED
    }

    public static class QuantumException
            extends RuntimeException {

        public QuantumException(String message) {
            super(message);
        }
    }

    public static class ValidationException
            extends QuantumException {

        public ValidationException(String message) {
            super(message);
        }
    }

    public record Complex(double real, double imaginary) {

        public Complex {
            if (!Double.isFinite(real)
                    || !Double.isFinite(imaginary)) {
                throw new ValidationException(
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
                    real * other.real
                            - imaginary * other.imaginary,
                    real * other.imaginary
                            + imaginary * other.real
            );
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

        public Complex conjugate() {
            return new Complex(real, -imaginary);
        }

        public static Complex expi(double angle) {
            return new Complex(
                    Math.cos(angle),
                    Math.sin(angle)
            );
        }
    }

    public record PhotonState(
            Complex alpha,
            Complex beta
    ) {
        public PhotonState {
            Objects.requireNonNull(alpha);
            Objects.requireNonNull(beta);

            double norm =
                    alpha.magnitudeSquared()
                            + beta.magnitudeSquared();

            if (Math.abs(norm - 1.0) > EPSILON) {
                throw new ValidationException(
                        "Photon state must be normalized."
                );
            }
        }

        public static PhotonState horizontal() {
            return new PhotonState(
                    new Complex(1, 0),
                    new Complex(0, 0)
            );
        }

        public static PhotonState vertical() {
            return new PhotonState(
                    new Complex(0, 0),
                    new Complex(1, 0)
            );
        }

        public static PhotonState diagonal() {
            double s = 1 / Math.sqrt(2);

            return new PhotonState(
                    new Complex(s, 0),
                    new Complex(s, 0)
            );
        }

        public static PhotonState circular() {
            double s = 1 / Math.sqrt(2);

            return new PhotonState(
                    new Complex(s, 0),
                    new Complex(0, s)
            );
        }

        public double probabilityH() {
            return alpha.magnitudeSquared();
        }

        public double probabilityV() {
            return beta.magnitudeSquared();
        }

        public double[] blochVector() {
            Complex product =
                    alpha.conjugate().multiply(beta);

            return new double[]{
                    2 * product.real(),
                    2 * product.imaginary(),
                    probabilityH() - probabilityV()
            };
        }
    }

    public record MeasurementResult(
            Polarization outcome,
            double probability
    ) {}

    public interface PhotonSource {
        PhotonState emit();
    }

    public static class PolarizedPhotonSource
            implements PhotonSource {

        private final PhotonState configuredState;

        public PolarizedPhotonSource(PhotonState state) {
            this.configuredState =
                    Objects.requireNonNull(state);
        }

        @Override
        public PhotonState emit() {
            return configuredState;
        }
    }

    public static class QuantumGate {

        private final Complex[][] matrix;
        private final String name;

        public QuantumGate(
                String name,
                Complex[][] matrix
        ) {
            this.name = Objects.requireNonNull(name);

            if (matrix == null
                    || matrix.length != 2
                    || matrix[0].length != 2
                    || matrix[1].length != 2) {
                throw new ValidationException(
                        "Gate must have a 2x2 matrix."
                );
            }

            this.matrix = new Complex[][]{
                    matrix[0].clone(),
                    matrix[1].clone()
            };

            for (Complex[] row : this.matrix) {
                for (Complex element : row) {
                    Objects.requireNonNull(element);
                }
            }

            validateUnitary();
        }

        private void validateUnitary() {
            // A†A must equal the identity matrix.
            for (int i = 0; i < 2; i++) {
                for (int j = 0; j < 2; j++) {
                    Complex sum = new Complex(0, 0);

                    for (int k = 0; k < 2; k++) {
                        sum = sum.add(
                                matrix[k][i]
                                        .conjugate()
                                        .multiply(matrix[k][j])
                        );
                    }

                    double expected = i == j ? 1 : 0;

                    if (Math.abs(sum.real() - expected) > EPSILON
                            || Math.abs(sum.imaginary()) > EPSILON) {
                        throw new ValidationException(
                                "Gate matrix is not unitary: " + name
                        );
                    }
                }
            }
        }

        public PhotonState apply(PhotonState state) {
            Complex alpha =
                    matrix[0][0].multiply(state.alpha())
                            .add(
                                    matrix[0][1].multiply(state.beta())
                            );

            Complex beta =
                    matrix[1][0].multiply(state.alpha())
                            .add(
                                    matrix[1][1].multiply(state.beta())
                            );

            return new PhotonState(alpha, beta);
        }

        public String name() {
            return name;
        }

        public static QuantumGate create(GateType type) {
            double s = 1 / Math.sqrt(2);

            return switch (type) {
                case PAULI_X -> new QuantumGate(
                        "Pauli-X",
                        new Complex[][]{
                                {
                                        new Complex(0, 0),
                                        new Complex(1, 0)
                                },
                                {
                                        new Complex(1, 0),
                                        new Complex(0, 0)
                                }
                        }
                );

                case PAULI_Z -> new QuantumGate(
                        "Pauli-Z",
                        new Complex[][]{
                                {
                                        new Complex(1, 0),
                                        new Complex(0, 0)
                                },
                                {
                                        new Complex(0, 0),
                                        new Complex(-1, 0)
                                }
                        }
                );

                case HADAMARD -> new QuantumGate(
                        "Hadamard",
                        new Complex[][]{
                                {
                                        new Complex(s, 0),
                                        new Complex(s, 0)
                                },
                                {
                                        new Complex(s, 0),
                                        new Complex(-s, 0)
                                }
                        }
                );

                case PHASE_SHIFT -> phaseGate(Math.PI / 2);
            };
        }

        public static QuantumGate phaseGate(double angle) {
            if (!Double.isFinite(angle)) {
                throw new ValidationException("Invalid phase.");
            }

            return new QuantumGate(
                    "Phase Shift",
                    new Complex[][]{
                            {
                                    new Complex(1, 0),
                                    new Complex(0, 0)
                            },
                            {
                                    new Complex(0, 0),
                                    Complex.expi(angle)
                            }
                    }
            );
        }
    }

    public static class OpticalCircuit {

        private final List<QuantumGate> gates =
                new ArrayList<>();

        public OpticalCircuit add(QuantumGate gate) {
            gates.add(Objects.requireNonNull(gate));
            return this;
        }

        public PhotonState execute(PhotonState input) {
            PhotonState state = input;

            for (QuantumGate gate : gates) {
                state = gate.apply(state);
            }

            return state;
        }

        public List<String> gateSequence() {
            return gates.stream()
                    .map(QuantumGate::name)
                    .toList();
        }
    }

    public static class PhotonMeasurement {

        private final Random random;

        public PhotonMeasurement(long seed) {
            random = new Random(seed);
        }

        public MeasurementResult measure(PhotonState state) {
            double pH = state.probabilityH();

            if (random.nextDouble() < pH) {
                return new MeasurementResult(
                        Polarization.HORIZONTAL,
                        pH
                );
            }

            return new MeasurementResult(
                    Polarization.VERTICAL,
                    1 - pH
            );
        }

        public Map<Polarization, Long> sample(
                PhotonState state,
                int shots
        ) {
            if (shots <= 0) {
                throw new ValidationException(
                        "Shots must be positive."
                );
            }

            Map<Polarization, Long> counts =
                    new EnumMap<>(Polarization.class);

            counts.put(Polarization.HORIZONTAL, 0L);
            counts.put(Polarization.VERTICAL, 0L);

            for (int i = 0; i < shots; i++) {
                Polarization result =
                        measure(state).outcome();

                counts.put(
                        result,
                        counts.get(result) + 1
                );
            }

            return Collections.unmodifiableMap(counts);
        }
    }

    public record OpticalChannel(
            double transmission,
            double detectorEfficiency
    ) {
        public OpticalChannel {
            if (!valid(transmission)
                    || !valid(detectorEfficiency)) {
                throw new ValidationException(
                        "Channel efficiencies must be in [0,1]."
                );
            }
        }

        private static boolean valid(double value) {
            return Double.isFinite(value)
                    && value >= 0
                    && value <= 1;
        }

        public double detectionProbability() {
            return transmission * detectorEfficiency;
        }
    }

    public record BeamSplitterOutput(
            Complex reflected,
            Complex transmitted
    ) {
        public double reflectionProbability() {
            return reflected.magnitudeSquared();
        }

        public double transmissionProbability() {
            return transmitted.magnitudeSquared();
        }
    }

    public static class BeamSplitter {

        public static BeamSplitterOutput split(
                double reflectivity
        ) {
            if (!Double.isFinite(reflectivity)
                    || reflectivity < 0
                    || reflectivity > 1) {
                throw new ValidationException(
                        "Reflectivity must be in [0,1]."
                );
            }

            return new BeamSplitterOutput(
                    new Complex(0, Math.sqrt(reflectivity)),
                    new Complex(Math.sqrt(1 - reflectivity), 0)
            );
        }
    }

    public record InterferenceResult(
            double coincidenceProbability,
            double bunchingProbability
    ) {}

    public static class HongOuMandelExperiment {

        public static InterferenceResult evaluate(
                double overlap,
                double reflectivity
        ) {
            if (!Double.isFinite(overlap)
                    || overlap < 0
                    || overlap > 1
                    || !Double.isFinite(reflectivity)
                    || reflectivity < 0
                    || reflectivity > 1) {
                throw new ValidationException(
                        "Invalid interference parameters."
                );
            }

            double coincidence =
                    4 * reflectivity
                            * (1 - reflectivity)
                            * (1 - overlap);

            return new InterferenceResult(
                    coincidence,
                    1 - coincidence
            );
        }
    }

    public static class ExperimentReport {

        private final int shots;
        private final int detected;
        private final int lost;
        private final Map<Polarization, Integer> counts;

        public ExperimentReport(
                int shots,
                int detected,
                int lost,
                Map<Polarization, Integer> counts
        ) {
            this.shots = shots;
            this.detected = detected;
            this.lost = lost;
            this.counts = Map.copyOf(counts);

            if (detected + lost != shots) {
                throw new ValidationException(
                        "Photon accounting is inconsistent."
                );
            }

            int measured = counts.values()
                    .stream()
                    .mapToInt(Integer::intValue)
                    .sum();

            if (measured != detected) {
                throw new ValidationException(
                        "Measurement accounting is inconsistent."
                );
            }
        }

        public double detectionRate() {
            return (double) detected / shots;
        }

        public double horizontalFraction() {
            return detected == 0
                    ? 0
                    : (double) counts.get(
                            Polarization.HORIZONTAL
                    ) / detected;
        }

        public void display() {
            System.out.println("Shots: " + shots);
            System.out.println("Detected: " + detected);
            System.out.println("Lost: " + lost);
            System.out.println("Counts: " + counts);
            System.out.printf(
                    "Detection rate: %.4f%n",
                    detectionRate()
            );
            System.out.printf(
                    "Horizontal fraction: %.4f%n",
                    horizontalFraction()
            );
        }
    }

    public static class ExperimentService {

        private final PhotonSource source;
        private final OpticalChannel channel;
        private final PhotonMeasurement measurement;
        private final Random random;

        public ExperimentService(
                PhotonSource source,
                OpticalChannel channel,
                long seed
        ) {
            this.source = Objects.requireNonNull(source);
            this.channel = Objects.requireNonNull(channel);
            this.measurement = new PhotonMeasurement(seed + 1);
            this.random = new Random(seed);
        }

        public ExperimentReport run(int shots) {
            if (shots <= 0) {
                throw new ValidationException(
                        "Experiment must contain at least one shot."
                );
            }

            int detected = 0;
            int lost = 0;

            Map<Polarization, Integer> counts =
                    new EnumMap<>(Polarization.class);

            counts.put(Polarization.HORIZONTAL, 0);
            counts.put(Polarization.VERTICAL, 0);

            for (int i = 0; i < shots; i++) {
                PhotonState photon = source.emit();

                boolean successful =
                        random.nextDouble()
                                < channel.detectionProbability();

                if (!successful) {
                    lost++;
                    continue;
                }

                detected++;

                Polarization result =
                        measurement.measure(photon).outcome();

                counts.put(
                        result,
                        counts.get(result) + 1
                );
            }

            return new ExperimentReport(
                    shots,
                    detected,
                    lost,
                    counts
            );
        }
    }

    private static void validate() {
        PhotonState horizontal = PhotonState.horizontal();

        PhotonState flipped = QuantumGate.create(
                GateType.PAULI_X
        ).apply(horizontal);

        if (Math.abs(flipped.probabilityV() - 1) > EPSILON) {
            throw new AssertionError("Pauli-X failed.");
        }

        PhotonState superposition = QuantumGate.create(
                GateType.HADAMARD
        ).apply(horizontal);

        if (Math.abs(superposition.probabilityH() - 0.5)
                > EPSILON) {
            throw new AssertionError("Hadamard failed.");
        }

        BeamSplitterOutput split =
                BeamSplitter.split(0.5);

        if (Math.abs(
                split.reflectionProbability()
                        + split.transmissionProbability()
                        - 1
        ) > EPSILON) {
            throw new AssertionError("Beam splitter failed.");
        }

        InterferenceResult result =
                HongOuMandelExperiment.evaluate(1, 0.5);

        if (Math.abs(result.coincidenceProbability()) > EPSILON) {
            throw new AssertionError("Interference failed.");
        }

        boolean rejected = false;

        try {
            new PhotonState(
                    new Complex(2, 0),
                    new Complex(0, 0)
            );
        } catch (ValidationException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError(
                    "Invalid state was accepted."
            );
        }

        System.out.println("All Java 17 validation checks passed.");
    }

    public static void main(String[] args) {
        try {
            validate();

            System.out.println(
                    "\nPHOTONIC QUANTUM COMPUTING"
            );

            PhotonSource source =
                    new PolarizedPhotonSource(
                            PhotonState.diagonal()
                    );

            OpticalCircuit circuit = new OpticalCircuit()
                    .add(QuantumGate.create(GateType.PAULI_Z))
                    .add(QuantumGate.phaseGate(Math.PI / 2));

            PhotonState output =
                    circuit.execute(source.emit());

            System.out.println(
                    "\nOptical circuit: "
                            + circuit.gateSequence()
            );

            System.out.printf(
                    "P(H): %.4f%nP(V): %.4f%n",
                    output.probabilityH(),
                    output.probabilityV()
            );

            System.out.println("\nHong-Ou-Mandel interference:");

            for (double overlap : new double[]{0, 0.5, 1}) {
                InterferenceResult result =
                        HongOuMandelExperiment.evaluate(
                                overlap,
                                0.5
                        );

                System.out.printf(
                        "Overlap %.1f: coincidence %.4f%n",
                        overlap,
                        result.coincidenceProbability()
                );
            }

            OpticalChannel channel =
                    new OpticalChannel(0.85, 0.90);

            ExperimentService service =
                    new ExperimentService(
                            source,
                            channel,
                            2026
                    );

            System.out.println("\nEnterprise experiment report:");
            service.run(10000).display();

        } catch (QuantumException exception) {
            System.err.println(
                    "Quantum experiment error: "
                            + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
