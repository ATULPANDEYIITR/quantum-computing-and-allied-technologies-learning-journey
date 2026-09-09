"""
Eigenvalues & Eigenvectors: Quantum-State Applications
=======================================================

A self-contained tutorial from absolute beginner to advanced applications.

The script uses only the Python standard library. Numerical linear-algebra
routines are implemented explicitly so that the underlying mathematics remains
visible. Complex arithmetic is used because quantum states, amplitudes, and
operators are generally complex-valued.

Topics covered
--------------
1. Vectors, matrices, matrix multiplication, and linear transformations
2. Eigenvalues and eigenvectors
3. Characteristic equations and eigenspaces
4. Normalization and orthogonality
5. Hermitian matrices and the spectral theorem
6. Quantum states and bra-ket notation
7. Observables, measurement, and Born probabilities
8. Projectors and expectation values
9. Pauli matrices and qubit states
10. Quantum measurement in different bases
11. Hamiltonians, energy eigenstates, and time evolution
12. Two-level systems and Bloch-sphere coordinates
13. Degeneracy and repeated eigenvalues
14. Numerical eigenvalue computation using power iteration
15. Numerical stability, residuals, and tolerances
16. Tensor products for multi-qubit systems
17. Entangled states and Bell-state measurements
18. Density matrices and mixed states
19. Von Neumann entropy
20. Commutators and simultaneous eigenstates
21. Quantum gates as unitary operators
22. Spectral decomposition and matrix functions
23. Advanced two-level Hamiltonian dynamics
24. Validation, edge cases, debugging, and testing
25. Practical quantum-computing interpretations

The examples intentionally favor transparent implementations over optimized
scientific-computing libraries. For large production-scale systems, specialized
linear-algebra libraries should normally be used.
"""

from __future__ import annotations

import cmath
import math
import random
from typing import Callable, Iterable, List, Optional, Sequence, Tuple


# ============================================================================
# SECTION 1: BASIC LINEAR ALGEBRA REPRESENTATIONS
# ============================================================================

Complex = complex
Vector = List[complex]
Matrix = List[List[complex]]


def clean_number(value: complex, tolerance: float = 1e-10):
    """Convert tiny real/imaginary components into exact-looking values."""
    value = complex(value)
    real = 0.0 if abs(value.real) < tolerance else value.real
    imag = 0.0 if abs(value.imag) < tolerance else value.imag

    if abs(imag) < tolerance:
        return real
    if abs(real) < tolerance:
        return 1j * imag
    return complex(real, imag)


def format_number(value: complex, precision: int = 5) -> str:
    """Human-readable formatting for real and complex numbers."""
    value = clean_number(value)

    if isinstance(value, float) or not isinstance(value, complex):
        return f"{value:.{precision}g}"

    if abs(value.imag) < 1e-10:
        return f"{value.real:.{precision}g}"

    if abs(value.real) < 1e-10:
        return f"{value.imag:.{precision}g}i"

    sign = "+" if value.imag >= 0 else "-"
    return f"{value.real:.{precision}g}{sign}{abs(value.imag):.{precision}g}i"


def format_vector(vector: Sequence[complex]) -> str:
    return "[" + ", ".join(format_number(x) for x in vector) + "]"


def format_matrix(matrix: Matrix) -> str:
    rows = []
    for row in matrix:
        rows.append("[ " + "  ".join(format_number(x) for x in row) + " ]")
    return "\n".join(rows)


def shape(matrix: Matrix) -> Tuple[int, int]:
    if not matrix:
        return 0, 0
    return len(matrix), len(matrix[0])


def validate_matrix(matrix: Matrix) -> None:
    """Ensure all rows have the same length."""
    if not matrix:
        raise ValueError("A matrix must contain at least one row.")

    columns = len(matrix[0])
    if columns == 0:
        raise ValueError("A matrix must contain at least one column.")

    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must all have the same length.")


def identity_matrix(n: int) -> Matrix:
    if n < 1:
        raise ValueError("Matrix dimension must be positive.")

    return [
        [1.0 + 0j if i == j else 0j for j in range(n)]
        for i in range(n)
    ]


def zero_vector(n: int) -> Vector:
    return [0j for _ in range(n)]


def zero_matrix(rows: int, columns: int) -> Matrix:
    return [[0j for _ in range(columns)] for _ in range(rows)]


def vector_add(a: Sequence[complex], b: Sequence[complex]) -> Vector:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return [x + y for x, y in zip(a, b)]


def vector_subtract(a: Sequence[complex], b: Sequence[complex]) -> Vector:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return [x - y for x, y in zip(a, b)]


def scalar_multiply(scalar: complex, vector: Sequence[complex]) -> Vector:
    return [scalar * x for x in vector]


def matrix_add(A: Matrix, B: Matrix) -> Matrix:
    validate_matrix(A)
    validate_matrix(B)

    if shape(A) != shape(B):
        raise ValueError("Matrices must have the same shape.")

    return [
        [A[i][j] + B[i][j] for j in range(len(A[0]))]
        for i in range(len(A))
    ]


def matrix_subtract(A: Matrix, B: Matrix) -> Matrix:
    validate_matrix(A)
    validate_matrix(B)

    if shape(A) != shape(B):
        raise ValueError("Matrices must have the same shape.")

    return [
        [A[i][j] - B[i][j] for j in range(len(A[0]))]
        for i in range(len(A))
    ]


def matrix_multiply(A: Matrix, B: Matrix) -> Matrix:
    """
    Standard matrix multiplication.

    If A is m x n and B is n x p, the result is m x p.
    """
    validate_matrix(A)
    validate_matrix(B)

    rows_a, cols_a = shape(A)
    rows_b, cols_b = shape(B)

    if cols_a != rows_b:
        raise ValueError(
            f"Cannot multiply {rows_a}x{cols_a} by {rows_b}x{cols_b}."
        )

    return [
        [
            sum(A[i][k] * B[k][j] for k in range(cols_a))
            for j in range(cols_b)
        ]
        for i in range(rows_a)
    ]


def matrix_vector_multiply(A: Matrix, vector: Sequence[complex]) -> Vector:
    validate_matrix(A)

    rows, columns = shape(A)

    if columns != len(vector):
        raise ValueError(
            f"Matrix has {columns} columns but vector has {len(vector)} entries."
        )

    return [
        sum(A[i][j] * vector[j] for j in range(columns))
        for i in range(rows)
    ]


def transpose(A: Matrix) -> Matrix:
    validate_matrix(A)
    return [list(column) for column in zip(*A)]


def conjugate_vector(vector: Sequence[complex]) -> Vector:
    return [x.conjugate() for x in vector]


def conjugate_transpose(A: Matrix) -> Matrix:
    """Conjugate transpose, also called the Hermitian adjoint A†."""
    validate_matrix(A)
    return [
        [A[i][j].conjugate() for i in range(len(A))]
        for j in range(len(A[0]))
    ]


def vector_inner_product(a: Sequence[complex],
                         b: Sequence[complex]) -> complex:
    """
    Complex inner product <a|b>.

    The first vector is conjugated:
        <a|b> = sum(conj(a_i) * b_i)
    """
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")

    return sum(x.conjugate() * y for x, y in zip(a, b))


def vector_norm(vector: Sequence[complex]) -> float:
    """Euclidean norm sqrt(<v|v>)."""
    return math.sqrt(max(0.0, vector_inner_product(vector, vector).real))


def normalize(vector: Sequence[complex],
              tolerance: float = 1e-14) -> Vector:
    norm = vector_norm(vector)

    if norm < tolerance:
        raise ValueError("Cannot normalize the zero vector.")

    return [x / norm for x in vector]


def matrix_trace(A: Matrix) -> complex:
    validate_matrix(A)
    rows, columns = shape(A)

    if rows != columns:
        raise ValueError("Trace is defined for square matrices.")

    return sum(A[i][i] for i in range(rows))


def matrix_scalar_multiply(scalar: complex, A: Matrix) -> Matrix:
    validate_matrix(A)
    return [[scalar * x for x in row] for row in A]


def matrix_power(A: Matrix, exponent: int) -> Matrix:
    """Integer matrix powers using exponentiation by squaring."""
    validate_matrix(A)
    rows, columns = shape(A)

    if rows != columns:
        raise ValueError("Matrix powers require a square matrix.")

    if exponent < 0:
        raise ValueError("This implementation accepts only nonnegative powers.")

    result = identity_matrix(rows)
    base = A

    while exponent:
        if exponent & 1:
            result = matrix_multiply(result, base)
        base = matrix_multiply(base, base)
        exponent >>= 1

    return result


def is_approximately_equal(a: complex,
                           b: complex,
                           tolerance: float = 1e-9) -> bool:
    return abs(a - b) <= tolerance


