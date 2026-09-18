# Operators: Hermitian and unitary operators

## Introduction

In linear algebra and quantum mechanics, an operator is a mathematical transformation that acts on vectors in a vector space. When the vector space is a complex Hilbert space, the adjoint of an operator becomes especially important.

Two operator classes have central roles in quantum theory:

- **Hermitian operators**, which represent measurable observables under the standard quantum-mechanical model.
- **Unitary operators**, which represent reversible transformations such as ideal quantum gates and closed-system time evolution.

These two classes are related but are not interchangeable. An operator can be Hermitian without being unitary, unitary without being Hermitian, both, or neither.

The three implementations in this repository approach the subject from complementary perspectives:

- The Python implementation develops the mathematical machinery and provides an extensive educational implementation.
- The JavaScript implementation develops a reusable complex-number and matrix system and uses it to build a small state-vector quantum simulator.
- The C++ implementation presents a more structured technical case study involving operator validation, quantum circuits, measurement, and a parameterized observable calculation.

The implementations use dense matrices and state vectors so that the mathematical operations remain visible. Dense representations are appropriate for small educational examples but become expensive as the number of quantum subsystems increases.

---

## Fundamental terminology

### Vector

A vector is an ordered collection of numbers. In quantum mechanics, a pure state is commonly represented by a complex column vector.

For a single qubit, a state can be written as

`|ψ⟩ = α|0⟩ + β|1⟩`

with complex amplitudes `α` and `β`.

A normalized state satisfies

`|α|² + |β|² = 1`.

The squared magnitudes of the amplitudes are interpreted as measurement probabilities in the computational basis.

### Operator

An operator maps vectors to vectors.

For a matrix `A` and state vector `|ψ⟩`:

`|φ⟩ = A|ψ⟩`.

For a finite-dimensional Hilbert space, operators can be represented by square complex matrices.

### Adjoint

The adjoint of an operator `A` is written as `A†`.

For a matrix, it is the conjugate transpose:

`A† = (A*)ᵀ`.

The operation has two parts:

1. Take the complex conjugate of every matrix element.
2. Transpose the matrix.

The distinction between transpose and adjoint matters whenever complex-valued matrix elements occur.

### Hermitian operator

An operator `A` is Hermitian when

`A† = A`.

Hermitian operators are also called self-adjoint in the finite-dimensional matrix setting used here.

Important consequences include:

- eigenvalues are real;
- eigenvectors belonging to distinct eigenvalues can be chosen orthogonal;
- the operator has an orthonormal eigenbasis;
- expectation values of normalized states are real, apart from numerical round-off;
- Hermitian operators are normal.

Hermitian operators are fundamental representations of observables.

### Unitary operator

An operator `U` is unitary when

`U†U = UU† = I`.

Consequently,

`U⁻¹ = U†`.

Unitary operators preserve inner products:

`⟨Uψ|Uφ⟩ = ⟨ψ|φ⟩`.

They therefore preserve vector norms:

`||Uψ|| = ||ψ||`.

In quantum mechanics, unitary operators describe reversible transformations of closed quantum states.

### Normal operator

An operator `A` is normal when

`A†A = AA†`.

Both Hermitian and unitary operators are normal.

The converse does not hold. A normal operator does not have to be Hermitian or unitary.

Normal operators are important because finite-dimensional normal matrices admit unitary diagonalization.

---

## The adjoint in detail

Consider a complex matrix

`A = [[a, b], [c, d]]`.

Its adjoint is

`A† = [[a*, c*], [b*, d*]]`.

The conjugation is essential.

For real-valued matrices, the adjoint happens to equal the ordinary transpose. For complex-valued matrices, this is generally not true.

The Python implementation provides `conjugate_transpose()` and `adjoint()`.

The JavaScript implementation implements the same operation through the `Complex.conjugate()` method and `conjugateTranspose()`.

The C++ implementation uses `std::conj()` inside its `adjoint()` function.

---

## Hermitian operators

The defining relation is

`A† = A`.

For a Hermitian matrix, diagonal elements must be real, and an off-diagonal element must be the complex conjugate of its reflected counterpart.

For example,

`A = [[2, 1+i], [1-i, 3]]`

is Hermitian.

The upper-right entry is `1+i`, while the lower-left entry is its complex conjugate, `1-i`.

### Hermitian does not mean unitary

Consider

