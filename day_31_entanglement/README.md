# Entanglement: Bell States and Non-Classical Correlations

## Scope

This project studies two-qubit entanglement through the four Bell states and the correlations produced when the two subsystems are measured jointly.

The central distinction is between **local measurement randomness** and **joint non-classical correlation**. An individual subsystem of a Bell pair can have completely random measurement statistics while the pair as a whole exhibits highly structured correlations. The Bell-state formalism provides a compact mathematical setting in which this distinction can be implemented and tested.

The three implementations approach the same subject from different technical perspectives:

- The Python program is a mathematical and simulation-oriented learning implementation. It constructs Bell states, applies single-qubit gates, samples measurements, calculates reduced density matrices and entropy, evaluates Pauli correlations, and simulates a CHSH experiment.
- The JavaScript program emphasizes explicit complex-number operations, matrix processing, asynchronous measurement events, and an event-driven experimental stream.
- The C++ program treats the subject as a quantum-network verification case study in which a correlation engine validates states, evaluates measurement observables, estimates finite-shot correlations, and computes CHSH statistics.

The implementations use state-vector mathematics rather than a hardware-specific quantum SDK, making the underlying mechanisms visible.

## Entanglement and Two-Qubit States

A single qubit can be written as

`|ψ> = α|0> + β|1>`

where the complex amplitudes satisfy

`|α|² + |β|² = 1`.

A two-qubit state has four computational-basis components:

`|ψ> = α₀₀|00> + α₀₁|01> + α₁₀|10> + α₁₁|11>`.

The four amplitudes are stored in the implementations in the order:

`|00>, |01>, |10>, |11>`.

A two-qubit pure state is separable when it can be expressed as a tensor product of two single-qubit states:

`|ψ> = |u> ⊗ |v>`.

An entangled state cannot be decomposed into that form. This is not simply a statement that the amplitudes are complicated. It is a structural property of the joint state.

For example,

`(|0> + |1>) / sqrt(2) ⊗ (|0> + |1>) / sqrt(2)`

is a superposition but remains separable. By contrast,

`(|00> + |11>) / sqrt(2)`

is entangled.

The distinction is important because superposition and entanglement are different concepts. Superposition concerns a quantum system having multiple basis-state amplitudes. Entanglement concerns correlations that cannot be represented as independent states of the constituent subsystems.

## Bell States

The four Bell states form an orthonormal basis for the two-qubit Hilbert space:

| Bell state | Definition | Z-basis correlation |
|---|---|---|
| `Phi+` | `(|00> + |11>) / sqrt(2)` | Equal bits |
| `Phi-` | `(|00> - |11>) / sqrt(2)` | Equal bits |
| `Psi+` | `(|01> + |10>) / sqrt(2)` | Opposite bits |
| `Psi-` | `(|01> - |10>) / sqrt(2)` | Opposite bits |

The signs in these expressions are relative phases. They are not interchangeable with an arbitrary change of notation because relative phase affects the result of measurements in other bases.

`Phi+` and `Phi-` demonstrate this particularly clearly. Both have probability one-half for `00` and one-half for `11`, with zero probability for `01` and `10`. Their computational-basis probability distributions therefore look identical.

Their correlation behavior is not identical. For example, the Python, JavaScript, and C++ implementations evaluate the Pauli correlation `<X ⊗ X>` and show different signs for `Phi+` and `Phi-`.

## Measurement and the Born Rule

A state-vector amplitude does not directly represent a measurement probability. The probability of obtaining a computational-basis outcome is the squared magnitude of its complex amplitude:

`P(i) = |αᵢ|²`.

For `Phi+`,

`P(00) = 1/2`

and

`P(11) = 1/2`.

The measurement result is therefore individually unpredictable. The important feature is the relationship between the two results: they agree whenever the pair is measured in the computational basis.

This gives two different statements:

- Each local result can be random.
- The joint outcomes can nevertheless be strongly correlated.

Entanglement should not be described as one particle simply containing a predetermined classical copy of the other particle's measurement result. Bell-state correlations become particularly significant when measurements are performed along different axes.

## Python Implementation

The Python implementation is organized around the `QubitState` class. It stores four complex amplitudes and validates normalization when a state is constructed.

The `probabilities()` method applies the Born rule directly to the four amplitudes. `sample_measurement()` and `sample_many()` turn the mathematical distribution into finite measurement data using Python's standard pseudo-random generator.

The Bell-state factory constructs all four states explicitly. This makes the relative phase visible instead of hiding the state definitions behind a library abstraction.

