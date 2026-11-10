# NISQ Era: Noisy Intermediate-Scale Quantum Computing

## 1. Introduction

Noisy Intermediate-Scale Quantum (NISQ) computing describes the generation of quantum processors characterized by a limited number of physical qubits, imperfect operations, finite coherence times, and the absence of sufficiently comprehensive fault-tolerant error correction.

NISQ processors provide an experimental environment for investigating quantum algorithms, quantum simulation, optimization, and hybrid quantum-classical computation.

Their practical limitations influence every stage of quantum application development, from circuit construction and hardware selection to execution, measurement, and result interpretation.

This project implements five complementary perspectives on NISQ computing:

- Python: A state-vector quantum circuit simulator with stochastic noise.
- JavaScript: An asynchronous quantum experiment scheduler.
- C++17: A hardware governance and noise-aware eligibility engine.
- Java 17: An enterprise quantum experiment management system.
- PostgreSQL: A relational database for quantum hardware, calibration, experiments, and execution results.

The implementations use mathematical models and simulated hardware behavior. They do not communicate with physical quantum processors.

## 2. NISQ Computing Fundamentals

### 2.1 Quantum bits

A classical bit occupies either zero or one.

A qubit is represented by a normalized complex state:

\[
|\psi\rangle = \alpha|0\rangle+\beta|1\rangle
\]

where:

\[
|\alpha|^2+|\beta|^2=1
\]

The coefficients are complex probability amplitudes.

Measurement in the computational basis produces:

- Outcome 0 with probability \(|\alpha|^2\).
- Outcome 1 with probability \(|\beta|^2\).

For multiple qubits, the computational state belongs to a tensor-product Hilbert space.

An \(n\)-qubit pure state requires \(2^n\) complex amplitudes in a state-vector representation.

This exponential growth explains why exact classical simulation becomes expensive as qubit count increases.

### 2.2 Superposition

Superposition allows a qubit to represent a linear combination of computational basis states.

The Hadamard gate produces:

\[
H|0\rangle =
\frac{|0\rangle+|1\rangle}{\sqrt{2}}
\]

The resulting state has equal measurement probabilities for zero and one.

Superposition does not mean that a measurement returns every possible answer simultaneously. Measurement produces one outcome according to the probability distribution.

### 2.3 Entanglement

Entanglement describes quantum correlations that cannot be represented as independent states of individual qubits.

The Bell state is:

\[
|\Phi^+\rangle =
\frac{|00\rangle+|11\rangle}{\sqrt{2}}
\]

Its measurement outcomes are correlated.

The GHZ state generalizes this construction:

\[
|GHZ_n\rangle =
\frac{|0\rangle^{\otimes n}
+|1\rangle^{\otimes n}}{\sqrt{2}}
\]

Bell and GHZ experiments provide useful tests of state preparation, two-qubit gate behavior, measurement statistics, and hardware noise.

### 2.4 Quantum gates

Quantum gates transform quantum states through unitary operations.

| Gate | Operation | Purpose |
|---|---|---|
| H | Hadamard | Creates superposition |
| X | Pauli-X | Bit flip |
| Y | Pauli-Y | Bit and phase transformation |
| Z | Pauli-Z | Phase flip |
| S | Phase gate | Relative phase rotation |
| T | T gate | Non-Clifford phase operation |
| CNOT | Controlled-X | Conditional bit flip |
| CZ | Controlled-Z | Conditional phase flip |

Single-qubit gates operate on one qubit.

Two-qubit gates act on a pair of qubits and are particularly important because they create entanglement and often introduce greater hardware error.

## 3. Characteristics of NISQ Processors

### 3.1 Limited qubit capacity

A NISQ processor has a finite physical qubit inventory.

The number of available qubits does not directly determine useful computational capability.

A processor with more physical qubits can perform worse on a particular experiment if its gate quality, connectivity, calibration stability, or coherence characteristics are inferior.

### 3.2 Gate fidelity and gate error

Gate fidelity describes the agreement between an implemented quantum operation and its intended operation under a specified fidelity definition.

Gate error represents the corresponding deviation from ideal behavior.

A simplified relationship is:

\[
p_{\text{error}}=1-p_{\text{success}}
\]

