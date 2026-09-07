"""
Linear Algebra for Quantum Computing
Topic: Vector Spaces and Inner Products

A self-contained study script covering vector spaces and inner products from
absolute beginner concepts through quantum-computing applications.

The script uses only the Python standard library.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence


# =============================================================================
# 1. FOUNDATIONS: SCALARS, VECTORS, AND BASIC OPERATIONS
# =============================================================================

Scalar = complex
Vector = list[complex]
Matrix = list[list[complex]]


def clean_number(value: complex, tolerance: float = 1e-10):
    """Display a complex number cleanly without changing its mathematical value."""
    value = complex(value)
    real = 0.0 if abs(value.real) < tolerance else value.real
    imag = 0.0 if abs(value.imag) < tolerance else value.imag

    if imag == 0:
        return real
    if real == 0:
        return complex(0, imag)
    return complex(real, imag)


def format_complex(value: complex, precision: int = 4) -> str:
    """Return a readable representation of a real or complex number."""
    value = complex(value)
    real = 0 if abs(value.real) < 10 ** (-precision) else value.real
    imag = 0 if abs(value.imag) < 10 ** (-precision) else value.imag

    if imag == 0:
        return f"{real:.{precision}g}"
    if real == 0:
        return f"{imag:.{precision}g}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.{precision}g}{sign}{abs(imag):.{precision}g}i"


def format_vector(vector: Sequence[complex], precision: int = 4) -> str:
    return "(" + ", ".join(format_complex(x, precision) for x in vector) + ")"


def format_matrix(matrix: Matrix, precision: int = 4) -> str:
    rows = []
    for row in matrix:
        rows.append(
            "[" + ", ".join(format_complex(x, precision) for x in row) + "]"
        )
    return "[\n  " + ",\n  ".join(rows) + "\n]"


def is_close(a: complex, b: complex, tolerance: float = 1e-10) -> bool:
    return abs(a - b) <= tolerance


def vectors_equal(
    first: Sequence[complex],
    second: Sequence[complex],
    tolerance: float = 1e-10,
) -> bool:
    return (
        len(first) == len(second)
        and all(is_close(a, b, tolerance) for a, b in zip(first, second))
    )


def vector_add(first: Sequence[complex], second: Sequence[complex]) -> Vector:
    """Vector addition: (u + v)_i = u_i + v_i."""
    if len(first) != len(second):
        raise ValueError("Vectors must have the same dimension.")
    return [a + b for a, b in zip(first, second)]


def vector_subtract(first: Sequence[complex], second: Sequence[complex]) -> Vector:
    """Vector subtraction: (u - v)_i = u_i - v_i."""
    if len(first) != len(second):
        raise ValueError("Vectors must have the same dimension.")
    return [a - b for a, b in zip(first, second)]


def scalar_multiply(scalar: complex, vector: Sequence[complex]) -> Vector:
    """Scalar multiplication: c|v>."""
    return [scalar * value for value in vector]


def dot_product_real(
    first: Sequence[complex],
    second: Sequence[complex],
) -> complex:
    """
    Algebraic dot product without conjugation.

    This is suitable for real vectors when complex conjugation is unnecessary.
    It is NOT the standard complex inner product.
    """
    if len(first) != len(second):
        raise ValueError("Vectors must have the same dimension.")
    return sum(a * b for a, b in zip(first, second))


def vector_norm(vector: Sequence[complex]) -> float:
    """
    Euclidean/Hilbert-space norm induced by the complex inner product.

    ||v|| = sqrt(<v|v>) = sqrt(sum_i conjugate(v_i) * v_i)
    """
    return math.sqrt(sum(abs(value) ** 2 for value in vector))


def normalize(vector: Sequence[complex], tolerance: float = 1e-12) -> Vector:
    """Return a unit vector in the same direction."""
    norm = vector_norm(vector)
    if norm <= tolerance:
        raise ValueError("The zero vector cannot be normalized.")
    return [value / norm for value in vector]


# =============================================================================
# 2. VECTOR SPACES
# =============================================================================

def demonstrate_vector_space_axioms():
    """
    Demonstrate the main vector-space operations computationally.

    A vector space over a field F is a set V equipped with vector addition and
    scalar multiplication satisfying closure, associativity, commutativity of
    addition, additive identity, additive inverses, and compatibility with
    scalar multiplication.
    """
    u = [1, 2, 3]
    v = [4, 5, 6]
    w = [-1, 2, 4]

    a = 2
    b = -3

    print("u =", u)
    print("v =", v)
    print("w =", w)

    print("u + v =", vector_add(u, v))
    print("a*u =", scalar_multiply(a, u))

    # Associativity of vector addition:
    left = vector_add(vector_add(u, v), w)
    right = vector_add(u, vector_add(v, w))
    print("(u + v) + w == u + (v + w):", left == right)

    # Commutativity:
    print("u + v == v + u:", vector_add(u, v) == vector_add(v, u))

    # Additive identity:
    zero = [0, 0, 0]
    print("u + 0 == u:", vector_add(u, zero) == u)

    # Additive inverse:
    negative_u = scalar_multiply(-1, u)
    print("u + (-u) == 0:", vector_add(u, negative_u) == zero)

    # Distributivity:
    left = scalar_multiply(a, vector_add(u, v))
    right = vector_add(scalar_multiply(a, u), scalar_multiply(a, v))
    print("a(u + v) == au + av:", left == right)

    # Scalar distributivity:
    left = scalar_multiply(a + b, u)
    right = vector_add(scalar_multiply(a, u), scalar_multiply(b, u))
    print("(a + b)u == au + bu:", left == right)

    # Compatibility of scalar multiplication:
    left = scalar_multiply(a * b, u)
    right = scalar_multiply(a, scalar_multiply(b, u))
    print("(ab)u == a(bu):", left == right)


# =============================================================================
# 3. SUBSPACES
# =============================================================================

def is_subspace(
    vectors: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> bool:
    """
    Basic practical subspace test for a finite list of vectors.

    A finite set of vectors is not itself necessarily a subspace. Its span is
    always a subspace. This function checks whether the supplied finite set is
    closed under the simple operations represented by the given sample points,
    so it is mainly educational rather than a general symbolic proof engine.
    """
    if not vectors:
        return True

    dimension = len(vectors[0])
    if any(len(v) != dimension for v in vectors):
        return False

    # A finite nonzero vector collection is generally not a subspace because
    # scalar multiplication creates infinitely many vectors.
    return all(vectors_equal(v, [0] * dimension, tolerance) for v in vectors)


def span(vectors: Sequence[Sequence[complex]]) -> list[Vector]:
    """
    Return a simple list of vectors demonstrating linear combinations.

    For a complete span, infinitely many combinations are possible. This
    function samples coefficients to make the concept executable.
    """
    if not vectors:
        return [[]]

    coefficient_choices = [-1, 0, 1]
    results: list[Vector] = []

    def recurse(index: int, current: Vector):
        if index == len(vectors):
            results.append(current)
            return

        for coefficient in coefficient_choices:
            contribution = scalar_multiply(coefficient, vectors[index])
            recurse(index + 1, vector_add(current, contribution))

    recurse(0, [0] * len(vectors[0]))

    unique: list[Vector] = []
    for value in results:
        if not any(vectors_equal(value, existing) for existing in unique):
            unique.append(value)

    return unique


# =============================================================================
# 4. LINEAR COMBINATIONS, INDEPENDENCE, BASIS, AND DIMENSION
# =============================================================================

def matrix_shape(matrix: Matrix) -> tuple[int, int]:
    if not matrix:
        return 0, 0

    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal lengths.")

    return len(matrix), columns


def rref(matrix: Matrix, tolerance: float = 1e-12) -> Matrix:
    """
    Compute reduced row-echelon form using Gaussian-Jordan elimination.
    """
    result = [list(map(complex, row)) for row in matrix]
    rows, columns = matrix_shape(result)

    pivot_row = 0

    for pivot_column in range(columns):
        if pivot_row >= rows:
            break

        best_row = max(
            range(pivot_row, rows),
            key=lambda r: abs(result[r][pivot_column]),
        )

        if abs(result[best_row][pivot_column]) <= tolerance:
            continue

        result[pivot_row], result[best_row] = result[best_row], result[pivot_row]

        pivot = result[pivot_row][pivot_column]
        result[pivot_row] = [
            value / pivot for value in result[pivot_row]
        ]

        for row in range(rows):
            if row == pivot_row:
                continue

            factor = result[row][pivot_column]
            if abs(factor) > tolerance:
                result[row] = [
                    current - factor * pivot_value
                    for current, pivot_value in zip(
                        result[row],
                        result[pivot_row],
                    )
                ]

        pivot_row += 1

    return [
        [0 if abs(value) <= tolerance else value for value in row]
        for row in result
    ]


def rank(matrix: Matrix, tolerance: float = 1e-12) -> int:
    """Rank is the number of pivot rows in RREF."""
    reduced = rref(matrix, tolerance)
    return sum(
        any(abs(value) > tolerance for value in row)
        for row in reduced
    )


def vectors_as_columns(vectors: Sequence[Sequence[complex]]) -> Matrix:
    if not vectors:
        return []

    dimension = len(vectors[0])
    if any(len(v) != dimension for v in vectors):
        raise ValueError("All vectors must have the same dimension.")

    return [
        [vectors[column][row] for column in range(len(vectors))]
        for row in range(dimension)
    ]


def is_linearly_independent(
    vectors: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> bool:
    if not vectors:
        return True

    matrix = vectors_as_columns(vectors)
    return rank(matrix, tolerance) == len(vectors)


def solve_linear_system(
    matrix: Matrix,
    right_side: Sequence[complex],
    tolerance: float = 1e-10,
) -> Vector:
    """
    Solve a square linear system Ax=b when a unique solution exists.
    """
    rows, columns = matrix_shape(matrix)
    if rows != columns:
        raise ValueError("This educational solver requires a square matrix.")

    if len(right_side) != rows:
        raise ValueError("Right-hand side has incompatible dimension.")

    augmented = [
        list(map(complex, matrix[row])) + [complex(right_side[row])]
        for row in range(rows)
    ]

    reduced = rref(augmented, tolerance)

    for row in reduced:
        coefficient_part = row[:columns]
        if all(abs(value) <= tolerance for value in coefficient_part):
            if abs(row[-1]) > tolerance:
                raise ValueError("The system is inconsistent.")

    if rank(matrix, tolerance) < columns:
        raise ValueError("The system does not have a unique solution.")

    return [reduced[i][-1] for i in range(columns)]


def coordinates_in_basis(
    vector: Sequence[complex],
    basis: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> Vector:
    """Find coefficients c such that vector = sum_i c_i basis_i."""
    if len(basis) != len(vector):
        raise ValueError(
            "This function expects a basis with as many vectors as dimensions."
        )

    matrix = vectors_as_columns(basis)
    return solve_linear_system(matrix, vector, tolerance)


# =============================================================================
# 5. REAL AND COMPLEX VECTOR SPACES
# =============================================================================

def demonstrate_real_and_complex_vectors():
    real_vector = [1, 2, 3]
    complex_vector = [1 + 2j, -2j, 3 - 1j]

    print("Real vector:", real_vector)
    print("Complex vector:", complex_vector)
    print("2 * real vector:", scalar_multiply(2, real_vector))
    print("(1+i) * complex vector:", scalar_multiply(1 + 1j, complex_vector))

    # Quantum states use complex vector spaces such as C^2 and C^(2^n).
    print("Norm of complex vector:", vector_norm(complex_vector))
    print("Normalized complex vector:", normalize(complex_vector))


# =============================================================================
# 6. BRA-KET NOTATION
# =============================================================================

def ket(vector: Sequence[complex]) -> Vector:
    """Represent a column vector |v> as a Python list."""
    return list(map(complex, vector))


def bra(vector: Sequence[complex]) -> Vector:
    """
    Represent <v|, the conjugate transpose of |v|, as a one-dimensional
    Python sequence containing conjugated entries.
    """
    return [complex(value).conjugate() for value in vector]


def bra_ket_inner_product(
    bra_vector: Sequence[complex],
    ket_vector: Sequence[complex],
) -> complex:
    """
    Compute <u|v> = sum_i conjugate(u_i) v_i.
    """
    if len(bra_vector) != len(ket_vector):
        raise ValueError("Vectors must have the same dimension.")

    return sum(
        complex(u).conjugate() * complex(v)
        for u, v in zip(bra_vector, ket_vector)
    )


def ket_bra_outer_product(
    ket_vector: Sequence[complex],
    bra_vector: Sequence[complex],
) -> Matrix:
    """
    Compute |u><v|.

    Entry (i,j) is u_i * conjugate(v_j).
    """
    return [
        [
            complex(u) * complex(v).conjugate()
            for v in bra_vector
        ]
        for u in ket_vector
    ]


def demonstrate_bra_ket():
    psi = ket([1, 1j])
    phi = ket([2, -1j])

    print("|psi> =", format_vector(psi))
    print("<psi| =", format_vector(bra(psi)))
    print("<psi|phi> =", format_complex(bra_ket_inner_product(psi, phi)))
    print("|psi><phi| =")
    print(format_matrix(ket_bra_outer_product(psi, phi)))


# =============================================================================
# 7. INNER PRODUCTS
# =============================================================================

def complex_inner_product(
    first: Sequence[complex],
    second: Sequence[complex],
) -> complex:
    """
    Standard finite-dimensional complex inner product.

    Mathematical convention:
        <u, v> = sum_i conjugate(u_i) v_i

    The first argument is conjugate-linear and the second argument is linear.
    """
    return bra_ket_inner_product(first, second)


def demonstrate_inner_product_axioms():
    u = [1 + 1j, 2 - 1j]
    v = [3 - 2j, -1 + 4j]
    w = [2 + 3j, 5 - 2j]

    a = 2 - 1j
    b = -1 + 2j

    print("<u,v> =", format_complex(complex_inner_product(u, v)))

    # Conjugate symmetry:
    left = complex_inner_product(u, v)
    right = complex_inner_product(v, u).conjugate()
    print("Conjugate symmetry:", is_close(left, right))

    # Linearity in the second argument:
    left = complex_inner_product(u, vector_add(v, w))
    right = complex_inner_product(u, v) + complex_inner_product(u, w)
    print("Linearity in second argument:", is_close(left, right))

    # Conjugate-linearity in the first argument:
    left = complex_inner_product(scalar_multiply(a, u), v)
    right = a.conjugate() * complex_inner_product(u, v)
    print("Conjugate-linearity in first argument:", is_close(left, right))

    # Positive definiteness:
    print("<u,u> =", format_complex(complex_inner_product(u, u)))
    print("||u||^2 =", vector_norm(u) ** 2)


def gram_matrix(
    vectors: Sequence[Sequence[complex]],
) -> Matrix:
    """
    Construct the Gram matrix G_ij = <v_i, v_j>.
    """
    return [
        [
            complex_inner_product(vectors[i], vectors[j])
            for j in range(len(vectors))
        ]
        for i in range(len(vectors))
    ]


# =============================================================================
# 8. NORM, DISTANCE, ANGLES, AND ORTHOGONALITY
# =============================================================================

def distance(
    first: Sequence[complex],
    second: Sequence[complex],
) -> float:
    """Distance induced by the inner product: ||u-v||."""
    return vector_norm(vector_subtract(first, second))


def are_orthogonal(
    first: Sequence[complex],
    second: Sequence[complex],
    tolerance: float = 1e-10,
) -> bool:
    """Two vectors are orthogonal when <u,v> = 0."""
    return abs(complex_inner_product(first, second)) <= tolerance


def complex_angle(
    first: Sequence[complex],
    second: Sequence[complex],
) -> float:
    """
    A useful angle-like quantity based on the magnitude of the inner product.

    cos(theta) = |<u,v>| / (||u|| ||v||)

    The phase of a complex inner product means that complex vectors do not have
    exactly the same geometric angle interpretation as real vectors.
    """
    norm_product = vector_norm(first) * vector_norm(second)

    if norm_product == 0:
        raise ValueError("The angle is undefined for the zero vector.")

    cosine = abs(complex_inner_product(first, second)) / norm_product
    cosine = max(-1.0, min(1.0, cosine))
    return math.acos(cosine)


def demonstrate_geometry():
    u = [1, 0]
    v = [0, 1]
    w = [1, 1]

    print("||u|| =", vector_norm(u))
    print("||w|| =", vector_norm(w))
    print("distance(u,w) =", distance(u, w))
    print("u orthogonal to v:", are_orthogonal(u, v))
    print("angle(u,w) in degrees:", math.degrees(complex_angle(u, w)))


# =============================================================================
# 9. CAUCHY-SCHWARZ AND TRIANGLE INEQUALITY
# =============================================================================

def demonstrate_inequalities():
    vectors = [
        ([1 + 1j, 2], [3 - 1j, -2j]),
        ([1, 0, 2], [2, 3, -1]),
    ]

    for u, v in vectors:
        inner = abs(complex_inner_product(u, v))
        bound = vector_norm(u) * vector_norm(v)

        print("|<u,v>| =", inner)
        print("||u|| ||v|| =", bound)
        print("Cauchy-Schwarz holds:", inner <= bound + 1e-10)

    u = [1, 2]
    v = [-3, 4]

    left = vector_norm(vector_add(u, v))
    right = vector_norm(u) + vector_norm(v)

    print("Triangle inequality:", left <= right + 1e-10)


# =============================================================================
# 10. ORTHONORMAL VECTORS AND ORTHONORMAL BASES
# =============================================================================

def is_orthonormal_set(
    vectors: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> bool:
    for i, first in enumerate(vectors):
        for j, second in enumerate(vectors):
            expected = 1 if i == j else 0
            if abs(complex_inner_product(first, second) - expected) > tolerance:
                return False
    return True


def computational_basis(num_qubits: int) -> list[Vector]:
    """
    Construct the computational basis for n qubits.

    Dimension = 2^n.
    """
    if num_qubits < 0:
        raise ValueError("Number of qubits cannot be negative.")

    dimension = 2 ** num_qubits
    basis = []

    for position in range(dimension):
        vector = [0j] * dimension
        vector[position] = 1 + 0j
        basis.append(vector)

    return basis


def demonstrate_orthonormal_basis():
    basis = computational_basis(2)

    print("Two-qubit computational basis:")
    for index, vector in enumerate(basis):
        print(f"|{index:02b}> =", format_vector(vector))

    print("Orthonormal:", is_orthonormal_set(basis))


# =============================================================================
# 11. PROJECTION
# =============================================================================

def project_onto_vector(
    vector: Sequence[complex],
    direction: Sequence[complex],
    tolerance: float = 1e-12,
) -> Vector:
    """
    Orthogonal projection onto span{direction}.

    proj_direction(v)
      = (<direction,v> / <direction,direction>) direction
    """
    denominator = complex_inner_product(direction, direction)

    if abs(denominator) <= tolerance:
        raise ValueError("Cannot project onto the zero vector.")

    coefficient = complex_inner_product(direction, vector) / denominator
    return scalar_multiply(coefficient, direction)


def demonstrate_projection():
    vector = [2, 3]
    direction = [1, 1]

    projection = project_onto_vector(vector, direction)
    residual = vector_subtract(vector, projection)

    print("v =", vector)
    print("direction =", direction)
    print("projection =", projection)
    print("residual =", residual)
    print("Residual orthogonal to direction:", are_orthogonal(residual, direction))


# =============================================================================
# 12. GRAM-SCHMIDT ORTHONORMALIZATION
# =============================================================================

def gram_schmidt(
    vectors: Sequence[Sequence[complex]],
    tolerance: float = 1e-12,
) -> list[Vector]:
    """
    Orthonormalize linearly independent vectors using Gram-Schmidt.

    Important numerical note:
    Classical Gram-Schmidt can lose orthogonality in finite precision.
    Modified Gram-Schmidt is generally more numerically stable.
    """
    orthonormal: list[Vector] = []

    for original in vectors:
        vector = list(map(complex, original))

        for basis_vector in orthonormal:
            coefficient = complex_inner_product(basis_vector, vector)
            projection = scalar_multiply(coefficient, basis_vector)
            vector = vector_subtract(vector, projection)

        norm = vector_norm(vector)

        if norm <= tolerance:
            raise ValueError(
                "Input vectors are linearly dependent or numerically dependent."
            )

        orthonormal.append(normalize(vector))

    return orthonormal


def modified_gram_schmidt(
    vectors: Sequence[Sequence[complex]],
    tolerance: float = 1e-12,
) -> list[Vector]:
    """
    Modified Gram-Schmidt implementation.

    Each vector is progressively orthogonalized against already-normalized
    vectors. It is preferable to classical Gram-Schmidt for numerical work.
    """
    working = [list(map(complex, vector)) for vector in vectors]
    orthonormal: list[Vector] = []

    for i in range(len(working)):
        norm = vector_norm(working[i])

        if norm <= tolerance:
            raise ValueError(
                "Input vectors are linearly dependent or numerically dependent."
            )

        q = scalar_multiply(1 / norm, working[i])
        orthonormal.append(q)

        for j in range(i + 1, len(working)):
            coefficient = complex_inner_product(q, working[j])
            working[j] = vector_subtract(
                working[j],
                scalar_multiply(coefficient, q),
            )

    return orthonormal


# =============================================================================
# 13. QUANTUM STATES AS UNIT VECTORS
# =============================================================================

@dataclass
class QuantumState:
    """
    A normalized state vector in a finite-dimensional complex Hilbert space.

    The state vector must satisfy:
        <psi|psi> = 1
    """
    amplitudes: Vector

    def __post_init__(self):
        self.amplitudes = [complex(x) for x in self.amplitudes]

        if not self.amplitudes:
            raise ValueError("A quantum state cannot have zero dimension.")

        norm = vector_norm(self.amplitudes)

        if abs(norm - 1.0) > 1e-10:
            raise ValueError(
                f"Quantum state must be normalized; received norm {norm}."
            )

    @classmethod
    def from_amplitudes(cls, amplitudes: Sequence[complex]) -> "QuantumState":
        """Normalize arbitrary nonzero amplitudes into a valid state."""
        return cls(normalize(amplitudes))

    @property
    def dimension(self) -> int:
        return len(self.amplitudes)

    def inner_product(self, other: "QuantumState") -> complex:
        return complex_inner_product(self.amplitudes, other.amplitudes)

    def overlap_probability(self, other: "QuantumState") -> float:
        """
        Probability of projecting |self> onto |other>.

        P = |<other|self>|^2.
        """
        return abs(other.inner_product(self)) ** 2

    def global_phase_equivalent(
        self,
        other: "QuantumState",
        tolerance: float = 1e-10,
    ) -> bool:
        """
        Check whether two states differ only by a global phase.

        |phi> = exp(i theta)|psi>

        Such states represent the same physical pure state.
        """
        if self.dimension != other.dimension:
            return False

        nonzero_index = None
        for index, value in enumerate(self.amplitudes):
            if abs(value) > tolerance:
                nonzero_index = index
                break

        if nonzero_index is None:
            return False

        phase = other.amplitudes[nonzero_index] / self.amplitudes[nonzero_index]

        if abs(abs(phase) - 1) > tolerance:
            return False

        for a, b in zip(self.amplitudes, other.amplitudes):
            if abs(b - phase * a) > tolerance:
                return False

        return True


def qubit_zero() -> QuantumState:
    return QuantumState([1, 0])


def qubit_one() -> QuantumState:
    return QuantumState([0, 1])


def plus_state() -> QuantumState:
    return QuantumState.from_amplitudes([1, 1])


def minus_state() -> QuantumState:
    return QuantumState.from_amplitudes([1, -1])


def demonstrate_quantum_states():
    zero = qubit_zero()
    one = qubit_one()
    plus = plus_state()

    print("|0> =", format_vector(zero.amplitudes))
    print("|1> =", format_vector(one.amplitudes))
    print("|+> =", format_vector(plus.amplitudes))

    print("<0|1> =", format_complex(zero.inner_product(one)))
    print("|<0|+>|^2 =", zero.overlap_probability(plus))
    print("|<1|+>|^2 =", one.overlap_probability(plus))

    # A global phase does not change a physical pure state.
    phase_shifted_plus = QuantumState.from_amplitudes([1j, 1j])
    print(
        "|+> and i|+> are physically equivalent:",
        plus.global_phase_equivalent(phase_shifted_plus),
    )


# =============================================================================
# 14. MEASUREMENT PROBABILITIES FROM INNER PRODUCTS
# =============================================================================

def computational_measurement_probabilities(
    state: QuantumState,
) -> list[float]:
    """
    In the computational basis, probability of outcome i is |alpha_i|^2.
    """
    probabilities = [abs(amplitude) ** 2 for amplitude in state.amplitudes]

    # Small floating-point deviations can cause a sum such as 1.0000000000000002.
    total = sum(probabilities)

    if abs(total - 1.0) > 1e-9:
        raise ValueError("State is not normalized.")

    return probabilities


def sample_measurement(
    state: QuantumState,
    shots: int = 1000,
    seed: int | None = 7,
) -> dict[int, int]:
    """Sample computational-basis measurements using Python's random module."""
    if shots <= 0:
        raise ValueError("shots must be positive.")

    rng = random.Random(seed)
    probabilities = computational_measurement_probabilities(state)

    counts = {index: 0 for index in range(state.dimension)}

    for _ in range(shots):
        sample = rng.random()
        cumulative = 0.0

        for index, probability in enumerate(probabilities):
            cumulative += probability
            if sample < cumulative:
                counts[index] += 1
                break

    return counts


