#!/usr/bin/env python3
"""
Quantum Fourier Transform fundamentals.

This script implements the QFT directly from its definition, verifies its
unitarity, compares the QFT with a classical discrete Fourier transform,
simulates measurement probabilities, and demonstrates the inverse QFT.

The implementation uses complex amplitudes and the Python standard library
only.
"""

from __future__ import annotations

import cmath
import math
import random
from typing import Sequence


EPSILON = 1e-10


def validate_state(state: Sequence[complex]) -> None:
    """Validate that an amplitude vector represents a legal quantum state."""
    if not state:
        raise ValueError("State vector cannot be empty.")

    dimension = len(state)

    if dimension & (dimension - 1):
        raise ValueError(
            "QFT state dimension must be a power of two for an n-qubit register."
        )

    norm_squared = sum(abs(amplitude) ** 2 for amplitude in state)

    if not math.isclose(norm_squared, 1.0, abs_tol=EPSILON):
        raise ValueError(
            f"State must be normalized. Squared norm is {norm_squared:.12f}."
        )


def computational_basis_state(qubits: int, index: int) -> list[complex]:
    """Construct |index> for a register containing the requested qubits."""
    if qubits < 1:
        raise ValueError("Number of qubits must be positive.")

    dimension = 1 << qubits

    if not 0 <= index < dimension:
        raise ValueError("Basis-state index is outside the register dimension.")

    state = [0j] * dimension
    state[index] = 1.0 + 0j
    return state


def normalize(state: Sequence[complex]) -> list[complex]:
    """Return a normalized copy of an arbitrary nonzero vector."""
    norm = math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))

    if norm <= EPSILON:
        raise ValueError("Cannot normalize the zero vector.")

    return [amplitude / norm for amplitude in state]


def qft(state: Sequence[complex]) -> list[complex]:
    """
    Apply the mathematical Quantum Fourier Transform.

    For dimension N:

        y_k = 1/sqrt(N) * sum_j x_j * exp(2*pi*i*j*k/N)

    Complexity:
        Time:  O(N^2)
        Space: O(N)

    This is a state-vector simulation, not a physical quantum circuit.
    """
    validate_state(state)

    n = len(state)
    scale = 1.0 / math.sqrt(n)
    transformed = []

    for k in range(n):
        amplitude = 0j

        for j, value in enumerate(state):
            phase = 2.0 * math.pi * j * k / n
            amplitude += value * cmath.exp(1j * phase)

        transformed.append(scale * amplitude)

    return transformed


def inverse_qft(state: Sequence[complex]) -> list[complex]:
    """Apply the inverse QFT using the negative Fourier phase."""
    validate_state(state)

    n = len(state)
    scale = 1.0 / math.sqrt(n)
    transformed = []

    for k in range(n):
        amplitude = 0j

        for j, value in enumerate(state):
            phase = -2.0 * math.pi * j * k / n
            amplitude += value * cmath.exp(1j * phase)

        transformed.append(scale * amplitude)

    return transformed


def hadamard_transform_on_all_qubits(state: Sequence[complex]) -> list[complex]:
    """
    Apply H tensor H tensor ... tensor H using the direct Walsh-Hadamard rule.

    This is useful for comparison because QFT is not simply a collection
    of independent Hadamard gates.
    """
    validate_state(state)

    values = list(state)
    dimension = len(values)
    stride = 1

    while stride < dimension:
        block = stride * 2

        for start in range(0, dimension, block):
            for offset in range(stride):
                left = start + offset
                right = left + stride

                a = values[left]
                b = values[right]

                values[left] = (a + b) / math.sqrt(2)
                values[right] = (a - b) / math.sqrt(2)

        stride *= 2

    return values


def classical_dft(state: Sequence[complex]) -> list[complex]:
    """
    Compute the classical DFT without quantum normalization.

    The positive exponential matches the QFT convention used above.
    """
    n = len(state)
    return [
        sum(
            value * cmath.exp(2j * math.pi * j * k / n)
            for j, value in enumerate(state)
        )
        for k in range(n)
    ]


def probabilities(state: Sequence[complex]) -> list[float]:
    """Convert amplitudes into computational-basis measurement probabilities."""
    validate_state(state)
    return [abs(amplitude) ** 2 for amplitude in state]


def sample_measurement(
    state: Sequence[complex],
    shots: int = 1000,
    seed: int | None = 7,
) -> dict[int, int]:
    """
    Sample computational-basis measurements from the state.

    A local random generator avoids changing global application randomness.
    """
    if shots <= 0:
        raise ValueError("Shots must be positive.")

    validate_state(state)

    rng = random.Random(seed)
    distribution = probabilities(state)
    outcomes = list(range(len(state)))
    counts = {outcome: 0 for outcome in outcomes}

    for _ in range(shots):
        measured = rng.choices(outcomes, weights=distribution, k=1)[0]
        counts[measured] += 1

    return counts


def max_vector_error(
    first: Sequence[complex],
    second: Sequence[complex],
) -> float:
    """Return the maximum element-wise absolute difference."""
    if len(first) != len(second):
        raise ValueError("Vectors must have equal dimensions.")

    return max(
        (abs(a - b) for a, b in zip(first, second)),
        default=0.0,
    )