`A = [[2, 0], [0, -3]]`.

This matrix is Hermitian because it equals its adjoint.

It is not unitary because

`A†A = [[4, 0], [0, 9]]`

rather than the identity matrix.

The Python and C++ implementations explicitly demonstrate this distinction.

---

## Unitary operators

The defining relation is

`U†U = I`.

For a square finite-dimensional matrix, this also implies

`UU† = I`.

Unitary transformations preserve:

- norms;
- inner products;
- angles;
- orthogonality;
- normalization of quantum states;
- reversibility.

If

`|φ⟩ = U|ψ⟩`

and `U` is unitary, then

`⟨φ|φ⟩ = ⟨ψ|U†U|ψ⟩ = ⟨ψ|ψ⟩`.

This is why unitary transformations are suitable for reversible quantum evolution.

### Unitary does not mean Hermitian

A phase operator provides a simple example:

`U = [[1, 0], [0, e^(iθ)]]`.

It is unitary because the magnitude of each diagonal entry is one.

For a general value of `θ`, it is not Hermitian.

The JavaScript and Python implementations construct phase gates and test both properties.

---

## Operators that are both Hermitian and unitary

Some important quantum operators satisfy both conditions.

The Pauli operators

`X = [[0, 1], [1, 0]]`

`Y = [[0, -i], [i, 0]]`

`Z = [[1, 0], [0, -1]]`

are Hermitian and unitary.

The Hadamard operator

`H = 1/sqrt(2) [[1, 1], [1, -1]]`

is also both Hermitian and unitary.

For such an operator,

`A† = A`

and

`A†A = I`.

Therefore,

`A² = I`.

This means these operators are their own inverses.

---

## Observables and Hermitian operators

In the standard finite-dimensional quantum formalism, an observable is represented by a Hermitian operator.

For a normalized state `|ψ⟩`, the expectation value of an observable `A` is

`⟨A⟩ = ⟨ψ|A|ψ⟩`.

When `A` is Hermitian, this value is real.

The implementations demonstrate expectation values for the Pauli X, Y, and Z observables.

For example, the computational-basis state

`|0⟩ = [1, 0]ᵀ`

satisfies

`⟨Z⟩ = 1`.

The equal superposition state

`|+⟩ = (|0⟩ + |1⟩)/sqrt(2)`

satisfies

`⟨X⟩ = 1`

and

`⟨Z⟩ = 0`.

These calculations illustrate the distinction between a state and an observable:

- the state describes the system;
- the Hermitian operator describes the quantity being measured;
- the expectation value describes the statistical mean obtained from repeated measurements.

---

## Variance of an observable

The variance of an observable is

`Var(A) = ⟨A²⟩ - ⟨A⟩²`.

For a Hermitian observable, the variance is non-negative.

The implementations calculate this quantity directly.

For an eigenstate of an observable, the variance is zero because every measurement produces the corresponding eigenvalue.

For a state that is a superposition of different eigenstates, the variance can be positive.

---

## Eigenvalues and eigenvectors

An eigenvector `|v⟩` of an operator `A` satisfies

`A|v⟩ = λ|v⟩`

where `λ` is the corresponding eigenvalue.

Hermitian operators have real eigenvalues.

This is one of the reasons Hermitian operators are appropriate for observables: physical measurement outcomes are represented by real numbers.

For a Hermitian operator, the spectral theorem provides an orthonormal eigenbasis.

In finite dimensions, an observable can therefore be represented in spectral form as

`A = Σᵢ aᵢ Pᵢ`

where:

- `aᵢ` are real eigenvalues;
- `Pᵢ` are orthogonal projectors.

For non-degenerate eigenvalues, a projector can be written as

`Pᵢ = |aᵢ⟩⟨aᵢ|`.

The Python implementation includes a small closed-form eigenvalue calculation for 2 × 2 matrices. It intentionally does not attempt to implement a general-purpose eigenvalue algorithm.

Production numerical software should use specialized, numerically stable eigensolver implementations.

---

## Projectors

A projector `P` satisfies

`P² = P`.

An orthogonal projector is also Hermitian.

The computational-basis projectors for a single qubit are

`P₀ = [[1, 0], [0, 0]]`

and

`P₁ = [[0, 0], [0, 1]]`.

They satisfy

`P₀² = P₀`

and

`P₁² = P₁`.

