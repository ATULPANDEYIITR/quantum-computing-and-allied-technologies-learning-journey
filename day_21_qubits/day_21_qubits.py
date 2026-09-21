"""
Qubits: From First Principles to Quantum-Circuit Simulation

This file is a self-contained study program for learning qubits from the
absolute beginner level through practical quantum-circuit simulation.

Topics demonstrated:
- Classical bits versus qubits
- Computational basis states |0> and |1>
- Superposition
- Probability amplitudes
- Complex numbers
- Normalization
- Measurement
- Born's rule
- Global and relative phase
- Hadamard, Pauli-X, Pauli-Y, Pauli-Z gates
- S, T, and rotation gates
- Quantum interference
- Multi-qubit state vectors
- Tensor products
- CNOT and entanglement
- Bell states
- Partial measurement
- Expectation values
- Density matrices
- Mixed states
- Decoherence-style noise
- Quantum circuit execution
- Measurement statistics
- A small BB84-style educational simulation
- Numerical precision and edge cases
- Complexity considerations
- Validation and error handling

No external packages are required.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple


EPSILON = 1e-12


# ---------------------------------------------------------------------------
# Section 1: Basic mathematical utilities
# ---------------------------------------------------------------------------

ComplexVector = List[complex]
ComplexMatrix = List[List[complex]]


def clean_complex(value: complex, tolerance: float = 1e-12) -> complex:
    """Remove tiny floating-point artifacts from a complex number."""
    real = 0.0 if abs(value.real) < tolerance else value.real
    imag = 0.0 if abs(value.imag) < tolerance else value.imag
    return complex(real, imag)


def vector_norm(state: Sequence[complex]) -> float:
    """Return the Euclidean norm of a state vector."""
    return math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def normalize_state(state: Sequence[complex]) -> ComplexVector:
    """
    Normalize a state vector.

    Quantum state vectors must have total probability equal to one.
    """
    norm = vector_norm(state)

    if norm < EPSILON:
        raise ValueError("The zero vector cannot represent a quantum state.")

    return [amplitude / norm for amplitude in state]


def probabilities_from_state(state: Sequence[complex]) -> List[float]:
    """Apply Born's rule: P(i) = |amplitude_i|^2."""
    return [float(abs(amplitude) ** 2) for amplitude in state]


def validate_normalized_state(state: Sequence[complex]) -> None:
    """Raise an error if a state is not approximately normalized."""
    total_probability = sum(abs(amplitude) ** 2 for amplitude in state)

    if not math.isclose(total_probability, 1.0, abs_tol=1e-9):
        raise ValueError(
            f"State is not normalized. Total probability = {total_probability}"
        )


def matrix_vector_multiply(
    matrix: ComplexMatrix,
    vector: Sequence[complex],
) -> ComplexVector:
    """Multiply a square matrix by a state vector."""
    if len(matrix) != len(vector):
        raise ValueError("Matrix and vector dimensions do not match.")

    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("Matrix must be square and match vector dimension.")

    result = []

    for row in matrix:
        result.append(
            sum(matrix_element * vector_element
                for matrix_element, vector_element in zip(row, vector))
        )

    return result


def matrix_multiply(
    left: ComplexMatrix,
    right: ComplexMatrix,
) -> ComplexMatrix:
    """Multiply two compatible matrices."""
    if not left or not right:
        raise ValueError("Matrices cannot be empty.")

    left_columns = len(left[0])
    right_rows = len(right)

    if left_columns != right_rows:
        raise ValueError("Matrix dimensions do not match.")

    if any(len(row) != left_columns for row in left):
        raise ValueError("Left matrix is not rectangular.")

    if any(len(row) != len(right[0]) for row in right):
        raise ValueError("Right matrix is not rectangular.")

    return [
        [
            sum(left[i][k] * right[k][j] for k in range(right_rows))
            for j in range(len(right[0]))
        ]
        for i in range(len(left))
    ]


def dagger(matrix: ComplexMatrix) -> ComplexMatrix:
    """Return the conjugate transpose of a matrix."""
    return [
        [matrix[row][column].conjugate() for row in range(len(matrix))]
        for column in range(len(matrix[0]))
    ]


def is_unitary(matrix: ComplexMatrix, tolerance: float = 1e-9) -> bool:
    """
    Check U†U = I.

    Quantum gates are represented by unitary matrices because unitary
    evolution preserves total probability.
    """
    product = matrix_multiply(dagger(matrix), matrix)

    for row in range(len(product)):
        for column in range(len(product)):
            expected = 1.0 if row == column else 0.0
            if abs(product[row][column] - expected) > tolerance:
                return False

    return True


