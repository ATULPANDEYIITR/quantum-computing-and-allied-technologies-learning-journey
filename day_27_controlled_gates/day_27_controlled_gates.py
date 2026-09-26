"""
Controlled Gates: Controlled-X and Controlled Operations
========================================================

A standalone study program covering controlled quantum operations from
beginner to advanced level.

The program uses only the Python standard library. It implements a small
state-vector simulator so that controlled gates can be studied through
actual calculations rather than only through abstract descriptions.

Topics demonstrated:
- Qubits and computational basis states
- Single-qubit gates
- Controlled operations
- Controlled-X (CNOT/CX)
- Truth-table behavior
- Matrix representation
- State-vector simulation
- Multi-qubit indexing
- Controlled-Z and controlled-phase gates
- SWAP built from controlled operations
- Toffoli / controlled-controlled-X
- General controlled unitary operations
- Entanglement
- Bell states
- Measurement probabilities
- Partial measurement intuition
- Reversibility
- Gate validation
- Numerical precision
- Circuit simulation
- Complexity considerations
- Common implementation mistakes
- Practical quantum-circuit examples

No external package is required.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple


EPSILON = 1e-10


# ---------------------------------------------------------------------------
# 1. BASIC MATHEMATICAL REPRESENTATION
# ---------------------------------------------------------------------------

ComplexVector = List[complex]
ComplexMatrix = List[List[complex]]


def clean_complex(value: complex, digits: int = 8) -> complex:
    """Remove tiny floating-point artifacts for readable output."""
    real = 0.0 if abs(value.real) < EPSILON else round(value.real, digits)
    imag = 0.0 if abs(value.imag) < EPSILON else round(value.imag, digits)
    return complex(real, imag)


def format_complex(value: complex) -> str:
    """Format a complex number in a beginner-readable form."""
    value = clean_complex(value)

    if abs(value.imag) < EPSILON:
        return f"{value.real:.6g}"

    if abs(value.real) < EPSILON:
        return f"{value.imag:.6g}i"

    sign = "+" if value.imag >= 0 else "-"
    return f"{value.real:.6g}{sign}{abs(value.imag):.6g}i"


def vector_norm(state: ComplexVector) -> float:
    """Return the Euclidean norm of a quantum state."""
    return math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def normalize_state(state: ComplexVector) -> ComplexVector:
    """
    Normalize a state vector.

    Quantum states must have total probability 1, which means the vector
    norm must be 1.
    """
    norm = vector_norm(state)

    if norm < EPSILON:
        raise ValueError("Cannot normalize a zero vector.")

    return [amplitude / norm for amplitude in state]


def probabilities(state: ComplexVector) -> List[float]:
    """Return measurement probabilities for every computational basis state."""
    return [abs(amplitude) ** 2 for amplitude in state]


def validate_normalized_state(state: ComplexVector) -> None:
    """Reject states whose total probability is not approximately 1."""
    total = sum(probabilities(state))

    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError(
            f"Quantum state is not normalized. Total probability={total}"
        )


# ---------------------------------------------------------------------------
# 2. BASIS STATES
# ---------------------------------------------------------------------------

ZERO = [1.0 + 0.0j, 0.0 + 0.0j]
ONE = [0.0 + 0.0j, 1.0 + 0.0j]


def basis_state(bits: str) -> ComplexVector:
    """
    Create an n-qubit computational basis state.

    Example:
        basis_state("00") -> |00>
        basis_state("10") -> |10>

    The string is treated as the visible quantum-register ordering.
    """
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("bits must be a non-empty binary string.")

    dimension = 2 ** len(bits)
    state = [0.0 + 0.0j] * dimension
    state[int(bits, 2)] = 1.0 + 0.0j
    return state


def basis_label(index: int, number_of_qubits: int) -> str:
    """Convert a basis-state index to a binary label."""
    return format(index, f"0{number_of_qubits}b")


# ---------------------------------------------------------------------------
# 3. SINGLE-QUBIT MATRICES
# ---------------------------------------------------------------------------

I: ComplexMatrix = [
    [1.0 + 0.0j, 0.0 + 0.0j],
    [0.0 + 0.0j, 1.0 + 0.0j],
]

X: ComplexMatrix = [
    [0.0 + 0.0j, 1.0 + 0.0j],
    [1.0 + 0.0j, 0.0 + 0.0j],
]

Y: ComplexMatrix = [
    [0.0 + 0.0j, -1.0j],
    [1.0j, 0.0 + 0.0j],
]

Z: ComplexMatrix = [
    [1.0 + 0.0j, 0.0 + 0.0j],
    [0.0 + 0.0j, -1.0 + 0.0j],
]

HADAMARD: ComplexMatrix = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]


def phase_gate(theta: float) -> ComplexMatrix:
    """
    Return a one-qubit phase gate.

    P(theta) = diag(1, e^(i theta))
    """
    return [
        [1.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, cmath.exp(1j * theta)],
    ]


def matrix_multiply(
    left: ComplexMatrix,
    right: ComplexMatrix,
) -> ComplexMatrix:
    """Multiply two matrices."""
    if not left or not right:
        raise ValueError("Matrices cannot be empty.")

    if len(left[0]) != len(right):
        raise ValueError("Matrix dimensions are incompatible.")

    result = [
        [0.0 + 0.0j for _ in range(len(right[0]))]
        for _ in range(len(left))
    ]

    for row in range(len(left)):
        for column in range(len(right[0])):
            result[row][column] = sum(
                left[row][k] * right[k][column]
                for k in range(len(right))
            )

    return result


def matrix_vector_multiply(
    matrix: ComplexMatrix,
    vector: ComplexVector,
) -> ComplexVector:
    """Multiply a matrix by a vector."""
    if len(matrix[0]) != len(vector):
        raise ValueError("Matrix and vector dimensions are incompatible.")

    return [
        sum(matrix[row][column] * vector[column] for column in range(len(vector)))
        for row in range(len(matrix))
    ]


def conjugate_transpose(matrix: ComplexMatrix) -> ComplexMatrix:
    """Return the conjugate transpose (dagger) of a matrix."""
    return [
        [matrix[row][column].conjugate() for row in range(len(matrix))]
        for column in range(len(matrix[0]))
    ]


def is_unitary(matrix: ComplexMatrix) -> bool:
    """
    A matrix U is unitary when U†U = I.

    Quantum gates must be unitary because quantum evolution is reversible
    and preserves total probability.
    """
    dagger = conjugate_transpose(matrix)
    product = matrix_multiply(dagger, matrix)

    for row in range(len(product)):
        for column in range(len(product)):
            expected = 1.0 if row == column else 0.0
            if not math.isclose(
                product[row][column].real,
                expected,
                abs_tol=1e-9,
            ):
                return False
            if not math.isclose(
                product[row][column].imag,
                0.0,
                abs_tol=1e-9,
            ):
                return False

    return True


# ---------------------------------------------------------------------------
# 4. CONTROLLED OPERATIONS
# ---------------------------------------------------------------------------

def controlled_matrix(target_operation: ComplexMatrix) -> ComplexMatrix:
    """
    Construct the two-qubit controlled version of a 2x2 operation.

    Controlled-U has block-matrix form:

        |0><0| ⊗ I + |1><1| ⊗ U

    In computational basis ordering |00>, |01>, |10>, |11>, this means:

        |00> -> |00>
        |01> -> |01>
        |10>, |11> are transformed by U

    This construction assumes the first qubit is the control and the
    second qubit is the target.
    """
    if len(target_operation) != 2 or any(
        len(row) != 2 for row in target_operation
    ):
        raise ValueError("target_operation must be a 2x2 matrix.")

    result = [[0.0 + 0.0j for _ in range(4)] for _ in range(4)]

    # Control = 0: apply identity to target.
    result[0][0] = 1.0 + 0.0j
    result[1][1] = 1.0 + 0.0j

    # Control = 1: apply U to target.
    result[2][2] = target_operation[0][0]
    result[2][3] = target_operation[0][1]
    result[3][2] = target_operation[1][0]
    result[3][3] = target_operation[1][1]

    return result


CX_MATRIX = controlled_matrix(X)
CY_MATRIX = controlled_matrix(Y)
CZ_MATRIX = controlled_matrix(Z)
CPHASE_PI_OVER_2_MATRIX = controlled_matrix(phase_gate(math.pi / 2))


def print_matrix(matrix: ComplexMatrix, title: str = "") -> None:
    if title:
        print(f"\n{title}")

    for row in matrix:
        print("[ " + ", ".join(format_complex(value) for value in row) + " ]")


def print_state(
    state: ComplexVector,
    title: str = "",
    threshold: float = 1e-9,
) -> None:
    """Print non-zero amplitudes in Dirac notation."""
    if title:
        print(f"\n{title}")

    number_of_qubits = int(math.log2(len(state)))

    terms = []

    for index, amplitude in enumerate(state):
        if abs(amplitude) > threshold:
            label = basis_label(index, number_of_qubits)
            terms.append(f"({format_complex(amplitude)})|{label}>")

    if terms:
        print(" + ".join(terms))
    else:
        print("0")


# ---------------------------------------------------------------------------
# 5. DIRECT CONTROLLED-X STATE TRANSFORMATION
# ---------------------------------------------------------------------------

def apply_single_qubit_matrix_to_two_qubits(
    state: ComplexVector,
    operation: ComplexMatrix,
    target_qubit: int,
) -> ComplexVector:
    """
    Apply a 2x2 gate to one target qubit of an n-qubit state.

    Qubit numbering:
        0 = leftmost/most-significant visible qubit
        n-1 = rightmost/least-significant visible qubit

    The implementation works directly on amplitudes and avoids constructing
    a full 2^n x 2^n matrix.
    """
    number_of_qubits = int(math.log2(len(state)))

    if 2 ** number_of_qubits != len(state):
        raise ValueError("State dimension must be a power of two.")

    if not 0 <= target_qubit < number_of_qubits:
        raise IndexError("target_qubit is outside the register.")

    if len(operation) != 2 or any(len(row) != 2 for row in operation):
        raise ValueError("operation must be a 2x2 matrix.")

    result = state.copy()
    bit_position = number_of_qubits - 1 - target_qubit
    mask = 1 << bit_position

    for base_index in range(len(state)):
        if base_index & mask:
            continue

        zero_index = base_index
        one_index = base_index | mask

        amplitude_zero = state[zero_index]
        amplitude_one = state[one_index]

        result[zero_index] = (
            operation[0][0] * amplitude_zero
            + operation[0][1] * amplitude_one
        )

        result[one_index] = (
            operation[1][0] * amplitude_zero
            + operation[1][1] * amplitude_one
        )

    return result


def apply_controlled_operation(
    state: ComplexVector,
    control_qubit: int,
    target_qubit: int,
    target_operation: ComplexMatrix,
) -> ComplexVector:
    """
    Apply controlled-U directly to an arbitrary n-qubit state.

    Only amplitudes whose control qubit equals |1> are transformed.

    This is usually preferable to explicitly constructing a huge matrix.
    """
    number_of_qubits = int(math.log2(len(state)))

    if 2 ** number_of_qubits != len(state):
        raise ValueError("State dimension must be a power of two.")

    if not 0 <= control_qubit < number_of_qubits:
        raise IndexError("control_qubit is outside the register.")

    if not 0 <= target_qubit < number_of_qubits:
        raise IndexError("target_qubit is outside the register.")

    if control_qubit == target_qubit:
        raise ValueError("Control and target must be different qubits.")

    if len(target_operation) != 2 or any(
        len(row) != 2 for row in target_operation
    ):
        raise ValueError("target_operation must be 2x2.")

    result = state.copy()

    control_bit_position = number_of_qubits - 1 - control_qubit
    target_bit_position = number_of_qubits - 1 - target_qubit

    control_mask = 1 << control_bit_position
    target_mask = 1 << target_bit_position

    for base_index in range(len(state)):
        # Only process the |target=0> member of each target pair.
        if base_index & target_mask:
            continue

        # Control is |0>: controlled operation does nothing.
        if not (base_index & control_mask):
            continue

        zero_index = base_index
        one_index = base_index | target_mask

        amplitude_zero = state[zero_index]
        amplitude_one = state[one_index]

        result[zero_index] = (
            target_operation[0][0] * amplitude_zero
            + target_operation[0][1] * amplitude_one
        )

        result[one_index] = (
            target_operation[1][0] * amplitude_zero
            + target_operation[1][1] * amplitude_one
        )

    return result


def apply_cx(
    state: ComplexVector,
    control_qubit: int,
    target_qubit: int,
) -> ComplexVector:
    """Convenience wrapper for controlled-X."""
    return apply_controlled_operation(
        state,
        control_qubit,
        target_qubit,
        X,
    )


# ---------------------------------------------------------------------------
# 6. BEGINNER EXAMPLES
# ---------------------------------------------------------------------------

def beginner_single_qubit_example() -> None:
    print("\n" + "=" * 72)
    print("BEGINNER: SINGLE-QUBIT GATES")
    print("=" * 72)

    state_zero = ZERO
    state_one = ONE

    print_state(state_zero, "Initial |0>")
    print_state(
        matrix_vector_multiply(X, state_zero),
        "X|0> = |1>",
    )

    print_state(
        matrix_vector_multiply(X, state_one),
        "X|1> = |0>",
    )

    plus_state = matrix_vector_multiply(HADAMARD, state_zero)
    minus_state = matrix_vector_multiply(HADAMARD, state_one)

    print_state(plus_state, "H|0> = |+>")
    print_state(minus_state, "H|1> = |->")

    print("Probabilities for |+>:", probabilities(plus_state))
    print("Probabilities for |->:", probabilities(minus_state))


def cx_truth_table_example() -> None:
    print("\n" + "=" * 72)
    print("BEGINNER: CONTROLLED-X TRUTH TABLE")
    print("=" * 72)

    print("Control Target  ->  Output")
    print("----------------------------")

    for control in "01":
        for target in "01":
            input_state = basis_state(control + target)
            output_state = matrix_vector_multiply(CX_MATRIX, input_state)

            nonzero_index = max(
                range(len(output_state)),
                key=lambda index: abs(output_state[index]),
            )

            print(
                f"   {control}      {target}     ->     "
                f"{basis_label(nonzero_index, 2)}"
            )

    print("\nRule:")
    print("If control = 0, target remains unchanged.")
    print("If control = 1, X flips the target.")


def cx_basis_state_examples() -> None:
    print("\n" + "=" * 72)
    print("BEGINNER: APPLYING CX TO BASIS STATES")
    print("=" * 72)

    examples = ["00", "01", "10", "11"]

    for bits in examples:
        input_state = basis_state(bits)
        output_state = matrix_vector_multiply(CX_MATRIX, input_state)

        print_state(input_state, f"Input |{bits}>")
        print_state(output_state, "After CX")


# ---------------------------------------------------------------------------
# 7. CONTROLLED-Z AND CONTROLLED-PHASE
# ---------------------------------------------------------------------------

def controlled_z_example() -> None:
    print("\n" + "=" * 72)
    print("INTERMEDIATE: CONTROLLED-Z")
    print("=" * 72)

    print_matrix(CZ_MATRIX, "CZ matrix")

    for bits in ["00", "01", "10", "11"]:
        state = basis_state(bits)
        output = matrix_vector_multiply(CZ_MATRIX, state)
        print_state(output, f"CZ|{bits}>")


def controlled_phase_example() -> None:
    print("\n" + "=" * 72)
    print("INTERMEDIATE: CONTROLLED-PHASE")
    print("=" * 72)

    theta = math.pi / 2
    matrix = controlled_matrix(phase_gate(theta))

    print_matrix(
        matrix,
        "Controlled phase with theta = pi/2",
    )

    for bits in ["00", "01", "10", "11"]:
        state = basis_state(bits)
        output = matrix_vector_multiply(matrix, state)
        print_state(output, f"CP(pi/2)|{bits}>")


# ---------------------------------------------------------------------------
# 8. SUPERPOSITION AND ENTANGLEMENT
# ---------------------------------------------------------------------------

def bell_state_example() -> ComplexVector:
    """
    Prepare a Bell state:

        |00>
          --H(control)--
          --CX(control,target)--

    Result:
        (|00> + |11>) / sqrt(2)
    """
    print("\n" + "=" * 72)
    print("INTERMEDIATE: BELL STATE AND ENTANGLEMENT")
    print("=" * 72)

    state = basis_state("00")

    state = apply_single_qubit_matrix_to_two_qubits(
        state,
        HADAMARD,
        target_qubit=0,
    )

    print_state(state, "After H on qubit 0")

    state = apply_cx(
        state,
        control_qubit=0,
        target_qubit=1,
    )

    print_state(
        state,
        "After CX: (|00> + |11>)/sqrt(2)",
    )

    print("Measurement probabilities:", probabilities(state))

    return state


def bell_measurement_demo(
    state: ComplexVector,
    trials: int = 1000,
) -> None:
    """
    Sample the computational-basis measurement distribution.

    An ideal Bell state produces only 00 and 11, each approximately 50%.
    """
    if trials <= 0:
        raise ValueError("trials must be positive.")

    distribution = probabilities(state)
    counts = [0] * len(distribution)

    for _ in range(trials):
        random_value = random.random()
        cumulative = 0.0

        for index, probability in enumerate(distribution):
            cumulative += probability
            if random_value <= cumulative:
                counts[index] += 1
                break

    print(f"\nMeasurement results over {trials} trials:")
    for index, count in enumerate(counts):
        label = basis_label(index, 2)
        print(f"|{label}>: {count}")


# ---------------------------------------------------------------------------
# 9. GENERAL MULTI-QUBIT CONTROLLED OPERATIONS
# ---------------------------------------------------------------------------

def three_qubit_controlled_example() -> None:
    print("\n" + "=" * 72)
    print("ADVANCED: CONTROLLED OPERATION ON A THREE-QUBIT REGISTER")
    print("=" * 72)

    # |100> has control qubit 0 equal to 1 and target qubit 2 equal to 0.
    state = basis_state("100")

    print_state(state, "Initial state")

    state = apply_cx(
        state,
        control_qubit=0,
        target_qubit=2,
    )

    print_state(
        state,
        "After CX(control=0, target=2)",
    )

    # Here control qubit 0 is still 1 and target qubit 2 is now 1.
    state = apply_controlled_operation(
        state,
        control_qubit=0,
        target_qubit=2,
        target_operation=Z,
    )

    print_state(
        state,
        "After CZ(control=0, target=2)",
    )


def controlled_y_example() -> None:
    print("\n" + "=" * 72)
    print("ADVANCED: CONTROLLED-Y")
    print("=" * 72)

    matrix = controlled_matrix(Y)
    print_matrix(matrix, "Controlled-Y matrix")

    state = basis_state("11")
    output = matrix_vector_multiply(matrix, state)

    print_state(output, "CY|11>")


def general_controlled_unitary_example() -> None:
    print("\n" + "=" * 72)
    print("ADVANCED: GENERAL CONTROLLED UNITARY")
    print("=" * 72)

    theta = math.pi / 3
    rotation_like_phase = phase_gate(theta)

    controlled_operation = controlled_matrix(rotation_like_phase)

    print_matrix(
        controlled_operation,
        "Controlled phase operation",
    )

    state = basis_state("10")
    output = matrix_vector_multiply(
        controlled_operation,
        state,
    )

    print_state(
        output,
        "Controlled operation applied to |10>",
    )

    print(
        "Target amplitude receives phase e^(i*pi/3) because the control is 1."
    )


# ---------------------------------------------------------------------------
# 10. SWAP FROM THREE CNOT GATES
# ---------------------------------------------------------------------------

def swap_using_cx(
    state: ComplexVector,
    first_qubit: int,
    second_qubit: int,
) -> ComplexVector:
    """
    Implement SWAP using three CX gates:

        CX(a,b)
        CX(b,a)
        CX(a,b)

    This is a fundamental example of decomposing one operation into
    simpler controlled operations.
    """
    if first_qubit == second_qubit:
        raise ValueError("SWAP requires two distinct qubits.")

    state = apply_cx(state, first_qubit, second_qubit)
    state = apply_cx(state, second_qubit, first_qubit)
    state = apply_cx(state, first_qubit, second_qubit)

    return state


def swap_decomposition_example() -> None:
    print("\n" + "=" * 72)
    print("ADVANCED: SWAP DECOMPOSED INTO THREE CX GATES")
    print("=" * 72)

    for bits in ["00", "01", "10", "11"]:
        state = basis_state(bits)
        swapped = swap_using_cx(state, 0, 1)

        print_state(state, f"Input |{bits}>")
        print_state(swapped, "After SWAP")


# ---------------------------------------------------------------------------
# 11. TOFFOLI / CONTROLLED-CONTROLLED-X
# ---------------------------------------------------------------------------

def apply_toffoli(
    state: ComplexVector,
    first_control: int,
    second_control: int,
    target: int,
) -> ComplexVector:
    """
    Apply a Toffoli gate.

    X is applied to target only when BOTH controls are |1>.

    This is a controlled-controlled operation and illustrates how
    multi-control logic generalizes ordinary CX behavior.
    """
    number_of_qubits = int(math.log2(len(state)))

    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension must be a power of two.")

    qubits = [first_control, second_control, target]

    if len(set(qubits)) != 3:
        raise ValueError("Toffoli requires three distinct qubits.")

    if any(q < 0 or q >= number_of_qubits for q in qubits):
        raise IndexError("A qubit index is outside the register.")

    result = state.copy()

    first_mask = 1 << (number_of_qubits - 1 - first_control)
    second_mask = 1 << (number_of_qubits - 1 - second_control)
    target_mask = 1 << (number_of_qubits - 1 - target)

    for base_index in range(len(state)):
        if base_index & target_mask:
            continue

        if not (base_index & first_mask and base_index & second_mask):
            continue

        zero_index = base_index
        one_index = base_index | target_mask

        # Since X swaps the target amplitudes:
        result[zero_index] = state[one_index]
        result[one_index] = state[zero_index]

    return result


def toffoli_example() -> None:
    print("\n" + "=" * 72)
    print("ADVANCED: TOFFOLI GATE")
    print("=" * 72)

    for bits in ["000", "001", "010", "011", "100", "101", "110", "111"]:
        state = basis_state(bits)
        output = apply_toffoli(state, 0, 1, 2)

        print_state(state, f"Input |{bits}>")
        print_state(output, "After Toffoli")


# ---------------------------------------------------------------------------
# 12. QUANTUM CIRCUIT ABSTRACTION
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateOperation:
    """Describe one operation in a circuit."""

    name: str
    operation: Callable[[ComplexVector], ComplexVector]


class QuantumCircuit:
    """
    Minimal state-vector quantum circuit.

    This is intentionally small so that the controlled-gate mechanism remains
    visible instead of being hidden behind a framework.
    """

    def __init__(self, number_of_qubits: int) -> None:
        if number_of_qubits <= 0:
            raise ValueError("A circuit needs at least one qubit.")

        self.number_of_qubits = number_of_qubits
        self.state = basis_state("0" * number_of_qubits)
        self.operations: List[GateOperation] = []

    def add_single_qubit_gate(
        self,
        name: str,
        operation: ComplexMatrix,
        target: int,
    ) -> None:
        def action(
            current_state: ComplexVector,
            operation: ComplexMatrix = operation,
            target: int = target,
        ) -> ComplexVector:
            return apply_single_qubit_matrix_to_two_qubits(
                current_state,
                operation,
                target,
            )

        # The helper name refers to its general amplitude-pair mechanism;
        # it works for arbitrary n-qubit registers.
        self.operations.append(GateOperation(name, action))

    def add_controlled_gate(
        self,
        name: str,
        operation: ComplexMatrix,
        control: int,
        target: int,
    ) -> None:
        def action(
            current_state: ComplexVector,
            operation: ComplexMatrix = operation,
            control: int = control,
            target: int = target,
        ) -> ComplexVector:
            return apply_controlled_operation(
                current_state,
                control,
                target,
                operation,
            )

        self.operations.append(GateOperation(name, action))

    def run(self) -> ComplexVector:
        for gate in self.operations:
            self.state = gate.operation(self.state)

        return self.state

    def describe(self) -> None:
        print("\nCircuit operations:")
        for position, gate in enumerate(self.operations, start=1):
            print(f"{position}. {gate.name}")


def circuit_example() -> None:
    print("\n" + "=" * 72)
    print("ADVANCED: CIRCUIT ABSTRACTION")
    print("=" * 72)

    circuit = QuantumCircuit(2)

    circuit.add_single_qubit_gate(
        "H(q0)",
        HADAMARD,
        target=0,
    )

    circuit.add_controlled_gate(
        "CX(q0 -> q1)",
        X,
        control=0,
        target=1,
    )

    circuit.describe()

    final_state = circuit.run()

    print_state(
        final_state,
        "Circuit output",
    )


# ---------------------------------------------------------------------------
# 13. MEASUREMENT AND COLLAPSE
# ---------------------------------------------------------------------------

def measure_state(
    state: ComplexVector,
    rng: random.Random | None = None,
) -> Tuple[int, ComplexVector]:
    """
    Measure the complete computational basis state.

    Measurement chooses index i with probability |amplitude_i|^2 and then
    collapses the state to the corresponding basis state.
    """
    validate_normalized_state(state)

    if rng is None:
        rng = random.Random()

    random_value = rng.random()
    cumulative = 0.0

    for index, probability in enumerate(probabilities(state)):
        cumulative += probability

        if random_value <= cumulative:
            collapsed = [0.0 + 0.0j] * len(state)
            collapsed[index] = 1.0 + 0.0j
            return index, collapsed

    # Protect against tiny floating-point accumulation error.
    last_index = len(state) - 1
    collapsed = [0.0 + 0.0j] * len(state)
    collapsed[last_index] = 1.0 + 0.0j
    return last_index, collapsed


def measurement_collapse_example() -> None:
    print("\n" + "=" * 72)
    print("INTERMEDIATE: MEASUREMENT AND STATE COLLAPSE")
    print("=" * 72)

    state = basis_state("00")
    state = apply_single_qubit_matrix_to_two_qubits(
        state,
        HADAMARD,
        0,
    )
    state = apply_cx(state, 0, 1)

    print_state(state, "Before measurement")

    rng = random.Random(7)
    measured_index, collapsed = measure_state(state, rng)

    print(
        "Measured:",
        basis_label(measured_index, 2),
    )
    print_state(collapsed, "Collapsed state")


# ---------------------------------------------------------------------------
# 14. EDGE CASES AND VALIDATION
# ---------------------------------------------------------------------------

def edge_case_examples() -> None:
    print("\n" + "=" * 72)
    print("EDGE CASES AND VALIDATION")
    print("=" * 72)

    tests = [
        (
            "Control and target are identical",
            lambda: apply_cx(basis_state("00"), 0, 0),
        ),
        (
            "Control index outside register",
            lambda: apply_cx(basis_state("00"), 2, 1),
        ),
        (
            "Target index outside register",
            lambda: apply_cx(basis_state("00"), 0, 2),
        ),
        (
            "Invalid basis string",
            lambda: basis_state("012"),
        ),
        (
            "Zero-vector normalization",
            lambda: normalize_state([0j, 0j]),
        ),
    ]

    for description, action in tests:
        try:
            action()
        except (ValueError, IndexError) as error:
            print(f"{description}: correctly rejected -> {error}")


def invalid_state_example() -> None:
    print("\n" + "=" * 72)
    print("INVALID STATE NORMALIZATION CHECK")
    print("=" * 72)

    try:
        validate_normalized_state([1.0 + 0j, 1.0 + 0j])
    except ValueError as error:
        print("Validation caught the error:", error)

    normalized = normalize_state([1.0 + 0j, 1.0 + 0j])
    print_state(normalized, "Normalized vector")


# ---------------------------------------------------------------------------
# 15. UNITARITY CHECKS
# ---------------------------------------------------------------------------

def unitary_checks() -> None:
    print("\n" + "=" * 72)
    print("UNITARITY CHECKS")
    print("=" * 72)

    matrices = {
        "I": I,
        "X": X,
        "Y": Y,
        "Z": Z,
        "H": HADAMARD,
        "CX": CX_MATRIX,
        "CY": CY_MATRIX,
        "CZ": CZ_MATRIX,
    }

    for name, matrix in matrices.items():
        print(f"{name:>3}: unitary = {is_unitary(matrix)}")


# ---------------------------------------------------------------------------
# 16. CONTROLLED OPERATIONS AND PHASE
# ---------------------------------------------------------------------------

def phase_behavior_example() -> None:
    print("\n" + "=" * 72)
    print("PHASE BEHAVIOR")
    print("=" * 72)

    # Start with |10>. The control is 1.
    state = basis_state("10")

    phase = phase_gate(math.pi)

    result = apply_controlled_operation(
        state,
        control_qubit=0,
        target_qubit=1,
        target_operation=phase,
    )

    print_state(
        result,
        "Controlled phase applied to |10>",
    )

    print(
        "A global phase does not change measurement probabilities, "
        "but relative phase can affect later interference."
    )


def relative_phase_example() -> None:
    print("\n" + "=" * 72)
    print("RELATIVE PHASE AND INTERFERENCE")
    print("=" * 72)

    # Prepare |+> on the target while the control is definitely 1.
    state = basis_state("10")

    state = apply_single_qubit_matrix_to_two_qubits(
        state,
        HADAMARD,
        target_qubit=1,
    )

    print_state(state, "Control=1 and target=|+>")

    state = apply_controlled_operation(
        state,
        control_qubit=0,
        target_qubit=1,
        target_operation=Z,
    )

    print_state(
        state,
        "After CZ: target phase is changed",
    )

    state = apply_single_qubit_matrix_to_two_qubits(
        state,
        HADAMARD,
        target_qubit=1,
    )

    print_state(
        state,
        "Hadamard converts phase difference into computational-basis behavior",
    )

    print("Probabilities:", probabilities(state))


# ---------------------------------------------------------------------------
# 17. CONTROLLED OPERATION AS CONDITIONAL LOGIC
# ---------------------------------------------------------------------------

def classical_logic_view_example() -> None:
    print("\n" + "=" * 72)
    print("CLASSICAL LOGIC VIEW OF CX")
    print("=" * 72)

    print("For computational-basis inputs, CX behaves as:")
    print("output_control = control")
    print("output_target  = target XOR control")

    for control in [0, 1]:
        for target in [0, 1]:
            output_target = target ^ control
            print(
                f"control={control}, target={target} "
                f"-> control={control}, target={output_target}"
            )

    print(
        "\nQuantum CX extends this reversible XOR behavior to "
        "superpositions and entangled states."
    )


# ---------------------------------------------------------------------------
# 18. MATRIX VS DIRECT STATE-VECTOR IMPLEMENTATION
# ---------------------------------------------------------------------------

def implementation_comparison_example() -> None:
    print("\n" + "=" * 72)
    print("IMPLEMENTATION COMPARISON")
    print("=" * 72)

    state = basis_state("10")

    matrix_result = matrix_vector_multiply(
        CX_MATRIX,
        state,
    )

    direct_result = apply_cx(
        state,
        control_qubit=0,
        target_qubit=1,
    )

    print_state(matrix_result, "Matrix multiplication result")
    print_state(direct_result, "Direct state-vector result")

    equal = all(
        abs(left - right) < EPSILON
        for left, right in zip(matrix_result, direct_result)
    )

    print("Results agree:", equal)

    print(
        "\nFor n qubits, the full state vector has 2^n amplitudes. "
        "A full operator matrix has 2^n by 2^n entries, so constructing "
        "large matrices is usually much more expensive than applying "
        "a local gate directly to affected amplitudes."
    )


# ---------------------------------------------------------------------------
# 19. SIMPLE CIRCUIT IDENTITY CHECKS
# ---------------------------------------------------------------------------

def cx_self_inverse_example() -> None:
    print("\n" + "=" * 72)
    print("CX IS SELF-INVERSE")
    print("=" * 72)

    for bits in ["00", "01", "10", "11"]:
        state = basis_state(bits)
        once = apply_cx(state, 0, 1)
        twice = apply_cx(once, 0, 1)

        print(
            f"|{bits}> -> ",
            end="",
        )
        print_state(once)
        print("   -> ", end="")
        print_state(twice)

    print(
        "\nApplying CX twice returns the original state because X^2 = I."
    )


def controlled_z_phase_example() -> None:
    print("\n" + "=" * 72)
    print("CZ AS A DIAGONAL CONTROLLED OPERATION")
    print("=" * 72)

    print(
        "CZ changes the phase of |11> while leaving |00>, |01>, and |10> "
        "unchanged."
    )

    print_matrix(CZ_MATRIX)


# ---------------------------------------------------------------------------
# 20. SIMPLE TWO-QUBIT STATE ANALYSIS
# ---------------------------------------------------------------------------

def analyze_two_qubit_state(state: ComplexVector) -> None:
    """
    Print probabilities and identify the basis states carrying probability.
    """
    validate_normalized_state(state)

    print("\nTwo-qubit state analysis:")

    for index, probability in enumerate(probabilities(state)):
        if probability > EPSILON:
            label = basis_label(index, 2)
            amplitude = state[index]
            print(
                f"|{label}>: amplitude={format_complex(amplitude)}, "
                f"probability={probability:.6f}"
            )


def bell_state_analysis_example() -> None:
    print("\n" + "=" * 72)
    print("BELL STATE ANALYSIS")
    print("=" * 72)

    state = bell_state_example()
    analyze_two_qubit_state(state)


# ---------------------------------------------------------------------------
# 21. ADVANCED: CONTROLLED OPERATION ON SUPERPOSITION
# ---------------------------------------------------------------------------

def controlled_superposition_example() -> None:
    print("\n" + "=" * 72)
    print("CONTROLLED OPERATION ON SUPERPOSITION")
    print("=" * 72)

    # Start in |00>.
    state = basis_state("00")

    # Create (|00> + |10>) / sqrt(2), where the control is in superposition.
    state = apply_single_qubit_matrix_to_two_qubits(
        state,
        HADAMARD,
        target_qubit=0,
    )

    print_state(
        state,
        "Before CX",
    )

    # The |00> branch remains |00>.
    # The |10> branch becomes |11>.
    state = apply_cx(
        state,
        control_qubit=0,
        target_qubit=1,
    )

    print_state(
        state,
        "After CX",
    )

    print(
        "This conditional transformation creates correlations between "
        "the control and target."
    )


# ---------------------------------------------------------------------------
# 22. ADVANCED: CONTROLLED UNITARY VERIFICATION
# ---------------------------------------------------------------------------

def controlled_unitary_verification() -> None:
    print("\n" + "=" * 72)
    print("CONTROLLED-UNITARY VERIFICATION")
    print("=" * 72)

    theta = 0.73
    U = phase_gate(theta)
    controlled_U = controlled_matrix(U)

    print("U is unitary:", is_unitary(U))
    print("Controlled-U is unitary:", is_unitary(controlled_U))

    print(
        "\nIf U is unitary, controlled-U is also unitary. "
        "The control determines whether U or I acts on the target."
    )


# ---------------------------------------------------------------------------
# 23. PERFORMANCE DEMONSTRATION
# ---------------------------------------------------------------------------

def performance_scaling_explanation() -> None:
    print("\n" + "=" * 72)
    print("PERFORMANCE AND SCALING")
    print("=" * 72)

    print("Number of qubits -> state-vector amplitudes")

    for number_of_qubits in range(1, 11):
        amplitudes = 2 ** number_of_qubits
        print(
            f"{number_of_qubits:>2} qubits -> "
            f"{amplitudes:>4} complex amplitudes"
        )

    print(
        "\nA state-vector simulator requires memory proportional to O(2^n)."
    )
    print(
        "A direct controlled-gate application can process O(2^n) "
        "amplitudes without explicitly storing a 2^n x 2^n matrix."
    )

    print(
        "The exponential state-space size is a fundamental simulation "
        "challenge, not merely a Python implementation detail."
    )


# ---------------------------------------------------------------------------
# 24. SECURITY AND CORRECTNESS CONSIDERATIONS
# ---------------------------------------------------------------------------

def correctness_considerations() -> None:
    print("\n" + "=" * 72)
    print("CORRECTNESS CONSIDERATIONS")
    print("=" * 72)

    print("1. Always preserve normalization.")
    print("2. Validate control and target indices.")
    print("3. Never allow control == target for a standard two-qubit CX.")
    print("4. Preserve complex amplitudes, including phase.")
    print("5. Avoid treating amplitudes as probabilities.")
    print("6. Use tolerances when comparing floating-point values.")
    print("7. Verify unitary operations when implementing custom gates.")
    print("8. Distinguish global phase from relative phase.")
    print("9. Test computational-basis cases before testing superpositions.")
    print("10. Test inverse/self-inverse circuit identities.")


# ---------------------------------------------------------------------------
# 25. COMMON MISTAKES
# ---------------------------------------------------------------------------

def common_mistakes_example() -> None:
    print("\n" + "=" * 72)
    print("COMMON MISTAKES")
    print("=" * 72)

    mistakes = [
        (
            "Mistake: thinking CX always flips the target.",
            "Correction: CX flips the target only when its control is |1>."
        ),
        (
            "Mistake: treating an amplitude as a probability.",
            "Correction: probability is |amplitude|^2."
        ),
        (
            "Mistake: ignoring complex phase.",
            "Correction: phase affects interference and later measurements."
        ),
        (
            "Mistake: confusing CX with CZ.",
            "Correction: CX changes the computational value of the target; "
            "CZ applies a phase of -1 to |11>."
        ),
        (
            "Mistake: using control and target interchangeably.",
            "Correction: controlled gates are directional unless a circuit "
            "identity explicitly transforms them."
        ),
        (
            "Mistake: assuming entanglement is merely classical correlation.",
            "Correction: entangled quantum states can exhibit correlations "
            "that cannot be represented as independent local states."
        ),
    ]

    for mistake, correction in mistakes:
        print("\n" + mistake)
        print(correction)


# ---------------------------------------------------------------------------
# 26. FULL DEMONSTRATION
# ---------------------------------------------------------------------------

def run_all_examples() -> None:
    beginner_single_qubit_example()
    cx_truth_table_example()
    cx_basis_state_examples()
    controlled_z_example()
    controlled_phase_example()

    bell_state = bell_state_example()
    bell_measurement_demo(bell_state, trials=1000)

    three_qubit_controlled_example()
    controlled_y_example()
    general_controlled_unitary_example()

    swap_decomposition_example()
    toffoli_example()
    circuit_example()

    measurement_collapse_example()
    edge_case_examples()
    invalid_state_example()

    unitary_checks()
    phase_behavior_example()
    relative_phase_example()
    classical_logic_view_example()

    implementation_comparison_example()
    cx_self_inverse_example()
    controlled_z_phase_example()

    bell_state_analysis_example()
    controlled_superposition_example()
    controlled_unitary_verification()

    performance_scaling_explanation()
    correctness_considerations()
    common_mistakes_example()


# ---------------------------------------------------------------------------
# 27. PROGRAM ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 72)
    print("CONTROLLED GATES STUDY PROGRAM")
    print("Controlled-X (CX/CNOT) and Controlled Quantum Operations")
    print("=" * 72)

    random.seed(42)

    run_all_examples()

    print("\n" + "=" * 72)
    print("END OF CONTROLLED-GATE STUDY PROGRAM")
    print("=" * 72)
