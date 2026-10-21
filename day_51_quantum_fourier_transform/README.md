# Quantum Fourier Transform Fundamentals

## Scope

This project develops the Quantum Fourier Transform (QFT) from its mathematical definition into executable state-vector simulations.

The central operation for a register of dimension \(N = 2^n\) is

\[
|j\rangle \mapsto
\frac{1}{\sqrt{N}}
\sum_{k=0}^{N-1}
e^{2\pi i jk/N}|k\rangle.
\]

For an arbitrary state

\[
|\psi\rangle =
\sum_{j=0}^{N-1} a_j|j\rangle,
\]

the transformed amplitude at frequency \(k\) is

\[
b_k =
\frac{1}{\sqrt{N}}
\sum_{j=0}^{N-1}
a_j e^{2\pi i jk/N}.
\]

The implementations use the positive phase convention for the forward QFT and the negative phase convention for the inverse QFT.

The four implementations use different computational perspectives:

| File | Primary perspective |
|---|---|
| Python | Direct state-vector model with validation, numerical verification, and measurement simulation |
| JavaScript | Event-driven QFT analysis with explicit complex-number objects |
| C++17 | Numerical linear-algebra case study with explicit matrices and stochastic measurement |
| Java 17 | Domain-oriented QFT service with immutable records and explicit transformation direction |
| PostgreSQL | Relational representation of amplitudes, probabilities, experiments, and measurement observations |

The implementations are intentionally independent. They share the same mathematical model but do not merely translate one program into another language.

---

## Mathematical Model

The QFT is the normalized discrete Fourier transform applied to quantum amplitudes.

For \(N\) basis states, its matrix is

\[
F_N =
\frac{1}{\sqrt{N}}
\begin{bmatrix}
1 & 1 & 1 & \cdots & 1 \\
1 & \omega & \omega^2 & \cdots & \omega^{N-1} \\
1 & \omega^2 & \omega^4 & \cdots & \omega^{2(N-1)} \\
\vdots & \vdots & \vdots & \ddots & \vdots \\
1 & \omega^{N-1} & \omega^{2(N-1)} &
\cdots & \omega^{(N-1)^2}
\end{bmatrix},
\]

where

\[
\omega = e^{2\pi i/N}.
\]

The normalization factor \(1/\sqrt{N}\) is essential. It makes the transformation unitary, meaning

\[
F_N^\dagger F_N = I.
\]

Consequently, the QFT preserves the norm of a valid quantum state and can be reversed by its conjugate-transpose transformation.

---

## Amplitudes and Measurement

A quantum state stores amplitudes, not direct probabilities.

For an amplitude

\[
a = x + iy,
\]

the computational-basis measurement probability is

\[
P = |a|^2 = x^2+y^2.
\]

The probabilities must satisfy

\[
\sum_k |a_k|^2 = 1.
\]

The programs therefore reject unnormalized states rather than silently treating arbitrary vectors as valid quantum states.

After a QFT, measurement does not expose the complex phase directly. Measurement samples computational-basis indices according to the squared magnitude of their transformed amplitudes.

This distinction is important:

| Quantity | Meaning |
|---|---|
| Real part | Real component of an amplitude |
| Imaginary part | Imaginary component of an amplitude |
| Complex phase | Relative phase information carried by amplitudes |
| Squared magnitude | Probability of observing the associated basis state |
| Measurement result | One sampled computational-basis outcome |

---

## Python Implementation

The Python implementation provides the broadest direct state-vector treatment.

It validates that:

- the state is non-empty;
- the dimension is a power of two;
- every state is normalized;
- measurement shots are positive;
- basis-state indices are valid.

The `qft()` function implements the mathematical definition directly with nested loops. Its time complexity is \(O(N^2)\), while the state vector requires \(O(N)\) storage.

`inverse_qft()` changes the Fourier phase from positive to negative and uses the same normalization. Applying the inverse transformation after the forward transformation tests numerical reversibility.

The script also constructs the QFT matrix and checks its unitarity numerically. This is a stronger property check than simply observing that one example appears to transform correctly.

The classical DFT calculation provides a useful mathematical comparison. The QFT state-vector transformation is the normalized DFT of the amplitude vector under the chosen phase convention.