def demonstrate_measurement():
    state = plus_state()

    print("State |+> probabilities:")
    print(computational_measurement_probabilities(state))

    counts = sample_measurement(state, shots=1000, seed=42)
    print("1000 simulated measurements:", counts)


# =============================================================================
# 15. CHANGE OF BASIS
# =============================================================================

def matrix_vector_multiply(
    matrix: Matrix,
    vector: Sequence[complex],
) -> Vector:
    rows, columns = matrix_shape(matrix)

    if columns != len(vector):
        raise ValueError("Matrix and vector dimensions are incompatible.")

    return [
        sum(matrix[row][column] * vector[column] for column in range(columns))
        for row in range(rows)
    ]


def matrix_multiply(first: Matrix, second: Matrix) -> Matrix:
    rows_a, columns_a = matrix_shape(first)
    rows_b, columns_b = matrix_shape(second)

    if columns_a != rows_b:
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        [
            sum(
                first[i][k] * second[k][j]
                for k in range(columns_a)
            )
            for j in range(columns_b)
        ]
        for i in range(rows_a)
    ]


def conjugate_transpose(matrix: Matrix) -> Matrix:
    rows, columns = matrix_shape(matrix)

    return [
        [
            matrix[row][column].conjugate()
            for row in range(rows)
        ]
        for column in range(columns)
    ]


