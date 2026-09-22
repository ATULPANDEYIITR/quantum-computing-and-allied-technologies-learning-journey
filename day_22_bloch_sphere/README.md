# Bloch Sphere

## Topic introduction

The Bloch sphere is a geometric representation of the state of a single qubit. A classical bit has two discrete values, 0 and 1. A qubit can occupy the computational basis states `|0>` and `|1>`, as well as coherent superpositions of those states. The Bloch sphere converts the mathematical description of a single-qubit state into a three-dimensional geometric representation that makes state preparation, phase, measurement, and single-qubit gate operations easier to understand.

A normalized pure qubit can be written as `|ψ> = α|0> + β|1>`, where `α` and `β` are complex probability amplitudes satisfying `|α|² + |β|² = 1`. A global phase does not change the physical state, so the two complex amplitudes contain fewer independent physical parameters than their raw representation suggests. After removing the physically irrelevant global phase, every pure single-qubit state can be described by two real angles, `θ` and `φ`.

The canonical Bloch-sphere representation is `|ψ> = cos(θ/2)|0> + exp(iφ)sin(θ/2)|1>`. The corresponding Bloch vector is `r = (x, y, z)`, where `x = sin(θ)cos(φ)`, `y = sin(θ)sin(φ)`, and `z = cos(θ)`. Pure states have a vector length of one and therefore lie on the surface of the sphere. Mixed states have a vector length less than one and occupy points inside the sphere.

The three implementations in this study approach the subject from different technical perspectives. Python provides a compact mathematical simulator suitable for studying the equations and transformations. JavaScript implements the same underlying mathematics with explicit complex-number and matrix classes and also produces an SVG representation. C++ develops an industry-style single-qubit calibration experiment involving gate sequences, measurement statistics, tomography, density matrices, noise, validation, and performance-conscious standard-library implementation.

## Fundamental concepts

### Qubits

A qubit is a two-level quantum system. Its computational basis consists of `|0>` and `|1>`. A pure state has the form:

`|ψ> = α|0> + β|1>`

with the normalization condition:

`|α|² + |β|² = 1`

The quantities `|α|²` and `|β|²` are probabilities for measurement in the computational basis.

The Python implementation represents the state as a two-element complex vector. The JavaScript implementation creates a `Complex` class because standard JavaScript numbers do not provide native complex arithmetic. The C++ implementation uses `std::complex<double>` and `std::array` for a compact, statically sized representation.

The basis state `|0>` corresponds to the Bloch vector `(0, 0, 1)`, while `|1>` corresponds to `(0, 0, -1)`. These are conventionally called the north and south poles.

### Bloch coordinates

For a pure state with amplitudes `α` and `β`, the Cartesian coordinates are:

`x = 2 Re(α*β)`

`y = 2 Im(α*β)`

`z = |α|² - |β|²`

The notation `α*` means the complex conjugate of `α`.

The coordinates have direct physical interpretations. The `z` coordinate determines computational-basis measurement probabilities:

`P(0) = (1 + z)/2`

`P(1) = (1 - z)/2`

The transverse coordinates `x` and `y` encode the coherence and relative phase between the two computational-basis amplitudes.

The Bloch vector is not an additional physical degree of freedom. It is another representation of the same single-qubit state.

### Spherical coordinates

A pure state can be parameterized using two angles:

`θ ∈ [0, π]`

`φ ∈ [0, 2π)`

The state is:

`|ψ> = cos(θ/2)|0> + exp(iφ)sin(θ/2)|1>`

The corresponding Cartesian coordinates are:

`x = sin(θ)cos(φ)`

`y = sin(θ)sin(φ)`

`z = cos(θ)`

The Python, JavaScript, and C++ implementations all construct states from these two angles.

The half-angle appearing in the state amplitudes is important. A rotation of the Bloch vector through angle `θ` corresponds to amplitudes involving `θ/2`. This is one of the characteristic features of the spin-1/2 mathematical structure underlying a qubit.

## Density matrices and mixed states

A state vector describes a pure quantum state. A more general representation is the density matrix:

`ρ = |ψ><ψ|`

For a pure qubit,

`ρ = [[|α|², αβ*], [α*β, |β|²]]`

The density matrix is especially useful because it can also represent statistical mixtures of quantum states.

Every single-qubit density matrix can be written as:

`ρ = 1/2(I + xX + yY + zZ)`

where `I` is the identity matrix and `X`, `Y`, and `Z` are the Pauli matrices.

The Python function `density_matrix_from_bloch()` implements this expression directly. The JavaScript version follows the same construction through matrix arithmetic. The C++ case study uses the representation to move between pure-state vectors and density matrices.

A valid Bloch vector must satisfy:

`x² + y² + z² ≤ 1`

A pure state satisfies equality. A mixed state satisfies a strict inequality.

The point `(0, 0, 0)` represents the maximally mixed single-qubit state:

`ρ = I/2`

This state has no preferred Bloch direction and has purity `1/2`.

## Pauli matrices and expectation values

The Pauli matrices are:

`X = [[0,1],[1,0]]`

`Y = [[0,-i],[i,0]]`

`Z = [[1,0],[0,-1]]`

They form a natural operator basis for single-qubit states and observables.

The Bloch coordinates can be recovered directly from expectation values:

`x = Tr(ρX)`

`y = Tr(ρY)`

`z = Tr(ρZ)`

This relationship is demonstrated in the Python and C++ implementations and is fundamental to quantum state tomography.

The Pauli matrices also correspond to rotations around the three Cartesian axes. Their role is therefore both algebraic and geometric.

For a computational-basis measurement, the observable is associated with `Z`. A state at the north pole has a `Z` expectation value of `+1`, while a state at the south pole has an expectation value of `-1`.

A state on the equator has `z = 0`, so its computational-basis measurement probabilities are exactly `1/2` and `1/2`. Such a state can still contain well-defined phase information represented by its position around the equator.

## Quantum gates as rotations

Single-qubit quantum gates are represented by unitary matrices. A matrix `U` is unitary when:

`U†U = I`

A state evolves according to:

`|ψ'> = U|ψ>`

In the density-matrix representation:

`ρ' = UρU†`

The Python program explicitly checks the unitarity of several gates. The C++ program performs similar validation for the Pauli matrices, Hadamard gate, phase gate, and continuous rotation operators.

### X gate

The Pauli-X gate is:

`X = [[0,1],[1,0]]`

It exchanges `|0>` and `|1>`. Geometrically, it corresponds to a rotation of the Bloch vector by π radians around the x axis, up to the physically irrelevant global phase associated with the SU(2) representation.

### Y gate

The Pauli-Y gate is:

`Y = [[0,-i],[i,0]]`

It exchanges the basis amplitudes while introducing phase factors. Geometrically, it represents a π rotation around the y axis.

### Z gate

The Pauli-Z gate is:

`Z = [[1,0],[0,-1]]`

It leaves `|0>` unchanged and adds a minus sign to `|1>`. It therefore changes relative phase without changing computational-basis probabilities.

On the Bloch sphere, the Z operation is a π rotation around the z axis.

### Hadamard gate

The Hadamard gate is:

`H = 1/sqrt(2) [[1,1],[1,-1]]`

It transforms:

`|0>` into `|+>`

and

`|1>` into `|->`

where:

`|+> = (|0> + |1>)/sqrt(2)`

`|-> = (|0> - |1>)/sqrt(2)`

The Bloch vectors of `|+>` and `|->` lie at opposite points on the x axis.

### S and T gates

The phase gate is:

`S = diag(1, i)`

The T gate is:

`T = diag(1, exp(iπ/4))`

These gates alter relative phase and can therefore rotate a state around the z axis.

The JavaScript implementation explicitly demonstrates how phase gates move a state around the equator.

## Continuous rotation operators

The standard rotation operators are:

`Rx(θ) = exp(-iθX/2)`

`Ry(θ) = exp(-iθY/2)`

`Rz(θ) = exp(-iθZ/2)`

Their explicit matrix forms include:

`Rx(θ) = [[cos(θ/2), -i sin(θ/2)], [-i sin(θ/2), cos(θ/2)]]`

`Ry(θ) = [[cos(θ/2), -sin(θ/2)], [sin(θ/2), cos(θ/2)]]`

`Rz(θ) = [[exp(-iθ/2), 0], [0, exp(iθ/2)]]`

These operations provide a direct connection between matrix-based quantum computation and three-dimensional geometry.

