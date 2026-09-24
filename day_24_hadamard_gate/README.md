# Hadamard Gate: Creating Superposition

## Topic introduction

The Hadamard gate is one of the fundamental single-qubit gates in quantum computing. Its most important educational role is transforming a computational-basis state into a balanced superposition.

For the computational basis,

- `|0>` represents the state vector `[1, 0]`.
- `|1>` represents the state vector `[0, 1]`.

The Hadamard gate is represented by the matrix

    H = 1/sqrt(2) [[1, 1],
                   [1, -1]]

Its action on the basis states is

    H|0> = (|0> + |1>) / sqrt(2)

and

    H|1> = (|0> - |1>) / sqrt(2)

The first transformation creates the state commonly called `|+>`, while the second creates `|->`.

The important point is that a quantum state is described using amplitudes. Measurement probabilities are obtained from the squared magnitudes of those amplitudes. The Hadamard gate therefore does not simply convert a classical bit into an ordinary random bit. It creates a coherent quantum state whose amplitudes can later interfere.

## Fundamental concepts

### Qubit

A qubit is the basic unit of quantum information.

A general pure single-qubit state can be written as

    |psi> = alpha|0> + beta|1>

where `alpha` and `beta` are generally complex numbers.

A valid normalized state satisfies

    |alpha|^2 + |beta|^2 = 1

The Python and JavaScript implementations represent these amplitudes explicitly. The C++ implementation extends the same idea to a complete state vector for multiple qubits.

### Computational basis

The computational basis consists of `|0>` and `|1>` for a single qubit.

For a two-qubit system, the basis is

    |00>
    |01>
    |10>
    |11>

For `n` qubits, there are `2^n` computational-basis states.

This exponential growth is directly reflected in the state-vector simulators implemented in Python, JavaScript, and C++.

### Amplitude

An amplitude is a complex coefficient associated with a basis state.

For

    |psi> = alpha|0> + beta|1>

`alpha` is the amplitude of `|0>` and `beta` is the amplitude of `|1>`.

An amplitude itself is not a probability.

### Born rule

The probability of observing a basis state is the squared magnitude of its amplitude.

For a single-qubit state,

    P(0) = |alpha|^2
    P(1) = |beta|^2

The implementations calculate these values explicitly rather than treating amplitudes as probabilities.

### Superposition

A state is in superposition with respect to a chosen basis when multiple basis states have nonzero amplitudes.

For example,

    |+> = (|0> + |1>) / sqrt(2)

contains nonzero amplitudes for both `|0>` and `|1>`.

Measurement in the computational basis produces `0` or `1` with equal probability.

Superposition should not be interpreted as classical uncertainty. The amplitudes possess phase information that can participate in interference.

## The Hadamard transformation

The Hadamard matrix is

    H = 1/sqrt(2) [[1, 1],
                   [1, -1]]

For an arbitrary single-qubit state,

    |psi> = alpha|0> + beta|1>

the Hadamard transformation produces

    H|psi> =
        ((alpha + beta) / sqrt(2))|0>
        +
        ((alpha - beta) / sqrt(2))|1>

This formula is implemented directly in all three programming languages.

The Python `Qubit.apply_hadamard()` method performs these two amplitude calculations.

The JavaScript `Qubit.hadamard()` method performs the same transformation while using a custom `Complex` class because JavaScript does not provide a native complex-number primitive.

The C++ `QuantumRegister::applyHadamard()` method applies the same transformation to every appropriate pair of amplitudes in an `n`-qubit state vector.

## H|0>

Starting with

    |0> = [1, 0]

the Hadamard operation gives

    H|0> = 1/sqrt(2) [1, 1]

or

    H|0> = (|0> + |1>) / sqrt(2)

The amplitudes are

    alpha = 1/sqrt(2)
    beta  = 1/sqrt(2)

Therefore,

    P(0) = 1/2
    P(1) = 1/2

This is the principal superposition example demonstrated in the Python and JavaScript programs.

## H|1>

Starting with

    |1> = [0, 1]

the Hadamard operation gives

    H|1> = 1/sqrt(2) [1, -1]

or

    H|1> = (|0> - |1>) / sqrt(2)

The measurement probabilities are still

    P(0) = 1/2
    P(1) = 1/2

but the relative sign between the amplitudes is different.

That difference is important even though a computational-basis measurement immediately after the gate cannot distinguish the two states through their probabilities alone.

