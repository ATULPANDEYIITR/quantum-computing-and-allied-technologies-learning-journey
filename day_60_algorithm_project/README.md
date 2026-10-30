# Quantum Algorithms: State-Vector Simulation and Experiment Management

## Project Scope

This project implements four quantum algorithms across five technical perspectives:

- Deutsch-Jozsa for classifying promised Boolean functions.
- Bernstein-Vazirani for recovering a hidden bit string.
- Grover search for amplifying marked computational-basis states.
- Quantum Phase Estimation for estimating an eigenphase of a unitary operator.

The implementations use quantum state vectors rather than relying on a third-party quantum computing package. They represent amplitudes, apply quantum operations, derive measurement probabilities, and sample computational-basis outcomes.

The project also separates algorithm execution from experiment management. The JavaScript and Java programs provide execution workflows, while PostgreSQL stores experiment configurations, execution states, circuit gates, measurements, metrics, and audit events.

## Relationship Between the Four Algorithms

The algorithms share a mathematical foundation but solve different computational problems.

| Algorithm | Problem | Main mechanism | Expected output |
|---|---|---|---|
| Deutsch-Jozsa | Determine whether a promised Boolean function is constant or balanced | Interference following a phase oracle | An all-zero or nonzero bit string |
| Bernstein-Vazirani | Recover a hidden binary string | Parity oracle and interference | The hidden bit string |
| Grover | Find one or more marked items in an unstructured search space | Oracle phase inversion and amplitude amplification | A marked basis state |
| Quantum Phase Estimation | Estimate the phase associated with a unitary eigenvalue | Controlled unitary powers and inverse QFT | A binary phase estimate |

The first two algorithms use structured Boolean oracles. Grover uses an oracle that identifies solutions in a search space. Phase estimation works with an eigenstate of a unitary operation and extracts information about its eigenvalue.

These algorithms should not be interpreted as interchangeable forms of quantum search. Their input models, circuit structures, and outputs are different.

## Quantum State Representation

An \(n\)-qubit pure state is represented as:

\[
|\psi\rangle =
\sum_{x=0}^{2^n-1}\alpha_x|x\rangle
\]

Each amplitude \(\alpha_x\) is a complex number. The state must satisfy the normalization condition:

\[
\sum_{x=0}^{2^n-1}|\alpha_x|^2=1
\]

The probability of measuring basis state \(x\) is:

\[
P(x)=|\alpha_x|^2
\]

A quantum gate transforms the amplitudes while preserving the state's total probability. Measurement samples from the resulting probability distribution. It does not reveal every amplitude or provide a direct copy of the complete quantum state.

### Qubit ordering

All five implementations use little-endian basis indexing:

- Qubit 0 corresponds to the least significant bit.
- Qubit 1 corresponds to the next bit.
- The integer basis index represents the complete computational-basis state.

For a four-qubit register, basis index 11 is represented as `1011`. Consistent bit ordering is important when comparing oracle masks, measurements, and secret strings.

### Hadamard operation

The Hadamard gate creates superposition and enables interference:

\[
H =
\frac{1}{\sqrt{2}}
\begin{bmatrix}
1 & 1\\
1 & -1
\end{bmatrix}
\]

For a single qubit:

\[
H|0\rangle=\frac{|0\rangle+|1\rangle}{\sqrt{2}}
\]

The implementations apply Hadamard transformations directly to pairs of amplitudes whose basis indices differ in one selected bit.

### Phase oracles

A phase oracle changes the sign of selected amplitudes:

\[
O_f|x\rangle=(-1)^{f(x)}|x\rangle
\]

This operation does not change the probability of a basis state at the instant it is applied. It changes relative phase, which can alter subsequent interference and therefore change measurement probabilities.

The simulator implements phase oracles as predicates over basis indices. The predicate returns true for states whose amplitudes must be multiplied by \(-1\).

## Deutsch-Jozsa Algorithm

