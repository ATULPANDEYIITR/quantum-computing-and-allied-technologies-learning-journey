# Grover's Algorithm: Quantum Search

## Purpose

Grover's algorithm searches an unstructured space of \(N=2^n\) possible states for one or more states satisfying a specified condition. It uses a quantum oracle to mark valid states by changing their phases, then applies amplitude amplification to increase their measurement probabilities.

For \(M\) marked states, the query complexity is \(O(\sqrt{N/M})\) when \(M\) is known and substantially smaller than \(N\). A classical search may require \(O(N/M)\) evaluations in the worst case under a suitable search model. Grover's algorithm does not eliminate the cost of implementing the oracle or preparing and measuring the quantum state.

The five implementations approach the subject from complementary perspectives:

- **Python:** A state-vector simulator with validation, a classical comparison, and numerical assertions.
- **JavaScript:** A search engine with typed arrays, asynchronous events, and an event audit trail.
- **C++17:** A resource-conscious state-vector engine using STL containers, explicit configuration checks, and numerical validation.
- **Java 17:** An enterprise-oriented search service with immutable request records, execution states, policy limits, and audit events.
- **PostgreSQL:** A relational experiment registry with oracle targets, execution records, probability distributions, validation reports, and reporting queries.

## Mathematical Model

### Search space and marked states

An \(n\)-qubit system has \(N=2^n\) computational basis states. Each basis state corresponds to an integer from \(0\) to \(N-1\), which can also be represented by an \(n\)-bit binary string.

A Boolean oracle identifies marked states. If the number of marked states is \(M\), the initial state is an equal superposition:

\[
|s\rangle=\frac{1}{\sqrt{N}}\sum_{x=0}^{N-1}|x\rangle
\]

Each basis state initially has amplitude \(1/\sqrt{N}\) and measurement probability \(1/N\).

The example searches four qubits, giving sixteen possible states, and marks state \(5\), represented as `0101`.

### Phase oracle

The phase oracle applies a sign change to each marked state:

\[
O_f|x\rangle=(-1)^{f(x)}|x\rangle
\]

Here, \(f(x)=1\) for a marked state and \(f(x)=0\) otherwise. The oracle does not directly increase a marked state's probability because measurement probabilities are squared amplitude magnitudes.

The phase change creates the relative phase differences needed by the next operation.

### Diffusion operator

The diffusion operator reflects amplitudes around their mean:

\[
D=2|s\rangle\langle s|-I
\]

For a real-valued amplitude vector with mean \(\bar a\), the updated amplitude of state \(x\) is:

\[
a'_x=2\bar a-a_x
\]

A Grover iteration applies the phase oracle followed by the diffusion operator. Repeating this operation transfers probability toward the marked subspace.

### Optimal iteration count

Define

\[
\theta=\arcsin\sqrt{\frac{M}{N}}
\]

After \(r\) Grover iterations, the ideal probability of measuring a marked state is

\[
P_{\text{success}}=\sin^2((2r+1)\theta)
\]

A useful near-optimal iteration count is

\[
r\approx\left\lfloor\frac{\pi}{4\theta}-\frac12\right\rfloor
\]

with negative values clamped to zero. The exact integer choice depends on \(M\) and \(N\). More iterations are not always better: repeated amplification can rotate the state past its highest marked-state probability.

When all states are marked, no amplification is necessary and the optimal iteration count is zero. When the marked-state count is unknown, a search procedure cannot directly use the count-dependent iteration formula without an estimation or adaptive strategy.

## Four Distinct Computational Responsibilities

The implementations separate the main computational responsibilities.

| Component | Responsibility | What it does not guarantee |
|---|---|---|
| Search-space preparation | Initializes equal amplitudes over the basis states | Does not identify a marked state |
| Oracle | Applies phase inversion to marked states | Does not by itself amplify measurement probability |
| Diffusion | Amplifies the marked subspace through amplitude reflection | Does not guarantee success after an arbitrary iteration count |
| Measurement model | Converts the final state into a probability distribution | Does not guarantee a particular outcome in a physical measurement |

The examples use a deterministic most-probable-state selection for reproducibility. That selection is a reporting convenience, not a simulation of random quantum measurement. A physical measurement produces an individual outcome sampled according to the probability distribution.

## Python Implementation

The Python file defines `GroverSearch`, `SearchResult`, and `QuantumSearchError`.

### State-vector representation

The state vector is a list of real amplitudes. The constructor validates the qubit count, search-domain boundaries, and marked-state collection. Duplicate marked states are removed, and the normalized set is stored as a tuple and a frozen set.

The simulator limits the number of qubits to twenty. This prevents unrestricted memory allocation, although the permitted upper bound can still require substantial memory.

### Execution workflow

The `run` method performs the following operations:

1. Initialize a uniform superposition.
2. Apply the phase oracle to every marked state.
3. Calculate the mean amplitude.
4. Apply the diffusion reflection.
5. Convert amplitudes into probabilities.
6. Calculate total marked-state probability.
7. Validate normalization and return an immutable result record.

The separate `classical_search` function performs sequential predicate evaluation. It reports the number of evaluations, making the comparison explicit rather than suggesting that a quantum simulator is automatically faster than a classical program.

### Validation

The executable example checks that probabilities sum to one, that state `5` is the most probable outcome, and that its success probability exceeds the configured example threshold. It also verifies the all-marked and invalid-target cases.

The classical comparison stops at the first match. Its evaluation count depends on the ordering of the predicate's matches.

## JavaScript Implementation

The JavaScript file uses a `Float64Array` for the amplitude vector. This gives predictable numeric storage and avoids the overhead of a general-purpose array for the numerical state.

### Search engine

`GroverSearch` validates the search configuration, calculates the near-optimal iteration count, applies the phase oracle and diffusion operator, and produces a frozen result object. The probability array is constructed from the final amplitudes.

The implementation uses real-valued amplitudes because the selected Grover operations preserve real amplitudes when starting from the uniform real superposition. General quantum circuits, including circuits with arbitrary phase rotations, may require complex amplitudes.

### Event-driven coordination

`SearchCoordinator` separates the execution request from event handling. It emits `search.started`, `search.completed`, and `search.failed` events. Subscribers can register listeners and receive an unsubscribe function.

The event system uses promises to wait for all listeners registered for an event. A listener failure can cause event processing to reject, so production services should define whether audit-listener errors should fail the search, be isolated, or be sent to a separate durable logging system.

The in-memory event log is useful for demonstrations but is not a durable audit store. It has no authentication, authorization, persistence, or protection against process termination.

### Error handling

Invalid qubit counts, missing marked states, invalid targets, and negative iteration counts are rejected. The top-level handler reports failures and sets a nonzero process exit status.

## C++17 Implementation

The C++17 program treats the simulator as a compact numerical engine.

### Resource and state management

`GroverEngine` owns the search-space configuration and validates it during construction. Its state vector uses `std::vector<double>`, while `std::set<int>` supports membership checks when calculating the marked probability.

The implementation uses integer state identifiers for basis-state indexing. The maximum qubit count is checked before calculating the state-space size, and the size is calculated with a shift on `size_t` to avoid an invalid signed shift.

### Numerical execution

The `run` method applies phase inversion and amplitude reflection directly to the state vector. It then computes the probability distribution, normalization, marked probability, and most-probable state.

The returned `SearchResult` groups the numerical output with the configuration and execution status. Exceptions distinguish invalid configuration from failures encountered during numerical execution.

### Engineering trade-offs

The engine stores all amplitudes explicitly. This simplifies inspection and validation but requires \(O(2^n)\) memory. Each iteration takes \(O(2^n+M)\) work in this implementation, and the complete execution takes \(O(r2^n)\) time for \(r\) iterations when the marked-state count is small.

The program does not simulate hardware noise, gate errors, finite-shot measurement statistics, or a fault-tolerant quantum processor. It is a state-vector case study, not a hardware performance benchmark.

## Java 17 Implementation

The Java implementation separates request validation, search execution, execution policy, and audit reporting.

### Domain records and policy

`SearchRequest` is an immutable record that defensively copies the supplied marked-state list. `SearchPolicy` defines the maximum permitted iteration count and minimum acceptable success probability. `SearchResult` returns an immutable probability distribution and execution status.

The service validates that target states are unique and lie within the search domain. The iteration limit prevents requests that exceed the configured execution budget.

### Explicit execution states

The service records transitions through `CREATED`, `VALIDATED`, `EXECUTING`, and `COMPLETED`. Failures are reported using the `FAILED` state.

`SearchAudit` provides an interface for recording state changes. The supplied `ConsoleAudit` implementation prints events, while a production implementation could persist them in a database or send them to a centralized audit system.

### Policy evaluation

The minimum success-probability policy is evaluated after the numerical distribution is calculated. A result that falls below the configured threshold is rejected rather than silently presented as a successful search.

This is a service-level acceptance rule, not a mathematical guarantee of Grover's algorithm. A legitimate quantum execution can have a success probability below an application's threshold, especially with an unsuitable iteration count or noisy hardware.

The example policy requires at least 0.90 success probability and permits up to 100 iterations. The sample four-qubit search with one marked state satisfies this policy.

## PostgreSQL Experiment Model

The PostgreSQL script stores experiment configuration separately from execution outcomes and validation reports. It uses the `quantum_search` schema to isolate its tables and functions.

### Relational structure

The principal relationships are:

- `algorithms` identifies an algorithm and its complexity description.
- `experiments` records the qubit count, search-space size, expected number of marked states, requested iterations, and experiment status.
- `oracle_targets` records each marked basis state and its label.
- `executions` stores individual runs, iteration counts, observed states, success probabilities, timestamps, and failures.
- `state_probabilities` stores the probability associated with each basis state for an execution.
- `validation_reports` records normalization, marked-probability, domain, and policy checks.

The `experiments` table calculates the search-space size from the qubit count. Foreign keys preserve relationships, check constraints reject invalid values, and unique constraints prevent duplicate experiment names, execution numbers within an experiment, and basis states within an execution.

### Trigger-enforced rules

The `validate_oracle_target` trigger checks that a target belongs to the configured search domain.

The `validate_execution_domain` trigger checks observed-state bounds and verifies that a completed execution has a recorded result and completion timestamp. It also checks that the configured number of oracle targets agrees with the experiment's expected marked-state count.

These checks complement ordinary constraints. They do not prove that the stored numerical results were produced by a valid quantum circuit. Trusted computation or independent numerical verification is still required.

### Evaluation function

`evaluate_execution` calculates the sum of the stored probability distribution and the total probability assigned to marked states. It compares the results against normalization and the recorded success probability, then writes validation reports.

The function rejects missing executions, invalid normalization tolerances, and basis states outside the configured domain.

### Reporting and transactions

The `experiment_execution_report` view combines experiment configuration with execution state, probability totals, and target counts. Additional queries aggregate execution performance by qubit count and inspect individual basis-state probabilities.

The demonstration uses `INSERT ... ON CONFLICT` to make sample-data insertion repeatable. The invalid-target example runs inside a nested PL/pgSQL exception block, so the failed insertion is rolled back without aborting the rest of the script.

For concurrent production workloads, experiment execution updates and probability-distribution inserts should be performed transactionally. Database access should use least-privilege roles, and untrusted users should not be granted permission to modify execution results or validation reports.

## Performance and Accuracy

### Time and memory complexity

Let \(N=2^n\) be the number of basis states, \(M\) the number of marked states, and \(r\) the number of Grover iterations.

| Operation | Time complexity | Space complexity |
|---|---:|---:|
| Initialize state vector | \(O(N)\) | \(O(N)\) |
| Apply phase oracle | \(O(M)\) for explicit target lists | \(O(1)\) additional space |
| Apply diffusion operator | \(O(N)\) | \(O(1)\) additional space |
| Run \(r\) iterations | \(O(rN)\) | \(O(N)\) |
| Calculate all probabilities | \(O(N)\) | \(O(N)\) when stored |

The explicit-target oracle is convenient for small demonstrations. A real problem may require a reversible circuit that computes the marking predicate, and its gate count can dominate the physical cost.

Grover's query advantage is meaningful when oracle evaluation is expensive in the relevant computational model. It does not imply a universal wall-clock advantage over optimized classical search.

### Floating-point accuracy

All numerical implementations use double-precision floating-point arithmetic. The diffusion step should preserve the state norm mathematically, but accumulated floating-point error can cause small deviations.

The implementations check that the probability distribution sums to approximately one. This detects some numerical failures but does not verify the correctness of every oracle or circuit operation.

### Iteration selection

Too few iterations may leave the marked-state probability low. Too many can reduce it after the state passes the amplification maximum.

When the marked-state count is known, the count-dependent estimate is appropriate for the basic algorithm. When it is unknown, repeated searches with adaptive iteration choices or a separate estimation procedure may be necessary.

## Practical Limitations

- The source programs simulate a state vector rather than executing a physical quantum circuit.
- The real-valued simulation is sufficient for the selected operations but not for arbitrary quantum gates.
- The most-probable-state output is deterministic and should not be confused with a sampled measurement.
- The supplied examples assume a correct oracle and an ideal diffusion operation.
- The PostgreSQL probability records are example data, not a live quantum execution log.
- A database trigger can validate structure and consistency but cannot establish the physical validity of a quantum experiment.
- Dense state-vector storage becomes impractical as qubit counts increase because the number of amplitudes doubles for every additional qubit.

## Running the Implementations

The Python program uses only the Python standard library and can be run with `python grover_search.py`.

The JavaScript program uses Node.js built-in functionality and can be run with `node grover_search.js`.

Compile the C++17 program with a compiler supporting C++17, for example `g++ -std=c++17 -O2 grover_search.cpp -o grover_search`, and run `./grover_search` on Unix-like systems.

Compile and run the Java 17 program using `javac GroverSearch.java` followed by `java GroverSearch`.

Execute the PostgreSQL script with a PostgreSQL client connected to a database where the executing role has permission to create schemas, tables, functions, triggers, and views. The script creates a dedicated schema, records a four-qubit example, evaluates its probability distribution, and demonstrates rejection of an invalid oracle target.
