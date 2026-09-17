# Hilbert spaces

## Mathematical framework

Hilbert spaces provide a mathematical framework for studying geometry, approximation, convergence, functions, operators, and infinite-dimensional systems using the structure of an inner product.

The essential definition is:

> A Hilbert space is a complete inner-product space.

This definition combines two ideas. An inner product supplies geometric information such as length, angle, orthogonality, and projection. Completeness guarantees that Cauchy sequences converge to elements that remain inside the space.

The three implementations in this repository approach the subject from different computational perspectives:

- Python develops the mathematical framework from elementary vector geometry through function spaces, orthogonal expansions, operators, and numerical approximation.
- JavaScript implements the same mathematical structures with JavaScript-specific classes, functional transformations, asynchronous execution, validation, and browser interaction.
- C++ develops an industry-style signal reconstruction system in which a noisy signal is projected onto a Hilbert-space model subspace.

The implementations use finite-dimensional numerical models to make abstract Hilbert-space concepts executable. Infinite-dimensional spaces are discussed mathematically and approximated computationally through discretization.

## Fundamental concepts

### Vector space

A vector space consists of elements called vectors together with two operations:

- vector addition
- scalar multiplication

For vectors \(x\) and \(y\), the sum \(x+y\) must remain in the space. For a scalar \(a\), the product \(ax\) must also remain in the space.

Examples include:

- \(\mathbb{R}^n\)
- \(\mathbb{C}^n\)
- polynomial spaces
- spaces of functions
- spaces of sequences

A vector space alone does not provide a concept of distance or angle.

### Inner product

An inner product is a function that assigns a scalar to two vectors.

For real Euclidean vectors,

\[
\langle x,y\rangle =
\sum_{i=1}^{n}x_i y_i.
\]

For complex vectors, using the convention implemented in the Python and JavaScript demonstrations,

\[
\langle x,y\rangle =
\sum_{i=1}^{n}\overline{x_i}y_i.
\]

The complex conjugate is essential.

An inner product provides the geometric information required for Hilbert-space geometry.

### Inner-product axioms

For vectors \(x,y,z\) and scalars \(a,b\), an inner product satisfies:

#### Conjugate symmetry

\[
\langle x,y\rangle =
\overline{\langle y,x\rangle}.
\]

For real vector spaces this reduces to ordinary symmetry:

\[
\langle x,y\rangle=\langle y,x\rangle.
\]

#### Linearity

With the convention used here, linearity occurs in the second argument:

\[
\langle x,ay+bz\rangle
=
a\langle x,y\rangle+
b\langle x,z\rangle.
\]

The first argument is conjugate-linear in a complex inner-product space.

#### Positive definiteness

\[
\langle x,x\rangle\geq0
\]

and

\[
\langle x,x\rangle=0
\]

if and only if

\[
x=0.
\]

These conditions distinguish an inner product from an arbitrary bilinear or sesquilinear expression.

## Norm induced by an inner product

Every inner product produces a norm:

\[
\|x\|=\sqrt{\langle x,x\rangle}.
\]

For a real vector,

\[
\|x\|_2 =
\sqrt{x_1^2+x_2^2+\cdots+x_n^2}.
\]

For example,

\[
\|(3,4)\|_2=5.
\]

The Python function `norm()` and the JavaScript function `vectorNorm()` implement this relationship directly.

The C++ function `norm()` uses the same mathematical definition.

## Distance

The inner-product-induced distance is

\[
d(x,y)=\|x-y\|.
\]

This converts the vector space into a metric space.

Distance is essential when discussing convergence and approximation.

For example, if a sequence \(x_n\) approaches \(x\), then

\[
\|x_n-x\|\rightarrow0.
\]

This is called strong or norm convergence.

## Orthogonality

Two vectors are orthogonal when

\[
\langle x,y\rangle=0.
\]

In Euclidean geometry, this corresponds to perpendicular vectors.

The implementations use a numerical tolerance because floating-point arithmetic rarely produces exact zero.

For example,

\[
(3,4)\cdot(4,-3)
=
12-12
=
0.
\]

Therefore these vectors are orthogonal.

## Pythagorean theorem

If \(x\) and \(y\) are orthogonal, then

\[
\|x+y\|^2
=
\|x\|^2+\|y\|^2.
\]

This is the Hilbert-space form of the Pythagorean theorem.

