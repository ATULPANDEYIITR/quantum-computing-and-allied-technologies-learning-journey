# SWAP & Controlled-SWAP: Multi-Qubit Operations

## 1. Topic Introduction

SWAP and controlled-SWAP are fundamental multi-qubit quantum operations.

The **SWAP gate** exchanges the quantum states of two target qubits. For two qubits, its computational-basis behavior is:

| Input | Output |
|---|---|
| `|00>` | `|00>` |
| `|01>` | `|10>` |
| `|10>` | `|01>` |
| `|11>` | `|11>` |

The **controlled-SWAP**, also called the **Fredkin gate**, adds a control qubit. The two target qubits are exchanged only when the control qubit is `|1>`.

For control `c` and targets `a` and `b`:

- `c = 0`: leave `a` and `b` unchanged.
- `c = 1`: exchange `a` and `b`.
- The control qubit itself is unchanged.

These operations are important because quantum computation frequently requires moving, routing, comparing, conditionally exchanging, and coherently manipulating information stored in different qubits.

The implementations in this repository model the gates using state vectors and computational-basis permutations.

---

## 2. Fundamental Quantum Concepts

### 2.1 Qubit

A classical bit is either `0` or `1`.

A qubit can be in a state represented as:

`|ψ> = α|0> + β|1>`

where `α` and `β` are complex probability amplitudes satisfying:

`|α|² + |β|² = 1`

The probabilities of observing `0` and `1` are `|α|²` and `|β|²`.

### 2.2 Computational Basis

For one qubit, the computational basis is:

- `|0>`
- `|1>`

For two qubits:

- `|00>`
- `|01>`
- `|10>`
- `|11>`

For three qubits there are eight basis states, from `|000>` through `|111>`.

In general, `n` qubits require `2^n` computational-basis states.

### 2.3 State Vectors

A two-qubit state can be represented as:

`[α00, α01, α10, α11]`

where each element is the amplitude associated with the corresponding basis state.

For example:

`|ψ> = (|01> + |10>) / √2`

has the vector:

`[0, 1/√2, 1/√2, 0]`

The Python, JavaScript, and C++ implementations explicitly store these amplitudes.

### 2.4 Normalization

A valid quantum state satisfies:

`Σ |αi|² = 1`

The implementations validate normalization and normalize constructed states where appropriate.

---

## 3. Multi-Qubit State Space

The dimension of an `n`-qubit state vector is:

`2^n`

Examples:

| Qubits | Amplitudes |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 10 | 1,024 |
| 20 | 1,048,576 |
| 30 | 1,073,741,824 |

This exponential state-space growth is the central reason classical full-state simulation becomes expensive.

The gates studied here operate on only two or three qubits, but a state-vector simulator must potentially move amplitudes throughout the complete `2^n`-element vector.

---

## 4. SWAP Gate

### 4.1 Definition

The SWAP gate exchanges two qubits.

If the first qubit contains state `A` and the second contains state `B`:

`SWAP(A, B) = (B, A)`

For basis states:

- `|00> → |00>`
- `|01> → |10>`
- `|10> → |01>`
- `|11> → |11>`

Only the middle two computational-basis states change.

### 4.2 Matrix Representation

Using the ordering:

`|00>, |01>, |10>, |11>`

the SWAP matrix is:

    [1 0 0 0]
    [0 0 1 0]
    [0 1 0 0]
    [0 0 0 1]

The matrix exchanges the amplitudes associated with `|01>` and `|10>`.

### 4.3 SWAP Is Reversible

Applying SWAP twice restores the original state:

`SWAP × SWAP = I`

Therefore:

`SWAP² = I`

This property is demonstrated by all three implementations.

### 4.4 SWAP Is Unitary

Quantum gates must preserve the norm of the quantum state.

Because SWAP only permutes amplitudes, it does not change:

`Σ |αi|²`

Therefore it preserves normalization and is unitary.

---

## 5. Controlled-SWAP / Fredkin Gate

### 5.1 Definition

The Fredkin gate contains:

- one control qubit
- two target qubits

The operation is:

`|0>|a>|b> → |0>|a>|b>`

and:

