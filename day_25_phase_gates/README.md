# Phase Gates: S, T and Phase Operations

## 1. Topic Introduction

Quantum computation represents information using quantum states whose amplitudes are generally complex numbers. The magnitude of an amplitude determines its contribution to measurement probability, while its phase affects how amplitudes interfere with one another.

A **phase operation** changes the phase of one or more amplitudes without necessarily changing their immediate computational-basis probabilities.

The central single-qubit phase operation is the parameterized phase gate

`P(theta) = [[1, 0], [0, exp(i theta)]]`

For a qubit state

`|psi> = alpha|0> + beta|1>`

the operation produces

`P(theta)|psi> = alpha|0> + exp(i theta) beta|1>`

The probability magnitudes of the two computational-basis amplitudes are initially unchanged:

`|alpha|^2`

and

`|beta|^2`

The relative phase between the terms can nevertheless change the result of later interference operations.

This topic is therefore fundamental to understanding quantum circuits, interference, controlled operations, phase kickback, quantum Fourier transforms, and phase-estimation techniques.

---

## 2. Fundamental Quantum-State Concepts

### 2.1 Qubit

A classical bit has two possible logical values, 0 and 1.

A qubit can be represented as

`|psi> = alpha|0> + beta|1>`

where `alpha` and `beta` are complex amplitudes.

A valid pure quantum state satisfies

`|alpha|^2 + |beta|^2 = 1`

This is the normalization condition.

### 2.2 Computational basis

The computational basis consists of

`|0> = [1, 0]^T`

and

`|1> = [0, 1]^T`

The Python, JavaScript, and C++ implementations use vectors corresponding to these basis states.

### 2.3 Amplitude

An amplitude is a complex-valued coefficient associated with a basis state.

For example:

`|psi> = (1/sqrt(2))|0> + (i/sqrt(2))|1>`

has amplitudes

`alpha = 1/sqrt(2)`

and

`beta = i/sqrt(2)`.

### 2.4 Measurement probability

When measuring in the computational basis, the probability of observing a basis state is the squared magnitude of its amplitude.

For amplitude `alpha`:

`P(0) = |alpha|^2`

For amplitude `beta`:

`P(1) = |beta|^2`

The sum of all probabilities must be 1.

---

## 3. What Is Phase?

A complex number can be represented in polar form as

`z = r exp(i theta)`

where:

- `r` is the magnitude
- `theta` is the phase angle
- `i` is the imaginary unit
- `exp(i theta)` is a unit-magnitude complex rotation

Euler's identity gives

`exp(i theta) = cos(theta) + i sin(theta)`

A phase operation therefore multiplies an amplitude by a complex number lying on the unit circle.

For example:

`exp(i pi) = -1`

`exp(i pi/2) = i`

`exp(i pi/4) = (1+i)/sqrt(2)`

---

## 4. Global Phase and Relative Phase

This distinction is one of the most important ideas in quantum phase operations.

### 4.1 Global phase

Suppose

`|psi'> = exp(i phi)|psi>`

for some real `phi`.

Every amplitude receives the same phase factor.

The two states represent the same physical pure state because their measurement statistics and observable predictions are unchanged.

The Python implementation explicitly checks this using `global_phase_equivalent()`.

### 4.2 Relative phase

Consider

`|+> = (|0> + |1>)/sqrt(2)`

and

`|-> = (|0> - |1>)/sqrt(2)`.

The minus sign represents a relative phase difference of `pi`.

These states have identical computational-basis probabilities:

`P(0) = 1/2`

`P(1) = 1/2`

Yet they behave differently under another Hadamard operation.

`H|+> = |0>`

while

`H|-> = |1>`.

The phase has become observable through interference.

This is why saying that phase is irrelevant would be incorrect. Global phase is physically unobservable in this setting, while relative phase can directly affect future measurement outcomes.

---

## 5. General Phase Gate P(theta)

The parameterized phase gate is

`P(theta) = [[1, 0], [0, exp(i theta)]]`

Its action on basis states is

