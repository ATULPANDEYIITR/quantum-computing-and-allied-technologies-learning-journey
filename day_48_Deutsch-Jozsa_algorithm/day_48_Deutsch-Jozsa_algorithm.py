"""
Deutsch-Jozsa Algorithm: Oracle-Based Quantum Computation

A self-contained simulation using Python's standard library.

The algorithm determines whether a Boolean function is constant or balanced
with one quantum oracle query, assuming the promise that the function belongs
to one of these two classes.

This simulator represents quantum states with complex amplitude vectors and
implements Hadamard transforms, phase oracles, measurement probabilities,
and classical verification.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Sequence


BitFunction = Callable[[int], int]


class QuantumSimulationError(ValueError):
    """Raised when a quantum circuit violates its simulation constraints."""


@dataclass(frozen=True)
class Measurement:
    bitstring: str
    probability: float


@dataclass
class QuantumRegister:
    """State-vector representation of a small quantum register."""

    num_qubits: int
    amplitudes: list[complex]

    def __post_init__(self) -> None:
        expected = 1 << self.num_qubits
        if self.num_qubits < 1 or len(self.amplitudes) != expected:
            raise QuantumSimulationError("Invalid quantum register dimensions.")

        norm = sum(abs(amplitude) ** 2 for amplitude in self.amplitudes)
        if not math.isclose(norm, 1.0, abs_tol=1e-9):
            raise QuantumSimulationError(
                f"State must be normalized; squared norm is {norm}."
            )

    @classmethod
    def zero_state(cls, num_qubits: int) -> QuantumRegister:
        if num_qubits < 1:
            raise QuantumSimulationError("At least one qubit is required.")
        amplitudes = [0j] * (1 << num_qubits)
        amplitudes[0] = 1 + 0j
        return cls(num_qubits, amplitudes)

    @property
    def dimension(self) -> int:
        return len(self.amplitudes)

    def hadamard_all(self) -> None:
        """Apply H tensor-product gates using a Walsh-Hadamard transform."""
        size = self.dimension
        stride = 1

        while stride < size:
            for start in range(0, size, stride * 2):
                for offset in range(stride):
                    left = self.amplitudes[start + offset]
                    right = self.amplitudes[start + offset + stride]

                    self.amplitudes[start + offset] = left + right
                    self.amplitudes[start + offset + stride] = left - right

            stride *= 2

        scale = 1 / math.sqrt(size)
        self.amplitudes = [amplitude * scale for amplitude in self.amplitudes]

    def probabilities(self) -> list[float]:
        return [abs(amplitude) ** 2 for amplitude in self.amplitudes]

    def measure(self, rng: random.Random | None = None) -> Measurement:
        """Sample a computational-basis outcome from the Born distribution."""
        generator = rng if rng is not None else random.Random()
        probabilities = self.probabilities()
        outcome = generator.choices(
            range(self.dimension), weights=probabilities, k=1
        )[0]

        return Measurement(
            bitstring=format(outcome, f"0{self.num_qubits}b"),
            probability=probabilities[outcome],
        )


def validate_boolean_function(function: BitFunction, n: int) -> list[int]:
    if n < 1:
        raise QuantumSimulationError("Input width must be positive.")

    outputs = []
    for x in range(1 << n):
        value = function(x)
        if value not in (0, 1):
            raise QuantumSimulationError(
                f"Oracle returned {value!r} for input {x}; expected 0 or 1."
            )
        outputs.append(value)

    return outputs


def classify_promise(outputs: Sequence[int]) -> str:
    """Classify a function only when it satisfies the Deutsch-Jozsa promise."""
    if not outputs:
        raise QuantumSimulationError("Oracle truth table cannot be empty.")

    if all(value == outputs[0] for value in outputs):
        return "constant"

    if outputs.count(1) * 2 == len(outputs):
        return "balanced"

    raise QuantumSimulationError(
        "Function is neither constant nor balanced; promise is violated."
    )


def phase_oracle(
    register: QuantumRegister, function: BitFunction, input_qubits: int
) -> None:
    """
    Implement phase kickback using an implicit ancilla in |->.

    The oracle transforms |x> into (-1)^f(x)|x> on the input register.
    The ancilla need not be stored explicitly because its effect is known.
    """
    if register.num_qubits != input_qubits:
        raise QuantumSimulationError("Register width does not match input width.")

    for x in range(register.dimension):
        value = function(x)
        if value not in (0, 1):
            raise QuantumSimulationError("Oracle outputs must be binary.")
        if value == 1:
            register.amplitudes[x] *= -1


def deutsch_jozsa(
    function: BitFunction,
    n: int,
    rng: random.Random | None = None,
) -> dict[str, object]:
    """
    Execute the ideal Deutsch-Jozsa circuit.

    The state vector contains n input qubits. A conventional circuit also
    prepares an ancilla in |->; phase kickback is simulated directly here.
    """
    outputs = validate_boolean_function(function, n)
    classification = classify_promise(outputs)

    register = QuantumRegister.zero_state(n)
    register.hadamard_all()

    uniform_initial_state = register.amplitudes.copy()

    phase_oracle(register, function, n)
    register.hadamard_all()

    probabilities = register.probabilities()
    zero_probability = probabilities[0]

    # The ideal circuit gives probability one for |0...0> on constant
    # functions and zero for that outcome on balanced functions.
    predicted = "constant" if math.isclose(
        zero_probability, 1.0, abs_tol=1e-9
    ) else "balanced"

    measurement = register.measure(rng)

    return {
        "input_qubits": n,
        "oracle_queries": 1,
        "truth_table": outputs,
        "promise_class": classification,
        "predicted_class": predicted,
        "measurement": measurement.bitstring,
        "measurement_probability": measurement.probability,
        "zero_state_probability": zero_probability,
        "final_probabilities": probabilities,
        "initial_superposition": uniform_initial_state,
    }


def constant_zero(_: int) -> int:
    return 0


def constant_one(_: int) -> int:
    return 1


def parity_function(x: int) -> int:
    """Balanced function equal to the least significant input bit."""
    return x & 1


def xor_parity(x: int) -> int:
    """Balanced function equal to the parity of all input bits."""
    return x.bit_count() & 1


def non_promise_function(x: int) -> int:
    """For two input bits, this function has one marked input."""
    return int(x == 0)


def run_tests() -> None:
    assert classify_promise([0, 0, 0, 0]) == "constant"
    assert classify_promise([1, 1, 1, 1]) == "constant"
    assert classify_promise([0, 1, 0, 1]) == "balanced"

    for function in (constant_zero, constant_one):
        result = deutsch_jozsa(function, 3, random.Random(7))
        assert result["predicted_class"] == "constant"
        assert math.isclose(result["zero_state_probability"], 1.0)

    for function in (parity_function, xor_parity):
        result = deutsch_jozsa(function, 3, random.Random(7))
        assert result["predicted_class"] == "balanced"
        assert math.isclose(result["zero_state_probability"], 0.0)

    try:
        deutsch_jozsa(non_promise_function, 2)
    except QuantumSimulationError:
        pass
    else:
        raise AssertionError("Promise violation should have been rejected.")

    try:
        validate_boolean_function(lambda _: 2, 2)
    except QuantumSimulationError:
        pass
    else:
        raise AssertionError("Non-binary oracle output should be rejected.")

    print("All Deutsch-Jozsa tests passed.")


def demonstrate_interference() -> None:
    examples: list[tuple[str, BitFunction]] = [
        ("Constant zero", constant_zero),
        ("Constant one", constant_one),
        ("Single-bit parity", parity_function),
        ("Three-bit XOR parity", xor_parity),
    ]

    rng = random.Random(42)

    for name, function in examples:
        result = deutsch_jozsa(function, 3, rng)
        print(f"\n{name}")
        print(f"  Oracle outputs: {result['truth_table']}")
        print(f"  Promise class:  {result['promise_class']}")
        print(f"  Circuit result: {result['predicted_class']}")
        print(f"  Measured state: {result['measurement']}")
        print(
            "  P(|000>):      "
            f"{result['zero_state_probability']:.6f}"
        )
        print(f"  Oracle calls:   {result['oracle_queries']}")


def demonstrate_scaling() -> None:
    print("\nQuery-complexity comparison")

    for n in (2, 4, 8, 12):
        classical_worst_case = (1 << (n - 1)) + 1
        quantum_queries = 1
        print(
            f"n={n:2d}: states={1 << n:5d}, "
            f"quantum oracle queries={quantum_queries}, "
            f"classical deterministic worst-case queries="
            f"{classical_worst_case}"
        )


if __name__ == "__main__":
    run_tests()
    demonstrate_interference()
    demonstrate_scaling()
