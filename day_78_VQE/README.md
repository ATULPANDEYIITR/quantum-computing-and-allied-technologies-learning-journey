# Variational Quantum Eigensolver (VQE)

## 1. Introduction

The Variational Quantum Eigensolver is a hybrid quantum-classical algorithm designed to estimate the minimum eigenvalue of a Hermitian Hamiltonian.

The algorithm combines:

- Quantum circuits for preparing parameterized quantum states.
- Quantum measurements for estimating Hamiltonian expectation values.
- Classical optimization for updating circuit parameters.
- Iterative evaluation until an acceptable energy estimate is obtained.

VQE is particularly relevant to molecular electronic structure calculations, quantum chemistry, material science, and optimization problems involving quantum Hamiltonians.

Unlike quantum phase estimation, VQE does not require a long coherent quantum computation for its basic operation. Its iterative structure makes it suitable for investigating algorithms on noisy intermediate-scale quantum devices.

## 2. Mathematical Foundation

### 2.1 Hamiltonian and Ground-State Energy

A quantum Hamiltonian is a Hermitian operator representing the energy of a physical system.

Its eigenvalue equation is:

\[
H|\psi_i\rangle=E_i|\psi_i\rangle
\]

The ground-state energy is the smallest eigenvalue:

\[
E_0=\min_i E_i
\]

For a normalized trial state, the variational principle gives:

\[
E(\theta)=
\langle\psi(\theta)|H|\psi(\theta)\rangle
\geq E_0
\]

The objective of VQE is to minimize this expectation value.

### 2.2 Pauli Decomposition

A Hamiltonian can be represented as a weighted sum of Pauli operators:

\[
H=\sum_j c_jP_j
\]

Here:

- \(c_j\) represents a real-valued coefficient.
- \(P_j\) represents a Pauli operator or tensor product of Pauli operators.
- \(I\) represents the identity operator.
- \(X\), \(Y\), and \(Z\) represent the Pauli matrices.

For a single-qubit example:

\[
H=-Z-0.5X
\]

The ground-state energy can be calculated analytically:

\[
E_0=-\sqrt{1^2+0.5^2}
\]

\[
E_0\approx -1.11803398875
\]

This analytical value provides a reference against which the VQE result can be evaluated.

## 3. Variational Quantum Circuit

### 3.1 Ansatz

An ansatz is a parameterized quantum circuit used to construct candidate quantum states.

The implementations use an \(R_y\) rotation:

