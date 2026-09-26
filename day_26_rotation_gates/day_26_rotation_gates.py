"""
Rotation Gates: RX, RY, RZ
==========================

A standalone study program for learning single-qubit rotation gates from
beginner to advanced level.

Topics covered:
- Qubits and computational basis states
- Complex amplitudes and normalization
- Bloch sphere representation
- Rotation gates RX, RY, RZ
- Matrix representations
- State-vector application
- Measurement probabilities
- Global and relative phase
- Euler-angle decomposition
- Gate composition and order
- Non-commutativity
- Expectation values
- Numerical precision
- Parameterized rotations
- Rotation periodicity
- Inverse rotations
- Conjugation relationships
- Circuit simulation
- Validation and edge cases
- Fidelity and state comparison
- Practical optimization considerations

No external packages are required.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Fundamental constants and numerical helpers
# ---------------------------------------------------------------------------

EPSILON = 1e-10
PI = math.pi
TAU = 2.0 * math.pi


def nearly_equal(a: float, b: float, tolerance: float = EPSILON) -> bool:
    """Return True when two real numbers are numerically close."""
    return abs(a - b) <= tolerance


def complex_nearly_equal(
    a: complex,
    b: complex,
    tolerance: float = EPSILON,
) -> bool:
    """Return True when two complex numbers are numerically close."""
    return abs(a - b) <= tolerance


def wrap_angle(angle: float) -> float:
    """
    Wrap an angle into the interval [-pi, pi).

    Quantum rotations are periodic. For example:
        RY(theta + 2*pi) = RY(theta)
    """
    wrapped = (angle + PI) % TAU - PI
    if wrapped == PI:
        return -PI
    return wrapped


def format_complex(value: complex, digits: int = 5) -> str:
    """Produce compact human-readable complex-number output."""
    real = 0.0 if abs(value.real) < 10 ** (-digits) else value.real
    imag = 0.0 if abs(value.imag) < 10 ** (-digits) else value.imag

    if abs(imag) < 10 ** (-digits):
        return f"{real:.{digits}f}"

    if abs(real) < 10 ** (-digits):
        return f"{imag:.{digits}f}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.{digits}f} {sign} {abs(imag):.{digits}f}i"


def print_matrix(matrix: Sequence[Sequence[complex]], name: str = "Matrix") -> None:
    """Print a small complex matrix in a readable form."""
    print(f"\n{name}:")
    for row in matrix:
        print("  [ " + " , ".join(format_complex(x) for x in row) + " ]")


def print_state(state: "QubitState", label: str = "State") -> None:
    """Print a qubit state in vector and Dirac notation."""
    alpha, beta = state.amplitudes
    print(
        f"\n{label}: "
        f"{format_complex(alpha)}|0> + {format_complex(beta)}|1>"
    )
    print(
        f"  P(0) = {state.probability_zero():.6f}, "
        f"P(1) = {state.probability_one():.6f}"
    )
    print(
        f"  Bloch vector = "
        f"({state.bloch_vector()[0]:.6f}, "
        f"{state.bloch_vector()[1]:.6f}, "
        f"{state.bloch_vector()[2]:.6f})"
    )


# ---------------------------------------------------------------------------
# Basic linear-algebra operations
# ---------------------------------------------------------------------------

Matrix2 = tuple[tuple[complex, complex], tuple[complex, complex]]
Vector2 = tuple[complex, complex]


def matrix_multiply(a: Matrix2, b: Matrix2) -> Matrix2:
    """Multiply two 2x2 complex matrices."""
    return (
        (
            a[0][0] * b[0][0] + a[0][1] * b[1][0],
            a[0][0] * b[0][1] + a[0][1] * b[1][1],
        ),
        (
            a[1][0] * b[0][0] + a[1][1] * b[1][0],
            a[1][0] * b[0][1] + a[1][1] * b[1][1],
        ),
    )


def matrix_vector_multiply(matrix: Matrix2, vector: Vector2) -> Vector2:
    """Multiply a 2x2 matrix by a two-component state vector."""
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def conjugate_transpose(matrix: Matrix2) -> Matrix2:
    """Return the Hermitian adjoint U†."""
    return (
        (matrix[0][0].conjugate(), matrix[1][0].conjugate()),
        (matrix[0][1].conjugate(), matrix[1][1].conjugate()),
    )


def identity_matrix() -> Matrix2:
    return (
        (1 + 0j, 0 + 0j),
        (0 + 0j, 1 + 0j),
    )


def matrix_difference_norm(a: Matrix2, b: Matrix2) -> float:
    """Frobenius norm of the difference between two 2x2 matrices."""
    total = 0.0
    for row in range(2):
        for column in range(2):
            total += abs(a[row][column] - b[row][column]) ** 2
    return math.sqrt(total)


def is_unitary(matrix: Matrix2, tolerance: float = 1e-9) -> bool:
    """Check whether U†U is approximately the identity matrix."""
    product = matrix_multiply(conjugate_transpose(matrix), matrix)
    return matrix_difference_norm(product, identity_matrix()) <= tolerance


# ---------------------------------------------------------------------------
# Qubit state representation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QubitState:
    """
    A single-qubit state.

    A normalized pure qubit has the form

        |psi> = alpha|0> + beta|1>

    with

        |alpha|² + |beta|² = 1.

    The amplitudes can be complex numbers. Their phases are physically
    important when they are relative to one another.
    """

    alpha: complex
    beta: complex

    def __post_init__(self) -> None:
        norm_squared = abs(self.alpha) ** 2 + abs(self.beta) ** 2
        if abs(norm_squared - 1.0) > 1e-9:
            raise ValueError(
                "QubitState must be normalized: "
                "|alpha|^2 + |beta|^2 must equal 1."
            )

    @property
    def amplitudes(self) -> Vector2:
        return self.alpha, self.beta

    @staticmethod
    def zero() -> "QubitState":
        """Computational basis state |0>."""
        return QubitState(1 + 0j, 0 + 0j)

    @staticmethod
    def one() -> "QubitState":
        """Computational basis state |1>."""
        return QubitState(0 + 0j, 1 + 0j)

    @staticmethod
    def plus() -> "QubitState":
        """|+> = (|0> + |1>) / sqrt(2)."""
        amplitude = 1 / math.sqrt(2)
        return QubitState(amplitude + 0j, amplitude + 0j)

    @staticmethod
    def minus() -> "QubitState":
        """|-> = (|0> - |1>) / sqrt(2)."""
        amplitude = 1 / math.sqrt(2)
        return QubitState(amplitude + 0j, -amplitude + 0j)

    @staticmethod
    def from_bloch(theta: float, phi: float) -> "QubitState":
        """
        Construct a pure state from Bloch-sphere angles:

            |psi> = cos(theta/2)|0>
                    + exp(i*phi) sin(theta/2)|1>

        theta controls latitude/polar angle.
        phi controls azimuthal angle.
        """
        alpha = math.cos(theta / 2)
        beta = cmath.exp(1j * phi) * math.sin(theta / 2)
        return QubitState(alpha + 0j, beta)

    def normalized(self) -> "QubitState":
        """Return a normalized copy, useful for numerical calculations."""
        norm = math.sqrt(abs(self.alpha) ** 2 + abs(self.beta) ** 2)
        if norm < EPSILON:
            raise ValueError("Cannot normalize a zero vector.")
        return QubitState(self.alpha / norm, self.beta / norm)

    def apply(self, gate: Matrix2) -> "QubitState":
        """Apply a 2x2 unitary gate to this qubit."""
        if not is_unitary(gate):
            raise ValueError("The supplied matrix is not approximately unitary.")

        alpha, beta = matrix_vector_multiply(gate, self.amplitudes)
        return QubitState(alpha, beta).normalized()

    def probability_zero(self) -> float:
        return abs(self.alpha) ** 2

    def probability_one(self) -> float:
        return abs(self.beta) ** 2

    def measurement_probabilities(self) -> tuple[float, float]:
        return self.probability_zero(), self.probability_one()

    def bloch_vector(self) -> tuple[float, float, float]:
        """
        Convert a pure-state vector into Bloch coordinates.

        x = 2 Re(alpha* beta)
        y = 2 Im(alpha* beta)
        z = |alpha|² - |beta|²
        """
        coherence = self.alpha.conjugate() * self.beta
        x = 2.0 * coherence.real
        y = 2.0 * coherence.imag
        z = abs(self.alpha) ** 2 - abs(self.beta) ** 2
        return x, y, z

    def relative_phase(self) -> float:
        """
        Return phase(beta) - phase(alpha).

        If either amplitude is zero, the relative phase is not uniquely
        defined from that computational-basis representation.
        """
        if abs(self.alpha) < EPSILON or abs(self.beta) < EPSILON:
            raise ValueError(
                "Relative phase is undefined when one computational-basis "
                "amplitude is zero."
            )
        return cmath.phase(self.beta) - cmath.phase(self.alpha)

    def global_phase_adjusted(self, phase: float) -> "QubitState":
        """
        Multiply the complete state by a global phase.

        Global phase cannot be observed by itself, but retaining it here
        helps demonstrate the distinction between global and relative phase.
        """
        factor = cmath.exp(1j * phase)
        return QubitState(self.alpha * factor, self.beta * factor)


# ---------------------------------------------------------------------------
# Pauli matrices and elementary gates
# ---------------------------------------------------------------------------

I: Matrix2 = (
    (1 + 0j, 0 + 0j),
    (0 + 0j, 1 + 0j),
)

X: Matrix2 = (
    (0 + 0j, 1 + 0j),
    (1 + 0j, 0 + 0j),
)

Y: Matrix2 = (
    (0 + 0j, -1j),
    (1j, 0 + 0j),
)

Z: Matrix2 = (
    (1 + 0j, 0 + 0j),
    (0 + 0j, -1 + 0j),
)


def rx(theta: float) -> Matrix2:
    """
    Rotation around the x-axis:

        RX(theta) = exp(-i * theta * X / 2)

                 [ cos(theta/2)       -i sin(theta/2) ]
                 [ -i sin(theta/2)      cos(theta/2) ]

    """
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return (
        (complex(c), -1j * s),
        (-1j * s, complex(c)),
    )


def ry(theta: float) -> Matrix2:
    """
    Rotation around the y-axis:

        RY(theta) = exp(-i * theta * Y / 2)

                 [ cos(theta/2)  -sin(theta/2) ]
                 [ sin(theta/2)   cos(theta/2) ]
    """
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return (
        (complex(c), complex(-s)),
        (complex(s), complex(c)),
    )


def rz(theta: float) -> Matrix2:
    """
    Rotation around the z-axis:

        RZ(theta) = exp(-i * theta * Z / 2)

                 [ exp(-i theta/2)       0       ]
                 [       0          exp(i theta/2) ]
    """
    return (
        (cmath.exp(-1j * theta / 2), 0 + 0j),
        (0 + 0j, cmath.exp(1j * theta / 2)),
    )


# ---------------------------------------------------------------------------
# General rotation and Euler decomposition
# ---------------------------------------------------------------------------

def general_axis_rotation(
    axis: tuple[float, float, float],
    angle: float,
) -> Matrix2:
    """
    Build a rotation about an arbitrary normalized Bloch-sphere axis.

        R_n(theta) = exp(-i theta (n·sigma)/2)

    where sigma = (X, Y, Z).

    The closed form is:

        R_n(theta) =
            cos(theta/2) I
            - i sin(theta/2)(nx X + ny Y + nz Z)
    """
    nx, ny, nz = axis
    length = math.sqrt(nx * nx + ny * ny + nz * nz)

    if length < EPSILON:
        raise ValueError("Rotation axis cannot be the zero vector.")

    nx /= length
    ny /= length
    nz /= length

    half = angle / 2
    c = math.cos(half)
    s = math.sin(half)

    sigma_n = (
        (
            complex(nz),
            complex(nx, -ny),
        ),
        (
            complex(nx, ny),
            complex(-nz),
        ),
    )

    result = (
        (
            complex(c) - 1j * s * sigma_n[0][0],
            -1j * s * sigma_n[0][1],
        ),
        (
            -1j * s * sigma_n[1][0],
            complex(c) - 1j * s * sigma_n[1][1],
        ),
    )
    return result


def u3(theta: float, phi: float, lam: float) -> Matrix2:
    """
    Standard U3 parameterization:

        U3(theta, phi, lambda)

    = RZ(phi) RY(theta) RZ(lambda)

    up to the exact convention represented by these matrices.
    """
    return matrix_multiply(
        matrix_multiply(rz(phi), ry(theta)),
        rz(lam),
    )


def equivalent_up_to_global_phase(
    a: Matrix2,
    b: Matrix2,
    tolerance: float = 1e-9,
) -> bool:
    """
    Test whether two matrices differ only by a global phase.

    If b[0][0] is nonzero, estimate the phase from that element.
    If not, search for another nonzero pair.
    """
    reference_ratio: complex | None = None

    for row in range(2):
        for column in range(2):
            av = a[row][column]
            bv = b[row][column]

            if abs(bv) > tolerance:
                ratio = av / bv
                if reference_ratio is None:
                    if abs(abs(ratio) - 1.0) > tolerance:
                        return False
                    reference_ratio = ratio
                elif abs(ratio - reference_ratio) > tolerance:
                    return False
            elif abs(av) > tolerance:
                return False

    return True


# ---------------------------------------------------------------------------
# Gate sequences and circuit utilities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateOperation:
    name: str
    matrix: Matrix2
    angle: float | None = None


class QubitCircuit:
    """Small educational single-qubit circuit simulator."""

    def __init__(self, initial_state: QubitState | None = None) -> None:
        self.initial_state = initial_state or QubitState.zero()
        self.operations: list[GateOperation] = []

    def add_rx(self, angle: float) -> "QubitCircuit":
        self.operations.append(GateOperation("RX", rx(angle), angle))
        return self

    def add_ry(self, angle: float) -> "QubitCircuit":
        self.operations.append(GateOperation("RY", ry(angle), angle))
        return self

    def add_rz(self, angle: float) -> "QubitCircuit":
        self.operations.append(GateOperation("RZ", rz(angle), angle))
        return self

    def add_matrix(self, name: str, matrix: Matrix2) -> "QubitCircuit":
        if not is_unitary(matrix):
            raise ValueError(f"{name} is not unitary.")
        self.operations.append(GateOperation(name, matrix))
        return self

    def run(self) -> QubitState:
        state = self.initial_state
        for operation in self.operations:
            state = state.apply(operation.matrix)
        return state

    def combined_unitary(self) -> Matrix2:
        """
        Return the circuit unitary.

        For operations G1, G2, G3 applied in that order to a state,

            |psi_final> = G3 G2 G1 |psi_initial>.

        Therefore the new operation is multiplied on the left.
        """
        combined = I
        for operation in self.operations:
            combined = matrix_multiply(operation.matrix, combined)
        return combined

    def describe(self) -> None:
        print("\nCircuit:")
        if not self.operations:
            print("  <empty>")
            return

        for index, operation in enumerate(self.operations, start=1):
            if operation.angle is None:
                print(f"  {index}. {operation.name}")
            else:
                print(
                    f"  {index}. {operation.name}"
                    f"({operation.angle:.6f} radians)"
                )


# ---------------------------------------------------------------------------
# Measurement simulation
# ---------------------------------------------------------------------------

def sample_measurement(
    state: QubitState,
    shots: int,
    seed: int | None = None,
) -> dict[int, int]:
    """
    Simulate computational-basis measurements.

    This samples according to the Born rule:
        P(0) = |alpha|²
        P(1) = |beta|²
    """
    if shots <= 0:
        raise ValueError("shots must be a positive integer.")

    rng = random.Random(seed)
    probability_zero = state.probability_zero()

    counts = {0: 0, 1: 0}
    for _ in range(shots):
        result = 0 if rng.random() < probability_zero else 1
        counts[result] += 1

    return counts


# ---------------------------------------------------------------------------
# Expectation values
# ---------------------------------------------------------------------------

def expectation_value(state: QubitState, observable: Matrix2) -> float:
    """
    Compute <psi|A|psi> for a Hermitian observable A.

    For Pauli operators:
        <X> = x
        <Y> = y
        <Z> = z
    """
    transformed = matrix_vector_multiply(observable, state.amplitudes)
    value = (
        state.alpha.conjugate() * transformed[0]
        + state.beta.conjugate() * transformed[1]
    )

    if abs(value.imag) > 1e-8:
        raise ValueError(
            "Expectation value has a significant imaginary component; "
            "the supplied observable may not be Hermitian."
        )

    return value.real


# ---------------------------------------------------------------------------
# Fidelity and state equivalence
# ---------------------------------------------------------------------------

def state_fidelity(a: QubitState, b: QubitState) -> float:
    """
    Fidelity between two pure states:

        F = |<a|b>|²

    F = 1 means the states are physically identical up to global phase.
    """
    inner_product = (
        a.alpha.conjugate() * b.alpha
        + a.beta.conjugate() * b.beta
    )
    return abs(inner_product) ** 2


def states_equivalent_up_to_global_phase(
    a: QubitState,
    b: QubitState,
    tolerance: float = 1e-9,
) -> bool:
    return state_fidelity(a, b) >= 1.0 - tolerance


# ---------------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def demonstrate_fundamentals() -> None:
    section("1. QUBIT FUNDAMENTALS")

    zero = QubitState.zero()
    one = QubitState.one()
    plus = QubitState.plus()
    minus = QubitState.minus()

    print_state(zero, "|0>")
    print_state(one, "|1>")
    print_state(plus, "|+>")
    print_state(minus, "|->")

    print(
        "\nA pure qubit is alpha|0> + beta|1>, where "
        "|alpha|² + |beta|² = 1."
    )


def demonstrate_rotation_matrices() -> None:
    section("2. RX, RY, AND RZ MATRIX REPRESENTATIONS")

    angle = PI / 2

    print_matrix(rx(angle), "RX(pi/2)")
    print_matrix(ry(angle), "RY(pi/2)")
    print_matrix(rz(angle), "RZ(pi/2)")

    print("\nAll three matrices are unitary:")
    print(f"  RX: {is_unitary(rx(angle))}")
    print(f"  RY: {is_unitary(ry(angle))}")
    print(f"  RZ: {is_unitary(rz(angle))}")

    print(
        "\nThe factor theta/2 is essential. A qubit rotation by theta on "
        "the Bloch sphere corresponds to a unitary using half-angle "
        "trigonometric terms."
    )


def demonstrate_basic_rotations() -> None:
    section("3. BASIC ROTATION EFFECTS")

    print_state(QubitState.zero(), "Initial |0>")

    state = QubitState.zero().apply(rx(PI))
    print_state(state, "RX(pi)|0>")

    state = QubitState.zero().apply(ry(PI))
    print_state(state, "RY(pi)|0>")

    state = QubitState.zero().apply(rz(PI / 2))
    print_state(state, "RZ(pi/2)|0>")

    print(
        "\nImportant observation: RZ changes phase but leaves computational "
        "basis measurement probabilities unchanged."
    )

    initial = QubitState.plus()
    after_rz = initial.apply(rz(PI / 2))

    print_state(initial, "|+>")
    print_state(after_rz, "RZ(pi/2)|+>")

    print(
        "\nRZ becomes observable when the state has coherent superposition, "
        "because it changes relative phase."
    )


def demonstrate_bloch_sphere_rotations() -> None:
    section("4. BLOCH-SPHERE INTERPRETATION")

    states = [
        ("|0>", QubitState.zero()),
        ("|1>", QubitState.one()),
        ("|+>", QubitState.plus()),
        ("|->", QubitState.minus()),
        ("|+i>", QubitState.from_bloch(PI / 2, PI / 2)),
    ]

    for name, state in states:
        print(f"{name:6s} -> {state.bloch_vector()}")

    initial = QubitState.from_bloch(PI / 3, PI / 5)
    print_state(initial, "Arbitrary initial state")

    for name, gate in (
        ("RX(pi/4)", rx(PI / 4)),
        ("RY(pi/4)", ry(PI / 4)),
        ("RZ(pi/4)", rz(PI / 4)),
    ):
        print_state(initial.apply(gate), f"After {name}")


def demonstrate_measurement() -> None:
    section("5. MEASUREMENT PROBABILITIES AND SHOT SIMULATION")

    theta = PI / 3
    state = QubitState.zero().apply(ry(theta))

    print_state(state, "RY(pi/3)|0>")

    counts = sample_measurement(state, shots=10_000, seed=42)
    print(f"\n10,000 simulated measurements: {counts}")

    empirical_zero = counts[0] / 10_000
    empirical_one = counts[1] / 10_000

    print(f"Empirical P(0): {empirical_zero:.5f}")
    print(f"Empirical P(1): {empirical_one:.5f}")


def demonstrate_non_commutativity() -> None:
    section("6. ROTATION ORDER MATTERS")

    theta = PI / 3
    phi = PI / 4

    first_rx_then_ry = (
        QubitState.zero()
        .apply(rx(theta))
        .apply(ry(phi))
    )

    first_ry_then_rx = (
        QubitState.zero()
        .apply(ry(phi))
        .apply(rx(theta))
    )

    print_state(first_rx_then_ry, "RX then RY")
    print_state(first_ry_then_rx, "RY then RX")

    fidelity = state_fidelity(first_rx_then_ry, first_ry_then_rx)
    print(f"\nFidelity between results: {fidelity:.10f}")

    print(
        "\nGenerally RX(theta)RY(phi) != RY(phi)RX(theta). "
        "Matrix multiplication is not commutative."
    )


def demonstrate_periodicity_and_inverse() -> None:
    section("7. PERIODICITY AND INVERSE ROTATIONS")

    theta = 0.73
    state = QubitState.from_bloch(PI / 2.7, -0.8)

    shifted = state.apply(ry(theta + TAU))
    original = state.apply(ry(theta))

    print(
        "RY(theta) and RY(theta + 2*pi) produce physically equivalent states:"
    )
    print(f"  Fidelity = {state_fidelity(original, shifted):.12f}")

    restored = state.apply(rx(theta)).apply(rx(-theta))
    print_state(restored, "RX(theta) followed by RX(-theta)")

    print(
        "\nFor a rotation gate, the inverse is obtained by negating the angle:"
        "\n  RX(theta)^dagger = RX(-theta)"
        "\n  RY(theta)^dagger = RY(-theta)"
        "\n  RZ(theta)^dagger = RZ(-theta)"
    )


def demonstrate_global_and_relative_phase() -> None:
    section("8. GLOBAL PHASE VERSUS RELATIVE PHASE")

    state = QubitState.from_bloch(PI / 2, PI / 3)
    globally_shifted = state.global_phase_adjusted(1.2)

    print_state(state, "Original")
    print_state(globally_shifted, "Global phase shifted")

    print(
        f"\nFidelity after global phase multiplication: "
        f"{state_fidelity(state, globally_shifted):.12f}"
    )

    print(
        "\nThe two state vectors look different algebraically, but their "
        "physical pure-state descriptions are equivalent because only the "
        "relative phase affects interference."
    )

    before = state.relative_phase()
    after = state.apply(rz(PI / 2)).relative_phase()

    print(f"\nRelative phase before RZ: {wrap_angle(before):.6f}")
    print(f"Relative phase after RZ:  {wrap_angle(after):.6f}")


def demonstrate_general_axis_rotation() -> None:
    section("9. GENERAL AXIS ROTATION")

    axis = (1.0, 1.0, 1.0)
    angle = PI / 3

    gate = general_axis_rotation(axis, angle)
    print_matrix(gate, "Rotation around normalized (1,1,1) axis")

    print(f"\nUnitary: {is_unitary(gate)}")

    state = QubitState.from_bloch(PI / 4, PI / 7)
    transformed = state.apply(gate)

    print_state(state, "Before arbitrary-axis rotation")
    print_state(transformed, "After arbitrary-axis rotation")


def demonstrate_euler_decomposition() -> None:
    section("10. EULER-ANGLE / Z-Y-Z DECOMPOSITION")

    theta = 0.8
    phi = -0.4
    lam = 1.2

    decomposed = u3(theta, phi, lam)

    print_matrix(decomposed, "RZ(phi) RY(theta) RZ(lambda)")
    print(f"\nUnitary: {is_unitary(decomposed)}")

    print(
        "\nA general single-qubit unitary can be parameterized using Euler "
        "rotations together with a possible global phase. This is why RX, "
        "RY, and RZ are fundamental building blocks for single-qubit "
        "control and circuit compilation."
    )


def demonstrate_circuit() -> None:
    section("11. PARAMETERIZED SINGLE-QUBIT CIRCUIT")

    circuit = (
        QubitCircuit(QubitState.zero())
        .add_ry(PI / 3)
        .add_rz(PI / 5)
        .add_rx(-PI / 7)
        .add_ry(0.41)
    )

    circuit.describe()
    result = circuit.run()

    print_state(result, "Circuit output")

    combined = circuit.combined_unitary()
    print_matrix(combined, "Combined circuit unitary")
    print(f"\nCombined unitary check: {is_unitary(combined)}")

    direct = QubitState.zero().apply(combined)
    print(
        f"Direct matrix application fidelity: "
        f"{state_fidelity(result, direct):.12f}"
    )


def demonstrate_expectation_values() -> None:
    section("12. EXPECTATION VALUES")

    state = QubitState.from_bloch(1.1, 0.7)

    x_expectation = expectation_value(state, X)
    y_expectation = expectation_value(state, Y)
    z_expectation = expectation_value(state, Z)

    x, y, z = state.bloch_vector()

    print_state(state, "State")
    print("\nPauli expectation values:")
    print(f"  <X> = {x_expectation:.8f}")
    print(f"  <Y> = {y_expectation:.8f}")
    print(f"  <Z> = {z_expectation:.8f}")

    print("\nBloch-vector components:")
    print(f"  x = {x:.8f}")
    print(f"  y = {y:.8f}")
    print(f"  z = {z:.8f}")


def demonstrate_edge_cases() -> None:
    section("13. EDGE CASES AND EXCEPTIONS")

    cases = [
        ("RX(0)", rx(0.0)),
        ("RY(2*pi)", ry(TAU)),
        ("RZ(-2*pi)", rz(-TAU)),
        ("RX(4*pi)", rx(4 * PI)),
    ]

    for name, gate in cases:
        print(f"{name:12s} unitary = {is_unitary(gate)}")

    print("\nZero-vector axis validation:")
    try:
        general_axis_rotation((0.0, 0.0, 0.0), PI / 2)
    except ValueError as error:
        print(f"  Correctly rejected: {error}")

    print("\nInvalid state validation:")
    try:
        QubitState(1 + 0j, 1 + 0j)
    except ValueError as error:
        print(f"  Correctly rejected: {error}")

    print("\nInvalid measurement validation:")
    try:
        sample_measurement(QubitState.zero(), 0)
    except ValueError as error:
        print(f"  Correctly rejected: {error}")


def demonstrate_precision() -> None:
    section("14. NUMERICAL PRECISION")

    state = QubitState.from_bloch(0.9, -1.3)
    current = state

    # Repeated forward and inverse rotations should return close to the
    # original state, but floating-point arithmetic introduces tiny errors.
    for _ in range(100):
        current = current.apply(rx(0.17))
        current = current.apply(rx(-0.17))

    print(
        "Fidelity after 100 RX(angle)/RX(-angle) pairs: "
        f"{state_fidelity(state, current):.15f}"
    )

    print(
        "\nProduction simulators normally use carefully tested numerical "
        "linear algebra and tolerance-based comparisons rather than exact "
        "floating-point equality."
    )


def demonstrate_optimization() -> None:
    section("15. PARAMETER COMBINATION AND OPTIMIZATION")

    # Rotations around the same axis commute and their angles add:
    #
    # RX(a) RX(b) = RX(a+b)
    #
    # This is useful for circuit simplification.
    a = 0.31
    b = 0.92

    separate = matrix_multiply(rx(b), rx(a))
    combined = rx(a + b)

    difference = matrix_difference_norm(separate, combined)

    print(f"RX(a)RX(b) vs RX(a+b) matrix difference: {difference:.3e}")

    # The same identity holds for RY and RZ.
    print(
        "RY combination error: "
        f"{matrix_difference_norm("
        f"matrix_multiply(ry(b), ry(a)), ry(a + b)"
        f"):.3e}"
    )
    print(
        "RZ combination error: "
        f"{matrix_difference_norm("
        f"matrix_multiply(rz(b), rz(a)), rz(a + b)"
        f"):.3e}"
    )

    print(
        "\nRotations around different axes generally cannot be combined by "
        "simply adding angles. A compiler must preserve the resulting "
        "unitary transformation."
    )


def demonstrate_comparison_with_pauli_generators() -> None:
    section("16. PAULI-MATRIX GENERATOR RELATIONSHIP")

    theta = 0.8

    print(
        "RX(theta) is generated by X, RY(theta) by Y, and RZ(theta) by Z."
    )

    print_matrix(X, "Pauli X")
    print_matrix(Y, "Pauli Y")
    print_matrix(Z, "Pauli Z")

    print("\nThe conceptual formula is:")
    print("  R_axis(theta) = exp(-i * theta * Pauli_axis / 2)")

    # The direct closed forms implemented above are equivalent to the
    # exponential definitions. The comparison here uses the known formulas.
    print(f"\nRX({theta}) unitary: {is_unitary(rx(theta))}")
    print(f"RY({theta}) unitary: {is_unitary(ry(theta))}")
    print(f"RZ({theta}) unitary: {is_unitary(rz(theta))}")


def demonstrate_physical_interpretation() -> None:
    section("17. PRACTICAL INTERPRETATION")

    print(
        """
