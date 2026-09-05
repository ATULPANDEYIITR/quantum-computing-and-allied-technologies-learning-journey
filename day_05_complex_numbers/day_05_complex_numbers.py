"""
Complex Numbers: Complex Arithmetic and Quantum Amplitudes
============================================================

A comprehensive standalone study script covering complex numbers from
absolute beginner concepts through advanced quantum-amplitude applications.

The script uses only Python's standard library.

Topics covered:
1. Complex-number fundamentals
2. Real and imaginary parts
3. Python complex-number syntax
4. Arithmetic operations
5. Conjugates
6. Modulus and distance in the complex plane
7. Division and numerical stability
8. Polar and exponential forms
9. Euler's formula
10. Powers and roots
11. De Moivre's theorem
12. Complex logarithms
13. Complex exponentials and trigonometric functions
14. Geometry and rotations
15. Numerical edge cases
16. Quantum amplitudes
17. Probability normalization
18. Quantum states and phase
19. Single-qubit amplitudes
20. Superposition
21. Measurement probabilities
22. Global and relative phase
23. Quantum gates as complex transformations
24. Unitary matrices
25. Inner products and orthogonality
26. Bloch-sphere parameterization
27. Multi-qubit amplitudes
28. Tensor-product state construction
29. Entanglement
30. Bell states
31. Measurement simulation
32. Numerical verification
33. Testing and debugging
34. Common mistakes and implementation considerations
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence


# =============================================================================
# SECTION 1: FUNDAMENTAL COMPLEX-NUMBER CONCEPTS
# =============================================================================

def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def show_complex_number(z: complex, label: str = "z") -> None:
    """
    Display the principal properties of a complex number.

    A complex number has the form:

        z = a + bi

    where:
        a = real part
        b = imaginary part
        i = sqrt(-1)
    """
    print(f"{label} = {z}")
    print(f"  real part      = {z.real}")
    print(f"  imaginary part = {z.imag}")
    print(f"  conjugate      = {z.conjugate()}")
    print(f"  modulus        = {abs(z)}")
    print(f"  phase/radian   = {cmath.phase(z)}")


section("1. Complex Numbers: Fundamental Definition")

# Python uses j rather than i for the imaginary unit.
i = 1j

z1 = 3 + 4j
z2 = -2 + 5j

show_complex_number(z1, "z1")
show_complex_number(z2, "z2")

# The imaginary unit satisfies i^2 = -1.
print("\ni^2 =", i ** 2)

# Python also accepts complex() for construction.
constructed = complex(3, 4)
print("complex(3, 4) =", constructed)


# =============================================================================
# SECTION 2: REAL AND IMAGINARY COMPONENTS
# =============================================================================

section("2. Real and Imaginary Components")

a = 7
b = -3
z = complex(a, b)

print("z =", z)
print("Re(z) =", z.real)
print("Im(z) =", z.imag)

# A purely real value can be represented as a complex number.
purely_real = complex(8, 0)

# A purely imaginary value has zero real component.
purely_imaginary = complex(0, 8)

print("Purely real:", purely_real)
print("Purely imaginary:", purely_imaginary)


# =============================================================================
# SECTION 3: BASIC ARITHMETIC
# =============================================================================

section("3. Complex Arithmetic")

z1 = 3 + 4j
z2 = 1 - 2j

print("z1 =", z1)
print("z2 =", z2)
print("Addition       =", z1 + z2)
print("Subtraction    =", z1 - z2)
print("Multiplication =", z1 * z2)
print("Division       =", z1 / z2)
print("Power          =", z1 ** 2)

# Multiplication illustrates:
#
# (a + bi)(c + di)
# = ac + adi + bci + bd i^2
# = (ac - bd) + (ad + bc)i
#
# because i^2 = -1.

product = z1 * z2
expected_product = (z1.real * z2.real - z1.imag * z2.imag) + (
    z1.real * z2.imag + z1.imag * z2.real
) * 1j

print("Manual multiplication =", expected_product)
print("Matches Python:", math.isclose(product.real, expected_product.real) and
      math.isclose(product.imag, expected_product.imag))


# =============================================================================
# SECTION 4: CONJUGATES
# =============================================================================

section("4. Complex Conjugates")

z = 3 + 4j
z_conjugate = z.conjugate()

print("z =", z)
print("conjugate(z) =", z_conjugate)

# Important identity:
#
# z * conjugate(z) = |z|^2

print("z * conjugate(z) =", z * z_conjugate)
print("|z|^2 =", abs(z) ** 2)

# Conjugation changes the sign of the imaginary component.
assert z_conjugate == 3 - 4j


# =============================================================================
# SECTION 5: MODULUS AND GEOMETRY
# =============================================================================

section("5. Modulus and the Complex Plane")

z = 3 + 4j

# The modulus is:
#
# |z| = sqrt(a^2 + b^2)

manual_modulus = math.sqrt(z.real ** 2 + z.imag ** 2)

print("|z| using abs() =", abs(z))
print("|z| manually    =", manual_modulus)

# Geometrically, the modulus is the distance from the origin.
point_a = 1 + 2j
point_b = 4 + 6j

distance = abs(point_b - point_a)

print("Point A =", point_a)
print("Point B =", point_b)
print("Distance A -> B =", distance)


# =============================================================================
# SECTION 6: DIVISION
# =============================================================================

section("6. Complex Division")

z1 = 5 + 3j
z2 = 2 - 1j

result = z1 / z2

print("z1 / z2 =", result)

# Algebraically:
#
# z1 / z2
# = z1 * conjugate(z2) / (z2 * conjugate(z2))
#
# The denominator becomes a real number.

manual_division = z1 * z2.conjugate() / (abs(z2) ** 2)

print("Manual division =", manual_division)

# Division by zero is invalid.
try:
    print((1 + 2j) / 0j)
except ZeroDivisionError as error:
    print("Division by zero:", error)


# =============================================================================
# SECTION 7: POLAR FORM
# =============================================================================

section("7. Polar Form")

z = 1 + 1j

r = abs(z)
theta = cmath.phase(z)

print("z =", z)
print("Magnitude r =", r)
print("Angle theta =", theta)

# Polar form:
#
# z = r(cos(theta) + i sin(theta))

polar_reconstruction = r * (
    math.cos(theta) + 1j * math.sin(theta)
)

print("Polar reconstruction =", polar_reconstruction)

# Floating-point arithmetic may introduce tiny differences.
print("Approximately equal:",
      abs(z - polar_reconstruction) < 1e-12)


# =============================================================================
# SECTION 8: EXPONENTIAL FORM AND EULER'S FORMULA
# =============================================================================

section("8. Euler's Formula")

# Euler's formula:
#
# e^(i theta) = cos(theta) + i sin(theta)

theta = math.pi / 3

left_side = cmath.exp(1j * theta)
right_side = math.cos(theta) + 1j * math.sin(theta)

print("exp(i*theta) =", left_side)
print("cos(theta) + i sin(theta) =", right_side)

print(
    "Euler identity verified:",
    abs(left_side - right_side) < 1e-12
)

# The famous identity:
#
# e^(i*pi) + 1 = 0

euler_identity = cmath.exp(1j * math.pi) + 1

print("e^(i*pi) + 1 =", euler_identity)


# =============================================================================
# SECTION 9: ARGUMENT AND PHASE
# =============================================================================

section("9. Argument and Phase")

numbers = [
    1 + 0j,
    0 + 1j,
    -1 + 0j,
    0 - 1j,
    1 + 1j,
    -1 + 1j,
]

for number in numbers:
    print(
        f"{number:>8} -> magnitude={abs(number):.6f}, "
        f"phase={cmath.phase(number):.6f} radians"
    )

# The principal argument is normally returned in the interval (-pi, pi].
#
# Therefore, equivalent angles can have different numerical
# representations because angles repeat every 2*pi.


# =============================================================================
# SECTION 10: POWERS AND DE MOIVRE'S THEOREM
# =============================================================================

section("10. Powers of Complex Numbers")

z = 2 * cmath.exp(1j * math.pi / 4)
n = 5

python_power = z ** n

# De Moivre's theorem:
#
# [r(cos(theta) + i sin(theta))]^n
# = r^n [cos(n*theta) + i sin(n*theta)]

r = abs(z)
theta = cmath.phase(z)

de_moivre_power = (r ** n) * (
    math.cos(n * theta) + 1j * math.sin(n * theta)
)

print("Python power       =", python_power)
print("De Moivre result   =", de_moivre_power)
print(
    "Agreement:",
    abs(python_power - de_moivre_power) < 1e-10
)


# =============================================================================
# SECTION 11: ROOTS OF COMPLEX NUMBERS
# =============================================================================

section("11. Complex Roots")

def complex_nth_roots(z: complex, n: int) -> list[complex]:
    """
    Return all n distinct complex nth roots of z.

    If:
        z = r * exp(i*theta)

    then the roots are:

        r^(1/n) * exp(i*(theta + 2*pi*k)/n)

    for k = 0, 1, ..., n-1.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")

    if z == 0:
        return [0j for _ in range(n)]

    r = abs(z)
    theta = cmath.phase(z)
    root_radius = r ** (1 / n)

    roots = []

    for k in range(n):
        root_angle = (theta + 2 * math.pi * k) / n
        root = root_radius * cmath.exp(1j * root_angle)
        roots.append(root)

    return roots


