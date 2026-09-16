# Quantum States: State Vectors and Notation

## Introduction

A quantum state describes the physical condition of a quantum system. For a pure state, one of the most important mathematical representations is the **state vector**, commonly written using **Dirac notation**.

A single qubit has two computational-basis states:

`|0>` and `|1>`

A general pure single-qubit state can be written as:

`|ψ> = α|0> + β|1>`

where `α` and `β` are generally complex numbers called **probability amplitudes**.

The amplitudes are constrained by normalization:

`|α|² + |β|² = 1`

The quantities `|α|²` and `|β|²` are measurement probabilities in the computational basis.

This project develops state-vector concepts from elementary notation to multi-qubit systems, operators, basis transformations, entanglement, density matrices, and numerical simulation. The Python and JavaScript implementations emphasize the mathematical model and executable demonstrations. The C++ implementation develops a more structured two-qubit case study resembling a small quantum-state analysis engine.

## Fundamental terminology

### Quantum state

A quantum state is a mathematical description of all information available about a quantum system within the chosen formalism.

For a pure state, a normalized state vector is sufficient.

For a mixed state, a density matrix is generally required.

### Qubit

A qubit is a two-level quantum system. Its computational basis is conventionally written as:

`|0>` and `|1>`

Unlike a classical bit, a qubit may occupy a coherent superposition of these basis states.

### Ket

A **ket** is a column-vector representation written with a right angle bracket:

`|ψ>`

For example:

`|0> = [1, 0]ᵀ`

and

`|1> = [0, 1]ᵀ`

### Bra

A **bra** is the conjugate transpose of a ket:

`<ψ|`

If:

`|ψ> = [α, β]ᵀ`

then:

`<ψ| = [α*, β*]`

where `*` denotes complex conjugation.

### State vector

A state vector is a vector of complex amplitudes representing a pure quantum state relative to a specified basis.

For a single qubit:

`|ψ> = [α, β]ᵀ`

For two qubits, the state vector has four amplitudes:

`|ψ> = [α₀₀, α₀₁, α₁₀, α₁₁]ᵀ`

For `n` qubits, the state vector has `2ⁿ` amplitudes.

## Computational basis

The computational basis is the standard basis used for qubits.

For one qubit:

`|0> = [1, 0]ᵀ`

`|1> = [0, 1]ᵀ`

For two qubits:

`|00> = [1, 0, 0, 0]ᵀ`

`|01> = [0, 1, 0, 0]ᵀ`

`|10> = [0, 0, 1, 0]ᵀ`

`|11> = [0, 0, 0, 1]ᵀ`

The ordering used in the implementations is:

`|00>, |01>, |10>, |11>`

For three qubits, there are eight basis states, from `|000>` through `|111>`.

The general rule is:

`n qubits → 2ⁿ computational-basis states`

## Probability amplitudes

The coefficients of a quantum state are amplitudes rather than direct probabilities.

For:

`|ψ> = α|0> + β|1>`

the computational-basis measurement probabilities are:

`P(0) = |α|²`

`P(1) = |β|²`

The Born rule requires:

`P(0) + P(1) = 1`

which follows from normalization.

A complex amplitude such as:

`(1 + i)/2`

is not itself a probability. Its probability contribution is:

`|(1 + i)/2|² = 1/2`

This distinction is fundamental to quantum-state calculations.

## Normalization

A physical state vector must have unit norm.

For:

`|ψ> = α|0> + β|1>`

normalization means:

`<ψ|ψ> = 1`

or equivalently:

`|α|² + |β|² = 1`

For a general vector:

`v = [v₀, v₁, ..., vₙ₋₁]ᵀ`

the squared norm is:

`||v||² = Σᵢ |vᵢ|²`

The normalized vector is:

`v_normalized = v / ||v||`

The Python, JavaScript, and C++ implementations normalize state vectors during construction.

The zero vector cannot be normalized because division by its norm would require division by zero.

## Superposition

A superposition is a linear combination of basis states.

The most familiar single-qubit examples are:

`|+> = (|0> + |1>) / √2`

and

`|-> = (|0> - |1>) / √2`

Both have computational-basis probabilities:

`P(0) = 1/2`

`P(1) = 1/2`

The difference between them is their relative phase.

The state vectors are:

`|+> = [1/√2, 1/√2]ᵀ`

