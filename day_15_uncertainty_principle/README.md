# Quantum uncertainty and the Heisenberg uncertainty principle

## Topic introduction

Quantum uncertainty is a fundamental feature of quantum mechanics. It describes statistical restrictions on the possible outcomes of measurements performed on a quantum state.

The most familiar form is the position-momentum uncertainty relation:

`Δx Δp ≥ ħ/2`

where `Δx` is the standard deviation of position, `Δp` is the standard deviation of momentum, and `ħ` is the reduced Planck constant.

The relation does not simply state that laboratory instruments are imperfect. It follows from the mathematical structure of quantum mechanics, particularly the noncommutation of position and momentum operators:

`[x̂, p̂] = iħ`

This project approaches quantum uncertainty computationally using Python, JavaScript, and C++. The three implementations use different techniques. Python emphasizes mathematical exploration and numerical experiments, JavaScript emphasizes executable numerical demonstrations and explicit complex-number handling, and C++ develops an industry-style numerical case study around a discretized quantum wave packet.

## Fundamental concepts

### Quantum state

A quantum state contains the information required to calculate probabilities for measurements. For a one-dimensional particle, a common representation is a wavefunction `ψ(x)`.

The wavefunction itself is generally complex-valued. It is not directly interpreted as a probability density.

According to the Born rule,

`P(x) = |ψ(x)|²`

gives the position probability density.

The probability of finding a particle in an interval is obtained by integrating the probability density over that interval.

### Probability amplitude

The wavefunction is a probability amplitude. Its complex phase can affect interference even though the probability density depends on its absolute square.

For a complex number

`z = a + ib`

the magnitude squared is

`|z|² = a² + b²`.

This is why complex arithmetic is central to quantum-mechanical calculations.

### Expectation value

For an observable represented by operator `Â`, the expectation value is

`⟨A⟩ = ⟨ψ|Â|ψ⟩`.

In position representation, this becomes an integral involving the wavefunction, its complex conjugate, and the operator.

The expectation value is not necessarily the result of a single measurement. It represents the average obtained from many identically prepared systems.

### Variance and standard deviation

The variance of an observable is

`(ΔA)² = ⟨A²⟩ - ⟨A⟩²`.

The standard deviation is

`ΔA = sqrt(⟨A²⟩ - ⟨A⟩²)`.

Quantum uncertainty is normally expressed through this standard deviation.

A state can therefore have a well-defined expectation value while still producing a distribution of individual measurement outcomes.

## Core principle

For position and momentum,

`Δx Δp ≥ ħ/2`.

This means the product of their standard deviations cannot be made arbitrarily small.

If a quantum state is strongly localized in position, it must contain a sufficiently broad range of momentum components. If its momentum is sharply defined, the corresponding position distribution must be spatially extended.

The relation is a property of the quantum state. It is not necessary to interpret it as an inability of an observer to know two pre-existing classical values simultaneously.

## Why position and momentum behave differently from classical variables

Classical mechanics allows a particle to be described by an exact position and exact momentum at a particular instant.

Quantum mechanics represents physical quantities using operators acting on states.

The position operator in position representation is simply multiplication by `x`:

`x̂ ψ(x) = x ψ(x)`.

The momentum operator is

`p̂ = -iħ d/dx`.

Applying the two operators in opposite orders produces different results. Their commutator is

`[x̂,p̂] = x̂p̂ - p̂x̂ = iħ`.

This nonzero commutator is the mathematical basis of the position-momentum uncertainty relation.

## Robertson uncertainty relation

The position-momentum relation is one instance of a more general result.

For two observables `A` and `B`,

`ΔA ΔB ≥ |⟨[Â,B̂]⟩|/2`.

This is the Robertson uncertainty relation.

The important idea is that uncertainty depends on the algebraic relationship between observables.

If two observables commute, the commutator does not impose the same nonzero lower bound. If their operators do not commute, simultaneous arbitrarily sharp values generally cannot be obtained in a common quantum state.

