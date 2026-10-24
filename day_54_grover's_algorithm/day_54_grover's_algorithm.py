#!/usr/bin/env python3
"""Grover's quantum search algorithm using a self-contained state-vector simulator."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence


class QuantumSearchError(ValueError):
    """Raised when a quantum search configuration is invalid."""


@dataclass(frozen=True)
class SearchResult:
    qubits: int
    marked_states: tuple[int, ...]
    iterations: int
    probabilities: tuple[float, ...]
    success_probability: float
    measured_state: int
    oracle_queries: int


class GroverSearch:
    """Simulate Grover search using complex state amplitudes.

    The simulator stores 2**n amplitudes, so memory usage is exponential
    in the number of qubits. It is intended for small educational examples.
    """

    def __init__(self, qubits: int, marked_states: Sequence[int]):
        if not isinstance(qubits, int) or isinstance(qubits, bool):
            raise QuantumSearchError("Qubit count must be an integer.")
        if not 1 <= qubits <= 20:
            raise QuantumSearchError("Use between 1 and 20 qubits.")

        self.qubits = qubits
        self.size = 1 << qubits

        marked = tuple(sorted(set(marked_states)))
        if not marked:
            raise QuantumSearchError("At least one marked state is required.")
        if any(
            not isinstance(state, int)
            or isinstance(state, bool)
            or state < 0
            or state >= self.size
            for state in marked
        ):
            raise QuantumSearchError(
                f"Marked states must be integers in [0, {self.size - 1}]."
            )

        self.marked_states = marked
        self.marked_set = frozenset(marked)

    @property
    def optimal_iterations(self) -> int:
        """Return the first near-optimal iteration count for known M."""
        n = self.size
        m = len(self.marked_states)

        if m == n:
            return 0

        theta = math.asin(math.sqrt(m / n))
        estimate = math.floor(math.pi / (4 * theta) - 0.5)
        return max(0, estimate)

    def run(self, iterations: int | None = None) -> SearchResult:
        if iterations is None:
            iterations = self.optimal_iterations
        if (
            not isinstance(iterations, int)
            or isinstance(iterations, bool)
            or iterations < 0
        ):
            raise QuantumSearchError("Iterations must be a nonnegative integer.")

        n = self.size
        m = len(self.marked_states)
        amplitudes = [1.0 / math.sqrt(n)] * n

        for _ in range(iterations):
            # Phase oracle: marked basis states acquire a factor of -1.
            for state in self.marked_states:
                amplitudes[state] = -amplitudes[state]

            # Diffusion operator: inversion about the mean amplitude.
            mean = sum(amplitudes) / n
            amplitudes = [2.0 * mean - amplitude for amplitude in amplitudes]

        probabilities = tuple(
            amplitude * amplitude for amplitude in amplitudes
        )
        success_probability = sum(
            probabilities[state] for state in self.marked_states
        )

        # Deterministic maximum-probability measurement for reproducibility.
        measured_state = max(
            range(n), key=lambda state: probabilities[state]
        )

        norm = sum(probabilities)
        if not math.isclose(norm, 1.0, rel_tol=1e-10, abs_tol=1e-10):
            raise ArithmeticError(f"State normalization failed: {norm}")

        return SearchResult(
            qubits=self.qubits,
            marked_states=self.marked_states,
            iterations=iterations,
            probabilities=probabilities,
            success_probability=success_probability,
            measured_state=measured_state,
            oracle_queries=iterations,
        )


def classical_search(
    domain_size: int, predicate: Callable[[int], bool]
) -> tuple[int | None, int]:
    """Search sequentially and return the result and predicate evaluations."""
    if domain_size < 1:
        raise ValueError("Domain size must be positive.")

    evaluations = 0
    for candidate in range(domain_size):
        evaluations += 1
        if predicate(candidate):
            return candidate, evaluations

    return None, evaluations


def format_binary(state: int, qubits: int) -> str:
    return format(state, f"0{qubits}b")


def demonstrate_search() -> None:
    qubits = 4
    marked = (5,)
    search = GroverSearch(qubits, marked)
    result = search.run()

    print("Grover quantum search")
    print(f"Qubits: {result.qubits}")
    print(f"Search space: {1 << qubits} states")
    print(f"Marked states: {result.marked_states}")
    print(f"Grover iterations: {result.iterations}")
    print(f"Success probability: {result.success_probability:.6f}")
    print(
        "Most probable state:",
        format_binary(result.measured_state, qubits),
        f"({result.measured_state})",
    )
    print("\nState probabilities:")
    for state, probability in enumerate(result.probabilities):
        print(
            f"  {format_binary(state, qubits)}: {probability:.6f}"
        )

    found, evaluations = classical_search(
        1 << qubits, lambda candidate: candidate in marked
    )
    print(f"\nClassical first match: {found}")
    print(f"Classical predicate evaluations: {evaluations}")

    # Validate normalization, optimal behavior, and edge cases.
    assert math.isclose(sum(result.probabilities), 1.0, abs_tol=1e-10)
    assert result.success_probability > 0.9
    assert result.measured_state == 5

    all_marked = GroverSearch(2, (0, 1, 2, 3)).run()
    assert all_marked.iterations == 0
    assert math.isclose(all_marked.success_probability, 1.0)

    try:
        GroverSearch(2, (4,))
    except QuantumSearchError:
        pass
    else:
        raise AssertionError("Out-of-range states must be rejected.")

    print("\nValidation checks passed.")


if __name__ == "__main__":
    demonstrate_search()
