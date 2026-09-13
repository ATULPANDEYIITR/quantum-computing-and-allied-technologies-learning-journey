# Superposition, quantum states and amplitudes

## Introduction

Quantum superposition is one of the fundamental principles used to describe quantum systems. A quantum state can be represented as a linear combination of basis states, with complex coefficients called probability amplitudes.

For a single qubit, the computational basis consists of the states `|0>` and `|1>`. A general pure qubit state can be written as

`|ψ> = α|0> + β|1>`

where `α` and `β` are complex amplitudes satisfying the normalization condition

`|α|² + |β|² = 1`.

The Python script develops this subject from complex numbers and basic state vectors through measurement, interference, quantum gates, multi-qubit systems, entanglement, density matrices, decoherence, quantum circuits, and numerical simulation.

The implementation uses only Python's standard library so that the mathematical ideas remain visible in the source code.

## Quantum states

A quantum state is a mathematical representation of the physical state of a quantum system.

For a two-level system, the computational basis is

`|0> = [1, 0]`

and

`|1> = [0, 1]`.

A general pure qubit state is therefore

`|ψ> = α|0> + β|1>`.

The coefficients `α` and `β` are not ordinary probabilities. They are probability amplitudes.

The script represents a qubit using the `QubitState` class. Its two attributes correspond to the amplitudes of `|0>` and `|1>`.

The class provides methods for normalization, probability calculation, phase analysis, and removal of global phase.

## Complex probability amplitudes

Quantum amplitudes are generally complex numbers. A complex number has the form

`z = x + iy`

where `i` is the imaginary unit.

For an amplitude `z`, its magnitude is

`|z|`

and its squared magnitude is

`|z|²`.

The squared magnitude is the quantity used by the Born rule to obtain a measurement probability.

For example, if an amplitude is

`0.6`

then its associated probability is

`0.6² = 0.36`.

For a complex amplitude such as

`0.3 + 0.4i`

the probability contribution is

`|0.3 + 0.4i|² = 0.3² + 0.4² = 0.25`.

The distinction between amplitude and probability is fundamental. Treating an amplitude directly as a probability is a conceptual and implementation error.

## Superposition

Superposition is the representation of a quantum state as a linear combination of basis states.

The most familiar qubit superposition is

`|+> = (|0> + |1>)/√2`.

The amplitudes are both `1/√2`, so the computational-basis probabilities are

`P(0) = 1/2`

and

`P(1) = 1/2`.

Another important state is

`|-> = (|0> - |1>)/√2`.

Its computational-basis probabilities are also one-half each.

The difference between these two states is their relative phase. Although their immediate computational-basis probability distributions are identical, they respond differently to later quantum operations.

This demonstrates why a quantum state contains more information than a list of measurement probabilities.

## Normalization

A physical pure state must have unit norm.

For

`|ψ> = α|0> + β|1>`

the normalization requirement is

`|α|² + |β|² = 1`.

For a general state

`|ψ> = Σ cᵢ|i>`

the requirement becomes

`Σ |cᵢ|² = 1`.

The script includes general normalization functions and demonstrates how an arbitrary nonzero vector can be converted into a normalized state.

The zero vector cannot be normalized because division by its norm would require division by zero. It therefore cannot represent a physical pure state.

## Bra-ket notation

Dirac notation represents quantum states using kets such as

`|ψ>`.

The corresponding conjugate transpose is a bra:

`<ψ|`.

The inner product of two states is

`<φ|ψ>`.

For vectors, the bra requires complex conjugation. If

`|ψ> = [a, b]`

then

`<ψ| = [a*, b*]`.

The normalization condition can therefore be written as

`<ψ|ψ> = 1`.

The Python function `inner_product()` explicitly performs the complex conjugation required for the bra.

## Basis states and representations

A state is represented relative to a basis.

The computational basis for one qubit is

`{|0>, |1>}`.

The Hadamard basis is

`{|+>, |->}`

where

`|+> = (|0> + |1>)/√2`

and

`|-> = (|0> - |1>)/√2`.

The same physical state can have different amplitudes when expressed in different bases.

For example, `|0>` is a definite computational-basis state, but in the Hadamard basis it is

`|0> = (|+> + |->)/√2`.

This means that whether a state is described as a superposition depends on the basis used for the description.

The physical state itself has not changed merely because its mathematical representation has been changed.

## The Born rule

The Born rule connects quantum amplitudes to experimentally observable probabilities.

