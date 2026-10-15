# Multi-Qubit Quantum Circuit Programming

## Project scope

This project develops a small quantum circuit simulator for studying how several qubits interact through unitary gates, controlled operations, entanglement, and measurement. The implementations use a state-vector representation and make qubit ordering explicit so that the mathematical behavior can be checked against executable results.

The project covers circuit construction, gate application, controlled gates, parameterized rotations, measurement statistics, multi-qubit entanglement, and execution validation. It also illustrates the differences between an in-memory simulator and a persistent experiment-management system.

The implementations use only standard language libraries. They are educational simulators, not replacements for hardware-calibrated quantum execution systems.

## Quantum state representation

A pure state of \(n\) qubits is represented as

\[
|\psi\rangle=\sum_{x=0}^{2^n-1}\alpha_x|x\rangle,
\]

where each amplitude \(\alpha_x\) is a complex number and the probabilities satisfy

\[
\sum_{x=0}^{2^n-1}|\alpha_x|^2=1.
\]

For two qubits, the computational basis is \(|00\rangle\), \(|01\rangle\), \(|10\rangle\), and \(|11\rangle\). The simulator stores these amplitudes in an array of length four. For three qubits, the array contains eight amplitudes.

The programs consistently treat qubit zero as the most significant bit in displayed bitstrings. Consequently, qubit zero corresponds to the leftmost character of an output such as `101`. The convention is important because controlled gates, state preparation, measurement, and printed results must all agree on the relationship between qubit indices and array positions.

A normalized state vector contains the complete information needed to calculate measurement probabilities for a pure-state circuit. The vector alone does not model hardware noise, gate calibration errors, decoherence, or the general mixed states that arise when a system interacts with an environment.

## Gates and circuit composition

### Single-qubit operations

A single-qubit gate is a \(2\times2\) unitary matrix. If the target qubit has amplitudes \(a_0\) and \(a_1\), applying a gate \(U\) transforms them into

\[
\begin{pmatrix}b_0\\b_1\end{pmatrix}
=
U\begin{pmatrix}a_0\\a_1\end{pmatrix}.
\]

The implementations provide Hadamard, Pauli-X, and Pauli-Z gates, together with parameterized rotation gates where supported. The Hadamard gate creates an equal superposition from \(|0\rangle\), while the Pauli-X gate exchanges the basis states. Pauli-Z changes the phase of the \(|1\rangle\) component without changing its measurement probability in the computational basis.

The rotation gates introduce continuous parameters. For example, the Y-axis rotation is

