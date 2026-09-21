# Qubits

## Introduction

A qubit, or quantum bit, is the basic unit of quantum information. A classical bit has two possible logical values, 0 and 1. A qubit is described by a quantum state that can contain probability amplitudes associated with the computational basis states |0⟩ and |1⟩.

A general pure single-qubit state is written as:

`|ψ⟩ = α|0⟩ + β|1⟩`

where `α` and `β` are complex probability amplitudes satisfying the normalization condition:

`|α|² + |β|² = 1`

The probabilities obtained when measuring in the computational basis are:

`P(0) = |α|²`

`P(1) = |β|²`

This relationship is called the Born rule.

The three implementations in this repository approach qubits from different technical perspectives:

- Python provides a readable mathematical simulator suitable for studying the concepts directly.
- JavaScript demonstrates the same underlying mechanisms in a language commonly used for interactive applications and web environments.
- C++ develops a more structured state-vector engine and applies it to a quantum communication case study.

The implementations are educational simulators. They do not model the physical details of a quantum processor or replace a full quantum-computing framework.

## Fundamental concepts

### Classical bit

A classical bit has a definite logical state:

`0`

or

`1`

A classical system can use a probability distribution to represent uncertainty about a bit, but that is not the same physical concept as a coherent quantum superposition.

### Qubit

A qubit uses amplitudes rather than ordinary classical probabilities.

The state

`|ψ⟩ = α|0⟩ + β|1⟩`

does not mean that the qubit is simply an ordinary probabilistic mixture of 0 and 1. The complex amplitudes contain phase information that can influence later interference.

### Computational basis

The two standard basis states are:

`|0⟩ = [1, 0]ᵀ`

`|1⟩ = [0, 1]ᵀ`

They form the computational basis for a single qubit.

### Superposition

Applying a Hadamard gate to `|0⟩` produces:

`H|0⟩ = (|0⟩ + |1⟩) / √2`

The resulting measurement probabilities are 50% for 0 and 50% for 1.

Superposition should not be interpreted as a classical coin that is secretly either 0 or 1. The amplitudes have phase relationships and can interfere during subsequent quantum operations.

### Probability amplitude

An amplitude is generally a complex number. Its squared magnitude determines measurement probability.

If:

`α = a + bi`

then:

`|α|² = a² + b²`

The amplitude itself is not a probability because it can be negative or complex.

### Normalization

A valid quantum state must have total probability one:

`Σ |αᵢ|² = 1`

The Python, JavaScript, and C++ implementations validate normalization after quantum operations. This catches many implementation errors such as incorrectly constructed gates or state-update logic.

## Measurement

Measurement converts quantum information into a classical result.

For:

`|ψ⟩ = α|0⟩ + β|1⟩`

a computational-basis measurement produces:

- 0 with probability `|α|²`
- 1 with probability `|β|²`

An ideal projective measurement also changes the state. After obtaining 0, the state is projected to `|0⟩`. After obtaining 1, it is projected to `|1⟩`.

For multiple qubits, measurement produces one computational-basis bit string. A two-qubit state has four possible computational results:

`00`, `01`, `10`, and `11`

The simulator repeatedly samples the probability distribution to create measurement histograms.

## Complex numbers and quantum states

Complex numbers are fundamental to quantum mechanics.

The Python implementation uses Python's built-in `complex` type. The JavaScript implementation defines a `Complex` class because standard JavaScript does not provide a native complex-number type. The C++ implementation uses `std::complex<double>` from the standard library.

A complex amplitude can be expressed as:

`α = a + bi`

Its complex conjugate is:

`α* = a - bi`

The magnitude squared is:

`|α|² = α*α`

This operation converts a complex amplitude into a non-negative real probability.

## Quantum gates

Quantum gates are transformations applied to quantum states.

For isolated ideal quantum evolution, gates are represented by unitary matrices:

`U†U = I`

