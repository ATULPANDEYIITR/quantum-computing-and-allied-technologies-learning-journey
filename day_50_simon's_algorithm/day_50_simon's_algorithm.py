from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import gcd
from typing import Iterable


@dataclass(frozen=True)
class SimonInstance:
    n: int
    secret: str

    def __post_init__(self) -> None:
        if self.n <= 0:
            raise ValueError("n must be positive")
        if len(self.secret) != self.n or any(bit not in "01" for bit in self.secret):
            raise ValueError("secret must be an n-bit binary string")
        if self.secret == "0" * self.n:
            raise ValueError("Simon instances require a non-zero hidden period")


class SimonOracle:
    """
    A classical representation of Simon's oracle.

    The oracle satisfies f(x) = f(x xor s), where s is the hidden
    non-zero period. A canonical collision-safe construction is used:
    the function value is the canonical representative of {x, x xor s}.
    """

    def __init__(self, secret: str) -> None:
        if not secret or any(bit not in "01" for bit in secret):
            raise ValueError("secret must be a non-empty binary string")
        if set(secret) == {"0"}:
            raise ValueError("secret cannot be the zero vector")
        self.secret = secret
        self.n = len(secret)
        self.secret_int = int(secret, 2)

    def evaluate(self, x: int) -> int:
        if x < 0 or x >= (1 << self.n):
            raise ValueError("x is outside the n-bit domain")
        partner = x ^ self.secret_int
        return min(x, partner)

    def verify_period(self) -> bool:
        return all(
            self.evaluate(x) == self.evaluate(x ^ self.secret_int)
            for x in range(1 << self.n)
        )

    def verify_two_to_one(self) -> bool:
        outputs: dict[int, list[int]] = {}
        for x in range(1 << self.n):
            outputs.setdefault(self.evaluate(x), []).append(x)
        return all(len(inputs) == 2 for inputs in outputs.values())


def bits(value: int, n: int) -> str:
    return format(value, f"0{n}b")


def dot_mod_2(left: str, right: str) -> int:
    if len(left) != len(right):
        raise ValueError("vectors must have equal length")
    return sum(a == "1" and b == "1" for a, b in zip(left, right)) % 2


def hadamard_sample(secret: str, rng) -> str:
    """
    Simulates the measurement distribution after the Simon circuit.

    The measured y must satisfy y dot s = 0 mod 2. The full quantum
    interference is represented by sampling uniformly from this
    (n-1)-dimensional subspace.
    """
    n = len(secret)
    candidates = [
        bits(value, n)
        for value in range(1 << n)
        if dot_mod_2(bits(value, n), secret) == 0
    ]
    return rng.choice(candidates)


def gaussian_elimination_mod2(rows: list[str], n: int) -> list[int]:
    matrix = [
        [int(bit) for bit in row]
        for row in rows
        if len(row) == n and any(bit == "1" for bit in row)
    ]

    rank = 0
    pivots: list[int] = []

    for column in range(n):
        pivot = next(
            (r for r in range(rank, len(matrix)) if matrix[r][column] == 1),
            None,
        )
        if pivot is None:
            continue

        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]

        for r in range(len(matrix)):
            if r != rank and matrix[r][column]:
                matrix[r] = [
                    a ^ b for a, b in zip(matrix[r], matrix[rank])
                ]

        pivots.append(column)
        rank += 1

        if rank == len(matrix):
            break

    return pivots


def nullspace_mod2(rows: list[str], n: int) -> list[str]:
    matrix = [
        [int(bit) for bit in row]
        for row in rows
        if len(row) == n
    ]

    pivot_columns: list[int] = []
    rank = 0

    for column in range(n):
        pivot = next(
            (r for r in range(rank, len(matrix)) if matrix[r][column]),
            None,
        )
        if pivot is None:
            continue

        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]

        for r in range(len(matrix)):
            if r != rank and matrix[r][column]:
                matrix[r] = [
                    a ^ b for a, b in zip(matrix[r], matrix[rank])
                ]

        pivot_columns.append(column)
        rank += 1

    free_columns = [
        column for column in range(n)
        if column not in pivot_columns
    ]

    basis: list[str] = []

    for free in free_columns:
        vector = [0] * n
        vector[free] = 1

        for row, pivot_column in enumerate(pivot_columns):
            vector[pivot_column] = matrix[row][free]

        basis.append("".join(map(str, vector)))

    return basis


def recover_secret(observations: Iterable[str], n: int) -> str:
    rows = list(observations)
    if any(len(row) != n or any(bit not in "01" for bit in row) for row in rows):
        raise ValueError("observations must contain n-bit binary strings")

    basis = nullspace_mod2(rows, n)

    if len(basis) != 1:
        raise ValueError(
            f"observations do not uniquely determine the secret; "
            f"nullspace dimension is {len(basis)}"
        )

    return basis[0]


def required_independent_observations(n: int) -> int:
    """
    n-1 independent equations are sufficient for a unique non-zero
    hidden period in an n-bit Simon problem.
    """
    if n <= 1:
        return 0
    return n - 1


def run_simulation(secret: str, seed: int = 7) -> None:
    import random

    instance = SimonInstance(len(secret), secret)
    oracle = SimonOracle(instance.secret)

    assert oracle.verify_period()
    assert oracle.verify_two_to_one()

    rng = random.Random(seed)
    observations: list[str] = []

    target_rank = required_independent_observations(instance.n)

    while len(observations) < max(target_rank, 1):
        measurement = hadamard_sample(secret, rng)
        if measurement not in observations:
            observations.append(measurement)

    recovered = recover_secret(observations, instance.n)

    print("Simon algorithm simulation")
    print(f"Hidden period:       {secret}")
    print(f"Oracle period valid: {oracle.verify_period()}")
    print(f"Oracle two-to-one:   {oracle.verify_two_to_one()}")
    print(f"Measurements:        {observations}")
    print(f"Independent rows:    {len(gaussian_elimination_mod2(observations, instance.n))}")
    print(f"Recovered period:    {recovered}")
    print(f"Recovery successful: {recovered == secret}")


def demonstrate_edge_case() -> None:
    """
    For n=1, the only non-zero secret is 1 and the equation y*s=0
    permits only y=0. No measured equation is needed to identify it
    once the Simon promise is known.
    """
    secret = "1"
    oracle = SimonOracle(secret)

    assert oracle.evaluate(0) == oracle.evaluate(1)
    assert recover_secret([], 1) == "1"


if __name__ == "__main__":
    demonstrate_edge_case()
    run_simulation("1011")

    # A larger instance demonstrates that the same linear-algebra
    # machinery scales without representing a 2^n quantum state.
    run_simulation("110101")
