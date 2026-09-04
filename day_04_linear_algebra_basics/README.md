# Linear Algebra Basics: Vectors, Matrices, and Notation

## 1. Topic Introduction

Linear algebra is the mathematical study of vectors, matrices, linear transformations, systems of linear equations, and the spaces in which these objects exist.

The Python script accompanying this README develops these ideas progressively. It begins with scalars and vectors, introduces matrix notation and matrix operations, and then connects those operations to geometric transformations, linear systems, subspaces, bases, determinants, inverses, orthogonality, and numerical computation.

The implementations are intentionally written largely from scratch using Python's standard library. This makes the mathematical mechanisms explicit rather than hiding them behind a specialized numerical package.

---

## 2. Scalars and Numbers

A **scalar** is a single numerical quantity.

Examples include:

- `5`
- `-3`
- `2.75`
- `0`

Scalars are used to measure magnitude and to scale vectors and matrices.

For a scalar `c` and vector `v`, scalar multiplication is written as:

`cv`

If

`v = [2, 4, 6]`

then

`3v = [6, 12, 18]`.

The script demonstrates scalar arithmetic and scalar multiplication before introducing vectors.

---

## 3. Vectors

A **vector** is an ordered collection of numbers.

A two-dimensional vector can be written as:

`v = [v₁, v₂]`

A three-dimensional vector can be written as:

`v = [v₁, v₂, v₃]`

More generally:

`v = [v₁, v₂, ..., vₙ]`

The number of components is the vector's **dimension**.

The script implements a `Vector` class that stores components and supports:

- vector addition
- vector subtraction
- negation
- scalar multiplication
- scalar division
- dot products
- norms
- normalization
- distance
- angles

### 3.1 Vector Addition

Two vectors of the same dimension are added component by component:

`u + v = [u₁ + v₁, u₂ + v₂, ..., uₙ + vₙ]`

For example:

`[1, 2] + [3, 4] = [4, 6]`

Vectors with different dimensions cannot be added.

### 3.2 Vector Subtraction

Vector subtraction is also component-wise:

`u - v = [u₁ - v₁, ..., uₙ - vₙ]`

It can also be interpreted geometrically as the displacement from one point or vector to another.

### 3.3 Scalar Multiplication

Multiplying a vector by a scalar multiplies every component:

`c[v₁, v₂, ..., vₙ] = [cv₁, cv₂, ..., cvₙ]`

A positive scalar changes magnitude without changing direction. A negative scalar reverses direction.

---

## 4. Vector Dimension and Rⁿ

The notation `Rⁿ` represents the set of all real-valued vectors with `n` components.

Examples:

- `R¹` contains real numbers.
- `R²` contains two-dimensional real vectors.
- `R³` contains three-dimensional real vectors.
- `Rⁿ` contains n-dimensional real vectors.

A vector in `R³` has three real components:

`v = [v₁, v₂, v₃]`

Dimension is not the same concept as magnitude. A vector may belong to `R³` while having length zero, one, or any other nonnegative value.

---

## 5. Dot Product

The **dot product**, or inner product in ordinary Euclidean space, combines two vectors of equal dimension to produce a scalar.

For:

`u = [u₁, ..., uₙ]`

and

`v = [v₁, ..., vₙ]`

the dot product is:

`u · v = u₁v₁ + u₂v₂ + ... + uₙvₙ`

For example:

`[1, 2] · [3, 4] = 1(3) + 2(4) = 11`

The script implements the dot product directly with component-wise multiplication and summation.

### 5.1 Geometric Meaning

For nonzero vectors:

`u · v = ||u|| ||v|| cos(θ)`

where:

- `||u||` is the length of `u`
- `||v||` is the length of `v`
- `θ` is the angle between them

This gives several important consequences.

If:

`u · v > 0`

the angle is acute.

If:

`u · v = 0`

the vectors are perpendicular.

If:

`u · v < 0`

the angle is obtuse.

---

## 6. Vector Norm

A **norm** measures the size or length of a vector.

The standard Euclidean, or L2, norm is:

`||v|| = sqrt(v₁² + v₂² + ... + vₙ²)`

For:

`v = [3, 4]`

the norm is:

`||v|| = sqrt(3² + 4²) = 5`

The script provides:

- Euclidean norm
- squared Euclidean norm
- L1 norm
- infinity norm

### 6.1 L1 Norm

The L1 norm is:

`||v||₁ = |v₁| + |v₂| + ... + |vₙ|`

It measures total absolute magnitude.

### 6.2 Infinity Norm

The infinity norm is:

`||v||∞ = max(|v₁|, ..., |vₙ|)`

It measures the magnitude of the largest component.

Different norms are useful in different mathematical and computational settings.

---

## 7. Unit Vectors

A **unit vector** has norm equal to one.

For a nonzero vector:

`v̂ = v / ||v||`

The result points in the same direction as `v` but has length one.

The zero vector cannot be normalized because division by its norm would require division by zero and the zero vector has no unique direction.

The script explicitly raises an error when normalization of the zero vector is attempted.

---

## 8. Distance Between Vectors

The Euclidean distance between two vectors is:

`d(u, v) = ||u - v||`

For example:

`u = [1, 2]`

`v = [4, 6]`

gives:

`v - u = [3, 4]`

and therefore:

`d(u, v) = 5`.

This relationship connects vector subtraction with geometry.

---

## 9. Cross Product

The script also demonstrates the three-dimensional **cross product**.

For:

`a = [a₁, a₂, a₃]`

and

`b = [b₁, b₂, b₃]`

the cross product is:

`a × b = [a₂b₃ - a₃b₂, a₃b₁ - a₁b₃, a₁b₂ - a₂b₁]`

The result is a vector perpendicular to both input vectors.

Unlike the dot product, which produces a scalar, the cross product produces a vector.

The familiar binary cross product is specifically associated with three-dimensional Euclidean vectors. It should not be treated as a general replacement for vector multiplication in arbitrary dimensions.

The order matters:

`a × b = -(b × a)`

---

## 10. Matrices

A **matrix** is a rectangular arrangement of numbers.

A matrix with `m` rows and `n` columns has shape:

`m × n`

For example:

`A =`

`[1 2 3]`

`[4 5 6]`

is a `2 × 3` matrix.

The script's `Matrix` class represents matrices as immutable tuples internally and provides:

- indexing
- shape information
- row access
- column access
- addition
- subtraction
- scalar multiplication
- matrix multiplication
- matrix-vector multiplication
- transpose
- trace

---

## 11. Matrix Notation

Matrix elements are conventionally written using two indices.

For matrix `A`:

`Aᵢⱼ`

means the element in row `i` and column `j`.

Mathematical notation generally begins indexing at 1:

`A₁₁`

Python uses zero-based indexing, so the corresponding Python expression is:

`A[0][0]`

This distinction is important when translating mathematical algorithms into programs.

---

## 12. Matrix Shape

A matrix's shape is written as:

`rows × columns`

For example:

`A ∈ R²ˣ³`

means that `A` has two rows and three columns.

Shape determines which operations are valid.

### Matrix Addition

For:

`A + B`

both matrices must have exactly the same shape.

### Matrix Multiplication

For:

`AB`

the number of columns in `A` must equal the number of rows in `B`.

If:

`A` is `m × n`

and:

`B` is `n × p`

then:

`AB` is `m × p`.

This rule is one of the most important practical rules in introductory linear algebra.

---

## 13. Matrix Addition and Subtraction

Matrix addition is component-wise.

If:

`A = [aᵢⱼ]`

and:

`B = [bᵢⱼ]`

then:

`A + B = [aᵢⱼ + bᵢⱼ]`

The matrices must have identical dimensions.

Matrix subtraction follows the same shape requirement.

---

## 14. Scalar Multiplication of Matrices

A scalar multiplies every matrix entry.

For scalar `c`:

`cA = [caᵢⱼ]`

This operation does not change the matrix shape.

---

## 15. Matrix Transpose

The **transpose** of a matrix exchanges rows and columns.

If:

`A =`

`[1 2 3]`

`[4 5 6]`

then:

`Aᵀ =`

`[1 4]`

`[2 5]`

`[3 6]`

The shape changes from `m × n` to `n × m`.

Important identities include:

`(Aᵀ)ᵀ = A`

`(A + B)ᵀ = Aᵀ + Bᵀ`

`(AB)ᵀ = BᵀAᵀ`

The reversal of multiplication order in the last identity is important.

---

## 16. Special Matrices

The script demonstrates several important matrix classifications.

### 16.1 Zero Matrix

A zero matrix contains only zeros.

For example:

`[0 0]`

`[0 0]`

is a `2 × 2` zero matrix.