### Single-Qubit Gate Operation

The Python implementation includes a general `apply_single_qubit_gate()` method for a 2x2 gate acting on either qubit. The method maps each two-qubit basis index into its individual bit positions and applies the gate to the selected subsystem.

The demonstration uses the Hadamard matrix to transform `|00>` into

`(|00> + |10>) / sqrt(2)`.

This is deliberately shown before Bell-state analysis because it illustrates a common conceptual mistake: creating a superposition on one qubit does not automatically create entanglement.

An additional interaction between subsystems is required to produce a non-separable state.

### Reduced Density Matrix

The function `partial_trace_first_qubit()` calculates the reduced density matrix of the second subsystem.

For amplitudes `a_ij`, the reduced matrix elements are calculated as

`rho_B[j,k] = sum_i a_ij * conjugate(a_ik)`.

For a Bell state, the reduced state is

`I / 2`.

The Python program then calculates the von Neumann entropy of that reduced state. Its eigenvalues are `1/2` and `1/2`, giving one bit of entropy.

This is an important distinction between the joint and local descriptions:

- The Bell state itself is a pure state.
- Either individual subsystem is represented by a maximally mixed reduced state.

For a pure bipartite state, nonzero entropy of a reduced subsystem is an indicator of entanglement.

### Pauli Correlations

The Python implementation constructs the Pauli `X`, `Y`, and `Z` matrices and their tensor products.

It evaluates quantities such as

`<X ⊗ X>`

and

`<Z ⊗ Z>`.

These expectation values describe correlations of binary observables whose outcomes can be interpreted as `+1` or `-1`.

The correlation table gives each Bell state a characteristic signature. This demonstrates why Bell states cannot be completely characterized by their computational-basis probability distributions alone.

### CHSH Simulation

The Python implementation also defines a rotated spin observable

`n · sigma`

where `n` is a three-dimensional unit vector.

The CHSH expression is implemented as

`S = E(a,b) + E(a,b') + E(a',b) - E(a',b')`.

For the selected `Phi+` state and measurement axes, the exact value reaches the quantum maximum

`2 sqrt(2)`.

The classical CHSH limit is

`|S| <= 2`.

The finite-shot simulator then estimates the four correlations from random experimental samples. The estimate does not equal the theoretical value exactly because a finite number of measurements introduces statistical fluctuation.

## JavaScript Implementation

The JavaScript implementation deliberately does not depend on a quantum-computing package. The `Complex` class provides the arithmetic required by the state-vector calculations.

This makes several JavaScript-specific implementation details visible:

- Objects represent state and matrix structures.
- Methods encapsulate complex-number operations.
- Arrays represent vectors and matrices.
- `async` and `await` represent an event-driven measurement stream.
- `setTimeout()` yields execution to the Node.js event loop between simulated observations.
- Exceptions are propagated through asynchronous execution and handled by the top-level `catch`.

The `TwoQubitState` class normalizes amplitudes when a state is constructed. Its `densityMatrix()` method forms the outer product of the state vector with its conjugate transpose, while `reducedDensityMatrixOfSecondQubit()` performs the subsystem trace directly from the amplitudes.

### Event-Driven Measurement Stream

The JavaScript implementation introduces `createMeasurementStream()` to represent repeated experimental observations as an asynchronous process.

A measurement is produced, its count is recorded, and the next measurement is scheduled through `setTimeout()`. This does not make the mathematics quantum. It demonstrates how a real application could represent a stream of measurement events without blocking the Node.js event loop.

The final result is a histogram of Bell-state measurement outcomes.

For `Phi+` in the computational basis, the `01` and `10` counts should remain near zero, while `00` and `11` fluctuate around equal proportions.

## C++ Case Study: Quantum-Network Correlation Verification

The C++ implementation models a hypothetical verification service for an entangled-pair experiment.

Two endpoints receive members of a pair. Each endpoint has two possible measurement settings. The verification system collects joint outcomes and calculates the CHSH statistic rather than treating a single measurement as evidence of a particular correlation structure.

The architectural flow is:

`Bell state -> measurement observables -> joint correlations -> finite-shot estimates -> CHSH statistic`

The `BellState` class owns a normalized four-component state vector. Its constructor rejects states whose squared amplitude norm is not one.

The `Matrix2` and `Matrix4` types provide fixed-size representations for one- and two-qubit operators. The `kronecker()` function constructs joint observables such as `X ⊗ X` and `Z ⊗ Z`.

The fixed-size `std::array` structures are appropriate for this case study because the system is explicitly limited to two qubits. They avoid dynamic allocation for the core mathematical objects and make matrix dimensions apparent in the type definitions.