where `U†` is the conjugate transpose of `U`.

Unitary transformations preserve normalization.

### Identity gate

The identity gate does nothing:

`I|ψ⟩ = |ψ⟩`

It is useful as a mathematical building block for multi-qubit operations.

### Pauli-X

The X gate is analogous to a classical bit flip:

`X|0⟩ = |1⟩`

`X|1⟩ = |0⟩`

Its matrix is:

`[[0, 1], [1, 0]]`

### Pauli-Y

The Y gate performs a bit-and-phase transformation:

`Y = [[0, -i], [i, 0]]`

It is one of the three Pauli operators.

### Pauli-Z

The Z gate leaves `|0⟩` unchanged while changing the phase of `|1⟩`:

`Z|0⟩ = |0⟩`

`Z|1⟩ = -|1⟩`

This demonstrates why phase is important even when computational-basis measurement probabilities do not immediately change.

### Hadamard

The Hadamard gate is:

`H = 1/√2 [[1, 1], [1, -1]]`

It creates and removes important superpositions.

For example:

`H|0⟩ = |+⟩`

and:

`H|1⟩ = |−⟩`

where:

`|+⟩ = (|0⟩ + |1⟩)/√2`

`|−⟩ = (|0⟩ - |1⟩)/√2`

### S and T gates

The S gate applies a phase of π/2 to the `|1⟩` component.

The T gate applies a phase of π/4.

They are examples of phase gates and are useful when constructing more general quantum circuits.

### Rotation gates

The implementations include rotations around the X, Y, and Z axes.

The X rotation is:

`Rx(θ) = cos(θ/2)I - i sin(θ/2)X`

The Y rotation is:

`Ry(θ) = cos(θ/2)I - i sin(θ/2)Y`

The Z rotation is:

`Rz(θ) = cos(θ/2)I - i sin(θ/2)Z`

These gates provide continuous control over a qubit's state.

## Interference

Interference is one of the central differences between quantum amplitudes and classical probabilities.

Consider:

`H|0⟩ = (|0⟩ + |1⟩)/√2`

Applying another Hadamard gives:

`H(H|0⟩) = |0⟩`

The intermediate amplitudes combine so that the `|1⟩` contribution cancels.

The Python and JavaScript implementations demonstrate this directly. The C++ implementation contains the gate infrastructure required for the same behavior.

Quantum algorithms exploit constructive and destructive interference to alter the probability distribution of measurement results.

## Phase

There are two important ideas concerning phase.

A global phase multiplies the complete state by the same factor:

`|ψ⟩ → e^{iφ}|ψ⟩`

This does not change observable measurement probabilities.

A relative phase changes the relationship between components of a superposition:

`α|0⟩ + β|1⟩`

versus:

`α|0⟩ - β|1⟩`

can produce different results when further gates are applied.

The Python and JavaScript phase demonstrations use the Z gate and Hadamard gate to expose this behavior.

## Bloch sphere

Every pure single-qubit state can be represented geometrically on the Bloch sphere.

A common parameterization is:

`|ψ⟩ = cos(θ/2)|0⟩ + e^{iφ}sin(θ/2)|1⟩`

The corresponding Bloch vector is:

`x = 2 Re(α*β)`

`y = 2 Im(α*β)`

`z = |α|² - |β|²`

The Python and JavaScript implementations calculate these coordinates.

Important locations include:

- `|0⟩`: north pole
- `|1⟩`: south pole
- `|+⟩`: positive X direction
- `|−⟩`: negative X direction

The Bloch sphere provides an intuitive geometric representation for one-qubit pure states, but it does not scale directly as a complete visualization of arbitrary many-qubit states.

## Multiple qubits

One qubit requires two complex amplitudes.

Two qubits require four amplitudes.

Three qubits require eight amplitudes.

In general, `n` qubits require:

`2ⁿ`

complex amplitudes in a dense state-vector representation.

