"""
Tensor Products | Multi-system quantum states

A self-contained study script covering tensor products and multi-system quantum
states from beginner to advanced level.

Requirements:
    Python 3.9+
    NumPy

Install NumPy if necessary:
    pip install numpy

The script uses numerical linear algebra to make the mathematical structure of
multi-system quantum mechanics executable. All demonstrations are deterministic
except where measurement sampling is explicitly requested.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


# =============================================================================
# 1. BASIC NUMERICAL HELPERS
# =============================================================================

TOLERANCE = 1e-10


def clean_complex(value: complex, tolerance: float = TOLERANCE) -> complex:
    """Remove tiny numerical real/imaginary components caused by floating point."""
    real = 0.0 if abs(value.real) < tolerance else value.real
    imaginary = 0.0 if abs(value.imag) < tolerance else value.imag
    return complex(real, imaginary)


def clean_array(array: np.ndarray, tolerance: float = TOLERANCE) -> np.ndarray:
    """Return a copy with numerically insignificant values replaced by zero."""
    result = np.array(array, dtype=complex, copy=True)
    result.real[np.abs(result.real) < tolerance] = 0.0
    result.imag[np.abs(result.imag) < tolerance] = 0.0
    return result


def format_complex(value: complex, precision: int = 4) -> str:
    """Create readable text for a complex number."""
    value = clean_complex(complex(value))
    if abs(value.imag) < TOLERANCE:
        return f"{value.real:.{precision}f}"
    if abs(value.real) < TOLERANCE:
        return f"{value.imag:.{precision}f}i"
    sign = "+" if value.imag >= 0 else "-"
    return f"{value.real:.{precision}f}{sign}{abs(value.imag):.{precision}f}i"


def print_vector(
    vector: np.ndarray,
    basis_labels: Sequence[str] | None = None,
    title: str = "Vector",
) -> None:
    """Print a state vector with optional basis labels."""
    vector = np.asarray(vector).reshape(-1)
    print(f"\n{title}")
    for index, amplitude in enumerate(vector):
        label = basis_labels[index] if basis_labels is not None else str(index)
        if abs(amplitude) > TOLERANCE:
            print(f"  {format_complex(amplitude)} |{label}>")


def print_matrix(matrix: np.ndarray, title: str = "Matrix") -> None:
    """Print a complex matrix in a compact readable form."""
    print(f"\n{title}")
    for row in np.asarray(matrix):
        print("  [" + ", ".join(format_complex(x) for x in row) + "]")


def normalize(state: np.ndarray) -> np.ndarray:
    """Normalize a state vector."""
    state = np.asarray(state, dtype=complex).reshape(-1)
    norm = np.linalg.norm(state)
    if norm < TOLERANCE:
        raise ValueError("The zero vector cannot be normalized.")
    return state / norm


def is_normalized(state: np.ndarray, tolerance: float = TOLERANCE) -> bool:
    """Check whether a state has unit norm."""
    state = np.asarray(state, dtype=complex).reshape(-1)
    return abs(np.vdot(state, state).real - 1.0) < tolerance


def is_unitary(matrix: np.ndarray, tolerance: float = TOLERANCE) -> bool:
    """Check U†U = I."""
    matrix = np.asarray(matrix, dtype=complex)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        return False
    identity = np.eye(matrix.shape[0], dtype=complex)
    return np.allclose(matrix.conj().T @ matrix, identity, atol=tolerance)


def kron(*objects: np.ndarray) -> np.ndarray:
    """
    Compute a repeated Kronecker product.

    A tensor product is represented numerically by NumPy's kron operation.
    """
    if not objects:
        raise ValueError("At least one object is required.")
    result = np.asarray(objects[0], dtype=complex)
    for obj in objects[1:]:
        result = np.kron(result, np.asarray(obj, dtype=complex))
    return result


def ket0() -> np.ndarray:
    return np.array([1, 0], dtype=complex)


def ket1() -> np.ndarray:
    return np.array([0, 1], dtype=complex)


def ket_plus() -> np.ndarray:
    return normalize(ket0() + ket1())


def ket_minus() -> np.ndarray:
    return normalize(ket0() - ket1())


def computational_basis_state(index: int, number_of_qubits: int) -> np.ndarray:
    """Return |index> for an n-qubit computational basis."""
    dimension = 2**number_of_qubits
    if not 0 <= index < dimension:
        raise ValueError("Basis-state index is outside the Hilbert-space dimension.")
    state = np.zeros(dimension, dtype=complex)
    state[index] = 1
    return state


def basis_labels(number_of_qubits: int) -> List[str]:
    """Return computational basis labels in tensor-product ordering."""
    return [format(index, f"0{number_of_qubits}b") for index in range(2**number_of_qubits)]


# =============================================================================
# 2. SINGLE-SYSTEM QUANTUM STATES
# =============================================================================

def single_qubit_examples() -> None:
    print("\n" + "=" * 80)
    print("2. SINGLE-QUBIT STATES")
    print("=" * 80)

    zero = ket0()
    one = ket1()
    plus = ket_plus()
    minus = ket_minus()

    print_vector(zero, ["0", "1"], "|0>")
    print_vector(one, ["0", "1"], "|1>")
    print_vector(plus, ["0", "1"], "|+>")
    print_vector(minus, ["0", "1"], "|->")

    # A general pure qubit:
    #
    # |ψ> = α|0> + β|1>
    #
    # with |α|² + |β|² = 1.
    alpha = 1 / math.sqrt(3)
    beta = math.sqrt(2 / 3) * 1j
    psi = np.array([alpha, beta], dtype=complex)

    print_vector(psi, ["0", "1"], "General normalized qubit")
    print(f"Norm squared = {np.vdot(psi, psi).real:.6f}")
    print(f"P(0) = {abs(alpha) ** 2:.6f}")
    print(f"P(1) = {abs(beta) ** 2:.6f}")


# =============================================================================
# 3. TENSOR PRODUCT OF VECTORS
# =============================================================================

def tensor_product_basics() -> None:
    print("\n" + "=" * 80)
    print("3. TENSOR PRODUCTS OF QUANTUM STATES")
    print("=" * 80)

    zero = ket0()
    one = ket1()

    # The two-qubit state |0> ⊗ |1> is written |01>.
    zero_one = kron(zero, one)

    print_vector(
        zero_one,
        ["00", "01", "10", "11"],
        "|0> ⊗ |1> = |01>",
    )

    # Tensor products multiply dimensions.
    print(f"Dimension of one qubit: {len(zero)}")
    print(f"Dimension of two qubits: {len(zero_one)}")

    # A general product state:
    #
    # (α|0> + β|1>) ⊗ (γ|0> + δ|1>)
    #
    # = αγ|00> + αδ|01> + βγ|10> + βδ|11>
    alpha = 1 / math.sqrt(2)
    beta = 1 / math.sqrt(2)
    gamma = 1
    delta = 0

    first = np.array([alpha, beta], dtype=complex)
    second = np.array([gamma, delta], dtype=complex)

    product_state = kron(first, second)

    print_vector(
        product_state,
        ["00", "01", "10", "11"],
        "(|0> + |1>)/√2 ⊗ |0>",
    )

    # The order matters:
    # |0> ⊗ |1> is not the same vector as |1> ⊗ |0>.
    one_zero = kron(one, zero)
    print_vector(one_zero, ["00", "01", "10", "11"], "|1> ⊗ |0>")

    print("\nAre |01> and |10> equal?", np.allclose(zero_one, one_zero))


# =============================================================================
# 4. MULTI-QUBIT HILBERT-SPACE DIMENSION
# =============================================================================

def dimension_growth() -> None:
    print("\n" + "=" * 80)
    print("4. HILBERT-SPACE DIMENSION")
    print("=" * 80)

    print("Number of qubits -> Hilbert-space dimension")
    for number_of_qubits in range(1, 11):
        print(f"  {number_of_qubits:2d} -> {2**number_of_qubits:5d}")

    print(
        "\nFor n qubits, the state vector requires 2^n complex amplitudes "
        "before considering any compression or special structure."
    )


# =============================================================================
# 5. GENERAL TWO-QUBIT STATES
# =============================================================================

def general_two_qubit_state() -> None:
    print("\n" + "=" * 80)
    print("5. GENERAL TWO-QUBIT STATE")
    print("=" * 80)

    # A general pure two-qubit state is:
    #
    # |ψ> = a|00> + b|01> + c|10> + d|11>
    #
    # with |a|² + |b|² + |c|² + |d|² = 1.
    raw = np.array(
        [
            1,
            1j,
            2,
            -1j,
        ],
        dtype=complex,
    )

    state = normalize(raw)

    print_vector(state, ["00", "01", "10", "11"], "Normalized two-qubit state")

    probabilities = np.abs(state) ** 2

    print("\nComputational-basis probabilities:")
    for label, probability in zip(["00", "01", "10", "11"], probabilities):
        print(f"  P({label}) = {probability:.6f}")

    print(f"\nTotal probability = {probabilities.sum():.6f}")


# =============================================================================
# 6. TENSOR PRODUCTS OF OPERATORS
# =============================================================================

def operator_tensor_products() -> None:
    print("\n" + "=" * 80)
    print("6. TENSOR PRODUCTS OF OPERATORS")
    print("=" * 80)

    I = np.eye(2, dtype=complex)

    X = np.array(
        [
            [0, 1],
            [1, 0],
        ],
        dtype=complex,
    )

    Z = np.array(
        [
            [1, 0],
            [0, -1],
        ],
        dtype=complex,
    )

    H = (1 / math.sqrt(2)) * np.array(
        [
            [1, 1],
            [1, -1],
        ],
        dtype=complex,
    )

    print_matrix(X, "Pauli-X")
    print_matrix(Z, "Pauli-Z")
    print_matrix(H, "Hadamard")

    # X ⊗ I applies X to the first qubit and leaves the second unchanged.
    X_I = kron(X, I)

    # I ⊗ X applies X to the second qubit.
    I_X = kron(I, X)

    print_matrix(X_I, "X ⊗ I")
    print_matrix(I_X, "I ⊗ X")

    state_00 = kron(ket0(), ket0())

    result_first = X_I @ state_00
    result_second = I_X @ state_00

    print_vector(result_first, ["00", "01", "10", "11"], "(X ⊗ I)|00>")
    print_vector(result_second, ["00", "01", "10", "11"], "(I ⊗ X)|00>")

    # Local operators remain unitary when combined through a tensor product.
    print("\nX ⊗ I unitary:", is_unitary(X_I))
    print("I ⊗ X unitary:", is_unitary(I_X))


# =============================================================================
# 7. DISTRIBUTIVITY AND BILINEAR STRUCTURE
# =============================================================================

def tensor_algebra_properties() -> None:
    print("\n" + "=" * 80)
    print("7. IMPORTANT ALGEBRAIC PROPERTIES")
    print("=" * 80)

    a = np.array([1, 2], dtype=complex)
    b = np.array([3, 4], dtype=complex)
    c = np.array([5, 6], dtype=complex)

    left = kron(a, b + c)
    right = kron(a, b) + kron(a, c)

    print("Distributivity:")
    print("  a ⊗ (b + c) == a ⊗ b + a ⊗ c ->", np.allclose(left, right))

    # Scalar factors can be moved between tensor factors:
    #
    # (λa) ⊗ b = a ⊗ (λb) = λ(a ⊗ b)
    scalar = 2 + 3j
    left_scalar = kron(scalar * a, b)
    right_scalar = kron(a, scalar * b)

    print(
        "Scalar compatibility:",
        np.allclose(left_scalar, right_scalar),
    )

    # Associativity:
    # (A ⊗ B) ⊗ C = A ⊗ (B ⊗ C)
    d = np.array([7, 8], dtype=complex)

    associative_left = kron(kron(a, b), d)
    associative_right = kron(a, kron(b, d))

    print(
        "Associativity:",
        np.allclose(associative_left, associative_right),
    )

    # Tensor products are generally not commutative.
    print(
        "Commutativity in general:",
        np.allclose(kron(a, b), kron(b, a)),
    )


# =============================================================================
# 8. PRODUCT STATES VERSUS ENTANGLED STATES
# =============================================================================

def product_vs_entangled() -> None:
    print("\n" + "=" * 80)
    print("8. PRODUCT STATES VERSUS ENTANGLED STATES")
    print("=" * 80)

    # Product state:
    #
    # |ψ> = |+> ⊗ |0>
    #
    # This state can be written as separate states of two subsystems.
    product = kron(ket_plus(), ket0())

    print_vector(
        product,
        ["00", "01", "10", "11"],
        "Product state |+0>",
    )

    # Bell state:
    #
    # |Φ+> = (|00> + |11>) / √2
    #
    # This state cannot be expressed as |a> ⊗ |b>.
    bell_phi_plus = normalize(
        computational_basis_state(0, 2)
        + computational_basis_state(3, 2)
    )

    print_vector(
        bell_phi_plus,
        ["00", "01", "10", "11"],
        "Bell state |Φ+>",
    )

    print(
        "\nProduct state factorable:",
        is_product_two_qubit_state(product),
    )
    print(
        "Bell state factorable:",
        is_product_two_qubit_state(bell_phi_plus),
    )


# =============================================================================
# 9. PRODUCT-STATE TEST USING THE COEFFICIENT MATRIX
# =============================================================================

def coefficient_matrix_two_qubit(state: np.ndarray) -> np.ndarray:
    """
    Reshape a two-qubit state into

        C = [[a, b],
             [c, d]]

    for

        |ψ> = a|00> + b|01> + c|10> + d|11>.

    A pure two-qubit state is a product state exactly when this matrix has rank 1.
    """
    state = np.asarray(state, dtype=complex).reshape(-1)
    if len(state) != 4:
        raise ValueError("A two-qubit state must contain exactly four amplitudes.")
    return state.reshape(2, 2)


def is_product_two_qubit_state(
    state: np.ndarray,
    tolerance: float = TOLERANCE,
) -> bool:
    """
    Test whether a pure two-qubit state is separable.

    For a 2x2 coefficient matrix, separability is equivalent to determinant zero,
    up to numerical precision.
    """
    state = normalize(state)
    coefficient_matrix = coefficient_matrix_two_qubit(state)
    determinant = np.linalg.det(coefficient_matrix)
    return abs(determinant) < tolerance


def product_state_factorization(
    state: np.ndarray,
    tolerance: float = TOLERANCE,
) -> Tuple[np.ndarray, np.ndarray] | None:
    """
    Recover one possible tensor factorization of a separable two-qubit state.

    The global phase and local phases are not unique. This function chooses a
    convenient factorization based on the first significant coefficient.
    """
    state = normalize(state)
    matrix = coefficient_matrix_two_qubit(state)

    row_norms = np.linalg.norm(matrix, axis=1)
    column_norms = np.linalg.norm(matrix, axis=0)

    if not is_product_two_qubit_state(state, tolerance):
        return None

    if np.max(row_norms) < tolerance or np.max(column_norms) < tolerance:
        raise ValueError("Unexpected zero state.")

    # If the first row has nonzero norm, use it as the first factor.
    first_row_index = int(np.argmax(row_norms))
    first_row = matrix[first_row_index]

    first_factor = np.zeros(2, dtype=complex)
    second_factor = np.zeros(2, dtype=complex)

    # We can construct a rank-one decomposition matrix = u v^T.
    pivot = int(np.argmax(np.abs(first_row)))
    if abs(first_row[pivot]) < tolerance:
        return None

    second_factor = first_row.copy()
    first_factor = matrix[:, pivot] / second_factor[pivot]

    # Normalize each local state separately.
    first_norm = np.linalg.norm(first_factor)
    second_norm = np.linalg.norm(second_factor)

    first_factor /= first_norm
    second_factor *= first_norm
    second_factor /= np.linalg.norm(second_factor)

    reconstructed = kron(first_factor, second_factor)

    # Global phase adjustment so the reconstruction matches the original.
    overlap = np.vdot(reconstructed, state)
    if abs(overlap) > tolerance:
        reconstructed *= overlap / abs(overlap)

    # The factorization may differ by global phase, so verify it.
    if not np.allclose(reconstructed, state, atol=1e-8):
        return None

    return first_factor, second_factor


def separability_demonstration() -> None:
    print("\n" + "=" * 80)
    print("9. SEPARABILITY TEST")
    print("=" * 80)

    product = normalize(
        kron(
            np.array([1, 2j], dtype=complex),
            np.array([3, -1], dtype=complex),
        )
    )

    entangled = normalize(
        np.array(
            [
                1,
                0,
                0,
                1,
            ],
            dtype=complex,
        )
    )

    for name, state in [
        ("Product state", product),
        ("Bell state", entangled),
    ]:
        matrix = coefficient_matrix_two_qubit(state)
        print_matrix(matrix, f"Coefficient matrix: {name}")
        print(f"Determinant: {format_complex(np.linalg.det(matrix))}")
        print(f"Separable: {is_product_two_qubit_state(state)}")

        factors = product_state_factorization(state)
        if factors is not None:
            first, second = factors
            print_vector(first, ["0", "1"], "First local factor")
            print_vector(second, ["0", "1"], "Second local factor")


# =============================================================================
# 10. BELL STATES
# =============================================================================

def bell_states() -> Dict[str, np.ndarray]:
    """Return the four standard Bell states."""
    zero_zero = computational_basis_state(0, 2)
    zero_one = computational_basis_state(1, 2)
    one_zero = computational_basis_state(2, 2)
    one_one = computational_basis_state(3, 2)

    return {
        "Phi+": normalize(zero_zero + one_one),
        "Phi-": normalize(zero_zero - one_one),
        "Psi+": normalize(zero_one + one_zero),
        "Psi-": normalize(zero_one - one_zero),
    }


def demonstrate_bell_states() -> None:
    print("\n" + "=" * 80)
    print("10. THE FOUR BELL STATES")
    print("=" * 80)

    states = bell_states()
    labels = ["00", "01", "10", "11"]

    for name, state in states.items():
        print_vector(state, labels, f"|{name}>")
        print(f"  Normalized: {is_normalized(state)}")
        print(f"  Product state: {is_product_two_qubit_state(state)}")

    matrix = np.column_stack(list(states.values()))
    print("\nBell-state orthonormality:")
    print(np.allclose(matrix.conj().T @ matrix, np.eye(4)))


# =============================================================================
# 11. BUILDING ENTANGLEMENT WITH QUANTUM GATES
# =============================================================================

def create_bell_state_with_gates() -> None:
    print("\n" + "=" * 80)
    print("11. CREATING ENTANGLEMENT WITH GATES")
    print("=" * 80)

    I = np.eye(2, dtype=complex)

    X = np.array(
        [
            [0, 1],
            [1, 0],
        ],
        dtype=complex,
    )

    H = (1 / math.sqrt(2)) * np.array(
        [
            [1, 1],
            [1, -1],
        ],
        dtype=complex,
    )

    # Start with |00>.
    state = kron(ket0(), ket0())
    print_vector(state, ["00", "01", "10", "11"], "Initial |00>")

    # Apply H to the first qubit:
    # (H ⊗ I)|00> = (|00> + |10>)/√2.
    state = kron(H, I) @ state
    print_vector(state, ["00", "01", "10", "11"], "After H on qubit 1")

    # A CNOT maps |10> -> |11>, while leaving |00> unchanged.
    cnot = controlled_not()
    state = cnot @ state

    print_vector(
        state,
        ["00", "01", "10", "11"],
        "After CNOT",
    )

    expected = bell_states()["Phi+"]
    print("Matches |Φ+>:", np.allclose(state, expected))


# =============================================================================
# 12. CONTROLLED-NOT OPERATOR
# =============================================================================

def controlled_not() -> np.ndarray:
    """
    Standard two-qubit CNOT in computational basis ordering
    |00>, |01>, |10>, |11>.

    The first qubit is control and the second is target.
    """
    return np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=complex,
    )


def controlled_gate(
    control_gate: np.ndarray,
    target_gate: np.ndarray,
) -> np.ndarray:
    """
    Construct a controlled-U gate for two qubits.

    The first qubit is the control.
    The operator is:
        |0><0| ⊗ I + |1><1| ⊗ U
    """
    control_gate = np.asarray(control_gate, dtype=complex)
    target_gate = np.asarray(target_gate, dtype=complex)

    if control_gate.shape != (2, 2):
        raise ValueError("The target operation must be a 2x2 single-qubit gate.")

    p0 = np.array([[1, 0], [0, 0]], dtype=complex)
    p1 = np.array([[0, 0], [0, 1]], dtype=complex)

    return kron(p0, np.eye(2)) + kron(p1, target_gate)


def controlled_gate_demo() -> None:
    print("\n" + "=" * 80)
    print("12. CONTROLLED OPERATIONS")
    print("=" * 80)

    X = np.array(
        [
            [0, 1],
            [1, 0],
        ],
        dtype=complex,
    )

    cnot_from_definition = controlled_gate(X, X)
    print_matrix(cnot_from_definition, "Controlled-X")

    print("Controlled-X equals CNOT:", np.allclose(cnot_from_definition, controlled_not()))
    print("CNOT is unitary:", is_unitary(cnot_from_definition))


# =============================================================================
# 13. THREE-QUBIT STATES
# =============================================================================

def three_qubit_states() -> None:
    print("\n" + "=" * 80)
    print("13. THREE-QUBIT STATES")
    print("=" * 80)

    # |000>
    zero_zero_zero = kron(ket0(), ket0(), ket0())

    print_vector(
        zero_zero_zero,
        basis_labels(3),
        "|000>",
    )

    # GHZ state:
    #
    # |GHZ> = (|000> + |111>) / √2
    ghz = normalize(
        computational_basis_state(0, 3)
        + computational_basis_state(7, 3)
    )

    print_vector(
        ghz,
        basis_labels(3),
        "Three-qubit GHZ state",
    )

    # W state:
    #
    # |W> = (|001> + |010> + |100>) / √3
    w_state = normalize(
        computational_basis_state(1, 3)
        + computational_basis_state(2, 3)
        + computational_basis_state(4, 3)
    )

    print_vector(
        w_state,
        basis_labels(3),
        "Three-qubit W state",
    )


# =============================================================================
# 14. GENERAL N-QUBIT PRODUCT STATES
# =============================================================================

def n_qubit_product_state(local_states: Sequence[np.ndarray]) -> np.ndarray:
    """Construct an n-qubit product state from local single-qubit states."""
    if not local_states:
        raise ValueError("At least one local state is required.")

    result = np.asarray(local_states[0], dtype=complex)
    for state in local_states[1:]:
        result = kron(result, np.asarray(state, dtype=complex))

    return normalize(result)


def general_product_state_demo() -> None:
    print("\n" + "=" * 80)
    print("14. GENERAL N-QUBIT PRODUCT STATES")
    print("=" * 80)

    local_states = [
        ket_plus(),
        ket_minus(),
        ket0(),
        ket1(),
    ]

    state = n_qubit_product_state(local_states)

    print_vector(
        state,
        basis_labels(4),
        "|+> ⊗ |-> ⊗ |0> ⊗ |1>",
    )

    print("Dimension:", len(state))
    print("Normalized:", is_normalized(state))


# =============================================================================
# 15. PARTIAL TRACE
# =============================================================================

def partial_trace_two_qubit(
    density_matrix: np.ndarray,
    trace_out: int,
) -> np.ndarray:
    """
    Partial trace of a two-qubit density matrix.

    trace_out = 0:
        trace out the first qubit and return the second-qubit state.

    trace_out = 1:
        trace out the second qubit and return the first-qubit state.

    The density matrix is reshaped as:
        ρ[i,j,k,l]
    where i,k identify subsystem A and j,l identify subsystem B.
    """
    rho = np.asarray(density_matrix, dtype=complex)

    if rho.shape != (4, 4):
        raise ValueError("A two-qubit density matrix must have shape (4, 4).")

    if trace_out not in (0, 1):
        raise ValueError("trace_out must be 0 or 1.")

    tensor = rho.reshape(2, 2, 2, 2)

    if trace_out == 0:
        # Trace over first subsystem:
        # ρ_B[j,l] = Σ_i ρ[i,j,i,l]
        return np.einsum("ijil->jl", tensor)

    # Trace over second subsystem:
    # ρ_A[i,k] = Σ_j ρ[i,j,k,j]
    return np.einsum("ijkj->ik", tensor)


def density_matrix(state: np.ndarray) -> np.ndarray:
    """Construct |ψ><ψ|."""
    state = np.asarray(state, dtype=complex).reshape(-1)
    return np.outer(state, state.conj())


def partial_trace_demo() -> None:
    print("\n" + "=" * 80)
    print("15. REDUCED STATES AND PARTIAL TRACE")
    print("=" * 80)

    product = kron(ket_plus(), ket0())
    bell = bell_states()["Phi+"]

    for name, state in [
        ("Product state |+0>", product),
        ("Bell state |Φ+>", bell),
    ]:
        rho = density_matrix(state)
        rho_first = partial_trace_two_qubit(rho, trace_out=1)
        rho_second = partial_trace_two_qubit(rho, trace_out=0)

        print_matrix(rho, f"Density matrix: {name}")
        print_matrix(rho_first, "Reduced state of first qubit")
        print_matrix(rho_second, "Reduced state of second qubit")

        print("Trace of first reduced state:", np.trace(rho_first))
        print("Trace of second reduced state:", np.trace(rho_second))


# =============================================================================
# 16. PURE-STATE ENTANGLEMENT THROUGH REDUCED DENSITY MATRICES
# =============================================================================

def purity(density: np.ndarray) -> float:
    """Return Tr(ρ²), a useful mixedness diagnostic."""
    density = np.asarray(density, dtype=complex)
    return float(np.trace(density @ density).real)


def reduced_state_entanglement_demo() -> None:
    print("\n" + "=" * 80)
    print("16. ENTANGLEMENT AND REDUCED-STATE PURITY")
    print("=" * 80)

    product = kron(ket_plus(), ket0())
    bell = bell_states()["Phi+"]

    for name, state in [
        ("Product state", product),
        ("Bell state", bell),
    ]:
        rho = density_matrix(state)
        reduced = partial_trace_two_qubit(rho, trace_out=1)

        print(f"\n{name}")
        print(f"  Reduced-state purity = {purity(reduced):.6f}")
        print(
            "  Pure reduced state:",
            np.isclose(purity(reduced), 1.0, atol=1e-9),
        )

    print(
        "\nFor a pure bipartite state, a reduced subsystem is pure exactly "
        "when the global state is separable."
    )


# =============================================================================
# 17. SCHMIDT DECOMPOSITION
# =============================================================================

@dataclass
class SchmidtDecomposition:
    coefficients: np.ndarray
    left_vectors: np.ndarray
    right_vectors: np.ndarray


def schmidt_decomposition_two_qubit(
    state: np.ndarray,
    tolerance: float = TOLERANCE,
) -> SchmidtDecomposition:
    """
    Compute the Schmidt decomposition of a pure two-qubit state.

    If C is the 2x2 coefficient matrix, singular-value decomposition gives:
        C = U S V†

    Therefore:
        |ψ> = Σ_k s_k |u_k> ⊗ |v_k*>

    where the singular values are the Schmidt coefficients.
    """
    state = normalize(state)
    coefficient_matrix = coefficient_matrix_two_qubit(state)

    U, singular_values, Vh = np.linalg.svd(coefficient_matrix)

    # Vh = V†. For the tensor expansion using C = U S V†,
    # the second ket vectors are the complex conjugates of V's columns.
    right_vectors = Vh.conj().T.conj()

    singular_values[singular_values < tolerance] = 0.0

    return SchmidtDecomposition(
        coefficients=singular_values,
        left_vectors=U,
        right_vectors=right_vectors,
    )


def schmidt_demo() -> None:
    print("\n" + "=" * 80)
    print("17. SCHMIDT DECOMPOSITION")
    print("=" * 80)

    examples = {
        "Product state": kron(ket_plus(), ket0()),
        "Bell state": bell_states()["Phi+"],
        "Partially entangled state": normalize(
            2 * computational_basis_state(0, 2)
            + computational_basis_state(3, 2)
        ),
    }

    for name, state in examples.items():
        decomposition = schmidt_decomposition_two_qubit(state)

        print(f"\n{name}")
        print("Schmidt coefficients:")
        for coefficient in decomposition.coefficients:
            if coefficient > TOLERANCE:
                print(f"  {coefficient:.6f}")

        rank = int(np.sum(decomposition.coefficients > TOLERANCE))
        print("Schmidt rank:", rank)


# =============================================================================
# 18. VON NEUMANN ENTROPY AND ENTANGLEMENT ENTROPY
# =============================================================================

def von_neumann_entropy(
    density: np.ndarray,
    base: float = 2.0,
    tolerance: float = TOLERANCE,
) -> float:
    """Compute S(ρ) = -Tr(ρ log ρ) using the eigenvalue spectrum."""
    density = np.asarray(density, dtype=complex)

    eigenvalues = np.linalg.eigvalsh(density).real
    entropy = 0.0

    for eigenvalue in eigenvalues:
        if eigenvalue > tolerance:
            entropy -= eigenvalue * math.log(eigenvalue, base)

    return float(entropy)


def entanglement_entropy_demo() -> None:
    print("\n" + "=" * 80)
    print("18. ENTANGLEMENT ENTROPY")
    print("=" * 80)

    product = kron(ket_plus(), ket0())
    bell = bell_states()["Phi+"]

    partially_entangled = normalize(
        2 * computational_basis_state(0, 2)
        + computational_basis_state(3, 2)
    )

    for name, state in [
        ("Product state", product),
        ("Partially entangled state", partially_entangled),
        ("Bell state", bell),
    ]:
        reduced = partial_trace_two_qubit(
            density_matrix(state),
            trace_out=1,
        )

        entropy = von_neumann_entropy(reduced)

        print(f"{name}: entanglement entropy = {entropy:.6f} bits")


# =============================================================================
# 19. DENSITY MATRICES
# =============================================================================

def density_matrix_properties_demo() -> None:
    print("\n" + "=" * 80)
    print("19. DENSITY-MATRIX REPRESENTATION")
    print("=" * 80)

    state = bell_states()["Psi-"]
    rho = density_matrix(state)

    print_matrix(rho, "Bell-state density matrix")

    print("Hermitian:", np.allclose(rho, rho.conj().T))
    print("Trace one:", np.isclose(np.trace(rho), 1.0))
    print(
        "Positive semidefinite:",
        np.all(np.linalg.eigvalsh(rho) >= -TOLERANCE),
    )
    print("Purity:", purity(rho))


# =============================================================================
# 20. MIXED STATES AND CLASSICAL CORRELATION
# =============================================================================

def mixed_state_demo() -> None:
    print("\n" + "=" * 80)
    print("20. MIXED MULTI-SYSTEM STATES")
    print("=" * 80)

    # A classical mixture:
    #
    # ρ = 1/2 |00><00| + 1/2 |11><11|
    #
    # It has correlations, but it is not the same as the coherent Bell state.
    zero_zero = computational_basis_state(0, 2)
    one_one = computational_basis_state(3, 2)

    mixed = 0.5 * density_matrix(zero_zero) + 0.5 * density_matrix(one_one)
    bell = density_matrix(bell_states()["Phi+"])

    print_matrix(mixed, "Classically correlated mixed state")
    print_matrix(bell, "Bell-state density matrix")

    print("\nMixed-state purity:", purity(mixed))
    print("Bell-state purity:", purity(bell))

    mixed_reduced = partial_trace_two_qubit(mixed, trace_out=1)
    bell_reduced = partial_trace_two_qubit(bell, trace_out=1)

    print_matrix(mixed_reduced, "Reduced state of mixed state")
    print_matrix(bell_reduced, "Reduced state of Bell state")


# =============================================================================
# 21. MEASUREMENT PROBABILITIES
# =============================================================================

def computational_measurement_probabilities(
    state: np.ndarray,
) -> Dict[str, float]:
    """Return computational-basis probabilities."""
    state = normalize(state)
    labels = basis_labels(int(math.log2(len(state))))

    return {
        label: float(abs(amplitude) ** 2)
        for label, amplitude in zip(labels, state)
    }


def measurement_demo() -> None:
    print("\n" + "=" * 80)
    print("21. MEASUREMENT OF MULTI-QUBIT STATES")
    print("=" * 80)

    state = bell_states()["Phi+"]

    probabilities = computational_measurement_probabilities(state)

    print("Measurement probabilities for |Φ+>:")
    for basis_state, probability in probabilities.items():
        print(f"  {basis_state}: {probability:.6f}")

    print(
        "\nThe Bell state produces only 00 and 11 in the computational basis, "
        "each with probability 1/2."
    )


# =============================================================================
# 22. RANDOM MEASUREMENT SAMPLING
# =============================================================================

def sample_measurements(
    state: np.ndarray,
    shots: int = 1000,
    seed: int = 42,
) -> Dict[str, int]:
    """Sample computational-basis measurements."""
    if shots <= 0:
        raise ValueError("shots must be positive.")

    state = normalize(state)
    probabilities = np.abs(state) ** 2
    labels = basis_labels(int(math.log2(len(state))))

    rng = np.random.default_rng(seed)
    sampled_indices = rng.choice(
        len(state),
        size=shots,
        p=probabilities,
    )

    counts = {label: 0 for label in labels}
    for index in sampled_indices:
        counts[labels[index]] += 1

    return counts


def measurement_sampling_demo() -> None:
    print("\n" + "=" * 80)
    print("22. MEASUREMENT SAMPLING")
    print("=" * 80)

    counts = sample_measurements(
        bell_states()["Phi+"],
        shots=1000,
        seed=7,
    )

    print("1000 simulated measurements:")
    for label, count in counts.items():
        print(f"  {label}: {count}")


# =============================================================================
# 23. PROJECTIVE MEASUREMENT AND COLLAPSE
# =============================================================================

def project_state_onto_computational_basis(
    state: np.ndarray,
    outcome_index: int,
) -> np.ndarray:
    """
    Return the post-measurement state conditioned on a computational-basis outcome.

    If the outcome probability is zero, the requested projection is impossible.
    """
    state = normalize(state)

    if not 0 <= outcome_index < len(state):
        raise ValueError("Measurement outcome is outside the state dimension.")

    probability = abs(state[outcome_index]) ** 2

    if probability < TOLERANCE:
        raise ValueError("The requested outcome has zero probability.")

    collapsed = np.zeros_like(state)
    collapsed[outcome_index] = state[outcome_index]

    return normalize(collapsed)


def collapse_demo() -> None:
    print("\n" + "=" * 80)
    print("23. CONDITIONAL STATE COLLAPSE")
    print("=" * 80)

    bell = bell_states()["Phi+"]

    # If 00 is observed, the two-qubit state becomes exactly |00>.
    collapsed_00 = project_state_onto_computational_basis(bell, 0)

    print_vector(
        collapsed_00,
        ["00", "01", "10", "11"],
        "Bell state after observing 00",
    )

    print(
        "\nFor an entangled state, measurement of one subsystem can "
        "condition the state of the other subsystem."
    )


# =============================================================================
# 24. SWAP OPERATOR
# =============================================================================

def swap_operator() -> np.ndarray:
    """Construct the two-qubit SWAP gate."""
    return np.array(
        [
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
        ],
        dtype=complex,
    )


def swap_demo() -> None:
    print("\n" + "=" * 80)
    print("24. SWAP AND SUBSYSTEM ORDER")
    print("=" * 80)

    state = kron(ket0(), ket1())
    swapped = swap_operator() @ state

    print_vector(state, ["00", "01", "10", "11"], "Before SWAP")
    print_vector(swapped, ["00", "01", "10", "11"], "After SWAP")

    print("SWAP is unitary:", is_unitary(swap_operator()))
    print("SWAP squared equals identity:", np.allclose(
        swap_operator() @ swap_operator(),
        np.eye(4),
    ))


# =============================================================================
# 25. LOCAL VERSUS GLOBAL OPERATIONS
# =============================================================================

def local_vs_global_operations_demo() -> None:
    print("\n" + "=" * 80)
    print("25. LOCAL VERSUS GLOBAL OPERATIONS")
    print("=" * 80)

    X = np.array(
        [
            [0, 1],
            [1, 0],
        ],
        dtype=complex,
    )

    H = (1 / math.sqrt(2)) * np.array(
        [
            [1, 1],
            [1, -1],
        ],
        dtype=complex,
    )

    local_x = kron(X, np.eye(2))
    local_h = kron(np.eye(2), H)

    # Local gates act independently on one subsystem.
    # A general two-qubit unitary need not factor into A ⊗ B.
    global_gate = controlled_gate(X, X)

    print("X ⊗ I is unitary:", is_unitary(local_x))
    print("I ⊗ H is unitary:", is_unitary(local_h))
    print("CNOT is unitary:", is_unitary(global_gate))

    print(
        "\nCNOT is a genuinely two-system operation: it cannot generally "
        "be represented as a single tensor product A ⊗ B."
    )


# =============================================================================
# 26. OPERATOR SCHMIDT RANK
# =============================================================================

def operator_coefficient_matrix_for_two_qubit_gate(
    operator: np.ndarray,
) -> np.ndarray:
    """
    Rearrange a 4x4 two-qubit operator into a 4x4 matrix whose rank gives
    the operator Schmidt rank.

    For an operator represented as:
        U[i,j,k,l]
    with output indices i,j and input indices k,l,
    reshape to:
        M[(i,k), (j,l)]
    """
    operator = np.asarray(operator, dtype=complex)

    if operator.shape != (4, 4):
        raise ValueError("A two-qubit operator must have shape (4, 4).")

    tensor = operator.reshape(2, 2, 2, 2)

    # Move indices to group first subsystem input/output together.
    rearranged = np.transpose(tensor, (0, 2, 1, 3))
    return rearranged.reshape(4, 4)


def operator_schmidt_rank(operator: np.ndarray) -> int:
    """Return the numerical operator Schmidt rank."""
    matrix = operator_coefficient_matrix_for_two_qubit_gate(operator)
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    return int(np.sum(singular_values > TOLERANCE))


def operator_schmidt_demo() -> None:
    print("\n" + "=" * 80)
    print("26. OPERATOR SCHMIDT RANK")
    print("=" * 80)

    X = np.array(
        [
            [0, 1],
            [1, 0],
        ],
        dtype=complex,
    )

    local = kron(X, np.eye(2))
    cnot = controlled_not()

    print("Operator Schmidt rank of X ⊗ I:", operator_schmidt_rank(local))
    print("Operator Schmidt rank of CNOT:", operator_schmidt_rank(cnot))

    print(
        "\nRank 1 indicates a simple tensor-product operator. "
        "CNOT has a higher operator Schmidt rank and therefore cannot "
        "be written as A ⊗ B."
    )


# =============================================================================
# 27. EXPECTATION VALUES OF MULTI-SYSTEM OBSERVABLES
# =============================================================================

def expectation_value(
    state: np.ndarray,
    operator: np.ndarray,
) -> complex:
    """Calculate <ψ|O|ψ>."""
    state = normalize(state)
    operator = np.asarray(operator, dtype=complex)

    if operator.shape != (len(state), len(state)):
        raise ValueError("Operator dimension does not match the state.")

    return complex(np.vdot(state, operator @ state))


def expectation_demo() -> None:
    print("\n" + "=" * 80)
    print("27. MULTI-SYSTEM OBSERVABLES")
    print("=" * 80)

    X = np.array(
        [
            [0, 1],
            [1, 0],
        ],
        dtype=complex,
    )

    Z = np.array(
        [
            [1, 0],
            [0, -1],
        ],
        dtype=complex,
    )

    bell = bell_states()["Phi+"]

    ZZ = kron(Z, Z)
    XX = kron(X, X)
    XI = kron(X, np.eye(2))

    print("<Φ+| Z⊗Z |Φ+> =", format_complex(expectation_value(bell, ZZ)))
    print("<Φ+| X⊗X |Φ+> =", format_complex(expectation_value(bell, XX)))
    print("<Φ+| X⊗I |Φ+> =", format_complex(expectation_value(bell, XI)))


# =============================================================================
# 28. CORRELATION FUNCTIONS
# =============================================================================

def correlation_demo() -> None:
    print("\n" + "=" * 80)
    print("28. CORRELATIONS")
    print("=" * 80)

    X = np.array(
        [
            [0, 1],
            [1, 0],
        ],
        dtype=complex,
    )

    Y = np.array(
        [
            [0, -1j],
            [1j, 0],
        ],
        dtype=complex,
    )

    Z = np.array(
        [
            [1, 0],
            [0, -1],
        ],
        dtype=complex,
    )

    bell = bell_states()["Phi+"]

    observables = {
        "X⊗X": kron(X, X),
        "Y⊗Y": kron(Y, Y),
        "Z⊗Z": kron(Z, Z),
    }

    for name, operator in observables.items():
        value = expectation_value(bell, operator)
        print(f"<{name}> = {format_complex(value)}")

    print(
        "\nTwo-system expectation values contain information about joint "
        "behavior that individual subsystem expectation values do not capture."
    )


# =============================================================================
# 29. TENSOR PRODUCT OF DENSITY MATRICES
# =============================================================================

def density_tensor_product_demo() -> None:
    print("\n" + "=" * 80)
    print("29. TENSOR PRODUCTS OF DENSITY MATRICES")
    print("=" * 80)

    rho_a = density_matrix(ket_plus())
    rho_b = density_matrix(ket1())

    rho_ab = kron(rho_a, rho_b)

    expected = density_matrix(kron(ket_plus(), ket1()))

    print_matrix(rho_a, "ρ_A")
    print_matrix(rho_b, "ρ_B")
    print_matrix(rho_ab, "ρ_A ⊗ ρ_B")

    print(
        "\nρ_A ⊗ ρ_B equals the density matrix of |+>⊗|1>:",
        np.allclose(rho_ab, expected),
    )


# =============================================================================
# 30. PURE AND MIXED STATE DISTINCTION
# =============================================================================

def pure_mixed_distinction_demo() -> None:
    print("\n" + "=" * 80)
    print("30. PURE VERSUS MIXED STATES")
    print("=" * 80)

    pure = density_matrix(ket_plus())

    mixed = 0.5 * density_matrix(ket0()) + 0.5 * density_matrix(ket1())

    print_matrix(pure, "Pure state density matrix")
    print_matrix(mixed, "Mixed state density matrix")

    print("Pure-state purity:", purity(pure))
    print("Mixed-state purity:", purity(mixed))


# =============================================================================
# 31. MULTI-SYSTEM DENSITY MATRIX DIMENSION
# =============================================================================

def density_matrix_dimension_demo() -> None:
    print("\n" + "=" * 80)
    print("31. DENSITY-MATRIX SCALING")
    print("=" * 80)

    print("For n qubits:")
    print("  State vector dimension = 2^n")
    print("  Density matrix dimension = 2^n × 2^n")
    print("  Number of matrix entries = 4^n")

    for n in range(1, 9):
        vector_dimension = 2**n
        matrix_entries = 4**n
        print(
            f"  n={n}: vector dimension={vector_dimension:4d}, "
            f"density-matrix entries={matrix_entries:7d}"
        )


# =============================================================================
# 32. PARTIAL TRACE FOR A THREE-QUBIT STATE
# =============================================================================

def partial_trace_three_qubit(
    density: np.ndarray,
    trace_out: int,
) -> np.ndarray:
    """
    Trace out one qubit from a three-qubit density matrix.

    Output is a 4x4 density matrix for the remaining two qubits.
    """
    rho = np.asarray(density, dtype=complex)

    if rho.shape != (8, 8):
        raise ValueError("A three-qubit density matrix must have shape (8, 8).")

    if trace_out not in (0, 1, 2):
        raise ValueError("trace_out must be 0, 1, or 2.")

    tensor = rho.reshape(2, 2, 2, 2, 2, 2)

    # Indices are:
    # (a,b,c, a',b',c')
    #
    # Trace out subsystem q by setting q == q' and summing over it.
    if trace_out == 0:
        return np.einsum("abcAbC->bcBC", tensor).reshape(4, 4)

    if trace_out == 1:
        return np.einsum("abcAdC->acAC", tensor).reshape(4, 4)

    return np.einsum("abcABc->abAB", tensor).reshape(4, 4)


def partial_trace_three_qubit_demo() -> None:
    print("\n" + "=" * 80)
    print("32. PARTIAL TRACE OF A THREE-QUBIT GHZ STATE")
    print("=" * 80)

    ghz = normalize(
        computational_basis_state(0, 3)
        + computational_basis_state(7, 3)
    )

    rho = density_matrix(ghz)

    for qubit in range(3):
        reduced = partial_trace_three_qubit(rho, qubit)
        print_matrix(
            reduced,
            f"Two-qubit state after tracing out qubit {qubit}",
        )
        print("  Trace:", format_complex(np.trace(reduced)))
        print("  Purity:", purity(reduced))


# =============================================================================
# 33. QUBIT PERMUTATION AND TENSOR ORDERING
# =============================================================================

def permute_two_qubit_state(state: np.ndarray) -> np.ndarray:
    """Swap the tensor factors of a two-qubit state."""
    state = np.asarray(state, dtype=complex).reshape(2, 2)
    return state.T.reshape(4)


def tensor_ordering_demo() -> None:
    print("\n" + "=" * 80)
    print("33. TENSOR ORDERING")
    print("=" * 80)

    first = normalize(np.array([1, 2], dtype=complex))
    second = normalize(np.array([3, 4j], dtype=complex))

    state_ab = kron(first, second)
    state_ba = kron(second, first)

    print_vector(state_ab, ["00", "01", "10", "11"], "|A>⊗|B>")
    print_vector(state_ba, ["00", "01", "10", "11"], "|B>⊗|A>")

    permuted = permute_two_qubit_state(state_ab)

    print(
        "Transpose-based subsystem permutation correct:",
        np.allclose(permuted, state_ba),
    )


# =============================================================================
# 34. TENSOR PRODUCTS AND EIGENVALUES
# =============================================================================

def tensor_eigenvalue_demo() -> None:
    print("\n" + "=" * 80)
    print("34. EIGENVALUES OF TENSOR-PRODUCT OPERATORS")
    print("=" * 80)

    A = np.diag([2, 3]).astype(complex)
    B = np.diag([5, 7]).astype(complex)

    AB = kron(A, B)
    eigenvalues = np.linalg.eigvals(AB)

    expected = np.array([10, 14, 15, 21], dtype=complex)

    print("Eigenvalues of A:", np.linalg.eigvals(A))
    print("Eigenvalues of B:", np.linalg.eigvals(B))
    print("Eigenvalues of A⊗B:", np.sort(eigenvalues.real))
    print("Pairwise products:", np.sort(expected.real))

    print(
        "\nFor tensor-product operators, eigenvalues are products of "
        "eigenvalues from the component operators."
    )


# =============================================================================
# 35. TRACE AND DETERMINANT IDENTITIES
# =============================================================================

def tensor_matrix_identity_demo() -> None:
    print("\n" + "=" * 80)
    print("35. TRACE AND DETERMINANT IDENTITIES")
    print("=" * 80)

    A = np.array([[1, 2], [3, 4]], dtype=complex)
    B = np.array([[5, 6], [7, 8]], dtype=complex)

    AB = kron(A, B)

    # Trace identity:
    # Tr(A ⊗ B) = Tr(A) Tr(B)
    left_trace = np.trace(AB)
    right_trace = np.trace(A) * np.trace(B)

    print(
        "Tr(A⊗B) = Tr(A)Tr(B):",
        np.isclose(left_trace, right_trace),
    )

    # Determinant identity:
    # det(A⊗B) = det(A)^n det(B)^m
    # for A of size m×m and B of size n×n.
    left_det = np.linalg.det(AB)
    right_det = np.linalg.det(A) ** 2 * np.linalg.det(B) ** 2

    print(
        "det(A⊗B) = det(A)^2 det(B)^2 for 2×2 matrices:",
        np.isclose(left_det, right_det),
    )


# =============================================================================
# 36. COMMUTATORS OF LOCAL OPERATORS
# =============================================================================

def local_operator_commutator_demo() -> None:
    print("\n" + "=" * 80)
    print("36. OPERATORS ON DIFFERENT SUBSYSTEMS")
    print("=" * 80)

    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    I = np.eye(2, dtype=complex)

    X_first = kron(X, I)
    Z_second = kron(I, Z)

    commutator = X_first @ Z_second - Z_second @ X_first

    print_matrix(commutator, "[X⊗I, I⊗Z]")
    print(
        "Operators acting on different subsystems commute:",
        np.allclose(commutator, np.zeros((4, 4))),
    )

    # Operators acting on the same subsystem can fail to commute:
    same_subsystem_commutator = X @ Z - Z @ X
    print_matrix(same_subsystem_commutator, "[X, Z]")


# =============================================================================
# 37. PARTIAL MEASUREMENT
# =============================================================================

def measure_first_qubit_probabilities(state: np.ndarray) -> Dict[int, float]:
    """
    Calculate probabilities for measuring only the first qubit.

    For two qubits:
        P(first=0) = P(00) + P(01)
        P(first=1) = P(10) + P(11)
    """
    state = normalize(state)

    if len(state) != 4:
        raise ValueError("This demonstration expects two qubits.")

    probabilities = np.abs(state) ** 2

    return {
        0: float(probabilities[0] + probabilities[1]),
        1: float(probabilities[2] + probabilities[3]),
    }


def partial_measurement_demo() -> None:
    print("\n" + "=" * 80)
    print("37. MEASURING ONE SUBSYSTEM")
    print("=" * 80)

    product = kron(ket_plus(), ket0())
    bell = bell_states()["Phi+"]

    for name, state in [
        ("Product state |+0>", product),
        ("Bell state |Φ+>", bell),
    ]:
        probabilities = measure_first_qubit_probabilities(state)
        print(f"\n{name}")
        for outcome, probability in probabilities.items():
            print(f"  First qubit = {outcome}: {probability:.6f}")


# =============================================================================
# 38. ENTANGLEMENT IS NOT THE SAME AS CORRELATION IN GENERAL
# =============================================================================

def correlation_vs_entanglement_demo() -> None:
    print("\n" + "=" * 80)
    print("38. CORRELATION VERSUS ENTANGLEMENT")
    print("=" * 80)

    # This state is correlated but separable:
    # ρ = 1/2 |00><00| + 1/2 |11><11|.
    classical = 0.5 * density_matrix(
        computational_basis_state(0, 2)
    ) + 0.5 * density_matrix(
        computational_basis_state(3, 2)
    )

    quantum = density_matrix(bell_states()["Phi+"])

    print("Classically correlated state purity:", purity(classical))
    print("Bell-state purity:", purity(quantum))

    print(
        "\nA density matrix can contain correlations without being an "
        "entangled quantum state. Entanglement is a stronger structural property."
    )


# =============================================================================
# 39. SWAP TEST IDEA
# =============================================================================

def swap_test_probability_equal(
    state_a: np.ndarray,
    state_b: np.ndarray,
) -> float:
    """
    Probability of measuring the symmetric ancilla outcome in an ideal SWAP test.

    P(0) = (1 + |<a|b>|²) / 2

    The calculation directly demonstrates the mathematical result without
    requiring a separate ancilla simulation.
    """
    state_a = normalize(state_a)
    state_b = normalize(state_b)

    overlap = np.vdot(state_a, state_b)
    return float((1 + abs(overlap) ** 2) / 2)


def swap_test_demo() -> None:
    print("\n" + "=" * 80)
    print("39. SWAP TEST MATHEMATICS")
    print("=" * 80)

    a = ket0()
    b = ket0()
    c = ket1()

    print("P(0) for |0> versus |0>:", swap_test_probability_equal(a, b))
    print("P(0) for |0> versus |1>:", swap_test_probability_equal(a, c))
    print("P(0) for |0> versus |+>:", swap_test_probability_equal(a, ket_plus()))


# =============================================================================
# 40. NO-CLONING CONTEXT
# =============================================================================

def no_cloning_tensor_structure_demo() -> None:
    print("\n" + "=" * 80)
    print("40. TENSOR-PRODUCT VIEW OF TWO COPIES")
    print("=" * 80)

    # If a single-qubit state |ψ> is supplied twice, the two-copy state is
    # |ψ>⊗|ψ>, not a second copy created from an arbitrary unknown state
    # by a universal physical operation.
    psi = normalize(
        np.array(
            [1, 1j],
            dtype=complex,
        )
    )

    two_copy = kron(psi, psi)

    print_vector(
        psi,
        ["0", "1"],
        "Single-qubit state |ψ>",
    )

    print_vector(
        two_copy,
        ["00", "01", "10", "11"],
        "Formal two-copy state |ψ>⊗|ψ>",
    )

    print(
        "\nThe tensor product describes how two copies are represented "
        "mathematically. It does not imply that an arbitrary unknown quantum "
        "state can be physically cloned."
    )


# =============================================================================
# 41. ERROR CASES AND VALIDATION
# =============================================================================

def error_handling_demo() -> None:
    print("\n" + "=" * 80)
    print("41. EDGE CASES AND ERROR HANDLING")
    print("=" * 80)

    cases = []

    try:
        normalize(np.zeros(2, dtype=complex))
    except ValueError as error:
        cases.append(("Normalize zero vector", str(error)))

    try:
        kron()
    except ValueError as error:
        cases.append(("Empty tensor product", str(error)))

    try:
        partial_trace_two_qubit(np.eye(2), 0)
    except ValueError as error:
        cases.append(("Wrong density-matrix dimension", str(error)))

    try:
        computational_basis_state(8, 3)
    except ValueError as error:
        cases.append(("Invalid basis-state index", str(error)))

    try:
        sample_measurements(ket0(), shots=0)
    except ValueError as error:
        cases.append(("Invalid measurement shot count", str(error)))

    for name, message in cases:
        print(f"{name}: {message}")


# =============================================================================
# 42. NUMERICAL STABILITY
# =============================================================================

def numerical_stability_demo() -> None:
    print("\n" + "=" * 80)
    print("42. NUMERICAL STABILITY")
    print("=" * 80)

    # Floating-point arithmetic can produce values such as 1e-16 where exact
    # mathematics would produce zero. Quantum-state algorithms therefore use
    # tolerances when testing equality, normalization, rank, and positivity.
    tiny_state = np.array(
        [
            1.0,
            1e-14,
        ],
        dtype=complex,
    )

    normalized_state = normalize(tiny_state)

    print_vector(
        normalized_state,
        ["0", "1"],
        "State containing a very small amplitude",
    )

    print(
        "Normalized:",
        is_normalized(normalized_state),
    )

    print(
        "Tiny amplitude treated as numerically zero:",
        abs(normalized_state[1]) < TOLERANCE,
    )


# =============================================================================
# 43. PERFORMANCE AND MEMORY ESTIMATION
# =============================================================================

def memory_estimate_for_state(
    number_of_qubits: int,
    bytes_per_complex: int = 16,
) -> int:
    """Estimate raw bytes for a dense state vector."""
    return (2**number_of_qubits) * bytes_per_complex


def format_bytes(number_of_bytes: int) -> str:
    """Convert bytes into a readable binary unit."""
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    value = float(number_of_bytes)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{number_of_bytes} B"


def performance_demo() -> None:
    print("\n" + "=" * 80)
    print("43. PERFORMANCE AND MEMORY")
    print("=" * 80)

    print("Approximate dense state-vector memory using 16 bytes per complex amplitude:")

    for n in [10, 20, 30, 40, 50]:
        memory = memory_estimate_for_state(n)
        print(
            f"  {n:2d} qubits: {2**n:>18,} amplitudes -> {format_bytes(memory)}"
        )

    print(
        "\nThe exponential dimension of the tensor-product Hilbert space is a "
        "central computational limitation of classical simulation."
    )


# =============================================================================
# 44. TENSOR NETWORK MOTIVATION
# =============================================================================

def tensor_network_motivation_demo() -> None:
    print("\n" + "=" * 80)
    print("44. TENSOR NETWORK MOTIVATION")
    print("=" * 80)

    # A product state has a highly compressible tensor structure.
    #
    # Instead of storing 2^n amplitudes independently, we can store n local
    # two-component vectors when the state is exactly a product state.
    local_states = [ket_plus(), ket0(), ket_minus(), ket1(), ket_plus()]

    dense_state = n_qubit_product_state(local_states)

    dense_entries = len(dense_state)
    local_entries = sum(len(state) for state in local_states)

    print(f"Dense amplitudes for 5 qubits: {dense_entries}")
    print(f"Local amplitudes for product representation: {local_entries}")

    print(
        "\nTensor-network methods exploit structure in many multi-system "
        "states rather than explicitly storing every global amplitude."
    )


# =============================================================================
# 45. ENTANGLEMENT AND SCHMIDT RANK
# =============================================================================

def schmidt_rank_demo() -> None:
    print("\n" + "=" * 80)
    print("45. SCHMIDT RANK AS AN ENTANGLEMENT INDICATOR")
    print("=" * 80)

    examples = {
        "Product": kron(ket_plus(), ket0()),
        "Bell": bell_states()["Phi+"],
        "Partial": normalize(
            3 * computational_basis_state(0, 2)
            + 2 * computational_basis_state(3, 2)
        ),
    }

    for name, state in examples.items():
        coefficients = schmidt_decomposition_two_qubit(state).coefficients
        rank = int(np.sum(coefficients > TOLERANCE))
        print(f"{name:8s}: Schmidt rank = {rank}")


# =============================================================================
# 46. FIDELITY BETWEEN PURE STATES
# =============================================================================

def pure_state_fidelity(
    state_a: np.ndarray,
    state_b: np.ndarray,
) -> float:
    """
    Fidelity between pure states:
        F = |<ψ|φ>|²
    """
    state_a = normalize(state_a)
    state_b = normalize(state_b)

    if len(state_a) != len(state_b):
        raise ValueError("States must have equal dimensions.")

    return float(abs(np.vdot(state_a, state_b)) ** 2)


def fidelity_demo() -> None:
    print("\n" + "=" * 80)
    print("46. PURE-STATE FIDELITY")
    print("=" * 80)

    a = ket0()
    b = ket0()
    c = ket1()
    d = ket_plus()

    print("F(|0>, |0>) =", pure_state_fidelity(a, b))
    print("F(|0>, |1>) =", pure_state_fidelity(a, c))
    print("F(|0>, |+>) =", pure_state_fidelity(a, d))


# =============================================================================
# 47. GLOBAL PHASE VERSUS RELATIVE PHASE
# =============================================================================

def phase_demo() -> None:
    print("\n" + "=" * 80)
    print("47. GLOBAL PHASE AND RELATIVE PHASE")
    print("=" * 80)

    state = ket_plus()

    global_phase = np.exp(1j * math.pi / 3)
    globally_shifted = global_phase * state

    print(
        "Fidelity with global-phase-shifted state:",
        pure_state_fidelity(state, globally_shifted),
    )

    # Relative phase changes the physical state:
    relative_phase_state = normalize(
        ket0() + 1j * ket1()
    )

    print_vector(
        state,
        ["0", "1"],
        "|+>",
    )

    print_vector(
        relative_phase_state,
        ["0", "1"],
        "(|0> + i|1>)/√2",
    )

    print(
        "Fidelity with relative-phase state:",
        pure_state_fidelity(state, relative_phase_state),
    )


# =============================================================================
# 48. ANTI-LINEAR COMPLEX CONJUGATION PITFALL
# =============================================================================

def complex_conjugation_demo() -> None:
    print("\n" + "=" * 80)
    print("48. COMPLEX CONJUGATION IN BRA-KET CALCULATIONS")
    print("=" * 80)

    state = normalize(
        np.array(
            [1 + 1j, 2 - 1j],
            dtype=complex,
        )
    )

    # <ψ| is the conjugate transpose of |ψ>.
    bra = state.conj().T

    print_vector(state, ["0", "1"], "|ψ>")
    print("\nBra <ψ|:", [format_complex(x) for x in bra])

    print(
        "<ψ|ψ> =",
        format_complex(np.vdot(state, state)),
    )

    print(
        "Correct unit norm:",
        np.isclose(np.vdot(state, state).real, 1.0),
    )


# =============================================================================
# 49. MULTI-SYSTEM HAMILTONIANS
# =============================================================================

def multi_system_hamiltonian_demo() -> None:
    print("\n" + "=" * 80)
    print("49. MULTI-SYSTEM HAMILTONIANS")
    print("=" * 80)

    Z = np.array(
        [
            [1, 0],
            [0, -1],
        ],
        dtype=complex,
    )

    I = np.eye(2, dtype=complex)

    # Non-interacting Hamiltonian:
    #
    # H = H_A ⊗ I + I ⊗ H_B
    #
    # Each term acts locally on one subsystem.
    H_A = 0.5 * Z
    H_B = 1.5 * Z

    H_noninteracting = kron(H_A, I) + kron(I, H_B)

    print_matrix(
        H_noninteracting,
        "H_A⊗I + I⊗H_B",
    )

    # An interaction term such as Z⊗Z directly couples the two systems.
    H_interaction = 0.7 * kron(Z, Z)

    H_total = H_noninteracting + H_interaction

    print_matrix(
        H_total,
        "H_total including 0.7 Z⊗Z interaction",
    )


# =============================================================================
# 50. TIME EVOLUTION OF A TWO-QUBIT SYSTEM
# =============================================================================

def matrix_exponential_hermitian(
    hermitian_matrix: np.ndarray,
    time: float,
) -> np.ndarray:
    """
    Compute exp(-i H t) for a Hermitian matrix using eigendecomposition.

    This avoids requiring SciPy for the demonstration.
    """
    H = np.asarray(hermitian_matrix, dtype=complex)

    eigenvalues, eigenvectors = np.linalg.eigh(H)
    phase_factors = np.exp(-1j * eigenvalues * time)

    return (
        eigenvectors
        @ np.diag(phase_factors)
        @ eigenvectors.conj().T
    )


def time_evolution_demo() -> None:
    print("\n" + "=" * 80)
    print("50. MULTI-SYSTEM TIME EVOLUTION")
    print("=" * 80)

    Z = np.array(
        [
            [1, 0],
            [0, -1],
        ],
        dtype=complex,
    )

    H = kron(Z, np.eye(2)) + kron(np.eye(2), Z)

    initial = kron(ket_plus(), ket0())

    U = matrix_exponential_hermitian(H, time=0.75)
    evolved = U @ initial

    print_vector(
        initial,
        ["00", "01", "10", "11"],
        "Initial state",
    )

    print_vector(
        evolved,
        ["00", "01", "10", "11"],
        "Evolved state",
    )

    print("Evolution operator unitary:", is_unitary(U))
    print("State remains normalized:", is_normalized(evolved))


# =============================================================================
# 51. BIPARTITE VERSUS MULTIPARTITE SYSTEMS
# =============================================================================

def bipartite_multipartite_demo() -> None:
    print("\n" + "=" * 80)
    print("51. BIPARTITE AND MULTIPARTITE SYSTEMS")
    print("=" * 80)

    bipartite = kron(ket_plus(), ket1())
    tripartite = kron(ket_plus(), ket1(), ket0())

    print("Bipartite dimension:", len(bipartite))
    print("Tripartite dimension:", len(tripartite))

    print(
        "\nA composite Hilbert space is built as "
        "H_total = H_1 ⊗ H_2 ⊗ ... ⊗ H_n."
    )

    print(
        "The partition of a multipartite system matters. For three qubits, "
        "one can study A|BC, B|AC, or C|AB bipartitions."
    )


# =============================================================================
# 52. GHZ REDUCED STATES
# =============================================================================

def ghz_reduced_state_demo() -> None:
    print("\n" + "=" * 80)
    print("52. GHZ ENTANGLEMENT ACROSS A BIPARTITION")
    print("=" * 80)

    ghz = normalize(
        computational_basis_state(0, 3)
        + computational_basis_state(7, 3)
    )

    rho = density_matrix(ghz)
    first_qubit = partial_trace_three_qubit(rho, trace_out=1)
    entropy = von_neumann_entropy(first_qubit)

    print_matrix(first_qubit, "Reduced state after tracing out qubit 1 and 2")
    print("Entropy of one-qubit reduced state:", entropy)

    print(
        "\nThe GHZ state has strong multipartite correlations, and the "
        "single-qubit reduced state is maximally mixed."
    )


# =============================================================================
# 53. W STATE REDUCED STATE
# =============================================================================

def w_state_reduced_state_demo() -> None:
    print("\n" + "=" * 80)
    print("53. W-STATE REDUCED STATE")
    print("=" * 80)

    w_state = normalize(
        computational_basis_state(1, 3)
        + computational_basis_state(2, 3)
        + computational_basis_state(4, 3)
    )

    rho = density_matrix(w_state)

    first_qubit = partial_trace_three_qubit(rho, trace_out=1)
    entropy = von_neumann_entropy(first_qubit)

    print_matrix(
        first_qubit,
        "Reduced state of the first qubit",
    )
    print("Entropy:", entropy)


# =============================================================================
# 54. ENTANGLEMENT DOES NOT REQUIRE MAXIMAL ENTANGLEMENT
# =============================================================================

def partial_entanglement_demo() -> None:
    print("\n" + "=" * 80)
    print("54. PARTIAL ENTANGLEMENT")
    print("=" * 80)

    # α|00> + β|11> is entangled whenever both α and β are nonzero.
    examples = [
        ("Weakly entangled", normalize(
            3 * computational_basis_state(0, 2)
            + computational_basis_state(3, 2)
        )),
        ("Maximally entangled", bell_states()["Phi+"]),
    ]

    for name, state in examples:
        entropy = von_neumann_entropy(
            partial_trace_two_qubit(
                density_matrix(state),
                trace_out=1,
            )
        )

        print(f"{name}: entropy = {entropy:.6f} bits")


# =============================================================================
# 55. BASIS CHANGE AND TENSOR PRODUCTS
# =============================================================================

def basis_change_demo() -> None:
    print("\n" + "=" * 80)
    print("55. BASIS CHANGES ON MULTI-SYSTEM STATES")
    print("=" * 80)

    H = (1 / math.sqrt(2)) * np.array(
        [
            [1, 1],
            [1, -1],
        ],
        dtype=complex,
    )

    two_qubit_hadamard = kron(H, H)

    state = computational_basis_state(0, 2)
    transformed = two_qubit_hadamard @ state

    print_vector(
        transformed,
        ["00", "01", "10", "11"],
        "(H⊗H)|00>",
    )

    print(
        "\nApplying the same local basis transformation to both subsystems "
        "is represented by H⊗H."
    )


# =============================================================================
# 56. BELL BASIS TRANSFORMATION
# =============================================================================

def bell_basis_demo() -> None:
    print("\n" + "=" * 80)
    print("56. BELL BASIS")
    print("=" * 80)

    states = bell_states()
    bell_basis_matrix = np.column_stack(list(states.values()))

    print(
        "Bell basis matrix is unitary:",
        is_unitary(bell_basis_matrix),
    )

    computational_state = computational_basis_state(0, 2)

    # Coordinates in the Bell basis are obtained by U†|ψ>.
    bell_coordinates = bell_basis_matrix.conj().T @ computational_state

    print_vector(
        bell_coordinates,
        list(states.keys()),
        "Coordinates of |00> in the Bell basis",
    )


# =============================================================================
# 57. TELEPORTATION STATE STRUCTURE
# =============================================================================

def teleportation_state_decomposition_demo() -> None:
    print("\n" + "=" * 80)
    print("57. TELEPORTATION AND TENSOR-PRODUCT STRUCTURE")
    print("=" * 80)

    # Unknown input qubit:
    alpha = 1 / math.sqrt(3)
    beta = math.sqrt(2 / 3) * 1j
    unknown = normalize(np.array([alpha, beta], dtype=complex))

    # Shared Bell pair:
    bell = bell_states()["Phi+"]
    total_state = kron(unknown, bell)

    print_vector(
        unknown,
        ["0", "1"],
        "Unknown input |ψ>",
    )

    print_vector(
        total_state,
        basis_labels(3),
        "|ψ> ⊗ |Φ+>",
    )

    print(
        "\nTeleportation begins with a three-qubit tensor-product state. "
        "The protocol then uses entangling operations and measurement to "
        "transfer the quantum state without physically moving the original qubit."
    )


# =============================================================================
# 58. DENSE REPRESENTATION LIMITATIONS
# =============================================================================

def dense_representation_limitations_demo() -> None:
    print("\n" + "=" * 80)
    print("58. LIMITATIONS OF DENSE STATE REPRESENTATIONS")
    print("=" * 80)

    for n in [20, 25, 30]:
        amplitudes = 2**n
        print(
            f"{n} qubits require {amplitudes:,} complex amplitudes "
            f"in a dense state vector."
        )

    print(
        "\nA dense classical representation becomes impractical as n grows "
        "because tensor-product dimension increases exponentially."
    )

    print(
        "This is a computational-scaling statement, not a claim that every "
        "physical quantum state must be stored explicitly by a quantum computer."
    )


# =============================================================================
# 59. SECURITY AND QUANTUM INFORMATION CONTEXT
# =============================================================================

def quantum_information_security_context() -> None:
    print("\n" + "=" * 80)
    print("59. SECURITY AND INFORMATION-SCIENCE RELEVANCE")
    print("=" * 80)

    print(
        "Tensor-product structure is foundational to quantum cryptography, "
        "quantum communication, quantum error correction, and distributed "
        "quantum information."
    )

    print(
        "Entanglement enables correlations that cannot generally be reproduced "
        "by separable quantum states, while measurement and no-cloning impose "
        "important constraints on information processing."
    )

    print(
        "Implementation note: security claims for a real protocol require "
        "a complete threat model, noise model, authentication assumptions, "
        "and proof or validated analysis. A tensor-product simulation alone "
        "does not establish security."
    )


# =============================================================================
# 60. COMMON IMPLEMENTATION MISTAKES
# =============================================================================

def common_mistakes_demo() -> None:
    print("\n" + "=" * 80)
    print("60. COMMON IMPLEMENTATION MISTAKES")
    print("=" * 80)

    mistakes = [
        (
            "Ignoring tensor-factor ordering",
            "|01> and |10> represent different ordered subsystem states.",
        ),
        (
            "Forgetting normalization",
            "Probabilities are derived from squared amplitudes and must sum to one.",
        ),
        (
            "Using transpose instead of conjugate transpose",
            "A complex bra is the conjugate transpose of a ket.",
        ),
        (
            "Confusing a tensor product with ordinary multiplication",
            "The tensor product expands dimensions rather than producing a scalar.",
        ),
        (
            "Assuming every multi-qubit state is separable",
            "Entangled states cannot generally be decomposed into local factors.",
        ),
        (
            "Confusing classical correlation with entanglement",
            "Mixed separable states can be correlated without being entangled.",
        ),
        (
            "Ignoring numerical tolerance",
            "Floating-point calculations rarely produce exact mathematical zeros.",
        ),
        (
            "Ignoring exponential scaling",
            "Dense state-vector simulation requires 2^n amplitudes for n qubits.",
        ),
    ]

    for mistake, explanation in mistakes:
        print(f"\n{mistake}")
        print(f"  {explanation}")


# =============================================================================
# 61. INTEGRATED WORKED EXAMPLE
# =============================================================================

def integrated_worked_example() -> None:
    print("\n" + "=" * 80)
    print("61. INTEGRATED WORKED EXAMPLE")
    print("=" * 80)

    # Step 1: Build |+0>.
    state = kron(ket_plus(), ket0())

    # Step 2: Entangle the systems using CNOT.
    state = controlled_not() @ state

    # Step 3: Construct the density matrix.
    rho = density_matrix(state)

    # Step 4: Obtain the reduced state of the first subsystem.
    reduced_first = partial_trace_two_qubit(rho, trace_out=1)

    # Step 5: Compute entanglement entropy.
    entropy = von_neumann_entropy(reduced_first)

    # Step 6: Calculate a correlation observable.
    Z = np.array(
        [
            [1, 0],
            [0, -1],
        ],
        dtype=complex,
    )

    zz = kron(Z, Z)
    correlation = expectation_value(state, zz)

    print_vector(
        state,
        ["00", "01", "10", "11"],
        "Final entangled state",
    )

    print_matrix(
        reduced_first,
        "Reduced density matrix of first qubit",
    )

    print(f"Entanglement entropy: {entropy:.6f} bits")
    print(f"<Z⊗Z>: {format_complex(correlation)}")


# =============================================================================
# 62. SELF-TESTS
# =============================================================================

def run_self_tests() -> None:
    print("\n" + "=" * 80)
    print("62. SELF-TESTS")
    print("=" * 80)

    # Tensor-product dimensions.
    assert len(kron(ket0(), ket1())) == 4
    assert len(kron(ket0(), ket1(), ket_plus())) == 8

    # Normalization.
    assert is_normalized(ket0())
    assert is_normalized(ket_plus())
    assert is_normalized(bell_states()["Phi+"])

    # Unitary gates.
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    H = (1 / math.sqrt(2)) * np.array(
        [[1, 1], [1, -1]],
        dtype=complex,
    )

    assert is_unitary(X)
    assert is_unitary(H)
    assert is_unitary(controlled_not())
    assert is_unitary(swap_operator())

    # Product and entangled states.
    product = kron(ket_plus(), ket0())
    bell = bell_states()["Phi+"]

    assert is_product_two_qubit_state(product)
    assert not is_product_two_qubit_state(bell)

    # Partial trace.
    bell_reduced = partial_trace_two_qubit(
        density_matrix(bell),
        trace_out=1,
    )

    expected_maximally_mixed = 0.5 * np.eye(2, dtype=complex)

    assert np.allclose(
        bell_reduced,
        expected_maximally_mixed,
    )

    # Entropy.
    assert np.isclose(
        von_neumann_entropy(bell_reduced),
        1.0,
    )

    # Measurement probabilities.
    probabilities = computational_measurement_probabilities(bell)
    assert np.isclose(sum(probabilities.values()), 1.0)
    assert np.isclose(probabilities["00"], 0.5)
    assert np.isclose(probabilities["11"], 0.5)

    # Tensor matrix identities.
    A = np.diag([2, 3]).astype(complex)
    B = np.diag([5, 7]).astype(complex)

    assert np.isclose(
        np.trace(kron(A, B)),
        np.trace(A) * np.trace(B),
    )

    # CNOT Bell-state preparation.
    prepared = controlled_not() @ (kron(H, np.eye(2)) @ kron(ket0(), ket0()))
    assert np.allclose(prepared, bell)

    # Swap.
    assert np.allclose(
        swap_operator() @ kron(ket0(), ket1()),
        kron(ket1(), ket0()),
    )

    # Fidelity.
    assert np.isclose(pure_state_fidelity(ket0(), ket0()), 1.0)
    assert np.isclose(pure_state_fidelity(ket0(), ket1()), 0.0)

    print("All self-tests passed.")


# =============================================================================
# 63. STUDY CHECKLIST PRINTED BY THE PROGRAM
# =============================================================================

def study_checklist() -> None:
    print("\n" + "=" * 80)
    print("63. CONCEPTUAL CHECKLIST")
    print("=" * 80)

    checklist = [
        "Single-system Hilbert spaces",
        "Tensor-product construction",
        "Subsystem ordering",
        "Product states",
        "General multi-qubit states",
        "Tensor products of operators",
        "Local and global operations",
        "Entangled states",
        "Bell states",
        "GHZ and W states",
        "Density matrices",
        "Partial trace",
        "Reduced states",
        "Measurement probabilities",
        "Conditional state collapse",
        "Schmidt decomposition",
        "Schmidt rank",
        "Entanglement entropy",
        "Mixed states",
        "Classical correlation versus entanglement",
        "Expectation values and correlations",
        "SWAP and controlled operations",
        "Multi-system Hamiltonians",
        "Time evolution",
        "Tensor-product scaling",
        "Numerical stability",
        "Tensor-network motivation",
        "Quantum-information applications",
    ]

    for item in checklist:
        print(f"  [x] {item}")


# =============================================================================
# 64. MAIN PROGRAM
# =============================================================================

def main() -> None:
    """
    Execute the complete educational sequence.

    Each section is intentionally implemented as a function so individual
    examples can also be imported and executed independently.
    """
    np.set_printoptions(
        precision=4,
        suppress=True,
    )

    print("=" * 80)
    print("TENSOR PRODUCTS | MULTI-SYSTEM QUANTUM STATES")
    print("=" * 80)
    print(
        "This program demonstrates the mathematical and computational "
        "structure of composite quantum systems."
    )

    single_qubit_examples()
    tensor_product_basics()
    dimension_growth()
    general_two_qubit_state()
    operator_tensor_products()
    tensor_algebra_properties()
    product_vs_entangled()
    separability_demonstration()
    demonstrate_bell_states()
    create_bell_state_with_gates()
    controlled_gate_demo()
    three_qubit_states()
    general_product_state_demo()
    partial_trace_demo()
    reduced_state_entanglement_demo()
    schmidt_demo()
    entanglement_entropy_demo()
    density_matrix_properties_demo()
    mixed_state_demo()
    measurement_demo()
    measurement_sampling_demo()
    collapse_demo()
    swap_demo()
    local_vs_global_operations_demo()
    operator_schmidt_demo()
    expectation_demo()
    correlation_demo()
    density_tensor_product_demo()
    pure_mixed_distinction_demo()
    density_matrix_dimension_demo()
    partial_trace_three_qubit_demo()
    tensor_ordering_demo()
    tensor_eigenvalue_demo()
    tensor_matrix_identity_demo()
    local_operator_commutator_demo()
    partial_measurement_demo()
    correlation_vs_entanglement_demo()
    swap_test_demo()
    no_cloning_tensor_structure_demo()
    error_handling_demo()
    numerical_stability_demo()
    performance_demo()
    tensor_network_motivation_demo()
    schmidt_rank_demo()
    fidelity_demo()
    phase_demo()
    complex_conjugation_demo()
    multi_system_hamiltonian_demo()
    time_evolution_demo()
    bipartite_multipartite_demo()
    ghz_reduced_state_demo()
    w_state_reduced_state_demo()
    partial_entanglement_demo()
    basis_change_demo()
    bell_basis_demo()
    teleportation_state_decomposition_demo()
    dense_representation_limitations_demo()
    quantum_information_security_context()
    common_mistakes_demo()
    integrated_worked_example()
    run_self_tests()
    study_checklist()

    print("\n" + "=" * 80)
    print("END OF STUDY SCRIPT")
    print("=" * 80)


if __name__ == "__main__":
    main()