`|-> = [1/√2, -1/√2]ᵀ`

Their amplitudes have equal magnitudes but different signs.

## Global phase

Suppose:

`|ψ'> = e^{iφ}|ψ>`

where `φ` is a real phase angle.

The entire state has been multiplied by the same phase factor. This is called a **global phase**.

For pure-state quantum mechanics, a global phase does not change measurement probabilities or the physical pure state.

For example:

`|+>`

and

`i|+>`

have the same computational-basis probabilities.

The implementations explicitly demonstrate this property.

A global phase must be distinguished from a relative phase.

## Relative phase

Consider:

`|ψ₁> = (|0> + |1>)/√2`

and:

`|ψ₂> = (|0> - |1>)/√2`

Their amplitudes have the same magnitudes, but their relative phase differs by π.

Relative phase can affect interference and therefore can affect the result of later operations and measurements.

This is one of the important reasons that a quantum state cannot be treated as an ordinary probability distribution.

A classical probability distribution might store only:

`[0.5, 0.5]`

but the quantum states:

`(|0> + |1>)/√2`

and

`(|0> - |1>)/√2`

require different amplitude information.

## Inner product

The inner product between two states is written:

`<φ|ψ>`

For state vectors `φ` and `ψ`:

`<φ|ψ> = Σᵢ φᵢ* ψᵢ`

The first vector is complex-conjugated.

This is important when amplitudes are complex.

For normalized states:

`|<φ|ψ>| ≤ 1`

If:

`<φ|ψ> = 0`

the states are orthogonal.

The computational basis states satisfy:

`<0|0> = 1`

`<1|1> = 1`

`<0|1> = 0`

`<1|0> = 0`

The Python, JavaScript, and C++ implementations explicitly implement complex conjugation in the inner product.

## Orthogonality

Orthogonal states have zero inner product.

The states `|+>` and `|->` are orthogonal:

`<+|-> = 0`

Orthogonality is important because orthogonal quantum states can be perfectly distinguished by a suitable measurement.

The implementation checks orthogonality numerically using a tolerance rather than requiring floating-point values to equal exactly zero.

## Outer product

The outer product of a ket and bra is written:

`|ψ><φ|`

For a pure state:

`ρ = |ψ><ψ|`

This creates a matrix rather than a scalar.

For:

`|+> = [1/√2, 1/√2]ᵀ`

the density matrix is:

`ρ = 1/2 [[1, 1], [1, 1]]`

The Python, JavaScript, and C++ implementations calculate this matrix directly.

## State-vector notation and coordinate systems

A state vector is always expressed relative to a basis.

The physical state is not tied to the computational basis. Changing the basis changes its coordinates.

If the columns of a unitary matrix `U` are the vectors of a new orthonormal basis, the new coordinates can be obtained through:

`U†|ψ>`

where `U†` is the conjugate transpose of `U`.

The Hadamard matrix is:

`H = 1/√2 [[1, 1], [1, -1]]`

Its columns correspond to the `|+>` and `|->` basis states.

For example, expressing `|0>` in the X basis gives equal amplitudes for `|+>` and `|->`.

This means that measuring `|0>` in the X basis produces either X-basis outcome with probability `1/2`.

## Operators

An operator is a mathematical transformation acting on a state.

For a state `|ψ>` and operator `A`:

`A|ψ>`

is the transformed vector.

Common single-qubit operators include the Pauli matrices.

### Pauli-X

`X = [[0, 1], [1, 0]]`

It exchanges the computational basis states:

`X|0> = |1>`

`X|1> = |0>`

### Pauli-Y

`Y = [[0, -i], [i, 0]]`

It also exchanges basis states while introducing phase factors.

### Pauli-Z

`Z = [[1, 0], [0, -1]]`

It leaves `|0>` unchanged and changes the phase of `|1>`:

`Z|0> = |0>`

`Z|1> = -|1>`

### Hadamard

`H = 1/√2 [[1, 1], [1, -1]]`

The Hadamard transformation creates computational-basis superpositions:

`H|0> = |+>`

`H|1> = |->`

## Unitary operators

Closed-system quantum evolution is represented by unitary operators.

A matrix `U` is unitary when:

`U†U = I`

where `I` is the identity matrix.

Unitary transformations preserve inner products and therefore preserve state normalization.

