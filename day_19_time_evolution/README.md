# Time evolution and Schrödinger equation concepts

## Introduction

Time evolution is the central dynamical problem of non-relativistic quantum mechanics. A quantum state is represented by a wavefunction, and its evolution is governed by the time-dependent Schrödinger equation.

For a single particle moving in one spatial dimension,

    iħ ∂ψ(x,t)/∂t = Hψ(x,t)

where the Hamiltonian for a particle of mass `m` in a potential `V(x,t)` is

    H = -(ħ²/2m) ∂²/∂x² + V(x,t)

The Python, JavaScript, and C++ implementations in this repository treat the equation as both a mathematical object and a computational problem.

The implementations use dimensionless units in most demonstrations:

    ħ = 1
    m = 1

This removes unnecessary numerical scale factors while preserving the structure of the physical equations.

## Fundamental concepts

### Quantum state

A quantum state contains the information required to calculate the probabilities of possible measurement outcomes.

For a particle described in position space, the state is represented by the complex-valued wavefunction

    ψ(x,t)

The wavefunction itself is not directly interpreted as a probability density. The Born rule states that

    ρ(x,t) = |ψ(x,t)|²

is the probability density for position.

For a normalized state,

    ∫ |ψ(x,t)|² dx = 1

The probability of finding the particle in an interval `[a,b]` is

    P(a ≤ x ≤ b) = ∫aᵇ |ψ(x,t)|² dx

The Python, JavaScript, and C++ programs all calculate this quantity numerically.

### Complex wavefunctions

Quantum wavefunctions are generally complex.

A complex number can be written as

    z = a + ib

where `i² = -1`.

A complex phase can be represented as

    e^(iθ) = cos(θ) + i sin(θ)

The implementations explicitly represent complex amplitudes. Python provides native complex arithmetic, while JavaScript and C++ use explicit complex-number representations.

### Hamiltonian

The Hamiltonian operator represents the total energy of the system.

For one spatial dimension,

    H = T + V

with kinetic-energy operator

    T = -(ħ²/2m) ∂²/∂x²

and potential-energy operator

    V = V(x,t)

The Hamiltonian is fundamental because it determines the time evolution through

    iħ ∂ψ/∂t = Hψ

The numerical programs implement the Hamiltonian by applying a finite-difference approximation to the second spatial derivative and then adding the potential-energy contribution.

## Time-dependent Schrödinger equation

The time-dependent Schrödinger equation is

    iħ ∂ψ/∂t = Hψ

For a time-independent Hamiltonian, this can be rearranged as

    ∂ψ/∂t = -(i/ħ)Hψ

This form is directly useful for numerical integration.

The Python and C++ implementations calculate the right-hand side explicitly and pass it to a fourth-order Runge-Kutta integrator. The JavaScript implementation performs the same mathematical operation while representing complex numbers with JavaScript objects.

## Time-evolution operator

The formal solution for a time-independent Hamiltonian is

    ψ(t) = U(t,t₀)ψ(t₀)

where

    U(t,t₀) = exp[-iH(t-t₀)/ħ]

The time-evolution operator is unitary when the Hamiltonian is Hermitian. Consequently,

    U†U = I

and normalized states remain normalized under exact evolution.

The exponential of an operator is more complicated than the exponential of an ordinary number because the Hamiltonian is an operator acting on a state vector. Numerical algorithms approximate this evolution without explicitly constructing a dense matrix exponential in the basic implementations.

## Stationary states

A stationary state is an energy eigenstate satisfying

    Hφₙ = Eₙφₙ

For such a state,

    ψₙ(x,t) = φₙ(x)e^(-iEₙt/ħ)

The time-dependent factor is a phase. Its magnitude is one:

    |e^(-iEₙt/ħ)| = 1

Therefore,

    |ψₙ(x,t)|² = |φₙ(x)|²

does not change with time.

The programs demonstrate this behavior using the infinite square well.

