# Quantum Noise: Sources and Models of Noise

## 1. Technical Scope

Quantum noise describes unwanted physical interactions, control imperfections, and measurement errors that affect quantum states and quantum operations.

An isolated qubit can maintain a coherent superposition. In practical quantum devices, interactions with the environment and imperfections in control electronics change the state, reduce coherence, and affect measurement outcomes.

This implementation studies the mathematical and computational representation of quantum noise through five complementary technical implementations:

| Deliverable | Engineering purpose |
|---|---|
| Python | Density-matrix simulation and Kraus operators |
| JavaScript | Bloch-vector transformations and event-driven channel execution |
| C++17 | Efficient quantum noise simulation using typed channel models |
| Java 17 | Enterprise-oriented experiment and calibration management |
| PostgreSQL | Relational storage, validation, and experiment governance |

The implementations focus on single-qubit noise models. They do not claim to simulate a complete multi-qubit quantum processor.

## 2. Mathematical Representation of a Qubit

A pure qubit state can be represented as:

\[
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
\]

where:

\[
|\alpha|^2+|\beta|^2=1
\]

Here, \(\alpha\) and \(\beta\) are complex probability amplitudes.

The density matrix is:

\[
\rho=|\psi\rangle\langle\psi|
\]

For a single qubit:

\[
\rho=
\begin{bmatrix}
\rho_{00}&\rho_{01}\\
\rho_{10}&\rho_{11}
\end{bmatrix}
\]

A valid density matrix must satisfy:

- Hermiticity: \(\rho=\rho^\dagger\)
- Unit trace: \(\operatorname{Tr}(\rho)=1\)
- Positive semidefiniteness: all eigenvalues are nonnegative.

The Bloch representation expresses the same state as:

\[
\rho=\frac{1}{2}(I+xX+yY+zZ)
\]

The Bloch vector is:

\[
\vec r=(x,y,z)
\]

Its magnitude must satisfy:

\[
x^2+y^2+z^2\leq1
\]

Pure states lie on the Bloch sphere surface. Mixed states lie inside it.

The Python implementation uses density matrices, while JavaScript, C++17, and Java 17 use Bloch-vector transformations.

## 3. Sources of Quantum Noise

Quantum noise arises from several physically distinct mechanisms.

### 3.1 Environmental energy exchange

A qubit can exchange energy with its surroundings.

For example, an excited qubit can transition from:

\[
|1\rangle\rightarrow|0\rangle
\]

This mechanism produces energy relaxation and is characterized by the relaxation time \(T_1\).

Typical contributors include:

- Coupling to electromagnetic environments.
- Energy loss through control and readout structures.
- Material defects.
- Unwanted environmental interactions.

### 3.2 Environmental phase fluctuations

Environmental fluctuations can change the relative phase between computational basis states.

These fluctuations reduce off-diagonal density-matrix elements without necessarily changing the computational-basis populations.

This mechanism is called pure dephasing.

It is characterized by the pure-dephasing time \(T_\phi\).

### 3.3 Thermal fluctuations

A quantum system can exchange energy with an environment that has a nonzero excited-state population.

Unlike zero-temperature amplitude damping, thermal relaxation can produce both downward and upward transitions.

### 3.4 Control imperfections

Quantum gates depend on accurate control pulses.

Imperfect pulse duration, amplitude, or phase can introduce systematic errors.

Examples include:

- Incorrect rotation angles.
- Frequency detuning.
- Phase miscalibration.
- Unwanted control-axis rotations.

These errors can be coherent rather than stochastic.

### 3.5 Measurement imperfections

Quantum measurement converts a quantum state into a classical result.

A measurement apparatus can report the wrong computational-basis outcome.

Readout errors are commonly described through a confusion matrix rather than a quantum evolution channel.

## 4. Principal Quantum Noise Models

### 4.1 Amplitude damping

Amplitude damping models energy relaxation.

Its Kraus operators are:

\[
K_0=
\begin{bmatrix}
1&0\\
0&\sqrt{1-\gamma}
\end{bmatrix}
\]

\[
K_1=
\begin{bmatrix}
0&\sqrt{\gamma}\\
0&0
\end{bmatrix}
\]

The resulting state is:

\[
\rho'=\sum_i K_i\rho K_i^\dagger
\]

The parameter \(\gamma\) represents the probability of energy relaxation during the modeled interval.

For a constant relaxation time:

\[
\gamma=1-e^{-t/T_1}
\]

The ground state remains unchanged. The excited-state population decreases.

### 4.2 Pure dephasing

Pure dephasing changes coherence without directly changing populations.

A stochastic phase-flip representation uses:

\[
K_0=\sqrt{1-p}I
\]

\[
K_1=\sqrt p Z
\]

The off-diagonal elements are multiplied by:

\[
1-2p
\]

The computational-basis populations remain unchanged.

