# Shor Circuit Components: QFT, Phase Estimation and Period Finding

## Scope

This project models the principal circuit components that make Shor's factoring algorithm work:

- Quantum Fourier Transform (QFT)
- Inverse QFT
- Quantum phase estimation as the mechanism for extracting periodic phase information
- Modular exponentiation and periodicity
- Continued-fraction-style rational reconstruction
- Classical factor recovery from an even period
- Circuit decomposition into elementary gates
- Validation, state management, and failure conditions

The five implementations use the same mathematical pipeline but emphasize different engineering perspectives.

The central relationship is:

`Modular exponentiation → periodic phase → phase estimation → QFT measurement → rational approximation → period candidate → factor extraction`

The project deliberately separates the mathematical roles of these components. QFT is a quantum basis transformation. Phase estimation converts an eigenphase into a measurable binary fraction. Period finding interprets that phase as information about the period of modular exponentiation. Factor extraction is a classical post-processing step.

## Mathematical Context

For an integer `a` relatively prime to `N`, the multiplicative order `r` is the smallest positive integer satisfying

`a^r ≡ 1 (mod N)`.

The function

`f(x) = a^x mod N`

is therefore periodic with period `r`.

Shor's algorithm does not need to factor `N` directly inside the quantum circuit. The quantum portion obtains information about `r`. Once a suitable even period is known, classical arithmetic can attempt to recover factors through

`x = a^(r/2) mod N`

and

`gcd(x - 1, N)` and `gcd(x + 1, N)`.

The method can fail even when the period is mathematically correct. A useful period must normally be even, and `a^(r/2)` must not be congruent to `1` or `-1` modulo `N`. Different phase measurements can also produce approximations that do not immediately reveal the correct denominator.

## QFT

For an `N`-dimensional state vector with amplitudes `x_0 ... x_(N-1)`, the normalized QFT produces

`y_k = 1/sqrt(N) × Σ_x x_x exp(2πikx/N)`.

The inverse QFT changes the sign of the phase term.

The Python, JavaScript, C++17, and Java 17 implementations directly calculate the transform for small state vectors. This makes the amplitude transformation observable without requiring an external quantum-computing framework.

The direct simulation has `O(N²)` arithmetic complexity. If `N = 2^q`, this is exponential in the number of qubits `q`. The actual QFT circuit uses a decomposition containing:

- one Hadamard operation per qubit
- controlled phase rotations between qubit pairs
- final swaps to reverse the computational-register ordering

The circuit representation therefore contains `O(q²)` elementary gates even though a classical state-vector simulation can require `O(4^q)` arithmetic operations.

## QFT Circuit Decomposition

The elementary decomposition follows the standard structure:

`Qubit 0 → H → controlled rotations`
  
`Qubit 1 → H → controlled rotations`
  
`Qubit 2 → H → controlled rotations`
  
`...`

followed by bit-order reversal through SWAP operations.

A controlled phase rotation has the form

`R_k = diag(1, 1, 1, exp(2πi / 2^k))`

when represented as a two-qubit controlled operation.

The source implementations store gate type, participating qubits, and rotation angle explicitly. This allows the circuit structure to be inspected independently from the numerical state-vector calculation.

## Phase Estimation

Phase estimation is the bridge between the modular periodicity problem and the QFT.

Suppose a unitary operation has eigenvalue

`exp(2πiφ)`.

The phase estimation procedure encodes an approximation to `φ` into a counting register. The inverse QFT converts the phase information into a computational-basis measurement.

For modular exponentiation in Shor's algorithm, the relevant phases are related to fractions of the form

`φ = s/r`

for integer values of `s`.

If the counting register contains `q = 2^t` states, a measurement `y` gives an approximation

`y/q ≈ s/r`.

The denominator `r` can then be reconstructed from a suitable rational approximation.

The implementations use idealized phase measurements rather than claiming to emulate physical quantum noise or a complete fault-tolerant quantum processor.

## Period Finding

Period finding is treated as a distinct algorithmic layer.

For the demonstration with

`a = 2`

and

`N = 15`,

the modular sequence is:

| `x` | `2^x mod 15` |
|---:|---:|
| 0 | 1 |
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 1 |
| 5 | 2 |
| 6 | 4 |
| 7 | 8 |

