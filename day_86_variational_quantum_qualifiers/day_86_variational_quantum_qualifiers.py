#!/usr/bin/env python3
"""
Variational Quantum Classifier (VQC)
A self-contained two-qubit state-vector simulator and binary classifier.

Features:
- Quantum state-vector simulation
- Feature-map encoding
- Parameterized quantum circuit
- CNOT entanglement
- Pauli-Z expectation measurement
- Parameter-shift gradient calculation
- Binary cross-entropy optimization
- Train/test evaluation
- Model persistence and validation

Uses only the Python standard library.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


EPSILON = 1e-10


class QuantumError(Exception):
    """Base exception for quantum classifier errors."""


class ValidationError(QuantumError):
    """Raised when input data or parameters are invalid."""


@dataclass(frozen=True)
class Sample:
    features: tuple[float, float]
    label: int

    def __post_init__(self):
        if len(self.features) != 2:
            raise ValidationError("Exactly two features are required.")
        if any(not math.isfinite(x) for x in self.features):
            raise ValidationError("Features must be finite.")
        if self.label not in (0, 1):
            raise ValidationError("Labels must be binary.")

    @property
    def target(self) -> float:
        return float(self.label)


@dataclass
class TrainingConfig:
    epochs: int = 120
    learning_rate: float = 0.08
    seed: int = 42

    def validate(self):
        if self.epochs <= 0:
            raise ValidationError("Epochs must be positive.")
        if not 0 < self.learning_rate <= 1:
            raise ValidationError("Invalid learning rate.")


class QuantumCircuit:
    """Two-qubit state-vector simulator."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = [
            complex(1, 0),
            complex(0, 0),
            complex(0, 0),
            complex(0, 0),
        ]

    @staticmethod
    def ry(theta: float):
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        return c, s

    def apply_ry(self, qubit: int, theta: float):
        if qubit not in (0, 1):
            raise ValidationError("Invalid qubit index.")

        c, s = self.ry(theta)
        mask = 1 << qubit
        updated = self.state.copy()

        for i in range(4):
            if i & mask:
                continue

            j = i | mask
            a, b = self.state[i], self.state[j]

            updated[i] = c * a - s * b
            updated[j] = s * a + c * b

        self.state = updated

    def apply_cnot(self, control: int, target: int):
        if control == target or control not in (0, 1) or target not in (0, 1):
            raise ValidationError("Invalid CNOT configuration.")

        updated = [0j] * 4

        for index, amplitude in enumerate(self.state):
            destination = index
            if (index >> control) & 1:
                destination ^= 1 << target
            updated[destination] = amplitude

        self.state = updated

    def probability(self, basis_state: int) -> float:
        if basis_state not in range(4):
            raise ValidationError("Invalid basis state.")
        return abs(self.state[basis_state]) ** 2

    def expectation_z0(self) -> float:
        """Measure the Pauli-Z observable on qubit zero."""
        return (
            self.probability(0)
            + self.probability(2)
            - self.probability(1)
            - self.probability(3)
        )

    def validate_state(self):
        norm = sum(abs(a) ** 2 for a in self.state)
        if not math.isclose(norm, 1.0, abs_tol=1e-8):
            raise QuantumError(f"State normalization violated: {norm}")