For a state `|ψ⟩`, the probability of the corresponding projected measurement outcome is represented by

`⟨ψ|Pᵢ|ψ⟩`.

The Python and JavaScript implementations calculate these probabilities directly.

The projectors also satisfy

`P₀ + P₁ = I`.

This expresses completeness of the computational-basis measurement.

---

## Unitary transformations and quantum gates

An ideal quantum gate is represented by a unitary operator.

Common one-qubit gates include:

| Gate | Matrix | Hermitian | Unitary |
| --- | --- | --- | --- |
| Identity | `[[1,0],[0,1]]` | Yes | Yes |
| X | `[[0,1],[1,0]]` | Yes | Yes |
| Y | `[[0,-i],[i,0]]` | Yes | Yes |
| Z | `[[1,0],[0,-1]]` | Yes | Yes |
| H | `1/sqrt(2)[[1,1],[1,-1]]` | Yes | Yes |
| General phase | `[[1,0],[0,e^(iθ)]]` | Generally no | Yes |

The distinction is important because being a valid quantum gate does not require being Hermitian.

---

## Composition and operator order

If an initial state is transformed by `A` and then by `B`, the final state is

`|ψ_final⟩ = B A |ψ_initial⟩`.

The rightmost operator acts first.

Matrix multiplication is generally non-commutative:

`AB ≠ BA`.

The implementations explicitly compare `HX` with `XH`.

This is a practical source of errors when translating a circuit diagram into matrix multiplication.

---

## Inverses of unitary operators

For a unitary operator,

`U⁻¹ = U†`.

Therefore the inverse transformation is easy to construct from the adjoint.

For a unitary quantum gate,

`U†U = I`.

The Python, JavaScript, and C++ implementations verify this relation for common gates.

A useful special case occurs when

`U† = U`.

Then

`U² = I`.

This is true for Pauli X, Pauli Y, Pauli Z, and the Hadamard operator.

---

## Tensor products

A multi-qubit state space is constructed using tensor products.

If `A` is an operator on one subsystem and `B` is an operator on another, their combined operator is

`A ⊗ B`.

If `A` is an `m × n` matrix and `B` is a `p × q` matrix, then

`A ⊗ B`

has dimensions

`mp × nq`.

For two qubits,

`H ⊗ H`

is a 4 × 4 operator.

The implementations use tensor products to construct multi-qubit transformations.

### Unitarity of tensor products

If `A` and `B` are unitary, then

`A ⊗ B`

is unitary because

`(A ⊗ B)†(A ⊗ B) = (A†A) ⊗ (B†B) = I ⊗ I`.

The Python, JavaScript, and C++ implementations verify this property.

---

## Controlled operators

A controlled-U operation applies `U` to a target system only when the control system satisfies a specified condition.

For a single control and target qubit, a controlled-U matrix can be represented as

`CU = [[I, 0], [0, U]]`

when the basis is ordered as

`|00⟩, |01⟩, |10⟩, |11⟩`.

Controlled-X is the CNOT gate.

The implementation constructs CNOT using the general controlled-unitary construction.

Because X is unitary, CNOT is also unitary.

CNOT maps the computational basis as follows:

`|00⟩ → |00⟩`

`|01⟩ → |01⟩`

`|10⟩ → |11⟩`

`|11⟩ → |10⟩`.

---

## Bell-state case study

The JavaScript and C++ implementations construct the circuit

`|00⟩ → H on qubit 0 → CNOT`.

The resulting state is

`(|00⟩ + |11⟩)/sqrt(2)`.

The computational-basis probabilities are approximately:

- probability of `|00⟩`: 1/2;
- probability of `|01⟩`: 0;
- probability of `|10⟩`: 0;
- probability of `|11⟩`: 1/2.

This example demonstrates several operator concepts at once:

- H is unitary;
- CNOT is unitary;
- tensor-product spaces are required for multiple qubits;
- composition of operators produces the circuit transformation;
- normalization is preserved;
- measurement produces probabilistic outcomes.

---

## Time evolution and Hermitian generators

For a closed quantum system, time evolution is represented by a unitary operator.

A standard expression is

`U(t) = exp(-iHt)`

where `H` is the Hamiltonian.

The Hamiltonian is Hermitian.

The Hermiticity of `H` ensures that the generator produces unitary evolution under the standard finite-dimensional formulation.

