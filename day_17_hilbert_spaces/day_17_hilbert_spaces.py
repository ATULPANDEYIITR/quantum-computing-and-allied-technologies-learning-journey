"""
Hilbert Spaces
Mathematical framework

A self-contained study file progressing from Euclidean inner-product spaces
to abstract Hilbert-space ideas and practical numerical implementations.

The central theme is that a Hilbert space is an inner-product space that is
complete under the norm induced by its inner product.

This file uses finite-dimensional vector spaces for executable numerical
experiments and also demonstrates the mathematical structure of function
spaces through discrete approximations.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


# ============================================================================
# 1. FOUNDATIONS: VECTORS, INNER PRODUCTS, NORMS, AND DISTANCES
# ============================================================================

Vector = list[complex]


def add_vectors(a: Sequence[complex], b: Sequence[complex]) -> Vector:
    """Vector addition."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return [x + y for x, y in zip(a, b)]


def subtract_vectors(a: Sequence[complex], b: Sequence[complex]) -> Vector:
    """Vector subtraction."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return [x - y for x, y in zip(a, b)]


def scale_vector(scalar: complex, vector: Sequence[complex]) -> Vector:
    """Scalar multiplication."""
    return [scalar * x for x in vector]


def inner_product(a: Sequence[complex], b: Sequence[complex]) -> complex:
    """
    Standard complex inner product.

    Mathematically:
        <x, y> = sum(conjugate(x_i) * y_i)

    Conjugation is essential for complex inner-product spaces because it
    makes <x, x> real and non-negative.
    """
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimension.")
    return sum(x.conjugate() * y for x, y in zip(a, b))


def norm(vector: Sequence[complex]) -> float:
    """Norm induced by the inner product: ||x|| = sqrt(<x, x>)."""
    value = inner_product(vector, vector).real

    # Numerical round-off can produce a tiny negative number such as -1e-16.
    if value < 0 and abs(value) < 1e-12:
        value = 0.0

    if value < 0:
        raise ValueError("The computed squared norm is negative.")

    return math.sqrt(value)


def distance(a: Sequence[complex], b: Sequence[complex]) -> float:
    """Metric induced by the Hilbert-space norm."""
    return norm(subtract_vectors(a, b))


def is_orthogonal(a: Sequence[complex], b: Sequence[complex], tol: float = 1e-10) -> bool:
    """Two vectors are orthogonal when their inner product is zero."""
    return abs(inner_product(a, b)) <= tol


def normalize(vector: Sequence[complex], tol: float = 1e-12) -> Vector:
    """Return a unit vector in the same direction."""
    vector_norm = norm(vector)

    if vector_norm <= tol:
        raise ValueError("The zero vector cannot be normalized.")

    return [x / vector_norm for x in vector]


def print_vector(name: str, vector: Sequence[complex]) -> None:
    """Small utility for readable demonstrations."""
    formatted = ", ".join(
        f"{x.real:.6f}" if abs(x.imag) < 1e-12
        else f"{x.real:.6f}{x.imag:+.6f}i"
        for x in vector
    )
    print(f"{name} = [{formatted}]")


def demonstrate_basic_geometry() -> None:
    print("\n" + "=" * 78)
    print("1. BASIC INNER-PRODUCT GEOMETRY")
    print("=" * 78)

    x = [3.0, 4.0]
    y = [4.0, -3.0]

    print_vector("x", x)
    print_vector("y", y)

    print(f"<x, y> = {inner_product(x, y)}")
    print(f"||x|| = {norm(x)}")
    print(f"||y|| = {norm(y)}")
    print(f"distance(x, y) = {distance(x, y)}")
    print(f"x and y orthogonal = {is_orthogonal(x, y)}")

    # Pythagorean theorem is a direct consequence of orthogonality.
    if is_orthogonal(x, y):
        lhs = norm(add_vectors(x, y)) ** 2
        rhs = norm(x) ** 2 + norm(y) ** 2
        print(f"Pythagorean check: {lhs:.6f} = {rhs:.6f}")


# ============================================================================
# 2. AXIOMS AND BASIC INEQUALITIES
# ============================================================================

def verify_inner_product_axioms() -> None:
    """
    Numerically verify representative properties of the standard complex
    inner product.

    Exact mathematical properties:
        conjugate symmetry:
            <x, y> = conjugate(<y, x>)

        linearity in the second argument under this convention:
            <x, a*y + b*z> = a<x,y> + b<x,z>

        positive definiteness:
            <x,x> >= 0
            <x,x> = 0 iff x = 0
    """
    print("\n" + "=" * 78)
    print("2. INNER-PRODUCT AXIOMS AND INEQUALITIES")
    print("=" * 78)

    x = [1 + 2j, 2 - 1j, 3 + 0j]
    y = [2 - 1j, -1 + 4j, 1 + 2j]
    z = [3 + 2j, 1 - 3j, -2 + 1j]

    alpha = 2 - 3j
    beta = -1 + 0.5j

    conjugate_symmetry = inner_product(x, y) == inner_product(y, x).conjugate()

    lhs = inner_product(x, add_vectors(scale_vector(alpha, y), scale_vector(beta, z)))
    rhs = alpha * inner_product(x, y) + beta * inner_product(x, z)
    linearity = abs(lhs - rhs) < 1e-10

    positive = inner_product(x, x).real >= 0

    print(f"Conjugate symmetry: {conjugate_symmetry}")
    print(f"Linearity: {linearity}")
    print(f"Positive semidefiniteness check: {positive}")
    print(f"<x,x> = {inner_product(x, x)}")

    # Cauchy-Schwarz:
    #     |<x,y>| <= ||x|| ||y||
    cs_left = abs(inner_product(x, y))
    cs_right = norm(x) * norm(y)
    print(f"Cauchy-Schwarz: {cs_left:.12f} <= {cs_right:.12f}")

    # Triangle inequality:
    #     ||x+y|| <= ||x|| + ||y||
    triangle_left = norm(add_vectors(x, y))
    triangle_right = norm(x) + norm(y)
    print(f"Triangle inequality: {triangle_left:.12f} <= {triangle_right:.12f}")

    # A common mistake is to treat an arbitrary dot-like expression as an
    # inner product without checking positive definiteness.
    def invalid_bilinear_form(a: Sequence[float], b: Sequence[float]) -> float:
        return a[0] * b[0] - a[1] * b[1]

    candidate = [0.0, 1.0]
    print(
        "Example of a non-inner-product form:",
        invalid_bilinear_form(candidate, candidate),
        "(negative values violate positive definiteness)",
    )


# ============================================================================
# 3. SUBSPACES, SPANS, BASIS, AND ORTHONORMALITY
# ============================================================================

def linear_combination(coefficients: Sequence[complex],
                        vectors: Sequence[Sequence[complex]]) -> Vector:
    """Compute sum_i coefficient_i * vector_i."""
    if len(coefficients) != len(vectors):
        raise ValueError("Coefficient and vector counts must match.")

    if not vectors:
        return []

    result = [0j] * len(vectors[0])

    for coefficient, vector in zip(coefficients, vectors):
        if len(vector) != len(result):
            raise ValueError("All vectors must have the same dimension.")
        result = add_vectors(result, scale_vector(coefficient, vector))

    return result


def gram_schmidt(vectors: Sequence[Sequence[complex]],
                  tol: float = 1e-12) -> list[Vector]:
    """
    Classical Gram-Schmidt orthonormalization.

    Given linearly independent vectors v_1,...,v_n, construct orthonormal
    vectors q_1,...,q_n spanning the same subspace.

    At each stage:
        u_k = v_k - sum_j <q_j, v_k> q_j
        q_k = u_k / ||u_k||

    Nearly dependent vectors are rejected because their residual norm falls
    below the tolerance.
    """
    orthonormal_basis: list[Vector] = []

    for vector in vectors:
        residual = list(vector)

        for basis_vector in orthonormal_basis:
            coefficient = inner_product(basis_vector, vector)
            residual = subtract_vectors(
                residual,
                scale_vector(coefficient, basis_vector),
            )

        residual_norm = norm(residual)

        if residual_norm <= tol:
            raise ValueError(
                "Input vectors are linearly dependent or numerically "
                "too close to dependent."
            )

        orthonormal_basis.append(
            [value / residual_norm for value in residual]
        )

    return orthonormal_basis


def demonstrate_basis_and_orthogonality() -> None:
    print("\n" + "=" * 78)
    print("3. BASIS, SPAN, AND ORTHONORMALIZATION")
    print("=" * 78)

    vectors = [
        [1.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    basis = gram_schmidt(vectors)

    for index, vector in enumerate(basis, start=1):
        print_vector(f"q{index}", vector)

    print("\nInner-product matrix of the resulting basis:")
    for q in basis:
        print([round(inner_product(q, p).real, 10) for p in basis])

    # An orthonormal basis has Gram matrix equal to the identity.
    print("\nThe diagonal should be approximately 1 and off-diagonal values 0.")


# ============================================================================
# 4. ORTHOGONAL PROJECTION
# ============================================================================

def project_onto_orthonormal_basis(
    vector: Sequence[complex],
    basis: Sequence[Sequence[complex]],
) -> Vector:
    """
    Orthogonal projection onto span(basis), assuming basis is orthonormal.

        P_M x = sum_i <q_i, x> q_i
    """
    if not basis:
        return [0j] * len(vector)

    projection = [0j] * len(vector)

    for q in basis:
        coefficient = inner_product(q, vector)
        projection = add_vectors(
            projection,
            scale_vector(coefficient, q),
        )

    return projection


def project_onto_subspace(
    vector: Sequence[complex],
    spanning_vectors: Sequence[Sequence[complex]],
) -> tuple[Vector, list[Vector]]:
    """
    Build an orthonormal basis and then perform orthogonal projection.
    """
    basis = gram_schmidt(spanning_vectors)
    return project_onto_orthonormal_basis(vector, basis), basis


def demonstrate_projection() -> None:
    print("\n" + "=" * 78)
    print("4. ORTHOGONAL PROJECTION AND BEST APPROXIMATION")
    print("=" * 78)

    target = [3.0, 1.0, 4.0]
    subspace_generators = [
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    projection, basis = project_onto_subspace(target, subspace_generators)
    residual = subtract_vectors(target, projection)

    print_vector("target", target)
    print_vector("projection", projection)
    print_vector("residual", residual)
    print(f"||target|| = {norm(target):.6f}")
    print(f"||projection|| = {norm(projection):.6f}")
    print(f"||residual|| = {norm(residual):.6f}")

    # The residual must be orthogonal to every vector in the subspace.
    for index, q in enumerate(basis, start=1):
        print(f"<q{index}, residual> = {inner_product(q, residual):.12f}")

    # Pythagorean decomposition:
    print(
        "Squared-norm decomposition:",
        f"{norm(target) ** 2:.10f} ≈ "
        f"{norm(projection) ** 2 + norm(residual) ** 2:.10f}",
    )

    # Projection theorem:
    # The projection is the unique element of a closed subspace closest to x.
    alternative = add_vectors(
        projection,
        scale_vector(2.0, basis[0]),
    )
    print(f"||target - projection|| = {distance(target, projection):.6f}")
    print(f"||target - another point|| = {distance(target, alternative):.6f}")


# ============================================================================
# 5. HILBERT SPACE AS A COMPLETE INNER-PRODUCT SPACE
# ============================================================================

@dataclass
class SequenceApproximation:
    """
    A finite approximation to an infinite sequence.

    Infinite-dimensional Hilbert spaces cannot be represented exactly by an
    ordinary finite Python list. This class models finite prefixes so that
    convergence can be studied numerically.
    """
    values: list[float]

    def norm(self) -> float:
        return math.sqrt(sum(value * value for value in self.values))

    def distance_to(self, other: "SequenceApproximation") -> float:
        if len(self.values) != len(other.values):
            raise ValueError("Approximations must have equal lengths.")
        return math.sqrt(
            sum(
                (a - b) ** 2
                for a, b in zip(self.values, other.values)
            )
        )


def demonstrate_completeness_concept() -> None:
    print("\n" + "=" * 78)
    print("5. COMPLETENESS AND CAUCHY SEQUENCES")
    print("=" * 78)

    print(
        """
