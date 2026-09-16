"""
Quantum States: State Vectors and Notation
==========================================

A self-contained study program covering quantum states from introductory
notation through advanced state-vector concepts.

The examples use only the Python standard library. Numerical calculations
are implemented directly so that the mathematical ideas remain visible.

Topics demonstrated:
- Classical states versus quantum states
- Complex numbers and probability amplitudes
- Dirac bra-ket notation
- Qubit basis states |0> and |1>
- State vectors and normalization
- Measurement probabilities
- Global and relative phase
- Bloch-sphere coordinates
- Inner products and orthogonality
- Quantum state overlap and fidelity for pure states
- Operators and expectation values
- Tensor products and multi-qubit states
- Product states versus entangled states
- Partial measurement probabilities
- Change of basis
- Density matrices as an extension of state-vector notation
- Numerical precision and validation
- Common implementation errors
- A small quantum-state analysis workflow
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


EPSILON = 1e-10


# ---------------------------------------------------------------------------
# 1. Complex vectors: the mathematical foundation
# ---------------------------------------------------------------------------

ComplexVector = List[complex]
Matrix = List[List[complex]]


def format_complex(value: complex, digits: int = 6) -> str:
    """Return a compact human-readable representation of a complex number."""
    real = 0.0 if abs(value.real) < EPSILON else value.real
    imag = 0.0 if abs(value.imag) < EPSILON else value.imag

    if abs(imag) < EPSILON:
        return f"{real:.{digits}f}"
    if abs(real) < EPSILON:
        return f"{imag:.{digits}f}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.{digits}f}{sign}{abs(imag):.{digits}f}i"


def format_ket(vector: Sequence[complex], labels: Sequence[str] | None = None) -> str:
    """
    Format a vector using ket notation.

    For a two-dimensional vector [a, b], this produces:
        (a)|0> + (b)|1>
    """
    if labels is None:
        labels = [str(i) for i in range(len(vector))]

    terms = []
    for amplitude, label in zip(vector, labels):
        if abs(amplitude) > EPSILON:
            terms.append(f"({format_complex(amplitude)})|{label}>")

    return " + ".join(terms) if terms else "0"


def vector_add(a: Sequence[complex], b: Sequence[complex]) -> ComplexVector:
    """Add two vectors of equal dimension."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return [x + y for x, y in zip(a, b)]


def vector_scale(vector: Sequence[complex], scalar: complex) -> ComplexVector:
    """Multiply every vector component by a scalar."""
    return [scalar * value for value in vector]


def vector_norm_squared(vector: Sequence[complex]) -> float:
    """
    Return <psi|psi>, which is the squared Euclidean norm.

    For a quantum state this must equal 1 after normalization.
    """
    return sum(abs(value) ** 2 for value in vector)


def vector_norm(vector: Sequence[complex]) -> float:
    """Return sqrt(<psi|psi>)."""
    return math.sqrt(vector_norm_squared(vector))


def normalize(vector: Sequence[complex]) -> ComplexVector:
    """
    Normalize a nonzero vector.

    Quantum state vectors are conventionally normalized so that
    sum_i |alpha_i|^2 = 1.
    """
    norm = vector_norm(vector)
    if norm < EPSILON:
        raise ValueError("The zero vector cannot represent a quantum state.")
    return [value / norm for value in vector]


def is_normalized(vector: Sequence[complex], tolerance: float = EPSILON) -> bool:
    """Check whether a vector has unit norm within numerical tolerance."""
    return abs(vector_norm_squared(vector) - 1.0) <= tolerance


# ---------------------------------------------------------------------------
# 2. Bra-ket notation and inner products
# ---------------------------------------------------------------------------

def conjugate_vector(vector: Sequence[complex]) -> ComplexVector:
    """Return the complex conjugate of every component."""
    return [value.conjugate() for value in vector]


def inner_product(bra_vector: Sequence[complex],
                  ket_vector: Sequence[complex]) -> complex:
    """
    Calculate <bra|ket>.

    The first vector is conjugated before multiplication.
    This conjugation is essential for complex quantum amplitudes.
    """
    if len(bra_vector) != len(ket_vector):
        raise ValueError("Inner-product vectors must have the same dimension.")

    return sum(
        left.conjugate() * right
        for left, right in zip(bra_vector, ket_vector)
    )


