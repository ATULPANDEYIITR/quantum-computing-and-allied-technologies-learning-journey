#!/usr/bin/env python3
"""Quantum Algorithm Fundamentals through executable algorithmic thinking.

This standard-library implementation develops classical problem decomposition,
quantum-state simulation, interference, measurement, Deutsch's algorithm,
Bernstein-Vazirani, Grover search, and quantum resource analysis.

The simulator is intentionally limited to small state vectors. It illustrates
ideal gate-level behavior, not hardware noise or physical quantum execution.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

ComplexVector = list[complex]
EPSILON = 1e-9


class QuantumAlgorithmError(ValueError):
    """Raised when a quantum circuit or algorithm violates its assumptions."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise QuantumAlgorithmError(message)


def probability_distribution(state: Sequence[complex]) -> list[float]:
    """Convert amplitudes into measurement probabilities."""
    probabilities = [abs(amplitude) ** 2 for amplitude in state]
    total = sum(probabilities)
    require(total > EPSILON, "State has zero total probability.")
    return [probability / total for probability in probabilities]


def validate_state(state: Sequence[complex]) -> None:
    """Verify that a state vector is normalized."""
    require(len(state) > 0, "A state vector cannot be empty.")
    norm_squared = sum(abs(amplitude) ** 2 for amplitude in state)
    require(
        math.isclose(norm_squared, 1.0, abs_tol=EPSILON),
        f"State must be normalized; squared norm is {norm_squared}.",
    )


def measure_state(
    state: Sequence[complex], rng: random.Random
) -> int:
    """Sample one computational-basis outcome using its Born probability."""
    validate_state(state)
    probabilities = probability_distribution(state)
    threshold = rng.random()
    cumulative = 0.0

    for index, probability in enumerate(probabilities):
        cumulative += probability
        if threshold < cumulative:
            return index

    return len(probabilities) - 1


def hadamard_transform(state: Sequence[complex]) -> ComplexVector:
    """Apply H to every qubit using the Walsh-Hadamard transform."""
    validate_state(state)
    size = len(state)
    require(
        size & (size - 1) == 0,
        "State-vector length must be a power of two.",
    )

    output = list(state)
    width = 1

    # Each butterfly combines amplitudes whose relative sign is changed.
    # The transform costs O(N log N), rather than multiplying dense matrices.
    while width < size:
        for start in range(0, size, 2 * width):
            for offset in range(width):
                left = output[start + offset]
                right = output[start + offset + width]
                output[start + offset] = (left + right) / math.sqrt(2)
                output[start + offset + width] = (
                    left - right
                ) / math.sqrt(2)
        width *= 2

    validate_state(output)
    return output


def basis_state(qubit_count: int, index: int = 0) -> ComplexVector:
    """Create a computational-basis state using little-endian qubit indexing."""
    require(qubit_count >= 0, "Qubit count cannot be negative.")
    size = 1 << qubit_count
    require(0 <= index < size, "Basis index is outside the state space.")
    state = [0j] * size
    state[index] = 1 + 0j
    return state


def apply_x(state: Sequence[complex], qubit: int) -> ComplexVector:
    """Apply a Pauli-X gate to one qubit."""
    validate_state(state)
    qubit_count = (len(state)).bit_length() - 1
    require(0 <= qubit < qubit_count, "Invalid qubit index.")
    output = [0j] * len(state)
    mask = 1 << qubit

    for index, amplitude in enumerate(state):
        output[index ^ mask] = amplitude

    validate_state(output)
    return output


def apply_z(state: Sequence[complex], qubit: int) -> ComplexVector:
    """Apply a Pauli-Z phase flip to basis states with the chosen bit set."""
    validate_state(state)
    qubit_count = len(state).bit_length() - 1
    require(0 <= qubit < qubit_count, "Invalid qubit index.")
    mask = 1 << qubit

    output = [
        -amplitude if index & mask else amplitude
        for index, amplitude in enumerate(state)
    ]
    validate_state(output)
    return output


