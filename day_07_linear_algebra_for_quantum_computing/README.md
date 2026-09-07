# Linear Algebra for Quantum Computing: Vector Spaces and Inner Products

## 1. Topic Introduction

Linear algebra provides the mathematical language used to represent quantum states, quantum operations, measurement, superposition, interference, and entanglement.

Quantum computing is built largely on finite-dimensional complex vector spaces. A single qubit is represented by a unit vector in the two-dimensional complex vector space

C².

An n-qubit pure state is represented by a unit vector in

C^(2ⁿ).

The Python script accompanying this README develops the required linear-algebra concepts progressively. It begins with scalars and vectors, proceeds through vector spaces, linear combinations, basis, dimension, inner products, norms, orthogonality, projections, and orthonormal bases, and then connects these concepts directly to quantum states and operators.

The implementation uses only the Python standard library and represents vectors and matrices with ordinary Python lists.

---

## 2. Scalars and Fields

A scalar is a quantity that can multiply a vector.

The two scalar fields most relevant to introductory linear algebra are:

- The real numbers, R
- The complex numbers, C

Quantum computing uses complex amplitudes, so the complex field is fundamental.

A complex number has the form

z = a + bi

where:

- a is the real part
- b is the imaginary part
- i is the imaginary unit satisfying i² = -1

The script represents complex values using Python's `complex` type.

For example, a quantum amplitude can be represented by values such as:

1 / sqrt(2)

or

(1 + i) / 2.

Complex numbers are essential because quantum amplitudes can contain both magnitude and phase.

---

## 3. Vectors

A vector is an ordered collection of scalars.

A vector in C² can be written as

|v> = [a, b]ᵀ

where a and b are complex numbers.

In quantum notation, the vertical notation is called ket notation.

The script represents a vector as a Python list:

`[a, b]`

Vectors support several fundamental operations.

### Vector addition

For

u = [u₁, u₂, ..., uₙ]

and

v = [v₁, v₂, ..., vₙ],

their sum is

u + v = [u₁ + v₁, u₂ + v₂, ..., uₙ + vₙ].

### Scalar multiplication

For a scalar c,

c u = [c u₁, c u₂, ..., c uₙ].

The functions `vector_add`, `vector_subtract`, and `scalar_multiply` implement these operations.

---

## 4. Vector Spaces

A vector space is a set of objects called vectors together with two operations:

1. Vector addition
2. Scalar multiplication

The vectors and scalars must satisfy a collection of algebraic axioms.

Important properties include:

- Closure under vector addition
- Closure under scalar multiplication
- Associativity of vector addition
- Commutativity of vector addition
- Existence of an additive identity
- Existence of additive inverses
- Compatibility of scalar multiplication
- Distributivity of scalar multiplication

The script demonstrates these properties computationally.

### Additive identity

There must be a zero vector such that

v + 0 = v.

For C²:

0 = [0, 0].

### Additive inverse

Every vector must have an inverse:

v + (-v) = 0.

### Scalar compatibility

For scalars a and b,

(ab)v = a(bv).

These properties distinguish vector-space operations from arbitrary collections of data.

---

## 5. Examples of Vector Spaces

Vector spaces are more general than ordinary geometric arrows.

Examples include:

- Rⁿ
- Cⁿ
- Polynomials of bounded degree
- Matrices of a fixed size
- Functions satisfying appropriate closure properties
- Quantum state-vector spaces

The script includes polynomials as an example of an abstract vector space.

A polynomial can be represented by its coefficient vector. For example,

p(x) = 1 + 2x + x²

can be represented as

[1, 2, 1].

Polynomial addition and scalar multiplication obey the vector-space rules.

This illustrates that a vector does not have to represent a physical arrow in space.

---

## 6. Subspaces

A subspace is a subset of a vector space that is itself a vector space under the same operations.

A nonempty subset W of V is a subspace when it is closed under:

- Vector addition
- Scalar multiplication

A particularly useful characterization is:

For every u, v in W and scalars a, b,

au + bv

must also belong to W.

The span of any collection of vectors is a subspace.

The script demonstrates spans and subspace projections.

---

## 7. Linear Combinations

A linear combination of vectors v₁, v₂, ..., vₖ has the form

c₁v₁ + c₂v₂ + ... + cₖvₖ.

The scalars c₁, ..., cₖ are called coefficients.

Linear combinations are central because they describe how vectors are constructed from basis vectors.

Quantum superposition is a physical application of linear combination.

For example,

|ψ> = α|0> + β|1>.

Here α and β are complex coefficients.

---

## 8. Span

The span of vectors v₁, ..., vₖ is the set of every possible linear combination of those vectors:

span{v₁, ..., vₖ}
=
{c₁v₁ + ... + cₖvₖ}.

The span is always a subspace.

If two vectors in C² are linearly independent, their span is the entire C² space.

The script provides a finite coefficient demonstration of span. Since a mathematical span can contain infinitely many vectors, the executable demonstration samples representative coefficients rather than attempting to enumerate an infinite set.

---

## 9. Linear Independence

Vectors v₁, ..., vₖ are linearly independent when

c₁v₁ + ... + cₖvₖ = 0

implies

c₁ = c₂ = ... = cₖ = 0.

If a nontrivial combination produces the zero vector, the vectors are linearly dependent.