The Python implementation includes a direct Taylor-series matrix exponential to demonstrate this connection.

The implementation is intentionally educational. A Taylor series is not the preferred production algorithm for arbitrary large matrices.

Production numerical software commonly uses algorithms based on techniques such as scaling and squaring, Padé approximants, Krylov methods, or specialized eigendecomposition depending on the matrix and problem structure.

---

## Rotation operators

Single-qubit rotation operators can be written as

`Rₓ(θ) = exp(-iθX/2)`

`Rᵧ(θ) = exp(-iθY/2)`

`R_z(θ) = exp(-iθZ/2)`.

Because X, Y, and Z are Hermitian, these exponentials are unitary.

The implementations provide explicit matrix forms for the rotations.

For example,

`R_z(θ) = [[e^(-iθ/2), 0], [0, e^(iθ/2)]]`.

The phase factors have unit magnitude, which ensures unitarity.

---

## Python implementation

The Python implementation is designed as a mathematical study file.

### Complex arithmetic

The standard Python `complex` type is used for complex scalars. Operations such as conjugation, multiplication, and magnitude are provided by the language and standard library.

### Matrix representation

Matrices are represented as lists of lists.

For example, the identity operator is represented internally as a nested list corresponding to

`[[1, 0], [0, 1]]`.

The implementation provides:

- matrix addition;
- matrix subtraction;
- scalar multiplication;
- matrix multiplication;
- matrix-vector multiplication;
- transpose;
- conjugate transpose;
- trace;
- identity construction.

### Operator classification

The functions `is_hermitian()`, `is_unitary()`, and `is_normal()` implement the mathematical definitions.

`is_hermitian()` compares an operator with its adjoint.

`is_unitary()` checks both

`U†U = I`

and

`UU† = I`.

`is_normal()` checks

`A†A = AA†`.

### Observable calculations

The function `expectation_value()` evaluates

`⟨ψ|A|ψ⟩`.

The implementation explicitly normalizes the state before calculating the expectation value. This prevents an accidental unnormalized input from being treated as a physical state.

### Measurement

The measurement demonstration converts amplitude magnitudes into probabilities and samples computational-basis outcomes.

A deterministic random seed is used in the educational example so that repeated executions produce reproducible demonstration output.

---

## JavaScript implementation

The JavaScript implementation uses a custom `Complex` class.

This makes the complex-number operations explicit instead of relying on a built-in complex scalar type.

The class provides:

- addition;
- subtraction;
- multiplication;
- scalar multiplication;
- conjugation;
- squared magnitude;
- magnitude;
- approximate equality;
- formatted output.

The matrix layer then builds on this class.

### Matrix operations

The JavaScript file implements:

- rectangular-matrix validation;
- matrix multiplication;
- matrix-vector multiplication;
- matrix addition;
- matrix subtraction;
- conjugate transpose;
- identity matrices;
- tensor products.

This separation mirrors the mathematical dependency structure:

`Complex → Vector/Matrix → Operator → Quantum Circuit`.

### QuantumCircuit class

The `QuantumCircuit` class maintains:

- qubit count;
- state-vector dimension;
- current state vector.

The state vector begins in the computational basis state `|00...0⟩`.

Single-qubit gates are expanded to the full system using tensor products.

The circuit rejects non-unitary gates.

After each transformation, the state is normalized to control the accumulation of small floating-point errors.

The simulator deliberately limits dense circuits to a small number of qubits.

---

## C++ case study

The C++ implementation models a small state-vector quantum engine.

The case study is structured around a realistic computational requirement: validate operators, apply gates to a state vector, measure observables, and sample measurement outcomes.

### Main components

The implementation contains:

- `Complex` as an alias for `std::complex<double>`;
- `Vector` as a complex state vector;
- `Matrix` as a dense complex matrix;
- matrix construction and validation functions;
- vector normalization and inner products;
- adjoint and operator-classification functions;
- standard quantum gates;
- tensor-product construction;
- controlled-unitary construction;
- measurement sampling;
- `QuantumCircuit`;
- `VariationalCircuit`.

### Why C++ is useful here

C++ provides explicit control over data structures and memory representation.

The implementation makes several production-oriented concerns visible:

- dimensional validation;
- exception-based failure handling;
- dense matrix computational cost;
- explicit numerical tolerance;
- deterministic random-number seeding;
- class-based encapsulation;
- separation between mathematical primitives and circuit-level behavior.

