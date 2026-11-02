import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

public class TrappedIonControl {

    enum GateType {
        SINGLE_QUBIT,
        ENTANGLING
    }

    enum ReviewStatus {
        PASS,
        FAIL
    }

    static final class ControlException extends RuntimeException {
        ControlException(String message) {
            super(message);
        }
    }

    record Ion(
        int id,
        double massAmu,
        double axialFrequencyMHz
    ) {
        Ion {
            if (id < 0 || massAmu <= 0 || axialFrequencyMHz <= 0) {
                throw new ControlException("Invalid ion parameters.");
            }
        }
    }

    record Trap(
        double radialFrequencyMHz,
        double axialFrequencyMHz,
        double laserWavelengthNm
    ) {
        Trap {
            if (radialFrequencyMHz <= axialFrequencyMHz) {
                throw new ControlException(
                    "Radial frequency must exceed axial frequency."
                );
            }

            if (laserWavelengthNm < 200 || laserWavelengthNm > 2000) {
                throw new ControlException("Unsupported laser wavelength.");
            }
        }

        double modeSpacingMHz() {
            return radialFrequencyMHz - axialFrequencyMHz;
        }
    }

    record LaserCalibration(
        double rabiScale,
        double frequencyOffsetMHz
    ) {
        LaserCalibration {
            if (rabiScale <= 0 || !Double.isFinite(frequencyOffsetMHz)) {
                throw new ControlException("Invalid laser calibration.");
            }
        }
    }

    record LaserChannel(
        String name,
        double maxPowerMw,
        LaserCalibration calibration
    ) {
        LaserChannel {
            Objects.requireNonNull(name);
            Objects.requireNonNull(calibration);

            if (name.isBlank() || maxPowerMw <= 0) {
                throw new ControlException("Invalid laser channel.");
            }
        }

        double effectiveRabi(double requestedMHz) {
            return requestedMHz * calibration.rabiScale();
        }

        double effectiveDetuning(double requestedMHz) {
            return requestedMHz + calibration.frequencyOffsetMHz();
        }
    }

    record Pulse(
        String id,
        int ion,
        Optional<Integer> targetIon,
        double startNs,
        double durationNs,
        double rabiFrequencyMHz,
        double detuningMHz,
        double phaseRad,
        GateType gateType,
        String laserChannel
    ) {
        Pulse {
            if (id == null || id.isBlank()) {
                throw new ControlException("Pulse ID is required.");
            }

            if (startNs < 0 || durationNs <= 0) {
                throw new ControlException("Invalid pulse timing.");
            }

            if (rabiFrequencyMHz <= 0) {
                throw new ControlException("Rabi frequency must be positive.");
            }

            Objects.requireNonNull(targetIon);
            Objects.requireNonNull(gateType);
            Objects.requireNonNull(laserChannel);

            if (gateType == GateType.ENTANGLING &&
                (targetIon.isEmpty() || targetIon.get() == ion)) {
                throw new ControlException(
                    "Entangling pulse needs two distinct ions."
                );
            }
        }

        double endNs() {
            return startNs + durationNs;
        }

        Set<Integer> occupiedIons() {
            Set<Integer> result = new HashSet<>();
            result.add(ion);
            targetIon.ifPresent(result::add);
            return result;
        }
    }

    interface ControlPolicy {
        void validate(Pulse pulse, Trap trap, LaserChannel channel);
    }

    static final class ConservativeLaserPolicy implements ControlPolicy {
        private final double maxDetuningMHz;
        private final double maxPulseNs;

        ConservativeLaserPolicy(
            double maxDetuningMHz,
            double maxPulseNs
        ) {
            this.maxDetuningMHz = maxDetuningMHz;
            this.maxPulseNs = maxPulseNs;
        }