class VariationalQuantumClassifier:
    """
    Two-qubit variational classifier.

    Circuit:
        |00>
          |
        Feature map: RY(x0), RY(x1)
          |
        Entanglement: CNOT(0,1)
          |
        Ansatz layer: RY(theta0), RY(theta1)
          |
        Entanglement: CNOT(0,1)
          |
        Ansatz layer: RY(theta2), RY(theta3)
          |
        Measurement: <Z0>
          |
        Probability and binary prediction
    """

    def __init__(self, seed: int = 42):
        rng = random.Random(seed)
        self.parameters = [
            rng.uniform(-0.5, 0.5) for _ in range(4)
        ]
        self.training_history: list[float] = []

    def expectation(
        self,
        features: Sequence[float],
        parameters: Sequence[float] | None = None,
    ) -> float:
        if len(features) != 2:
            raise ValidationError("Two input features are required.")

        if any(not math.isfinite(x) for x in features):
            raise ValidationError("Non-finite feature detected.")

        params = self.parameters if parameters is None else parameters

        if len(params) != 4:
            raise ValidationError("Exactly four trainable parameters required.")

        circuit = QuantumCircuit()

        # Encode classical features as quantum rotation angles.
        circuit.apply_ry(0, features[0])
        circuit.apply_ry(1, features[1])

        circuit.apply_cnot(0, 1)

        # Trainable variational ansatz.
        circuit.apply_ry(0, params[0])
        circuit.apply_ry(1, params[1])

        circuit.apply_cnot(0, 1)

        circuit.apply_ry(0, params[2])
        circuit.apply_ry(1, params[3])

        circuit.validate_state()

        return circuit.expectation_z0()

    @staticmethod
    def probability_from_expectation(expectation: float) -> float:
        # P(class 1) = (1 - <Z>) / 2.
        return min(1.0 - EPSILON, max(EPSILON, (1 - expectation) / 2))

    def predict_proba(self, features: Sequence[float]) -> float:
        expectation = self.expectation(features)
        return self.probability_from_expectation(expectation)

    def predict(self, features: Sequence[float]) -> int:
        return int(self.predict_proba(features) >= 0.5)

    @staticmethod
    def loss(probability: float, label: int) -> float:
        p = min(1 - EPSILON, max(EPSILON, probability))
        return -(label * math.log(p) + (1 - label) * math.log(1 - p))

    def parameter_shift_gradient(
        self,
        sample: Sample,
        parameters: Sequence[float],
    ) -> list[float]:
        """
        Parameter-shift rule:
        df/dtheta = [f(theta + pi/2) - f(theta - pi/2)] / 2.

        The expectation derivative is converted into a probability
        derivative before applying the binary cross-entropy chain rule.
        """
        base_expectation = self.expectation(sample.features, parameters)
        probability = self.probability_from_expectation(base_expectation)

        gradient = []

        for index in range(len(parameters)):
            plus = list(parameters)
            minus = list(parameters)

            plus[index] += math.pi / 2
            minus[index] -= math.pi / 2

            exp_plus = self.expectation(sample.features, plus)
            exp_minus = self.expectation(sample.features, minus)

            derivative_expectation = (exp_plus - exp_minus) / 2
            derivative_probability = -0.5 * derivative_expectation

            derivative_loss = (
                (probability - sample.target)
                / (probability * (1 - probability))
            )

            gradient.append(
                derivative_loss * derivative_probability
            )

        return gradient

    def train(
        self,
        samples: Sequence[Sample],
        config: TrainingConfig,
    ):
        config.validate()

        if len(samples) < 2:
            raise ValidationError("At least two training samples are required.")

        if len({sample.label for sample in samples}) != 2:
            raise ValidationError("Training data must contain both classes.")

        for epoch in range(config.epochs):
            total_loss = 0.0
            gradients = [0.0] * len(self.parameters)

            # Full-batch gradient descent provides deterministic updates.
            for sample in samples:
                probability = self.predict_proba(sample.features)
                total_loss += self.loss(probability, sample.label)

                sample_gradient = self.parameter_shift_gradient(
                    sample, self.parameters
                )

                for i, value in enumerate(sample_gradient):
                    gradients[i] += value

            count = len(samples)
            total_loss /= count

            self.parameters = [
                max(-4 * math.pi, min(4 * math.pi,
                    parameter - config.learning_rate * gradient / count))
                for parameter, gradient in zip(
                    self.parameters, gradients
                )
            ]

            self.training_history.append(total_loss)

            if not math.isfinite(total_loss):
                raise QuantumError("Training produced a non-finite loss.")

            if epoch % 20 == 0:
                print(
                    f"Epoch {epoch:03d} | "
                    f"Loss: {total_loss:.6f}"
                )

        return self

    def evaluate(self, samples: Sequence[Sample]) -> dict:
        if not samples:
            raise ValidationError("Evaluation dataset cannot be empty.")

        correct = 0
        total_loss = 0.0
        true_positive = 0
        false_positive = 0
        true_negative = 0
        false_negative = 0

        for sample in samples:
            probability = self.predict_proba(sample.features)
            prediction = int(probability >= 0.5)

            total_loss += self.loss(probability, sample.label)
            correct += prediction == sample.label

            if prediction == 1 and sample.label == 1:
                true_positive += 1
            elif prediction == 1:
                false_positive += 1
            elif sample.label == 0:
                true_negative += 1
            else:
                false_negative += 1

        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive else 0.0
        )

        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative else 0.0
        )

        return {
            "accuracy": correct / len(samples),
            "loss": total_loss / len(samples),
            "precision": precision,
            "recall": recall,
            "confusion_matrix": {
                "true_positive": true_positive,
                "false_positive": false_positive,
                "true_negative": true_negative,
                "false_negative": false_negative,
            },
        }

    def save(self, filepath: str):
        data = {
            "format_version": 1,
            "qubits": 2,
            "parameters": self.parameters,
            "training_history": self.training_history,
        }

        path = Path(filepath)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, filepath: str):
        data = json.loads(
            Path(filepath).read_text(encoding="utf-8")
        )

        if data.get("format_version") != 1 or data.get("qubits") != 2:
            raise ValidationError("Unsupported model format.")

        parameters = data.get("parameters")

        if (
            not isinstance(parameters, list)
            or len(parameters) != 4
            or not all(
                isinstance(x, (int, float)) and math.isfinite(x)
                for x in parameters
            )
        ):
            raise ValidationError("Invalid model parameters.")

        self.parameters = [float(x) for x in parameters]
        self.training_history = data.get("training_history", [])
        return self