The implementations explicitly calculate:

`U†U`

and compare it with the identity matrix.

The matrices `X`, `Y`, `Z`, and `H` are all unitary.

Not every arbitrary matrix is a valid closed-system quantum-evolution operator.

Measurement operations and open-system processes require a broader formalism than simply applying an arbitrary matrix as if it were a unitary gate.

## Measurement

Quantum measurement maps quantum information to a classical outcome.

When measuring:

`|ψ> = Σᵢ αᵢ|i>`

in the computational basis, the probability of outcome `i` is:

`P(i) = |αᵢ|²`

The state vector describes amplitudes before measurement. A single experimental measurement produces one outcome, not a list of probabilities.

The probability distribution becomes visible statistically through repeated measurements.

The Python, JavaScript, and C++ implementations include repeated measurement simulations.

For a state with theoretical probabilities:

`[0.5, 0.5]`

a sufficiently large number of simulated measurements should produce frequencies approaching those probabilities, subject to statistical fluctuation.

## Measurement basis

The probabilities depend on the measurement basis.

A state can be deterministic in one basis and probabilistic in another.

For example:

`|0>`

is deterministic in the computational Z basis:

`P(0) = 1`

`P(1) = 0`

But in the X basis:

`|0> = (|+> + |->)/√2`

so:

`P(+) = 1/2`

`P(-) = 1/2`

This is a direct demonstration of why the state vector and the measurement basis must both be specified when discussing measurement probabilities.

## Expectation values

For an observable `A` and normalized state `|ψ>`, the expectation value is:

`<A> = <ψ|A|ψ>`

The expectation value is the statistical mean obtained from many repeated measurements of that observable on identically prepared states.

For a Hermitian observable, the expectation value is real.

For the `|+>` state:

`<X> = 1`

`<Y> = 0`

`<Z> = 0`

The implementations calculate these values directly using matrix-vector multiplication and the inner product.

## Variance

The variance of an observable is:

`Var(A) = <A²> - <A>²`

The standard deviation is the square root of the variance.

For `|+>`:

`Var(X) = 0`

because `|+>` is an eigenstate of `X`.

For `Z`, the variance is nonzero because `|+>` is not an eigenstate of `Z`.

The Python and C++ implementations demonstrate this calculation.

## Bloch-sphere representation

Every pure single-qubit state can be represented, up to global phase, using two angles:

`|ψ> = cos(θ/2)|0> + e^(iφ) sin(θ/2)|1>`

The corresponding Bloch vector is:

`x = 2 Re(α*β)`

`y = 2 Im(α*β)`

`z = |α|² - |β|²`

For a pure state:

`x² + y² + z² = 1`

Important examples include:

`|0>` → `(0, 0, 1)`

`|1>` → `(0, 0, -1)`

`|+>` → `(1, 0, 0)`

`(|0> + i|1>)/√2` → `(0, 1, 0)`

The Python and JavaScript implementations calculate these coordinates directly.

The Bloch sphere is particularly useful for visualizing single-qubit states, phase relationships, and rotations. It does not directly provide an equivalent three-dimensional visualization for arbitrary multi-qubit pure states.

## Tensor products

When independent quantum systems are combined, their state spaces are combined using the tensor product.

For two states:

`|ψ>`

and:

`|φ>`

the composite state is:

`|ψ> ⊗ |φ>`

or:

`|ψφ>`

If both are qubits, the resulting state has dimension four.

For example:

`|+> ⊗ |+>`

produces:

`1/2(|00> + |01> + |10> + |11>)`

The implementation provides vector and matrix tensor-product functions.

The tensor product is essential because multi-qubit systems do not simply concatenate independent vectors. Their combined state space has multiplicative dimension.

## Multi-qubit state vectors

An `n`-qubit state has `2ⁿ` computational-basis amplitudes.

For two qubits:

`|ψ> = α₀₀|00> + α₀₁|01> + α₁₀|10> + α₁₁|11>`

For three qubits:

`|ψ> = Σ αᵢ|i>`

with eight amplitudes.

This exponential growth has major computational consequences.

A state vector for `n` qubits requires storage proportional to:

`O(2ⁿ)`

A dense operator acting on an `n`-qubit state requires a matrix with:

`2ⁿ × 2ⁿ = 4ⁿ`

entries.

