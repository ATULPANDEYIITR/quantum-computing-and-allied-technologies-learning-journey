# Bell States: Generate and Measure Bell Pairs

## Scope

This project studies the four Bell states and the operations required to generate, measure, and distinguish Bell pairs.

The four states form the standard maximally entangled basis for two qubits:

- `|Phi+> = (|00> + |11>) / sqrt(2)`
- `|Phi-> = (|00> - |11>) / sqrt(2)`
- `|Psi+> = (|01> + |10>) / sqrt(2)`
- `|Psi-> = (|01> - |10>) / sqrt(2)`

The implementations deliberately approach the subject from three different perspectives:

- The Python program is a state-vector learning simulator with probability, density-matrix, entanglement, noise, and correlation analysis.
- The JavaScript program emphasizes an executable event-driven experiment model, deterministic sampling, asynchronous workflow, measurement processing, and state inspection.
- The C++ program models a laboratory-style Bell-pair experiment as a structured system with configuration validation, measurement orchestration, statistical reporting, and Bell-state identification.

The central relationship is:

`Bell-state preparation -> entangled two-qubit state -> basis selection -> repeated measurement -> correlation analysis`

The programs simulate ideal quantum mechanics rather than controlling physical quantum hardware.

## Bell-State Structure

A two-qubit computational basis contains four basis states:

`|00>`, `|01>`, `|10>`, and `|11>`.

A general pure two-qubit state can be written as:

`|psi> = a|00> + b|01> + c|10> + d|11>`

with the normalization condition:

`|a|^2 + |b|^2 + |c|^2 + |d|^2 = 1`

The Bell states are special because their probability amplitudes are distributed across two computational basis states while their relative phases determine additional measurement correlations.

The sign is physically important. For example:

`|Phi+> = (|00> + |11>) / sqrt(2)`

and

`|Phi-> = (|00> - |11>) / sqrt(2)`

have the same computational-basis probabilities. Measuring only in the Z basis therefore cannot distinguish them. Their relative phase becomes observable when measurements are performed in another basis.

This is why Bell-state characterization cannot be reduced to inspecting a single set of computational-basis frequencies.

## Generating a Bell Pair

The common preparation circuit begins with two qubits in `|00>`.

The first operation is a Hadamard gate on the first qubit:

`H|0> = (|0> + |1>) / sqrt(2)`

The two-qubit state therefore becomes:

`(|00> + |10>) / sqrt(2)`

A controlled-NOT with the first qubit as control changes the second qubit whenever the first qubit is `1`.

The resulting state is:

`(|00> + |11>) / sqrt(2)`

which is `|Phi+>`.

This mechanism is represented directly in all three implementations, but the code is organized differently in each language.

The other Bell states can be obtained from `|Phi+>` with local Pauli operations:

| State | Transformation from `Phi+` |
|---|---|
| `Phi+` | No additional operation |
| `Phi-` | `Z` on one qubit |
| `Psi+` | `X` on one qubit |
| `Psi-` | `X` and `Z` on one qubit |

These transformations do not require a second entangling operation after the initial CNOT. They change the local basis state or relative phase while preserving maximal entanglement.

## The Four Bell States and Measurement Correlations

The defining measurement behavior can be expressed using two measurement bases.

The Z basis is the computational basis:

`|0>`, `|1>`

The X basis is:

`|+> = (|0> + |1>) / sqrt(2)`

`|-> = (|0> - |1>) / sqrt(2)`

For ideal measurements, the Bell states have the following correlation signatures:

| Bell state | Z-basis relationship | X-basis relationship |
|---|---|---|
| `Phi+` | same outcomes | same outcomes |
| `Phi-` | same outcomes | opposite outcomes |
| `Psi+` | opposite outcomes | same outcomes |
| `Psi-` | opposite outcomes | opposite outcomes |

This distinction is important because a Bell state is not identified merely by its computational-basis probability distribution.

For example, both `Phi+` and `Phi-` produce approximately:

`P(00) = 1/2`

`P(11) = 1/2`

when measured in the Z basis.