def matrices_approximately_equal(A: Matrix,
                                 B: Matrix,
                                 tolerance: float = 1e-9) -> bool:
    if shape(A) != shape(B):
        return False

    return all(
        abs(A[i][j] - B[i][j]) <= tolerance
        for i in range(len(A))
        for j in range(len(A[0]))
    )


# ============================================================================
# SECTION 2: WHAT AN EIGENVALUE AND EIGENVECTOR MEAN
# ============================================================================

def demonstrate_eigenvector_definition() -> None:
    """
    An eigenvector v of A satisfies

        A v = lambda v

    where:
        A      = square matrix / linear transformation
        v      = nonzero eigenvector
        lambda = corresponding eigenvalue

    The transformation changes the eigenvector's magnitude and possibly
    complex phase, but does not change its direction in vector space.
    """
    print("\n" + "=" * 78)
    print("1. THE EIGENVALUE-EIGENVECTOR EQUATION")
    print("=" * 78)

    A = [
        [3, 0],
        [0, 2],
    ]

    v = [1, 0]
    eigenvalue = 3

    print("Matrix A:")
    print(format_matrix(A))
    print("\nCandidate eigenvector v:", format_vector(v))

    transformed = matrix_vector_multiply(A, v)
    scaled = scalar_multiply(eigenvalue, v)

    print("A v       =", format_vector(transformed))
    print("lambda v  =", format_vector(scaled))
    print("Equation holds:", transformed == scaled)

    print(
        "\nInterpretation: [1, 0] is unchanged in direction by A and is "
        "scaled by 3. Therefore 3 is its eigenvalue."
    )


# ============================================================================
# SECTION 3: DETERMINANTS AND CHARACTERISTIC POLYNOMIALS
# ============================================================================

def determinant(A: Matrix) -> complex:
    """
    Compute a determinant using recursive Laplace expansion.

    This is intentionally educational rather than computationally efficient.
    Complexity is poor for large matrices, so production software normally
    uses LU decomposition or optimized numerical routines.
    """
    validate_matrix(A)
    rows, columns = shape(A)

    if rows != columns:
        raise ValueError("Determinant requires a square matrix.")

    n = rows

    if n == 1:
        return A[0][0]

    if n == 2:
        return A[0][0] * A[1][1] - A[0][1] * A[1][0]

    total = 0j

    for column in range(n):
        minor = [
            [
                A[i][j]
                for j in range(n)
                if j != column
            ]
            for i in range(1, n)
        ]

        cofactor = ((-1) ** column) * A[0][column]
        total += cofactor * determinant(minor)

    return total


def characteristic_polynomial_2x2(A: Matrix) -> Tuple[complex, complex, complex]:
    """
    For

        A = [[a, b],
             [c, d]]

    the characteristic polynomial is

        det(A - lambda I)
        = lambda^2 - trace(A) lambda + det(A)

    Returned as coefficients (1, -trace(A), det(A)).
    """
    if shape(A) != (2, 2):
        raise ValueError("This educational helper is only for 2x2 matrices.")

    return (
        1,
        -matrix_trace(A),
        determinant(A),
    )


def solve_quadratic(a: complex, b: complex, c: complex) -> Tuple[complex, complex]:
    """Solve a*x^2 + b*x + c = 0, including complex roots."""
    if abs(a) < 1e-15:
        if abs(b) < 1e-15:
            raise ValueError("Not a valid quadratic equation.")
        return (-c / b, -c / b)

    discriminant = b * b - 4 * a * c
    root = cmath.sqrt(discriminant)

    return (
        (-b + root) / (2 * a),
        (-b - root) / (2 * a),
    )


def eigenvalues_2x2(A: Matrix) -> Tuple[complex, complex]:
    """Analytic eigenvalues for a 2x2 matrix."""
    coefficients = characteristic_polynomial_2x2(A)
    return solve_quadratic(*coefficients)


def demonstrate_characteristic_equation() -> None:
    print("\n" + "=" * 78)
    print("2. CHARACTERISTIC EQUATION")
    print("=" * 78)

    A = [
        [4, 1],
        [2, 3],
    ]

    coefficients = characteristic_polynomial_2x2(A)
    eigenvalues = eigenvalues_2x2(A)

    print("A:")
    print(format_matrix(A))
    print("\nCharacteristic polynomial coefficients:")
    print(
        f"lambda^2 + ({format_number(coefficients[1])}) lambda "
        f"+ ({format_number(coefficients[2])})"
    )
    print("\nEigenvalues:")
    for value in eigenvalues:
        print(" ", format_number(value))

    print(
        "\nEigenvalues are found by solving det(A - lambda I) = 0. "
        "For a 2x2 matrix, this becomes a quadratic equation."
    )


# ============================================================================
# SECTION 4: EIGENVECTORS FOR 2x2 MATRICES
# ============================================================================

def cross_product_3d(a: Sequence[complex],
                      b: Sequence[complex]) -> Vector:
    if len(a) != 3 or len(b) != 3:
        raise ValueError("Cross product requires three-dimensional vectors.")

    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def eigenvector_2x2(A: Matrix,
                    eigenvalue: complex,
                    tolerance: float = 1e-12) -> Vector:
    """
    Find one eigenvector of a 2x2 matrix by solving (A - lambda I)v = 0.

    For
        [[p, q],
         [r, s]]
    one convenient null vector is often [q, -p] or [s, -r].
    """
    if shape(A) != (2, 2):
        raise ValueError("This helper is only for 2x2 matrices.")

    B = [
        [A[0][0] - eigenvalue, A[0][1]],
        [A[1][0], A[1][1] - eigenvalue],
    ]

    p, q = B[0]
    r, s = B[1]

    candidates = [
        [q, -p],
        [s, -r],
        [1 + 0j, 0j],
        [0j, 1 + 0j],
    ]

    for candidate in candidates:
        if vector_norm(matrix_vector_multiply(B, candidate)) > tolerance:
            continue

        if vector_norm(candidate) > tolerance:
            return normalize(candidate)

    raise ValueError("Could not find an eigenvector numerically.")


def demonstrate_eigenvectors() -> None:
    print("\n" + "=" * 78)
    print("3. COMPUTING EIGENVECTORS")
    print("=" * 78)

    A = [
        [4, 1],
        [2, 3],
    ]

    for eigenvalue in eigenvalues_2x2(A):
        vector = eigenvector_2x2(A, eigenvalue)
        left = matrix_vector_multiply(A, vector)
        right = scalar_multiply(eigenvalue, vector)

        print(f"\nlambda = {format_number(eigenvalue)}")
        print("normalized eigenvector =", format_vector(vector))
        print("A v =", format_vector(left))
        print("lambda v =", format_vector(right))
        print("Residual norm =", vector_norm(vector_subtract(left, right)))


# ============================================================================
# SECTION 5: HERMITIAN MATRICES
# ============================================================================

def is_hermitian(A: Matrix, tolerance: float = 1e-10) -> bool:
    return matrices_approximately_equal(
        A,
        conjugate_transpose(A),
        tolerance,
    )


def is_unitary(A: Matrix, tolerance: float = 1e-10) -> bool:
    validate_matrix(A)
    rows, columns = shape(A)

    if rows != columns:
        return False

    product = matrix_multiply(conjugate_transpose(A), A)
    return matrices_approximately_equal(
        product,
        identity_matrix(rows),
        tolerance,
    )


def demonstrate_hermitian_matrices() -> None:
    """
    Hermitian condition:

        A† = A

    Hermitian matrices are fundamental in quantum mechanics because physical
    observables are represented by Hermitian operators.

    Spectral theorem:
        A = U D U†

    for Hermitian A, where U is unitary and D contains real eigenvalues.
    """
    print("\n" + "=" * 78)
    print("4. HERMITIAN MATRICES AND THE SPECTRAL THEOREM")
    print("=" * 78)

    A = [
        [2, 1 - 2j],
        [1 + 2j, 5],
    ]

    print("A:")
    print(format_matrix(A))
    print("\nA†:")
    print(format_matrix(conjugate_transpose(A)))
    print("\nHermitian:", is_hermitian(A))

    values = eigenvalues_2x2(A)
    print("\nEigenvalues:")
    for value in values:
        print(" ", format_number(value))

    print(
        "\nFor a Hermitian matrix, eigenvalues are guaranteed to be real "
        "and eigenvectors belonging to distinct eigenvalues are orthogonal."
    )


# ============================================================================
# SECTION 6: QUANTUM STATES
# ============================================================================

def ket_zero() -> Vector:
    return [1 + 0j, 0j]


def ket_one() -> Vector:
    return [0j, 1 + 0j]


def ket_plus() -> Vector:
    return normalize([1 + 0j, 1 + 0j])


def ket_minus() -> Vector:
    return normalize([1 + 0j, -1 + 0j])


def ket_y_plus() -> Vector:
    return normalize([1 + 0j, 1j])


