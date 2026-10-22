# QFT Implementation: Build QFT Circuits

## Scope

This project implements the Quantum Fourier Transform (QFT) as a gate-level quantum circuit and connects circuit construction to state-vector simulation, inverse transformation, circuit validation, execution auditing, and relational workflow modeling.

The four implementation languages use deliberately different perspectives:

| File | Primary perspective | Main responsibility |
|---|---|---|
| Python | Quantum-state model | Construct and verify QFT circuits with direct numerical comparison |
| JavaScript | Event-driven execution | Execute circuit stages asynchronously and expose progress |
| C++17 | High-performance simulation | Implement a gate engine with explicit complexity and memory controls |
| Java 17 | Enterprise domain model | Separate circuit policy, execution state, validation, and domain behavior |
| PostgreSQL | Persistent workflow model | Store circuits, gates, states, executions, and validation events |

The four conceptual areas are kept distinct:

- **QFT circuit:** Describes how the Fourier transformation is constructed from quantum gates.
- **QFT implementation:** Executes those gates against a quantum state.
- **Validation:** Establishes that the gate decomposition agrees with the mathematical QFT.
- **Execution auditing:** Records whether a circuit satisfies operational constraints before and after execution.

## Mathematical Basis

For a state vector of dimension \(N = 2^n\), the QFT maps amplitudes \(x_j\) to amplitudes \(y_k\):

\[
y_k =
\frac{1}{\sqrt{N}}
\sum_{j=0}^{N-1}
x_j e^{2\pi i jk/N}
\]

The inverse QFT changes the sign of the phase:

\[
x_j =
\frac{1}{\sqrt{N}}
\sum_{k=0}^{N-1}
y_k e^{-2\pi i jk/N}
\]

The transformation is unitary. Therefore, applying the inverse QFT after the forward QFT must recover the original quantum state up to numerical floating-point error.

The implementations use computational-basis indexing where qubit 0 is the least-significant bit.

## Circuit Construction

The standard QFT decomposition is built from three types of operations:

- Hadamard gates
- Controlled phase rotations
- Final qubit swaps

For \(n\) qubits, the decomposition contains:

\[
n + \frac{n(n-1)}{2} + \left\lfloor\frac{n}{2}\right\rfloor
\]

gate operations.

The first term represents Hadamard gates.

The second term represents controlled phase rotations.

The final term represents the swaps required to reverse the qubit ordering produced by the decomposition.

For a three-qubit QFT, the circuit contains:

| Gate type | Count |
|---|---:|
| Hadamard | 3 |
| Controlled phase | 3 |
| SWAP | 1 |
| Total | 7 |

The controlled rotations use progressively smaller angles:

\[
R_k =
\begin{bmatrix}
1 & 0\\
0 & e^{2\pi i/2^k}
\end{bmatrix}
\]

The implementations express these rotations through angles such as \(\pi/2\) and \(\pi/4\), depending on the distance between control and target qubits.

## QFT Versus Direct Fourier Evaluation

The mathematical QFT can be calculated directly with the discrete Fourier expression. That approach evaluates every input-output pair and requires \(O(N^2)\) arithmetic operations.

Because \(N=2^n\), this becomes:

\[
O(4^n)
\]

in terms of qubit count.

The circuit decomposition instead applies \(O(n^2)\) gates, while state-vector simulation still requires processing \(2^n\) amplitudes for gate operations. Its state-vector execution cost is approximately:

\[
O(n2^n)
\]

with:

\[
O(2^n)
\]

memory.

This distinction is important. The QFT circuit has efficient gate complexity, but classical state-vector simulation remains exponential in the number of qubits.

## Python Implementation

The Python implementation provides the most complete numerical reference model.

`QuantumState` validates that:

- The state is non-empty.
- Its dimension is a power of two.
- Its norm is non-zero.
- Its amplitudes are normalized.

`QFTCircuit` stores the actual gate sequence rather than only computing the Fourier matrix. It constructs Hadamard gates, controlled-phase operations, and output-reversal swaps.

The implementation includes an explicit `InverseQFTCircuit`. It reverses the gate order and negates controlled-phase angles, which follows the rule:

\[
(ABC)^{-1}=C^{-1}B^{-1}A^{-1}
\]

The Python program also contains a direct \(O(N^2)\) QFT implementation. The circuit implementation is compared with this mathematical reference for basis states from one through four qubits.

The validation process checks:

- Gate decomposition correctness
- Inverse-QFT recovery
- Unitary behavior
- Invalid state dimensions
- Zero-norm state rejection

