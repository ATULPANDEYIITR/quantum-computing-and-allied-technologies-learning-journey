#!/usr/bin/env python3
"""
QAOA Implementation for Combinatorial Optimization.

Problem: Maximum Cut (MaxCut)
Method: Quantum Approximate Optimization Algorithm (QAOA), p = 1
Simulator: Exact statevector simulation
Optimizer: Parameter grid search
"""

from __future__ import annotations

import cmath
import itertools
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Edge:
    u: int
    v: int
    weight: float = 1.0


@dataclass
class OptimizationResult:
    gamma: float
    beta: float
    expected_cut: float
    best_bitstring: str
    best_cut: float
    classical_optimum: float
    approximation_ratio: float
    evaluations: int


class Graph:
    def __init__(self, vertices: int, edges: Sequence[Edge]):
        if vertices < 2 or vertices > 20:
            raise ValueError("Vertices must be between 2 and 20.")

        self.vertices = vertices
        self.edges = tuple(edges)

        for edge in self.edges:
            if not (0 <= edge.u < vertices and 0 <= edge.v < vertices):
                raise ValueError("Edge references an invalid vertex.")
            if edge.u == edge.v:
                raise ValueError("Self-loops are not supported.")
            if not math.isfinite(edge.weight) or edge.weight <= 0:
                raise ValueError("Edge weights must be positive and finite.")

    def cut_value(self, bitstring: str) -> float:
        if len(bitstring) != self.vertices:
            raise ValueError("Incorrect bitstring length.")
        if any(bit not in "01" for bit in bitstring):
            raise ValueError("Bitstring must contain only 0 and 1.")

        return sum(
            edge.weight
            for edge in self.edges
            if bitstring[edge.u] != bitstring[edge.v]
        )

    def classical_optimum(self) -> tuple[float, str]:
        best_value = -math.inf
        best_state = ""

        # Fixing the first bit removes the complementary symmetry.
        for assignment in itertools.product(
            "01", repeat=self.vertices - 1
        ):
            state = "0" + "".join(assignment)
            value = self.cut_value(state)

            if value > best_value:
                best_value = value
                best_state = state

        return best_value, best_state


class StateVectorSimulator:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.n = graph.vertices
        self.dimension = 1 << self.n

    def initial_state(self) -> list[complex]:
        amplitude = 1.0 / math.sqrt(self.dimension)
        return [complex(amplitude, 0.0)] * self.dimension

    def apply_cost_layer(
        self, state: list[complex], gamma: float
    ) -> None:
        # U_C = exp(-i * gamma * C).
        # Every edge contributes a phase when its endpoints differ.
        for index in range(self.dimension):
            cost = sum(
                edge.weight
                for edge in self.graph.edges
                if ((index >> edge.u) & 1)
                != ((index >> edge.v) & 1)
            )
            state[index] *= cmath.exp(-1j * gamma * cost)

    def apply_mixer_layer(
        self, state: list[complex], beta: float
    ) -> None:
        # Apply exp(-i * beta * X) independently to each qubit.
        cosine = math.cos(beta)
        sine = -1j * math.sin(beta)

        for qubit in range(self.n):
            mask = 1 << qubit

            for index in range(self.dimension):
                if index & mask:
                    continue

                partner = index | mask
                a = state[index]
                b = state[partner]

                state[index] = cosine * a + sine * b
                state[partner] = sine * a + cosine * b

    def run(self, gamma: float, beta: float) -> list[complex]:
        if not math.isfinite(gamma) or not math.isfinite(beta):
            raise ValueError("Parameters must be finite.")

        state = self.initial_state()
        self.apply_cost_layer(state, gamma)
        self.apply_mixer_layer(state, beta)

        return state

    def probabilities(
        self, state: Sequence[complex]
    ) -> list[float]:
        return [abs(amplitude) ** 2 for amplitude in state]

    def expected_cut(self, state: Sequence[complex]) -> float:
        probabilities = self.probabilities(state)

        return sum(
            probabilities[index]
            * self.graph.cut_value(format(index, f"0{self.n}b")[::-1])
            for index in range(self.dimension)
        )

    def sample_best_state(
        self, state: Sequence[complex]
    ) -> tuple[str, float]:
        probabilities = self.probabilities(state)
        index = max(range(self.dimension), key=probabilities.__getitem__)

        bitstring = format(index, f"0{self.n}b")[::-1]
        return bitstring, self.graph.cut_value(bitstring)


