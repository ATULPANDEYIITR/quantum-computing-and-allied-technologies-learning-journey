"""
Bernstein-Vazirani Algorithm
Hidden-string discovery with classical and quantum simulation.

This self-contained script demonstrates:
- The hidden-string problem and oracle model.
- Classical query complexity.
- The Bernstein-Vazirani quantum circuit.
- State-vector simulation of Hadamard, oracle, and measurement operations.
- Deterministic recovery of the hidden string after one quantum oracle query.
- Noisy measurement experiments.
- Oracle validation and edge cases.
- Circuit-level inspection and query-complexity comparison.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import random
import math
from typing import Iterable


# ---------------------------------------------------------------------------
# Hidden-string oracle
# ---------------------------------------------------------------------------

def validate_bit_string(bits: str, name: str = "bit string") -> None:
    if not bits:
        raise ValueError(f"{name} must not be empty.")
    if any(bit not in "01" for bit in bits):
        raise ValueError(f"{name} must contain only 0 and 1.")


def dot_product_mod2(a: str, b: str) -> int:
    """Compute a · b over GF(2), where addition is XOR."""
    if len(a) != len(b):
        raise ValueError("Bit strings must have equal length.")
    validate_bit_string(a, "a")
    validate_bit_string(b, "b")
    return sum(x == "1" and y == "1" for x, y in zip(a, b)) % 2


@dataclass(frozen=True)
class HiddenStringOracle:
    """Oracle implementing f_s(x) = s · x mod 2."""

    hidden: str

    def __post_init__(self) -> None:
        validate_bit_string(self.hidden, "hidden string")

    @property
    def width(self) -> int:
        return len(self.hidden)

    def evaluate(self, x: str) -> int:
        if len(x) != self.width:
            raise ValueError(
                f"Oracle expects {self.width} input bits, received {len(x)}."
            )
        return dot_product_mod2(self.hidden, x)

    def truth_table(self) -> list[tuple[str, int]]:
        return [
            (format(x, f"0{self.width}b"), self.evaluate(format(x, f"0{self.width}b")))
            for x in range(2**self.width)
        ]


# ---------------------------------------------------------------------------
# Classical hidden-string discovery
# ---------------------------------------------------------------------------

def discover_classically(oracle: HiddenStringOracle) -> tuple[str, int]:
    """
    Recover every hidden bit by querying the oracle with each unit vector.

    Query e_i returns the i-th hidden bit because:
        s · e_i = s_i mod 2

    The method therefore uses exactly n oracle queries for an n-bit secret.
    """
    recovered = []

    for index in range(oracle.width):
        input_bits = ["0"] * oracle.width
        input_bits[index] = "1"
        recovered.append(str(oracle.evaluate("".join(input_bits))))

    return "".join(recovered), oracle.width


def classical_worst_case_query_count(n: int) -> int:
    if n < 1:
        raise ValueError("n must be positive.")
    return n


# ---------------------------------------------------------------------------
# Quantum state-vector utilities
# ---------------------------------------------------------------------------

ComplexVector = list[complex]


def basis_state(index: int, qubits: int) -> ComplexVector:
    size = 2**qubits
    state = [0j] * size
    state[index] = 1 + 0j
    return state


def tensor_product(a: ComplexVector, b: ComplexVector) -> ComplexVector:
    return [x * y for x in a for y in b]


def normalize(state: ComplexVector) -> ComplexVector:
    magnitude = math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))
    if magnitude == 0:
        raise ValueError("Cannot normalize a zero vector.")
    return [amplitude / magnitude for amplitude in state]


def apply_hadamard_all(state: ComplexVector, qubits: int) -> ComplexVector:
    """
    Apply H to every qubit.

    The amplitude transformation is performed directly from the
    state-vector definition rather than constructing a matrix.
    """
    size = 2**qubits
    result = [0j] * size
    scale = 1 / math.sqrt(2)

    for output in range(size):
        total = 0j
        for source in range(size):
            parity = (output & source).bit_count() % 2
            sign = -1 if parity else 1
            total += sign * state[source]
        result[output] = total * (scale**qubits)

    return normalize(result)


def prepare_bv_initial_state(n: int) -> ComplexVector:
    """
    Prepare |0...0>|1> and apply H to all n+1 qubits.

    Qubit ordering here is:
        [n input qubits][one oracle-output qubit]
    """
    state = basis_state(1, n + 1)
    return apply_hadamard_all(state, n + 1)


def apply_bv_oracle(
    state: ComplexVector,
    hidden: str,
) -> ComplexVector:
    """
    Apply the Bernstein-Vazirani oracle.

    The oracle maps:
        |x>|y> -> |x>|y XOR f_s(x)>

    Since the state is represented by basis-index amplitudes, each basis
    amplitude is moved to the corresponding transformed basis index.
    """
    validate_bit_string(hidden, "hidden string")
    n = len(hidden)
    expected_size = 2 ** (n + 1)

    if len(state) != expected_size:
        raise ValueError("State vector has the wrong number of amplitudes.")

    result = [0j] * expected_size
    output_mask = 1

    for index, amplitude in enumerate(state):
        if abs(amplitude) < 1e-15:
            continue

        input_value = index >> 1
        output_bit = index & output_mask

        input_bits = format(input_value, f"0{n}b")
        function_value = dot_product_mod2(hidden, input_bits)
        new_output = output_bit ^ function_value
        new_index = (input_value << 1) | new_output

        result[new_index] += amplitude

    return result


def probabilities(state: ComplexVector) -> list[float]:
    return [abs(amplitude) ** 2 for amplitude in state]


def apply_hadamard_to_input_register(
    state: ComplexVector,
    n: int,
) -> ComplexVector:
    """
    Apply H to the n input qubits while leaving the oracle-output qubit
    untouched.

    For this implementation, each basis index has the output qubit in
    the least-significant bit.
    """
    result = [0j] * len(state)
    scale = 1 / math.sqrt(2**n)
    input_size = 2**n

    for output_bit in (0, 1):
        for output_input in range(input_size):
            total = 0j

            for source_input in range(input_size):
                parity = (output_input & source_input).bit_count() % 2
                sign = -1 if parity else 1
                source_index = (source_input << 1) | output_bit
                total += sign * state[source_index]

            result[(output_input << 1) | output_bit] = total * scale

    return normalize(result)


def measure_input_register(
    state: ComplexVector,
    n: int,
    rng: random.Random,
) -> str:
    """
    Sample the input register according to its marginal probabilities.
    """
    input_probabilities = [0.0] * (2**n)

    for index, amplitude in enumerate(state):
        input_value = index >> 1
        input_probabilities[input_value] += abs(amplitude) ** 2

    sample = rng.random()
    cumulative = 0.0

    for input_value, probability in enumerate(input_probabilities):
        cumulative += probability
        if sample <= cumulative:
            return format(input_value, f"0{n}b")

    return format((2**n) - 1, f"0{n}b")


# ---------------------------------------------------------------------------
# Bernstein-Vazirani quantum algorithm
# ---------------------------------------------------------------------------

def bernstein_vazirani(
    hidden: str,
    rng: random.Random | None = None,
) -> tuple[str, ComplexVector]:
    """
    Run a full ideal state-vector simulation.

    The phase-kickback mechanism turns the oracle response into phases
    (-1)^(s·x). The final Hadamards transform those phases into the basis
    state |s>, so measuring the input register returns s with probability 1.
    """
    validate_bit_string(hidden, "hidden string")

    if rng is None:
        rng = random.Random()

    n = len(hidden)

    state = prepare_bv_initial_state(n)
    state = apply_bv_oracle(state, hidden)
    state = apply_hadamard_to_input_register(state, n)

    recovered = measure_input_register(state, n, rng)
    return recovered, state


# ---------------------------------------------------------------------------
# Circuit inspection
# ---------------------------------------------------------------------------

def oracle_circuit_description(hidden: str) -> list[str]:
    """
    Describe the oracle as CNOT connections.

    For every hidden bit equal to 1, the corresponding input qubit controls
    a CNOT targeting the oracle-output qubit.
    """
    validate_bit_string(hidden, "hidden string")

    gates = []
    for index, bit in enumerate(hidden):
        if bit == "1":
            gates.append(f"CNOT(input[{index}], output)")
    return gates


def print_state_support(
    state: ComplexVector,
    qubits: int,
    threshold: float = 1e-10,
) -> None:
    for index, amplitude in enumerate(state):
        if abs(amplitude) > threshold:
            print(
                f"|{index:0{qubits}b}> : "
                f"amplitude={amplitude.real:+.6f}{amplitude.imag:+.6f}i, "
                f"probability={abs(amplitude) ** 2:.6f}"
            )


# ---------------------------------------------------------------------------
# Noisy measurement experiment
# ---------------------------------------------------------------------------

def noisy_measurement(
    correct_state: str,
    error_probability: float,
    rng: random.Random,
) -> str:
    """
    Model classical readout noise.

    This is deliberately separate from the ideal quantum circuit: the ideal
    BV circuit produces the correct basis state, while this function models
    errors introduced when the result is read.
    """
    if not 0 <= error_probability <= 1:
        raise ValueError("error_probability must be between 0 and 1.")

    result = list(correct_state)

    for i, bit in enumerate(result):
        if rng.random() < error_probability:
            result[i] = "1" if bit == "0" else "0"

    return "".join(result)


def run_noisy_experiment(
    hidden: str,
    trials: int = 1000,
    error_probability: float = 0.02,
    seed: int = 7,
) -> Counter[str]:
    validate_bit_string(hidden, "hidden string")

    if trials <= 0:
        raise ValueError("trials must be positive.")

    rng = random.Random(seed)
    counts: Counter[str] = Counter()

    for _ in range(trials):
        recovered, _ = bernstein_vazirani(hidden, rng)
        observed = noisy_measurement(recovered, error_probability, rng)
        counts[observed] += 1

    return counts


# ---------------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------------

def demonstrate_oracle(hidden: str) -> None:
    oracle = HiddenStringOracle(hidden)

    print("\nOracle truth table")
    print("------------------")
    for x, value in oracle.truth_table():
        print(f"f({x}) = {value}")


def demonstrate_classical_solution(hidden: str) -> None:
    oracle = HiddenStringOracle(hidden)
    recovered, queries = discover_classically(oracle)

    print("\nClassical discovery")
    print("-------------------")
    print(f"Hidden string : {hidden}")
    print(f"Recovered     : {recovered}")
    print(f"Oracle calls  : {queries}")


def demonstrate_quantum_solution(hidden: str) -> None:
    rng = random.Random(11)
    recovered, final_state = bernstein_vazirani(hidden, rng)

    print("\nQuantum Bernstein-Vazirani discovery")
    print("------------------------------------")
    print(f"Hidden string : {hidden}")
    print(f"Recovered     : {recovered}")
    print("Oracle calls  : 1")

    print("\nOracle decomposition")
    print("--------------------")
    for gate in oracle_circuit_description(hidden):
        print(gate)

    print("\nFinal state support")
    print("-------------------")
    print_state_support(final_state, len(hidden) + 1)


def demonstrate_query_scaling() -> None:
    print("\nQuery complexity")
    print("----------------")
    print("Input size | Classical unit-vector queries | BV oracle queries")

    for n in (2, 4, 8, 16, 32):
        print(f"{n:10d} | {n:31d} | {1:17d}")

    print(
        "\nThe distinction is oracle-query complexity: classical discovery "
        "requires n queries for an n-bit hidden string, while the ideal "
        "Bernstein-Vazirani circuit requires one quantum oracle query."
    )


def demonstrate_noisy_measurements(hidden: str) -> None:
    counts = run_noisy_experiment(
        hidden,
        trials=1000,
        error_probability=0.02,
        seed=42,
    )

    print("\nNoisy readout experiment")
    print("------------------------")
    print(f"Hidden string : {hidden}")
    print("Readout error : 2% per bit")
    print(f"Trials        : {sum(counts.values())}")

    for observed, count in counts.most_common(8):
        print(f"{observed} -> {count}")


def demonstrate_edge_cases() -> None:
    print("\nValidation and edge cases")
    print("-------------------------")

    try:
        HiddenStringOracle("")
    except ValueError as exc:
        print(f"Empty secret rejected: {exc}")

    try:
        HiddenStringOracle("10201")
    except ValueError as exc:
        print(f"Non-binary secret rejected: {exc}")

    oracle = HiddenStringOracle("1011")

    try:
        oracle.evaluate("101")
    except ValueError as exc:
        print(f"Wrong-width query rejected: {exc}")

    try:
        noisy_measurement("1011", 1.5, random.Random())
    except ValueError as exc:
        print(f"Invalid noise probability rejected: {exc}")


def main() -> None:
    hidden = "101101"

    print("Bernstein-Vazirani Algorithm")
    print("============================")
    print(f"Selected hidden string: {hidden}")

    demonstrate_oracle(hidden)
    demonstrate_classical_solution(hidden)
    demonstrate_quantum_solution(hidden)
    demonstrate_query_scaling()
    demonstrate_noisy_measurements(hidden)
    demonstrate_edge_cases()


if __name__ == "__main__":
    main()