It follows directly from expanding the inner product:

\[
\begin{aligned}
\|x+y\|^2
&=
\langle x+y,x+y\rangle\\
&=
\langle x,x\rangle+
\langle x,y\rangle+
\langle y,x\rangle+
\langle y,y\rangle.
\end{aligned}
\]

The cross terms vanish when \(x\) and \(y\) are orthogonal.

## Cauchy-Schwarz inequality

Every inner-product space satisfies

\[
|\langle x,y\rangle|
\leq
\|x\|\|y\|.
\]

This inequality is fundamental because it guarantees that the inner product is controlled by the norm.

The Python implementation explicitly evaluates both sides numerically.

## Triangle inequality

The induced norm satisfies

\[
\|x+y\|
\leq
\|x\|+\|y\|.
\]

Therefore the norm produces a valid metric.

## The parallelogram identity

A norm comes from an inner product precisely when it satisfies the parallelogram identity:

\[
\|x+y\|^2+\|x-y\|^2
=
2\|x\|^2+2\|y\|^2.
\]

The Python implementation verifies this identity numerically.

This distinction is important because not every normed vector space is an inner-product space.

## Related mathematical structures

### Vector space

Provides addition and scalar multiplication.

### Normed vector space

Adds a norm measuring vector magnitude.

### Inner-product space

Adds an inner product, which induces a norm and provides geometric notions such as orthogonality.

### Banach space

A complete normed vector space.

### Hilbert space

A complete inner-product space.

Every Hilbert space is a Banach space under the norm induced by its inner product.

The reverse is not true. A Banach space does not necessarily have a norm generated by an inner product.

## Completeness

Completeness is the feature that distinguishes Hilbert spaces from arbitrary inner-product spaces.

A sequence \((x_n)\) is Cauchy if its elements eventually become arbitrarily close to one another:

\[
\forall\epsilon>0,\quad
\exists N
\]

such that

\[
m,n\geq N
\Rightarrow
\|x_n-x_m\|<\epsilon.
\]

A space is complete if every Cauchy sequence converges to an element of the space.

Therefore a Hilbert space satisfies:

\[
\text{inner-product structure}
+
\text{completeness}.
\]

The Python implementation uses finite prefixes of the sequence

\[
1,\frac12,\frac13,\ldots
\]

to illustrate convergence toward an element of \(\ell^2\).

The finite program cannot represent the infinite sequence exactly, so it uses increasingly long prefixes.

## Important distinction: finite versus infinite dimensions

Every finite-dimensional inner-product space over \(\mathbb{R}\) or \(\mathbb{C}\) is complete.

Therefore

\[
\mathbb{R}^n
\]

with the standard Euclidean inner product is a Hilbert space.

Infinite-dimensional spaces require more care.

Important examples include:

- \(\ell^2\), the square-summable sequence space
- \(L^2\), the square-integrable function space
- spaces of square-integrable signals
- certain spaces of solutions to differential equations

## Function-space Hilbert spaces

One of the most important aspects of Hilbert-space theory is that vectors do not have to be finite coordinate arrays.

A vector can be a function.

For \(L^2([a,b])\), the inner product is commonly written as

\[
\langle f,g\rangle
=
\int_a^b
\overline{f(x)}g(x)\,dx.
\]

The corresponding norm is

\[
\|f\|_2
=
\left(
\int_a^b |f(x)|^2dx
\right)^{1/2}.
\]

The Python and JavaScript implementations numerically approximate these integrals using the trapezoidal rule.

## Orthogonal functions

Functions can be orthogonal in exactly the same sense as vectors.

For example,

\[
\int_0^\pi
\sin(x)\cos(x)\,dx
=
0.
\]

Thus sine and cosine are orthogonal under the \(L^2([0,\pi])\) inner product.

This idea is central to Fourier analysis.

## Orthonormal systems

A set \(\{q_i\}\) is orthonormal when

\[
\langle q_i,q_j\rangle
=
\begin{cases}
1,&i=j,\\
0,&i\neq j.
\end{cases}
\]

An orthonormal basis provides coordinates without requiring a nontrivial Gram matrix.

If

\[
x=\sum_i c_iq_i,
\]

then

\[
c_i=\langle q_i,x\rangle.
\]

This simple coefficient formula is one of the most useful properties of Hilbert spaces.

## Span and basis

