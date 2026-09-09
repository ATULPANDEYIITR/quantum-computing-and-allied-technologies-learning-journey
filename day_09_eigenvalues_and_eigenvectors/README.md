# Eigenvalues & Eigenvectors: Quantum-State Applications

## Introduction

Eigenvalues and eigenvectors are fundamental concepts in linear algebra. They describe directions that a linear transformation preserves while changing their scale by a corresponding eigenvalue.

For a square matrix \(A\), an eigenvector \(v\neq 0\) and eigenvalue \(\lambda\) satisfy

\[
Av=\lambda v.
\]

This relationship becomes particularly important in quantum mechanics because quantum states are vectors in a complex Hilbert space, while physical observables are represented by Hermitian operators. The eigenvalues of an observable correspond to possible measurement outcomes, and its eigenvectors define the associated measurement states.

The accompanying Python script develops the subject progressively. It begins with elementary vectors and matrices, constructs the eigenvalue problem explicitly, and then connects eigenvalues and eigenvectors to quantum states, projective measurement, Pauli operators, Hamiltonians, time evolution, Bloch-sphere coordinates, tensor products, Bell states, density matrices, entropy, commutators, and unitary quantum gates.

The implementation deliberately uses the Python standard library rather than relying on a numerical linear-algebra package. This exposes the mathematical mechanisms directly. The resulting algorithms are educational implementations and are not intended to replace optimized numerical eigensolvers for large matrices.

---

## 1. Vectors and Matrices

A vector can be represented as an ordered collection of numbers. In quantum mechanics, vectors are generally complex-valued.

For example,

\[
|\psi\rangle =
\begin{bmatrix}
\alpha\\
\beta
\end{bmatrix}
\]

is a general two-dimensional state vector.

A matrix represents a linear transformation:

\[
A=
\begin{bmatrix}
a & b\\
c & d
\end{bmatrix}.
\]

Multiplication of a matrix by a vector produces another vector:

\[
A|\psi\rangle.
\]

The script implements:

- vector addition
- vector subtraction
- scalar multiplication
- matrix addition
- matrix subtraction
- matrix multiplication
- matrix-vector multiplication
- transpose
- conjugate transpose
- trace
- determinant
- matrix powers

These operations form the computational foundation for the later quantum examples.

---

## 2. Complex Inner Products

For real vectors, the ordinary dot product is sufficient. Quantum mechanics requires a complex inner product.

For vectors \(a\) and \(b\),

\[
\langle a|b\rangle
=
\sum_i a_i^*b_i,
\]

where \(a_i^*\) denotes complex conjugation.

The complex conjugation of the first vector is essential.

The norm of a vector is

\[
\|v\|=\sqrt{\langle v|v\rangle}.
\]

A quantum state must satisfy

\[
\langle\psi|\psi\rangle=1.
\]

The script therefore provides explicit normalization functionality.

A zero vector cannot be normalized because its norm is zero.

---

## 3. Eigenvalues and Eigenvectors

An eigenvector is a nonzero vector whose direction is preserved by a linear transformation:

\[
Av=\lambda v.
\]

Here:

- \(A\) is the matrix or operator
- \(v\) is the eigenvector
- \(\lambda\) is the eigenvalue

The transformation does not necessarily leave the vector numerically unchanged. It multiplies it by \(\lambda\).

For example, if

\[
A=
\begin{bmatrix}
3&0\\
0&2
\end{bmatrix},
\]

then

\[
A
\begin{bmatrix}
1\\
0
\end{bmatrix}
=
3
\begin{bmatrix}
1\\
0
\end{bmatrix}.
\]

Thus,

\[
\lambda=3
\]

and

\[
v=
\begin{bmatrix}
1\\
0
\end{bmatrix}
\]

form an eigenpair.

The eigenvalue equation is central to quantum-state applications because many physically meaningful quantities are defined through eigenvalue problems.

---

## 4. Characteristic Equation

To determine eigenvalues, start with

\[
Av=\lambda v.
\]

Rearranging gives

\[
(A-\lambda I)v=0.
\]

For a nonzero solution \(v\) to exist, the matrix \(A-\lambda I\) must be singular. Therefore,

\[
\det(A-\lambda I)=0.
\]

This is the characteristic equation.

For

\[
A=
\begin{bmatrix}
a&b\\
c&d
\end{bmatrix},
\]

the characteristic polynomial can be written as

\[
\lambda^2-\operatorname{tr}(A)\lambda+\det(A)=0.
\]

The script implements the determinant recursively and uses the quadratic formula for the \(2\times2\) eigenvalue problem.

