# Matrices & Matrix Operations

## Introduction

A matrix is a rectangular arrangement of numbers organized into rows and columns. Matrices provide a compact way to represent systems of linear equations, geometric transformations, datasets, networks, probabilities, and many other mathematical and computational structures.

This study script develops matrix operations from fundamental concepts through more advanced algorithms. It implements the operations directly in Python using only the standard library. This makes the underlying mathematics and algorithms visible instead of hiding them behind specialized numerical libraries.

The main topics are:

- Matrix representation and validation
- Matrix dimensions and shape
- Matrix addition and subtraction
- Scalar multiplication
- Matrix transpose
- Matrix multiplication
- Identity and zero matrices
- Special matrix classifications
- Determinants
- Minors and cofactors
- Adjugate matrices
- Matrix inverses
- Gaussian elimination
- Gauss-Jordan elimination
- Row echelon forms
- Reduced row echelon form
- Matrix rank
- Solving systems of linear equations
- Matrix powers
- Important matrix identities
- Numerical precision
- Computational complexity
- Practical applications

---

# 1. Matrix Fundamentals

A matrix is usually written using an uppercase letter such as:

    A = [a11 a12 a13
         a21 a22 a23]

The entry in row `i` and column `j` is commonly written as:

    a(i,j)

In Python, a matrix can be represented as a list of lists:

    [
        [1, 2, 3],
        [4, 5, 6],
    ]

This matrix has:

- 2 rows
- 3 columns
- Shape `2 x 3`

The script represents matrices using nested Python lists and validates that every row has the same number of elements.

A structure such as:

    [
        [1, 2],
        [3],
    ]

is not a valid rectangular matrix because its rows have different lengths.

---

# 2. Matrix Dimensions and Shape

The dimensions of a matrix describe its number of rows and columns.

A matrix with `m` rows and `n` columns has shape:

    m x n

Examples:

| Matrix Shape | Description |
|---|---|
| 1 x n | Row matrix or row vector |
| m x 1 | Column matrix or column vector |
| n x n | Square matrix |
| m x n | Rectangular matrix |

Matrix dimensions determine which operations are valid.

For example:

- Addition requires equal shapes.
- Subtraction requires equal shapes.
- Matrix multiplication requires compatible inner dimensions.
- Determinants require square matrices.
- Ordinary matrix inverses require square non-singular matrices.

The `matrix_shape()` function validates a matrix and returns:

    (rows, columns)

---

# 3. Creating Matrices

The script implements several useful matrix constructors.

## Zero Matrix

A zero matrix contains only zero values.

Example:

    [0 0 0
     0 0 0]

A zero matrix is useful as an additive identity:

    A + 0 = A

The script provides:

    zeros(rows, columns)

## Identity Matrix

An identity matrix is square and contains ones on the main diagonal and zeros elsewhere.

For example:

    I3 = [1 0 0
          0 1 0
          0 0 1]

The identity matrix behaves like the multiplicative identity:

    A * I = A

and, for compatible square matrices:

    I * A = A

The script provides:

    identity(size)

## Diagonal Matrix

A diagonal matrix has zero values outside the main diagonal.

Example:

    [2 0 0
     0 5 0
     0 0 7]

The script constructs such matrices from a sequence of diagonal values.

---

# 4. Matrix Addition

Two matrices can be added only when they have identical dimensions.

For matrices:

    A = [a b
         c d]

and:

    B = [e f
         g h]

their sum is:

    A + B = [a+e b+f
             c+g d+h]

The operation is element-wise.

Formally:

    (A + B)[i][j] = A[i][j] + B[i][j]

Matrix addition has important properties:

- Commutativity: `A + B = B + A`
- Associativity: `(A + B) + C = A + (B + C)`
- Zero identity: `A + 0 = A`

The script validates dimensions before performing addition.

---

# 5. Matrix Subtraction

Matrix subtraction also requires equal dimensions.

For each entry:

    (A - B)[i][j] = A[i][j] - B[i][j]

