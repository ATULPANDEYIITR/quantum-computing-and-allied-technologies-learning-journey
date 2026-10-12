#!/usr/bin/env python3
"""
Quantum simulators: statevector and shot-based simulation.

A self-contained educational simulator using only the Python standard library.
It implements complex statevectors, single-qubit gates, controlled gates,
measurement probabilities, seeded shot sampling, entanglement, noise-free
circuit execution, statistical comparisons, and resource estimates.

Run:
    python quantum_simulators.py

The simulator is intended for learning and small circuits. It is not a
replacement for optimized quantum simulation frameworks.
"""

from __future__ import annotations

import math
import random
import time
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Sequence


ComplexMatrix2 = tuple[
    tuple[complex, complex],
    tuple[complex, complex],
]


class QuantumSimulationError(Exception):
    """Base exception for quantum simulation failures."""


class InvalidCircuitError(QuantumSimulationError):
    """Raised when a gate or circuit violates its structural constraints."""


class ResourceLimitError(QuantumSimulationError):
    """Raised before an unsafe statevector allocation."""


def validate_qubit_count(qubits: int, maximum: int = 24) -> None:
    if isinstance(qubits, bool) or not isinstance(qubits, int):
        raise InvalidCircuitError("Qubit count must be an integer.")
    if qubits < 1:
        raise InvalidCircuitError("At least one qubit is required.")
    if qubits > maximum:
        raise ResourceLimitError(
            f"{qubits} qubits exceed the configured limit of {maximum}."
        )


def validate_qubit(qubit: int, qubits: int) -> None:
    if isinstance(qubit, bool) or not isinstance(qubit, int):
        raise InvalidCircuitError("Qubit index must be an integer.")
    if not 0 <= qubit < qubits:
        raise InvalidCircuitError(
            f"Qubit index {qubit} is outside [0, {qubits - 1}]."
        )


def validate_probability(probability: float) -> float:
    if isinstance(probability, bool) or not isinstance(
        probability, (int, float)
    ):
        raise InvalidCircuitError("Probability must be numeric.")
    probability = float(probability)
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise InvalidCircuitError("Probability must be finite and in [0, 1].")
    return probability


def normalize_state(state: Sequence[complex]) -> list[complex]:
    if not state:
        raise InvalidCircuitError("A statevector cannot be empty.")

    vector = [complex(amplitude) for amplitude in state]
    if not all(
        math.isfinite(a.real) and math.isfinite(a.imag) for a in vector
    ):
        raise InvalidCircuitError("State amplitudes must be finite.")

    norm_squared = sum(abs(a) ** 2 for a in vector)
    if norm_squared <= 0.0:
        raise InvalidCircuitError("The zero vector cannot be normalized.")

    norm = math.sqrt(norm_squared)
    return [amplitude / norm for amplitude in vector]


def matrix_is_unitary(matrix: ComplexMatrix2, tolerance: float = 1e-10) -> bool:
    for row in matrix:
        if len(row) != 2:
            return False

    for i in range(2):
        for j in range(2):
            inner_product = sum(
                matrix[k][i].conjugate() * matrix[k][j]
                for k in range(2)
            )
            expected = 1.0 if i == j else 0.0
            if abs(inner_product - expected) > tolerance:
                return False
    return True


I: ComplexMatrix2 = (
    (1 + 0j, 0j),
    (0j, 1 + 0j),
)

X: ComplexMatrix2 = (
    (0j, 1 + 0j),
    (1 + 0j, 0j),
)

Y: ComplexMatrix2 = (
    (0j, -1j),
    (1j, 0j),
)

Z: ComplexMatrix2 = (
    (1 + 0j, 0j),
    (0j, -1 + 0j),
)

HADAMARD: ComplexMatrix2 = (
    (1 / math.sqrt(2), 1 / math.sqrt(2)),
    (1 / math.sqrt(2), -1 / math.sqrt(2)),
)


def phase_gate(theta: float) -> ComplexMatrix2:
    if not math.isfinite(theta):
        raise InvalidCircuitError("Phase angle must be finite.")
    return (
        (1 + 0j, 0j),
        (0j, complex(math.cos(theta), math.sin(theta))),
    )


