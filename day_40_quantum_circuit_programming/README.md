# Quantum Circuit Programming: Build and Simulate Circuits

## Purpose

This project develops a practical understanding of quantum circuit programming through gate composition, complex amplitudes, controlled operations, interference, entanglement, measurement, and statistical sampling.

The implementations use a state-vector simulator built with standard language features. They illustrate the mathematical behavior of ideal quantum circuits without requiring quantum hardware or third-party quantum SDKs.

The Python, JavaScript, C++, and Java programs each implement circuit operations and simulate their execution. The PostgreSQL script stores circuit definitions, gate sequences, simulation-run metadata, and measurement observations for analysis.

## Quantum circuit fundamentals

### Qubits and computational basis states

A classical bit holds either zero or one. A qubit can occupy a superposition of the computational basis states:

\[
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle
\]

The complex amplitudes satisfy the normalization condition:

\[
|\alpha|^2 + |\beta|^2 = 1
\]

The squared magnitude of each amplitude determines the probability of measuring the corresponding basis state.

For a circuit containing \(n\) qubits, the state vector contains \(2^n\) complex amplitudes. A two-qubit state can be represented as:

\[
|\psi\rangle =
\alpha_{00}|00\rangle +
\alpha_{01}|01\rangle +
\alpha_{10}|10\rangle +
\alpha_{11}|11\rangle
\]

The programs use little-endian qubit indexing: qubit zero is the least significant bit of a basis-state index. Displayed bitstrings place qubit zero on the left, so their ordering is intentionally reversed relative to the conventional most-significant-bit-first binary representation.

### Quantum gates

A quantum gate transforms a state vector using a unitary matrix. For a single-qubit gate:

\[
\begin{bmatrix}
\alpha'\\
\beta'
\end{bmatrix}
=
U
\begin{bmatrix}
\alpha\\
\beta
\end{bmatrix}
\]

The matrix must satisfy \(U^\dagger U=I\), where \(U^\dagger\) is the conjugate transpose. Unitarity preserves state normalization and represents reversible evolution in an ideal closed quantum system.

The implementations include the following operations.

| Gate | Operation | Principal behavior |
|---|---|---|
| X | Pauli-X | Exchanges the amplitudes of zero and one |
| Y | Pauli-Y | Exchanges amplitudes while introducing phase factors |
| Z | Pauli-Z | Reverses the phase of the one component |
| H | Hadamard | Creates or recombines equal-amplitude superpositions |
| S and T | Phase gates | Apply fixed relative phase shifts |
| RX, RY, RZ | Rotation gates | Rotate a qubit state around a Bloch-sphere axis |
| CNOT | Controlled-X | Applies X to the target when the control is one |
| CZ | Controlled-Z | Applies a phase change when both qubits are one |
| SWAP | Exchange operation | Exchanges the states associated with two target qubits |

Gate composition follows circuit order. If \(U_1\) is followed by \(U_2\), the resulting state is \(U_2U_1|\psi\rangle\).

### Superposition, interference, and entanglement

Superposition refers to the coexistence of multiple probability amplitudes in a quantum state. Interference occurs when those amplitudes combine, allowing constructive or destructive interference to change measurement probabilities.

The sequence H-Z-H applied to an initial zero state produces one with certainty. The intermediate phase change reverses the relative sign of the amplitudes, and the final Hadamard recombines them.

Entanglement describes correlations that cannot be represented as a product of independent pure states for the individual qubits. A Bell-state circuit uses H followed by CNOT:

\[
|00\rangle \xrightarrow{H_0}
\frac{|00\rangle+|01\rangle}{\sqrt{2}}
\xrightarrow{\mathrm{CNOT}_{0,1}}
\frac{|00\rangle+|11\rangle}{\sqrt{2}}
\]

The ideal measurement probabilities are \(P(00)=P(11)=0.5\). The outcomes 01 and 10 have zero probability in the ideal state.

### Measurement and shot-based simulation

Measurement converts a quantum state into a classical outcome. A single measurement samples one basis state according to its probability and collapses the state vector to that outcome.

Shot-based simulation repeats sampling from the same ideal probability distribution. The resulting counts fluctuate because finite samples do not reproduce theoretical probabilities exactly.

For a Bernoulli outcome with probability \(p\), the approximate standard error of the measured frequency after \(N\) independent shots is:

\[
\sqrt{\frac{p(1-p)}{N}}
\]

Increasing the shot count generally reduces sampling uncertainty, but it does not eliminate hardware noise, model error, or simulator inaccuracies.

## Architecture and execution model

