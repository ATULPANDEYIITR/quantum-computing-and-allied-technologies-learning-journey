#!/usr/bin/env python3
"""
Quantum Approximate Optimization Algorithm (QAOA)
=================================================
A self-contained statevector implementation for the Max-Cut problem.

Features:
- Graph validation and Max-Cut objective evaluation.
- QAOA cost and mixer Hamiltonian operations.
- Statevector simulation using standard-library complex arithmetic.
- Parameterized QAOA circuits with configurable depth.
- Expectation-value calculation.
- Deterministic coordinate-search optimization.
- Measurement sampling.
- Classical approximation and optimal-solution comparison.
- Numerical and structural validation.

No external dependencies required.
"""

from __future__ import annotations

import cmath
import itertools
import math
import random
from dataclasses import dataclass, field
from typing import Sequence


EPSILON = 1e-10


class QAOAError(Exception):
    """Base exception for QAOA operations."""


class GraphValidationError(QAOAError):
    """Invalid Max-Cut graph."""


class CircuitValidationError(QAOAError):
    """Invalid QAOA circuit parameters."""


@dataclass(frozen=True)
class Edge:
    u: int
    v: int
    weight: float = 1.0


@dataclass
class Graph:
    num_vertices: int
    edges: list[Edge]

    def __post_init__(self) -> None:
        if not isinstance(self.num_vertices, int) or isinstance(
            self.num_vertices, bool
        ):
            raise GraphValidationError("Vertex count must be an integer.")

        if self.num_vertices < 1 or self.num_vertices > 20:
            raise GraphValidationError(
                "Statevector simulation supports 1 to 20 vertices."
            )

        seen = set()

        for edge in self.edges:
            if not (0 <= edge.u < self.num_vertices):
                raise GraphValidationError("Invalid edge endpoint.")

            if not (0 <= edge.v < self.num_vertices):
                raise GraphValidationError("Invalid edge endpoint.")

            if edge.u == edge.v:
                raise GraphValidationError("Self-loops are not supported.")

            if not math.isfinite(edge.weight) or edge.weight <= 0:
                raise GraphValidationError(
                    "Edge weights must be positive and finite."
                )

            key = tuple(sorted((edge.u, edge.v)))

            if key in seen:
                raise GraphValidationError("Duplicate edges are not allowed.")

            seen.add(key)

    def cut_value(self, bitstring: str) -> float:
        if len(bitstring) != self.num_vertices:
            raise ValueError("Bitstring length does not match graph.")

        if any(bit not in "01" for bit in bitstring):
            raise ValueError("Bitstring must contain only 0 and 1.")

        return sum(
            edge.weight
            for edge in self.edges
            if bitstring[edge.u] != bitstring[edge.v]
        )

    def optimal_solution(self) -> tuple[float, list[str]]:
        best = -math.inf
        solutions = []

        for bits in itertools.product("01", repeat=self.num_vertices):
            candidate = "".join(bits)
            value = self.cut_value(candidate)

            if value > best + EPSILON:
                best = value
                solutions = [candidate]
            elif abs(value - best) <= EPSILON:
                solutions.append(candidate)

        return best, solutions


@dataclass
class QAOAResult:
    gamma: list[float]
    beta: list[float]
    expectation: float
    optimal_cut: float
    approximation_ratio: float
    probabilities: dict[str, float]
    best_sample: str
    iterations: int
    history: list[float] = field(default_factory=list)