def rotation_y(theta: float) -> ComplexMatrix2:
    if not math.isfinite(theta):
        raise InvalidCircuitError("Rotation angle must be finite.")
    cosine = math.cos(theta / 2)
    sine = math.sin(theta / 2)
    return (
        (complex(cosine), complex(-sine)),
        (complex(sine), complex(cosine)),
    )


@dataclass(frozen=True)
class Gate:
    """A gate description; target and control use little-endian qubit indices."""

    name: str
    target: int
    matrix: ComplexMatrix2
    control: int | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise InvalidCircuitError("Gate name cannot be empty.")
        if not matrix_is_unitary(self.matrix):
            raise InvalidCircuitError(f"Gate {self.name} is not unitary.")
        if self.control is not None and self.control == self.target:
            raise InvalidCircuitError("Control and target must differ.")


class QuantumCircuit:
    """Circuit builder with validated gate placement."""

    def __init__(self, qubits: int, maximum_qubits: int = 24):
        validate_qubit_count(qubits, maximum_qubits)
        self.qubits = qubits
        self.maximum_qubits = maximum_qubits
        self.gates: list[Gate] = []
        self.measurement_qubits: tuple[int, ...] = tuple(range(qubits))

    def add_gate(
        self,
        name: str,
        target: int,
        matrix: ComplexMatrix2,
        control: int | None = None,
    ) -> QuantumCircuit:
        validate_qubit(target, self.qubits)
        if control is not None:
            validate_qubit(control, self.qubits)
            if control == target:
                raise InvalidCircuitError("Control and target must differ.")

        self.gates.append(Gate(name, target, matrix, control))
        return self

    def x(self, target: int) -> QuantumCircuit:
        return self.add_gate("X", target, X)

    def h(self, target: int) -> QuantumCircuit:
        return self.add_gate("H", target, HADAMARD)

    def y(self, target: int) -> QuantumCircuit:
        return self.add_gate("Y", target, Y)

    def z(self, target: int) -> QuantumCircuit:
        return self.add_gate("Z", target, Z)

    def phase(self, target: int, theta: float) -> QuantumCircuit:
        return self.add_gate("P", target, phase_gate(theta))

    def ry(self, target: int, theta: float) -> QuantumCircuit:
        return self.add_gate("RY", target, rotation_y(theta))

    def cx(self, control: int, target: int) -> QuantumCircuit:
        return self.add_gate("CX", target, X, control)

    def measure(self, *qubits: int) -> QuantumCircuit:
        selected = qubits if qubits else tuple(range(self.qubits))
        if not selected:
            raise InvalidCircuitError("At least one measurement qubit is required.")
        if len(set(selected)) != len(selected):
            raise InvalidCircuitError("Measurement qubits must be unique.")
        for qubit in selected:
            validate_qubit(qubit, self.qubits)
        self.measurement_qubits = tuple(selected)
        return self


def apply_gate(
    state: list[complex],
    qubits: int,
    gate: Gate,
) -> list[complex]:
    """
    Apply a one-qubit or controlled-X-like unitary in O(2**n) time.

    Qubit zero is the least significant bit of the basis-state index.
    The statevector is updated in pairs so amplitudes are not overwritten
    before both output amplitudes have been calculated.
    """
    validate_qubit(gate.target, qubits)
    if gate.control is not None:
        validate_qubit(gate.control, qubits)

    target_mask = 1 << gate.target
    control_mask = 1 << gate.control if gate.control is not None else 0
    result = state.copy()

    for index in range(len(state)):
        if index & target_mask:
            continue

        partner = index | target_mask

        if control_mask and not (index & control_mask):
            continue

        a0 = state[index]
        a1 = state[partner]
        u00, u01 = gate.matrix[0]
        u10, u11 = gate.matrix[1]

        result[index] = u00 * a0 + u01 * a1
        result[partner] = u10 * a0 + u11 * a1

    return result


def statevector_simulate(
    circuit: QuantumCircuit,
    initial_state: Sequence[complex] | None = None,
) -> list[complex]:
    """Return all final amplitudes without sampling measurement outcomes."""
    dimension = 1 << circuit.qubits

    if initial_state is None:
        state = [0j] * dimension
        state[0] = 1 + 0j
    else:
        if len(initial_state) != dimension:
            raise InvalidCircuitError(
                f"Expected {dimension} amplitudes, received {len(initial_state)}."
            )
        state = normalize_state(initial_state)

    for gate in circuit.gates:
        state = apply_gate(state, circuit.qubits, gate)

    norm_squared = sum(abs(amplitude) ** 2 for amplitude in state)
    if abs(norm_squared - 1.0) > 1e-9:
        raise QuantumSimulationError(
            f"State norm drifted from one: {norm_squared:.12f}"
        )

    return state


