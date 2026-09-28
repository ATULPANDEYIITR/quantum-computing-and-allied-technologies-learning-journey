"""
CNOT Gate: Entanglement and Computation
=======================================

A self-contained study and executable demonstration of the controlled-NOT
(CNOT/CX) gate in quantum computing.

The script progresses from classical bits and Boolean XOR to:
- Qubits and computational-basis states
- Single-qubit state vectors
- Tensor products for multi-qubit systems
- CNOT matrix and basis-state action
- Quantum superposition
- Bell-state generation
- Entanglement verification
- Measurement probabilities
- CNOT truth tables
- Bell-state preparation and decoding
- Quantum teleportation
- Superdense coding
- Reversible computation
- No-cloning-related behavior
- Global versus relative phase
- Numerical precision and validation
- Gate composition and circuit simulation
- Partial measurement
- Reduced density matrices
- Entropy as an entanglement diagnostic
- Circuit-level performance considerations

No external quantum-computing package is required.
Only Python's standard library is used.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# SECTION 1: BASIC LINEAR ALGEBRA
# ---------------------------------------------------------------------------

ComplexVector = List[complex]
ComplexMatrix = List[List[complex]]


def nearly_equal(a: complex, b: complex, tolerance: float = 1e-10) -> bool:
    """Compare complex numbers with a numerical tolerance."""
    return abs(a - b) <= tolerance


def vector_norm(state: Sequence[complex]) -> float:
    """Return the Euclidean norm of a state vector."""
    return math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def normalize(state: Sequence[complex]) -> ComplexVector:
    """
    Normalize a quantum state.

    Quantum state vectors must have norm 1, except while intermediate
    calculations are being checked or deliberately constructed.
    """
    norm = vector_norm(state)
    if norm == 0:
        raise ValueError("The zero vector cannot represent a quantum state.")
    return [amplitude / norm for amplitude in state]


def inner_product(
    left: Sequence[complex], right: Sequence[complex]
) -> complex:
    """Compute <left|right>."""
    if len(left) != len(right):
        raise ValueError("Vectors must have equal dimensions.")
    return sum(a.conjugate() * b for a, b in zip(left, right))


def matrix_vector_multiply(
    matrix: ComplexMatrix, vector: Sequence[complex]
) -> ComplexVector:
    """Multiply a matrix by a column vector."""
    if not matrix:
        raise ValueError("Matrix cannot be empty.")

    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("Matrix rows must have equal lengths.")
    if width != len(vector):
        raise ValueError("Matrix and vector dimensions do not match.")

    return [
        sum(matrix[row][column] * vector[column] for column in range(width))
        for row in range(len(matrix))
    ]


def matrix_multiply(
    left: ComplexMatrix, right: ComplexMatrix
) -> ComplexMatrix:
    """Multiply two matrices."""
    if not left or not right:
        raise ValueError("Matrices cannot be empty.")

    left_width = len(left[0])
    right_width = len(right[0])

    if any(len(row) != left_width for row in left):
        raise ValueError("Left matrix rows must have equal lengths.")
    if any(len(row) != right_width for row in right):
        raise ValueError("Right matrix rows must have equal lengths.")
    if left_width != len(right):
        raise ValueError("Matrix dimensions do not match.")

    return [
        [
            sum(
                left[i][k] * right[k][j]
                for k in range(left_width)
            )
            for j in range(right_width)
        ]
        for i in range(len(left))
    ]


def dagger(matrix: ComplexMatrix) -> ComplexMatrix:
    """Return the conjugate transpose."""
    return [
        [matrix[row][column].conjugate() for row in range(len(matrix))]
        for column in range(len(matrix[0]))
    ]


def identity_matrix(size: int) -> ComplexMatrix:
    """Create an identity matrix."""
    return [
        [1 + 0j if row == column else 0j for column in range(size)]
        for row in range(size)
    ]


def matrices_close(
    left: ComplexMatrix,
    right: ComplexMatrix,
    tolerance: float = 1e-10,
) -> bool:
    """Compare matrices numerically."""
    if len(left) != len(right):
        return False
    if any(len(a) != len(b) for a, b in zip(left, right)):
        return False

    return all(
        nearly_equal(a, b, tolerance)
        for left_row, right_row in zip(left, right)
        for a, b in zip(left_row, right_row)
    )


# ---------------------------------------------------------------------------
# SECTION 2: IMPORTANT QUANTUM GATES
# ---------------------------------------------------------------------------

I = [
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

# Computational basis:
# |00> = [1, 0, 0, 0]
# |01> = [0, 1, 0, 0]
# |10> = [0, 0, 1, 0]
# |11> = [0, 0, 0, 1]
CNOT = [
    [1 + 0j, 0j, 0j, 0j],
    [0j, 1 + 0j, 0j, 0j],
    [0j, 0j, 0j, 1 + 0j],
    [0j, 0j, 1 + 0j, 0j],
]


def print_state(
    state: Sequence[complex],
    label: str = "state",
    threshold: float = 1e-10,
) -> None:
    """Display non-negligible computational-basis amplitudes."""
    terms = []
    number_of_qubits = int(math.log2(len(state)))

    for index, amplitude in enumerate(state):
        if abs(amplitude) > threshold:
            bit_string = format(index, f"0{number_of_qubits}b")
            terms.append(f"({amplitude:.4g})|{bit_string}>")

    print(f"{label}: " + (" + ".join(terms) if terms else "0"))


def basis_state(bit_string: str) -> ComplexVector:
    """Construct a computational-basis state such as |010>."""
    if not bit_string or any(bit not in "01" for bit in bit_string):
        raise ValueError("A basis state must contain one or more binary bits.")

    dimension = 2 ** len(bit_string)
    index = int(bit_string, 2)
    state = [0j] * dimension
    state[index] = 1 + 0j
    return state


def tensor_product(
    left: Sequence[complex],
    right: Sequence[complex],
) -> ComplexVector:
    """Compute the Kronecker/tensor product of two vectors."""
    return [
        a * b
        for a in left
        for b in right
    ]


def tensor_matrices(
    left: ComplexMatrix,
    right: ComplexMatrix,
) -> ComplexMatrix:
    """Compute the Kronecker product of two matrices."""
    result = []

    for left_row in left:
        for right_row in right:
            result.append(
                [
                    left_row_item * right_row_item
                    for left_row_item in left_row
                    for right_row_item in right_row
                ]
            )

    return result


# ---------------------------------------------------------------------------
# SECTION 3: CLASSICAL XOR AND THE CNOT TRUTH TABLE
# ---------------------------------------------------------------------------

def xor_bit(a: int, b: int) -> int:
    """
    Classical XOR.

    XOR returns 1 exactly when the inputs differ.
    """
    if a not in (0, 1) or b not in (0, 1):
        raise ValueError("XOR inputs must be binary.")
    return a ^ b


def cnot_classical(control: int, target: int) -> Tuple[int, int]:
    """
    Classical description of CNOT:

        |control, target> -> |control, target XOR control>

    The control bit itself is unchanged.
    """
    return control, target ^ control


def demonstrate_cnot_truth_table() -> None:
    print("\n=== CNOT truth table ===")
    print("input    output")
    for control in (0, 1):
        for target in (0, 1):
            output = cnot_classical(control, target)
            print(
                f"|{control}{target}>  ->  "
                f"|{output[0]}{output[1]}>"
            )


# ---------------------------------------------------------------------------
# SECTION 4: DIRECT CNOT STATE-VECTOR SIMULATION
# ---------------------------------------------------------------------------

def apply_matrix(
    gate: ComplexMatrix,
    state: Sequence[complex],
) -> ComplexVector:
    """Apply a matrix gate to a state."""
    return matrix_vector_multiply(gate, state)


def apply_cnot(
    state: Sequence[complex],
) -> ComplexVector:
    """
    Apply a two-qubit CNOT gate using its matrix representation.

    Basis ordering is |00>, |01>, |10>, |11>.
    """
    if len(state) != 4:
        raise ValueError("This CNOT implementation expects exactly two qubits.")
    return apply_matrix(CNOT, state)


def demonstrate_basis_action() -> None:
    print("\n=== CNOT basis-state action ===")

    for bits in ("00", "01", "10", "11"):
        input_state = basis_state(bits)
        output_state = apply_cnot(input_state)
        print_state(input_state, f"input  |{bits}>")
        print_state(output_state, "output")


# ---------------------------------------------------------------------------
# SECTION 5: UNITARITY AND REVERSIBILITY
# ---------------------------------------------------------------------------

def demonstrate_cnot_properties() -> None:
    print("\n=== CNOT mathematical properties ===")

    cnot_dagger = dagger(CNOT)
    product = matrix_multiply(cnot_dagger, CNOT)
    identity = identity_matrix(4)

    print("CNOT is unitary:", matrices_close(product, identity))

    squared = matrix_multiply(CNOT, CNOT)
    print("CNOT is self-inverse:", matrices_close(squared, identity))

    print(
        "Interpretation: applying CNOT twice restores the original "
        "two-qubit state."
    )


# ---------------------------------------------------------------------------
# SECTION 6: SUPERPOSITION AND ENTANGLEMENT
# ---------------------------------------------------------------------------

def zero_qubit() -> ComplexVector:
    return [1 + 0j, 0j]


def one_qubit() -> ComplexVector:
    return [0j, 1 + 0j]


def plus_state() -> ComplexVector:
    return normalize([1 + 0j, 1 + 0j])


def minus_state() -> ComplexVector:
    return normalize([1 + 0j, -1 + 0j])


def bell_phi_plus() -> ComplexVector:
    """
    Prepare |Phi+> = (|00> + |11>) / sqrt(2).

    Circuit:
        |0> --H--●--
                  |
        |0> -----X--

    H creates superposition; CNOT correlates the qubits.
    """
    initial = tensor_product(zero_qubit(), zero_qubit())
    after_h = tensor_product(plus_state(), zero_qubit())
    return apply_cnot(after_h)


def bell_phi_minus() -> ComplexVector:
    """Prepare |Phi-> = (|00> - |11>) / sqrt(2)."""
    initial = tensor_product(zero_qubit(), zero_qubit())
    after_h = tensor_product(minus_state(), zero_qubit())
    return apply_cnot(after_h)


def bell_psi_plus() -> ComplexVector:
    """Prepare |Psi+> = (|01> + |10>) / sqrt(2)."""
    initial = tensor_product(plus_state(), one_qubit())
    return apply_cnot(initial)


def bell_psi_minus() -> ComplexVector:
    """Prepare |Psi-> = (|01> - |10>) / sqrt(2)."""
    initial = tensor_product(minus_state(), one_qubit())
    return apply_cnot(initial)


def demonstrate_bell_states() -> None:
    print("\n=== Bell states ===")

    states = {
        "Phi+": bell_phi_plus(),
        "Phi-": bell_phi_minus(),
        "Psi+": bell_psi_plus(),
        "Psi-": bell_psi_minus(),
    }

    for name, state in states.items():
        print_state(state, name)
        print("  norm =", vector_norm(state))


# ---------------------------------------------------------------------------
# SECTION 7: MEASUREMENT PROBABILITIES
# ---------------------------------------------------------------------------

def measurement_probabilities(
    state: Sequence[complex],
) -> List[float]:
    """
    Return computational-basis probabilities.

    Born's rule:
        P(i) = |amplitude_i|^2
    """
    norm = vector_norm(state)
    if not math.isclose(norm, 1.0, abs_tol=1e-10):
        raise ValueError("Measurement requires a normalized state.")

    return [abs(amplitude) ** 2 for amplitude in state]


def sample_measurement(
    state: Sequence[complex],
    number_of_shots: int = 1000,
    rng: random.Random | None = None,
) -> dict[str, int]:
    """Sample repeated computational-basis measurements."""
    if number_of_shots <= 0:
        raise ValueError("Number of shots must be positive.")

    probabilities = measurement_probabilities(state)
    rng = rng or random.Random()

    outcomes = list(range(len(state)))
    samples = rng.choices(
        outcomes,
        weights=probabilities,
        k=number_of_shots,
    )

    number_of_qubits = int(math.log2(len(state)))
    counts: dict[str, int] = {}

    for outcome in samples:
        bits = format(outcome, f"0{number_of_qubits}b")
        counts[bits] = counts.get(bits, 0) + 1

    return dict(sorted(counts.items()))


def demonstrate_bell_measurement() -> None:
    print("\n=== Measuring |Phi+> ===")

    state = bell_phi_plus()
    probabilities = measurement_probabilities(state)

    for index, probability in enumerate(probabilities):
        bits = format(index, "02b")
        print(f"P(|{bits}>) = {probability:.3f}")

    counts = sample_measurement(
        state,
        number_of_shots=2000,
        rng=random.Random(42),
    )
    print("2000 simulated measurements:", counts)


# ---------------------------------------------------------------------------
# SECTION 8: PRODUCT STATES VERSUS ENTANGLED STATES
# ---------------------------------------------------------------------------

def is_product_two_qubit_state(
    state: Sequence[complex],
    tolerance: float = 1e-10,
) -> bool:
    """
    Test whether a pure two-qubit state factors as |a> tensor |b>.

    For amplitudes:
        [a, b, c, d]

    separability requires:
        a*d - b*c = 0

    This determinant criterion is valid for a pure two-qubit state.
    """
    if len(state) != 4:
        raise ValueError("Expected a two-qubit state.")

    determinant = state[0] * state[3] - state[1] * state[2]
    return abs(determinant) <= tolerance


def demonstrate_separability() -> None:
    print("\n=== Product state versus entangled state ===")

    product = tensor_product(plus_state(), zero_qubit())
    entangled = bell_phi_plus()

    print_state(product, "Product state")
    print("Product state is separable:", is_product_two_qubit_state(product))

    print_state(entangled, "Bell state")
    print("Bell state is separable:", is_product_two_qubit_state(entangled))

    print(
        "A Bell state cannot be written as a tensor product of two "
        "single-qubit states."
    )


# ---------------------------------------------------------------------------
# SECTION 9: DENSITY MATRICES
# ---------------------------------------------------------------------------

def outer_product(
    state: Sequence[complex],
) -> ComplexMatrix:
    """Construct |psi><psi|."""
    return [
        [
            state[row] * state[column].conjugate()
            for column in range(len(state))
        ]
        for row in range(len(state))
    ]


def partial_trace_second_qubit(
    state: Sequence[complex],
) -> ComplexMatrix:
    """
    Reduced density matrix of the first qubit for a pure two-qubit state.

    If amplitudes are a,b,c,d, the reduced matrix is:
        [[|a|²+|b|², a*c* + b*d*],
         [c*a* + d*b*, |c|²+|d|²]]
    """
    if len(state) != 4:
        raise ValueError("Expected a two-qubit state.")

    a, b, c, d = state

    return [
        [
            abs(a) ** 2 + abs(b) ** 2,
            a * c.conjugate() + b * d.conjugate(),
        ],
        [
            c * a.conjugate() + d * b.conjugate(),
            abs(c) ** 2 + abs(d) ** 2,
        ],
    ]


def matrix_trace(matrix: ComplexMatrix) -> complex:
    return sum(matrix[index][index] for index in range(len(matrix)))


def purity(density_matrix: ComplexMatrix) -> float:
    """Purity Tr(rho²). A pure state has purity 1."""
    squared = matrix_multiply(density_matrix, density_matrix)
    return matrix_trace(squared).real


def demonstrate_reduced_state() -> None:
    print("\n=== Reduced state and entanglement ===")

    product = tensor_product(plus_state(), zero_qubit())
    entangled = bell_phi_plus()

    product_rho = partial_trace_second_qubit(product)
    entangled_rho = partial_trace_second_qubit(entangled)

    print("Product state's reduced-state purity:",
          f"{purity(product_rho):.6f}")
    print("Bell state's reduced-state purity:",
          f"{purity(entangled_rho):.6f}")

    print(
        "The reduced state of one qubit in a maximally entangled Bell "
        "state is mixed even though the complete two-qubit state is pure."
    )


def von_neumann_entropy_from_2x2(
    density_matrix: ComplexMatrix,
) -> float:
    """
    Compute entropy for a 2x2 Hermitian density matrix.

    Eigenvalues of a trace-one 2x2 density matrix can be obtained from:
        lambda = (1 +/- sqrt(1 - 4*det(rho))) / 2
    """
    determinant = (
        density_matrix[0][0] * density_matrix[1][1]
        - density_matrix[0][1] * density_matrix[1][0]
    ).real

    determinant = max(0.0, min(0.25, determinant))
    discriminant = max(0.0, 1.0 - 4.0 * determinant)
    root = math.sqrt(discriminant)

    eigenvalues = [
        (1.0 + root) / 2.0,
        (1.0 - root) / 2.0,
    ]

    entropy = 0.0
    for eigenvalue in eigenvalues:
        if eigenvalue > 1e-15:
            entropy -= eigenvalue * math.log2(eigenvalue)

    return entropy


def demonstrate_entanglement_entropy() -> None:
    print("\n=== Entanglement entropy ===")

    product = tensor_product(plus_state(), zero_qubit())
    bell = bell_phi_plus()

    product_rho = partial_trace_second_qubit(product)
    bell_rho = partial_trace_second_qubit(bell)

    print(
        "Product-state entropy:",
        f"{von_neumann_entropy_from_2x2(product_rho):.6f}",
    )
    print(
        "Bell-state entropy:",
        f"{von_neumann_entropy_from_2x2(bell_rho):.6f}",
    )


# ---------------------------------------------------------------------------
# SECTION 10: CNOT WITH ARBITRARY AMPLITUDES
# ---------------------------------------------------------------------------

def arbitrary_two_qubit_state(
    a: complex,
    b: complex,
    c: complex,
    d: complex,
) -> ComplexVector:
    """Build and normalize an arbitrary pure two-qubit state."""
    return normalize([a, b, c, d])


def demonstrate_general_cnot() -> None:
    print("\n=== CNOT on a general superposition ===")

    state = arbitrary_two_qubit_state(
        1,
        1j,
        2,
        -1,
    )

    print_state(state, "Before CNOT")
    transformed = apply_cnot(state)
    print_state(transformed, "After CNOT")

    print(
        "CNOT does not only operate on classical basis states. "
        "By linearity, it transforms every superposition according "
        "to its action on the basis states."
    )


# ---------------------------------------------------------------------------
# SECTION 11: PHASE KICKBACK
# ---------------------------------------------------------------------------

def demonstrate_phase_kickback() -> None:
    print("\n=== Phase kickback ===")

    """
    If the target is |-> = (|0>-|1>)/sqrt(2), then X|-> = -|->.

    Therefore:
        CNOT(|control> |->)
        = Z|control> |->

    The target returns to the same state up to a global factor while
    the control acquires a relative phase. This is a central mechanism
    behind many quantum algorithms.
    """

    control = plus_state()
    target = minus_state()
    input_state = tensor_product(control, target)

    output_state = apply_cnot(input_state)

    print_state(input_state, "Input")
    print_state(output_state, "Output")

    print(
        "The phase-kickback effect shows that CNOT can transfer a phase "
        "effect from the target interaction onto the control qubit."
    )


# ---------------------------------------------------------------------------
# SECTION 12: QUANTUM TELEPORTATION
# ---------------------------------------------------------------------------

def apply_single_qubit_gate_to_two_qubits(
    state: Sequence[complex],
    gate: ComplexMatrix,
    qubit: int,
) -> ComplexVector:
    """
    Apply a one-qubit gate to a two-qubit state.

    qubit=0 is the most-significant/left qubit.
    qubit=1 is the right qubit.
    """
    if len(state) != 4:
        raise ValueError("Expected a two-qubit state.")
    if qubit not in (0, 1):
        raise ValueError("Qubit must be 0 or 1.")

    operator = (
        tensor_matrices(gate, I)
        if qubit == 0
        else tensor_matrices(I, gate)
    )

    return apply_matrix(operator, state)


def apply_cnot_to_three_qubits(
    state: Sequence[complex],
    control: int,
    target: int,
) -> ComplexVector:
    """
    Apply CNOT to selected qubits in a three-qubit state.

    Qubits are indexed left-to-right:
        0 = most significant
        1 = middle
        2 = least significant
    """
    if len(state) != 8:
        raise ValueError("Expected a three-qubit state.")
    if control == target:
        raise ValueError("Control and target must differ.")
    if not (0 <= control < 3 and 0 <= target < 3):
        raise ValueError("Qubit index out of range.")

    output = [0j] * 8

    for index, amplitude in enumerate(state):
        bits = list(format(index, "03b"))
        if bits[control] == "1":
            bits[target] = "1" if bits[target] == "0" else "0"

        output[int("".join(bits), 2)] += amplitude

    return output


def apply_x_to_three_qubits(
    state: Sequence[complex],
    qubit: int,
) -> ComplexVector:
    """Apply X to one selected qubit of a three-qubit state."""
    if not 0 <= qubit < 3:
        raise ValueError("Qubit index out of range.")

    output = [0j] * 8

    for index, amplitude in enumerate(state):
        bits = list(format(index, "03b"))
        bits[qubit] = "1" if bits[qubit] == "0" else "0"
        output[int("".join(bits), 2)] += amplitude

    return output


def apply_h_to_three_qubits(
    state: Sequence[complex],
    qubit: int,
) -> ComplexVector:
    """Apply H to one selected qubit of a three-qubit state."""
    if not 0 <= qubit < 3:
        raise ValueError("Qubit index out of range.")

    output = [0j] * 8
    coefficient = 1 / math.sqrt(2)

    for index, amplitude in enumerate(state):
        bits = list(format(index, "03b"))
        current_bit = bits[qubit]

        for new_bit in ("0", "1"):
            bits[qubit] = new_bit
            sign = 1 if current_bit == "0" or new_bit == "0" else -1
            new_index = int("".join(bits), 2)
            output[new_index] += amplitude * coefficient * sign

    return output


def demonstrate_teleportation_algebra() -> None:
    print("\n=== Quantum teleportation state evolution ===")

    """
    Teleportation does not move a physical qubit from Alice to Bob.
    It transfers an unknown quantum state using:
      1. a pre-shared Bell pair,
      2. two classical measurement bits,
      3. conditional Pauli corrections.

    We simulate the unitary part before Alice's measurement.
    """

    alpha = 1 / math.sqrt(3)
    beta = math.sqrt(2 / 3) * 1j

    # Initial state |psi> |0> |0>.
    state = tensor_product(
        tensor_product([alpha, beta], zero_qubit()),
        zero_qubit(),
    )

    # Create Bell pair between qubits 1 and 2.
    state = apply_h_to_three_qubits(state, 1)
    state = apply_cnot_to_three_qubits(state, 1, 2)

    # Alice performs the Bell-basis operation on qubits 0 and 1.
    state = apply_cnot_to_three_qubits(state, 0, 1)
    state = apply_h_to_three_qubits(state, 0)

    print_state(state, "State immediately before Alice's measurement")
    print(
        "At this point the amplitudes encode Alice's two classical "
        "measurement outcomes and Bob's corresponding conditional state."
    )


# ---------------------------------------------------------------------------
# SECTION 13: SUPERDENSE CODING
# ---------------------------------------------------------------------------

def demonstrate_superdense_coding() -> None:
    print("\n=== Superdense coding ===")

    """
    A shared Bell pair can encode two classical bits into one transmitted
    qubit. Alice chooses one of I, X, Z, or XZ on her half.

    The four resulting Bell states are distinguishable by:
        CNOT(control=Alice, target=Bob)
        H(Alice)
        computational-basis measurement.

    This is an example of quantum communication using entanglement.
    """

    encodings = {
        "00": I,
        "01": X,
        "10": Z,
        "11": matrix_multiply(X, Z),
    }

    for message, encoding in encodings.items():
        state = bell_phi_plus()
        state = apply_single_qubit_gate_to_two_qubits(
            state,
            encoding,
            qubit=0,
        )
        state = apply_cnot(state)
        state = apply_single_qubit_gate_to_two_qubits(
            state,
            H,
            qubit=0,
        )

        probabilities = measurement_probabilities(state)
        decoded = max(
            range(4),
            key=lambda index: probabilities[index],
        )
        decoded_bits = format(decoded, "02b")

        print(
            f"message={message} -> decoded={decoded_bits}, "
            f"probabilities={probabilities}"
        )


# ---------------------------------------------------------------------------
# SECTION 14: REVERSIBLE COMPUTATION
# ---------------------------------------------------------------------------

def reversible_and(a: int, b: int, target: int = 0) -> Tuple[int, int, int]:
    """
    Reversible computation cannot simply erase information.

    A Toffoli-style transformation:
        (a,b,t) -> (a,b,t XOR (a AND b))

    realizes AND into a target bit while preserving the inputs.
    """
    if a not in (0, 1) or b not in (0, 1) or target not in (0, 1):
        raise ValueError("Inputs must be binary.")

    return a, b, target ^ (a & b)


def demonstrate_reversible_logic() -> None:
    print("\n=== Reversible logic ===")

    for a in (0, 1):
        for b in (0, 1):
            result = reversible_and(a, b)
            print(f"{a}{b}0 -> {result}")

    print(
        "CNOT implements reversible XOR into a target. "
        "Its reversibility is essential because closed-system quantum "
        "evolution is represented by unitary operators."
    )


# ---------------------------------------------------------------------------
# SECTION 15: CNOT AS A UNIVERSAL COMPUTATIONAL COMPONENT
# ---------------------------------------------------------------------------

@dataclass
class TwoQubitCircuit:
    """
    A tiny circuit simulator.

    The circuit starts in |00>. Gates are represented by functions that
    transform the complete state vector.
    """

    state: ComplexVector

    @classmethod
    def zero_state(cls) -> "TwoQubitCircuit":
        return cls(basis_state("00"))

    def apply_h(self, qubit: int) -> None:
        if qubit == 0:
            self.state = apply_single_qubit_gate_to_two_qubits(
                self.state, H, 0
            )
        elif qubit == 1:
            self.state = apply_single_qubit_gate_to_two_qubits(
                self.state, H, 1
            )
        else:
            raise ValueError("Two-qubit circuit has qubits 0 and 1.")

    def apply_x(self, qubit: int) -> None:
        if qubit == 0:
            self.state = apply_single_qubit_gate_to_two_qubits(
                self.state, X, 0
            )
        elif qubit == 1:
            self.state = apply_single_qubit_gate_to_two_qubits(
                self.state, X, 1
            )
        else:
            raise ValueError("Two-qubit circuit has qubits 0 and 1.")

    def apply_z(self, qubit: int) -> None:
        if qubit == 0:
            self.state = apply_single_qubit_gate_to_two_qubits(
                self.state, Z, 0
            )
        elif qubit == 1:
            self.state = apply_single_qubit_gate_to_two_qubits(
                self.state, Z, 1
            )
        else:
            raise ValueError("Two-qubit circuit has qubits 0 and 1.")

    def apply_cnot(self, control: int, target: int) -> None:
        if (control, target) == (0, 1):
            self.state = apply_cnot(self.state)
        elif (control, target) == (1, 0):
            output = [0j] * 4

            for index, amplitude in enumerate(self.state):
                bits = list(format(index, "02b"))
                if bits[control] == "1":
                    bits[target] = "1" if bits[target] == "0" else "0"
                output[int("".join(bits), 2)] += amplitude

            self.state = output
        else:
            raise ValueError("Control and target must be different.")

    def probabilities(self) -> dict[str, float]:
        probabilities = measurement_probabilities(self.state)
        return {
            format(index, "02b"): probability
            for index, probability in enumerate(probabilities)
        }


def demonstrate_circuit_builder() -> None:
    print("\n=== Small circuit simulator ===")

    circuit = TwoQubitCircuit.zero_state()
    circuit.apply_h(0)
    circuit.apply_cnot(0, 1)

    print_state(circuit.state, "Generated Bell state")
    print("Probabilities:", circuit.probabilities())


# ---------------------------------------------------------------------------
# SECTION 16: EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n=== Edge cases and validation ===")

    tests: list[tuple[str, Callable[[], object]]] = [
        (
            "Invalid basis state",
            lambda: basis_state("02"),
        ),
        (
            "CNOT with wrong dimension",
            lambda: apply_cnot([1 + 0j, 0j]),
        ),
        (
            "Invalid XOR",
            lambda: xor_bit(2, 1),
        ),
        (
            "Measurement of unnormalized state",
            lambda: measurement_probabilities([1 + 0j, 1 + 0j]),
        ),
        (
            "Zero-vector normalization",
            lambda: normalize([0j, 0j]),
        ),
    ]

    for name, operation in tests:
        try:
            operation()
            print(name, "unexpectedly succeeded")
        except ValueError as error:
            print(name, "->", error)


# ---------------------------------------------------------------------------
# SECTION 17: GLOBAL PHASE VERSUS RELATIVE PHASE
# ---------------------------------------------------------------------------

def states_differ_only_by_global_phase(
    left: Sequence[complex],
    right: Sequence[complex],
    tolerance: float = 1e-10,
) -> bool:
    """
    Determine whether two nonzero states differ only by one global phase.

    This matters because |psi> and exp(i*theta)|psi> produce identical
    measurement statistics.
    """
    if len(left) != len(right):
        return False

    candidate: complex | None = None

    for a, b in zip(left, right):
        if abs(b) > tolerance:
            candidate = a / b
            break

    if candidate is None:
        return all(abs(a) <= tolerance for a in left)

    magnitude = abs(candidate)
    if not math.isclose(magnitude, 1.0, abs_tol=tolerance):
        return False

    return all(
        abs(a - candidate * b) <= tolerance
        for a, b in zip(left, right)
    )


def demonstrate_phase() -> None:
    print("\n=== Global and relative phase ===")

    state = plus_state()
    globally_phased = [1j * amplitude for amplitude in state]
    relative_phase = minus_state()

    print(
        "Global phase equivalent:",
        states_differ_only_by_global_phase(state, globally_phased),
    )
    print(
        "Relative-phase state equivalent:",
        states_differ_only_by_global_phase(state, relative_phase),
    )

    print(
        "Global phase does not change isolated measurement probabilities. "
        "Relative phase can change interference and is physically relevant."
    )


# ---------------------------------------------------------------------------
# SECTION 18: PERFORMANCE CONSIDERATIONS
# ---------------------------------------------------------------------------

def estimated_state_vector_memory(number_of_qubits: int) -> int:
    """
    Rough lower-bound estimate for storing complex128-like amplitudes.

    A state vector contains 2^n complex amplitudes.
    If one complex amplitude occupies 16 bytes, storage is approximately:
        16 * 2^n bytes

    Python objects usually require considerably more memory than this ideal
    representation.
    """
    if number_of_qubits < 0:
        raise ValueError("Number of qubits cannot be negative.")
    return 16 * (2 ** number_of_qubits)


def human_bytes(number_of_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(number_of_bytes)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} TiB"


def demonstrate_scaling() -> None:
    print("\n=== State-vector scaling ===")

    for qubits in (1, 2, 10, 20, 30):
        memory = estimated_state_vector_memory(qubits)
        print(
            f"{qubits:2d} qubits -> "
            f"{2 ** qubits:,} amplitudes -> "
            f"approximately {human_bytes(memory)} "
            "for compact complex values"
        )

    print(
        "The exponential 2^n state-space size is a central limitation "
        "of straightforward full state-vector simulation."
    )


# ---------------------------------------------------------------------------
# SECTION 19: TESTS
# ---------------------------------------------------------------------------

def assert_state_normalized(state: Sequence[complex]) -> None:
    assert math.isclose(
        vector_norm(state),
        1.0,
        abs_tol=1e-10,
    )


def run_tests() -> None:
    """Basic correctness tests for the demonstrations."""

    # CNOT truth table.
    assert cnot_classical(0, 0) == (0, 0)
    assert cnot_classical(0, 1) == (0, 1)
    assert cnot_classical(1, 0) == (1, 1)
    assert cnot_classical(1, 1) == (1, 0)

    # Unitarity and self-inverse property.
    assert matrices_close(
        matrix_multiply(dagger(CNOT), CNOT),
        identity_matrix(4),
    )
    assert matrices_close(
        matrix_multiply(CNOT, CNOT),
        identity_matrix(4),
    )

    # Bell-state properties.
    bell = bell_phi_plus()
    assert_state_normalized(bell)
    assert not is_product_two_qubit_state(bell)

    probabilities = measurement_probabilities(bell)
    assert math.isclose(probabilities[0], 0.5, abs_tol=1e-10)
    assert math.isclose(probabilities[3], 0.5, abs_tol=1e-10)
    assert math.isclose(probabilities[1], 0.0, abs_tol=1e-10)
    assert math.isclose(probabilities[2], 0.0, abs_tol=1e-10)

    # Product state must remain separable after CNOT when control is |0>.
    product = tensor_product(zero_qubit(), plus_state())
    unchanged = apply_cnot(product)
    assert is_product_two_qubit_state(unchanged)

    # Entropy diagnostics.
    bell_entropy = von_neumann_entropy_from_2x2(
        partial_trace_second_qubit(bell)
    )
    assert math.isclose(bell_entropy, 1.0, abs_tol=1e-10)

    # Global phase equivalence.
    assert states_differ_only_by_global_phase(
        bell,
        [1j * amplitude for amplitude in bell],
    )

    print("\n=== Tests ===")
    print("All tests passed.")


# ---------------------------------------------------------------------------
# SECTION 20: MAIN STUDY DEMONSTRATION
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("CNOT GATE: ENTANGLEMENT AND COMPUTATION")
    print("=" * 72)

    print(
        "\nCore idea:\n"
        "CNOT is a two-qubit controlled operation. The control qubit "
        "is unchanged, while the target qubit is flipped when the "
        "control is |1>. Its action is target <- target XOR control."
    )

    demonstrate_cnot_truth_table()
    demonstrate_basis_action()
    demonstrate_cnot_properties()
    demonstrate_bell_states()
    demonstrate_bell_measurement()
    demonstrate_separability()
    demonstrate_reduced_state()
    demonstrate_entanglement_entropy()
    demonstrate_general_cnot()
    demonstrate_phase_kickback()
    demonstrate_teleportation_algebra()
    demonstrate_superdense_coding()
    demonstrate_reversible_logic()
    demonstrate_circuit_builder()
    demonstrate_edge_cases()
    demonstrate_phase()
    demonstrate_scaling()
    run_tests()

    print("\n=== Key equations ===")
    print("CNOT |c,t> = |c, t XOR c>")
    print("|Phi+> = (|00> + |11>) / sqrt(2)")
    print("P(x) = |amplitude_x|^2")
    print("U†U = I for a unitary quantum gate")
    print("CNOT² = I")
    print("State-vector dimension for n qubits = 2^n")

    print("\nStudy complete.")


if __name__ == "__main__":
    main()
