# Quantum Circuits: Circuit Construction Fundamentals

## Scope

This repository studies the construction and execution of quantum circuits from the level of individual gates through multi-qubit circuit composition and small state-vector simulation.

The three implementations approach the same subject from different engineering perspectives:

- The Python program provides a compact educational simulator with reusable gate application functions, circuit objects, validation, measurement probabilities, sampling, parameterized rotations, controlled operations, and executable tests.
- The JavaScript program treats circuit construction as an event-driven object model. It adds lifecycle events, asynchronous execution boundaries, circuit serialization, validation reporting, and probability sampling.
- The C++ program presents a more structured case study resembling a small circuit-execution engine. It introduces typed operations, validation exceptions, conservative circuit optimization, semantic-equivalence checking, and explicit analysis of state-vector scaling.

The central mathematical model is a sequence of unitary transformations applied to an initial computational-basis state. A circuit therefore has two related but distinct representations: its construction as an ordered operation sequence and its execution as transformations of a quantum state.

## Quantum Register and Computational Basis

A quantum circuit begins with a register containing a fixed number of qubits. For an `n`-qubit register, the computational basis contains `2^n` basis states.

For two qubits, the basis is:

- `|00>`
- `|01>`
- `|10>`
- `|11>`

A state vector assigns a complex amplitude to every basis state. For example, the two-qubit state

`(|00> + |11>) / sqrt(2)`

has amplitudes `1/sqrt(2)` for `|00>` and `|11>`, with zero amplitude for `|01>` and `|10>`.

The probability of observing a basis state is the squared magnitude of its amplitude:

`P(x) = |alpha_x|^2`

The probabilities must sum to one for a normalized state.

The implementations explicitly verify this normalization before exposing measurement probabilities. This makes state-vector execution useful for understanding how circuit construction becomes observable measurement behavior.

## Circuit Construction Model

A circuit is represented as an ordered collection of operations. Order matters because quantum gates generally do not commute.

For a circuit containing operations `G1`, `G2`, and `G3`, execution applies them sequentially:

`|psi_final> = G3 G2 G1 |psi_initial>`

The source-code order is therefore part of the circuit's meaning.

The implementations separate construction from execution. Calling methods such as `h(0)`, `x(1)`, `ry(0, theta)`, or `cx(0, 1)` records an operation. Execution later starts from the all-zero state and applies the recorded operations.

This separation is useful because a circuit can be inspected, validated, serialized, optimized, or modified before execution.

## Single-Qubit Gates

The Python, JavaScript, and C++ implementations include the Pauli-X, Pauli-Z, Hadamard, and parameterized rotation operations.

### Pauli-X

The X gate exchanges the computational basis states:

`X|0> = |1>`

`X|1> = |0>`

It is therefore useful for deterministic basis-state preparation.

The implementations represent X as the matrix:

`[[0, 1], [1, 0]]`

Applying it to a target qubit requires identifying pairs of state-vector entries that differ only in that qubit's binary value.

### Pauli-Z

The Z gate leaves `|0>` unchanged and changes the phase of `|1>`:

`Z|0> = |0>`

`Z|1> = -|1>`

This is important because phase is part of a quantum state even though a phase change alone may not alter immediate computational-basis measurement probabilities.

### Hadamard

The Hadamard gate creates an equal superposition from `|0>`:

`H|0> = (|0> + |1>) / sqrt(2)`

It also creates the corresponding negative-phase superposition from `|1>`.

The Bell-state examples use H as the first operation because it creates the superposition that the subsequent controlled operation correlates with another qubit.

### Parameterized rotations

`RY(theta)` and `RZ(theta)` demonstrate that circuit construction does not have to be limited to a fixed gate vocabulary.

The rotation angle is stored with the operation and converted into a matrix during circuit construction. This makes the circuit model suitable for parameterized experiments where changing an angle changes the resulting state without changing the circuit architecture.

## Multi-Qubit Operations

Single-qubit gates act independently on one selected qubit. Controlled gates introduce conditional behavior between qubits.

The controlled-X gate, commonly called CX or CNOT, applies X to the target only when the control qubit is in `|1>`.

Its operational rule is:

`|00> -> |00>`

`|01> -> |01>`

`|10> -> |11>`

`|11> -> |10>`

The implementation does not construct a full `2^n x 2^n` matrix for every controlled gate. Instead, it directly identifies state-vector amplitude pairs whose control bit is set and applies the 2-by-2 target matrix to those pairs.