### Problem definition

The Deutsch-Jozsa problem supplies a Boolean function with a promise:

- A constant function returns the same output for every input.
- A balanced function returns zero for half of the inputs and one for the other half.

The objective is to determine which category applies.

### Circuit mechanism

The implementation follows this sequence:

1. Initialize the register to the all-zero basis state.
2. Apply Hadamard gates to every qubit.
3. Apply the Boolean oracle through phase kickback.
4. Apply Hadamard gates again.
5. Measure the input register.

A constant function produces the all-zero result. A balanced function produces a nonzero result under the promised oracle model.

The balanced parity oracle uses a nonzero bit mask. Its output is the parity of the selected input bits. A nonzero parity mask produces a balanced Boolean function because changing any selected input bit reverses the output.

The constant-one oracle changes the global phase of the complete state. Global phase is physically unobservable, so the resulting measurement is the same as for the constant-zero oracle.

### Implementation coverage

| File | Implementation |
|---|---|
| Python | `run_deutsch_jozsa` |
| JavaScript | `DEUTSCH_JOZSA` execution branch |
| C++17 | `deutschJozsa` |
| Java 17 | `runDeutschJozsa` |
| PostgreSQL | `DEUTSCH_JOZSA` configuration and experiment records |

The oracle promise is part of the algorithm's input assumptions. Arbitrary Boolean functions are not automatically classified by this implementation.

## Bernstein-Vazirani Algorithm

### Problem definition

The algorithm receives access to a parity function defined by a secret bit string \(s\):

\[
f_s(x)=x\cdot s \pmod 2
\]

The dot product is calculated using bitwise conjunction followed by parity evaluation.

The objective is to recover \(s\).

### Circuit mechanism

The implementation applies Hadamard gates, evaluates the phase oracle, and applies Hadamard gates again. Interference concentrates the final probability distribution on the hidden string.

The phase oracle uses:

\[
(-1)^{x\cdot s}
\]

The binary secret is converted to an integer mask. The parity of the bitwise conjunction between an input basis index and that mask determines whether the phase is inverted.

For an ideal oracle and exact state-vector simulation, the recovered bit string is deterministic. Multiple measurement shots are still useful for building histograms and exercising the experiment workflow.

### Important distinction

Bernstein-Vazirani is not a general procedure for recovering arbitrary information from an unknown program. It assumes that the oracle implements the specified parity function.

### Validation

The implementations reject:

- Empty secrets.
- Characters other than `0` and `1`.
- Secrets whose length does not match the register.
- Register sizes outside the simulator's configured limits.

## Grover Search

### Problem definition

Grover search addresses an unstructured search space of size:

\[
N=2^n
\]

A marking function identifies one or more solutions. The algorithm increases the amplitudes of marked states so that a measurement is more likely to produce a solution.

### Oracle operation

The oracle applies a phase inversion to every marked state:

\[
O|x\rangle =
\begin{cases}
-|x\rangle & x \text{ is marked}\\
|x\rangle & x \text{ is unmarked}
\end{cases}
\]

The oracle does not directly write the answer into a measurement register. It changes relative phase.

### Diffusion operation

The diffusion operator reflects amplitudes around their mean:

\[
D|\psi\rangle = 2|s\rangle\langle s|\psi\rangle-|\psi\rangle
\]

For an equally weighted initial superposition, this operation increases marked-state amplitudes after the oracle has inverted their signs.

The simulator calculates the mean complex amplitude and applies the reflection directly. This is mathematically equivalent to the diffusion operator but avoids constructing a separate sequence of Hadamard, controlled-phase, and Pauli-X gates.

### Iteration count

For \(M\) marked states in a space of size \(N\), define:

\[
\theta=\arcsin\left(\sqrt{\frac{M}{N}}\right)
\]

The implementations use an iteration count near the first amplitude maximum:

\[
r \approx \frac{\pi}{4\theta}-\frac{1}{2}
\]

