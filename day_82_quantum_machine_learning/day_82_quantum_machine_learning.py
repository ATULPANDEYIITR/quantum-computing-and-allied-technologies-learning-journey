#!/usr/bin/env python3
"""
Quantum Machine Learning: Landscape, Concepts, and Variational Quantum Learning

A self-contained educational implementation covering:
- Quantum computing fundamentals
- Qubits and quantum states
- Superposition and entanglement
- Quantum gates and measurements
- Statevector simulation
- Data encoding
- Variational quantum circuits
- Hybrid quantum-classical optimization
- Quantum kernel evaluation
- Model evaluation and resource estimation
- QML limitations and experiment validation

Requires Python 3.10+.
No external dependencies.
"""

from __future__ import annotations

import cmath
import json
import math
import random
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence


# ============================================================
# 1. DOMAIN DEFINITIONS
# ============================================================

class AlgorithmFamily(Enum):
    VARIATIONAL = "Variational Quantum Algorithms"
    QUANTUM_KERNEL = "Quantum Kernel Methods"
    QUANTUM_NEURAL_NETWORK = "Quantum Neural Networks"
    QUANTUM_CLASSIFICATION = "Quantum Classification"
    QUANTUM_GENERATIVE = "Quantum Generative Models"
    QUANTUM_REINFORCEMENT = "Quantum Reinforcement Learning"
    QUANTUM_INSPIRED = "Quantum-Inspired Classical Methods"


class BackendType(Enum):
    STATEVECTOR = "statevector_simulator"
    SHOT_BASED = "shot_based_simulator"
    NOISY = "noisy_simulator"
    HARDWARE = "quantum_hardware"


@dataclass(frozen=True)
class Qubit:
    index: int
    label: str

    def __post_init__(self):
        if self.index < 0:
            raise ValueError("Qubit index cannot be negative.")


@dataclass
class QMLExperiment:
    name: str
    algorithm: AlgorithmFamily
    qubits: int
    circuit_depth: int
    shots: int
    backend: BackendType
    dataset_size: int

    def validate(self):
        if not self.name.strip():
            raise ValueError("Experiment name cannot be empty.")
        if not 1 <= self.qubits <= 20:
            raise ValueError("Educational simulator supports 1-20 qubits.")
        if self.circuit_depth < 1:
            raise ValueError("Circuit depth must be positive.")
        if self.shots < 1:
            raise ValueError("Shots must be positive.")
        if self.dataset_size < 1:
            raise ValueError("Dataset size must be positive.")


# ============================================================
# 2. QUANTUM STATE REPRESENTATION
# ============================================================

