# NumPy Linear Algebra: Vectors, Matrices, and Tensor Operations

## Scope

This learning artifact focuses on numerical linear algebra with NumPy, with emphasis on three related structures:

- **Vectors** represent one-dimensional numerical quantities and support operations such as addition, scalar multiplication, dot products, norms, projections, normalization, and similarity calculations.
- **Matrices** represent two-dimensional linear transformations and support matrix multiplication, transposition, determinants, linear-system solving, decompositions, eigenvalue analysis, and least-squares estimation.
- **Tensors** generalize arrays beyond two dimensions and are useful for batched observations, multidimensional scientific data, and operations that contract or reduce selected axes.

The implementations deliberately distinguish these structures rather than treating every NumPy array as interchangeable. Shape, dimensionality, broadcasting behavior, and the meaning of each axis determine whether an operation is mathematically valid.

## NumPy's Array Model

NumPy's central numerical structure is `ndarray`. An array has a shape, number of dimensions, data type, and contiguous block-oriented numerical storage managed by NumPy.

A vector such as `np.array([3.0, 4.0])` has shape `(2,)`.

A matrix such as `np.array([[1.0, 2.0], [3.0, 4.0]])` has shape `(2, 2)`.

A batch tensor such as `np.arange(24).reshape(2, 3, 4)` has shape `(2, 3, 4)`. The three axes may represent batch, row, and feature positions, but NumPy itself does not assign those semantic names. The programmer must define what each axis means.

This distinction is important because two arrays can contain the same number of values while representing completely different mathematical objects.

## Vectors

A vector is a one-dimensional array.

The Python implementation creates vectors with explicit floating-point values and examines properties such as `shape`, `ndim`, `size`, and `dtype`. It then demonstrates vector addition, subtraction, element-wise multiplication, scalar multiplication, and the dot product.

For vectors `a` and `b`, the dot product is

`a · b = Σ a_i b_i`

and is implemented in NumPy with `np.dot(a, b)` or, for ordinary vectors, `a @ b`.

### Norms

The Python implementation calculates:

- The L1 norm with `np.linalg.norm(v, ord=1)`.
- The Euclidean or L2 norm with `np.linalg.norm(v, ord=2)`.
- The L-infinity norm with `np.linalg.norm(v, ord=np.inf)`.

The L2 norm is

`||v||₂ = sqrt(Σ v_i²)`.

Normalization divides a nonzero vector by its L2 norm. The implementation explicitly avoids normalizing the zero vector because division by its norm is undefined.

### Projection

Projection separates a vector into a component parallel to another vector and a rejection component.

The projection of `a` onto `b` is

`proj_b(a) = ((a · b) / (b · b)) b`.

The Python script computes both the projection and the rejection and verifies that their sum reconstructs the original vector.

### Cosine Similarity

The Python implementation calculates cosine similarity as

`cos(theta) = (a · b) / (||a||₂ ||b||₂)`.

This measures angular alignment rather than absolute magnitude. The script clips the computed value before applying `arccos`, which prevents tiny floating-point errors from producing a value just outside the mathematical range `[-1, 1]`.

## Matrices

A matrix is a two-dimensional NumPy array with shape `(rows, columns)`.

The Python implementation demonstrates matrix indexing, row and column selection, slicing, scalar operations, element-wise multiplication, transposition, trace calculation, and matrix-vector multiplication.

Matrix multiplication is distinct from element-wise multiplication.

For matrices `A` and `B`, `A @ B` is valid when the number of columns in `A` equals the number of rows in `B`.

If `A` has shape `(m, n)` and `B` has shape `(n, p)`, then `A @ B` has shape `(m, p)`.

The `@` operator is therefore a shape-sensitive mathematical operation, whereas `A * B` performs element-wise multiplication when broadcasting permits it.

## Broadcasting

Broadcasting allows NumPy to combine arrays whose shapes are compatible according to NumPy's broadcasting rules.