## Relative phase

The states

    |+> = (|0> + |1>) / sqrt(2)

and

    |-> = (|0> - |1>) / sqrt(2)

have identical computational-basis measurement probabilities.

The difference is their relative phase.

The implementations demonstrate that applying another Hadamard exposes this distinction:

    H|+> = |0>

and

    H|-> = |1>

The second transformation causes amplitudes to add or cancel. This is a basic example of quantum interference.

## Global phase

A global phase multiplies every amplitude in a state by the same complex phase factor.

For example,

    |psi>
    
and

    i|psi>

produce identical measurement probabilities.

The JavaScript implementation explicitly demonstrates this distinction using states whose amplitudes differ by a global phase.

Global phase is not directly observable through ordinary measurement statistics. Relative phase between components of a superposition can affect subsequent interference.

## Measurement

Quantum measurement converts a probability distribution over basis states into an actual observed result.

For

    |+> = (|0> + |1>) / sqrt(2)

one measurement produces either `0` or `1`.

The probability distribution is

    P(0) = 0.5
    P(1) = 0.5

Repeated measurements reveal the distribution statistically.

The Python implementation performs thousands of simulated measurements. The JavaScript implementation does the same with a deterministic pseudo-random generator for reproducibility.

The C++ implementation performs repeated Bell-state measurements.

## Measurement collapse

The state-vector implementations explicitly model measurement collapse.

If the outcome is `|0>`, the post-measurement state becomes

    |0>

If the outcome is `|1>`, the post-measurement state becomes

    |1>

This is why each measurement shot in the simulation starts with a freshly prepared state when estimating a probability distribution.

Repeatedly measuring an already collapsed state does not reproduce the original superposition distribution.

## Hadamard is self-inverse

A fundamental property of the Hadamard gate is

    H^2 = I

where `I` is the identity matrix.

Therefore,

    H(H|0>) = |0>

and

    H(H|1>) = |1>

The three implementations verify this property programmatically.

The Python implementation performs explicit assertions.

The JavaScript implementation uses correctness checks.

The C++ implementation checks the resulting state-vector amplitudes.

This property also follows from the fact that the Hadamard matrix is real, symmetric, and unitary.

## Unitarity

Quantum gates acting on closed quantum systems are represented by unitary transformations.

A matrix `U` is unitary when

    U†U = I

where `U†` is the conjugate transpose.

The Hadamard matrix is unitary, so it preserves the norm of a quantum state.

Before the transformation,

    sum |amplitude_i|^2 = 1

After the transformation,

    sum |amplitude_i'|^2 = 1

The simulators use normalization validation to detect implementation errors.

## Python implementation

The Python program begins with the simplest possible representation of a qubit:

    Qubit(alpha, beta)

The object stores the amplitude of `|0>` and the amplitude of `|1>`.

The `validate()` method enforces normalization.

The `probabilities()` method applies the Born rule.

The `apply_hadamard()` method implements

    alpha' = (alpha + beta) / sqrt(2)
    beta'  = (alpha - beta) / sqrt(2)

The Python implementation also includes Pauli-X and Pauli-Z operations so that the role of phase and gate composition can be examined.

### Python measurement

The `measure()` method calculates the probability of `0`, samples an outcome, and then collapses the qubit to the corresponding basis state.

A copy of a prepared state is used for every independent measurement shot when estimating a probability distribution.

### Python multi-qubit simulation

The `QuantumRegister` class represents an `n`-qubit state using a list of `2^n` complex amplitudes.

For two qubits, the state vector contains four amplitudes:

    [a_00, a_01, a_10, a_11]

For three qubits, it contains eight amplitudes.

The simulator applies a Hadamard gate by processing pairs of basis states that differ only at the selected qubit.

The implementation also includes CNOT, which makes it possible to demonstrate entanglement.

### Python validation

The program explicitly rejects:

- non-normalized single-qubit states
- negative qubit indices
- out-of-range qubit indices
- CNOT operations with identical control and target qubits
- excessively large educational simulation registers

These checks are important because state-vector simulations can consume exponentially increasing amounts of memory.

## JavaScript implementation

The JavaScript implementation uses a custom `Complex` class.

The class provides:

- addition
- subtraction
- multiplication
- magnitude
- squared magnitude
- approximate equality
- formatted output

The implementation uses immutable-style operations that return new `Complex` values instead of modifying an existing complex number.

### JavaScript Hadamard implementation