def identity_matrix(size: int) -> Matrix:
    if size < 0:
        raise ValueError("Matrix size cannot be negative.")

    return [
        [1 if row == column else 0 for column in range(size)]
        for row in range(size)
    ]


def matrix_is_close(
    first: Matrix,
    second: Matrix,
    tolerance: float = 1e-10,
) -> bool:
    if matrix_shape(first) != matrix_shape(second):
        return False

    return all(
        is_close(a, b, tolerance)
        for row_a, row_b in zip(first, second)
        for a, b in zip(row_a, row_b)
    )


def basis_change_coordinates(
    vector: Sequence[complex],
    orthonormal_basis: Sequence[Sequence[complex]],
) -> Vector:
    """
    For an orthonormal basis {q_i}:

        c_i = <q_i|v>

    and

        |v> = sum_i c_i |q_i>.
    """
    if len(orthonormal_basis) != len(vector):
        raise ValueError("Basis must have one vector per dimension.")

    if not is_orthonormal_set(orthonormal_basis):
        raise ValueError("Basis must be orthonormal.")

    return [
        complex_inner_product(basis_vector, vector)
        for basis_vector in orthonormal_basis
    ]


def reconstruct_from_orthonormal_basis(
    coordinates: Sequence[complex],
    basis: Sequence[Sequence[complex]],
) -> Vector:
    if len(coordinates) != len(basis):
        raise ValueError("Coordinate count must equal basis-vector count.")

    result = [0j] * len(basis[0])

    for coefficient, basis_vector in zip(coordinates, basis):
        result = vector_add(
            result,
            scalar_multiply(coefficient, basis_vector),
        )

    return result