class QAOAOptimizer:
    def __init__(
        self,
        simulator: StateVectorSimulator,
        gamma_steps: int = 40,
        beta_steps: int = 40,
    ):
        if gamma_steps < 2 or beta_steps < 2:
            raise ValueError("Grid dimensions must be at least 2.")

        self.simulator = simulator
        self.gamma_steps = gamma_steps
        self.beta_steps = beta_steps

    def optimize(self) -> OptimizationResult:
        best_expected = -math.inf
        best_parameters = (0.0, 0.0)
        best_state = None
        evaluations = 0

        # Search the p=1 parameter space.
        for i in range(self.gamma_steps):
            gamma = 2.0 * math.pi * i / self.gamma_steps

            for j in range(self.beta_steps):
                beta = math.pi * j / self.beta_steps

                state = self.simulator.run(gamma, beta)
                expected = self.simulator.expected_cut(state)
                evaluations += 1

                if expected > best_expected:
                    best_expected = expected
                    best_parameters = (gamma, beta)
                    best_state = state

        assert best_state is not None

        bitstring, best_cut = self.simulator.sample_best_state(best_state)
        classical_optimum, _ = (
            self.simulator.graph.classical_optimum()
        )

        ratio = (
            best_expected / classical_optimum
            if classical_optimum > 0
            else 0.0
        )

        return OptimizationResult(
            gamma=best_parameters[0],
            beta=best_parameters[1],
            expected_cut=best_expected,
            best_bitstring=bitstring,
            best_cut=best_cut,
            classical_optimum=classical_optimum,
            approximation_ratio=ratio,
            evaluations=evaluations,
        )


def verify_simulator(
    simulator: StateVectorSimulator,
    graph: Graph,
) -> None:
    state = simulator.run(0.0, 0.0)

    assert len(state) == 1 << graph.vertices

    probability_sum = sum(
        simulator.probabilities(state)
    )
    assert math.isclose(probability_sum, 1.0, abs_tol=1e-10)

    # At gamma=beta=0, the initial uniform distribution is unchanged.
    expected = sum(
        graph.cut_value(format(i, f"0{graph.vertices}b")[::-1])
        for i in range(1 << graph.vertices)
    ) / (1 << graph.vertices)

    assert math.isclose(
        simulator.expected_cut(state), expected, abs_tol=1e-10
    )


def save_result(
    result: OptimizationResult,
    filename: str = "qaoa_result.json",
) -> None:
    path = Path(filename)
    temporary = path.with_suffix(path.suffix + ".tmp")

    try:
        temporary.write_text(
            json.dumps(asdict(result), indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def main() -> None:
    graph = Graph(
        vertices=6,
        edges=[
            Edge(0, 1, 1.0),
            Edge(0, 2, 1.0),
            Edge(1, 2, 1.0),
            Edge(1, 3, 1.0),
            Edge(2, 4, 1.0),
            Edge(3, 4, 1.0),
            Edge(3, 5, 1.0),
            Edge(4, 5, 1.0),
            Edge(0, 5, 1.0),
        ],
    )

    simulator = StateVectorSimulator(graph)
    verify_simulator(simulator, graph)

    optimizer = QAOAOptimizer(
        simulator,
        gamma_steps=40,
        beta_steps=40,
    )

    result = optimizer.optimize()

    print("QAOA MAX-CUT OPTIMIZATION")
    print("=" * 45)
    print(f"Vertices:              {graph.vertices}")
    print(f"Edges:                 {len(graph.edges)}")
    print(f"QAOA depth (p):        1")
    print(f"Optimal gamma:         {result.gamma:.6f}")
    print(f"Optimal beta:          {result.beta:.6f}")
    print(f"Expected cut:          {result.expected_cut:.6f}")
    print(f"Most probable state:   {result.best_bitstring}")
    print(f"Observed cut:          {result.best_cut:.6f}")
    print(f"Classical optimum:     {result.classical_optimum:.6f}")
    print(f"Approximation ratio:   {result.approximation_ratio:.4f}")
    print(f"Parameter evaluations: {result.evaluations}")

    save_result(result)
    print("Result saved to qaoa_result.json")


if __name__ == "__main__":
    main()
