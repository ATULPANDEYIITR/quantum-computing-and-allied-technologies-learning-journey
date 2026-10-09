# Qiskit Fundamentals: Installation and First Circuit

## Scope

Qiskit is an open-source software development kit for constructing, transforming, and executing quantum circuits. A first circuit introduces the relationship between quantum bits, quantum gates, quantum states, measurement, and classical results.

The examples in this collection cover three progressively more informative experiments:

- A Pauli-X gate flips the computational-basis state from \(|0\rangle\) to \(|1\rangle\).
- A Hadamard gate prepares an equal superposition whose computational-basis measurements approach a 50% distribution.
- A Hadamard gate followed by a controlled-X gate prepares a two-qubit Bell state with correlated measurement outcomes.

The Python implementation uses Qiskit and Qiskit Aer when available. The JavaScript, C++, and Java implementations provide independent educational simulators using their respective standard libraries. The PostgreSQL script records circuit definitions, backend metadata, execution records, and measured outcome counts.

These implementations do not claim that the non-Python programs are Qiskit SDK bindings or that classical simulation performs quantum computation on physical hardware.

## Installation and environment preparation

Use a supported Python installation and create a dedicated virtual environment. Keeping quantum-computing packages separate from system packages reduces dependency conflicts.

On Windows PowerShell:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install qiskit qiskit-aer

On Linux or macOS:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install qiskit qiskit-aer

Confirm that the packages are importable:

    python -c "import qiskit; print(qiskit.__version__)"
    python -c "from qiskit_aer import AerSimulator; print('Aer available')"

The `qiskit` package provides circuit construction, quantum information utilities, and execution interfaces. `qiskit-aer` supplies local simulators, including shot-based simulation. They are separate packages and can have different version numbers.

A successful installation does not imply access to a quantum processor. Local simulation and remote hardware execution have different operational requirements, noise characteristics, costs, and availability.

## Quantum bits, states, and gates

A classical bit holds either zero or one. A qubit is represented mathematically by a normalized state

\[
|\psi\rangle = \alpha |0\rangle + \beta |1\rangle,
\]

where \(\alpha\) and \(\beta\) are complex amplitudes and

\[
|\alpha|^2 + |\beta|^2 = 1.
\]

The squared magnitudes give the probabilities of computational-basis measurement outcomes. The amplitudes themselves contain phase information that can affect later gates and interference.

The computational basis for one qubit is \(|0\rangle\) and \(|1\rangle\). In a statevector representation, these basis states correspond to the vectors \((1,0)\) and \((0,1)\).

The Pauli-X gate swaps the amplitudes associated with these basis states:

\[
X =
\begin{pmatrix}
0 & 1\\
1 & 0
\end{pmatrix}.
\]

The Hadamard gate creates superposition from a computational-basis state:

\[
H = \frac{1}{\sqrt{2}}
\begin{pmatrix}
1 & 1\\
1 & -1
\end{pmatrix}.
\]

Applying the Hadamard gate to \(|0\rangle\) gives

\[
H|0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}.
\]

Both measurement outcomes have probability \(1/2\). This does not mean that each individual measurement returns a fractional bit. Each measurement returns a classical outcome, while repeated measurements estimate the underlying distribution.

## Constructing the first Qiskit circuit

The Python implementation creates a one-qubit circuit with one classical bit:

`QuantumCircuit(1, 1)`

It applies a Hadamard gate and then measures the qubit into the classical bit. The circuit is deliberately small so that the gate operation, measurement instruction, and execution result can be inspected separately.

The relevant operations are:

- `h(0)` applies the Hadamard gate to qubit zero.
- `measure(0, 0)` maps qubit zero's measurement result into classical bit zero.
- `draw(output="text")` produces a text representation of the circuit.
- `AerSimulator()` constructs a local simulator backend.
- `run(..., shots=4096)` requests repeated executions to collect an empirical distribution.

The `shots` parameter specifies how many measurement samples are collected. Increasing the shot count generally reduces the relative sampling uncertainty, but it does not remove hardware noise or systematic errors.

The Python script also inspects the statevector of an unmeasured circuit. Measurement instructions are excluded from this state preparation because the statevector describes the quantum state before measurement. The program uses `Statevector.from_instruction` to inspect amplitudes and `probabilities_dict()` to calculate computational-basis probabilities.

## Measurement, sampling, and reproducibility

A circuit's theoretical probabilities and its observed counts are distinct quantities.

For an ideal Hadamard experiment,

\[
P(0) = P(1) = \frac{1}{2}.
\]