The Python implementation adds a length-three vector to every row of a `(2, 3)` matrix. The vector has shape `(3,)`, so NumPy aligns it with the final matrix dimension.

Broadcasting avoids explicit Python loops, but it does not remove the need for shape reasoning. A shape that is mathematically incompatible still produces a `ValueError`.

For linear algebra, broadcasting is especially useful for batch operations and repeated centering or scaling.

## Linear Systems

A linear system can be written as

`Ax = b`.

The Python implementation uses `np.linalg.solve(A, b)` to compute `x`.

The important numerical practice is that solving `Ax = b` is normally preferable to explicitly computing `A⁻¹` and evaluating `A⁻¹b`. An inverse may be useful for analysis, but solving directly is generally more appropriate numerically and computationally.

The script validates the result by calculating `A @ x` and measuring the residual

`r = Ax - b`.

A small residual indicates that the computed solution satisfies the system to numerical precision.

Singular matrices are explicitly demonstrated as failure cases.

## Determinants, Inverses, and Conditioning

The determinant indicates whether a square matrix is singular. A zero determinant means the matrix does not have an ordinary inverse.

The Python script computes determinants with `np.linalg.det` and inverses with `np.linalg.inv`.

It also calculates the condition number using `np.linalg.cond`.

Conditioning matters because a matrix can be mathematically invertible while still being numerically sensitive. An ill-conditioned system can amplify small errors in input values and floating-point arithmetic.

The implementation therefore contrasts direct inversion with `np.linalg.solve` and shows why numerical linear algebra requires more than checking whether a determinant is nonzero.

## Eigenvalues and Eigenvectors

An eigenvector `v` of a matrix `A` satisfies

`Av = λv`.

The Python implementation uses `np.linalg.eig` for a general matrix and `np.linalg.eigh` for a symmetric matrix.

For symmetric matrices, `eigh` is preferred because it exploits the mathematical structure of the input and provides an appropriate numerical algorithm.

The script verifies computed eigenpairs by evaluating the residual

`Av - λv`.

A small residual provides an executable correctness check rather than assuming the returned values are correct.

## QR and SVD

The Python implementation uses QR decomposition to represent a matrix as

`A = QR`.

The script verifies that `Q` is approximately orthogonal by examining `QᵀQ` and reconstructs `A` through `Q @ R`.

Singular value decomposition represents a matrix as

`A = UΣVᵀ`.

The implementation obtains `U`, singular values, and `Vᵀ` with `np.linalg.svd`. It then constructs a rank-one approximation from the largest singular value and its associated singular vectors.

This demonstrates why singular values are useful for understanding numerical rank and low-rank approximations.

## Least-Squares Regression

When a system has more observations than unknown coefficients, an exact solution may not exist.

The Python implementation constructs a design matrix containing an intercept column and a feature column and uses `np.linalg.lstsq`.

For the linear model

`y ≈ Xβ`

the least-squares solution minimizes the squared residual magnitude.

The script checks the resulting residual vector and evaluates `Xᵀr`. At the least-squares optimum, the residual is orthogonal to the columns of the design matrix up to numerical precision.

## Tensors

A tensor is represented in NumPy by an array with more than two dimensions.

The Python tensor example has shape `(2, 3, 4)`. Its axes are deliberately treated as distinct dimensions rather than flattened immediately.

The implementation demonstrates:

- Shape and dimensionality inspection.
- Selecting slices.
- Reduction with `np.sum`.
- Reduction with `np.mean`.
- Axis reordering with `np.transpose`.
- Reshaping.
- Stacking.
- Concatenation.
- Tensor contraction with `np.tensordot`.

Reshaping changes how existing values are indexed without changing their total count. Transposition changes axis order. These operations should not be treated as interchangeable.

## Tensor Contraction

`np.tensordot` generalizes the idea of the dot product by contracting selected axes.

