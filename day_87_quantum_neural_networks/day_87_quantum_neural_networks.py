"""
QUANTUM NEURAL NETWORKS: FUNDAMENTALS
A self-contained variational quantum neural network simulator.

Features:
- Complex-valued quantum state representation
- Qubit initialization and normalization
- Quantum gates: RX, RY, RZ and CNOT
- Angle-based feature encoding
- Parameterized quantum circuits
- Measurement and expectation values
- Variational parameter optimization
- Finite-difference gradient calculation
- Binary classification
- Validation and numerical stability checks

Runtime: Python 3.10+
Dependencies: Python standard library only
"""

from __future__ import annotations

import math
import random
import json
from dataclasses import dataclass
from typing import Sequence


EPSILON = 1e-10


class QuantumError(Exception):
    """Base exception for quantum simulation errors."""


class ValidationError(QuantumError):
    """Invalid quantum circuit or input configuration."""


@dataclass
class TrainingMetrics:
    epoch: int
    loss: float
    accuracy: float


@dataclass
class TrainingResult:
    parameters: list[float]
    history: list[TrainingMetrics]
    converged: bool


class QuantumState:
    """State-vector simulator for a small quantum register."""

    def __init__(self, qubits: int):
        if not isinstance(qubits, int) or isinstance(qubits, bool):
            raise ValidationError("Qubit count must be an integer.")

        if not 1 <= qubits <= 20:
            raise ValidationError("Qubit count must be between 1 and 20.")

        self.qubits = qubits
        self.dimension = 1 << qubits
        self.state = [0j] * self.dimension
        self.state[0] = 1.0 + 0j

    def apply_single_qubit_gate(
        self,
        qubit: int,
        matrix: tuple[complex, complex, complex, complex]
    ) -> None:
        """Apply a 2x2 unitary matrix to one qubit."""

        if not 0 <= qubit < self.qubits:
            raise ValidationError("Qubit index out of range.")

        a, b, c, d = matrix
        mask = 1 << qubit

        for i in range(self.dimension):
            if i & mask:
                continue

            j = i | mask
            alpha = self.state[i]
            beta = self.state[j]

            self.state[i] = a * alpha + b * beta
            self.state[j] = c * alpha + d * beta

    def rx(self, qubit: int, angle: float) -> None:
        c = math.cos(angle / 2)
        s = math.sin(angle / 2)

        self.apply_single_qubit_gate(
            qubit,
            (c, -1j * s, -1j * s, c)
        )

    def ry(self, qubit: int, angle: float) -> None:
        c = math.cos(angle / 2)
        s = math.sin(angle / 2)

        self.apply_single_qubit_gate(
            qubit,
            (c, -s, s, c)
        )

    def rz(self, qubit: int, angle: float) -> None:
        self.apply_single_qubit_gate(
            qubit,
            (
                complex(math.cos(angle / 2), -math.sin(angle / 2)),
                0j,
                0j,
                complex(math.cos(angle / 2), math.sin(angle / 2))
            )
        )

    def cnot(self, control: int, target: int) -> None:
        """Apply controlled-NOT using computational basis indexing."""

        if control == target:
            raise ValidationError("Control and target must differ.")

        if not all(0 <= q < self.qubits for q in (control, target)):
            raise ValidationError("Invalid CNOT qubit index.")

        control_mask = 1 << control
        target_mask = 1 << target

        for i in range(self.dimension):
            if (i & control_mask) and not (i & target_mask):
                j = i | target_mask
                self.state[i], self.state[j] = (
                    self.state[j],
                    self.state[i]
                )

    def probabilities(self) -> list[float]:
        return [abs(amplitude) ** 2 for amplitude in self.state]

    def expectation_z(self, qubit: int) -> float:
        """Calculate the expectation value of Pauli-Z."""

        if not 0 <= qubit < self.qubits:
            raise ValidationError("Qubit index out of range.")

        mask = 1 << qubit
        expectation = 0.0

        for i, amplitude in enumerate(self.state):
            probability = abs(amplitude) ** 2
            expectation += probability * (
                -1.0 if i & mask else 1.0
            )

        return expectation

    def measure(self, qubit: int, shots: int = 1000) -> dict:
        """Perform repeated computational-basis measurements."""

        if shots <= 0:
            raise ValidationError("Shots must be positive.")

        if not 0 <= qubit < self.qubits:
            raise ValidationError("Qubit index out of range.")

        probabilities = [
            sum(
                p for i, p in enumerate(self.probabilities())
                if bool(i & (1 << qubit)) == bool(outcome)
            )
            for outcome in (0, 1)
        ]

        counts = {0: 0, 1: 0}

        for _ in range(shots):
            outcome = random.choices(
                [0, 1],
                weights=probabilities
            )[0]
            counts[outcome] += 1

        return {
            "counts": counts,
            "shots": shots,
            "expectation": (
                counts[0] - counts[1]
            ) / shots
        }

    def validate_normalization(self) -> None:
        norm = sum(abs(a) ** 2 for a in self.state)

        if abs(norm - 1.0) > 1e-8:
            raise QuantumError(
                f"Quantum state is not normalized: {norm}"
            )


