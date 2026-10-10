#!/usr/bin/env python3
"""Build and simulate quantum circuits using a dependency-free state-vector simulator.

The simulator supports single-qubit gates, controlled operations, measurement,
shot sampling, circuit inspection, entanglement demonstrations, and Grover search
for small quantum systems. It uses complex amplitudes and NumPy is not required.
"""

from __future__ import annotations

import cmath
import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Sequence

ComplexMatrix = tuple[tuple[complex, ...], ...]


def matrix_multiply(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("Incompatible matrix dimensions")
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0])))
        for i in range(len(a))
    )


def dagger(matrix: ComplexMatrix) -> ComplexMatrix:
    return tuple(
        tuple(matrix[j][i].conjugate() for j in range(len(matrix)))
        for i in range(len(matrix[0]))
    )


def identity(size: int) -> ComplexMatrix:
    return tuple(tuple(complex(i == j) for j in range(size)) for i in range(size))


def validate_unitary(matrix: ComplexMatrix, tolerance: float = 1e-10) -> None:
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("A gate matrix must be square and nonempty")
    product = matrix_multiply(dagger(matrix), matrix)
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            expected = complex(i == j)
            if abs(product[i][j] - expected) > tolerance:
                raise ValueError("Gate matrix is not unitary")


SQRT2 = math.sqrt(2)
I = complex(0, 1)

GATES: dict[str, ComplexMatrix] = {
    "I": ((1, 0), (0, 1)),
    "X": ((0, 1), (1, 0)),
    "Y": ((0, -I), (I, 0)),
    "Z": ((1, 0), (0, -1)),
    "H": ((1 / SQRT2, 1 / SQRT2), (1 / SQRT2, -1 / SQRT2)),
    "S": ((1, 0), (0, I)),
    "T": ((1, 0), (0, cmath.exp(I * math.pi / 4))),
}


def rotation_x(theta: float) -> ComplexMatrix:
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return ((c, -I * s), (-I * s, c))


def rotation_y(theta: float) -> ComplexMatrix:
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return ((c, -s), (s, c))


def rotation_z(theta: float) -> ComplexMatrix:
    return (
        (cmath.exp(-I * theta / 2), 0),
        (0, cmath.exp(I * theta / 2)),
    )


@dataclass(frozen=True)
class Operation:
    name: str
    targets: tuple[int, ...]
    matrix: ComplexMatrix | None = None
    controls: tuple[int, ...] = ()
    parameters: tuple[float, ...] = ()


