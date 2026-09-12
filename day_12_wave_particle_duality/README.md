# Wave-particle duality and quantum behavior

## Topic introduction

Wave-particle duality is one of the central ideas of quantum physics. Classical physics traditionally separates physical objects into two broad categories.

A **particle** is normally associated with localization, momentum, collisions, and a definite position at a given time.

A **wave** is normally associated with wavelength, frequency, phase, interference, diffraction, and superposition.

Quantum systems do not fit completely into either classical description. Electromagnetic radiation can produce localized detection events and exchange energy in discrete amounts, while also producing interference and diffraction. Matter such as electrons can produce localized detector events while also exhibiting diffraction and interference.

The Python script develops these ideas quantitatively. It begins with elementary wave relationships and progresses through photons, the photoelectric effect, de Broglie matter waves, double-slit interference, probability amplitudes, uncertainty, quantum states, measurement, decoherence, entanglement, and the classical limit.

The central lesson is that wave-particle duality is not best understood as a quantum object physically changing between two classical identities. Quantum mechanics provides a more general framework in which states evolve according to quantum rules and measurements produce probabilistic outcomes. Wave-like phenomena appear in the mathematical structure of amplitudes and their phases, while individual measurements can produce localized particle-like events.

## Classical wave foundations

A simple traveling wave can be represented mathematically as

    y(x,t) = A cos(kx - omega t + phi)

where:

- `A` is the amplitude.
- `k` is the wave number.
- `omega` is the angular frequency.
- `phi` is the phase.
- `x` is position.
- `t` is time.

The wave number and angular frequency are related to wavelength and ordinary frequency by

    k = 2 pi / lambda

and

    omega = 2 pi f

For a wave traveling without dispersion, the classical relationship is

    v = f lambda

For electromagnetic radiation in vacuum,

    c = f lambda

where `c` is the speed of light.

These relationships provide the mathematical vocabulary needed to understand quantum wave behavior.

## Quantization of energy

One of the foundations of quantum physics is the relationship

    E = h f

where `E` is the energy associated with a photon, `h` is Planck's constant, and `f` is frequency.

The script calculates photon energies for specified frequencies and also demonstrates integer multiples of the photon energy.

The important implication is that electromagnetic energy exchange at the quantum level is not always adequately described as an arbitrarily divisible classical quantity. A photon of frequency `f` has energy `hf`.

Higher frequency means greater energy per photon.

Intensity has a different role. At fixed frequency, increasing the intensity of a beam primarily corresponds to increasing the number of photons arriving per unit time rather than increasing the energy of each photon.

## The photoelectric effect

The photoelectric effect provided important evidence for the particle-like behavior of electromagnetic radiation.

Einstein's photoelectric equation is

    K_max = h f - phi

where:

- `K_max` is the maximum kinetic energy of an emitted electron.
- `h f` is the photon energy.
- `phi` is the material's work function.

If

    h f < phi

the photon does not have sufficient energy to eject an electron in the simple one-photon model.

The threshold frequency is

    f_threshold = phi / h

and the corresponding threshold wavelength is

    lambda_threshold = c / f_threshold

The script also calculates the stopping voltage. Since one electron accelerated through one volt gains one electron-volt of energy, the numerical value of the maximum kinetic energy in electron-volts corresponds to the stopping voltage in volts for a simple idealized setup.

This experiment distinguishes two quantities that are frequently confused:

**Frequency** determines photon energy.

**Intensity** determines photon flux when the frequency is fixed.

Consequently, increasing the intensity of light below the threshold frequency does not produce photoelectrons in the idealized one-photon description.

## Photons as quantum particles

A photon has energy

    E = h f

and momentum

    p = h / lambda

Since electromagnetic radiation in vacuum satisfies

    c = f lambda

the photon relationships can also be written as

    E = p c

A photon has zero rest mass but carries energy and momentum.

The photoelectric effect demonstrates quantized energy transfer, while Compton scattering provides evidence for photon momentum through the measured wavelength shift of scattered radiation.

## Compton scattering

The Compton wavelength shift is

    Delta lambda = h/(m_e c) (1 - cos(theta))

where:

- `m_e` is the electron mass.
- `theta` is the photon scattering angle.

At zero scattering angle,

    Delta lambda = 0

At 180 degrees, the shift reaches

    Delta lambda = 2 h/(m_e c)