For larger matrices, recursive determinant expansion is computationally inefficient. Numerical software generally uses specialized factorizations and eigensolvers instead.

---

## 5. Computing Eigenvectors

Once an eigenvalue \(\lambda\) has been obtained, substitute it into

\[
(A-\lambda I)v=0.
\]

The resulting homogeneous system determines the corresponding eigenspace.

For a simple eigenvalue in a \(2\times2\) matrix, the eigenspace is usually one-dimensional. Any nonzero scalar multiple of an eigenvector is also an eigenvector.

For quantum mechanics, eigenvectors are commonly normalized so that

\[
\langle v|v\rangle=1.
\]

The script computes normalized eigenvectors for \(2\times2\) matrices and evaluates the residual

\[
\|Av-\lambda v\|.
\]

A small residual indicates that the computed eigenpair approximately satisfies the defining equation.

---

## 6. Algebraic and Geometric Multiplicity

Repeated eigenvalues require special care.

The **algebraic multiplicity** is the number of times an eigenvalue occurs as a root of the characteristic polynomial.

The **geometric multiplicity** is the dimension of the corresponding eigenspace.

For example,

\[
A=
\begin{bmatrix}
5&0\\
0&5
\end{bmatrix}
\]

has eigenvalue \(5\) with algebraic multiplicity two. Its eigenspace is also two-dimensional because every vector satisfies

\[
Av=5v.
\]

A repeated eigenvalue does not guarantee that every matrix is proportional to the identity. Some matrices have repeated eigenvalues but insufficiently many linearly independent eigenvectors.

In quantum mechanics, degeneracy means that multiple independent states correspond to the same measurement value.

---

## 7. Hermitian Matrices

The conjugate transpose of a matrix is denoted by

\[
A^\dagger.
\]

A matrix is Hermitian if

\[
A^\dagger=A.
\]

Hermitian operators are especially important in quantum mechanics because physical observables are represented by Hermitian operators.

For example,

\[
A=
\begin{bmatrix}
2&1-2i\\
1+2i&5
\end{bmatrix}
\]

is Hermitian.

Important properties of Hermitian matrices include:

1. Eigenvalues are real.
2. Eigenvectors belonging to distinct eigenvalues are orthogonal.
3. A Hermitian matrix can be diagonalized using a unitary matrix.
4. Its eigenspaces provide an orthogonal decomposition of the underlying space.

The reality of eigenvalues is crucial because physical measurement results must be real numbers.

---

## 8. The Spectral Theorem

For a Hermitian matrix,

\[
A=UDU^\dagger,
\]

where:

- \(U\) contains orthonormal eigenvectors
- \(D\) is diagonal
- the diagonal entries of \(D\) are eigenvalues
- \(U^\dagger U=I\)

An equivalent projector form is

\[
A=\sum_i\lambda_iP_i,
\]

where \(P_i\) is the projector onto the eigenspace associated with \(\lambda_i\).

For distinct eigenvalues of a \(2\times2\) matrix, the script constructs projectors directly using

\[
P_1=
\frac{A-\lambda_2I}
{\lambda_1-\lambda_2}
\]

and

\[
P_2=
\frac{A-\lambda_1I}
{\lambda_2-\lambda_1}.
\]

This representation becomes directly useful for understanding quantum measurement.

---

## 9. Quantum States

A pure quantum state is represented by a normalized vector.

For a qubit,

\[
|\psi\rangle=
\alpha|0\rangle+\beta|1\rangle,
\]

where

\[
|\alpha|^2+|\beta|^2=1.
\]

The computational basis is

\[
|0\rangle=
\begin{bmatrix}
1\\
0
\end{bmatrix},
\qquad
|1\rangle=
\begin{bmatrix}
0\\
1
\end{bmatrix}.
\]

The coefficients \(\alpha\) and \(\beta\) are probability amplitudes, not probabilities themselves.

The corresponding probabilities are

\[
P(0)=|\alpha|^2
\]

and

\[
P(1)=|\beta|^2.
\]

The script explicitly demonstrates normalization and calculates computational-basis measurement probabilities.

---

## 10. Born Rule

If a normalized state \(|\psi\rangle\) is measured in an orthonormal basis containing \(|\phi\rangle\), the amplitude for obtaining that outcome is

\[
\langle\phi|\psi\rangle.
\]

The probability is

\[
P(\phi)=|\langle\phi|\psi\rangle|^2.
\]

This is the Born rule.

The script separates the amplitude calculation from the probability calculation so that the distinction is visible.

