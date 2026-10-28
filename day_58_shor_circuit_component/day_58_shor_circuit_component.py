from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd, log2
from typing import Iterable, Sequence
import cmath
import math
import random


class QuantumCircuitError(ValueError):
    """Raised when a circuit or algorithm input is invalid."""


def validate_power_of_two(value: int, name: str = "value") -> None:
    if value <= 0 or value & (value - 1):
        raise QuantumCircuitError(f"{name} must be a positive power of two")


def qft_state(amplitudes: Sequence[complex]) -> list[complex]:
    """
    Apply the normalized Quantum Fourier Transform to a state vector.

    This direct implementation is O(N^2), which is useful for studying the
    transformation itself. Production quantum simulators use more efficient
    circuit decompositions or specialized FFT-like methods.
    """
    n = len(amplitudes)
    validate_power_of_two(n, "state dimension")

    norm = math.sqrt(n)
    result: list[complex] = []
    for k in range(n):
        total = 0j
        for x, amplitude in enumerate(amplitudes):
            angle = 2.0 * math.pi * k * x / n
            total += amplitude * cmath.exp(1j * angle)
        result.append(total / norm)
    return result


def inverse_qft_state(amplitudes: Sequence[complex]) -> list[complex]:
    n = len(amplitudes)
    validate_power_of_two(n, "state dimension")

    norm = math.sqrt(n)
    result: list[complex] = []
    for x in range(n):
        total = 0j
        for k, amplitude in enumerate(amplitudes):
            angle = -2.0 * math.pi * k * x / n
            total += amplitude * cmath.exp(1j * angle)
        result.append(total / norm)
    return result


def probability_distribution(amplitudes: Sequence[complex]) -> list[float]:
    probabilities = [abs(value) ** 2 for value in amplitudes]
    total = sum(probabilities)
    if total <= 0:
        raise QuantumCircuitError("state has zero norm")
    return [p / total for p in probabilities]


@dataclass(frozen=True)
class Gate:
    name: str
    qubits: tuple[int, ...]
    parameter: float | None = None


@dataclass
class Circuit:
    qubits: int
    gates: list[Gate] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.qubits <= 0:
            raise QuantumCircuitError("a circuit needs at least one qubit")

    def add(self, name: str, *qubits: int, parameter: float | None = None) -> None:
        if not qubits:
            raise QuantumCircuitError("a gate needs at least one qubit")
        if any(q < 0 or q >= self.qubits for q in qubits):
            raise QuantumCircuitError("gate references an invalid qubit")
        self.gates.append(Gate(name, tuple(qubits), parameter))

    def qft(self, qubits: Iterable[int]) -> None:
        selected = list(qubits)
        if not selected:
            raise QuantumCircuitError("QFT requires at least one qubit")
        if len(set(selected)) != len(selected):
            raise QuantumCircuitError("QFT qubits must be unique")

        # The decomposition is expressed in the standard H + controlled-phase
        # form. The final swaps reverse the computational-bit ordering.
        for target_index, target in enumerate(selected):
            self.add("H", target)
            for control_index in range(target_index + 1, len(selected)):
                control = selected[control_index]
                angle = math.pi / (2 ** (control_index - target_index))
                self.add("CR", control, target, parameter=angle)

        for left, right in zip(selected, reversed(selected)):
            if left < right:
                self.add("SWAP", left, right)

    def inverse_qft(self, qubits: Iterable[int]) -> None:
        selected = list(qubits)
        if not selected:
            raise QuantumCircuitError("inverse QFT requires at least one qubit")

        # Inverse QFT is the adjoint: reverse gate order and negate rotation
        # angles. H and SWAP are self-adjoint.
        temporary = Circuit(self.qubits)
        temporary.qft(selected)
        for gate in reversed(temporary.gates):
            if gate.name == "CR":
                self.gates.append(
                    Gate("CR†", gate.qubits, -float(gate.parameter))
                )
            else:
                self.gates.append(gate)

    def describe(self) -> str:
        lines = [f"Circuit: {self.qubits} qubits, {len(self.gates)} gates"]
        for index, gate in enumerate(self.gates, start=1):
            if gate.parameter is None:
                lines.append(f"{index:03d}: {gate.name} {gate.qubits}")
            else:
                lines.append(
                    f"{index:03d}: {gate.name} {gate.qubits}, "
                    f"angle={gate.parameter:.8f}"
                )
        return "\n".join(lines)


def controlled_modular_multiplication(
    value: int,
    multiplier: int,
    modulus: int,
) -> int:
    """Classical permutation representing modular multiplication."""
    if modulus <= 1:
        raise QuantumCircuitError("modulus must be greater than one")
    if gcd(multiplier, modulus) != 1:
        raise QuantumCircuitError("multiplier must be invertible modulo modulus")
    if not 0 <= value < modulus:
        raise QuantumCircuitError("value must be inside the modular domain")
    return (value * multiplier) % modulus


def modular_order(a: int, n: int, max_period: int | None = None) -> int | None:
    """
    Find the multiplicative order r of a modulo n.

    This is the classical period-finding core used to validate the quantum
    phase-estimation result. It is deliberately separate from QFT.
    """
    if n <= 1 or not 1 < a < n or gcd(a, n) != 1:
        raise QuantumCircuitError("require 1 < a < n and gcd(a, n) = 1")

    limit = max_period or n
    value = 1
    for r in range(1, limit + 1):
        value = (value * a) % n
        if value == 1:
            return r
    return None