`|1>|a>|b> → |1>|b>|a>`

The control determines whether the target exchange occurs.

### 5.2 Basis-State Behavior

For qubit ordering `control, target1, target2`:

| Input | Output |
|---|---|
| `|000>` | `|000>` |
| `|001>` | `|001>` |
| `|010>` | `|010>` |
| `|011>` | `|011>` |
| `|100>` | `|100>` |
| `|101>` | `|110>` |
| `|110>` | `|101>` |
| `|111>` | `|111>` |

The first four states have control `0`, so they are unchanged.

The last four have control `1`, so the two target bits are exchanged.

### 5.3 Fredkin Is Reversible

The Fredkin gate is also self-inverse:

`Fredkin² = I`

Applying the same controlled-SWAP twice restores the original state.

---

## 6. Quantum Superposition and Controlled-SWAP

A classical conditional operation might first inspect the control value.

A quantum operation cannot generally do this without measurement consequences.

Suppose the input is:

`(|0>|01> + |1>|01>) / √2`

The control is in a superposition.

Applying controlled-SWAP produces:

`(|0>|01> + |1>|10>) / √2`

or, using three-qubit computational-basis labels:

`(|001> + |110>) / √2`

The gate therefore performs both conditional transformations coherently.

The Python, JavaScript, and C++ implementations explicitly demonstrate this transformation.

---

## 7. Measurement

Measurement converts a quantum state into an observed computational-basis result.

If a state is:

`|ψ> = Σ αi|i>`

then the probability of measuring basis state `|i>` is:

`Pi = |αi|²`

The total probability must be:

`Σ Pi = 1`

The implementations calculate these probabilities directly from complex amplitudes.

They also include random computational-basis sampling.

Measurement is intentionally kept separate from gate application. SWAP and controlled-SWAP transform amplitudes without requiring measurement.

---

## 8. Python Implementation

The Python implementation is designed as a broad educational simulator.

### 8.1 Complex Amplitudes

The implementation uses Python's built-in `complex` type.

This avoids an external numerical dependency while still allowing states such as:

`(1 + i)|01>`

to be represented directly.

### 8.2 State Validation

`validate_state()` checks:

- correct vector dimension
- normalization
- consistency between qubit count and vector length

For `n` qubits, the expected dimension is `2 ** n`.

### 8.3 Basis States

`basis_state("101")` constructs the state:

`|101>`

Only the amplitude corresponding to binary index `5` is nonzero.

### 8.4 Generic Permutation Engine

`apply_permutation()` provides the common mechanism used by SWAP and controlled-SWAP.

The gate supplies a mapping:

`source basis index → destination basis index`

The amplitude associated with the source is copied to the destination.

This is a natural implementation because both SWAP and controlled-SWAP are permutations of computational-basis states.

### 8.5 SWAP Implementation

`swap_gate()` delegates the basis-index transformation to `swap_basis_index()`.

The implementation first extracts the two selected bits.

If they are equal, no change is needed.

If they differ, the bits are exchanged.

This avoids constructing a large full matrix.

### 8.6 Controlled-SWAP Implementation

`controlled_swap_gate()` first reads the control bit.

If the control is `0`, the basis index remains unchanged.

If the control is `1`, the target bits are exchanged.

The operation is therefore a conditional permutation.

### 8.7 Entanglement Example

The Python script demonstrates the Bell state:

`|Φ+> = (|00> + |11>) / √2`

SWAP leaves this particular state unchanged.

The script also demonstrates the antisymmetric singlet:

`|Ψ-> = (|01> - |10>) / √2`

Under SWAP, the singlet becomes:

`-|Ψ->`

The negative sign is a global phase for the complete state and does not change computational-basis measurement probabilities.

The distinction is useful because a gate can have a nontrivial action even when it appears to leave one particular state physically indistinguishable from the original.

### 8.8 Circuit Abstraction

`QuantumCircuit` stores operations and executes them sequentially.

The circuit supports:

- SWAP
- controlled-SWAP

This demonstrates an important principle of quantum-circuit simulation: individual gates can be composed into larger transformations.

### 8.9 SWAP Decomposition

