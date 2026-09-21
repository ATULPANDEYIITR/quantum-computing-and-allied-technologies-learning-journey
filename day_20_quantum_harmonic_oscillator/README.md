# Quantum Harmonic Oscillator

## Introduction

The quantum harmonic oscillator is one of the central exactly solvable models in quantum mechanics. It describes a particle moving in a quadratic potential,

`V(x) = 1/2 m omega^2 x^2`.

Its importance extends far beyond the particular physical system represented by this potential. The oscillator provides a mathematical framework for understanding quantized energy, stationary states, zero-point motion, operator methods, ladder operators, uncertainty, coherent states, perturbation theory, semiclassical approximations, and thermal occupation.

Many physical systems can be approximated by a harmonic oscillator near a stable equilibrium. Examples include molecular vibrations, lattice vibrations, electromagnetic field modes, mechanical resonators, phonons, quantum optical modes, and small oscillations of larger systems.

The three implementations in this repository approach the same physical model from different computational perspectives:

- The Python implementation develops the mathematical model extensively and uses numerical integration, operator matrices, state vectors, coherent states, thermal calculations, perturbation theory, and measurement simulations.
- The JavaScript implementation emphasizes executable numerical demonstrations, complex-number manipulation, finite-dimensional operators, state evolution, and reproducible measurement simulation without external packages.
- The C++ implementation develops an industry-style technical case study around a finite-basis quantum resonator engine, with explicit classes, matrix operations, state management, validation, performance considerations, and failure handling.

All three implementations use dimensionless units by default:

`hbar = 1`, `m = 1`, and `omega = 1`.

This removes unnecessary numerical scales while preserving the structure of the physical equations.

---

## Fundamental physical model

The classical harmonic oscillator has the Hamiltonian

`H = p^2/(2m) + 1/2 m omega^2 x^2`.

The corresponding potential energy is

`V(x) = 1/2 m omega^2 x^2`.

The classical equation of motion is

`m d^2x/dt^2 + m omega^2 x = 0`.

Its general solution is sinusoidal. The oscillator has a continuous range of possible classical energies.

Quantum mechanics changes the mathematical description. Position and momentum become operators, and the state is represented by a wavefunction or an abstract vector in Hilbert space.

The quantum Hamiltonian becomes

`H = p-hat^2/(2m) + 1/2 m omega^2 x-hat^2`.

The stationary Schrödinger equation is

`H psi_n = E_n psi_n`.

Its allowed energies are discrete:

`E_n = hbar omega (n + 1/2)`,

where

`n = 0, 1, 2, ...`.

The integer `n` is the quantum number associated with the oscillator's energy eigenstate.

---

## Important terminology

### Hamiltonian

The Hamiltonian is the operator representing the total energy of a quantum system.

For the harmonic oscillator,

`H = p-hat^2/(2m) + 1/2 m omega^2 x-hat^2`.

The Hamiltonian determines time evolution through the Schrödinger equation.

### Potential

The potential specifies how potential energy varies with position.

For the oscillator,

`V(x) = 1/2 m omega^2 x^2`.

The quadratic form makes the oscillator exactly solvable.

### Energy eigenstate

An energy eigenstate satisfies

`H |n> = E_n |n>`.

A measurement of energy on an exact energy eigenstate produces its corresponding energy eigenvalue with certainty.

### Quantum number

The oscillator quantum number `n` identifies the energy eigenstate.

It begins at zero rather than one.

### Zero-point energy

The ground-state energy is

`E_0 = 1/2 hbar omega`.

Therefore the lowest energy is not zero.

This is called zero-point energy.

### Wavefunction

The position-space wavefunction `psi_n(x)` contains the probability amplitude for finding the particle at position `x`.

The probability density is

`|psi_n(x)|^2`.

### Hilbert space

The quantum state belongs to a Hilbert space. The oscillator has infinitely many number states in its exact mathematical description.

Computational implementations normally truncate this infinite space to a finite basis.

### Ladder operators

The annihilation operator `a` lowers the number state:

`a |n> = sqrt(n) |n-1>`.

The creation operator `a-dagger` raises it:

`a-dagger |n> = sqrt(n+1) |n+1>`.

These operators provide a compact algebraic solution to the oscillator.

### Number operator

The number operator is

`N = a-dagger a`.

It satisfies

`N |n> = n |n>`.

The Hamiltonian can therefore be written as

`H = hbar omega (N + 1/2)`.

---

## Dimensionless formulation

The characteristic oscillator length is

`x_osc = sqrt(hbar/(m omega))`.

A dimensionless coordinate can be defined by

`xi = x / x_osc`.

