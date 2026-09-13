"""
Superposition: Quantum States and Amplitudes
=============================================

A self-contained study script covering quantum superposition, quantum states,
probability amplitudes, measurement, normalization, interference, phase,
qubits, basis changes, Bloch-sphere intuition, tensor products, multi-qubit
superposition, entanglement, quantum gates, density matrices, mixed states,
measurement probabilities, simulation, numerical precision, and practical
implementation considerations.

The examples use only Python's standard library.
"""

import cmath
import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


# =============================================================================
# 1. FUNDAMENTAL MATHEMATICAL IDEAS
# =============================================================================

print("=" * 80)
print("SUPERPOSITION: QUANTUM STATES AND AMPLITUDES")
print("=" * 80)


def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


section("1. Complex numbers and probability amplitudes")

# Quantum amplitudes are generally complex numbers.
#
# A complex amplitude has the form:
#
#     a = x + iy
#
# where i^2 = -1.
#
# The amplitude itself is not normally a probability.
# Its probability contribution is obtained from the squared magnitude:
#
#     P = |a|^2 = a * conjugate(a)
#
# For a = x + iy:
#
#     |a|^2 = x^2 + y^2


amplitude = 1 + 2j
squared_magnitude = abs(amplitude) ** 2

print("Amplitude:", amplitude)
print("Magnitude:", abs(amplitude))
print("Squared magnitude:", squared_magnitude)

# The phase of a nonzero complex amplitude is its angle in the complex plane.
phase = cmath.phase(amplitude)

print("Phase in radians:", phase)
print("Phase in degrees:", math.degrees(phase))


def probability_from_amplitude(amplitude: complex) -> float:
    """
    Convert a quantum amplitude into a measurement probability.

    The Born rule states that the probability associated with an amplitude
    is the squared magnitude of that amplitude.
    """
    return abs(amplitude) ** 2


print("Probability from 0.6 amplitude:", probability_from_amplitude(0.6))


# =============================================================================
# 2. QUANTUM STATES
# =============================================================================

section("2. Quantum states")

# A quantum state is a mathematical description of the state of a quantum
# system. For a two-level system (qubit), a general pure state can be written:
#
#     |psi> = alpha |0> + beta |1>
#
# where alpha and beta are complex probability amplitudes.
#
# The state must be normalized:
#
#     |alpha|^2 + |beta|^2 = 1
#
# This guarantees that the probabilities of all mutually exclusive outcomes
# add to one.


@dataclass
class QubitState:
    """
    A pure single-qubit state.

    alpha is the amplitude of |0>.
    beta is the amplitude of |1>.
    """

    alpha: complex
    beta: complex

    def norm_squared(self) -> float:
        """Return <psi|psi>, the squared norm of the state vector."""
        return abs(self.alpha) ** 2 + abs(self.beta) ** 2

    def is_normalized(self, tolerance: float = 1e-12) -> bool:
        """Check whether the state is normalized within numerical tolerance."""
        return math.isclose(self.norm_squared(), 1.0, abs_tol=tolerance)

    def normalize(self) -> "QubitState":
        """Return a normalized copy of the state."""
        norm = math.sqrt(self.norm_squared())

        if norm == 0:
            raise ValueError("The zero vector cannot represent a quantum state.")

        return QubitState(
            self.alpha / norm,
            self.beta / norm,
        )

    def probabilities(self) -> Tuple[float, float]:
        """Return measurement probabilities in the computational basis."""
        normalized = self.normalize()

        return (
            abs(normalized.alpha) ** 2,
            abs(normalized.beta) ** 2,
        )

    def phase_difference(self) -> float:
        """
        Return the relative phase beta - alpha.

        Global phase is physically irrelevant for measurement predictions,
        while relative phase can affect interference.
        """
        if self.alpha == 0 or self.beta == 0:
            return 0.0

        return cmath.phase(self.beta) - cmath.phase(self.alpha)

    def global_phase_removed(self) -> "QubitState":
        """
        Remove the global phase by making the first nonzero amplitude real.

        A state |psi> and e^(i*theta)|psi> produce identical measurement
        probabilities for every measurement.
        """
        state = self.normalize()

        reference = state.alpha if state.alpha != 0 else state.beta

        if reference == 0:
            raise ValueError("Invalid zero state.")

        phase = cmath.phase(reference)
        factor = cmath.exp(-1j * phase)

        return QubitState(
            state.alpha * factor,
            state.beta * factor,
        )

    def __str__(self) -> str:
        return f"({self.alpha})|0> + ({self.beta})|1>"


zero = QubitState(1, 0)
one = QubitState(0, 1)

print("|0> =", zero)
print("|1> =", one)
print("|0> probabilities =", zero.probabilities())
print("|1> probabilities =", one.probabilities())


# =============================================================================
# 3. SUPERPOSITION
# =============================================================================

section("3. What superposition means")

# Superposition means that a quantum state can be expressed as a linear
# combination of basis states.
#
# For a qubit:
#
#     |psi> = alpha|0> + beta|1>
#
# with:
#
#     |alpha|^2 + |beta|^2 = 1
#
# A balanced superposition is:
#
#     |+> = (|0> + |1>) / sqrt(2)
#
# Its amplitudes are both 1/sqrt(2), so the measurement probabilities are
# both 1/2.


sqrt_half = 1 / math.sqrt(2)

plus = QubitState(
    sqrt_half,
    sqrt_half,
)

minus = QubitState(
    sqrt_half,
    -sqrt_half,
)

print("|+> =", plus)
print("|+> probabilities =", plus.probabilities())

print("|-> =", minus)
print("|-> probabilities =", minus.probabilities())


# Important distinction:
#
# It is tempting to say that a qubit in:
#
#     (|0> + |1>)/sqrt(2)
#
# is simply "50% zero and 50% one before measurement."
#
# That description loses important information.
#
# The quantum state contains amplitudes, not merely probabilities.
# The signs and complex phases of amplitudes can later affect interference.


# =============================================================================
# 4. NORMALIZATION
# =============================================================================

section("4. Normalization")

# A state vector must have total probability one.
#
# Example:
#
#     |psi> = 3|0> + 4|1>
#
# has squared norm:
#
#     3^2 + 4^2 = 25
#
# so it is not normalized.
#
# Dividing by 5 gives:
#
#     |psi> = 3/5 |0> + 4/5 |1>
#
# and probabilities:
#
#     P(0) = 9/25
#     P(1) = 16/25


unnormalized = QubitState(3, 4)

print("Unnormalized state:", unnormalized)
print("Squared norm:", unnormalized.norm_squared())

normalized = unnormalized.normalize()

print("Normalized state:", normalized)
print("Squared norm after normalization:", normalized.norm_squared())
print("Probabilities:", normalized.probabilities())


# A useful general vector implementation follows.


def vector_norm_squared(state: Sequence[complex]) -> float:
    """Return the squared Euclidean norm of a complex state vector."""
    return sum(abs(value) ** 2 for value in state)


def normalize_state(state: Sequence[complex]) -> List[complex]:
    """Normalize an arbitrary finite-dimensional complex state vector."""
    norm_squared = vector_norm_squared(state)

    if norm_squared <= 0:
        raise ValueError("The zero vector cannot be normalized.")

    norm = math.sqrt(norm_squared)

    return [value / norm for value in state]


example_state = [1 + 0j, 2 + 0j, 2j]

print("General state:", example_state)
print("Squared norm:", vector_norm_squared(example_state))

normalized_example = normalize_state(example_state)

print("Normalized state:", normalized_example)
print("Normalized squared norm:", vector_norm_squared(normalized_example))


# =============================================================================
# 5. BRA-KET NOTATION
# =============================================================================

section("5. Bra-ket notation and state vectors")

# Dirac notation:
#
#     |psi>
#
# is called a ket.
#
# Its conjugate transpose is:
#
#     <psi|
#
# called a bra.
#
# The inner product:
#
#     <phi|psi>
#
# is a complex number.
#
# The normalization condition:
#
#     <psi|psi> = 1
#
# is equivalent to the state-vector norm being one.


def inner_product(
    bra_state: Sequence[complex],
    ket_state: Sequence[complex],
) -> complex:
    """
    Calculate <bra|ket>.

    The bra is conjugated before multiplication.
    """
    if len(bra_state) != len(ket_state):
        raise ValueError("States must have the same dimension.")

    return sum(
        complex(bra_value).conjugate() * ket_value
        for bra_value, ket_value in zip(bra_state, ket_state)
    )


ket_a = [1 / math.sqrt(2), 1j / math.sqrt(2)]
ket_b = [1 / math.sqrt(2), -1j / math.sqrt(2)]

print("<a|a> =", inner_product(ket_a, ket_a))
print("<a|b> =", inner_product(ket_a, ket_b))


# =============================================================================
# 6. BASIS STATES AND BASIS REPRESENTATION
# =============================================================================

section("6. Basis and representation")

# A quantum state does not have one universal list of amplitudes independent
# of representation. Amplitudes are defined relative to a chosen basis.
#
# For a qubit, the computational basis is:
#
#     |0> = [1, 0]^T
#     |1> = [0, 1]^T
#
# The same physical state can have different amplitudes in another basis.
#
# The Hadamard basis is:
#
#     |+> = (|0> + |1>)/sqrt(2)
#     |-> = (|0> - |1>)/sqrt(2)


computational_zero = [1 + 0j, 0 + 0j]
computational_one = [0 + 0j, 1 + 0j]

hadamard_plus = [
    1 / math.sqrt(2),
    1 / math.sqrt(2),
]

hadamard_minus = [
    1 / math.sqrt(2),
    -1 / math.sqrt(2),
]

print("Computational |0>:", computational_zero)
print("Computational |1>:", computational_one)
print("Hadamard |+>:", hadamard_plus)
print("Hadamard |->:", hadamard_minus)


# =============================================================================
# 7. PROBABILITY AMPLITUDES VERSUS PROBABILITIES
# =============================================================================

section("7. Amplitudes are not probabilities")

# Consider:
#
#     |psi> = (1/sqrt(2))|0> + (1/sqrt(2))|1>
#
# Amplitudes:
#
#     alpha = 1/sqrt(2)
#     beta  = 1/sqrt(2)
#
# Probabilities:
#
#     |alpha|^2 = 1/2
#     |beta|^2  = 1/2
#
# Complex amplitudes can contain phase information that ordinary probabilities
# cannot represent.


states_to_compare = {
    "|+>": QubitState(1 / math.sqrt(2), 1 / math.sqrt(2)),
    "|->": QubitState(1 / math.sqrt(2), -1 / math.sqrt(2)),
    "phase i": QubitState(1 / math.sqrt(2), 1j / math.sqrt(2)),
    "phase -i": QubitState(1 / math.sqrt(2), -1j / math.sqrt(2)),
}

for name, state in states_to_compare.items():
    print(f"{name:10s} amplitudes={state} probabilities={state.probabilities()}")


# Notice that all four examples have the same computational-basis
# probabilities, but they are not the same quantum state.
#
# Their relative phases differ.


# =============================================================================
# 8. GLOBAL PHASE VERSUS RELATIVE PHASE
# =============================================================================

section("8. Global phase and relative phase")

# Multiplying an entire state by e^(i*theta) gives:
#
#     |psi'> = e^(i*theta)|psi>
#
# This is called a global phase.
#
# It does not change ordinary measurement probabilities.
#
# Relative phase is different:
#
#     |psi> = (|0> + |1>)/sqrt(2)
#
# versus:
#
#     |phi> = (|0> - |1>)/sqrt(2)
#
# have different relative phase and can behave differently under later
# transformations.


base_state = QubitState(
    1 / math.sqrt(2),
    1j / math.sqrt(2),
)

global_phase = cmath.exp(1j * 1.234)

phase_shifted_state = QubitState(
    global_phase * base_state.alpha,
    global_phase * base_state.beta,
)