Subtraction is generally not commutative:

    A - B != B - A

The script raises an exception if the matrix shapes are different.

---

# 6. Scalar Multiplication

A scalar is a single number.

Multiplying a matrix by scalar `c` means multiplying every entry by `c`.

For example:

    2 * [1 2
         3 4]

produces:

    [2 4
     6 8]

Formally:

    (cA)[i][j] = c * A[i][j]

Scalar multiplication distributes over matrix addition:

    c(A + B) = cA + cB

---

# 7. Matrix Transpose

The transpose of a matrix exchanges rows and columns.

If:

    A = [1 2 3
         4 5 6]

then:

    A^T = [1 4
           2 5
           3 6]

If `A` has shape:

    m x n

then:

    A^T

has shape:

    n x m

The script implements transpose by iterating through columns and constructing new rows.

Important transpose identities include:

    (A^T)^T = A

    (A + B)^T = A^T + B^T

    (AB)^T = B^T A^T

The order reversal in the last identity is important.

---

# 8. Matrix Multiplication

Matrix multiplication is one of the most important matrix operations.

Suppose:

    A has shape m x n

and:

    B has shape n x p

Then the product:

    C = AB

has shape:

    m x p

The inner dimensions must match:

    number of columns of A = number of rows of B

Each element is computed using a dot product:

    C[i][j] = sum(A[i][k] * B[k][j])

For example:

    A = [1 2
         3 4]

    B = [5 6
         7 8]

Then:

    AB = [1*5 + 2*7    1*6 + 2*8
          3*5 + 4*7    3*6 + 4*8]

which gives:

    [19 22
     43 50]

## Non-Commutativity

Matrix multiplication is generally not commutative.

In general:

    AB != BA

Both products may even have different dimensions.

This is especially important in applications involving transformations. Applying transformation `A` and then `B` is generally different from applying `B` and then `A`.

## Associativity

Matrix multiplication is associative:

    (AB)C = A(BC)

## Distributivity

Matrix multiplication distributes over addition:

    A(B + C) = AB + AC

and:

    (A + B)C = AC + BC

---

# 9. Matrix-Vector Multiplication

A vector can be represented as a one-dimensional Python sequence.

For a matrix `A` with shape:

    m x n

a compatible vector must contain `n` elements.

The result contains `m` elements.

This operation is fundamental in:

- Linear transformations
- Machine learning
- Computer graphics
- Systems of linear equations
- Probability models
- Scientific computing

The script implements:

    multiply_matrix_vector(matrix, vector)

---

# 10. Special Matrix Types

## Square Matrix

A square matrix has equal numbers of rows and columns.

Examples:

    2 x 2
    3 x 3
    n x n

Determinants and ordinary matrix inverses are defined for square matrices.

## Zero Matrix

Every entry is zero.

## Identity Matrix

The diagonal entries are one and all other entries are zero.

## Diagonal Matrix

All off-diagonal entries are zero.

## Upper Triangular Matrix

All entries below the main diagonal are zero.

Example:

    [1 2 3
     0 4 5
     0 0 6]

## Lower Triangular Matrix

All entries above the main diagonal are zero.

Example:

    [1 0 0
     2 3 0
     4 5 6]

## Symmetric Matrix

A square matrix is symmetric when:

    A = A^T

Example:

    [2 3
     3 5]

Symmetric matrices occur frequently in optimization, statistics, physics, and numerical computation.

---

# 11. Determinants

A determinant is a scalar value associated with a square matrix.

For a `2 x 2` matrix:

    A = [a b
         c d]

the determinant is:

    det(A) = ad - bc

The determinant provides important information about a matrix.

For a square matrix:

- `det(A) != 0` indicates that the matrix is invertible.
- `det(A) = 0` indicates that the matrix is singular.
- A singular matrix does not have an ordinary inverse.

## Determinant of a 3 x 3 Matrix

The script demonstrates recursive cofactor expansion.

For larger matrices, recursive expansion becomes expensive.

---