class QuantumCircuit:
    """Little-endian state-vector circuit; qubit zero is the least significant bit."""

    def __init__(self, num_qubits: int, seed: int | None = 7):
        if not isinstance(num_qubits, int) or isinstance(num_qubits, bool):
            raise TypeError("num_qubits must be an integer")
        if not 1 <= num_qubits <= 20:
            raise ValueError("Supported circuit size is 1 to 20 qubits")
        self.num_qubits = num_qubits
        self.operations: list[Operation] = []
        self.state = [0j] * (1 << num_qubits)
        self.state[0] = 1 + 0j
        self.rng = random.Random(seed)
        self.measurements: list[int] = []
        self._measured = False

    def _check_qubit(self, qubit: int) -> None:
        if not isinstance(qubit, int) or isinstance(qubit, bool):
            raise TypeError("Qubit index must be an integer")
        if not 0 <= qubit < self.num_qubits:
            raise ValueError(f"Qubit {qubit} is outside the circuit")

    def _add_gate(
        self,
        name: str,
        targets: Sequence[int],
        matrix: ComplexMatrix,
        controls: Sequence[int] = (),
        parameters: Sequence[float] = (),
    ) -> QuantumCircuit:
        if self._measured:
            raise RuntimeError("Create a fresh circuit after sampling measurements")
        targets = tuple(targets)
        controls = tuple(controls)
        if not targets or len(set(targets)) != len(targets):
            raise ValueError("Targets must be nonempty and unique")
        if len(set(controls)) != len(controls):
            raise ValueError("Control qubits must be unique")
        for q in targets + controls:
            self._check_qubit(q)
        if set(targets) & set(controls):
            raise ValueError("A qubit cannot be both a control and a target")
        if len(matrix) != 1 << len(targets):
            raise ValueError("Gate dimension does not match target count")
        validate_unitary(matrix)
        self.operations.append(Operation(name, targets, matrix, controls, tuple(parameters)))
        return self

    def gate(self, name: str, qubit: int) -> QuantumCircuit:
        if name not in GATES:
            raise ValueError(f"Unknown gate: {name}")
        return self._add_gate(name, (qubit,), GATES[name])

    def x(self, qubit: int) -> QuantumCircuit:
        return self.gate("X", qubit)

    def h(self, qubit: int) -> QuantumCircuit:
        return self.gate("H", qubit)

    def z(self, qubit: int) -> QuantumCircuit:
        return self.gate("Z", qubit)

    def s(self, qubit: int) -> QuantumCircuit:
        return self.gate("S", qubit)

    def t(self, qubit: int) -> QuantumCircuit:
        return self.gate("T", qubit)

    def rx(self, theta: float, qubit: int) -> QuantumCircuit:
        return self._add_gate("RX", (qubit,), rotation_x(theta), parameters=(theta,))

    def ry(self, theta: float, qubit: int) -> QuantumCircuit:
        return self._add_gate("RY", (qubit,), rotation_y(theta), parameters=(theta,))

    def rz(self, theta: float, qubit: int) -> QuantumCircuit:
        return self._add_gate("RZ", (qubit,), rotation_z(theta), parameters=(theta,))

    def cnot(self, control: int, target: int) -> QuantumCircuit:
        return self._add_gate("X", (target,), GATES["X"], controls=(control,))

    def cz(self, control: int, target: int) -> QuantumCircuit:
        return self._add_gate("Z", (target,), GATES["Z"], controls=(control,))

    def swap(self, first: int, second: int) -> QuantumCircuit:
        if first == second:
            raise ValueError("SWAP requires two different qubits")
        matrix = (
            (1, 0, 0, 0),
            (0, 0, 1, 0),
            (0, 1, 0, 0),
            (0, 0, 0, 1),
        )
        return self._add_gate("SWAP", (first, second), matrix)

    def unitary(
        self, matrix: ComplexMatrix, targets: Sequence[int], name: str = "U"
    ) -> QuantumCircuit:
        return self._add_gate(name, targets, matrix)

    def apply(self, operation: Operation) -> None:
        """Apply a local gate without constructing the full 2^n by 2^n matrix."""
        n = self.num_qubits
        dimension = 1 << n
        targets = operation.targets
        target_mask = sum(1 << q for q in targets)
        control_mask = sum(1 << q for q in operation.controls)
        output = self.state.copy()
        local_dimension = 1 << len(targets)

        # Visit only basis states whose target bits are zero. Each local block is
        # transformed exactly once, reducing the cost of a k-qubit gate to O(2^n 2^k).
        for base in range(dimension):
            if base & target_mask:
                continue
            if (base & control_mask) != control_mask:
                continue

            indices = []
            for local in range(local_dimension):
                index = base
                for position, qubit in enumerate(targets):
                    if local & (1 << position):
                        index |= 1 << qubit
                indices.append(index)

            old = [self.state[index] for index in indices]
            for row, index in enumerate(indices):
                output[index] = sum(
                    operation.matrix[row][column] * old[column]
                    for column in range(local_dimension)
                )

        self.state = output

    def run(self) -> list[complex]:
        for operation in self.operations:
            self.apply(operation)
        return self.state.copy()

    def probabilities(self) -> dict[str, float]:
        self.run()
        return {
            format(index, f"0{self.num_qubits}b")[::-1]: abs(amplitude) ** 2
            for index, amplitude in enumerate(self.state)
            if abs(amplitude) ** 2 > 1e-14
        }

    def sample(self, shots: int = 1000) -> Counter[str]:
        if not isinstance(shots, int) or isinstance(shots, bool) or shots <= 0:
            raise ValueError("shots must be a positive integer")
        self.run()
        weights = [abs(amplitude) ** 2 for amplitude in self.state]
        total = sum(weights)
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            raise RuntimeError(f"State normalization failed: {total}")
        counts: Counter[str] = Counter()
        for _ in range(shots):
            index = self.rng.choices(range(len(weights)), weights=weights, k=1)[0]
            bits = format(index, f"0{self.num_qubits}b")[::-1]
            counts[bits] += 1
        return counts

    def measure_all(self) -> str:
        """Perform one projective measurement and collapse the state."""
        self.run()
        probabilities = [abs(amplitude) ** 2 for amplitude in self.state]
        selected = self.rng.choices(range(len(probabilities)), weights=probabilities, k=1)[0]
        norm = math.sqrt(probabilities[selected])
        self.state = [0j] * len(self.state)
        self.state[selected] = 1 + 0j
        self.measurements = [
            (selected >> q) & 1 for q in range(self.num_qubits)
        ]
        self._measured = True
        return format(selected, f"0{self.num_qubits}b")[::-1]

    def diagram(self) -> str:
        rows = [f"q{q}: |0>" for q in range(self.num_qubits)]
        for op in self.operations:
            for q in range(self.num_qubits):
                if q in op.targets:
                    symbol = op.name
                elif q in op.controls:
                    symbol = "●"
                else:
                    symbol = "─"
                rows[q] += f" ──{symbol}──"
        return "\n".join(rows)

    def expectation_z(self, qubit: int) -> float:
        self._check_qubit(qubit)
        self.run()
        return sum(
            (1 if ((index >> qubit) & 1) == 0 else -1) * abs(amplitude) ** 2
            for index, amplitude in enumerate(self.state)
        )

    def fidelity(self, other: QuantumCircuit) -> float:
        if self.num_qubits != other.num_qubits:
            raise ValueError("Fidelity requires equal circuit dimensions")
        a, b = self.run(), other.run()
        overlap = sum(x.conjugate() * y for x, y in zip(a, b))
        return abs(overlap) ** 2