The state printer reports computational-basis amplitudes and probabilities, making phase information and measurement probabilities visible separately.

## JavaScript Implementation

The JavaScript implementation uses an event-driven execution model rather than reproducing the Python organization.

The circuit is represented as an ordered sequence of JavaScript objects. The asynchronous `apply` method executes one gate at a time and yields to the Node.js event loop after each stage.

This makes the model appropriate for an interactive execution service where circuit progress could be reported to another component.

The execution callback receives:

- Current gate number
- Total gate count
- The operation being executed

The implementation uses explicit complex-number objects because JavaScript has no built-in complex-number primitive.

The asynchronous structure also exposes an operational concern that is less visible in a purely synchronous numerical implementation: circuit execution can be integrated into a long-running service without monopolizing the event loop during every individual circuit stage.

The program validates circuit and state dimensions before execution and demonstrates an explicit simulation-size policy. This is important because a request for an unrestricted number of qubits can cause exponential memory allocation.

## C++17 Implementation

The C++ implementation treats the QFT as a compact gate engine.

The `Gate` structure stores:

- Gate type
- Target qubit
- Optional control qubit
- Optional second qubit
- Rotation angle

`QFTCircuit` constructs the complete gate sequence and provides separate forward and inverse execution.

The inverse circuit is not separately generated as a new matrix. Instead, the original gate sequence is traversed in reverse order. Hadamard and SWAP gates are self-inverse, while controlled phase rotations require negation of their angle.

The implementation explicitly compares:

- Gate-level QFT
- Direct Fourier evaluation
- Inverse-QFT recovery

It restricts simulation to a practical maximum of 20 qubits. This is not a mathematical restriction on QFT itself. It is an operational protection for classical state-vector simulation.

For \(n\) qubits, a state vector contains \(2^n\) complex values. Consequently, increasing the qubit count by one doubles the state-vector memory requirement.

## Java 17 Implementation

The Java implementation models QFT execution as an explicit domain workflow.

`Gate` is an immutable record containing the gate parameters.

`QuantumState` owns the normalized state vector.

`QFTPolicy` represents execution policy separately from circuit construction. This separation allows operational rules such as maximum supported qubits and normalization requirements to be changed without modifying the QFT decomposition.

`ExecutionReport` captures the outcome of policy validation:

- Accepted
- Rejected
- Completed

The `MergeLikeCircuitAudit` service records the validation decision before circuit execution. The name describes its workflow role without conflating validation with the mathematical QFT itself.

The enterprise-oriented structure makes several concerns explicit:

- Domain validation
- Execution policy
- State normalization
- Circuit construction
- Forward execution
- Inverse execution
- Execution reporting

The implementation also uses Java's immutable record types to reduce accidental mutation of circuit definitions.

## PostgreSQL Implementation

The PostgreSQL model treats a QFT circuit as persistent structured data.

The central relationships are:

- `circuits`
  - `circuit_gates`
  - `basis_states`
  - `executions`
    - `execution_gate_events`

`circuits` stores circuit-level metadata and lifecycle status.

`circuit_gates` stores the ordered gate sequence.

`basis_states` stores reproducible computational-basis inputs.

`executions` records forward or inverse execution attempts.

`execution_gate_events` provides an auditable relationship between an execution and the gates applied during that execution.

The database uses PostgreSQL enumerated types for controlled lifecycle values. This prevents arbitrary status strings from entering the workflow.

## Database Integrity Rules

Several rules are enforced at the database layer rather than relying only on application code.

Primary keys identify circuits, gates, states, executions, and execution events.

Foreign keys preserve relationships between those entities.

Unique constraints prevent duplicate gate positions inside a circuit and duplicate basis-state indexes within a circuit.

Check constraints enforce:

- Positive gate positions
- Valid qubit numbers
- Valid execution directions
- Non-negative numerical errors
- Valid controlled-phase structure
- Valid SWAP structure

The `validate_qft_gate` trigger checks the circuit's qubit count before accepting a gate. This protects the database even when an insertion originates outside the application implementation.

## Transactional Workflow

Circuit validation is performed before execution.

The database function `validate_qft_circuit` compares the actual gate count with the expected QFT decomposition:

\[
n + \frac{n(n-1)}{2} + \left\lfloor\frac{n}{2}\right\rfloor
\]

A circuit that does not satisfy the structural requirements is marked rejected.

Execution is then represented by an `executions` record.

The completion function records the maximum reference error and converts the numerical result into a completed or rejected execution state.