The Compton effect is important because it demonstrates that electromagnetic radiation cannot always be described as a purely continuous classical wave when analyzing energy and momentum transfer.

## de Broglie matter waves

Louis de Broglie proposed that matter should also have an associated wavelength.

The central relation is

    lambda = h / p

where `p` is momentum.

For a slowly moving nonrelativistic particle,

    p = m v

so

    lambda = h / (m v)

The script calculates matter wavelengths for electrons, protons, neutrons, and a macroscopic object.

The reason quantum wave behavior is much easier to observe for microscopic particles is that their de Broglie wavelengths can be comparable to experimentally relevant structures.

For ordinary macroscopic objects, the wavelength is generally extremely small.

## Relativistic momentum

The classical expression

    p = m v

is only appropriate when the speed is sufficiently smaller than the speed of light.

Relativistically,

    p = gamma m v

where

    gamma = 1 / sqrt(1 - v^2/c^2)

The de Broglie relationship remains

    lambda = h / p

but the correct momentum must be used.

The script compares classical and relativistic momentum for electrons traveling at increasing fractions of the speed of light.

At low velocity, the two descriptions are nearly identical.

As the velocity approaches the speed of light, the difference becomes substantial.

This is an important implementation distinction because applying `p = mv` at relativistic speeds produces an incorrect wavelength.

## Double-slit interference

The double-slit experiment is one of the clearest demonstrations of quantum wave behavior.

For two slits separated by distance `d`, the approximate path difference is

    Delta = d sin(theta)

Constructive interference occurs when

    d sin(theta) = m lambda

where `m` is an integer.

Destructive interference occurs when

    d sin(theta) = (m + 1/2) lambda

For small angles and a screen at distance `L`, the position of the bright fringes is approximately

    x_m = m lambda L / d

Therefore the spacing between adjacent bright fringes is approximately

    Delta x = lambda L / d

The script generates an ASCII representation of a two-slit interference pattern.

The model assumes idealized conditions. Real experiments include finite slit width, finite source size, detector resolution, coherence effects, and other experimental factors.

## Single-particle interference

A particularly important feature of quantum experiments is that the interference pattern does not require a large classical wave carrying many particles simultaneously.

Individual quantum particles can be detected one at a time.

Each detector event is localized.

If the experiment is repeated many times, the accumulated distribution can develop an interference pattern.

This distinction is fundamental:

**Individual result:** localized detection event.

**Distribution of many results:** wave-like interference structure.

The script models this using random sampling from an interference probability distribution.

The simulation illustrates the statistical character of quantum measurement. Individual outcomes fluctuate, while the distribution becomes increasingly stable as the number of measurements increases.

## Probability amplitudes

Quantum mechanics does not generally add probabilities directly when alternatives remain coherent.

Instead, it adds probability amplitudes.

If two alternatives have amplitudes `A1` and `A2`, the combined amplitude is

    A = A1 + A2

The probability is then determined by Born's rule:

    P = |A|^2

Therefore,

    P = |A1 + A2|^2

Expanding this expression gives

    P = |A1|^2 + |A2|^2 + 2 Re(A1* A2)

The final term is the interference term.

This term can be positive, negative, or zero depending on the relative phase of the amplitudes.

For constructive interference, the amplitudes reinforce one another.

For destructive interference, they can cancel.

This is one of the most important mathematical differences between classical probability and coherent quantum alternatives.

## Born's rule

The wave function is generally represented by a complex quantity.

For a position-space wave function `psi(x)`, the probability density is

    P(x) = |psi(x)|^2

The wave function itself should not be confused with the probability density.

If the state is normalized, the total probability of finding the particle somewhere in the relevant space is one.

For a discrete set of states,

    sum_i |c_i|^2 = 1

The coefficients `c_i` are probability amplitudes.

Their squared magnitudes are probabilities.

## Relative phase

Complex amplitudes contain both magnitude and phase.

The magnitude affects probability.

The relative phase between amplitudes affects interference.

A global phase has the form

    |psi> -> exp(i gamma) |psi>

Multiplying the complete state by the same phase does not change ordinary measurement probabilities.

A relative phase changes the relationship between components of a superposition and can therefore change measurable interference outcomes.

The script compares states with identical measurement probabilities but different global phases and also demonstrates states with different relative phases.

This distinction is essential in quantum mechanics and quantum information.

## Complementarity

Complementarity describes the fact that different experimental arrangements can reveal different aspects of quantum behavior.