It acts as the additive identity:

`A + 0 = A`

### 16.2 Identity Matrix

The identity matrix contains ones on the main diagonal and zeros elsewhere.

For `I₃`:

`[1 0 0]`

`[0 1 0]`

`[0 0 1]`

The identity satisfies:

`AI = IA = A`

when the dimensions are compatible.

### 16.3 Diagonal Matrix

A diagonal matrix has zeros outside its main diagonal.

Example:

`[2 0 0]`

`[0 5 0]`

`[0 0 7]`

### 16.4 Triangular Matrix

An upper triangular matrix has zeros below the main diagonal.

A lower triangular matrix has zeros above the main diagonal.

For a triangular matrix, the determinant is the product of its diagonal entries.

### 16.5 Symmetric Matrix

A square matrix is symmetric if:

`A = Aᵀ`

Thus:

`Aᵢⱼ = Aⱼᵢ`

for every pair of indices.

The script also demonstrates the decomposition:

`A = (A + Aᵀ)/2 + (A - Aᵀ)/2`

where the first component is symmetric and the second is skew-symmetric.

---

## 17. Matrix Multiplication

Matrix multiplication is fundamentally different from element-wise multiplication.

For:

`A ∈ Rᵐˣⁿ`

and:

`B ∈ Rⁿˣᵖ`

the product `AB` has entries:

`(AB)ᵢⱼ = Σₖ AᵢₖBₖⱼ`

Each output element is the dot product of a row of `A` and a column of `B`.

The script implements this row-column rule directly.

### 17.1 Non-Commutativity

In general:

`AB ≠ BA`

Sometimes both products exist and differ. Sometimes one product exists while the reverse product is dimensionally invalid.

This differs from ordinary scalar multiplication, where:

`ab = ba`.

---

## 18. Matrix-Vector Multiplication

If:

`A ∈ Rᵐˣⁿ`

and:

`x ∈ Rⁿ`

then:

`Ax ∈ Rᵐ`.

Each component of the result is a dot product between one row of `A` and the vector `x`.

Matrix-vector multiplication is one of the central operations of linear algebra.

---

## 19. Matrices as Linear Transformations

A matrix can represent a function between vector spaces.

For a matrix `A`, define:

`T(x) = Ax`

The transformation is **linear** if:

`T(u + v) = T(u) + T(v)`

and:

`T(cu) = cT(u)`.

The script explicitly verifies these properties.

Common transformations represented by matrices include:

- scaling
- rotation
- reflection
- shearing
- projection
- coordinate transformations

---

## 20. Composition of Transformations

If transformation `S` is followed by transformation `R`, the combined transformation is:

`R(S(x))`

which can be written:

`RSx`.

The order is significant.

For example:

`RS ≠ SR`

in general.

This is another practical interpretation of the non-commutativity of matrix multiplication.

---

## 21. Row Vectors and Column Vectors

A row vector can be represented as:

`[1 2 3]`

with shape `1 × 3`.

A column vector is:

`[1]`

`[2]`

`[3]`

with shape `3 × 1`.

Although the same numerical components appear, their shapes and multiplication behavior are different.

The conventional representation of a vector in expressions such as:

`Ax`

is a column vector.

---

## 22. Outer Product

The **outer product** of vectors `u` and `v` is:

`uvᵀ`

If `u` has `m` components and `v` has `n` components, then `uvᵀ` is an `m × n` matrix.

Its entries are:

`(uvᵀ)ᵢⱼ = uᵢvⱼ`

This should be distinguished from the dot product.

The dot product:

`uᵀv`

produces a scalar.

The outer product:

`uvᵀ`

produces a matrix.

---

## 23. Hadamard Product

The **Hadamard product** is element-wise matrix multiplication.

It is commonly written:

`A ⊙ B`

with:

`(A ⊙ B)ᵢⱼ = AᵢⱼBᵢⱼ`

The matrices must have the same shape.

This differs from:

`AB`

which uses row-column multiplication.

The script deliberately computes both operations on the same matrices to make the distinction explicit.

---

## 24. Linear Combinations

A **linear combination** of vectors is an expression of the form:

`c₁v₁ + c₂v₂ + ... + cₖvₖ`

where the `cᵢ` are scalars.

The script implements arbitrary linear combinations.

The standard basis in `R²` is:

`e₁ = [1, 0]`

`e₂ = [0, 1]`

