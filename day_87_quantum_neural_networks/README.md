# Quantum Neural Networks: Fundamentals

## 1. Introduction

A Quantum Neural Network (QNN) is a computational learning architecture that combines classical machine-learning techniques with parameterized quantum circuits.

A conventional neural network processes information using numerical operations on classical data. A QNN uses quantum states, quantum gates, measurements, and classical optimization to construct a trainable computational model.

The central architecture is a variational quantum circuit (VQC). Its parameters are adjusted by a classical optimizer to minimize a defined loss function.

A QNN is not automatically more efficient or more accurate than a classical neural network. Its practical value depends on the problem, circuit architecture, hardware capabilities, data encoding, noise characteristics, and optimization strategy.

The implementations in this repository demonstrate the mathematical and computational foundations of small variational quantum classifiers.

## 2. Mathematical foundations

### 2.1 Qubits

A classical bit takes one of two values:

- 0
- 1

A qubit is represented by a normalized complex-valued quantum state:

\[
|\psi\rangle = \alpha|0\rangle+\beta|1\rangle
\]

Where:

- \(\alpha\) is the complex amplitude associated with state 0.
- \(\beta\) is the complex amplitude associated with state 1.

The normalization condition is:

\[
|\alpha|^2+|\beta|^2=1
\]

The computational basis consists of:

\[
|0\rangle =
\begin{bmatrix}
1\\0
\end{bmatrix}
\]

\[
|1\rangle =
\begin{bmatrix}
0\\1
\end{bmatrix}
\]

A qubit can exist in a superposition of these basis states.

### 2.2 Superposition

Superposition describes a quantum state that is a linear combination of computational basis states.

An equal superposition is:

\[
|+\rangle =
\frac{|0\rangle+|1\rangle}{\sqrt{2}}
\]

The probability of observing an outcome is determined by the squared magnitude of its amplitude.

For the equal superposition:

\[
P(0)=P(1)=0.5
\]

The implementations construct superposition using the Pauli-Y rotation gate.

### 2.3 Multiple qubits

An \(n\)-qubit register has a state vector containing:

\[
2^n
\]

complex amplitudes.

For two qubits:

\[
|\psi\rangle =
\alpha_{00}|00\rangle+
\alpha_{01}|01\rangle+
\alpha_{10}|10\rangle+
\alpha_{11}|11\rangle
\]

The state must satisfy:

\[
\sum_i|\alpha_i|^2=1
\]

This exponential growth in state-vector dimension is important when evaluating the computational cost of classical quantum simulation.

### 2.4 Entanglement

Entanglement describes quantum correlations that cannot be represented as a product of independent single-qubit states.

A Bell state is:

\[
|\Phi^+\rangle =
\frac{|00\rangle+|11\rangle}{\sqrt{2}}
\]

It can be constructed using:

1. Initialization in \(|00\rangle\).
2. A Hadamard gate on the first qubit.
3. A CNOT gate using the first qubit as control.

The implementations use an equivalent rotation-based construction:

\[
RY(\pi/2)\rightarrow CNOT
\]

Entanglement enables quantum circuits to represent correlations between qubits.

It is an important component of many variational quantum architectures.

## 3. Quantum gates

Quantum gates transform quantum states through unitary operations.

A unitary operator \(U\) satisfies:

\[
U^\dagger U=I
\]

This property preserves the normalization of an ideal quantum state.

### 3.1 Pauli-X

\[
X =
\begin{bmatrix}
0&1\\
1&0
\end{bmatrix}
\]

The X gate exchanges the computational basis states.

\[
X|0\rangle=|1\rangle
\]

### 3.2 Pauli-Y

\[
Y =
\begin{bmatrix}
0&-i\\
i&0
\end{bmatrix}
\]

The Y gate performs a rotation-related transformation involving complex amplitudes.

### 3.3 Pauli-Z

\[
Z =
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
\]

The Z gate changes the phase of the \(|1\rangle\) component.

It is also used as an observable for extracting model outputs.

### 3.4 Rotation gates

