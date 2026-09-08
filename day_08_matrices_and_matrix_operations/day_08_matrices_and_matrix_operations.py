"""
Matrices & Matrix Operations
============================

A self-contained study script covering matrices from absolute fundamentals
through intermediate and advanced operations.

Topics:
1. Matrix terminology and representation
2. Creating and validating matrices
3. Matrix dimensions and shapes
4. Addition and subtraction
5. Scalar multiplication
6. Transpose
7. Matrix multiplication
8. Identity and zero matrices
9. Determinants
10. Minors and cofactors
11. Adjugate matrices
12. Matrix inverse
13. Gaussian elimination
14. Gauss-Jordan elimination
15. Solving systems of linear equations
16. Rank
17. Matrix properties and identities
18. Special matrix classifications
19. Numerical precision and floating-point issues
20. Performance considerations
21. Practical applications
22. Testing and debugging matrix operations

Only the Python standard library is used.
"""

from __future__ import annotations

from copy import deepcopy
from math import isclose
from typing import Iterable, List, Sequence, Tuple, Union

Number = Union[int, float]
Matrix = List[List[Number]]

EPSILON = 1e-10


# ============================================================================
# 1. FUNDAMENTAL MATRIX REPRESENTATION
# ============================================================================

def matrix_shape(matrix: Matrix) -> Tuple[int, int]:
    """
    Return the shape of a matrix as (rows, columns).

    A valid matrix must be rectangular: every row must contain the same
    number of elements.

    Examples:
        [[1, 2], [3, 4]] -> (2, 2)
        [[1, 2, 3]]       -> (1, 3)
    """
    if not isinstance(matrix, list) or len(matrix) == 0:
        raise ValueError("A matrix must be a non-empty list of rows.")

    if not all(isinstance(row, list) for row in matrix):
        raise TypeError("Each matrix row must be a list.")

    columns = len(matrix[0])

    if columns == 0:
        raise ValueError("A matrix cannot contain empty rows.")

    for row in matrix:
        if len(row) != columns:
            raise ValueError(
                "Invalid matrix: all rows must have the same number of columns."
            )

    return len(matrix), columns


def validate_numeric_matrix(matrix: Matrix) -> None:
    """Validate that a matrix is rectangular and contains numeric values."""
    matrix_shape(matrix)

    for row in matrix:
        for value in row:
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Matrix values must be int or float, received {type(value).__name__}."
                )


def copy_matrix(matrix: Matrix) -> Matrix:
    """Return an independent copy of a matrix."""
    return [row[:] for row in matrix]


def print_matrix(
    matrix: Matrix,
    title: str = "",
    precision: int = 6,
    width: int = 12,
) -> None:
    """
    Print a matrix in aligned form.

    Small floating-point values close to zero are displayed as zero to make
    results from numerical algorithms easier to read.
    """
    validate_numeric_matrix(matrix)

    if title:
        print(title)

    for row in matrix:
        formatted_values = []

        for value in row:
            display_value = 0 if abs(value) < EPSILON else value

            if isinstance(display_value, float):
                text = f"{display_value:.{precision}g}"
            else:
                text = str(display_value)

            formatted_values.append(f"{text:>{width}}")

        print("[" + " ".join(formatted_values) + " ]")

    print()


# ============================================================================
# 2. MATRIX CREATION
# ============================================================================

def zeros(rows: int, columns: int) -> Matrix:
    """
    Create a zero matrix.

    Example:
        zeros(2, 3)

    Produces:
        [[0, 0, 0],
         [0, 0, 0]]
    """
    if rows <= 0 or columns <= 0:
        raise ValueError("Matrix dimensions must be positive.")

    return [[0 for _ in range(columns)] for _ in range(rows)]


def identity(size: int) -> Matrix:
    """
    Create a square identity matrix.

    The identity matrix I satisfies:
        A * I = I * A = A

    for any compatible square matrix A.
    """
    if size <= 0:
        raise ValueError("Identity matrix size must be positive.")

    return [
        [1 if row == column else 0 for column in range(size)]
        for row in range(size)
    ]


def diagonal_matrix(diagonal_values: Sequence[Number]) -> Matrix:
    """Create a diagonal matrix from a sequence of diagonal values."""
    if len(diagonal_values) == 0:
        raise ValueError("At least one diagonal value is required.")

    size = len(diagonal_values)

    return [
        [
            diagonal_values[row] if row == column else 0
            for column in range(size)
        ]
        for row in range(size)
    ]


def constant_matrix(rows: int, columns: int, value: Number) -> Matrix:
    """Create a matrix whose entries all contain the same value."""
    if rows <= 0 or columns <= 0:
        raise ValueError("Matrix dimensions must be positive.")

    return [[value for _ in range(columns)] for _ in range(rows)]


# ============================================================================
# 3. MATRIX CLASSIFICATION
# ============================================================================

def is_square(matrix: Matrix) -> bool:
    """Return True when a matrix has equal numbers of rows and columns."""
    rows, columns = matrix_shape(matrix)
    return rows == columns


def is_zero_matrix(matrix: Matrix, tolerance: float = EPSILON) -> bool:
    """Return True when every entry is approximately zero."""
    validate_numeric_matrix(matrix)

    return all(abs(value) < tolerance for row in matrix for value in row)


