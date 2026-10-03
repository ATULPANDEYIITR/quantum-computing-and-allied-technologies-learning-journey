#!/usr/bin/env python3
"""
Bell States: Generate and Measure Bell Pairs

A self-contained quantum-state simulator for the four Bell states.

The program demonstrates:
- Two-qubit computational basis states
- Single-qubit Hadamard and Pauli gates
- Controlled-NOT entanglement
- Construction of all four Bell states
- Exact probability calculation
- Quantum measurement and state collapse
- Repeated measurement statistics
- Correlated measurements in matching bases
- Bell-state identification through measurement data
- Partial measurement and conditional state behavior
- Numerical normalization and validation
- A small density-matrix calculation for reduced states
- Practical simulation limitations

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt
from random import Random
from typing import Dict, Iterable, List, Sequence, Tuple


EPSILON = 1e-12

BasisState = Tuple[int, int]
ComplexState = Dict[BasisState, complex]


def format_complex(value: complex, precision: int = 4) -> str:
    """Format a complex amplitude compactly for educational output."""
    real = 0.0 if abs(value.real) < EPSILON else value.real
    imag = 0.0 if abs(value.imag) < EPSILON else value.imag

    if abs(imag) < EPSILON:
        return f"{real:.{precision}f}"

    if abs(real) < EPSILON:
        return f"{imag:.{precision}f}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.{precision}f} {sign} {abs(imag):.{precision}f}i"


def basis_label(state: BasisState) -> str:
    return f"|{state[0]}{state[1]}>"


def clean_state(state: ComplexState) -> ComplexState:
    """Remove numerically negligible amplitudes after gate operations."""
    return {
        basis: amplitude
        for basis, amplitude in state.items()
        if abs(amplitude) > EPSILON
    }


def normalize(state: ComplexState) -> ComplexState:
    """Normalize a quantum state so total probability is exactly one."""
    norm_squared = sum(abs(amplitude) ** 2 for amplitude in state.values())

    if norm_squared <= EPSILON:
        raise ValueError("Cannot normalize a zero quantum state.")

    factor = 1.0 / sqrt(norm_squared)
    normalized = {
        basis: amplitude * factor for basis, amplitude in state.items()
    }
    return clean_state(normalized)


def validate_normalized(state: ComplexState) -> None:
    """Reject invalid state vectors whose probabilities do not sum to one."""
    probability = sum(abs(amplitude) ** 2 for amplitude in state.values())

    if not isclose(probability, 1.0, abs_tol=1e-10):
        raise ValueError(
            f"Invalid quantum state: total probability is {probability:.12f}."
        )


def computational_state(first: int, second: int) -> ComplexState:
    """Create one of the four two-qubit computational basis states."""
    if first not in (0, 1) or second not in (0, 1):
        raise ValueError("Each computational-basis bit must be 0 or 1.")

    return {(first, second): 1.0 + 0.0j}


def add_states(*states: ComplexState) -> ComplexState:
    """Add state amplitudes, useful when constructing superpositions."""
    result: ComplexState = {}

    for state in states:
        for basis, amplitude in state.items():
            result[basis] = result.get(basis, 0.0j) + amplitude

    return clean_state(result)


def scale_state(state: ComplexState, factor: complex) -> ComplexState:
    return clean_state(
        {basis: amplitude * factor for basis, amplitude in state.items()}
    )


def apply_hadamard(state: ComplexState, qubit: int) -> ComplexState:
    """
    Apply H to one qubit.

    H|0> = (|0> + |1>) / sqrt(2)
    H|1> = (|0> - |1>) / sqrt(2)

    The transformation acts on amplitudes rather than classical bits.
    """
    if qubit not in (0, 1):
        raise ValueError("Qubit must be 0 or 1.")

    factor = 1.0 / sqrt(2.0)
    result: ComplexState = {}

    for (q0, q1), amplitude in state.items():
        bits = [q0, q1]
        current = bits[qubit]

        for new_value in (0, 1):
            new_bits = bits.copy()
            new_bits[qubit] = new_value

            phase = -1.0 if current == 1 and new_value == 1 else 1.0
            new_amplitude = amplitude * factor * phase

            basis = (new_bits[0], new_bits[1])
            result[basis] = result.get(basis, 0.0j) + new_amplitude

    return normalize(clean_state(result))


def apply_pauli_x(state: ComplexState, qubit: int) -> ComplexState:
    """Apply X, which exchanges |0> and |1> on the selected qubit."""
    if qubit not in (0, 1):
        raise ValueError("Qubit must be 0 or 1.")

    result: ComplexState = {}

    for (q0, q1), amplitude in state.items():
        bits = [q0, q1]
        bits[qubit] ^= 1
        basis = (bits[0], bits[1])
        result[basis] = result.get(basis, 0.0j) + amplitude

    return normalize(clean_state(result))


def apply_pauli_z(state: ComplexState, qubit: int) -> ComplexState:
    """
    Apply Z.

    Z|0> = |0>
    Z|1> = -|1>

    This changes phase without changing computational-basis probabilities.
    """
    if qubit not in (0, 1):
        raise ValueError("Qubit must be 0 or 1.")

    result: ComplexState = {}

    for basis, amplitude in state.items():
        phase = -1.0 if basis[qubit] == 1 else 1.0
        result[basis] = amplitude * phase

    return normalize(result)


def apply_cnot(
    state: ComplexState,
    control: int,
    target: int,
) -> ComplexState:
    """
    Apply CNOT.

    If the control qubit is |1>, the target bit flips.
    The operation is conditional and therefore cannot be represented
    as an ordinary independent transformation of each qubit.
    """
    if control not in (0, 1) or target not in (0, 1):
        raise ValueError("Control and target must be qubit 0 or 1.")
    if control == target:
        raise ValueError("Control and target must be different qubits.")

    result: ComplexState = {}

    for basis, amplitude in state.items():
        bits = list(basis)

        if bits[control] == 1:
            bits[target] ^= 1

        new_basis = (bits[0], bits[1])
        result[new_basis] = result.get(new_basis, 0.0j) + amplitude

    return normalize(clean_state(result))


def probabilities(state: ComplexState) -> Dict[BasisState, float]:
    """Return Born-rule probabilities for computational-basis outcomes."""
    validate_normalized(state)

    result = {
        basis: abs(amplitude) ** 2
        for basis, amplitude in state.items()
    }

    for basis in (
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ):
        result.setdefault(basis, 0.0)

    return result


def measure(
    state: ComplexState,
    rng: Random,
) -> Tuple[BasisState, ComplexState]:
    """
    Perform a projective computational-basis measurement.

    The selected outcome is sampled according to |amplitude|^2.
    After observing an outcome, all incompatible amplitudes disappear
    and the remaining state is normalized.
    """
    distribution = probabilities(state)
    threshold = rng.random()
    cumulative = 0.0
    selected: BasisState | None = None

    for basis in sorted(distribution):
        cumulative += distribution[basis]
        if threshold < cumulative:
            selected = basis
            break

    if selected is None:
        selected = (1, 1)

    collapsed = computational_state(*selected)
    return selected, collapsed


def measure_qubit(
    state: ComplexState,
    qubit: int,
    rng: Random,
) -> Tuple[int, ComplexState]:
    """
    Measure only one qubit.

    This is useful because measuring one member of an entangled pair
    can condition the state of the unmeasured member.
    """
    if qubit not in (0, 1):
        raise ValueError("Qubit must be 0 or 1.")

    marginal = {0: 0.0, 1: 0.0}

    for basis, amplitude in state.items():
        marginal[basis[qubit]] += abs(amplitude) ** 2

    selected_value = 0 if rng.random() < marginal[0] else 1

    compatible = {
        basis: amplitude
        for basis, amplitude in state.items()
        if basis[qubit] == selected_value
    }

    collapsed = normalize(compatible)
    return selected_value, collapsed


def create_bell_state(index: int) -> ComplexState:
    """
    Construct the four Bell states using gates.

    |Phi+> = (|00> + |11>) / sqrt(2)
    |Phi-> = (|00> - |11>) / sqrt(2)
    |Psi+> = (|01> + |10>) / sqrt(2)
    |Psi-> = (|01> - |10>) / sqrt(2)

    The common circuit begins with |00>, applies H to qubit 0,
    then CNOT(0 -> 1). X and Z operations create the other variants.
    """
    if index not in range(4):
        raise ValueError("Bell-state index must be 0, 1, 2, or 3.")

    state = computational_state(0, 0)
    state = apply_hadamard(state, 0)
    state = apply_cnot(state, 0, 1)

    if index == 1:
        state = apply_pauli_z(state, 0)
    elif index == 2:
        state = apply_pauli_x(state, 1)
    elif index == 3:
        state = apply_pauli_z(state, 0)
        state = apply_pauli_x(state, 1)

    return normalize(state)


BELL_NAMES = {
    0: "Phi+",
    1: "Phi-",
    2: "Psi+",
    3: "Psi-",
}


def print_state(label: str, state: ComplexState) -> None:
    print(f"\n{label}")
    for basis in sorted(state):
        print(f"  {basis_label(basis)} : {format_complex(state[basis])}")


def print_probabilities(state: ComplexState) -> None:
    for basis, probability in probabilities(state).items():
        if probability > EPSILON:
            print(f"  P({basis_label(basis)}) = {probability:.4f}")


def demonstrate_bell_construction() -> None:
    print("=" * 72)
    print("BELL STATE CONSTRUCTION")
    print("=" * 72)

    for index in range(4):
        state = create_bell_state(index)
        print_state(f"|{BELL_NAMES[index]}>", state)
        print_probabilities(state)


def demonstrate_measurement_statistics(
    state: ComplexState,
    trials: int = 5000,
    seed: int = 20261003,
) -> Dict[BasisState, int]:
    """
    Repeatedly prepare a fresh Bell pair and measure it.

    A fresh preparation is required for every trial because measurement
    is destructive in this simulation: the state collapses to an outcome.
    """
    rng = Random(seed)
    counts = {
        (0, 0): 0,
        (0, 1): 0,
        (1, 0): 0,
        (1, 1): 0,
    }

    for _ in range(trials):
        outcome, _ = measure(state, rng)
        counts[outcome] += 1

    return counts


def print_statistics(
    state_name: str,
    counts: Dict[BasisState, int],
    trials: int,
) -> None:
    print(f"\nMeasurement statistics for |{state_name}>")
    for basis in sorted(counts):
        frequency = counts[basis] / trials
        print(
            f"  {basis_label(basis)}: "
            f"{counts[basis]:5d} / {trials} = {frequency:.4f}"
        )


def demonstrate_all_bell_statistics() -> None:
    print("\n" + "=" * 72)
    print("REPEATED COMPUTATIONAL-BASIS MEASUREMENTS")
    print("=" * 72)

    for index in range(4):
        state = create_bell_state(index)
        counts = demonstrate_measurement_statistics(state)
        print_statistics(BELL_NAMES[index], counts, 5000)


def demonstrate_partial_measurement() -> None:
    print("\n" + "=" * 72)
    print("PARTIAL MEASUREMENT AND COLLAPSE")
    print("=" * 72)

    state = create_bell_state(0)
    rng = Random(42)

    print_state("Initial |Phi+>", state)

    measured_value, collapsed = measure_qubit(state, 0, rng)

    print(
        f"\nMeasured qubit 0 and observed {measured_value}."
        " The unmeasured qubit is now conditioned by that result."
    )
    print_state("Post-measurement state", collapsed)


def expectation_z(state: ComplexState, qubit: int) -> float:
    """Calculate <Z> for one qubit in the computational basis."""
    if qubit not in (0, 1):
        raise ValueError("Qubit must be 0 or 1.")

    value = 0.0

    for basis, amplitude in state.items():
        eigenvalue = 1.0 if basis[qubit] == 0 else -1.0
        value += abs(amplitude) ** 2 * eigenvalue

    return value


def expectation_zz(state: ComplexState) -> float:
    """
    Calculate <Z ⊗ Z>.

    For Phi states the two bits agree, giving +1.
    For Psi states they differ, giving -1.
    """
    value = 0.0

    for basis, amplitude in state.items():
        eigenvalue = 1.0 if basis[0] == basis[1] else -1.0
        value += abs(amplitude) ** 2 * eigenvalue

    return value


def demonstrate_correlations() -> None:
    print("\n" + "=" * 72)
    print("CORRELATION OBSERVABLES")
    print("=" * 72)

    for index in range(4):
        state = create_bell_state(index)

        print(
            f"|{BELL_NAMES[index]}>: "
            f"<Z0>={expectation_z(state, 0):+.1f}, "
            f"<Z1>={expectation_z(state, 1):+.1f}, "
            f"<Z0 Z1>={expectation_zz(state):+.1f}"
        )


def bell_state_fingerprint(state: ComplexState) -> str:
    """
    Identify a Bell state when the exact simulated state vector is known.

    Real hardware does not expose an exact state vector to the user.
    Experimental Bell-state identification instead requires a suitable
    measurement protocol and statistical inference.
    """
    state = normalize(state)

    targets = {
        "Phi+": create_bell_state(0),
        "Phi-": create_bell_state(1),
        "Psi+": create_bell_state(2),
        "Psi-": create_bell_state(3),
    }

    def fidelity(candidate: ComplexState, target: ComplexState) -> float:
        inner_product = sum(
            candidate.get(basis, 0.0j).conjugate()
            * target.get(basis, 0.0j)
            for basis in set(candidate) | set(target)
        )
        return abs(inner_product) ** 2

    scores = {
        name: fidelity(state, target)
        for name, target in targets.items()
    }

    return max(scores, key=scores.get)


def demonstrate_identification() -> None:
    print("\n" + "=" * 72)
    print("SIMULATED BELL-STATE IDENTIFICATION")
    print("=" * 72)

    for index in range(4):
        state = create_bell_state(index)
        print(
            f"Prepared state |{BELL_NAMES[index]}> "
            f"-> simulator fingerprint: |{bell_state_fingerprint(state)}>"
        )


def density_matrix(state: ComplexState) -> List[List[complex]]:
    """Construct the full 4x4 density matrix rho = |psi><psi|."""
    ordered_basis = [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ]

    vector = [state.get(basis, 0.0j) for basis in ordered_basis]

    return [
        [
            vector[row] * vector[column].conjugate()
            for column in range(4)
        ]
        for row in range(4)
    ]


def partial_trace_first_qubit(state: ComplexState) -> List[List[complex]]:
    """
    Reduce a two-qubit pure state to qubit 1.

    For every Bell state the reduced density matrix is I/2.
    This is a direct mathematical signature of maximal entanglement
    for these pure two-qubit states.
    """
    rho = density_matrix(state)

    # Basis order is |00>, |01>, |10>, |11>.
    reduced = [
        [
            rho[0][0] + rho[2][2],
            rho[0][1] + rho[2][3],
        ],
        [
            rho[1][0] + rho[3][2],
            rho[1][1] + rho[3][3],
        ],
    ]

    return reduced


def demonstrate_reduced_states() -> None:
    print("\n" + "=" * 72)
    print("REDUCED DENSITY MATRICES")
    print("=" * 72)

    for index in range(4):
        reduced = partial_trace_first_qubit(create_bell_state(index))

        print(f"\nReduced state of qubit 1 for |{BELL_NAMES[index]}>:")
        for row in reduced:
            print(
                "  ["
                + ", ".join(format_complex(value) for value in row)
                + "]"
            )


def demonstrate_error_handling() -> None:
    print("\n" + "=" * 72)
    print("VALIDATION AND FAILURE CONDITIONS")
    print("=" * 72)

    invalid_inputs = [
        ("invalid Bell index", lambda: create_bell_state(4)),
        ("invalid qubit", lambda: apply_hadamard(computational_state(0, 0), 2)),
        (
            "same CNOT control and target",
            lambda: apply_cnot(computational_state(0, 0), 0, 0),
        ),
        ("zero-state normalization", lambda: normalize({})),
    ]

    for description, operation in invalid_inputs:
        try:
            operation()
        except (ValueError, KeyError) as exc:
            print(f"{description}: correctly rejected -> {exc}")


def main() -> None:
    demonstrate_bell_construction()
    demonstrate_all_bell_statistics()
    demonstrate_partial_measurement()
    demonstrate_correlations()
    demonstrate_identification()
    demonstrate_reduced_states()
    demonstrate_error_handling()

    print("\n" + "=" * 72)
    print("BELL-STATE SIMULATION COMPLETE")
    print("=" * 72)
    print(
        "\nKey simulation rule: a Bell pair must be prepared again before "
        "each independent measurement trial because measurement collapses "
        "the state."
    )


if __name__ == "__main__":
    main()
