"""
Bloch Sphere: From Qubit Fundamentals to Advanced Visualization and Simulation
===========================================================================
A self-contained study program covering:

1. Qubits and computational basis states
2. Bloch-sphere representation
3. Pure and mixed states
4. State vectors and density matrices
5. Spherical coordinates
6. Pauli matrices and expectation values
7. Single-qubit gates as rotations
8. X, Y, Z, H, S, T and rotation gates
9. Measurement probabilities
10. Global phase versus physically observable phase
11. Relative phase and the equator
12. Density-matrix Bloch vectors
13. Unitary evolution
14. Measurement and state collapse
15. Noise and mixed states
16. Depolarizing, dephasing and bit-flip channels
17. Fidelity and purity
18. Numerical validation and edge cases
19. A small tomography example
20. A simple gate-sequence simulator
21. Geometric interpretation of quantum operations

The implementation uses only the Python standard library.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple


EPSILON = 1e-10


# ---------------------------------------------------------------------------
# Basic linear-algebra helpers
# ---------------------------------------------------------------------------

Complex = complex
Vector = List[Complex]
Matrix = List[List[Complex]]


def vector_norm(vector: Sequence[Complex]) -> float:
    """Return the Euclidean norm of a complex vector."""
    return math.sqrt(sum(abs(value) ** 2 for value in vector))


def normalize_state(state: Sequence[Complex]) -> Vector:
    """Normalize a two-component qubit state."""
    if len(state) != 2:
        raise ValueError("A single-qubit state must contain exactly two amplitudes.")

    norm = vector_norm(state)
    if norm < EPSILON:
        raise ValueError("The zero vector cannot represent a quantum state.")

    return [value / norm for value in state]


def inner_product(a: Sequence[Complex], b: Sequence[Complex]) -> Complex:
    """Return <a|b> using complex conjugation on the first vector."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")

    return sum(a_value.conjugate() * b_value for a_value, b_value in zip(a, b))


def matrix_vector_multiply(matrix: Matrix, vector: Sequence[Complex]) -> Vector:
    """Multiply a matrix by a vector."""
    if len(matrix) == 0:
        raise ValueError("Matrix cannot be empty.")

    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("Matrix dimensions do not match the vector.")

    return [
        sum(matrix[row_index][column_index] * vector[column_index]
            for column_index in range(len(vector)))
        for row_index in range(len(matrix))
    ]


def matrix_multiply(a: Matrix, b: Matrix) -> Matrix:
    """Multiply two matrices."""
    if not a or not b:
        raise ValueError("Matrices cannot be empty.")

    if len(a[0]) != len(b):
        raise ValueError("Matrix dimensions do not match.")

    return [
        [
            sum(a[i][k] * b[k][j] for k in range(len(b)))
            for j in range(len(b[0]))
        ]
        for i in range(len(a))
    ]


def dagger(matrix: Matrix) -> Matrix:
    """Return the conjugate transpose of a matrix."""
    return [
        [matrix[row][column].conjugate() for row in range(len(matrix))]
        for column in range(len(matrix[0]))
    ]


def trace(matrix: Matrix) -> Complex:
    """Return the trace of a square matrix."""
    if len(matrix) != len(matrix[0]):
        raise ValueError("Trace requires a square matrix.")

    return sum(matrix[i][i] for i in range(len(matrix)))


def outer_product(state: Sequence[Complex]) -> Matrix:
    """Construct |psi><psi| from a state vector."""
    return [
        [
            state[row] * state[column].conjugate()
            for column in range(len(state))
        ]
        for row in range(len(state))
    ]


def matrix_add(a: Matrix, b: Matrix) -> Matrix:
    """Add two matrices of equal dimensions."""
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError("Matrices must have identical dimensions.")

    return [
        [a[i][j] + b[i][j] for j in range(len(a[0]))]
        for i in range(len(a))
    ]


def matrix_scale(scalar: Complex, matrix: Matrix) -> Matrix:
    """Multiply every matrix element by a scalar."""
    return [[scalar * value for value in row] for row in matrix]


def clean_complex(value: Complex, digits: int = 6) -> Complex:
    """Remove tiny numerical noise from a complex number."""
    real = 0.0 if abs(value.real) < 10 ** (-digits) else round(value.real, digits)
    imag = 0.0 if abs(value.imag) < 10 ** (-digits) else round(value.imag, digits)
    return complex(real, imag)