def demonstrate_change_of_basis():
    h = 1 / math.sqrt(2)

    hadamard_basis = [
        [h, h],
        [h, -h],
    ]

    vector = [1, 0]

    coordinates = basis_change_coordinates(vector, hadamard_basis)
    reconstructed = reconstruct_from_orthonormal_basis(
        coordinates,
        hadamard_basis,
    )

    print("Vector in computational coordinates:", vector)
    print("Coordinates in {|+>, |->} basis:", format_vector(coordinates))
    print("Reconstructed vector:", format_vector(reconstructed))


# =============================================================================
# 16. PROJECTIONS ONTO SUBSPACES
# =============================================================================

def project_onto_orthonormal_basis(
    vector: Sequence[complex],
    orthonormal_basis: Sequence[Sequence[complex]],
) -> Vector:
    """
    Projection onto span{q_1,...,q_k} for an orthonormal set:

        P|v> = sum_i |q_i><q_i|v>
    """
    if not is_orthonormal_set(orthonormal_basis):
        raise ValueError("The supplied vectors must be orthonormal.")

    result = [0j] * len(vector)

    for basis_vector in orthonormal_basis:
        coefficient = complex_inner_product(basis_vector, vector)
        result = vector_add(
            result,
            scalar_multiply(coefficient, basis_vector),
        )

    return result


def demonstrate_subspace_projection():
    q1 = normalize([1, 1, 0])
    q2 = normalize([1, -1, 0])

    vector = [1, 2, 3]

    projection = project_onto_orthonormal_basis(
        vector,
        [q1, q2],
    )

    residual = vector_subtract(vector, projection)

    print("v =", vector)
    print("Projection onto xy-plane =", format_vector(projection))
    print("Residual =", format_vector(residual))
    print("Residual orthogonal to q1:", are_orthogonal(residual, q1))
    print("Residual orthogonal to q2:", are_orthogonal(residual, q2))


# =============================================================================
# 17. TENSOR PRODUCTS
# =============================================================================

def tensor_product(
    first: Sequence[complex],
    second: Sequence[complex],
) -> Vector:
    """
    Kronecker/tensor product of two vectors.

    If |a> has dimension m and |b> has dimension n,
    |a> tensor |b> has dimension mn.
    """
    return [
        a * b
        for a in first
        for b in second
    ]