This simplified expression should not be interpreted as a universal conversion between all fidelity measures and error probabilities.

The project uses independent stochastic gate-error probabilities for its analytical estimates.

### 3.3 Decoherence

Decoherence describes the loss of quantum coherence through interactions with the surrounding environment.

Two important coherence measurements are:

- \(T_1\): Energy relaxation time.
- \(T_2\): Phase coherence time.

A short coherence time limits the useful duration of a circuit.

A circuit with many sequential operations can accumulate substantial error even when individual gates have relatively low error rates.

### 3.4 Connectivity

Physical qubits do not necessarily support direct interactions with every other qubit.

A processor may have a linear, grid-based, heavy-hexagonal, or another restricted connectivity topology.

For example:

`Q0 -- Q1 -- Q2 -- Q3`

A direct CNOT operation between Q0 and Q3 may not be available.

The circuit must be mapped to the physical topology. SWAP operations may be introduced to move quantum information between connected qubits.

These operations increase circuit depth and can introduce additional errors.

### 3.5 Measurement errors

Measurement is imperfect on physical quantum processors.

A measurement operation may report zero when the actual state is one, or report one when the actual state is zero.

A simplified symmetric readout-error model uses:

\[
P(\text{incorrect measurement})=p_r
\]

The actual readout process may be asymmetric and qubit-dependent.

### 3.6 Shot-based execution

Quantum hardware normally executes a circuit repeatedly.

Each execution is called a shot.

For \(N\) shots, the estimated probability of an outcome \(x\) is:

\[
\hat{P}(x)=\frac{n_x}{N}
\]

where \(n_x\) is the number of occurrences of that outcome.

Increasing the number of shots generally improves statistical precision, but it does not eliminate systematic hardware errors.

For a measured probability \(p\), the approximate standard error is:

\[
SE=\sqrt{\frac{p(1-p)}{N}}
\]

## 4. Quantum Noise Models

### 4.1 Depolarizing noise

Depolarizing noise represents a quantum operation becoming partially randomized.

For a single qubit, one common channel representation is:

\[
\mathcal{E}(\rho)=
(1-p)\rho+
\frac{p}{3}
(X\rho X+Y\rho Y+Z\rho Z)
\]

where:

- \(\rho\) is the density matrix.
- \(p\) is the depolarizing probability.
- \(X,Y,Z\) are Pauli operators.

The Python implementation uses a stochastic Pauli-error mechanism after ideal gate application.

The implementation is a trajectory-style approximation, not a complete density-matrix simulation.

### 4.2 Amplitude damping

Amplitude damping models energy relaxation.

A qubit in the excited state can transition toward the ground state.

The corresponding Kraus operators are:

\[
E_0=
\begin{bmatrix}
1&0\\
0&\sqrt{1-\gamma}
\end{bmatrix}
\]

\[
E_1=
\begin{bmatrix}
0&\sqrt{\gamma}\\
0&0
\end{bmatrix}
\]

where \(\gamma\) represents the damping probability.

The Python simulator approximates relaxation through stochastic quantum-state jumps.

### 4.3 Readout noise

Readout noise affects the final measurement distribution rather than the ideal gate transformation.

The Python implementation independently flips measured bits with the configured readout-error probability.

### 4.4 Noise accumulation

Under a simplified independent-error approximation:

\[
P_{\text{gate success}}=
\prod_{i=1}^{m}(1-p_i)
\]

where \(p_i\) is the error probability of gate \(i\).

For a circuit with \(n\) measured qubits and a uniform readout-error probability:

\[
P_{\text{readout success}}=(1-p_r)^n
\]

A simplified combined estimate is:

\[
P_{\text{success}}=
P_{\text{gate success}}
P_{\text{readout success}}
\]

This expression is an engineering approximation. It is not equivalent to state fidelity, process fidelity, or the probability that the entire measured bitstring matches an ideal result in every possible quantum noise model.

## 5. Hardware and Algorithm Considerations

### 5.1 Quantum circuit depth

Circuit depth measures the number of sequential operation layers.

Gates operating on independent qubits may execute in parallel.

For example:

`Layer 1: H(Q0)`

`Layer 2: CNOT(Q0,Q1)`

