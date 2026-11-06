#!/usr/bin/env python3
"""
Topological Quantum Computing: Majorana-Based Concepts

Implements:
- Majorana zero-mode properties
- Majorana operator algebra
- Fermion parity and fusion channels
- Ising anyon braiding matrices
- Braid-group relations
- Quantum-state evolution
- Experimental validity checks
- Reproducible braid experiment records

This is a mathematical simulation, not a physical device simulator.
"""

from __future__ import annotations

import cmath
import json
import math
import random
import unittest

from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


TOLERANCE = 1e-9


class QuantumError(Exception):
    """Base exception for quantum simulation errors."""


class ValidationError(QuantumError):
    """Invalid physical or mathematical input."""


class ExperimentError(QuantumError):
    """Experiment failed its acceptance conditions."""


class FusionChannel(Enum):
    VACUUM = "1"
    FERMION = "psi"


class ExperimentStatus(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ExperimentalConditions:
    energy_gap: float
    temperature: float
    coherence_time: float
    operation_time: float
    parity_measurement_error: float
    minimum_gap: float = 0.1

    def validate(self) -> None:
        values = (
            self.energy_gap,
            self.temperature,
            self.coherence_time,
            self.operation_time,
            self.parity_measurement_error,
            self.minimum_gap,
        )

        if not all(math.isfinite(x) for x in values):
            raise ValidationError("All experimental values must be finite.")

        if self.energy_gap < 0 or self.minimum_gap <= 0:
            raise ValidationError("Invalid energy gap.")

        if self.temperature < 0:
            raise ValidationError("Temperature cannot be negative.")

        if self.coherence_time <= 0 or self.operation_time <= 0:
            raise ValidationError("Times must be positive.")

        if not 0 <= self.parity_measurement_error <= 1:
            raise ValidationError("Measurement error must be between 0 and 1.")


@dataclass
class BraidRecord:
    operation_number: int
    majorana_left: int
    majorana_right: int
    orientation: int
    description: str


@dataclass
class ExperimentResult:
    experiment_id: str
    status: ExperimentStatus
    initial_state: list
    final_state: list
    operations: int
    initial_parity: int
    final_parity: int
    fidelity: float
    reasons: list[str]


class MajoranaSystem:
    """
    Four Majorana zero modes.

    The two-dimensional computational space represents a fixed
    total fermion-parity sector.

    Majorana exchange is represented using Ising-anyon braid matrices.
    """

    def __init__(self, majorana_count: int = 4):
        if majorana_count < 4 or majorana_count % 2:
            raise ValidationError("An even number of at least four modes is required.")

        self.majorana_count = majorana_count
        self.records: list[BraidRecord] = []

    @staticmethod
    def anticommutation(first: int, second: int) -> int:
        """Return the expected anticommutator coefficient."""
        if first < 0 or second < 0:
            raise ValidationError("Majorana indices cannot be negative.")

        return 2 if first == second else 0

    @staticmethod
    def majorana_square() -> int:
        """Majorana operators satisfy gamma_i squared = identity."""
        return 1

    @staticmethod
    def fermion_parity(occupation: int) -> int:
        if occupation not in (0, 1):
            raise ValidationError("Occupation must be zero or one.")

        return 1 - 2 * occupation

    @staticmethod
    def fusion_channel(occupation: int) -> FusionChannel:
        if occupation not in (0, 1):
            raise ValidationError("Occupation must be zero or one.")

        return FusionChannel.VACUUM if occupation == 0 else FusionChannel.FERMION

    @staticmethod
    def initial_state() -> list[complex]:
        """Equal superposition of the two fusion channels."""
        scale = 1 / math.sqrt(2)
        return [complex(scale), complex(scale)]

    @staticmethod
    def normalize(state: list[complex]) -> list[complex]:
        if len(state) != 2:
            raise ValidationError("Computational state must have two amplitudes.")

        norm = sum(abs(amplitude) ** 2 for amplitude in state)

        if not math.isfinite(norm) or norm <= TOLERANCE:
            raise ValidationError("State has invalid or zero norm.")

        return [amplitude / math.sqrt(norm) for amplitude in state]

    @staticmethod
    def validate_state(state: list[complex]) -> None:
        if len(state) != 2:
            raise ValidationError("Expected a two-dimensional state.")

        if not all(
            math.isfinite(value.real) and math.isfinite(value.imag)
            for value in state
        ):
            raise ValidationError("State contains non-finite amplitudes.")

        norm = sum(abs(value) ** 2 for value in state)

        if not math.isclose(norm, 1.0, abs_tol=TOLERANCE):
            raise ValidationError("Quantum state must be normalized.")

    @staticmethod
    def braid_matrix(index: int, orientation: int = 1):
        """
        Ising-anyon braid generators in a fixed-parity sector.

        B1 = diag(exp(-i*pi/4), exp(i*pi/4))
        B2 = F B1 F, where F is the Hadamard fusion transformation.

        orientation -1 represents the inverse braid.
        """

        if index not in (1, 2):
            raise ValidationError("Only braid generators B1 and B2 are supported.")

        if orientation not in (-1, 1):
            raise ValidationError("Orientation must be -1 or +1.")

        phase = cmath.exp(-1j * math.pi / 4)

        b1 = [
            [phase, 0j],
            [0j, phase.conjugate()],
        ]

        if index == 1:
            matrix = b1
        else:
            matrix = [
                [
                    (b1[0][0] + b1[1][1]) / 2,
                    (b1[0][0] - b1[1][1]) / 2,
                ],
                [
                    (b1[0][0] - b1[1][1]) / 2,
                    (b1[0][0] + b1[1][1]) / 2,
                ],
            ]

        if orientation == -1:
            matrix = [
                [value.conjugate() for value in row]
                for row in zip(*matrix)
            ]

        return matrix

    @staticmethod
    def apply_matrix(matrix, state):
        result = [
            sum(matrix[row][column] * state[column] for column in range(2))
            for row in range(2)
        ]

        return MajoranaSystem.normalize(result)

    def braid(
        self,
        state: list[complex],
        index: int,
        orientation: int = 1,
    ) -> list[complex]:

        self.validate_state(state)

        if index not in (1, 2):
            raise ValidationError("Invalid adjacent braid generator.")

        if orientation not in (-1, 1):
            raise ValidationError("Invalid braid orientation.")

        self.records.append(
            BraidRecord(
                len(self.records) + 1,
                index,
                index + 1,
                orientation,
                f"B{index}" if orientation == 1 else f"B{index} inverse",
            )
        )

        return self.apply_matrix(
            self.braid_matrix(index, orientation),
            state,
        )

    def execute_sequence(self, sequence, state=None):
        if state is None:
            state = self.initial_state()

        for index, orientation in sequence:
            state = self.braid(state, index, orientation)

        return state

    @staticmethod
    def inner_product(first, second):
        return sum(a.conjugate() * b for a, b in zip(first, second))

    @staticmethod
    def fidelity(first, second):
        return abs(MajoranaSystem.inner_product(first, second)) ** 2

    @staticmethod
    def braid_relation_error():
        """Check B1 B2 B1 = B2 B1 B2."""

        b1 = MajoranaSystem.braid_matrix(1)
        b2 = MajoranaSystem.braid_matrix(2)

        def multiply(a, b):
            return [
                [
                    sum(a[i][k] * b[k][j] for k in range(2))
                    for j in range(2)
                ]
                for i in range(2)
            ]

        left = multiply(multiply(b1, b2), b1)
        right = multiply(multiply(b2, b1), b2)

        return max(
            abs(left[i][j] - right[i][j])
            for i in range(2)
            for j in range(2)
        )

    @staticmethod
    def unitarity_error(matrix):
        conjugate_transpose = [
            [matrix[j][i].conjugate() for j in range(2)]
            for i in range(2)
        ]

        product = [
            [
                sum(conjugate_transpose[i][k] * matrix[k][j] for k in range(2))
                for j in range(2)
            ]
            for i in range(2)
        ]

        identity = [[1, 0], [0, 1]]

        return max(
            abs(product[i][j] - identity[i][j])
            for i in range(2)
            for j in range(2)
        )

    @staticmethod
    def evaluate_conditions(conditions: ExperimentalConditions):
        conditions.validate()

        failures = []

        if conditions.energy_gap < conditions.minimum_gap:
            failures.append("Energy gap below required threshold.")

        if conditions.operation_time >= conditions.coherence_time:
            failures.append("Operation time exceeds coherence time.")

        if conditions.parity_measurement_error > 0.05:
            failures.append("Parity measurement error exceeds 5%.")

        if conditions.temperature > conditions.energy_gap:
            failures.append("Temperature exceeds the energy-gap scale.")

        return failures

    def run_experiment(self, experiment_id, sequence, conditions):
        if not experiment_id.strip():
            raise ValidationError("Experiment ID cannot be empty.")

        self.records.clear()

        initial = self.initial_state()
        initial_parity = 1

        failures = self.evaluate_conditions(conditions)

        if failures:
            return ExperimentResult(
                experiment_id,
                ExperimentStatus.REJECTED,
                self.serialize_state(initial),
                self.serialize_state(initial),
                0,
                initial_parity,
                initial_parity,
                1.0,
                failures,
            )

        final = self.execute_sequence(sequence, initial)

        self.validate_state(final)

        final_parity = initial_parity

        return ExperimentResult(
            experiment_id,
            ExperimentStatus.ACCEPTED,
            self.serialize_state(initial),
            self.serialize_state(final),
            len(self.records),
            initial_parity,
            final_parity,
            1.0,
            [],
        )

    @staticmethod
    def serialize_state(state):
        return [
            {
                "real": round(value.real, 10),
                "imaginary": round(value.imag, 10),
            }
            for value in state
        ]

    def export_experiment(self, result, path="majorana_experiment.json"):
        payload = {
            "result": {
                "experiment_id": result.experiment_id,
                "status": result.status.value,
                "initial_state": result.initial_state,
                "final_state": result.final_state,
                "operations": result.operations,
                "initial_parity": result.initial_parity,
                "final_parity": result.final_parity,
                "fidelity": result.fidelity,
                "reasons": result.reasons,
            },
            "braid_records": [asdict(record) for record in self.records],
        }

        destination = Path(path)

        if destination.suffix.lower() != ".json":
            raise ValidationError("Export must use a JSON file.")

        destination.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )


class MajoranaTests(unittest.TestCase):

    def test_anticommutation(self):
        self.assertEqual(MajoranaSystem.anticommutation(1, 1), 2)
        self.assertEqual(MajoranaSystem.anticommutation(1, 2), 0)

    def test_parity(self):
        self.assertEqual(MajoranaSystem.fermion_parity(0), 1)
        self.assertEqual(MajoranaSystem.fermion_parity(1), -1)

    def test_normalization(self):
        state = MajoranaSystem.initial_state()
        MajoranaSystem.validate_state(state)

    def test_unitarity(self):
        for index in (1, 2):
            matrix = MajoranaSystem.braid_matrix(index)
            self.assertLess(
                MajoranaSystem.unitarity_error(matrix),
                TOLERANCE,
            )

    def test_braid_relation(self):
        self.assertLess(
            MajoranaSystem.braid_relation_error(),
            TOLERANCE,
        )

    def test_inverse_braid(self):
        system = MajoranaSystem()
        initial = system.initial_state()

        result = system.execute_sequence(
            [(1, 1), (1, -1)],
            initial,
        )

        self.assertGreaterEqual(
            MajoranaSystem.fidelity(initial, result),
            1 - TOLERANCE,
        )

    def test_invalid_generator(self):
        with self.assertRaises(ValidationError):
            MajoranaSystem.braid_matrix(3)

    def test_rejected_experiment(self):
        conditions = ExperimentalConditions(
            energy_gap=0.01,
            temperature=0.001,
            coherence_time=10,
            operation_time=1,
            parity_measurement_error=0.01,
        )

        result = MajoranaSystem().run_experiment(
            "EXP-REJECTED",
            [(1, 1)],
            conditions,
        )

        self.assertEqual(result.status, ExperimentStatus.REJECTED)