The span of vectors \(v_1,\ldots,v_k\) is the collection of all finite linear combinations:

\[
\operatorname{span}\{v_1,\ldots,v_k\}
=
\left\{
\sum_{i=1}^k c_iv_i
\right\}.
\]

A basis is a linearly independent spanning set.

An orthonormal basis is a basis whose elements are pairwise orthogonal and have norm one.

## Gram-Schmidt orthonormalization

The Gram-Schmidt process converts linearly independent vectors into an orthonormal basis for the same subspace.

Given \(v_1,\ldots,v_k\),

\[
u_1=v_1
\]

and

\[
q_1=\frac{u_1}{\|u_1\|}.
\]

For subsequent vectors,

\[
u_k
=
v_k-
\sum_{j=1}^{k-1}
\langle q_j,v_k\rangle q_j
\]

and

\[
q_k=
\frac{u_k}{\|u_k\|}.
\]

The Python, JavaScript, and C++ implementations all contain complete Gram-Schmidt implementations.

### Numerical limitation

Classical Gram-Schmidt is mathematically straightforward but can lose orthogonality when vectors are nearly linearly dependent.

For demanding numerical applications, modified Gram-Schmidt or Householder QR factorization is generally preferred.

The implementations explicitly reject vectors whose residual norm falls below a numerical tolerance.

## Orthogonal projection

Let \(M\) be a subspace of a Hilbert space and let \(x\) be a vector.

The orthogonal projection \(P_Mx\) is the element of \(M\) closest to \(x\).

If \(q_1,\ldots,q_k\) is an orthonormal basis for \(M\), then

\[
P_Mx
=
\sum_{i=1}^k
\langle q_i,x\rangle q_i.
\]

The residual is

\[
r=x-P_Mx.
\]

The residual satisfies

\[
r\perp M.
\]

Consequently,

\[
\langle q_i,r\rangle=0
\]

for every basis vector \(q_i\).

The Python, JavaScript, and C++ implementations explicitly check this property.

## Best approximation property

The projection satisfies

\[
\|x-P_Mx\|
\leq
\|x-y\|
\]

for every \(y\in M\).

Therefore orthogonal projection provides the best approximation in the Hilbert-space norm.

This is the geometric foundation of least-squares methods.

## Closed subspaces

For a closed subspace \(M\) of a Hilbert space \(H\), every \(x\in H\) has a unique orthogonal decomposition

\[
x=P_Mx+(x-P_Mx)
\]

where

\[
P_Mx\in M
\]

and

\[
x-P_Mx\in M^\perp.
\]

The closedness requirement is important in infinite-dimensional settings.

Finite-dimensional subspaces are automatically closed, so the projection theorem behaves particularly cleanly in the finite-dimensional implementations.

## Orthogonal complement

For a subset \(M\) of a Hilbert space,

\[
M^\perp
=
\{x\in H:\langle x,m\rangle=0
\text{ for every }m\in M\}.
\]

For an appropriate closed subspace,

\[
H=M\oplus M^\perp.
\]

This means every vector can be decomposed uniquely into a component in \(M\) and a component orthogonal to \(M\).

## Least squares

Suppose a data vector \(b\) cannot be represented exactly by the columns of a matrix \(A\).

The least-squares problem is

\[
\min_x\|Ax-b\|_2.
\]

Geometrically, the desired vector \(Ax\) is the orthogonal projection of \(b\) onto the column space of \(A\).

The Python and JavaScript implementations demonstrate this relationship with a simple linear-data example.

The C++ case study applies the same idea to signal reconstruction.

## Normal equations

The least-squares solution satisfies

\[
A^T(Ax-b)=0.
\]

Equivalently,

\[
A^TAx=A^Tb.
\]

These are the normal equations.

They express the orthogonality condition

\[
A^T(b-Ax)=0.
\]

Although the normal equations are mathematically useful, explicitly forming \(A^TA\) can worsen numerical conditioning. QR factorization is generally preferable for numerically sensitive least-squares problems.

The C++ implementation uses orthonormalization and projection rather than directly solving normal equations.

## Parseval's identity

For a complete orthonormal basis \(\{q_i\}\),

\[
\|x\|^2
=
\sum_i
|\langle q_i,x\rangle|^2.
\]

This is Parseval's identity.

It says that the total energy of a vector is exactly represented by the squared magnitudes of its orthonormal coordinates.