An experiment designed to preserve coherent alternatives can reveal interference.

An experiment that provides usable which-path information can reduce or eliminate interference visibility.

This should not be interpreted as a particle consciously deciding whether to behave as a wave or a particle.

The experimental arrangement determines which observables and relationships can be meaningfully extracted.

Wave-like interference and particle-like path information cannot generally be treated as independent classical properties that can always be observed simultaneously at full resolution.

## Which-path information

The script uses an idealized relation between distinguishability and visibility:

    D^2 + V^2 <= 1

where:

- `D` is path distinguishability.
- `V` is interference visibility.

Visibility is defined as

    V = (I_max - I_min) / (I_max + I_min)

A perfectly visible interference pattern has `V = 1`.

A pattern with no interference contrast has `V = 0`.

The simplified model used in the script takes the equality case

    V = sqrt(1 - D^2)

This is an idealized relation. Real experimental systems can involve additional imperfections and unequal path probabilities.

The physical principle is that acquiring increasingly reliable path information generally reduces the available interference contrast.

## Diffraction

Diffraction occurs when wave behavior interacts with an aperture or periodic structure.

For a single slit of width `a`, the first diffraction minimum approximately satisfies

    a sin(theta) = lambda

For two slits, the interference structure depends on slit separation, while the finite width of each slit also produces a diffraction envelope.

Diffraction is therefore another experimental signature of wave behavior.

The script calculates first-minimum angles for several slit widths and demonstrates that smaller apertures produce larger angular spreading.

## Electron diffraction

Electron diffraction provides direct evidence for matter-wave behavior.

When an electron has a wavelength comparable to atomic spacings in a crystal, the periodic crystal structure can produce diffraction.

For a crystal treated using the Bragg condition,

    n lambda = 2 d sin(theta)

where:

- `n` is the diffraction order.
- `d` is the relevant lattice-plane spacing.
- `theta` is the Bragg angle.

The script calculates electron wavelengths after acceleration through a voltage using the nonrelativistic approximation.

For an electron accelerated through voltage `V`,

    K = eV

and

    p = sqrt(2 m_e K)

so

    lambda = h / sqrt(2 m_e eV)

This approximation becomes increasingly inaccurate at sufficiently high electron energies, where relativistic corrections should be included.

## Wave packets

A pure plane wave has a definite wave number but extends over an unlimited spatial region.

A localized particle-like state can instead be represented by a wave packet.

The script uses a Gaussian-modulated complex wave of the form

    psi(x) = exp(-(x-x0)^2/(4 sigma^2)) exp(i kx)

The Gaussian factor provides localization.

The oscillatory factor contains the phase.

A wave packet therefore combines localization with wave-like phase structure.

A realistic time-dependent wave packet may spread as it evolves, depending on the system's dispersion relation.

## Phase velocity and group velocity

The phase velocity is

    v_phase = omega / k

The group velocity is

    v_group = d omega / d k

Phase velocity describes the propagation of a constant phase point.

Group velocity describes the propagation of a wave packet under appropriate conditions.

For electromagnetic waves in vacuum, both velocities are `c`.

In dispersive systems, they can differ.

The distinction is important because a wave packet is a better model of localization than a single infinite plane wave.

## Fourier analysis and localization

Position and wave-number descriptions are connected by Fourier transformation.

Schematically,

    psi(x) = integral phi(k) exp(i kx) dk

where `phi(k)` represents the wave-number distribution.

A narrow spatial wave packet generally requires a broad range of wave numbers.

A broad spatial state can be represented with a narrower range of wave numbers.

Because

    p = hbar k

a spread in wave number corresponds to a spread in momentum.

The script implements a direct discrete Fourier transform to illustrate this relationship.

The direct implementation is intentionally simple rather than computationally optimal. It has `O(N^2)` computational complexity.

Fast Fourier Transform algorithms can reduce the typical computational cost to approximately `O(N log N)`.

## The uncertainty principle

The position-momentum uncertainty relation is

    Delta x Delta p >= hbar / 2

This is not merely a statement about imperfect measuring instruments.

It follows from the mathematical structure of quantum states and the non-commutation of position and momentum operators.

More generally, for two observables `A` and `B`,

    Delta A Delta B >= 1/2 |< [A,B] >|

where the commutator is

    [A,B] = AB - BA

