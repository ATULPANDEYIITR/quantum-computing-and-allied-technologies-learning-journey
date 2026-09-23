"""
Quantum Gates: X, Y, Z, and Identity Gates
===========================================

A self-contained educational study program covering:

1. Classical bits versus quantum bits.
2. Computational basis states |0> and |1>.
3. State vectors and normalization.
4. Complex amplitudes and measurement probabilities.
5. Single-qubit X, Y, Z, and Identity gates.
6. Matrix multiplication and gate application.
7. Bloch-sphere interpretation.
8. Global phase versus relative phase.
9. Sequential gate composition.
10. Gate inverses and unitarity.
11. Measurement simulation.
12. State validation and numerical precision.
13. Basis-state transformations.
14. Superposition examples.
15. Phase-sensitive experiments.
16. Expectation values and Pauli operators.
17. Tensor products for multiple qubits.
18. Entanglement-related examples.
19. Quantum teleportation building blocks.
20. Error handling, edge cases, and testing.
21. Complexity and implementation considerations.

The program uses only Python's standard library.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EPSILON = 1e-10
DEFAULT_SHOTS = 10_000

SQRT_TWO = math.sqrt(2.0)

ZERO = 0
ONE = 1


# ---------------------------------------------------------------------------
# Basic mathematical helpers
# ---------------------------------------------------------------------------

def is_close(a: complex, b: complex, tolerance: float = EPSILON) -> bool:
    """Return True when two complex numbers are numerically close."""
    return abs(a - b) <= tolerance


def format_complex(value: complex, digits: int = 4) -> str:
    """
    Format a complex number for educational output.

    Very small real or imaginary components are displayed as zero so that
    floating-point noise does not obscure the mathematics.
    """
    real = 0.0 if abs(value.real) < 10 ** (-digits) else value.real
    imag = 0.0 if abs(value.imag) < 10 ** (-digits) else value.imag

    if imag == 0:
        return f"{real:.{digits}f}"

    if real == 0:
        return f"{imag:.{digits}f}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.{digits}f} {sign} {abs(imag):.{digits}f}i"


def probability_from_amplitude(amplitude: complex) -> float:
    """Born rule: probability = |amplitude|^2."""
    return abs(amplitude) ** 2


def normalize_vector(vector: Sequence[complex]) -> List[complex]:
    """
    Normalize a state vector.

    A quantum state must have total probability equal to one.
    """
    norm_squared = sum(abs(amplitude) ** 2 for amplitude in vector)

    if norm_squared <= EPSILON:
        raise ValueError("The zero vector cannot represent a quantum state.")

    norm = math.sqrt(norm_squared)
    return [amplitude / norm for amplitude in vector]


def vector_norm(vector: Sequence[complex]) -> float:
    """Return the Euclidean norm of a complex vector."""
    return math.sqrt(sum(abs(value) ** 2 for value in vector))


def validate_state(vector: Sequence[complex]) -> None:
    """
    Validate the structural and physical requirements of a single-qubit state.
    """
    if len(vector) != 2:
        raise ValueError("A single-qubit state must contain exactly two amplitudes.")

    if not all(isinstance(value, complex) for value in vector):
        raise TypeError("State amplitudes must be complex numbers.")

    probability_sum = sum(abs(value) ** 2 for value in vector)

    if not math.isclose(probability_sum, 1.0, abs_tol=EPSILON):
        raise ValueError(
            f"State is not normalized. Probability sum = {probability_sum:.12f}"
        )


# ---------------------------------------------------------------------------
# Matrix operations
# ---------------------------------------------------------------------------

Matrix = List[List[complex]]
Vector = List[complex]


def matrix_shape(matrix: Matrix) -> Tuple[int, int]:
    """Return the number of rows and columns."""
    if not matrix:
        return 0, 0

    return len(matrix), len(matrix[0])


def validate_matrix(matrix: Matrix) -> None:
    """Ensure that a matrix is rectangular."""
    if not matrix:
        raise ValueError("Matrix cannot be empty.")

    width = len(matrix[0])

    if width == 0:
        raise ValueError("Matrix cannot contain empty rows.")

    for row in matrix:
        if len(row) != width:
            raise ValueError("Matrix must be rectangular.")


def matrix_vector_multiply(matrix: Matrix, vector: Vector) -> Vector:
    """
    Multiply a matrix by a column vector.

    For a quantum gate U and state |psi>:

        |psi'> = U |psi>
    """
    validate_matrix(matrix)

    rows, columns = matrix_shape(matrix)

    if columns != len(vector):
        raise ValueError(
            f"Matrix has {columns} columns but vector has {len(vector)} elements."
        )

    result: Vector = []

    for row in matrix:
        value = sum(row[index] * vector[index] for index in range(columns))
        result.append(value)

    return result


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    """Multiply two matrices."""
    validate_matrix(left)
    validate_matrix(right)

    left_rows, left_columns = matrix_shape(left)
    right_rows, right_columns = matrix_shape(right)

    if left_columns != right_rows:
        raise ValueError("Matrix dimensions are incompatible for multiplication.")

    result: Matrix = []

    for i in range(left_rows):
        row = []

        for j in range(right_columns):
            value = sum(
                left[i][k] * right[k][j]
                for k in range(left_columns)
            )
            row.append(value)

        result.append(row)

    return result


def conjugate_transpose(matrix: Matrix) -> Matrix:
    """Return the conjugate transpose U† of U."""
    validate_matrix(matrix)

    rows, columns = matrix_shape(matrix)

    return [
        [matrix[row][column].conjugate() for row in range(rows)]
        for column in range(columns)
    ]


def identity_matrix(size: int) -> Matrix:
    """Create an identity matrix."""
    if size <= 0:
        raise ValueError("Matrix size must be positive.")

    return [
        [
            complex(1 if row == column else 0, 0)
            for column in range(size)
        ]
        for row in range(size)
    ]


def matrices_are_close(
    first: Matrix,
    second: Matrix,
    tolerance: float = EPSILON,
) -> bool:
    """Compare two matrices numerically."""
    if matrix_shape(first) != matrix_shape(second):
        return False

    for i in range(len(first)):
        for j in range(len(first[0])):
            if abs(first[i][j] - second[i][j]) > tolerance:
                return False

    return True


# ---------------------------------------------------------------------------
# Quantum states
# ---------------------------------------------------------------------------

@dataclass
class Qubit:
    """
    A single qubit represented by the state:

        |psi> = alpha|0> + beta|1>

    where |alpha|^2 + |beta|^2 = 1.
    """

    alpha: complex
    beta: complex

    def __post_init__(self) -> None:
        self.alpha = complex(self.alpha)
        self.beta = complex(self.beta)
        validate_state(self.vector)

    @property
    def vector(self) -> Vector:
        return [self.alpha, self.beta]

    @property
    def probability_zero(self) -> float:
        return probability_from_amplitude(self.alpha)

    @property
    def probability_one(self) -> float:
        return probability_from_amplitude(self.beta)

    def apply(self, gate: Matrix) -> "Qubit":
        """Apply a 2x2 single-qubit gate."""
        validate_matrix(gate)

        if matrix_shape(gate) != (2, 2):
            raise ValueError("A single-qubit gate must be a 2x2 matrix.")

        transformed = matrix_vector_multiply(gate, self.vector)

        return Qubit(transformed[0], transformed[1])

    def probabilities(self) -> Tuple[float, float]:
        """Return measurement probabilities for |0> and |1>."""
        return self.probability_zero, self.probability_one

    def normalized(self) -> "Qubit":
        """Return a normalized copy."""
        normalized = normalize_vector(self.vector)
        return Qubit(normalized[0], normalized[1])

    def measure(self, rng: random.Random | None = None) -> int:
        """
        Perform a computational-basis measurement.

        Measurement changes the state to the observed basis state.
        """
        if rng is None:
            rng = random.Random()

        outcome = 0 if rng.random() < self.probability_zero else 1

        if outcome == 0:
            self.alpha = complex(1, 0)
            self.beta = complex(0, 0)
        else:
            self.alpha = complex(0, 0)
            self.beta = complex(1, 0)

        return outcome

    def copy(self) -> "Qubit":
        """Return an independent copy."""
        return Qubit(self.alpha, self.beta)

    def __str__(self) -> str:
        alpha = format_complex(self.alpha)
        beta = format_complex(self.beta)
        return f"{alpha}|0> + ({beta})|1>"


# ---------------------------------------------------------------------------
# Standard one-qubit states
# ---------------------------------------------------------------------------

def ket_zero() -> Qubit:
    """Return |0>."""
    return Qubit(1, 0)


def ket_one() -> Qubit:
    """Return |1>."""
    return Qubit(0, 1)


def plus_state() -> Qubit:
    """Return |+> = (|0> + |1>) / sqrt(2)."""
    return Qubit(1 / SQRT_TWO, 1 / SQRT_TWO)


def minus_state() -> Qubit:
    """Return |-> = (|0> - |1>) / sqrt(2)."""
    return Qubit(1 / SQRT_TWO, -1 / SQRT_TWO)


def plus_i_state() -> Qubit:
    """Return |+i> = (|0> + i|1>) / sqrt(2)."""
    return Qubit(1 / SQRT_TWO, 1j / SQRT_TWO)


def minus_i_state() -> Qubit:
    """Return |-i> = (|0> - i|1>) / sqrt(2)."""
    return Qubit(1 / SQRT_TWO, -1j / SQRT_TWO)


# ---------------------------------------------------------------------------
# Quantum gates
# ---------------------------------------------------------------------------

IDENTITY: Matrix = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, 1 + 0j],
]

X_GATE: Matrix = [
    [0 + 0j, 1 + 0j],
    [1 + 0j, 0 + 0j],
]

Y_GATE: Matrix = [
    [0 + 0j, -1j],
    [1j, 0 + 0j],
]

Z_GATE: Matrix = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, -1 + 0j],
]


GATES = {
    "I": IDENTITY,
    "X": X_GATE,
    "Y": Y_GATE,
    "Z": Z_GATE,
}


def apply_gate(state: Qubit, gate_name: str) -> Qubit:
    """Apply a named standard gate."""
    normalized_name = gate_name.upper()

    if normalized_name not in GATES:
        raise KeyError(f"Unknown gate: {gate_name}")

    return state.apply(GATES[normalized_name])


# ---------------------------------------------------------------------------
# Educational gate demonstrations
# ---------------------------------------------------------------------------

def print_state_probabilities(label: str, state: Qubit) -> None:
    """Print a state and its computational-basis probabilities."""
    p0, p1 = state.probabilities()

    print(f"{label}")
    print(f"  State: {state}")
    print(f"  P(0):  {p0:.6f}")
    print(f"  P(1):  {p1:.6f}")
    print(f"  Total: {p0 + p1:.6f}")
    print()


def demonstrate_basis_states() -> None:
    print("=" * 72)
    print("1. BASIS STATES")
    print("=" * 72)

    print_state_probabilities("|0>", ket_zero())
    print_state_probabilities("|1>", ket_one())


def demonstrate_x_gate() -> None:
    print("=" * 72)
    print("2. X GATE")
    print("=" * 72)

    print("The Pauli-X gate swaps computational basis states:")
    print("X|0> = |1>")
    print("X|1> = |0>")
    print()

    print_state_probabilities("X applied to |0>:", apply_gate(ket_zero(), "X"))
    print_state_probabilities("X applied to |1>:", apply_gate(ket_one(), "X"))

    print("X applied twice:")
    twice = apply_gate(apply_gate(ket_zero(), "X"), "X")
    print_state_probabilities("X(X|0>):", twice)


def demonstrate_y_gate() -> None:
    print("=" * 72)
    print("3. Y GATE")
    print("=" * 72)

    print("The Pauli-Y gate both flips the basis state and introduces")
    print("a complex phase:")
    print()
    print("Y|0> = i|1>")
    print("Y|1> = -i|0>")
    print()

    print_state_probabilities("Y applied to |0>:", apply_gate(ket_zero(), "Y"))
    print_state_probabilities("Y applied to |1>:", apply_gate(ket_one(), "Y"))

    print("The phase is not visible in computational-basis probabilities,")
    print("but it becomes important when later gates cause interference.")


def demonstrate_z_gate() -> None:
    print("=" * 72)
    print("4. Z GATE")
    print("=" * 72)

    print("The Pauli-Z gate leaves |0> unchanged and changes the sign")
    print("of the |1> amplitude:")
    print()
    print("Z|0> = |0>")
    print("Z|1> = -|1>")
    print()

    print_state_probabilities("Z applied to |0>:", apply_gate(ket_zero(), "Z"))
    print_state_probabilities("Z applied to |1>:", apply_gate(ket_one(), "Z"))


def demonstrate_identity_gate() -> None:
    print("=" * 72)
    print("5. IDENTITY GATE")
    print("=" * 72)

    state = Qubit(0.6, 0.8)

    print("The identity gate performs no state transformation:")
    print("I|psi> = |psi>")
    print()

    result = apply_gate(state, "I")

    print_state_probabilities("Original state:", state)
    print_state_probabilities("After I:", result)


# ---------------------------------------------------------------------------
# Superposition and phase
# ---------------------------------------------------------------------------

def demonstrate_superposition() -> None:
    print("=" * 72)
    print("6. SUPERPOSITION")
    print("=" * 72)

    state = plus_state()

    print_state_probabilities("|+>:", state)
    print_state_probabilities("X|+>:", apply_gate(state, "X"))

    print(
        "X leaves |+> unchanged because |+> is an eigenstate of X "
        "with eigenvalue +1."
    )
    print()


def demonstrate_phase_interference() -> None:
    print("=" * 72)
    print("7. RELATIVE PHASE AND INTERFERENCE")
    print("=" * 72)

    plus = plus_state()
    minus = minus_state()

    print_state_probabilities("|+>:", plus)
    print_state_probabilities("|->:", minus)

    print("Z transforms the states:")
    print_state_probabilities("Z|+>:", apply_gate(plus, "Z"))
    print_state_probabilities("Z|->:", apply_gate(minus, "Z"))

    print(
        "Both |+> and |-> have the same computational-basis probabilities, "
        "but their relative phases differ."
    )
    print()


def demonstrate_global_phase() -> None:
    print("=" * 72)
    print("8. GLOBAL PHASE")
    print("=" * 72)

    state = plus_state()

    global_phase_state = Qubit(
        -state.alpha,
        -state.beta,
    )

    print("Original state:")
    print(f"  {state}")
    print()

    print("State multiplied by global phase -1:")
    print(f"  {global_phase_state}")
    print()

    print("Both states have identical measurement probabilities:")
    print(
        f"  Original: {state.probabilities()}"
    )
    print(
        f"  Global phase: {global_phase_state.probabilities()}"
    )
    print()

    print(
        "A global phase cannot be detected by measurement alone, while "
        "relative phase can affect interference."
    )
    print()


# ---------------------------------------------------------------------------
# Gate composition
# ---------------------------------------------------------------------------

def compose_gates(first: Matrix, second: Matrix) -> Matrix:
    """
    Return the matrix corresponding to:

        second(first(|psi>))

    Therefore the resulting matrix is second * first.
    """
    return matrix_multiply(second, first)


def demonstrate_gate_composition() -> None:
    print("=" * 72)
    print("9. GATE COMPOSITION")
    print("=" * 72)

    state = ket_zero()

    sequential = apply_gate(apply_gate(state, "X"), "Z")

    combined_gate = compose_gates(X_GATE, Z_GATE)
    combined = state.apply(combined_gate)

    print("Starting state: |0>")
    print("Sequence: X followed by Z")
    print(f"Sequential result: {sequential}")
    print(f"Combined result:   {combined}")
    print()

    print(
        "Matrix multiplication encodes the complete sequence into one "
        "operator."
    )
    print()


def demonstrate_non_commutativity() -> None:
    print("=" * 72)
    print("10. NON-COMMUTATIVITY")
    print("=" * 72)

    state = plus_state()

    xy = apply_gate(apply_gate(state, "X"), "Y")
    yx = apply_gate(apply_gate(state, "Y"), "X")

    print("For quantum gates, order can matter.")
    print()
    print("Y(X|+>):")
    print(f"  {xy}")
    print()
    print("X(Y|+>):")
    print(f"  {yx}")
    print()

    xy_matrix = compose_gates(X_GATE, Y_GATE)
    yx_matrix = compose_gates(Y_GATE, X_GATE)

    print(
        "Are YX and XY identical matrices?",
        matrices_are_close(xy_matrix, yx_matrix),
    )
    print()


# ---------------------------------------------------------------------------
# Unitarity and inverse operations
# ---------------------------------------------------------------------------

def is_unitary(matrix: Matrix) -> bool:
    """Check whether U†U = I."""
    validate_matrix(matrix)

    rows, columns = matrix_shape(matrix)

    if rows != columns:
        return False

    conjugate = conjugate_transpose(matrix)
    product = matrix_multiply(conjugate, matrix)
    expected = identity_matrix(rows)

    return matrices_are_close(product, expected)


def demonstrate_unitarity() -> None:
    print("=" * 72)
    print("11. UNITARITY")
    print("=" * 72)

    for name, gate in GATES.items():
        print(f"{name} is unitary: {is_unitary(gate)}")

    print()
    print(
        "Unitary transformations preserve vector norms and therefore "
        "preserve total probability."
    )
    print()


def demonstrate_inverses() -> None:
    print("=" * 72)
    print("12. GATE INVERSES")
    print("=" * 72)

    print("For X, Y, and Z:")
    print("X^2 = I")
    print("Y^2 = I")
    print("Z^2 = I")
    print()

    for name in ("X", "Y", "Z"):
        square = matrix_multiply(GATES[name], GATES[name])
        print(
            f"{name}^2 = I:",
            matrices_are_close(square, IDENTITY),
        )

    print()


# ---------------------------------------------------------------------------
# Bloch-sphere representation
# ---------------------------------------------------------------------------

def bloch_coordinates(state: Qubit) -> Tuple[float, float, float]:
    """
    Compute Bloch-vector coordinates.

    For |psi> = alpha|0> + beta|1>:

        x = 2 Re(alpha* beta)
        y = 2 Im(alpha* beta)
        z = |alpha|^2 - |beta|^2

    where alpha* is the complex conjugate of alpha.
    """
    alpha = state.alpha
    beta = state.beta

    x = 2.0 * (alpha.conjugate() * beta).real
    y = 2.0 * (alpha.conjugate() * beta).imag
    z = abs(alpha) ** 2 - abs(beta) ** 2

    return x, y, z


def demonstrate_bloch_sphere() -> None:
    print("=" * 72)
    print("13. BLOCH-SPHERE INTERPRETATION")
    print("=" * 72)

    states = {
        "|0>": ket_zero(),
        "|1>": ket_one(),
        "|+>": plus_state(),
        "|->": minus_state(),
        "|+i>": plus_i_state(),
        "|-i>": minus_i_state(),
    }

    for name, state in states.items():
        x, y, z = bloch_coordinates(state)
        print(
            f"{name:4s} -> "
            f"(x={x:+.4f}, y={y:+.4f}, z={z:+.4f})"
        )

    print()
    print(
        "The X, Y, and Z gates correspond to rotations by pi radians "
        "around the respective Bloch-sphere axes, up to the physically "
        "irrelevant global phase convention."
    )
    print()


# ---------------------------------------------------------------------------
# Measurement simulation
# ---------------------------------------------------------------------------

def simulate_measurements(
    state: Qubit,
    shots: int = DEFAULT_SHOTS,
    seed: int = 42,
) -> Tuple[int, int]:
    """
    Simulate repeated computational-basis measurements.

    A fixed seed makes the educational demonstration reproducible.
    """
    if shots <= 0:
        raise ValueError("Number of shots must be positive.")

    rng = random.Random(seed)

    zero_count = 0
    one_count = 0

    for _ in range(shots):
        outcome = 0 if rng.random() < state.probability_zero else 1

        if outcome == 0:
            zero_count += 1
        else:
            one_count += 1

    return zero_count, one_count


def demonstrate_measurement_statistics() -> None:
    print("=" * 72)
    print("14. MEASUREMENT STATISTICS")
    print("=" * 72)

    state = plus_state()

    zero_count, one_count = simulate_measurements(
        state,
        shots=10_000,
        seed=12345,
    )

    print("State: |+>")
    print(f"Expected P(0): {state.probability_zero:.4f}")
    print(f"Expected P(1): {state.probability_one:.4f}")
    print()
    print(f"Observed zeros: {zero_count}")
    print(f"Observed ones:  {one_count}")
    print(f"Observed P(0): {zero_count / 10_000:.4f}")
    print(f"Observed P(1): {one_count / 10_000:.4f}")
    print()
    print(
        "Finite sampling does not generally produce exactly the theoretical "
        "probabilities."
    )
    print()


def demonstrate_state_collapse() -> None:
    print("=" * 72)
    print("15. MEASUREMENT COLLAPSE")
    print("=" * 72)

    state = plus_state()

    print("Before measurement:")
    print_state_probabilities("State:", state)

    rng = random.Random(7)
    outcome = state.measure(rng)

    print(f"Measured outcome: {outcome}")
    print()
    print("After measurement:")
    print_state_probabilities("Collapsed state:", state)


# ---------------------------------------------------------------------------
# Pauli expectation values
# ---------------------------------------------------------------------------

def expectation_value(state: Qubit, operator: Matrix) -> complex:
    """
    Compute <psi|O|psi> for a single qubit.

    This is useful for understanding measurements associated with
    Pauli observables.
    """
    transformed = matrix_vector_multiply(operator, state.vector)

    bra = [state.alpha.conjugate(), state.beta.conjugate()]

    return sum(
        bra[index] * transformed[index]
        for index in range(2)
    )


def demonstrate_expectation_values() -> None:
    print("=" * 72)
    print("16. PAULI EXPECTATION VALUES")
    print("=" * 72)

    states = {
        "|0>": ket_zero(),
        "|1>": ket_one(),
        "|+>": plus_state(),
        "|->": minus_state(),
        "|+i>": plus_i_state(),
        "|-i>": minus_i_state(),
    }

    for state_name, state in states.items():
        x_value = expectation_value(state, X_GATE)
        y_value = expectation_value(state, Y_GATE)
        z_value = expectation_value(state, Z_GATE)

        print(
            f"{state_name:4s}: "
            f"<X>={x_value.real:+.4f}, "
            f"<Y>={y_value.real:+.4f}, "
            f"<Z>={z_value.real:+.4f}"
        )

    print()


# ---------------------------------------------------------------------------
# Multiple-qubit tensor products
# ---------------------------------------------------------------------------

def tensor_product(
    left: Sequence[complex],
    right: Sequence[complex],
) -> List[complex]:
    """
    Compute the Kronecker/tensor product of two vectors.

    If:
        |a> = [a0, a1]
        |b> = [b0, b1]

    then:
        |a> ⊗ |b>
        = [a0b0, a0b1, a1b0, a1b1]
    """
    result = []

    for left_value in left:
        for right_value in right:
            result.append(left_value * right_value)

    return result


def tensor_matrix(
    left: Matrix,
    right: Matrix,
) -> Matrix:
    """Compute the Kronecker product of two matrices."""
    validate_matrix(left)
    validate_matrix(right)

    left_rows, left_columns = matrix_shape(left)
    right_rows, right_columns = matrix_shape(right)

    result: Matrix = [
        [
            0j
            for _ in range(left_columns * right_columns)
        ]
        for _ in range(left_rows * right_rows)
    ]

    for i in range(left_rows):
        for j in range(left_columns):
            for k in range(right_rows):
                for l in range(right_columns):
                    result[
                        i * right_rows + k
                    ][
                        j * right_columns + l
                    ] = left[i][j] * right[k][l]

    return result


def demonstrate_two_qubit_states() -> None:
    print("=" * 72)
    print("17. TWO-QUBIT TENSOR PRODUCTS")
    print("=" * 72)

    zero_zero = tensor_product(ket_zero().vector, ket_zero().vector)
    zero_one = tensor_product(ket_zero().vector, ket_one().vector)
    plus_plus = tensor_product(plus_state().vector, plus_state().vector)

    print("|00> amplitudes:")
    print([format_complex(value) for value in zero_zero])
    print()

    print("|01> amplitudes:")
    print([format_complex(value) for value in zero_one])
    print()

    print("|++> amplitudes:")
    print([format_complex(value) for value in plus_plus])
    print()

    print(
        "For two qubits, the computational basis contains four states:"
    )
    print("|00>, |01>, |10>, |11>")
    print()


def demonstrate_bell_state() -> None:
    print("=" * 72)
    print("18. A BELL-STATE EXAMPLE")
    print("=" * 72)

    print(
        "The Bell state |Phi+> = (|00> + |11>) / sqrt(2) is an entangled "
        "two-qubit state."
    )
    print()

    bell_state = [
        1 / SQRT_TWO,
        0j,
        0j,
        1 / SQRT_TWO,
    ]

    labels = ["|00>", "|01>", "|10>", "|11>"]

    for label, amplitude in zip(labels, bell_state):
        print(
            f"{label}: amplitude={format_complex(amplitude)}, "
            f"probability={probability_from_amplitude(amplitude):.4f}"
        )

    print()
    print(
        "A computational-basis measurement produces either 00 or 11, "
        "with equal theoretical probabilities."
    )
    print()


# ---------------------------------------------------------------------------
# Quantum teleportation building blocks
# ---------------------------------------------------------------------------

def demonstrate_teleportation_relation() -> None:
    print("=" * 72)
    print("19. TELEPORTATION BUILDING BLOCKS")
    print("=" * 72)

    print(
        "Quantum teleportation uses entanglement together with single-qubit "
        "operations and classical communication."
    )
    print()

    print("Important single-qubit gates appearing in standard circuits:")
    print("  X: computational bit flip")
    print("  Y: bit flip plus phase")
    print("  Z: phase flip")
    print("  I: identity/no operation")
    print()

    print(
        "The full teleportation protocol also requires multi-qubit gates, "
        "especially CNOT, which is outside the four-gate focus of this study."
    )
    print()


# ---------------------------------------------------------------------------
# Edge cases and failure conditions
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("=" * 72)
    print("20. EDGE CASES AND VALIDATION")
    print("=" * 72)

    examples = [
        (
            "Invalid single-qubit vector",
            lambda: validate_state([1 + 0j, 1 + 0j]),
        ),
        (
            "Zero vector normalization",
            lambda: normalize_vector([0j, 0j]),
        ),
        (
            "Wrong gate size",
            lambda: ket_zero().apply([[1 + 0j]]),
        ),
        (
            "Unknown gate",
            lambda: apply_gate(ket_zero(), "H"),
        ),
        (
            "Invalid measurement shot count",
            lambda: simulate_measurements(ket_zero(), 0),
        ),
    ]

    for description, operation in examples:
        try:
            operation()
            print(f"{description}: unexpectedly succeeded")
        except (ValueError, TypeError, KeyError) as error:
            print(f"{description}: correctly rejected")
            print(f"  Reason: {error}")

    print()


# ---------------------------------------------------------------------------
# Gate tables
# ---------------------------------------------------------------------------

def print_gate_matrix(name: str, matrix: Matrix) -> None:
    """Display a small matrix."""
    print(f"{name} =")

    for row in matrix:
        formatted = "  ".join(
            f"{format_complex(value):>15}"
            for value in row
        )
        print(f"  {formatted}")

    print()


def demonstrate_gate_matrices() -> None:
    print("=" * 72)
    print("21. STANDARD GATE MATRICES")
    print("=" * 72)

    for name in ("I", "X", "Y", "Z"):
        print_gate_matrix(name, GATES[name])


# ---------------------------------------------------------------------------
# Transformation table
# ---------------------------------------------------------------------------

def demonstrate_transformation_table() -> None:
    print("=" * 72)
    print("22. BASIS-STATE TRANSFORMATION TABLE")
    print("=" * 72)

    basis_states = {
        "|0>": ket_zero(),
        "|1>": ket_one(),
    }

    for gate_name in ("I", "X", "Y", "Z"):
        print(f"{gate_name} gate:")

        for state_name, state in basis_states.items():
            transformed = apply_gate(state, gate_name)
            print(f"  {state_name:4s} -> {transformed}")

        print()


# ---------------------------------------------------------------------------
# Automated correctness tests
# ---------------------------------------------------------------------------

def assert_state_equal(
    actual: Qubit,
    expected: Qubit,
    tolerance: float = EPSILON,
) -> None:
    """Assert equality of two qubit state vectors."""
    if not (
        abs(actual.alpha - expected.alpha) <= tolerance
        and abs(actual.beta - expected.beta) <= tolerance
    ):
        raise AssertionError(
            f"States differ:\nActual: {actual}\nExpected: {expected}"
        )


def run_tests() -> None:
    print("=" * 72)
    print("23. AUTOMATED TESTS")
    print("=" * 72)

    assert_state_equal(
        apply_gate(ket_zero(), "I"),
        ket_zero(),
    )

    assert_state_equal(
        apply_gate(ket_zero(), "X"),
        ket_one(),
    )

    assert_state_equal(
        apply_gate(ket_one(), "X"),
        ket_zero(),
    )

    assert_state_equal(
        apply_gate(ket_zero(), "Y"),
        Qubit(0, 1j),
    )

    assert_state_equal(
        apply_gate(ket_one(), "Y"),
        Qubit(-1j, 0),
    )

    assert_state_equal(
        apply_gate(ket_zero(), "Z"),
        ket_zero(),
    )

    assert_state_equal(
        apply_gate(ket_one(), "Z"),
        Qubit(0, -1),
    )

    for name in ("I", "X", "Y", "Z"):
        assert is_unitary(GATES[name])

    for name in ("X", "Y", "Z"):
        square = matrix_multiply(GATES[name], GATES[name])
        assert matrices_are_close(square, IDENTITY)

    assert math.isclose(
        sum(abs(value) ** 2 for value in plus_state().vector),
        1.0,
        abs_tol=EPSILON,
    )

    x_expectation = expectation_value(plus_state(), X_GATE)
    assert math.isclose(x_expectation.real, 1.0, abs_tol=EPSILON)

    z_expectation = expectation_value(ket_zero(), Z_GATE)
    assert math.isclose(z_expectation.real, 1.0, abs_tol=EPSILON)

    print("All quantum-gate tests passed.")
    print()


# ---------------------------------------------------------------------------
# Performance discussion through executable measurements
# ---------------------------------------------------------------------------

def benchmark_single_qubit_operations() -> None:
    print("=" * 72)
    print("24. SMALL PERFORMANCE EXPERIMENT")
    print("=" * 72)

    import time

    iterations = 100_000
    state = plus_state()

    start = time.perf_counter()

    for _ in range(iterations):
        state = state.apply(X_GATE)

    elapsed = time.perf_counter() - start

    print(f"Operations: {iterations:,}")
    print(f"Elapsed time: {elapsed:.6f} seconds")
    print(f"Operations/second: {iterations / elapsed:,.0f}")
    print()

    print(
        "This implementation uses ordinary Python lists and complex numbers. "
        "For large quantum simulations, dense state vectors require memory "
        "that grows exponentially with the number of qubits."
    )
    print()


# ---------------------------------------------------------------------------
# Study guide
# ---------------------------------------------------------------------------

def print_concept_reference() -> None:
    print("=" * 72)
    print("25. QUICK CONCEPT REFERENCE")
    print("=" * 72)

    reference = [
        ("Qubit", "A two-level quantum system."),
        ("|0>", "Computational basis state with amplitude [1, 0]."),
        ("|1>", "Computational basis state with amplitude [0, 1]."),
        ("Amplitude", "A complex coefficient of a quantum state."),
        ("Born rule", "Measurement probability equals squared amplitude magnitude."),
        ("X gate", "Pauli-X bit-flip gate."),
        ("Y gate", "Pauli-Y bit-and-phase-flip gate."),
        ("Z gate", "Pauli-Z phase-flip gate."),
        ("I gate", "Identity operation."),
        ("Unitary", "A transformation preserving inner products and norms."),
        ("Global phase", "A common phase multiplying the complete state."),
        ("Relative phase", "Phase difference between components of a state."),
        ("Superposition", "A linear combination of basis states."),
        ("Measurement", "A process producing classical outcomes."),
        ("Bloch sphere", "Geometric representation of a pure single-qubit state."),
        ("Tensor product", "Operation used to construct composite quantum systems."),
    ]

    for term, explanation in reference:
        print(f"{term:20s} : {explanation}")

    print()


# ---------------------------------------------------------------------------
# Main educational program
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("#" * 72)
    print("QUANTUM GATES: X, Y, Z, AND IDENTITY")
    print("#" * 72)
    print()
    print(
        "This executable study file develops the mathematics and programming "
        "ideas behind four fundamental single-qubit gates."
    )
    print()

    demonstrate_basis_states()
    demonstrate_gate_matrices()
    demonstrate_x_gate()
    demonstrate_y_gate()
    demonstrate_z_gate()
    demonstrate_identity_gate()
    demonstrate_superposition()
    demonstrate_phase_interference()
    demonstrate_global_phase()
    demonstrate_gate_composition()
    demonstrate_non_commutativity()
    demonstrate_unitarity()
    demonstrate_inverses()
    demonstrate_bloch_sphere()
    demonstrate_measurement_statistics()
    demonstrate_state_collapse()
    demonstrate_expectation_values()
    demonstrate_two_qubit_states()
    demonstrate_bell_state()
    demonstrate_teleportation_relation()
    demonstrate_edge_cases()
    demonstrate_transformation_table()
    run_tests()
    benchmark_single_qubit_operations()
    print_concept_reference()

    print("=" * 72)
    print("END OF STUDY PROGRAM")
    print("=" * 72)


if __name__ == "__main__":
    main()
