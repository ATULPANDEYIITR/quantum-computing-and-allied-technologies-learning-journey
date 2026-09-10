# Tensor products | Multi-system quantum states

## Topic introduction

Quantum systems are not combined by ordinary addition or ordinary multiplication of state vectors. The mathematical structure used to describe a composite quantum system is the **tensor product**.

If system A has Hilbert space \( \mathcal{H}_A \) and system B has Hilbert space \( \mathcal{H}_B \), their joint system is described by

\[
\mathcal{H}_{AB} = \mathcal{H}_A \otimes \mathcal{H}_B.
\]

This construction is fundamental to multi-qubit quantum computing, quantum communication, quantum information, quantum cryptography, quantum simulation, quantum error correction, and quantum many-body physics.

The accompanying Python script develops this subject computationally. It begins with single-qubit states and tensor products, then develops product states, entanglement, Bell states, controlled operations, density matrices, partial traces, Schmidt decomposition, entanglement entropy, multipartite states, Hamiltonians, time evolution, numerical issues, and computational scaling.

## Single-system quantum states

A pure qubit state can be written as

\[
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle,
\]

where

\[
|\alpha|^2 + |\beta|^2 = 1.
\]

The complex numbers \(\alpha\) and \(\beta\) are probability amplitudes. The probabilities obtained from computational-basis measurement are

\[
P(0)=|\alpha|^2,
\qquad
P(1)=|\beta|^2.
\]

The normalization condition is essential because the total probability must equal one.

The script represents a qubit as a two-element complex NumPy vector:

\[
|0\rangle =
\begin{bmatrix}
1\\
0
\end{bmatrix},
\qquad
|1\rangle =
\begin{bmatrix}
0\\
1
\end{bmatrix}.
\]

The states

\[
|+\rangle = \frac{|0\rangle+|1\rangle}{\sqrt 2}
\]

and

\[
|-\rangle = \frac{|0\rangle-|1\rangle}{\sqrt 2}
\]

are also implemented.

## What a tensor product represents

The tensor product combines the state spaces of independent quantum systems.

For two qubits,

\[
\mathbb{C}^2\otimes\mathbb{C}^2
\cong \mathbb{C}^4.
\]

Therefore, two qubits require four computational-basis amplitudes.

The computational basis is

\[
|00\rangle,\quad
|01\rangle,\quad
|10\rangle,\quad
|11\rangle.
\]

For example,

\[
|0\rangle\otimes|1\rangle = |01\rangle.
\]

The tensor product of column vectors is constructed by multiplying every element of the first vector by every element of the second vector.

For

\[
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
\]

and

\[
|\phi\rangle=\gamma|0\rangle+\delta|1\rangle,
\]

the tensor product is

\[
|\psi\rangle\otimes|\phi\rangle
=
\alpha\gamma|00\rangle
+\alpha\delta|01\rangle
+\beta\gamma|10\rangle
+\beta\delta|11\rangle.
\]

The Python script uses NumPy's Kronecker-product operation to perform this construction.

## Tensor-product ordering

Subsystem ordering is important.

In the convention used by the script,

\[
|0\rangle\otimes|1\rangle = |01\rangle
\]

while

\[
|1\rangle\otimes|0\rangle = |10\rangle.
\]

These are different vectors.

The order of tensor factors must remain consistent when constructing states, operators, measurements, partial traces, and permutations.

Many implementation errors in multi-qubit simulations are caused by silently changing the assumed subsystem ordering.

## Dimension growth

If subsystem \(A\) has dimension \(d_A\) and subsystem \(B\) has dimension \(d_B\), then

\[
\dim(\mathcal{H}_A\otimes\mathcal{H}_B)
=
d_A d_B.
\]

For \(n\) qubits,

\[
\dim(\mathcal{H})=2^n.
\]

Consequently:

| Qubits | State-vector dimension |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 10 | 1,024 |
| 20 | 1,048,576 |
| 30 | 1,073,741,824 |

This exponential growth is one of the central computational facts of quantum information.