The number of iterations is rounded down and cannot be negative.

Using too many iterations can reduce the probability of measuring a marked state. The iteration rule is therefore tied to the number of marked states, not just the total register size.

### Reported probabilities

The Grover implementations report the total probability assigned to all marked states after amplification. This theoretical probability is distinct from the observed fraction of successful measurement shots.

A small shot count can produce a measured success fraction that differs from the theoretical probability.

### Edge cases

The implementation validates that:

- At least one marked state exists.
- Every marked state fits inside the register.
- Duplicate marked states are rejected.
- The iteration count is non-negative.

When every basis state is marked, no amplitude amplification is required because the initial state already has probability one of being marked.

## Quantum Phase Estimation

### Problem definition

Phase estimation estimates an eigenphase \(\phi\) for a unitary operator \(U\) and eigenstate \(|u\rangle\):

\[
U|u\rangle=e^{2\pi i\phi}|u\rangle
\]

The Python and Java implementations use a one-qubit diagonal operator:

\[
U=
\begin{bmatrix}
1 & 0\\
0 & e^{2\pi i\phi}
\end{bmatrix}
\]

The target qubit is initialized in \(|1\rangle\), which is an eigenstate of this operator.

### Controlled powers

The counting register is placed in superposition. Controlled applications of:

\[
U^{2^j}
\]

encode progressively larger multiples of the phase in the counting register.

For the selected target eigenstate, each controlled operation applies a phase rotation:

\[
e^{2\pi i\phi 2^j}
\]

The inverse quantum Fourier transform converts this phase information into a computational-basis measurement.

### Inverse quantum Fourier transform

For a register of size \(N=2^m\), the inverse transform uses:

\[
|x\rangle \mapsto
\frac{1}{\sqrt{N}}
\sum_{y=0}^{N-1}
e^{-2\pi ixy/N}|y\rangle
\]

The Python and Java implementations evaluate this transform directly as a matrix operation on the low-order counting register.

The direct approach is easy to inspect, but its computational cost grows as \(O(4^m)\). It is not a suitable replacement for an optimized quantum Fourier transform circuit on large registers.

### Interpretation and precision

With \(m\) counting qubits, the phase estimate has resolution:

\[
\frac{1}{2^m}
\]

For an exactly representable phase such as \(5/16\), four counting qubits produce the binary result `0101` with probability one in the ideal simulator.

For phases that are not exactly representable with the available register size, measurement outcomes can be distributed across nearby bit strings.

## Python Implementation

The Python file is a compact state-vector laboratory with four algorithm implementations.

### State management

The `StateVector` class stores a list of complex amplitudes. Its methods implement:

- Hadamard transformations.
- Phase-oracle evaluation.
- Controlled phase rotations.
- Grover diffusion.
- Inverse QFT on a low-order register.
- Full-register and partial-register measurement.

The simulator checks the initial basis index and register size before allocating the amplitude array.

### Algorithm functions

| Function | Responsibility |
|---|---|
| `run_deutsch_jozsa` | Classifies a constant or balanced oracle |
| `run_bernstein_vazirani` | Recovers the hidden parity string |
| `run_grover` | Searches a supplied set of marked states |
| `run_phase_estimation` | Estimates a diagonal unitary's eigenphase |
| `optimal_grover_iterations` | Selects an amplitude-amplification iteration count |
| `run_self_tests` | Verifies expected outcomes and validation failures |

The `ExperimentResult` dataclass provides a consistent result structure containing the algorithm name, measured bit string, interpretation, success probability, and algorithm-specific details.

### Measurement and reproducibility

The program uses a seeded instance of `random.Random`. The seed makes a simulation run reproducible, subject to the same Python behavior and implementation.

The `sample` method uses the squared magnitude of each complex amplitude as the measurement weight. Phase information is retained until measurement, where it influences the probability distribution through previous gate operations.

