"""
Phase Gates: S, T, and Phase Operations
========================================

A self-contained study program covering quantum phase operations from beginner
to advanced level.

Topics demonstrated:
- Complex amplitudes and quantum states
- Global and relative phase
- Single-qubit phase gate P(theta)
- Z, S, and T gates
- Adjoint/inverse gates
- Gate powers and phase relationships
- Bloch-sphere interpretation
- Interference
- Controlled phase operations
- CZ and controlled-P(theta)
- Multi-qubit state simulation
- Tensor products
- Basis-state action
- Measurement probabilities
- Numerical precision
- Matrix unitarity
- Circuit composition
- Gate commutation and non-commutation
- Phase kickback
- Quantum Fourier Transform phase rotations
- Error handling and validation
- Performance considerations
- Security/reliability considerations for simulators
- A small advanced quantum phase circuit simulator

No external packages are required.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Iterable, Sequence


# ============================================================================
# 1. BASIC COMPLEX-NUMBER AND QUANTUM-STATE UTILITIES
# ============================================================================

EPSILON = 1e-10


def clean_complex(value: complex, tolerance: float = 1e-10) -> complex:
    """Remove tiny numerical noise from real and imaginary components."""
    real = 0.0 if abs(value.real) < tolerance else value.real
    imag = 0.0 if abs(value.imag) < tolerance else value.imag
    return complex(real, imag)


def format_complex(value: complex, precision: int = 4) -> str:
    """Format a complex number compactly for educational output."""
    value = clean_complex(value)
    real = round(value.real, precision)
    imag = round(value.imag, precision)

    if abs(imag) < EPSILON:
        return f"{real:.{precision}f}"
    if abs(real) < EPSILON:
        return f"{imag:.{precision}f}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.{precision}f} {sign} {abs(imag):.{precision}f}i"


def format_angle(theta: float) -> str:
    """Show an angle in radians and degrees."""
    return f"{theta:.6f} rad ({math.degrees(theta):.2f}°)"


def vector_norm(state: Sequence[complex]) -> float:
    """Calculate the Euclidean norm of a quantum state vector."""
    return math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def normalize_state(state: Sequence[complex]) -> list[complex]:
    """
    Normalize a state vector.

    Quantum state vectors must have norm 1 so that measurement probabilities
    sum to one.
    """
    norm = vector_norm(state)

    if norm < EPSILON:
        raise ValueError("Cannot normalize a zero vector.")

    return [amplitude / norm for amplitude in state]


def probabilities(state: Sequence[complex]) -> list[float]:
    """Convert amplitudes into computational-basis probabilities."""
    return [abs(amplitude) ** 2 for amplitude in state]


def validate_state(state: Sequence[complex]) -> None:
    """Verify that a vector has a valid normalized quantum-state norm."""
    if not state:
        raise ValueError("A quantum state cannot be empty.")

    norm = vector_norm(state)

    if not math.isclose(norm, 1.0, abs_tol=1e-9):
        raise ValueError(f"State is not normalized. Norm = {norm}")


def global_phase_equivalent(
    state_a: Sequence[complex],
    state_b: Sequence[complex],
    tolerance: float = 1e-9,
) -> bool:
    """
    Determine whether two states differ only by a global phase.

    |psi> and exp(i*phi)|psi> describe the same physical pure state.
    """
    if len(state_a) != len(state_b):
        return False

    norm_a = vector_norm(state_a)
    norm_b = vector_norm(state_b)

    if not math.isclose(norm_a, norm_b, abs_tol=tolerance):
        return False

    reference_index = None

    for index, amplitude in enumerate(state_a):
        if abs(amplitude) > tolerance and abs(state_b[index]) > tolerance:
            reference_index = index
            break

    if reference_index is None:
        return True

    phase_ratio = state_b[reference_index] / state_a[reference_index]

    if not math.isclose(abs(phase_ratio), 1.0, abs_tol=tolerance):
        return False

    for a, b in zip(state_a, state_b):
        if not math.isclose(b, phase_ratio * a, abs_tol=tolerance):
            return False

    return True


# ============================================================================
# 2. MATRIX OPERATIONS
# ============================================================================

Matrix = list[list[complex]]


def identity_matrix(size: int) -> Matrix:
    """Create an identity matrix."""
    return [
        [1.0 + 0.0j if row == column else 0.0 + 0.0j
         for column in range(size)]
        for row in range(size)
    ]


def matrix_multiply(a: Matrix, b: Matrix) -> Matrix:
    """Multiply two compatible matrices."""
    if not a or not b:
        raise ValueError("Matrices cannot be empty.")

    if len(a[0]) != len(b):
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        [
            sum(a[row][k] * b[k][column] for k in range(len(b)))
            for column in range(len(b[0]))
        ]
        for row in range(len(a))
    ]


def matrix_vector_multiply(matrix: Matrix, vector: Sequence[complex]) -> list[complex]:
    """Apply a matrix to a state vector."""
    if len(matrix[0]) != len(vector):
        raise ValueError("Matrix and vector dimensions are incompatible.")

    return [
        sum(matrix[row][column] * vector[column]
            for column in range(len(vector)))
        for row in range(len(matrix))
    ]


def conjugate_transpose(matrix: Matrix) -> Matrix:
    """Calculate the Hermitian adjoint U†."""
    return [
        [matrix[column][row].conjugate() for column in range(len(matrix))]
        for row in range(len(matrix[0]))
    ]


def matrices_close(a: Matrix, b: Matrix, tolerance: float = 1e-9) -> bool:
    """Compare two matrices numerically."""
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        return False

    return all(
        math.isclose(a[row][column].real, b[row][column].real, abs_tol=tolerance)
        and math.isclose(a[row][column].imag, b[row][column].imag, abs_tol=tolerance)
        for row in range(len(a))
        for column in range(len(a[0]))
    )


def is_unitary(matrix: Matrix, tolerance: float = 1e-9) -> bool:
    """
    Check U†U = I.

    Quantum gates must be unitary because quantum evolution is reversible
    before measurement.
    """
    if len(matrix) != len(matrix[0]):
        return False

    product = matrix_multiply(conjugate_transpose(matrix), matrix)
    return matrices_close(product, identity_matrix(len(matrix)), tolerance)


def print_matrix(matrix: Matrix, title: str = "") -> None:
    """Print a readable complex matrix."""
    if title:
        print(f"\n{title}")

    for row in matrix:
        print("[ " + ", ".join(format_complex(value) for value in row) + " ]")


# ============================================================================
# 3. FUNDAMENTAL SINGLE-QUBIT GATES
# ============================================================================

SQRT_2_INV = 1 / math.sqrt(2)

I_GATE: Matrix = [
    [1, 0],
    [0, 1],
]

X_GATE: Matrix = [
    [0, 1],
    [1, 0],
]

Y_GATE: Matrix = [
    [0, -1j],
    [1j, 0],
]

Z_GATE: Matrix = [
    [1, 0],
    [0, -1],
]

H_GATE: Matrix = [
    [SQRT_2_INV, SQRT_2_INV],
    [SQRT_2_INV, -SQRT_2_INV],
]


def phase_gate(theta: float) -> Matrix:
    """
    General single-qubit phase gate.

        P(theta) = [[1, 0],
                    [0, exp(i theta)]]

    It leaves |0> unchanged and multiplies |1> by exp(i theta).
    """
    return [
        [1, 0],
        [0, cmath.exp(1j * theta)],
    ]


def s_gate() -> Matrix:
    """S = P(pi/2)."""
    return phase_gate(math.pi / 2)


def t_gate() -> Matrix:
    """T = P(pi/4)."""
    return phase_gate(math.pi / 4)


def s_dagger_gate() -> Matrix:
    """S† = P(-pi/2)."""
    return phase_gate(-math.pi / 2)


def t_dagger_gate() -> Matrix:
    """T† = P(-pi/4)."""
    return phase_gate(-math.pi / 4)


def z_from_phase() -> Matrix:
    """
    P(pi) is diag(1, -1), exactly the Z gate.
    """
    return phase_gate(math.pi)


# ============================================================================
# 4. BASIC PHASE-GATE DEMONSTRATIONS
# ============================================================================

def demonstrate_basic_phase_gates() -> None:
    print("\n" + "=" * 80)
    print("BASIC PHASE GATES")
    print("=" * 80)

    gates = {
        "I": I_GATE,
        "Z": Z_GATE,
        "P(pi)": phase_gate(math.pi),
        "S": s_gate(),
        "T": t_gate(),
        "S†": s_dagger_gate(),
        "T†": t_dagger_gate(),
    }

    for name, matrix in gates.items():
        print_matrix(matrix, name)
        print(f"Unitary: {is_unitary(matrix)}")

    print("\nKey relationships:")
    print("Z = P(pi)")
    print("S = P(pi/2)")
    print("T = P(pi/4)")
    print("S^2 = Z")
    print("T^2 = S")
    print("T^4 = Z")
    print("T^8 = I")


# ============================================================================
# 5. APPLYING PHASE OPERATIONS TO STATES
# ============================================================================

def apply_gate(state: Sequence[complex], gate: Matrix) -> list[complex]:
    """Apply a unitary gate to a state."""
    validate_state(state)
    if not is_unitary(gate):
        raise ValueError("The supplied matrix is not unitary.")
    return matrix_vector_multiply(gate, state)


def show_state(
    label: str,
    state: Sequence[complex],
    basis_labels: Sequence[str] | None = None,
) -> None:
    """Display amplitudes and probabilities."""
    validate_state(state)

    print(f"\n{label}")

    if basis_labels is None:
        basis_labels = [f"|{i}>" for i in range(len(state))]

    for basis, amplitude, probability in zip(
        basis_labels,
        state,
        probabilities(state),
    ):
        print(
            f"{basis:>6}: amplitude={format_complex(amplitude)}, "
            f"probability={probability:.6f}"
        )


def demonstrate_state_action() -> None:
    print("\n" + "=" * 80)
    print("PHASE GATES ACTING ON BASIS STATES")
    print("=" * 80)

    zero = [1 + 0j, 0 + 0j]
    one = [0 + 0j, 1 + 0j]

    for gate_name, gate in [
        ("Z", Z_GATE),
        ("S", s_gate()),
        ("T", t_gate()),
    ]:
        print(f"\n{gate_name}|0> =")
        show_state("", apply_gate(zero, gate))

        print(f"{gate_name}|1> =")
        show_state("", apply_gate(one, gate))

    print(
        "\nThe probability of measuring |1> remains 1 after Z, S, or T, "
        "but its phase changes."
    )


# ============================================================================
# 6. GLOBAL PHASE VERSUS RELATIVE PHASE
# ============================================================================

def demonstrate_global_and_relative_phase() -> None:
    print("\n" + "=" * 80)
    print("GLOBAL PHASE VERSUS RELATIVE PHASE")
    print("=" * 80)

    state = [SQRT_2_INV, SQRT_2_INV]
    global_phase_state = [
        1j * amplitude for amplitude in state
    ]

    relative_phase_state = [
        SQRT_2_INV,
        -SQRT_2_INV,
    ]

    show_state("Original |+> state", state)
    show_state("Global phase: i|+>", global_phase_state)
    show_state("Relative phase: |->", relative_phase_state)

    print("\nOriginal and global-phase states equivalent:",
          global_phase_equivalent(state, global_phase_state))

    print("Original and relative-phase states equivalent:",
          global_phase_equivalent(state, relative_phase_state))

    print(
        "\nImportant distinction: a global phase does not change measurement "
        "statistics, while a relative phase can change interference."
    )


# ============================================================================
# 7. INTERFERENCE: WHY PHASE MATTERS
# ============================================================================

def demonstrate_interference() -> None:
    print("\n" + "=" * 80)
    print("INTERFERENCE CREATED BY RELATIVE PHASE")
    print("=" * 80)

    plus_state = apply_gate([1 + 0j, 0 + 0j], H_GATE)
    minus_state = apply_gate([1 + 0j, 0 + 0j], H_GATE)
    minus_state = apply_gate(minus_state, Z_GATE)

    plus_after_h = apply_gate(plus_state, H_GATE)
    minus_after_h = apply_gate(minus_state, H_GATE)

    show_state("H|0> = |+>", plus_state)
    show_state("ZH|0> = |->", minus_state)

    show_state("H|+>", plus_after_h)
    show_state("H|->", minus_after_h)

    print(
        "\nThe phase difference converts into different amplitudes after "
        "the second Hadamard. This is interference."
    )


# ============================================================================
# 8. POWERS AND PERIODICITY OF S AND T
# ============================================================================

def matrix_power(matrix: Matrix, exponent: int) -> Matrix:
    """Integer matrix exponentiation using repeated squaring."""
    if exponent < 0:
        inverse = conjugate_transpose(matrix)
        return matrix_power(inverse, -exponent)

    result = identity_matrix(len(matrix))
    base = matrix

    while exponent:
        if exponent & 1:
            result = matrix_multiply(result, base)
        base = matrix_multiply(base, base)
        exponent >>= 1

    return result


def demonstrate_gate_powers() -> None:
    print("\n" + "=" * 80)
    print("S AND T POWERS")
    print("=" * 80)

    for gate_name, gate in [("S", s_gate()), ("T", t_gate())]:
        print(f"\n{gate_name} powers:")
        for exponent in range(1, 9):
            power = matrix_power(gate, exponent)
            print_matrix(power, f"{gate_name}^{exponent}")

    print("\nExact periodicity:")
    print("S^4 = I")
    print("T^8 = I")


# ============================================================================
# 9. CONTROLLED PHASE GATES
# ============================================================================

def controlled_phase_gate(theta: float) -> Matrix:
    """
    Controlled phase gate on two qubits.

    Basis ordering:
        |00>, |01>, |10>, |11>

    Only |11> receives exp(i*theta).
    """
    return [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, cmath.exp(1j * theta)],
    ]


def demonstrate_controlled_phase() -> None:
    print("\n" + "=" * 80)
    print("CONTROLLED PHASE OPERATIONS")
    print("=" * 80)

    basis_states = {
        "|00>": [1, 0, 0, 0],
        "|01>": [0, 1, 0, 0],
        "|10>": [0, 0, 1, 0],
        "|11>": [0, 0, 0, 1],
    }

    controlled_t = controlled_phase_gate(math.pi / 4)

    for label, state in basis_states.items():
        transformed = apply_gate(state, controlled_t)
        print(f"\nControlled-T acting on {label}:")
        show_state("", transformed, list(basis_states.keys()))


# ============================================================================
# 10. TENSOR PRODUCTS
# ============================================================================

def tensor_product(a: Sequence[complex], b: Sequence[complex]) -> list[complex]:
    """Tensor product of two state vectors."""
    return [x * y for x in a for y in b]


def tensor_matrix(a: Matrix, b: Matrix) -> Matrix:
    """Kronecker/tensor product of two matrices."""
    result: Matrix = []

    for row_a in a:
        for row_b in b:
            result.append([
                value_a * value_b
                for value_a in row_a
                for value_b in row_b
            ])

    return result


def demonstrate_tensor_products() -> None:
    print("\n" + "=" * 80)
    print("TENSOR PRODUCTS AND MULTI-QUBIT PHASE OPERATIONS")
    print("=" * 80)

    zero = [1, 0]
    one = [0, 1]

    state_01 = tensor_product(zero, one)
    state_11 = tensor_product(one, one)

    show_state("|01>", state_01, ["|00>", "|01>", "|10>", "|11>"])
    show_state("|11>", state_11, ["|00>", "|01>", "|10>", "|11>"])

    local_t_on_second = tensor_matrix(I_GATE, t_gate())

    transformed = matrix_vector_multiply(local_t_on_second, state_01)

    show_state(
        "(I ⊗ T)|01>",
        transformed,
        ["|00>", "|01>", "|10>", "|11>"],
    )

    print(
        "\nA local phase operation can be represented by a tensor product "
        "with identity operators on unaffected qubits."
    )


# ============================================================================
# 11. PHASE KICKBACK
# ============================================================================

def demonstrate_phase_kickback() -> None:
    print("\n" + "=" * 80)
    print("PHASE KICKBACK")
    print("=" * 80)

    """
    A controlled-U operation can transfer a phase into a control register
    when the target is prepared in an eigenstate of U.

    For the Z gate:
        Z|1> = -|1>

    If the target is |1>, controlled-Z effectively applies Z to the control
    component conditional on the control state.
    """

    plus_control = [SQRT_2_INV, 0, SQRT_2_INV, 0]
    cz = controlled_phase_gate(math.pi)

    result = apply_gate(plus_control, cz)

    show_state(
        "CZ applied to (|00> + |10>)/sqrt(2)",
        result,
        ["|00>", "|01>", "|10>", "|11>"],
    )

    print(
        "\nControlled operations can encode phase information in a control "
        "register. This mechanism is central to several quantum algorithms."
    )


# ============================================================================
# 12. QFT-STYLE PHASE ROTATIONS
# ============================================================================

def qft_phase_angle(distance: int) -> float:
    """Return the QFT phase angle for a positive denominator distance."""
    if distance <= 0:
        raise ValueError("Distance must be positive.")
    return math.pi / (2 ** (distance - 1))


def demonstrate_qft_phase_rotations() -> None:
    print("\n" + "=" * 80)
    print("PHASE ROTATIONS USED BY THE QUANTUM FOURIER TRANSFORM")
    print("=" * 80)

    for distance in range(1, 5):
        theta = qft_phase_angle(distance)
        print(
            f"R_{distance}: theta={format_angle(theta)}, "
            f"matrix diagonal phase={format_complex(cmath.exp(1j * theta))}"
        )

    print(
        "\nQFT circuits use a family of controlled phase rotations with "
        "progressively smaller angles."
    )


# ============================================================================
# 13. NON-COMMUTATION AND CIRCUIT ORDER
# ============================================================================

def demonstrate_gate_order() -> None:
    print("\n" + "=" * 80)
    print("GATE ORDER AND COMMUTATION")
    print("=" * 80)

    state = [1 + 0j, 0 + 0j]

    z_then_h = apply_gate(apply_gate(state, Z_GATE), H_GATE)
    h_then_z = apply_gate(apply_gate(state, H_GATE), Z_GATE)

    show_state("H Z |0>", z_then_h)
    show_state("Z H |0>", h_then_z)

    print(
        "\nZ and H generally do not commute: HZ != ZH."
    )

    s_then_t = matrix_multiply(t_gate(), s_gate())
    t_then_s = matrix_multiply(s_gate(), t_gate())

    print(
        "S and T commute because both are diagonal in the computational basis:",
        matrices_close(s_then_t, t_then_s),
    )


# ============================================================================
# 14. PHASE ESTIMATION-STYLE ACCUMULATION
# ============================================================================

def demonstrate_phase_accumulation() -> None:
    print("\n" + "=" * 80)
    print("PHASE ACCUMULATION")
    print("=" * 80)

    initial = [SQRT_2_INV, SQRT_2_INV]
    state = initial

    print("Starting state: (|0> + |1>)/sqrt(2)")

    for step in range(1, 5):
        state = apply_gate(state, t_gate())
        print(
            f"After T^{step}: "
            f"|1> phase = {format_angle(step * math.pi / 4)}"
        )
        show_state("", state)

    print(
        "\nRepeated phase gates accumulate phase modulo 2π. "
        "Because T has an angle of π/4, eight applications return to identity."
    )


# ============================================================================
# 15. MEASUREMENT SIMULATION
# ============================================================================

def sample_measurements(
    state: Sequence[complex],
    shots: int = 1000,
    seed: int = 7,
) -> dict[int, int]:
    """
    Simple measurement sampler.

    Python's standard library random module is sufficient for educational
    simulation. Real quantum hardware has additional physical and device-level
    behavior that this simulator does not model.
    """
    import random

    if shots <= 0:
        raise ValueError("shots must be positive.")

    validate_state(state)

    generator = random.Random(seed)
    probability_distribution = probabilities(state)

    cumulative = []
    total = 0.0

    for probability in probability_distribution:
        total += probability
        cumulative.append(total)

    counts = {index: 0 for index in range(len(state))}

    for _ in range(shots):
        random_value = generator.random()

        for index, boundary in enumerate(cumulative):
            if random_value < boundary:
                counts[index] += 1
                break

    return counts


def demonstrate_measurement() -> None:
    print("\n" + "=" * 80)
    print("MEASUREMENT STATISTICS")
    print("=" * 80)

    state = apply_gate([1, 0], H_GATE)
    state = apply_gate(state, t_gate())

    counts = sample_measurements(state, shots=2000, seed=42)

    show_state("State before measurement", state)

    print("\n2000 simulated measurements:")
    print(counts)

    print(
        "\nT changes phase but does not change computational-basis "
        "probabilities when applied directly to |+>."
    )


# ============================================================================
# 16. VALIDATION AND FAILURE CASES
# ============================================================================

def demonstrate_validation() -> None:
    print("\n" + "=" * 80)
    print("VALIDATION AND FAILURE CASES")
    print("=" * 80)

    invalid_state = [1 + 0j, 1 + 0j]

    try:
        validate_state(invalid_state)
    except ValueError as error:
        print(f"Invalid state rejected: {error}")

    try:
        normalize_state([0j, 0j])
    except ValueError as error:
        print(f"Zero vector rejected: {error}")

    non_unitary = [
        [1, 0],
        [0, 2],
    ]

    try:
        apply_gate([1, 0], non_unitary)
    except ValueError as error:
        print(f"Non-unitary gate rejected: {error}")


# ============================================================================
# 17. ADVANCED: PARAMETERIZED PHASE CIRCUIT
# ============================================================================

@dataclass
class GateApplication:
    """Record one gate operation in a circuit."""

    name: str
    matrix: Matrix


class SingleQubitCircuit:
    """Small educational circuit class supporting arbitrary unitary gates."""

    def __init__(self) -> None:
        self.operations: list[GateApplication] = []

    def add_gate(self, name: str, matrix: Matrix) -> None:
        if len(matrix) != 2 or len(matrix[0]) != 2:
            raise ValueError("SingleQubitCircuit accepts only 2x2 gates.")

        if not is_unitary(matrix):
            raise ValueError(f"{name} is not unitary.")

        self.operations.append(GateApplication(name, matrix))

    def add_phase(self, theta: float) -> None:
        self.add_gate(
            f"P({math.degrees(theta):.2f}°)",
            phase_gate(theta),
        )

    def run(self, initial_state: Sequence[complex]) -> list[complex]:
        state = list(initial_state)
        validate_state(state)

        for operation in self.operations:
            state = apply_gate(state, operation.matrix)

        return state

    def combined_matrix(self) -> Matrix:
        """
        Return the matrix representing the complete circuit.

        If gates are G1, G2, G3 in execution order, the total operation is
        G3 * G2 * G1.
        """
        result = identity_matrix(2)

        for operation in self.operations:
            result = matrix_multiply(operation.matrix, result)

        return result

    def describe(self) -> None:
        print("\nCircuit operations:")
        for index, operation in enumerate(self.operations, start=1):
            print(f"{index}. {operation.name}")


def demonstrate_advanced_circuit() -> None:
    print("\n" + "=" * 80)
    print("ADVANCED PARAMETERIZED PHASE CIRCUIT")
    print("=" * 80)

    circuit = SingleQubitCircuit()

    circuit.add_gate("H", H_GATE)
    circuit.add_gate("T", t_gate())
    circuit.add_phase(math.pi / 3)
    circuit.add_gate("S†", s_dagger_gate())
    circuit.add_gate("H", H_GATE)

    circuit.describe()

    initial_state = [1 + 0j, 0 + 0j]
    final_state = circuit.run(initial_state)

    show_state("Final state", final_state)

    combined = circuit.combined_matrix()
    print_matrix(combined, "Combined circuit matrix")
    print("Combined matrix is unitary:", is_unitary(combined))


# ============================================================================
# 18. ADVANCED: PHASE OPERATION COMPARISON
# ============================================================================

def compare_phase_gates() -> None:
    print("\n" + "=" * 80)
    print("COMPARISON OF Z, S, T, AND GENERAL P(theta)")
    print("=" * 80)

    rows = [
        ("Z", math.pi),
        ("S", math.pi / 2),
        ("T", math.pi / 4),
        ("P(pi/8)", math.pi / 8),
    ]

    print(f"{'Gate':<10}{'Angle':<25}{'Phase on |1>':<20}")

    for name, theta in rows:
        phase = cmath.exp(1j * theta)
        print(
            f"{name:<10}"
            f"{format_angle(theta):<25}"
            f"{format_complex(phase):<20}"
        )

    print("\nAll are diagonal phase operations.")
    print("Their key difference is the phase angle applied to |1>.")


# ============================================================================
# 19. ADVANCED: PHASE-SENSITIVE INTERFERENCE EXPERIMENT
# ============================================================================

def interference_experiment(theta: float) -> tuple[float, float]:
    """
    Prepare |+>, apply P(theta), then H.

    Starting from |+>:
        H P(theta) H |0>

    The probability of |0> is cos²(theta/2).
    The probability of |1> is sin²(theta/2).
    """
    state = apply_gate([1, 0], H_GATE)
    state = apply_gate(state, phase_gate(theta))
    state = apply_gate(state, H_GATE)

    result = probabilities(state)
    return result[0], result[1]


def demonstrate_phase_to_probability_conversion() -> None:
    print("\n" + "=" * 80)
    print("CONVERTING PHASE INFORMATION INTO MEASUREMENT PROBABILITY")
    print("=" * 80)

    for degrees in [0, 45, 90, 135, 180, 270, 360]:
        theta = math.radians(degrees)
        p_zero, p_one = interference_experiment(theta)

        theoretical_zero = math.cos(theta / 2) ** 2
        theoretical_one = math.sin(theta / 2) ** 2

        print(
            f"theta={degrees:>3}° | "
            f"P(0)={p_zero:.4f} "
            f"(theory {theoretical_zero:.4f}) | "
            f"P(1)={p_one:.4f} "
            f"(theory {theoretical_one:.4f})"
        )


# ============================================================================
# 20. ADVANCED: MULTI-QUBIT PHASE ORACLE
# ============================================================================

class TwoQubitPhaseOracle:
    """
    Educational diagonal phase oracle.

    Each computational basis state can receive its own phase.
    This demonstrates the general principle that a diagonal unitary can
    encode phase information without changing computational-basis magnitudes.
    """

    BASIS = ["00", "01", "10", "11"]

    def __init__(self, phases: dict[str, float]) -> None:
        missing = set(self.BASIS) - set(phases)
        if missing:
            raise ValueError(f"Missing phases for basis states: {sorted(missing)}")

        self.phases = dict(phases)

    def matrix(self) -> Matrix:
        return [
            [
                cmath.exp(1j * self.phases[self.BASIS[index]])
                if row == index
                else 0
                for index in range(4)
            ]
            for row in range(4)
        ]

    def apply(self, state: Sequence[complex]) -> list[complex]:
        return apply_gate(state, self.matrix())


def demonstrate_phase_oracle() -> None:
    print("\n" + "=" * 80)
    print("MULTI-QUBIT PHASE ORACLE")
    print("=" * 80)

    oracle = TwoQubitPhaseOracle({
        "00": 0,
        "01": math.pi / 4,
        "10": math.pi / 2,
        "11": math.pi,
    })

    print_matrix(oracle.matrix(), "Oracle matrix")

    uniform = [0.5, 0.5, 0.5, 0.5]
    transformed = oracle.apply(uniform)

    show_state(
        "Uniform superposition after phase oracle",
        transformed,
        ["|00>", "|01>", "|10>", "|11>"],
    )

    print(
        "\nThe probabilities remain equal immediately after the diagonal "
        "phase oracle, but later interference operations can reveal the "
        "encoded phase pattern."
    )


# ============================================================================
# 21. SECURITY AND IMPLEMENTATION CONSIDERATIONS
# ============================================================================

def discuss_production_considerations() -> None:
    print("\n" + "=" * 80)
    print("PRODUCTION AND IMPLEMENTATION CONSIDERATIONS")
    print("=" * 80)

    points = [
        "Validate state dimensions before matrix multiplication.",
        "Validate gate unitarity when arbitrary matrices are accepted.",
        "Use numerically stable tolerance checks rather than exact float equality.",
        "Track qubit ordering explicitly in multi-qubit simulators.",
        "Document whether matrices act on column vectors from the left.",
        "Avoid unnecessary dense matrices for large quantum systems.",
        "Use sparse or structured representations when the circuit permits them.",
        "Separate circuit construction, simulation, measurement, and reporting.",
        "Treat random measurement simulation as probabilistic and seedable for tests.",
        "Do not confuse simulator correctness with physical hardware fidelity.",
        "For security-sensitive software, validate input and avoid trusting serialized gates.",
        "For large n-qubit systems, memory grows exponentially with n.",
    ]

    for number, point in enumerate(points, start=1):
        print(f"{number:>2}. {point}")


# ============================================================================
# 22. PERFORMANCE DEMONSTRATION
# ============================================================================

def performance_notes() -> None:
    print("\n" + "=" * 80)
    print("PERFORMANCE CONSIDERATIONS")
    print("=" * 80)

    print(
        "A state-vector simulator for n qubits stores 2^n amplitudes."
    )
    print(
        "Applying a dense 2^n × 2^n matrix directly is generally O(4^n) "
        "per matrix-vector multiplication."
    )
    print(
        "Applying local one- or two-qubit gates using specialized operations "
        "can be substantially cheaper than constructing a full dense matrix."
    )

    for qubits in range(1, 11):
        amplitudes = 2 ** qubits
        print(
            f"{qubits:2} qubits -> {amplitudes:5} complex amplitudes"
        )


# ============================================================================
# 23. SELF-TESTS
# ============================================================================

def assert_matrix_identity(a: Matrix, b: Matrix, message: str) -> None:
    if not matrices_close(a, b):
        raise AssertionError(message)


def run_self_tests() -> None:
    print("\n" + "=" * 80)
    print("SELF-TESTS")
    print("=" * 80)

    assert is_unitary(H_GATE)
    assert is_unitary(X_GATE)
    assert is_unitary(Y_GATE)
    assert is_unitary(Z_GATE)
    assert is_unitary(s_gate())
    assert is_unitary(t_gate())

    assert_matrix_identity(
        matrix_power(s_gate(), 2),
        Z_GATE,
        "S^2 must equal Z.",
    )

    assert_matrix_identity(
        matrix_power(t_gate(), 2),
        s_gate(),
        "T^2 must equal S.",
    )

    assert_matrix_identity(
        matrix_power(t_gate(), 4),
        Z_GATE,
        "T^4 must equal Z.",
    )

    assert_matrix_identity(
        matrix_power(t_gate(), 8),
        I_GATE,
        "T^8 must equal I.",
    )

    assert_matrix_identity(
        matrix_multiply(s_gate(), s_dagger_gate()),
        I_GATE,
        "S S† must equal I.",
    )

    assert_matrix_identity(
        matrix_multiply(t_gate(), t_dagger_gate()),
        I_GATE,
        "T T† must equal I.",
    )

    assert global_phase_equivalent(
        [SQRT_2_INV, SQRT_2_INV],
        [1j * SQRT_2_INV, 1j * SQRT_2_INV],
    )

    p_zero, p_one = interference_experiment(math.pi)
    assert math.isclose(p_zero, 0.0, abs_tol=1e-9)
    assert math.isclose(p_one, 1.0, abs_tol=1e-9)

    controlled_t = controlled_phase_gate(math.pi / 4)
    assert is_unitary(controlled_t)

    print("All self-tests passed.")


# ============================================================================
# 24. MAIN STUDY PROGRAM
# ============================================================================

def main() -> None:
    print("=" * 80)
    print("PHASE GATES: S, T, AND PHASE OPERATIONS")
    print("=" * 80)
    print(
        "This executable study file demonstrates quantum phase operations "
        "from foundational concepts to multi-qubit applications."
    )

    demonstrate_basic_phase_gates()
    demonstrate_state_action()
    demonstrate_global_and_relative_phase()
    demonstrate_interference()
    demonstrate_gate_powers()
    demonstrate_controlled_phase()
    demonstrate_tensor_products()
    demonstrate_phase_kickback()
    demonstrate_qft_phase_rotations()
    demonstrate_gate_order()
    demonstrate_phase_accumulation()
    demonstrate_measurement()
    demonstrate_validation()
    demonstrate_advanced_circuit()
    compare_phase_gates()
    demonstrate_phase_to_probability_conversion()
    demonstrate_phase_oracle()
    discuss_production_considerations()
    performance_notes()
    run_self_tests()

    print("\n" + "=" * 80)
    print("END OF PHASE-GATE STUDY")
    print("=" * 80)


if __name__ == "__main__":
    main()