For \(N\) independent measurements, the count of outcome one follows a binomial distribution with success probability \(1/2\). Its estimated probability fluctuates around the theoretical value. The standard deviation of the estimated probability is

\[
\sigma_{\hat p} = \sqrt{\frac{p(1-p)}{N}}.
\]

At 4,096 shots and \(p=1/2\), the standard deviation is approximately 0.0078. A small difference between the two observed counts is therefore expected and is not evidence that the circuit is incorrect.

The Python and C++ examples use seeded simulation where the API supports it. The Java and JavaScript examples use seeded pseudorandom generators in their educational simulators. A seed helps reproduce a simulated sample under the same implementation and runtime assumptions. It does not make actual quantum hardware measurements deterministic.

The Python implementation checks that the measured probability remains within a configured tolerance. This is a basic regression test rather than a formal statistical certification procedure.

## Two-qubit circuits and entanglement

A two-qubit state uses four computational-basis amplitudes:

\[
|\psi\rangle =
\alpha_{00}|00\rangle +
\alpha_{01}|01\rangle +
\alpha_{10}|10\rangle +
\alpha_{11}|11\rangle.
\]

The Bell-state circuit applies a Hadamard gate to qubit zero, followed by a controlled-X operation whose control is qubit zero and whose target is qubit one.

The controlled-X gate flips its target only when the control is one. The resulting ideal state is

\[
|\Phi^+\rangle =
\frac{|00\rangle + |11\rangle}{\sqrt{2}}.
\]

A computational-basis measurement therefore permits only `00` and `11`. The outcomes are correlated, even though neither individual qubit has a definite computational-basis value before measurement.

Qiskit uses qubit zero as the least-significant bit in its statevector indexing convention. Classical bit strings displayed by Qiskit normally place the highest-index bit on the left. This convention matters when comparing array indices, circuit diagrams, and displayed measurement counts.

The Bell-state checks in the implementations validate the support of the observed distribution. A simulator using exact ideal gates should never produce `01` or `10` for this circuit. On real hardware, readout and gate errors can make these outcomes appear.

## Python implementation

The Python script is the primary Qiskit workflow.

Its installation check uses package metadata and imports to distinguish a missing Qiskit installation from a missing Aer simulator. If Qiskit is absent, the script reports the installation command and runs a small standard-library simulator.

The simulator uses a complex-valued statevector and applies one-qubit matrices by pairing basis indices that differ at the target bit. Its controlled-X operation permutes amplitudes according to the control bit. The measurement routine converts squared amplitude magnitudes into cumulative probabilities and samples from that distribution.

The implementation also validates shot counts, statevector dimensions, state normalization, and controlled-X qubit indices. These checks catch common errors before they contaminate the measured distribution.

The fallback is useful for understanding statevector arithmetic, but it is not a replacement for Qiskit's circuit compiler, backend interface, noise models, transpilation, or hardware execution facilities.

## JavaScript implementation

The JavaScript file models a circuit as a sequence of gate-operation objects. Its `QuantumCircuitModel` validates qubit indices and prevents a controlled-X operation from using the same qubit as both control and target.

Complex amplitudes are represented as objects containing real and imaginary components. Gate methods transform these amplitudes, while the measurement function converts the statevector into a sampled outcome distribution.

The `ExperimentRunner` demonstrates an event-driven experiment lifecycle. It emits start, completion, and failure events and records an event identifier and timestamp for each event. Its asynchronous boundary models an asynchronous application workflow, not a quantum processor call.

The program is useful for understanding how a quantum experiment could be represented in a JavaScript application that manages circuit descriptions, experiment records, and results. It does not import the Python Qiskit package or execute circuits through a Qiskit backend.

## C++ case study

The C++ program models a circuit-validation engine for a quantum software team.

Its `Circuit` class stores gate operations and applies them to a statevector of complex amplitudes. The implementation uses bit masks to identify computational-basis indices affected by each gate.

The Hadamard operation combines amplitude pairs with opposite signs for the target-one component. The Pauli-X operation swaps amplitude pairs. The controlled-X operation swaps target pairs only for basis indices whose control bit is set.

The measurement engine uses cumulative probabilities and a seeded pseudorandom generator. It validates normalization before sampling, counts observed bit strings, and checks both the approximate Hadamard distribution and the Bell-state outcome support.

The statevector representation requires \(2^n\) complex amplitudes for \(n\) qubits. Consequently, memory and computation grow exponentially with qubit count. The program limits circuit width to reduce the risk of unreasonable allocations, although the actual practical limit depends on available memory and execution conditions.