def outer_product(ket: Sequence[complex],
                  bra: Sequence[complex]) -> Matrix:
    """
    Calculate |ket><bra|.

    The bra is conjugated component-wise when constructing the matrix.
    """
    return [
        [ket[i] * bra[j].conjugate() for j in range(len(bra))]
        for i in range(len(ket))
    ]


def matrix_vector_multiply(matrix: Matrix,
                           vector: Sequence[complex]) -> ComplexVector:
    """Multiply a matrix by a vector."""
    if not matrix:
        raise ValueError("Matrix cannot be empty.")

    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal length.")
    if columns != len(vector):
        raise ValueError("Matrix and vector dimensions are incompatible.")

    return [
        sum(matrix[row][column] * vector[column] for column in range(columns))
        for row in range(len(matrix))
    ]


def matrix_multiply(a: Matrix, b: Matrix) -> Matrix:
    """Multiply two matrices."""
    if not a or not b:
        raise ValueError("Matrices cannot be empty.")

    a_columns = len(a[0])
    b_columns = len(b[0])

    if any(len(row) != a_columns for row in a):
        raise ValueError("Matrix A is not rectangular.")
    if any(len(row) != b_columns for row in b):
        raise ValueError("Matrix B is not rectangular.")
    if a_columns != len(b):
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        [
            sum(a[i][k] * b[k][j] for k in range(a_columns))
            for j in range(b_columns)
        ]
        for i in range(len(a))
    ]


def print_matrix(matrix: Matrix, title: str = "") -> None:
    """Print a small complex matrix."""
    if title:
        print(title)
    for row in matrix:
        print("  [" + ", ".join(format_complex(value) for value in row) + "]")


# ---------------------------------------------------------------------------
# 3. Basic quantum-state representation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QuantumState:
    """
    Immutable representation of a pure quantum state vector.

    The vector is normalized during construction. A non-normalized input
    therefore becomes the physically equivalent normalized state.

    Important distinction:
    A vector that differs from another by a global phase represents the
    same physical pure state, even though the vectors are mathematically
    different.
    """

    amplitudes: Tuple[complex, ...]

    def __post_init__(self) -> None:
        if not self.amplitudes:
            raise ValueError("A quantum state cannot have zero dimension.")

        if not all(
            isinstance(value, (complex, int, float))
            for value in self.amplitudes
        ):
            raise TypeError("All amplitudes must be numeric.")

        normalized = tuple(normalize(list(self.amplitudes)))
        object.__setattr__(self, "amplitudes", normalized)

        dimension = len(self.amplitudes)
        if dimension & (dimension - 1):
            raise ValueError(
                "For this teaching class, the dimension must be a power of two "
                "so it can represent an integer number of qubits."
            )

    @property
    def dimension(self) -> int:
        return len(self.amplitudes)

    @property
    def qubit_count(self) -> int:
        return int(math.log2(self.dimension))

    def probability(self, basis_index: int) -> float:
        """Probability of measuring a computational-basis index."""
        if not 0 <= basis_index < self.dimension:
            raise IndexError("Basis index is outside the state dimension.")
        return abs(self.amplitudes[basis_index]) ** 2

    def probabilities(self) -> List[float]:
        """Return measurement probabilities in computational basis order."""
        return [abs(value) ** 2 for value in self.amplitudes]

    def ket(self) -> str:
        """Return computational-basis ket notation."""
        labels = [
            format(index, f"0{self.qubit_count}b")
            for index in range(self.dimension)
        ]
        return format_ket(self.amplitudes, labels)

    def global_phase_removed(self) -> "QuantumState":
        """
        Choose a representation whose first nonzero amplitude is real
        and positive. This does not change the physical state.
        """
        first_nonzero = next(
            value for value in self.amplitudes if abs(value) > EPSILON
        )
        phase = cmath.phase(first_nonzero)
        return QuantumState(tuple(
            value * cmath.exp(-1j * phase)
            for value in self.amplitudes
        ))

    def apply(self, operator: Matrix) -> "QuantumState":
        """Apply a square operator and return the normalized resulting state."""
        if len(operator) != self.dimension:
            raise ValueError("Operator dimension does not match state.")

        if any(len(row) != self.dimension for row in operator):
            raise ValueError("Operator must be square with state dimension.")

        result = matrix_vector_multiply(operator, self.amplitudes)

        if vector_norm(result) < EPSILON:
            raise ValueError("Operator produced the zero vector.")

        return QuantumState(tuple(result))


