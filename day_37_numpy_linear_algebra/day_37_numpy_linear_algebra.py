import numpy as np


def print_heading(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def validate_vector(vector: np.ndarray, name: str = "vector") -> np.ndarray:
    array = np.asarray(vector)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional; got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError(f"{name} must contain numeric values")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains NaN or infinite values")
    return array


def validate_matrix(matrix: np.ndarray, name: str = "matrix") -> np.ndarray:
    array = np.asarray(matrix)
    if array.ndim != 2:
        raise ValueError(f"{name} must be two-dimensional; got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError(f"{name} must contain numeric values")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains NaN or infinite values")
    return array


def validate_tensor(tensor: np.ndarray, name: str = "tensor") -> np.ndarray:
    array = np.asarray(tensor)
    if array.ndim < 3:
        raise ValueError(f"{name} must have at least three dimensions; got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError(f"{name} must contain numeric values")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains NaN or infinite values")
    return array


def vector_basics() -> None:
    print_heading("Vectors: representation, arithmetic, norms, and projections")

    vector = np.array([3.0, 4.0, 0.0])
    other = np.array([1.0, 2.0, 5.0])

    validate_vector(vector)
    validate_vector(other)

    print("vector:", vector)
    print("shape:", vector.shape)
    print("dimension:", vector.ndim)
    print("element count:", vector.size)
    print("dtype:", vector.dtype)

    print("addition:", vector + other)
    print("subtraction:", vector - other)
    print("element-wise multiplication:", vector * other)
    print("scalar multiplication:", 2.5 * vector)
    print("dot product:", np.dot(vector, other))

    l1 = np.linalg.norm(vector, ord=1)
    l2 = np.linalg.norm(vector, ord=2)
    linf = np.linalg.norm(vector, ord=np.inf)

    print("L1 norm:", l1)
    print("L2 norm:", l2)
    print("L-infinity norm:", linf)

    unit = vector / np.linalg.norm(vector)
    print("unit vector:", unit)
    print("unit-vector norm:", np.linalg.norm(unit))

    projection = np.dot(vector, other) / np.dot(other, other) * other
    rejection = vector - projection

    print("projection of vector onto other:", projection)
    print("rejection component:", rejection)
    print("projection + rejection:", projection + rejection)

    cosine = np.dot(vector, other) / (
        np.linalg.norm(vector) * np.linalg.norm(other)
    )
    print("cosine similarity:", cosine)

    angle = np.arccos(np.clip(cosine, -1.0, 1.0))
    print("angle in radians:", angle)
    print("angle in degrees:", np.degrees(angle))


def matrix_basics() -> None:
    print_heading("Matrices: construction, indexing, broadcasting, and multiplication")

    matrix = np.array(
        [
            [2.0, 1.0, 3.0],
            [4.0, 0.0, 5.0],
            [1.0, 2.0, 1.0],
        ]
    )

    vector = np.array([10.0, 20.0, 30.0])

    validate_matrix(matrix)
    validate_vector(vector)

    print("matrix:\n", matrix)
    print("shape:", matrix.shape)
    print("rows:", matrix.shape[0])
    print("columns:", matrix.shape[1])

    print("first row:", matrix[0])
    print("second column:", matrix[:, 1])
    print("bottom-right element:", matrix[-1, -1])
    print("top-left 2x2 block:\n", matrix[:2, :2])

    print("matrix + 10:\n", matrix + 10)
    print("matrix * 2:\n", matrix * 2)
    print("element-wise matrix multiplication:\n", matrix * matrix)
    print("matrix-vector product:", matrix @ vector)
    print("transpose:\n", matrix.T)
    print("trace:", np.trace(matrix))
    print("determinant:", np.linalg.det(matrix))


def matrix_products_and_shapes() -> None:
    print_heading("Matrix multiplication and shape reasoning")

    a = np.arange(6, dtype=float).reshape(2, 3)
    b = np.arange(12, dtype=float).reshape(3, 4)

    print("A shape:", a.shape)
    print("B shape:", b.shape)
    print("A:\n", a)
    print("B:\n", b)
    print("A @ B shape:", (a @ b).shape)
    print("A @ B:\n", a @ b)

    try:
        print(a + b)
    except ValueError as error:
        print("Expected incompatible broadcasting error:", error)

    print("sum of each row:", np.sum(a, axis=1))
    print("sum of each column:", np.sum(a, axis=0))
    print("mean of each row:", np.mean(a, axis=1))
    print("column-wise maximum:", np.max(a, axis=0))

    expanded = a[:, :, np.newaxis]
    print("A with a singleton trailing axis:", expanded.shape)

    broadcast_vector = np.array([100.0, 200.0, 300.0])
    print("row-wise broadcasting:\n", a + broadcast_vector)


def linear_systems() -> None:
    print_heading("Linear systems: solving Ax = b")

    a = np.array(
        [
            [3.0, 2.0, -1.0],
            [2.0, -2.0, 4.0],
            [-1.0, 0.5, -1.0],
        ]
    )
    b = np.array([1.0, -2.0, 0.0])

    x = np.linalg.solve(a, b)

    print("A:\n", a)
    print("b:", b)
    print("solution x:", x)
    print("A @ x:", a @ x)
    print("residual:", a @ x - b)
    print("residual norm:", np.linalg.norm(a @ x - b))

    singular = np.array([[1.0, 2.0], [2.0, 4.0]])
    try:
        np.linalg.solve(singular, np.array([3.0, 6.0]))
    except np.linalg.LinAlgError as error:
        print("Singular-system failure:", error)


def inverse_and_conditioning() -> None:
    print_heading("Inverse matrices and numerical conditioning")

    matrix = np.array(
        [
            [4.0, 7.0],
            [2.0, 6.0],
        ]
    )

    determinant = np.linalg.det(matrix)
    inverse = np.linalg.inv(matrix)

    print("determinant:", determinant)
    print("inverse:\n", inverse)
    print("A @ A^-1:\n", matrix @ inverse)

    condition_number = np.linalg.cond(matrix)
    print("condition number:", condition_number)

    ill_conditioned = np.array(
        [
            [1.0, 1.0],
            [1.0, 1.00000001],
        ]
    )

    print("ill-conditioned matrix condition number:",
          np.linalg.cond(ill_conditioned))

    # A direct inverse is often unnecessary. Solving Ax=b is generally
    # numerically preferable to explicitly computing A^-1 and multiplying.
    b = np.array([2.0, 2.00000001])
    direct_solution = np.linalg.solve(ill_conditioned, b)
    inverse_solution = np.linalg.inv(ill_conditioned) @ b

    print("solve(A, b):", direct_solution)
    print("inv(A) @ b:", inverse_solution)


def eigenvalues_and_eigenvectors() -> None:
    print_heading("Eigenvalues and eigenvectors")

    matrix = np.array(
        [
            [4.0, 1.0],
            [2.0, 3.0],
        ]
    )

    eigenvalues, eigenvectors = np.linalg.eig(matrix)

    print("matrix:\n", matrix)
    print("eigenvalues:", eigenvalues)
    print("eigenvectors:\n", eigenvectors)

    for index, eigenvalue in enumerate(eigenvalues):
        vector = eigenvectors[:, index]
        residual = matrix @ vector - eigenvalue * vector
        print(
            f"eigenpair {index}: residual norm = "
            f"{np.linalg.norm(residual):.3e}"
        )

    symmetric = np.array(
        [
            [5.0, 2.0],
            [2.0, 2.0],
        ]
    )

    # eigh exploits the symmetry and provides numerically appropriate
    # eigenvalue/eigenvector calculations for symmetric matrices.
    values, vectors = np.linalg.eigh(symmetric)
    print("symmetric eigenvalues:", values)
    print("symmetric eigenvectors:\n", vectors)


def decompositions() -> None:
    print_heading("LU-style solving, QR, SVD, and low-rank approximation")

    matrix = np.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0],
        ]
    )

    q, r = np.linalg.qr(matrix)

    print("A:\n", matrix)
    print("Q:\n", q)
    print("R:\n", r)
    print("Q^T Q:\n", q.T @ q)
    print("Q @ R:\n", q @ r)

    u, singular_values, vt = np.linalg.svd(matrix, full_matrices=False)

    print("U:\n", u)
    print("singular values:", singular_values)
    print("V^T:\n", vt)
    print("SVD reconstruction:\n", u @ np.diag(singular_values) @ vt)

    rank = np.linalg.matrix_rank(matrix)
    print("matrix rank:", rank)

    # Keeping only the dominant singular component produces a rank-one
    # approximation and illustrates dimensionality reduction.
    rank_one = (
        singular_values[0]
        * np.outer(u[:, 0], vt[0, :])
    )
    print("rank-one approximation:\n", rank_one)
    print(
        "rank-one Frobenius error:",
        np.linalg.norm(matrix - rank_one, ord="fro"),
    )