\[
R_y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

Starting with the computational basis state:

\[
|0\rangle=
\begin{bmatrix}
1\\
0
\end{bmatrix}
\]

The parameterized state becomes:

\[
|\psi(\theta)\rangle=
\begin{bmatrix}
\cos(\theta/2)\\
\sin(\theta/2)
\end{bmatrix}
\]

The circuit parameter controls the state prepared by the quantum circuit.

For the example Hamiltonian:

\[
E(\theta)=-\cos(\theta)-0.5\sin(\theta)
\]

The minimum occurs at:

\[
\theta^*=\tan^{-1}(0.5)
\]

The optimized energy is the exact ground-state energy for this particular one-qubit problem.

### 3.2 Ansatz Expressibility

The quality of a VQE result depends partly on the expressibility of its ansatz.

A simple circuit may not represent the ground state of a complex Hamiltonian.

More sophisticated circuits can use:

- Multiple rotation layers.
- Entangling gates.
- Hardware-efficient ansätze.
- Unitary coupled-cluster constructions.
- Problem-inspired circuit structures.

Increasing circuit depth can improve representational capacity, but it can also increase noise, measurement requirements, and optimization difficulty.

The supplied programs use a single-qubit \(R_y\) ansatz. They are executable demonstrations of VQE mechanisms, not complete molecular quantum chemistry solvers.

## 4. VQE Execution Workflow

The general execution sequence is:

1. Define the Hamiltonian.
2. Select a parameterized ansatz.
3. Initialize variational parameters.
4. Prepare the quantum state.
5. Measure Hamiltonian observables.
6. Calculate the energy expectation.
7. Calculate parameter gradients.
8. Update the parameters using a classical optimizer.
9. Evaluate convergence.
10. Report the optimized energy and experimental information.

The hybrid computational structure is:

**Classical initialization**

↓

**Quantum circuit preparation**

↓

**Quantum measurements**

↓

**Classical energy evaluation**

↓

**Gradient calculation**

↓

**Parameter optimization**

↓

**Convergence evaluation**

↓

**Final energy estimate**

The quantum processor performs state preparation and measurement. The classical processor manages optimization, numerical evaluation, and experiment control.

## 5. Parameter-Shift Rule

Gradient calculation is central to variational optimization.

The parameter-shift rule calculates derivatives using circuit evaluations at shifted parameter values.

For the single-qubit rotation used here:

\[
\frac{\partial E}{\partial\theta}
=
\frac{
E(\theta+\pi/2)-E(\theta-\pi/2)
}{2}
\]

This method is useful because it obtains gradients through quantum-circuit evaluations rather than relying on direct differentiation of measured quantum states.

For a circuit with multiple independent parameters, the corresponding shifted evaluations are performed for each parameter.

The number of circuit evaluations increases with the number of parameters.

For more complicated gates and generators, the appropriate parameter-shift coefficients and shifts depend on the generator spectrum. The single-shift formula must not be applied indiscriminately to every possible parameterized gate.

## 6. Classical Optimization

The implementations use gradient descent.

The update equation is:

\[
\theta_{t+1}
=
\theta_t-\eta\nabla E(\theta_t)
\]

Where:

- \(\theta_t\) represents the current parameters.
- \(\eta\) represents the learning rate.
- \(\nabla E\) represents the energy gradient.
- \(t\) represents the optimization iteration.

The learning rate controls the magnitude of parameter updates.

A learning rate that is too large may produce unstable optimization. A very small learning rate may require excessive iterations.

Other optimization methods commonly relevant to VQE include:

| Method | Mechanism | Practical consideration |
|---|---|---|
| Gradient descent | Uses objective gradients | Simple but sensitive to learning rate |
| Adam | Adaptive gradient updates | Maintains moving gradient statistics |
| SPSA | Uses stochastic simultaneous perturbations | Can reduce gradient evaluation requirements |
| COBYLA | Derivative-free constrained optimization | Useful when gradients are unavailable or unreliable |

The source implementations expose the optimizer configuration and use gradient descent for their principal numerical demonstrations. The SQL schema also represents alternative optimization methods for experiment tracking.

## 7. Quantum Measurement and Shot Noise

Quantum hardware does not directly return an exact expectation value.

An observable is estimated by repeatedly preparing a quantum state and measuring it.

For a Pauli observable with measurement outcomes \(+1\) and \(-1\):

\[
\langle P\rangle
\approx
\frac{N_+-N_-}{N}
\]

Where:

- \(N_+\) represents positive measurement outcomes.
- \(N_-\) represents negative measurement outcomes.
- \(N\) represents the total number of shots.

The estimated Hamiltonian energy is:

\[
E(\theta)\approx
\sum_j c_j\langle P_j\rangle
\]

Finite measurement samples introduce statistical uncertainty.

For an independent Pauli measurement, the standard error of the sample mean is:

\[
SE=
\sqrt{
\frac{1-\langle P\rangle^2}{N}
}
\]

Increasing the number of shots generally reduces statistical uncertainty, but increases execution cost.

The Python, JavaScript, C++17, and Java implementations include finite-shot measurement mechanisms. Exact statevector evaluation is the default for the primary optimization demonstration.

## 8. Distinguishing Exact Simulation and Quantum Hardware

These execution environments have different characteristics.

| Property | Statevector simulation | Shot simulation | Quantum hardware |
|---|---|---|---|
| State representation | Classical complex amplitudes | Simulated measurement outcomes | Physical quantum state |
| Measurement | Exact expectation | Statistical estimate | Statistical estimate |
| Noise | Normally absent | Sampling noise | Hardware and sampling noise |
| Execution cost | Classical computation | Repeated simulated sampling | Hardware access and execution |
| Scalability | Exponential in qubit count | Depends on simulator | Limited by hardware capabilities |

The supplied programs use one-qubit statevector simulation and optional simulated measurements.

They do not connect to physical quantum hardware.

## 9. Python Implementation

The Python implementation provides a numerical VQE workflow using standard-library functionality.

### 9.1 Domain Model

The principal classes are:

| Class | Responsibility |
|---|---|
| `PauliTerm` | Validates a Hamiltonian coefficient and Pauli operator |
| `Hamiltonian` | Calculates expectation values and analytical ground-state energy |
| `StatevectorSimulator` | Prepares the variational state and evaluates observables |
| `MeasurementSimulator` | Simulates finite-shot measurements |
| `VQEConfig` | Defines optimization settings |
| `VQE` | Coordinates optimization and experiment execution |

`OptimizationRecord` stores the parameter vector, energy, gradient norm, and iteration number.

`ExperimentStatus` provides explicit experiment lifecycle states.

### 9.2 Optimization and Validation

The `VQE` class separates state preparation, energy evaluation, gradient calculation, and optimization.

It supports:

- Parameter validation.
- Hamiltonian validation.
- Parameter-shift differentiation.
- Exact and sampled energy evaluation.
- Iteration history.
- Convergence monitoring.
- Experiment failure handling.
- JSON report persistence.

The built-in assertions verify observable expectations and the analytical ground-state calculation.

The resulting JSON report records the optimized parameters, energy estimate, exact reference energy, and absolute error.

## 10. JavaScript Implementation

The JavaScript implementation emphasizes asynchronous execution and event-driven experiment monitoring.

### 10.1 Event-Driven Experiment Management

`VQEExperiment` extends Node.js `EventEmitter`.

It emits events for:

- Experiment initialization.
- Optimization iterations.
- Experiment completion.
- Experiment failure.

This design separates numerical processing from monitoring and reporting.

External components can subscribe to experiment events without changing the optimization engine.

### 10.2 Asynchronous Processing

The optimization loop periodically yields control through `setImmediate`.

This allows the Node.js event loop to process monitoring callbacks between iterations.

The implementation uses asynchronous file operations for report persistence.

### 10.3 Convergence Policy

`ConvergencePolicy` monitors changes in consecutive energy evaluations.

It uses a tolerance and patience threshold to determine when further optimization is unlikely to produce a meaningful improvement.

The gradient calculation remains deterministic and uses exact statevector evaluations, while optional energy evaluations can use simulated measurement shots.

This distinction avoids allowing independent sampling noise in gradient evaluations to obscure the numerical behavior of the demonstration.

## 11. C++17 Implementation

The C++ implementation emphasizes numerical control, domain separation, and resource-efficient data structures.

### 11.1 Core Components

| Component | Responsibility |
|---|---|
| `Complex` | Stores complex amplitudes |
| `Statevector` | Represents the quantum state |
| `PauliTerm` | Models an observable and coefficient |
| `Hamiltonian` | Evaluates energy expectations |
| `QuantumCircuit` | Constructs the variational state |
| `PauliMeasurement` | Evaluates Pauli observables |
| `MeasurementService` | Simulates finite-shot sampling |
| `VQEOptimizer` | Executes gradient-based optimization |

The program uses STL vectors for Hamiltonian terms and optimization history.

### 11.2 Numerical Validation

The statevector verifies normalization:

\[
|\alpha|^2+|\beta|^2=1
\]

Hamiltonian coefficients and circuit parameters are checked for finite values.

The optimizer rejects invalid configurations and prevents an experiment from being executed more than once.

Optimization history is written to CSV for subsequent numerical analysis.

### 11.3 Performance Considerations

For a one-qubit simulation, state preparation and observable evaluation require constant time.

The optimization cost is proportional to the number of iterations and Hamiltonian terms:

\[
O(IT)
\]

Where:

- \(I\) is the number of optimization iterations.
- \(T\) is the number of Hamiltonian terms.

For general statevector simulation with \(n\) qubits, memory requirements grow exponentially:

\[
O(2^n)
\]

This exponential growth is a fundamental practical limitation of classical statevector simulation.

## 12. Java 17 Enterprise Implementation

The Java implementation models VQE as an experiment-management service.

It emphasizes explicit domain types, immutable records, policy interfaces, validation, and auditability.

### 12.1 Domain Architecture

The implementation separates:

- Quantum states.
- Hamiltonian terms.
- Circuit preparation.
- Measurement services.
- Optimization policies.
- Experiment execution.
- Audit records.
- Report persistence.

Java records represent immutable data structures.

The `QuantumAnsatz` interface separates circuit preparation from the optimization service.

The `OptimizationPolicy` interface provides a replaceable convergence mechanism.

`ExperimentAudit` maintains an immutable external view of optimization records.

### 12.2 Experiment Lifecycle

The experiment uses the following states:

| State | Meaning |
|---|---|
| `CREATED` | Experiment initialized |
| `RUNNING` | Optimization in progress |
| `COMPLETED` | Optimization finished successfully |
| `FAILED` | Execution failed |

An experiment cannot be executed repeatedly after leaving its initial state.

The service wraps execution failures in a domain-specific exception.

### 12.3 Enterprise Considerations

The Java implementation demonstrates several controls useful in research platforms:

- Explicit experiment identification.
- Configuration validation.
- Separation of computation and persistence.
- Immutable optimization records.
- Controlled lifecycle transitions.
- Auditable experiment history.
- Temporary-file report persistence.

For production deployments, these controls would need to be supplemented with authentication, authorization, persistent transaction management, experiment ownership validation, and distributed execution coordination.

## 13. PostgreSQL Experiment Management

The SQL implementation provides a relational data model for managing VQE experiments.

It separates experiment definitions, Hamiltonians, optimization history, measurements, researchers, organizations, and execution backends.

### 13.1 Relational Architecture

The principal relationships are:

**Research Organization**

→ Researchers

→ Quantum Experiments

→ Quantum Backends

→ Hamiltonians

→ Hamiltonian Terms

→ Optimization Iterations

→ Measurement Batches

### 13.2 Experiment Records

`quantum_experiments` stores:

- Experiment ownership.
- Quantum backend.
- Number of qubits.
- Ansatz configuration.
- Optimization method.
- Learning rate.
- Convergence tolerance.
- Measurement-shot count.
- Initial and optimized parameters.
- Execution status.
- Final and reference energies.

The experiment table uses foreign keys to enforce relationships between researchers, organizations, and execution backends.

### 13.3 Hamiltonian Storage

`hamiltonians` stores the physical system and experiment-level Hamiltonian information.

`hamiltonian_terms` stores individual Pauli strings and their coefficients.

For example:

| Coefficient | Pauli string |
|---:|---|
| -1.0 | Z |
| -0.5 | X |

Together, these rows represent:

\[
H=-Z-0.5X
\]

The database validates Pauli-string characters and prevents duplicate terms within a Hamiltonian.

The SQL schema allows multi-qubit Pauli strings, while the executable language demonstrations use a single-qubit Hamiltonian.

### 13.4 Optimization History

`optimization_iterations` stores each optimization step independently.

The table captures:

- Iteration number.
- Parameter vector.
- Energy.
- Gradient norm.
- Learning rate.
- Evaluation type.

A unique constraint on experiment and iteration number prevents duplicate iteration identifiers.

This design preserves experiment history rather than overwriting previous optimization results.

### 13.5 Measurement Management

`measurement_batches` records individual observable measurements.

It stores:

- Observable.
- Hamiltonian coefficient.
- Shot count.
- Positive outcomes.
- Negative outcomes.
- Estimated expectation.
- Execution status.

A database trigger calculates:

\[
\langle P\rangle=
\frac{N_+-N_-}{N}
\]

when all expected measurement outcomes are available.

### 13.6 Database Procedures and Triggers

The SQL implementation includes three important workflow controls.

**Experiment validation**

Checks researcher eligibility, organization membership, backend availability, qubit capacity, and measurement capabilities.

**Experiment lifecycle enforcement**

Prevents invalid state transitions.

**Experiment completion**

Stores the final energy, optimized parameter vector, exact reference energy, and absolute energy error.

These controls protect database consistency even when experiment updates originate from different application components.

### 13.7 Reporting and Evaluation

The database includes views and queries for:

- Experiment retrieval.
- Hamiltonian inspection.
- Optimization statistics.
- Best observed energy.
- Measurement aggregation.
- Result eligibility.
- Backend performance reporting.

The `ROW_NUMBER()` window function identifies the lowest-energy iteration for each experiment.

The reporting views avoid repeatedly writing the same joins for operational queries.

## 14. Important VQE Distinctions

Several concepts must remain separate when evaluating VQE implementations.

| Concept | Meaning |
|---|---|
| Hamiltonian | Mathematical representation of system energy |
| Ansatz | Parameterized circuit family |
| Variational parameters | Adjustable circuit values |
| State preparation | Construction of the trial quantum state |
| Observable measurement | Estimation of Pauli expectation values |
| Energy estimation | Weighted combination of observable measurements |
| Gradient calculation | Estimation of energy derivatives |
| Classical optimization | Updating the variational parameters |
| Convergence | Determination of an acceptable stopping condition |
| Ground-state energy | Minimum eigenvalue of the Hamiltonian |

A low energy estimate does not automatically establish that the prepared state is physically accurate for every observable.

Energy accuracy, state fidelity, measurement uncertainty, and hardware performance are different evaluation criteria.

## 15. Edge Cases and Failure Conditions

The implementations address several numerical and operational failure conditions.

| Failure condition | Handling |
|---|---|
| Empty Hamiltonian | Reject construction |
| Invalid Pauli operator | Reject input |
| Non-finite coefficient | Reject input |
| Invalid rotation parameter | Reject circuit execution |
| Invalid learning rate | Reject configuration |
| Zero or negative iteration limit | Reject configuration |
| Invalid measurement-shot count | Reject measurement |
| Invalid quantum-state normalization | Reject state |
| Repeated experiment execution | Reject state transition |
| Persistence failure | Report an execution error |
| Incomplete measurement batch | Prevent completed measurement status |

The SQL implementation further enforces foreign-key relationships, status constraints, and backend capacity restrictions.

## 16. Limitations of the Implementations

The five implementations are deliberately designed as compact, executable VQE learning systems.

Their limitations are important.

### Quantum Simulation

The Python, JavaScript, C++17, and Java implementations support one qubit and one variational rotation parameter.

They do not implement general multi-qubit tensor-product simulation or entangling circuits.

### Hamiltonian Representation

The SQL model supports multi-qubit Pauli strings, but the language implementations evaluate single-character Pauli observables.

### Optimization

The main optimization demonstration uses gradient descent.

The SQL schema records several other optimizer types, but does not implement their numerical algorithms.

### Measurement

Finite-shot simulation models independent Pauli measurement outcomes.

It does not model readout errors, gate noise, decoherence, calibration drift, or correlated measurement errors.

### Quantum Chemistry

The examples do not perform molecular orbital calculations, fermion-to-qubit transformations, or realistic molecular ground-state calculations.

A production quantum chemistry VQE workflow would require additional domain-specific components.

### Quantum Hardware

No implementation directly submits circuits to a physical quantum processor.

Hardware execution would require backend integration, transpilation, device calibration, job management, and measurement-result processing.

## 17. Performance and Security Considerations

### Performance

Important performance factors include:

- Number of Hamiltonian terms.
- Number of variational parameters.
- Circuit depth.
- Number of optimization iterations.
- Number of measurement shots.
- Number of independent measurement groups.
- Backend execution latency.

For large Hamiltonians, measurement grouping can reduce the number of distinct measurement circuits when compatible observables commute.

Classical optimization can also become expensive when the number of circuit parameters increases.

### Security

A research-grade VQE platform should implement:

- Authenticated researcher accounts.
- Role-based experiment access.
- Input validation.
- Controlled backend access.
- Protected experiment configuration.
- Audit logging.
- Secure storage of experiment results.
- Validation of externally supplied Hamiltonians.
- Isolation of untrusted execution jobs.

The SQL demonstration provides relational integrity and experiment ownership relationships, but it does not implement a complete authorization system.

## 18. Running the Implementations

### Python

Requirements:

- Python 3.10 or later.
- Python standard library.

Execute:

`python vqe.py`

The program runs numerical assertions, optimizes the Hamiltonian, and generates `vqe_results.json`.

### JavaScript

Requirements:

- Node.js 18 or later.
- Node.js standard library.

Execute:

`node vqe.js`

The application runs asynchronously, publishes experiment events, and generates `vqe_results.json`.

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic vqe.cpp -o vqe`

Execute:

`./vqe`

On Windows:

`.\vqe.exe`

The program generates `vqe_history.csv`.

### Java 17

Compile:

`javac VQEApplication.java`

Execute:

`java VQEApplication`

The application generates `vqe_report.txt`.

### PostgreSQL

Execute the SQL script using a PostgreSQL database account with permission to create schemas, tables, functions, procedures, and triggers.

The script creates the `quantum_lab` schema, populates the example records, executes the experiment workflow, and runs reporting queries.

The database transaction protects the setup and sample operations from partial completion if an error occurs.

## 19. Implementation Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Primary role | Numerical VQE model | Event-driven experiment execution | Numerical optimization engine | Enterprise experiment service | Experiment data management |
| Quantum state | Complex amplitudes | Complex-value objects | Complex-value structure | Immutable complex record | Not stored directly |
| Hamiltonian | Pauli terms | Pauli terms | Pauli terms | Immutable Pauli terms | Relational Pauli terms |
| Optimization | Gradient descent | Gradient descent | Gradient descent | Policy-driven gradient descent | Optimization history |
| Measurement | Shot simulation | Shot simulation | Shot simulation | Shot simulation | Measurement records |
| Audit | JSON | JSON | CSV | Text report | Relational records |
| Validation | Exceptions and assertions | Domain exceptions | Exceptions | Domain exceptions | Constraints and triggers |

The implementations share the same mathematical example but emphasize different engineering responsibilities.

Python emphasizes numerical clarity, JavaScript emphasizes asynchronous monitoring, C++17 emphasizes efficient numerical execution, Java 17 emphasizes domain modeling and experiment governance, and PostgreSQL emphasizes persistent research data integrity.

## 20. Evaluation Criteria

A VQE implementation should be evaluated using more than its final reported energy.

Important evaluation dimensions include:

| Metric | Purpose |
|---|---|
| Energy error | Measures deviation from a reference energy |
| Convergence rate | Measures optimization progress |
| Circuit depth | Indicates circuit execution complexity |
| Parameter count | Indicates optimization dimensionality |
| Measurement shots | Measures sampling effort |
| Gradient stability | Evaluates optimization reliability |
| State fidelity | Measures similarity to the reference quantum state |
| Execution time | Measures computational efficiency |
| Noise sensitivity | Evaluates robustness under imperfect execution |
| Reproducibility | Measures consistency across repeated experiments |

For the included one-qubit Hamiltonian, the analytical ground-state energy provides an exact numerical reference.

For larger quantum systems, obtaining a reference ground-state energy may itself require substantial classical computation.

The difference between a variational energy estimate and the reference energy should therefore always be interpreted in the context of the Hamiltonian, ansatz expressibility, optimization procedure, measurement uncertainty, and execution environment.
