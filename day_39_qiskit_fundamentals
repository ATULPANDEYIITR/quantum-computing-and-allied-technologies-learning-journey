#!/usr/bin/env python3
"""
Qiskit Fundamentals: Installation and First Circuit

A self-contained educational program that introduces Qiskit through
environment validation, circuit construction, quantum-state inspection,
measurement, simulation, statistical analysis, and reproducible experiments.

Installation:
    python -m pip install qiskit qiskit-aer

Execution:
    python qiskit_fundamentals.py

The program uses Qiskit and Aer when available. If Qiskit is absent,
it reports the installation instructions and runs a small standard-library
quantum-state simulator so the mathematical fundamentals remain executable.
"""

from __future__ import annotations

import importlib.metadata
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any, Sequence


def print_title(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def validate_positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def inspect_installation() -> bool:
    """Check installed package metadata without assuming an Aer backend exists."""
    print_title("Qiskit environment")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")

    for package in ("qiskit", "qiskit-aer"):
        try:
            print(f"{package}: {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            print(f"{package}: not installed")

    try:
        import qiskit  # noqa: F401
        from qiskit import QuantumCircuit  # noqa: F401
        return True
    except ImportError:
        print("\nInstall the quantum-computing packages with:")
        print("  python -m pip install qiskit qiskit-aer")
        return False


@dataclass(frozen=True)
class MeasurementResult:
    counts: dict[str, int]
    shots: int

    def probabilities(self) -> dict[str, float]:
        return {
            outcome: count / self.shots
            for outcome, count in sorted(self.counts.items())
        }

    def assert_valid(self) -> None:
        validate_positive_integer(self.shots, "shots")
        if sum(self.counts.values()) != self.shots:
            raise ValueError("Measurement counts must sum to the shot count.")
        if any(count < 0 for count in self.counts.values()):
            raise ValueError("Measurement counts cannot be negative.")


def print_counts(result: MeasurementResult) -> None:
    result.assert_valid()
    print(f"Shots: {result.shots}")
    for outcome, probability in result.probabilities().items():
        print(
            f"  {outcome}: {result.counts[outcome]:5d} "
            f"({probability:.3%})"
        )


def run_qiskit_examples() -> None:
    """Build and execute circuits using the public Qiskit circuit API."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise RuntimeError(
            "Qiskit is installed, but Qiskit Aer is missing. "
            "Run: python -m pip install qiskit-aer"
        ) from exc

    print_title("Constructing the first quantum circuit")

    # A quantum circuit is a sequence of operations on quantum and classical bits.
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    print(circuit.draw(output="text"))

    # Remove measurements to inspect the quantum state before collapse.
    state_circuit = QuantumCircuit(1)
    state_circuit.h(0)
    state = Statevector.from_instruction(state_circuit)
    print(f"State after H: {state.data}")
    print(f"Probabilities: {state.probabilities_dict()}")

    simulator = AerSimulator()
    compiled = simulator.run(circuit, shots=4096, seed_simulator=42).result()
    counts = compiled.get_counts(circuit)
    result = MeasurementResult(dict(counts), 4096)

    print_title("Hadamard measurement experiment")
    print_counts(result)

    # The Hadamard gate produces equal probabilities for zero and one.
    # Finite samples fluctuate, so the assertion checks a statistical tolerance.
    p_one = result.counts.get("1", 0) / result.shots
    if abs(p_one - 0.5) > 0.06:
        raise AssertionError("Unexpected Hadamard measurement distribution.")

    print("\nCreating a deterministic circuit.")
    deterministic = QuantumCircuit(1, 1)
    deterministic.x(0)
    deterministic.measure(0, 0)
    deterministic_counts = simulator.run(
        deterministic, shots=128, seed_simulator=42
    ).result().get_counts(deterministic)
    print_counts(MeasurementResult(dict(deterministic_counts), 128))

    print_title("A two-qubit entanglement experiment")
    bell = QuantumCircuit(2, 2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure([0, 1], [0, 1])

    print(bell.draw(output="text"))
    bell_counts = simulator.run(
        bell, shots=2048, seed_simulator=17
    ).result().get_counts(bell)
    bell_result = MeasurementResult(dict(bell_counts), 2048)
    print_counts(bell_result)

    # Qiskit displays classical bit strings with the highest-index bit on the left.
    unexpected = set(bell_counts) - {"00", "11"}
    if unexpected:
        raise AssertionError(f"Unexpected Bell-state outcomes: {unexpected}")

    print("\nQiskit experiments completed successfully.")


def apply_single_qubit_gate(
    state: list[complex],
    qubit_count: int,
    target: int,
    matrix: Sequence[Sequence[complex]],
) -> list[complex]:
    """
    Apply a one-qubit matrix to a statevector.

    Basis index bit target represents qubit target. Qubit zero is the
    least-significant bit, matching Qiskit's statevector convention.
    """
    if not 0 <= target < qubit_count:
        raise ValueError("Target qubit is outside the circuit.")

    dimension = 1 << qubit_count
    if len(state) != dimension:
        raise ValueError("Statevector dimension does not match qubit count.")

    result = state.copy()
    bit = 1 << target

    for index in range(dimension):
        if index & bit:
            continue

        paired = index | bit
        amplitude_zero = state[index]
        amplitude_one = state[paired]

        result[index] = (
            matrix[0][0] * amplitude_zero
            + matrix[0][1] * amplitude_one
        )
        result[paired] = (
            matrix[1][0] * amplitude_zero
            + matrix[1][1] * amplitude_one
        )

    return result


def apply_cnot(
    state: list[complex],
    control: int,
    target: int,
    qubit_count: int,
) -> list[complex]:
    """Apply controlled-X using explicit computational-basis index mapping."""
    if control == target:
        raise ValueError("Control and target qubits must differ.")
    if not (0 <= control < qubit_count and 0 <= target < qubit_count):
        raise ValueError("Control or target qubit is outside the circuit.")

    result = [0j] * len(state)
    control_mask = 1 << control
    target_mask = 1 << target

    for index, amplitude in enumerate(state):
        destination = index
        if index & control_mask:
            destination ^= target_mask
        result[destination] = amplitude

    return result


def validate_statevector(state: Sequence[complex]) -> None:
    """Check the normalization condition for a valid pure quantum state."""
    norm_squared = sum(abs(amplitude) ** 2 for amplitude in state)
    if not math.isclose(norm_squared, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"Statevector is not normalized: norm²={norm_squared}")


def sample_measurements(
    state: Sequence[complex],
    qubit_count: int,
    shots: int,
    seed: int = 42,
) -> MeasurementResult:
    """Sample computational-basis outcomes from statevector probabilities."""
    validate_positive_integer(shots, "shots")
    validate_statevector(state)

    if len(state) != 1 << qubit_count:
        raise ValueError("Statevector dimension does not match qubit count.")

    probabilities = [abs(amplitude) ** 2 for amplitude in state]
    generator = random.Random(seed)
    cumulative: list[float] = []
    running = 0.0

    for probability in probabilities:
        running += probability
        cumulative.append(running)

    counts: Counter[str] = Counter()
    for _ in range(shots):
        sample = generator.random()
        outcome_index = next(
            (
                index
                for index, threshold in enumerate(cumulative)
                if sample < threshold
            ),
            len(cumulative) - 1,
        )
        counts[format(outcome_index, f"0{qubit_count}b")] += 1

    result = MeasurementResult(dict(counts), shots)
    result.assert_valid()
    return result


def run_standard_library_simulator() -> None:
    """Teach statevector mechanics without requiring external packages."""
    print_title("Standard-library quantum statevector simulator")

    inv_sqrt_two = 1 / math.sqrt(2)
    hadamard = (
        (inv_sqrt_two, inv_sqrt_two),
        (inv_sqrt_two, -inv_sqrt_two),
    )

    zero_state = [1 + 0j, 0j]
    superposition = apply_single_qubit_gate(
        zero_state, 1, 0, hadamard
    )
    validate_statevector(superposition)

    print("Initial state |0>: ", zero_state)
    print("After Hadamard:    ", superposition)
    print_counts(sample_measurements(superposition, 1, 2048))

    # Build the Bell state: H on qubit zero followed by CNOT(0, 1).
    two_qubit_zero = [1 + 0j, 0j, 0j, 0j]
    first_gate = apply_single_qubit_gate(
        two_qubit_zero, 2, 0, hadamard
    )
    bell_state = apply_cnot(first_gate, 0, 1, 2)
    validate_statevector(bell_state)

    print("\nBell state amplitudes in index order |00>, |01>, |10>, |11>:")
    for index, amplitude in enumerate(bell_state):
        print(f"  |{index:02b}>: {amplitude}")

    print_counts(sample_measurements(bell_state, 2, 2048, seed=17))

    # A zero-probability outcome must never be sampled.
    x_matrix = ((0, 1), (1, 0))
    one_state = apply_single_qubit_gate(zero_state, 1, 0, x_matrix)
    deterministic = sample_measurements(one_state, 1, 64)
    if deterministic.counts != {"1": 64}:
        raise AssertionError("X gate failed its deterministic test.")

    print("\nSimulator validation passed.")


def demonstrate_common_errors() -> None:
    print_title("Validation and common errors")

    for invalid_shots in (0, -1, True):
        try:
            validate_positive_integer(invalid_shots, "shots")
        except ValueError as exc:
            print(f"Rejected invalid shot count {invalid_shots!r}: {exc}")

    try:
        apply_cnot([1 + 0j, 0j], 0, 0, 1)
    except ValueError as exc:
        print(f"Rejected invalid CNOT: {exc}")

    try:
        validate_statevector([1 + 0j, 1 + 0j])
    except ValueError as exc:
        print(f"Rejected unnormalized state: {exc}")

    print(
        "A circuit containing measurements should not be treated as an "
        "unmeasured state preparation when inspecting amplitudes."
    )


def main() -> None:
    if inspect_installation():
        try:
            run_qiskit_examples()
        except (ImportError, RuntimeError) as exc:
            print(f"\nQiskit execution unavailable: {exc}")
            print("Running the standard-library simulator instead.")
            run_standard_library_simulator()
    else:
        run_standard_library_simulator()

    demonstrate_common_errors()


if __name__ == "__main__":
    main()