A sequence (x_n) in a metric space is Cauchy when, for every epsilon > 0,
there exists N such that ||x_n - x_m|| < epsilon whenever n,m >= N.

Completeness means every Cauchy sequence converges to an element of the
same space.

A Hilbert space is therefore:

    inner product space + completeness under the induced norm.
"""
    )

    # Example:
    # x_n = [1, 1/2, 1/3, ..., 1/n] as finite approximations.
    # This sequence converges in l^2 because the limiting sequence
    # [1, 1/2, 1/3, ...] has finite squared norm:
    #
    #     sum_{k=1}^\infty 1/k^2 = pi^2/6.
    #
    # We approximate that limiting norm using finite prefixes.
    for n in [10, 100, 1000, 10000]:
        approximation = SequenceApproximation(
            [1.0 / k for k in range(1, n + 1)]
        )
        print(
            f"n={n:5d}, prefix l2 norm={approximation.norm():.10f}"
        )

    print(f"Expected limiting norm ≈ {math.pi / math.sqrt(6):.10f}")

    print(
        """
Why completeness matters:
A vector-space structure alone does not guarantee that limits of Cauchy
sequences remain inside the space. Completion adds the missing limit points.

For example, the rational numbers Q with the usual absolute-value metric
form an inner-product-like normed setting but are not complete. Their
completion is R.