### 4.3 Depolarizing noise

Depolarizing noise represents an isotropic random Pauli-error model.

Its channel is:

\[
\mathcal E(\rho)=
(1-p)\rho+
\frac p3
(X\rho X+Y\rho Y+Z\rho Z)
\]

The Bloch vector is scaled by:

\[
\vec r'=
\left(1-\frac{4p}{3}\right)\vec r
\]

The parameter \(p\) is the total probability assigned to the three nonidentity Pauli errors in this convention.

Different software libraries use different depolarizing-parameter conventions. Comparisons must use the same convention.

### 4.4 Bit-flip noise

Bit-flip noise represents a probabilistic Pauli-X operation.

\[
\mathcal E(\rho)=
(1-p)\rho+pX\rho X
\]

Its Bloch transformation is:

\[
(x,y,z)\rightarrow
(x,(1-2p)y,(1-2p)z)
\]

It changes computational-basis populations.

### 4.5 Phase-flip noise

Phase-flip noise represents a probabilistic Pauli-Z operation.

\[
\mathcal E(\rho)=
(1-p)\rho+pZ\rho Z
\]

Its Bloch transformation is:

\[
(x,y,z)\rightarrow
((1-2p)x,(1-2p)y,z)
\]

It changes phase coherence without changing computational-basis populations.

### 4.6 Coherent rotation error

A systematic Z-axis rotation error can be represented as:

\[
U_Z(\theta)=e^{-i\theta Z/2}
\]

The density matrix transforms as:

\[
\rho'=U_Z(\theta)\rho U_Z^\dagger(\theta)
\]

The corresponding Bloch transformation is:

\[
x'=x\cos\theta-y\sin\theta
\]

\[
y'=x\sin\theta+y\cos\theta
\]

\[
z'=z
\]

A coherent error must not be confused with stochastic phase-flip noise. Repeated coherent errors can accumulate systematically.

### 4.7 Thermal relaxation

Generalized amplitude damping models interaction with an environment having an equilibrium excited-state population \(q\).

Its Bloch transformation is:

\[
x'=\sqrt{1-\gamma}x
\]

\[
y'=\sqrt{1-\gamma}y
\]

\[
z'=\gamma(1-2q)+(1-\gamma)z
\]

When \(q=0\), this reduces to ordinary amplitude damping.

### 4.8 Measurement readout errors

Readout errors are represented through:

\[
M=
\begin{bmatrix}
1-p_{01}&p_{10}\\
p_{01}&1-p_{10}
\end{bmatrix}
\]

Here:

- \(p_{01}\): probability of reporting 1 when the actual result is 0.
- \(p_{10}\): probability of reporting 0 when the actual result is 1.

The measurement confusion matrix operates on classical outcome probabilities.

It is conceptually different from a quantum noise channel acting on the density matrix.

## 5. Relationship Between T1, T2, and Tphi

The principal coherence relationship is:

\[
\frac{1}{T_2}=
\frac{1}{2T_1}+\frac{1}{T_\phi}
\]

Consequently:

\[
T_2\leq2T_1
\]

The pure-dephasing contribution is:

\[
\frac{1}{T_\phi}=
\frac{1}{T_2}-\frac{1}{2T_1}
\]

For a physical calibration, the implementation validates the relationship before calculating noise probabilities.

The pure-dephasing probability over duration \(t\) is:

\[
p_\phi=
\frac{1-e^{-t/T_\phi}}{2}
\]

The amplitude-damping probability is:

\[
\gamma=1-e^{-t/T_1}
\]

These equations assume exponential relaxation and dephasing under the modeled conditions.

The total coherence decay must not be counted twice. The pure-dephasing channel is calculated after accounting for the contribution of energy relaxation.

## 6. Implementation Architecture

### 6.1 Python: Density-matrix simulation

The Python implementation provides the most direct mathematical representation.

Important components:

| Component | Responsibility |
|---|---|
| `NoiseParameters` | Validates noise and coherence parameters |
| `NoiseType` | Defines supported channel categories |
| `density_matrix()` | Constructs a normalized qubit state |
| `apply_kraus()` | Applies completely positive quantum operations |
| `amplitude_damping()` | Constructs relaxation operators |
| `pure_dephasing()` | Constructs stochastic phase-noise operators |
| `depolarizing()` | Constructs the Pauli depolarizing channel |
| `thermal_relaxation()` | Constructs generalized amplitude-damping operators |
| `measurement_with_readout_error()` | Applies classical readout confusion |
| `fidelity_pure_state()` | Evaluates overlap with a pure target |

The Kraus representation is:

\[
\mathcal E(\rho)=\sum_i K_i\rho K_i^\dagger
\]

For a trace-preserving channel:

\[
\sum_i K_i^\dagger K_i=I
\]

The implementation checks density-matrix normalization, Hermiticity, and positivity.

