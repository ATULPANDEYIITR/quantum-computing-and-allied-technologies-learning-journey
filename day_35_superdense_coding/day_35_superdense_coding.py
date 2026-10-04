"""
Superdense Coding: a self-contained quantum communication simulator.

This program builds the protocol from classical bit communication through
Bell-state preparation, Alice's encoding, quantum transmission, and Bob's
Bell-basis measurement.

The implementation uses state vectors and matrices directly, so it does not
require an external quantum-computing package.

Convention:
    Qubit order is (q0, q1).
    Basis ordering is |00>, |01>, |10>, |11>.
    Alice owns q0 and Bob owns q1.

Protocol:
    1. Alice and Bob share an entangled Bell pair.
    2. Alice encodes two classical bits using one of I, X, Z, or XZ.
    3. Alice sends her single qubit to Bob.
    4. Bob applies a Bell-basis decoding circuit.
    5. Bob measures two qubits and recovers the two classical bits.

A noiseless run can communicate two classical bits by transmitting one
physical qubit after the entanglement has already been shared.

This is a simulation of quantum mechanics, not a physical quantum network.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


Complex = complex
Vector = List[Complex]
Matrix = List[List[Complex]]


def print_heading(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def fmt_complex(value: complex, precision: int = 4) -> str:
    real = 0.0 if abs(value.real) < 10 ** (-precision) else value.real
    imag = 0.0 if abs(value.imag) < 10 ** (-precision) else value.imag

    if imag == 0:
        return f"{real:.{precision}f}"
    if real == 0:
        return f"{imag:.{precision}f}i"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.{precision}f} {sign} {abs(imag):.{precision}f}i"


def normalize(state: Vector) -> Vector:
    norm = math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))
    if norm == 0:
        raise ValueError("A quantum state cannot have zero norm.")
    return [amplitude / norm for amplitude in state]


def vector_norm(state: Vector) -> float:
    return math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def apply_matrix(matrix: Matrix, vector: Vector) -> Vector:
    if len(matrix) != len(vector):
        raise ValueError("Matrix and vector dimensions do not match.")

    result = []
    for row in matrix:
        if len(row) != len(vector):
            raise ValueError("Matrix must be rectangular and square.")
        result.append(sum(row[i] * vector[i] for i in range(len(vector))))
    return result


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    if len(left[0]) != len(right):
        raise ValueError("Matrix dimensions cannot be multiplied.")

    return [
        [
            sum(left[i][k] * right[k][j] for k in range(len(right)))
            for j in range(len(right[0]))
        ]
        for i in range(len(left))
    ]


def tensor_product(left: Matrix, right: Matrix) -> Matrix:
    result: Matrix = []
    for left_row in left:
        for right_row in right:
            row = []
            for left_value in left_row:
                for right_value in right_row:
                    row.append(left_value * right_value)
            result.append(row)
    return result


I: Matrix = [
    [1, 0],
    [0, 1],
]

X: Matrix = [
    [0, 1],
    [1, 0],
]

Z: Matrix = [
    [1, 0],
    [0, -1],
]

H: Matrix = [
    [1 / math.sqrt(2), 1 / math.sqrt(2)],
    [1 / math.sqrt(2), -1 / math.sqrt(2)],
]

CNOT_01: Matrix = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
]

I2: Matrix = tensor_product(I, I)
H0: Matrix = tensor_product(H, I)


def basis_state(bits: str) -> Vector:
    if len(bits) != 2 or any(bit not in "01" for bit in bits):
        raise ValueError("A two-qubit basis state must contain two binary digits.")

    index = int(bits, 2)
    state = [0j] * 4
    state[index] = 1 + 0j
    return state


def probabilities(state: Vector) -> List[float]:
    total = sum(abs(amplitude) ** 2 for amplitude in state)
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError(f"State is not normalized; probability total is {total}.")
    return [abs(amplitude) ** 2 for amplitude in state]


def measure(state: Vector, rng: random.Random | None = None) -> Tuple[int, Vector]:
    rng = rng or random.Random()
    probs = probabilities(state)
    threshold = rng.random()
    cumulative = 0.0

    for index, probability in enumerate(probs):
        cumulative += probability
        if threshold <= cumulative:
            collapsed = [0j] * len(state)
            collapsed[index] = 1 + 0j
            return index, collapsed

    index = len(state) - 1
    collapsed = [0j] * len(state)
    collapsed[index] = 1 + 0j
    return index, collapsed


def pretty_state(state: Vector, labels: Sequence[str]) -> str:
    terms = []
    for amplitude, label in zip(state, labels):
        if abs(amplitude) > 1e-9:
            terms.append(f"({fmt_complex(amplitude)})|{label}>")
    return " + ".join(terms) if terms else "0"


def classical_to_gate_pair(message: str) -> Tuple[Matrix, str]:
    """
    Superdense coding maps:
        00 -> I
        01 -> X
        10 -> Z
        11 -> X followed by Z

    The chosen order of X and Z differs only by a global phase for the
    relevant Bell states, so the measurement result is unchanged.
    """
    mapping = {
        "00": (I, "I"),
        "01": (X, "X"),
        "10": (Z, "Z"),
        "11": (matrix_multiply(Z, X), "ZX"),
    }

    if message not in mapping:
        raise ValueError("Message must be one of 00, 01, 10, or 11.")

    return mapping[message]


def apply_single_qubit_gate(
    state: Vector,
    gate: Matrix,
    qubit: int,
) -> Vector:
    """
    Expand a one-qubit gate to the two-qubit system.

    qubit=0 means Alice's first qubit.
    qubit=1 means Bob's second qubit.
    """
    if qubit == 0:
        full_gate = tensor_product(gate, I)
    elif qubit == 1:
        full_gate = tensor_product(I, gate)
    else:
        raise ValueError("Qubit index must be 0 or 1.")

    return apply_matrix(full_gate, state)


def create_bell_pair() -> Vector:
    """
    Start with |00>, then apply H to q0 and CNOT(q0 -> q1).

    Result:
        (|00> + |11>) / sqrt(2)
    """
    state = basis_state("00")
    state = apply_matrix(H0, state)
    state = apply_matrix(CNOT_01, state)
    return normalize(state)


def alice_encode(state: Vector, message: str) -> Vector:
    gate, _ = classical_to_gate_pair(message)
    return apply_single_qubit_gate(state, gate, qubit=0)


def bob_decode(state: Vector) -> Vector:
    """
    Convert the Bell basis back to the computational basis.

    The inverse of Bell-pair preparation is:
        CNOT(q0 -> q1), followed by H(q0)
    """
    state = apply_matrix(CNOT_01, state)
    state = apply_matrix(H0, state)
    return normalize(state)


@dataclass(frozen=True)
class TransmissionResult:
    message: str
    encoded_state: Vector
    decoded_state: Vector
    measured_bits: str


def run_protocol(message: str, rng: random.Random | None = None) -> TransmissionResult:
    shared = create_bell_pair()
    encoded = alice_encode(shared, message)
    decoded = bob_decode(encoded)
    measured_index, _ = measure(decoded, rng)
    measured_bits = format(measured_index, "02b")

    return TransmissionResult(
        message=message,
        encoded_state=encoded,
        decoded_state=decoded,
        measured_bits=measured_bits,
    )


def demonstrate_bell_states() -> None:
    print_heading("Bell-pair preparation")

    bell = create_bell_pair()

    print("Prepared state:")
    print(pretty_state(bell, ["00", "01", "10", "11"]))

    print("\nProbabilities:")
    for label, probability in zip(["00", "01", "10", "11"], probabilities(bell)):
        print(f"  |{label}>: {probability:.4f}")

    print(
        "\nThe state is entangled: measuring one qubit in the computational "
        "basis determines the corresponding value of the other."
    )


def demonstrate_encoding_table() -> None:
    print_heading("Alice's encoding operations")

    shared = create_bell_pair()

    for message in ("00", "01", "10", "11"):
        _, operation = classical_to_gate_pair(message)
        encoded = alice_encode(shared, message)
        decoded = bob_decode(encoded)

        print(f"\nMessage {message}")
        print(f"  Alice operation: {operation}")
        print(f"  Encoded Bell state: {pretty_state(encoded, ['00', '01', '10', '11'])}")
        print(f"  After Bob's decoding circuit: "
              f"{pretty_state(decoded, ['00', '01', '10', '11'])}")
        print(f"  Decoded probability distribution: "
              f"{[round(p, 4) for p in probabilities(decoded)]}")


def demonstrate_all_messages(trials_per_message: int = 100) -> None:
    print_heading("Repeated noiseless transmissions")

    rng = random.Random(20261005)

    for message in ("00", "01", "10", "11"):
        successes = 0

        for _ in range(trials_per_message):
            result = run_protocol(message, rng)
            if result.measured_bits == message:
                successes += 1

        print(
            f"Message {message}: "
            f"{successes}/{trials_per_message} successful decodings"
        )


def apply_depolarizing_error(
    state: Vector,
    qubit: int,
    error_probability: float,
    rng: random.Random,
) -> Vector:
    """
    A simple Pauli-channel model.

    With probability p, one of X, Y, Z is applied to the transmitted qubit.
    This is not a full physical noise model, but it exposes how channel noise
    changes the ideal protocol.
    """
    if not 0 <= error_probability <= 1:
        raise ValueError("Error probability must be between 0 and 1.")

    if rng.random() >= error_probability:
        return state

    error_gate = rng.choice([
        X,
        Z,
        matrix_multiply(X, Z),
    ])

    return apply_single_qubit_gate(state, error_gate, qubit)


def simulate_noisy_channel(
    error_probability: float,
    trials_per_message: int = 1000,
) -> Dict[str, float]:
    rng = random.Random(42)
    results: Dict[str, float] = {}

    for message in ("00", "01", "10", "11"):
        successes = 0

        for _ in range(trials_per_message):
            shared = create_bell_pair()
            encoded = alice_encode(shared, message)

            # Alice sends q0. The error model acts on that transmitted qubit.
            noisy = apply_depolarizing_error(
                encoded,
                qubit=0,
                error_probability=error_probability,
                rng=rng,
            )

            decoded = bob_decode(noisy)
            measured_index, _ = measure(decoded, rng)

            if format(measured_index, "02b") == message:
                successes += 1

        results[message] = successes / trials_per_message

    return results


def demonstrate_noise() -> None:
    print_heading("Channel-noise simulation")

    for error_probability in (0.00, 0.05, 0.15, 0.30):
        results = simulate_noisy_channel(error_probability, 1000)
        average = sum(results.values()) / len(results)

        print(
            f"Noise probability {error_probability:.2f}: "
            f"average decoding accuracy {average:.3f}"
        )


def demonstrate_capacity_accounting() -> None:
    print_heading("Communication accounting")

    print(
        "A superdense-coding transmission carries four distinguishable logical "
        "messages: 00, 01, 10, and 11."
    )
    print(
        "Four messages require log2(4) = 2 classical bits of information."
    )
    print(
        "Alice physically transmits one qubit during the communication phase."
    )
    print(
        "The protocol does not create two qubits of communication from one "
        "qubit alone: the pre-shared entangled pair is an essential resource."
    )


def demonstrate_failure_conditions() -> None:
    print_heading("Validation and failure conditions")

    invalid_messages = ["0", "000", "2a", "", "01 "]

    for message in invalid_messages:
        try:
            classical_to_gate_pair(message)
        except ValueError as exc:
            print(f"Rejected message {message!r}: {exc}")

    try:
        normalize([0j, 0j])
    except ValueError as exc:
        print(f"Rejected zero state: {exc}")

    try:
        probabilities([1 + 0j, 1 + 0j, 0j, 0j])
    except ValueError as exc:
        print(f"Rejected unnormalized state: {exc}")


def demonstrate_protocol_invariants() -> None:
    print_heading("Quantum-state invariants")

    for message in ("00", "01", "10", "11"):
        shared = create_bell_pair()
        encoded = alice_encode(shared, message)
        decoded = bob_decode(encoded)

        print(
            f"{message}: "
            f"shared norm={vector_norm(shared):.6f}, "
            f"encoded norm={vector_norm(encoded):.6f}, "
            f"decoded norm={vector_norm(decoded):.6f}"
        )

    print(
        "\nUnitary gate operations preserve the norm of a valid quantum state. "
        "A simulator can therefore use normalization checks as useful debugging "
        "invariants."
    )


def main() -> None:
    demonstrate_bell_states()
    demonstrate_encoding_table()
    demonstrate_all_messages()
    demonstrate_noise()
    demonstrate_capacity_accounting()
    demonstrate_failure_conditions()
    demonstrate_protocol_invariants()

    print_heading("Protocol completed")
    print(
        "Superdense coding demonstrates how pre-shared entanglement changes "
        "the information capacity of a transmitted quantum system."
    )


if __name__ == "__main__":
    main()