The `Qubit.hadamard()` method performs the same mathematical transformation as the Python implementation.

JavaScript-specific concerns are visible in the explicit handling of complex numbers and numeric tolerance.

JavaScript's ordinary `Number` type uses IEEE 754 floating-point arithmetic, so exact equality should generally not be expected for calculated quantum amplitudes.

The `assertClose()` and `assertComplexClose()` helpers therefore use tolerances.

### JavaScript state-vector simulator

The `QuantumRegister` class represents a multi-qubit state using an array of complex amplitudes.

The `hadamard()` method uses bit masks to identify pairs of basis-state indices.

For example, with two qubits, changing one selected bit maps one basis state to another. The bit-mask approach avoids constructing a complete `2^n × 2^n` matrix for every gate.

This is substantially more memory-efficient than explicitly materializing the complete operator matrix.

## C++ case study

The C++ implementation models an industry-style quantum circuit execution component.

The central problem is:

1. Create a quantum register.
2. Build a sequence of gates.
3. Execute the circuit.
4. Inspect amplitudes and probabilities.
5. Perform measurements.
6. Validate mathematical invariants.
7. Handle invalid circuit operations safely.

The main architectural components are `QuantumRegister`, `GateOperation`, and `QuantumCircuit`.

### QuantumRegister

`QuantumRegister` owns the state vector.

It is responsible for:

- qubit-count validation
- state-vector storage
- basis-state labels
- normalization checks
- Hadamard operations
- Pauli-X operations
- Pauli-Z operations
- CNOT operations
- measurement
- probability extraction

The state starts in

    |00...0>

because the first amplitude is `1` and all other amplitudes are `0`.

### QuantumCircuit

`QuantumCircuit` stores a sequence of gate operations.

A gate is represented by a `GateOperation` containing a gate type and one or two qubit indices.

The circuit is executed against a newly initialized register.

This separates circuit description from state execution.

The separation is useful because the same circuit description can be executed repeatedly for independent measurement shots.

## Bell-state case study

The C++ case study constructs the Bell state using

    H on q0
    CNOT with q0 as control and q1 as target

Starting from

    |00>

the first operation creates

    (|00> + |10>) / sqrt(2)

under the implementation's qubit-ordering convention.

The CNOT then produces

    (|00> + |11>) / sqrt(2)

The exact printed basis labels are controlled by the documented least-significant-bit convention.

The resulting probabilities are

    P(00) = 1/2
    P(11) = 1/2
    P(01) = 0
    P(10) = 0

This is an entangled Bell state.

The important conceptual distinction is that two independently generated random bits would not possess the same quantum-state structure. The Bell state contains coherent amplitudes and correlations generated by a quantum circuit.

## Two-qubit superposition

Applying H to each qubit starting from `|00>` creates

    (|00> + |01> + |10> + |11>) / 2

Each basis state has probability

    1/4

This demonstrates how a single Hadamard operation generalizes from one qubit to multiple qubits.

For `n` qubits, applying H to every qubit beginning from `|00...0>` creates a uniform superposition over all `2^n` computational-basis states.

## Hadamard versus classical randomness

A classical random bit can have probabilities

    P(0) = 1/2
    P(1) = 1/2

A Hadamard-prepared qubit can produce the same measurement probabilities.

The states are not equivalent in general.

The quantum state has amplitudes and relative phase. For example,

    |+> = (|0> + |1>) / sqrt(2)

and

    |-> = (|0> - |1>) / sqrt(2)

have the same computational-basis probabilities but behave differently under subsequent quantum operations.

This phase-sensitive behavior is what enables interference.

## Hadamard versus measurement

The Hadamard gate is a deterministic unitary transformation of the quantum state.

Measurement is probabilistic.

For a fixed input state, the Hadamard operation always produces the same mathematical state. The randomness appears when that state is measured.

This distinction is central to understanding quantum circuits.

## Hadamard versus entanglement

The Hadamard gate is a single-qubit gate.

It can create superposition without creating entanglement.

For example,

    H|0> = |+>

is a one-qubit superposition.

Entanglement requires a multi-qubit state that cannot be expressed as a tensor product of independent single-qubit states.

The C++ Bell-state circuit demonstrates how H can be combined with CNOT to create entanglement.

Thus, superposition and entanglement are related quantum concepts but are not interchangeable terms.

## Bit ordering

