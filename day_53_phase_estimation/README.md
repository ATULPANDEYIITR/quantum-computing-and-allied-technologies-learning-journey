
# Quantum Phase Estimation

## Scope

Quantum Phase Estimation (QPE) estimates the phase associated with an eigenvalue of a unitary operator.

For a unitary operator \(U\) and eigenstate \(|\psi\rangle\),

\[
U|\psi\rangle = e^{2\pi i\theta}|\psi\rangle
\]

where \(0 \leq \theta < 1\).

QPE estimates \(\theta\) by encoding controlled powers of \(U\) into a counting register and then applying the inverse Quantum Fourier Transform (QFT). Measurement converts the encoded phase into an integer \(y\), with the standard estimate

\[
\hat{\theta}=\frac{y}{2^m}
\]

where \(m\) is the number of counting qubits.

The four source implementations use the same mathematical problem from different engineering perspectives:

| File | Perspective | Primary implementation |
|---|---|---|
| Python | State-vector learning simulator | Complete QPE execution and measurement simulation |
| JavaScript | Event-driven numerical model | QPE plus asynchronous batch evaluation |
| C++17 | Numerical systems case study | Explicit state-vector and performance-oriented implementation |
| Java 17 | Enterprise-style domain model | Records, domain types, validation, experiment state, numerical engine |
| PostgreSQL | Experimental data model | Persistent QPE experiments, circuit operations, probability distributions, measurements |

The implementations intentionally avoid external quantum-computing libraries. The purpose is to expose the mechanics of phase encoding, controlled powers, inverse QFT, and measurement directly.

## Mathematical mechanism

QPE uses two registers.

```text
Counting register:   |0> |0> ... |0>
                       |    |      |
                       H    H      H
                       |    |      |
                    controlled powers of U
                       |    |      |
Target register:     |psi> |psi> ... |psi>

After controlled-U operations:
        phase information is stored as relative phases

After inverse QFT:
        phase information becomes computational-basis amplitudes

Measurement:
        y
        |
        +--> estimate = y / 2^m
```

The target register must contain an eigenstate of \(U\). If the eigenstate condition is satisfied, each controlled power contributes a predictable phase factor.

For

\[
U|\psi\rangle=e^{2\pi i\theta}|\psi\rangle
\]

the operation \(U^{2^k}\) produces

\[
U^{2^k}|\psi\rangle=e^{2\pi i2^k\theta}|\psi\rangle
\]

The powers \(1,2,4,\ldots,2^{m-1}\) therefore encode progressively more significant binary information about \(\theta\).

## Counting-register resolution

With \(m\) counting qubits there are \(2^m\) possible measurement outcomes. The phase grid has spacing

\[
\frac{1}{2^m}
\]

For example, four counting qubits produce sixteen possible phase values:

| Measurement integer | Phase |
|---:|---:|
| 0 | 0 |
| 1 | 0.0625 |
| 2 | 0.125 |
| 4 | 0.25 |
| 8 | 0.5 |
| 10 | 0.625 |
| 15 | 0.9375 |

A phase such as \(0.625=10/16\) is exactly represented by four counting qubits. A phase such as \(0.37\) is not exactly represented on that grid, so QPE produces a probability distribution concentrated around the closest representable values.

Increasing the counting-register size improves phase resolution but increases the computational cost of a classical state-vector simulation exponentially.

## Controlled powers of the unitary

The controlled operations are the central phase-encoding mechanism.

For control qubit \(k\), QPE applies

\[
CU^{2^k}
\]

When the control qubit is \(|1\rangle\), the eigenstate receives the phase associated with \(U^{2^k}\). When the control is \(|0\rangle\), the target state is unchanged.

The Python implementation explicitly modifies amplitudes whose control-register bit is one. The JavaScript and C++ implementations use equivalent complex-amplitude transformations with different numerical representations. Java separates the unitary domain object from the state-vector engine.

This distinction matters because QPE is not simply repeated application of \(U\). The exponent doubles with each counting qubit, which is what extracts binary information about the phase.

## Inverse Quantum Fourier Transform

The inverse QFT converts relative phase information into computational-basis probability.

For a register of \(N=2^m\) states, the direct inverse transformation used by the simulators is

\[
a_y=\frac{1}{\sqrt{N}}\sum_{x=0}^{N-1}a_xe^{-2\pi ixy/N}
\]

The Python, JavaScript, C++, and Java implementations calculate this transformation explicitly. This is intentionally different from an optimized circuit implementation.

The direct matrix-style calculation has \(O(N^2)\) arithmetic complexity. Since \(N=2^m\), this becomes \(O(4^m)\) with respect to the number of counting qubits.

A physical QFT circuit is not implemented by constructing this full matrix. It uses Hadamard gates, controlled phase rotations, and qubit-order reversal. A hardware implementation therefore has a polynomial gate count in the number of qubits, although hardware noise and connectivity introduce other costs.

## Python implementation

The Python source is a dependency-free state-vector simulator.

The state is represented as a list of complex amplitudes. The implementation provides explicit functions for:

- Validation of phase and qubit counts
- Preparation of the counting register in \(|+\rangle^{\otimes m}\)
- Controlled \(U^{2^k}\) operations
- Inverse QFT
- Probability normalization
- Measurement sampling
- Precision comparison
- Circular phase-error evaluation
- Invalid-input handling

The target unitary is represented by the one-qubit phase operator

\[
P(\theta)=\operatorname{diag}(1,e^{2\pi i\theta})
\]

The target eigenstate is \(|1\rangle\), so

\[
P(\theta)|1\rangle=e^{2\pi i\theta}|1\rangle
\]

The simulator therefore does not need to store a separate target register for this particular unitary. It directly applies the resulting eigenphase to the counting-register amplitudes.

The script compares exactly representable and non-binary phases and prints both theoretical probabilities and sampled measurement histograms.

The explicit inverse QFT is useful for understanding the algorithm, but its exponential simulation cost makes it unsuitable for large registers.

## JavaScript implementation

The JavaScript implementation uses Node.js and defines a small `Complex` class rather than depending on a numerical package.

It complements the Python implementation by emphasizing:

- Object-oriented complex arithmetic
- Seeded pseudo-random measurement sampling
- Event-loop scheduling
- Asynchronous batch evaluation
- Explicit validation of runtime inputs

The asynchronous example uses `Promise.all()` and `setImmediate()` to model how several QPE jobs could be scheduled without blocking the Node.js event loop. The numerical QPE itself remains synchronous because it is a local calculation.

This distinction is useful in practical quantum-service applications. Circuit submission, remote execution, polling, and result collection are naturally asynchronous even though the mathematical transformation of an already available state vector is computationally synchronous.

The implementation also reports the probability distribution and sampled measurement histogram for a phase that is not exactly represented by the selected counting-register size.

## C++17 implementation

The C++ implementation treats QPE as a numerical systems problem.

It uses:

- `std::complex<double>` for amplitudes
- `std::vector` for the state vector
- Bit operations for controlled-qubit selection
- `std::polar` for phase factors
- `std::discrete_distribution` for measurement sampling
- Explicit validation and exception handling
- Deterministic random seeds for reproducible experiments

Bit operations are particularly important in a state-vector simulator. A computational-basis state is represented by an integer index, and

```cpp
(basis >> control) & 1
```

determines whether the relevant control qubit is \(|0\rangle\) or \(|1\rangle\).

The C++ version also makes the memory constraint explicit. A state vector with \(m\) qubits requires \(2^m\) complex amplitudes. Even before the inverse QFT is considered, this exponential state-space growth limits classical simulation.

The direct inverse QFT is retained because the objective is to expose the transformation rather than hide it behind a specialized numerical library.

## Java 17 implementation

The Java implementation uses a more explicit domain model.

`PhaseUnitary` represents the mathematical unitary and exposes its eigenvalue and powered eigenvalues. `PhaseEstimate` is a Java record representing an immutable result. `ReviewState` models the experiment lifecycle:

`PREPARED -> PHASE_ENCODED -> TRANSFORMED -> MEASURED`

The state-vector implementation uses an interleaved real/imaginary array:

```text
[real0, imaginary0, real1, imaginary1, ...]
```

This avoids external numerical dependencies while keeping the storage compact and predictable.

Java records provide immutable result objects, while validation methods reject phases outside the mathematical domain and counting-register sizes outside the simulator's practical bound.

The Java implementation also calculates both direct and circular phase error. Circular error is useful because phase is periodic:

\[
\min(|\theta-\hat{\theta}|,1-|\theta-\hat{\theta}|)
\]

## PostgreSQL representation

The PostgreSQL implementation treats QPE as experimental data rather than attempting to perform complex-number linear algebra inside SQL.

The relational model separates the major entities:

```text
phase_unitaries
      |
      v
qpe_experiments
      |
      +------------------+
      |                  |
      v                  v
qpe_operations     probability_outcomes
      |
      v
measurement_results
```

`phase_unitaries` stores the eigenphase and eigenstate metadata.

`qpe_experiments` stores the counting-register size, number of shots, experiment state, selected estimate, and completion information.

`qpe_operations` records the controlled powers used by an experiment. The `power_exponent` values follow the QPE sequence \(1,2,4,\ldots\).

`probability_outcomes` stores theoretical outcome probabilities and their corresponding phase-grid values.

`measurement_results` stores individual measured outcomes, making empirical distributions queryable independently from theoretical distributions.

The schema uses primary keys, foreign keys, uniqueness constraints, range checks, indexes, triggers, PL/pgSQL functions, a view, common table expressions, and transactional operations.

## Database integrity

The database enforces several rules directly.

A unitary phase must satisfy

```sql
0 <= eigenphase AND eigenphase < 1
```

A counting register must contain between one and twenty qubits in this demonstration schema.

For \(m\) counting qubits, a measured integer must satisfy

```text
0 <= outcome < 2^m
```

The `qpe_record_measurement` function locks the experiment row before validating and recording a measurement. This prevents the validation from operating against an inconsistent experiment definition during concurrent updates.

The `qpe_validate_estimate` trigger derives `estimated_phase` from the measured integer when necessary and rejects a measured experiment that lacks an estimate.