class StateVector:
    """Statevector representation using little-endian qubit indexing."""

    def __init__(self, num_qubits: int):
        if not 1 <= num_qubits <= 20:
            raise ValueError("Unsupported number of qubits.")

        self.num_qubits = num_qubits
        self.size = 1 << num_qubits
        self.amplitudes = [0j] * self.size

    def initialize_uniform(self) -> None:
        amplitude = 1 / math.sqrt(self.size)

        for i in range(self.size):
            self.amplitudes[i] = complex(amplitude, 0)

    def apply_cost_unitary(
        self,
        graph: Graph,
        gamma: float
    ) -> None:
        """
        Apply exp(-i * gamma * H_C).

        H_C = sum w_uv * (1 - Z_u Z_v) / 2

        Its eigenvalue on a computational basis state is
        the weighted cut value.
        """
        for state in range(self.size):
            bits = format(state, f"0{self.num_qubits}b")
            cut = graph.cut_value(bits)

            phase = cmath.exp(-1j * gamma * cut)
            self.amplitudes[state] *= phase

    def apply_mixer_unitary(self, beta: float) -> None:
        """
        Apply exp(-i * beta * sum(X_i)).

        Each qubit undergoes an independent RX(2*beta) rotation.
        """
        cosine = math.cos(beta)
        sine = math.sin(beta)

        for qubit in range(self.num_qubits):
            mask = 1 << qubit

            for state in range(self.size):
                if state & mask:
                    continue

                partner = state | mask

                a0 = self.amplitudes[state]
                a1 = self.amplitudes[partner]

                self.amplitudes[state] = (
                    cosine * a0 - 1j * sine * a1
                )

                self.amplitudes[partner] = (
                    -1j * sine * a0 + cosine * a1
                )

    def probabilities(self) -> list[float]:
        return [abs(amplitude) ** 2 for amplitude in self.amplitudes]

    def validate_normalization(self) -> None:
        total = sum(self.probabilities())

        if not math.isclose(total, 1.0, abs_tol=1e-8):
            raise QAOAError(
                f"Statevector normalization failed: {total}"
            )


class QAOA:
    def __init__(self, graph: Graph, depth: int = 1):
        if not isinstance(depth, int) or isinstance(depth, bool):
            raise CircuitValidationError("Depth must be an integer.")

        if depth < 1 or depth > 10:
            raise CircuitValidationError("Depth must be between 1 and 10.")

        self.graph = graph
        self.depth = depth
        self.num_qubits = graph.num_vertices

    def validate_parameters(
        self,
        gamma: Sequence[float],
        beta: Sequence[float]
    ) -> None:
        if len(gamma) != self.depth or len(beta) != self.depth:
            raise CircuitValidationError(
                "Parameter count must equal QAOA depth."
            )

        for parameter in list(gamma) + list(beta):
            if not math.isfinite(parameter):
                raise CircuitValidationError(
                    "Circuit parameters must be finite."
                )

    def simulate(
        self,
        gamma: Sequence[float],
        beta: Sequence[float]
    ) -> StateVector:
        self.validate_parameters(gamma, beta)

        state = StateVector(self.num_qubits)
        state.initialize_uniform()

        for layer in range(self.depth):
            state.apply_cost_unitary(
                self.graph,
                gamma[layer]
            )

            state.apply_mixer_unitary(beta[layer])

        state.validate_normalization()
        return state

    def expectation(
        self,
        gamma: Sequence[float],
        beta: Sequence[float]
    ) -> float:
        state = self.simulate(gamma, beta)
        probabilities = state.probabilities()

        return sum(
            probabilities[index]
            * self.graph.cut_value(
                format(index, f"0{self.num_qubits}b")
            )
            for index in range(state.size)
        )

    def optimize(
        self,
        iterations: int = 100,
        step_size: float = 0.15,
        seed: int = 42
    ) -> QAOAResult:
        if iterations < 1:
            raise ValueError("Iterations must be positive.")

        if not math.isfinite(step_size) or step_size <= 0:
            raise ValueError("Step size must be positive and finite.")

        rng = random.Random(seed)

        gamma = [
            rng.uniform(0, math.pi)
            for _ in range(self.depth)
        ]

        beta = [
            rng.uniform(0, math.pi / 2)
            for _ in range(self.depth)
        ]

        best = self.expectation(gamma, beta)
        history = [best]

        # Coordinate search maximizes the expected cut value.
        for iteration in range(iterations):
            improved = False

            for parameters, lower, upper in (
                (gamma, 0.0, math.pi),
                (beta, 0.0, math.pi / 2),
            ):
                for index in range(self.depth):
                    original = parameters[index]
                    best_parameter = original
                    local_best = best

                    for direction in (-1, 1):
                        candidate = max(
                            lower,
                            min(
                                upper,
                                original + direction * step_size
                            )
                        )

                        parameters[index] = candidate

                        value = self.expectation(gamma, beta)

                        if value > local_best + EPSILON:
                            local_best = value
                            best_parameter = candidate

                    parameters[index] = best_parameter

                    if local_best > best + EPSILON:
                        best = local_best
                        improved = True

            history.append(best)

            if not improved:
                step_size *= 0.5

            if step_size < 1e-5:
                break

        final_state = self.simulate(gamma, beta)
        probabilities = final_state.probabilities()

        probability_map = {
            format(index, f"0{self.num_qubits}b"): probability
            for index, probability in enumerate(probabilities)
        }

        best_sample = max(
            probability_map,
            key=probability_map.get
        )

        optimal_cut, _ = self.graph.optimal_solution()

        ratio = (
            best / optimal_cut
            if optimal_cut > EPSILON
            else 1.0
        )

        return QAOAResult(
            gamma=list(gamma),
            beta=list(beta),
            expectation=best,
            optimal_cut=optimal_cut,
            approximation_ratio=ratio,
            probabilities=probability_map,
            best_sample=best_sample,
            iterations=len(history) - 1,
            history=history
        )

    def sample(
        self,
        gamma: Sequence[float],
        beta: Sequence[float],
        shots: int = 1000,
        seed: int = 42
    ) -> dict[str, int]:
        if shots < 1 or shots > 10_000_000:
            raise ValueError("Shots must be between 1 and 10 million.")

        state = self.simulate(gamma, beta)
        probabilities = state.probabilities()

        rng = random.Random(seed)
        outcomes = [0] * len(probabilities)

        for _ in range(shots):
            index = rng.choices(
                range(len(probabilities)),
                weights=probabilities,
                k=1
            )[0]

            outcomes[index] += 1

        return {
            format(index, f"0{self.num_qubits}b"): count
            for index, count in enumerate(outcomes)
            if count > 0
        }