The example also contains a transaction that attempts to insert a gate targeting a nonexistent qubit. The trigger rejects the operation and the transaction is rolled back.

This illustrates the distinction between:

- Application-level numerical correctness
- Database-level structural integrity

## Validation Strategy

The implementations do not rely on visual inspection of amplitudes alone.

A circuit implementation is validated against the direct Fourier equation.

For an input state \(x\), the expected output is calculated directly and compared with the gate-level result.

The maximum amplitude difference is used as the numerical error:

\[
\epsilon = \max_i |a_i-b_i|
\]

A tolerance around \(10^{-9}\) is appropriate for the small floating-point simulations used here.

The inverse transform provides an independent validation path. If:

\[
QFT^{-1}(QFT(|\psi\rangle))
\]

does not recover the original state within numerical tolerance, either the gate ordering, phase convention, bit ordering, or numerical implementation is incorrect.

## Bit Ordering

Bit ordering is a common source of QFT implementation errors.

The implementations define qubit 0 as the least-significant bit.

For a three-qubit basis state with integer index 3:

- Integer index: `3`
- Binary state: `011`
- Qubit 0: least-significant bit
- Qubit 1: middle bit
- Qubit 2: most-significant bit

The final SWAP operations reverse the qubit ordering generated by the standard decomposition.

Removing those swaps changes the representation of the output rather than simply producing an unrelated transformation. A circuit intended to match the conventional QFT therefore needs an explicit ordering convention.

## Edge Cases

The implementations reject empty state vectors.

They reject state dimensions that are not powers of two.

They reject zero-norm states.

They reject circuits whose state-vector dimensions do not match the circuit's qubit count.

Controlled-phase gates reject identical control and target qubits.

The database rejects gates whose qubit positions exceed the circuit width.

The execution policies impose maximum simulation sizes because classical simulation has exponential memory requirements.

Floating-point comparisons use tolerances rather than exact equality because complex arithmetic accumulates rounding error.

## Performance Considerations

The gate decomposition has approximately \(O(n^2)\) logical gates.

Classical state-vector execution requires \(O(2^n)\) storage.

A complete circuit execution is approximately:

\[
O(n2^n)
\]

for the state-vector approach used here.

The direct reference QFT requires:

\[
O(N^2)=O(4^n)
\]

operations.

The direct implementation is therefore useful as a correctness oracle for small systems but is not an appropriate scalable execution strategy.

The PostgreSQL indexes target actual access patterns:

- Ordered gate retrieval by circuit
- Execution lookup by circuit and status

The database does not attempt to store every amplitude of a large state vector. Such a representation would reproduce the same exponential storage problem at the database layer without providing a useful persistence advantage.

## Security and Operational Considerations

A QFT circuit definition supplied by an external caller should be validated before memory allocation or execution.

The number of qubits is the most important resource-control parameter because state-vector size grows exponentially.

A service should therefore establish explicit limits on:

- Maximum qubits
- Maximum circuit depth
- Maximum number of concurrent executions
- Execution time
- State-vector memory

The JavaScript implementation demonstrates an event-loop-friendly execution pattern, while the C++ and Java implementations enforce explicit simulation-size limits.

Database constraints provide a second layer of protection against structurally invalid circuits.

Numerical errors should be recorded rather than silently discarded because reproducibility and auditability are important when circuit results are used in larger computational workflows.

## Practical Circuit Interpretation

For a computational-basis input \(|x\rangle\), the QFT distributes amplitude across the Fourier basis while encoding information about the input integer into relative phases.

The transformation is therefore not equivalent to simply redistributing classical probabilities.

A state can have the same measurement probabilities while having different relative phases. The controlled-phase gates are responsible for building these phase relationships.

The Hadamard gates establish superposition components, while the controlled rotations condition phase changes on the states of other qubits.

The final swaps are an ordering operation required by the conventional gate decomposition.

## Relationship Between the Source Files

The five executable artifacts represent the same mathematical transformation but emphasize different engineering properties.

The Python implementation is the primary numerical reference and exposes the mathematical-to-circuit correspondence.

The JavaScript implementation treats the circuit as an asynchronous execution workflow.

The C++ implementation emphasizes compact gate representation, state-vector performance, and explicit resource constraints.

The Java implementation separates domain policy from execution and models circuit behavior through immutable domain types.

The PostgreSQL implementation persists the circuit definition and its execution lifecycle, enforcing structural integrity at the database boundary.

These perspectives are complementary because a QFT implementation is not only a mathematical formula. A usable implementation requires a circuit representation, a gate execution model, numerical validation, resource controls, and reliable state management.