`P(theta)|0> = |0>`

and

`P(theta)|1> = exp(i theta)|1>`.

For

`|psi> = alpha|0> + beta|1>`

the result is

`alpha|0> + exp(i theta)beta|1>`.

The Python implementation defines this operation in `phase_gate(theta)`.

The JavaScript implementation defines it in `phaseGate(theta)`.

The C++ case study defines it in `phaseGate(double theta)`.

---

## 6. The Z Gate

The Pauli-Z gate is

`Z = [[1, 0], [0, -1]]`.

It is equivalent to a phase rotation of `pi`:

`Z = P(pi)`.

Its basis-state action is

`Z|0> = |0>`

and

`Z|1> = -|1>`.

Thus Z introduces a relative phase of `pi` between the computational-basis components.

---

## 7. The S Gate

The S gate is

`S = [[1, 0], [0, i]]`.

It is a phase gate with angle `pi/2`:

`S = P(pi/2)`.

Its basis-state action is

`S|0> = |0>`

and

`S|1> = i|1>`.

The S gate is sometimes called the phase gate.

Its powers demonstrate an important relationship:

`S^2 = Z`

`S^4 = I`.

The fourth power returns to the identity because four rotations of `pi/2` produce a total rotation of `2pi`.

---

## 8. The T Gate

The T gate is

`T = [[1, 0], [0, exp(i pi/4)]]`.

It therefore performs a phase rotation of `pi/4`.

Its powers satisfy

`T^2 = S`

`T^4 = Z`

`T^8 = I`.

The T gate is particularly important in quantum circuit design because it provides a finer phase rotation than Clifford gates such as H, S, and X.

The Python, JavaScript, and C++ programs explicitly verify these identities.

---

## 9. Adjoint and Inverse Phase Gates

A unitary gate has an inverse equal to its conjugate transpose.

For the phase gate,

`P(theta)^dagger = P(-theta)`.

Therefore:

`S^dagger = P(-pi/2)`

and

`T^dagger = P(-pi/4)`.

The inverse relationships are

`S S^dagger = I`

and

`T T^dagger = I`.

This reversibility is a fundamental property of quantum gates.

---

## 10. Why Quantum Gates Must Be Unitary

A quantum operation representing closed-system evolution must preserve the total probability.

For a gate `U`, unitarity requires

`U^dagger U = I`.

A unitary transformation preserves vector norms.

The implementations therefore contain explicit unitary checks.

The Python function is `is_unitary()`.

The JavaScript function is also `isUnitary()`.

The C++ implementation provides `isUnitary()`.

This is more than a mathematical convenience. Accepting an arbitrary non-unitary matrix as a quantum gate could produce an invalid state whose probabilities no longer sum to one.

---

## 11. Phase Does Not Necessarily Change Immediate Probability

Consider

`|+> = (|0> + |1>)/sqrt(2)`.

Applying T gives

`T|+> = (|0> + exp(i pi/4)|1>)/sqrt(2)`.

The amplitude magnitudes are still both `1/sqrt(2)`.

Therefore the computational-basis probabilities remain

`P(0) = 1/2`

and

`P(1) = 1/2`.

The state has nevertheless changed.

A later gate can convert that phase difference into a difference in measurement probabilities.

This distinction is demonstrated directly in all three implementations.

---

## 12. Interference

Interference occurs because complex amplitudes add before probabilities are calculated.

A useful circuit is

`H P(theta) H |0>`.

The first Hadamard creates

`|+> = (|0> + |1>)/sqrt(2)`.

The phase gate creates

`(|0> + exp(i theta)|1>)/sqrt(2)`.

The second Hadamard converts the phase relationship into computational-basis amplitudes.

The resulting probabilities are

`P(0) = cos^2(theta/2)`

and

`P(1) = sin^2(theta/2)`.

This relationship is demonstrated numerically by the `interference_experiment()` function in Python, `interferenceExperiment()` in JavaScript, and `phaseInterferenceExperiment()` in C++.

For important special cases:

- `theta = 0`: `P(0) = 1`
- `theta = pi/2`: `P(0) = P(1) = 1/2`
- `theta = pi`: `P(0) = 0`, `P(1) = 1`
- `theta = 2pi`: `P(0) = 1`

This demonstrates how a phase that is initially hidden from computational-basis probability measurement can become observable through interference.

---

## 13. Bloch-Sphere Interpretation

For a single qubit, a pure state can be visualized on the Bloch sphere.

A phase operation changes the azimuthal angle around the Z axis.

The general phase gate

`P(theta)`

therefore corresponds to a rotation around the Z axis, up to the conventional global-phase representation used when comparing it with rotation operators.

The important conceptual distinction is:

- X-like operations change population between basis states.
- Z/phase operations rotate relative phase.
- H changes the basis in which phase and amplitude relationships are represented.

This explains why a phase operation can leave computational-basis probabilities unchanged while still changing the future behavior of the state.

---

## 14. Tensor Products

A multi-qubit system is represented using tensor products.

For two qubits,

`|0> tensor |1> = |01>`.

The computational basis becomes

`|00>, |01>, |10>, |11>`.

A local operation on only the second qubit can be represented as

`I tensor T`.

The Python implementation provides `tensor_product()` and `tensor_matrix()`.

The JavaScript implementation provides `tensorProductVector()` and `tensorProductMatrix()`.

The C++ implementation overloads `tensorProduct()` for state vectors and matrices.

The tensor-product structure is essential because the dimension of an n-qubit state vector is `2^n`.

---

## 15. Controlled Phase Operations

A controlled phase gate applies a phase only when a control condition is satisfied.

For a two-qubit controlled phase operation,

`CP(theta) = diag(1, 1, 1, exp(i theta))`.

Using the basis ordering

`|00>, |01>, |10>, |11>`,

only `|11>` receives the phase factor.

For `theta = pi`:

`CP(pi) = diag(1, 1, 1, -1)`

which is the controlled-Z gate.

For `theta = pi/4`, the operation is controlled-T.

The implementations provide a general controlled phase function rather than hard-coding only one special case.

---

## 16. Phase Kickback

Phase kickback is a mechanism in which a controlled operation causes phase information to appear in another part of a quantum state.

Suppose a target state is an eigenstate of an operation U:

`U|u> = lambda|u>`.

If the control determines whether U is applied, the eigenvalue can become a phase factor associated with the control component.

This mechanism is important in quantum algorithms and is closely connected with phase estimation.

The examples use controlled-Z as an accessible illustration.

---

## 17. QFT-Style Phase Rotations

The Quantum Fourier Transform uses controlled phase rotations with progressively smaller angles.

A common sequence uses angles related to

`pi/2`

`pi/4`

`pi/8`

`pi/16`

and so on.

The Python implementation calculates these angles through `qft_phase_angle()`.

The JavaScript implementation generates the corresponding values in `demonstrateQFTPhases()`.

The exact circuit structure of a complete QFT involves Hadamard gates, controlled rotations, qubit ordering, and often final swaps. The implementations focus specifically on the phase-rotation component relevant to this topic.

---

## 18. Phase-Gate Algebra

Because phase gates are diagonal in the computational basis, they commute with one another.

For example,

`P(a)P(b) = P(b)P(a) = P(a+b)`,

where the angle is interpreted modulo `2pi`.

This property applies to S and T because both are special cases of P(theta).

Thus

`ST = TS`.

By contrast, phase gates generally do not commute with H.

For example,

`HZ != ZH`.

The order of gates therefore matters when phase operations are combined with basis-changing operations.

The implementations explicitly compare different gate orders.

---

## 19. Circuit Composition

If a circuit executes

`G1`

followed by

`G2`

followed by

`G3`,

the resulting matrix is

`G3 G2 G1`.

Matrix multiplication therefore appears in reverse textual execution order when the complete operation is written as one matrix.

The `SingleQubitCircuit` class in Python, `SingleQubitCircuit` class in JavaScript, and `QuantumCircuit` class in C++ maintain an ordered list of operations and construct the combined circuit matrix accordingly.

