#!/usr/bin/env python3
"""Grover's quantum search algorithm with validation and optimization."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SearchResult:
    marked_states: tuple[int, ...]
    measured_state: int
    iterations: int
    success_probability: float
    qubits: int
    state_count: int


class GroverSearch:
    """State-vector simulator for Grover search using a real amplitude vector."""

    def __init__(self, qubits: int, seed: int = 7) -> None:
        if not isinstance(qubits, int) or isinstance(qubits, bool):
            raise TypeError("Qubit count must be an integer.")
        if not 1 <= qubits <= 20:
            raise ValueError("Qubit count must be between 1 and 20.")

        self.qubits = qubits
        self.size = 1 << qubits
        self.rng = random.Random(seed)
        self.amplitudes = [1.0 / math.sqrt(self.size)] * self.size

    def oracle(self, marked: set[int]) -> None:
        """Apply the phase oracle: |x> becomes -|x> when x is marked."""
        for state in marked:
            self.amplitudes[state] = -self.amplitudes[state]

    def diffusion(self) -> None:
        """Reflect every amplitude about the vector's mean amplitude."""
        mean = sum(self.amplitudes) / self.size
        self.amplitudes = [
            2.0 * mean - amplitude for amplitude in self.amplitudes
        ]

    @staticmethod
    def optimal_iterations(size: int, marked_count: int) -> int:
        """Choose a near-optimal iteration count for a known number of matches."""
        if not 0 <= marked_count <= size:
            raise ValueError("Marked-state count is outside the search space.")
        if marked_count == 0 or marked_count == size:
            return 0

        theta = math.asin(math.sqrt(marked_count / size))
        return max(0, round(math.pi / (4.0 * theta) - 0.5))

    def probability(self, marked: set[int]) -> float:
        return sum(self.amplitudes[state] ** 2 for state in marked)

    def measure(self) -> int:
        """Sample a computational-basis outcome from squared amplitudes."""
        probabilities = [amplitude * amplitude for amplitude in self.amplitudes]
        total = sum(probabilities)
        if not math.isclose(total, 1.0, rel_tol=1e-8, abs_tol=1e-8):
            raise ArithmeticError(f"State normalization failed: {total}")

        threshold = self.rng.random() * total
        cumulative = 0.0
        for state, probability in enumerate(probabilities):
            cumulative += probability
            if threshold <= cumulative:
                return state
        return self.size - 1

    def search(
        self,
        marked_states: set[int],
        iterations: int | None = None,
    ) -> SearchResult:
        if not marked_states:
            raise ValueError(
                "At least one marked state is required for this search."
            )
        if any(
            not isinstance(state, int)
            or isinstance(state, bool)
            or not 0 <= state < self.size
            for state in marked_states
        ):
            raise ValueError("Every marked state must be inside the search space.")

        if iterations is None:
            iterations = self.optimal_iterations(
                self.size, len(marked_states)
            )
        if not isinstance(iterations, int) or isinstance(iterations, bool):
            raise TypeError("Iteration count must be an integer.")
        if not 0 <= iterations <= 100_000:
            raise ValueError("Iteration count must be between 0 and 100000.")

        # Reinitialize so repeated calls on one instance are independent.
        self.amplitudes = [1.0 / math.sqrt(self.size)] * self.size

        for _ in range(iterations):
            self.oracle(marked_states)
            self.diffusion()

        return SearchResult(
            marked_states=tuple(sorted(marked_states)),
            measured_state=self.measure(),
            iterations=iterations,
            success_probability=self.probability(marked_states),
            qubits=self.qubits,
            state_count=self.size,
        )


def classical_search(items: list[int], target: int) -> int | None:
    """Classical baseline with O(N) worst-case query complexity."""
    for index, value in enumerate(items):
        if value == target:
            return index
    return None


def main() -> None:
    qubits = 4
    target = 11
    marked = {target}

    search = GroverSearch(qubits, seed=42)
    result = search.search(marked)

    print("Grover quantum search simulation")
    print(f"Qubits: {result.qubits}")
    print(f"Search-space size: {result.state_count}")
    print(f"Marked states: {result.marked_states}")
    print(f"Grover iterations: {result.iterations}")
    print(f"Success probability before measurement: "
          f"{result.success_probability:.6f}")
    print(f"Measured state: {result.measured_state}")
    print(f"Measurement found a marked state: "
          f"{result.measured_state in marked}")

    # A single measurement is probabilistic, not guaranteed to succeed.
    trials = 1000
    hits = 0
    for seed in range(trials):
        trial = GroverSearch(qubits, seed=seed)
        if trial.search(marked).measured_state in marked:
            hits += 1
    print(f"Empirical success rate over {trials} trials: "
          f"{hits / trials:.3%}")

    # Validate amplitude amplification for one marked state in 16 states.
    assert result.iterations == 3
    assert result.success_probability > 0.96
    assert abs(sum(a * a for a in search.amplitudes) - 1.0) < 1e-8

    data = list(range(1 << qubits))
    assert classical_search(data, target) == target
    assert classical_search(data, 99) is None

    print("Validation checks passed.")


if __name__ == "__main__":
    main()
