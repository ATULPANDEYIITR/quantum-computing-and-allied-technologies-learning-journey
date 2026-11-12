# Quantum Decoherence: T1, T2 and Environmental Effects

## Project Overview

This project studies quantum decoherence through the relationship between energy relaxation, phase coherence and environmental disturbances.

A qubit is a quantum two-level system. Its state can be represented as a point inside or on the surface of the Bloch sphere. Interactions with the surrounding environment change its population distribution and reduce its quantum coherence.

The project implements mathematical models, numerical simulations, experiment management and relational data storage across Python, JavaScript, C++17, Java 17 and PostgreSQL.

The central distinction is between T1 and T2:

- T1 describes the relaxation of energy populations.
- T2 describes the decay of transverse quantum coherence.
- T_phi describes pure dephasing that reduces coherence without requiring energy relaxation.

## 1. Quantum Decoherence

Quantum decoherence is the loss of observable phase relationships between quantum-state components due to interactions with environmental degrees of freedom.

A qubit can initially exist in a coherent superposition:

\[
|\psi\rangle = \alpha |0\rangle + \beta |1\rangle
\]

where:

\[
|\alpha|^2+|\beta|^2=1
\]

The corresponding density matrix is:

\[
\rho =
\begin{bmatrix}
|\alpha|^2 & \alpha\beta^*\\
\alpha^*\beta & |\beta|^2
\end{bmatrix}
\]

The diagonal elements represent state populations. The off-diagonal elements represent quantum coherence.

Decoherence reduces the off-diagonal elements and can also change the population distribution.

### Density Matrix and Bloch Sphere

A single-qubit density matrix can be expressed as:

\[
\rho =
\frac{1}{2}
(I+x\sigma_x+y\sigma_y+z\sigma_z)
\]

where:

- \(I\) is the identity matrix.
- \(\sigma_x\), \(\sigma_y\) and \(\sigma_z\) are Pauli matrices.
- \(x,y,z\) are Bloch-vector coordinates.

The physical-state condition is:

\[
x^2+y^2+z^2\leq 1
\]

The Bloch-vector magnitude is:

\[
r=\sqrt{x^2+y^2+z^2}
\]

A pure state has \(r=1\), while a mixed state has \(r<1\).

The purity is:

\[
\operatorname{Tr}(\rho^2)
=
\frac{1+x^2+y^2+z^2}{2}
\]

Purity ranges from 0.5 to 1 for a single qubit.

## 2. T1: Energy Relaxation

T1 is the longitudinal relaxation time.

It describes how the population of an excited quantum state approaches its equilibrium population through interactions with the environment.

For a qubit relaxing towards its ground state at zero temperature:

\[
P_1(t)=P_1(0)e^{-t/T_1}
\]

where:

- \(P_1(0)\) is the initial excited-state population.
- \(P_1(t)\) is the excited-state population at time \(t\).
- \(T_1\) is the energy relaxation time.

The Bloch-vector longitudinal component follows:

\[
z(t)=1-[1-z(0)]e^{-t/T_1}
\]

For a nonzero equilibrium excited-state population \(p_{\mathrm{eq}}\):

\[
z_{\mathrm{eq}}=1-2p_{\mathrm{eq}}
\]

\[
z(t)=z_{\mathrm{eq}}+
[z(0)-z_{\mathrm{eq}}]e^{-t/T_1}
\]

### Physical Interpretation

A smaller T1 indicates faster energy relaxation.

A larger T1 indicates that the qubit retains its excited-state population for longer.

Energy relaxation is associated with processes such as:

- Coupling to electromagnetic modes.
- Interaction with material defects.
- Thermal environmental excitation and relaxation.
- Unwanted coupling to control and readout circuitry.

T1 is especially relevant when evaluating how long quantum information encoded in population differences can persist.

## 3. T2: Transverse Coherence Decay

T2 is the transverse relaxation or coherence-decay time.

It measures the decay of phase relationships between the computational basis states.

The transverse Bloch components evolve as:

\[
x(t)=x(0)e^{-t/T_2}
\]

\[
y(t)=y(0)e^{-t/T_2}
\]

The transverse coherence magnitude is:

\[
C(t)=\sqrt{x(t)^2+y(t)^2}
\]

For exponential decay:

\[
C(t)=C(0)e^{-t/T_2}
\]