The standard library is sufficient for the implementation.

---

## Variational observable case study

The C++ implementation defines a one-qubit Hamiltonian

`H = 0.8Z + 0.3X`.

Since X and Z are Hermitian and their coefficients are real, H is Hermitian.

A parameterized circuit prepares a state using:

`H`

followed by

`Rᵧ(θ)`.

The circuit then evaluates

`E(θ) = ⟨ψ(θ)|H|ψ(θ)⟩`.

This resembles the core calculation used in variational quantum algorithms, where a parameterized quantum state is evaluated against a Hamiltonian or other Hermitian cost observable.

The implementation focuses on the operator mathematics rather than optimization of the parameter.

---

## Important distinctions

| Property | Hermitian | Unitary |
| --- | --- | --- |
| Defining condition | `A† = A` | `U†U = I` |
| Inverse | Not necessarily present | `U⁻¹ = U†` |
| Eigenvalues | Real | Magnitude 1 |
| Preserves norms | Not generally | Yes |
| Represents an observable | Yes, in standard quantum formalism | Not generally |
| Represents reversible state evolution | Not generally | Yes |
| Normal | Always | Always |
| Can be both | Yes | Yes |

Neither category should be treated as a synonym for "operator."

A general operator can belong to neither category.

---

## Hermitian versus symmetric

A common mistake is to use the terms symmetric and Hermitian interchangeably.

A real matrix is symmetric when

`Aᵀ = A`.

A complex matrix is Hermitian when

`A† = A`.

For real-valued matrices, these definitions coincide.

For complex-valued matrices, conjugation is essential.

For example,

`[[1, i], [-i, 2]]`

is Hermitian but not an ordinary symmetric matrix because the off-diagonal entries differ.

---

## Hermitian versus unitary

Another common mistake is assuming that an observable must be a valid reversible gate.

This is false.

A Hermitian matrix such as

`[[2, 0], [0, -3]]`

is an observable but is not unitary.

Likewise, a phase gate can be unitary without being Hermitian.

Some special operators, such as Pauli X, satisfy both conditions.

---

## Normal operators

Normality provides a useful broader classification.

An operator is normal when

`A†A = AA†`.

Hermitian and unitary operators are subsets of the normal operators.

The normality condition is particularly useful because normal matrices can be unitarily diagonalized in finite-dimensional complex vector spaces.

This makes normal operators a natural bridge between arbitrary operators and the more specialized Hermitian and unitary classes.

---

## Edge cases

### Zero vector

The zero vector cannot be normalized.

The implementations explicitly reject normalization of

`[0, 0]`.

### Non-square matrices

An operator on a finite-dimensional vector space is represented by a square matrix when it maps the space to itself.

The implementations reject non-square matrices when checking Hermitian or unitary properties.

### Dimension mismatch

Matrix-vector multiplication requires the number of matrix columns to equal the vector dimension.

Matrix multiplication requires the number of columns of the first matrix to equal the number of rows of the second.

The implementations validate these conditions.

### Non-unitary circuit gate

The C++ and JavaScript circuit layers reject non-unitary gates.

This prevents an invalid transformation from silently being treated as an ideal quantum gate.

### Floating-point error

Mathematical identities such as

`U†U = I`

are exact in theory.

Computer representations use finite-precision floating-point numbers, so computed values may differ from the exact result by a small amount.

The implementations therefore use tolerance-based comparisons.

---

## Numerical considerations

### Absolute tolerance

The examples generally use a tolerance near `10^-10`.

A comparison is therefore based on whether the numerical difference is sufficiently small rather than whether two floating-point values are exactly identical.

### Why exact equality is dangerous

A calculation involving square roots, trigonometric functions, complex arithmetic, or repeated matrix multiplication may produce values such as

`0.9999999999999998`

instead of exactly

`1`.

An exact equality test could incorrectly classify the result as invalid.

### Choosing tolerances

A tolerance should reflect:

- floating-point precision;
- problem size;
- conditioning;
- number of operations;
- expected numerical error;
- required application accuracy.

A fixed tolerance is useful for educational examples but should not automatically be treated as a universal production setting.

---

## Performance considerations

For dense matrices of dimension `N × N`, ordinary matrix multiplication has cubic time complexity:

`O(N³)`.

Matrix-vector multiplication requires

`O(N²)`.