# ---------------------------------------------------------------------------
# 4. Basis states and simple superpositions
# ---------------------------------------------------------------------------

ZERO = QuantumState((1 + 0j, 0 + 0j))
ONE = QuantumState((0 + 0j, 1 + 0j))

print("=" * 78)
print("QUANTUM STATES: STATE VECTORS AND NOTATION")
print("=" * 78)

print("\n1. Computational basis")
print("----------------------")
print("|0> =", ZERO.ket())
print("|1> =", ONE.ket())
print("Measurement probabilities for |0>:", ZERO.probabilities())
print("Measurement probabilities for |1>:", ONE.probabilities())

plus = QuantumState((1, 1))
minus = QuantumState((1, -1))

print("\n2. Superposition states")
print("-----------------------")
print("|+> =", plus.ket())
print("|-> =", minus.ket())
print("P(0) for |+> =", plus.probability(0))
print("P(1) for |+> =", plus.probability(1))

# A complex-amplitude state.
complex_state = QuantumState((1, 1j))
print("\n3. Complex amplitudes")
print("---------------------")
print("State:", complex_state.ket())
print("Probabilities:", complex_state.probabilities())
print("Normalized:", is_normalized(complex_state.amplitudes))


# ---------------------------------------------------------------------------
# 5. Normalization and probability amplitudes
# ---------------------------------------------------------------------------

print("\n4. Normalization")
print("----------------")
unnormalized = [2 + 0j, 2 + 0j]
print("Unnormalized vector:", unnormalized)
print("Squared norm:", vector_norm_squared(unnormalized))

normalized = normalize(unnormalized)
print("Normalized vector:", [format_complex(x) for x in normalized])
print("Squared norm after normalization:", vector_norm_squared(normalized))

print(
    "\nThe amplitude itself is generally not a probability. "
    "The probability is |amplitude|^2."
)

amplitudes = [math.sqrt(0.8), math.sqrt(0.2)]
probability_state = QuantumState(tuple(amplitudes))
print("Example state:", probability_state.ket())
print("Probabilities:", probability_state.probabilities())


# ---------------------------------------------------------------------------
# 6. Global phase versus relative phase
# ---------------------------------------------------------------------------

print("\n5. Global phase and relative phase")
print("----------------------------------")

state_a = QuantumState((1, 1))
state_b = QuantumState((1j, 1j))
state_c = QuantumState((1, -1))

print("State A:", state_a.ket())
print("State B:", state_b.ket())
print("State C:", state_c.ket())

print(
    "A and B have identical measurement probabilities:",
    state_a.probabilities() == state_b.probabilities()
)

overlap_ab = inner_product(state_a.amplitudes, state_b.amplitudes)
overlap_ac = inner_product(state_a.amplitudes, state_c.amplitudes)

print("<A|B> =", format_complex(overlap_ab))
print("<A|C> =", format_complex(overlap_ac))

print(
    "A and B differ only by a global phase; "
    "A and C differ in relative phase."
)


# ---------------------------------------------------------------------------
# 7. Orthogonality
# ---------------------------------------------------------------------------

print("\n6. Orthogonality")
print("----------------")

orthogonality = inner_product(
    plus.amplitudes,
    minus.amplitudes
)

print("<+|-> =", format_complex(orthogonality))
print("Are |+> and |-> orthogonal?", abs(orthogonality) < EPSILON)

print(
    "Orthogonal states have zero inner product and can be perfectly "
    "distinguished by an appropriate measurement."
)


# ---------------------------------------------------------------------------
# 8. Bloch-sphere parameterization
# ---------------------------------------------------------------------------

def bloch_state(theta: float, phi: float) -> QuantumState:
    """
    Construct the pure qubit state

        cos(theta/2)|0> + exp(i*phi) sin(theta/2)|1>.

    Every pure single-qubit state can be represented this way up to a
    physically irrelevant global phase.
    """
    return QuantumState((
        math.cos(theta / 2),
        cmath.exp(1j * phi) * math.sin(theta / 2)
    ))


def bloch_coordinates(state: QuantumState) -> Tuple[float, float, float]:
    """
    Calculate the Bloch vector (x, y, z) for a pure single-qubit state.

    For |psi> = alpha|0> + beta|1>:
        x = 2 Re(alpha* beta)
        y = 2 Im(alpha* beta)
        z = |alpha|^2 - |beta|^2

    The conjugation in alpha* beta is important.
    """
    if state.dimension != 2:
        raise ValueError("Bloch coordinates apply here only to one qubit.")

    alpha, beta = state.amplitudes
    x = 2 * (alpha.conjugate() * beta).real
    y = 2 * (alpha.conjugate() * beta).imag
    z = abs(alpha) ** 2 - abs(beta) ** 2

    return x, y, z