Their X-basis behavior differs because the relative phase between `|00>` and `|11>` changes the correlation structure.

## Measurement and State Collapse

Measurement is probabilistic before the result is obtained.

For a state:

`|psi> = a|00> + b|01> + c|10> + d|11>`

the computational-basis probabilities are:

`P(00) = |a|^2`

`P(01) = |b|^2`

`P(10) = |c|^2`

`P(11) = |d|^2`

Once a projective measurement produces an outcome, the measured state collapses to the corresponding basis state.

For example, measuring `Phi+` in the Z basis can produce `00` or `11`.

Before measurement:

`|Phi+> = (|00> + |11>) / sqrt(2)`

After obtaining `00`:

`|00>`

After obtaining `11`:

`|11>`

The Python and JavaScript implementations explicitly construct the post-measurement state. The C++ implementation concentrates on repeated experimental sampling and statistical analysis.

A new Bell pair must be prepared for each independent shot. Reusing a pair after measurement would not represent independent Bell-pair preparation because the measurement has already changed the state.

## Measuring in the X Basis

The implementations use the standard basis-rotation method.

Applying `H` before computational-basis measurement changes an X-basis measurement into an ordinary Z-basis measurement.

Conceptually:

`X-basis measurement = H -> Z-basis measurement`

For two qubits, the basis rotation is applied independently to both qubits before the computational measurement.

The operation is reversible because:

`H^2 = I`

so applying the Hadamard transformation again restores the original basis representation.

This technique is useful in both simulators because it avoids requiring a separate primitive for every measurement basis.

## Python Implementation

The Python program is designed as a complete state-vector simulator rather than as a collection of isolated Bell-state formulas.

Its `generate_bell_pair()` function constructs a Bell pair from `|00>` using the Hadamard and CNOT operations. Local Pauli transformations then create the remaining Bell states.

The program implements complex arithmetic directly with Python's built-in `complex` type. State vectors are represented as lists of four amplitudes, following the basis order:

`|00>`, `|01>`, `|10>`, `|11>`

The `apply_single_qubit_gate()` function demonstrates how a two-by-two single-qubit operation is embedded into a two-qubit state without requiring a numerical computing library.

The Python program also provides repeated sampling. The `sample_measurements()` function prepares independent copies for each shot and uses a seeded pseudo-random generator to make the experiment reproducible.

The measurement section distinguishes between:

- State amplitudes
- Measurement probabilities
- A single sampled outcome
- The collapsed post-measurement state
- Aggregated shot counts
- Empirical correlations

This separation is important because an amplitude is not itself a probability. The probability is obtained from the squared magnitude of the amplitude.

### Density Matrices and Reduced States

The Python implementation goes beyond pure state vectors by constructing:

`rho = |psi><psi|`

The `partial_trace_first_qubit()` function traces out one subsystem.

For a Bell state, the reduced density matrix of an individual qubit is:

`I / 2`

The individual qubit therefore has purity:

`Tr(rho^2) = 1/2`

while the complete Bell pair is a pure state.

This illustrates an important property of entanglement: the complete two-qubit system can be in a pure state while either individual subsystem is maximally mixed.

### Concurrence

The Python program uses the pure-state two-qubit concurrence formula:

`C = 2|ad - bc|`

for:

`|psi> = a|00> + b|01> + c|10> + d|11>`

Each Bell state has:

`C = 1`

which corresponds to maximal entanglement for a pure two-qubit state.

The calculation is included as an executable diagnostic rather than merely as a theoretical statement.

### Noise Experiment

The Python implementation includes a stochastic bit-flip model.

A bit flip applies:

`X`

with a configurable probability.

This is intentionally a simple educational noise model. It is useful for observing the degradation of measured Bell correlations but is not a complete physical model of decoherence.

A realistic quantum-device model can require density matrices, quantum channels, Kraus operators, relaxation, dephasing, measurement error, crosstalk, gate error, and device-specific calibration data.

The distinction matters because a state-vector simulator containing a random bit flip should not be interpreted as a complete model of hardware noise.

### CHSH Correlations