For a quantum state of `n` qubits, the state vector contains

`2ⁿ`

complex amplitudes.

A dense operator therefore contains

`4ⁿ`

matrix elements.

This exponential growth quickly becomes the dominant constraint.

For this reason, the implementations intentionally remain small.

Real quantum-computing software may use:

- sparse representations;
- tensor-network methods;
- gate-local state updates;
- matrix-free operators;
- specialized linear algebra kernels;
- GPU acceleration;
- distributed state vectors;
- stabilizer representations for suitable circuits;
- problem-specific decompositions.

The appropriate representation depends on the operator structure and the computational problem.

---

## Tensor-product performance trade-off

The educational implementations explicitly construct full tensor-product matrices.

This is mathematically transparent but can be inefficient.

For example, applying a one-qubit gate to an `n`-qubit state does not require constructing a complete `2ⁿ × 2ⁿ` dense matrix in an optimized simulator.

A production simulator can update appropriate amplitudes directly.

The explicit tensor-product construction is therefore best understood as a demonstration of the mathematical definition rather than an optimal implementation strategy.

---

## Security and correctness considerations

Hermitian and unitary checks can also be viewed as validation mechanisms.

A system accepting externally supplied operator matrices should validate:

- dimensions;
- finite numerical values;
- matrix shape;
- Hermiticity where an observable is required;
- unitarity where a reversible gate is required;
- state normalization;
- measurement-probability normalization.

Invalid input should be rejected rather than silently corrected when correctness matters.

For scientific or engineering systems, validation failures should be observable through structured errors or logging.

The examples use exceptions for invalid dimensions, invalid states, invalid gates, and unsupported simulator sizes.

---

## Common implementation mistakes

### Using transpose instead of adjoint

Incorrect for complex operators:

`Aᵀ`.

Correct:

`A†`.

### Forgetting conjugation in the inner product

The complex inner product is

`⟨a|b⟩ = Σ aᵢ* bᵢ`.

Using `Σ aᵢbᵢ` instead changes the mathematical operation.

### Checking only one side of unitarity

For a square matrix, checking `U†U = I` is sufficient mathematically under the usual finite-dimensional assumptions, but explicitly checking both `U†U` and `UU†` is useful in validation code because it makes the intended property clear.

The implementations check both.

### Applying operators in the wrong order

If A acts first and B acts second, the combined operator is

`BA`.

Not

`AB`.

### Treating measurement as unitary

Measurement is not represented as an ordinary reversible unitary transformation.

Unitary evolution changes amplitudes while preserving normalization. Measurement produces probabilistic classical outcomes and generally changes the quantum state according to the measurement model.

### Ignoring numerical tolerances

Exact floating-point comparisons can produce false failures.

### Assuming every operator is Hermitian or unitary

Most mathematical operators do not automatically satisfy either condition.

---

## Limitations of the implementations

The implementations intentionally use dense matrix representations.

They are therefore not intended to be high-performance quantum simulators.

The Python matrix-exponential routine uses a direct Taylor-series expansion for educational clarity. It does not implement a production-grade matrix exponential.

The small eigenvalue demonstration in Python is limited to 2 × 2 matrices.

The JavaScript and C++ simulators use explicit dense state vectors and restrict circuit size for practical memory reasons.

The implementations also focus on pure states and ideal unitary circuit evolution. They do not attempt to model the full range of quantum channels, noise models, density matrices, or general positive-operator-valued measurements.

These limitations preserve mathematical transparency while keeping the implementations self-contained.

---

## Advanced conceptual relationships

### Hermitian operators and real spectra

For a Hermitian operator,

`A† = A`.

The spectral theorem implies that A has an orthonormal eigenbasis and real eigenvalues.

This permits an observable to be expressed through its spectral decomposition.

### Unitary operators and the unit circle

If

`U|v⟩ = λ|v⟩`

and U is unitary, then

`|λ| = 1`.

Thus unitary eigenvalues lie on the complex unit circle.

They can be written as

`λ = e^(iθ)`.

### Hermitian generators of unitary evolution

If H is Hermitian, then

`U(t) = exp(-iHt)`

is unitary under the standard finite-dimensional construction.

This creates a fundamental connection:

`Hermitian generator → unitary evolution`.

### Logarithms of unitary operators

Under suitable conditions, a unitary operator can be expressed as an exponential

`U = exp(iK)`

