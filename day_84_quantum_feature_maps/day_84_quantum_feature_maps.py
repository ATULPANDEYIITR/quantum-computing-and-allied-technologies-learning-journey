#!/usr/bin/env python3
"""
Quantum Feature Maps: Encoding Classical Data into Quantum States

Implements:
1. Classical feature validation and normalization.
2. Single-qubit angle encoding.
3. Multi-qubit quantum feature maps.
4. Hadamard-style rotational feature maps.
5. ZZ entanglement feature maps.
6. Statevector simulation.
7. Quantum kernel evaluation using state fidelity.
8. Pairwise quantum kernel matrices.
9. Numerical validation and reproducibility.
10. Feature-map comparison and execution reporting.

Uses only the Python standard library.
"""

from __future__ import annotations

import cmath
import json
import math
import random
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Sequence


EPSILON = 1e-10


class FeatureMapError(Exception):
    """Base exception for quantum feature-map operations."""


class ValidationError(FeatureMapError):
    """Invalid classical input or circuit configuration."""


class SimulationError(FeatureMapError):
    """Invalid quantum state or simulation operation."""


class EncodingType(Enum):
    ANGLE = "angle"
    ZZ = "zz"
    IQP = "iqp"


@dataclass(frozen=True)
class FeatureVector:
    values: tuple[float, ...]

    def __post_init__(self):
        if not self.values:
            raise ValidationError("Feature vector cannot be empty.")

        if any(not math.isfinite(x) for x in self.values):
            raise ValidationError("Features must be finite numbers.")

    @classmethod
    def from_list(cls, values: Sequence[float]):
        return cls(tuple(float(x) for x in values))

    def normalize(self, lower=-math.pi, upper=math.pi):
        """Map each feature independently into a bounded interval."""
        if lower >= upper:
            raise ValidationError("Invalid normalization interval.")

        minimum = min(self.values)
        maximum = max(self.values)

        if maximum == minimum:
            return FeatureVector(tuple(
                (lower + upper) / 2 for _ in self.values
            ))

        normalized = tuple(
            lower + (x - minimum) * (upper - lower)
            / (maximum - minimum)
            for x in self.values
        )

        return FeatureVector(normalized)


@dataclass(frozen=True)
class FeatureMapConfig:
    encoding: EncodingType
    repetitions: int = 1
    entanglement_strength: float = 1.0

    def __post_init__(self):
        if self.repetitions < 1:
            raise ValidationError("Repetitions must be positive.")

        if not math.isfinite(self.entanglement_strength):
            raise ValidationError("Entanglement strength must be finite.")


@dataclass
class QuantumState:
    amplitudes: list[complex]
    qubits: int

    def __post_init__(self):
        if self.qubits < 1:
            raise ValidationError("At least one qubit is required.")

        if len(self.amplitudes) != 2 ** self.qubits:
            raise ValidationError("Statevector dimension mismatch.")

        if any(
            not math.isfinite(a.real) or not math.isfinite(a.imag)
            for a in self.amplitudes
        ):
            raise SimulationError("Non-finite state amplitudes.")

        self.validate()

    def validate(self):
        norm = sum(abs(a) ** 2 for a in self.amplitudes)

        if abs(norm - 1.0) > 1e-8:
            raise SimulationError(
                f"State is not normalized. Norm squared: {norm}"
            )

    def probabilities(self):
        return [abs(a) ** 2 for a in self.amplitudes]

    def measure_probabilities(self):
        """Return computational-basis probabilities."""
        return {
            format(index, f"0{self.qubits}b"): probability
            for index, probability in enumerate(self.probabilities())
        }

    def sample_measurements(self, shots=1000, seed=42):
        if shots < 1:
            raise ValidationError("Shots must be positive.")

        generator = random.Random(seed)
        probabilities = self.probabilities()

        counts = {
            format(i, f"0{self.qubits}b"): 0
            for i in range(len(probabilities))
        }

        for _ in range(shots):
            outcome = generator.choices(
                range(len(probabilities)),
                weights=probabilities,
                k=1
            )[0]

            counts[format(outcome, f"0{self.qubits}b")] += 1

        return counts