The Python and JavaScript implementations verify the finite-dimensional form.

## Bessel's inequality

For an arbitrary orthonormal set,

\[
\sum_i
|\langle q_i,x\rangle|^2
\leq
\|x\|^2.
\]

This is Bessel's inequality.

Equality occurs when the orthonormal set is complete for the relevant space.

In projection problems, the difference between total energy and coefficient energy is associated with the orthogonal residual.

## Fourier expansion

Fourier analysis represents functions using orthogonal or orthonormal trigonometric systems.

A normalized sine basis can be written as

\[
q_n(x)
=
\sqrt{\frac{2}{L}}
\sin\left(\frac{n\pi x}{L}\right).
\]

The coefficient of a function \(f\) is

\[
c_n
=
\langle q_n,f\rangle.
\]

A finite approximation is

\[
f_N(x)
=
\sum_{n=1}^{N}
c_nq_n(x).
\]

The Python and JavaScript implementations compute coefficients numerically and reconstruct a function from a finite number of basis elements.

## Function discretization

A continuous function-space problem can be approximated on a grid:

\[
x_0,x_1,\ldots,x_{N-1}.
\]

The function then becomes a finite vector

\[
[f(x_0),f(x_1),\ldots,f(x_{N-1})].
\]

This creates a bridge between infinite-dimensional Hilbert-space theory and finite-dimensional numerical computation.

The approximation introduces discretization error. Increasing the sampling resolution can reduce this error for sufficiently well-behaved functions, but numerical integration, floating-point precision, and sampling effects remain relevant.

## Riesz representation theorem

The Riesz representation theorem is one of the central results of Hilbert-space theory.

For every continuous linear functional \(F\) on a Hilbert space \(H\), there exists a unique \(y\in H\) such that

\[
F(x)=\langle y,x\rangle.
\]

In finite-dimensional Euclidean space, a functional such as

\[
F(x_1,x_2,x_3)
=
2x_1-x_2+3x_3
\]

can be represented using the vector

\[
y=(2,-1,3).
\]

Then

\[
F(x)=\langle y,x\rangle.
\]

The Python implementation demonstrates this finite-dimensional form.

## Linear operators

A linear operator \(T:H\rightarrow H\) satisfies

\[
T(ax+by)=aT(x)+bT(y).
\]

Operators generalize matrices from finite-dimensional spaces to function spaces and other infinite-dimensional settings.

Important operator classes include:

- bounded operators
- adjoint operators
- self-adjoint operators
- unitary operators
- compact operators
- projection operators

## Bounded operators

A linear operator \(T\) is bounded if there exists a constant \(C\) such that

\[
\|Tx\|\leq C\|x\|
\]

for every \(x\).

For linear operators between normed spaces, boundedness is equivalent to continuity.

The induced operator norm is

\[
\|T\|
=
\sup_{x\neq0}
\frac{\|Tx\|}{\|x\|}.
\]

The Python implementation estimates this quantity for a small matrix using random test vectors.

## Adjoint operator

For a bounded operator \(T\), the adjoint \(T^*\) is defined through

\[
\langle Tx,y\rangle
=
\langle x,T^*y\rangle.
\]

For a complex matrix, the adjoint is its conjugate transpose.

For a real matrix, it is simply the transpose.

## Self-adjoint operators

An operator is self-adjoint when

\[
T=T^*.
\]

A real symmetric matrix is self-adjoint under the standard Euclidean inner product.

Self-adjoint operators are particularly important because their spectral behavior has strong structure.

The Python implementation evaluates Rayleigh quotients for a symmetric matrix.

## Rayleigh quotient

For a nonzero vector \(x\),

\[
R_A(x)
=
\frac{\langle x,Ax\rangle}
{\langle x,x\rangle}.
\]

For self-adjoint operators, this value is real.

The Rayleigh quotient is important in eigenvalue analysis, optimization, numerical linear algebra, and variational methods.

## Unitary operators

An operator \(U\) is unitary if

\[
U^*U=I.
\]

Equivalently,

\[
\langle Ux,Uy\rangle
=
\langle x,y\rangle.
\]

Therefore

\[
\|Ux\|=\|x\|.
\]

Unitary transformations preserve Hilbert-space geometry.

In finite-dimensional real spaces, orthogonal matrices play the corresponding role.

## Projection operators

An orthogonal projection \(P\) satisfies