## Schrödinger uncertainty relation

A stronger relation includes covariance between the observables. In schematic form,

`ΔA² ΔB² ≥ |⟨[Â,B̂]⟩|²/4 + covariance term²`.

The covariance term captures correlations that are not represented by the basic Robertson expression.

This distinction becomes important for correlated Gaussian states and squeezed states.

## Gaussian minimum-uncertainty wave packets

A Gaussian wave packet provides a particularly important example.

A position-space Gaussian can be written in proportional form as

`ψ(x) ∝ exp[-(x-x₀)²/(4σₓ²)] exp(ip₀x/ħ)`.

Here:

- `x₀` is the mean position.
- `σₓ` is the position standard deviation.
- `p₀` is the mean momentum.
- The second exponential supplies the spatial phase associated with momentum.

For an ideal Gaussian packet,

`Δp = ħ/(2Δx)`.

Therefore,

`Δx Δp = ħ/2`.

Such a state saturates the Heisenberg lower bound and is called a minimum-uncertainty state.

The implementations use Gaussian packets repeatedly because they provide an analytical result against which numerical calculations can be tested.

## Fourier-transform interpretation

There is another important way to understand quantum uncertainty.

Position and momentum representations are related by a Fourier transform.

The spatial wavefunction can be expressed as a superposition of wave numbers. Momentum is related to wave number by

`p = ħk`.

A narrow function in position space requires a broad collection of Fourier components. A broad position-space function can have a narrower Fourier spectrum.

This mathematical property of Fourier transforms is closely connected to the position-momentum uncertainty relation.

The Python and JavaScript implementations include direct discrete Fourier transforms to demonstrate this relationship computationally.

A direct discrete Fourier transform has approximately `O(N²)` computational complexity. Fast Fourier transform algorithms reduce the scaling to approximately `O(N log N)` and are therefore much more suitable for large numerical simulations.

## Python implementation

The Python script develops the subject from basic probability through numerical quantum mechanics.

It first implements ordinary statistical concepts such as mean, variance, and standard deviation. This establishes the statistical meaning of uncertainty before quantum operators are introduced.

The script then constructs complex Gaussian wavefunctions and uses the Born rule to calculate probability densities.

The Gaussian packet is represented by the `GaussianPacket` class. Its analytical momentum uncertainty is calculated from

`Δp = ħ/(2Δx)`.

This provides an exact reference for the numerical calculations.

### Numerical integration

The script implements a trapezoidal integration method. This is used to approximate expectation values on a finite spatial grid.

For a normalized wavefunction,

`∫ |ψ(x)|² dx = 1`.

The numerical implementation explicitly normalizes the discretized wavefunction before calculating expectation values.

### Numerical momentum operator

The Python implementation uses a finite-difference derivative to approximate

`dψ/dx`.

The momentum operator is then applied as

`p̂ψ = -iħ dψ/dx`.

The second derivative is used for the momentum-squared expectation value.

This demonstrates how an abstract quantum operator becomes an executable numerical operation.

### Fourier transformation

A direct discrete Fourier transform is implemented rather than relying on an external package. This makes the mathematical structure visible.

The inverse transform is also implemented and tested by reconstructing the original signal.

The reconstruction error provides a basic numerical consistency check.

### Commutator demonstration

The Python script explicitly applies `x̂p̂` and `p̂x̂` in both orders.

Their difference approximates

`[x̂,p̂]ψ ≈ iħψ`.

Boundary points are treated cautiously because finite-difference approximations behave differently at the edges of a finite grid.

### Wave-packet spreading

The Python implementation also calculates the analytical spreading of a free Gaussian packet:

`σₓ(t) = σₓ(0) sqrt(1 + [ħt/(2mσₓ(0)²)]²)`.

This demonstrates an important distinction. The uncertainty principle is a constraint on the statistical widths of observables, while wave-packet spreading is a consequence of time evolution.