The script determines independence using matrix rank.

If the vectors are treated as columns of a matrix A, then they are linearly independent exactly when

rank(A) = number of columns.

Linear independence is important for constructing bases.

---

## 10. Basis

A basis is a set of vectors that is both:

- Linearly independent
- Spanning

A vector can therefore be represented uniquely as a linear combination of basis vectors.

For C², the standard computational basis is

|0> = [1, 0]ᵀ

|1> = [0, 1]ᵀ.

Every single-qubit state can be written as

|ψ> = α|0> + β|1>.

For n qubits, the computational basis contains 2ⁿ vectors.

The script generates computational bases with `computational_basis`.

---

## 11. Dimension

The dimension of a finite-dimensional vector space is the number of vectors in any basis.

Examples:

- dim(R²) = 2
- dim(C²) = 2
- dim(C⁴) = 4
- An n-qubit state space has dimension 2ⁿ

The exponential dimension of multi-qubit state spaces is one of the fundamental mathematical facts underlying quantum computing.

A two-qubit pure state requires four complex amplitudes:

|ψ> =
a|00> +
b|01> +
c|10> +
d|11>.

A three-qubit state requires eight amplitudes.

---

## 12. Coordinates Relative to a Basis

If B = {b₁, ..., bₙ} is a basis, every vector v has a unique representation

v = c₁b₁ + ... + cₙbₙ.

The coefficient vector

[c₁, ..., cₙ]

contains the coordinates of v relative to B.

The script solves for these coordinates using Gaussian-Jordan elimination.

For an orthonormal basis, the coordinates become especially simple:

cᵢ = <bᵢ|v>.

This identity is heavily used in quantum mechanics and quantum computing.

---

## 13. Matrices and Linear Systems

A matrix can represent a linear transformation.

If A is an m × n matrix and v is an n-dimensional vector, then

Av

is an m-dimensional vector.

The script implements:

- Matrix-vector multiplication
- Matrix multiplication
- Identity matrices
- Conjugate transpose
- Matrix powers
- Gaussian-Jordan elimination
- Rank
- Linear-system solving

These operations provide the computational foundation for basis transformations and quantum operators.

---

## 14. Complex Vector Spaces

Quantum states are not generally vectors over R. They are vectors over C.

The difference becomes important when defining inner products.

For real vectors, the ordinary Euclidean inner product is

u · v = Σᵢ uᵢvᵢ.

For complex vectors, the standard inner product is

<u|v> = Σᵢ conjugate(uᵢ)vᵢ.

The complex conjugation is essential.

---

## 15. Inner Products

An inner product is a generalized notion of multiplication between two vectors that produces a scalar.

For complex finite-dimensional vectors,

<u|v> = Σᵢ conjugate(uᵢ)vᵢ.

The script implements this operation with `complex_inner_product`.

An inner product provides concepts such as:

- Length
- Orthogonality
- Angle-like relationships
- Projection
- Similarity
- Coordinates in an orthonormal basis

---

## 16. Inner-Product Axioms

A complex inner product satisfies several fundamental properties.

### Conjugate symmetry

<u|v> = conjugate(<v|u>).

For real vectors this reduces to ordinary symmetry.

### Linearity in the second argument

<u|av + bw>
=
a<u|v> + b<u|w>.

### Conjugate-linearity in the first argument

<au + bv|w>
=
conjugate(a)<u|w>
+
conjugate(b)<v|w>.

### Positive definiteness

<v|v> ≥ 0.

Also,

<v|v> = 0

if and only if

v = 0.

The script explicitly checks these properties numerically.

---

## 17. Why Conjugation Matters

For complex vectors, simply multiplying corresponding components without conjugation does not produce the standard inner product.

For example, if

v = [i, 1],

the naive product

v · v

would be

i² + 1²
=
-1 + 1
=
0.

That is not an appropriate measure of vector length.

The Hermitian inner product gives

<v|v>
=
conjugate(i)i + 1
=
(-i)i + 1
=
2.

Thus the norm is sqrt(2).

The script contains an explicit comparison between the naive component-wise product and the correct complex inner product.

---

## 18. Bra-Ket Notation

Quantum computing commonly uses Dirac notation.

A ket is written as

|ψ>.

It represents a column vector.

For example,

|ψ> =
[a, b]ᵀ.

The corresponding bra is

<ψ|.

The bra is the conjugate transpose of the ket:

<ψ|
=
[conjugate(a), conjugate(b)].

The inner product is therefore

<ψ|φ>.

The script implements:

- `ket`
- `bra`
- `bra_ket_inner_product`
- `ket_bra_outer_product`

---

## 19. Norm

The norm induced by the inner product is

||v||
=
sqrt(<v|v>).

For a complex vector,

||v||²
=
Σᵢ |vᵢ|².

The norm measures the length of the vector.

The script implements this as `vector_norm`.

A normalized vector satisfies

||v|| = 1.

---

## 20. Normalization

A nonzero vector can be normalized by dividing it by its norm:

v_normalized
=
v / ||v||.

This preserves direction while changing its magnitude to one.

For a quantum state,

<ψ|ψ> = 1.

Normalization is not optional for a pure quantum state represented by a state vector.

The script's `normalize` function performs this operation.

The zero vector cannot be normalized because division by its norm would require division by zero.