def demonstrate_tensor_products():
    zero = qubit_zero().amplitudes
    one = qubit_one().amplitudes
    plus = plus_state().amplitudes

    zero_one = tensor_product(zero, one)
    plus_zero = tensor_product(plus, zero)

    print("|0> tensor |1> =", format_vector(zero_one))
    print("|+> tensor |0> =", format_vector(plus_zero))
    print("Dimension of two-qubit state:", len(zero_one))

    # Inner products factorize:
    left = complex_inner_product(
        tensor_product(plus, zero),
        tensor_product(one, one),
    )
    right = (
        complex_inner_product(plus, one)
        * complex_inner_product(zero, one)
    )

    print("Tensor-product inner-product identity:", is_close(left, right))


# =============================================================================
# 18. SEPARABLE AND ENTANGLED TWO-QUBIT STATES
# =============================================================================

def bell_phi_plus() -> QuantumState:
    """
    |Phi+> = (|00> + |11>) / sqrt(2)
    """
    h = 1 / math.sqrt(2)
    return QuantumState([h, 0, 0, h])


def is_product_two_qubit_state(
    state: QuantumState,
    tolerance: float = 1e-10,
) -> bool:
    """
    For a two-qubit pure state with amplitudes [a,b,c,d], separability requires

        a*d - b*c = 0

    up to numerical tolerance.
    """
    if state.dimension != 4:
        raise ValueError("This function is for two-qubit states.")

    a, b, c, d = state.amplitudes
    return abs(a * d - b * c) <= tolerance


def demonstrate_entanglement():
    product_state = QuantumState(
        tensor_product(plus_state().amplitudes, qubit_zero().amplitudes)
    )

    entangled_state = bell_phi_plus()

    print(
        "|+>|0> is a product state:",
        is_product_two_qubit_state(product_state),
    )

    print(
        "|Phi+> is a product state:",
        is_product_two_qubit_state(entangled_state),
    )


# =============================================================================
# 19. MATRICES AS LINEAR OPERATORS
# =============================================================================

def apply_operator(
    operator: Matrix,
    state: QuantumState,
) -> QuantumState:
    result = matrix_vector_multiply(operator, state.amplitudes)
    return QuantumState.from_amplitudes(result)


def pauli_x() -> Matrix:
    return [
        [0, 1],
        [1, 0],
    ]


def pauli_y() -> Matrix:
    return [
        [0, -1j],
        [1j, 0],
    ]


def pauli_z() -> Matrix:
    return [
        [1, 0],
        [0, -1],
    ]


def hadamard() -> Matrix:
    h = 1 / math.sqrt(2)
    return [
        [h, h],
        [h, -h],
    ]


def demonstrate_linear_operators():
    zero = qubit_zero()

    x_zero = apply_operator(pauli_x(), zero)
    z_zero = apply_operator(pauli_z(), zero)
    h_zero = apply_operator(hadamard(), zero)

    print("X|0> =", format_vector(x_zero.amplitudes))
    print("Z|0> =", format_vector(z_zero.amplitudes))
    print("H|0> =", format_vector(h_zero.amplitudes))


# =============================================================================
# 20. ADJOINT, HERMITIAN MATRICES, AND UNITARY MATRICES
# =============================================================================

def is_hermitian(
    matrix: Matrix,
    tolerance: float = 1e-10,
) -> bool:
    return matrix_is_close(
        matrix,
        conjugate_transpose(matrix),
        tolerance,
    )


def is_unitary(
    matrix: Matrix,
    tolerance: float = 1e-10,
) -> bool:
    rows, columns = matrix_shape(matrix)

    if rows != columns:
        return False

    adjoint = conjugate_transpose(matrix)
    product = matrix_multiply(adjoint, matrix)

    return matrix_is_close(
        product,
        identity_matrix(rows),
        tolerance,
    )


def demonstrate_operators():
    operators = {
        "Pauli X": pauli_x(),
        "Pauli Y": pauli_y(),
        "Pauli Z": pauli_z(),
        "Hadamard": hadamard(),
    }

    for name, operator in operators.items():
        print(name)
        print(format_matrix(operator))
        print("Hermitian:", is_hermitian(operator))
        print("Unitary:", is_unitary(operator))


# =============================================================================
# 21. ORTHOGONALITY PRESERVATION UNDER UNITARY OPERATORS
# =============================================================================

def demonstrate_unitary_geometry():
    u = normalize([1, 2j])
    v = normalize([2, -1j])

    h = hadamard()

    hu = matrix_vector_multiply(h, u)
    hv = matrix_vector_multiply(h, v)

    original_norm_u = vector_norm(u)
    transformed_norm_u = vector_norm(hu)

    original_inner = complex_inner_product(u, v)
    transformed_inner = complex_inner_product(hu, hv)

    print("Original ||u||:", original_norm_u)
    print("Transformed ||Hu||:", transformed_norm_u)
    print(
        "Norm preserved:",
        is_close(original_norm_u, transformed_norm_u),
    )

    print(
        "Inner product preserved:",
        is_close(original_inner, transformed_inner),
    )


# =============================================================================
# 22. EIGENVECTORS OF THE PAULI AND HADAMARD OPERATORS
# =============================================================================

def eigenvector_check(
    operator: Matrix,
    vector: Sequence[complex],
    eigenvalue: complex,
    tolerance: float = 1e-10,
) -> bool:
    left = matrix_vector_multiply(operator, vector)
    right = scalar_multiply(eigenvalue, vector)
    return vectors_equal(left, right, tolerance)


def demonstrate_eigenvectors():
    x = pauli_x()
    z = pauli_z()
    h = hadamard()

    plus = plus_state().amplitudes
    minus = minus_state().amplitudes

    print("X|+> = +|+>:", eigenvector_check(x, plus, 1))
    print("X|-> = -|->:", eigenvector_check(x, minus, -1))

    print("Z|0> = +|0>:", eigenvector_check(z, [1, 0], 1))
    print("Z|1> = -|1>:", eigenvector_check(z, [0, 1], -1))

    h_plus = h
    print("Hadamard matrix squared is identity:")
    print(
        matrix_is_close(
            matrix_multiply(h_plus, h_plus),
            identity_matrix(2),
        )
    )


# =============================================================================
# 23. EXPECTATION VALUES
# =============================================================================

def expectation_value(
    state: QuantumState,
    operator: Matrix,
) -> complex:
    """
    Expectation value:

        <A> = <psi|A|psi>

    For a Hermitian observable, the result is real up to floating-point error.
    """
    transformed = matrix_vector_multiply(
        operator,
        state.amplitudes,
    )

    return complex_inner_product(
        state.amplitudes,
        transformed,
    )


def demonstrate_expectation_values():
    zero = qubit_zero()
    plus = plus_state()

    for state_name, state in [("|0>", zero), ("|+>", plus)]:
        print(state_name, "expectation of X:")
        print(format_complex(expectation_value(state, pauli_x())))

        print(state_name, "expectation of Z:")
        print(format_complex(expectation_value(state, pauli_z())))


# =============================================================================
# 24. VARIANCE OF AN OBSERVABLE
# =============================================================================

def matrix_subtract(first: Matrix, second: Matrix) -> Matrix:
    if matrix_shape(first) != matrix_shape(second):
        raise ValueError("Matrices must have the same dimensions.")

    return [
        [a - b for a, b in zip(row_a, row_b)]
        for row_a, row_b in zip(first, second)
    ]


def matrix_scalar_multiply(
    scalar: complex,
    matrix: Matrix,
) -> Matrix:
    return [
        [scalar * value for value in row]
        for row in matrix
    ]


def matrix_power(matrix: Matrix, exponent: int) -> Matrix:
    if exponent < 0:
        raise ValueError("This implementation supports nonnegative powers.")

    size, columns = matrix_shape(matrix)

    if size != columns:
        raise ValueError("Matrix must be square.")

    result = identity_matrix(size)
    base = [row[:] for row in matrix]

    while exponent:
        if exponent % 2 == 1:
            result = matrix_multiply(result, base)

        base = matrix_multiply(base, base)
        exponent //= 2

    return result