The measurement simulator uses probabilities derived from amplitudes and samples outcomes according to those probabilities. A local random generator makes the demonstration reproducible when a seed is supplied.

---

## JavaScript Implementation

The JavaScript implementation models complex arithmetic through a dedicated `Complex` class rather than relying on an external numerical library.

The `Complex` class supports:

- addition;
- multiplication;
- scaling;
- conjugation;
- magnitude;
- squared magnitude;
- polar-form construction.

The state validation layer checks both dimensional structure and normalization.

The JavaScript implementation adds an event-driven perspective. Analysis jobs are scheduled with `setImmediate()` and executed through `Promise`-based asynchronous control flow. Independent calculations such as unitarity verification, basis-state transformation, periodic-state transformation, and inverse-QFT testing can therefore be coordinated through `Promise.all()`.

The periodic-state example is particularly important. A state proportional to

\[
|000\rangle + |100\rangle
\]

has periodic structure in its computational-basis amplitudes. The Fourier transformation exposes that structure as a concentrated frequency pattern.

The implementation also separates probability generation from measurement sampling. This makes the distinction between the deterministic QFT transformation and the stochastic measurement process explicit.

---

## C++17 Implementation

The C++ implementation emphasizes numerical computation and explicit resource-oriented data structures.

`std::complex<double>` provides the complex arithmetic required by the Fourier transformation. State vectors use `std::vector`, while the explicit QFT matrix is represented as a vector of complex-number rows.

The implementation contains separate operations for:

- validating normalized states;
- normalizing raw vectors;
- constructing computational-basis states;
- calculating the forward QFT;
- calculating the inverse QFT;
- constructing a QFT matrix;
- checking matrix unitarity;
- converting amplitudes to probabilities;
- sampling measurements.

The QFT matrix verification computes the inner products of matrix columns and compares them against the identity matrix. This tests

\[
F^\dagger F = I
\]

within floating-point tolerance.

The C++ measurement implementation uses `std::discrete_distribution`, which is appropriate for sampling from a discrete probability distribution. The random generator is kept separate from the deterministic transformation code.

The direct QFT remains \(O(N^2)\). This is suitable for a small educational simulator but becomes impractical as the number of qubits grows because \(N=2^n\). A state-vector simulator already has exponential memory requirements before the \(O(N^2)\) transformation cost is considered.

---

## Java 17 Implementation

The Java implementation uses explicit domain types to make QFT invariants visible in the program structure.

`Complex` is an immutable record containing the real and imaginary components.

`QuantumState` is another record that validates its dimension, prevents null amplitudes, copies the supplied array, and verifies normalization.

`TransformDirection` is an enum distinguishing the forward and inverse transformations. This prevents the sign convention from being represented as an unexplained Boolean at the public service boundary.

`QftService` contains the transformation and unitarity-verification behavior. The service accepts a validated `QuantumState` and returns another validated state.

This design creates a clear domain boundary:

    Raw numerical values
            |
            v
    Normalized QuantumState
            |
            v
         QftService
         /        \
    Forward      Inverse
         \        /
            v
    Validated QuantumState

The implementation also models measurement as a separate operation. QFT itself is deterministic for a given input state, while measurement introduces probabilistic sampling.

The matrix verification intentionally limits the matrix size used for explicit unitarity testing. Constructing an \(N \times N\) QFT matrix becomes expensive quickly, even though the mathematical QFT can be described compactly.

---

## PostgreSQL Model

The PostgreSQL implementation treats QFT experiments as persistent numerical records.

The central entities are:

| Table | Purpose |
|---|---|
| `qft_experiment` | Register size, dimension, direction, and experiment metadata |
| `qft_amplitude` | Complex computational-basis amplitudes and derived probabilities |
| `measurement_result` | Observed counts from repeated computational-basis measurements |

The experiment table derives the register dimension from the number of qubits:

`dimension = 2 ^ qubits`

The amplitude table stores real and imaginary components separately. PostgreSQL generated columns calculate

`real_part² + imaginary_part²`

as the measurement probability.

This keeps the stored representation normalized to the underlying mathematical model rather than storing probability as an independently editable value.