### Resource limits

Dense state-vector storage requires \(2^n\) complex amplitudes. The Python implementation therefore caps the general register at 16 qubits and the phase-estimation counting register at 10 qubits.

The memory requirement grows exponentially, even when the circuit contains relatively few gates.

## JavaScript Implementation

The JavaScript implementation provides an event-driven experiment runner for Deutsch-Jozsa, Bernstein-Vazirani, and Grover search.

### Typed-array representation

The `StateVector` class stores real and imaginary amplitudes in a single `Float64Array`.

For each basis index \(x\):

- `amplitudes[2 * x]` stores the real component.
- `amplitudes[2 * x + 1]` stores the imaginary component.

This representation avoids allocating an object for every complex amplitude.

Hadamard transformations update paired amplitudes directly. Grover diffusion calculates the mean real and imaginary components before performing the reflection.

### Experiment orchestration

`QuantumExperimentRunner` extends Node.js `EventEmitter`.

Its lifecycle produces three event types:

| Event | Meaning |
|---|---|
| `started` | A validated experiment has entered execution |
| `completed` | The result and measurement histogram are available |
| `failed` | Execution or cancellation produced an error |

The `run` method returns a Promise. It yields to the Node.js event loop before running the circuit, allowing callers to process events and cancel work before circuit execution begins.

The optional `AbortSignal` is checked before execution and after the event-loop yield. It does not interrupt a circuit in the middle of a synchronous state-vector operation.

### Policy and validation

The runner checks the algorithm name, register size, shot count, hidden string, oracle type, marked states, and duplicate marked states before allocating the experiment's state vector.

The `Map` histogram tracks observed outcomes. A `Set` represents marked Grover states and provides efficient membership checks.

The deterministic pseudo-random generator makes experiment examples repeatable without third-party packages.

### Operational limits

The JavaScript implementation limits the register to 16 qubits and measurements to 100,000 shots. State-vector operations are synchronous and therefore block the Node.js event loop while a circuit is being calculated.

For larger circuits, the execution model would require worker threads, a native backend, or a remote quantum execution service. Those execution modes are not implemented in this project.

## C++17 Implementation

The C++ file focuses on algorithm execution using STL containers, complex arithmetic, predicates, and explicit error handling.

### Core architecture

| Component | Responsibility |
|---|---|
| `StateVector` | Owns the state amplitudes and applies quantum operations |
| `phaseOracle` | Applies a predicate-driven phase inversion |
| `diffuse` | Performs Grover amplitude reflection |
| `oddParity` | Calculates binary parity efficiently |
| `deutschJozsa` | Runs the promised-function classification circuit |
| `bernsteinVazirani` | Recovers a hidden parity string |
| `groverSearch` | Executes amplitude amplification |

The `StateVector` stores amplitudes in `std::vector<std::complex<double>>`.

The simulator validates every register index before applying a gate. It uses `std::discrete_distribution` for measurement sampling and a seeded `std::mt19937_64` generator for reproducibility.

### Parity calculation

The parity function uses the identity:

\[
x \leftarrow x \mathbin{\&} (x-1)
\]

Each iteration removes the least significant set bit. The parity flag changes once per removed bit.

This avoids converting a binary value to a string merely to count its set bits.

### Grover search representation

The marked-state collection is stored in `std::set<std::uint64_t>`. Duplicate values are rejected before circuit execution.

The same set is used by the phase oracle and the success-probability calculation. This keeps the definition of a solution consistent throughout the experiment.

### Complexity and memory

The state-vector representation uses \(O(2^n)\) complex values.

A single Hadamard operation, phase-oracle pass, or diffusion operation requires \(O(2^n)\) work in this implementation.

Grover execution therefore has state-vector simulation cost:

\[
O(r2^n)
\]

where \(r\) is the number of Grover iterations.

This simulation cost is not the same as the gate-query complexity of Grover's algorithm on quantum hardware.

