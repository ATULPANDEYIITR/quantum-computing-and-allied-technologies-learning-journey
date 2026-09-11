# Introduction to Quantum Mechanics: Core Principles and Terminology

## Topic introduction

Quantum mechanics is the framework used to describe physical systems at microscopic scales and, more generally, systems whose behavior cannot be explained adequately by classical mechanics.

The theory describes phenomena such as atomic spectra, electron behavior in solids, tunneling, spin, interference, entanglement, and the operation of many modern electronic and optical technologies.

The Python script accompanying this README develops the subject from basic terminology to important mathematical structures and selected applications. The numerical examples use Python's standard library and focus on transparent implementations of quantum concepts rather than on high-performance scientific computing.

## Fundamental terminology

### Quantum system

A quantum system is a physical system described according to the principles of quantum mechanics. Examples include an electron, an atom, a photon, a spin system, or an engineered two-level device.

### Quantum state

A quantum state contains the information required to calculate the probabilities of possible measurement outcomes.

For a pure state, the state is commonly represented by a normalized vector

`|ψ⟩`

in a Hilbert space.

More generally, a quantum state can be represented by a density operator or density matrix.

### Hilbert space

A Hilbert space is a complete vector space equipped with an inner product.

Quantum states are represented mathematically within Hilbert spaces. The dimension of the relevant Hilbert space depends on the number of independent quantum states required to describe the system.

A qubit, for example, has a two-dimensional Hilbert space.

### Ket

A ket is written as

`|ψ⟩`

and represents a quantum state vector.

For a two-level system,

`|ψ⟩ = α|0⟩ + β|1⟩`

where α and β are generally complex probability amplitudes.

### Bra

The corresponding bra is

`⟨ψ|`

and is obtained by taking the conjugate transpose of the ket.

The inner product of a state with itself is

`⟨ψ|ψ⟩ = 1`

for a normalized state.

### Probability amplitude

A probability amplitude is generally a complex number.

The amplitude itself is not a probability. According to the Born rule, a probability is obtained from the squared magnitude of an appropriate amplitude.

For an amplitude `c`,

`P = |c|²`.

### Observable

An observable is a physical quantity that can be measured, such as position, momentum, energy, or angular momentum.

In the standard formulation of quantum mechanics, observables are represented by Hermitian operators.

### Operator

An operator is a mathematical transformation acting on states or other mathematical objects.

An observable is represented by an operator whose eigenvalues correspond to possible measurement outcomes.

### Eigenvalue

If an operator satisfies

`A|a⟩ = a|a⟩`

then `a` is an eigenvalue and `|a⟩` is the corresponding eigenstate.

When the system is already in an eigenstate of an observable, measuring that observable produces the associated eigenvalue with certainty.

### Hamiltonian

The Hamiltonian, usually written as `H`, is the energy operator of the system.

It plays a central role in determining time evolution through the Schrodinger equation.

### Wavefunction

A wavefunction is a representation of a quantum state in a particular basis.

For a particle in one-dimensional position space, the wavefunction can be written as `ψ(x)`.

The quantity

`|ψ(x)|²`

is a probability density for position.

A probability over an interval is obtained by integrating the probability density over that interval.

## Quantization

One of the foundational ideas of quantum mechanics is that certain physical quantities can take discrete values under appropriate physical conditions.

Planck's relation connects photon energy and frequency:

`E = hf`

where:

- `E` is photon energy
- `h` is Planck's constant
- `f` is frequency

The script calculates photon energies and demonstrates how an energy difference corresponds to an electromagnetic transition frequency.

Quantization does not mean that every physical quantity is always discrete. The allowed values depend on the physical system and its boundary conditions.

## Planck's constant

Planck's constant is

`h = 6.62607015 × 10⁻³⁴ J·s`

The reduced Planck constant is

`ℏ = h / 2π`.

The reduced constant appears extensively in quantum-mechanical equations, including the Schrodinger equation and angular-momentum relations.

## Wave-particle duality

Quantum objects can display properties traditionally associated with both particles and waves.

The de Broglie relation assigns a wavelength to a particle with momentum `p`:

`λ = h/p`.

For an electron with sufficiently small momentum, the corresponding wavelength can become comparable with atomic or nanoscale dimensions, making wave effects experimentally significant.

Wave-particle duality should not be interpreted as saying that a microscopic object is simply a classical particle that periodically turns into a classical wave. Quantum objects require the quantum-mechanical formalism itself.

## Superposition

Superposition is a direct consequence of the linear structure of quantum states.

If `|0⟩` and `|1⟩` are allowed states, then a state of the form

`|ψ⟩ = α|0⟩ + β|1⟩`

