#!/usr/bin/env python3
"""State-vector implementations of four quantum algorithms.

Qubit numbering is little-endian: qubit 0 is the least significant bit
of a computational-basis index. State-vector simulation is exact up to
floating-point error; measurement is probabilistic.
"""

from __future__ import annotations

import cmath
import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Callable, Sequence


MAX_STATE_QUBITS = 16
MAX_QPE_COUNTING_QUBITS = 10


class QuantumError(Exception):
    """Base exception for quantum simulation errors."""


class ValidationError(QuantumError):
    """Raised when a circuit or algorithm configuration is invalid."""


@dataclass(frozen=True)
class ExperimentResult:
    algorithm: str
    measurement: str
    interpretation: str
    success_probability: float
    details: dict[str, object]


class StateVector:
    """Dense state-vector simulator using complex probability amplitudes."""

    def __init__(self, qubits: int, initial_basis: int = 0) -> None:
        if not isinstance(qubits, int) or not 1 <= qubits <= MAX_STATE_QUBITS:
            raise ValidationError(
                f"Qubit count must be between 1 and {MAX_STATE_QUBITS}."
            )

        self.qubits = qubits
        self.dimension = 1 << qubits

        if not isinstance(initial_basis, int) or not 0 <= initial_basis < self.dimension:
            raise ValidationError("Initial basis state is outside the register.")

        self.amplitudes = [0j] * self.dimension
        self.amplitudes[initial_basis] = 1 + 0j

    def _validate_qubit(self, qubit: int) -> None:
        if not isinstance(qubit, int) or not 0 <= qubit < self.qubits:
            raise ValidationError(f"Invalid qubit index: {qubit!r}.")

    def apply_hadamard(self, qubit: int) -> None:
        """Apply H to one qubit in O(2^n) time."""
        self._validate_qubit(qubit)
        stride = 1 << qubit
        scale = 1 / math.sqrt(2)

        for block_start in range(0, self.dimension, stride << 1):
            for offset in range(stride):
                left = block_start + offset
                right = left + stride
                a = self.amplitudes[left]
                b = self.amplitudes[right]
                self.amplitudes[left] = (a + b) * scale
                self.amplitudes[right] = (a - b) * scale

    def apply_phase_oracle(self, predicate: Callable[[int], bool]) -> None:
        """Apply a phase flip to basis states satisfying predicate."""
        for basis in range(self.dimension):
            if predicate(basis):
                self.amplitudes[basis] *= -1

    def apply_controlled_phase(
        self, control: int, target: int, angle: float
    ) -> None:
        """Apply a controlled phase rotation to |11> on two distinct qubits."""
        self._validate_qubit(control)
        self._validate_qubit(target)

        if control == target:
            raise ValidationError("Control and target qubits must be different.")
        if not math.isfinite(angle):
            raise ValidationError("Phase angle must be finite.")

        control_mask = 1 << control
        target_mask = 1 << target
        phase = cmath.exp(1j * math.remainder(angle, 2 * math.pi))

        for basis in range(self.dimension):
            if basis & control_mask and basis & target_mask:
                self.amplitudes[basis] *= phase

    def diffuse(self) -> None:
        """Apply Grover diffusion: 2|s><s| - I."""
        mean_amplitude = sum(self.amplitudes) / self.dimension
        self.amplitudes = [
            2 * mean_amplitude - amplitude
            for amplitude in self.amplitudes
        ]

    def inverse_qft_on_low_register(self, register_qubits: int) -> None:
        """Apply an exact inverse QFT to the low-order register.

        This direct matrix implementation costs O(4^m) per block, where
        m is the number of transformed qubits. It is suitable for small
        phase-estimation examples, not large quantum registers.
        """
        if not 1 <= register_qubits <= self.qubits:
            raise ValidationError("Invalid inverse-QFT register size.")

        dimension = 1 << register_qubits
        scale = 1 / math.sqrt(dimension)
        angle_scale = -2 * math.pi / dimension

        for block_start in range(0, self.dimension, dimension):
            source = self.amplitudes[block_start:block_start + dimension]
            transformed = [0j] * dimension

            for output_index in range(dimension):
                total = 0j
                for input_index, amplitude in enumerate(source):
                    angle = angle_scale * input_index * output_index
                    total += amplitude * cmath.exp(1j * angle)
                transformed[output_index] = total * scale

            self.amplitudes[block_start:block_start + dimension] = transformed

    def probabilities(self) -> list[float]:
        return [abs(amplitude) ** 2 for amplitude in self.amplitudes]

    def marginal_probabilities(self, low_register_qubits: int) -> list[float]:
        """Return probabilities for the low-order register only."""
        if not 1 <= low_register_qubits <= self.qubits:
            raise ValidationError("Invalid measurement-register size.")

        register_size = 1 << low_register_qubits
        mask = register_size - 1
        marginal = [0.0] * register_size

        for basis, amplitude in enumerate(self.amplitudes):
            marginal[basis & mask] += abs(amplitude) ** 2

        return marginal

    def sample(self, rng: random.Random) -> int:
        return rng.choices(
            range(self.dimension),
            weights=self.probabilities(),
            k=1,
        )[0]

    def sample_low_register(
        self, register_qubits: int, rng: random.Random
    ) -> int:
        probabilities = self.marginal_probabilities(register_qubits)
        return rng.choices(
            range(len(probabilities)),
            weights=probabilities,
            k=1,
        )[0]


