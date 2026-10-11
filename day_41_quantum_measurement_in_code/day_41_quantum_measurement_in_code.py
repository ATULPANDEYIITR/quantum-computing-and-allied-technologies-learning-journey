#!/usr/bin/env python3
"""Quantum measurement: shots, counts, probabilities, and statistical uncertainty.

Self-contained educational simulator for computational-basis measurements.
Uses Python's standard library and a seeded pseudorandom generator.

This simulates measurement of an already-prepared state. It does not simulate
quantum gates, entanglement dynamics, or hardware noise.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Sequence


def validate_probabilities(
    probabilities: Mapping[str, float],
    tolerance: float = 1e-9,
) -> dict[str, float]:
    """Validate and normalize a probability distribution."""
    if not probabilities:
        raise ValueError("At least one outcome is required.")

    normalized: dict[str, float] = {}
    for outcome, probability in probabilities.items():
        if not isinstance(outcome, str) or not outcome:
            raise ValueError("Outcome labels must be non-empty strings.")
        if any(bit not in "01" for bit in outcome):
            raise ValueError(f"Invalid computational-basis outcome: {outcome!r}")
        if not isinstance(probability, (int, float)) or isinstance(
            probability, bool
        ):
            raise TypeError("Probabilities must be numeric.")
        probability = float(probability)
        if not math.isfinite(probability) or probability < 0:
            raise ValueError("Probabilities must be finite and non-negative.")
        normalized[outcome] = probability

    total = math.fsum(normalized.values())
    if total <= 0:
        raise ValueError("At least one probability must be positive.")
    if abs(total - 1.0) > tolerance:
        raise ValueError(f"Probabilities must sum to one, received {total}.")

    return {outcome: p / total for outcome, p in normalized.items()}


def probability_from_amplitudes(
    amplitudes: Mapping[str, complex],
) -> dict[str, float]:
    """Convert computational-basis amplitudes into Born-rule probabilities."""
    if not amplitudes:
        raise ValueError("At least one amplitude is required.")

    weights: dict[str, float] = {}
    for outcome, amplitude in amplitudes.items():
        if not isinstance(outcome, str) or not outcome:
            raise ValueError("Outcome labels must be non-empty strings.")
        if any(bit not in "01" for bit in outcome):
            raise ValueError(f"Invalid basis state: {outcome!r}")
        amplitude = complex(amplitude)
        if not math.isfinite(amplitude.real) or not math.isfinite(amplitude.imag):
            raise ValueError("Amplitudes must be finite.")
        weights[outcome] = abs(amplitude) ** 2

    norm = math.fsum(weights.values())
    if not math.isclose(norm, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"State must be normalized; squared norm is {norm}.")
    return weights


def format_bitstring(value: int, width: int) -> str:
    """Preserve leading zeros when displaying a measured register."""
    if width < 1 or value < 0 or value >= 2**width:
        raise ValueError("Value does not fit the requested register width.")
    return format(value, f"0{width}b")


@dataclass(frozen=True)
class MeasurementResult:
    shots: int
    counts: Mapping[str, int]
    probabilities: Mapping[str, float]

    def __post_init__(self) -> None:
        if self.shots <= 0:
            raise ValueError("Shots must be positive.")
        if any(count < 0 for count in self.counts.values()):
            raise ValueError("Counts cannot be negative.")
        if sum(self.counts.values()) != self.shots:
            raise ValueError("Counts must sum to the number of shots.")
        if set(self.counts) != set(self.probabilities):
            raise ValueError("Counts and probabilities must use the same outcomes.")

    def empirical_probabilities(self) -> dict[str, float]:
        return {
            outcome: self.counts[outcome] / self.shots
            for outcome in self.counts
        }

    def standard_errors(self) -> dict[str, float]:
        """Estimate binomial standard error for each outcome frequency."""
        estimates = self.empirical_probabilities()
        return {
            outcome: math.sqrt(p * (1.0 - p) / self.shots)
            for outcome, p in estimates.items()
        }

    def total_variation_distance(self) -> float:
        """Half the L1 distance between empirical and theoretical distributions."""
        observed = self.empirical_probabilities()
        return 0.5 * math.fsum(
            abs(observed[outcome] - self.probabilities[outcome])
            for outcome in self.probabilities
        )


class QuantumMeasurementSimulator:
    def __init__(
        self,
        probabilities: Mapping[str, float],
        seed: int | None = None,
    ) -> None:
        self.probabilities = validate_probabilities(probabilities)
        self.random = random.Random(seed)
        self.widths = {len(outcome) for outcome in self.probabilities}
        if len(self.widths) != 1:
            raise ValueError("All outcomes must have the same bit width.")

    @classmethod
    def from_amplitudes(
        cls,
        amplitudes: Mapping[str, complex],
        seed: int | None = None,
    ) -> QuantumMeasurementSimulator:
        return cls(probability_from_amplitudes(amplitudes), seed)

    def measure(self, shots: int) -> MeasurementResult:
        """Draw independent samples from the Born-rule distribution."""
        if not isinstance(shots, int) or isinstance(shots, bool) or shots <= 0:
            raise ValueError("Shots must be a positive integer.")

        outcomes = list(self.probabilities)
        weights = [self.probabilities[outcome] for outcome in outcomes]
        samples = self.random.choices(outcomes, weights=weights, k=shots)
        observed = Counter(samples)

        # Include zero-count outcomes so results remain comparable across runs.
        counts = {outcome: observed[outcome] for outcome in outcomes}
        return MeasurementResult(shots, counts, self.probabilities)


def print_result(result: MeasurementResult) -> None:
    empirical = result.empirical_probabilities()
    errors = result.standard_errors()

    print(f"\nShots: {result.shots}")
    print(f"{'Outcome':<12}{'Expected':>12}{'Count':>10}{'Observed':>12}{'Std. error':>13}")
    for outcome, theoretical in result.probabilities.items():
        print(
            f"{outcome:<12}{theoretical:>12.4f}"
            f"{result.counts[outcome]:>10}"
            f"{empirical[outcome]:>12.4f}"
            f"{errors[outcome]:>13.4f}"
        )
    print(f"Total variation distance: {result.total_variation_distance():.4f}")


def compare_shot_budgets(
    simulator: QuantumMeasurementSimulator,
    budgets: Sequence[int],
) -> None:
    """Compare independent experiments using increasing shot budgets."""
    print("\nShot-budget comparison")
    print(f"{'Shots':>10}{'Distance':>14}{'Expected scale':>18}")
    for shots in budgets:
        result = simulator.measure(shots)
        # Sampling errors commonly scale as 1/sqrt(shots), not as 1/shots.
        print(
            f"{shots:>10}"
            f"{result.total_variation_distance():>14.4f}"
            f"{1 / math.sqrt(shots):>18.4f}"
        )


def run_edge_case_checks() -> None:
    print("\nValidation checks")
    invalid_cases = [
        ({"0": 0.4, "1": 0.4}, "probabilities do not sum to one"),
        ({"0": -0.1, "1": 1.1}, "negative probability"),
        ({"0": float("nan"), "1": 0.0}, "non-finite probability"),
        ({"0": 0.5, "10": 0.5}, "inconsistent register widths"),
    ]

    for distribution, description in invalid_cases:
        try:
            simulator = QuantumMeasurementSimulator(distribution)
            simulator.measure(10)
        except (ValueError, TypeError) as error:
            print(f"Rejected {description}: {error}")
        else:
            raise AssertionError(f"Expected rejection: {description}")

    for shots in (0, -5, 1.5, True):
        try:
            QuantumMeasurementSimulator({"0": 0.5, "1": 0.5}).measure(shots)
        except ValueError:
            print(f"Rejected invalid shot count: {shots!r}")
        else:
            raise AssertionError(f"Expected rejection for shots={shots!r}")


def main() -> None:
    print("Quantum measurement: shots, counts, and probabilities")

    # A Hadamard-prepared qubit has equal probabilities for |0> and |1>.
    hadamard = QuantumMeasurementSimulator(
        {"0": 0.5, "1": 0.5},
        seed=42,
    )
    print("\nHadamard-prepared qubit")
    print_result(hadamard.measure(1000))

    # Amplitudes may be complex; the Born rule uses squared magnitudes.
    bell_state = QuantumMeasurementSimulator.from_amplitudes(
        {"00": 1 / math.sqrt(2), "11": 1 / math.sqrt(2)},
        seed=17,
    )
    print("\nBell state measured in the computational basis")
    bell_result = bell_state.measure(2000)
    print_result(bell_result)
    assert bell_result.counts["01"] == 0
    assert bell_result.counts["10"] == 0

    # A biased state makes clear that counts estimate, rather than equal,
    # theoretical probabilities.
    biased = QuantumMeasurementSimulator(
        {"0": 0.8, "1": 0.2},
        seed=7,
    )
    print("\nBiased qubit")
    print_result(biased.measure(500))

    compare_shot_budgets(
        QuantumMeasurementSimulator({"0": 0.5, "1": 0.5}, seed=2026),
        [100, 1000, 10000],
    )

    run_edge_case_checks()


if __name__ == "__main__":
    main()
