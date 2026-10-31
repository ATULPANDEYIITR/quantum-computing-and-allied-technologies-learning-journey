from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import pi
from pathlib import Path
from statistics import mean
from typing import Iterable


class QubitTechnology(Enum):
    SUPERCONDUCTING = "superconducting"
    TRAPPED_ION = "trapped_ion"
    NEUTRAL_ATOM = "neutral_atom"
    PHOTONIC = "photonic"
    SPIN = "spin"


class ControlLayer(Enum):
    CRYOGENICS = "cryogenics"
    VACUUM = "vacuum"
    OPTICAL = "optical"
    MICROWAVE = "microwave"
    ELECTRONICS = "electronics"
    SOFTWARE = "software"


@dataclass(frozen=True)
class Qubit:
    identifier: int
    technology: QubitTechnology
    frequency_ghz: float
    coherence_us: float
    gate_fidelity: float
    readout_fidelity: float

    def validate(self) -> None:
        if self.identifier < 0:
            raise ValueError("Qubit identifier cannot be negative")
        if self.frequency_ghz <= 0:
            raise ValueError("Qubit frequency must be positive")
        if self.coherence_us <= 0:
            raise ValueError("Coherence time must be positive")
        if not 0 < self.gate_fidelity <= 1:
            raise ValueError("Gate fidelity must be in (0, 1]")
        if not 0 < self.readout_fidelity <= 1:
            raise ValueError("Readout fidelity must be in (0, 1]")


@dataclass
class HardwareLayer:
    name: str
    purpose: str
    components: list[str] = field(default_factory=list)
    operating_constraints: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Hardware layer requires a name")
        if not self.components:
            raise ValueError(f"{self.name} must contain at least one component")


@dataclass
class Gate:
    name: str
    duration_ns: float
    error_rate: float

    def validate(self) -> None:
        if self.duration_ns <= 0:
            raise ValueError("Gate duration must be positive")
        if not 0 <= self.error_rate < 1:
            raise ValueError("Gate error rate must be in [0, 1)")


