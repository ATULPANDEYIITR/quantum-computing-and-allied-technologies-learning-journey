#!/usr/bin/env python3
"""
Quantum Generative Models: Quantum Generative Learning

A self-contained statevector implementation of a parameterized quantum
circuit (PQC), a Born machine, synthetic data generation, training using
finite-difference SPSA, sampling, and evaluation.

Runtime: Python 3.10+
Dependencies: Python standard library only.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Sequence


EPSILON = 1e-12


class ModelError(Exception):
    """Base exception for quantum generative model failures."""


class ValidationError(ModelError):
    """Invalid model configuration or input data."""


class ExperimentStatus(Enum):
    CREATED = "created"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ModelConfig:
    qubits: int = 2
    learning_rate: float = 0.08
    iterations: int = 300
    shots: int = 5000
    seed: int = 42

    def __post_init__(self):
        if not 1 <= self.qubits <= 12:
            raise ValidationError("Qubits must be between 1 and 12.")
        if self.learning_rate <= 0:
            raise ValidationError("Learning rate must be positive.")
        if self.iterations <= 0:
            raise ValidationError("Iterations must be positive.")
        if self.shots <= 0:
            raise ValidationError("Shots must be positive.")


@dataclass
class TrainingRecord:
    iteration: int
    loss: float
    learning_rate: float


@dataclass
class Experiment:
    experiment_id: str
    status: ExperimentStatus
    initial_loss: float = 0.0
    final_loss: float = 0.0
    history: list[TrainingRecord] | None = None


class QuantumCircuit:
    """
    Statevector simulator supporting Ry rotations and CNOT gates.

    Statevector size is 2**n. Qubit zero is the most significant bit.
    """

    def __init__(self, qubits: int):
        if not 1 <= qubits <= 12:
            raise ValidationError("Unsupported qubit count.")

        self.qubits = qubits
        self.dimension = 1 << qubits

    def apply_ry(self, state: list[complex], qubit: int, theta: float):
        if not 0 <= qubit < self.qubits:
            raise ValidationError("Invalid qubit index.")

        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        mask = 1 << (self.qubits - 1 - qubit)

        for index in range(self.dimension):
            if index & mask:
                continue

            paired = index | mask
            a = state[index]
            b = state[paired]

            state[index] = c * a - s * b
            state[paired] = s * a + c * b

    def apply_cnot(
        self,
        state: list[complex],
        control: int,
        target: int
    ):
        if control == target:
            raise ValidationError("Control and target must differ.")

        if not (
            0 <= control < self.qubits
            and 0 <= target < self.qubits
        ):
            raise ValidationError("Invalid CNOT qubit index.")

        control_mask = 1 << (self.qubits - 1 - control)
        target_mask = 1 << (self.qubits - 1 - target)

        for index in range(self.dimension):
            if index & control_mask and not index & target_mask:
                paired = index | target_mask
                state[index], state[paired] = (
                    state[paired],
                    state[index]
                )

    def execute(self, parameters: Sequence[float]) -> list[float]:
        if len(parameters) != 2 * self.qubits:
            raise ValidationError(
                f"Expected {2 * self.qubits} parameters."
            )

        if not all(math.isfinite(x) for x in parameters):
            raise ValidationError("Parameters must be finite.")

        state = [0j] * self.dimension
        state[0] = 1 + 0j

        # First parameterized rotation layer.
        for qubit in range(self.qubits):
            self.apply_ry(state, qubit, parameters[qubit])

        # Entanglement layer.
        for qubit in range(self.qubits - 1):
            self.apply_cnot(state, qubit, qubit + 1)

        # Second parameterized rotation layer.
        for qubit in range(self.qubits):
            self.apply_ry(
                state,
                qubit,
                parameters[self.qubits + qubit]
            )

        # Born probabilities are squared statevector amplitudes.
        probabilities = [abs(amplitude) ** 2 for amplitude in state]

        total = sum(probabilities)

        if total <= EPSILON:
            raise ModelError("Invalid quantum state normalization.")

        return [p / total for p in probabilities]


class QuantumBornMachine:
    """
    Trainable quantum generative model.

    The model defines p(x) = |<x|U(theta)|0>|^2.

    SPSA estimates gradients using two circuit evaluations per iteration,
    independent of the number of circuit parameters.
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self.circuit = QuantumCircuit(config.qubits)
        self.random = random.Random(config.seed)

        self.parameters = [
            self.random.uniform(-0.8, 0.8)
            for _ in range(2 * config.qubits)
        ]

        self.history: list[TrainingRecord] = []

    def probabilities(self) -> list[float]:
        return self.circuit.execute(self.parameters)

    @staticmethod
    def validate_distribution(target: Sequence[float]) -> list[float]:
        if not target:
            raise ValidationError("Target distribution cannot be empty.")

        if any(not math.isfinite(x) or x < 0 for x in target):
            raise ValidationError(
                "Distribution values must be finite and nonnegative."
            )

        total = sum(target)

        if total <= EPSILON:
            raise ValidationError("Distribution has zero probability mass.")

        return [x / total for x in target]

    @staticmethod
    def kl_divergence(
        target: Sequence[float],
        generated: Sequence[float]
    ) -> float:
        if len(target) != len(generated):
            raise ValidationError("Distribution dimensions differ.")

        return sum(
            p * math.log(p / max(q, EPSILON))
            for p, q in zip(target, generated)
            if p > 0
        )

    @staticmethod
    def total_variation_distance(
        target: Sequence[float],
        generated: Sequence[float]
    ) -> float:
        return 0.5 * sum(
            abs(p - q) for p, q in zip(target, generated)
        )

    def loss(self, target: Sequence[float]) -> float:
        return self.kl_divergence(target, self.probabilities())

    def train(
        self,
        target: Sequence[float],
        iterations: int | None = None
    ) -> list[TrainingRecord]:

        target = self.validate_distribution(target)

        if len(target) != self.circuit.dimension:
            raise ValidationError(
                "Target dimension must equal 2**qubits."
            )

        iterations = iterations or self.config.iterations

        if iterations <= 0:
            raise ValidationError("Iterations must be positive.")

        self.history.clear()

        initial_loss = self.loss(target)

        parameter_count = len(self.parameters)

        # SPSA perturbation and learning-rate schedules.
        a = self.config.learning_rate
        alpha = 0.602
        gamma = 0.101
        stability = 10.0

        for iteration in range(iterations):
            ak = a / ((iteration + 1 + stability) ** alpha)
            ck = 0.12 / ((iteration + 1) ** gamma)

            perturbation = [
                self.random.choice((-1.0, 1.0))
                for _ in range(parameter_count)
            ]

            original = self.parameters.copy()

            self.parameters = [
                original[i] + ck * perturbation[i]
                for i in range(parameter_count)
            ]
            loss_plus = self.loss(target)

            self.parameters = [
                original[i] - ck * perturbation[i]
                for i in range(parameter_count)
            ]
            loss_minus = self.loss(target)

            gradient_scale = (loss_plus - loss_minus) / (2 * ck)

            self.parameters = [
                original[i] - ak * gradient_scale / perturbation[i]
                for i in range(parameter_count)
            ]

            # Keep rotations numerically bounded without changing
            # their physical periodicity.
            self.parameters = [
                ((value + math.pi) % (2 * math.pi)) - math.pi
                for value in self.parameters
            ]

            current_loss = self.loss(target)

            if not math.isfinite(current_loss):
                raise ModelError("Training produced a non-finite loss.")

            self.history.append(
                TrainingRecord(
                    iteration=iteration + 1,
                    loss=current_loss,
                    learning_rate=ak
                )
            )

        final_loss = self.loss(target)

        print(f"Initial KL divergence: {initial_loss:.6f}")
        print(f"Final KL divergence:   {final_loss:.6f}")

        return self.history

    def sample(self, shots: int | None = None) -> dict[str, int]:
        shots = shots or self.config.shots

        if shots <= 0:
            raise ValidationError("Shots must be positive.")

        probabilities = self.probabilities()
        counts = [0] * len(probabilities)

        # Cumulative sampling approximates computational-basis measurement.
        cumulative = []
        running = 0.0

        for probability in probabilities:
            running += probability
            cumulative.append(running)

        for _ in range(shots):
            value = self.random.random()

            for index, threshold in enumerate(cumulative):
                if value <= threshold:
                    counts[index] += 1
                    break
            else:
                counts[-1] += 1

        return {
            format(index, f"0{self.config.qubits}b"): count
            for index, count in enumerate(counts)
        }

    def evaluate(self, target: Sequence[float]) -> dict:
        target = self.validate_distribution(target)
        generated = self.probabilities()

        if len(target) != len(generated):
            raise ValidationError("Evaluation dimensions differ.")

        return {
            "kl_divergence": self.kl_divergence(target, generated),
            "total_variation_distance": self.total_variation_distance(
                target, generated
            ),
            "generated_entropy": -sum(
                p * math.log2(p)
                for p in generated
                if p > EPSILON
            ),
            "target_entropy": -sum(
                p * math.log2(p)
                for p in target
                if p > EPSILON
            ),
            "probabilities": generated
        }


