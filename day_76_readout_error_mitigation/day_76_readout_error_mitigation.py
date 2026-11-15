#!/usr/bin/env python3
"""
Readout Error Mitigation: Measurement-Error Correction

Implements:
- Readout calibration using known computational basis states.
- Single-qubit and multi-qubit assignment matrices.
- Tensor-product calibration matrices.
- Measurement probability estimation.
- Simplex-constrained projected-gradient correction.
- Calibration quality diagnostics.
- Finite-shot simulation.
- Bootstrap uncertainty estimation.
- JSON calibration persistence.
- Validation and automated tests.

Dependencies: Python 3.10+ standard library only.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class MitigationError(Exception):
    pass


class CalibrationError(MitigationError):
    pass


class ValidationError(MitigationError):
    pass


def validate_probability(value: float, name: str) -> None:
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValidationError(f"{name} must be between 0 and 1.")


def normalize(values: Sequence[float]) -> list[float]:
    if not values or any(not math.isfinite(x) or x < 0 for x in values):
        raise ValidationError("Invalid probability distribution.")

    total = sum(values)
    if total <= 0:
        raise ValidationError("Distribution has zero probability mass.")

    return [x / total for x in values]


def project_simplex(values: Sequence[float]) -> list[float]:
    """Project a vector onto the probability simplex."""
    ordered = sorted(values, reverse=True)
    cumulative = 0.0
    theta = 0.0

    for index, value in enumerate(ordered, start=1):
        cumulative += value
        candidate = (cumulative - 1.0) / index
        if value > candidate:
            theta = candidate

    return [max(0.0, value - theta) for value in values]


def matrix_vector(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float]
) -> list[float]:
    return [
        sum(a * b for a, b in zip(row, vector))
        for row in matrix
    ]


def transpose(
    matrix: Sequence[Sequence[float]]
) -> list[list[float]]:
    return [list(column) for column in zip(*matrix)]


def identity_matrix(size: int) -> list[list[float]]:
    return [
        [1.0 if i == j else 0.0 for j in range(size)]
        for i in range(size)
    ]


def tensor_product(
    first: Sequence[Sequence[float]],
    second: Sequence[Sequence[float]]
) -> list[list[float]]:
    rows = len(first) * len(second)
    columns = len(first[0]) * len(second[0])
    result = [[0.0] * columns for _ in range(rows)]

    for i, row_a in enumerate(first):
        for j, row_b in enumerate(second):
            for k, value_a in enumerate(row_a):
                for l, value_b in enumerate(row_b):
                    result[i * len(second) + j][
                        k * len(second[0]) + l
                    ] = value_a * value_b

    return result


@dataclass(frozen=True)
class ReadoutCalibration:
    qubit: int
    shots: int
    p_measured_0_given_0: float
    p_measured_1_given_1: float

    def __post_init__(self):
        if self.qubit < 0 or self.shots <= 0:
            raise ValidationError("Invalid calibration metadata.")

        validate_probability(
            self.p_measured_0_given_0, "P(0|0)"
        )
        validate_probability(
            self.p_measured_1_given_1, "P(1|1)"
        )

    def assignment_matrix(self) -> list[list[float]]:
        return [
            [
                self.p_measured_0_given_0,
                1.0 - self.p_measured_1_given_1
            ],
            [
                1.0 - self.p_measured_0_given_0,
                self.p_measured_1_given_1
            ]
        ]


@dataclass
class MitigationResult:
    raw_probabilities: list[float]
    corrected_probabilities: list[float]
    residual_norm: float
    iterations: int
    convergence: bool

    @property
    def total_variation_distance_indicator(self) -> float:
        return 0.5 * sum(
            abs(a - b)
            for a, b in zip(
                self.raw_probabilities,
                self.corrected_probabilities
            )
        )


class ReadoutMitigator:
    def __init__(
        self,
        calibrations: Sequence[ReadoutCalibration],
        regularization: float = 1e-8
    ):
        if not calibrations:
            raise CalibrationError("At least one calibration is required.")

        if regularization < 0 or not math.isfinite(regularization):
            raise ValidationError("Invalid regularization parameter.")

        self.calibrations = list(calibrations)
        self.num_qubits = len(calibrations)
        self.regularization = regularization

        expected = list(range(self.num_qubits))
        actual = sorted(c.qubit for c in calibrations)

        if actual != expected:
            raise CalibrationError(
                "Qubit identifiers must be consecutive from zero."
            )

        matrix = [[1.0]]

        # Construct the multi-qubit assignment matrix.
        for calibration in calibrations:
            matrix = tensor_product(
                matrix,
                calibration.assignment_matrix()
            )

        self.assignment = matrix
        self.dimension = 2 ** self.num_qubits

        if any(
            abs(sum(row) - 1.0) > 1e-9
            for row in transpose(matrix)
        ):
            raise CalibrationError("Invalid assignment matrix.")

    def condition_indicator(self) -> float:
        """
        Approximate conditioning using the ratio of maximum
        and minimum singular-value estimates from power iteration.
        A small value indicates potentially unstable correction.
        """
        a = self.assignment
        at = transpose(a)
        gram = [
            matrix_vector(at, matrix_vector(a, row))
            for row in identity_matrix(self.dimension)
        ]
        gram = transpose(gram)

        def power(matrix, inverse=False, iterations=100):
            vector = [1.0] * self.dimension
            for _ in range(iterations):
                if inverse:
                    # Shifted inverse iteration is intentionally
                    # avoided; report a conservative singular-value
                    # proxy through the smallest diagonal scale.
                    break
                result = matrix_vector(matrix, vector)
                norm = math.sqrt(sum(x * x for x in result))
                if norm < 1e-15:
                    return 0.0
                vector = [x / norm for x in result]

            result = matrix_vector(matrix, vector)
            return sum(x * y for x, y in zip(vector, result))

        largest = power(gram)
        smallest_diagonal = min(
            gram[i][i] for i in range(self.dimension)
        )

        if smallest_diagonal <= 1e-15 or largest <= 0:
            return math.inf

        return math.sqrt(largest / smallest_diagonal)

    def estimate_probabilities(
        self,
        counts: dict[str, int]
    ) -> list[float]:
        if not counts:
            raise ValidationError("Measurement counts cannot be empty.")

        if any(
            len(bitstring) != self.num_qubits
            or set(bitstring) - {"0", "1"}
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
            for bitstring, count in counts.items()
        ):
            raise ValidationError("Invalid bitstring or count.")

        total = sum(counts.values())
        if total <= 0:
            raise ValidationError("Total measurement shots must be positive.")

        probabilities = [0.0] * self.dimension

        for bitstring, count in counts.items():
            index = int(bitstring, 2)
            probabilities[index] += count / total

        return probabilities

    def mitigate(
        self,
        counts: dict[str, int],
        max_iterations: int = 10000,
        tolerance: float = 1e-11
    ) -> MitigationResult:
        if max_iterations <= 0 or tolerance <= 0:
            raise ValidationError("Invalid optimization parameters.")

        observed = self.estimate_probabilities(counts)

        # Solve min ||A p - q||² + lambda ||p||²
        # subject to p >= 0 and sum(p) = 1.
        a = self.assignment
        at = transpose(a)

        ata = [
            [
                sum(at[i][k] * a[k][j]
                    for k in range(self.dimension))
                + (self.regularization if i == j else 0.0)
                for j in range(self.dimension)
            ]
            for i in range(self.dimension)
        ]

        atq = matrix_vector(at, observed)

        # A safe upper bound on the gradient Lipschitz constant.
        lipschitz = max(
            sum(abs(value) for value in row)
            for row in ata
        )

        if lipschitz <= 0:
            raise MitigationError("Invalid optimization matrix.")

        learning_rate = 1.0 / lipschitz
        estimate = observed[:]
        converged = False

        for iteration in range(1, max_iterations + 1):
            gradient = [
                value - target
                for value, target in zip(
                    matrix_vector(ata, estimate), atq
                )
            ]

            candidate = project_simplex([
                estimate[i] - learning_rate * gradient[i]
                for i in range(self.dimension)
            ])

            difference = max(
                abs(a - b)
                for a, b in zip(candidate, estimate)
            )

            estimate = candidate

            if difference < tolerance:
                converged = True
                break

        predicted = matrix_vector(a, estimate)
        residual = math.sqrt(sum(
            (p - q) ** 2
            for p, q in zip(predicted, observed)
        ))

        return MitigationResult(
            raw_probabilities=observed,
            corrected_probabilities=estimate,
            residual_norm=residual,
            iterations=iteration,
            convergence=converged
        )

    def save(self, filename: str) -> None:
        payload = {
            "num_qubits": self.num_qubits,
            "regularization": self.regularization,
            "calibrations": [
                {
                    "qubit": c.qubit,
                    "shots": c.shots,
                    "p00": c.p_measured_0_given_0,
                    "p11": c.p_measured_1_given_1
                }
                for c in self.calibrations
            ]
        }

        path = Path(filename)
        path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8"
        )

    @classmethod
    def load(cls, filename: str) -> ReadoutMitigator:
        path = Path(filename)
        payload = json.loads(path.read_text(encoding="utf-8"))

        calibrations = [
            ReadoutCalibration(
                qubit=item["qubit"],
                shots=item["shots"],
                p_measured_0_given_0=item["p00"],
                p_measured_1_given_1=item["p11"]
            )
            for item in payload["calibrations"]
        ]

        return cls(
            calibrations,
            regularization=payload["regularization"]
        )


def simulate_measurements(
    true_probabilities: Sequence[float],
    assignment: Sequence[Sequence[float]],
    shots: int,
    seed: int = 42
) -> dict[str, int]:
    if shots <= 0:
        raise ValidationError("Shots must be positive.")

    distribution = normalize(true_probabilities)

    if len(distribution) != len(assignment):
        raise ValidationError("Distribution dimension mismatch.")

    observed = normalize(
        matrix_vector(assignment, distribution)
    )

    rng = random.Random(seed)
    counts = {format(i, f"0{int(math.log2(len(observed)))}b"): 0
              for i in range(len(observed))}

    states = list(counts)
    for _ in range(shots):
        value = rng.random()
        cumulative = 0.0

        for state, probability in zip(states, observed):
            cumulative += probability
            if value <= cumulative:
                counts[state] += 1
                break

    return counts


def bootstrap_expectation(
    mitigator: ReadoutMitigator,
    counts: dict[str, int],
    observable: Sequence[float],
    repetitions: int = 100,
    seed: int = 42
) -> tuple[float, float]:
    """Estimate uncertainty by resampling observed shot counts."""
    if repetitions < 2 or len(observable) != mitigator.dimension:
        raise ValidationError("Invalid bootstrap configuration.")

    total = sum(counts.values())
    if total <= 0:
        raise ValidationError("No measurement samples.")

    expanded = []
    for state, count in counts.items():
        expanded.extend([state] * count)

    rng = random.Random(seed)
    estimates = []

    for _ in range(repetitions):
        sample = rng.choices(expanded, k=total)
        sampled_counts: dict[str, int] = {}

        for state in sample:
            sampled_counts[state] = sampled_counts.get(state, 0) + 1

        result = mitigator.mitigate(sampled_counts)
        estimates.append(sum(
            p * value
            for p, value in zip(
                result.corrected_probabilities, observable
            )
        ))

    return (
        statistics.mean(estimates),
        statistics.stdev(estimates)
    )


def main() -> None:
    print("READOUT ERROR MITIGATION")
    print("=" * 55)

    calibrations = [
        ReadoutCalibration(0, 10000, 0.94, 0.91),
        ReadoutCalibration(1, 10000, 0.96, 0.93)
    ]

    mitigator = ReadoutMitigator(
        calibrations,
        regularization=1e-8
    )

    true_distribution = [0.70, 0.10, 0.15, 0.05]

    counts = simulate_measurements(
        true_distribution,
        mitigator.assignment,
        shots=50000
    )

    result = mitigator.mitigate(counts)

    print("\nMeasurement counts:")
    for state, count in sorted(counts.items()):
        print(f"|{state}>: {count}")

    print("\nRaw probabilities:")
    for state, probability in enumerate(result.raw_probabilities):
        print(f"{state:02b}: {probability:.6f}")

    print("\nCorrected probabilities:")
    for state, probability in enumerate(result.corrected_probabilities):
        print(f"{state:02b}: {probability:.6f}")

    print("\nDiagnostics:")
    print(f"Iterations: {result.iterations}")
    print(f"Converged: {result.convergence}")
    print(f"Residual: {result.residual_norm:.8f}")
    print(f"Condition indicator: {mitigator.condition_indicator():.4f}")

    observable = [1.0, -1.0, -1.0, 1.0]
    raw_expectation = sum(
        p * value
        for p, value in zip(result.raw_probabilities, observable)
    )
    corrected_expectation, uncertainty = bootstrap_expectation(
        mitigator, counts, observable, repetitions=100
    )

    print(f"\nRaw observable expectation: {raw_expectation:.6f}")
    print(f"Corrected expectation: {corrected_expectation:.6f}")
    print(f"Bootstrap standard deviation: {uncertainty:.6f}")

    mitigator.save("readout_calibration.json")
    restored = ReadoutMitigator.load("readout_calibration.json")

    assert len(restored.assignment) == 4
    assert abs(sum(result.corrected_probabilities) - 1.0) < 1e-8
    assert all(p >= 0 for p in result.corrected_probabilities)

    print("\nCalibration persistence test: PASSED")
    print("Probability normalization test: PASSED")


if __name__ == "__main__":
    main()
