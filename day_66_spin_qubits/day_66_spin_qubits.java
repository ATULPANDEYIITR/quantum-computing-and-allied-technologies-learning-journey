/*
 * Spin Qubits in Semiconductor Quantum Systems
 *
 * Java 17 enterprise-oriented laboratory control model.
 *
 * Features:
 * - Semiconductor device registry
 * - Electron spin state management
 * - ESR and EDSR pulse policies
 * - Calibration approval
 * - Experiment lifecycle management
 * - Measurement records
 * - Device access authorization
 * - Coherence monitoring
 * - Exchange interaction scheduling
 *
 * Compile: javac SpinQubitEnterprise.java
 * Run: java SpinQubitEnterprise
 */

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

public class SpinQubitEnterprise {

    enum Material {
        SILICON,
        GERMANIUM,
        GALLIUM_ARSENIDE
    }

    enum Architecture {
        GATE_DEFINED_QUANTUM_DOT,
        DOUBLE_QUANTUM_DOT,
        DONOR_BOUND_ELECTRON
    }

    enum DeviceStatus {
        OFFLINE,
        READY,
        RUNNING,
        FAULT
    }

    enum ReviewStatus {
        PENDING,
        APPROVED,
        REJECTED
    }

    enum ControlMechanism {
        ESR,
        EDSR,
        VIRTUAL_Z
    }

    enum ExperimentStatus {
        CREATED,
        CALIBRATING,
        APPROVED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    record DeviceConfiguration(
        String deviceId,
        Material material,
        Architecture architecture,
        double temperatureMilliKelvin,
        double magneticFieldTesla,
        double t1Microseconds,
        double t2Microseconds,
        double exchangeCouplingMHz
    ) {
        DeviceConfiguration {
            Objects.requireNonNull(deviceId);
            Objects.requireNonNull(material);
            Objects.requireNonNull(architecture);

            if (deviceId.isBlank() ||
                temperatureMilliKelvin <= 0 ||
                magneticFieldTesla < 0 ||
                t1Microseconds <= 0 ||
                t2Microseconds <= 0 ||
                exchangeCouplingMHz < 0 ||
                t2Microseconds > 2 * t1Microseconds) {
                throw new IllegalArgumentException(
                    "Invalid semiconductor device configuration."
                );
            }
        }
    }

    record CalibrationRecord(
        String calibrationId,
        String deviceId,
        String operator,
        double gateFidelity,
        double fieldErrorTesla,
        Instant calibratedAt
    ) {
        CalibrationRecord {
            Objects.requireNonNull(calibrationId);
            Objects.requireNonNull(deviceId);
            Objects.requireNonNull(operator);
            Objects.requireNonNull(calibratedAt);

            if (gateFidelity < 0 || gateFidelity > 1 ||
                fieldErrorTesla < 0 ||
                operator.isBlank()) {
                throw new IllegalArgumentException(
                    "Invalid calibration record."
                );
            }
        }
    }

    record Approval(
        String reviewer,
        ReviewStatus status,
        String reason,
        Instant reviewedAt
    ) {
        Approval {
            Objects.requireNonNull(reviewer);
            Objects.requireNonNull(status);
            Objects.requireNonNull(reviewedAt);

            if (reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer is required.");
            }
        }
    }

    record Measurement(
        String measurementId,
        String experimentId,
        String qubitId,
        int shots,
        int zeroCount,
        int oneCount,
        Instant timestamp
    ) {
        Measurement {
            Objects.requireNonNull(measurementId);
            Objects.requireNonNull(experimentId);
            Objects.requireNonNull(qubitId);
            Objects.requireNonNull(timestamp);

            if (shots <= 0 || zeroCount < 0 || oneCount < 0 ||
                zeroCount + oneCount != shots) {
                throw new IllegalArgumentException(
                    "Invalid measurement counts."
                );
            }
        }

        double probabilityZero() {
            return (double) zeroCount / shots;
        }

        double probabilityOne() {
            return (double) oneCount / shots;
        }
    }