def apply_cnot(
    state: Sequence[complex], control: int, target: int
) -> ComplexVector:
    """Apply CNOT, flipping the target only when the control equals one."""
    validate_state(state)
    qubit_count = len(state).bit_length() - 1
    require(0 <= control < qubit_count, "Invalid control qubit.")
    require(0 <= target < qubit_count, "Invalid target qubit.")
    require(control != target, "Control and target must differ.")

    output = [0j] * len(state)
    control_mask = 1 << control
    target_mask = 1 << target

    for index, amplitude in enumerate(state):
        destination = (
            index ^ target_mask if index & control_mask else index
        )
        output[destination] = amplitude

    validate_state(output)
    return output


def format_bitstring(index: int, width: int) -> str:
    """Render an integer as a fixed-width binary string."""
    require(width >= 0, "Width cannot be negative.")
    require(0 <= index < (1 << width), "Index exceeds requested width.")
    return format(index, f"0{width}b")


def sample_counts(
    state: Sequence[complex], shots: int, seed: int = 7
) -> dict[int, int]:
    """Estimate measurement frequencies with a reproducible random stream."""
    require(shots > 0, "Shot count must be positive.")
    validate_state(state)
    rng = random.Random(seed)
    counts: dict[int, int] = {}

    for _ in range(shots):
        outcome = measure_state(state, rng)
        counts[outcome] = counts.get(outcome, 0) + 1

    return dict(sorted(counts.items()))


def deutsch_algorithm(
    oracle: Callable[[int], int]
) -> tuple[str, int]:
    """Determine whether a one-bit Boolean function is constant or balanced.

    The oracle is f(0), f(1). The phase-oracle construction uses a target
    qubit prepared in |->, so f(x) changes the phase by (-1)^f(x).
    """
    values = (oracle(0), oracle(1))
    require(
        all(value in (0, 1) for value in values),
        "Oracle must return bits.",
    )

    # Two-qubit basis index = target_bit * 2 + input_bit.
    state = basis_state(2, 2)  # |0>|1>
    state = hadamard_transform(state)  # H on both qubits
    transformed = [0j] * 4

    # U_f: |x,y> -> |x,y XOR f(x)>.
    for index, amplitude in enumerate(state):
        x = index & 1
        y = (index >> 1) & 1
        destination = x + 2 * (y ^ values[x])
        transformed[destination] += amplitude

    state = hadamard_transform(transformed)
    outcome = measure_state(state, random.Random(17))
    input_bit = outcome & 1

    # Constant functions produce input bit zero; balanced functions produce
    # input bit one with certainty in this ideal, noiseless circuit.
    classification = "constant" if input_bit == 0 else "balanced"
    return classification, outcome


def bernstein_vazirani(secret: str) -> str:
    """Recover an unknown bit string using one ideal oracle query."""
    require(bool(secret), "Secret must contain at least one bit.")
    require(
        all(bit in "01" for bit in secret),
        "Secret must contain only binary digits.",
    )

    width = len(secret)
    state = basis_state(width + 1, 1 << width)
    state = hadamard_transform(state)

    # The phase oracle implements (-1)^(secret dot x mod 2).
    phase_state = [
        (
            -amplitude
            if (index & ((1 << width) - 1) & int(secret[::-1], 2)).bit_count()
            % 2
            else amplitude
        )
        for index, amplitude in enumerate(state)
    ]

    state = hadamard_transform(phase_state)
    outcome = measure_state(state, random.Random(23))
    return format_bitstring(outcome & ((1 << width) - 1), width)


