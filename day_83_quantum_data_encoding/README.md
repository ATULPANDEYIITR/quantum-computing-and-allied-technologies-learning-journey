# Quantum Data Encoding: Basis, Angle and Amplitude Encoding

## 1. Introduction

Quantum data encoding is the process of representing classical information within the mathematical state space of a quantum system.

A quantum algorithm operates on qubits rather than directly processing conventional numerical arrays. Consequently, classical features must be transformed into quantum states before they can participate in quantum computation.

Three important encoding methods are implemented in this project:

1. Basis encoding
2. Angle encoding
3. Amplitude encoding

Each method has a different relationship between classical input dimensions, qubit requirements, state preparation, and information representation.

The implementations provide numerical simulations of quantum state preparation and measurement probabilities. They use mathematical state-vector representations rather than executing circuits on physical quantum processors.

## 2. Mathematical Foundations

### 2.1 Qubits

A classical bit takes one of two values:

- 0
- 1

A qubit is represented by a normalized complex-valued quantum state:

\[
|\psi\rangle = \alpha|0\rangle+\beta|1\rangle
\]

where:

\[
\alpha,\beta\in\mathbb{C}
\]

The normalization condition is:

\[
|\alpha|^2+|\beta|^2=1
\]

The computational basis states are:

\[
|0\rangle=
\begin{bmatrix}
1\\0
\end{bmatrix}
\]

\[
|1\rangle=
\begin{bmatrix}
0\\1
\end{bmatrix}
\]

A multi-qubit system is represented using tensor products.

For \(n\) qubits, the state vector contains:

\[
2^n
\]

complex amplitudes.

The general state is:

\[
|\psi\rangle=
\sum_{i=0}^{2^n-1}\alpha_i|i\rangle
\]

subject to:

\[
\sum_{i=0}^{2^n-1}|\alpha_i|^2=1
\]

This exponential state-space dimension is central to quantum data representation and classical simulation costs.

### 2.2 Measurement

Quantum measurement converts a quantum state into classical outcomes.

For computational basis state \(|i\rangle\), the probability of observing outcome \(i\) is:

\[
P(i)=|\alpha_i|^2
\]

Repeated measurements are called shots.

For example, a state with probabilities:

\[
P(0)=0.36
\]

\[
P(1)=0.64
\]

will produce approximately 360 observations of outcome 0 and 640 observations of outcome 1 over 1,000 independent shots.

The actual frequencies fluctuate because measurement outcomes are probabilistic.

Measurement does not reveal the complete quantum state from a single observation.

## 3. Basis Encoding

### 3.1 Definition

Basis encoding represents binary classical information using computational basis states.

A binary vector:

\[
x=[1,0,1,1]
\]

is represented by:

\[
|x\rangle=|1011\rangle
\]

The corresponding state vector contains sixteen amplitudes because four qubits provide:

\[
2^4=16
\]

computational basis states.

Only one amplitude is non-zero:

\[
|1011\rangle=
\begin{bmatrix}
0\\
0\\
\vdots\\
1\\
\vdots\\
0
\end{bmatrix}
\]

The non-zero amplitude is located at binary index 11.

### 3.2 Encoding mechanism

For a binary input:

\[
x=(x_0,x_1,\ldots,x_{n-1})
\]

the number of required qubits is:

\[
n_{\text{qubits}}=n
\]

The basis index is calculated as:

\[
I=\sum_{j=0}^{n-1}x_j2^{n-1-j}
\]

The resulting state satisfies:

\[
\alpha_I=1
\]

and:

\[
\alpha_k=0,\quad k\neq I
\]

### 3.3 Characteristics

| Property | Basis encoding |
|---|---|
| Input | Binary values |
| Qubit requirement | One qubit per bit |
| State dimension | \(2^n\) |
| Non-zero amplitudes | One |
| Normalization | Automatic |
| Classical information | Directly represented as a basis index |
| Main limitation | Binary input restriction |

Basis encoding is useful when the input naturally consists of binary states, categorical indicators, or discrete computational configurations.

It does not directly represent arbitrary continuous-valued features.

