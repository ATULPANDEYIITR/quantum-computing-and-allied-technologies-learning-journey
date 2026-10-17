#!/usr/bin/env python3
"""
Deutsch Algorithm: an executable study of the first quantum speedup.

The Deutsch problem distinguishes two classes of Boolean functions:
constant functions, whose two outputs are equal, and balanced functions,
whose two outputs differ.

A deterministic classical algorithm needs two function evaluations in
the worst case. A single ideal quantum oracle query suffices because
Hadamard interference converts the relevant global property into a
measurable computational-basis result.

This program implements a state-vector simulator using only the Python
standard library. It includes the quantum circuit, reversible oracle,
state normalization checks, measurement interpretation, exhaustive
function verification, and a noisy measurement experiment.

The speedup concerns oracle-query complexity, not a universal reduction
in total computation time.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Sequence


Complex = complex
StateVector = list[Complex]
BooleanFunction = Callable[[int], int]

EPSILON = 1e-10


def format_complex(value: Complex) -> str:
    """Format a complex amplitude for readable circuit diagnostics."""
    return f"{value.real:+.4f}{value.imag:+.4f}j"


def inner_product(left: Sequence[Complex],
                  right: Sequence[Complex]) -> Complex:
    """Compute the standard complex inner product."""
    if len(left) != len(right):
        raise ValueError("State vectors must have equal dimensions.")
    return sum(a.conjugate() * b for a, b in zip(left, right))


def norm_squared(state: Sequence[Complex]) -> float:
    """Return the probability norm of a state vector."""
    return sum(abs(amplitude) ** 2 for amplitude in state)


def validate_state(state: Sequence[Complex],
                   expected_qubits: int | None = None) -> None:
    """Reject malformed, non-finite, or non-normalized quantum states."""
    if not state:
        raise ValueError("A state vector cannot be empty.")

    dimension = len(state)
    if dimension & (dimension - 1):
        raise ValueError("State dimension must be a power of two.")

    if expected_qubits is not None and dimension != 2 ** expected_qubits:
        raise ValueError("State dimension does not match qubit count.")

    if any(not math.isfinite(value.real)
           or not math.isfinite(value.imag) for value in state):
        raise ValueError("State amplitudes must be finite.")

    if not math.isclose(norm_squared(state), 1.0, abs_tol=EPSILON):
        raise ValueError("Quantum state must be normalized.")


def hadamard_matrix() -> list[list[float]]:
    """Return the single-qubit Hadamard matrix."""
    scale = 1.0 / math.sqrt(2.0)
    return [[scale, scale], [scale, -scale]]


def apply_single_qubit_gate(
    state: Sequence[Complex],
    gate: Sequence[Sequence[Complex]],
    qubit: int,
    number_of_qubits: int,
) -> StateVector:
    """
    Apply a 2x2 gate to one qubit using little-endian qubit indexing.

    Qubit zero is the least significant bit of the basis-state index.
    """
    if number_of_qubits < 1:
        raise ValueError("At least one qubit is required.")
    if not 0 <= qubit < number_of_qubits:
        raise ValueError("Qubit index is out of range.")
    if len(state) != 2 ** number_of_qubits:
        raise ValueError("State dimension is incorrect.")
    if len(gate) != 2 or any(len(row) != 2 for row in gate):
        raise ValueError("A single-qubit gate must be a 2x2 matrix.")

    result = list(state)
    mask = 1 << qubit

    for index in range(len(state)):
        if index & mask:
            continue

        paired_index = index | mask
        amplitude_zero = state[index]
        amplitude_one = state[paired_index]

        result[index] = (
            gate[0][0] * amplitude_zero
            + gate[0][1] * amplitude_one
        )
        result[paired_index] = (
            gate[1][0] * amplitude_zero
            + gate[1][1] * amplitude_one
        )

    return result


def apply_hadamard_all(
    state: Sequence[Complex],
    number_of_qubits: int,
) -> StateVector:
    """Apply a Hadamard gate to every qubit."""
    result = list(state)
    for qubit in range(number_of_qubits):
        result = apply_single_qubit_gate(
            result, hadamard_matrix(), qubit, number_of_qubits
        )
    return result


def zero_state(number_of_qubits: int) -> StateVector:
    """Construct the computational basis state |00...0>."""
    if number_of_qubits < 1:
        raise ValueError("At least one qubit is required.")
    state = [0j] * (2 ** number_of_qubits)
    state[0] = 1 + 0j
    return state


def x_gate() -> list[list[Complex]]:
    """Return the Pauli-X gate, which exchanges |0> and |1>."""
    return [[0j, 1 + 0j], [1 + 0j, 0j]]


def validate_boolean_function(function: BooleanFunction) -> None:
    """Ensure a one-bit Boolean oracle returns an actual binary integer."""
    for input_bit in (0, 1):
        output = function(input_bit)
        if type(output) is not int or output not in (0, 1):
            raise ValueError(
                f"f({input_bit}) must return integer 0 or 1."
            )


@dataclass(frozen=True)
class OracleDescription:
    """Truth-table representation of a Deutsch oracle."""
    f_zero: int
    f_one: int

    def __post_init__(self) -> None:
        if self.f_zero not in (0, 1) or self.f_one not in (0, 1):
            raise ValueError("Oracle outputs must be bits.")

    @classmethod
    def from_function(
        cls, function: BooleanFunction
    ) -> OracleDescription:
        validate_boolean_function(function)
        return cls(function(0), function(1))

    @property
    def is_constant(self) -> bool:
        return self.f_zero == self.f_one

    @property
    def classification(self) -> str:
        return "constant" if self.is_constant else "balanced"

    def evaluate(self, input_bit: int) -> int:
        """Evaluate the truth table without changing the oracle."""
        if input_bit not in (0, 1):
            raise ValueError("Input must be a bit.")
        return self.f_zero if input_bit == 0 else self.f_one


def apply_deutsch_oracle(
    state: Sequence[Complex],
    oracle: OracleDescription,
) -> StateVector:
    """
    Apply Uf|x,y> = |x, y XOR f(x)>.

    Basis indices use index = x + 2*y. This reversible permutation
    implements the oracle without erasing information about x.
    """
    if len(state) != 4:
        raise ValueError("Deutsch's circuit requires exactly two qubits.")

    result = [0j] * 4

    for index, amplitude in enumerate(state):
        x = index & 1
        y = (index >> 1) & 1
        output_y = y ^ oracle.evaluate(x)
        output_index = x | (output_y << 1)
        result[output_index] += amplitude

    validate_state(result, expected_qubits=2)
    return result


def measurement_probabilities(
    state: Sequence[Complex],
) -> list[float]:
    """Convert amplitudes into computational-basis probabilities."""
    validate_state(state)
    return [abs(amplitude) ** 2 for amplitude in state]


def measure_qubit_zero(
    state: Sequence[Complex],
    rng: random.Random,
) -> int:
    """
    Sample the first qubit's computational-basis measurement.

    The probability of outcome zero is the sum of probabilities for
    basis indices whose least significant bit is zero.
    """
    validate_state(state)

    probability_zero = sum(
        abs(amplitude) ** 2
        for index, amplitude in enumerate(state)
        if (index & 1) == 0
    )

    return 0 if rng.random() < probability_zero else 1


def deutsch_circuit(
    oracle: OracleDescription,
) -> StateVector:
    """
    Run the complete ideal Deutsch circuit.

    The ancilla begins in |1>. Hadamards prepare |+>|->, the oracle
    introduces a phase determined by f(x), and a final Hadamard on
    the input qubit converts that phase pattern into a classification.
    """
    state = zero_state(2)

    # Prepare the phase-kickback ancilla in |->.
    state = apply_single_qubit_gate(state, x_gate(), 1, 2)
    state = apply_hadamard_all(state, 2)

    # A single oracle invocation encodes both truth-table values
    # into relative phase while leaving the ancilla in |->.
    state = apply_deutsch_oracle(state, oracle)

    # Interference places constant functions in input outcome 0 and
    # balanced functions in input outcome 1.
    state = apply_single_qubit_gate(
        state, hadamard_matrix(), 0, 2
    )

    validate_state(state, expected_qubits=2)
    return state


def theoretical_output_probability(
    oracle: OracleDescription,
) -> float:
    """
    Calculate P(input=0) from the phase difference.

    The result is ((-1)^f(0) + (-1)^f(1))^2 / 4.
    """
    phase_sum = (
        (-1) ** oracle.f_zero
        + (-1) ** oracle.f_one
    )
    return float(phase_sum ** 2 / 4.0)


def run_classical_deterministic_strategy(
    oracle: OracleDescription,
) -> tuple[str, int]:
    """
    Model a deterministic classical strategy with early termination.

    One observed output cannot distinguish a constant function from
    a balanced function. The second query resolves the ambiguity.
    """
    first = oracle.evaluate(0)
    second = oracle.evaluate(1)

    classification = (
        "constant" if first == second else "balanced"
    )
    return classification, 2


def demonstrate_oracle_families() -> None:
    """Inspect every Boolean function from its truth table."""
    print("\nOracle families and ideal circuit outcomes")
    print("-" * 66)

    for f_zero in (0, 1):
        for f_one in (0, 1):
            oracle = OracleDescription(f_zero, f_one)
            state = deutsch_circuit(oracle)
            probabilities = measurement_probabilities(state)
            predicted_probability = theoretical_output_probability(
                oracle
            )

            result = "constant" if probabilities[0] > 0.5 else "balanced"

            assert result == oracle.classification
            assert math.isclose(
                probabilities[0],
                predicted_probability,
                abs_tol=EPSILON,
            )

            print(
                f"f(0)={f_zero}, f(1)={f_one} | "
                f"{oracle.classification:8s} | "
                f"P(input=0)={probabilities[0]:.1f} | "
                f"result={result}"
            )


def demonstrate_interference() -> None:
    """Display the amplitudes after each meaningful circuit stage."""
    print("\nState-vector evolution for f(x)=x")
    print("-" * 66)

    state = zero_state(2)
    print("Initial |01>: ", [format_complex(a) for a in state])

    state = apply_single_qubit_gate(state, x_gate(), 1, 2)
    state = apply_hadamard_all(state, 2)
    print("After preparation:", [format_complex(a) for a in state])

    oracle = OracleDescription(0, 1)
    state = apply_deutsch_oracle(state, oracle)
    print("After oracle:     ", [format_complex(a) for a in state])

    state = apply_single_qubit_gate(
        state, hadamard_matrix(), 0, 2
    )
    print("After final H:    ", [format_complex(a) for a in state])

    probabilities = measurement_probabilities(state)
    print("Probabilities:    ", [
        round(probability, 6) for probability in probabilities
    ])

    assert math.isclose(probabilities[1], 0.0, abs_tol=EPSILON)
    assert math.isclose(probabilities[0], 0.0, abs_tol=EPSILON)
    assert math.isclose(probabilities[2], 0.5, abs_tol=EPSILON)
    assert math.isclose(probabilities[3], 0.5, abs_tol=EPSILON)


def demonstrate_measurement_statistics(
    oracle: OracleDescription,
    shots: int = 1000,
    seed: int = 2026,
) -> None:
    """
    Repeat measurements of the same ideal circuit.

    Repetition estimates probabilities but does not increase the
    number of oracle calls required by each individual circuit run.
    """
    if shots <= 0:
        raise ValueError("shots must be positive.")

    state = deutsch_circuit(oracle)
    rng = random.Random(seed)
    counts = {0: 0, 1: 0}

    for _ in range(shots):
        counts[measure_qubit_zero(state, rng)] += 1

    print(f"\nMeasurement experiment: {shots} shots")
    print(f"Expected classification: {oracle.classification}")
    print(f"Input-qubit counts: {counts}")
    print(
        "Observed classification: "
        + ("constant" if counts[0] == shots else "balanced")
    )


def demonstrate_noise(
    oracle: OracleDescription,
    shots: int = 1000,
    bit_flip_probability: float = 0.02,
    seed: int = 73,
) -> None:
    """
    Simulate readout bit-flip noise on the measured input qubit.

    This models classical readout errors only, not gate errors,
    decoherence, or errors inside the oracle.
    """
    if shots <= 0:
        raise ValueError("shots must be positive.")
    if not 0.0 <= bit_flip_probability <= 1.0:
        raise ValueError("Noise probability must lie in [0, 1].")

    rng = random.Random(seed)
    state = deutsch_circuit(oracle)
    counts = {0: 0, 1: 0}

    for _ in range(shots):
        outcome = measure_qubit_zero(state, rng)
        if rng.random() < bit_flip_probability:
            outcome ^= 1
        counts[outcome] += 1

    print("\nReadout-noise experiment")
    print(f"Flip probability: {bit_flip_probability:.3f}")
    print(f"Measured counts: {counts}")
    print(
        "A single noisy measurement can misclassify the function; "
        "repeated measurements can help estimate the dominant outcome."
    )


def verify_unitary_oracle_reversibility() -> None:
    """Check that each oracle is a norm-preserving permutation."""
    test_states = [
        [1 + 0j, 0j, 0j, 0j],
        [0j, 1 + 0j, 0j, 0j],
        [0j, 0j, 1 + 0j, 0j],
        [0j, 0j, 0j, 1 + 0j],
    ]

    for f_zero in (0, 1):
        for f_one in (0, 1):
            oracle = OracleDescription(f_zero, f_one)
            for state in test_states:
                transformed = apply_deutsch_oracle(state, oracle)
                assert math.isclose(
                    norm_squared(transformed),
                    1.0,
                    abs_tol=EPSILON,
                )


def verify_inner_product_preservation() -> None:
    """Check the oracle's action on a pair of normalized superpositions."""
    scale = 1 / math.sqrt(2)
    first = [scale + 0j, 0j, scale + 0j, 0j]
    second = [0j, scale + 0j, 0j, scale + 0j]

    for oracle in (
        OracleDescription(0, 0),
        OracleDescription(0, 1),
        OracleDescription(1, 0),
        OracleDescription(1, 1),
    ):
        transformed_first = apply_deutsch_oracle(first, oracle)
        transformed_second = apply_deutsch_oracle(second, oracle)

        assert abs(
            inner_product(first, second)
            - inner_product(transformed_first, transformed_second)
        ) < EPSILON