def create_target_distribution() -> list[float]:
    """
    Four-outcome distribution representing a structured binary dataset.
    """
    return [0.40, 0.10, 0.10, 0.40]


def save_experiment(
    model: QuantumBornMachine,
    evaluation: dict,
    filename: str = "quantum_experiment.json"
):
    result = {
        "model": "Parameterized Quantum Born Machine",
        "qubits": model.config.qubits,
        "parameters": model.parameters,
        "evaluation": evaluation,
        "history": [asdict(record) for record in model.history],
        "samples": model.sample()
    }

    path = Path(filename)

    # Avoid writing outside the current working directory.
    if path.name != str(path) or path.suffix != ".json":
        raise ValidationError("Invalid experiment filename.")

    path.write_text(
        json.dumps(result, indent=2, allow_nan=False),
        encoding="utf-8"
    )


def run_experiment():
    config = ModelConfig(
        qubits=2,
        learning_rate=0.08,
        iterations=300,
        shots=5000,
        seed=42
    )

    model = QuantumBornMachine(config)
    experiment = Experiment(
        experiment_id="QGM-001",
        status=ExperimentStatus.CREATED,
        history=[]
    )

    target = create_target_distribution()

    print("=" * 55)
    print("QUANTUM GENERATIVE LEARNING")
    print("=" * 55)

    print("\nTarget distribution:")
    for index, probability in enumerate(target):
        print(f"|{index:02b}>: {probability:.4f}")

    try:
        experiment.status = ExperimentStatus.TRAINING

        experiment.initial_loss = model.loss(target)
        model.train(target)

        evaluation = model.evaluate(target)
        experiment.final_loss = evaluation["kl_divergence"]
        experiment.history = model.history
        experiment.status = ExperimentStatus.COMPLETED

        print("\nGenerated probability distribution:")

        for index, probability in enumerate(
            evaluation["probabilities"]
        ):
            print(f"|{index:02b}>: {probability:.6f}")

        print("\nEvaluation:")
        for metric, value in evaluation.items():
            if isinstance(value, list):
                continue
            print(f"{metric}: {value:.6f}")

        print("\nMeasurement samples:")
        print(model.sample())

        save_experiment(model, evaluation)

        print("\nExperiment status:", experiment.status.value)
        print("Saved: quantum_experiment.json")

    except (ModelError, OSError, ValueError) as error:
        experiment.status = ExperimentStatus.FAILED
        print(f"Experiment failed: {error}")
        raise


def run_tests():
    circuit = QuantumCircuit(2)

    probabilities = circuit.execute([0.0, 0.0, 0.0, 0.0])

    assert abs(probabilities[0] - 1.0) < 1e-10
    assert abs(sum(probabilities) - 1.0) < 1e-10

    model = QuantumBornMachine(ModelConfig(iterations=20))
    target = [0.25, 0.25, 0.25, 0.25]

    history = model.train(target, iterations=20)

    assert len(history) == 20
    assert all(math.isfinite(record.loss) for record in history)

    samples = model.sample(1000)
    assert sum(samples.values()) == 1000

    try:
        model.train([0.5, 0.5])
    except ValidationError:
        pass
    else:
        raise AssertionError("Invalid target dimension was accepted.")

    print("\nAll tests passed.")


if __name__ == "__main__":
    run_experiment()
    run_tests()