# 12. Minor Matrices

The minor associated with an entry is formed by removing that entry's row and column.

For example, for:

    [a b c
     d e f
     g h i]

the minor associated with the entry `a` is:

    [e f
     h i]

The script provides:

    minor_matrix(matrix, remove_row, remove_column)

Minors are used to compute cofactors, determinants, and adjugate matrices.

---

# 13. Cofactors

The cofactor of an entry is:

    C(i,j) = (-1)^(i+j) * det(M(i,j))

where:

    M(i,j)

is the minor matrix.

The sign pattern begins as:

    + - +
    - + -
    + - +

The script implements:

- Individual cofactor calculation
- Construction of the complete cofactor matrix

---

# 14. Adjugate Matrix

The adjugate of a matrix is the transpose of its cofactor matrix.

Formally:

    adj(A) = Cofactor(A)^T

For an invertible matrix:

    A^-1 = adj(A) / det(A)

This formula is mathematically important and is implemented in the script for educational purposes.

For large matrices, computing inverses through repeated cofactor determinants is computationally expensive.

---

# 15. Matrix Inverse

For an invertible matrix `A`, the inverse is written:

    A^-1

The inverse satisfies:

    A * A^-1 = I

and:

    A^-1 * A = I

where `I` is the identity matrix.

A matrix is invertible only when:

    det(A) != 0

## Inverse Using the Adjugate Formula

The script implements:

    A^-1 = adj(A) / det(A)

This method directly reflects the mathematical definition.

## Inverse Using Gauss-Jordan Elimination

The more algorithmic implementation starts with:

    [A | I]

Elementary row operations are applied until the left side becomes the identity:

    [I | A^-1]

The script uses partial pivoting to improve numerical stability.

---

# 16. Singular Matrices

A singular matrix does not have an inverse.

Example:

    [1 2
     2 4]

The second row is a multiple of the first.

Its determinant is:

    1*4 - 2*2 = 0

This matrix represents linearly dependent information.

The script detects singular or numerically singular matrices and raises a `ValueError`.

---

# 17. Elementary Row Operations

Three elementary row operations are used in elimination algorithms.

## Row Swapping

Exchange two rows:

    R1 <-> R2

## Row Scaling

Multiply a row by a non-zero scalar:

    R1 -> cR1

## Row Replacement

Add a multiple of one row to another:

    R1 -> R1 + cR2

These operations are central to:

- Gaussian elimination
- Gauss-Jordan elimination
- Matrix inversion
- Rank calculation
- Solving systems of equations

---

# 18. Gaussian Elimination

Gaussian elimination transforms a matrix into Row Echelon Form.

The method progressively eliminates values below pivot positions.

A pivot is a leading non-zero entry used to eliminate entries beneath it.

The script uses partial pivoting, selecting the largest available absolute value in a pivot column.

Partial pivoting is important because division by a very small pivot can significantly amplify floating-point errors.

---

# 19. Row Echelon Form

A matrix is in Row Echelon Form when:

1. Non-zero rows appear above zero rows.
2. Each pivot lies to the right of the pivot in the row above.
3. Entries below each pivot are zero.

Example:

    [1 2 3
     0 4 5
     0 0 0]

Row Echelon Form is useful for determining rank and solving systems.

---

# 20. Reduced Row Echelon Form

Reduced Row Echelon Form, also called RREF, has stricter requirements.

Each pivot:

- Equals one.
- Is the only non-zero value in its column.

Example:

    [1 0 2
     0 1 3
     0 0 0]

RREF is useful because the resulting structure often exposes solutions directly.

The script implements complete Gauss-Jordan elimination.

---

# 21. Matrix Rank

The rank of a matrix is the number of linearly independent rows or columns.

Row rank and column rank are equal.

The script calculates rank by:

1. Converting the matrix to Row Echelon Form.
2. Counting non-zero rows.

Examples:

A matrix with dependent rows has reduced rank.

For:

    [1 2
     2 4]

the second row is twice the first, so the rank is:

    1

