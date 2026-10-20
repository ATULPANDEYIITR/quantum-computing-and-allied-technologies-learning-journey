# Simon's Algorithm: Hidden-Period Problem

## Scope

Simon's algorithm solves a promise problem in which an unknown binary string `s`, called the hidden period, determines a two-to-one oracle function:

`f(x) = f(x XOR s)`

for every input `x`, with `s` non-zero.

The computational objective is to recover `s`.

The implementations in this project deliberately separate four layers:

| Layer | Role |
|---|---|
| Oracle | Encodes the hidden period through paired inputs |
| Measurement | Produces binary vectors satisfying `y · s = 0 mod 2` |
| Linear algebra | Collects independent equations over GF(2) |
| Recovery | Finds the unique non-zero vector in the nullspace |

The key relationship is:

`Simon oracle → quantum interference → orthogonality constraints → GF(2) linear system → hidden period`

The quantum portion creates useful measurement constraints. The final recovery is classical linear algebra.

## Mathematical Model

Let the hidden period be

` s ∈ {0,1}^n, s ≠ 0 `

and let the oracle satisfy

` f(x) = f(x ⊕ s) `.

The Simon promise also requires that the function has exactly two preimages for each output. The two inputs in a collision differ by the hidden period:

`x ⊕ x' = s`.

After applying the oracle and interference operations in Simon's circuit, a measured vector `y` satisfies

`y · s = 0 (mod 2)`.

The dot product is calculated using binary multiplication followed by addition modulo two.

For example, with:

` s = 1011 `

a measurement such as:

` y = 0110 `

is valid because:

`0·1 ⊕ 1·0 ⊕ 1·1 ⊕ 0·1 = 1`

so this particular vector would not be accepted for that secret. A valid measurement must evaluate to zero.

Each independent measurement contributes one linear constraint. For an `n`-bit secret, `n - 1` independent equations normally leave a one-dimensional nullspace containing `{0, s}`. The promise that `s` is non-zero identifies `s`.

## Oracle Construction

The source implementations use a deterministic classical oracle representation:

`f(x) = min(x, x XOR s)`.

This is not intended as a universal construction for arbitrary Simon functions. It is a compact simulation that explicitly guarantees the collision relation.

For every `x`:

`f(x) = f(x XOR s)`.

Each output therefore represents the pair:

`{x, x XOR s}`.

The implementations also verify the two-to-one property for finite demonstration domains.

The classical verification requires enumeration of the domain and therefore has exponential cost in `n`. A real quantum implementation does not construct a complete classical table of all `2^n` inputs.

## Python Implementation

The Python program treats the problem as a simulation of the information produced by Simon's quantum circuit.

`SimonInstance` validates the problem width and rejects the zero secret.

`SimonOracle` provides the paired-input oracle and checks both the hidden-period relation and the two-to-one property.

`hadamard_sample()` models the measurement distribution directly. It does not construct a quantum state vector. Instead, it samples vectors satisfying the exact condition produced by Simon's interference stage:

`y · s = 0`.

The `nullspace_mod2()` routine performs Gaussian elimination over GF(2). Ordinary integer addition is replaced by XOR, which is the appropriate arithmetic for binary linear equations.

The program collects distinct measurements until the linear system has enough information to produce a one-dimensional nullspace.

The Python implementation also includes the `n = 1` edge case. When the Simon promise guarantees a non-zero one-bit secret, the only possible secret is `1`.

### Important implementation properties

- Input secrets are validated as binary strings.
- The zero vector is rejected because Simon's hidden period is non-zero.
- Oracle inputs outside the domain are rejected.
- Measurements are validated before elimination.
- Rank is used to distinguish independent evidence from duplicate equations.
- Failure to obtain a unique nullspace raises an explicit exception.
- The implementation uses only the Python standard library.

## JavaScript Implementation

The JavaScript implementation uses an event-driven workflow rather than reproducing the Python structure.

`SimonOracle` models the two-to-one oracle and verifies the Simon promise.

`MeasurementStream` supplies reproducible measurements using a deterministic xorshift32 generator. The generator is used only to make the simulation repeatable. It is not a cryptographic random-number generator.

`SimonWorkflow` manages the asynchronous collection process. `setImmediate()` represents a stream of measurement events and prevents the collection loop from being expressed as one large blocking operation.

The implementation uses rejection sampling to generate uniformly distributed binary vectors satisfying the orthogonality condition.

