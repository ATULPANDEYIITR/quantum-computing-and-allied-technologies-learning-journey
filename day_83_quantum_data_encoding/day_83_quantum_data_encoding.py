"""
QUANTUM DATA ENCODING
Basis Encoding, Angle Encoding, and Amplitude Encoding

A self-contained quantum data encoding simulator using Python's
standard library.

Encoding methods:
1. Basis encoding: maps binary values to computational basis states.
2. Angle encoding: maps numerical values to RY rotation angles.
3. Amplitude encoding: maps normalized numerical vectors to quantum
   state amplitudes.

The simulator includes validation, state-vector construction,
measurement probabilities, sampling, and comparative analysis.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class EncodingError(ValueError):
    """Raised when quantum encoding input is invalid."""


class EncodingType(Enum):
    BASIS = "basis"
    ANGLE = "angle"
    AMPLITUDE = "amplitude"


@dataclass(frozen=True)
class QuantumState:
    encoding: EncodingType
    num_qubits: int
    amplitudes: tuple[complex, ...]
    metadata: dict

    def __post_init__(self):
        expected = 2 ** self.num_qubits

        if len(self.amplitudes) != expected:
            raise EncodingError("State dimension does not match qubit count.")

        if self.num_qubits < 0:
            raise EncodingError("Qubit count cannot be negative.")

        norm = sum(abs(a) ** 2 for a in self.amplitudes)

        if not math.isclose(norm, 1.0, abs_tol=1e-9):
            raise EncodingError(f"State is not normalized: norm={norm}")

    def probabilities(self) -> list[float]:
        return [abs(a) ** 2 for a in self.amplitudes]

    def probability(self, basis_index: int) -> float:
        if not 0 <= basis_index < len(self.amplitudes):
            raise EncodingError("Basis index is out of range.")

        return abs(self.amplitudes[basis_index]) ** 2

    def measure(self, shots: int = 1000, seed: int | None = None):
        if shots <= 0:
            raise EncodingError("Shots must be positive.")

        rng = random.Random(seed)
        probabilities = self.probabilities()
        outcomes = rng.choices(
            range(len(probabilities)),
            weights=probabilities,
            k=shots
        )

        counts: dict[str, int] = {}

        for outcome in outcomes:
            bitstring = format(outcome, f"0{self.num_qubits}b")
            counts[bitstring] = counts.get(bitstring, 0) + 1

        return counts


class QuantumEncoder:

    @staticmethod
    def _validate_real_vector(values: Sequence[float]) -> list[float]:
        if not values:
            raise EncodingError("Input vector cannot be empty.")

        result = []

        for value in values:
            if isinstance(value, bool):
                raise EncodingError("Boolean values are not accepted.")

            try:
                number = float(value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise EncodingError("Input must contain real numbers.") from exc

            if not math.isfinite(number):
                raise EncodingError("Input contains a non-finite value.")

            result.append(number)

        return result

    @staticmethod
    def required_qubits(dimension: int) -> int:
        if dimension <= 0:
            raise EncodingError("Dimension must be positive.")

        return (dimension - 1).bit_length()

    @classmethod
    def basis_encode(cls, values: Sequence[int]) -> QuantumState:
        """
        Encode binary data into a computational basis state.

        Example:
        [1, 0, 1] -> |101>
        """
        if not values:
            raise EncodingError("At least one bit is required.")

        bits = []

        for bit in values:
            if isinstance(bit, bool):
                bits.append(int(bit))
            elif isinstance(bit, int) and bit in (0, 1):
                bits.append(bit)
            else:
                raise EncodingError("Basis encoding accepts only binary values.")

        index = int("".join(map(str, bits)), 2)
        dimension = 2 ** len(bits)

        amplitudes = [0j] * dimension
        amplitudes[index] = 1 + 0j

        return QuantumState(
            encoding=EncodingType.BASIS,
            num_qubits=len(bits),
            amplitudes=tuple(amplitudes),
            metadata={
                "bitstring": "".join(map(str, bits)),
                "basis_index": index
            }
        )

    @classmethod
    def angle_encode(
        cls,
        values: Sequence[float],
        input_range: tuple[float, float] = (0.0, 1.0)
    ) -> QuantumState:
        """
        Encode each feature using an RY(theta) rotation.

        theta = pi * (x - minimum) / (maximum - minimum)

        Each feature is represented by one qubit.
        """
        features = cls._validate_real_vector(values)

        minimum, maximum = input_range

        if not math.isfinite(minimum) or not math.isfinite(maximum):
            raise EncodingError("Input range must be finite.")

        if maximum <= minimum:
            raise EncodingError("Invalid input range.")

        if any(x < minimum or x > maximum for x in features):
            raise EncodingError("Feature falls outside the specified range.")

        single_qubit_states = []
        angles = []

        for value in features:
            theta = math.pi * (value - minimum) / (maximum - minimum)

            # RY(theta)|0> = cos(theta/2)|0> + sin(theta/2)|1>
            state = (
                complex(math.cos(theta / 2), 0),
                complex(math.sin(theta / 2), 0)
            )

            single_qubit_states.append(state)
            angles.append(theta)

        amplitudes = [1 + 0j]

        # Tensor product constructs the complete multi-qubit state.
        for state in single_qubit_states:
            amplitudes = [
                amplitude * component
                for amplitude in amplitudes
                for component in state
            ]

        return QuantumState(
            encoding=EncodingType.ANGLE,
            num_qubits=len(features),
            amplitudes=tuple(amplitudes),
            metadata={
                "angles_radians": angles,
                "input_range": input_range,
                "features": features
            }
        )

    @classmethod
    def amplitude_encode(
        cls,
        values: Sequence[float]
    ) -> QuantumState:
        """
        Encode a real-valued vector as normalized amplitudes.

        Zero-padding extends the vector to the next power of two.
        The resulting state uses the minimum required qubit count.
        """
        features = cls._validate_real_vector(values)

        norm = math.sqrt(sum(x * x for x in features))

        if norm == 0:
            raise EncodingError(
                "Amplitude encoding requires a non-zero vector."
            )

        normalized = [x / norm for x in features]

        num_qubits = cls.required_qubits(len(features))
        dimension = 2 ** num_qubits

        normalized.extend([0.0] * (dimension - len(normalized)))

        amplitudes = tuple(complex(x, 0) for x in normalized)

        return QuantumState(
            encoding=EncodingType.AMPLITUDE,
            num_qubits=num_qubits,
            amplitudes=amplitudes,
            metadata={
                "original_dimension": len(features),
                "encoded_dimension": dimension,
                "original_norm": norm,
                "normalized_features": tuple(normalized)
            }
        )


def compare_encodings(features: Sequence[float]) -> dict:
    """Compare the three encoding methods where their input domains overlap."""

    values = QuantumEncoder._validate_real_vector(features)

    if any(x not in (0.0, 1.0) for x in values):
        basis_result = "Not applicable: basis encoding requires binary data."
    else:
        basis_result = QuantumEncoder.basis_encode(
            [int(x) for x in values]
        )

    angle_result = QuantumEncoder.angle_encode(values)
    amplitude_result = QuantumEncoder.amplitude_encode(values)

    return {
        "basis": basis_result,
        "angle": angle_result,
        "amplitude": amplitude_result
    }


def print_state(name: str, state: QuantumState):
    print(f"\n{name}")
    print("-" * 55)
    print("Encoding:", state.encoding.value)
    print("Qubits:", state.num_qubits)
    print("Dimension:", len(state.amplitudes))
    print("Metadata:", state.metadata)

    print("Non-zero amplitudes:")

    for index, amplitude in enumerate(state.amplitudes):
        if abs(amplitude) > 1e-10:
            bitstring = format(index, f"0{state.num_qubits}b")
            print(
                f"|{bitstring}> = {amplitude.real:.6f}"
                f" + {amplitude.imag:.6f}i"
            )

    print("Probabilities:", [
        round(p, 6) for p in state.probabilities()
    ])

    print("Measurement:", state.measure(shots=1000, seed=42))


def demonstrate_edge_cases():
    """Verify validation and state construction."""

    invalid_cases = [
        lambda: QuantumEncoder.basis_encode([1, 2, 0]),
        lambda: QuantumEncoder.angle_encode([0.5, 1.5]),
        lambda: QuantumEncoder.amplitude_encode([0, 0, 0]),
        lambda: QuantumEncoder.amplitude_encode([1, float("nan")]),
        lambda: QuantumEncoder.angle_encode([0.5], (1.0, 1.0))
    ]

    for index, operation in enumerate(invalid_cases, start=1):
        try:
            operation()
        except EncodingError as exc:
            print(f"Validation case {index}: {exc}")
        else:
            raise AssertionError(f"Case {index} should have failed.")

    assert QuantumEncoder.required_qubits(1) == 0
    assert QuantumEncoder.required_qubits(3) == 2
    assert QuantumEncoder.required_qubits(8) == 3

    state = QuantumEncoder.amplitude_encode([3, 4])
    assert math.isclose(state.probability(0), 0.36)
    assert math.isclose(state.probability(1), 0.64)

    basis = QuantumEncoder.basis_encode([1, 0, 1])
    assert basis.probability(5) == 1.0

    angle = QuantumEncoder.angle_encode([0.0, 0.5, 1.0])
    assert len(angle.amplitudes) == 8

    print("\nAll validation assertions passed.")


def main():
    print("=" * 65)
    print("QUANTUM DATA ENCODING SIMULATOR")
    print("=" * 65)

    binary_data = [1, 0, 1, 1]
    numerical_data = [0.2, 0.5, 0.8]
    vector_data = [3, 4, 0]

    basis = QuantumEncoder.basis_encode(binary_data)
    angle = QuantumEncoder.angle_encode(numerical_data)
    amplitude = QuantumEncoder.amplitude_encode(vector_data)

    print_state("1. BASIS ENCODING", basis)
    print_state("2. ANGLE ENCODING", angle)
    print_state("3. AMPLITUDE ENCODING", amplitude)

    print("\nENCODING RESOURCE COMPARISON")
    print("-" * 55)

    for name, state in [
        ("Basis", basis),
        ("Angle", angle),
        ("Amplitude", amplitude)
    ]:
        print(
            f"{name:12} | Qubits: {state.num_qubits:2} "
            f"| State dimension: {len(state.amplitudes):4}"
        )

    demonstrate_edge_cases()

    print("\nSimulation completed successfully.")


if __name__ == "__main__":
    main()
