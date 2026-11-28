# Hybrid Quantum-Classical Machine Learning

## 1. Introduction

Hybrid Quantum-Classical Machine Learning combines quantum computation with classical machine-learning algorithms within a single computational workflow.

The quantum component performs selected operations such as quantum feature encoding, parameterized circuit execution, entanglement, quantum kernel evaluation, and measurement.

The classical component manages data preparation, parameter optimization, statistical learning, loss evaluation, model validation, and experiment management.

The objective is to investigate whether quantum computational representations can improve particular learning tasks while retaining the flexibility and established optimization capabilities of classical computing.

A hybrid architecture does not imply that every operation is quantum. Most practical implementations distribute computation between classical processors and quantum processing units.

## 2. Fundamental Architecture

A typical hybrid learning workflow follows this structure:

Classical Dataset
    |
    v
Data Validation and Preprocessing
    |
    v
Feature Encoding
    |
    v
Parameterized Quantum Circuit
    |
    v
Quantum Measurement
    |
    v
Classical Feature Representation
    |
    v
Classical Prediction or Loss Function
    |
    v
Classical Optimizer
    |
    v
Updated Quantum Parameters
    |
    +-----------> Repeat Training
    |
    v
Model Evaluation

The quantum circuit produces measurement information. A classical optimizer uses the resulting objective value or gradient information to update model parameters.

This iterative process forms the basis of variational hybrid learning.

## 3. Classical and Quantum Computing Responsibilities

| Operation | Classical component | Quantum component |
|---|---|---|
| Data storage | Primary responsibility | Not normally used |
| Data cleaning | Primary responsibility | Not normally used |
| Feature normalization | Primary responsibility | Not normally used |
| Feature encoding | Calculates encoding parameters | Maps data into quantum states |
| Circuit execution | Submits and manages jobs | Executes quantum gates |
| Measurement | Processes measurement results | Produces quantum outcomes |
| Loss calculation | Primary responsibility | Supplies measurement-derived values |
| Optimization | Updates parameters | Executes updated circuits |
| Evaluation | Calculates model metrics | May generate additional measurements |

A hybrid system therefore requires coordination between two computational environments.

Classical computation generally handles the larger portion of the workflow, while quantum computation is assigned selected operations.

## 4. Quantum Computing Fundamentals

### 4.1 Qubits

A classical bit has two possible states: zero and one.

A qubit is represented by a normalized quantum state:

\[
|\psi\rangle = \alpha|0\rangle+\beta|1\rangle
\]

where:

\[
|\alpha|^2+|\beta|^2=1
\]

The coefficients are complex amplitudes.

Measurement produces a classical outcome. The probability of observing zero is:

\[
P(0)=|\alpha|^2
\]

The probability of observing one is:

\[
P(1)=|\beta|^2
\]

A qubit is not simply a classical bit storing both values simultaneously. Its amplitudes describe a quantum state whose measurement outcomes follow probability distributions.

### 4.2 Multiple Qubits

An n-qubit register has a state-vector dimension of:

\[
2^n
\]

For two qubits:

\[
|\psi\rangle =
\alpha_{00}|00\rangle+
\alpha_{01}|01\rangle+
\alpha_{10}|10\rangle+
\alpha_{11}|11\rangle
\]

The state-vector representation grows exponentially with qubit count.

This creates an important limitation for classical quantum simulation.

### 4.3 Quantum Gates

Quantum gates transform quantum states through unitary operations.

The implementations include three fundamental operations.

**Hadamard gate**

The Hadamard gate creates an equal-amplitude superposition from a computational basis state.

\[
H=\frac{1}{\sqrt{2}}
\begin{bmatrix}
1&1\\
1&-1
\end{bmatrix}
\]

**Rotation around the Y-axis**