### Measurement simulation

Repeated discrete measurements are simulated using randomly sampled outcomes.

This demonstrates the distinction between an individual measurement and a probability distribution. A single measurement produces one outcome, while expectation values and standard deviations describe the statistical behavior of repeated measurements.

## JavaScript implementation

The JavaScript implementation complements the Python program by implementing complex arithmetic explicitly.

JavaScript does not provide a built-in complex-number primitive, so the program defines a `Complex` class containing:

- real and imaginary components
- addition
- subtraction
- multiplication
- conjugation
- magnitude
- magnitude squared
- scaling
- polar representation

This is useful for showing exactly how quantum amplitudes are represented computationally.

### Born rule

The `magnitudeSquared()` method directly implements the mathematical operation required by the Born rule.

A complex amplitude is converted into a probability through its absolute square.

### Gaussian wavefunction

The JavaScript program constructs a Gaussian wavefunction with a complex phase.

The Gaussian envelope controls spatial localization, while the phase factor represents the mean momentum.

### Numerical position statistics

The program constructs a finite grid, evaluates the wavefunction at every point, normalizes it, and numerically calculates the expectation value and standard deviation of position.

The use of a finite grid demonstrates that a continuous quantum problem becomes an approximation when implemented on a computer.

### Momentum operator

The JavaScript program uses central finite differences to approximate the spatial derivative.

The momentum operator is then implemented as

`p̂ = -iħ d/dx`.

The resulting momentum expectation and uncertainty can be compared against the analytical Gaussian result.

### Fourier transformation

The JavaScript file includes a direct discrete Fourier transform and inverse transform.

The transform is deliberately implemented without an external package so that the `O(N²)` structure of the basic DFT is visible.

The file also estimates the relative computational scaling of direct DFT and FFT approaches.

## C++ technical case study

The C++ program models a one-dimensional quantum particle prepared as a localized Gaussian wave packet.

The case study follows a numerical-scientific workflow:

1. Define a spatial computational domain.
2. Construct a numerical grid.
3. Prepare a normalized quantum state.
4. Calculate position statistics.
5. Apply the momentum operator.
6. Calculate momentum statistics.
7. Test the uncertainty relation.
8. Test the canonical commutator.
9. Simulate repeated measurements.
10. Calculate free-particle wave-packet spreading.
11. Examine numerical convergence.

This structure resembles a small scientific-computing application rather than an isolated formula demonstration.

## C++ data structures and architecture

The C++ implementation uses several structures and functions with distinct responsibilities.

`Grid` stores spatial coordinates and grid spacing.

`GaussianPacket` stores the physical parameters of the wave packet and provides an `evaluate()` method for calculating its complex amplitude.

`MomentumStatistics` stores the mean momentum, mean momentum squared, and momentum standard deviation.

`MeasurementStatistics` stores empirical results from repeated measurements.

The implementation separates:

- grid construction
- integration
- wavefunction generation
- normalization
- differentiation
- operator application
- statistical analysis
- physical time evolution
- validation

This separation makes numerical errors easier to identify and reduces the risk of mixing unrelated responsibilities.

## Position calculation in the C++ case study

The position expectation value is calculated using

`⟨x⟩ = ∫ ψ*(x) x ψ(x) dx`.

Since `ψ*ψ = |ψ|²`, this can also be written as an integral of `x|ψ|²`.

The position variance is then obtained from

`(Δx)² = ⟨x²⟩ - ⟨x⟩²`.

The implementation protects against tiny negative variances caused by floating-point subtraction.

A mathematically nonnegative quantity can sometimes become something like `-10^-16` numerically because two nearly equal floating-point quantities were subtracted.

## Momentum calculation in the C++ case study

The momentum operator is applied through the finite-difference derivative:

`p̂ψ = -iħ dψ/dx`.

The momentum-squared operator is calculated through the second derivative:

`p̂²ψ = -ħ² d²ψ/dx²`.