    record ControlPulse(
        String pulseId,
        String qubitId,
        String axis,
        double angleRadians,
        double durationNanoseconds,
        ControlMechanism mechanism
    ) {
        ControlPulse {
            Objects.requireNonNull(pulseId);
            Objects.requireNonNull(qubitId);
            Objects.requireNonNull(axis);
            Objects.requireNonNull(mechanism);

            if (!List.of("X", "Y", "Z").contains(axis) ||
                !Double.isFinite(angleRadians) ||
                !Double.isFinite(durationNanoseconds) ||
                durationNanoseconds <= 0) {
                throw new IllegalArgumentException("Invalid control pulse.");
            }

            if (mechanism == ControlMechanism.VIRTUAL_Z &&
                !axis.equals("Z")) {
                throw new IllegalArgumentException(
                    "Virtual-Z pulses require the Z axis."
                );
            }
        }
    }

    record BlochState(double x, double y, double z) {

        BlochState {
            if (!Double.isFinite(x) ||
                !Double.isFinite(y) ||
                !Double.isFinite(z) ||
                magnitude(x, y, z) > 1.0 + 1e-9) {
                throw new IllegalArgumentException(
                    "Invalid Bloch state."
                );
            }
        }

        private static double magnitude(double x, double y, double z) {
            return Math.sqrt(x * x + y * y + z * z);
        }

        double purity() {
            return (1 + magnitude(x, y, z) * magnitude(x, y, z)) / 2;
        }

        double probabilityZero() {
            return (1 + z) / 2;
        }

        double probabilityOne() {
            return (1 - z) / 2;
        }

        BlochState rotate(String axis, double angle) {
            double c = Math.cos(angle);
            double s = Math.sin(angle);

            return switch (axis) {
                case "X" -> new BlochState(
                    x, y * c - z * s, y * s + z * c
                );
                case "Y" -> new BlochState(
                    x * c + z * s, y, -x * s + z * c
                );
                case "Z" -> new BlochState(
                    x * c - y * s, x * s + y * c, z
                );
                default -> throw new IllegalArgumentException(
                    "Unsupported rotation axis."
                );
            };
        }

        BlochState evolve(double duration, DeviceConfiguration device) {
            if (duration < 0 || !Double.isFinite(duration)) {
                throw new IllegalArgumentException("Invalid duration.");
            }

            double relaxation = Math.exp(-duration / device.t1Microseconds());
            double dephasing = Math.exp(-duration / device.t2Microseconds());

            return new BlochState(
                x * Math.sqrt(relaxation) * dephasing,
                y * Math.sqrt(relaxation) * dephasing,
                1 - (1 - z) * relaxation
            );
        }
    }

    static final class QuantumDevice {
        private final DeviceConfiguration configuration;
        private DeviceStatus status = DeviceStatus.OFFLINE;
        private CalibrationRecord calibration;

        QuantumDevice(DeviceConfiguration configuration) {
            this.configuration = Objects.requireNonNull(configuration);
        }

        synchronized void initialize() {
            if (status != DeviceStatus.OFFLINE) {
                throw new DomainException("Invalid initialization state.");
            }

            status = DeviceStatus.READY;
        }

        synchronized void calibrate(CalibrationRecord record) {
            if (status != DeviceStatus.READY) {
                throw new DomainException("Device is not ready.");
            }

            if (!record.deviceId().equals(configuration.deviceId())) {
                throw new DomainException("Calibration device mismatch.");
            }

            if (record.gateFidelity() < 0.95) {
                throw new DomainException("Calibration fidelity too low.");
            }

            calibration = record;
        }

        synchronized void start() {
            if (status != DeviceStatus.READY || calibration == null) {
                throw new DomainException(
                    "Ready device and valid calibration are required."
                );
            }

            status = DeviceStatus.RUNNING;
        }

        synchronized void stop() {
            if (status != DeviceStatus.RUNNING) {
                throw new DomainException("Device is not running.");
            }

            status = DeviceStatus.READY;
        }

        DeviceConfiguration configuration() {
            return configuration;
        }

        DeviceStatus status() {
            return status;
        }

        boolean isCalibrated() {
            return calibration != null;
        }
    }

    static final class Qubit {
        private final String id;
        private final QuantumDevice device;
        private BlochState state = new BlochState(0, 0, 1);
        private final List<ControlPulse> executedPulses = new ArrayList<>();