is also an allowed state, subject to normalization:

`|α|² + |β|² = 1`.

Superposition is different from classical uncertainty.

A classical mixture of 50% `|0⟩` and 50% `|1⟩` and a coherent state

`(|0⟩ + |1⟩)/√2`

can produce the same probabilities in one measurement basis while producing different results in another basis.

The difference is the presence or absence of quantum coherence.

## Complex numbers and phase

Quantum amplitudes are generally complex.

A complex amplitude can be expressed in polar form as

`c = r exp(iθ)`.

The magnitude determines probability-related quantities, while the phase determines how amplitudes combine.

A global phase applied to an entire state does not change ordinary measurement probabilities:

`|ψ⟩ → exp(iφ)|ψ⟩`.

Relative phase between components can be physically important because it affects interference.

## Interference

Quantum amplitudes are added before probabilities are calculated.

For two indistinguishable alternatives with amplitudes `A₁` and `A₂`,

`A_total = A₁ + A₂`

and

`P = |A_total|²`.

Expanding the squared magnitude produces cross terms. These terms can be positive or negative depending on the relative phase.

Constructive interference increases the resulting probability, while destructive interference can suppress it.

This principle explains the characteristic behavior of experiments such as the double-slit experiment.

## Born rule

The Born rule connects the mathematical quantum state with experimentally observable probabilities.

For a state `|ψ⟩` and normalized measurement state `|a⟩`,

`P(a) = |⟨a|ψ⟩|²`.

For a measurement with projectors, the probability is determined by the corresponding projection of the state.

The Born rule is one of the central principles of quantum mechanics.

## Normalization

A valid pure quantum state must be normalized.

For a discrete state,

`Σ |cᵢ|² = 1`.

For a position-space wavefunction,

`∫ |ψ(x)|² dx = 1`.

Normalization expresses the fact that the total probability of all mutually exclusive outcomes must equal one.

The Python script explicitly normalizes state vectors and demonstrates numerical normalization of a Gaussian wave packet.

## Expectation values

The expectation value is the statistical average obtained from many identically prepared measurements.

For discrete outcomes,

`⟨A⟩ = Σ aᵢP(aᵢ)`.

For an observable operator `A` and a pure state,

`⟨A⟩ = ⟨ψ|A|ψ⟩`.

For a density matrix,

`⟨A⟩ = Tr(ρA)`.

An expectation value does not necessarily correspond to an outcome obtainable in a single measurement.

## Variance and standard deviation

The variance describes the spread of measurement outcomes around the expectation value.

For a random variable,

`Var(A) = ⟨A²⟩ - ⟨A⟩²`.

The standard deviation is

`ΔA = √Var(A)`.

Quantum uncertainty relations are expressed in terms of these statistical spreads.

## Operators and observables

Operators provide the mathematical representation of physical quantities and transformations.

For a state vector `|ψ⟩`, applying an operator `A` gives

`A|ψ⟩`.

For an observable, the operator's eigenvalues represent possible measurement outcomes.

The Python script implements matrix-vector multiplication and calculates operator expectation values directly.

## Hermitian operators

An operator `A` is Hermitian when

`A† = A`.

Hermitian operators have real eigenvalues under the usual finite-dimensional assumptions. This is important because physical measurement results must be real.

The Pauli matrices used to represent spin measurements are Hermitian.

## Eigenstates and eigenvalues

An eigenstate satisfies

`A|a⟩ = a|a⟩`.

If the system is in `|a⟩`, measurement of `A` produces `a` with certainty.

A general state can be expanded as a linear combination of eigenstates of an observable. The coefficients in that expansion determine the probabilities of the corresponding measurement outcomes.

## Position and momentum

In the position representation, the position operator acts through multiplication by position:

`x̂ = x`.

The momentum operator is represented by

`p̂ = -iℏ d/dx`.

These operators generally do not commute.

The non-commutativity is central to the position-momentum uncertainty relation.

## Commutator

The commutator of two operators is

`[A,B] = AB - BA`.

If

`[A,B] = 0`

the operators commute.

If the commutator is nonzero, the operators generally cannot be simultaneously diagonalized in a common eigenbasis.

The Pauli matrices provide a simple example:

`[σₓ,σᵧ] = 2iσ_z`.

Commutators are also useful for identifying conserved quantities and analyzing symmetries.

## Heisenberg uncertainty principle

The position-momentum uncertainty relation is

`Δx Δp ≥ ℏ/2`.

A more general Robertson relation is

`ΔA ΔB ≥ 1/2 |⟨[A,B]⟩|`.

This principle is not merely a statement about inaccurate instruments. It follows from the mathematical structure of quantum states and non-commuting observables.