The implementations calculate circuit depth by tracking the availability of each qubit.

A gate cannot execute until all of its target qubits are available.

Depth is important because sequential operations consume coherence time.

### 5.2 Physical versus logical qubits

A physical qubit is a hardware-level quantum system.

A logical qubit is an encoded computational unit designed to provide improved reliability through quantum error correction.

Fault-tolerant computation generally requires multiple physical qubits to encode a logical qubit.

NISQ experiments commonly operate directly on physical qubits without comprehensive fault-tolerant encoding.

### 5.3 Quantum error correction

Quantum error correction uses encoded quantum information, syndrome measurements, and recovery operations to detect and correct errors.

Its purpose differs from simply repeating a circuit multiple times.

Repeated execution improves measurement statistics, while error correction addresses the reliability of quantum information during computation.

### 5.4 Variational quantum algorithms

Variational quantum algorithms combine parameterized quantum circuits with classical optimization.

A typical workflow is:

1. Construct a parameterized circuit.
2. Execute the circuit on a quantum processor.
3. Measure observables.
4. Estimate an objective function.
5. Update circuit parameters using a classical optimizer.
6. Repeat until a stopping condition is reached.

Examples include:

- Variational Quantum Eigensolver (VQE).
- Quantum Approximate Optimization Algorithm (QAOA).

These algorithms are relevant to NISQ research because they use relatively shallow circuits and hybrid optimization.

They still face difficulties involving noise, optimization landscapes, measurement cost, and scaling.

## 6. Python Implementation: State-Vector Simulation

The Python program implements a functional state-vector simulator.

### 6.1 Circuit representation

`QuantumCircuit` stores:

- Qubit count.
- Circuit name.
- Ordered gate operations.
- Circuit depth.

`Gate` is an immutable dataclass containing the gate type and target qubits.

The circuit validates gate arity, qubit indices, and duplicate targets.

### 6.2 State representation

The simulator stores amplitudes in a list of complex numbers.

For \(n\) qubits:

\[
|\psi\rangle =
\sum_{i=0}^{2^n-1}\alpha_i|i\rangle
\]

The initial state is:

\[
|0\rangle^{\otimes n}
\]

Only the amplitude associated with the all-zero basis state is initially nonzero.

The simulator uses little-endian indexing:

- Qubit 0 is the least significant bit.
- Qubit 1 is the next significant bit.

Measurement output is displayed in conventional most-significant-bit-first order.

### 6.3 Gate application

Single-qubit gates are applied to pairs of amplitudes.

The simulator identifies basis states that differ only in the target qubit and applies the corresponding two-dimensional matrix.

CNOT swaps amplitudes when the control bit is one and the target bit is zero.

CZ changes the phase of basis states in which both target qubits are one.

### 6.4 Noise mechanisms

`NoiseModel` defines:

- Single-qubit gate error.
- Two-qubit gate error.
- Readout error.
- Relaxation error.

The simulator applies stochastic Pauli errors and approximate amplitude-damping jumps.

A seeded random-number generator makes experiments reproducible.

### 6.5 Execution and measurement

Each shot starts with a fresh initial state.

The circuit is executed, noise is applied, and the final state is measured.

The measurement distribution is stored in a frequency counter.

The simulator supports JSON export through an atomic file-replacement operation.

### 6.6 Experiments

The implementation includes:

- Bell-state preparation.
- GHZ-state preparation.
- Ideal execution.
- Noisy execution.
- Analytical success-probability estimation.

Example execution options:

- `python nisq.py`
- `python nisq.py --noise`
- `python nisq.py --experiment ghz --qubits 4`
- `python nisq.py --shots 10000 --noise --output results.json`
- `python nisq.py --test`

### 6.7 Complexity

For \(n\) qubits, the state vector contains \(2^n\) amplitudes.

| Operation | Approximate complexity |
|---|---|
| State initialization | \(O(2^n)\) |
| Single-qubit gate | \(O(2^n)\) |
| CNOT | \(O(2^n)\) |
| CZ | \(O(2^n)\) |
| Measurement sampling | \(O(2^n)\) in this implementation |
| Shot execution | \(O(SG2^n)\) |

Here, \(S\) represents the shot count and \(G\) represents gate count.