z = 1 + 0j
roots = complex_nth_roots(z, 4)

for index, root in enumerate(roots):
    print(f"Fourth root {index}: {root}")
    print(f"  root^4 = {root ** 4}")


# =============================================================================
# SECTION 12: COMPLEX EXPONENTIAL, LOGARITHM, TRIGONOMETRY
# =============================================================================

section("12. Advanced Complex Functions")

z = 1 + 2j

print("z =", z)
print("exp(z) =", cmath.exp(z))
print("log(z) =", cmath.log(z))
print("sqrt(z) =", cmath.sqrt(z))
print("sin(z) =", cmath.sin(z))
print("cos(z) =", cmath.cos(z))
print("tan(z) =", cmath.tan(z))

# Complex logarithms are multivalued mathematically:
#
# log(z) = ln(r) + i(theta + 2*pi*k)
#
# Python's cmath.log returns the principal branch.

principal_log = cmath.log(z)
print("Principal logarithm =", principal_log)

# A principal logarithm does not represent every possible logarithm.
# Adding 2*pi*i*k gives other branches.

for k in range(-2, 3):
    branch = math.log(abs(z)) + 1j * (
        cmath.phase(z) + 2 * math.pi * k
    )
    print(f"Logarithm branch k={k}: {branch}")


# =============================================================================
# SECTION 13: COMPLEX GEOMETRIC TRANSFORMATIONS
# =============================================================================

section("13. Rotation Using Complex Multiplication")

point = 1 + 0j
rotation_angle = math.pi / 2

rotation_factor = cmath.exp(1j * rotation_angle)
rotated_point = point * rotation_factor

print("Original point =", point)
print("Rotation factor =", rotation_factor)
print("Rotated point =", rotated_point)

# Multiplication by exp(i*theta) rotates a complex number
# counterclockwise by theta radians without changing its magnitude.

print("Original magnitude =", abs(point))
print("Rotated magnitude  =", abs(rotated_point))


def rotate(z: complex, angle_radians: float) -> complex:
    """Rotate z counterclockwise by the specified angle."""
    return z * cmath.exp(1j * angle_radians)


for angle_degrees in [0, 90, 180, 270]:
    angle = math.radians(angle_degrees)
    print(
        f"{angle_degrees:>3} degrees ->",
        rotate(1 + 0j, angle)
    )


