#!/usr/bin/env python3
"""
QFT Implementation: Build QFT circuits.

Self-contained implementation of the Quantum Fourier Transform using
state-vector simulation. The script builds QFT circuits, applies them to
quantum states, verifies unitarity and inverse behavior, demonstrates
phase-kickback structure, and compares the direct QFT with a circuit
decomposition using Hadamard and controlled-phase gates.

No external dependencies are required.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Iterable, Sequence


EPSILON = 1e-10


@dataclass(frozen=True)
class GateOperation:
    """A gate operation in a circuit description."""

    name: str
    target: int
    control: int | None = None
    angle: float | None = None


class QuantumState:
    """Minimal state-vector representation for n qubits."""

    def __init__(self, amplitudes: Sequence[complex]):
        values = [complex(value) for value in amplitudes]

        if not values:
            raise ValueError("A quantum state cannot be empty.")

        dimension = len(values)
        if dimension & (dimension - 1):
            raise ValueError("State dimension must be a power of two.")

        norm = math.sqrt(sum(abs(value) ** 2 for value in values))
        if norm < EPSILON:
            raise ValueError("Quantum state cannot have zero norm.")

        self.amplitudes = [value / norm for value in values]

    @property
    def dimension(self) -> int:
        return len(self.amplitudes)

    @property
    def num_qubits(self) -> int:
        return int(math.log2(self.dimension))

    def probability(self, basis_index: int) -> float:
        if not 0 <= basis_index < self.dimension:
            raise IndexError("Basis index is outside the state space.")
        return abs(self.amplitudes[basis_index]) ** 2

    def probabilities(self) -> list[float]:
        return [abs(value) ** 2 for value in self.amplitudes]

    def copy(self) -> "QuantumState":
        return QuantumState(self.amplitudes)

    @classmethod
    def basis(cls, num_qubits: int, index: int) -> "QuantumState":
        if num_qubits < 1:
            raise ValueError("The number of qubits must be positive.")

        dimension = 2**num_qubits
        if not 0 <= index < dimension:
            raise ValueError("Basis index is outside the state space.")

        amplitudes = [0j] * dimension
        amplitudes[index] = 1 + 0j
        return cls(amplitudes)


class QFTCircuit:
    """
    QFT circuit using the standard decomposition:

        H(q)
        controlled-R_k(q, control)

    followed by bit reversal.

    Qubit 0 is the least-significant bit in the computational basis index.
    """

    def __init__(self, num_qubits: int):
        if num_qubits < 1:
            raise ValueError("QFT requires at least one qubit.")
        self.num_qubits = num_qubits
        self.operations: list[GateOperation] = []
        self._build()

    def _build(self) -> None:
        for target in range(self.num_qubits):
            self.operations.append(GateOperation("H", target))

            for control in range(target + 1, self.num_qubits):
                distance = control - target
                angle = math.pi / (2**distance)
                self.operations.append(
                    GateOperation(
                        "CR",
                        target=target,
                        control=control,
                        angle=angle,
                    )
                )

        for left in range(self.num_qubits // 2):
            right = self.num_qubits - 1 - left
            self.operations.append(
                GateOperation("SWAP", target=left, control=right)
            )

    def inverse(self) -> "InverseQFTCircuit":
        return InverseQFTCircuit(self)

    def apply(self, state: QuantumState) -> QuantumState:
        self._validate_state(state)
        result = state.copy()

        for operation in self.operations:
            if operation.name == "H":
                apply_hadamard(result.amplitudes, operation.target)
            elif operation.name == "CR":
                apply_controlled_phase(
                    result.amplitudes,
                    operation.control,
                    operation.target,
                    operation.angle,
                )
            elif operation.name == "SWAP":
                apply_swap(
                    result.amplitudes,
                    operation.target,
                    operation.control,
                )
            else:
                raise RuntimeError(f"Unsupported gate: {operation.name}")

        return QuantumState(result.amplitudes)

    def matrix(self) -> list[list[complex]]:
        dimension = 2**self.num_qubits
        matrix = []

        for column in range(dimension):
            state = QuantumState.basis(self.num_qubits, column)
            transformed = self.apply(state)
            matrix.append(transformed.amplitudes)

        return [
            [matrix[column][row] for column in range(dimension)]
            for row in range(dimension)
        ]

    def draw(self) -> str:
        lines = [f"QFT circuit with {self.num_qubits} qubits:"]
        for index, operation in enumerate(self.operations, start=1):
            if operation.name == "H":
                lines.append(f"{index:02d}. H(q{operation.target})")
            elif operation.name == "CR":
                lines.append(
                    f"{index:02d}. CR(q{operation.control}, "
                    f"q{operation.target}, angle={operation.angle:.8f})"
                )
            elif operation.name == "SWAP":
                lines.append(
                    f"{index:02d}. SWAP(q{operation.target}, q{operation.control})"
                )
        return "\n".join(lines)

    def _validate_state(self, state: QuantumState) -> None:
        if state.num_qubits != self.num_qubits:
            raise ValueError(
                f"QFT expects {self.num_qubits} qubits, "
                f"received {state.num_qubits}."
            )


class InverseQFTCircuit:
    """Inverse of a QFT decomposition."""

    def __init__(self, qft: QFTCircuit):
        self.num_qubits = qft.num_qubits
        self.operations = self._invert(qft.operations)

    @staticmethod
    def _invert(operations: Sequence[GateOperation]) -> list[GateOperation]:
        inverted: list[GateOperation] = []

        for operation in reversed(operations):
            if operation.name == "H":
                inverted.append(operation)
            elif operation.name == "CR":
                inverted.append(
                    GateOperation(
                        "CR",
                        target=operation.target,
                        control=operation.control,
                        angle=-operation.angle,
                    )
                )
            elif operation.name == "SWAP":
                inverted.append(operation)
            else:
                raise RuntimeError(f"Unsupported gate: {operation.name}")

        return inverted

    def apply(self, state: QuantumState) -> QuantumState:
        if state.num_qubits != self.num_qubits:
            raise ValueError("State and circuit qubit counts do not match.")

        result = state.copy()

        for operation in self.operations:
            if operation.name == "H":
                apply_hadamard(result.amplitudes, operation.target)
            elif operation.name == "CR":
                apply_controlled_phase(
                    result.amplitudes,
                    operation.control,
                    operation.target,
                    operation.angle,
                )
            elif operation.name == "SWAP":
                apply_swap(
                    result.amplitudes,
                    operation.target,
                    operation.control,
                )

        return QuantumState(result.amplitudes)


def apply_hadamard(amplitudes: list[complex], target: int) -> None:
    """Apply H independently to every pair differing only at target."""
    mask = 1 << target
    scale = 1 / math.sqrt(2)

    for base in range(0, len(amplitudes), 2 * mask):
        for offset in range(mask):
            i = base + offset
            j = i + mask
            a = amplitudes[i]
            b = amplitudes[j]
            amplitudes[i] = (a + b) * scale
            amplitudes[j] = (a - b) * scale


def apply_controlled_phase(
    amplitudes: list[complex],
    control: int,
    target: int,
    angle: float,
) -> None:
    """
    Apply a phase e^(i*angle) when both control and target are |1>.
    """
    if control is None:
        raise ValueError("Controlled phase requires a control qubit.")

    control_mask = 1 << control
    target_mask = 1 << target
    phase = cmath.exp(1j * angle)

    for index in range(len(amplitudes)):
        if index & control_mask and index & target_mask:
            amplitudes[index] *= phase


def apply_swap(
    amplitudes: list[complex],
    first: int,
    second: int,
) -> None:
    """Swap two qubit positions in every computational-basis amplitude."""
    if first == second:
        return

    first_mask = 1 << first
    second_mask = 1 << second

    for index in range(len(amplitudes)):
        first_bit = bool(index & first_mask)
        second_bit = bool(index & second_mask)

        if first_bit != second_bit:
            swapped = index ^ first_mask ^ second_mask

            if index < swapped:
                amplitudes[index], amplitudes[swapped] = (
                    amplitudes[swapped],
                    amplitudes[index],
                )


def direct_qft(amplitudes: Sequence[complex]) -> list[complex]:
    """
    Direct O(N^2) QFT definition:

        y_k = 1/sqrt(N) * sum_x x_x exp(2*pi*i*x*k/N)
    """
    values = [complex(value) for value in amplitudes]
    dimension = len(values)

    if dimension == 0 or dimension & (dimension - 1):
        raise ValueError("Input dimension must be a non-zero power of two.")

    norm = math.sqrt(sum(abs(value) ** 2 for value in values))
    if abs(norm - 1.0) > EPSILON:
        values = [value / norm for value in values]

    scale = 1 / math.sqrt(dimension)
    result = []

    for k in range(dimension):
        total = 0j
        for x in range(dimension):
            angle = 2 * math.pi * x * k / dimension
            total += values[x] * cmath.exp(1j * angle)
        result.append(scale * total)

    return result


def inverse_direct_qft(amplitudes: Sequence[complex]) -> list[complex]:
    """Direct inverse QFT using the negative Fourier phase."""
    values = [complex(value) for value in amplitudes]
    dimension = len(values)

    if dimension == 0 or dimension & (dimension - 1):
        raise ValueError("Input dimension must be a non-zero power of two.")

    scale = 1 / math.sqrt(dimension)
    return [
        scale
        * sum(
            values[x]
            * cmath.exp(-2j * math.pi * x * k / dimension)
            for x in range(dimension)
        )
        for k in range(dimension)
    ]


def pretty_state(state: QuantumState, threshold: float = 1e-8) -> str:
    """Display only amplitudes that are numerically significant."""
    terms = []

    for index, amplitude in enumerate(state.amplitudes):
        if abs(amplitude) <= threshold:
            continue

        real = amplitude.real
        imaginary = amplitude.imag

        if abs(real) < threshold:
            real = 0.0
        if abs(imaginary) < threshold:
            imaginary = 0.0

        terms.append(
            f"|{index:0{state.num_qubits}b}>: "
            f"{real:.6f}{imaginary:+.6f}i "
            f"(p={abs(amplitude) ** 2:.6f})"
        )

    return "\n".join(terms) if terms else "zero state"


def max_difference(
    first: Sequence[complex],
    second: Sequence[complex],
) -> float:
    if len(first) != len(second):
        raise ValueError("Vectors must have the same dimension.")
    return max(
        (abs(a - b) for a, b in zip(first, second)),
        default=0.0,
    )


def verify_unitarity(matrix: Sequence[Sequence[complex]]) -> float:
    """Return the largest deviation from U†U = I."""
    dimension = len(matrix)
    maximum_error = 0.0

    for row in range(dimension):
        for column in range(dimension):
            value = sum(
                matrix[k][row].conjugate() * matrix[k][column]
                for k in range(dimension)
            )
            expected = 1.0 if row == column else 0.0
            maximum_error = max(maximum_error, abs(value - expected))

    return maximum_error


def run_demo(num_qubits: int = 3) -> None:
    qft = QFTCircuit(num_qubits)

    print(qft.draw())
    print()

    input_state = QuantumState.basis(num_qubits, 3)
    transformed = qft.apply(input_state)

    print("Input computational-basis state:")
    print(pretty_state(input_state))
    print()

    print("QFT result:")
    print(pretty_state(transformed))
    print()

    direct = direct_qft(input_state.amplitudes)
    print(
        "Circuit-vs-direct QFT maximum amplitude error:",
        f"{max_difference(transformed.amplitudes, direct):.3e}",
    )

    recovered = qft.inverse().apply(transformed)
    print(
        "QFT followed by inverse-QFT maximum recovery error:",
        f"{max_difference(recovered.amplitudes, input_state.amplitudes):.3e}",
    )

    unitary_error = verify_unitarity(qft.matrix())
    print(f"QFT unitarity error: {unitary_error:.3e}")

    print()
    print("Uniform superposition example:")
    uniform = QuantumState([1 / math.sqrt(2**num_qubits)] * (2**num_qubits))
    uniform_qft = qft.apply(uniform)
    print(pretty_state(uniform_qft))

    print()
    print("Complex phase example:")
    phase_state = QuantumState(
        [
            cmath.exp(2j * math.pi * index / 2**num_qubits)
            / math.sqrt(2**num_qubits)
            for index in range(2**num_qubits)
        ]
    )
    phase_result = qft.apply(phase_state)
    print(pretty_state(phase_result))


def run_validation() -> None:
    """Exercise edge cases and correctness properties."""
    for qubits in range(1, 5):
        qft = QFTCircuit(qubits)
        dimension = 2**qubits

        for basis_index in range(dimension):
            state = QuantumState.basis(qubits, basis_index)
            circuit_result = qft.apply(state)
            direct_result = direct_qft(state.amplitudes)

            error = max_difference(
                circuit_result.amplitudes,
                direct_result,
            )
            if error > 1e-9:
                raise AssertionError(
                    f"QFT mismatch for {qubits} qubits, "
                    f"basis state {basis_index}: {error}"
                )

            recovered = qft.inverse().apply(circuit_result)
            recovery_error = max_difference(
                recovered.amplitudes,
                state.amplitudes,
            )
            if recovery_error > 1e-9:
                raise AssertionError(
                    f"Inverse-QFT failure: {recovery_error}"
                )

        if verify_unitarity(qft.matrix()) > 1e-9:
            raise AssertionError("QFT matrix failed unitarity validation.")

    try:
        QuantumState([])
    except ValueError:
        pass
    else:
        raise AssertionError("Empty states must be rejected.")

    try:
        QuantumState([1, 2, 3])
    except ValueError:
        pass
    else:
        raise AssertionError("Non-power-of-two states must be rejected.")

    print("Validation passed for QFT circuits from 1 through 4 qubits.")


if __name__ == "__main__":
    run_validation()
    print()
    run_demo(3)