The period is therefore `r = 4`.

The phase-estimation model contains phases corresponding to:

| `s` | `s/r` |
|---:|---:|
| 0 | 0 |
| 1 | 1/4 |
| 2 | 1/2 |
| 3 | 3/4 |

With an eight-qubit counting register, the ideal integer measurements for these phases are approximately:

| Phase | Measurement |
|---:|---:|
| 0 | 0 |
| 1/4 | 64 |
| 1/2 | 128 |
| 3/4 | 192 |

The classical reconstruction stage interprets the measured ratio as a rational approximation and tests candidate periods.

## Factor Recovery

For `N = 15`, `a = 2`, and `r = 4`:

`a^(r/2) = 2^2 = 4`.

Then:

`gcd(4 - 1, 15) = gcd(3, 15) = 3`

and

`gcd(4 + 1, 15) = gcd(5, 15) = 5`.

The recovered factors are therefore `3` and `5`.

The implementations also model unsuccessful cases. An odd candidate period cannot directly use the `r/2` extraction step. A period producing `a^(r/2) ≡ ±1 mod N` does not provide useful non-trivial factors. A base that already shares a factor with `N` can reveal a factor through a classical GCD before phase estimation is needed.

## Python Implementation

The Python source provides a compact end-to-end educational simulator.

### State representation

Complex amplitudes are represented using Python's built-in complex number type. `qft_state()` and `inverse_qft_state()` operate directly on lists of amplitudes.

`probability_distribution()` converts amplitudes into normalized measurement probabilities.

### Circuit representation

`Gate` is a dataclass containing:

- gate name
- participating qubits
- optional rotation angle

`Circuit` stores an ordered list of gates and constructs a QFT decomposition through `qft()`.

### Period-finding pipeline

`shor_period_pipeline()` separates:

1. trivial GCD detection
2. classical order discovery for the educational model
3. idealized phase estimation
4. rational denominator reconstruction
5. period validation
6. factor extraction

The classical order search is intentionally separated from the quantum circuit representation. A real Shor implementation would replace that classical search with quantum modular exponentiation and phase estimation.

### Validation

The Python program rejects:

- non-power-of-two QFT dimensions
- invalid circuit qubit indices
- non-invertible modular bases
- invalid moduli
- invalid periods

The executable demonstrations also verify that the `15 = 3 × 5` example produces the expected period and factors.

## JavaScript Implementation

The JavaScript implementation emphasizes event-driven processing and exact integer arithmetic.

### Complex arithmetic

JavaScript does not provide a built-in complex-number primitive, so the source defines an immutable `Complex` class with:

- addition
- multiplication
- scalar multiplication
- magnitude squared

### Circuit model

`QuantumCircuit` stores gate objects and validates qubit indices before accepting operations.

The QFT construction uses:

- Hadamard gates
- controlled phase gates
- SWAP gates

The circuit is inspectable through `describe()`.

### Asynchronous measurement stream

The phase-estimation demonstration contains an asynchronous generator. It separates measurement acquisition from classical interpretation.

This models an important architectural boundary:

`measurement acquisition → asynchronous records → classical analysis`

The implementation uses only JavaScript runtime facilities and does not require npm packages.

### Exact modular arithmetic

`BigInt` is used for modular exponentiation and period calculations. This avoids the precision limitations of JavaScript's IEEE-754 `Number` type for integer values outside the safe-integer range.

## C++17 Implementation

The C++17 program is structured as a technical case study around explicit value types and deterministic execution.

### Numerical model

`std::complex<double>` represents state amplitudes.

The direct QFT implementation uses the standard complex exponential representation. The inverse transformation changes the sign of the phase angle.

### Circuit architecture

The circuit contains:

- `GateType`
- `Gate`
- `QuantumCircuit`

The circuit class validates qubit references and rejects invalid controlled operations and degenerate SWAP gates.

### Modular arithmetic

The implementation uses `unsigned __int128` for intermediate multiplication when calculating modular products from 64-bit operands. This prevents overflow in the intermediate product for the supported integer range.

Repeated squaring makes modular exponentiation logarithmic in the exponent.

### Period estimation