In this representation, the wavefunction has a particularly simple form and the mathematical structure becomes independent of the particular physical values of `hbar`, `m`, and `omega`.

Using dimensionless variables is common in theoretical and computational work because it:

- reduces numerical scale differences
- makes equations easier to compare
- exposes universal mathematical structure
- simplifies debugging
- avoids unnecessary unit conversions
- often improves numerical conditioning

The Python implementation explicitly demonstrates both dimensionless and physical-parameter calculations.

---

## Energy quantization

The exact spectrum is

`E_n = hbar omega (n + 1/2)`.

The first levels are

`E_0 = 1/2 hbar omega`

`E_1 = 3/2 hbar omega`

`E_2 = 5/2 hbar omega`

`E_3 = 7/2 hbar omega`.

The difference between adjacent levels is constant:

`E_(n+1) - E_n = hbar omega`.

This equal spacing distinguishes the ideal harmonic oscillator from many more complicated quantum systems.

The Python, JavaScript, and C++ implementations all calculate these levels directly.

The C++ implementation stores the spectrum as the diagonal of the exact Hamiltonian matrix.

---

## Classical versus quantum oscillator

The classical and quantum descriptions share the same quadratic Hamiltonian but differ fundamentally in their state descriptions and allowed energies.

| Property | Classical oscillator | Quantum oscillator |
|---|---|---|
| Position | Numerical variable | Operator |
| Momentum | Numerical variable | Operator |
| State | Phase-space trajectory | Hilbert-space state |
| Energy | Continuous | Discrete for stationary states |
| Ground energy | Can be zero | `hbar omega / 2` |
| Probability | Not fundamental in the same way | Central to measurement |
| Time evolution | Classical differential equation | Schrödinger equation |
| State superposition | Not a quantum principle | Fundamental |

The classical oscillator is still important because the quantum oscillator approaches classical behavior in suitable limits.

---

## Harmonic oscillator wavefunctions

The normalized stationary-state wavefunctions are

`psi_n(x) = 1/sqrt(2^n n! sqrt(pi) x_osc) H_n(xi) exp(-xi^2/2)`,

where `H_n` is the physicists' Hermite polynomial.

The first Hermite polynomials are

`H_0(x) = 1`

`H_1(x) = 2x`

`H_2(x) = 4x^2 - 2`

`H_3(x) = 8x^3 - 12x`

`H_4(x) = 16x^4 - 48x^2 + 12`.

The implementations calculate Hermite polynomials using the recurrence relation

`H_(n+1)(x) = 2x H_n(x) - 2n H_(n-1)(x)`.

This recurrence is preferable to repeatedly expanding large symbolic expressions.

---

## Parity and nodes

The oscillator potential is symmetric:

`V(-x) = V(x)`.

Consequently, oscillator eigenstates have definite parity.

For even `n`, the wavefunction is even:

`psi_n(-x) = psi_n(x)`.

For odd `n`, it is odd:

`psi_n(-x) = -psi_n(x)`.

The probability density is always even:

`|psi_n(-x)|^2 = |psi_n(x)|^2`.

The state `n` has exactly `n` nodes in the finite position domain.

The Python implementation evaluates wavefunctions numerically and checks density symmetry.

---

## Normalization

A physical wavefunction must satisfy

`integral |psi(x)|^2 dx = 1`.

This condition ensures that the total probability of all possible position measurements is one.

The Python and JavaScript implementations numerically evaluate this integral using the trapezoidal rule.

The numerical domain is finite, such as `[-8, 8]`, rather than the exact infinite interval. The Gaussian factor causes the wavefunction to become extremely small away from the origin, so the finite computational interval provides a practical approximation.

A numerical normalization error can arise from:

- an insufficient spatial interval
- too few integration intervals
- floating-point roundoff
- an incorrect normalization constant
- an incorrect Hermite polynomial
- overflow or underflow at extreme parameters

The implementations use explicit verification tolerances rather than requiring exact floating-point equality.

---

## Orthogonality

Distinct stationary states are orthogonal:

`integral psi_n(x) psi_m(x) dx = 0` for `n != m`.

Together with normalization, this gives

`<n|m> = delta_nm`.

This property is essential because the number states form an orthonormal basis.

It allows a general state to be expressed as

`|psi> = sum_n c_n |n>`.

The coefficients satisfy

`sum_n |c_n|^2 = 1`.

The Python implementation numerically checks selected wavefunction overlaps.

---

## Ladder-operator method

The ladder-operator approach defines

`a = sqrt(m omega/(2 hbar)) x-hat + i p-hat/sqrt(2 m hbar omega)`