Multi-qubit simulations require a defined mapping between qubit numbers and state-vector indices.

The implementations use:

    qubit 0 = least-significant bit

For two qubits:

    index 0 -> |00>
    index 1 -> |01>
    index 2 -> |10>
    index 3 -> |11>

A different software system may use the opposite convention.

There is no universal requirement that every simulator use the same internal indexing convention, but a correct implementation must use its chosen convention consistently.

Incorrect qubit ordering can make an otherwise mathematically correct circuit appear to produce incorrect results.

## State-vector simulation

An `n`-qubit pure state requires `2^n` complex amplitudes in a dense state-vector representation.

The growth is exponential:

| Qubits | Basis states |
| ---: | ---: |
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 5 | 32 |
| 10 | 1,024 |
| 20 | 1,048,576 |
| 30 | 1,073,741,824 |

The C++ and Python implementations deliberately limit their educational simulators to avoid uncontrolled memory allocation.

The JavaScript implementation uses the same conceptual limit.

## Gate complexity

For a dense state vector, applying a one-qubit gate requires visiting a number of amplitudes proportional to `2^n`.

Therefore, the typical time complexity is

    O(2^n)

and the memory complexity is

    O(2^n)

for the state vector.

The implementation does not construct the complete `2^n × 2^n` operator matrix for every single-qubit operation. Instead, it transforms amplitude pairs directly.

This is an important implementation optimization.

## Numerical precision

The amplitudes are stored using floating-point complex numbers.

Floating-point arithmetic introduces small numerical errors.

For that reason, the implementations use tolerance-based comparisons instead of relying on exact equality for calculated values.

For example, a theoretically zero amplitude may appear internally as a very small value such as `1e-16`.

Normalization checks therefore use an appropriate tolerance.

## Edge cases

Important edge cases include:

### Invalid normalization

A state such as

    0.5|0> + 0.5|1>

is not normalized because

    0.5^2 + 0.5^2 = 0.5

rather than `1`.

The implementations reject such a state.

### Invalid qubit index

A two-qubit register has valid indices `0` and `1`.

Using index `2` is invalid.

The simulators explicitly validate this condition.

### Invalid CNOT

The control and target of a CNOT must be different qubits.

Using the same qubit for both is rejected.

### Large state vectors

Although the mathematical definition works for arbitrary `n`, a dense classical simulator cannot allocate unlimited state vectors.

The number of amplitudes doubles whenever one additional qubit is added.

## Common mistakes

### Treating amplitudes as probabilities

Incorrect interpretation:

    amplitude = probability

Correct interpretation:

    probability = |amplitude|^2

### Ignoring phase

The states `|+>` and `|->` have the same computational-basis probabilities but different relative phases.

Ignoring the sign can produce incorrect predictions for later gates.

### Treating superposition as ordinary randomness

A superposition contains coherent amplitudes. Classical probability distributions do not encode the same phase information.

### Forgetting measurement collapse

After measurement, the simulated state is a basis state corresponding to the observed result.

Independent statistical sampling therefore requires repeated state preparation.

### Assuming H is irreversible

The Hadamard gate is reversible.

It satisfies

    H^-1 = H

and therefore

    H^2 = I

### Mixing qubit-order conventions

A simulator must document which qubit corresponds to which bit position.

A circuit can appear incorrect if the implementation and the user interpret qubit ordering differently.

### Expecting exact floating-point results

Expressions involving `sqrt(2)` and complex arithmetic are subject to floating-point rounding.

Tolerance-based comparisons are more reliable.

## Practical applications

The Hadamard gate appears throughout quantum-circuit construction.

Relevant uses include:

- preparing balanced superpositions
- converting between computational and phase-sensitive representations
- creating the initial superposition in several quantum algorithms
- exposing relative phase through interference
- preparing one component of Bell-state circuits
- constructing quantum Fourier-transform structures
- forming interference-based quantum circuits
- transforming measurement bases
- initializing quantum algorithm registers

The gate is especially important because it provides a simple connection between state preparation, amplitude, phase, interference, and measurement.

## Important distinctions

| Concept | Meaning |
|---|---|
| Qubit | Unit of quantum information |
| Basis state | A state such as `|0>` or `|1>` |
| Amplitude | Complex coefficient associated with a basis state |
| Probability | Squared magnitude of an amplitude |
| Superposition | Coherent combination of basis states |
| Relative phase | Phase difference between components of a state |
| Global phase | Common phase factor applied to the entire state |
| Measurement | Process that produces an observable outcome |
| Unitary gate | Reversible norm-preserving quantum transformation |
| Hadamard gate | Unitary gate that maps basis states to balanced phase-sensitive superpositions |
| Entanglement | Non-separable multi-qubit quantum correlation |