def is_diagonal(matrix: Matrix, tolerance: float = EPSILON) -> bool:
    """
    Return True when every off-diagonal element is zero.

    A diagonal matrix must be square.
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        return False

    size = len(matrix)

    for row in range(size):
        for column in range(size):
            if row != column and abs(matrix[row][column]) >= tolerance:
                return False

    return True


def is_upper_triangular(matrix: Matrix, tolerance: float = EPSILON) -> bool:
    """
    Return True if all elements below the main diagonal are zero.

    Example:
        [1 2 3]
        [0 4 5]
        [0 0 6]
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        return False

    size = len(matrix)

    for row in range(size):
        for column in range(row):
            if abs(matrix[row][column]) >= tolerance:
                return False

    return True


def is_lower_triangular(matrix: Matrix, tolerance: float = EPSILON) -> bool:
    """
    Return True if all elements above the main diagonal are zero.

    Example:
        [1 0 0]
        [2 3 0]
        [4 5 6]
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        return False

    size = len(matrix)

    for row in range(size):
        for column in range(row + 1, size):
            if abs(matrix[row][column]) >= tolerance:
                return False

    return True


def is_symmetric(matrix: Matrix, tolerance: float = EPSILON) -> bool:
    """
    Return True if A = A^T.

    A symmetric matrix must be square.
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        return False

    rows, columns = matrix_shape(matrix)

    for row in range(rows):
        for column in range(columns):
            if abs(matrix[row][column] - matrix[column][row]) >= tolerance:
                return False

    return True


# ============================================================================
# 4. BASIC MATRIX OPERATIONS
# ============================================================================

def add_matrices(matrix_a: Matrix, matrix_b: Matrix) -> Matrix:
    """
    Add two matrices element by element.

    Both matrices must have identical shapes.

        (A + B)[i][j] = A[i][j] + B[i][j]
    """
    validate_numeric_matrix(matrix_a)
    validate_numeric_matrix(matrix_b)

    if matrix_shape(matrix_a) != matrix_shape(matrix_b):
        raise ValueError(
            "Matrix addition requires matrices with identical dimensions."
        )

    rows, columns = matrix_shape(matrix_a)

    return [
        [
            matrix_a[row][column] + matrix_b[row][column]
            for column in range(columns)
        ]
        for row in range(rows)
    ]


def subtract_matrices(matrix_a: Matrix, matrix_b: Matrix) -> Matrix:
    """
    Subtract matrix B from matrix A element by element.

        (A - B)[i][j] = A[i][j] - B[i][j]
    """
    validate_numeric_matrix(matrix_a)
    validate_numeric_matrix(matrix_b)

    if matrix_shape(matrix_a) != matrix_shape(matrix_b):
        raise ValueError(
            "Matrix subtraction requires matrices with identical dimensions."
        )

    rows, columns = matrix_shape(matrix_a)

    return [
        [
            matrix_a[row][column] - matrix_b[row][column]
            for column in range(columns)
        ]
        for row in range(rows)
    ]


def scalar_multiply(scalar: Number, matrix: Matrix) -> Matrix:
    """
    Multiply every matrix entry by a scalar.

        (cA)[i][j] = c * A[i][j]
    """
    if not isinstance(scalar, (int, float)):
        raise TypeError("The scalar must be numeric.")

    validate_numeric_matrix(matrix)

    return [
        [scalar * value for value in row]
        for row in matrix
    ]


def transpose(matrix: Matrix) -> Matrix:
    """
    Compute the transpose of a matrix.

    Rows become columns:

        A has shape m x n
        A^T has shape n x m

    Example:
        [1 2 3]      [1 4]
        [4 5 6]  ->  [2 5]
                     [3 6]
    """
    validate_numeric_matrix(matrix)

    rows, columns = matrix_shape(matrix)

    return [
        [matrix[row][column] for row in range(rows)]
        for column in range(columns)
    ]


# ============================================================================
# 5. MATRIX MULTIPLICATION
# ============================================================================

def multiply_matrices(matrix_a: Matrix, matrix_b: Matrix) -> Matrix:
    """
    Multiply two matrices.

    If:
        A has shape m x n
        B has shape n x p

    then:
        A * B has shape m x p

    The number of columns in A must equal the number of rows in B.

    Each output element is a dot product:

        C[i][j] = sum(A[i][k] * B[k][j])

    Important:
        Matrix multiplication is generally NOT commutative.

        A * B may not equal B * A.
    """
    validate_numeric_matrix(matrix_a)
    validate_numeric_matrix(matrix_b)

    rows_a, columns_a = matrix_shape(matrix_a)
    rows_b, columns_b = matrix_shape(matrix_b)

    if columns_a != rows_b:
        raise ValueError(
            f"Cannot multiply matrices with shapes "
            f"{rows_a}x{columns_a} and {rows_b}x{columns_b}. "
            f"The first matrix has {columns_a} columns while the second "
            f"has {rows_b} rows."
        )

    result = zeros(rows_a, columns_b)

    for row in range(rows_a):
        for column in range(columns_b):
            total = 0

            for shared_index in range(columns_a):
                total += (
                    matrix_a[row][shared_index]
                    * matrix_b[shared_index][column]
                )

            result[row][column] = total

    return result


def multiply_matrix_vector(matrix: Matrix, vector: Sequence[Number]) -> List[Number]:
    """
    Multiply a matrix by a column vector represented as a Python sequence.

    If A has shape m x n, the vector must contain n elements.
    The result contains m elements.
    """
    validate_numeric_matrix(matrix)

    rows, columns = matrix_shape(matrix)

    if len(vector) != columns:
        raise ValueError(
            f"Matrix has {columns} columns but vector has {len(vector)} elements."
        )

    return [
        sum(matrix[row][column] * vector[column] for column in range(columns))
        for row in range(rows)
    ]