# ---------------------------------------------------------------------------
# Section 2: Computational basis and state representation
# ---------------------------------------------------------------------------

def basis_state(bit: int) -> ComplexVector:
    """Return |0> or |1>."""
    if bit == 0:
        return [1 + 0j, 0 + 0j]

    if bit == 1:
        return [0 + 0j, 1 + 0j]

    raise ValueError("A computational-basis bit must be 0 or 1.")


def format_complex(value: complex) -> str:
    """Readable representation for demonstrations."""
    value = clean_complex(value)

    if abs(value.imag) < EPSILON:
        return f"{value.real:.6f}"

    if abs(value.real) < EPSILON:
        return f"{value.imag:.6f}i"

    sign = "+" if value.imag >= 0 else "-"
    return f"{value.real:.6f}{sign}{abs(value.imag):.6f}i"


def print_state(
    state: Sequence[complex],
    label: str = "state",
    basis_labels: Sequence[str] | None = None,
) -> None:
    """Print amplitudes and probabilities."""
    validate_normalized_state(state)

    if basis_labels is None:
        basis_labels = [f"|{index}>"
                        for index in range(len(state))]

    print(f"\n{label}")
    for basis, amplitude in zip(basis_labels, state):
        probability = abs(amplitude) ** 2
        print(
            f"  {basis}: amplitude={format_complex(amplitude)}, "
            f"probability={probability:.6f}"
        )


# ---------------------------------------------------------------------------
# Section 3: Single-qubit gates
# ---------------------------------------------------------------------------

SQRT2_INV = 1 / math.sqrt(2)

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
    [SQRT2_INV + 0j, SQRT2_INV + 0j],
    [SQRT2_INV + 0j, -SQRT2_INV + 0j],
]

S = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, 1j],
]

T = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, cmath.exp(1j * math.pi / 4)],
]


def rx(theta: float) -> ComplexMatrix:
    """Rotation around the X axis."""
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)

    return [
        [c + 0j, -1j * s],
        [-1j * s, c + 0j],
    ]


def ry(theta: float) -> ComplexMatrix:
    """Rotation around the Y axis."""
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)

    return [
        [c + 0j, -s + 0j],
        [s + 0j, c + 0j],
    ]


def rz(theta: float) -> ComplexMatrix:
    """Rotation around the Z axis."""
    return [
        [cmath.exp(-1j * theta / 2), 0 + 0j],
        [0 + 0j, cmath.exp(1j * theta / 2)],
    ]


def apply_gate(
    state: Sequence[complex],
    gate: ComplexMatrix,
) -> ComplexVector:
    """Apply a quantum gate and verify probability preservation."""
    if not is_unitary(gate):
        raise ValueError("Quantum evolution gate must be unitary.")

    result = matrix_vector_multiply(gate, state)
    result = [clean_complex(value) for value in result]
    validate_normalized_state(result)
    return result


# ---------------------------------------------------------------------------
# Section 4: Beginner examples
# ---------------------------------------------------------------------------

def demonstrate_classical_bit_vs_qubit() -> None:
    print("\n" + "=" * 72)
    print("CLASSICAL BIT VERSUS QUBIT")
    print("=" * 72)

    print("A classical bit is either 0 or 1.")
    print("A qubit can be represented as α|0> + β|1>.")
    print("The amplitudes α and β are complex numbers satisfying")
    print("|α|² + |β|² = 1.")

    zero = basis_state(0)
    one = basis_state(1)

    print_state(zero, "Classical-like computational state |0>")
    print_state(one, "Computational state |1>")


def demonstrate_superposition() -> None:
    print("\n" + "=" * 72)
    print("SUPERPOSITION")
    print("=" * 72)

    state = basis_state(0)
    state = apply_gate(state, H)

    print_state(
        state,
        "H|0> = (|0> + |1>) / sqrt(2)",
        ["|0>", "|1>"],
    )

    print(
        "\nThe amplitudes are equal, so measurement gives approximately "
        "50% probability for each computational result."
    )


def demonstrate_measurement(
    state: Sequence[complex],
    shots: int = 1000,
    seed: int = 7,
) -> dict[int, int]:
    """
    Repeatedly measure a qubit.

    Measurement is probabilistic. The state is projected onto the observed
    basis state in an ideal projective measurement.
    """
    if len(state) != 2:
        raise ValueError("This simple measurement function expects one qubit.")

    if shots <= 0:
        raise ValueError("shots must be positive.")

    validate_normalized_state(state)

    rng = random.Random(seed)
    probabilities = probabilities_from_state(state)

    counts = {0: 0, 1: 0}

    for _ in range(shots):
        outcome = 0 if rng.random() < probabilities[0] else 1
        counts[outcome] += 1

    print(
        f"\nMeasurement over {shots} shots: "
        f"|0>={counts[0]}, |1>={counts[1]}"
    )

    return counts