---

## 21. Quantum State Vectors

A pure quantum state is represented by a normalized vector in a complex Hilbert space.

For one qubit,

|ψ>
=
α|0> + β|1>.

The computational basis is

|0> = [1, 0]ᵀ

|1> = [0, 1]ᵀ.

The normalization condition is

|α|² + |β|² = 1.

For multiple qubits, the same principle applies, but the vector dimension becomes exponential.

The `QuantumState` class validates normalization when a state is created.

---

## 22. Superposition

Superposition is represented mathematically by linear combinations of basis states.

For one qubit,

|ψ>
=
α|0> + β|1>.

The amplitudes α and β can be complex.

The measurement probabilities in the computational basis are

P(0) = |α|²

P(1) = |β|².

Normalization guarantees

P(0) + P(1) = 1.

The script demonstrates superposition using normalized combinations of |0> and |1>.

---

## 23. Inner Products Between Quantum States

For normalized states |ψ> and |φ>,

<φ|ψ>

is their complex overlap.

Its magnitude satisfies

0 ≤ |<φ|ψ>| ≤ 1.

If

<φ|ψ> = 0,

the states are orthogonal.

If

|<φ|ψ>| = 1,

the two normalized state vectors differ only by a phase factor.

The squared magnitude

|<φ|ψ>|²

is directly connected to the probability of obtaining |φ> when measuring |ψ> using a measurement containing that state.

The `QuantumState.overlap_probability` method implements this quantity.

---

## 24. Orthogonality

Two vectors are orthogonal if

<u|v> = 0.

For real vectors this generalizes perpendicularity.

For quantum states, orthogonal states can be perfectly distinguished by an appropriate measurement.

The computational basis states satisfy

<0|1> = 0.

They are therefore orthogonal.

---

## 25. Orthonormal Sets

A collection of vectors is orthonormal when

<qᵢ|qⱼ> = δᵢⱼ,

where δᵢⱼ is the Kronecker delta.

Therefore:

- Each vector has norm one.
- Different vectors are mutually orthogonal.

The computational basis is orthonormal.

The script uses `is_orthonormal_set` to verify this property.

---

## 26. Computational Basis

For one qubit:

|0> = [1, 0]

|1> = [0, 1].

For two qubits:

|00> = [1, 0, 0, 0]

|01> = [0, 1, 0, 0]

|10> = [0, 0, 1, 0]

|11> = [0, 0, 0, 1].

The dimension is 4.

For n qubits, the basis states are indexed by n-bit strings and there are 2ⁿ of them.

The script generates these basis vectors programmatically.

---

## 27. Distance

An inner product induces a distance:

d(u,v) = ||u-v||.

The script implements this with `distance`.

Distance is useful for numerical analysis, approximation, geometric interpretation, and comparing vectors.

For quantum states, raw Euclidean vector distance must be interpreted carefully because global phase has no physical significance for pure states.

---

## 28. Angles and Complex Vector Spaces

In real vector spaces,

cos(theta)
=
<u,v> / (||u|| ||v||).

Complex vector spaces require more care because the inner product can itself be complex.

A commonly useful phase-insensitive quantity is

cos(theta)
=
|<u,v>| / (||u|| ||v||).

This gives a geometric angle-like measure based on the magnitude of the overlap.

The script uses this definition in `complex_angle`.

---

## 29. Cauchy-Schwarz Inequality

For every pair of vectors,

|<u|v>|
≤
||u|| ||v||.

This is the Cauchy-Schwarz inequality.

It is fundamental because it establishes bounds on inner products and guarantees that normalized-state overlaps cannot exceed one.

For normalized quantum states,

|<u|v>| ≤ 1.

The script checks this inequality numerically.

---

## 30. Triangle Inequality

For the norm induced by an inner product,

||u+v||
≤
||u|| + ||v||.

This is the triangle inequality.

Together with positivity, homogeneity, and definiteness, it contributes to the structure of a normed vector space.

The script demonstrates the inequality with explicit vectors.

---

## 31. Projection Onto a Vector

The orthogonal projection of v onto a nonzero vector u is

proj_u(v)
=
<u|v> / <u|u> u.

If u is normalized, this becomes

proj_u(v)
=
<u|v>u.

The residual

v - proj_u(v)

is orthogonal to u.

The script implements this formula and verifies the orthogonality of the residual.

---

## 32. Projection Onto a Subspace

Suppose {q₁, ..., qₖ} is an orthonormal basis for a subspace W.

The projection of v onto W is

P_W v
=
Σᵢ <qᵢ|v> qᵢ.

In bra-ket notation,

P_W
=
Σᵢ |qᵢ><qᵢ|.

This is a projector operator.

The script demonstrates projection onto an orthonormal subspace and checks that the residual is orthogonal to the subspace.

---

## 33. Projectors

A projector P satisfies

P² = P.

This property means applying the projection twice produces the same result as applying it once.

A rank-one projector associated with a normalized state |ψ> is

P
=
|ψ><ψ|.

The script constructs projectors and verifies:

P² = P.

For a Hermitian projector,

P† = P.

---

## 34. Resolution of the Identity

For an orthonormal basis {|qᵢ>},

Σᵢ |qᵢ><qᵢ|
=
I.

This is called the resolution of the identity.

