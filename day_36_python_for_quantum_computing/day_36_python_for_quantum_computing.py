"""
Python for Quantum Computing: Python Fundamentals and NumPy

A self-contained progression from Python fundamentals into numerical
simulation of small quantum systems using NumPy.

The implementation uses only Python's standard library and NumPy.
No quantum-computing framework is required.

The simulator demonstrates:
- Python data structures and functions used for quantum state modeling
- Complex-valued NumPy arrays
- Dirac-ket state vectors
- Normalization and validation
- Single-qubit gates
- Multi-qubit tensor products
- Measurement probabilities and sampling
- Bloch-vector calculations
- Expectation values
- Entanglement through Bell states
- Quantum circuit simulation
- Matrix composition
- Numerical precision and failure conditions
- A small variational-style energy calculation
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt
from typing import Callable, Iterable, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Basic Python utilities used throughout the quantum simulator
# ---------------------------------------------------------------------------

TOLERANCE = 1e-10


def heading(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def format_complex(value: complex) -> str:
    """Format a complex amplitude without unnecessary zero components."""
    real = 0.0 if abs(value.real) < TOLERANCE else value.real
    imag = 0.0 if abs(value.imag) < TOLERANCE else value.imag

    if abs(imag) < TOLERANCE:
        return f"{real:.6f}"

    if abs(real) < TOLERANCE:
        return f"{imag:.6f}j"

    sign = "+" if imag >= 0 else "-"
    return f"{real:.6f} {sign} {abs(imag):.6f}j"


def format_state(state: np.ndarray, precision: int = 4) -> str:
    """Render a state vector in computational-basis notation."""
    n = number_of_qubits(state)
    terms = []

    for index, amplitude in enumerate(state):
        if abs(amplitude) > TOLERANCE:
            basis = format(index, f"0{n}b")
            terms.append(
                f"({format_complex(complex(amplitude))})|{basis}>"
            )

    return " + ".join(terms) if terms else "0"


def number_of_qubits(state: np.ndarray) -> int:
    """Return the number of qubits represented by a state vector."""
    size = len(state)

    if size == 0 or size & (size - 1):
        raise ValueError("A quantum state vector must have 2^n amplitudes.")

    return int(np.log2(size))


def validate_state(state: np.ndarray) -> np.ndarray:
    """
    Validate a state vector.

    Quantum state vectors must have:
    - one dimension
    - a length that is a power of two
    - finite complex amplitudes
    - unit norm
    """
    state = np.asarray(state, dtype=np.complex128)

    if state.ndim != 1:
        raise ValueError("Quantum states must be one-dimensional vectors.")

    if len(state) == 0 or len(state) & (len(state) - 1):
        raise ValueError("Quantum state length must be a power of two.")

    if not np.all(np.isfinite(state.real)) or not np.all(np.isfinite(state.imag)):
        raise ValueError("Quantum states cannot contain NaN or infinity.")

    norm = np.linalg.norm(state)

    if not np.isclose(norm, 1.0, atol=TOLERANCE):
        raise ValueError(f"State is not normalized. Norm={norm}")

    return state


def normalize(vector: Iterable[complex]) -> np.ndarray:
    """Return a normalized complex vector."""
    array = np.asarray(list(vector), dtype=np.complex128)
    norm = np.linalg.norm(array)

    if norm < TOLERANCE:
        raise ValueError("Cannot normalize the zero vector.")

    return array / norm


# ---------------------------------------------------------------------------
# NumPy representations of quantum states
# ---------------------------------------------------------------------------

ZERO = np.array([1, 0], dtype=np.complex128)
ONE = np.array([0, 1], dtype=np.complex128)

PLUS = normalize([1, 1])
MINUS = normalize([1, -1])

I2 = np.eye(2, dtype=np.complex128)

X = np.array(
    [
        [0, 1],
        [1, 0],
    ],
    dtype=np.complex128,
)

Y = np.array(
    [
        [0, -1j],
        [1j, 0],
    ],
    dtype=np.complex128,
)

Z = np.array(
    [
        [1, 0],
        [0, -1],
    ],
    dtype=np.complex128,
)

H = (1 / sqrt(2)) * np.array(
    [
        [1, 1],
        [1, -1],
    ],
    dtype=np.complex128,
)

S = np.array(
    [
        [1, 0],
        [0, 1j],
    ],
    dtype=np.complex128,
)


def kron(*matrices: np.ndarray) -> np.ndarray:
    """Compute a tensor/Kronecker product from left to right."""
    result = np.array([[1]], dtype=np.complex128)

    for matrix in matrices:
        result = np.kron(result, matrix)

    return result


def basis_state(bits: str) -> np.ndarray:
    """
    Construct a computational-basis state.

    Example:
        basis_state("101") -> |101>
    """
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("Basis labels must contain only 0 and 1.")

    dimension = 2 ** len(bits)
    vector = np.zeros(dimension, dtype=np.complex128)
    vector[int(bits, 2)] = 1.0
    return vector


# ---------------------------------------------------------------------------
# Measurement and probability calculations
# ---------------------------------------------------------------------------

def probabilities(state: np.ndarray) -> np.ndarray:
    """Calculate computational-basis measurement probabilities."""
    state = validate_state(state)
    return np.abs(state) ** 2


def sample_measurements(
    state: np.ndarray,
    shots: int = 1000,
    seed: int | None = 42,
) -> dict[str, int]:
    """
    Sample computational-basis measurement outcomes.

    Measurement destroys the coherent state in a physical experiment.
    This function therefore returns classical counts rather than a new
    post-measurement quantum state.
    """
    if shots <= 0:
        raise ValueError("shots must be positive.")

    state = validate_state(state)
    qubits = number_of_qubits(state)
    probability = probabilities(state)

    rng = np.random.default_rng(seed)
    outcomes = rng.choice(len(state), size=shots, p=probability)

    counts: dict[str, int] = {}

    for outcome in outcomes:
        bitstring = format(int(outcome), f"0{qubits}b")
        counts[bitstring] = counts.get(bitstring, 0) + 1

    return dict(sorted(counts.items()))


# ---------------------------------------------------------------------------
# Expectation values and Bloch-sphere quantities
# ---------------------------------------------------------------------------

def expectation_value(
    state: np.ndarray,
    operator: np.ndarray,
) -> complex:
    """
    Compute <psi|A|psi>.

    The conjugate transpose is required because quantum amplitudes
    are complex-valued.
    """
    state = validate_state(state)
    operator = np.asarray(operator, dtype=np.complex128)

    dimension = len(state)

    if operator.shape != (dimension, dimension):
        raise ValueError("Operator dimension does not match state dimension.")

    return np.vdot(state, operator @ state)


def bloch_vector(state: np.ndarray) -> tuple[float, float, float]:
    """
    Calculate the Bloch vector of a single-qubit pure state.

    x = <X>
    y = <Y>
    z = <Z>
    """
    if len(state) != 2:
        raise ValueError("A Bloch vector requires exactly one qubit.")

    values = (
        expectation_value(state, X),
        expectation_value(state, Y),
        expectation_value(state, Z),
    )

    return tuple(float(np.real_if_close(value)) for value in values)


# ---------------------------------------------------------------------------
# Gate application
# ---------------------------------------------------------------------------

def apply_gate(
    state: np.ndarray,
    gate: np.ndarray,
) -> np.ndarray:
    """Apply a full-system unitary operator to a state."""
    state = validate_state(state)
    gate = np.asarray(gate, dtype=np.complex128)

    if gate.shape != (len(state), len(state)):
        raise ValueError("Gate dimensions do not match the state.")

    result = gate @ state
    norm = np.linalg.norm(result)

    if not np.isclose(norm, 1.0, atol=1e-9):
        raise ValueError("Gate application produced a non-normalized state.")

    return result


def apply_single_qubit_gate(
    state: np.ndarray,
    gate: np.ndarray,
    target: int,
) -> np.ndarray:
    """
    Apply a one-qubit gate to a multi-qubit state.

    Qubit indexing follows the conventional circuit convention:
    target 0 is the leftmost/high-order qubit in the displayed bitstring.
    """
    state = validate_state(state)
    qubits = number_of_qubits(state)

    if gate.shape != (2, 2):
        raise ValueError("A single-qubit gate must be a 2x2 matrix.")

    if not 0 <= target < qubits:
        raise IndexError("Target qubit is outside the circuit.")

    operators = [
        gate if position == target else I2
        for position in range(qubits)
    ]

    return apply_gate(state, kron(*operators))


# ---------------------------------------------------------------------------
# Controlled operations
# ---------------------------------------------------------------------------

def controlled_gate(
    gate: np.ndarray,
    control: int,
    target: int,
    qubits: int,
) -> np.ndarray:
    """
    Build a controlled single-qubit gate.

    The operation applies `gate` only when the control qubit is |1>.
    """
    if gate.shape != (2, 2):
        raise ValueError("Controlled operations require a 2x2 target gate.")

    if control == target:
        raise ValueError("Control and target qubits must differ.")

    if not 0 <= control < qubits or not 0 <= target < qubits:
        raise IndexError("Control or target qubit is outside the circuit.")

    dimension = 2**qubits
    operation = np.zeros((dimension, dimension), dtype=np.complex128)

    for column in range(dimension):
        bits = format(column, f"0{qubits}b")

        if bits[control] == "1":
            target_bit = int(bits[target])

            for output_target_bit in range(2):
                output_bits = list(bits)
                output_bits[target] = str(output_target_bit)
                row = int("".join(output_bits), 2)

                operation[row, column] = gate[
                    output_target_bit,
                    target_bit,
                ]
        else:
            operation[column, column] = 1.0

    return operation


CNOT = controlled_gate(X, control=0, target=1, qubits=2)


# ---------------------------------------------------------------------------
# Quantum circuit abstraction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateOperation:
    """Immutable record describing one circuit operation."""
    name: str
    matrix: np.ndarray


class QuantumCircuit:
    """
    Small educational state-vector quantum circuit.

    The simulator stores the full 2^n-dimensional state vector. This is
    excellent for learning and small simulations but scales exponentially
    with the number of qubits.
    """

    def __init__(self, qubits: int):
        if qubits <= 0:
            raise ValueError("A circuit must contain at least one qubit.")

        if qubits > 20:
            raise ValueError(
                "This educational state-vector simulator limits circuits "
                "to 20 qubits to avoid accidental large allocations."
            )

        self.qubits = qubits
        self.state = basis_state("0" * qubits)
        self.operations: list[GateOperation] = []

    def apply(self, name: str, matrix: np.ndarray) -> None:
        """Apply a complete-system matrix."""
        self.state = apply_gate(self.state, matrix)
        self.operations.append(GateOperation(name, matrix))

    def h(self, target: int) -> None:
        """Apply a Hadamard gate."""
        self.state = apply_single_qubit_gate(self.state, H, target)
        self.operations.append(GateOperation(f"H q{target}", H))

    def x(self, target: int) -> None:
        """Apply a Pauli-X gate."""
        self.state = apply_single_qubit_gate(self.state, X, target)
        self.operations.append(GateOperation(f"X q{target}", X))

    def y(self, target: int) -> None:
        """Apply a Pauli-Y gate."""
        self.state = apply_single_qubit_gate(self.state, Y, target)
        self.operations.append(GateOperation(f"Y q{target}", Y))

    def z(self, target: int) -> None:
        """Apply a Pauli-Z gate."""
        self.state = apply_single_qubit_gate(self.state, Z, target)
        self.operations.append(GateOperation(f"Z q{target}", Z))

    def s(self, target: int) -> None:
        """Apply a phase gate."""
        self.state = apply_single_qubit_gate(self.state, S, target)
        self.operations.append(GateOperation(f"S q{target}", S))

    def cnot(self, control: int, target: int) -> None:
        """Apply a controlled-NOT operation."""
        operation = controlled_gate(
            X,
            control=control,
            target=target,
            qubits=self.qubits,
        )

        self.state = apply_gate(self.state, operation)
        self.operations.append(
            GateOperation(f"CNOT q{control}->q{target}", operation)
        )

    def measure(self, shots: int = 1000, seed: int | None = 42) -> dict[str, int]:
        """Sample computational-basis measurements."""
        return sample_measurements(self.state, shots, seed)

    def describe(self) -> None:
        """Print circuit operations and current state."""
        print("Circuit operations:")
        for operation in self.operations:
            print(f"  {operation.name}")

        print(f"State: {format_state(self.state)}")


# ---------------------------------------------------------------------------
# Bell-state construction
# ---------------------------------------------------------------------------

def create_bell_state() -> np.ndarray:
    """
    Construct |Phi+> = (|00> + |11>) / sqrt(2).

    H on the first qubit creates superposition. CNOT correlates the
    second qubit with the first.
    """
    state = basis_state("00")
    state = apply_single_qubit_gate(state, H, target=0)
    state = apply_gate(state, CNOT)
    return state


def reduced_single_qubit_probabilities(
    bell_state: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract computational-basis probabilities for each qubit.

    For |Phi+>, each individual qubit is locally random even though
    the pair has perfectly correlated computational-basis outcomes.
    """
    probabilities_2q = probabilities(bell_state)

    first = np.array(
        [
            probabilities_2q[0] + probabilities_2q[1],
            probabilities_2q[2] + probabilities_2q[3],
        ]
    )

    second = np.array(
        [
            probabilities_2q[0] + probabilities_2q[2],
            probabilities_2q[1] + probabilities_2q[3],
        ]
    )

    return first, second