If two observables do not commute, they cannot generally possess simultaneously sharp values in an arbitrary quantum state.

The Fourier relationship between position and momentum provides an intuitive mathematical interpretation of the position-momentum uncertainty relation.

## Quantum states

A quantum state can be represented as a vector in an abstract state space.

For a simple two-level system,

    |psi> = alpha |0> + beta |1>

Normalization requires

    |alpha|^2 + |beta|^2 = 1

Measurement in the basis consisting of `|0>` and `|1>` gives

    P(0) = |alpha|^2

and

    P(1) = |beta|^2

The script implements a small `QubitState` class to demonstrate normalization, Born-rule probabilities, and repeated measurement.

The qubit example is not intended to reduce all quantum mechanics to two-level systems. It provides a compact representation of superposition, amplitudes, phase, normalization, and measurement.

## Measurement

In an ideal projective measurement, a quantum state can produce one of the observable's allowed eigenvalues.

The corresponding state-update rule can be represented schematically as projection onto the state associated with the observed outcome.

For a simple two-level system,

    alpha |0> + beta |1>

can produce outcome `0` with probability `|alpha|^2` or outcome `1` with probability `|beta|^2`.

After an ideal measurement in this basis, the simplified state-update model places the system in the corresponding basis state.

The phrase **wave-function collapse** is commonly used to describe this state-update aspect of quantum theory.

The physical interpretation of collapse differs among interpretations of quantum mechanics, but the standard mathematical measurement rules provide definite predictions for the situations represented in the script.

## Observables and expectation values

Quantum observables are represented mathematically by operators.

Measurement outcomes correspond to allowed eigenvalues.

For a discrete probability distribution, the expectation value has the form

    <A> = sum_i P_i a_i

where `a_i` is a possible outcome and `P_i` is its probability.

The expectation value does not necessarily equal an outcome obtained in a single measurement.

It represents the average that would be approached by many repeated measurements on identically prepared systems.

The script also calculates variance and standard deviation, which quantify the statistical spread of measurement results.

## Classical probability versus quantum probability

Suppose two alternatives have classical probabilities `P_A` and `P_B`.

For mutually exclusive classical alternatives, the total probability can be obtained by adding probabilities.

Quantum mechanics instead uses amplitudes for coherent alternatives.

If the amplitudes are `A` and `B`, the probability is

    |A + B|^2

rather than simply

    |A|^2 + |B|^2

The difference is the interference term.

This distinction explains why interference can occur even though individual detector events remain localized.

When coherence is lost, the cross terms may cease to contribute to observable interference, producing statistics that resemble classical probability addition.

## Decoherence

Decoherence occurs when a quantum system becomes correlated with environmental degrees of freedom.

The environment can effectively acquire information about different quantum alternatives.

As a result, relative phase information between those alternatives becomes inaccessible for local observations, and interference can become strongly suppressed.

Decoherence is important in understanding why macroscopic systems usually exhibit classical-looking behavior.

Decoherence should not automatically be identified with every meaning of wave-function collapse.

Decoherence describes a physical mechanism for suppression of observable interference through environmental correlations. Different interpretations of quantum mechanics provide different conceptual accounts of measurement and collapse.

## Entanglement and wave-particle duality

Entanglement is related to quantum superposition but is not identical to wave-particle duality.

A simple two-particle entangled state is

    |Psi> = (|00> + |11>) / sqrt(2)

The two particles cannot be represented as independent single-particle states whose tensor product reproduces the complete state.

Measurements of the two subsystems can exhibit correlations that have no equivalent description as independent classical variables under the relevant assumptions.

Wave-particle duality concerns the appearance of wave-like and particle-like phenomena.

Entanglement concerns the structure of composite quantum states and correlations between subsystems.

The concepts are connected through the general framework of quantum mechanics but should not be treated as interchangeable.

## Classical limit

Macroscopic objects usually have extremely small de Broglie wavelengths relative to ordinary experimental length scales.

For a particle with momentum `p`,

    lambda = h / p

As mass or momentum increases, the wavelength becomes smaller.

This makes direct interference effects increasingly difficult to resolve.

Small wavelength alone is not the complete explanation for classical behavior.

The transition toward classical behavior also involves:

- action scales much larger than `hbar`
- environmental decoherence
- many degrees of freedom
- finite measurement resolution
- coarse-grained observations
- suppression of observable phase relationships