RX(theta):
  Rotates the Bloch vector around the x-axis.
  It mixes |0> and |1> with complex amplitudes.
  It is useful for changing population and phase relationships.

RY(theta):
  Rotates around the y-axis.
  Starting from |0>, it directly changes computational-basis
  probabilities according to cos²(theta/2) and sin²(theta/2).

RZ(theta):
  Rotates around the z-axis.
  It applies opposite phases to |0> and |1>.
  For a computational-basis eigenstate, probabilities do not change.
  For a superposition, the relative phase changes and can affect
  later interference.

All three:
  - are unitary;
  - preserve state normalization;
  - are parameterized by a real angle;
  - have inverse obtained by negating the angle;
  - are periodic at the level of physical Bloch-sphere rotations;
  - form fundamental building blocks for single-qubit circuits.
"""
    )


def run_self_tests() -> None:
    section("18. AUTOMATED SELF-TESTS")

    # Identity rotations.
    for gate_factory in (rx, ry, rz):
        result = QubitState.from_bloch(0.7, -0.4).apply(gate_factory(0.0))
        original = QubitState.from_bloch(0.7, -0.4)
        assert state_fidelity(result, original) > 1 - 1e-12

    # pi rotations map |0> to |1> up to a global phase for X/Y rotations.
    rx_pi = QubitState.zero().apply(rx(PI))
    ry_pi = QubitState.zero().apply(ry(PI))
    assert state_fidelity(rx_pi, QubitState.one()) > 1 - 1e-12
    assert state_fidelity(ry_pi, QubitState.one()) > 1 - 1e-12

    # Z rotation does not change computational-basis probabilities.
    state = QubitState.zero()
    rotated = state.apply(rz(1.234))
    assert nearly_equal(rotated.probability_zero(), 1.0)
    assert nearly_equal(rotated.probability_one(), 0.0)

    # Same-axis rotations combine.
    a = 0.23
    b = -0.91
    state = QubitState.from_bloch(1.2, 0.4)

    separate = state.apply(rx(a)).apply(rx(b))
    combined = state.apply(rx(a + b))
    assert state_fidelity(separate, combined) > 1 - 1e-12

    separate = state.apply(ry(a)).apply(ry(b))
    combined = state.apply(ry(a + b))
    assert state_fidelity(separate, combined) > 1 - 1e-12

    separate = state.apply(rz(a)).apply(rz(b))
    combined = state.apply(rz(a + b))
    assert state_fidelity(separate, combined) > 1 - 1e-12

    # Circuit and combined matrix must agree.
    circuit = (
        QubitCircuit(state)
        .add_rx(0.2)
        .add_ry(-0.4)
        .add_rz(0.7)
    )

    circuit_state = circuit.run()
    direct_state = state.apply(circuit.combined_unitary())
    assert state_fidelity(circuit_state, direct_state) > 1 - 1e-12

    # General axis rotation must be unitary.
    assert is_unitary(general_axis_rotation((2.0, -1.0, 3.0), 0.9))

    # Euler-style construction must be unitary.
    assert is_unitary(u3(0.8, -0.4, 1.2))

    print("\nAll self-tests passed.")


# ---------------------------------------------------------------------------
# Main study runner
# ---------------------------------------------------------------------------

def main() -> None:
    print("ROTATION GATES: RX, RY, RZ")
    print("Single-Qubit Quantum Computing Study Program")
    print("Angles are expressed in radians.")

    demonstrate_fundamentals()
    demonstrate_rotation_matrices()
    demonstrate_basic_rotations()
    demonstrate_bloch_sphere_rotations()
    demonstrate_measurement()
    demonstrate_non_commutativity()
    demonstrate_periodicity_and_inverse()
    demonstrate_global_and_relative_phase()
    demonstrate_general_axis_rotation()
    demonstrate_euler_decomposition()
    demonstrate_circuit()
    demonstrate_expectation_values()
    demonstrate_edge_cases()
    demonstrate_precision()
    demonstrate_optimization()
    demonstrate_comparison_with_pauli_generators()
    demonstrate_physical_interpretation()
    run_self_tests()

    section("19. STUDY REFERENCE")

    print(
        """