def matrix_power(matrix: Matrix, exponent: int) -> Matrix:
    """
    Compute A^n for a square matrix using exponentiation by squaring.

    Rules:
        A^0 = I
        A^1 = A
        A^n = A * A * ... * A

    This implementation is significantly faster than repeated multiplication
    for large exponents.

    Negative exponents use the inverse:

        A^(-n) = (A^-1)^n
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        raise ValueError("Matrix powers require a square matrix.")

    if not isinstance(exponent, int):
        raise TypeError("The exponent must be an integer.")

    size = len(matrix)

    if exponent == 0:
        return identity(size)

    if exponent < 0:
        return matrix_power(inverse(matrix), -exponent)

    result = identity(size)
    base = copy_matrix(matrix)
    power = exponent

    while power > 0:
        if power % 2 == 1:
            result = multiply_matrices(result, base)

        base = multiply_matrices(base, base)
        power //= 2

    return result


# ============================================================================
# 6. MATRIX MINORS, DETERMINANTS, AND COFACTORS
# ============================================================================

def minor_matrix(matrix: Matrix, remove_row: int, remove_column: int) -> Matrix:
    """
    Return the submatrix obtained by removing one row and one column.

    Minors are used when computing determinants and cofactors.
    """
    validate_numeric_matrix(matrix)

    rows, columns = matrix_shape(matrix)

    if not is_square(matrix):
        raise ValueError("Minors in this implementation require a square matrix.")

    if not (0 <= remove_row < rows and 0 <= remove_column < columns):
        raise IndexError("Row or column index is outside the matrix.")

    return [
        [
            matrix[row][column]
            for column in range(columns)
            if column != remove_column
        ]
        for row in range(rows)
        if row != remove_row
    ]


def determinant_recursive(matrix: Matrix) -> Number:
    """
    Compute a determinant using cofactor expansion.

    This method is educational and straightforward but expensive for larger
    matrices because its time complexity grows approximately factorially.

    Use determinant_elimination() for larger practical matrices.
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        raise ValueError("Determinants are defined only for square matrices.")

    size = len(matrix)

    if size == 1:
        return matrix[0][0]

    if size == 2:
        return (
            matrix[0][0] * matrix[1][1]
            - matrix[0][1] * matrix[1][0]
        )

    determinant_value = 0

    for column in range(size):
        sign = 1 if column % 2 == 0 else -1

        determinant_value += (
            sign
            * matrix[0][column]
            * determinant_recursive(minor_matrix(matrix, 0, column))
        )

    return determinant_value


def determinant_elimination(matrix: Matrix) -> Number:
    """
    Compute a determinant using Gaussian elimination with partial pivoting.

    Row operations affect determinants as follows:

    1. Swapping two rows changes the sign.
    2. Multiplying a row by c multiplies the determinant by c.
    3. Adding a multiple of one row to another does not change the determinant.

    The implementation converts the matrix to upper triangular form.

    For an upper triangular matrix:

        det(A) = product of diagonal entries
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        raise ValueError("Determinants are defined only for square matrices.")

    working = [
        [float(value) for value in row]
        for row in matrix
    ]

    size = len(working)
    sign = 1

    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(working[row][pivot_column]),
        )

        if abs(working[pivot_row][pivot_column]) < EPSILON:
            return 0

        if pivot_row != pivot_column:
            working[pivot_column], working[pivot_row] = (
                working[pivot_row],
                working[pivot_column],
            )
            sign *= -1

        pivot = working[pivot_column][pivot_column]

        for row in range(pivot_column + 1, size):
            factor = working[row][pivot_column] / pivot

            for column in range(pivot_column, size):
                working[row][column] -= (
                    factor * working[pivot_column][column]
                )

    result = sign

    for index in range(size):
        result *= working[index][index]

    return result


def cofactor(matrix: Matrix, row: int, column: int) -> Number:
    """
    Compute the cofactor C(row, column):

        C(i, j) = (-1)^(i+j) * det(M(i, j))

    where M(i, j) is the minor matrix.
    """
    sign = 1 if (row + column) % 2 == 0 else -1

    return sign * determinant_recursive(
        minor_matrix(matrix, row, column)
    )


def cofactor_matrix(matrix: Matrix) -> Matrix:
    """Return the matrix containing every cofactor."""
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        raise ValueError("A cofactor matrix requires a square matrix.")

    size = len(matrix)

    return [
        [
            cofactor(matrix, row, column)
            for column in range(size)
        ]
        for row in range(size)
    ]


def adjugate(matrix: Matrix) -> Matrix:
    """
    Return the adjugate matrix.

        adj(A) = transpose(cofactor_matrix(A))
    """
    return transpose(cofactor_matrix(matrix))


# ============================================================================
# 7. MATRIX INVERSE
# ============================================================================

def inverse_adjugate(matrix: Matrix) -> Matrix:
    """
    Compute an inverse using the classical adjugate formula:

        A^-1 = adj(A) / det(A)

    This method is useful for understanding the mathematical definition.
    It becomes computationally inefficient for large matrices.
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        raise ValueError("Only square matrices can have inverses.")

    determinant_value = determinant_recursive(matrix)

    if abs(determinant_value) < EPSILON:
        raise ValueError(
            "The matrix is singular or numerically singular and has no inverse."
        )

    adj = adjugate(matrix)

    return scalar_multiply(1 / determinant_value, adj)


