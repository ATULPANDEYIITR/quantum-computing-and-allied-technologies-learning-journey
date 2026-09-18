"""
Operators: Hermitian and Unitary Operators
==========================================

A standalone study file covering operator basics, adjoints, Hermitian operators,
unitary operators, spectral properties, observables, projectors, quantum-state
transformations, numerical verification, and a small quantum-circuit simulator.

The script uses only Python's standard library.
"""

from __future__ import annotations

import cmath
import math
import random
from typing import Callable, Iterable, List, Sequence, Tuple


ComplexMatrix = List[List[complex]]
ComplexVector = List[complex]


# ---------------------------------------------------------------------------
# 1. Basic complex-number and matrix utilities
# ---------------------------------------------------------------------------

def format_complex(value: complex, digits: int = 4) -> str:
    """Format a complex number compactly for educational output."""
    real = round(value.real, digits)
    imag = round(value.imag, digits)

    if abs(real) < 10 ** (-digits):
        real = 0.0
    if abs(imag) < 10 ** (-digits):
        imag = 0.0

    if imag == 0:
        return f"{real:g}"
    if real == 0:
        return f"{imag:g}i"
    sign = "+" if imag >= 0 else "-"
    return f"{real:g}{sign}{abs(imag):g}i"


def format_vector(vector: Sequence[complex]) -> str:
    return "[" + ", ".join(format_complex(x) for x in vector) + "]"


def format_matrix(matrix: ComplexMatrix) -> str:
    rows = []
    for row in matrix:
        rows.append("[ " + ", ".join(f"{format_complex(x):>10}" for x in row) + " ]")
    return "\n".join(rows)


def zeros(rows: int, columns: int) -> ComplexMatrix:
    return [[0j for _ in range(columns)] for _ in range(rows)]


def identity_matrix(size: int) -> ComplexMatrix:
    return [
        [1 + 0j if row == column else 0j for column in range(size)]
        for row in range(size)
    ]


def clone_matrix(matrix: ComplexMatrix) -> ComplexMatrix:
    return [row[:] for row in matrix]


def matrix_shape(matrix: ComplexMatrix) -> Tuple[int, int]:
    if not matrix:
        return 0, 0
    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal lengths.")
    return len(matrix), columns


def validate_square_matrix(matrix: ComplexMatrix) -> None:
    rows, columns = matrix_shape(matrix)
    if rows != columns:
        raise ValueError("The operator must be represented by a square matrix.")


def validate_vector(vector: Sequence[complex]) -> None:
    if not vector:
        raise ValueError("A vector cannot be empty.")


