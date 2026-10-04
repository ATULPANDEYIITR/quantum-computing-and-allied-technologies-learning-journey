"""
Quantum Teleportation: Quantum Information Transfer

A self-contained educational simulation of the quantum teleportation protocol.

This program uses state-vector mathematics to demonstrate:
- Qubit state representation
- Single-qubit gates
- Tensor products for multi-qubit systems
- Bell-state preparation
- Entanglement
- Alice's Bell-basis measurement
- Classical communication of measurement results
- Bob's conditional correction
- Fidelity of the teleported state
- Deterministic branch-by-branch verification
- No-cloning and no-faster-than-light communication constraints
- Noise and imperfect operations
- Density matrices and partial trace for mixed-state analysis

The simulation uses only Python's standard library.

Important physical distinction:
Quantum teleportation transfers an unknown quantum state from Alice's qubit
to Bob's qubit. It does not transport matter, and it does not transmit the
quantum state faster than light. Alice must send two classical bits to Bob
before Bob can complete the reconstruction.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence


EPSILON = 1e-10


# ---------------------------------------------------------------------------
# Basic linear-algebra utilities
# ---------------------------------------------------------------------------

ComplexVector = list[complex]
ComplexMatrix = list[list[complex]]


def vector_norm(vector: Sequence[complex]) -> float:
    """Return the Euclidean norm of a complex vector."""
    return math.sqrt(sum(abs(value) ** 2 for value in vector))


def normalize(vector: Sequence[complex]) -> ComplexVector:
    """Normalize a non-zero quantum state vector."""
    norm = vector_norm(vector)
    if norm < EPSILON:
        raise ValueError("A quantum state cannot be normalized from zero.")
    return [value / norm for value in vector]


def inner_product(left: Sequence[complex], right: Sequence[complex]) -> complex:
    """Compute <left|right> using complex conjugation on the bra."""
    if len(left) != len(right):
        raise ValueError("Vectors must have equal dimensions.")
    return sum(a.conjugate() * b for a, b in zip(left, right))


def matrix_vector_multiply(
    matrix: ComplexMatrix,
    vector: Sequence[complex],
) -> ComplexVector:
    """Apply a square matrix to a state vector."""
    if len(matrix) == 0:
        raise ValueError("Matrix cannot be empty.")

    dimension = len(vector)
    if len(matrix) != dimension:
        raise ValueError("Matrix dimension does not match vector dimension.")

    if any(len(row) != dimension for row in matrix):
        raise ValueError("Matrix must be square.")

    return [
        sum(matrix[row][column] * vector[column] for column in range(dimension))
        for row in range(dimension)
    ]


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
        raise ValueError("Matrix dimensions are incompatible.")

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


def kron(left: Sequence[Sequence[complex]], right: Sequence[Sequence[complex]]) -> ComplexMatrix:
    """
    Compute the Kronecker product of two matrices.

    For teleportation, tensor products combine the individual qubit
    operators into operations acting on the complete three-qubit register.
    """
    result: ComplexMatrix = []

    for left_row in left:
        for right_row in right:
            row: list[complex] = []
            for left_value in left_row:
                row.extend(left_value * right_value for right_value in right_row)
            result.append(row)

    return result


def apply_unitary(
    state: Sequence[complex],
    unitary: ComplexMatrix,
) -> ComplexVector:
    """Apply a unitary operation and verify that normalization is preserved."""
    output = matrix_vector_multiply(unitary, state)
    if abs(vector_norm(output) - 1.0) > 1e-8:
        raise ArithmeticError("Unitary operation produced an unnormalized state.")
    return output


# ---------------------------------------------------------------------------
# Quantum gates
# ---------------------------------------------------------------------------

SQRT_HALF = 1.0 / math.sqrt(2)

I = [
    [1, 0],
    [0, 1],
]

X = [
    [0, 1],
    [1, 0],
]

Y = [
    [0, -1j],
    [1j, 0],
]

Z = [
    [1, 0],
    [0, -1],
]

H = [
    [SQRT_HALF, SQRT_HALF],
    [SQRT_HALF, -SQRT_HALF],
]


def phase(theta: float) -> ComplexMatrix:
    """Construct a single-qubit phase rotation matrix."""
    return [
        [1, 0],
        [0, cmath.exp(1j * theta)],
    ]


def identity_matrix(dimension: int) -> ComplexMatrix:
    """Create an identity matrix of the requested dimension."""
    return [
        [1 if row == column else 0 for column in range(dimension)]
        for row in range(dimension)
    ]


# ---------------------------------------------------------------------------
# Computational-basis state construction
# ---------------------------------------------------------------------------

def basis_state(bits: str) -> ComplexVector:
    """
    Construct a computational-basis state such as |010>.

    Basis index follows the conventional binary ordering:
    |000> = index 0, |001> = index 1, ..., |111> = index 7.
    """
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("Basis state must be a non-empty binary string.")

    dimension = 2 ** len(bits)
    state = [0j] * dimension
    state[int(bits, 2)] = 1.0 + 0j
    return state


def tensor_product_vectors(
    left: Sequence[complex],
    right: Sequence[complex],
) -> ComplexVector:
    """Compute the tensor product of two state vectors."""
    return [a * b for a in left for b in right]


def qubit_state(alpha: complex, beta: complex) -> ComplexVector:
    """
    Construct |psi> = alpha|0> + beta|1> and normalize it.

    A global phase does not change the physical qubit state, so normalization
    is the only requirement enforced here.
    """
    return normalize([complex(alpha), complex(beta)])


def tensor_many(vectors: Sequence[Sequence[complex]]) -> ComplexVector:
    """Tensor product several state vectors from left to right."""
    if not vectors:
        raise ValueError("At least one state vector is required.")

    result = list(vectors[0])
    for vector in vectors[1:]:
        result = tensor_product_vectors(result, vector)
    return result


# ---------------------------------------------------------------------------
# Three-qubit gate application
# ---------------------------------------------------------------------------

def index_with_bit(index: int, qubit: int, value: int) -> int:
    """Replace one qubit in a computational-basis index."""
    mask = 1 << (2 - qubit)
    return (index | mask) if value else (index & ~mask)


def get_bit(index: int, qubit: int, number_of_qubits: int) -> int:
    """
    Read a qubit using left-to-right qubit numbering.

    For three qubits:
      qubit 0 = most significant bit
      qubit 1 = middle bit
      qubit 2 = least significant bit
    """
    shift = number_of_qubits - 1 - qubit
    return (index >> shift) & 1


def apply_single_qubit_gate(
    state: Sequence[complex],
    gate: ComplexMatrix,
    target_qubit: int,
    number_of_qubits: int,
) -> ComplexVector:
    """
    Apply a one-qubit gate to one position in a multi-qubit register.

    This explicitly constructs the transformed amplitudes instead of
    materializing a large full-system matrix.
    """
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension does not match qubit count.")
    if not 0 <= target_qubit < number_of_qubits:
        raise ValueError("Invalid target qubit.")

    result = [0j] * len(state)

    for index in range(len(state)):
        old_bit = get_bit(index, target_qubit, number_of_qubits)

        for new_bit in (0, 1):
            source = index_with_bit(index, target_qubit, old_bit)
            destination = index_with_bit(index, target_qubit, new_bit)
            result[destination] += gate[new_bit][old_bit] * state[source]

    return normalize(result)


def apply_controlled_x(
    state: Sequence[complex],
    control: int,
    target: int,
    number_of_qubits: int,
) -> ComplexVector:
    """
    Apply CNOT.

    The target bit is flipped only when the control bit equals one.
    """
    if control == target:
        raise ValueError("Control and target must be different.")

    dimension = 2 ** number_of_qubits
    if len(state) != dimension:
        raise ValueError("State dimension does not match qubit count.")

    result = [0j] * dimension

    for index, amplitude in enumerate(state):
        control_value = get_bit(index, control, number_of_qubits)

        if control_value == 1:
            target_value = get_bit(index, target, number_of_qubits)
            destination = index_with_bit(index, target, 1 - target_value)
        else:
            destination = index

        result[destination] += amplitude

    return normalize(result)


def apply_controlled_z(
    state: Sequence[complex],
    control: int,
    target: int,
    number_of_qubits: int,
) -> ComplexVector:
    """Apply a controlled-Z phase flip."""
    if control == target:
        raise ValueError("Control and target must be different.")

    result = list(state)

    for index in range(len(state)):
        control_value = get_bit(index, control, number_of_qubits)
        target_value = get_bit(index, target, number_of_qubits)

        if control_value == 1 and target_value == 1:
            result[index] *= -1

    return normalize(result)


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MeasurementResult:
    bit: int
    probability: float


def measure_qubit(
    state: Sequence[complex],
    qubit: int,
    number_of_qubits: int,
    rng: random.Random,
) -> tuple[ComplexVector, MeasurementResult]:
    """
    Projectively measure one qubit in the computational basis.

    The returned state is the post-measurement collapsed state.
    """
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension does not match qubit count.")

    probabilities = [0.0, 0.0]

    for index, amplitude in enumerate(state):
        bit = get_bit(index, qubit, number_of_qubits)
        probabilities[bit] += abs(amplitude) ** 2

    total = sum(probabilities)
    if abs(total - 1.0) > 1e-8:
        raise ArithmeticError("Measurement requires a normalized state.")

    sample = rng.random()
    measured_bit = 0 if sample < probabilities[0] else 1
    probability = probabilities[measured_bit]

    if probability < EPSILON:
        raise ArithmeticError("Measurement selected an impossible outcome.")

    collapsed = [
        amplitude if get_bit(index, qubit, number_of_qubits) == measured_bit else 0j
        for index, amplitude in enumerate(state)
    ]

    collapsed = normalize(collapsed)
    return collapsed, MeasurementResult(measured_bit, probability)


def measure_two_qubits(
    state: Sequence[complex],
    first_qubit: int,
    second_qubit: int,
    number_of_qubits: int,
    rng: random.Random,
) -> tuple[ComplexVector, tuple[int, int]]:
    """
    Jointly measure two qubits.

    This is useful for the teleportation protocol because Alice's Bell-basis
    measurement can be represented by measuring her two qubits after the
    appropriate basis-changing gates.
    """
    if first_qubit == second_qubit:
        raise ValueError("Measured qubits must be distinct.")

    probabilities = {(0, 0): 0.0, (0, 1): 0.0, (1, 0): 0.0, (1, 1): 0.0}

    for index, amplitude in enumerate(state):
        outcome = (
            get_bit(index, first_qubit, number_of_qubits),
            get_bit(index, second_qubit, number_of_qubits),
        )
        probabilities[outcome] += abs(amplitude) ** 2

    draw = rng.random()
    cumulative = 0.0
    chosen = None

    for outcome, probability in probabilities.items():
        cumulative += probability
        if draw <= cumulative:
            chosen = outcome
            break

    if chosen is None:
        chosen = (1, 1)

    selected_probability = probabilities[chosen]
    if selected_probability < EPSILON:
        raise ArithmeticError("Joint measurement selected an impossible outcome.")

    collapsed = [
        amplitude
        if (
            get_bit(index, first_qubit, number_of_qubits),
            get_bit(index, second_qubit, number_of_qubits),
        ) == chosen
        else 0j
        for index, amplitude in enumerate(state)
    ]

    return normalize(collapsed), chosen


# ---------------------------------------------------------------------------
# State inspection and fidelity
# ---------------------------------------------------------------------------

def format_complex(value: complex, precision: int = 4) -> str:
    """Render a complex amplitude compactly."""
    real = round(value.real, precision)
    imag = round(value.imag, precision)

    if abs(imag) < 10 ** (-precision):
        return f"{real:g}"
    if abs(real) < 10 ** (-precision):
        return f"{imag:g}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:g}{sign}{abs(imag):g}i"


def print_state(
    state: Sequence[complex],
    label: str,
    threshold: float = 1e-8,
) -> None:
    """Print only computational-basis components with meaningful amplitudes."""
    number_of_qubits = int(math.log2(len(state)))
    print(f"\n{label}")

    for index, amplitude in enumerate(state):
        if abs(amplitude) > threshold:
            basis = format(index, f"0{number_of_qubits}b")
            print(f"  |{basis}> : {format_complex(amplitude)}")


def single_qubit_fidelity(
    actual: Sequence[complex],
    expected: Sequence[complex],
) -> float:
    """
    Pure-state fidelity F = |<expected|actual>|^2.

    F = 1 means identical physical pure states up to global phase.
    """
    if len(actual) != 2 or len(expected) != 2:
        raise ValueError("Single-qubit fidelity requires two-dimensional states.")

    overlap = inner_product(expected, actual)
    return abs(overlap) ** 2


def extract_qubit_when_product(
    state: Sequence[complex],
    target_qubit: int,
    number_of_qubits: int,
) -> ComplexVector:
    """
    Extract a qubit from a product state.

    This helper intentionally rejects entangled states because a single
    qubit does not have its own state vector when the global state is entangled.
    """
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension does not match qubit count.")

    amplitudes = [0j, 0j]

    for index, amplitude in enumerate(state):
        target_value = get_bit(index, target_qubit, number_of_qubits)

        other_index = index
        other_index = index_with_bit(
            other_index,
            target_qubit,
            0,
        )

        # The extraction is safe for the final post-teleportation state only
        # after Alice's qubits have been measured and the system is separable.
        amplitudes[target_value] += amplitude

    norm = vector_norm(amplitudes)
    if norm < EPSILON:
        raise ValueError("Target qubit has no extractable pure state.")

    return normalize(amplitudes)


# ---------------------------------------------------------------------------
# Density matrices and reduced states
# ---------------------------------------------------------------------------

def outer_product(
    vector: Sequence[complex],
) -> ComplexMatrix:
    """Construct |psi><psi|."""
    return [
        [row_value * column_value.conjugate() for column_value in vector]
        for row_value in vector
    ]


def partial_trace_keep_one_qubit(
    state: Sequence[complex],
    kept_qubit: int,
    number_of_qubits: int,
) -> ComplexMatrix:
    """
    Compute the reduced density matrix of one qubit.

    This routine performs the partial trace over all other qubits.
    The density-matrix representation is important because an entangled
    qubit generally cannot be represented by a pure two-component vector.
    """
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension does not match qubit count.")

    reduced = [[0j, 0j], [0j, 0j]]

    for row in range(2):
        for column in range(2):
            total = 0j

            for environment in range(2 ** (number_of_qubits - 1)):
                row_index = 0
                column_index = 0
                environment_bit_position = 0

                for qubit in range(number_of_qubits):
                    if qubit == kept_qubit:
                        row_bit = row
                        column_bit = column
                    else:
                        bit = (
                            environment
                            >> (number_of_qubits - 2 - environment_bit_position)
                        ) & 1
                        environment_bit_position += 1
                        row_bit = bit
                        column_bit = bit

                    row_index = (row_index << 1) | row_bit
                    column_index = (column_index << 1) | column_bit

                total += state[row_index] * state[column_index].conjugate()

            reduced[row][column] = total

    return reduced


def matrix_trace(matrix: ComplexMatrix) -> complex:
    """Return the trace of a square matrix."""
    return sum(matrix[i][i] for i in range(len(matrix)))


def print_density_matrix(matrix: ComplexMatrix, label: str) -> None:
    """Print a small density matrix."""
    print(f"\n{label}")
    for row in matrix:
        print("  " + "  ".join(format_complex(value) for value in row))


# ---------------------------------------------------------------------------
# Teleportation-specific structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TeleportationRun:
    input_state: ComplexVector
    measurement_bits: tuple[int, int]
    corrected_state: ComplexVector
    fidelity: float


def prepare_bell_pair() -> ComplexVector:
    """
    Prepare the Bell state |Phi+> = (|00> + |11>) / sqrt(2).

    The first H creates superposition and CNOT correlates the second qubit.
    """
    state = basis_state("00")
    state = apply_single_qubit_gate(state, H, 0, 2)
    state = apply_controlled_x(state, 0, 1, 2)
    return state


def prepare_teleportation_register(
    input_state: Sequence[complex],
) -> ComplexVector:
    """
    Build |psi> tensor |Phi+>.

    Qubit ordering:
      q0 = Alice's unknown state
      q1 = Alice's half of the Bell pair
      q2 = Bob's half of the Bell pair
    """
    if len(input_state) != 2:
        raise ValueError("Teleportation input must be one qubit.")

    bell_pair = prepare_bell_pair()
    return tensor_product_vectors(input_state, bell_pair)


def alice_bell_measurement(
    state: Sequence[complex],
    rng: random.Random,
) -> tuple[ComplexVector, tuple[int, int]]:
    """
    Perform Alice's Bell-basis measurement.

    Alice first applies CNOT(q0 -> q1) and H(q0), converting the Bell basis
    into the computational basis. Measuring q0 and q1 then yields two
    classical bits.
    """
    state = apply_controlled_x(state, 0, 1, 3)
    state = apply_single_qubit_gate(state, H, 0, 3)
    return measure_two_qubits(state, 0, 1, 3, rng)


def bob_correction(
    state: Sequence[complex],
    measurement_bits: tuple[int, int],
) -> ComplexVector:
    """
    Apply Bob's correction based on Alice's two classical bits.

    If Alice obtains:
      00 -> I
      01 -> X
      10 -> Z
      11 -> X then Z

    The correction is classically controlled. Entanglement alone does not
    give Bob enough information to reconstruct the state before these bits
    arrive.
    """
    first_bit, second_bit = measurement_bits

    if second_bit == 1:
        state = apply_single_qubit_gate(state, X, 2, 3)

    if first_bit == 1:
        state = apply_single_qubit_gate(state, Z, 2, 3)

    return state


def extract_bob_state_after_measurement(
    state: Sequence[complex],
    measurement_bits: tuple[int, int],
) -> ComplexVector:
    """
    Extract Bob's state after Alice's two qubits have collapsed.

    The selected classical measurement result determines exactly one pair
    of Alice basis bits, so the global state is separable at this point.
    """
    bob_amplitudes = [0j, 0j]

    for index, amplitude in enumerate(state):
        bits = (
            get_bit(index, 0, 3),
            get_bit(index, 1, 3),
            get_bit(index, 2, 3),
        )

        if bits[:2] == measurement_bits:
            bob_amplitudes[bits[2]] += amplitude

    return normalize(bob_amplitudes)


# ---------------------------------------------------------------------------
# Complete protocol
# ---------------------------------------------------------------------------

def teleport(
    input_state: Sequence[complex],
    seed: int | None = None,
) -> TeleportationRun:
    """Run one complete quantum teleportation experiment."""
    input_state = normalize(list(input_state))
    rng = random.Random(seed)

    register = prepare_teleportation_register(input_state)

    print_state(register, "Initial three-qubit teleportation register")

    collapsed, measurement_bits = alice_bell_measurement(register, rng)

    print_state(
        collapsed,
        f"State after Alice's Bell measurement {measurement_bits}",
    )

    bob_before_correction = extract_bob_state_after_measurement(
        collapsed,
        measurement_bits,
    )

    print(
        "\nBob's state immediately after Alice's measurement "
        "(before classical correction):"
    )
    print(
        f"  {format_complex(bob_before_correction[0])}|0> + "
        f"{format_complex(bob_before_correction[1])}|1>"
    )

    corrected = bob_correction(collapsed, measurement_bits)
    bob_after_correction = extract_bob_state_after_measurement(
        corrected,
        measurement_bits,
    )

    fidelity = single_qubit_fidelity(bob_after_correction, input_state)

    print("\nBob's state after conditional correction:")
    print(
        f"  {format_complex(bob_after_correction[0])}|0> + "
        f"{format_complex(bob_after_correction[1])}|1>"
    )
    print(f"  Fidelity with original state: {fidelity:.12f}")

    return TeleportationRun(
        input_state=list(input_state),
        measurement_bits=measurement_bits,
        corrected_state=bob_after_correction,
        fidelity=fidelity,
    )


# ---------------------------------------------------------------------------
# Bell-state analysis
# ---------------------------------------------------------------------------

def demonstrate_bell_entanglement() -> None:
    """Show why Bob's half of an entangled pair is not a pure known qubit."""
    bell_pair = prepare_bell_pair()

    print_state(bell_pair, "Prepared Bell state |Phi+>")

    reduced_bob = partial_trace_keep_one_qubit(
        bell_pair,
        kept_qubit=1,
        number_of_qubits=2,
    )

    print_density_matrix(
        reduced_bob,
        "Bob's reduced density matrix before teleportation",
    )

    print(
        f"  Trace = {matrix_trace(reduced_bob).real:.6f}; "
        "a maximally mixed single-qubit state has trace 1."
    )