For the computational basis of a qubit,

|0><0|
+
|1><1|
=
I.

This identity explains why every vector can be reconstructed from its projections onto an orthonormal basis.

The script explicitly constructs this sum and verifies that it equals the identity matrix.

---

## 35. Basis Expansion

Given an orthonormal basis {|qᵢ>}, a vector can be expanded as

|v>
=
Σᵢ cᵢ|qᵢ>.

The coefficients are

cᵢ
=
<qᵢ|v>.

Therefore,

|v>
=
Σᵢ |qᵢ><qᵢ|v>.

This is one of the most important relationships between inner products and coordinates.

The script demonstrates this expansion and reconstructs the original state.

---

## 36. Gram-Schmidt Orthonormalization

Gram-Schmidt transforms linearly independent vectors into an orthonormal set spanning the same subspace.

For the first vector,

q₁
=
v₁ / ||v₁||.

For the next vector,

u₂
=
v₂ - <q₁|v₂>q₁,

then

q₂
=
u₂ / ||u₂||.

The process continues by subtracting projections onto all previous orthonormal vectors.

The script contains both:

- Classical Gram-Schmidt
- Modified Gram-Schmidt

Modified Gram-Schmidt is generally more numerically stable.

---

## 37. Numerical Stability

Mathematical equality and floating-point equality are not always identical in computer programs.

For example,

0.1 + 0.2

may not be represented exactly as 0.3 in binary floating-point arithmetic.

Quantum calculations can also accumulate small numerical errors.

The script therefore uses tolerance-based comparisons such as:

`abs(a - b) <= tolerance`

rather than relying exclusively on exact equality.

This is particularly important when checking:

- Normalization
- Orthogonality
- Hermiticity
- Unitarity
- Projector identities
- Eigenvector relationships

---

## 38. Classical Versus Modified Gram-Schmidt

Classical Gram-Schmidt can lose orthogonality because of floating-point roundoff.

Modified Gram-Schmidt reorganizes the computation so that each remaining vector is immediately corrected after a basis vector is produced.

For numerical linear algebra, modified Gram-Schmidt is generally preferable when robustness matters.

For large-scale production numerical work, specialized numerical linear-algebra libraries often provide even more stable algorithms such as Householder QR factorization.

The script includes Gram-Schmidt primarily to expose the underlying mathematics.

---

## 39. Tensor Products

Composite quantum systems are represented using tensor products.

If

|a> ∈ Cᵐ

and

|b> ∈ Cⁿ,

then

|a> ⊗ |b>

belongs to

C^(mn).

For two qubits, each qubit has dimension 2, so

2 × 2 = 4.

Thus two-qubit states live in C⁴.

The script implements vector tensor products with `tensor_product`.

---

## 40. Tensor-Product Inner Product

A key identity is

< a⊗b | c⊗d >
=
<a|c><b|d>.

This factorization is important for composite quantum systems.

The script verifies this identity numerically.

Tensor products also explain why the state-space dimension grows exponentially with the number of qubits.

---

## 41. Product States

A two-qubit state is a product state when it can be written as

|ψ> = |a> ⊗ |b>.

For a state

[a, b, c, d],

a pure two-qubit state is separable when

ad - bc = 0.

The script uses this condition in `is_product_two_qubit_state`.

Product states contain no entanglement between the two subsystems.

---

## 42. Entangled States

The Bell state

|Φ⁺>
=
(|00> + |11>) / sqrt(2)

is an entangled state.

Its vector representation is

[1/sqrt(2), 0, 0, 1/sqrt(2)].

It cannot be expressed as a tensor product of two single-qubit states.

The script constructs this Bell state and demonstrates that it is not a product state.

---

## 43. Global Phase

Suppose

|φ>
=
e^(iθ)|ψ>.

The two state vectors are mathematically different unless θ is a multiple of 2π.

Nevertheless, they represent the same physical pure quantum state because a global phase does not affect measurement probabilities.

The script provides `global_phase_equivalent` to distinguish mathematical vector equality from physical equivalence.

This distinction is critical in quantum computing.

A global phase must not be confused with relative phase. Relative phases between components of a superposition can affect interference and are physically observable.

---

## 44. Relative Phase

Consider

|+>
=
(|0> + |1>) / sqrt(2)

and

|->
=
(|0> - |1>) / sqrt(2).

The minus sign is a relative phase difference.

It changes the state physically.

The states are orthogonal:

<+|-> = 0.

By contrast,

i|+>

differs from |+> only by a global phase.

The script demonstrates both situations.

---

## 45. Linear Operators

A linear operator A maps vectors to vectors while satisfying

A(u+v) = Au + Av

and

A(cv) = cAv.

In matrix form, a linear operator acts as

|ψ'> = A|ψ>.

Quantum gates are represented by linear operators.

The script implements matrix-vector multiplication and several important quantum operators.

---

## 46. Pauli Operators

The Pauli matrices are

X =
[[0, 1],
 [1, 0]]

Y =
[[0, -i],
 [i, 0]]

Z =
[[1, 0],
 [0, -1]].

Their action on computational basis states includes:

X|0> = |1>

X|1> = |0>

Z|0> = |0>

Z|1> = -|1>.

The script implements all three.

---

## 47. Hadamard Operator

The Hadamard operator is

