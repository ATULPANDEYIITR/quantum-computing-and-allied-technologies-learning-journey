#!/usr/bin/env python3
"""
Shor's algorithm: integer factorization concepts.

This self-contained implementation provides:
- Classical preprocessing and trial division
- gcd and modular arithmetic
- Continued-fraction extraction of candidate periods
- Classical simulation of Shor's order-finding step
- A small quantum-state simulation using QFT for educational cases
- Period validation
- Factor extraction from a valid even period
- Deterministic demonstrations for composite integers such as 15 and 21

The state-vector simulator is intentionally limited to small examples.
It models the mathematical structure of the quantum period-finding
subroutine rather than attempting to factor cryptographically large integers.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Iterable


class FactorStatus(Enum):
    FACTORED = "factored"
    PRIME = "prime"
    RETRY = "retry"
    FAILURE = "failure"


@dataclass(frozen=True)
class FactorizationResult:
    n: int
    factors: tuple[int, ...]
    status: FactorStatus
    base: int | None = None
    period: int | None = None
    message: str = ""


def gcd(a: int, b: int) -> int:
    """Euclidean algorithm."""
    while b:
        a, b = b, a % b
    return abs(a)


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Return (g, x, y) such that ax + by = g."""
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1

    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t

    return old_r, old_s, old_t


def mod_inverse(a: int, modulus: int) -> int:
    g, x, _ = extended_gcd(a, modulus)
    if g != 1:
        raise ValueError(f"{a} has no inverse modulo {modulus}")
    return x % modulus


def modular_power(base: int, exponent: int, modulus: int) -> int:
    """Fast modular exponentiation in O(log exponent)."""
    if modulus <= 0:
        raise ValueError("Modulus must be positive.")
    if exponent < 0:
        base = mod_inverse(base, modulus)
        exponent = -exponent

    result = 1
    base %= modulus

    while exponent:
        if exponent & 1:
            result = (result * base) % modulus
        base = (base * base) % modulus
        exponent >>= 1

    return result


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2

    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2

    return True


def trial_factorization(n: int) -> tuple[int, ...]:
    """Reference implementation used for validation and small inputs."""
    if n < 2:
        raise ValueError("Factorization requires n >= 2.")

    factors: list[int] = []
    value = n

    while value % 2 == 0:
        factors.append(2)
        value //= 2

    divisor = 3
    while divisor * divisor <= value:
        while value % divisor == 0:
            factors.append(divisor)
            value //= divisor
        divisor += 2

    if value > 1:
        factors.append(value)

    return tuple(factors)


def multiplicative_order(a: int, n: int, limit: int | None = None) -> int | None:
    """
    Find the smallest r > 0 with a^r = 1 (mod n).

    This classical routine represents the period that Shor's quantum
    period-finding circuit is designed to recover.
    """
    if n <= 1 or gcd(a, n) != 1:
        return None

    if limit is None:
        limit = n

    value = 1
    for r in range(1, limit + 1):
        value = (value * a) % n
        if value == 1:
            return r

    return None


def continued_fraction_convergents(
    numerator: int, denominator: int
) -> Iterable[tuple[int, int]]:
    """Generate convergents of numerator / denominator."""
    if denominator <= 0:
        raise ValueError("Denominator must be positive.")

    quotient: list[int] = []
    a, b = numerator, denominator

    while b:
        q, remainder = divmod(a, b)
        quotient.append(q)
        a, b = b, remainder

    p_minus_2, p_minus_1 = 0, 1
    q_minus_2, q_minus_1 = 1, 0

    for q in quotient:
        p = q * p_minus_1 + p_minus_2
        denominator_value = q * q_minus_1 + q_minus_2
        yield p, denominator_value
        p_minus_2, p_minus_1 = p_minus_1, p
        q_minus_2, q_minus_1 = q_minus_1, denominator_value


def recover_period_from_measurement(
    measured: int, q: int, a: int, n: int
) -> int | None:
    """
    Convert a simulated phase measurement into a candidate period.

    The measured phase is approximately s/r. Continued fractions provide
    rational approximations whose denominators are candidates for r.
    """
    if q <= 0 or measured < 0 or measured >= q:
        raise ValueError("Measurement must satisfy 0 <= measured < q.")

    for numerator, denominator in continued_fraction_convergents(measured, q):
        if denominator <= 0 or denominator > n:
            continue

        if modular_power(a, denominator, n) == 1:
            return denominator

        # A convergent denominator can be a divisor of the true period.
        # Test small multiples before abandoning the candidate.
        for multiple in range(2, n + 1):
            candidate = denominator * multiple
            if candidate > n * 2:
                break
            if modular_power(a, candidate, n) == 1:
                return candidate

    return None


