from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import asin, floor, pi, sqrt
from typing import Iterable


class SearchMode(Enum):
    STANDARD = "standard"
    GENERALIZED = "generalized"


class SearchError(Exception):
    """Raised when a quantum-search configuration is invalid."""


@dataclass(frozen=True)
class SearchProblem:
    n_qubits: int
    marked_states: frozenset[int]
    target_probability: float = 0.99

    def __post_init__(self) -> None:
        if not 1 <= self.n_qubits <= 20:
            raise SearchError("n_qubits must be between 1 and 20.")
        dimension = 1 << self.n_qubits
        if not self.marked_states:
            raise SearchError("At least one marked state is required.")
        if any(state < 0 or state >= dimension for state in self.marked_states):
            raise SearchError("A marked state is outside the search space.")
        if not 0.0 < self.target_probability <= 1.0:
            raise SearchError("target_probability must be in (0, 1].")

    @property
    def dimension(self) -> int:
        return 1 << self.n_qubits

    @property
    def marked_count(self) -> int:
        return len(self.marked_states)


@dataclass
class AmplificationState:
    iteration: int
    good_amplitude: float
    bad_amplitude: float
    success_probability: float


@dataclass
class SearchResult:
    problem: SearchProblem
    iterations: int
    measured_state: int
    success_probability: float
    history: list[AmplificationState] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.measured_state in self.problem.marked_states


def validate_marked_states(
    n_qubits: int, marked_states: Iterable[int]
) -> frozenset[int]:
    states = frozenset(marked_states)
    dimension = 1 << n_qubits

    if not states:
        raise SearchError("The oracle must mark at least one state.")
    if any(not isinstance(x, int) or isinstance(x, bool) for x in states):
        raise SearchError("Marked states must be integers.")
    if any(x < 0 or x >= dimension for x in states):
        raise SearchError("Marked state is outside the Hilbert-space dimension.")

    return states


def initial_angle(problem: SearchProblem) -> float:
    """sin(theta)^2 equals the initial probability of measuring a marked state."""
    return asin(sqrt(problem.marked_count / problem.dimension))


def success_probability(problem: SearchProblem, iterations: int) -> float:
    if iterations < 0:
        raise SearchError("Iteration count cannot be negative.")

    theta = initial_angle(problem)
    return sin_squared((2 * iterations + 1) * theta)


def sin_squared(angle: float) -> float:
    value = __import__("math").sin(angle)
    return value * value


def optimal_iterations(problem: SearchProblem) -> int:
    """
    Grover's rotation reaches its maximum near
    (2k+1)theta = pi/2.
    """
    theta = initial_angle(problem)
    estimate = (pi / (4.0 * theta)) - 0.5
    candidates = {
        max(0, floor(estimate)),
        max(0, floor(estimate) + 1),
    }
    return max(candidates, key=lambda k: success_probability(problem, k))


def iterations_for_threshold(problem: SearchProblem) -> int:
    """
    Finds the first iteration reaching the requested threshold.
    This is intentionally a bounded simulation rather than a claim that
    every arbitrary threshold is monotonically reachable.
    """
    for iteration in range(0, 10_000):
        if success_probability(problem, iteration) >= problem.target_probability:
            return iteration
    raise SearchError("Threshold was not reached within the simulation bound.")


def simulate_amplification(problem: SearchProblem, iterations: int) -> list[AmplificationState]:
    theta = initial_angle(problem)
    good_amplitude = sqrt(problem.marked_count / problem.dimension)
    bad_amplitude = sqrt((problem.dimension - problem.marked_count) / problem.dimension)

    history: list[AmplificationState] = []

    for k in range(iterations + 1):
        angle = (2 * k + 1) * theta
        probability = sin_squared(angle)

        # Amplitudes are represented in the two-dimensional good/bad subspace.
        good = __import__("math").sin(angle)
        bad = __import__("math").cos(angle)

        history.append(
            AmplificationState(
                iteration=k,
                good_amplitude=good,
                bad_amplitude=bad,
                success_probability=probability,
            )
        )

    # Keep the variables explicit because they correspond to the initial state
    # decomposition used by the amplitude-amplification derivation.
    _ = good_amplitude, bad_amplitude
    return history