class QuantumState:
    """
    Statevector representation.

    An n-qubit pure state contains 2**n complex amplitudes.

    Computational basis:
        |00>, |01>, |10>, |11>

    Probability of observing basis state i:
        abs(amplitudes[i]) ** 2
    """

    def __init__(self, qubits: int):
        if not 1 <= qubits <= 20:
            raise ValueError("Qubit count must be between 1 and 20.")

        self.qubits = qubits
        self.amplitudes = [0j] * (2 ** qubits)
        self.amplitudes[0] = 1 + 0j

    def normalize(self):
        norm = math.sqrt(sum(abs(a) ** 2 for a in self.amplitudes))

        if norm == 0:
            raise ArithmeticError("Quantum state has zero norm.")

        self.amplitudes = [a / norm for a in self.amplitudes]

    def apply_single_qubit(
        self,
        target: int,
        matrix: Sequence[Sequence[complex]]
    ):
        if not 0 <= target < self.qubits:
            raise IndexError("Invalid target qubit.")

        if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
            raise ValueError("A single-qubit gate must be 2x2.")

        bit = 1 << target

        # Update pairs of amplitudes without modifying the same
        # amplitude twice.
        for base in range(len(self.amplitudes)):
            if base & bit:
                continue

            zero = self.amplitudes[base]
            one = self.amplitudes[base | bit]

            self.amplitudes[base] = (
                matrix[0][0] * zero + matrix[0][1] * one
            )
            self.amplitudes[base | bit] = (
                matrix[1][0] * zero + matrix[1][1] * one
            )

    def ry(self, target: int, angle: float):
        c = math.cos(angle / 2)
        s = math.sin(angle / 2)

        self.apply_single_qubit(
            target,
            [[c, -s], [s, c]]
        )

    def rz(self, target: int, angle: float):
        self.apply_single_qubit(
            target,
            [
                [cmath.exp(-1j * angle / 2), 0j],
                [0j, cmath.exp(1j * angle / 2)]
            ]
        )

    def hadamard(self, target: int):
        scale = 1 / math.sqrt(2)

        self.apply_single_qubit(
            target,
            [[scale, scale], [scale, -scale]]
        )

    def cnot(self, control: int, target: int):
        if control == target:
            raise ValueError("Control and target must differ.")

        if not (
            0 <= control < self.qubits
            and 0 <= target < self.qubits
        ):
            raise IndexError("Invalid CNOT qubit.")

        control_mask = 1 << control
        target_mask = 1 << target

        for index in range(len(self.amplitudes)):
            if index & control_mask and not index & target_mask:
                other = index | target_mask
                self.amplitudes[index], self.amplitudes[other] = (
                    self.amplitudes[other],
                    self.amplitudes[index]
                )

    def probabilities(self):
        return [abs(a) ** 2 for a in self.amplitudes]

    def measure_z(self, target: int) -> float:
        if not 0 <= target < self.qubits:
            raise IndexError("Invalid measurement qubit.")

        bit = 1 << target

        # Expectation value: P(0) - P(1).
        return sum(
            (1 if not index & bit else -1) * abs(amplitude) ** 2
            for index, amplitude in enumerate(self.amplitudes)
        )

    def sample(self, shots: int, seed: int = 42):
        if shots < 1:
            raise ValueError("Shots must be positive.")

        rng = random.Random(seed)
        probabilities = self.probabilities()

        return rng.choices(
            range(len(probabilities)),
            weights=probabilities,
            k=shots
        )


# ============================================================
# 3. QUANTUM GATES AND SUPERPOSITION
# ============================================================

def demonstrate_quantum_fundamentals():
    state = QuantumState(2)

    state.hadamard(0)
    state.cnot(0, 1)

    print("\nQUANTUM FUNDAMENTALS")
    print("Bell-state amplitudes:")

    for index, amplitude in enumerate(state.amplitudes):
        print(f"|{index:02b}>: {amplitude}")

    print("Probabilities:", state.probabilities())
    print("Measurement expectation Z0:", state.measure_z(0))

    assert math.isclose(
        state.probabilities()[0], 0.5, abs_tol=1e-9
    )
    assert math.isclose(
        state.probabilities()[3], 0.5, abs_tol=1e-9
    )


# ============================================================
# 4. DATA ENCODING
# ============================================================

class DataEncoder:
    """
    Angle encoding maps numerical features to rotation angles.

    x_i -> RY(pi * x_i)

    Inputs are constrained to [-1, 1].
    """

    @staticmethod
    def encode(features: Sequence[float]) -> QuantumState:
        if not features:
            raise ValueError("Feature vector cannot be empty.")

        if len(features) > 8:
            raise ValueError("Maximum eight encoded features.")

        state = QuantumState(len(features))

        for index, value in enumerate(features):
            if not math.isfinite(value) or not -1 <= value <= 1:
                raise ValueError(
                    f"Feature {index} must be finite and in [-1, 1]."
                )

            state.ry(index, math.pi * value)

        return state


# ============================================================
# 5. VARIATIONAL QUANTUM CIRCUIT
# ============================================================