# =============================================================================
# SECTION 14: NUMERICAL COMPARISONS
# =============================================================================

section("14. Floating-Point Precision")

a = cmath.exp(1j * math.pi)
expected = -1 + 0j

print("Computed:", a)
print("Expected:", expected)
print("Exact equality:", a == expected)
print("Approximate equality:", abs(a - expected) < 1e-12)

# Floating-point values should normally be compared with a tolerance.

def complex_is_close(
    a: complex,
    b: complex,
    *,
    relative_tolerance: float = 1e-9,
    absolute_tolerance: float = 1e-12,
) -> bool:
    """Compare complex numbers using magnitude-based tolerance."""
    difference = abs(a - b)
    scale = max(abs(a), abs(b))

    return difference <= max(
        absolute_tolerance,
        relative_tolerance * scale,
    )


print(
    complex_is_close(
        cmath.exp(1j * math.pi),
        -1 + 0j
    )
)


# =============================================================================
# SECTION 15: COMPLEX POLYNOMIAL EVALUATION
# =============================================================================

section("15. Evaluating Polynomials with Complex Numbers")

def evaluate_polynomial(
    coefficients: Sequence[complex],
    x: complex,
) -> complex:
    """
    Evaluate a polynomial using Horner's method.

    coefficients are ordered from highest degree to constant term.

    Example:
        [2, 3, 4]
    represents:
        2x^2 + 3x + 4
    """
    result = 0j

    for coefficient in coefficients:
        result = result * x + coefficient

    return result


coefficients = [2, 3, 4]
x = 1 + 2j

print("Polynomial value =", evaluate_polynomial(coefficients, x))


# =============================================================================
# SECTION 16: FINDING ROOTS BY DIRECT FACTORIZATION
# =============================================================================

section("16. Polynomial Roots and Complex Numbers")

# x^2 + 1 = 0
#
# Its roots are:
# x = +i and x = -i

roots = [1j, -1j]

for root in roots:
    value = evaluate_polynomial([1, 0, 1], root)
    print(f"x = {root}, polynomial(x) = {value}")


# =============================================================================
# SECTION 17: QUANTUM AMPLITUDES
# =============================================================================

section("17. Quantum Amplitudes: Why Complex Numbers Matter")

# A quantum state can use complex numbers as amplitudes.
#
# For a single qubit:
#
# |psi> = alpha|0> + beta|1>
#
# where alpha and beta are complex amplitudes.
#
# A valid normalized state satisfies:
#
# |alpha|^2 + |beta|^2 = 1

alpha = 1 / math.sqrt(2)
beta = 1j / math.sqrt(2)

normalization = abs(alpha) ** 2 + abs(beta) ** 2

print("alpha =", alpha)
print("beta  =", beta)
print("|alpha|^2 =", abs(alpha) ** 2)
print("|beta|^2  =", abs(beta) ** 2)
print("Normalization =", normalization)


# =============================================================================
# SECTION 18: QUANTUM STATE REPRESENTATION
# =============================================================================

section("18. A Single-Qubit State Class")

@dataclass
class QubitState:
    """
    Represent a normalized single-qubit state.

    State:
        alpha|0> + beta|1>

    alpha and beta may be complex.
    """

    alpha: complex
    beta: complex

    def norm_squared(self) -> float:
        """Return the squared norm of the state."""
        return abs(self.alpha) ** 2 + abs(self.beta) ** 2

    def norm(self) -> float:
        """Return the Euclidean norm."""
        return math.sqrt(self.norm_squared())

    def is_normalized(self, tolerance: float = 1e-10) -> bool:
        """Check whether the state has norm approximately one."""
        return math.isclose(
            self.norm_squared(),
            1.0,
            rel_tol=tolerance,
            abs_tol=tolerance,
        )

    def normalize(self) -> QubitState:
        """Return a normalized copy of the state."""
        magnitude = self.norm()

        if magnitude == 0:
            raise ValueError("The zero vector cannot be normalized.")

        return QubitState(
            self.alpha / magnitude,
            self.beta / magnitude,
        )

    def probabilities(self) -> tuple[float, float]:
        """Return measurement probabilities for |0> and |1>."""
        return (
            abs(self.alpha) ** 2,
            abs(self.beta) ** 2,
        )

    def global_phase_removed(self) -> QubitState:
        """
        Remove the global phase by making the first nonzero amplitude
        real and nonnegative.

        Global phase does not affect measurement probabilities.
        """
        if abs(self.alpha) > 1e-15:
            phase = cmath.phase(self.alpha)
        elif abs(self.beta) > 1e-15:
            phase = cmath.phase(self.beta)
        else:
            raise ValueError("The zero state has no defined global phase.")

        factor = cmath.exp(-1j * phase)

        return QubitState(
            self.alpha * factor,
            self.beta * factor,
        )


state = QubitState(
    1 / math.sqrt(2),
    1j / math.sqrt(2),
)

print("State =", state)
print("Norm squared =", state.norm_squared())
print("Normalized =", state.is_normalized())
print("Probabilities =", state.probabilities())


# =============================================================================
# SECTION 19: NORMALIZATION
# =============================================================================

section("19. Quantum-State Normalization")

unnormalized = QubitState(2 + 1j, 3 - 2j)

print("Before normalization:")
print("  norm =", unnormalized.norm())
print("  probabilities-like magnitudes =", unnormalized.probabilities())

normalized = unnormalized.normalize()

print("After normalization:")
print("  state =", normalized)
print("  norm =", normalized.norm())
print("  probabilities =", normalized.probabilities())
print("  normalized =", normalized.is_normalized())


# =============================================================================
# SECTION 20: MEASUREMENT PROBABILITIES
# =============================================================================

section("20. Measurement Probabilities")

state = QubitState(
    1 / math.sqrt(3),
    math.sqrt(2 / 3) * 1j,
)

