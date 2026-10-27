# Shor's Algorithm and Integer Factorization

## Scope

This project implements the mathematical structure of Shor's algorithm for integer factorization across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The central distinction is between **factoring** and **order finding**:

- Integer factorization seeks non-trivial divisors of a composite integer `N`.
- Multiplicative order finding seeks the smallest positive integer `r` satisfying `a^r ≡ 1 mod N`, where `gcd(a, N) = 1`.
- Shor's algorithm uses quantum period finding to obtain information about `r`.
- Classical arithmetic converts a suitable even period into non-trivial factors.

The implementations use small integers so that the mathematical workflow can be inspected directly. The Python and JavaScript programs also contain small state-vector QFT demonstrations. The C++ and Java programs emphasize modular domain design and workflow control. PostgreSQL represents the factorization process as a relational workflow with database-level integrity checks.

## Mathematical Structure

For an odd composite integer `N`, choose an integer `a` satisfying:

`1 < a < N`

and test:

`gcd(a, N)`

If the greatest common divisor is already non-trivial, a factor has been found.

When:

`gcd(a, N) = 1`

the multiplicative order `r` is the smallest positive integer for which:

`a^r ≡ 1 mod N`

If `r` is even and:

`a^(r/2) ≠ -1 mod N`

then the values:

`gcd(a^(r/2) - 1, N)`

and:

`gcd(a^(r/2) + 1, N)`

can produce non-trivial factors of `N`.

The factorization stage therefore depends on a useful period. Not every randomly selected base produces a successful factorization attempt.

## Conceptual Workflow

    Composite integer N
            |
            v
       Select base a
            |
            v
       Compute gcd(a, N)
        /             \
    non-trivial         1
        |                |
        v                v
   factor found      Find order r
                         |
                         v
                   Is r even?
                     /     \
                   no       yes
                   |         |
                 retry       v
                       Check a^(r/2)
                             |
                             v
                  Is it different from -1?
                       /           \
                     no             yes
                     |               |
                   retry             v
                              Compute two gcds
                                   |
                                   v
                            Non-trivial factors

The quantum portion of Shor's algorithm is the efficient method for discovering the period. The classical portions perform base selection, modular arithmetic, continued-fraction processing, validation, and factor extraction.

## Four Distinct Technical Areas

The implementation separates four mathematical concerns that are often incorrectly treated as one operation.

### Integer Factorization

Factorization asks for numbers `p` and `q` such that:

`N = p × q`

For example:

`15 = 3 × 5`

Trial division is adequate for the small examples in this project but becomes impractical for sufficiently large semiprimes.

### Multiplicative Order

Order finding is not itself factorization.

For `N = 15` and `a = 2`:

`2^0 mod 15 = 1`

`2^1 mod 15 = 2`

`2^2 mod 15 = 4`

`2^3 mod 15 = 8`

`2^4 mod 15 = 1`

Therefore:

`r = 4`

The period is the information Shor's quantum subroutine is designed to recover.

### Quantum Fourier Transform

The QFT maps periodic information into measurable frequency information.

The small state-vector implementations construct a periodic computational state and apply a direct discrete QFT. Peaks in the resulting probability distribution correspond to values related to fractions of the unknown period.

This is useful for demonstrating the mathematics, but direct state-vector simulation is exponentially expensive as the number of qubits increases.

### Classical Factor Extraction

After recovering a candidate period, the implementation checks:

- whether the period is positive,
- whether it is even,
- whether modular exponentiation confirms the period,
- whether `a^(r/2)` is unsuitable for the trivial `-1` case,
- whether the resulting gcd operations produce non-trivial factors.

A failed condition causes another base or another period attempt to be considered.

## Python Implementation

The Python program provides the most complete mathematical reference implementation.

### Core Structures

The implementation uses:

- functions for modular arithmetic and number-theoretic operations,
- `dataclass` for structured factorization results,
- `Enum` for result states,
- `random.Random` for reproducible classical demonstrations,
- exceptions for invalid mathematical inputs,
- lists and probability distributions for state-vector simulation.

The `modular_power` function uses repeated squaring, reducing the exponentiation cost from repeated multiplication to logarithmic exponent complexity.

`multiplicative_order` explicitly computes the period for small educational inputs.

`continued_fraction_convergents` generates rational approximations used to recover a candidate period from a phase measurement.

### QFT Simulation

The Python implementation contains a direct QFT:

`O(Q²)`

where `Q` is the state-vector size.

This is intentionally not presented as a scalable quantum simulation. Its purpose is to expose the periodic-state-to-frequency-domain transformation.

The state-vector demonstration is restricted to small inputs to prevent accidental use as a large-memory simulation.