def ket_y_minus() -> Vector:
    return normalize([1 + 0j, -1j])


def probability_amplitude(basis_state: Sequence[complex],
                           state: Sequence[complex]) -> complex:
    """
    Compute <basis_state|state>.

    This is an amplitude. The corresponding probability is its squared
    magnitude.
    """
    return vector_inner_product(basis_state, state)


def probability_from_amplitude(amplitude: complex) -> float:
    return abs(amplitude) ** 2


def measurement_probability(basis_state: Sequence[complex],
                             state: Sequence[complex]) -> float:
    return probability_from_amplitude(
        probability_amplitude(basis_state, state)
    )


def demonstrate_quantum_state() -> None:
    print("\n" + "=" * 78)
    print("5. QUANTUM STATES AS NORMALIZED VECTORS")
    print("=" * 78)

    alpha = 1 / math.sqrt(3)
    beta = math.sqrt(2 / 3) * cmath.exp(1j * math.pi / 4)

    psi = [alpha, beta]

    print("|psi> =", format_vector(psi))
    print("Norm =", vector_norm(psi))
    print("Normalization condition:")
    print("  |alpha|^2 + |beta|^2 =", abs(alpha) ** 2 + abs(beta) ** 2)

    p0 = measurement_probability(ket_zero(), psi)
    p1 = measurement_probability(ket_one(), psi)

    print("\nMeasurement in computational basis:")
    print("P(0) =", p0)
    print("P(1) =", p1)
    print("P(0) + P(1) =", p0 + p1)

    print(
        "\nA pure qubit state is represented by"
        " |psi> = alpha|0> + beta|1>, with |alpha|^2 + |beta|^2 = 1."
    )


# ============================================================================
# SECTION 7: BRA-KET NOTATION, PROJECTORS, AND EXPECTATION VALUES
# ============================================================================

def outer_product(a: Sequence[complex],
                  b: Sequence[complex]) -> Matrix:
    """
    Construct |a><b|.

    The bra <b| contributes conjugated components.
    """
    return [
        [
            a[i] * b[j].conjugate()
            for j in range(len(b))
        ]
        for i in range(len(a))
    ]


def expectation_value(state: Sequence[complex],
                      operator: Matrix) -> complex:
    """
    Calculate

        <A> = <psi|A|psi>
    """
    transformed = matrix_vector_multiply(operator, state)
    return vector_inner_product(state, transformed)


def projector(state: Sequence[complex]) -> Matrix:
    normalized = normalize(state)
    return outer_product(normalized, normalized)


def demonstrate_projectors_and_expectation() -> None:
    print("\n" + "=" * 78)
    print("6. PROJECTORS AND EXPECTATION VALUES")
    print("=" * 78)

    psi = normalize([1 + 0j, 2 + 1j])

    P0 = projector(ket_zero())

    print("|psi> =", format_vector(psi))
    print("\nProjector |0><0|:")
    print(format_matrix(P0))

    probability_zero = expectation_value(psi, P0)

    print("\n<psi|(|0><0|)|psi> =", format_number(probability_zero))
    print(
        "\nA projector represents a yes/no measurement event. "
        "Its expectation value gives the probability of that event."
    )


# ============================================================================
# SECTION 8: PAULI MATRICES
# ============================================================================

I2 = [
    [1 + 0j, 0j],
    [0j, 1 + 0j],
]

SIGMA_X = [
    [0j, 1 + 0j],
    [1 + 0j, 0j],
]

SIGMA_Y = [
    [0j, -1j],
    [1j, 0j],
]

SIGMA_Z = [
    [1 + 0j, 0j],
    [0j, -1 + 0j],
]


def demonstrate_pauli_matrices() -> None:
    print("\n" + "=" * 78)
    print("7. PAULI MATRICES AND THEIR EIGENSTATES")
    print("=" * 78)

    paulis = {
        "X": SIGMA_X,
        "Y": SIGMA_Y,
        "Z": SIGMA_Z,
    }

    known_eigenstates = {
        "X": [ket_plus(), ket_minus()],
        "Y": [ket_y_plus(), ket_y_minus()],
        "Z": [ket_zero(), ket_one()],
    }

    for name, matrix in paulis.items():
        print(f"\nPauli {name}:")
        print(format_matrix(matrix))

        values = eigenvalues_2x2(matrix)
        print("Eigenvalues:", [format_number(v) for v in values])

        for state in known_eigenstates[name]:
            transformed = matrix_vector_multiply(matrix, state)
            eigenvalue = vector_inner_product(state, transformed)
            residual = vector_norm(
                vector_subtract(
                    transformed,
                    scalar_multiply(eigenvalue, state),
                )
            )

            print(
                "state =", format_vector(state),
                "| eigenvalue =", format_number(eigenvalue),
                "| residual =", residual,
            )

    print(
        "\nThe Pauli matrices represent measurements of spin-like components "
        "for a qubit. Their eigenvectors are the corresponding measurement "
        "outcomes."
    )


# ============================================================================
# SECTION 9: MEASUREMENT IN DIFFERENT EIGENBASES
# ============================================================================

def demonstrate_measurement_bases() -> None:
    print("\n" + "=" * 78)
    print("8. MEASUREMENT AS PROJECTION ONTO AN EIGENBASIS")
    print("=" * 78)

    state = ket_zero()

    bases = {
        "Z basis": [ket_zero(), ket_one()],
        "X basis": [ket_plus(), ket_minus()],
        "Y basis": [ket_y_plus(), ket_y_minus()],
    }

    print("State:", format_vector(state))

    for basis_name, basis in bases.items():
        probabilities = [
            measurement_probability(basis_vector, state)
            for basis_vector in basis
        ]

        print(f"\n{basis_name}:")
        for index, probability in enumerate(probabilities):
            print(f"  outcome {index}: {probability:.6f}")

        print("  total:", sum(probabilities))

    print(
        "\nThe same physical state can produce different outcome "
        "probabilities because the measurement basis changes."
    )


# ============================================================================
# SECTION 10: SPECTRAL DECOMPOSITION
# ============================================================================

def spectral_decomposition_2x2(A: Matrix) -> List[Tuple[complex, Matrix]]:
    """
    Construct spectral projectors for a 2x2 Hermitian matrix with distinct
    eigenvalues.

    For distinct eigenvalues lambda_1 and lambda_2:

        P_1 = (A - lambda_2 I) / (lambda_1 - lambda_2)
        P_2 = (A - lambda_1 I) / (lambda_2 - lambda_1)

    and

        A = lambda_1 P_1 + lambda_2 P_2.
    """
    if not is_hermitian(A):
        raise ValueError("Spectral projector helper expects a Hermitian matrix.")

    lambda_1, lambda_2 = eigenvalues_2x2(A)

    if abs(lambda_1 - lambda_2) < 1e-10:
        raise ValueError(
            "This simple spectral decomposition requires distinct eigenvalues."
        )

    I = identity_matrix(2)

    P1 = matrix_scalar_multiply(
        1 / (lambda_1 - lambda_2),
        matrix_subtract(
            A,
            matrix_scalar_multiply(lambda_2, I),
        ),
    )

    P2 = matrix_scalar_multiply(
        1 / (lambda_2 - lambda_1),
        matrix_subtract(
            A,
            matrix_scalar_multiply(lambda_1, I),
        ),
    )

    return [(lambda_1, P1), (lambda_2, P2)]


def demonstrate_spectral_decomposition() -> None:
    print("\n" + "=" * 78)
    print("9. SPECTRAL DECOMPOSITION")
    print("=" * 78)

    A = [
        [2, 1],
        [1, 2],
    ]

    print("Hermitian operator A:")
    print(format_matrix(A))

    decomposition = spectral_decomposition_2x2(A)

    reconstructed = zero_matrix(2, 2)

    for eigenvalue, P in decomposition:
        print(f"\nEigenvalue: {format_number(eigenvalue)}")
        print("Spectral projector:")
        print(format_matrix(P))

        reconstructed = matrix_add(
            reconstructed,
            matrix_scalar_multiply(eigenvalue, P),
        )

    print("\nReconstructed A:")
    print(format_matrix(reconstructed))

    print(
        "\nSpectral decomposition expresses a Hermitian operator as a weighted "
        "sum of projectors onto its eigenspaces."
    )


# ============================================================================
# SECTION 11: HAMILTONIANS AND ENERGY EIGENSTATES
# ============================================================================