H
=
1/sqrt(2)
[[1, 1],
 [1, -1]].

Its action includes

H|0> = |+>

H|1> = |->.

The Hadamard transform is central to quantum algorithms because it converts computational-basis states into superposition states.

It is both Hermitian and unitary.

The script verifies that

H² = I.

---

## 48. Hermitian Matrices

A matrix A is Hermitian when

A† = A,

where A† is the conjugate transpose.

Hermitian operators represent observables in quantum mechanics.

The Pauli X, Y, and Z operators are Hermitian.

A Hermitian operator has real eigenvalues.

The expectation value of a Hermitian observable is real, apart from tiny floating-point errors.

The script checks Hermiticity and evaluates expectation values.

---

## 49. Adjoint and Conjugate Transpose

For a matrix A,

A†

is obtained by:

1. Taking the transpose
2. Taking the complex conjugate

For an inner product,

<Au|v>
=
<u|A†v>.

This identity is central to the definition of an adjoint.

The script explicitly checks this identity.

The adjoint is the complex-vector-space analogue of transpose with the conjugation required by the Hermitian inner product.

---

## 50. Unitary Operators

A matrix U is unitary when

U†U = I.

For a square matrix, this also implies

UU† = I.

Unitary transformations preserve inner products:

<Uu|Uv>
=
<u|v>.

Consequently, they preserve norms:

||Uu|| = ||u||.

This makes unitary matrices suitable for reversible quantum evolution and quantum gates.

The script verifies that Pauli matrices and the Hadamard matrix are unitary.

---

## 51. Why Unitarity Preserves Normalization

If

U†U = I,

then

||U|ψ>||²
=
<Uψ|Uψ>.

Using the adjoint,

<Uψ|Uψ>
=
<ψ|U†U|ψ>.

Since U†U = I,

<ψ|U†U|ψ>
=
<ψ|ψ>.

Therefore,

||Uψ|| = ||ψ||.

A normalized quantum state remains normalized after a unitary transformation.

---

## 52. Unitary Operators Preserve Inner Products

The same argument gives

<Uψ|Uφ>
=
<ψ|U†U|φ>
=
<ψ|φ>.

Therefore unitary transformations preserve:

- Norms
- Inner products
- Orthogonality
- Distances
- Transition probabilities

This means quantum gates transform the representation of a state without destroying its underlying Hilbert-space geometry.

---

## 53. Eigenvectors and Eigenvalues

A vector v is an eigenvector of A when

Av = λv.

The scalar λ is the eigenvalue.

Eigenvectors of observables correspond to definite measurement outcomes.

For Pauli X:

X|+> = +|+>

X|-> = -|->.

For Pauli Z:

Z|0> = +|0>

Z|1> = -|1>.

The script checks these relationships directly.

---

## 54. Expectation Values

For a quantum state |ψ> and observable A,

< A >
=
<ψ|A|ψ>.

This is called the expectation value.

If A is Hermitian, the expectation value is real.

For the Pauli Z observable:

- |0> has expectation value +1
- |1> has expectation value -1
- |+> has expectation value 0

The script implements expectation values with `expectation_value`.

---

## 55. Variance of an Observable

The variance of an observable A is

Var(A)
=
<A²> - <A>².

It quantifies the spread of possible measurement outcomes.

If the state is an eigenstate of A, the variance is zero.

For example, |0> is an eigenstate of Z, so

Var(Z) = 0.

The |+> state is not a Z eigenstate, so its Z measurement has nonzero variance.

The script computes observable variance.

---

## 56. Born's Rule

For a normalized state |ψ> and a rank-one projector

P = |φ><φ|,

the probability of the corresponding outcome is

p
=
<ψ|P|ψ>.

Using the projector definition,

p
=
|<φ|ψ>|².

This is the Born rule in the rank-one projective-measurement case.

The script implements the equivalent overlap-squared expression.

---

## 57. Measurement in the Computational Basis

For

|ψ>
=
Σᵢ αᵢ|i>,

measurement in the computational basis gives outcome i with probability

P(i)
=
|αᵢ|².

Normalization requires

Σᵢ |αᵢ|² = 1.

The script implements `computational_measurement_probabilities`.

It also contains a measurement simulator that samples outcomes according to these probabilities.

The simulation illustrates statistical convergence but does not replace the mathematical definition of probability.

---

## 58. Measurement in an Alternative Basis

A quantum state does not have a single set of probabilities independent of the measurement basis.

For example,

|0>
=
(|+> + |->) / sqrt(2).

Therefore measuring |0> in the {|+>, |->} basis gives

P(+) = 1/2

P(-) = 1/2.

The script demonstrates this with `measure_in_orthonormal_basis`.

The basis determines which amplitudes are relevant for the measurement.

---

## 59. Orthonormal Bases and Quantum Measurements

An orthonormal basis

{|q₁>, ..., |qₙ>}

provides projectors

Pᵢ = |qᵢ><qᵢ|.

They satisfy

PᵢPⱼ = 0

for i ≠ j,

and

Σᵢ Pᵢ = I.

For a state |ψ>, the probability of outcome i is

pᵢ
=
<ψ|Pᵢ|ψ>
=
|<qᵢ|ψ>|².

This connects vector-space geometry directly to measurement.

---

## 60. Gram Matrices