The program then evaluates

`⟨p⟩`

and

`⟨p²⟩`

to obtain

`Δp = sqrt(⟨p²⟩ - ⟨p⟩²)`.

For the Gaussian packet, this numerical result can be compared with the analytical value

`Δp = ħ/(2σₓ)`.

## Numerical differentiation

The interior points use the central finite-difference approximation

`f'(x) ≈ [f(x+Δx)-f(x-Δx)]/(2Δx)`.

This approximation has second-order truncation accuracy with respect to the grid spacing.

The boundaries use one-sided differences because points outside the computational domain are unavailable.

This creates a practical numerical consideration: operator identities that are exact in continuous infinite-dimensional quantum mechanics may only be approximately reproduced on a finite numerical grid.

## Numerical commutator

The C++ program calculates

`x̂p̂ψ`

and

`p̂x̂ψ`

separately.

Their difference is compared with

`iħψ`.

This is a direct computational representation of

`[x̂,p̂] = iħ`.

The test excludes a small number of boundary points because finite-difference boundary stencils have different numerical behavior.

## Uncertainty-product test

The program calculates

`ΔxΔp`

and compares it against

`ħ/2`.

For a Gaussian minimum-uncertainty packet, the analytical product is exactly

`ħ/2`.

The numerical result may differ slightly because of:

- finite domain size
- grid resolution
- numerical integration
- finite-difference truncation
- floating-point rounding
- boundary treatment

The program treats these effects as numerical approximation rather than physical violations of quantum mechanics.

## Convergence analysis

The C++ program performs calculations at several grid resolutions.

The convergence study reports:

- number of grid points
- grid spacing
- numerical `Δx`
- numerical `Δp`
- uncertainty product

Increasing the resolution normally reduces discretization error within an appropriate numerical regime.

This is an important scientific-computing practice. A single numerical result does not establish accuracy. Repeating the calculation with different resolutions helps identify whether the result is converging.

## Free-particle spreading

For a free Gaussian packet, the position uncertainty evolves according to

`σₓ(t) = σₓ(0) sqrt(1 + [ħt/(2mσₓ(0)²)]²)`.

The C++ implementation evaluates this expression for an electron using SI units.

The formula shows that a highly localized initial packet has a large momentum spread. The different momentum components then evolve at different rates, causing the spatial packet to broaden.

This is a dynamical consequence of quantum mechanics and should not be confused with the mathematical definition of the uncertainty relation.

## Squeezed states

The Python and JavaScript implementations include a simplified model of squeezing.

For ideal conjugate quadratures, a squeezing transformation can reduce the uncertainty of one variable while increasing the uncertainty of the conjugate variable.

Schematically,

`ΔX ∝ exp(-r)`

and

`ΔP ∝ exp(r)`.

Their product can remain at the minimum allowed value.

Squeezing is therefore not a violation of the uncertainty principle. It is a redistribution of uncertainty.

The concept is important in quantum optics and precision measurement.

## Energy-time uncertainty

A frequently encountered expression is

`ΔE Δt ≳ ħ/2`.

It requires more careful interpretation than the position-momentum relation.

In ordinary nonrelativistic quantum mechanics, time is generally treated as an evolution parameter rather than an observable represented by a position-like operator.

Depending on context, `Δt` can represent a characteristic duration, lifetime, evolution timescale, or measurement interval.

It should therefore not automatically be interpreted as exactly the same mathematical construction as `Δx` and `Δp`.

## Other uncertainty relations

The general operator framework applies to other pairs of observables.

For angular momentum,

`[Lₓ,Lᵧ] = iħL_z`.

The corresponding uncertainty relation is

`ΔLₓ ΔLᵧ ≥ ħ|⟨L_z⟩|/2`.

This demonstrates that the lower bound can depend on the state through the expectation value of the commutator.

## Quantum uncertainty versus measurement error

These concepts must be distinguished carefully.

### Quantum uncertainty