For a two-dimensional density matrix, trace, Hermiticity, nonnegative diagonal elements, and determinant provide a practical positivity check.

### 6.2 JavaScript: Event-driven noise pipeline

The JavaScript implementation uses Bloch-vector transformations.

The `NoiseChannel` class encapsulates channel identity, model type, and immutable parameters.

The `NoisePipeline` class manages channel registration, execution, and event reporting.

Important events include:

- `channelAdded`
- `channelRemoved`
- `channelApplied`
- `executionCompleted`

The execution trace records the state after each channel.

This makes it possible to identify which modeled mechanism contributes to the final loss of coherence.

The implementation uses asynchronous file writing through Node.js filesystem APIs.

### 6.3 C++17: Typed simulation engine

The C++ implementation uses explicit domain types.

`BlochVector` represents a physical qubit state.

`NoiseType` identifies the channel category.

`NoiseChannel` encapsulates the state transformation.

`ThermalRelaxationChannel` separates thermal dynamics from zero-temperature amplitude damping.

`QuantumNoisePipeline` applies registered channels in sequence.

This design provides compile-time structure and avoids unnecessary dynamic allocation during individual state transformations.

The implementation validates the physical Bloch-sphere constraint after each channel.

### 6.4 Java 17: Experiment management

The Java implementation separates the simulation model from the experiment lifecycle.

The principal components are:

| Component | Responsibility |
|---|---|
| `BlochVector` | Immutable quantum-state representation |
| `NoiseParameters` | Parameter validation |
| `CoherenceCalibration` | T1/T2-derived probability calculations |
| `QuantumChannel` | Channel contract |
| `StandardNoiseChannel` | Noise transformations |
| `NoiseExperiment` | Experiment lifecycle |
| `ReadoutCalibration` | Measurement assignment correction |
| `ExperimentReport` | Immutable execution result |

The experiment lifecycle is:

CREATED → VALIDATED → EXECUTED

A failed execution transitions to FAILED.

Channel registration is restricted after validation. This prevents changes to the experiment configuration after execution has been authorized.

### 6.5 PostgreSQL: Experimental data governance

The relational database models quantum hardware, calibration records, noise mechanisms, and experimental observations.

The principal relationships are:

Quantum Device
→ Qubits
→ Coherence Calibrations
→ Noise Experiments
→ Applied Noise Channels
→ Observations
→ Quality Reports

Separate tables preserve the distinction between:

- Physical noise sources.
- Mathematical channel models.
- Device-specific calibration values.
- Experimental configurations.
- Measured observations.
- Experiment acceptance outcomes.

Check constraints enforce physical parameter limits.

Foreign keys preserve relationships between devices, qubits, calibration records, and experiments.

Triggers validate channel parameters and experiment configuration.

The experiment lifecycle function performs controlled state transitions using row-level locking.

Views provide reusable reporting for calibration quality, noise-channel distribution, and experimental results.

## 7. Noise Channel Comparison

| Model | Primary effect | Main parameter | Physical or mathematical interpretation |
|---|---|---|---|
| Amplitude damping | Population relaxation | gamma | Energy loss |
| Pure dephasing | Coherence reduction | p | Environmental phase fluctuations |
| Depolarizing | Isotropic state contraction | p | Random Pauli errors |
| Bit flip | Computational-basis inversion | p | Pauli X errors |
| Phase flip | Relative phase inversion | p | Pauli Z errors |
| Coherent rotation | Systematic state rotation | theta | Control miscalibration |
| Thermal relaxation | Upward and downward transitions | gamma, q | Finite-temperature environment |
| Readout error | Incorrect classical result | p01, p10 | Measurement assignment error |

## 8. Fidelity and Purity

Fidelity measures the agreement between a simulated state and a target state.

For a pure target state:

\[
F(\rho,|\psi\rangle)=
\langle\psi|\rho|\psi\rangle
\]

For two Bloch vectors, when the target is pure:

\[
F=\frac{1+\vec r\cdot\vec r_{\text{target}}}{2}
\]

Purity measures how mixed a quantum state is:

\[
\operatorname{Tr}(\rho^2)
\]

For a single-qubit Bloch representation:

\[
\operatorname{Tr}(\rho^2)=
\frac{1+x^2+y^2+z^2}{2}
\]

Interpretation:

- Purity equals one for pure states.
- Purity is below one for mixed states.
- Purity equals one-half for the maximally mixed single-qubit state.

A reduction in purity indicates increased mixing, but fidelity and purity measure different properties.

A state can have high purity while still being far from the intended target state.

## 9. Execution Workflows

### 9.1 Python

1. Construct a normalized quantum state.
2. Select the required noise channel.
3. Construct its Kraus operators.
4. Apply the channel to the density matrix.
5. Validate the output state.
6. Calculate fidelity and measurement probabilities.
7. Export experiment results as JSON.

