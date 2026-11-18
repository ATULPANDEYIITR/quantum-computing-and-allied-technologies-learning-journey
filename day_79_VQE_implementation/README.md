# Variational Quantum Eigensolver: Molecular Energy Optimization

## 1. Problem Definition

The Variational Quantum Eigensolver (VQE) is a hybrid quantum-classical optimization algorithm used to estimate the ground-state energy of a quantum system.

Its primary objective is to find the minimum eigenvalue of a molecular Hamiltonian:

\[
H|\psi\rangle=E|\psi\rangle
\]

where:

- \(H\) is the Hamiltonian describing the physical system.
- \(|\psi\rangle\) is a quantum state.
- \(E\) is the corresponding energy eigenvalue.

The ground-state energy is:

\[
E_0=\min_{\|\psi\|=1}\langle\psi|H|\psi\rangle
\]

VQE constructs a parameterized quantum state and optimizes its parameters to minimize the expected energy.

The implementations use molecular hydrogen, H2, as a compact quantum chemistry example.

The problem is deliberately reduced to two qubits so that the complete Hamiltonian, quantum circuit, statevector, optimization process, and exact reference solution can be examined.

## 2. Molecular Hydrogen and the Hamiltonian

Molecular hydrogen contains two electrons and two nuclei.

The electronic Hamiltonian describes the interactions between electrons and nuclei, including electron kinetic energy, electron-nuclear attraction, and electron-electron repulsion.

A quantum chemistry calculation generally begins with:

1. Defining molecular geometry.
2. Selecting a basis set.
3. Constructing molecular orbitals.
4. Building the electronic Hamiltonian.
5. Mapping fermionic operators to qubit operators.
6. Reducing the qubit representation where justified.

The implementations use a commonly employed reduced two-qubit H2 Hamiltonian:

\[
\begin{aligned}
H={}&-1.052373245772859I\\
&+0.39793742484318045ZI\\
&-0.39793742484318045IZ\\
&-0.01128010425623538ZZ\\
&+0.18093119978423156XX
\end{aligned}
\]

All coefficients are expressed in Hartree.

The Pauli operators are:

| Operator | Matrix | Function |
|---|---|---|
| \(I\) | Identity | Leaves the state unchanged |
| \(X\) | Bit-flip | Exchanges computational basis states |
| \(Y\) | Phase and bit-flip | Introduces complex amplitudes |
| \(Z\) | Phase-flip | Changes the sign of the \(|1\rangle\) component |

A two-qubit operator such as \(ZI\) is a tensor product:

\[
ZI=Z\otimes I
\]

The first operator acts on qubit 0 and the second on qubit 1 in these implementations.

The Hamiltonian is Hermitian, ensuring real eigenvalues and physically meaningful energy expectations.

The approximate reference ground-state energy for this reduced model is:

\[
E_0\approx-1.8572750302023802\ Ha
\]

This value is used for numerical validation.

The reference value must not be interpreted as an independently established result from every VQE run. The VQE output depends on the ansatz, initialization, optimization policy, and convergence behavior.

## 3. Mathematical Foundation of VQE

VQE combines quantum-state preparation with classical optimization.

A parameterized state is constructed:

\[
|\psi(\boldsymbol{\theta})\rangle
=U(\boldsymbol{\theta})|0\rangle
\]

where:

- \(U\) is a parameterized quantum circuit.
- \(\boldsymbol{\theta}\) represents adjustable circuit parameters.
- \(|0\rangle\) is the initial computational basis state.

The energy objective is:

\[
E(\boldsymbol{\theta})=
\langle\psi(\boldsymbol{\theta})|
H
|\psi(\boldsymbol{\theta})\rangle
\]

The classical optimizer searches for:

\[
\boldsymbol{\theta}^{*}
=
\arg\min_{\boldsymbol{\theta}}
E(\boldsymbol{\theta})
\]

The minimum energy found by VQE provides an upper bound on the exact ground-state energy when the Hamiltonian, state preparation, and energy evaluation are exact.

This follows from the variational principle:

\[
E(\boldsymbol{\theta})\geq E_0
\]

The quality of the result depends on how effectively the selected ansatz represents the molecular ground state.

## 4. Quantum Circuit and Ansatz

All four programming implementations use the following two-qubit circuit:

\[
|00\rangle
\]

\[
\downarrow
\]

\[
RY(\theta_0)\otimes RY(\theta_1)
\]

\[
\downarrow
\]