The implementations support the following rotation operations.

**RX rotation**

\[
R_X(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-i\sin(\theta/2)\\
-i\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

**RY rotation**

\[
R_Y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

**RZ rotation**

\[
R_Z(\theta)=
\begin{bmatrix}
e^{-i\theta/2}&0\\
0&e^{i\theta/2}
\end{bmatrix}
\]

Rotation angles are measured in radians.

The rotation parameters can be optimized during QNN training.

### 3.5 Controlled-NOT

The CNOT gate applies an X transformation to the target qubit when the control qubit is in state 1.

Its computational basis behavior is:

| Input | Output |
|---|---|
| 00 | 00 |
| 01 | 01 |
| 10 | 11 |
| 11 | 10 |

The gate introduces entanglement when applied to an appropriate superposition state.

## 4. Quantum Neural Network architecture

The implemented QNN follows a variational architecture.

Its processing sequence is:

Classical input features

↓

Feature preprocessing

↓

Quantum feature encoding

↓

Parameterized quantum circuit

↓

Entangling operations

↓

Measurement

↓

Expectation-value calculation

↓

Classical loss calculation

↓

Classical parameter optimization

↓

Updated quantum circuit

The process repeats until the training limit or convergence condition is reached.

### 4.1 Classical feature encoding

Classical datasets contain numerical feature vectors.

A quantum circuit cannot directly operate on an ordinary classical feature vector. The information must first be encoded into a quantum state.

The implementations use angle encoding.

For two features:

\[
x=[x_0,x_1]
\]

The feature map applies:

\[
|\psi(x)\rangle =
RY_0(x_0)RY_1(x_1)|00\rangle
\]

Where the subscripts identify the affected qubits.

Angle encoding is relatively straightforward and allows direct use of rotation gates.

Its limitations include feature scaling, periodicity, and the relationship between feature count and qubit requirements.

Features should be preprocessed according to the chosen encoding scheme.

### 4.2 Parameterized quantum circuit

A parameterized quantum circuit contains trainable gate parameters.

The implemented architecture is:

| Sequence | Operation | Purpose |
|---|---|---|
| 1 | RY(x0) | Encode first feature |
| 2 | RY(x1) | Encode second feature |
| 3 | RY(theta0) | Trainable transformation |
| 4 | RY(theta1) | Trainable transformation |
| 5 | CNOT(0,1) | Entanglement |
| 6 | RY(theta2) | Trainable transformation |
| 7 | RY(theta3) | Trainable transformation |
| 8 | CNOT(1,0) | Additional entanglement |

The four trainable parameters are:

\[
\theta =
[\theta_0,\theta_1,\theta_2,\theta_3]
\]

The circuit output depends on both the input features and these parameters.

### 4.3 Measurement

Quantum measurement converts quantum information into classical outcomes.

The implementations use the Pauli-Z observable:

\[
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
\]

The expectation value is:

\[
\langle Z\rangle =
\langle\psi|Z|\psi\rangle
\]

For the first qubit:

\[
\langle Z_0\rangle =
P(0)-P(1)
\]

The result lies within:

\[
-1\leq\langle Z_0\rangle\leq1
\]

This value acts as a continuous model output.

The classifier applies a decision threshold:

\[
\hat{y} =
\begin{cases}
+1 & \text{if }\langle Z_0\rangle\geq0\\
-1 & \text{otherwise}
\end{cases}
\]

### 4.4 Shot-based measurement

A physical quantum computer generally produces measurement samples rather than an exact probability distribution.

A shot is one execution and measurement of a quantum circuit.

For \(N\) measurement shots:

\[
\widehat{\langle Z\rangle}=
\frac{N_0-N_1}{N}
\]

Where:

- \(N_0\) is the number of observations of 0.
- \(N_1\) is the number of observations of 1.
- \(N=N_0+N_1\).

Increasing the number of shots generally reduces sampling uncertainty.

For independent measurements, the standard error of a bounded Pauli-Z expectation estimate is:

\[
SE=
\sqrt{\frac{1-\langle Z\rangle^2}{N}}
\]

This creates a practical trade-off between measurement precision and execution cost.

## 5. Variational quantum learning

### 5.1 Classical optimization

A variational quantum model has two computational components:

- A quantum circuit that evaluates the model.
- A classical optimizer that updates the circuit parameters.

The training objective is to minimize a loss function.

The implementations use mean squared error:

\[
L(\theta)=
\frac{1}{M}
\sum_{i=1}^{M}
(f_\theta(x_i)-y_i)^2
\]

Where:

- \(M\) is the number of training examples.
- \(x_i\) is an input feature vector.
- \(y_i\) is its target.
- \(f_\theta\) is the quantum circuit output.

### 5.2 Parameter-shift rule

The parameter-shift rule estimates derivatives of quantum expectation values.

For a parameter appearing in a standard rotation gate:

\[
\frac{\partial f}{\partial\theta}
=
\frac{
f(\theta+\pi/2)-f(\theta-\pi/2)
}{2}
\]

For a loss function, the shift must be applied to the complete loss evaluation, as implemented in the JavaScript and Java training engines.

The rule is particularly useful because it estimates gradients using quantum circuit evaluations.

Its direct form requires appropriate gate generators and parameter usage. More complex parameterized gates or parameters reused across multiple gates may require generalized shift rules.

The Python implementation also includes central finite-difference estimation:

\[
\frac{\partial L}{\partial\theta}
\approx
\frac{L(\theta+\epsilon)-L(\theta-\epsilon)}
{2\epsilon}
\]

Finite differences are useful for small classical simulations but introduce numerical approximation error.

### 5.3 Gradient descent

The parameter update is:

\[
\theta_{t+1}
=
\theta_t-\eta\nabla L(\theta_t)
\]

Where:

- \(\eta\) represents the learning rate.
- \(\nabla L\) represents the loss gradient.
- \(t\) represents the training iteration.

An excessively high learning rate can cause unstable optimization.

A very low learning rate can result in slow convergence.

### 5.4 Training workflow

The implemented classifier follows this process:

1. Initialize trainable parameters.
2. Encode a training example.
3. Execute the variational circuit.
4. Calculate its expectation value.
5. Calculate the prediction error.
6. Estimate parameter gradients.
7. Update the trainable parameters.
8. Evaluate training loss and accuracy.
9. Repeat until the configured epoch limit or convergence condition is reached.

The implementations use small synthetic datasets to demonstrate the mechanics. Their results are educational rather than evidence of generalization to real-world datasets.

## 6. Implementation architecture

### 6.1 Python

The Python implementation provides a self-contained state-vector simulator and training workflow.

| Component | Responsibility |
|---|---|
| `QuantumState` | Stores complex amplitudes and applies gates |
| `QuantumFeatureMap` | Encodes classical input features |
| `VariationalCircuit` | Defines the trainable circuit |
| `QuantumNeuralNetwork` | Performs training and classification |
| `TrainingMetrics` | Stores epoch-level results |
| `TrainingResult` | Stores final model parameters and history |

Important implementation decisions:

- Complex amplitudes are represented using Python's built-in complex type.
- Computational basis states are represented by integer indices.
- Single-qubit gate operations update pairs of amplitudes.
- CNOT uses bit masks to identify computational basis states.
- State normalization is checked after circuit execution.
- Central finite differences provide a numerical gradient.
- Measurement sampling uses probability-weighted random selection.
- Experiment metadata is exported as JSON.

The state-vector representation requires exponential memory as the number of qubits increases.

The implementation therefore limits the register to 20 qubits as a defensive configuration limit, not a claim that every machine can efficiently simulate that many qubits.

### 6.2 JavaScript

The JavaScript implementation emphasizes asynchronous execution and event-driven experiment management.

| Component | Responsibility |
|---|---|
| `Complex` | Complex-number arithmetic |
| `QuantumRegister` | Quantum state and gate operations |
| `ParameterizedQuantumCircuit` | Variational circuit execution |
| `QuantumDataset` | Validated immutable training examples |
| `VariationalOptimizer` | Loss and parameter-shift gradients |
| `QuantumExperiment` | Experiment lifecycle and event reporting |

The experiment service exposes events:

| Event | Meaning |
|---|---|
| `started` | Training has started |
| `epoch` | An epoch has completed |
| `completed` | Training has finished |
| `failed` | Training encountered an error |

The asynchronous training method periodically yields to the Node.js event loop.

This allows monitoring code to process events during execution.

The JavaScript implementation uses the parameter-shift rule instead of the Python implementation's finite-difference approximation.

Its dataset objects use immutable feature arrays to reduce accidental changes during training.

### 6.3 C++17

The C++ implementation emphasizes efficient state manipulation and explicit domain modeling.

| Component | Responsibility |
|---|---|
| `QuantumRegister` | Stores and transforms quantum states |
| `QuantumCircuit` | Stores ordered quantum gate operations |
| `Gate` | Represents a gate instruction |
| `Example` | Represents a labeled training example |
| `VariationalQuantumClassifier` | Executes and trains the classifier |
| `Metrics` | Stores training results |

The implementation uses:

- `std::complex<double>` for amplitudes.
- `std::vector` for state storage.
- `std::array` for fixed-size feature vectors and parameters.
- Bitwise masks for efficient gate application.
- STL algorithms for aggregation.
- Exceptions for invalid circuit configurations.

The gate representation also supports circuit construction independently of the quantum register.

The program uses parameter-shift optimization and validates the state normalization after circuit execution.

### 6.4 Java 17

The Java implementation provides an enterprise-oriented experiment model.

Its architecture separates the quantum execution mechanism from experiment configuration and training management.

| Component | Responsibility |
|---|---|
| `FeatureVector` | Validated input representation |
| `TrainingExample` | Input and target relationship |
| `TrainingPolicy` | Training limits and configuration |
| `QuantumRegister` | Quantum state operations |
| `FeatureEncoder` | Classical-to-quantum encoding |
| `QuantumModel` | Model execution interface |
| `VariationalQuantumClassifier` | QNN architecture |
| `Dataset` | Immutable training dataset |
| `QuantumTrainingService` | Optimization and evaluation |
| `ExperimentService` | Experiment execution boundary |

Java records provide compact immutable representations for data objects.

The training policy validates:

- Epoch limits.
- Learning-rate boundaries.
- Convergence thresholds.
- Maximum dataset size.

The training service separates model evaluation, gradient estimation, and optimization.

This structure supports clearer testing and configuration management in larger research systems.

## 7. PostgreSQL experiment management

The SQL implementation provides relational storage for quantum neural network experiments.

It manages experiment configuration, circuit architecture, datasets, training executions, and evaluation results.

The database does not execute quantum gates or replace a quantum simulator.

### 7.1 Relational model

The principal relationships are:

Projects

→ Experiments

→ Quantum Circuits

→ Circuit Gates

→ Circuit Parameters

Experiments

→ Training Datasets

→ Optimizer Configurations

Quantum Circuits

→ Observables

Training Runs

→ Quantum Measurements

→ Training Metrics

→ Evaluation Results

### 7.2 Main database entities

| Entity | Purpose |
|---|---|
| `projects` | Research project organization |
| `experiments` | QNN experiment definitions |
| `quantum_circuits` | Circuit architecture and configuration |
| `circuit_gates` | Ordered quantum gate instructions |
| `circuit_parameters` | Trainable parameter values |
| `training_datasets` | Dataset versions and splits |
| `optimizer_configs` | Optimization configuration |
| `observables` | Measurement definitions |
| `training_runs` | Individual training executions |
| `quantum_measurements` | Shot counts and expectation values |
| `training_metrics` | Epoch-level training performance |
| `evaluation_results` | Held-out evaluation metrics |

### 7.3 Integrity enforcement

The database implements:

- Primary and foreign keys.
- Unique constraints.
- Check constraints.
- Gate-to-qubit validation triggers.
- Observable validation.
- Experiment lifecycle enforcement.
- Training-run lifecycle enforcement.

These controls prevent several invalid configurations, including:

- Negative qubit indices.
- CNOT gates with identical control and target qubits.
- Parameter values outside configured bounds.
- Invalid measurement counts.
- Incorrect observable definitions.
- Completed experiments transitioning back into active states.

### 7.4 Readiness determination

The `check_experiment_readiness` function checks whether an experiment contains:

1. A validated circuit.
2. A training dataset.
3. An optimizer configuration.

This separates experiment configuration from actual execution.

A configured experiment is not automatically a successfully trained model.

### 7.5 Performance reporting

The `v_training_performance` view combines circuit, optimizer, dataset, and training-metric information.

The reporting queries calculate:

- Minimum training loss.
- Average training accuracy.
- Maximum training accuracy.
- Completed epochs.
- Aggregate execution time.
- Measurement statistics.

Indexes support common retrieval patterns involving experiment status, circuit identity, training runs, and epoch-level metrics.

### 7.6 Transaction handling

The SQL script demonstrates transactional workflow processing and exception handling.

The rollback demonstration uses a nested PL/pgSQL exception block, which establishes a subtransaction.

An intentional exception rolls back changes made within that block while preserving the surrounding transaction.

This illustrates how database integrity can be maintained when an experiment operation fails.

## 8. Important distinctions in QNN research

### 8.1 Quantum neural networks versus classical neural networks

| Dimension | Classical neural network | Quantum neural network |
|---|---|---|
| Information unit | Classical bit | Qubit |
| State representation | Numerical tensors | Complex quantum amplitudes |
| Core operations | Matrix multiplication and nonlinear functions | Quantum gates and measurements |
| Model parameters | Weights and biases | Parameterized gate angles |
| Training | Classical optimization | Classical optimization with quantum evaluations |
| Output | Numerical prediction | Measurement-derived expectation values |

Hybrid QNN architectures retain classical preprocessing and optimization components.

### 8.2 Variational circuits versus quantum kernels

These are different quantum machine-learning approaches.

**Variational quantum circuits**

Use trainable quantum circuit parameters to optimize a prediction function.

**Quantum kernel methods**

Estimate similarities between encoded quantum states.

A quantum kernel can be defined as:

\[
K(x_i,x_j)=
|\langle\phi(x_i)|\phi(x_j)\rangle|^2
\]

The kernel values are then used by a classical kernel-learning algorithm.

The implementations in this repository focus on variational quantum circuits rather than quantum kernel classifiers.

### 8.3 Exact simulation versus physical quantum execution

The source files use ideal state-vector simulations.

An exact simulator calculates amplitudes and expectation values directly.

A physical quantum device introduces practical constraints:

- Gate errors.
- Measurement errors.
- Decoherence.
- Limited connectivity.
- Circuit execution time.
- Finite measurement shots.
- Hardware-dependent noise.

A model that performs well in an ideal simulator may perform differently on physical hardware.

### 8.4 State vectors versus density matrices

State-vector simulation represents a pure quantum state:

\[
|\psi\rangle
\]

A density matrix represents quantum states more generally:

\[
\rho =
|\psi\rangle\langle\psi|
\]

Density matrices can represent mixed states and support the mathematical modeling of noise and partial measurements.

They require approximately \(O(4^n)\) complex storage rather than \(O(2^n)\) for a state vector.

The current implementations use pure-state simulation.

## 9. Practical limitations and research considerations

### 9.1 Exponential simulation complexity

An \(n\)-qubit state-vector simulator stores \(2^n\) complex amplitudes.

Each additional qubit doubles the state-vector dimension.

This limits the scale of direct classical simulation.

### 9.2 Barren plateaus

A barren plateau is a region of a variational circuit's parameter space where gradients become extremely small.

This can make optimization difficult.

Potential contributing factors include:

- Circuit architecture.
- Entanglement structure.
- Number of qubits.
- Initialization strategy.
- Observable selection.
- Cost-function design.

The small circuit in this repository does not establish whether a barren plateau exists.

### 9.3 Noise and measurement uncertainty

Real quantum measurements are stochastic.

Finite shots introduce statistical uncertainty into expectation values.

Hardware noise can further distort the measurement distribution.

Research-grade evaluations should distinguish simulator results from hardware results.

### 9.4 Data encoding limitations

Encoding classical information into quantum states is not free.

The number of qubits, circuit depth, gate count, and preprocessing requirements affect execution cost.

Angle encoding is straightforward but may introduce periodic representations of the original numerical features.

Feature normalization and appropriate encoding choices are therefore important.

### 9.5 Optimization limitations

A variational circuit is generally non-convex with respect to its trainable parameters.

Different initializations may produce different optimization outcomes.

Gradient estimates can become expensive when measurements are performed on physical hardware.

The parameter-shift method is analytically motivated, but the number of required circuit evaluations can still become substantial.

### 9.6 Security and data governance

Quantum computation does not automatically provide data confidentiality.

A production QNN workflow should consider:

- Dataset access controls.
- Sensitive-feature minimization.
- Secure experiment metadata.
- Authentication for execution services.
- Integrity of circuit configurations.
- Controlled access to measurement results.
- Reproducible experiment records.
- Protection of exported model parameters.

The PostgreSQL schema includes a sensitive-data indicator for dataset governance, but it does not implement encryption, access-control policies, or comprehensive audit logging.

## 10. Running the implementations

### Python

Requirements:

- Python 3.10 or newer.
- Standard library only.

Execute the Python file using:

`python qnn_fundamentals.py`

The program runs correctness tests, demonstrates quantum superposition and entanglement, trains a variational classifier, and exports `qnn_experiment.json`.

### JavaScript

Requirements:

- Node.js 18 or newer.
- Standard library only.

Execute:

`node qnn_fundamentals.js`

The program executes quantum-state validation, runs asynchronous training, emits experiment events, and exports `qnn_experiment_js.json`.

### C++17

Requirements:

- C++17-compatible compiler.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic qnn_fundamentals.cpp -o qnn_fundamentals`

Execute:

`./qnn_fundamentals`

On Windows:

`qnn_fundamentals.exe`

### Java 17

Requirements:

- JDK 17.

Compile:

`javac QuantumNeuralNetwork.java`

Execute:

`java QuantumNeuralNetwork`

### PostgreSQL

Requirements:

- PostgreSQL 15 or newer.
- Permission to create schemas, tables, functions, and triggers.

Execute the SQL file using:

`psql -U postgres -d your_database -f qnn_fundamentals.sql`

The SQL script creates the `qnn` schema, its relational structures, demonstration records, workflow transitions, validation functions, and reporting queries.

Run the SQL script against a dedicated learning database because it creates database objects and demonstration records.

## 11. Technical reference

| Concept | Mathematical or computational representation |
|---|---|
| Qubit | Complex two-dimensional state |
| Superposition | Linear combination of basis states |
| Entanglement | Non-separable multi-qubit state |
| Quantum gate | Unitary transformation |
| Feature encoding | Classical values mapped to quantum operations |
| Ansatz | Parameterized quantum circuit architecture |
| Variational parameter | Trainable quantum gate parameter |
| Measurement | Conversion of quantum state information into classical outcomes |
| Observable | Operator associated with a measurable quantity |
| Expectation value | Probability-weighted measurement result |
| Loss function | Numerical measure of prediction error |
| Parameter-shift rule | Gradient estimation using shifted circuit evaluations |
| Optimizer | Classical procedure for updating circuit parameters |
| Shot | One circuit execution and measurement |
| State-vector simulator | Classical representation of a pure quantum state |
| Hybrid QNN | Quantum circuit combined with classical processing and optimization |

The five implementations establish a common computational model while emphasizing different engineering concerns: Python numerical experimentation, JavaScript asynchronous execution, C++ state manipulation, Java enterprise-oriented domain modeling, and PostgreSQL experiment governance.