The script illustrates the action scale using the dimensionless quantity

    S / hbar

Quantum phases can contain terms of the form

    exp(iS/hbar)

When the action is very large compared with `hbar`, phase variations can become extremely rapid. Interference among many contributions can then strongly favor paths near stationary action, providing an important connection between quantum and classical mechanics.

## Wave-particle duality as a unified framework

The major equations in the script are not independent facts.

For electromagnetic radiation,

    E = h f

    p = h / lambda

    E = p c

For matter,

    lambda = h / p

Using

    p = hbar k

and

    E = hbar omega

the wave and particle descriptions become connected through the same quantum constants.

The quantum state introduces amplitudes whose magnitudes and phases determine measurement probabilities.

A superposition has the form

    psi = c1 psi1 + c2 psi2

and interference arises because

    P = |psi|^2

The same framework therefore connects energy, momentum, wavelength, phase, interference, probability, localization, and measurement.

## Experimental design relationships

For an ideal double-slit experiment, the approximate fringe spacing is

    Delta x = lambda L / d

where:

- `lambda` is wavelength.
- `L` is screen distance.
- `d` is slit separation.

Increasing wavelength increases fringe spacing.

Increasing screen distance increases fringe spacing.

Increasing slit separation decreases fringe spacing.

These relationships are useful when determining whether an interference pattern will be experimentally resolvable.

The ideal equation assumes small angles and does not account for every property of a real optical or matter-wave system.

## Edge cases and exceptions

Several assumptions in simplified quantum calculations have boundaries.

A wavelength must be positive.

A momentum magnitude must be positive when calculating a positive scalar wavelength.

The speed of a massive relativistic particle must satisfy

    0 <= v < c

The classical momentum formula is not valid as a relativistic expression.

A quantum probability distribution must be normalized.

A wave function is not directly the probability distribution. The relevant probability density is obtained from its squared magnitude.

Interference is not guaranteed in every experiment. Coherence and the measurement arrangement matter.

Real experiments can contain detector inefficiency, environmental interactions, imperfect sources, finite resolution, background noise, and other effects that are not represented in an ideal mathematical model.

## Common misconceptions

### "An electron is literally both a tiny ball and a classical wave"

Quantum objects are not required to fit either classical category. Wave and particle language describes experimentally observable aspects of quantum behavior.

### "The wave function is simply a classical material wave"

A quantum wave function is a mathematical state description. Its interpretation depends on the physical system and representation. In ordinary nonrelativistic position-space quantum mechanics, its squared magnitude gives a position probability density.

### "A particle detector sees half a particle at each slit"

A detector records localized measurement events. The interference pattern emerges statistically from the probability distribution generated by quantum amplitudes.

### "Higher light intensity always makes photoelectrons more energetic"

For fixed frequency, increasing intensity mainly increases photon flux. The energy of each photon remains `hf`.

### "The uncertainty principle only describes poor instruments"

The position-momentum uncertainty relation is a mathematical property of quantum states and non-commuting observables.

### "Quantum randomness means quantum mechanics has no precise mathematical rules"

Quantum mechanics provides precise state evolution, operators, probability amplitudes, and probability distributions. The probabilistic character concerns measurement outcomes.

### "Wave-particle duality means an object physically changes from wave to particle"

The more useful description is that quantum systems require a framework that can account for wave-like propagation and particle-like measurement outcomes.

## Real-world applications

### Electron microscopy

Electrons can have wavelengths far smaller than visible-light wavelengths. This allows electron microscopes to resolve structures that are inaccessible to ordinary optical microscopy.

### Electron diffraction

Electron diffraction uses the wave nature of electrons to investigate crystal structures and material properties.

### Neutron diffraction

Neutrons can also behave as matter waves. Their wavelengths can be selected to investigate crystalline and magnetic structures.

### Scanning tunneling microscopy

Quantum tunneling is a direct consequence of quantum wave behavior. The tunneling current in scanning tunneling microscopy is sensitive to surface structure at very small scales.

### Semiconductor physics

Quantum states, energy levels, wave functions, tunneling, and carrier behavior are fundamental to nanoscale semiconductor devices.

### Lasers

Lasers depend on quantized energy levels, stimulated emission, population dynamics, and coherent electromagnetic radiation.

### Quantum information

Superposition, relative phase, measurement, and entanglement are central concepts in quantum information processing.

## Implementation structure of the Python script