## Infinite square well

For an infinite square well extending from `0` to `L`, the stationary eigenfunctions are

    φₙ(x) = sqrt(2/L) sin(nπx/L)

where

    n = 1,2,3,...

The corresponding energy eigenvalues are

    Eₙ = n²π²ħ²/(2mL²)

The implementations use these equations to construct exact reference states.

The infinite well illustrates several important ideas:

- energy quantization
- orthogonal eigenstates
- stationary probability densities
- global phase evolution
- superposition of different energy eigenstates

The numerical programs do not need a numerical eigensolver for this example because the analytic eigenfunctions and energies are known.

## Superposition

Quantum states obey linearity.

If `φ₁` and `φ₂` are valid solutions, then

    ψ = c₁φ₁ + c₂φ₂

is also a valid state when the coefficients satisfy the appropriate normalization condition.

For an orthonormal basis,

    Σ |cₙ|² = 1

The probability density becomes

    |ψ|² = |c₁φ₁ + c₂φ₂|²

which contains cross terms. These terms represent interference.

For a two-state superposition,

    |ψ|² =
    |c₁|²|φ₁|² +
    |c₂|²|φ₂|² +
    c₁* c₂ φ₁* φ₂ +
    c₂* c₁ φ₂* φ₁

The individual stationary states have fixed probability densities, but their relative phase changes with time when their energies differ. The resulting probability density can therefore become time dependent.

This distinction is demonstrated in all three implementations.

## Global phase versus relative phase

A global phase transformation has the form

    ψ → e^(iα)ψ

and leaves all ordinary measurement probabilities unchanged.

A relative phase between components of a superposition is physically relevant because it affects interference.

For example,

    ψ = c₁φ₁ + c₂φ₂

evolves into

    ψ(t) =
    c₁φ₁e^(-iE₁t/ħ) +
    c₂φ₂e^(-iE₂t/ħ)

The relative phase contains

    exp[-i(E₂-E₁)t/ħ]

This is why a superposition of different energies can have time-dependent observables even though each individual energy eigenstate is stationary.

## Observables and expectation values

An observable is represented by an operator.

For an observable `A`,

    <A> = ∫ ψ* A ψ dx

provided the state and operator satisfy the mathematical conditions required for the expectation value.

The position operator in one dimension is

    x̂ = x

so

    <x> = ∫ ψ* x ψ dx

The momentum operator is

    p̂ = -iħ ∂/∂x

giving

    <p> = ∫ ψ* (-iħ ∂ψ/∂x) dx

The Hamiltonian itself is the energy operator, so

    <H> = ∫ ψ* Hψ dx

The implementations calculate position, momentum, potential energy, and total energy numerically.

## Probability current

The probability density obeys a continuity equation.

For one dimension,

    ∂ρ/∂t + ∂j/∂x = 0

where

    ρ = |ψ|²

and, for the standard one-dimensional Schrödinger equation,

    j = (ħ/m) Im(ψ* ∂ψ/∂x)

The continuity equation expresses local probability conservation. Probability can move from one region to another, but under appropriate closed-system conditions it is not created or destroyed.

The implementations primarily verify global normalization rather than explicitly calculating the current at every grid point, but the finite-difference derivative used for momentum is the same type of spatial operation needed to construct the current.

## Uncertainty principle

Position and momentum do not generally have simultaneously arbitrary precision.

The standard uncertainty relation is

    Δx Δp ≥ ħ/2

where

    Δx = sqrt(<x²> - <x>²)

and

    Δp = sqrt(<p²> - <p>²)

The Python implementation calculates the position spread and estimates momentum variance numerically.

The underlying reason is operator non-commutativity:

    [x̂,p̂] = iħ

More generally, for two observables `A` and `B`,

    ΔA ΔB ≥ (1/2)|< [A,B] >|

under the usual assumptions.

## Ehrenfest theorem