# ---------------------------------------------------------------------------
# No-cloning demonstration
# ---------------------------------------------------------------------------

def demonstrate_no_cloning_constraint() -> None:
    """
    Demonstrate that teleportation moves the state rather than copying it.

    After Alice measures her original qubit, the original quantum information
    is no longer available as an untouched copy. The protocol therefore does
    not violate the no-cloning theorem.
    """
    print("\nNo-cloning constraint:")
    print(
        "  Alice's original qubit participates in the Bell measurement. "
        "It is not retained as an independent copy."
    )
    print(
        "  Bob reconstructs the state only after receiving two classical bits."
    )


# ---------------------------------------------------------------------------
# Controlled experiment across several input states
# ---------------------------------------------------------------------------

def run_representative_states() -> None:
    """
    Teleport states from different regions of the Bloch sphere.

    Real amplitudes demonstrate basis/superposition states, while complex
    amplitudes demonstrate that teleportation preserves relative phase.
    """
    examples = {
        "|0>": qubit_state(1, 0),
        "|1>": qubit_state(0, 1),
        "|+>": qubit_state(1, 1),
        "|->": qubit_state(1, -1),
        "phase state": qubit_state(1, 1j),
        "non-trivial complex state": qubit_state(1 + 0.5j, 0.7 - 0.2j),
    }

    print("\nRepresentative teleportation states:")

    for name, state in examples.items():
        result = teleport(state, seed=hash(name) & 0xFFFFFFFF)
        status = "PASS" if result.fidelity > 1 - 1e-9 else "FAIL"
        print(f"  {name:26s} {status}  fidelity={result.fidelity:.12f}")


