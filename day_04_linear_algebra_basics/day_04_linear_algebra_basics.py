"""
Linear Algebra Basics: Vectors, Matrices, and Notation
=======================================================

A self-contained study and practice script covering linear algebra from
absolute beginner level through advanced introductory matrix operations.

Requirements:
    Python 3.9+

Dependencies:
    Standard library only.

The script intentionally implements many operations from scratch so that
the mathematical ideas and their computational mechanisms remain visible.
Floating-point comparisons use a tolerance because real-number arithmetic
in computers is approximate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt
from typing import Iterable, Iterator, List, Sequence, Tuple


# ============================================================================
# 1. BASIC MATHEMATICAL NOTATION
# ============================================================================

"""
Common notation used throughout this file:

Scalar:
    A single number, such as 3, -2.5, or pi.

Vector:
    An ordered collection of numbers.
    Example: v = [2, 4, -1]

Column vector:
        [ 2 ]
    v = [ 4 ]
        [-1 ]

Matrix:
    A rectangular arrangement of numbers.
    Example:
        A = [1 2 3]
            [4 5 6]

A matrix with m rows and n columns is an m x n matrix.

Element notation:
    A_ij means the element in row i and column j.
    Mathematical indexing commonly starts at 1.
    Python indexing starts at 0.

Transpose:
    A^T changes rows into columns.

Identity matrix:
    I has 1s on its main diagonal and 0s elsewhere.

Zero vector:
    Every component is zero.

Zero matrix:
    Every matrix element is zero.

Dimension:
    R^n represents the set of n-dimensional real vectors.

The symbols:
    R     real numbers
    R^n   n-dimensional real vector space
    ||v|| vector norm / length
    v · w dot product
    A v   matrix-vector multiplication
    A B   matrix-matrix multiplication
    A^T   transpose
    det(A) determinant
    A^-1 inverse, when it exists
