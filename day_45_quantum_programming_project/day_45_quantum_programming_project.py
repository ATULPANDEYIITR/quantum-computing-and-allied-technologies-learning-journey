#!/usr/bin/env python3
"""
Multi-Qubit Quantum Circuit Laboratory.

A self-contained quantum programming project using only the Python standard
library. It implements state-vector simulation, tensor products, single-qubit
gates, controlled operations, entanglement, measurement, circuit validation,
and quantum teleportation.

Run:
    python quantum_circuit.py

The simulator is intended for educational and small-circuit experiments.
Its state-vector memory requirement grows exponentially with qubit count.
"""

from __future__ import annotations

import cmath
import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

Complex = complex
Matrix2 = tuple[tuple[Complex, Complex], tuple[Complex, Complex]]
EPSILON = 1e-10


def close(a: Complex, b: Complex, tolerance: float = EPSILON) -> bool:
    return abs(a - b) <= tolerance


def normalize_state(state: Sequence[Complex]) -> list[Complex]:
    """Normalize amplitudes and reject the zero vector."""
    norm = math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))
    if norm <= EPSILON:
        raise ValueError("A quantum state cannot have zero norm.")
    return [amplitude / norm for amplitude in state]


def validate_unitary(matrix: Sequence[Sequence[Complex]]) -> None:
    """Check that U†U equals the identity for a two-dimensional gate."""
    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        raise ValueError("This simulator expects 2x2 single-qubit gates.")

    for row in range(2):
        for column in range(2):
            inner_product = sum(
                matrix[k][row].conjugate() * matrix[k][column]
                for k in range(2)
            )
            expected = 1.0 if row == column else 0.0
            if not close(inner_product, expected):
                raise ValueError("Gate matrix is not unitary.")


I: Matrix2 = ((1, 0), (0, 1))
X: Matrix2 = ((0, 1), (1, 0))
Y: Matrix2 = ((0, -1j), (1j, 0))
Z: Matrix2 = ((1, 0), (0, -1))
H: Matrix2 = (
    (1 / math.sqrt(2), 1 / math.sqrt(2)),
    (1 / math.sqrt(2), -1 / math.sqrt(2)),
)
S: Matrix2 = ((1, 0), (0, 1j))
T: Matrix2 = ((1, 0), (0, cmath.exp(1j * math.pi / 4)))


def rotation_x(theta: float) -> Matrix2:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return ((c, -1j * s), (-1j * s, c))


def rotation_y(theta: float) -> Matrix2:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return ((c, -s), (s, c))


def rotation_z(theta: float) -> Matrix2:
    return (
        (cmath.exp(-1j * theta / 2), 0),
        (0, cmath.exp(1j * theta / 2)),
    )


def apply_matrix_to_bit(
    state: Sequence[Complex],
    qubit_count: int,
    target: int,
    matrix: Matrix2,
    controls: Sequence[int] = (),
) -> list[Complex]:
    """
    Apply a single-qubit matrix to a state vector.

    Qubit 0 is the most significant bit in displayed bitstrings. The matrix
    acts on target only when every listed control is measured as |1>.
    Each amplitude pair is updated exactly once.
    """
    if not 0 <= target < qubit_count:
        raise IndexError("Target qubit is outside the circuit.")
    if target in controls or len(set(controls)) != len(controls):
        raise ValueError("Controls must be distinct from the target.")
    if any(not 0 <= control < qubit_count for control in controls):
        raise IndexError("Control qubit is outside the circuit.")

    validate_unitary(matrix)
    dimension = 1 << qubit_count
    output = list(state)
    target_mask = 1 << (qubit_count - 1 - target)
    control_mask = sum(1 << (qubit_count - 1 - c) for c in controls)

    for index in range(dimension):
        if index & target_mask:
            continue
        if (index & control_mask) != control_mask:
            continue

        partner = index | target_mask
        a0, a1 = state[index], state[partner]
        output[index] = matrix[0][0] * a0 + matrix[0][1] * a1
        output[partner] = matrix[1][0] * a0 + matrix[1][1] * a1

    return output


@dataclass(frozen=True)
class GateOperation:
    name: str
    target: int
    matrix: Matrix2
    controls: tuple[int, ...] = ()