def make_dataset() -> list[Sample]:
    """Create a deterministic two-class nonlinear demonstration dataset."""
    raw = [
        ((0.15, 0.20), 0),
        ((0.35, 0.25), 0),
        ((0.20, 0.55), 0),
        ((0.55, 0.30), 0),
        ((0.40, 0.65), 0),
        ((2.10, 2.00), 1),
        ((2.40, 1.80), 1),
        ((1.90, 2.45), 1),
        ((2.65, 2.30), 1),
        ((2.20, 2.70), 1),
    ]
    return [Sample(features, label) for features, label in raw]


def main():
    print("=" * 58)
    print("VARIATIONAL QUANTUM CLASSIFIER")
    print("=" * 58)

    dataset = make_dataset()

    # Stratified split keeps both classes in each partition.
    training = dataset[:4] + dataset[5:9]
    testing = [dataset[4], dataset[9]]

    model = VariationalQuantumClassifier(seed=42)

    config = TrainingConfig(
        epochs=120,
        learning_rate=0.08,
        seed=42,
    )

    print("\nTraining quantum classifier...")
    model.train(training, config)

    print("\nTraining evaluation:")
    print(json.dumps(model.evaluate(training), indent=2))

    print("\nTesting evaluation:")
    print(json.dumps(model.evaluate(testing), indent=2))

    print("\nIndividual predictions:")
    for sample in testing:
        probability = model.predict_proba(sample.features)
        print(
            f"Features={sample.features}, "
            f"Actual={sample.label}, "
            f"Predicted={model.predict(sample.features)}, "
            f"P(class=1)={probability:.4f}"
        )

    model.save("vqc_model.json")
    restored = VariationalQuantumClassifier().load("vqc_model.json")

    assert restored.parameters == model.parameters

    print("\nModel persistence verified.")
    print("Training epochs:", len(model.training_history))
    print(
        "Final training loss:",
        f"{model.training_history[-1]:.6f}"
    )


if __name__ == "__main__":
    main()