For Hilbert spaces, completeness is with respect to the norm induced by
the inner product.
"""
    )


# ============================================================================
# 6. FUNCTION SPACES: L2 AS A NUMERICAL APPROXIMATION
# ============================================================================

def trapezoidal_inner_product(
    f: Callable[[float], complex],
    g: Callable[[float], complex],
    left: float,
    right: float,
    samples: int = 10001,
) -> complex:
    """
    Numerically approximate the L2 inner product

        <f,g> = integral_left^right conjugate(f(x)) g(x) dx

    using the composite trapezoidal rule.
    """
    if samples < 2:
        raise ValueError("At least two samples are required.")

    step = (right - left) / (samples - 1)
    total = 0j

    for i in range(samples):
        x = left + i * step
        weight = 0.5 if i in (0, samples - 1) else 1.0
        total += weight * f(x).conjugate() * g(x)

    return total * step


def function_norm(
    f: Callable[[float], complex],
    left: float,
    right: float,
    samples: int = 10001,
) -> float:
    """Numerical L2 norm."""
    value = trapezoidal_inner_product(
        f, f, left, right, samples
    ).real

    return math.sqrt(max(value, 0.0))


def demonstrate_function_space() -> None:
    print("\n" + "=" * 78)
    print("6. FUNCTION SPACES AND L2")
    print("=" * 78)

    # L2([0, pi]) is the set of measurable functions whose squared absolute
    # value has finite integral:
    #
    #     integral |f(x)|^2 dx < infinity.
    #
    # The inner product is:
    #
    #     <f,g> = integral conjugate(f(x)) g(x) dx.
    #
    # This implementation uses numerical integration rather than representing
    # functions as finite vectors.
    f = lambda x: math.sin(x)
    g = lambda x: math.cos(x)
    h = lambda x: math.sin(x) + math.cos(x)

    fg = trapezoidal_inner_product(f, g, 0, math.pi)
    ff = function_norm(f, 0, math.pi)
    gg = function_norm(g, 0, math.pi)
    hh = function_norm(h, 0, math.pi)

    print(f"<sin, cos> on [0, pi] ≈ {fg.real:.12e}")
    print(f"||sin||_2 on [0, pi] ≈ {ff:.10f}")
    print(f"||cos||_2 on [0, pi] ≈ {gg:.10f}")
    print(f"||sin + cos||_2 on [0, pi] ≈ {hh:.10f}")

    print(
        """