A dense classical simulation of an arbitrary \(n\)-qubit pure state requires \(2^n\) complex amplitudes.

## Product states

A composite state is a **product state**, also called a separable pure state, when it can be written as

\[
|\Psi\rangle
=
|\psi_A\rangle\otimes|\psi_B\rangle.
\]

For example,

\[
|\Psi\rangle
=
|+\rangle\otimes|0\rangle.
\]

The state has a complete description in terms of independent local states.

For two qubits,

\[
|\Psi\rangle
=
a|00\rangle+b|01\rangle+c|10\rangle+d|11\rangle.
\]

It is separable precisely when the coefficients satisfy

\[
ad-bc=0.
\]

The Python script reshapes the four coefficients into

\[
C=
\begin{bmatrix}
a & b\\
c & d
\end{bmatrix}
\]

and uses the determinant to test separability.

A nonzero determinant indicates that the state cannot be represented as a tensor product of two single-qubit states.

## Entangled states

A pure composite state is entangled when it cannot be expressed as a tensor product of states belonging to the individual subsystems.

The standard example is the Bell state

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2}.
\]

There are four standard Bell states:

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

All four are normalized and mutually orthogonal.

They form an alternative basis for the two-qubit Hilbert space called the **Bell basis**.

## Why entanglement is different from a product state

Consider

\[
|+\rangle\otimes|0\rangle
=
\frac{|00\rangle+|10\rangle}{\sqrt2}.
\]

The first and second qubits have independent local descriptions.

For

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2},
\]

there is no pair of single-qubit states whose tensor product equals this state.

The distinction is structural rather than merely a difference in the numerical values of amplitudes.

## Tensor products of operators

Tensor products apply to operators as well as states.

If \(A\) acts on system A and \(B\) acts on system B, then

\[
A\otimes B
\]

acts on the composite system.

For example,

\[
X\otimes I
\]

applies the Pauli-X operation to the first qubit while leaving the second qubit unchanged.

Similarly,

\[
I\otimes X
\]

applies X to the second qubit.

For two qubits,

\[
X\otimes I
\]

and

\[
I\otimes X
\]

are different four-by-four matrices.

## Pauli operators

The Pauli matrices used in the script are

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

The identity is

\[
I=
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}.
\]

These operators are important building blocks for quantum gates, observables, Hamiltonians, and correlation functions.

## Algebraic properties of tensor products

Tensor products have several important properties.

### Bilinearity

\[
A\otimes(B+C)
=
A\otimes B+A\otimes C.
\]

Likewise,

\[
(A+B)\otimes C
=
A\otimes C+B\otimes C.
\]

### Scalar compatibility

For a scalar \(\lambda\),

\[
(\lambda A)\otimes B
=
A\otimes(\lambda B)
=
\lambda(A\otimes B).
\]

### Associativity

Tensor products are associative up to the natural identification of the corresponding spaces:

\[
(A\otimes B)\otimes C
=
A\otimes(B\otimes C).
\]

### Non-commutativity

Tensor products are not generally commutative:

\[
A\otimes B\neq B\otimes A.
\]

When systems are exchanged, an explicit permutation or SWAP operation is required.

## The SWAP operator

The two-qubit SWAP gate exchanges two subsystems:

\[
\operatorname{SWAP}|a\rangle|b\rangle
=
|b\rangle|a\rangle.
\]

Its matrix in the computational basis is

\[
\operatorname{SWAP}
=
\begin{bmatrix}
1&0&0&0\\
0&0&1&0\\
0&1&0&0\\
0&0&0&1
\end{bmatrix}.
\]

SWAP is unitary and satisfies

\[
\operatorname{SWAP}^2=I.
\]

The script demonstrates how subsystem ordering changes under this operation.

## Controlled operations

A controlled operation applies an operation to a target subsystem conditional on the state of another subsystem.

For a controlled-\(U\) operation with the first qubit as control,

\[
CU
=
|0\rangle\langle0|\otimes I
+
|1\rangle\langle1|\otimes U.
\]

For \(U=X\), this produces the controlled-NOT or CNOT gate.

CNOT acts as