def demonstrate() -> None:
    print("=" * 65)
    print("QUANTUM APPROXIMATE OPTIMIZATION ALGORITHM")
    print("=" * 65)

    graph = Graph(
        num_vertices=4,
        edges=[
            Edge(0, 1),
            Edge(0, 2),
            Edge(1, 2),
            Edge(1, 3),
            Edge(2, 3),
        ]
    )

    qaoa = QAOA(graph, depth=1)

    print("\nGraph")
    print(f"Vertices: {graph.num_vertices}")
    print(f"Edges: {len(graph.edges)}")

    optimum, optimal_solutions = graph.optimal_solution()

    print(f"Classical optimum: {optimum}")
    print(f"Optimal bitstrings: {optimal_solutions}")

    result = qaoa.optimize(
        iterations=100,
        step_size=0.15,
        seed=42
    )

    print("\nOptimization")
    print(f"Depth: {qaoa.depth}")
    print(f"Gamma: {[round(x, 5) for x in result.gamma]}")
    print(f"Beta: {[round(x, 5) for x in result.beta]}")
    print(f"Expected cut: {result.expectation:.6f}")
    print(f"Approximation ratio: {result.approximation_ratio:.6f}")
    print(f"Iterations: {result.iterations}")
    print(f"Most probable sample: {result.best_sample}")

    print("\nMeasurement probabilities")

    for bitstring, probability in sorted(
        result.probabilities.items(),
        key=lambda item: item[1],
        reverse=True
    )[:8]:
        print(
            f"{bitstring}: {probability:.6f}, "
            f"cut={graph.cut_value(bitstring)}"
        )

    print("\nShot-based measurements")

    counts = qaoa.sample(
        result.gamma,
        result.beta,
        shots=2000,
        seed=123
    )

    for bitstring, count in sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True
    )[:8]:
        print(
            f"{bitstring}: {count} shots, "
            f"cut={graph.cut_value(bitstring)}"
        )

    assert result.expectation <= optimum + EPSILON
    assert result.expectation >= -EPSILON
    assert abs(sum(result.probabilities.values()) - 1.0) < 1e-8

    print("\nValidation: PASSED")


if __name__ == "__main__":
    demonstrate()