The sine and cosine functions are orthogonal on [0, pi] under this
inner product because their product integrates to zero.

Function-space Hilbert spaces are fundamental in Fourier analysis, signal
processing, quantum mechanics, partial differential equations, statistics,
optimization, and approximation theory.
"""
    )


# ============================================================================
# 7. FOURIER-LIKE ORTHONORMAL EXPANSION
# ============================================================================

def sine_basis(index: int, x: float, interval_length: float) -> float:
    """
    Normalized sine basis on [0, L]:

        q_n(x) = sqrt(2/L) sin(n*pi*x/L)
    """
    return math.sqrt(2.0 / interval_length) * math.sin(
        index * math.pi * x / interval_length
    )


def project_function_onto_sine_basis(
    function: Callable[[float], float],
    interval_length: float,
    basis_count: int,
    samples: int = 5001,
) -> list[float]:
    """
    Compute coefficients:
        c_n = <q_n, f>
    for a normalized sine basis.
    """
    coefficients = []

    for n in range(1, basis_count + 1):
        basis_function = lambda x, n=n: sine_basis(
            n, x, interval_length
        )

        coefficient = trapezoidal_inner_product(
            basis_function,
            function,
            0.0,
            interval_length,
            samples,
        )

        coefficients.append(coefficient.real)

    return coefficients


def reconstruct_from_sine_basis(
    x: float,
    interval_length: float,
    coefficients: Sequence[float],
) -> float:
    """Reconstruct a function from a finite orthonormal expansion."""
    return sum(
        coefficient * sine_basis(
            n,
            x,
            interval_length,
        )
        for n, coefficient in enumerate(coefficients, start=1)
    )


def demonstrate_fourier_projection() -> None:
    print("\n" + "=" * 78)
    print("7. ORTHONORMAL FUNCTION EXPANSIONS")
    print("=" * 78)

    L = math.pi

    # f(x)=x on [0,pi]. It does not consist of only one sine basis function,
    # so finite projection produces an approximation.
    target_function = lambda x: x

    coefficients = project_function_onto_sine_basis(
        target_function,
        L,
        basis_count=8,
    )

    print("First eight sine-basis coefficients for f(x)=x:")
    for index, coefficient in enumerate(coefficients, start=1):
        print(f"c_{index} = {coefficient:.10f}")

    test_points = [0.25, 0.75, 1.5, 2.25, 3.0]

    print("\nFinite-basis reconstruction:")
    for x in test_points:
        approximation = reconstruct_from_sine_basis(
            x,
            L,
            coefficients,
        )
        print(
            f"x={x:.2f}, target={x:.8f}, "
            f"approximation={approximation:.8f}"
        )


# ============================================================================
# 8. RIESZ REPRESENTATION IDEA IN FINITE DIMENSIONS
# ============================================================================

def linear_functional(vector: Sequence[float],
                      coefficients: Sequence[float]) -> float:
    """
    A continuous linear functional in R^n can be represented as

        F(x) = <a, x>

    for a unique vector a.

    This is the finite-dimensional form of the Riesz representation theorem.
    """
    if len(vector) != len(coefficients):
        raise ValueError("Dimensions must match.")
    return float(inner_product(coefficients, vector).real)


def demonstrate_riesz_representation() -> None:
    print("\n" + "=" * 78)
    print("8. RIESZ REPRESENTATION IN FINITE DIMENSIONS")
    print("=" * 78)

    representing_vector = [2.0, -1.0, 3.0]

    for vector in ([1.0, 2.0, 0.0], [0.0, -2.0, 1.0]):
        functional_value = linear_functional(
            vector,
            representing_vector,
        )
        inner_product_value = inner_product(
            representing_vector,
            vector,
        ).real

        print_vector("x", vector)
        print(f"F(x) = {functional_value:.6f}")
        print(f"<a,x> = {inner_product_value:.6f}")

    print(
        """
The Riesz representation theorem states that for every continuous linear
functional F on a Hilbert space H, there exists a unique vector y in H such
that

    F(x) = <y,x>

for every x in H.