The script is organized as a progressive study file rather than as a collection of unrelated snippets.

Fundamental sections establish physical constants and basic relationships.

Mathematical sections implement:

- photon energy
- wavelength and frequency conversion
- classical and relativistic momentum
- de Broglie wavelength
- Bragg diffraction
- Compton wavelength shift
- phase and group velocity
- Gaussian wave packets
- discrete Fourier transformation
- expectation values
- variance
- probability normalization

Simulation sections implement:

- double-slit interference
- single-particle detection
- probability-amplitude interference
- Poisson-like measurement statistics
- qubit measurement
- relative phase
- idealized complementarity
- decoherence models

Object-oriented structure is demonstrated with `QubitState` and `DoubleSlitExperiment`.

The code uses dataclasses where a compact representation of a physical state or experiment is useful.

## Error handling

The script validates physically meaningful input ranges.

Examples include rejection of:

- zero or negative wavelengths
- non-positive momentum
- negative mass
- invalid relativistic velocities
- probabilities outside their allowed ranges
- invalid diffraction orders
- physically impossible Bragg angles
- zero-norm quantum states
- improperly normalized probability distributions

This is important because numerical software should not silently produce physically meaningless values.

Input validation is part of scientific correctness, not merely a programming convenience.

## Numerical considerations

The script uses Python's standard library to remain self-contained.

The direct discrete Fourier transform intentionally uses the mathematical definition directly:

    X_k = sum_n x_n exp(-2 pi i k n / N)

Its computational complexity is `O(N^2)`.

This is suitable for a small educational demonstration but becomes inefficient for large datasets.

An FFT algorithm can typically reduce the computational complexity to `O(N log N)`.

Monte Carlo simulations have statistical uncertainty. Increasing the number of simulated measurements generally makes the empirical distribution approach the theoretical probability distribution.

ASCII visualizations are also intentionally low resolution. They are useful for conceptual demonstrations but do not represent the spatial resolution of a scientific plotting system.

## Physical model limitations

The script contains idealized models.

The double-slit interference calculations assume simplified geometry and small-angle approximations.

The electron acceleration wavelength calculation uses nonrelativistic kinetic energy.

Real electron diffraction at high energies requires relativistic treatment.

Real slits have finite widths and therefore produce diffraction envelopes.

Real sources may have finite coherence lengths.

Real detectors have finite efficiency and spatial resolution.

Environmental interactions can cause decoherence.

Many realistic systems require more advanced mathematical frameworks, including full three-dimensional quantum mechanics, spin, relativistic quantum mechanics, many-body quantum theory, or quantum field theory.

The simplified models are therefore appropriate for learning the relationships but should not be interpreted as complete descriptions of every physical experiment.

## Security considerations for scientific implementations

The educational script does not access networks, execute operating-system commands, read arbitrary files, or execute user-provided Python expressions.

This keeps its basic execution environment simple.

Scientific software becomes more security-sensitive when it accepts external input, evaluates formulas dynamically, loads serialized objects, reads untrusted files, or exposes calculations through a network service.

Unrestricted dynamic execution such as arbitrary `eval()` or `exec()` should not be used with untrusted mathematical expressions. A restricted expression parser or explicitly defined mathematical grammar is safer.

## Debugging and scientific validation

Scientific programming requires two kinds of correctness.

The first is software correctness.

The second is physical correctness.

The script includes assertions for several relationships:

    f lambda = c

    |alpha|^2 + |beta|^2 = 1

    sum(P_i) = 1

and

    Delta lambda(theta=0) = 0

It also checks that invalid physical inputs are rejected.

Useful validation techniques for quantum-physics calculations include:

- dimensional analysis
- limiting cases
- normalization checks
- symmetry checks
- conservation laws
- comparison with analytical relationships
- controlled parameter changes
- independent numerical calculations
- repeated statistical trials

For example, a probability distribution that does not sum to one should be treated as a modeling or implementation error rather than simply normalized without investigation.

## Testing

The script includes lightweight automated tests using Python assertions.

The tests cover:

- electromagnetic wavelength-frequency conversion
- photon energy
- de Broglie wavelength
- probability normalization
- quantum-state normalization
- expectation values
- Compton scattering limits
- invalid input handling

Testing physical software is particularly important because a program can execute without a Python error while still implementing the wrong physical equation.

A reliable scientific implementation therefore requires validation of both the code and the underlying model.

## Performance considerations