def probabilities_from_state(state: Sequence[complex]) -> list[float]:
    probabilities = [abs(amplitude) ** 2 for amplitude in state]
    total = sum(probabilities)

    if total <= 0 or not math.isfinite(total):
        raise QuantumSimulationError("Invalid measurement probability mass.")

    # Correct tiny floating-point drift while preserving relative probabilities.
    return [probability / total for probability in probabilities]


def marginal_probabilities(
    state: Sequence[complex],
    qubits: int,
    measured_qubits: Sequence[int],
) -> list[float]:
    """
    Compute the exact distribution for selected qubits.

    Output bits follow the supplied measured_qubits order, with the first
    selected qubit occupying the least significant output bit.
    """
    if len(state) != 1 << qubits:
        raise InvalidCircuitError("Statevector dimension does not match qubits.")
    if not measured_qubits:
        raise InvalidCircuitError("Select at least one qubit.")
    if len(set(measured_qubits)) != len(measured_qubits):
        raise InvalidCircuitError("Measured qubits must be unique.")

    for qubit in measured_qubits:
        validate_qubit(qubit, qubits)

    output = [0.0] * (1 << len(measured_qubits))

    for basis_index, amplitude in enumerate(state):
        outcome = 0
        for output_bit, source_qubit in enumerate(measured_qubits):
            if basis_index & (1 << source_qubit):
                outcome |= 1 << output_bit
        output[outcome] += abs(amplitude) ** 2

    total = sum(output)
    return [p / total for p in output]


def format_bitstring(value: int, width: int) -> str:
    return format(value, f"0{width}b")


def exact_distribution(
    circuit: QuantumCircuit,
    state: Sequence[complex] | None = None,
) -> dict[str, float]:
    vector = (
        statevector_simulate(circuit)
        if state is None
        else normalize_state(state)
    )
    if len(vector) != 1 << circuit.qubits:
        raise InvalidCircuitError("State dimension does not match circuit.")

    probabilities = marginal_probabilities(
        vector, circuit.qubits, circuit.measurement_qubits
    )
    width = len(circuit.measurement_qubits)

    return {
        format_bitstring(index, width): probability
        for index, probability in enumerate(probabilities)
    }


def sample_shots(
    circuit: QuantumCircuit,
    shots: int,
    seed: int | None = 7,
    state: Sequence[complex] | None = None,
) -> Counter[str]:
    """
    Sample measurement outcomes from exact probabilities.

    A seeded generator makes the demonstration reproducible. Sampling
    introduces statistical uncertainty absent from the exact distribution.
    """
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise InvalidCircuitError("Shots must be a positive integer.")
    if shots > 10_000_000:
        raise ResourceLimitError("Shot count exceeds the configured limit.")

    distribution = exact_distribution(circuit, state)
    outcomes = list(distribution)
    weights = [distribution[outcome] for outcome in outcomes]

    rng = random.Random(seed)
    sampled = rng.choices(outcomes, weights=weights, k=shots)
    return Counter(sampled)


def counts_to_probabilities(
    counts: Counter[str],
    shots: int | None = None,
) -> dict[str, float]:
    actual_shots = sum(counts.values()) if shots is None else shots
    if actual_shots <= 0:
        raise InvalidCircuitError("Counts must contain at least one shot.")
    if sum(counts.values()) != actual_shots:
        raise InvalidCircuitError("Declared shot count does not match counts.")
    return {key: value / actual_shots for key, value in sorted(counts.items())}


def total_variation_distance(
    first: dict[str, float],
    second: dict[str, float],
) -> float:
    """Half the L1 distance between two discrete probability distributions."""
    outcomes = set(first) | set(second)
    return 0.5 * sum(
        abs(first.get(outcome, 0.0) - second.get(outcome, 0.0))
        for outcome in outcomes
    )


