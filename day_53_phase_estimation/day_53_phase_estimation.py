#!/usr/bin/env python3
"""
Quantum Phase Estimation implemented as a dependency-free state-vector simulator.

The program models the standard QPE circuit:
    |0>^m -- QFT† -- measurement
      |
    Hadamards
      |
    controlled-U^(2^k)
      |
    |psi> eigenstate of U

For U|psi> = exp(2*pi*i*theta)|psi>, QPE estimates theta in [0, 1).
The simulator includes:
- complex state-vector representation
- controlled phase evolution
- inverse Quantum Fourier Transform
- probability distributions
- measurement sampling
- exact and noisy examples
- validation and numerical diagnostics

No external packages are required.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple


EPSILON = 1e-12


@dataclass(frozen=True)
class EstimationResult:
    theta: float
    qubits: int
    probabilities: List[float]
    most_likely_integer: int
    estimate: float
    samples: List[int]

    @property
    def absolute_error(self) -> float:
        return abs(self.theta - self.estimate)


def validate_theta(theta: float) -> None:
    if not math.isfinite(theta):
        raise ValueError("theta must be finite")
    if not 0.0 <= theta < 1.0:
        raise ValueError("theta must satisfy 0 <= theta < 1")


def validate_qubits(qubits: int) -> None:
    if not isinstance(qubits, int) or isinstance(qubits, bool):
        raise TypeError("qubits must be an integer")
    if not 1 <= qubits <= 20:
        raise ValueError("qubits must be between 1 and 20 for this simulator")


def normalize(state: Sequence[complex]) -> List[complex]:
    norm = math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))
    if norm < EPSILON:
        raise ValueError("cannot normalize a zero state")
    return [amplitude / norm for amplitude in state]


def kron(left: Sequence[complex], right: Sequence[complex]) -> List[complex]:
    return [a * b for a in left for b in right]


def basis_zero() -> List[complex]:
    return [1.0 + 0j, 0.0 + 0j]


def basis_one() -> List[complex]:
    return [0.0 + 0j, 1.0 + 0j]


def hadamard(qubit: Sequence[complex]) -> List[complex]:
    if len(qubit) != 2:
        raise ValueError("Hadamard operates on a single qubit")
    factor = 1.0 / math.sqrt(2.0)
    return [
        factor * (qubit[0] + qubit[1]),
        factor * (qubit[0] - qubit[1]),
    ]


def initial_counting_register(qubits: int) -> List[complex]:
    """Create |+>^m, the counting register after m Hadamards."""
    state = [1.0 + 0j]
    plus = hadamard(basis_zero())

    for _ in range(qubits):
        state = kron(state, plus)

    return normalize(state)


def phase_eigenstate(theta: float) -> List[complex]:
    """
    A one-qubit state that is an eigenstate of the phase gate.

    P(theta) = diag(1, exp(2*pi*i*theta))
    |1> is an eigenstate with eigenvalue exp(2*pi*i*theta).

    The target eigenstate is therefore |1>.
    """
    validate_theta(theta)
    return basis_one()


def apply_hadamards_to_counting_register(
    state: List[complex], qubits: int
) -> List[complex]:
    """
    The counting register is initialized as |0...0>.
    Applying H to every counting qubit produces |+>^m.
    """
    expected = 2**qubits
    if len(state) != expected:
        raise ValueError("state dimension does not match qubit count")

    return initial_counting_register(qubits)


def apply_controlled_phase_power(
    state: List[complex],
    theta: float,
    control_qubit: int,
    qubits: int,
) -> List[complex]:
    """
    Apply controlled-U^(2^control_qubit).

    For eigenstate |1>, U^(2^k) contributes:
        exp(2*pi*i*theta*2^k)

    The counting register basis index is interpreted in binary.
    """
    validate_theta(theta)

    if not 0 <= control_qubit < qubits:
        raise ValueError("invalid control qubit")

    phase = cmath.exp(
        2j * math.pi * theta * (2**control_qubit)
    )
    result = state.copy()

    for basis_index, amplitude in enumerate(state):
        bit = (basis_index >> control_qubit) & 1
        if bit:
            result[basis_index] = amplitude * phase

    return result


def inverse_qft(state: Sequence[complex]) -> List[complex]:
    """
    Apply the inverse QFT directly to a state vector.

    For N = 2^m:
        |x> -> 1/sqrt(N) sum_y exp(-2*pi*i*x*y/N)|y>

    This O(N^2) implementation is intentionally explicit. A production
    simulator would normally use a structured O(m^2) gate decomposition
    or a specialized FFT-like implementation.
    """
    n = len(state)
    if n == 0 or n & (n - 1):
        raise ValueError("inverse QFT requires a power-of-two dimension")

    scale = 1.0 / math.sqrt(n)
    transformed = [0j] * n

    for y in range(n):
        total = 0j
        for x, amplitude in enumerate(state):
            angle = -2.0 * math.pi * x * y / n
            total += amplitude * cmath.exp(1j * angle)
        transformed[y] = total * scale

    return normalize(transformed)


def probabilities(state: Sequence[complex]) -> List[float]:
    values = [abs(amplitude) ** 2 for amplitude in state]
    total = sum(values)

    if total < EPSILON:
        raise ValueError("state has zero probability mass")

    values = [value / total for value in values]
    return values


def sample_distribution(
    probability_values: Sequence[float],
    samples: int,
    seed: int | None = 7,
) -> List[int]:
    if samples <= 0:
        raise ValueError("samples must be positive")

    if seed is not None:
        random.seed(seed)

    cumulative = []
    running = 0.0

    for probability in probability_values:
        if probability < -EPSILON:
            raise ValueError("probabilities cannot be negative")
        running += probability
        cumulative.append(running)

    cumulative[-1] = 1.0
    measurements = []

    for _ in range(samples):
        draw = random.random()
        for index, boundary in enumerate(cumulative):
            if draw <= boundary:
                measurements.append(index)
                break

    return measurements


def run_qpe(
    theta: float,
    qubits: int,
    samples: int = 1000,
    seed: int | None = 7,
) -> EstimationResult:
    """
    Run QPE for the one-qubit phase gate using |1> as the eigenstate.

    The phase information is encoded by controlled powers of U, then the
    inverse QFT converts relative phases into computational-basis amplitudes.
    """
    validate_theta(theta)
    validate_qubits(qubits)

    # The target eigenstate is |1>. Its state is not explicitly included in
    # the counting-register simulation because it remains unchanged.
    target = phase_eigenstate(theta)
    if target != basis_one():
        raise RuntimeError("unexpected target eigenstate")

    state = initial_counting_register(qubits)

    for control in range(qubits):
        state = apply_controlled_phase_power(
            state,
            theta,
            control,
            qubits,
        )

    transformed = inverse_qft(state)
    probability_values = probabilities(transformed)

    most_likely = max(
        range(len(probability_values)),
        key=probability_values.__getitem__,
    )

    estimate = most_likely / (2**qubits)
    measurements = sample_distribution(
        probability_values,
        samples,
        seed,
    )

    return EstimationResult(
        theta=theta,
        qubits=qubits,
        probabilities=probability_values,
        most_likely_integer=most_likely,
        estimate=estimate,
        samples=measurements,
    )


def circular_phase_error(theta: float, estimate: float) -> float:
    """
    Phase is periodic, so error can be evaluated on a circle.
    """
    raw = abs(theta - estimate)
    return min(raw, 1.0 - raw)


def print_distribution(result: EstimationResult, threshold: float = 1e-4) -> None:
    scale = 2**result.qubits

    print("\nMeasurement probability distribution:")
    for integer, probability in enumerate(result.probabilities):
        if probability >= threshold:
            phase = integer / scale
            print(
                f"  {integer:>4}  phase={phase:.8f}  "
                f"probability={probability:.8f}"
            )


def print_sample_histogram(samples: Sequence[int], qubits: int) -> None:
    counts = {}
    for value in samples:
        counts[value] = counts.get(value, 0) + 1

    print("\nSampled outcomes:")
    scale = 2**qubits

    for outcome in sorted(counts):
        print(
            f"  {outcome:>4}  "
            f"phase={outcome / scale:.8f}  "
            f"count={counts[outcome]}"
        )


def demonstrate_precision() -> None:
    """
    Compare different counting-register sizes.

    More counting qubits increase phase resolution from 1/2^m to a
    progressively finer grid.
    """
    theta = 0.3125

    print("Precision experiment")
    print("--------------------")
    print(f"Target phase: {theta}\n")

    for qubits in (3, 4, 5, 6):
        result = run_qpe(theta, qubits, samples=2000, seed=11)
        print(
            f"qubits={qubits:2d}  "
            f"estimate={result.estimate:.8f}  "
            f"absolute_error={result.absolute_error:.8f}"
        )


def demonstrate_non_binary_phase() -> None:
    """
    A phase such as 0.37 is not exactly representable with a small binary
    register. QPE therefore produces a peaked distribution rather than a
    single certain measurement.
    """
    result = run_qpe(0.37, 5, samples=2000, seed=19)

    print("\nNon-binary phase experiment")
    print("---------------------------")
    print(f"Target phase:       {result.theta:.8f}")
    print(f"Most likely result: {result.most_likely_integer}")
    print(f"Estimated phase:    {result.estimate:.8f}")
    print(f"Absolute error:     {result.absolute_error:.8f}")
    print(
        f"Circular error:     "
        f"{circular_phase_error(result.theta, result.estimate):.8f}"
    )

    print_distribution(result)
    print_sample_histogram(result.samples, result.qubits)


def demonstrate_failure_conditions() -> None:
    print("\nValidation checks")
    print("-----------------")

    for theta in (-0.1, 1.0, float("nan")):
        try:
            run_qpe(theta, 4)
        except (ValueError, TypeError) as error:
            print(f"Rejected theta={theta!r}: {error}")

    try:
        run_qpe(0.25, 0)
    except (ValueError, TypeError) as error:
        print(f"Rejected invalid qubit count: {error}")


def main() -> None:
    print("Quantum Phase Estimation")
    print("========================")
    print("Dependency-free state-vector simulation")

    exact = run_qpe(0.625, 4, samples=1000, seed=3)

    print("\nExactly representable phase")
    print("---------------------------")
    print(f"Target phase:       {exact.theta:.8f}")
    print(f"Most likely result: {exact.most_likely_integer}")
    print(f"Estimated phase:    {exact.estimate:.8f}")
    print(f"Absolute error:     {exact.absolute_error:.8f}")

    print_distribution(exact)

    demonstrate_non_binary_phase()
    demonstrate_precision()
    demonstrate_failure_conditions()

    print("\nImplementation notes")
    print("--------------------")
    print("State dimension: 2^m for m counting qubits.")
    print("Controlled phase operations: O(2^m) per operation.")
    print("Direct inverse QFT: O(4^m) arithmetic operations.")
    print("Measurement samples reuse the final probability distribution.")
    print(
        "For production-scale simulation, avoid materializing exponentially "
        "large state vectors and use a specialized quantum simulator."
    )


if __name__ == "__main__":
    main()