The uncertainty principle constrains statistical spreads. It should not be interpreted as saying that every individual measurement is intrinsically inaccurate.

## Measurement disturbance versus uncertainty

Two related but distinct concepts should be separated.

Uncertainty describes the statistical spread of measurement outcomes in a state.

Measurement disturbance describes how a particular measurement procedure changes the state or influences subsequent measurements.

A careful analysis of disturbance requires specifying the measurement procedure rather than treating every measurement as an identical process.

## Schrodinger equation

The time-dependent Schrodinger equation is

`iℏ ∂|ψ⟩/∂t = H|ψ⟩`.

The Hamiltonian `H` determines the time evolution of a closed quantum system.

For an energy eigenstate,

`H|ψ⟩ = E|ψ⟩`.

Its time dependence includes a phase factor:

`|ψ(t)⟩ = exp(-iEt/ℏ)|ψ(0)⟩`.

The Schrodinger equation plays a role analogous to the equations of motion in classical mechanics, although the mathematical structure and interpretation are different.

## Unitary evolution

Closed-system quantum evolution is unitary.

A unitary operator `U` satisfies

`U†U = I`.

Unitary transformations preserve inner products and therefore preserve normalization and total probability.

The Python script demonstrates the Hadamard transformation and verifies its unitarity numerically.

## Measurement and state update

Quantum measurement is described using a measurement formalism.

For a projective measurement, the possible outcomes correspond to projection operators associated with an observable's eigenspaces.

After an outcome is obtained, the state is updated according to the measurement rule.

The exact mathematical description depends on whether the measurement is ideal projective measurement, a generalized measurement, or another physical measurement model.

## Measurement basis

A quantum state does not have one universal list of probabilities independent of what is measured.

For example, the state

`|+⟩ = (|0⟩ + |1⟩)/√2`

produces equal probabilities when measured in the computational basis, but it is an eigenstate of the corresponding X-basis observable and therefore produces a definite result in that basis.

This illustrates the importance of the measurement basis.

## Spin

Spin is intrinsic angular momentum.

It is not simply the literal rotation of a small classical sphere.

A spin-1/2 system has two-dimensional state space and is naturally represented using the Pauli matrices.

The conventional spin measurement outcomes along a chosen axis are

`+ℏ/2`

and

`-ℏ/2`.

## Pauli matrices

The Pauli matrices are

`σₓ = [[0,1],[1,0]]`

`σᵧ = [[0,-i],[i,0]]`

`σ_z = [[1,0],[0,-1]]`.

They are Hermitian and unitary.

They are fundamental in descriptions of spin-1/2 systems and quantum information.

## Dirac notation

Dirac notation provides a compact language for quantum mechanics.

A ket is written as `|ψ⟩`.

A bra is written as `⟨ψ|`.

An inner product is

`⟨φ|ψ⟩`.

An outer product is

`|ψ⟩⟨φ|`.

Outer products are used to construct projection operators and density matrices.

## Density matrices

A pure state can be represented by

`ρ = |ψ⟩⟨ψ|`.

Density matrices also describe statistical mixtures and subsystem states.

Important properties of a valid density matrix include:

- Hermiticity
- Positive semidefiniteness
- Unit trace

For a pure state,

`Tr(ρ²) = 1`.

For a mixed state,

`Tr(ρ²) < 1`.

The quantity `Tr(ρ²)` is commonly called purity.

## Pure state versus mixed state

A pure state represents maximal quantum-state knowledge within the theory.

A mixed state represents a statistical ensemble or an effective state of a subsystem.

The pure state

`(|0⟩ + |1⟩)/√2`

and the equal mixture of `|0⟩` and `|1⟩` both produce 50/50 computational-basis probabilities.

They are nevertheless different because the pure state contains coherent off-diagonal terms in its density matrix.

## Tensor products

Composite quantum systems are represented using tensor products.

If subsystem A has dimension `d₁` and subsystem B has dimension `d₂`, the combined system has dimension

`d₁d₂`.

For `n` qubits, the Hilbert-space dimension is

`2ⁿ`.

This exponential growth is one reason that direct classical simulation of large quantum systems can become computationally difficult.

## Entanglement

A composite state is entangled when it cannot be expressed as a tensor product of independent subsystem states.

A fundamental example is the Bell state

`|Φ⁺⟩ = (|00⟩ + |11⟩)/√2`.

Measuring one qubit in the computational basis determines the corresponding outcome of the other qubit for this particular state.

Entanglement produces correlations that cannot generally be explained by assigning independent classical states to the subsystems.

Entanglement does not permit controllable faster-than-light communication.

## Classical mixture versus quantum superposition