# ---------------------------------------------------------------------------
# A small variational-style numerical example
# ---------------------------------------------------------------------------

def ry(theta: float) -> np.ndarray:
    """Construct the real Y-rotation matrix RY(theta)."""
    half = theta / 2

    return np.array(
        [
            [np.cos(half), -np.sin(half)],
            [np.sin(half), np.cos(half)],
        ],
        dtype=np.complex128,
    )


def single_qubit_energy(theta: float) -> float:
    """
    Evaluate <psi(theta)|Z|psi(theta)> for |psi> = RY(theta)|0>.

    This is a minimal example of the numerical objective used in
    variational quantum algorithms.
    """
    state = apply_gate(basis_state("0"), ry(theta))
    return float(np.real(expectation_value(state, Z)))


def find_lowest_energy(
    objective: Callable[[float], float],
    start: float,
    stop: float,
    samples: int = 1001,
) -> tuple[float, float]:
    """
    Perform a simple grid search.

    It is deliberately transparent rather than using an optimizer package.
    """
    if samples < 2:
        raise ValueError("At least two grid points are required.")

    angles = np.linspace(start, stop, samples)
    energies = np.array([objective(float(angle)) for angle in angles])

    index = int(np.argmin(energies))
    return float(angles[index]), float(energies[index])