def demonstrate_interference() -> None:
    print("\n" + "=" * 72)
    print("QUANTUM INTERFERENCE")
    print("=" * 72)

    state = basis_state(0)
    state = apply_gate(state, H)
    print_state(state, "After H")

    state = apply_gate(state, H)
    print_state(
        state,
        "After H followed by H",
        ["|0>", "|1>"],
    )

    print(
        "\nThe second Hadamard causes amplitudes to interfere so that "
        "the original |0> state is recovered."
    )

    state = basis_state(0)
    state = apply_gate(state, H)
    state = apply_gate(state, Z)
    state = apply_gate(state, H)

    print_state(
        state,
        "H-Z-H sequence",
        ["|0>", "|1>"],
    )


def demonstrate_phase() -> None:
    print("\n" + "=" * 72)
    print("GLOBAL AND RELATIVE PHASE")
    print("=" * 72)

    zero = basis_state(0)

    state_a = apply_gate(zero, H)
    state_b = apply_gate(state_a, Z)

    print_state(state_a, "H|0>")
    print_state(state_b, "Z H|0>")

    print(
        "\nA global phase does not change measurement probabilities, "
        "but a relative phase between basis components can change "
        "interference in later operations."
    )


# ---------------------------------------------------------------------------
# Section 5: Bloch-sphere coordinates
# ---------------------------------------------------------------------------

def bloch_vector(state: Sequence[complex]) -> Tuple[float, float, float]:
    """
    Compute Bloch-sphere coordinates for a pure single-qubit state.

    For |ψ> = α|0> + β|1>:
      x = 2 Re(α* β)
      y = 2 Im(α* β)
      z = |α|² - |β|²
    """
    if len(state) != 2:
        raise ValueError("Bloch coordinates require exactly one qubit.")

    validate_normalized_state(state)

    alpha, beta = state

    x = 2 * (alpha.conjugate() * beta).real
    y = 2 * (alpha.conjugate() * beta).imag
    z = abs(alpha) ** 2 - abs(beta) ** 2

    return (x, y, z)


def demonstrate_bloch_sphere() -> None:
    print("\n" + "=" * 72)
    print("BLOCH-SPHERE REPRESENTATION")
    print("=" * 72)

    states = {
        "|0>": basis_state(0),
        "|1>": basis_state(1),
        "|+>": apply_gate(basis_state(0), H),
        "|->": apply_gate(basis_state(1), H),
    }

    for name, state in states.items():
        x, y, z = bloch_vector(state)
        print(f"{name}: x={x:.6f}, y={y:.6f}, z={z:.6f}")


# ---------------------------------------------------------------------------
# Section 6: Multi-qubit states
# ---------------------------------------------------------------------------

def tensor_product(
    left: Sequence[complex],
    right: Sequence[complex],
) -> ComplexVector:
    """
    Compute the Kronecker/tensor product.

    If A has dimension 2^n and B has dimension 2^m, A⊗B has dimension
    2^(n+m). This exponential growth is central to quantum simulation.
    """
    return [
        left_amplitude * right_amplitude
        for left_amplitude in left
        for right_amplitude in right
    ]


def tensor_many(states: Sequence[Sequence[complex]]) -> ComplexVector:
    """Tensor several state vectors from left to right."""
    if not states:
        raise ValueError("At least one state is required.")

    result = list(states[0])

    for state in states[1:]:
        result = tensor_product(result, state)

    return result


def computational_basis_state(
    bits: str,
) -> ComplexVector:
    """
    Create |bits> using big-endian display order.

    For example, "10" corresponds to the vector [0, 0, 1, 0].
    """
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("bits must be a non-empty string containing only 0 and 1.")

    dimension = 2 ** len(bits)
    index = int(bits, 2)

    state = [0j] * dimension
    state[index] = 1 + 0j
    return state


def index_to_bitstring(index: int, number_of_qubits: int) -> str:
    return format(index, f"0{number_of_qubits}b")


def print_multi_qubit_state(
    state: Sequence[complex],
    number_of_qubits: int,
    label: str,
) -> None:
    validate_normalized_state(state)

    print(f"\n{label}")

    for index, amplitude in enumerate(state):
        if abs(amplitude) > 1e-10:
            bitstring = index_to_bitstring(index, number_of_qubits)
            print(
                f"  |{bitstring}>: amplitude={format_complex(amplitude)}, "
                f"probability={abs(amplitude) ** 2:.6f}"
            )