Rank is important for:

- Determining linear independence
- Analyzing systems of equations
- Detecting redundancy
- Understanding singularity

For a square matrix of size `n`:

    rank(A) = n

is necessary and sufficient for invertibility.

---

# 22. Solving Systems of Linear Equations

A system can be represented as:

    Ax = b

where:

- `A` is the coefficient matrix.
- `x` is the vector of unknowns.
- `b` is the constants vector.

For example:

    2x + y = 5
    x - y = 1

can be written as:

    [2  1] [x] = [5]
    [1 -1] [y]   [1]

The script solves systems using Gauss-Jordan elimination.

For a unique solution, the coefficient matrix must be invertible.

The solution can also be expressed mathematically as:

    x = A^-1 b

The script demonstrates both approaches.

## Practical Consideration

Although the inverse formula is mathematically correct, explicitly computing an inverse is often not the preferred production method for solving numerical systems.

Direct elimination methods generally require fewer operations and can provide better numerical behavior.

---

# 23. Matrix Powers

For a square matrix:

    A^2 = A * A

and:

    A^n = A multiplied by itself n times

The identity property is:

    A^0 = I

for square matrices.

The script supports negative powers for invertible matrices:

    A^(-n) = (A^-1)^n

## Exponentiation by Squaring

Repeated multiplication is inefficient for large exponents.

The script uses exponentiation by squaring.

Instead of performing `n` multiplications, the exponent is repeatedly divided by two.

This reduces the number of matrix multiplications to approximately logarithmic growth with respect to the exponent.

---

# 24. Important Matrix Identities

The script verifies several important identities.

## Transpose of a Sum

    (A + B)^T = A^T + B^T

## Transpose of a Product

    (AB)^T = B^T A^T

The order reverses.

## Inverse of a Product

For invertible matrices:

    (AB)^-1 = B^-1 A^-1

The order reverses here as well.

These order reversals are common sources of mistakes.

---

# 25. Numerical Precision and Floating-Point Arithmetic

Python floating-point values use finite precision.

Operations that should theoretically produce zero may produce values such as:

    1.1102230246251565e-16

The script defines a small tolerance:

    EPSILON = 1e-10

Values whose absolute magnitude is below this tolerance can be treated as numerically zero.

Approximate equality is particularly important when verifying:

    A * A^-1 = I

The computed result may contain values extremely close to zero or one rather than mathematically exact integers.

The `matrices_equal()` function compares matrix values using tolerances.

---

# 26. Partial Pivoting

During Gaussian and Gauss-Jordan elimination, a pivot can be zero or extremely small.

Dividing by such a value can cause instability.

Partial pivoting addresses this by searching the current column and selecting the row with the largest absolute pivot value.

The row is then moved into the pivot position.

Partial pivoting improves numerical stability and also handles many cases where a straightforward elimination algorithm would encounter division by zero.

---

# 27. Computational Complexity

The cost of matrix operations depends on matrix dimensions.

## Addition and Subtraction

For an `m x n` matrix:

    O(mn)

Every entry is processed once.

## Transpose

Also:

    O(mn)

## Naive Matrix Multiplication

For:

    A of size m x n
    B of size n x p

the approximate complexity is:

    O(mnp)

For two `n x n` matrices:

    O(n^3)

## Gaussian Elimination

For dense square matrices:

    O(n^3)

## Matrix Inversion

Gauss-Jordan inversion also has approximately cubic complexity for dense square matrices.

## Recursive Determinant Expansion

Recursive cofactor expansion grows extremely quickly as matrix size increases.

It is useful for teaching and small matrices but is generally unsuitable for large numerical computations.

The elimination-based determinant implementation is substantially more practical.

---

# 28. Matrix Multiplication Performance Considerations

The implementation in the script uses explicit nested loops.

This is educational because it directly demonstrates the dot-product definition.

For very large matrices, performance depends heavily on:

- Memory layout
- Cache behavior
- Loop ordering
- Optimized low-level arithmetic
- Parallel execution
- Hardware acceleration

