# Quantum Approximate Optimization Algorithm (QAOA)

## 1. Technical Scope

This project implements the Quantum Approximate Optimization Algorithm (QAOA) through five complementary engineering perspectives:

| Implementation | Primary responsibility |
|---|---|
| Python | Statevector simulation, graph optimization and measurement |
| JavaScript | Event-driven experiment execution and asynchronous lifecycle management |
| C++17 | Efficient statevector operations and numerical optimization |
| Java 17 | Enterprise experiment orchestration and typed domain modeling |
| PostgreSQL | Experiment persistence, circuit configuration, measurements and analytics |

The implementations use the weighted Max-Cut problem as their common optimization domain.

The project demonstrates how a combinatorial optimization problem can be represented as a Hamiltonian, encoded into a parameterized quantum circuit, evaluated using a statevector simulator and optimized using a classical optimization procedure.

The implementations are educational simulators. They do not require a quantum processor or quantum cloud service.

---

## 2. Quantum Approximate Optimization Algorithm

QAOA is a hybrid quantum-classical optimization algorithm designed for approximate solutions to combinatorial optimization problems.

It combines:

- A classical representation of the optimization problem.
- A quantum circuit containing parameterized operations.
- Quantum state preparation and measurement.
- A classical optimizer that updates circuit parameters.
- Repeated circuit evaluation until a stopping condition is reached.

The algorithm uses two Hamiltonians:

1. Cost Hamiltonian, representing the optimization objective.
2. Mixer Hamiltonian, introducing transitions between computational basis states.

The circuit depth is controlled by the integer parameter `p`.

Each layer contains one cost operation and one mixer operation.

For a circuit with depth `p`, the parameter vectors are:

- Gamma: \(\gamma_1,\gamma_2,\ldots,\gamma_p\)
- Beta: \(\beta_1,\beta_2,\ldots,\beta_p\)

The complete parameter vector contains `2p` real-valued parameters.

The optimization process searches for parameters that maximize the expected objective value.

---

## 3. Mathematical Formulation

### 3.1 Combinatorial optimization

A combinatorial optimization problem consists of:

- A finite set of possible solutions.
- An objective function.
- Constraints defining feasible solutions.

For Max-Cut, the input is an undirected weighted graph:

\[
G=(V,E)
\]

where:

- \(V\) represents vertices.
- \(E\) represents edges.
- \(w_{uv}\) represents the weight of edge \((u,v)\).

Each vertex is assigned to one of two partitions.

A binary variable represents its assignment:

\[
x_i\in\{0,1\}
\]

An edge contributes its weight when its endpoints belong to different partitions.

The objective is:

\[
C(x)=
\sum_{(u,v)\in E}
w_{uv}(x_u\oplus x_v)
\]

The optimization problem is:

\[
\max_{x\in\{0,1\}^{|V|}}C(x)
\]

The optimal cut is the partitioning with the highest total weight across the two partitions.

### 3.2 Binary-to-quantum representation

The computational basis of a qubit is represented by:

\[
|0\rangle,\quad |1\rangle
\]

The Pauli-Z operator is:

\[
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
\]

For a binary variable represented by a qubit:

\[
x_i=\frac{1-Z_i}{2}
\]

The edge contribution becomes:

\[
x_u\oplus x_v
=
\frac{1-Z_uZ_v}{2}
\]

Therefore, the Max-Cut cost Hamiltonian is:

\[
H_C=
\sum_{(u,v)\in E}
\frac{w_{uv}}{2}
(I-Z_uZ_v)
\]

Its eigenvalue on a computational basis state equals the corresponding cut value.

The optimization objective is to maximize:

\[
\langle H_C\rangle
\]

### 3.3 Cost unitary

The cost unitary is:

\[
U_C(\gamma)=e^{-i\gamma H_C}
\]

It applies a phase to each computational basis state according to its objective value.

For a particular state \(x\):

\[
U_C(\gamma)|x\rangle
=
e^{-i\gamma C(x)}|x\rangle
\]

The cost operation does not change computational basis probabilities immediately. It changes the relative phases between amplitudes.

Those phases affect subsequent mixer operations.

### 3.4 Mixer Hamiltonian