class QuantumCircuit:
    """A small state-vector circuit with explicit qubit ordering."""

    def __init__(self, qubit_count: int, seed: int | None = 7):
        if not isinstance(qubit_count, int) or isinstance(qubit_count, bool):
            raise TypeError("Qubit count must be an integer.")
        if qubit_count < 1:
            raise ValueError("A circuit requires at least one qubit.")
        if qubit_count > 20:
            raise ValueError(
                "This educational simulator limits circuits to 20 qubits."
            )

        self.qubit_count = qubit_count
        self.dimension = 1 << qubit_count
        self.state = [0j] * self.dimension
        self.state[0] = 1 + 0j
        self.operations: list[GateOperation] = []
        self.rng = random.Random(seed)

    def _record(
        self,
        name: str,
        target: int,
        matrix: Matrix2,
        controls: Iterable[int] = (),
    ) -> None:
        controls = tuple(controls)
        self.state = apply_matrix_to_bit(
            self.state, self.qubit_count, target, matrix, controls
        )
        self.operations.append(GateOperation(name, target, matrix, controls))
        self._assert_normalized()

    def _assert_normalized(self) -> None:
        probability = sum(abs(a) ** 2 for a in self.state)
        if not close(probability, 1.0, 1e-8):
            raise ArithmeticError(f"State normalization failed: {probability}")

    def gate(self, matrix: Matrix2, target: int, name: str = "U") -> None:
        self._record(name, target, matrix)

    def h(self, target: int) -> None:
        self._record("H", target, H)

    def x(self, target: int) -> None:
        self._record("X", target, X)

    def y(self, target: int) -> None:
        self._record("Y", target, Y)

    def z(self, target: int) -> None:
        self._record("Z", target, Z)

    def s(self, target: int) -> None:
        self._record("S", target, S)

    def t(self, target: int) -> None:
        self._record("T", target, T)

    def rx(self, target: int, theta: float) -> None:
        self._record(f"RX({theta:.4f})", target, rotation_x(theta))

    def ry(self, target: int, theta: float) -> None:
        self._record(f"RY({theta:.4f})", target, rotation_y(theta))

    def rz(self, target: int, theta: float) -> None:
        self._record(f"RZ({theta:.4f})", target, rotation_z(theta))

    def controlled_x(self, control: int, target: int) -> None:
        self._record("CX", target, X, (control,))

    def controlled_z(self, control: int, target: int) -> None:
        self._record("CZ", target, Z, (control,))

    def controlled_h(self, control: int, target: int) -> None:
        self._record("CH", target, H, (control,))

    def multi_controlled_x(
        self, controls: Sequence[int], target: int
    ) -> None:
        self._record("MCX", target, X, controls)

    def probabilities(self) -> list[float]:
        return [abs(amplitude) ** 2 for amplitude in self.state]

    def statevector(self) -> list[Complex]:
        return list(self.state)

    def basis_probabilities(self) -> dict[str, float]:
        return {
            format(index, f"0{self.qubit_count}b"): probability
            for index, probability in enumerate(self.probabilities())
            if probability > EPSILON
        }

    def measure_qubit(self, target: int) -> int:
        """Perform a projective measurement and collapse the state."""
        if not 0 <= target < self.qubit_count:
            raise IndexError("Measurement target is outside the circuit.")

        mask = 1 << (self.qubit_count - 1 - target)
        probability_one = sum(
            abs(amplitude) ** 2
            for index, amplitude in enumerate(self.state)
            if index & mask
        )
        outcome = int(self.rng.random() < probability_one)
        probability = probability_one if outcome else 1 - probability_one

        if probability <= EPSILON:
            raise ArithmeticError("Selected measurement outcome has zero probability.")

        for index, amplitude in enumerate(self.state):
            if bool(index & mask) != bool(outcome):
                self.state[index] = 0j
            else:
                self.state[index] = amplitude / math.sqrt(probability)

        return outcome

    def measure_all(self) -> str:
        index = self._sample_basis_index()
        outcome = format(index, f"0{self.qubit_count}b")
        self.state = [0j] * self.dimension
        self.state[index] = 1 + 0j
        return outcome

    def _sample_basis_index(self) -> int:
        probabilities = self.probabilities()
        draw = self.rng.random()
        cumulative = 0.0
        for index, probability in enumerate(probabilities):
            cumulative += probability
            if draw < cumulative:
                return index
        return self.dimension - 1

    def run_shots(self, shots: int = 1000) -> Counter[str]:
        if not isinstance(shots, int) or isinstance(shots, bool) or shots < 1:
            raise ValueError("Shots must be a positive integer.")
        probabilities = self.probabilities()
        counts: Counter[str] = Counter()

        # Repeated shots sample the same pre-measurement circuit distribution.
        for _ in range(shots):
            draw = self.rng.random()
            cumulative = 0.0
            for index, probability in enumerate(probabilities):
                cumulative += probability
                if draw < cumulative:
                    counts[format(index, f"0{self.qubit_count}b")] += 1
                    break
            else:
                counts[format(self.dimension - 1, f"0{self.qubit_count}b")] += 1

        return counts

    def expectation_z(self, target: int) -> float:
        if not 0 <= target < self.qubit_count:
            raise IndexError("Target qubit is outside the circuit.")
        mask = 1 << (self.qubit_count - 1 - target)
        return sum(
            (1.0 if not index & mask else -1.0) * abs(amplitude) ** 2
            for index, amplitude in enumerate(self.state)
        )

    def describe(self) -> None:
        print(f"Circuit: {self.qubit_count} qubits")
        for position, operation in enumerate(self.operations):
            controls = (
                f", controls={operation.controls}" if operation.controls else ""
            )
            print(
                f"  {position:02d}: {operation.name} "
                f"target={operation.target}{controls}"
            )

    def draw_ascii(self) -> str:
        """Render an operation-oriented listing without assuming equal gate widths."""
        lines = []
        for qubit in range(self.qubit_count):
            operations = []
            for operation in self.operations:
                if qubit in operation.controls:
                    operations.append("●")
                elif qubit == operation.target:
                    operations.append(operation.name)
                else:
                    operations.append("─")
            lines.append(f"q{qubit}: " + " ─ ".join(operations or ["|0>"]))
        return "\n".join(lines)