print("\n7. Bloch-sphere representation")
print("------------------------------")

north_pole = bloch_state(0, 0)
south_pole = bloch_state(math.pi, 0)
equator_x = bloch_state(math.pi / 2, 0)
equator_y = bloch_state(math.pi / 2, math.pi / 2)

for name, state in [
    ("|0>", north_pole),
    ("|1>", south_pole),
    ("|+>", equator_x),
    ("+Y state", equator_y),
]:
    print(name, "->", tuple(round(x, 6) for x in bloch_coordinates(state)))


# ---------------------------------------------------------------------------
# 9. Standard single-qubit operators
# ---------------------------------------------------------------------------

I = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, 1 + 0j],
]

X = [
    [0 + 0j, 1 + 0j],
    [1 + 0j, 0 + 0j],
]

Y = [
    [0 + 0j, -1j],
    [1j, 0 + 0j],
]

Z = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, -1 + 0j],
]

H = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]


print("\n8. Operators acting on states")
print("-----------------------------")

print("X|0> =", ZERO.apply(X).ket())
print("X|1> =", ONE.apply(X).ket())
print("H|0> =", ZERO.apply(H).ket())
print("H|1> =", ONE.apply(H).ket())
print("Z|+> =", plus.apply(Z).ket())
print("Z|-> =", minus.apply(Z).ket())


# ---------------------------------------------------------------------------
# 10. Hermitian operators and expectation values
# ---------------------------------------------------------------------------

def expectation_value(state: QuantumState, operator: Matrix) -> complex:
    """
    Calculate <psi|A|psi>.

    For a Hermitian observable A, this value is real up to floating-point
    round-off error.
    """
    transformed = matrix_vector_multiply(operator, state.amplitudes)
    return inner_product(state.amplitudes, transformed)


print("\n9. Expectation values")
print("---------------------")

for name, operator in [("X", X), ("Y", Y), ("Z", Z)]:
    value = expectation_value(equator_x, operator)
    print(f"<+|{name}|+> =", format_complex(value))

print(
    "For a normalized state and Hermitian observable, expectation values "
    "represent the statistical average over repeated measurements."
)


# ---------------------------------------------------------------------------
# 11. Variance and uncertainty
# ---------------------------------------------------------------------------

def matrix_power(matrix: Matrix, exponent: int) -> Matrix:
    """Compute a small square matrix power using repeated multiplication."""
    if exponent < 0:
        raise ValueError("Exponent must be non-negative.")

    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("Matrix must be non-empty and square.")

    result = [[complex(I[i][j]) if i == j else 0j for j in range(size)]
              for i in range(size)]

    for _ in range(exponent):
        result = matrix_multiply(result, matrix)

    return result


def variance(state: QuantumState, observable: Matrix) -> float:
    """Calculate Var(A) = <A^2> - <A>^2 for a Hermitian observable."""
    mean = expectation_value(state, observable)
    second_moment = expectation_value(
        state,
        matrix_power(observable, 2)
    )
    value = second_moment - mean * mean
    return max(0.0, value.real)


print("\n10. Measurement variance")
print("------------------------")
print("Variance of X for |+>:", variance(plus, X))
print("Variance of Z for |+>:", variance(plus, Z))


# ---------------------------------------------------------------------------
# 12. Measurement simulation
# ---------------------------------------------------------------------------

import random


def sample_measurement(state: QuantumState,
                       trials: int = 1000,
                       seed: int | None = 7) -> dict[int, int]:
    """
    Simulate computational-basis measurements.

    A real quantum measurement produces one classical outcome per trial.
    The simulation samples according to Born probabilities.
    """
    if trials <= 0:
        raise ValueError("Number of trials must be positive.")

    probabilities = state.probabilities()

    if seed is not None:
        random.seed(seed)

    counts = {index: 0 for index in range(state.dimension)}

    for _ in range(trials):
        random_value = random.random()
        cumulative = 0.0

        for index, probability in enumerate(probabilities):
            cumulative += probability
            if random_value < cumulative:
                counts[index] += 1
                break

    return counts