# ---------------------------------------------------------------------------
# Section 7: Two-qubit gates
# ---------------------------------------------------------------------------

CNOT = [
    [1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],
    [0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],
    [0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],
    [0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j],
]

SWAP = [
    [1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j],
    [0 + 0j, 0 + 0j, 1 + 0j, 0 + 0j],
    [0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j],
    [0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j],
]


def demonstrate_entanglement() -> ComplexVector:
    print("\n" + "=" * 72)
    print("ENTANGLEMENT AND THE BELL STATE")
    print("=" * 72)

    # Start in |00>.
    state = computational_basis_state("00")

    # Apply H to the first qubit.
    # H⊗I transforms |00> into (|00> + |10>)/sqrt(2).
    state = matrix_vector_multiply(
        matrix_kronecker(H, I),
        state,
    )

    # CNOT maps |10> -> |11>, producing a Bell state.
    state = apply_gate(state, CNOT)

    print_multi_qubit_state(
        state,
        2,
        "Bell state produced by H on qubit 0 followed by CNOT",
    )

    probabilities = probabilities_from_state(state)

    print(
        "\nBell-state probabilities:",
        {
            "00": probabilities[0],
            "01": probabilities[1],
            "10": probabilities[2],
            "11": probabilities[3],
        },
    )

    print(
        "\nThe two qubits are not independently describable by separate "
        "single-qubit pure states. Their measurement outcomes are correlated."
    )

    return state


def matrix_kronecker(
    left: ComplexMatrix,
    right: ComplexMatrix,
) -> ComplexMatrix:
    """Kronecker product for matrices."""
    result = []

    for left_row in left:
        for right_row in right:
            row = []

            for left_value in left_row:
                for right_value in right_row:
                    row.append(left_value * right_value)

            result.append(row)

    return result


# ---------------------------------------------------------------------------
# Section 8: Generic gate application to selected qubits
# ---------------------------------------------------------------------------

def apply_single_qubit_gate(
    state: Sequence[complex],
    gate: ComplexMatrix,
    target_qubit: int,
    number_of_qubits: int,
) -> ComplexVector:
    """
    Apply a 2x2 gate to one qubit in an n-qubit state.

    Qubit indexing here uses big-endian convention:
    qubit 0 is the leftmost bit in the displayed bitstring.
    """
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension does not match qubit count.")

    if not 0 <= target_qubit < number_of_qubits:
        raise IndexError("target_qubit is out of range.")

    if len(gate) != 2 or any(len(row) != 2 for row in gate):
        raise ValueError("A single-qubit gate must be a 2x2 matrix.")

    result = [0j] * len(state)
    bit_position = number_of_qubits - 1 - target_qubit
    mask = 1 << bit_position

    for index in range(len(state)):
        if index & mask:
            continue

        partner = index | mask

        a0 = state[index]
        a1 = state[partner]

        result[index] = gate[0][0] * a0 + gate[0][1] * a1
        result[partner] = gate[1][0] * a0 + gate[1][1] * a1

    validate_normalized_state(result)
    return [clean_complex(value) for value in result]


def apply_cnot(
    state: Sequence[complex],
    control_qubit: int,
    target_qubit: int,
    number_of_qubits: int,
) -> ComplexVector:
    """Apply CNOT without constructing a full 2^n x 2^n matrix."""
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension does not match qubit count.")

    if control_qubit == target_qubit:
        raise ValueError("Control and target qubits must be different.")

    if not 0 <= control_qubit < number_of_qubits:
        raise IndexError("control_qubit is out of range.")

    if not 0 <= target_qubit < number_of_qubits:
        raise IndexError("target_qubit is out of range.")

    control_position = number_of_qubits - 1 - control_qubit
    target_position = number_of_qubits - 1 - target_qubit

    control_mask = 1 << control_position
    target_mask = 1 << target_position

    result = [0j] * len(state)

    for index, amplitude in enumerate(state):
        if index & control_mask:
            destination = index ^ target_mask
        else:
            destination = index

        result[destination] += amplitude

    validate_normalized_state(result)
    return [clean_complex(value) for value in result]


def demonstrate_generic_multi_qubit_gates() -> None:
    print("\n" + "=" * 72)
    print("GENERIC MULTI-QUBIT GATE APPLICATION")
    print("=" * 72)

    state = computational_basis_state("000")

    state = apply_single_qubit_gate(state, H, 0, 3)
    state = apply_single_qubit_gate(state, H, 2, 3)
    state = apply_cnot(state, 0, 1, 3)

    print_multi_qubit_state(
        state,
        3,
        "Three-qubit state after H, H, and CNOT operations",
    )