class QuantumFeatureMap:
    """
    Statevector simulator for rotational and diagonal feature maps.

    State convention:
        |0...0> is represented by amplitude vector [1, 0, ...].
    """

    def __init__(self, config: FeatureMapConfig):
        self.config = config

    @staticmethod
    def apply_ry(state: list[complex], qubit: int, theta: float):
        """Apply a real Y-axis rotation to one qubit."""
        dimension = len(state)
        mask = 1 << qubit

        cosine = math.cos(theta / 2)
        sine = math.sin(theta / 2)

        for index in range(dimension):
            if index & mask:
                continue

            paired = index | mask
            zero = state[index]
            one = state[paired]

            state[index] = cosine * zero - sine * one
            state[paired] = sine * zero + cosine * one

    @staticmethod
    def apply_rz(state: list[complex], qubit: int, theta: float):
        """Apply a diagonal Z-axis rotation."""
        mask = 1 << qubit

        zero_phase = cmath.exp(-0.5j * theta)
        one_phase = cmath.exp(0.5j * theta)

        for index in range(len(state)):
            state[index] *= (
                one_phase if index & mask else zero_phase
            )

    @staticmethod
    def apply_zz(state: list[complex], first: int, second: int, theta: float):
        """
        Apply exp(-i * theta * Z(first)Z(second) / 2).

        The gate is diagonal, so it changes phases without
        changing computational-basis probabilities directly.
        """
        if first == second:
            raise ValidationError("ZZ gate requires distinct qubits.")

        first_mask = 1 << first
        second_mask = 1 << second

        for index in range(len(state)):
            first_bit = bool(index & first_mask)
            second_bit = bool(index & second_mask)

            eigenvalue = (
                -1 if first_bit != second_bit else 1
            )

            state[index] *= cmath.exp(
                -0.5j * theta * eigenvalue
            )

    def encode(self, features: FeatureVector) -> QuantumState:
        values = features.values
        qubits = len(values)

        if qubits > 20:
            raise ValidationError(
                "Exact statevector simulation is limited to 20 qubits."
            )

        state = [0j] * (2 ** qubits)
        state[0] = 1.0 + 0j

        for _ in range(self.config.repetitions):
            for qubit, value in enumerate(values):
                if self.config.encoding == EncodingType.ANGLE:
                    self.apply_ry(state, qubit, value)

                elif self.config.encoding == EncodingType.ZZ:
                    self.apply_ry(state, qubit, 2 * value)
                    self.apply_rz(state, qubit, value)

                elif self.config.encoding == EncodingType.IQP:
                    self.apply_ry(state, qubit, value)
                    self.apply_rz(state, qubit, 2 * value)

            if self.config.encoding in (
                EncodingType.ZZ,
                EncodingType.IQP
            ):
                for first in range(qubits):
                    for second in range(first + 1, qubits):
                        if self.config.encoding == EncodingType.ZZ:
                            angle = (
                                self.config.entanglement_strength
                                * values[first]
                                * values[second]
                            )
                        else:
                            angle = (
                                2 * values[first] * values[second]
                            )

                        self.apply_zz(
                            state, first, second, angle
                        )

        return QuantumState(state, qubits)