def observable_variance(
    state: QuantumState,
    observable: Matrix,
) -> float:
    mean = expectation_value(state, observable)
    mean_square = expectation_value(
        state,
        matrix_power(observable, 2),
    )

    variance = (mean_square - mean * mean).real

    if variance < 0 and abs(variance) < 1e-10:
        variance = 0

    return variance


def demonstrate_variance():
    zero = qubit_zero()
    plus = plus_state()

    print("Variance of Z for |0>:", observable_variance(zero, pauli_z()))
    print("Variance of Z for |+>:", observable_variance(plus, pauli_z()))


# =============================================================================
# 25. PROJECTORS AND BORN'S RULE
# =============================================================================

def projector(
    state: QuantumState,
) -> Matrix:
    """
    Rank-one projector P = |psi><psi|.
    """
    return ket_bra_outer_product(
        state.amplitudes,
        state.amplitudes,
    )


def demonstrate_projector():
    plus = plus_state()
    p_plus = projector(plus)

    print("Projector |+><+|:")
    print(format_matrix(p_plus))

    print("P^2 = P:")
    print(
        matrix_is_close(
            matrix_multiply(p_plus, p_plus),
            p_plus,
        )
    )

    print("P is Hermitian:", is_hermitian(p_plus))


def measurement_probability_for_projector(
    state: QuantumState,
    measurement_state: QuantumState,
) -> float:
    """
    Born rule for a rank-one projector:

        p = <psi|P|psi>
          = |<measurement_state|psi>|^2
    """
    probability = abs(
        measurement_state.inner_product(state)
    ) ** 2

    return max(0.0, min(1.0, probability))


# =============================================================================
# 26. ORTHOGONAL COMPLEMENTS
# =============================================================================

def demonstrate_orthogonal_complement():
    u = normalize([1, 1])
    v = normalize([1, -1])

    print("u =", format_vector(u))
    print("v =", format_vector(v))
    print("u perpendicular to v:", are_orthogonal(u, v))

    # In C^2, a normalized vector perpendicular to u spans u's orthogonal
    # complement. This is the geometric structure behind many quantum bases.
    print("Orthogonal complement basis vector:", format_vector(v))


# =============================================================================
# 27. GRAM MATRICES AND POSITIVE SEMIDEFINITENESS
# =============================================================================

def demonstrate_gram_matrix():
    vectors = [
        [1, 0],
        [1, 1],
        [0, 2],
    ]

    gram = gram_matrix(vectors)

    print("Vectors:")
    for vector in vectors:
        print(format_vector(vector))

    print("Gram matrix:")
    print(format_matrix(gram))

    # Diagonal entries are squared norms.
    for index, vector in enumerate(vectors):
        print(
            f"G[{index},{index}] = ||v_{index}||^2:",
            format_complex(gram[index][index]),
        )


# =============================================================================
# 28. DISTANCE BETWEEN QUANTUM STATES AND GLOBAL PHASE
# =============================================================================

def state_vector_distance(
    first: QuantumState,
    second: QuantumState,
) -> float:
    """
    Raw Euclidean distance between state vectors.

    This is not physically phase-invariant.
    """
    return vector_norm(
        vector_subtract(
            first.amplitudes,
            second.amplitudes,
        )
    )


def demonstrate_global_phase():
    psi = plus_state()
    phi = QuantumState.from_amplitudes([1j, 1j])

    print("Raw vector distance:", state_vector_distance(psi, phi))
    print("Physically global-phase equivalent:", psi.global_phase_equivalent(phi))

    # The distinction is important:
    # vectors differing by a global phase are different mathematical vectors
    # but represent the same pure physical quantum state.


# =============================================================================
# 29. LINEAR FUNCTIONALS AND RIESZ-STYLE REPRESENTATION IN FINITE DIMENSIONS
# =============================================================================

def linear_functional(
    coefficient_bra: Sequence[complex],
    vector: Sequence[complex],
) -> complex:
    """
    A linear functional represented by a bra.

    f(v) = <a|v>
    """
    return complex_inner_product(coefficient_bra, vector)


def demonstrate_linear_functionals():
    a = [1 + 1j, 2]
    v = [3, -1j]

    result = linear_functional(a, v)

    print("<a|v> =", format_complex(result))

    # A bra is conjugate-linear as a function of its ket label and linear as
    # a functional acting on the ket argument.


# =============================================================================
# 30. DUALITY AND THE DISTINCTION BETWEEN DOT PRODUCTS
# =============================================================================

def demonstrate_dot_product_difference():
    u = [1 + 1j, 2]
    v = [3 - 2j, 4 + 1j]

    naive = dot_product_real(u, v)
    hermitian = complex_inner_product(u, v)

    print("Algebraic component-wise product:", format_complex(naive))
    print("Complex inner product:", format_complex(hermitian))

    # For complex quantum amplitudes, conjugation is essential.
    # Without conjugation, <v|v> can fail to be a nonnegative real number.
    print("Naive v dot v:", format_complex(dot_product_real(v, v)))
    print("Hermitian <v|v>:", format_complex(complex_inner_product(v, v)))


# =============================================================================
# 31. POLYNOMIALS AS AN EXAMPLE OF A VECTOR SPACE
# =============================================================================

def polynomial_add(
    first: Sequence[complex],
    second: Sequence[complex],
) -> Vector:
    size = max(len(first), len(second))
    result = [0j] * size

    for index in range(size):
        a = first[index] if index < len(first) else 0
        b = second[index] if index < len(second) else 0
        result[index] = a + b

    return result


def polynomial_scalar_multiply(
    scalar: complex,
    polynomial: Sequence[complex],
) -> Vector:
    return [scalar * coefficient for coefficient in polynomial]


def polynomial_evaluate(
    polynomial: Sequence[complex],
    x: complex,
) -> complex:
    """Evaluate using Horner's method."""
    result = 0j

    for coefficient in reversed(polynomial):
        result = result * x + coefficient

    return result


def demonstrate_abstract_vector_space():
    # [a0, a1, a2] represents a0 + a1*x + a2*x^2.
    p = [1, 2, 1]
    q = [0, -1, 3]

    print("p(x) =", p)
    print("q(x) =", q)
    print("p + q =", polynomial_add(p, q))
    print("2p =", polynomial_scalar_multiply(2, p))
    print("p(2) =", polynomial_evaluate(p, 2))


# =============================================================================
# 32. COMPLEX PHASE AND INNER PRODUCTS
# =============================================================================

def demonstrate_phase():
    psi = [1 / math.sqrt(2), 1j / math.sqrt(2)]
    phi = [1 / math.sqrt(2), -1j / math.sqrt(2)]

    overlap = complex_inner_product(psi, phi)

    print("|psi> =", format_vector(psi))
    print("|phi> =", format_vector(phi))
    print("<psi|phi> =", format_complex(overlap))
    print("|<psi|phi>| =", abs(overlap))
    print("Squared overlap =", abs(overlap) ** 2)


# =============================================================================
# 33. NUMERICAL STABILITY AND TOLERANCES
# =============================================================================

def demonstrate_floating_point_issue():
    value = 0.1 + 0.2

    print("0.1 + 0.2 =", value)
    print("Exact equality with 0.3:", value == 0.3)
    print("Tolerance-based equality:", math.isclose(value, 0.3))

    state = QuantumState.from_amplitudes(
        [1, 1 + 1e-14]
    )

    probabilities = computational_measurement_probabilities(state)

    print("Normalized state probabilities:", probabilities)
    print("Probability sum:", sum(probabilities))


# =============================================================================
# 34. CLASSICAL GRAM-SCHMIDT VS MODIFIED GRAM-SCHMIDT
# =============================================================================

