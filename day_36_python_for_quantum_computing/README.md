# Python for Quantum Computing: Python Fundamentals and NumPy

## Scope

This repository presents Python as a numerical foundation for small-scale quantum computing simulations. The central connection is the representation of quantum states as complex-valued vectors and quantum gates as matrices.

The implementations distinguish three layers:

- **Python fundamentals** provide the control structures, functions, classes, dictionaries, validation, exceptions, and data modeling needed to build a simulator.
- **NumPy** provides dense numerical arrays, complex arithmetic, vector norms, matrix-vector multiplication, tensor products, probability calculations, and numerical optimization.
- **Quantum computing** supplies the mathematical domain: state vectors, amplitudes, computational-basis states, unitary gates, measurement, expectation values, tensor products, entanglement, and circuit execution.

The examples intentionally use small state-vector simulations. A full state vector contains \(2^n\) complex amplitudes for \(n\) qubits, so this representation becomes expensive as the number of qubits grows.

## Core Quantum Representation

A single-qubit state is represented as

\[
|\psi\rangle =
\begin{bmatrix}
\alpha \\
\beta
\end{bmatrix}
\]

where \(\alpha\) and \(\beta\) are complex amplitudes.

The physical probability of measuring `0` is

\[
P(0)=|\alpha|^2
\]

and the probability of measuring `1` is

\[
P(1)=|\beta|^2.
\]

A valid quantum state satisfies

\[
|\alpha|^2 + |\beta|^2 = 1.
\]

The Python implementation represents this structure with a NumPy `complex128` array. This choice matters because quantum amplitudes are not generally real numbers. A phase such as \(i\beta\) changes interference behavior even though its magnitude may remain unchanged.

The `validate_state()` function therefore checks dimensionality, power-of-two state size, finite numerical values, and normalization.

## Python Fundamentals Used in the Simulator

Python lists are useful for circuit histories and collections of operations. Dictionaries are used for measurement counts because a classical measurement result naturally maps a bitstring such as `00` or `11` to the number of times it occurred.

Functions isolate mathematical operations such as normalization, measurement, expectation-value calculation, tensor products, and gate application. This separation prevents the circuit abstraction from having to implement every numerical detail itself.

The `QuantumCircuit` class provides stateful behavior while keeping the underlying state vector explicit. Its methods such as `h()`, `x()`, `z()`, and `cnot()` represent domain operations rather than generic Python demonstrations.

Python exceptions are used to reject invalid quantum states, invalid qubit indexes, incompatible matrix dimensions, invalid measurement shot counts, and impossible circuit configurations.

The `dataclass` used by `GateOperation` gives each recorded operation a clear immutable structure rather than storing loosely related values.

## NumPy as the Numerical Layer

NumPy is used where array-oriented computation is the natural abstraction.

The state vector is a dense one-dimensional array:

`np.array([alpha, beta], dtype=np.complex128)`

The norm is calculated with `np.linalg.norm()`. Measurement probabilities are calculated efficiently with:

`np.abs(state) ** 2`

Complex conjugation is important when calculating expectation values. The implementation uses `np.vdot()` so that the first vector is conjugated before the inner product is evaluated.

Matrix-vector multiplication uses the `@` operator. For example, applying a gate follows the mathematical form

`new_state = gate @ state`

Tensor products are implemented through `np.kron()`. A multi-qubit state is not merely a longer independent list. Its vector dimension grows according to the combined Hilbert-space dimension.

The implementation uses `np.linspace()` for numerical parameter sweeps and `np.argmin()` for selecting the lowest sampled objective value in the variational example.

## Single-Qubit Gates

The Pauli-X matrix exchanges the computational basis states:

\[
X =
\begin{bmatrix}
0 & 1 \\
1 & 0
\end{bmatrix}.
\]

Therefore \(X|0\rangle=|1\rangle\).

The Pauli-Y matrix introduces complex phase:

\[
Y =
\begin{bmatrix}
0 & -i \\
i & 0
\end{bmatrix}.
\]

The Pauli-Z matrix changes the phase of the `|1>` component:

\[
Z =
\begin{bmatrix}
1 & 0 \\
0 & -1
\end{bmatrix}.
\]

The Hadamard matrix creates computational-basis superposition:

\[
H =
\frac{1}{\sqrt{2}}
\begin{bmatrix}
1 & 1 \\
1 & -1
\end{bmatrix}.
\]

Consequently,

\[
H|0\rangle =
\frac{|0\rangle+|1\rangle}{\sqrt{2}}.
\]

The Python implementation also checks that these gates are unitary. For a unitary matrix \(U\),

\[
U^\dagger U=I.
\]

This is important because ideal quantum gates preserve state-vector normalization.

## Tensor Products and Multiple Qubits

A two-qubit system has four computational basis states:

`|00>`, `|01>`, `|10>`, and `|11>`.

The state-vector dimension is therefore four rather than two.

The tensor product combines subsystem operators and states. For example,

\[
|+\rangle\otimes|0\rangle
\]

is represented with `np.kron(PLUS, ZERO)`.

For a circuit containing several qubits, a single-qubit operation must be expanded into the complete system space. If a gate acts on one of three qubits, the complete operator has the form

\[
I\otimes H\otimes I
\]

when the middle qubit is the target.

The `apply_single_qubit_gate()` function constructs this full operator before applying it to the state vector.

## Controlled Operations

A controlled operation makes one operation conditional on the state of another qubit.

The implementation constructs a controlled gate by examining computational-basis bitstrings. For a controlled-X operation, the target bit is flipped only when the control bit is `1`.

This mechanism produces the two-qubit CNOT operation used by the Bell-state example.

The CNOT implementation validates that the control and target are different and that both indexes belong to the circuit.

## Bell State

The Bell-state example constructs

\[
|\Phi^+\rangle =
\frac{|00\rangle+|11\rangle}{\sqrt{2}}.
\]

The circuit begins with `|00>`, applies a Hadamard gate to the first qubit, and then applies CNOT.

The resulting computational-basis probabilities are:

| Outcome | Probability |
|---|---:|
| `00` | 0.5 |
| `01` | 0 |
| `10` | 0 |
| `11` | 0.5 |

This demonstrates the difference between local randomness and correlation. Each individual qubit has equal computational-basis probabilities, while the pair produces correlated `00` or `11` outcomes.

The simulation does not claim that the individual qubits contain definite classical values before measurement. It represents the joint quantum state and derives classical statistics from that state.

## Measurement

Measurement converts a quantum probability distribution into classical samples.

The `probabilities()` function obtains theoretical probabilities from amplitude magnitudes. The `sample_measurements()` function then uses NumPy's random generator to draw repeated computational-basis outcomes.

The distinction between probabilities and samples is important:

- The state vector represents amplitudes.
- Squared magnitudes represent ideal measurement probabilities.
- A finite number of shots produces an empirical distribution.
- Sampling noise means measured frequencies do not normally equal theoretical probabilities exactly.

A fixed random seed is used in the examples to make demonstrations reproducible.

The simulator does not attempt to represent the complete post-measurement state history. It is designed around repeated computational-basis sampling from the modeled state.

## Bloch Vector

A single-qubit state can be characterized through expectation values of the Pauli operators.

The Bloch-vector components are

\[
x=\langle X\rangle,
\qquad
y=\langle Y\rangle,
\qquad
z=\langle Z\rangle.
\]

The Python `bloch_vector()` function calculates these values from the state vector.

For `|0>`, the vector points along positive Z:

\[
(0,0,1).
\]

For `|1>`, it points along negative Z:

\[
(0,0,-1).
\]

For `|+>`, it points along positive X:

\[
(1,0,0).
\]

This is a concrete example of Python and NumPy translating an abstract quantum representation into numerical observables.

## Expectation Values