Every vector `[x, y]` can be written as:

`xe₁ + ye₂`.

This demonstrates the relationship between vectors and coordinates.

---

## 25. Linear Independence

A collection of vectors is **linearly independent** if the equation:

`c₁v₁ + ... + cₖvₖ = 0`

has only the trivial solution:

`c₁ = ... = cₖ = 0`.

A set is dependent if there is a nontrivial combination that produces the zero vector.

For two vectors in `R²`, placing them as matrix columns gives:

`A = [v₁ v₂]`

and the vectors are independent exactly when:

`det(A) ≠ 0`.

The script demonstrates both independent and dependent pairs.

---

## 26. Basis

A **basis** is a linearly independent set that spans a vector space.

For `R²`, the standard basis is:

`{[1, 0], [0, 1]}`.

A basis provides a coordinate system for the vector space.

A vector can be represented by coordinates relative to a chosen basis.

If the basis vectors are columns of matrix `B`, then finding coordinates `c` of a target vector `x` requires solving:

`Bc = x`.

The script implements this using its linear-system solver.

---

## 27. Affine Combinations

A linear combination allows arbitrary scalar coefficients.

An **affine combination** imposes the additional constraint:

`c₁ + c₂ + ... + cₖ = 1`.

For two points `p` and `q`, the midpoint is:

`0.5p + 0.5q`.

The script demonstrates affine combinations because they clarify an important distinction between linear algebra and affine geometry.

A linear subspace must contain the origin. An affine set does not necessarily contain the origin.

---

## 28. Linear and Affine Geometry

Consider the line:

`y = 2x`.

It passes through the origin and can be represented as:

`t[1, 2]`.

This is a linear subspace of `R²`.

Now consider:

`y = 2x + 1`.

This line does not pass through the origin. It can be represented as:

`[0, 1] + t[1, 2]`.

It is an affine line but not a linear subspace.

This distinction becomes important when interpreting equations, transformations, optimization problems, and geometric models.

---

## 29. Determinants

The **determinant** is a scalar associated with a square matrix.

For a `2 × 2` matrix:

`A = [a b; c d]`

the determinant is:

`det(A) = ad - bc`.

The script also implements determinants of larger matrices recursively through minors and cofactors.

### 29.1 Geometric Meaning

For a linear transformation represented by `A`:

- `|det(A)|` gives the area-scaling factor in two dimensions.
- `|det(A)|` gives the volume-scaling factor in three dimensions.
- A negative determinant indicates orientation reversal.

### 29.2 Invertibility

A square matrix is invertible exactly when:

`det(A) ≠ 0`.

If:

`det(A) = 0`

the matrix is singular and has no ordinary inverse.

---

## 30. Minors and Cofactors

The **minor** `Mᵢⱼ` is obtained by deleting row `i` and column `j`.

The **cofactor** is:

`Cᵢⱼ = (-1)^(i+j) Mᵢⱼ`.

The signs follow the checkerboard pattern:

`+ - +`

`- + -`

`+ - +`

The determinant can be calculated by expanding along a row or column using cofactors.

The script implements:

- minor matrices
- individual cofactors
- cofactor matrices
- the adjugate

---

## 31. Adjugate and Inverse

The **adjugate** is the transpose of the cofactor matrix:

`adj(A) = Cᵀ`.

For an invertible square matrix:

`A⁻¹ = adj(A) / det(A)`.

Although this formula is mathematically important, explicitly computing an inverse through cofactors is usually not the preferred numerical method for solving systems.

The script computes inverses through Gauss-Jordan elimination, which exposes the operational mechanism:

`[A | I] → [I | A⁻¹]`.

---

## 32. Gaussian Elimination

**Gaussian elimination** transforms a system or matrix using elementary row operations.

The fundamental row operations are:

1. Swap two rows.
2. Multiply a row by a nonzero scalar.
3. Add a multiple of one row to another row.

These operations preserve the solution set of a linear system when applied consistently to the augmented system.

The script implements Gaussian elimination with partial pivoting.

---

## 33. Partial Pivoting

Numerical computation introduces floating-point error.

When eliminating a column, a very small pivot can cause large numerical errors when used as a divisor.

**Partial pivoting** chooses a row with a comparatively large absolute pivot value and swaps it into the pivot position.

This generally improves numerical stability.

It does not eliminate every possible numerical problem, but it is a fundamental improvement over naive elimination.