print("Original probabilities:", base_state.probabilities())
print("Global-phase-shifted probabilities:", phase_shifted_state.probabilities())

print("Original:", base_state)
print("Global phase applied:", phase_shifted_state)


# =============================================================================
# 9. THE BORN RULE
# =============================================================================

section("9. The Born rule")

# If a normalized state is:
#
#     |psi> = sum_i c_i |i>
#
# then measuring in that basis gives outcome i with probability:
#
#     P(i) = |c_i|^2
#
# This is the Born rule.


def measurement_probabilities(state: Sequence[complex]) -> List[float]:
    """
    Calculate Born-rule probabilities from a state vector.

    The state is normalized internally so the function is tolerant of small
    scaling differences in input.
    """
    normalized = normalize_state(state)
    return [abs(amplitude) ** 2 for amplitude in normalized]


state = [
    1,
    1j,
    2,
]

probabilities = measurement_probabilities(state)

print("State:", state)
print("Measurement probabilities:", probabilities)
print("Probability total:", sum(probabilities))


# =============================================================================
# 10. MEASUREMENT SIMULATION
# =============================================================================

section("10. Simulating measurement")

# A quantum measurement produces one classical outcome.
#
# Repeating the same preparation and measurement many times produces a
# statistical distribution that approaches the theoretical probabilities.


def sample_from_probabilities(probabilities: Sequence[float]) -> int:
    """Sample one index according to a normalized probability distribution."""
    if not probabilities:
        raise ValueError("Probability list cannot be empty.")

    total = sum(probabilities)

    if total <= 0:
        raise ValueError("Probability total must be positive.")

    normalized = [p / total for p in probabilities]

    if any(p < 0 for p in normalized):
        raise ValueError("Probabilities cannot be negative.")

    random_value = random.random()
    cumulative = 0.0

    for index, probability in enumerate(normalized):
        cumulative += probability

        if random_value < cumulative:
            return index

    return len(normalized) - 1


def simulate_measurements(
    state: Sequence[complex],
    shots: int,
) -> Dict[int, int]:
    """Simulate repeated computational-basis measurements."""
    if shots <= 0:
        raise ValueError("shots must be positive.")

    probabilities = measurement_probabilities(state)
    counts = {index: 0 for index in range(len(state))}

    for _ in range(shots):
        outcome = sample_from_probabilities(probabilities)
        counts[outcome] += 1

    return counts


random.seed(42)

measurement_state = [
    math.sqrt(0.7),
    math.sqrt(0.3),
]

counts = simulate_measurements(measurement_state, 10_000)

print("Theoretical probabilities:", measurement_probabilities(measurement_state))
print("Measurement counts:", counts)

frequencies = {
    outcome: count / 10_000
    for outcome, count in counts.items()
}

print("Observed frequencies:", frequencies)


# =============================================================================
# 11. PROJECTIVE MEASUREMENT AND COLLAPSE
# =============================================================================

section("11. Measurement and state update")

# For the computational basis, the projectors are:
#
#     P0 = |0><0|
#     P1 = |1><1|
#
# If a measurement returns 0, the post-measurement state becomes |0>.
# If it returns 1, it becomes |1>.
#
# This is commonly described as state collapse.
#
# The exact physical interpretation of "collapse" depends on the formulation
# of quantum theory, but the mathematical state-update rule is unambiguous
# for an ideal projective measurement.


def measure_qubit(
    state: QubitState,
) -> Tuple[int, QubitState]:
    """
    Perform one computational-basis measurement of a qubit.

    Returns:
        outcome: 0 or 1
        post_measurement_state: |0> or |1>
    """
    probabilities = state.probabilities()
    outcome = sample_from_probabilities(probabilities)

    if outcome == 0:
        return 0, QubitState(1, 0)

    return 1, QubitState(0, 1)


random.seed(7)

outcome, post_state = measure_qubit(plus)

print("Measured outcome:", outcome)
print("Post-measurement state:", post_state)


# =============================================================================
# 12. INTERFERENCE
# =============================================================================

section("12. Interference from amplitudes")

# One of the most important reasons amplitudes matter is that amplitudes add
# before probabilities are calculated.
#
# If two alternatives contribute amplitudes a and b to the same outcome:
#
#     total amplitude = a + b
#
# then:
#
#     P = |a + b|^2
#
# Expanding:
#
#     |a + b|^2
#       = |a|^2 + |b|^2 + 2 Re(a* conjugate(b))
#
# The last term is the interference term.
#
# Constructive interference increases probability.
# Destructive interference decreases probability.


def interference_probability(
    amplitude_a: complex,
    amplitude_b: complex,
) -> float:
    """Return |a + b|^2."""
    return abs(amplitude_a + amplitude_b) ** 2


constructive = interference_probability(1 / math.sqrt(2), 1 / math.sqrt(2))
destructive = interference_probability(1 / math.sqrt(2), -1 / math.sqrt(2))

print("Constructive interference:", constructive)
print("Destructive interference:", destructive)


# Classical probability would not generally treat alternatives this way.
# Quantum mechanics preserves phase information between alternatives until
# measurement or decoherence destroys the relevant coherence.


# =============================================================================
# 13. INTERFERENCE AS A FUNCTION OF PHASE
# =============================================================================

section("13. Relative phase controls interference")

# Consider two equal-amplitude contributions:
#
#     a = 1/sqrt(2)
#     b = exp(i*theta)/sqrt(2)
#
# Their combined probability depends on theta.


def two_path_interference(relative_phase: float) -> float:
    """Probability produced by two equal-amplitude paths."""
    amplitude_a = 1 / math.sqrt(2)
    amplitude_b = cmath.exp(1j * relative_phase) / math.sqrt(2)

    return abs(amplitude_a + amplitude_b) ** 2


for degrees in [0, 45, 90, 135, 180, 225, 270, 315]:
    radians = math.radians(degrees)
    probability = two_path_interference(radians)
    print(f"Phase {degrees:3d} degrees -> probability {probability:.6f}")


# The result follows:
#
#     P(theta) = 1 + cos(theta)
#
# for this particular equal-amplitude construction.


# =============================================================================
# 14. HADAMARD TRANSFORMATION
# =============================================================================

section("14. Hadamard gate and basis conversion")

# The Hadamard matrix is:
#
#              1   1
#     H = 1/sqrt(2) [     ]
#              1  -1
#
# Its important actions include:
#
#     H|0> = |+>
#     H|1> = |->
#
# and:
#
#     H|+> = |0>
#     H|-> = |1>
#
# This illustrates how a state that looks like a superposition in one basis
# can correspond to a definite state in another basis.


HADAMARD = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]


def matrix_vector_multiply(
    matrix: Sequence[Sequence[complex]],
    vector: Sequence[complex],
) -> List[complex]:
    """Multiply a rectangular matrix by a compatible vector."""
    if not matrix:
        raise ValueError("Matrix cannot be empty.")

    columns = len(matrix[0])

    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal lengths.")

    if columns != len(vector):
        raise ValueError("Matrix and vector dimensions are incompatible.")

    return [
        sum(matrix[row][column] * vector[column] for column in range(columns))
        for row in range(len(matrix))
    ]


def apply_matrix_to_qubit(
    matrix: Sequence[Sequence[complex]],
    state: QubitState,
) -> QubitState:
    """Apply a 2x2 matrix to a qubit state."""
    result = matrix_vector_multiply(
        matrix,
        [state.alpha, state.beta],
    )

    return QubitState(result[0], result[1])


print("H|0> =", apply_matrix_to_qubit(HADAMARD, zero))
print("H|1> =", apply_matrix_to_qubit(HADAMARD, one))
print("H|+> =", apply_matrix_to_qubit(HADAMARD, plus))
print("H|-> =", apply_matrix_to_qubit(HADAMARD, minus))


# =============================================================================
# 15. X, Y, Z AND PHASE GATES
# =============================================================================

section("15. Basic single-qubit gates")

# Common Pauli operators:
#
#     X = [0 1]
#         [1 0]
#
#     Y = [0 -i]
#         [i  0]
#
#     Z = [1  0]
#         [0 -1]
#
# Their actions on computational basis states include:
#
#     X|0> = |1>
#     X|1> = |0>
#
#     Z|0> = |0>
#     Z|1> = -|1>
#
# The Z operation changes relative phase without changing computational-basis
# probabilities immediately.


PAULI_X = [
    [0, 1],
    [1, 0],
]

PAULI_Y = [
    [0, -1j],
    [1j, 0],
]

PAULI_Z = [
    [1, 0],
    [0, -1],
]

PHASE_S = [
    [1, 0],
    [0, 1j],
]

PHASE_T = [
    [1, 0],
    [0, cmath.exp(1j * math.pi / 4)],
]

print("X|0> =", apply_matrix_to_qubit(PAULI_X, zero))
print("X|1> =", apply_matrix_to_qubit(PAULI_X, one))
print("Z|+> =", apply_matrix_to_qubit(PAULI_Z, plus))
print("S|+> =", apply_matrix_to_qubit(PHASE_S, plus))
print("T|+> =", apply_matrix_to_qubit(PHASE_T, plus))


# =============================================================================
# 16. UNITARY EVOLUTION
# =============================================================================

section("16. Unitary transformations")

# An isolated quantum system evolves through unitary transformations.
#
# A matrix U is unitary if:
#
#     U†U = I
#
# where U† is the conjugate transpose.
#
# Unitary evolution preserves inner products and therefore preserves
# normalization.