def demonstrate_hamiltonian_eigenstates() -> None:
    print("\n" + "=" * 78)
    print("10. HAMILTONIANS, ENERGY EIGENVALUES, AND STATIONARY STATES")
    print("=" * 78)

    # A simple two-level Hamiltonian.
    H = [
        [1.0, 0.0],
        [0.0, 3.0],
    ]

    energies = eigenvalues_2x2(H)

    print("Hamiltonian H:")
    print(format_matrix(H))

    print("\nEnergy eigenvalues:")
    for energy in energies:
        print(" E =", format_number(energy))

    for energy in energies:
        state = eigenvector_2x2(H, energy)
        print(
            "\nEnergy E =", format_number(energy),
            "\nEnergy eigenstate =", format_vector(state),
        )

    print(
        "\nFor a Hamiltonian H, the eigenvalue equation"
        " H|E> = E|E> identifies energy eigenstates. "
        "The eigenvalue E is the possible energy measurement result."
    )


# ============================================================================
# SECTION 12: TIME EVOLUTION
# ============================================================================

def matrix_exponential_series(A: Matrix,
                              terms: int = 40) -> Matrix:
    """
    Approximate exp(A) using

        exp(A) = I + A + A^2/2! + A^3/3! + ...

    This educational implementation is useful for small matrices and moderate
    operator norms. It is not a replacement for robust production algorithms.
    """
    validate_matrix(A)
    rows, columns = shape(A)

    if rows != columns:
        raise ValueError("Matrix exponential requires a square matrix.")

    result = identity_matrix(rows)
    term = identity_matrix(rows)

    for n in range(1, terms):
        term = matrix_multiply(term, A)
        term = matrix_scalar_multiply(1 / math.factorial(n), term)
        result = matrix_add(result, term)

    return result


def time_evolution_operator(H: Matrix,
                            time: float,
                            hbar: float = 1.0) -> Matrix:
    """
    Quantum time evolution:

        U(t) = exp(-i H t / hbar)
    """
    generator = matrix_scalar_multiply(
        -1j * time / hbar,
        H,
    )
    return matrix_exponential_series(generator)


def demonstrate_time_evolution() -> None:
    print("\n" + "=" * 78)
    print("11. TIME EVOLUTION AND HAMILTONIAN EIGENVECTORS")
    print("=" * 78)

    H = [
        [1.0, 0.0],
        [0.0, 3.0],
    ]

    state = normalize([1 + 0j, 1 + 0j])
    time = math.pi / 2

    U = time_evolution_operator(H, time)
    evolved = matrix_vector_multiply(U, state)

    print("Initial state:")
    print(format_vector(state))

    print("\nU(t) = exp(-iHt):")
    print(format_matrix(U))

    print("\nEvolved state:")
    print(format_vector(evolved))

    print("\nInitial norm:", vector_norm(state))
    print("Final norm:", vector_norm(evolved))

    print(
        "\nA unitary time-evolution operator preserves normalization. "
        "An energy eigenstate evolves only by a global phase, so its "
        "measurement probabilities remain constant."
    )


# ============================================================================
# SECTION 13: BLOCH-SPHERE REPRESENTATION
# ============================================================================

def bloch_vector(state: Sequence[complex]) -> Tuple[float, float, float]:
    """
    For a normalized pure qubit |psi>, calculate

        x = <X>
        y = <Y>
        z = <Z>

    These coordinates locate the state on the Bloch sphere.
    """
    state = normalize(state)

    x = expectation_value(state, SIGMA_X).real
    y = expectation_value(state, SIGMA_Y).real
    z = expectation_value(state, SIGMA_Z).real

    return x, y, z


def demonstrate_bloch_sphere_coordinates() -> None:
    print("\n" + "=" * 78)
    print("12. EIGENSTATES AND THE BLOCH SPHERE")
    print("=" * 78)

    states = {
        "|0>": ket_zero(),
        "|1>": ket_one(),
        "|+>": ket_plus(),
        "|->": ket_minus(),
        "|+y>": ket_y_plus(),
        "|-y>": ket_y_minus(),
    }

    for name, state in states.items():
        coordinates = bloch_vector(state)
        radius = math.sqrt(sum(x * x for x in coordinates))

        print(
            f"{name:5s} -> "
            f"(x, y, z) = ({coordinates[0]: .3f}, "
            f"{coordinates[1]: .3f}, {coordinates[2]: .3f}), "
            f"radius = {radius:.3f}"
        )

    print(
        "\nPauli expectation values provide the Cartesian coordinates of a "
        "pure qubit state on the Bloch sphere."
    )


# ============================================================================
# SECTION 14: DEGENERATE EIGENVALUES
# ============================================================================

def demonstrate_degeneracy() -> None:
    print("\n" + "=" * 78)
    print("13. DEGENERATE EIGENVALUES")
    print("=" * 78)

    A = [
        [5, 0],
        [0, 5],
    ]

    print("A =")
    print(format_matrix(A))

    print("\nBoth eigenvalues equal 5.")

    print(
        "\nEvery nonzero vector is an eigenvector because"
        " A v = 5 v for every vector v."
    )

    vectors = [
        [1, 0],
        [0, 1],
        normalize([1, 1]),
        normalize([1, 1j]),
    ]

    for vector in vectors:
        transformed = matrix_vector_multiply(A, vector)
        residual = vector_norm(
            vector_subtract(
                transformed,
                scalar_multiply(5, vector),
            )
        )

        print(
            "v =", format_vector(vector),
            "residual =", residual,
        )

    print(
        "\nA repeated eigenvalue does not necessarily imply that every "
        "matrix is proportional to the identity. Degeneracy means the "
        "eigenspace has dimension greater than one."
    )


# ============================================================================
# SECTION 15: POWER ITERATION
# ============================================================================

def power_iteration(A: Matrix,
                    iterations: int = 1000,
                    tolerance: float = 1e-12,
                    initial_vector: Optional[Sequence[complex]] = None
                    ) -> Tuple[complex, Vector, int]:
    """
    Estimate the dominant eigenvalue/eigenvector.

    For a matrix with a unique eigenvalue of largest magnitude, repeated
    multiplication tends to align a vector with its dominant eigenvector.

    Rayleigh quotient:
        lambda ~= <v|Av> / <v|v>
    """
    validate_matrix(A)
    rows, columns = shape(A)

    if rows != columns:
        raise ValueError("Power iteration requires a square matrix.")

    if initial_vector is None:
        vector = normalize([1 + 0j for _ in range(rows)])
    else:
        if len(initial_vector) != rows:
            raise ValueError("Initial vector has the wrong dimension.")
        vector = normalize(initial_vector)

    previous_eigenvalue = None

    for iteration in range(1, iterations + 1):
        next_vector = matrix_vector_multiply(A, vector)
        norm = vector_norm(next_vector)

        if norm < tolerance:
            raise ValueError(
                "Iteration reached the zero vector. "
                "The chosen starting vector may be orthogonal to "
                "the relevant eigenspace."
            )

        vector = normalize(next_vector)

        Av = matrix_vector_multiply(A, vector)
        eigenvalue = vector_inner_product(vector, Av)

        if (
            previous_eigenvalue is not None
            and abs(eigenvalue - previous_eigenvalue) < tolerance
        ):
            return eigenvalue, vector, iteration

        previous_eigenvalue = eigenvalue

    return eigenvalue, vector, iterations


def demonstrate_power_iteration() -> None:
    print("\n" + "=" * 78)
    print("14. NUMERICAL EIGENVALUE ESTIMATION: POWER ITERATION")
    print("=" * 78)

    A = [
        [4, 1],
        [1, 3],
    ]

    eigenvalue, vector, iterations = power_iteration(A)

    residual = vector_norm(
        vector_subtract(
            matrix_vector_multiply(A, vector),
            scalar_multiply(eigenvalue, vector),
        )
    )

    print("A:")
    print(format_matrix(A))
    print("\nEstimated dominant eigenvalue:", format_number(eigenvalue))
    print("Estimated eigenvector:", format_vector(vector))
    print("Iterations:", iterations)
    print("Residual norm:", residual)

    print(
        "\nPower iteration is simple and useful for teaching, but it has "
        "limitations: convergence can be slow, it targets the dominant "
        "eigenvalue by magnitude, and it can fail or behave poorly when "
        "eigenvalues are close in magnitude or repeated."
    )


# ============================================================================
# SECTION 16: RESIDUALS AND NUMERICAL ACCURACY
# ============================================================================

def eigenpair_residual(A: Matrix,
                       eigenvalue: complex,
                       eigenvector: Sequence[complex]) -> float:
    """
    Residual:

        ||A v - lambda v||

    A small residual indicates that the computed pair approximately satisfies
    the eigenvalue equation.
    """
    left = matrix_vector_multiply(A, eigenvector)
    right = scalar_multiply(eigenvalue, eigenvector)
    return vector_norm(vector_subtract(left, right))


def demonstrate_numerical_validation() -> None:
    print("\n" + "=" * 78)
    print("15. NUMERICAL VALIDATION WITH RESIDUALS")
    print("=" * 78)

    A = [
        [2, 1],
        [1, 2],
    ]

    for eigenvalue in eigenvalues_2x2(A):
        vector = eigenvector_2x2(A, eigenvalue)
        residual = eigenpair_residual(A, eigenvalue, vector)

        print(
            f"lambda={format_number(eigenvalue)}, "
            f"residual={residual:.3e}"
        )

    print(
        "\nExact symbolic mathematics and floating-point computation differ. "
        "A numerical eigenpair should normally be checked with a residual "
        "rather than with exact equality."
    )