# ---------------------------------------------------------------------------
# Section 9: Measurement of arbitrary computational-basis states
# ---------------------------------------------------------------------------

def measure_state(
    state: Sequence[complex],
    number_of_qubits: int,
    rng: random.Random | None = None,
) -> Tuple[str, ComplexVector]:
    """
    Measure an n-qubit state in the computational basis.

    The returned state is the post-measurement collapsed basis state.
    """
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension does not match number_of_qubits.")

    validate_normalized_state(state)

    if rng is None:
        rng = random.Random()

    probabilities = probabilities_from_state(state)
    random_value = rng.random()

    cumulative = 0.0

    for index, probability in enumerate(probabilities):
        cumulative += probability

        if random_value <= cumulative or index == len(probabilities) - 1:
            collapsed_state = [0j] * len(state)
            collapsed_state[index] = 1 + 0j

            return (
                index_to_bitstring(index, number_of_qubits),
                collapsed_state,
            )

    raise RuntimeError("Measurement failed unexpectedly.")


def sample_measurements(
    state: Sequence[complex],
    number_of_qubits: int,
    shots: int,
    seed: int = 11,
) -> dict[str, int]:
    """Collect a histogram of repeated circuit measurements."""
    if shots <= 0:
        raise ValueError("shots must be positive.")

    rng = random.Random(seed)
    counts = {}

    for _ in range(shots):
        outcome, _ = measure_state(state, number_of_qubits, rng)
        counts[outcome] = counts.get(outcome, 0) + 1

    return dict(sorted(counts.items()))


def demonstrate_measurement_histogram() -> None:
    print("\n" + "=" * 72)
    print("MULTI-QUBIT MEASUREMENT STATISTICS")
    print("=" * 72)

    state = computational_basis_state("00")
    state = apply_single_qubit_gate(state, H, 0, 2)
    state = apply_single_qubit_gate(state, H, 1, 2)

    counts = sample_measurements(state, 2, 2000)

    print("Circuit: H on both qubits.")
    print("Expected probabilities: approximately 25% for each basis state.")
    print("Observed counts:", counts)


# ---------------------------------------------------------------------------
# Section 10: Expectation values
# ---------------------------------------------------------------------------

def expectation_value(
    state: Sequence[complex],
    operator: ComplexMatrix,
) -> complex:
    """
    Calculate <ψ|O|ψ>.

    For Hermitian observables this value is real, up to numerical error.
    """
    transformed = matrix_vector_multiply(operator, state)

    return sum(
        amplitude.conjugate() * transformed_amplitude
        for amplitude, transformed_amplitude in zip(state, transformed)
    )


def demonstrate_expectation_values() -> None:
    print("\n" + "=" * 72)
    print("EXPECTATION VALUES")
    print("=" * 72)

    plus_state = apply_gate(basis_state(0), H)

    for name, operator in [("X", X), ("Y", Y), ("Z", Z)]:
        value = expectation_value(plus_state, operator)
        print(f"<{name}> for |+> = {format_complex(value)}")

    print(
        "\nFor |+>, the expectation of X is +1 while the expectations "
        "of Y and Z are zero."
    )


# ---------------------------------------------------------------------------
# Section 11: Density matrices
# ---------------------------------------------------------------------------

def outer_product(
    ket: Sequence[complex],
    bra_vector: Sequence[complex],
) -> ComplexMatrix:
    """Return |ket><bra_vector|."""
    return [
        [
            ket[row] * bra_vector[column].conjugate()
            for column in range(len(bra_vector))
        ]
        for row in range(len(ket))
    ]


def pure_state_density_matrix(
    state: Sequence[complex],
) -> ComplexMatrix:
    """Construct rho = |psi><psi|."""
    validate_normalized_state(state)
    return outer_product(state, state)


def trace(matrix: ComplexMatrix) -> complex:
    """Return the matrix trace."""
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Trace requires a square matrix.")

    return sum(matrix[index][index] for index in range(len(matrix)))


def mix_density_matrices(
    first: ComplexMatrix,
    second: ComplexMatrix,
    first_weight: float,
) -> ComplexMatrix:
    """
    Construct a classical mixture:
        rho = p rho_1 + (1-p) rho_2
    """
    if not 0 <= first_weight <= 1:
        raise ValueError("first_weight must be between 0 and 1.")

    if len(first) != len(second):
        raise ValueError("Density matrices must have equal dimensions.")

    second_weight = 1 - first_weight

    return [
        [
            first[row][column] * first_weight
            + second[row][column] * second_weight
            for column in range(len(first))
        ]
        for row in range(len(first))
    ]