def conjugate_transpose(
    matrix: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    """Return the conjugate transpose of a matrix."""
    if not matrix:
        return []

    rows = len(matrix)
    columns = len(matrix[0])

    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal lengths.")

    return [
        [complex(matrix[row][column]).conjugate() for row in range(rows)]
        for column in range(columns)
    ]


def matrix_multiply(
    left: Sequence[Sequence[complex]],
    right: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    """Multiply two compatible matrices."""
    if not left or not right:
        raise ValueError("Matrices cannot be empty.")

    left_columns = len(left[0])
    right_columns = len(right[0])

    if any(len(row) != left_columns for row in left):
        raise ValueError("Left matrix is not rectangular.")

    if any(len(row) != right_columns for row in right):
        raise ValueError("Right matrix is not rectangular.")

    if left_columns != len(right):
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        [
            sum(left[i][k] * right[k][j] for k in range(left_columns))
            for j in range(right_columns)
        ]
        for i in range(len(left))
    ]


def identity_matrix(size: int) -> List[List[complex]]:
    """Create an identity matrix."""
    return [
        [
            1 if row == column else 0
            for column in range(size)
        ]
        for row in range(size)
    ]


def is_unitary(
    matrix: Sequence[Sequence[complex]],
    tolerance: float = 1e-12,
) -> bool:
    """Check U†U = I numerically."""
    if not matrix or len(matrix) != len(matrix[0]):
        return False

    product = matrix_multiply(
        conjugate_transpose(matrix),
        matrix,
    )

    identity = identity_matrix(len(matrix))

    for row in range(len(matrix)):
        for column in range(len(matrix)):
            if abs(product[row][column] - identity[row][column]) > tolerance:
                return False

    return True


print("Hadamard is unitary:", is_unitary(HADAMARD))
print("Pauli X is unitary:", is_unitary(PAULI_X))
print("Pauli Y is unitary:", is_unitary(PAULI_Y))
print("Pauli Z is unitary:", is_unitary(PAULI_Z))


# =============================================================================
# 17. BLOCH-SPHERE PARAMETERIZATION
# =============================================================================

section("17. Bloch-sphere representation")

# Every pure single-qubit state can be written, up to global phase, as:
#
#     |psi> = cos(theta/2)|0> + exp(i*phi) sin(theta/2)|1>
#
# where:
#
#     0 <= theta <= pi
#     0 <= phi < 2*pi
#
# The Bloch vector is:
#
#     x = sin(theta) cos(phi)
#     y = sin(theta) sin(phi)
#     z = cos(theta)
#
# and has length one for a pure state.


def qubit_to_bloch_vector(state: QubitState) -> Tuple[float, float, float]:
    """
    Convert a normalized qubit state into its Bloch-vector coordinates.

    For |psi> = alpha|0> + beta|1>:
        x = 2 Re(conjugate(alpha) beta)
        y = 2 Im(conjugate(alpha) beta)
        z = |alpha|^2 - |beta|^2
    """
    normalized = state.normalize()

    alpha = normalized.alpha
    beta = normalized.beta

    x = 2 * (alpha.conjugate() * beta).real
    y = 2 * (alpha.conjugate() * beta).imag
    z = abs(alpha) ** 2 - abs(beta) ** 2

    return x, y, z


for name, state in [
    ("|0>", zero),
    ("|1>", one),
    ("|+>", plus),
    ("|->", minus),
    ("phase i", states_to_compare["phase i"]),
]:
    print(f"{name:8s} -> Bloch vector {qubit_to_bloch_vector(state)}")


# =============================================================================
# 18. EXPECTATION VALUES
# =============================================================================

section("18. Observables and expectation values")

# An observable is represented by a Hermitian operator A.
#
# For a pure state:
#
#     <A> = <psi|A|psi>
#
# is the expectation value.
#
# For Pauli operators, the expectation values correspond to Bloch-vector
# coordinates:
#
#     <X> = x
#     <Y> = y
#     <Z> = z


def expectation_value(
    state: Sequence[complex],
    operator: Sequence[Sequence[complex]],
) -> complex:
    """Calculate <psi|A|psi>."""
    normalized = normalize_state(state)
    transformed = matrix_vector_multiply(operator, normalized)

    return inner_product(normalized, transformed)


bloch_test = QubitState(
    math.sqrt(0.75),
    0.5j,
)

bloch_state_vector = [bloch_test.alpha, bloch_test.beta]

print("<X> =", expectation_value(bloch_state_vector, PAULI_X))
print("<Y> =", expectation_value(bloch_state_vector, PAULI_Y))
print("<Z> =", expectation_value(bloch_state_vector, PAULI_Z))

print("Bloch vector =", qubit_to_bloch_vector(bloch_test))


# =============================================================================
# 19. DETERMINISTIC STATES VERSUS SUPERPOSITIONS
# =============================================================================

section("19. Basis states and superpositions")

# A basis state such as |0> is deterministic when measured in the
# computational basis.
#
# A superposition such as |+> produces multiple possible computational-basis
# outcomes.
#
# Importantly, "superposition" is basis-dependent. A state can be:
#
#     |0>
#
# in one basis and:
#
#     (|+> + |->)/sqrt(2)
#
# in another.


def decompose_in_hadamard_basis(state: QubitState) -> Tuple[complex, complex]:
    """
    Return amplitudes relative to |+>, |->.

    Since |+> and |-> form an orthonormal basis:
        c_plus  = <+|psi>
        c_minus = <-|psi>
    """
    plus_vector = [1 / math.sqrt(2), 1 / math.sqrt(2)]
    minus_vector = [1 / math.sqrt(2), -1 / math.sqrt(2)]

    vector = [state.alpha, state.beta]

    c_plus = inner_product(plus_vector, vector)
    c_minus = inner_product(minus_vector, vector)

    return c_plus, c_minus


print("|0> in {|+>, |->} basis:", decompose_in_hadamard_basis(zero))
print("|1> in {|+>, |->} basis:", decompose_in_hadamard_basis(one))
print("|+> in {|+>, |->} basis:", decompose_in_hadamard_basis(plus))
print("|-> in {|+>, |->} basis:", decompose_in_hadamard_basis(minus))


# =============================================================================
# 20. LINEARITY
# =============================================================================

section("20. Linearity of quantum transformations")

# Quantum gates are linear operators.
#
# If U is a quantum operation:
#
#     U(a|0> + b|1>)
#
# equals:
#
#     a U|0> + b U|1>
#
# This property is central to superposition.
#
# A gate does not need a special rule for every possible superposition.
# Its action on basis vectors plus linearity determines its action on arbitrary
# states.


def add_vectors(
    first: Sequence[complex],
    second: Sequence[complex],
) -> List[complex]:
    """Add two vectors."""
    if len(first) != len(second):
        raise ValueError("Vector dimensions must match.")

    return [a + b for a, b in zip(first, second)]


def scale_vector(
    scalar: complex,
    vector: Sequence[complex],
) -> List[complex]:
    """Multiply a vector by a scalar."""
    return [scalar * value for value in vector]


left_side = matrix_vector_multiply(
    HADAMARD,
    [
        0.6,
        0.8,
    ],
)

right_side = add_vectors(
    scale_vector(
        0.6,
        matrix_vector_multiply(HADAMARD, [1, 0]),
    ),
    scale_vector(
        0.8,
        matrix_vector_multiply(HADAMARD, [0, 1]),
    ),
)

print("U(a|0>+b|1>) =", left_side)
print("aU|0>+bU|1> =", right_side)


# =============================================================================
# 21. MULTI-QUBIT STATE SPACES
# =============================================================================

section("21. Tensor products and multi-qubit states")

# A single qubit has a two-dimensional state space.
#
# Two qubits have a four-dimensional state space:
#
#     |00>, |01>, |10>, |11>
#
# Three qubits have eight basis states.
#
# In general, n qubits require 2^n computational-basis amplitudes.
#
# This exponential growth is a central feature of quantum computing.
#
# The tensor product combines subsystem states.


def tensor_product(
    first: Sequence[complex],
    second: Sequence[complex],
) -> List[complex]:
    """Compute the Kronecker/tensor product of two state vectors."""
    return [
        first_value * second_value
        for first_value in first
        for second_value in second
    ]


two_qubit_zero_zero = tensor_product(
    [1, 0],
    [1, 0],
)

two_qubit_plus_plus = tensor_product(
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
)

print("|00> =", two_qubit_zero_zero)
print("|++> =", two_qubit_plus_plus)
print("Probability distribution for |++> =",
      measurement_probabilities(two_qubit_plus_plus))


# =============================================================================
# 22. MULTI-QUBIT SUPERPOSITION
# =============================================================================

section("22. Uniform superposition over many basis states")

# Applying H to every qubit initially in |0> produces:
#
#     H^⊗n |00...0>
#
# =   1/sqrt(2^n) sum_x |x>
#
# Every computational basis state has equal amplitude.


def uniform_superposition(number_of_qubits: int) -> List[complex]:
    """Create a normalized uniform superposition of n qubits."""
    if number_of_qubits < 0:
        raise ValueError("number_of_qubits cannot be negative.")

    dimension = 2 ** number_of_qubits
    amplitude = 1 / math.sqrt(dimension)

    return [amplitude for _ in range(dimension)]


for qubit_count in range(1, 5):
    state = uniform_superposition(qubit_count)

    print(
        f"{qubit_count} qubits -> "
        f"{len(state)} amplitudes, "
        f"probability per basis state={abs(state[0]) ** 2:.6f}"
    )


# =============================================================================
# 23. BASIS-STATE LABELING
# =============================================================================

section("23. Mapping amplitudes to computational basis states")


def basis_label(index: int, number_of_qubits: int) -> str:
    """Convert an integer basis index into an n-bit computational label."""
    if number_of_qubits < 1:
        raise ValueError("number_of_qubits must be positive.")

    dimension = 2 ** number_of_qubits

    if not 0 <= index < dimension:
        raise ValueError("Basis index is outside the state space.")

    return format(index, f"0{number_of_qubits}b")


def print_state_distribution(
    state: Sequence[complex],
    number_of_qubits: int,
    threshold: float = 1e-12,
) -> None:
    """Print non-negligible amplitudes and their probabilities."""
    expected_dimension = 2 ** number_of_qubits

    if len(state) != expected_dimension:
        raise ValueError("State dimension does not match number of qubits.")

    normalized = normalize_state(state)

    for index, amplitude in enumerate(normalized):
        probability = abs(amplitude) ** 2

        if probability > threshold:
            print(
                f"|{basis_label(index, number_of_qubits)}> : "
                f"amplitude={amplitude}, probability={probability:.6f}"
            )


print_state_distribution(two_qubit_plus_plus, 2)


# =============================================================================
# 24. PRODUCT STATES
# =============================================================================

section("24. Product states")

# A multi-qubit state is a product state if it can be written:
#
#     |psi> = |a> ⊗ |b>
#
# for its two subsystems.
#
# For example:
#
#     |+> ⊗ |1>
#
# is a product state.
#
# The amplitudes factor into amplitudes for the separate systems.


plus_one = tensor_product(
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [0, 1],
)

print("|+>|1> state:")
print_state_distribution(plus_one, 2)


# =============================================================================
# 25. ENTANGLEMENT AND SUPERPOSITION
# =============================================================================

section("25. Entanglement as a special multi-qubit structure")

# A famous entangled state is the Bell state:
#
#     |Phi+> = (|00> + |11>)/sqrt(2)
#
# It is a superposition of two joint basis states.
#
# It cannot be expressed as:
#
#     |a> ⊗ |b>
#
# for two individual single-qubit states.
#
# Entanglement and superposition are related but are not synonymous:
#
# - Superposition can exist for a single qubit.
# - Entanglement concerns non-separable correlations between subsystems.


bell_phi_plus = [
    1 / math.sqrt(2),
    0,
    0,
    1 / math.sqrt(2),
]

print("Bell state |Phi+>:")
print_state_distribution(bell_phi_plus, 2)


# =============================================================================
# 26. A SIMPLE PRODUCT-STATE TEST FOR TWO QUBITS
# =============================================================================

section("26. Detecting separability of a pure two-qubit state")

# A two-qubit state:
#
#     a|00> + b|01> + c|10> + d|11>
#
# is separable if and only if:
#
#     ad - bc = 0
#
# up to numerical precision.
#
# This criterion is specific to pure two-qubit states.


def is_product_two_qubit_state(
    state: Sequence[complex],
    tolerance: float = 1e-12,
) -> bool:
    """Check separability of a pure two-qubit state."""
    if len(state) != 4:
        raise ValueError("A two-qubit state must contain four amplitudes.")

    normalized = normalize_state(state)

    a, b, c, d = normalized

    return abs(a * d - b * c) <= tolerance


print("Is |++> a product state?",
      is_product_two_qubit_state(two_qubit_plus_plus))

print("Is Bell |Phi+> a product state?",
      is_product_two_qubit_state(bell_phi_plus))


# =============================================================================
# 27. CONTROLLED-NOT AND ENTANGLEMENT CREATION
# =============================================================================

section("27. Controlled-NOT and creation of an entangled superposition")

# The CNOT gate flips the second qubit when the first qubit is |1>.
#
# Its computational-basis mapping is:
#
#     |00> -> |00>
#     |01> -> |01>
#     |10> -> |11>
#     |11> -> |10>
#
# Starting from:
#
#     |+>|0>
#
# we have:
#
#     (|00> + |10>)/sqrt(2)
#
# Applying CNOT:
#
#     (|00> + |11>)/sqrt(2)
#
# which is entangled.


CNOT = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
]

plus_zero = tensor_product(
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1, 0],
)

bell_generated = matrix_vector_multiply(CNOT, plus_zero)

print("Initial |+>|0>:")
print_state_distribution(plus_zero, 2)

print("After CNOT:")
print_state_distribution(bell_generated, 2)

print("Entangled:", not is_product_two_qubit_state(bell_generated))


# =============================================================================
# 28. DENSITY MATRICES
# =============================================================================

section("28. Density matrices")

# A pure state |psi> can be represented by:
#
#     rho = |psi><psi|
#
# This is a density matrix.
#
# Density matrices are useful because they can represent:
#
# - pure states
# - mixed states
# - statistical uncertainty
# - subsystems of entangled systems
# - noise and decoherence