A two-qubit state can be written as:

`|ψ⟩ = α₀₀|00⟩ + α₀₁|01⟩ + α₁₀|10⟩ + α₁₁|11⟩`

The amplitudes must satisfy:

`|α₀₀|² + |α₀₁|² + |α₁₀|² + |α₁₁|² = 1`

### Tensor product

Independent systems are combined using the tensor product.

If:

`|a⟩ = α|0⟩ + β|1⟩`

and:

`|b⟩ = γ|0⟩ + δ|1⟩`

then:

`|a⟩ ⊗ |b⟩`

produces a four-dimensional state.

The Python implementation provides `tensor_product` and `tensor_many`. The C++ implementation uses the same mathematical idea in its state-vector representation.

## Entanglement

Entanglement occurs when a multi-qubit state cannot be expressed as a tensor product of independent single-qubit states.

One important example is the Bell state:

`|Φ+⟩ = (|00⟩ + |11⟩)/√2`

The standard circuit is:

1. Start with `|00⟩`.
2. Apply H to the first qubit.
3. Apply CNOT with the first qubit as control and the second as target.

The result is:

`(|00⟩ + |11⟩)/√2`

A computational-basis measurement produces `00` or `11`, each with probability one half in the ideal state.

The Python, JavaScript, and C++ implementations all model this mechanism.

Entanglement is not simply "two random bits that happen to match." The joint quantum state contains correlations that cannot generally be represented as independent local states.

## CNOT

CNOT is a controlled operation.

For control `c` and target `t`:

- If the control is 0, the target is unchanged.
- If the control is 1, the target is flipped.

For computational basis states:

`|00⟩ → |00⟩`

`|01⟩ → |01⟩`

`|10⟩ → |11⟩`

`|11⟩ → |10⟩`

CNOT is especially important because it can convert a single-qubit superposition into an entangled multi-qubit state.

## Python implementation

The Python program is designed as the most explicit mathematical teaching implementation.

### State representation

A qubit is represented by a Python list of complex amplitudes:

`[alpha, beta]`

A two-qubit state contains four amplitudes, and an n-qubit state contains `2**n` amplitudes.

### Gate representation

Gates are represented as nested lists containing complex numbers.

The program defines:

- `I`
- `X`
- `Y`
- `Z`
- `H`
- `S`
- `T`
- `Rx`
- `Ry`
- `Rz`
- `CNOT`
- `SWAP`

The `apply_gate` function checks that a matrix is unitary before applying it.

### Measurement

The `measure_state` function calculates probabilities from squared amplitude magnitudes, selects a result according to those probabilities, and returns the collapsed basis state.

The `sample_measurements` function repeats this process for multiple shots.

This separation is useful because quantum hardware generally executes a circuit many times when estimating a probability distribution.

### Multi-qubit operations

The Python implementation contains two different approaches.

`matrix_kronecker` constructs a full Kronecker product for matrices. This directly demonstrates the mathematics but can become expensive as the number of qubits grows.

`apply_single_qubit_gate` applies a one-qubit operation directly to selected amplitudes without explicitly constructing the entire `2ⁿ × 2ⁿ` matrix.

This distinction is important in practical quantum simulation.

### Density matrices

The Python implementation also introduces:

`ρ = |ψ⟩⟨ψ|`

for a pure state.

It demonstrates a classical mixture using:

`ρ = pρ₁ + (1-p)ρ₂`

Density matrices are required when describing mixed states, noise, partial information, and many open-system calculations.

## JavaScript implementation

The JavaScript implementation builds an explicit `Complex` class.

This is necessary because JavaScript's standard numeric type does not have a native complex-number abstraction.

The class implements:

- addition
- subtraction
- multiplication
- conjugation
- scaling
- magnitude
- magnitude squared
- polar representation

The implementation then builds matrix and state-vector operations on top of this class.

### Why JavaScript is useful here