---

## Database Integrity

Several rules are enforced directly by PostgreSQL.

The experiment model restricts the number of qubits to a practical simulation range and limits the transformation direction to `forward` or `inverse`.

Amplitude records require non-negative basis indices and use a composite primary key:

`(experiment_id, basis_index)`

This prevents duplicate amplitudes for the same basis state within one experiment.

Measurement records require positive shot counts and constrain observed counts to the interval

`0 <= observed_count <= shots`

Foreign keys ensure that amplitudes and measurements cannot exist without their parent experiment.

Indexes are placed on experiment-associated probabilities and measurement history because those are natural access paths for analytical queries.

---

## SQL QFT Calculation

The SQL function `qft_amplitude()` evaluates one transformed frequency directly from stored amplitudes.

It calculates the real and imaginary components separately:

\[
\operatorname{Re}(b_k) =
\frac{1}{\sqrt{N}}
\sum_j
\left(
x_j\cos\theta_{jk}
-
y_j\sin\theta_{jk}
\right)
\]

and

\[
\operatorname{Im}(b_k) =
\frac{1}{\sqrt{N}}
\sum_j
\left(
x_j\sin\theta_{jk}
+
y_j\cos\theta_{jk}
\right),
\]

where

\[
\theta_{jk} = \frac{2\pi jk}{N}.
\]

This makes the complex-number arithmetic explicit even though PostgreSQL does not have a built-in complex scalar type equivalent to the numerical types used by the source-language implementations.

The `generate_series()` function is used to enumerate computational-basis indices and Fourier frequencies.

---

## Normalization Validation

`validate_quantum_state()` checks two separate conditions.

First, the number of stored amplitudes must equal the expected Hilbert-space dimension.

Second, the squared amplitude magnitudes must sum to approximately one.

Both checks are necessary. A state could have the correct number of amplitudes but still violate normalization, or it could have a normalized subset of amplitudes while failing to represent the complete register.

Floating-point tolerance is used because Fourier calculations involve trigonometric functions and therefore cannot be expected to produce exact decimal values.

---

## Periodicity and the QFT

A major reason the QFT is important in quantum algorithms is its relationship with periodic structure.

Consider a state containing equally weighted amplitudes at selected computational indices. The QFT converts structure in the index domain into structure in the frequency domain.

For the demonstration state

\[
\frac{|000\rangle + |100\rangle}{\sqrt{2}},
\]

the amplitudes have a regular spacing of four in an eight-dimensional register.

The transformed state therefore exhibits constructive and destructive interference. Some frequency amplitudes become large while others cancel.

This is a central QFT mechanism: the transformation does not merely rearrange amplitudes. Relative phases cause interference that reveals periodic or phase-related structure.

---

## QFT Versus a Classical DFT

The QFT and classical DFT share the same Fourier mathematics but operate in different computational contexts.

A classical DFT transforms a numerical vector.

A QFT transforms the amplitudes of a quantum state using a unitary operator.

The normalization convention is therefore important. The QFT uses \(1/\sqrt{N}\), which makes the transformation unitary. Classical DFT libraries may instead place normalization on the forward transform, inverse transform, or split it between both directions.

The QFT should not be interpreted as a generic replacement for an FFT implementation. A quantum circuit realizes the Fourier transformation through a structured sequence of quantum gates, while these source files use direct state-vector simulation.

---

## Direct QFT Complexity

The implementations calculate every output frequency from every input amplitude.

For \(N\) amplitudes:

\[
T(N)=O(N^2).
\]

Since

\[
N=2^n,
\]

this becomes

\[
O(4^n)
\]

when expressed directly in terms of the number of qubits for the dense state-vector QFT calculation.

State storage is already

\[
O(2^n).
\]

The explicit QFT matrix requires

\[
O(N^2)
\]

memory and is therefore considerably more expensive than storing only the state vector.

These implementations intentionally favor transparency over large-scale simulation performance.

---

## Numerical Precision

All implementations use floating-point arithmetic.

Expressions such as

\[
e^{i\theta}
\]

are evaluated through sine and cosine functions. Values that are theoretically zero may therefore appear as very small nonzero values.