These rules illustrate an important separation: application code can calculate QPE, while the database protects the integrity of stored experimental results.

## Theoretical probability distribution

When the target phase is not exactly represented by the counting register, measurement is probabilistic.

For outcome \(y\) and \(N=2^m\), the standard QPE probability can be written as

\[
p(y)=\frac{1}{N^2}\left|\sum_{k=0}^{N-1}e^{2\pi ik(\theta-y/N)}\right|^2
\]

The PostgreSQL function `qpe_theoretical_probability` uses the equivalent sine-ratio form.

This makes the database capable of storing and reporting expected probability distributions without storing complex amplitudes.

The probability peak becomes narrower as the counting-register size increases. The trade-off is improved phase precision at the cost of more qubits and, for classical simulation, substantially more state.

## Exact versus approximate estimation

Two cases are important.

### Exactly representable phase

For \(\theta=0.625\),

\[
0.625=\frac{10}{16}
\]

Four counting qubits therefore provide an exact grid point. The ideal simulator concentrates the measurement probability at integer 10.

The resulting estimate is

```text
10 / 16 = 0.625
```

### Non-binary-grid phase

For \(\theta=0.37\), five counting qubits provide 32 grid points. The exact phase is not a multiple of \(1/32\).

The inverse QFT therefore produces a distribution around the nearest relevant outcomes rather than a single exact computational-basis result.

This is not an implementation failure. It is the expected behavior of finite-resolution phase estimation.

## Measurement and sampling

An ideal state-vector calculation produces probabilities. A physical or simulated experiment produces measurement outcomes.

The Python, JavaScript, C++, and Java implementations therefore distinguish:

- Amplitude state
- Probability distribution
- Most likely outcome
- Sampled measurement results

A histogram of repeated shots approximates the underlying probability distribution.

For a sufficiently large number of shots, the empirical frequency of an outcome approaches its theoretical probability. A small number of shots can produce a noisy histogram even when the underlying QPE calculation is exact.

The PostgreSQL model stores individual shots and can calculate empirical frequencies with aggregation.

## Failure conditions and numerical limitations

The implementations reject phases outside the standard interval \([0,1)\). A phase of exactly `1` is equivalent to phase zero mathematically, but the chosen representation normalizes the phase domain to one period.

The state-vector simulators also reject excessively large register sizes. This is a practical protection against allocating enormous arrays rather than a mathematical limitation of QPE.

Floating-point arithmetic introduces small normalization and phase errors. These become increasingly relevant as numerical state sizes and circuit depths grow.

The direct inverse QFT is also a major computational limitation. With \(m\) counting qubits, the state has \(2^m\) amplitudes and the direct transform performs approximately \(4^m\) complex-arithmetic operations.

The database representation does not attempt to reproduce the entire quantum state. It records experiment metadata, theoretical distributions, and measurements, which is appropriate for persistence and reporting but not for simulating arbitrary quantum circuits.

## Precision and resource trade-off

The fundamental relationship is:

| Counting qubits | Possible outcomes | Phase-grid spacing |
|---:|---:|---:|
| 3 | 8 | 0.125 |
| 4 | 16 | 0.0625 |
| 5 | 32 | 0.03125 |
| 6 | 64 | 0.015625 |

More counting qubits provide finer resolution.

For a classical state-vector simulator, this improvement is expensive because the state-space size doubles for every additional simulated qubit.

For quantum hardware, the resource trade-off is different. The register grows linearly in the number of qubits, but additional controlled operations and inverse-QFT gates increase circuit depth and exposure to noise.

## Practical interpretation

QPE is valuable because phase is often hidden inside a unitary eigenvalue rather than directly observable as a classical scalar.

The algorithm converts that phase into measurable information through a sequence of transformations:

```text
Known eigenstate
      |
      v
Hadamard counting register
      |
      v
Controlled U, U², U⁴, ...
      |
      v
Relative phase encoding
      |
      v
Inverse QFT
      |
      v
Probability distribution
      |
      v
Measurement integer y
      |
      v
Phase estimate y / 2^m
```

The implementations keep this workflow distinct from general quantum simulation. They focus specifically on eigenphase encoding, controlled unitary powers, inverse Fourier transformation, finite precision, and measurement.

## Security and production considerations

QPE itself is a mathematical algorithm rather than an authentication mechanism. Production systems executing QPE experiments still need ordinary application controls.

Experiment identifiers should be treated as untrusted input when exposed through an API. Database functions should validate identifiers and outcome ranges before inserting measurements.

Deterministic random seeds are useful for educational and testing environments but should not be confused with physical quantum randomness.

For production quantum workloads, numerical simulation should not be assumed to scale to hardware-sized circuits. Classical state-vector simulation has exponential memory requirements. Circuit execution should instead use an appropriate quantum execution backend, while the persistence layer records circuit configuration, calibration context, execution metadata, measurement results, and reproducibility information.

The central engineering boundary is therefore clear:

- QPE defines how phase information is encoded and estimated.
- The numerical implementations demonstrate the algorithm on classical state vectors.
- The database records experiments and their results.
- A production quantum execution system would provide the actual quantum state evolution and measurement process.