## Java 17 Implementation

The Java program models an experiment service rather than only exposing isolated algorithm functions.

### Domain model

The main types separate request validation, execution, and results.

| Type | Responsibility |
|---|---|
| `Algorithm` | Defines the supported algorithms |
| `ExperimentRequest` | Holds immutable experiment input |
| `ExperimentResult` | Holds immutable execution output |
| `QuantumBackend` | Defines the execution boundary |
| `ExperimentPolicy` | Defines request validation |
| `DefaultExperimentPolicy` | Enforces the configured operating limits |
| `StateVectorBackend` | Executes the quantum algorithms |
| `ExperimentService` | Coordinates asynchronous experiment submissions |

Java records are used for immutable request and result values. The compact constructors normalize null collections and reject missing mandatory values.

### Explicit policy evaluation

`DefaultExperimentPolicy` evaluates algorithm-specific requirements before submitting work to the executor.

The policy enforces:

- Register and shot-count limits.
- Exact hidden-string width for Bernstein-Vazirani.
- Valid marked-state indices for Grover.
- Supported oracle types for Deutsch-Jozsa.
- A valid phase and an extra target qubit for phase estimation.

This separates invalid requests from execution failures.

### Asynchronous execution

`ExperimentService` uses a bounded fixed-thread executor and returns `CompletableFuture<ExperimentResult>` values.

Each backend invocation creates a fresh state vector and random generator. This prevents concurrent requests from sharing mutable amplitude arrays.

The service shuts down its executor during resource cleanup and waits for active tasks before forcing shutdown.

### Measurement histograms

Measurement outcomes are accumulated in a `LinkedHashMap`. The map records the number of times each bit string was observed.

The backend distinguishes three types of result information:

- The measurement histogram contains observed outcomes.
- The interpretation describes the algorithm-level outcome.
- The success metric reports either a theoretical probability or an observed fraction, depending on the algorithm.

For Grover, the success metric is the theoretical total probability of the marked states after amplification. For Bernstein-Vazirani, it is the observed fraction of shots equal to the expected secret.

## PostgreSQL Experiment Model

The SQL file stores quantum experiment configurations and execution records as relational data.

It does not perform quantum simulation inside the database. Algorithm execution belongs to the application or quantum backend. PostgreSQL provides configuration integrity, lifecycle enforcement, measurement storage, metrics, and reporting.

### Relational structure

The core relationships are:

    algorithm
       |
       | 1-to-many
       v
    experiment -------- quantum_backend
       |
       +---- circuit_gate
       |
       +---- measurement
       |
       +---- experiment_metric
       |
       +---- experiment_event

An experiment references one algorithm and one execution backend. It can contain multiple circuit-gate records, measurement records, metrics, and lifecycle events.

### Algorithm catalog

The `algorithm` table records the algorithm code, display name, description, and computational model.

The computational model differentiates:

- `ORACLE`: promise problems and hidden-function oracles.
- `SEARCH`: marked-state search.
- `PHASE_ESTIMATION`: eigenphase estimation.

The catalog prevents experiment records from referring to arbitrary algorithm names.

### Backend capacity

The `quantum_backend` table records the backend type, available qubit capacity, and active status.

Backend types distinguish state-vector simulators, gate simulators, and quantum hardware. The capacity trigger rejects an experiment whose effective qubit requirement exceeds the selected backend's capacity.

Phase estimation requires one extra target qubit beyond the counting register. The validation trigger accounts for that additional qubit.

### Experiment configuration

The `experiment` table stores the main execution request:

- Algorithm.
- Backend.
- Requesting user or service.
- Qubit count.
- Number of shots.
- Algorithm-specific parameters.
- Random seed.
- Execution state.
- Timing and error information.

The `parameters` column uses `jsonb` because the algorithms require different input structures. The trigger validates the fields that are specific to each algorithm.