def format_bits(value: int, width: int) -> str:
    if width < 1 or not 0 <= value < (1 << width):
        raise ValidationError("Cannot format an invalid bit register.")
    return format(value, f"0{width}b")


def parse_bits(bits: str) -> int:
    if not isinstance(bits, str) or not bits or any(bit not in "01" for bit in bits):
        raise ValidationError("A bit string must contain one or more binary digits.")
    return int(bits, 2)


def run_deutsch_jozsa(
    qubits: int,
    oracle_type: str,
    rng: random.Random,
    balanced_mask: int = 1,
) -> ExperimentResult:
    """Distinguish a constant Boolean oracle from a balanced oracle."""
    state = StateVector(qubits)
    dimension = state.dimension

    if oracle_type not in {
        "constant-zero",
        "constant-one",
        "balanced-parity",
    }:
        raise ValidationError("Unsupported Deutsch-Jozsa oracle type.")

    if oracle_type == "balanced-parity":
        if not isinstance(balanced_mask, int) or not 0 < balanced_mask < dimension:
            raise ValidationError("Balanced parity mask must be nonzero and fit the register.")

    for qubit in range(qubits):
        state.apply_hadamard(qubit)

    if oracle_type == "constant-one":
        state.apply_phase_oracle(lambda _: True)
    elif oracle_type == "balanced-parity":
        state.apply_phase_oracle(
            lambda basis: (basis & balanced_mask).bit_count() % 2 == 1
        )

    for qubit in range(qubits):
        state.apply_hadamard(qubit)

    measurement = state.sample(rng)
    measured_bits = format_bits(measurement, qubits)
    classification = "constant" if measurement == 0 else "balanced"

    return ExperimentResult(
        algorithm="Deutsch-Jozsa",
        measurement=measured_bits,
        interpretation=classification,
        success_probability=1.0,
        details={
            "oracle_type": oracle_type,
            "balanced_mask": balanced_mask if oracle_type == "balanced-parity" else None,
            "basis_index": measurement,
        },
    )


def run_bernstein_vazirani(
    secret: str, rng: random.Random
) -> ExperimentResult:
    """Recover a hidden bit string with one phase-oracle query."""
    secret_value = parse_bits(secret)
    qubits = len(secret)

    state = StateVector(qubits)
    for qubit in range(qubits):
        state.apply_hadamard(qubit)

    state.apply_phase_oracle(
        lambda basis: (basis & secret_value).bit_count() % 2 == 1
    )

    for qubit in range(qubits):
        state.apply_hadamard(qubit)

    measurement = state.sample(rng)
    measured_bits = format_bits(measurement, qubits)

    return ExperimentResult(
        algorithm="Bernstein-Vazirani",
        measurement=measured_bits,
        interpretation=(
            "secret recovered" if measured_bits == secret else "measurement mismatch"
        ),
        success_probability=1.0,
        details={
            "secret": secret,
            "oracle_queries": 1,
            "basis_index": measurement,
        },
    )


def optimal_grover_iterations(qubits: int, marked_count: int) -> int:
    """Choose an iteration count near the first amplitude maximum."""
    dimension = 1 << qubits

    if not 1 <= marked_count <= dimension:
        raise ValidationError("At least one valid marked state is required.")

    theta = math.asin(math.sqrt(marked_count / dimension))
    return max(0, math.floor(math.pi / (4 * theta) - 0.5))


