from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import Dict, List, Sequence, Tuple
import cmath
import json


class WalkType(Enum):
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"


@dataclass(frozen=True)
class Graph:
    adjacency: Tuple[Tuple[int, ...], ...]

    def __post_init__(self) -> None:
        n = len(self.adjacency)
        if n == 0:
            raise ValueError("Graph must contain at least one vertex.")

        for row in self.adjacency:
            if len(row) != n:
                raise ValueError("Adjacency matrix must be square.")
            if any(value not in (0, 1) for value in row):
                raise ValueError("This implementation accepts a binary adjacency matrix.")

        for i in range(n):
            if self.adjacency[i][i] != 0:
                raise ValueError("Self-loops are not supported.")
            for j in range(n):
                if self.adjacency[i][j] != self.adjacency[j][i]:
                    raise ValueError("The graph must be undirected.")

    @property
    def size(self) -> int:
        return len(self.adjacency)

    def neighbors(self, vertex: int) -> List[int]:
        self.validate_vertex(vertex)
        return [j for j, connected in enumerate(self.adjacency[vertex]) if connected]

    def degree(self, vertex: int) -> int:
        return len(self.neighbors(vertex))

    def validate_vertex(self, vertex: int) -> None:
        if not 0 <= vertex < self.size:
            raise IndexError(f"Vertex {vertex} is outside [0, {self.size - 1}].")


def normalize(state: Sequence[complex]) -> List[complex]:
    norm = sqrt(sum(abs(amplitude) ** 2 for amplitude in state))
    if norm == 0:
        raise ValueError("Cannot normalize the zero vector.")
    return [amplitude / norm for amplitude in state]


def probabilities(state: Sequence[complex]) -> List[float]:
    return [abs(amplitude) ** 2 for amplitude in state]


def classical_random_walk(graph: Graph, start: int, steps: int) -> List[float]:
    graph.validate_vertex(start)
    if steps < 0:
        raise ValueError("steps must be non-negative.")

    distribution = [0.0] * graph.size
    distribution[start] = 1.0

    for _ in range(steps):
        next_distribution = [0.0] * graph.size
        for vertex, mass in enumerate(distribution):
            neighbors = graph.neighbors(vertex)
            if not neighbors:
                next_distribution[vertex] += mass
                continue
            share = mass / len(neighbors)
            for neighbor in neighbors:
                next_distribution[neighbor] += share
        distribution = next_distribution

    return distribution


def hadamard_step(state: Sequence[complex]) -> List[complex]:
    if len(state) != 2:
        raise ValueError("Hadamard operation requires a two-state vector.")

    a, b = state
    factor = 1.0 / sqrt(2.0)
    return [(a + b) * factor, (a - b) * factor]


def one_dimensional_discrete_quantum_walk(
    steps: int,
    initial_coin: Sequence[complex] = (1 / sqrt(2), 1j / sqrt(2)),
) -> Dict[int, float]:
    """
    Simulates a coined quantum walk on a line.

    State keys are (position, coin), where coin 0 moves left and coin 1
    moves right. The Hadamard coin creates interference between paths.
    """
    if steps < 0:
        raise ValueError("steps must be non-negative.")
    if len(initial_coin) != 2:
        raise ValueError("initial_coin must contain two amplitudes.")

    initial = normalize(initial_coin)
    state: Dict[Tuple[int, int], complex] = {
        (0, 0): initial[0],
        (0, 1): initial[1],
    }

    for _ in range(steps):
        after_coin: Dict[Tuple[int, int], complex] = {}

        positions = sorted({position for position, _ in state})
        for position in positions:
            coin_state = [
                state.get((position, 0), 0j),
                state.get((position, 1), 0j),
            ]
            transformed = hadamard_step(coin_state)
            after_coin[(position, 0)] = transformed[0]
            after_coin[(position, 1)] = transformed[1]

        next_state: Dict[Tuple[int, int], complex] = {}
        for (position, coin), amplitude in after_coin.items():
            new_position = position - 1 if coin == 0 else position + 1
            key = (new_position, coin)
            next_state[key] = next_state.get(key, 0j) + amplitude

        state = next_state

    position_probabilities: Dict[int, float] = {}
    for (position, _), amplitude in state.items():
        position_probabilities[position] = (
            position_probabilities.get(position, 0.0) + abs(amplitude) ** 2
        )

    return dict(sorted(position_probabilities.items()))