# ============================================================================
# SECTION 17: TENSOR PRODUCTS
# ============================================================================

def kron_vector(a: Sequence[complex],
                b: Sequence[complex]) -> Vector:
    """Tensor/Kronecker product of two vectors."""
    return [
        x * y
        for x in a
        for y in b
    ]


def kron_matrix(A: Matrix, B: Matrix) -> Matrix:
    """Kronecker product of two matrices."""
    validate_matrix(A)
    validate_matrix(B)

    rows_a, cols_a = shape(A)
    rows_b, cols_b = shape(B)

    result = zero_matrix(rows_a * rows_b, cols_a * cols_b)

    for i in range(rows_a):
        for j in range(cols_a):
            for k in range(rows_b):
                for l in range(cols_b):
                    result[i * rows_b + k][j * cols_b + l] = (
                        A[i][j] * B[k][l]
                    )

    return result


def demonstrate_tensor_products() -> None:
    print("\n" + "=" * 78)
    print("16. MULTI-QUBIT SYSTEMS AND TENSOR PRODUCTS")
    print("=" * 78)

    zero_zero = kron_vector(ket_zero(), ket_zero())
    zero_one = kron_vector(ket_zero(), ket_one())
    plus_zero = kron_vector(ket_plus(), ket_zero())

    print("|00> =", format_vector(zero_zero))
    print("|01> =", format_vector(zero_one))
    print("|+0> =", format_vector(plus_zero))

    XX = kron_matrix(SIGMA_X, SIGMA_X)

    print("\nX ⊗ X:")
    print(format_matrix(XX))

    print(
        "\nA single qubit has dimension 2. Two qubits have dimension 4. "
        "For n qubits, the Hilbert-space dimension is 2^n."
    )


# ============================================================================
# SECTION 18: BELL STATES AND ENTANGLEMENT
# ============================================================================

def bell_phi_plus() -> Vector:
    return normalize(
        vector_add(
            kron_vector(ket_zero(), ket_zero()),
            kron_vector(ket_one(), ket_one()),
        )
    )


def bell_phi_minus() -> Vector:
    return normalize(
        vector_subtract(
            kron_vector(ket_zero(), ket_zero()),
            kron_vector(ket_one(), ket_one()),
        )
    )


def bell_psi_plus() -> Vector:
    return normalize(
        vector_add(
            kron_vector(ket_zero(), ket_one()),
            kron_vector(ket_one(), ket_zero()),
        )
    )


def bell_psi_minus() -> Vector:
    return normalize(
        vector_subtract(
            kron_vector(ket_zero(), ket_one()),
            kron_vector(ket_one(), ket_zero()),
        )
    )


def demonstrate_bell_states() -> None:
    print("\n" + "=" * 78)
    print("17. BELL STATES, EIGENVECTORS, AND ENTANGLEMENT")
    print("=" * 78)

    bells = {
        "Phi+": bell_phi_plus(),
        "Phi-": bell_phi_minus(),
        "Psi+": bell_psi_plus(),
        "Psi-": bell_psi_minus(),
    }

    for name, state in bells.items():
        print(f"|{name}> =", format_vector(state))
        print("  norm =", vector_norm(state))

    # XX and ZZ have Bell states as simultaneous eigenstates.
    XX = kron_matrix(SIGMA_X, SIGMA_X)
    ZZ = kron_matrix(SIGMA_Z, SIGMA_Z)

    print("\nBell-state eigenvalue relations:")

    for name, state in bells.items():
        xx_result = matrix_vector_multiply(XX, state)
        zz_result = matrix_vector_multiply(ZZ, state)

        xx_eigenvalue = vector_inner_product(state, xx_result)
        zz_eigenvalue = vector_inner_product(state, zz_result)

        xx_residual = vector_norm(
            vector_subtract(
                xx_result,
                scalar_multiply(xx_eigenvalue, state),
            )
        )

        zz_residual = vector_norm(
            vector_subtract(
                zz_result,
                scalar_multiply(zz_eigenvalue, state),
            )
        )

        print(
            f"  {name:4s}: "
            f"XX eigenvalue={format_number(xx_eigenvalue)}, "
            f"ZZ eigenvalue={format_number(zz_eigenvalue)}, "
            f"residuals=({xx_residual:.2e}, {zz_residual:.2e})"
        )

    print(
        "\nBell states illustrate an important relationship between "
        "eigenvectors and quantum correlations: certain entangled states "
        "are simultaneous eigenstates of commuting multi-qubit observables."
    )


# ============================================================================
# SECTION 19: DENSITY MATRICES
# ============================================================================

def density_matrix_from_state(state: Sequence[complex]) -> Matrix:
    state = normalize(state)
    return outer_product(state, state)


def matrix_multiply_scalar_trace(A: Matrix, B: Matrix) -> complex:
    return matrix_trace(matrix_multiply(A, B))


def density_matrix_purity(rho: Matrix) -> float:
    """Purity Tr(rho^2). Pure states have purity 1."""
    rho_squared = matrix_multiply(rho, rho)
    return matrix_trace(rho_squared).real


def demonstrate_density_matrices() -> None:
    print("\n" + "=" * 78)
    print("18. DENSITY MATRICES AND MIXED STATES")
    print("=" * 78)

    pure_state = ket_plus()
    rho_pure = density_matrix_from_state(pure_state)

    # Equal classical mixture of |0> and |1>.
    rho_mixed = matrix_scalar_multiply(
        0.5,
        matrix_add(
            density_matrix_from_state(ket_zero()),
            density_matrix_from_state(ket_one()),
        ),
    )

    print("Density matrix for |+>:")
    print(format_matrix(rho_pure))

    print("\nDensity matrix for 50/50 mixture of |0> and |1>:")
    print(format_matrix(rho_mixed))

    print("\nPurity of pure state:", density_matrix_purity(rho_pure))
    print("Purity of mixed state:", density_matrix_purity(rho_mixed))

    print(
        "\nA pure state has rho = |psi><psi| and satisfies Tr(rho^2)=1. "
        "A genuinely mixed state has purity below 1."
    )


# ============================================================================
# SECTION 20: DENSITY-MATRIX EXPECTATION VALUES
# ============================================================================

def density_expectation(rho: Matrix,
                        operator: Matrix) -> complex:
    """
    Expectation value in density-matrix form:

        <A> = Tr(rho A)
    """
    return matrix_multiply_scalar_trace(rho, operator)


def demonstrate_density_expectation() -> None:
    print("\n" + "=" * 78)
    print("19. EXPECTATION VALUES WITH DENSITY MATRICES")
    print("=" * 78)

    rho = density_matrix_from_state(ket_plus())

    print("rho:")
    print(format_matrix(rho))

    print("\n<X> =", format_number(density_expectation(rho, SIGMA_X)))
    print("<Y> =", format_number(density_expectation(rho, SIGMA_Y)))
    print("<Z> =", format_number(density_expectation(rho, SIGMA_Z)))

    print(
        "\nThe density-matrix formula Tr(rho A) generalizes expectation "
        "values from pure states to mixed states."
    )


# ============================================================================
# SECTION 21: VON NEUMANN ENTROPY
# ============================================================================

def eigenvalues_hermitian_2x2(A: Matrix) -> List[float]:
    """
    Return real-valued eigenvalues for a 2x2 Hermitian matrix.

    Small numerical imaginary components are discarded.
    """
    if not is_hermitian(A):
        raise ValueError("Matrix must be Hermitian.")

    values = eigenvalues_2x2(A)

    return sorted(
        [float(value.real) for value in values],
        reverse=True,
    )


def von_neumann_entropy_2x2(rho: Matrix,
                            tolerance: float = 1e-12) -> float:
    """
    S(rho) = -Tr(rho log2 rho)
           = -sum(lambda_i log2(lambda_i))

    Eigenvalues near zero contribute zero by continuity.
    """
    eigenvalues = eigenvalues_hermitian_2x2(rho)

    entropy = 0.0

    for eigenvalue in eigenvalues:
        if eigenvalue > tolerance:
            entropy -= eigenvalue * math.log2(eigenvalue)

    return entropy


def demonstrate_entropy() -> None:
    print("\n" + "=" * 78)
    print("20. VON NEUMANN ENTROPY")
    print("=" * 78)

    pure = density_matrix_from_state(ket_plus())

    maximally_mixed = [
        [0.5 + 0j, 0j],
        [0j, 0.5 + 0j],
    ]

    print("Pure-state entropy:")
    print(von_neumann_entropy_2x2(pure))

    print("\nMaximally mixed qubit entropy:")
    print(von_neumann_entropy_2x2(maximally_mixed))

    print(
        "\nFor a qubit, entropy ranges from 0 for a pure state to 1 bit "
        "for a maximally mixed state."
    )