\[
|00\rangle\rightarrow|00\rangle,
\]

\[
|01\rangle\rightarrow|01\rangle,
\]

\[
|10\rangle\rightarrow|11\rangle,
\]

\[
|11\rangle\rightarrow|10\rangle.
\]

## Creating a Bell state

A standard Bell-state preparation sequence is:

1. Start with \(|00\rangle\).
2. Apply Hadamard to the first qubit.
3. Apply CNOT.

The Hadamard operation produces

\[
(H\otimes I)|00\rangle
=
\frac{|00\rangle+|10\rangle}{\sqrt2}.
\]

CNOT then transforms the second term:

\[
|10\rangle\rightarrow|11\rangle.
\]

The result is

\[
\frac{|00\rangle+|11\rangle}{\sqrt2}
=
|\Phi^+\rangle.
\]

This demonstrates an important principle: local operations alone cannot create entanglement from a separable input, while an appropriate multi-system interaction such as CNOT can.

## Local versus global operations

A local operation has the form

\[
A\otimes I
\]

or

\[
I\otimes B.
\]

A general operation on the complete system need not have the form

\[
A\otimes B.
\]

CNOT is an important example of a two-system operation that cannot be represented as a single tensor product of two independent one-qubit operators.

This distinction is fundamental to quantum circuits.

## Operator Schmidt rank

The idea of Schmidt decomposition also has an operator analogue.

An operator on a bipartite system can sometimes be written as

\[
M=\sum_k s_k A_k\otimes B_k.
\]

The smallest number of required tensor-product terms is related to the **operator Schmidt rank**.

An operator with rank one has the form

\[
M=A\otimes B.
\]

CNOT has operator Schmidt rank greater than one, which reflects its genuinely composite nature.

The script constructs an appropriate rearranged coefficient matrix and determines its numerical rank using singular values.

## Three-qubit states

For three qubits,

\[
\mathcal{H}
=
\mathbb{C}^2
\otimes
\mathbb{C}^2
\otimes
\mathbb{C}^2
\cong
\mathbb{C}^8.
\]

The computational basis contains eight states:

\[
|000\rangle,
|001\rangle,
|010\rangle,
|011\rangle,
|100\rangle,
|101\rangle,
|110\rangle,
|111\rangle.
\]

The script demonstrates the GHZ and W states.

## GHZ state

The three-qubit GHZ state is

\[
|GHZ\rangle
=
\frac{|000\rangle+|111\rangle}{\sqrt2}.
\]

It exhibits strong multipartite correlations.

Its reduced state for one qubit is

\[
\rho=
\frac12|0\rangle\langle0|
+
\frac12|1\rangle\langle1|
=
\frac12 I.
\]

Thus the individual qubit is maximally mixed even though the overall three-qubit state is pure.

## W state

The three-qubit W state is

\[
|W\rangle
=
\frac{|001\rangle+|010\rangle+|100\rangle}{\sqrt3}.
\]

GHZ and W states are important examples of different forms of multipartite entanglement.

They also illustrate why multipartite entanglement cannot always be understood simply by extending two-qubit intuition.

## Density matrices

A pure state

\[
|\psi\rangle
\]

can be represented by the density matrix

\[
\rho=|\psi\rangle\langle\psi|.
\]

A valid density matrix satisfies:

- Hermiticity:
  \[
  \rho^\dagger=\rho
  \]

- Unit trace:
  \[
  \operatorname{Tr}(\rho)=1
  \]

- Positive semidefiniteness:
  \[
  \rho\succeq0.
  \]

For a pure state,

\[
\operatorname{Tr}(\rho^2)=1.
\]

The script checks these properties numerically.

## Tensor products of density matrices

If two independent systems are described by density matrices \(\rho_A\) and \(\rho_B\), their joint state is

\[
\rho_{AB}
=
\rho_A\otimes\rho_B.
\]

For example,

\[
\rho_{AB}
=
|+\rangle\langle+|
\otimes
|1\rangle\langle1|
\]

represents the product state \(|+\rangle\otimes|1\rangle\).