def inverse(matrix: Matrix) -> Matrix:
    """
    Compute a matrix inverse using Gauss-Jordan elimination.

    Start with an augmented matrix:

        [A | I]

    Apply elementary row operations until:

        [I | A^-1]

    Partial pivoting is used to improve numerical stability.
    """
    validate_numeric_matrix(matrix)

    if not is_square(matrix):
        raise ValueError("Only square matrices can have inverses.")

    size = len(matrix)

    augmented = [
        [float(value) for value in matrix[row]]
        + [float(value) for value in identity(size)[row]]
        for row in range(size)
    ]

    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(augmented[row][pivot_column]),
        )

        if abs(augmented[pivot_row][pivot_column]) < EPSILON:
            raise ValueError(
                "The matrix is singular or numerically singular and has no inverse."
            )

        if pivot_row != pivot_column:
            augmented[pivot_column], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[pivot_column],
            )

        pivot = augmented[pivot_column][pivot_column]

        # Scale the pivot row so the pivot becomes 1.
        augmented[pivot_column] = [
            value / pivot
            for value in augmented[pivot_column]
        ]

        # Eliminate the pivot column from every other row.
        for row in range(size):
            if row == pivot_column:
                continue

            factor = augmented[row][pivot_column]

            if abs(factor) < EPSILON:
                continue

            augmented[row] = [
                augmented[row][column]
                - factor * augmented[pivot_column][column]
                for column in range(2 * size)
            ]

    return [
        row[size:]
        for row in augmented
    ]


# ============================================================================
# 8. ELEMENTARY ROW OPERATIONS
# ============================================================================

def swap_rows(matrix: Matrix, row_a: int, row_b: int) -> Matrix:
    """Return a new matrix with two rows exchanged."""
    validate_numeric_matrix(matrix)

    result = copy_matrix(matrix)
    result[row_a], result[row_b] = result[row_b], result[row_a]

    return result


def scale_row(matrix: Matrix, row: int, scalar: Number) -> Matrix:
    """Return a new matrix with one row multiplied by a scalar."""
    validate_numeric_matrix(matrix)

    result = copy_matrix(matrix)
    result[row] = [scalar * value for value in result[row]]

    return result


def add_scaled_row(
    matrix: Matrix,
    target_row: int,
    source_row: int,
    scalar: Number,
) -> Matrix:
    """
    Perform:

        target_row = target_row + scalar * source_row
    """
    validate_numeric_matrix(matrix)

    result = copy_matrix(matrix)

    result[target_row] = [
        result[target_row][column]
        + scalar * result[source_row][column]
        for column in range(len(result[target_row]))
    ]

    return result


# ============================================================================
# 9. ROW ECHELON FORM AND REDUCED ROW ECHELON FORM
# ============================================================================

def row_echelon_form(matrix: Matrix) -> Matrix:
    """
    Convert a matrix to Row Echelon Form (REF).

    Characteristics:
    - Zero rows appear at the bottom.
    - Each pivot is to the right of the pivot above it.
    - Entries below pivots are zero.

    Partial pivoting chooses the largest available pivot by absolute value.
    """
    validate_numeric_matrix(matrix)

    working = [
        [float(value) for value in row]
        for row in matrix
    ]

    rows, columns = matrix_shape(working)
    pivot_row = 0

    for pivot_column in range(columns):
        if pivot_row >= rows:
            break

        best_row = max(
            range(pivot_row, rows),
            key=lambda row: abs(working[row][pivot_column]),
        )

        if abs(working[best_row][pivot_column]) < EPSILON:
            continue

        if best_row != pivot_row:
            working[pivot_row], working[best_row] = (
                working[best_row],
                working[pivot_row],
            )

        pivot = working[pivot_row][pivot_column]

        for row in range(pivot_row + 1, rows):
            factor = working[row][pivot_column] / pivot

            for column in range(pivot_column, columns):
                working[row][column] -= (
                    factor * working[pivot_row][column]
                )

        pivot_row += 1

    return clean_matrix(working)


def reduced_row_echelon_form(matrix: Matrix) -> Matrix:
    """
    Convert a matrix to Reduced Row Echelon Form (RREF).

    Characteristics:
    - Every pivot equals 1.
    - Every pivot is the only non-zero entry in its column.
    - Pivot positions move to the right as rows progress.
    - Zero rows appear at the bottom.
    """
    validate_numeric_matrix(matrix)

    working = [
        [float(value) for value in row]
        for row in matrix
    ]

    rows, columns = matrix_shape(working)
    pivot_row = 0

    for pivot_column in range(columns):
        if pivot_row >= rows:
            break

        best_row = max(
            range(pivot_row, rows),
            key=lambda row: abs(working[row][pivot_column]),
        )

        if abs(working[best_row][pivot_column]) < EPSILON:
            continue

        working[pivot_row], working[best_row] = (
            working[best_row],
            working[pivot_row],
        )

        pivot = working[pivot_row][pivot_column]

        working[pivot_row] = [
            value / pivot
            for value in working[pivot_row]
        ]

        for row in range(rows):
            if row == pivot_row:
                continue

            factor = working[row][pivot_column]

            working[row] = [
                working[row][column]
                - factor * working[pivot_row][column]
                for column in range(columns)
            ]

        pivot_row += 1

    return clean_matrix(working)