This is why general classical simulation becomes increasingly expensive as the number of qubits grows.

## Product states

A two-qubit state is a product state if it can be written as:

`|ψ> = |a> ⊗ |b>`

For:

`|++>`

this factorization exists.

The two-qubit coefficient matrix can be written as:

`[[a₀₀, a₀₁], [a₁₀, a₁₁]]`

For a pure two-qubit state, separability is equivalent to the matrix having rank one.

For a 2 × 2 matrix this means:

`a₀₀a₁₁ - a₀₁a₁₀ = 0`

The implementations use this determinant condition as a compact two-qubit separability test.

## Entangled states

An entangled state cannot be represented as a tensor product of independent subsystem state vectors.

A central example is the Bell state:

`|Φ⁺> = (|00> + |11>)/√2`

Its vector is:

`[1/√2, 0, 0, 1/√2]ᵀ`

The computational-basis probabilities are:

`P(00) = 1/2`

`P(01) = 0`

`P(10) = 0`

`P(11) = 1/2`

The state is not a product state.

If the first qubit is measured in the computational basis, the probability of obtaining `0` is `1/2`, and the probability of obtaining `1` is `1/2`.

The correlations between the subsystems are part of the joint quantum state and cannot be reproduced by simply assigning each subsystem its own independent pure state vector.

## Partial measurement

For a two-qubit state ordered as:

`|00>, |01>, |10>, |11>`

the probability that the first qubit is `0` is:

`P(first = 0) = |α₀₀|² + |α₀₁|²`

The probability that the first qubit is `1` is:

`P(first = 1) = |α₁₀|² + |α₁₁|²`

The implementations demonstrate these marginal probabilities for the Bell state.

This is an important distinction from measuring the entire register. A partial measurement groups several computational-basis outcomes according to the value of the measured subsystem.

## Density matrices

A pure state can be represented using:

`ρ = |ψ><ψ|`

The density-matrix representation is useful because it extends naturally to mixed states and subsystem descriptions.

For a valid quantum density matrix:

`ρ† = ρ`

`Tr(ρ) = 1`

and:

`ρ` is positive semidefinite.

For a pure state:

`Tr(ρ²) = 1`

The quantity:

`Tr(ρ²)`

is called the purity.

A pure state has purity one. A genuinely mixed state has purity below one.

The implementations calculate density matrices for pure states and verify their trace and purity.

## Why state vectors are not sufficient for every situation

A state vector is a complete representation of a pure state.

It is not, by itself, a complete representation of a general mixed state.

Suppose a system is prepared as `|0>` with probability `1/2` and `|1>` with probability `1/2`. This is represented by the mixed density matrix:

`ρ = 1/2|0><0| + 1/2|1><1|`

which is:

`ρ = [[1/2, 0], [0, 1/2]]`

This is not the same physical state as:

`|+> = (|0> + |1>)/√2`

even though both give equal computational-basis probabilities.

The superposition contains coherence information represented by the off-diagonal elements of its density matrix.

## Pure-state fidelity

For two pure states:

`|ψ>` and `|φ>`

the fidelity is:

`F = |<ψ|φ>|²`

Its value is between zero and one.

For identical pure states:

`F = 1`

For orthogonal states:

`F = 0`

The C++ and Python implementations use this definition.

A value of one means the pure states are physically equivalent up to global phase.

## Python implementation

The Python program develops the mathematical ideas incrementally.

### Complex arithmetic

Python provides native complex numbers, allowing amplitudes to be represented naturally as values such as:

`1 + 2j`

The script implements vector and matrix operations directly instead of relying on an external numerical package.

This makes the relationship between the mathematics and implementation explicit.

### `QuantumState` class

The `QuantumState` class stores amplitudes as an immutable tuple.

Its constructor:

- validates that the dimension is nonzero
- requires a power-of-two dimension for qubit registers
- normalizes the amplitudes

The class exposes:

- `dimension`
- `qubit_count`
- `probability()`
- `probabilities()`
- `ket()`
- `apply()`

This gives the script a reusable abstraction instead of representing every state as an unrelated list.

### Mathematical operations

The Python implementation includes:

- vector normalization
- vector scaling
- inner products
- outer products
- matrix-vector multiplication
- matrix multiplication
- matrix adjoints
- matrix powers

These operations provide the foundation for state evolution and observable calculations.