class QuantumKernel:
    """Compute state overlaps and fidelity-based kernel values."""

    @staticmethod
    def inner_product(
        first: QuantumState,
        second: QuantumState
    ) -> complex:
        if first.qubits != second.qubits:
            raise ValidationError(
                "Quantum states must have equal dimensions."
            )

        return sum(
            a.conjugate() * b
            for a, b in zip(first.amplitudes, second.amplitudes)
        )

    @classmethod
    def fidelity(
        cls,
        first: QuantumState,
        second: QuantumState
    ) -> float:
        overlap = cls.inner_product(first, second)
        result = abs(overlap) ** 2

        return min(1.0, max(0.0, result))

    @classmethod
    def kernel_matrix(
        cls,
        states: Sequence[QuantumState]
    ) -> list[list[float]]:
        matrix = []

        for first in states:
            row = [
                cls.fidelity(first, second)
                for second in states
            ]
            matrix.append(row)

        return matrix


def validate_kernel_matrix(matrix):
    """Check symmetry, diagonal normalization and bounded values."""
    size = len(matrix)

    for row in matrix:
        if len(row) != size:
            raise ValidationError("Kernel matrix must be square.")

    for i in range(size):
        if abs(matrix[i][i] - 1.0) > 1e-8:
            raise SimulationError("Kernel diagonal must equal one.")

        for j in range(size):
            if not 0 <= matrix[i][j] <= 1:
                raise SimulationError("Kernel value outside [0, 1].")

            if abs(matrix[i][j] - matrix[j][i]) > 1e-8:
                raise SimulationError("Kernel matrix is asymmetric.")

    return True


def run_experiment():
    print("=" * 65)
    print("QUANTUM FEATURE MAP EXPERIMENT")
    print("=" * 65)

    dataset = [
        [0.2, 0.4, 0.6],
        [0.3, 0.7, 0.5],
        [0.8, 0.2, 0.9],
        [0.9, 0.6, 0.1],
    ]

    vectors = [
        FeatureVector.from_list(row)
        for row in dataset
    ]

    print("\n1. Classical input")
    for index, vector in enumerate(vectors):
        print(f"Sample {index}: {vector.values}")

    print("\n2. Feature normalization")
    normalized = [vector.normalize() for vector in vectors]

    for index, vector in enumerate(normalized):
        print(f"Normalized {index}: {vector.values}")

    for encoding in EncodingType:
        print(f"\n3. Feature map: {encoding.value.upper()}")

        config = FeatureMapConfig(
            encoding=encoding,
            repetitions=2,
            entanglement_strength=0.75
        )

        feature_map = QuantumFeatureMap(config)

        states = [
            feature_map.encode(vector)
            for vector in normalized
        ]

        for index, state in enumerate(states):
            print(
                f"Sample {index}: "
                f"qubits={state.qubits}, "
                f"dimension={len(state.amplitudes)}, "
                f"norm={sum(state.probabilities()):.8f}"
            )

        matrix = QuantumKernel.kernel_matrix(states)
        validate_kernel_matrix(matrix)

        print("\nQuantum kernel matrix:")

        for row in matrix:
            print(" ".join(f"{value:.5f}" for value in row))

        print("\nMeasurement simulation:")
        print(json.dumps(
            states[0].sample_measurements(shots=1000),
            indent=2
        ))

    print("\n4. Identical-input fidelity test")

    feature_map = QuantumFeatureMap(
        FeatureMapConfig(EncodingType.ZZ)
    )

    state = feature_map.encode(normalized[0])

    fidelity = QuantumKernel.fidelity(state, state)

    assert abs(fidelity - 1.0) < EPSILON

    print(f"Self-fidelity: {fidelity:.8f}")

    print("\n5. Distinct-input fidelity")

    second = feature_map.encode(normalized[1])

    print(
        "Fidelity:",
        f"{QuantumKernel.fidelity(state, second):.8f}"
    )

    print("\n6. Invalid-input handling")

    try:
        FeatureVector.from_list([0.1, float("nan")])
    except ValidationError as error:
        print("Correctly rejected:", error)

    try:
        FeatureMapConfig(EncodingType.ANGLE, repetitions=0)
    except ValidationError as error:
        print("Correctly rejected:", error)

    print("\nExperiment completed successfully.")


if __name__ == "__main__":
    run_experiment()
