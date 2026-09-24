"""
Hadamard Gate: Creating Superposition
=====================================

A self-contained study program for understanding the Hadamard (H) gate,
single-qubit superposition, measurement probabilities, phase, interference,
multi-qubit states, entanglement, and practical simulation.

No external packages are required.

The computational basis is:
    |0> = [1, 0]
    |1> = [0, 1]

The Hadamard matrix is:

                 1     1
    H = 1/sqrt(2) [       ]
                1    -1

Therefore:
    H|0> = (|0> + |1>) / sqrt(2)
    H|1> = (|0> - |1>) / sqrt(2)

Important distinction:
A qubit in superposition is not simply "randomly 0 or 1".
Its state contains amplitudes, and measurement probabilities are obtained
from the squared magnitudes of those amplitudes.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


EPSILON = 1e-12
SQRT_TWO = math.sqrt(2.0)
H_SCALE = 1.0 / SQRT_TWO


def section(title: str) -> None:
    """Print a consistent study-section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def format_complex(value: complex, digits: int = 4) -> str:
    """Format a complex number compactly for educational output."""
    real = round(value.real, digits)
    imaginary = round(value.imag, digits)

    if abs(real) < 10 ** (-digits):
        real = 0.0
    if abs(imaginary) < 10 ** (-digits):
        imaginary = 0.0

    if imaginary == 0:
        return f"{real:g}"
    if real == 0:
        return f"{imaginary:g}i"
    sign = "+" if imaginary >= 0 else "-"
    return f"{real:g} {sign} {abs(imaginary):g}i"


def probability_from_amplitude(amplitude: complex) -> float:
    """
    Born rule:
        P(outcome) = |amplitude|^2

    For a normalized quantum state, probabilities sum to one.
    """
    return abs(amplitude) ** 2


@dataclass
class Qubit:
    """
    A single qubit represented by two complex probability amplitudes.

    alpha corresponds to |0>.
    beta corresponds to |1>.

    State:
        |psi> = alpha|0> + beta|1>

    Normalization requires:
        |alpha|^2 + |beta|^2 = 1
    """

    alpha: complex = 1.0 + 0.0j
    beta: complex = 0.0 + 0.0j

    def __post_init__(self) -> None:
        self.alpha = complex(self.alpha)
        self.beta = complex(self.beta)
        self.validate()

    def norm_squared(self) -> float:
        return probability_from_amplitude(self.alpha) + probability_from_amplitude(
            self.beta
        )

    def norm(self) -> float:
        return math.sqrt(self.norm_squared())

    def validate(self) -> None:
        if not math.isclose(self.norm_squared(), 1.0, abs_tol=EPSILON):
            raise ValueError(
                "A physical qubit state must be normalized: "
                "|alpha|^2 + |beta|^2 = 1."
            )

    def probabilities(self) -> Dict[str, float]:
        return {
            "0": probability_from_amplitude(self.alpha),
            "1": probability_from_amplitude(self.beta),
        }

    def copy(self) -> "Qubit":
        return Qubit(self.alpha, self.beta)

    def apply_hadamard(self) -> "Qubit":
        """
        Apply the Hadamard matrix:

            alpha' = (alpha + beta) / sqrt(2)
            beta'  = (alpha - beta) / sqrt(2)

        This is the most useful direct formula for a one-qubit H gate.
        """
        new_alpha = (self.alpha + self.beta) * H_SCALE
        new_beta = (self.alpha - self.beta) * H_SCALE
        return Qubit(new_alpha, new_beta)

    def apply_pauli_x(self) -> "Qubit":
        """X swaps |0> and |1> amplitudes."""
        return Qubit(self.beta, self.alpha)

    def apply_pauli_z(self) -> "Qubit":
        """Z preserves |0> and changes the sign of |1>."""
        return Qubit(self.alpha, -self.beta)

    def measure(self, rng: random.Random | None = None) -> int:
        """
        Perform one projective measurement in the computational basis.

        Measurement changes the state:
            outcome 0 -> |0>
            outcome 1 -> |1>
        """
        if rng is None:
            rng = random.Random()

        probability_zero = self.probabilities()["0"]
        outcome = 0 if rng.random() < probability_zero else 1

        if outcome == 0:
            self.alpha, self.beta = 1.0 + 0j, 0.0 + 0j
        else:
            self.alpha, self.beta = 0.0 + 0j, 1.0 + 0j

        return outcome

    def describe(self) -> str:
        return (
            f"|psi> = ({format_complex(self.alpha)})|0> + "
            f"({format_complex(self.beta)})|1>"
        )