For two matrices, contracting one axis from each matrix can reproduce ordinary matrix multiplication.

The Python implementation compares a `tensordot` contraction with `@` for a two-dimensional example, then uses `einsum` for batched matrix multiplication.

## Einstein Summation

`np.einsum` provides explicit control over tensor contractions through index notation.

The Python implementation uses expressions such as:

`ij,j->i`

for matrix-vector multiplication and

`ij,jk->ik`

for matrix multiplication.

It also demonstrates extracting a diagonal with `ii->i`, calculating a trace with `ii->`, and performing batched matrix multiplication with `bij,bjk->bik`.

The notation is powerful because it makes contracted and preserved axes explicit. It can also make complicated expressions harder to read when the index labels are poorly chosen, so the operation should be documented when used in production code.

## Batched Linear Algebra

NumPy can operate on multiple matrices or vectors simultaneously.

The Python implementation stores three two-by-two matrices in an array with shape `(3, 2, 2)` and three corresponding vectors with shape `(3, 2)`.

Adding a singleton dimension to the vectors allows `np.matmul` to process the batch as matrix-vector products.

The same principle is used with `np.linalg.solve` to solve multiple compatible systems in one call.

This is one of the important distinctions between ordinary matrix operations and higher-dimensional tensor operations: leading dimensions can represent batches while the final dimensions represent the mathematical operands.

## Geometric Transformations

The Python implementation models two-dimensional rotations using a matrix:

`R = [[cos(theta), -sin(theta)], [sin(theta), cos(theta)]]`.

Point coordinates are transformed using matrix multiplication.

It also demonstrates scaling and homogeneous coordinates for translation. Homogeneous coordinates add a third coordinate so that translation can be represented by a matrix multiplication.

This connects abstract matrix multiplication to a concrete geometric interpretation.

## Covariance and PCA

The Python implementation centers observations, calculates a covariance matrix, and performs an eigenvalue decomposition.

For a data matrix whose rows are observations, centering subtracts the feature-wise mean.

The covariance matrix describes pairwise variation between features.

For symmetric covariance matrices, `np.linalg.eigh` returns eigenvalues and eigenvectors. Sorting the eigenvalues in descending order identifies the principal directions.

The corresponding explained variance ratios are calculated by dividing each eigenvalue by the sum of all eigenvalues.

## Python Implementation

The Python program is the primary NumPy implementation.

It contains executable demonstrations of:

- Vector arithmetic and geometry.
- Vector norms and normalization.
- Projection and cosine similarity.
- Matrix indexing and slicing.
- Broadcasting.
- Matrix-vector and matrix-matrix multiplication.
- Linear-system solving.
- Determinants, inverses, and condition numbers.
- Eigenvalue and eigenvector analysis.
- QR decomposition.
- SVD and low-rank approximation.
- Least-squares regression.
- Tensor reshaping and axis manipulation.
- `tensordot`.
- `einsum`.
- Batched matrix operations.
- Geometric transformations.
- Covariance and PCA.
- Numerical validation and edge cases.

Validation functions reject arrays with unsuitable dimensionality, nonnumeric values, NaN values, and infinite values where those conditions would make the demonstration mathematically invalid.

## JavaScript Implementation

The JavaScript program takes a complementary approach rather than pretending that ordinary JavaScript arrays are NumPy arrays.

It implements vector operations, matrix multiplication, matrix-vector multiplication, transpose, determinant calculation, Gaussian elimination, outer products, tensor shape inspection, flattening, reshaping, and basic tensor reduction.

The matrix solver uses Gaussian elimination with partial pivot selection. This demonstrates the algorithmic mechanism rather than relying on an external numerical library.

The program also demonstrates `Float64Array`. Typed arrays provide predictable numerical storage but do not automatically carry multidimensional shape metadata. Shape information therefore has to be managed separately.

Floating-point comparison is treated explicitly. The program shows why `0.1 + 0.2 === 0.3` is not a reliable numerical test and uses a tolerance-based comparison instead.

