# Quantum Walks and Applications

## Scope

Quantum walks are quantum-mechanical counterparts of classical random walks on graphs, lines, lattices, and other state spaces. A classical walker carries a probability distribution that is updated by stochastic transitions. A quantum walker carries complex amplitudes, and observable probabilities are obtained from the squared magnitudes of those amplitudes.

This project treats four related implementation concerns:

- discrete coined quantum walks
- continuous-time quantum walks
- graph-based quantum search and routing
- probability measurement and application-level evaluation

The implementations deliberately use small graphs so that the state evolution can be inspected directly and the numerical behavior can be validated without external numerical libraries.

## Core Mathematical Model

A quantum state is represented by amplitudes

`|psi> = sum_x alpha_x |x>`

where each `alpha_x` is generally complex and the measurement probability at state `x` is

`P(x) = |alpha_x|^2`.

The state must satisfy

`sum_x P(x) = 1`.

A quantum walk differs from a classical walk because amplitudes can have both magnitude and phase. Paths that reach the same state can interfere constructively or destructively.

### Classical versus quantum evolution

| Property | Classical random walk | Quantum walk |
|---|---|---|
| State representation | Probabilities | Complex amplitudes |
| Transition | Stochastic | Unitary or Hamiltonian evolution |
| Negative or complex phase | No | Yes |
| Interference | No | Yes |
| Measurement | Direct probability state | Probability obtained from amplitude magnitude |
| Typical graph representation | Transition matrix | Adjacency/operator representation |
| Evolution constraint | Probability conservation | Norm conservation |

The comparison is useful because a quantum walk is not simply a faster version of a classical random walk. Its behavior follows from coherent amplitude evolution and interference.

## Discrete Coined Quantum Walk

The Python and JavaScript implementations include a one-dimensional coined walk.

The walker has two components:

- position
- coin state

The coin state determines the direction of movement. A Hadamard transformation is applied to the two coin amplitudes before the conditional movement.

For amplitudes `a` and `b`, the Hadamard transformation is

`H(a,b) = ((a+b)/sqrt(2), (a-b)/sqrt(2))`.

The resulting coin components are shifted in opposite directions.

The complete evolution therefore consists of:

`coin transformation -> conditional shift -> next quantum state`

The implementation stores the state using `(position, coin)` pairs. This makes the distinction between spatial position and internal coin state explicit.

The Python implementation uses dictionaries keyed by state tuples. The JavaScript implementation uses `Map`, which is appropriate for a sparse state representation because most theoretically possible positions are absent at a particular step.

## Continuous-Time Quantum Walk

The C++17 and Java implementations focus on continuous-time quantum walks.

For an adjacency matrix `A`, the evolution operator is represented by

`U(t) = exp(-iAt)`.

The initial state evolves according to

`|psi(t)> = exp(-iAt)|psi(0)>`.

For the small graphs used in this project, the implementations calculate the matrix exponential through a truncated Taylor expansion. This keeps the programs self-contained and exposes the evolution mechanism directly.

The expansion is

`exp(-iAt) = I + (-iAt) + (-iAt)^2/2! + ...`.

Terms are accumulated until their contribution becomes numerically negligible.

For production scientific computation on large graphs, this direct approach is not the preferred numerical strategy. Large sparse systems generally require specialized matrix-exponential, eigensolver, sparse-linear-algebra, or Hamiltonian-simulation techniques.

## Graph Representation

The domain model follows:

`Graph -> Vertices -> Edges -> Quantum State -> Evolution -> Measurement`

The graph is represented by an adjacency matrix in the executable examples.

An undirected graph requires

`A[i][j] = A[j][i]`.

Self-loops are rejected by the implementations because the examples model movement between distinct graph vertices.

The PostgreSQL implementation stores the same conceptual structure relationally:

| Table | Responsibility |
|---|---|
| `graph` | Graph metadata |
| `vertex` | Graph vertices |
| `graph_edge` | Graph connectivity |
| `quantum_experiment` | Walk configuration and lifecycle |
| `probability_observation` | Measured or simulated vertex probabilities |
| `application_requirement` | Application-specific probability thresholds |
| `experiment_event` | Operational experiment history |

This separation prevents graph topology from being mixed with experiment state.

## Python Implementation

The Python program provides the broadest simulation model.

### Graph validation

The `Graph` dataclass validates:

- non-empty graph
- square adjacency matrix
- binary adjacency values
- absence of self-loops
- undirected symmetry

Invalid graph structures fail immediately rather than producing misleading quantum probabilities.

### State normalization

`normalize()` computes the Euclidean norm of a complex state and scales every amplitude accordingly.

This protects later probability calculations from accumulated numerical drift.

### Discrete walk

`one_dimensional_discrete_quantum_walk()` stores amplitudes in a dictionary.

A dictionary is useful because the number of occupied positions grows with the number of steps rather than requiring a large fixed array.

The implementation applies the Hadamard coin and then performs the conditional spatial shift.

### Continuous-time walk

`continuous_time_quantum_walk()` uses the adjacency matrix as the Hamiltonian for the educational model and approximates its exponential through a Taylor expansion.

The result is normalized before probabilities are returned.

### Validation scenarios

The Python program checks:

- probability normalization
- zero-state rejection
- invalid graph structures
- negative time
- negative step counts
- invalid vertex indexes
- disconnected-node reachability

The program also produces a JSON-compatible report containing the principal probability distributions.

## JavaScript Implementation

The JavaScript program emphasizes asynchronous and event-driven execution.

`QuantumWalkEngine` extends `EventEmitter`.

The discrete walk emits a `step` event after each evolution step. A scheduled event-loop yield prevents the example from monopolizing the Node.js event loop during repeated asynchronous processing.

Measurement emits a `measurement` event containing the selected vertex and measurement number.

The JavaScript complex-number representation uses plain objects containing `re` and `im` fields. Complex addition, multiplication, scaling, and magnitude calculations are implemented explicitly.

This avoids external packages while keeping the mathematical representation visible.

The `measure()` method validates that probabilities are normalized before sampling a vertex. The sampling operation uses cumulative probability intervals.

This reflects an important distinction:

`quantum evolution -> probability distribution -> classical measurement result`

The measurement output is classical even though the state before measurement is represented by quantum amplitudes.

## C++17 Governance and Analysis Engine

The C++17 program presents the topic as a graph-analysis engine.

The `Graph` class owns and validates the topology. `QuantumWalkEngine` operates on the validated graph without modifying it.

The separation provides two useful properties:

1. graph invariants are established before simulation
2. simulation logic does not need to repeatedly defend against malformed topology

The engine contains both:

- a classical random-walk implementation
- a continuous-time quantum-walk implementation

This allows the same graph to be evaluated under different stochastic and quantum dynamics.

The `MergeSearchApplication` class provides an application-oriented layer that interprets quantum-walk probabilities as candidate route or target probabilities.

The example also tests a disconnected graph. A node belonging to a disconnected component must retain zero probability when the initial state is outside that component.

## Java 17 Enterprise Domain Model

The Java implementation models quantum-walk processing as an explicit service workflow.

The primary domain types are:

- `WalkModel`
- `NodeRole`
- `Node`
- `ProbabilityResult`
- `Graph`
- `WalkPolicy`
- `ContinuousTimePolicy`
- `WalkService`
- `RouteAnalysis`

The `WalkPolicy` interface provides an extension point for different walk models.

`WalkService` selects the policy registered for a requested model. This prevents the application layer from embedding numerical details directly into business workflow code.

`ProbabilityResult` is immutable. It contains both the probability vector and the normalization error.

`RouteAnalysis` separates graph reachability and probability ranking from the numerical evolution service.

This produces a clear enterprise-oriented boundary:

`domain validation -> walk policy -> probability result -> application analysis`

