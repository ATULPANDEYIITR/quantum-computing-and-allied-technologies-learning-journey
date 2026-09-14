"""
Quantum measurement: observables, collapse, and probabilities
==============================================================

A self-contained study script covering quantum measurement from beginner
foundations through advanced finite-dimensional examples.

The script uses only the Python standard library. It implements small complex
matrices and vectors directly so that the mathematical mechanisms remain
visible rather than being hidden behind a quantum-computing package.

Main topics
-----------
1. States and amplitudes
2. Born probabilities
3. Projective measurements
4. Observables and Hermitian operators
5. Eigenvalues and eigenstates
6. Degeneracy
7. State collapse and conditional states
8. Measurement in different bases
9. Sequential measurements
10. Compatible and incompatible observables
11. Commutators and uncertainty
12. Density matrices
13. Mixed states and the maximally mixed state
14. Generalized measurements and POVMs
15. Quantum channels and measurement disturbance
16. Weak measurement concepts
17. No-cloning and information-disturbance considerations
18. Numerical validation and edge cases
19. Practical measurement simulations
20. Production-oriented implementation considerations
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


# ============================================================================
# SECTION 1: SMALL COMPLEX LINEAR-ALGEBRA TOOLKIT
# ============================================================================

Complex = complex
Vector = list[Complex]
Matrix = list[list[Complex]]

TOLERANCE = 1e-10


def clean_complex(value: complex, tolerance: float = 1e-10) -> complex:
    """Remove tiny numerical real/imaginary parts for readable output."""
    real = 0.0 if abs(value.real) < tolerance else value.real
    imag = 0.0 if abs(value.imag) < tolerance else value.imag
    return complex(real, imag)


def clean_vector(vector: Vector, tolerance: float = 1e-10) -> Vector:
    return [clean_complex(x, tolerance) for x in vector]


def clean_matrix(matrix: Matrix, tolerance: float = 1e-10) -> Matrix:
    return [[clean_complex(x, tolerance) for x in row] for row in matrix]


def vector_add(a: Vector, b: Vector) -> Vector:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return [x + y for x, y in zip(a, b)]


def vector_scale(scalar: complex, vector: Vector) -> Vector:
    return [scalar * x for x in vector]


def vector_inner(a: Vector, b: Vector) -> complex:
    """
    Bra-ket inner product <a|b>.

    Complex conjugation belongs to the bra, so the operation is not ordinary
    component-wise multiplication.
    """
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return sum(x.conjugate() * y for x, y in zip(a, b))


def vector_norm_squared(vector: Vector) -> float:
    return float(vector_inner(vector, vector).real)


def vector_norm(vector: Vector) -> float:
    return math.sqrt(max(0.0, vector_norm_squared(vector)))


def normalize(vector: Vector) -> Vector:
    norm = vector_norm(vector)
    if norm < TOLERANCE:
        raise ValueError("Cannot normalize the zero vector.")
    return [x / norm for x in vector]


def matrix_shape(matrix: Matrix) -> tuple[int, int]:
    rows = len(matrix)
    columns = len(matrix[0]) if rows else 0
    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal lengths.")
    return rows, columns


def matrix_identity(size: int) -> Matrix:
    return [
        [1.0 + 0.0j if row == column else 0.0 + 0.0j
         for column in range(size)]
        for row in range(size)
    ]


def matrix_zero(rows: int, columns: int) -> Matrix:
    return [[0.0 + 0.0j for _ in range(columns)] for _ in range(rows)]


def matrix_add(a: Matrix, b: Matrix) -> Matrix:
    if matrix_shape(a) != matrix_shape(b):
        raise ValueError("Matrices must have the same dimensions.")
    return [
        [x + y for x, y in zip(row_a, row_b)]
        for row_a, row_b in zip(a, b)
    ]


def matrix_scale(scalar: complex, matrix: Matrix) -> Matrix:
    return [[scalar * value for value in row] for row in matrix]


def matrix_multiply(a: Matrix, b: Matrix) -> Matrix:
    rows_a, cols_a = matrix_shape(a)
    rows_b, cols_b = matrix_shape(b)

    if cols_a != rows_b:
        raise ValueError("Inner matrix dimensions must agree.")

    return [
        [
            sum(a[row][k] * b[k][column] for k in range(cols_a))
            for column in range(cols_b)
        ]
        for row in range(rows_a)
    ]


def matrix_vector_multiply(matrix: Matrix, vector: Vector) -> Vector:
    rows, columns = matrix_shape(matrix)

    if columns != len(vector):
        raise ValueError("Matrix and vector dimensions do not agree.")

    return [
        sum(matrix[row][column] * vector[column]
            for column in range(columns))
        for row in range(rows)
    ]


def conjugate_transpose(matrix: Matrix) -> Matrix:
    rows, columns = matrix_shape(matrix)
    return [
        [matrix[row][column].conjugate() for row in range(rows)]
        for column in range(columns)
    ]


def trace(matrix: Matrix) -> complex:
    rows, columns = matrix_shape(matrix)
    if rows != columns:
        raise ValueError("Trace requires a square matrix.")
    return sum(matrix[i][i] for i in range(rows))


def matrix_is_close(a: Matrix, b: Matrix, tolerance: float = TOLERANCE) -> bool:
    if matrix_shape(a) != matrix_shape(b):
        return False

    return all(
        abs(x - y) <= tolerance
        for row_a, row_b in zip(a, b)
        for x, y in zip(row_a, row_b)
    )


def vector_is_close(a: Vector, b: Vector, tolerance: float = TOLERANCE) -> bool:
    return len(a) == len(b) and all(
        abs(x - y) <= tolerance for x, y in zip(a, b)
    )


def matrix_power(matrix: Matrix, exponent: int) -> Matrix:
    """
    Integer matrix power using repeated squaring.

    This is useful for finite-dimensional demonstrations of projectors,
    Pauli matrices, and simple unitary operators.
    """
    rows, columns = matrix_shape(matrix)
    if rows != columns:
        raise ValueError("Matrix power requires a square matrix.")
    if exponent < 0:
        raise ValueError("This implementation only accepts non-negative powers.")

    result = matrix_identity(rows)
    base = matrix
    power = exponent

    while power:
        if power & 1:
            result = matrix_multiply(result, base)
        base = matrix_multiply(base, base)
        power >>= 1

    return result


def pretty_complex(value: complex, digits: int = 4) -> str:
    value = clean_complex(value)

    if abs(value.imag) < 10 ** (-digits):
        return f"{value.real:.{digits}f}"

    if abs(value.real) < 10 ** (-digits):
        return f"{value.imag:.{digits}f}i"

    sign = "+" if value.imag >= 0 else "-"
    return f"{value.real:.{digits}f} {sign} {abs(value.imag):.{digits}f}i"


def print_vector(name: str, vector: Vector) -> None:
    formatted = ", ".join(pretty_complex(x) for x in clean_vector(vector))
    print(f"{name} = [{formatted}]")


def print_matrix(name: str, matrix: Matrix) -> None:
    print(f"{name} =")
    for row in clean_matrix(matrix):
        print("  [" + ", ".join(pretty_complex(x) for x in row) + "]")


# ============================================================================
# SECTION 2: BASIC QUANTUM STATES
# ============================================================================

KET_0: Vector = [1.0 + 0.0j, 0.0 + 0.0j]
KET_1: Vector = [0.0 + 0.0j, 1.0 + 0.0j]

KET_PLUS: Vector = normalize([
    1.0 + 0.0j,
    1.0 + 0.0j,
])

KET_MINUS: Vector = normalize([
    1.0 + 0.0j,
    -1.0 + 0.0j,
])

KET_Y_PLUS: Vector = normalize([
    1.0 + 0.0j,
    1.0j,
])

KET_Y_MINUS: Vector = normalize([
    1.0 + 0.0j,
    -1.0j,
])

KET_T: Vector = normalize([
    1.0 + 0.0j,
    cmath.exp(1j * math.pi / 4),
])


def validate_state(state: Vector, tolerance: float = TOLERANCE) -> None:
    """A pure quantum state must be normalized to unit norm."""
    norm_squared = vector_norm_squared(state)

    if abs(norm_squared - 1.0) > tolerance:
        raise ValueError(
            f"State is not normalized. Norm squared = {norm_squared}"
        )


def global_phase_equivalent(a: Vector, b: Vector, tolerance: float = TOLERANCE) -> bool:
    """
    Two pure states that differ only by a global phase represent the same
    physical state.

    If b[0] is nonzero, use it to infer the phase. Otherwise find another
    nonzero component.
    """
    if len(a) != len(b):
        return False

    validate_state(a, tolerance)
    validate_state(b, tolerance)

    pivot = None
    for index, value in enumerate(b):
        if abs(value) > tolerance:
            pivot = index
            break

    if pivot is None:
        return False

    phase = a[pivot] / b[pivot]

    if abs(abs(phase) - 1.0) > tolerance:
        return False

    return all(
        abs(a_i - phase * b_i) <= tolerance
        for a_i, b_i in zip(a, b)
    )


def demonstrate_basic_state() -> None:
    print("\n" + "=" * 78)
    print("1. QUANTUM STATES AND AMPLITUDES")
    print("=" * 78)

    print_vector("|0>", KET_0)
    print_vector("|1>", KET_1)
    print_vector("|+>", KET_PLUS)

    print("\nA general qubit can be written as:")
    print("  |psi> = alpha |0> + beta |1>")
    print("with |alpha|^2 + |beta|^2 = 1.")

    alpha = math.sqrt(0.7)
    beta = cmath.sqrt(0.3) * cmath.exp(1j * 0.8)

    state = normalize([alpha, beta])
    validate_state(state)

    p_zero = abs(state[0]) ** 2
    p_one = abs(state[1]) ** 2

    print_vector("Example |psi>", state)
    print(f"P(0) = |alpha|^2 = {p_zero:.6f}")
    print(f"P(1) = |beta|^2  = {p_one:.6f}")
    print(f"P(0) + P(1)    = {p_zero + p_one:.6f}")

    global_phase_state = vector_scale(cmath.exp(1j * 0.73), KET_PLUS)

    print(
        "\nGlobal phase equivalence:",
        global_phase_equivalent(KET_PLUS, global_phase_state)
    )


# ============================================================================
# SECTION 3: OBSERVABLES
# ============================================================================

# Pauli matrices are the standard two-level examples.
SIGMA_X: Matrix = [
    [0.0 + 0.0j, 1.0 + 0.0j],
    [1.0 + 0.0j, 0.0 + 0.0j],
]

SIGMA_Y: Matrix = [
    [0.0 + 0.0j, -1.0j],
    [1.0j, 0.0 + 0.0j],
]

SIGMA_Z: Matrix = [
    [1.0 + 0.0j, 0.0 + 0.0j],
    [0.0 + 0.0j, -1.0 + 0.0j],
]


def is_hermitian(matrix: Matrix, tolerance: float = TOLERANCE) -> bool:
    return matrix_is_close(matrix, conjugate_transpose(matrix), tolerance)


def expectation_value(state: Vector, observable: Matrix) -> complex:
    """
    Calculate <A> = <psi|A|psi> for a normalized pure state.

    For a Hermitian observable, the result is real apart from numerical
    floating-point noise.
    """
    validate_state(state)
    transformed = matrix_vector_multiply(observable, state)
    return vector_inner(state, transformed)


def demonstrate_observables() -> None:
    print("\n" + "=" * 78)
    print("2. OBSERVABLES AND EXPECTATION VALUES")
    print("=" * 78)

    print_matrix("Pauli X", SIGMA_X)
    print_matrix("Pauli Y", SIGMA_Y)
    print_matrix("Pauli Z", SIGMA_Z)

    for name, observable in [
        ("X", SIGMA_X),
        ("Y", SIGMA_Y),
        ("Z", SIGMA_Z),
    ]:
        print(f"\nIs {name} Hermitian? {is_hermitian(observable)}")

    state = KET_PLUS

    print("\nFor |+>, the expectation values are:")
    for name, observable in [
        ("X", SIGMA_X),
        ("Y", SIGMA_Y),
        ("Z", SIGMA_Z),
    ]:
        value = expectation_value(state, observable)
        print(f"<{name}> = {pretty_complex(value)}")

    print(
        "\nAn expectation value is an average over many identically prepared "
        "experiments. It is not necessarily an individual measurement result."
    )


# ============================================================================
# SECTION 4: EIGENVALUES, EIGENVECTORS, AND SPECTRAL DECOMPOSITION
# ============================================================================

@dataclass
class SpectralComponent:
    eigenvalue: float
    eigenvector: Vector


def normalize_phase(vector: Vector) -> Vector:
    """
    Choose a deterministic phase for displaying a vector.

    This does not change its physical state.
    """
    for value in vector:
        if abs(value) > TOLERANCE:
            phase = value / abs(value)
            return [x / phase for x in vector]
    return vector


def eigenpairs_2x2_hermitian(matrix: Matrix) -> list[SpectralComponent]:
    """
    Find eigenpairs of a 2x2 Hermitian matrix analytically.

    For
        [[a, c],
         [c*, d]]
    the characteristic polynomial is
        lambda^2 - (a+d) lambda + (ad-|c|^2).

    The implementation assumes numerical Hermiticity and is intended for
    educational two-dimensional examples.
    """
    rows, columns = matrix_shape(matrix)

    if (rows, columns) != (2, 2):
        raise ValueError("This educational solver only handles 2x2 matrices.")

    if not is_hermitian(matrix):
        raise ValueError("The matrix must be Hermitian.")

    a = matrix[0][0].real
    d = matrix[1][1].real
    c = matrix[0][1]

    discriminant = max(
        0.0,
        (a - d) ** 2 + 4.0 * abs(c) ** 2
    )

    root = math.sqrt(discriminant)

    eigenvalue_1 = (a + d + root) / 2.0
    eigenvalue_2 = (a + d - root) / 2.0

    components: list[SpectralComponent] = []

    for eigenvalue in [eigenvalue_1, eigenvalue_2]:
        # Solve (A - lambda I)v = 0.
        row_a = [a - eigenvalue, c]
        row_b = [c.conjugate(), d - eigenvalue]

        if abs(row_a[0]) + abs(row_a[1]) > TOLERANCE:
            vector = [-row_a[1], row_a[0]]
        elif abs(row_b[0]) + abs(row_b[1]) > TOLERANCE:
            vector = [-row_b[1], row_b[0]]
        else:
            vector = [1.0 + 0.0j, 0.0 + 0.0j]

        vector = normalize(vector)
        vector = normalize_phase(vector)

        components.append(
            SpectralComponent(
                eigenvalue=float(eigenvalue),
                eigenvector=vector,
            )
        )

    return components


def outer_product(a: Vector, b: Vector) -> Matrix:
    """Return |a><b|."""
    return [
        [a_value * b_value.conjugate() for b_value in b]
        for a_value in a
    ]


def projector_from_state(state: Vector) -> Matrix:
    validate_state(state)
    return outer_product(state, state)


def demonstrate_spectral_structure() -> None:
    print("\n" + "=" * 78)
    print("3. OBSERVABLES AS HERMITIAN OPERATORS")
    print("=" * 78)

    for name, observable in [
        ("X", SIGMA_X),
        ("Y", SIGMA_Y),
        ("Z", SIGMA_Z),
    ]:
        print(f"\nEigenstructure of {name}:")
        for component in eigenpairs_2x2_hermitian(observable):
            print(
                f"  eigenvalue = {component.eigenvalue:+.1f}, "
                f"eigenvector = "
                f"[{', '.join(pretty_complex(x) for x in component.eigenvector)}]"
            )

    print("\nSpectral decomposition of Z:")
    p_plus = projector_from_state(KET_0)
    p_minus = projector_from_state(KET_1)

    spectral_z = matrix_add(
        matrix_scale(+1.0, p_plus),
        matrix_scale(-1.0, p_minus),
    )

    print_matrix("Z reconstructed from projectors", spectral_z)

    print(
        "\nFor a discrete observable A = sum_a a P_a, the P_a are projectors "
        "onto eigenspaces. Measurement probabilities are determined by these "
        "projectors."
    )


# ============================================================================
# SECTION 5: BORN RULE AND PROJECTIVE MEASUREMENT
# ============================================================================

@dataclass
class MeasurementOutcome:
    label: str
    eigenvalue: complex
    probability: float
    projector: Matrix
    post_state: Vector


def projective_measurement(
    state: Vector,
    outcomes: Sequence[tuple[str, complex, Vector]],
) -> list[MeasurementOutcome]:
    """
    Perform a projective measurement description.

    Each tuple contains:
        label
        eigenvalue
        normalized eigenvector

    For a nondegenerate projective measurement:
        P_i = |i><i|
        p_i = <psi|P_i|psi> = |<i|psi>|^2
        |psi_i> = P_i|psi> / sqrt(p_i)

    The function returns the possible outcomes and conditional states.
    """
    validate_state(state)

    result = []

    for label, eigenvalue, eigenvector in outcomes:
        eigenvector = normalize(eigenvector)
        projector = projector_from_state(eigenvector)

        projected = matrix_vector_multiply(projector, state)
        probability = max(0.0, vector_norm_squared(projected))

        if probability > TOLERANCE:
            post_state = normalize(projected)
        else:
            # A zero-probability branch has no physically realized
            # conditional state. The vector is kept only as a placeholder
            # for a complete return structure.
            post_state = [0.0 + 0.0j for _ in state]

        result.append(
            MeasurementOutcome(
                label=label,
                eigenvalue=eigenvalue,
                probability=probability,
                projector=projector,
                post_state=post_state,
            )
        )

    total = sum(item.probability for item in result)

    if abs(total - 1.0) > 1e-8:
        raise ValueError(
            "Measurement projectors do not form a complete orthonormal "
            f"basis. Probability total = {total}"
        )

    return result


Z_OUTCOMES = [
    ("z=+1", +1.0, KET_0),
    ("z=-1", -1.0, KET_1),
]

X_OUTCOMES = [
    ("x=+1", +1.0, KET_PLUS),
    ("x=-1", -1.0, KET_MINUS),
]

Y_OUTCOMES = [
    ("y=+1", +1.0, KET_Y_PLUS),
    ("y=-1", -1.0, KET_Y_MINUS),
]


def demonstrate_born_rule() -> None:
    print("\n" + "=" * 78)
    print("4. BORN RULE AND PROJECTIVE MEASUREMENT")
    print("=" * 78)

    state = KET_T

    print_vector("Initial state", state)

    print("\nMeasurement in the computational/Z basis:")
    results = projective_measurement(state, Z_OUTCOMES)

    for result in results:
        print(
            f"  {result.label}: probability = {result.probability:.6f}"
        )

        if result.probability > TOLERANCE:
            print_vector("    conditional state", result.post_state)

    print(
        "\nBorn rule for a projector P:"
        "\n  P(outcome) = <psi|P|psi>"
        "\nFor a rank-one projector |phi><phi|:"
        "\n  P(outcome) = |<phi|psi>|^2"
    )


# ============================================================================
# SECTION 6: SIMULATING REPEATED MEASUREMENTS
# ============================================================================

def weighted_choice(
    labels: Sequence[str],
    probabilities: Sequence[float],
    rng: random.Random,
) -> str:
    if len(labels) != len(probabilities):
        raise ValueError("Labels and probabilities must have equal length.")

    total = sum(probabilities)
    if total <= 0:
        raise ValueError("At least one probability must be positive.")

    target = rng.random() * total
    cumulative = 0.0

    for label, probability in zip(labels, probabilities):
        cumulative += probability
        if target < cumulative:
            return label

    return labels[-1]


def simulate_measurements(
    state: Vector,
    outcomes: Sequence[tuple[str, complex, Vector]],
    trials: int,
    seed: int = 12345,
) -> dict[str, int]:
    if trials <= 0:
        raise ValueError("Number of trials must be positive.")

    measurement = projective_measurement(state, outcomes)
    labels = [item.label for item in measurement]
    probabilities = [item.probability for item in measurement]

    rng = random.Random(seed)
    counts = {label: 0 for label in labels}

    for _ in range(trials):
        selected = weighted_choice(labels, probabilities, rng)
        counts[selected] += 1

    return counts


def demonstrate_sampling() -> None:
    print("\n" + "=" * 78)
    print("5. REPEATED MEASUREMENTS AND FREQUENCY")
    print("=" * 78)

    state = KET_T
    trials = 20_000

    counts = simulate_measurements(state, Z_OUTCOMES, trials)

    print(f"Prepared state: |T>")
    print(f"Trials: {trials}")

    for label, count in counts.items():
        print(
            f"  {label}: count = {count:5d}, "
            f"frequency = {count / trials:.6f}"
        )

    print(
        "\nFinite experimental frequencies fluctuate around the Born "
        "probabilities. Increasing the number of trials reduces typical "
        "sampling fluctuations."
    )


# ============================================================================
# SECTION 7: STATE COLLAPSE AND THE MEASUREMENT POSTULATE
# ============================================================================

def demonstrate_collapse() -> None:
    print("\n" + "=" * 78)
    print("6. COLLAPSE / STATE UPDATE")
    print("=" * 78)

    state = KET_PLUS

    print("Initial state:")
    print_vector("|+>", state)

    results = projective_measurement(state, Z_OUTCOMES)

    print("\nA Z measurement has two possible branches:")

    for result in results:
        print(
            f"\nOutcome {result.label}, probability = "
            f"{result.probability:.6f}"
        )

        if result.probability > TOLERANCE:
            print_vector("Post-measurement state", result.post_state)

    print(
        "\nThe state update is conditional on the recorded outcome:"
        "\n  |psi> -> P_a|psi> / sqrt(<psi|P_a|psi>)"
        "\nwhen the probability is nonzero."
    )

    print(
        "\nThe phrase 'collapse' describes this conditional state update in "
        "the standard textbook measurement formalism. The formalism predicts "
        "the outcome probabilities and the state used for subsequent "
        "predictions."
    )


# ============================================================================
# SECTION 8: DEGENERATE MEASUREMENTS
# ============================================================================

def demonstrate_degenerate_measurement() -> None:
    print("\n" + "=" * 78)
    print("7. DEGENERATE OBSERVABLES")
    print("=" * 78)

    print(
        "A degenerate eigenvalue corresponds to an eigenspace with dimension "
        "greater than one. The measurement projector is then the projector "
        "onto the entire eigenspace, not necessarily onto one particular "
        "basis vector."
    )

    # A three-dimensional state with an observable whose first two basis
    # states share the same eigenvalue.
    state_3d = normalize([
        math.sqrt(0.2),
        math.sqrt(0.3),
        math.sqrt(0.5),
    ])

    p_degenerate = [
        [1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, 1.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
    ]

    p_third = [
        [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, 0.0 + 0.0j, 1.0 + 0.0j],
    ]

    projected = matrix_vector_multiply(p_degenerate, state_3d)
    probability = vector_norm_squared(projected)
    post_state = normalize(projected)

    print_vector("Initial 3D state", state_3d)
    print(f"\nProbability of degenerate outcome = {probability:.6f}")
    print_vector("Conditional state in the degenerate subspace", post_state)

    print(
        "\nThe measurement identifies the subspace but does not, by itself, "
        "distinguish the individual states inside that subspace."
    )

    # Completeness demonstration.
    completeness = matrix_add(p_degenerate, p_third)
    print(
        "\nP_degenerate + P_third equals identity:",
        matrix_is_close(completeness, matrix_identity(3))
    )


# ============================================================================
# SECTION 9: SEQUENTIAL MEASUREMENTS
# ============================================================================

def perform_one_projective_measurement(
    state: Vector,
    outcomes: Sequence[tuple[str, complex, Vector]],
    rng: random.Random,
) -> MeasurementOutcome:
    results = projective_measurement(state, outcomes)
    labels = [result.label for result in results]
    probabilities = [result.probability for result in results]

    selected_label = weighted_choice(labels, probabilities, rng)

    selected = next(
        result for result in results
        if result.label == selected_label
    )

    return selected


def demonstrate_sequential_measurements() -> None:
    print("\n" + "=" * 78)
    print("8. SEQUENTIAL MEASUREMENTS")
    print("=" * 78)

    print(
        "Consider an initial |0> state, followed by X and then Z "
        "measurements. X changes |0> into |1> deterministically. The later "
        "Z measurement therefore returns -1 deterministically."
    )

    initial = KET_0

    x_results = projective_measurement(initial, X_OUTCOMES)

    for result in x_results:
        if result.probability > TOLERANCE:
            print(
                f"X outcome {result.label} has probability "
                f"{result.probability:.6f}"
            )
            print_vector("State after X measurement", result.post_state)

            z_results = projective_measurement(result.post_state, Z_OUTCOMES)

            for z_result in z_results:
                if z_result.probability > TOLERANCE:
                    print(
                        f"Then Z outcome {z_result.label} has probability "
                        f"{z_result.probability:.6f}"
                    )

    print(
        "\nA measurement can change the state, so probabilities for a later "
        "measurement generally depend on whether and how an earlier "
        "measurement occurred."
    )


# ============================================================================
# SECTION 10: COMMUTATORS, COMPATIBILITY, AND ORDER EFFECTS
# ============================================================================

def matrix_commutator(a: Matrix, b: Matrix) -> Matrix:
    """[A,B] = AB - BA."""
    ab = matrix_multiply(a, b)
    ba = matrix_multiply(b, a)
    return matrix_add(ab, matrix_scale(-1.0, ba))


def matrix_anticommutator(a: Matrix, b: Matrix) -> Matrix:
    """{A,B} = AB + BA."""
    return matrix_add(
        matrix_multiply(a, b),
        matrix_multiply(b, a),
    )


def demonstrate_commutators() -> None:
    print("\n" + "=" * 78)
    print("9. COMPATIBILITY, COMMUTATORS, AND ORDER")
    print("=" * 78)

    comm_xy = matrix_commutator(SIGMA_X, SIGMA_Y)
    comm_xz = matrix_commutator(SIGMA_X, SIGMA_Z)

    print_matrix("[X,Y]", comm_xy)
    print_matrix("[X,Z]", comm_xz)

    print(
        "\nFor X and Y:"
        "\n  [X,Y] = 2iZ"
        "\nThe nonzero commutator indicates that the observables are "
        "incompatible in the standard simultaneous-eigenbasis sense."
    )

    print(
        "\nCommuting observables can be simultaneously diagonalized under "
        "appropriate finite-dimensional conditions. Noncommuting observables "
        "generally do not possess a common complete eigenbasis."
    )


# ============================================================================
# SECTION 11: UNCERTAINTY RELATIONS
# ============================================================================

def expectation_squared(state: Vector, observable: Matrix) -> complex:
    squared = matrix_multiply(observable, observable)
    return expectation_value(state, squared)


def variance(state: Vector, observable: Matrix) -> float:
    mean = expectation_value(state, observable).real
    second_moment = expectation_squared(state, observable).real
    result = second_moment - mean * mean
    return max(0.0, result)


def standard_deviation(state: Vector, observable: Matrix) -> float:
    return math.sqrt(variance(state, observable))


def demonstrate_uncertainty() -> None:
    print("\n" + "=" * 78)
    print("10. UNCERTAINTY")
    print("=" * 78)

    state = KET_0

    sigma_x = standard_deviation(state, SIGMA_X)
    sigma_z = standard_deviation(state, SIGMA_Z)

    commutator_expectation = expectation_value(
        state,
        matrix_commutator(SIGMA_X, SIGMA_Z),
    )

    lower_bound = 0.5 * abs(commutator_expectation)

    print(f"State = |0>")
    print(f"Delta X = {sigma_x:.6f}")
    print(f"Delta Z = {sigma_z:.6f}")
    print(f"Delta X * Delta Z = {sigma_x * sigma_z:.6f}")
    print(f"Robertson lower bound = {lower_bound:.6f}")

    print(
        "\nThe uncertainty relation concerns the statistical spreads of "
        "outcomes for a state. It is not simply a statement that an "
        "instrument is inaccurate."
    )

    print(
        "\nRobertson form:"
        "\n  Delta A Delta B >= 1/2 |< [A,B] >|"
    )


# ============================================================================
# SECTION 12: DENSITY MATRICES
# ============================================================================

DensityMatrix = Matrix


def density_matrix_from_pure_state(state: Vector) -> DensityMatrix:
    validate_state(state)
    return projector_from_state(state)


def density_matrix_from_ensemble(
    states: Sequence[Vector],
    probabilities: Sequence[float],
) -> DensityMatrix:
    if len(states) != len(probabilities):
        raise ValueError("States and probabilities must have equal lengths.")

    if not states:
        raise ValueError("An ensemble cannot be empty.")

    if any(p < -TOLERANCE for p in probabilities):
        raise ValueError("Probabilities cannot be negative.")

    total = sum(probabilities)

    if abs(total - 1.0) > TOLERANCE:
        raise ValueError(
            f"Ensemble probabilities must sum to one, got {total}."
        )

    dimension = len(states[0])
    result = matrix_zero(dimension, dimension)

    for state, probability in zip(states, probabilities):
        validate_state(state)
        if len(state) != dimension:
            raise ValueError("All states must have equal dimension.")
        result = matrix_add(
            result,
            matrix_scale(
                probability,
                density_matrix_from_pure_state(state),
            ),
        )

    return result


def density_matrix_expectation(
    density_matrix: DensityMatrix,
    observable: Matrix,
) -> complex:
    """Tr(rho A)."""
    product = matrix_multiply(density_matrix, observable)
    return trace(product)


def density_matrix_purity(density_matrix: DensityMatrix) -> float:
    squared = matrix_multiply(density_matrix, density_matrix)
    return float(trace(squared).real)


def density_matrix_is_hermitian(
    density_matrix: DensityMatrix,
    tolerance: float = TOLERANCE,
) -> bool:
    return is_hermitian(density_matrix, tolerance)


def density_matrix_has_unit_trace(
    density_matrix: DensityMatrix,
    tolerance: float = TOLERANCE,
) -> bool:
    return abs(trace(density_matrix).real - 1.0) <= tolerance


def demonstrate_density_matrices() -> None:
    print("\n" + "=" * 78)
    print("11. DENSITY MATRICES AND MIXED STATES")
    print("=" * 78)

    pure_plus = density_matrix_from_pure_state(KET_PLUS)

    mixed = density_matrix_from_ensemble(
        states=[KET_0, KET_1],
        probabilities=[0.5, 0.5],
    )

    print_matrix("rho for |+><+|", pure_plus)
    print_matrix("rho for 50/50 mixture of |0> and |1>", mixed)

    print(f"\nPurity of pure state = {density_matrix_purity(pure_plus):.6f}")
    print(f"Purity of mixed state = {density_matrix_purity(mixed):.6f}")

    print(
        "\nFor a normalized density matrix:"
        "\n  rho = rho†"
        "\n  Tr(rho) = 1"
        "\n  rho is positive semidefinite"
        "\nA pure state satisfies Tr(rho²) = 1. A genuinely mixed state has "
        "Tr(rho²) < 1."
    )

    print(
        "\nThe density matrix can represent either classical uncertainty "
        "about preparation or quantum statistical states. Distinguishing "
        "these interpretations requires attention to how the ensemble was "
        "physically prepared."
    )


# ============================================================================
# SECTION 13: PROJECTIVE MEASUREMENTS WITH DENSITY MATRICES
# ============================================================================

def projector_probability(
    density_matrix: DensityMatrix,
    projector: Matrix,
) -> float:
    probability = density_matrix_expectation(density_matrix, projector).real

    # Small negative values can arise from floating-point roundoff.
    if -TOLERANCE < probability < 0:
        probability = 0.0

    return probability


def luseless_rank_one_update(
    density_matrix: DensityMatrix,
    projector: Matrix,
    probability: float,
) -> DensityMatrix:
    """
    Lüders update for a single projective outcome:
        rho' = P rho P / p

    This works for a projector, including a projector onto a degenerate
    eigenspace. It is named explicitly to distinguish it from a generic
    state-update operation.
    """
    if probability <= TOLERANCE:
        raise ValueError("Cannot condition on a zero-probability outcome.")

    numerator = matrix_multiply(
        matrix_multiply(projector, density_matrix),
        projector,
    )

    return matrix_scale(1.0 / probability, numerator)


def demonstrate_luders_update() -> None:
    print("\n" + "=" * 78)
    print("12. LÜDERS STATE UPDATE")
    print("=" * 78)

    rho = density_matrix_from_pure_state(KET_PLUS)
    projector = projector_from_state(KET_0)

    probability = projector_probability(rho, projector)
    updated = luseless_rank_one_update(rho, projector, probability)

    print(f"Outcome probability = {probability:.6f}")
    print_matrix("Updated density matrix", updated)

    print(
        "\nFor a projective measurement outcome represented by P:"
        "\n  rho -> P rho P / Tr(P rho)"
        "\nwhen Tr(P rho) > 0."
    )


# ============================================================================
# SECTION 14: GENERALIZED MEASUREMENTS AND POVMs
# ============================================================================

def matrix_multiply_chain(*matrices: Matrix) -> Matrix:
    if not matrices:
        raise ValueError("At least one matrix is required.")

    result = matrices[0]
    for matrix in matrices[1:]:
        result = matrix_multiply(result, matrix)
    return result


def dagger(matrix: Matrix) -> Matrix:
    return conjugate_transpose(matrix)


def povm_probability(
    state: Vector,
    effect: Matrix,
) -> float:
    """
    For a POVM effect E:
        p = <psi|E|psi>
    with 0 <= E <= I.
    """
    probability = expectation_value(state, effect).real

    if -TOLERANCE < probability < 0:
        probability = 0.0

    return probability


def demonstrate_povm() -> None:
    print("\n" + "=" * 78)
    print("13. GENERALIZED MEASUREMENTS AND POVMs")
    print("=" * 78)

    # A simple three-outcome qubit POVM can be constructed from scaled
    # projectors. For a pedagogical example, use the computational basis
    # effects split into multiple outcomes.
    p0 = projector_from_state(KET_0)
    p1 = projector_from_state(KET_1)

    effects = [
        matrix_scale(0.5, p0),
        matrix_scale(0.5, p0),
        p1,
    ]

    completeness = matrix_zero(2, 2)
    for effect in effects:
        completeness = matrix_add(completeness, effect)

    print_matrix("Sum of POVM effects", completeness)
    print(
        "POVM completeness condition:",
        matrix_is_close(completeness, matrix_identity(2))
    )

    state = KET_PLUS

    probabilities = [
        povm_probability(state, effect)
        for effect in effects
    ]

    print("\nOutcome probabilities for |+>:")
    for index, probability in enumerate(probabilities, start=1):
        print(f"  outcome {index}: {probability:.6f}")

    print(f"  total: {sum(probabilities):.6f}")

    print(
        "\nA POVM is a collection of positive operators {E_m} satisfying:"
        "\n  E_m >= 0"
        "\n  sum_m E_m = I"
        "\nThe probability is p(m) = Tr(rho E_m)."
    )

    print(
        "\nA POVM specifies outcome probabilities but does not by itself "
        "uniquely specify the post-measurement state. Measurement operators "
        "provide the additional state-update information."
    )


# ============================================================================
# SECTION 15: KRAUS / MEASUREMENT OPERATORS
# ============================================================================

def measurement_probability_from_kraus(
    density_matrix: DensityMatrix,
    operator: Matrix,
) -> float:
    """p(m) = Tr(M_m rho M_m^dagger)."""
    transformed = matrix_multiply_chain(
        operator,
        density_matrix,
        dagger(operator),
    )
    return max(0.0, trace(transformed).real)


def demonstrate_kraus_measurement() -> None:
    print("\n" + "=" * 78)
    print("14. MEASUREMENT OPERATORS AND KRAUS REPRESENTATION")
    print("=" * 78)

    # Projective Z measurement:
    # M_0 = |0><0| and M_1 = |1><1|.
    m0 = projector_from_state(KET_0)
    m1 = projector_from_state(KET_1)

    rho = density_matrix_from_pure_state(KET_PLUS)

    p0 = measurement_probability_from_kraus(rho, m0)
    p1 = measurement_probability_from_kraus(rho, m1)

    print(f"p(0) = {p0:.6f}")
    print(f"p(1) = {p1:.6f}")
    print(f"total = {p0 + p1:.6f}")

    print(
        "\nA measurement operation M_m obeys:"
        "\n  E_m = M_m^dagger M_m"
        "\n  p(m) = Tr(M_m rho M_m^dagger)"
        "\nThe conditional post-measurement state is:"
        "\n  rho_m = M_m rho M_m^dagger / p(m)"
    )

    print(
        "\nDifferent sets of measurement operators can produce the same POVM "
        "effects while producing different conditional states. Therefore "
        "the observable statistics alone do not completely specify physical "
        "measurement back-action."
    )


# ============================================================================
# SECTION 16: NONSELECTIVE MEASUREMENT
# ============================================================================

def nonselective_projective_measurement(
    density_matrix: DensityMatrix,
    projectors: Sequence[Matrix],
) -> DensityMatrix:
    """
    Average over outcomes when the classical result is discarded:
        rho' = sum_i P_i rho P_i
    """
    result = matrix_zero(*matrix_shape(density_matrix))

    for projector in projectors:
        contribution = matrix_multiply_chain(
            projector,
            density_matrix,
            projector,
        )
        result = matrix_add(result, contribution)

    return result


def demonstrate_nonselective_measurement() -> None:
    print("\n" + "=" * 78)
    print("15. SELECTIVE VS NONSELECTIVE MEASUREMENT")
    print("=" * 78)

    rho = density_matrix_from_pure_state(KET_PLUS)

    p0 = projector_from_state(KET_0)
    p1 = projector_from_state(KET_1)

    print("Initial state:")
    print_matrix("rho", rho)

    final_state = nonselective_projective_measurement(
        rho,
        [p0, p1],
    )

    print(
        "\nAfter a Z measurement when the result is discarded:"
    )
    print_matrix("rho'", final_state)

    print(
        "\nSelective measurement retains information about which branch "
        "occurred. Nonselective measurement averages over all branches and "
        "can destroy coherence in the measurement basis."
    )

    print(
        f"\nInitial purity = {density_matrix_purity(rho):.6f}"
        f"\nFinal purity   = {density_matrix_purity(final_state):.6f}"
    )


# ============================================================================
# SECTION 17: MEASUREMENT DISTURBANCE AND BASIS DEPENDENCE
# ============================================================================

def demonstrate_basis_dependence() -> None:
    print("\n" + "=" * 78)
    print("16. MEASUREMENT BASIS MATTERS")
    print("=" * 78)

    state = KET_0

    x_results = projective_measurement(state, X_OUTCOMES)
    z_results = projective_measurement(state, Z_OUTCOMES)

    print("Initial state = |0>")

    print("\nX measurement:")
    for result in x_results:
        print(
            f"  {result.label}: P = {result.probability:.6f}"
        )

    print("\nZ measurement:")
    for result in z_results:
        print(
            f"  {result.label}: P = {result.probability:.6f}"
        )

    print(
        "\nThe same physical state can produce different probability "
        "distributions because probabilities depend on the measurement being "
        "performed."
    )

    print(
        "\nThis is one reason the phrase 'the probability of the state' is "
        "incomplete. A probability must be associated with a specified "
        "measurement event."
    )


# ============================================================================
# SECTION 18: CONDITIONAL PROBABILITIES AND QUANTUM BAYESIAN STRUCTURE
# ============================================================================

def sequential_probability(
    initial_state: Vector,
    first_outcome: tuple[str, complex, Vector],
    second_outcome: tuple[str, complex, Vector],
) -> float:
    first_results = projective_measurement(
        initial_state,
        [first_outcome],
    )

    # This helper intentionally expects a complete branch only in examples
    # where the first projector's probability is interpreted conditionally.
    first_projector = projector_from_state(first_outcome[2])
    first_probability = vector_norm_squared(
        matrix_vector_multiply(first_projector, initial_state)
    )

    if first_probability <= TOLERANCE:
        return 0.0

    projected = matrix_vector_multiply(
        first_projector,
        initial_state,
    )
    conditional_state = normalize(projected)

    second_projector = projector_from_state(second_outcome[2])
    second_probability = vector_norm_squared(
        matrix_vector_multiply(second_projector, conditional_state)
    )

    return first_probability * second_probability


def demonstrate_sequential_probability() -> None:
    print("\n" + "=" * 78)
    print("17. SEQUENTIAL PROBABILITY")
    print("=" * 78)

    initial = KET_T

    probability = sequential_probability(
        initial,
        Z_OUTCOMES[0],
        X_OUTCOMES[0],
    )

    print(
        "Probability of first obtaining Z=+1 and then X=+1 "
        f"= {probability:.6f}"
    )

    print(
        "\nFor a sequence of measurements, the joint probability is obtained "
        "by multiplying the probability of an earlier outcome by the "
        "conditional probability of the later outcome after the state update."
    )


# ============================================================================
# SECTION 19: GLOBAL PHASE VS RELATIVE PHASE
# ============================================================================

def demonstrate_phase() -> None:
    print("\n" + "=" * 78)
    print("18. GLOBAL PHASE AND RELATIVE PHASE")
    print("=" * 78)

    state_a = KET_PLUS
    state_b = vector_scale(cmath.exp(1j * 1.2), state_a)
    state_c = normalize([1.0 + 0.0j, 1.0j])

    print(
        "Global-phase equivalent:",
        global_phase_equivalent(state_a, state_b)
    )

    print(
        "Different relative phase:",
        global_phase_equivalent(state_a, state_c)
    )

    print(
        "\nMultiplying every amplitude by the same phase does not change "
        "measurement probabilities. Changing the phase between components "
        "can change interference and therefore can change measurement "
        "statistics in another basis."
    )

    z_a = projective_measurement(state_a, Z_OUTCOMES)
    z_c = projective_measurement(state_c, Z_OUTCOMES)

    x_a = projective_measurement(state_a, X_OUTCOMES)
    x_c = projective_measurement(state_c, X_OUTCOMES)

    print("\nZ-basis probabilities:")
    print(
        "  |+> :",
        [round(result.probability, 4) for result in z_a]
    )
    print(
        "  relative-phase state :",
        [round(result.probability, 4) for result in z_c]
    )

    print("\nX-basis probabilities:")
    print(
        "  |+> :",
        [round(result.probability, 4) for result in x_a]
    )
    print(
        "  relative-phase state :",
        [round(result.probability, 4) for result in x_c]
    )


# ============================================================================
# SECTION 20: BLOCH-SPHERE DESCRIPTION OF A QUBIT
# ============================================================================

def bloch_vector_from_density_matrix(
    density_matrix: DensityMatrix,
) -> tuple[float, float, float]:
    """
    For a qubit:
        rho = 1/2 (I + r_x X + r_y Y + r_z Z)

    Therefore:
        r_x = Tr(rho X)
        r_y = Tr(rho Y)
        r_z = Tr(rho Z)
    """
    return (
        density_matrix_expectation(density_matrix, SIGMA_X).real,
        density_matrix_expectation(density_matrix, SIGMA_Y).real,
        density_matrix_expectation(density_matrix, SIGMA_Z).real,
    )


def demonstrate_bloch_vector() -> None:
    print("\n" + "=" * 78)
    print("19. BLOCH-VECTOR INTERPRETATION")
    print("=" * 78)

    states = {
        "|0>": KET_0,
        "|1>": KET_1,
        "|+>": KET_PLUS,
        "|->": KET_MINUS,
        "|y+>": KET_Y_PLUS,
        "mixed": None,
    }

    for name, state in states.items():
        if state is not None:
            rho = density_matrix_from_pure_state(state)
        else:
            rho = density_matrix_from_ensemble(
                [KET_0, KET_1],
                [0.5, 0.5],
            )

        vector = bloch_vector_from_density_matrix(rho)
        length = math.sqrt(sum(component ** 2 for component in vector))

        print(
            f"{name:>6}: r = "
            f"({vector[0]:+.3f}, {vector[1]:+.3f}, {vector[2]:+.3f}), "
            f"|r| = {length:.3f}"
        )

    print(
        "\nPure qubit states lie on the surface of the Bloch sphere. Mixed "
        "states lie inside it. The maximally mixed state is at the center."
    )


# ============================================================================
# SECTION 21: INFORMATION GAIN AND DISTURBANCE
# ============================================================================

def distinguishability_probability_same_basis(
    state: Vector,
    target_basis: Sequence[tuple[str, complex, Vector]],
) -> list[float]:
    return [
        result.probability
        for result in projective_measurement(state, target_basis)
    ]


def demonstrate_information_disturbance() -> None:
    print("\n" + "=" * 78)
    print("20. INFORMATION GAIN AND DISTURBANCE")
    print("=" * 78)

    state = KET_PLUS

    print(
        "A Z measurement on |+> produces random Z outcomes but prepares "
        "a Z eigenstate conditional on the result."
    )

    z_results = projective_measurement(state, Z_OUTCOMES)

    for result in z_results:
        if result.probability > TOLERANCE:
            x_after = distinguishability_probability_same_basis(
                result.post_state,
                X_OUTCOMES,
            )
            print(
                f"After {result.label}, X probabilities become "
                f"{[round(p, 3) for p in x_after]}"
            )

    print(
        "\nThe measurement has extracted information about Z and changed "
        "coherence relevant to X measurements. This illustrates the "
        "information-disturbance relationship without treating disturbance "
        "as a universal synonym for measurement error."
    )


# ============================================================================
# SECTION 22: WEAK MEASUREMENT CONCEPT
# ============================================================================

def demonstrate_weak_measurement_concept() -> None:
    print("\n" + "=" * 78)
    print("21. WEAK MEASUREMENT CONCEPT")
    print("=" * 78)

    print(
        "A projective measurement is not the only possible measurement "
        "regime. A weak measurement couples a system only weakly to a "
        "measurement apparatus."
    )

    print(
        "\nConceptual distinctions:"
        "\n  Strong/projective measurement:"
        "\n    - large state discrimination"
        "\n    - substantial state update in the measurement basis"
        "\n    - discrete projective outcome model"
        "\n"
        "\n  Weak measurement:"
        "\n    - small information extracted per individual interaction"
        "\n    - typically smaller disturbance per interaction"
        "\n    - useful for continuous monitoring and weak-value experiments"
        "\n"
        "\nWeak does not mean 'unphysical' or 'just noisy'. It refers to the "
        "strength of the system-apparatus interaction and resulting "
        "information/disturbance."
    )


# ============================================================================
# SECTION 23: MEASUREMENT OF AN OBSERVABLE WITH MORE THAN TWO OUTCOMES
# ============================================================================

def qutrit_example() -> None:
    print("\n" + "=" * 78)
    print("22. MULTI-OUTCOME MEASUREMENT")
    print("=" * 78)

    omega = cmath.exp(2j * math.pi / 3)

    # Fourier-like qutrit basis.
    basis = [
        normalize([1, 1, 1]),
        normalize([1, omega, omega ** 2]),
        normalize([1, omega ** 2, omega]),
    ]

    state = normalize([
        math.sqrt(0.2),
        math.sqrt(0.3) * cmath.exp(0.4j),
        math.sqrt(0.5) * cmath.exp(-0.8j),
    ])

    print_vector("Qutrit state", state)

    probabilities = []

    for index, basis_vector in enumerate(basis):
        probability = abs(vector_inner(basis_vector, state)) ** 2
        probabilities.append(probability)
        print(
            f"  Fourier-basis outcome {index}: "
            f"P = {probability:.6f}"
        )

    print(f"Total probability = {sum(probabilities):.6f}")

    print(
        "\nThe measurement formalism is not restricted to two-level systems. "
        "A d-dimensional system can have a complete projective measurement "
        "with d orthonormal basis states."
    )


# ============================================================================
# SECTION 24: PROJECTOR PROPERTIES
# ============================================================================

def demonstrate_projector_properties() -> None:
    print("\n" + "=" * 78)
    print("23. PROJECTOR PROPERTIES")
    print("=" * 78)

    projector = projector_from_state(KET_PLUS)
    squared = matrix_multiply(projector, projector)

    print_matrix("P_+", projector)

    print("\nP^2 = P:", matrix_is_close(squared, projector))
    print("P† = P:", matrix_is_close(
        conjugate_transpose(projector),
        projector,
    ))

    print(
        "\nA projector satisfies:"
        "\n  P² = P"
        "\n  P† = P"
        "\nIts eigenvalues are 0 or 1. For a rank-one projector, it selects "
        "the one-dimensional subspace spanned by a normalized state."
    )


# ============================================================================
# SECTION 25: EXPECTATION VALUE AS A PROBABILITY-WEIGHTED AVERAGE
# ============================================================================

def expectation_from_outcomes(
    measurement_results: Sequence[MeasurementOutcome],
) -> complex:
    return sum(
        result.eigenvalue * result.probability
        for result in measurement_results
    )


def demonstrate_expectation_from_probabilities() -> None:
    print("\n" + "=" * 78)
    print("24. EXPECTATION VALUES FROM MEASUREMENT DISTRIBUTIONS")
    print("=" * 78)

    state = KET_T

    results = projective_measurement(state, Z_OUTCOMES)
    direct = expectation_value(state, SIGMA_Z)
    from_distribution = expectation_from_outcomes(results)

    print(f"<Z> from <psi|Z|psi> = {pretty_complex(direct)}")
    print(
        f"<Z> from sum(a p(a)) = "
        f"{pretty_complex(from_distribution)}"
    )

    print(
        "\nFor a discrete observable with outcomes a:"
        "\n  <A> = sum_a a p(a)"
        "\nThe operator expression and the probability-distribution expression "
        "are equivalent when the probabilities are generated by the spectral "
        "measurement of A."
    )


# ============================================================================
# SECTION 26: STATISTICAL ERROR IN EXPERIMENTAL FREQUENCIES
# ============================================================================

def estimate_binomial_standard_error(
    probability: float,
    trials: int,
) -> float:
    if trials <= 0:
        raise ValueError("Trials must be positive.")
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1.")

    return math.sqrt(probability * (1.0 - probability) / trials)


def demonstrate_sampling_error() -> None:
    print("\n" + "=" * 78)
    print("25. STATISTICAL FLUCTUATIONS")
    print("=" * 78)

    probability = 0.5

    for trials in [100, 1_000, 10_000, 1_000_000]:
        error = estimate_binomial_standard_error(probability, trials)
        print(
            f"N = {trials:>8,d}: expected standard error "
            f"≈ {error:.6f}"
        )

    print(
        "\nFor independent Bernoulli trials, the standard deviation of the "
        "sample frequency is approximately sqrt[p(1-p)/N]. The statistical "
        "uncertainty therefore decreases approximately as 1/sqrt(N), not "
        "as 1/N."
    )


# ============================================================================
# SECTION 27: EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("26. EDGE CASES AND EXCEPTIONS")
    print("=" * 78)

    print("Case 1: Measuring an eigenstate of the observable.")

    results = projective_measurement(KET_0, Z_OUTCOMES)
    for result in results:
        print(
            f"  {result.label}: P = {result.probability:.6f}"
        )

    print(
        "\nAn eigenstate produces its associated eigenvalue with probability "
        "one in an ideal projective measurement."
    )

    print("\nCase 2: Zero-probability conditional branch.")

    impossible = projective_measurement(KET_0, Z_OUTCOMES)[1]

    print(
        f"  Outcome {impossible.label} has P = "
        f"{impossible.probability:.6f}"
    )
    print(
        "  A conditional post-measurement state is not physically defined "
        "for a branch with exactly zero probability."
    )

    print("\nCase 3: Unnormalized input state.")

    try:
        validate_state([2.0 + 0.0j, 0.0 + 0.0j])
    except ValueError as error:
        print(f"  Correctly rejected: {error}")

    print("\nCase 4: Invalid negative probability.")

    try:
        density_matrix_from_ensemble(
            [KET_0, KET_1],
            [1.2, -0.2],
        )
    except ValueError as error:
        print(f"  Correctly rejected: {error}")

    print(
        "\nNumerical implementations should distinguish mathematical "
        "constraints from tiny floating-point errors. A computed value such "
        "as -1e-14 may represent zero within numerical tolerance, while a "
        "substantial negative probability indicates an implementation error "
        "or an invalid input."
    )


# ============================================================================
# SECTION 28: COMMON CONCEPTUAL MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    print("\n" + "=" * 78)
    print("27. COMMON CONCEPTUAL MISTAKES")
    print("=" * 78)

    mistakes = [
        (
            "Probability amplitude is a probability",
            "Incorrect. Probabilities are squared magnitudes of amplitudes "
            "for projective rank-one measurements."
        ),
        (
            "Expectation value is always a possible single outcome",
            "Incorrect. An expectation value is generally an average and may "
            "not equal any individual eigenvalue."
        ),
        (
            "Measurement always destroys the state",
            "Too broad. Measuring an observable when the state is already an "
            "eigenstate can leave the state unchanged."
        ),
        (
            "All measurement operators are projectors",
            "Incorrect. General measurements use measurement operators and "
            "POVM effects; projective measurements are a special case."
        ),
        (
            "POVM effects uniquely determine state disturbance",
            "Incorrect. The same effects can be implemented with different "
            "measurement operators and therefore different state updates."
        ),
        (
            "Uncertainty is only an instrument limitation",
            "Incorrect. Quantum uncertainty can arise from noncommuting "
            "observables and the structure of quantum states."
        ),
        (
            "Global phase is observable",
            "Not by itself. A common phase multiplying an entire pure state "
            "does not affect ordinary measurement probabilities."
        ),
        (
            "Relative phase is also irrelevant",
            "Incorrect. Relative phase can change interference and "
            "probabilities in a different measurement basis."
        ),
    ]

    for misconception, correction in mistakes:
        print(f"\nMisconception: {misconception}")
        print(f"  Correction: {correction}")


# ============================================================================
# SECTION 29: COMPARISON OF MEASUREMENT FORMALISMS
# ============================================================================

def demonstrate_formalism_comparison() -> None:
    print("\n" + "=" * 78)
    print("28. MEASUREMENT FORMALISM COMPARISON")
    print("=" * 78)

    rows = [
        (
            "Projective measurement",
            "Projectors P_i",
            "Tr(rho P_i)",
            "P_i rho P_i / p_i",
        ),
        (
            "POVM",
            "Effects E_i",
            "Tr(rho E_i)",
            "Not determined by E_i alone",
        ),
        (
            "Kraus/instrument",
            "Operators M_i",
            "Tr(M_i rho M_i†)",
            "M_i rho M_i† / p_i",
        ),
    ]

    headers = (
        "Formalism",
        "Mathematical object",
        "Probability",
        "Conditional update",
    )

    print(
        f"{headers[0]:<24} | {headers[1]:<22} | "
        f"{headers[2]:<25} | {headers[3]}"
    )
    print("-" * 105)

    for row in rows:
        print(
            f"{row[0]:<24} | {row[1]:<22} | "
            f"{row[2]:<25} | {row[3]}"
        )


# ============================================================================
# SECTION 30: IDEALIZED QUANTUM MEASUREMENT VS REAL DEVICES
# ============================================================================

def demonstrate_real_measurement_considerations() -> None:
    print("\n" + "=" * 78)
    print("29. IDEALIZED THEORY VS REAL MEASUREMENT DEVICES")
    print("=" * 78)

    considerations = {
        "Readout noise":
            "The classical detector output can contain noise even when the "
            "underlying quantum event is well defined.",
        "Finite measurement fidelity":
            "A detector may incorrectly identify an outcome.",
        "Decoherence":
            "Interaction with uncontrolled environmental degrees of freedom "
            "can suppress observable coherence.",
        "Calibration":
            "The physical apparatus must be mapped to a mathematical "
            "measurement model.",
        "Drift":
            "Measurement parameters can change with time and operating "
            "conditions.",
        "Back-action":
            "The measurement interaction can alter the state being measured.",
        "Finite sampling":
            "Observed frequencies are estimates of theoretical probabilities.",
        "Model mismatch":
            "An ideal projective model may be insufficient for a real "
            "measurement apparatus.",
    }

    for name, description in considerations.items():
        print(f"\n{name}:")
        print(f"  {description}")

    print(
        "\nThe mathematical Born rule and an experimental measurement record "
        "are related through a physical measurement model, calibration, "
        "noise characterization, and statistical analysis."
    )


# ============================================================================
# SECTION 31: SIMPLE READOUT-ERROR MODEL
# ============================================================================

def apply_binary_readout_error(
    ideal_probability_one: float,
    false_positive_rate: float,
    false_negative_rate: float,
) -> float:
    """
    Model classical readout errors.

    observed P(1) =
        P(1)*P(read 1 | true 1)
        + P(0)*P(read 1 | true 0)

    where:
        P(read 1 | true 1) = 1 - false_negative_rate
        P(read 1 | true 0) = false_positive_rate
    """
    if not 0 <= ideal_probability_one <= 1:
        raise ValueError("Ideal probability must lie in [0, 1].")

    if not 0 <= false_positive_rate <= 1:
        raise ValueError("False-positive rate must lie in [0, 1].")

    if not 0 <= false_negative_rate <= 1:
        raise ValueError("False-negative rate must lie in [0, 1].")

    return (
        ideal_probability_one * (1.0 - false_negative_rate)
        + (1.0 - ideal_probability_one) * false_positive_rate
    )


def demonstrate_readout_error() -> None:
    print("\n" + "=" * 78)
    print("30. CLASSICAL READOUT ERROR")
    print("=" * 78)

    ideal = 0.70
    false_positive = 0.05
    false_negative = 0.10

    observed = apply_binary_readout_error(
        ideal,
        false_positive,
        false_negative,
    )

    print(f"Ideal P(1) = {ideal:.3f}")
    print(f"False-positive rate = {false_positive:.3f}")
    print(f"False-negative rate = {false_negative:.3f}")
    print(f"Observed P(read 1) = {observed:.3f}")

    print(
        "\nThis simple model separates quantum outcome statistics from a "
        "classical detector's readout errors. More complete experimental "
        "models can use a confusion matrix or a quantum instrument."
    )


# ============================================================================
# SECTION 32: INTERFERENCE AND MEASUREMENT
# ============================================================================

def demonstrate_interference() -> None:
    print("\n" + "=" * 78)
    print("31. INTERFERENCE AFFECTS MEASUREMENT PROBABILITIES")
    print("=" * 78)

    phase_values = [
        0.0,
        math.pi / 4,
        math.pi / 2,
        math.pi,
    ]

    print("State: (|0> + exp(i phi)|1>) / sqrt(2)")
    print("Probability of X=+1 depends on the relative phase:")

    for phase in phase_values:
        state = normalize([
            1.0 + 0.0j,
            cmath.exp(1j * phase),
        ])

        results = projective_measurement(state, X_OUTCOMES)
        probability_plus = results[0].probability

        print(
            f"  phi = {phase:6.3f} rad -> "
            f"P(X=+1) = {probability_plus:.6f}"
        )

    print(
        "\nThe measurement probabilities depend on interference between "
        "amplitudes. This is why relative phase matters even though global "
        "phase does not."
    )


# ============================================================================
# SECTION 33: A SIMPLE QUANTUM MEASUREMENT EXPERIMENT CLASS
# ============================================================================

@dataclass
class QuantumExperiment:
    """
    Small educational abstraction for repeated ideal measurements.

    It keeps preparation and measurement separate. This mirrors a useful
    software-design principle: represent the state, the measurement model,
    and the sampling process as distinct layers.
    """

    state: Vector
    outcomes: Sequence[tuple[str, complex, Vector]]
    seed: int = 1234

    def theoretical_probabilities(self) -> dict[str, float]:
        results = projective_measurement(self.state, self.outcomes)
        return {
            result.label: result.probability
            for result in results
        }

    def run(self, trials: int) -> dict[str, int]:
        return simulate_measurements(
            self.state,
            self.outcomes,
            trials,
            self.seed,
        )


def demonstrate_experiment_class() -> None:
    print("\n" + "=" * 78)
    print("32. REUSABLE MEASUREMENT EXPERIMENT")
    print("=" * 78)

    experiment = QuantumExperiment(
        state=KET_T,
        outcomes=X_OUTCOMES,
        seed=2026,
    )

    print("Theoretical probabilities:")
    for label, probability in experiment.theoretical_probabilities().items():
        print(f"  {label}: {probability:.6f}")

    counts = experiment.run(10_000)

    print("\nSimulated counts:")
    for label, count in counts.items():
        print(f"  {label}: {count}")


# ============================================================================
# SECTION 34: TESTS AND VALIDATION
# ============================================================================

def assert_close(
    actual: complex | float,
    expected: complex | float,
    tolerance: float = 1e-8,
) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"Expected {expected}, received {actual}."
        )


def run_tests() -> None:
    print("\n" + "=" * 78)
    print("33. INTERNAL VALIDATION TESTS")
    print("=" * 78)

    # State normalization.
    validate_state(KET_0)
    validate_state(KET_1)
    validate_state(KET_PLUS)

    # Pauli matrices are Hermitian.
    assert is_hermitian(SIGMA_X)
    assert is_hermitian(SIGMA_Y)
    assert is_hermitian(SIGMA_Z)

    # Pauli X squared is identity.
    assert matrix_is_close(
        matrix_power(SIGMA_X, 2),
        matrix_identity(2),
    )

    # Projectors are idempotent.
    plus_projector = projector_from_state(KET_PLUS)
    assert matrix_is_close(
        matrix_multiply(plus_projector, plus_projector),
        plus_projector,
    )

    # Born rule for |+> measured in Z.
    z_results = projective_measurement(KET_PLUS, Z_OUTCOMES)
    assert_close(z_results[0].probability, 0.5)
    assert_close(z_results[1].probability, 0.5)

    # Eigenstate measurement is deterministic.
    z_zero = projective_measurement(KET_0, Z_OUTCOMES)
    assert_close(z_zero[0].probability, 1.0)
    assert_close(z_zero[1].probability, 0.0)

    # Expectation value from direct operator calculation.
    assert_close(expectation_value(KET_PLUS, SIGMA_X), 1.0)
    assert_close(expectation_value(KET_PLUS, SIGMA_Z), 0.0)

    # Pure-state density matrix.
    rho_plus = density_matrix_from_pure_state(KET_PLUS)
    assert_close(trace(rho_plus), 1.0)
    assert_close(density_matrix_purity(rho_plus), 1.0)

    # Maximally mixed state.
    rho_mixed = density_matrix_from_ensemble(
        [KET_0, KET_1],
        [0.5, 0.5],
    )
    assert_close(density_matrix_purity(rho_mixed), 0.5)

    # POVM probabilities.
    p0 = matrix_scale(
        0.5,
        projector_from_state(KET_0),
    )
    p1 = matrix_scale(
        0.5,
        projector_from_state(KET_0),
    )

    p2 = projector_from_state(KET_1)

    total = [
        p0,
        p1,
        p2,
    ]

    probability_sum = sum(
        povm_probability(KET_PLUS, effect)
        for effect in total
    )

    assert_close(probability_sum, 1.0)

    # Global phase invariance.
    phased = vector_scale(
        cmath.exp(1j * 0.91),
        KET_PLUS,
    )
    assert global_phase_equivalent(KET_PLUS, phased)

    # Sampling sanity check.
    counts = simulate_measurements(
        KET_PLUS,
        Z_OUTCOMES,
        trials=20_000,
        seed=99,
    )

    frequency_zero = counts["z=+1"] / 20_000
    if abs(frequency_zero - 0.5) > 0.03:
        raise AssertionError(
            "Sampling result is unexpectedly far from the theoretical "
            "probability."
        )

    print("All internal tests passed.")


# ============================================================================
# SECTION 35: PERFORMANCE CONSIDERATIONS
# ============================================================================

def demonstrate_performance_considerations() -> None:
    print("\n" + "=" * 78)
    print("34. PERFORMANCE CONSIDERATIONS")
    print("=" * 78)

    print(
        "This educational implementation deliberately uses plain Python "
        "lists. That keeps the mathematics explicit but is not appropriate "
        "for large-scale numerical linear algebra."
    )

    print(
        "\nFor a d-dimensional dense state vector:"
        "\n  vector operations are generally O(d)"
        "\nFor dense d x d matrix-vector multiplication:"
        "\n  O(d^2)"
        "\nFor dense matrix-matrix multiplication:"
        "\n  approximately O(d^3) with the straightforward algorithm used here."
    )

    print(
        "\nQuantum systems composed of n qubits have Hilbert-space dimension "
        "2^n. Storing a generic state vector therefore requires memory that "
        "grows exponentially with n. This exponential scaling is a central "
        "computational consideration in classical simulation of quantum "
        "systems."
    )

    print(
        "\nFor production numerical work, optimized linear-algebra libraries, "
        "sparse representations, tensor-network methods, symmetry reductions, "
        "or specialized simulation techniques may be necessary."
    )


# ============================================================================
# SECTION 36: SECURITY AND REPRODUCIBILITY CONSIDERATIONS
# ============================================================================

def demonstrate_security_and_reproducibility() -> None:
    print("\n" + "=" * 78)
    print("35. SECURITY AND REPRODUCIBILITY")
    print("=" * 78)

    print(
        "Quantum measurement software should distinguish three different "
        "roles:"
        "\n  1. Physical randomness"
        "\n  2. Pseudorandom simulation"
        "\n  3. Classical data-processing randomness"
    )

    print(
        "\nThis educational script uses random.Random with a fixed seed so "
        "examples can be reproduced. A pseudorandom generator should not be "
        "mistaken for a physical quantum random-number source."
    )

    print(
        "\nFor security-sensitive applications, randomness requirements must "
        "be evaluated separately from the mathematical measurement model. "
        "Cryptographic randomness, device trust, side-channel resistance, "
        "measurement calibration, and entropy estimation can become important."
    )

    print(
        "\nMeasurement records can also contain sensitive experimental or "
        "operational information. Production systems should apply appropriate "
        "access control, integrity checks, audit logging, and data-retention "
        "policies."
    )


# ============================================================================
# SECTION 37: ADVANCED CONCEPTUAL MAP
# ============================================================================

def print_conceptual_map() -> None:
    print("\n" + "=" * 78)
    print("36. CONCEPTUAL MAP")
    print("=" * 78)

    concepts = [
        ("State", "Contains the information used to predict measurement outcomes."),
        ("Amplitude", "Complex coefficient whose squared magnitude contributes to probability."),
        ("Observable", "Hermitian operator representing a measurable quantity in the standard formalism."),
        ("Eigenvalue", "Possible ideal projective-measurement result of an observable."),
        ("Eigenstate", "State that gives a definite result for its associated observable."),
        ("Projector", "Operator selecting a subspace; used to calculate projective probabilities."),
        ("Born rule", "Maps a quantum state and measurement to outcome probabilities."),
        ("Collapse", "Conditional state update following a selected measurement outcome."),
        ("Degeneracy", "Multiple independent states share the same eigenvalue."),
        ("Density matrix", "General representation of pure and mixed quantum states."),
        ("POVM", "General measurement probability description using positive effects."),
        ("Kraus operator", "Measurement or quantum-operation operator that also specifies state transformation."),
        ("Commutator", "Measures algebraic incompatibility between two operators."),
        ("Variance", "Quantifies the statistical spread of observable outcomes."),
        ("Weak measurement", "Measurement regime with limited information extraction per interaction."),
    ]

    for concept, meaning in concepts:
        print(f"{concept:<18} -> {meaning}")


# ============================================================================
# SECTION 38: MAIN PROGRAM
# ============================================================================

def main() -> None:
    print("=" * 78)
    print("QUANTUM MEASUREMENT: OBSERVABLES, COLLAPSE, AND PROBABILITIES")
    print("=" * 78)

    demonstrate_basic_state()
    demonstrate_observables()
    demonstrate_spectral_structure()
    demonstrate_born_rule()
    demonstrate_sampling()
    demonstrate_collapse()
    demonstrate_degenerate_measurement()
    demonstrate_sequential_measurements()
    demonstrate_commutators()
    demonstrate_uncertainty()
    demonstrate_density_matrices()
    demonstrate_luders_update()
    demonstrate_povm()
    demonstrate_kraus_measurement()
    demonstrate_nonselective_measurement()
    demonstrate_basis_dependence()
    demonstrate_sequential_probability()
    demonstrate_phase()
    demonstrate_bloch_vector()
    demonstrate_information_disturbance()
    demonstrate_weak_measurement_concept()
    qutrit_example()
    demonstrate_projector_properties()
    demonstrate_expectation_from_probabilities()
    demonstrate_sampling_error()
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    demonstrate_formalism_comparison()
    demonstrate_real_measurement_considerations()
    demonstrate_readout_error()
    demonstrate_interference()
    demonstrate_experiment_class()
    run_tests()
    demonstrate_performance_considerations()
    demonstrate_security_and_reproducibility()
    print_conceptual_map()

    print("\n" + "=" * 78)
    print("END OF QUANTUM MEASUREMENT STUDY SCRIPT")
    print("=" * 78)


if __name__ == "__main__":
    main()