This is one reason Hilbert spaces are particularly powerful: geometry and
continuous linear functionals can be expressed through the same inner
product structure.
"""
    )


# ============================================================================
# 9. LEAST SQUARES AS ORTHOGONAL PROJECTION
# ============================================================================

def solve_least_squares(
    matrix_columns: Sequence[Sequence[float]],
    target: Sequence[float],
) -> tuple[Vector, Vector, list[Vector]]:
    """
    Solve the least-squares approximation using QR-like orthonormalization.

    Given columns a_1,...,a_k, find coefficients c minimizing

        ||A c - b||.

    If q_i is an orthonormal basis for the column space of A, then

        projection(b) = sum_i <q_i,b> q_i.

    We then recover coefficients by back-substitution against the
    Gram-Schmidt vectors. For clarity and numerical stability, the example
    computes coefficients using the original independent columns through
    the orthonormal basis transformation.
    """
    q_basis = gram_schmidt(matrix_columns)

    projection = project_onto_orthonormal_basis(
        target,
        q_basis,
    )

    # Build R where R_ij = <q_i, a_j>.
    # Since q_i and a_j have the same span:
    #
    #     A = Q R
    #
    # and Q^T b gives the least-squares transformed right side.
    k = len(matrix_columns)
    R = [
        [
            inner_product(q_basis[i], matrix_columns[j]).real
            for j in range(k)
        ]
        for i in range(k)
    ]

    transformed_target = [
        inner_product(q, target).real
        for q in q_basis
    ]

    coefficients = [0.0] * k

    # R is upper triangular under Gram-Schmidt.
    for i in range(k - 1, -1, -1):
        remainder = transformed_target[i]

        for j in range(i + 1, k):
            remainder -= R[i][j] * coefficients[j]

        if abs(R[i][i]) < 1e-12:
            raise ValueError("Singular or nearly singular system.")

        coefficients[i] = remainder / R[i][i]

    return coefficients, projection, q_basis


def demonstrate_least_squares() -> None:
    print("\n" + "=" * 78)
    print("9. LEAST SQUARES AND PROJECTION")
    print("=" * 78)

    # Fit y ≈ c0 + c1*x using vectors representing the columns of the
    # design matrix.
    x_values = [0.0, 1.0, 2.0, 3.0, 4.0]
    y_values = [1.2, 2.9, 5.1, 6.8, 9.2]

    intercept_column = [1.0] * len(x_values)
    slope_column = x_values

    coefficients, projection, _ = solve_least_squares(
        [intercept_column, slope_column],
        y_values,
    )

    intercept, slope = coefficients

    print(f"Estimated intercept = {intercept:.6f}")
    print(f"Estimated slope = {slope:.6f}")

    print("\nObserved versus fitted:")
    for x, observed, fitted in zip(
        x_values,
        y_values,
        projection,
    ):
        print(
            f"x={x:.1f}, observed={observed:.4f}, "
            f"fitted={fitted.real:.4f}, residual={observed-fitted.real:.4f}"
        )

    print(f"Residual norm = {distance(y_values, projection):.10f}")


# ============================================================================
# 10. PARALLEL AND ORTHOGONAL COMPONENTS
# ============================================================================

def decompose_relative_to_vector(
    vector: Sequence[complex],
    direction: Sequence[complex],
) -> tuple[Vector, Vector]:
    """
    Decompose vector as

        x = x_parallel + x_perpendicular

    where x_parallel lies in span(direction).
    """
    denominator = inner_product(direction, direction)

    if abs(denominator) <= 1e-12:
        raise ValueError("Direction must be non-zero.")

    coefficient = inner_product(direction, vector) / denominator

    parallel = scale_vector(coefficient, direction)
    perpendicular = subtract_vectors(vector, parallel)

    return parallel, perpendicular


def demonstrate_decomposition() -> None:
    print("\n" + "=" * 78)
    print("10. PARALLEL AND ORTHOGONAL COMPONENTS")
    print("=" * 78)

    vector = [5.0, 2.0]
    direction = [1.0, 1.0]

    parallel, perpendicular = decompose_relative_to_vector(
        vector,
        direction,
    )

    print_vector("x_parallel", parallel)
    print_vector("x_perpendicular", perpendicular)

    print(
        "Orthogonality:",
        inner_product(parallel, perpendicular),
    )

    reconstructed = add_vectors(parallel, perpendicular)
    print_vector("reconstructed x", reconstructed)


# ============================================================================
# 11. CLOSED SUBSPACES AND WHY CLOSURE MATTERS
# ============================================================================

def demonstrate_closed_subspace_idea() -> None:
    print("\n" + "=" * 78)
    print("11. CLOSED SUBSPACES")
    print("=" * 78)

    print(
        """
In a Hilbert space, orthogonal projection onto a closed subspace M exists
and is unique.

Closedness is important. A subspace may contain all finite linear
combinations of a collection of vectors but fail to contain limits of those
combinations.

The closure of M, written closure(M), contains all limits of convergent
sequences from M.

Important distinction:

    algebraic span:
        finite linear combinations only

    closed linear span:
        limits of convergent combinations are included