class QuantumFeatureMap:
    """Encode classical features into quantum rotation angles."""

    @staticmethod
    def encode(
        state: QuantumState,
        features: Sequence[float]
    ) -> None:

        if len(features) != state.qubits:
            raise ValidationError(
                "Feature count must equal qubit count."
            )

        for index, feature in enumerate(features):
            if not math.isfinite(feature):
                raise ValidationError("Features must be finite.")

            state.ry(index, float(feature))


class VariationalCircuit:
    """
    Two-qubit variational quantum circuit.

    Feature map:
        RY(x0), RY(x1)

    Trainable ansatz:
        RY(theta0), RY(theta1)
        CNOT(0, 1)
        RY(theta2), RY(theta3)
        CNOT(1, 0)

    Observable:
        Pauli-Z on qubit zero.
    """

    PARAMETER_COUNT = 4

    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)

    def initialize_parameters(self) -> list[float]:
        return [
            self.random.uniform(-0.5, 0.5)
            for _ in range(self.PARAMETER_COUNT)
        ]

    def forward(
        self,
        features: Sequence[float],
        parameters: Sequence[float]
    ) -> float:

        if len(features) != 2:
            raise ValidationError("Exactly two features are required.")

        if len(parameters) != self.PARAMETER_COUNT:
            raise ValidationError("Expected four trainable parameters.")

        if not all(math.isfinite(float(x)) for x in features):
            raise ValidationError("Features must be finite.")

        if not all(math.isfinite(float(x)) for x in parameters):
            raise ValidationError("Parameters must be finite.")

        state = QuantumState(2)

        QuantumFeatureMap.encode(state, features)

        state.ry(0, parameters[0])
        state.ry(1, parameters[1])
        state.cnot(0, 1)

        state.ry(0, parameters[2])
        state.ry(1, parameters[3])
        state.cnot(1, 0)

        state.validate_normalization()

        return state.expectation_z(0)


class QuantumNeuralNetwork:
    """Train a variational quantum classifier."""

    def __init__(self, learning_rate: float = 0.05):
        if not 0 < learning_rate <= 1:
            raise ValidationError("Invalid learning rate.")

        self.learning_rate = learning_rate
        self.circuit = VariationalCircuit()
        self.parameters = self.circuit.initialize_parameters()

    def predict(self, features: Sequence[float]) -> float:
        return self.circuit.forward(features, self.parameters)

    def classify(self, features: Sequence[float]) -> int:
        return 1 if self.predict(features) >= 0 else 0

    def loss(
        self,
        dataset: Sequence[tuple[Sequence[float], float]],
        parameters: Sequence[float]
    ) -> float:

        if not dataset:
            raise ValidationError("Dataset cannot be empty.")

        total = 0.0

        for features, target in dataset:
            if target not in (-1, 1):
                raise ValidationError("Targets must be -1 or +1.")

            prediction = self.circuit.forward(features, parameters)
            total += (prediction - target) ** 2

        return total / len(dataset)

    def gradient(
        self,
        dataset: Sequence[tuple[Sequence[float], float]],
        parameters: Sequence[float],
        delta: float = 1e-5
    ) -> list[float]:
        """Numerically estimate the loss gradient."""

        gradients = []

        for index in range(len(parameters)):
            plus = list(parameters)
            minus = list(parameters)

            plus[index] += delta
            minus[index] -= delta

            derivative = (
                self.loss(dataset, plus)
                - self.loss(dataset, minus)
            ) / (2 * delta)

            gradients.append(derivative)

        return gradients

    def accuracy(
        self,
        dataset: Sequence[tuple[Sequence[float], float]],
        parameters: Sequence[float]
    ) -> float:

        correct = 0

        for features, target in dataset:
            prediction = self.circuit.forward(features, parameters)
            predicted_class = 1 if prediction >= 0 else -1

            if predicted_class == target:
                correct += 1

        return correct / len(dataset)

    def fit(
        self,
        dataset: Sequence[tuple[Sequence[float], float]],
        epochs: int = 100,
        tolerance: float = 1e-7
    ) -> TrainingResult:

        if not dataset:
            raise ValidationError("Training dataset cannot be empty.")

        if epochs <= 0 or tolerance < 0:
            raise ValidationError("Invalid training configuration.")

        for features, target in dataset:
            if len(features) != 2:
                raise ValidationError("Each example needs two features.")

            if target not in (-1, 1):
                raise ValidationError("Targets must be -1 or +1.")

            if not all(math.isfinite(float(x)) for x in features):
                raise ValidationError("Features must be finite.")

        history = []
        converged = False

        for epoch in range(1, epochs + 1):

            gradients = self.gradient(dataset, self.parameters)

            self.parameters = [
                p - self.learning_rate * g
                for p, g in zip(self.parameters, gradients)
            ]

            current_loss = self.loss(dataset, self.parameters)
            current_accuracy = self.accuracy(
                dataset, self.parameters
            )

            history.append(
                TrainingMetrics(
                    epoch,
                    current_loss,
                    current_accuracy
                )
            )

            if current_loss < tolerance:
                converged = True
                break

        return TrainingResult(
            parameters=self.parameters.copy(),
            history=history,
            converged=converged
        )