Each state-vector implementation uses the same essential mathematical model but adapts it to the strengths of its language.

A circuit begins in \(|0\rangle^{\otimes n}\), represented by an amplitude of one at basis index zero and zero amplitudes elsewhere. Operations are recorded in circuit order. During execution, each operation transforms the amplitudes associated with its target qubits.

Rather than constructing a dense \(2^n \times 2^n\) matrix for every gate, the simulators transform local amplitude blocks. This approach avoids unnecessary full-system matrix storage.

For an \(n\)-qubit state, storage is \(O(2^n)\). A gate acting on \(k\) qubits has a typical application cost proportional to \(O(2^n 2^k)\) in the implemented local-block approach. The exponential growth in state-vector size remains the principal scalability limitation.

## Python implementation

The Python program provides the broadest educational implementation.

`QuantumCircuit` stores the state vector, an ordered operation list, and a seeded random-number generator. Its gate methods append validated operations, while `run()` executes the recorded sequence.

The matrix-validation functions check that custom gates are unitary. Rotation constructors implement RX, RY, and RZ using their standard trigonometric and complex-exponential definitions. The controlled operations activate only when every control bit is one.

The `probabilities()` method converts amplitudes into nonzero basis-state probabilities. `sample()` returns shot counts, while `measure_all()` performs a single measurement and collapses the state. `expectation_z()` calculates the expectation value of the Pauli-Z observable for a selected qubit.

The Bell-state example validates entanglement-related measurement behavior. Rotation tests compare simulated probabilities against analytical values. The two-qubit Grover demonstration combines a phase oracle and diffusion operation to amplify the marked state's amplitude.

The tests also cover invalid control-target combinations, nonpositive shot counts, gate composition, and normalization-sensitive behavior.

The simulator limits its supported circuit size because its state vector grows exponentially. Its configured maximum is a resource guard, not a statement that all circuits at that size will run comfortably on every machine.

## JavaScript implementation

The JavaScript program makes complex arithmetic explicit through the `Complex` class. Each value supports addition, multiplication, conjugation, scaling, and squared magnitude.

`QuantumCircuit` records gate operations and applies them to a state vector. The deterministic pseudo-random generator makes repeated demonstrations reproducible for the same runtime and seed. The sampling method builds a measurement distribution from squared amplitudes and converts sampled indices into little-endian bitstrings.

The interference test checks that H-Z-H produces one with certainty. The Bell-pair example checks that only 00 and 11 are observed. The parameterized rotation test verifies the analytical probability:

\[
P(1)=\sin^2(\theta/2)
\]

The sampling-statistics example compares an empirical frequency against the theoretical value and a multiple of its estimated standard error.

These examples demonstrate the difference between deterministic state-vector evolution and probabilistic measurement output. The ideal state can be represented exactly within floating-point tolerance, while shot counts vary between finite sampling experiments.

## C++ case study

The C++ implementation is organized around `StateVectorSimulator`, which owns the qubit count, state vector, operation list, and random-number generator.

`Operation` captures the gate name, target qubits, control qubits, and matrix. `addGate()` validates target uniqueness, control-target separation, matrix dimensions, and unitarity before accepting an operation.

The simulator applies each local matrix to the relevant amplitude blocks. `execute()` then verifies that the resulting state remains normalized within a floating-point tolerance. `probabilities()` and `sample()` expose theoretical probabilities and empirical measurement counts.

The case study constructs a Bell state and a parameterized RY rotation. The rotation is checked against its expected probability of 0.25 for measuring one when the angle is \(\pi/3\).

`QuantumExperiment` also reports illustrative gate-error and readout-error events against sampled counts. This is deliberately a simplified diagnostic illustration, not a physical noise channel, density-matrix simulation, or calibrated hardware model.

The design separates circuit execution from experiment reporting. In a larger simulator, the same separation would support distinct backends, configurable noise models, measurement calibration, and experiment-level diagnostics without embedding those concerns into gate-matrix operations.

## Java implementation

The Java program uses explicit domain types for quantum operations. `GateType` enumerates supported operation categories, and the immutable `GateOperation` record captures targets, controls, and a copied matrix.

The `Circuit` class owns circuit state and execution behavior. Its `add()` method validates operation structure, and `execute()` checks the normalization invariant after applying the operation sequence.

`ExperimentPolicy` represents operational restrictions such as maximum qubit count and maximum shot count. It validates a circuit request before execution, separating experiment admission rules from quantum-state mathematics.