A common mistake is to interpret a complex amplitude directly as a probability. Probabilities are real and nonnegative. The squared magnitude of an amplitude gives the probability.

---

## 11. Bra-Ket Notation

Quantum mechanics frequently uses Dirac notation.

A ket

\[
|\psi\rangle
\]

represents a column vector.

Its corresponding bra is

\[
\langle\psi|
\]

and is obtained through conjugate transpose.

The inner product is

\[
\langle\phi|\psi\rangle.
\]

An outer product is

\[
|\psi\rangle\langle\phi|.
\]

The script implements outer products explicitly.

---

## 12. Projectors

For a normalized state \(|v\rangle\), the rank-one projector is

\[
P=|v\rangle\langle v|.
\]

A projector satisfies

\[
P^2=P.
\]

If the state is \(|\psi\rangle\), then

\[
\langle\psi|P|\psi\rangle
\]

is the probability that the state is projected onto that one-dimensional subspace.

For the computational state \(|0\rangle\),

\[
P_0=|0\rangle\langle0|
=
\begin{bmatrix}
1&0\\
0&0
\end{bmatrix}.
\]

The script demonstrates how a measurement probability can be computed directly as the expectation value of a projector.

---

## 13. Expectation Values

For an observable \(A\) and state \(|\psi\rangle\),

\[
\langle A\rangle
=
\langle\psi|A|\psi\rangle.
\]

The expectation value is the average measurement result obtained over many repetitions of the same experiment.

If the observable has eigenvalues \(\lambda_i\) and corresponding projectors \(P_i\), then

\[
\langle A\rangle
=
\sum_i\lambda_i p_i,
\]

where

\[
p_i=\langle\psi|P_i|\psi\rangle.
\]

The script calculates the expectation value both directly and as a probability-weighted eigenvalue average.

---

## 14. Observables and Eigenvalues

A quantum observable is represented by a Hermitian operator.

Suppose

\[
A|a_i\rangle=a_i|a_i\rangle.
\]

Then:

- \(a_i\) is a possible measurement result
- \(|a_i\rangle\) is the corresponding eigenstate

This provides the direct physical interpretation of the eigenvalue problem.

The mathematical equation

\[
A|a_i\rangle=a_i|a_i\rangle
\]

is therefore not just a computational technique. It identifies the possible outcomes and states associated with a quantum measurement.

---

## 15. Pauli Matrices

The three Pauli matrices are

\[
X=
\begin{bmatrix}
0&1\\
1&0
\end{bmatrix},
\]

\[
Y=
\begin{bmatrix}
0&-i\\
i&0
\end{bmatrix},
\]

and

\[
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}.
\]

They are all Hermitian and unitary.

Their eigenvalues are

\[
+1,\,-1.
\]

Important eigenstates include

\[
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt2},
\]

\[
|-\rangle=\frac{|0\rangle-|1\rangle}{\sqrt2},
\]

and the \(Y\)-basis states

\[
|+y\rangle
=
\frac{|0\rangle+i|1\rangle}{\sqrt2},
\]

\[
|-y\rangle
=
\frac{|0\rangle-i|1\rangle}{\sqrt2}.
\]

The computational states \(|0\rangle\) and \(|1\rangle\) are eigenstates of \(Z\).

The states \(|+\rangle\) and \(|-\rangle\) are eigenstates of \(X\).

The \(Y\)-basis states are eigenstates of \(Y\).

---

## 16. Measurement Basis

The physical state does not change merely because a different basis is chosen to describe or measure it.

For example, \(|0\rangle\) produces:

- certainty for the \(Z\)-basis outcome \(+1\)
- equal probabilities for the two \(X\)-basis outcomes
- equal probabilities for the two \(Y\)-basis outcomes

This illustrates why measurement probabilities depend on the relationship between the state and the measurement eigenbasis.

The script calculates these probabilities explicitly.

---

## 17. Hamiltonians and Energy Eigenstates

The Hamiltonian \(H\) represents the energy observable of a quantum system.

The eigenvalue equation is

\[
H|E\rangle=E|E\rangle.
\]

Here:

- \(H\) is the Hamiltonian
- \(E\) is a possible energy
- \(|E\rangle\) is the corresponding energy eigenstate

For a diagonal Hamiltonian,

\[
H=
\begin{bmatrix}
E_0&0\\
0&E_1
\end{bmatrix},
\]

the computational basis states are already energy eigenstates.

The script also includes a nontrivial two-level Hamiltonian with off-diagonal coupling. In such a system, the energy eigenstates are generally superpositions of the computational basis states.