For an observable with no explicit time dependence,

    d<A>/dt = (i/ħ)<[H,A]>

For position,

    d<x>/dt = <p>/m

For momentum in a potential,

    d<p>/dt = -<∂V/∂x>

These relations connect quantum expectation values with classical-looking equations of motion.

A localized wave packet can therefore exhibit approximately classical motion of its center under suitable conditions, even though the complete quantum state follows the Schrödinger equation.

## Gaussian wave packets

The implementations use Gaussian wave packets because they provide a convenient localized state.

A representative form is

    ψ(x,0) =
    A exp[-(x-x₀)²/(4σ²)] exp(ik₀x)

where:

- `x₀` is the initial center
- `σ` controls spatial width
- `k₀` is the central wave number
- `p₀ = ħk₀` is the corresponding central momentum
- `A` is a normalization constant

A Gaussian wave packet illustrates the distinction between a localized particle description and a momentum eigenstate.

A perfectly sharp momentum state is spatially delocalized, while a localized packet requires a range of momentum components.

## Spatial discretization

A computer cannot directly store a continuous function at every real value of `x`.

The numerical implementations replace continuous space with a finite grid:

    x₀, x₁, x₂, ..., xₙ₋₁

with approximately constant spacing

    Δx = xᵢ₊₁ - xᵢ

The wavefunction becomes a vector,

    ψ → [ψ₀, ψ₁, ..., ψₙ₋₁]

This turns differential equations into systems of ordinary differential equations.

The approximation introduces several sources of error:

- finite spatial resolution
- finite numerical domain
- boundary-condition approximation
- finite time-step size
- floating-point roundoff
- discretization of integrals

## Finite-difference approximation

The second derivative is approximated by

    ψ''(x) ≈
    [ψ(x+Δx) - 2ψ(x) + ψ(x-Δx)] / Δx²

This is the central second-order finite-difference formula.

The numerical Hamiltonian therefore becomes approximately

    Hψᵢ =
    -(ħ²/2m)
    [ψᵢ₊₁ - 2ψᵢ + ψᵢ₋₁]/Δx²
    + Vᵢψᵢ

The computational cost of applying this local one-dimensional Hamiltonian is `O(N)` for `N` grid points.

## Boundary conditions

Boundary conditions are part of the physical model.

For an infinite square well,

    ψ(0,t) = ψ(L,t) = 0

The implementations impose zero values at the numerical boundaries for their finite computational boxes.

This is appropriate for a hard-wall model but not automatically appropriate for a free particle in an infinite physical space.

A finite computational domain can introduce artificial reflections when a wave packet reaches the edge. A production simulation must therefore select boundary treatment according to the intended physics.

Possible approaches include:

- hard-wall boundaries
- periodic boundaries
- absorbing boundaries
- complex absorbing potentials
- sufficiently large domains
- specialized open-boundary methods

## Numerical time integration

After spatial discretization, the Schrödinger equation can be written schematically as

    dψ/dt = F(ψ,t)

The implementations use fourth-order Runge-Kutta integration.

For a state `ψₙ`,

    k₁ = F(ψₙ,tₙ)

    k₂ = F(ψₙ + Δt k₁/2,tₙ + Δt/2)

    k₃ = F(ψₙ + Δt k₂/2,tₙ + Δt/2)

    k₄ = F(ψₙ + Δt k₃,tₙ + Δt)

and

    ψₙ₊₁ =
    ψₙ + Δt(k₁ + 2k₂ + 2k₃ + k₄)/6

RK4 has fourth-order local integration accuracy under the usual smoothness assumptions, but accuracy order does not mean that it automatically preserves every physical property of quantum evolution.

In particular, standard explicit RK4 is not exactly unitary.

## Unitarity

Exact closed-system Schrödinger evolution generated by a Hermitian Hamiltonian is unitary.

Consequently,

    <ψ(t)|ψ(t)> = <ψ(0)|ψ(0)>