        Qubit(String id, QuantumDevice device) {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Qubit ID is required.");
            }

            this.id = id;
            this.device = Objects.requireNonNull(device);
        }

        synchronized void execute(ControlPulse pulse) {
            if (device.status() != DeviceStatus.RUNNING) {
                throw new DomainException("Device is not running.");
            }

            if (!device.isCalibrated()) {
                throw new DomainException("Device is not calibrated.");
            }

            if (!pulse.qubitId().equals(id)) {
                throw new DomainException("Pulse-qubit mismatch.");
            }

            state = state.rotate(pulse.axis(), pulse.angleRadians());
            executedPulses.add(pulse);
        }

        synchronized void evolve(double duration) {
            state = state.evolve(duration, device.configuration());
        }

        synchronized BlochState state() {
            return state;
        }

        String id() {
            return id;
        }

        List<ControlPulse> pulseHistory() {
            return Collections.unmodifiableList(
                new ArrayList<>(executedPulses)
            );
        }
    }

    static final class Experiment {
        private final String id;
        private final QuantumDevice device;
        private final Map<String, Qubit> qubits = new HashMap<>();
        private final List<Measurement> measurements = new ArrayList<>();
        private ExperimentStatus status = ExperimentStatus.CREATED;
        private Approval approval;

        Experiment(String id, QuantumDevice device) {
            this.id = Objects.requireNonNull(id);
            this.device = Objects.requireNonNull(device);

            if (id.isBlank()) {
                throw new IllegalArgumentException(
                    "Experiment ID is required."
                );
            }
        }

        synchronized void registerQubit(Qubit qubit) {
            if (status == ExperimentStatus.RUNNING ||
                status == ExperimentStatus.COMPLETED) {
                throw new DomainException(
                    "Cannot register qubits after experiment execution."
                );
            }

            if (qubits.putIfAbsent(qubit.id(), qubit) != null) {
                throw new DomainException("Duplicate qubit.");
            }
        }

        synchronized void submitForApproval() {
            if (status != ExperimentStatus.CREATED) {
                throw new DomainException("Invalid approval transition.");
            }

            status = ExperimentStatus.CALIBRATING;
        }

        synchronized void review(Approval decision) {
            if (status != ExperimentStatus.CALIBRATING) {
                throw new DomainException("Experiment is not under review.");
            }

            approval = decision;

            if (decision.status() == ReviewStatus.APPROVED) {
                status = ExperimentStatus.APPROVED;
            } else if (decision.status() == ReviewStatus.REJECTED) {
                status = ExperimentStatus.FAILED;
            }
        }

        synchronized void start() {
            if (status != ExperimentStatus.APPROVED) {
                throw new DomainException("Experiment is not approved.");
            }

            device.start();
            status = ExperimentStatus.RUNNING;
        }

        synchronized Measurement measure(String qubitId, int shots) {
            if (status != ExperimentStatus.RUNNING) {
                throw new DomainException(
                    "Experiment must be running."
                );
            }

            if (shots <= 0 || shots > 10_000_000) {
                throw new IllegalArgumentException("Invalid shot count.");
            }

            Qubit qubit = qubits.get(qubitId);

            if (qubit == null) {
                throw new DomainException("Unknown qubit.");
            }

            int zeros = 0;

            // Independent Bernoulli trials model computational-basis readout.
            for (int i = 0; i < shots; i++) {
                if (Math.random() < qubit.state().probabilityZero()) {
                    zeros++;
                }
            }

            Measurement result = new Measurement(
                UUID.randomUUID().toString(),
                id,
                qubitId,
                shots,
                zeros,
                shots - zeros,
                Instant.now()
            );

            measurements.add(result);
            return result;
        }

        synchronized void complete() {
            if (status != ExperimentStatus.RUNNING) {
                throw new DomainException("Experiment is not running.");
            }

            device.stop();
            status = ExperimentStatus.COMPLETED;
        }

        List<Measurement> measurements() {
            return Collections.unmodifiableList(
                new ArrayList<>(measurements)
            );
        }

        ExperimentStatus status() {
            return status;
        }

        String id() {
            return id;
        }
    }