### Measurement

The measurement simulator uses the Born probabilities to generate classical outcomes.

A fixed random seed can be used for reproducible demonstrations.

The output compares theoretical probabilities with empirical frequencies.

### Multi-qubit representation

Tensor products construct larger state vectors.

The two-qubit Bell states demonstrate that the same vector representation can describe both product and entangled states.

### Density matrices

The Python implementation constructs:

`ρ = |ψ><ψ|`

and evaluates:

`Tr(ρ)`

and:

`Tr(ρ²)`

This connects state-vector notation to the more general density-matrix formalism.

## JavaScript implementation

The JavaScript implementation deliberately differs from the Python implementation in one important technical respect: JavaScript does not provide a built-in complex-number primitive.

A custom `Complex` class therefore implements:

- addition
- subtraction
- multiplication
- conjugation
- scaling
- magnitude
- magnitude squared
- phase
- approximate equality
- polar representation

This demonstrates a practical issue encountered when implementing quantum mathematics in a language without native complex-number support.

### Object-oriented state representation

The JavaScript `QuantumState` class performs normalization and dimensional validation during construction.

The state can then:

- report its dimension
- report its qubit count
- calculate measurement probabilities
- apply operators
- produce ket notation

This resembles how a small application-level quantum-state model could be structured.

### Deterministic measurement simulation

Standard JavaScript `Math.random()` does not provide a standard seed interface.

The implementation therefore includes a small deterministic pseudo-random generator for demonstrations where reproducible results are useful.

This is a software-engineering convenience, not a model of a physical quantum random-number generator.

### Browser and application relevance

Although the file is executable in a JavaScript runtime such as Node.js, its mathematical classes could also serve as the foundation for browser-side educational interfaces.

A browser application could connect these state operations to:

- interactive state-vector displays
- measurement controls
- Bloch-sphere visualizations
- basis-selection controls
- probability charts
- gate-sequence interfaces

The implementation itself remains dependency-free.

## C++ case study

The C++ program is organized as a small quantum-state analysis engine.

The modeled scenario is a two-qubit communication register.

The system:

- initializes a register
- constructs a product superposition
- constructs a Bell state
- calculates measurement probabilities
- performs partial measurement calculations
- simulates repeated measurements
- applies quantum operators
- calculates expectation values
- checks operator unitarity
- changes basis
- constructs density matrices
- calculates purity
- calculates pure-state fidelity
- constructs multi-qubit operators
- validates mathematical invariants
- demonstrates failure conditions

This is intentionally more structured than a collection of isolated syntax examples.

### C++ complex numbers

C++ uses:

`std::complex<double>`

for probability amplitudes.

This provides native complex arithmetic while keeping the implementation within the C++ standard library.

### `QuantumState`

The `QuantumState` class owns a vector of complex amplitudes.

Its constructor normalizes the vector and validates the dimension.

The class exposes:

- `amplitudes()`
- `dimension()`
- `qubitCount()`
- `probability()`
- `probabilities()`
- `apply()`
- `ket()`

The design keeps state representation and common state operations together.

### Matrix representation

Matrices are represented as:

`std::vector<std::vector<std::complex<double>>>`

This is straightforward for an educational implementation.

For high-performance quantum simulation, more specialized representations would normally be considered because dense matrix storage scales poorly.

### Tensor products

The C++ implementation provides tensor-product overloads for both vectors and matrices.

For vectors:

`|a> ⊗ |b>`

constructs a composite state.

For operators:

`A ⊗ B`

constructs a composite operator.

For two qubits, a single-qubit operator of dimension two becomes a four-by-four operator after tensoring.

### Bell-state case study

The C++ program creates:

`|Φ⁺> = (|00> + |11>)/√2`

It then checks whether the state can be represented as a tensor product.

The determinant condition:

`a₀₀a₁₁ - a₀₁a₁₀ = 0`

is used to identify separability for pure two-qubit states.

The Bell state fails this condition and is therefore entangled.

### Partial measurement

The program calculates:

`P(first qubit = 0)`

and:

`P(first qubit = 1)`

by summing the probabilities of the relevant basis states.

This is an example of marginalizing over an unmeasured subsystem.

### Measurement simulation

The C++ implementation uses `std::mt19937` and a uniform distribution to sample outcomes according to the Born probabilities.