        @Override
        public void validate(
            Pulse pulse,
            Trap trap,
            LaserChannel channel
        ) {
            double effectiveDetuning =
                channel.effectiveDetuning(pulse.detuningMHz());

            if (Math.abs(effectiveDetuning) > maxDetuningMHz) {
                throw new ControlException(
                    "Effective detuning exceeds policy."
                );
            }

            if (pulse.durationNs() > maxPulseNs) {
                throw new ControlException(
                    "Pulse duration exceeds policy."
                );
            }

            double estimatedPower =
                channel.effectiveRabi(pulse.rabiFrequencyMHz()) * 0.02;

            if (estimatedPower > channel.maxPowerMw()) {
                throw new ControlException(
                    "Estimated optical power exceeds channel limit."
                );
            }

            if (pulse.gateType() == GateType.ENTANGLING &&
                trap.modeSpacingMHz() <= 0) {
                throw new ControlException(
                    "Trap does not provide valid mode separation."
                );
            }
        }
    }

    static final class PulseTimeline {
        private final List<Pulse> pulses = new ArrayList<>();

        void add(Pulse candidate) {
            for (Pulse existing : pulses) {
                if (overlaps(existing, candidate) &&
                    !disjointIons(existing, candidate)) {
                    throw new ControlException(
                        "Pulse conflicts with an existing pulse."
                    );
                }
            }

            pulses.add(candidate);
            pulses.sort(Comparator.comparingDouble(Pulse::startNs));
        }

        private boolean overlaps(Pulse a, Pulse b) {
            return a.startNs() < b.endNs() &&
                   b.startNs() < a.endNs();
        }

        private boolean disjointIons(Pulse a, Pulse b) {
            Set<Integer> first = a.occupiedIons();
            Set<Integer> second = b.occupiedIons();

            return first.stream().noneMatch(second::contains);
        }

        List<Pulse> snapshot() {
            return List.copyOf(pulses);
        }
    }

    static final class IonTrapService {
        private final Trap trap;
        private final Map<Integer, Ion> ions;
        private final Map<String, LaserChannel> lasers;
        private final ControlPolicy policy;
        private final PulseTimeline timeline;

        IonTrapService(
            Trap trap,
            List<Ion> ions,
            List<LaserChannel> lasers,
            ControlPolicy policy
        ) {
            this.trap = Objects.requireNonNull(trap);
            this.ions = new HashMap<>();
            this.lasers = new HashMap<>();
            this.policy = Objects.requireNonNull(policy);
            this.timeline = new PulseTimeline();

            for (Ion ion : ions) {
                if (this.ions.putIfAbsent(ion.id(), ion) != null) {
                    throw new ControlException("Duplicate ion ID.");
                }
            }

            if (this.ions.isEmpty()) {
                throw new ControlException("At least one ion is required.");
            }

            for (LaserChannel laser : lasers) {
                if (this.lasers.putIfAbsent(laser.name(), laser) != null) {
                    throw new ControlException("Duplicate laser channel.");
                }
            }
        }

        void apply(Pulse pulse) {
            if (!ions.containsKey(pulse.ion())) {
                throw new ControlException("Unknown primary ion.");
            }

            pulse.targetIon().ifPresent(target -> {
                if (!ions.containsKey(target)) {
                    throw new ControlException("Unknown target ion.");
                }
            });

            LaserChannel laser = lasers.get(pulse.laserChannel());

            if (laser == null) {
                throw new ControlException("Unknown laser channel.");
            }

            policy.validate(pulse, trap, laser);
            timeline.add(pulse);
        }

        List<Pulse> scheduledPulses() {
            return timeline.snapshot();
        }

        Map<GateType, Long> countByGateType() {
            return timeline.snapshot()
                .stream()
                .collect(Collectors.groupingBy(
                    Pulse::gateType,
                    () -> new EnumMap<>(GateType.class),
                    Collectors.counting()
                ));
        }
    }

    static final class CalibrationService {
        record Result(
            ReviewStatus status,
            double measuredRabiMHz,
            double measuredDetuningMHz
        ) {}

