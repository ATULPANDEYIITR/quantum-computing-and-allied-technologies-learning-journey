# Quantum Feature Maps: Encoding Classical Data into Quantum States

## 1. Introduction

A quantum feature map is a mathematical transformation that converts a classical feature vector into a quantum state.

Classical machine learning represents an observation using a numerical vector:

\[
x = (x_1,x_2,\ldots,x_d)
\]

A quantum feature map transforms this vector into a quantum state:

\[
\phi:x\longrightarrow |\phi(x)\rangle
\]

The encoded state belongs to a Hilbert space whose dimension grows exponentially with the number of qubits.

For a system containing \(n\) qubits, the state is represented as:

\[
|\phi(x)\rangle =
\sum_{j=0}^{2^n-1}\alpha_j(x)|j\rangle
\]

where:

- \(n\) is the number of qubits.
- \(|j\rangle\) represents a computational basis state.
- \(\alpha_j(x)\) is a complex probability amplitude.
- The amplitudes satisfy the normalization condition:

\[
\sum_{j=0}^{2^n-1}|\alpha_j(x)|^2=1
\]

The six deliverables implement classical feature preprocessing, quantum state encoding, statevector simulation, fidelity-based kernel evaluation, and experimental data management.

## 2. Mathematical Foundations

### 2.1 Classical feature vectors

A dataset consists of observations with numerical features.

For example:

| Sample | Feature 1 | Feature 2 | Feature 3 |
|---|---:|---:|---:|
| A | 0.2 | 0.4 | 0.6 |
| B | 0.3 | 0.7 | 0.5 |
| C | 0.8 | 0.2 | 0.9 |
| D | 0.9 | 0.6 | 0.1 |

Each feature can be assigned to a qubit or transformed into a circuit parameter.

The relationship between classical dimensions and qubits is an implementation decision, not a universal requirement. Some feature maps use several circuit parameters per qubit, while others reduce dimensionality before encoding.

### 2.2 Feature normalization

Quantum gates operate on rotation angles. Unbounded classical values can produce unnecessarily large parameters and repeated rotations.

Min-max normalization maps values into a specified interval:

\[
x'_i =
a+
\frac{x_i-x_{\min}}{x_{\max}-x_{\min}}
(b-a)
\]

The implementations use the interval:

\[
[-\pi,\pi]
\]

Constant-valued features are mapped to the interval midpoint to avoid division by zero.

Normalization parameters should be learned from training data and reused for validation and test data. Computing them independently for each sample changes the representation and can introduce data leakage.

### 2.3 Qubit representation

A single qubit is represented by:

\[
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
\]

Its normalization requirement is:

\[
|\alpha|^2+|\beta|^2=1
\]

The computational basis states are:

\[
|0\rangle=
\begin{bmatrix}
1\\0
\end{bmatrix},
\qquad
|1\rangle=
\begin{bmatrix}
0\\1
\end{bmatrix}
\]

For multiple qubits, the complete statevector is constructed using tensor products.

For three qubits, the statevector contains eight complex amplitudes.

### 2.4 Quantum gates as encoding operations

A quantum feature map is generally implemented as a parameterized unitary transformation:

\[
|\phi(x)\rangle=U_{\phi}(x)|0\rangle^{\otimes n}
\]

The circuit parameters depend on classical input features.

The unitary transformation preserves state normalization and quantum inner products.

The encoded state is not simply a classical vector stored in a different format. It is a representation produced through quantum operations.

## 3. Feature Encoding Mechanisms

### 3.1 Angle encoding

Angle encoding maps classical values to single-qubit rotation parameters.

The Y-axis rotation is:

\[
R_Y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

Applying this operation to the initial state gives:

\[
R_Y(x_i)|0\rangle
=
\cos(x_i/2)|0\rangle+
\sin(x_i/2)|1\rangle
\]

For three features:

\[
|\phi(x)\rangle=
R_Y(x_1)\otimes R_Y(x_2)\otimes R_Y(x_3)
|000\rangle
\]

Angle encoding is relatively simple and provides direct feature-to-parameter correspondence.

Its principal limitation is that independent rotations do not automatically introduce entanglement between qubits.

The Python, JavaScript, C++17, and Java implementations provide this encoding through the `ANGLE` configuration.

### 3.2 Z-axis rotation

The Z-axis rotation is:

\[
R_Z(\theta)=
\begin{bmatrix}
e^{-i\theta/2}&0\\
0&e^{i\theta/2}
\end{bmatrix}
\]

Unlike an RY rotation, an RZ gate changes the relative phase between computational basis components without changing their probabilities.

Phase information becomes particularly important when subsequent operations cause interference.

### 3.3 ZZ feature maps

A ZZ feature map introduces pairwise interactions between features.

The two-qubit interaction is:

\[
U_{ZZ}(\theta)=
e^{-i\theta Z_iZ_j/2}
\]

Here, \(Z_i\) and \(Z_j\) are Pauli-Z operators acting on different qubits.

For a feature vector with three dimensions, the pairwise interactions are:

\[
(x_1,x_2),\quad
(x_1,x_3),\quad
(x_2,x_3)
\]

A representative interaction parameter is:

\[
\theta_{ij}=\lambda x_ix_j
\]

where \(\lambda\) controls the interaction strength.

The implementation applies local rotations followed by diagonal ZZ interactions.

This creates input-dependent relative phases and can produce entanglement.

The number of pairwise interactions for a fully connected feature map is:

\[
N_{\text{pairs}}=\frac{n(n-1)}{2}
\]

A fully connected circuit can increase circuit depth and hardware execution cost.

### 3.4 IQP-inspired encoding

Instantaneous Quantum Polynomial-time-inspired feature maps use structured quantum operations, especially diagonal interactions.

The implementation provides a simplified IQP-inspired circuit using:

- RY rotations.
- RZ rotations.
- Pairwise diagonal ZZ interactions.

Its interaction parameters depend on products of classical features.

This implementation is an educational circuit construction, not a claim that every IQP circuit has the same structure or computational complexity.

### 3.5 Repeated feature maps

Feature-map repetitions increase the number of encoding layers:

\[
U_{\phi}(x)=
U_L(x)U_{L-1}(x)\cdots U_1(x)
\]

Repeated layers can increase the expressive capacity of the circuit.

They also introduce additional gates, greater circuit depth, and potential sensitivity to hardware noise.

The source implementations expose repetitions as a configurable parameter.

## 4. Quantum Statevector Simulation

### 4.1 Statevector representation

The simulator represents a quantum state using a one-dimensional array of complex numbers.

For three qubits:

\[
|\psi\rangle =
\begin{bmatrix}
\alpha_0&
\alpha_1&
\alpha_2&
\alpha_3&
\alpha_4&
\alpha_5&
\alpha_6&
\alpha_7
\end{bmatrix}^{T}
\]

The amplitudes correspond to:

| Index | Basis state |
|---:|---|
| 0 | \(|000\rangle\) |
| 1 | \(|001\rangle\) |
| 2 | \(|010\rangle\) |
| 3 | \(|011\rangle\) |
| 4 | \(|100\rangle\) |
| 5 | \(|101\rangle\) |
| 6 | \(|110\rangle\) |
| 7 | \(|111\rangle\) |

The implementations use a consistent convention in which the least significant index bit identifies qubit zero.

### 4.2 Applying single-qubit gates

For a gate acting on qubit \(q\), the simulator identifies pairs of amplitudes that differ only in that qubit.

The RY transformation updates each pair:

\[
\begin{bmatrix}
\alpha'_0\\
\alpha'_1
\end{bmatrix}
=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\begin{bmatrix}
\alpha_0\\
\alpha_1
\end{bmatrix}
\]

This avoids constructing a full \(2^n\times2^n\) gate matrix.

The simulator performs updates directly on the statevector.

### 4.3 Applying diagonal gates

RZ and ZZ operations are diagonal in the computational basis.

Each amplitude is multiplied by a complex phase:

\[
\alpha_j'=\alpha_j e^{i\theta_j}
\]

This makes diagonal gate execution relatively efficient because it does not require exchanging amplitude pairs.

### 4.4 State normalization

A valid pure quantum state must satisfy:

\[
\langle\psi|\psi\rangle=1
\]

The implementations validate this property after encoding.

A failed normalization check indicates a numerical or implementation error.

The simulators also reject non-finite amplitudes, invalid feature dimensions, and unsupported circuit configurations.

## 5. Quantum Feature Kernels

Quantum feature maps can be used to construct kernel functions.

A quantum kernel compares two encoded states:

\[
K(x,y)=
|\langle\phi(x)|\phi(y)\rangle|^2
\]

The quantity inside the absolute-value operation is the complex inner product.

For two states:

\[
|\phi(x)\rangle=\sum_i a_i|i\rangle
\]

\[
|\phi(y)\rangle=\sum_i b_i|i\rangle
\]

their overlap is:

\[
\langle\phi(x)|\phi(y)\rangle
=
\sum_i a_i^*b_i
\]

The fidelity kernel is:

\[
K(x,y)=
\left|\sum_i a_i^*b_i\right|^2
\]

### 5.1 Kernel properties

For normalized pure quantum states:

\[
0\leq K(x,y)\leq1
\]

Identical states have:

\[
K(x,x)=1
\]

The kernel is symmetric:

\[
K(x,y)=K(y,x)
\]

The fidelity kernel is positive semidefinite because it can be represented as an inner product in an expanded feature space of density matrices.

A Gram matrix is constructed as:

\[
K_{ij}=K(x_i,x_j)
\]

This matrix can be supplied to a classical kernel-learning algorithm, including a support vector machine.

A real quantum processor can estimate the overlap using a suitable circuit, such as an inverse feature-map construction or a SWAP-test-based procedure.

The source implementations calculate exact overlaps from simulated statevectors.

## 6. Measurement and Probability Distributions

Quantum measurement converts amplitudes into classical outcomes.

For a computational basis state:

\[
P(j)=|\alpha_j|^2
\]

For example, if:

\[
|\psi\rangle=
\frac{1}{\sqrt{2}}|0\rangle+
\frac{1}{\sqrt{2}}|1\rangle
\]

then:

\[
P(0)=0.5,\qquad P(1)=0.5
\]

A measurement experiment repeats the process over multiple shots.

The observed frequency approximates the theoretical probability:

\[
\hat P(j)=\frac{N_j}{N}
\]

where:

- \(N_j\) is the number of observations of outcome \(j\).
- \(N\) is the total number of shots.

The implementations provide seeded measurement simulation for reproducibility.

The measurement results are estimates, whereas statevector probabilities are exact up to floating-point precision.

## 7. Python Implementation

The Python script uses standard-library features to provide a self-contained simulator.

| Component | Implementation |
|---|---|
| Feature representation | Frozen dataclass |
| Encoding configuration | Enum and dataclass |
| Input validation | Custom exceptions |
| Quantum state | Complex-number list |
| Single-qubit operations | RY and RZ functions |
| Entanglement | ZZ interaction |
| Kernel evaluation | Fidelity calculation |
| Measurement | Weighted random sampling |
| Testing | Assertions and validation cases |
| Reporting | Console output and JSON |

The `FeatureVector` class provides feature validation and normalization.

`FeatureMapConfig` defines the circuit configuration.

`QuantumFeatureMap` implements the gate operations and encoding workflow.

`QuantumState` verifies normalization and provides measurement probabilities.

`QuantumKernel` evaluates state overlaps and constructs kernel matrices.

The script demonstrates all three encoding configurations using the same dataset.

## 8. JavaScript Implementation

The JavaScript implementation provides an event-driven simulation architecture.

It uses `Float64Array` objects to maintain separate real and imaginary amplitude components.

This design avoids allocating a large number of temporary complex-number objects during gate execution.

| Component | Responsibility |
|---|---|
| `ComplexVector` | Complex statevector storage |
| `FeatureDataset` | Dataset validation and normalization |
| `QuantumCircuit` | Circuit construction and gate operations |
| `QuantumKernelService` | Fidelity and kernel matrix calculation |
| `ExperimentRunner` | Asynchronous execution and events |

The experiment runner extends `EventTarget`.

It publishes:

- `sampleencoded`
- `completed`
- `cancelled`

The asynchronous execution method yields control between samples. This allows event handlers and cancellation requests to execute.

The simulator uses a deterministic pseudorandom generator for measurement sampling.

The implementation is useful for understanding how quantum experiment execution can be integrated into a larger asynchronous application.

## 9. C++17 Implementation

The C++ implementation emphasizes explicit state management, value ownership, and efficient numerical operations.

| Component | Responsibility |
|---|---|
| `FeatureVector` | Validated classical input |
| `QuantumState` | Statevector and normalization |
| `CircuitConfig` | Encoding policy |
| `QuantumFeatureMap` | Gate execution |
| `QuantumKernel` | Fidelity and matrix evaluation |
| `MeasurementSimulator` | Repeated measurements |

The program uses `std::complex<double>` to represent amplitudes.

STL containers provide state storage and experiment datasets.

`std::discrete_distribution` performs measurement sampling according to state probabilities.

The gate implementation operates directly on paired amplitudes or diagonal phase factors.

This approach avoids the memory overhead of explicitly materializing full gate matrices.

The program can be compiled with a C++17-compatible compiler.

## 10. Java 17 Enterprise Implementation

The Java implementation introduces explicit domain types and experiment lifecycle management.

Its immutable records represent:

- Classical feature vectors.
- Feature-map policies.
- Complex values.

The `FeatureMapEncoder` is responsible for translating validated feature vectors into quantum states.

The `QuantumKernelService` evaluates similarity between encoded observations.

The `ExperimentService` controls experiment execution and records its state.

The experiment lifecycle is:

`CREATED -> VALIDATED -> ENCODING -> COMPLETED`

Execution errors produce:

`FAILED`

The service validates policy constraints before encoding and returns immutable collections of generated states.

This separation makes the implementation suitable as a foundation for a larger experiment-management application.

## 11. PostgreSQL Data Model

The SQL implementation manages the relational workflow surrounding quantum feature-map experiments.

It separates classical observations, encoding configurations, generated states, and kernel results.

### 11.1 Entity relationships

The main relationships are:

- A dataset contains multiple samples.
- Each sample contains a classical feature vector.
- A feature-map configuration defines the encoding method.
- An experiment associates one dataset with one feature map.
- An experiment contains multiple encoded quantum states.
- Kernel evaluations compare pairs of encoded states.
- Experiment events record execution history.

Conceptual relationship:

`Dataset -> Samples -> Experiments -> Quantum States -> Kernel Evaluations`

`Feature Maps -> Experiments`

`Experiments -> Audit Events`

### 11.2 Dataset management

The `datasets` table stores dataset-level metadata.

The `dataset_samples` table stores numerical feature vectors using PostgreSQL arrays.

The sample-validation trigger checks that:

- The vector is not empty.
- Its dimension matches the dataset configuration.
- Every value is finite.
- The referenced dataset exists.

A separate trigger maintains the sample count when records are inserted, updated, or deleted.

### 11.3 Feature-map configuration

The `feature_maps` table stores:

- Encoding type.
- Number of repetitions.
- Entanglement strength.
- Configuration name.
- Description.

The encoding type uses a PostgreSQL enum to prevent unsupported values.

### 11.4 Experiment management

The `experiments` table associates a dataset with a feature-map configuration.

It stores normalization limits, execution status, maximum qubit limits, and requested measurement shots.

The transition trigger prevents invalid lifecycle changes.

The experiment eligibility function checks dataset availability, feature dimensions, qubit limits, and experiment status before execution.

### 11.5 Quantum state persistence

The `quantum_states` table stores statevector metadata and amplitudes.

Real and imaginary components are stored separately because PostgreSQL arrays do not directly provide a complex-number data type.

For an \(n\)-qubit state:

\[
D=2^n
\]

The state record must contain exactly \(D\) real amplitudes and \(D\) imaginary amplitudes.

A database trigger verifies:

- Experiment and sample ownership.
- Qubit count.
- Statevector dimension.
- Finite amplitudes.
- State normalization.

The database stores validated results. It does not perform quantum gate execution.

### 11.6 Kernel evaluation

The `kernel_evaluations` table stores pairwise fidelity measurements.

Its constraints enforce:

- Fidelity values between zero and one.
- State ownership by the same experiment.
- Equal qubit counts.
- Canonical ordering of state identifiers.
- Unique state-pair evaluations per experiment.

The `experiment_kernel_report` view provides aggregated evaluation metrics.

### 11.7 Audit and reporting

The `experiment_events` table maintains an execution history.

The reporting views support:

- Dataset integrity checks.
- Experiment monitoring.
- State normalization validation.
- Kernel statistics.
- Missing-state detection.
- Experiment execution reporting.

Indexes support common filtering and joins by dataset, experiment, status, and state identifiers.

The transaction groups schema creation, sample insertion, experiment setup, example state insertion, and execution updates into one atomic operation.

## 12. Comparison of Feature Encoding Methods

| Property | Angle encoding | ZZ feature map | IQP-inspired map |
|---|---|---|---|
| Classical parameters | Rotation angles | Rotations and interactions | Rotations and diagonal interactions |
| Entanglement | Not inherently generated | Can generate entanglement | Can generate entanglement |
| Feature interactions | Primarily local | Pairwise | Pairwise |
| Circuit complexity | Relatively low | Higher | Depends on interaction structure |
| Parameter sensitivity | Rotation-dependent | Rotation and interaction-dependent | Phase and interaction-dependent |
| Implementation | Simple | More complex | Structured diagonal operations |

No encoding method is universally superior.

The appropriate choice depends on the dataset, learning objective, circuit architecture, available hardware, noise conditions, and computational budget.

## 13. Computational Complexity

For \(n\) qubits, a full statevector contains:

\[
2^n
\]

complex amplitudes.

Statevector memory grows exponentially:

\[
M=O(2^n)
\]

A single-qubit gate can be applied in:

\[
O(2^n)
\]

time.

A fully connected pairwise ZZ layer contains:

\[
\frac{n(n-1)}{2}
\]

interactions.

Direct application of all these diagonal interactions requires:

\[
O(n^2 2^n)
\]

time per layer in the implementations.

For a dataset containing \(m\) samples, direct pairwise kernel computation requires:

\[
O(m^2 2^n)
\]

time after encoding.

Storing a dense kernel matrix requires:

\[
O(m^2)
\]

memory.

These costs explain why exact statevector simulation becomes impractical as qubit counts increase.

The source programs enforce a 20-qubit simulation limit. This is a conservative implementation limit, not a fundamental limit on quantum hardware.

## 14. Practical Failure Conditions

| Failure condition | Validation mechanism |
|---|---|
| Empty feature vector | Input validation |
| NaN or infinite values | Finite-number checks |
| Inconsistent feature dimensions | Dataset validation |
| Invalid rotation configuration | Policy validation |
| Zero repetitions | Configuration constraint |
| Invalid qubit count | Simulation limit |
| Non-normalized state | Statevector validation |
| Different state dimensions | Kernel validation |
| Invalid fidelity | Range validation |
| Incorrect SQL sample dimension | Database trigger |
| Experiment lifecycle conflict | Transition trigger |
| Cross-experiment state comparison | Database ownership trigger |

An invalid input should be rejected before it reaches the gate-execution stage.

## 15. Security and Data Governance

Quantum feature-map experiments may process confidential scientific, financial, medical, or commercial data.

Important controls include:

- Validate all externally supplied feature values.
- Restrict access to datasets and experiment records.
- Avoid storing identifiable information when numerical features are sufficient.
- Separate experiment configuration permissions from execution permissions.
- Maintain audit events for execution and configuration changes.
- Restrict database roles to the minimum required privileges.
- Avoid exposing raw feature vectors in operational logs.
- Protect stored amplitudes and experimental results.
- Apply appropriate retention and deletion policies.

Quantum encoding does not automatically anonymize or encrypt classical information.

A quantum state may retain information about its original input, depending on the encoding function and measurement procedure.

## 16. Simulation Versus Quantum Hardware

The implementations in this project use classical statevector simulation.

They calculate the complete quantum state using classical memory and numerical operations.

This differs from execution on a physical quantum processor.

| Characteristic | Statevector simulation | Quantum hardware |
|---|---|---|
| State representation | Complete amplitude vector | Physical quantum state |
| Noise | Ideal unless explicitly modeled | Gate, readout and environmental noise |
| Measurement | Classical probability sampling | Physical measurement |
| Memory | Exponential in qubit count | Not a complete classical statevector |
| Fidelity | Calculated from amplitudes | Estimated using quantum circuits |
| Execution | Classical computation | Quantum processor |

The source programs are suitable for studying encoding mathematics, circuit construction, and kernel evaluation.

They do not claim quantum computational advantage.

## 17. Limitations

The implementations deliberately use a restricted set of operations.

They do not implement:

- General arbitrary unitary circuit synthesis.
- Full quantum error correction.
- Mixed-state density-matrix simulation.
- Hardware noise channels.
- Quantum error mitigation.
- Real quantum processor connectivity constraints.
- Hardware-specific compilation.
- Distributed quantum simulation.
- Full quantum machine-learning model training.
- Hardware-based kernel estimation.

The IQP implementation is a simplified educational construction.

The exact simulator assumes ideal unitary operations and uses floating-point arithmetic.

The SQL implementation records experiment configurations and results rather than simulating quantum states.

These boundaries keep the implementations focused on the central problem: encoding classical data into quantum states and evaluating the resulting representations.

## 18. Cross-Language Implementation Mapping

| Technical concept | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Classical input | `FeatureVector` | `FeatureDataset` | `FeatureVector` | `FeatureVector` record | `dataset_samples` |
| Encoding configuration | `FeatureMapConfig` | `QuantumCircuit` options | `CircuitConfig` | `FeatureMapPolicy` | `feature_maps` |
| State representation | Complex list | Typed arrays | Complex vector | `ComplexValue[]` | Amplitude arrays |
| Rotation gates | Gate methods | Circuit methods | Static operations | Encoder methods | Stored results |
| ZZ interaction | `apply_zz` | `applyZZ` | `applyZZ` | `applyZZ` | Encoding metadata |
| Kernel evaluation | `QuantumKernel` | `QuantumKernelService` | `QuantumKernel` | `QuantumKernelService` | `kernel_evaluations` |
| Measurements | Weighted sampling | Seeded sampling | Discrete distribution | Random sampling | Experiment metadata |
| Validation | Exceptions | Exceptions | Exceptions | Domain exceptions | Constraints and triggers |
| Execution tracking | Experiment function | Event-driven runner | Experiment workflow | Experiment service | Experiment lifecycle |

## 19. Experimental Interpretation

The most important distinction in quantum feature mapping is between classical information and the quantum representation created from it.

The classical vector supplies parameters to a circuit. The circuit produces a state whose amplitudes and relative phases depend on those parameters.

Different encoding architectures create different representations of the same input.

Angle encoding provides a direct rotational representation. ZZ interactions introduce feature-dependent correlations through entangling operations. IQP-inspired constructions introduce structured diagonal interactions.

The resulting states can be compared through quantum fidelity kernels, providing a mathematical connection between quantum state preparation and classical kernel-based learning.

The quality of a feature map must be evaluated through measurable criteria such as kernel structure, classification performance, computational cost, circuit depth, and robustness to noise.