The Python implementation also contains a CHSH-style experiment.

The observable used in the X-Z plane is:

`A(theta) = cos(theta) Z + sin(theta) X`

The expectation value is evaluated as:

`<psi|O|psi>`

The CHSH expression combines four correlation measurements.

For suitable measurement directions, an entangled Bell state can produce a magnitude above the classical local-hidden-variable bound:

`|S| <= 2`

while quantum mechanics is bounded by the Tsirelson value:

`2 sqrt(2)`

The code demonstrates the calculation using the `Psi-` Bell state.

This is conceptually different from simply checking whether two computational-basis bits match. A CHSH experiment probes correlations across multiple measurement settings.

## JavaScript Implementation

The JavaScript implementation uses a different architecture from the Python simulator.

It defines a `Complex` class instead of relying on JavaScript's lack of a native complex-number primitive. This makes amplitude arithmetic explicit and allows the state-vector operations to remain self-contained.

The JavaScript program also uses `EventTarget` through the `BellExperiment` class.

The experiment emits events for:

- Bell-pair preparation
- Z-basis measurement
- X-basis measurement
- Experiment completion

This models an event-driven experimental workflow rather than simply running a sequence of print statements.

The asynchronous `run()` method uses Promise scheduling between stages. This is useful for representing how a real software system may receive measurement data asynchronously even though the mathematical state-vector simulation itself is computationally synchronous.

### Deterministic Sampling

The JavaScript implementation contains a small seeded pseudo-random generator.

Its purpose is reproducibility during demonstrations. It is explicitly not intended for cryptographic randomness.

Reproducibility is valuable when debugging a measurement pipeline because the same seed can recreate the same experimental sequence.

For production cryptographic applications, a deterministic educational generator should not be substituted for an operating-system or hardware-backed cryptographically secure random source.

### Bell-State Identification

The JavaScript implementation measures each Bell state in both the Z and X bases.

The two observed correlation signs form a compact classification signature:

`Z same, X same -> Phi+`

`Z same, X opposite -> Phi-`

`Z opposite, X same -> Psi+`

`Z opposite, X opposite -> Psi-`

With finite samples, an empirical correlation will usually be close to, but not exactly, `+1` or `-1`.

The implementation therefore classifies according to the sign of the empirical correlation.

This is a statistical classifier for the ideal Bell-state model. A physical experiment would need confidence intervals, calibrated measurement errors, and a more complete noise model before making a robust state-identification claim.

### Noise and Measurement Processing

The JavaScript noise experiment modifies the measured binary result with configurable bit-flip probabilities.

This deliberately places the noise model around the measurement workflow rather than pretending that detector noise and quantum-state noise are mathematically identical.

The resulting counts can be used to observe the transition from near-perfect Bell correlation toward weaker empirical correlation as noise increases.

## C++ Laboratory Case Study

The C++ program models a small Bell-pair laboratory system.

The central components are:

- `BellState` for the four Bell-state identities
- `Basis` for Z- and X-basis measurements
- `ExperimentConfig` for shot count, target state, noise level, and seed
- `MeasurementCounts` for recorded outcomes
- `ExperimentResult` for derived correlations and identification
- `BellLaboratory` for experiment orchestration

The architecture separates preparation, measurement, statistical analysis, and reporting.

This is intentionally different from the Python and JavaScript implementations. Rather than emphasizing a broad educational simulator API, the C++ version treats the Bell-pair experiment as a coherent system with configuration validation and a controlled execution boundary.

### State Representation

The C++ state is:

`std::array<std::complex<double>, 4>`

The four entries correspond to:

`|00>`, `|01>`, `|10>`, `|11>`

Using a fixed-size array makes the two-qubit state representation explicit and avoids dynamic allocation for this small fixed problem.

The C++ implementation applies the Hadamard gate and CNOT directly to the state vector.

The CNOT matrix maps:

`|00> -> |00>`

`|01> -> |01>`

`|10> -> |11>`

`|11> -> |10>`

This establishes the control-target behavior needed for Bell-pair generation.

### Experiment Configuration

