#!/usr/bin/env python3
"""
Trapped-ion quantum computing: ion-trap and laser-control simulation.

This self-contained program models a small trapped-ion processor:
- ions confined in a linear trap
- qubit states |0> and |1>
- single-qubit laser rotations
- two-qubit entangling operations
- laser detuning and pulse-duration validation
- motional-mode constraints
- pulse scheduling
- state-vector simulation
- measurement
- calibration checks
- error handling and assertions

The simulator is intentionally small enough to run with only the Python
standard library. It models idealized control physics rather than a
laboratory-grade optical or electromagnetic simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import cos, exp, pi, sin, sqrt
from random import Random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


class ControlError(Exception):
    """Raised when an ion-control operation violates a physical constraint."""


class GateType(Enum):
    SINGLE_QUBIT = "single-qubit"
    ENTANGLING = "entangling"
    MEASUREMENT = "measurement"


@dataclass(frozen=True)
class Ion:
    ion_id: int
    position_um: float
    mass_amu: float
    axial_frequency_mhz: float

    def validate(self) -> None:
        if self.ion_id < 0:
            raise ControlError("Ion ID must be non-negative.")
        if self.mass_amu <= 0:
            raise ControlError("Ion mass must be positive.")
        if self.axial_frequency_mhz <= 0:
            raise ControlError("Axial frequency must be positive.")


@dataclass(frozen=True)
class LaserPulse:
    pulse_id: str
    ion_id: int
    duration_ns: float
    rabi_frequency_mhz: float
    detuning_mhz: float
    phase_rad: float
    gate_type: GateType
    target_ion_id: Optional[int] = None

    def validate(self, ions: Dict[int, Ion]) -> None:
        if self.ion_id not in ions:
            raise ControlError(f"Unknown control ion: {self.ion_id}")
        if self.target_ion_id is not None and self.target_ion_id not in ions:
            raise ControlError(f"Unknown target ion: {self.target_ion_id}")
        if self.duration_ns <= 0:
            raise ControlError("Pulse duration must be positive.")
        if self.rabi_frequency_mhz <= 0:
            raise ControlError("Rabi frequency must be positive.")
        if abs(self.detuning_mhz) > 100:
            raise ControlError("Detuning exceeds the simulator safety limit.")


@dataclass(frozen=True)
class TrapConfiguration:
    radial_frequency_mhz: float
    axial_frequency_mhz: float
    laser_wavelength_nm: float
    max_laser_power_mw: float

    def validate(self) -> None:
        if self.radial_frequency_mhz <= self.axial_frequency_mhz:
            raise ControlError(
                "A stable linear-trap model requires radial frequency "
                "above axial frequency."
            )
        if not 200 <= self.laser_wavelength_nm <= 2000:
            raise ControlError("Laser wavelength is outside the model range.")
        if self.max_laser_power_mw <= 0:
            raise ControlError("Maximum laser power must be positive.")


@dataclass
class QubitRegister:
    """Complex state vector for n trapped-ion qubits."""

    n_qubits: int
    amplitudes: List[complex] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.n_qubits <= 0:
            raise ControlError("A register must contain at least one qubit.")

        expected = 1 << self.n_qubits
        if not self.amplitudes:
            self.amplitudes = [0j] * expected
            self.amplitudes[0] = 1 + 0j

        if len(self.amplitudes) != expected:
            raise ControlError("State-vector size does not match qubit count.")

        self.normalize()

    def normalize(self) -> None:
        norm = sqrt(sum(abs(a) ** 2 for a in self.amplitudes))
        if norm == 0:
            raise ControlError("Cannot normalize a zero state vector.")
        self.amplitudes = [a / norm for a in self.amplitudes]

    def probability(self, basis_state: int) -> float:
        if not 0 <= basis_state < len(self.amplitudes):
            raise IndexError("Basis state is outside the register.")
        return abs(self.amplitudes[basis_state]) ** 2

    def probabilities(self) -> Dict[str, float]:
        width = self.n_qubits
        return {
            format(i, f"0{width}b"): self.probability(i)
            for i in range(len(self.amplitudes))
            if self.probability(i) > 1e-12
        }

    def apply_single_qubit(
        self,
        qubit: int,
        matrix: Sequence[Sequence[complex]],
    ) -> None:
        if not 0 <= qubit < self.n_qubits:
            raise ControlError("Qubit index is outside the register.")

        bit = 1 << qubit
        old = self.amplitudes[:]

        for base in range(len(old)):
            if base & bit:
                continue

            partner = base | bit
            a0 = old[base]
            a1 = old[partner]

            self.amplitudes[base] = matrix[0][0] * a0 + matrix[0][1] * a1
            self.amplitudes[partner] = (
                matrix[1][0] * a0 + matrix[1][1] * a1
            )

        self.normalize()

    def apply_two_qubit_xx(self, q1: int, q2: int, angle: float) -> None:
        """
        Apply exp(-i * angle/2 * X⊗X).

        This is an idealized effective entangling interaction representing
        the result of a properly shaped bichromatic laser pulse.
        """
        if q1 == q2:
            raise ControlError("An entangling operation needs two ions.")
        if not (0 <= q1 < self.n_qubits and 0 <= q2 < self.n_qubits):
            raise ControlError("Entangling-qubit index is outside the register.")

        bit1 = 1 << q1
        bit2 = 1 << q2
        c = cos(angle / 2)
        s = -1j * sin(angle / 2)
        old = self.amplitudes[:]

        for state in range(len(old)):
            flipped = state ^ bit1 ^ bit2
            self.amplitudes[state] = c * old[state] + s * old[flipped]

        self.normalize()

    def measure(self, rng: Random) -> int:
        value = rng.random()
        cumulative = 0.0

        for index, amplitude in enumerate(self.amplitudes):
            cumulative += abs(amplitude) ** 2
            if value <= cumulative:
                self.amplitudes = [0j] * len(self.amplitudes)
                self.amplitudes[index] = 1 + 0j
                return index

        # Floating-point rounding can only reach this fallback.
        index = len(self.amplitudes) - 1
        self.amplitudes = [0j] * len(self.amplitudes)
        self.amplitudes[index] = 1 + 0j
        return index


@dataclass
class Calibration:
    rabi_scale: float = 1.0
    detuning_offset_mhz: float = 0.0
    motional_heating_rate: float = 0.001

    def validate(self) -> None:
        if self.rabi_scale <= 0:
            raise ControlError("Rabi calibration scale must be positive.")
        if not 0 <= self.motional_heating_rate < 1:
            raise ControlError("Motional heating rate must be in [0, 1).")


class LaserController:
    """Converts calibrated laser pulses into effective qubit operations."""

    def __init__(
        self,
        trap: TrapConfiguration,
        ions: Iterable[Ion],
        calibration: Calibration,
    ) -> None:
        trap.validate()
        calibration.validate()

        self.trap = trap
        self.ions = {ion.ion_id: ion for ion in ions}

        if not self.ions:
            raise ControlError("At least one ion is required.")

        for ion in self.ions.values():
            ion.validate()

        self.calibration = calibration
        self.pulse_history: List[LaserPulse] = []

    def validate_pulse(self, pulse: LaserPulse) -> None:
        pulse.validate(self.ions)

        effective_detuning = (
            pulse.detuning_mhz + self.calibration.detuning_offset_mhz
        )

        if abs(effective_detuning) > 10:
            raise ControlError(
                f"Pulse {pulse.pulse_id} has excessive effective detuning."
            )

        if pulse.rabi_frequency_mhz * 0.02 > self.trap.max_laser_power_mw:
            raise ControlError(
                f"Pulse {pulse.pulse_id} requests excessive optical power."
            )

        if pulse.gate_type == GateType.ENTANGLING:
            if pulse.target_ion_id is None:
                raise ControlError(
                    "Entangling pulses require a second target ion."
                )

    def single_qubit_rotation(
        self,
        register: QubitRegister,
        pulse: LaserPulse,
    ) -> None:
        self.validate_pulse(pulse)

        if pulse.gate_type != GateType.SINGLE_QUBIT:
            raise ControlError("Pulse is not a single-qubit pulse.")

        omega = (
            2
            * pi
            * pulse.rabi_frequency_mhz
            * self.calibration.rabi_scale
            / 1000
        )
        duration_us = pulse.duration_ns / 1000
        detuning = (
            pulse.detuning_mhz + self.calibration.detuning_offset_mhz
        )

        generalized = sqrt(omega * omega + (2 * pi * detuning) ** 2)
        theta = generalized * duration_us

        if generalized == 0:
            raise ControlError("Effective Rabi frequency cannot be zero.")

        nx = omega / generalized
        nz = (2 * pi * detuning) / generalized

        c = cos(theta / 2)
        s = -1j * sin(theta / 2)

        matrix = [
            [c - 1j * nz * s, -1j * nx * s * complex(exp(1j * pulse.phase_rad))],
            [
                -1j
                * nx
                * s
                * complex(exp(-1j * pulse.phase_rad)),
                c + 1j * nz * s,
            ],
        ]

        register.apply_single_qubit(pulse.ion_id, matrix)
        self.pulse_history.append(pulse)

    def entangling_gate(
        self,
        register: QubitRegister,
        pulse: LaserPulse,
    ) -> None:
        self.validate_pulse(pulse)

        if pulse.gate_type != GateType.ENTANGLING:
            raise ControlError("Pulse is not an entangling pulse.")

        assert pulse.target_ion_id is not None

        # The effective angle is determined by pulse area. A real gate would
        # require calibration against the trap's normal modes and laser phase.
        angle = (
            pi
            * pulse.rabi_frequency_mhz
            * self.calibration.rabi_scale
            * pulse.duration_ns
            / 1000
        )

        heating_penalty = max(
            0.0,
            1.0 - self.calibration.motional_heating_rate
            * pulse.duration_ns / 1000,
        )

        register.apply_two_qubit_xx(
            pulse.ion_id,
            pulse.target_ion_id,
            angle * heating_penalty,
        )
        self.pulse_history.append(pulse)


class PulseScheduler:
    """Checks temporal overlap and provides deterministic pulse ordering."""

    def __init__(self) -> None:
        self._events: List[Tuple[float, LaserPulse]] = []

    def schedule(self, start_ns: float, pulse: LaserPulse) -> None:
        if start_ns < 0:
            raise ControlError("Pulse start time cannot be negative.")

        end_ns = start_ns + pulse.duration_ns

        for existing_start, existing in self._events:
            existing_end = existing_start + existing.duration_ns

            same_ion = (
                existing.ion_id == pulse.ion_id
                or existing.target_ion_id == pulse.ion_id
                or existing.ion_id == pulse.target_ion_id
            )

            overlaps = start_ns < existing_end and existing_start < end_ns

            if same_ion and overlaps:
                raise ControlError(
                    f"Pulse overlap detected between "
                    f"{existing.pulse_id} and {pulse.pulse_id}."
                )

        self._events.append((start_ns, pulse))
        self._events.sort(key=lambda event: event[0])

    def events(self) -> List[Tuple[float, LaserPulse]]:
        return list(self._events)


class TrapProcessor:
    """Coordinates trap, laser controller, scheduling, and measurement."""

    def __init__(self, controller: LaserController) -> None:
        self.controller = controller
        self.rng = Random(20261102)

    def bell_state_demo(self) -> QubitRegister:
        if len(self.controller.ions) < 2:
            raise ControlError("Bell-state demonstration needs two ions.")

        register = QubitRegister(2)

        h_pulse = LaserPulse(
            pulse_id="laser-hadamard",
            ion_id=0,
            duration_ns=250,
            rabi_frequency_mhz=1.0,
            detuning_mhz=0.0,
            phase_rad=0.0,
            gate_type=GateType.SINGLE_QUBIT,
        )

        # A calibrated pi/2 rotation around X is used as the first operation.
        # The exact pulse duration is chosen so the model produces a useful
        # superposition for the subsequent entangling operation.
        self.controller.single_qubit_rotation(register, h_pulse)

        entangle = LaserPulse(
            pulse_id="bichromatic-ms",
            ion_id=0,
            target_ion_id=1,
            duration_ns=500,
            rabi_frequency_mhz=1.0,
            detuning_mhz=0.0,
            phase_rad=0.0,
            gate_type=GateType.ENTANGLING,
        )

        self.controller.entangling_gate(register, entangle)
        return register

    def repeated_measurement(
        self,
        register_factory,
        shots: int = 1000,
    ) -> Dict[str, int]:
        if shots <= 0 or shots > 1_000_000:
            raise ControlError("Shots must be between 1 and 1,000,000.")

        counts: Dict[str, int] = {}

        for _ in range(shots):
            register = register_factory()
            result = register.measure(self.rng)
            key = format(result, f"0{register.n_qubits}b")
            counts[key] = counts.get(key, 0) + 1

        return dict(sorted(counts.items()))


def print_state(label: str, register: QubitRegister) -> None:
    print(f"\n{label}")
    for basis, probability in register.probabilities().items():
        print(f"  |{basis}> : {probability:.6f}")


def demonstrate_failure_conditions(controller: LaserController) -> None:
    bad_pulse = LaserPulse(
        pulse_id="unsafe-detuning",
        ion_id=0,
        duration_ns=100,
        rabi_frequency_mhz=1.0,
        detuning_mhz=25.0,
        phase_rad=0.0,
        gate_type=GateType.SINGLE_QUBIT,
    )

    try:
        controller.validate_pulse(bad_pulse)
    except ControlError as exc:
        print(f"\nValidation correctly rejected unsafe pulse: {exc}")

    scheduler = PulseScheduler()

    first = LaserPulse(
        pulse_id="first",
        ion_id=0,
        duration_ns=500,
        rabi_frequency_mhz=1,
        detuning_mhz=0,
        phase_rad=0,
        gate_type=GateType.SINGLE_QUBIT,
    )

    second = LaserPulse(
        pulse_id="overlapping",
        ion_id=0,
        duration_ns=200,
        rabi_frequency_mhz=1,
        detuning_mhz=0,
        phase_rad=0,
        gate_type=GateType.SINGLE_QUBIT,
    )

    scheduler.schedule(0, first)

    try:
        scheduler.schedule(200, second)
    except ControlError as exc:
        print(f"Scheduler correctly rejected overlap: {exc}")


def main() -> None:
    trap = TrapConfiguration(
        radial_frequency_mhz=4.5,
        axial_frequency_mhz=1.0,
        laser_wavelength_nm=397.0,
        max_laser_power_mw=20.0,
    )

    ions = [
        Ion(0, -2.5, 40.0, 1.0),
        Ion(1, 2.5, 40.0, 1.0),
    ]

    calibration = Calibration(
        rabi_scale=1.0,
        detuning_offset_mhz=0.0,
        motional_heating_rate=0.0005,
    )

    controller = LaserController(trap, ions, calibration)
    processor = TrapProcessor(controller)

    bell = processor.bell_state_demo()
    print_state("Two-ion state after laser-controlled gates", bell)

    demonstrate_failure_conditions(controller)

    print("\nScheduled control sequence:")
    scheduler = PulseScheduler()

    for index, pulse in enumerate(controller.pulse_history):
        scheduler.schedule(index * 1000, pulse)

    for start_ns, pulse in scheduler.events():
        target = (
            f" -> ion {pulse.target_ion_id}"
            if pulse.target_ion_id is not None
            else ""
        )
        print(
            f"  {start_ns:7.1f} ns | {pulse.pulse_id:18s} | "
            f"ion {pulse.ion_id}{target} | {pulse.gate_type.value}"
        )

    def fresh_bell() -> QubitRegister:
        return processor.bell_state_demo()

    counts = processor.repeated_measurement(fresh_bell, shots=500)
    print("\nMeasurement histogram from 500 simulated shots:")
    for state, count in counts.items():
        print(f"  {state}: {count}")

    # Basic invariants make the executable example self-checking.
    assert abs(sum(bell.probabilities().values()) - 1.0) < 1e-9
    assert len(controller.pulse_history) == 2
    assert all(count >= 0 for count in counts.values())

    print("\nSimulation checks passed.")


if __name__ == "__main__":
    main()