A general joint density matrix need not factor in this way.

## Mixed states

A mixed state represents classical statistical uncertainty over quantum states.

For example,

\[
\rho
=
\frac12|00\rangle\langle00|
+
\frac12|11\rangle\langle11|
\]

is a classically correlated mixed state.

It differs from the Bell-state density matrix

\[
|\Phi^+\rangle\langle\Phi^+|.
\]

The Bell state contains coherent off-diagonal terms between \(|00\rangle\) and \(|11\rangle\), while the classical mixture does not.

This distinction is important because classical correlation and quantum entanglement are not synonymous.

## Purity

Purity is defined as

\[
P=\operatorname{Tr}(\rho^2).
\]

For a pure state,

\[
P=1.
\]

For a mixed state,

\[
P<1.
\]

For a maximally mixed qubit,

\[
\rho=\frac{I}{2},
\]

the purity is

\[
P=\frac12.
\]

Purity is useful for characterizing reduced states and detecting whether a subsystem of a pure bipartite state remains pure.

## Partial trace

A composite system can be described globally while a subsystem is described by a reduced density matrix.

For a bipartite state \(\rho_{AB}\), the reduced state of A is

\[
\rho_A
=
\operatorname{Tr}_B(\rho_{AB}).
\]

Similarly,

\[
\rho_B
=
\operatorname{Tr}_A(\rho_{AB}).
\]

The partial trace removes the degrees of freedom belonging to the subsystem being ignored.

The script implements partial traces explicitly by reshaping the density matrix into tensor indices and summing over matching subsystem indices.

## Reduced state of a Bell state

For

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2},
\]

the reduced state of either qubit is

\[
\rho_A
=
\rho_B
=
\frac12I.
\]

Thus the global state is pure while each individual subsystem is maximally mixed.

This is a defining feature of bipartite entanglement.

## Product states and reduced states

For a product state

\[
|\psi_A\rangle\otimes|\phi_B\rangle,
\]

the reduced states are

\[
\rho_A=|\psi_A\rangle\langle\psi_A|
\]

and

\[
\rho_B=|\phi_B\rangle\langle\phi_B|.
\]

They are pure.

For a pure bipartite state, the reduced state is pure if and only if the global state is separable.

## Schmidt decomposition

Every pure bipartite state can be written in Schmidt form:

\[
|\psi\rangle
=
\sum_k s_k
|u_k\rangle\otimes|v_k\rangle,
\]

where:

- \(s_k\ge0\) are the Schmidt coefficients,
- the \( |u_k\rangle \) are orthonormal,
- the \( |v_k\rangle \) are orthonormal,
- the squared Schmidt coefficients sum to one.

For a two-qubit state, the Schmidt decomposition can be obtained from the singular value decomposition of the two-by-two coefficient matrix.

If

\[
C=USV^\dagger,
\]

the singular values in \(S\) are the Schmidt coefficients.

## Schmidt rank

The number of nonzero Schmidt coefficients is the **Schmidt rank**.

For a pure bipartite state:

- Schmidt rank 1 means the state is separable.
- Schmidt rank greater than 1 means the state is entangled.

For two qubits, the maximum Schmidt rank is two.

A Bell state has Schmidt rank two.

A product state has Schmidt rank one.

## Entanglement entropy

The von Neumann entropy is

\[
S(\rho)
=
-\operatorname{Tr}(\rho\log_2\rho).
\]

For a pure bipartite state, the entropy of either reduced state is called the **entanglement entropy**.

A product state has

\[
S=0.
\]

A maximally entangled two-qubit state has

\[
S=1
\]

bit.

For a partially entangled state such as

\[
|\psi\rangle
=
\alpha|00\rangle+\beta|11\rangle,
\]

the entropy lies between zero and one when both coefficients are nonzero.

## Measurement probabilities

For

\[
|\psi\rangle
=
\sum_i c_i|i\rangle,
\]

the probability of measuring basis state \(|i\rangle\) is

\[
P(i)=|c_i|^2.
\]

For

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2},
\]

the computational-basis probabilities are