This is an important implementation detail because reversing the multiplication order produces a different circuit.

---

## 20. Python Implementation

The Python script is designed as an executable study environment.

### Complex arithmetic

Python's built-in `complex` type represents quantum amplitudes without requiring an external numerical package.

Functions such as `format_complex()` make complex amplitudes readable.

### State handling

The script provides:

- `vector_norm()`
- `normalize_state()`
- `validate_state()`
- `probabilities()`

These establish the basic invariants required for state-vector simulation.

### Matrix handling

The script implements:

- matrix multiplication
- matrix-vector multiplication
- conjugate transpose
- identity matrices
- matrix powers
- unitary checks

This allows the phase-gate examples to remain self-contained.

### Gate construction

The central function is `phase_gate(theta)`.

The specialized gates are derived from it:

- `s_gate()`
- `t_gate()`
- `s_dagger_gate()`
- `t_dagger_gate()`

This is preferable to treating S and T as unrelated hard-coded concepts because it demonstrates their mathematical relationship to the general phase operation.

### Advanced examples

The Python implementation also includes:

- controlled phase gates
- tensor products
- phase kickback
- QFT phase angles
- phase oracles
- parameterized circuits
- measurement sampling
- numerical validation
- self-tests

---

## 21. JavaScript Implementation

The JavaScript implementation uses a custom `Complex` class because JavaScript does not have a built-in general-purpose complex-number primitive.

The class supports:

- addition
- subtraction
- multiplication
- conjugation
- magnitude
- squared magnitude
- phase
- polar conversion

This provides the mathematical foundation required by the quantum-state simulator.

### Why JavaScript is useful here

JavaScript is particularly relevant when quantum concepts need to be connected to application-level software.

A browser implementation could use the same principles to build:

- interactive circuit editors
- phase visualizers
- Bloch-sphere interfaces
- state-vector inspection tools
- measurement dashboards
- educational circuit simulators

The supplied file remains runtime-independent and does not require browser APIs or external npm packages.

### Error handling

The JavaScript code validates:

- empty states
- normalization
- matrix dimensions
- unitary gates
- invalid measurement shot counts

It also includes deterministic measurement sampling for reproducible demonstrations.

---

## 22. C++ Case Study

The C++ implementation models a programmable quantum signal-processing pipeline.

The scenario is:

1. Prepare an initial qubit.
2. Create a superposition using H.
3. Apply T.
4. Apply a programmable phase rotation.
5. Apply S-dagger.
6. Apply another H.
7. Inspect the final measurement probabilities.
8. Demonstrate controlled phase behavior.
9. Apply a two-qubit phase oracle.
10. Perform repeated measurement simulation.
11. Sweep the phase angle and observe interference.

### Architecture

The implementation separates responsibilities into several components.

#### Matrix operations

The functions `matrixMultiply()`, `matrixVectorMultiply()`, `conjugateTranspose()`, and `isUnitary()` provide the linear-algebra layer.

#### Quantum states

`State` is an alias for a vector of complex amplitudes.

The state layer validates normalization and calculates measurement probabilities.

#### Gate layer

The functions

- `XGate()`
- `YGate()`
- `ZGate()`
- `HGate()`
- `phaseGate()`
- `SGate()`
- `TGate()`
- `SDaggerGate()`
- `TDaggerGate()`

represent the gate library.

#### Controlled operations

`controlledPhaseGate()` models two-qubit conditional phase behavior.

#### Circuit layer

`QuantumCircuit` stores operations, validates gates, executes them in sequence, and constructs the combined unitary matrix.

#### Phase oracle

`TwoQubitPhaseOracle` demonstrates a more general diagonal unitary in which each computational-basis state can receive an independently specified phase.

---

## 23. Why the Three Implementations Differ

The implementations intentionally do not simply duplicate one another.

### Python

Python emphasizes mathematical readability, experimentation, and rapid construction of a simulator.

It is particularly convenient for exploring:

- complex arithmetic
- state-vector calculations
- matrix operations
- numerical experiments
- parameter sweeps
- educational simulations

### JavaScript

JavaScript emphasizes application-level execution and implements complex arithmetic explicitly.

It provides a natural foundation for browser-based visualizations and interactive quantum-circuit applications.

### C++

C++ emphasizes a structured technical case study with explicit data structures, classes, validation, deterministic measurement, and performance awareness.

C++ is also useful when simulation performance, memory layout, deterministic execution, and low-level control become important.

The underlying mathematics is the same, but the implementation concerns differ.

---

## 24. Edge Cases

### 24.1 Zero vector

The vector

`[0, 0]`

cannot represent a normalized quantum state.

Attempting to normalize it is therefore an error.

All three implementations reject this situation.

### 24.2 Unnormalized state

The vector

`[1, 1]`

has norm `sqrt(2)` and therefore does not directly represent a normalized state.

It can be normalized to

`[1/sqrt(2), 1/sqrt(2)]`.

### 24.3 Non-unitary matrix

The matrix

`[[1, 0], [0, 2]]`

is not unitary.

Using it as a reversible quantum gate would violate the expected norm-preservation property.

The implementations reject arbitrary non-unitary gates.

### 24.4 Floating-point equality

Numerical calculations use floating-point values.

Therefore expressions that are mathematically identical may differ by tiny numerical errors.

The implementations use tolerance-based comparisons rather than relying exclusively on exact equality.

### 24.5 Phase periodicity

Phase angles are periodic modulo `2pi`.

For example,

`P(theta) = P(theta + 2pi)`.

Consequently, large accumulated phase values can be reduced modulo `2pi` when an application only requires the corresponding unitary phase factor.

---

## 25. Common Mistakes

### Mistake 1: Treating phase as measurement probability

A phase factor has unit magnitude.

Multiplying an amplitude by a phase does not change its magnitude.

It can still affect future interference.

### Mistake 2: Treating global phase as relative phase

Multiplying every amplitude by the same phase factor produces a global phase.

Changing only one component relative to another changes the relative phase.

These have different physical consequences.

### Mistake 3: Assuming phase gates always change immediate probabilities

A diagonal phase gate can leave computational-basis probabilities unchanged.

Its effect may only become visible after another operation changes the measurement basis.

### Mistake 4: Reversing matrix multiplication order

If `A` executes first and `B` executes second, the combined transformation is

`BA`.

It is not generally `AB`.

### Mistake 5: Ignoring normalization

A state-vector simulator must preserve normalization under valid unitary operations.

### Mistake 6: Using arbitrary matrices as quantum gates

Not every matrix represents a valid closed-system quantum gate.

Unitarity is the required mathematical condition.

### Mistake 7: Confusing controlled phase with ordinary phase

An ordinary phase gate acts on one qubit.

A controlled phase gate applies the phase conditionally according to the control and target states.

---

## 26. Important Distinctions

| Concept | Meaning |
|---|---|
| Amplitude | Complex coefficient of a basis state |
| Magnitude | Size of a complex amplitude |
| Probability | Squared magnitude of an amplitude |
| Global phase | Same phase factor applied to the complete state |
| Relative phase | Phase difference between components |
| P(theta) | General single-qubit phase gate |
| Z | P(pi) |
| S | P(pi/2) |
| T | P(pi/4) |
| S-dagger | P(-pi/2) |
| T-dagger | P(-pi/4) |
| Controlled phase | Phase applied conditionally |
| Interference | Amplitude combination that makes phase observable |
| Unitary | Norm-preserving reversible linear transformation |

---

## 27. S, T, and Z Relationship

The three gates form a simple hierarchy of phase rotations:

`T = P(pi/4)`

`S = P(pi/2) = T^2`

`Z = P(pi) = T^4`

and

`T^8 = I`.

This relationship is explicitly tested by the supplied programs.

The identity does not mean that all eight intermediate applications are physically irrelevant. Each intermediate phase can change interference when combined with other gates.

---

## 28. Controlled Phase and Entanglement