The standard transverse-field mixer Hamiltonian is:

\[
H_B=\sum_{i=1}^{n}X_i
\]

where \(X_i\) is the Pauli-X operator acting on qubit \(i\).

The mixer unitary is:

\[
U_B(\beta)=e^{-i\beta H_B}
\]

Because the individual Pauli-X operators act on separate qubits, the mixer can be implemented as a product of single-qubit rotations:

\[
U_B(\beta)=
\prod_{i=1}^{n}
e^{-i\beta X_i}
\]

Each operation corresponds to an RX rotation with angle:

\[
\theta=2\beta
\]

### 3.5 Initial state

The standard QAOA initial state is the uniform superposition:

\[
|+\rangle^{\otimes n}
\]

where:

\[
|+\rangle=
\frac{|0\rangle+|1\rangle}{\sqrt{2}}
\]

For \(n\) qubits:

\[
|\psi_0\rangle=
\frac{1}{\sqrt{2^n}}
\sum_{x\in\{0,1\}^{n}}|x\rangle
\]

This initializes every computational basis solution with equal probability.

### 3.6 Complete QAOA circuit

The parameterized state is:

\[
|\gamma,\beta\rangle=
U_B(\beta_p)U_C(\gamma_p)
\cdots
U_B(\beta_1)U_C(\gamma_1)
|\psi_0\rangle
\]

The expected objective value is:

\[
F(\gamma,\beta)=
\langle\gamma,\beta|
H_C
|\gamma,\beta\rangle
\]

The classical optimization process searches for:

\[
(\gamma^*,\beta^*)=
\arg\max_{\gamma,\beta}
F(\gamma,\beta)
\]

The algorithm subsequently measures the optimized state to obtain candidate solutions.

---

## 4. Max-Cut Problem Implemented

The five implementations use the following graph:

| Vertex | Connected vertices |
|---|---|
| 0 | 1, 2 |
| 1 | 0, 2, 3 |
| 2 | 0, 1, 3 |
| 3 | 1, 2 |

The edge set is:

\[
E=\{(0,1),(0,2),(1,2),(1,3),(2,3)\}
\]

All edges have weight one.

The graph contains:

- Four vertices.
- Five undirected edges.
- Four qubits.
- Sixteen computational basis states.

The optimal cut value is four.

One optimal assignment is:

\[
x=0101
\]

Another equivalent assignment is:

\[
x=1010
\]

Complementary assignments represent the same partition with the two sides exchanged.

The example is intentionally small enough for exhaustive classical verification.

---

## 5. Statevector Simulation

A statevector stores the complex probability amplitudes of all computational basis states.

For \(n\) qubits:

\[
|\psi\rangle=
\sum_{x=0}^{2^n-1}\alpha_x|x\rangle
\]

Each amplitude is a complex number:

\[
\alpha_x=a_x+ib_x
\]

The probability of measuring state \(x\) is:

\[
P(x)=|\alpha_x|^2
\]

Therefore:

\[
P(x)=a_x^2+b_x^2
\]

A valid statevector must satisfy:

\[
\sum_x|\alpha_x|^2=1
\]

### 5.1 Initialization

All amplitudes are initialized to:

\[
\alpha_x=\frac{1}{\sqrt{2^n}}
\]

This creates the uniform superposition.

### 5.2 Cost operation

For each basis state, the simulator:

1. Calculates its binary assignment.
2. Evaluates its weighted cut.
3. Calculates the corresponding complex phase.
4. Multiplies the amplitude by that phase.

The operation is diagonal and does not require a dense matrix multiplication.

### 5.3 Mixer operation

For each qubit, amplitudes are processed in pairs.

The pair consists of:

- A basis state whose selected bit is zero.
- A basis state differing only in that bit.

For amplitudes \(a_0\) and \(a_1\):

\[
\begin{bmatrix}
a'_0\\
a'_1
\end{bmatrix}
=
\begin{bmatrix}
\cos\beta&-i\sin\beta\\
-i\sin\beta&\cos\beta
\end{bmatrix}
\begin{bmatrix}
a_0\\
a_1
\end{bmatrix}
\]

This implements the mixer without constructing a complete matrix.