A fixed seed is supplied so the demonstration is reproducible.

In an actual physical quantum experiment, the source of randomness is fundamentally different from this classical simulation.

## Conceptual relationship between the three implementations

The three programs represent the same mathematical formalism from different software perspectives.

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Complex numbers | Built-in language support | Custom `Complex` class | `std::complex<double>` |
| State abstraction | `QuantumState` dataclass | `QuantumState` class | `QuantumState` class |
| Vector operations | Explicit functions | Explicit functions | Explicit functions |
| Matrix operations | Nested lists | Nested arrays | STL vectors |
| Measurement simulation | Python random module | Custom seeded generator | `std::mt19937` |
| Single-qubit operators | Direct matrices | Direct matrices | Direct matrices |
| Tensor products | Yes | Yes | Yes |
| Entanglement test | Yes | Yes | Yes |
| Density matrix | Yes | Yes | Yes |
| Basis transformation | Yes | Yes | Yes |
| Main emphasis | Mathematical exploration | Language-level implementation | Structured systems case study |

## State vector versus probability distribution

A probability distribution contains nonnegative real values that sum to one.

A quantum state vector contains complex amplitudes that must satisfy a normalization condition.

These are different mathematical objects.

For example, both:

`|+> = (|0> + |1>)/√2`

and:

`ρ = 1/2|0><0| + 1/2|1><1|`

produce equal probabilities when measured in the computational basis.

They are nevertheless different quantum states.

The first is a coherent pure superposition.

The second is an incoherent classical mixture.

The distinction becomes visible when changing measurement basis or examining the density matrix.

## State vector versus density matrix

A state vector is compact for a pure state.

A density matrix is more general.

For a pure state:

`ρ = |ψ><ψ|`

For a mixed state:

`ρ = Σᵢ pᵢ |ψᵢ><ψᵢ|`

where:

`pᵢ ≥ 0`

and:

`Σᵢ pᵢ = 1`

Density matrices are particularly useful for:

- mixed states
- subsystems
- noise
- decoherence
- statistical ensembles
- open-system descriptions

The state-vector implementations provide the pure-state foundation from which these concepts can be developed.

## State vector versus global phase

The mathematical vectors:

`|ψ>`

and:

`e^(iφ)|ψ>`

are different vectors unless `φ` is a multiple of `2π`.

For pure-state quantum mechanics, they represent the same physical state.

This does not mean that every phase difference is irrelevant.

A common phase applied to every amplitude is global.

A phase difference between amplitudes is relative and can affect interference.

This distinction is demonstrated by comparing `|+>` with `|->`.

## Edge cases

### Zero vector

`[0, 0]`

cannot represent a physical quantum state because its norm is zero.

The implementations reject it.

### Wrong dimension

A qubit register must have dimension:

`2ⁿ`

for some nonnegative integer `n`.

A vector of length three cannot represent a complete qubit register.

### Non-normalized input

An arbitrary nonzero vector can be normalized.

For example:

`[2, 2]`

becomes:

`[1/√2, 1/√2]`

The normalized state has unit probability total.

### Complex amplitudes

Expressions involving `i` require complex conjugation when calculating inner products and probabilities.

Forgetting conjugation can produce incorrect mathematical results.

### Floating-point zero

Computer arithmetic may produce values such as:

`1.2 × 10⁻¹⁶`

where the exact mathematical result is zero.

The implementations therefore compare floating-point values using tolerances.

## Common mistakes

### Treating amplitudes as probabilities

Incorrect:

`P(0) = α`

Correct:

`P(0) = |α|²`

### Forgetting conjugation

Incorrect inner product:

`Σ αᵢβᵢ`

Correct inner product:

`Σ αᵢ*βᵢ`

### Ignoring normalization

A state vector must satisfy:

`<ψ|ψ> = 1`

before being interpreted as a normalized quantum state.

### Assuming equal probabilities imply equal states

The states `|+>` and `|->` have identical computational-basis probabilities but are different quantum states.

Their relative phase differs.

### Assuming every multi-qubit state is separable

A general two-qubit state cannot always be factored into:

`|a> ⊗ |b>`

Bell states provide a standard counterexample.

### Confusing global and relative phase

A global phase does not change the physical pure state.

A relative phase can affect interference.

### Applying arbitrary matrices as unitary gates