The implementation also distinguishes graph reachability from quantum probability. A graph can structurally connect two vertices while a particular finite-time quantum evolution gives the target a small probability.

## PostgreSQL Data Model

The PostgreSQL script represents a persistent experimental environment.

### Graph data

`graph` stores graph-level metadata.

`vertex` stores individual vertices.

`graph_edge` stores connections between vertices and enforces foreign-key integrity.

### Experiment data

`quantum_experiment` records:

- graph
- walk model
- application
- start vertex
- optional target
- evolution time
- discrete step count
- lifecycle status

This prevents configuration from being confused with observations.

### Probability observations

`probability_observation` stores a probability associated with a vertex and experiment.

A trigger rejects probabilities outside the interval `[0,1]`.

The `probability_total()` function provides a reusable normalization query.

The `target_probability()` function retrieves the observation associated with the experiment's configured target.

### Application thresholds

`application_requirement` gives different applications separate thresholds.

For example, graph search and graph analysis do not need to share the same decision criterion.

The `eligible_targets` view joins observed probabilities with the relevant application requirement. This creates an explicit distinction between a numerical observation and an application-level decision.

## Database Validation

The PostgreSQL design uses multiple layers of integrity.

Structural integrity is enforced with:

- primary keys
- foreign keys
- unique constraints
- check constraints

Behavioral validation is enforced with triggers.

Analytical validation is performed with queries and CTEs.

The normalization query calculates:

`ABS(sum(probability) - 1)`

A sufficiently small value indicates that the stored observation set represents a normalized state.

The transaction demonstrates atomic creation of an experiment, its observations, and its event record.

A deliberately invalid experiment is also attempted inside a protected PL/pgSQL block. The database rejects the invalid vertex through the trigger rather than allowing an inconsistent experiment into persistent storage.

## Applications of Quantum Walks

### Quantum search

Quantum walks can define dynamics over a graph where marked vertices represent candidate targets.

The graph structure determines possible movement, while interference determines the resulting amplitude distribution.

A practical search workflow can therefore be expressed as:

`graph -> initial state -> quantum evolution -> target amplitude -> measurement`

The probability of a target is not equivalent to graph distance. It depends on the walk model, initial state, evolution time, graph topology, and interference.

### Network analysis

Graphs can represent communication, transport, dependency, or interaction networks.

A continuous-time walk can provide a dynamical perspective on graph structure. Probability distributions can be inspected to identify vertices receiving significant amplitude at selected evolution times.

This should not be interpreted automatically as a routing algorithm. The quantum walk supplies a physical or mathematical evolution model; an application layer must define what a probability means operationally.

### Quantum simulation

Quantum walks are useful as compact models for studying quantum dynamics on discrete structures.

The adjacency matrix provides a convenient Hamiltonian for continuous-time examples.

The small examples here make the evolution observable without depending on a full quantum-computing stack.

### Graph analysis

Quantum-walk behavior can reveal properties that differ from classical diffusion.

Interference can produce probability distributions that are more structured than those obtained from repeated classical averaging.

The comparison implemented in the C++ program provides a direct baseline between classical and quantum dynamics.

## Measurement and Interpretation

The simulation produces probabilities, but a real measurement produces a single classical outcome.

For a state with probabilities

`[p0, p1, p2, ..., pn]`

a measurement samples one vertex according to those probabilities.

Repeated measurements produce an empirical frequency distribution that approaches the theoretical probability distribution as the number of independent experiments increases.

This distinction is important when interpreting application results.

A probability of `0.40` for a target does not mean that the target is reached deterministically. It means that the target would be observed with that probability under the specified state preparation, evolution, and measurement process.

## Edge Cases

The implementations explicitly address several failure conditions.