### 5.4 Numerical validation

The implementations check state normalization after circuit execution.

Other validation conditions include:

- Valid graph dimensions.
- Valid edge endpoints.
- No self-loops.
- No duplicate undirected edges.
- Positive finite edge weights.
- Valid parameter dimensions.
- Finite circuit parameters.
- Valid measurement bitstrings.

---

## 6. Classical Optimization

QAOA uses a classical optimizer to update the quantum circuit parameters.

The project implements coordinate search.

For each parameter:

1. Evaluate the current objective.
2. Test a positive parameter adjustment.
3. Test a negative parameter adjustment.
4. Retain the best candidate.
5. Reduce the step size when no improvement is found.
6. Stop when the step size becomes sufficiently small or the iteration limit is reached.

The optimization problem is:

\[
\max_{\gamma,\beta}F(\gamma,\beta)
\]

The implementation restricts the search ranges to:

\[
0\leq\gamma_i\leq\pi
\]

\[
0\leq\beta_i\leq\frac{\pi}{2}
\]

These are practical search bounds for the implemented examples, not universal restrictions on all QAOA formulations.

### Coordinate-search characteristics

| Property | Description |
|---|---|
| Optimization type | Derivative-free |
| Search direction | One parameter at a time |
| Objective | Expected cut value |
| Step adjustment | Reduction when improvement stops |
| Gradient requirement | None |
| Main limitation | May converge to a local solution |

The optimizer is intended for transparent experimentation rather than large-scale production optimization.

---

## 7. Measurement and Approximation Quality

After optimization, the circuit produces a probability distribution over computational basis states.

A measurement selects one bitstring according to that distribution.

Repeated measurements produce a frequency distribution.

For `N` shots:

\[
\hat P(x)=\frac{N_x}{N}
\]

where \(N_x\) is the number of times state \(x\) is measured.

The empirical expected cut is:

\[
\hat C=
\sum_x\hat P(x)C(x)
\]

The approximation ratio is:

\[
R=
\frac{\mathbb{E}[C]}
{C_{\mathrm{optimal}}}
\]

For a nonnegative maximization objective with positive optimum, the ratio is between zero and one.

The implementations distinguish:

- Expected cut: Average objective under the complete probability distribution.
- Best observed cut: Highest objective among sampled solutions.
- Most probable state: Bitstring with the highest individual probability.
- Classical optimum: Best solution established through exhaustive classical enumeration.

These values are not interchangeable.

The most probable state is not necessarily the optimal state. A state with a lower probability may have a higher cut value.

---

## 8. Python Implementation

The Python implementation provides the primary numerical simulation.

### Main components

| Component | Responsibility |
|---|---|
| `Edge` | Immutable graph edge |
| `Graph` | Graph validation and cut evaluation |
| `StateVector` | Complex amplitudes and quantum operations |
| `QAOA` | Circuit execution and parameter optimization |
| `QAOAResult` | Experiment output and optimization history |

### Implemented mechanisms

- Uniform superposition initialization.
- Cost Hamiltonian phase application.
- Transverse-field mixer operations.
- State normalization validation.
- Expected cut calculation.
- Coordinate-search optimization.
- Classical exhaustive enumeration.
- Shot-based sampling.
- Reproducible random seeds.
- Assertions for numerical correctness.

The implementation uses Python's built-in complex arithmetic and standard-library functionality.

It does not require NumPy, SciPy or a quantum SDK.

The statevector representation requires exponential memory:

\[
O(2^n)
\]

The cost operation requires:

\[
O(|E|2^n)
\]

The mixer requires:

\[
O(n2^n)
\]

for each QAOA layer.

Consequently, this implementation is intended for small graph instances.

---

## 9. JavaScript Implementation

The JavaScript implementation focuses on experiment execution and event-driven architecture.

### Main components

| Component | Responsibility |
|---|---|
| `Graph` | Graph construction and objective calculation |
| `StateVector` | Complex amplitude operations |
| `QAOACircuit` | Circuit simulation and optimization |
| `ExperimentRunner` | Experiment lifecycle and asynchronous execution |

### Event-driven execution

The experiment runner publishes lifecycle events:

| Event | Meaning |
|---|---|
| `queued` | Experiment accepted |
| `started` | Execution begins |
| `completed` | Optimization and measurement finish |
| `failed` | Execution encounters an error |
| `cancellation-requested` | Cancellation is requested |
| `cancelled` | Cancellation is processed |

The execution model uses Node.js `EventEmitter` and asynchronous functions.

Each experiment receives a UUID.

Experiment records are maintained in a `Map`.

### State management

The experiment lifecycle follows:

`QUEUED → RUNNING → COMPLETED`

Failure produces:

`RUNNING → FAILED`

Cancellation produces:

`RUNNING → CANCELLED`

The implementation includes deterministic pseudorandom measurement sampling for reproducible experiments.

It also uses cumulative probabilities and binary search to select measurement outcomes.

For `S` shots and `2^n` basis states, the sampling process has approximately:

\[
O(S\log(2^n))
\]

selection complexity after probability preparation.

The implementation demonstrates application-level orchestration. Its event-driven interface does not imply that the underlying statevector computation executes on quantum hardware.

---

## 10. C++17 Implementation

The C++ implementation focuses on numerical operations, memory management and domain modeling.

### Main components

| Component | Responsibility |
|---|---|
| `Edge` | Weighted graph edge |
| `Graph` | Objective evaluation and classical optimum |
| `Parameters` | Gamma and beta parameter vectors |
| `StateVector` | Complex amplitude storage |
| `QAOACircuit` | Circuit execution and optimization |
| `Experiment` | Execution status and result |
| `ExperimentManager` | Experiment lifecycle management |

### Engineering decisions

The implementation uses:

- `std::complex<double>` for amplitudes.
- `std::vector` for state storage.
- `std::unordered_set` for duplicate-edge validation.
- `std::mt19937` for reproducible initialization.
- STL algorithms for probability ranking.
- Enumerations for experiment states.
- Exceptions for validation and execution failures.

The basis states are represented by unsigned integer bitmasks.

A selected qubit is accessed using:

\[
mask=1\ll i
\]

This allows direct identification of basis states that differ in one bit.

The implementation uses in-place amplitude transformations rather than dense matrix multiplication.

### Performance considerations

Statevector memory grows exponentially.

For \(n\) qubits, the amplitude count is:

\[
2^n
\]

Each complex double generally requires 16 bytes.

The amplitude storage alone therefore requires approximately:

\[
16\times2^n\text{ bytes}
\]

Additional memory is required for temporary data and graph structures.

The implementation deliberately limits the number of qubits to reduce accidental memory exhaustion.

---

## 11. Java 17 Implementation

The Java implementation models QAOA as an enterprise experiment service.

It emphasizes typed domain objects, immutable configuration, concurrency and explicit execution states.

### Main domain types

| Type | Purpose |
|---|---|
| `Edge` | Immutable graph edge |
| `Graph` | Validated graph definition |
| `Complex` | Complex amplitude arithmetic |
| `CircuitParameters` | Immutable parameter configuration |
| `OptimizationPolicy` | Optimizer execution policy |
| `OptimizationResult` | Optimization output |
| `ExperimentRequest` | Experiment submission contract |
| `ExperimentReport` | Structured execution report |
| `ExperimentService` | Experiment orchestration |

### State transitions

The service uses an `AtomicReference` to manage experiment state.

Valid transitions include:

| Current state | Permitted next states |
|---|---|
| CREATED | QUEUED, FAILED, CANCELLED |
| QUEUED | RUNNING, FAILED, CANCELLED |
| RUNNING | COMPLETED, FAILED, CANCELLED |
| COMPLETED | None |
| FAILED | None |
| CANCELLED | None |

The implementation uses atomic state transitions to prevent conflicting updates.

### Concurrent experiment execution

`ExecutorService` manages worker threads.

`CompletableFuture` provides asynchronous experiment submission and result retrieval.

The service separates:

- Experiment configuration.
- Circuit execution.
- Optimization policy.
- Measurement distribution.
- Final reporting.

This separation is useful when several graph instances or circuit configurations must be evaluated under a common execution service.

The example uses a local executor and in-memory experiment registry. It does not implement durable distributed job scheduling.

---