A valid closed-system evolution operator must be unitary.

An arbitrary matrix does not preserve normalization and inner products.

### Comparing floating-point values exactly

Expressions involving square roots and complex arithmetic should generally use numerical tolerances.

## Exceptions and implementation errors

The implementations deliberately validate several invalid situations.

The Python implementation raises exceptions for:

- zero-vector normalization
- invalid state dimensions
- invalid basis indices
- incompatible matrix dimensions
- invalid tensor operations

The JavaScript implementation uses `Error`, `TypeError`, and `RangeError` where appropriate.

The C++ implementation uses standard exceptions such as:

- `std::invalid_argument`
- `std::out_of_range`
- `std::runtime_error`

The C++ `main()` function catches unexpected exceptions and reports them through standard error.

## Numerical precision

Quantum-state calculations often contain irrational values such as:

`1/√2`

and complex phase factors.

Floating-point arithmetic represents these values approximately.

Therefore:

`1/2 + 1/2`

may be represented very close to, but not necessarily exactly equal to, one after a long numerical calculation.

The implementations use tolerances such as:

`1e-9`

or:

`1e-10`

when checking identities such as:

`<ψ|ψ> = 1`

or:

`U†U = I`

The tolerance should be selected according to the numerical scale and algorithm rather than treated as a universal constant.

## Performance considerations

The central performance challenge of state-vector simulation is exponential state-space growth.

For `n` qubits:

`dimension = 2ⁿ`

A state vector therefore requires:

`O(2ⁿ)`

complex values.

If each amplitude occupies 16 bytes using two 64-bit floating-point values, the raw amplitude storage is approximately:

`16 × 2ⁿ bytes`

before accounting for container overhead.

Examples:

| Qubits | Amplitudes |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 10 | 1,024 |
| 20 | 1,048,576 |
| 30 | 1,073,741,824 |

Dense operator storage grows as:

`O(4ⁿ)`

because a general operator has `2ⁿ × 2ⁿ` entries.

For practical simulation, applying a full dense matrix is often much more expensive than applying a local gate using the structure of the operation.

The examples use dense matrices because their mathematical behavior is transparent.

## Memory considerations

For large quantum registers, memory can become the primary constraint.

A simulator storing amplitudes in double-precision complex format needs approximately:

`16 × 2ⁿ bytes`

just for the raw state vector.

The exact memory footprint depends on:

- numeric precision
- container representation
- alignment
- metadata
- temporary buffers
- operator storage
- parallelization strategy

The C++ case study keeps the state sizes intentionally small so that the mathematical operations remain visible.

## Security considerations

State-vector mathematics is not inherently a cybersecurity mechanism.

When quantum-state calculations are incorporated into a software system, ordinary software-security principles still apply.

Relevant concerns include:

- validating dimensions and input values
- preventing uncontrolled memory allocation
- checking numerical assumptions
- avoiding silent failure
- protecting external inputs
- handling malformed data
- separating simulation logic from application interfaces
- testing mathematical invariants

If quantum-state software is connected to a network service, authentication, authorization, logging, rate limiting, and input validation become application-level concerns.

The mathematical representation itself does not provide those protections.

## Implementation considerations

A practical quantum-state library needs to define several conventions explicitly.

### Basis ordering

The implementations use:

`|00>, |01>, |10>, |11>`

for two qubits.

A different library might use a different ordering convention.

Mixing conventions without documenting them can produce apparently incorrect results.

### Endianness

Multi-qubit software must specify which vector index corresponds to which physical or logical qubit.

The choice of most-significant-bit and least-significant-bit ordering can affect tensor-product and gate-application code.

### Precision

Double precision is sufficient for many small educational simulations but does not eliminate numerical error.

Large or ill-conditioned calculations may require more careful numerical methods.

### Sparse representations

Many operators are sparse.

Storing every zero entry in a dense matrix is inefficient for large systems.

Sparse representations can reduce memory usage and computation for suitable problems.

### Local operators

A one-qubit gate acting on a large register does not necessarily require constructing a complete dense `2ⁿ × 2ⁿ` matrix.

A production simulator can exploit tensor structure and apply local operations directly to groups of amplitudes.

## Design considerations

The implementations separate several responsibilities:

- complex arithmetic
- vector arithmetic
- matrix arithmetic
- state validation
- quantum-state representation
- operators
- measurements
- tensor products
- density matrices
- analysis functions