p0, p1 = state.probabilities()

print("P(0) =", p0)
print("P(1) =", p1)
print("P(0) + P(1) =", p0 + p1)

# Probability is based on squared magnitude, not the amplitude itself.
#
# Incorrect:
#     probability = alpha
#
# Correct:
#     probability = |alpha|^2


# =============================================================================
# SECTION 21: PHASE
# =============================================================================

section("21. Global Phase and Relative Phase")

state_a = QubitState(
    1 / math.sqrt(2),
    1 / math.sqrt(2),
)

global_phase = cmath.exp(1j * math.pi / 3)

state_b = QubitState(
    global_phase * state_a.alpha,
    global_phase * state_a.beta,
)

print("State A probabilities =", state_a.probabilities())
print("State B probabilities =", state_b.probabilities())

print(
    "Global phase changes probabilities:",
    state_a.probabilities() != state_b.probabilities()
)

# The relative phase between amplitudes can affect interference.
state_c = QubitState(
    1 / math.sqrt(2),
    -1 / math.sqrt(2),
)

print("State C probabilities =", state_c.probabilities())


# =============================================================================
# SECTION 22: QUANTUM INNER PRODUCT
# =============================================================================

section("22. Inner Products")

def inner_product(
    vector_a: Sequence[complex],
    vector_b: Sequence[complex],
) -> complex:
    """
    Compute <a|b>.

    The first vector is complex-conjugated.

        <a|b> = sum(conj(a_i) * b_i)
    """
    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have equal dimensions.")

    return sum(
        a.conjugate() * b
        for a, b in zip(vector_a, vector_b)
    )


ket_zero = [1 + 0j, 0 + 0j]
ket_one = [0 + 0j, 1 + 0j]

print("<0|0> =", inner_product(ket_zero, ket_zero))
print("<1|1> =", inner_product(ket_one, ket_one))
print("<0|1> =", inner_product(ket_zero, ket_one))

# Orthogonality means:
#
# <a|b> = 0


# =============================================================================
# SECTION 23: VECTOR NORMS
# =============================================================================

section("23. Quantum State Vectors")

def vector_norm_squared(vector: Sequence[complex]) -> float:
    """Return the squared norm of a complex vector."""
    return sum(abs(value) ** 2 for value in vector)


def normalize_vector(vector: Sequence[complex]) -> list[complex]:
    """Normalize a complex vector."""
    norm_squared = vector_norm_squared(vector)

    if norm_squared == 0:
        raise ValueError("Cannot normalize the zero vector.")

    norm = math.sqrt(norm_squared)

    return [value / norm for value in vector]


vector = [1 + 1j, 2 - 1j, 3 + 0j]

print("Original norm squared =", vector_norm_squared(vector))

normalized_vector = normalize_vector(vector)

print("Normalized vector =", normalized_vector)
print(
    "Normalized norm squared =",
    vector_norm_squared(normalized_vector),
)


# =============================================================================
# SECTION 24: QUANTUM GATES AS MATRICES
# =============================================================================

section("24. Quantum Gates and Complex Matrices")

# A quantum gate can be represented by a complex matrix.
#
# The Hadamard gate is:
#
# H = 1/sqrt(2) [[1,  1],
#                [1, -1]]
#
# Applying H to |0> creates:
#
# (|0> + |1>) / sqrt(2)

SQRT2_INV = 1 / math.sqrt(2)

H = [
    [SQRT2_INV + 0j, SQRT2_INV + 0j],
    [SQRT2_INV + 0j, -SQRT2_INV + 0j],
]

X = [
    [0j, 1 + 0j],
    [1 + 0j, 0j],
]

Y = [
    [0j, -1j],
    [1j, 0j],
]

Z = [
    [1 + 0j, 0j],
    [0j, -1 + 0j],
]


def matrix_vector_multiply(
    matrix: Sequence[Sequence[complex]],
    vector: Sequence[complex],
) -> list[complex]:
    """Multiply a matrix by a vector."""
    if not matrix:
        raise ValueError("Matrix cannot be empty.")

    columns = len(matrix[0])

    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal length.")

    if len(vector) != columns:
        raise ValueError("Matrix and vector dimensions do not match.")

    return [
        sum(
            matrix[row][column] * vector[column]
            for column in range(columns)
        )
        for row in range(len(matrix))
    ]


ket0 = [1 + 0j, 0 + 0j]

hadamard_ket0 = matrix_vector_multiply(H, ket0)

print("H|0> =", hadamard_ket0)

print(
    "Probabilities after H:",
    [abs(amplitude) ** 2 for amplitude in hadamard_ket0],
)


# =============================================================================
# SECTION 25: MATRIX OPERATIONS
# =============================================================================

section("25. Complex Matrix Operations")

def matrix_conjugate_transpose(
    matrix: Sequence[Sequence[complex]],
) -> list[list[complex]]:
    """Return the conjugate transpose (Hermitian adjoint)."""
    if not matrix:
        return []

    rows = len(matrix)
    columns = len(matrix[0])

    if any(len(row) != columns for row in matrix):
        raise ValueError("Matrix rows must have equal length.")

    return [
        [
            matrix[row][column].conjugate()
            for row in range(rows)
        ]
        for column in range(columns)
    ]


def matrix_multiply(
    matrix_a: Sequence[Sequence[complex]],
    matrix_b: Sequence[Sequence[complex]],
) -> list[list[complex]]:
    """Multiply two compatible matrices."""
    if not matrix_a or not matrix_b:
        raise ValueError("Matrices cannot be empty.")

    a_columns = len(matrix_a[0])
    b_columns = len(matrix_b[0])

    if any(len(row) != a_columns for row in matrix_a):
        raise ValueError("Matrix A is not rectangular.")

    if any(len(row) != b_columns for row in matrix_b):
        raise ValueError("Matrix B is not rectangular.")

    if a_columns != len(matrix_b):
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        [
            sum(
                matrix_a[i][k] * matrix_b[k][j]
                for k in range(a_columns)
            )
            for j in range(b_columns)
        ]
        for i in range(len(matrix_a))
    ]