| Edge case | Handling |
|---|---|
| Empty graph | Rejected |
| Non-square adjacency matrix | Rejected |
| Invalid adjacency value | Rejected |
| Self-loop | Rejected |
| Asymmetric undirected graph | Rejected |
| Invalid vertex | Rejected |
| Negative time | Rejected |
| Negative step count | Rejected |
| Zero quantum state | Rejected |
| Probability outside `[0,1]` | Rejected |
| Probability normalization drift | Detected |
| Disconnected target | Reachability remains false or probability remains zero |
| Numerical convergence | Taylor expansion terminates when terms become negligible |

## Performance Considerations

For a graph with `n` vertices, dense adjacency-matrix multiplication requires approximately `O(n²)` work per matrix-vector operation.

The Taylor-series matrix-exponential implementation performs multiple such operations, so it is intended for small educational graphs rather than large production simulations.

The discrete coined walk uses sparse state storage in Python and JavaScript. This is useful when only a subset of all possible position/coin states is populated.

The PostgreSQL schema indexes graph edges by source vertex and experiment observations by probability. These indexes correspond to actual access patterns used by graph traversal and probability-ranking queries.

Large quantum-walk simulations require different numerical strategies. Sparse matrices, spectral decomposition, Krylov-subspace methods, tensor representations, or specialized quantum simulation systems may be appropriate depending on the graph and physical model.

## Security and Integrity Considerations

The implementations do not treat probability values as trusted application input.

Validation occurs before probabilities are used for measurement or decision logic.

The database provides a second integrity boundary through constraints and triggers. This matters because application-level validation alone cannot prevent another database client from inserting invalid values.

The PostgreSQL design also separates graph topology from experiment results. This reduces the chance that modifying an experiment accidentally changes the underlying graph.

For a production service, access control should restrict who can modify graph definitions and experiment configurations. Audit events should record configuration changes and execution outcomes where reproducibility is required.

## Reproducibility

A quantum-walk experiment is determined by its model parameters and initial state.

A reproducible experiment record should capture at least:

- graph identity
- graph topology
- walk model
- starting vertex or initial state
- coin operator for coined walks
- evolution time or number of steps
- target definition
- numerical precision
- software version
- measurement procedure

The PostgreSQL `quantum_experiment` table captures the core graph, model, start, target, time, and step configuration. A production research system would extend this with explicit initial-state and numerical-method metadata.

## Relationship Between the Five Implementations

| Implementation | Primary perspective | Main mechanism |
|---|---|---|
| Python | Mathematical simulation | Dataclasses, dictionaries, complex amplitudes, normalization |
| JavaScript | Event-driven simulation | `Map`, asynchronous execution, events, measurement |
| C++17 | Graph-analysis engine | Strong domain classes, STL containers, numerical evolution |
| Java 17 | Enterprise domain model | Records, policies, services, immutable results, validation |
| PostgreSQL | Persistent experiment system | Relational integrity, functions, triggers, views, transactions |

The implementations share the same conceptual domain without being mechanical translations.

Python emphasizes direct state simulation.

JavaScript emphasizes event-driven execution and measurement events.

C++17 emphasizes a reusable graph and numerical engine.

Java 17 emphasizes domain boundaries and policy-driven services.

PostgreSQL emphasizes persistence, validation, reporting, and transactional integrity.

## Practical Workflow

A complete experimental workflow can be represented as:

`Graph definition`
`      ↓`
`Vertex and edge validation`
`      ↓`
`Initial quantum state`
`      ↓`
`Choose walk model`
`      ↓`
`Quantum evolution`
`      ↓`
`Amplitude calculation`
`      ↓`
`Probability calculation`
`      ↓`
`Normalization validation`
`      ↓`
`Application-specific analysis`
`      ↓`
`Measurement or decision`

The important distinction is that graph structure, quantum evolution, probability, and application interpretation are separate layers.

A graph defines where transitions are possible.

The walk model defines how the state evolves.

Amplitudes encode the quantum state.

Probabilities describe measurement likelihood.

The application layer determines what those probabilities mean for search, routing, simulation, or graph analysis.