This separation makes mathematical behavior easier to test.

The `QuantumState` abstraction also prevents callers from repeatedly reimplementing normalization and probability calculations.

For production software, additional abstractions could be required for:

- gate circuits
- sparse operators
- mixed states
- noise channels
- measurement operators
- parameterized gates
- automatic differentiation
- parallel execution
- GPU acceleration

Those concerns are outside the narrow state-vector focus of this implementation.

## Real-world relevance

State vectors are foundational to many areas of quantum computing.

They appear in the mathematical description of:

- quantum circuits
- quantum algorithms
- quantum simulation
- quantum communication
- quantum error correction
- quantum information theory
- quantum chemistry simulation
- quantum machine-learning models
- quantum-device simulation

The same core concepts recur across these fields:

`state → operator → transformed state → measurement`

For example, a quantum circuit can be viewed as a sequence of transformations:

`|ψ_final> = Uₙ ... U₂ U₁ |ψ_initial>`

where each `Uᵢ` represents an appropriate quantum operation.

## Core mathematical relationships

The most important relationships demonstrated by the implementations are:

`|ψ> = Σᵢ αᵢ|i>`

`<ψ|ψ> = 1`

`P(i) = |αᵢ|²`

`<φ|ψ> = Σᵢ φᵢ*ψᵢ`

`|ψ><φ| = outer product`

`|ψ₁₂> = |ψ₁> ⊗ |ψ₂>`

`|ψ'> = U|ψ>`

`U†U = I`

`<A> = <ψ|A|ψ>`

`Var(A) = <A²> - <A>²`

`ρ = |ψ><ψ|`

`Tr(ρ) = 1`

`Tr(ρ²) = 1` for a pure state

`F(|ψ>, |φ>) = |<ψ|φ>|²`

These equations form a compact mathematical map of the subject.

## Practical interpretation of the complete workflow

A typical state-vector calculation follows a sequence such as:

1. Choose a basis.
2. Represent the initial state as a vector of complex amplitudes.
3. Normalize the vector.
4. Apply valid operators.
5. Maintain numerical precision and dimensional consistency.
6. Express the resulting state in the desired basis.
7. Convert amplitudes to probabilities for a specified measurement.
8. Repeat measurements when estimating empirical frequencies.
9. Use inner products to study overlap and orthogonality.
10. Use tensor products to construct composite systems.
11. Test whether a pure composite state factors into subsystem states.
12. Use density matrices when the state description requires the mixed-state formalism.

The Python script follows this progression in a mathematically exploratory form. The JavaScript implementation emphasizes language-level construction of the same concepts. The C++ program organizes the concepts into a small, validated two-qubit case study.

## Key distinctions

| Concept | Meaning |
|---|---|
| Amplitude | Complex coefficient associated with a basis state |
| Probability | Squared magnitude of an amplitude for the corresponding basis measurement |
| Ket | Column-vector notation for a quantum state |
| Bra | Conjugate transpose of a ket |
| Inner product | Scalar overlap between two vectors |
| Outer product | Matrix formed from a ket and bra |
| Normalization | Requirement that total probability equals one |
| Global phase | Common phase factor with no physical effect on a pure state |
| Relative phase | Phase difference that can affect interference |
| Basis | Set of vectors used to express state coordinates |
| Unitary | Operator preserving inner products and normalization |
| Product state | Composite state factorizable into subsystem states |
| Entangled state | Composite state that cannot be factored into subsystem pure states |
| Pure state | State represented by one normalized ket |
| Mixed state | Statistical quantum state represented generally by a density matrix |
| Fidelity | Measure of overlap between quantum states |
| Expectation value | Statistical average associated with an observable |

## Implementation checklist

A correct basic state-vector implementation should verify that:

- the state dimension corresponds to a valid number of qubits
- the state is normalized
- probabilities are nonnegative up to numerical tolerance
- probabilities sum to one within tolerance
- complex conjugation is used in inner products
- operators have compatible dimensions
- unitary operators satisfy `U†U ≈ I`
- tensor-product ordering is documented
- measurement probabilities use squared amplitudes
- floating-point comparisons use appropriate tolerances
- invalid inputs are rejected rather than silently accepted

These checks are present in executable form throughout the three implementations.