A controlled phase gate is diagonal and therefore does not necessarily change computational-basis probabilities immediately.

When acting on an appropriate superposition, it can change relative phases between joint basis states.

When combined with other gates, these phase differences can produce entanglement and observable interference effects.

For example, controlled-Z is central to many quantum circuit constructions.

A key implementation point is that a two-qubit state has four amplitudes, so a controlled phase gate is represented by a `4 x 4` matrix in the basic state-vector representation.

---

## 29. Phase Oracles

A phase oracle can encode information in phases instead of directly marking computational-basis probabilities.

For two qubits, a diagonal oracle can be represented as

`diag(exp(i theta_00), exp(i theta_01), exp(i theta_10), exp(i theta_11))`.

The C++ case study implements this idea through `TwoQubitPhaseOracle`.

This is useful for understanding the architecture of algorithms where information is encoded in phase and later extracted through interference.

---

## 30. Performance Considerations

For `n` qubits, a state vector contains

`2^n`

complex amplitudes.

This exponential growth is one of the main computational constraints of classical state-vector simulation.

A full dense operator over `n` qubits has dimension

`2^n x 2^n`

and therefore contains

`4^n`

matrix elements.

Naive dense matrix-vector multiplication consequently becomes extremely expensive.

For local gates, a simulator should generally avoid materializing a complete dense matrix whenever possible.

A production simulator may instead:

- update only affected amplitudes
- exploit tensor-product structure
- use sparse representations
- use specialized kernels
- exploit SIMD or GPU hardware
- avoid unnecessary state copies
- track qubit ordering carefully

The supplied implementations deliberately use straightforward dense representations because they are intended to make the mathematics visible.

---

## 31. Numerical Precision

Quantum simulators normally use floating-point arithmetic.

Important consequences include:

- tiny residual imaginary values may appear where exact mathematics gives zero
- repeated operations accumulate rounding error
- matrix equality should use tolerances
- normalization should be checked with a tolerance
- large circuits may accumulate more numerical error than small circuits

The examples use approximately `1e-9` or `1e-10` tolerance values for educational validation.

A production implementation should choose tolerances based on numerical precision, circuit depth, algorithm sensitivity, and required accuracy.

---

## 32. Security and Reliability Considerations

A quantum simulator is software and should still validate external inputs.

Relevant safeguards include:

- checking matrix dimensions
- checking normalization
- checking gate unitarity
- rejecting invalid shot counts
- validating the number of phases in multi-qubit phase oracles
- keeping circuit execution separate from input parsing
- avoiding unchecked assumptions about qubit ordering
- using deterministic random seeds for reproducible tests
- using secure randomness where randomness itself is security-sensitive

The deterministic random generators in the educational examples are intended for reproducibility, not cryptographic security.

A deterministic simulator should not be interpreted as a physical quantum random-number generator.

---

## 33. Implementation Considerations

A useful phase-operation simulator should make several design choices explicit.

### State ordering

For two qubits, the examples use

`|00>, |01>, |10>, |11>`.

Different frameworks can choose different conventions, so state ordering must be documented.

### Operator convention

The examples treat states as column vectors and apply gates from the left.

### Gate validation

Arbitrary matrices are checked for unitarity before being accepted as gates.

### Measurement

Measurement probabilities are calculated as squared amplitude magnitudes.

The examples then use classical random sampling to simulate repeated measurements.

### Circuit composition

The complete circuit matrix is constructed in the mathematical execution order:

`U_total = U_last ... U_second U_first`.

---

## 34. Advanced Relationship to Rotation Operators

The phase gate is closely related to the Z-axis rotation operator

`Rz(theta) = exp(-i theta Z / 2)`.

Using the diagonal form of Z,

`Rz(theta) = diag(exp(-i theta/2), exp(i theta/2))`.

The phase gate satisfies

`P(theta) = exp(i theta/2) Rz(theta)`.

The difference is the global phase factor

`exp(i theta/2)`.

Thus P(theta) and Rz(theta) have the same physically relevant relative-phase rotation, even though their matrices differ by a global phase.

