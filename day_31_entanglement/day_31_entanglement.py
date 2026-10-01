"""
Entanglement: Bell States and Non-Classical Correlations

A self-contained executable learning model for two-qubit entanglement.
The program develops the subject from computational-basis states through
Bell-state construction, measurement statistics, density matrices,
partial traces, reduced-state entropy, local measurements, and a CHSH
Bell-test simulation.

The simulation uses exact amplitudes where possible and pseudo-random
sampling for repeated measurements. It does not claim to reproduce every
detail of a physical quantum experiment. Instead, it implements the
mathematical state-vector and measurement rules needed to study Bell
states and their non-classical correlations.

No external packages are required.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


EPSILON = 1e-10
BIT_LABELS = ("00", "01", "10", "11")


def complex_close(a: complex, b: complex, tolerance: float = EPSILON) -> bool:
    """Compare complex amplitudes while allowing floating-point error."""
    return abs(a - b) <= tolerance


def probability_from_amplitude(amplitude: complex) -> float:
    """Apply the Born rule: probability equals squared amplitude magnitude."""
    return amplitude.real * amplitude.real + amplitude.imag * amplitude.imag


def normalize_probabilities(probabilities: Sequence[float]) -> List[float]:
    """Validate and normalize a finite probability distribution."""
    if not probabilities:
        raise ValueError("A probability distribution cannot be empty.")

    if any(not math.isfinite(value) or value < -EPSILON for value in probabilities):
        raise ValueError("Probabilities must be finite and non-negative.")

    total = sum(probabilities)
    if total <= EPSILON:
        raise ValueError("The total probability must be positive.")

    return [max(0.0, value) / total for value in probabilities]


def sample_from_distribution(
    labels: Sequence[str],
    probabilities: Sequence[float],
    rng: random.Random,
) -> str:
    """Sample one measurement outcome according to the Born probabilities."""
    normalized = normalize_probabilities(probabilities)
    threshold = rng.random()
    cumulative = 0.0

    for label, probability in zip(labels, normalized):
        cumulative += probability
        if threshold < cumulative:
            return label

    # Protect against tiny floating-point accumulation errors.
    return labels[-1]


class QubitState:
    """
    Represent a pure two-qubit state in the computational basis.

    Basis ordering is:
        |00>, |01>, |10>, |11>

    A state is physically valid when the squared magnitudes of its
    amplitudes sum to one. Global phase is physically unobservable, but
    relative phase between components can change interference and
    correlations.
    """

    def __init__(self, amplitudes: Sequence[complex], name: str = "unnamed"):
        if len(amplitudes) != 4:
            raise ValueError("A two-qubit state requires exactly four amplitudes.")

        self.amplitudes = tuple(complex(value) for value in amplitudes)
        self.name = name
        self._validate()

    def _validate(self) -> None:
        norm = sum(probability_from_amplitude(a) for a in self.amplitudes)
        if not math.isclose(norm, 1.0, abs_tol=EPSILON):
            raise ValueError(
                f"State '{self.name}' is not normalized. Calculated norm: {norm}"
            )

    def probabilities(self) -> Dict[str, float]:
        """Return computational-basis probabilities from the Born rule."""
        return {
            label: probability_from_amplitude(amplitude)
            for label, amplitude in zip(BIT_LABELS, self.amplitudes)
        }

    def measurement_probabilities(self) -> List[float]:
        return list(self.probabilities().values())

    def sample_measurement(self, rng: random.Random | None = None) -> str:
        """Perform one computational-basis measurement."""
        rng = rng or random.Random()
        return sample_from_distribution(
            BIT_LABELS,
            self.measurement_probabilities(),
            rng,
        )

    def sample_many(
        self,
        shots: int,
        rng: random.Random | None = None,
    ) -> Dict[str, int]:
        """Repeat computational-basis measurements and count outcomes."""
        if shots <= 0:
            raise ValueError("The number of measurement shots must be positive.")

        rng = rng or random.Random()
        counts = {label: 0 for label in BIT_LABELS}

        for _ in range(shots):
            counts[self.sample_measurement(rng)] += 1

        return counts

    def describe(self) -> str:
        terms = []

        for label, amplitude in zip(BIT_LABELS, self.amplitudes):
            if abs(amplitude) <= EPSILON:
                continue

            magnitude = abs(amplitude)
            phase = math.atan2(amplitude.imag, amplitude.real)

            if math.isclose(phase, 0.0, abs_tol=EPSILON):
                coefficient = f"{magnitude:.4f}"
            elif math.isclose(phase, math.pi, abs_tol=EPSILON) or math.isclose(
                phase, -math.pi, abs_tol=EPSILON
            ):
                coefficient = f"-{magnitude:.4f}"
            else:
                coefficient = (
                    f"{magnitude:.4f}·exp(i·{phase:.4f})"
                )

            terms.append(f"{coefficient}|{label}>")

        return " + ".join(terms) if terms else "0"

    def apply_single_qubit_gate(
        self,
        gate: Sequence[Sequence[complex]],
        target: int,
    ) -> "QubitState":
        """
        Apply a 2x2 gate to one qubit.

        target=0 refers to the first/left qubit.
        target=1 refers to the second/right qubit.
        """
        if target not in (0, 1):
            raise ValueError("target must be 0 or 1.")

        if len(gate) != 2 or any(len(row) != 2 for row in gate):
            raise ValueError("A single-qubit gate must be a 2x2 matrix.")

        gate = [[complex(value) for value in row] for row in gate]
        output = [0j] * 4

        for input_index, amplitude in enumerate(self.amplitudes):
            first_bit = (input_index >> 1) & 1
            second_bit = input_index & 1
            input_bit = first_bit if target == 0 else second_bit

            for output_bit in (0, 1):
                if target == 0:
                    output_index = (output_bit << 1) | second_bit
                else:
                    output_index = (first_bit << 1) | output_bit

                output[output_index] += gate[output_bit][input_bit] * amplitude

        return QubitState(output, name=f"{self.name} after gate on q{target}")


def basis_state(bit_string: str) -> QubitState:
    """Construct one of the four computational-basis states."""
    if bit_string not in BIT_LABELS:
        raise ValueError("A two-qubit basis state must be 00, 01, 10, or 11.")

    amplitudes = [0j] * 4
    amplitudes[BIT_LABELS.index(bit_string)] = 1 + 0j
    return QubitState(amplitudes, name=f"|{bit_string}>")


def bell_states() -> Dict[str, QubitState]:
    """
    Construct the four maximally entangled Bell states.

    The relative plus/minus signs are physical relative phases and affect
    correlations in different measurement bases.
    """
    inverse_sqrt_two = 1 / math.sqrt(2)

    return {
        "Phi+": QubitState(
            [inverse_sqrt_two, 0, 0, inverse_sqrt_two],
            "|Phi+> = (|00> + |11>)/sqrt(2)",
        ),
        "Phi-": QubitState(
            [inverse_sqrt_two, 0, 0, -inverse_sqrt_two],
            "|Phi-> = (|00> - |11>)/sqrt(2)",
        ),
        "Psi+": QubitState(
            [0, inverse_sqrt_two, inverse_sqrt_two, 0],
            "|Psi+> = (|01> + |10>)/sqrt(2)",
        ),
        "Psi-": QubitState(
            [0, inverse_sqrt_two, -inverse_sqrt_two, 0],
            "|Psi-> = (|01> - |10>)/sqrt(2)",
        ),
    }


def hadamard() -> List[List[complex]]:
    value = 1 / math.sqrt(2)
    return [[value, value], [value, -value]]


def pauli_x() -> List[List[complex]]:
    return [[0, 1], [1, 0]]


def pauli_y() -> List[List[complex]]:
    return [[0, -1j], [1j, 0]]


def pauli_z() -> List[List[complex]]:
    return [[1, 0], [0, -1]]


def matrix_multiply(
    left: Sequence[Sequence[complex]],
    right: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    """Small matrix multiplication utility used for observable calculations."""
    if len(left[0]) != len(right):
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        [
            sum(left[i][k] * right[k][j] for k in range(len(right)))
            for j in range(len(right[0]))
        ]
        for i in range(len(left))
    ]


def conjugate_transpose(
    matrix: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    return [
        [matrix[row][column].conjugate() for row in range(len(matrix))]
        for column in range(len(matrix[0]))
    ]


def matrix_vector_multiply(
    matrix: Sequence[Sequence[complex]],
    vector: Sequence[complex],
) -> List[complex]:
    return [
        sum(matrix[row][column] * vector[column] for column in range(len(vector)))
        for row in range(len(matrix))
    ]


def kron(
    left: Sequence[Sequence[complex]],
    right: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    """Kronecker product for constructing two-qubit observables."""
    result = []

    for left_row in left:
        for right_row in right:
            row = []
            for left_value in left_row:
                for right_value in right_row:
                    row.append(left_value * right_value)
            result.append(row)

    return result


def statevector_inner_product(
    left: Sequence[complex],
    right: Sequence[complex],
) -> complex:
    return sum(a.conjugate() * b for a, b in zip(left, right))


def expectation_value(
    state: QubitState,
    observable: Sequence[Sequence[complex]],
) -> float:
    """
    Compute <psi|O|psi> for a Hermitian observable.

    The result should be real for a valid Hermitian observable. A small
    imaginary residual can arise from floating-point arithmetic.
    """
    if len(observable) != 4 or any(len(row) != 4 for row in observable):
        raise ValueError("A two-qubit observable must be a 4x4 matrix.")

    transformed = matrix_vector_multiply(observable, state.amplitudes)
    result = statevector_inner_product(state.amplitudes, transformed)

    if abs(result.imag) > 1e-8:
        raise ValueError("The supplied observable produced a non-real expectation.")

    return result.real


def tensor_observable(
    first: Sequence[Sequence[complex]],
    second: Sequence[Sequence[complex]],
) -> List[List[complex]]:
    return kron(first, second)


def bell_correlation_table(state: QubitState) -> Dict[str, float]:
    """
    Measure correlations of the form <sigma_i tensor sigma_i>.

    For Bell states, these three values identify characteristic
    non-classical correlation patterns.
    """
    observables = {
        "XX": tensor_observable(pauli_x(), pauli_x()),
        "YY": tensor_observable(pauli_y(), pauli_y()),
        "ZZ": tensor_observable(pauli_z(), pauli_z()),
    }

    return {
        label: expectation_value(state, observable)
        for label, observable in observables.items()
    }


def partial_trace_first_qubit(
    state: QubitState,
) -> List[List[complex]]:
    """
    Compute the reduced density matrix of the second qubit.

    For a pure state |psi> with amplitudes a_ij, the reduced matrix is
    rho_B[j,k] = sum_i a_ij * conjugate(a_ik).

    A Bell state therefore gives I/2 locally, despite the joint state being
    pure and perfectly correlated in suitable bases.
    """
    amplitudes = state.amplitudes
    rho = [[0j, 0j], [0j, 0j]]

    for first_bit in (0, 1):
        for second_row in (0, 1):
            row_index = (first_bit << 1) | second_row

            for second_column in (0, 1):
                column_index = (first_bit << 1) | second_column
                rho[second_row][second_column] += (
                    amplitudes[row_index] * amplitudes[column_index].conjugate()
                )

    return rho


def eigenvalues_2x2(matrix: Sequence[Sequence[complex]]) -> Tuple[float, float]:
    """Compute real eigenvalues for a 2x2 Hermitian density matrix."""
    a = matrix[0][0].real
    d = matrix[1][1].real
    b = matrix[0][1]

    center = (a + d) / 2
    radius = math.sqrt(max(0.0, ((a - d) / 2) ** 2 + abs(b) ** 2))

    return center + radius, center - radius


def von_neumann_entropy_qubit(rho: Sequence[Sequence[complex]]) -> float:
    """
    Calculate S(rho) = -Tr(rho log2 rho).

    Zero eigenvalues contribute zero by continuity. A Bell state's reduced
    density matrix has eigenvalues 1/2 and 1/2, giving one bit of entropy.
    """
    eigenvalues = eigenvalues_2x2(rho)
    entropy = 0.0

    for eigenvalue in eigenvalues:
        if eigenvalue > EPSILON:
            entropy -= eigenvalue * math.log2(eigenvalue)

    return entropy


def rotate_basis_observable(
    theta_degrees: float,
    phi_degrees: float = 0.0,
) -> List[List[complex]]:
    """
    Construct the qubit spin observable n·sigma.

    n = (sin(theta) cos(phi), sin(theta) sin(phi), cos(theta)).

    This lets the CHSH experiment use measurement axes rather than only
    computational-basis Z measurements.
    """
    theta = math.radians(theta_degrees)
    phi = math.radians(phi_degrees)

    nx = math.sin(theta) * math.cos(phi)
    ny = math.sin(theta) * math.sin(phi)
    nz = math.cos(theta)

    return [
        [nz, nx - 1j * ny],
        [nx + 1j * ny, -nz],
    ]


def chsh_value(
    state: QubitState,
    a: Sequence[Sequence[complex]],
    a_prime: Sequence[Sequence[complex]],
    b: Sequence[Sequence[complex]],
    b_prime: Sequence[Sequence[complex]],
) -> float:
    """
    Calculate S = E(a,b) + E(a,b') + E(a',b) - E(a',b').

    Local hidden-variable theories satisfying the standard CHSH assumptions
    obey |S| <= 2. Quantum mechanics permits values up to 2*sqrt(2).
    """
    e_ab = expectation_value(state, kron(a, b))
    e_ab_prime = expectation_value(state, kron(a, b_prime))
    e_a_prime_b = expectation_value(state, kron(a_prime, b))
    e_a_prime_b_prime = expectation_value(state, kron(a_prime, b_prime))

    return e_ab + e_ab_prime + e_a_prime_b - e_a_prime_b_prime


def binary_observable_outcome(
    state: QubitState,
    observable: Sequence[Sequence[complex]],
    rng: random.Random,
) -> int:
    """
    Sample an abstract ±1 outcome from a single two-qubit expectation.

    This helper is intentionally used for independent product observables
    in a simplified Bell-test Monte Carlo model. It is not a substitute for
    a full quantum measurement circuit.
    """
    expectation = expectation_value(state, observable)
    expectation = max(-1.0, min(1.0, expectation))

    probability_plus = (1.0 + expectation) / 2.0
    return 1 if rng.random() < probability_plus else -1


def simulate_correlation(
    state: QubitState,
    first_observable: Sequence[Sequence[complex]],
    second_observable: Sequence[Sequence[complex]],
    shots: int,
    rng: random.Random,
) -> float:
    """
    Estimate E(A,B) with a joint ±1 correlation distribution.

    For a maximally entangled Phi+ state and spin observables restricted
    to the x-z plane, the ideal correlation is n_A dot n_B. A pair of
    outcomes with product expectation E can be sampled by first choosing
    A uniformly and then choosing B so that E[A*B] equals the target.
    """
    if shots <= 0:
        raise ValueError("shots must be positive.")

    joint_observable = kron(first_observable, second_observable)
    target_correlation = expectation_value(state, joint_observable)

    products = 0

    for _ in range(shots):
        first_outcome = 1 if rng.random() < 0.5 else -1

        probability_same = (1.0 + target_correlation) / 2.0
        same = rng.random() < probability_same

        second_outcome = (
            first_outcome if same else -first_outcome
        )

        products += first_outcome * second_outcome

    return products / shots


def simulate_chsh_experiment(
    state: QubitState,
    axes: Dict[str, Sequence[Sequence[complex]]],
    shots_per_setting: int,
    rng: random.Random,
) -> Tuple[Dict[str, float], float]:
    """Estimate the four CHSH correlation terms from finite samples."""
    correlations = {}

    settings = {
        "E(a,b)": ("a", "b"),
        "E(a,b')": ("a", "b'"),
        "E(a',b)": ("a'", "b"),
        "E(a',b')": ("a'", "b'"),
    }

    for label, (first_key, second_key) in settings.items():
        correlations[label] = simulate_correlation(
            state,
            axes[first_key],
            axes[second_key],
            shots_per_setting,
            rng,
        )

    value = (
        correlations["E(a,b)"]
        + correlations["E(a,b')"]
        + correlations["E(a',b)"]
        - correlations["E(a',b')"]
    )

    return correlations, value


def print_probability_table(state: QubitState) -> None:
    print(f"\nState: {state.name}")
    print(f"Vector: {state.describe()}")
    for label, probability in state.probabilities().items():
        print(f"  P({label}) = {probability:.6f}")


def demonstrate_computational_basis() -> None:
    print("=== Computational-basis foundation ===")

    state = basis_state("00")
    print_probability_table(state)

    hadamard_state = state.apply_single_qubit_gate(hadamard(), target=0)
    print_probability_table(hadamard_state)

    print(
        "\nThe Hadamard gate creates equal amplitudes for |00> and |10>. "
        "A later two-qubit operation can turn this superposition into an "
        "entangled state."
    )


def demonstrate_bell_states() -> None:
    print("\n=== Bell states ===")

    for name, state in bell_states().items():
        print_probability_table(state)

        correlation = bell_correlation_table(state)
        print("  Pauli correlations:")
        for observable, value in correlation.items():
            print(f"    <{observable}> = {value:+.3f}")


def demonstrate_entanglement_vs_product_state() -> None:
    print("\n=== Product state versus entangled state ===")

    product = QubitState(
        [0.5, 0.5, 0.5, 0.5],
        "(|0> + |1>)/sqrt(2) tensor (|0> + |1>)/sqrt(2)",
    )

    phi_plus = bell_states()["Phi+"]

    for state in (product, phi_plus):
        rho_b = partial_trace_first_qubit(state)
        entropy = von_neumann_entropy_qubit(rho_b)

        print(f"\n{state.name}")
        print("Reduced density matrix of qubit B:")
        for row in rho_b:
            print("  ", " ".join(f"{value.real:+.4f}" for value in row))

        print(f"Reduced-state entropy S(B) = {entropy:.6f} bits")

    print(
        "\nThe product state has a pure reduced state and zero entropy. "
        "The Bell state's reduced state is maximally mixed with entropy "
        "one bit, which is a signature of bipartite entanglement for this "
        "pure two-qubit state."
    )


def demonstrate_measurement_sampling() -> None:
    print("\n=== Bell-state measurement sampling ===")

    rng = random.Random(20261001)
    state = bell_states()["Phi+"]

    counts = state.sample_many(10_000, rng)

    print("Expected computational-basis probabilities for Phi+:")
    print("  P(00) = 0.5")
    print("  P(11) = 0.5")
    print("  P(01) = 0")
    print("  P(10) = 0")

    print("\n10,000 simulated measurements:")
    for label in BIT_LABELS:
        print(f"  {label}: {counts[label]}")

    print(
        "\nThe individual result is random, but the two measured bits agree. "
        "That distinction between local randomness and joint correlation is "
        "central to Bell-state behavior."
    )


def demonstrate_local_measurement_limit() -> None:
    print("\n=== Local statistics do not reveal the Bell-state identity ===")

    states = bell_states()

    for name, state in states.items():
        rho_b = partial_trace_first_qubit(state)
        print(f"{name}: reduced probabilities =", [
            round(rho_b[0][0].real, 3),
            round(rho_b[1][1].real, 3),
        ])

    print(
        "\nEvery Bell state has the same maximally mixed single-qubit "
        "statistics in the computational basis. Their differences appear "
        "in joint correlations and in correlations measured along other axes."
    )


def demonstrate_chsh() -> None:
    print("\n=== CHSH Bell-test simulation ===")

    phi_plus = bell_states()["Phi+"]

    # These x-z plane axes are chosen to obtain the quantum maximum for
    # Phi+ under the CHSH sign convention used here.
    axes = {
        "a": rotate_basis_observable(0),
        "a'": rotate_basis_observable(90),
        "b": rotate_basis_observable(45),
        "b'": rotate_basis_observable(-45),
    }

    exact_value = chsh_value(
        phi_plus,
        axes["a"],
        axes["a'"],
        axes["b"],
        axes["b'"],
    )

    rng = random.Random(424242)
    estimated_correlations, estimated_value = simulate_chsh_experiment(
        phi_plus,
        axes,
        shots_per_setting=20_000,
        rng=rng,
    )

    print("Exact quantum correlations:")
    for label, (first, second) in {
        "E(a,b)": ("a", "b"),
        "E(a,b')": ("a", "b'"),
        "E(a',b)": ("a'", "b"),
        "E(a',b')": ("a'", "b'"),
    }.items():
        exact = expectation_value(phi_plus, kron(axes[first], axes[second]))
        print(f"  {label} = {exact:+.6f}")

    print(f"Exact CHSH S = {exact_value:+.6f}")
    print("\nFinite-shot estimates:")
    for label, value in estimated_correlations.items():
        print(f"  {label} = {value:+.6f}")
    print(f"Estimated CHSH S = {estimated_value:+.6f}")

    print("\nReference bounds:")
    print("  Classical CHSH bound: |S| <= 2")
    print(f"  Quantum Tsirelson bound: |S| <= {2 * math.sqrt(2):.6f}")

    if abs(exact_value) > 2.0:
        print(
            "\nThe selected Bell state and measurement axes produce a "
            "correlation value outside the classical CHSH bound."
        )


def demonstrate_phase_difference() -> None:
    print("\n=== Relative phase changes correlations ===")

    phi_plus = bell_states()["Phi+"]
    phi_minus = bell_states()["Phi-"]

    print("Computational-basis probabilities:")
    for state in (phi_plus, phi_minus):
        print(f"  {state.name}: {state.probabilities()}")

    print("\nXX, YY, and ZZ correlations:")
    for state in (phi_plus, phi_minus):
        print(f"  {state.name}: {bell_correlation_table(state)}")

    print(
        "\nPhi+ and Phi- have identical computational-basis probabilities. "
        "Their relative phase differs, so measurements involving a different "
        "basis can distinguish their correlation structure."
    )


def demonstrate_edge_cases() -> None:
    print("\n=== Validation and edge cases ===")

    cases = [
        ("wrong amplitude count", lambda: QubitState([1, 0, 0], "invalid")),
        (
            "unnormalized state",
            lambda: QubitState([1, 1, 0, 0], "invalid"),
        ),
        (
            "invalid basis label",
            lambda: basis_state("22"),
        ),
        (
            "invalid shot count",
            lambda: bell_states()["Phi+"].sample_many(0),
        ),
        (
            "invalid gate target",
            lambda: bell_states()["Phi+"].apply_single_qubit_gate(
                hadamard(), 2
            ),
        ),
    ]

    for label, operation in cases:
        try:
            operation()
        except ValueError as error:
            print(f"{label}: correctly rejected -> {error}")

    print(
        "\nValidation matters because a quantum state must remain normalized, "
        "matrix dimensions must match the operation, and sampling requires "
        "a meaningful positive number of trials."
    )


def main() -> None:
    print("Entanglement: Bell States and Non-Classical Correlations")
    print("=" * 58)

    demonstrate_computational_basis()
    demonstrate_bell_states()
    demonstrate_entanglement_vs_product_state()
    demonstrate_measurement_sampling()
    demonstrate_local_measurement_limit()
    demonstrate_phase_difference()
    demonstrate_chsh()
    demonstrate_edge_cases()

    print("\n=== Completed ===")
    print(
        "The demonstrations connect state vectors, Bell-state correlations, "
        "reduced states, entropy, measurement randomness, and CHSH violation."
    )


if __name__ == "__main__":
    main()
