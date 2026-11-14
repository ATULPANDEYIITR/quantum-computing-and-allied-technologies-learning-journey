#!/usr/bin/env python3
"""
Zero-Noise Extrapolation (ZNE): Practical Quantum Error Mitigation

A self-contained educational implementation demonstrating:
- Noise scaling through gate-folding-inspired models
- Observable measurement at multiple noise scales
- Linear and polynomial extrapolation
- Least-squares regression
- Measurement uncertainty
- Richardson extrapolation
- Validation and experiment reporting

Uses only the Python standard library.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import argparse
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Sequence

class ExtrapolationMethod(Enum):
    LINEAR = "linear"
    QUADRATIC = "quadratic"
    RICHARDSON = "richardson"

@dataclass(frozen=True)
class NoiseScale:
    factor: float

    def __post_init__(self):
        if not math.isfinite(self.factor) or self.factor < 1.0:
            raise ValueError("Noise scale must be finite and >= 1.")

@dataclass
class Measurement:
    scale: float
    mean: float
    standard_error: float
    shots: int

@dataclass
class ZNEResult:
    method: str
    ideal_reference: float
    noisy_baseline: float
    mitigated_estimate: float
    mitigation_error: float
    baseline_error: float
    measurements: list[dict]
    coefficients: list[float]

    def to_dict(self):
        return asdict(self)

class ZNEError(Exception):
    """Base exception for ZNE experiment failures."""

class InsufficientDataError(ZNEError):
    pass

class NumericalError(ZNEError):
    pass

def solve_linear_system(
    matrix: list[list[float]],
    vector: list[float]
) -> list[float]:
    """Solve a small dense linear system using Gaussian elimination."""
    n = len(vector)

    if n == 0 or len(matrix) != n:
        raise NumericalError("Invalid matrix dimensions.")

    a = [
        [float(value) for value in matrix[i]] + [float(vector[i])]
        for i in range(n)
    ]

    if any(len(row) != n + 1 for row in a):
        raise NumericalError("Matrix must be square.")

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))

        if abs(a[pivot][col]) < 1e-12:
            raise NumericalError("Singular regression matrix.")

        a[col], a[pivot] = a[pivot], a[col]

        divisor = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= divisor

        for row in range(n):
            if row == col:
                continue

            factor = a[row][col]
            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]

    return [a[i][n] for i in range(n)]

def polynomial_regression(
    x_values: Sequence[float],
    y_values: Sequence[float],
    degree: int
) -> list[float]:
    """
    Fit y = c0 + c1*x + ... + cd*x**d.

    Returns coefficients in ascending power order.
    """
    if len(x_values) != len(y_values):
        raise ValueError("Input arrays must have equal lengths.")

    if degree < 0 or len(x_values) < degree + 1:
        raise InsufficientDataError("Insufficient regression observations.")

    if not all(math.isfinite(x) for x in x_values):
        raise ValueError("Noise scales must be finite.")

    if not all(math.isfinite(y) for y in y_values):
        raise ValueError("Measurements must be finite.")

    if len(set(x_values)) < degree + 1:
        raise InsufficientDataError("Insufficient distinct noise scales.")

    powers = [
        sum(x ** power for x in x_values)
        for power in range(2 * degree + 1)
    ]

    matrix = [
        [powers[row + col] for col in range(degree + 1)]
        for row in range(degree + 1)
    ]

    vector = [
        sum(
            y * (x ** power)
            for x, y in zip(x_values, y_values)
        )
        for power in range(degree + 1)
    ]

    return solve_linear_system(matrix, vector)

class QuantumNoiseSimulator:
    """
    Simplified observable-noise model.

    This is a statistical simulation, not a quantum hardware simulator.
    The underlying expectation value is:

        E(lambda) = ideal + a*lambda + b*lambda^2
    """

    def __init__(
        self,
        ideal_value: float,
        linear_noise: float = -0.12,
        quadratic_noise: float = -0.025,
        seed: int = 42
    ):
        if not math.isfinite(ideal_value):
            raise ValueError("Ideal value must be finite.")

        if not -1 <= ideal_value <= 1:
            raise ValueError("Observable expectation must be in [-1, 1].")

        if not all(
            math.isfinite(v)
            for v in (linear_noise, quadratic_noise)
        ):
            raise ValueError("Noise coefficients must be finite.")

        self.ideal = ideal_value
        self.linear_noise = linear_noise
        self.quadratic_noise = quadratic_noise
        self.random = random.Random(seed)

    def expectation(self, scale: float) -> float:
        value = (
            self.ideal
            + self.linear_noise * scale
            + self.quadratic_noise * scale ** 2
        )
        return max(-1.0, min(1.0, value))

    def measure(self, scale: NoiseScale, shots: int) -> Measurement:
        if shots < 2:
            raise ValueError("At least two measurement shots are required.")

        probability_plus = (
            1.0 + self.expectation(scale.factor)
        ) / 2.0

        plus_count = sum(
            self.random.random() < probability_plus
            for _ in range(shots)
        )

        estimate = 2.0 * plus_count / shots - 1.0

        # Standard error of the sample mean for +/-1 outcomes.
        standard_error = math.sqrt(
            max(0.0, 1.0 - estimate ** 2) / shots
        )

        return Measurement(
            scale=scale.factor,
            mean=estimate,
            standard_error=standard_error,
            shots=shots
        )

class ZeroNoiseExtrapolator:

    def __init__(self, method: ExtrapolationMethod):
        self.method = method

    def fit(self, measurements: Sequence[Measurement]) -> tuple[float, list[float]]:
        if self.method == ExtrapolationMethod.LINEAR:
            degree = 1
        elif self.method == ExtrapolationMethod.QUADRATIC:
            degree = 2
        else:
            return self.richardson(measurements), []

        if len(measurements) < degree + 1:
            raise InsufficientDataError(
                f"{self.method.value} requires at least {degree + 1} measurements."
            )

        x = [m.scale for m in measurements]
        y = [m.mean for m in measurements]

        coefficients = polynomial_regression(x, y, degree)

        # At zero noise, the polynomial equals its intercept.
        return coefficients[0], coefficients

    @staticmethod
    def richardson(measurements: Sequence[Measurement]) -> float:
        """
        First-order Richardson extrapolation.

        For two distinct noise scales:
        E(0) = (lambda2*E(lambda1) -
                lambda1*E(lambda2)) / (lambda2-lambda1)
        """
        if len(measurements) != 2:
            raise InsufficientDataError(
                "Richardson implementation requires exactly two scales."
            )

        first, second = measurements

        if first.scale == second.scale:
            raise ValueError("Richardson scales must be different.")

        return (
            second.scale * first.mean
            - first.scale * second.mean
        ) / (second.scale - first.scale)

class ZNEExperiment:

    def __init__(
        self,
        simulator: QuantumNoiseSimulator,
        scales: Sequence[float],
        shots: int = 20000
    ):
        if len(scales) < 2:
            raise ValueError("At least two noise scales are required.")

        self.scales = [NoiseScale(s) for s in scales]

        if len({s.factor for s in self.scales}) != len(self.scales):
            raise ValueError("Noise scales must be unique.")

        if shots < 2:
            raise ValueError("Shots must be >= 2.")

        self.simulator = simulator
        self.shots = shots

    def run(
        self,
        method: ExtrapolationMethod
    ) -> ZNEResult:

        if method == ExtrapolationMethod.RICHARDSON:
            selected_scales = sorted(
                self.scales,
                key=lambda s: s.factor
            )[:2]
        else:
            selected_scales = self.scales

        measurements = [
            self.simulator.measure(scale, self.shots)
            for scale in selected_scales
        ]

        extrapolator = ZeroNoiseExtrapolator(method)
        estimate, coefficients = extrapolator.fit(measurements)

        baseline = measurements[0].mean
        ideal = self.simulator.ideal

        return ZNEResult(
            method=method.value,
            ideal_reference=ideal,
            noisy_baseline=baseline,
            mitigated_estimate=estimate,
            mitigation_error=abs(estimate - ideal),
            baseline_error=abs(baseline - ideal),
            measurements=[asdict(m) for m in measurements],
            coefficients=coefficients
        )

def run_self_tests():
    # Exact polynomial recovery.
    coefficients = polynomial_regression(
        [1.0, 2.0, 3.0],
        [0.8, 0.5, 0.15],
        2
    )

    assert abs(coefficients[0] - 1.0) < 1e-9
    assert abs(coefficients[1] + 0.15) < 1e-9
    assert abs(coefficients[2] - 0.0) < 1e-9

    # Richardson extrapolation.
    result = ZeroNoiseExtrapolator.richardson([
        Measurement(1.0, 0.8, 0.01, 10000),
        Measurement(2.0, 0.6, 0.01, 10000)
    ])

    assert abs(result - 1.0) < 1e-9

    # Invalid scales.
    try:
        NoiseScale(0.5)
        raise AssertionError("Invalid scale was accepted.")
    except ValueError:
        pass

    # Insufficient measurements.
    try:
        ZeroNoiseExtrapolator(
            ExtrapolationMethod.QUADRATIC
        ).fit([
            Measurement(1.0, 0.8, 0.01, 1000),
            Measurement(2.0, 0.6, 0.01, 1000)
        ])
        raise AssertionError("Insufficient data was accepted.")
    except InsufficientDataError:
        pass

    print("All self-tests passed.")

def main():
    parser = argparse.ArgumentParser(
        description="Zero-Noise Extrapolation experiment"
    )

    parser.add_argument("--shots", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("zne_results.json")
    )

    args = parser.parse_args()

    run_self_tests()

    simulator = QuantumNoiseSimulator(
        ideal_value=0.85,
        linear_noise=-0.12,
        quadratic_noise=-0.025,
        seed=args.seed
    )

    experiment = ZNEExperiment(
        simulator,
        scales=[1.0, 1.5, 2.0, 2.5],
        shots=args.shots
    )

    results = []

    for method in ExtrapolationMethod:
        result = experiment.run(method)
        results.append(result.to_dict())

        print(f"\nMethod: {result.method}")
        print(f"Ideal reference: {result.ideal_reference:.6f}")
        print(f"Noisy baseline: {result.noisy_baseline:.6f}")
        print(f"Mitigated estimate: {result.mitigated_estimate:.6f}")
        print(f"Baseline error: {result.baseline_error:.6f}")
        print(f"Mitigation error: {result.mitigation_error:.6f}")

    output = {
        "experiment": "Zero-Noise Extrapolation",
        "shots_per_scale": args.shots,
        "noise_scales": [1.0, 1.5, 2.0, 2.5],
        "results": results
    }

    # Write atomically to avoid leaving a partially written report.
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")

    try:
        temporary.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8"
        )
        temporary.replace(args.output)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise

    print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