def demonstrate_basis_states() -> None:
    section("1. Computational basis states")

    zero = Qubit(1, 0)
    one = Qubit(0, 1)

    print("The |0> state:")
    print(" ", zero.describe())
    print(" ", zero.probabilities())

    print("\nThe |1> state:")
    print(" ", one.describe())
    print(" ", one.probabilities())


def demonstrate_hadamard_definition() -> None:
    section("2. The Hadamard gate")

    print("Hadamard matrix:")
    print("        1       1")
    print("H = 1/sqrt(2) [     ]")
    print("        1      -1")

    zero = Qubit(1, 0)
    one = Qubit(0, 1)

    h_zero = zero.apply_hadamard()
    h_one = one.apply_hadamard()

    print("\nH|0> =", h_zero.describe())
    print("Probabilities:", h_zero.probabilities())

    print("\nH|1> =", h_one.describe())
    print("Probabilities:", h_one.probabilities())

    print(
        "\nThe amplitudes are different for H|0> and H|1>, even though "
        "both have 50/50 measurement probabilities."
    )


def demonstrate_matrix_multiplication() -> None:
    section("3. Explicit matrix-vector multiplication")

    matrix = [
        [H_SCALE, H_SCALE],
        [H_SCALE, -H_SCALE],
    ]

    state_zero = [1.0 + 0j, 0.0 + 0j]

    result = [
        matrix[row][0] * state_zero[0] + matrix[row][1] * state_zero[1]
        for row in range(2)
    ]

    print("Input vector for |0>:", state_zero)
    print("H|0>:", [format_complex(value) for value in result])

    print(
        "\nThis is equivalent to the compact Qubit.apply_hadamard() "
        "implementation used elsewhere in this program."
    )


def demonstrate_normalization() -> None:
    section("4. Normalization and the Born rule")

    state = Qubit(H_SCALE, H_SCALE)

    print(state.describe())
    print("Squared amplitude of |0>:", abs(state.alpha) ** 2)
    print("Squared amplitude of |1>:", abs(state.beta) ** 2)
    print("Total probability:", state.norm_squared())

    print(
        "\nA common mistake is to treat the amplitudes themselves as "
        "probabilities. They are not. Their squared magnitudes are."
    )


def demonstrate_hadamard_twice() -> None:
    section("5. Applying H twice")

    initial = Qubit(1, 0)
    after_first = initial.apply_hadamard()
    after_second = after_first.apply_hadamard()

    print("Initial:", initial.describe())
    print("After H:", after_first.describe())
    print("After H again:", after_second.describe())

    print(
        "\nBecause H is self-inverse, H^2 = I. "
        "Two consecutive Hadamard gates return the original state."
    )


def demonstrate_phase() -> None:
    section("6. Relative phase")

    plus = Qubit(H_SCALE, H_SCALE)
    minus = Qubit(H_SCALE, -H_SCALE)

    print("|+> =", plus.describe())
    print("|-> =", minus.describe())

    print("\nComputational-basis probabilities:")
    print("|+>:", plus.probabilities())
    print("|->:", minus.probabilities())

    print(
        "\nBoth states have the same computational-basis probabilities, "
        "but their relative phase differs."
    )

    print("\nApplying H again:")
    print("H|+> =", plus.apply_hadamard().describe())
    print("H|-> =", minus.apply_hadamard().describe())

    print(
        "\nThe phase becomes observable after another operation because "
        "quantum amplitudes can interfere."
    )


