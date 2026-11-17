#!/usr/bin/env python3
"""
Variational Quantum Eigensolver (VQE)
A self-contained implementation using Python's standard library.

Features:
- Pauli Hamiltonian representation
- Parameterized quantum circuit using Ry rotations
- Statevector simulation
- Expectation-value calculation
- Parameter-shift gradient
- Gradient-descent optimization
- Measurement-shot simulation
- Exact analytical ground-state comparison
- Experiment tracking and validation
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Callable


class Pauli(Enum):
    I = "I"
    X = "X"
    Y = "Y"
    Z = "Z"


class ExperimentStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PauliTerm:
    coefficient: float
    operator: str

    def __post_init__(self):
        if not math.isfinite(self.coefficient):
            raise ValueError("Hamiltonian coefficient must be finite.")

        if not self.operator:
            raise ValueError("Pauli operator cannot be empty.")

        if any(char not in "IXYZ" for char in self.operator):
            raise ValueError("Invalid Pauli operator.")

    @property
    def qubits(self) -> int:
        return len(self.operator)


@dataclass
class OptimizationRecord:
    iteration: int
    parameters: list[float]
    energy: float
    gradient_norm: float


@dataclass
class VQEConfig:
    learning_rate: float = 0.15
    max_iterations: int = 300
    tolerance: float = 1e-10
    initial_parameters: tuple[float, ...] = (0.5,)
    shots: int = 0
    seed: int = 42

    def validate(self):
        if self.learning_rate <= 0:
            raise ValueError("Learning rate must be positive.")

        if self.max_iterations <= 0:
            raise ValueError("Maximum iterations must be positive.")

        if self.tolerance <= 0:
            raise ValueError("Tolerance must be positive.")

        if self.shots < 0:
            raise ValueError("Shots cannot be negative.")

        if not self.initial_parameters:
            raise ValueError("At least one parameter is required.")


class StatevectorSimulator:
    """Statevector simulator for single-qubit Pauli Hamiltonians."""

    def __init__(self, qubits: int = 1):
        if qubits != 1:
            raise ValueError("This educational simulator supports one qubit.")

        self.qubits = qubits

    @staticmethod
    def ry(theta: float) -> list[complex]:
        """Apply an Ry rotation to the initial |0> state."""
        return [
            complex(math.cos(theta / 2), 0),
            complex(math.sin(theta / 2), 0)
        ]

    @staticmethod
    def pauli_expectation(
        state: list[complex],
        operator: str
    ) -> float:
        if len(operator) != 1:
            raise ValueError("Expected a single-qubit Pauli operator.")

        alpha, beta = state

        if operator == "I":
            result = abs(alpha) ** 2 + abs(beta) ** 2
        elif operator == "X":
            result = 2 * (alpha.conjugate() * beta).real
        elif operator == "Y":
            result = 2 * (alpha.conjugate() * complex(0, -1) * beta).real
        elif operator == "Z":
            result = abs(alpha) ** 2 - abs(beta) ** 2
        else:
            raise ValueError("Unsupported Pauli operator.")

        return float(result)

    def apply_pauli(
        self,
        state: list[complex],
        operator: str
    ) -> list[complex]:
        alpha, beta = state

        if operator == "I":
            return state.copy()
        if operator == "X":
            return [beta, alpha]
        if operator == "Y":
            return [-1j * beta, 1j * alpha]
        if operator == "Z":
            return [alpha, -beta]

        raise ValueError("Unsupported Pauli operator.")


class Hamiltonian:
    """Represents H = sum(c_i * P_i)."""

    def __init__(self, terms: list[PauliTerm]):
        if not terms:
            raise ValueError("Hamiltonian requires at least one term.")

        qubit_counts = {term.qubits for term in terms}

        if len(qubit_counts) != 1:
            raise ValueError("All Hamiltonian terms must have equal width.")

        self.terms = tuple(terms)
        self.qubits = next(iter(qubit_counts))

    def expectation(self, state: list[complex]) -> float:
        energy = 0.0

        for term in self.terms:
            value = StatevectorSimulator.pauli_expectation(
                state,
                term.operator
            )
            energy += term.coefficient * value

        return energy

    def exact_single_qubit_ground_energy(self) -> float:
        """
        For H = aI + bX + cY + dZ:
        Eigenvalues = a +/- sqrt(b²+c²+d²).
        """
        if self.qubits != 1:
            raise ValueError("Analytical comparison requires one qubit.")

        coefficients = {"I": 0.0, "X": 0.0, "Y": 0.0, "Z": 0.0}

        for term in self.terms:
            coefficients[term.operator] += term.coefficient

        a = coefficients["I"]
        b = coefficients["X"]
        c = coefficients["Y"]
        d = coefficients["Z"]

        return a - math.sqrt(b * b + c * c + d * d)


class MeasurementSimulator:
    """Simulates finite-shot measurements of Pauli observables."""

    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)

    def measure(
        self,
        expectation: float,
        shots: int
    ) -> float:
        if shots <= 0:
            raise ValueError("Shots must be positive.")

        if not -1.0 <= expectation <= 1.0:
            raise ValueError("Pauli expectation must be in [-1, 1].")

        probability_positive = (1.0 + expectation) / 2.0

        positive = sum(
            self.random.random() < probability_positive
            for _ in range(shots)
        )

        return 2.0 * positive / shots - 1.0


class VQE:
    """Variational Quantum Eigensolver optimization engine."""

    def __init__(
        self,
        hamiltonian: Hamiltonian,
        config: VQEConfig
    ):
        config.validate()

        if hamiltonian.qubits != 1:
            raise ValueError("VQE requires a one-qubit Hamiltonian.")

        self.hamiltonian = hamiltonian
        self.config = config
        self.simulator = StatevectorSimulator()
        self.measurements = MeasurementSimulator(config.seed)
        self.history: list[OptimizationRecord] = []
        self.status = ExperimentStatus.CREATED

    def state(self, parameters: list[float]) -> list[complex]:
        if len(parameters) != 1:
            raise ValueError("Exactly one variational parameter is required.")

        if not math.isfinite(parameters[0]):
            raise ValueError("Parameter must be finite.")

        return self.simulator.ry(parameters[0])

    def energy(self, parameters: list[float]) -> float:
        state = self.state(parameters)

        if self.config.shots == 0:
            return self.hamiltonian.expectation(state)

        total = 0.0

        for term in self.hamiltonian.terms:
            exact_value = self.simulator.pauli_expectation(
                state,
                term.operator
            )

            measured_value = self.measurements.measure(
                exact_value,
                self.config.shots
            )

            total += term.coefficient * measured_value

        return total

    def exact_energy(self, parameters: list[float]) -> float:
        return self.hamiltonian.expectation(self.state(parameters))

    def gradient(self, parameters: list[float]) -> list[float]:
        """
        Parameter-shift rule:
        dE/dtheta = [E(theta + pi/2) - E(theta - pi/2)] / 2.
        """
        gradients = []

        for index in range(len(parameters)):
            plus = parameters.copy()
            minus = parameters.copy()

            plus[index] += math.pi / 2
            minus[index] -= math.pi / 2

            gradient = (
                self.energy(plus) - self.energy(minus)
            ) / 2.0

            gradients.append(gradient)

        return gradients

    def optimize(self) -> OptimizationRecord:
        self.status = ExperimentStatus.RUNNING
        parameters = list(self.config.initial_parameters)

        try:
            for iteration in range(self.config.max_iterations):
                current_energy = self.energy(parameters)
                gradients = self.gradient(parameters)

                gradient_norm = math.sqrt(
                    sum(value * value for value in gradients)
                )

                record = OptimizationRecord(
                    iteration=iteration,
                    parameters=parameters.copy(),
                    energy=current_energy,
                    gradient_norm=gradient_norm
                )

                self.history.append(record)

                if gradient_norm < self.config.tolerance:
                    break

                parameters = [
                    parameter - self.config.learning_rate * gradient
                    for parameter, gradient
                    in zip(parameters, gradients)
                ]

                # Normalize the rotation angle to a stable interval.
                parameters = [
                    math.remainder(parameter, 2 * math.pi)
                    for parameter in parameters
                ]

            final_record = OptimizationRecord(
                iteration=len(self.history),
                parameters=parameters.copy(),
                energy=self.exact_energy(parameters),
                gradient_norm=0.0
            )

            self.status = ExperimentStatus.COMPLETED
            return final_record

        except Exception:
            self.status = ExperimentStatus.FAILED
            raise

    def report(self) -> dict:
        if self.status != ExperimentStatus.COMPLETED:
            raise RuntimeError("Experiment has not completed.")

        best = min(self.history, key=lambda item: item.energy)

        exact_ground = (
            self.hamiltonian.exact_single_qubit_ground_energy()
        )

        return {
            "algorithm": "Variational Quantum Eigensolver",
            "status": self.status.value,
            "hamiltonian": [
                asdict(term) for term in self.hamiltonian.terms
            ],
            "iterations": len(self.history),
            "best_observed_energy": best.energy,
            "final_variational_energy": self.history[-1].energy,
            "exact_ground_energy": exact_ground,
            "absolute_energy_error": abs(
                self.history[-1].energy - exact_ground
            ),
            "optimized_parameters": self.history[-1].parameters,
            "measurement_shots": self.config.shots
        }


def save_report(report: dict, filename: str = "vqe_results.json"):
    """Write experiment results using atomic replacement."""
    destination = Path(filename)
    temporary = destination.with_suffix(".tmp")

    try:
        temporary.write_text(
            json.dumps(report, indent=4),
            encoding="utf-8"
        )
        temporary.replace(destination)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Could not save experiment: {error}") from error


def run_tests():
    """Basic numerical and validation tests."""
    simulator = StatevectorSimulator()

    state = simulator.ry(math.pi / 2)

    assert abs(
        simulator.pauli_expectation(state, "X") - 1.0
    ) < 1e-10

    assert abs(
        simulator.pauli_expectation(state, "Z")
    ) < 1e-10

    hamiltonian = Hamiltonian([
        PauliTerm(-1.0, "Z"),
        PauliTerm(-0.5, "X")
    ])

    expected = -math.sqrt(1.25)

    assert abs(
        hamiltonian.exact_single_qubit_ground_energy() - expected
    ) < 1e-10

    try:
        PauliTerm(1.0, "A")
        raise AssertionError("Invalid Pauli operator was accepted.")
    except ValueError:
        pass


def main():
    run_tests()

    # H = -Z - 0.5X
    hamiltonian = Hamiltonian([
        PauliTerm(-1.0, "Z"),
        PauliTerm(-0.5, "X")
    ])

    config = VQEConfig(
        learning_rate=0.15,
        max_iterations=300,
        tolerance=1e-10,
        initial_parameters=(0.5,),
        shots=0,
        seed=42
    )

    solver = VQE(hamiltonian, config)
    result = solver.optimize()

    report = solver.report()

    print("VARIATIONAL QUANTUM EIGENSOLVER")
    print("=" * 45)
    print(json.dumps(report, indent=4))

    save_report(report)

    print("\nExperiment completed successfully.")
    print(f"Final energy: {result.energy:.12f}")
    print(f"Exact energy: {report['exact_ground_energy']:.12f}")
    print("Results saved to vqe_results.json")


if __name__ == "__main__":
    main()
