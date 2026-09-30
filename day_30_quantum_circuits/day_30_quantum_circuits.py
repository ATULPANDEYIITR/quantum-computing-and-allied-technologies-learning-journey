"""
Quantum Circuits | Circuit Construction Fundamentals

A self-contained educational implementation of quantum-circuit construction
using only Python's standard library.

The simulator uses state vectors and explicitly implements common one- and
two-qubit gates, circuit composition, measurement probabilities, sampling,
parameterized rotations, controlled operations, and circuit validation.

The simulator is intentionally small enough to inspect, while preserving the
core linear-algebra mechanism behind circuit execution.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


Complex = complex
Matrix2 = tuple[tuple[Complex, Complex], tuple[Complex, Complex]]


def format_complex(value: Complex, digits: int = 4) -> str:
    """Format a complex number while suppressing numerical noise."""
    real = 0.0 if abs(value.real) < 10 ** -digits else value.real
    imag = 0.0 if abs(value.imag) < 10 ** -digits else value.imag

    if imag == 0:
        return f"{real:.{digits}f}"
    if real == 0:
        return f"{imag:.{digits}f}i"
    sign = "+" if imag >= 0 else "-"
    return f"{real:.{digits}f} {sign} {abs(imag):.{digits}f}i"


def bit_string(index: int, qubits: int) -> str:
    """Return a computational-basis state such as |010>."""
    return format(index, f"0{qubits}b")


def validate_qubit(qubit: int, qubits: int) -> None:
    if not isinstance(qubit, int):
        raise TypeError("Qubit index must be an integer.")
    if qubit < 0 or qubit >= qubits:
        raise ValueError(f"Qubit {qubit} is outside a {qubits}-qubit circuit.")


def validate_distinct_qubits(first: int, second: int, qubits: int) -> None:
    validate_qubit(first, qubits)
    validate_qubit(second, qubits)
    if first == second:
        raise ValueError("A two-qubit operation requires two distinct qubits.")


def matrix_multiply(left: Matrix2, right: Matrix2) -> Matrix2:
    """Multiply two 2x2 complex matrices."""
    return (
        (
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ),
        (
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ),
    )


def apply_single_qubit_matrix(
    state: list[Complex],
    qubits: int,
    target: int,
    matrix: Matrix2,
) -> None:
    """
    Apply a 2x2 operator to one logical qubit.

    Basis indices are represented in binary. The most significant bit is
    qubit 0, so target q acts at bit position (qubits - 1 - target).
    """
    validate_qubit(target, qubits)
    bit = 1 << (qubits - 1 - target)

    for base in range(len(state)):
        if base & bit:
            continue

        zero_index = base
        one_index = base | bit
        amplitude_zero = state[zero_index]
        amplitude_one = state[one_index]

        state[zero_index] = (
            matrix[0][0] * amplitude_zero
            + matrix[0][1] * amplitude_one
        )
        state[one_index] = (
            matrix[1][0] * amplitude_zero
            + matrix[1][1] * amplitude_one
        )


def apply_controlled_matrix(
    state: list[Complex],
    qubits: int,
    control: int,
    target: int,
    matrix: Matrix2,
) -> None:
    """Apply a controlled 2x2 operator when the control qubit is |1>."""
    validate_distinct_qubits(control, target, qubits)

    control_bit = 1 << (qubits - 1 - control)
    target_bit = 1 << (qubits - 1 - target)

    for base in range(len(state)):
        if base & control_bit == 0 or base & target_bit:
            continue

        zero_index = base
        one_index = base | target_bit
        amplitude_zero = state[zero_index]
        amplitude_one = state[one_index]

        state[zero_index] = (
            matrix[0][0] * amplitude_zero
            + matrix[0][1] * amplitude_one
        )
        state[one_index] = (
            matrix[1][0] * amplitude_zero
            + matrix[1][1] * amplitude_one
        )


I: Matrix2 = (
    (1 + 0j, 0j),
    (0j, 1 + 0j),
)

X: Matrix2 = (
    (0j, 1 + 0j),
    (1 + 0j, 0j),
)

Y: Matrix2 = (
    (0j, -1j),
    (1j, 0j),
)

Z: Matrix2 = (
    (1 + 0j, 0j),
    (0j, -1 + 0j),
)

H: Matrix2 = (
    (1 / math.sqrt(2), 1 / math.sqrt(2)),
    (1 / math.sqrt(2), -1 / math.sqrt(2)),
)


def rotation_x(theta: float) -> Matrix2:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return (
        (c, -1j * s),
        (-1j * s, c),
    )


def rotation_y(theta: float) -> Matrix2:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return (
        (c, -s),
        (s, c),
    )


def rotation_z(theta: float) -> Matrix2:
    return (
        (cmath.exp(-1j * theta / 2), 0j),
        (0j, cmath.exp(1j * theta / 2)),
    )


@dataclass(frozen=True)
class Operation:
    name: str
    qubits: tuple[int, ...]
    matrix: Matrix2 | None = None
    parameter: float | None = None
    control: int | None = None
    target: int | None = None


class QuantumCircuit:
    """
    Small state-vector quantum circuit.

    The circuit stores operations first and executes them later. This mirrors
    the useful separation between circuit construction and circuit execution.
    """

    def __init__(self, qubits: int):
        if not isinstance(qubits, int) or qubits <= 0:
            raise ValueError("A circuit must contain at least one qubit.")
        if qubits > 12:
            raise ValueError(
                "This educational simulator limits circuits to 12 qubits "
                "because a state vector contains 2^n amplitudes."
            )

        self.qubits = qubits
        self.operations: list[Operation] = []

    @property
    def dimension(self) -> int:
        return 2 ** self.qubits

    def _append_single(
        self,
        name: str,
        qubit: int,
        matrix: Matrix2,
        parameter: float | None = None,
    ) -> "QuantumCircuit":
        validate_qubit(qubit, self.qubits)
        self.operations.append(
            Operation(name, (qubit,), matrix=matrix, parameter=parameter)
        )
        return self

    def x(self, qubit: int) -> "QuantumCircuit":
        return self._append_single("X", qubit, X)

    def y(self, qubit: int) -> "QuantumCircuit":
        return self._append_single("Y", qubit, Y)

    def z(self, qubit: int) -> "QuantumCircuit":
        return self._append_single("Z", qubit, Z)

    def h(self, qubit: int) -> "QuantumCircuit":
        return self._append_single("H", qubit, H)

    def rx(self, qubit: int, theta: float) -> "QuantumCircuit":
        return self._append_single("RX", qubit, rotation_x(theta), theta)

    def ry(self, qubit: int, theta: float) -> "QuantumCircuit":
        return self._append_single("RY", qubit, rotation_y(theta), theta)

    def rz(self, qubit: int, theta: float) -> "QuantumCircuit":
        return self._append_single("RZ", qubit, rotation_z(theta), theta)

    def cx(self, control: int, target: int) -> "QuantumCircuit":
        validate_distinct_qubits(control, target, self.qubits)
        self.operations.append(
            Operation(
                "CX",
                (control, target),
                control=control,
                target=target,
                matrix=X,
            )
        )
        return self

    def controlled(
        self,
        control: int,
        target: int,
        matrix: Matrix2,
        name: str = "CU",
    ) -> "QuantumCircuit":
        validate_distinct_qubits(control, target, self.qubits)
        self.operations.append(
            Operation(
                name,
                (control, target),
                control=control,
                target=target,
                matrix=matrix,
            )
        )
        return self

    def measure_probabilities(self, state: Sequence[Complex]) -> dict[str, float]:
        """Convert amplitudes into computational-basis probabilities."""
        if len(state) != self.dimension:
            raise ValueError("State-vector dimension does not match circuit.")

        probabilities: dict[str, float] = {}
        total = sum(abs(amplitude) ** 2 for amplitude in state)

        if not math.isclose(total, 1.0, abs_tol=1e-9):
            raise ValueError(
                f"State is not normalized. Probability total={total:.12f}"
            )

        for index, amplitude in enumerate(state):
            probabilities[bit_string(index, self.qubits)] = abs(amplitude) ** 2

        return probabilities

    def execute(self) -> list[Complex]:
        """Execute every operation from left to right on |00...0>."""
        state = [0j] * self.dimension
        state[0] = 1 + 0j

        for operation in self.operations:
            if operation.name in {"X", "Y", "Z", "H", "RX", "RY", "RZ"}:
                assert operation.matrix is not None
                apply_single_qubit_matrix(
                    state,
                    self.qubits,
                    operation.qubits[0],
                    operation.matrix,
                )
            elif operation.name == "CX":
                assert operation.matrix is not None
                assert operation.control is not None
                assert operation.target is not None
                apply_controlled_matrix(
                    state,
                    self.qubits,
                    operation.control,
                    operation.target,
                    operation.matrix,
                )
            else:
                assert operation.matrix is not None
                assert operation.control is not None
                assert operation.target is not None
                apply_controlled_matrix(
                    state,
                    self.qubits,
                    operation.control,
                    operation.target,
                    operation.matrix,
                )

        return state

    def probabilities(self) -> dict[str, float]:
        return self.measure_probabilities(self.execute())

    def sample(self, shots: int = 1000, seed: int | None = None) -> dict[str, int]:
        """
        Simulate repeated computational-basis measurements.

        A real quantum device samples physical measurement outcomes. This
        simulator samples from the ideal probability distribution.
        """
        if shots <= 0:
            raise ValueError("shots must be positive.")

        if seed is not None:
            random.seed(seed)

        probabilities = self.probabilities()
        states = list(probabilities)
        weights = [probabilities[state] for state in states]
        samples = random.choices(states, weights=weights, k=shots)

        counts = {state: 0 for state in states}
        for result in samples:
            counts[result] += 1

        return counts

    def draw(self) -> str:
        """Render a compact circuit diagram."""
        wires = [[f"q{q}"] for q in range(self.qubits)]

        for operation in self.operations:
            involved = set(operation.qubits)
            for q in range(self.qubits):
                if q not in involved:
                    wires[q].append("───")
                elif operation.name == "CX":
                    if q == operation.control:
                        wires[q].append("─●─")
                    else:
                        wires[q].append("─X─")
                else:
                    wires[q].append(f"-{operation.name:^3}-")

        return "\n".join(f"{label}: " + "".join(parts[1:]) for label, *parts in wires)

    def describe(self) -> None:
        print(f"Circuit: {self.qubits} qubit(s), {len(self.operations)} operation(s)")
        for position, operation in enumerate(self.operations):
            parameter = (
                f", theta={operation.parameter:.6f}"
                if operation.parameter is not None
                else ""
            )
            print(
                f"  {position}: {operation.name}"
                f" on {operation.qubits}{parameter}"
            )


def print_state(state: Sequence[Complex], qubits: int) -> None:
    print("State vector:")
    for index, amplitude in enumerate(state):
        if abs(amplitude) > 1e-10:
            print(
                f"  |{bit_string(index, qubits)}> : "
                f"{format_complex(amplitude)}"
            )


def normalize_probabilities(
    probabilities: dict[str, float],
) -> dict[str, float]:
    total = sum(probabilities.values())
    if total <= 0:
        raise ValueError("Cannot normalize an empty probability distribution.")
    return {key: value / total for key, value in probabilities.items()}


def bell_state_demo() -> None:
    print("\n=== Bell-state construction ===")
    circuit = QuantumCircuit(2)
    circuit.h(0).cx(0, 1)

    circuit.describe()
    print(circuit.draw())

    state = circuit.execute()
    print_state(state, circuit.qubits)

    probabilities = circuit.probabilities()
    print("Measurement probabilities:")
    for state_name, probability in probabilities.items():
        if probability > 1e-10:
            print(f"  {state_name}: {probability:.3f}")

    print("Sampled measurements:")
    print(circuit.sample(1000, seed=7))


def superposition_demo() -> None:
    print("\n=== Single-qubit superposition ===")
    circuit = QuantumCircuit(1).h(0)
    print_state(circuit.execute(), 1)
    print(circuit.sample(20, seed=11))


def basis_state_demo() -> None:
    print("\n=== Basis-state preparation ===")
    circuit = QuantumCircuit(3).x(0).x(2)
    state = circuit.execute()
    print_state(state, 3)
    print("Expected computational basis state: |101>")


def rotation_demo() -> None:
    print("\n=== Parameterized rotation ===")
    circuit = QuantumCircuit(1).ry(0, math.pi / 3)
    probabilities = circuit.probabilities()
    print(f"RY(pi/3) probabilities: {probabilities}")

    # The same circuit construction can be changed without rewriting the
    # simulator because gate parameters are represented as matrix operators.
    circuit2 = QuantumCircuit(1).rx(0, math.pi)
    print("RX(pi) state:")
    print_state(circuit2.execute(), 1)


def controlled_operation_demo() -> None:
    print("\n=== Controlled-Z construction ===")
    circuit = QuantumCircuit(2)
    circuit.h(0).h(1)

    # Controlled-Z applies Z to q1 only when q0 is |1>.
    circuit.controlled(0, 1, Z, name="CZ")

    circuit.describe()
    print_state(circuit.execute(), 2)


def circuit_composition_demo() -> None:
    print("\n=== Circuit composition ===")

    preparation = QuantumCircuit(2)
    preparation.h(0).x(1)

    transformation = QuantumCircuit(2)
    transformation.cx(0, 1).rz(0, math.pi / 2)

    combined = QuantumCircuit(2)
    combined.operations.extend(preparation.operations)
    combined.operations.extend(transformation.operations)

    print("Combined circuit:")
    combined.describe()
    print_state(combined.execute(), 2)


def validation_demo() -> None:
    print("\n=== Validation and failure conditions ===")

    checks: list[Callable[[], object]] = [
        lambda: QuantumCircuit(0),
        lambda: QuantumCircuit(2).h(2),
        lambda: QuantumCircuit(2).cx(1, 1),
        lambda: QuantumCircuit(1).sample(0),
    ]

    for check in checks:
        try:
            check()
        except (ValueError, TypeError) as error:
            print(f"Rejected invalid construction: {error}")


def advanced_parameterized_demo() -> None:
    print("\n=== Parameterized circuit with a nontrivial probability distribution ===")

    circuit = QuantumCircuit(2)
    circuit.ry(0, math.pi / 4)
    circuit.ry(1, math.pi / 6)
    circuit.cx(0, 1)
    circuit.rz(1, math.pi / 3)

    probabilities = normalize_probabilities(circuit.probabilities())

    for state_name, probability in probabilities.items():
        if probability > 1e-10:
            print(f"  |{state_name}> -> {probability:.6f}")

    print("2000-shot measurement estimate:")
    print(circuit.sample(2000, seed=1234))


def explain_scaling() -> None:
    print("\n=== State-vector scaling ===")
    for qubits in range(1, 11):
        amplitudes = 2 ** qubits
        memory_bytes = amplitudes * 16
        print(
            f"{qubits:2d} qubits -> {amplitudes:5d} amplitudes "
            f"-> approximately {memory_bytes / 1024:.1f} KiB"
        )

    print(
        "The exponential state-vector size is the main reason this small "
        "simulator is intentionally bounded."
    )


def run_self_tests() -> None:
    """Small executable correctness checks for circuit-construction behavior."""
    zero = QuantumCircuit(1)
    assert math.isclose(zero.probabilities()["0"], 1.0, abs_tol=1e-9)

    one = QuantumCircuit(1).x(0)
    assert math.isclose(one.probabilities()["1"], 1.0, abs_tol=1e-9)

    bell = QuantumCircuit(2).h(0).cx(0, 1)
    bell_probabilities = bell.probabilities()
    assert math.isclose(bell_probabilities["00"], 0.5, abs_tol=1e-9)
    assert math.isclose(bell_probabilities["11"], 0.5, abs_tol=1e-9)
    assert math.isclose(bell_probabilities["01"], 0.0, abs_tol=1e-9)
    assert math.isclose(bell_probabilities["10"], 0.0, abs_tol=1e-9)

    try:
        QuantumCircuit(2).cx(0, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Identical control and target should be rejected.")

    print("Self-tests passed.")


def main() -> None:
    print("QUANTUM CIRCUITS: CIRCUIT CONSTRUCTION FUNDAMENTALS")
    print("=" * 58)

    run_self_tests()
    basis_state_demo()
    superposition_demo()
    bell_state_demo()
    rotation_demo()
    controlled_operation_demo()
    circuit_composition_demo()
    advanced_parameterized_demo()
    validation_demo()
    explain_scaling()


if __name__ == "__main__":
    main()