The script prioritizes clarity and correctness rather than specialized high-performance numerical optimization.

The multiplication algorithm should not be assumed to be optimal for large production workloads.

---

# 29. Practical Application: Geometric Transformations

Matrices are used to transform geometric points.

A two-dimensional point can be represented as:

    [x
     y]

## Scaling

A scaling matrix is:

    [sx  0
      0 sy]

It changes the size of coordinates independently along each axis.

## Rotation

A 90-degree counterclockwise rotation can be represented by:

    [0 -1
     1  0]

Multiplying this matrix by a point rotates the point.

The script demonstrates scaling and rotation using matrix-vector multiplication.

---

# 30. Transformation Order

Transformation order matters.

For column vectors:

    A * B * point

means that `B` acts first and `A` acts second.

In general:

    AB != BA

Therefore:

    rotate(scale(point))

may produce a different result from:

    scale(rotate(point))

This principle is important in:

- Computer graphics
- Robotics
- Animation
- Coordinate systems
- Physics simulations

---

# 31. Practical Application: Markov Transition Matrices

A Markov model represents transitions between states.

For example, states might represent weather conditions:

- Sunny
- Rainy

A transition matrix contains probabilities of moving between states.

Repeated multiplication updates the state probabilities.

The script demonstrates a two-state model over several transitions.

A valid probability transition representation must be constructed consistently.

For a row-stochastic matrix:

- Every row represents outgoing probabilities.
- Every row sums to one.

The script transposes the row-stochastic matrix when applying it to a column-vector state representation.

This distinction between row-vector and column-vector conventions is important. Mixing conventions can produce incorrect results even when the individual matrix values appear reasonable.

---

# 32. Common Mistakes

## Adding Matrices with Different Shapes

Invalid:

    2 x 3 + 3 x 2

Matrix addition requires identical dimensions.

## Multiplying Incompatible Matrices

If:

    A is 2 x 3
    B is 2 x 2

then:

    AB

is undefined because the inner dimensions do not match.

## Assuming Matrix Multiplication Is Commutative

In general:

    AB != BA

## Assuming Every Square Matrix Has an Inverse

A square matrix must also be non-singular.

The determinant must be non-zero.

## Using Exact Equality for Floating-Point Results

Numerical algorithms may produce very small rounding errors.

Tolerance-based comparisons are more appropriate.

## Ignoring Pivoting

Elimination without pivoting can fail or become numerically unstable when pivots are zero or very small.

## Computing Large Determinants with Recursive Cofactor Expansion

Recursive expansion becomes computationally expensive rapidly.

Elimination methods are more suitable for larger matrices.

## Explicitly Computing an Inverse Only to Solve a Linear System

Although:

    x = A^-1 b

is mathematically correct, direct elimination is often computationally preferable.

---

# 33. Edge Cases and Exceptions

The script explicitly demonstrates several invalid situations.

## Non-Rectangular Matrices

All rows must have equal length.

## Invalid Addition

Matrices with different dimensions cannot be added.

## Invalid Multiplication

The inner dimensions must match.

## Determinant of a Non-Square Matrix

Ordinary determinants are defined only for square matrices.

## Inverse of a Singular Matrix

A singular matrix does not have an ordinary inverse.

The script raises descriptive exceptions for invalid operations rather than silently returning incorrect results.

---

# 34. Testing Matrix Operations

The script contains deterministic self-tests using Python assertions.

The tests verify:

- Matrix shape
- Zero matrices
- Identity matrices
- Addition
- Subtraction
- Scalar multiplication
- Transpose
- Matrix multiplication
- Determinants
- Matrix inverse verification
- Matrix rank
- Linear system solutions

Testing is particularly important because matrix algorithms often involve nested loops and index calculations.

Common implementation errors include:

- Using incorrect loop bounds
- Confusing row and column indices
- Multiplying in the wrong order
- Failing to copy matrices before modification
- Applying elimination factors to incorrect rows
- Ignoring numerical tolerances