\[
P^2=P
\]

and

\[
P^*=P.
\]

The first property is idempotence: projecting an already projected vector changes nothing.

The second expresses orthogonality.

Projection operators are fundamental in approximation and signal processing.

## Weak and strong convergence

Strong convergence means

\[
\|x_n-x\|\rightarrow0.
\]

Weak convergence means

\[
\langle x_n,y\rangle
\rightarrow
\langle x,y\rangle
\]

for every fixed \(y\).

Strong convergence implies weak convergence.

In infinite-dimensional spaces, weak convergence can occur without strong convergence.

This distinction is important in functional analysis, optimization, partial differential equations, and variational analysis.

## Separable Hilbert spaces

A Hilbert space is separable if it contains a countable dense subset.

Separable Hilbert spaces admit countable orthonormal bases.

This property makes them especially suitable for computational representations because vectors can be described through countably many coordinates.

## C++ case study: signal reconstruction

The C++ implementation models a digital signal as an element of

\[
\mathbb{R}^N.
\]

With the standard inner product,

\[
\langle x,y\rangle
=
\sum_{n=0}^{N-1}x_ny_n,
\]

this finite-dimensional space is a Hilbert space.

The system performs the following operations:

1. Generate a clean signal.
2. Add bounded random noise.
3. Construct a model basis from known frequency components.
4. Orthonormalize the basis.
5. Project the noisy signal onto the model subspace.
6. Treat the projection as the reconstructed signal.
7. Treat the difference as the residual.
8. Measure reconstruction error.
9. Verify residual orthogonality.
10. Compare energy in the projection and residual.

### Signal model

The clean signal is composed of two sinusoidal components:

\[
s(t)
=
1.4\sin(2\pi f_1t)
+
0.6\cos(2\pi f_2t).
\]

The implementation uses frequencies 3 and 7 in the synthetic model.

Noise is generated using a deterministic pseudorandom generator so that program runs are reproducible.

### Model subspace

The basis contains sine and cosine components associated with the modeled frequencies.

The basis vectors are normalized before projection.

The orthonormalization stage ensures that coefficients can be computed directly as

\[
c_i=\langle q_i,x\rangle.
\]

### Reconstruction

For noisy signal \(x\), the reconstructed signal is

\[
\hat{x}
=
P_Mx.
\]

The residual is

\[
r=x-\hat{x}.
\]

The fundamental projection property is

\[
r\perp M.
\]

The C++ program explicitly calculates inner products between the residual and every orthonormal basis vector.

### Energy decomposition

Because the projection and residual are orthogonal,

\[
\|x\|^2
=
\|\hat{x}\|^2
+
\|r\|^2.
\]

This provides a numerical verification of the Pythagorean theorem in the signal-processing system.

### Reconstruction error

The C++ implementation calculates root mean squared error:

\[
RMSE
=
\sqrt{
\frac{1}{N}
\sum_{n=0}^{N-1}
(x_n-\hat{x}_n)^2
}.
\]

The comparison between noisy RMSE and reconstructed RMSE provides a direct numerical measure of approximation quality.

## Python implementation

The Python program provides the broadest mathematical progression.

It implements:

- vector addition
- vector subtraction
- scalar multiplication
- real and complex inner products
- norms
- distances
- orthogonality
- inner-product axioms
- Cauchy-Schwarz inequality
- triangle inequality
- Gram-Schmidt orthonormalization
- projection
- completeness demonstrations
- numerical \(L^2\) inner products
- function norms
- sine-basis expansion
- Riesz representation
- least squares
- orthogonal decomposition
- closed-subspace concepts
- Parseval's identity
- Bessel's inequality
- Rayleigh quotients
- bounded-operator concepts
- complex Hilbert-space geometry
- edge cases
- signal processing
- self-tests

The Python implementation emphasizes readability and direct correspondence between formulas and executable functions.

## JavaScript implementation

The JavaScript implementation focuses on application-oriented numerical programming.

It demonstrates:

- vector operations
- tolerance-based comparisons
- complex-number classes
- complex inner products
- Gram-Schmidt
- projection
- least squares
- numerical integration
- function-space approximation
- Fourier-like expansions
- an object-oriented `HilbertVector` abstraction
- input validation
- error handling
- performance measurement
- asynchronous computation
- browser DOM integration
- self-tests