def least_squares_regression() -> None:
    print_heading("Least-squares linear regression")

    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.1, 4.0, 6.2, 8.1, 9.9])

    design = np.column_stack((np.ones_like(x), x))
    coefficients, residuals, rank, singular_values = np.linalg.lstsq(
        design, y, rcond=None
    )

    predictions = design @ coefficients
    errors = y - predictions

    print("design matrix:\n", design)
    print("coefficients [intercept, slope]:", coefficients)
    print("predictions:", predictions)
    print("residuals:", errors)
    print("sum squared error:", np.sum(errors**2))
    print("rank:", rank)
    print("singular values:", singular_values)

    # The residual vector should be orthogonal to the design-matrix columns
    # at the least-squares optimum.
    print("X^T residual:", design.T @ errors)


def tensor_basics() -> None:
    print_heading("Tensors: axes, reshaping, stacking, and contraction")

    tensor = np.arange(24, dtype=float).reshape(2, 3, 4)
    validate_tensor(tensor)

    print("tensor shape:", tensor.shape)
    print("tensor ndim:", tensor.ndim)
    print("tensor:\n", tensor)

    print("first 2x4 slice:\n", tensor[:, 0, :])
    print("sum over last axis shape:", np.sum(tensor, axis=2).shape)
    print("sum over last axis:\n", np.sum(tensor, axis=2))

    print("mean over middle axis:\n", np.mean(tensor, axis=1))

    transposed = np.transpose(tensor, (2, 0, 1))
    print("axes reordered from (batch, row, column) to (column, batch, row):",
          transposed.shape)

    flattened = tensor.reshape(2, -1)
    print("flattened per batch:\n", flattened)

    restored = flattened.reshape(tensor.shape)
    print("reshape restored original:", np.array_equal(restored, tensor))

    first = np.ones((2, 3))
    second = np.full((2, 3), 5.0)
    print("stacked along a new axis:\n", np.stack([first, second], axis=0))
    print("concatenated along rows:\n", np.concatenate([first, second], axis=0))

    # tensordot contracts the specified axes, generalizing dot products to
    # higher-dimensional arrays.
    left = np.arange(6, dtype=float).reshape(2, 3)
    right = np.arange(12, dtype=float).reshape(3, 4)
    contraction = np.tensordot(left, right, axes=([1], [0]))
    print("tensordot contraction:\n", contraction)
    print("same operation using @:\n", left @ right)