and

`a-dagger = sqrt(m omega/(2 hbar)) x-hat - i p-hat/sqrt(2 m hbar omega)`.

Their fundamental commutation relation is

`[a, a-dagger] = 1`.

The position and momentum operators can then be recovered as

`x-hat = sqrt(hbar/(2m omega)) (a + a-dagger)`

and

`p-hat = -i sqrt(m hbar omega/2) (a - a-dagger)`.

The Hamiltonian becomes

`H = hbar omega (a-dagger a + 1/2)`.

Defining

`N = a-dagger a`

gives

`H = hbar omega (N + 1/2)`.

This algebra immediately produces the energy spectrum.

---

## The ground state and annihilation operator

The ground state is defined by

`a |0> = 0`.

This equation is powerful because it determines the ground-state wavefunction without solving the full differential equation directly.

Repeated application of the creation operator produces higher states:

`|n> = 1/sqrt(n!) (a-dagger)^n |0>`.

The Python, JavaScript, and C++ programs explicitly apply the annihilation and creation operators to finite state vectors.

For example, the annihilation operator acting on `|3>` gives

`a|3> = sqrt(3)|2>`.

The creation operator gives

`a-dagger|3> = 2|4>`.

The ground-state case is special:

`a|0> = 0`.

---

## Finite-dimensional truncation

The exact oscillator has infinitely many basis states.

A computer cannot normally store an infinite vector, so implementations choose a finite cutoff `N`.

The state becomes

`|psi> = c_0|0> + c_1|1> + ... + c_(N-1)|N-1>`.

This is an approximation to the infinite-dimensional problem.

The cutoff introduces an important subtlety.

In the exact Hilbert space,

`[a, a-dagger] = I`.

In a finite matrix representation, this cannot hold exactly for every basis state.

The final state cannot be raised because there is no represented `|N>` state. Consequently, the top boundary produces an artificial deviation in the commutator.

Both the Python and JavaScript implementations explicitly demonstrate this effect.

This is not a physical violation of quantum mechanics. It is a numerical truncation artifact.

---

## Position and momentum matrix structure

In the number basis, the position operator has nonzero matrix elements only between neighboring states:

`<n-1|x|n> = sqrt(hbar n/(2m omega))`

and

`<n+1|x|n> = sqrt(hbar(n+1)/(2m omega))`.

The momentum operator has the same nearest-neighbor structure but with imaginary coefficients and opposite signs.

This sparsity is computationally important.

For large basis dimensions, storing these operators as dense matrices wastes memory and computation. Sparse representations or direct recurrence formulas are preferable.

The C++ implementation deliberately uses general matrices for clarity while reporting the associated performance limitation.

---

## Expectation values

For an energy eigenstate,

`<x> = 0`

and

`<p> = 0`.

The oscillator's symmetry is responsible for these vanishing first moments.

The second moments are

`<x^2> = hbar/(m omega) (n + 1/2)`

and

`<p^2> = m hbar omega (n + 1/2)`.

Since the first moments vanish,

`Delta x = sqrt(<x^2>)`

and

`Delta p = sqrt(<p^2>)`.

Therefore,

`Delta x Delta p = hbar (n + 1/2)`.

For the ground state,

`Delta x Delta p = hbar/2`.

The ground state therefore saturates the Heisenberg uncertainty bound.

For excited number states, the product is larger.

---

## Zero-point motion

The ground state cannot have both position and momentum equal to zero with zero uncertainty.

If the particle had exactly zero position uncertainty and zero momentum uncertainty, it would violate the uncertainty principle.

The ground state instead has finite uncertainties:

`Delta x_0 = sqrt(hbar/(2m omega))`

and

`Delta p_0 = sqrt(m hbar omega/2)`.

The oscillator therefore possesses zero-point fluctuations even at its lowest energy.

This concept is important in quantum optical modes, mechanical resonators, molecular vibrations, phonons, and quantum field theory.

---

## Time evolution

A stationary state evolves according to

`psi_n(x,t) = psi_n(x) exp(-i E_n t/hbar)`.

The complex phase changes with time, but the probability density does not:

`|psi_n(x,t)|^2 = |psi_n(x)|^2`.

For a superposition,

`|psi(t)> = sum_n c_n exp(-i E_n t/hbar)|n>`.

Relative phases between components can change, producing time-dependent interference patterns.

The implementations evolve number-basis coefficients directly. Because the Hamiltonian is diagonal in this basis, no general matrix-exponential algorithm is necessary.

This is both mathematically exact for the truncated number-state model and computationally efficient.

---

## Coherent states

A coherent state is written as