### Validation

The script verifies:

- `gcd(84, 30) = 6`,
- `7^4 mod 15 = 1`,
- the order of `2 mod 15` is `4`,
- the period `4` produces factors `3` and `5`,
- trial factorization produces expected small factors.

## JavaScript Implementation

The JavaScript program is designed around Node.js standard-library functionality and uses `BigInt` for modular arithmetic.

This is important because JavaScript's ordinary `Number` type cannot exactly represent arbitrary large integers. The modular exponentiation implementation therefore converts arithmetic operands to `BigInt` and uses repeated squaring.

The implementation also includes:

- direct domain functions where simple structures are sufficient,
- classes for mathematical errors,
- cryptographically sourced randomness for measurement sampling,
- direct QFT state vectors,
- continued-fraction processing,
- explicit factorization validation.

The QFT probability distribution is represented as pairs containing real and imaginary components. This avoids external complex-number packages.

The program demonstrates the distinction between a classical period-finding path and the small QFT-based path.

## C++17 Implementation

The C++ program treats the algorithm as a small numerical engine.

A `ShorOrderEngine` class separates base selection and order discovery from factor extraction.

The implementation uses:

- `std::optional` for operations that may fail,
- `std::vector` for factor collections,
- `std::pair` for two-factor results,
- STL algorithms and numeric utilities,
- exceptions for invalid inputs,
- `std::mt19937_64` for deterministic educational base selection,
- `unsigned __int128` for safe intermediate multiplication.

The widened multiplication is significant because calculating:

`(a × b) mod N`

can overflow a 64-bit intermediate even when `a`, `b`, and `N` individually fit in 64 bits.

The program keeps order discovery, period validation, and factor extraction separate so that a failed period does not get incorrectly interpreted as a failed factorization algorithm.

## Java 17 Implementation

The Java program models factorization as an explicit enterprise-style workflow.

The domain includes:

- `FactorizationRequest`,
- `FactorizationResult`,
- `FactorizationState`,
- `OrderFindingService`,
- `ClassicalOrderFindingService`,
- `FactorizationService`.

Java `record` types provide immutable request and result objects.

`FactorizationState` represents workflow transitions such as:

`RECEIVED`

`PREPROCESSED`

`ORDER_SEARCH`

`PERIOD_FOUND`

`FACTORS_RECOVERED`

`RETRY_REQUIRED`

`PRIME`

The `OrderFindingService` interface isolates the order-finding mechanism. The supplied implementation is classical and exists to provide a deterministic reference model.

A real quantum backend could replace that service without changing the factor-extraction domain logic.

`BigInteger` is used instead of primitive integer types so that the mathematical model is not artificially limited to 32-bit or 64-bit values.

## PostgreSQL Implementation

The PostgreSQL implementation models factorization as persistent relational state.

The principal relationships are:

    Factoring Job
        |
        +--> Factoring Attempts
        |
        +--> Factorization Result

A factoring job contains:

- the integer `N`,
- the current workflow state,
- the order-finding method,
- an attempt limit,
- the number of attempts used,
- timestamps.

Each factoring attempt contains:

- selected base `a`,
- `gcd(a, N)`,
- candidate period `r`,
- period parity,
- period validation state,
- candidate factors,
- failure information.

A final factorization result stores either a prime classification or a pair of non-trivial factors.

### Database Constraints

The schema uses:

- primary keys,
- foreign keys,
- unique constraints,
- check constraints,
- enum types,
- partial indexes,
- triggers,
- views,
- PL/pgSQL functions.

The `validate_attempt` trigger checks that the stored GCD agrees with the database's calculated GCD and that stored period-validation information agrees with modular exponentiation.

The `enforce_result` trigger verifies that a non-prime factorization result actually multiplies to the job's original integer.

### PostgreSQL Arithmetic

`NUMERIC(100, 0)` is used for stored integers so that the relational model is not restricted to native 32-bit or 64-bit arithmetic.

The `mod_pow_numeric` function implements repeated squaring inside PostgreSQL.

The `factor_from_period` function implements the classical factor-extraction stage directly in SQL/PLpgSQL.

## Continued Fractions

Quantum phase estimation produces an approximation related to:

`s / r`

where `s` is an integer and `r` is the unknown order.

A measured value `y` from a sufficiently large phase register approximates:

`y / Q ≈ s / r`

Continued fractions identify rational approximations whose denominators can reveal `r`.

The implementations therefore treat period recovery as a separate stage from QFT measurement.

For small examples, exact classical order computation can validate the candidate produced by the continued-fraction process.

## Edge Cases

Several cases prevent a single attempt from producing factors.

