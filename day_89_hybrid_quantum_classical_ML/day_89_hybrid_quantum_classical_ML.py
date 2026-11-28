#!/usr/bin/env python3
"""
Hybrid Quantum-Classical Machine Learning
Classical optimization + quantum circuit simulation.

Features:
- State-vector quantum simulation
- Single-qubit and controlled gates
- Parameterized quantum circuits
- Quantum feature maps
- Expectation-value measurements
- Parameter-shift gradient estimation
- Classical logistic regression
- Hybrid model training
- Model evaluation and validation
- Reproducible experiments
- JSON experiment reporting

Dependencies: Python 3.10+
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SEED = 42
random.seed(SEED)

EPSILON = 1e-12


class ModelStatus(Enum):
    INITIALIZED = "initialized"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"


class ExperimentError(Exception):
    pass


class QuantumCircuitError(ExperimentError):
    pass


# ---------------------------------------------------------
# Numerical utilities
# ---------------------------------------------------------

def sigmoid(value: float) -> float:
    value = max(-500.0, min(500.0, value))
    return 1.0 / (1.0 + math.exp(-value))


def validate_vector(values: Sequence[float], expected: int) -> None:
    if len(values) != expected:
        raise ValueError(f"Expected {expected} values, received {len(values)}")

    if not all(math.isfinite(float(x)) for x in values):
        raise ValueError("Input contains non-finite values")


def normalize(values: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in values))

    if norm < EPSILON:
        raise ValueError("Cannot normalize a zero vector")

    return [x / norm for x in values]


# ---------------------------------------------------------
# Quantum state-vector simulator
# ---------------------------------------------------------

class QuantumRegister:

    def __init__(self, num_qubits: int):
        if not 1 <= num_qubits <= 12:
            raise ValueError("Qubit count must be between 1 and 12")

        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits

        self.state = [0j] * self.dimension
        self.state[0] = 1.0 + 0j

    def apply_single_qubit_gate(
        self,
        qubit: int,
        matrix: tuple[tuple[complex, complex],
                      tuple[complex, complex]]
    ) -> None:

        if not 0 <= qubit < self.num_qubits:
            raise QuantumCircuitError("Invalid qubit index")

        mask = 1 << qubit

        for index in range(self.dimension):
            if index & mask:
                continue

            paired = index | mask

            a = self.state[index]
            b = self.state[paired]

            self.state[index] = matrix[0][0] * a + matrix[0][1] * b
            self.state[paired] = matrix[1][0] * a + matrix[1][1] * b

    def ry(self, qubit: int, theta: float) -> None:
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        self.apply_single_qubit_gate(
            qubit,
            ((complex(c), complex(-s)),
             (complex(s), complex(c)))
        )

    def rz(self, qubit: int, theta: float) -> None:
        a = complex(math.cos(theta / 2), -math.sin(theta / 2))
        b = complex(math.cos(theta / 2), math.sin(theta / 2))

        self.apply_single_qubit_gate(
            qubit,
            ((a, 0j), (0j, b))
        )

    def hadamard(self, qubit: int) -> None:
        c = 1.0 / math.sqrt(2)

        self.apply_single_qubit_gate(
            qubit,
            ((complex(c), complex(c)),
             (complex(c), complex(-c)))
        )

    def cnot(self, control: int, target: int) -> None:
        if control == target:
            raise QuantumCircuitError("Control and target must differ")

        if not (0 <= control < self.num_qubits):
            raise QuantumCircuitError("Invalid control qubit")

        if not (0 <= target < self.num_qubits):
            raise QuantumCircuitError("Invalid target qubit")

        control_mask = 1 << control
        target_mask = 1 << target

        for index in range(self.dimension):
            if index & control_mask and not index & target_mask:
                paired = index | target_mask

                self.state[index], self.state[paired] = (
                    self.state[paired],
                    self.state[index]
                )

    def expectation_z(self, qubit: int) -> float:
        if not 0 <= qubit < self.num_qubits:
            raise QuantumCircuitError("Invalid qubit index")

        mask = 1 << qubit
        result = 0.0

        for index, amplitude in enumerate(self.state):
            probability = abs(amplitude) ** 2

            result += probability * (
                -1.0 if index & mask else 1.0
            )

        return result

    def probabilities(self) -> list[float]:
        return [abs(amplitude) ** 2 for amplitude in self.state]

    def sample(self, shots: int = 1000) -> dict[str, int]:
        if shots <= 0:
            raise ValueError("Shots must be positive")

        probabilities = self.probabilities()
        counts = {}

        for _ in range(shots):
            value = random.random()
            cumulative = 0.0

            for index, probability in enumerate(probabilities):
                cumulative += probability

                if value <= cumulative:
                    key = format(index, f"0{self.num_qubits}b")
                    counts[key] = counts.get(key, 0) + 1
                    break

        return counts


# ---------------------------------------------------------
# Quantum feature map
# ---------------------------------------------------------

class QuantumFeatureMap:

    def __init__(self, num_qubits: int = 2):
        self.num_qubits = num_qubits

    def transform(self, features: Sequence[float]) -> list[float]:
        validate_vector(features, self.num_qubits)

        circuit = QuantumRegister(self.num_qubits)

        for index, value in enumerate(features):
            circuit.hadamard(index)
            circuit.ry(index, value)
            circuit.rz(index, value * value)

        for index in range(self.num_qubits - 1):
            circuit.cnot(index, index + 1)

        return [
            circuit.expectation_z(index)
            for index in range(self.num_qubits)
        ]


# ---------------------------------------------------------
# Variational quantum circuit
# ---------------------------------------------------------

class VariationalQuantumCircuit:

    def __init__(self, num_qubits: int = 2):
        self.num_qubits = num_qubits

    def execute(
        self,
        features: Sequence[float],
        parameters: Sequence[float]
    ) -> list[float]:

        validate_vector(features, self.num_qubits)
        validate_vector(parameters, self.num_qubits * 2)

        circuit = QuantumRegister(self.num_qubits)

        for index in range(self.num_qubits):
            circuit.hadamard(index)
            circuit.ry(index, features[index])

        for index in range(self.num_qubits):
            circuit.ry(index, parameters[index])

        for index in range(self.num_qubits - 1):
            circuit.cnot(index, index + 1)

        for index in range(self.num_qubits):
            circuit.rz(index, parameters[self.num_qubits + index])

        return [
            circuit.expectation_z(index)
            for index in range(self.num_qubits)
        ]


# ---------------------------------------------------------
# Synthetic binary classification dataset
# ---------------------------------------------------------

@dataclass(frozen=True)
class Sample:
    features: tuple[float, ...]
    label: int


def generate_dataset(size: int = 120) -> list[Sample]:
    if size < 20:
        raise ValueError("Dataset must contain at least 20 samples")

    samples = []

    for index in range(size):
        x1 = random.uniform(-math.pi, math.pi)
        x2 = random.uniform(-math.pi, math.pi)

        label = int(math.sin(x1) * math.cos(x2) > 0)

        samples.append(
            Sample((x1, x2), label)
        )

    random.shuffle(samples)
    return samples


# ---------------------------------------------------------
# Classical logistic regression head
# ---------------------------------------------------------

class ClassicalHead:

    def __init__(self, input_size: int):
        self.weights = [
            random.uniform(-0.1, 0.1)
            for _ in range(input_size)
        ]

        self.bias = 0.0

    def predict_probability(self, features: Sequence[float]) -> float:
        validate_vector(features, len(self.weights))

        linear = sum(
            weight * value
            for weight, value in zip(self.weights, features)
        ) + self.bias

        return sigmoid(linear)

    def update(
        self,
        features: Sequence[float],
        label: int,
        learning_rate: float
    ) -> None:

        probability = self.predict_probability(features)
        error = probability - label

        for index in range(len(self.weights)):
            self.weights[index] -= (
                learning_rate * error * features[index]
            )

        self.bias -= learning_rate * error


# ---------------------------------------------------------
# Hybrid quantum-classical classifier
# ---------------------------------------------------------

class HybridClassifier:

    def __init__(
        self,
        num_qubits: int = 2,
        learning_rate: float = 0.03
    ):

        if learning_rate <= 0:
            raise ValueError("Learning rate must be positive")

        self.num_qubits = num_qubits
        self.learning_rate = learning_rate

        self.quantum = VariationalQuantumCircuit(num_qubits)

        self.parameters = [
            random.uniform(-0.2, 0.2)
            for _ in range(num_qubits * 2)
        ]

        self.classical = ClassicalHead(num_qubits)
        self.status = ModelStatus.INITIALIZED
        self.history = []

    def quantum_features(
        self,
        features: Sequence[float]
    ) -> list[float]:

        return self.quantum.execute(
            features,
            self.parameters
        )

    def predict_probability(
        self,
        features: Sequence[float]
    ) -> float:

        quantum_output = self.quantum_features(features)

        return self.classical.predict_probability(
            quantum_output
        )

    def loss(
        self,
        dataset: Sequence[Sample]
    ) -> float:

        total = 0.0

        for sample in dataset:
            probability = self.predict_probability(sample.features)

            probability = min(
                1.0 - EPSILON,
                max(EPSILON, probability)
            )

            total -= (
                sample.label * math.log(probability)
                + (1 - sample.label) * math.log(1 - probability)
            )

        return total / len(dataset)

    def parameter_shift_gradient(
        self,
        dataset: Sequence[Sample]
    ) -> list[float]:

        gradients = []

        # Parameter-shift rule for Pauli rotation parameters.
        # The classical head is held fixed during this calculation.
        shift = math.pi / 2

        for index in range(len(self.parameters)):
            original = self.parameters[index]

            self.parameters[index] = original + shift
            positive = self.loss(dataset)

            self.parameters[index] = original - shift
            negative = self.loss(dataset)

            self.parameters[index] = original

            gradients.append((positive - negative) / 2.0)

        return gradients

    def train(
        self,
        dataset: Sequence[Sample],
        epochs: int = 40
    ) -> None:

        if not dataset:
            raise ValueError("Training dataset cannot be empty")

        if epochs <= 0:
            raise ValueError("Epochs must be positive")

        if any(sample.label not in (0, 1) for sample in dataset):
            raise ValueError("Labels must be binary")

        self.status = ModelStatus.TRAINING

        try:
            for epoch in range(epochs):

                gradients = self.parameter_shift_gradient(dataset)

                # Update variational quantum parameters.
                self.parameters = [
                    parameter - self.learning_rate * gradient
                    for parameter, gradient in zip(
                        self.parameters, gradients
                    )
                ]

                # Update classical parameters using current quantum outputs.
                for sample in dataset:
                    quantum_output = self.quantum_features(
                        sample.features
                    )

                    self.classical.update(
                        quantum_output,
                        sample.label,
                        self.learning_rate
                    )

                current_loss = self.loss(dataset)

                self.history.append({
                    "epoch": epoch + 1,
                    "loss": current_loss
                })

                if not math.isfinite(current_loss):
                    raise ExperimentError("Non-finite training loss")

            self.status = ModelStatus.TRAINED

        except Exception:
            self.status = ModelStatus.FAILED
            raise

    def predict(self, features: Sequence[float]) -> int:
        if self.status != ModelStatus.TRAINED:
            raise ExperimentError("Model must be trained before prediction")

        return int(self.predict_probability(features) >= 0.5)


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

@dataclass
class Evaluation:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int


def evaluate(
    model: HybridClassifier,
    dataset: Sequence[Sample]
) -> Evaluation:

    if not dataset:
        raise ValueError("Evaluation dataset cannot be empty")

    tp = tn = fp = fn = 0

    for sample in dataset:
        predicted = model.predict(sample.features)

        if predicted == 1 and sample.label == 1:
            tp += 1
        elif predicted == 0 and sample.label == 0:
            tn += 1
        elif predicted == 1 and sample.label == 0:
            fp += 1
        else:
            fn += 1

    accuracy = (tp + tn) / len(dataset)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return Evaluation(
        accuracy,
        precision,
        recall,
        f1,
        tp,
        tn,
        fp,
        fn
    )


# ---------------------------------------------------------
# Experiment management
# ---------------------------------------------------------

@dataclass
class ExperimentReport:
    experiment_name: str
    num_qubits: int
    training_samples: int
    testing_samples: int
    epochs: int
    execution_seconds: float
    final_training_loss: float
    evaluation: dict


def save_report(
    report: ExperimentReport,
    filename: str = "hybrid_quantum_experiment.json"
) -> None:

    destination = Path(filename).resolve()

    if destination.suffix.lower() != ".json":
        raise ValueError("Report filename must use .json")

    with destination.open("w", encoding="utf-8") as file:
        json.dump(
            asdict(report),
            file,
            indent=4,
            allow_nan=False
        )


# ---------------------------------------------------------
# Tests and demonstration
# ---------------------------------------------------------

def run_tests() -> None:

    register = QuantumRegister(1)
    register.hadamard(0)

    assert abs(register.expectation_z(0)) < 1e-9

    counts = register.sample(1000)
    assert sum(counts.values()) == 1000

    circuit = QuantumRegister(2)
    circuit.hadamard(0)
    circuit.cnot(0, 1)

    assert abs(circuit.expectation_z(0)) < 1e-9
    assert abs(circuit.expectation_z(1)) < 1e-9

    feature_map = QuantumFeatureMap(2)
    output = feature_map.transform([0.5, 0.7])

    assert len(output) == 2

    try:
        QuantumRegister(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid qubit count was accepted")


def main() -> None:

    run_tests()

    dataset = generate_dataset(160)

    split = int(len(dataset) * 0.8)

    training_data = dataset[:split]
    testing_data = dataset[split:]

    model = HybridClassifier(
        num_qubits=2,
        learning_rate=0.03
    )

    start = time.perf_counter()

    model.train(
        training_data,
        epochs=40
    )

    elapsed = time.perf_counter() - start

    results = evaluate(model, testing_data)

    report = ExperimentReport(
        experiment_name="Hybrid Quantum-Classical Binary Classifier",
        num_qubits=2,
        training_samples=len(training_data),
        testing_samples=len(testing_data),
        epochs=40,
        execution_seconds=elapsed,
        final_training_loss=model.history[-1]["loss"],
        evaluation=asdict(results)
    )

    save_report(report)

    print("HYBRID QUANTUM-CLASSICAL EXPERIMENT")
    print("----------------------------------")
    print("Model status:", model.status.value)
    print("Training samples:", len(training_data))
    print("Testing samples:", len(testing_data))
    print("Final loss:", round(model.history[-1]["loss"], 6))
    print("Accuracy:", round(results.accuracy, 4))
    print("Precision:", round(results.precision, 4))
    print("Recall:", round(results.recall, 4))
    print("F1 score:", round(results.f1_score, 4))
    print("Execution time:", round(elapsed, 4), "seconds")
    print("Report: hybrid_quantum_experiment.json")


if __name__ == "__main__":
    main()