For an observable \(A\), the expectation value is

\[
\langle A\rangle =
\langle\psi|A|\psi\rangle.
\]

The Python implementation uses the conjugate transpose of the state through `np.vdot()`.

Expectation values are useful because many quantum algorithms do not require reconstructing every amplitude directly. They instead estimate quantities such as energies or correlations from measurements.

The example evaluates Pauli-X and Pauli-Z expectations for several basic states.

## Variational Numerical Calculation

The `RY` function constructs a parameterized rotation:

\[
R_Y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{bmatrix}.
\]

The state

\[
|\psi(\theta)\rangle=R_Y(\theta)|0\rangle
\]

is evaluated against the Z observable.

The `find_lowest_energy()` function performs a transparent grid search over parameter values. It is intentionally simple so that the connection between quantum-state preparation and classical numerical optimization remains visible.

This is representative of the numerical structure behind variational quantum algorithms: a classical process proposes parameters, a quantum circuit prepares a parameterized state, an observable is evaluated, and the resulting numerical objective can be optimized.

The implementation is not a complete VQE framework. It is a compact demonstration of the mathematical relationship.

## Python Implementation

The Python script is the primary educational implementation.

Its progression is deliberate:

- Python collections and functions establish the basic program structure.
- Complex NumPy arrays represent amplitudes.
- Validation ensures that state vectors satisfy basic mathematical requirements.
- Gate matrices transform states.
- Tensor products extend single-qubit operations to multiple qubits.
- Measurement converts amplitudes into classical statistics.
- Expectation values connect states to observables.
- The circuit class groups operations into a reusable stateful model.
- The Bell-state experiment demonstrates multi-qubit correlation.
- The variational example connects quantum simulation to classical numerical search.
- Scaling output exposes the exponential memory cost of dense state-vector simulation.

The implementation uses no quantum-computing framework. That makes the mathematical role of Python and NumPy explicit rather than hiding it behind a high-level circuit API.

## JavaScript Implementation

The JavaScript implementation takes a different engineering perspective.

Instead of relying on NumPy's complex-number and matrix facilities, it defines a `Complex` class and explicit matrix operations. This makes the data transformations visible within ordinary JavaScript objects and arrays.

The `QuantumCircuit` class uses event listeners. Circuit operations emit events, and measurement emits a separate event containing shot results. This models an event-driven execution environment that is natural in JavaScript applications.

The circuit is therefore not just a line-by-line translation of the Python program. It demonstrates how quantum numerical concepts can be integrated with JavaScript's object model and asynchronous execution style.

The JavaScript version also demonstrates measurement randomness and a small parameter-search calculation without requiring an npm dependency.

## C++ Case Study

The C++ program treats the simulator as a small technical system rather than as a collection of syntax examples.

The state vector uses `std::vector<std::complex<double>>`. Matrix operations are explicitly represented with nested vectors.

The `QuantumCircuit` class owns the current state and records an operation history. Gate expansion uses Kronecker products so that a one-qubit operation can act within a multi-qubit Hilbert space.

The CNOT implementation works directly with binary indexes. A control bit is inspected and the target bit is flipped when the control is active.

The Bell-state case study verifies that the expected computational-basis outcomes are restricted to `00` and `11`. Unexpected `01` or `10` outcomes are treated as a simulation failure.

The program also calculates an expectation value and reports state-vector memory growth.

C++ makes an important systems-level trade-off visible: a dense state-vector simulator requires explicit memory for every amplitude, and matrix-based implementations can require substantially more memory and computation than specialized sparse or tensor-network techniques.

## Java Enterprise-Oriented Model

The Java implementation models a quantum experiment as a domain object with explicit types.

`ExperimentConfig` represents validated execution configuration. The record enforces constraints such as positive shot count and a bounded educational circuit size.

`GateType` makes gate identity explicit rather than relying on arbitrary strings.

`Operation` captures target and control qubits.

`QuantumState` owns validated complex amplitudes and prevents construction of a non-normalized state.