---

## 34. Row-Echelon Form

A matrix is in row-echelon form when:

- all nonzero rows occur above zero rows
- each leading entry is to the right of the leading entry in the row above
- entries below each pivot are zero

Gaussian elimination produces row-echelon form.

---

## 35. Reduced Row-Echelon Form

A matrix is in **reduced row-echelon form**, or RREF, when it satisfies stronger conditions:

- every nonzero row has a leading 1
- every leading 1 is the only nonzero entry in its column
- pivots move to the right as rows progress downward
- zero rows occur at the bottom

RREF is unique for a matrix.

The script implements Gauss-Jordan elimination to compute RREF.

---

## 36. Rank

The **rank** of a matrix is the number of pivot positions.

Equivalent interpretations include:

- dimension of the row space
- dimension of the column space
- maximum number of linearly independent rows
- maximum number of linearly independent columns
- number of pivots in RREF

For a matrix `A`:

`rank(A) ≤ min(rows(A), columns(A))`.

A square `n × n` matrix has full rank when:

`rank(A) = n`.

For a square matrix, full rank is equivalent to invertibility.

---

## 37. Solving Linear Systems

A linear system can be written compactly as:

`Ax = b`.

For example:

`2x + y = 7`

`x - y = 1`

becomes:

`[2 1] [x] = [7]`

`[1 -1] [y]   [1]`.

The matrix `A` contains coefficients, `x` contains unknowns, and `b` contains the right-hand side.

The script solves a square system with a unique solution using:

1. partial pivoting
2. forward elimination
3. back substitution

---

## 38. Types of Linear-System Behavior

A system may have:

### Unique solution

There is exactly one vector `x` satisfying:

`Ax = b`.

### No solution

The equations are inconsistent.

### Infinitely many solutions

The system is consistent but contains free variables.

Rank provides a systematic way to classify these cases.

For an augmented system:

`Ax = b`

the system is consistent when:

`rank(A) = rank([A | b])`.

A unique solution occurs when that common rank equals the number of unknowns.

---

## 39. Matrix Inverse

For a square matrix `A`, an inverse `A⁻¹` satisfies:

`AA⁻¹ = A⁻¹A = I`.

The inverse exists only when `A` is nonsingular.

If:

`Ax = b`

and `A` is invertible, then:

`x = A⁻¹b`.

This identity is mathematically useful, but directly computing an inverse is not always the best numerical strategy.

When only a solution is needed, a suitable decomposition-based solver is usually preferable to explicitly forming `A⁻¹`.

---

## 40. Orthogonality

Two vectors are **orthogonal** when their dot product is zero:

`u · v = 0`.

For example:

`[1, 0] · [0, 1] = 0`.

Orthogonality generalizes the idea of perpendicularity to higher-dimensional vector spaces.

Orthogonal vectors are especially useful because many calculations simplify when components are perpendicular.

---

## 41. Projection

The projection of `u` onto a nonzero vector `v` is:

`projᵥ(u) = ((u · v)/(v · v))v`.

The script computes the projection and the residual:

`u - projᵥ(u)`.

The residual is orthogonal to `v`.

This decomposition is fundamental to least squares, orthogonal bases, approximation, and numerical linear algebra.

---

## 42. Gram-Schmidt Process

The **Gram-Schmidt process** transforms linearly independent vectors into an orthonormal set spanning the same subspace.

For the first vector:

`u₁ = v₁`

`q₁ = u₁ / ||u₁||`.

For later vectors:

`uₖ = vₖ - Σⱼ projection(qⱼ, vₖ)`

followed by:

`qₖ = uₖ / ||uₖ||`.

An orthonormal set satisfies:

`qᵢ · qⱼ = 0` for `i ≠ j`

and:

`||qᵢ|| = 1`.

The script explicitly verifies these properties.

---

## 43. Column Space

The **column space** of a matrix is the span of its columns.

If:

`A = [a₁ a₂ ... aₙ]`

then:

`Col(A) = span{a₁, a₂, ..., aₙ}`.

Only the independent columns are needed to construct a basis.

The script finds pivot columns and returns the corresponding original matrix columns as a basis for the column space.

---

## 44. Row Space

The **row space** is the span of the rows of a matrix.

An important theorem states:

`dim(Row(A)) = dim(Col(A)) = rank(A)`.

Although the script focuses computationally on RREF and pivot information, the rank examples illustrate this relationship.