# ---------------------------------------------------------------------------
# Noise model
# ---------------------------------------------------------------------------

def depolarizing_channel(
    state: Sequence[complex],
    error_probability: float,
    rng: random.Random,
) -> ComplexVector:
    """
    Apply a simple stochastic Pauli noise model.

    With probability p, one of X, Y, or Z is applied. This is a pedagogical
    channel rather than a full density-matrix noise simulator.
    """
    if not 0.0 <= error_probability <= 1.0:
        raise ValueError("Error probability must lie between 0 and 1.")

    draw = rng.random()

    if draw >= error_probability:
        return list(state)

    gate = rng.choice((X, Y, Z))
    return normalize(matrix_vector_multiply(gate, state))


def teleport_with_channel_noise(
    input_state: Sequence[complex],
    error_probability: float,
    trials: int = 1000,
    seed: int = 12345,
) -> float:
    """
    Estimate average teleportation fidelity under stochastic channel noise.

    Noise is inserted on Bob's qubit after Alice's classical outcome has been
    encoded but before Bob's correction. This isolates the effect of a noisy
    quantum channel from the ideal protocol logic.
    """
    if trials <= 0:
        raise ValueError("Number of trials must be positive.")

    rng = random.Random(seed)
    fidelities: list[float] = []

    for _ in range(trials):
        register = prepare_teleportation_register(input_state)
        collapsed, bits = alice_bell_measurement(register, rng)

        # Extract Bob's state, inject channel noise, then place it back into
        # the measured branch so that Bob's correction remains explicit.
        bob_state = extract_bob_state_after_measurement(collapsed, bits)
        noisy_bob = depolarizing_channel(
            bob_state,
            error_probability,
            rng,
        )

        # Once Alice's measurement has happened, Bob's qubit is separable.
        # Reconstructing the branch here avoids pretending that the stochastic
        # channel is a deterministic unitary.
        corrected_bob = list(noisy_bob)

        if bits[1] == 1:
            corrected_bob = normalize(
                matrix_vector_multiply(X, corrected_bob)
            )

        if bits[0] == 1:
            corrected_bob = normalize(
                matrix_vector_multiply(Z, corrected_bob)
            )

        fidelities.append(
            single_qubit_fidelity(corrected_bob, input_state)
        )

    return sum(fidelities) / len(fidelities)