| Algorithm | Required parameters |
|---|---|
| Deutsch-Jozsa | `oracle` |
| Bernstein-Vazirani | `secret` |
| Grover | `marked_states` |
| Phase Estimation | `phase` |

The JSONB representation preserves a common experiment table without forcing unrelated algorithm parameters into separate nullable columns.

### Circuit gates

The `circuit_gate` table stores ordered gate records.

Each row identifies:

- The experiment.
- The gate's sequence number.
- Gate name.
- Target qubit.
- Optional control qubit.
- Optional phase angle.

The composite primary key prevents duplicate sequence numbers within one experiment.

The register-position trigger verifies that target and control qubits fit the experiment's effective register. The table is an execution record, not a complete universal quantum-circuit intermediate representation.

### Measurement records

The `measurement` table stores shot-level outcomes.

Each measurement includes:

- Experiment identifier.
- Shot number.
- Measured bit string.
- Probability associated with the recorded outcome.
- Measurement timestamp.

The database checks that the bit string contains only binary digits and has the correct register width. Measurements are accepted only while the experiment is in the `RUNNING` state.

The unique constraint on `(experiment_id, shot_number)` prevents duplicate records for the same shot.

### Metrics

The `experiment_metric` table stores numerical results independently of individual measurements.

This permits different algorithms to record different metrics without repeatedly altering the experiment table.

Examples include:

- Success probability.
- Secret recovery rate.
- Grover iteration count.
- Number of marked states.
- Absolute phase-estimation error.

Metric names are unique within an experiment. Their values use PostgreSQL `numeric` to preserve decimal precision for stored measurements and reports.

### Lifecycle and audit events

Experiment state transitions are restricted to:

    QUEUED
       |
       +------> RUNNING ------> SUCCEEDED
       |             |
       |             +--------> FAILED
       |             |
       +----------------------> CANCELLED
                     |
                     +--------> CANCELLED

The implementation allows a queued experiment to start or be cancelled. A running experiment can succeed, fail, or be cancelled. Terminal states cannot be reopened.

The transition trigger automatically records start and completion timestamps. A failed experiment must include an error message.

The `experiment_event` table records state changes separately from the current experiment state. This maintains a historical view of execution without requiring consumers to reconstruct transitions from the current row.

### Transactional finalization

The `finalize_experiment` procedure accepts a JSON object of numeric metrics.

It performs the following operations within the caller's transaction:

1. Locks the experiment row.
2. Checks that the experiment exists and is `RUNNING`.
3. Validates that every metric has a numeric value.
4. Inserts or updates experiment metrics.
5. Transitions the experiment to `SUCCEEDED`.

The row lock prevents two concurrent finalization operations from successfully finalizing the same running experiment.

A failure during metric insertion prevents the procedure's transaction from committing a successful state transition.

### Views and operational queries

Three views provide common reporting perspectives.

| View | Purpose |
|---|---|
| `v_experiment_summary` | Combines algorithm, backend, configuration, lifecycle, and timing information |
| `v_algorithm_performance` | Aggregates successful and failed experiments and selected metrics |
| `v_execution_eligibility` | Evaluates whether queued experiments are eligible for scheduling |

Execution eligibility is not a measure of quantum correctness. It identifies whether an experiment is queued, whether its backend is active, and whether the backend has sufficient capacity.

Indexes support the main access patterns:

- Filtering experiment records by status and creation time.
- Retrieving experiment history by algorithm.
- Searching JSONB experiment parameters.
- Retrieving measurements by experiment and bit string.
- Reading lifecycle events in chronological order.

The schema uses indexes where the sample reporting and retrieval queries have clear filtering or ordering requirements.

## Running the Implementations

### Python

Save the Python block as `quantum_algorithms.py` and run:

`python quantum_algorithms.py`

The program executes built-in assertions before printing JSON results for all four algorithms.

### JavaScript

Save the JavaScript block as `quantum_algorithms.js` and run:

`node quantum_algorithms.js`

The program submits three experiments through the event-driven runner and prints their result histograms.

### C++17

Save the C++ block as `quantum_algorithms.cpp`.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic quantum_algorithms.cpp -o quantum_algorithms`

Run:

`./quantum_algorithms`

The executable checks the Deutsch-Jozsa, Bernstein-Vazirani, and Grover outcomes before printing their results.

### Java 17

Save the Java block as `QuantumWorkbench.java`.

Compile:

`javac --release 17 QuantumWorkbench.java`

Run:

`java QuantumWorkbench`

The Java service executes four experiments through its asynchronous backend interface and validates an intentionally invalid request.

### PostgreSQL

Save the SQL block as `quantum_lab.sql` and execute it against a PostgreSQL database:

`psql -v ON_ERROR_STOP=1 -f quantum_lab.sql`

The script creates the schema, inserts sample experiments, executes lifecycle transitions, records sample measurements, finalizes successful experiments, demonstrates validation failures, and runs reporting queries.

The script drops and recreates the `quantum_lab` schema. Existing objects in that schema are therefore removed when it is executed.

## Validation and Failure Behavior

The implementations distinguish configuration failures from measurement outcomes.

| Failure condition | Handling |
|---|---|
| Invalid qubit count | Rejected before state-vector allocation |
| Invalid bit string | Rejected by input validation |
| Missing Grover targets | Rejected before circuit execution |
| Out-of-range marked state | Rejected by the algorithm or database trigger |
| Invalid phase | Rejected by phase-estimation validation |
| Invalid measurement register | Rejected before sampling |
| Invalid backend capacity | Rejected during experiment configuration |
| Measurement recorded before execution | Rejected by database trigger |
| Invalid status transition | Rejected by lifecycle trigger |
| Failed execution without an error | Rejected by database constraints and trigger |

A measurement that produces an unexpected result is not necessarily a software failure. Quantum measurement is probabilistic, and an algorithm can have a nonzero probability of producing an undesired outcome.

For this reason, the project reports probability and measured frequency separately where applicable.

## Computational Limits and Design Trade-Offs

### Dense state-vector simulation

A state vector requires \(2^n\) complex amplitudes for an \(n\)-qubit system.

The memory cost is exponential. With double-precision real and imaginary components, the amplitude data alone requires approximately:

\[
16 \times 2^n \text{ bytes}
\]

Actual memory consumption is higher where a language uses complex-number objects or additional container overhead.

The implementations impose register limits to prevent unrestricted memory allocation.

### Simulation versus quantum hardware

A state-vector simulator calculates ideal quantum amplitudes in classical memory. It does not reproduce all physical hardware effects.

The project does not model:

- Gate errors.
- Decoherence.
- Readout errors.
- Crosstalk.
- Connectivity restrictions.
- Hardware calibration drift.
- Noise channels.
- Error-correction procedures.
- Real quantum-device queueing or execution latency.

A probability of one in the simulator does not imply that a physical quantum processor will return the same result in every shot.

### Oracle assumptions

Deutsch-Jozsa, Bernstein-Vazirani, and Grover depend on oracle access.

The implementations encode the oracle directly as a predicate over computational-basis indices. They do not construct a complete reversible Boolean circuit with an explicit output ancilla for every oracle.

This phase-oracle representation is appropriate for the algorithms demonstrated here, where phase kickback gives the required behavior.

### Complexity distinction

A state-vector simulator's classical computation cost should not be confused with the theoretical query complexity of a quantum algorithm.

For example, Grover's algorithm uses approximately \(O(\sqrt{N/M})\) oracle iterations for \(M\) marked states in a search space of size \(N\). A dense classical state-vector simulator still processes arrays whose size is proportional to \(N\) during each iteration.

The simulation verifies mathematical behavior on small registers. It does not provide the same resource advantage as executing a quantum circuit on suitable physical hardware.