`QuantumCircuit` models state transitions and records operations.

`MeasurementService` isolates classical sampling from circuit construction.

`GovernanceService` coordinates configuration validation, circuit execution, and measurement. This separation demonstrates a service-oriented structure appropriate for a larger application.

The use of Java records, enums, immutable-style copies, explicit exceptions, and domain-oriented classes keeps the numerical implementation connected to enterprise application design.

## SQL Data Model

The PostgreSQL script treats the quantum workflow as relational experiment data.

The main relationships are:

`experiments` → `circuits` → `gate_operations`

and

`circuits` → `quantum_states` → `state_amplitudes`.

Measurement data is represented through:

`measurements` → `measurement_counts`.

Observable results are stored in `observables`.

This structure separates the definition of an experiment from its circuit, state, measurement, and observable records.

The `experiments.qubit_count` field defines the circuit size. The trigger on `circuits` ensures that the initial computational-basis string has the correct width.

The gate-operation constraints prevent invalid CNOT records in which the control qubit is omitted or equals the target qubit.

The state-amplitude table stores real and imaginary components separately. PostgreSQL then calculates probability as a generated column:

`real_part * real_part + imaginary_part * imaginary_part`

This keeps probability derivation deterministic from stored amplitudes.

## Database-Level Integrity

The schema deliberately places structural rules in PostgreSQL rather than assuming every client will validate them correctly.

Primary keys prevent duplicate entity identities.

Foreign keys prevent orphaned circuits, operations, states, and measurement records.

Unique constraints prevent duplicate circuit versions and duplicate observable records.

Check constraints enforce valid gate names, positive shot counts, valid basis-state syntax, non-negative probabilities, and normalized-state metadata.

The transaction example demonstrates how a malformed CNOT operation can be attempted and then rolled back.

The database is not responsible for implementing arbitrary quantum linear algebra. Its role is to preserve experiment definitions, numerical results, reproducibility metadata, and relationships with strong integrity guarantees.

## Relationship Between Python and NumPy

Python and NumPy play different roles.

Python provides the programming model:

- Functions organize numerical operations.
- Classes represent circuits.
- Dictionaries store measurement counts.
- Exceptions express invalid configurations.
- Dataclasses represent structured operation records.
- Loops control circuit construction and simulation workflows.

NumPy provides the numerical substrate:

- `ndarray` represents vectors and matrices.
- `complex128` represents complex amplitudes.
- `np.kron()` implements tensor products.
- `np.vdot()` implements the conjugate inner product.
- `np.linalg.norm()` evaluates vector norms.
- `np.abs()` extracts amplitude magnitudes.
- `np.random.default_rng()` provides reproducible sampling.
- `np.linspace()` generates parameter grids.

Quantum computing gives these programming constructs a specific mathematical meaning.

A Python list by itself is merely a collection. A NumPy complex array validated to unit norm can represent a quantum state within the state-vector model.

## Numerical Precision

The simulator uses floating-point arithmetic. Mathematical identities such as

\[
|\alpha|^2+|\beta|^2=1
\]

may therefore be represented numerically as values extremely close to one rather than exactly one.

For that reason, validation uses tolerance-based comparisons instead of exact floating-point equality.

The code uses values around `1e-10` for strict state validation and somewhat wider tolerances after numerical gate operations.

This matters when circuits contain many transformations because rounding error can accumulate.

A tolerance that is too strict can reject valid numerical results. A tolerance that is too loose can conceal genuine implementation errors.

## Failure Conditions

The implementations explicitly reject several invalid conditions.

A zero vector cannot be normalized because it has no valid normalization factor.

A state vector whose dimension is not a power of two cannot represent an integer number of qubits in the computational-basis state-vector model.

A non-normalized state is rejected because measurement probabilities would not form a valid probability distribution.

A gate with incompatible dimensions cannot be applied to a state.

A controlled operation cannot use the same qubit as both control and target.