This relationship is important when comparing gate libraries and circuit decompositions.

---

## 35. Phase Gates and Clifford Structure

The S gate is a Clifford operation.

The T gate is not a Clifford gate.

This distinction matters in fault-tolerant quantum computing because Clifford operations alone have important classical-simulation properties, while adding suitable non-Clifford operations such as T enables more general quantum computation.

The T gate therefore has a particularly important role in quantum circuit synthesis and fault-tolerant architectures.

The supplied code does not attempt to implement a fault-tolerant error-correction stack, but the algebraic relationships among T, S, and Z provide the required phase-gate foundation.

---

## 36. Phase Accumulation

Repeated application of a phase gate produces accumulated phase.

For example,

`T|1> = exp(i pi/4)|1>`

`T^2|1> = exp(i pi/2)|1>`

`T^4|1> = exp(i pi)|1> = -|1>`

`T^8|1> = exp(i 2pi)|1> = |1>`.

The Python program demonstrates this numerically.

The same principle is relevant to phase estimation, eigenvalue estimation, controlled-unitary circuits, and Fourier-transform-based algorithms.

---

## 37. Practical Applications

Phase operations are used as building blocks in:

- quantum Fourier transform circuits
- phase estimation
- controlled-unitary constructions
- quantum simulation
- interference-based algorithms
- quantum signal processing
- quantum amplitude transformations
- fault-tolerant gate synthesis
- variational quantum circuits
- quantum error-correction circuits
- phase-oracle constructions

Their significance comes less from changing immediate probabilities and more from controlling relative phase so that later interference produces useful information.

---

## 38. What the Executable Tests Establish

The three programs contain direct tests for several mathematical identities.

They verify:

`S^2 = Z`

`T^2 = S`

`T^4 = Z`

`T^8 = I`

`S S-dagger = I`

`T T-dagger = I`

They also verify that:

- H is unitary
- X is unitary
- Y is unitary
- Z is unitary
- S is unitary
- T is unitary
- controlled phase operations are unitary
- phase information can become measurable through interference

These tests connect the theoretical definitions directly to executable behavior.

---

## 39. C++ Case-Study Flow

The C++ implementation follows a progressively developed system:

1. Construct fundamental gates.
2. Validate their unitarity.
3. Verify S and T algebraic identities.
4. Prepare a superposition.
5. Apply a phase operation.
6. Convert phase into measurable interference.
7. Build a programmable circuit.
8. Execute the circuit.
9. Construct the combined circuit matrix.
10. Apply a controlled phase operation.
11. Construct a two-qubit phase oracle.
12. Simulate repeated measurement.
13. Sweep phase angles.
14. Run self-tests.
15. Report state-vector scaling.

This structure demonstrates how a mathematical concept can become a reusable software component.

---

## 40. Core Equations

### General phase gate

`P(theta) = [[1, 0], [0, exp(i theta)]]`

### Z gate

`Z = P(pi)`

### S gate

`S = P(pi/2)`

### T gate

`T = P(pi/4)`

### Inverses

`S-dagger = P(-pi/2)`

`T-dagger = P(-pi/4)`

### Powers

`S^2 = Z`

`T^2 = S`

`T^4 = Z`

`T^8 = I`

### Controlled phase

`CP(theta) = diag(1, 1, 1, exp(i theta))`

### Interference

For `H P(theta) H |0>`:

`P(0) = cos^2(theta/2)`

`P(1) = sin^2(theta/2)`

### State-vector size

`n qubits -> 2^n amplitudes`

### Dense operator size

`n qubits -> 2^n x 2^n matrix`

---

## 41. File Execution

The Python implementation can be executed with a standard Python 3 installation because it relies on the standard library.

The JavaScript implementation can be executed in a modern Node.js runtime.

The C++ implementation targets C++17 or later and uses only standard-library facilities.

The three implementations are deliberately self-contained so that the mathematical behavior of S, T, and general phase operations can be inspected without a quantum-computing framework.