def tensor_product(
    left: Sequence[Complex], right: Sequence[Complex]
) -> list[Complex]:
    """Construct |left> ⊗ |right>, preserving left-to-right bit ordering."""
    return [a * b for a in left for b in right]


def bell_state_example() -> QuantumCircuit:
    circuit = QuantumCircuit(2, seed=11)
    circuit.h(0)
    circuit.controlled_x(0, 1)
    return circuit


def ghz_state_example(qubit_count: int = 3) -> QuantumCircuit:
    """Prepare (|00...0> + |11...1>) / sqrt(2)."""
    circuit = QuantumCircuit(qubit_count, seed=13)
    circuit.h(0)
    for target in range(1, qubit_count):
        circuit.controlled_x(target - 1, target)
    return circuit


def deutsch_jozsa_oracle(circuit: QuantumCircuit, balanced: bool) -> None:
    """Use f(x)=x[0] as a balanced oracle or f(x)=0 as a constant oracle."""
    if balanced:
        circuit.controlled_x(0, circuit.qubit_count - 1)


def deutsch_jozsa_demo(balanced: bool) -> tuple[QuantumCircuit, str]:
    """
    Distinguish a constant from a balanced oracle with one oracle query.

    The last qubit is the oracle output; preceding qubits are input registers.
    """
    if not balanced and False:
        raise ValueError("Unreachable oracle configuration.")

    circuit = QuantumCircuit(3, seed=17)
    circuit.x(2)
    for qubit in range(3):
        circuit.h(qubit)

    deutsch_jozsa_oracle(circuit, balanced)

    for qubit in range(2):
        circuit.h(qubit)

    probabilities = circuit.basis_probabilities()
    input_distribution: dict[str, float] = {}
    for bitstring, probability in probabilities.items():
        input_bits = bitstring[:2]
        input_distribution[input_bits] = (
            input_distribution.get(input_bits, 0.0) + probability
        )

    if balanced:
        assert close(input_distribution.get("00", 0.0), 0.0)
    else:
        assert close(input_distribution.get("00", 0.0), 1.0)

    return circuit, max(input_distribution, key=input_distribution.get)