def clean_matrix(matrix: Matrix, tolerance: float = EPSILON) -> Matrix:
    """
    Replace very small floating-point values with zero.

    Floating-point arithmetic often produces values such as:
        1.1102230246251565e-16

    when the mathematical answer should be exactly zero.
    """
    return [
        [
            0.0 if abs(value) < tolerance else value
            for value in row
        ]
        for row in matrix
    ]


# ============================================================================
# 10. MATRIX RANK
# ============================================================================

def matrix_rank(matrix: Matrix) -> int:
    """
    Compute matrix rank using row reduction.

    The rank equals the number of non-zero rows in row echelon form.
    """
    validate_numeric_matrix(matrix)

    ref = row_echelon_form(matrix)

    rank = 0

    for row in ref:
        if any(abs(value) >= EPSILON for value in row):
            rank += 1

    return rank


# ============================================================================
# 11. SOLVING LINEAR SYSTEMS
# ============================================================================

def solve_linear_system(coefficients: Matrix, constants: Sequence[Number]) -> List[float]:
    """
    Solve a square system:

        A * x = b

    using Gauss-Jordan elimination.

    Example:
        2x + y = 5
        x - y = 1

    becomes:
        A = [[2, 1],
             [1, -1]]

        b = [5, 1]

    A unique solution requires a non-singular square coefficient matrix.
    """
    validate_numeric_matrix(coefficients)

    if not is_square(coefficients):
        raise ValueError(
            "This solver requires a square coefficient matrix."
        )

    size = len(coefficients)

    if len(constants) != size:
        raise ValueError(
            "The constants vector must have one value for each equation."
        )

    augmented = [
        [float(value) for value in coefficients[row]]
        + [float(constants[row])]
        for row in range(size)
    ]

    rref = reduced_row_echelon_form(augmented)

    # A unique solution requires the left side to become the identity matrix.
    for row in range(size):
        for column in range(size):
            expected = 1.0 if row == column else 0.0

            if not isclose(
                rref[row][column],
                expected,
                abs_tol=EPSILON,
            ):
                raise ValueError(
                    "The system does not have a unique solution."
                )

    return [rref[row][-1] for row in range(size)]


def solve_using_inverse(
    coefficients: Matrix,
    constants: Sequence[Number],
) -> List[Number]:
    """
    Solve A*x = b using:

        x = A^-1 * b

    This is mathematically valid for invertible A, but explicitly computing
    an inverse is often less efficient and less numerically stable than
    solving the system directly in production numerical software.
    """
    inverse_matrix = inverse(coefficients)

    return multiply_matrix_vector(inverse_matrix, constants)


# ============================================================================
# 12. MATRIX EQUALITY WITH FLOATING-POINT TOLERANCE
# ============================================================================

def matrices_equal(
    matrix_a: Matrix,
    matrix_b: Matrix,
    tolerance: float = EPSILON,
) -> bool:
    """
    Compare matrices using approximate equality.

    Exact equality is often unsuitable after floating-point calculations.
    """
    validate_numeric_matrix(matrix_a)
    validate_numeric_matrix(matrix_b)

    if matrix_shape(matrix_a) != matrix_shape(matrix_b):
        return False

    rows, columns = matrix_shape(matrix_a)

    for row in range(rows):
        for column in range(columns):
            if not isclose(
                matrix_a[row][column],
                matrix_b[row][column],
                abs_tol=tolerance,
                rel_tol=tolerance,
            ):
                return False

    return True


# ============================================================================
# 13. ADVANCED MATRIX IDENTITIES
# ============================================================================

def demonstrate_matrix_identities() -> None:
    """
    Demonstrate important algebraic identities.

    For compatible matrices:

        (A + B)^T = A^T + B^T
        (AB)^T = B^T A^T
        (ABC)^T = C^T B^T A^T

    For invertible matrices:

        (AB)^-1 = B^-1 A^-1

    Notice the reversed order in both transpose and inverse identities.
    """
    print("=" * 78)
    print("ADVANCED MATRIX IDENTITIES")
    print("=" * 78)

    matrix_a = [
        [1, 2],
        [3, 4],
    ]

    matrix_b = [
        [5, 6],
        [7, 8],
    ]

    left_transpose_sum = transpose(add_matrices(matrix_a, matrix_b))
    right_transpose_sum = add_matrices(
        transpose(matrix_a),
        transpose(matrix_b),
    )

    print(
        "(A + B)^T = A^T + B^T:",
        matrices_equal(left_transpose_sum, right_transpose_sum),
    )

    left_product_transpose = transpose(
        multiply_matrices(matrix_a, matrix_b)
    )

    right_product_transpose = multiply_matrices(
        transpose(matrix_b),
        transpose(matrix_a),
    )

    print(
        "(AB)^T = B^T A^T:",
        matrices_equal(
            left_product_transpose,
            right_product_transpose,
        ),
    )

    invertible_a = [
        [2, 1],
        [1, 1],
    ]

    invertible_b = [
        [1, 2],
        [3, 5],
    ]

    inverse_product = inverse(
        multiply_matrices(invertible_a, invertible_b)
    )

    reversed_inverse_product = multiply_matrices(
        inverse(invertible_b),
        inverse(invertible_a),
    )

    print(
        "(AB)^-1 = B^-1 A^-1:",
        matrices_equal(
            inverse_product,
            reversed_inverse_product,
        ),
    )

    print()