print("\n11. Repeated measurement simulation")
print("------------------------------------")

counts = sample_measurement(probability_state, 10000, seed=42)
print("Theoretical probabilities:", probability_state.probabilities())
print("Observed counts:", counts)
print(
    "Observed frequencies:",
    {
        index: round(count / 10000, 4)
        for index, count in counts.items()
    }
)


# ---------------------------------------------------------------------------
# 13. Tensor products
# ---------------------------------------------------------------------------

def tensor_product_vector(a: Sequence[complex],
                          b: Sequence[complex]) -> ComplexVector:
    """
    Compute |a> tensor |b>.

    If a has dimension m and b has dimension n, the result has dimension
    m*n. For qubits, tensor products build multi-qubit state vectors.
    """
    return [
        amplitude_a * amplitude_b
        for amplitude_a in a
        for amplitude_b in b
    ]


def tensor_product_matrix(a: Matrix, b: Matrix) -> Matrix:
    """
    Compute the Kronecker product A tensor B.

    If A is m x n and B is p x q, the result is (m*p) x (n*q).
    """
    if not a or not b:
        raise ValueError("Matrices cannot be empty.")

    result: Matrix = []

    for row_a in a:
        for row_b in b:
            row = []
            for value_a in row_a:
                for value_b in row_b:
                    row.append(value_a * value_b)
            result.append(row)

    return result


def basis_label(index: int, qubits: int) -> str:
    """Format an integer as a computational basis bit string."""
    return format(index, f"0{qubits}b")


print("\n12. Tensor products and multi-qubit states")
print("-------------------------------------------")

zero_zero = QuantumState(
    tuple(tensor_product_vector(ZERO.amplitudes, ZERO.amplitudes))
)

plus_plus = QuantumState(
    tuple(tensor_product_vector(plus.amplitudes, plus.amplitudes))
)

print("|00> =", zero_zero.ket())
print("|++> =", plus_plus.ket())
print("Dimension of two-qubit state:", plus_plus.dimension)
print("Number of qubits:", plus_plus.qubit_count)


# ---------------------------------------------------------------------------
# 14. Product states versus entangled states
# ---------------------------------------------------------------------------

def is_product_of_two_qubits(state: QuantumState,
                             tolerance: float = 1e-9) -> bool:
    """
    Test separability of a pure two-qubit state.

    Arrange amplitudes as a 2x2 coefficient matrix:

        [a00 a01]
        [a10 a11]

    A pure two-qubit state is separable exactly when this matrix has rank 1,
    which for a 2x2 matrix is equivalent to:

        a00*a11 - a01*a10 = 0.
    """
    if state.dimension != 4:
        raise ValueError("This function expects a two-qubit state.")

    a00, a01, a10, a11 = state.amplitudes
    determinant = a00 * a11 - a01 * a10
    return abs(determinant) <= tolerance


bell_phi_plus = QuantumState((
    1 / math.sqrt(2),
    0,
    0,
    1 / math.sqrt(2),
))

bell_phi_minus = QuantumState((
    1 / math.sqrt(2),
    0,
    0,
    -1 / math.sqrt(2),
))

print("\n13. Product and entangled states")
print("--------------------------------")

print("|++> is product:", is_product_of_two_qubits(plus_plus))
print("|Phi+> is product:", is_product_of_two_qubits(bell_phi_plus))
print("|Phi-> is product:", is_product_of_two_qubits(bell_phi_minus))

print(
    "A Bell state cannot be written as |a> tensor |b> for single-qubit "
    "states |a> and |b>."
)


# ---------------------------------------------------------------------------
# 15. Partial measurement probabilities
# ---------------------------------------------------------------------------

def marginal_probability_for_first_qubit(
    state: QuantumState,
    first_qubit_value: int
) -> float:
    """
    Compute P(first qubit = 0 or 1) for a two-qubit state.

    Computational ordering used here:
        |00>, |01>, |10>, |11>
    """
    if state.dimension != 4:
        raise ValueError("This example expects a two-qubit state.")

    if first_qubit_value not in (0, 1):
        raise ValueError("Qubit value must be 0 or 1.")

    selected_indices = (
        [0, 1] if first_qubit_value == 0 else [2, 3]
    )

    return sum(
        state.probability(index)
        for index in selected_indices
    )


print("\n14. Partial measurement probabilities")
print("-------------------------------------")