A numerical algorithm may not preserve this identity exactly.

The Python, JavaScript, and C++ examples explicitly monitor normalization and, in selected educational simulations, renormalize the state after each time step.

Renormalization can prevent probability drift from becoming large, but it does not transform a non-unitary numerical method into an exactly unitary propagator.

This distinction is important in serious numerical quantum mechanics.

## Split-operator method

The Python implementation also contains an FFT-based split-operator propagator.

Write the Hamiltonian as

    H = T + V

where

    T = p²/(2m)

and

    V = V(x)

The exact propagator is

    exp[-i(T+V)Δt/ħ]

Since kinetic and potential operators generally do not commute,

    [T,V] ≠ 0

their exponentials cannot simply be multiplied as an exact identity.

A second-order symmetric splitting is

    U(Δt) ≈
    exp[-iVΔt/(2ħ)]
    exp[-iTΔt/ħ]
    exp[-iVΔt/(2ħ)]

The potential operator is diagonal in position space.

The kinetic-energy operator is diagonal in momentum space.

This motivates the sequence:

    position space
    → Fourier transform
    → momentum space
    → kinetic phase
    → inverse Fourier transform
    → position-space potential phase

The split-operator method is particularly useful for wave-packet propagation because FFT algorithms can perform transforms in approximately `O(N log N)` operations rather than the `O(N²)` cost of a direct discrete Fourier transform.

The Python implementation contains both a direct DFT and a recursive radix-2 FFT to expose this computational distinction.

## Fourier representation

A wavefunction can be represented in position space or momentum space.

The direct discrete Fourier transform used in the implementations follows the structure

    Xₖ = Σₙ xₙ exp(-2πikn/N)

The inverse transform is

    xₙ = (1/N)Σₖ Xₖ exp(2πikn/N)

The DFT is mathematically useful but computationally expensive for large `N`.

Its direct complexity is

    O(N²)

An FFT exploits structure in the transform to achieve approximately

    O(N log N)

The JavaScript implementation uses a direct DFT for clarity, while the Python implementation also includes a recursive FFT because the split-operator method benefits from efficient Fourier transforms.

## Tunneling

The potential-barrier example uses a finite barrier:

    V(x) = V₀

inside a specified interval and

    V(x) = 0

outside it.

Classically, a particle with energy `E < V₀` cannot cross the barrier.

Quantum mechanically, the wavefunction can have nonzero amplitude in the classically forbidden region and beyond the barrier.

This phenomenon is quantum tunneling.

The barrier simulation tracks probability on the left, inside the barrier, and on the right.

A numerical simulation does not replace the analytical theory of tunneling, but it provides a direct representation of how a wavefunction evolves under a spatially varying Hamiltonian.

## Harmonic oscillator

The harmonic oscillator potential is

    V(x) = (1/2)mω²x²

The corresponding Hamiltonian is

    H =
    -(ħ²/2m)∂²/∂x²
    + (1/2)mω²x²

The exact energy spectrum is

    Eₙ = ħω(n + 1/2)

The implementations use the harmonic potential for numerical energy calculations and wave-packet propagation.

The harmonic oscillator is important because it provides a system with exact analytical solutions, well-defined energy quantization, and strong connections between quantum and classical dynamics.

## Measurement simulation

The programs include a simple position-measurement sampler.

The sampling distribution is proportional to

    |ψ(x)|²

A random number is compared with cumulative discrete probability weights.

One measurement produces one position value. Repeating the process produces a distribution that approaches the underlying probability density.

The simulation therefore distinguishes between:

- the quantum state
- the probability distribution
- an individual measurement outcome
- the statistics of repeated measurements

The random generators in the Python and C++ implementations use fixed seeds for reproducibility.

## Python implementation

The Python program is organized as a computational laboratory.

It demonstrates:

- wavefunction normalization
- Gaussian state construction
- probability density
- position expectation values
- momentum expectation values
- finite-difference derivatives
- potential functions
- Hamiltonian application
- energy expectation values
- the Schrödinger-equation right-hand side
- RK4 propagation
- stationary-state evolution
- superposition
- uncertainty
- harmonic-oscillator energy
- barrier propagation
- direct DFT
- recursive FFT
- split-operator evolution
- measurement sampling
- validation and numerical edge cases

The implementation uses only the Python standard library.

This is deliberate. The finite-difference formulas, complex arithmetic, integration rules, DFT, and FFT are visible instead of being hidden behind a scientific-computing package.

For high-performance research calculations, specialized numerical libraries would normally be preferable.

## JavaScript implementation

The JavaScript program emphasizes application-oriented numerical computation.

JavaScript does not have a built-in primitive scalar complex-number type, so the program represents a complex number with an object containing:

- `re`
- `im`

Operations such as multiplication, conjugation, magnitude, and complex exponentiation are implemented explicitly.

The JavaScript implementation demonstrates:

- grid creation
- complex arithmetic
- Gaussian wave packets
- probability density
- finite differences
- Hamiltonian application
- observables
- RK4 evolution
- stationary states
- superposition
- potential barriers
- DFT and inverse DFT
- asynchronous evolution
- progress reporting
- validation
- runtime error handling

The asynchronous evolution function is particularly relevant to browser-based scientific interfaces. A long numerical calculation can otherwise block the event loop and make an interactive page unresponsive.

For larger simulations, a browser implementation could move computation into a Web Worker, use typed arrays, use WebAssembly, or connect to optimized numerical libraries.

## C++ case study

The C++ implementation models a one-dimensional quantum wave-packet laboratory.

The simulated system begins with a Gaussian packet:

    ψ(x,0) =
    A exp[-(x-x₀)²/(4σ²)]
    exp(ik₀x)

The case study then performs free-particle propagation, reinitializes the state for a finite potential barrier, performs barrier propagation, samples measurement outcomes, and compares numerical evolution with an analytically known infinite-well stationary state.

### Main components

The program defines:

- `Complex` as `std::complex<double>`
- `Wavefunction` as `std::vector<Complex>`
- a numerical position grid
- normalization functions
- Gaussian state construction
- potential functions
- first and second derivatives
- the Hamiltonian
- expectation-value functions
- Schrödinger-equation evaluation
- RK4 integration
- boundary handling
- measurement sampling
- infinite-well reference states
- a `QuantumWavePacketLab` class
- validation tests

### System model

The main case-study object stores:

- spatial coordinates
- grid spacing
- the current wavefunction

Its methods control different stages of the numerical experiment.

The architecture separates numerical primitives from the higher-level simulation class. This makes the code easier to inspect and makes individual mathematical operations independently testable.

### Algorithms

The major algorithms are:

- trapezoidal numerical integration
- second-order finite differences
- fourth-order Runge-Kutta integration
- cumulative-probability sampling
- analytical infinite-well state construction

For a grid containing `N` points, the finite-difference Hamiltonian application is `O(N)` because each point depends only on a small local neighborhood.

One RK4 step requires four Hamiltonian evaluations, giving `O(N)` spatial work per time step for the implemented one-dimensional local Hamiltonian.

For `S` time steps, the basic propagation therefore scales approximately as

    O(SN)

The constant factors depend on the number of Hamiltonian operations and diagnostics.

## Important distinctions

### Wavefunction versus probability density

`ψ` is a complex amplitude.

`|ψ|²` is the position probability density.

They are not interchangeable.

### Energy eigenstate versus arbitrary state

An energy eigenstate satisfies

    Hφ = Eφ

and has stationary probability density when the Hamiltonian is time independent.

A general state can be a superposition of energy eigenstates and may have time-dependent observables.

### Global phase versus relative phase

A global phase does not change standard measurement probabilities.

Relative phases in a superposition affect interference and can change measurable quantities.