The most computationally significant demonstration is the direct discrete Fourier transform, which scales as `O(N^2)`.

The Monte Carlo measurement simulation scales approximately linearly with the number of simulated events.

The interference pattern generation scales approximately linearly with the number of screen positions.

For small educational examples, these implementations are adequate and transparent.

For large scientific datasets, optimized numerical algorithms, efficient array operations, parallel computation, and validated scientific libraries would generally be more appropriate.

## Important distinctions

### Wave versus wave function

A classical wave is typically a physical field or oscillatory quantity.

A quantum wave function is a mathematical state description whose squared magnitude gives probability density in appropriate representations.

### Probability versus probability amplitude

Probability is a real non-negative quantity.

A quantum probability amplitude can be complex.

Amplitudes are added first when alternatives remain coherent. Probabilities are then obtained from squared magnitudes.

### Photon energy versus beam intensity

Photon energy depends on frequency.

Beam intensity can change the rate at which photons arrive.

These quantities should not be conflated.

### Global phase versus relative phase

Global phase does not affect ordinary measurement probabilities.

Relative phase can affect interference and is physically observable through suitable measurements.

### Wave-particle duality versus entanglement

Wave-particle duality describes complementary wave-like and particle-like aspects of quantum phenomena.

Entanglement describes non-factorizable correlations within composite quantum states.

### Decoherence versus collapse

Decoherence describes environmental suppression of observable interference.

Collapse is commonly used to describe the state update associated with measurement in standard formulations.

The two concepts are related but not identical.

### Classical momentum versus relativistic momentum

The expression `p = mv` is a low-speed approximation.

At high velocity,

    p = gamma m v

must be used.

### Plane wave versus localized wave packet

A plane wave has a well-defined wave number but is spatially extended.

A wave packet combines multiple wave numbers and can be localized.

## Conceptual progression represented by the script

The Python implementation follows a deliberate conceptual sequence.

Classical wave behavior establishes wavelength, frequency, phase, and propagation.

Planck's relation introduces quantized electromagnetic energy.

The photoelectric effect demonstrates particle-like energy transfer.

de Broglie's relation extends wave behavior to matter.

The double-slit experiment demonstrates interference.

Single-particle simulation separates localized detection events from the wave-like statistical distribution.

Probability amplitudes explain why interference arises mathematically.

Complementarity and which-path information connect interference to measurement arrangements.

Wave packets and Fourier analysis connect localization with momentum spread.

The uncertainty principle formalizes this relationship.

Quantum-state examples introduce superposition, normalization, relative phase, and measurement.

Decoherence connects quantum behavior with the emergence of classical-looking statistics.

Entanglement demonstrates a related but distinct feature of composite quantum states.

The final sections address experimental applications, numerical limitations, validation, performance, and physical edge cases.

## Key equations represented in the script

Electromagnetic wave relation:

    c = f lambda

Photon energy:

    E = h f

Photon momentum:

    p = h / lambda

Photon energy-momentum relation:

    E = p c

de Broglie wavelength:

    lambda = h / p

Nonrelativistic momentum:

    p = m v

Relativistic momentum:

    p = gamma m v

Lorentz factor:

    gamma = 1 / sqrt(1 - v^2/c^2)

Photoelectric equation:

    K_max = h f - phi

Compton shift:

    Delta lambda = h/(m_e c)(1 - cos(theta))

Bragg diffraction:

    n lambda = 2 d sin(theta)

Single-slit first minimum:

    a sin(theta) = lambda

Two-slit constructive interference:

    d sin(theta) = m lambda

Two-slit destructive interference:

    d sin(theta) = (m + 1/2) lambda

Approximate fringe spacing:

    Delta x = lambda L / d

Quantum probability:

    P = |psi|^2

Two-path amplitude rule:

    P = |A1 + A2|^2

Position-momentum uncertainty:

    Delta x Delta p >= hbar / 2

General uncertainty relation:

    Delta A Delta B >= 1/2 |< [A,B] >|

Qubit normalization:

    |alpha|^2 + |beta|^2 = 1

Qubit measurement probabilities:

    P(0) = |alpha|^2

    P(1) = |beta|^2

Duality relation in an ideal balanced two-path model:

    D^2 + V^2 <= 1

These equations form a connected mathematical framework for understanding why quantum systems exhibit phenomena that cannot be represented completely by classical particle or classical wave models.