This is an important implementation decision. The mathematical operation acts on the full state space, but sparse indexing logic can apply the same transformation without materializing the entire large matrix.

The JavaScript and C++ programs also include controlled-Z. This demonstrates that controlled operations are a construction pattern rather than a synonym for CX.

## Bell-State Construction

The canonical two-qubit example is:

`H(q0)`

followed by:

`CX(q0, q1)`

Starting from `|00>`, the Hadamard produces:

`(|00> + |10>) / sqrt(2)`

The CX operation changes the target only for the `q0 = 1` component, producing:

`(|00> + |11>) / sqrt(2)`

The resulting measurement distribution contains only `00` and `11`, each with probability one half.

The Python implementation prints the state vector and samples repeated measurements. The JavaScript implementation adds circuit lifecycle events and asynchronous execution. The C++ implementation treats the Bell circuit as a concrete system case study and performs deterministic assertions against its expected distribution.

## Qubit Indexing

The implementations use a consistent convention in which the displayed binary representation follows circuit qubit order, with `q0` corresponding to the most significant displayed bit.

For a three-qubit register:

`|q0 q1 q2>`

is represented by an integer index whose binary form has the same ordering.

When applying a gate to a target qubit, the simulator calculates the corresponding bit position using:

`qubits - 1 - target`

This indexing detail is critical. A circuit can produce apparently plausible results while still being incorrect if the mapping between logical qubits and state-vector indices is inconsistent.

The implementations therefore use the same mapping throughout gate application, state display, probability reporting, and measurement labels.

## State-Vector Execution

The simulators begin execution in:

`|00...0>`

The state vector has `2^n` entries, with the first entry initialized to one and all others initialized to zero.

For a single-qubit operation, the simulator processes pairs of amplitudes. The two entries represent the target qubit being `0` and `1` while all other qubit values remain fixed.

For a matrix

`U = [[u00, u01], [u10, u11]]`

and amplitudes `a0` and `a1`, the updated pair is:

`a0' = u00*a0 + u01*a1`

`a1' = u10*a0 + u11*a1`

Controlled operations use the same transformation only for index pairs whose control bit is set.

This direct state-vector approach is intentionally transparent. It demonstrates the computational mechanism without requiring a large quantum-computing framework.

## Measurement and Sampling

Circuit execution produces amplitudes rather than classical answers.

The measurement probability for basis state `x` is:

`|alpha_x|^2`

The Python program uses weighted random selection through the standard library. The JavaScript program performs cumulative probability sampling with `Math.random()`. The C++ program uses `std::discrete_distribution`.

The random mechanisms serve different purposes from cryptographic randomness. They model repeated measurement sampling and should not be interpreted as secure random-number generation.

The sampled counts are estimates of the ideal probability distribution. Increasing the number of shots generally makes the empirical frequencies approach the theoretical probabilities, although individual finite samples still fluctuate.

## Python Implementation

The Python program is organized around the `QuantumCircuit` class and small matrix/state-vector helper functions.

Circuit construction methods include `x`, `y`, `z`, `h`, `rx`, `ry`, `rz`, `cx`, and a general controlled-operation method. Each method validates qubit indices before recording an `Operation`.

The state-vector engine uses lists of complex numbers. The `apply_single_qubit_matrix` function locates pairs of amplitudes that differ in the selected target bit. The `apply_controlled_matrix` function performs the same matrix transformation only when the control bit is set.

The Python implementation also demonstrates:

- deterministic basis-state preparation with X gates
- superposition using H
- Bell-state construction
- parameterized rotations
- controlled-Z
- circuit composition by combining operation sequences
- probability normalization checks
- repeated measurement sampling
- invalid qubit and gate validation
- executable self-tests
- explicit state-vector memory scaling

The `draw` method provides a compact textual representation of the constructed circuit, while `describe` exposes the stored operation sequence and parameters.

The twelve-qubit limit is a practical safety boundary for the educational simulator. A state vector grows exponentially, so an unrestricted constructor could consume substantial memory as the number of qubits increases.

## JavaScript Implementation

The JavaScript implementation models the circuit as an event-driven object.

`CircuitEventBus` provides event registration and dispatch. `QuantumCircuit` emits events when operations are added and when asynchronous execution starts and finishes. This reflects an important engineering distinction between a local mathematical simulator and a circuit workflow that might submit work to a remote execution backend.