### Even Input

If `N` is even, the factor `2` is immediately available.

The quantum period-finding procedure is unnecessary for this case.

### Prime Input

A prime input does not require non-trivial factor extraction.

The implementations identify small primes before attempting the general workflow.

### Non-Coprime Base

If:

`gcd(a, N) > 1`

the selected base has already exposed a factor.

This is a successful classical preprocessing outcome rather than a period-finding result.

### Odd Period

An odd period cannot be directly used by the standard factor-extraction equation.

Another base must be selected.

### Trivial Half-Period Result

If:

`a^(r/2) ≡ -1 mod N`

the two gcd calculations do not provide the desired non-trivial factors.

The attempt is therefore retried.

### Invalid Period Candidate

A candidate period must satisfy:

`a^r mod N = 1`

before it is used for factor extraction.

The PostgreSQL trigger explicitly enforces this relationship.

## Performance

The computational characteristics differ substantially between the reference components.

| Component | Main operation | Educational complexity |
|---|---|---|
| Trial factorization | Trial division | Approximately `O(sqrt(N))` |
| Modular exponentiation | Repeated squaring | `O(log exponent)` modular multiplications |
| Classical order search | Sequential period testing | Up to `O(N log N)` arithmetic work in the simple implementation |
| Direct QFT | Dense state transformation | `O(Q²)` |
| State-vector storage | Amplitudes | `O(Q)` memory |
| PostgreSQL period validation | Modular repeated squaring | `O(log r)` loop iterations |

The direct QFT is the principal scalability limitation in the educational simulators.

A real quantum circuit does not explicitly materialize the full vector of amplitudes in the same way a classical state-vector simulator does.

## Security and Cryptographic Relevance

The significance of Shor's algorithm is its asymptotic impact on integer-factorization-based public-key cryptography.

Classical cryptographic systems based on the computational difficulty of factoring large integers rely on factoring remaining infeasible with known classical algorithms at relevant key sizes.

A sufficiently capable fault-tolerant quantum computer running Shor's algorithm would change that assumption.

This project does not implement cryptographic key recovery and does not operate on real private keys. Its examples use small public integers such as `15`, `21`, `35`, and `77` so that every mathematical step can be inspected.

Important security properties for real systems include:

- never exposing private keys to experimental factoring software,
- separating research simulations from production cryptographic infrastructure,
- validating all externally supplied integers,
- preventing integer overflow in modular multiplication,
- using exact integer arithmetic where required,
- treating quantum factorization capability as a cryptographic migration concern rather than as a conventional optimization.

## Limitations

The implementations are educational mathematical models rather than scalable quantum computers.

The main limitations are:

- small integer inputs,
- classical order-finding in the C++ and Java reference workflows,
- direct QFT state-vector simulation in Python and JavaScript,
- simplified continued-fraction recovery,
- simplified primality testing for demonstration purposes,
- no physical quantum noise model,
- no quantum error correction,
- no physical qubit mapping,
- no hardware-specific gate decomposition.

The distinction between a classical order finder and a quantum order finder is essential. The classical implementations reproduce the mathematical target of Shor's quantum subroutine but do not provide the quantum speedup.

## File Responsibilities

| File | Primary role |
|---|---|
| Python | Mathematical reference implementation, QFT state-vector simulation, continued fractions, validation |
| JavaScript | Node.js implementation using `BigInt`, event-compatible standard-library primitives, QFT probability sampling |
| C++17 | Numerical factoring engine with explicit modular arithmetic and widened multiplication |
| Java 17 | Enterprise-style domain model with services, records, interfaces, and explicit workflow states |
| PostgreSQL | Persistent factorization workflow, mathematical validation, constraints, reporting, and transactional state |
| README.md | Technical description of the mathematical and implementation relationships |

## Practical Relationship Between the Components

The five source implementations represent different layers of the same mathematical workflow.

    Shor's Algorithm
            |
       +----+----+
       |         |
       v         v
    Classical   Quantum
      logic    subroutine
       |         |
       |      Period finding
       |      QFT / phase estimation
       |         |
       +----+----+
            |
            v
     Candidate period r
            |
            v
     Even-period checks
            |
            v
     GCD factor extraction
            |
            v
      Non-trivial factors

The Python and JavaScript programs make the quantum-state representation visible. The C++ and Java implementations emphasize numerical correctness and domain separation. PostgreSQL demonstrates how the same mathematical state can be stored, validated, queried, and audited transactionally.

The central engineering principle is to keep **period discovery**, **period validation**, and **factor extraction** as separate operations. This prevents a failed period attempt from being confused with a failure of the complete factorization method.