### Exact evolution versus numerical evolution

The exact equation may preserve normalization and other structural properties exactly.

A numerical approximation can introduce:

- truncation error
- discretization error
- floating-point error
- boundary artifacts
- time-integration error

### Continuous space versus computational grid

The physical model may use continuous coordinates.

The program uses a finite set of grid points.

The grid is therefore an approximation of the physical domain.

### Classical probability versus quantum probability

The quantum probability density is derived from a complex amplitude:

    ρ = |ψ|²

The phase of `ψ` therefore matters to interference even though it disappears from the probability density of an isolated state.

## Edge cases

### Zero wavefunction

A zero wavefunction cannot be normalized because

    ∫|ψ|²dx = 0

The implementations explicitly reject this condition.

### Insufficient grid points

Finite-difference second derivatives require neighboring points.

The programs reject grids that are too small.

### Invalid Gaussian width

A Gaussian width must be positive. A zero or negative width does not represent the intended normalizable Gaussian packet.

### Incompatible vector sizes

The numerical operators require the spatial grid and wavefunction to contain the same number of elements.

The C++ implementation explicitly validates this relationship.

### Inadequate spatial resolution

A rapidly oscillating wavefunction requires sufficiently small `Δx`.

If the grid is too coarse, important phase variation can be lost.

### Large time steps

A time step that is too large can produce substantial integration error or instability.

The appropriate limit depends on the numerical method, grid spacing, Hamiltonian, and desired accuracy.

### Boundary reflections

A wave packet reaching a hard numerical boundary can reflect even when the intended physical system represents open space.

The finite computational domain must therefore be selected deliberately.

### Non-unitary numerical propagation

Standard RK4 is not exactly unitary.

The examples monitor normalization and use explicit renormalization in selected simulations.

This reduces normalization drift but should not be treated as a mathematically exact replacement for a unitary integrator.

## Common mistakes

### Treating `ψ` as probability

Incorrect:

    P(x) = ψ(x)

Correct:

    ρ(x) = |ψ(x)|²

### Forgetting normalization

A numerical state should satisfy

    ∫|ψ|²dx ≈ 1

before probabilities are interpreted.

### Confusing energy with angular frequency

For a stationary state,

    phase frequency = E/ħ

The phase is

    exp(-iEt/ħ)

not simply `exp(-iEt)` unless units have explicitly set `ħ = 1`.

### Ignoring boundary conditions

The boundary behavior is part of the physical problem.

A numerical box is not automatically equivalent to infinite physical space.

### Using a coarse grid

A grid that cannot resolve the wavefunction's shortest relevant wavelength can produce severe numerical errors.

### Using a large time step

Even a high-order integrator can fail to provide useful results when the time step is inappropriate for the spatial discretization and energy scales.

### Assuming numerical normalization proves accuracy

A state can be renormalized while other quantities remain inaccurate.

Normalization is an important diagnostic, but it is not a complete accuracy test.

### Ignoring operator ordering

Operators do not generally commute.

For example,

    [x̂,p̂] ≠ 0

and for position-dependent potentials,

    [T,V] ≠ 0

This matters when deriving propagator approximations.

## Numerical accuracy

Several convergence studies are useful for validating a simulation.

### Spatial convergence

Run the same physical problem with increasingly fine spatial grids:

    N
    2N
    4N

Then compare observables and wavefunctions.

For a second-order finite-difference derivative, the spatial discretization error is expected to decrease approximately with the square of the grid spacing under suitable smoothness and boundary assumptions.

### Temporal convergence

Repeat the calculation with smaller time steps:

    Δt
    Δt/2
    Δt/4

The results should converge toward a stable numerical solution.

### Conservation diagnostics

Useful quantities include:

- total probability
- energy for time-independent Hamiltonians
- symmetry properties
- expected stationary-state behavior
- expectation-value evolution
- agreement with analytical solutions

