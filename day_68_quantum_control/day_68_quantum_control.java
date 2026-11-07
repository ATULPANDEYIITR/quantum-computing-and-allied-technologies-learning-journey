import java.util.*;
import java.util.stream.Collectors;

/**
 * Quantum Control Enterprise Laboratory.
 *
 * Models:
 * - Qubit configuration and hardware capabilities
 * - Microwave pulse definitions
 * - Bloch-sphere state transitions
 * - Rabi calibration
 * - Ramsey detuning measurements
 * - Calibration approval and versioning
 * - Pulse scheduling
 * - Safety-policy enforcement
 *
 * Requires Java 17.
 */
public class QuantumControl {

    private static final double PI = Math.PI;
    private static final double EPSILON = 1e-12;

    enum PulseType {
        X, Y, ARBITRARY
    }

    enum CalibrationStatus {
        PENDING, PASSED, FAILED, REVOKED
    }

    enum CalibrationStage {
        CREATED, MEASURED, VALIDATED, APPROVED, REJECTED
    }

    static class ControlException extends RuntimeException {
        ControlException(String message) {
            super(message);
        }
    }

    static class ValidationException extends ControlException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class SafetyException extends ControlException {
        SafetyException(String message) {
            super(message);
        }
    }

    record HardwareLimits(
        double maxAmplitude,
        double minDurationUs,
        double maxDurationUs,
        double maxDetuningMhz,
        int maxPulses
    ) {
        HardwareLimits {
            if (
                !Double.isFinite(maxAmplitude) ||
                !Double.isFinite(minDurationUs) ||
                !Double.isFinite(maxDurationUs) ||
                !Double.isFinite(maxDetuningMhz) ||
                maxAmplitude <= 0 ||
                minDurationUs <= 0 ||
                maxDurationUs < minDurationUs ||
                maxDetuningMhz < 0 ||
                maxPulses < 1
            ) {
                throw new ValidationException("Invalid hardware limits.");
            }
        }
    }

    record Qubit(
        String id,
        double frequencyGhz,
        double t1Us,
        double t2Us
    ) {
        Qubit {
            if (
                id == null || id.isBlank() ||
                !Double.isFinite(frequencyGhz) ||
                !Double.isFinite(t1Us) ||
                !Double.isFinite(t2Us) ||
                frequencyGhz <= 0 ||
                t1Us <= 0 ||
                t2Us <= 0 ||
                t2Us > 2 * t1Us
            ) {
                throw new ValidationException("Invalid qubit configuration.");
            }
        }
    }

    record Pulse(
        String id,
        PulseType type,
        double amplitude,
        double durationUs,
        double phaseRad,
        double detuningMhz,
        double startUs
    ) {
        Pulse {
            if (
                id == null || id.isBlank() ||
                type == null ||
                !Double.isFinite(amplitude) ||
                !Double.isFinite(durationUs) ||
                !Double.isFinite(phaseRad) ||
                !Double.isFinite(detuningMhz) ||
                !Double.isFinite(startUs) ||
                amplitude < 0 ||
                durationUs <= 0 ||
                startUs < 0
            ) {
                throw new ValidationException("Invalid pulse definition.");
            }
        }

        double endUs() {
            return startUs + durationUs;
        }
    }

    record BlochSnapshot(
        double x,
        double y,
        double z,
        double excitedProbability
    ) {}

    static final class BlochState {
        private double x = 0;
        private double y = 0;
        private double z = 1;

        double excitedProbability() {
            return Math.max(0, Math.min(1, (1 - z) / 2));
        }

        void rotate(
            double ax,
            double ay,
            double az,
            double angle
        ) {
            double magnitude = Math.sqrt(
                ax * ax + ay * ay + az * az
            );

            if (magnitude < EPSILON) return;

            double ux = ax / magnitude;
            double uy = ay / magnitude;
            double uz = az / magnitude;

            double c = Math.cos(angle);
            double s = Math.sin(angle);

            double dot = ux * x + uy * y + uz * z;

            double cx = uy * z - uz * y;
            double cy = uz * x - ux * z;
            double cz = ux * y - uy * x;

            double oldX = x;
            double oldY = y;
            double oldZ = z;

            x = oldX * c + cx * s + ux * dot * (1 - c);
            y = oldY * c + cy * s + uy * dot * (1 - c);
            z = oldZ * c + cz * s + uz * dot * (1 - c);
        }

        BlochSnapshot snapshot() {
            return new BlochSnapshot(
                x, y, z, excitedProbability()
            );
        }
    }

    interface PulseValidator {
        void validate(Pulse pulse);
    }

    static final class HardwareSafetyPolicy implements PulseValidator {
        private final HardwareLimits limits;

        HardwareSafetyPolicy(HardwareLimits limits) {
            this.limits = Objects.requireNonNull(limits);
        }