For vectors v₁, ..., vₖ, the Gram matrix is

Gᵢⱼ
=
<vᵢ|vⱼ>.

The diagonal entries are squared norms:

Gᵢᵢ = ||vᵢ||².

The Gram matrix is Hermitian and positive semidefinite.

It contains information about pairwise inner products and therefore about the geometry of the vector set.

The script constructs Gram matrices with `gram_matrix`.

---

## 61. Positive Semidefiniteness

A Hermitian matrix G is positive semidefinite when

x†Gx ≥ 0

for every vector x.

Gram matrices have this property because

x†Gx

can be interpreted as the squared norm of a linear combination of the original vectors.

This is one reason inner products are so powerful: they induce a positive geometry.

---

## 62. Orthogonal Complements

For a subspace W, the orthogonal complement W⊥ contains every vector orthogonal to every vector in W.

A vector v belongs to W⊥ when

<v|w> = 0

for every w in W.

In finite-dimensional inner-product spaces,

V = W ⊕ W⊥

under the standard conditions.

This decomposition supports projection and least-squares methods.

The script illustrates orthogonal complements using orthonormal vectors in C².

---

## 63. Density-Matrix Connection

Although the primary topic is vector spaces and inner products, pure quantum states naturally produce operators of the form

ρ
=
|ψ><ψ|.

This is the density matrix of a pure state.

It satisfies:

ρ† = ρ

ρ² = ρ

Tr(ρ) = 1.

The script constructs this object using `projector` and verifies these properties.

This connection shows how ket-bra algebra extends vector-space concepts into operator representations.

---

## 64. Kets, Bras, and Outer Products

The inner product

<φ|ψ>

produces a scalar.

The outer product

|ψ><φ|

produces an operator.

For vectors

|ψ> = [a, b]ᵀ

and

<φ| = [conjugate(c), conjugate(d)],

the outer product is

[[a conjugate(c), a conjugate(d)],
 [b conjugate(c), b conjugate(d)]].

The distinction between inner and outer products is essential:

- Inner product: vector + vector → scalar
- Outer product: vector + bra → matrix/operator

---

## 65. Global Phase Versus Relative Phase

A global phase has the form

|ψ'> = e^(iθ)|ψ>.

It does not change physical measurement probabilities.

A relative phase changes the relationship between amplitudes.

For example,

(|0> + |1>) / sqrt(2)

and

(|0> - |1>) / sqrt(2)

have different relative phases and are physically distinct.

The script explicitly distinguishes these cases.

---

## 66. Linear Functionals

A linear functional maps a vector to a scalar.

For a fixed bra <a|,

f(v) = <a|v>.

The function is linear in v:

f(av + bw)
=
a f(v) + b f(w).

Inner-product spaces provide a natural way of representing linear functionals by bras.

In finite-dimensional complex vector spaces, this relationship is a concrete manifestation of the Riesz representation principle.

---

## 67. Change of Basis

A vector does not depend on the coordinate system used to describe it.

Its coordinate representation changes when the basis changes.

If Q is an orthonormal basis matrix whose columns are basis vectors, coordinates can be obtained through inner products.

For basis vectors qᵢ,

cᵢ = <qᵢ|v>.

This makes inner products the mechanism for extracting coordinates in orthonormal bases.

Quantum circuits frequently change the basis in which states are represented or measured.

---

## 68. Important Distinctions

### Dot product versus complex inner product

For real vectors:

u · v = Σuᵢvᵢ.

For complex vectors:

<u|v> = Σconjugate(uᵢ)vᵢ.

The conjugation is required.

### Vector versus state

Any vector can exist mathematically, but a pure quantum state must be normalized.

### Mathematical equality versus physical equivalence

Two vectors that differ by a global phase are mathematically different vectors but represent the same pure physical state.

### Orthogonal versus orthonormal

Orthogonal means inner product zero for distinct vectors.

Orthonormal additionally requires each vector to have norm one.

### Inner product versus outer product

An inner product produces a scalar.

An outer product produces a linear operator.

### Hermitian versus unitary

Hermitian:

A† = A.

Unitary:

A†A = I.

An operator can be both, but the concepts describe different properties.

---

## 69. Common Mistakes

### Forgetting complex conjugation

Using

Σuᵢvᵢ

for complex vectors is not the standard quantum inner product.

Use

Σconjugate(uᵢ)vᵢ.

### Treating every vector as a valid quantum state

A state vector must satisfy

<ψ|ψ> = 1.

### Normalizing the zero vector

The zero vector cannot be normalized.

### Ignoring dimension compatibility

Vector addition requires equal dimensions.

Matrix multiplication requires compatible inner dimensions.

### Assuming orthogonality from visual intuition

For complex vectors, calculate the Hermitian inner product.

### Treating global phase as observable

A global phase does not affect physical measurement probabilities for a pure state.

### Confusing global and relative phase

Relative phase can change interference and measurement outcomes.

### Using exact floating-point comparisons

Numerical calculations should normally use tolerances.

### Assuming classical Gram-Schmidt is always numerically stable

It can suffer from loss of orthogonality in finite precision.

### Confusing Hermitian and unitary

Hermitian means equal to its adjoint.

Unitary means inverse equals adjoint.

---

## 70. Edge Cases