# ============================================================================
# SECTION 22: COMMUTATORS
# ============================================================================

def commutator(A: Matrix, B: Matrix) -> Matrix:
    """[A, B] = AB - BA."""
    return matrix_subtract(
        matrix_multiply(A, B),
        matrix_multiply(B, A),
    )


def demonstrate_commutators() -> None:
    print("\n" + "=" * 78)
    print("21. COMMUTATORS AND COMPATIBLE OBSERVABLES")
    print("=" * 78)

    xy = commutator(SIGMA_X, SIGMA_Y)
    xz = commutator(SIGMA_X, SIGMA_Z)

    print("[X, Y] =")
    print(format_matrix(xy))

    print("\n[X, Z] =")
    print(format_matrix(xz))

    print(
        "\nNonzero commutators indicate that the corresponding observables "
        "do not generally possess a common eigenbasis. Commuting observables "
        "can be simultaneously diagonalized under suitable conditions."
    )


# ============================================================================
# SECTION 23: QUANTUM GATES AND UNITARITY
# ============================================================================

HADAMARD = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]

PHASE = [
    [1 + 0j, 0j],
    [0j, 1j],
]

S_GATE = PHASE

T_GATE = [
    [1 + 0j, 0j],
    [0j, cmath.exp(1j * math.pi / 4)],
]


def demonstrate_quantum_gates() -> None:
    print("\n" + "=" * 78)
    print("22. UNITARY OPERATORS AND QUANTUM GATES")
    print("=" * 78)

    gates = {
        "Hadamard": HADAMARD,
        "Phase": PHASE,
        "T": T_GATE,
        "Pauli X": SIGMA_X,
        "Pauli Y": SIGMA_Y,
        "Pauli Z": SIGMA_Z,
    }

    for name, gate in gates.items():
        print(f"{name:10s} unitary = {is_unitary(gate)}")

    state = ket_zero()
    after_h = matrix_vector_multiply(HADAMARD, state)
    after_hz = matrix_vector_multiply(SIGMA_Z, after_h)

    print("\n|0> -> H|0> =", format_vector(after_h))
    print("\nZ H|0> =", format_vector(after_hz))

    print(
        "\nQuantum gates are represented by unitary matrices. "
        "Unitarity guarantees preservation of inner products and therefore "
        "preservation of total probability."
    )


# ============================================================================
# SECTION 24: MATRIX FUNCTIONS THROUGH SPECTRAL DECOMPOSITION
# ============================================================================

def spectral_matrix_function_2x2(
    A: Matrix,
    function: Callable[[complex], complex],
) -> Matrix:
    """
    For a Hermitian 2x2 matrix with distinct eigenvalues:

        f(A) = sum_i f(lambda_i) P_i
    """
    result = zero_matrix(2, 2)

    for eigenvalue, P in spectral_decomposition_2x2(A):
        result = matrix_add(
            result,
            matrix_scalar_multiply(function(eigenvalue), P),
        )

    return result


def demonstrate_matrix_functions() -> None:
    print("\n" + "=" * 78)
    print("23. MATRIX FUNCTIONS AND SPECTRAL CALCULUS")
    print("=" * 78)

    H = [
        [1, 0],
        [0, 3],
    ]

    exp_H = spectral_matrix_function_2x2(
        H,
        lambda x: cmath.exp(-1j * x),
    )

    print("H:")
    print(format_matrix(H))

    print("\nexp(-iH):")
    print(format_matrix(exp_H))

    print(
        "\nOnce an operator is spectrally decomposed, functions of that "
        "operator can be evaluated by applying the scalar function to each "
        "eigenvalue while preserving the corresponding spectral projectors."
    )


# ============================================================================
# SECTION 25: QUANTUM MEASUREMENT USING SPECTRAL PROJECTORS
# ============================================================================

def projective_measurement_probabilities(
    state: Sequence[complex],
    spectral_projectors: Sequence[Matrix],
) -> List[float]:
    """
    For a projective measurement {P_i}:

        p_i = <psi|P_i|psi>

    The projectors should satisfy:
        P_i^2 = P_i
        P_i P_j = 0 for i != j
        sum_i P_i = I
    """
    state = normalize(state)

    probabilities = []

    for P in spectral_projectors:
        value = expectation_value(state, P).real

        # Numerical noise can produce values such as -1e-16.
        if abs(value) < 1e-12:
            value = 0.0

        probabilities.append(value)

    return probabilities


def demonstrate_projective_measurement() -> None:
    print("\n" + "=" * 78)
    print("24. PROJECTIVE MEASUREMENT FROM AN OPERATOR'S EIGENPROJECTORS")
    print("=" * 78)

    observable = SIGMA_X
    spectral = spectral_decomposition_2x2(observable)

    state = normalize([1, 2j])

    projectors = [projector(eigenvector_2x2(observable, value))
                  for value, _ in spectral]

    probabilities = projective_measurement_probabilities(
        state,
        projectors,
    )

    print("State:")
    print(format_vector(state))

    print("\nMeasurement probabilities for X:")
    for index, ((eigenvalue, _), probability) in enumerate(
        zip(spectral, probabilities)
    ):
        print(
            f"  eigenvalue {format_number(eigenvalue)}: "
            f"probability {probability:.6f}"
        )

    print("\nTotal probability:", sum(probabilities))


# ============================================================================
# SECTION 26: EXPECTATION VALUE AS AN EIGENVALUE WEIGHTED AVERAGE
# ============================================================================

def demonstrate_expectation_as_weighted_average() -> None:
    print("\n" + "=" * 78)
    print("25. EXPECTATION VALUE AND EIGENVALUE PROBABILITIES")
    print("=" * 78)

    A = [
        [2, 1],
        [1, 2],
    ]

    state = normalize([2, 1])

    decomposition = spectral_decomposition_2x2(A)

    expectation = expectation_value(state, A)

    weighted_sum = 0j

    print("State:", format_vector(state))
    print("\nEigenvalue probabilities:")

    for eigenvalue, P in decomposition:
        probability = expectation_value(state, P).real
        weighted_sum += eigenvalue * probability

        print(
            f"  lambda={format_number(eigenvalue)}, "
            f"p={probability:.6f}"
        )

    print("\nDirect expectation value:", format_number(expectation))
    print("Weighted eigenvalue average:", format_number(weighted_sum))

    print(
        "\nFor a Hermitian observable, the expectation value is the "
        "probability-weighted average of its possible eigenvalues."
    )


# ============================================================================
# SECTION 27: TWO-LEVEL HAMILTONIAN WITH NONTRIVIAL EIGENVECTORS
# ============================================================================

def demonstrate_two_level_hamiltonian() -> None:
    print("\n" + "=" * 78)
    print("26. NONTRIVIAL TWO-LEVEL HAMILTONIAN")
    print("=" * 78)

    delta = 1.5
    coupling = 0.8

    H = [
        [delta, coupling],
        [coupling, -delta],
    ]

    print("H:")
    print(format_matrix(H))

    energies = eigenvalues_2x2(H)

    for energy in energies:
        state = eigenvector_2x2(H, energy)
        residual = eigenpair_residual(H, energy, state)

        print(
            f"\nEnergy = {format_number(energy)}"
            f"\nEigenstate = {format_vector(state)}"
            f"\nResidual = {residual:.3e}"
        )

    print(
        "\nChanging the off-diagonal coupling changes the eigenvectors. "
        "This is a basic model of a coupled two-level quantum system."
    )


# ============================================================================
# SECTION 28: GLOBAL PHASE
# ============================================================================

def states_physically_equivalent_up_to_global_phase(
    a: Sequence[complex],
    b: Sequence[complex],
    tolerance: float = 1e-9,
) -> bool:
    """
    Two normalized pure states represent the same physical ray when

        |b> = exp(i theta) |a>

    for some real theta.
    """
    a = normalize(a)
    b = normalize(b)

    reference_index = None

    for index, value in enumerate(a):
        if abs(value) > tolerance:
            reference_index = index
            break

    if reference_index is None:
        return False

    phase = b[reference_index] / a[reference_index]

    if abs(phase) < tolerance:
        return False

    phase /= abs(phase)

    return all(
        abs(b[i] - phase * a[i]) <= tolerance
        for i in range(len(a))
    )