def outer_product(
    ket: Sequence[complex],
    bra: Sequence[complex],
) -> List[List[complex]]:
    """Return |ket><bra| with conjugation applied to the bra."""
    return [
        [
            ket_value * complex(bra_value).conjugate()
            for bra_value in bra
        ]
        for ket_value in ket
    ]


plus_density_matrix = outer_product(
    [plus.alpha, plus.beta],
    [plus.alpha, plus.beta],
)

print("Density matrix of |+>:")
for row in plus_density_matrix:
    print(row)


# =============================================================================
# 29. MIXED STATES
# =============================================================================

section("29. Pure versus mixed states")

# A pure state has density matrix:
#
#     rho = |psi><psi|
#
# and satisfies:
#
#     Tr(rho^2) = 1
#
# A mixed state can be represented as:
#
#     rho = sum_i p_i |psi_i><psi_i|
#
# where:
#
#     p_i >= 0
#     sum_i p_i = 1
#
# For a genuinely mixed state:
#
#     Tr(rho^2) < 1


def matrix_trace(matrix: Sequence[Sequence[complex]]) -> complex:
    """Return the trace of a square matrix."""
    if not matrix:
        raise ValueError("Matrix cannot be empty.")

    if any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Matrix must be square.")

    return sum(matrix[i][i] for i in range(len(matrix)))


def matrix_power(
    matrix: Sequence[Sequence[complex]],
    exponent: int,
) -> List[List[complex]]:
    """Compute a nonnegative integer matrix power."""
    if exponent < 0:
        raise ValueError("Exponent must be nonnegative.")

    result = identity_matrix(len(matrix))

    for _ in range(exponent):
        result = matrix_multiply(result, matrix)

    return result


pure_plus_rho = plus_density_matrix

mixed_rho = [
    [0.5, 0],
    [0, 0.5],
]

print("Purity of |+>:", matrix_trace(matrix_power(pure_plus_rho, 2)))
print("Purity of maximally mixed qubit:", matrix_trace(matrix_power(mixed_rho, 2)))


# =============================================================================
# 30. DENSITY-MATRIX MEASUREMENT PROBABILITIES
# =============================================================================

section("30. Measurement probabilities from density matrices")

# For a projective measurement operator P:
#
#     P(outcome) = Tr(P rho)
#
# For computational-basis projectors:
#
#     P0 = |0><0|
#     P1 = |1><1|


PROJECTOR_0 = [
    [1, 0],
    [0, 0],
]

PROJECTOR_1 = [
    [0, 0],
    [0, 1],
]


def matrix_elementwise_trace_product(
    left: Sequence[Sequence[complex]],
    right: Sequence[Sequence[complex]],
) -> complex:
    """Return Tr(left * right)."""
    return matrix_trace(matrix_multiply(left, right))


print(
    "P(0) for |+>:",
    matrix_elementwise_trace_product(PROJECTOR_0, pure_plus_rho),
)

print(
    "P(1) for |+>:",
    matrix_elementwise_trace_product(PROJECTOR_1, pure_plus_rho),
)


# =============================================================================
# 31. PARTIAL TRACE INTUITION
# =============================================================================

section("31. Reduced states and partial trace")

# If a two-qubit system is entangled, an individual qubit may not have a
# pure-state description even though the combined system does.
#
# For a two-qubit density matrix rho_AB, tracing out subsystem B gives:
#
#     rho_A = Tr_B(rho_AB)
#
# This produces the reduced density matrix of subsystem A.


def bell_density_matrix() -> List[List[complex]]:
    """Construct rho = |Phi+><Phi+|."""
    return outer_product(bell_phi_plus, bell_phi_plus)