\[
P(00)=\frac12,
\]

\[
P(11)=\frac12,
\]

while

\[
P(01)=P(10)=0.
\]

The script includes both exact probability calculations and simulated repeated measurements.

## Measurement sampling

A real experiment produces individual outcomes rather than directly returning the complete probability distribution.

The script samples outcomes using the calculated probabilities.

With sufficiently many measurements, empirical frequencies approach the theoretical probabilities.

For a finite number of measurements, observed frequencies fluctuate because of statistical sampling.

## Conditional state collapse

A projective measurement updates the quantum state conditional on the observed outcome.

For the Bell state, observing 00 leaves the system in

\[
|00\rangle.
\]

Observing 11 leaves it in

\[
|11\rangle.
\]

An outcome with zero probability cannot occur, so attempting to condition on such an outcome is correctly treated as an error in the script.

## Measuring only one subsystem

Suppose

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2}.
\]

Measuring only the first qubit produces:

\[
P(A=0)=\frac12,
\qquad
P(A=1)=\frac12.
\]

The joint system contains correlations that are not visible from the individual marginal probabilities alone.

This is one reason joint-state descriptions are necessary in quantum information.

## Expectation values

For a state \(|\psi\rangle\) and observable \(O\),

\[
\langle O\rangle
=
\langle\psi|O|\psi\rangle.
\]

For multi-system observables, tensor products are used.

Examples include

\[
X\otimes X,
\]

\[
Y\otimes Y,
\]

and

\[
Z\otimes Z.
\]

For a Bell state, these joint observables reveal strong correlations.

## Correlation functions

An observable such as

\[
Z\otimes Z
\]

measures a joint property of two systems.

This is different from measuring

\[
Z\otimes I
\]

or

\[
I\otimes Z,
\]

which describe local properties.

Quantum information uses such joint expectation values in the study of entanglement, Bell inequalities, quantum states, many-body systems, and quantum error correction.

## Operators acting on different subsystems

If \(A\) acts on subsystem A and \(B\) acts on subsystem B, then

\[
[A\otimes I,I\otimes B]=0.
\]

This follows because they act on different tensor factors.

For example,

\[
[X\otimes I,I\otimes Z]=0.
\]

This should not be confused with operators acting on the same subsystem. Pauli X and Z satisfy

\[
[X,Z]\neq0.
\]

## Tensor-product eigenvalues

If

\[
A|a\rangle=\lambda|a\rangle
\]

and

\[
B|b\rangle=\mu|b\rangle,
\]

then

\[
(A\otimes B)
(|a\rangle\otimes|b\rangle)
=
\lambda\mu
(|a\rangle\otimes|b\rangle).
\]

Therefore eigenvalues of tensor-product operators are pairwise products of eigenvalues from the component operators.

The script verifies this numerically with diagonal matrices.

## Trace identity

For compatible matrices,

\[
\operatorname{Tr}(A\otimes B)
=
\operatorname{Tr}(A)\operatorname{Tr}(B).
\]

This identity is useful when manipulating density matrices and operators.

## Determinant identity

If \(A\) is \(m\times m\) and \(B\) is \(n\times n\),

\[
\det(A\otimes B)
=
\det(A)^n\det(B)^m.
\]

For two two-by-two matrices,

\[
\det(A\otimes B)
=
\det(A)^2\det(B)^2.
\]

The script verifies this relationship numerically.

## Multipartite systems

For several subsystems,

\[
\mathcal{H}
=
\mathcal{H}_1
\otimes
\mathcal{H}_2
\otimes
\cdots
\otimes
\mathcal{H}_n.
\]

The tensor product can describe systems containing qubits, qudits, registers, quantum memories, physical particles, or other quantum subsystems.

Multipartite systems introduce different possible partitions.

For three subsystems A, B, and C, one can study:

\[
A|BC,
\]

\[
B|AC,
\]

or

\[
C|AB.
\]

Entanglement properties can depend on the chosen partition.

## GHZ versus W states

The GHZ and W states demonstrate that multipartite entanglement has different structures.

GHZ:

\[
|GHZ\rangle
=
\frac{|000\rangle+|111\rangle}{\sqrt2}.
\]

W:

\[
|W\rangle
=
\frac{|001\rangle+|010\rangle+|100\rangle}{\sqrt3}.
\]

They are not interchangeable examples of the same type of multipartite entanglement.

Their reduced states, correlations, and behavior under particle loss differ.

## Hamiltonians for composite systems

For two non-interacting systems, a common Hamiltonian structure is

\[
H
=
H_A\otimes I
+
I\otimes H_B.
\]

The first term represents the energy associated with subsystem A and the second represents subsystem B.

An interaction term can be added:

\[
H_{\text{total}}
=
H_A\otimes I
+
I\otimes H_B
+
H_{\text{interaction}}.
\]

For example,

\[
H_{\text{interaction}}
=
J(Z\otimes Z)
\]

describes a simple two-qubit coupling model.

The interaction term is structurally different from independent local evolution.

## Time evolution

For a time-independent Hamiltonian,

\[
|\psi(t)\rangle
=
e^{-iHt}|\psi(0)\rangle
\]

when units are chosen so that \(\hbar=1\).

The time-evolution operator

\[
U(t)=e^{-iHt}
\]

is unitary when \(H\) is Hermitian.

The script computes the exponential for a Hermitian matrix using eigendecomposition and verifies that the resulting evolution preserves normalization.

## Basis changes

Quantum states can be represented in different bases.

Applying a local Hadamard transformation to two qubits is represented by

\[
H\otimes H.
\]

More generally, if \(U_A\) and \(U_B\) are basis transformations,

\[
U_A\otimes U_B
\]

acts on the complete bipartite state.

This is another direct application of tensor-product structure.

## Bell basis

The four Bell states form an orthonormal basis of the two-qubit Hilbert space.

If the Bell basis vectors are arranged as columns of a matrix \(U\), then

\[
U^\dagger U=I.
\]

The coordinates of a state in the Bell basis are obtained using

\[
U^\dagger|\psi\rangle.
\]

This illustrates that tensor-product Hilbert spaces support multiple useful bases, not only the computational basis.

## Teleportation and tensor products

Quantum teleportation begins with three qubits:

\[
|\psi\rangle\otimes|\Phi^+\rangle.
\]

The first qubit contains the state to be transferred and the other two form an entangled Bell pair.

The initial three-qubit state therefore belongs to

\[
\mathcal{H}_1\otimes\mathcal{H}_2\otimes\mathcal{H}_3.
\]

The teleportation protocol subsequently applies multi-system gates and measurements.

The tensor-product representation is essential for writing the complete initial and intermediate states.

## Global phase and relative phase

Multiplying an entire quantum state by a phase

\[
e^{i\theta}
\]

does not change the physical pure state:

\[
|\psi\rangle
\sim
e^{i\theta}|\psi\rangle.
\]

For example,

\[
|\psi\rangle
\]

and

\[
e^{i\pi/3}|\psi\rangle
\]

have fidelity one.

A relative phase is different.

The states

\[
\frac{|0\rangle+|1\rangle}{\sqrt2}
\]

and

\[
\frac{|0\rangle+i|1\rangle}{\sqrt2}
\]

are physically distinguishable.

The script demonstrates both cases.

## Complex conjugation and bras

If

\[
|\psi\rangle
\]

is a complex state vector, then its bra is

\[
\langle\psi|
=
|\psi\rangle^\dagger.
\]

The dagger means conjugate transpose.

For complex vectors, ordinary transpose is not sufficient.

This distinction is essential when computing:

\[
\langle\psi|\psi\rangle,
\]

\[
\langle\psi|O|\psi\rangle,
\]

density matrices, and reduced states.

## Fidelity

For two pure states,

\[
F(|\psi\rangle,|\phi\rangle)
=
|\langle\psi|\phi\rangle|^2.
\]

Its value ranges from zero to one.

For identical physical states,

\[
F=1.
\]

For orthogonal states,

\[
F=0.
\]

The script uses fidelity to compare computational-basis states, superposition states, and states differing only by global phase.