Core formulas:

RX(theta) =
    [ cos(theta/2)   -i sin(theta/2) ]
    [ -i sin(theta/2)  cos(theta/2)  ]

RY(theta) =
    [ cos(theta/2)  -sin(theta/2) ]
    [ sin(theta/2)   cos(theta/2) ]

RZ(theta) =
    [ exp(-i theta/2)       0      ]
    [       0         exp(i theta/2) ]

State:
    |psi> = alpha|0> + beta|1>

Normalization:
    |alpha|² + |beta|² = 1

Measurement:
    P(0) = |alpha|²
    P(1) = |beta|²

Bloch coordinates:
    x = 2 Re(alpha* beta)
    y = 2 Im(alpha* beta)
    z = |alpha|² - |beta|²

Rotation generator:
    R_axis(theta) = exp(-i theta sigma_axis / 2)

Inverse:
    R_axis(theta)^† = R_axis(-theta)

Same-axis composition:
    R_axis(a)R_axis(b) = R_axis(a+b)

Different-axis rotations:
    Generally non-commutative.

The central distinction is that RX, RY, and RZ are not merely
three alternative names for the same operation. They rotate a
qubit around three different axes of the Bloch sphere, producing
different transformations of amplitudes and relative phase.
"""
    )


if __name__ == "__main__":
    main()