---

## 18. Time Evolution

The time-evolution operator for a time-independent Hamiltonian is

\[
U(t)=e^{-iHt/\hbar}.
\]

The state evolves according to

\[
|\psi(t)\rangle
=
U(t)|\psi(0)\rangle.
\]

If \(|E\rangle\) is an energy eigenstate,

\[
|\psi(t)\rangle
=
e^{-iEt/\hbar}|E\rangle.
\]

Only a phase changes.

The corresponding measurement probabilities remain unchanged.

The script approximates the matrix exponential using the series

\[
e^A=
I+A+\frac{A^2}{2!}
+\frac{A^3}{3!}+\cdots.
\]

This is useful for demonstrating the mathematical definition but is not the preferred production algorithm for large or difficult matrices.

---

## 19. Unitary Operators

A matrix \(U\) is unitary if

\[
U^\dagger U=I.
\]

Unitary transformations preserve inner products and therefore preserve norms.

Quantum gates and closed-system time evolution are represented by unitary operators.

The script verifies unitarity for:

- Pauli \(X\)
- Pauli \(Y\)
- Pauli \(Z\)
- Hadamard
- phase gate
- \(T\) gate

---

## 20. Hadamard Gate

The Hadamard operator is

\[
H=
\frac{1}{\sqrt2}
\begin{bmatrix}
1&1\\
1&-1
\end{bmatrix}.
\]

Its action on \(|0\rangle\) is

\[
H|0\rangle
=
\frac{|0\rangle+|1\rangle}{\sqrt2}
=
|+\rangle.
\]

This demonstrates a direct connection between matrix operations, eigenstates, and quantum superposition.

---

## 21. Bloch Sphere

Every pure qubit state can be represented geometrically by a point on the Bloch sphere.

The Cartesian coordinates are

\[
x=\langle X\rangle,
\]

\[
y=\langle Y\rangle,
\]

\[
z=\langle Z\rangle.
\]

For a pure state,

\[
x^2+y^2+z^2=1.
\]

The script calculates Bloch coordinates for several standard states.

Important examples include:

- \(|0\rangle\): north pole
- \(|1\rangle\): south pole
- \(|+\rangle\): positive \(x\)-axis
- \(|-\rangle\): negative \(x\)-axis
- \(|+y\rangle\): positive \(y\)-axis
- \(|-y\rangle\): negative \(y\)-axis

The Bloch representation provides an intuitive geometric interpretation of eigenstates of the Pauli operators.

---

## 22. Global Phase and Relative Phase

Quantum states are physically equivalent under multiplication by a global phase:

\[
|\psi\rangle
\sim
e^{i\theta}|\psi\rangle.
\]

The global phase does not change measurement probabilities.

The script tests physical equivalence up to global phase.

This should not be confused with relative phase.

For example,

\[
\frac{|0\rangle+|1\rangle}{\sqrt2}
\]

and

\[
\frac{|0\rangle+i|1\rangle}{\sqrt2}
\]

are not equivalent merely by a global phase.

Relative phase affects interference and therefore has observable consequences.

---

## 23. Orthogonality of Eigenvectors

For a Hermitian operator, eigenvectors corresponding to distinct eigenvalues are orthogonal.

If

\[
A|u\rangle=\lambda_u|u\rangle
\]

and

\[
A|v\rangle=\lambda_v|v\rangle
\]

with

\[
\lambda_u\neq\lambda_v,
\]

then

\[
\langle u|v\rangle=0.
\]

After normalization, such eigenvectors form orthonormal measurement bases.

This property is one reason Hermitian operators are so useful in quantum theory.

---

## 24. Trace and Determinant

Eigenvalues are closely related to two important matrix invariants.

For a square matrix,

\[
\operatorname{tr}(A)
=
\sum_i\lambda_i.
\]

The determinant satisfies

\[
\det(A)
=
\prod_i\lambda_i.
\]

Eigenvalues are counted according to algebraic multiplicity.

For a \(2\times2\) matrix, these relationships are directly visible in the characteristic polynomial.

The script checks both relationships numerically.

---

## 25. Tensor Products

A multi-qubit Hilbert space is constructed using tensor products.

For two qubits,

\[
|00\rangle
=
|0\rangle\otimes|0\rangle.
\]

The dimension changes multiplicatively:

\[
2\times2=4.
\]

For \(n\) qubits,

\[
\dim(\mathcal H)=2^n.
\]

The script implements tensor products for both vectors and matrices.

For example,

\[
X\otimes X
\]