## 12. PostgreSQL Experiment Database

The PostgreSQL implementation provides a relational model for managing QAOA experiments.

### Entity relationships

The principal relationships are:

`Graphs → Graph Edges`

`Graphs → Experiments`

`Experiments → Circuit Layers`

`Experiments → Optimizer Iterations`

`Experiments → Measurement Outcomes`

`Experiments → Experiment Evaluations`

### Database objects

| Object | Purpose |
|---|---|
| `graphs` | Graph definitions |
| `graph_edges` | Weighted graph connections |
| `experiments` | Experiment configuration and lifecycle |
| `circuit_layers` | Cost and mixer parameters |
| `optimizer_iterations` | Optimization history |
| `measurement_outcomes` | Measured bitstrings and frequencies |
| `experiment_evaluations` | Approximation and performance metrics |

### Integrity controls

The database uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Triggers.
- Stored functions.
- Stored procedures.
- Transaction handling.

The graph-edge trigger validates endpoint ranges and enforces canonical ordering for undirected edges.

The experiment transition trigger prevents invalid lifecycle transitions.

The circuit-layer trigger checks parameter bounds and prevents configuration changes after submission.

The measurement trigger independently calculates the cut value from the graph definition and rejects inconsistent measurement records.

### Stored functions

`calculate_cut_value` evaluates a binary assignment against a stored graph.

Its inputs are:

- Graph identifier.
- Binary measurement string.

Its output is the weighted cut value.

The calculation uses the stored edge definitions rather than trusting an externally supplied objective value.

### Stored procedure

`submit_experiment` checks that the configured experiment contains all required cost and mixer layers before transitioning it into the queued state.

The procedure locks the experiment row using `FOR UPDATE` to reduce concurrent submission conflicts.

### Analytical views

`experiment_readiness` identifies whether the configured circuit contains the expected number of cost and mixer layers.

`experiment_performance` combines experiment metadata with classical and quantum evaluation results.

These views separate operational information from reporting logic.

---

## 13. QAOA Workflow

The implemented workflow follows:

`Graph Definition`

`↓`

`Binary Optimization Objective`

`↓`

`Cost Hamiltonian Construction`

`↓`

`Mixer Hamiltonian Construction`

`↓`

`Uniform Superposition`

`↓`

`Parameterized QAOA Circuit`

`↓`

`Statevector Simulation`

`↓`

`Expected Objective Calculation`

`↓`

`Classical Parameter Optimization`

`↓`

`Optimized Circuit`

`↓`

`Measurement Sampling`

`↓`

`Candidate Bitstrings`

`↓`

`Classical Solution Evaluation`

`↓`

`Approximation Performance Report`

The classical optimizer and quantum circuit have different responsibilities.

The circuit produces a parameter-dependent probability distribution.

The classical optimizer selects new parameters based on the objective calculated from that distribution.

This interaction is the defining hybrid feature of QAOA.

---

## 14. Distinctions Between Important Concepts

| Concept | Meaning |
|---|---|
| QAOA depth | Number of alternating cost and mixer layers |
| Gamma | Cost-unitary parameter |
| Beta | Mixer-unitary parameter |
| Cost Hamiltonian | Quantum representation of the objective |
| Mixer Hamiltonian | Operator that changes computational basis amplitudes |
| Statevector | Complex amplitudes representing the quantum state |
| Probability distribution | Measurement probabilities derived from amplitudes |
| Shot | One measurement execution |
| Expected cut | Probability-weighted average objective |
| Best observed cut | Highest objective among measured candidates |
| Classical optimum | Globally best solution established by classical evaluation |
| Approximation ratio | Expected objective divided by the classical optimum |

A higher QAOA depth increases the number of trainable parameters and circuit operations.

It does not guarantee a better practical result under finite computational or hardware resources.

---

## 15. Edge Cases and Failure Handling

The implementations address several important failure conditions.