def qft(state: list[complex], inverse: bool = False) -> list[complex]:
    """Direct O(Q^2) quantum Fourier transform for a small state vector."""
    size = len(state)
    if size == 0 or size & (size - 1):
        raise ValueError("QFT size must be a power of two.")

    sign = 1 if inverse else -1
    scale = 1 / math.sqrt(size)
    transformed = [0j] * size

    for k in range(size):
        total = 0j
        for j, amplitude in enumerate(state):
            angle = sign * 2 * math.pi * j * k / size
            total += amplitude * cmath.exp(1j * angle)
        transformed[k] = total * scale

    return transformed


def sample_probability_distribution(
    probabilities: list[float], rng: random.Random
) -> int:
    total = sum(probabilities)
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError("Probability distribution must sum to one.")

    threshold = rng.random()
    cumulative = 0.0

    for index, probability in enumerate(probabilities):
        cumulative += probability
        if threshold <= cumulative:
            return index

    return len(probabilities) - 1


def simulate_period_measurement(
    n: int, a: int, rng: random.Random | None = None
) -> tuple[int, int, list[float]]:
    """
    Small state-vector model of phase estimation.

    It constructs the periodic sequence f(x)=a^x mod n over a power-of-two
    register, applies a QFT, and samples the resulting frequency register.

    This is a pedagogical state simulation, not a scalable quantum computer.
    """
    if rng is None:
        rng = random.Random()

    if n < 2 or gcd(a, n) != 1:
        raise ValueError("a must be coprime to n.")

    order = multiplicative_order(a, n)
    if order is None:
        raise RuntimeError("Could not determine the classical period.")

    register_size = 1
    while register_size < n * n:
        register_size <<= 1

    if register_size > 256:
        raise ValueError(
            "State-vector demonstration is limited to small n; "
            "use a smaller composite number."
        )

    # The first register is assigned amplitudes according to the periodic
    # function. Measuring the second register leaves a periodic first register.
    target_value = modular_power(a, rng.randrange(order), n)
    positions = [
        x
        for x in range(register_size)
        if modular_power(a, x, n) == target_value
    ]

    state = [0j] * register_size
    amplitude = 1 / math.sqrt(len(positions))

    for x in positions:
        state[x] = complex(amplitude, 0)

    transformed = qft(state)

    probabilities = [abs(amplitude) ** 2 for amplitude in transformed]
    total = sum(probabilities)

    # Floating-point normalization protects sampling from tiny accumulated error.
    probabilities = [p / total for p in probabilities]
    measured = sample_probability_distribution(probabilities, rng)

    return measured, register_size, probabilities