def demonstrate_gram_schmidt_comparison():
    vectors = [
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 1],
    ]

    classical = gram_schmidt(vectors)
    modified = modified_gram_schmidt(vectors)

    print("Classical Gram-Schmidt:")
    for vector in classical:
        print(format_vector(vector))

    print("Modified Gram-Schmidt:")
    for vector in modified:
        print(format_vector(vector))

    print(
        "Classical result orthonormal:",
        is_orthonormal_set(classical),
    )

    print(
        "Modified result orthonormal:",
        is_orthonormal_set(modified),
    )


# =============================================================================
# 35. QUANTUM STATE SUPERPOSITION
# =============================================================================

def superpose(
    first: QuantumState,
    second: QuantumState,
    coefficient_first: complex,
    coefficient_second: complex,
) -> QuantumState:
    """
    Form a normalized superposition:
        alpha|psi> + beta|phi>
    """
    if first.dimension != second.dimension:
        raise ValueError("States must have the same dimension.")

    combined = vector_add(
        scalar_multiply(coefficient_first, first.amplitudes),
        scalar_multiply(coefficient_second, second.amplitudes),
    )

    return QuantumState.from_amplitudes(combined)


def demonstrate_superposition():
    zero = qubit_zero()
    one = qubit_one()

    state = superpose(
        zero,
        one,
        1 / math.sqrt(3),
        math.sqrt(2 / 3),
    )

    print("Superposition amplitudes:", format_vector(state.amplitudes))
    print(
        "Measurement probabilities:",
        computational_measurement_probabilities(state),
    )


# =============================================================================
# 36. QUANTUM STATES AND ORTHONORMAL EXPANSION
# =============================================================================

def demonstrate_state_expansion():
    zero = qubit_zero()
    one = qubit_one()

    state = QuantumState.from_amplitudes([1, 2j])

    c0 = zero.inner_product(state)
    c1 = one.inner_product(state)

    reconstructed = vector_add(
        scalar_multiply(c0, zero.amplitudes),
        scalar_multiply(c1, one.amplitudes),
    )

    print("|psi> =", format_vector(state.amplitudes))
    print("c0 = <0|psi> =", format_complex(c0))
    print("c1 = <1|psi> =", format_complex(c1))
    print("Reconstructed =", format_vector(reconstructed))


# =============================================================================
# 37. QUANTUM MEASUREMENT IN A NON-COMPUTATIONAL BASIS
# =============================================================================

def measure_in_orthonormal_basis(
    state: QuantumState,
    basis: Sequence[QuantumState],
) -> list[float]:
    if len(basis) != state.dimension:
        raise ValueError("A complete basis must contain dimension vectors.")

    amplitudes = [
        basis_state.inner_product(state)
        for basis_state in basis
    ]

    probabilities = [abs(amplitude) ** 2 for amplitude in amplitudes]

    total = sum(probabilities)

    if abs(total - 1) > 1e-9:
        raise ValueError("Basis must be orthonormal and complete.")

    return probabilities


def demonstrate_noncomputational_measurement():
    plus = plus_state()
    minus = minus_state()
    zero = qubit_zero()

    probabilities = measure_in_orthonormal_basis(
        zero,
        [plus, minus],
    )

    print(
        "Probabilities of measuring |0> in {|+>, |->}:",
        probabilities,
    )


# =============================================================================
# 38. LINEAR OPERATORS AND ADJOINT RELATIONSHIP
# =============================================================================

def demonstrate_adjoint_inner_product_identity():
    operator = [
        [1 + 1j, 2],
        [0, -1j],
    ]

    u = [1, 2j]
    v = [2 - 1j, 3]

    au = matrix_vector_multiply(operator, u)
    adjoint = conjugate_transpose(operator)
    adjoint_v = matrix_vector_multiply(adjoint, v)

    left = complex_inner_product(au, v)
    right = complex_inner_product(u, adjoint_v)

    print("<Au,v> =", format_complex(left))
    print("<u,A†v> =", format_complex(right))
    print("Adjoint identity holds:", is_close(left, right))


# =============================================================================
# 39. HERMITIAN OBSERVABLES AND REAL EXPECTATION VALUES
# =============================================================================

def demonstrate_hermitian_observables():
    observables = {
        "X": pauli_x(),
        "Y": pauli_y(),
        "Z": pauli_z(),
    }

    state = QuantumState.from_amplitudes([1 + 1j, 2])

    for name, observable in observables.items():
        value = expectation_value(state, observable)

        print(
            f"<{name}> =",
            format_complex(value),
            "real up to tolerance:",
            abs(value.imag) <= 1e-10,
        )


# =============================================================================
# 40. UNITARY OPERATORS PRESERVE NORMALIZATION
# =============================================================================

def demonstrate_unitarity_preserves_norm():
    states = [
        qubit_zero(),
        qubit_one(),
        plus_state(),
        QuantumState.from_amplitudes([1 + 2j, 3 - 1j]),
    ]

    operators = [
        pauli_x(),
        pauli_y(),
        pauli_z(),
        hadamard(),
    ]

    for operator in operators:
        print("Operator is unitary:", is_unitary(operator))

        for state in states:
            transformed = apply_operator(operator, state)
            print(
                "  norm before =",
                vector_norm(state.amplitudes),
                "norm after =",
                vector_norm(transformed.amplitudes),
            )


# =============================================================================
# 41. DENSITY-MATRIX PREVIEW CONNECTED TO INNER PRODUCTS
# =============================================================================

def pure_state_density_matrix(
    state: QuantumState,
) -> Matrix:
    """
    rho = |psi><psi|

    This connects vector-space notation with density operators.
    """
    return projector(state)


def density_matrix_trace(matrix: Matrix) -> complex:
    rows, columns = matrix_shape(matrix)

    if rows != columns:
        raise ValueError("Trace requires a square matrix.")

    return sum(matrix[i][i] for i in range(rows))


def demonstrate_density_matrix_connection():
    state = plus_state()
    rho = pure_state_density_matrix(state)

    print("rho = |+><+|:")
    print(format_matrix(rho))
    print("Trace(rho) =", format_complex(density_matrix_trace(rho)))
    print("rho is Hermitian:", is_hermitian(rho))


# =============================================================================
# 42. KET-BRA ALGEBRA
# =============================================================================

def demonstrate_ket_bra_algebra():
    zero = qubit_zero()
    one = qubit_one()

    p0 = projector(zero)
    p1 = projector(one)

    sum_projectors = [
        [a + b for a, b in zip(row_a, row_b)]
        for row_a, row_b in zip(p0, p1)
    ]

    print("|0><0| + |1><1|:")
    print(format_matrix(sum_projectors))
    print(
        "Completeness relation:",
        matrix_is_close(sum_projectors, identity_matrix(2)),
    )


# =============================================================================
# 43. RESOLUTION OF IDENTITY IN AN ORTHONORMAL BASIS
# =============================================================================

def resolution_of_identity(
    basis: Sequence[Sequence[complex]],
) -> Matrix:
    if not is_orthonormal_set(basis):
        raise ValueError("Basis must be orthonormal.")

    size = len(basis[0])
    result = [[0j] * size for _ in range(size)]

    for vector in basis:
        projector_matrix = ket_bra_outer_product(vector, vector)

        for i in range(size):
            for j in range(size):
                result[i][j] += projector_matrix[i][j]

    return result


def demonstrate_resolution_of_identity():
    basis = [
        qubit_zero().amplitudes,
        qubit_one().amplitudes,
    ]

    result = resolution_of_identity(basis)

    print("Sum of computational basis projectors:")
    print(format_matrix(result))

    print(
        "Equals identity:",
        matrix_is_close(result, identity_matrix(2)),
    )


# =============================================================================
# 44. COMPLEX VECTOR SPACE PHASE CONVENTIONS
# =============================================================================