def grover_search(
    marked_indices: Iterable[int], qubit_count: int
) -> tuple[int, ComplexVector, int]:
    """Run Grover search with a known marked set and ideal phase oracle.

    The iteration count approximates pi/4 * sqrt(N/M), where N is the
    search-space size and M is the number of marked states.
    """
    require(qubit_count > 0, "Grover search requires at least one qubit.")
    size = 1 << qubit_count
    marked = set(marked_indices)

    require(bool(marked), "At least one marked state is required.")
    require(
        all(0 <= index < size for index in marked),
        "A marked index lies outside the search space.",
    )
    require(len(marked) < size, "All states are marked; no search is needed.")

    state = hadamard_transform(basis_state(qubit_count))
    marked_count = len(marked)
    iterations = max(
        1,
        round((math.pi / 4) * math.sqrt(size / marked_count)),
    )

    for _ in range(iterations):
        # The phase oracle reverses the sign of every marked amplitude.
        state = [
            -amplitude if index in marked else amplitude
            for index, amplitude in enumerate(state)
        ]

        # The diffusion operator performs reflection about the mean amplitude.
        mean_amplitude = sum(state) / size
        state = [2 * mean_amplitude - amplitude for amplitude in state]

    validate_state(state)
    return iterations, state, marked_count


@dataclass(frozen=True)
class AlgorithmEstimate:
    name: str
    oracle_queries: int
    qubits: int
    state_vector_amplitudes: int
    caveat: str


def resource_estimates() -> list[AlgorithmEstimate]:
    """Describe logical resources without claiming wall-clock speedups."""
    return [
        AlgorithmEstimate(
            "Deutsch",
            1,
            2,
            4,
            "Distinguishes constant from balanced one-bit functions.",
        ),
        AlgorithmEstimate(
            "Bernstein-Vazirani",
            1,
            5,
            64,
            "Five qubits encode four input bits and one target bit.",
        ),
        AlgorithmEstimate(
            "Grover",
            3,
            6,
            64,
            "Three oracle iterations for a 64-state search example.",
        ),
    ]


def run_demonstrations() -> None:
    print("Quantum Algorithm Fundamentals")
    print("=" * 42)

    print("\nMeasurement probabilities")
    state = hadamard_transform(basis_state(2))
    for index, probability in enumerate(probability_distribution(state)):
        print(f"|{format_bitstring(index, 2)}> : {probability:.3f}")

    print("\nInterference through H followed by H")
    restored = hadamard_transform(hadamard_transform(basis_state(1)))
    print("Recovered state:", [round(value.real, 6) for value in restored])

    print("\nDeutsch algorithm")
    oracles = {
        "constant zero": lambda x: 0,
        "constant one": lambda x: 1,
        "identity": lambda x: x,
        "negated identity": lambda x: 1 - x,
    }
    for name, oracle in oracles.items():
        classification, _ = deutsch_algorithm(oracle)
        print(f"{name:18s} -> {classification}")

    print("\nBernstein-Vazirani")
    secret = "1011"
    recovered = bernstein_vazirani(secret)
    print(f"Hidden bit string: {secret}")
    print(f"Recovered string:  {recovered}")
    require(recovered == secret, "Bernstein-Vazirani result mismatch.")

    print("\nGrover search")
    iterations, final_state, marked_count = grover_search({13}, 4)
    probabilities = probability_distribution(final_state)
    best_index = max(range(len(probabilities)), key=probabilities.__getitem__)
    print(f"Search-space size: {len(final_state)}")
    print(f"Marked states: {marked_count}")
    print(f"Iterations: {iterations}")
    print(f"Most probable result: {format_bitstring(best_index, 4)}")
    print(f"Marked-state probability: {probabilities[13]:.4f}")
    print(
        "Sample counts:",
        {
            format_bitstring(index, 4): count
            for index, count in sample_counts(final_state, 1000).items()
        },
    )

    print("\nResource model")
    for estimate in resource_estimates():
        print(
            f"{estimate.name}: queries={estimate.oracle_queries}, "
            f"qubits={estimate.qubits}, "
            f"state amplitudes={estimate.state_vector_amplitudes}"
        )
        print(f"  {estimate.caveat}")

    print("\nValidation checks")
    try:
        hadamard_transform([1 + 0j, 1 + 0j])
    except QuantumAlgorithmError as error:
        print("Rejected invalid state:", error)

    try:
        grover_search(set(), 3)
    except QuantumAlgorithmError as error:
        print("Rejected invalid search:", error)


if __name__ == "__main__":
    run_demonstrations()