The JavaScript implementation also illustrates an important language-level distinction: JavaScript does not provide a primitive complex-number type, so the example implements a small `Complex` class.

The browser demonstration is conditional on the availability of `document`, allowing the same source file to run in a Node.js environment without assuming browser APIs.

## C++ implementation

The C++ program is structured as a complete numerical case study rather than a collection of isolated mathematical demonstrations.

Its principal components are:

- `Vector`
- `Matrix`
- vector arithmetic
- inner products
- norms
- distance calculations
- orthogonality checks
- Gram-Schmidt
- projection
- matrix operations
- Fourier-like basis generation
- `Signal`
- synthetic signal generation
- noise generation
- basis construction
- reconstruction
- RMSE
- energy analysis
- finite-value validation
- dimension validation
- coefficient reporting
- self-tests

The program is organized under the `hilbert` namespace and uses standard C++17 facilities.

## Important distinctions

### Inner product versus norm

An inner product provides more information:

\[
\langle x,y\rangle.
\]

A norm provides magnitude:

\[
\|x\|.
\]

When a norm is induced by an inner product,

\[
\|x\|=\sqrt{\langle x,x\rangle}.
\]

Not every norm comes from an inner product.

### Banach space versus Hilbert space

A Banach space is complete with respect to its norm.

A Hilbert space is complete with respect to a norm induced by an inner product.

Thus Hilbert spaces have additional geometric structure.

### Orthogonal versus orthonormal

Orthogonal vectors satisfy

\[
\langle x,y\rangle=0.
\]

Orthonormal vectors additionally have unit norm:

\[
\|x\|=1.
\]

### Span versus closed span

The algebraic span contains finite linear combinations.

The closed span also contains limits of convergent sequences from the span.

This distinction becomes particularly important in infinite-dimensional spaces.

### Strong versus weak convergence

Strong convergence:

\[
\|x_n-x\|\rightarrow0.
\]

Weak convergence:

\[
\langle x_n,y\rangle
\rightarrow
\langle x,y\rangle
\]

for every \(y\).

The two notions agree in many finite-dimensional situations but differ significantly in infinite-dimensional analysis.

### Complete basis versus incomplete orthonormal set

A complete orthonormal basis gives Parseval's identity:

\[
\|x\|^2
=
\sum_i|\langle q_i,x\rangle|^2.
\]

An incomplete orthonormal set gives Bessel's inequality:

\[
\sum_i|\langle q_i,x\rangle|^2
\leq
\|x\|^2.
\]

## Edge cases

### Zero vector

The zero vector cannot be normalized because

\[
\|0\|=0
\]

and division by zero is undefined.

All implementations explicitly reject zero-vector normalization.

### Linearly dependent vectors

Gram-Schmidt cannot produce a new nonzero orthogonal direction from a vector already contained in the span of earlier vectors.

The implementations therefore detect a residual whose norm is below a tolerance.

### Nearly dependent vectors

Floating-point arithmetic makes numerical dependence different from exact mathematical dependence.

Vectors can be mathematically independent but numerically indistinguishable at a selected precision.

A tolerance is therefore required.

### Dimension mismatch

Operations such as addition and inner products require compatible dimensions.

The JavaScript and C++ implementations explicitly validate dimensions.

### Non-finite values

Numerical applications must handle NaN and infinity carefully.

A single non-finite value can contaminate an entire calculation.

The C++ signal-processing pipeline validates all signal samples before processing.

### Empty data

An empty vector cannot provide a meaningful signal norm or ordinary finite-dimensional Hilbert-space representation for these implementations.

The C++ and JavaScript abstractions reject empty inputs where appropriate.

## Numerical considerations

Mathematical equality and floating-point equality are different.

A mathematical result may be exactly

\[
\langle x,y\rangle=0
\]

while a computer produces a value such as

\[
2.1\times10^{-16}.
\]

Therefore numerical code should usually evaluate

\[
|a-b|\leq\epsilon
\]

instead of requiring `a === b`.

The value of the tolerance depends on scale, conditioning, algorithm, and floating-point precision.

## Gram-Schmidt stability

Classical Gram-Schmidt is conceptually simple:

\[
u_k
=
v_k-
\sum_j
\langle q_j,v_k\rangle q_j.
\]

Its numerical behavior can degrade when vectors are nearly linearly dependent.