def demonstrate_interference() -> None:
    section("7. Interference through Hadamard operations")

    # H|0> creates two paths with equal positive amplitude.
    plus = Qubit(1, 0).apply_hadamard()

    # H|1> creates equal magnitudes but opposite relative phase.
    minus = Qubit(0, 1).apply_hadamard()

    print("H|0>:", plus.describe())
    print("H|1>:", minus.describe())

    print("\nH(H|0>) =", plus.apply_hadamard().describe())
    print("H(H|1>) =", minus.apply_hadamard().describe())

    print(
        "\nThe second H causes amplitudes to add or cancel. "
        "This is the basic mechanism behind quantum interference."
    )


def demonstrate_measurement_statistics(
    shots: int = 10_000, seed: int = 42
) -> None:
    section("8. Simulated measurement statistics")

    if shots <= 0:
        raise ValueError("shots must be positive.")

    rng = random.Random(seed)
    state = Qubit(1, 0).apply_hadamard()

    counts = {0: 0, 1: 0}

    for _ in range(shots):
        # Each shot starts from the same pre-measurement state.
        measured_state = state.copy()
        outcome = measured_state.measure(rng)
        counts[outcome] += 1

    print(f"Shots: {shots}")
    print("Observed |0>:", counts[0], f"({counts[0] / shots:.4%})")
    print("Observed |1>:", counts[1], f"({counts[1] / shots:.4%})")
    print("Ideal probability of each outcome: 50%")

    print(
        "\nIndividual measurements are probabilistic, while the "
        "probability distribution is determined by the state amplitudes."
    )


def demonstrate_edge_cases() -> None:
    section("9. Edge cases and important distinctions")

    states = {
        "|0>": Qubit(1, 0),
        "|1>": Qubit(0, 1),
        "|+>": Qubit(H_SCALE, H_SCALE),
        "|->": Qubit(H_SCALE, -H_SCALE),
        "i|1>": Qubit(0, 1j),
    }

    for name, state in states.items():
        print(f"{name:>5}: {state.describe():45} probabilities={state.probabilities()}")

    print(
        "\nThe global phase in i|1> does not change computational-basis "
        "measurement probabilities. Relative phase can affect interference."
    )

    print("\nInvalid state demonstration:")
    try:
        Qubit(1, 1)
    except ValueError as error:
        print("Rejected:", error)


def demonstrate_gate_composition() -> None:
    section("10. Gate composition")

    initial = Qubit(1, 0)

    # X changes |0> into |1>.
    after_x = initial.apply_pauli_x()

    # H creates a superposition from |1>, with a relative minus sign.
    after_h = after_x.apply_hadamard()

    # Z changes the phase of |1>.
    after_z = after_h.apply_pauli_z()

    # H converts the phase information into computational-basis information.
    after_final_h = after_z.apply_hadamard()

    print("Initial:", initial.describe())
    print("X:", after_x.describe())
    print("H:", after_h.describe())
    print("Z:", after_z.describe())
    print("H:", after_final_h.describe())

    print(
        "\nThis sequence illustrates why quantum circuits cannot be understood "
        "only by tracking classical bit values. Phase matters."
    )