print(
    "Bell state P(first qubit=0):",
    marginal_probability_for_first_qubit(bell_phi_plus, 0)
)
print(
    "Bell state P(first qubit=1):",
    marginal_probability_for_first_qubit(bell_phi_plus, 1)
)


# ---------------------------------------------------------------------------
# 16. Change of basis
# ---------------------------------------------------------------------------

def adjoint(matrix: Matrix) -> Matrix:
    """Return the conjugate transpose of a matrix."""
    if not matrix:
        raise ValueError("Matrix cannot be empty.")

    rows = len(matrix)
    columns = len(matrix[0])

    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix must be rectangular.")

    return [
        [
            matrix[row][column].conjugate()
            for row in range(rows)
        ]
        for column in range(columns)
    ]


def change_basis(state: QuantumState,
                 basis_matrix: Matrix) -> ComplexVector:
    """
    Express a state in a new orthonormal basis.

    If columns of U are the new basis vectors, coordinates are:

        U^† |psi>
    """
    if len(basis_matrix) != state.dimension:
        raise ValueError("Basis dimension does not match state.")

    if any(len(row) != state.dimension for row in basis_matrix):
        raise ValueError("Basis matrix must be square.")

    return matrix_vector_multiply(
        adjoint(basis_matrix),
        state.amplitudes
    )


print("\n15. Change of basis")
print("-------------------")

z_coordinates = ZERO.amplitudes
x_coordinates = change_basis(ZERO, H)

print("Coordinates of |0> in Z basis:",
      [format_complex(value) for value in z_coordinates])
print("Coordinates of |0> in X basis:",
      [format_complex(value) for value in x_coordinates])

print(
    "A quantum state does not depend on a particular coordinate system. "
    "The vector components change when the basis changes."
)


# ---------------------------------------------------------------------------
# 17. Density matrix as an extension of state-vector representation
# ---------------------------------------------------------------------------

def density_matrix(state: QuantumState) -> Matrix:
    """Construct rho = |psi><psi| for a pure state."""
    return outer_product(state.amplitudes, state.amplitudes)


def trace(matrix: Matrix) -> complex:
    """Calculate the trace of a square matrix."""
    if len(matrix) == 0:
        raise ValueError("Matrix cannot be empty.")

    if any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Matrix must be square.")

    return sum(matrix[i][i] for i in range(len(matrix)))


def purity(rho: Matrix) -> float:
    """
    Calculate Tr(rho^2).

    A pure density matrix has purity 1.
    Mixed states have purity below 1.
    """
    rho_squared = matrix_multiply(rho, rho)
    return trace(rho_squared).real


print("\n16. Density-matrix representation")
print("--------------------------------")

rho_plus = density_matrix(plus)
print_matrix(rho_plus, "rho = |+><+|:")
print("Trace:", format_complex(trace(rho_plus)))
print("Purity:", purity(rho_plus))


# ---------------------------------------------------------------------------
# 18. Pure-state overlap and fidelity
# ---------------------------------------------------------------------------

def pure_state_fidelity(a: QuantumState, b: QuantumState) -> float:
    """
    Fidelity between two pure states:

        F = |<a|b>|^2

    F = 1 means physically identical pure states up to global phase.
    F = 0 means orthogonal states.
    """
    if a.dimension != b.dimension:
        raise ValueError("States must have equal dimension.")

    return abs(inner_product(a.amplitudes, b.amplitudes)) ** 2


print("\n17. Pure-state fidelity")
print("-----------------------")

print("F(|+>, |+>) =", pure_state_fidelity(plus, plus))
print("F(|+>, |->) =", pure_state_fidelity(plus, minus))
print("F(|+>, |0>) =", pure_state_fidelity(plus, ZERO))


# ---------------------------------------------------------------------------
# 19. Applying a sequence of gates
# ---------------------------------------------------------------------------

def apply_operator_sequence(
    state: QuantumState,
    operators: Sequence[Matrix]
) -> QuantumState:
    """Apply operators from left to right in the supplied sequence."""
    current = state
    for operator in operators:
        current = current.apply(operator)
    return current


print("\n18. Gate sequence")
print("-----------------")

# H|0> = |+>, then Z|+> = |->.
sequence_result = apply_operator_sequence(ZERO, [H, Z])
print("Start: |0>")
print("After H then Z:", sequence_result.ket())


# ---------------------------------------------------------------------------
# 20. Operator unitarity
# ---------------------------------------------------------------------------