The C++ implementation uses a bounded rational approximation search to keep the demonstration deterministic and self-contained. The mathematical role corresponds to the continued-fraction reconstruction stage used by practical Shor implementations.

The implementation intentionally does not represent this bounded search as the quantum algorithm itself. It represents the classical interpretation of a phase-estimation result.

## Java 17 Implementation

The Java implementation emphasizes explicit domain modeling and policy separation.

### Domain types

The source defines:

- `GateType`
- `Gate`
- `Complex`
- `PhaseMeasurement`
- `ShorResult`

Java records provide immutable value objects for these concepts.

### Circuit service

`QuantumCircuit` owns gate validation and QFT construction. The circuit's gate list is exposed through an unmodifiable view so callers cannot mutate internal state accidentally.

### Phase policy

`PhasePolicy` is an interface defining how a measurement is selected from a collection of phase observations.

`NearestNonZeroPhasePolicy` implements the policy used by the demonstration.

This separation makes the measurement-selection rule explicit instead of embedding it inside the period-finding service.

### Shor period service

`ShorPeriodService` owns:

- input validation
- early GCD detection
- order calculation for the educational model
- phase measurement construction
- rational denominator approximation
- factor extraction

The resulting `ShorResult` records the workflow state and recovered factors.

## PostgreSQL Model

The PostgreSQL implementation treats the experiment as persistent relational state.

The central relationship is:

`Experiment → Qubit Registers → Circuit Gates → Phase Measurements → Period Candidates → Factor Results`

### `experiment`

Stores the mathematical experiment:

- base `a`
- modulus `N`
- counting-qubit count
- workflow status
- discovered period
- timestamps

The status enum distinguishes `CREATED`, `RUNNING`, `COMPLETE`, `FAILED`, and `TRIVIAL_FACTOR`.

### `qubit_register`

Separates counting and work registers.

The counting register supports phase estimation. The work register represents the modular-exponentiation state.

### `circuit_gate`

Stores the physical circuit description independently from experiment metadata.

Gate types include:

- Hadamard
- controlled phase
- SWAP
- controlled modular multiplication
- measurement

Sequence numbers enforce a deterministic gate order.

### `phase_measurement`

Stores measurement records with:

- shot number
- measured integer
- counting-register size
- measured phase
- ideal phase
- probability

A trigger prevents a measurement integer from exceeding the representable range of its counting register.

### `period_candidate`

Stores classical rational-reconstruction results.

The `is_even` generated column makes the principal Shor period condition queryable without duplicating application logic.

### `factor_result`

Stores recovered factors and their mathematical derivation.

The unique index prevents the same factor from being recorded repeatedly for one experiment.

## Database Workflow

The PostgreSQL workflow is:

`CREATE experiment`

→ `define registers`

→ `store QFT gates`

→ `store phase measurements`

→ `create period candidate`

→ `evaluate period`

→ `derive factors`

→ `mark experiment COMPLETE`

The status trigger records state transitions in `branch_state_audit`.

This makes the workflow auditable and prevents important state changes from becoming invisible application-side mutations.

## Distinguishing the Core Components

| Component | Primary role | Output |
|---|---|---|
| QFT | Changes representation into a Fourier basis | Phase-sensitive amplitudes |
| Inverse QFT | Converts phase information back to computational basis | Measurement distribution |
| Phase estimation | Encodes an eigenphase in a counting register | Approximate phase |
| Period finding | Interprets phase as `s/r` information | Candidate period |
| Continued-fraction reconstruction | Recovers rational denominator | Candidate `r` |
| Factor extraction | Uses a valid even period classically | Non-trivial factors |

These are related stages, not interchangeable names.

QFT is the transformation used inside phase estimation. Phase estimation is the measurement procedure that extracts phase information. Period finding interprets that information in the modular-exponentiation problem. Factor extraction happens after a useful period has been identified.

## Failure Conditions

A complete implementation must account for cases where the algorithm cannot proceed directly.

### Non-coprime base

If

`gcd(a, N) > 1`,

a non-trivial factor has already been discovered. Quantum period estimation is unnecessary for that attempt.

### Odd period

If `r` is odd, `r/2` is not an integer and the standard factor-extraction expression cannot be applied.

### Trivial half-period value

If

`a^(r/2) ≡ -1 mod N`