In Hilbert-space analysis, the closed span often represents the actual
approximation space used by projection and expansion theorems.
"""
    )

    # A simple finite-dimensional illustration: every linear subspace of
    # finite-dimensional Euclidean space is closed.
    basis = gram_schmidt([[1.0, 2.0, 3.0], [2.0, -1.0, 1.0]])

    print("Finite-dimensional subspaces are automatically closed.")
    print("Constructed orthonormal basis dimension:", len(basis))


# ============================================================================
# 12. PARSEVAL'S IDENTITY IN FINITE ORTHONORMAL COORDINATES
# ============================================================================

def demonstrate_parseval() -> None:
    print("\n" + "=" * 78)
    print("12. PARSEVAL'S IDENTITY")
    print("=" * 78)

    # In a complete orthonormal basis:
    #
    #     ||x||^2 = sum_i |<q_i,x>|^2
    #
    # In a finite-dimensional space this is exact when the basis is complete.
    basis = gram_schmidt([
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 1.0],
        [1.0, 1.0, 0.0],
    ])

    x = [2.0, -1.0, 4.0]

    coefficients = [
        inner_product(q, x)
        for q in basis
    ]

    left = norm(x) ** 2
    right = sum(abs(c) ** 2 for c in coefficients)

    print_vector("x", x)
    print("Coordinates in orthonormal basis:")
    for i, coefficient in enumerate(coefficients, start=1):
        print(f"c{i} = {coefficient}")

    print(f"||x||² = {left:.12f}")
    print(f"sum |ci|² = {right:.12f}")


# ============================================================================
# 13. BESSel's INEQUALITY
# ============================================================================

def demonstrate_bessel_inequality() -> None:
    print("\n" + "=" * 78)
    print("13. BESSEL'S INEQUALITY")
    print("=" * 78)

    basis = gram_schmidt([
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 1.0],
    ])

    x = [4.0, 2.0, 5.0]

    coefficient_energy = sum(
        abs(inner_product(q, x)) ** 2
        for q in basis
    )

    total_energy = norm(x) ** 2

    print(f"sum |<q_i,x>|² = {coefficient_energy:.10f}")
    print(f"||x||² = {total_energy:.10f}")
    print("Bessel inequality holds:", coefficient_energy <= total_energy + 1e-10)

    print(
        """
Bessel's inequality says that for any orthonormal set {q_i},

    sum_i |<q_i,x>|² <= ||x||².

Equality holds when the orthonormal set is complete for the relevant
space, producing Parseval's identity.
"""
    )


# ============================================================================
# 14. RAYLEIGH QUOTIENT AND SELF-ADJOINT MATRICES
# ============================================================================

def matrix_vector_multiply(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
) -> list[float]:
    """Multiply a real matrix by a vector."""
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("Matrix dimensions are incompatible.")

    return [
        sum(row[j] * vector[j] for j in range(len(vector)))
        for row in matrix
    ]


def quadratic_form(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
) -> float:
    """Compute x^T A x for real vectors."""
    transformed = matrix_vector_multiply(matrix, vector)
    return sum(x * y for x, y in zip(vector, transformed))


def rayleigh_quotient(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
) -> float:
    """
    R_A(x) = <x, Ax> / <x,x>.

    For self-adjoint matrices, the Rayleigh quotient is real and is closely
    connected to spectral theory.
    """
    denominator = inner_product(vector, vector).real

    if denominator <= 1e-12:
        raise ValueError("Rayleigh quotient requires a non-zero vector.")

    return quadratic_form(matrix, vector) / denominator


def demonstrate_rayleigh_quotient() -> None:
    print("\n" + "=" * 78)
    print("14. RAYLEIGH QUOTIENT AND SELF-ADJOINT OPERATORS")
    print("=" * 78)

    symmetric_matrix = [
        [4.0, 1.0],
        [1.0, 2.0],
    ]

    for vector in ([1.0, 0.0], [0.0, 1.0], [1.0, 1.0]):
        print(
            f"x={vector}, Rayleigh quotient="
            f"{rayleigh_quotient(symmetric_matrix, vector):.6f}"
        )

    print(
        """
A real symmetric matrix represents a self-adjoint operator under the
standard Euclidean inner product.

For a complex Hilbert space, the corresponding condition is

    A = A*

where A* is the conjugate transpose.

Self-adjoint operators are central to Hilbert-space spectral theory.
"""
    )


# ============================================================================
# 15. OPERATOR NORMS AND BOUNDEDNESS
# ============================================================================

def operator_norm_estimate(
    matrix: Sequence[Sequence[float]],
    samples: int = 10000,
) -> float:
    """
    Monte Carlo estimate of the induced 2-norm.

    The exact operator norm is

        ||A|| = sup_{x != 0} ||Ax|| / ||x||.

    This sampling implementation is illustrative, not an exact algorithm.
    """
    if not matrix or not matrix[0]:
        raise ValueError("Matrix cannot be empty.")

    dimension = len(matrix[0])
    best = 0.0

    rng = random.Random(42)

    for _ in range(samples):
        vector = [
            rng.gauss(0.0, 1.0)
            for _ in range(dimension)
        ]

        vector_norm = norm(vector)
        if vector_norm <= 1e-15:
            continue

        transformed = matrix_vector_multiply(matrix, vector)
        ratio = norm(transformed) / vector_norm
        best = max(best, ratio)

    return best


def demonstrate_operator_norm() -> None:
    print("\n" + "=" * 78)
    print("15. BOUNDED LINEAR OPERATORS")
    print("=" * 78)

    matrix = [
        [3.0, 0.0],
        [0.0, 1.0],
    ]

    estimate = operator_norm_estimate(matrix)

    print(f"Estimated ||A||_2 ≈ {estimate:.6f}")
    print("For this diagonal matrix, the exact operator norm is 3.")

    print(
        """
A linear operator T between normed spaces is bounded when there exists C
such that

    ||Tx|| <= C ||x||

for every x.

For linear operators, boundedness is equivalent to continuity.