---

## 45. Null Space

The **null space**, or kernel, of `A` is:

`Null(A) = {x : Ax = 0}`.

A vector in the null space is mapped to the zero vector by the linear transformation represented by `A`.

Free variables in a system `Ax = 0` generate the null-space basis.

The script demonstrates this relationship for a simple two-column matrix.

---

## 46. Rank-Nullity Relationship

For a linear transformation represented by an `m × n` matrix:

`rank(A) + nullity(A) = n`.

Here:

- `rank(A)` is the dimension of the image or column space.
- `nullity(A)` is the dimension of the null space.
- `n` is the number of columns.

This is the **rank-nullity theorem**.

It explains how the input-space dimensions divide between directions that survive the transformation and directions that collapse into the kernel.

---

## 47. Trace

The **trace** of a square matrix is the sum of its diagonal elements:

`tr(A) = Σᵢ Aᵢᵢ`.

For:

`A = [1 2; 3 4]`

the trace is:

`1 + 4 = 5`.

An important identity is:

`tr(AB) = tr(BA)`

when both products are defined and square.

This does not imply:

`AB = BA`.

The trace is also linear:

`tr(A + B) = tr(A) + tr(B)`.

---

## 48. Determinant Identities

Important determinant properties include:

`det(I) = 1`

`det(Aᵀ) = det(A)`

`det(AB) = det(A)det(B)`

If `A` is invertible:

`det(A⁻¹) = 1/det(A)`.

The script tests the multiplicative determinant identity directly.

---

## 49. Numerical Precision

Computer arithmetic uses finite-precision floating-point representations.

A classic example is:

`0.1 + 0.2`

which may not be represented as exactly `0.3` in binary floating-point arithmetic.

Consequently, numerical code should often compare values using a tolerance rather than exact equality.

The script provides an `approximately_equal` helper.

A tolerance is not universally correct. Appropriate tolerances depend on:

- numerical scale
- algorithm
- conditioning
- expected error
- floating-point precision

---

## 50. Conditioning

A problem can be mathematically well-defined but numerically sensitive.

A matrix that is nearly singular can have a determinant that is nonzero while still causing numerical difficulties.

The **condition number** measures sensitivity of a problem to perturbations.

A large condition number means that small errors in the input can potentially cause large errors in the output.

This distinction is essential:

- mathematical invertibility concerns whether an inverse exists
- numerical stability concerns whether computation produces reliable results

The script demonstrates a nearly dependent matrix to illustrate this distinction.

---

## 51. Common Matrix Mistakes

### Treating `AB` as element-wise multiplication

Ordinary matrix multiplication uses row-column dot products.

Element-wise multiplication is a separate operation, represented in the script as the Hadamard product.

### Assuming `AB = BA`

Matrix multiplication is generally non-commutative.

### Ignoring dimensions

For:

`A ∈ Rᵐˣⁿ`

and:

`B ∈ Rᵖˣᑫ`

the product `AB` is defined only when:

`n = p`.

### Adding incompatible matrices

Matrix addition requires equal shapes.

### Assuming every square matrix is invertible

A square matrix can be singular.

Invertibility requires:

`det(A) ≠ 0`

or equivalently:

`rank(A) = n`

for an `n × n` matrix.

### Normalizing the zero vector

The zero vector cannot be normalized because its norm is zero.

### Confusing vectors with their coordinate representations

A vector is an abstract mathematical object, while its coordinates depend on a selected basis.

### Using exact floating-point equality

Numerical results should generally be compared with an appropriate tolerance.

---

## 52. Edge Cases Demonstrated by the Script

The implementation explicitly handles several invalid or exceptional cases:

- adding vectors of different dimensions
- multiplying incompatible matrices
- multiplying an incompatible matrix and vector
- normalizing the zero vector
- computing a determinant of a non-square matrix
- computing an inverse of a singular matrix
- dividing a vector by zero
- constructing empty vectors or matrices
- creating matrices with inconsistent row lengths
- attempting to compute an angle involving the zero vector
- using invalid affine-combination weights
- attempting Gram-Schmidt on dependent vectors

These checks are important because mathematical definitions often include domain restrictions.

---

## 53. Block Matrices

Large matrices can be partitioned into smaller matrix blocks.

A block matrix can be written conceptually as:

`[A B]`

`[C D]`

Block notation is useful when a problem naturally contains subsystems.

It appears in:

- optimization
- statistics
- numerical linear algebra
- control systems
- computer graphics
- scientific computing

The block representation does not change the underlying matrix. It changes how the matrix is organized conceptually for analysis or computation.

---

## 54. Matrix Decompositions and Structure

The script introduces several structural ideas without relying on external numerical packages.

Important classifications include:

- square matrices
- rectangular matrices
- diagonal matrices
- triangular matrices
- symmetric matrices
- zero matrices
- identity matrices
- singular matrices
- nonsingular matrices
- full-rank matrices
- rank-deficient matrices

Recognizing structure can make calculations substantially simpler.

For example, the determinant of a triangular matrix is simply the product of its diagonal entries.

---

## 55. Performance Considerations

The educational implementations prioritize clarity over numerical performance.

The determinant function uses recursive expansion by minors. This is useful for demonstrating the mathematical definition but becomes computationally expensive as matrix size increases.

Similarly, explicitly computing an inverse through Gauss-Jordan elimination is educational but is not always the best choice for production numerical workloads.

For serious numerical computation, algorithms based on factorizations such as:

- LU decomposition
- QR decomposition
- Cholesky decomposition
- singular value decomposition

are generally more appropriate depending on the problem.

The key principle is to choose an algorithm according to the mathematical structure and numerical requirements rather than automatically expanding formulas.

---

## 56. Security and Validation Considerations

Linear algebra itself is mathematical rather than security-specific, but software implementing mathematical operations still requires defensive validation.

The script validates:

- dimensions
- shapes
- empty inputs
- zero denominators
- square-matrix requirements
- singularity
- affine coefficient constraints

In a production system, additional concerns can include:

- input size limits
- memory consumption
- denial-of-service risks from unexpectedly large matrices
- numerical overflow and underflow
- malformed serialized data
- precision and reproducibility requirements

Untrusted matrix dimensions should not be allowed to trigger uncontrolled computational work.

---

## 57. Implementation Design

The script separates mathematical concepts into reusable components.

The `Vector` class encapsulates vector operations.

The `Matrix` class encapsulates matrix operations.

Utility functions provide:

- approximate equality
- identity matrices
- zero matrices
- diagonal matrices
- determinant computation
- Gaussian elimination
- RREF
- rank
- linear-system solving
- matrix inversion
- projections
- Gram-Schmidt orthonormalization
- linear combinations
- affine combinations
- outer products
- Hadamard products

This separation makes the mathematical operations independently testable.

---

## 58. Testing Strategy

The script includes a dedicated test section using Python assertions.

The tests cover:

- vector addition
- vector subtraction
- scalar multiplication
- dot products
- norms
- matrix addition
- matrix multiplication
- transpose
- determinants
- inverse verification
- linear-system solutions
- rank
- orthogonality
- Gram-Schmidt orthonormality
- determinant multiplication

For example, inverse correctness is checked through:

`AA⁻¹ ≈ I`.

Approximate comparison is used because floating-point computations can introduce tiny numerical errors.

---

## 59. Practical Application: Linear Models

The script demonstrates a simple weighted model:

`y = wᵀx + b`.

Here:

- `x` is the feature vector
- `w` is the weight vector
- `b` is a scalar bias
- `y` is the resulting scalar

The weighted component calculation is exactly a dot product.

This illustrates why vectors and dot products are fundamental computational building blocks for many mathematical models.

---

## 60. Practical Application: Weighted Quantities

A weighted aggregate can be represented as:

`wᵀx`.

For values:

`x = [x₁, x₂, ..., xₙ]`

and weights:

`w = [w₁, w₂, ..., wₙ]`

the result is:

`w₁x₁ + ... + wₙxₙ`.

This is simply a linear combination and demonstrates how elementary linear algebra expresses weighted calculations compactly.

---

## 61. Practical Application: Simultaneous Equations

A collection of equations can be represented as:

`Ax = b`.

This notation provides a compact representation that scales naturally from two equations to thousands or millions of equations.

The same structural idea appears in:

- engineering models
- physical simulations
- optimization
- economics
- statistics
- computer graphics
- scientific computing
- numerical analysis

The mathematics remains the same even as the matrix size changes.

---

## 62. Important Distinctions

### Scalar vs Vector

A scalar is one numerical quantity.

A vector is an ordered collection of quantities.

### Vector vs Matrix