def bernoulli_standard_error(probability: float, shots: int) -> float:
    probability = validate_probability(probability)
    if shots <= 0:
        raise InvalidCircuitError("Shots must be positive.")
    return math.sqrt(probability * (1 - probability) / shots)


def expectation_z(state: Sequence[complex], qubit: int, qubits: int) -> float:
    """Calculate the expectation value of Pauli Z for one qubit."""
    validate_qubit(qubit, qubits)
    if len(state) != 1 << qubits:
        raise InvalidCircuitError("State dimension does not match qubit count.")

    expectation = 0.0
    for index, amplitude in enumerate(state):
        eigenvalue = 1.0 if not (index & (1 << qubit)) else -1.0
        expectation += eigenvalue * abs(amplitude) ** 2
    return expectation


def ghz_circuit(qubits: int) -> QuantumCircuit:
    """Create a GHZ circuit with correlated all-zero and all-one outcomes."""
    validate_qubit_count(qubits)
    circuit = QuantumCircuit(qubits).h(0)
    for target in range(1, qubits):
        circuit.cx(0, target)
    return circuit


def bell_circuit() -> QuantumCircuit:
    return QuantumCircuit(2).h(0).cx(0, 1)


def demonstrate_single_qubit_measurement() -> None:
    print("\nSingle-qubit superposition")
    circuit = QuantumCircuit(1).h(0).measure(0)
    state = statevector_simulate(circuit)

    print("Amplitudes:", [complex(round(a.real, 6), round(a.imag, 6)) for a in state])
    print("Exact probabilities:", exact_distribution(circuit))
    counts = sample_shots(circuit, shots=1000, seed=11)
    print("Counts from 1000 shots:", dict(sorted(counts.items())))
    print("Observed probabilities:", counts_to_probabilities(counts))


def demonstrate_bell_entanglement() -> None:
    print("\nBell-state entanglement")
    circuit = bell_circuit().measure(0, 1)
    state = statevector_simulate(circuit)

    print("Nonzero amplitudes:")
    for index, amplitude in enumerate(state):
        if abs(amplitude) > 1e-12:
            print(f"  |{index:02b}>: {amplitude.real:.6f}")

    print("Exact joint distribution:", exact_distribution(circuit))
    counts = sample_shots(circuit, shots=2000, seed=23)
    print("Observed joint counts:", dict(sorted(counts.items())))

    # The reduced measurement distribution for either qubit is uniform,
    # while the joint distribution contains only correlated outcomes.
    print(
        "Qubit 0 exact marginal:",
        marginal_probabilities(state, 2, (0,)),
    )


def demonstrate_shot_convergence() -> None:
    print("\nShot-based convergence toward exact probabilities")
    circuit = QuantumCircuit(1).ry(0, math.pi / 3).measure(0)
    exact = exact_distribution(circuit)
    print("Exact:", exact)

    for shots in (100, 1000, 10000):
        counts = sample_shots(circuit, shots, seed=101)
        observed = counts_to_probabilities(counts)
        distance = total_variation_distance(exact, observed)
        expected_one = exact["1"]
        standard_error = bernoulli_standard_error(expected_one, shots)

        print(
            f"shots={shots:>5} observed={observed} "
            f"TV-distance={distance:.5f} "
            f"SE(P(1))={standard_error:.5f}"
        )


def demonstrate_phase_and_interference() -> None:
    print("\nPhase and interference")
    circuit = (
        QuantumCircuit(1)
        .h(0)
        .phase(0, math.pi)
        .h(0)
        .measure(0)
    )
    state = statevector_simulate(circuit)

    print("Final amplitudes:", state)
    print("Exact distribution:", exact_distribution(circuit))
    print("Interpretation: the phase changes interference after the second H gate.")


def demonstrate_ghz_state() -> None:
    print("\nGHZ correlation")
    circuit = ghz_circuit(4).measure(0, 1, 2, 3)
    distribution = exact_distribution(circuit)
    counts = sample_shots(circuit, 3000, seed=17)

    print("Exact distribution:", distribution)
    print("Sampled counts:", dict(sorted(counts.items())))
    print("Only 0000 and 1111 should have nonzero ideal probabilities.")