## Best practices

A robust Hadamard-gate implementation should:

- represent amplitudes using complex numbers
- enforce normalization
- apply the Born rule correctly
- distinguish amplitudes from probabilities
- track relative phase
- document qubit ordering
- use numerical tolerances
- validate gate indices
- reject invalid multi-qubit operations
- model measurement collapse when measurement is simulated
- separate circuit description from state execution when appropriate
- avoid unnecessarily constructing large dense gate matrices
- account for exponential state-vector growth
- test known identities such as `H^2 = I`
- verify expected probability distributions statistically

## Security and production considerations

The Hadamard gate itself is a mathematical transformation and does not introduce conventional application-security risks.

A production quantum software system still requires careful engineering around the surrounding infrastructure.

Relevant considerations include:

- validating circuit input
- limiting requested simulation sizes
- preventing uncontrolled memory allocation
- handling malformed gate sequences
- defining deterministic testing modes
- controlling random-number generation for reproducibility
- protecting externally supplied circuit descriptions
- recording circuit versions and execution parameters
- distinguishing simulation results from results produced by physical quantum hardware
- accounting for numerical precision
- validating normalization and other mathematical invariants

A state-vector simulator should never accept an unrestricted qubit count from an untrusted caller without resource controls because `2^n` state-vector growth can cause severe memory and computation consumption.

## Implementation considerations

The three implementations intentionally emphasize different programming concerns.

### Python

Python makes the mathematical structure easy to inspect.

Its `Qubit` and `QuantumRegister` classes provide a compact representation of the underlying quantum operations.

It is particularly suitable for experimenting with formulas, probability distributions, simulations, assertions, and algorithmic ideas.

### JavaScript

JavaScript demonstrates explicit complex-number handling and practical runtime validation.

The implementation also uses JavaScript's object-oriented syntax and deterministic pseudo-random sampling to make measurement experiments reproducible.

Its state-vector implementation follows the same mathematical model while adapting the representation to JavaScript's standard numeric facilities.

### C++

C++ demonstrates how the same mathematical model can be organized as a more strongly structured systems-oriented implementation.

`QuantumRegister` manages state, `GateOperation` represents operations, and `QuantumCircuit` separates circuit construction from execution.

The implementation uses the C++ standard library only and includes validation, exception handling, state invariants, measurement, and performance analysis.

## Conceptual progression represented by the implementations

The examples progress through several levels of abstraction:

1. `|0>` and `|1>` establish the computational basis.
2. Complex amplitudes provide the mathematical state representation.
3. The Hadamard matrix defines the gate.
4. `H|0>` demonstrates superposition.
5. `H|1>` demonstrates relative phase.
6. A second H demonstrates interference and reversibility.
7. Measurement demonstrates probabilistic outcomes and collapse.
8. Multiple Hadamard gates create multi-qubit superpositions.
9. CNOT combined with H creates a Bell state.
10. State-vector simulation exposes the exponential computational cost of classical simulation.
11. Circuit abstractions demonstrate how these operations can be incorporated into a software architecture.

## Mathematical relationships

The central identities demonstrated by the implementations are

    H|0> = |+>

    H|1> = |->

    |+> = (|0> + |1>) / sqrt(2)

    |-> = (|0> - |1>) / sqrt(2)

    H^2 = I

    P(x) = |amplitude_x|^2

For a normalized state,

    sum_x |amplitude_x|^2 = 1

For an `n`-qubit dense state vector,

    number of amplitudes = 2^n

These relationships form the mathematical foundation for the executable demonstrations.

## Real-world relevance

The Hadamard gate is a basic building block rather than a complete quantum algorithm by itself.

Its importance comes from how it interacts with other quantum operations.

A circuit can use H to create alternative computational paths, manipulate relative phase, and allow subsequent gates to produce constructive or destructive interference.

The combination of H and controlled operations is also sufficient to demonstrate the transition from single-qubit superposition to multi-qubit entanglement.

The Python, JavaScript, and C++ programs therefore treat the Hadamard gate not as an isolated matrix exercise but as an operation embedded in a complete state-vector and circuit-execution model.