## SWAP test

The SWAP test compares two quantum states using their overlap.

The probability of the symmetric ancilla outcome is

\[
P(0)
=
\frac{1+|\langle\psi|\phi\rangle|^2}{2}.
\]

Thus the test provides information about the similarity between two states without requiring direct classical access to their full amplitude descriptions.

The script demonstrates the mathematical probability formula.

## No-cloning context

The tensor product provides the mathematical representation of two copies:

\[
|\psi\rangle\otimes|\psi\rangle.
\]

This does not imply that an arbitrary unknown quantum state can be copied by a universal physical operation.

The no-cloning theorem is a physical restriction on quantum operations, not a limitation of the tensor-product notation.

Tensor products describe the state space of multiple systems; they do not by themselves specify which transformations are physically implementable.

## Classical correlation versus entanglement

A mixed state such as

\[
\rho
=
\frac12|00\rangle\langle00|
+
\frac12|11\rangle\langle11|
\]

contains correlations.

Yet it is separable because it can be expressed as a probabilistic mixture of product states.

The Bell state

\[
|\Phi^+\rangle
=
\frac{|00\rangle+|11\rangle}{\sqrt2}
\]

is entangled.

Therefore:

- correlation does not automatically mean entanglement;
- mixed-state correlations can be classical;
- entanglement concerns whether a state admits an appropriate separable decomposition;
- coherent superposition terms are important in distinguishing quantum entanglement from a classical mixture.

## Numerical implementation

The script uses NumPy for vector and matrix operations.

The main numerical representations are:

- state vectors as one-dimensional complex arrays;
- operators as square complex matrices;
- density matrices as square complex matrices;
- tensor products through the Kronecker product;
- eigenvalue calculations through Hermitian eigendecomposition;
- Schmidt coefficients through singular-value decomposition.

The script is designed to remain self-contained and does not require a quantum-computing framework.

## Numerical tolerance

Exact mathematical statements such as

\[
\det(C)=0
\]

are evaluated numerically using floating-point arithmetic.

A calculation that is theoretically zero might produce a small value such as

\[
10^{-15}.
\]

For this reason, the script uses a tolerance when checking:

- normalization;
- zero amplitudes;
- matrix equality;
- separability;
- singular-value rank;
- positive semidefiniteness;
- unitary matrices.

This is a general numerical-computing principle rather than a special property of quantum mechanics.

## Error handling and edge cases

The script explicitly handles several invalid situations.

Examples include:

- attempting to normalize the zero vector;
- constructing an empty tensor product;
- using a state with the wrong dimension;
- using an invalid computational-basis index;
- requesting an invalid partial trace;
- requesting a measurement sample with zero shots;
- conditioning on a measurement outcome with zero probability.

Explicit validation prevents silent propagation of invalid states.

## Performance considerations

The most important performance issue is exponential state-space growth.

For \(n\) qubits, a dense state vector has

\[
2^n
\]

complex amplitudes.

A density matrix has

\[
2^n\times2^n=4^n
\]

entries.

Therefore density-matrix simulation grows substantially faster in memory than pure-state simulation.

For a complex double-precision value requiring approximately 16 bytes, the raw state-vector storage is approximately

\[
16\times2^n
\]

bytes.

The script calculates illustrative memory requirements for increasing numbers of qubits.

This scaling limits brute-force classical simulation of arbitrary large quantum systems.

## Tensor-network motivation

Although the full Hilbert space has exponential dimension, not every physically relevant state requires an explicit dense representation.

Product states have highly structured tensor representations:

\[
|\psi_1\rangle\otimes|\psi_2\rangle\otimes\cdots\otimes|\psi_n\rangle.
\]

Instead of storing every global amplitude independently, the individual local factors can be stored separately.

More sophisticated tensor-network methods generalize this idea by representing structured entanglement through interconnected tensors.

This does not eliminate exponential complexity in every problem. Computational efficiency depends strongly on the amount and structure of entanglement and on the specific tensor-network representation.

## Multipartite partial traces