def einsum_examples() -> None:
    print_heading("Einstein summation with einsum")

    matrix_a = np.array([[1.0, 2.0], [3.0, 4.0]])
    matrix_b = np.array([[5.0, 6.0], [7.0, 8.0]])
    vector = np.array([10.0, 20.0])

    matrix_vector = np.einsum("ij,j->i", matrix_a, vector)
    matrix_matrix = np.einsum("ij,jk->ik", matrix_a, matrix_b)
    diagonal = np.einsum("ii->i", matrix_a)
    trace = np.einsum("ii->", matrix_a)

    print("matrix-vector:", matrix_vector)
    print("matrix-matrix:\n", matrix_matrix)
    print("diagonal:", diagonal)
    print("trace:", trace)

    # Batched matrix multiplication demonstrates how einsum can express
    # tensor contractions while retaining batch dimensions.
    batch_a = np.arange(12, dtype=float).reshape(2, 2, 3)
    batch_b = np.arange(18, dtype=float).reshape(2, 3, 3)
    batch_result = np.einsum("bij,bjk->bik", batch_a, batch_b)

    print("batched A shape:", batch_a.shape)
    print("batched B shape:", batch_b.shape)
    print("batched result shape:", batch_result.shape)
    print("batched result:\n", batch_result)


def broadcasting_and_batch_linear_algebra() -> None:
    print_heading("Broadcasting and batched linear algebra")

    matrices = np.array(
        [
            [[2.0, 0.0], [0.0, 3.0]],
            [[4.0, 1.0], [2.0, 5.0]],
            [[1.0, 2.0], [3.0, 4.0]],
        ]
    )
    vectors = np.array(
        [
            [10.0, 20.0],
            [30.0, 40.0],
            [50.0, 60.0],
        ]
    )

    # np.matmul broadcasts over leading dimensions, so all three 2x2 systems
    # can be multiplied by their corresponding two-element vector in one call.
    result = np.matmul(matrices, vectors[..., np.newaxis]).squeeze(-1)

    print("matrices shape:", matrices.shape)
    print("vectors shape:", vectors.shape)
    print("batched matrix-vector result:\n", result)

    diagonal_matrices = np.array(
        [
            [[2.0, 0.0], [0.0, 5.0]],
            [[3.0, 0.0], [0.0, 7.0]],
        ]
    )
    right_hand_sides = np.array([[4.0, 10.0], [9.0, 21.0]])

    solutions = np.linalg.solve(diagonal_matrices, right_hand_sides)
    print("batched solutions:\n", solutions)


