#!/usr/bin/env python3
"""
Variational Quantum Eigensolver (VQE)
Application: Ground-state energy estimation for molecular hydrogen (H2).

Implements:
- Pauli Hamiltonian representation.
- Two-qubit statevector simulation.
- Parameterized quantum circuit.
- Variational energy measurement.
- Parameter-shift gradient estimation.
- Adam optimization.
- Exact diagonalization for validation.
- Experiment tracking and JSON export.

Dependencies: Python 3.10+
"""

from __future__ import annotations

import json
import math
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

import numpy as np


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

LOGGER = logging.getLogger("VQE")

SEED = 42
TOLERANCE = 1e-9


# ---------------------------------------------------------
# 1. Molecular Hamiltonian
# ---------------------------------------------------------

@dataclass(frozen=True)
class PauliTerm:
    coefficient: float
    operators: str

    def __post_init__(self):
        if not math.isfinite(self.coefficient):
            raise ValueError("Hamiltonian coefficient must be finite.")

        if not self.operators:
            raise ValueError("Pauli operator string cannot be empty.")

        if any(p not in "IXYZ" for p in self.operators):
            raise ValueError("Only I, X, Y and Z operators are supported.")


class Hamiltonian:
    """Real-valued molecular Hamiltonian represented by Pauli strings."""

    MATRICES = {
        "I": np.array([[1, 0], [0, 1]], dtype=complex),
        "X": np.array([[0, 1], [1, 0]], dtype=complex),
        "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
        "Z": np.array([[1, 0], [0, -1]], dtype=complex),
    }

    def __init__(self, terms: list[PauliTerm]):
        if not terms:
            raise ValueError("Hamiltonian requires at least one term.")

        self.terms = tuple(terms)
        self.num_qubits = len(terms[0].operators)

        if any(len(t.operators) != self.num_qubits for t in terms):
            raise ValueError("All Pauli strings must have equal length.")

        self.matrix = self._build_matrix()

        if not np.allclose(self.matrix, self.matrix.conj().T):
            raise ValueError("Hamiltonian must be Hermitian.")

    def _build_matrix(self) -> np.ndarray:
        dimension = 2 ** self.num_qubits
        result = np.zeros((dimension, dimension), dtype=complex)

        for term in self.terms:
            operator = np.array([[1]], dtype=complex)

            for symbol in term.operators:
                operator = np.kron(
                    operator,
                    self.MATRICES[symbol]
                )

            result += term.coefficient * operator

        return result

    def energy(self, state: np.ndarray) -> float:
        value = np.vdot(state, self.matrix @ state)

        if abs(value.imag) > 1e-8:
            raise ArithmeticError("Expected a real energy.")

        return float(value.real)

    def exact_ground_energy(self) -> float:
        return float(np.linalg.eigvalsh(self.matrix)[0])


def hydrogen_hamiltonian() -> Hamiltonian:
    """
    Two-qubit reduced H2 Hamiltonian.

    STO-3G molecular model at an approximately 0.735 angstrom
    internuclear separation, using a commonly employed
    reduced-qubit representation.

    Energy units: Hartree.
    """

    return Hamiltonian([
        PauliTerm(-1.052373245772859, "II"),
        PauliTerm(0.39793742484318045, "ZI"),
        PauliTerm(-0.39793742484318045, "IZ"),
        PauliTerm(-0.01128010425623538, "ZZ"),
        PauliTerm(0.18093119978423156, "XX"),
    ])


# ---------------------------------------------------------
# 2. Quantum circuit simulation
# ---------------------------------------------------------

def ry(theta: float) -> np.ndarray:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)

    return np.array([
        [c, -s],
        [s, c]
    ], dtype=complex)


def apply_single_qubit(
    state: np.ndarray,
    gate: np.ndarray,
    qubit: int,
    num_qubits: int
) -> np.ndarray:
    """Apply a one-qubit gate using tensor reshaping."""

    tensor = state.reshape([2] * num_qubits)

    transformed = np.tensordot(
        gate,
        tensor,
        axes=([1], [qubit])
    )

    transformed = np.moveaxis(transformed, 0, qubit)

    return transformed.reshape(-1)


def apply_cnot(
    state: np.ndarray,
    control: int,
    target: int,
    num_qubits: int
) -> np.ndarray:
    """Apply CNOT using computational-basis indexing."""

    result = np.zeros_like(state)

    for index, amplitude in enumerate(state):
        bits = list(format(index, f"0{num_qubits}b"))

        if bits[control] == "1":
            bits[target] = "0" if bits[target] == "1" else "1"

        destination = int("".join(bits), 2)
        result[destination] = amplitude

    return result


