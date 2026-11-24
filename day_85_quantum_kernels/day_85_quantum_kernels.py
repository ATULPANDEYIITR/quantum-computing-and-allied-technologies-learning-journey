#!/usr/bin/env python3
"""
Quantum Kernels: Kernel Methods with Quantum Circuits

Implements:
- State-vector quantum circuit simulation.
- Parameterized quantum feature maps.
- Single-qubit rotations and entangling gates.
- Quantum fidelity kernel computation.
- Kernel matrix construction and caching.
- Positive-semidefinite validation.
- Kernel ridge classification.
- Model evaluation and numerical diagnostics.

Uses only the Python standard library.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Sequence


EPSILON = 1e-10


class QuantumKernelError(Exception):
    """Base exception for quantum kernel operations."""


class ValidationError(QuantumKernelError):
    """Invalid input or circuit configuration."""


class NumericalError(QuantumKernelError):
    """Numerical computation failure."""


@dataclass(frozen=True)
class CircuitConfig:
    n_qubits: int = 2
    entanglement: bool = True
    rotation_scale: float = 2.0

    def __post_init__(self):
        if not 1 <= self.n_qubits <= 12:
            raise ValidationError("Qubit count must be between 1 and 12.")
        if not math.isfinite(self.rotation_scale):
            raise ValidationError("Rotation scale must be finite.")


@dataclass
class Evaluation:
    accuracy: float
    predictions: list[int]
    actual: list[int]
    confusion_matrix: dict[str, int]


def validate_vector(
    vector: Sequence[float],
    expected_dimensions: int
) -> tuple[float, ...]:
    if len(vector) != expected_dimensions:
        raise ValidationError(
            f"Expected {expected_dimensions} features, "
            f"received {len(vector)}."
        )

    values = tuple(float(x) for x in vector)

    if not all(math.isfinite(x) for x in values):
        raise ValidationError("Features must contain finite values.")

    return values


class QuantumCircuitSimulator:
    """
    State-vector simulator using complex amplitudes.

    Computational basis states are stored in a dense vector
    of size 2**n_qubits.
    """

    def __init__(self, config: CircuitConfig):
        self.config = config
        self.dimension = 1 << config.n_qubits

    def initial_state(self) -> list[complex]:
        state = [0j] * self.dimension
        state[0] = 1.0 + 0j
        return state

    def hadamard(
        self,
        state: list[complex],
        qubit: int
    ) -> None:
        mask = 1 << qubit
        factor = 1.0 / math.sqrt(2.0)

        for index in range(self.dimension):
            if not index & mask:
                partner = index | mask
                a = state[index]
                b = state[partner]

                state[index] = (a + b) * factor
                state[partner] = (a - b) * factor

    def rz(
        self,
        state: list[complex],
        qubit: int,
        angle: float
    ) -> None:
        mask = 1 << qubit
        half = angle / 2.0
        phase_zero = complex(math.cos(-half), math.sin(-half))
        phase_one = complex(math.cos(half), math.sin(half))

        for index in range(self.dimension):
            if index & mask:
                state[index] *= phase_one
            else:
                state[index] *= phase_zero

    def rx(
        self,
        state: list[complex],
        qubit: int,
        angle: float
    ) -> None:
        mask = 1 << qubit
        cosine = math.cos(angle / 2.0)
        sine = math.sin(angle / 2.0)

        for index in range(self.dimension):
            if not index & mask:
                partner = index | mask

                a = state[index]
                b = state[partner]

                state[index] = cosine * a - 1j * sine * b
                state[partner] = cosine * b - 1j * sine * a

    def cz(
        self,
        state: list[complex],
        control: int,
        target: int
    ) -> None:
        if control == target:
            raise ValidationError("CZ requires distinct qubits.")

        control_mask = 1 << control
        target_mask = 1 << target

        for index in range(self.dimension):
            if index & control_mask and index & target_mask:
                state[index] = -state[index]

    def feature_map(
        self,
        features: Sequence[float]
    ) -> tuple[complex, ...]:
        x = validate_vector(features, self.config.n_qubits)
        state = self.initial_state()

        # Uniform superposition establishes a nontrivial basis.
        for qubit in range(self.config.n_qubits):
            self.hadamard(state, qubit)

        # Data-dependent phase and amplitude transformations.
        for qubit, value in enumerate(x):
            angle = self.config.rotation_scale * value
            self.rz(state, qubit, angle)
            self.rx(state, qubit, angle)

        # Entanglement creates interactions between features.
        if self.config.entanglement:
            for qubit in range(self.config.n_qubits - 1):
                self.cz(state, qubit, qubit + 1)

        norm = sum(abs(amplitude) ** 2 for amplitude in state)

        if abs(norm - 1.0) > 1e-9:
            raise NumericalError(
                f"State normalization failure: {norm}"
            )

        return tuple(state)


class QuantumFidelityKernel:
    """
    Fidelity kernel:

        K(x, z) = |<phi(x)|phi(z)>|^2

    The overlap is calculated from simulated state vectors.
    """

    def __init__(self, config: CircuitConfig):
        self.simulator = QuantumCircuitSimulator(config)
        self.cache: dict[
            tuple[tuple[float, ...], tuple[float, ...]], float
        ] = {}
        self.state_cache: dict[
            tuple[float, ...], tuple[complex, ...]
        ] = {}

    def state(self, features: Sequence[float]):
        x = validate_vector(
            features,
            self.simulator.config.n_qubits
        )

        if x not in self.state_cache:
            self.state_cache[x] = self.simulator.feature_map(x)

        return self.state_cache[x]

    def evaluate(
        self,
        first: Sequence[float],
        second: Sequence[float]
    ) -> float:
        x = validate_vector(
            first,
            self.simulator.config.n_qubits
        )
        z = validate_vector(
            second,
            self.simulator.config.n_qubits
        )

        # Fidelity is symmetric, so canonicalize cache keys.
        key = (x, z) if x <= z else (z, x)

        if key in self.cache:
            return self.cache[key]

        state_x = self.state(x)
        state_z = self.state(z)

        overlap = sum(
            a.conjugate() * b
            for a, b in zip(state_x, state_z)
        )

        fidelity = abs(overlap) ** 2

        # Suppress floating-point excursions outside [0, 1].
        fidelity = min(1.0, max(0.0, fidelity))

        self.cache[key] = fidelity
        return fidelity

    def matrix(
        self,
        first: Sequence[Sequence[float]],
        second: Sequence[Sequence[float]] | None = None
    ) -> list[list[float]]:
        if not first:
            raise ValidationError("First dataset cannot be empty.")

        second = first if second is None else second

        if not second:
            raise ValidationError("Second dataset cannot be empty.")

        if second is first:
            result = [
                [0.0] * len(first)
                for _ in range(len(first))
            ]

            for i in range(len(first)):
                result[i][i] = 1.0

                for j in range(i + 1, len(first)):
                    value = self.evaluate(first[i], first[j])
                    result[i][j] = value
                    result[j][i] = value

            return result

        return [
            [self.evaluate(x, z) for z in second]
            for x in first
        ]

    def diagnostics(
        self,
        matrix: Sequence[Sequence[float]]
    ) -> dict[str, float | bool]:
        size = len(matrix)

        if size == 0 or any(len(row) != size for row in matrix):
            raise ValidationError("Expected a nonempty square matrix.")

        symmetry_error = max(
            abs(matrix[i][j] - matrix[j][i])
            for i in range(size)
            for j in range(size)
        )

        diagonal_error = max(
            abs(matrix[i][i] - 1.0)
            for i in range(size)
        )

        # Cholesky-style positive-semidefinite check.
        lower = [[0.0] * size for _ in range(size)]
        psd = True

        for i in range(size):
            for j in range(i + 1):
                value = matrix[i][j] - sum(
                    lower[i][k] * lower[j][k]
                    for k in range(j)
                )

                if i == j:
                    if value < -1e-8:
                        psd = False
                        break

                    lower[i][j] = math.sqrt(max(0.0, value))
                else:
                    if lower[j][j] > EPSILON:
                        lower[i][j] = value / lower[j][j]
                    elif abs(value) > 1e-8:
                        psd = False
                        break

            if not psd:
                break

        return {
            "symmetry_error": symmetry_error,
            "diagonal_error": diagonal_error,
            "positive_semidefinite": psd,
            "cache_entries": float(len(self.cache)),
            "cached_states": float(len(self.state_cache)),
        }


def solve_linear_system(
    matrix: list[list[float]],
    vector: list[float]
) -> list[float]:
    """Gaussian elimination with partial pivoting."""

    n = len(vector)

    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValidationError("Linear system dimensions do not match.")

    a = [row[:] + [vector[i]] for i, row in enumerate(matrix)]

    for column in range(n):
        pivot = max(
            range(column, n),
            key=lambda row: abs(a[row][column])
        )

        if abs(a[pivot][column]) < EPSILON:
            raise NumericalError(
                "Singular or ill-conditioned linear system."
            )

        a[column], a[pivot] = a[pivot], a[column]

        for row in range(column + 1, n):
            factor = a[row][column] / a[column][column]

            for j in range(column, n + 1):
                a[row][j] -= factor * a[column][j]

    solution = [0.0] * n

    for i in range(n - 1, -1, -1):
        solution[i] = (
            a[i][n]
            - sum(a[i][j] * solution[j] for j in range(i + 1, n))
        ) / a[i][i]

    return solution


class QuantumKernelRidgeClassifier:
    """
    Kernel ridge classifier for binary labels {-1, +1}.

    alpha = (K + lambda * I)^(-1) y
    f(x) = sum_i alpha_i K(x_i, x)
    """

    def __init__(
        self,
        kernel: QuantumFidelityKernel,
        regularization: float = 0.1
    ):
        if not math.isfinite(regularization) or regularization <= 0:
            raise ValidationError(
                "Regularization must be positive and finite."
            )

        self.kernel = kernel
        self.regularization = regularization
        self.training_data: list[tuple[float, ...]] = []
        self.coefficients: list[float] = []
        self.fitted = False

    def fit(
        self,
        features: Sequence[Sequence[float]],
        labels: Sequence[int]
    ):
        if len(features) != len(labels) or len(features) < 2:
            raise ValidationError(
                "At least two matching training samples are required."
            )

        if set(labels) != {-1, 1}:
            raise ValidationError(
                "Training labels must contain both -1 and +1."
            )

        self.training_data = [
            validate_vector(
                row,
                self.kernel.simulator.config.n_qubits
            )
            for row in features
        ]

        if len(set(self.training_data)) != len(self.training_data):
            raise ValidationError(
                "Duplicate training observations are not supported."
            )

        matrix = self.kernel.matrix(self.training_data)

        for i in range(len(matrix)):
            matrix[i][i] += self.regularization

        self.coefficients = solve_linear_system(
            matrix,
            [float(label) for label in labels]
        )

        self.fitted = True
        return self

    def decision_function(
        self,
        features: Sequence[float]
    ) -> float:
        if not self.fitted:
            raise QuantumKernelError("Model has not been fitted.")

        values = [
            self.kernel.evaluate(training, features)
            for training in self.training_data
        ]

        return sum(
            coefficient * value
            for coefficient, value in zip(
                self.coefficients, values
            )
        )

    def predict(self, features: Sequence[float]) -> int:
        return (
            1
            if self.decision_function(features) >= 0
            else -1
        )

    def predict_batch(
        self,
        features: Sequence[Sequence[float]]
    ) -> list[int]:
        return [self.predict(row) for row in features]


def evaluate_classifier(
    actual: Sequence[int],
    predicted: Sequence[int]
) -> Evaluation:
    if len(actual) != len(predicted) or not actual:
        raise ValidationError("Evaluation datasets are incompatible.")

    if any(value not in (-1, 1) for value in actual):
        raise ValidationError("Actual labels must be -1 or +1.")

    if any(value not in (-1, 1) for value in predicted):
        raise ValidationError("Predictions must be -1 or +1.")

    confusion = {
        "true_positive": 0,
        "true_negative": 0,
        "false_positive": 0,
        "false_negative": 0,
    }

    for expected, result in zip(actual, predicted):
        if expected == 1 and result == 1:
            confusion["true_positive"] += 1
        elif expected == -1 and result == -1:
            confusion["true_negative"] += 1
        elif expected == -1:
            confusion["false_positive"] += 1
        else:
            confusion["false_negative"] += 1

    accuracy = sum(
        expected == result
        for expected, result in zip(actual, predicted)
    ) / len(actual)

    return Evaluation(
        accuracy=accuracy,
        predictions=list(predicted),
        actual=list(actual),
        confusion_matrix=confusion
    )


def generate_dataset(seed: int = 42):
    """
    Generate a nonlinear binary classification dataset.

    The class boundary depends on the interaction between
    two input features.
    """
    rng = random.Random(seed)
    features = []
    labels = []

    for _ in range(32):
        x = rng.uniform(-1.2, 1.2)
        z = rng.uniform(-1.2, 1.2)

        label = 1 if math.sin(2 * x) * math.cos(2 * z) >= 0 else -1

        features.append((x, z))
        labels.append(label)

    return features, labels


def main():
    start = time.perf_counter()

    config = CircuitConfig(
        n_qubits=2,
        entanglement=True,
        rotation_scale=2.0
    )

    kernel = QuantumFidelityKernel(config)

    features, labels = generate_dataset()

    # Deterministic train/test split.
    training_features = features[:24]
    training_labels = labels[:24]
    testing_features = features[24:]
    testing_labels = labels[24:]

    classifier = QuantumKernelRidgeClassifier(
        kernel,
        regularization=0.15
    )

    classifier.fit(training_features, training_labels)

    predictions = classifier.predict_batch(testing_features)

    evaluation = evaluate_classifier(
        testing_labels,
        predictions
    )

    training_matrix = kernel.matrix(training_features)

    diagnostics = kernel.diagnostics(training_matrix)

    print("QUANTUM KERNEL CLASSIFICATION")
    print("=" * 45)
    print("Qubits:", config.n_qubits)
    print("Training samples:", len(training_features))
    print("Testing samples:", len(testing_features))
    print("Regularization:", classifier.regularization)
    print(f"Accuracy: {evaluation.accuracy:.4f}")
    print("Confusion matrix:", evaluation.confusion_matrix)
    print("Kernel diagnostics:", diagnostics)
    print(f"Elapsed seconds: {time.perf_counter() - start:.6f}")

    print("\nSample predictions:")

    for actual, predicted in zip(testing_labels, predictions):
        print(f"Actual={actual:+d}, Predicted={predicted:+d}")

    # Fundamental kernel properties.
    assert abs(kernel.evaluate(features[0], features[0]) - 1.0) < 1e-9
    assert abs(
        kernel.evaluate(features[0], features[1])
        - kernel.evaluate(features[1], features[0])
    ) < 1e-9

    assert diagnostics["positive_semidefinite"]
    assert diagnostics["symmetry_error"] < 1e-9

    print("\nAll numerical validation checks passed.")


if __name__ == "__main__":
    main()