def teleportation_demo(
    alpha: Complex, beta: Complex, seed: int = 23
) -> tuple[str, list[Complex]]:
    """
    Teleport an arbitrary normalized one-qubit state using three qubits.

    q0 is the input, q1 is Alice's entangled qubit, and q2 is Bob's qubit.
    Classical measurement outcomes select Bob's X and Z corrections.
    """
    if not close(abs(alpha) ** 2 + abs(beta) ** 2, 1.0):
        raise ValueError("Input amplitudes must define a normalized state.")

    circuit = QuantumCircuit(3, seed=seed)
    circuit.state = [0j] * 8
    circuit.state[0] = alpha
    circuit.state[4] = beta
    circuit.state = normalize_state(circuit.state)

    # Create an entangled resource between q1 and q2.
    circuit.h(1)
    circuit.controlled_x(1, 2)

    # Bell-basis transformation on the input and Alice's qubit.
    circuit.controlled_x(0, 1)
    circuit.h(0)

    # Measurements are sequential; collapse preserves the conditional state.
    classical_0 = circuit.measure_qubit(0)
    classical_1 = circuit.measure_qubit(1)

    # Apply Bob's corrections using the two classical measurement bits.
    if classical_1:
        circuit.x(2)
    if classical_0:
        circuit.z(2)

    # Extract Bob's reduced state from the computational-basis amplitudes.
    # Alice's measured bits are known, so only their collapsed sector remains.
    bob_amplitudes = [0j, 0j]
    for index, amplitude in enumerate(circuit.state):
        bits = format(index, "03b")
        if int(bits[0]) == classical_0 and int(bits[1]) == classical_1:
            bob_amplitudes[int(bits[2])] += amplitude

    bob_state = normalize_state(bob_amplitudes)
    return f"{classical_0}{classical_1}", bob_state


def run_unit_checks() -> None:
    """Validate core gate and state invariants without third-party testing tools."""
    circuit = QuantumCircuit(1)
    circuit.x(0)
    assert circuit.basis_probabilities() == {"1": 1.0}

    circuit.h(0)
    assert close(circuit.probabilities()[0], 0.5)
    assert close(circuit.probabilities()[1], 0.5)

    bell = bell_state_example()
    assert close(bell.probabilities()[0], 0.5)
    assert close(bell.probabilities()[3], 0.5)
    assert close(bell.probabilities()[1], 0.0)
    assert close(bell.probabilities()[2], 0.0)

    ghz = ghz_state_example(4)
    assert close(ghz.probabilities()[0], 0.5)
    assert close(ghz.probabilities()[-1], 0.5)

    try:
        QuantumCircuit(0)
    except ValueError:
        pass
    else:
        raise AssertionError("A zero-qubit circuit must be rejected.")

    try:
        apply_matrix_to_bit([1 + 0j, 0j], 1, 0, ((1, 1), (0, 1)))
    except ValueError:
        pass
    else:
        raise AssertionError("A non-unitary gate must be rejected.")


def main() -> None:
    run_unit_checks()

    print("MULTI-QUBIT CIRCUIT: BELL STATE")
    bell = bell_state_example()
    bell.describe()
    print("State amplitudes:", bell.statevector())
    print("Nonzero probabilities:", bell.basis_probabilities())
    print("Measured shot distribution:", bell.run_shots(1000))
    print("Circuit layout:")
    print(bell.draw_ascii())

    print("\nMULTI-QUBIT CIRCUIT: FOUR-QUBIT GHZ STATE")
    ghz = ghz_state_example(4)
    print(ghz.basis_probabilities())
    print("Z expectation for q0:", ghz.expectation_z(0))

    print("\nROTATION GATES")
    rotation = QuantumCircuit(1)
    rotation.ry(0, math.pi / 3)
    print(rotation.basis_probabilities())
    print("Expected Z:", rotation.expectation_z(0))

    print("\nDEUTSCH-JOZSA ORACLE")
    for is_balanced in (False, True):
        circuit, observed = deutsch_jozsa_demo(is_balanced)
        print(
            f"Oracle={'balanced' if is_balanced else 'constant'}, "
            f"observed input={observed}"
        )

    print("\nQUANTUM TELEPORTATION")
    alpha = math.sqrt(0.7)
    beta = cmath.exp(1j * 0.4) * math.sqrt(0.3)
    classical_bits, bob_state = teleportation_demo(alpha, beta)
    print("Alice's classical measurement bits:", classical_bits)
    print("Bob's reconstructed amplitudes:", bob_state)
    fidelity = abs(alpha.conjugate() * bob_state[0] + beta.conjugate() * bob_state[1]) ** 2
    print("State fidelity:", fidelity)
    assert close(fidelity, 1.0)

    print("\nAll quantum circuit checks passed.")


if __name__ == "__main__":
    main()