class VariationalQuantumClassifier:
    """
    A hybrid quantum-classical binary classifier.

    Workflow:

        Classical input
             |
        Angle encoding
             |
        Trainable quantum rotations
             |
        Entanglement
             |
        Measurement
             |
        Classical probability transformation
             |
        Binary prediction

    The objective is optimized using finite-difference gradients.
    """

    def __init__(self, qubits: int = 2, seed: int = 42):
        if not 1 <= qubits <= 8:
            raise ValueError("Classifier supports 1-8 qubits.")

        self.qubits = qubits
        rng = random.Random(seed)

        self.parameters = [
            rng.uniform(-0.3, 0.3)
            for _ in range(qubits)
        ]

    def quantum_expectation(
        self,
        features: Sequence[float],
        parameters: Sequence[float] | None = None
    ) -> float:
        if len(features) != self.qubits:
            raise ValueError("Feature count must equal qubit count.")

        if parameters is None:
            parameters = self.parameters

        if len(parameters) != self.qubits:
            raise ValueError("Parameter count mismatch.")

        state = DataEncoder.encode(features)

        for index, parameter in enumerate(parameters):
            if not math.isfinite(parameter):
                raise ValueError("Parameters must be finite.")
            state.ry(index, parameter)

        # A ring-like entanglement pattern.
        for index in range(self.qubits - 1):
            state.cnot(index, index + 1)

        return state.measure_z(0)

    def predict_probability(self, features):
        expectation = self.quantum_expectation(features)

        # Convert an expectation value in [-1, 1] to [0, 1].
        return (1.0 + expectation) / 2.0

    def predict(self, features):
        return int(self.predict_probability(features) >= 0.5)

    @staticmethod
    def binary_cross_entropy(labels, probabilities):
        if len(labels) != len(probabilities) or not labels:
            raise ValueError("Labels and predictions must have equal size.")

        epsilon = 1e-12
        loss = 0.0

        for label, probability in zip(labels, probabilities):
            if label not in (0, 1):
                raise ValueError("Binary labels must be 0 or 1.")

            probability = min(
                1 - epsilon,
                max(epsilon, probability)
            )

            loss -= (
                label * math.log(probability)
                + (1 - label) * math.log(1 - probability)
            )

        return loss / len(labels)

    def loss(self, dataset):
        probabilities = [
            self.predict_probability(features)
            for features, _ in dataset
        ]

        labels = [label for _, label in dataset]

        return self.binary_cross_entropy(labels, probabilities)

    def train(
        self,
        dataset,
        epochs: int = 30,
        learning_rate: float = 0.15
    ):
        if not dataset:
            raise ValueError("Training dataset cannot be empty.")

        if epochs < 1 or learning_rate <= 0:
            raise ValueError("Invalid training configuration.")

        for features, label in dataset:
            if len(features) != self.qubits:
                raise ValueError("Inconsistent feature dimensions.")
            if label not in (0, 1):
                raise ValueError("Invalid training label.")

        history = []
        delta = 1e-4

        for epoch in range(epochs):
            gradients = []

            # Numerical gradient of the hybrid objective.
            for index in range(self.qubits):
                original = self.parameters[index]

                self.parameters[index] = original + delta
                positive = self.loss(dataset)

                self.parameters[index] = original - delta
                negative = self.loss(dataset)

                self.parameters[index] = original

                gradients.append(
                    (positive - negative) / (2 * delta)
                )

            # Gradient descent in the classical optimizer.
            self.parameters = [
                max(-math.pi, min(math.pi, parameter - learning_rate * gradient))
                for parameter, gradient in zip(
                    self.parameters, gradients
                )
            ]

            current_loss = self.loss(dataset)
            history.append(current_loss)

            if not math.isfinite(current_loss):
                raise ArithmeticError("Training produced invalid loss.")

            print(
                f"Epoch {epoch + 1:02d} | "
                f"Loss: {current_loss:.6f}"
            )

        return history


# ============================================================
# 6. QUANTUM KERNEL METHODS
# ============================================================

