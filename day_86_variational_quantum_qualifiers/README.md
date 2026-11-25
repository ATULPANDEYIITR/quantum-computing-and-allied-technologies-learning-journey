# Variational Quantum Classifiers

## 1. Introduction

A Variational Quantum Classifier (VQC) is a hybrid quantum-classical machine learning model that uses a parameterized quantum circuit to classify classical input data.

A VQC combines three computational components:

1. Classical preprocessing converts input observations into numerical feature vectors.
2. A quantum circuit encodes those features, applies parameterized quantum operations, and produces measurement outcomes.
3. A classical optimizer updates the circuit parameters to minimize a classification loss function.

The model is trained iteratively. Quantum circuit evaluations provide information about the current model, while classical optimization determines how its parameters should change.

The implementations in this repository demonstrate binary classification using a two-qubit state-vector simulator.

## 2. Mathematical Foundations

### 2.1 Quantum states

A quantum state is represented by a normalized state vector:

\[
|\psi\rangle =
\sum_{i=0}^{2^n-1}\alpha_i|i\rangle
\]

where:

- \(n\) is the number of qubits.
- \(|i\rangle\) represents a computational basis state.
- \(\alpha_i\) is a complex probability amplitude.

The amplitudes satisfy:

\[
\sum_i |\alpha_i|^2=1
\]

For two qubits, the state vector contains four amplitudes:

\[
|\psi\rangle =
\alpha_{00}|00\rangle+
\alpha_{01}|01\rangle+
\alpha_{10}|10\rangle+
\alpha_{11}|11\rangle
\]

The probability of observing a particular computational basis state is the squared magnitude of its amplitude.

\[
P(i)=|\alpha_i|^2
\]

The implementations use real-valued amplitudes because the selected circuit contains only real-valued RY rotations and CNOT gates. This is sufficient for the demonstrated circuit but does not represent every possible quantum circuit.

### 2.2 Qubit rotations

The RY gate rotates a qubit around the Y axis of the Bloch sphere.