If

`|ψ> = Σ cᵢ|i>`

is normalized and measured in the corresponding basis, the probability of obtaining outcome `i` is

`P(i) = |cᵢ|²`.

The script implements this rule through `measurement_probabilities()`.

The probabilities are always nonnegative because squared magnitudes cannot be negative. For a normalized state, they sum to one.

## Measurement

Quantum measurement differs fundamentally from simply inspecting the complete state vector.

A state may contain amplitudes for many possible basis outcomes, but one measurement produces one classical outcome.

For example,

`|+> = (|0> + |1>)/√2`

produces either `0` or `1` in a computational-basis measurement, with equal probability.

Repeating the same preparation and measurement many times produces frequencies that approach the theoretical probabilities.

The script uses Python's pseudorandom generator to simulate repeated measurements. This is a classical numerical simulation of the probability distribution rather than a physical quantum measurement.

## Measurement and state update

For an ideal computational-basis measurement of a qubit, the projectors are

`P₀ = |0><0|`

and

`P₁ = |1><1|`.

If the result is `0`, the post-measurement state is `|0>`.

If the result is `1`, the post-measurement state is `|1>`.

This state-update process is commonly described as collapse of the wavefunction.

The script's `measure_qubit()` function demonstrates this behavior.

The distinction between unitary evolution and measurement is important. Unitary operations are reversible, whereas a measurement generally discards information about the original coherent state.

## Global phase

A global phase multiplies an entire state by the same complex phase factor.

If

`|ψ'> = e^(iθ)|ψ>`

then `|ψ'>` and `|ψ>` have identical measurement predictions.

The global phase changes the mathematical representation but does not change ordinary physical measurement probabilities.

The script demonstrates this by applying a complex phase factor to every amplitude and comparing the resulting probabilities and fidelity.

## Relative phase

Relative phase is the phase difference between components of a superposition.

Consider

`|+> = (|0> + |1>)/√2`

and

`|-> = (|0> - |1>)/√2`.

The minus sign corresponds to a relative phase of π between the two components.

Unlike global phase, relative phase can affect observable behavior after subsequent quantum operations.

This is one of the central reasons probability amplitudes must be represented as complex quantities.

## Interference

Quantum interference occurs because amplitudes add before probabilities are calculated.

If two coherent alternatives contribute amplitudes `a` and `b`, the total amplitude is

`a + b`.

The corresponding probability is

`|a + b|²`.

Expanding the expression gives

`|a|² + |b|² + 2 Re(a*b)`

where the final term is the interference contribution.

The interference term can be positive or negative.

Constructive interference increases an outcome's probability. Destructive interference decreases it.

For equal amplitudes with opposite signs,

`1/√2 + (-1/√2) = 0`.

The resulting probability is therefore zero.

This behavior has no direct classical analogue in ordinary probability addition.

## Amplitude addition versus probability addition

A major conceptual distinction is between coherent and incoherent alternatives.

For coherent alternatives, amplitudes are combined first:

`P = |a + b|²`.

For independent classical alternatives, probabilities are added according to the relevant classical probability model.

The difference arises because coherent quantum amplitudes retain relative phase information.

When which-path information or environmental interactions destroy coherence, interference can be suppressed.

## The Hadamard gate

The Hadamard gate is one of the most important operations for demonstrating superposition.

Its matrix is

`H = (1/√2) [[1, 1], [1, -1]]`.

Its key transformations are

`H|0> = |+>`

and

`H|1> = |->`.

It also satisfies

`H|+> = |0>`

and

`H|-> = |1>`.

The Hadamard gate is unitary, so it preserves normalization and is reversible.

It also provides a clear demonstration of interference. A superposition can be transformed back into a definite computational-basis state when the relative phases are arranged appropriately.

## Pauli gates and phase gates

The script implements the Pauli matrices

`X = [[0, 1], [1, 0]]`

`Y = [[0, -i], [i, 0]]`

`Z = [[1, 0], [0, -1]]`.

The `X` gate exchanges `|0>` and `|1>`.

The `Z` gate leaves `|0>` unchanged while multiplying `|1>` by `-1`.

Therefore, when `Z` acts on `|+>`, it produces `|->`.

The script also includes the `S` and `T` phase gates, which introduce more general relative phases.

## Unitary evolution

An isolated quantum system evolves through unitary transformations.

A matrix `U` is unitary when

`U†U = I`.

Here `U†` is the conjugate transpose.