A target outside the circuit's qubit range is rejected.

Measurement requires a positive number of shots.

The educational simulators also impose practical qubit limits so that an accidental request does not allocate an unexpectedly large dense vector.

## Entanglement and State Size

The number of amplitudes grows exponentially:

| Qubits | Amplitudes |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 5 | 32 |
| 10 | 1,024 |
| 20 | 1,048,576 |
| 30 | 1,073,741,824 |

A complex double-precision amplitude requires 16 bytes in the representations used here.

At 20 qubits, the state vector alone requires roughly 16 MiB.

At 30 qubits, the same dense representation requires roughly 16 GiB before accounting for matrices, temporary arrays, circuit objects, measurement data, and runtime overhead.

The important lesson is that Python syntax is not the principal scalability constraint. The underlying quantum state space itself grows exponentially in this representation.

## Performance Considerations

Applying a dense \(2^n \times 2^n\) matrix to a \(2^n\)-element state vector becomes expensive rapidly.

The educational implementation intentionally favors clarity over high-performance simulation.

For small systems, NumPy's optimized native numerical routines are substantially more appropriate than manually iterating over every scalar operation in pure Python.

For larger simulations, constructing a complete dense matrix for every single-qubit gate is itself inefficient. More specialized state-vector simulators apply local gates directly to amplitude pairs without materializing the entire operator.

The C++ and Java implementations make this architectural trade-off visible by explicitly constructing matrices. The Python version uses NumPy to keep the implementation concise while retaining the underlying mathematical structure.

## Security and Reproducibility

The simulation examples use explicit seeds when reproducible results are useful.

A seed is not equivalent to cryptographic randomness. The purpose of deterministic seeds in these experiments is reproducibility for testing, debugging, and education.

The JavaScript implementation attempts to use stronger runtime randomness where available and falls back to ordinary pseudorandom generation for environments without a suitable randomness source.

Neither approach should be interpreted as a secure quantum random-number generator.

A production quantum application must also distinguish simulated randomness from randomness produced by actual quantum hardware.

## Debugging Strategy

The most useful debugging invariant is state normalization.

After every ideal unitary operation,

\[
\lVert|\psi\rangle\rVert=1
\]

should remain true within an appropriate numerical tolerance.

Probability sums provide another diagnostic:

\[
\sum_i |\alpha_i|^2=1.
\]

For a Bell state, the presence of `01` or `10` outcomes indicates a serious simulation error rather than ordinary sampling noise.

Gate dimensions should always match the state dimension.

Controlled-gate indexes should remain within the circuit.

When debugging a multi-qubit circuit, inspecting the state vector after each operation is often more informative than looking only at the final measurement histogram.

## Practical Distinctions

A **state vector** stores complex amplitudes.

A **probability distribution** stores squared amplitude magnitudes.

A **quantum gate** is represented by a matrix acting on a state.

A **unitary gate** preserves the state's norm.

A **measurement** produces classical outcomes sampled according to probabilities.

An **expectation value** evaluates the average result associated with an observable.

A **tensor product** combines quantum subsystems into a larger Hilbert space.

An **entangled state** cannot generally be represented as a simple tensor product of independent single-qubit states.

These distinctions are maintained across the implementations rather than treating every numerical array as interchangeable.

## Limitations

This material implements an educational state-vector simulator rather than a production quantum runtime.

It does not model hardware noise, decoherence, readout error, gate calibration, device topology, pulse-level control, error correction, fault-tolerant logical qubits, or realistic hardware scheduling.

The circuit simulator also uses dense representations and therefore does not scale to large quantum systems.

The SQL layer stores numerical experiment data but does not replace a numerical linear-algebra engine.

The variational example demonstrates the structure of parameterized quantum optimization but does not implement a complete optimizer, gradient estimator, or hardware execution loop.

These limitations are intentional because the central objective is to expose the relationship between Python fundamentals, NumPy numerical computation, and the mathematical representation of small quantum systems.
