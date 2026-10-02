"""
Bell States: Generate and Measure Bell Pairs
============================================

A self-contained learning and simulation program covering:

- The four Bell states
- Computational-basis state representation
- Single-qubit gates
- Hadamard and Pauli-X/Z operations
- Controlled-NOT
- Bell-pair generation circuits
- Measurement in the computational basis
- Measurement in the X basis
- Correlation analysis
- Bell-state identification through measurements
- State-vector simulation
- Sampling and empirical probabilities
- Noise models
- Density-matrix representation
- Partial measurement and collapse
- Reduced states and entanglement
- CHSH-style correlation experiments
- Validation and reproducible experiments

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from random import Random
from typing import Dict, Iterable, List, Sequence, Tuple


Complex = complex
StateVector = List[Complex]
Matrix2 = List[List[Complex]]
Matrix4 = List[List[Complex]]


# ---------------------------------------------------------------------------
# Basic linear-algebra utilities
# ---------------------------------------------------------------------------

def almost_equal(a: complex, b: complex, tolerance: float = 1e-10) -> bool:
    """Compare two complex amplitudes with a numerical tolerance."""
    return abs(a - b) <= tolerance


def vector_norm(state: StateVector) -> float:
    """Return the Euclidean norm of a state vector."""
    return sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def normalize_state(state: StateVector) -> StateVector:
    """Normalize a non-zero quantum state vector."""
    norm = vector_norm(state)
    if norm == 0:
        raise ValueError("A quantum state cannot be normalized because its norm is zero.")
    return [amplitude / norm for amplitude in state]


def normalize_probability_distribution(
    probabilities: Dict[str, float],
) -> Dict[str, float]:
    """Normalize non-negative probabilities and reject invalid values."""
    if not probabilities:
        raise ValueError("The probability distribution cannot be empty.")

    if any(value < 0 for value in probabilities.values()):
        raise ValueError("Probabilities cannot be negative.")

    total = sum(probabilities.values())
    if total <= 0:
        raise ValueError("The probability total must be positive.")

    return {key: value / total for key, value in probabilities.items()}


def format_complex(value: complex, precision: int = 4) -> str:
    """Format complex amplitudes compactly for educational output."""
    real = 0.0 if abs(value.real) < 10 ** (-precision) else value.real
    imaginary = 0.0 if abs(value.imag) < 10 ** (-precision) else value.imag

    if imaginary == 0:
        return f"{real:.{precision}f}"

    if real == 0:
        return f"{imaginary:.{precision}f}i"

    sign = "+" if imaginary >= 0 else "-"
    return f"{real:.{precision}f} {sign} {abs(imaginary):.{precision}f}i"


def format_state(state: StateVector) -> str:
    """Render a two-qubit state vector in ket notation."""
    basis = ["|00>", "|01>", "|10>", "|11>"]
    terms = []

    for amplitude, label in zip(state, basis):
        if abs(amplitude) > 1e-10:
            terms.append(f"({format_complex(amplitude)}){label}")

    return " + ".join(terms) if terms else "0"


def matrix_multiply(a: Sequence[Sequence[complex]],
                    b: Sequence[Sequence[complex]]) -> List[List[complex]]:
    """Multiply compatible matrices using ordinary complex arithmetic."""
    if not a or not b:
        raise ValueError("Matrices must not be empty.")

    if len(a[0]) != len(b):
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        [
            sum(a[row][k] * b[k][column] for k in range(len(b)))
            for column in range(len(b[0]))
        ]
        for row in range(len(a))
    ]


def matrix_vector_multiply(
    matrix: Sequence[Sequence[complex]],
    vector: Sequence[complex],
) -> StateVector:
    """Apply a matrix to a vector."""
    if len(matrix[0]) != len(vector):
        raise ValueError("Matrix and vector dimensions are incompatible.")

    return [
        sum(matrix[row][column] * vector[column] for column in range(len(vector)))
        for row in range(len(matrix))
    ]


# ---------------------------------------------------------------------------
# Quantum gates
# ---------------------------------------------------------------------------

SQRT_HALF = 1 / sqrt(2)

I: Matrix2 = [
    [1, 0],
    [0, 1],
]

X: Matrix2 = [
    [0, 1],
    [1, 0],
]

Y: Matrix2 = [
    [0, -1j],
    [1j, 0],
]

Z: Matrix2 = [
    [1, 0],
    [0, -1],
]

H: Matrix2 = [
    [SQRT_HALF, SQRT_HALF],
    [SQRT_HALF, -SQRT_HALF],
]


def kron(a: Sequence[Sequence[complex]],
         b: Sequence[Sequence[complex]]) -> List[List[complex]]:
    """Compute the Kronecker product used to build multi-qubit operators."""
    result = []

    for a_row in a:
        for b_row in b:
            result.append([
                a_row_index * b_column_index
                for a_row_index in a_row
                for b_column_index in b_row
            ])

    return result


def tensor_product(a: Sequence[complex],
                   b: Sequence[complex]) -> StateVector:
    """Compute a tensor product of two state vectors."""
    return [
        a_value * b_value
        for a_value in a
        for b_value in b
    ]


def cnot_matrix() -> Matrix4:
    """
    Return the two-qubit CNOT matrix.

    Basis ordering:
        |00>, |01>, |10>, |11>

    The first qubit is the control and the second is the target.
    """
    return [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ]


CNOT = cnot_matrix()


def apply_single_qubit_gate(
    state: StateVector,
    gate: Matrix2,
    qubit: int,
) -> StateVector:
    """
    Apply a 2x2 gate to one qubit of a two-qubit state.

    Qubit numbering follows the displayed basis:
        qubit 0 = first/left bit
        qubit 1 = second/right bit
    """
    if len(state) != 4:
        raise ValueError("This educational simulator expects exactly two qubits.")

    if qubit not in (0, 1):
        raise ValueError("Qubit must be 0 or 1.")

    result = [0j] * 4

    for index in range(4):
        bit = (index >> (1 - qubit)) & 1

        for output_bit in (0, 1):
            source_index = index
            if output_bit != bit:
                source_index ^= 1 << (1 - qubit)

            result[source_index] += gate[output_bit][bit] * state[index]

    return normalize_state(result)


def apply_two_qubit_gate(
    state: StateVector,
    gate: Matrix4,
) -> StateVector:
    """Apply a complete 4x4 two-qubit gate."""
    if len(state) != 4:
        raise ValueError("A two-qubit gate requires a four-element state vector.")

    result = matrix_vector_multiply(gate, state)
    return normalize_state(result)


# ---------------------------------------------------------------------------
# Bell-state definitions
# ---------------------------------------------------------------------------

BELL_STATES: Dict[str, StateVector] = {
    "Phi+": [
        SQRT_HALF,
        0,
        0,
        SQRT_HALF,
    ],
    "Phi-": [
        SQRT_HALF,
        0,
        0,
        -SQRT_HALF,
    ],
    "Psi+": [
        0,
        SQRT_HALF,
        SQRT_HALF,
        0,
    ],
    "Psi-": [
        0,
        SQRT_HALF,
        -SQRT_HALF,
        0,
    ],
}


@dataclass(frozen=True)
class BellStateDefinition:
    """Metadata describing one of the four maximally entangled Bell states."""

    name: str
    expression: str
    same_z_result: bool
    same_x_result: bool


BELL_METADATA = [
    BellStateDefinition(
        "Phi+",
        "(|00> + |11>)/sqrt(2)",
        True,
        True,
    ),
    BellStateDefinition(
        "Phi-",
        "(|00> - |11>)/sqrt(2)",
        True,
        False,
    ),
    BellStateDefinition(
        "Psi+",
        "(|01> + |10>)/sqrt(2)",
        False,
        True,
    ),
    BellStateDefinition(
        "Psi-",
        "(|01> - |10>)/sqrt(2)",
        False,
        False,
    ),
]


def zero_state() -> StateVector:
    """Return the |00> computational-basis state."""
    return [1 + 0j, 0j, 0j, 0j]


def generate_bell_pair(bell_name: str = "Phi+") -> StateVector:
    """
    Generate a Bell state from |00> using a Bell-state preparation circuit.

    The circuit starts with:
        |00>

    H on qubit 0:
        (|00> + |10>)/sqrt(2)

    CNOT:
        (|00> + |11>)/sqrt(2)

    Local Pauli operations then transform Phi+ into the other Bell states.
    """
    if bell_name not in BELL_STATES:
        raise ValueError(
            f"Unknown Bell state '{bell_name}'. "
            f"Choose from {', '.join(BELL_STATES)}."
        )

    state = zero_state()
    state = apply_single_qubit_gate(state, H, 0)
    state = apply_two_qubit_gate(state, CNOT)

    if bell_name == "Phi+":
        return state

    if bell_name == "Phi-":
        return apply_single_qubit_gate(state, Z, 0)

    if bell_name == "Psi+":
        return apply_single_qubit_gate(state, X, 1)

    # Applying X and Z to one qubit converts Phi+ into Psi-.
    state = apply_single_qubit_gate(state, X, 1)
    state = apply_single_qubit_gate(state, Z, 0)
    return state


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def computational_probabilities(state: StateVector) -> Dict[str, float]:
    """Calculate computational-basis measurement probabilities."""
    probabilities = {
        basis: abs(amplitude) ** 2
        for basis, amplitude in zip(
            ("00", "01", "10", "11"),
            state,
        )
    }

    return normalize_probability_distribution(probabilities)


def sample_distribution(
    probabilities: Dict[str, float],
    shots: int,
    rng: Random,
) -> Dict[str, int]:
    """
    Sample measurement outcomes.

    A cumulative distribution is used instead of relying on an external
    numerical package, making the simulator completely self-contained.
    """
    if shots <= 0:
        raise ValueError("The number of shots must be positive.")

    probabilities = normalize_probability_distribution(probabilities)

    cumulative: List[Tuple[float, str]] = []
    running_total = 0.0

    for outcome, probability in probabilities.items():
        running_total += probability
        cumulative.append((running_total, outcome))

    counts = {outcome: 0 for outcome in probabilities}

    for _ in range(shots):
        random_value = rng.random()

        for threshold, outcome in cumulative:
            if random_value <= threshold:
                counts[outcome] += 1
                break

    return counts


def measure_computational_basis(
    state: StateVector,
    rng: Random | None = None,
) -> Tuple[str, StateVector]:
    """
    Perform one projective measurement in the computational basis.

    The returned state is the post-measurement collapsed state.
    """
    rng = rng or Random()

    probabilities = computational_probabilities(state)
    outcome = sample_distribution(probabilities, 1, rng)

    measured = next(key for key, value in outcome.items() if value == 1)

    collapsed = [0j] * 4
    index = int(measured, 2)
    collapsed[index] = 1 + 0j

    return measured, collapsed


def apply_x_basis_measurement_basis_change(
    state: StateVector,
) -> StateVector:
    """
    Transform an X-basis measurement into a computational-basis measurement.

    Measuring in the X basis is equivalent to applying H first and then
    measuring in the computational basis.
    """
    state = apply_single_qubit_gate(state, H, 0)
    state = apply_single_qubit_gate(state, H, 1)
    return state


def measure_x_basis(
    state: StateVector,
    rng: Random | None = None,
) -> Tuple[str, StateVector]:
    """
    Measure both qubits in the X basis.

    The two-character result uses:
        0 = |+>
        1 = |->

    Internally H maps these states to computational |0> and |1>.
    """
    transformed = apply_x_basis_measurement_basis_change(state)
    outcome, _ = measure_computational_basis(transformed, rng)

    # The physical post-measurement state is expressed back in the original
    # basis by reversing the basis-change transformation.
    collapsed_transformed = [0j] * 4
    collapsed_transformed[int(outcome, 2)] = 1 + 0j

    collapsed_original = apply_single_qubit_gate(
        collapsed_transformed, H, 0
    )
    collapsed_original = apply_single_qubit_gate(
        collapsed_original, H, 1
    )

    return outcome, collapsed_original


def sample_measurements(
    state: StateVector,
    shots: int,
    basis: str = "Z",
    seed: int = 7,
) -> Dict[str, int]:
    """
    Repeatedly measure a freshly prepared copy of a Bell state.

    Each shot uses a new copy because a real quantum measurement collapses
    the state and cannot be repeated on the same pair to obtain independent
    samples.
    """
    if basis.upper() not in {"Z", "X"}:
        raise ValueError("Basis must be 'Z' or 'X'.")

    rng = Random(seed)

    if basis.upper() == "Z":
        probabilities = computational_probabilities(state)
    else:
        transformed = apply_x_basis_measurement_basis_change(state)
        probabilities = computational_probabilities(transformed)

    return sample_distribution(probabilities, shots, rng)


# ---------------------------------------------------------------------------
# Correlation analysis
# ---------------------------------------------------------------------------

def parity_correlation(counts: Dict[str, int]) -> float:
    """
    Calculate a correlation value from binary outcomes.

    Equal bits contribute +1.
    Different bits contribute -1.
    """
    total = sum(counts.values())
    if total == 0:
        raise ValueError("Cannot calculate correlation from zero measurements.")

    score = 0

    for outcome, count in counts.items():
        if outcome[0] == outcome[1]:
            score += count
        else:
            score -= count

    return score / total


def identify_bell_state(
    z_counts: Dict[str, int],
    x_counts: Dict[str, int],
) -> str:
    """
    Identify a Bell state from ideal Z- and X-basis correlation signs.

    The pair of correlation signs distinguishes the four Bell states:
        Phi+ : (+, +)
        Phi- : (+, -)
        Psi+ : (-, +)
        Psi- : (-, -)

    This is an idealized classification procedure. Finite-shot noise or
    physical noise can make the empirical correlations imperfect.
    """
    z_correlation = parity_correlation(z_counts)
    x_correlation = parity_correlation(x_counts)

    z_same = z_correlation >= 0
    x_same = x_correlation >= 0

    mapping = {
        (True, True): "Phi+",
        (True, False): "Phi-",
        (False, True): "Psi+",
        (False, False): "Psi-",
    }

    return mapping[(z_same, x_same)]


# ---------------------------------------------------------------------------
# Entanglement and reduced-state calculations
# ---------------------------------------------------------------------------

def density_matrix(state: StateVector) -> List[List[complex]]:
    """Construct rho = |psi><psi| from a pure state vector."""
    return [
        [
            state[row] * state[column].conjugate()
            for column in range(len(state))
        ]
        for row in range(len(state))
    ]


def partial_trace_first_qubit(
    rho: Sequence[Sequence[complex]],
) -> Matrix2:
    """
    Trace out the first qubit from a two-qubit density matrix.

    For Bell states the remaining one-qubit density matrix is I/2.
    """
    if len(rho) != 4 or any(len(row) != 4 for row in rho):
        raise ValueError("A 4x4 density matrix is required.")

    reduced = [[0j, 0j], [0j, 0j]]

    for second_row in range(2):
        for second_column in range(2):
            reduced[second_row][second_column] = (
                rho[second_row][second_column]
                + rho[second_row + 2][second_column + 2]
            )

    return reduced


def matrix_trace(matrix: Sequence[Sequence[complex]]) -> complex:
    """Return the trace of a square matrix."""
    return sum(matrix[index][index] for index in range(len(matrix)))


def purity(matrix: Sequence[Sequence[complex]]) -> float:
    """
    Calculate Tr(rho^2), a useful mixed-state diagnostic.

    A pure single-qubit state has purity 1.
    A maximally mixed qubit has purity 1/2.
    """
    squared = matrix_multiply(matrix, matrix)
    return float(matrix_trace(squared).real)


def determinant_2x2(matrix: Matrix2) -> complex:
    """Calculate the determinant of a 2x2 matrix."""
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def pure_two_qubit_concurrence(state: StateVector) -> float:
    """
    Calculate concurrence for a pure two-qubit state.

    For amplitudes a,b,c,d:
        C = 2 |ad - bc|

    Bell states have C = 1.
    """
    a, b, c, d = state
    return min(1.0, 2.0 * abs(a * d - b * c))


# ---------------------------------------------------------------------------
# Simple noise models
# ---------------------------------------------------------------------------

def bit_flip_noise(
    state: StateVector,
    qubit: int,
    probability: float,
    rng: Random,
) -> StateVector:
    """
    Apply a classical stochastic bit-flip event to a state vector.

    This is a pedagogical stochastic channel. It is not a full density-matrix
    treatment of decoherence, but it is useful for observing measurement errors.
    """
    if not 0 <= probability <= 1:
        raise ValueError("Noise probability must be between 0 and 1.")

    if rng.random() < probability:
        return apply_single_qubit_gate(state, X, qubit)

    return state[:]


def noisy_measurement_experiment(
    bell_name: str,
    shots: int,
    bit_flip_probability: float,
    seed: int = 11,
) -> Dict[str, int]:
    """Generate Bell pairs and apply stochastic readout-like bit flips."""
    rng = Random(seed)
    counts = {outcome: 0 for outcome in ("00", "01", "10", "11")}

    for _ in range(shots):
        state = generate_bell_pair(bell_name)
        state = bit_flip_noise(state, 0, bit_flip_probability, rng)
        state = bit_flip_noise(state, 1, bit_flip_probability, rng)

        outcome, _ = measure_computational_basis(state, rng)
        counts[outcome] += 1

    return counts


# ---------------------------------------------------------------------------
# Bell-state experiments
# ---------------------------------------------------------------------------

def print_probability_table(state_name: str, state: StateVector) -> None:
    """Print computational-basis probabilities for one Bell state."""
    print(f"\n{state_name}")
    print(f"State: {format_state(state)}")

    probabilities = computational_probabilities(state)

    for outcome, probability in probabilities.items():
        print(f"  P({outcome}) = {probability:.4f}")


def demonstrate_bell_state_generation() -> None:
    """Show the common Bell-generation circuit and local transformations."""
    print("=" * 72)
    print("BELL-STATE GENERATION")
    print("=" * 72)

    print("\nStarting state:")
    print("  |00>")

    print("\nApply H to qubit 0:")
    state_after_h = apply_single_qubit_gate(zero_state(), H, 0)
    print(f"  {format_state(state_after_h)}")

    print("\nApply CNOT(control=q0, target=q1):")
    phi_plus = apply_two_qubit_gate(state_after_h, CNOT)
    print(f"  {format_state(phi_plus)}")

    print("\nTransform Phi+ with local Pauli gates:")
    for name in BELL_STATES:
        state = generate_bell_pair(name)
        print(f"  {name:5s}: {format_state(state)}")


def demonstrate_measurements(shots: int = 4000) -> None:
    """Compare Z-basis and X-basis correlations for every Bell state."""
    print("\n" + "=" * 72)
    print("BELL-PAIR MEASUREMENT")
    print("=" * 72)

    for name in BELL_STATES:
        state = generate_bell_pair(name)

        z_counts = sample_measurements(state, shots, "Z", seed=101)
        x_counts = sample_measurements(state, shots, "X", seed=202)

        print(f"\n{name}")
        print(f"  Z-basis counts: {z_counts}")
        print(f"  Z correlation:  {parity_correlation(z_counts):+.3f}")
        print(f"  X-basis counts: {x_counts}")
        print(f"  X correlation:  {parity_correlation(x_counts):+.3f}")
        print(f"  Identified as:  {identify_bell_state(z_counts, x_counts)}")


def demonstrate_single_measurement_collapse() -> None:
    """Show that measuring a Bell pair collapses it to a classical outcome."""
    print("\n" + "=" * 72)
    print("MEASUREMENT COLLAPSE")
    print("=" * 72)

    rng = Random(42)
    state = generate_bell_pair("Phi+")

    print("\nBefore measurement:")
    print(f"  {format_state(state)}")

    outcome, collapsed = measure_computational_basis(state, rng)

    print(f"\nMeasured outcome: |{outcome}>")
    print("Post-measurement state:")
    print(f"  {format_state(collapsed)}")

    print(
        "\nThe second qubit is correlated with the first because Phi+ "
        "contains only |00> and |11>."
    )


def demonstrate_entanglement() -> None:
    """Show why a Bell pair does not reduce to two independent pure states."""
    print("\n" + "=" * 72)
    print("ENTANGLEMENT AND REDUCED STATES")
    print("=" * 72)

    for name in BELL_STATES:
        state = generate_bell_pair(name)
        rho = density_matrix(state)
        reduced = partial_trace_first_qubit(rho)

        print(f"\n{name}")
        print(f"  concurrence: {pure_two_qubit_concurrence(state):.4f}")
        print(f"  reduced state of qubit 1:")
        for row in reduced:
            print("   ", [format_complex(value) for value in row])
        print(f"  reduced-state purity: {purity(reduced):.4f}")


def demonstrate_noise() -> None:
    """Show how stochastic bit flips reduce observed Bell correlations."""
    print("\n" + "=" * 72)
    print("NOISY BELL-PAIR MEASUREMENTS")
    print("=" * 72)

    shots = 5000

    for noise in (0.0, 0.01, 0.05, 0.15):
        counts = noisy_measurement_experiment(
            "Phi+",
            shots,
            noise,
            seed=900 + int(noise * 1000),
        )
        correlation = parity_correlation(counts)

        print(
            f"\nBit-flip probability={noise:.2%}"
            f"\n  counts={counts}"
            f"\n  correlation={correlation:+.3f}"
        )


# ---------------------------------------------------------------------------
# CHSH-style correlation experiment
# ---------------------------------------------------------------------------

def observable_for_angle(angle: float) -> Matrix2:
    """
    Build a qubit observable in the X-Z plane.

    A(theta) = cos(theta) Z + sin(theta) X

    Its eigenvalues are +1 and -1.
    """
    return [
        [
            cos(angle),
            sin(angle),
        ],
        [
            sin(angle),
            -cos(angle),
        ],
    ]


def expectation_value(
    state: StateVector,
    operator: Matrix4,
) -> float:
    """Calculate <psi|O|psi> for a normalized state."""
    transformed = matrix_vector_multiply(operator, state)
    value = sum(
        state[index].conjugate() * transformed[index]
        for index in range(len(state))
    )
    return value.real


def tensor_matrix(a: Matrix2, b: Matrix2) -> Matrix4:
    """Build a two-qubit operator from two one-qubit operators."""
    return kron(a, b)


def chsh_value(
    state: StateVector,
    alice_angles: Tuple[float, float],
    bob_angles: Tuple[float, float],
) -> float:
    """
    Calculate the CHSH expression for the supplied observables.

    The singlet state reaches the quantum maximum 2*sqrt(2) with suitable
    measurement directions. The other Bell states can also violate CHSH
    after choosing appropriate local measurement axes.
    """
    a0 = observable_for_angle(alice_angles[0])
    a1 = observable_for_angle(alice_angles[1])
    b0 = observable_for_angle(bob_angles[0])
    b1 = observable_for_angle(bob_angles[1])

    e00 = expectation_value(state, tensor_matrix(a0, b0))
    e01 = expectation_value(state, tensor_matrix(a0, b1))
    e10 = expectation_value(state, tensor_matrix(a1, b0))
    e11 = expectation_value(state, tensor_matrix(a1, b1))

    return e00 + e01 + e10 - e11


def demonstrate_chsh() -> None:
    """Demonstrate a Bell inequality violation for the singlet state."""
    print("\n" + "=" * 72)
    print("CHSH-STYLE CORRELATION")
    print("=" * 72)

    singlet = generate_bell_pair("Psi-")

    # These angles produce a maximal violation for the selected observable
    # convention, up to sign depending on the chosen CHSH expression.
    angles_a = (0.0, pi / 2)
    angles_b = (pi / 4, -pi / 4)

    value = chsh_value(singlet, angles_a, angles_b)

    print(f"\nPsi- CHSH value: {value:.6f}")
    print("Classical local-hidden-variable bound: |S| <= 2")
    print(f"Quantum magnitude for this configuration: {abs(value):.6f}")
    print(f"Tsirelson bound: 2*sqrt(2) = {2 * sqrt(2):.6f}")


# ---------------------------------------------------------------------------
# Validation and edge cases
# ---------------------------------------------------------------------------

def validate_bell_states() -> None:
    """Verify normalization, expected support, and entanglement."""
    for name, expected in BELL_STATES.items():
        generated = generate_bell_pair(name)

        if abs(vector_norm(generated) - 1.0) > 1e-10:
            raise AssertionError(f"{name} is not normalized.")

        # Global phase can make physically equivalent states differ by a phase.
        # Here the construction is expected to match the canonical definitions.
        for actual, target in zip(generated, expected):
            if not almost_equal(actual, target):
                raise AssertionError(
                    f"{name} does not match its canonical state."
                )

        if abs(pure_two_qubit_concurrence(generated) - 1.0) > 1e-10:
            raise AssertionError(f"{name} should have concurrence 1.")

    print("\nValidation: all four Bell states passed.")


def demonstrate_edge_cases() -> None:
    """Exercise validation rules that prevent misleading simulations."""
    print("\n" + "=" * 72)
    print("VALIDATION AND EDGE CASES")
    print("=" * 72)

    checks = [
        ("invalid Bell-state name", lambda: generate_bell_pair("Phi2")),
        ("zero shots", lambda: sample_measurements(
            generate_bell_pair("Phi+"), 0
        )),
        ("invalid basis", lambda: sample_measurements(
            generate_bell_pair("Phi+"), 100, "Y"
        )),
        ("negative noise probability", lambda: noisy_measurement_experiment(
            "Phi+", 10, -0.1
        )),
    ]

    for description, operation in checks:
        try:
            operation()
        except (ValueError, AssertionError) as exc:
            print(f"  {description}: correctly rejected ({exc})")
        else:
            print(f"  {description}: ERROR, invalid input was accepted")


def print_reference_table() -> None:
    """Print the defining measurement correlations of the Bell basis."""
    print("\n" + "=" * 72)
    print("BELL-STATE REFERENCE")
    print("=" * 72)

    print(
        "\nState    Z basis correlation    X basis correlation    Expression"
    )
    print("-" * 72)

    for metadata in BELL_METADATA:
        z = "same" if metadata.same_z_result else "opposite"
        x = "same" if metadata.same_x_result else "opposite"

        print(
            f"{metadata.name:<8}"
            f"{z:<23}"
            f"{x:<23}"
            f"{metadata.expression}"
        )


# ---------------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the complete Bell-state learning and simulation program."""
    print("BELL STATES: GENERATE AND MEASURE BELL PAIRS")
    print("=" * 72)
    print("Two-qubit state-vector simulator using only the Python standard library.")

    print_reference_table()
    demonstrate_bell_state_generation()

    print("\n" + "=" * 72)
    print("COMPUTATIONAL-BASIS PROBABILITIES")
    print("=" * 72)

    for name, state in BELL_STATES.items():
        print_probability_table(name, state)

    demonstrate_measurements(shots=4000)
    demonstrate_single_measurement_collapse()
    demonstrate_entanglement()
    demonstrate_noise()
    demonstrate_chsh()
    demonstrate_edge_cases()
    validate_bell_states()

    print("\n" + "=" * 72)
    print("END OF BELL-STATE SIMULATION")
    print("=" * 72)


if __name__ == "__main__":
    main()