def clean_matrix(matrix: Matrix) -> Matrix:
    return [[clean_complex(value) for value in row] for row in matrix]


# ---------------------------------------------------------------------------
# Pauli matrices and fundamental constants
# ---------------------------------------------------------------------------

I2: Matrix = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, 1 + 0j],
]

X: Matrix = [
    [0 + 0j, 1 + 0j],
    [1 + 0j, 0 + 0j],
]

Y: Matrix = [
    [0 + 0j, -1j],
    [1j, 0 + 0j],
]

Z: Matrix = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, -1 + 0j],
]

H: Matrix = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]

S: Matrix = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, 1j],
]

T: Matrix = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, cmath.exp(1j * math.pi / 4)],
]


def rotation_x(theta: float) -> Matrix:
    """R_x(theta) = exp(-i theta X / 2)."""
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return [
        [c, -1j * s],
        [-1j * s, c],
    ]


def rotation_y(theta: float) -> Matrix:
    """R_y(theta) = exp(-i theta Y / 2)."""
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return [
        [c, -s],
        [s, c],
    ]


def rotation_z(theta: float) -> Matrix:
    """R_z(theta) = exp(-i theta Z / 2)."""
    return [
        [cmath.exp(-1j * theta / 2), 0],
        [0, cmath.exp(1j * theta / 2)],
    ]


# ---------------------------------------------------------------------------
# Bloch sphere representation
# ---------------------------------------------------------------------------