def grover_two_qubit(marked_state: str = "11", shots: int = 1000) -> Counter[str]:
    """Run a two-qubit Grover search with one marked basis state."""
    if len(marked_state) != 2 or any(bit not in "01" for bit in marked_state):
        raise ValueError("marked_state must contain two binary digits")

    circuit = QuantumCircuit(2, seed=21)
    circuit.h(0).h(1)

    # A phase oracle multiplies only the marked amplitude by -1.
    marked_index = int(marked_state[::-1], 2)
    oracle = [list(row) for row in identity(4)]
    oracle[marked_index][marked_index] = -1
    circuit.unitary(tuple(tuple(row) for row in oracle), (0, 1), "Oracle")

    # The diffusion operator is 2|s><s| - I, where |s> is the uniform state.
    diffusion = []
    for row in range(4):
        diffusion.append(tuple(
            complex(0.5 if row != column else -0.5) for column in range(4)
        ))
    diffusion_matrix = [list(row) for row in diffusion]
    for row in range(4):
        diffusion_matrix[row][row] += 1
    circuit.unitary(tuple(tuple(row) for row in diffusion_matrix), (0, 1), "Diffusion")
    return circuit.sample(shots)


def demonstrate_bell_state() -> None:
    circuit = QuantumCircuit(2, seed=4)
    circuit.h(0).cnot(0, 1)
    print("Bell circuit")
    print(circuit.diagram())
    print("Probabilities:", circuit.probabilities())
    print("Sample counts:", dict(circuit.sample(1000)))
    print("Z expectation on q0:", circuit.expectation_z(0))


def demonstrate_rotations() -> None:
    circuit = QuantumCircuit(1)
    circuit.ry(math.pi / 3, 0)
    probabilities = circuit.probabilities()
    expected_zero = math.cos(math.pi / 6) ** 2
    assert math.isclose(probabilities["0"], expected_zero, abs_tol=1e-9)
    print("RY(pi/3) probabilities:", probabilities)


def run_self_tests() -> None:
    # X applied twice restores the original state.
    original = QuantumCircuit(1)
    restored = QuantumCircuit(1).x(0).x(0)
    assert math.isclose(original.fidelity(restored), 1.0, abs_tol=1e-9)

    # A Bell pair has equal probabilities for 00 and 11.
    bell = QuantumCircuit(2).h(0).cnot(0, 1)
    probs = bell.probabilities()
    assert math.isclose(probs.get("00", 0), 0.5, abs_tol=1e-9)
    assert math.isclose(probs.get("11", 0), 0.5, abs_tol=1e-9)

    # A rotation followed by its inverse returns the input state.
    rotation = QuantumCircuit(1).ry(0.7, 0).ry(-0.7, 0)
    assert math.isclose(rotation.fidelity(QuantumCircuit(1)), 1.0, abs_tol=1e-9)

    try:
        QuantumCircuit(1).cnot(0, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("A target cannot also be a control")

    try:
        QuantumCircuit(1).sample(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Zero shots must be rejected")

    print("All simulator tests passed.")


def main() -> None:
    run_self_tests()
    demonstrate_rotations()
    demonstrate_bell_state()
    print("Two-qubit Grover search for state 11:", dict(grover_two_qubit("11", 1000)))


if __name__ == "__main__":
    main()
