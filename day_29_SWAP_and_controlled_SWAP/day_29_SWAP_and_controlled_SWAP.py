"""
SWAP and Controlled-SWAP (Fredkin) Gates
=========================================

A self-contained study and executable demonstration of multi-qubit SWAP and
controlled-SWAP operations.

The script begins with computational-basis states and classical intuition,
then develops tensor-product state vectors, unitary gate application,
SWAP, controlled-SWAP/Fredkin, superposition, entanglement, measurement,
verification, circuit simulation, complexity, and practical considerations.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt
from random import random
from typing import Iterable, Sequence


EPSILON = 1e-10


# ---------------------------------------------------------------------------
# 1. Complex-number and state-vector fundamentals
# ---------------------------------------------------------------------------

Complex = complex
StateVector = list[Complex]


def format_complex(value: complex, precision: int = 3) -> str:
    """Return a compact human-readable complex number."""
    real = 0.0 if abs(value.real) < 0.5 * 10 ** (-precision) else value.real
    imag = 0.0 if abs(value.imag) < 0.5 * 10 ** (-precision) else value.imag

    if imag == 0:
        return f"{real:.{precision}f}"
    if real == 0:
        return f"{imag:.{precision}f}i"
    sign = "+" if imag >= 0 else "-"
    return f"{real:.{precision}f}{sign}{abs(imag):.{precision}f}i"


def basis_label(index: int, qubit_count: int) -> str:
    """Convert an integer basis index to a fixed-width computational basis label."""
    return format(index, f"0{qubit_count}b")


def state_norm(state: Sequence[complex]) -> float:
    """Compute the Euclidean norm of a quantum state vector."""
    return sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def normalize(state: Sequence[complex]) -> StateVector:
    """Normalize a nonzero state vector."""
    norm = state_norm(state)
    if norm <= EPSILON:
        raise ValueError("A zero vector cannot represent a quantum state.")
    return [amplitude / norm for amplitude in state]


def validate_state(state: Sequence[complex], qubit_count: int) -> None:
    """Validate dimension and normalization."""
    expected_dimension = 2 ** qubit_count
    if len(state) != expected_dimension:
        raise ValueError(
            f"{qubit_count} qubits require {expected_dimension} amplitudes; "
            f"received {len(state)}."
        )

    norm = state_norm(state)
    if not isclose(norm, 1.0, abs_tol=EPSILON):
        raise ValueError(f"State is not normalized. Norm = {norm}")


def basis_state(bits: str) -> StateVector:
    """
    Construct a computational-basis state.

    The leftmost character is treated as the highest-order qubit.
    For example, |101> corresponds to vector index 5.
    """
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("A basis state must be a non-empty binary string.")

    vector = [0j] * (2 ** len(bits))
    vector[int(bits, 2)] = 1 + 0j
    return vector


def uniform_superposition(qubit_count: int) -> StateVector:
    """Create |+>^n = equal superposition of all computational basis states."""
    dimension = 2 ** qubit_count
    amplitude = 1 / sqrt(dimension)
    return [complex(amplitude, 0) for _ in range(dimension)]


def print_state(
    state: Sequence[complex],
    qubit_count: int,
    title: str = "State",
    threshold: float = 1e-9,
) -> None:
    """Print only amplitudes that are materially nonzero."""
    print(f"\n{title}")
    validate_state(state, qubit_count)

    terms = []
    for index, amplitude in enumerate(state):
        if abs(amplitude) > threshold:
            label = basis_label(index, qubit_count)
            terms.append(f"({format_complex(amplitude)})|{label}>")

    print(" + ".join(terms) if terms else "0")


# ---------------------------------------------------------------------------
# 2. General multi-qubit gate machinery
# ---------------------------------------------------------------------------

def apply_permutation(
    state: Sequence[complex],
    qubit_count: int,
    mapping,
) -> StateVector:
    """
    Apply a computational-basis permutation.

    mapping(index) returns the destination basis index for each source index.
    This is particularly convenient for SWAP-like gates because these gates
    merely permute computational-basis states and do not alter amplitudes.
    """
    validate_state(state, qubit_count)

    result = [0j] * len(state)

    for source_index, amplitude in enumerate(state):
        destination_index = mapping(source_index)
        if not 0 <= destination_index < len(state):
            raise ValueError("Gate mapping produced an invalid basis index.")
        result[destination_index] += amplitude

    return result


def replace_bit(index: int, qubit_count: int, qubit: int, value: int) -> int:
    """
    Replace one qubit in a basis index.

    Qubit numbering is 0-based from the leftmost displayed bit.
    Thus, for |q0 q1 q2>, q0 is the most significant bit.
    """
    if not 0 <= qubit < qubit_count:
        raise IndexError("Qubit index is outside the circuit.")
    if value not in (0, 1):
        raise ValueError("A qubit value must be 0 or 1.")

    shift = qubit_count - 1 - qubit
    mask = 1 << shift
    return (index | mask) if value else (index & ~mask)


def get_bit(index: int, qubit_count: int, qubit: int) -> int:
    """Read a qubit from a computational-basis index."""
    if not 0 <= qubit < qubit_count:
        raise IndexError("Qubit index is outside the circuit.")

    shift = qubit_count - 1 - qubit
    return (index >> shift) & 1


def swap_basis_index(
    index: int,
    qubit_count: int,
    first: int,
    second: int,
) -> int:
    """Return the basis index obtained by exchanging two qubits."""
    if first == second:
        return index

    a = get_bit(index, qubit_count, first)
    b = get_bit(index, qubit_count, second)

    if a == b:
        return index

    index = replace_bit(index, qubit_count, first, b)
    index = replace_bit(index, qubit_count, second, a)
    return index


# ---------------------------------------------------------------------------
# 3. SWAP gate
# ---------------------------------------------------------------------------

def swap_gate(
    state: Sequence[complex],
    qubit_count: int,
    first: int,
    second: int,
) -> StateVector:
    """
    Apply the two-qubit SWAP operation.

    Matrix representation on two qubits, in the basis
    |00>, |01>, |10>, |11>:

        [1 0 0 0]
        [0 0 1 0]
        [0 1 0 0]
        [0 0 0 1]

    Therefore:
        |00> -> |00>
        |01> -> |10>
        |10> -> |01>
        |11> -> |11>
    """
    if not 0 <= first < qubit_count or not 0 <= second < qubit_count:
        raise IndexError("SWAP qubit index is outside the circuit.")

    return apply_permutation(
        state,
        qubit_count,
        lambda index: swap_basis_index(
            index, qubit_count, first, second
        ),
    )


def demonstrate_swap_truth_table() -> None:
    """Show the complete computational-basis behavior of SWAP."""
    print("\n" + "=" * 72)
    print("SWAP GATE: COMPUTATIONAL-BASIS TRUTH TABLE")
    print("=" * 72)

    for bits in ("00", "01", "10", "11"):
        state = basis_state(bits)
        result = swap_gate(state, 2, 0, 1)

        destination = next(
            basis_label(i, 2)
            for i, amplitude in enumerate(result)
            if abs(amplitude) > EPSILON
        )

        print(f"|{bits}>  ->  |{destination}>")


# ---------------------------------------------------------------------------
# 4. Controlled-SWAP / Fredkin gate
# ---------------------------------------------------------------------------

def controlled_swap_gate(
    state: Sequence[complex],
    qubit_count: int,
    control: int,
    first: int,
    second: int,
) -> StateVector:
    """
    Apply a controlled-SWAP (Fredkin) gate.

    The control qubit is unchanged.

    If control = 0:
        target qubits are unchanged.

    If control = 1:
        target qubits are exchanged.

    The control and target qubits must be distinct.
    """
    if len({control, first, second}) != 3:
        raise ValueError(
            "Controlled-SWAP requires three distinct qubits: "
            "one control and two targets."
        )

    if any(not 0 <= q < qubit_count for q in (control, first, second)):
        raise IndexError("Controlled-SWAP qubit index is outside the circuit.")

    def mapping(index: int) -> int:
        if get_bit(index, qubit_count, control) == 1:
            return swap_basis_index(index, qubit_count, first, second)
        return index

    return apply_permutation(state, qubit_count, mapping)


def demonstrate_fredkin_truth_table() -> None:
    """Show the eight basis-state mappings of a three-qubit Fredkin gate."""
    print("\n" + "=" * 72)
    print("CONTROLLED-SWAP / FREDKIN GATE: TRUTH TABLE")
    print("=" * 72)

    for bits in ("000", "001", "010", "011", "100", "101", "110", "111"):
        result = controlled_swap_gate(basis_state(bits), 3, 0, 1, 2)

        destination = next(
            basis_label(i, 3)
            for i, amplitude in enumerate(result)
            if abs(amplitude) > EPSILON
        )

        print(f"|{bits}>  ->  |{destination}>")


# ---------------------------------------------------------------------------
# 5. Linearity and superposition
# ---------------------------------------------------------------------------

def demonstrate_linearity() -> None:
    """
    Demonstrate that quantum gates act linearly on amplitudes.

    A gate does not need a separate rule for every superposition. Its action
    on basis states determines its action on arbitrary linear combinations.
    """
    print("\n" + "=" * 72)
    print("LINEARITY OF SWAP")
    print("=" * 72)

    # State: (|01> + i|10>) / sqrt(2)
    state = [
        0j,
        1 / sqrt(2),
        1j / sqrt(2),
        0j,
    ]

    print_state(state, 2, "Input superposition")
    result = swap_gate(state, 2, 0, 1)
    print_state(result, 2, "After SWAP")

    # Applying SWAP twice must return the original state.
    round_trip = swap_gate(result, 2, 0, 1)

    print(
        "Applying SWAP twice returns the original state:",
        states_close(state, round_trip),
    )


# ---------------------------------------------------------------------------
# 6. Measurement and probability
# ---------------------------------------------------------------------------

def probabilities(state: Sequence[complex]) -> list[float]:
    """Return computational-basis measurement probabilities."""
    return [abs(amplitude) ** 2 for amplitude in state]


def measure_distribution(
    state: Sequence[complex],
    qubit_count: int,
) -> dict[str, float]:
    """Return basis-state probabilities as a readable dictionary."""
    validate_state(state, qubit_count)
    return {
        basis_label(index, qubit_count): probability
        for index, probability in enumerate(probabilities(state))
        if probability > EPSILON
    }


def sample_measurement(
    state: Sequence[complex],
    qubit_count: int,
) -> str:
    """Perform one computational-basis measurement using inverse CDF sampling."""
    validate_state(state, qubit_count)

    threshold = random()
    cumulative = 0.0

    for index, probability in enumerate(probabilities(state)):
        cumulative += probability
        if threshold <= cumulative:
            return basis_label(index, qubit_count)

    # Floating-point rounding can leave a tiny residual.
    return basis_label(len(state) - 1, qubit_count)


def demonstrate_measurement() -> None:
    """Show that SWAP changes labels but preserves the probability multiset."""
    print("\n" + "=" * 72)
    print("MEASUREMENT PROBABILITIES")
    print("=" * 72)

    state = normalize(
        [
            1 + 0j,
            1 + 1j,
            2 + 0j,
            0.5j,
        ]
    )

    result = swap_gate(state, 2, 0, 1)

    print("Input probabilities:")
    for label, probability in measure_distribution(state, 2).items():
        print(f"  |{label}>: {probability:.4f}")

    print("After SWAP:")
    for label, probability in measure_distribution(result, 2).items():
        print(f"  |{label}>: {probability:.4f}")

    print(
        "Norm before:",
        f"{state_norm(state):.12f}",
        "| Norm after:",
        f"{state_norm(result):.12f}",
    )


# ---------------------------------------------------------------------------
# 7. Entanglement-related example
# ---------------------------------------------------------------------------

def bell_state_phi_plus() -> StateVector:
    """Create the Bell state (|00> + |11>) / sqrt(2)."""
    amplitude = 1 / sqrt(2)
    return [complex(amplitude), 0j, 0j, complex(amplitude)]


def demonstrate_entangled_swap() -> None:
    """
    SWAP on an already symmetric Bell state leaves it unchanged.

    This does not mean SWAP is the identity operation. It means this
    particular state is an eigenstate of SWAP with eigenvalue +1.
    """
    print("\n" + "=" * 72)
    print("SWAP AND AN ENTANGLED STATE")
    print("=" * 72)

    bell = bell_state_phi_plus()
    swapped = swap_gate(bell, 2, 0, 1)

    print_state(bell, 2, "Bell state |Phi+>")
    print_state(swapped, 2, "After SWAP")
    print("State unchanged:", states_close(bell, swapped))

    # The antisymmetric singlet state acquires a phase of -1 under SWAP.
    singlet = [
        0j,
        1 / sqrt(2),
        -1 / sqrt(2),
        0j,
    ]
    swapped_singlet = swap_gate(singlet, 2, 0, 1)

    print_state(singlet, 2, "Singlet state")
    print_state(swapped_singlet, 2, "Singlet after SWAP")

    phase_relation = all(
        isclose(
            swapped_singlet[i],
            -singlet[i],
            abs_tol=EPSILON,
        )
        for i in range(4)
    )
    print("SWAP changes the singlet by a global phase of -1:", phase_relation)


# ---------------------------------------------------------------------------
# 8. Controlled-SWAP and coherent control
# ---------------------------------------------------------------------------

def demonstrate_controlled_swap_superposition() -> None:
    """
    Demonstrate coherent conditional behavior.

    Input:
        (|0>|01> + |1>|01>) / sqrt(2)

    Fredkin produces:
        (|0>|01> + |1>|10>) / sqrt(2)

    The control is not measured. The operation is coherent.
    """
    print("\n" + "=" * 72)
    print("CONTROLLED-SWAP WITH A SUPERPOSED CONTROL")
    print("=" * 72)

    # Qubit order is control, target-1, target-2.
    state = [0j] * 8
    state[int("001", 2)] = 1 / sqrt(2)
    state[int("101", 2)] = 1 / sqrt(2)

    print_state(state, 3, "Input")
    result = controlled_swap_gate(state, 3, 0, 1, 2)
    print_state(result, 3, "After Fredkin")

    expected = [0j] * 8
    expected[int("001", 2)] = 1 / sqrt(2)
    expected[int("110", 2)] = 1 / sqrt(2)

    print("Matches expected coherent transformation:", states_close(result, expected))


# ---------------------------------------------------------------------------
# 9. Gate properties
# ---------------------------------------------------------------------------

def states_close(
    first: Sequence[complex],
    second: Sequence[complex],
    tolerance: float = EPSILON,
) -> bool:
    """Compare two state vectors element by element."""
    if len(first) != len(second):
        return False

    return all(
        isclose(a.real, b.real, abs_tol=tolerance)
        and isclose(a.imag, b.imag, abs_tol=tolerance)
        for a, b in zip(first, second)
    )


def global_phase_equivalent(
    first: Sequence[complex],
    second: Sequence[complex],
) -> bool:
    """
    Determine whether two states differ only by a global phase.

    Global phase does not change measurement probabilities, although relative
    phase between components does affect interference.
    """
    if len(first) != len(second):
        return False

    reference = None

    for a, b in zip(first, second):
        if abs(a) > EPSILON and abs(b) > EPSILON:
            reference = b / a
            break
        if abs(a) > EPSILON or abs(b) > EPSILON:
            return False

    if reference is None:
        return True

    if not isclose(abs(reference), 1.0, abs_tol=EPSILON):
        return False

    return all(
        isclose(
            first[i] * reference,
            second[i],
            abs_tol=EPSILON,
        )
        for i in range(len(first))
    )


def demonstrate_gate_properties() -> None:
    """Verify important algebraic properties."""
    print("\n" + "=" * 72)
    print("GATE PROPERTIES")
    print("=" * 72)

    state = normalize(
        [
            1 + 0j,
            1j,
            2 + 1j,
            -1 + 0j,
            0.5j,
            1 + 2j,
            0.25 + 0j,
            -0.75j,
        ]
    )

    # SWAP is self-inverse.
    after_one = swap_gate(state, 3, 0, 2)
    after_two = swap_gate(after_one, 3, 0, 2)

    print("SWAP^2 = I:", states_close(state, after_two))

    # Fredkin is also self-inverse.
    fredkin_once = controlled_swap_gate(state, 3, 0, 1, 2)
    fredkin_twice = controlled_swap_gate(fredkin_once, 3, 0, 1, 2)

    print("Fredkin^2 = I:", states_close(state, fredkin_twice))

    # Both operations are permutations, so normalization is preserved.
    print("Initial norm:", f"{state_norm(state):.12f}")
    print("SWAP norm:", f"{state_norm(after_one):.12f}")
    print("Fredkin norm:", f"{state_norm(fredkin_once):.12f}")


# ---------------------------------------------------------------------------
# 10. Circuit abstraction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Operation:
    """A simple immutable circuit operation description."""

    name: str
    qubits: tuple[int, ...]


class QuantumCircuit:
    """
    Small educational state-vector simulator.

    It intentionally supports only SWAP and controlled-SWAP because the
    purpose is to make multi-qubit permutation behavior explicit.
    """

    def __init__(self, qubit_count: int):
        if qubit_count <= 0:
            raise ValueError("A circuit must contain at least one qubit.")

        self.qubit_count = qubit_count
        self.operations: list[Operation] = []

    def add_swap(self, first: int, second: int) -> None:
        self._validate_qubits((first, second))
        self.operations.append(Operation("SWAP", (first, second)))

    def add_controlled_swap(
        self,
        control: int,
        first: int,
        second: int,
    ) -> None:
        self._validate_qubits((control, first, second))
        if len({control, first, second}) != 3:
            raise ValueError("Fredkin qubits must be distinct.")

        self.operations.append(
            Operation("CSWAP", (control, first, second))
        )

    def _validate_qubits(self, qubits: Iterable[int]) -> None:
        for qubit in qubits:
            if not 0 <= qubit < self.qubit_count:
                raise IndexError(
                    f"Qubit {qubit} is outside a "
                    f"{self.qubit_count}-qubit circuit."
                )

    def run(self, initial_state: Sequence[complex]) -> StateVector:
        """Execute every operation in sequence."""
        state = normalize(initial_state)

        for operation in self.operations:
            if operation.name == "SWAP":
                state = swap_gate(
                    state,
                    self.qubit_count,
                    operation.qubits[0],
                    operation.qubits[1],
                )
            elif operation.name == "CSWAP":
                state = controlled_swap_gate(
                    state,
                    self.qubit_count,
                    operation.qubits[0],
                    operation.qubits[1],
                    operation.qubits[2],
                )
            else:
                raise RuntimeError(f"Unknown operation: {operation.name}")

        return state

    def describe(self) -> None:
        """Print the circuit as an operation list."""
        print("\nCircuit:")
        for number, operation in enumerate(self.operations, start=1):
            qubits = ", ".join(str(q) for q in operation.qubits)
            print(f"  {number}. {operation.name}({qubits})")


def demonstrate_circuit() -> None:
    """Run a multi-operation circuit."""
    print("\n" + "=" * 72)
    print("MULTI-OPERATION CIRCUIT")
    print("=" * 72)

    circuit = QuantumCircuit(4)
    circuit.add_swap(0, 3)
    circuit.add_controlled_swap(1, 2, 3)
    circuit.add_swap(0, 2)
    circuit.describe()

    initial = normalize(
        [
            1 + 0j,
            0.5 + 0j,
            0.25j,
            1 + 1j,
            0.5j,
            -0.75 + 0j,
            0.25 + 0.5j,
            0j,
            1j,
            0.1 + 0j,
            -0.3j,
            0.4 + 0.1j,
            0.2 + 0j,
            -0.2j,
            0.3 + 0j,
            0.5j,
        ]
    )

    print_state(initial, 4, "Initial state")
    final = circuit.run(initial)
    print_state(final, 4, "Final state")


# ---------------------------------------------------------------------------
# 11. Decomposition of SWAP into three CNOT gates
# ---------------------------------------------------------------------------

def cnot_gate(
    state: Sequence[complex],
    qubit_count: int,
    control: int,
    target: int,
) -> StateVector:
    """
    Educational CNOT implementation.

    CNOT flips the target only when the control is |1>.
    """
    if control == target:
        raise ValueError("CNOT control and target must differ.")

    def mapping(index: int) -> int:
        if get_bit(index, qubit_count, control) == 1:
            target_value = get_bit(index, qubit_count, target)
            return replace_bit(
                index,
                qubit_count,
                target,
                1 - target_value,
            )
        return index

    return apply_permutation(state, qubit_count, mapping)


def swap_via_three_cnots(
    state: Sequence[complex],
    qubit_count: int,
    first: int,
    second: int,
) -> StateVector:
    """
    Implement SWAP using the identity:

        CNOT(a,b)
        CNOT(b,a)
        CNOT(a,b)
    """
    result = cnot_gate(state, qubit_count, first, second)
    result = cnot_gate(result, qubit_count, second, first)
    result = cnot_gate(result, qubit_count, first, second)
    return result


def demonstrate_swap_decomposition() -> None:
    """Verify the standard three-CNOT SWAP decomposition."""
    print("\n" + "=" * 72)
    print("SWAP DECOMPOSITION")
    print("=" * 72)

    state = normalize(
        [
            1 + 0j,
            2j,
            1 - 1j,
            0.5 + 0j,
        ]
    )

    direct = swap_gate(state, 2, 0, 1)
    decomposed = swap_via_three_cnots(state, 2, 0, 1)

    print_state(direct, 2, "Direct SWAP")
    print_state(decomposed, 2, "Three-CNOT implementation")
    print(
        "Implementations agree:",
        states_close(direct, decomposed),
    )


# ---------------------------------------------------------------------------
# 12. Validation and edge cases
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    """Demonstrate expected behavior for important boundary conditions."""
    print("\n" + "=" * 72)
    print("EDGE CASES AND VALIDATION")
    print("=" * 72)

    # SWAP of a qubit with itself is mathematically the identity.
    state = basis_state("101")
    same_qubit = swap_gate(state, 3, 1, 1)
    print(
        "SWAP(q, q) behaves as identity:",
        states_close(state, same_qubit),
    )

    # Invalid Fredkin topology.
    try:
        controlled_swap_gate(state, 3, 0, 0, 2)
    except ValueError as error:
        print("Rejected invalid Fredkin gate:", error)

    # Invalid normalization.
    try:
        validate_state([1 + 0j, 1 + 0j], 1)
    except ValueError as error:
        print("Rejected unnormalized state:", error)

    # Invalid qubit index.
    try:
        swap_gate(state, 3, 0, 3)
    except IndexError as error:
        print("Rejected invalid qubit index:", error)


# ---------------------------------------------------------------------------
# 13. Conceptual comparison
# ---------------------------------------------------------------------------

def print_comparison() -> None:
    """Print the key distinction between SWAP and controlled-SWAP."""
    print("\n" + "=" * 72)
    print("SWAP VS CONTROLLED-SWAP")
    print("=" * 72)

    comparison = [
        ("Qubits involved", "2", "3"),
        ("Control qubit", "None", "1"),
        ("Condition", "Always exchanges targets", "Exchange only if control=1"),
        ("Self-inverse", "Yes", "Yes"),
        ("Reversible", "Yes", "Yes"),
        ("Basis action", "Permutation", "Conditional permutation"),
        ("Typical role", "Move/exchange quantum states", "Conditional routing"),
    ]

    print(f"{'Property':<22} {'SWAP':<34} {'Controlled-SWAP':<34}")
    print("-" * 92)

    for property_name, swap_value, controlled_value in comparison:
        print(
            f"{property_name:<22} "
            f"{swap_value:<34} "
            f"{controlled_value:<34}"
        )


# ---------------------------------------------------------------------------
# 14. Educational checklist
# ---------------------------------------------------------------------------

def print_study_checklist() -> None:
    """Display the major concepts demonstrated by this file."""
    print("\n" + "=" * 72)
    print("STUDY CHECKLIST")
    print("=" * 72)

    concepts = [
        "Computational-basis states",
        "Qubit indexing",
        "State-vector normalization",
        "Complex probability amplitudes",
        "Measurement probabilities",
        "Multi-qubit state dimension",
        "SWAP gate mapping",
        "Controlled-SWAP / Fredkin mapping",
        "Superposition and linearity",
        "Entangled states",
        "Global phase",
        "Self-inverse gates",
        "State-vector simulation",
        "Circuit composition",
        "SWAP decomposition into CNOT gates",
        "Input validation and edge cases",
        "Permutation-based simulation",
        "Time and memory considerations",
        "Reversibility and unitary behavior",
    ]

    for number, concept in enumerate(concepts, start=1):
        print(f"{number:2}. {concept}")


# ---------------------------------------------------------------------------
# 15. Main demonstration
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("SWAP & CONTROLLED-SWAP: MULTI-QUBIT OPERATIONS")
    print("=" * 72)
    print(
        "\nThe simulator uses exact computational-basis permutations. "
        "For educational clarity, qubits are numbered from the left."
    )

    demonstrate_swap_truth_table()
    demonstrate_fredkin_truth_table()
    demonstrate_linearity()
    demonstrate_measurement()
    demonstrate_entangled_swap()
    demonstrate_controlled_swap_superposition()
    demonstrate_gate_properties()
    demonstrate_circuit()
    demonstrate_swap_decomposition()
    demonstrate_edge_cases()
    print_comparison()
    print_study_checklist()

    print("\n" + "=" * 72)
    print("PERFORMANCE NOTE")
    print("=" * 72)
    print(
        "A state-vector simulator stores 2^n amplitudes for n qubits. "
        "Memory therefore grows exponentially with qubit count."
    )
    print(
        "For SWAP and controlled-SWAP, each basis amplitude is moved once, "
        "so a direct state-vector permutation takes O(2^n) time and O(2^n) "
        "state storage."
    )
    print(
        "Real quantum hardware applies physical gate operations without "
        "classically storing all 2^n amplitudes."
    )


if __name__ == "__main__":
    main()