A vector can be treated as a special one-dimensional mathematical object. A matrix is a two-dimensional rectangular arrangement.

### Dot Product vs Outer Product

The dot product generally produces a scalar.

The outer product produces a matrix.

### Matrix Multiplication vs Hadamard Product

Matrix multiplication uses row-column products.

Hadamard multiplication is element-wise.

### Linear Combination vs Affine Combination

A linear combination allows arbitrary coefficients.

An affine combination requires coefficients to sum to one.

### Invertible vs Singular

An invertible matrix has an inverse.

A singular matrix does not.

### Mathematical Equality vs Numerical Approximation

Exact mathematical equality is not always represented exactly by floating-point computation.

---

## 63. Core Notation Reference

| Concept | Mathematical notation | Meaning |
|---|---|---|
| Scalar | `c` | One number |
| Vector | `v` | Ordered numerical components |
| Vector space | `Rⁿ` | Real vectors with n components |
| Matrix | `A` | Rectangular array |
| Matrix element | `Aᵢⱼ` | Entry in row i, column j |
| Matrix shape | `m × n` | m rows and n columns |
| Addition | `u + v` | Component-wise vector addition |
| Scalar multiplication | `cv` | Scale a vector |
| Dot product | `u · v` | Scalar inner product |
| Norm | `||v||` | Vector magnitude |
| Transpose | `Aᵀ` | Rows become columns |
| Identity | `I` | Multiplicative identity |
| Matrix multiplication | `AB` | Row-column multiplication |
| Matrix-vector product | `Ax` | Linear transformation |
| Determinant | `det(A)` | Scalar describing matrix properties |
| Inverse | `A⁻¹` | Matrix satisfying `AA⁻¹ = I` |
| Trace | `tr(A)` | Sum of diagonal entries |
| Rank | `rank(A)` | Number of independent directions/pivots |
| Null space | `Null(A)` | Vectors mapped to zero |
| Transpose | `Aᵀ` | Reflection across the main diagonal |
| Outer product | `uvᵀ` | Matrix formed from two vectors |
| Hadamard product | `A ⊙ B` | Element-wise multiplication |

---

## 64. Fundamental Rules

The most important operational rules demonstrated by the script are:

1. Vectors can be added only when they have the same dimension.
2. Matrices can be added only when they have the same shape.
3. A scalar can multiply any vector or matrix.
4. Matrix multiplication requires the inner dimensions to match.
5. The shape of `AB` is determined by the outer dimensions.
6. Matrix multiplication is generally not commutative.
7. The transpose reverses the order in a product: `(AB)ᵀ = BᵀAᵀ`.
8. A determinant exists for square matrices.
9. A square matrix is invertible exactly when it is nonsingular.
10. Rank equals the number of pivots.
11. Orthogonality can be tested with a zero dot product.
12. The zero vector cannot be normalized.
13. Floating-point results should generally be compared with suitable tolerances.
14. A basis must be linearly independent and spanning.
15. A linear subspace must contain the zero vector.

---

## 65. Relationship Between Major Concepts

Many introductory linear algebra topics are connected rather than isolated.

A matrix can represent a linear transformation.

That transformation maps vectors to vectors through:

`x → Ax`.

The columns of `A` describe where the standard basis vectors are mapped.

The column space describes the set of reachable outputs.

The null space describes the inputs that collapse to zero.

The rank measures the dimension of the reachable output space.

The determinant describes volume scaling for square transformations and determines whether a square matrix is invertible.

Gaussian elimination exposes pivots and rank and provides a practical method for solving systems.

A basis provides an independent coordinate system for representing vectors.

Orthogonality provides especially convenient bases and decompositions.

These relationships form the conceptual foundation of more advanced linear algebra.

---

## 66. Scope of the Implementation

The Python script is intentionally a foundational implementation rather than a replacement for a numerical linear algebra library.

It covers substantial introductory material, including:

- notation
- vectors
- vector operations
- norms
- dot products
- cross products
- matrices
- matrix arithmetic
- matrix multiplication
- transformations
- determinants
- cofactors
- inverses
- Gaussian elimination
- RREF
- rank
- systems of equations
- bases
- linear independence
- affine combinations
- orthogonality
- projections
- Gram-Schmidt
- column space
- null space
- special matrices
- numerical precision
- conditioning
- practical linear models
- automated tests

The implementations emphasize transparency so that the relationship between mathematical formulas and executable algorithms remains visible.