"""


# ============================================================================
# 2. GENERAL UTILITY FUNCTIONS
# ============================================================================

DEFAULT_TOLERANCE = 1e-9


def approximately_equal(a: float, b: float, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    """Return True when two floating-point values are approximately equal."""
    return isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)


def format_number(value: float) -> str:
    """Make numerical output easier to read."""
    if approximately_equal(value, round(value)):
        return str(int(round(value)))
    return f"{value:.6g}"


def print_section(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subsection(title: str) -> None:
    """Print a consistent subsection heading."""
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


# ============================================================================
# 3. SCALARS
# ============================================================================

def scalar_examples() -> None:
    """
    A scalar represents one numerical quantity.

    Scalars can be added, subtracted, multiplied, and divided subject to
    ordinary arithmetic rules. In linear algebra, scalars are often used to
    scale vectors and matrices.
    """
    print_section("1. Scalars")

    a = 5
    b = -2

    print("a =", a)
    print("b =", b)
    print("a + b =", a + b)
    print("a - b =", a - b)
    print("a * b =", a * b)
    print("a / b =", a / b)

    vector = [2, 4, 6]
    scalar = 3
    scaled_vector = [scalar * x for x in vector]

    print("Vector:", vector)
    print("Scalar:", scalar)
    print("Scalar multiplication:", scaled_vector)


# ============================================================================
# 4. VECTOR CLASS
# ============================================================================

@dataclass
class Vector:
    """
    A finite-dimensional real vector.

    Internally, components are stored as a tuple. Immutability-like behavior
    prevents accidental modification of an existing vector and makes the
    object safe to use in demonstrations.

    Example:
        Vector((1, 2, 3))

    represents

        [1]
        [2]
        [3]
    """

    components: Tuple[float, ...]

    def __init__(self, components: Iterable[float]):
        values = tuple(float(x) for x in components)

        if not values:
            raise ValueError("A vector must contain at least one component.")

        object.__setattr__(self, "components", values)

    @property
    def dimension(self) -> int:
        """Return the number of components."""
        return len(self.components)

    def __len__(self) -> int:
        return self.dimension

    def __iter__(self) -> Iterator[float]:
        return iter(self.components)

    def __getitem__(self, index: int) -> float:
        return self.components[index]

    def __repr__(self) -> str:
        values = ", ".join(format_number(x) for x in self.components)
        return f"Vector({values})"

    def __add__(self, other: "Vector") -> "Vector":
        self._check_same_dimension(other)
        return Vector(a + b for a, b in zip(self, other))

    def __sub__(self, other: "Vector") -> "Vector":
        self._check_same_dimension(other)
        return Vector(a - b for a, b in zip(self, other))

    def __neg__(self) -> "Vector":
        return Vector(-x for x in self)

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(scalar * x for x in self)

    def __rmul__(self, scalar: float) -> "Vector":
        return self * scalar

    def __truediv__(self, scalar: float) -> "Vector":
        if approximately_equal(scalar, 0):
            raise ZeroDivisionError("Cannot divide a vector by zero.")
        return Vector(x / scalar for x in self)

    def _check_same_dimension(self, other: "Vector") -> None:
        if self.dimension != other.dimension:
            raise ValueError(
                f"Dimension mismatch: {self.dimension} and {other.dimension}."
            )

    def dot(self, other: "Vector") -> float:
        """
        Compute the dot product.

        For vectors

            u = [u1, u2, ..., un]
            v = [v1, v2, ..., vn]

        u · v = u1*v1 + u2*v2 + ... + un*vn.
        """
        self._check_same_dimension(other)
        return sum(a * b for a, b in zip(self, other))

    def norm(self) -> float:
        """
        Euclidean length:

            ||v|| = sqrt(v1^2 + ... + vn^2)
        """
        return sqrt(self.dot(self))

    def squared_norm(self) -> float:
        """Return ||v||^2 without computing a square root."""
        return self.dot(self)

    def unit(self) -> "Vector":
        """
        Normalize the vector.

        A unit vector has length 1 and points in the same direction.
        The zero vector has no defined direction and cannot be normalized.
        """
        length = self.norm()

        if approximately_equal(length, 0):
            raise ValueError("The zero vector cannot be normalized.")

        return self / length

    def distance_to(self, other: "Vector") -> float:
        """Return Euclidean distance between two vectors."""
        return (self - other).norm()

    def angle_with(self, other: "Vector") -> float:
        """
        Return the angle in radians.

        Using:

            cos(theta) = (u · v) / (||u|| ||v||)

        The ratio is clamped to [-1, 1] to protect against tiny floating-point
        errors before calling the inverse cosine.
        """
        from math import acos

        self._check_same_dimension(other)

        denominator = self.norm() * other.norm()

        if approximately_equal(denominator, 0):
            raise ValueError("Angle with the zero vector is undefined.")

        cosine = self.dot(other) / denominator
        cosine = max(-1.0, min(1.0, cosine))

        return acos(cosine)


def vector_examples() -> None:
    print_section("2. Vectors")

    v = Vector((2, 3))
    w = Vector((4, -1))

    print("v =", v)
    print("w =", w)
    print("dimension of v =", v.dimension)
    print("v + w =", v + w)
    print("v - w =", v - w)
    print("2v =", 2 * v)
    print("-v =", -v)

    print("v · w =", v.dot(w))
    print("||v|| =", format_number(v.norm()))
    print("unit(v) =", v.unit())
    print("distance(v, w) =", format_number(v.distance_to(w)))

    # Geometrically, vector addition combines displacement or other directed
    # quantities. Algebraically, it is component-wise addition.
    a = Vector((1, 2, 3))
    b = Vector((4, 5, 6))
    print("3D vector example:", a + b)


# ============================================================================
# 5. VECTOR GEOMETRY AND FUNDAMENTAL RELATIONSHIPS
# ============================================================================

def vector_geometry_examples() -> None:
    print_section("3. Vector Geometry")

    perpendicular_a = Vector((1, 2))
    perpendicular_b = Vector((2, -1))

    print("Perpendicular test:")
    print("a · b =", perpendicular_a.dot(perpendicular_b))
    print("Dot product zero:", approximately_equal(perpendicular_a.dot(perpendicular_b), 0))

    same_direction_a = Vector((2, 4))
    same_direction_b = Vector((1, 2))

    print("\nParallel vectors:")
    print("a =", same_direction_a)
    print("b =", same_direction_b)
    print("a · b =", same_direction_a.dot(same_direction_b))

    # Cauchy-Schwarz inequality:
    #
    # |u · v| <= ||u|| ||v||
    #
    # This relationship is central to geometry, optimization, statistics,
    # numerical analysis, and machine learning.
    u = Vector((1, 2, 3))
    v = Vector((3, 0, -1))

    left_side = abs(u.dot(v))
    right_side = u.norm() * v.norm()

    print("\nCauchy-Schwarz check:")
    print("|u · v| =", format_number(left_side))
    print("||u|| ||v|| =", format_number(right_side))
    print("Inequality holds:", left_side <= right_side + DEFAULT_TOLERANCE)


# ============================================================================
# 6. CROSS PRODUCT IN R^3
# ============================================================================

def cross_product(a: Vector, b: Vector) -> Vector:
    """
    Compute the 3-dimensional cross product.

        a x b =
        [a2*b3 - a3*b2]
        [a3*b1 - a1*b3]
        [a1*b2 - a2*b1]

    The result is perpendicular to both input vectors.

    Cross product is specifically a familiar binary vector product in R^3;
    it is not a general replacement for the dot product in arbitrary
    dimensions.
    """
    if a.dimension != 3 or b.dimension != 3:
        raise ValueError("The cross product is implemented here only for R^3.")

    return Vector(
        (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )
    )


def cross_product_examples() -> None:
    print_section("4. Cross Product")

    a = Vector((1, 0, 0))
    b = Vector((0, 1, 0))
    c = cross_product(a, b)

    print("a =", a)
    print("b =", b)
    print("a x b =", c)
    print("(a x b) · a =", c.dot(a))
    print("(a x b) · b =", c.dot(b))

    # Reversing the order changes the sign:
    # a x b = -(b x a)
    print("b x a =", cross_product(b, a))


# ============================================================================
# 7. MATRIX CLASS
# ============================================================================

class Matrix:
    """
    A general real matrix.

    Matrix entries are stored as immutable tuples of tuples.

    A matrix with m rows and n columns has shape (m, n).

    Python:
        Matrix([[1, 2], [3, 4]])

    Mathematics:
        [1 2]
        [3 4]
    """

    def __init__(self, rows: Sequence[Sequence[float]]):
        if not rows:
            raise ValueError("A matrix must have at least one row.")

        converted_rows = tuple(tuple(float(x) for x in row) for row in rows)

        if not converted_rows[0]:
            raise ValueError("A matrix must have at least one column.")

        column_count = len(converted_rows[0])

        if any(len(row) != column_count for row in converted_rows):
            raise ValueError("All matrix rows must have the same length.")

        object.__setattr__(self, "_rows", converted_rows)

    @property
    def rows(self) -> int:
        """Number of rows, m."""
        return len(self._rows)

    @property
    def columns(self) -> int:
        """Number of columns, n."""
        return len(self._rows[0])

    @property
    def shape(self) -> Tuple[int, int]:
        """Return matrix shape (rows, columns)."""
        return self.rows, self.columns

    def __getitem__(self, index: int) -> Tuple[float, ...]:
        return self._rows[index]

    def __iter__(self) -> Iterator[Tuple[float, ...]]:
        return iter(self._rows)

    def __repr__(self) -> str:
        return f"Matrix({self._rows!r})"

    def pretty(self) -> str:
        """Return a human-readable rectangular matrix."""
        formatted = [
            [format_number(value) for value in row]
            for row in self._rows
        ]

        widths = [
            max(len(formatted[row][column]) for row in range(self.rows))
            for column in range(self.columns)
        ]

        lines = []

        for row_index, row in enumerate(formatted):
            content = "  ".join(
                value.rjust(widths[column])
                for column, value in enumerate(row)
            )

            left = "[" if row_index == 0 else " "
            right = "]" if row_index == self.rows - 1 else " "

            lines.append(f"{left}{content}{right}")

        return "\n".join(lines)

    def _check_same_shape(self, other: "Matrix") -> None:
        if self.shape != other.shape:
            raise ValueError(
                f"Matrix shape mismatch: {self.shape} and {other.shape}."
            )

    def __add__(self, other: "Matrix") -> "Matrix":
        self._check_same_shape(other)

        return Matrix(
            [
                [a + b for a, b in zip(row_a, row_b)]
                for row_a, row_b in zip(self, other)
            ]
        )

    def __sub__(self, other: "Matrix") -> "Matrix":
        self._check_same_shape(other)

        return Matrix(
            [
                [a - b for a, b in zip(row_a, row_b)]
                for row_a, row_b in zip(self, other)
            ]
        )

    def __neg__(self) -> "Matrix":
        return Matrix([[-x for x in row] for row in self])

    def __mul__(self, scalar: float) -> "Matrix":
        return Matrix([[scalar * x for x in row] for row in self])

    def __rmul__(self, scalar: float) -> "Matrix":
        return self * scalar

    def __matmul__(self, other):
        """
        Implement the @ operator.

        A @ B represents matrix multiplication.
        A may be multiplied by B only when:

            columns(A) == rows(B)

        If A is m x n and B is n x p, the result is m x p.
        """
        if isinstance(other, Matrix):
            return self.multiply_matrix(other)

        if isinstance(other, Vector):
            return self.multiply_vector(other)

        return NotImplemented

    def multiply_matrix(self, other: "Matrix") -> "Matrix":
        """Multiply two matrices using the standard row-column rule."""
        if self.columns != other.rows:
            raise ValueError(
                f"Cannot multiply shapes {self.shape} and {other.shape}."
            )

        result = []

        for i in range(self.rows):
            result_row = []

            for j in range(other.columns):
                value = sum(
                    self[i][k] * other[k][j]
                    for k in range(self.columns)
                )
                result_row.append(value)

            result.append(result_row)

        return Matrix(result)

    def multiply_vector(self, vector: Vector) -> Vector:
        """
        Multiply an m x n matrix by an n-dimensional vector.

        The result is an m-dimensional vector.
        """
        if self.columns != vector.dimension:
            raise ValueError(
                f"Cannot multiply matrix shape {self.shape} by "
                f"vector of dimension {vector.dimension}."
            )

        return Vector(
            sum(self[i][j] * vector[j] for j in range(self.columns))
            for i in range(self.rows)
        )

    def transpose(self) -> "Matrix":
        """Return A^T."""
        return Matrix(
            [
                [self[row][column] for row in range(self.rows)]
                for column in range(self.columns)
            ]
        )

    def is_square(self) -> bool:
        return self.rows == self.columns

    def trace(self) -> float:
        """
        Return the trace of a square matrix.

        trace(A) = sum of diagonal elements.
        """
        if not self.is_square():
            raise ValueError("Trace is defined here only for square matrices.")

        return sum(self[i][i] for i in range(self.rows))

    def row(self, index: int) -> Vector:
        """Return a row as a vector."""
        return Vector(self[index])

    def column(self, index: int) -> Vector:
        """Return a column as a vector."""
        return Vector(self[row][index] for row in range(self.rows))


def matrix_examples() -> None:
    print_section("5. Matrices and Notation")

    A = Matrix(
        [
            [1, 2, 3],
            [4, 5, 6],
        ]
    )

    print("A =")
    print(A.pretty())
    print("shape(A) =", A.shape)
    print("A[0][1] =", format_number(A[0][1]))
    print("first row =", A.row(0))
    print("second column =", A.column(1))

    B = Matrix(
        [
            [6, 5, 4],
            [3, 2, 1],
        ]
    )

    print("\nA + B =")
    print((A + B).pretty())

    print("\nA - B =")
    print((A - B).pretty())

    print("\n2A =")
    print((2 * A).pretty())

    print("\nA^T =")
    print(A.transpose().pretty())


# ============================================================================
# 8. SPECIAL MATRICES
# ============================================================================

def zero_matrix(rows: int, columns: int) -> Matrix:
    """Construct an m x n zero matrix."""
    if rows <= 0 or columns <= 0:
        raise ValueError("Matrix dimensions must be positive.")

    return Matrix([[0.0] * columns for _ in range(rows)])


def identity_matrix(size: int) -> Matrix:
    """Construct the n x n identity matrix I_n."""
    if size <= 0:
        raise ValueError("Identity matrix size must be positive.")

    return Matrix(
        [
            [1.0 if row == column else 0.0 for column in range(size)]
            for row in range(size)
        ]
    )


def diagonal_matrix(values: Sequence[float]) -> Matrix:
    """Construct a diagonal matrix from its diagonal values."""
    n = len(values)

    if n == 0:
        raise ValueError("A diagonal matrix needs at least one diagonal value.")

    return Matrix(
        [
            [float(values[row]) if row == column else 0.0 for column in range(n)]
            for row in range(n)
        ]
    )


def special_matrix_examples() -> None:
    print_section("6. Special Matrices")

    print("Zero matrix:")
    print(zero_matrix(2, 3).pretty())

    print("\nIdentity matrix I3:")
    I = identity_matrix(3)
    print(I.pretty())

    print("\nDiagonal matrix:")
    print(diagonal_matrix([2, 5, 7]).pretty())

    A = Matrix([[1, 2], [3, 4]])

    # Multiplication by the identity leaves a matrix unchanged:
    # AI = IA = A.
    print("\nA I =")
    print((A @ identity_matrix(2)).pretty())


# ============================================================================
# 9. MATRIX MULTIPLICATION
# ============================================================================

def matrix_multiplication_examples() -> None:
    print_section("7. Matrix Multiplication")

    A = Matrix(
        [
            [1, 2, 3],
            [4, 5, 6],
        ]
    )

    B = Matrix(
        [
            [7, 8],
            [9, 10],
            [11, 12],
        ]
    )

    C = A @ B

    print("A:")
    print(A.pretty())

    print("\nB:")
    print(B.pretty())

    print("\nA @ B:")
    print(C.pretty())

    print("\nShape rule:")
    print(f"{A.shape} @ {B.shape} -> {C.shape}")

    vector = Vector((1, 2, 3))
    print("\nA @ vector =", A @ vector)

    # Matrix multiplication is generally NOT commutative:
    # AB may exist while BA does not, or both may exist but differ.
    X = Matrix([[1, 2], [3, 4]])
    Y = Matrix([[0, 1], [1, 0]])

    print("\nXY:")
    print((X @ Y).pretty())

    print("\nYX:")
    print((Y @ X).pretty())

    print("\nXY == YX:", X @ Y == Y @ X)


# ============================================================================
# 10. EQUALITY HELPERS
# ============================================================================

def vectors_equal(
    a: Vector,
    b: Vector,
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    if a.dimension != b.dimension:
        return False

    return all(
        approximately_equal(x, y, tolerance)
        for x, y in zip(a, b)
    )


def matrices_equal(
    A: Matrix,
    B: Matrix,
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    if A.shape != B.shape:
        return False

    return all(
        approximately_equal(A[i][j], B[i][j], tolerance)
        for i in range(A.rows)
        for j in range(A.columns)
    )


# ============================================================================
# 11. LINEAR COMBINATIONS
# ============================================================================

def linear_combination(
    vectors: Sequence[Vector],
    coefficients: Sequence[float],
) -> Vector:
    """
    Compute:

        c1*v1 + c2*v2 + ... + ck*vk

    A linear combination uses scalar multiplication and vector addition only.
    """
    if not vectors:
        raise ValueError("At least one vector is required.")

    if len(vectors) != len(coefficients):
        raise ValueError("Vectors and coefficients must have equal lengths.")

    result = Vector([0.0] * vectors[0].dimension)

    for vector, coefficient in zip(vectors, coefficients):
        result = result + coefficient * vector

    return result


def linear_combination_examples() -> None:
    print_section("8. Linear Combinations")

    v1 = Vector((1, 0))
    v2 = Vector((0, 1))

    result = linear_combination(
        [v1, v2],
        [3, 5],
    )

    print("3v1 + 5v2 =", result)

    # Standard basis vectors provide coordinates directly:
    # [x, y] = x*e1 + y*e2.
    e1 = Vector((1, 0))
    e2 = Vector((0, 1))
    target = Vector((7, -2))

    reconstructed = linear_combination([e1, e2], [7, -2])

    print("Target:", target)
    print("Reconstructed:", reconstructed)
    print("Equal:", vectors_equal(target, reconstructed))


# ============================================================================
# 12. LINEAR INDEPENDENCE
# ============================================================================

def determinant_2x2(A: Matrix) -> float:
    """Compute determinant of a 2 x 2 matrix."""
    if A.shape != (2, 2):
        raise ValueError("This function requires a 2 x 2 matrix.")

    return A[0][0] * A[1][1] - A[0][1] * A[1][0]


def vectors_are_independent_2d(a: Vector, b: Vector) -> bool:
    """
    Determine independence of two vectors in R^2.

    Put the vectors into a matrix as columns:

        [a1 b1]
        [a2 b2]

    The vectors are independent exactly when the determinant is nonzero.
    """
    if a.dimension != 2 or b.dimension != 2:
        raise ValueError("Both vectors must belong to R^2.")

    A = Matrix(
        [
            [a[0], b[0]],
            [a[1], b[1]],
        ]
    )

    return not approximately_equal(determinant_2x2(A), 0)


def linear_independence_examples() -> None:
    print_section("9. Linear Independence")

    a = Vector((1, 2))
    b = Vector((2, 4))

    c = Vector((1, 2))
    d = Vector((-2, 1))

    print("a =", a)
    print("b =", b)
    print("Independent:", vectors_are_independent_2d(a, b))

    print("\nc =", c)
    print("d =", d)
    print("Independent:", vectors_are_independent_2d(c, d))

    print(
        "\nInterpretation: a set is linearly dependent when at least one "
        "vector can be expressed as a linear combination of the others."
    )


# ============================================================================
# 13. MATRIX TRANSFORMATIONS
# ============================================================================

def transformation_examples() -> None:
    print_section("10. Matrices as Linear Transformations")

    rotation_90 = Matrix(
        [
            [0, -1],
            [1, 0],
        ]
    )

    vector = Vector((2, 1))
    transformed = rotation_90 @ vector

    print("Rotation matrix:")
    print(rotation_90.pretty())
    print("Original vector:", vector)
    print("Transformed vector:", transformed)

    scaling = Matrix(
        [
            [3, 0],
            [0, 2],
        ]
    )

    print("\nScaling transformation:")
    print((scaling @ vector))

    # A matrix transformation preserves vector addition and scalar
    # multiplication:
    #
    # A(u + v) = Au + Av
    # A(cu) = c(Au)
    u = Vector((1, 2))
    v = Vector((3, -1))
    c = 4

    left_addition = rotation_90 @ (u + v)
    right_addition = (rotation_90 @ u) + (rotation_90 @ v)

    left_scaling = rotation_90 @ (c * u)
    right_scaling = c * (rotation_90 @ u)

    print("\nLinearity check:")
    print("A(u + v) =", left_addition)
    print("Au + Av   =", right_addition)
    print("Equal:", vectors_equal(left_addition, right_addition))

    print("\nA(cu) =", left_scaling)
    print("c(Au) =", right_scaling)
    print("Equal:", vectors_equal(left_scaling, right_scaling))


# ============================================================================
# 14. ROW VECTORS AND COLUMN VECTORS
# ============================================================================

def row_column_vector_examples() -> None:
    print_section("11. Row and Column Vectors")

    row_vector = Matrix([[1, 2, 3]])
    column_vector = Matrix([[1], [2], [3]])

    print("Row vector:")
    print(row_vector.pretty())
    print("shape =", row_vector.shape)

    print("\nColumn vector:")
    print(column_vector.pretty())
    print("shape =", column_vector.shape)

    # A column vector is the common representation for multiplying A x.
    A = Matrix(
        [
            [2, 1, 0],
            [0, 3, 1],
        ]
    )

    x = Vector((4, 5, 6))

    print("\nA x =")
    print((A @ x))


# ============================================================================
# 15. DETERMINANTS
# ============================================================================

def determinant(A: Matrix) -> float:
    """
    Compute a determinant recursively using Laplace expansion.

    This implementation is educational rather than performance-oriented.

    Properties:
        det(I) = 1
        det(AB) = det(A)det(B)
        det(A^T) = det(A)

    Geometric interpretation:
        |det(A)| is the scaling factor for area in R^2 or volume in R^3.
        A negative determinant additionally indicates orientation reversal.

    A square matrix is invertible exactly when its determinant is nonzero.
    """
    if not A.is_square():
        raise ValueError("A determinant requires a square matrix.")

    n = A.rows

    if n == 1:
        return A[0][0]

    if n == 2:
        return determinant_2x2(A)

    total = 0.0

    for column in range(n):
        minor = Matrix(
            [
                [
                    A[row][other_column]
                    for other_column in range(n)
                    if other_column != column
                ]
                for row in range(1, n)
            ]
        )

        sign = 1 if column % 2 == 0 else -1

        total += sign * A[0][column] * determinant(minor)

    return total


def determinant_examples() -> None:
    print_section("12. Determinants")

    A = Matrix(
        [
            [2, 3],
            [1, 4],
        ]
    )

    B = Matrix(
        [
            [1, 2, 0],
            [0, 3, 4],
            [5, 0, 1],
        ]
    )

    print("A:")
    print(A.pretty())
    print("det(A) =", format_number(determinant(A)))

    print("\nB:")
    print(B.pretty())
    print("det(B) =", format_number(determinant(B)))

    singular = Matrix(
        [
            [1, 2],
            [2, 4],
        ]
    )

    print("\nSingular matrix:")
    print(singular.pretty())
    print("det =", format_number(determinant(singular)))

    # Determinant as area scaling:
    unit_square_basis = Matrix(
        [
            [2, 0],
            [0, 3],
        ]
    )

    print("\nScaling by 2 horizontally and 3 vertically:")
    print(unit_square_basis.pretty())
    print("Area scaling factor =", determinant(unit_square_basis))


# ============================================================================
# 16. MINORS, COFACTORS, AND ADJUGATE
# ============================================================================

def minor_matrix(A: Matrix, remove_row: int, remove_column: int) -> Matrix:
    """Return the matrix formed by deleting one row and one column."""
    if not A.is_square():
        raise ValueError("Minor matrices require a square matrix.")

    return Matrix(
        [
            [
                A[row][column]
                for column in range(A.columns)
                if column != remove_column
            ]
            for row in range(A.rows)
            if row != remove_row
        ]
    )


def cofactor(A: Matrix, row: int, column: int) -> float:
    """
    Compute C_ij = (-1)^(i+j) M_ij using zero-based indices internally.

    Mathematical indices are one-based, so the sign pattern is:

        + - + -
        - + - +
        + - + -
        - + - +
    """
    minor = minor_matrix(A, row, column)
    sign = 1 if (row + column) % 2 == 0 else -1
    return sign * determinant(minor)


def cofactor_matrix(A: Matrix) -> Matrix:
    """Return the matrix of cofactors."""
    if not A.is_square():
        raise ValueError("Cofactor matrix requires a square matrix.")

    return Matrix(
        [
            [cofactor(A, row, column) for column in range(A.columns)]
            for row in range(A.rows)
        ]
    )


def adjugate(A: Matrix) -> Matrix:
    """
    Return adj(A) = C^T.

    For an invertible square matrix:

        A^-1 = adj(A) / det(A)
    """
    return cofactor_matrix(A).transpose()


def cofactor_examples() -> None:
    print_section("13. Minors, Cofactors, and Adjugate")

    A = Matrix(
        [
            [1, 2],
            [3, 4],
        ]
    )

    print("A:")
    print(A.pretty())

    print("\nCofactor matrix:")
    print(cofactor_matrix(A).pretty())

    print("\nAdjugate:")
    print(adjugate(A).pretty())


# ============================================================================
# 17. GAUSSIAN ELIMINATION
# ============================================================================

def swap_rows(rows: List[List[float]], first: int, second: int) -> None:
    """Swap two rows in a mutable matrix representation."""
    rows[first], rows[second] = rows[second], rows[first]


def gaussian_elimination(
    A: Matrix,
    b: Sequence[float] | None = None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Tuple[Matrix, Vector | None]:
    """
    Perform Gaussian elimination with partial pivoting.

    If b is supplied, it is treated as the right-hand side of A x = b.

    Partial pivoting chooses a large available pivot in each column. This
    reduces numerical instability compared with blindly dividing by the
    first available value.

    The function produces row-echelon form, not necessarily reduced
    row-echelon form.
    """
    rows = [list(row) for row in A]

    rhs = None
    if b is not None:
        if len(b) != A.rows:
            raise ValueError("Right-hand side length must equal row count.")

        rhs = [float(value) for value in b]

    pivot_row = 0

    for pivot_column in range(A.columns):
        if pivot_row >= A.rows:
            break

        best_row = max(
            range(pivot_row, A.rows),
            key=lambda row: abs(rows[row][pivot_column]),
        )

        if approximately_equal(
            rows[best_row][pivot_column],
            0,
            tolerance,
        ):
            continue

        swap_rows(rows, pivot_row, best_row)

        if rhs is not None:
            rhs[pivot_row], rhs[best_row] = rhs[best_row], rhs[pivot_row]

        pivot = rows[pivot_row][pivot_column]

        for row in range(pivot_row + 1, A.rows):
            factor = rows[row][pivot_column] / pivot

            if approximately_equal(factor, 0, tolerance):
                continue

            for column in range(pivot_column, A.columns):
                rows[row][column] -= factor * rows[pivot_row][column]

            if rhs is not None:
                rhs[row] -= factor * rhs[pivot_row]

        pivot_row += 1

    return Matrix(rows), Vector(rhs) if rhs is not None else None


def reduced_row_echelon_form(
    A: Matrix,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Matrix:
    """
    Compute reduced row-echelon form using Gauss-Jordan elimination.

    RREF properties:
        1. Every nonzero row has a leading 1.
        2. Each leading 1 is the only nonzero entry in its column.
        3. Leading entries move rightward down the rows.
        4. Zero rows appear below nonzero rows.

    RREF is unique for a given matrix.
    """
    rows = [list(row) for row in A]
    pivot_row = 0

    for pivot_column in range(A.columns):
        if pivot_row >= A.rows:
            break

        best_row = max(
            range(pivot_row, A.rows),
            key=lambda row: abs(rows[row][pivot_column]),
        )

        if approximately_equal(
            rows[best_row][pivot_column],
            0,
            tolerance,
        ):
            continue

        swap_rows(rows, pivot_row, best_row)

        pivot = rows[pivot_row][pivot_column]

        for column in range(A.columns):
            rows[pivot_row][column] /= pivot

        for row in range(A.rows):
            if row == pivot_row:
                continue

            factor = rows[row][pivot_column]

            if approximately_equal(factor, 0, tolerance):
                continue

            for column in range(A.columns):
                rows[row][column] -= factor * rows[pivot_row][column]

        pivot_row += 1

    # Remove tiny floating-point noise for cleaner educational output.
    for row in range(A.rows):
        for column in range(A.columns):
            if approximately_equal(rows[row][column], 0, tolerance):
                rows[row][column] = 0.0

    return Matrix(rows)


def elimination_examples() -> None:
    print_section("14. Gaussian Elimination and RREF")

    A = Matrix(
        [
            [2, 1, -1],
            [-3, -1, 2],
            [-2, 1, 2],
        ]
    )

    b = Vector((8, -11, -3))

    print("Coefficient matrix A:")
    print(A.pretty())

    print("\nRight-hand side b:")
    print(b)

    echelon, transformed_rhs = gaussian_elimination(A, b)

    print("\nRow-echelon form of A:")
    print(echelon.pretty())

    print("\nTransformed right-hand side:")
    print(transformed_rhs)

    print("\nRREF(A):")
    print(reduced_row_echelon_form(A).pretty())


# ============================================================================
# 18. RANK
# ============================================================================

def rank(A: Matrix, tolerance: float = DEFAULT_TOLERANCE) -> int:
    """
    Compute matrix rank from its RREF.

    Rank equals:
        - number of pivot positions
        - dimension of the row space
        - dimension of the column space
        - number of linearly independent rows
        - number of linearly independent columns
    """
    R = reduced_row_echelon_form(A, tolerance)

    result = 0

    for row in R:
        if any(not approximately_equal(x, 0, tolerance) for x in row):
            result += 1

    return result


def rank_examples() -> None:
    print_section("15. Matrix Rank")

    full_rank = Matrix(
        [
            [1, 2],
            [3, 4],
        ]
    )

    rank_deficient = Matrix(
        [
            [1, 2],
            [2, 4],
        ]
    )

    rectangular = Matrix(
        [
            [1, 2, 3],
            [2, 4, 6],
            [1, 1, 1],
        ]
    )

    print("Rank of full-rank matrix:", rank(full_rank))
    print("Rank of dependent-row matrix:", rank(rank_deficient))
    print("Rank of rectangular matrix:", rank(rectangular))


# ============================================================================
# 19. SOLVING LINEAR SYSTEMS
# ============================================================================

def solve_linear_system(
    A: Matrix,
    b: Vector,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Vector:
    """
    Solve A x = b for a unique solution using Gaussian elimination.

    This routine intentionally handles only systems with exactly one
    solution. Singular or underdetermined systems raise ValueError.

    In production numerical computing, specialized linear algebra libraries
    and decompositions such as LU, QR, or SVD are generally preferable.
    """
    if A.rows != A.columns:
        raise ValueError(
            "This solver requires a square coefficient matrix."
        )

    if b.dimension != A.rows:
        raise ValueError("Right-hand side dimension does not match A.")

    rows = [list(row) for row in A]
    rhs = list(b)

    n = A.rows

    # Forward elimination.
    for pivot_column in range(n):
        pivot_row = max(
            range(pivot_column, n),
            key=lambda row: abs(rows[row][pivot_column]),
        )

        if approximately_equal(
            rows[pivot_row][pivot_column],
            0,
            tolerance,
        ):
            raise ValueError("System does not have a unique solution.")

        swap_rows(rows, pivot_column, pivot_row)
        rhs[pivot_column], rhs[pivot_row] = (
            rhs[pivot_row],
            rhs[pivot_column],
        )

        pivot = rows[pivot_column][pivot_column]

        for row in range(pivot_column + 1, n):
            factor = rows[row][pivot_column] / pivot

            for column in range(pivot_column, n):
                rows[row][column] -= factor * rows[pivot_column][column]

            rhs[row] -= factor * rhs[pivot_column]

    # Back substitution.
    solution = [0.0] * n

    for row in range(n - 1, -1, -1):
        known = sum(
            rows[row][column] * solution[column]
            for column in range(row + 1, n)
        )

        denominator = rows[row][row]

        if approximately_equal(denominator, 0, tolerance):
            raise ValueError("System does not have a unique solution.")

        solution[row] = (rhs[row] - known) / denominator

    return Vector(solution)


def linear_system_examples() -> None:
    print_section("16. Solving Linear Systems")

    A = Matrix(
        [
            [2, 1],
            [1, -1],
        ]
    )

    b = Vector((7, 1))

    solution = solve_linear_system(A, b)

    print("System:")
    print(A.pretty())
    print("x =", solution)

    print("\nVerification A x:")
    print(A @ solution)
    print("Expected b:")
    print(b)
    print("Correct:", vectors_equal(A @ solution, b))


# ============================================================================
# 20. INVERSE MATRICES
# ============================================================================

def inverse(A: Matrix, tolerance: float = DEFAULT_TOLERANCE) -> Matrix:
    """
    Compute A^-1 using Gauss-Jordan elimination on [A | I].

    The inverse exists exactly when A is square and nonsingular.

    Mathematical definition:

        A A^-1 = A^-1 A = I
    """
    if not A.is_square():
        raise ValueError("Only square matrices can have an inverse.")

    n = A.rows

    augmented = [
        list(A[row]) + list(identity_matrix(n)[row])
        for row in range(n)
    ]

    pivot_row = 0

    for pivot_column in range(n):
        best_row = max(
            range(pivot_row, n),
            key=lambda row: abs(augmented[row][pivot_column]),
        )

        if approximately_equal(
            augmented[best_row][pivot_column],
            0,
            tolerance,
        ):
            raise ValueError("Matrix is singular and has no inverse.")

        swap_rows(augmented, pivot_row, best_row)

        pivot = augmented[pivot_row][pivot_column]

        for column in range(2 * n):
            augmented[pivot_row][column] /= pivot

        for row in range(n):
            if row == pivot_row:
                continue

            factor = augmented[row][pivot_column]

            if approximately_equal(factor, 0, tolerance):
                continue

            for column in range(2 * n):
                augmented[row][column] -= (
                    factor * augmented[pivot_row][column]
                )

        pivot_row += 1

    inverse_rows = [
        row[n:]
        for row in augmented
    ]

    return Matrix(inverse_rows)


def inverse_examples() -> None:
    print_section("17. Matrix Inverse")

    A = Matrix(
        [
            [4, 7],
            [2, 6],
        ]
    )

    A_inverse = inverse(A)

    print("A:")
    print(A.pretty())

    print("\nA^-1:")
    print(A_inverse.pretty())

    product = A @ A_inverse

    print("\nA @ A^-1:")
    print(product.pretty())

    print("\nApproximately identity:", matrices_equal(
        product,
        identity_matrix(2),
    ))

    singular = Matrix(
        [
            [1, 2],
            [2, 4],
        ]
    )

    try:
        inverse(singular)
    except ValueError as error:
        print("\nSingular inverse attempt:", error)


# ============================================================================
# 21. ORTHOGONAL VECTORS AND ORTHONORMAL SETS
# ============================================================================

def orthogonal_projection(vector: Vector, direction: Vector) -> Vector:
    """
    Project vector u onto direction v:

        proj_v(u) = ((u · v) / (v · v)) v
    """
    denominator = direction.squared_norm()

    if approximately_equal(denominator, 0):
        raise ValueError("Cannot project onto the zero vector.")

    return (vector.dot(direction) / denominator) * direction


def orthogonality_examples() -> None:
    print_section("18. Orthogonality and Projection")

    u = Vector((3, 2))
    v = Vector((1, 0))

    projection = orthogonal_projection(u, v)
    residual = u - projection

    print("u =", u)
    print("v =", v)
    print("Projection of u onto v =", projection)
    print("Residual =", residual)
    print("Residual · v =", residual.dot(v))

    # The residual is perpendicular to the direction used for projection.
    print(
        "Residual is perpendicular:",
        approximately_equal(residual.dot(v), 0),
    )


# ============================================================================
# 22. GRAM-SCHMIDT ORTHONORMALIZATION
# ============================================================================

def gram_schmidt(vectors: Sequence[Vector]) -> List[Vector]:
    """
    Apply the Gram-Schmidt process.

    Starting with linearly independent vectors v1, ..., vk, construct
    orthonormal vectors q1, ..., qk spanning the same subspace.

    At each stage:

        u_k = v_k - sum_j projection_{q_j}(v_k)
        q_k = u_k / ||u_k||

    A dependent or numerically nearly dependent input raises ValueError.
    """
    orthonormal: List[Vector] = []

    for vector in vectors:
        residual = vector

        for basis_vector in orthonormal:
            residual = residual - orthogonal_projection(
                vector,
                basis_vector,
            )

        if approximately_equal(residual.norm(), 0):
            raise ValueError(
                "Input vectors are linearly dependent or numerically "
                "nearly dependent."
            )

        orthonormal.append(residual.unit())

    return orthonormal


def gram_schmidt_examples() -> None:
    print_section("19. Gram-Schmidt Orthonormalization")

    vectors = [
        Vector((1, 1)),
        Vector((1, 0)),
    ]

    orthonormal = gram_schmidt(vectors)

    print("Input vectors:")
    for vector in vectors:
        print(vector)

    print("\nOrthonormal basis:")
    for vector in orthonormal:
        print(vector)

    print("\nNorms:")
    for vector in orthonormal:
        print(format_number(vector.norm()))

    print("\nPairwise dot product:")
    print(format_number(orthonormal[0].dot(orthonormal[1])))


# ============================================================================
# 23. COLUMN SPACE, ROW SPACE, NULL SPACE
# ============================================================================

def pivot_columns(A: Matrix, tolerance: float = DEFAULT_TOLERANCE) -> List[int]:
    """
    Identify pivot columns of A by tracking pivot positions in RREF.

    RREF itself does not preserve the original column vectors, so the pivot
    column indices are obtained from the locations of leading ones.
    """
    R = reduced_row_echelon_form(A, tolerance)
    pivots = []

    for row in range(R.rows):
        for column in range(R.columns):
            if not approximately_equal(R[row][column], 0, tolerance):
                pivots.append(column)
                break

    return pivots


def column_space_basis(A: Matrix) -> List[Vector]:
    """Return original columns corresponding to pivot columns."""
    return [A.column(index) for index in pivot_columns(A)]


def null_space_basis_2x2(A: Matrix, tolerance: float = DEFAULT_TOLERANCE) -> List[Vector]:
    """
    Compute a simple null-space basis for a 2-column matrix.

    This educational implementation uses RREF and handles common 2-column
    cases explicitly. It demonstrates the relationship between free
    variables and solutions to A x = 0.
    """
    if A.columns != 2:
        raise ValueError("This educational helper expects exactly 2 columns.")

    R = reduced_row_echelon_form(A, tolerance)
    pivots = pivot_columns(A, tolerance)
    pivot_set = set(pivots)

    if len(pivots) == 2:
        return []

    if len(pivots) == 0:
        return [Vector((1, 0)), Vector((0, 1))]

    free_column = next(
        column for column in range(2)
        if column not in pivot_set
    )

    basis = [0.0, 0.0]
    basis[free_column] = 1.0

    pivot_column = pivots[0]

    # RREF contains x_pivot + R[pivot_row][free] * x_free = 0.
    pivot_row = next(
        row
        for row in range(R.rows)
        if not approximately_equal(R[row][pivot_column], 0, tolerance)
    )

    basis[pivot_column] = -R[pivot_row][free_column]

    return [Vector(basis)]


def space_examples() -> None:
    print_section("20. Column Space, Row Space, and Null Space")

    A = Matrix(
        [
            [1, 2],
            [2, 4],
            [3, 6],
        ]
    )

    print("A:")
    print(A.pretty())

    print("\nRREF(A):")
    print(reduced_row_echelon_form(A).pretty())

    print("\nRank(A):", rank(A))

    print("\nPivot columns:", pivot_columns(A))

    print("\nColumn-space basis:")
    for vector in column_space_basis(A):
        print(vector)

    print("\nNull-space basis:")
    for vector in null_space_basis_2x2(A):
        print(vector)


# ============================================================================
# 24. BASIS AND COORDINATES
# ============================================================================

def coordinates_in_basis(
    basis: Sequence[Vector],
    target: Vector,
) -> Vector:
    """
    Find coordinates c satisfying:

        c1*b1 + ... + cn*bn = target.

    The basis vectors become columns of a square matrix B, giving:

        Bc = target.
    """
    if len(basis) != target.dimension:
        raise ValueError(
            "A basis for R^n must contain n vectors for this implementation."
        )

    if any(vector.dimension != target.dimension for vector in basis):
        raise ValueError("Basis vectors must match target dimension.")

    B = Matrix(
        [
            [basis[column][row] for column in range(len(basis))]
            for row in range(target.dimension)
        ]
    )

    return solve_linear_system(B, target)


def basis_examples() -> None:
    print_section("21. Basis and Coordinates")

    basis = [
        Vector((1, 1)),
        Vector((1, -1)),
    ]

    target = Vector((5, 1))

    coordinates = coordinates_in_basis(basis, target)

    print("Basis:")
    for vector in basis:
        print(vector)

    print("Target:", target)
    print("Coordinates relative to basis:", coordinates)

    reconstructed = linear_combination(basis, coordinates.components)

    print("Reconstructed target:", reconstructed)


# ============================================================================
# 25. AFFINE COMBINATIONS
# ============================================================================

def affine_combination(
    vectors: Sequence[Vector],
    weights: Sequence[float],
) -> Vector:
    """
    Compute an affine combination.

    An affine combination has weights satisfying:

        w1 + w2 + ... + wk = 1

    Unlike a general linear combination, the coefficients are constrained to
    sum to one. Affine combinations are central to points, interpolation,
    barycentric coordinates, and affine geometry.
    """
    if not vectors:
        raise ValueError("At least one vector is required.")

    if len(vectors) != len(weights):
        raise ValueError("Vectors and weights must have equal lengths.")

    if not approximately_equal(sum(weights), 1):
        raise ValueError("Affine-combination weights must sum to 1.")

    return linear_combination(vectors, weights)


def affine_examples() -> None:
    print_section("22. Affine Combinations")

    p = Vector((0, 0))
    q = Vector((10, 10))

    midpoint = affine_combination(
        [p, q],
        [0.5, 0.5],
    )

    quarter = affine_combination(
        [p, q],
        [0.75, 0.25],
    )

    print("p =", p)
    print("q =", q)
    print("midpoint =", midpoint)
    print("point at 25% from q toward p =", quarter)


# ============================================================================
# 26. SYMMETRIC MATRICES
# ============================================================================

def is_symmetric(A: Matrix, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    """A is symmetric when A = A^T."""
    if not A.is_square():
        return False

    return matrices_equal(A, A.transpose(), tolerance)


def symmetric_matrix_examples() -> None:
    print_section("23. Symmetric Matrices")

    A = Matrix(
        [
            [2, 3, 5],
            [3, 4, 6],
            [5, 6, 9],
        ]
    )

    B = Matrix(
        [
            [1, 2],
            [3, 4],
        ]
    )

    print("A:")
    print(A.pretty())
    print("Symmetric:", is_symmetric(A))

    print("\nB:")
    print(B.pretty())
    print("Symmetric:", is_symmetric(B))

    # Every real square matrix can be decomposed into symmetric and
    # skew-symmetric parts:
    #
    # A = (A + A^T)/2 + (A - A^T)/2
    #
    # This illustrates structural decomposition of matrices.
    symmetric_part = 0.5 * (B + B.transpose())
    skew_part = 0.5 * (B - B.transpose())

    print("\nSymmetric part of B:")
    print(symmetric_part.pretty())

    print("\nSkew-symmetric part of B:")
    print(skew_part.pretty())


# ============================================================================
# 27. DIAGONAL AND TRIANGULAR MATRICES
# ============================================================================

def is_diagonal(A: Matrix, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    if not A.is_square():
        return False

    return all(
        approximately_equal(A[i][j], 0, tolerance)
        for i in range(A.rows)
        for j in range(A.columns)
        if i != j
    )


def triangular_examples() -> None:
    print_section("24. Diagonal and Triangular Structure")

    upper = Matrix(
        [
            [2, 3, 4],
            [0, 5, 6],
            [0, 0, 7],
        ]
    )

    lower = Matrix(
        [
            [2, 0, 0],
            [3, 5, 0],
            [4, 6, 7],
        ]
    )

    diagonal = diagonal_matrix([2, 5, 7])

    print("Upper triangular:")
    print(upper.pretty())

    print("\nLower triangular:")
    print(lower.pretty())

    print("\nDiagonal:")
    print(diagonal.pretty())

    print("\nIs diagonal:", is_diagonal(diagonal))

    # For triangular matrices, determinant is the product of diagonal entries.
    print(
        "det(upper) from general determinant =",
        format_number(determinant(upper)),
    )
    print(
        "Product of diagonal entries =",
        format_number(2 * 5 * 7),
    )


# ============================================================================
# 28. BLOCK MATRICES
# ============================================================================

def block_matrix_examples() -> None:
    print_section("25. Block-Matrix Thinking")

    """
    A large matrix can be viewed as smaller rectangular blocks.

    Example:

        [ A B ]
        [ C D ]

    Block notation is useful when matrices have natural subsystems,
    especially in numerical linear algebra, statistics, optimization,
    control, and computer graphics.
    """

    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[5], [6]])
    C = Matrix([[7, 8]])
    D = Matrix([[9]])

    combined = Matrix(
        [
            [A[0][0], A[0][1], B[0][0]],
            [A[1][0], A[1][1], B[1][0]],
            [C[0][0], C[0][1], D[0][0]],
        ]
    )

    print("Block matrix [A B; C D]:")
    print(combined.pretty())


# ============================================================================
# 29. OUTER PRODUCT
# ============================================================================

def outer_product(u: Vector, v: Vector) -> Matrix:
    """
    Compute the outer product:

        u v^T

    If u has m components and v has n components, the result is m x n.

    Each entry is:

        (u v^T)_ij = u_i v_j

    The outer product should not be confused with the dot product, which
    produces a scalar.
    """
    return Matrix(
        [
            [u[i] * v[j] for j in range(v.dimension)]
            for i in range(u.dimension)
        ]
    )


def outer_product_examples() -> None:
    print_section("26. Outer Product")

    u = Vector((1, 2, 3))
    v = Vector((4, 5))

    print("u =", u)
    print("v =", v)

    print("\nOuter product u v^T:")
    print(outer_product(u, v).pretty())

    print("\nDot product u · [4, 5, 6]:")
    print(u.dot(Vector((4, 5, 6))))


# ============================================================================
# 30. HADAMARD ELEMENT-WISE PRODUCT
# ============================================================================

def hadamard_product(A: Matrix, B: Matrix) -> Matrix:
    """
    Element-wise matrix multiplication.

    A ⊙ B has entries:

        (A ⊙ B)_ij = A_ij B_ij

    This is different from ordinary matrix multiplication A @ B.
    """
    A._check_same_shape(B)

    return Matrix(
        [
            [a * b for a, b in zip(row_a, row_b)]
            for row_a, row_b in zip(A, B)
        ]
    )


def hadamard_examples() -> None:
    print_section("27. Hadamard Product")

    A = Matrix(
        [
            [1, 2],
            [3, 4],
        ]
    )

    B = Matrix(
        [
            [5, 6],
            [7, 8],
        ]
    )

    print("A ⊙ B:")
    print(hadamard_product(A, B).pretty())

    print("\nA @ B:")
    print((A @ B).pretty())

    print(
        "\nImportant distinction: element-wise multiplication and "
        "matrix multiplication are different operations."
    )


# ============================================================================
# 31. TRACE IDENTITIES
# ============================================================================

def trace_examples() -> None:
    print_section("28. Trace Identities")

    A = Matrix(
        [
            [1, 2],
            [3, 4],
        ]
    )

    B = Matrix(
        [
            [5, 6],
            [7, 8],
        ]
    )

    print("trace(A) =", format_number(A.trace()))
    print("trace(B) =", format_number(B.trace()))
    print("trace(A + B) =", format_number((A + B).trace()))
    print(
        "trace(A) + trace(B) =",
        format_number(A.trace() + B.trace()),
    )

    # For compatible square matrices:
    # trace(AB) = trace(BA), even though AB and BA need not be equal.
    AB = A @ B
    BA = B @ A

    print("\ntrace(AB) =", format_number(AB.trace()))
    print("trace(BA) =", format_number(BA.trace()))


# ============================================================================
# 32. DETERMINANT IDENTITIES
# ============================================================================

def determinant_identity_examples() -> None:
    print_section("29. Important Determinant Identities")

    A = Matrix(
        [
            [1, 2],
            [3, 5],
        ]
    )

    B = Matrix(
        [
            [2, 0],
            [1, 4],
        ]
    )

    det_a = determinant(A)
    det_b = determinant(B)
    det_ab = determinant(A @ B)

    print("det(A) =", format_number(det_a))
    print("det(B) =", format_number(det_b))
    print("det(AB) =", format_number(det_ab))
    print(
        "det(A)det(B) =",
        format_number(det_a * det_b),
    )

    print(
        "Multiplicative identity holds:",
        approximately_equal(det_ab, det_a * det_b),
    )


# ============================================================================
# 33. VECTOR NORMS
# ============================================================================

def l1_norm(vector: Vector) -> float:
    """Manhattan / L1 norm: sum |x_i|."""
    return sum(abs(x) for x in vector)


def linf_norm(vector: Vector) -> float:
    """Infinity norm: max |x_i|."""
    return max(abs(x) for x in vector)


def norm_examples() -> None:
    print_section("30. Vector Norms")

    v = Vector((-3, 4, -5))

    print("v =", v)
    print("L1 norm =", format_number(l1_norm(v)))
    print("L2 norm =", format_number(v.norm()))
    print("L-infinity norm =", format_number(linf_norm(v)))

    # Different norms measure size differently.
    # The Euclidean norm is the standard geometric length.
    # L1 is common in sparsity-oriented optimization.
    # L-infinity measures the largest absolute component.


# ============================================================================
# 34. DISTANCE AND NEAREST-POINT IDEAS
# ============================================================================

def distance_examples() -> None:
    print_section("31. Distance")

    a = Vector((1, 2))
    b = Vector((4, 6))

    difference = b - a

    print("a =", a)
    print("b =", b)
    print("b - a =", difference)
    print("Euclidean distance =", format_number(a.distance_to(b)))

    # Distance can be viewed as the norm of a difference:
    #
    # d(a, b) = ||a - b||
    #
    # This is fundamental in geometry, clustering, nearest-neighbor methods,
    # optimization, and many numerical algorithms.


# ============================================================================
# 35. LINEAR VERSUS AFFINE STRUCTURE
# ============================================================================

def linear_vs_affine_examples() -> None:
    print_section("32. Linear and Affine Structure")

    """
    A linear subspace must contain the zero vector and be closed under
    vector addition and scalar multiplication.

    An affine set can be a translated subspace and need not contain zero.

    Example:
        y = 2x

    is a line through the origin and is a linear subspace of R^2.

    Example:
        y = 2x + 1

    is an affine line but is not a linear subspace because it does not
    contain (0, 0).
    """

    origin_line_direction = Vector((1, 2))

    print("Linear line through origin:")
    print("t =", origin_line_direction)

    point = Vector((0, 1))
    direction = Vector((1, 2))

    print("\nAffine line:")
    print("point =", point)
    print("direction =", direction)
    print("point at t=3 =", point + 3 * direction)


# ============================================================================
# 36. NUMERICAL STABILITY AND TOLERANCE
# ============================================================================

def numerical_precision_examples() -> None:
    print_section("33. Floating-Point Precision")

    value = 0.1 + 0.2

    print("0.1 + 0.2 =", value)
    print("Exact comparison with 0.3:", value == 0.3)
    print(
        "Approximate comparison:",
        approximately_equal(value, 0.3),
    )

    """
    Exact equality is often inappropriate after floating-point operations.

    A tolerance should be chosen according to the numerical scale and
    conditioning of the problem. A fixed tolerance is adequate for teaching
    simple examples but is not universally safe for production numerical
    software.
    """


# ============================================================================
# 37. CONDITIONING AND SINGULARITY
# ============================================================================

def conditioning_examples() -> None:
    print_section("34. Conditioning and Near-Singularity")

    A = Matrix(
        [
            [1.0, 1.0],
            [1.0, 1.000001],
        ]
    )

    print("Nearly dependent matrix:")
    print(A.pretty())

    print("det(A) =", determinant(A))
    print("rank(A) under default tolerance =", rank(A))

    """
    A matrix can be invertible mathematically while being numerically close
    to singular.

    The condition number measures sensitivity of a problem to perturbations.
    A large condition number indicates that small input errors can cause
    large output errors.

    This distinction matters in scientific computing: mathematical
    invertibility alone does not guarantee numerically reliable computation.
    """


# ============================================================================
# 38. EDGE CASES
# ============================================================================

def edge_case_examples() -> None:
    print_section("35. Important Edge Cases")

    cases = []

    # Dimension mismatch.
    try:
        Vector((1, 2)) + Vector((1, 2, 3))
    except ValueError as error:
        cases.append(f"Vector dimension mismatch: {error}")

    # Invalid matrix multiplication.
    try:
        Matrix([[1, 2]]) @ Matrix([[1, 2]])
    except ValueError as error:
        cases.append(f"Matrix shape mismatch: {error}")

    # Zero-vector normalization.
    try:
        Vector((0, 0)).unit()
    except ValueError as error:
        cases.append(f"Zero-vector normalization: {error}")

    # Non-square determinant.
    try:
        determinant(Matrix([[1, 2, 3], [4, 5, 6]]))
    except ValueError as error:
        cases.append(f"Non-square determinant: {error}")

    # Singular inverse.
    try:
        inverse(Matrix([[1, 2], [2, 4]]))
    except ValueError as error:
        cases.append(f"Singular inverse: {error}")

    for case in cases:
        print(case)


# ============================================================================
# 39. COMMON MISTAKES
# ============================================================================

def common_mistakes_examples() -> None:
    print_section("36. Common Conceptual Mistakes")

    """
    Mistake 1:
        Assuming matrix multiplication is element-wise.

    Correct:
        A @ B uses row-column products.

    Mistake 2:
        Assuming AB = BA.

    Correct:
        Matrix multiplication is generally non-commutative.

    Mistake 3:
        Adding matrices with different shapes.

    Correct:
        A and B must have the same shape for A + B.

    Mistake 4:
        Multiplying any two matrices.

    Correct:
        columns(A) must equal rows(B).

    Mistake 5:
        Assuming every square matrix has an inverse.

    Correct:
        A square matrix is invertible only when it is nonsingular.

    Mistake 6:
        Treating row and column vectors as interchangeable in every
        multiplication expression.

    Correct:
        Their shapes determine which products are valid.

    Mistake 7:
        Testing floating-point results only with ==.

    Correct:
        Use an appropriate numerical tolerance.
    """

    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[5, 6], [7, 8]])

    print("A @ B:")
    print((A @ B).pretty())

    print("\nA ⊙ B:")
    print(hadamard_product(A, B).pretty())


# ============================================================================
# 40. PRACTICAL EXAMPLE: 2D LINEAR TRANSFORMATIONS
# ============================================================================

def practical_2d_transformation() -> None:
    print_section("37. Practical Example: 2D Transformation")

    """
    Consider a point/vector p = (2, 1).

    First scale x by 2 and y by 3:

        S = [2 0]
            [0 3]

    Then rotate by 90 degrees counterclockwise:

        R = [0 -1]
            [1  0]

    Applying S and then R gives:

        R(S p)

    Matrix composition is represented by multiplication:

        R S p

    The order matters because matrix multiplication is generally
    non-commutative.
    """

    p = Vector((2, 1))

    S = Matrix(
        [
            [2, 0],
            [0, 3],
        ]
    )

    R = Matrix(
        [
            [0, -1],
            [1, 0],
        ]
    )

    result = R @ (S @ p)
    composed = (R @ S) @ p

    print("p =", p)
    print("Scaled then rotated =", result)
    print("Using composed matrix =", composed)
    print("Equivalent:", vectors_equal(result, composed))


# ============================================================================
# 41. PRACTICAL EXAMPLE: LINEAR MODEL
# ============================================================================

def linear_model_example() -> None:
    print_section("38. Practical Example: Linear Model")

    """
    Suppose a simple model uses two features:

        x1 = study hours
        x2 = practice hours

    and weights:

        w1 = 2
        w2 = 3

    with bias b = 5.

    Prediction:

        y = w^T x + b

    The dot product expresses the weighted sum compactly.
    """

    features = Vector((4, 2))
    weights = Vector((2, 3))
    bias = 5

    prediction = weights.dot(features) + bias

    print("features =", features)
    print("weights =", weights)
    print("bias =", bias)
    print("prediction =", format_number(prediction))


# ============================================================================
# 42. PRACTICAL EXAMPLE: PORTFOLIO-LIKE LINEAR COMBINATION
# ============================================================================

def linear_combination_application() -> None:
    print_section("39. Practical Example: Weighted Quantities")

    """
    A weighted combination can represent an aggregate quantity.

    Suppose three components have values [100, 80, 120] and weights
    [0.5, 0.3, 0.2].

    The weighted result is their dot product.

    This is mathematically the same operation used in many applications
    involving weighted sums.
    """

    values = Vector((100, 80, 120))
    weights = Vector((0.5, 0.3, 0.2))

    result = values.dot(weights)

    print("values =", values)
    print("weights =", weights)
    print("weighted result =", format_number(result))


# ============================================================================
# 43. PRACTICAL EXAMPLE: SYSTEM OF EQUATIONS
# ============================================================================

def system_application() -> None:
    print_section("40. Practical Example: Simultaneous Equations")

    """
    Consider:

        2x + y = 7
        x - y = 1

    In matrix form:

        [2  1] [x] = [7]
        [1 -1] [y]   [1]

    This is:

        A x = b
    """

    A = Matrix(
        [
            [2, 1],
            [1, -1],
        ]
    )

    b = Vector((7, 1))
    x = solve_linear_system(A, b)

    print("A:")
    print(A.pretty())
    print("b:", b)
    print("solution:", x)
    print("verification:", A @ x)


# ============================================================================
# 44. TESTS
# ============================================================================

def run_tests() -> None:
    """
    Lightweight tests using only Python's standard library.

    These checks validate the core implementations and also demonstrate
    expected mathematical identities.
    """
    print_section("41. Automated Tests")

    # Vector tests.
    a = Vector((1, 2))
    b = Vector((3, 4))

    assert vectors_equal(a + b, Vector((4, 6)))
    assert vectors_equal(b - a, Vector((2, 2)))
    assert vectors_equal(2 * a, Vector((2, 4)))
    assert approximately_equal(a.dot(b), 11)
    assert approximately_equal(a.norm(), sqrt(5))

    # Matrix tests.
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[5, 6], [7, 8]])

    assert matrices_equal(
        A + B,
        Matrix([[6, 8], [10, 12]]),
    )

    assert matrices_equal(
        A @ B,
        Matrix([[19, 22], [43, 50]]),
    )

    assert matrices_equal(
        A.transpose(),
        Matrix([[1, 3], [2, 4]]),
    )

    # Determinant.
    assert approximately_equal(determinant(A), -2)

    # Inverse.
    A_inv = inverse(A)
    assert matrices_equal(
        A @ A_inv,
        identity_matrix(2),
    )

    # Linear system.
    solution = solve_linear_system(
        Matrix([[2, 1], [1, -1]]),
        Vector((7, 1)),
    )

    assert vectors_equal(solution, Vector((8 / 3, 1 / 3)))

    # Rank.
    assert rank(Matrix([[1, 2], [2, 4]])) == 1
    assert rank(Matrix([[1, 0], [0, 1]])) == 2

    # Orthogonality.
    orthogonal = Vector((1, 0))
    other = Vector((0, 1))
    assert approximately_equal(orthogonal.dot(other), 0)

    # Gram-Schmidt.
    basis = gram_schmidt(
        [
            Vector((1, 1)),
            Vector((1, 0)),
        ]
    )

    assert all(approximately_equal(vector.norm(), 1) for vector in basis)
    assert approximately_equal(basis[0].dot(basis[1]), 0)

    # Determinant product identity.
    C = Matrix([[2, 1], [1, 3]])
    D = Matrix([[4, 0], [1, 2]])

    assert approximately_equal(
        determinant(C @ D),
        determinant(C) * determinant(D),
    )

    print("All tests passed.")


# ============================================================================
# 45. MINI REFERENCE TABLE
# ============================================================================

def reference_examples() -> None:
    print_section("42. Compact Reference")

    reference = [
        ("Vector addition", "u + v", "Same dimension"),
        ("Scalar multiplication", "c v", "Any scalar c"),
        ("Dot product", "u · v", "Same dimension; scalar result"),
        ("Vector norm", "||v||", "Nonnegative scalar"),
        ("Matrix addition", "A + B", "Same shape"),
        ("Matrix transpose", "A^T", "Rows become columns"),
        ("Matrix product", "AB", "columns(A) = rows(B)"),
        ("Matrix-vector product", "Ax", "columns(A) = dimension(x)"),
        ("Identity", "I", "AI = IA = A"),
        ("Determinant", "det(A)", "Square matrices"),
        ("Inverse", "A^-1", "Square nonsingular matrices"),
        ("Rank", "rank(A)", "Number of pivots"),
        ("Trace", "tr(A)", "Square matrices"),
        ("Outer product", "uv^T", "Produces a matrix"),
        ("Hadamard product", "A ⊙ B", "Same shape; element-wise"),
    ]

    for name, notation, condition in reference:
        print(f"{name:24} | {notation:12} | {condition}")


# ============================================================================
# 46. COMPLETE DEMONSTRATION
# ============================================================================

def run_course() -> None:
    """
    Execute the complete educational sequence.

    The ordering moves from scalars and vectors to matrices, transformations,
    systems, subspaces, numerical issues, and practical applications.
    """
    scalar_examples()
    vector_examples()
    vector_geometry_examples()
    cross_product_examples()
    matrix_examples()
    special_matrix_examples()
    matrix_multiplication_examples()
    linear_combination_examples()
    linear_independence_examples()
    transformation_examples()
    row_column_vector_examples()
    determinant_examples()
    cofactor_examples()
    elimination_examples()
    rank_examples()
    linear_system_examples()
    inverse_examples()
    orthogonality_examples()
    gram_schmidt_examples()
    space_examples()
    basis_examples()
    affine_examples()
    symmetric_matrix_examples()
    triangular_examples()
    block_matrix_examples()
    outer_product_examples()
    hadamard_examples()
    trace_examples()
    determinant_identity_examples()
    norm_examples()
    distance_examples()
    linear_vs_affine_examples()
    numerical_precision_examples()
    conditioning_examples()
    edge_case_examples()
    common_mistakes_examples()
    practical_2d_transformation()
    linear_model_example()
    linear_combination_application()
    system_application()
    reference_examples()
    run_tests()


# ============================================================================
# 47. ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    run_course()