Hilbert-space theory often studies bounded operators, adjoints, projections,
compact operators, unitary operators, and self-adjoint operators.
"""
    )


# ============================================================================
# 16. COMPLEX HILBERT-SPACE GEOMETRY
# ============================================================================

def demonstrate_complex_geometry() -> None:
    print("\n" + "=" * 78)
    print("16. COMPLEX HILBERT-SPACE GEOMETRY")
    print("=" * 78)

    x = [1 + 2j, 2 - 1j]
    y = [3 - 1j, -1 + 4j]

    print_vector("x", x)
    print_vector("y", y)

    print(f"<x,y> = {inner_product(x, y)}")
    print(f"<y,x> = {inner_product(y, x)}")
    print(f"conjugate(<y,x>) = {inner_product(y, x).conjugate()}")

    print(
        """
For complex spaces, the inner product is not generally a real number.
Angles therefore require care. The norm remains real because

    ||x||² = <x,x>.

The conjugation rule is what makes the geometry positive definite.
"""
    )


# ============================================================================
# 17. EDGE CASES AND NUMERICAL PITFALLS
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("17. EDGE CASES AND NUMERICAL PITFALLS")
    print("=" * 78)

    zero = [0.0, 0.0, 0.0]

    try:
        normalize(zero)
    except ValueError as error:
        print("Zero normalization rejected:", error)

    try:
        gram_schmidt([
            [1.0, 2.0],
            [2.0, 4.0],
        ])
    except ValueError as error:
        print("Dependent vectors rejected:", error)

    nearly_dependent = [
        [1.0, 1.0],
        [1.0, 1.0 + 1e-14],
    ]

    try:
        gram_schmidt(nearly_dependent)
    except ValueError as error:
        print("Nearly dependent vectors rejected:", error)

    print(
        """
Important numerical issues:

1. Floating-point zero is approximate.
2. Nearly linearly dependent vectors can make Gram-Schmidt unstable.
3. Classical Gram-Schmidt can lose orthogonality for ill-conditioned data.
4. Modified Gram-Schmidt or Householder QR is generally preferable for
   demanding numerical linear algebra.
5. Infinite-dimensional mathematical statements cannot be established merely
   by testing a finite number of samples.
"""
    )


# ============================================================================
# 18. COMPARISON OF RELATED STRUCTURES
# ============================================================================

def explain_related_structures() -> None:
    print("\n" + "=" * 78)
    print("18. RELATED MATHEMATICAL STRUCTURES")
    print("=" * 78)

    print(
        """
Vector space
    Provides vector addition and scalar multiplication.

Normed vector space
    Adds a norm ||x|| measuring size.

Inner-product space
    Adds <x,y>, which induces a norm through ||x||=sqrt(<x,x>).

Banach space
    A complete normed vector space.

Hilbert space
    A complete inner-product space.

Every Hilbert space is a Banach space because its inner product induces a
norm. Not every Banach space is a Hilbert space because not every norm comes
from an inner product.

The parallelogram identity characterizes norms induced by inner products:

    ||x+y||² + ||x-y||²
        = 2||x||² + 2||y||².

For arbitrary norms this identity need not hold.
"""
    )

    x = [2.0, 3.0]
    y = [-1.0, 4.0]

    lhs = norm(add_vectors(x, y)) ** 2 + norm(subtract_vectors(x, y)) ** 2
    rhs = 2 * norm(x) ** 2 + 2 * norm(y) ** 2

    print(f"Parallelogram identity LHS = {lhs:.10f}")
    print(f"Parallelogram identity RHS = {rhs:.10f}")


# ============================================================================
# 19. PRACTICAL SIGNAL-APPROXIMATION EXAMPLE
# ============================================================================

def generate_noisy_signal(
    samples: int,
    noise_amplitude: float,
) -> tuple[list[float], list[float]]:
    """
    Generate a signal composed of low-frequency components plus deterministic
    pseudo-random noise.
    """
    rng = random.Random(7)

    clean = []
    noisy = []

    for i in range(samples):
        t = i / samples
        clean_value = (
            1.5 * math.sin(2 * math.pi * t)
            + 0.5 * math.cos(4 * math.pi * t)
        )
        noisy_value = clean_value + rng.uniform(
            -noise_amplitude,
            noise_amplitude,
        )

        clean.append(clean_value)
        noisy.append(noisy_value)

    return clean, noisy


def moving_average(signal: Sequence[float], window: int) -> list[float]:
    """Simple finite-dimensional smoothing operation."""
    if window <= 0:
        raise ValueError("Window must be positive.")

    result = []

    for index in range(len(signal)):
        start = max(0, index - window + 1)
        section = signal[start:index + 1]
        result.append(sum(section) / len(section))

    return result


def demonstrate_signal_application() -> None:
    print("\n" + "=" * 78)
    print("19. PRACTICAL SIGNAL-APPROXIMATION APPLICATION")
    print("=" * 78)

    clean, noisy = generate_noisy_signal(
        samples=100,
        noise_amplitude=0.35,
    )

    filtered = moving_average(noisy, window=5)

    clean_error = math.sqrt(
        sum((a - b) ** 2 for a, b in zip(clean, noisy))
        / len(clean)
    )

    filtered_error = math.sqrt(
        sum((a - b) ** 2 for a, b in zip(clean, filtered))
        / len(clean)
    )

    print(f"RMS error of noisy signal:    {clean_error:.6f}")
    print(f"RMS error after smoothing:    {filtered_error:.6f}")

    print(
        """
Signal-processing systems often model signals as vectors in an inner-product
space. Orthogonality separates independent components, projections perform
best approximation, and orthonormal expansions provide efficient
representations.