class QuantumKernel:
    """
    Fidelity kernel:

        K(x, y) = |<phi(x)|phi(y)>|^2

    A quantum feature map transforms classical data into quantum
    states. A classical SVM can use the resulting kernel matrix.
    """

    @staticmethod
    def feature_state(features):
        state = DataEncoder.encode(features)

        for index in range(len(features) - 1):
            state.cnot(index, index + 1)

        return state.amplitudes

    @classmethod
    def fidelity(cls, x, y):
        if len(x) != len(y):
            raise ValueError("Kernel inputs must have equal dimensions.")

        state_x = cls.feature_state(x)
        state_y = cls.feature_state(y)

        overlap = sum(
            a.conjugate() * b
            for a, b in zip(state_x, state_y)
        )

        return abs(overlap) ** 2

    @classmethod
    def matrix(cls, dataset):
        size = len(dataset)

        if not size:
            raise ValueError("Kernel dataset cannot be empty.")

        result = [[0.0] * size for _ in range(size)]

        for i in range(size):
            for j in range(i, size):
                value = cls.fidelity(dataset[i], dataset[j])
                result[i][j] = value
                result[j][i] = value

        return result


# ============================================================
# 7. RESOURCE ESTIMATION
# ============================================================

@dataclass
class ResourceEstimate:
    qubits: int
    statevector_amplitudes: int
    estimated_state_memory_bytes: int
    circuit_depth: int
    measurement_shots: int
    estimated_measurement_work: int


def estimate_resources(
    qubits: int,
    circuit_depth: int,
    shots: int
) -> ResourceEstimate:
    if not 1 <= qubits <= 30:
        raise ValueError("Resource estimator supports 1-30 qubits.")

    if circuit_depth < 1 or shots < 1:
        raise ValueError("Depth and shots must be positive.")

    amplitudes = 2 ** qubits

    # A complex double uses approximately 16 bytes.
    memory = amplitudes * 16

    return ResourceEstimate(
        qubits=qubits,
        statevector_amplitudes=amplitudes,
        estimated_state_memory_bytes=memory,
        circuit_depth=circuit_depth,
        measurement_shots=shots,
        estimated_measurement_work=shots * circuit_depth
    )


# ============================================================
# 8. EVALUATION
# ============================================================

def evaluate_classifier(model, dataset):
    correct = 0
    true_positive = 0
    false_positive = 0
    false_negative = 0

    for features, actual in dataset:
        predicted = model.predict(features)

        correct += predicted == actual

        if predicted == 1 and actual == 1:
            true_positive += 1
        elif predicted == 1 and actual == 0:
            false_positive += 1
        elif predicted == 0 and actual == 1:
            false_negative += 1

    total = len(dataset)

    if total == 0:
        raise ValueError("Evaluation dataset cannot be empty.")

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive else 0.0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative else 0.0
    )

    return {
        "accuracy": correct / total,
        "precision": precision,
        "recall": recall,
        "evaluated_samples": total
    }


# ============================================================
# 9. QML LANDSCAPE AND ALGORITHM SELECTION
# ============================================================

QML_LANDSCAPE = {
    "Variational Quantum Algorithms": [
        "Variational Quantum Eigensolver",
        "Quantum Approximate Optimization Algorithm",
        "Variational Quantum Classifiers"
    ],
    "Quantum Kernel Methods": [
        "Quantum feature maps",
        "Fidelity kernels",
        "Quantum kernel estimation"
    ],
    "Quantum Neural Networks": [
        "Parameterized quantum circuits",
        "Quantum convolutional circuits",
        "Hybrid neural architectures"
    ],
    "Quantum Generative Models": [
        "Quantum circuit Born machines",
        "Quantum generative adversarial models"
    ],
    "Quantum Reinforcement Learning": [
        "Parameterized policy circuits",
        "Quantum value-function models"
    ],
    "Quantum-Inspired Classical Methods": [
        "Tensor networks",
        "Classical optimization inspired by quantum systems"
    ]
}