def matrix_add(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    shape_a = matrix_shape(a)
    shape_b = matrix_shape(b)
    if shape_a != shape_b:
        raise ValueError("Matrices must have the same dimensions.")
    return [
        [x + y for x, y in zip(row_a, row_b)]
        for row_a, row_b in zip(a, b)
    ]


def matrix_subtract(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    shape_a = matrix_shape(a)
    shape_b = matrix_shape(b)
    if shape_a != shape_b:
        raise ValueError("Matrices must have the same dimensions.")
    return [
        [x - y for x, y in zip(row_a, row_b)]
        for row_a, row_b in zip(a, b)
    ]


def matrix_scalar_multiply(
    scalar: complex, matrix: ComplexMatrix
) -> ComplexMatrix:
    return [[scalar * value for value in row] for row in matrix]


def matrix_multiply(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    rows_a, columns_a = matrix_shape(a)
    rows_b, columns_b = matrix_shape(b)

    if columns_a != rows_b:
        raise ValueError(
            f"Cannot multiply a {rows_a}x{columns_a} matrix by "
            f"a {rows_b}x{columns_b} matrix."
        )

    result = zeros(rows_a, columns_b)

    for i in range(rows_a):
        for j in range(columns_b):
            result[i][j] = sum(
                a[i][k] * b[k][j] for k in range(columns_a)
            )

    return result


def matrix_vector_multiply(
    matrix: ComplexMatrix, vector: Sequence[complex]
) -> ComplexVector:
    rows, columns = matrix_shape(matrix)
    if columns != len(vector):
        raise ValueError(
            f"Matrix has {columns} columns but vector has {len(vector)} entries."
        )

    return [
        sum(matrix[row][column] * vector[column] for column in range(columns))
        for row in range(rows)
    ]


def vector_inner_product(
    left: Sequence[complex], right: Sequence[complex]
) -> complex:
    if len(left) != len(right):
        raise ValueError("Vectors must have equal dimensions.")
    return sum(
        left[index].conjugate() * right[index]
        for index in range(len(left))
    )


def vector_norm(vector: Sequence[complex]) -> float:
    return math.sqrt(vector_inner_product(vector, vector).real)


def normalize_vector(vector: Sequence[complex]) -> ComplexVector:
    norm = vector_norm(vector)
    if norm == 0:
        raise ValueError("The zero vector cannot be normalized.")
    return [value / norm for value in vector]


def conjugate_transpose(matrix: ComplexMatrix) -> ComplexMatrix:
    rows, columns = matrix_shape(matrix)
    return [
        [matrix[row][column].conjugate() for row in range(rows)]
        for column in range(columns)
    ]


def transpose(matrix: ComplexMatrix) -> ComplexMatrix:
    rows, columns = matrix_shape(matrix)
    return [
        [matrix[row][column] for row in range(rows)]
        for column in range(columns)
    ]


def trace(matrix: ComplexMatrix) -> complex:
    validate_square_matrix(matrix)
    return sum(matrix[i][i] for i in range(len(matrix)))


def matrix_max_abs_difference(a: ComplexMatrix, b: ComplexMatrix) -> float:
    difference = matrix_subtract(a, b)
    return max(
        (abs(value) for row in difference for value in row),
        default=0.0,
    )


def vector_max_abs_difference(
    a: Sequence[complex], b: Sequence[complex]
) -> float:
    if len(a) != len(b):
        return math.inf
    return max(
        (abs(x - y) for x, y in zip(a, b)),
        default=0.0,
    )


def matrices_close(
    a: ComplexMatrix,
    b: ComplexMatrix,
    tolerance: float = 1e-10,
) -> bool:
    return matrix_max_abs_difference(a, b) <= tolerance


def vectors_close(
    a: Sequence[complex],
    b: Sequence[complex],
    tolerance: float = 1e-10,
) -> bool:
    return vector_max_abs_difference(a, b) <= tolerance


def is_identity(
    matrix: ComplexMatrix,
    tolerance: float = 1e-10,
) -> bool:
    rows, columns = matrix_shape(matrix)
    if rows != columns:
        return False
    return matrices_close(matrix, identity_matrix(rows), tolerance)


# ---------------------------------------------------------------------------
# 2. Operators and the adjoint
# ---------------------------------------------------------------------------

def adjoint(operator: ComplexMatrix) -> ComplexMatrix:
    """
    The adjoint A† is the conjugate transpose of A.

    For a matrix:
        A† = (A*)^T

    Hermitian operators satisfy:
        A† = A

    Unitary operators satisfy:
        A† A = A A† = I
    """
    return conjugate_transpose(operator)


def is_hermitian(
    operator: ComplexMatrix,
    tolerance: float = 1e-10,
) -> bool:
    validate_square_matrix(operator)
    return matrices_close(operator, adjoint(operator), tolerance)


def is_unitary(
    operator: ComplexMatrix,
    tolerance: float = 1e-10,
) -> bool:
    validate_square_matrix(operator)
    identity = identity_matrix(len(operator))
    left_product = matrix_multiply(adjoint(operator), operator)
    right_product = matrix_multiply(operator, adjoint(operator))
    return (
        matrices_close(left_product, identity, tolerance)
        and matrices_close(right_product, identity, tolerance)
    )


def is_normal(
    operator: ComplexMatrix,
    tolerance: float = 1e-10,
) -> bool:
    """
    A normal operator satisfies A†A = AA†.

    Every Hermitian and every unitary operator is normal.
    The converse is not true.
    """
    validate_square_matrix(operator)
    return matrices_close(
        matrix_multiply(adjoint(operator), operator),
        matrix_multiply(operator, adjoint(operator)),
        tolerance,
    )


def apply_operator(
    operator: ComplexMatrix,
    state: Sequence[complex],
) -> ComplexVector:
    """Apply an operator to a state vector."""
    return matrix_vector_multiply(operator, state)


# ---------------------------------------------------------------------------
# 3. Pauli operators and common quantum operators
# ---------------------------------------------------------------------------

I2 = [
    [1 + 0j, 0j],
    [0j, 1 + 0j],
]

X = [
    [0j, 1 + 0j],
    [1 + 0j, 0j],
]

Y = [
    [0j, -1j],
    [1j, 0j],
]

Z = [
    [1 + 0j, 0j],
    [0j, -1 + 0j],
]

H = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]


def phase_gate(theta: float) -> ComplexMatrix:
    return [
        [1 + 0j, 0j],
        [0j, cmath.exp(1j * theta)],
    ]


def rotation_x(theta: float) -> ComplexMatrix:
    half = theta / 2
    return [
        [math.cos(half), -1j * math.sin(half)],
        [-1j * math.sin(half), math.cos(half)],
    ]


def rotation_y(theta: float) -> ComplexMatrix:
    half = theta / 2
    return [
        [math.cos(half), -math.sin(half)],
        [math.sin(half), math.cos(half)],
    ]


def rotation_z(theta: float) -> ComplexMatrix:
    half = theta / 2
    return [
        [cmath.exp(-1j * half), 0j],
        [0j, cmath.exp(1j * half)],
    ]


# ---------------------------------------------------------------------------
# 4. Demonstrating fundamental distinctions
# ---------------------------------------------------------------------------

def demonstrate_basic_properties() -> None:
    print("\n" + "=" * 78)
    print("1. FUNDAMENTAL OPERATOR PROPERTIES")
    print("=" * 78)

    print("\nIdentity operator:")
    print(format_matrix(I2))
    print("Hermitian:", is_hermitian(I2))
    print("Unitary:", is_unitary(I2))
    print("Normal:", is_normal(I2))

    print("\nPauli-X operator:")
    print(format_matrix(X))
    print("Hermitian:", is_hermitian(X))
    print("Unitary:", is_unitary(X))
    print("X†X:")
    print(format_matrix(matrix_multiply(adjoint(X), X)))

    print("\nPauli-Y operator:")
    print(format_matrix(Y))
    print("Hermitian:", is_hermitian(Y))
    print("Unitary:", is_unitary(Y))

    print("\nPauli-Z operator:")
    print(format_matrix(Z))
    print("Hermitian:", is_hermitian(Z))
    print("Unitary:", is_unitary(Z))

    print("\nHadamard operator:")
    print(format_matrix(H))
    print("Hermitian:", is_hermitian(H))
    print("Unitary:", is_unitary(H))

    print(
        "\nImportant distinction: an operator can be both Hermitian and unitary."
    )
    print(
        "Pauli X, Y, Z and Hadamard are examples. Hermitian and unitary are "
        "different mathematical conditions."
    )


# ---------------------------------------------------------------------------
# 5. States, normalization, and expectation values
# ---------------------------------------------------------------------------

def probability_amplitudes_to_probabilities(
    state: Sequence[complex],
) -> List[float]:
    return [abs(amplitude) ** 2 for amplitude in state]


def expectation_value(
    state: Sequence[complex],
    operator: ComplexMatrix,
) -> complex:
    """
    Expectation value:

        <A> = <psi| A |psi>

    For a normalized state and Hermitian A, the result is real up to
    floating-point error.
    """
    normalized_state = normalize_vector(state)
    transformed = apply_operator(operator, normalized_state)
    return vector_inner_product(normalized_state, transformed)


def variance(
    state: Sequence[complex],
    operator: ComplexMatrix,
) -> float:
    """
    Variance:

        Var(A) = <A^2> - <A>^2

    For Hermitian A, the result should be real and non-negative.
    """
    normalized_state = normalize_vector(state)
    mean = expectation_value(normalized_state, operator)
    squared_operator = matrix_multiply(operator, operator)
    second_moment = expectation_value(normalized_state, squared_operator)
    result = second_moment - mean * mean

    if abs(result.imag) < 1e-10:
        return max(0.0, result.real)
    return result.real


def demonstrate_observables() -> None:
    print("\n" + "=" * 78)
    print("2. HERMITIAN OPERATORS AS OBSERVABLES")
    print("=" * 78)

    zero_state = [1 + 0j, 0j]
    one_state = [0j, 1 + 0j]
    plus_state = normalize_vector([1 + 0j, 1 + 0j])
    arbitrary_state = normalize_vector(
        [1 + 0j, 1j]
    )

    for name, state in [
        ("|0>", zero_state),
        ("|1>", one_state),
        ("|+>", plus_state),
        ("( |0> + i|1> ) / sqrt(2)", arbitrary_state),
    ]:
        print(f"\nState {name}")
        print("Vector:", format_vector(state))
        print(
            "Probabilities:",
            [round(p, 6) for p in probability_amplitudes_to_probabilities(state)],
        )

        for observable_name, observable in [
            ("X", X),
            ("Y", Y),
            ("Z", Z),
        ]:
            value = expectation_value(state, observable)
            spread = variance(state, observable)
            print(
                f"  <{observable_name}> = {format_complex(value)}, "
                f"variance = {spread:.6f}"
            )


# ---------------------------------------------------------------------------
# 6. Spectral properties and projectors
# ---------------------------------------------------------------------------

def projective_measurement_probability(
    state: Sequence[complex],
    projector: ComplexMatrix,
) -> float:
    probability = expectation_value(state, projector)
    if abs(probability.imag) > 1e-9:
        raise ValueError("A projector expectation should be real.")
    return min(1.0, max(0.0, probability.real))


P0 = [
    [1 + 0j, 0j],
    [0j, 0j],
]

P1 = [
    [0j, 0j],
    [0j, 1 + 0j],
]


def verify_projector(projector: ComplexMatrix) -> bool:
    """A projector obeys P² = P."""
    squared = matrix_multiply(projector, projector)
    return matrices_close(squared, projector)


def demonstrate_projectors() -> None:
    print("\n" + "=" * 78)
    print("3. PROJECTORS AND SPECTRAL STRUCTURE")
    print("=" * 78)

    for name, projector in [("P0", P0), ("P1", P1)]:
        print(f"\n{name}:")
        print(format_matrix(projector))
        print("Hermitian:", is_hermitian(projector))
        print("Projector condition P² = P:", verify_projector(projector))

    state = normalize_vector(
        [math.sqrt(0.7), cmath.exp(1j * 0.3) * math.sqrt(0.3)]
    )

    print("\nState:")
    print(format_vector(state))
    print("Probability of outcome 0:", projective_measurement_probability(state, P0))
    print("Probability of outcome 1:", projective_measurement_probability(state, P1))
    print(
        "Probabilities sum to:",
        projective_measurement_probability(state, P0)
        + projective_measurement_probability(state, P1),
    )

    print(
        "\nFor a Hermitian observable, the spectral theorem gives an "
        "orthonormal eigenbasis and real eigenvalues."
    )


# ---------------------------------------------------------------------------
# 7. Unitary operators preserve inner products and norms
# ---------------------------------------------------------------------------

def inner_product_preservation_test(
    operator: ComplexMatrix,
    first_state: Sequence[complex],
    second_state: Sequence[complex],
) -> Tuple[complex, complex]:
    transformed_first = apply_operator(operator, first_state)
    transformed_second = apply_operator(operator, second_state)

    before = vector_inner_product(first_state, second_state)
    after = vector_inner_product(transformed_first, transformed_second)
    return before, after


def demonstrate_unitary_invariance() -> None:
    print("\n" + "=" * 78)
    print("4. UNITARY OPERATORS PRESERVE GEOMETRY")
    print("=" * 78)

    state_a = normalize_vector([1 + 0j, 2 - 1j])
    state_b = normalize_vector([2 + 1j, -1 + 0j])

    for name, operator in [
        ("X", X),
        ("Y", Y),
        ("Z", Z),
        ("H", H),
        ("Rz(pi/3)", rotation_z(math.pi / 3)),
    ]:
        before, after = inner_product_preservation_test(
            operator, state_a, state_b
        )
        norm_before = vector_norm(state_a)
        norm_after = vector_norm(apply_operator(operator, state_a))

        print(f"\n{name}")
        print("  unitary:", is_unitary(operator))
        print("  inner product before:", format_complex(before))
        print("  inner product after :", format_complex(after))
        print(f"  norm before: {norm_before:.12f}")
        print(f"  norm after : {norm_after:.12f}")


# ---------------------------------------------------------------------------
# 8. Composition and inverses
# ---------------------------------------------------------------------------

def demonstrate_composition() -> None:
    print("\n" + "=" * 78)
    print("5. COMPOSITION, INVERSES, AND ORDER")
    print("=" * 78)

    hx = matrix_multiply(H, X)
    xh = matrix_multiply(X, H)

    print("\nH X:")
    print(format_matrix(hx))

    print("\nX H:")
    print(format_matrix(xh))

    print("\nAre HX and XH equal?", matrices_close(hx, xh))
    print(
        "Matrix multiplication is generally non-commutative, so operator order "
        "matters."
    )

    x_inverse = adjoint(X)
    h_inverse = adjoint(H)

    print("\nFor a unitary U, U† = U⁻¹.")
    print("X†:")
    print(format_matrix(x_inverse))
    print("H†:")
    print(format_matrix(h_inverse))

    print("X†X = I:", is_identity(matrix_multiply(x_inverse, X)))
    print("H†H = I:", is_identity(matrix_multiply(h_inverse, H)))


# ---------------------------------------------------------------------------
# 9. Hermitian versus unitary examples and counterexamples
# ---------------------------------------------------------------------------

def demonstrate_counterexamples() -> None:
    print("\n" + "=" * 78)
    print("6. COUNTEREXAMPLES AND IMPORTANT DISTINCTIONS")
    print("=" * 78)

    hermitian_not_unitary = [
        [2 + 0j, 0j],
        [0j, -3 + 0j],
    ]

    unitary_not_hermitian = phase_gate(math.pi / 3)

    non_normal = [
        [0j, 1 + 0j],
        [0j, 0j],
    ]

    matrices = [
        ("Hermitian but not unitary", hermitian_not_unitary),
        ("Unitary but not Hermitian", unitary_not_hermitian),
        ("Neither Hermitian nor unitary", non_normal),
    ]

    for name, operator in matrices:
        print(f"\n{name}:")
        print(format_matrix(operator))
        print("Hermitian:", is_hermitian(operator))
        print("Unitary:", is_unitary(operator))
        print("Normal:", is_normal(operator))

    print(
        "\nA Hermitian matrix may have real eigenvalues without preserving norms."
    )
    print(
        "A unitary matrix preserves norms and has eigenvalues on the unit circle."
    )
    print(
        "A general operator need not be Hermitian, unitary, or normal."
    )


# ---------------------------------------------------------------------------
# 10. Eigenvalue equations without external numerical packages
# ---------------------------------------------------------------------------

def eigenvalues_2x2(matrix: ComplexMatrix) -> Tuple[complex, complex]:
    """
    Closed-form eigenvalues for a 2x2 complex matrix.

        lambda² - tr(A) lambda + det(A) = 0

    This is intentionally limited to 2x2 matrices so the example remains
    self-contained and avoids implementing a general-purpose eigensolver.
    """
    rows, columns = matrix_shape(matrix)
    if rows != 2 or columns != 2:
        raise ValueError("This educational solver supports only 2x2 matrices.")

    a, b = matrix[0]
    c, d = matrix[1]

    tr = a + d
    determinant = a * d - b * c
    discriminant = tr * tr - 4 * determinant
    root = cmath.sqrt(discriminant)

    return (
        (tr + root) / 2,
        (tr - root) / 2,
    )


def demonstrate_eigenvalues() -> None:
    print("\n" + "=" * 78)
    print("7. EIGENVALUES AND HERMITIAN/UNITARY STRUCTURE")
    print("=" * 78)

    operators = [
        ("X", X),
        ("Y", Y),
        ("Z", Z),
        ("H", H),
        ("Rz(pi/2)", rotation_z(math.pi / 2)),
        ("Diagonal Hermitian", [[2 + 0j, 0j], [0j, -3 + 0j]]),
    ]

    for name, operator in operators:
        values = eigenvalues_2x2(operator)
        print(f"\n{name}")
        print("  eigenvalue 1:", format_complex(values[0]))
        print("  eigenvalue 2:", format_complex(values[1]))

        if is_hermitian(operator):
            print("  Hermitian consequence: eigenvalues should be real.")

        if is_unitary(operator):
            print(
                "  Unitary consequence: eigenvalues should have magnitude 1."
            )


# ---------------------------------------------------------------------------
# 11. Functions of Hermitian operators
# ---------------------------------------------------------------------------

def matrix_power(operator: ComplexMatrix, exponent: int) -> ComplexMatrix:
    if exponent < 0:
        raise ValueError("This educational function accepts non-negative powers.")
    validate_square_matrix(operator)

    result = identity_matrix(len(operator))
    base = clone_matrix(operator)

    # Exponentiation by squaring reduces multiplication count from O(n)
    # matrix multiplications to O(log n).
    while exponent:
        if exponent & 1:
            result = matrix_multiply(result, base)
        base = matrix_multiply(base, base)
        exponent >>= 1

    return result


def demonstrate_matrix_powers() -> None:
    print("\n" + "=" * 78)
    print("8. OPERATOR POWERS")
    print("=" * 78)

    for name, operator in [("X", X), ("Y", Y), ("Z", Z), ("H", H)]:
        print(f"\n{name}²:")
        print(format_matrix(matrix_power(operator, 2)))

    print(
        "\nPauli matrices satisfy X² = Y² = Z² = I."
    )
    print(
        "Hadamard also satisfies H² = I, which means H is its own inverse."
    )


# ---------------------------------------------------------------------------
# 12. Unitary time evolution
# ---------------------------------------------------------------------------

def approximate_matrix_exponential(
    matrix: ComplexMatrix,
    terms: int = 40,
) -> ComplexMatrix:
    """
    Compute exp(A) with a direct Taylor series:

        exp(A) = I + A + A²/2! + A³/3! + ...

    This is an educational implementation, not a production-quality matrix
    exponential. Numerical libraries use more stable algorithms such as
    scaling-and-squaring with Padé approximants.

    For A = -iHt with Hermitian H, exp(A) is unitary.
    """
    validate_square_matrix(matrix)
    size = len(matrix)

    result = identity_matrix(size)
    term = identity_matrix(size)
    factorial = 1

    for power in range(1, terms):
        term = matrix_multiply(term, matrix)
        factorial *= power
        result = matrix_add(
            result,
            matrix_scalar_multiply(1 / factorial, term),
        )

    return result


def demonstrate_time_evolution() -> None:
    print("\n" + "=" * 78)
    print("9. HERMITIAN HAMILTONIAN AND UNITARY TIME EVOLUTION")
    print("=" * 78)

    hamiltonian = matrix_scalar_multiply(0.75, Z)
    time = 1.2

    generator = matrix_scalar_multiply(-1j * time, hamiltonian)
    evolution = approximate_matrix_exponential(generator)

    print("\nHamiltonian H:")
    print(format_matrix(hamiltonian))

    print("\nEvolution operator U = exp(-iHt):")
    print(format_matrix(evolution))

    print("\nH is Hermitian:", is_hermitian(hamiltonian))
    print("U is approximately unitary:", is_unitary(evolution, 1e-8))

    state = normalize_vector([1 + 0j, 1 + 0j])
    evolved = apply_operator(evolution, state)

    print("\nInitial state:")
    print(format_vector(state))
    print("Evolved state:")
    print(format_vector(evolved))
    print("Initial norm:", vector_norm(state))
    print("Evolved norm:", vector_norm(evolved))

    print(
        "\nThe relation U(t) = exp(-iHt) connects Hermitian generators H "
        "with unitary time-evolution operators U."
    )


# ---------------------------------------------------------------------------
# 13. Quantum gates and state evolution
# ---------------------------------------------------------------------------

def basis_state(index: int, dimension: int) -> ComplexVector:
    if index < 0 or index >= dimension:
        raise ValueError("Basis-state index is outside the vector dimension.")
    state = [0j] * dimension
    state[index] = 1 + 0j
    return state


def demonstrate_single_qubit_circuit() -> None:
    print("\n" + "=" * 78)
    print("10. SINGLE-QUBIT UNITARY CIRCUIT")
    print("=" * 78)

    state = basis_state(0, 2)
    print("\nInitial |0>:", format_vector(state))

    state = apply_operator(H, state)
    print("After H:", format_vector(state))

    state = apply_operator(Z, state)
    print("After Z:", format_vector(state))

    state = apply_operator(H, state)
    print("After H:", format_vector(state))

    probabilities = probability_amplitudes_to_probabilities(state)
    print("Final probabilities:", [round(p, 8) for p in probabilities])

    print(
        "\nThe final state is |1> up to numerical round-off. "
        "Each gate is unitary, so normalization is preserved."
    )


# ---------------------------------------------------------------------------
# 14. Multi-qubit tensor products
# ---------------------------------------------------------------------------

def tensor_product(
    a: ComplexMatrix,
    b: ComplexMatrix,
) -> ComplexMatrix:
    """
    Kronecker product A ⊗ B.

    If A is m×n and B is p×q, the result is (mp)×(nq).
    """
    rows_a, columns_a = matrix_shape(a)
    rows_b, columns_b = matrix_shape(b)

    result = zeros(rows_a * rows_b, columns_a * columns_b)

    for i in range(rows_a):
        for j in range(columns_a):
            for k in range(rows_b):
                for l in range(columns_b):
                    result[i * rows_b + k][j * columns_b + l] = (
                        a[i][j] * b[k][l]
                    )

    return result


def demonstrate_tensor_products() -> None:
    print("\n" + "=" * 78)
    print("11. TENSOR PRODUCTS AND MULTI-QUBIT OPERATORS")
    print("=" * 78)

    two_qubit_hadamard = tensor_product(H, H)
    two_qubit_x_identity = tensor_product(X, I2)

    print("\nH ⊗ H:")
    print(format_matrix(two_qubit_hadamard))
    print("Unitary:", is_unitary(two_qubit_hadamard))

    print("\nX ⊗ I:")
    print(format_matrix(two_qubit_x_identity))
    print("Unitary:", is_unitary(two_qubit_x_identity))

    state_00 = basis_state(0, 4)
    transformed = apply_operator(two_qubit_hadamard, state_00)

    print("\n(H ⊗ H)|00>:")
    print(format_vector(transformed))
    print(
        "Each of the four computational-basis states has probability 1/4."
    )


# ---------------------------------------------------------------------------
# 15. Controlled unitary construction
# ---------------------------------------------------------------------------

def controlled_unitary(single_qubit_operator: ComplexMatrix) -> ComplexMatrix:
    """
    Construct a controlled-U gate for one control qubit and one target qubit.

    Basis order:
        |00>, |01>, |10>, |11>

    The control is the first qubit. If control = 0, identity acts on target.
    If control = 1, U acts on target.
    """
    if matrix_shape(single_qubit_operator) != (2, 2):
        raise ValueError("Controlled-U requires a 2x2 target operator.")

    result = zeros(4, 4)

    # Upper 2x2 block: I
    for i in range(2):
        result[i][i] = 1 + 0j

    # Lower 2x2 block: U
    for i in range(2):
        for j in range(2):
            result[i + 2][j + 2] = single_qubit_operator[i][j]

    return result


def demonstrate_controlled_operator() -> None:
    print("\n" + "=" * 78)
    print("12. CONTROLLED UNITARY OPERATOR")
    print("=" * 78)

    cnot = controlled_unitary(X)

    print("\nControlled-X / CNOT:")
    print(format_matrix(cnot))
    print("Unitary:", is_unitary(cnot))

    states = {
        "|00>": basis_state(0, 4),
        "|01>": basis_state(1, 4),
        "|10>": basis_state(2, 4),
        "|11>": basis_state(3, 4),
    }

    for name, state in states.items():
        output = apply_operator(cnot, state)
        print(f"{name} -> {format_vector(output)}")

    print(
        "\nCNOT flips the target only when the control qubit is |1>."
    )


# ---------------------------------------------------------------------------
# 16. Measurement simulation
# ---------------------------------------------------------------------------

def sample_measurement(
    state: Sequence[complex],
    shots: int = 1000,
    rng: random.Random | None = None,
) -> List[int]:
    """
    Sample computational-basis measurement outcomes.

    The function returns integer basis-state indices rather than bit strings.
    """
    if shots <= 0:
        raise ValueError("shots must be positive.")

    normalized = normalize_vector(state)
    probabilities = probability_amplitudes_to_probabilities(normalized)

    total = sum(probabilities)
    probabilities = [p / total for p in probabilities]

    random_source = rng if rng is not None else random.Random()

    outcomes = []
    for _ in range(shots):
        r = random_source.random()
        cumulative = 0.0

        for index, probability in enumerate(probabilities):
            cumulative += probability
            if r < cumulative:
                outcomes.append(index)
                break
        else:
            outcomes.append(len(probabilities) - 1)

    return outcomes


def demonstrate_measurement_sampling() -> None:
    print("\n" + "=" * 78)
    print("13. MEASUREMENT SAMPLING")
    print("=" * 78)

    state = apply_operator(H, basis_state(0, 2))
    outcomes = sample_measurement(
        state,
        shots=10000,
        rng=random.Random(7),
    )

    counts = {
        0: outcomes.count(0),
        1: outcomes.count(1),
    }

    print("\nState H|0>:", format_vector(state))
    print("Theoretical probabilities:", probability_amplitudes_to_probabilities(state))
    print("10,000 simulated measurements:", counts)

    print(
        "\nMeasurement is probabilistic. The unitary operator determines the "
        "state amplitudes, while measurement converts amplitudes into outcomes."
    )


# ---------------------------------------------------------------------------
# 17. Numerical stability and tolerance
# ---------------------------------------------------------------------------

def demonstrate_numerical_tolerance() -> None:
    print("\n" + "=" * 78)
    print("14. NUMERICAL PRECISION")
    print("=" * 78)

    tiny_error = [
        [1 + 1e-14j, 2e-14 + 0j],
        [0j, 1 - 1e-14j],
    ]

    print("\nNearly identity matrix:")
    print(format_matrix(tiny_error))
    print("Exact comparison:", tiny_error == identity_matrix(2))
    print("Tolerance-based comparison:", is_identity(tiny_error, 1e-12))

    print(
        "\nFloating-point calculations rarely produce exact mathematical "
        "equalities. Numerical operator tests should therefore use tolerances."
    )


# ---------------------------------------------------------------------------
# 18. Edge cases and validation
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("15. EDGE CASES AND VALIDATION")
    print("=" * 78)

    cases = []

    try:
        normalize_vector([0j, 0j])
    except ValueError as error:
        cases.append(f"Zero-state normalization rejected: {error}")

    try:
        matrix_multiply([[1 + 0j, 0j]], [[1 + 0j]])
    except ValueError as error:
        cases.append(f"Invalid matrix multiplication rejected: {error}")

    try:
        is_hermitian([[1 + 0j, 2 + 0j]])
    except ValueError as error:
        cases.append(f"Non-square operator rejected: {error}")

    try:
        sample_measurement([1 + 0j, 0j], shots=0)
    except ValueError as error:
        cases.append(f"Invalid shot count rejected: {error}")

    for message in cases:
        print(message)

    print(
        "\nCommon implementation hazards include dimension mismatches, "
        "unnormalized states, exact floating-point comparisons, incorrect "
        "conjugation in inner products, and reversing operator order."
    )


# ---------------------------------------------------------------------------
# 19. A small operator-analysis report
# ---------------------------------------------------------------------------

def operator_report(
    name: str,
    operator: ComplexMatrix,
) -> None:
    print(f"\n{name}")
    print("-" * len(name))
    print(format_matrix(operator))
    print("Shape:", matrix_shape(operator))
    print("Trace:", format_complex(trace(operator)))
    print("Hermitian:", is_hermitian(operator))
    print("Unitary:", is_unitary(operator))
    print("Normal:", is_normal(operator))

    if matrix_shape(operator) == (2, 2):
        eigenvalues = eigenvalues_2x2(operator)
        print(
            "Eigenvalues:",
            ", ".join(format_complex(value) for value in eigenvalues),
        )


def demonstrate_operator_catalogue() -> None:
    print("\n" + "=" * 78)
    print("16. OPERATOR CATALOGUE")
    print("=" * 78)

    operators = [
        ("Identity I", I2),
        ("Pauli X", X),
        ("Pauli Y", Y),
        ("Pauli Z", Z),
        ("Hadamard H", H),
        ("Phase S", phase_gate(math.pi / 2)),
        ("Rotation X(pi/4)", rotation_x(math.pi / 4)),
        ("Rotation Y(pi/4)", rotation_y(math.pi / 4)),
        ("Rotation Z(pi/4)", rotation_z(math.pi / 4)),
    ]

    for name, operator in operators:
        operator_report(name, operator)


# ---------------------------------------------------------------------------
# 20. Production-oriented checklist
# ---------------------------------------------------------------------------

def production_checklist() -> None:
    print("\n" + "=" * 78)
    print("17. IMPLEMENTATION CHECKLIST")
    print("=" * 78)

    checklist = [
        "Use A†, not ordinary transpose Aᵀ, when complex entries are present.",
        "Check Hermiticity with a numerical tolerance.",
        "Check both U†U = I and UU† = I when validating finite matrices.",
        "Preserve state normalization after every intended unitary operation.",
        "Track matrix and vector dimensions explicitly.",
        "Remember that operator composition is order-sensitive.",
        "Use stable matrix-exponential/eigensolver algorithms in production.",
        "Avoid forming large dense tensor-product matrices when scalable methods exist.",
        "Treat measurement as probabilistic rather than as a unitary transformation.",
        "Validate physical constraints before accepting user-supplied operators.",
    ]

    for item in checklist:
        print(" -", item)


# ---------------------------------------------------------------------------
# 21. Main educational program
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("OPERATORS: HERMITIAN AND UNITARY OPERATORS")
    print("=" * 78)
    print(
        "This program develops the subject from matrix fundamentals to "
        "quantum-state evolution and multi-qubit operators."
    )

    demonstrate_basic_properties()
    demonstrate_observables()
    demonstrate_projectors()
    demonstrate_unitary_invariance()
    demonstrate_composition()
    demonstrate_counterexamples()
    demonstrate_eigenvalues()
    demonstrate_matrix_powers()
    demonstrate_time_evolution()
    demonstrate_single_qubit_circuit()
    demonstrate_tensor_products()
    demonstrate_controlled_operator()
    demonstrate_measurement_sampling()
    demonstrate_numerical_tolerance()
    demonstrate_edge_cases()
    demonstrate_operator_catalogue()
    production_checklist()

    print("\n" + "=" * 78)
    print("END OF STUDY PROGRAM")
    print("=" * 78)


if __name__ == "__main__":
    main()