T2 characterizes how quickly a qubit loses phase coherence.

A qubit can lose coherence even when its energy population remains approximately unchanged.

This distinction is important because phase information is necessary for quantum interference and many quantum-computing operations.

## 4. T_phi: Pure Dephasing

Pure dephasing is a coherence-loss mechanism that does not require population relaxation.

It arises when environmental fluctuations change the relative phase accumulated by the qubit states.

The standard relationship between the three time constants is:

\[
\frac{1}{T_2}
=
\frac{1}{2T_1}
+
\frac{1}{T_\phi}
\]

Therefore:

\[
\frac{1}{T_\phi}
=
\frac{1}{T_2}
-
\frac{1}{2T_1}
\]

The pure dephasing time is:

\[
T_\phi=
\frac{1}{
\frac{1}{T_2}-\frac{1}{2T_1}
}
\]

The physical consistency condition is:

\[
T_2\leq 2T_1
\]

### Interpretation

| Relationship | Interpretation |
|---|---|
| \(T_2=2T_1\) | No additional pure dephasing in the standard Markovian model |
| \(T_2<2T_1\) | Additional pure dephasing contributes to coherence loss |
| \(T_2>T_2^{\mathrm{max}}=2T_1\) | Physically inconsistent with the standard model |

When \(T_2=2T_1\), the pure dephasing rate is zero and \(T_\phi\) is infinite.

When T2 is substantially smaller than 2T1, pure dephasing makes a significant contribution.

## 5. Environmental Effects

A quantum system is never completely independent of its physical surroundings.

Environmental interactions introduce fluctuations that influence energy relaxation, phase coherence and measurement outcomes.

The implementations represent several environmental categories.

### Thermal Environment

<text>Temperature affects the interaction between a qubit and its surroundings.</text>

Thermal occupation can produce both upward and downward transitions between energy levels.

For a two-level system in thermal equilibrium:

\[
p_1^{\mathrm{eq}}
=
\frac{1}{
1+e^{\hbar\omega/(k_BT)}
}
\]

where:

- \(\hbar\) is the reduced Planck constant.
- \(\omega\) is the qubit angular frequency.
- \(k_B\) is the Boltzmann constant.
- \(T\) is absolute temperature.

The simulations accept an equilibrium excited-state population directly rather than deriving it from frequency and temperature.

### Magnetic Noise

Magnetic-field fluctuations can change the qubit transition frequency and cause phase instability.

This is particularly relevant to systems whose energy levels or transition frequencies depend on magnetic fields.

### Electric Noise

Electric-field fluctuations can influence qubit energy levels, transition frequencies and coupling characteristics.

The magnitude of the effect depends on the device architecture and its sensitivity to electric fields.

### Vibrational Effects

Mechanical vibrations can influence physical device structures and their electromagnetic or material properties.

These disturbances may contribute to changes in qubit frequency, coupling and coherence.

### Mixed Environmental Effects

Real devices can experience several disturbance sources simultaneously.

Mixed environmental profiles represent combined disturbances rather than assuming that every environmental mechanism has an independent, directly measurable effect on T1 or T2.

## 6. Mathematical Simulation Model

The implementations use a phenomenological Bloch-vector model.

For the transverse components:

\[
x(t)=x_0e^{-t/T_2}
\]

\[
y(t)=y_0e^{-t/T_2}
\]

For the longitudinal component:

\[
z(t)=z_{\mathrm{eq}}+
(z_0-z_{\mathrm{eq}})e^{-t/T_1}
\]

The complete state is:

\[
\vec r(t)=
\begin{bmatrix}
x(t)\\
y(t)\\
z(t)
\end{bmatrix}
\]

The model assumes exponential relaxation with constant T1 and T2.

It does not explicitly simulate microscopic environmental degrees of freedom, non-Markovian dynamics, individual noise trajectories or a full quantum bath.

### Example Configuration

| Parameter | Value |
|---|---:|
| T1 | 100 microseconds |
| T2 | 60 microseconds |
| Initial X | 1 |
| Initial Y | 0 |
| Initial Z | 0 |
| Equilibrium excited population | 0.01 |
| Simulation duration | 300 microseconds |
| Measurement steps | 300 |

The pure dephasing time is:

\[
T_\phi=
\frac{1}{
\frac{1}{60}-\frac{1}{200}
}
\]

\[
T_\phi\approx85.7143\ \mu s
\]

The transverse coherence at 60 microseconds is:

\[
C(60)=e^{-60/60}
\]

\[
C(60)\approx0.367879
\]

This demonstrates the exponential decay of phase coherence.

## 7. Python Implementation

The Python implementation provides the primary numerical simulation.

### Main Components

| Component | Responsibility |
|---|---|
| `Environment` | Environmental classification |
| `DecoherenceParameters` | T1, T2 and environmental parameters |
| `QubitState` | Bloch-vector representation |
| `Measurement` | Time-dependent observations |
| `DecoherenceSimulator` | Quantum-state evolution |
| `fit_exponential_decay` | Estimation of exponential decay time |
| `simulate_measurement_shots` | Computational-basis measurement sampling |

### State Validation

The implementation rejects:

- Negative relaxation times.
- Non-finite numerical values.
- T2 values exceeding twice T1.
- Bloch vectors outside the unit sphere.
- Invalid equilibrium populations.
- Negative simulation durations.
- Invalid measurement counts.

### Exponential Fitting

The implementation estimates T2 using logarithmic linear regression.

Starting from:

\[
C(t)=C_0e^{-t/T_2}
\]

Taking logarithms gives:

\[
\ln C(t)=\ln C_0-\frac{t}{T_2}
\]

The regression slope is:

\[
m=-\frac{1}{T_2}
\]

Therefore:

\[
T_2=-\frac{1}{m}
\]

This approach estimates T2 from ideal simulated coherence measurements.

Experimental data may require offset correction, uncertainty estimation, outlier handling and nonlinear fitting.

### Measurement Sampling

The measurement function samples the computational basis.

The probabilities are:

\[
P(0)=\frac{1+z}{2}
\]

\[
P(1)=\frac{1-z}{2}
\]

Finite measurement shots introduce statistical sampling variation.

## 8. JavaScript Implementation

The JavaScript implementation provides an event-driven experiment engine.

### Architecture

| Component | Responsibility |
|---|---|
| `DecoherenceConfig` | Immutable experiment configuration |
| `BlochState` | State validation and derived quantities |
| `DecoherenceExperiment` | Experiment execution |
| `EventEmitter` | Measurement and completion events |
| `estimateT2()` | Coherence-decay estimation |
| `sampleMeasurement()` | Reproducible measurement sampling |
| `exportJSON()` | Experiment data persistence |

### Event-Driven Execution

The experiment emits:

- `measurement`: generated observation.
- `completed`: successful experiment completion.
- `experimentError`: execution failure.

The asynchronous execution periodically yields to the Node.js event loop.

This allows other event-loop operations to proceed while long simulations are running.

### Data Export

The implementation exports:

- Experiment configuration.
- Environmental classification.
- T1 and T2.
- Derived T_phi.
- Measurement time.
- Bloch-vector coordinates.
- Coherence.
- Purity.
- Excited-state probability.

The export is structured JSON.

## 9. C++17 Implementation

The C++17 implementation emphasizes numerical computation, domain modeling and explicit resource management.

### Main Components

| Component | Responsibility |
|---|---|
| `Environment` | Strongly typed environment classification |
| `DecoherenceParameters` | Physical parameter validation |
| `BlochVector` | Quantum-state representation |
| `Observation` | Time-series data |
| `DecoherenceEngine` | State evolution and simulation |
| `estimateDecayTime()` | Regression-based T2 estimation |
| `exportCSV()` | CSV data export |

### Engineering Decisions

The simulation stores observations in an STL vector.

Memory is reserved using `reserve()` before the simulation loop to reduce repeated allocations.

The numerical model uses standard mathematical functions from `<cmath>`.

Exceptions handle invalid inputs and failed file operations.

CSV export provides a simple interface for further numerical analysis.

### Complexity

For N time steps:

| Operation | Complexity |
|---|---|
| Single state evolution | O(1) |
| Complete simulation | O(N) |
| Observation storage | O(N) |
| Exponential regression | O(N) |
| CSV export | O(N) |

The simulation uses constant computational work per observation.

## 10. Java 17 Implementation

The Java implementation represents an experiment-monitoring service with explicit domain types and controlled lifecycle transitions.

### Domain Model