def demonstrate_noise() -> None:
    """Compare ideal and noisy teleportation fidelity."""
    state = qubit_state(0.8 + 0.2j, 0.4 - 0.1j)

    print("\nStochastic Pauli-channel experiment:")

    for probability in (0.0, 0.01, 0.05, 0.10, 0.25):
        average = teleport_with_channel_noise(
            state,
            error_probability=probability,
            trials=2000,
        )
        print(
            f"  error probability={probability:>4.2f} "
            f"average fidelity={average:.5f}"
        )


# ---------------------------------------------------------------------------
# Protocol invariants and validation
# ---------------------------------------------------------------------------

def validate_protocol_invariants() -> None:
    """Check mathematical invariants required by the teleportation protocol."""
    print("\nProtocol invariant checks:")

    for name, state in {
        "zero state": qubit_state(1, 0),
        "one state": qubit_state(0, 1),
        "plus state": qubit_state(1, 1),
        "complex state": qubit_state(0.6 + 0.2j, 0.4 - 0.7j),
    }.items():
        result = teleport(state, seed=42)

        if abs(vector_norm(result.corrected_state) - 1.0) > 1e-9:
            raise AssertionError(f"{name} lost normalization.")

        if result.fidelity < 1 - 1e-9:
            raise AssertionError(f"{name} was not teleported exactly.")

    print("  Normalization preserved.")
    print("  Corrected Bob states match the input states.")
    print("  All tested protocol branches satisfy the ideal-state invariant.")