def demonstrate_phase_convention():
    theta = math.pi / 3
    phase = cmath.exp(1j * theta)

    state = plus_state()
    phased = QuantumState(
        scalar_multiply(phase, state.amplitudes)
    )

    print("Phase factor:", format_complex(phase))
    print("Original:", format_vector(state.amplitudes))
    print("Phased:", format_vector(phased.amplitudes))
    print("Same physical pure state:", state.global_phase_equivalent(phased))


# =============================================================================
# 45. EDGE CASES
# =============================================================================

def demonstrate_edge_cases():
    print("Zero vector norm:", vector_norm([0, 0]))

    try:
        normalize([0, 0])
    except ValueError as error:
        print("Zero-vector normalization error:", error)

    try:
        complex_inner_product([1, 2], [1])
    except ValueError as error:
        print("Dimension mismatch error:", error)

    try:
        QuantumState([1, 0, 0])
    except ValueError as error:
        print("Unnormalized quantum-state error:", error)

    try:
        project_onto_vector([1, 2], [0, 0])
    except ValueError as error:
        print("Zero-direction projection error:", error)

    try:
        gram_schmidt([[1, 0], [2, 0]])
    except ValueError as error:
        print("Dependent-vector Gram-Schmidt error:", error)


# =============================================================================
# 46. EDUCATIONAL UNIT TESTS
# =============================================================================

def run_tests():
    """Run assertions covering the most important mathematical properties."""

    # Basic vector algebra.
    assert vector_add([1, 2], [3, 4]) == [4, 6]
    assert vector_subtract([4, 6], [1, 2]) == [3, 4]
    assert scalar_multiply(3, [1, 2]) == [3, 6]

    # Complex inner product.
    u = [1 + 1j, 2]
    v = [3 - 2j, 4 + 1j]

    assert is_close(
        complex_inner_product(u, v),
        complex_inner_product(v, u).conjugate(),
    )

    # Norm and normalization.
    normalized = normalize([3, 4])
    assert is_close(vector_norm(normalized), 1)

    # Orthonormality.
    basis = computational_basis(2)
    assert is_orthonormal_set(basis)

    # Gram-Schmidt.
    q = modified_gram_schmidt([[1, 1], [1, -1]])
    assert is_orthonormal_set(q)

    # Quantum state.
    plus = plus_state()
    assert is_close(vector_norm(plus.amplitudes), 1)

    # Measurement probabilities.
    probabilities = computational_measurement_probabilities(plus)
    assert math.isclose(sum(probabilities), 1)
    assert math.isclose(probabilities[0], 0.5)
    assert math.isclose(probabilities[1], 0.5)

    # Unitary operators.
    assert is_unitary(pauli_x())
    assert is_unitary(pauli_y())
    assert is_unitary(pauli_z())
    assert is_unitary(hadamard())

    # Hermitian operators.
    assert is_hermitian(pauli_x())
    assert is_hermitian(pauli_y())
    assert is_hermitian(pauli_z())

    # X swaps |0> and |1>.
    assert vectors_equal(
        apply_operator(pauli_x(), qubit_zero()).amplitudes,
        qubit_one().amplitudes,
    )

    # H maps |0> to |+>.
    assert vectors_equal(
        apply_operator(hadamard(), qubit_zero()).amplitudes,
        plus.amplitudes,
    )

    # Projection.
    projected = project_onto_vector([2, 3], [1, 1])
    residual = vector_subtract([2, 3], projected)
    assert are_orthogonal(residual, [1, 1])

    # Tensor-product inner-product factorization.
    a = plus_state().amplitudes
    b = qubit_zero().amplitudes
    c = qubit_one().amplitudes

    lhs = complex_inner_product(
        tensor_product(a, b),
        tensor_product(c, c),
    )
    rhs = complex_inner_product(a, c) * complex_inner_product(b, c)

    assert is_close(lhs, rhs)

    # Bell state is entangled.
    assert not is_product_two_qubit_state(bell_phi_plus())

    # Density matrix.
    rho = projector(plus)
    assert matrix_is_close(matrix_multiply(rho, rho), rho)
    assert is_hermitian(rho)
    assert is_close(density_matrix_trace(rho), 1)

    # Completeness.
    assert matrix_is_close(
        resolution_of_identity(
            [qubit_zero().amplitudes, qubit_one().amplitudes]
        ),
        identity_matrix(2),
    )

    print("All tests passed.")


# =============================================================================
# 47. GUIDED STUDY DEMONSTRATION
# =============================================================================

def run_demonstrations():
    sections = [
        ("Vector-space axioms", demonstrate_vector_space_axioms),
        ("Real and complex vectors", demonstrate_real_and_complex_vectors),
        ("Bra-ket notation", demonstrate_bra_ket),
        ("Inner-product axioms", demonstrate_inner_product_axioms),
        ("Geometry: norm, distance, orthogonality", demonstrate_geometry),
        ("Cauchy-Schwarz and triangle inequality", demonstrate_inequalities),
        ("Orthonormal computational basis", demonstrate_orthonormal_basis),
        ("Projection", demonstrate_projection),
        ("Gram-Schmidt", lambda: demonstrate_gram_schmidt_comparison()),
        ("Quantum states", demonstrate_quantum_states),
        ("Measurement probabilities", demonstrate_measurement),
        ("Change of basis", demonstrate_change_of_basis),
        ("Subspace projection", demonstrate_subspace_projection),
        ("Tensor products", demonstrate_tensor_products),
        ("Product versus entangled states", demonstrate_entanglement),
        ("Linear operators", demonstrate_linear_operators),
        ("Hermitian and unitary matrices", demonstrate_operators),
        ("Unitary geometry", demonstrate_unitary_geometry),
        ("Eigenvectors", demonstrate_eigenvectors),
        ("Expectation values", demonstrate_expectation_values),
        ("Observable variance", demonstrate_variance),
        ("Projectors", demonstrate_projector),
        ("Orthogonal complement", demonstrate_orthogonal_complement),
        ("Gram matrix", demonstrate_gram_matrix),
        ("Global phase", demonstrate_global_phase),
        ("Linear functionals", demonstrate_linear_functionals),
        ("Complex dot product distinction", demonstrate_dot_product_difference),
        ("Abstract vector spaces", demonstrate_abstract_vector_space),
        ("Complex phase", demonstrate_phase),
        ("Floating-point stability", demonstrate_floating_point_issue),
        ("Superposition", demonstrate_superposition),
        ("State expansion", demonstrate_state_expansion),
        ("Non-computational measurement", demonstrate_noncomputational_measurement),
        ("Adjoint identity", demonstrate_adjoint_inner_product_identity),
        ("Hermitian observables", demonstrate_hermitian_observables),
        ("Unitary normalization", demonstrate_unitarity_preserves_norm),
        ("Density matrices", demonstrate_density_matrix_connection),
        ("Ket-bra algebra", demonstrate_ket_bra_algebra),
        ("Resolution of identity", demonstrate_resolution_of_identity),
        ("Phase convention", demonstrate_phase_convention),
        ("Edge cases", demonstrate_edge_cases),
    ]

    for title, function in sections:
        print("\n" + "=" * 78)
        print(title.upper())
        print("=" * 78)
        function()


# =============================================================================
# 48. MAIN PROGRAM
# =============================================================================

def main():
    """
    Execute the complete tutorial.

    The examples intentionally progress from elementary vector arithmetic to
    quantum-state geometry, operators, measurement, tensor products,
    entanglement, and finite-dimensional Hilbert-space concepts.
    """
    print("=" * 78)
    print("LINEAR ALGEBRA FOR QUANTUM COMPUTING")
    print("VECTOR SPACES AND INNER PRODUCTS")
    print("=" * 78)

    print("\nThis script is executable educational material.")
    print("All calculations use Python's standard library.")

    run_demonstrations()

    print("\n" + "=" * 78)
    print("UNIT TESTS")
    print("=" * 78)
    run_tests()

    print("\n" + "=" * 78)
    print("END OF TUTORIAL")
    print("=" * 78)


if __name__ == "__main__":
    main()