`ExperimentConfig` contains the parameters required for a run.

The validation layer rejects:

- Zero-shot experiments
- Negative noise probabilities
- Noise probabilities greater than one

The configuration boundary is important because invalid experimental parameters should fail before measurement processing begins.

### Repeated Measurements

A shot is treated as:

`prepare -> optional basis transformation -> measure -> optional stochastic detector/channel error -> record`

A new Bell pair is generated for every shot.

This is a critical implementation detail. Once a pair has been measured, it cannot be reused as though it were a freshly prepared pair.

The C++ implementation records all four possible two-bit outcomes even when ideal Bell-state preparation makes two of them theoretically impossible in a particular basis.

That design makes the data structure stable under noise and allows unexpected outcomes to be represented instead of discarded.

### Correlation Calculation

The program maps each outcome to a correlation contribution.

Equal bits contribute:

`+1`

Different bits contribute:

`-1`

The correlation is therefore:

`C = (N_same - N_opposite) / N_total`

For an ideal `Phi+` state measured in Z, the correlation approaches `+1`.

For an ideal `Psi-` state measured in Z, it approaches `-1`.

With finite shots, the result fluctuates around the theoretical value.

### Bell-State Identification

The C++ case study performs two measurement campaigns.

The first uses the Z basis.

The second uses the X basis.

The resulting correlation signs identify the ideal Bell state.

This creates a clear separation between the physical concepts:

- Preparation creates a specific entangled state.
- Measurement chooses an observable basis.
- Sampling produces experimental data.
- Correlation processing extracts a statistical signature.
- Classification maps that signature to a Bell-state identity.

## Why Two Measurement Bases Are Necessary

Computational-basis measurements alone cannot distinguish all four Bell states.

The pair:

`Phi+` and `Phi-`

has identical Z-basis probabilities.

Likewise:

`Psi+` and `Psi-`

has identical Z-basis probabilities.

The difference between the plus and minus states is encoded in relative phase.

Changing measurement basis converts phase information into observable outcome statistics.

This is a recurring principle in quantum measurement: information that is hidden in one basis can become visible in another basis.

The X-basis measurement is therefore not an optional cosmetic feature of the simulator. It is necessary for complete discrimination of the four Bell states using the correlation strategy implemented here.

## Entanglement Versus Classical Correlation

A Bell pair produces correlations that cannot be explained merely by saying that two classical bits were independently generated with matching probabilities.

For example, `Phi+` measured in Z always produces either `00` or `11`.

One could reproduce that single measurement distribution with a classical random process that chooses `00` and `11` with equal probability.

The distinction becomes visible when multiple incompatible measurement bases are considered.

The Bell-state structure preserves specific correlations across different observables, and suitable CHSH experiments can violate the classical local-hidden-variable bound.

The simulators therefore distinguish:

- A computational-basis outcome distribution
- Cross-basis correlation structure
- Entanglement of the underlying quantum state

These are related but not interchangeable properties.

## Finite-Shot Effects

The mathematical probabilities describe the ideal distribution.

An actual experiment collects a finite number of measurements.

For example, an ideal probability of `0.5` does not require a 4,000-shot experiment to contain exactly 2,000 observations. A finite sample can contain 1,987 observations in one category and 2,013 in another.

As the number of shots increases, empirical frequencies generally approach the theoretical probabilities.

This is why the programs report counts and calculated correlations instead of simply printing theoretical values.

The statistical experiment is separate from the underlying state preparation.

## Noise and Failure Conditions

The included noise models are intentionally limited.

A bit-flip model can transform:

`0 -> 1`

and:

`1 -> 0`

with a configurable probability.

For a Bell pair, independent flips can create outcomes that would have zero probability in the ideal model.

For example, an ideal `Phi+` Z-basis experiment supports `00` and `11`. Noise can introduce `01` and `10`.

Several practical failure modes must be distinguished:

| Failure mode | Effect |
|---|---|
| Incorrect state preparation | The intended Bell state is never created |
| Gate error | The state deviates before measurement |
| Measurement error | Recorded bits differ from the physical measurement result |
| Decoherence | Quantum coherence and correlations decay |
| Insufficient shots | Statistical estimates become unstable |
| Basis-selection error | Phase information may not be characterized correctly |
| Incorrect state reuse | Measurements are incorrectly treated as independent |
| Invalid probability configuration | The simulation itself becomes mathematically invalid |

The supplied programs intentionally model only a subset of these effects.

## Computational Complexity

For two qubits, the state vector contains only four complex amplitudes.

A generic state-vector simulator for `n` qubits requires:

`2^n`

complex amplitudes.

This exponential state-space growth is one of the principal limitations of classical full-state simulation of quantum systems.

For the two-qubit Bell-state examples, the computational cost is trivial. The same design would become increasingly expensive as the number of simulated qubits grows.

A simulator that repeatedly performs matrix-vector multiplication with a full `2^n x 2^n` operator can also incur substantial additional cost. Production simulators generally exploit gate locality, sparse structure, tensor representations, specialized kernels, or other optimizations instead of constructing dense matrices for every gate.

The educational implementations intentionally favor transparency over large-scale simulation performance.

## Numerical Considerations

Quantum amplitudes are represented using floating-point complex numbers.

Operations such as:

`1 / sqrt(2)`

cannot generally be represented exactly in binary floating-point arithmetic.

Consequently, a theoretically zero amplitude may appear as a tiny value such as `1e-16`.

The programs therefore use tolerance-based comparisons in places where exact equality would be inappropriate.

The Python implementation normalizes states after gate application. The C++ implementation follows the same approach.

Normalization is not a replacement for correct gate mathematics. It is a numerical safeguard that keeps accumulated floating-point error from causing a state to drift away from unit norm.

## Security and Randomness Considerations

The seeded random generators are appropriate for reproducible simulations.

They are not suitable for cryptographic key generation, secure protocols, or security-sensitive randomness.

A quantum experiment itself obtains measurement randomness from the physical measurement process. A classical simulator must instead model that randomness with a pseudo-random number generator unless a hardware entropy source is deliberately integrated.

Reproducibility and unpredictability have different requirements. Scientific debugging benefits from reproducibility, while cryptographic protocols require unpredictability.

## Practical Distinctions

### Bell-pair generation

Generation is the state-preparation process.

The essential circuit is:

`|00> -> H(q0) -> CNOT(q0, q1) -> |Phi+>`

Additional local Pauli operations select one of the other Bell states.

### Bell-pair measurement

Measurement converts the quantum state into classical data according to a selected basis.

The measurement basis determines which properties of the state become directly observable.

### Correlation analysis

Correlation processing converts individual two-bit outcomes into a statistical description.

For the implementations here:

`correlation = (same - opposite) / total`

### Bell-state identification

Identification combines measurements from different bases.

The Z-basis relationship distinguishes the `Phi` family from the `Psi` family.

The X-basis relationship distinguishes the plus and minus phase variants.

This is why state preparation, measurement, correlation analysis, and identification are represented as separate mechanisms rather than one combined operation.

## Common Implementation Mistakes

### Measuring the same pair repeatedly

After a projective measurement, the state has collapsed. Treating subsequent measurements as independent samples of the original Bell state gives incorrect statistics.

The correct simulation prepares a fresh pair for every shot.

### Confusing amplitudes with probabilities

An amplitude such as:

`1 / sqrt(2)`

corresponds to probability:

`1/2`

because measurement probability uses the squared magnitude.

### Ignoring relative phase

`Phi+` and `Phi-` have the same Z-basis probabilities.

Their relative phase is therefore invisible if the experiment uses only Z-basis measurements.

### Assuming every correlated distribution proves entanglement

A classical random source can reproduce some individual Bell-basis measurement distributions.

Entanglement concerns the structure of the quantum state and its behavior across compatible sets of measurements, not merely one matching-bit frequency.

### Reusing the wrong basis

If the goal is to identify all four Bell states, measuring only in the computational basis is insufficient.

### Treating a simple bit-flip model as a complete hardware model