JavaScript is particularly suitable for interactive quantum demonstrations because it runs directly in browsers and integrates naturally with visual interfaces.

The implementation is deliberately kept independent of external packages so that the quantum-state mechanisms remain visible.

The JavaScript version demonstrates:

- single-qubit gates
- rotations
- multi-qubit operations
- measurement
- circuit construction
- Bloch coordinates
- density matrices
- noise
- BB84-style basis selection
- validation
- state-vector scaling

The `QuantumCircuit` class separates circuit construction from execution.

This resembles a common software architecture in which a circuit description is created first and executed afterward.

## C++ case study

The C++ implementation develops a small state-vector engine around an industry-style scenario.

The case study combines three elements:

1. Entangled qubits
2. Quantum communication
3. A noisy quantum channel

This makes the implementation more representative of a technical system than a collection of isolated gate examples.

### Problem being modeled

The simulated system needs to:

- represent qubit states
- apply unitary operations
- manipulate selected qubits
- create entanglement
- perform measurement
- collect repeated measurement statistics
- model a simple channel error
- prepare and measure BB84 states
- validate invalid operations
- expose simulation scaling

### Major components

The C++ program contains:

- `Complex` as an alias for `std::complex<double>`
- `StateVector` for amplitudes
- `Matrix` for quantum operators
- mathematical validation functions
- common quantum gates
- tensor-product support
- selected-qubit gate application
- CNOT implementation
- measurement functions
- `QuantumCircuit`
- BB84-style state preparation
- measurement-basis handling
- a bit-flip noise model
- reporting functions

### Circuit abstraction

The `QuantumCircuit` class stores operations and executes them sequentially.

An operation can be:

- a single-qubit gate
- a CNOT operation

The circuit starts in the all-zero computational state.

For example, the Bell-state circuit stores:

`H q0`

followed by:

`CNOT q0 -> q1`

The circuit can then be executed repeatedly for measurement statistics.

### Direct selected-qubit updates

The C++ implementation does not construct a full matrix for every multi-qubit operation.

Instead, it identifies amplitude pairs associated with the target qubit.

For a single-qubit operation, each pair of amplitudes corresponds to the two possible target-bit values while the other bits remain fixed.

This reduces unnecessary matrix construction.

The same concept appears in the Python and JavaScript implementations.

## BB84-style qubit communication

The C++ case study contains a simplified BB84-style protocol.

Four states are involved:

- `|0⟩`
- `|1⟩`
- `|+⟩`
- `|−⟩`

Alice selects a bit and a preparation basis.

For the computational basis:

- bit 0 produces `|0⟩`
- bit 1 produces `|1⟩`

For the Hadamard basis:

- bit 0 produces `|+⟩`
- bit 1 produces `|−⟩`

Bob independently selects a measurement basis.

When Bob chooses the same basis as Alice, the ideal noiseless model reproduces Alice's bit.

When Bob chooses the incompatible basis, the result is probabilistic.

After transmission, the parties compare bases publicly and keep positions where their bases agree. This is called sifting.

The Python, JavaScript, and C++ versions contain educational BB84-style simulations.

These implementations are not complete cryptographic systems. A practical quantum key-distribution system requires authenticated classical communication, error correction, privacy amplification, finite-key security analysis, physical-device modeling, side-channel analysis, and secure implementation.

## Density matrices

A state vector is appropriate for a pure state.

A density matrix provides a more general representation.

For a pure state:

`ρ = |ψ⟩⟨ψ|`

A density matrix must satisfy important physical properties, including:

- Hermiticity
- trace equal to one
- positive semidefiniteness

A classical mixture can be represented as:

`ρ = Σ pᵢ |ψᵢ⟩⟨ψᵢ|`

The distinction between a coherent superposition and a classical mixture is important.

For example, the states:

`(|0⟩ + |1⟩)/√2`

and

`50% |0⟩, 50% |1⟩`