class QuantumRegister:
    """
    A compact state-vector simulator for n qubits.

    Basis states are stored using integer indices:
        index 0 -> |00...0>
        index 1 -> |00...1>
        ...
        index 2^n - 1 -> |11...1>

    Qubit positions use:
        qubit 0 = least-significant bit.

    This convention is explicitly documented because qubit-ordering mistakes
    are a common source of bugs in quantum programming.
    """

    def __init__(self, number_of_qubits: int) -> None:
        if number_of_qubits < 1:
            raise ValueError("A register must contain at least one qubit.")
        if number_of_qubits > 20:
            raise ValueError(
                "This educational simulator limits registers to 20 qubits "
                "to prevent accidental large memory allocations."
            )

        self.number_of_qubits = number_of_qubits
        self.amplitudes: List[complex] = [0j] * (2**number_of_qubits)
        self.amplitudes[0] = 1.0 + 0j

    def basis_label(self, index: int) -> str:
        return format(index, f"0{self.number_of_qubits}b")

    def validate(self) -> None:
        total = sum(abs(amplitude) ** 2 for amplitude in self.amplitudes)
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            raise ValueError(f"Register is not normalized: probability sum={total}")

    def apply_hadamard(self, qubit: int) -> None:
        """
        Apply H to one selected qubit.

        For every pair of basis states differing only at that qubit:

            a' = (a + b) / sqrt(2)
            b' = (a - b) / sqrt(2)

        This updates the state vector in O(2^n) time.
        """
        self._validate_qubit_index(qubit)
        mask = 1 << qubit
        new_amplitudes = self.amplitudes.copy()

        for index in range(len(self.amplitudes)):
            if index & mask:
                continue

            paired_index = index | mask
            a = self.amplitudes[index]
            b = self.amplitudes[paired_index]

            new_amplitudes[index] = (a + b) * H_SCALE
            new_amplitudes[paired_index] = (a - b) * H_SCALE

        self.amplitudes = new_amplitudes
        self.validate()

    def apply_x(self, qubit: int) -> None:
        """Apply X by swapping amplitudes of basis-state pairs."""
        self._validate_qubit_index(qubit)
        mask = 1 << qubit

        for index in range(len(self.amplitudes)):
            if index & mask:
                continue

            paired_index = index | mask
            self.amplitudes[index], self.amplitudes[paired_index] = (
                self.amplitudes[paired_index],
                self.amplitudes[index],
            )

        self.validate()

    def apply_z(self, qubit: int) -> None:
        """Apply Z by negating amplitudes where the target bit is 1."""
        self._validate_qubit_index(qubit)
        mask = 1 << qubit

        for index in range(len(self.amplitudes)):
            if index & mask:
                self.amplitudes[index] *= -1

        self.validate()

    def apply_cnot(self, control: int, target: int) -> None:
        """
        Controlled-NOT:
            if control bit = 1, flip the target bit.

        This is an important step beyond the single-qubit Hadamard gate
        because H + CNOT can create entanglement.
        """
        self._validate_qubit_index(control)
        self._validate_qubit_index(target)

        if control == target:
            raise ValueError("Control and target must be different qubits.")

        control_mask = 1 << control
        target_mask = 1 << target

        for index in range(len(self.amplitudes)):
            if index & control_mask and not index & target_mask:
                paired_index = index | target_mask
                self.amplitudes[index], self.amplitudes[paired_index] = (
                    self.amplitudes[paired_index],
                    self.amplitudes[index],
                )

        self.validate()

    def probabilities(self) -> Dict[str, float]:
        return {
            self.basis_label(index): abs(amplitude) ** 2
            for index, amplitude in enumerate(self.amplitudes)
        }

    def nonzero_states(self, threshold: float = 1e-10) -> List[Tuple[str, complex]]:
        return [
            (self.basis_label(index), amplitude)
            for index, amplitude in enumerate(self.amplitudes)
            if abs(amplitude) > threshold
        ]

    def measure(self, rng: random.Random | None = None) -> str:
        """Measure the entire register and collapse it to one basis state."""
        if rng is None:
            rng = random.Random()

        random_value = rng.random()
        cumulative_probability = 0.0

        for index, amplitude in enumerate(self.amplitudes):
            cumulative_probability += abs(amplitude) ** 2
            if random_value < cumulative_probability:
                outcome = self.basis_label(index)
                self.amplitudes = [0j] * len(self.amplitudes)
                self.amplitudes[index] = 1.0 + 0j
                return outcome

        # Floating-point rounding can reach this point for a value extremely
        # close to 1. Returning the final basis state preserves normalization.
        final_index = len(self.amplitudes) - 1
        self.amplitudes = [0j] * len(self.amplitudes)
        self.amplitudes[final_index] = 1.0 + 0j
        return self.basis_label(final_index)

    def _validate_qubit_index(self, qubit: int) -> None:
        if not isinstance(qubit, int):
            raise TypeError("Qubit index must be an integer.")
        if not 0 <= qubit < self.number_of_qubits:
            raise IndexError(
                f"Qubit index must be between 0 and {self.number_of_qubits - 1}."
            )