def demonstrate_query_complexity() -> None:
    """Contrast oracle calls with the surrounding circuit operations."""
    print("\nOracle-query complexity")
    print("-" * 66)
    print("Classical deterministic worst case: 2 oracle evaluations")
    print("Deutsch quantum circuit:            1 oracle invocation")
    print("Quantum circuit gates:               several elementary gates")
    print("Input size:                           one Boolean input bit")
    print(
        "The result establishes a query-complexity separation, "
        "not an unconditional wall-clock speedup."
    )


def demonstrate_validation() -> None:
    """Exercise invalid inputs and ensure failures are explicit."""
    print("\nValidation checks")
    print("-" * 66)

    invalid_functions: list[BooleanFunction] = [
        lambda bit: 2,
        lambda bit: True,
        lambda bit: -1,
    ]

    for function in invalid_functions:
        try:
            OracleDescription.from_function(function)
        except ValueError as error:
            print(f"Rejected invalid oracle: {error}")
        else:
            raise AssertionError("Invalid Boolean function was accepted.")

    try:
        validate_state([1 + 0j, 1 + 0j])
    except ValueError as error:
        print(f"Rejected unnormalized state: {error}")

    try:
        apply_single_qubit_gate(
            [1 + 0j, 0j, 0j, 0j],
            hadamard_matrix(),
            2,
            2,
        )
    except ValueError as error:
        print(f"Rejected invalid qubit index: {error}")


def main() -> None:
    print("DEUTSCH ALGORITHM: QUANTUM ORACLE INTERFERENCE")
    print("=" * 66)

    demonstrate_oracle_families()
    demonstrate_interference()

    oracle = OracleDescription.from_function(lambda bit: bit)
    quantum_state = deutsch_circuit(oracle)
    quantum_result = (
        "constant"
        if measurement_probabilities(quantum_state)[0] > 0.5
        else "balanced"
    )
    classical_result, classical_queries = (
        run_classical_deterministic_strategy(oracle)
    )

    print("\nClassical and quantum results")
    print("-" * 66)
    print(f"Classical: {classical_result}, queries={classical_queries}")
    print(f"Quantum:   {quantum_result}, oracle calls=1")

    demonstrate_measurement_statistics(
        OracleDescription(1, 1), shots=1000
    )
    demonstrate_noise(oracle, shots=1000)
    demonstrate_query_complexity()
    demonstrate_validation()

    verify_unitary_oracle_reversibility()
    verify_inner_product_preservation()
    print("\nAll Deutsch algorithm assertions passed.")


if __name__ == "__main__":
    main()