The script explicitly handles several important edge cases.

### Zero vector

Its norm is zero and it cannot be normalized.

### Dimension mismatch

Operations such as vector addition and inner products require compatible dimensions.

### Dependent vectors

Gram-Schmidt cannot create a new normalized direction from a vector already in the span of previous vectors.

### Unnormalized quantum amplitudes

The `QuantumState` class rejects vectors whose norm differs from one beyond the numerical tolerance.

### Zero projection direction

Projection onto the zero vector is undefined because the denominator

<u|u>

is zero.

### Numerical near-dependence

Vectors that are mathematically independent can appear nearly dependent under finite precision.

Tolerance selection therefore matters.

---

## 71. Performance Considerations

The script intentionally uses plain Python lists so that the mathematical operations are transparent.

This is suitable for education but not optimal for large-scale numerical linear algebra.

For an n-qubit pure state, the vector dimension is

2ⁿ.

Consequently, explicitly storing a state vector requires memory proportional to 2ⁿ complex amplitudes.

Basic vector operations are typically O(N) for an N-dimensional vector.

Dense matrix-vector multiplication is typically O(N²).

Dense matrix multiplication is typically O(N³).

For quantum systems, these costs become significant quickly because N itself may be exponential in the number of qubits.

The script therefore prioritizes conceptual clarity over high-performance simulation.

---

## 72. Quantum-State Memory Scaling

An n-qubit pure state contains 2ⁿ complex amplitudes.

For example:

- 1 qubit → 2 amplitudes
- 2 qubits → 4 amplitudes
- 3 qubits → 8 amplitudes
- 10 qubits → 1,024 amplitudes
- 20 qubits → 1,048,576 amplitudes
- 30 qubits → 1,073,741,824 amplitudes

The exponential growth is a mathematical property of the state space.

It does not mean every quantum algorithm explicitly stores a full classical array of all amplitudes on a physical quantum computer. Quantum hardware represents states through physical quantum systems, while classical simulation is subject to the memory and computational costs of the chosen representation.

---

## 73. Security and Correctness Considerations

Vector-space mathematics itself is not a security mechanism.

In quantum-computing implementations, correctness depends on preserving mathematical invariants such as:

- State normalization
- Operator unitarity
- Hermiticity of observables
- Valid probability distributions
- Dimension consistency
- Correct complex conjugation

Incorrect normalization or an invalid operator can produce results that look numerically plausible while violating the mathematical model.

For software intended for scientific or production use, numerical validation and independent tests are therefore important.

---

## 74. Implementation Design

The script separates mathematical operations into small functions.

Examples include:

- `vector_add`
- `scalar_multiply`
- `complex_inner_product`
- `vector_norm`
- `normalize`
- `rref`
- `rank`
- `gram_schmidt`
- `project_onto_vector`
- `tensor_product`
- `expectation_value`
- `projector`

The `QuantumState` class adds a domain-level invariant: a quantum state must remain normalized.

This separation makes it easier to distinguish generic linear algebra from quantum-specific rules.

---

## 75. Numerical Validation

The script includes executable tests covering:

- Vector addition
- Scalar multiplication
- Inner-product conjugate symmetry
- Normalization
- Orthonormality
- Gram-Schmidt
- Quantum-state normalization
- Measurement probabilities
- Unitarity
- Hermiticity
- Quantum-gate action
- Projection
- Tensor-product inner products
- Bell-state entanglement
- Projector properties
- Density-matrix trace
- Resolution of identity

The tests are intentionally lightweight and use Python assertions.

They are mathematical consistency checks rather than a replacement for a comprehensive numerical test suite.

---

## 76. Practical Quantum-Computing Applications

Vector spaces and inner products appear directly in:

- Qubit representation
- Quantum-state normalization
- Superposition
- Measurement probabilities
- Quantum-basis transformations
- Quantum gates
- Unitary evolution
- Observable expectation values
- Quantum measurement
- Orthogonal projective measurements
- Tensor-product systems
- Entanglement
- State overlap
- Quantum-state discrimination
- Density-matrix construction
- Variational quantum methods
- Quantum algorithm analysis

The mathematical relationships in the script are therefore not merely abstract linear algebra. They form the underlying formalism for quantum information processing.

---

## 77. Conceptual Structure of the Script

The script progresses through the following dependency chain:

1. Scalars
2. Vectors
3. Vector operations
4. Vector spaces
5. Linear combinations
6. Span
7. Linear independence
8. Basis
9. Dimension
10. Complex vector spaces
11. Inner products
12. Norms
13. Distance
14. Orthogonality
15. Orthonormal bases
16. Projection
17. Gram-Schmidt
18. Bra-ket notation
19. Quantum states
20. Superposition
21. Measurement probabilities
22. Change of basis
23. Tensor products
24. Entanglement
25. Linear operators
26. Adjoint
27. Hermitian operators
28. Unitary operators
29. Eigenvectors
30. Expectation values
31. Variance
32. Projectors
33. Density matrices

Each later concept relies on structures established earlier.

---

## 78. Mathematical Identities Implemented in the Script

The most important identities demonstrated include:

### Vector-space identities

u + v = v + u

(u + v) + w = u + (v + w)

u + 0 = u

u + (-u) = 0

a(u + v) = au + av

(a + b)u = au + bu