The Python implementation also demonstrates:

`SWAP(a,b) = CNOT(a,b) · CNOT(b,a) · CNOT(a,b)`

Depending on circuit notation conventions, operator order may be described from right to left or left to right. Operationally, the implementation applies the three CNOT operations in the listed execution sequence.

This decomposition matters because many quantum hardware platforms provide CNOT-like entangling operations as primitive or native gates while implementing SWAP from smaller components.

---

## 9. JavaScript Implementation

The JavaScript implementation provides a parallel executable state-vector simulator while emphasizing JavaScript-specific structure.

### 9.1 Complex Number Class

JavaScript does not have a built-in complex-number primitive equivalent to Python's `complex`.

The implementation therefore defines a `Complex` class with:

- `add()`
- `multiply()`
- `scale()`
- `magnitude()`
- `magnitudeSquared()`
- `toString()`

This makes the mathematical operations explicit.

### 9.2 Arrays as State Vectors

JavaScript arrays represent amplitude vectors.

For a two-qubit system:

`[α00, α01, α10, α11]`

is represented by an array containing four `Complex` objects.

### 9.3 Gate Functions

The JavaScript version contains explicit implementations of:

- `swapGate()`
- `controlledSwapGate()`
- `cnotGate()`

The gate functions use a common permutation engine.

### 9.4 Measurement

`measurementProbabilities()` converts amplitudes into probabilities.

`sampleMeasurement()` performs random sampling using cumulative probability intervals.

This models the probabilistic nature of computational-basis measurement.

### 9.5 Circuit Object

The `QuantumCircuit` class stores operations as objects.

For example, an operation contains:

- gate name
- target qubit indices

The circuit then executes each operation in sequence.

This resembles how application-level circuit representations can be constructed before execution.

---

## 10. C++ Case Study

The C++ implementation models a more structured technical scenario: a **coherent quantum-network routing unit**.

### 10.1 Problem Being Modeled

The router has three logical qubits:

- `q0`: routing decision
- `q1`: channel A
- `q2`: channel B

The routing policy is:

- when `q0 = 0`, preserve both channels
- when `q0 = 1`, exchange the two channels

A controlled-SWAP directly expresses this policy.

### 10.2 Architectural Structure

The C++ program is divided into several components.

#### `QuantumState`

Stores:

- qubit count
- complex amplitude vector

It provides:

- normalization
- basis-state construction
- uniform superposition construction
- probability calculation
- measurement
- formatted state output

#### Qubit Index Functions

`getBit()`, `replaceBit()`, and `swapBasisIndex()` convert between integer basis indices and individual qubit values.

This is important because state-vector simulators normally use integer indices rather than storing every basis state as a string.

#### Generic Permutation Engine

`applyPermutation()` provides the common implementation layer for reversible computational-basis operations.

#### Gate Functions

The program provides:

- `swapGate()`
- `controlledSwapGate()`
- `cnotGate()`

#### `QuantumCircuit`

This class stores and executes a sequence of operations.

It demonstrates modular circuit design rather than placing all gate behavior inside `main()`.

#### `QuantumRouter`

The router encapsulates a realistic use of controlled-SWAP.

Its `route()` method applies the Fredkin gate using:

- one control qubit
- two channel qubits

---

## 11. Router Case Study

The input state is:

`(|001> + |101>) / √2`

The control is the first bit.

For `|001>`:

- control = `0`
- targets = `01`
- targets remain `01`

Therefore:

`|001> → |001>`

For `|101>`:

- control = `1`
- targets = `01`
- targets become `10`

Therefore:

`|101> → |110>`

The final state is:

`(|001> + |110>) / √2`

This example demonstrates why controlled-SWAP is more than a classical conditional statement. The control itself can remain coherent, so the complete transformation operates on the superposition as one reversible quantum operation.

---

## 12. Important Distinction: Conditional Gate vs Measurement

A controlled-SWAP should not be confused with:

1. measuring the control
2. using a classical `if` statement
3. applying SWAP after measurement

Measurement changes the quantum state and removes coherence between the measurement outcomes.

A controlled-SWAP performs a unitary transformation without measuring the control.

Conceptually:

`CSWAP = |0><0| ⊗ I + |1><1| ⊗ SWAP`

This expression shows the two branches of the operation.

The projector `|0><0|` selects the no-SWAP branch.

The projector `|1><1|` selects the SWAP branch.

---

## 13. Matrix Structure of Controlled-SWAP

With basis ordering:

`|000>, |001>, |010>, |011>, |100>, |101>, |110>, |111>`

the Fredkin matrix is an `8 × 8` permutation matrix.

Its first four basis states are unchanged.

The `|101>` and `|110>` amplitudes are exchanged.

Thus the matrix has ones on the diagonal except for the two positions representing the exchange of `|101>` and `|110>`.

A permutation-matrix implementation is more efficient for this educational simulator than constructing and multiplying a full matrix.

---

## 14. SWAP as a Permutation

A useful implementation insight is that SWAP does not require general matrix multiplication.

For every computational-basis index:

1. extract the selected qubit values
2. exchange them
3. calculate the destination index
4. move the amplitude

This is especially useful in simulation code because a full matrix representation would contain many zero entries.

For a system of `n` qubits, a dense matrix representation of a full operator would require `2^n × 2^n` entries, while the permutation description requires only the gate logic.

The state vector still requires `2^n` amplitudes.

---

## 15. Gate Decomposition

SWAP can be constructed from three CNOT operations:

`CNOT(a,b)`

`CNOT(b,a)`

`CNOT(a,b)`

The sequence exchanges the logical values of the two target qubits.

This demonstrates an important concept in quantum compilation:

**A high-level gate does not necessarily correspond to one physical hardware operation.**

A compiler may translate a high-level gate into a sequence of native operations supported by a particular processor.

The exact cost depends on the hardware's available gate set and connectivity.

---

## 16. SWAP and Hardware Connectivity

Physical quantum processors may not support arbitrary direct interaction between every pair of qubits.

Suppose a circuit requires an operation between logical qubits that are not physically adjacent.

SWAP operations can move logical quantum states through the device's connectivity graph.

For example, with a linear topology:

`q0 — q1 — q2`

moving information between `q0` and `q2` may require intermediate routing.

SWAP is therefore important in:

- quantum circuit routing
- qubit mapping
- compiler optimization
- nearest-neighbor architectures
- distributed quantum processing

The cost is that additional gates increase circuit depth and may introduce additional physical error.

---

## 17. Controlled-SWAP Applications

Controlled-SWAP is useful as a building block for quantum algorithms and coherent conditional routing.

One important conceptual connection is the **SWAP test**.

The SWAP test uses:

- an ancilla/control qubit
- two quantum states
- a controlled-SWAP
- interference involving the control
- measurement of the control

The controlled-SWAP is therefore an important primitive for comparing quantum states.

The implementations here focus on the gate itself rather than implementing the complete SWAP test.

---

## 18. Entanglement and SWAP

SWAP does not automatically create entanglement.

It simply exchanges two quantum subsystems.

If two input qubits are separable:

`|a> ⊗ |b>`

SWAP produces:

`|b> ⊗ |a>`

which remains separable.

A gate can nevertheless act on an entangled state.

For example:

`|Φ+> = (|00> + |11>) / √2`

is symmetric under exchange:

`SWAP|Φ+> = |Φ+>`

The singlet state is antisymmetric:

`|Ψ-> = (|01> - |10>) / √2`

and satisfies:

`SWAP|Ψ-> = -|Ψ->`

These examples demonstrate the relationship between SWAP and symmetry under particle or subsystem exchange.

---

## 19. Global Phase

The singlet example illustrates global phase.

If:

`|ψ'> = e^(iφ)|ψ>`

then `|ψ>` and `|ψ'>` have identical measurement probabilities.

For `φ = π`:

`e^(iπ) = -1`

so:

`|ψ'> = -|ψ>`

The sign is not observable by itself.

This must be distinguished from **relative phase**, which can affect interference and therefore observable results.

---

## 20. Edge Cases

The implementations explicitly handle several important boundary conditions.

### 20.1 SWAP of a Qubit With Itself

`SWAP(q,q)` is the identity.

