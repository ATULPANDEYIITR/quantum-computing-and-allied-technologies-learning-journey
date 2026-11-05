"""
Spin Qubits in Semiconductor Quantum Systems
---------------------------------------------
Models electron-spin qubits, Bloch-sphere dynamics, magnetic control,
relaxation, dephasing, exchange coupling, gate operations, and fidelity.

Uses only the Python standard library.
"""

from dataclasses import dataclass, field
from enum import Enum
from math import cos, sin, sqrt, pi, exp
from typing import Optional
import json
import statistics


class QubitStateError(Exception):
    """Raised when a quantum state or operation is invalid."""


class GateType(Enum):
    RX = "RX"
    RY = "RY"
    RZ = "RZ"


@dataclass
class Device:
    device_id: str
    material: str
    architecture: str
    electron_count: int
    magnetic_field_t: float
    temperature_mk: float
    coherence_time_us: float
    relaxation_time_us: float
    exchange_coupling_mhz: float

    def validate(self):
        if not self.device_id:
            raise ValueError("Device ID cannot be empty.")
        if self.material not in {"silicon", "germanium", "gaas"}:
            raise ValueError("Unsupported semiconductor material.")
        if self.electron_count < 1:
            raise ValueError("At least one electron is required.")
        if self.magnetic_field_t < 0:
            raise ValueError("Magnetic field cannot be negative.")
        if self.temperature_mk <= 0:
            raise ValueError("Temperature must be positive.")
        if self.coherence_time_us <= 0 or self.relaxation_time_us <= 0:
            raise ValueError("Coherence times must be positive.")
        if self.exchange_coupling_mhz < 0:
            raise ValueError("Exchange coupling cannot be negative.")


@dataclass
class BlochState:
    """Single-qubit density-state representation using a Bloch vector."""

    x: float = 0.0
    y: float = 0.0
    z: float = 1.0

    def validate(self):
        magnitude = self.magnitude()
        if magnitude > 1.0 + 1e-9:
            raise QubitStateError("Bloch vector magnitude exceeds one.")

    def magnitude(self):
        return sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def purity(self):
        return (1.0 + self.magnitude() ** 2) / 2.0

    def probability_zero(self):
        return (1.0 + self.z) / 2.0

    def probability_one(self):
        return (1.0 - self.z) / 2.0

    def as_dict(self):
        return {
            "x": round(self.x, 8),
            "y": round(self.y, 8),
            "z": round(self.z, 8),
            "purity": round(self.purity(), 8),
            "probability_0": round(self.probability_zero(), 8),
            "probability_1": round(self.probability_one(), 8),
        }


@dataclass
class GateResult:
    gate: str
    angle_rad: float
    state: BlochState
    fidelity: float


class SpinQubit:
    """
    Effective two-level electron-spin model.

    The Bloch vector represents a single-qubit state.
    Relaxation and dephasing are applied as a phenomenological
    Markovian approximation.
    """

    def __init__(self, qubit_id: str, device: Device):
        device.validate()
        if not qubit_id:
            raise ValueError("Qubit ID cannot be empty.")

        self.qubit_id = qubit_id
        self.device = device
        self.state = BlochState()
        self.history = []

    def set_state(self, state: BlochState):
        state.validate()
        self.state = BlochState(state.x, state.y, state.z)
        self.history.append(("set_state", self.state.as_dict()))

    def rotate(self, gate: GateType, angle_rad: float):
        if not isinstance(gate, GateType):
            raise ValueError("Unsupported quantum gate.")
        if not isinstance(angle_rad, (int, float)) or not (
            float("-inf") < angle_rad < float("inf")
        ):
            raise ValueError("Rotation angle must be finite.")

        x, y, z = self.state.x, self.state.y, self.state.z
        c = cos(angle_rad)
        s = sin(angle_rad)

        if gate == GateType.RX:
            result = BlochState(x, y * c - z * s, y * s + z * c)
        elif gate == GateType.RY:
            result = BlochState(x * c + z * s, y, -x * s + z * c)
        else:
            result = BlochState(x * c - y * s, x * s + y * c, z)

        result.validate()
        self.state = result
        fidelity = self.state.purity()

        record = GateResult(gate.value, angle_rad, result, fidelity)
        self.history.append((gate.value, record.state.as_dict()))
        return record

    def apply_magnetic_precession(self, duration_us: float):
        """
        Apply free spin precession.

        Angular frequency is calculated from the electron gyromagnetic
        ratio. The effective g-factor is approximated as 2.
        """
        if duration_us < 0:
            raise ValueError("Duration cannot be negative.")

        gamma_rad_per_s_t = 1.76085963023e11
        omega = gamma_rad_per_s_t * self.device.magnetic_field_t

        angle = omega * duration_us * 1e-6
        angle = angle % (2 * pi)

        self.rotate(GateType.RZ, angle)
        return angle

    def apply_relaxation(self, duration_us: float):
        """Apply T1 relaxation toward the ground state."""
        if duration_us < 0:
            raise ValueError("Duration cannot be negative.")

        t1 = self.device.relaxation_time_us
        decay = exp(-duration_us / t1)

        self.state.x *= sqrt(decay)
        self.state.y *= sqrt(decay)
        self.state.z = 1.0 - (1.0 - self.state.z) * decay

        self.state.validate()
        self.history.append(("relaxation", self.state.as_dict()))

    def apply_dephasing(self, duration_us: float):
        """Apply pure transverse dephasing using an effective T2."""
        if duration_us < 0:
            raise ValueError("Duration cannot be negative.")

        t2 = self.device.coherence_time_us
        decay = exp(-duration_us / t2)

        self.state.x *= decay
        self.state.y *= decay

        self.state.validate()
        self.history.append(("dephasing", self.state.as_dict()))

    def evolve(self, duration_us: float):
        """Apply relaxation and pure dephasing over an interval."""
        self.apply_relaxation(duration_us)
        self.apply_dephasing(duration_us)
        return self.state

    def measure(self, shots: int = 1000):
        """
        Simulate computational-basis measurements.

        The binomial result is sampled deterministically through
        expected counts and rounded for a reproducible demonstration.
        """
        if shots <= 0:
            raise ValueError("Shots must be positive.")

        p0 = self.state.probability_zero()
        zeros = round(shots * p0)
        ones = shots - zeros

        result = {
            "qubit_id": self.qubit_id,
            "shots": shots,
            "zero_count": zeros,
            "one_count": ones,
            "estimated_probability_zero": zeros / shots,
            "estimated_probability_one": ones / shots,
        }

        self.history.append(("measurement", result))
        return result