`|alpha> = exp(-|alpha|^2/2) sum_n alpha^n/sqrt(n!) |n>`.

The coherent-state parameter `alpha` is complex.

Its mean occupation number is

`<N> = |alpha|^2`.

The number-state probability distribution is Poissonian:

`P(n) = exp(-|alpha|^2) |alpha|^(2n) / n!`.

The mean position is

`<x> = sqrt(2hbar/(m omega)) Re(alpha)`.

The mean momentum is

`<p> = sqrt(2m hbar omega) Im(alpha)`.

The coherent-state uncertainties are

`Delta x = sqrt(hbar/(2m omega))`

and

`Delta p = sqrt(m hbar omega/2)`.

Thus,

`Delta x Delta p = hbar/2`.

Coherent states are minimum-uncertainty states.

They are particularly important because their expectation values follow classical oscillator-like motion.

The Python and JavaScript implementations construct coherent states in a finite number basis. The C++ implementation does the same using standard-library complex arithmetic.

---

## Coherent-state truncation

The exact coherent state contains infinitely many number-state components.

A finite implementation therefore chooses a maximum basis dimension.

The probability distribution is Poissonian with mean

`|alpha|^2`.

Consequently, the basis must be large enough to include the region where the probability distribution has significant weight.

If `|alpha|^2` becomes large while the basis remains small, truncation becomes inaccurate.

This illustrates a general numerical principle:

**The required basis size depends on the physical state being represented.**

A fixed cutoff is not universally valid.

---

## Measurement simulation

Quantum mechanics predicts probabilities, not deterministic outcomes for arbitrary states.

For

`|psi> = sum_n c_n |n>`,

a measurement of energy in the number basis produces outcome `n` with probability

`P(n) = |c_n|^2`.

The implementations simulate repeated measurements.

The workflow is:

1. Construct a normalized state.
2. Calculate `|c_n|^2`.
3. Interpret the probabilities as a discrete distribution.
4. Generate many random measurements.
5. Compare empirical frequencies with theoretical probabilities.

The Python implementation uses a seeded pseudo-random generator.

The JavaScript implementation contains a deterministic educational pseudo-random generator.

The C++ implementation uses `std::mt19937` and `std::discrete_distribution`.

The random generators are intended for reproducible numerical demonstrations, not cryptographic applications.

---

## Thermal harmonic oscillator

At finite temperature, the oscillator is not generally in one energy eigenstate.

Using

`beta = 1/(k_B T)`,

the canonical partition function is

`Z = exp(-beta hbar omega/2) / (1 - exp(-beta hbar omega))`.

The mean occupation number is

`<N> = 1/(exp(beta hbar omega) - 1)`.

The mean energy is

`<E> = hbar omega [1/2 + 1/(exp(beta hbar omega) - 1)]`.

The implementations use units where `k_B = 1` for the thermal demonstrations.

At low temperature, the thermal population is concentrated near the ground state.

At high temperature, many energy levels become populated and the oscillator approaches classical thermal behavior.

---

## Numerical stability at low temperature

The thermal occupation contains

`1/(exp(x) - 1)`.

For large `x`, direct exponential evaluation can overflow in some environments.

The implementations explicitly handle large values and use `expm1` where appropriate.

This is a useful numerical-programming lesson:

Mathematically equivalent expressions are not necessarily numerically equivalent.

For small `x`, `expm1(x)` provides better numerical precision than calculating `exp(x) - 1` directly.

---

## Quartic anharmonic perturbation

The ideal oscillator has a quadratic potential:

`V(x) = 1/2 m omega^2 x^2`.

A more realistic system can contain anharmonic terms such as

`H' = lambda x^4`.

The total Hamiltonian becomes

`H = H_0 + lambda x^4`.

For sufficiently weak perturbations, first-order perturbation theory gives

`Delta E_n^(1) = <n|lambda x^4|n>`.

For the harmonic oscillator,

`<n|x^4|n> = 3 [hbar/(2m omega)]^2 (2n^2 + 2n + 1)`.

Therefore,

`Delta E_n^(1) = lambda 3 [hbar/(2m omega)]^2 (2n^2 + 2n + 1)`.

The Python, JavaScript, and C++ implementations calculate this correction.

The result demonstrates an important relationship between exactly solvable models and more complicated systems: a solvable model can serve as the reference system for controlled approximations.

---

## Why the perturbative correction increases with n

Higher oscillator states have larger spatial extent.

The second moment grows according to

`<x^2> = hbar/(m omega)(n + 1/2)`.

Higher-order spatial moments also increase with `n`.