The GF(2) routines operate on arrays of numeric bits. XOR is used for row operations, matching the arithmetic of Simon's equations.

The workflow stops when the measurement matrix reaches rank `n - 1`.

This implementation demonstrates an important distinction between a physical quantum implementation and an algorithmic simulator: the simulator directly generates the classical information that the quantum circuit guarantees rather than allocating exponentially many complex amplitudes.

## C++17 Implementation

The C++ program presents Simon's problem as a constrained recovery engine.

`SimonOracle` owns the binary secret and provides the paired oracle behavior. It also validates the two-to-one promise over the explicitly represented input domain.

`BinaryVector` represents vectors over GF(2). Vector addition is implemented as element-wise XOR.

The elimination engine performs row reduction using:

- pivot selection,
- row swapping,
- XOR elimination,
- rank calculation,
- nullspace construction.

The program separates measurement generation from recovery. `measureAllowedVector()` produces a measurement satisfying the Simon constraint, while `recoverSecret()` operates only on collected evidence.

The `MergeEligibilityEngine` name emphasizes the decision boundary in the simulation: enough independent constraints must exist before the hidden period can be resolved. It is not a Git workflow model; its purpose is to make the transition from insufficient information to a determined mathematical result explicit.

The C++ implementation is suitable for examining memory and algorithmic behavior because the binary vectors are represented compactly as `std::vector<int>` rather than as strings throughout the elimination stage.

For a matrix with `m` observations and `n` variables, Gaussian elimination has approximately `O(mn²)` arithmetic complexity.

The explicit oracle enumeration remains `O(2^n)` and is therefore suitable only for demonstration-sized domains.

## Java 17 Implementation

The Java implementation models the algorithm as an enterprise-style domain service.

The `SimonProblem` record represents immutable problem configuration and performs construction-time validation.

`Measurement` is another immutable domain value. Invalid binary representations cannot enter the model.

`Oracle` is an interface separating the oracle contract from the `PairOracle` implementation.

`ReviewState` represents the information state of the recovery process:

| State | Meaning |
|---|---|
| `UNOBSERVED` | No useful measurement evidence has been collected |
| `CONSTRAINED` | Measurements exist but do not uniquely determine the secret |
| `DETERMINED` | The measurement matrix has rank `n - 1` |

`GovernanceService` owns the measurement workflow and controls the transition between these states. It refuses to resolve a secret while the available evidence is insufficient.

`GF2Solver` performs rank and nullspace calculations without external dependencies.

This separation prevents mathematical concerns from being hidden inside random sampling or application state management.

Java records provide immutable value-oriented domain types, while interfaces isolate the oracle abstraction. Exceptions represent invalid states such as inconsistent vector dimensions or an unresolved hidden period.

## PostgreSQL Model

The PostgreSQL implementation treats Simon's algorithm as a relational experiment.

The main entities are:

| Table | Purpose |
|---|---|
| `problem` | Stores problem width and hidden period |
| `oracle_input` | Stores the finite demonstration oracle |
| `measurement` | Stores measured binary constraints |
| `status_check` | Stores validation results for operational reporting |

The database enforces binary secrets through regular-expression checks and rejects the zero secret.

The `bit_dot_mod2()` function implements the orthogonality equation directly in PostgreSQL.

The `xor_bit_strings()` function supplies GF(2) vector addition for the database-side elimination routine.

A trigger invokes `validate_measurement()` before measurements are inserted. Consequently, a measurement that violates:

`y · s = 0 mod 2`

cannot enter the `measurement` table.

This is an example of database-level integrity enforcement rather than relying exclusively on application validation.

## Database-Side Rank Calculation

`independent_measurement_count()` performs row reduction over GF(2).

Its operations correspond to classical Gaussian elimination:

- locate a pivot,
- exchange rows,
- eliminate the pivot column using XOR,
- advance to the next column,
- count pivots.

The `measurement_status` view exposes the resulting rank and compares it with the required `n - 1` independent equations.

This creates three operational states:

- `unobserved`
- `constrained`
- `determined`

The database therefore represents not only raw measurements but also the information state of the recovery process.

## Oracle Integrity

`problem_integrity_report` checks whether stored oracle values agree with the configured hidden period.

`oracle_collision_report` groups inputs by oracle output and verifies that each output has exactly two preimages.

These checks distinguish two properties that should not be conflated:

**Period property**

`f(x) = f(x XOR s)`