can produce the same computational-basis measurement probabilities while having different phase coherence and different behavior under subsequent quantum operations.

## Noise

Real quantum hardware is not perfectly isolated.

The implementations use a simple stochastic bit-flip model:

`ρ → (1-p)ρ + pXρX`

The executable demonstrations implement the corresponding trajectory-level behavior by randomly applying X with probability `p`.

This is intentionally simplified.

Important real-world error mechanisms include:

### Bit-flip error

A logical 0 can become 1 and vice versa.

### Phase-flip error

The relative phase can be altered.

### Depolarizing noise

A model may represent a process that drives a state toward a maximally mixed state.

### Dephasing

Phase coherence is lost without necessarily causing a bit flip.

### Relaxation

An excited state can decay toward a lower-energy state.

### Readout error

The physical measurement device can report an incorrect classical result.

### Leakage

A physical qubit can leave the computational subspace entirely.

### Crosstalk

Operations on one physical qubit can influence another.

These effects are substantially more complicated than the single bit-flip model used in the case study.

## Expectation values

For a state `|ψ⟩` and operator `O`, the expectation value is:

`⟨O⟩ = ⟨ψ|O|ψ⟩`

For a Hermitian observable, the expectation value is real.

The Python and JavaScript implementations calculate expectation values for the Pauli operators X, Y, and Z.

For `|+⟩`:

`⟨X⟩ = 1`

`⟨Y⟩ = 0`

`⟨Z⟩ = 0`

Expectation values are important because many quantum algorithms ultimately require estimates of observables rather than the complete state vector.

## Measurement statistics and shots

A quantum circuit usually does not reveal the entire state vector through a single measurement.

Instead, the circuit is executed repeatedly.

Each execution produces one classical outcome.

For example, a Bell state ideally gives:

`00` approximately 50%

`11` approximately 50%

`01` approximately 0%

`10` approximately 0%

With a finite number of shots, observed frequencies fluctuate around the theoretical probabilities.

This is statistical sampling rather than a deterministic extraction of every amplitude.

## Global phase versus relative phase

A global phase:

`e^{iφ}|ψ⟩`

does not alter measurement probabilities.

A relative phase does matter.

For example:

`(|0⟩ + |1⟩)/√2`

and:

`(|0⟩ - |1⟩)/√2`

have identical computational-basis probabilities.

Applying H afterward produces different computational-basis outcomes.

This is one reason a qubit cannot be accurately described only by its measurement probabilities in a single basis.

## Edge cases demonstrated

The implementations intentionally reject invalid states and operations.

Examples include:

- basis values other than 0 or 1
- zero-vector normalization
- invalid measurement shot counts
- invalid qubit indices
- identical CNOT control and target
- mismatched matrix dimensions
- non-unitary gate matrices
- invalid noise probabilities
- invalid BB84 basis values
- state vectors with incorrect dimensions

These checks are important because quantum simulation is sensitive to numerical and structural errors.

## Common implementation mistakes

### Treating amplitudes as probabilities

An amplitude such as `1/√2` is not itself a probability.

Its probability contribution is:

`(1/√2)² = 1/2`

For complex amplitudes, the correct operation is the squared magnitude.

### Forgetting normalization

A state with:

`|α|² + |β|² ≠ 1`

is not a valid normalized pure-state vector.

### Using ordinary multiplication instead of tensor products

Combining quantum systems requires tensor products.

Simply multiplying corresponding amplitudes does not create the complete composite state.

### Confusing superposition with a classical mixture

A coherent superposition contains phase information. A classical mixture represents uncertainty without requiring the same coherence.

### Ignoring qubit ordering

Multi-qubit simulators must define whether the first qubit corresponds to the most significant or least significant bit.

The implementations explicitly use a big-endian display convention where qubit 0 is the leftmost displayed bit.

### Building enormous matrices unnecessarily