| Type | Responsibility |
|---|---|
| `Environment` | Environmental category |
| `ExperimentStatus` | Experiment lifecycle |
| `Parameters` | Immutable physical configuration |
| `QuantumState` | Immutable Bloch vector |
| `Observation` | Measurement record |
| `ExperimentReport` | Final experiment report |
| `ExperimentPolicy` | Validation contract |
| `StandardExperimentPolicy` | Standard experiment validation |
| `ExperimentService` | Experiment execution and analysis |

### Lifecycle

The experiment follows:

`CREATED → RUNNING → COMPLETED`

Failure produces:

`RUNNING → FAILED`

The implementation prevents restarting a completed or failed experiment.

### Immutability

Java records represent immutable parameter, state and observation objects.

The observation accessor returns an immutable copy of the recorded observations.

This reduces accidental modification of experiment results.

### Failure Handling

The implementation handles:

- Invalid physical parameters.
- Invalid Bloch vectors.
- Invalid experiment durations.
- Excessive measurement counts.
- Repeated execution attempts.
- Regression failures.
- File-export failures.

## 11. PostgreSQL Database Architecture

The PostgreSQL implementation models a quantum laboratory experiment-management workflow.

### Entity Relationships

`Quantum Devices`

→ `Qubits`

→ `Decoherence Experiments`

→ `Environmental Conditions`

→ `Decoherence Measurements`

→ `Relaxation Analysis`

The experiment event table records lifecycle changes.

### Database Tables

| Table | Purpose |
|---|---|
| `quantum_devices` | Quantum hardware registry |
| `qubits` | Qubit identification and device relationships |
| `environmental_conditions` | Environmental measurements and categories |
| `decoherence_experiments` | T1/T2 experiment configuration |
| `experiment_events` | Experiment lifecycle audit |
| `decoherence_measurements` | Time-series Bloch-vector observations |
| `relaxation_analysis` | Calculated and estimated relaxation parameters |

### Integrity Constraints

The schema uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Numeric validation.
- Experiment lifecycle restrictions.
- Bloch-vector physical-state validation.
- Measurement probability validation.

These mechanisms protect stored experiment data independently of the application layer.

### Database Functions

`calculate_t_phi()` computes the pure dephasing time.

`calculate_purity()` computes the quantum-state purity from Bloch-vector coordinates.

`insert_measurement()` calculates derived measurement quantities before insertion.

### Database Procedure

`transition_experiment()` controls experiment lifecycle changes.

It uses row-level locking to prevent conflicting concurrent status transitions.

### Trigger

`record_experiment_status()` records status changes in `experiment_events`.

This provides an auditable history of experiment execution.

### Reporting View

`experiment_summary` combines device, qubit, environmental, experiment and measurement information.

It supports consolidated experiment reporting without repeating the underlying joins.

## 12. Distinction Between T1, T2 and T_phi

| Property | T1 | T2 | T_phi |
|---|---|---|---|
| Primary meaning | Energy relaxation | Coherence decay | Pure dephasing |
| Physical direction | Longitudinal | Transverse | Phase |
| Population change | Yes | Not necessarily | No direct population relaxation |
| Phase coherence | Can contribute to loss | Directly characterizes loss | Directly contributes to loss |
| Main relevance | Excited-state lifetime | Quantum coherence lifetime | Environmental phase instability |

The three quantities are related but are not interchangeable.

T1 describes population relaxation.

T2 describes total transverse coherence decay.

T_phi describes the additional pure-dephasing contribution in the standard relaxation model.

## 13. Environmental Effects and Experimental Interpretation

The simulated environmental categories are useful for organizing experiments and comparing parameter sets.

The following distinctions are important:

- A temperature value alone does not determine T1 or T2.
- Magnetic noise does not always produce the same effect across different qubit architectures.
- Electric noise can affect both transition frequencies and relaxation mechanisms.
- Mechanical disturbances can influence device properties through several physical pathways.
- Environmental effects can be correlated.
- A phenomenological noise-strength value is not a universal physical unit.
- Environmental comparisons require controlled experimental conditions.

The environmental labels in the implementations describe scenarios. Their numerical T1 and T2 values are configured inputs, not predictions derived from the noise-strength fields.

## 14. Practical Applications

Understanding decoherence is important in:

- Quantum processor characterization.
- Qubit lifetime measurement.
- Quantum error correction.
- Quantum circuit design.
- Quantum memory development.
- Quantum sensing.
- Cryogenic hardware engineering.
- Quantum device benchmarking.

Longer T1 and T2 values generally support longer-lived quantum information, although actual computational performance also depends on gate fidelity, measurement fidelity, crosstalk, leakage and other device characteristics.

## 15. Limitations and Modeling Assumptions

The implementations use a simplified exponential Bloch-vector model.

They do not implement a complete microscopic quantum-environment simulation.

Specific limitations include:

1. Constant T1 and T2 are assumed during each experiment.
2. Exponential decay is assumed rather than derived from arbitrary noise spectra.
3. The environment is represented through configured parameters and equilibrium population.
4. Non-Markovian memory effects are not simulated.
5. Correlated multi-qubit noise is not modeled.
6. Random environmental phase trajectories are not generated.
7. Spin echo and dynamical decoupling pulse sequences are not implemented.
8. The database stores modeled measurements rather than independently acquired hardware measurements.
9. The exponential regression estimator does not calculate confidence intervals.
10. The database analysis records configured theoretical values as reference estimates, not independently fitted experimental results.

For real laboratory characterization, additional experimental controls and uncertainty analysis are required.

## 16. Execution

### Python

Run the standalone script using Python 3:

- Executes the decoherence simulation.
- Compares environmental configurations.
- Estimates T2.
- Simulates measurement shots.
- Exports `decoherence_results.json`.

### JavaScript

Run using Node.js:

- Executes the asynchronous experiment.
- Emits measurement events.
- Estimates T2.
- Samples computational-basis measurements.
- Exports `decoherence_experiment.json`.

### C++17

Compile using a C++17-compatible compiler.

The program exports `decoherence_results.csv`.

### Java 17

Compile and run the `DecoherenceMonitor` class.

The program exports `decoherence_java_results.csv`.

### PostgreSQL

Execute the SQL script against a PostgreSQL database.

The script creates the `quantum_lab` schema, database objects, sample experiments, measurement records, lifecycle events and reporting queries.

The database script uses transactions for initial schema and sample-data setup.

## 17. Technical Coverage

| Technical Area | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| T1 relaxation | Yes | Yes | Yes | Yes | Yes |
| T2 coherence decay | Yes | Yes | Yes | Yes | Yes |
| T_phi calculation | Yes | Yes | Yes | Yes | Yes |
| Bloch-vector modeling | Yes | Yes | Yes | Yes | Yes |
| Environmental classification | Yes | Yes | Yes | Yes | Yes |
| Thermal equilibrium | Yes | Yes | Yes | Yes | Yes |
| Purity calculation | Yes | Yes | Yes | Yes | Yes |
| Measurement sampling | Yes | Yes | No | No | Shot-count storage |
| Exponential fitting | Yes | Yes | Yes | Yes | Reference analysis |
| Data export | JSON | JSON | CSV | CSV | Relational tables |
| Input validation | Yes | Yes | Yes | Yes | Yes |
| Experiment lifecycle | Simulation | Events | Engine | Service | Procedures and triggers |

## 18. Key Mathematical Relationships

| Quantity | Equation |
|---|---|
| Energy relaxation | \(P_1(t)=P_1(0)e^{-t/T_1}\) |
| Transverse X decay | \(x(t)=x_0e^{-t/T_2}\) |
| Transverse Y decay | \(y(t)=y_0e^{-t/T_2}\) |
| Longitudinal evolution | \(z(t)=z_{\mathrm{eq}}+[z_0-z_{\mathrm{eq}}]e^{-t/T_1}\) |
| Pure dephasing | \(1/T_\phi=1/T_2-1/(2T_1)\) |
| Physical constraint | \(T_2\leq2T_1\) |
| Coherence magnitude | \(C=\sqrt{x^2+y^2}\) |
| Quantum purity | \(\operatorname{Tr}(\rho^2)=(1+x^2+y^2+z^2)/2\) |
| Excited-state probability | \(P_1=(1-z)/2\) |
| Ground-state probability | \(P_0=(1+z)/2\) |

The central engineering objective is to distinguish energy relaxation from phase decoherence, quantify their relationship and maintain physically valid quantum-state representations throughout simulation and data management.