Unitary transformations preserve vector norms and therefore preserve total probability.

The script implements matrix multiplication, conjugate transpose, identity matrices, and numerical unitarity checking.

This is important when building or validating quantum gates. A matrix that is intended to represent an ideal closed-system quantum operation must satisfy the unitary condition.

## Linearity

Quantum evolution is linear.

If `U` is an operation and

`|ψ> = a|0> + b|1>`

then

`U|ψ> = aU|0> + bU|1>`.

This principle means that understanding a linear operation on basis states determines its action on arbitrary superpositions.

The script explicitly calculates both sides of this relationship and demonstrates that they agree numerically.

Linearity is the mathematical mechanism through which quantum gates operate naturally on superpositions.

## Bloch-sphere representation

Every pure single-qubit state can be represented geometrically on the Bloch sphere, ignoring global phase.

A common parameterization is

`|ψ> = cos(θ/2)|0> + e^(iφ)sin(θ/2)|1>`.

The corresponding Bloch vector is

`x = sin(θ)cos(φ)`

`y = sin(θ)sin(φ)`

`z = cos(θ)`.

For a pure state, the Bloch vector has unit length.

The script instead calculates the coordinates directly from the amplitudes:

`x = 2 Re(α*β)`

`y = 2 Im(α*β)`

`z = |α|² - |β|²`.

The Bloch sphere provides an intuitive geometric interpretation of single-qubit superposition and phase.

## Observables and expectation values

A measurable physical quantity is represented mathematically by an observable, normally a Hermitian operator.

For a pure state, the expectation value is

`<A> = <ψ|A|ψ>`.

The script calculates expectation values for the Pauli operators.

For a single qubit, the expectation values of `X`, `Y`, and `Z` correspond to the three components of the Bloch vector.

The variance of an observable is

`Var(A) = <A²> - <A>²`.

Variance describes the spread of measurement outcomes around the expectation value.

## Multi-qubit state spaces

A single qubit has a two-dimensional state space.

Two qubits have a four-dimensional state space:

`|00>`

`|01>`

`|10>`

`|11>`.

Three qubits have eight computational-basis states.

In general, `n` qubits require

`2^n`

complex amplitudes for a general dense state-vector representation.

This exponential growth is one of the most important computational characteristics of quantum systems.

The script uses tensor products to construct multi-qubit states.

## Tensor products

The tensor product combines the state spaces of independent quantum systems.

If

`|a> = Σ aᵢ|i>`

and

`|b> = Σ bⱼ|j>`

then their joint state is

`|a> ⊗ |b>`.

For two qubits, the tensor product produces four amplitudes.

For example,

`|+> ⊗ |1>`

is a product state containing amplitudes for `|01>` and `|11>`.

The order of basis states must be documented carefully in software because different implementations can use different qubit-ordering conventions.

## Product states

A multi-qubit state is a product state if it can be factored into subsystem states.

For two systems,

`|ψ> = |a> ⊗ |b>`.

Product states do not contain entanglement between the two subsystems.

The script includes a separability test for pure two-qubit states. For

`a|00> + b|01> + c|10> + d|11>`

the state is separable when

`ad - bc = 0`

within numerical tolerance.

This condition is specific to pure two-qubit states.

## Entanglement

Entanglement occurs when a composite quantum state cannot be written as a product of independent subsystem states.

A standard example is the Bell state

`|Φ+> = (|00> + |11>)/√2`.

The Bell state is itself a superposition. Superposition and entanglement should therefore not be treated as synonyms.

Superposition can occur in one qubit.

Entanglement requires a composite system and concerns the inability to factor its joint state into separate subsystem states.

## Controlled-NOT and entanglement creation

The controlled-NOT, or CNOT, gate flips a target qubit when the control qubit is `|1>`.

Its computational-basis action is

`|00> → |00>`

`|01> → |01>`

`|10> → |11>`

`|11> → |10>`.

Starting with

`|+>|0>`

gives

`(|00> + |10>)/√2`.

Applying CNOT produces

`(|00> + |11>)/√2`.

The resulting state is a Bell state and is entangled.

The script implements this sequence both through matrices and through a small state-vector simulator.

## Density matrices

A pure state can be represented by a density matrix

`ρ = |ψ><ψ|`.

Density matrices are more general than state vectors because they can represent both pure states and mixed states.

They are particularly useful for:

- statistical mixtures
- subsystems of entangled systems
- noise
- decoherence
- generalized measurements
- quantum information calculations

The script implements outer products and density matrices using ordinary Python lists.

## Pure and mixed states

A pure state has the form

`ρ = |ψ><ψ|`.

Its purity is

`Tr(ρ²) = 1`.

A mixed state can be written as

`ρ = Σ pᵢ |ψᵢ><ψᵢ|`

where

`pᵢ ≥ 0`

and

`Σ pᵢ = 1`.

For a genuinely mixed state,

`Tr(ρ²) < 1`.

The script compares the pure state `|+>` with the maximally mixed single-qubit state

`ρ = [[1/2, 0], [0, 1/2]]`.

Although these two states have identical computational-basis measurement probabilities, they are physically different because the pure state contains coherence.

## Coherence

For

`|+> = (|0> + |1>)/√2`

the density matrix is

`ρ = [[1/2, 1/2], [1/2, 1/2]]`.

The off-diagonal elements contain coherence information.

The maximally mixed state is

`ρ = [[1/2, 0], [0, 1/2]]`.

The absence of off-diagonal coherence means the relative phase information required for the corresponding interference behavior is absent.

This distinction is essential when comparing superposition with classical statistical mixtures.

## Decoherence

Decoherence describes the loss of quantum coherence through interaction with an environment or other degrees of freedom.

The script includes a simple phase-damping model in which off-diagonal density-matrix elements are multiplied by a coherence factor between zero and one.

A factor of one leaves the state unchanged.

A factor of zero removes the modeled off-diagonal coherence.

This is a pedagogical noise model rather than a complete physical description of every decoherence process.

## Reduced states and partial trace

For a composite system, a subsystem can be described by a reduced density matrix.

If the total density matrix is `ρ_AB`, tracing out subsystem B produces

`ρ_A = Tr_B(ρ_AB)`.

The script implements the partial trace for a two-qubit density matrix.

For a Bell state, the total two-qubit system is pure, but the reduced state of either individual qubit is maximally mixed:

`ρ_A = I/2`.

This is a central property of entanglement.

The purity of the complete system is one, while the purity of an individual subsystem is one-half.

## Generalized measurements and POVMs

Projective measurements are not the only possible quantum measurements.

A generalized measurement can be represented by POVM elements `Eᵢ` satisfying

`Eᵢ ≥ 0`

and

`Σ Eᵢ = I`.

For a density matrix `ρ`, the probability of outcome `i` is

`P(i) = Tr(Eᵢρ)`.

POVMs provide a general framework for describing measurements that are not restricted to orthogonal projectors.

The script demonstrates the probability calculation for a simple two-outcome qubit POVM.

## Measurement in different bases

Measurement probabilities depend on the chosen measurement basis.

For `|+>` in the computational basis,

`P(0) = 1/2`

and

`P(1) = 1/2`.

In the Hadamard basis,

`P(+) = 1`

and

`P(-) = 0`.

This is an important illustration of the basis dependence of state representations and measurement statistics.

It also demonstrates how interference can convert phase information into observable probability differences.

## State fidelity

For pure states, fidelity is

`F(|ψ>, |φ>) = |<ψ|φ>|²`.

A fidelity of one means the states are physically identical up to global phase.

A fidelity of zero means the states are orthogonal.

The script calculates fidelities between computational-basis states, Hadamard-basis states, and globally phase-shifted states.

## Quantum state tomography

Quantum state tomography is the reconstruction of a quantum state from repeated measurement data.

For a single qubit, expectation values of `X`, `Y`, and `Z` determine the Bloch vector.

A single-qubit density matrix can be written as

`ρ = 1/2(I + xX + yY + zZ)`.

The script constructs a density matrix from Bloch-vector coordinates.

Tomography requires multiple measurements because one measurement produces only one classical outcome.

## Quantum circuit simulation

The script contains a small state-vector simulator.

The simulator stores a vector containing the amplitude for every computational-basis state.

For a two-qubit system, the state vector has four entries.

For a three-qubit system, it has eight entries.

The simulator demonstrates:

- initialization
- single-qubit gates
- Hadamard superposition
- CNOT
- probability calculation
- measurement
- state collapse
- Bell-state creation

The implementation is deliberately simple so that the relationship between a quantum circuit and its amplitude vector is visible.

## Shot-based simulation

Quantum algorithms are normally interpreted through repeated measurements.

A circuit may be executed many times, commonly described as taking multiple shots.