def demonstrate_global_phase() -> None:
    print("\n" + "=" * 78)
    print("27. GLOBAL PHASE VERSUS RELATIVE PHASE")
    print("=" * 78)

    state = ket_plus()
    globally_phased = [
        cmath.exp(1j * math.pi / 3) * x
        for x in state
    ]

    relative_phase_state = normalize([1 + 0j, 1j])

    print("Original:", format_vector(state))
    print("Global phase:", format_vector(globally_phased))
    print(
        "Same physical state:",
        states_physically_equivalent_up_to_global_phase(
            state,
            globally_phased,
        ),
    )

    print("\nRelative-phase state:", format_vector(relative_phase_state))
    print(
        "Same as original:",
        states_physically_equivalent_up_to_global_phase(
            state,
            relative_phase_state,
        ),
    )

    print(
        "\nA global phase has no observable consequence for an isolated "
        "pure state. A relative phase between amplitudes is physically "
        "meaningful and affects interference."
    )


# ============================================================================
# SECTION 29: ORTHOGONALITY OF DISTINCT EIGENVECTORS
# ============================================================================

def demonstrate_orthogonality() -> None:
    print("\n" + "=" * 78)
    print("28. ORTHOGONAL EIGENVECTORS OF HERMITIAN OPERATORS")
    print("=" * 78)

    A = [
        [2, 1],
        [1, 2],
    ]

    values = eigenvalues_2x2(A)
    vectors = [
        eigenvector_2x2(A, value)
        for value in values
    ]

    print("Eigenvectors:")
    for vector in vectors:
        print(" ", format_vector(vector))

    overlap = vector_inner_product(vectors[0], vectors[1])

    print("\nInner product between eigenvectors:")
    print(format_number(overlap))

    print(
        "\nFor Hermitian A, eigenvectors associated with distinct "
        "eigenvalues are orthogonal. This allows them to form an "
        "orthonormal measurement basis after normalization."
    )


# ============================================================================
# SECTION 30: TRACE, DETERMINANT, AND EIGENVALUE RELATIONSHIPS
# ============================================================================

def demonstrate_eigenvalue_invariants() -> None:
    print("\n" + "=" * 78)
    print("29. TRACE AND DETERMINANT AS EIGENVALUE INVARIANTS")
    print("=" * 78)

    A = [
        [4, 1],
        [2, 3],
    ]

    values = eigenvalues_2x2(A)

    eigenvalue_sum = sum(values)
    eigenvalue_product = values[0] * values[1]

    print("A:")
    print(format_matrix(A))

    print("\nTrace(A) =", format_number(matrix_trace(A)))
    print("Sum of eigenvalues =", format_number(eigenvalue_sum))

    print("\nDet(A) =", format_number(determinant(A)))
    print("Product of eigenvalues =", format_number(eigenvalue_product))

    print(
        "\nFor a square matrix, the trace equals the sum of eigenvalues "
        "counted with algebraic multiplicity, while the determinant equals "
        "their product."
    )


# ============================================================================
# SECTION 31: SIMULTANEOUS EIGENSTATES
# ============================================================================

def demonstrate_simultaneous_eigenstates() -> None:
    print("\n" + "=" * 78)
    print("30. SIMULTANEOUS EIGENSTATES OF COMMUTING OPERATORS")
    print("=" * 78)

    # X⊗X and Z⊗Z commute and have Bell states as simultaneous eigenstates.
    XX = kron_matrix(SIGMA_X, SIGMA_X)
    ZZ = kron_matrix(SIGMA_Z, SIGMA_Z)

    comm = commutator(XX, ZZ)

    print("[X⊗X, Z⊗Z] =")
    print(format_matrix(comm))

    state = bell_phi_plus()

    xx = matrix_vector_multiply(XX, state)
    zz = matrix_vector_multiply(ZZ, state)

    lambda_xx = vector_inner_product(state, xx)
    lambda_zz = vector_inner_product(state, zz)

    print("\n|Phi+> =", format_vector(state))
    print("XX eigenvalue =", format_number(lambda_xx))
    print("ZZ eigenvalue =", format_number(lambda_zz))

    print(
        "\nThis example demonstrates how commuting observables can have "
        "common eigenstates, which is central to compatible quantum "
        "measurements and stabilizer descriptions."
    )


# ============================================================================
# SECTION 32: EDGE CASES AND COMMON ERRORS
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("31. EDGE CASES AND COMMON IMPLEMENTATION MISTAKES")
    print("=" * 78)

    print("\n1. Zero vector cannot be normalized:")
    try:
        normalize([0j, 0j])
    except ValueError as error:
        print("  Correctly rejected:", error)

    print("\n2. Matrix-vector dimension mismatch:")
    try:
        matrix_vector_multiply([[1, 2], [3, 4]], [1])
    except ValueError as error:
        print("  Correctly rejected:", error)

    print("\n3. Non-square determinant:")
    try:
        determinant([[1, 2, 3], [4, 5, 6]])
    except ValueError as error:
        print("  Correctly rejected:", error)

    print("\n4. Non-Hermitian operator used as an observable:")
    non_hermitian = [
        [0, 1],
        [0, 0],
    ]

    print("  Is Hermitian:", is_hermitian(non_hermitian))

    print(
        "\nImportant distinction: an arbitrary square matrix can have "
        "eigenvalues and eigenvectors, but it is not automatically a "
        "valid quantum observable. Observables require Hermiticity."
    )


# ============================================================================
# SECTION 33: SECURITY AND IMPLEMENTATION CONSIDERATIONS
# ============================================================================

def demonstrate_implementation_considerations() -> None:
    print("\n" + "=" * 78)
    print("32. NUMERICAL, SECURITY, AND PRODUCTION CONSIDERATIONS")
    print("=" * 78)

    considerations = [
        (
            "Floating-point equality",
            "Use tolerances and residuals instead of exact equality."
        ),
        (
            "Ill-conditioned problems",
            "Small input errors can produce large changes in computed eigenvectors."
        ),
        (
            "Degenerate eigenspaces",
            "Individual eigenvectors may not be unique; the subspace is the stable object."
        ),
        (
            "Large matrices",
            "Recursive determinants and naive matrix multiplication become expensive."
        ),
        (
            "Complex arithmetic",
            "Do not silently discard imaginary components in quantum calculations."
        ),
        (
            "Input validation",
            "Validate dimensions, normalization, Hermiticity, and numerical ranges."
        ),
        (
            "Randomness",
            "Simulation of measurement outcomes requires an appropriate random-number model."
        ),
        (
            "Cryptographic security",
            "Ordinary pseudorandom simulation is not automatically suitable for cryptographic protocols."
        ),
        (
            "Production computation",
            "Use numerically tested eigensolvers such as Hermitian/symmetric routines for large systems."
        ),
    ]

    for name, explanation in considerations:
        print(f"\n{name}:")
        print(" ", explanation)


# ============================================================================
# SECTION 34: MEASUREMENT SAMPLING SIMULATION
# ============================================================================

def sample_discrete_outcome(probabilities: Sequence[float],
                            rng: random.Random) -> int:
    """Sample one index according to a probability distribution."""
    if not probabilities:
        raise ValueError("Probability list cannot be empty.")

    if any(p < -1e-12 for p in probabilities):
        raise ValueError("Probabilities cannot be negative.")

    total = sum(probabilities)

    if abs(total - 1.0) > 1e-9:
        raise ValueError("Probabilities must sum to 1.")

    threshold = rng.random()
    cumulative = 0.0

    for index, probability in enumerate(probabilities):
        cumulative += max(0.0, probability)

        if threshold < cumulative:
            return index

    return len(probabilities) - 1


def demonstrate_measurement_sampling() -> None:
    print("\n" + "=" * 78)
    print("33. SIMULATED QUANTUM MEASUREMENT")
    print("=" * 78)

    state = normalize([1, 2])

    basis = [ket_zero(), ket_one()]
    probabilities = [
        measurement_probability(b, state)
        for b in basis
    ]

    rng = random.Random(42)
    shots = 1000
    counts = [0, 0]

    for _ in range(shots):
        outcome = sample_discrete_outcome(probabilities, rng)
        counts[outcome] += 1

    print("State:", format_vector(state))
    print("Theoretical probabilities:", probabilities)
    print("Shots:", shots)
    print("Counts:", counts)
    print(
        "Empirical probabilities:",
        [count / shots for count in counts],
    )

    print(
        "\nRepeated measurement approaches the Born-rule probabilities "
        "as the number of independent shots increases."
    )


# ============================================================================
# SECTION 35: VARIANCE OF AN OBSERVABLE
# ============================================================================

def observable_variance(state: Sequence[complex],
                        operator: Matrix) -> float:
    """
    Variance:

        Var(A) = <A^2> - <A>^2

    For Hermitian A, the result is real and nonnegative up to numerical noise.
    """
    mean = expectation_value(state, operator)
    second_moment = expectation_value(
        state,
        matrix_multiply(operator, operator),
    )

    variance = (second_moment - mean * mean).real

    if abs(variance) < 1e-12:
        return 0.0

    return variance


