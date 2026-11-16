#!/usr/bin/env python3
"""
Variational Quantum Circuits (VQCs)
Parameterized quantum computation using state-vector simulation,
parameterized gates, expectation values, parameter-shift gradients,
and gradient-descent optimization.

Dependencies: Python 3.10+
External dependencies: None
"""

from __future__ import annotations

import json
import math
import random
import statistics
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence


# ============================================================
# 1. Configuration and domain types
# ============================================================

class GateType(Enum):
    RX = "RX"
    RY = "RY"
    RZ = "RZ"
    CNOT = "CNOT"


class ExperimentStatus(Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class CircuitConfig:
    num_qubits: int = 2
    layers: int = 2
    seed: int = 42

    def __post_init__(self):
        if not 1 <= self.num_qubits <= 12:
            raise ValueError("Qubit count must be between 1 and 12.")
        if not 1 <= self.layers <= 20:
            raise ValueError("Layer count must be between 1 and 20.")


@dataclass
class OptimizationResult:
    initial_cost: float
    final_cost: float
    parameters: list[float]
    iterations: int
    converged: bool
    history: list[float] = field(default_factory=list)


# ============================================================
# 2. Complex-number state-vector operations
# ============================================================

class QuantumState:
    """
    State-vector simulator.

    The amplitude at index i corresponds to the computational
    basis state represented by the binary representation of i.

    Qubit 0 is the least significant bit.
    """

    def __init__(self, num_qubits: int):
        if not 1 <= num_qubits <= 12:
            raise ValueError("Unsupported qubit count.")

        self.num_qubits = num_qubits
        self.dimension = 1 << num_qubits
        self.amplitudes = [0j] * self.dimension
        self.amplitudes[0] = 1 + 0j

    def normalize(self):
        norm = math.sqrt(
            sum(abs(amplitude) ** 2 for amplitude in self.amplitudes)
        )

        if norm <= 1e-15:
            raise ArithmeticError("Cannot normalize a zero state.")

        self.amplitudes = [
            amplitude / norm for amplitude in self.amplitudes
        ]

    def apply_single_qubit_gate(
        self,
        qubit: int,
        matrix: tuple[tuple[complex, complex],
                      tuple[complex, complex]]
    ):
        if not 0 <= qubit < self.num_qubits:
            raise ValueError("Invalid qubit index.")

        mask = 1 << qubit

        for index in range(self.dimension):
            if index & mask:
                continue

            partner = index | mask

            a = self.amplitudes[index]
            b = self.amplitudes[partner]

            self.amplitudes[index] = (
                matrix[0][0] * a + matrix[0][1] * b
            )

            self.amplitudes[partner] = (
                matrix[1][0] * a + matrix[1][1] * b
            )

    def apply_rx(self, qubit: int, theta: float):
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        self.apply_single_qubit_gate(
            qubit,
            (
                (complex(c), complex(0, -s)),
                (complex(0, -s), complex(c))
            )
        )

    def apply_ry(self, qubit: int, theta: float):
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        self.apply_single_qubit_gate(
            qubit,
            (
                (complex(c), complex(-s)),
                (complex(s), complex(c))
            )
        )

    def apply_rz(self, qubit: int, theta: float):
        self.apply_single_qubit_gate(
            qubit,
            (
                (complex(math.cos(theta / 2),
                         -math.sin(theta / 2)), 0j),
                (0j, complex(math.cos(theta / 2),
                             math.sin(theta / 2)))
            )
        )

    def apply_cnot(self, control: int, target: int):
        if control == target:
            raise ValueError("Control and target must differ.")

        if not (
            0 <= control < self.num_qubits
            and 0 <= target < self.num_qubits
        ):
            raise ValueError("Invalid CNOT qubit index.")

        control_mask = 1 << control
        target_mask = 1 << target

        for index in range(self.dimension):
            if index & control_mask and not index & target_mask:
                partner = index | target_mask

                self.amplitudes[index], self.amplitudes[partner] = (
                    self.amplitudes[partner],
                    self.amplitudes[index]
                )

    def probabilities(self) -> list[float]:
        return [
            abs(amplitude) ** 2
            for amplitude in self.amplitudes
        ]

    def expectation_z(self, qubit: int) -> float:
        if not 0 <= qubit < self.num_qubits:
            raise ValueError("Invalid observable qubit.")

        mask = 1 << qubit

        return sum(
            (1.0 if not index & mask else -1.0)
            * abs(amplitude) ** 2
            for index, amplitude in enumerate(self.amplitudes)
        )

    def expectation_zz(self, first: int, second: int) -> float:
        if first == second:
            raise ValueError("Observable requires distinct qubits.")

        if not (
            0 <= first < self.num_qubits
            and 0 <= second < self.num_qubits
        ):
            raise ValueError("Invalid observable qubit.")

        first_mask = 1 << first
        second_mask = 1 << second

        result = 0.0

        for index, amplitude in enumerate(self.amplitudes):
            first_value = 1 if index & first_mask else -1
            second_value = 1 if index & second_mask else -1

            result += (
                first_value * second_value * abs(amplitude) ** 2
            )

        return result

    def sample(self, shots: int, seed: int = 42) -> dict[str, int]:
        if shots <= 0:
            raise ValueError("Shots must be positive.")

        rng = random.Random(seed)
        probabilities = self.probabilities()
        cumulative = []

        running = 0.0

        for probability in probabilities:
            running += probability
            cumulative.append(running)

        counts = {}

        for _ in range(shots):
            value = rng.random()

            low, high = 0, len(cumulative)

            while low < high:
                middle = (low + high) // 2

                if cumulative[middle] < value:
                    low = middle + 1
                else:
                    high = middle

            bitstring = format(low, f"0{self.num_qubits}b")
            counts[bitstring] = counts.get(bitstring, 0) + 1

        return counts


# ============================================================
# 3. Parameterized circuit
# ============================================================

class VariationalCircuit:

    def __init__(self, config: CircuitConfig):
        self.config = config
        self.parameter_count = (
            config.num_qubits * config.layers * 2
        )

    def validate_parameters(self, parameters: Sequence[float]):
        if len(parameters) != self.parameter_count:
            raise ValueError(
                f"Expected {self.parameter_count} parameters, "
                f"received {len(parameters)}."
            )

        if not all(math.isfinite(float(p)) for p in parameters):
            raise ValueError("Parameters must be finite.")

    def execute(
        self,
        parameters: Sequence[float]
    ) -> QuantumState:

        self.validate_parameters(parameters)

        state = QuantumState(self.config.num_qubits)

        position = 0

        for _layer in range(self.config.layers):

            # Local parameterized rotations.
            for qubit in range(self.config.num_qubits):
                state.apply_ry(qubit, parameters[position])
                position += 1

                state.apply_rz(qubit, parameters[position])
                position += 1

            # Entanglement ring.
            if self.config.num_qubits > 1:
                for qubit in range(self.config.num_qubits - 1):
                    state.apply_cnot(qubit, qubit + 1)

                if self.config.num_qubits > 2:
                    state.apply_cnot(
                        self.config.num_qubits - 1, 0
                    )

        return state

    def cost(self, parameters: Sequence[float]) -> float:
        """
        Hamiltonian:
            H = -Z0 - Z1 + 0.5 * Z0Z1

        The implementation generalizes the local Z terms
        to every configured qubit.
        """

        state = self.execute(parameters)

        energy = -sum(
            state.expectation_z(qubit)
            for qubit in range(self.config.num_qubits)
        )

        if self.config.num_qubits > 1:
            energy += 0.5 * state.expectation_zz(0, 1)

        return energy


# ============================================================
# 4. Parameter-shift differentiation
# ============================================================

def parameter_shift_gradient(
    circuit: VariationalCircuit,
    parameters: Sequence[float]
) -> list[float]:
    """
    For a Pauli rotation parameter:
        df/dtheta = 0.5 * (
            f(theta + pi/2) - f(theta - pi/2)
        )
    """

    circuit.validate_parameters(parameters)

    gradient = []

    for index in range(len(parameters)):
        plus = list(parameters)
        minus = list(parameters)

        plus[index] += math.pi / 2
        minus[index] -= math.pi / 2

        derivative = 0.5 * (
            circuit.cost(plus) - circuit.cost(minus)
        )

        gradient.append(derivative)

    return gradient


# ============================================================
# 5. Gradient-descent optimizer
# ============================================================

def optimize(
    circuit: VariationalCircuit,
    initial_parameters: Sequence[float],
    learning_rate: float = 0.08,
    max_iterations: int = 150,
    tolerance: float = 1e-7
) -> OptimizationResult:

    circuit.validate_parameters(initial_parameters)

    if learning_rate <= 0 or not math.isfinite(learning_rate):
        raise ValueError("Learning rate must be finite and positive.")

    if max_iterations <= 0:
        raise ValueError("Iteration count must be positive.")

    if tolerance <= 0:
        raise ValueError("Tolerance must be positive.")

    parameters = list(initial_parameters)
    initial_cost = circuit.cost(parameters)
    history = [initial_cost]

    converged = False

    for iteration in range(1, max_iterations + 1):

        gradient = parameter_shift_gradient(
            circuit, parameters
        )

        gradient_norm = math.sqrt(
            sum(value * value for value in gradient)
        )

        if gradient_norm < tolerance:
            converged = True
            break

        candidate = [
            parameter - learning_rate * derivative
            for parameter, derivative
            in zip(parameters, gradient)
        ]

        candidate_cost = circuit.cost(candidate)

        # Backtracking protects optimization against unstable steps.
        if candidate_cost > history[-1]:
            learning_rate *= 0.5

            if learning_rate < 1e-8:
                break

            continue

        parameters = candidate
        history.append(candidate_cost)

        if abs(history[-2] - history[-1]) < tolerance:
            converged = True
            break

    return OptimizationResult(
        initial_cost=initial_cost,
        final_cost=circuit.cost(parameters),
        parameters=parameters,
        iterations=len(history) - 1,
        converged=converged,
        history=history
    )


# ============================================================
# 6. Measurement and experiment management
# ============================================================

@dataclass
class Experiment:
    experiment_id: str
    configuration: dict
    status: ExperimentStatus = ExperimentStatus.CREATED
    started_at: float | None = None
    completed_at: float | None = None
    result: dict | None = None
    error: str | None = None


class ExperimentManager:

    def __init__(self):
        self.experiments: dict[str, Experiment] = {}

    def register(self, experiment: Experiment):
        if experiment.experiment_id in self.experiments:
            raise ValueError("Duplicate experiment identifier.")

        self.experiments[experiment.experiment_id] = experiment

    def run(
        self,
        experiment_id: str,
        circuit: VariationalCircuit,
        parameters: Sequence[float]
    ) -> Experiment:

        experiment = self.experiments[experiment_id]

        if experiment.status != ExperimentStatus.CREATED:
            raise RuntimeError("Experiment cannot be restarted.")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = time.time()

        try:
            state = circuit.execute(parameters)

            experiment.result = {
                "energy": circuit.cost(parameters),
                "probabilities": state.probabilities(),
                "measurement_counts": state.sample(
                    1000, seed=42
                )
            }

            experiment.status = ExperimentStatus.COMPLETED

        except Exception as exc:
            experiment.status = ExperimentStatus.FAILED
            experiment.error = str(exc)
            raise

        finally:
            experiment.completed_at = time.time()

        return experiment

    def save(self, destination: str):
        payload = []

        for experiment in self.experiments.values():
            item = asdict(experiment)
            item["status"] = experiment.status.value
            payload.append(item)

        path = Path(destination)
        temporary = path.with_suffix(path.suffix + ".tmp")

        # Replace atomically to avoid partially written JSON files.
        temporary.write_text(
            json.dumps(payload, indent=2, allow_nan=False),
            encoding="utf-8"
        )

        temporary.replace(path)


# ============================================================
# 7. Numerical verification
# ============================================================

def verify_quantum_operations():
    state = QuantumState(1)
    state.apply_ry(0, math.pi)

    assert abs(state.expectation_z(0) + 1.0) < 1e-9

    state = QuantumState(2)
    state.apply_ry(0, math.pi / 2)
    state.apply_cnot(0, 1)

    probabilities = state.probabilities()

    assert abs(probabilities[0] - 0.5) < 1e-9
    assert abs(probabilities[3] - 0.5) < 1e-9

    assert abs(state.expectation_zz(0, 1) - 1.0) < 1e-9


def verify_gradient(circuit, parameters):
    analytic = parameter_shift_gradient(circuit, parameters)

    epsilon = 1e-6

    for index, derivative in enumerate(analytic):
        plus = list(parameters)
        minus = list(parameters)

        plus[index] += epsilon
        minus[index] -= epsilon

        numerical = (
            circuit.cost(plus) - circuit.cost(minus)
        ) / (2 * epsilon)

        assert abs(derivative - numerical) < 1e-5


# ============================================================
# 8. Main execution
# ============================================================

def main():

    random.seed(42)

    verify_quantum_operations()

    config = CircuitConfig(
        num_qubits=2,
        layers=2,
        seed=42
    )

    circuit = VariationalCircuit(config)

    rng = random.Random(config.seed)

    initial_parameters = [
        rng.uniform(-0.5, 0.5)
        for _ in range(circuit.parameter_count)
    ]

    verify_gradient(circuit, initial_parameters)

    initial_state = circuit.execute(initial_parameters)

    print("VARIATIONAL QUANTUM CIRCUIT EXPERIMENT")
    print("=" * 48)
    print("Qubits:", config.num_qubits)
    print("Layers:", config.layers)
    print("Parameters:", circuit.parameter_count)
    print("Initial energy:", round(circuit.cost(initial_parameters), 8))

    result = optimize(
        circuit,
        initial_parameters,
        learning_rate=0.08,
        max_iterations=150
    )

    final_state = circuit.execute(result.parameters)

    print("\nOPTIMIZATION")
    print("Initial energy:", round(result.initial_cost, 8))
    print("Final energy:", round(result.final_cost, 8))
    print("Iterations:", result.iterations)
    print("Converged:", result.converged)

    print("\nOPTIMIZED PARAMETERS")
    for index, parameter in enumerate(result.parameters):
        print(f"theta[{index}] = {parameter:.8f}")

    print("\nFINAL STATE PROBABILITIES")

    for index, probability in enumerate(final_state.probabilities()):
        print(
            f"|{index:0{config.num_qubits}b}> : "
            f"{probability:.8f}"
        )

    print("\nMEASUREMENT COUNTS")
    print(final_state.sample(1000, seed=42))

    manager = ExperimentManager()

    experiment = Experiment(
        experiment_id="vqc-two-qubit-001",
        configuration=asdict(config)
    )

    manager.register(experiment)

    manager.run(
        experiment.experiment_id,
        circuit,
        result.parameters
    )

    manager.save("vqc_experiments.json")

    print("\nExperiment status:", experiment.status.value)
    print("Experiment records saved to vqc_experiments.json")

    assert abs(
        sum(final_state.probabilities()) - 1.0
    ) < 1e-9

    print("\nAll verification checks passed.")


if __name__ == "__main__":
    main()