The simulator limits circuits to 20 qubits to constrain memory consumption.

A production simulator would normally use more specialized numerical methods, optimized state-vector operations, density matrices, or tensor-network methods depending on the experiment.

## 7. JavaScript Implementation: Asynchronous Experiment Scheduling

The JavaScript implementation concentrates on experiment orchestration rather than reproducing the Python state-vector algorithm.

It models a quantum computing service that receives experiment requests, evaluates device suitability, schedules jobs, and records outcomes.

### 7.1 Device registry

`DeviceRegistry` manages available processors through a `Map`.

Each `QuantumDevice` contains:

- Device identity.
- Qubit capacity.
- Connectivity.
- Single-qubit error.
- Two-qubit error.
- Readout error.
- Coherence time.
- Gate duration.
- Availability state.

Device selection rejects processors that cannot execute the circuit topology.

### 7.2 Calibration-aware selection

Each device calculates an estimated success probability based on its calibration data.

The selection service evaluates compatible devices and chooses the eligible processor with the highest estimated success probability.

This is a simplified scheduling strategy.

A production scheduler could also consider queue length, execution cost, reservation priority, calibration age, expected runtime, and service-level agreements.

### 7.3 Asynchronous job execution

`QuantumScheduler` extends Node.js `EventEmitter`.

It supports events for:

- Job submission.
- Job execution.
- Job completion.
- Job failure.
- Job cancellation.

A concurrency limit controls the number of active jobs.

Promises and asynchronous functions manage execution and error propagation.

### 7.4 Job state management

The lifecycle is:

`QUEUED → RUNNING → COMPLETED`

Alternative terminal states include:

- FAILED
- CANCELLED

Invalid state transitions are rejected.

Cancellation is supported for queued and running jobs.

Running cancellation is cooperative and is checked after the simulated execution delay.

### 7.5 Reporting

The scheduler creates a structured experiment report containing:

- Total jobs.
- Completed jobs.
- Failed jobs.
- Cancelled jobs.
- Queued jobs.
- Running jobs.

Results are persisted in a JSON report with restricted file permissions where supported by the operating system.

### 7.6 Important limitation

The scheduler does not simulate quantum measurement outcomes and does not submit commands to physical hardware.

It calculates engineering estimates and demonstrates asynchronous experiment management.

Example execution:

- `node nisq.js`
- `node nisq.js --test`

## 8. C++17 Implementation: Hardware Governance Engine

The C++ implementation focuses on resource validation and device eligibility.

Its central component is `GovernanceEngine`.

### 8.1 Domain structures

The implementation defines:

| Structure | Responsibility |
|---|---|
| `Gate` | Quantum operation and qubit targets |
| `Circuit` | Ordered operations and resource requirements |
| `Calibration` | Hardware error and timing characteristics |
| `QuantumDevice` | Physical processor capabilities |
| `NoiseEstimate` | Estimated execution quality |
| `EvaluationPolicy` | Acceptance constraints |
| `EvaluationResult` | Eligibility decision and rejection reasons |

### 8.2 Connectivity validation

A two-qubit gate requires an available physical connection.

The implementation stores undirected connectivity edges in a set.

The edge normalization function maps both directions to the same representation.

This avoids duplicate representations of the same physical connection.

### 8.3 Noise estimation

The engine separately estimates:

- Single-qubit gate success.
- Two-qubit gate success.
- Readout success.
- Coherence penalty.

The combined estimate incorporates all four factors.

The exponential coherence penalty is:

\[
P_c=e^{-t/T}
\]

where:

- \(t\) is the estimated execution duration.
- \(T\) is the configured coherence-time reference.

This is a simplified phenomenological model rather than a hardware-calibrated decoherence channel.

### 8.4 Eligibility policies

A processor is eligible only when it satisfies the configured requirements.

These include:

- Online hardware status.
- Sufficient physical qubits.
- Compatible connectivity.
- Acceptable gate error.
- Current calibration.
- Acceptable circuit depth.
- Coherence budget.
- Minimum estimated success probability.

Rejected experiments include explicit reasons.

### 8.5 Device selection

The engine evaluates every available processor.

It selects the eligible device with the highest estimated success probability.

The approach has approximately:

\[
O(D(G+Q))
\]

evaluation complexity, where \(D\) is the number of devices, \(G\) is the number of gates, and \(Q\) is the circuit qubit count.

The example uses a small inventory. Large processor inventories would benefit from indexed connectivity checks, cached calibration summaries, and scheduling queues.

### 8.6 Execution

The program processes Bell and GHZ experiments against three example processors.

It demonstrates successful selection, calibration validation, maintenance rejection, and policy enforcement.

Compile with C++17:

`g++ -std=c++17 -O2 nisq.cpp -o nisq`

## 9. Java 17 Implementation: Enterprise Experiment Management

The Java implementation models a service-oriented quantum research environment.

It introduces explicit domain types, immutable records, service classes, and controlled state transitions.

### 9.1 Domain model

The principal domain objects are:

- `QuantumCircuit`
- `Gate`
- `Calibration`
- `Device`
- `ApprovalPolicy`
- `NoiseEstimate`
- `Evaluation`
- `ExperimentJob`

Records are used for immutable value objects.

The experiment job is a mutable lifecycle entity because its status changes during processing.

### 9.2 Service separation

The implementation separates responsibilities into distinct services.

| Service | Responsibility |
|---|---|
| `DeviceInventory` | Processor registration and lookup |
| `NoisePolicyService` | Calibration and error evaluation |
| `DeviceSelectionService` | Eligible processor selection |
| `ExperimentService` | Job submission and execution |

This separation prevents hardware inventory management, policy decisions, and experiment lifecycle operations from becoming one tightly coupled class.

### 9.3 Approval policy

The approval policy defines:

- Minimum calibration version.
- Maximum gate error.
- Minimum estimated success probability.
- Maximum coherence ratio.
- Maximum circuit depth.
- Online-device requirement.

A rejected experiment includes a collection of policy violations.

### 9.4 State transitions

The enterprise lifecycle is:

`SUBMITTED → VALIDATING → APPROVED → RUNNING → COMPLETED`

Alternative states include:

- REJECTED
- FAILED
- CANCELLED

The `transition` method validates state changes.

Synchronization protects transitions against concurrent modification of an individual job.

The inventory and job registries use concurrent collections.

### 9.5 Device selection

The selection service evaluates available processors using Java Streams.

Eligible processors are sorted by estimated success probability.

The processor with the highest estimated success probability is selected.

The design keeps selection logic separate from circuit construction and execution.

### 9.6 Execution model

The demonstration records the completion of an approved experiment.

It does not run a quantum simulation or communicate with a quantum processor.

A physical integration would require a hardware adapter, authenticated provider access, asynchronous execution tracking, and provider-specific result normalization.

Compile and execute:

- `javac NISQEnterprise.java`
- `java NISQEnterprise`

## 10. PostgreSQL Implementation: Quantum Experiment Database

The database represents the operational structure of a quantum research environment.

The schema separates hardware inventory, calibration records, experiment definitions, policies, job execution, and measurement data.

### 10.1 Relational structure

| Table | Purpose |
|---|---|
| `organizations` | Research organization records |
| `users` | Authorized platform users |
| `quantum_devices` | Physical processor inventory |
| `device_qubits` | Individual qubit characteristics |
| `device_connectivity` | Physical qubit connections |
| `gate_calibrations` | Gate error and timing records |
| `noise_models` | Reusable noise configurations |
| `quantum_circuits` | Experiment circuit definitions |
| `circuit_gates` | Ordered circuit operations |
| `approval_policies` | Execution eligibility constraints |
| `experiment_jobs` | Experiment submissions and lifecycle |
| `measurement_results` | Observed measurement distributions |
| `eligibility_audits` | Historical policy evaluation decisions |

### 10.2 Organization isolation

Each organization owns its users, processors, circuits, noise models, and approval policies.

The experiment submission procedure checks that the circuit, device, policy, and user belong to the same organization.

This prevents accidental cross-organization experiment submissions.

The implementation uses application-level database checks. Production deployments should also implement PostgreSQL row-level security and least-privilege database roles.

### 10.3 Hardware inventory

The device table records processor technology, qubit capacity, and operational status.

The `device_qubits` table records individual qubit properties.