No two distinct quantum subsystems are being exchanged.

The implementations accept this as a mathematical identity case.

### 20.2 Invalid Fredkin Topology

A controlled-SWAP requires three distinct roles:

- control
- first target
- second target

Therefore a call such as:

`CSWAP(0,0,2)`

is rejected.

### 20.3 Invalid Qubit Index

A three-qubit circuit has valid indices:

`0, 1, 2`

An index of `3` is invalid.

The implementations explicitly validate these indices.

### 20.4 Invalid State Dimension

An `n`-qubit state must contain exactly `2^n` amplitudes.

A mismatch indicates an invalid state representation.

### 20.5 Unnormalized State

A physical state must have total probability one.

The implementations reject or normalize states as appropriate.

---

## 21. Common Mistakes

### Mistake 1: Treating SWAP as a Classical Variable Assignment

Quantum states contain amplitudes and can be entangled.

A complete implementation must operate on the full multi-qubit state representation rather than simply assigning two classical variables.

### Mistake 2: Forgetting the Control

Controlled-SWAP does not always exchange its targets.

The target exchange occurs only on the `|1>` branch of the control.

### Mistake 3: Measuring the Control to Implement a Conditional Operation

Measurement destroys coherence.

A controlled gate provides coherent conditional behavior without measurement.

### Mistake 4: Confusing Qubit Order

The implementation uses a clearly defined convention:

For `|q0 q1 q2>`, `q0` is the leftmost and most significant displayed bit.

A different simulator may use a little-endian convention.

This distinction must be established before interpreting integer state-vector indices.

### Mistake 5: Assuming Every High-Level Gate Is Physically Native

SWAP may be decomposed into lower-level gates.

The physical cost depends on hardware connectivity and the available native gate set.

### Mistake 6: Ignoring State-Space Growth

A local gate can be inexpensive conceptually while classical simulation remains expensive because the entire `2^n` state vector may need to be updated.

---

## 22. Performance Considerations

For an `n`-qubit state-vector simulator:

- number of amplitudes: `O(2^n)`
- state memory: `O(2^n)`
- direct SWAP simulation: `O(2^n)` time
- direct controlled-SWAP simulation: `O(2^n)` time

The implementations avoid dense matrix multiplication for these gates.

This is an important optimization because a two-qubit gate has a small local definition even when the complete system contains many qubits.

### Matrix-Based Approach

A generic matrix-vector multiplication for an `n`-qubit operator can be substantially more expensive when represented densely.

### Permutation Approach

SWAP and controlled-SWAP are computational-basis permutations, so the simulator can move amplitudes directly.

This reduces unnecessary arithmetic.

### Physical Quantum Hardware

A physical quantum processor does not classically store all `2^n` amplitudes.

The exponential state-vector representation is a property of the classical simulation model, not a requirement that a physical device explicitly store all amplitudes in classical memory.

---

## 23. Security and Reliability Considerations

Quantum gates themselves are mathematical transformations, but practical quantum systems introduce reliability concerns.

Relevant issues include:

- gate errors
- decoherence
- crosstalk
- readout errors
- connectivity restrictions
- calibration drift
- accumulated circuit depth

SWAP can be especially relevant to error budgets because routing may require multiple physical gates.

A compiler may therefore trade:

- fewer SWAP operations
- shorter circuit depth
- lower communication distance
- hardware-native gate usage

against other optimization objectives.

---

## 24. Python, JavaScript, and C++ Comparison

| Implementation | Primary Demonstration |
|---|---|
| Python | Mathematical clarity, state-vector simulation, extensive educational examples |
| JavaScript | Application-oriented implementation, explicit complex-number class, executable circuit model |
| C++ | Structured technical case study, modular architecture, explicit type design, performance-oriented implementation |

### Python

Python makes the mathematical structure compact and readable.

The script emphasizes:

- state manipulation
- validation
- circuit composition
- measurement
- gate decomposition
- conceptual experiments

### JavaScript

JavaScript demonstrates how the same concepts can be implemented without built-in complex-number support.

The custom `Complex` class makes arithmetic explicit.

The object-based circuit representation also resembles application-level data structures used by software systems.