The JavaScript implementation also demonstrates circuit serialization. The `serialize` method stores circuit structure, operation names, qubit indices, and rotation parameters as JSON rather than serializing internal complex-number matrix objects.

This is a deliberate representation boundary. The serialized circuit contains enough information to reconstruct the operation sequence without coupling the external format to the simulator's internal matrix representation.

`executeAsync` introduces an asynchronous execution boundary. The implementation uses a scheduled event-loop yield rather than a real remote quantum backend, so the example demonstrates asynchronous workflow structure without pretending to perform hardware execution.

Validation is represented as a structured result containing `valid` and `errors`, while construction methods immediately reject invalid qubit references and non-finite rotation angles.

## C++ Case Study

The C++ implementation models a small circuit execution engine with typed `Operation` records.

An operation contains:

- an operation kind distinguishing single and controlled gates
- a gate name
- target and optional control indices
- a two-by-two complex matrix
- an optional rotation parameter

The `QuantumCircuit` class owns the ordered operation sequence and performs validation at construction time.

The case study uses a two-qubit Bell circuit as its primary end-to-end scenario. It constructs the circuit, prints its architecture, executes it, validates normalization, and generates a five-thousand-shot measurement sample.

A second three-qubit scenario demonstrates parameterized rotations combined with H, CX, CZ, and RZ operations. This provides a more complex circuit graph without introducing unrelated algorithms.

The program also contains a conservative optimization pass. Adjacent identical self-inverse gates are removed because:

`G * G = I`

for X, H, Z, CX, and CZ.

The optimizer does not reorder gates. This restriction is intentional because arbitrary gate reordering can change circuit semantics when operations do not commute.

After optimization, the program executes the circuit again and compares every amplitude with the pre-optimization state. This provides an explicit semantic-equivalence check rather than assuming that a shorter operation sequence is automatically correct.

## Circuit Construction Versus Execution

Circuit construction describes what should happen.

Execution determines the resulting state.

These concerns are deliberately separated in all three implementations.

Construction is responsible for:

- gate selection
- qubit targets
- control-target relationships
- operation ordering
- rotation parameters
- structural validation

Execution is responsible for:

- initializing the state
- applying operations
- maintaining amplitudes
- checking normalization
- deriving measurement probabilities

This separation also creates a natural location for transformations such as optimization, serialization, visualization, validation, or backend compilation before execution.

## Parameterized Circuit Construction

Parameterized gates introduce numerical values into circuit structure.

For a rotation gate, the angle determines the unitary transformation. The Python, JavaScript, and C++ implementations retain the angle in the operation representation while also constructing the corresponding matrix.

This matters when circuits are used as computational templates. A fixed architecture can be evaluated at many parameter values without changing which qubits are connected.

The implementations validate that rotation angles are finite. Rejecting `NaN` and infinite values early prevents invalid complex amplitudes from silently propagating through the state vector.

## Circuit Composition

Circuit composition means creating a larger operation sequence from smaller circuit fragments.

The Python program explicitly constructs a preparation circuit and a transformation circuit and combines their operations into a new circuit.

This demonstrates an important distinction between mathematical composition and textual concatenation. Combining circuits is only safe when qubit mappings and operation ordering are understood. A transformation intended for one register layout cannot simply be appended to a differently mapped register without accounting for that mapping.

The example therefore uses circuits with the same qubit count and convention.

## Validation and Failure Conditions

Circuit construction should reject invalid structures before execution.

The implementations check conditions such as:

- a register must contain at least one qubit
- a qubit index must be inside the register
- controlled gates require distinct control and target qubits
- rotation parameters must be finite
- measurement shots must be positive
- state vectors must have the expected dimension
- normalized states must have probability totals close to one

These checks prevent failures from appearing much later as incorrect measurement results.

A controlled gate with identical control and target is particularly important to reject. Treating the same physical qubit as both roles does not represent the intended controlled-operation semantics.

## Edge Cases

An empty circuit represents the initial all-zero state mathematically, although the JavaScript validation report flags it as an empty construction when structural validation is requested. The Python and C++ examples primarily use non-empty circuits for executable demonstrations.

Repeated self-inverse operations provide another useful edge case. Applying X twice returns a qubit to its original state. The C++ optimizer exploits this property only when the operations are adjacent and identical.