def demonstrate_density_matrix() -> None:
    print("\n" + "=" * 72)
    print("DENSITY MATRICES AND MIXED STATES")
    print("=" * 72)

    zero_density = pure_state_density_matrix(basis_state(0))
    one_density = pure_state_density_matrix(basis_state(1))

    mixed = mix_density_matrices(
        zero_density,
        one_density,
        0.5,
    )

    print("Trace of |0><0|:", trace(zero_density))
    print("Trace of |1><1|:", trace(one_density))
    print("Trace of 50/50 mixed state:", trace(mixed))

    print("\n50/50 mixed-state density matrix:")

    for row in mixed:
        print(
            "  ",
            " ".join(format_complex(value) for value in row),
        )

    print(
        "\nA mixed state is not simply the same concept as a coherent "
        "superposition. Both may produce identical computational-basis "
        "probabilities while behaving differently under other measurements."
    )


# ---------------------------------------------------------------------------
# Section 12: Simple noise models
# ---------------------------------------------------------------------------

def apply_bit_flip_noise(
    state: Sequence[complex],
    probability: float,
    rng: random.Random | None = None,
) -> ComplexVector:
    """
    Educational stochastic bit-flip channel.

    With probability p, apply X; otherwise leave the state unchanged.
    """
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1.")

    if rng is None:
        rng = random.Random()

    if rng.random() < probability:
        return apply_gate(state, X)

    return list(state)


def demonstrate_noise() -> None:
    print("\n" + "=" * 72)
    print("NOISE AND IMPERFECT QUANTUM SYSTEMS")
    print("=" * 72)

    rng = random.Random(19)
    state = basis_state(0)

    flip_count = 0
    shots = 1000

    for _ in range(shots):
        noisy_state = apply_bit_flip_noise(
            state,
            probability=0.1,
            rng=rng,
        )

        if abs(noisy_state[1]) ** 2 > 0.5:
            flip_count += 1

    print(
        f"With an idealized 10% bit-flip probability, "
        f"{flip_count}/{shots} trials produced |1>."
    )

    print(
        "\nReal hardware has richer noise processes, including relaxation, "
        "dephasing, gate errors, readout errors, crosstalk, and leakage."
    )


# ---------------------------------------------------------------------------
# Section 13: Quantum circuit abstraction
# ---------------------------------------------------------------------------

@dataclass
class Operation:
    """One operation in a small educational circuit."""

    name: str
    apply: Callable[[ComplexVector], ComplexVector]


class QuantumCircuit:
    """
    Small state-vector quantum circuit simulator.

    This simulator is deliberately educational. It uses dense state vectors,
    so memory grows exponentially with the number of simulated qubits.
    """

    def __init__(self, number_of_qubits: int):
        if number_of_qubits <= 0:
            raise ValueError("A circuit needs at least one qubit.")

        self.number_of_qubits = number_of_qubits
        self.state = computational_basis_state("0" * number_of_qubits)
        self.operations: List[Operation] = []

    def add_single_qubit_gate(
        self,
        name: str,
        gate: ComplexMatrix,
        target_qubit: int,
    ) -> None:
        def operation(current_state: ComplexVector) -> ComplexVector:
            return apply_single_qubit_gate(
                current_state,
                gate,
                target_qubit,
                self.number_of_qubits,
            )

        self.operations.append(Operation(name, operation))

    def add_cnot(
        self,
        control_qubit: int,
        target_qubit: int,
    ) -> None:
        def operation(current_state: ComplexVector) -> ComplexVector:
            return apply_cnot(
                current_state,
                control_qubit,
                target_qubit,
                self.number_of_qubits,
            )

        self.operations.append(
            Operation(
                f"CNOT q{control_qubit}->q{target_qubit}",
                operation,
            )
        )

    def run(self) -> ComplexVector:
        self.state = computational_basis_state(
            "0" * self.number_of_qubits
        )

        for operation in self.operations:
            self.state = operation.apply(self.state)

        return self.state

    def measure(self, shots: int = 1000) -> dict[str, int]:
        """Run the circuit and sample its final state."""
        state = self.run()
        return sample_measurements(
            state,
            self.number_of_qubits,
            shots,
        )

    def describe(self) -> None:
        print(f"\nCircuit with {self.number_of_qubits} qubits:")

        for index, operation in enumerate(self.operations, start=1):
            print(f"  {index}. {operation.name}")


def demonstrate_quantum_circuit() -> None:
    print("\n" + "=" * 72)
    print("QUANTUM CIRCUIT")
    print("=" * 72)

    circuit = QuantumCircuit(2)

    circuit.add_single_qubit_gate("H q0", H, 0)
    circuit.add_cnot(0, 1)

    circuit.describe()

    final_state = circuit.run()

    print_multi_qubit_state(
        final_state,
        2,
        "Final circuit state",
    )

    print("Measurement histogram:", circuit.measure(2000))


