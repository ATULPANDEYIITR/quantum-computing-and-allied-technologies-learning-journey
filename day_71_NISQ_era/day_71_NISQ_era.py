#!/usr/bin/env python3
"""
NISQ Era: Noisy Intermediate-Scale Quantum Computing

A self-contained educational quantum circuit simulator featuring:
- State-vector simulation
- Single-qubit and controlled gates
- Measurement
- Stochastic gate depolarization
- Readout errors
- Shot-based execution
- Circuit validation
- Noise-aware execution analysis
- Reproducible experiments
- JSON result export

Python 3.10+
No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time

from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


EPSILON = 1e-10


class QuantumError(Exception):
    """Base exception for quantum simulation errors."""


class CircuitValidationError(QuantumError):
    """Raised when a quantum circuit is invalid."""


class SimulationError(QuantumError):
    """Raised when quantum simulation fails."""


class GateType(str, Enum):
    H = "H"
    X = "X"
    Y = "Y"
    Z = "Z"
    S = "S"
    T = "T"
    CNOT = "CNOT"
    CZ = "CZ"


@dataclass(frozen=True)
class Gate:
    gate_type: GateType
    targets: tuple[int, ...]

    def __post_init__(self) -> None:
        expected = 2 if self.gate_type in {
            GateType.CNOT, GateType.CZ
        } else 1

        if len(self.targets) != expected:
            raise CircuitValidationError(
                f"{self.gate_type.value} requires {expected} qubit(s)"
            )

        if len(set(self.targets)) != len(self.targets):
            raise CircuitValidationError(
                "A gate cannot target the same qubit twice"
            )


@dataclass
class QuantumCircuit:
    num_qubits: int
    gates: list[Gate] = field(default_factory=list)
    name: str = "quantum-experiment"

    def __post_init__(self) -> None:
        if not isinstance(self.num_qubits, int):
            raise CircuitValidationError("Qubit count must be an integer")

        if not 1 <= self.num_qubits <= 20:
            raise CircuitValidationError(
                "Qubit count must be between 1 and 20"
            )

    def add_gate(self, gate_type: GateType, *targets: int) -> None:
        gate = Gate(gate_type, tuple(targets))

        for target in gate.targets:
            if not 0 <= target < self.num_qubits:
                raise CircuitValidationError(
                    f"Invalid qubit index: {target}"
                )

        self.gates.append(gate)

    def h(self, qubit: int) -> None:
        self.add_gate(GateType.H, qubit)

    def x(self, qubit: int) -> None:
        self.add_gate(GateType.X, qubit)

    def y(self, qubit: int) -> None:
        self.add_gate(GateType.Y, qubit)

    def z(self, qubit: int) -> None:
        self.add_gate(GateType.Z, qubit)

    def s(self, qubit: int) -> None:
        self.add_gate(GateType.S, qubit)

    def t(self, qubit: int) -> None:
        self.add_gate(GateType.T, qubit)

    def cnot(self, control: int, target: int) -> None:
        self.add_gate(GateType.CNOT, control, target)

    def cz(self, control: int, target: int) -> None:
        self.add_gate(GateType.CZ, control, target)

    @property
    def depth(self) -> int:
        """Calculate circuit depth using qubit scheduling."""
        availability = [0] * self.num_qubits

        for gate in self.gates:
            layer = max(
                availability[q] for q in gate.targets
            ) + 1

            for q in gate.targets:
                availability[q] = layer

        return max(availability, default=0)

    def validate(self) -> None:
        if not self.gates:
            raise CircuitValidationError("Circuit contains no gates")

        for gate in self.gates:
            for q in gate.targets:
                if not 0 <= q < self.num_qubits:
                    raise CircuitValidationError(
                        "Circuit contains an invalid qubit index"
                    )


@dataclass(frozen=True)
class NoiseModel:
    single_qubit_error: float = 0.001
    two_qubit_error: float = 0.01
    readout_error: float = 0.02
    relaxation_error: float = 0.001

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1"
                )


@dataclass
class SimulationResult:
    circuit_name: str
    num_qubits: int
    shots: int
    counts: dict[str, int]
    probabilities: dict[str, float]
    circuit_depth: int
    gate_count: int
    execution_seconds: float
    noise_enabled: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StateVectorSimulator:
    """
    State-vector simulator using little-endian qubit indexing.

    Qubit 0 corresponds to the least significant bit.
    The state vector requires O(2^n) complex memory.
    """

    SQRT_HALF = 1 / math.sqrt(2)

    def __init__(
        self,
        circuit: QuantumCircuit,
        noise: NoiseModel | None = None,
        seed: int | None = None,
    ) -> None:
        circuit.validate()

        self.circuit = circuit
        self.noise = noise
        self.rng = random.Random(seed)
        self.dimension = 1 << circuit.num_qubits

    def initial_state(self) -> list[complex]:
        state = [0j] * self.dimension
        state[0] = 1 + 0j
        return state

    def apply_single(
        self,
        state: list[complex],
        qubit: int,
        matrix: tuple[tuple[complex, complex],
                      tuple[complex, complex]],
    ) -> None:
        mask = 1 << qubit

        for base in range(self.dimension):
            if base & mask:
                continue

            other = base | mask
            a = state[base]
            b = state[other]

            state[base] = matrix[0][0] * a + matrix[0][1] * b
            state[other] = matrix[1][0] * a + matrix[1][1] * b

    def apply_cnot(
        self,
        state: list[complex],
        control: int,
        target: int,
    ) -> None:
        control_mask = 1 << control
        target_mask = 1 << target

        for index in range(self.dimension):
            if index & control_mask and not index & target_mask:
                other = index | target_mask
                state[index], state[other] = (
                    state[other], state[index]
                )

    def apply_cz(
        self,
        state: list[complex],
        control: int,
        target: int,
    ) -> None:
        for index in range(self.dimension):
            if (
                index & (1 << control)
                and index & (1 << target)
            ):
                state[index] *= -1

    def apply_gate(
        self,
        state: list[complex],
        gate: Gate,
    ) -> None:
        matrices = {
            GateType.H: (
                (self.SQRT_HALF, self.SQRT_HALF),
                (self.SQRT_HALF, -self.SQRT_HALF),
            ),
            GateType.X: (
                (0j, 1 + 0j),
                (1 + 0j, 0j),
            ),
            GateType.Y: (
                (0j, -1j),
                (1j, 0j),
            ),
            GateType.Z: (
                (1 + 0j, 0j),
                (0j, -1 + 0j),
            ),
            GateType.S: (
                (1 + 0j, 0j),
                (0j, 1j),
            ),
            GateType.T: (
                (1 + 0j, 0j),
                (0j, complex(math.cos(math.pi / 4),
                              math.sin(math.pi / 4))),
            ),
        }

        if gate.gate_type in matrices:
            self.apply_single(
                state,
                gate.targets[0],
                matrices[gate.gate_type],
            )

        elif gate.gate_type == GateType.CNOT:
            self.apply_cnot(state, *gate.targets)

        elif gate.gate_type == GateType.CZ:
            self.apply_cz(state, *gate.targets)

    def apply_stochastic_noise(
        self,
        state: list[complex],
        gate: Gate,
    ) -> None:
        if self.noise is None:
            return

        probability = (
            self.noise.two_qubit_error
            if len(gate.targets) == 2
            else self.noise.single_qubit_error
        )

        if self.rng.random() < probability:
            qubit = self.rng.choice(gate.targets)
            error = self.rng.choice([
                GateType.X, GateType.Y, GateType.Z
            ])

            self.apply_gate(
                state,
                Gate(error, (qubit,)),
            )

        if self.rng.random() < self.noise.relaxation_error:
            qubit = self.rng.choice(gate.targets)

            # Amplitude-damping jump: |1> becomes |0>.
            mask = 1 << qubit

            jump_probability = sum(
                abs(state[i]) ** 2
                for i in range(self.dimension)
                if i & mask
            )

            if jump_probability > EPSILON:
                if self.rng.random() < jump_probability:
                    for i in range(self.dimension):
                        if i & mask:
                            state[i] = 0j

                    norm = math.sqrt(sum(
                        abs(value) ** 2 for value in state
                    ))

                    if norm > EPSILON:
                        state[:] = [
                            value / norm for value in state
                        ]

    def execute(self) -> list[complex]:
        state = self.initial_state()

        for gate in self.circuit.gates:
            self.apply_gate(state, gate)
            self.apply_stochastic_noise(state, gate)

        norm = sum(abs(value) ** 2 for value in state)

        if not math.isclose(norm, 1.0, abs_tol=1e-8):
            raise SimulationError(
                f"State normalization failed: {norm}"
            )

        return state

    def measure(self, state: list[complex]) -> str:
        probabilities = [abs(value) ** 2 for value in state]
        selected = self.rng.random()
        cumulative = 0.0
        outcome = self.dimension - 1

        for index, probability in enumerate(probabilities):
            cumulative += probability

            if selected <= cumulative:
                outcome = index
                break

        result = [
            str((outcome >> q) & 1)
            for q in reversed(range(self.circuit.num_qubits))
        ]

        if self.noise is not None:
            result = [
                str(1 - int(bit))
                if self.rng.random() < self.noise.readout_error
                else bit
                for bit in result
            ]

        return "".join(result)

    def run(self, shots: int = 1000) -> SimulationResult:
        if not 1 <= shots <= 10_000_000:
            raise ValueError("Shots must be between 1 and 10,000,000")

        start = time.perf_counter()
        counts: Counter[str] = Counter()

        for _ in range(shots):
            state = self.execute()
            counts[self.measure(state)] += 1

        elapsed = time.perf_counter() - start

        probabilities = {
            outcome: count / shots
            for outcome, count in sorted(counts.items())
        }

        return SimulationResult(
            circuit_name=self.circuit.name,
            num_qubits=self.circuit.num_qubits,
            shots=shots,
            counts=dict(sorted(counts.items())),
            probabilities=probabilities,
            circuit_depth=self.circuit.depth,
            gate_count=len(self.circuit.gates),
            execution_seconds=elapsed,
            noise_enabled=self.noise is not None,
        )


def bell_circuit() -> QuantumCircuit:
    """Create a two-qubit Bell-state preparation circuit."""
    circuit = QuantumCircuit(2, name="bell-state")
    circuit.h(0)
    circuit.cnot(0, 1)
    return circuit


def ghz_circuit(num_qubits: int = 3) -> QuantumCircuit:
    """Create an n-qubit GHZ preparation circuit."""
    if num_qubits < 2:
        raise ValueError("GHZ states require at least two qubits")

    circuit = QuantumCircuit(num_qubits, name="ghz-state")
    circuit.h(0)

    for target in range(1, num_qubits):
        circuit.cnot(0, target)

    return circuit


def estimate_success_probability(
    circuit: QuantumCircuit,
    noise: NoiseModel,
) -> float:
    """
    Approximate probability of no stochastic gate or readout error.

    This is an analytical estimate, not a fidelity calculation.
    """
    probability = 1.0

    for gate in circuit.gates:
        gate_error = (
            noise.two_qubit_error
            if len(gate.targets) == 2
            else noise.single_qubit_error
        )

        probability *= 1.0 - gate_error

    probability *= (
        1.0 - noise.readout_error
    ) ** circuit.num_qubits

    return probability


def export_result(
    result: SimulationResult,
    output_path: Path,
) -> None:
    """Write results atomically to avoid partially written JSON files."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")

    try:
        temporary.write_text(
            json.dumps(result.to_dict(), indent=2),
            encoding="utf-8",
        )
        temporary.replace(output_path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def print_report(
    result: SimulationResult,
    estimated_success: float | None = None,
) -> None:
    print(f"\nExperiment: {result.circuit_name}")
    print(f"Qubits: {result.num_qubits}")
    print(f"Gates: {result.gate_count}")
    print(f"Depth: {result.circuit_depth}")
    print(f"Shots: {result.shots}")
    print(f"Noise enabled: {result.noise_enabled}")
    print(f"Execution time: {result.execution_seconds:.4f}s")

    print("\nMeasurement distribution:")

    for outcome, probability in result.probabilities.items():
        print(
            f"  {outcome}: {result.counts[outcome]:5d} "
            f"({probability:.4%})"
        )

    if estimated_success is not None:
        print(
            f"\nEstimated no-error probability: "
            f"{estimated_success:.4%}"
        )


def run_self_tests() -> None:
    bell = bell_circuit()
    simulator = StateVectorSimulator(bell, seed=42)
    state = simulator.execute()

    assert math.isclose(abs(state[0]) ** 2, 0.5, abs_tol=1e-8)
    assert math.isclose(abs(state[3]) ** 2, 0.5, abs_tol=1e-8)
    assert math.isclose(abs(state[1]) ** 2, 0.0, abs_tol=1e-8)

    result = simulator.run(2000)
    assert set(result.counts).issubset({"00", "11"})
    assert sum(result.counts.values()) == 2000

    noisy = StateVectorSimulator(
        bell,
        NoiseModel(),
        seed=42,
    ).run(100)

    assert sum(noisy.counts.values()) == 100

    ghz = ghz_circuit(4)
    ghz_result = StateVectorSimulator(
        ghz,
        seed=42,
    ).run(100)

    assert set(ghz_result.counts).issubset({"0000", "1111"})

    try:
        QuantumCircuit(2).add_gate(GateType.CNOT, 0, 0)
        raise AssertionError("Invalid CNOT was accepted")
    except CircuitValidationError:
        pass

    print("All self-tests passed.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NISQ noisy quantum circuit simulator"
    )

    parser.add_argument(
        "--experiment",
        choices=["bell", "ghz"],
        default="bell",
    )
    parser.add_argument("--qubits", type=int, default=3)
    parser.add_argument("--shots", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--noise", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    try:
        if args.test:
            run_self_tests()
            return 0

        if args.experiment == "bell":
            circuit = bell_circuit()
        else:
            circuit = ghz_circuit(args.qubits)

        noise = NoiseModel() if args.noise else None

        simulator = StateVectorSimulator(
            circuit,
            noise=noise,
            seed=args.seed,
        )

        result = simulator.run(args.shots)

        estimate = (
            estimate_success_probability(circuit, noise)
            if noise else None
        )

        print_report(result, estimate)

        if args.output:
            export_result(result, args.output)
            print(f"\nResults saved to {args.output}")

        return 0

    except (QuantumError, ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