        Result evaluate(
            double targetRabiMHz,
            double measuredRabiMHz,
            double measuredDetuningMHz
        ) {
            if (targetRabiMHz <= 0) {
                throw new ControlException("Invalid calibration target.");
            }

            double relativeError =
                Math.abs(measuredRabiMHz - targetRabiMHz) /
                targetRabiMHz;

            ReviewStatus status =
                relativeError <= 0.05 &&
                Math.abs(measuredDetuningMHz) <= 5.0
                    ? ReviewStatus.PASS
                    : ReviewStatus.FAIL;

            return new Result(
                status,
                measuredRabiMHz,
                measuredDetuningMHz
            );
        }
    }

    private static void printTimeline(
        List<Pulse> pulses
    ) {
        System.out.println("\nControl timeline");

        pulses.forEach(pulse -> {
            String target = pulse.targetIon()
                .map(id -> " -> ion " + id)
                .orElse("");

            System.out.printf(
                "  %7.1f-%7.1f ns | %-30s | ion %d%s | %s%n",
                pulse.startNs(),
                pulse.endNs(),
                pulse.id(),
                pulse.ion(),
                target,
                pulse.gateType()
            );
        });
    }

    public static void main(String[] args) {
        Trap trap = new Trap(
            4.5,
            1.0,
            397.0
        );

        List<Ion> ions = List.of(
            new Ion(0, 40.0, 1.0),
            new Ion(1, 40.0, 1.0),
            new Ion(2, 40.0, 1.0)
        );

        LaserChannel controlLaser = new LaserChannel(
            "397nm-control",
            20.0,
            new LaserCalibration(0.98, 0.01)
        );

        ControlPolicy policy =
            new ConservativeLaserPolicy(5.0, 2000.0);

        IonTrapService service = new IonTrapService(
            trap,
            ions,
            List.of(controlLaser),
            policy
        );

        CalibrationService calibration =
            new CalibrationService();

        CalibrationService.Result calibrationResult =
            calibration.evaluate(1.0, 0.99, 0.01);

        if (calibrationResult.status() != ReviewStatus.PASS) {
            throw new ControlException(
                "Laser calibration failed."
            );
        }

        Pulse singleQubit = new Pulse(
            "carrier-pi-over-two",
            0,
            Optional.empty(),
            0,
            250,
            1.0,
            0.0,
            0.0,
            GateType.SINGLE_QUBIT,
            "397nm-control"
        );

        Pulse entangling = new Pulse(
            "motional-entangling-pulse",
            0,
            Optional.of(1),
            1000,
            500,
            1.0,
            0.0,
            Math.PI / 2,
            GateType.ENTANGLING,
            "397nm-control"
        );

        service.apply(singleQubit);
        service.apply(entangling);

        printTimeline(service.scheduledPulses());

        System.out.println("\nCalibration status: " +
            calibrationResult.status());

        System.out.printf(
            "Measured Rabi frequency: %.3f MHz%n",
            calibrationResult.measuredRabiMHz()
        );

        System.out.printf(
            "Measured detuning: %.3f MHz%n",
            calibrationResult.measuredDetuningMHz()
        );

        System.out.println(
            "\nGate counts: " +
            service.countByGateType()
        );

        Pulse unsafe = new Pulse(
            "unsafe-detuning",
            0,
            Optional.empty(),
            2000,
            100,
            1.0,
            15.0,
            0.0,
            GateType.SINGLE_QUBIT,
            "397nm-control"
        );

        try {
            service.apply(unsafe);
            throw new ControlException(
                "Unsafe pulse was accepted unexpectedly."
            );
        } catch (ControlException expected) {
            System.out.println(
                "Safety policy rejection: " + expected.getMessage()
            );
        }

        Pulse conflicting = new Pulse(
            "conflicting-pulse",
            0,
            Optional.empty(),
            100,
            300,
            1.0,
            0.0,
            0.0,
            GateType.SINGLE_QUBIT,
            "397nm-control"
        );

        try {
            service.apply(conflicting);
            throw new ControlException(
                "Conflicting pulse was accepted unexpectedly."
            );
        } catch (ControlException expected) {
            System.out.println(
                "Scheduler rejection: " + expected.getMessage()
            );
        }

        System.out.printf(
            "%nMode spacing: %.3f MHz%n",
            trap.modeSpacingMHz()
        );

        System.out.println("Enterprise control model checks passed.");
    }
}