No single diagnostic is sufficient for all simulations.

## Performance considerations

### Python

The educational Python implementation uses ordinary Python lists and explicit loops. This makes the numerical methods readable but is not optimal for large simulations.

The direct DFT has `O(N²)` complexity.

The recursive FFT has approximately `O(N log N)` complexity for suitable power-of-two grid sizes.

Production Python implementations generally use optimized numerical arrays and compiled numerical kernels.

### JavaScript

JavaScript arrays are convenient but can have more overhead than typed numerical arrays.

For computationally intensive browser applications, `Float64Array` or related typed arrays can provide more predictable memory representation.

A complex state can also be stored as interleaved real and imaginary components to improve memory locality.

Web Workers can move computation away from the browser's main UI thread.

WebAssembly can provide access to high-performance compiled numerical kernels.

### C++

The C++ implementation uses `std::vector` and `std::complex<double>`.

These provide contiguous dynamic storage and standard complex arithmetic.

The main one-dimensional finite-difference operation has `O(N)` complexity.

The implementation is therefore substantially more scalable than a direct dense matrix representation of the Hamiltonian for this local one-dimensional problem.

A dense `N × N` Hamiltonian would require `O(N²)` storage, while the local finite-difference operator can be represented implicitly using a small neighborhood.

## Matrix representation

After discretization, the Hamiltonian can be viewed as a matrix acting on a vector.

For the kinetic term, the central finite difference creates a tridiagonal structure:

    Hᵢᵢ₋₁
    Hᵢᵢ
    Hᵢᵢ₊₁

The diagonal also contains the potential term.

This structure is important because sparse methods can exploit it.

The programs apply the Hamiltonian directly rather than constructing a dense matrix. This reduces memory usage and exposes the underlying finite-difference operation.

## Time-dependent potentials

The basic Hamiltonian can be generalized to

    H(t) = T + V(x,t)

In this case, the Hamiltonian at different times may not commute with itself:

    [H(t₁),H(t₂)] ≠ 0

The simple expression

    U(t,t₀) = exp[-iH(t-t₀)/ħ]

is then generally insufficient.

The formal solution requires time ordering, commonly written conceptually as a time-ordered exponential.

Numerical algorithms must account for the changing Hamiltonian.

The basic educational propagators focus primarily on time-independent potentials, where the structure is easier to expose.

## Time-dependent observables

For an explicitly time-dependent observable `A(t)`,

    d<A>/dt =
    (i/ħ)<[H,A]>
    + <∂A/∂t>

This separates changes caused by quantum dynamics from explicit time dependence of the operator itself.

The relation is useful for deriving conservation laws.

If an observable has no explicit time dependence and commutes with the Hamiltonian,

    [H,A] = 0

then its expectation value is conserved under the usual closed-system assumptions.

## Energy conservation

For a time-independent Hamiltonian,

    d<H>/dt = 0

under exact Schrödinger evolution.

A numerical simulation can show small changes in computed energy because of discretization and time-integration errors.

A significant energy drift can indicate:

- insufficient temporal resolution
- insufficient spatial resolution
- unsuitable boundary conditions
- a numerical instability
- accumulated floating-point error
- an inappropriate propagation method

## Production implementation considerations

A production quantum-dynamics solver needs more than a correct equation.

Important design questions include:

- Which boundary conditions are physical?
- Is the Hamiltonian time dependent?
- Is the potential smooth or discontinuous?
- Is the system closed or open?
- How large is the spatial domain?
- What wavelengths must be resolved?
- How many dimensions are required?
- Is the Hamiltonian sparse?
- Is exact or approximate unitarity important?
- Which observables must be conserved?
- How will numerical convergence be tested?
- How will long-time error accumulation be controlled?

For multidimensional systems, computational cost and memory requirements increase rapidly.

For many-body quantum systems, the difficulty is substantially greater because the dimension of Hilbert space can grow exponentially with the number of constituent two-level degrees of freedom.