## C++ Case Study

The C++ program models an analytics system in which a customer profile is represented as a vector and a feature transformation is represented as a matrix.

The `Matrix` class stores values in contiguous row-major storage. It validates dimensions and implements matrix-matrix and matrix-vector multiplication.

The case study uses:

- Customer feature vectors.
- Weight vectors.
- Dot products.
- Normalization.
- Vector projection.
- Feature transformations.
- Gaussian elimination.
- Partial pivoting.
- Determinant calculation.
- Covariance matrices.
- Gram-matrix construction.
- Dimension validation.

The linear-system solver uses partial pivoting because blindly selecting the current diagonal element can produce unstable divisions when that value is very small.

The implementation also exposes the computational characteristics of dense linear algebra. Matrix-vector multiplication is quadratic for a square matrix, while dense square matrix multiplication is cubic in the conventional algorithm.

The handwritten implementation is intentionally educational. Large production C++ systems normally use optimized numerical libraries rather than application-level implementations of every numerical kernel.

## Java Enterprise Model

The Java program models linear algebra through explicit domain types.

`VectorModel` represents validated vectors and defensively copies its internal values.

`MatrixModel` represents matrices and associates each matrix with a `MatrixRole`. The role distinguishes matrices used as feature transformations, covariance matrices, system matrices, or projections.

This semantic distinction is useful in enterprise systems because shape alone does not explain the meaning of numerical data.

`VectorService` contains vector operations.

`LinearSystemService` contains the linear-system algorithm and its validation rules.

`CovarianceService` calculates a sample covariance matrix from observations.

The implementation uses Java records for the immutable vector domain value, standard collections and arrays, explicit exception handling, and defensive copies.

Failure states include zero-vector normalization, singular systems, and incompatible dimensions.

## SQL Data Model

The PostgreSQL implementation represents vectors, matrices, tensors, operations, and linear systems as relational entities.

`vector_dataset` stores a one-dimensional PostgreSQL array and a declared dimension. A check constraint ensures that the declared dimension matches the array length.

`matrix_dataset` stores a two-dimensional PostgreSQL array and separately records row and column counts. Shape constraints compare those declarations with the actual array dimensions.

`tensor_dataset` stores tensor dimensions separately from flattened values. The constraints ensure that the declared rank and total number of elements agree with the stored representation.

`matrix_vector_operation` records operations between compatible matrix and vector entities.

`linear_system` records the matrix, right-hand side, optional solution, residual norm, and solve timestamp.

Indexes are placed on matrix role and operation foreign keys because those fields support common lookup patterns.

## SQL Linear Algebra Operations

The SQL script demonstrates vector dot products by pairing array positions through `generate_series`.

The L2 norm is calculated from the sum of squared elements.

Vector normalization is expressed as a query that divides each element by the computed norm while protecting against division by zero with `NULLIF`.

Matrix trace is calculated by selecting equal row and column indexes.

Row and column reductions show how relational queries can reproduce selected matrix-axis operations.

Tensor metadata is queried without expanding every value. A tensor reduction then calculates sums across the final logical dimension using the tensor's declared shape and flattened storage.

A view named `linear_algebra_shapes` provides a unified shape inspection surface for vectors, matrices, and tensors.

The SQL transaction demonstrates atomic recording of a matrix-vector operation.

## Shape Is Part of the Type

NumPy arrays are dynamically typed with respect to dimensional shape, so mathematical correctness often depends on explicit shape reasoning.

A vector of shape `(3,)` and a matrix of shape `(3, 1)` both contain three numbers but behave differently in matrix operations.

Similarly, `(2, 3)` and `(3, 2)` have the same element count but represent incompatible orientations for many operations.

The implementations repeatedly validate shape before performing calculations because many linear algebra failures are dimensional rather than syntactic.

## Element-Wise Operations Versus Algebraic Operations