The Python implementation uses these operators to trace points around the Bloch sphere. The JavaScript implementation demonstrates continuous rotations and the C++ calibration experiment uses a sequence of rotations as if they were calibrated control pulses.

The Bloch-vector rotation is a real three-dimensional rotation even though the underlying state transformation occurs in a complex two-dimensional Hilbert space.

## Global phase and relative phase

A global phase multiplies the entire state by the same complex phase:

`|ψ'> = exp(iγ)|ψ>`

This changes the mathematical vector but not any physical prediction. Measurement probabilities remain unchanged, and the Bloch vector remains the same.

The Python and JavaScript implementations explicitly compare an original state with a globally phased version and calculate fidelity between them.

Relative phase is different. Consider:

`|ψ> = (|0> + exp(iφ)|1>)/sqrt(2)`

Changing `φ` changes the position around the equator. The phase is therefore physically meaningful when it is relative between components.

This distinction is essential when interpreting quantum interference. The absolute phase of an isolated state is not directly observable, while relative phase can influence the result of subsequent operations and measurements.

## Measurement and state collapse

For a computational-basis measurement:

`P(0) = |α|²`

`P(1) = |β|²`

In Bloch coordinates:

`P(0) = (1 + z)/2`

`P(1) = (1 - z)/2`

After measurement, the state is projected onto the corresponding measurement eigenstate. If the result is zero, the post-measurement state is `|0>`. If the result is one, it is `|1>`.

The Python, JavaScript, and C++ implementations simulate repeated measurements. Because measurement is probabilistic, the empirical frequencies approach the theoretical probabilities as the number of shots increases.

The C++ case study performs a 10,000-shot measurement experiment and compares the observed frequencies with the theoretical probabilities.

A common mistake is to interpret a single measurement as evidence that the underlying probability was deterministic. Quantum measurement produces individual outcomes, while the probability distribution is inferred statistically from repeated trials.

## Noise and mixed states

Real quantum systems interact with their environment. Noise makes the density-matrix representation particularly important because the resulting state may become mixed.

The Bloch-sphere picture provides an intuitive interpretation. Ideal unitary evolution moves a pure state along the surface. Noise can reduce the length of the Bloch vector and move the state toward the center.

### Bit-flip noise

A bit-flip channel can be written as:

`ρ' = (1-p)ρ + pXρX`

The channel randomly applies an X operation with probability `p`.

### Phase-flip noise

A phase-flip channel is:

`ρ' = (1-p)ρ + pZρZ`

It modifies phase coherence and affects the transverse components of the Bloch vector.

### Depolarizing noise

The implementation uses:

`ρ' = (1-p)ρ + p/3(XρX + YρY + ZρZ)`

This symmetric channel reduces the Bloch-vector magnitude and models isotropic loss of information in a simplified single-qubit setting.

The precise physical model of a real device can be more complicated. A depolarizing channel is useful for mathematical experiments but should not automatically be treated as an exact model of a particular hardware platform.

## Purity

Purity is defined as:

`Tr(ρ²)`

For a pure state:

`Tr(ρ²) = 1`

For the maximally mixed qubit:

`Tr(ρ²) = 1/2`

For a single qubit, the Bloch-vector length gives an equivalent expression:

`Tr(ρ²) = (1 + |r|²)/2`

Therefore, shrinking the Bloch vector corresponds directly to reducing purity.

The implementations calculate purity after applying noise to demonstrate this relationship numerically.

## Fidelity

For two pure states, fidelity can be expressed as:

`F = |<ψ|φ>|²`

A value of one means the states are physically identical up to global phase. A value near zero indicates orthogonality.

The implementations use pure-state fidelity for gate-sequence validation and global-phase demonstrations.

For a mixed state and a pure target state, the relevant expression is:

`F(ρ, |ψ>) = <ψ|ρ|ψ>`

More general mixed-state fidelity uses the Uhlmann expression, which is not required for the single-qubit pure-target examples implemented here.

## Python implementation

The Python implementation is primarily a mathematical study environment. It starts with low-level vector and matrix operations so that the later quantum concepts do not depend on a specialized quantum-computing package.

The `Complex` type is provided by Python itself, which makes complex arithmetic concise. The script implements matrix multiplication, conjugate transpose, outer products, matrix addition, and scalar multiplication directly.

The `BlochVector` class stores the three Cartesian coordinates and provides methods for computing the vector magnitude, testing whether the vector is physically valid, identifying pure states, and recovering spherical coordinates.