## 4. Angle Encoding

### 4.1 Definition

Angle encoding represents numerical features through parameterized quantum rotations.

A commonly used operation is the rotation around the Y-axis, represented by the RY gate.

Its matrix is:

\[
R_Y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}
\]

Applied to the initial state:

\[
|0\rangle=
\begin{bmatrix}
1\\0
\end{bmatrix}
\]

the resulting state is:

\[
R_Y(\theta)|0\rangle=
\cos(\theta/2)|0\rangle+
\sin(\theta/2)|1\rangle
\]

### 4.2 Numerical feature normalization

Suppose a feature belongs to:

\[
x\in[a,b]
\]

A linear transformation maps it into an angular parameter:

\[
\theta=
\pi\frac{x-a}{b-a}
\]

For normalized features between zero and one:

\[
\theta=\pi x
\]

The resulting representation is:

\[
|\psi(x)\rangle=
\cos(\pi x/2)|0\rangle+
\sin(\pi x/2)|1\rangle
\]

Three illustrative inputs produce:

| Input | Rotation angle | State |
|---|---:|---|
| 0.0 | 0 | \(|0\rangle\) |
| 0.5 | \(\pi/2\) | Equal amplitudes |
| 1.0 | \(\pi\) | \(|1\rangle\) |

### 4.3 Multiple features

For three features:

\[
x=(x_1,x_2,x_3)
\]

the corresponding state is:

\[
|\psi\rangle=
R_Y(\theta_1)|0\rangle
\otimes
R_Y(\theta_2)|0\rangle
\otimes
R_Y(\theta_3)|0\rangle
\]

The system requires three qubits.

The state vector contains:

\[
2^3=8
\]

amplitudes.

### 4.4 Characteristics

| Property | Angle encoding |
|---|---|
| Input | Real-valued features |
| Qubit requirement | One qubit per feature |
| Primary operation | RY rotation |
| State dimension | \(2^n\) |
| Normalization | Preserved by unitary rotations |
| Main advantage | Direct parameterized representation |
| Main limitation | Qubit count grows with feature count |

Angle encoding is particularly useful in parameterized quantum circuits and variational quantum algorithms.

Its performance depends on feature scaling, circuit architecture, rotation choices, and subsequent quantum operations.

## 5. Amplitude Encoding

### 5.1 Definition

Amplitude encoding represents a classical numerical vector through the amplitudes of a quantum state.

Given:

\[
x=(x_0,x_1,\ldots,x_{d-1})
\]

the normalized state is:

\[
|\psi\rangle=
\frac{1}{\|x\|}
\sum_{i=0}^{d-1}x_i|i\rangle
\]

where:

\[
\|x\|_2=
\sqrt{\sum_{i=0}^{d-1}|x_i|^2}
\]

For a real-valued vector:

\[
x=[3,4]
\]

the norm is:

\[
\|x\|_2=\sqrt{3^2+4^2}=5
\]

The encoded state is:

\[
|\psi\rangle=
0.6|0\rangle+0.8|1\rangle
\]

Its measurement probabilities are:

\[
P(0)=0.36
\]

\[
P(1)=0.64
\]

### 5.2 Qubit requirements

A quantum system with \(n\) qubits has \(2^n\) available computational basis states.

Therefore, representing \(d\) features requires:

\[
n=\lceil\log_2(d)\rceil
\]

For example:

| Classical features | Required qubits | State dimension |
|---:|---:|---:|
| 2 | 1 | 2 |
| 3 | 2 | 4 |
| 4 | 2 | 4 |
| 5 | 3 | 8 |
| 8 | 3 | 8 |
| 16 | 4 | 16 |
| 32 | 5 | 32 |
| 64 | 6 | 64 |

### 5.3 Zero-padding

When the input dimension is not a power of two, additional zero amplitudes are introduced.

For:

\[
x=[3,4,0]
\]

the normalized vector becomes:

\[
[0.6,0.8,0]
\]

The next valid state dimension is four:

\[
|\psi\rangle=
0.6|00\rangle+
0.8|01\rangle+
0|10\rangle+
0|11\rangle
\]