A direct `2ⁿ × 2ⁿ` matrix becomes expensive rapidly.

Applying local gates directly to the affected amplitude pairs can reduce unnecessary computation.

### Assuming simulation equals hardware

A state-vector simulator operates with exact mathematical objects subject only to floating-point error. Physical quantum processors introduce calibration error, noise, decoherence, measurement imperfections, connectivity constraints, control errors, and other engineering limitations.

## Performance considerations

The most important scaling property of dense state-vector simulation is exponential growth.

An n-qubit state requires:

`2ⁿ`

complex amplitudes.

Examples:

| Qubits | Amplitudes |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 4 | 16 |
| 8 | 256 |
| 12 | 4,096 |
| 16 | 65,536 |
| 20 | 1,048,576 |

At larger scales, memory becomes the limiting resource before many simple demonstrations can be executed comfortably.

Gate application also has computational cost related to the state-vector dimension.

A naive dense matrix-vector multiplication can require roughly quadratic work in the matrix dimension. Local quantum gates can often be applied more efficiently by updating structured amplitude pairs.

### Techniques used to reduce unnecessary work

The implementations use direct local updates for single-qubit gates and CNOT.

This avoids constructing the complete multi-qubit matrix for every operation.

Other simulation strategies used in quantum computing include:

- sparse state representations
- stabilizer simulation
- tensor-network methods
- decision diagrams
- specialized classical hardware
- distributed state-vector simulation
- problem-specific mathematical simplifications

The appropriate method depends on circuit structure and the properties being simulated.

## Numerical precision

The implementations use floating-point complex numbers.

Floating-point arithmetic introduces small errors.

For this reason, exact comparisons such as:

`value == 0`

are generally inappropriate for numerical quantum simulation.

The implementations use tolerance-based comparisons such as:

`abs(value) < ε`

The normalization checks also allow small numerical deviations.

## Security considerations

Qubits have important applications in quantum cryptography, including quantum key distribution.

The BB84-style implementation demonstrates the relationship between incompatible bases and measurement disturbance, but it should not be treated as secure cryptographic software.

A real security analysis must account for:

- authentication
- adversarial capabilities
- finite sample sizes
- error correction
- privacy amplification
- imperfect detectors
- source imperfections
- side channels
- device-specific leakage
- implementation vulnerabilities
- classical cryptographic assumptions
- protocol-level security proofs

A mathematically correct state-vector simulation does not automatically establish security for a physical implementation.

## Python, JavaScript, and C++ comparison

### Python

Python is particularly useful for mathematical exploration.

The Python implementation emphasizes:

- readable formulas
- rapid experimentation
- state-vector manipulation
- density matrices
- measurement
- expectation values
- Bloch vectors
- circuit abstractions

Python's built-in complex numbers make the basic state representation concise.

### JavaScript

JavaScript provides a natural environment for browser-based quantum demonstrations.

The implementation emphasizes:

- explicit complex-number handling
- object-oriented circuit construction
- reusable functions
- state-vector simulation
- interactive-application suitability
- deterministic demonstration randomness

A browser application could use the same computational structures to connect quantum operations to visual interfaces.

### C++

C++ is appropriate when low-level performance and resource control matter.

The case study demonstrates:

- `std::complex`
- strongly typed data structures
- explicit memory-oriented state representation
- modular classes
- standard-library random number generation
- structured error handling
- state-vector simulation
- a communication-system case study

The C++ implementation also makes the simulation-scaling problem particularly visible.

## Important distinctions

### Qubit versus bit

A bit is a classical information unit.

A qubit is a quantum information unit described by amplitudes and governed by quantum-mechanical evolution.

### Amplitude versus probability

Amplitude is generally complex.

Probability is a non-negative real quantity derived from squared magnitude.

### Superposition versus mixture

Superposition preserves coherent phase relationships.

A mixture represents classical uncertainty over possible states.

### Entanglement versus correlation