# ============================================================================
# 14. COMMON EDGE CASES AND EXCEPTIONS
# ============================================================================

def demonstrate_edge_cases() -> None:
    """Demonstrate important invalid operations and their exceptions."""
    print("=" * 78)
    print("EDGE CASES AND COMMON ERRORS")
    print("=" * 78)

    try:
        add_matrices(
            [[1, 2]],
            [[1], [2]],
        )
    except ValueError as error:
        print("Addition shape mismatch:", error)

    try:
        multiply_matrices(
            [[1, 2, 3]],
            [[1, 2], [3, 4]],
        )
    except ValueError as error:
        print("Multiplication shape mismatch:", error)

    try:
        determinant_recursive(
            [[1, 2, 3], [4, 5, 6]]
        )
    except ValueError as error:
        print("Determinant of non-square matrix:", error)

    try:
        inverse(
            [[1, 2], [2, 4]]
        )
    except ValueError as error:
        print("Inverse of singular matrix:", error)

    try:
        matrix_shape(
            [[1, 2], [3]]
        )
    except ValueError as error:
        print("Non-rectangular matrix:", error)

    print()


# ============================================================================
# 15. PERFORMANCE COMPARISON
# ============================================================================

def operation_complexity_notes() -> None:
    """
    Print approximate computational complexity for common dense matrix
    operations.

    These estimates depend on implementation and matrix structure.
    """
    print("=" * 78)
    print("PERFORMANCE CONSIDERATIONS")
    print("=" * 78)

    notes = [
        "Addition/Subtraction: O(m*n)",
        "Transpose: O(m*n)",
        "Naive matrix multiplication: O(m*n*p)",
        "Square matrix multiplication: approximately O(n^3)",
        "Gaussian elimination: approximately O(n^3)",
        "Gauss-Jordan inversion: approximately O(n^3)",
        "Recursive cofactor determinant: approximately factorial growth",
        "Exponentiation by squaring for A^k: O(log k) matrix multiplications",
    ]

    for note in notes:
        print("-", note)

    print()


# ============================================================================
# 16. PRACTICAL APPLICATION: 2D GEOMETRIC TRANSFORMATIONS
# ============================================================================

def demonstrate_geometric_transformations() -> None:
    """
    Demonstrate matrix multiplication in 2D geometry.

    A point [x, y] can be transformed using matrices.

    Scaling:
        [sx  0]
        [ 0 sy]

    Rotation by angle theta:
        [ cos(theta)  -sin(theta)]
        [ sin(theta)   cos(theta)]

    This script uses a simple 90-degree rotation matrix to avoid importing
    trigonometric functions.
    """
    print("=" * 78)
    print("PRACTICAL APPLICATION: 2D GEOMETRIC TRANSFORMATIONS")
    print("=" * 78)

    point = [2, 3]

    scaling_matrix = [
        [2, 0],
        [0, 0.5],
    ]

    rotation_90_counterclockwise = [
        [0, -1],
        [1, 0],
    ]

    scaled_point = multiply_matrix_vector(
        scaling_matrix,
        point,
    )

    rotated_point = multiply_matrix_vector(
        rotation_90_counterclockwise,
        point,
    )

    print("Original point:", point)
    print("Scaled point:", scaled_point)
    print("90-degree counterclockwise rotation:", rotated_point)
    print()


# ============================================================================
# 17. PRACTICAL APPLICATION: MARKOV TRANSITION MATRICES
# ============================================================================

def demonstrate_markov_chain() -> None:
    """
    Demonstrate repeated matrix multiplication using a Markov transition matrix.

    Each row represents the probability of moving from one state to another.

    State order:
        0 = Sunny
        1 = Rainy

    The matrix is row-stochastic because every row sums to 1.

    State after one step:
        next_state = transition^T * current_column_state

    This implementation uses a column-vector state representation.
    """
    print("=" * 78)
    print("PRACTICAL APPLICATION: MARKOV TRANSITION MATRIX")
    print("=" * 78)

    transition = [
        [0.8, 0.2],
        [0.4, 0.6],
    ]

    # Convert the row-stochastic transition matrix for column-vector use.
    transition_for_column_vector = transpose(transition)

    current_state = [1.0, 0.0]

    print("Initial probabilities [Sunny, Rainy]:", current_state)

    for day in range(1, 6):
        current_state = multiply_matrix_vector(
            transition_for_column_vector,
            current_state,
        )

        print(
            f"After {day} transition(s): "
            f"Sunny={current_state[0]:.6f}, "
            f"Rainy={current_state[1]:.6f}"
        )

    print()


# ============================================================================
# 18. PRACTICAL APPLICATION: LINEAR TRANSFORMATION COMPOSITION
# ============================================================================

def demonstrate_transformation_order() -> None:
    """
    Demonstrate why matrix multiplication order matters.

    For column vectors:

        If a point first undergoes B and then A:

            result = A * B * point

    The rightmost matrix acts first.
    """
    print("=" * 78)
    print("ORDER OF MATRIX TRANSFORMATIONS")
    print("=" * 78)

    point = [1, 2]

    scale = [
        [2, 0],
        [0, 3],
    ]

    rotate_90 = [
        [0, -1],
        [1, 0],
    ]

    scale_then_rotate = multiply_matrix_vector(
        rotate_90,
        multiply_matrix_vector(scale, point),
    )

    rotate_then_scale = multiply_matrix_vector(
        scale,
        multiply_matrix_vector(rotate_90, point),
    )

    print("Original point:", point)
    print("Scale, then rotate:", scale_then_rotate)
    print("Rotate, then scale:", rotate_then_scale)

    print(
        "The results differ because matrix multiplication is generally "
        "not commutative."
    )
    print()