Zero-padding does not change the normalized values of the original features.

It increases the represented state dimension to the next power of two.

### 5.4 Characteristics

| Property | Amplitude encoding |
|---|---|
| Input | Real or complex numerical vectors |
| Qubit requirement | \(\lceil\log_2 d\rceil\) |
| State dimension | Next power of two |
| Representation | State amplitudes |
| Normalization | Required |
| Main advantage | Compact qubit representation |
| Main limitation | State preparation complexity |

Amplitude encoding can represent a high-dimensional vector with relatively few qubits.

This does not automatically make the complete computational workflow efficient.

Preparing an arbitrary amplitude-encoded state can require substantial gate operations. The cost depends on circuit structure, input assumptions, hardware connectivity, and available state-preparation techniques.

## 6. Comparison of the Three Methods

| Evaluation criterion | Basis | Angle | Amplitude |
|---|---|---|---|
| Classical input | Binary | Numerical | Numerical |
| Representation | Basis index | Rotation parameters | Amplitudes |
| Qubit scaling | Linear | Linear | Logarithmic |
| State dimension | Exponential in input bits | Exponential in features | Padded input dimension |
| Normalization | Automatic | Unitary-preserved | Explicit |
| Feature scaling | Not required | Usually required | Vector normalization |
| Zero-vector handling | Not applicable | Valid | Invalid |
| State preparation | Basis-state preparation | Parameterized rotations | Amplitude state preparation |
| Typical application | Binary configurations | Quantum machine learning | Vector and state representation |

The number of qubits alone is not a sufficient measure of encoding efficiency.

State-preparation complexity, circuit depth, gate count, connectivity, measurement cost, and data-loading requirements must also be considered.

## 7. Python Implementation

File: `quantum_data_encoding.py`

The Python implementation uses standard-library numerical and data-handling features.

### 7.1 QuantumState

The `QuantumState` dataclass stores:

- Encoding method
- Qubit count
- Complex amplitudes
- Encoding metadata

Its constructor validates the state-vector dimension and normalization condition.

The probability calculation follows:

\[
P(i)=|\alpha_i|^2
\]

The measurement function uses weighted random sampling to simulate repeated computational-basis measurements.

A fixed random seed supports reproducible demonstrations.

### 7.2 QuantumEncoder

The encoder provides three independent methods.

**basis_encode()**

- Validates binary values.
- Calculates the computational basis index.
- Constructs a one-hot state vector.
- Records the original bitstring.

**angle_encode()**

- Validates numerical features.
- Applies range normalization.
- Calculates RY rotation angles.
- Constructs the tensor-product state.

**amplitude_encode()**

- Validates the input vector.
- Calculates its Euclidean norm.
- Normalizes its amplitudes.
- Pads the vector to the next power of two.

### 7.3 Validation

The implementation rejects:

- Empty input.
- Invalid binary values.
- Out-of-range angle features.
- Non-finite numerical values.
- Zero amplitude vectors.
- Invalid measurement shot counts.

Assertions verify selected probability calculations and qubit requirements.

### 7.4 Complexity

For \(n\) angle-encoded features, the simulator constructs:

\[
2^n
\]

amplitudes.

Its time and memory requirements are therefore:

\[
O(2^n)
\]

For amplitude encoding of a vector of dimension \(d\), the state dimension is:

\[
2^{\lceil\log_2d\rceil}
\]

which is less than \(2d\) for positive \(d\).

The state-vector simulation still requires memory proportional to this dimension.

## 8. JavaScript Implementation

File: `quantum_data_encoding.js`

The JavaScript implementation focuses on asynchronous processing and event-driven execution.

### 8.1 QuantumState

The state class maintains:

- Encoding type
- Number of qubits
- Amplitude array
- Metadata

The amplitude collection and metadata are frozen to reduce accidental mutation.

Measurement uses a cumulative probability distribution and deterministic pseudo-random sampling.

### 8.2 EncodingPolicy

The policy object evaluates resource requirements before accepting a state.

Two constraints are enforced:

- Maximum qubit count.
- Maximum estimated state-vector memory.

For complex double-precision amplitudes, the memory estimate is:

\[
M=16\times2^n
\]

bytes.

The estimate excludes JavaScript object overhead and runtime-specific memory allocation.

### 8.3 EncodingService

The service extends Node.js `EventEmitter`.

It supports the following events:

| Event | Purpose |
|---|---|
| `job:started` | Encoding job submitted |
| `job:completed` | Encoding and policy validation completed |
| `job:failed` | Processing rejected or failed |

The service uses asynchronous execution to demonstrate concurrent job scheduling.

`Promise.allSettled()` ensures that the failure of one encoding request does not prevent the application from collecting the results of other requests.

The job registry maintains execution states independently of the encoded quantum states.

This is an application-level simulation, not a distributed quantum execution service.

## 9. C++17 Implementation

File: `quantum_data_encoding.cpp`

The C++ implementation focuses on explicit numerical representation and memory management.

### 9.1 Complex state representation

The program uses:

- `std::complex<double>`
- `std::vector`
- `std::map`
- `std::discrete_distribution`
- `std::mt19937`

The state vector stores real and imaginary components for every computational basis state.

### 9.2 Tensor-product construction

Angle encoding expands the state after each rotation.

For a previous amplitude \(\alpha\):

\[
\alpha\rightarrow
\begin{bmatrix}
\alpha\cos(\theta/2)\\
\alpha\sin(\theta/2)
\end{bmatrix}
\]

Each additional qubit doubles the vector dimension.

The implementation uses move semantics when replacing intermediate state vectors.

### 9.3 Resource management

`QuantumResourceManager` checks:

- Maximum permitted qubit count.
- Estimated memory allocation.

This separates numerical encoding from resource-governance decisions.

The state-vector representation uses:

\[
16\times2^n
\]

bytes when `std::complex<double>` occupies 16 bytes.

### 9.4 Measurement

The program uses a discrete probability distribution to sample basis-state outcomes.

It aggregates observations into a map of bitstrings and counts.

The fixed random seed makes the demonstration reproducible within the same implementation and runtime environment.

## 10. Java 17 Enterprise Implementation

File: `QuantumDataEncoding.java`

The Java implementation uses explicit domain types and application-service separation.

### 10.1 Domain model

The principal domain objects are:

| Type | Responsibility |
|---|---|
| `EncodingRequest` | Validated input request |
| `ResourcePolicy` | Resource allocation limits |
| `QuantumState` | Normalized encoded state |
| `JobResult` | Processing outcome |
| `EncodingType` | Encoding method |
| `JobStatus` | Job lifecycle state |

Java records provide compact immutable data structures for requests, policies, states, and job results.

### 10.2 Strategy registry

The `EncodingStrategy` interface defines a common encoding contract.

`EncodingStrategyRegistry` associates each encoding method with its implementation.

This design separates the selection of an encoding method from the application service that processes requests.

### 10.3 Resource governance

`ResourceGovernanceService` validates:

- Maximum qubit allocation.
- State-vector memory requirements.
- Method-specific organizational permissions.

A request can be mathematically valid but rejected by resource policy.

This distinction is important in enterprise execution systems.

### 10.4 Asynchronous processing

`EncodingApplicationService` uses:

- `ExecutorService`
- `CompletableFuture`
- `ConcurrentHashMap`

Independent requests can be submitted concurrently.

The audit service records both successful and failed execution results.

The implementation uses a fixed-size executor to limit concurrent application-level processing.

It does not implement durable job storage or distributed transaction coordination.

## 11. PostgreSQL Data Model

File: `quantum_data_encoding.sql`

The PostgreSQL implementation models an organizational quantum encoding workflow.

### 11.1 Relational architecture

The main relationship is:

Organization

→ Datasets

→ Dataset Features

→ Encoding Configurations

→ Encoding Jobs

→ Quantum States

→ State Amplitudes

→ Measurement Runs

→ Measurement Outcomes

Additional tables represent:

- Resource policies
- Resource evaluations
- Angle rotations
- Basis encodings