Classical systems can have correlations.

Quantum entanglement refers to states whose joint quantum description cannot generally be decomposed into independent local pure states.

### Measurement versus simulation

A simulator can inspect its internal state vector because it is implementing the mathematical model.

A physical quantum device cannot simply expose all amplitudes through a single measurement.

### Quantum gate versus classical instruction

A quantum gate is generally represented by a unitary transformation on amplitudes.

A classical instruction operates on definite classical values or classical data structures.

## Real-world relevance

Qubits are the basic abstraction underlying quantum-computing architectures.

They are relevant to:

- quantum algorithms
- quantum simulation
- quantum chemistry
- optimization research
- quantum communication
- quantum cryptography
- quantum error correction
- quantum sensing
- quantum networking
- quantum control
- quantum hardware engineering

A physical qubit can be implemented using different technologies, including superconducting circuits, trapped ions, neutral atoms, photonic systems, semiconductor spin systems, and other physical platforms.

The abstract qubit model allows algorithms and information-processing principles to be studied independently of a specific hardware implementation.

## Implementation limitations

These three programs intentionally simplify several aspects of real quantum computing.

They use:

- ideal unitary gates
- finite-precision arithmetic
- dense state vectors
- simplified measurement
- simplified noise
- small circuit sizes
- no physical device calibration
- no hardware topology
- no pulse-level control
- no complete error-correction system

The C++ BB84 example is an educational protocol model rather than a complete QKD implementation.

The simulations are valuable because they make the mathematical structure of qubits explicit without requiring specialized hardware.

## Practical architecture of the implementations

The implementations follow a layered design.

### Mathematical layer

This layer handles:

- complex numbers
- vector operations
- matrix operations
- normalization
- conjugation
- tensor products
- unitarity checks

### Quantum-state layer

This layer represents:

- basis states
- superposition
- multi-qubit states
- measurement
- state collapse

### Gate layer

This layer implements:

- Pauli gates
- Hadamard
- phase gates
- rotations
- CNOT
- SWAP

### Circuit layer

The circuit abstraction stores operations and executes them sequentially.

### Application layer

The C++ implementation adds a quantum communication scenario using:

- state preparation
- basis selection
- measurement
- sifting
- noise
- mismatch analysis

This separation makes the simulator easier to extend and test.

## Testing considerations

A useful quantum simulator should test mathematical invariants rather than only printed output.

Important tests include:

- every gate preserves normalization
- every declared gate is unitary
- X twice returns the original state
- H twice returns the original state
- measurement probabilities sum to one
- CNOT produces the expected computational-basis mapping
- Bell-state measurements produce only the expected correlated outcomes
- invalid dimensions are rejected
- invalid qubit indices are rejected
- invalid probabilities are rejected

Testing numerical quantum software requires tolerances because floating-point calculations are not exact.

## Complexity considerations

For `n` qubits:

- state-vector size is `O(2ⁿ)`
- storing every amplitude requires exponential memory
- a local single-qubit gate can be applied in `O(2ⁿ)` time
- repeated measurement requires work proportional to the number of shots and the state dimension in a straightforward implementation
- full dense multi-qubit matrices can require `O(4ⁿ)` storage

The direct local-gate approach used by the implementations avoids constructing many of those large matrices.

This does not remove the fundamental exponential state-space requirement for arbitrary states.

## Production considerations

A production quantum software system would normally need substantially more engineering around the mathematical core.

Important concerns include:

- deterministic and reproducible testing
- efficient memory management
- numerical stability
- optimized linear algebra
- circuit validation
- gate decomposition
- hardware-specific constraints
- connectivity mapping
- error modeling
- noise-aware compilation
- measurement calibration
- logging
- benchmarking
- parallel execution
- distributed simulation
- secure interfaces
- versioned circuit representations

The small simulators in this repository focus on the conceptual and algorithmic foundations rather than production-scale hardware integration.