The `state_from_bloch()` function implements the canonical spherical parameterization. `bloch_from_state()` calculates Cartesian coordinates directly from amplitudes. The round-trip validation tests confirm that converting a pure state into Bloch coordinates and reconstructing its density matrix preserves the original state representation up to numerical precision.

The Python simulator also includes unitary evolution, measurement, density matrices, noise channels, fidelity, purity, tomography, and a small gate-sequence simulator. The `QubitSimulator` class records a trajectory of operations and Bloch vectors, allowing a sequence of gates to be inspected as a geometric path.

The tomography example is particularly important. It does not assume that the Bloch coordinates are directly observable. Instead, it generates simulated measurement outcomes and estimates the expectation values of X, Y, and Z. This models the statistical nature of quantum state reconstruction.

## JavaScript implementation

The JavaScript implementation uses an explicit `Complex` class. JavaScript's standard numeric type is a real floating-point number, so complex arithmetic must be represented manually when no external mathematical library is used.

The `Complex` class supports addition, subtraction, multiplication, scaling, conjugation, magnitude, and polar-coordinate construction. This provides the mathematical foundation required by the qubit calculations.

The JavaScript implementation mirrors the central Bloch-sphere operations while emphasizing application-level execution. Matrix and vector operations are represented using arrays, and the `QubitSimulator` class provides an object-oriented interface for applying gates and recording the state trajectory.

A meaningful JavaScript-specific feature is the SVG visualization function. The `createBlochSphereSVG()` function produces a standalone SVG representation containing the sphere outline, axes, labels, and a vector pointing to the selected Bloch coordinate. The projection is deliberately educational rather than a full three-dimensional renderer.

The implementation can therefore serve both as a Node.js numerical program and as a source of SVG content suitable for browser-based visualization.

## C++ case study

The C++ program models a laboratory-style single-qubit calibration experiment.

The scenario begins with a prepared qubit whose state is specified by spherical Bloch coordinates. A sequence of calibrated rotations, a Hadamard operation, and a phase operation is then applied.

The `QubitCalibrationExperiment` class stores the current state and a trajectory containing the operation name and corresponding Bloch vector. This separates experiment control from the mathematical primitives used by the simulator.

The case study proceeds through several stages.

First, the system prepares a nontrivial pure state. Second, it applies a gate sequence and records the resulting trajectory. Third, it converts the final state into a density matrix. Fourth, it calculates theoretical measurement probabilities. Fifth, it performs 10,000 simulated measurements and reports empirical frequencies. Sixth, it performs state tomography using X, Y, and Z expectation values. Seventh, it introduces depolarizing noise. Eighth, it models phase noise. Ninth, it calculates fidelity against an independently constructed ideal sequence.

The design uses `std::array` for fixed-size two-component vectors and 2×2 matrices. This is appropriate for a single-qubit educational implementation because the dimensions are known at compile time.

The implementation also uses `std::complex<double>` for complex amplitudes and `std::mt19937` for deterministic, reproducible pseudorandom simulation when initialized with a fixed seed.

## State tomography

Quantum state tomography estimates an unknown quantum state using measurement data.

For a single qubit, the three Pauli expectation values are sufficient to reconstruct the Bloch vector:

`x = <X>`

`y = <Y>`

`z = <Z>`

For an observable with outcomes `+1` and `-1`:

`<P> = P(+1) - P(-1)`

and:

`P(+1) = (1 + <P>)/2`

The Python and C++ implementations simulate finite-shot measurements. The estimated coordinates are therefore not expected to exactly equal the theoretical values.

Increasing the number of shots generally reduces statistical uncertainty. The error is not eliminated by the mathematical representation because the measurements themselves are probabilistic.

Tomography also has experimental limitations. Real systems contain measurement errors, calibration errors, drift, state-preparation errors, gate errors, and environmental noise. The implementations model only the statistical component.

## Important distinctions and comparisons