    static final class ExchangePolicy {
        private record Reservation(
            String first,
            String second,
            double start,
            double end
        ) {}

        private final List<Reservation> reservations = new ArrayList<>();

        synchronized double schedule(
            Qubit first,
            Qubit second,
            double startMicroseconds,
            double durationMicroseconds,
            double couplingMHz
        ) {
            if (first.id().equals(second.id()) ||
                startMicroseconds < 0 ||
                durationMicroseconds <= 0 ||
                couplingMHz < 0) {
                throw new DomainException(
                    "Invalid exchange interaction request."
                );
            }

            double end = startMicroseconds + durationMicroseconds;

            for (Reservation reservation : reservations) {
                if (startMicroseconds < reservation.end() &&
                    end > reservation.start()) {
                    throw new DomainException(
                        "Exchange control channel conflict."
                    );
                }
            }

            reservations.add(new Reservation(
                first.id(),
                second.id(),
                startMicroseconds,
                end
            ));

            return 2 * Math.PI * couplingMHz * durationMicroseconds;
        }
    }

    static final class DeviceAccessPolicy {
        private final Map<String, List<String>> permissions = new HashMap<>();

        void grant(String operator, String permission) {
            permissions.computeIfAbsent(
                operator, ignored -> new ArrayList<>()
            ).add(permission);
        }

        void authorize(String operator, String permission) {
            if (!permissions.getOrDefault(operator, List.of())
                    .contains(permission)) {
                throw new SecurityException(
                    "Operator is not authorized for " + permission
                );
            }
        }
    }

    public static void main(String[] args) {
        try {
            DeviceConfiguration configuration = new DeviceConfiguration(
                "SI-QD-001",
                Material.SILICON,
                Architecture.DOUBLE_QUANTUM_DOT,
                20,
                0.5,
                1000,
                100,
                5
            );

            QuantumDevice device = new QuantumDevice(configuration);
            device.initialize();

            CalibrationRecord calibration = new CalibrationRecord(
                "CAL-001",
                "SI-QD-001",
                "operator-01",
                0.995,
                0.0001,
                Instant.now()
            );

            device.calibrate(calibration);

            DeviceAccessPolicy accessPolicy = new DeviceAccessPolicy();
            accessPolicy.grant("researcher-01", "RUN_EXPERIMENT");
            accessPolicy.authorize("researcher-01", "RUN_EXPERIMENT");

            Experiment experiment = new Experiment("EXP-001", device);

            Qubit q0 = new Qubit("Q0", device);
            Qubit q1 = new Qubit("Q1", device);

            experiment.registerQubit(q0);
            experiment.registerQubit(q1);

            experiment.submitForApproval();

            experiment.review(new Approval(
                "principal-investigator",
                ReviewStatus.APPROVED,
                "Calibration and experiment configuration verified.",
                Instant.now()
            ));

            experiment.start();

            ControlPulse pulse = new ControlPulse(
                "PULSE-001",
                "Q0",
                "Y",
                Math.PI / 2,
                50,
                ControlMechanism.ESR
            );

            q0.execute(pulse);
            q0.evolve(10);

            Measurement measurement = experiment.measure("Q0", 1000);

            ExchangePolicy exchangePolicy = new ExchangePolicy();

            double phase = exchangePolicy.schedule(
                q0, q1, 0, 0.05, 5
            );

            experiment.complete();

            System.out.println("Experiment: " + experiment.id());
            System.out.println("Status: " + experiment.status());
            System.out.println("Device: " + configuration.deviceId());
            System.out.println("Material: " + configuration.material());
            System.out.println("Qubit state: " + q0.state());
            System.out.println("State purity: " + q0.state().purity());
            System.out.println("Measurement: " + measurement);
            System.out.println("P(0): " + measurement.probabilityZero());
            System.out.println("Exchange phase: " + phase);
            System.out.println("Executed pulses: " +
                q0.pulseHistory().size());

            System.out.println(
                "Measurement records: " +
                experiment.measurements().stream()
                    .filter(m -> m.shots() > 0)
                    .count()
            );

        } catch (Exception exception) {
            System.err.println(
                "Laboratory workflow failed: " + exception.getMessage()
            );
            System.exitCode = 1;
        }
    }
}