A quartic potential therefore affects high-energy states more strongly than low-energy states.

This is why the first-order correction contains the quadratic polynomial

`2n^2 + 2n + 1`.

For sufficiently strong anharmonicity, first-order perturbation theory may no longer be reliable and direct numerical methods become necessary.

---

## Semiclassical WKB relationship

The Wentzel-Kramers-Brillouin approximation provides a semiclassical quantization condition.

For a one-dimensional bound system, the leading quantization rule can be expressed schematically as

`integral p(x) dx = (n + 1/2) h`.

For the harmonic oscillator, this procedure reproduces

`E_n = hbar omega(n + 1/2)`.

The harmonic oscillator is therefore a special and important example in which the leading WKB spectrum agrees with the exact quantum result.

This agreement should not be assumed for arbitrary potentials.

---

## Classical limit

The oscillator is a useful model for studying the relationship between quantum and classical mechanics.

Several regimes can make quantum behavior appear increasingly classical.

One is a high quantum number regime where `n` is large.

Another is a thermal regime where

`k_B T >> hbar omega`.

For a coherent state with a large mean occupation,

`|alpha|^2 >> 1`,

the relative quantum fluctuations become small compared with the magnitude of the classical oscillation.

The classical limit is therefore not a single switch. It depends on the physical quantities being compared.

---

## Python implementation

The Python file is the most extensive mathematical study.

It contains a classical oscillator model through the `ClassicalOscillator` class.

The quantum spectrum is implemented through functions such as `energy_level()` and `energy_levels()`.

The characteristic length is calculated by `oscillator_length()`.

Hermite polynomials are implemented using recurrence relations in `hermite_physicists()`.

The normalized stationary wavefunctions are implemented by `dimensionless_wavefunction()` and `wavefunction()`.

Probability density is obtained from `probability_density()`.

The numerical integration routine `trapezoidal_integral()` is used to verify normalization, orthogonality, and expectation values.

Expectation-value functions demonstrate exact analytical results for position and momentum moments.

The ladder operators are represented both as transformations on state vectors and as finite matrices.

The matrix implementation includes:

- matrix addition
- matrix subtraction
- matrix multiplication
- scalar multiplication
- matrix-vector multiplication
- inner products
- expectation values
- commutators

The functions `position_matrix()` and `momentum_matrix()` construct the physical operators from `a` and `a-dagger`.

The Hamiltonian is constructed in two ways:

- directly as the exact diagonal number-basis Hamiltonian
- from finite position and momentum matrices

This comparison exposes the effects of basis truncation.

The Python file also includes coherent-state construction, thermal occupation, time evolution, quartic perturbation, WKB comparison, measurement simulation, parameter scaling, probability-current analysis, parity checks, edge-case validation, and an automated verification suite.

---

## JavaScript implementation

The JavaScript implementation focuses on executable numerical programming using the language's standard features.

Because JavaScript does not provide a standard built-in complex-number class, the implementation defines complex values using objects containing `real` and `imaginary` components.

Operations such as:

- addition
- multiplication
- scaling
- conjugation
- magnitude
- complex exponentiation

are implemented explicitly.

This makes the mathematics visible rather than hiding it behind an external library.

The JavaScript file implements Hermite polynomials using the same recurrence relation as the Python implementation.

It performs numerical integration with the trapezoidal rule.

It constructs number-state vectors and applies ladder operators directly.

Finite matrices are represented as arrays of arrays.

The `commutator()` function demonstrates

`[A,B] = AB - BA`.

The position and momentum matrices are constructed from the ladder operators.

The `expectationMatrix()` function evaluates expressions of the form

`<psi|A|psi>`.

The time-evolution function applies the phase

`exp(-i E_n t/hbar)`

to every number-state coefficient.

The coherent-state implementation constructs the finite representation and normalizes it after truncation.

Thermal quantities are calculated using standard JavaScript mathematical functions, including `Math.expm1()` for improved numerical behavior.

The measurement simulation demonstrates how theoretical quantum probabilities can be converted into repeated discrete outcomes.

The JavaScript implementation is therefore particularly useful for understanding how the mathematical model can be translated into a runtime that is also widely used for browser and application development.

---

## C++ case study

The C++ program models a technical scenario involving a quantum nanomechanical resonator.

The central class is `QuantumHarmonicOscillator`.

It receives `PhysicalParameters` containing:

- `hbar`
- `mass`
- `omega`

and a finite basis dimension.

The `PhysicalParameters` structure validates the physical values before the oscillator is constructed.

The oscillator class provides:

- energy levels
- basis states
- annihilation operator
- creation operator
- position operator
- momentum operator
- exact Hamiltonian
- Hamiltonian constructed from x and p
- ladder-operator application
- time evolution
- uncertainty calculations
- coherent states
- thermal quantities
- quartic perturbation corrections

The implementation separates generic matrix operations from the physical oscillator class.

This separation is an important software-engineering decision because matrix arithmetic is a general computational mechanism, while the harmonic oscillator defines the domain-specific behavior.

---

## C++ matrix design

Matrices are represented as

`std::vector<std::vector<Complex>>`.

This representation is simple and readable, although it is not optimal for large-scale numerical linear algebra.

The program implements matrix:

- creation
- identity construction
- addition
- subtraction
- scalar multiplication
- multiplication
- vector multiplication

The number-basis operators are sparse, but the demonstration intentionally uses dense matrices so that the operator algebra can be inspected directly.

In a production numerical implementation, a sparse matrix structure would be preferable for large basis sizes.

---

## C++ state representation

A quantum state is represented as

`std::vector<Complex>`.

Each element is a coefficient corresponding to a number state.

For example, conceptually,

`state[0]` represents the coefficient of `|0>`,

`state[1]` represents the coefficient of `|1>`,

and so on.

The `stateNorm()` function calculates

`sqrt(sum |c_n|^2)`.

The `normalizeState()` function divides every coefficient by this norm.

This explicitly enforces the physical requirement that a valid state has unit norm.

---

## C++ time evolution design

The oscillator Hamiltonian is diagonal in the number basis.

Therefore, the time evolution can be performed without computing a general matrix exponential.

Each coefficient is updated using

`c_n(t) = c_n(0) exp(-i E_n t/hbar)`.

This is substantially simpler than applying a general-purpose matrix exponential.

The example demonstrates a broader computational principle:

**Use known mathematical structure before selecting a general numerical algorithm.**

A generic algorithm may be mathematically valid but unnecessarily expensive.

---

## Complexity considerations

For a basis dimension `N`:

- A dense matrix requires `O(N^2)` storage.
- Dense matrix multiplication requires `O(N^3)` arithmetic operations.
- Dense matrix-vector multiplication requires `O(N^2)` operations.
- The ladder operators contain only `O(N)` nonzero entries.
- The exact diagonal Hamiltonian needs only `O(N)` meaningful values.

The C++ implementation deliberately uses dense matrices because the objective is to expose the mathematical structure.

For larger calculations, sparse matrices, direct operator actions, and specialized eigensolvers would reduce computational cost.

---

## Finite-basis boundary effects

The finite basis is one of the most important implementation details.

Suppose the basis contains

`|0>, |1>, ..., |N-1>`.

The creation operator should transform

`|N-1>` into a multiple of `|N>`.

But `|N>` is not stored.

The computational representation therefore drops this component.

This causes the finite-dimensional commutator to differ from the exact identity at the upper boundary.

The same issue can appear when:

- evolving highly excited states
- representing coherent states with large `|alpha|`
- calculating high-order moments
- constructing nonlinear Hamiltonians
- comparing finite matrices against infinite-dimensional analytical identities

A basis cutoff should therefore be treated as a numerical parameter, not merely as an implementation detail.

---

## Edge cases

The implementations explicitly address several edge conditions.

### Ground state

The ground state has

`n = 0`.

The annihilation operator must return the zero state.

The energy remains

`E_0 = hbar omega/2`.

### Negative quantum number

Negative `n` values are invalid.

The implementations reject them instead of silently producing incorrect results.

### Nonpositive physical parameters

The harmonic oscillator requires positive:

- mass
- angular frequency
- hbar

The implementations validate these quantities.

### Nonpositive temperature

Thermal formulas require positive temperature.

A zero or negative temperature is rejected by the relevant functions in these conventional canonical calculations.

### Zero vector normalization

The zero vector cannot be converted into a normalized quantum state.

Attempting to normalize it produces an error.

### Finite basis cutoff

Raising the highest represented state cannot be performed exactly within the finite representation.

The code documents this as a truncation boundary rather than treating it as physical behavior.

### Numerical integration domain

The exact wavefunctions extend over the entire real line.

Numerical calculations use a finite interval and therefore introduce a small approximation.

---

## Common mistakes

### Treating energy as continuous

The harmonic oscillator's stationary energy spectrum is discrete.

Writing `E = arbitrary value` for a stationary oscillator state is incorrect.

### Forgetting zero-point energy

The ground state is not zero energy.

The correct value is

`E_0 = hbar omega/2`.

### Using the wrong Hermite convention

Different fields use different Hermite-polynomial conventions.