\[
CNOT(0,1)
\]

\[
\downarrow
\]

\[
|\psi(\theta_0,\theta_1)\rangle
\]

The rotation gate is:

\[
RY(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

The CNOT gate flips its target qubit when the control qubit is in state \(|1\rangle\).

The circuit creates a parameterized state with the potential for entanglement.

For the specified circuit and real-valued initial state, the resulting amplitudes are:

\[
|\psi\rangle=
\begin{bmatrix}
\cos(\theta_0/2)\cos(\theta_1/2)\\
\cos(\theta_0/2)\sin(\theta_1/2)\\
\sin(\theta_0/2)\sin(\theta_1/2)\\
\sin(\theta_0/2)\cos(\theta_1/2)
\end{bmatrix}
\]

The vector is normalized because the rotation and CNOT operations are unitary.

The ansatz is intentionally compact. It demonstrates VQE mechanics without claiming to represent every possible molecular state or to be an optimal circuit for larger chemistry problems.

## 5. Energy Evaluation

The Hamiltonian is expressed as a weighted sum of Pauli strings:

\[
H=\sum_i c_iP_i
\]

Therefore:

\[
E(\boldsymbol{\theta})=
\sum_i c_i
\langle\psi(\boldsymbol{\theta})|
P_i
|\psi(\boldsymbol{\theta})\rangle
\]

Each Pauli term produces an expectation value.

In the supplied statevector implementations, these expectation values are calculated through matrix-vector operations.

For an actual quantum processor, measurements replace direct statevector access.

The expectation value of an observable is estimated from repeated measurements:

\[
\langle P_i\rangle
\approx
\frac{1}{N}
\sum_{k=1}^{N}p_k
\]

where \(p_k\) represents the measured eigenvalue associated with an individual shot.

For Pauli observables, the measured eigenvalues are generally \(+1\) or \(-1\).

A finite number of shots introduces statistical uncertainty. Increasing the number of shots generally improves measurement precision but increases execution cost.

## 6. Parameter-Shift Gradient

The implementations use the parameter-shift rule rather than ordinary finite-difference differentiation.

For a parameterized rotation generated by a Pauli operator:

\[
\frac{\partial E}{\partial\theta_i}
=
\frac{1}{2}
\left[
E\left(\theta_i+\frac{\pi}{2}\right)
-
E\left(\theta_i-\frac{\pi}{2}\right)
\right]
\]

This method evaluates the objective at two shifted parameter values.

For two parameters, one gradient evaluation requires four shifted energy evaluations.

The parameter-shift rule is particularly useful for quantum circuits because it can estimate gradients through circuit measurements without requiring access to the internal quantum state.

The exact formula applies to the individual Pauli-generated rotations used here. More complicated gates or generators with multiple eigenvalue gaps may require generalized shift rules.

## 7. Classical Optimization with Adam

The optimization layer uses Adam, an adaptive gradient-based optimization algorithm.

Its first moment is:

\[
m_t=\beta_1m_{t-1}+(1-\beta_1)g_t
\]

Its second moment is:

\[
v_t=\beta_2v_{t-1}+(1-\beta_2)g_t^2
\]

Bias-corrected moments are:

\[
\hat m_t=\frac{m_t}{1-\beta_1^t}
\]

\[
\hat v_t=\frac{v_t}{1-\beta_2^t}
\]

The parameter update is:

\[
\theta_t=
\theta_{t-1}
-
\eta
\frac{\hat m_t}
{\sqrt{\hat v_t}+\epsilon}
\]

The supplied default configuration uses:

| Parameter | Value |
|---|---:|
| Learning rate | 0.05 |
| First moment coefficient | 0.9 |
| Second moment coefficient | 0.999 |
| Numerical stabilization | \(10^{-8}\) |
| Maximum iterations | 2,000 |
| Convergence tolerance | \(10^{-9}\) |

These are illustrative numerical settings rather than universal optimal values.

VQE objectives can contain local minima, flat regions, and parameter-dependent convergence behavior. Different initial parameters can produce different optimization trajectories.

A robust research workflow should evaluate multiple initializations and compare the resulting energies.

## 8. Python Implementation

The Python implementation provides a complete statevector-based VQE workflow.

### Main components

| Component | Responsibility |
|---|---|
| `PauliTerm` | Represents a Hamiltonian term |
| `Hamiltonian` | Builds the molecular Hamiltonian |
| `QuantumAnsatz` | Constructs the parameterized state |
| `AdamOptimizer` | Minimizes the energy objective |
| `VQEExperiment` | Coordinates the optimization |
| `OptimizationRecord` | Stores iteration-level results |
| `VQEResult` | Stores final experiment information |

### Implementation decisions

NumPy is used for complex matrices, tensor products, statevector operations, and exact diagonalization.

The `Hamiltonian` class constructs the full matrix from Pauli operators.

The quantum circuit uses tensor reshaping to apply single-qubit gates and computational-basis indexing for CNOT.

The parameter-shift gradient is implemented independently of the optimizer. This separation allows the gradient method to be tested or replaced without redesigning the circuit.

Adam maintains first and second moments and applies bias correction.

The experiment records energy, gradient norm, and parameters for every optimization iteration.

The JSON export uses a temporary file followed by an atomic replacement to reduce the possibility of leaving a partially written result file.

### Measurement simulation

The Python implementation samples the final computational-basis state using a multinomial distribution.

The resulting counts represent a simulated measurement experiment, not actual hardware measurements.

The measurement simulation is reproducible when the random seed remains unchanged.

### Execution

Requirements:

- Python 3.10 or later.
- NumPy.

Install NumPy and execute the file using Python.

The program reports optimized energy, reference energy, absolute error, convergence status, parameter values, and measurement counts.

## 9. JavaScript Implementation

The JavaScript implementation uses an event-driven experiment architecture.

Its central design decision is to separate quantum-state operations from experiment orchestration.

### Main components

| Component | Responsibility |
|---|---|
| `QuantumState` | Maintains complex amplitudes |
| `MolecularHamiltonian` | Evaluates Pauli expectations |
| `HardwareEfficientAnsatz` | Constructs parameterized states |
| `GradientCalculator` | Calculates parameter-shift gradients |
| `AdamOptimizer` | Updates circuit parameters |
| `MeasurementService` | Samples computational-basis outcomes |
| `VQEExperiment` | Manages experiment lifecycle |

Complex values are represented as pairs of real and imaginary numbers.

This avoids external numerical dependencies.

`Map` is used for measurement counts, and `EventEmitter` exposes experiment lifecycle events.

The experiment supports the following states:

\[
CREATED\rightarrow RUNNING\rightarrow COMPLETED
\]

Failure and cancellation produce separate terminal states.

The asynchronous optimizer periodically yields to the Node.js event loop. This makes cancellation and monitoring possible without converting the numerical operations into a line-by-line asynchronous implementation.

An `AbortSignal` can be supplied to stop an active optimization.

The result is persisted as JSON through Node.js file operations.

### Execution

Requirements:

- Node.js 18 or later.

Execute the JavaScript file using Node.js.

No npm packages are required.

## 10. C++17 Implementation

The C++ implementation emphasizes computational control and explicit mathematical operations.

### Main components

| Component | Responsibility |
|---|---|
| `PauliTerm` | Defines operator coefficients |
| `MolecularHamiltonian` | Builds and evaluates the Hamiltonian |
| `QuantumCircuit` | Applies rotation and entanglement gates |
| `VariationalObjective` | Calculates energy and gradients |
| `AdamOptimizer` | Performs parameter optimization |
| `OptimizationResult` | Stores optimization history |
| `RepositoryIndependentExperiment` | Manages execution state |

The implementation uses:

- `std::array` for fixed-size quantum states.
- `std::vector` for Hamiltonian terms and optimization history.
- `std::complex<double>` for complex amplitudes.
- `std::hypot` for gradient norm calculation.
- Standard exceptions for invalid configurations and numerical failures.

The exact ground-state energy is obtained through a Jacobi diagonalization procedure for a real symmetric matrix.

This provides an independent reference against which the variational result can be checked.

### Compilation

Use a C++17-compatible compiler.

The implementation has no external library requirements.

Compile with optimization enabled and execute the resulting program.

## 11. Java 17 Enterprise Implementation

The Java implementation uses explicit domain types and service-oriented architecture.

### Domain architecture

| Component | Responsibility |
|---|---|
| `PauliTerm` | Immutable Hamiltonian term |
| `Hamiltonian` | Molecular operator and exact reference calculation |
| `OptimizationPolicy` | Controls optimizer behavior |
| `EnergyObjective` | Defines objective and gradient operations |
| `QuantumCircuit` | Constructs the quantum state |
| `OptimizationService` | Performs optimization |
| `ExperimentService` | Manages experiment lifecycle |
| `ExperimentResult` | Immutable experiment output |

Java records represent immutable scientific data.

The `EnergyObjective` interface separates mathematical evaluation from the optimization algorithm.

The optimization policy validates all important parameters before execution.

The experiment service prevents invalid state transitions and verifies the variational energy bound.

The final result includes the exact reference energy, optimized energy, absolute error, iteration count, convergence indicator, and immutable optimization history.

### Enterprise considerations

A larger deployment could separate the molecular Hamiltonian repository, experiment orchestration, quantum execution backend, and persistent result service.

Experiment identifiers, policy versions, circuit configurations, and measurement provenance should be retained for reproducibility.

The supplied program implements the numerical and domain logic directly rather than introducing external infrastructure.

### Compilation

Requirements:

- Java 17.

Compile the source as `VQEApplication.java` and run the `VQEApplication` class.

No third-party dependencies are required.

## 12. PostgreSQL Data Model

The SQL implementation provides a relational model for managing VQE experiments.

### Entity relationships

Molecules
|
+-- Hamiltonians
|   |
|   +-- Hamiltonian Terms
|
+-- Experiments
    |
    +-- Ansatz Definitions
    |
    +-- Optimization Policies
    |
    +-- Experiment Parameters
    |
    +-- Optimization Iterations
    |
    +-- Measurements
    |
    +-- Experiment Validations

### Main tables

| Table | Purpose |
|---|---|
| `molecules` | Molecular identity and geometry |
| `hamiltonians` | Qubit Hamiltonian definitions |
| `hamiltonian_terms` | Pauli strings and coefficients |
| `ansatz_definitions` | Quantum circuit configurations |
| `optimization_policies` | Optimizer settings |
| `experiments` | Experiment lifecycle and final results |
| `experiment_parameters` | Optimized parameter values |
| `optimization_iterations` | Iteration-level energy history |
| `measurements` | Basis measurement counts |
| `experiment_validations` | Numerical validation results |

### Integrity controls

Primary keys identify individual records.

Foreign keys enforce relationships between molecules, Hamiltonians, circuits, policies, and experiments.

Unique constraints prevent duplicate Pauli terms, parameter indices, and iteration numbers.

Check constraints validate physical and numerical ranges.

Triggers enforce consistency between the Hamiltonian's qubit count and its Pauli strings.

Additional triggers verify that an ansatz and its Hamiltonian use the same number of qubits.

Experiment state transitions are constrained so that completed, failed, and cancelled experiments cannot be reopened through ordinary status updates.

Iteration records can only be added while an experiment is running.

### Stored procedures

`record_iteration` records sequential optimization iterations.

It locks the corresponding experiment row and verifies the expected next iteration number.

`complete_experiment` stores the final energy, reference energy, absolute error, convergence indicator, and terminal experiment state.

Both procedures support transactional database operations.

### Eligibility determination

`check_experiment_eligibility` verifies:

- Experiment existence.
- Running status.
- Hamiltonian availability.
- Presence of Hamiltonian terms.
- Completeness of the initial parameter vector.

It returns an eligibility decision and an explanatory reason.

### Reporting views

`v_experiment_summary` combines molecular and experiment information.

`v_energy_convergence` uses SQL window functions to calculate energy changes and the best observed energy at each iteration.

`v_measurement_statistics` aggregates recorded measurement counts and probabilities.

The reporting queries provide experiment-level performance, convergence, validation, and measurement information.

### Data provenance

The database separates experimental measurements from optimized energies.

It also distinguishes the exact reference energy from the result produced by a particular variational run.

This distinction is essential when comparing experiments, optimizer policies, circuit configurations, and measurement strategies.

The SQL demonstration records representative iteration data. These illustrative database records are not claimed to be the measured output of the independently executed Python, JavaScript, C++17, or Java 17 programs.

## 13. Exact Diagonalization Versus VQE

Exact diagonalization and VQE solve related problems using different computational strategies.

| Characteristic | Exact diagonalization | VQE |
|---|---|---|
| Objective | Compute Hamiltonian eigenvalues | Minimize variational energy |
| State representation | Classical matrix representation | Parameterized quantum circuit |
| Optimization | Not required | Classical optimization required |
| Quantum hardware | Not required | Optional hardware execution |
| Reference quality | Exact within the modeled Hamiltonian | Depends on ansatz and optimization |
| Scaling | Exponential state-space growth | Depends on circuit, measurements, and optimization |

For \(n\) qubits, the statevector contains:

\[
2^n
\]

complex amplitudes.

A dense Hamiltonian matrix contains:

\[
4^n
\]

complex entries.

Consequently, exact dense matrix methods become expensive as the number of qubits increases.

VQE avoids explicitly requiring a full Hamiltonian eigendecomposition on quantum hardware. Its practical cost is transferred to circuit execution, measurement sampling, and classical optimization.

The small H2 problem used here remains suitable for exact classical verification.

## 14. Measurement Noise and Hardware Execution

The source implementations use exact statevector expectation values during optimization.

They also provide computational-basis sampling demonstrations.

A real quantum processor introduces additional complications:

- Gate errors.
- Readout errors.
- Decoherence.
- Shot noise.
- Circuit compilation overhead.
- Connectivity constraints.
- Calibration drift.

For a hardware experiment, each Pauli term must be measured in an appropriate basis.

Compatible commuting Pauli terms can sometimes be grouped to reduce the number of measurement circuits.

The estimated energy then becomes:

\[
\hat E=\sum_i c_i\hat P_i
\]

where \(\hat P_i\) is the experimentally estimated expectation value.

The uncertainty of the total energy depends on measurement variance, coefficient magnitudes, shot allocation, and correlations introduced by measurement grouping.

A hardware implementation should therefore maintain measurement counts, basis configurations, calibration information, and statistical uncertainty separately from optimizer convergence information.

## 15. Important Numerical and Scientific Limitations

The implementations are educational numerical models rather than complete production quantum chemistry packages.

Their limitations include:

- The molecular system is represented by a reduced two-qubit Hamiltonian.
- The Hamiltonian is supplied directly rather than generated from molecular integrals.
- The ansatz uses only two rotation parameters and one entangling gate.
- The optimizer uses a single initialization in the main execution path.
- The statevector model does not simulate realistic hardware noise.
- Computational-basis measurement does not independently measure every Pauli term.
- The measurement sampling demonstrations do not replace a complete chemistry measurement pipeline.
- The reference energy is tied to the specified reduced Hamiltonian and must not be generalized to arbitrary molecular geometries or basis sets.

The chosen ansatz is not guaranteed to reach the ground state for every Hamiltonian.

A failure to converge does not necessarily indicate an error in the Hamiltonian. It can result from insufficient ansatz expressibility, an unsuitable initial point, optimizer settings, or numerical behavior.

A production-grade study should also examine multiple initializations, energy variance, parameter sensitivity, shot allocation, uncertainty intervals, and hardware execution fidelity.

## 16. Computational Complexity

Let:

- \(n\) represent the number of qubits.
- \(L\) represent the number of Hamiltonian terms.
- \(P\) represent the number of ansatz parameters.
- \(T\) represent the number of optimization iterations.

For statevector simulation, storing the quantum state requires:

\[
O(2^n)
\]

memory.

Applying a one-qubit gate through a direct statevector operation requires:

\[
O(2^n)
\]

time.

For \(L\) Pauli terms, a direct statevector energy evaluation requires approximately:

\[
O(L2^n)
\]

time.

With parameter-shift differentiation, one gradient evaluation requires approximately \(2P\) additional energy evaluations.

The total optimization cost is approximately:

\[
O(TPL2^n)
\]

for the supplied parameter-shift implementation, ignoring constant factors and the final objective evaluations.

Exact dense diagonalization has substantially higher memory requirements because it explicitly stores a matrix of dimension \(2^n\times2^n\).

The exact diagonalization routines in these implementations are restricted to four-dimensional matrices, making them appropriate for validation of the two-qubit example.

## 17. Reproducibility and Experiment Governance

A scientifically reproducible VQE experiment should preserve:

- Molecular geometry.
- Basis set.
- Hamiltonian coefficients.
- Qubit mapping.
- Ansatz structure.
- Initial parameter values.
- Optimizer configuration.
- Random seeds.
- Measurement basis.
- Shot counts.
- Iteration history.
- Convergence criteria.
- Final energy.
- Reference energy.
- Numerical validation results.

The SQL schema separates these elements into related entities.

The source programs preserve optimization histories and use explicit numerical configurations.

A result should only be compared with another experiment when the underlying molecular configuration, Hamiltonian representation, and energy units are consistent.

The distinction between a converged optimizer and a scientifically accurate ground-state estimate is particularly important. Convergence indicates that the selected numerical procedure has met its stopping conditions. It does not independently establish that the ansatz has reached the true ground state.