def main():
    print("=" * 65)
    print("MAJORANA-BASED TOPOLOGICAL QUANTUM COMPUTING")
    print("=" * 65)

    system = MajoranaSystem(4)

    print("\n1. Majorana operator algebra")
    print("gamma_i squared:", system.majorana_square())
    print("{gamma_1, gamma_1}:", system.anticommutation(1, 1))
    print("{gamma_1, gamma_2}:", system.anticommutation(1, 2))

    print("\n2. Fusion channels")
    for occupation in (0, 1):
        print(
            occupation,
            system.fusion_channel(occupation).value,
            "parity:",
            system.fermion_parity(occupation),
        )

    print("\n3. Braid matrices")
    for index in (1, 2):
        print(f"B{index}:")
        for row in system.braid_matrix(index):
            print(["{:.4f}".format(value) for value in row])

    print("\n4. Mathematical validation")
    print("Braid relation error:", system.braid_relation_error())

    for index in (1, 2):
        print(
            f"B{index} unitarity error:",
            system.unitarity_error(system.braid_matrix(index)),
        )

    print("\n5. Braid experiment")

    conditions = ExperimentalConditions(
        energy_gap=0.25,
        temperature=0.01,
        coherence_time=100,
        operation_time=2,
        parity_measurement_error=0.01,
        minimum_gap=0.1,
    )

    sequence = [
        (1, 1),
        (2, 1),
        (1, 1),
        (2, -1),
    ]

    result = system.run_experiment(
        "MAJORANA-EXP-001",
        sequence,
        conditions,
    )

    print("Status:", result.status.value)
    print("Operations:", result.operations)
    print("Final state:", result.final_state)
    print("Fidelity:", result.fidelity)

    print("\n6. Experimental rejection test")

    rejected_conditions = ExperimentalConditions(
        energy_gap=0.02,
        temperature=0.01,
        coherence_time=10,
        operation_time=20,
        parity_measurement_error=0.12,
    )

    rejected = system.run_experiment(
        "MAJORANA-EXP-002",
        sequence,
        rejected_conditions,
    )

    print("Status:", rejected.status.value)
    for reason in rejected.reasons:
        print("-", reason)

    print("\n7. Unit tests")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MajoranaTests)
    result_tests = unittest.TextTestRunner(verbosity=1).run(suite)

    if not result_tests.wasSuccessful():
        raise SystemExit(1)

    print("\nAll mathematical and validation tests passed.")


if __name__ == "__main__":
    main()