@dataclass
class BlochVector:
    """
    Cartesian coordinates (x, y, z) of a qubit on or inside the Bloch sphere.

    Pure states satisfy x^2 + y^2 + z^2 = 1.
    Mixed states satisfy x^2 + y^2 + z^2 < 1.
    """

    x: float
    y: float
    z: float

    def norm(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def is_valid(self) -> bool:
        return self.norm() <= 1.0 + EPSILON

    def is_pure(self) -> bool:
        return abs(self.norm() - 1.0) < 1e-8

    def spherical_coordinates(self) -> Tuple[float, float]:
        """
        Return theta and phi.

        theta is measured from +z.
        phi is measured from +x toward +y.
        """
        r = self.norm()
        if r < EPSILON:
            return 0.0, 0.0

        theta = math.acos(max(-1.0, min(1.0, self.z / r)))
        phi = math.atan2(self.y, self.x)
        if phi < 0:
            phi += 2 * math.pi

        return theta, phi

    def __str__(self) -> str:
        return f"({self.x:.6f}, {self.y:.6f}, {self.z:.6f})"


def state_from_bloch(theta: float, phi: float) -> Vector:
    """
    Construct the canonical pure state

        |psi> = cos(theta/2)|0> + exp(i phi) sin(theta/2)|1>.

    A global phase has been chosen so that the |0> amplitude is real.
    """
    return [
        math.cos(theta / 2),
        cmath.exp(1j * phi) * math.sin(theta / 2),
    ]


def bloch_from_state(state: Sequence[Complex]) -> BlochVector:
    """
    Convert a normalized pure-state vector into Bloch coordinates.

    x = 2 Re(alpha* beta)
    y = 2 Im(alpha* beta)
    z = |alpha|^2 - |beta|^2
    """
    state = normalize_state(state)
    alpha, beta = state

    x = 2 * (alpha.conjugate() * beta).real
    y = 2 * (alpha.conjugate() * beta).imag
    z = abs(alpha) ** 2 - abs(beta) ** 2

    return BlochVector(x, y, z)


def density_matrix_from_state(state: Sequence[Complex]) -> Matrix:
    """Convert a pure state to its density matrix."""
    normalized = normalize_state(state)
    return outer_product(normalized)


def density_matrix_from_bloch(bloch: BlochVector) -> Matrix:
    """
    rho = 1/2 (I + xX + yY + zZ).

    This representation also handles mixed states when |r| < 1.
    """
    if not bloch.is_valid():
        raise ValueError("A Bloch vector must lie inside or on the unit sphere.")

    result = matrix_scale(0.5, I2)
    result = matrix_add(result, matrix_scale(0.5 * bloch.x, X))
    result = matrix_add(result, matrix_scale(0.5 * bloch.y, Y))
    result = matrix_add(result, matrix_scale(0.5 * bloch.z, Z))
    return result


def bloch_from_density_matrix(rho: Matrix) -> BlochVector:
    """
    Recover Bloch coordinates using expectation values:
        x = Tr(rho X)
        y = Tr(rho Y)
        z = Tr(rho Z)
    """
    x = trace(matrix_multiply(rho, X)).real
    y = trace(matrix_multiply(rho, Y)).real
    z = trace(matrix_multiply(rho, Z)).real

    return BlochVector(x, y, z)


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def measurement_probabilities(state: Sequence[Complex]) -> Tuple[float, float]:
    """Return computational-basis probabilities P(0) and P(1)."""
    normalized = normalize_state(state)
    p0 = abs(normalized[0]) ** 2
    p1 = abs(normalized[1]) ** 2

    # Floating-point calculations can produce values such as 1.0000000000002.
    p0 = max(0.0, min(1.0, p0))
    p1 = max(0.0, min(1.0, p1))

    return p0, p1


def measure_state(state: Sequence[Complex], rng: random.Random | None = None) -> Tuple[int, Vector]:
    """
    Perform a projective measurement in the computational basis.

    The returned state is the collapsed post-measurement state.
    """
    rng = rng or random.Random()
    p0, _ = measurement_probabilities(state)

    if rng.random() < p0:
        return 0, [1 + 0j, 0 + 0j]

    return 1, [0 + 0j, 1 + 0j]


def repeated_measurements(
    state: Sequence[Complex],
    shots: int = 1000,
    seed: int = 42,
) -> Tuple[int, int]:
    """Perform repeated independent measurements."""
    if shots <= 0:
        raise ValueError("shots must be positive.")

    rng = random.Random(seed)
    counts = {0: 0, 1: 0}

    for _ in range(shots):
        outcome, _ = measure_state(state, rng)
        counts[outcome] += 1

    return counts[0], counts[1]


# ---------------------------------------------------------------------------
# State evolution
# ---------------------------------------------------------------------------

def apply_gate(state: Sequence[Complex], gate: Matrix) -> Vector:
    """Apply a 2x2 single-qubit unitary to a state."""
    if len(gate) != 2 or any(len(row) != 2 for row in gate):
        raise ValueError("A single-qubit gate must be a 2x2 matrix.")

    result = matrix_vector_multiply(gate, state)
    return normalize_state(result)


def apply_density_operator(rho: Matrix, gate: Matrix) -> Matrix:
    """Unitary density-matrix evolution: rho' = U rho U†."""
    return matrix_multiply(matrix_multiply(gate, rho), dagger(gate))


def state_fidelity(a: Sequence[Complex], b: Sequence[Complex]) -> float:
    """
    Pure-state fidelity:
        F = |<a|b>|^2
    """
    a = normalize_state(a)
    b = normalize_state(b)
    return abs(inner_product(a, b)) ** 2


def density_matrix_fidelity_pure_target(
    rho: Matrix,
    target_state: Sequence[Complex],
) -> float:
    """Fidelity F(rho, |psi>) = <psi|rho|psi>."""
    target = normalize_state(target_state)
    rho_target = matrix_vector_multiply(rho, target)
    return inner_product(target, rho_target).real


def purity(rho: Matrix) -> float:
    """Purity is Tr(rho^2), equal to 1 for pure states."""
    squared = matrix_multiply(rho, rho)
    return trace(squared).real


# ---------------------------------------------------------------------------
# Noise channels
# ---------------------------------------------------------------------------

def bit_flip_channel(rho: Matrix, probability: float) -> Matrix:
    """Apply a bit-flip channel: rho'=(1-p)rho+pXrhoX."""
    validate_probability(probability)

    unchanged = matrix_scale(1 - probability, rho)
    flipped = matrix_scale(
        probability,
        matrix_multiply(matrix_multiply(X, rho), X),
    )

    return matrix_add(unchanged, flipped)


def phase_flip_channel(rho: Matrix, probability: float) -> Matrix:
    """Apply a phase-flip channel: rho'=(1-p)rho+pZrhoZ."""
    validate_probability(probability)

    unchanged = matrix_scale(1 - probability, rho)
    flipped = matrix_scale(
        probability,
        matrix_multiply(matrix_multiply(Z, rho), Z),
    )

    return matrix_add(unchanged, flipped)


def depolarizing_channel(rho: Matrix, probability: float) -> Matrix:
    """
    Symmetric Pauli depolarizing channel:

        rho' = (1-p)rho
             + p/3 (XrhoX + YrhoY + ZrhoZ).

    In Bloch-vector form this shrinks all three components by
    1 - 4p/3.
    """
    validate_probability(probability)

    result = matrix_scale(1 - probability, rho)

    for pauli in (X, Y, Z):
        transformed = matrix_multiply(matrix_multiply(pauli, rho), pauli)
        result = matrix_add(result, matrix_scale(probability / 3, transformed))

    return result


def dephasing_channel(rho: Matrix, probability: float) -> Matrix:
    """
    A phase-randomization channel implemented as a phase flip with
    probability p. It leaves z unchanged and reduces transverse
    coherence.
    """
    return phase_flip_channel(rho, probability)


def validate_probability(probability: float) -> None:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("Probability must be between 0 and 1.")


# ---------------------------------------------------------------------------
# Quantum gate demonstrations
# ---------------------------------------------------------------------------

def demonstrate_basic_states() -> None:
    print("\n=== 1. Computational basis states ===")

    zero = [1 + 0j, 0 + 0j]
    one = [0 + 0j, 1 + 0j]

    print("|0> =", zero)
    print("Bloch(|0>) =", bloch_from_state(zero))
    print("|1> =", one)
    print("Bloch(|1>) =", bloch_from_state(one))

    plus = apply_gate(zero, H)
    minus = apply_gate(one, H)

    print("|+> = H|0> =", [clean_complex(x) for x in plus])
    print("Bloch(|+>) =", bloch_from_state(plus))
    print("|-> = H|1> =", [clean_complex(x) for x in minus])
    print("Bloch(|->) =", bloch_from_state(minus))


def demonstrate_spherical_parameterization() -> None:
    print("\n=== 2. Spherical-coordinate parameterization ===")

    examples = [
        ("north pole |0>", 0, 0),
        ("east equator |+>", math.pi / 2, 0),
        ("north-east equator", math.pi / 2, math.pi / 4),
        ("south pole |1>", math.pi, 0),
    ]

    for name, theta, phi in examples:
        state = state_from_bloch(theta, phi)
        bloch = bloch_from_state(state)
        print(f"{name:24s} theta={theta:.4f}, phi={phi:.4f}")
        print("  state =", [clean_complex(x) for x in state])
        print("  Bloch =", bloch)


def demonstrate_gates_as_rotations() -> None:
    print("\n=== 3. Gates as geometric rotations ===")

    zero = [1 + 0j, 0 + 0j]

    gates = [
        ("X", X),
        ("Y", Y),
        ("Z", Z),
        ("H", H),
        ("S", S),
        ("T", T),
    ]

    for name, gate in gates:
        transformed = apply_gate(zero, gate)
        print(f"{name:2s} |0> -> Bloch {bloch_from_state(transformed)}")

    theta = math.pi / 2
    rx_state = apply_gate(zero, rotation_x(theta))
    ry_state = apply_gate(zero, rotation_y(theta))
    rz_state = apply_gate(
        state_from_bloch(math.pi / 2, 0),
        rotation_z(theta),
    )

    print("Rx(pi/2)|0> ->", bloch_from_state(rx_state))
    print("Ry(pi/2)|0> ->", bloch_from_state(ry_state))
    print("Rz(pi/2)|+> ->", bloch_from_state(rz_state))


def demonstrate_global_phase() -> None:
    print("\n=== 4. Global phase versus physical state ===")

    state = state_from_bloch(math.pi / 3, math.pi / 5)
    global_phase = cmath.exp(1j * 1.234)
    phased = [global_phase * value for value in state]

    print("Original Bloch vector:", bloch_from_state(state))
    print("Globally phased Bloch vector:", bloch_from_state(phased))
    print("Fidelity:", state_fidelity(state, phased))

    print(
        "The vector components changed, but all measurement probabilities "
        "and the physical Bloch point remain unchanged."
    )


def demonstrate_relative_phase() -> None:
    print("\n=== 5. Relative phase changes the Bloch position ===")

    theta = math.pi / 2
    phases = [0, math.pi / 2, math.pi, 3 * math.pi / 2]

    for phi in phases:
        state = state_from_bloch(theta, phi)
        print(
            f"phi={phi:.4f} -> "
            f"state={state} -> Bloch={bloch_from_state(state)}"
        )


# ---------------------------------------------------------------------------
# Density matrices and mixed states
# ---------------------------------------------------------------------------

def demonstrate_density_matrices() -> None:
    print("\n=== 6. Pure and mixed states ===")

    plus = state_from_bloch(math.pi / 2, 0)
    rho_plus = density_matrix_from_state(plus)

    maximally_mixed = density_matrix_from_bloch(BlochVector(0, 0, 0))

    print("rho(|+>) =", clean_matrix(rho_plus))
    print("Bloch(rho(|+>)) =", bloch_from_density_matrix(rho_plus))
    print("Purity(|+>) =", purity(rho_plus))

    print("Maximally mixed rho =", clean_matrix(maximally_mixed))
    print("Bloch(maximally mixed) =", bloch_from_density_matrix(maximally_mixed))
    print("Purity(maximally mixed) =", purity(maximally_mixed))


def demonstrate_noise() -> None:
    print("\n=== 7. Noise channels ===")

    initial = state_from_bloch(math.pi / 2, math.pi / 4)
    rho = density_matrix_from_state(initial)

    print("Initial Bloch:", bloch_from_density_matrix(rho))
    print("Initial purity:", purity(rho))

    for probability in (0.1, 0.25, 0.5):
        noisy = depolarizing_channel(rho, probability)
        print(
            f"Depolarizing p={probability:.2f}: "
            f"Bloch={bloch_from_density_matrix(noisy)}, "
            f"purity={purity(noisy):.6f}"
        )

    phase_noisy = dephasing_channel(rho, 0.25)
    print(
        "Dephasing p=0.25:",
        bloch_from_density_matrix(phase_noisy),
    )


# ---------------------------------------------------------------------------
# Quantum state tomography
# ---------------------------------------------------------------------------

def simulate_pauli_expectations(
    state: Sequence[Complex],
    shots: int = 10000,
    seed: int = 123,
) -> Tuple[float, float, float]:
    """
    Estimate x, y, z expectation values by repeated Pauli measurements.

    For a Pauli observable with outcomes +1 and -1:
        <P> = P(+1) - P(-1).
    """
    if shots <= 0:
        raise ValueError("shots must be positive.")

    rng = random.Random(seed)
    rho = density_matrix_from_state(state)

    exact = []
    for pauli in (X, Y, Z):
        exact.append(trace(matrix_multiply(rho, pauli)).real)

    estimates = []

    for expectation in exact:
        probability_plus = (1 + expectation) / 2
        plus_count = sum(
            1 for _ in range(shots)
            if rng.random() < probability_plus
        )
        estimates.append((plus_count - (shots - plus_count)) / shots)

    return estimates[0], estimates[1], estimates[2]


def demonstrate_tomography() -> None:
    print("\n=== 8. Single-qubit tomography ===")

    true_state = state_from_bloch(1.1, 2.2)
    true_bloch = bloch_from_state(true_state)

    estimated = simulate_pauli_expectations(true_state)

    print("True Bloch vector:     ", true_bloch)
    print("Estimated Bloch vector:", BlochVector(*estimated))
    print(
        "Tomography estimates the unknown state from measurement "
        "statistics rather than directly observing its amplitudes."
    )


# ---------------------------------------------------------------------------
# Gate-sequence simulator
# ---------------------------------------------------------------------------

@dataclass
class GateOperation:
    name: str
    matrix: Matrix


class QubitSimulator:
    """Small educational single-qubit simulator."""

    def __init__(self, initial_state: Sequence[Complex] | None = None):
        self.state = normalize_state(
            initial_state if initial_state is not None else [1 + 0j, 0 + 0j]
        )
        self.history: List[Tuple[str, BlochVector]] = [
            ("initial", bloch_from_state(self.state))
        ]

    def apply(self, name: str, gate: Matrix) -> None:
        self.state = apply_gate(self.state, gate)
        self.history.append((name, bloch_from_state(self.state)))

    def measure(self, seed: int = 42) -> int:
        outcome, collapsed = measure_state(self.state, random.Random(seed))
        self.state = collapsed
        self.history.append((f"measure -> {outcome}", bloch_from_state(self.state)))
        return outcome

    def print_history(self) -> None:
        for operation, bloch in self.history:
            print(f"{operation:16s}: {bloch}")


def demonstrate_gate_sequence() -> None:
    print("\n=== 9. Gate-sequence simulator ===")

    simulator = QubitSimulator()

    simulator.apply("H", H)
    simulator.apply("S", S)
    simulator.apply("Rx(pi/3)", rotation_x(math.pi / 3))
    simulator.apply("Rz(pi/5)", rotation_z(math.pi / 5))

    simulator.print_history()

    outcome = simulator.measure(seed=7)
    print("Measurement outcome:", outcome)
    print("Collapsed state:", simulator.state)


# ---------------------------------------------------------------------------
# Validation and edge cases
# ---------------------------------------------------------------------------

def assert_close(a: float, b: float, tolerance: float = 1e-8) -> None:
    if abs(a - b) > tolerance:
        raise AssertionError(f"{a} is not sufficiently close to {b}.")


def validate_bloch_representation() -> None:
    print("\n=== 10. Mathematical validation ===")

    test_points = [
        (0.0, 0.0),
        (math.pi / 2, 0.0),
        (math.pi / 2, math.pi / 2),
        (math.pi / 2, math.pi),
        (math.pi, 0.0),
        (1.234, 4.321),
    ]

    for theta, phi in test_points:
        state = state_from_bloch(theta, phi)
        bloch = bloch_from_state(state)
        recovered_rho = density_matrix_from_bloch(bloch)
        original_rho = density_matrix_from_state(state)

        difference = max(
            abs(recovered_rho[i][j] - original_rho[i][j])
            for i in range(2)
            for j in range(2)
        )

        assert_close(bloch.norm(), 1.0, 1e-8)
        assert difference < 1e-8

    print("Pure-state Bloch conversion tests passed.")

    invalid_points = [
        BlochVector(1.1, 0, 0),
        BlochVector(0, -1.01, 0),
        BlochVector(0, 0, 1.0001),
    ]

    for point in invalid_points:
        try:
            density_matrix_from_bloch(point)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid Bloch vector was accepted.")

    print("Invalid-state validation tests passed.")


# ---------------------------------------------------------------------------
# Advanced conceptual demonstrations
# ---------------------------------------------------------------------------

def demonstrate_expectation_values() -> None:
    print("\n=== 11. Bloch coordinates as expectation values ===")

    state = state_from_bloch(1.2, 2.4)
    rho = density_matrix_from_state(state)
    bloch = bloch_from_state(state)

    print("Bloch vector:", bloch)

    for name, pauli in (("X", X), ("Y", Y), ("Z", Z)):
        expectation = trace(matrix_multiply(rho, pauli)).real
        print(f"<{name}> = {expectation:.6f}")


def demonstrate_rotation_geometry() -> None:
    print("\n=== 12. Continuous rotations ===")

    state = state_from_bloch(math.pi / 2, 0)
    print("Starting point:", bloch_from_state(state))

    for angle_degrees in (0, 45, 90, 135, 180, 270):
        angle = math.radians(angle_degrees)
        transformed = apply_gate(state, rotation_z(angle))
        print(
            f"Rz({angle_degrees:3d}°): "
            f"{bloch_from_state(transformed)}"
        )


def demonstrate_measurement_geometry() -> None:
    print("\n=== 13. Measurement probabilities from z coordinate ===")

    for theta in (0, math.pi / 4, math.pi / 2, 3 * math.pi / 4, math.pi):
        state = state_from_bloch(theta, 0)
        bloch = bloch_from_state(state)
        p0, p1 = measurement_probabilities(state)

        formula_p0 = (1 + bloch.z) / 2
        formula_p1 = (1 - bloch.z) / 2

        print(
            f"theta={theta:.4f}, z={bloch.z:.6f}, "
            f"P0={p0:.6f}, P1={p1:.6f}, "
            f"formula=({formula_p0:.6f}, {formula_p1:.6f})"
        )


def demonstrate_phase_gate() -> None:
    print("\n=== 14. Phase gates rotate around z ===")

    state = state_from_bloch(math.pi / 2, 0)

    for name, gate in (("S", S), ("T", T), ("S²", matrix_multiply(S, S))):
        transformed = apply_gate(state, gate)
        print(f"{name:3s} -> {bloch_from_state(transformed)}")


def demonstrate_unitarity() -> None:
    print("\n=== 15. Unitarity checks ===")

    gates = {
        "X": X,
        "Y": Y,
        "Z": Z,
        "H": H,
        "S": S,
        "T": T,
        "Rx": rotation_x(0.73),
        "Ry": rotation_y(1.17),
        "Rz": rotation_z(2.13),
    }

    for name, gate in gates.items():
        product = matrix_multiply(dagger(gate), gate)

        maximum_error = max(
            abs(product[i][j] - I2[i][j])
            for i in range(2)
            for j in range(2)
        )

        print(f"{name:3s} maximum unitarity error = {maximum_error:.3e}")


# ---------------------------------------------------------------------------
# Educational text output
# ---------------------------------------------------------------------------

def print_conceptual_reference() -> None:
    print("\n=== 16. Bloch-sphere reference ===")

    concepts = {
        "Qubit":
            "A two-level quantum system represented by alpha|0> + beta|1>.",
        "Normalization":
            "|alpha|^2 + |beta|^2 = 1 for a pure normalized state.",
        "Bloch vector":
            "r = (x, y, z), with rho = 1/2(I + xX + yY + zZ).",
        "Pure state":
            "|r| = 1, represented on the sphere surface.",
        "Mixed state":
            "|r| < 1, represented inside the sphere.",
        "North pole":
            "|0>, with r=(0,0,1).",
        "South pole":
            "|1>, with r=(0,0,-1).",
        "Equator":
            "Equal measurement probabilities in the computational basis.",
        "Global phase":
            "A common phase factor that does not alter a single-qubit physical state.",
        "Relative phase":
            "Phase difference between amplitudes that changes the Bloch position.",
        "Measurement":
            "A probabilistic projection onto measurement eigenstates.",
        "Unitary gate":
            "A reversible transformation represented by U†U=I.",
        "Noise":
            "A non-unitary open-system process that can move a state inward.",
        "Purity":
            "Tr(rho²), equal to one for a pure state and below one for a mixed state.",
    }

    for name, explanation in concepts.items():
        print(f"{name:18s}: {explanation}")


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("BLOCH SPHERE: SINGLE-QUBIT GEOMETRY AND SIMULATION")
    print("=" * 78)

    demonstrate_basic_states()
    demonstrate_spherical_parameterization()
    demonstrate_gates_as_rotations()
    demonstrate_global_phase()
    demonstrate_relative_phase()
    demonstrate_density_matrices()
    demonstrate_noise()
    demonstrate_tomography()
    demonstrate_gate_sequence()
    validate_bloch_representation()
    demonstrate_expectation_values()
    demonstrate_rotation_geometry()
    demonstrate_measurement_geometry()
    demonstrate_phase_gate()
    demonstrate_unitarity()
    print_conceptual_reference()

    print("\n=== 17. Final integrated example ===")

    # Prepare a nontrivial state, evolve it, convert between representations,
    # and estimate its measurement statistics.
    state = state_from_bloch(theta=1.15, phi=2.05)
    print("Initial state:", [clean_complex(value) for value in state])

    state = apply_gate(state, rotation_y(0.7))
    state = apply_gate(state, rotation_z(-0.4))

    bloch = bloch_from_state(state)
    rho = density_matrix_from_state(state)
    p0, p1 = measurement_probabilities(state)
    counts = repeated_measurements(state, shots=5000, seed=99)

    print("Final Bloch vector:", bloch)
    print("Final density matrix:", clean_matrix(rho))
    print(f"Measurement probabilities: P(0)={p0:.6f}, P(1)={p1:.6f}")
    print(f"5000-shot sample counts: |0>={counts[0]}, |1>={counts[1]}")
    print("Purity:", purity(rho))

    print("\nProgram completed successfully.")


if __name__ == "__main__":
    main()