def matrices_are_close(
    matrix_a: Sequence[Sequence[complex]],
    matrix_b: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> bool:
    """Compare matrices using complex numerical tolerance."""
    if len(matrix_a) != len(matrix_b):
        return False

    for row_a, row_b in zip(matrix_a, matrix_b):
        if len(row_a) != len(row_b):
            return False

        for value_a, value_b in zip(row_a, row_b):
            if abs(value_a - value_b) > tolerance:
                return False

    return True


H_adjoint = matrix_conjugate_transpose(H)
identity = matrix_multiply(H_adjoint, H)

expected_identity = [
    [1 + 0j, 0 + 0j],
    [0 + 0j, 1 + 0j],
]

print("H†H =", identity)
print("H is unitary:", matrices_are_close(identity, expected_identity))


# =============================================================================
# SECTION 26: UNITARY MATRICES
# =============================================================================

section("26. Unitary Transformations")

def is_unitary(
    matrix: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> bool:
    """
    Check whether a square matrix is unitary.

    A matrix U is unitary when:

        U†U = I
    """
    if not matrix:
        return False

    size = len(matrix)

    if any(len(row) != size for row in matrix):
        return False

    adjoint = matrix_conjugate_transpose(matrix)
    product = matrix_multiply(adjoint, matrix)

    identity_matrix = [
        [
            1 + 0j if row == column else 0j
            for column in range(size)
        ]
        for row in range(size)
    ]

    return matrices_are_close(
        product,
        identity_matrix,
        tolerance,
    )


for name, gate in {
    "X": X,
    "Y": Y,
    "Z": Z,
    "H": H,
}.items():
    print(f"{name} unitary:", is_unitary(gate))


# =============================================================================
# SECTION 27: BLOCH-SPHERE PARAMETERIZATION
# =============================================================================

section("27. Bloch-Sphere Parameterization")

def qubit_from_bloch_angles(
    theta: float,
    phi: float,
) -> QubitState:
    """
    Construct a pure qubit state:

        cos(theta/2)|0> +
        exp(i*phi) sin(theta/2)|1>

    theta determines polar position.
    phi determines azimuthal phase.
    """
    alpha = math.cos(theta / 2)
    beta = cmath.exp(1j * phi) * math.sin(theta / 2)

    return QubitState(alpha, beta)


north_pole = qubit_from_bloch_angles(0, 0)
equator = qubit_from_bloch_angles(math.pi / 2, math.pi / 2)
south_pole = qubit_from_bloch_angles(math.pi, 0)

print("North pole =", north_pole)
print("Equator state =", equator)
print("South pole =", south_pole)

print("North probabilities =", north_pole.probabilities())
print("Equator probabilities =", equator.probabilities())
print("South probabilities =", south_pole.probabilities())


# =============================================================================
# SECTION 28: TENSOR PRODUCTS
# =============================================================================

section("28. Tensor Products and Multi-Qubit States")

def tensor_product(
    vector_a: Sequence[complex],
    vector_b: Sequence[complex],
) -> list[complex]:
    """
    Compute the tensor/Kronecker product of two vectors.

    If:
        a = [a0, a1]
        b = [b0, b1]

    then:
        a ⊗ b =
        [a0*b0, a0*b1, a1*b0, a1*b1]
    """
    return [
        value_a * value_b
        for value_a in vector_a
        for value_b in vector_b
    ]


ket0 = [1 + 0j, 0 + 0j]
ket1 = [0 + 0j, 1 + 0j]

ket00 = tensor_product(ket0, ket0)
ket01 = tensor_product(ket0, ket1)
ket10 = tensor_product(ket1, ket0)
ket11 = tensor_product(ket1, ket1)

print("|00> =", ket00)
print("|01> =", ket01)
print("|10> =", ket10)
print("|11> =", ket11)


# =============================================================================
# SECTION 29: MULTI-QUBIT AMPLITUDES
# =============================================================================

section("29. Two-Qubit Superposition")

one_qubit_plus = [
    1 / math.sqrt(2),
    1 / math.sqrt(2),
]

two_qubit_plus = tensor_product(
    one_qubit_plus,
    one_qubit_plus,
)

print("Two-qubit |++> state:")
for basis_state, amplitude in zip(
    ["00", "01", "10", "11"],
    two_qubit_plus,
):
    print(
        f"  |{basis_state}> amplitude={amplitude}, "
        f"probability={abs(amplitude) ** 2}"
    )

print(
    "Total probability =",
    sum(abs(amplitude) ** 2 for amplitude in two_qubit_plus)
)


# =============================================================================
# SECTION 30: BELL STATE AND ENTANGLEMENT
# =============================================================================

section("30. Bell State")

# One Bell state is:
#
# |Phi+> = (|00> + |11>) / sqrt(2)
#
# Its amplitude vector is:
#
# [1/sqrt(2), 0, 0, 1/sqrt(2)]

bell_phi_plus = [
    1 / math.sqrt(2),
    0j,
    0j,
    1 / math.sqrt(2),
]

for basis_state, amplitude in zip(
    ["00", "01", "10", "11"],
    bell_phi_plus,
):
    print(
        f"|{basis_state}>: amplitude={amplitude}, "
        f"probability={abs(amplitude) ** 2}"
    )

print(
    "Bell-state normalization =",
    vector_norm_squared(bell_phi_plus),
)


# =============================================================================
# SECTION 31: PRODUCT-STATE TEST FOR TWO QUBITS
# =============================================================================

section("31. Detecting a Simple Form of Two-Qubit Entanglement")

def is_product_state_two_qubit(
    state: Sequence[complex],
    tolerance: float = 1e-10,
) -> bool:
    """
    Determine whether a two-qubit state is separable.

    For amplitudes:
        [a, b, c, d]

    a two-qubit pure state is a product state exactly when:

        a*d - b*c = 0

    up to numerical tolerance.

    This criterion applies to a normalized pure two-qubit state.
    """
    if len(state) != 4:
        raise ValueError("A two-qubit state must have four amplitudes.")

    determinant = state[0] * state[3] - state[1] * state[2]

    return abs(determinant) <= tolerance


product_state = [
    value
    for value in tensor_product(
        one_qubit_plus,
        one_qubit_plus,
    )
]

print(
    "Product state is separable:",
    is_product_state_two_qubit(product_state)
)

print(
    "Bell state is separable:",
    is_product_state_two_qubit(bell_phi_plus)
)


# =============================================================================
# SECTION 32: QUANTUM MEASUREMENT SIMULATION
# =============================================================================

section("32. Quantum Measurement Simulation")

def validate_probability_distribution(
    probabilities: Sequence[float],
    tolerance: float = 1e-10,
) -> None:
    """Validate a probability distribution."""
    if any(
        probability < -tolerance
        for probability in probabilities
    ):
        raise ValueError("Probabilities cannot be negative.")

    total = sum(probabilities)

    if not math.isclose(
        total,
        1.0,
        rel_tol=tolerance,
        abs_tol=tolerance,
    ):
        raise ValueError(
            f"Probabilities must sum to 1, got {total}."
        )


def sample_measurement(
    amplitudes: Sequence[complex],
    rng: random.Random | None = None,
) -> int:
    """
    Simulate a measurement in the computational basis.

    The probability of index i is |amplitude_i|^2.
    """
    if not amplitudes:
        raise ValueError("At least one amplitude is required.")

    probabilities = [
        abs(amplitude) ** 2
        for amplitude in amplitudes
    ]

    validate_probability_distribution(probabilities)

    generator = rng if rng is not None else random

    random_value = generator.random()
    cumulative = 0.0

    for index, probability in enumerate(probabilities):
        cumulative += probability

        if random_value < cumulative:
            return index

    # Protect against floating-point accumulation near 1.0.
    return len(probabilities) - 1


rng = random.Random(42)

state = [
    1 / math.sqrt(2),
    1j / math.sqrt(2),
]

counts = [0, 0]

for _ in range(10000):
    result = sample_measurement(state, rng)
    counts[result] += 1

print("Measurement counts:", counts)
print(
    "Estimated probabilities:",
    [count / sum(counts) for count in counts],
)


# =============================================================================
# SECTION 33: INTERFERENCE
# =============================================================================

section("33. Interference and Complex Amplitudes")

# Complex amplitudes can add before probabilities are calculated.
#
# For amplitudes A and B:
#
# Probability is |A + B|^2
#
# which contains cross terms:
#
# |A|^2 + |B|^2 + 2 Re(A*conj(B))
#
# Those cross terms produce constructive or destructive interference.

amplitude_a = 1 / math.sqrt(2)
amplitude_b = 1 / math.sqrt(2)

constructive = amplitude_a + amplitude_b
destructive = amplitude_a - amplitude_b

print("Constructive amplitude =", constructive)
print("Constructive probability =", abs(constructive) ** 2)

print("Destructive amplitude =", destructive)
print("Destructive probability =", abs(destructive) ** 2)

# The result is fundamentally different from adding probabilities first.


# =============================================================================
# SECTION 34: PHASE-DEPENDENT INTERFERENCE
# =============================================================================

section("34. Relative Phase and Interference")

magnitude = 1 / math.sqrt(2)

for phase in [
    0,
    math.pi / 4,
    math.pi / 2,
    math.pi,
    3 * math.pi / 2,
]:
    first = magnitude
    second = magnitude * cmath.exp(1j * phase)

    combined = first + second

    print(
        f"phase={phase:.4f}, "
        f"amplitude={combined:.6f}, "
        f"probability={abs(combined) ** 2:.6f}"
    )


# =============================================================================
# SECTION 35: QUANTUM GATE SEQUENCES
# =============================================================================

section("35. Applying a Sequence of Quantum Gates")

def apply_gate(
    gate: Sequence[Sequence[complex]],
    state: Sequence[complex],
) -> list[complex]:
    """Apply a quantum gate to a state vector."""
    if not is_unitary(gate):
        raise ValueError("The supplied gate is not unitary.")

    return matrix_vector_multiply(gate, state)


state = [1 + 0j, 0 + 0j]

print("Initial |0> =", state)

state = apply_gate(H, state)
print("After H =", state)

state = apply_gate(H, state)
print("After H again =", state)

# H applied twice is the identity:
#
# H^2 = I

print(
    "Recovered |0>:",
    complex_is_close(state[0], 1 + 0j)
    and complex_is_close(state[1], 0 + 0j)
)


# =============================================================================
# SECTION 36: PHASE GATES
# =============================================================================

section("36. Phase Gates")

S = [
    [1 + 0j, 0j],
    [0j, 1j],
]

T = [
    [1 + 0j, 0j],
    [0j, cmath.exp(1j * math.pi / 4)],
]

for name, gate in {
    "S": S,
    "T": T,
}.items():
    print(f"{name} unitary:", is_unitary(gate))

state = apply_gate(H, ket0)
print("H|0> =", state)

phase_state = apply_gate(S, state)

print("S(H|0>) =", phase_state)
print(
    "Measurement probabilities:",
    [abs(value) ** 2 for value in phase_state]
)


# =============================================================================
# SECTION 37: ADJOINT AND UNITARITY
# =============================================================================

section("37. Adjoint, Norm Preservation, and Unitarity")

original = normalize_vector([1 + 2j, 3 - 4j])

transformed = matrix_vector_multiply(H, original)

print("Original state =", original)
print("Transformed state =", transformed)

print(
    "Original norm squared =",
    vector_norm_squared(original)
)

print(
    "Transformed norm squared =",
    vector_norm_squared(transformed)
)

# Unitary transformations preserve inner products and therefore norms.


# =============================================================================
# SECTION 38: EXPECTATION VALUE OF A QUBIT OBSERVABLE
# =============================================================================

section("38. Expectation Values")

def matrix_vector_inner_product(
    vector: Sequence[complex],
    matrix: Sequence[Sequence[complex]],
) -> complex:
    """
    Calculate <v|M|v>.
    """
    transformed = matrix_vector_multiply(matrix, vector)
    return inner_product(vector, transformed)


state = [
    1 / math.sqrt(2),
    1 / math.sqrt(2),
]

expectation_z = matrix_vector_inner_product(state, Z)

print("<Z> =", expectation_z)

# For a Hermitian observable, expectation values should be real,
# apart from tiny floating-point error.


# =============================================================================
# SECTION 39: HERMITIAN MATRICES
# =============================================================================

section("39. Hermitian Matrices")

def is_hermitian(
    matrix: Sequence[Sequence[complex]],
    tolerance: float = 1e-10,
) -> bool:
    """Check whether M = M†."""
    if not matrix:
        return False

    if any(len(row) != len(matrix) for row in matrix):
        return False

    adjoint = matrix_conjugate_transpose(matrix)

    return matrices_are_close(
        matrix,
        adjoint,
        tolerance,
    )


print("X Hermitian:", is_hermitian(X))
print("Y Hermitian:", is_hermitian(Y))
print("Z Hermitian:", is_hermitian(Z))
print("H Hermitian:", is_hermitian(H))


# =============================================================================
# SECTION 40: EDGE CASES
# =============================================================================

section("40. Important Edge Cases")

edge_cases = [
    0j,
    1 + 0j,
    -1 + 0j,
    0 + 1j,
    0 - 1j,
    complex(1e-15, -1e-15),
]

for value in edge_cases:
    print(
        f"z={value!r}, "
        f"abs(z)={abs(value):.16g}, "
        f"phase(z)={cmath.phase(value):.16g}"
    )

# The phase of zero is mathematically undefined.
# Python returns 0.0 for cmath.phase(0j).
#
# Code that relies on phase should therefore explicitly handle zero.


def safe_phase(z: complex) -> float:
    """
    Return the phase of a nonzero complex number.

    Zero has no mathematically defined argument.
    """
    if z == 0:
        raise ValueError("The phase of zero is undefined.")

    return cmath.phase(z)


try:
    safe_phase(0j)
except ValueError as error:
    print("safe_phase(0j):", error)


# =============================================================================
# SECTION 41: COMPLEX PARSING
# =============================================================================

section("41. Parsing Complex Numbers")

valid_strings = [
    "3+4j",
    "3-4j",
    "5j",
    "-2j",
    "7",
    "1.5+2.5j",
]

for text in valid_strings:
    try:
        parsed = complex(text)
        print(f"{text!r} -> {parsed}")
    except ValueError as error:
        print(f"{text!r} -> invalid: {error}")


# =============================================================================
# SECTION 42: ERROR HANDLING
# =============================================================================

section("42. Validation and Error Handling")

def require_normalized_state(
    state: Sequence[complex],
    tolerance: float = 1e-10,
) -> None:
    """Raise an error when a state is not normalized."""
    norm_squared = vector_norm_squared(state)

    if not math.isclose(
        norm_squared,
        1.0,
        rel_tol=tolerance,
        abs_tol=tolerance,
    ):
        raise ValueError(
            f"State is not normalized. Norm squared = {norm_squared}"
        )


try:
    require_normalized_state([1 + 0j, 1 + 0j])
except ValueError as error:
    print("Validation error:", error)

require_normalized_state(ket0)
print("Valid normalized state accepted.")


# =============================================================================
# SECTION 43: PERFORMANCE CONSIDERATIONS
# =============================================================================

section("43. Performance Considerations")

# A state vector for n qubits contains 2^n amplitudes.
#
# Therefore:
#
#   1 qubit  -> 2 amplitudes
#   2 qubits -> 4 amplitudes
#   10 qubits -> 1,024 amplitudes
#   20 qubits -> 1,048,576 amplitudes
#
# This exponential growth is one of the central computational challenges
# of classical simulation of general quantum states.

for qubits in range(1, 11):
    amplitudes = 2 ** qubits
    print(
        f"{qubits:2d} qubits -> "
        f"{amplitudes:6d} state amplitudes"
    )


# =============================================================================
# SECTION 44: SPARSE STATE REPRESENTATION
# =============================================================================

section("44. Sparse Representation")

# Many computational-basis states contain mostly zero amplitudes.
# A dictionary can represent only nonzero entries.

sparse_state = {
    0: 1 / math.sqrt(2),
    3: 1 / math.sqrt(2),
}

print("Sparse state:", sparse_state)

sparse_norm = sum(
    abs(amplitude) ** 2
    for amplitude in sparse_state.values()
)

print("Sparse state norm squared =", sparse_norm)


# =============================================================================
# SECTION 45: COMMON MISTAKES
# =============================================================================

section("45. Common Complex-Number Mistakes")

# Mistake 1:
# Using i instead of Python's j syntax.
#
# Correct:
correct = 2 + 3j

# Mistake 2:
# Using amplitude directly as probability.
amplitude = 1j / math.sqrt(2)

print("Amplitude =", amplitude)
print("Correct probability =", abs(amplitude) ** 2)

# Mistake 3:
# Forgetting conjugation in an inner product.
#
# Correct:
a = 1 + 2j
b = 3 + 4j

correct_inner = a.conjugate() * b
incorrect_inner = a * b

print("Correct scalar inner-product term =", correct_inner)
print("Without conjugation =", incorrect_inner)


# =============================================================================
# SECTION 46: REUSABLE QUANTUM UTILITIES
# =============================================================================

section("46. Reusable Quantum Utility Functions")

def probabilities_from_amplitudes(
    amplitudes: Sequence[complex],
) -> list[float]:
    """Convert normalized amplitudes into measurement probabilities."""
    probabilities = [
        abs(amplitude) ** 2
        for amplitude in amplitudes
    ]

    validate_probability_distribution(probabilities)

    return probabilities


def phase_difference(
    a: complex,
    b: complex,
) -> float:
    """
    Return the principal phase difference between two nonzero amplitudes.

    The result is wrapped into (-pi, pi].
    """
    if a == 0 or b == 0:
        raise ValueError(
            "Phase difference requires nonzero amplitudes."
        )

    return cmath.phase(a / b)


a = 1 + 0j
b = 1j

print("Probabilities =", probabilities_from_amplitudes([
    1 / math.sqrt(2),
    1j / math.sqrt(2),
]))

print(
    "Phase difference a/b =",
    phase_difference(a, b)
)


# =============================================================================
# SECTION 47: UNIT TESTS
# =============================================================================

section("47. Built-In Verification Tests")

def run_tests() -> None:
    """Run correctness checks for the main mathematical utilities."""

    # Complex arithmetic
    assert complex_is_close(
        (3 + 4j) * (1 - 2j),
        11 - 2j,
    )

    # Modulus
    assert math.isclose(abs(3 + 4j), 5.0)

    # Conjugate identity
    z = 3 + 4j
    assert complex_is_close(
        z * z.conjugate(),
        abs(z) ** 2,
    )

    # Euler identity
    assert complex_is_close(
        cmath.exp(1j * math.pi),
        -1 + 0j,
    )

    # Root verification
    for root in complex_nth_roots(1 + 0j, 5):
        assert complex_is_close(root ** 5, 1 + 0j)

    # Vector normalization
    vector = normalize_vector([1 + 2j, 3 - 4j])
    assert math.isclose(vector_norm_squared(vector), 1.0)

    # Hadamard is unitary
    assert is_unitary(H)

    # Pauli matrices are unitary and Hermitian
    assert is_unitary(X)
    assert is_unitary(Y)
    assert is_unitary(Z)

    assert is_hermitian(X)
    assert is_hermitian(Y)
    assert is_hermitian(Z)

    # H|0> has equal probabilities
    h_state = apply_gate(H, ket0)
    probabilities = [
        abs(value) ** 2
        for value in h_state
    ]

    assert math.isclose(probabilities[0], 0.5)
    assert math.isclose(probabilities[1], 0.5)

    # Bell state is normalized and entangled.
    assert math.isclose(
        vector_norm_squared(bell_phi_plus),
        1.0,
    )

    assert not is_product_state_two_qubit(
        bell_phi_plus
    )

    # A product state should be separable.
    assert is_product_state_two_qubit(
        product_state
    )

    print("All tests passed.")


run_tests()


# =============================================================================
# SECTION 48: COMPLETE DEMONSTRATION
# =============================================================================

section("48. End-to-End Quantum-Amplitude Demonstration")

# Start with |0>.
initial_state = ket0

# Apply H:
# |0> -> (|0> + |1>)/sqrt(2)
superposition_state = apply_gate(
    H,
    initial_state,
)

# Apply a phase gate:
# The magnitude of the |1> amplitude remains unchanged,
# but its phase changes.
phased_state = apply_gate(
    S,
    superposition_state,
)

# Apply H again.
final_state = apply_gate(
    H,
    phased_state,
)

print("Initial state:")
print(initial_state)

print("\nAfter H:")
print(superposition_state)

print("\nAfter S:")
print(phased_state)

print("\nAfter H again:")
print(final_state)

print("\nFinal probabilities:")
print([
    abs(amplitude) ** 2
    for amplitude in final_state
])


# =============================================================================
# SECTION 49: IMPORTANT IDENTITIES
# =============================================================================

section("49. Important Identities")

z = 2 - 3j
w = -1 + 4j

identities = {
    "conjugate(conjugate(z)) = z":
        z.conjugate().conjugate() == z,

    "conjugate(z*w) = conjugate(z)*conjugate(w)":
        complex_is_close(
            (z * w).conjugate(),
            z.conjugate() * w.conjugate(),
        ),

    "|z*w| = |z|*|w|":
        math.isclose(
            abs(z * w),
            abs(z) * abs(w),
        ),

    "|z|^2 = z*conjugate(z)":
        complex_is_close(
            abs(z) ** 2,
            z * z.conjugate(),
        ),
}

for identity, result in identities.items():
    print(f"{identity}: {result}")


# =============================================================================
# SECTION 50: FINAL EXECUTABLE REFERENCE
# =============================================================================

section("50. Compact Reference")

print(
    """
Complex number:
    z = a + bj

Python:
    z = complex(a, b)
    z = a + bj

Core properties:
    z.real
    z.imag
    z.conjugate()
    abs(z)
    cmath.phase(z)

Arithmetic:
    z1 + z2
    z1 - z2
    z1 * z2
    z1 / z2
    z ** n

Polar/exponential:
    z = r * exp(i*theta)

Euler:
    exp(i*theta) = cos(theta) + i*sin(theta)

Quantum state:
    |psi> = sum(alpha_i |i>)

Normalization:
    sum(|alpha_i|^2) = 1

Measurement:
    P(i) = |alpha_i|^2

Inner product:
    <a|b> = sum(conj(a_i) * b_i)

Unitary transformation:
    U†U = I

Global phase:
    |psi> and exp(i*gamma)|psi> have identical measurement
    probabilities.

Relative phase:
    Can change interference and therefore observable outcomes.

n-qubit state dimension:
    2^n amplitudes
"""
)

print("\nStudy script completed successfully.")