# ---------------------------------------------------------------------------
# Section 14: Bell-state correlation test
# ---------------------------------------------------------------------------

def demonstrate_bell_correlations() -> None:
    print("\n" + "=" * 72)
    print("BELL-STATE CORRELATIONS")
    print("=" * 72)

    circuit = QuantumCircuit(2)
    circuit.add_single_qubit_gate("H q0", H, 0)
    circuit.add_cnot(0, 1)

    state = circuit.run()
    rng = random.Random(31)

    same_count = 0
    shots = 1000

    for _ in range(shots):
        outcome, _ = measure_state(state, 2, rng)

        if outcome[0] == outcome[1]:
            same_count += 1

    print(f"Same-bit outcomes: {same_count}/{shots}")

    print(
        "For the ideal |Φ+> Bell state, computational-basis outcomes "
        "00 and 11 occur while 01 and 10 have zero ideal probability."
    )


# ---------------------------------------------------------------------------
# Section 15: Educational BB84-style protocol
# ---------------------------------------------------------------------------

def prepare_bb84_state(bit: int, basis: int) -> ComplexVector:
    """
    Prepare one of four BB84 states.

    basis=0 means computational/Z basis:
        bit 0 -> |0>
        bit 1 -> |1>

    basis=1 means Hadamard/X basis:
        bit 0 -> |+>
        bit 1 -> |->

    This is an educational state-vector simulation, not a complete
    cryptographic implementation.
    """
    if bit not in (0, 1):
        raise ValueError("BB84 bit must be 0 or 1.")

    if basis not in (0, 1):
        raise ValueError("BB84 basis must be 0 or 1.")

    state = basis_state(bit)

    if basis == 1:
        state = apply_gate(state, H)

    return state


def measure_bb84_state(
    state: Sequence[complex],
    measurement_basis: int,
    rng: random.Random,
) -> int:
    """Measure a BB84 qubit in either Z or X basis."""
    if measurement_basis not in (0, 1):
        raise ValueError("Measurement basis must be 0 or 1.")

    measurement_state = list(state)

    # Measuring in X basis is equivalent to applying H and measuring in Z.
    if measurement_basis == 1:
        measurement_state = apply_gate(measurement_state, H)

    outcome, _ = measure_state(
        measurement_state,
        1,
        rng,
    )

    return int(outcome)


def demonstrate_bb84() -> None:
    print("\n" + "=" * 72)
    print("EDUCATIONAL BB84-STYLE QUBIT PROTOCOL")
    print("=" * 72)

    rng = random.Random(101)

    alice_bits = [rng.randint(0, 1) for _ in range(12)]
    alice_bases = [rng.randint(0, 1) for _ in range(12)]
    bob_bases = [rng.randint(0, 1) for _ in range(12)]

    bob_results = []

    for bit, alice_basis, bob_basis in zip(
        alice_bits,
        alice_bases,
        bob_bases,
    ):
        state = prepare_bb84_state(bit, alice_basis)

        result = measure_bb84_state(
            state,
            bob_basis,
            rng,
        )

        bob_results.append(result)

    sifted_positions = [
        index
        for index, (alice_basis, bob_basis)
        in enumerate(zip(alice_bases, bob_bases))
        if alice_basis == bob_basis
    ]

    alice_key = [
        alice_bits[index]
        for index in sifted_positions
    ]

    bob_key = [
        bob_results[index]
        for index in sifted_positions
    ]

    print("Alice bits:     ", alice_bits)
    print("Alice bases:    ", alice_bases)
    print("Bob bases:      ", bob_bases)
    print("Bob results:    ", bob_results)
    print("Sifted indices: ", sifted_positions)
    print("Alice key:      ", alice_key)
    print("Bob key:        ", bob_key)

    mismatches = sum(
        alice != bob
        for alice, bob in zip(alice_key, bob_key)
    )

    print(
        f"Sifted mismatches: {mismatches}/{len(sifted_positions)}"
    )

    print(
        "\nThe protocol illustrates why incompatible measurement bases "
        "matter in quantum key distribution. A production cryptographic "
        "protocol requires authentication, finite-key analysis, security "
        "proofs, carefully modeled noise, and implementation protections."
    )