### Measurement Axes

The C++ function `rotatedObservable()` constructs

`n · sigma`

from polar and azimuthal angles.

This permits the case study to use measurement directions that are not restricted to the computational `Z` axis.

The CHSH configuration uses axes corresponding to angles of `0°`, `90°`, `45°`, and `-45°`. These settings produce the characteristic quantum violation for the selected Bell state under the implemented CHSH convention.

### Finite-Shot Experiment

The C++ program estimates each correlation from `25,000` simulated shots per measurement setting.

The finite-shot model samples binary outcomes with the target correlation determined from the exact quantum expectation value. The resulting estimates fluctuate around the theoretical correlations.

This distinction is important in practical experimental analysis. A theoretical expectation is a mathematical value, while experimental data are finite observations affected by statistical variation and, in real hardware, experimental imperfections.

### Failure Handling

The C++ implementation treats state normalization and experiment size as invariants.

An unnormalized state is rejected through `std::invalid_argument`. A zero-shot experiment is also rejected because a correlation estimate cannot be formed from an empty sample.

The program's top-level exception handler converts unexpected failures into a nonzero process exit status, which is appropriate for a command-line verification component.

## Non-Classical Correlations

The phrase **non-classical correlation** does not mean that the two measurement results are merely correlated more strongly than ordinary classical variables can be.

Classical probability theory can produce perfectly correlated or anti-correlated variables. For example, two classical records can be constructed so that they always contain the same bit.

The distinctive feature of Bell-state correlations is their behavior across multiple incompatible measurement settings.

A Bell test uses correlations from different choices of measurement basis. Under the assumptions used to derive the CHSH inequality, local hidden-variable models satisfy

`|S| <= 2`.

Quantum mechanics allows

`|S| <= 2 sqrt(2)`,

known as the Tsirelson bound for the CHSH expression.

The Bell-state implementations produce a value above the classical CHSH limit for the selected measurement configuration.

This does not mean that a single measurement proves entanglement. The inference concerns an ensemble of correlations obtained under controlled measurement settings and depends on the assumptions and experimental design of the Bell test.

## Local Randomness and Joint Structure

A Bell state illustrates why a local measurement cannot be used to reconstruct the complete joint state.

For `Phi+`, the reduced density matrix of either qubit is

`rho = [[1/2, 0], [0, 1/2]]`.

Consequently, a local computational-basis measurement gives `0` and `1` with equal probability.

Yet the joint state satisfies

`<Z ⊗ Z> = +1`.

The first statement describes the statistics available to one subsystem. The second describes a relationship between the two subsystems.

The distinction is central to entanglement:

`local state information != complete joint-state information`.

## Relative Phase

The states

`Phi+ = (|00> + |11>) / sqrt(2)`

and

`Phi- = (|00> - |11>) / sqrt(2)`

have the same computational-basis probabilities.

The difference is the relative phase between `|00>` and `|11>`.

A measurement basis sensitive to that phase reveals a different correlation structure. In particular, the sign of `<X ⊗ X>` changes.

This demonstrates why replacing a state vector with only a probability table loses information. Quantum amplitudes contain phase information that can influence later measurements.

## Bell-State Correlation Signatures

The Pauli correlation pattern is useful for distinguishing Bell states:

| State | `<XX>` | `<YY>` | `<ZZ>` |
|---|---:|---:|---:|
| `Phi+` | `+1` | `-1` | `+1` |
| `Phi-` | `-1` | `+1` | `+1` |
| `Psi+` | `+1` | `+1` | `-1` |
| `Psi-` | `-1` | `-1` | `-1` |

These values describe ideal mathematical states. Physical measurements produce finite samples, so observed estimates normally fluctuate around the theoretical expectation.

The table also illustrates why a single measurement basis is insufficient to identify every Bell state. `Phi+` and `Phi-`, for example, share the same `ZZ` correlation but differ in `XX` and `YY`.

## CHSH and the Meaning of a Violation

The CHSH expression used by the implementations is

`S = E(a,b) + E(a,b') + E(a',b) - E(a',b')`.

Here `E(a,b)` is the expectation of the product of the two binary measurement outcomes when the first endpoint uses setting `a` and the second uses setting `b`.

The classical bound of `2` follows under the assumptions associated with the CHSH scenario, including locality and predetermined outcome assignments in the relevant hidden-variable model.

Quantum theory predicts values exceeding `2` for appropriate entangled states and measurement settings.

The maximum quantum value is `2 sqrt(2)`, approximately `2.828427`.

