#!/usr/bin/env python3
"""
Quantum Control: Pulse Generation, Calibration, and Qubit Control.

Implements:
- Qubit state representation using Bloch vectors.
- Microwave control pulses.
- X, Y, and arbitrary-axis rotations.
- Rabi oscillation experiments.
- Pi and pi/2 pulse calibration.
- Ramsey detuning estimation.
- Pulse-sequence validation and scheduling.
- Calibration history and reproducibility.
- Safety limits and automated tests.

This is a pedagogical simulator, not hardware-control software.
"""

from __future__ import annotations

import json
import math
import statistics
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


EPSILON = 1e-10


class ControlError(Exception):
    """Base exception for quantum-control failures."""


class ValidationError(ControlError):
    """Invalid pulse or calibration parameters."""


class SafetyError(ControlError):
    """A control operation violates safety limits."""


class PulseType(Enum):
    X = "X"
    Y = "Y"
    ARBITRARY = "ARBITRARY"


class CalibrationStatus(Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class HardwareLimits:
    max_amplitude: float = 10.0
    max_duration: float = 100.0
    min_duration: float = 0.001
    max_detuning: float = 5.0
    max_pulses: int = 1000


@dataclass
class Qubit:
    qubit_id: str
    frequency_ghz: float
    t1_us: float
    t2_us: float

    def __post_init__(self):
        if not self.qubit_id:
            raise ValidationError("Qubit ID cannot be empty.")
        if self.frequency_ghz <= 0:
            raise ValidationError("Frequency must be positive.")
        if self.t1_us <= 0 or self.t2_us <= 0:
            raise ValidationError("Relaxation times must be positive.")
        if self.t2_us > 2 * self.t1_us:
            raise ValidationError("Physical constraint T2 <= 2*T1 violated.")


@dataclass(frozen=True)
class Pulse:
    pulse_id: str
    pulse_type: PulseType
    amplitude: float
    duration_us: float
    phase_rad: float = 0.0
    detuning_mhz: float = 0.0
    start_us: float = 0.0

    def __post_init__(self):
        values = (
            self.amplitude,
            self.duration_us,
            self.phase_rad,
            self.detuning_mhz,
            self.start_us,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValidationError("Pulse parameters must be finite.")
        if self.amplitude < 0 or self.duration_us <= 0:
            raise ValidationError("Amplitude must be nonnegative and duration positive.")
        if self.start_us < 0:
            raise ValidationError("Pulse start time cannot be negative.")

    @property
    def end_us(self) -> float:
        return self.start_us + self.duration_us


@dataclass
class BlochState:
    x: float = 0.0
    y: float = 0.0
    z: float = 1.0

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.x, self.y, self.z)):
            raise ValidationError("Bloch coordinates must be finite.")

    @property
    def excited_probability(self) -> float:
        return max(0.0, min(1.0, (1.0 - self.z) / 2.0))

    @property
    def norm(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def rotate(self, axis_x: float, axis_y: float,
               axis_z: float, angle: float) -> None:
        """Apply Rodrigues' rotation formula."""
        norm = math.sqrt(axis_x**2 + axis_y**2 + axis_z**2)
        if norm < EPSILON:
            return

        ux, uy, uz = axis_x / norm, axis_y / norm, axis_z / norm
        c, s = math.cos(angle), math.sin(angle)

        dot = ux * self.x + uy * self.y + uz * self.z
        cross_x = uy * self.z - uz * self.y
        cross_y = uz * self.x - ux * self.z
        cross_z = ux * self.y - uy * self.x

        self.x = self.x * c + cross_x * s + ux * dot * (1 - c)
        self.y = self.y * c + cross_y * s + uy * dot * (1 - c)
        self.z = self.z * c + cross_z * s + uz * dot * (1 - c)


class PulseController:
    def __init__(self, limits: HardwareLimits):
        self.limits = limits
        self.executed_pulses = 0

    def validate(self, pulse: Pulse) -> None:
        if pulse.amplitude > self.limits.max_amplitude:
            raise SafetyError("Pulse amplitude exceeds hardware limit.")
        if not self.limits.min_duration <= pulse.duration_us <= self.limits.max_duration:
            raise SafetyError("Pulse duration violates hardware limits.")
        if abs(pulse.detuning_mhz) > self.limits.max_detuning:
            raise SafetyError("Detuning exceeds hardware limit.")

    def execute(self, pulse: Pulse, state: BlochState) -> BlochState:
        self.validate(pulse)

        if self.executed_pulses >= self.limits.max_pulses:
            raise SafetyError("Maximum pulse count exceeded.")

        # Angular frequency is expressed in radians per microsecond.
        drive = pulse.amplitude
        detuning = 2 * math.pi * pulse.detuning_mhz / 1000.0

        axis_x = drive * math.cos(pulse.phase_rad)
        axis_y = drive * math.sin(pulse.phase_rad)
        axis_z = detuning

        angular_frequency = math.sqrt(
            axis_x**2 + axis_y**2 + axis_z**2
        )

        angle = angular_frequency * pulse.duration_us

        state.rotate(axis_x, axis_y, axis_z, angle)
        self.executed_pulses += 1
        return state


class PulseSequence:
    def __init__(self, controller: PulseController):
        self.controller = controller
        self.pulses: list[Pulse] = []

    def add(self, pulse: Pulse) -> None:
        self.controller.validate(pulse)

        if len(self.pulses) >= self.controller.limits.max_pulses:
            raise SafetyError("Sequence pulse limit exceeded.")

        for existing in self.pulses:
            overlaps = (
                pulse.start_us < existing.end_us
                and existing.start_us < pulse.end_us
            )
            if overlaps:
                raise ValidationError(
                    f"Pulse overlap: {pulse.pulse_id} and {existing.pulse_id}"
                )

        self.pulses.append(pulse)
        self.pulses.sort(key=lambda item: item.start_us)

    def run(self, initial_state: Optional[BlochState] = None) -> BlochState:
        state = initial_state or BlochState()

        for pulse in self.pulses:
            self.controller.execute(pulse, state)

        return state


@dataclass
class CalibrationResult:
    calibration_id: str
    qubit_id: str
    calibration_type: str
    pi_amplitude: float
    pi_over_2_amplitude: float
    measured_error: float
    status: CalibrationStatus
    timestamp: str


class CalibrationEngine:
    def __init__(self, controller: PulseController):
        self.controller = controller
        self.history: list[CalibrationResult] = []

    def rabi_probability(self, amplitude: float,
                         duration_us: float) -> float:
        pulse = Pulse(
            pulse_id="rabi-test",
            pulse_type=PulseType.X,
            amplitude=amplitude,
            duration_us=duration_us,
        )

        state = BlochState()
        self.controller.validate(pulse)
        self.controller.execute(pulse, state)
        return state.excited_probability

    def calibrate_rabi(
        self,
        qubit: Qubit,
        pulse_duration_us: float,
        target_amplitude: float,
        samples: int = 101,
    ) -> CalibrationResult:
        if not 3 <= samples <= 10001:
            raise ValidationError("Samples must be between 3 and 10001.")

        if not 0 < target_amplitude <= self.controller.limits.max_amplitude:
            raise ValidationError("Invalid target amplitude.")

        candidates = [
            target_amplitude * i / (samples - 1)
            for i in range(1, samples)
        ]

        measurements = [
            (amplitude, self.rabi_probability(
                amplitude, pulse_duration_us
            ))
            for amplitude in candidates
        ]

        # A pi pulse maximizes the excited-state probability.
        best_amplitude, best_probability = max(
            measurements, key=lambda item: item[1]
        )

        result = CalibrationResult(
            calibration_id=str(uuid.uuid4()),
            qubit_id=qubit.qubit_id,
            calibration_type="RABI",
            pi_amplitude=best_amplitude,
            pi_over_2_amplitude=best_amplitude / 2,
            measured_error=1.0 - best_probability,
            status=(
                CalibrationStatus.PASSED
                if best_probability >= 0.95
                else CalibrationStatus.FAILED
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self.history.append(result)
        return result

    @staticmethod
    def estimate_ramsey_detuning(
        probabilities: list[float],
        delays_us: list[float],
        sampling_frequency_mhz: float,
    ) -> float:
        """Estimate frequency from adjacent Ramsey phase differences.

        This estimator assumes a sufficiently sampled, approximately
        sinusoidal signal without phase wrapping between samples.
        """
        if len(probabilities) != len(delays_us) or len(delays_us) < 3:
            raise ValidationError("At least three matching samples are required.")

        if sampling_frequency_mhz <= 0:
            raise ValidationError("Sampling frequency must be positive.")

        if any(not 0 <= p <= 1 for p in probabilities):
            raise ValidationError("Probabilities must be between zero and one.")

        if any(
            not math.isfinite(t) for t in delays_us
        ) or any(
            delays_us[i] >= delays_us[i + 1]
            for i in range(len(delays_us) - 1)
        ):
            raise ValidationError("Delays must be finite and increasing.")

        centered = [p - statistics.mean(probabilities) for p in probabilities]

        # Estimate phase using the quadrature of the measured signal.
        phases = []
        for i in range(len(centered) - 1):
            phases.append(math.atan2(
                centered[i + 1], centered[i]
            ))

        mean_phase = statistics.mean(phases)
        mean_interval = statistics.mean(
            delays_us[i + 1] - delays_us[i]
            for i in range(len(delays_us) - 1)
        )

        estimate = mean_phase / (2 * math.pi * mean_interval) * 1000

        if abs(estimate) > sampling_frequency_mhz / 2:
            raise ValidationError("Estimated frequency exceeds Nyquist limit.")

        return estimate


def save_calibrations(
    results: list[CalibrationResult],
    filename: str = "quantum_calibrations.json",
) -> None:
    """Persist calibration records as JSON."""
    data = []
    for result in results:
        record = asdict(result)
        record["status"] = result.status.value
        data.append(record)

    path = Path(filename)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_tests() -> None:
    controller = PulseController(HardwareLimits())

    # A calibrated pi pulse flips |0> to |1>.
    pi_pulse = Pulse(
        "pi-test", PulseType.X, math.pi, 1.0
    )
    state = controller.execute(pi_pulse, BlochState())
    assert abs(state.excited_probability - 1.0) < 1e-9

    # A pi/2 pulse produces an equal superposition.
    half_pulse = Pulse(
        "half-test", PulseType.X, math.pi / 2, 1.0
    )
    state = controller.execute(half_pulse, BlochState())
    assert abs(state.excited_probability - 0.5) < 1e-9

    # Y rotation is also a valid state transition.
    y_pulse = Pulse(
        "y-test", PulseType.Y, math.pi, 1.0,
        phase_rad=math.pi / 2
    )
    state = controller.execute(y_pulse, BlochState())
    assert abs(state.excited_probability - 1.0) < 1e-9

    try:
        controller.validate(Pulse(
            "unsafe", PulseType.X, 100.0, 1.0
        ))
        raise AssertionError("Unsafe pulse was accepted.")
    except SafetyError:
        pass

    try:
        sequence = PulseSequence(controller)
        sequence.add(Pulse("p1", PulseType.X, 1.0, 2.0, start_us=0))
        sequence.add(Pulse("p2", PulseType.Y, 1.0, 2.0, start_us=1))
        raise AssertionError("Overlapping pulses were accepted.")
    except ValidationError:
        pass

    print("All quantum-control tests passed.")


def main() -> None:
    qubit = Qubit(
        qubit_id="QUBIT-001",
        frequency_ghz=5.0,
        t1_us=100.0,
        t2_us=80.0,
    )

    controller = PulseController(HardwareLimits())
    engine = CalibrationEngine(controller)

    print("\nQUANTUM CONTROL SIMULATION")
    print("=" * 55)

    calibration = engine.calibrate_rabi(
        qubit=qubit,
        pulse_duration_us=1.0,
        target_amplitude=math.pi,
        samples=101,
    )

    print("\nRABI CALIBRATION")
    print(f"Qubit: {calibration.qubit_id}")
    print(f"Pi amplitude: {calibration.pi_amplitude:.6f}")
    print(f"Pi/2 amplitude: {calibration.pi_over_2_amplitude:.6f}")
    print(f"Excitation error: {calibration.measured_error:.8f}")
    print(f"Status: {calibration.status.value}")

    sequence = PulseSequence(controller)

    sequence.add(Pulse(
        "calibrated-pi",
        PulseType.X,
        calibration.pi_amplitude,
        1.0,
        start_us=0.0,
    ))

    final_state = sequence.run()

    print("\nPULSE EXECUTION")
    print(f"Bloch X: {final_state.x:.6f}")
    print(f"Bloch Y: {final_state.y:.6f}")
    print(f"Bloch Z: {final_state.z:.6f}")
    print(f"Excited probability: {final_state.excited_probability:.6f}")

    save_calibrations(engine.history)
    print("\nCalibration history saved.")

    run_tests()


if __name__ == "__main__":
    try:
        main()
    except ControlError as error:
        print(f"CONTROL ERROR: {error}")
        raise SystemExit(1)