Real devices can exhibit multiple independent and correlated error mechanisms. A single stochastic flip probability is useful for demonstrating robustness but does not reproduce a complete physical noise model.

## Production-Oriented Considerations

A production quantum software stack would generally separate:

- Circuit construction
- Backend selection
- Device execution
- Measurement acquisition
- Calibration data
- Noise characterization
- Statistical analysis
- State reconstruction
- Experiment metadata
- Result validation

The educational programs combine some of these layers to remain self-contained.

A hardware-facing implementation would also need to account for physical qubit connectivity, native gate sets, gate durations, readout calibration, decoherence times, compiler transformations, shot scheduling, backend failures, and measurement error mitigation where appropriate.

State-vector simulation should also not be confused with a physical quantum processor. The simulator calculates the mathematical model on a classical machine.

## Relationship Between the Three Implementations

The implementations share the same quantum foundations but emphasize different engineering structures.

The Python program is broadest in mathematical coverage. It includes state vectors, density matrices, partial traces, concurrence, noise, measurement sampling, and CHSH-style expectation values.

The JavaScript program treats the experiment as an event-driven software process. Its `BellExperiment` object demonstrates how preparation, measurement, and completion can produce observable application events while still using a self-contained state-vector model.

The C++ program treats the experiment as a structured laboratory system. Its configuration, result types, measurement engine, validation layer, and laboratory controller demonstrate how the mathematical model can be embedded into a strongly typed technical application.

None of the implementations requires an external quantum-computing package. The gate operations, state representation, sampling, and measurement logic are intentionally visible in the source.

## Running the Implementations

The Python program can be executed directly with a Python 3 interpreter:

`python bell_states.py`

The JavaScript program can be executed with Node.js:

`node bell_states.js`

The C++ program requires a C++17-compatible compiler. A typical compilation command is:

`g++ -std=c++17 -O2 bell_states.cpp -o bell_states`

The resulting executable can then be run as:

`./bell_states`

On Windows with a compatible compiler, the generated executable can be invoked with:

`bell_states.exe`

The programs use only standard-library facilities and therefore do not require third-party quantum SDKs.

## Expected Experimental Behavior

For ideal Bell-state generation:

- `Phi+` produces same Z outcomes and same X outcomes.
- `Phi-` produces same Z outcomes and opposite X outcomes.
- `Psi+` produces opposite Z outcomes and same X outcomes.
- `Psi-` produces opposite Z outcomes and opposite X outcomes.

With enough shots, the empirical correlation values approach the corresponding ideal signs.

When noise is introduced, previously forbidden outcomes can appear and the magnitude of the empirical correlation generally decreases.

The exact sampled counts depend on the random sequence and shot count, even when the theoretical probabilities are fixed.

## Limitations

The programs simulate only two qubits. They are therefore unsuitable as performance demonstrations for large quantum circuits.

The noise models are intentionally simplified and should not be interpreted as calibrated device models.

The Bell-state classifier assumes the experiment is intended to contain one of the four ideal Bell states. It does not perform general quantum-state tomography.

The CHSH implementation calculates expectation values from an ideal state vector rather than modeling a complete laboratory measurement apparatus.

Floating-point arithmetic introduces small numerical errors, so exact symbolic identities are not assumed during validation.

The implementations also do not model physical qubit layout, hardware-specific native gates, pulse-level control, calibration drift, or realistic detector electronics.

## Technical Takeaway

A Bell pair is generated by combining superposition with conditional interaction.

The Hadamard gate creates the required superposition, while CNOT correlates the second qubit with the first. Local Pauli operations select the remaining Bell states.

Measurement then converts the quantum state into classical outcomes. The measurement basis determines which properties of the state are visible. Z-basis measurements expose one correlation structure, while X-basis measurements reveal information about relative phase.

Repeated measurements turn the underlying probabilities into empirical data. Correlation analysis then provides a compact way to characterize the observed Bell-pair behavior.

The Python, JavaScript, and C++ implementations demonstrate the same physical concepts through different software architectures: mathematical simulation, event-driven experiment processing, and a strongly typed laboratory-style execution engine.