# ============================================================================
# 19. COMPREHENSIVE DEMONSTRATION
# ============================================================================

def demonstrate_fundamentals() -> None:
    """Demonstrate core matrix creation and basic operations."""
    print("=" * 78)
    print("MATRIX FUNDAMENTALS")
    print("=" * 78)

    matrix_a = [
        [1, 2, 3],
        [4, 5, 6],
    ]

    matrix_b = [
        [10, 20, 30],
        [40, 50, 60],
    ]

    print_matrix(matrix_a, "Matrix A:")
    print("Shape of A:", matrix_shape(matrix_a))
    print()

    print_matrix(matrix_b, "Matrix B:")
    print("Shape of B:", matrix_shape(matrix_b))
    print()

    print_matrix(
        add_matrices(matrix_a, matrix_b),
        "A + B:",
    )

    print_matrix(
        subtract_matrices(matrix_b, matrix_a),
        "B - A:",
    )

    print_matrix(
        scalar_multiply(2, matrix_a),
        "2A:",
    )

    print_matrix(
        transpose(matrix_a),
        "Transpose of A:",
    )


def demonstrate_multiplication() -> None:
    """Demonstrate matrix multiplication and non-commutativity."""
    print("=" * 78)
    print("MATRIX MULTIPLICATION")
    print("=" * 78)

    matrix_a = [
        [1, 2, 3],
        [4, 5, 6],
    ]

    matrix_b = [
        [7, 8],
        [9, 10],
        [11, 12],
    ]

    product = multiply_matrices(matrix_a, matrix_b)

    print_matrix(matrix_a, "Matrix A (2x3):")
    print_matrix(matrix_b, "Matrix B (3x2):")
    print_matrix(product, "A * B (2x2):")

    matrix_c = [
        [1, 2],
        [3, 4],
    ]

    matrix_d = [
        [0, 1],
        [1, 0],
    ]

    print_matrix(
        multiply_matrices(matrix_c, matrix_d),
        "C * D:",
    )

    print_matrix(
        multiply_matrices(matrix_d, matrix_c),
        "D * C:",
    )

    print(
        "C * D equals D * C:",
        matrices_equal(
            multiply_matrices(matrix_c, matrix_d),
            multiply_matrices(matrix_d, matrix_c),
        ),
    )
    print()


def demonstrate_determinants() -> None:
    """Demonstrate determinants using two algorithms."""
    print("=" * 78)
    print("DETERMINANTS")
    print("=" * 78)

    matrix_2x2 = [
        [4, 7],
        [2, 6],
    ]

    matrix_3x3 = [
        [1, 2, 3],
        [0, 1, 4],
        [5, 6, 0],
    ]

    print_matrix(matrix_2x2, "2x2 Matrix:")
    print(
        "Recursive determinant:",
        determinant_recursive(matrix_2x2),
    )
    print(
        "Elimination determinant:",
        determinant_elimination(matrix_2x2),
    )
    print()

    print_matrix(matrix_3x3, "3x3 Matrix:")
    print(
        "Recursive determinant:",
        determinant_recursive(matrix_3x3),
    )
    print(
        "Elimination determinant:",
        determinant_elimination(matrix_3x3),
    )
    print()


def demonstrate_inverse() -> None:
    """Demonstrate matrix inversion and verification."""
    print("=" * 78)
    print("MATRIX INVERSE")
    print("=" * 78)

    matrix_a = [
        [4, 7],
        [2, 6],
    ]

    print_matrix(matrix_a, "Matrix A:")

    inverse_by_adjugate = inverse_adjugate(matrix_a)
    inverse_by_elimination = inverse(matrix_a)

    print_matrix(
        inverse_by_adjugate,
        "Inverse using adjugate formula:",
    )

    print_matrix(
        inverse_by_elimination,
        "Inverse using Gauss-Jordan elimination:",
    )

    verification = multiply_matrices(
        matrix_a,
        inverse_by_elimination,
    )

    print_matrix(
        verification,
        "A * A^-1 (should approximate identity):",
    )


def demonstrate_row_reduction_and_rank() -> None:
    """Demonstrate REF, RREF, and rank."""
    print("=" * 78)
    print("ROW REDUCTION AND MATRIX RANK")
    print("=" * 78)

    matrix = [
        [1, 2, 3],
        [2, 4, 6],
        [1, 1, 1],
    ]

    print_matrix(matrix, "Original matrix:")

    print_matrix(
        row_echelon_form(matrix),
        "Row Echelon Form (REF):",
    )

    print_matrix(
        reduced_row_echelon_form(matrix),
        "Reduced Row Echelon Form (RREF):",
    )

    print("Rank:", matrix_rank(matrix))
    print()