\[
R_y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

This gate introduces trainable rotation parameters.

**Controlled-NOT gate**

CNOT applies a bit flip to the target qubit when the control qubit is one.

It is an entangling operation when applied to an appropriate superposition.

### 4.4 Quantum Measurement

Measurement converts quantum information into classical outcomes.

For a Pauli-Z observable, the expectation value is:

\[
\langle Z\rangle=P(0)-P(1)
\]

The result lies between -1 and 1.

Repeated measurements estimate expectation values statistically.

The number of measurement repetitions is called the shot count.

A higher shot count generally improves statistical precision but increases execution cost and latency.

## 5. Quantum Feature Maps

A feature map converts classical input data into quantum states.

Mathematically:

\[
x\longrightarrow |\phi(x)\rangle
\]

A quantum feature map may use rotation gates, entangling gates, or more complex parameterized transformations.

The Python, JavaScript, C++, and Java implementations use a two-qubit encoding circuit.

The encoding applies:

1. Hadamard operations.
2. Feature-dependent Y-axis rotations.
3. Feature-dependent Z-axis rotations in the feature-map implementations.
4. Controlled-NOT operations between neighboring qubits.

The resulting state contains a representation of the original classical features.

The purpose is to explore representations that may capture relationships differently from conventional feature transformations.

Feature-map quality depends on the encoding circuit, data distribution, number of qubits, and computational constraints.

A more complicated circuit does not automatically provide better predictive performance.

## 6. Variational Quantum Circuits

A variational quantum circuit is a parameterized quantum circuit.

Its general representation is:

\[
|\psi(x,\theta)\rangle =
U(x,\theta)|0\rangle^{\otimes n}
\]

where:

- \(x\) represents input features.
- \(\theta\) represents trainable circuit parameters.
- \(U\) represents the sequence of quantum operations.

The circuit first encodes input features and then applies trainable rotations and entangling gates.

The measurement layer converts the resulting quantum state into classical numerical features.

The Python, JavaScript, and Java implementations use this architecture.

### Parameterized circuit workflow

1. Initialize circuit parameters.
2. Encode input features.
3. Apply parameterized rotation gates.
4. Apply entangling operations.
5. Measure selected observables.
6. Pass measurements to a classical prediction model.
7. Calculate the training loss.
8. Estimate gradients.
9. Update parameters.
10. Repeat until the training limit is reached.

The circuit is evaluated repeatedly during training.

This creates an important engineering concern: quantum circuit execution can dominate training time, especially when hardware access involves remote job submission.

## 7. Classical Optimization

Classical optimization updates model parameters based on the calculated objective function.

The binary classification implementations use logistic regression.

The prediction probability is:

\[
p(y=1|z)=\sigma(w^Tz+b)
\]

where:

- \(z\) represents quantum measurement features.
- \(w\) represents classical weights.
- \(b\) represents the bias.
- \(\sigma\) represents the sigmoid function.

The binary cross-entropy loss is:

\[
L=-\frac{1}{N}\sum_{i=1}^{N}
\left[
y_i\log(p_i)+(1-y_i)\log(1-p_i)
\right]
\]

The classical prediction head and the quantum circuit parameters are updated through separate mechanisms.

This distinction is important because the classical weights and quantum gate parameters belong to different parts of the computational model.

### Parameter-shift rule

For a suitable parameterized Pauli rotation gate, a derivative can be estimated using:

\[
\frac{\partial f}{\partial\theta}
=
\frac{
f(\theta+\pi/2)-f(\theta-\pi/2)
}{2}
\]

The Python, JavaScript, and Java examples demonstrate this parameter-shift calculation.

It is a quantum-circuit gradient technique, not a universal finite-difference approximation for arbitrary parameters.

The implementations hold the classical prediction head fixed while calculating these quantum parameter gradients.

A complete gradient treatment for a larger hybrid model must account for the dependencies between all trainable components.

## 8. Quantum Kernel Methods

Quantum kernel learning provides an alternative hybrid architecture.

Instead of training a variational circuit through an iterative optimizer, a quantum feature map transforms input data into quantum states.

The kernel function is:

\[
K(x,y)=
|\langle\phi(x)|\phi(y)\rangle|^2
\]

This is the fidelity between two encoded pure quantum states.

A kernel matrix is constructed using:

\[
K_{ij}=K(x_i,x_j)
\]

The resulting Gram matrix is supplied to a classical kernel-learning algorithm.

### C++ implementation

The C++ program implements:

- Quantum state encoding.
- State-vector overlap calculations.
- Fidelity-based quantum kernels.
- Gram matrix construction.
- Kernel ridge classification.
- Gaussian elimination with partial pivoting.
- Classification evaluation.

The classifier solves:

\[
(K+\lambda I)\alpha=y
\]

where:

- \(K\) is the training Gram matrix.
- \(\lambda\) is the regularization parameter.
- \(I\) is the identity matrix.
- \(y\) contains binary targets encoded as -1 and +1.
- \(\alpha\) contains the fitted coefficients.

The prediction function is:

\[
f(x)=\sum_{i=1}^{N}\alpha_iK(x_i,x)
\]

The sign of the resulting decision value determines the predicted class.

Kernel methods and variational classifiers are distinct approaches to hybrid quantum-classical learning.

A kernel model learns through a classical solver operating on quantum-derived similarities. A variational model learns through repeated parameterized circuit execution.

## 9. Implementation Architecture

### 9.1 Python

The Python implementation provides an end-to-end hybrid learning experiment.

| Component | Responsibility |
|---|---|
| QuantumRegister | Quantum state representation |
| QuantumFeatureMap | Classical-to-quantum feature encoding |
| VariationalQuantumCircuit | Parameterized circuit execution |
| ClassicalHead | Logistic regression |
| HybridClassifier | Training and prediction orchestration |
| parameter_shift_gradient | Quantum gradient estimation |
| Evaluation | Classification metrics |
| ExperimentReport | Experiment reporting |

Python uses standard-library features for numerical operations, data classes, exceptions, file handling, and testing.

The simulator is deliberately limited to twelve qubits to prevent uncontrolled memory consumption.

The generated JSON report contains experiment configuration, execution time, training loss, and evaluation metrics.

### 9.2 JavaScript

The JavaScript implementation uses an event-driven experiment architecture.

Its main components are:

- `Complex`: complex-number arithmetic.
- `QuantumRegister`: state-vector simulation.
- `QuantumFeatureExtractor`: quantum feature transformation.
- `VariationalCircuit`: parameterized circuit.
- `ClassicalOptimizer`: classical logistic optimization.
- `EventBus`: experiment lifecycle notifications.
- `HybridExperiment`: complete experiment execution.

The `EventBus` separates experiment processing from monitoring.

The asynchronous training method yields to the Node.js event loop between epochs.

The model emits training-started, epoch-completed, training-completed, and training-failed events.

The experiment report uses a unique identifier and is written to a JSON file.

### 9.3 C++17

The C++ implementation focuses on computational efficiency and quantum kernel learning.

Its main classes are:

- `QuantumRegister`
- `QuantumFeatureMap`
- `QuantumKernel`
- `QuantumKernelClassifier`

The implementation uses:

- `std::complex` for complex amplitudes.
- `std::vector` for state storage.
- STL algorithms for dataset processing.
- Partial pivoting for linear-system solving.
- Exceptions for invalid quantum operations.

The C++ model demonstrates a quantum kernel rather than mechanically reproducing the variational classifier.

This provides a distinct perspective on hybrid architecture.

### 9.4 Java 17

The Java implementation uses an enterprise-oriented architecture.

Its components include:

- `Dataset`
- `Sample`
- `BackendConfiguration`
- `TrainingPolicy`
- `QuantumBackend`
- `StateVectorBackend`
- `LogisticHead`
- `HybridModelService`
- `ExperimentService`

Java records provide immutable experiment configuration and result objects.

The `QuantumBackend` interface separates the execution contract from the simulator implementation.

The experiment service manages asynchronous execution using `ExecutorService` and `Future`.

The model service controls training states and prevents prediction before training completion.

The implementation also demonstrates timeout handling and lifecycle validation.

## 10. PostgreSQL Experiment Management

The PostgreSQL implementation provides persistent management of hybrid quantum-classical experiments.

The database is responsible for storing metadata and execution records rather than performing quantum gate operations.

### Relational model

The primary relationships are:

Organizations
    |
    +--> Research Users
    |
    +--> Datasets
    |
    +--> Models
    |
    +--> Execution Policies
             |
             v
        Experiments
             |
             +--> Experiment Reviews
             |
             +--> Training Runs
                      |
                      +--> Quantum Circuit Runs
                      |
                      +--> Optimization Steps
                      |
                      +--> Evaluation Metrics

### Database entities

| Table | Purpose |
|---|---|
| organizations | Research organization boundaries |
| research_users | Researchers, operators, reviewers, and administrators |
| datasets | Dataset versions and research approval |
| quantum_backends | Simulator and hardware configurations |
| models | Hybrid and quantum model definitions |
| execution_policies | Execution restrictions |
| experiments | Experiment configuration and lifecycle |
| experiment_reviews | Research approval decisions |
| training_runs | Individual training executions |
| quantum_circuit_runs | Circuit execution metadata |
| optimization_steps | Classical optimization history |
| evaluation_metrics | Model performance |
| model_approvals | Model approval records |
| experiment_audit | Experiment status changes |

### Execution eligibility

The `check_experiment_eligibility` function evaluates:

- Dataset research approval.
- Organization ownership.
- User authorization and active status.
- Backend availability.
- Maximum qubit capacity.
- Execution mode restrictions.
- Shot limits.
- Epoch limits.
- Model and dataset dimensions.
- Review requirements.

The function returns an eligibility decision and an explanation.

The `queue_experiment` procedure locks the experiment record before changing its state.

This prevents concurrent requests from independently transitioning the same experiment from the created state.

### Audit logging

The `record_experiment_status` trigger records experiment status transitions.

Audit records include:

- Experiment identifier.
- Acting user.
- Previous state.
- New state.
- Timestamp.
- Additional structured information.

The audit table provides a history of lifecycle changes.

### Performance-oriented database design

Indexes support:

- Experiment status filtering.
- Researcher-specific experiment retrieval.
- Training run retrieval.
- Circuit execution monitoring.
- Optimization history.
- Evaluation reporting.
- Audit history.

JSONB stores measurement counts, expectation values, and parameter vectors.

Relational columns remain responsible for important constraints and frequently queried attributes.

## 11. Hybrid Learning Workflows

### Workflow A: Variational quantum classifier

The Python, JavaScript, and Java implementations follow this workflow.

1. Generate or load classical training data.
2. Validate feature dimensions.
3. Initialize a parameterized quantum circuit.
4. Initialize the classical logistic regression head.
5. Encode each training sample.
6. Execute the quantum circuit.
7. Calculate measurement-derived features.
8. Calculate binary cross-entropy loss.
9. Estimate quantum parameter gradients.
10. Update quantum parameters.
11. Update classical prediction weights.
12. Repeat for the specified number of epochs.
13. Evaluate the trained model on testing data.

### Workflow B: Quantum kernel classifier

The C++ implementation follows a different workflow.

1. Load the training dataset.
2. Construct a quantum feature map.
3. Encode each training sample.
4. Calculate pairwise quantum state fidelities.
5. Construct a symmetric Gram matrix.
6. Add regularization to the diagonal.
7. Solve the kernel ridge regression system.
8. Calculate kernel similarities for testing samples.
9. Produce decision scores.
10. Calculate classification metrics.

### Workflow C: Managed research experiment

The PostgreSQL implementation represents an enterprise research workflow.

1. Register an organization.
2. Register authorized users.
3. Register a dataset and its checksum.
4. Register a model.
5. Configure a quantum backend.
6. Define execution policies.
7. Submit an experiment.
8. Obtain the required review.
9. Evaluate execution eligibility.
10. Queue the experiment.
11. Record training runs.
12. Record quantum circuit executions.
13. Record classical optimization steps.
14. Store evaluation metrics.
15. Complete the experiment.
16. Inspect reports and audit records.

## 12. Important Technical Distinctions

### Quantum simulation versus quantum hardware

A state-vector simulator executes mathematical representations of quantum states on classical hardware.

A quantum processing unit physically executes quantum operations.

The implementations in Python, JavaScript, C++, and Java use classical state-vector simulation.

They do not communicate with actual quantum hardware.

A hardware deployment requires a backend adapter, provider authentication, circuit transpilation, job submission, measurement retrieval, and hardware-specific error handling.

### Exact simulation versus shot-based measurement

The state-vector simulators calculate expectation values directly from state amplitudes.

This is an exact mathematical expectation for the simulated state, subject to floating-point precision.

Actual quantum hardware produces finite measurement samples.

For a finite number of shots, expectation estimates contain statistical uncertainty.

The Python, JavaScript, C++, and Java implementations therefore demonstrate idealized quantum execution rather than a complete noisy hardware experiment.

### Quantum advantage versus hybrid experimentation

A successful hybrid experiment does not establish quantum advantage.

Quantum advantage requires evidence that a quantum approach offers a meaningful benefit over appropriate classical alternatives.

Evaluation should consider:

- Predictive performance.
- Runtime.
- Memory consumption.
- Circuit execution cost.
- Measurement overhead.
- Hardware noise.
- Data encoding cost.
- Classical preprocessing.
- Classical baseline quality.

The computational overhead of quantum simulation must not be interpreted as quantum hardware performance.

## 13. Performance and Complexity

For a state-vector simulator with \(n\) qubits:

\[
D=2^n
\]

where \(D\) is the number of amplitudes.

| Operation | Approximate complexity |
|---|---|
| State initialization | \(O(2^n)\) |
| Single-qubit gate | \(O(2^n)\) |
| CNOT gate | \(O(2^n)\) |
| State-vector storage | \(O(2^n)\) |
| Expectation calculation | \(O(2^n)\) |
| Full quantum kernel matrix | \(O(N^2 2^n)\) |
| Kernel ridge solver | \(O(N^3)\) |

Here, \(N\) represents the number of training samples.

Quantum kernel learning can become expensive because each pair of training samples requires a kernel evaluation.

The Gram matrix requires quadratic storage:

\[
O(N^2)
\]

The classical dense linear solver has cubic computational complexity.

Larger datasets therefore require strategies such as:

- Kernel approximation.
- Reduced training sets.
- Batching.
- Parallel circuit execution.
- Sparse representations where applicable.
- Iterative linear solvers.

Increasing qubit count in a classical state-vector simulator is particularly expensive because its memory requirement doubles with every additional qubit.

## 14. Validation and Failure Handling

The five implementations contain different validation mechanisms.

| Failure condition | Handling mechanism |
|---|---|
| Invalid qubit count | Configuration validation |
| Incorrect feature dimension | Input validation |
| Non-finite numerical values | Numerical validation |
| Invalid rotation parameters | Gate validation |
| Invalid CNOT operands | Circuit exception |
| Zero or negative shots | Measurement validation |
| Invalid classification labels | Dataset validation |
| Empty training dataset | Training rejection |
| Empty evaluation dataset | Evaluation rejection |
| Singular kernel matrix | Linear solver exception |
| Invalid experiment transition | Lifecycle validation |
| Training divergence | Experiment failure |
| Backend execution failure | Backend exception |
| Asynchronous timeout | Future cancellation |
| Invalid experiment policy | Database eligibility rejection |

These controls are important because quantum-classical workflows involve multiple computational stages.

A failure in circuit execution, parameter optimization, or dataset validation should not silently produce a valid-looking experiment result.

## 15. Security and Research Governance

Production hybrid-learning environments should enforce security at multiple layers.

### Dataset security

- Verify dataset checksums.
- Restrict access by organization.
- Record dataset versions.
- Enforce research approval.
- Apply privacy and data-retention controls.
- Separate training and testing partitions.

### Quantum backend security

- Store provider credentials outside source files.
- Use authenticated backend connections.
- Restrict hardware access.
- Apply shot and execution quotas.
- Record circuit execution identifiers.
- Monitor provider failures and execution costs.

### Model security

- Validate model parameters.
- Record model versions.
- Protect serialized model artifacts.
- Track experiment configuration.
- Maintain reproducibility records.
- Restrict model deployment approvals.

### Database security

- Use separate database roles.
- Apply least-privilege permissions.
- Restrict cross-organization access.
- Protect sensitive records.
- Audit administrative changes.
- Use row-level security where required.

The supplied SQL demonstrates organization ownership checks and research approval rules. A production system should supplement these checks with database grants, row-level security, controlled service accounts, and external identity management.

## 16. Limitations of the Implementations

| Implementation | Main limitation |
|---|---|
| Python | Small state-vector simulation; synthetic dataset |
| JavaScript | In-memory experiment execution; no physical backend |
| C++17 | Dense kernel matrix and Gaussian elimination |
| Java 17 | Simulator-specific backend adapter; bounded execution |
| PostgreSQL | Stores execution metadata rather than executing circuits |

The Python, JavaScript, and Java implementations use idealized state-vector measurements.

Their parameter-shift demonstrations also hold the classical prediction head fixed during quantum gradient estimation.

The C++ kernel implementation uses exact simulated state fidelities and does not model finite-shot uncertainty or hardware noise.

The PostgreSQL script manages experiment lifecycle and governance, but it is not a quantum execution engine.

The sample classification dataset is synthetic. Its performance should not be interpreted as evidence of performance on real scientific, financial, medical, or industrial datasets.

## 17. Execution Requirements

| File | Runtime | External dependencies |
|---|---|---|
| Python | Python 3.10+ | None |
| JavaScript | Node.js 18+ | None |
| C++17 | C++17 compiler | None |
| Java | Java 17 | None |
| PostgreSQL | PostgreSQL 15+ | None |

### Python

Save the Python source as `hybrid_quantum_ml.py`.

Execute it using Python 3.

The experiment generates `hybrid_quantum_experiment.json` in the current working directory.

### JavaScript

Save the JavaScript source as `hybrid_quantum_ml.js`.

Execute it using Node.js.

The experiment generates `hybrid_quantum_report.json`.

### C++17

Save the C++ source as `hybrid_quantum_ml.cpp`.

Compile with a C++17-compatible compiler.

The implementation does not require external libraries.

### Java 17

Save the Java source as `HybridQuantumML.java`.

Compile and execute using Java 17.

The public class name and source filename must match.

### PostgreSQL

Execute the SQL script using a PostgreSQL 15 or newer database.

The script creates the `hybrid_ml` schema and its experiment-management objects.

The script uses a transaction so that schema creation, sample data, and demonstration operations can be committed together.

## 18. Experimental Interpretation

The implementations demonstrate three different hybrid learning perspectives.

| Perspective | Quantum contribution | Classical contribution |
|---|---|---|
| Variational classifier | Parameterized quantum feature processing | Logistic prediction and optimization |
| Quantum kernel learning | Quantum state fidelity | Kernel ridge regression |
| Enterprise experiment management | Circuit execution records and backend configuration | Experiment governance, optimization records, and reporting |

The central architectural principle is the separation of quantum computation from classical orchestration.

Quantum circuits generate representations or measurements. Classical algorithms interpret those outputs, optimize model parameters, evaluate predictions, and manage the overall experiment.

This separation makes hybrid quantum-classical machine learning suitable for modular research systems in which quantum simulators, quantum hardware providers, and classical machine-learning services can be integrated through well-defined interfaces.