The `device_connectivity` table stores physical connectivity edges.

A normalized edge representation prevents duplicate connections.

### 10.4 Calibration management

Calibration records contain:

- Gate type.
- Target qubits.
- Gate error.
- Gate duration.
- Calibration version.
- Calibration timestamp.
- Calibrating user.

Multiple calibration records can exist for a device and gate type.

This preserves calibration history instead of replacing previous measurements.

The reporting queries can compare observed calibration errors across processors.

### 10.5 Circuit storage

`quantum_circuits` stores circuit-level information.

`circuit_gates` stores individual gate operations.

Sequence numbers preserve operation order.

Database triggers enforce valid qubit indices and connectivity bounds for registered hardware.

The schema stores the control and target qubit for controlled gates.

It does not implement a complete quantum intermediate representation or parallel gate scheduler.

### 10.6 Experiment submission

The `submit_experiment` procedure performs the following operations:

1. Validates the shot count.
2. Checks user authorization.
3. Verifies circuit ownership.
4. Verifies processor organization.
5. Retrieves the active approval policy.
6. Evaluates circuit eligibility.
7. Creates an approved or rejected experiment job.
8. Records an eligibility audit.

The procedure uses a single database transaction when called within a transaction.

A failure during submission prevents partial persistence.

### 10.7 Eligibility determination

`evaluate_experiment` evaluates:

- Device availability.
- Qubit capacity.
- Circuit gate inventory.
- Gate calibration error.
- Calibration version.
- Estimated success probability.

The function returns a Boolean eligibility decision, an estimated probability, and structured rejection reasons.

The example does not calculate a fully calibrated coherence estimate from individual \(T_1\) and \(T_2\) measurements. A production implementation would incorporate those measurements, gate scheduling, and hardware-specific noise models.

### 10.8 Experiment lifecycle

The procedure `process_approved_jobs` demonstrates transitions from approval through queueing, execution, and completion.

It is a simplified batch processor.

A production system should use worker ownership, row locking with `FOR UPDATE SKIP LOCKED`, execution leases, retry limits, and provider acknowledgements to avoid concurrent duplicate execution.

### 10.9 Measurement records

Measurement results are stored as bitstrings.

For each experiment, the database records:

- Measured bitstring.
- Occurrence count.
- Estimated probability.
- Recording timestamp.

A trigger validates that the bitstring contains only binary digits and matches the circuit's qubit count.

This provides a normalized basis for measurement reporting.

### 10.10 Database performance

The schema includes indexes for common retrieval patterns:

- Experiment status and submission time.
- Processor and job status.
- Organization and submission date.
- Circuit gate ordering.
- Calibration history.
- Eligibility audit history.

Indexes improve filtering and sorting but add write overhead.

For very large measurement datasets, partitioning by experiment submission date or organization may be appropriate.

## 11. Practical NISQ Experiment Workflow

A complete experimental workflow follows the sequence below.

`Research Question`

↓

`Quantum Algorithm Design`

↓

`Circuit Construction`

↓

`Circuit Validation`

↓

`Physical Qubit Mapping`

↓

`Connectivity Validation`

↓

`Hardware Calibration Inspection`

↓

`Noise and Coherence Estimation`

↓

`Device Selection`

↓

`Experiment Approval`

↓

`Shot-Based Execution`

↓

`Measurement Collection`

↓

`Statistical Analysis`

↓

`Result Validation`

↓

`Experiment Reporting`

Each stage addresses a different source of experimental uncertainty.

A circuit can be mathematically valid but unsuitable for a particular physical processor.

A processor can be available but fail the calibration policy.

An approved experiment can complete successfully while still producing results that are statistically or scientifically unreliable.

Execution completion must therefore remain separate from scientific validation.

## 12. Error Mitigation and Reliability Techniques

Error mitigation attempts to improve the quality of estimates obtained from noisy hardware without necessarily implementing full fault-tolerant error correction.

Important approaches include:

### 12.1 Readout mitigation

Readout mitigation estimates measurement errors using calibration experiments.

A measurement assignment matrix can describe transitions between actual and observed bitstrings.

Corrected probability estimates can then be obtained through matrix inversion or constrained statistical estimation.

### 12.2 Zero-noise extrapolation