This distinction is central to understanding quantum mechanics.

A classical mixture can be represented by

`ρ = 1/2 |0⟩⟨0| + 1/2 |1⟩⟨1|`.

A coherent superposition is represented by

`|+⟩ = (|0⟩ + |1⟩)/√2`.

Their computational-basis populations are identical, but their off-diagonal density-matrix elements differ.

Those coherence terms can change the results of measurements performed in other bases.

## Decoherence

Decoherence is the loss or suppression of observable quantum coherence caused by interaction with uncontrolled environmental degrees of freedom.

Common consequences include:

- Dephasing
- Relaxation
- Loss of interference
- Emergence of classical-looking behavior

The script uses a simple phenomenological dephasing model in which diagonal populations remain unchanged while off-diagonal coherence is reduced.

Decoherence is not simply synonymous with the measurement postulate. It is a dynamical process associated with environmental interaction.

## Infinite square well

The infinite square well is a standard exactly solvable quantum model.

For a particle of mass `m` confined to a one-dimensional region of width `L`, the energy levels are

`E_n = n²π²ℏ² / (2mL²)`

where

`n = 1, 2, 3, ...`.

The energy therefore grows as `n²`.

The corresponding stationary wavefunctions are

`ψ_n(x) = √(2/L) sin(nπx/L)`.

Boundary conditions determine which wavefunctions are allowed.

This provides a clear example of how quantization can emerge mathematically.

## Quantum numbers

Atomic states are characterized by quantum numbers.

The principal quantum number `n` determines the main energy level in the simplest hydrogen model.

The orbital angular momentum quantum number `l` satisfies

`l = 0, 1, ..., n-1`.

The magnetic quantum number `m_l` satisfies

`m_l = -l, ..., 0, ..., +l`.

For spin-1/2 particles, spin projection is represented by

`m_s = ±1/2`.

Quantum numbers encode discrete properties of quantum states.

## Hydrogen energy levels

The non-relativistic hydrogen energy approximation is

`E_n = -13.6 eV / n²`.

The negative sign indicates that the bound states lie below the chosen zero-energy reference.

When an electron transitions between energy levels, the energy difference can be emitted or absorbed as a photon.

For a transition,

`ΔE = hf`.

Atomic spectra therefore provide experimental evidence for quantized energy levels.

The simple hydrogen formula does not include corrections such as fine structure, Lamb shifts, external-field effects, and other higher-order contributions.

## Angular momentum

Orbital angular momentum obeys

`L²|l,m⟩ = ℏ²l(l+1)|l,m⟩`

and

`L_z|l,m⟩ = ℏm|l,m⟩`.

The possible values of `m` for a particular `l` are

`-l, -l+1, ..., l-1, l`.

Angular momentum is therefore quantized.

Spin adds another form of intrinsic angular momentum.

## Atomic orbitals

An orbital is a quantum state or wavefunction, not a classical planetary orbit.

The squared magnitude of the wavefunction gives probability density.

For the hydrogen 1s state, the radial probability distribution can be expressed in a form proportional to

`r² exp(-2r/a₀)`.

This distribution describes how likely the electron is to be detected at different radial distances.

## Quantum tunneling

Quantum tunneling occurs when a quantum state has nonzero amplitude in a region that would be classically forbidden.

For a simple barrier, an approximate transmission probability can have an exponential dependence such as

`T ≈ exp(-2κa)`

where `a` is the barrier width and `κ` depends on particle mass and the difference between barrier energy and particle energy.

The exponential dependence makes tunneling highly sensitive to barrier width.

Applications include:

- Alpha decay
- Scanning tunneling microscopy
- Semiconductor devices
- Nuclear processes
- Quantum electronic systems

The formula implemented in the script is an approximation rather than a universal exact transmission formula.

## Quantum harmonic oscillator

The quantum harmonic oscillator has energy levels

`E_n = ℏω(n + 1/2)`.

The quantum number satisfies

`n = 0, 1, 2, ...`.

The lowest energy is

`E₀ = ℏω/2`.

This is the zero-point energy.

The quantum harmonic oscillator is important because many physical systems can be approximated as harmonic near a stable equilibrium point.

## Zero-point energy

Zero-point energy is the nonzero minimum energy of systems such as the quantum harmonic oscillator.

It is connected to the uncertainty principle. A state with exactly zero position uncertainty and exactly zero momentum uncertainty is incompatible with the quantum-mechanical structure of the oscillator.

## Bosons and fermions

Particles are classified according to their spin and statistical behavior.

Bosons have integer spin and obey Bose-Einstein statistics.

Fermions have half-integer spin and obey Fermi-Dirac statistics.