A real experimental Bell test requires substantially more than evaluating the theoretical expression. Experimental analyses must account for finite statistics, detector behavior, locality constraints, measurement independence, background events, and other possible loopholes or systematic effects.

The programs in this project intentionally model the mathematical correlation mechanism rather than claiming to implement a loophole-free laboratory Bell experiment.

## Common Conceptual Errors

### Entanglement is not the same as superposition

A separable state can contain many basis-state amplitudes. Superposition alone therefore does not establish entanglement.

The Python and JavaScript implementations explicitly create a single-qubit superposition before discussing Bell-state construction.

### Correlation is not automatically evidence of quantum entanglement

Classical systems can be perfectly correlated. A Bell-state claim requires examination of correlations under appropriately chosen measurement settings or another valid entanglement criterion.

The CHSH implementation addresses this distinction by examining several joint observables.

### Random local outcomes do not imply absence of correlation

The local statistics of a Bell pair can be maximally mixed while the joint statistics are strongly structured.

Looking only at one subsystem can therefore hide the correlation present in the complete state.

### Equal computational probabilities do not imply identical states

`Phi+` and `Phi-` have identical computational-basis probabilities but different relative phases and different correlations in other measurement bases.

A probability table alone is not a complete representation of a quantum state.

### A finite-shot CHSH estimate is not exactly the theoretical value

Random sampling produces statistical fluctuations. Increasing the number of shots generally reduces the sampling uncertainty, but it does not eliminate systematic experimental effects.

## Edge Cases and Numerical Considerations

Quantum-state calculations are sensitive to normalization and floating-point precision.

The implementations reject zero-norm or improperly normalized states rather than silently treating them as valid states.

Complex arithmetic also introduces small numerical residuals. For a theoretically real expectation value, floating-point calculations can leave a tiny imaginary component. The programs therefore use tolerances rather than requiring an exact zero.

Measurement simulation has a different limitation. The random generator is a classical pseudo-random source used to sample the mathematical distribution. It models finite-shot statistics but does not constitute a physical quantum random-number generator.

The CHSH simulations also use the exact theoretical correlation as the target distribution. This is useful for demonstrating sampling behavior but does not model detector noise, state-preparation errors, decoherence, transmission loss, or hardware calibration errors.

## Security and Interpretation Considerations

Entanglement is often discussed in quantum communication and cryptographic protocols, but correlation alone should not be treated as an authentication mechanism.

A software implementation that reports a Bell-state correlation is only as trustworthy as its input state model, measurement data, randomization assumptions, and validation process.

For a real experimental system, the following concerns become important:

- Measurement settings must be controlled and recorded independently of the observed outcomes.
- Raw observations should be retained so that correlation statistics can be independently recomputed.
- Randomness used for experimental setting selection has different requirements from pseudo-random sampling used by this educational simulation.
- Statistical confidence should be reported instead of treating a finite-shot estimate as an exact quantum value.
- Experimental imperfections must be separated from the ideal theoretical model.
- A CHSH violation should be interpreted within the assumptions and controls of the actual experiment.

## Performance Characteristics

The core two-qubit calculations operate on fixed-size vectors and matrices.

For this deliberately small model, matrix operations have constant dimensions. The computational cost of a single expectation-value calculation is therefore effectively constant with respect to the number of measurement shots.

The expensive part of the simulations is repeated sampling. If `N` shots are collected, measurement simulation requires `O(N)` iterations.

A general quantum simulator cannot retain this constant-size behavior. An `n`-qubit state vector contains `2^n` complex amplitudes, so memory and many direct state-vector operations scale exponentially with the number of qubits.

This project intentionally remains at two qubits because Bell states provide a mathematically complete and computationally transparent setting for studying entanglement and Bell correlations.

## Practical Relationship Between the Implementations

The three programs divide the technical perspective rather than providing three copies of the same implementation.

The Python program emphasizes mathematical exploration. Its reduced-state entropy and partial-trace functions make the relationship between a pure entangled state and mixed local subsystems explicit.

The JavaScript program emphasizes application-style event processing. Its asynchronous measurement stream shows how repeated experimental observations could be collected in an event-driven runtime while retaining explicit complex-number and matrix calculations.

The C++ program emphasizes a fixed-size systems implementation. Its strong type structure, explicit validation, finite-shot experiment model, and CHSH verification workflow resemble a small numerical component that could form part of a larger quantum-network analysis system.

Together, these perspectives connect the mathematical state description to measurement processing and then to a structured correlation-analysis workflow.