def geometric_transformations() -> None:
    print_heading("Geometric transformations with matrices")

    points = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
            [0.0, -1.0],
        ]
    )

    theta = np.pi / 4
    rotation = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )

    transformed = points @ rotation.T

    print("original points:\n", points)
    print("rotation matrix:\n", rotation)
    print("rotated points:\n", transformed)

    scaling = np.diag([2.0, 0.5])
    scaled_then_rotated = points @ scaling.T @ rotation.T
    print("scaled then rotated:\n", scaled_then_rotated)

    homogeneous_points = np.column_stack(
        [points, np.ones(points.shape[0])]
    )

    translation = np.array(
        [
            [1.0, 0.0, 3.0],
            [0.0, 1.0, -2.0],
            [0.0, 0.0, 1.0],
        ]
    )

    translated = homogeneous_points @ translation.T
    print("homogeneous translated points:\n", translated[:, :2])


def covariance_and_pca() -> None:
    print_heading("Covariance and PCA")

    observations = np.array(
        [
            [2.0, 1.0],
            [3.0, 2.0],
            [4.0, 3.0],
            [5.0, 4.0],
            [6.0, 5.0],
            [7.0, 6.0],
        ]
    )

    centered = observations - observations.mean(axis=0)
    covariance = np.cov(centered, rowvar=False)

    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    principal_scores = centered @ eigenvectors

    print("centered observations:\n", centered)
    print("covariance matrix:\n", covariance)
    print("principal variances:", eigenvalues)
    print("principal directions:\n", eigenvectors)
    print("principal scores:\n", principal_scores)

    explained_variance_ratio = eigenvalues / np.sum(eigenvalues)
    print("explained variance ratio:", explained_variance_ratio)