The oscillator wavefunctions in this implementation use the physicists' Hermite polynomials.

### Confusing wavefunction with probability

`psi(x)` is a probability amplitude.

`|psi(x)|^2` is the probability density.

### Forgetting complex conjugation

The inner product is

`<phi|psi> = integral phi*(x) psi(x) dx`.

The complex conjugate is essential.

### Treating finite truncation as exact

A finite matrix representation is an approximation to the infinite-dimensional oscillator.

Boundary effects must be considered.

### Using too small a basis

A highly excited state or large-amplitude coherent state may require a larger cutoff.

### Using unstable thermal expressions

Direct evaluation of `exp(x)-1` can lose numerical precision for small `x`.

`expm1(x)` is preferable in numerical implementations.

### Assuming WKB is always exact

The harmonic oscillator has unusually favorable properties. Agreement here does not imply exact agreement for arbitrary potentials.

### Assuming perturbation theory always works

First-order perturbation theory is controlled only when the perturbation is sufficiently weak in the regime being studied.

---

## Performance considerations

The Python implementation uses standard-library numerical integration, which is suitable for educational calculations but not optimized scientific computing.

The JavaScript implementation similarly favors transparency over high-performance numerical linear algebra.

The C++ implementation provides the clearest basis for performance optimization.

For large oscillator bases, the following observations matter:

- Number-basis ladder operators are sparse.
- The harmonic oscillator Hamiltonian is diagonal in the number basis.
- Direct coefficient evolution is cheaper than a general matrix exponential.
- Dense matrix multiplication scales cubically with basis size.
- Dense matrix storage scales quadratically.
- High-order states can require larger basis cutoffs.
- Numerical integration can become expensive when the grid is unnecessarily fine.

The mathematically simplest representation is often also the computationally efficient representation.

---

## Security and reliability considerations

This topic does not inherently require network access, authentication, secrets, or external services.

The implementations therefore use no external dependencies.

The measurement simulations use pseudo-random generators only for educational statistical experiments. They are not cryptographically secure random-number generators and should not be used for security-sensitive applications.

Input validation is included for:

- negative quantum numbers
- invalid physical parameters
- invalid basis dimensions
- invalid temperatures
- zero-state normalization
- incompatible matrix and state dimensions

Floating-point values should not normally be compared using exact equality. The implementations use numerical tolerances for physical verification.

---

## Implementation considerations

The three languages expose different aspects of the same model.

Python provides concise mathematical experimentation. Functions can closely mirror the equations, making it convenient to move between analytical formulas and numerical demonstrations.

JavaScript makes the underlying data handling explicit. Complex-number arithmetic, arrays, state vectors, matrices, and deterministic simulations are implemented without external numerical libraries.

C++ introduces stronger structural organization and explicit types. The case study uses classes, structures, exceptions, standard containers, and algorithmic complexity analysis.

The physical mathematics does not change between languages. The implementation strategy changes according to the capabilities and conventions of each language.

---

## Real-world relevance

The harmonic oscillator appears directly or approximately in many areas of physics and engineering.

### Molecular vibration

Near an equilibrium bond length, a molecular potential can often be approximated by a quadratic potential. The harmonic approximation provides the first model of vibrational energy levels.

### Phonons

Lattice vibrations can be decomposed into normal modes, many of which are modeled as quantum harmonic oscillators.

### Quantum optics

A single electromagnetic field mode is mathematically equivalent to a quantum harmonic oscillator. The ladder operators become photon creation and annihilation operators.

### Mechanical resonators

Nanomechanical and optomechanical resonators can be modeled using oscillator states. Quantum fluctuations become important near the quantum regime.

### Solid-state physics

Normal modes of crystals can be quantized as harmonic oscillator degrees of freedom, producing phonon descriptions.

### Quantum field theory

Each independent normal mode of a free quantum field behaves mathematically like a quantum harmonic oscillator.

### Semiclassical physics

The oscillator provides a clear setting for studying the relationship between exact quantum mechanics, coherent states, and classical dynamics.

---

## Important distinctions

### Number state versus coherent state

A number state has definite energy and definite occupation number.

A coherent state is a superposition of infinitely many number states and has a Poissonian number distribution.

### Stationary state versus superposition

A stationary energy eigenstate has time-independent probability density.

A superposition can have time-dependent interference because its components acquire different phases.

### Exact Hilbert space versus computational basis

The exact oscillator has infinitely many number states.

A computer simulation normally uses a finite cutoff.

### Harmonic versus anharmonic potential

The harmonic potential is exactly quadratic.

An anharmonic potential contains higher-order terms such as `x^3` or `x^4`.