        @Override
        public void validate(Pulse pulse) {
            if (pulse.amplitude() > limits.maxAmplitude()) {
                throw new SafetyException("Amplitude limit exceeded.");
            }

            if (
                pulse.durationUs() < limits.minDurationUs() ||
                pulse.durationUs() > limits.maxDurationUs()
            ) {
                throw new SafetyException("Duration limit exceeded.");
            }

            if (
                Math.abs(pulse.detuningMhz()) >
                limits.maxDetuningMhz()
            ) {
                throw new SafetyException("Detuning limit exceeded.");
            }
        }
    }

    static final class QuantumController {
        private final PulseValidator validator;
        private final int maximumPulses;
        private int executionCount = 0;

        QuantumController(
            PulseValidator validator,
            int maximumPulses
        ) {
            this.validator = Objects.requireNonNull(validator);
            this.maximumPulses = maximumPulses;

            if (maximumPulses < 1) {
                throw new ValidationException("Invalid pulse quota.");
            }
        }

        BlochState execute(Pulse pulse, BlochState state) {
            validator.validate(pulse);

            if (executionCount >= maximumPulses) {
                throw new SafetyException("Pulse quota exceeded.");
            }

            double ax = pulse.amplitude() *
                Math.cos(pulse.phaseRad());

            double ay = pulse.amplitude() *
                Math.sin(pulse.phaseRad());

            double az = 2 * PI * pulse.detuningMhz() / 1000.0;

            double frequency = Math.sqrt(
                ax * ax + ay * ay + az * az
            );

            double angle = frequency * pulse.durationUs();

            state.rotate(ax, ay, az, angle);
            executionCount++;

            return state;
        }

        int getExecutionCount() {
            return executionCount;
        }
    }

    static final class PulseSchedule {
        private final List<Pulse> pulses = new ArrayList<>();
        private final PulseValidator validator;
        private final int maximumSize;

        PulseSchedule(
            PulseValidator validator,
            int maximumSize
        ) {
            this.validator = validator;
            this.maximumSize = maximumSize;
        }

        void add(Pulse pulse) {
            validator.validate(pulse);

            if (pulses.size() >= maximumSize) {
                throw new SafetyException("Schedule capacity exceeded.");
            }

            for (Pulse existing : pulses) {
                if (
                    pulse.startUs() < existing.endUs() &&
                    existing.startUs() < pulse.endUs()
                ) {
                    throw new ValidationException("Pulse overlap detected.");
                }
            }

            pulses.add(pulse);
            pulses.sort(
                Comparator.comparingDouble(Pulse::startUs)
            );
        }

        BlochState execute(QuantumController controller) {
            BlochState state = new BlochState();

            for (Pulse pulse : pulses) {
                controller.execute(pulse, state);
            }

            return state;
        }

        List<Pulse> getPulses() {
            return List.copyOf(pulses);
        }
    }

    record CalibrationRecord(
        String id,
        String qubitId,
        int version,
        double piAmplitude,
        double piOverTwoAmplitude,
        double excitationError,
        CalibrationStatus status,
        String timestamp
    ) {}

    static final class CalibrationPolicy {
        private final double minimumFidelity;

        CalibrationPolicy(double minimumFidelity) {
            if (
                minimumFidelity <= 0 ||
                minimumFidelity > 1
            ) {
                throw new ValidationException("Invalid fidelity threshold.");
            }

            this.minimumFidelity = minimumFidelity;
        }

        CalibrationStatus evaluate(double probability) {
            return probability >= minimumFidelity
                ? CalibrationStatus.PASSED
                : CalibrationStatus.FAILED;
        }
    }

    static final class CalibrationService {
        private final QuantumController controller;
        private final CalibrationPolicy policy;

        private final Map<String, List<CalibrationRecord>> history =
            new HashMap<>();

        CalibrationService(
            QuantumController controller,
            CalibrationPolicy policy
        ) {
            this.controller = controller;
            this.policy = policy;
        }

        private double measureRabi(
            double amplitude,
            double durationUs
        ) {
            Pulse pulse = new Pulse(
                UUID.randomUUID().toString(),
                PulseType.X,
                amplitude,
                durationUs,
                0,
                0,
                0
            );

            BlochState state = controller.execute(
                pulse,
                new BlochState()
            );

            return state.excitedProbability();
        }

        CalibrationRecord calibrate(
            Qubit qubit,
            double durationUs,
            double maximumAmplitude,
            int samples
        ) {
            if (
                samples < 3 ||
                samples > 10001 ||
                durationUs <= 0 ||
                maximumAmplitude <= 0
            ) {
                throw new ValidationException("Invalid calibration input.");
            }

            double bestAmplitude = 0;
            double bestProbability = -1;

            for (int i = 1; i < samples; i++) {
                double amplitude =
                    maximumAmplitude * i / (samples - 1);

                double probability = measureRabi(
                    amplitude,
                    durationUs
                );

                if (probability > bestProbability) {
                    bestProbability = probability;
                    bestAmplitude = amplitude;
                }
            }

            List<CalibrationRecord> existing =
                history.getOrDefault(qubit.id(), List.of());

            int version = existing.size() + 1;

            CalibrationRecord record = new CalibrationRecord(
                UUID.randomUUID().toString(),
                qubit.id(),
                version,
                bestAmplitude,
                bestAmplitude / 2,
                1 - bestProbability,
                policy.evaluate(bestProbability),
                java.time.Instant.now().toString()
            );

            history.computeIfAbsent(
                qubit.id(),
                key -> new ArrayList<>()
            ).add(record);

            return record;
        }