is a four-dimensional operator acting on two qubits.

The exponential growth of Hilbert-space dimension is one of the main computational challenges in classical simulation of quantum systems.

---

## 26. Bell States

The four Bell states are

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2},
\]

\[
|\Phi^-\rangle
=
\frac{|00\rangle-|11\rangle}{\sqrt2},
\]

\[
|\Psi^+\rangle
=
\frac{|01\rangle+|10\rangle}{\sqrt2},
\]

\[
|\Psi^-\rangle
=
\frac{|01\rangle-|10\rangle}{\sqrt2}.
\]

These states are entangled.

The script demonstrates that Bell states are eigenstates of commuting two-qubit operators such as

\[
X\otimes X
\]

and

\[
Z\otimes Z.
\]

This is an important example of eigenvectors providing a natural basis for analyzing multi-qubit correlations.

---

## 27. Commutators

The commutator of two operators is

\[
[A,B]=AB-BA.
\]

If

\[
[A,B]=0,
\]

the operators commute.

Commuting observables can generally be simultaneously diagonalized under appropriate mathematical conditions.

For the Pauli matrices,

\[
[X,Y]\neq0.
\]

The script calculates the commutators explicitly.

Noncommutativity is fundamental to quantum mechanics because it means that different observables need not have a common eigenbasis.

---

## 28. Simultaneous Eigenstates

The script uses

\[
X\otimes X
\]

and

\[
Z\otimes Z
\]

as an example of commuting multi-qubit observables.

The Bell states can be chosen as simultaneous eigenstates of these operators.

This provides a concrete relationship between:

- commuting operators
- common eigenvectors
- compatible measurements
- entangled states
- multi-qubit quantum systems

The idea is also central to stabilizer-based descriptions of quantum states.

---

## 29. Density Matrices

A pure state \(|\psi\rangle\) can be represented by

\[
\rho=|\psi\rangle\langle\psi|.
\]

For a pure state,

\[
\rho^2=\rho
\]

and

\[
\operatorname{Tr}(\rho^2)=1.
\]

A mixed state is represented by a probabilistic mixture,

\[
\rho=\sum_i p_i|\psi_i\rangle\langle\psi_i|.
\]

A maximally mixed qubit has

\[
\rho=
\frac12
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}.
\]

Its purity is

\[
\operatorname{Tr}(\rho^2)=\frac12.
\]

The density-matrix formalism extends the state-vector framework to statistical mixtures and subsystems of larger quantum systems.

---

## 30. Density-Matrix Expectation Values

For a density matrix,

\[
\langle A\rangle
=
\operatorname{Tr}(\rho A).
\]

This generalizes

\[
\langle\psi|A|\psi\rangle
\]

to mixed states.

The script evaluates the expectation values of the Pauli matrices for a density matrix corresponding to \(|+\rangle\).

---

## 31. Von Neumann Entropy

The von Neumann entropy is

\[
S(\rho)
=
-\operatorname{Tr}(\rho\log_2\rho).
\]

If the eigenvalues of \(\rho\) are \(p_i\), this becomes

\[
S(\rho)
=
-\sum_i p_i\log_2p_i.
\]

The script calculates entropy from the eigenvalues of a \(2\times2\) Hermitian density matrix.

For a pure state,

\[
S=0.
\]

For a maximally mixed qubit,

\[
S=1
\]

bit.

This demonstrates another major application of eigenvalues: many properties of a density matrix can be determined from its spectrum.

---

## 32. Spectra and Matrix Functions

If an operator has spectral decomposition

\[
A=\sum_i\lambda_iP_i,
\]

then a function of the operator can be written as

\[
f(A)=\sum_i f(\lambda_i)P_i.
\]

For example,

\[
e^{-iHt}
=
\sum_i e^{-iE_it}P_i.
\]

This provides a powerful connection between eigenvalues and quantum dynamics.

The script uses spectral projectors to construct matrix functions for a \(2\times2\) Hermitian operator.

---

## 33. Measurement Through Spectral Projectors

If an observable has spectral decomposition

\[
A=\sum_i a_iP_i,
\]

then the projective measurement associated with \(A\) has probabilities

\[
p_i
=
\langle\psi|P_i|\psi\rangle.
\]

The eigenvalues \(a_i\) are the possible measurement outcomes.

The projectors specify the corresponding measurement subspaces.

For nondegenerate eigenvalues, each projector may be rank one. For degenerate eigenvalues, the corresponding projector can have rank greater than one.

---

## 34. Degeneracy in Quantum Measurements

Suppose an observable has a repeated eigenvalue.