def print_register(register: QuantumRegister) -> None:
    for label, amplitude in register.nonzero_states():
        probability = abs(amplitude) ** 2
        print(
            f"|{label}> amplitude={format_complex(amplitude):>12} "
            f"probability={probability:.4f}"
        )


def demonstrate_two_qubit_superposition() -> None:
    section("11. Two-qubit superposition")

    register = QuantumRegister(2)

    print("Initial state:")
    print_register(register)

    # H on each qubit creates four equally likely computational states.
    register.apply_hadamard(0)
    register.apply_hadamard(1)

    print("\nAfter H on both qubits:")
    print_register(register)

    print(
        "\nTwo independent Hadamard operations create:\n"
        "(|00> + |01> + |10> + |11>) / 2"
    )


def demonstrate_bell_state() -> None:
    section("12. Creating a Bell state")

    register = QuantumRegister(2)

    # Step 1: H on qubit 0 creates a two-branch superposition.
    register.apply_hadamard(0)

    # Step 2: CNOT correlates qubit 1 with qubit 0.
    register.apply_cnot(control=0, target=1)

    print("Bell state:")
    print_register(register)

    print(
        "\nThe resulting state is:\n"
        "(|00> + |11>) / sqrt(2)"
    )

    print(
        "\nOnly 00 and 11 occur on measurement. This is an entangled state, "
        "not merely two classical random bits."
    )


def demonstrate_sampling_register(
    shots: int = 5000, seed: int = 123
) -> None:
    section("13. Sampling a two-qubit Bell state")

    rng = random.Random(seed)
    counts: Dict[str, int] = {"00": 0, "01": 0, "10": 0, "11": 0}

    for _ in range(shots):
        register = QuantumRegister(2)
        register.apply_hadamard(0)
        register.apply_cnot(0, 1)
        outcome = register.measure(rng)
        counts[outcome] += 1

    for state, count in counts.items():
        print(f"{state}: {count:4d} ({count / shots:.2%})")

    print(
        "\nThe cross outcomes 01 and 10 should remain absent in this ideal "
        "simulation."
    )


def compare_hadamard_properties() -> None:
    section("14. Important mathematical properties")

    h = [
        [H_SCALE, H_SCALE],
        [H_SCALE, -H_SCALE],
    ]

    def matrix_multiply(a: List[List[complex]], b: List[List[complex]]) -> List[List[complex]]:
        rows = len(a)
        columns = len(b[0])
        inner = len(b)
        result = [[0j for _ in range(columns)] for _ in range(rows)]

        for i in range(rows):
            for j in range(columns):
                result[i][j] = sum(a[i][k] * b[k][j] for k in range(inner))

        return result

    identity = matrix_multiply(h, h)

    print("H x H:")
    for row in identity:
        print([format_complex(value) for value in row])

    print(
        "\nThe result is the identity matrix, demonstrating H^2 = I."
    )

    print(
        "\nThe Hadamard gate is also unitary. Therefore it preserves the "
        "norm of quantum state vectors and has a valid inverse."
    )