def qft_matrix(qubits: int) -> list[list[complex]]:
    """Construct the QFT matrix explicitly."""
    if qubits < 1:
        raise ValueError("Number of qubits must be positive.")

    n = 1 << qubits
    scale = 1.0 / math.sqrt(n)

    return [
        [
            scale * cmath.exp(2j * math.pi * row * column / n)
            for column in range(n)
        ]
        for row in range(n)
    ]


def verify_unitarity(matrix: Sequence[Sequence[complex]]) -> float:
    """
    Check U*U = I and return the maximum numerical error.

    This establishes that the QFT preserves vector norms and is reversible.
    """
    n = len(matrix)

    if any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be square.")

    max_error = 0.0

    for row in range(n):
        for column in range(n):
            value = sum(
                matrix[row][k].conjugate() * matrix[column][k]
                for k in range(n)
            )
            expected = 1.0 if row == column else 0.0
            max_error = max(max_error, abs(value - expected))

    return max_error


def format_complex(value: complex) -> str:
    """Produce compact human-readable complex amplitudes."""
    real = 0.0 if abs(value.real) < 5e-12 else value.real
    imag = 0.0 if abs(value.imag) < 5e-12 else value.imag

    if imag == 0.0:
        return f"{real:+.5f}"
    if real == 0.0:
        return f"{imag:+.5f}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:+.5f}{sign}{abs(imag):.5f}i"


def print_state(title: str, state: Sequence[complex]) -> None:
    print(title)
    for index, amplitude in enumerate(state):
        print(
            f"  |{index:0{max(1, int(math.log2(len(state))))}b}>: "
            f"{format_complex(amplitude)}"
        )


def demonstrate_basis_state() -> None:
    """A basis state becomes an equal-magnitude phase state under QFT."""
    state = computational_basis_state(3, 1)
    transformed = qft(state)

    print_state("QFT of |001>:", transformed)
    print("Probabilities:", [round(p, 6) for p in probabilities(transformed)])
    print()


def demonstrate_superposition() -> None:
    """
    A periodic state produces a structured Fourier spectrum.

    The input contains |0> and |4>, giving a period of two in an eight-state
    register and producing nonzero output only at selected frequencies.
    """
    state = normalize([1, 0, 0, 0, 1, 0, 0, 0])
    transformed = qft(state)

    print_state("QFT of normalized (|000> + |100>) state:", transformed)
    print(
        "Probabilities:",
        [round(p, 6) for p in probabilities(transformed)],
    )
    print()


def demonstrate_inverse() -> None:
    """Verify that inverse QFT recovers the original state."""
    state = normalize(
        [
            1 + 1j,
            2 - 1j,
            -1 + 0.5j,
            0.25 - 2j,
        ]
    )

    transformed = qft(state)
    recovered = inverse_qft(transformed)

    error = max_vector_error(state, recovered)

    print(f"Inverse-QFT reconstruction error: {error:.3e}")
    if error > 1e-9:
        raise AssertionError("Inverse QFT failed numerical verification.")
    print()


def demonstrate_classical_relationship() -> None:
    """Show that the QFT is the normalized DFT applied to amplitudes."""
    state = normalize(
        [
            1,
            2,
            1j,
            -1,
        ]
    )

    quantum = qft(state)
    classical = classical_dft(state)
    expected = [value / math.sqrt(len(state)) for value in classical]

    error = max_vector_error(quantum, expected)

    print(f"QFT vs normalized DFT error: {error:.3e}")
    print()


def demonstrate_measurement() -> None:
    """Estimate measurement probabilities with repeated simulated shots."""
    state = normalize([1, 1, 0, 0])

    counts = sample_measurement(state, shots=2000, seed=42)

    print("Measurement counts from 2000 shots:")
    for outcome, count in counts.items():
        print(f"  |{outcome:02b}>: {count}")
    print()


def demonstrate_hadamard_difference() -> None:
    """
    Contrast QFT with applying H to every qubit.

    The two operations agree on some special states but are different
    unitary transformations in general.
    """
    state = computational_basis_state(3, 1)

    qft_result = qft(state)
    hadamard_result = hadamard_transform_on_all_qubits(state)

    difference = max_vector_error(qft_result, hadamard_result)

    print(f"QFT vs H^3 maximum amplitude difference: {difference:.3e}")
    print()


def main() -> None:
    print("Quantum Fourier Transform fundamentals")
    print("=" * 42)

    matrix = qft_matrix(3)
    unitarity_error = verify_unitarity(matrix)

    print(f"3-qubit QFT matrix unitarity error: {unitarity_error:.3e}")
    if unitarity_error > 1e-9:
        raise AssertionError("QFT matrix is not numerically unitary.")
    print()

    demonstrate_basis_state()
    demonstrate_superposition()
    demonstrate_inverse()
    demonstrate_classical_relationship()
    demonstrate_measurement()
    demonstrate_hadamard_difference()

    print("All QFT checks completed successfully.")


if __name__ == "__main__":
    main()