The program runs Bell-state, rotation, and interference checks. Its seeded `Random` instance makes examples repeatable, while measurement sampling uses a cumulative probability distribution.

This architecture provides a foundation for an enterprise experiment service in which circuit validation, execution, resource limits, result collection, and policy enforcement remain distinct responsibilities. The implementation remains an ideal simulator and does not model hardware calibration or decoherence.

## PostgreSQL circuit registry

The SQL script defines a relational model for storing quantum circuit definitions and experiment results.

### Circuit and operation tables

`circuits` stores the circuit identity, qubit count, description, and creation time. `gate_operations` stores the ordered operations belonging to each circuit.

The foreign key ensures that an operation refers to an existing circuit. A uniqueness constraint on `(circuit_id, sequence_no)` prevents duplicate operation positions within a circuit. The gate enum restricts operation names to the supported set.

Check constraints validate the required shape of single-qubit gates, rotations, controlled gates, and SWAP operations. A trigger checks qubit indices against the circuit's declared size, since an ordinary SQL CHECK constraint cannot inspect another table.

### Simulation runs and measurement results

`simulation_runs` records execution state, requested shots, simulator identity, seed, timestamps, and any error message. Its check constraint links each status to the required timestamps and error information.

The transition trigger prevents invalid status changes, such as restarting a completed run. It fills execution timestamps when a run enters the running or terminal state.

`measurement_results` stores a bitstring and the number of observed shots for each outcome. Its primary key prevents duplicate result rows for the same outcome in one run.

The script includes illustrative observations for Bell-state, rotation, and interference circuits. These rows demonstrate database storage and analysis; PostgreSQL does not execute the quantum gate sequence or generate the observations.

### Queries and integrity checks

The circuit-inspection query retrieves operations in execution order. The measurement query calculates empirical outcome frequencies. A shot-accounting query checks whether recorded counts equal the requested number of shots.

A separate query detects bitstrings whose lengths disagree with the circuit's qubit count. This is a cross-table rule, so it is evaluated explicitly rather than incorrectly represented as a simple row-level constraint.

Indexes support ordered circuit-operation retrieval, filtering by run status and creation time, and searches for particular measurement bitstrings.

## Design limitations and numerical considerations

### State-vector scaling

The state vector requires exponentially increasing memory. A system with \(n\) qubits requires \(2^n\) complex amplitudes. The practical limit depends on memory capacity, numerical precision, gate structure, and execution overhead.

The implementations impose a qubit limit to avoid unbounded allocations. That limit does not guarantee that every permitted circuit will fit in available memory.

### Floating-point precision

Gate matrices and state amplitudes use floating-point arithmetic. Small deviations from ideal probabilities can occur because of rounding. Tests should use numerical tolerances rather than exact floating-point equality.

Unitarity checks reduce the risk of accepting invalid custom gates, but they do not prove that a circuit represents the intended physical operation.

### Sampling versus state evolution

Applying ideal unitary gates is deterministic. Measurement sampling is probabilistic. A circuit may therefore have exactly calculable ideal probabilities but different finite-shot histograms across experiments.

A seeded pseudorandom generator makes a simulation repeatable within the relevant implementation and runtime. It is not a source of cryptographic randomness and should not be treated as a physical quantum random-number generator.

### Ideal circuits versus quantum hardware

The state-vector simulators do not automatically include decoherence, gate infidelity, readout errors, crosstalk, finite-temperature effects, or hardware connectivity restrictions.

A realistic hardware workflow must account for device-specific gate sets, qubit connectivity, transpilation, calibration data, noise, and measurement interpretation. Those features require additional modeling or a hardware execution backend.

### Measurement and circuit lifecycle

The Python and JavaScript examples distinguish single-measurement collapse from repeated shot sampling. The Java implementation similarly models a collapsed circuit as no longer modifiable. Circuit definitions should be treated as immutable experiment inputs once execution begins.

The C++ demonstration concentrates on operation execution and sampling. Its operation-recording interface does not implement a complete lifecycle state machine, so callers should manage circuit reuse carefully.

## Practical applications

Quantum circuit programming is useful for studying quantum algorithms, validating gate sequences, testing small circuits, analyzing interference, and understanding measurement statistics.

The Bell-state circuit demonstrates controlled operations and entanglement. Parameterized rotations illustrate how continuous circuit parameters affect measurement probabilities. The Grover example shows how phase marking and amplitude amplification can concentrate probability on a selected state.

The relational schema supports circuit registries, experiment tracking, run-state auditing, and result analysis. It complements simulation software by providing durable records and integrity checks rather than attempting to replace the quantum execution engine.