def partial_trace_second_qubit(
    rho: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    """
    Partial trace over the second qubit for a 4x4 two-qubit density matrix.

    Basis ordering is assumed to be:
        |00>, |01>, |10>, |11>
    """
    if len(rho) != 4 or any(len(row) != 4 for row in rho):
        raise ValueError("Input must be a 4x4 matrix.")

    return [
        [
            rho[0][0] + rho[1][1],
            rho[0][2] + rho[1][3],
        ],
        [
            rho[2][0] + rho[3][1],
            rho[2][2] + rho[3][3],
        ],
    ]


bell_rho = bell_density_matrix()
reduced_a = partial_trace_second_qubit(bell_rho)

print("Reduced density matrix of one Bell-state qubit:")
for row in reduced_a:
    print(row)

print("Reduced-state purity:",
      matrix_trace(matrix_power(reduced_a, 2)))


# =============================================================================
# 32. SUPERPOSITION, ENTANGLEMENT AND MIXTURE: COMPARISON
# =============================================================================

section("32. Important conceptual distinctions")

# Superposition:
# A linear combination of basis states.
#
# Entanglement:
# A joint state that cannot be factored into independent subsystem states.
#
# Mixed state:
# A statistical quantum state represented by a density matrix that may not
# correspond to one definite state vector.
#
# Classical uncertainty and quantum superposition are therefore not identical.
#
# A mixture such as:
#
#     50% |0>, 50% |1>
#
# has density matrix:
#
#     [[0.5, 0],
#      [0,   0.5]]
#
# while |+> has:
#
#     [[0.5, 0.5],
#      [0.5, 0.5]]
#
# The off-diagonal terms encode coherence.


# =============================================================================
# 33. COHERENCE AND OFF-DIAGONAL TERMS
# =============================================================================

section("33. Coherence")

# The density matrix of:
#
#     |+> = (|0> + |1>)/sqrt(2)
#
# contains off-diagonal terms:
#
#     rho_01 = rho_10 = 1/2
#
# The maximally mixed state has no such coherence:
#
#     rho = [[1/2, 0],
#            [0,   1/2]]
#
# This difference is crucial for interference.


print("Pure |+> density matrix:")
for row in pure_plus_rho:
    print(row)

print("\nMixed-state density matrix:")
for row in mixed_rho:
    print(row)


# =============================================================================
# 34. DECOHERENCE MODEL
# =============================================================================

section("34. Simple phase-damping decoherence model")

# A simple phenomenological model can reduce off-diagonal coherence:
#
#     [[rho00, rho01],
#      [rho10, rho11]]
#
# becomes approximately:
#
#     [[rho00, lambda*rho01],
#      [lambda*rho10, rho11]]
#
# where:
#
#     0 <= lambda <= 1
#
# lambda = 1 means no loss of coherence.
# lambda = 0 removes the off-diagonal coherence.


def phase_damping(
    density_matrix: Sequence[Sequence[complex]],
    coherence_factor: float,
) -> List[List[complex]]:
    """
    Apply a simple phase-damping model to a 2x2 density matrix.

    This is a pedagogical noise model, not a full physical noise simulator.
    """
    if len(density_matrix) != 2 or any(len(row) != 2 for row in density_matrix):
        raise ValueError("A single-qubit 2x2 density matrix is required.")

    if not 0 <= coherence_factor <= 1:
        raise ValueError("coherence_factor must be between 0 and 1.")

    return [
        [
            density_matrix[0][0],
            coherence_factor * density_matrix[0][1],
        ],
        [
            coherence_factor * density_matrix[1][0],
            density_matrix[1][1],
        ],
    ]


for factor in [1.0, 0.75, 0.5, 0.25, 0.0]:
    noisy_state = phase_damping(pure_plus_rho, factor)

    print(f"coherence={factor}")
    for row in noisy_state:
        print(" ", row)


# =============================================================================
# 35. AMPLITUDE VECTOR SIZE AND EXPONENTIAL SCALING
# =============================================================================

section("35. Computational scaling of state vectors")

# An n-qubit pure state requires 2^n complex amplitudes in a full state-vector
# representation.
#
# The number of amplitudes grows exponentially.


def state_vector_size(number_of_qubits: int) -> int:
    """Return the number of computational-basis amplitudes for n qubits."""
    if number_of_qubits < 0:
        raise ValueError("number_of_qubits cannot be negative.")

    return 2 ** number_of_qubits


for n in [1, 2, 5, 10, 20, 30, 40, 50]:
    print(f"{n:2d} qubits -> {state_vector_size(n):,} amplitudes")


# A rough memory estimate can be made assuming 16 bytes per complex128 value.
# Real systems may require more memory because of indexing, alignment,
# temporary buffers, distributed storage, and implementation overhead.


def approximate_state_vector_memory(
    number_of_qubits: int,
    bytes_per_amplitude: int = 16,
) -> int:
    """Estimate raw state-vector memory in bytes."""
    return state_vector_size(number_of_qubits) * bytes_per_amplitude


for n in [20, 30, 40]:
    bytes_required = approximate_state_vector_memory(n)

    print(
        f"{n} qubits -> approximately "
        f"{bytes_required / (1024 ** 3):.2f} GiB of raw amplitude storage"
    )


# =============================================================================
# 36. SPARSE SUPERPOSITION
# =============================================================================

section("36. Sparse state representations")

# Not every quantum state encountered in a simulation necessarily has
# significant amplitude on every basis state.
#
# A sparse dictionary can represent only nonzero or relevant amplitudes.
#
# This can reduce memory usage for sparse states, but dense operations may
# destroy sparsity quickly.


SparseState = Dict[int, complex]


def normalize_sparse_state(state: SparseState) -> SparseState:
    """Normalize a sparse state represented as index -> amplitude."""
    norm_squared = sum(abs(amplitude) ** 2 for amplitude in state.values())

    if norm_squared <= 0:
        raise ValueError("Cannot normalize the zero state.")

    norm = math.sqrt(norm_squared)

    return {
        index: amplitude / norm
        for index, amplitude in state.items()
        if amplitude != 0
    }


sparse_state = {
    0: 1,
    7: 2j,
}

normalized_sparse = normalize_sparse_state(sparse_state)

print("Sparse normalized state:", normalized_sparse)


# =============================================================================
# 37. NUMERICAL PRECISION
# =============================================================================

section("37. Numerical precision and normalization drift")

# Quantum simulations use floating-point arithmetic.
#
# Repeated calculations can introduce tiny errors:
#
#     sum |alpha_i|^2 = 0.9999999999999998
#
# rather than exactly 1.
#
# Numerical comparisons should therefore use tolerances rather than exact
# equality.


def approximately_equal(
    first: complex,
    second: complex,
    tolerance: float = 1e-12,
) -> bool:
    """Compare numerical values using an absolute tolerance."""
    return abs(first - second) <= tolerance


print(
    "1 and 1 + 1e-14 approximately equal:",
    approximately_equal(1, 1 + 1e-14),
)

print(
    "1 and 1 + 1e-8 approximately equal:",
    approximately_equal(1, 1 + 1e-8),
)


# =============================================================================
# 38. VALIDATING A QUANTUM STATE
# =============================================================================

section("38. State validation")

# A valid pure-state vector must:
#
# 1. Have a nonzero norm.
# 2. Have finite numerical values.
# 3. Be normalizable.
#
# Normalized states must have norm one.
#
# Probabilities derived from a valid normalized state must be nonnegative and
# sum to one.


def validate_pure_state(
    state: Sequence[complex],
    tolerance: float = 1e-10,
) -> None:
    """Raise ValueError if a pure state is invalid."""
    if not state:
        raise ValueError("State vector cannot be empty.")

    for amplitude in state:
        if not math.isfinite(amplitude.real) or not math.isfinite(amplitude.imag):
            raise ValueError("State contains a non-finite amplitude.")

    norm_squared = vector_norm_squared(state)

    if norm_squared <= tolerance:
        raise ValueError("State vector cannot be the zero vector.")

    if not math.isclose(norm_squared, 1.0, abs_tol=tolerance):
        raise ValueError(
            f"State is not normalized: squared norm={norm_squared}"
        )


valid_state = [1 / math.sqrt(2), 1 / math.sqrt(2)]

validate_pure_state(valid_state)

print("Valid normalized state passed validation.")


# =============================================================================
# 39. COMMON INVALID CASES
# =============================================================================

section("39. Invalid-state examples")

invalid_states = {
    "zero vector": [0, 0],
    "wrong normalization": [1, 1],
}

for name, invalid_state in invalid_states.items():
    try:
        validate_pure_state(invalid_state)
    except ValueError as error:
        print(f"{name}: rejected -> {error}")


# =============================================================================
# 40. MEASUREMENT IN A DIFFERENT BASIS
# =============================================================================

section("40. Measuring in the Hadamard basis")

# Measuring |+> in the computational basis gives:
#
#     P(0) = P(1) = 1/2
#
# Measuring |+> in the {|+>, |->} basis gives:
#
#     P(+) = 1
#     P(-) = 0
#
# The measurement basis matters.


def basis_measurement_probabilities(
    state: Sequence[complex],
    basis_vectors: Sequence[Sequence[complex]],
) -> List[float]:
    """
    Calculate probabilities of a measurement in an orthonormal basis.

    Each basis vector is treated as a ket |b_i>, and:
        P(i) = |<b_i|psi>|^2
    """
    normalized_state = normalize_state(state)
    probabilities = []

    for basis_vector in basis_vectors:
        if len(basis_vector) != len(normalized_state):
            raise ValueError("Basis and state dimensions must match.")

        amplitude = inner_product(
            basis_vector,
            normalized_state,
        )

        probabilities.append(abs(amplitude) ** 2)

    return probabilities


hadamard_basis = [
    hadamard_plus,
    hadamard_minus,
]

print(
    "Computational measurement of |+>:",
    measurement_probabilities([plus.alpha, plus.beta]),
)

print(
    "Hadamard-basis measurement of |+>:",
    basis_measurement_probabilities(
        [plus.alpha, plus.beta],
        hadamard_basis,
    ),
)


# =============================================================================
# 41. PROJECTORS AND GENERALIZED MEASUREMENTS
# =============================================================================

section("41. Projective measurements and POVMs")

# A projective measurement uses orthogonal projectors:
#
#     P_i P_j = 0 for i != j
#
# and:
#
#     sum_i P_i = I
#
# A more general measurement can be described by POVM elements E_i satisfying:
#
#     E_i >= 0
#     sum_i E_i = I
#
# The probability is:
#
#     P(i) = Tr(E_i rho)
#
# POVMs are useful for modeling generalized measurements, detectors, and
# quantum information protocols.
#
# The implementation below checks the basic probability normalization for a
# simple two-outcome qubit POVM.


def scale_matrix(
    scalar: complex,
    matrix: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    """Scale every element of a matrix."""
    return [
        [scalar * value for value in row]
        for row in matrix
    ]


def add_matrices(
    first: Sequence[Sequence[complex]],
    second: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    """Add two matrices of identical dimensions."""
    if len(first) != len(second):
        raise ValueError("Matrix row counts must match.")

    if any(len(a) != len(b) for a, b in zip(first, second)):
        raise ValueError("Matrix column counts must match.")

    return [
        [a + b for a, b in zip(row_a, row_b)]
        for row_a, row_b in zip(first, second)
    ]


povm_e0 = scale_matrix(0.75, PROJECTOR_0)
povm_e1 = add_matrices(
    scale_matrix(0.25, PROJECTOR_0),
    PROJECTOR_1,
)

povm_probability_0 = matrix_elementwise_trace_product(
    povm_e0,
    pure_plus_rho,
)

povm_probability_1 = matrix_elementwise_trace_product(
    povm_e1,
    pure_plus_rho,
)

print("POVM probability 0:", povm_probability_0)
print("POVM probability 1:", povm_probability_1)
print("POVM probability total:", povm_probability_0 + povm_probability_1)


# =============================================================================
# 42. EXPECTATION VALUES AND VARIANCE
# =============================================================================

section("42. Observable variance")

# For observable A:
#
#     Var(A) = <A^2> - <A>^2
#
# For a Hermitian operator, the result is real up to numerical precision.


def expectation_variance(
    state: Sequence[complex],
    operator: Sequence[Sequence[complex]],
) -> Tuple[complex, complex]:
    """Return expectation value and variance of an observable."""
    expectation = expectation_value(state, operator)

    squared_operator = matrix_multiply(operator, operator)

    second_moment = expectation_value(
        state,
        squared_operator,
    )

    variance = second_moment - expectation ** 2

    return expectation, variance


expectation, variance = expectation_variance(
    [plus.alpha, plus.beta],
    PAULI_Z,
)

print("<Z> =", expectation)
print("Var(Z) =", variance)


# =============================================================================
# 43. QUANTUM INTERFERENCE THROUGH A GATE SEQUENCE
# =============================================================================

section("43. Gate sequence demonstrating interference")

# Start with |0>.
#
# H transforms it into:
#
#     |+>
#
# Z changes the relative phase:
#
#     Z|+> = |->
#
# H then converts:
#
#     H|-> = |1>
#
# Thus the final measurement is deterministic even though the intermediate
# state was a superposition.


initial = zero
after_h = apply_matrix_to_qubit(HADAMARD, initial)
after_z = apply_matrix_to_qubit(PAULI_Z, after_h)
after_second_h = apply_matrix_to_qubit(HADAMARD, after_z)

print("Initial:", initial)
print("After H:", after_h)
print("After Z:", after_z)
print("After H again:", after_second_h)
print("Final probabilities:", after_second_h.probabilities())


# This is a compact example of why relative phase matters:
#
# H|0> = |+>
# Z|+> = |->
# H|-> = |1>
#
# If the sign introduced by Z were ignored, the final result would be
# incorrectly predicted.


# =============================================================================
# 44. PHASE KICKBACK INTUITION
# =============================================================================

section("44. Phase information and phase kickback")

# Controlled operations can transfer phase information between subsystems.
#
# A complete treatment of phase kickback involves controlled-unitary
# operators, eigenstates, and relative phase. The essential lesson is that
# phase is not directly visible as a computational-basis probability but can
# become observable after interference.


def controlled_z_matrix() -> List[List[complex]]:
    """
    Return a controlled-Z matrix in basis:
        |00>, |01>, |10>, |11>
    """
    return [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, -1],
    ]


CZ = controlled_z_matrix()

two_plus = tensor_product(
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
)

after_cz = matrix_vector_multiply(CZ, two_plus)

print("Before CZ:")
print_state_distribution(two_plus, 2)

print("After CZ:")
print_state_distribution(after_cz, 2)


# =============================================================================
# 45. ORTHOGONALITY
# =============================================================================

section("45. Orthogonality")

# Two states are orthogonal if:
#
#     <phi|psi> = 0
#
# Orthogonal states can be perfectly distinguished by an appropriate
# measurement.
#
# The computational basis and Hadamard basis are both orthonormal bases.


print("<0|1> =", inner_product([1, 0], [0, 1]))
print("<+|-> =", inner_product(hadamard_plus, hadamard_minus))
print("<+|+> =", inner_product(hadamard_plus, hadamard_plus))


# =============================================================================
# 46. STATE FIDELITY
# =============================================================================

section("46. Fidelity between pure states")

# For pure states:
#
#     F(|psi>, |phi>) = |<psi|phi>|^2
#
# Fidelity equals 1 for identical physical states up to global phase and
# equals 0 for orthogonal states.


def pure_state_fidelity(
    first: Sequence[complex],
    second: Sequence[complex],
) -> float:
    """Calculate fidelity between two pure states."""
    first_normalized = normalize_state(first)
    second_normalized = normalize_state(second)

    overlap = inner_product(
        first_normalized,
        second_normalized,
    )

    return abs(overlap) ** 2


print("Fidelity(|+>, |+>):",
      pure_state_fidelity(hadamard_plus, hadamard_plus))

print("Fidelity(|+>, |->):",
      pure_state_fidelity(hadamard_plus, hadamard_minus))

print("Fidelity(|0>, |1>):",
      pure_state_fidelity(computational_zero, computational_one))


# =============================================================================
# 47. GLOBAL-PHASE FIDELITY EXAMPLE
# =============================================================================

section("47. Global phase does not change physical overlap")

phase = cmath.exp(1j * 0.8)

globally_shifted_plus = [
    phase * value
    for value in hadamard_plus
]

print(
    "Fidelity between |+> and e^(i*theta)|+>:",
    pure_state_fidelity(hadamard_plus, globally_shifted_plus),
)


# =============================================================================
# 48. QUANTUM STATE TOMOGRAPHY INTUITION
# =============================================================================

section("48. Quantum state tomography")

# A state cannot generally be reconstructed from one measurement.
#
# Repeated measurements in different bases can estimate the state.
#
# For a single qubit, measuring expectation values of X, Y, and Z allows
# reconstruction of the Bloch vector:
#
#     rho = 1/2 (I + xX + yY + zZ)
#
# for a physical single-qubit density matrix.


def bloch_density_matrix(
    x: float,
    y: float,
    z: float,
) -> List[List[complex]]:
    """Construct rho = (I + xX + yY + zZ)/2."""
    identity = identity_matrix(2)

    result = add_matrices(
        identity,
        scale_matrix(x, PAULI_X),
    )

    result = add_matrices(
        result,
        scale_matrix(y, PAULI_Y),
    )

    result = add_matrices(
        result,
        scale_matrix(z, PAULI_Z),
    )

    return scale_matrix(0.5, result)


bloch = qubit_to_bloch_vector(bloch_test)
reconstructed = bloch_density_matrix(*bloch)

print("Bloch vector:", bloch)
print("Reconstructed density matrix:")

for row in reconstructed:
    print(row)


# =============================================================================
# 49. PHYSICALITY OF A DENSITY MATRIX
# =============================================================================

section("49. Density-matrix validity conditions")

# A physical density matrix must satisfy:
#
# 1. Hermiticity:
#       rho = rho†
#
# 2. Unit trace:
#       Tr(rho) = 1
#
# 3. Positive semidefiniteness:
#       <psi|rho|psi> >= 0 for every |psi>
#
# Numerical simulations often check these properties with tolerances.


def is_hermitian(
    matrix: Sequence[Sequence[complex]],
    tolerance: float = 1e-12,
) -> bool:
    """Check numerical Hermiticity."""
    conjugate_t = conjugate_transpose(matrix)

    if len(matrix) != len(conjugate_t):
        return False

    for row_a, row_b in zip(matrix, conjugate_t):
        if len(row_a) != len(row_b):
            return False

        for a, b in zip(row_a, row_b):
            if abs(a - b) > tolerance:
                return False

    return True


def density_matrix_basic_validation(
    density_matrix: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> bool:
    """Check Hermiticity and unit trace."""
    if not density_matrix:
        return False

    if any(len(row) != len(density_matrix) for row in density_matrix):
        return False

    if not is_hermitian(density_matrix, tolerance):
        return False

    trace = matrix_trace(density_matrix)

    return abs(trace - 1) <= tolerance


print(
    "Bell density matrix basic validation:",
    density_matrix_basic_validation(bell_rho),
)

print(
    "Mixed density matrix basic validation:",
    density_matrix_basic_validation(mixed_rho),
)


# =============================================================================
# 50. COMMON MISCONCEPTIONS
# =============================================================================

section("50. Common misconceptions")

misconceptions = {
    "Superposition is just classical uncertainty":
        "False. Coherent amplitudes carry phase information that can interfere.",
    "An amplitude is a probability":
        "False. Probability is the squared magnitude of the amplitude.",
    "Every superposition is entangled":
        "False. A single qubit can be in superposition without entanglement.",
    "Global phase changes measurement probabilities":
        "False. A common global phase cancels from ordinary probabilities.",
    "The basis is irrelevant":
        "False. The amplitudes and measurement probabilities depend on the chosen basis.",
    "A measurement returns all amplitudes":
        "False. A single measurement produces one classical outcome.",
    "More qubits always mean more directly accessible information":
        "False. Measurement access remains limited and destroys or changes the state.",
}

for misconception, correction in misconceptions.items():
    print(f"{misconception}: {correction}")


# =============================================================================
# 51. COMMON IMPLEMENTATION ERRORS
# =============================================================================

section("51. Common programming errors")

# Error 1: treating amplitudes as probabilities.
#
# Wrong conceptual operation:
#
#     probability = amplitude
#
# Correct:
#
#     probability = abs(amplitude)**2
#
# Error 2: forgetting normalization.
#
# Error 3: using ordinary multiplication instead of tensor products for
# multi-qubit states.
#
# Error 4: comparing floating-point values with ==.
#
# Error 5: forgetting complex conjugation in inner products.
#
# Error 6: accidentally modifying a state in place when a separate state is
# expected.
#
# Error 7: assuming computational-basis probabilities contain all phase
# information.


complex_amplitude = 0.3 + 0.4j

print("Amplitude:", complex_amplitude)
print("Incorrect if treated as probability:", complex_amplitude)
print("Correct probability:", abs(complex_amplitude) ** 2)


# =============================================================================
# 52. EDGE CASES
# =============================================================================

section("52. Important edge cases")

edge_cases = [
    ("Zero vector", [0j, 0j]),
    ("Already normalized", [1 + 0j, 0 + 0j]),
    ("Purely imaginary amplitude", [1j / math.sqrt(2), 1 / math.sqrt(2)]),
    ("Negative amplitude", [1 / math.sqrt(2), -1 / math.sqrt(2)]),
]

for name, state in edge_cases:
    print(name)

    try:
        normalized_state = normalize_state(state)
        print(" normalized:", normalized_state)
        print(" probabilities:", measurement_probabilities(state))
    except ValueError as error:
        print(" rejected:", error)


# =============================================================================
# 53. PHASE PERIODICITY
# =============================================================================

section("53. Phase periodicity")

# Complex phase is periodic:
#
#     e^(i(theta + 2*pi)) = e^(i*theta)
#
# Thus phases differing by integer multiples of 2*pi represent the same
# complex number.


theta = 0.73

print(
    "e^(i*theta):",
    cmath.exp(1j * theta),
)

print(
    "e^(i*(theta+2*pi)):",
    cmath.exp(1j * (theta + 2 * math.pi)),
)

print(
    "Numerically equal:",
    abs(
        cmath.exp(1j * theta)
        - cmath.exp(1j * (theta + 2 * math.pi))
    ) < 1e-12,
)


# =============================================================================
# 54. AMPLITUDE ADDITION VERSUS PROBABILITY ADDITION
# =============================================================================

section("54. Why quantum paths cannot always be treated as classical probabilities")

# If alternatives are indistinguishable and coherent, amplitudes add:
#
#     A = A1 + A2
#     P = |A|^2
#
# If which-path information makes alternatives distinguishable, interference
# can disappear and the corresponding probabilities can behave as a mixture.
#
# The important question is not simply "how many paths exist?" but whether
# coherent alternatives contribute to the same observable outcome.


a1 = 1 / math.sqrt(2)
a2 = 1 / math.sqrt(2)

coherent_probability = abs(a1 + a2) ** 2
incoherent_probability = abs(a1) ** 2 + abs(a2) ** 2

print("Coherent amplitude addition:", coherent_probability)
print("Incoherent probability addition:", incoherent_probability)


# =============================================================================
# 55. QUANTUM CIRCUIT STATE EVOLUTION
# =============================================================================

section("55. Simple state-vector quantum circuit simulator")

# The following class provides a compact educational simulator for small
# circuits. It supports:
#
# - state-vector storage
# - arbitrary single-qubit gates
# - measurement probabilities
# - computational-basis measurement
#
# It is intentionally small and transparent rather than optimized.


class QuantumRegisterSimulator:
    """Educational state-vector simulator for a small quantum register."""

    def __init__(self, number_of_qubits: int):
        if number_of_qubits < 1:
            raise ValueError("At least one qubit is required.")

        self.number_of_qubits = number_of_qubits
        self.dimension = 2 ** number_of_qubits

        self.state = [0j] * self.dimension
        self.state[0] = 1 + 0j

    def probabilities(self) -> List[float]:
        """Return computational-basis probabilities."""
        return measurement_probabilities(self.state)

    def apply_single_qubit_gate(
        self,
        gate: Sequence[Sequence[complex]],
        target_qubit: int,
    ) -> None:
        """
        Apply a 2x2 gate to one qubit.

        Qubit indexing uses the leftmost bit as qubit 0 in displayed labels.
        """
        if not 0 <= target_qubit < self.number_of_qubits:
            raise ValueError("target_qubit is outside the register.")

        if len(gate) != 2 or any(len(row) != 2 for row in gate):
            raise ValueError("A single-qubit gate must be 2x2.")

        bit_position = self.number_of_qubits - 1 - target_qubit
        mask = 1 << bit_position

        new_state = [0j] * self.dimension

        for index in range(self.dimension):
            bit = 1 if index & mask else 0

            partner = index ^ mask

            if bit == 0:
                new_state[index] += (
                    gate[0][0] * self.state[index]
                    + gate[0][1] * self.state[partner]
                )
            else:
                new_state[index] += (
                    gate[1][0] * self.state[partner]
                    + gate[1][1] * self.state[index]
                )

        self.state = new_state

    def measure(self) -> int:
        """Measure the entire register in the computational basis."""
        probabilities = self.probabilities()
        outcome = sample_from_probabilities(probabilities)

        # Project the state onto the observed basis state.
        self.state = [0j] * self.dimension
        self.state[outcome] = 1 + 0j

        return outcome

    def print_state(self, threshold: float = 1e-12) -> None:
        """Print the non-negligible amplitudes."""
        print_state_distribution(
            self.state,
            self.number_of_qubits,
            threshold,
        )


simulator = QuantumRegisterSimulator(2)

simulator.apply_single_qubit_gate(HADAMARD, 0)

print("After H on qubit 0:")
simulator.print_state()

print("Probabilities:", simulator.probabilities())


# =============================================================================
# 56. TWO-QUBIT CONTROLLED OPERATIONS
# =============================================================================

section("56. Adding CNOT to the simulator")

# A direct CNOT implementation shows how multi-qubit operations act on
# amplitudes.


class TwoQubitSimulator(QuantumRegisterSimulator):
    """Two-qubit extension with a CNOT operation."""

    def __init__(self):
        super().__init__(2)

    def apply_cnot(
        self,
        control_qubit: int,
        target_qubit: int,
    ) -> None:
        """Apply CNOT to a two-qubit register."""
        if control_qubit == target_qubit:
            raise ValueError("Control and target must differ.")

        if not {
            control_qubit,
            target_qubit,
        }.issubset({0, 1}):
            raise ValueError("Qubit indices must be 0 or 1.")

        control_bit_position = 1 - control_qubit
        target_bit_position = 1 - target_qubit

        control_mask = 1 << control_bit_position
        target_mask = 1 << target_bit_position

        new_state = self.state.copy()

        for index in range(self.dimension):
            if index & control_mask:
                partner = index ^ target_mask

                if index < partner:
                    new_state[index] = self.state[partner]
                    new_state[partner] = self.state[index]

        self.state = new_state


two_qubit_simulator = TwoQubitSimulator()

two_qubit_simulator.apply_single_qubit_gate(HADAMARD, 0)
two_qubit_simulator.apply_cnot(0, 1)

print("Bell-state circuit H(0) then CNOT(0,1):")
two_qubit_simulator.print_state()

print(
    "Is final state entangled:",
    not is_product_two_qubit_state(two_qubit_simulator.state),
)


# =============================================================================
# 57. SHOT-BASED CIRCUIT SIMULATION
# =============================================================================

section("57. Repeated circuit measurements")

random.seed(1234)

shot_count = 1000
bell_counts = {
    0: 0,
    1: 0,
    2: 0,
    3: 0,
}

for _ in range(shot_count):
    circuit = TwoQubitSimulator()

    circuit.apply_single_qubit_gate(HADAMARD, 0)
    circuit.apply_cnot(0, 1)

    outcome = circuit.measure()

    bell_counts[outcome] += 1

for index, count in bell_counts.items():
    print(
        f"|{basis_label(index, 2)}> -> "
        f"{count} shots ({count / shot_count:.3f})"
    )


# Ideally, only |00> and |11> occur, each close to 50%.


# =============================================================================
# 58. SUPERPOSITION IN ALGORITHMS
# =============================================================================

section("58. Superposition in quantum algorithms")

# Superposition is useful because a quantum circuit can create amplitudes over
# many basis states.
#
# A quantum algorithm then manipulates amplitudes so that:
#
# - amplitudes of useful outcomes can interfere constructively
# - amplitudes of unwanted outcomes can interfere destructively
#
# The final measurement samples from the resulting distribution.
#
# Superposition alone does not mean that all computational answers are
# simultaneously readable.
#
# The algorithm must engineer a useful measurement distribution.


def grover_like_amplitude_amplification_example() -> List[float]:
    """
    A tiny numerical illustration of amplitude amplification.

    This is not a complete Grover implementation. It demonstrates only the
    principle that redistributing amplitudes can increase the probability of
    a selected outcome.
    """
    return [
        math.sqrt(0.05),
        math.sqrt(0.95),
    ]


amplified_example = grover_like_amplitude_amplification_example()

print(
    "Illustrative amplified amplitudes:",
    amplified_example,
)

print(
    "Illustrative probabilities:",
    measurement_probabilities(amplified_example),
)


# =============================================================================
# 59. PHASE ESTIMATION INTUITION
# =============================================================================

section("59. Phase as useful computational information")

# Quantum algorithms can encode information into relative phase.
#
# Phase estimation, interference-based algorithms, and Fourier-transform-based
# methods demonstrate that a phase which is not directly visible in a single
# computational-basis measurement can become measurable after an appropriate
# transformation.
#
# The key pattern is:
#
#     encode phase -> interfere -> measure


phase_encoded = QubitState(
    1 / math.sqrt(2),
    cmath.exp(1j * math.pi / 3) / math.sqrt(2),
)

print("Phase-encoded state:", phase_encoded)
print("Computational probabilities:", phase_encoded.probabilities())

phase_interfered = apply_matrix_to_qubit(
    HADAMARD,
    phase_encoded,
)

print("After Hadamard:", phase_interfered)
print("After-Hadamard probabilities:", phase_interfered.probabilities())


# =============================================================================
# 60. QUANTUM FOURIER TRANSFORM INTUITION
# =============================================================================

section("60. Fourier structure and amplitudes")

# The quantum Fourier transform changes the amplitude representation of a
# state using a unitary discrete Fourier transform.
#
# For dimension N:
#
#     QFT|x> = 1/sqrt(N) sum_y exp(2*pi*i*x*y/N) |y>
#
# The phase factors are what allow interference to reveal periodic structure.


def qft(state: Sequence[complex]) -> List[complex]:
    """
    Compute the normalized quantum Fourier transform of a state vector.

    This direct implementation is O(N^2) and intended for education.
    """
    normalized = normalize_state(state)
    n = len(normalized)

    if n == 0:
        raise ValueError("State cannot be empty.")

    result = []

    for y in range(n):
        amplitude = 0j

        for x in range(n):
            angle = 2 * math.pi * x * y / n

            amplitude += (
                normalized[x]
                * cmath.exp(1j * angle)
            )

        result.append(amplitude / math.sqrt(n))

    return result


qft_input = [1, 0, 0, 0]

print("QFT input:", qft_input)
print("QFT output:", qft(qft_input))


# =============================================================================
# 61. QFT PROBABILITY CONSERVATION
# =============================================================================

section("61. Unitary transforms preserve total probability")

qft_example = qft([
    1,
    2,
    3,
    4,
])

qft_probabilities = measurement_probabilities(qft_example)

print("QFT probabilities:", qft_probabilities)
print("Probability total:", sum(qft_probabilities))


# =============================================================================
# 62. ENTANGLEMENT AND LOCAL MEASUREMENT CORRELATIONS
# =============================================================================

section("62. Bell-state measurement correlations")

# In |Phi+>:
#
#     |Phi+> = (|00> + |11>)/sqrt(2)
#
# measuring both qubits in the computational basis always gives matching
# results:
#
#     00 or 11
#
# each with probability 1/2.
#
# This correlation is stronger than what would be represented by two
# independently prepared random bits in the same way.


random.seed(99)

bell_measurement_counts = {
    "00": 0,
    "01": 0,
    "10": 0,
    "11": 0,
}

bell_probabilities = measurement_probabilities(bell_phi_plus)

for _ in range(10_000):
    outcome = sample_from_probabilities(bell_probabilities)
    label = basis_label(outcome, 2)
    bell_measurement_counts[label] += 1

print("Bell-state measurement counts:")
for label, count in bell_measurement_counts.items():
    print(label, count)


# =============================================================================
# 63. LOCAL STATES OF AN ENTANGLED SYSTEM
# =============================================================================

section("63. Why an entangled subsystem can look mixed")

# The Bell state is pure as a two-qubit state:
#
#     Tr(rho_AB^2) = 1
#
# but either individual qubit has reduced state:
#
#     I/2
#
# whose purity is 1/2.
#
# Thus "the total system is pure" and "the subsystem is mixed" can both be
# true.


print("Bell-state total purity:",
      matrix_trace(matrix_power(bell_rho, 2)))

print("Single-qubit reduced purity:",
      matrix_trace(matrix_power(reduced_a, 2)))


# =============================================================================
# 64. SUPERPOSITION UNDER GLOBAL PHASE
# =============================================================================

section("64. Explicit global-phase comparison")

theta = math.pi / 5

state_a = QubitState(
    1 / math.sqrt(2),
    1j / math.sqrt(2),
)

global_factor = cmath.exp(1j * theta)

state_b = QubitState(
    global_factor * state_a.alpha,
    global_factor * state_a.beta,
)

print("State A:", state_a)
print("State B:", state_b)

print("A probabilities:", state_a.probabilities())
print("B probabilities:", state_b.probabilities())

print(
    "Fidelity:",
    pure_state_fidelity(
        [state_a.alpha, state_a.beta],
        [state_b.alpha, state_b.beta],
    ),
)


# =============================================================================
# 65. RELATIVE-PHASE COMPARISON
# =============================================================================

section("65. Explicit relative-phase comparison")

state_plus = QubitState(
    1 / math.sqrt(2),
    1 / math.sqrt(2),
)

state_minus = QubitState(
    1 / math.sqrt(2),
    -1 / math.sqrt(2),
)

print("|+> computational probabilities:", state_plus.probabilities())
print("|-> computational probabilities:", state_minus.probabilities())

print(
    "|+> Hadamard-basis probabilities:",
    basis_measurement_probabilities(
        [state_plus.alpha, state_plus.beta],
        hadamard_basis,
    ),
)

print(
    "|-> Hadamard-basis probabilities:",
    basis_measurement_probabilities(
        [state_minus.alpha, state_minus.beta],
        hadamard_basis,
    ),
)


# =============================================================================
# 66. NORMALIZATION AFTER SUPERPOSITION
# =============================================================================

section("66. Building superpositions safely")

# If basis states are orthonormal:
#
#     |psi> = a|0> + b|1>
#
# is normalized when:
#
#     |a|^2 + |b|^2 = 1.
#
# If coefficients are supplied arbitrarily, normalize them explicitly.


def create_superposition(
    amplitudes: Sequence[complex],
) -> List[complex]:
    """Create a normalized superposition from arbitrary coefficients."""
    if not amplitudes:
        raise ValueError("At least one amplitude is required.")

    return normalize_state(amplitudes)


custom_superposition = create_superposition([
    2,
    1j,
    -1,
])

print("Custom normalized superposition:")
print(custom_superposition)
print("Probabilities:", measurement_probabilities(custom_superposition))


# =============================================================================
# 67. BASIS CHANGE USING A UNITARY MATRIX
# =============================================================================

section("67. General basis transformations")

# If B is a unitary matrix whose columns are basis vectors, amplitudes in the
# B-basis can be obtained through:
#
#     c_B = B† c_standard
#
# The transformation preserves norm because B is unitary.


def change_basis(
    state: Sequence[complex],
    basis_matrix: Sequence[Sequence[complex]],
) -> List[complex]:
    """Express a state in the basis represented by matrix columns."""
    return matrix_vector_multiply(
        conjugate_transpose(basis_matrix),
        normalize_state(state),
    )


hadamard_columns = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]

print(
    "|0> coefficients in Hadamard basis:",
    change_basis(
        [1, 0],
        hadamard_columns,
    ),
)

print(
    "|+> coefficients in Hadamard basis:",
    change_basis(
        hadamard_plus,
        hadamard_columns,
    ),
)


# =============================================================================
# 68. PERFORMANCE CONSIDERATIONS
# =============================================================================

section("68. Performance considerations")

# Dense state-vector simulation has exponential memory complexity:
#
#     O(2^n)
#
# A generic dense matrix representing an n-qubit operator has:
#
#     O(4^n)
#
# entries.
#
# This is why practical simulators generally apply gates locally rather than
# explicitly constructing a full dense 2^n x 2^n matrix for every gate.
#
# The educational code above favors clarity over high performance.
#
# Direct QFT:
#
#     O(N^2)
#
# Fast Fourier Transform style implementations can reduce this to:
#
#     O(N log N)
#
# subject to the structure of the transform and implementation.


for n in [10, 15, 20]:
    dimension = 2 ** n
    dense_operator_elements = dimension ** 2

    print(
        f"{n} qubits: state amplitudes={dimension:,}, "
        f"dense operator elements={dense_operator_elements:,}"
    )


# =============================================================================
# 69. MEMORY AND PRECISION TRADE-OFFS
# =============================================================================

section("69. Numerical representation trade-offs")

# Complex double precision is common because amplitudes require real and
# imaginary components.
#
# Lower precision can reduce memory and sometimes increase performance, but
# can introduce greater numerical error.
#
# Higher precision can improve accuracy but increases computational cost.
#
# The appropriate choice depends on:
#
# - circuit depth
# - condition numbers
# - algorithm sensitivity
# - hardware
# - required error tolerance


def memory_estimate(
    number_of_qubits: int,
    bytes_per_complex_amplitude: int,
) -> float:
    """Return raw memory estimate in GiB."""
    return (
        state_vector_size(number_of_qubits)
        * bytes_per_complex_amplitude
        / (1024 ** 3)
    )


for bytes_per_value in [8, 16]:
    print(
        f"30 qubits at {bytes_per_value} bytes/amplitude: "
        f"{memory_estimate(30, bytes_per_value):.2f} GiB"
    )


# =============================================================================
# 70. SECURITY AND CORRECTNESS CONSIDERATIONS
# =============================================================================

section("70. Security and correctness considerations")

# Quantum-state simulation is primarily a scientific/numerical correctness
# problem rather than a conventional application-security problem.
#
# Important implementation concerns include:
#
# - validating dimensions
# - rejecting invalid states
# - avoiding silent renormalization when validation is expected
# - using numerical tolerances
# - checking unitary operators
# - checking probability normalization
# - controlling random seeds for reproducible tests
# - avoiding accidental mutation of shared state
# - documenting basis ordering
# - documenting qubit-index conventions
#
# For cryptographic or security-sensitive applications, a toy random-number
# generator should not be substituted for a cryptographically secure source
# without an explicit security analysis.


# =============================================================================
# 71. TESTING FUNDAMENTAL PROPERTIES
# =============================================================================

section("71. Automated property checks")

# Scientific software benefits from testing mathematical invariants.


def assert_probability_distribution(
    probabilities: Sequence[float],
    tolerance: float = 1e-10,
) -> None:
    """Assert that probabilities form a valid distribution."""
    if any(probability < -tolerance for probability in probabilities):
        raise AssertionError("Negative probability detected.")

    if not math.isclose(
        sum(probabilities),
        1.0,
        abs_tol=tolerance,
    ):
        raise AssertionError("Probabilities do not sum to one.")


def run_core_tests() -> None:
    """Run core correctness checks."""
    # Normalization
    assert math.isclose(
        vector_norm_squared([1 / math.sqrt(2), 1 / math.sqrt(2)]),
        1.0,
        abs_tol=1e-12,
    )

    # Orthogonality
    assert abs(inner_product([1, 0], [0, 1])) < 1e-12

    # Hadamard transformation
    transformed_zero = apply_matrix_to_qubit(HADAMARD, zero)
    assert transformed_zero.is_normalized()

    # Unitarity
    assert is_unitary(HADAMARD)
    assert is_unitary(PAULI_X)
    assert is_unitary(PAULI_Y)
    assert is_unitary(PAULI_Z)

    # Probabilities
    assert_probability_distribution(
        measurement_probabilities([1, 1j, 2])
    )

    # Bell state
    assert not is_product_two_qubit_state(bell_phi_plus)

    # Product state
    assert is_product_two_qubit_state(two_qubit_plus_plus)

    # QFT
    qft_probabilities = measurement_probabilities(
        qft([1, 0, 0, 0])
    )
    assert_probability_distribution(qft_probabilities)

    print("All core tests passed.")


run_core_tests()


# =============================================================================
# 72. REPRODUCIBILITY
# =============================================================================

section("72. Reproducible measurement experiments")

# Quantum measurement simulation uses pseudorandom sampling in this educational
# program. Setting a seed makes results reproducible.
#
# A seed is useful for:
#
# - debugging
# - automated testing
# - comparing algorithm implementations
# - teaching
#
# It does not turn pseudorandom simulation into physical quantum randomness.


random.seed(2026)

reproducible_counts = simulate_measurements(
    [math.sqrt(0.25), math.sqrt(0.75)],
    1000,
)

print("Reproducible counts:", reproducible_counts)


# =============================================================================
# 73. PRODUCTION CONSIDERATIONS
# =============================================================================

section("73. Production-oriented design considerations")

# A production-quality quantum simulation system typically needs more than the
# educational primitives shown here.
#
# Important design areas include:
#
# 1. Efficient memory layout
# 2. Vectorized numerical kernels
# 3. Parallel execution
# 4. GPU acceleration
# 5. Distributed state-vector simulation
# 6. Sparse representations where appropriate
# 7. Stabilizer or tensor-network methods for special circuit families
# 8. Noise models
# 9. Measurement and sampling infrastructure
# 10. Deterministic testing
# 11. Numerical stability
# 12. Clear basis and endian conventions
#
# The best representation depends strongly on the quantum state and circuit
# structure.


# =============================================================================
# 74. STABILIZER-SPECIFIC OBSERVATION
# =============================================================================

section("74. Why specialized representations can outperform dense vectors")

# Some quantum circuits, particularly Clifford circuits, have structure that
# allows efficient classical simulation without storing every amplitude
# explicitly.
#
# This does not contradict exponential state-space dimension.
#
# It means that particular families of states and operations possess compact
# mathematical descriptions.
#
# Similar specialized approaches include:
#
# - stabilizer tableaux
# - tensor networks
# - decision diagrams
# - low-rank approximations
#
# Dense state vectors remain a general and conceptually direct representation.


# =============================================================================
# 75. TENSOR-PRODUCT DIMENSION
# =============================================================================

section("75. Tensor-product dimensionality")

# If system A has dimension d_A and system B has dimension d_B, the combined
# system has dimension:
#
#     d_A * d_B
#
# For n qubits:
#
#     2 * 2 * ... * 2 = 2^n


dimensions = [2, 2, 2, 2]

combined_dimension = 1

for dimension in dimensions:
    combined_dimension *= dimension

print("Four qubit tensor-product dimension:", combined_dimension)


# =============================================================================
# 76. MULTI-QUBIT SUPERPOSITION WITH COMPLEX PHASES
# =============================================================================

section("76. Complex phases in a multi-qubit superposition")

# Consider:
#
#     |psi> = 1/2(
#         |00> + |01> + i|10> - |11>
#     )
#
# Every basis state has probability 1/4 in the computational basis, but the
# phase pattern affects how the state behaves under later gates.


complex_two_qubit_state = [
    0.5,
    0.5,
    0.5j,
    -0.5,
]

print_state_distribution(complex_two_qubit_state, 2)


# =============================================================================
# 77. PHASE PATTERN AFTER A TRANSFORMATION
# =============================================================================

section("77. Phase patterns become observable through interference")

# Apply H to the first qubit of the phase-pattern state using the simulator.


phase_pattern_simulator = QuantumRegisterSimulator(2)
phase_pattern_simulator.state = complex_two_qubit_state.copy()

phase_pattern_simulator.apply_single_qubit_gate(
    HADAMARD,
    0,
)

print("After Hadamard on first qubit:")
phase_pattern_simulator.print_state()

print(
    "Probabilities:",
    phase_pattern_simulator.probabilities(),
)


# =============================================================================
# 78. MEASUREMENT EXPECTATION FROM AMPLITUDES
# =============================================================================

section("78. Computing measurement statistics directly")

# For computational basis:
#
#     E[f(X)] = sum_x f(x) |alpha_x|^2
#
# where f assigns a numerical value to each basis outcome.


def expected_classical_value_from_state(
    state: Sequence[complex],
    values: Sequence[float],
) -> float:
    """Calculate the expected value of a classical function of outcomes."""
    probabilities = measurement_probabilities(state)

    if len(values) != len(probabilities):
        raise ValueError("values and state dimensions must match.")

    return sum(
        probability * value
        for probability, value in zip(probabilities, values)
    )


expected_index = expected_classical_value_from_state(
    complex_two_qubit_state,
    [0, 1, 2, 3],
)

print("Expected basis index:", expected_index)


# =============================================================================
# 79. AMPLITUDE SIGN AS INFORMATION
# =============================================================================

section("79. Negative and complex amplitudes carry information")

# Classical probabilities cannot be negative.
#
# Quantum amplitudes can have negative or complex values.
#
# The sign or phase does not directly represent a negative probability.
# Instead, it affects interference when amplitudes are combined by quantum
# operations.


positive_superposition = QubitState(
    1 / math.sqrt(2),
    1 / math.sqrt(2),
)

negative_superposition = QubitState(
    1 / math.sqrt(2),
    -1 / math.sqrt(2),
)

print("Positive state:", positive_superposition)
print("Negative-relative-phase state:", negative_superposition)

print(
    "Same computational probabilities:",
    positive_superposition.probabilities()
    == negative_superposition.probabilities(),
)

print(
    "Different Hadamard probabilities:",
    basis_measurement_probabilities(
        [positive_superposition.alpha, positive_superposition.beta],
        hadamard_basis,
    ),
    basis_measurement_probabilities(
        [negative_superposition.alpha, negative_superposition.beta],
        hadamard_basis,
    ),
)


# =============================================================================
# 80. SUPERPOSITION AND LINEAR COMBINATIONS
# =============================================================================

section("80. General finite-dimensional superposition")

# For an orthonormal basis {|0>, |1>, ..., |d-1>}:
#
#     |psi> = c0|0> + c1|1> + ... + c(d-1)|d-1>
#
# with:
#
#     sum_i |ci|^2 = 1.
#
# A qubit is simply the d=2 case.


def describe_general_superposition(
    state: Sequence[complex],
) -> None:
    """Print a finite-dimensional state in ket notation."""
    normalized = normalize_state(state)

    for index, amplitude in enumerate(normalized):
        probability = abs(amplitude) ** 2

        print(
            f"|{index}>: amplitude={amplitude}, "
            f"probability={probability:.6f}"
        )


describe_general_superposition([
    1,
    1j,
    1,
    -1j,
])


# =============================================================================
# 81. UNITARY REVERSIBILITY
# =============================================================================

section("81. Reversibility of unitary evolution")

# Every unitary matrix has an inverse:
#
#     U^-1 = U†
#
# Therefore:
#
#     U†U = I
#
# A unitary operation is reversible.
#
# Measurement is different: it generally is not reversible because the
# classical outcome does not contain the complete pre-measurement quantum
# state.


hadamard_inverse = conjugate_transpose(HADAMARD)

print("H inverse:")
for row in hadamard_inverse:
    print(row)

print(
    "H inverse equals H numerically:",
    all(
        abs(hadamard_inverse[i][j] - HADAMARD[i][j]) < 1e-12
        for i in range(2)
        for j in range(2)
    ),
)


# =============================================================================
# 82. MEASUREMENT DESTROYS COHERENT INFORMATION
# =============================================================================

section("82. Measurement versus coherent evolution")

# Before measurement, a state can contain relative-phase information.
#
# After computational-basis measurement, the state has been projected onto a
# basis outcome in the ideal projective-measurement model.
#
# Repeating a measurement does not recover the original superposition.
#
# This is why quantum algorithms must perform interference before final
# measurement.


pre_measurement = plus

random.seed(321)

outcome, collapsed = measure_qubit(pre_measurement)

print("Before measurement:", pre_measurement)
print("Outcome:", outcome)
print("After measurement:", collapsed)


# =============================================================================
# 83. SUPERPOSITION AND INFORMATION ACCESS
# =============================================================================

section("83. Why superposition does not mean unlimited classical parallelism")

# A state such as:
#
#     sum_x alpha_x |x>
#
# contains amplitudes for many basis states.
#
# But a single measurement produces one outcome.
#
# Therefore a useful quantum algorithm must transform the amplitudes so that
# the desired information appears with sufficiently high probability.
#
# Quantum advantage, where present, arises from the structure of quantum
# evolution, interference, entanglement, and measurement, not merely from
# writing many basis states in a superposition.


uniform_three_qubit = uniform_superposition(3)

print("Three-qubit uniform superposition dimension:",
      len(uniform_three_qubit))

print("Probability of each basis state:",
      abs(uniform_three_qubit[0]) ** 2)


# =============================================================================
# 84. PHYSICAL INTERPRETATION OF AMPLITUDE
# =============================================================================

section("84. Interpretation of quantum amplitudes")

# A probability amplitude is a complex coefficient in a quantum state.
#
# It is not directly a detector reading.
#
# Its measurable role appears through:
#
# - squared magnitudes for probabilities
# - inner products for overlaps
# - relative phases for interference
# - expectation values
# - density-matrix coherence
# - transformations under unitary operators
#
# This is the operationally important meaning of amplitudes.


# =============================================================================
# 85. FINAL INTEGRATED EXAMPLE
# =============================================================================

section("85. Integrated example: superposition, phase, interference, measurement")

# Goal:
#
# 1. Start with |0>.
# 2. Create superposition using H.
# 3. Apply a relative phase using Z.
# 4. Interfere using H again.
# 5. Measure.
#
# Mathematically:
#
#     |0>
#       -> H
#     |+>
#       -> Z
#     |->
#       -> H
#     |1>
#
# This compact circuit captures the essential role of quantum amplitudes.

integrated_state = zero

print("Step 1:", integrated_state)

integrated_state = apply_matrix_to_qubit(
    HADAMARD,
    integrated_state,
)

print("Step 2 after H:", integrated_state)
print("Probabilities:", integrated_state.probabilities())

integrated_state = apply_matrix_to_qubit(
    PAULI_Z,
    integrated_state,
)

print("Step 3 after Z:", integrated_state)
print("Probabilities:", integrated_state.probabilities())

integrated_state = apply_matrix_to_qubit(
    HADAMARD,
    integrated_state,
)

print("Step 4 after H:", integrated_state)
print("Final probabilities:", integrated_state.probabilities())


# =============================================================================
# 86. CORE FORMULAS
# =============================================================================

section("86. Core formulas")

# The most important mathematical relationships covered in this script are:
#
# Qubit state:
#
#     |psi> = alpha|0> + beta|1>
#
# Normalization:
#
#     |alpha|^2 + |beta|^2 = 1
#
# Born rule:
#
#     P(i) = |alpha_i|^2
#
# Inner product:
#
#     <phi|psi> = sum_i conjugate(phi_i) psi_i
#
# Expectation:
#
#     <A> = <psi|A|psi>
#
# Variance:
#
#     Var(A) = <A^2> - <A>^2
#
# Density matrix:
#
#     rho = |psi><psi|
#
# General measurement:
#
#     P(i) = Tr(E_i rho)
#
# Bloch vector:
#
#     x = 2 Re(conjugate(alpha) beta)
#     y = 2 Im(conjugate(alpha) beta)
#     z = |alpha|^2 - |beta|^2
#
# Tensor-product dimension:
#
#     dim(H_A tensor H_B) = dim(H_A) * dim(H_B)
#
# n-qubit state dimension:
#
#     2^n


formulas = [
    "|psi> = alpha|0> + beta|1>",
    "|alpha|^2 + |beta|^2 = 1",
    "P(i) = |alpha_i|^2",
    "<phi|psi> = sum conjugate(phi_i) * psi_i",
    "<A> = <psi|A|psi>",
    "Var(A) = <A^2> - <A>^2",
    "rho = |psi><psi|",
    "P(i) = Tr(E_i rho)",
    "dim(n qubits) = 2^n",
]

for formula in formulas:
    print(formula)


# =============================================================================
# 87. TERMINOLOGY REFERENCE
# =============================================================================

section("87. Terminology reference")

terms = {
    "Quantum state":
        "Mathematical description of a quantum system.",
    "Amplitude":
        "Complex coefficient associated with a basis state.",
    "Probability amplitude":
        "Amplitude whose squared magnitude determines measurement probability.",
    "Superposition":
        "Linear combination of basis states.",
    "Basis":
        "A complete orthonormal set used to represent states.",
    "Normalization":
        "Condition that total probability equals one.",
    "Born rule":
        "Rule assigning squared amplitude magnitude to measurement probability.",
    "Relative phase":
        "Phase difference between components that can affect interference.",
    "Global phase":
        "Common phase factor that does not change physical measurement predictions.",
    "Interference":
        "Combination of amplitudes that can increase or decrease probabilities.",
    "Unitary":
        "A norm-preserving reversible linear transformation.",
    "Measurement":
        "Physical operation producing an outcome according to quantum probabilities.",
    "Density matrix":
        "Operator representation of pure or mixed quantum states.",
    "Coherence":
        "Phase-sensitive off-diagonal structure in a density matrix.",
    "Entanglement":
        "Non-separable structure of a composite quantum state.",
    "Tensor product":
        "Mathematical operation combining subsystem state spaces.",
    "Observable":
        "Hermitian operator representing a measurable quantity.",
    "POVM":
        "Generalized measurement represented by positive operators summing to identity.",
    "Bloch sphere":
        "Geometric representation of pure single-qubit states up to global phase.",
}

for term, definition in terms.items():
    print(f"{term}: {definition}")


# =============================================================================
# 88. FINAL VALIDATION
# =============================================================================

section("88. Final mathematical validation")

# Validate several central states and operations.


central_states = {
    "|0>": [1, 0],
    "|1>": [0, 1],
    "|+>": hadamard_plus,
    "|->": hadamard_minus,
    "Bell state": bell_phi_plus,
    "complex two-qubit state": complex_two_qubit_state,
}

for name, state in central_states.items():
    normalized = normalize_state(state)
    probabilities = measurement_probabilities(state)

    assert_probability_distribution(probabilities)

    print(
        f"{name:24s} "
        f"dimension={len(normalized):2d} "
        f"probability_total={sum(probabilities):.12f}"
    )

print("\nAll central-state validations completed successfully.")
print("\nEnd of comprehensive superposition and quantum-amplitude study script.")