The measurement outcome associated with that eigenvalue does not necessarily identify one unique state. It identifies an eigenspace.

For a degenerate eigenvalue \(\lambda\),

\[
A|\psi\rangle=\lambda|\psi\rangle
\]

for every state in the associated eigenspace.

The physically meaningful object is therefore the projector onto that eigenspace rather than one arbitrarily chosen eigenvector.

This distinction is particularly important in numerical implementations because eigenvectors inside a degenerate subspace are not uniquely determined.

---

## 35. Variance and Measurement Uncertainty

The variance of an observable is

\[
\operatorname{Var}(A)
=
\langle A^2\rangle
-
\langle A\rangle^2.
\]

An eigenstate of \(A\) has zero variance.

If

\[
A|\psi\rangle=a|\psi\rangle,
\]

then every measurement produces \(a\), so there is no statistical spread.

The script demonstrates this property using the Pauli \(X\) and \(Z\) operators.

---

## 36. Power Iteration

The script also demonstrates a basic numerical eigenvalue method called power iteration.

Starting with a vector \(v_0\),

\[
v_{k+1}
=
\frac{Av_k}{\|Av_k\|}.
\]

When the matrix has a unique dominant eigenvalue in magnitude, repeated application tends to align the vector with its corresponding eigenvector.

The Rayleigh quotient

\[
\lambda
\approx
\frac{\langle v|Av\rangle}
{\langle v|v\rangle}
\]

provides an eigenvalue estimate.

Power iteration has important limitations:

- it generally targets the dominant eigenvalue
- convergence can be slow
- close eigenvalue magnitudes can cause slow convergence
- repeated dominant eigenvalues can prevent unique convergence
- an unfortunate initial vector can eliminate useful components
- it is not a general-purpose eigensolver

It is valuable primarily for understanding iterative eigenvalue computation.

---

## 37. Numerical Residuals

Floating-point arithmetic introduces small numerical errors.

For a computed eigenpair \((\lambda,v)\), a useful validation quantity is

\[
r=Av-\lambda v.
\]

The residual norm is

\[
\|r\|.
\]

A small residual indicates that the computed pair approximately satisfies the eigenvalue equation.

Exact equality checks are generally inappropriate for floating-point results.

The script uses tolerances and residual norms instead.

---

## 38. Numerical Stability

Several numerical issues are relevant to eigenvalue calculations.

### Floating-point rounding

Numbers such as

\[
\frac{1}{\sqrt2}
\]

cannot generally be represented exactly in binary floating-point arithmetic.

### Nearly degenerate eigenvalues

When eigenvalues are extremely close, eigenvectors can become numerically sensitive.

### Ill-conditioned problems

Small perturbations in the input matrix can sometimes cause large changes in computed eigenvectors.

### Degenerate subspaces

When an eigenvalue is repeated, individual eigenvectors are not unique. Numerical algorithms may return different orthonormal bases for the same eigenspace.

### Residual versus exact equality

A small residual is usually a more meaningful numerical correctness test than direct equality.

---

## 39. Production Implementation Considerations

The educational implementations in the script are intentionally simple.

The recursive determinant implementation has poor scalability. Its purpose is to make the definition

\[
\det(A)
\]

visible rather than to provide a high-performance determinant routine.

Similarly, the matrix exponential series is suitable for demonstrating

\[
e^A
\]

but is not a general production-quality matrix exponential algorithm.

Large-scale numerical linear algebra generally relies on specialized algorithms designed for stability, efficiency, and particular matrix structures.

For Hermitian or real symmetric matrices, specialized eigensolvers can exploit their mathematical properties.

The choice of algorithm should consider:

- matrix dimension
- sparsity
- symmetry or Hermiticity
- whether all eigenvalues are required
- whether only a few eigenvalues are required
- conditioning
- memory requirements
- required numerical precision

---

## 40. Security and Simulation Considerations

The mathematical calculations themselves are not normally security-sensitive, but implementations can become security-relevant when used inside cryptographic or quantum-information systems.

Several distinctions matter.

### Pseudorandom measurement simulation

The script uses Python's ordinary pseudorandom generator to simulate measurement outcomes. This is suitable for educational sampling but should not automatically be treated as cryptographically secure randomness.

### Input validation

Matrix dimensions, normalization, Hermiticity, probability sums, and numerical ranges should be validated before computation.

### Numerical assumptions

A program should not silently assume that a matrix is Hermitian simply because it is intended to represent an observable. The implementation should check the property when correctness depends on it.

### Complex values