The measured frequencies approach the theoretical probabilities as the number of shots increases.

The Bell-state example demonstrates that repeated measurements of the state

`(|00> + |11>)/√2`

produce only `00` and `11` in the computational basis, ideally with approximately equal frequency.

The script uses a pseudorandom number generator to reproduce this statistical behavior.

## Superposition and quantum algorithms

Superposition is an important component of quantum algorithms, but superposition alone does not provide direct access to every amplitude.

A general state can be written as

`|ψ> = Σₓ αₓ|x>`.

Measurement produces one classical outcome.

Quantum algorithms therefore need to transform the amplitudes so that useful outcomes receive larger probabilities and unwanted outcomes receive smaller probabilities.

This is where interference becomes computationally important.

Quantum algorithms can use unitary operations to manipulate amplitudes, phases, and correlations before measurement.

## Amplitude amplification

The script includes a small numerical illustration of amplitude amplification.

The principle is that quantum transformations can redistribute amplitude so that a selected outcome has increased probability.

This is a central idea behind amplitude-amplification techniques.

The example is intentionally not a complete implementation of a search algorithm. It illustrates only the amplitude-level principle.

## Phase as computational information

Relative phase may not be directly visible in a computational-basis measurement.

For example, different states can have identical computational-basis probabilities while having different relative phases.

A suitable unitary transformation can convert this phase information into different measurement probabilities.

The script demonstrates this by applying a Hadamard operation to a phase-encoded qubit.

This general pattern can be described as

`encode phase → interfere → measure`.

Phase-sensitive interference is fundamental to several quantum algorithms.

## Quantum Fourier transform

The quantum Fourier transform changes the amplitude representation using complex phase factors.

For a dimension `N` system,

`QFT|x> = 1/√N Σᵧ exp(2πixy/N)|y>`.

The script includes a direct implementation of the QFT.

The direct implementation is computationally expensive because it performs a double loop over the vector.

For a vector of length `N`, this implementation requires approximately `O(N²)` operations.

Fast Fourier transform techniques can exploit additional mathematical structure to obtain approximately `O(N log N)` classical complexity for the corresponding transform.

The QFT is important because phase relationships and periodic structure can be manipulated through interference.

## State-vector scaling

An `n`-qubit state has

`2ⁿ`

computational-basis amplitudes.

The number of amplitudes grows exponentially.

For example:

- 10 qubits require 1,024 amplitudes.
- 20 qubits require 1,048,576 amplitudes.
- 30 qubits require 1,073,741,824 amplitudes.
- 40 qubits require 1,099,511,627,776 amplitudes.

If each complex amplitude occupies 16 bytes, raw state-vector storage grows rapidly.

This is one of the primary limitations of generic classical state-vector simulation.

The exponential dimension does not mean that every useful quantum state must always be stored as a dense vector. Special state structures can sometimes provide much more compact representations.

## Sparse state representations

Some states contain many zero or negligible amplitudes.

A sparse representation can store only the relevant basis indices and amplitudes.

The script demonstrates a dictionary-based sparse state representation.

Sparse representations can provide large memory savings when a state is genuinely sparse.

The limitation is that quantum operations can rapidly spread amplitude across many basis states, causing the representation to become dense.

Therefore sparse storage is highly dependent on the state and circuit structure.

## Numerical precision

Quantum simulation relies heavily on floating-point arithmetic.

Theoretically, a normalized state has exactly unit norm. Numerically, calculations may produce values such as

`0.9999999999999998`.

For this reason, scientific code should generally use numerical tolerances instead of exact floating-point comparisons.

The script uses `math.isclose()` and explicit absolute tolerances for normalization and matrix validation.

The appropriate tolerance depends on the numerical representation, circuit depth, algorithm, and required accuracy.

## State validation

A valid normalized state must have a nonzero norm and satisfy

`Σ |αᵢ|² = 1`

within the selected numerical tolerance.

The script validates:

- nonempty state vectors
- finite amplitudes
- nonzero norm
- normalization
- probability normalization

These checks are important because invalid state vectors can otherwise produce misleading simulation results.

## Density-matrix validation

A physical density matrix must satisfy several mathematical conditions.

It must be Hermitian:

`ρ = ρ†`.

Its trace must equal one:

`Tr(ρ) = 1`.

It must also be positive semidefinite, meaning that its expectation value is nonnegative for every possible state.

The script explicitly checks Hermiticity and unit trace.

