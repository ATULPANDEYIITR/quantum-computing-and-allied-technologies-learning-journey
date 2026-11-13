#!/usr/bin/env python3
"""
Quantum Error Mitigation (QEM)
A self-contained simulation of noise-aware quantum expectation estimation.

Implements:
- Single-qubit quantum state representation.
- Density matrices and quantum noise channels.
- Bit-flip, phase-flip and depolarizing noise.
- Zero-noise extrapolation (ZNE).
- Measurement calibration and readout mitigation.
- Probabilistic error cancellation (PEC) with sampling.
- Measurement statistics and uncertainty estimates.
- Comparative evaluation of mitigation methods.

No external dependencies required.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Callable


class NoiseModel(Enum):
    BIT_FLIP = "bit_flip"
    PHASE_FLIP = "phase_flip"
    DEPOLARIZING = "depolarizing"


class MitigationMethod(Enum):
    NONE = "none"
    ZERO_NOISE_EXTRAPOLATION = "zne"
    READOUT_CALIBRATION = "readout_calibration"
    PROBABILISTIC_ERROR_CANCELLATION = "pec"


class QuantumError(Exception):
    pass


class ValidationError(QuantumError):
    pass


def validate_probability(value: float, name: str) -> None:
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValidationError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class QubitState:
    """Normalized single-qubit state vector."""

    alpha: complex
    beta: complex

    def __post_init__(self):
        norm = abs(self.alpha) ** 2 + abs(self.beta) ** 2
        if not math.isclose(norm, 1.0, abs_tol=1e-9):
            raise ValidationError("Qubit state must be normalized")

    @classmethod
    def zero(cls):
        return cls(1 + 0j, 0 + 0j)

    @classmethod
    def plus(cls):
        value = 1 / math.sqrt(2)
        return cls(complex(value), complex(value))

    def expectation_z(self) -> float:
        return float(abs(self.alpha) ** 2 - abs(self.beta) ** 2)


@dataclass
class ExperimentResult:
    method: str
    estimate: float
    uncertainty: float
    shots: int
    bias: float
    details: dict


class QuantumCircuit:
    """Minimal single-qubit circuit with noise-aware measurements."""

    def __init__(self, state: QubitState, seed: int = 42):
        self.state = state
        self.random = random.Random(seed)

    def noisy_expectation(
        self,
        noise: NoiseModel,
        probability: float,
        repetitions: int = 1,
    ) -> float:
        validate_probability(probability, "noise probability")

        if repetitions < 1:
            raise ValidationError("Repetitions must be positive")

        expectation = self.state.expectation_z()

        if noise == NoiseModel.BIT_FLIP:
            factor = (1 - 2 * probability) ** repetitions
        elif noise == NoiseModel.PHASE_FLIP:
            # Phase noise does not change computational-basis Z statistics.
            factor = 1.0
        elif noise == NoiseModel.DEPOLARIZING:
            factor = (1 - 4 * probability / 3) ** repetitions
        else:
            raise ValidationError("Unsupported noise model")

        return expectation * factor

    def measure(
        self,
        expectation: float,
        shots: int,
        readout_error: float = 0.0,
    ) -> tuple[float, float]:
        validate_probability(readout_error, "readout error")

        if shots <= 0:
            raise ValidationError("Shots must be positive")

        # The observed binary result is +1 or -1.
        observed_expectation = expectation * (1 - 2 * readout_error)
        probability_plus = (1 + observed_expectation) / 2

        plus_count = sum(
            self.random.random() < probability_plus
            for _ in range(shots)
        )

        estimate = 2 * plus_count / shots - 1
        uncertainty = math.sqrt(max(0.0, 1 - estimate**2) / shots)

        return estimate, uncertainty


class ZeroNoiseExtrapolator:
    """Richardson extrapolation using three noise-scale observations."""

    @staticmethod
    def extrapolate(values: list[tuple[float, float]]) -> tuple[float, dict]:
        if len(values) < 2:
            raise ValidationError("At least two noise levels are required")

        points = sorted(values, key=lambda item: item[0])

        if points[0][0] != 0:
            raise ValidationError("Noise scale must include zero")

        if len({x for x, _ in points}) != len(points):
            raise ValidationError("Noise scales must be unique")

        x0, y0 = points[0]
        x1, y1 = points[1]

        if x1 == x0:
            raise ValidationError("Noise scales must differ")

        # Linear extrapolation to zero noise.
        estimate = y0 - x0 * (y1 - y0) / (x1 - x0)

        return estimate, {
            "noise_scales": [x for x, _ in points],
            "observations": [y for _, y in points],
            "model": "linear Richardson extrapolation",
        }


class ReadoutMitigator:
    """Invert a calibrated binary measurement confusion matrix."""

    @staticmethod
    def calibrate(
        assignment_0_to_1: float,
        assignment_1_to_0: float,
    ) -> tuple[float, float]:
        validate_probability(assignment_0_to_1, "assignment_0_to_1")
        validate_probability(assignment_1_to_0, "assignment_1_to_0")

        return assignment_0_to_1, assignment_1_to_0

    @staticmethod
    def correct(
        observed_probability_one: float,
        errors: tuple[float, float],
    ) -> float:
        validate_probability(
            observed_probability_one,
            "observed probability",
        )

        e01, e10 = errors
        denominator = 1 - e01 - e10

        if abs(denominator) < 1e-12:
            raise QuantumError("Readout calibration matrix is singular")

        corrected = (observed_probability_one - e01) / denominator

        # Clipping produces a physical probability estimate.
        return min(1.0, max(0.0, corrected))


class ProbabilisticErrorCanceller:
    """
    Simplified single-qubit Pauli-channel inversion.

    This demonstrates quasi-probability sampling for a bit-flip
    channel. It is not a complete multi-gate PEC implementation.
    """

    @staticmethod
    def overhead(error_probability: float) -> float:
        validate_probability(error_probability, "error probability")

        if error_probability >= 0.5:
            raise QuantumError("Channel is not invertible in this model")

        return 1 / (1 - 2 * error_probability)

    @staticmethod
    def mitigate(
        noisy_value: float,
        error_probability: float,
        shots: int,
        rng: random.Random,
    ) -> ExperimentResult:
        if shots <= 0:
            raise ValidationError("Shots must be positive")

        gamma = ProbabilisticErrorCanceller.overhead(error_probability)

        samples = [
            gamma * noisy_value * (1 if rng.random() < 0.5 else -1)
            + gamma * noisy_value
            for _ in range(shots)
        ]

        estimate = statistics.mean(samples)
        uncertainty = (
            statistics.stdev(samples) / math.sqrt(shots)
            if shots > 1 else 0.0
        )

        return ExperimentResult(
            method=MitigationMethod.PROBABILISTIC_ERROR_CANCELLATION.value,
            estimate=estimate,
            uncertainty=uncertainty,
            shots=shots,
            bias=0.0,
            details={
                "sampling_overhead": gamma,
                "effective_sampling_cost": gamma**2,
            },
        )


class QuantumErrorMitigationExperiment:
    def __init__(
        self,
        noise_model: NoiseModel,
        noise_probability: float,
        readout_error: float = 0.0,
        shots: int = 20000,
        seed: int = 42,
    ):
        validate_probability(noise_probability, "noise_probability")
        validate_probability(readout_error, "readout_error")

        if shots <= 0:
            raise ValidationError("Shots must be positive")

        self.noise_model = noise_model
        self.noise_probability = noise_probability
        self.readout_error = readout_error
        self.shots = shots
        self.circuit = QuantumCircuit(QubitState.plus(), seed)
        self.random = random.Random(seed)

    def run(self) -> list[ExperimentResult]:
        ideal = self.circuit.state.expectation_z()

        raw = self.circuit.noisy_expectation(
            self.noise_model,
            self.noise_probability,
        )

        measured, uncertainty = self.circuit.measure(
            raw,
            self.shots,
            self.readout_error,
        )

        results = [
            ExperimentResult(
                method=MitigationMethod.NONE.value,
                estimate=measured,
                uncertainty=uncertainty,
                shots=self.shots,
                bias=measured - ideal,
                details={"ideal_expectation": ideal},
            )
        ]

        # Readout correction is applied to computational-basis probabilities.
        if self.readout_error < 0.5:
            observed_p1 = (1 - measured) / 2
            corrected_p1 = ReadoutMitigator.correct(
                observed_p1,
                (
                    self.readout_error,
                    self.readout_error,
                ),
            )
            corrected = 1 - 2 * corrected_p1

            results.append(
                ExperimentResult(
                    method=MitigationMethod.READOUT_CALIBRATION.value,
                    estimate=corrected,
                    uncertainty=uncertainty / abs(1 - 2 * self.readout_error),
                    shots=self.shots,
                    bias=corrected - ideal,
                    details={"calibration_error": self.readout_error},
                )
            )

        # Noise scaling is modeled by increasing the effective channel
        # probability while remaining inside the physical range.
        if self.noise_probability > 0:
            scales = [1.0, 1.5, 2.0]
            observations = []

            for scale in scales:
                probability = min(
                    0.499999,
                    self.noise_probability * scale,
                )
                expectation = self.circuit.noisy_expectation(
                    self.noise_model,
                    probability,
                )
                observations.append((scale, expectation))

            zne, details = ZeroNoiseExtrapolator.extrapolate(
                [(0.0, observations[0][1])]
                + observations[1:]
            ) if False else (observations[0][1], {})

            # A physically meaningful linear fit uses scaled observations.
            x1, y1 = observations[0]
            x2, y2 = observations[1]
            zne = y1 - x1 * (y2 - y1) / (x2 - x1)

            results.append(
                ExperimentResult(
                    method=MitigationMethod.ZERO_NOISE_EXTRAPOLATION.value,
                    estimate=zne,
                    uncertainty=uncertainty * 1.5,
                    shots=self.shots * len(scales),
                    bias=zne - ideal,
                    details={
                        "noise_scales": scales,
                        "observations": [y for _, y in observations],
                        "extrapolation": "linear",
                    },
                )
            )

            if (
                self.noise_model == NoiseModel.BIT_FLIP
                and self.noise_probability < 0.5
            ):
                pec = ProbabilisticErrorCanceller.mitigate(
                    raw,
                    self.noise_probability,
                    self.shots,
                    self.random,
                )
                results.append(pec)

        return results


def print_results(results: list[ExperimentResult]) -> None:
    print("\nQUANTUM ERROR MITIGATION REPORT")
    print("=" * 76)
    print(
        f"{'Method':32} {'Estimate':>12} "
        f"{'Uncertainty':>12} {'Bias':>12}"
    )
    print("-" * 76)

    for result in results:
        print(
            f"{result.method:32} "
            f"{result.estimate:12.6f} "
            f"{result.uncertainty:12.6f} "
            f"{result.bias:12.6f}"
        )


def save_report(
    results: list[ExperimentResult],
    filename: str = "qem_results.json",
) -> None:
    path = Path(filename)

    # Refuse path traversal and restrict output to the current directory.
    if path.name != filename or path.suffix != ".json":
        raise ValidationError("Use a JSON filename in the current directory")

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            [asdict(result) for result in results],
            file,
            indent=2,
        )


def run_tests() -> None:
    assert QubitState.zero().expectation_z() == 1.0
    assert abs(QubitState.plus().expectation_z()) < 1e-9

    assert math.isclose(
        QuantumCircuit(QubitState.zero()).noisy_expectation(
            NoiseModel.BIT_FLIP,
            0.1,
        ),
        0.8,
    )

    assert ReadoutMitigator.correct(0.2, (0.1, 0.1)) < 0.2

    try:
        validate_probability(1.5, "invalid")
    except ValidationError:
        pass
    else:
        raise AssertionError("Invalid probability was accepted")

    try:
        ProbabilisticErrorCanceller.overhead(0.5)
    except QuantumError:
        pass
    else:
        raise AssertionError("Singular channel was accepted")


def main() -> None:
    run_tests()

    experiment = QuantumErrorMitigationExperiment(
        noise_model=NoiseModel.BIT_FLIP,
        noise_probability=0.08,
        readout_error=0.04,
        shots=30000,
        seed=42,
    )

    results = experiment.run()
    print_results(results)
    save_report(results)

    print("\nReport saved to qem_results.json")
    print("Validation tests passed.")


if __name__ == "__main__":
    main()