# ---------------------------------------------------------------------------
# Validation and numerical edge cases
# ---------------------------------------------------------------------------

def demonstrate_validation() -> None:
    """Show how invalid quantum states are rejected."""
    invalid_states = [
        np.array([1, 1], dtype=np.complex128),
        np.array([1, 0, 0], dtype=np.complex128),
        np.array([np.nan, 0], dtype=np.complex128),
    ]

    for invalid in invalid_states:
        try:
            validate_state(invalid)
        except ValueError as error:
            print(f"Rejected invalid state: {error}")


def verify_unitarity(matrix: np.ndarray) -> bool:
    """Check U†U = I within floating-point tolerance."""
    matrix = np.asarray(matrix, dtype=np.complex128)

    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        return False

    identity = np.eye(matrix.shape[0], dtype=np.complex128)
    return bool(
        np.allclose(
            matrix.conj().T @ matrix,
            identity,
            atol=TOLERANCE,
        )
    )


# ---------------------------------------------------------------------------
# Main executable demonstration
# ---------------------------------------------------------------------------

def main() -> None:
    heading("Python and NumPy Foundations for Quantum Computing")

    print("Python lists represent ordinary collections:")
    classical_bits = [0, 1, 0, 1]
    print(f"Classical bits: {classical_bits}")

    print("\nNumPy arrays represent numerical vectors:")
    classical_vector = np.array([1.0, 2.0, 3.0])
    print(f"Vector: {classical_vector}")
    print(f"Vector dot product with itself: {classical_vector @ classical_vector}")

    heading("Complex Amplitudes")

    state = normalize([1, 1j])
    print(f"Normalized state: {format_state(state)}")
    print(f"Norm: {np.linalg.norm(state):.6f}")
    print(f"Probabilities: {probabilities(state)}")

    heading("Computational Basis")

    zero = basis_state("0")
    one = basis_state("1")
    two_qubit_state = basis_state("10")

    print(f"|0>: {format_state(zero)}")
    print(f"|1>: {format_state(one)}")
    print(f"|10>: {format_state(two_qubit_state)}")

    heading("Quantum Gates")

    for name, gate in {
        "X": X,
        "Y": Y,
        "Z": Z,
        "H": H,
        "S": S,
    }.items():
        print(f"{name} is unitary: {verify_unitarity(gate)}")

    print(f"X|0> = {format_state(apply_gate(zero, X))}")
    print(f"H|0> = {format_state(apply_gate(zero, H))}")
    print(f"Z|+> = {format_state(apply_gate(PLUS, Z))}")

    heading("Measurement")

    measured_state = apply_gate(zero, H)
    print(f"State before measurement: {format_state(measured_state)}")
    print(f"Theoretical probabilities: {probabilities(measured_state)}")
    print(f"1000-shot sample: {sample_measurements(measured_state, 1000, 7)}")

    heading("Bloch Vector")

    for name, state_to_examine in {
        "|0>": ZERO,
        "|1>": ONE,
        "|+>": PLUS,
        "|->": MINUS,
    }.items():
        print(f"{name}: {bloch_vector(state_to_examine)}")

    heading("Expectation Values")

    for state_name, state_to_examine in {
        "|0>": ZERO,
        "|1>": ONE,
        "|+>": PLUS,
        "|->": MINUS,
    }.items():
        print(
            f"{state_name}: "
            f"<X>={expectation_value(state_to_examine, X):.3f}, "
            f"<Z>={expectation_value(state_to_examine, Z):.3f}"
        )

    heading("Tensor Products and Two-Qubit States")

    plus_zero = kron(PLUS, ZERO)
    print(f"|+>|0>: {format_state(plus_zero)}")
    print(f"Measurement probabilities: {probabilities(plus_zero)}")

    heading("Bell State and Entanglement")

    bell = create_bell_state()
    print(f"Bell state: {format_state(bell)}")
    print(f"Bell probabilities: {probabilities(bell)}")
    print(f"Bell measurements: {sample_measurements(bell, 1000, 19)}")

    first_probabilities, second_probabilities = reduced_single_qubit_probabilities(
        bell
    )
    print(f"First qubit local probabilities: {first_probabilities}")
    print(f"Second qubit local probabilities: {second_probabilities}")

    heading("Quantum Circuit Abstraction")

    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cnot(0, 1)
    circuit.describe()
    print(f"Measured circuit: {circuit.measure(1000, 23)}")

    heading("Variational Numerical Calculation")

    sample_angles = np.linspace(0, 2 * np.pi, 9)

    for angle in sample_angles:
        energy = single_qubit_energy(float(angle))
        print(f"theta={angle:.4f}, energy={energy:.6f}")

    best_angle, best_energy = find_lowest_energy(
        single_qubit_energy,
        start=0,
        stop=2 * np.pi,
        samples=1001,
    )

    print(f"Lowest sampled energy: {best_energy:.6f}")
    print(f"Angle producing it: {best_angle:.6f}")

    heading("Validation and Failure Conditions")
    demonstrate_validation()

    heading("State-Vector Scaling")

    for qubits in range(1, 11):
        amplitudes = 2**qubits
        bytes_required = amplitudes * np.dtype(np.complex128).itemsize
        mib = bytes_required / (1024**2)

        print(
            f"{qubits:2d} qubits -> "
            f"{amplitudes:5d} amplitudes -> "
            f"{mib:.4f} MiB for the state vector"
        )

    print(
        "\nThe exponential state-space size is the central scalability "
        "limitation of this educational simulator."
    )


if __name__ == "__main__":
    main()