NumPy distinguishes element-wise multiplication from matrix multiplication.

`A * B` performs element-wise multiplication when the shapes are broadcast-compatible.

`A @ B` performs matrix multiplication according to linear algebra rules.

This distinction is central to correct NumPy programming. Accidentally using `*` when `@` was intended can produce a valid numerical result with completely different mathematical meaning.

## Numerical Precision

NumPy normally uses floating-point arithmetic for scientific calculations. Floating-point numbers cannot represent every real number exactly.

The Python implementation therefore uses `np.isclose` and `np.allclose` when testing numerical equality.

Exact equality is appropriate for some discrete values but is generally inappropriate for results involving matrix decomposition, iterative numerical algorithms, or accumulated floating-point operations.

The scripts also detect NaN and infinity values before performing operations that require finite input.

## Performance Considerations

NumPy's major performance advantage comes from vectorized operations implemented in optimized native code rather than Python-level loops.

The Python implementation therefore favors operations such as `@`, `np.sum`, `np.linalg.solve`, `np.linalg.svd`, `np.einsum`, and broadcasting.

For dense matrix multiplication, the standard arithmetic complexity is cubic for square matrices. Matrix-vector multiplication is quadratic for square matrices.

Memory layout also matters. Large tensors can consume substantial memory because the number of elements grows as the product of their dimensions.

Reshaping may return a view when the memory layout permits it, while some transformations can require copying data. Production code should therefore consider both computational complexity and memory behavior.

## Numerical Stability

A mathematically correct formula is not necessarily a numerically stable implementation.

Explicitly computing an inverse and multiplying by a vector is one example. Solving a linear system directly is generally preferable.

Condition numbers provide a way to assess sensitivity to perturbations.

Gaussian elimination benefits from pivoting.

Symmetric matrices should use algorithms designed for symmetric structure, such as `np.linalg.eigh`.

These distinctions matter when the data contains measurement error or when the matrix is close to singular.

## Common Failure Modes

A zero vector cannot be normalized.

A singular matrix cannot be used for a unique ordinary linear-system solution.

A non-square matrix does not have an ordinary determinant or inverse.

Matrix multiplication fails when the inner dimensions do not agree.

Broadcasting can silently produce a mathematically unintended result if dimensions happen to be compatible.

NaN and infinite values can contaminate subsequent numerical calculations.

A very large tensor can exhaust memory even when its individual elements are inexpensive to store.

Exact floating-point comparisons can fail even when two values are mathematically expected to be equal.

## Production Considerations

For production numerical systems, input validation should occur at system boundaries rather than relying on every internal function to rediscover invalid data.

Large numerical workloads should use vectorized operations and optimized linear-algebra routines.

Matrix shape and axis semantics should be documented clearly. For tensors, descriptions such as `(batch, height, width, channels)` are much safer than referring only to axis numbers.

Numerical tests should use tolerances appropriate to the scale and conditioning of the calculation.

Algorithms should be selected according to matrix structure. Symmetric, triangular, diagonal, sparse, and ill-conditioned matrices can require substantially different approaches.

Security considerations include rejecting malformed numerical input, bounding array sizes before allocation, validating uploaded numerical data, and avoiding uncontrolled memory consumption from user-supplied tensor dimensions.

## Relationship Between Vectors, Matrices, and Tensors

Vectors, matrices, and tensors form a hierarchy of multidimensional numerical representation, but they have different mathematical interpretations.

A vector can represent a point, feature set, direction, or coefficient set.

A matrix can represent a linear transformation, system of equations, covariance structure, or collection of vectors.

A tensor can represent batches of matrices, multidimensional measurements, or higher-order relationships.

NumPy unifies their storage through `ndarray`, while operations distinguish their meaning through shape, axes, and the selected function.

The core technical skill is therefore not merely knowing NumPy function names. It is understanding the mathematical object represented by each array and ensuring that the dimensions participating in an operation have the intended meaning.