## Security and reliability considerations

Scientific numerical software has reliability concerns even when it does not handle conventional security-sensitive information.

Important safeguards include:

- validate numerical parameters
- reject zero-norm states
- reject incompatible array dimensions
- check for non-finite numerical values
- monitor probability normalization
- test analytical reference cases
- use deterministic seeds when reproducibility is required
- record physical units and numerical conventions
- avoid silently changing boundary conditions
- document numerical approximations

When numerical results influence engineering, scientific, or financial decisions, reproducibility and validation are essential.

## Implementation comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Complex arithmetic | Native complex numbers | Explicit object representation | `std::complex<double>` |
| Main numerical representation | Python lists | JavaScript arrays | `std::vector` |
| Primary propagation | RK4 and split operator | RK4 | RK4 |
| Fourier demonstration | DFT and recursive FFT | DFT | Not required for the case study |
| Interactive suitability | Moderate | High for browser applications | Application dependent |
| Low-level control | Moderate | Lower | High |
| Educational visibility | High | High | High |
| Raw numerical performance | Limited without optimized libraries | Moderate with optimization | High potential |
| Memory control | Higher-level | Higher-level | Fine-grained |
| Error handling | Exceptions | Exceptions and rejected promises | Exceptions |

The three implementations use the same physical principles but expose different computational mechanisms.

Python makes mathematical experimentation concise.

JavaScript demonstrates how quantum calculations can become part of an interactive application.

C++ exposes memory layout, explicit data structures, deterministic execution, and performance-oriented numerical design.

## Practical applications

Time-dependent Schrödinger-equation methods appear in many areas of quantum science and engineering, including:

- molecular dynamics in quantum models
- quantum chemistry
- atomic and molecular physics
- semiconductor modeling
- quantum transport
- nanoscale systems
- ultrafast laser physics
- quantum control
- wave-packet scattering
- tunneling analysis
- quantum optics models
- quantum-information simulations
- condensed-matter models
- computational materials science

The appropriate numerical method depends strongly on the physical system and computational scale.

## Mathematical reference

### Schrödinger equation

    iħ ∂ψ/∂t = Hψ

### One-dimensional Hamiltonian

    H =
    -(ħ²/2m)∂²/∂x² + V(x,t)

### Probability density

    ρ = |ψ|²

### Normalization

    ∫|ψ|²dx = 1

### Expectation value

    <A> = ∫ψ* A ψ dx

### Position operator

    x̂ = x

### Momentum operator

    p̂ = -iħ∂/∂x

### Energy operator

    Ĥ = H

### Time-independent propagator

    U(t,t₀) =
    exp[-iH(t-t₀)/ħ]

### Energy eigenvalue equation

    Hφₙ = Eₙφₙ

### Stationary-state evolution

    ψₙ(x,t) =
    φₙ(x)e^(-iEₙt/ħ)

### Infinite-well energy

    Eₙ =
    n²π²ħ²/(2mL²)

### Uncertainty relation

    ΔxΔp ≥ ħ/2

### Continuity equation

    ∂ρ/∂t + ∂j/∂x = 0

### Probability current

    j =
    (ħ/m)Im(ψ*∂ψ/∂x)

### Ehrenfest relation

    d<x>/dt = <p>/m

### General observable evolution

    d<A>/dt =
    (i/ħ)<[H,A]> +
    <∂A/∂t>

## Files

The three executable implementations correspond directly to the concepts documented here:

- Python: numerical laboratory covering analytical states, finite differences, RK4, Fourier methods, split-operator propagation, uncertainty, tunneling, and measurement sampling.
- JavaScript: executable numerical implementation with explicit complex arithmetic and asynchronous evolution suitable for application or browser-oriented work.
- C++: structured one-dimensional wave-packet case study with validation, numerical propagation, observables, barrier dynamics, measurement sampling, and analytical stationary-state comparison.