A finite digital signal is mathematically a vector. A continuous-time signal
may instead be modeled as an element of a function Hilbert space such as
L2.
"""
    )


# ============================================================================
# 20. ADVANCED CONCEPTS
# ============================================================================

def explain_advanced_topics() -> None:
    print("\n" + "=" * 78)
    print("20. ADVANCED HILBERT-SPACE CONCEPTS")
    print("=" * 78)

    print(
        """
Adjoint operator
    For a bounded operator T, its adjoint T* satisfies

        <Tx, y> = <x, T*y>.

Self-adjoint operator
    T = T*.

Unitary operator
    T preserves inner products:

        <Tx, Ty> = <x, y>.

    Consequently ||Tx|| = ||x||.

Orthogonal projection
    P satisfies

        P² = P
        P* = P.

Orthogonal complement
    For M subset H,

        M^perp = {x in H : <x,m> = 0 for every m in M}.

Direct orthogonal decomposition
    Under appropriate closedness conditions,

        H = M + M^perp.

Spectral theory
    Studies operators through their spectra. For self-adjoint operators,
    spectral structure generalizes diagonalization of symmetric matrices.

Compact operators
    Map bounded sets into relatively compact sets. They play an important
    role in infinite-dimensional spectral theory.

Weak convergence
    x_n converges weakly to x if

        <x_n,y> -> <x,y>

    for every y in H.

Strong convergence
    x_n converges strongly when

        ||x_n-x|| -> 0.

    Strong convergence implies weak convergence, but the converse need not
    hold in infinite-dimensional spaces.

Separable Hilbert space
    Contains a countable dense subset. A separable Hilbert space admits a
    countable orthonormal basis.

Tensor-product Hilbert spaces
    Provide mathematical structure for composite systems and are important
    in quantum mechanics, signal processing, and operator theory.
"""
    )


# ============================================================================
# 21. COMMON MISTAKES
# ============================================================================

def explain_common_mistakes() -> None:
    print("\n" + "=" * 78)
    print("21. COMMON MISTAKES")
    print("=" * 78)

    mistakes = [
        (
            "Confusing a norm with an inner product",
            "A norm measures size; an inner product also provides angles and orthogonality."
        ),
        (
            "Ignoring completeness",
            "A Hilbert space must be complete under the induced norm."
        ),
        (
            "Forgetting complex conjugation",
            "Complex inner products require conjugation in one argument."
        ),
        (
            "Assuming every norm comes from an inner product",
            "The parallelogram identity is required."
        ),
        (
            "Using a non-closed subspace for a projection theorem",
            "Orthogonal projection onto a general subspace may fail to exist."
        ),
        (
            "Treating numerical equality as exact mathematical equality",
            "Floating-point calculations require tolerances."
        ),
        (
            "Assuming finite-dimensional intuition always transfers directly",
            "Infinite-dimensional spaces have important distinctions involving closure, compactness, and weak convergence."
        ),
    ]

    for mistake, explanation in mistakes:
        print(f"- {mistake}: {explanation}")


# ============================================================================
# 22. MINI TEST SUITE
# ============================================================================

def assert_close(a: float, b: float, tolerance: float = 1e-9) -> None:
    if abs(a - b) > tolerance:
        raise AssertionError(f"{a} is not close to {b}")


def run_tests() -> None:
    print("\n" + "=" * 78)
    print("22. SELF-TESTS")
    print("=" * 78)

    assert_close(norm([3.0, 4.0]), 5.0)

    assert is_orthogonal([1.0, 0.0], [0.0, 1.0])

    normalized = normalize([3.0, 4.0])
    assert_close(norm(normalized), 1.0)

    basis = gram_schmidt([
        [1.0, 1.0],
        [1.0, -1.0],
    ])

    assert_close(abs(inner_product(basis[0], basis[1]).real), 0.0)

    projection, _ = project_onto_subspace(
        [3.0, 4.0],
        [[1.0, 0.0]],
    )

    assert_close(projection[0].real, 3.0)
    assert_close(projection[1].real, 0.0)

    print("All self-tests passed.")


# ============================================================================
# 23. MAIN PROGRAM
# ============================================================================

def main() -> None:
    print("=" * 78)
    print("HILBERT SPACES: FROM INNER-PRODUCT GEOMETRY TO FUNCTION SPACES")
    print("=" * 78)

    demonstrate_basic_geometry()
    verify_inner_product_axioms()
    demonstrate_basis_and_orthogonality()
    demonstrate_projection()
    demonstrate_completeness_concept()
    demonstrate_function_space()
    demonstrate_fourier_projection()
    demonstrate_riesz_representation()
    demonstrate_least_squares()
    demonstrate_decomposition()
    demonstrate_closed_subspace_idea()
    demonstrate_parseval()
    demonstrate_bessel_inequality()
    demonstrate_rayleigh_quotient()
    demonstrate_operator_norm()
    demonstrate_complex_geometry()
    demonstrate_edge_cases()
    explain_related_structures()
    demonstrate_signal_application()
    explain_advanced_topics()
    explain_common_mistakes()
    run_tests()

    print("\n" + "=" * 78)
    print("END OF HILBERT SPACE STUDY PROGRAM")
    print("=" * 78)


if __name__ == "__main__":
    main()