Examples include:

- Photon: boson
- Electron: fermion
- Proton: fermion
- Helium-4 atom: bosonic composite particle

The distinction has major consequences for many-particle systems.

## Pauli exclusion principle

Identical fermions cannot occupy the same complete quantum state.

For electrons in atoms, this restriction helps produce the structure of electron shells and the periodic table.

The Pauli exclusion principle also has broader consequences for the stability and properties of matter.

## Exchange symmetry

For identical particles, exchanging particle labels produces important symmetry requirements.

A two-particle symmetric state can have the form

`(|ab⟩ + |ba⟩)/√2`.

An antisymmetric state can have the form

`(|ab⟩ - |ba⟩)/√2`.

Bosonic states are symmetric under particle exchange, while fermionic states are antisymmetric.

## Time evolution

For an energy eigenstate,

`ψ(t) = exp(-iEt/ℏ)ψ(0)`.

The magnitude of the phase factor is one, so unitary evolution preserves normalization.

For a superposition of different energy eigenstates, different components accumulate different phases. Relative phases can therefore change with time and affect later measurements.

## Classical limit

Classical mechanics emerges as an effective approximation of quantum mechanics under appropriate conditions.

Important mechanisms include:

- Large quantum numbers
- Small de Broglie wavelengths relative to relevant length scales
- Decoherence
- Localization of wave packets
- Correspondence between quantum and classical dynamics

The de Broglie wavelength becomes extremely small for macroscopic objects at ordinary speeds, helping explain why their wave behavior is not normally visible.

## Wave-packet dispersion

A localized wave packet contains a range of momentum components.

For a non-relativistic free particle,

`E = p²/(2m)`.

Because energy depends nonlinearly on momentum, different momentum components acquire different time-dependent phases.

The wave packet can therefore spread over time.

This is one reason a localized quantum state should not generally be interpreted as a permanent classical point particle with a perfectly defined trajectory.

## Perturbation theory

Many quantum systems cannot be solved exactly.

Perturbation theory begins with a solvable Hamiltonian and treats an additional contribution as a relatively small correction.

For an unperturbed eigenstate `|n⟩`, the first-order energy correction is

`ΔE_n^(1) = ⟨n|V|n⟩`.

The approximation is useful when the perturbation is sufficiently small relative to the relevant energy scales.

It can fail or become poorly behaved when the perturbation is too large, when levels are degenerate, or when the assumptions behind the expansion are not satisfied.

## Variational principle

The variational principle is particularly useful for estimating ground-state energies.

For a normalized trial state,

`E_trial = ⟨ψ_trial|H|ψ_trial⟩`.

For a Hamiltonian bounded from below,

`E_trial ≥ E_ground`.

Therefore, improving the trial-state family can produce progressively better upper bounds on the ground-state energy.

This transforms part of a quantum-mechanical problem into an optimization problem.

## Generalized measurements and POVMs

Projective measurements are not the only measurement formalism.

A positive operator-valued measure, or POVM, consists of positive operators `E_i` satisfying

`ΣE_i = I`.

The corresponding probability is

`P(i) = Tr(ρE_i)`.

POVMs are useful for describing generalized measurement processes, imperfect detection, state discrimination, and quantum information protocols.

## Open quantum systems

The simplest closed-system evolution is

`ρ(t) = Uρ(0)U†`.

Real physical systems interact with environments.

A subsystem of a larger closed system can therefore undergo effective non-unitary evolution.

Important open-system phenomena include:

- Decoherence
- Dephasing
- Relaxation
- Thermalization
- Amplitude damping
- Environmental noise

Density matrices are particularly useful for describing these situations.

## Symmetry and conservation

Symmetry is closely connected with conservation laws.

Important examples include:

| Symmetry | Associated quantity |
| --- | --- |
| Time-translation symmetry | Energy |
| Spatial translation symmetry | Momentum |
| Rotational symmetry | Angular momentum |

For a time-independent observable `A`, a condition such as

`[H,A] = 0`

implies conservation of the corresponding observable under standard closed-system evolution, subject to the relevant assumptions.

## Energy-time relation

Energy-time uncertainty requires more careful interpretation than position-momentum uncertainty.

A commonly encountered scale is

`ΔE Δt ≈ ℏ/2`.

Time is not generally treated as an ordinary self-adjoint observable operator in standard non-relativistic quantum mechanics in the same way that position is.

Therefore, the energy-time relation should not simply be obtained by replacing position with time in the position-momentum uncertainty relation.

## No-cloning theorem

The no-cloning theorem states that there is no universal physical operation capable of perfectly copying an arbitrary unknown quantum state.

If a hypothetical operation attempted to satisfy