# ---------------------------------------------------------------------------
# Complexity discussion encoded as executable metadata
# ---------------------------------------------------------------------------

def complexity_profile() -> None:
    """
    Print practical scaling characteristics of this educational simulator.

    A full state-vector simulator requires 2^n complex amplitudes for n qubits.
    The teleportation circuit itself uses only three qubits, but the same
    representation becomes expensive rapidly as n increases.
    """
    print("\nState-vector simulation scaling:")

    for qubits in (3, 10, 20, 30, 40):
        amplitudes = 2 ** qubits
        print(
            f"  {qubits:2d} qubits -> {amplitudes:,} complex amplitudes"
        )

    print(
        "  Teleportation uses three qubits, so its ideal state vector is tiny; "
        "large-scale quantum simulation is constrained by exponential memory."
    )


# ---------------------------------------------------------------------------
# Production-oriented validation
# ---------------------------------------------------------------------------

def demonstrate_failure_conditions() -> None:
    """Exercise input validation relevant to a quantum protocol simulator."""
    print("\nFailure-condition checks:")

    invalid_inputs = [
        ("empty state", lambda: qubit_state(0, 0)),
        ("bad basis", lambda: basis_state("012")),
        ("invalid noise", lambda: depolarizing_channel([1, 0], 1.5, random.Random())),
        ("invalid gate target", lambda: apply_single_qubit_gate(
            basis_state("00"),
            H,
            2,
            2,
        )),
    ]

    for description, operation in invalid_inputs:
        try:
            operation()
        except (ValueError, ArithmeticError):
            print(f"  {description}: correctly rejected")
        else:
            raise AssertionError(f"Invalid operation was accepted: {description}")


# ---------------------------------------------------------------------------
# Main educational execution
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("QUANTUM TELEPORTATION: QUANTUM INFORMATION TRANSFER")
    print("=" * 72)

    print(
        "\nCore protocol:"
        "\n  Alice has an unknown qubit |psi>."
        "\n  Alice and Bob share an entangled Bell pair."
        "\n  Alice performs a Bell-basis measurement."
        "\n  Alice obtains two classical bits."
        "\n  Bob applies a classically selected correction."
        "\n  Bob's qubit becomes the original |psi>."
    )

    demonstrate_bell_entanglement()
    run_representative_states()
    demonstrate_no_cloning_constraint()
    demonstrate_noise()
    validate_protocol_invariants()
    demonstrate_failure_conditions()
    complexity_profile()

    print("\n" + "=" * 72)
    print("Quantum teleportation simulation completed.")
    print("=" * 72)


if __name__ == "__main__":
    main()