### Exact solution versus perturbative solution

The harmonic spectrum is exact.

A quartic correction calculated using first-order perturbation theory is approximate.

### Quantum versus classical oscillator

The classical oscillator uses trajectories and continuous energy.

The quantum oscillator uses states, operators, probability amplitudes, and quantized stationary energies.

---

## Key equations

Hamiltonian:

`H = p-hat^2/(2m) + 1/2 m omega^2 x-hat^2`

Energy:

`E_n = hbar omega(n + 1/2)`

Oscillator length:

`x_osc = sqrt(hbar/(m omega))`

Dimensionless coordinate:

`xi = x/x_osc`

Wavefunction:

`psi_n(x) = 1/sqrt(2^n n! sqrt(pi) x_osc) H_n(xi) exp(-xi^2/2)`

Annihilation:

`a|n> = sqrt(n)|n-1>`

Creation:

`a-dagger|n> = sqrt(n+1)|n+1>`

Number operator:

`N = a-dagger a`

Hamiltonian:

`H = hbar omega(N + 1/2)`

Commutation relation:

`[a,a-dagger] = 1`

Position:

`x-hat = sqrt(hbar/(2m omega))(a+a-dagger)`

Momentum:

`p-hat = -i sqrt(m hbar omega/2)(a-a-dagger)`

Position variance:

`<x^2>_n = hbar/(m omega)(n+1/2)`

Momentum variance:

`<p^2>_n = m hbar omega(n+1/2)`

Uncertainty:

`Delta x Delta p = hbar(n+1/2)`

Ground-state uncertainty:

`Delta x Delta p = hbar/2`

Coherent-state number mean:

`<N> = |alpha|^2`

Thermal occupation:

`<N> = 1/(exp(beta hbar omega)-1)`

Thermal mean energy:

`<E> = hbar omega[1/2 + 1/(exp(beta hbar omega)-1)]`

First-order quartic correction:

`Delta E_n^(1) = lambda 3[hbar/(2m omega)]^2(2n^2+2n+1)`

---

## Implementation correspondence

| Concept | Python | JavaScript | C++ |
|---|---|---|---|
| Energy spectrum | `energy_level()` | `energyLevel()` | `PhysicalParameters::energy()` |
| Oscillator length | `oscillator_length()` | `oscillatorLength()` | `oscillatorLength()` |
| Hermite polynomials | `hermite_physicists()` | `hermite()` | represented through number-basis operators |
| Wavefunctions | `wavefunction()` | `wavefunction()` | number-basis focus |
| Numerical integration | `trapezoidal_integral()` | `trapezoidalIntegral()` | validation through operator representation |
| Ladder operators | state and matrix functions | state and matrix functions | `QuantumHarmonicOscillator` methods |
| Position operator | `position_matrix()` | `positionMatrix()` | `positionOperator()` |
| Momentum operator | `momentum_matrix()` | `momentumMatrix()` | `momentumOperator()` |
| Hamiltonian | `diagonal_hamiltonian()` | matrix representation | `exactHamiltonian()` |
| Time evolution | `evolve_number_state()` | `evolveState()` | `evolve()` |
| Coherent states | `coherent_state()` | `coherentState()` | `coherentState()` |
| Thermal physics | thermal functions | thermal functions | class methods |
| Perturbation | quartic functions | quartic function | perturbation methods |
| Measurement | sampled number states | sampled number states | `sampleMeasurements()` |
| Validation | verification suite | verification suite | exception and numerical checks |

---

## Running the implementations

The Python file can be executed with a standard Python 3 installation.

The JavaScript file can be executed with a modern Node.js runtime.

The C++ program requires a compiler supporting C++17 or later.

The programs are self-contained and do not require external scientific libraries.

Each implementation prints numerical demonstrations and validation results when executed.

The C++ program is compiled using a command equivalent to `g++ -std=c++17 -O2 quantum_harmonic_oscillator.cpp -o qho`.

---

## Scope and limitations

The implementations are designed to make the oscillator mathematics computationally explicit.

They are not intended to replace specialized scientific-computing libraries for large numerical simulations.

Important limitations include:

- finite basis truncation
- finite numerical integration domains
- floating-point roundoff
- dense matrix operations in the C++ case study
- limited treatment of strongly anharmonic systems
- first-order rather than higher-order perturbation theory
- one-dimensional oscillator assumptions
- simplified thermal units with `k_B = 1`
- educational pseudo-random measurement simulations

The harmonic oscillator itself is exact within its mathematical model. The approximations arise primarily when the infinite mathematical system is represented numerically or when the harmonic model is used as an approximation to a different physical system.