`U|ψ⟩|0⟩ = |ψ⟩|ψ⟩`

for every unknown `|ψ⟩`, linearity of quantum mechanics would produce contradictions for general non-orthogonal states.

This restriction is important in quantum information and quantum cryptography.

## Quantum teleportation

Quantum teleportation transfers an unknown quantum state from one location to another using:

1. A shared entangled state
2. A joint measurement
3. Classical communication
4. A conditional quantum operation

Teleportation does not transport physical matter instantaneously.

It also does not violate the no-cloning theorem because the original state is not independently preserved as an additional copy.

Classical communication is required, so the protocol does not enable controllable faster-than-light information transfer.

## Quantum Zeno effect

The quantum Zeno effect describes situations where sufficiently frequent measurements or measurement-like interactions can inhibit or modify quantum evolution.

The precise behavior depends on the physical system, measurement process, and time regime.

The script uses a simple approximation to illustrate the basic idea rather than claiming a universal formula.

## Entropy

For a density matrix with eigenvalues `λᵢ`, the von Neumann entropy is

`S = -Σ λᵢ log₂(λᵢ)`.

For a pure state,

`S = 0`.

For a maximally mixed state in dimension `d`,

`S = log₂(d)`.

Entropy is important in quantum information, statistical mechanics, thermodynamics, and the analysis of mixed quantum states.

## Quantum information terminology

A few central terms are:

**Qubit:** A two-dimensional quantum information system.

**Superposition:** A linear combination of allowed quantum states.

**Coherence:** The presence of definite phase relationships between components of a quantum state.

**Entanglement:** A non-separable relationship within a composite quantum state.

**Decoherence:** Suppression of quantum coherence through environmental interaction.

**Unitary transformation:** A reversible norm-preserving quantum transformation.

**Density matrix:** A mathematical representation that describes pure states, mixed states, and reduced subsystem states.

**POVM:** A generalized measurement formalism.

## Quantum mechanics versus classical mechanics

| Classical mechanics | Quantum mechanics |
| --- | --- |
| State often represented by position and momentum | State represented by a vector or density operator |
| Probabilities often describe ignorance | Probabilities are fundamental to measurement predictions |
| Physical quantities are generally represented by ordinary variables | Observables are represented by operators |
| Classical variables generally commute | Quantum operators may not commute |
| Continuous trajectories are central | Measurement outcomes and state evolution follow quantum rules |
| Waves and particles are distinct classical concepts | Quantum systems exhibit wave-like and particle-like behavior |
| Deterministic evolution of classical state variables | Unitary evolution of closed quantum states with probabilistic measurement |

This table is a conceptual comparison. Classical mechanics also has probabilistic formulations, and quantum mechanics can produce deterministic evolution of a quantum state between measurements.

## Important distinctions

### State versus observable

A state describes the physical condition of a system.

An observable describes a measurable physical quantity.

They play different mathematical roles.

### Amplitude versus probability

An amplitude can be complex and can interfere with other amplitudes.

A probability is real, non-negative, and obtained from the appropriate squared magnitude or density-matrix expression.

### Superposition versus mixture

A superposition contains coherent phase relationships.

A mixture represents statistical weighting of possible states.

The two can produce identical probabilities in one basis while differing in another.

### Uncertainty versus measurement error

Quantum uncertainty is a property of the statistical distribution associated with a state and observables.

Experimental error is associated with limitations of a particular measurement apparatus or procedure.

They should not be treated as synonymous.

### Entanglement versus classical correlation

Classical systems can be correlated.

Entanglement is a stronger quantum property involving the structure of the joint quantum state and the inability to express it as a simple product of subsystem states.

### Wavefunction versus probability density

The wavefunction itself is generally complex.

Its squared magnitude gives probability density in a specified representation.

## Common mistakes

### Treating the wavefunction as an ordinary physical wave

A quantum wavefunction is a mathematical representation of a quantum state. It should not automatically be interpreted as a classical wave carrying material substance.

### Treating amplitudes as probabilities

The amplitude `α` is not itself the probability. The relevant probability is `|α|²`.

### Thinking measurement only reveals a hidden classical value

Quantum measurement has its own mathematical structure and can alter the state.

### Treating uncertainty as poor instrumentation

The uncertainty principle follows from quantum structure and non-commuting observables.

### Assuming entanglement permits faster-than-light communication

Entanglement creates nonclassical correlations but does not provide a controllable faster-than-light signaling mechanism.

### Assuming every quantum quantity is discrete

Some observables have discrete spectra in particular systems, while others can have continuous spectra. Quantization depends on the physical system and boundary conditions.

### Confusing expectation value with guaranteed measurement result