def is_identity(matrix: Matrix, tolerance: float = 1e-9) -> bool:
    """Check whether a matrix is numerically equal to identity."""
    if not matrix:
        return False

    rows = len(matrix)
    columns = len(matrix[0])

    if rows != columns:
        return False

    return all(
        abs(
            matrix[i][j] - (1 if i == j else 0)
        ) <= tolerance
        for i in range(rows)
        for j in range(columns)
    )


def is_unitary(matrix: Matrix, tolerance: float = 1e-9) -> bool:
    """
    A matrix U is unitary when U†U = I.

    Unitary evolution preserves inner products and state normalization.
    """
    if not matrix or len(matrix) != len(matrix[0]):
        return False

    product = matrix_multiply(adjoint(matrix), matrix)
    return is_identity(product, tolerance)


print("\n19. Unitary operators")
print("---------------------")

for name, operator in [
    ("I", I),
    ("X", X),
    ("Y", Y),
    ("Z", Z),
    ("H", H),
]:
    print(f"{name} is unitary:", is_unitary(operator))


# ---------------------------------------------------------------------------
# 21. Demonstrating numerical precision and invalid states
# ---------------------------------------------------------------------------

print("\n20. Validation and edge cases")
print("-----------------------------")

try:
    normalize([0j, 0j])
except ValueError as error:
    print("Zero-vector error:", error)

try:
    QuantumState((1, 1, 1))
except ValueError as error:
    print("Invalid dimension error:", error)

try:
    QuantumState((1, 0)).probability(2)
except IndexError as error:
    print("Invalid basis-index error:", error)

print(
    "Floating-point calculations use tolerances because expressions that "
    "are mathematically zero can produce tiny residual values."
)


# ---------------------------------------------------------------------------
# 22. Demonstrating the Born rule in a custom measurement basis
# ---------------------------------------------------------------------------

def probabilities_in_basis(
    state: QuantumState,
    basis_matrix: Matrix
) -> List[float]:
    """
    Calculate probabilities after expressing a state in a new orthonormal basis.
    """
    coordinates = change_basis(state, basis_matrix)
    return [abs(value) ** 2 for value in coordinates]


print("\n21. Measurement in a different basis")
print("------------------------------------")

print(
    "Probability of |0> and |1> when measuring |+> in Z basis:",
    probabilities_in_basis(plus, I)
)

print(
    "Probability of |+> and |-> when measuring |+> in X basis:",
    probabilities_in_basis(plus, H)
)

print(
    "The measurement basis determines which amplitudes are converted "
    "into observable probabilities."
)


# ---------------------------------------------------------------------------
# 23. A complete educational workflow
# ---------------------------------------------------------------------------

def analyze_state(state: QuantumState, name: str) -> None:
    """Print a compact analysis of a pure quantum state."""
    print(f"\nState analysis: {name}")
    print("-" * 40)
    print("Dimension:", state.dimension)
    print("Qubits:", state.qubit_count)
    print("Ket:", state.ket())
    print("Normalized:", is_normalized(state.amplitudes))
    print("Probabilities:", [
        round(probability, 8)
        for probability in state.probabilities()
    ])

    if state.dimension == 2:
        print(
            "Bloch coordinates:",
            tuple(round(value, 8) for value in bloch_coordinates(state))
        )

    print("X expectation:", format_complex(expectation_value(state, X))
          if state.dimension == 2 else "not applicable")
    print("Z expectation:", format_complex(expectation_value(state, Z))
          if state.dimension == 2 else "not applicable")


analyze_state(ZERO, "|0>")
analyze_state(plus, "|+>")
analyze_state(complex_state, "(|0> + i|1>)/sqrt(2)")
analyze_state(bell_phi_plus, "|Phi+>")


# ---------------------------------------------------------------------------
# 24. Conceptual reference printed by the program
# ---------------------------------------------------------------------------

print("\n22. Core notation reference")
print("---------------------------")
notation_reference = {
    "|psi>": "Ket representing a quantum state.",
    "<psi|": "Bra, the conjugate transpose of |psi>.",
    "<phi|psi>": "Inner product / probability amplitude for overlap.",
    "|psi><psi|": "Outer product; density matrix for a pure state.",
    "alpha|0> + beta|1>":
        "General single-qubit state with |alpha|^2 + |beta|^2 = 1.",
    "|psi> tensor |phi>":
        "Composite state formed from two subsystems.",
    "U|psi>":
        "State after applying operator U.",
    "<psi|A|psi>":
        "Expectation value of observable A.",
}