def choose_measurement(problem: SearchProblem, iterations: int) -> int:
    """
    Deterministic representative of measurement for a reproducible software
    simulation. A physical quantum measurement is probabilistic; this function
    selects the first marked state whenever the ideal success probability is
    at least 50%, otherwise the first state in the domain.
    """
    probability = success_probability(problem, iterations)

    if probability >= 0.5:
        return min(problem.marked_states)

    return 0


def run_search(problem: SearchProblem, iterations: int | None = None) -> SearchResult:
    if iterations is None:
        iterations = optimal_iterations(problem)

    if iterations < 0:
        raise SearchError("iterations must be non-negative.")

    history = simulate_amplification(problem, iterations)
    measured = choose_measurement(problem, iterations)

    return SearchResult(
        problem=problem,
        iterations=iterations,
        measured_state=measured,
        success_probability=history[-1].success_probability,
        history=history,
    )


def compare_marked_counts(n_qubits: int, marked_counts: Iterable[int]) -> None:
    dimension = 1 << n_qubits

    print(f"\nGeneralized amplitude amplification, N={dimension}")
    print("M\tInitial P\tOptimal k\tFinal P\tO(sqrt(N/M))")

    for count in marked_counts:
        if not 1 <= count <= dimension:
            continue

        problem = SearchProblem(
            n_qubits=n_qubits,
            marked_states=frozenset(range(count)),
        )
        k = optimal_iterations(problem)
        probability = success_probability(problem, k)
        estimate = sqrt(dimension / count)

        print(
            f"{count}\t"
            f"{count / dimension:.4f}\t"
            f"{k}\t"
            f"{probability:.6f}\t"
            f"{estimate:.3f}"
        )


def print_history(result: SearchResult) -> None:
    print("\nAmplitude rotation")
    print("k\tgood amplitude\tbad amplitude\tsuccess probability")

    for state in result.history:
        print(
            f"{state.iteration}\t"
            f"{state.good_amplitude:+.6f}\t"
            f"{state.bad_amplitude:+.6f}\t"
            f"{state.success_probability:.6f}"
        )


def main() -> None:
    marked = validate_marked_states(
        n_qubits=4,
        marked_states=[3, 7, 12],
    )

    problem = SearchProblem(
        n_qubits=4,
        marked_states=marked,
        target_probability=0.90,
    )

    optimal = optimal_iterations(problem)
    threshold = iterations_for_threshold(problem)

    print("Generalized Quantum Search")
    print("==========================")
    print(f"Search-space size: {problem.dimension}")
    print(f"Marked states: {sorted(problem.marked_states)}")
    print(f"Number of marked states: {problem.marked_count}")
    print(f"Initial success probability: {problem.marked_count / problem.dimension:.6f}")
    print(f"Optimal ideal iterations: {optimal}")
    print(f"First iteration reaching target threshold: {threshold}")

    result = run_search(problem, optimal)
    print_history(result)

    print("\nSelected measurement representative")
    print(f"State: {result.measured_state}")
    print(f"Marked: {result.success}")
    print(f"Ideal success probability: {result.success_probability:.6f}")

    compare_marked_counts(
        n_qubits=8,
        marked_counts=[1, 2, 4, 8, 16, 32, 64],
    )

    # Important edge case: if every state is marked, no amplification is needed.
    all_states = frozenset(range(8))
    trivial = SearchProblem(n_qubits=3, marked_states=all_states)
    assert optimal_iterations(trivial) == 0
    assert success_probability(trivial, 0) == 1.0

    # Generalized-search scaling check.
    one_marked = SearchProblem(n_qubits=10, marked_states=frozenset({777}))
    assert optimal_iterations(one_marked) > 0
    assert success_probability(one_marked, optimal_iterations(one_marked)) > 0.9


if __name__ == "__main__":
    main()