(ab)u = a(bu)

### Inner-product identities

<u|v> = conjugate(<v|u>)

<u|av + bw>
=
a<u|v> + b<u|w>

<au|v>
=
conjugate(a)<u|v>

<v|v> ≥ 0

<v|v> = 0 iff v = 0

### Norm identities

||v|| = sqrt(<v|v>)

||cv|| = |c| ||v||

||u+v|| ≤ ||u|| + ||v||

### Cauchy-Schwarz

|<u|v>| ≤ ||u|| ||v||

### Projection

proj_u(v)
=
<u|v>/<u|u> u

### Orthonormal expansion

|v>
=
Σᵢ <qᵢ|v>|qᵢ>

### Identity resolution

Σᵢ |qᵢ><qᵢ| = I

### Unitarity

U†U = I

### Inner-product preservation

<Uu|Uv> = <u|v>

### Expectation value

<A> = <ψ|A|ψ>

### Rank-one projector

P = |ψ><ψ|

### Projector property

P² = P

### Tensor-product inner product

<a⊗b|c⊗d>
=
<a|c><b|d>

### Quantum measurement

P(i) = |αᵢ|²

---

## 79. Relationship Between Linear Algebra and Quantum Computing

The core correspondence can be viewed as follows:

| Linear Algebra | Quantum Computing |
|---|---|
| Complex vector | Pure quantum state |
| Unit vector | Normalized quantum state |
| Basis | Measurement/state representation basis |
| Inner product | State overlap |
| Orthogonality | Perfect distinguishability of basis states |
| Linear combination | Quantum superposition |
| Matrix | Linear operator |
| Unitary matrix | Quantum gate/evolution operator |
| Hermitian matrix | Observable |
| Eigenvector | Definite state of an observable |
| Eigenvalue | Measurement value |
| Projection | Measurement component |
| Tensor product | Composite quantum system |
| Projector | Measurement outcome operator |
| Inner-product squared magnitude | Transition probability |

This correspondence is the central reason linear algebra is indispensable to quantum computing.

---

## 80. Computational Representation

The educational implementation intentionally maps mathematical objects directly to Python structures.

Vectors are represented as:

`list[complex]`

Matrices are represented as:

`list[list[complex]]`

A quantum state is represented by the `QuantumState` class.

This makes the correspondence between mathematical notation and executable code explicit.

For example, the mathematical expression

|ψ> = α|0> + β|1>

corresponds to a two-element Python vector containing α and β.

---

## 81. Production Considerations

The script is designed for conceptual study rather than production-scale quantum simulation.

For production numerical linear algebra, several issues become important:

- Stable matrix factorizations
- Efficient memory layout
- Vectorized operations
- Sparse representations
- Parallel computation
- Numerical conditioning
- High-quality linear-algebra kernels
- Error analysis
- Reproducible numerical tests
- Explicit tolerance policies

For quantum simulation, additional concerns include:

- Exponential state-vector growth
- Sparse state representations
- Tensor-network representations
- Circuit structure
- Gate locality
- Numerical precision
- Noise models
- Measurement sampling

These are implementation concerns layered on top of the mathematical framework developed in the script.

---

## 82. Scope of the Mathematical Model

The main quantum model used here is finite-dimensional pure-state quantum mechanics.

The script therefore focuses on:

- Cⁿ vector spaces
- Inner products
- Normalized state vectors
- Linear operators
- Unitary operators
- Hermitian operators
- Projectors
- Tensor products
- Pure-state density matrices

More general quantum information uses mixed states, positive operators, general measurements, channels, and other structures. The density-matrix section provides a bridge toward those concepts while keeping the primary focus on vector spaces and inner products.

---

## 83. Running the Script

The file is a standalone Python program using only the standard library.

Running it executes:

1. Fundamental vector-space demonstrations
2. Inner-product demonstrations
3. Geometric demonstrations
4. Quantum-state demonstrations
5. Operator demonstrations
6. Measurement examples
7. Tensor-product examples
8. Entanglement examples
9. Numerical-stability examples
10. Edge-case demonstrations
11. Automated mathematical consistency tests

The output is intentionally verbose so that each mathematical concept can be observed through an executable calculation.

---

## 84. Relationship Between Geometry and Quantum States

The most important geometric interpretation is that quantum states inhabit a complex inner-product space.

The inner product defines:

- Length
- Orthogonality
- Overlap
- Projection
- Coordinates in orthonormal bases

Normalization places physical pure states on the unit sphere of the complex vector space.

Unitary transformations move states while preserving the inner-product geometry.

Measurements extract information through projections onto appropriate subspaces or basis states.

This provides a unified mathematical explanation for many fundamental quantum-computing operations.

---

## 85. Central Conceptual Relationships

Several ideas should be understood as connected rather than isolated formulas.

A vector space provides the objects.

An inner product provides geometry.

The norm comes from the inner product.

Orthogonality comes from the inner product.

Orthonormal bases provide stable coordinate systems.

Projections use inner products to extract components.

Quantum amplitudes are coordinates of state vectors.

Measurement probabilities come from squared magnitudes of inner products.

Unitary operators preserve inner products.

Hermitian operators describe observables.

Tensor products construct composite systems.

These relationships form the mathematical structure connecting elementary linear algebra to quantum computation.