| Concept | Meaning |
|---|---|
| `|0>` | North pole of the Bloch sphere |
| `|1>` | South pole |
| `|+>` | Positive x-axis |
| `|->` | Negative x-axis |
| Pure state | Bloch-vector magnitude equals one |
| Mixed state | Bloch-vector magnitude is less than one |
| Global phase | Common phase factor with no physical effect on the isolated state |
| Relative phase | Phase difference that can affect interference and Bloch position |
| Unitary evolution | Reversible state evolution preserving purity |
| Measurement | Probabilistic projection associated with an observable |
| Density matrix | Representation capable of describing pure and mixed states |
| Purity | `Tr(ρ²)` |
| Fidelity | Quantitative similarity between quantum states |

A state vector is often the most convenient representation for a pure state. A density matrix is more general because it represents both pure states and statistical mixtures.

The Bloch sphere is especially useful for a single qubit. It does not scale into an equally simple three-dimensional picture for arbitrary multi-qubit states. A system of `n` qubits has a Hilbert-space dimension of `2^n`, and its general state contains exponentially more information.

## Edge cases

### Zero vector

`[0, 0]` is not a valid quantum state because it cannot be normalized. All three implementations reject this condition.

### Invalid Bloch vectors

A point such as `(1.2, 0, 0)` is outside the physical Bloch ball. It cannot represent a valid qubit density matrix. The implementations explicitly validate this condition.

### Numerical rounding

Floating-point arithmetic can produce values slightly outside expected mathematical boundaries, such as `1.0000000000000002`. Probability calculations are therefore clamped where appropriate, and validation uses tolerances instead of exact floating-point equality.

### Maximally mixed state

The origin `(0, 0, 0)` is valid. It represents the maximally mixed state and is not a pure state.

### Zero Bloch-vector direction

Spherical coordinates are not physically meaningful for the origin because there is no direction. The implementations return a conventional `(0, 0)` angular representation for this numerical edge case.

### Measurement collapse

After a computational-basis measurement, the simulated state is replaced by `|0>` or `|1>`. Subsequent measurements therefore return the same basis outcome unless another operation changes the state.

## Common mistakes

A frequent mistake is assuming that a qubit is simply a classical random bit. A superposition is not equivalent to an ordinary classical probability distribution because its complex amplitudes contain phase information and can interfere under later operations.

Another common mistake is treating `α` and `β` as ordinary probabilities. They are amplitudes. The probabilities are obtained by taking squared magnitudes.

Another mistake is forgetting normalization. A valid state vector must satisfy `|α|² + |β|² = 1`.

It is also incorrect to interpret every point inside the sphere as a pure state. Only the surface represents pure states. Interior points represent mixed states.

A further mistake is assuming that changing the global phase changes the physical state. Multiplying the entire state by the same phase factor leaves all physical predictions unchanged.

It is also important not to confuse relative phase with global phase. Relative phase changes the Bloch position and can influence interference.

Finally, the Bloch sphere should not be treated as a complete geometric representation of an arbitrary quantum computer. It provides a complete visualization for one qubit, while multi-qubit systems require much higher-dimensional mathematical descriptions.

## Exceptions and limitations

The Bloch-sphere representation is exact for a single qubit. Its simplicity comes from the fact that a 2×2 density matrix can be decomposed using the identity and the three Pauli matrices.

For multiple qubits, the state space grows exponentially with the number of qubits. A two-qubit pure state already requires four complex amplitudes before accounting for normalization and global phase. Entanglement also prevents the complete state of a multi-qubit system from being represented as independent Bloch vectors for each qubit.

The implementations are numerical educational simulators rather than physical-device controllers. They do not model hardware-specific pulse distortions, readout calibration matrices, crosstalk, leakage outside the computational subspace, thermal relaxation times, frequency drift, or detailed open-system dynamics.

The depolarizing and phase-flip channels are simplified noise models. Real quantum devices may require models such as amplitude damping, generalized amplitude damping, coherent errors, correlated noise, non-Markovian processes, or experimentally measured noise channels.

The SVG projection in JavaScript is also a simplified visualization. It does not implement physically accurate three-dimensional rendering, hidden-surface removal, perspective, lighting, or interactive camera control.

## Best practices

Keep state normalization explicit when accepting arbitrary numerical state vectors.

Use density matrices when mixed states or noise need to be represented.

Use unitary matrices for ideal closed-system gate evolution and verify `U†U = I` when implementing new gates.

Use tolerances when comparing floating-point values.

Separate mathematical operations from experiment or application logic. The C++ `QubitCalibrationExperiment` class demonstrates this separation.

Record random seeds when reproducibility is important in simulations.