def run_grover(
    qubits: int,
    marked_states: Sequence[int],
    rng: random.Random,
) -> ExperimentResult:
    """Search an unstructured basis-state space using amplitude amplification."""
    dimension = 1 << qubits

    if not marked_states:
        raise ValidationError("Grover search requires at least one marked state.")

    marked = set(marked_states)
    if len(marked) != len(marked_states):
        raise ValidationError("Marked states must not contain duplicates.")
    if any(not isinstance(value, int) or not 0 <= value < dimension for value in marked):
        raise ValidationError("A marked state is outside the search space.")

    state = StateVector(qubits)
    for qubit in range(qubits):
        state.apply_hadamard(qubit)

    iterations = optimal_grover_iterations(qubits, len(marked))

    for _ in range(iterations):
        state.apply_phase_oracle(lambda basis: basis in marked)
        state.diffuse()

    probabilities = state.probabilities()
    success_probability = sum(
        probability
        for basis, probability in enumerate(probabilities)
        if basis in marked
    )

    measurement = state.sample(rng)
    measured_bits = format_bits(measurement, qubits)

    return ExperimentResult(
        algorithm="Grover",
        measurement=measured_bits,
        interpretation=(
            "marked state found" if measurement in marked else "unmarked state measured"
        ),
        success_probability=success_probability,
        details={
            "marked_states": sorted(marked),
            "marked_count": len(marked),
            "search_space_size": dimension,
            "iterations": iterations,
        },
    )


def run_phase_estimation(
    phase: float,
    counting_qubits: int,
    rng: random.Random,
) -> ExperimentResult:
    """Estimate the eigenphase of U = diag(1, exp(2*pi*i*phase)).

    The target qubit is prepared in |1>, an eigenstate with eigenvalue
    exp(2*pi*i*phase). The low-order counting register is measured.
    """
    if not math.isfinite(phase) or not 0 <= phase < 1:
        raise ValidationError("Phase must be finite and lie in [0, 1).")
    if not 1 <= counting_qubits <= MAX_QPE_COUNTING_QUBITS:
        raise ValidationError(
            f"Counting register must contain 1 to {MAX_QPE_COUNTING_QUBITS} qubits."
        )

    target_qubit = counting_qubits
    state = StateVector(counting_qubits + 1, initial_basis=1 << target_qubit)

    for qubit in range(counting_qubits):
        state.apply_hadamard(qubit)

    # Controlled-U^(2^j) applies the eigenvalue phase 2^j times.
    for control_qubit in range(counting_qubits):
        angle = 2 * math.pi * phase * (1 << control_qubit)
        state.apply_controlled_phase(control_qubit, target_qubit, angle)

    state.inverse_qft_on_low_register(counting_qubits)

    measurement = state.sample_low_register(counting_qubits, rng)
    measured_bits = format_bits(measurement, counting_qubits)
    estimated_phase = measurement / (1 << counting_qubits)

    return ExperimentResult(
        algorithm="Quantum Phase Estimation",
        measurement=measured_bits,
        interpretation=f"estimated eigenphase {estimated_phase:.6f}",
        success_probability=1.0,
        details={
            "input_phase": phase,
            "estimated_phase": estimated_phase,
            "absolute_phase_error": abs(phase - estimated_phase),
            "counting_qubits": counting_qubits,
        },
    )


def run_self_tests() -> None:
    """Check deterministic algorithm properties and invalid configurations."""
    rng = random.Random(20261030)

    assert run_deutsch_jozsa(3, "constant-zero", rng).measurement == "000"
    assert run_deutsch_jozsa(3, "constant-one", rng).measurement == "000"
    assert run_deutsch_jozsa(3, "balanced-parity", rng).measurement != "000"
    assert run_bernstein_vazirani("1011", rng).measurement == "1011"

    grover = run_grover(3, [5], rng)
    assert grover.success_probability > 0.75

    qpe = run_phase_estimation(5 / 16, 4, rng)
    assert qpe.measurement == "0101"

    try:
        run_grover(3, [], rng)
    except ValidationError:
        pass
    else:
        raise AssertionError("Empty Grover target set should be rejected.")

    try:
        run_phase_estimation(1.0, 4, rng)
    except ValidationError:
        pass
    else:
        raise AssertionError("A phase of 1.0 should be rejected.")


def main() -> None:
    rng = random.Random(20261030)
    run_self_tests()

    experiments = [
        run_deutsch_jozsa(3, "balanced-parity", rng),
        run_bernstein_vazirani("1011", rng),
        run_grover(3, [5], rng),
        run_phase_estimation(5 / 16, 4, rng),
    ]

    print(json.dumps(
        [asdict(experiment) for experiment in experiments],
        indent=2,
    ))


if __name__ == "__main__":
    main()