An expectation value is an average over repeated measurements. It need not be one of the possible individual outcomes.

### Ignoring normalization

An unnormalized state cannot directly be interpreted as a properly normalized probability distribution.

### Ignoring approximation domains

A formula may be mathematically valid within a model but physically inappropriate outside the assumptions used to derive it.

## Edge cases and limitations

The examples in the script are intentionally simplified.

### Infinite square well

The infinite-well model assumes perfectly infinite barriers. Real physical barriers are finite.

### Gaussian wave packet

Numerical integration uses finite limits to approximate an infinite spatial domain. Floating-point calculations introduce small numerical errors.

### Tunneling

The exponential transmission formula demonstrated in the script is an approximation. Exact barrier transmission depends on the complete potential and boundary conditions.

### Hydrogen

The simple hydrogen energy formula neglects effects such as fine structure, reduced-mass corrections, Lamb shifts, spin interactions, and external fields.

### Qubit models

A qubit is an idealized two-level system. Real physical systems can contain many additional degrees of freedom and sources of noise.

### Numerical matrix calculations

Floating-point arithmetic can introduce rounding error, normalization drift, underflow, overflow, and loss of numerical precision.

## Performance considerations

The mathematical dimension of a quantum state grows rapidly for composite systems.

A single qubit requires a state vector with two complex amplitudes.

Two qubits require four.

Ten qubits require 1,024.

Twenty qubits require 1,048,576.

For `n` qubits, a direct state-vector representation requires `2ⁿ` complex amplitudes.

This exponential growth is a major computational consideration in classical simulation of quantum systems.

The small matrix implementations in the Python script are intended for education and transparency rather than large-scale simulation.

## Numerical implementation considerations

A numerical quantum program should carefully address:

- State normalization
- Floating-point precision
- Matrix dimensions
- Hermiticity
- Positive semidefiniteness of density matrices
- Unitary transformations
- Boundary conditions
- Numerical integration error
- Discretization error
- Underflow in exponentially small probabilities
- Stability of iterative algorithms

Physical validity and numerical validity are different questions. A calculation can be numerically successful while representing a physically inappropriate model.

## Validation and debugging

Several checks are particularly useful when implementing quantum calculations.

### Normalization

For a state vector,

`Σ|cᵢ|² = 1`.

If normalization changes unexpectedly during unitary evolution, the implementation should be investigated.

### Hermiticity

For an observable,

`A† = A`.

A numerical implementation can check whether the difference between a matrix and its conjugate transpose is within a chosen tolerance.

### Unitarity

For a unitary transformation,

`U†U = I`.

This verifies that the transformation preserves the quantum state's norm.

### Probability sum

All probabilities for a complete measurement must sum to one, within numerical tolerance.

### Dimensional consistency

Physical equations must have consistent units.

For example,

`E = hf`

has units

`(J·s)(1/s) = J`.

Dimensional analysis is a simple and effective debugging method.

## Security and computational integrity considerations

Quantum mechanics itself is a physical theory, so conventional software security concerns are not part of the physical postulates.

For computational implementations, normal software engineering considerations still apply.

Input validation prevents invalid parameters from producing misleading physical interpretations.

Numerical tolerances should be chosen carefully because exact equality is often inappropriate with floating-point values.

Scientific calculations should retain units or use clearly documented unit conventions to prevent dimensional mistakes.

Results from approximate numerical models should not be presented as exact physical predictions when the assumptions of the model do not justify that interpretation.

## Production considerations

The Python script is an educational implementation rather than a production-grade scientific simulation package.

A production quantum simulation system would generally require more sophisticated numerical methods, such as:

- Efficient sparse matrix representations
- High-performance linear algebra
- Stable eigensolvers
- Numerical integration libraries
- Differential-equation solvers
- Optimized tensor operations
- Memory-aware state representations
- Automated validation
- Reproducible numerical experiments
- Unit-aware physical quantities
- Carefully documented approximation assumptions

Large many-body quantum systems can require computational techniques substantially more advanced than direct dense matrix calculations.

## Real-world applications

Quantum mechanics is fundamental to many technologies and scientific fields, including:

- Transistors
- Semiconductor devices
- LEDs
- Lasers
- Solar cells
- Atomic clocks
- Spectroscopy
- Electron microscopy
- Scanning tunneling microscopy
- Nuclear magnetic resonance
- Magnetic resonance techniques
- Quantum sensors
- Superconducting technologies
- Nanotechnology
- Materials science
- Quantum communication
- Quantum information processing
- Nuclear physics
- Condensed-matter physics

The practical significance of quantum mechanics is therefore much broader than microscopic particle theory.