def demonstrate_state_validation() -> None:
    print("\nValidation and failure handling")
    invalid_examples: list[tuple[str, Callable[[], object]]] = [
        ("zero-qubit circuit", lambda: QuantumCircuit(0)),
        ("out-of-range gate", lambda: QuantumCircuit(2).h(2)),
        ("self-controlled gate", lambda: QuantumCircuit(2).cx(1, 1)),
        ("wrong state dimension", lambda: statevector_simulate(
            QuantumCircuit(2), [1 + 0j, 0j]
        )),
        ("zero state", lambda: normalize_state([0j, 0j])),
    ]

    for description, operation in invalid_examples:
        try:
            operation()
        except QuantumSimulationError as error:
            print(f"Rejected {description}: {error}")
        else:
            raise AssertionError(f"Expected rejection: {description}")


def estimate_statevector_memory(qubits: int) -> int:
    """
    Estimate raw complex128-like storage at 16 bytes per amplitude.

    Actual Python lists consume much more because every complex object and
    list pointer has additional overhead. This is a lower-bound estimate.
    """
    validate_qubit_count(qubits, maximum=60)
    return (1 << qubits) * 16


def demonstrate_scaling() -> None:
    print("\nStatevector resource estimates")
    for qubits in (10, 15, 20, 24, 28, 30):
        raw_bytes = estimate_statevector_memory(qubits)
        print(
            f"{qubits:>2} qubits: {1 << qubits:>12,} amplitudes, "
            f"raw storage approximately {raw_bytes / (1024 ** 2):.2f} MiB"
        )

    print(
        "A dense statevector needs O(2^n) memory. Applying a local gate "
        "usually costs O(2^n) time. Shot count controls sampling work but "
        "does not remove the need to construct the simulated state."
    )


def demonstrate_benchmark() -> None:
    print("\nSmall-circuit execution timing")
    circuit = ghz_circuit(18)

    started = time.perf_counter()
    state = statevector_simulate(circuit)
    elapsed = time.perf_counter() - started

    norm = sum(abs(amplitude) ** 2 for amplitude in state)
    nonzero = sum(abs(amplitude) > 1e-12 for amplitude in state)

    print(f"Qubits: {circuit.qubits}")
    print(f"Gates: {len(circuit.gates)}")
    print(f"Elapsed: {elapsed:.4f} seconds")
    print(f"Nonzero amplitudes: {nonzero}")
    print(f"Norm squared: {norm:.12f}")


def run_self_tests() -> None:
    """Check deterministic properties before presenting the examples."""
    assert abs(sum(probabilities_from_state([1 / math.sqrt(2)] * 2)) - 1) < 1e-12

    bell = bell_circuit()
    bell_state = statevector_simulate(bell)
    bell_probabilities = probabilities_from_state(bell_state)

    assert math.isclose(bell_probabilities[0], 0.5, abs_tol=1e-10)
    assert math.isclose(bell_probabilities[3], 0.5, abs_tol=1e-10)
    assert math.isclose(bell_probabilities[1], 0.0, abs_tol=1e-10)
    assert math.isclose(bell_probabilities[2], 0.0, abs_tol=1e-10)

    phase_circuit = (
        QuantumCircuit(1)
        .h(0)
        .phase(0, math.pi)
        .h(0)
    )
    phase_state = statevector_simulate(phase_circuit)
    assert math.isclose(abs(phase_state[1]) ** 2, 1.0, abs_tol=1e-10)

    ghz = statevector_simulate(ghz_circuit(3))
    ghz_probabilities = probabilities_from_state(ghz)
    assert math.isclose(ghz_probabilities[0], 0.5, abs_tol=1e-10)
    assert math.isclose(ghz_probabilities[7], 0.5, abs_tol=1e-10)

    assert total_variation_distance({"0": 1.0}, {"0": 1.0}) == 0.0
    print("All internal correctness checks passed.")


def main() -> None:
    print("QUANTUM SIMULATORS: STATEVECTOR AND SHOT-BASED SIMULATION")
    run_self_tests()
    demonstrate_single_qubit_measurement()
    demonstrate_bell_entanglement()
    demonstrate_shot_convergence()
    demonstrate_phase_and_interference()
    demonstrate_ghz_state()
    demonstrate_state_validation()
    demonstrate_scaling()
    demonstrate_benchmark()


if __name__ == "__main__":
    main()