### 9.2 JavaScript

1. Construct the initial Bloch vector.
2. Register noise channels.
3. Attach execution event listeners.
4. Execute the channel pipeline.
5. Capture intermediate states.
6. Evaluate fidelity and purity.
7. Save the report asynchronously.

### 9.3 C++17

1. Construct a physical Bloch vector.
2. Create typed channel objects.
3. Register channels with the pipeline.
4. Execute transformations sequentially.
5. Apply coherence calibration.
6. Evaluate measurement errors.
7. Validate the final state.

### 9.4 Java 17

1. Create an experiment with initial and target states.
2. Load T1 and T2 calibration values.
3. Register channel objects.
4. Validate the experiment.
5. Execute the experiment.
6. Generate an immutable report.
7. Evaluate readout calibration.

### 9.5 PostgreSQL

1. Register devices and physical qubits.
2. Store coherence calibration records.
3. Register noise sources and models.
4. Create an experiment.
5. Register applied noise channels.
6. Store measurement observations.
7. Execute experiment lifecycle transitions.
8. Retrieve quality and calibration reports.

## 10. Validation and Failure Conditions

The implementations enforce the following conditions:

| Condition | Validation |
|---|---|
| Invalid noise probability | Reject values outside the permitted interval |
| Invalid T1 | Require positive relaxation time |
| Invalid T2 | Require positive coherence time |
| Unphysical T1/T2 relationship | Require T2 no greater than 2T1 |
| Invalid Bloch vector | Reject magnitude greater than one |
| Invalid density matrix | Check trace, Hermiticity, and positivity |
| Invalid readout probability | Require probabilities in [0, 1] |
| Duplicate channel ID | Reject duplicate registrations |
| Empty experiment | Require at least one channel |
| Invalid experiment transition | Enforce lifecycle rules |
| Missing calibration | Validate referenced calibration records |
| Invalid database relationship | Enforce foreign-key constraints |

## 11. Performance Considerations

The Bloch representation requires only three real coordinates per single-qubit state.

Each implemented channel uses a constant number of arithmetic operations.

Consequently, an individual channel transformation has:

\[
O(1)
\]

time and space complexity for a single qubit.

A pipeline containing \(n\) channels has:

\[
O(n)
\]

time complexity.

The density-matrix implementation uses small 2 × 2 complex matrices.

For a general \(d\)-dimensional quantum system, density matrices require \(O(d^2)\) storage, and direct matrix multiplication generally requires \(O(d^3)\) operations.

For \(n\) qubits:

\[
d=2^n
\]

Therefore, full density-matrix simulation becomes expensive as the number of qubits increases.

The single-qubit implementations are educational and characterization models, not scalable substitutes for large-scale quantum simulation frameworks.

## 12. Security and Data Integrity

Quantum experiment records can contain sensitive hardware calibration and operational information.

The database design supports integrity through:

- Primary and foreign keys.
- Parameter-range constraints.
- Controlled experiment transitions.
- Timestamped calibration records.
- Separate device and experiment entities.
- Referential integrity.
- Transactional updates.

A production deployment should also implement:

- Role-based database permissions.
- Restricted execution privileges.
- Encrypted network connections.
- Protected calibration records.
- Audit logging.
- Backup and recovery procedures.
- Separation of experiment operators and administrators.

Database validation does not replace application-level authorization.

The PostgreSQL implementation demonstrates data integrity and workflow control. It does not provide a complete production identity-management or access-control system.

## 13. Important Modeling Limitations

The implemented channels are simplified models.

They do not fully represent every physical noise process in a quantum processor.

Important omitted effects include:

- Leakage outside the computational subspace.
- Crosstalk between neighboring qubits.
- Correlated multi-qubit noise.
- Non-Markovian environmental dynamics.
- Frequency-dependent noise.
- Time-dependent control errors.
- Spectral noise characteristics.
- Measurement backaction beyond the specified readout model.

The thermal model assumes a specified equilibrium excited-state population.

The T1/T2 relationship assumes the exponential Markovian relaxation and dephasing model used in the implementations.

The depolarizing channel uses the convention in which each nonidentity Pauli operator has probability p/3.

These assumptions must be considered when comparing simulated results with experimental hardware measurements.

## 14. Practical Applications

The implemented models support the following learning and research activities:

- Single-qubit noise characterization.
- Relaxation and coherence analysis.
- Quantum gate-error investigation.
- Readout calibration.
- Density-matrix validation.
- Quantum-state fidelity estimation.
- Comparative noise-channel experiments.
- Hardware calibration record management.
- Simulation pipeline development.
- Experimental result reporting.

The separation of physical mechanisms, mathematical channels, device calibrations, and measurement errors provides a consistent basis for studying quantum noise without treating every observed error as the same physical phenomenon.