Modified Gram-Schmidt changes the computational organization to reduce loss of orthogonality.

Householder QR is another important alternative for high-quality numerical linear algebra.

The implementations intentionally use classical Gram-Schmidt because its mathematical mechanism is transparent and closely matches the theory being taught.

## Performance considerations

For vectors of dimension \(n\):

- vector addition is \(O(n)\)
- subtraction is \(O(n)\)
- scalar multiplication is \(O(n)\)
- inner product is \(O(n)\)
- norm is \(O(n)\)
- projection onto \(k\) orthonormal vectors is approximately \(O(nk)\)

For \(k\) vectors of dimension \(n\), classical Gram-Schmidt is approximately

\[
O(nk^2).
\]

Dense matrix-vector multiplication for an \(n\times n\) matrix is

\[
O(n^2).
\]

Straightforward dense matrix multiplication is

\[
O(n^3).
\]

For large numerical systems, algorithm selection, memory layout, cache behavior, vectorization, sparse representations, and optimized linear-algebra libraries become important.

## Memory considerations

A dense vector of length \(n\) requires \(O(n)\) storage.

A dense \(n\times n\) matrix requires

\[
O(n^2)
\]

storage.

This difference becomes significant for large systems.

If an operator or signal has a sparse structure, sparse storage can reduce memory usage dramatically.

## Security and robustness considerations

Hilbert-space mathematics is not inherently a security technology, but software implementing numerical systems still requires defensive engineering.

Relevant concerns include:

- validating input dimensions
- rejecting NaN and infinity
- preventing invalid normalization
- detecting singular or nearly singular structures
- controlling resource consumption
- avoiding unchecked allocation sizes
- validating externally supplied numerical data
- using deterministic random seeds when reproducibility is required
- avoiding silent numerical failures

For applications processing untrusted input, dimensions and allocation requests should be bounded before memory-intensive operations begin.

## Practical applications

Hilbert spaces appear in many technical areas.

### Signal processing

Signals can be modeled as vectors or elements of \(L^2\).

Orthogonal projection can remove components outside a desired signal subspace.

Fourier expansions provide frequency-domain representations.

### Least-squares estimation

Observed data can be projected onto a model space.

This provides the mathematical basis for linear regression and many approximation methods.

### Quantum mechanics

Quantum states are represented using vectors in complex Hilbert spaces.

Observables are modeled by operators with strong structural properties, particularly self-adjoint operators.

### Partial differential equations

Function-space formulations of differential equations frequently use Hilbert spaces such as \(L^2\) and Sobolev spaces.

Orthogonal projection and variational formulations are central to numerical approximation methods.

### Fourier analysis

Fourier series and Fourier transforms rely heavily on orthogonality and inner-product structure.

### Statistics

Covariance structures, least-squares methods, principal component analysis, and projection methods have strong Hilbert-space interpretations.

### Machine learning

Many feature spaces can be viewed through inner products.

Kernel methods use inner-product-like structures and often connect to reproducing-kernel Hilbert spaces.

### Control systems

State spaces, operators, signal representations, and optimization problems can be formulated using Hilbert-space methods.

## Advanced mathematical perspective

The finite-dimensional computations represent only a small part of Hilbert-space theory.

Important advanced topics include:

- orthogonal decompositions
- projection theorems
- adjoint operators
- self-adjoint operators
- unitary operators
- compact operators
- spectral theory
- weak convergence
- weak compactness
- separability
- Riesz representation
- tensor-product Hilbert spaces
- reproducing-kernel Hilbert spaces
- Sobolev spaces
- variational methods
- spectral decompositions

These concepts extend the elementary geometry of vectors into functional analysis and operator theory.

## Mathematical structure represented by the implementations

The three implementations can be viewed as progressively different realizations of the same structure.

### Python

Python emphasizes mathematical transparency.

A vector is represented directly as a list, and each operation closely follows its mathematical definition.

Function-space operations are approximated through numerical integration.

### JavaScript

JavaScript emphasizes computational interfaces.

The `HilbertVector` class provides an object-oriented representation, while arrays and higher-order functions support numerical operations.

The browser demonstration connects mathematical projection with an event-driven user interface.

### C++

C++ emphasizes systems-level implementation.

The case study introduces explicit validation, strong data modeling, standard-library algorithms, deterministic signal generation, numerical diagnostics, complexity considerations, and error handling.