### C++

C++ emphasizes explicit architecture and control over data structures.

The case study separates:

- quantum state representation
- gate operations
- circuit representation
- router abstraction
- validation
- execution

This structure is appropriate for a larger simulator or systems-oriented implementation.

---

## 25. Implementation Design Principles

Several general software engineering principles appear throughout the implementations.

### Separation of Concerns

State representation is separated from gate logic.

### Validation at Boundaries

Invalid qubit indices and invalid gate topologies are detected early.

### Reusable Gate Infrastructure

A generic permutation mechanism is reused by multiple gates.

### Deterministic Gate Behavior

SWAP and controlled-SWAP are deterministic transformations of amplitudes.

### Explicit Measurement

Measurement is represented as a separate operation rather than being mixed into gate application.

### Composition

Small gates are combined into circuits.

### Mathematical Verification

The programs verify properties such as:

- SWAP² = I
- Fredkin² = I
- norm preservation
- equivalence between direct SWAP and three-CNOT decomposition

---

## 26. Important Conceptual Relationships

### SWAP vs CNOT

CNOT conditionally flips one target qubit.

SWAP exchanges two qubits.

SWAP can be decomposed into three CNOT operations.

### SWAP vs Controlled-SWAP

SWAP always exchanges its two target qubits.

Controlled-SWAP exchanges them only for control state `|1>`.

### Controlled-SWAP vs Measurement

Controlled-SWAP provides coherent conditional behavior.

Measurement produces a classical outcome and changes the quantum state.

### State Vector vs Circuit Description

The state vector describes the current quantum state.

The circuit description describes the sequence of operations applied to that state.

### Logical Qubit vs Physical Qubit

A logical qubit represents the algorithmic information.

A physical qubit is a hardware resource.

SWAP operations can be used to map logical qubits onto physically connected hardware locations.

---

## 27. Production Implementation Considerations

A production-grade quantum simulator or compiler would require additional concerns beyond this educational implementation.

Important engineering areas include:

- sparse-state representations for suitable workloads
- tensor-network methods
- SIMD and vectorized arithmetic
- parallel execution
- GPU acceleration
- distributed state-vector simulation
- numerical precision management
- circuit optimization
- gate fusion
- hardware topology awareness
- noise modeling
- error correction
- fault-tolerant logical operations

These are separate implementation layers from the fundamental definition of SWAP and controlled-SWAP.

The essential mathematical behavior remains a reversible, norm-preserving transformation.

---

## 28. Core Formulas

### SWAP

`SWAP|a>|b> = |b>|a>`

### Controlled-SWAP

`CSWAP|0>|a>|b> = |0>|a>|b>`

`CSWAP|1>|a>|b> = |1>|b>|a>`

### Measurement Probability

`P(i) = |αi|²`

### Normalization

`Σi |αi|² = 1`

### SWAP Self-Inverse Property

`SWAP² = I`

### Fredkin Self-Inverse Property

`CSWAP² = I`

### SWAP Decomposition

`SWAP(a,b) = CNOT(a,b) → CNOT(b,a) → CNOT(a,b)`

---

## 29. Implementation Coverage

The Python implementation demonstrates:

- computational-basis states
- state normalization
- complex amplitudes
- SWAP
- controlled-SWAP
- measurement
- superposition
- Bell states
- singlet symmetry
- circuit composition
- CNOT decomposition
- validation
- edge cases
- complexity considerations

The JavaScript implementation demonstrates:

- explicit complex-number arithmetic
- array-based state vectors
- basis indexing
- SWAP
- controlled-SWAP
- measurement
- coherent control
- entangled-state symmetry
- CNOT decomposition
- circuit objects
- validation
- performance considerations

The C++ implementation demonstrates:

- a strongly typed state-vector abstraction
- computational-basis indexing
- generic permutation gates
- SWAP
- controlled-SWAP
- CNOT
- circuit composition
- a quantum-router abstraction
- coherent conditional routing
- measurement
- validation and exception handling
- algebraic verification
- resource analysis

The three implementations therefore represent the same underlying quantum operations at different software abstraction levels while preserving the same mathematical behavior.