The programs use tolerances such as `1e-10` or `1e-9` when checking normalization, unitarity, and inverse reconstruction.

The tolerance should not be interpreted as part of the mathematical definition of the QFT. It is a numerical engineering threshold for deciding whether floating-point error is acceptably small.

---

## Edge Cases and Failure Conditions

The implementations reject several invalid conditions rather than producing misleading results.

### Invalid dimensions

A multi-qubit register has dimension

\[
2^n.
\]

Consequently, dimensions such as 3, 5, or 10 are rejected by the state-vector implementations.

### Unnormalized states

An amplitude vector whose squared magnitudes do not sum to one is rejected.

Normalization is provided explicitly where a raw vector is intentionally used as an intermediate mathematical representation.

### Zero vectors

The zero vector cannot be normalized because its norm is zero. The implementations raise an error rather than dividing by zero.

### Invalid basis indices

Computational-basis indices must fall within

\[
0 \leq j < 2^n.
\]

### Invalid measurement counts

Measurement operations require a positive number of shots, and database records prevent observed counts from exceeding the total number of shots.

### Numerical cancellation

Fourier interference can produce theoretically zero amplitudes. Floating-point arithmetic may represent these as very small values instead.

---

## Forward and Inverse QFT

The forward transformation uses

\[
F_{jk} = \frac{1}{\sqrt{N}} e^{2\pi ijk/N}.
\]

The inverse transformation uses

\[
F^{-1}_{jk} = \frac{1}{\sqrt{N}} e^{-2\pi ijk/N}.
\]

Because the QFT is unitary,

\[
F^{-1}=F^\dagger.
\]

The source implementations explicitly transform a state forward and then backward and measure the reconstruction error.

A small reconstruction error demonstrates numerical reversibility. A large error indicates an implementation error, an invalid state, or insufficient numerical precision.

---

## Measurement Workflow

The complete conceptual workflow is:

    Normalized quantum state
              |
              v
          Apply QFT
              |
              v
      Transformed amplitudes
              |
              v
          |amplitude|²
              |
              v
     Measurement probabilities
              |
              v
        Repeated sampling
              |
              v
    Observed computational states

The QFT itself does not select one measurement outcome.

The transformed state contains amplitudes for all possible computational-basis outcomes. Measurement converts those amplitudes into a probability distribution and samples from it.

Repeated measurements therefore produce empirical frequencies that approach the theoretical probabilities as the number of shots increases.

---

## Security and Reliability Considerations

These examples are numerical learning artifacts rather than production quantum-control systems.

For reliable scientific computation, production implementations would need explicit treatment of:

- floating-point error bounds;
- reproducible random-number policies;
- numerical conditioning;
- maximum supported qubit counts;
- memory consumption;
- deterministic experiment metadata;
- input validation;
- reproducible measurement seeds where appropriate;
- independent verification of transformation conventions.

The PostgreSQL model also separates theoretical probabilities from observed measurement counts. This prevents an observation from being confused with the mathematical state from which it was sampled.

No implementation treats measurement results as proof that an individual Fourier amplitude has a directly observable complex phase. Phase information affects interference, while computational-basis measurement exposes probabilities.

---

## Relationship Between the Five Implementations

The implementations intentionally divide responsibilities.

The Python program is the most direct mathematical reference. It provides normalization, state validation, QFT, inverse QFT, matrix unitarity checks, classical DFT comparison, and measurement simulation.

The JavaScript program emphasizes object-oriented complex arithmetic and asynchronous execution. Its event-driven orchestration demonstrates that independent QFT analyses can be scheduled and aggregated without changing the underlying mathematics.

The C++ program focuses on explicit numerical linear algebra, standard-library complex arithmetic, matrix verification, and stochastic sampling.

The Java program makes QFT domain rules explicit through immutable records and an enum representing transformation direction. Its service boundary separates state validation from transformation policy.

The PostgreSQL script persists experiments and amplitudes, derives probabilities through generated columns, evaluates Fourier components using SQL functions, validates normalization, records measurements, and produces analytical reports.

Together, they represent the same QFT fundamentals through distinct implementation models rather than five copies of one program.