Quantum uncertainty is the intrinsic statistical spread predicted by a quantum state.

For an observable `A`,

`ΔA = sqrt(⟨A²⟩ - ⟨A⟩²)`.

### Measurement error

Measurement error can arise from:

- detector noise
- calibration errors
- finite resolution
- environmental disturbances
- imperfect experimental procedures
- electronic noise
- statistical sampling limitations

Improving an instrument can reduce technical measurement error, but it does not eliminate the intrinsic variance of a quantum state.

Conversely, an experiment can have significant technical error even when the quantum state itself has a very small intrinsic uncertainty.

## Common misconceptions

### The uncertainty principle is only about bad instruments

Incorrect.

The lower bound follows from quantum-mechanical operator structure. Experimental imperfections are a separate issue.

### A particle does not have a quantum state until it is measured

Incorrect.

A quantum state is used to calculate probabilities for possible measurements. Measurement selects an outcome according to the relevant probability distribution.

### Position and momentum can never both be measured

This is too strong.

Both quantities can be measured experimentally, but the uncertainties associated with their distributions obey quantum constraints. The precise operational interpretation of sequential or joint measurements depends on the measurement scheme.

### Measurement disturbance is the entire explanation

Incomplete.

Measurement disturbance is relevant to many quantum measurement discussions, but the standard uncertainty relation follows mathematically from the state, operators, and their commutator.

### Every quantum observable must have nonzero uncertainty

Incorrect.

A quantum state can be an eigenstate of an observable and therefore have zero variance for that observable.

The important issue is whether the same state can simultaneously have zero variance for another noncommuting observable.

## Edge cases

### Momentum eigenstate

An ideal momentum eigenstate has sharply defined momentum but is spatially delocalized.

A perfect plane wave is not square-integrable over an infinite domain, so it is treated as a generalized state rather than an ordinary normalized wavefunction.

### Position eigenstate

An ideal position eigenstate is represented using a Dirac delta distribution rather than an ordinary square-integrable function.

Its momentum distribution is correspondingly completely spread out.

### Finite numerical domains

Computational simulations cannot normally represent an infinite spatial domain directly.

The selected boundaries can therefore influence the numerical result.

A wave packet that reaches a boundary may reflect, wrap around, or require a special absorbing boundary treatment depending on the numerical method.

### Finite grid spacing

A coarse grid cannot resolve arbitrarily narrow wavefunctions or high-frequency oscillations.

Insufficient resolution can produce incorrect expectation values, derivative errors, or apparent violations caused entirely by numerical approximation.

### Floating-point cancellation

Expressions such as

`⟨A²⟩ - ⟨A⟩²`

can involve subtraction of nearly equal numbers.

Finite precision can therefore produce a tiny negative value even though the exact variance is nonnegative.

The implementations explicitly account for this possibility.

## Common implementation mistakes

### Forgetting normalization

A wavefunction must satisfy the correct normalization condition before probabilities and expectation values are interpreted physically.

### Treating `ψ` as the probability

The wavefunction is an amplitude.

The probability density is `|ψ|²`.

### Omitting the complex conjugate

Inner products require the conjugate of the bra-side wavefunction.

For example,

`⟨ψ|A|ψ⟩`

contains `ψ*`.

### Using the wrong momentum operator

In position representation, momentum is

`p̂ = -iħ d/dx`.

The factor `-iħ` is essential.

### Ignoring units

Position and momentum have different physical units. Their product has units of action, matching the dimensions of `ħ`.

The numerical examples sometimes use dimensionless units with `ħ = 1` to simplify computation. The C++ spreading example switches to SI values when demonstrating a physical electron.

### Ignoring boundaries

Finite-difference operators near boundaries require special treatment.

### Assuming numerical equality must be exact

A numerical calculation is an approximation. Small deviations from analytical results are expected and should be evaluated relative to numerical resolution and error tolerances.

## Performance considerations