class QuantumAnsatz:
    """
    Two-qubit real-valued variational circuit.

    Circuit:
        |00>
         |
        RY(theta_0) on qubit 0
        RY(theta_1) on qubit 1
         |
        CNOT(0, 1)
         |
        Measurement
    """

    def __init__(self, num_qubits: int = 2):
        if num_qubits != 2:
            raise ValueError("This ansatz is designed for two qubits.")

        self.num_qubits = num_qubits
        self.num_parameters = 2

    def statevector(self, parameters: np.ndarray) -> np.ndarray:
        parameters = np.asarray(parameters, dtype=float)

        if parameters.shape != (self.num_parameters,):
            raise ValueError("Exactly two parameters are required.")

        if not np.all(np.isfinite(parameters)):
            raise ValueError("Circuit parameters must be finite.")

        state = np.zeros(4, dtype=complex)
        state[0] = 1.0

        state = apply_single_qubit(
            state, ry(parameters[0]), 0, 2
        )

        state = apply_single_qubit(
            state, ry(parameters[1]), 1, 2
        )

        state = apply_cnot(state, 0, 1, 2)

        return state

    def expectation(
        self,
        hamiltonian: Hamiltonian,
        parameters: np.ndarray
    ) -> float:
        return hamiltonian.energy(self.statevector(parameters))


# ---------------------------------------------------------
# 3. Parameter-shift gradient
# ---------------------------------------------------------

def parameter_shift_gradient(
    objective: Callable[[np.ndarray], float],
    parameters: np.ndarray
) -> np.ndarray:
    """
    Exact parameter-shift rule for gates generated by Pauli Y.

    dE/dtheta = 0.5 * [E(theta + pi/2) - E(theta - pi/2)]
    """

    gradient = np.zeros_like(parameters, dtype=float)
    shift = math.pi / 2

    for index in range(len(parameters)):
        positive = parameters.copy()
        negative = parameters.copy()

        positive[index] += shift
        negative[index] -= shift

        gradient[index] = 0.5 * (
            objective(positive) - objective(negative)
        )

    return gradient


# ---------------------------------------------------------
# 4. Adam optimizer
# ---------------------------------------------------------

@dataclass
class OptimizationRecord:
    iteration: int
    energy: float
    gradient_norm: float
    parameters: list[float]


@dataclass
class VQEResult:
    molecule: str
    energy: float
    exact_energy: float
    absolute_error: float
    parameters: list[float]
    iterations: int
    converged: bool
    history: list[OptimizationRecord]


class AdamOptimizer:

    def __init__(
        self,
        learning_rate: float = 0.05,
        beta1: float = 0.9,
        beta2: float = 0.999,
        epsilon: float = 1e-8
    ):
        if learning_rate <= 0:
            raise ValueError("Learning rate must be positive.")

        if not 0 < beta1 < 1 or not 0 < beta2 < 1:
            raise ValueError("Adam beta parameters must be between 0 and 1.")

        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon

    def minimize(
        self,
        objective: Callable[[np.ndarray], float],
        initial_parameters: np.ndarray,
        max_iterations: int = 2000,
        tolerance: float = 1e-9
    ) -> tuple[np.ndarray, list[OptimizationRecord], bool]:

        if max_iterations <= 0:
            raise ValueError("Maximum iterations must be positive.")

        parameters = np.asarray(
            initial_parameters, dtype=float
        ).copy()

        if parameters.ndim != 1 or not np.all(np.isfinite(parameters)):
            raise ValueError("Invalid initial parameters.")

        first_moment = np.zeros_like(parameters)
        second_moment = np.zeros_like(parameters)

        history = []
        converged = False

        previous_energy = objective(parameters)

        for iteration in range(1, max_iterations + 1):

            gradient = parameter_shift_gradient(
                objective,
                parameters
            )

            gradient_norm = float(np.linalg.norm(gradient))

            first_moment = (
                self.beta1 * first_moment
                + (1 - self.beta1) * gradient
            )

            second_moment = (
                self.beta2 * second_moment
                + (1 - self.beta2) * gradient ** 2
            )

            corrected_first = (
                first_moment / (1 - self.beta1 ** iteration)
            )

            corrected_second = (
                second_moment / (1 - self.beta2 ** iteration)
            )

            parameters -= (
                self.learning_rate
                * corrected_first
                / (np.sqrt(corrected_second) + self.epsilon)
            )

            parameters = (parameters + math.pi) % (2 * math.pi) - math.pi

            current_energy = objective(parameters)

            if not math.isfinite(current_energy):
                raise ArithmeticError("Non-finite energy encountered.")

            history.append(
                OptimizationRecord(
                    iteration=iteration,
                    energy=current_energy,
                    gradient_norm=gradient_norm,
                    parameters=parameters.tolist()
                )
            )

            if iteration % 100 == 0:
                LOGGER.info(
                    "Iteration %d | Energy %.12f Ha | Gradient %.3e",
                    iteration,
                    current_energy,
                    gradient_norm
                )

            energy_change = abs(current_energy - previous_energy)

            if (
                gradient_norm < tolerance
                and energy_change < tolerance
            ):
                converged = True
                break

            previous_energy = current_energy

        return parameters, history, converged