or

`a^(r/2) ≡ 1 mod N`,

the resulting GCD calculations do not produce the required non-trivial factors.

### Insufficient phase precision

A finite counting register only approximates the phase. The measured ratio can correspond to an incorrect denominator or an ambiguous rational approximation.

More counting qubits improve resolution but increase circuit size and the number of quantum resources required.

### State-vector simulation limits

The direct QFT implementations are educational numerical simulators. Their memory and runtime requirements grow rapidly with the number of qubits because a `q`-qubit state vector contains `2^q` amplitudes.

They should not be interpreted as scalable implementations of Shor's algorithm.

## Security and Practical Implications

Shor's algorithm is important in cryptography because sufficiently large fault-tolerant quantum computers could solve integer factorization and discrete logarithm problems substantially faster than known classical algorithms.

The project therefore treats the algorithm as a cryptographic systems concept rather than merely a Fourier-transform exercise.

The implementations do not claim to factor cryptographically sized RSA moduli. The numerical examples use small integers because the purpose is to expose the algorithmic structure, state transitions, validation rules, and classical post-processing.

For security analysis, the important distinction is between:

- a mathematical quantum algorithm
- a circuit decomposition
- a noisy hardware execution
- a fault-tolerant implementation
- a classical simulator

These layers have very different resource requirements.

## Performance Characteristics

| Operation | Educational implementation |
|---|---|
| Direct QFT | `O(N²)` arithmetic |
| QFT circuit decomposition | `O(q²)` gates |
| State-vector storage | `O(2^q)` amplitudes |
| Modular exponentiation | logarithmic number of multiplications in the exponent |
| Classical order search in examples | linear in the searched period bound |
| Rational denominator search | bounded by the selected denominator limit |

The direct QFT is intentionally simple enough to inspect. It is not the asymptotically best way to implement Fourier transforms on classical hardware.

The QFT circuit representation is more faithful to quantum-circuit construction, while the state-vector implementation makes the underlying mathematical transformation directly observable.

## Repository-Level Domain Structure

The complete technical model can be viewed as:

`Experiment`

`  ├── Counting Register`

`  ├── Work Register`

`  ├── Circuit Gates`

`  │     ├── Hadamard`

`  │     ├── Controlled Phase`

`  │     └── SWAP`

`  ├── Modular Exponentiation`

`  ├── Phase Measurements`

`  ├── Period Candidates`

`  └── Factor Results`

The important state boundaries are explicit:

`Circuit construction`

→ `Quantum transformation`

→ `Measurement`

→ `Classical reconstruction`

→ `Period validation`

→ `Factor extraction`

This separation prevents the QFT, phase-estimation, and period-finding concepts from being treated as one undifferentiated operation.

## Files

| File | Technical focus |
|---|---|
| Python source | State-vector QFT, circuit construction, phase estimation model, period pipeline and validation |
| JavaScript source | Complex arithmetic, QFT, BigInt modular arithmetic, asynchronous measurement processing and circuit modeling |
| C++17 source | Explicit gate architecture, complex state simulation, overflow-safe modular multiplication and deterministic period processing |
| Java 17 source | Immutable domain records, circuit objects, phase policies, service-layer period finding and explicit workflow results |
| PostgreSQL source | Relational experiment model, constraints, triggers, phase records, period candidates, factor results and reporting views |
| README | Mathematical, architectural and implementation explanation |

## Practical Interpretation

The five source files implement the same conceptual chain from different engineering perspectives:

`QFT`

provides the Fourier-basis transformation.

`Phase estimation`

uses controlled powers of a unitary and an inverse Fourier transformation to expose phase information.

`Period finding`

uses the phase approximation to recover information about the modular period.

`Factor extraction`

uses the recovered period in classical number-theoretic calculations.

The small `N = 15`, `a = 2` example is deliberately chosen because every stage can be inspected numerically:

`2^0 mod 15 = 1`

`2^1 mod 15 = 2`

`2^2 mod 15 = 4`

`2^3 mod 15 = 8`

`2^4 mod 15 = 1`

so `r = 4`, followed by recovery of `3` and `5`.

The implementations preserve that separation between quantum transformation, measurement interpretation, periodicity, and classical factor recovery.