### 11.2 Dataset management

The `datasets` table stores the original feature collection metadata.

The `dataset_features` table stores individual numerical observations.

Feature positions identify the order of the input vector.

Constraints prevent invalid binary feature values and duplicate feature positions.

A trigger enforces the declared feature capacity.

### 11.3 Encoding configurations

`encoding_configurations` stores:

- Encoding method
- Numerical range
- Maximum qubits
- Maximum memory
- Zero-padding policy
- Configuration availability

Different encoding methods can therefore operate under separate configuration policies.

### 11.4 Job lifecycle

The `encoding_jobs` table stores processing information.

The lifecycle is:

`SUBMITTED → PROCESSING → COMPLETED`

An unsuccessful request can transition to:

`FAILED`

The database procedure `submit_encoding_job()` validates dataset completeness, input compatibility, and estimated resource requirements before creating a job.

`complete_encoding_job()` records state metadata and transitions an accepted job to completion.

The SQL workflow registers metadata rather than performing the underlying quantum circuit calculations.

### 11.5 State representation

The `quantum_states` table stores state-level metadata.

The `state_amplitudes` table stores individual complex amplitude components.

A complex amplitude is represented as:

\[
\alpha_i=a_i+ib_i
\]

Its probability is:

\[
P(i)=a_i^2+b_i^2
\]

The generated PostgreSQL column calculates this probability automatically.

A trigger validates basis-index boundaries.

The complete state must be validated at the application or transaction level because checking each individual amplitude cannot establish total normalization.

### 11.6 Angle rotations

The `angle_rotations` table records:

- Job identifier
- Qubit position
- Source feature
- Rotation gate
- Rotation angle

The implemented rotation gate is RY.

For a normalized input feature:

\[
\theta=\pi x
\]

The records provide traceability between the original numerical dataset and its rotation parameters.

### 11.7 Resource evaluation

`resource_policies` defines permitted execution limits.

`job_resource_evaluations` records the decision and its supporting metadata.

This separates mathematical input validation from resource authorization.

### 11.8 Reporting

The database includes:

- `encoding_job_report`
- `encoding_method_statistics`

These views support operational reporting and comparison across encoding methods.

The CTE-based queries evaluate feature statistics and identify input compatibility.

## 12. Encoding Selection and Practical Trade-offs

Encoding selection should consider the original dataset and the intended quantum operation.

| Scenario | Suitable starting point | Reason |
|---|---|---|
| Binary classification inputs | Basis encoding | Direct binary representation |
| Small continuous feature vectors | Angle encoding | Parameterized single-qubit rotations |
| High-dimensional normalized vectors | Amplitude encoding | Compact qubit representation |
| Variational quantum circuits | Angle encoding | Convenient parameterized gates |
| Discrete state identification | Basis encoding | Direct computational basis mapping |
| Quantum vector representation | Amplitude encoding | Features represented by amplitudes |

These are starting points rather than universal selection rules.

A method with fewer qubits may require more expensive state preparation.

An encoding method must be evaluated in the context of the entire quantum algorithm.

## 13. Computational Complexity

Let:

- \(d\) represent the number of classical features.
- \(n\) represent the number of qubits.
- \(D=2^n\) represent the quantum state dimension.

| Operation | Time complexity | Space complexity |
|---|---|---|
| Basis index calculation | \(O(d)\) | \(O(D)\) |
| Basis state construction | \(O(D)\) | \(O(D)\) |
| Angle state construction | \(O(2^d)\) | \(O(2^d)\) |
| Amplitude normalization | \(O(d)\) | \(O(D)\) |
| Amplitude padding | \(O(D)\) | \(O(D)\) |
| Probability calculation | \(O(D)\) | \(O(D)\) |
| Measurement sampling | \(O(S\log D)\) with binary search | \(O(D)\) |
| Measurement aggregation | \(O(S)\) expected map operations | \(O(K)\) |

Here:

- \(S\) is the number of measurement shots.
- \(K\) is the number of distinct observed outcomes.