for a Hermitian operator K, subject to choices associated with eigenvalue phases and matrix logarithms.

This means Hermitian and unitary operators are connected through exponential mappings, although the mapping is not represented uniquely in every context.

---

## Implementation correspondence

| Concept | Python | JavaScript | C++ |
| --- | --- | --- | --- |
| Complex numbers | Built-in `complex` | `Complex` class | `std::complex<double>` |
| Adjoint | `adjoint()` | `adjoint()` | `adjoint()` |
| Hermitian check | `is_hermitian()` | `isHermitian()` | `isHermitian()` |
| Unitary check | `is_unitary()` | `isUnitary()` | `isUnitary()` |
| Normal check | `is_normal()` | `isNormal()` | `isNormal()` |
| Expectation value | `expectation_value()` | `expectationValue()` | `expectationValue()` |
| Projectors | `P0`, `P1` | `PROJECTOR_0`, `PROJECTOR_1` | projector functions |
| Tensor product | `tensor_product()` | `tensorProduct()` | `tensorProduct()` |
| Controlled-U | `controlled_unitary()` | `controlledUnitary()` | `controlledUnitary()` |
| Measurement | `sample_measurement()` | `measureComputationalBasis()` | `measure()` |
| Circuit abstraction | procedural demonstrations | `QuantumCircuit` | `QuantumCircuit` |
| Variational example | time-evolution demonstrations | circuit demonstrations | `VariationalCircuit` |

---

## Practical applications

Hermitian and unitary operators occur throughout quantum information and applied linear algebra.

### Quantum measurement

Hermitian operators model observables and provide real measurement eigenvalues.

### Quantum gates

Unitary matrices model ideal reversible quantum gates.

### Quantum simulation

Hamiltonians and unitary time-evolution operators are central to numerical simulation of quantum systems.

### Quantum algorithms

Circuit gates are composed from unitary transformations, while algorithmic outputs are obtained through measurement.

### Variational quantum methods

Parameterized unitary circuits prepare candidate states, while Hermitian Hamiltonians or cost observables provide expectation values used as objective functions.

### Signal and numerical processing

Unitary transformations also appear in broader areas of applied mathematics where norm and inner-product preservation are useful.

### Linear algebra

Hermitian, unitary, and normal matrices form important classes for diagonalization, spectral analysis, stability analysis, and numerical computation.

---

## Conceptual workflow

A typical operator-based quantum calculation can be viewed as:

`Define state`

→ `Validate normalization`

→ `Define operator`

→ `Classify operator`

→ `Apply operator or evaluate expectation`

→ `Validate numerical properties`

→ `Measure or analyze result`

For a circuit:

`Initial state`

→ `Unitary gate`

→ `Unitary gate`

→ `Controlled unitary`

→ `Final state`

→ `Measurement`

The C++ case study follows this pattern explicitly.

---

## Mathematical reference

### Adjoint

`A† = (A*)ᵀ`

### Hermitian condition

`A† = A`

### Unitary condition

`U†U = UU† = I`

### Normal condition

`A†A = AA†`

### Hermitian expectation value

`⟨A⟩ = ⟨ψ|A|ψ⟩`

### Variance

`Var(A) = ⟨A²⟩ - ⟨A⟩²`

### Eigenvalue equation

`A|v⟩ = λ|v⟩`

### Tensor product

`A ⊗ B`

### Unitary inverse

`U⁻¹ = U†`

### Norm preservation

`||U|ψ⟩|| = |||ψ⟩||`

### Inner-product preservation

`⟨Uψ|Uφ⟩ = ⟨ψ|φ⟩`

### Time evolution

`U(t) = exp(-iHt)`

where H is Hermitian.

---

## File structure

The four study components are:

- Python source file containing the mathematical demonstrations and numerical examples.
- JavaScript source file containing a custom complex-number implementation and state-vector circuit simulator.
- C++ source file containing the structured quantum operator and circuit case study.
- This README documenting the concepts and their implementation correspondence.

Each source file is self-contained and avoids unnecessary external dependencies.

---

## Execution characteristics

The Python implementation can be executed with a standard Python 3 installation.

The JavaScript implementation can be executed in a modern Node.js runtime.

The C++ implementation is designed for C++17 or later and uses only the standard library.

The examples intentionally operate on small matrices and small quantum registers because the dense mathematical representation grows rapidly with system size.