# ---------------------------------------------------------
# 5. Multi-start VQE experiment
# ---------------------------------------------------------

class VQEExperiment:

    def __init__(
        self,
        hamiltonian: Hamiltonian,
        molecule: str = "H2"
    ):
        self.hamiltonian = hamiltonian
        self.molecule = molecule
        self.ansatz = QuantumAnsatz(hamiltonian.num_qubits)

    def run(
        self,
        initial_parameters: np.ndarray | None = None,
        learning_rate: float = 0.05,
        max_iterations: int = 2000,
        tolerance: float = TOLERANCE
    ) -> VQEResult:

        if initial_parameters is None:
            initial_parameters = np.array([0.2, -0.4])

        objective = lambda p: self.ansatz.expectation(
            self.hamiltonian, p
        )

        optimizer = AdamOptimizer(learning_rate=learning_rate)

        parameters, history, converged = optimizer.minimize(
            objective,
            initial_parameters,
            max_iterations,
            tolerance
        )

        energy = objective(parameters)
        exact_energy = self.hamiltonian.exact_ground_energy()

        return VQEResult(
            molecule=self.molecule,
            energy=energy,
            exact_energy=exact_energy,
            absolute_error=abs(energy - exact_energy),
            parameters=parameters.tolist(),
            iterations=len(history),
            converged=converged,
            history=history
        )


# ---------------------------------------------------------
# 6. Measurement and sampling simulation
# ---------------------------------------------------------

def sample_computational_basis(
    state: np.ndarray,
    shots: int = 10000,
    seed: int = SEED
) -> dict[str, int]:

    if shots <= 0:
        raise ValueError("Shots must be positive.")

    probabilities = np.abs(state) ** 2

    if not np.isclose(probabilities.sum(), 1.0, atol=1e-9):
        raise ValueError("Statevector must be normalized.")

    rng = np.random.default_rng(seed)

    samples = rng.multinomial(shots, probabilities)

    return {
        format(index, f"0{int(math.log2(len(state)))}b"): int(count)
        for index, count in enumerate(samples)
        if count > 0
    }


# ---------------------------------------------------------
# 7. Persistence
# ---------------------------------------------------------

def save_result(
    result: VQEResult,
    filename: str = "vqe_h2_results.json"
) -> None:

    output = {
        "molecule": result.molecule,
        "energy_hartree": result.energy,
        "exact_energy_hartree": result.exact_energy,
        "absolute_error_hartree": result.absolute_error,
        "parameters": result.parameters,
        "iterations": result.iterations,
        "converged": result.converged,
        "history": [
            asdict(record) for record in result.history
        ]
    }

    path = Path(filename)

    # Prevent accidental writes outside the selected filename's directory.
    if path.name != filename or path.suffix.lower() != ".json":
        raise ValueError("Provide a simple JSON filename.")

    temporary = path.with_suffix(".json.tmp")

    try:
        temporary.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8"
        )
        temporary.replace(path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------
# 8. Validation and execution
# ---------------------------------------------------------

def run_validation() -> None:

    hamiltonian = hydrogen_hamiltonian()

    assert hamiltonian.num_qubits == 2
    assert np.allclose(
        hamiltonian.matrix,
        hamiltonian.matrix.conj().T
    )

    circuit = QuantumAnsatz()

    state = circuit.statevector(np.array([0.0, 0.0]))

    assert np.isclose(np.linalg.norm(state), 1.0)

    exact_energy = hamiltonian.exact_ground_energy()

    assert exact_energy < 0

    LOGGER.info("Hamiltonian validation passed.")
    LOGGER.info("Exact ground-state energy: %.12f Ha", exact_energy)


def main() -> None:

    run_validation()

    hamiltonian = hydrogen_hamiltonian()

    experiment = VQEExperiment(hamiltonian)

    result = experiment.run(
        initial_parameters=np.array([0.2, -0.4]),
        learning_rate=0.05,
        max_iterations=2000
    )

    final_state = experiment.ansatz.statevector(
        np.array(result.parameters)
    )

    counts = sample_computational_basis(final_state)

    print("\n========== VQE RESULT ==========")
    print(f"Molecule:             {result.molecule}")
    print(f"Optimized energy:     {result.energy:.12f} Ha")
    print(f"Exact energy:         {result.exact_energy:.12f} Ha")
    print(f"Absolute error:       {result.absolute_error:.12e} Ha")
    print(f"Iterations:           {result.iterations}")
    print(f"Converged:            {result.converged}")
    print(f"Parameters:           {result.parameters}")

    print("\nComputational basis measurement counts:")
    for state, count in sorted(counts.items()):
        print(f"|{state}>: {count}")

    print("\nEnergy history:")
    for record in result.history[::max(1, len(result.history) // 10)]:
        print(
            f"Iteration {record.iteration:4d}: "
            f"{record.energy:.10f} Ha"
        )

    save_result(result)

    print("\nResults saved to vqe_h2_results.json")


if __name__ == "__main__":
    main()