@dataclass
class ExchangePair:
    """
    Two-spin exchange interaction.

    H = J/4 * (sigma_1 . sigma_2)

    The implementation calculates the exchange-induced singlet-triplet
    relative phase. J is expressed as a frequency in MHz.
    """

    coupling_mhz: float

    def __post_init__(self):
        if self.coupling_mhz < 0:
            raise ValueError("Exchange coupling cannot be negative.")

    def relative_phase(self, duration_us: float):
        if duration_us < 0:
            raise ValueError("Duration cannot be negative.")

        return 2 * pi * self.coupling_mhz * duration_us

    def singlet_triplet_phase(self, duration_us: float):
        return self.relative_phase(duration_us)


@dataclass
class Calibration:
    calibration_id: str
    pi_rotation_rad: float
    measured_fidelity: float
    magnetic_field_error_t: float
    temperature_mk: float

    def validate(self):
        if not self.calibration_id:
            raise ValueError("Calibration ID is required.")
        if not 0 <= self.measured_fidelity <= 1:
            raise ValueError("Fidelity must be between zero and one.")
        if self.pi_rotation_rad <= 0:
            raise ValueError("Rotation angle must be positive.")
        if self.magnetic_field_error_t < 0:
            raise ValueError("Field error cannot be negative.")
        if self.temperature_mk <= 0:
            raise ValueError("Temperature must be positive.")


@dataclass
class Experiment:
    experiment_id: str
    device: Device
    qubits: list = field(default_factory=list)
    calibrations: list = field(default_factory=list)

    def add_qubit(self, qubit: SpinQubit):
        if any(q.qubit_id == qubit.qubit_id for q in self.qubits):
            raise ValueError("Duplicate qubit ID.")
        if qubit.device.device_id != self.device.device_id:
            raise ValueError("Qubit belongs to another device.")
        self.qubits.append(qubit)

    def add_calibration(self, calibration: Calibration):
        calibration.validate()
        self.calibrations.append(calibration)

    def calibration_report(self):
        if not self.calibrations:
            return {"status": "UNCALIBRATED"}

        average = statistics.mean(
            item.measured_fidelity for item in self.calibrations
        )

        return {
            "status": "CALIBRATED",
            "calibration_count": len(self.calibrations),
            "average_fidelity": round(average, 6),
            "minimum_fidelity": round(
                min(item.measured_fidelity for item in self.calibrations), 6
            ),
        }


def demonstrate():
    device = Device(
        device_id="SI-QD-001",
        material="silicon",
        architecture="gate-defined quantum dot",
        electron_count=2,
        magnetic_field_t=0.5,
        temperature_mk=20.0,
        coherence_time_us=100.0,
        relaxation_time_us=1000.0,
        exchange_coupling_mhz=5.0,
    )

    experiment = Experiment("SPIN-EXP-001", device)

    qubit = SpinQubit("Q0", device)
    experiment.add_qubit(qubit)

    print("INITIAL STATE")
    print(json.dumps(qubit.state.as_dict(), indent=2))

    print("\nHADAMARD-EQUIVALENT ROTATION")
    qubit.rotate(GateType.RY, pi / 2)
    print(json.dumps(qubit.state.as_dict(), indent=2))

    print("\nMAGNETIC PRECESSION")
    phase = qubit.apply_magnetic_precession(0.001)
    print("Precession angle:", round(phase, 6), "radians")

    print("\nRELAXATION AND DEPHASING")
    qubit.evolve(10.0)
    print(json.dumps(qubit.state.as_dict(), indent=2))

    print("\nMEASUREMENT")
    print(json.dumps(qubit.measure(1000), indent=2))

    print("\nEXCHANGE INTERACTION")
    exchange = ExchangePair(device.exchange_coupling_mhz)
    print(
        "Relative phase:",
        round(exchange.singlet_triplet_phase(0.05), 6),
        "radians",
    )

    calibration = Calibration(
        calibration_id="CAL-001",
        pi_rotation_rad=pi,
        measured_fidelity=0.995,
        magnetic_field_error_t=0.0001,
        temperature_mk=20.0,
    )
    experiment.add_calibration(calibration)

    print("\nCALIBRATION REPORT")
    print(json.dumps(experiment.calibration_report(), indent=2))

    print("\nEXPERIMENT HISTORY")
    print("Recorded events:", len(qubit.history))


if __name__ == "__main__":
    demonstrate()