\[
R_y(\theta)=
\begin{pmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{pmatrix}.
\]

These rotations are useful for preparing states with adjustable measurement probabilities and for constructing parameterized quantum circuits.

### Controlled operations

A controlled-X gate, commonly called CNOT or CX, applies an X gate to its target only when its control qubit is \(|1\rangle\). The multi-controlled-X gate extends the condition: every listed control must be set to one before the target is flipped.

The state-vector implementations evaluate this condition using bit masks. For each basis index, the executor checks whether the target bit is zero, whether all control bits satisfy the required condition, and which paired index differs only at the target bit. Each pair is transformed once. This avoids constructing a complete \(2^n\times2^n\) matrix for every gate.

The C++ and Java programs use this mechanism to build coherent circuits with explicit operation records. The Python implementation also exposes a circuit listing, while the JavaScript implementation emits events when gates are applied.

## Entanglement and multi-qubit circuits

A useful demonstration is the Bell-state preparation circuit:

\[
|00\rangle
\xrightarrow{H_0}
\frac{|00\rangle+|10\rangle}{\sqrt{2}}
\xrightarrow{CX_{0,1}}
\frac{|00\rangle+|11\rangle}{\sqrt{2}}.
\]

The final state has equal probabilities for `00` and `11`, with zero probability for `01` and `10`. Measuring one qubit determines the outcome of the other when both are measured in the computational basis. This correlation is a consequence of entanglement rather than two independent classical random choices.

The three-qubit GHZ state extends the same preparation principle:

\[
|\mathrm{GHZ}_3\rangle=
\frac{|000\rangle+|111\rangle}{\sqrt{2}}.
\]

A chain of controlled-X gates distributes the initial superposition across the remaining qubits. The four-qubit Python and C++ examples demonstrate the same pattern at a larger circuit width.

Entanglement does not mean that every pair of measurements always produces identical results. The observed correlation depends on the prepared state and the measurement basis.

## Python implementation

The Python program provides a complete state-vector execution path without third-party packages.

`QuantumCircuit` owns the qubit count, amplitude vector, operation history, and seeded pseudorandom generator. Its gate methods validate target and control indices before transforming the state. Gate matrices are checked for unitarity, and the simulator checks normalization after each operation.

The `basis_probabilities` method returns only outcomes with non-negligible probability. `run_shots` samples the current probability distribution repeatedly without collapsing the stored state, modeling independent repetitions of the same circuit. By contrast, `measure_qubit` performs a projective measurement, removes incompatible amplitudes, and renormalizes the remaining state.

The script includes a Bell-state test, a GHZ-state preparation, rotation-gate evaluation, a Deutsch-Jozsa example, and a three-qubit quantum teleportation demonstration. These exercises cover both circuit composition and the relationship between state amplitudes, classical outcomes, and conditional operations.

The teleportation demonstration prepares an entangled resource, performs a Bell-basis transformation, records two classical measurement outcomes, and applies corrections to Bob's qubit. It then extracts the corrected one-qubit state and evaluates its fidelity against the input state. The ideal noiseless simulation should yield fidelity close to one.

The implementation limits circuit width because state-vector storage grows exponentially. Even if a gate acts on just one qubit, the executor must process amplitude pairs across the entire vector. A simulator that supports more qubits therefore needs a different computational strategy or significantly more memory.

## JavaScript implementation

The JavaScript program emphasizes event-driven circuit execution and immutable operation descriptions.

Complex amplitudes are represented as objects with real and imaginary components. The simulator provides complex arithmetic, normalization, unitary validation, and gate execution without requiring an external numerical package. `QuantumCircuit` stores operations as frozen objects, while its event listeners receive structured notifications for gate application, measurement, and completed shot batches.

The `on` method returns an unsubscribe function. This supports the lifecycle of an audit listener and avoids retaining callbacks after they are no longer required. The Bell-state example records gate events and shot completion in an audit log.

The seeded linear congruential generator makes repeated demonstrations reproducible. It is suitable only for deterministic educational sampling and must not be used for cryptographic randomness or security-sensitive quantum protocols.

The multi-controlled operation example demonstrates how the same controlled-gate condition can be generalized to several controls. The parameterized circuit demonstrates how a rotation angle changes the distribution before and after entanglement. Validation rejects invalid qubit indices, duplicate controls, non-unitary matrices, and unreasonable shot counts.

## C++ case study

The C++ program models a research team's circuit-validation workflow. A circuit is constructed from a qubit count, records gate operations, executes validated unitary transformations, and produces measurement statistics.

`QuantumCircuit` owns a `std::vector<std::complex<double>>` state vector, a collection of operation records, and a seeded random engine. The use of `std::complex<double>` keeps complex arithmetic explicit while relying on the standard library for addition, multiplication, conjugation, and squared magnitude.

The gate executor creates a working state vector before applying each operation. It pairs basis indices that differ at the target bit and skips pairs that do not satisfy the control condition. This approach avoids in-place updates corrupting the second amplitude of a pair before it has been read.

The Bell-state validation checks the exact probability distribution rather than relying on a finite random sample. The shot simulation is then used to estimate observed frequencies. A second circuit constructs a four-qubit GHZ state, and a parameterized circuit demonstrates chained entanglement.

Invalid control-target combinations are rejected before execution. The program also reports the number of amplitudes and approximate amplitude storage, connecting circuit width to resource consumption.

For \(n\) qubits, state-vector storage requires \(2^n\) complex amplitudes. A direct single-qubit gate application takes \(O(2^n)\) time, while a full state-vector copy also takes \(O(2^n)\) time and memory. Repeated gate execution can therefore become expensive even when the logical circuit contains relatively few operations.

## Java implementation

The Java program separates experiment policy, gate operations, execution, and measurement sampling.

`GateKind` distinguishes gate families, while `ExperimentStatus` records whether an experiment is still a draft, has passed validation, has executed, or has been rejected. The `GateOperation` record provides an immutable description of the gate type, target, controls, and rotation angle.

`CircuitPolicy` evaluates the maximum allowed qubit count, operation budget, and requirement for at least one controlled operation. The circuit must pass this policy before execution. After execution, gate modification is prohibited, preserving the relationship between the validated operation sequence and the resulting state vector.

The policy model represents experiment-level requirements, not quantum mechanics itself. A circuit may be mathematically valid and still fail a laboratory policy because it exceeds a resource budget or does not satisfy the experiment's structural requirements.

Validation exceptions set the experiment status to rejected. Execution checks the validated state before applying operations, and shot sampling is permitted only after execution. This makes invalid lifecycle transitions explicit rather than relying on the order of print statements.

The implementation uses an unmodifiable view of the operation list and immutable records to reduce accidental mutation. It remains an in-memory teaching model; a production experiment service would also need persistent provenance, authorization, backend job management, concurrency control, and recovery after failed execution.

## SQL experiment registry

The PostgreSQL script models the persistence and audit layer around quantum circuit execution. It stores researchers, experiments, gate operations, control-qubit relationships, validation policies, validation results, execution runs, and measurement counts.

The schema uses foreign keys to connect operations to experiments, controls to operations, runs to experiments, and results to runs. Unique constraints prevent duplicate sequence numbers within an experiment and duplicate measurement bitstrings within a run. Check constraints enforce valid qubit ranges, positive shot counts, rotation-angle requirements, and valid bitstring syntax.

The `operation_controls` table represents controls as a separate relation because a gate can have multiple control qubits. The database triggers validate that target and control indices fit the circuit width and that a control does not equal its target. A controlled operation is also checked during experiment validation to ensure it has at least one associated control.

The `validate_experiment` function evaluates the experiment against a named policy, records the findings as JSONB, and changes the experiment status. The execution trigger requires a passing validation record before a run can be created. Measurement-result validation checks that the bitstring width matches the experiment and that accumulated counts do not exceed the requested shot count.

Indexes support common access patterns: listing experiments by owner and status, reading gate operations in circuit order, retrieving recent validation records, and finding queued or running jobs. The inventory view combines experiment metadata with operation counts and validation information, while the measurement summary compares recorded results with requested shots.

The example data includes Bell-state and GHZ experiments, a successful validation workflow, a completed execution with measurement counts, and a failed backend submission. An isolated exception block demonstrates how invalid target indices are rejected without aborting the complete example transaction.

The registry does not calculate quantum amplitudes. It records circuit structure, policy outcomes, execution metadata, and results produced by an execution engine. Keeping simulation separate from persistent governance makes the responsibilities of the database explicit.

## Measurement and statistical interpretation

For a state vector, the probability of a computational-basis outcome \(x\) is

\[
P(x)=|\alpha_x|^2.
\]

An exact state-vector distribution is different from a finite-shot histogram. If an ideal circuit gives probability \(1/2\) to two outcomes, a sample of one thousand shots will usually produce counts near five hundred for each outcome, but the counts need not be exactly equal.

Measurement also changes the state. When a single qubit is measured, the state collapses to the subspace consistent with the observed result. The simulator removes incompatible amplitudes and divides the remaining amplitudes by the square root of the selected outcome probability.

Repeated sampling in `run_shots` models independent preparations and measurements. It does not repeatedly measure and collapse the same stored state. This distinction is necessary when comparing simulator distributions with actual hardware shot results.

## Common implementation errors

- **Inconsistent qubit ordering:** A mismatch between bitstring display order and bit-mask construction can cause a gate to operate on the wrong logical qubit. The programs use the leftmost displayed bit for qubit zero.

- **Updating amplitudes in place:** A gate transforms two amplitudes simultaneously. Updating one amplitude before reading the other can produce incorrect results. Each implementation preserves the original pair while calculating the transformed values.

- **Incorrect control conditions:** A multi-controlled gate must verify every control bit. Testing only one control can silently change the circuit's behavior.

- **Non-unitary gates:** A valid closed-system quantum gate preserves the norm of every state. The simulators reject matrices that do not satisfy the unitary condition.

- **Confusing probabilities and amplitudes:** Amplitudes are complex values; probabilities are their squared magnitudes. Relative phase can affect later interference even when it does not change the current computational-basis probabilities.

- **Ignoring measurement collapse:** The distribution of outcomes and the post-measurement state are different objects. A measurement method must update the state, while a repeated-shot method must model fresh preparations.

- **Trusting sample counts as exact probabilities:** Finite samples contain statistical variation. Exact probabilities should be inspected separately from observed counts.

- **Ignoring exponential memory growth:** A state vector requires \(2^n\) amplitudes. Raising the qubit limit without accounting for memory and execution time can cause resource exhaustion.

## Limitations and production considerations

These simulators model ideal pure-state circuits with exact unitary transformations, apart from floating-point rounding. They do not simulate gate noise, readout error, decoherence, device topology, compiler optimization, or hardware scheduling. Their random generators are designed for reproducible educational experiments rather than security-sensitive use.

The SQL registry validates structural and operational metadata, but it cannot prove that a submitted amplitude vector is physically correct. A real service should validate results against the trusted execution engine, bind every run to an immutable circuit version, record backend configuration, and retain enough provenance to reproduce a reported result.

Production systems should also account for concurrent updates, idempotent job submission, authorization boundaries, failed and retried jobs, cancellation, schema migrations, and resource quotas. Database constraints provide useful integrity guarantees, but they do not replace access control or application-level authorization.

The central architectural distinction is between circuit description, quantum execution, and experiment governance. Gate operations define the computation, the simulator transforms amplitudes and models measurement, and the registry preserves the policy decisions and execution evidence associated with each experiment.