@dataclass
class QuantumDevice:
    name: str
    technology: QubitTechnology
    qubits: list[Qubit]
    layers: list[HardwareLayer]
    gates: list[Gate]

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Device name is required")
        if not self.qubits:
            raise ValueError("Device must contain qubits")

        identifiers = set()
        for qubit in self.qubits:
            qubit.validate()
            if qubit.identifier in identifiers:
                raise ValueError("Duplicate qubit identifier")
            identifiers.add(qubit.identifier)

        for layer in self.layers:
            layer.validate()

        for gate in self.gates:
            gate.validate()

    @property
    def average_gate_fidelity(self) -> float:
        return mean(1.0 - gate.error_rate for gate in self.gates)

    @property
    def average_coherence_us(self) -> float:
        return mean(qubit.coherence_us for qubit in self.qubits)

    @property
    def average_readout_fidelity(self) -> float:
        return mean(qubit.readout_fidelity for qubit in self.qubits)

    def estimated_depth_budget(self, gate_duration_ns: float | None = None) -> int:
        """
        Approximate how many sequential gates can execute before the
        average coherence time is consumed.
        """
        if gate_duration_ns is None:
            gate_duration_ns = mean(g.duration_ns for g in self.gates)

        if gate_duration_ns <= 0:
            raise ValueError("Gate duration must be positive")

        coherence_ns = self.average_coherence_us * 1_000.0
        return max(0, int(coherence_ns // gate_duration_ns))


class HardwareBuilder:
    @staticmethod
    def superconducting_example() -> QuantumDevice:
        qubits = [
            Qubit(i, QubitTechnology.SUPERCONDUCTING, 5.0 + i * 0.035,
                  85.0 - i * 1.5, 0.9991, 0.985)
            for i in range(8)
        ]

        layers = [
            HardwareLayer(
                "Cryogenic layer",
                "Maintains the quantum processor at millikelvin temperatures.",
                ["dilution refrigerator", "mixing chamber", "thermal stages"],
                ["heat load", "vibration", "thermalization"]
            ),
            HardwareLayer(
                "Microwave control",
                "Generates calibrated pulses for qubit control.",
                ["microwave sources", "attenuators", "IQ mixers", "filters"],
                ["phase noise", "pulse distortion", "crosstalk"]
            ),
            HardwareLayer(
                "Readout",
                "Maps quantum states into classical measurement signals.",
                ["readout resonators", "amplifiers", "digitizers"],
                ["amplifier noise", "measurement fidelity"]
            ),
            HardwareLayer(
                "Classical control",
                "Coordinates timing, calibration, feedback, and data capture.",
                ["FPGA controller", "control software", "calibration database"],
                ["latency", "clock synchronization"]
            ),
        ]

        gates = [
            Gate("single-qubit microwave gate", 25.0, 0.0009),
            Gate("two-qubit entangling gate", 220.0, 0.008),
            Gate("measurement", 700.0, 0.015),
        ]

        return QuantumDevice(
            "Cryogenic superconducting processor",
            QubitTechnology.SUPERCONDUCTING,
            qubits,
            layers,
            gates,
        )

    @staticmethod
    def trapped_ion_example() -> QuantumDevice:
        qubits = [
            Qubit(i, QubitTechnology.TRAPPED_ION, 0.0,
                  1_000_000.0, 0.9995, 0.997)
            for i in range(4)
        ]

        layers = [
            HardwareLayer(
                "Ultra-high vacuum",
                "Keeps ions isolated from collisions with background gas.",
                ["vacuum chamber", "ion pumps", "pressure monitoring"],
                ["pressure", "surface charging"]
            ),
            HardwareLayer(
                "Optical control",
                "Traps, cools, manipulates, and measures ions.",
                ["lasers", "optics", "beam steering", "photodetectors"],
                ["laser stability", "beam alignment"]
            ),
            HardwareLayer(
                "RF trapping",
                "Creates electromagnetic potentials that confine ions.",
                ["RF electrodes", "RF source", "amplifier"],
                ["field stability", "heating"]
            ),
        ]

        gates = [
            Gate("laser single-qubit gate", 1_000.0, 0.0005),
            Gate("entangling gate", 100_000.0, 0.003),
            Gate("fluorescence measurement", 200_000.0, 0.003),
        ]

        return QuantumDevice(
            "Trapped-ion processor",
            QubitTechnology.TRAPPED_ION,
            qubits,
            layers,
            gates,
        )


@dataclass
class CoolingBudget:
    input_power_w: float
    thermal_load_mw: float
    available_cooling_mw: float

    def utilization(self) -> float:
        if self.available_cooling_mw <= 0:
            raise ValueError("Available cooling capacity must be positive")
        return self.thermal_load_mw / self.available_cooling_mw

    def validate(self) -> None:
        if self.input_power_w < 0:
            raise ValueError("Input power cannot be negative")
        if self.thermal_load_mw < 0:
            raise ValueError("Thermal load cannot be negative")
        if self.available_cooling_mw <= 0:
            raise ValueError("Cooling capacity must be positive")


@dataclass
class ControlSignal:
    channel: int
    amplitude: float
    phase_rad: float
    duration_ns: float

    def validate(self) -> None:
        if self.channel < 0:
            raise ValueError("Channel cannot be negative")
        if not -1 <= self.amplitude <= 1:
            raise ValueError("Normalized amplitude must be between -1 and 1")
        if not 0 <= self.phase_rad < 2 * pi:
            raise ValueError("Phase must be in [0, 2*pi)")
        if self.duration_ns <= 0:
            raise ValueError("Duration must be positive")


def build_control_sequence(qubit_count: int) -> list[ControlSignal]:
    if qubit_count <= 0:
        raise ValueError("Qubit count must be positive")

    sequence = []
    for channel in range(qubit_count):
        signal = ControlSignal(
            channel=channel,
            amplitude=0.45,
            phase_rad=(channel * pi / 4) % (2 * pi),
            duration_ns=25.0,
        )
        signal.validate()
        sequence.append(signal)

    return sequence


def validate_device_for_operation(device: QuantumDevice) -> dict[str, object]:
    device.validate()

    return {
        "device": device.name,
        "technology": device.technology.value,
        "qubits": len(device.qubits),
        "average_coherence_us": round(device.average_coherence_us, 2),
        "average_gate_fidelity": round(device.average_gate_fidelity, 6),
        "average_readout_fidelity": round(device.average_readout_fidelity, 6),
        "estimated_sequential_gate_budget": device.estimated_depth_budget(),
    }


def write_hardware_report(device: QuantumDevice, path: Path) -> None:
    report = validate_device_for_operation(device)
    lines = [
        "QUANTUM HARDWARE ENGINEERING REPORT",
        "=" * 40,
        f"Device: {report['device']}",
        f"Technology: {report['technology']}",
        f"Qubits: {report['qubits']}",
        f"Average coherence: {report['average_coherence_us']} us",
        f"Average gate fidelity: {report['average_gate_fidelity']}",
        f"Average readout fidelity: {report['average_readout_fidelity']}",
        f"Estimated sequential gate budget: {report['estimated_sequential_gate_budget']}",
        "",
        "Hardware layers:",
    ]

    for layer in device.layers:
        lines.append(f"- {layer.name}: {layer.purpose}")
        lines.append(f"  Components: {', '.join(layer.components)}")
        lines.append(f"  Constraints: {', '.join(layer.operating_constraints)}")

    path.write_text("\n".join(lines), encoding="utf-8")


def run_self_tests() -> None:
    device = HardwareBuilder.superconducting_example()
    device.validate()

    assert len(device.qubits) == 8
    assert device.average_gate_fidelity > 0.98
    assert device.estimated_depth_budget() > 0

    cooling = CoolingBudget(
        input_power_w=2.0,
        thermal_load_mw=0.65,
        available_cooling_mw=1.2,
    )
    cooling.validate()
    assert cooling.utilization() < 1.0

    sequence = build_control_sequence(len(device.qubits))
    assert len(sequence) == len(device.qubits)

    try:
        Qubit(0, QubitTechnology.SUPERCONDUCTING, -1, 10, 0.99, 0.99).validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid frequency was accepted")

    ion_device = HardwareBuilder.trapped_ion_example()
    ion_device.validate()
    assert ion_device.technology is QubitTechnology.TRAPPED_ION


def main() -> None:
    run_self_tests()

    devices = [
        HardwareBuilder.superconducting_example(),
        HardwareBuilder.trapped_ion_example(),
    ]

    for device in devices:
        report = validate_device_for_operation(device)
        print("\n" + "=" * 55)
        print(report["device"])
        print("=" * 55)
        for key, value in report.items():
            print(f"{key}: {value}")

    cooling = CoolingBudget(2.0, 0.65, 1.2)
    print(f"\nCryogenic cooling utilization: {cooling.utilization():.1%}")

    output = Path("quantum_hardware_report.txt")
    write_hardware_report(devices[0], output)
    print(f"Report written to: {output.resolve()}")


if __name__ == "__main__":
    main()