Checking positive semidefiniteness generally requires an eigenvalue calculation or another mathematically equivalent procedure.

## Orthogonality

Two states are orthogonal when

`<φ|ψ> = 0`.

Orthogonal states can be perfectly distinguished by an appropriate measurement.

Examples include

`<0|1> = 0`

and

`<+|-> = 0`.

Orthogonality is important for basis construction, measurement theory, quantum coding, and state discrimination.

## Reversibility

Unitary quantum evolution is reversible.

For a unitary matrix,

`U⁻¹ = U†`.

Therefore applying `U†` after `U` returns the original state:

`U†U|ψ> = |ψ>`.

Measurement is fundamentally different because the post-measurement state does not generally retain enough information to reconstruct the complete pre-measurement superposition.

## Measurement destroys accessible coherence

Before measurement, a state can contain coherent relative-phase information.

After an ideal computational-basis measurement, the state is projected onto the observed basis state.

For example, measuring `|+>` can produce `|0>` or `|1>`.

Once the measurement has occurred, the original coherent superposition is not simply available for another measurement as though nothing happened.

This is why quantum algorithms must carefully arrange their unitary operations before the final measurement stage.

## Common misconceptions

### Superposition is just classical uncertainty

A classical random variable with two possible outcomes is not automatically equivalent to a quantum superposition.

The quantum state contains complex amplitudes and therefore phase information that can produce interference.

### Amplitudes are probabilities

They are not.

The probability is obtained from the squared magnitude of an amplitude.

### Every superposition is entangled

It is not.

A single qubit can be in a superposition without involving entanglement.

### Global phase is physically observable in ordinary measurement probabilities

A global phase does not change ordinary measurement predictions.

Relative phase can matter.

### A quantum computer can read every amplitude simultaneously

A quantum state may contain many amplitudes, but measurement returns a classical outcome according to the resulting probability distribution.

### Superposition alone produces quantum advantage

Superposition is one ingredient. Useful quantum computation also depends on carefully designed transformations, interference, entanglement in relevant algorithms, and measurement.

## Common implementation mistakes

A quantum-state program can produce incorrect results even when the Python code runs without errors.

Common mistakes include:

- treating amplitudes as probabilities
- forgetting normalization
- forgetting complex conjugation in inner products
- using ordinary vector multiplication instead of tensor products
- constructing non-unitary matrices when unitary evolution is intended
- comparing floating-point values using exact equality
- using inconsistent basis ordering
- using inconsistent qubit-index conventions
- accidentally modifying state data in place
- assuming computational-basis probabilities reveal relative phase
- ignoring numerical normalization drift
- failing to validate dimensions

These errors can produce plausible-looking but mathematically incorrect results.

## Basis-ordering considerations

Multi-qubit software must clearly define the ordering of basis states.

The script uses the ordering

`|00>, |01>, |10>, |11>`

for two qubits.

For larger systems, implementations must also document which qubit corresponds to the most significant or least significant bit.

Different conventions can represent the same mathematical circuit using different array indices.

This is an implementation detail that becomes especially important when comparing simulators, circuit descriptions, measurement results, and hardware interfaces.

## Performance considerations

A dense state-vector simulator requires

`O(2ⁿ)`

memory for `n` qubits.

A general dense operator acting on the full system has `2ⁿ × 2ⁿ` entries, resulting in

`O(4ⁿ)`

storage.

For this reason, practical simulators generally avoid constructing a complete dense matrix for every local gate.

Instead, they apply local transformations directly to the relevant amplitudes.

The educational simulator in the script uses this idea for single-qubit operations.

The QFT example is intentionally implemented directly with nested loops. This makes the mathematical definition clear but is not computationally optimal.

## Specialized simulation techniques

Dense state-vector simulation is general but expensive.

Certain families of quantum states and circuits can be represented more efficiently.

Examples include:

- stabilizer representations
- tensor networks
- decision diagrams
- structured sparse representations
- low-rank approximations

These techniques do not eliminate the exponential nature of the general quantum state space. They exploit special structure in particular states or circuit families.

The choice of representation is therefore an important algorithm and software-design decision.

## Memory and precision trade-offs

Complex floating-point values require memory for both real and imaginary components.

Higher precision can improve numerical accuracy but requires more memory and computational work.

Lower precision can reduce resource requirements but may accumulate larger numerical errors.

The appropriate precision depends on:

- circuit depth
- algorithm sensitivity
- hardware
- required accuracy
- numerical conditioning
- error tolerance

Scientific software should make these assumptions explicit.

## Security and correctness considerations

The main risks in a small quantum-state simulator are usually mathematical and numerical rather than conventional application-security problems.

Important correctness controls include:

- validating state dimensions
- validating normalization
- checking operator dimensions
- checking unitarity
- checking probability distributions
- using controlled numerical tolerances
- documenting basis conventions
- controlling random seeds during testing
- avoiding unintended state mutation

The script uses deterministic random seeds in several demonstrations so that measurement experiments can be reproduced.

A pseudorandom generator used for simulation should not automatically be treated as a source of cryptographically secure randomness.

## Production implementation considerations

A production quantum simulation environment may require:

- optimized memory layout
- vectorized numerical operations
- parallel processing
- GPU acceleration
- distributed state-vector simulation
- optimized sparse structures
- specialized tensor-network algorithms
- noise models
- high-performance linear algebra
- robust numerical testing
- reproducible experiment configuration
- explicit qubit-order conventions
- scalable measurement infrastructure

The simple Python implementation in the script is intended to expose the mathematics clearly rather than maximize computational performance.

## Practical applications

Quantum superposition and probability amplitudes are relevant to many areas of quantum information science, including:

- quantum computing
- quantum algorithms
- quantum simulation
- quantum communication
- quantum measurement theory
- quantum state tomography
- quantum error correction
- quantum sensing
- quantum cryptographic protocols
- quantum information theory

The computational significance of superposition comes from the ability to manipulate complex amplitudes and their relative phases before measurement.

## Core mathematical relationships

The central formulas implemented in the script are:

`|ψ> = α|0> + β|1>`

`|α|² + |β|² = 1`

`P(i) = |αᵢ|²`

`<φ|ψ> = Σᵢ φᵢ*ψᵢ`

`<A> = <ψ|A|ψ>`

`Var(A) = <A²> - <A>²`

`ρ = |ψ><ψ|`

`P(i) = Tr(Eᵢρ)`

`x = 2 Re(α*β)`

`y = 2 Im(α*β)`

`z = |α|² - |β|²`

`dim(H_A ⊗ H_B) = dim(H_A)dim(H_B)`

`dim(n qubits) = 2ⁿ`

These relationships connect the mathematical representation of quantum states to observable probabilities, interference, measurement, and computation.

## Terminology

| Term | Meaning |
|---|---|
| Quantum state | Mathematical description of a quantum system |
| Amplitude | Complex coefficient associated with a basis state |
| Probability amplitude | Complex coefficient whose squared magnitude determines probability |
| Superposition | Linear combination of basis states |
| Basis | Complete orthonormal set used to represent states |
| Normalization | Requirement that total probability equals one |
| Born rule | Rule connecting squared amplitude magnitudes to measurement probabilities |
| Global phase | Common phase factor applied to an entire state |
| Relative phase | Phase difference between components of a state |
| Interference | Combination of amplitudes that changes resulting probabilities |
| Unitary | Norm-preserving reversible linear transformation |
| Measurement | Operation producing an outcome according to quantum probabilities |
| Density matrix | Operator representation of pure and mixed quantum states |
| Coherence | Phase-sensitive structure represented by off-diagonal density-matrix elements |
| Entanglement | Non-separable structure in a composite quantum state |
| Tensor product | Operation combining subsystem state spaces |
| Observable | Hermitian operator associated with a measurable quantity |
| POVM | Generalized measurement represented by positive operators |
| Bloch sphere | Geometric representation of a pure single-qubit state up to global phase |
| Fidelity | Measure of similarity between quantum states |

## Scope of the implementation

The Python script is a mathematical and computational study of quantum superposition and amplitudes. It includes complete implementations for:

- complex amplitude calculations
- qubit states
- normalization
- Born-rule probabilities
- measurement sampling
- state collapse
- inner products
- basis changes
- global and relative phase
- interference
- quantum gates
- unitary validation
- Bloch vectors
- expectation values
- tensor products
- multi-qubit state vectors
- product-state testing
- Bell states
- CNOT
- density matrices
- mixed states
- partial trace
- decoherence modeling
- POVM probability calculations
- fidelity
- state tomography
- QFT
- state-vector simulation
- circuit measurement
- numerical validation
- performance estimation
- reproducibility testing

The implementation emphasizes the direct connection between mathematical definitions and executable numerical operations.