def continuous_time_quantum_walk(graph: Graph, start: int, time: float) -> List[float]:
    """
    Computes probabilities for a continuous-time quantum walk.

    For small educational graphs, matrix exponentiation is implemented
    directly using a truncated Taylor expansion of exp(-i A t).
    """
    graph.validate_vertex(start)
    if time < 0:
        raise ValueError("time must be non-negative.")

    n = graph.size
    vector = [0j] * n
    vector[start] = 1 + 0j

    # exp(-iAt) = sum_k (-iAt)^k / k!
    # Terms are accumulated until the contribution is negligible.
    result = vector[:]
    term = vector[:]
    matrix = [list(map(complex, row)) for row in graph.adjacency]

    for k in range(1, 80):
        product = [0j] * n
        for i in range(n):
            product[i] = sum(matrix[i][j] * term[j] for j in range(n))

        coefficient = (-1j * time) / k
        term = [coefficient * value for value in product]

        for i in range(n):
            result[i] += term[i]

        if max(abs(value) for value in term) < 1e-14:
            break

    return probabilities(normalize(result))


def search_amplitude(
    graph: Graph,
    start: int,
    target: int,
    time: float,
) -> float:
    """
    Returns the probability of observing target after a continuous-time walk.
    """
    graph.validate_vertex(start)
    graph.validate_vertex(target)
    return continuous_time_quantum_walk(graph, start, time)[target]


def print_distribution(title: str, distribution: Dict[int, float] | List[float]) -> None:
    print(f"\n{title}")
    if isinstance(distribution, dict):
        for position, probability in distribution.items():
            print(f"  {position:>3}: {probability:.8f}")
    else:
        for vertex, probability in enumerate(distribution):
            print(f"  vertex {vertex}: {probability:.8f}")


def run_examples() -> None:
    line_steps = 8
    quantum_distribution = one_dimensional_discrete_quantum_walk(line_steps)

    print_distribution(
        f"Discrete quantum walk on a line after {line_steps} steps",
        quantum_distribution,
    )

    cycle = Graph(
        (
            (0, 1, 0, 1),
            (1, 0, 1, 0),
            (0, 1, 0, 1),
            (1, 0, 1, 0),
        )
    )

    classical = classical_random_walk(cycle, start=0, steps=6)
    continuous = continuous_time_quantum_walk(cycle, start=0, time=1.5)

    print_distribution("Classical walk on a four-cycle", classical)
    print_distribution("Continuous-time quantum walk on a four-cycle", continuous)

    target_probability = search_amplitude(
        cycle,
        start=0,
        target=2,
        time=1.5,
    )
    print(f"\nProbability of reaching vertex 2 at t=1.5: {target_probability:.8f}")

    assert abs(sum(quantum_distribution.values()) - 1.0) < 1e-10
    assert abs(sum(classical) - 1.0) < 1e-10
    assert abs(sum(continuous) - 1.0) < 1e-10

    # A disconnected target remains unreachable in the continuous-time model.
    disconnected = Graph(
        (
            (0, 1, 0),
            (1, 0, 0),
            (0, 0, 0),
        )
    )
    unreachable = search_amplitude(disconnected, 0, 2, 2.0)
    assert unreachable < 1e-12

    report = {
        "discrete_walk_steps": line_steps,
        "discrete_position_probabilities": quantum_distribution,
        "cycle_classical_probabilities": classical,
        "cycle_quantum_probabilities": continuous,
        "cycle_target_probability": target_probability,
    }

    print("\nMachine-readable report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run_examples()