# ---------------------------------------------------------------------------
# Section 16: Edge cases and validation
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 72)
    print("EDGE CASES AND VALIDATION")
    print("=" * 72)

    tests = [
        ("Invalid computational bit", lambda: basis_state(2)),
        ("Zero-vector normalization", lambda: normalize_state([0j, 0j])),
        ("Invalid measurement shots", lambda: demonstrate_measurement(
            basis_state(0),
            shots=0,
        )),
        ("Invalid CNOT control", lambda: apply_cnot(
            computational_basis_state("00"),
            0,
            0,
            2,
        )),
    ]

    for description, test in tests:
        try:
            test()
        except (ValueError, IndexError) as error:
            print(f"{description}: correctly rejected -> {error}")


# ---------------------------------------------------------------------------
# Section 17: Performance demonstration
# ---------------------------------------------------------------------------

def demonstrate_scaling() -> None:
    print("\n" + "=" * 72)
    print("STATE-VECTOR SCALING")
    print("=" * 72)

    print(
        "An n-qubit pure state requires 2^n complex amplitudes "
        "in a dense state-vector simulator."
    )

    for number_of_qubits in [1, 2, 4, 8, 12, 16, 20]:
        dimension = 2 ** number_of_qubits
        print(
            f"  {number_of_qubits:2d} qubits -> "
            f"{dimension:>8,d} amplitudes"
        )

    print(
        "\nThis exponential state-space growth is one of the fundamental "
        "reasons classical simulation of general quantum systems becomes "
        "difficult as the number of qubits increases."
    )

    print(
        "\nSparse representations, tensor-network methods, stabilizer "
        "simulation, specialized hardware, and problem-specific structure "
        "can reduce the practical cost for important classes of circuits."
    )


# ---------------------------------------------------------------------------
# Section 18: Gate validation
# ---------------------------------------------------------------------------

def demonstrate_gate_properties() -> None:
    print("\n" + "=" * 72)
    print("UNITARITY OF COMMON QUANTUM GATES")
    print("=" * 72)

    gates = {
        "I": I,
        "X": X,
        "Y": Y,
        "Z": Z,
        "H": H,
        "S": S,
        "T": T,
        "Rx(pi/3)": rx(math.pi / 3),
        "Ry(pi/3)": ry(math.pi / 3),
        "Rz(pi/3)": rz(math.pi / 3),
        "CNOT": CNOT,
        "SWAP": SWAP,
    }

    for name, gate in gates.items():
        print(f"{name:10s} -> unitary={is_unitary(gate)}")


# ---------------------------------------------------------------------------
# Section 19: A more advanced circuit
# ---------------------------------------------------------------------------

def demonstrate_advanced_circuit() -> None:
    print("\n" + "=" * 72)
    print("ADVANCED CIRCUIT: SUPERPOSITION, PHASE, ENTANGLEMENT")
    print("=" * 72)

    circuit = QuantumCircuit(3)

    circuit.add_single_qubit_gate("H q0", H, 0)
    circuit.add_single_qubit_gate("H q1", H, 1)
    circuit.add_single_qubit_gate("T q0", T, 0)
    circuit.add_cnot(0, 2)
    circuit.add_single_qubit_gate("Ry(pi/5) q1", ry(math.pi / 5), 1)
    circuit.add_cnot(1, 2)
    circuit.add_single_qubit_gate("Z q2", Z, 2)

    circuit.describe()

    state = circuit.run()

    print_multi_qubit_state(
        state,
        3,
        "Final state of the advanced circuit",
    )

    counts = circuit.measure(3000)
    print("\n3000-shot measurement histogram:")

    for bitstring, count in counts.items():
        print(f"  {bitstring}: {count}")


# ---------------------------------------------------------------------------
# Section 20: Main educational execution
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("QUBITS: A COMPLETE PYTHON STUDY AND SIMULATION")
    print("=" * 72)

    demonstrate_classical_bit_vs_qubit()
    demonstrate_superposition()

    plus_state = apply_gate(
        basis_state(0),
        H,
    )
    demonstrate_measurement(
        plus_state,
        shots=1000,
    )

    demonstrate_interference()
    demonstrate_phase()
    demonstrate_bloch_sphere()

    bell_state = demonstrate_entanglement()
    print(
        "\nBell-state normalization:",
        vector_norm(bell_state),
    )

    demonstrate_generic_multi_qubit_gates()
    demonstrate_measurement_histogram()
    demonstrate_expectation_values()
    demonstrate_density_matrix()
    demonstrate_noise()
    demonstrate_quantum_circuit()
    demonstrate_bell_correlations()
    demonstrate_bb84()
    demonstrate_edge_cases()
    demonstrate_gate_properties()
    demonstrate_scaling()
    demonstrate_advanced_circuit()

    print("\n" + "=" * 72)
    print("END OF QUBIT STUDY PROGRAM")
    print("=" * 72)


if __name__ == "__main__":
    main()