| Condition | Expected handling |
|---|---|
| Zero vertices | Graph validation failure |
| Excessive qubit count | Simulation rejected |
| Negative edge weight | Graph validation failure |
| Self-loop | Graph validation failure |
| Duplicate undirected edge | Graph validation failure |
| Invalid bitstring | Measurement rejected |
| Non-finite parameter | Circuit validation failure |
| Incorrect parameter count | Circuit validation failure |
| Invalid QAOA depth | Configuration rejected |
| Invalid shot count | Sampling rejected |
| State normalization error | Simulation failure |
| Invalid experiment transition | Lifecycle update rejected |
| Failed experiment | Error state and diagnostic message |

An empty edge set is a valid graph configuration, although it produces a zero-valued Max-Cut objective.

For a zero optimum, the approximation ratio is defined as one in the example implementations to avoid division by zero.

---

## 16. Security and Operational Considerations

### Input validation

Graph definitions and circuit parameters must be validated before execution.

Untrusted graph inputs should be subject to limits on:

- Vertex count.
- Edge count.
- Weight magnitude.
- Circuit depth.
- Shot count.
- Optimization iterations.

### Resource management

Statevector simulation has exponential memory and computational requirements.

A production execution service should enforce:

- Maximum qubit limits.
- Maximum experiment duration.
- Memory quotas.
- Concurrent execution limits.
- Cancellation handling.
- Execution timeouts.

### Database security

The PostgreSQL implementation uses parameterized database operations as the expected application integration model.

Production deployments should also apply:

- Restricted database roles.
- Least-privilege permissions.
- Connection authentication.
- Encrypted connections.
- Audit logging.
- Backup and recovery procedures.
- Transaction isolation appropriate to concurrent experiment submission.

### Experiment reproducibility

Experiment metadata includes a random seed, backend identity, circuit depth and optimizer configuration.

A reproducible experiment should preserve:

- Graph definition.
- Edge weights.
- Initial parameters.
- Final parameters.
- Optimizer settings.
- Measurement counts.
- Backend configuration.
- Software version.
- Execution timestamps.

A random seed alone does not guarantee identical results across different quantum hardware, simulators or numerical implementations.

---

## 17. Limitations and Practical Implications

### Statevector scalability

The principal limitation is exponential statevector growth.

The simulator is useful for:

- Understanding quantum circuit operations.
- Validating Hamiltonian formulations.
- Comparing small optimization instances.
- Studying parameter sensitivity.
- Testing measurement distributions.

It is not suitable for simulating large quantum systems.

### Classical optimization

Coordinate search is simple and interpretable but does not guarantee a global optimum.

More advanced QAOA experiments can use gradient-based or gradient-free optimizers.

Examples include SPSA, COBYLA and Nelder-Mead.

Their practical effectiveness depends on circuit structure, objective landscape, noise and evaluation budget.

### Hardware execution

The five implementations simulate circuit behavior locally.

They do not include:

- Physical quantum gate execution.
- Hardware calibration.
- Device topology mapping.
- Noise characterization.
- Error mitigation.
- Readout calibration.
- Distributed quantum execution.

Actual hardware execution requires a quantum backend and appropriate circuit compilation.

### Approximation interpretation

A high expected objective does not guarantee that every measurement produces a high-quality solution.

Finite measurement shots introduce sampling uncertainty.

Hardware noise may also alter the probability distribution.

The measured solution quality must therefore be evaluated independently from the ideal statevector expectation.

---

## 18. Implementation Comparison

| Engineering dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Graph validation | Yes | Yes | Yes | Yes | Yes |
| Cost operation | Yes | Yes | Yes | Yes | Objective function |
| Mixer operation | Yes | Yes | Yes | Yes | Not simulated |
| Statevector | Yes | Yes | Yes | Yes | Not stored |
| Parameter optimization | Yes | Yes | Yes | Yes | History storage |
| Measurement | Yes | Yes | Probability reporting | Probability reporting | Measurement persistence |
| Experiment lifecycle | Basic | Event-driven | Status model | Enterprise service | Database state |
| Persistence | In-memory | In-memory | In-memory | In-memory | Relational |
| Concurrency | Sequential | Asynchronous orchestration | Sequential | Thread-pool execution | Transactional |

The five implementations share the same mathematical objective but address different engineering concerns.

The numerical implementations focus on state evolution and optimization.

The application implementations focus on execution management and reproducibility.

The database implementation focuses on durable experiment records and integrity enforcement.