        List<CalibrationRecord> history(String qubitId) {
            return List.copyOf(
                history.getOrDefault(qubitId, List.of())
            );
        }

        Optional<CalibrationRecord> latestApproved(String qubitId) {
            return history(qubitId).stream()
                .filter(r -> r.status() == CalibrationStatus.PASSED)
                .max(Comparator.comparingInt(CalibrationRecord::version));
        }

        static double estimateRamseyDetuning(
            List<Double> probabilities,
            List<Double> delaysUs
        ) {
            if (
                probabilities.size() != delaysUs.size() ||
                probabilities.size() < 3
            ) {
                throw new ValidationException("Insufficient Ramsey samples.");
            }

            for (int i = 0; i < probabilities.size(); i++) {
                double p = probabilities.get(i);
                double t = delaysUs.get(i);

                if (
                    !Double.isFinite(p) ||
                    p < 0 || p > 1 ||
                    !Double.isFinite(t) ||
                    t < 0
                ) {
                    throw new ValidationException("Invalid Ramsey data.");
                }

                if (i > 0 && t <= delaysUs.get(i - 1)) {
                    throw new ValidationException("Delays must increase.");
                }
            }

            double mean = probabilities.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElseThrow();

            List<Double> centered = probabilities.stream()
                .map(p -> p - mean)
                .collect(Collectors.toList());

            double phaseSum = 0;
            double intervalSum = 0;

            for (int i = 0; i < centered.size() - 1; i++) {
                phaseSum += Math.atan2(
                    centered.get(i + 1),
                    centered.get(i)
                );

                intervalSum += delaysUs.get(i + 1) - delaysUs.get(i);
            }

            double meanPhase = phaseSum / (centered.size() - 1);
            double meanInterval = intervalSum / (centered.size() - 1);

            return meanPhase / (2 * PI * meanInterval) * 1000;
        }
    }

    private static void runTests(HardwareSafetyPolicy policy) {
        QuantumController controller = new QuantumController(
            policy, 100
        );

        BlochState state = controller.execute(
            new Pulse("PI", PulseType.X, PI, 1, 0, 0, 0),
            new BlochState()
        );

        if (Math.abs(state.excitedProbability() - 1) > 1e-9) {
            throw new ControlException("Pi-pulse test failed.");
        }

        state = controller.execute(
            new Pulse("HALF", PulseType.X, PI / 2, 1, 0, 0, 0),
            new BlochState()
        );

        if (Math.abs(state.excitedProbability() - 0.5) > 1e-9) {
            throw new ControlException("Pi/2-pulse test failed.");
        }

        try {
            policy.validate(
                new Pulse("UNSAFE", PulseType.X, 100, 1, 0, 0, 0)
            );

            throw new ControlException("Unsafe pulse accepted.");
        } catch (SafetyException expected) {
            // Expected.
        }

        System.out.println("All Java 17 quantum-control tests passed.");
    }

    public static void main(String[] args) {
        try {
            Qubit qubit = new Qubit(
                "QUBIT-001",
                5.0,
                100,
                80
            );

            HardwareLimits limits = new HardwareLimits(
                10,
                0.001,
                100,
                5,
                1000
            );

            HardwareSafetyPolicy safety =
                new HardwareSafetyPolicy(limits);

            QuantumController controller =
                new QuantumController(safety, limits.maxPulses());

            CalibrationService service =
                new CalibrationService(
                    controller,
                    new CalibrationPolicy(0.95)
                );

            System.out.println("\nQUANTUM CONTROL ENTERPRISE SYSTEM");

            CalibrationRecord record = service.calibrate(
                qubit,
                1.0,
                PI,
                101
            );

            System.out.println("\nCALIBRATION RESULT");
            System.out.println("Qubit: " + record.qubitId());
            System.out.println("Version: " + record.version());
            System.out.println("Pi amplitude: " + record.piAmplitude());
            System.out.println(
                "Pi/2 amplitude: " + record.piOverTwoAmplitude()
            );
            System.out.println("Error: " + record.excitationError());
            System.out.println("Status: " + record.status());

            PulseSchedule schedule = new PulseSchedule(
                safety,
                limits.maxPulses()
            );

            schedule.add(new Pulse(
                "CALIBRATED-PI",
                PulseType.X,
                record.piAmplitude(),
                1.0,
                0,
                0,
                0
            ));

            BlochSnapshot finalState =
                schedule.execute(controller).snapshot();

            System.out.println("\nEXECUTION RESULT");
            System.out.println(finalState);

            System.out.println(
                "\nCalibration history: " +
                service.history(qubit.id()).size()
            );

            runTests(safety);

        } catch (ControlException exception) {
            System.err.println(
                "CONTROL ERROR: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