The C++ program demonstrates the mathematics and validation structure independently of Qiskit. It does not implement Qiskit's transpiler, noise simulation, backend scheduling, or remote execution protocol.

## Java enterprise implementation

The Java program separates circuit definition from experiment execution.

The `Operation` record represents an immutable gate instruction and validates the basic controlled-X constraint. The `Circuit` class owns the operation sequence, checks qubit bounds, applies the gate transformations, and returns measurement probabilities after checking state normalization.

`CircuitValidationService` handles shot validation, seeded sampling, and result construction. The immutable `MeasurementResult` record verifies that recorded counts sum to the requested number of shots and that counts are nonnegative.

This separation makes the code suitable as a small example of an experiment-validation service. Circuit construction rules are not duplicated inside the measurement loop, and invalid inputs fail through explicit exceptions.

The implementation is a simplified simulator rather than a production quantum service. A production system would also need backend capability validation, resource quotas, job tracking, serialization, execution timeouts, provider-specific errors, and noise-aware acceptance criteria.

## PostgreSQL data model

The SQL script records the structure and execution history of the example experiments.

| Table | Purpose |
|---|---|
| `simulation_backends` | Identifies the simulator or hardware target and records its declared capabilities. |
| `quantum_circuits` | Stores circuit names, descriptions, widths, and experiment purpose. |
| `circuit_operations` | Stores ordered gate operations, including controlled-X control and target indices. |
| `experiment_runs` | Records the circuit, backend, shot count, random seed, status, and execution timestamps. |
| `measurement_counts` | Stores the observed count for each classical bit string in a run. |

The primary keys prevent duplicate operation positions and duplicate outcomes within a run. Foreign keys prevent operations and measurement counts from referencing nonexistent parent records. Check constraints restrict supported gate names, valid circuit widths, positive shot counts, and consistent failure metadata.

The operation table uses a composite primary key consisting of circuit ID and operation index. This represents gate order explicitly. A controlled-X operation requires a control index distinct from the target index, while a one-qubit gate must not specify a control index.

The experiment-run indexes support common queries that filter by run status, inspect recent runs for a circuit, or retrieve a run's outcomes. The summary view joins circuit and backend metadata with observed counts and calculates each outcome's empirical probability.

The validation queries identify incomplete measurement accounting and impossible Bell-state outcomes. These queries are diagnostics rather than automatic repairs.

A simple `CHECK` constraint cannot verify that the sum of child measurement counts equals the shot count recorded in another row. That invariant spans multiple rows and requires transactional application logic, a carefully designed deferred constraint trigger, or a controlled database write procedure. The script explicitly queries for discrepancies instead of incorrectly claiming that its row-level constraints guarantee aggregate consistency.

The sample records are illustrative data for testing the schema. They are not presented as output captured from a live Qiskit execution.

## Implementation differences

| Implementation | Primary technical emphasis | Execution model |
|---|---|---|
| Python | Qiskit circuit construction, state inspection, and Aer execution | Real Qiskit APIs when dependencies are installed |
| JavaScript | Event-driven circuit representation and experiment processing | Standalone educational statevector simulator |
| C++ | Bit-mask transformations, amplitude permutations, and distribution validation | Standalone C++17 simulator |
| Java | Immutable operation records, domain validation, and service separation | Standalone Java 17 simulator |
| PostgreSQL | Relational experiment records, integrity constraints, and analytical queries | Database-backed experiment log |

The implementations share the same fundamental gate mathematics while using different data structures and runtime capabilities. They should not be expected to produce identical seeded samples because their random-number generators and sampling implementations differ.

## Limitations and practical considerations

A statevector simulator stores all amplitudes of a pure quantum state. The exponential memory requirement restricts the number of qubits that can be simulated directly. The educational simulators are intended for small circuits, where every amplitude can be inspected.

The examples use ideal unitary gates. They do not model decoherence, gate infidelity, readout error, device connectivity, queue delays, or compilation overhead. Real hardware measurements may therefore differ from ideal simulation results.

Measurement is destructive in the standard projective measurement model. The post-measurement state generally differs from the pre-measurement superposition. This is why the Python program inspects a circuit without measurement when obtaining its statevector and runs a separate measured circuit to obtain counts.

The SQL schema captures experiment metadata and results but does not verify quantum correctness independently. A record can satisfy relational constraints and still contain physically implausible results. Scientific validation must combine database integrity, circuit semantics, simulator or hardware behavior, and appropriate statistical tests.