Discarding imaginary components without justification can change the physical interpretation of a calculation.

---

## 41. Quantum Measurement Simulation

The script samples measurement outcomes according to calculated Born probabilities.

For a state

\[
|\psi\rangle
=
\alpha|0\rangle+\beta|1\rangle,
\]

the theoretical probabilities are

\[
P(0)=|\alpha|^2,
\qquad
P(1)=|\beta|^2.
\]

Repeated simulated measurements produce empirical frequencies that approach the theoretical probabilities as the number of trials increases.

This connects the deterministic linear-algebra calculation with the probabilistic nature of quantum measurement.

---

## 42. Common Mistakes

### Treating eigenvectors as unique

If \(v\) is an eigenvector, then

\[
cv
\]

is also an eigenvector for any nonzero scalar \(c\).

Quantum states add another equivalence: multiplication by a global phase does not change the physical pure state.

### Forgetting complex conjugation

The inner product is not simply

\[
\sum_i a_i b_i.
\]

It is

\[
\sum_i a_i^*b_i.
\]

### Confusing amplitudes and probabilities

The amplitude is

\[
\langle\phi|\psi\rangle.
\]

The probability is

\[
|\langle\phi|\psi\rangle|^2.
\]

### Assuming every matrix is an observable

A quantum observable must be Hermitian.

### Assuming eigenvalues are always real

General complex matrices can have complex eigenvalues. Reality is guaranteed for Hermitian operators.

### Normalizing incorrectly

A quantum state must satisfy

\[
\langle\psi|\psi\rangle=1.
\]

### Using exact floating-point comparisons

Numerical computations should normally use tolerances.

### Ignoring degeneracy

For degenerate eigenvalues, the eigenspace rather than an individual eigenvector is the important mathematical object.

### Confusing global and relative phase

Global phase is physically irrelevant for an isolated pure state, while relative phase affects interference.

---

## 43. Important Distinctions

| Concept | Meaning |
|---|---|
| Eigenvalue | Scalar multiplying an eigenvector under a transformation |
| Eigenvector | Nonzero vector satisfying \(Av=\lambda v\) |
| Eigenspace | Set of all eigenvectors associated with an eigenvalue, together with the zero vector |
| Hermitian operator | Operator satisfying \(A^\dagger=A\) |
| Observable | Hermitian operator representing a measurable quantity |
| Quantum state | Normalized vector for a pure state |
| Amplitude | Complex number such as \(\langle\phi|\psi\rangle\) |
| Probability | Squared magnitude of an amplitude |
| Projector | Operator representing projection onto a subspace |
| Hamiltonian | Operator representing energy |
| Unitary operator | Operator satisfying \(U^\dagger U=I\) |
| Density matrix | Operator representing pure or mixed quantum states |
| Pure state | State with density-matrix purity equal to one |
| Mixed state | Statistical mixture with purity below one |
| Degeneracy | Multiple independent states sharing an eigenvalue |
| Spectrum | Collection of eigenvalues of an operator |

---

## 44. Key Mathematical Relationships

The script repeatedly uses the following relationships.

### Eigenvalue equation

\[
Av=\lambda v
\]

### Characteristic equation

\[
\det(A-\lambda I)=0
\]

### Normalization

\[
\langle\psi|\psi\rangle=1
\]

### Born probability

\[
p_i=|\langle\phi_i|\psi\rangle|^2
\]

### Expectation value

\[
\langle A\rangle
=
\langle\psi|A|\psi\rangle
\]

### Density-matrix expectation value

\[
\langle A\rangle
=
\operatorname{Tr}(\rho A)
\]

### Projector

\[
P=|v\rangle\langle v|
\]

### Hermiticity

\[
A^\dagger=A
\]

### Unitarity

\[
U^\dagger U=I
\]

### Time evolution

\[
U(t)=e^{-iHt/\hbar}
\]

### Commutator

\[
[A,B]=AB-BA
\]

### Variance

\[
\operatorname{Var}(A)
=
\langle A^2\rangle-\langle A\rangle^2
\]

### Purity

\[
\operatorname{Tr}(\rho^2)
\]

### Von Neumann entropy

\[
S(\rho)
=
-\operatorname{Tr}(\rho\log_2\rho)
\]

### Bloch coordinates

\[
(x,y,z)
=
(\langle X\rangle,\langle Y\rangle,\langle Z\rangle)
\]

### Tensor-product dimension

\[
\dim(\mathcal H_n)=2^n
\]

for \(n\) qubits.

---

## 45. Relationship Between Linear Algebra and Quantum Physics