**Two-to-one promise**

Every valid output has exactly two inputs.

The first property establishes the hidden-period relationship. The second constrains the oracle so that the Simon problem has its promised structure.

## Measurement and Recovery Workflow

A complete execution follows this conceptual path:

`Problem definition`
  
`↓`

`Hidden non-zero period`

`↓`

`Two-to-one oracle`

`↓`

`Quantum interference represented by valid measurement constraints`

`↓`

`y · s = 0 mod 2`

`↓`

`Independent measurement collection`

`↓`

`GF(2) Gaussian elimination`

`↓`

`One-dimensional nullspace`

`↓`

`Recovered non-zero secret`

The measurement stage does not reveal `s` directly. Each measurement eliminates candidate secrets that do not satisfy its orthogonality equation.

Repeated or linearly dependent measurements provide no new information. This is why the implementations track rank rather than simply counting observations.

## Distinction Between Quantum and Classical Work

Simon's algorithm gains its speedup from the quantum portion, not from Gaussian elimination.

The quantum circuit processes a superposition of all possible oracle inputs. The oracle and interference operations transform the state so that measurements produce vectors orthogonal to the hidden period.

The classical computer then solves the resulting system.

A classical simulation that explicitly enumerates every quantum state would require resources exponential in `n`. The implementations here avoid that cost by directly simulating the mathematically relevant measurement distribution.

This makes them useful for understanding the algorithmic structure but does not constitute a quantum speedup by itself.

## Complexity

| Operation | Demonstration cost |
|---|---:|
| Oracle table construction | `O(2^n)` |
| Oracle promise verification | `O(2^n)` |
| Measurement generation | Expected constant-factor rejection work per sample |
| GF(2) rank | `O(mn²)` |
| GF(2) nullspace | `O(mn²)` |
| Required independent equations | `n - 1` |

Here `n` is the number of input bits and `m` is the number of collected measurements.

The exponential oracle operations exist because these artifacts explicitly materialize a classical demonstration domain. They are not representative of the resource requirements of the corresponding quantum circuit.

## Edge Cases and Failure Conditions

The implementations explicitly handle several important cases.

### Zero secret

The zero vector is rejected. Without this restriction, every input would satisfy `x XOR 0 = x`, which does not define the intended Simon promise.

### Invalid binary vectors

Secrets and measurements must contain only `0` and `1`.

### Incorrect vector width

A measurement from an `n`-bit problem cannot be used as an equation for an `m`-bit problem.

### Duplicate measurements

A repeated measurement does not increase matrix rank and therefore does not improve knowledge of the hidden period.

### Linearly dependent measurements

Different-looking vectors can still represent dependent equations. Rank, rather than row count, determines whether new information has been obtained.

### Insufficient measurements

If the nullspace contains multiple vectors, the secret is not uniquely recoverable from the available evidence.

### Invalid oracle behavior

The oracle verification routines detect violations of the required period relationship or two-to-one structure.

## Security and Reliability Considerations

The examples use deterministic or ordinary pseudo-random generators for reproducibility. These generators must not be interpreted as cryptographic randomness.

The hidden period is intentionally stored in the model because these programs are educational simulations. A real cryptographic or privacy-sensitive system would not expose secret state through logs, database reports, assertions, or diagnostic output.

The PostgreSQL trigger demonstrates defense in depth: measurements are validated at the database boundary even if an application attempts to submit invalid evidence.

The database functions also validate vector dimensions before performing binary arithmetic, preventing malformed input from silently producing incorrect linear-algebra results.

## Practical Interpretation

Simon's algorithm is important because it provides a clear example of how a quantum computer can transform a hidden algebraic relationship into efficiently usable classical information.

The essential separation is:

| Concept | Function |
|---|---|
| Hidden period | Unknown binary structure to recover |
| Oracle | Encodes the period through input collisions |
| Quantum interference | Converts the hidden structure into measurable constraints |
| Measurement | Produces `y` satisfying `y · s = 0` |
| GF(2) elimination | Combines constraints |
| Nullspace | Contains candidate hidden periods |
| Non-zero promise | Identifies the intended secret when the nullspace is one-dimensional |

The five implementations preserve this separation while emphasizing different engineering perspectives: Python focuses on algorithmic simulation, JavaScript on event-driven measurement processing, C++ on a compact recovery engine, Java on explicit domain and state modeling, and PostgreSQL on persistent constraints, validation, and relational analysis.