def phase_estimation_peaks(
    period: int,
    counting_qubits: int,
) -> list[tuple[int, float, float]]:
    """
    Idealized phase-estimation measurement model.

    For a periodic state with period r, phases near s/r occur. Each phase is
    represented by a counting-register integer y approximately Q*s/r.
    """
    if period <= 0:
        raise QuantumCircuitError("period must be positive")
    if counting_qubits <= 0:
        raise QuantumCircuitError("counting_qubits must be positive")

    q = 1 << counting_qubits
    peaks = []
    for s in range(period):
        phase = s / period
        y = round(q * phase) % q
        peaks.append((y, y / q, phase))
    return peaks


def continued_fraction_candidates(
    measurement: int,
    denominator: int,
    max_denominator: int,
) -> list[int]:
    """
    Extract denominator candidates from the rational approximation
    measurement/denominator.
    """
    if denominator <= 0:
        raise QuantumCircuitError("denominator must be positive")

    fraction = Fraction(measurement, denominator).limit_denominator(
        max_denominator
    )
    candidates = {fraction.denominator}

    # Neighboring denominators are useful because finite precision may make
    # the nearest convergent differ from the true period.
    for delta in range(1, 4):
        if fraction.denominator - delta > 0:
            candidates.add(fraction.denominator - delta)
        candidates.add(fraction.denominator + delta)

    return sorted(
        candidate
        for candidate in candidates
        if candidate > 0 and candidate <= max_denominator
    )


def shor_period_pipeline(
    a: int,
    n: int,
    counting_qubits: int = 8,
) -> dict:
    if n % 2 == 0:
        return {"status": "trivial_factor", "factor": 2}

    g = gcd(a, n)
    if g > 1:
        return {"status": "trivial_factor", "factor": g}

    r = modular_order(a, n)
    if r is None:
        return {"status": "period_not_found"}

    peaks = phase_estimation_peaks(r, counting_qubits)
    useful_peak = next((item for item in peaks if item[0] > 0), peaks[0])
    measurement, measured_phase, ideal_phase = useful_peak

    candidates = continued_fraction_candidates(
        measurement,
        1 << counting_qubits,
        n,
    )

    factors: set[int] = set()
    for candidate in candidates:
        if candidate % 2 != 0:
            continue
        x = pow(a, candidate // 2, n)
        if x in (1, n - 1):
            continue
        left = gcd(x - 1, n)
        right = gcd(x + 1, n)
        if 1 < left < n:
            factors.add(left)
        if 1 < right < n:
            factors.add(right)

    return {
        "status": "complete",
        "a": a,
        "n": n,
        "period": r,
        "counting_qubits": counting_qubits,
        "measurement": measurement,
        "measured_phase": measured_phase,
        "ideal_phase": ideal_phase,
        "candidate_periods": candidates,
        "factors": sorted(factors),
    }


def demo_qft() -> None:
    print("=== QFT demonstration ===")
    amplitudes = [1 / math.sqrt(4), 1 / math.sqrt(4), 0j, 0j]
    transformed = qft_state(amplitudes)

    for index, value in enumerate(transformed):
        print(
            f"|{index:02b}> amplitude="
            f"{value.real:+.6f}{value.imag:+.6f}i "
            f"probability={abs(value) ** 2:.6f}"
        )

    restored = inverse_qft_state(transformed)
    error = max(abs(a - b) for a, b in zip(amplitudes, restored))
    print(f"Inverse-QFT reconstruction error: {error:.3e}")

    circuit = Circuit(4)
    circuit.qft(range(4))
    print(circuit.describe())


def demo_shor() -> None:
    print("\n=== Shor period-finding demonstration ===")
    result = shor_period_pipeline(2, 15, counting_qubits=8)

    for key, value in result.items():
        print(f"{key}: {value}")

    if result["status"] != "complete":
        raise RuntimeError("period-finding demonstration did not complete")

    assert result["period"] == 4
    assert set(result["factors"]) == {3, 5}


def demo_edge_cases() -> None:
    print("\n=== Validation and edge cases ===")

    try:
        qft_state([1, 2, 3])
    except QuantumCircuitError as exc:
        print(f"Rejected invalid QFT dimension: {exc}")

    try:
        modular_order(6, 15)
    except QuantumCircuitError as exc:
        print(f"Rejected non-coprime base: {exc}")

    # A base sharing a factor with N can reveal a factor before period finding.
    result = shor_period_pipeline(6, 15)
    assert result["factor"] == 3
    print(f"Early GCD factor discovery: {result}")


def main() -> None:
    random.seed(7)
    demo_qft()
    demo_shor()
    demo_edge_cases()

    # Complexity notes are intentionally printed from the executable model:
    # direct QFT simulation is O(N^2), while the circuit decomposition uses
    # O(q^2) elementary gates for q qubits.
    print("\n=== Complexity ===")
    print("Direct state-vector QFT: O(N^2) arithmetic operations.")
    print("QFT gate decomposition: O(q^2) gates for q qubits.")
    print("Classical order search in this educational model: O(r).")
    print("Real Shor implementations replace classical order search with")
    print("quantum modular exponentiation plus phase estimation.")


if __name__ == "__main__":
    main()