\[
R_Y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

Its angle determines the resulting quantum state.

The rotation angle can encode a classical feature or represent a trainable model parameter.

### 2.3 Entanglement

A CNOT gate performs a controlled bit flip.

Its target qubit changes when the control qubit is in state one.

For the selected two-qubit circuit:

\[
CNOT(0,1)
\]

qubit zero controls qubit one.

Entanglement allows the circuit to represent correlations between qubits that cannot be described by independent single-qubit states.

The presence of an entangling gate does not automatically guarantee useful entanglement for every input and parameter configuration.

### 2.4 Measurement

The implementations measure the Pauli-Z observable on the first qubit.

\[
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
\]

Its expectation value is:

\[
\langle Z_0\rangle =
\langle\psi|Z_0|\psi\rangle
\]

For the two-qubit state:

\[
\langle Z_0\rangle =
|\alpha_{00}|^2+
|\alpha_{10}|^2-
|\alpha_{01}|^2-
|\alpha_{11}|^2
\]

The expectation value lies within:

\[
-1\leq\langle Z_0\rangle\leq1
\]

It is converted into a binary classification probability:

\[
P(y=1)=\frac{1-\langle Z_0\rangle}{2}
\]

The corresponding negative-class probability is:

\[
P(y=0)=\frac{1+\langle Z_0\rangle}{2}
\]

The prediction threshold is 0.5.

## 3. Variational Circuit Architecture

The implemented circuit has the following structure:

| Stage | Operation | Purpose |
|---|---|---|
| Initialization | \(|00\rangle\) | Prepare the initial state |
| Feature map | RY rotations | Encode two classical features |
| Entanglement | CNOT | Introduce inter-qubit interactions |
| Ansatz layer 1 | RY rotations | Apply trainable transformations |
| Entanglement | CNOT | Couple the qubits |
| Ansatz layer 2 | RY rotations | Refine the quantum representation |
| Measurement | Pauli-Z on qubit 0 | Produce the classification score |

The circuit can be represented as:

\[
|\psi(x,\theta)\rangle =
U_{\text{ansatz}}(\theta)
U_{\text{entangle}}
U_{\text{feature}}(x)|00\rangle
\]

where:

- \(x\) represents the input feature vector.
- \(\theta\) represents the trainable parameters.
- \(U_{\text{feature}}\) is the feature-encoding circuit.
- \(U_{\text{entangle}}\) introduces controlled interactions.
- \(U_{\text{ansatz}}\) represents the parameterized circuit.

The four trainable parameters are:

\[
\theta=(\theta_0,\theta_1,\theta_2,\theta_3)
\]

Feature-map angles and variational parameters have different roles. Feature angles depend on the observation, while variational parameters are updated during training.

## 4. Hybrid Quantum-Classical Optimization

### 4.1 Binary cross-entropy

The classifier uses binary cross-entropy:

\[
L(y,p)=-
[y\log(p)+(1-y)\log(1-p)]
\]

where:

- \(y\) is the actual binary label.
- \(p\) is the predicted positive-class probability.

The objective is to minimize the average loss across the training dataset:

\[
J(\theta)=
\frac{1}{N}
\sum_{i=1}^{N}
L(y_i,p_\theta(x_i))
\]

Numerical clipping prevents logarithms of zero and unstable divisions.

### 4.2 Parameter-shift rule

The gradient of a suitable parameterized quantum expectation value can be calculated using the parameter-shift rule.

For the single-frequency rotation gates used in this implementation:

\[
\frac{\partial f}{\partial\theta_j}
=
\frac{
f(\theta_j+\pi/2)-
f(\theta_j-\pi/2)
}{2}
\]

This rule evaluates the circuit twice for each differentiated parameter.

For four parameters, a gradient calculation requires eight shifted circuit evaluations per observation, excluding the ordinary forward evaluation.

The gradient of the classification loss also requires the chain rule:

\[
\frac{\partial L}{\partial\theta_j}
=
\frac{\partial L}{\partial p}
\frac{\partial p}{\partial\langle Z\rangle}
\frac{\partial\langle Z\rangle}{\partial\theta_j}
\]

The classical optimizer then updates the parameters:

\[
\theta_j^{(t+1)}
=
\theta_j^{(t)}
-
\eta
\frac{\partial J}{\partial\theta_j}
\]

where \(\eta\) is the learning rate.

The implementations use full-batch gradient descent.

### 4.3 Training workflow

The implemented training process is:

1. Validate the dataset and confirm that both classes are present.
2. Initialize the variational parameters.
3. Encode every training observation.
4. Execute the parameterized quantum circuit.
5. Calculate measurement expectation values.
6. Convert measurement results into classification probabilities.
7. Calculate binary cross-entropy.
8. Estimate gradients using parameter-shift evaluations.
9. Aggregate the gradients across the training dataset.
10. Update the variational parameters.
11. Record the training loss.
12. Repeat until the configured epoch limit is reached.

The training and testing datasets are kept separate to demonstrate evaluation on observations not used for optimization.

## 5. Python Implementation

The Python implementation provides a mathematical simulation of a two-qubit variational classifier using only standard-library functionality.

### 5.1 Domain structures

`Sample` is an immutable dataclass containing:

- Two numerical features.
- A binary classification label.

`TrainingConfig` stores the optimization configuration, including the epoch count, learning rate, and random seed.

Custom exceptions distinguish invalid input from general quantum simulation failures.

### 5.2 Quantum state simulation

`QuantumCircuit` maintains the four quantum amplitudes.

Its methods implement:

- State initialization.
- RY rotation.
- CNOT transformation.
- Basis-state probability.
- Pauli-Z expectation measurement.
- State normalization verification.

The implementation uses state-vector indexing and bit masks to identify the amplitudes affected by individual gates.

### 5.3 Classifier and optimizer

`VariationalQuantumClassifier` contains the feature map, ansatz, measurement logic, probability conversion, gradient calculation, and prediction methods.

The parameter-shift implementation calculates the derivative of the quantum expectation and propagates it through the classification probability and loss.

The optimizer applies full-batch gradient descent with bounded parameter values.

### 5.4 Persistence

The model can be saved as JSON.

The stored information includes:

- Format version.
- Qubit count.
- Trainable parameters.
- Training history.

The loader validates the model structure and numerical parameters before restoring the model.

Model files should be treated as untrusted input in production environments. File permissions, ownership, schema validation, and integrity checks should be enforced when models are shared between services.

## 6. JavaScript Implementation

The JavaScript implementation emphasizes event-driven training and asynchronous execution.

### 6.1 Event-driven architecture

`VQCTrainer` extends Node.js `EventEmitter`.

It publishes three important events:

| Event | Purpose |
|---|---|
| `epoch` | Reports training progress and loss |
| `training-complete` | Reports successful completion |
| `training-error` | Reports an optimization failure |

This design separates the training engine from monitoring and reporting components.

A monitoring service can subscribe to training events without modifying the circuit implementation.

### 6.2 Asynchronous execution

The training method is asynchronous and periodically yields control to the Node.js event loop.

This prevents a long-running simulation from monopolizing the event loop during the demonstration.

The training-state flag prevents simultaneous optimization operations on the same model.

### 6.3 Data validation

`Dataset` validates the sample structure, feature count, finite numerical values, and binary labels.

The constructor creates immutable copies of the observations to reduce accidental modification during training.

### 6.4 Engineering distinction

JavaScript provides an event-oriented perspective rather than merely reproducing the Python class structure.

The event system is particularly useful when integrating quantum experiments into:

- Web applications.
- Experiment dashboards.
- Asynchronous processing services.
- Training-monitoring systems.
- Model lifecycle workflows.

The implementation is a simulation. Its asynchronous execution does not make the underlying quantum circuit execute on actual quantum hardware.

## 7. C++17 Implementation

The C++ implementation focuses on computational efficiency, explicit state management, and domain-oriented circuit execution.

### 7.1 Quantum state representation

The `QuantumState` class maintains a fixed-size array of four amplitudes.

For a two-qubit system, this avoids dynamic state-vector allocation during individual gate operations.

The implementation uses:

- `std::array` for fixed-dimensional quantum states.
- `std::vector` for datasets and training history.
- `std::mt19937` for reproducible initialization.
- `std::clamp` for parameter and probability boundaries.
- Exceptions for invalid operations and numerical failures.

### 7.2 Separation of responsibilities

The principal components are:

| Component | Responsibility |
|---|---|
| `Sample` | Represents an observation and its label |
| `Dataset` | Validates classification data |
| `QuantumState` | Maintains and transforms amplitudes |
| `VariationalCircuit` | Executes the quantum gate sequence |
| `VQCClassifier` | Handles training, prediction, and evaluation |
| `Metrics` | Stores classification performance |

This separation makes the circuit reusable independently of the optimization and reporting logic.

### 7.3 Complexity

For an \(n\)-qubit state-vector simulator, the state contains:

\[
2^n
\]

amplitudes.

A single-qubit gate generally requires:

\[
O(2^n)
\]

state updates.

For \(P\) trainable parameters and \(N\) training observations, parameter-shift full-batch optimization has approximate simulation complexity:

\[
O(E \cdot N \cdot P \cdot 2^n)
\]

where \(E\) is the number of training epochs.

The implementation uses a fixed two-qubit system, so its state-vector memory consumption remains constant.

The exponential state-vector growth becomes a major limitation as the number of simulated qubits increases.

## 8. Java 17 Implementation

The Java implementation models the classifier as a structured service with explicit domain types and lifecycle states.

### 8.1 Domain model

The implementation uses Java records for immutable data structures:

- `Sample`
- `TrainingPolicy`
- `Metrics`
- `TrainingEvent`

The `Classification` enum prevents arbitrary integer labels from entering the classification domain.

The `ModelStatus` enum defines the model lifecycle:

\[
INITIALIZED
\rightarrow TRAINING
\rightarrow TRAINED
\]

A failed optimization transitions the model into `FAILED`.

### 8.2 Service separation

The main enterprise-oriented components are:

- `QuantumState`: state-vector operations.
- `QuantumCircuit`: gate execution.
- `Dataset`: data validation.
- `VQCModel`: model parameters and optimization.
- `EvaluationService`: classification reporting.
- `TrainingListener`: training event notification.

The evaluation service accepts only a trained model. This prevents evaluation from being presented as a completed model-validation operation when training has not finished.

### 8.3 Immutable structures

Records and immutable dataset collections help maintain predictable input state.

The parameter accessor returns a defensive copy rather than exposing the internal parameter array.

This reduces the possibility of accidental external modification of the trained model.

### 8.4 Enterprise implications

A production implementation would typically separate:

- Experiment configuration.
- Training execution.
- Quantum hardware access.
- Model registration.
- Model versioning.
- Evaluation approval.
- Deployment authorization.

The current implementation demonstrates the computational and lifecycle boundaries without introducing unnecessary infrastructure dependencies.

## 9. PostgreSQL Implementation

The PostgreSQL implementation provides relational storage and experiment management for variational quantum classification.

The schema is organized around experiments rather than storing the entire workflow in a single table.

### 9.1 Relational architecture

The principal relationships are:

| Entity | Responsibility |
|---|---|
| `experiments` | Experiment configuration and lifecycle |
| `circuit_layers` | Quantum gate and circuit-layer configuration |
| `datasets` | Dataset metadata |
| `classification_samples` | Feature vectors, labels, and data splits |
| `experiment_datasets` | Experiment-to-dataset association |
| `variational_parameters` | Trainable quantum parameters |
| `optimization_runs` | Individual training executions |
| `training_epochs` | Optimization history |
| `predictions` | Classification results |
| `evaluation_metrics` | Performance measurements |

The logical relationship is:

\[
Experiment
\rightarrow Dataset
\rightarrow Samples
\]

and:

\[
Experiment
\rightarrow Parameters
\rightarrow OptimizationRun
\rightarrow Epochs
\]

Evaluation records are associated with completed optimization runs.

### 9.2 Referential integrity

Primary keys uniquely identify records.

Foreign keys prevent orphaned records and maintain relationships between experiments, datasets, parameters, runs, predictions, and evaluation metrics.

Unique constraints prevent duplicate experiment names, duplicate sample references within a dataset, duplicate parameter indexes, and duplicate epoch numbers within a run.

Check constraints enforce numerical ranges and valid configuration values.

### 9.3 JSONB feature vectors

The classification samples store feature vectors using PostgreSQL `JSONB`.

For example, a two-feature observation is represented by a JSON array containing two numeric values.

The validation trigger checks:

- JSON array structure.
- Expected feature count.
- Numeric feature values.
- Dataset existence.

For high-volume production workloads, a normalized feature table, typed array, or specialized analytical storage may be more appropriate than JSONB.

### 9.4 Parameter management

The `variational_parameters` table stores individual trainable parameters.

Each parameter belongs to an experiment and has a unique parameter index.

The parameter validation function confirms that:

- The expected number of parameters exists.
- Parameter indexes start at zero.
- No parameter index is missing.

The timestamp trigger updates parameter modification times.

### 9.5 Training history

An optimization run represents an individual training execution.

The `training_epochs` table records:

- Epoch number.
- Training loss.
- Gradient norm.
- Learning rate.
- Recording timestamp.

The `record_training_epoch` procedure locks the associated run before inserting an epoch record.

This prevents concurrent workers from independently modifying the same run's state without coordination.

### 9.6 Evaluation and reporting

The evaluation metrics table records:

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Cross-entropy loss.
- Confusion matrix counts.

The reporting views combine experiment configuration, optimization results, evaluation records, and individual prediction outcomes.

The SQL script also includes queries for dataset validation, parameter validation, training aggregation, model status, and query-plan inspection.

### 9.7 Transaction management

The script uses a transaction to keep the schema and demonstration records consistent.

If a database operation fails before commit, the transaction can be rolled back.

In production, experiment creation, training execution, and evaluation should normally have separate transaction boundaries. Long-running quantum jobs should not hold database transactions open while circuit execution takes place.

## 10. Classification Metrics

The implementations report four primary classification metrics.

### 10.1 Accuracy

Accuracy measures the proportion of correct predictions:

\[
Accuracy=\frac{TP+TN}{TP+TN+FP+FN}
\]

### 10.2 Precision

Precision measures the proportion of positive predictions that are correct:

\[
Precision=\frac{TP}{TP+FP}
\]

### 10.3 Recall

Recall measures the proportion of actual positive observations correctly identified:

\[
Recall=\frac{TP}{TP+FN}
\]

### 10.4 F1-score

F1-score is the harmonic mean of precision and recall:

\[
F1=
2\cdot
\frac{Precision\cdot Recall}
{Precision+Recall}
\]

When the denominator of precision or recall is zero, the implementations return zero rather than performing an invalid division.

For imbalanced classification datasets, accuracy alone can be misleading. Precision, recall, F1-score, class-specific error rates, and probability calibration should be examined together.

## 11. Distinctions Between Quantum Classification Approaches

Variational quantum classifiers are related to several other quantum machine learning methods, but their computational mechanisms differ.

| Approach | Main mechanism |
|---|---|
| Variational Quantum Classifier | Trainable quantum circuit with measurement-based predictions |
| Quantum Kernel Classifier | Quantum feature map used to calculate kernel similarities |
| Quantum Neural Network | Broader family of trainable parameterized quantum models |
| Quantum Support Vector Machine | Classification using quantum-related feature representations or kernel estimation |
| Classical Neural Network | Classical numerical operations and trainable parameters |

A VQC directly optimizes parameters of a parameterized quantum circuit.

A quantum kernel classifier instead estimates similarities between encoded observations and typically passes the resulting kernel information to a classical learning algorithm.

These approaches should not be treated as interchangeable.

## 12. Important Practical Limitations

### 12.1 State-vector simulation

The implementations simulate quantum gates on classical computers.

They do not execute physical quantum operations.

The memory requirements grow exponentially with the number of qubits.

### 12.2 Measurement sampling

The simulator calculates exact expectation values from probability amplitudes.

Real quantum devices generally estimate expectation values from repeated measurements, known as shots.

Shot-based measurements introduce statistical uncertainty.

For an observable with outcomes in the interval \([-1,1]\), the estimation error decreases approximately with the inverse square root of the number of shots.

### 12.3 Hardware noise

Physical quantum processors introduce errors through:

- Gate imperfections.
- Decoherence.
- Readout errors.
- Connectivity limitations.
- Crosstalk.
- Calibration drift.

The implementations do not simulate these hardware effects.

### 12.4 Optimization difficulties

Variational circuits can experience:

- Vanishing gradients.
- Poor parameter initialization.
- Local optimization difficulties.
- Sensitivity to feature scaling.
- Overfitting.
- Unstable training.

A deeper circuit does not necessarily provide better classification performance.

### 12.5 Data encoding

The feature map determines how classical information enters the quantum circuit.

Poor feature scaling can produce unhelpful rotation angles or reduce the ability of the circuit to distinguish observations.

The demonstration uses two directly encoded features. Real datasets require a carefully designed preprocessing and feature-selection strategy.

## 13. Security and Reproducibility

Quantum classification experiments should maintain reproducibility and controlled data access.

Important considerations include:

- Validate input dimensions and numerical values.
- Avoid accepting arbitrary model parameters without validation.
- Protect persisted model files.
- Record random seeds and training configurations.
- Separate training, validation, and test datasets.
- Preserve experiment and model versions.
- Record optimization failures.
- Restrict access to sensitive training observations.
- Avoid logging personally identifiable feature data unnecessarily.
- Verify the integrity of externally supplied model artifacts.

A quantum circuit does not automatically provide data confidentiality, privacy protection, or secure computation.

## 14. Testing and Execution

The five source files implement the same general binary classification problem using different engineering perspectives.

| File | Runtime | Main execution |
|---|---|---|
| Python | Python 3.10+ | `python vqc.py` |
| JavaScript | Node.js 18+ | `node vqc.js` |
| C++17 | C++17 compiler | Compile and execute the program |
| Java | Java 17 | `javac VariationalQuantumClassifier.java` followed by execution |
| PostgreSQL | PostgreSQL 15+ | Execute the SQL script in a transaction-capable client |

No third-party dependencies are required for the four programming-language implementations.

The PostgreSQL script creates its own schema, tables, constraints, functions, procedures, triggers, views, and demonstration records.

The implementations use deterministic initialization to support repeatable demonstrations.

The Python, JavaScript, C++, and Java implementations independently simulate the same circuit architecture. Their floating-point outputs can differ slightly because of numerical representation and execution details.

The PostgreSQL implementation stores experiment metadata and representative training records. Its sample optimization history is illustrative database data, not a record of the exact optimization output produced by executing one of the four programs.

## 15. Engineering Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Main focus | Mathematical simulation | Event-driven training | Computational state management | Enterprise domain model | Experiment persistence |
| Quantum state | Dynamic list | Numeric array | Fixed array | Numeric array | Not simulated |
| Optimization | Full-batch descent | Asynchronous full-batch descent | Full-batch descent | Policy-driven descent | Run and epoch records |
| Validation | Exceptions and dataclasses | Dataset validation | Explicit domain validation | Records and lifecycle validation | Constraints and triggers |
| Reporting | Classification metrics | Event and metric reporting | Structured metric reporting | Evaluation service | SQL views and aggregations |
| Persistence | JSON | JSON | Runtime output | Runtime model state | Relational database |

The implementations demonstrate the same core variational classification mechanism while emphasizing different aspects of software engineering, numerical simulation, optimization, lifecycle management, and experiment governance.