Zero-noise extrapolation evaluates an observable at multiple effective noise levels.

The measured values are extrapolated toward the zero-noise limit.

The method introduces assumptions about noise scaling and extrapolation behavior.

It can amplify statistical uncertainty.

### 12.3 Probabilistic error cancellation

Probabilistic error cancellation uses calibrated noise models and sampling techniques to estimate ideal expectation values.

Its sampling overhead can increase substantially as circuit noise grows.

### 12.4 Dynamical decoupling

Dynamical decoupling inserts pulse sequences designed to reduce the effect of certain environmental interactions.

Its effectiveness depends on the hardware noise spectrum, pulse quality, and available timing constraints.

### 12.5 Measurement optimization

Observables may be grouped into compatible measurement settings.

Efficient grouping reduces measurement overhead.

The grouping strategy must preserve the mathematical validity of the requested observable estimates.

## 13. Distinctions Between Major Concepts

| Concept | Meaning | Primary concern |
|---|---|---|
| Qubit count | Number of physical qubits | Hardware capacity |
| Circuit width | Number of qubits used by a circuit | Resource requirements |
| Circuit depth | Sequential operation layers | Execution duration |
| Gate fidelity | Quality of quantum operations | Gate accuracy |
| Coherence time | Duration of preserved quantum coherence | Decoherence |
| Connectivity | Available physical interactions | Circuit mapping |
| Shot count | Number of repeated executions | Statistical precision |
| Readout error | Measurement inaccuracy | Observed outcomes |
| Error mitigation | Reduction of observable bias | Result quality |
| Error correction | Protection of encoded quantum information | Computational reliability |
| Logical qubit | Error-corrected computational unit | Fault tolerance |
| NISQ computing | Noisy, limited-scale quantum computation | Near-term experimentation |

These concepts are related but not interchangeable.

In particular, increasing shot count cannot directly compensate for every systematic gate error, and increasing physical qubit capacity does not automatically improve circuit quality.

## 14. Limitations and Engineering Assumptions

The five implementations deliberately use simplified models.

### Python

- Uses pure state vectors.
- Does not implement a complete density-matrix framework.
- Uses approximate stochastic noise mechanisms.
- Does not include parameterized rotation gates.
- Limits the number of qubits because of exponential memory growth.

### JavaScript

- Implements scheduling and policy evaluation.
- Uses analytical quality estimates.
- Simulates execution latency.
- Does not generate quantum measurement outcomes.
- Does not communicate with physical quantum hardware.

### C++17

- Implements processor governance and eligibility.
- Uses independent gate-error approximations.
- Uses a simplified coherence penalty.
- Does not implement a state-vector simulator.
- Does not perform physical circuit routing or SWAP insertion.

### Java 17

- Implements enterprise domain types and lifecycle services.
- Uses immutable records for stable domain values.
- Uses concurrent collections for shared registries.
- Does not provide a physical hardware execution adapter.
- Does not implement a distributed job queue.

### PostgreSQL

- Stores normalized experiment and hardware records.
- Implements validation and policy procedures.
- Uses simplified analytical estimates.
- Does not provide a complete hardware calibration engine.
- Does not enforce every physical circuit scheduling constraint.
- Uses a demonstration batch lifecycle rather than a distributed execution system.

## 15. Security and Production Considerations

Quantum research platforms can contain proprietary algorithms, calibration measurements, experimental results, and hardware-access credentials.

Production implementations should consider:

- Role-based access control.
- Organization-level data isolation.
- Encryption in transit and at rest.
- Secure credential storage.
- Authenticated hardware-provider connections.
- Immutable audit records.
- Experiment submission authorization.
- Calibration version management.
- Rate limiting.
- Resource quotas.
- Job cancellation and retry controls.
- Execution monitoring.
- Backup and recovery.
- Measurement data integrity.

Physical quantum hardware should never be treated as an unlimited computational resource.

Experiment scheduling should account for processor availability, calibration validity, queue capacity, execution duration, and the cost of repeated measurements.

Analytical success estimates should be labeled as estimates rather than measured hardware fidelity.

Scientific conclusions should be supported by repeated experiments, uncertainty estimates, suitable baselines, and documented calibration conditions.