def demonstrate_invalid_operations() -> None:
    section("15. Validation and failure conditions")

    register = QuantumRegister(2)

    cases = [
        ("negative qubit index", lambda: register.apply_hadamard(-1)),
        ("out-of-range qubit index", lambda: register.apply_hadamard(2)),
        ("same CNOT control/target", lambda: register.apply_cnot(0, 0)),
        ("invalid one-qubit state", lambda: Qubit(0.5, 0.5)),
    ]

    for name, operation in cases:
        try:
            operation()
            print(name, "unexpectedly succeeded")
        except (ValueError, IndexError, TypeError) as error:
            print(f"{name}: correctly rejected -> {error}")


def performance_discussion() -> None:
    section("16. Performance characteristics")

    print(
        "A single-qubit state vector contains 2 amplitudes: O(2).\n"
        "An n-qubit state vector contains 2^n amplitudes: O(2^n) memory.\n"
        "Applying a one-qubit gate to a state vector generally costs O(2^n) time.\n"
        "A dense classical state-vector simulator therefore scales exponentially "
        "with the number of simulated qubits."
    )

    print(
        "\nThis exponential state-space growth is a central reason why quantum "
        "simulation can become computationally expensive even when the circuit "
        "description itself is short."
    )


def practical_checklist() -> None:
    section("17. Practical Hadamard-gate checklist")

    checklist = [
        "Know the computational basis states |0> and |1>.",
        "Treat amplitudes as complex numbers, not direct probabilities.",
        "Use the Born rule: probability = squared magnitude of amplitude.",
        "Remember that H|0> creates the |+> state.",
        "Remember that H|1> creates the |-> state.",
        "Track relative phase because it affects interference.",
        "Remember H is self-inverse: H^2 = I.",
        "Distinguish superposition from classical uncertainty.",
        "Distinguish superposition from entanglement.",
        "Track qubit ordering explicitly in multi-qubit simulations.",
        "Normalize states after transformations.",
        "Expect exponentially growing state-vector storage for classical simulation.",
    ]

    for item in checklist:
        print("•", item)


def run_all_demonstrations() -> None:
    print("HADAMARD GATE — CREATING SUPERPOSITION")
    print("Self-contained quantum-computing study and simulation")

    demonstrate_basis_states()
    demonstrate_hadamard_definition()
    demonstrate_matrix_multiplication()
    demonstrate_normalization()
    demonstrate_hadamard_twice()
    demonstrate_phase()
    demonstrate_interference()
    demonstrate_measurement_statistics()
    demonstrate_edge_cases()
    demonstrate_gate_composition()
    demonstrate_two_qubit_superposition()
    demonstrate_bell_state()
    demonstrate_sampling_register()
    compare_hadamard_properties()
    demonstrate_invalid_operations()
    performance_discussion()
    practical_checklist()

    section("18. Final executable assertions")

    assert Qubit(1, 0).apply_hadamard().probabilities()["0"] == pytest_approx(0.5)
    assert Qubit(1, 0).apply_hadamard().probabilities()["1"] == pytest_approx(0.5)

    twice = Qubit(1, 0).apply_hadamard().apply_hadamard()
    assert math.isclose(abs(twice.alpha), 1.0, abs_tol=EPSILON)
    assert math.isclose(abs(twice.beta), 0.0, abs_tol=EPSILON)

    bell = QuantumRegister(2)
    bell.apply_hadamard(0)
    bell.apply_cnot(0, 1)
    bell_probabilities = bell.probabilities()

    assert math.isclose(bell_probabilities["00"], 0.5, abs_tol=EPSILON)
    assert math.isclose(bell_probabilities["11"], 0.5, abs_tol=EPSILON)
    assert math.isclose(bell_probabilities["01"], 0.0, abs_tol=EPSILON)
    assert math.isclose(bell_probabilities["10"], 0.0, abs_tol=EPSILON)

    print("All educational assertions passed.")


def pytest_approx(expected: float, tolerance: float = 1e-12) -> float:
    """
    Small helper used instead of depending on pytest.

    It returns the expected value so an exact-looking assertion remains
    readable while the detailed checks below use math.isclose().
    """
    return expected


if __name__ == "__main__":
    run_all_demonstrations()