## Relationship with relativity

The ordinary Schrodinger equation is non-relativistic.

It is highly successful when velocities are much smaller than the speed of light and relativistic effects are not important.

At relativistic energies, quantum descriptions require relativistic equations such as the Dirac equation, and a complete treatment involving particle creation and annihilation is provided by quantum field theory.

Quantum mechanics and relativity therefore meet in more advanced theoretical frameworks.

## Quantum mechanics and quantum field theory

Non-relativistic quantum mechanics is appropriate for many atomic, molecular, condensed-matter, and low-energy problems.

Quantum field theory extends quantum principles to relativistic fields and naturally accommodates particle creation and annihilation.

The concepts introduced in the script remain important in quantum field theory, including:

- State spaces
- Operators
- Commutation relations
- Symmetries
- Measurement probabilities
- Unitary evolution
- Density matrices
- Entanglement

## Core mathematical relationships

The most important equations covered in the script include:

Planck relation:

`E = hf`

de Broglie relation:

`λ = h/p`

Born rule:

`P = |amplitude|²`

Normalization:

`Σ|cᵢ|² = 1`

Expectation value:

`⟨A⟩ = ⟨ψ|A|ψ⟩`

Density-matrix expectation value:

`⟨A⟩ = Tr(ρA)`

Commutator:

`[A,B] = AB - BA`

Position-momentum uncertainty:

`ΔxΔp ≥ ℏ/2`

General uncertainty relation:

`ΔAΔB ≥ 1/2 |⟨[A,B]⟩|`

Time-dependent Schrodinger equation:

`iℏ∂|ψ⟩/∂t = H|ψ⟩`

Energy eigenvalue equation:

`H|ψ⟩ = E|ψ⟩`

Infinite-well energy:

`E_n = n²π²ℏ²/(2mL²)`

Hydrogen energy approximation:

`E_n = -13.6 eV/n²`

Harmonic oscillator:

`E_n = ℏω(n + 1/2)`

Angular momentum:

`L²|l,m⟩ = ℏ²l(l+1)|l,m⟩`

Angular momentum projection:

`L_z|l,m⟩ = ℏm|l,m⟩`

Von Neumann entropy:

`S = -Tr(ρ log₂ρ)`

## Structure of the Python script

The script is organized progressively.

It begins with constants, normalization, probability amplitudes, and basic physical relationships.

It then introduces:

- Quantization
- Wave-particle duality
- Complex amplitudes
- Superposition
- Interference
- Wavefunctions
- Expectation values
- Operators
- Eigenstates
- Hermitian operators
- Position and momentum
- Commutators
- Uncertainty
- Schrodinger dynamics
- Measurement
- Spin
- Bra-ket notation
- Density matrices
- Tensor products
- Entanglement
- Quantum wells
- Quantum numbers
- Atomic energy levels
- Tunneling
- Harmonic oscillators
- Bosons and fermions
- Exchange symmetry
- Decoherence
- Unitary transformations
- Quantum gates
- No-cloning
- Teleportation
- Quantum Zeno behavior
- Classical limits
- Perturbation theory
- Variational methods
- POVMs
- Open quantum systems
- Symmetry and conservation
- Entropy
- Quantum information terminology
- Practical applications
- Numerical validation
- Common conceptual mistakes
- Model limitations

The final sections combine several concepts into small integrated simulations and state-vector calculations.

## Interpretation of the computational examples

The Python implementations are intentionally explicit.

Matrix multiplication is written directly so that the connection between linear algebra and quantum operators is visible.

State vectors are normalized explicitly.

Measurement is simulated using random sampling from Born-rule probabilities.

The density-matrix examples construct outer products directly.

Tensor products show how composite quantum systems increase in dimension.

The quantum-gate examples use small matrices to demonstrate unitary transformations.

The infinite-well and harmonic-oscillator examples implement standard analytical formulas.

The tunneling example explicitly identifies its transmission expression as an approximation.

These choices prioritize conceptual transparency and physical interpretation over numerical optimization.

## Physical interpretation of the complete framework

The central structure of introductory quantum mechanics can be viewed as a sequence of relationships.

A physical system is represented by a quantum state.

The state can be expressed in a chosen basis.

Observable quantities are represented by operators.

The state and the measurement operator determine probability distributions.

Complex amplitudes and relative phases determine interference behavior.

Closed systems evolve according to unitary dynamics generated by the Hamiltonian.

Composite systems are described through tensor products.

Tensor-product states can be entangled.

Interactions with environments can produce decoherence and mixed states.

This framework provides the conceptual foundation for atomic physics, molecular physics, condensed-matter physics, quantum optics, nuclear physics, and quantum information science.