def demonstrate_fundamentals() -> None:
    print("\nQUANTUM NEURAL NETWORK FUNDAMENTALS")
    print("=" * 55)

    # Demonstrate superposition and measurement.
    state = QuantumState(1)
    state.ry(0, math.pi / 2)

    print("\n1. Quantum superposition")
    print("Probabilities:", state.probabilities())
    print("Pauli-Z expectation:", state.expectation_z(0))
    print("Measurement:", state.measure(0, shots=1000))

    # Demonstrate entanglement.
    entangled = QuantumState(2)
    entangled.ry(0, math.pi / 2)
    entangled.cnot(0, 1)

    print("\n2. Entangled two-qubit state")
    print("Probabilities:", entangled.probabilities())

    # Demonstrate parameterized quantum learning.
    dataset = [
        ([0.2, 0.3], 1),
        ([0.3, 0.5], 1),
        ([2.8, 2.5], -1),
        ([2.5, 2.9], -1),
        ([0.5, 0.2], 1),
        ([2.9, 2.7], -1),
    ]

    network = QuantumNeuralNetwork(learning_rate=0.05)

    print("\n3. Variational quantum classifier")
    print("Initial parameters:", network.parameters)
    print("Initial loss:", network.loss(dataset, network.parameters))

    result = network.fit(dataset, epochs=100)

    print("Final parameters:", result.parameters)
    print("Final loss:", result.history[-1].loss)
    print("Training accuracy:", result.history[-1].accuracy)
    print("Converged:", result.converged)

    print("\n4. Predictions")

    for features, target in dataset:
        output = network.predict(features)

        print({
            "features": features,
            "target": target,
            "expectation": round(output, 5),
            "predicted_class": network.classify(features)
        })

    # Save experiment metadata without exposing sensitive information.
    report = {
        "architecture": "Two-qubit variational quantum classifier",
        "qubits": 2,
        "parameters": result.parameters,
        "epochs": len(result.history),
        "final_loss": result.history[-1].loss,
        "accuracy": result.history[-1].accuracy
    }

    with open("qnn_experiment.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nExperiment metadata saved to qnn_experiment.json")


def run_tests() -> None:
    """Basic correctness and edge-case checks."""

    state = QuantumState(1)
    state.ry(0, math.pi / 2)

    assert abs(sum(state.probabilities()) - 1.0) < EPSILON
    assert abs(state.expectation_z(0)) < EPSILON

    bell = QuantumState(2)
    bell.ry(0, math.pi / 2)
    bell.cnot(0, 1)

    probabilities = bell.probabilities()

    assert abs(probabilities[0] - 0.5) < EPSILON
    assert abs(probabilities[3] - 0.5) < EPSILON
    assert abs(probabilities[1]) < EPSILON
    assert abs(probabilities[2]) < EPSILON

    try:
        QuantumState(0)
        raise AssertionError("Invalid qubit count was accepted.")
    except ValidationError:
        pass

    try:
        VariationalCircuit().forward([1.0], [0.0] * 4)
        raise AssertionError("Invalid feature count was accepted.")
    except ValidationError:
        pass

    print("All fundamental quantum simulation tests passed.")


if __name__ == "__main__":
    run_tests()
    demonstrate_fundamentals()