For a three-qubit density matrix, tracing out one qubit produces a two-qubit reduced density matrix.

The operation is implemented by matching the ket and bra indices belonging to the subsystem being removed and summing over those indices.

This is a direct computational realization of

\[
\rho_{AB}
=
\operatorname{Tr}_C(\rho_{ABC}).
\]

The same principle extends to larger systems.

## Entanglement entropy as a computational diagnostic

For a pure bipartite state,

\[
S(\rho_A)=S(\rho_B).
\]

The entropy is zero for separable pure states and positive for entangled pure states.

For two qubits, the maximum entanglement entropy is one bit.

For larger bipartite systems, the maximum entropy is bounded by the logarithm of the smaller subsystem dimension.

Thus the reduced-state entropy provides a quantitative way to study entanglement across a chosen bipartition.

## Important distinction: state dimension versus physical complexity

The mathematical Hilbert-space dimension of an \(n\)-qubit system is \(2^n\).

This does not mean every physical or computational task involving \(n\) qubits requires explicitly manipulating \(2^n\) arbitrary amplitudes.

Specific states, circuits, Hamiltonians, symmetries, and tensor-network structures can allow more compact representations.

The exponential dimension remains fundamental, but practical complexity depends on the structure of the problem being solved.

## Security and quantum-information relevance

Tensor products are foundational to:

- quantum cryptography;
- quantum communication;
- entanglement-based protocols;
- quantum error correction;
- distributed quantum computation;
- quantum teleportation;
- quantum networks;
- quantum sensing;
- quantum many-body physics.

Security properties cannot be established merely by constructing a tensor-product state in a numerical simulation. A real security analysis requires assumptions about adversaries, devices, noise, authentication, measurements, communication channels, and the relevant protocol.

## Common implementation mistakes

### Ignoring subsystem ordering

The meaning of every vector index depends on the chosen tensor ordering convention.

### Forgetting normalization

A quantum state must satisfy

\[
\langle\psi|\psi\rangle=1.
\]

### Using transpose instead of conjugate transpose

Complex quantum states require the Hermitian adjoint when converting kets into bras.

### Treating tensor products as ordinary multiplication

The tensor product changes the dimension of the space.

### Assuming every composite state is separable

Entangled states cannot generally be represented as independent local states.

### Confusing correlation with entanglement

Classically correlated mixed states can be separable.

### Ignoring floating-point error

Numerical zero and mathematical zero are not always identical in floating-point computation.

### Ignoring exponential scaling

A dense representation becomes expensive as the number of subsystems increases.

## Integrated example

The script contains an integrated workflow:

\[
|00\rangle
\rightarrow
(H\otimes I)|00\rangle
\rightarrow
\operatorname{CNOT}(H\otimes I)|00\rangle.
\]

The final state is

\[
|\Phi^+\rangle.
\]

The script then:

1. constructs its density matrix;
2. calculates a reduced state;
3. calculates the reduced-state entropy;
4. evaluates a two-qubit correlation observable.

This combines the main ideas of tensor products, gates, entanglement, density matrices, partial trace, entropy, and expectation values into one computational example.

## Self-tests

The Python script includes executable assertions checking core mathematical relationships.

The tests verify:

- tensor-product dimensions;
- normalization;
- unitarity of gates;
- separability of product states;
- non-separability of Bell states;
- the reduced state of a Bell state;
- Bell-state entanglement entropy;
- measurement probabilities;
- tensor-product trace identities;
- Bell-state preparation;
- SWAP behavior;
- pure-state fidelity.

These tests make the educational examples executable rather than purely illustrative.

## Real-world relevance

Tensor products provide the formal language required whenever multiple quantum systems must be represented jointly.

They explain why two qubits require a four-dimensional Hilbert space, why three qubits require an eight-dimensional space, how local gates are embedded into larger registers, how controlled operations act across subsystems, how entangled states differ from product states, and how subsystem information can be extracted through partial traces.

The same mathematical framework extends from two-qubit examples to quantum registers, quantum networks, many-body systems, quantum communication protocols, quantum algorithms, and quantum information theory.