The angle simulator explicitly constructs the full tensor-product state vector. A quantum circuit implementation does not necessarily need to materialize this vector.

## 14. Important Technical Limitations

### 14.1 State-vector simulation

All five source implementations use classical numerical representations of quantum states.

They do not demonstrate quantum computational speedup.

Classical state-vector simulation has exponential memory requirements with respect to qubit count.

### 14.2 State preparation

Constructing an amplitude vector mathematically is different from preparing that state using quantum gates.

Actual preparation may require substantial circuit depth and gate operations.

The preparation cost must be considered when evaluating the practical usefulness of amplitude encoding.

### 14.3 Measurement limitations

Measurement provides sampled outcomes rather than direct access to all amplitudes.

Recovering information about a quantum state generally requires repeated measurements and appropriate measurement strategies.

### 14.4 Feature scaling

Angle encoding depends on numerical scaling.

An unsuitable input range can distort feature relationships or produce invalid rotation parameters.

Amplitude encoding requires non-zero input vectors and normalization.

Normalization also removes the original vector's overall magnitude from the encoded state.

If vector magnitude carries meaningful information, it must be retained separately.

### 14.5 Correlation and entanglement

The implementations construct tensor products of individually encoded qubits.

These product states do not introduce entanglement during initial encoding.

Entanglement requires additional multi-qubit operations.

Encoding correlated classical features does not automatically produce an entangled quantum state.

### 14.6 Complex amplitudes

The mathematical framework permits complex-valued amplitudes.

The demonstrations primarily use real-valued inputs and real-valued initial state amplitudes.

A complete quantum simulation system must support complex-valued transformations, including phase-sensitive quantum gates.

## 15. Security and Production Considerations

Quantum data encoding systems can process sensitive classical datasets.

A production implementation should enforce:

- Authentication and authorization for dataset access.
- Encryption during data transfer and storage.
- Input validation before state preparation.
- Resource limits before exponential memory allocation.
- Job-level audit trails.
- Controlled access to encoded state data.
- Measurement provenance.
- Retention and deletion policies.
- Validation of externally supplied circuit configurations.

Amplitude encoding should not be treated as a data anonymization technique.

A normalized quantum state can still contain information derived from sensitive input features.

Resource policies must account for both the qubit count and the actual state-preparation workload.

## 16. Execution and Verification

The project contains five independent implementations.

| File | Runtime | Principal capability |
|---|---|---|
| `quantum_data_encoding.py` | Python 3 | Numerical state simulation and validation |
| `quantum_data_encoding.js` | Node.js | Event-driven encoding and resource policies |
| `quantum_data_encoding.cpp` | C++17 | Complex state-vector simulation |
| `QuantumDataEncoding.java` | Java 17 | Enterprise encoding workflow |
| `quantum_data_encoding.sql` | PostgreSQL 15+ | Relational workflow and reporting |

The Python implementation uses only the standard library.

The JavaScript implementation uses Node.js built-in modules.

The C++ implementation requires no third-party libraries.

The Java implementation requires Java 17.

The SQL script creates its own `quantum_encoding` schema and uses PostgreSQL's built-in UUID generation function.

### Verification cases

The implementations include representative tests for:

| Test case | Expected behavior |
|---|---|
| Binary vector `[1,0,1]` | Basis index 5 |
| Angle vector `[0,0.5,1]` | Three-qubit state |
| Amplitude vector `[3,4]` | Amplitudes 0.6 and 0.8 |
| Amplitude vector `[3,4,0]` | Two-qubit state with zero-padding |
| Zero amplitude vector | Rejected |
| Non-binary basis input | Rejected |
| Out-of-range angle input | Rejected |
| Non-finite numerical input | Rejected |
| Exceeded resource policy | Rejected |
| Valid normalized state | Accepted |

For the amplitude example:

\[
|\psi\rangle=0.6|0\rangle+0.8|1\rangle
\]

the verification conditions are:

\[
0.6^2+0.8^2=1
\]

\[
P(0)=0.36
\]

\[
P(1)=0.64
\]

These checks establish mathematical normalization and the expected computational-basis measurement probabilities.