def demonstrate_observable_variance() -> None:
    print("\n" + "=" * 78)
    print("34. EIGENSTATES, UNCERTAINTY, AND VARIANCE")
    print("=" * 78)

    states = {
        "|0>": ket_zero(),
        "|+>": ket_plus(),
        "generic": normalize([1, 1 + 1j]),
    }

    for name, state in states.items():
        variance_x = observable_variance(state, SIGMA_X)
        variance_z = observable_variance(state, SIGMA_Z)

        print(
            f"{name:8s}: Var(X)={variance_x:.6f}, "
            f"Var(Z)={variance_z:.6f}"
        )

    print(
        "\nAn eigenstate of an observable has zero variance for that "
        "observable because measurement always returns the corresponding "
        "eigenvalue."
    )


# ============================================================================
# SECTION 36: EIGENVALUE PROBLEM AS A QUANTUM COMPUTING WORKFLOW
# ============================================================================

def quantum_eigenvalue_workflow() -> None:
    print("\n" + "=" * 78)
    print("35. COMPLETE EIGENVALUE WORKFLOW FOR A QUANTUM OBSERVABLE")
    print("=" * 78)

    observable = [
        [1, 2],
        [2, 4],
    ]

    print("Observable candidate:")
    print(format_matrix(observable))

    print("\nStep 1: Check Hermiticity")
    print("Hermitian:", is_hermitian(observable))

    print("\nStep 2: Determine eigenvalues")
    values = eigenvalues_2x2(observable)

    for value in values:
        print(" ", format_number(value))

    print("\nStep 3: Determine eigenvectors")

    for value in values:
        vector = eigenvector_2x2(observable, value)
        residual = eigenpair_residual(observable, value, vector)

        print(
            f"lambda={format_number(value)}, "
            f"v={format_vector(vector)}, "
            f"residual={residual:.3e}"
        )

    print(
        "\nStep 4: Interpret eigenvalues as possible measurement outcomes "
        "and normalized eigenvectors as corresponding measurement states."
    )

    state = normalize([1, 1])

    print("\nStep 5: Evaluate expectation value")
    print(
        "<A> =",
        format_number(expectation_value(state, observable)),
    )


# ============================================================================
# SECTION 37: TEST SUITE
# ============================================================================

def assert_close(a: complex,
                 b: complex,
                 tolerance: float = 1e-8) -> None:
    if abs(a - b) > tolerance:
        raise AssertionError(
            f"Values differ: {a} versus {b}, "
            f"tolerance={tolerance}"
        )


def assert_vector_close(a: Sequence[complex],
                        b: Sequence[complex],
                        tolerance: float = 1e-8) -> None:
    if len(a) != len(b):
        raise AssertionError("Vectors have different dimensions.")

    for x, y in zip(a, b):
        assert_close(x, y, tolerance)


def run_tests() -> None:
    """Small correctness suite covering the central mathematical ideas."""

    # Matrix multiplication.
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    assert matrix_multiply(A, B) == [
        [19, 22],
        [43, 50],
    ]

    # Norm and normalization.
    normalized = normalize([3, 4])
    assert_close(vector_norm(normalized), 1.0)

    # Pauli Hermiticity.
    assert is_hermitian(SIGMA_X)
    assert is_hermitian(SIGMA_Y)
    assert is_hermitian(SIGMA_Z)

    # Pauli unitarity.
    assert is_unitary(SIGMA_X)
    assert is_unitary(SIGMA_Y)
    assert is_unitary(SIGMA_Z)

    # Hadamard unitarity.
    assert is_unitary(HADAMARD)

    # Eigenpairs.
    A = [[2, 1], [1, 2]]

    for eigenvalue in eigenvalues_2x2(A):
        vector = eigenvector_2x2(A, eigenvalue)
        assert eigenpair_residual(A, eigenvalue, vector) < 1e-8

    # Computational-basis probabilities.
    state = normalize([3, 4])
    p0 = measurement_probability(ket_zero(), state)
    p1 = measurement_probability(ket_one(), state)

    assert_close(p0, 9 / 25)
    assert_close(p1, 16 / 25)
    assert_close(p0 + p1, 1.0)

    # Bell-state normalization.
    for bell in [
        bell_phi_plus(),
        bell_phi_minus(),
        bell_psi_plus(),
        bell_psi_minus(),
    ]:
        assert_close(vector_norm(bell), 1.0)

    # Density matrix trace and purity.
    rho = density_matrix_from_state(ket_plus())
    assert_close(matrix_trace(rho), 1.0)
    assert_close(density_matrix_purity(rho), 1.0)

    mixed = [
        [0.5, 0],
        [0, 0.5],
    ]
    assert_close(density_matrix_purity(mixed), 0.5)

    # Entropy.
    assert_close(von_neumann_entropy_2x2(rho), 0.0)
    assert_close(von_neumann_entropy_2x2(mixed), 1.0)

    # Commutator [X, X] = 0.
    assert matrices_approximately_equal(
        commutator(SIGMA_X, SIGMA_X),
        zero_matrix(2, 2),
    )

    # Global phase equivalence.
    state = ket_plus()
    phase_state = [
        cmath.exp(1j * 0.73) * x
        for x in state
    ]

    assert states_physically_equivalent_up_to_global_phase(
        state,
        phase_state,
    )

    print("\nAll tests passed.")


# ============================================================================
# SECTION 38: CONCEPTUAL REFERENCE TABLE
# ============================================================================

def print_reference_table() -> None:
    print("\n" + "=" * 78)
    print("36. CONCEPTUAL REFERENCE")
    print("=" * 78)

    reference = [
        ("Eigenvalue equation", "A|v> = lambda|v>"),
        ("Characteristic equation", "det(A - lambda I) = 0"),
        ("Normalization", "<psi|psi> = 1"),
        ("Probability", "p = |<phi|psi>|^2"),
        ("Expectation value", "<A> = <psi|A|psi>"),
        ("Density expectation", "<A> = Tr(rho A)"),
        ("Projector", "P = |v><v|"),
        ("Hermitian operator", "A† = A"),
        ("Unitary operator", "U†U = I"),
        ("Time evolution", "U(t) = exp(-iHt/hbar)"),
        ("Commutator", "[A,B] = AB - BA"),
        ("Variance", "Var(A) = <A^2> - <A>^2"),
        ("Purity", "Tr(rho^2)"),
        ("Entropy", "S(rho) = -Tr(rho log2 rho)"),
        ("Bloch coordinates", "(<X>, <Y>, <Z>)"),
        ("Tensor-product dimension", "2^n for n qubits"),
    ]

    width = max(len(name) for name, _ in reference)

    for name, expression in reference:
        print(f"{name:<{width}} : {expression}")


# ============================================================================
# SECTION 39: MAIN EDUCATIONAL RUNNER
# ============================================================================

def main() -> None:
    """
    Execute the complete tutorial.

    The script intentionally prints both mathematical objects and numerical
    checks so that the relationship between the theory and implementation is
    visible.
    """
    print("=" * 78)
    print("EIGENVALUES & EIGENVECTORS: QUANTUM-STATE APPLICATIONS")
    print("=" * 78)
    print(
        "\nThis tutorial develops eigenvalue/eigenvector concepts and "
        "connects them directly to quantum states, observables, measurement, "
        "Hamiltonians, unitary evolution, and multi-qubit systems."
    )

    demonstrate_eigenvector_definition()
    demonstrate_characteristic_equation()
    demonstrate_eigenvectors()
    demonstrate_hermitian_matrices()
    demonstrate_quantum_state()
    demonstrate_projectors_and_expectation()
    demonstrate_pauli_matrices()
    demonstrate_measurement_bases()
    demonstrate_spectral_decomposition()
    demonstrate_hamiltonian_eigenstates()
    demonstrate_time_evolution()
    demonstrate_bloch_sphere_coordinates()
    demonstrate_degeneracy()
    demonstrate_power_iteration()
    demonstrate_numerical_validation()
    demonstrate_tensor_products()
    demonstrate_bell_states()
    demonstrate_density_matrices()
    demonstrate_density_expectation()
    demonstrate_entropy()
    demonstrate_commutators()
    demonstrate_quantum_gates()
    demonstrate_matrix_functions()
    demonstrate_projective_measurement()
    demonstrate_expectation_as_weighted_average()
    demonstrate_two_level_hamiltonian()
    demonstrate_global_phase()
    demonstrate_orthogonality()
    demonstrate_eigenvalue_invariants()
    demonstrate_simultaneous_eigenstates()
    demonstrate_edge_cases()
    demonstrate_implementation_considerations()
    demonstrate_measurement_sampling()
    demonstrate_observable_variance()
    quantum_eigenvalue_workflow()
    print_reference_table()

    print("\n" + "=" * 78)
    print("RUNNING TESTS")
    print("=" * 78)
    run_tests()


if __name__ == "__main__":
    main()