for notation, meaning in notation_reference.items():
    print(f"{notation:24} -> {meaning}")


# ---------------------------------------------------------------------------
# 25. Important distinctions
# ---------------------------------------------------------------------------

print("\n23. Important distinctions")
print("-------------------------")

distinctions = [
    (
        "Amplitude",
        "A generally complex coefficient; not itself a probability."
    ),
    (
        "Probability",
        "A real number in [0, 1], obtained from |amplitude|^2."
    ),
    (
        "State vector",
        "A coordinate representation of a pure state in a chosen basis."
    ),
    (
        "Global phase",
        "A common complex phase multiplying the whole state; physically irrelevant."
    ),
    (
        "Relative phase",
        "Phase difference between components; can affect interference."
    ),
    (
        "Basis",
        "A complete set of vectors used to express state coordinates."
    ),
    (
        "Pure state",
        "A state completely represented by one normalized ket."
    ),
    (
        "Mixed state",
        "A statistical ensemble represented naturally by a density matrix."
    ),
    (
        "Product state",
        "A composite state that factors into subsystem states."
    ),
    (
        "Entangled state",
        "A composite state that cannot be factored into subsystem state vectors."
    ),
]

for term, explanation in distinctions:
    print(f"{term:18} : {explanation}")


# ---------------------------------------------------------------------------
# 26. Common mistakes
# ---------------------------------------------------------------------------

print("\n24. Common implementation mistakes")
print("----------------------------------")

mistakes = [
    "Treating complex amplitudes directly as probabilities.",
    "Forgetting complex conjugation in the inner product.",
    "Using a non-normalized vector as a physical state without normalization.",
    "Confusing global phase with relative phase.",
    "Assuming every multi-qubit state is a tensor product of individual states.",
    "Changing basis without applying the appropriate basis transformation.",
    "Ignoring numerical tolerances when testing exact mathematical identities.",
    "Assuming a state vector alone represents a classical probability distribution.",
    "Applying a non-unitary operator as though it were ordinary closed-system evolution.",
]

for number, mistake in enumerate(mistakes, start=1):
    print(f"{number}. {mistake}")


# ---------------------------------------------------------------------------
# 27. Complexity considerations
# ---------------------------------------------------------------------------

print("\n25. Computational scaling")
print("-------------------------")
print(
    "An n-qubit state vector has 2^n complex amplitudes. "
    "Storing the vector therefore requires O(2^n) memory."
)
print(
    "A dense 2^n x 2^n operator requires O(4^n) matrix entries, "
    "which becomes impractical much faster than the state vector itself."
)
print(
    "This exponential state-space growth is one reason classical simulation "
    "of general quantum systems becomes difficult as qubit count increases."
)


# ---------------------------------------------------------------------------
# 28. Final executable checks
# ---------------------------------------------------------------------------

def run_self_tests() -> None:
    """Verify the principal mathematical invariants used in this tutorial."""

    assert is_normalized(ZERO.amplitudes)
    assert is_normalized(ONE.amplitudes)
    assert is_normalized(plus.amplitudes)

    assert abs(inner_product(ZERO.amplitudes, ONE.amplitudes)) < EPSILON
    assert abs(inner_product(plus.amplitudes, minus.amplitudes)) < EPSILON

    assert is_unitary(X)
    assert is_unitary(Y)
    assert is_unitary(Z)
    assert is_unitary(H)

    assert abs(sum(plus.probabilities()) - 1.0) < EPSILON
    assert abs(pure_state_fidelity(plus, plus) - 1.0) < EPSILON
    assert abs(pure_state_fidelity(plus, minus)) < EPSILON

    assert is_product_of_two_qubits(plus_plus)
    assert not is_product_of_two_qubits(bell_phi_plus)

    rho = density_matrix(plus)
    assert abs(trace(rho) - 1.0) < EPSILON
    assert abs(purity(rho) - 1.0) < EPSILON

    bloch = bloch_coordinates(plus)
    assert abs(bloch[0] - 1.0) < EPSILON
    assert abs(bloch[1]) < EPSILON
    assert abs(bloch[2]) < EPSILON

    print("\nSelf-tests: PASS")


run_self_tests()

print("\n" + "=" * 78)
print("END OF QUANTUM STATE VECTOR STUDY")
print("=" * 78)