def derive_factors(n: int, a: int, r: int) -> tuple[int, int] | None:
    """Extract non-trivial factors from a valid even order."""
    if r <= 0 or r % 2:
        return None

    half_power = modular_power(a, r // 2, n)
    if half_power == n - 1:
        return None

    left = gcd(half_power - 1, n)
    right = gcd(half_power + 1, n)

    if 1 < left < n and 1 < right < n and left * right == n:
        return tuple(sorted((left, right)))

    return None


def shor_factor(
    n: int,
    *,
    attempts: int = 32,
    seed: int = 7,
    use_quantum_simulation: bool = False,
) -> FactorizationResult:
    """
    Factor a small composite integer using the structure of Shor's algorithm.

    The order-finding phase can be:
    - classical, using multiplicative_order(), or
    - a small QFT state-vector simulation.

    Real quantum hardware replaces this simulation with a quantum circuit.
    """
    if n < 2:
        raise ValueError("n must be at least 2.")

    if is_prime(n):
        return FactorizationResult(
            n=n,
            factors=(n,),
            status=FactorStatus.PRIME,
            message="Input is prime.",
        )

    if n % 2 == 0:
        return FactorizationResult(
            n=n,
            factors=(2, n // 2),
            status=FactorStatus.FACTORED,
            message="Even-number preprocessing found a factor.",
        )

    rng = random.Random(seed)

    for _ in range(attempts):
        a = rng.randrange(2, n)

        common_factor = gcd(a, n)
        if 1 < common_factor < n:
            other = n // common_factor
            return FactorizationResult(
                n=n,
                factors=tuple(sorted((common_factor, other))),
                status=FactorStatus.FACTORED,
                base=a,
                message="Random base immediately exposed a non-trivial gcd.",
            )

        if common_factor != 1:
            continue

        if use_quantum_simulation:
            try:
                measured, q, _ = simulate_period_measurement(n, a, rng)
                period = recover_period_from_measurement(measured, q, a, n)
            except (ValueError, RuntimeError):
                period = None
        else:
            period = multiplicative_order(a, n)

        if period is None or period % 2:
            continue

        if modular_power(a, period, n) != 1:
            continue

        factors = derive_factors(n, a, period)
        if factors:
            return FactorizationResult(
                n=n,
                factors=factors,
                status=FactorStatus.FACTORED,
                base=a,
                period=period,
                message="Non-trivial factors recovered from the period.",
            )

    return FactorizationResult(
        n=n,
        factors=(),
        status=FactorStatus.RETRY,
        message="No usable period was obtained within the attempt limit.",
    )


def validate_result(result: FactorizationResult) -> None:
    if result.status == FactorStatus.FACTORED:
        if len(result.factors) != 2:
            raise AssertionError("Expected two factors in this demonstration.")

        if result.factors[0] * result.factors[1] != result.n:
            raise AssertionError("Recovered factors do not multiply to n.")

        if not all(1 < factor < result.n for factor in result.factors):
            raise AssertionError("Factors must be non-trivial.")


def demonstrate_order_finding(n: int, a: int) -> None:
    if gcd(a, n) != 1:
        print(f"a={a}, n={n}: gcd(a,n) != 1, so order-finding is skipped.")
        return

    order = multiplicative_order(a, n)
    if order is None:
        print(f"a={a}, n={n}: no order found.")
        return

    sequence = [modular_power(a, exponent, n) for exponent in range(order)]
    print(f"a={a}, n={n}")
    print(f"  periodic sequence: {sequence}")
    print(f"  order r = {order}")
    print(f"  a^r mod n = {modular_power(a, order, n)}")

    if order % 2 == 0:
        candidate = derive_factors(n, a, order)
        print(f"  gcd-derived factors: {candidate}")
    else:
        print("  odd order: this attempt cannot directly produce Shor factors.")


def main() -> None:
    print("Shor's Algorithm: Small-Integer Demonstration")
    print("=" * 48)

    for n in (15, 21, 35):
        result = shor_factor(n, attempts=40, seed=11)
        validate_result(result)

        print(
            f"n={result.n}: status={result.status.value}, "
            f"factors={result.factors or 'none'}, "
            f"base={result.base}, period={result.period}"
        )
        print(f"  {result.message}")

    print("\nOrder-finding examples")
    print("-" * 48)
    demonstrate_order_finding(15, 2)
    demonstrate_order_finding(21, 2)

    print("\nClassical-versus-QFT simulation")
    print("-" * 48)
    classical = shor_factor(15, attempts=20, seed=3)
    print(
        f"classical order path: factors={classical.factors}, "
        f"base={classical.base}, period={classical.period}"
    )

    # The QFT simulator is deliberately limited to small educational cases.
    quantum_simulated = shor_factor(
        15,
        attempts=20,
        seed=3,
        use_quantum_simulation=True,
    )
    print(
        f"state-vector QFT path: factors={quantum_simulated.factors}, "
        f"base={quantum_simulated.base}, period={quantum_simulated.period}"
    )

    print("\nReference factorization")
    print("-" * 48)
    for n in (15, 21, 35, 77):
        print(f"{n} = {' × '.join(map(str, trial_factorization(n)))}")

    # Basic correctness checks for the mathematical building blocks.
    assert gcd(84, 30) == 6
    assert modular_power(7, 4, 15) == 1
    assert multiplicative_order(2, 15) == 4
    assert derive_factors(15, 2, 4) == (3, 5)
    assert trial_factorization(84) == (2, 2, 3, 7)

    print("\nValidation checks passed.")


if __name__ == "__main__":
    main()