The script keeps functions separate so that individual operations can be tested independently.

---

# 35. Implementation Design

The script uses plain Python nested lists to make the matrix structure explicit.

Important design choices include:

## Input Validation

Matrix functions validate:

- The matrix is non-empty.
- Rows are lists.
- All rows have equal length.
- Entries are numeric where required.

## Non-Mutating Operations

Most operations return new matrices instead of modifying the original input.

This reduces unexpected side effects.

## Numerical Cleanup

Small floating-point values can be converted to zero for readable output.

## Approximate Comparison

Matrix equality uses tolerance rather than requiring exact floating-point equality.

## Separate Educational and Practical Algorithms

Determinants are implemented using both:

- Recursive cofactor expansion for mathematical understanding.
- Elimination for improved scalability.

Matrix inverses are implemented using both:

- The adjugate formula.
- Gauss-Jordan elimination.

This allows direct comparison between mathematical definitions and algorithmic implementations.

---

# 36. Security and Reliability Considerations

Matrix operations themselves do not typically introduce traditional security risks such as authentication or access-control vulnerabilities. Reliability considerations remain important when matrix data originates from external sources.

Input validation helps prevent:

- Unexpected non-numeric values
- Invalid shapes
- Ragged nested lists
- Dimension mismatches
- Invalid indexing assumptions

For untrusted or extremely large inputs, computational cost can become a practical availability concern.

For example, recursive determinant expansion can consume substantial computational resources for moderately large matrices.

Production systems should therefore:

- Validate dimensions before expensive operations.
- Place reasonable limits on input sizes where appropriate.
- Prefer scalable algorithms.
- Use numerically stable methods.
- Handle singular and near-singular matrices explicitly.

---

# 37. Real-World Relevance

Matrices are fundamental to many fields.

## Computer Graphics

Matrices represent:

- Rotation
- Scaling
- Translation through homogeneous coordinates
- Camera transformations
- Projection

## Data Analysis

Matrices represent tabular numerical data and relationships between variables.

## Machine Learning

Matrices are used for:

- Feature representations
- Linear transformations
- Model parameters
- Neural network computations
- Covariance structures

## Engineering

Matrices represent systems of equations, transformations, and physical models.

## Economics

Input-output relationships and system models can be represented using matrices.

## Probability

Transition matrices model stochastic processes.

## Networks

Adjacency matrices represent connections between nodes.

## Cryptography

Some mathematical cryptographic systems use modular matrix operations, although ordinary floating-point matrix inversion is not appropriate for cryptographic arithmetic.

---

# 38. Limitations of the Educational Implementation

The script is intentionally self-contained and emphasizes algorithmic transparency.

Its limitations include:

- Dense nested-list representation is not optimized for large-scale numerical computation.
- Floating-point arithmetic can introduce rounding error.
- Recursive determinant calculation is impractical for large matrices.
- Gauss-Jordan inversion is educational but not always the most efficient numerical strategy.
- The implementation does not include sparse matrix storage.
- The implementation does not include specialized decompositions such as LU, QR, or singular value decomposition.
- The implementation does not use hardware acceleration or optimized low-level numerical kernels.

These limitations are important when distinguishing educational implementations from large-scale scientific or production numerical systems.

---

# 39. Core Mathematical Relationships Demonstrated

The script demonstrates the following relationships directly:

    A + B = B + A

for compatible addition.

    (A + B)^T = A^T + B^T

for transpose.

    (AB)^T = B^T A^T

for products.

    A * I = A

for the identity matrix.

    A * A^-1 = I

for invertible matrices.

    (AB)^-1 = B^-1 A^-1

for invertible matrices.

    Ax = b

for systems of linear equations.

    x = A^-1 b

as the inverse-based solution when the inverse exists.

    A^0 = I

for square matrices.

These relationships demonstrate that matrix algebra resembles ordinary arithmetic in some ways while differing significantly in others, especially with respect to multiplication order and dimensional compatibility.