def demonstrate_linear_systems() -> None:
    """Demonstrate solving a system of linear equations."""
    print("=" * 78)
    print("SOLVING A SYSTEM OF LINEAR EQUATIONS")
    print("=" * 78)

    # System:
    #
    # 2x +  y - z = 8
    #-3x -  y + 2z = -11
    #-2x +  y + 2z = -3
    #
    # Expected solution:
    # x = 2, y = 3, z = -1

    coefficients = [
        [2, 1, -1],
        [-3, -1, 2],
        [-2, 1, 2],
    ]

    constants = [8, -11, -3]

    print_matrix(coefficients, "Coefficient matrix A:")
    print("Constants vector b:", constants)

    solution = solve_linear_system(
        coefficients,
        constants,
    )

    print("Solution using Gauss-Jordan:", solution)

    solution_inverse = solve_using_inverse(
        coefficients,
        constants,
    )

    print("Solution using A^-1 * b:", solution_inverse)

    verification = multiply_matrix_vector(
        coefficients,
        solution,
    )

    print("Verification A*x:", verification)
    print()


def demonstrate_special_matrices() -> None:
    """Demonstrate common special matrix types."""
    print("=" * 78)
    print("SPECIAL MATRIX TYPES")
    print("=" * 78)

    diagonal = diagonal_matrix([2, 5, 7])

    upper = [
        [1, 2, 3],
        [0, 4, 5],
        [0, 0, 6],
    ]

    lower = [
        [1, 0, 0],
        [2, 3, 0],
        [4, 5, 6],
    ]

    symmetric = [
        [2, 3, 4],
        [3, 5, 6],
        [4, 6, 7],
    ]

    print_matrix(diagonal, "Diagonal matrix:")
    print("Is diagonal:", is_diagonal(diagonal))
    print("Is square:", is_square(diagonal))
    print()

    print_matrix(upper, "Upper triangular matrix:")
    print("Is upper triangular:", is_upper_triangular(upper))
    print()

    print_matrix(lower, "Lower triangular matrix:")
    print("Is lower triangular:", is_lower_triangular(lower))
    print()

    print_matrix(symmetric, "Symmetric matrix:")
    print("Is symmetric:", is_symmetric(symmetric))
    print()


def demonstrate_matrix_powers() -> None:
    """Demonstrate positive, zero, and negative matrix powers."""
    print("=" * 78)
    print("MATRIX POWERS")
    print("=" * 78)

    matrix_a = [
        [1, 1],
        [1, 0],
    ]

    print_matrix(matrix_a, "Matrix A:")
    print_matrix(matrix_power(matrix_a, 2), "A^2:")
    print_matrix(matrix_power(matrix_a, 5), "A^5:")
    print_matrix(matrix_power(matrix_a, 0), "A^0 = Identity:")
    print_matrix(matrix_power(matrix_a, -1), "A^-1:")
    print()


# ============================================================================
# 20. TESTING
# ============================================================================

def run_self_tests() -> None:
    """
    Execute deterministic assertions.

    Assertions help detect implementation errors during maintenance.
    """
    # Shape and construction.
    assert matrix_shape([[1, 2], [3, 4]]) == (2, 2)
    assert zeros(2, 2) == [[0, 0], [0, 0]]
    assert identity(2) == [[1, 0], [0, 1]]

    # Basic arithmetic.
    assert add_matrices(
        [[1, 2]],
        [[3, 4]],
    ) == [[4, 6]]

    assert subtract_matrices(
        [[5, 7]],
        [[2, 3]],
    ) == [[3, 4]]

    assert scalar_multiply(
        3,
        [[1, 2]],
    ) == [[3, 6]]

    # Transpose.
    assert transpose(
        [[1, 2, 3], [4, 5, 6]]
    ) == [
        [1, 4],
        [2, 5],
        [3, 6],
    ]

    # Multiplication.
    assert multiply_matrices(
        [[1, 2], [3, 4]],
        [[5, 6], [7, 8]],
    ) == [
        [19, 22],
        [43, 50],
    ]

    # Determinant.
    assert determinant_recursive(
        [[4, 7], [2, 6]]
    ) == 10

    # Inverse verification.
    matrix = [
        [4, 7],
        [2, 6],
    ]

    matrix_inverse = inverse(matrix)

    assert matrices_equal(
        multiply_matrices(matrix, matrix_inverse),
        identity(2),
        tolerance=1e-9,
    )

    # Rank.
    assert matrix_rank(
        [[1, 2], [2, 4]]
    ) == 1

    # Linear system.
    solution = solve_linear_system(
        [[2, 1], [1, -1]],
        [5, 1],
    )

    assert matrices_equal(
        [[solution[0]], [solution[1]]],
        [[2.0], [1.0]],
    )

    print("All self-tests passed.")
    print()


# ============================================================================
# 21. MAIN EXECUTION
# ============================================================================

def main() -> None:
    """
    Run all demonstrations in a logical progression.

    The functions are also independently reusable. The demonstrations simply
    show representative inputs and expected mathematical behavior.
    """
    print("\n" + "#" * 78)
    print("MATRICES AND MATRIX OPERATIONS")
    print("#" * 78 + "\n")

    demonstrate_fundamentals()
    demonstrate_multiplication()
    demonstrate_determinants()
    demonstrate_inverse()
    demonstrate_row_reduction_and_rank()
    demonstrate_linear_systems()
    demonstrate_special_matrices()
    demonstrate_matrix_powers()
    demonstrate_matrix_identities()
    demonstrate_edge_cases()
    operation_complexity_notes()
    demonstrate_geometric_transformations()
    demonstrate_markov_chain()
    demonstrate_transformation_order()
    run_self_tests()

    print("#" * 78)
    print("END OF MATRIX OPERATIONS STUDY SCRIPT")
    print("#" * 78)


if __name__ == "__main__":
    main()