def sparse_like_manual_operation() -> None:
    print_heading("Efficient vectorized operations and memory awareness")

    rng = np.random.default_rng(42)
    data = rng.normal(size=(1000, 20))

    # Vectorized centering avoids an explicit Python loop over observations.
    centered = data - np.mean(data, axis=0)
    column_norms = np.linalg.norm(centered, axis=0)

    safe_norms = np.where(column_norms == 0, 1.0, column_norms)
    normalized_columns = centered / safe_norms

    print("data shape:", data.shape)
    print("centered shape:", centered.shape)
    print("largest column norm:", np.max(column_norms))
    print(
        "maximum absolute column norm after normalization:",
        np.max(np.linalg.norm(normalized_columns, axis=0)),
    )

    # Boolean masks select elements without manually iterating over indexes.
    high_values = data[data > 2.5]
    print("count of values greater than 2.5:", high_values.size)


def numerical_edge_cases() -> None:
    print_heading("Numerical edge cases and defensive checks")

    zero = np.zeros(3)
    try:
        zero_unit = zero / np.linalg.norm(zero)
        if not np.all(np.isfinite(zero_unit)):
            raise ValueError("Cannot normalize the zero vector")
    except ValueError as error:
        print("Zero-vector normalization:", error)

    empty = np.array([])
    print("empty vector shape:", empty.shape)

    try:
        validate_vector(np.array([1.0, np.nan]))
    except ValueError as error:
        print("NaN validation:", error)

    try:
        validate_matrix(np.ones((2, 2, 2)))
    except ValueError as error:
        print("Matrix-rank validation:", error)

    integer_matrix = np.array([[1, 2], [3, 4]])
    floating_result = integer_matrix / 2
    print("integer input with true division:\n", floating_result)

    # Floating-point equality should usually use a tolerance instead of ==.
    left = np.array([0.1 + 0.2])
    right = np.array([0.3])
    print("exact equality:", left == right)
    print("tolerance-aware equality:", np.allclose(left, right))


def performance_comparison() -> None:
    print_heading("Vectorization and computational complexity")

    rng = np.random.default_rng(7)
    matrix = rng.normal(size=(500, 500))
    vector = rng.normal(size=500)

    result = matrix @ vector
    print("matrix-vector result shape:", result.shape)

    # Matrix-vector multiplication for an m x n matrix requires O(mn)
    # arithmetic operations. NumPy delegates the heavy numerical work to
    # optimized native routines instead of executing Python-level loops.
    print("matrix-vector operation uses", matrix.size, "matrix elements")

    gram = matrix.T @ matrix
    print("Gram matrix shape:", gram.shape)
    print("Gram matrix approximately symmetric:",
          np.allclose(gram, gram.T, atol=1e-10))


def assertions_for_learning() -> None:
    print_heading("Executable correctness checks")

    vector = np.array([3.0, 4.0])
    assert np.isclose(np.linalg.norm(vector), 5.0)

    matrix = np.array([[1.0, 2.0], [3.0, 4.0]])
    inverse = np.linalg.inv(matrix)
    assert np.allclose(matrix @ inverse, np.eye(2))

    a = np.array([[2.0, 1.0], [1.0, 3.0]])
    b = np.array([5.0, 6.0])
    x = np.linalg.solve(a, b)
    assert np.allclose(a @ x, b)

    tensor = np.arange(24).reshape(2, 3, 4)
    assert tensor.transpose(2, 0, 1).shape == (4, 2, 3)

    print("All correctness checks passed.")


def main() -> None:
    print_heading("NumPy Linear Algebra: Vectors, Matrices, and Tensor Operations")
    print("NumPy version:", np.__version__)

    vector_basics()
    matrix_basics()
    matrix_products_and_shapes()
    linear_systems()
    inverse_and_conditioning()
    eigenvalues_and_eigenvectors()
    decompositions()
    least_squares_regression()
    tensor_basics()
    einsum_examples()
    broadcasting_and_batch_linear_algebra()
    geometric_transformations()
    covariance_and_pca()
    sparse_like_manual_operation()
    numerical_edge_cases()
    performance_comparison()
    assertions_for_learning()

    print_heading("Completed")
    print("The demonstrations covered vectors, matrices, tensors,")
    print("products, norms, systems, decompositions, contractions,")
    print("broadcasting, transformations, PCA, numerical stability,")
    print("and vectorized computation.")


if __name__ == "__main__":
    main()