The result is a realistic example of how Hilbert-space geometry can support a computational signal-processing pipeline.

## Implementation correspondence

| Mathematical concept | Python | JavaScript | C++ |
|---|---|---|---|
| Vector | `list` | `Array` | `std::vector<double>` |
| Inner product | `inner_product()` | `realInnerProduct()` | `innerProduct()` |
| Norm | `norm()` | `vectorNorm()` | `norm()` |
| Distance | `distance()` | `vectorDistance()` | `distance()` |
| Orthogonality | `is_orthogonal()` | tolerance check | `orthogonal()` |
| Normalization | `normalize()` | `normalizeVector()` | `normalize()` |
| Orthonormalization | `gram_schmidt()` | `gramSchmidt()` | `gramSchmidt()` |
| Projection | `project_onto_subspace()` | `projectOntoSubspace()` | `projectOntoOrthonormalBasis()` |
| Function space | numerical integration | trapezoidal integration | sampled signals |
| Fourier-like expansion | sine basis | sine basis | signal basis |
| Least squares | QR-like projection | projection | projection |
| Testing | `run_tests()` | `runTests()` | `runTests()` |
| Application | signal example | browser/numerical example | signal reconstruction system |

## Running the implementations

### Python

The Python source uses the standard library only.

Run it with a modern Python 3 interpreter.

The program executes the demonstrations sequentially and finishes with a self-test suite.

### JavaScript

The JavaScript source uses standard JavaScript functionality and requires no external npm package.

It can be executed in a modern Node.js runtime.

The browser-specific demonstration activates only when `document` is available.

### C++

The C++ program is designed for C++17 or later.

A standard compilation command is conceptually equivalent to compiling the source with C++17 support and then executing the resulting program.

The program reports validation failures through exceptions and returns a nonzero status if an unexpected error occurs.

## Conceptual relationship between projection and reconstruction

The central computational pattern in the C++ case study is

\[
x
=
P_Mx+
(I-P_M)x.
\]

Here:

- \(x\) is the observed signal
- \(P_Mx\) is the component represented by the model subspace
- \((I-P_M)x\) is the residual
- \(I\) is the identity operator

Because the two components are orthogonal,

\[
\langle P_Mx,(I-P_M)x\rangle=0.
\]

This gives

\[
\|x\|^2
=
\|P_Mx\|^2+
\|(I-P_M)x\|^2.
\]

The same geometric principle appears in linear regression, Fourier approximation, signal filtering, and many optimization problems.

## Limitations of the implementations

The implementations are educational numerical models rather than general-purpose functional-analysis systems.

The principal limitations are:

- infinite-dimensional spaces are represented through finite approximations
- numerical integration introduces discretization error
- floating-point arithmetic introduces rounding error
- classical Gram-Schmidt can lose numerical orthogonality
- the C++ signal model assumes a known family of basis functions
- the JavaScript implementation uses real arrays for most numerical operations
- no implementation provides a general-purpose arbitrary-precision numerical system
- no implementation attempts to prove mathematical completeness computationally

These limitations do not alter the mathematical definitions. They describe the difference between an abstract mathematical object and a finite numerical representation.

## Core formulas

The principal formulas implemented or discussed in the project are:

\[
\langle x,y\rangle
=
\sum_i\overline{x_i}y_i
\]

\[
\|x\|
=
\sqrt{\langle x,x\rangle}
\]

\[
d(x,y)
=
\|x-y\|
\]

\[
x\perp y
\iff
\langle x,y\rangle=0
\]

\[
P_Mx
=
\sum_i
\langle q_i,x\rangle q_i
\]

\[
x=P_Mx+(x-P_Mx)
\]

\[
x-P_Mx\perp M
\]

\[
\|x\|^2
=
\|P_Mx\|^2+
\|x-P_Mx\|^2
\]

\[
|\langle x,y\rangle|
\leq
\|x\|\|y\|
\]

\[
\|x+y\|^2+\|x-y\|^2
=
2\|x\|^2+2\|y\|^2
\]

\[
\sum_i
|\langle q_i,x\rangle|^2
\leq
\|x\|^2
\]

and, for a complete orthonormal basis,

\[
\sum_i
|\langle q_i,x\rangle|^2
=
\|x\|^2.
\]

These identities connect the elementary geometry of finite-dimensional vectors with the general framework of Hilbert-space mathematics.