def select_algorithm(
    dataset_size: int,
    available_qubits: int,
    requires_trainable_model: bool
):
    if dataset_size < 1 or available_qubits < 1:
        raise ValueError("Invalid selection constraints.")

    if available_qubits <= 4 and requires_trainable_model:
        return AlgorithmFamily.VARIATIONAL

    if dataset_size <= 500 and available_qubits >= 2:
        return AlgorithmFamily.QUANTUM_KERNEL

    return AlgorithmFamily.QUANTUM_INSPIRED


# ============================================================
# 10. EXPERIMENT EXECUTION
# ============================================================

def run_experiment():
    print("=" * 65)
    print("QUANTUM MACHINE LEARNING LANDSCAPE")
    print("=" * 65)

    demonstrate_quantum_fundamentals()

    # Synthetic binary dataset.
    # Label 1 when the first feature is positive.
    training_data = [
        ([-0.9, -0.4], 0),
        ([-0.7, 0.6], 0),
        ([-0.5, 0.2], 0),
        ([0.5, -0.3], 1),
        ([0.7, 0.4], 1),
        ([0.9, -0.6], 1)
    ]

    testing_data = [
        ([-0.8, 0.1], 0),
        ([-0.6, -0.5], 0),
        ([0.6, 0.2], 1),
        ([0.8, -0.4], 1)
    ]

    experiment = QMLExperiment(
        name="Two-Qubit Variational Classifier",
        algorithm=AlgorithmFamily.VARIATIONAL,
        qubits=2,
        circuit_depth=4,
        shots=1024,
        backend=BackendType.STATEVECTOR,
        dataset_size=len(training_data)
    )

    experiment.validate()

    print("\nEXPERIMENT CONFIGURATION")
    print(json.dumps({
        **asdict(experiment),
        "algorithm": experiment.algorithm.value,
        "backend": experiment.backend.value
    }, indent=2))

    model = VariationalQuantumClassifier(qubits=2)

    print("\nTRAINING")
    history = model.train(
        training_data,
        epochs=30,
        learning_rate=0.15
    )

    print("\nMODEL PARAMETERS")
    print(model.parameters)

    print("\nTEST EVALUATION")
    metrics = evaluate_classifier(model, testing_data)
    print(json.dumps(metrics, indent=2))

    print("\nQUANTUM KERNEL MATRIX")
    kernel_matrix = QuantumKernel.matrix([
        [-0.8, 0.1],
        [-0.6, -0.5],
        [0.6, 0.2],
        [0.8, -0.4]
    ])

    for row in kernel_matrix:
        print([round(value, 4) for value in row])

    print("\nRESOURCE ESTIMATION")
    resources = estimate_resources(
        qubits=experiment.qubits,
        circuit_depth=experiment.circuit_depth,
        shots=experiment.shots
    )

    print(json.dumps(asdict(resources), indent=2))

    print("\nALGORITHM LANDSCAPE")

    for category, algorithms in QML_LANDSCAPE.items():
        print(f"\n{category}")
        for algorithm in algorithms:
            print(f"  - {algorithm}")

    print("\nALGORITHM SELECTION")
    selected = select_algorithm(
        dataset_size=100,
        available_qubits=4,
        requires_trainable_model=True
    )

    print(selected.value)

    # Basic integrity tests.
    assert all(0 <= p <= 1 for p in kernel_matrix[0])
    assert len(history) == 30
    assert 0 <= metrics["accuracy"] <= 1

    report = {
        "experiment": experiment.name,
        "algorithm": experiment.algorithm.value,
        "final_training_loss": history[-1],
        "metrics": metrics,
        "parameters": model.parameters,
        "resources": asdict(resources)
    }

    output = Path("qml_experiment_report.json")
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print(f"\nReport saved to {output.resolve()}")


if __name__ == "__main__":
    run_experiment()