The direct DFT implementations in Python and JavaScript use the mathematical definition directly.

For `N` samples, the direct DFT requires approximately `N²` operations.

An FFT reduces this to approximately `N log N`.

This distinction becomes substantial as the grid grows.

Finite-difference methods have a different computational structure. Applying a local derivative operator is generally inexpensive because each point depends on a small number of neighboring points.

Spectral methods can provide high accuracy for suitable problems but introduce additional considerations involving Fourier transforms, boundary conditions, and domain representation.

## Numerical accuracy considerations

Accuracy depends on several factors:

- grid spacing
- spatial domain size
- integration method
- derivative approximation
- boundary conditions
- wavefunction normalization
- floating-point precision
- physical parameter scales
- algorithmic complexity

A reliable numerical study should compare results with analytical solutions when available and perform convergence tests.

The Gaussian minimum-uncertainty state is especially useful because its analytical position and momentum uncertainties are known.

## Security and reliability considerations

Scientific software has reliability requirements even when it does not process sensitive data.

The implementations validate:

- empty inputs
- invalid probabilities
- zero or negative widths
- invalid masses
- incompatible array sizes
- invalid numerical grids
- zero wavefunction norms
- significantly negative calculated variances

Explicit validation is preferable to silently propagating invalid numerical values.

In larger scientific systems, additional concerns include deterministic experiment configuration, reproducible random seeds, numerical overflow and underflow monitoring, input provenance, unit consistency, and independent verification of important calculations.

## Python, JavaScript, and C++ comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Primary role | Mathematical exploration | Executable numerical demonstration | Technical numerical case study |
| Complex numbers | Native complex type | Explicit `Complex` class | Standard-library complex type |
| Numerical integration | Implemented directly | Implemented directly | Implemented directly |
| Momentum operator | Finite differences | Finite differences | Finite differences |
| Fourier transform | Direct DFT | Direct DFT | Discussed through numerical design |
| Commutator | Numerically tested | Numerically tested | Numerically tested |
| Wave-packet spreading | Analytical model | Analytical model | Physical SI example |
| Measurement simulation | Random sampling | Random sampling | Random sampling |
| Convergence analysis | Numerical experiments | Basic numerical experiments | Explicit resolution study |
| Main educational emphasis | Mathematical and physical depth | Language-level numerical implementation | Systems and numerical-engineering design |

## Practical applications

The uncertainty principle is relevant to many areas of modern physics.

### Atomic physics

Atomic electrons cannot be treated as classical particles with simultaneously exact positions and momenta. Quantum uncertainty contributes to the structure and stability of atoms.

### Quantum chemistry

Electron wavefunctions and their momentum and position distributions are fundamental to molecular modeling.

### Quantum optics

Uncertainty relations apply to optical field quadratures. Squeezed states exploit the redistribution of uncertainty between conjugate variables.

### Semiconductor physics

Quantum confinement changes allowed states and spatial distributions in nanoscale structures.

### Nanotechnology

When characteristic dimensions become sufficiently small, quantum effects become increasingly important.

### Quantum information

Measurement uncertainty, incompatible observables, state preparation, and uncertainty relations are central to quantum information theory.

### Precision measurement

Quantum-limited noise and squeezed states are important in high-precision sensing and metrology.

## Conceptual interpretation

The central lesson is that quantum uncertainty is a mathematical and physical property of quantum states.

The standard deviation of an observable quantifies the spread of possible outcomes. Noncommuting operators impose limits on how sharply certain observables can simultaneously be defined within the same state.

For position and momentum, the key chain of ideas is:

`wavefunction → probability distribution → expectation values → variance → operators → commutator → uncertainty relation`

The Gaussian wave packet provides a particularly clear case because it reaches the minimum allowed position-momentum uncertainty product.

The computational implementations make the abstract mathematics concrete by constructing wavefunctions, calculating probability distributions, applying differential operators, evaluating expectation values, testing commutators, and examining numerical convergence.