Distinguish exact theoretical probabilities from finite-shot experimental estimates.

Use Bloch coordinates for geometric interpretation while retaining the underlying state vector or density matrix for numerical calculations.

Validate physical constraints before operating on a state. In particular, probabilities must remain within `[0, 1]`, state vectors must be normalizable, and density matrices must correspond to physically valid states.

## Performance considerations

A single-qubit state contains only two complex amplitudes, and its operators are 2×2 matrices. Consequently, the operations implemented here are computationally inexpensive.

The dominant cost in repeated measurement and tomography examples is proportional to the number of simulated shots. If `N` measurement shots are generated, the simulation requires `O(N)` measurement operations.

Matrix multiplication for the fixed 2×2 matrices used here has constant cost. In a general `d × d` matrix representation, conventional matrix multiplication has `O(d³)` time complexity, although optimized algorithms and hardware can reduce practical costs.

For an `n`-qubit state-vector simulator, the state dimension is `2^n`. Storing the state therefore requires memory proportional to `O(2^n)`. Applying a dense full-system matrix can be substantially more expensive, while local gates can be implemented much more efficiently using tensor-product structure.

The C++ implementation benefits from fixed-size containers and avoids external dynamic matrix frameworks because the problem dimension is known.

## Security and reliability considerations

The Bloch sphere itself is a mathematical representation and does not introduce a conventional security boundary. Security becomes relevant when quantum-state simulation is incorporated into a larger system.

Random measurement generation should use a suitable random source for the intended application. The pseudorandom generators used in these educational simulations are designed for reproducibility rather than cryptographic security.

Numerical simulators should validate input states and parameters to avoid propagating invalid physical values through later calculations.

When quantum control software interfaces with real hardware, malformed commands, invalid pulse parameters, calibration corruption, and unauthorized control access can become operational security concerns. Those concerns are outside the mathematical simulator implemented here but are important when moving from simulation to physical infrastructure.

## Implementation considerations

The Python implementation prioritizes mathematical clarity and rapid experimentation. Python's built-in complex arithmetic makes the formulas concise, while lists provide enough structure for a small single-qubit simulator.

The JavaScript implementation demonstrates how the same mathematics can be represented in a language where complex numbers are not built into the standard numeric type. Its SVG generator provides a direct connection between numerical state representation and browser-oriented visualization.

The C++ implementation emphasizes explicit types, fixed-size containers, deterministic simulation, modular functions, validation, and an application-style architecture. It illustrates why C++ is useful when numerical control software needs predictable memory behavior and high execution performance.

The mathematical result should remain consistent across all three implementations. Differences in printed values arise from floating-point representation and stochastic measurement sampling rather than from different quantum definitions.

## Real-world relevance

Bloch-sphere methods are widely useful for reasoning about single-qubit control and characterization. They provide an intuitive bridge between abstract quantum mechanics and the behavior of physical qubit states.

In quantum hardware calibration, a control sequence can be understood as a series of rotations that moves the state around the sphere. Measurement data can be used to estimate the resulting state. Noise can be represented as shrinking or distorting the Bloch vector.

In quantum algorithms, the sphere is useful for understanding elementary operations such as X, Y, Z, H, S, T, and arbitrary single-qubit rotations. It is particularly useful when learning how phase and interference arise from sequential gate operations.

In quantum communication, the representation helps visualize the state space of a single transmitted qubit and provides geometric intuition for basis changes and measurements.

In quantum characterization, the relationship between Pauli expectation values and Bloch coordinates provides the foundation for single-qubit tomography.

The central limitation remains dimensionality. The Bloch sphere gives a complete geometric picture of one qubit, while larger quantum systems require increasingly sophisticated mathematical representations.

## Relationship between the three implementations

The Python program emphasizes equations, transformations, validation, tomography, density matrices, noise, and a compact educational simulator.

The JavaScript program emphasizes explicit complex-number implementation, object-oriented numerical structures, executable gate sequences, measurement simulation, and SVG visualization.

The C++ program turns the mathematics into a structured technical case study. It combines state preparation, gate control, trajectory recording, density matrices, measurement statistics, tomography, noise channels, fidelity, validation, and deterministic random simulation.

Together, the implementations demonstrate the same physical model through three different programming approaches while keeping the underlying mathematical definitions consistent.