The central connection can be expressed as a chain of ideas:

\[
\text{Matrix}
\rightarrow
\text{Operator}
\rightarrow
\text{Eigenvalue Problem}
\rightarrow
\text{Eigenvalues and Eigenvectors}
\rightarrow
\text{Measurement Outcomes and States}.
\]

For a quantum observable \(A\),

\[
A|a_i\rangle=a_i|a_i\rangle.
\]

The eigenvalues \(a_i\) are possible measurement results, while the eigenvectors \(|a_i\rangle\) identify the states associated with those results.

For a Hamiltonian,

\[
H|E_i\rangle=E_i|E_i\rangle,
\]

the eigenvalues represent possible energies and the eigenvectors represent energy eigenstates.

For a density matrix, its eigenvalues determine quantities such as entropy and purity.

For a unitary transformation, eigenvectors can identify invariant directions or phase-accumulation modes.

Eigenvalues therefore occur throughout quantum theory rather than being restricted to one isolated calculation.

---

## 46. Structure of the Python Script

The script is organized progressively.

It begins with reusable linear-algebra primitives and then introduces increasingly specialized quantum concepts.

The major implementation groups are:

1. Basic vector and matrix operations
2. Determinants and characteristic equations
3. \(2\times2\) eigenvalue/eigenvector computation
4. Hermitian and unitary matrix checks
5. Quantum state construction
6. Measurement probabilities
7. Projectors and expectation values
8. Pauli operators
9. Spectral decomposition
10. Hamiltonians
11. Time evolution
12. Bloch-sphere coordinates
13. Numerical power iteration
14. Tensor products
15. Bell states
16. Density matrices
17. Entropy
18. Commutators
19. Quantum gates
20. Matrix functions
21. Measurement simulation
22. Variance
23. Edge cases
24. Validation and tests

Each section is executable independently through functions and is invoked by the main tutorial runner.

---

## 47. Testing

The script contains a dedicated test suite.

It verifies:

- matrix multiplication
- vector normalization
- Hermiticity of Pauli matrices
- unitarity of Pauli matrices
- unitarity of the Hadamard operator
- eigenpair residuals
- Born probabilities
- Bell-state normalization
- density-matrix trace
- density-matrix purity
- entropy values
- commutator properties
- global-phase equivalence

This is important because numerical linear algebra can produce plausible-looking output even when an implementation contains a subtle error.

The tests provide explicit mathematical assertions rather than relying solely on printed examples.

---

## 48. Performance Considerations

The script prioritizes readability and mathematical transparency.

Several implementations are intentionally not optimized:

- recursive determinant calculation
- naive matrix multiplication
- matrix exponential through a power series
- basic power iteration

For a matrix of dimension \(n\), ordinary dense matrix multiplication requires approximately cubic time in the matrix dimension.

For quantum systems, the situation becomes especially significant because an \(n\)-qubit state vector contains

\[
2^n
\]

complex amplitudes.

A dense operator acting on \(n\) qubits has

\[
2^n\times2^n
\]

entries.

This exponential growth makes structure, sparsity, tensor-product decomposition, iterative algorithms, and specialized representations important in practical quantum simulation.

---

## 49. Conceptual Interpretation of the Complete Workflow

The script demonstrates a full observable-measurement workflow:

1. Construct a candidate operator.
2. Verify that it is Hermitian.
3. Calculate its eigenvalues.
4. Calculate corresponding eigenvectors.
5. Normalize the eigenvectors.
6. Construct measurement projectors.
7. Calculate outcome probabilities.
8. Calculate expectation values.
9. Calculate variance.
10. Validate numerical eigenpairs using residuals.

This sequence connects abstract eigenvalue theory directly to the operational interpretation of quantum measurements.

---

## 50. Mathematical Perspective

Eigenvalues identify special scaling factors of linear transformations.

Eigenvectors identify the corresponding invariant directions or subspaces.

Hermitian operators add stronger structure:

- real eigenvalues
- orthogonal eigenspaces
- spectral decomposition

Quantum mechanics then gives those mathematical objects physical interpretations:

- eigenvalues become possible measurement outcomes
- eigenvectors become measurement states
- eigenspaces represent degenerate outcomes
- projectors represent measurement events
- spectral decompositions represent observables
- Hamiltonian eigenvalues represent energy levels
- Hamiltonian eigenvectors represent energy eigenstates
- unitary operators describe reversible quantum transformations
- density-matrix eigenvalues characterize statistical structure

This makes eigenvalue and eigenvector theory one of the central mathematical tools for understanding quantum-state applications.