Parameter edge cases include zero rotation, which produces the identity transformation for the corresponding rotation family, and invalid non-finite parameters, which the implementations reject.

Very small amplitudes can appear because of floating-point arithmetic. The examples therefore use small numerical tolerances rather than requiring floating-point values to equal exact mathematical zeros.

## Performance Characteristics

The state-vector representation has exponential memory growth.

An `n`-qubit state requires `2^n` complex amplitudes. If each amplitude occupies approximately 16 bytes, the raw amplitude storage is approximately:

`16 * 2^n bytes`

before accounting for container overhead and other program memory.

Gate application over a state vector is generally proportional to the number of amplitudes for the direct implementation used here. Consequently, adding qubits has a much larger effect on simulator resource requirements than adding a small number of gates.

The programs intentionally cap the number of simulated qubits. The cap is not a theoretical property of quantum circuits. It is a protection for these educational state-vector implementations.

The C++ implementation additionally demonstrates a simple optimization that can reduce operation count without changing the state. Its optimization is deliberately conservative because more aggressive transformations require stronger reasoning about gate commutation and circuit semantics.

## Numerical Considerations

The simulators use floating-point complex arithmetic.

Quantum gate matrices are mathematically unitary, but finite-precision arithmetic introduces small numerical errors during repeated operations. This is why normalization and semantic-equivalence checks use tolerances.

A test such as `probability == 0.5` is inappropriate for arbitrary floating-point simulation results. Comparisons such as `abs(actual - expected) < epsilon` are more robust.

The same consideration applies to identifying zero amplitudes for display. The implementations suppress values below a small threshold instead of requiring exact equality with zero.

## Measurement Does Not Mean Reading Amplitudes Directly

The simulator exposes amplitudes for educational inspection, but a physical measurement produces a classical outcome sampled according to the probability distribution.

The distinction is important:

- The state vector represents the mathematical state used by the simulator.
- The probability distribution is derived from amplitude magnitudes.
- A measurement sample is one classical outcome.
- Repeated shots produce empirical frequencies.

Displaying a state vector should therefore not be interpreted as a physical measurement returning every amplitude.

## Common Construction Errors

### Incorrect qubit indexing

Mixing different conventions for mapping logical qubits to state-vector bits can make a circuit appear to work for some gates while producing incorrect multi-qubit behavior.

### Confusing target and control

For CX, the control determines whether the target transformation occurs. Reversing them changes the circuit.

### Ignoring operation order

Gate sequences are not generally interchangeable. A circuit constructed as `H` followed by `Z` is not automatically equivalent to `Z` followed by `H`.

### Treating probability as amplitude

An amplitude may be negative or complex. Probability is its squared magnitude, not the amplitude itself.

### Removing gates without proving equivalence

The C++ optimizer removes only adjacent identical self-inverse operations. Removing or reordering arbitrary gates requires a mathematical equivalence argument.

### Allowing invalid parameters to propagate

A non-finite rotation angle can produce invalid numerical values throughout a state vector. Validation at construction time gives a much clearer failure point.

## Architectural Relationships

The three implementations demonstrate complementary layers of a quantum-circuit system.

Circuit construction establishes an ordered operation graph over logical qubits.

Gate application translates each operation into transformations of amplitudes.

Measurement converts the resulting state into an observable probability distribution.

Validation protects the boundary between circuit description and execution.

Optimization can transform the operation sequence when equivalence can be demonstrated.

Serialization provides a representation that can cross process or system boundaries without exposing internal numerical structures.

Asynchronous execution, shown in JavaScript, represents the workflow required when circuit execution is not an immediate local function call.

The central relationship is therefore:

`circuit description -> validation -> optional transformation -> execution -> probability distribution -> measurement samples`

Each stage has a different responsibility, and keeping those responsibilities distinct makes the implementations easier to reason about and test.

## Practical Technical Boundaries

These programs are educational state-vector simulators. They do not model the complete behavior of a physical quantum processor.

They do not attempt to reproduce:

- hardware calibration
- gate noise
- decoherence
- readout error
- device topology constraints
- pulse-level control
- quantum error correction
- hardware-specific transpilation
- distributed quantum execution

The absence of these mechanisms is deliberate. The implementations focus on circuit construction fundamentals and the direct relationship between gate operations and an ideal state-vector model.

The resulting programs are useful for examining how a circuit is represented and transformed mathematically, while physical hardware introduces additional layers between an abstract circuit and a measured device outcome.
