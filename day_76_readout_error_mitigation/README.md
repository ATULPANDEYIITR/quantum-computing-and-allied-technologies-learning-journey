# Readout Error Mitigation: Measurement-Error Correction

## 1. Technical Scope

Readout error mitigation is a measurement-level correction technique used in quantum computing. It addresses inaccuracies introduced when a quantum processor measures computational basis states.

A quantum measurement can produce an incorrect classical bit even when the underlying quantum state has been prepared correctly. These errors affect measured probability distributions, expectation values, correlation functions, and experimental conclusions.

The implementation focuses on characterizing measurement errors through calibration experiments and correcting observed probability distributions using assignment matrices.

The five source implementations provide complementary perspectives:

| File | Engineering perspective | Primary implementation |
|---|---|---|
| Python | Numerical experimentation | Calibration, correction, simulation, bootstrap uncertainty |
| JavaScript | Event-driven processing | Calibration events, drift monitoring, asynchronous batches |
| C++17 | Numerical and computational engine | Matrix operations and constrained optimization |
| Java 17 | Enterprise architecture | Domain types, policies, audit events, asynchronous processing |
| PostgreSQL | Experimental data governance | Relational calibration, experiment tracking, integrity enforcement |

## 2. Measurement Errors in Quantum Computing

### 2.1 Ideal and observed measurements

For an ideal measurement, the probability distribution of computational basis outcomes is represented by:

\[
p =
\begin{bmatrix}
p_0\\
p_1
\end{bmatrix}
\]

For a single qubit:

\[
p_0+p_1=1
\]

A real measurement apparatus can confuse the prepared states.

For example:

- A prepared zero can be measured as one.
- A prepared one can be measured as zero.
- The two error probabilities need not be equal.

This asymmetry is important. A model that assumes identical zero-to-one and one-to-zero error rates can produce inaccurate corrections.

### 2.2 Assignment matrix

The assignment matrix describes the probability of observing a measurement outcome given a known prepared state.

For one qubit:

\[
A =
\begin{bmatrix}
P(0|0)&P(0|1)\\
P(1|0)&P(1|1)
\end{bmatrix}
\]

The first column describes measurements when the prepared state is zero.

The second column describes measurements when the prepared state is one.

The matrix must satisfy:

\[
\sum_i A_{ij}=1
\]

for every prepared state \(j\).

The observed distribution is:

\[
q=Ap
\]

where:

- \(p\) is the ideal distribution.
- \(A\) is the assignment matrix.
- \(q\) is the observed distribution.

The measurement correction problem attempts to estimate \(p\) from \(q\) and \(A\).

### 2.3 Asymmetric measurement errors

Consider the following calibration:

\[
P(0|0)=0.94
\]

\[
P(1|1)=0.91
\]

The corresponding assignment matrix is:

\[
A =
\begin{bmatrix}
0.94&0.09\\
0.06&0.91
\end{bmatrix}
\]

The probability of incorrectly reading zero as one is 0.06.

The probability of incorrectly reading one as zero is 0.09.

These probabilities must remain separate throughout calibration and correction.

## 3. Calibration Experiments

Calibration uses known computational basis states.

For each qubit, two experiments are performed:

| Experiment | Prepared state | Measurement objective |
|---|---|---|
| Zero calibration | \(|0\rangle\) | Estimate zero-to-zero and zero-to-one probabilities |
| One calibration | \(|1\rangle\) | Estimate one-to-zero and one-to-one probabilities |

If 10,000 zero-state shots produce 9,400 zero measurements and 600 one measurements:

\[
P(0|0)=\frac{9400}{10000}=0.94
\]

Similarly, if 10,000 one-state shots produce 9,100 one measurements:

\[
P(1|1)=\frac{9100}{10000}=0.91
\]

The remaining entries are obtained from the corresponding conditional probabilities.

Calibration is not a permanent hardware property. It can change because of:

- Qubit frequency drift.
- Readout resonator changes.
- Environmental fluctuations.
- Control electronics.
- Measurement-chain instability.
- Hardware recalibration.

A calibration must therefore be associated with a particular instrument, calibration version, and measurement period.

## 4. Multi-Qubit Assignment Matrices

For multiple qubits, the assignment matrix represents transitions between computational basis states.

For two qubits, the basis states are:

\[
|00\rangle,\ |01\rangle,\ |10\rangle,\ |11\rangle
\]

Under an independent-readout approximation:

\[
A_{2}=A_1\otimes A_0
\]

The symbol \(\otimes\) denotes the Kronecker product.

For two single-qubit matrices:

\[
A_0=
\begin{bmatrix}
a&b\\
c&d
\end{bmatrix}
\]

\[
A_1=
\begin{bmatrix}
e&f\\
g&h
\end{bmatrix}
\]

their tensor product is:

\[
A_1\otimes A_0 =
\begin{bmatrix}
ea&eb&fa&fb\\
ec&ed&fc&fd\\
ga&gb&ha&hb\\
gc&gd&hc&hd
\end{bmatrix}
\]

The resulting matrix has \(2^n\) rows and \(2^n\) columns for \(n\) qubits.

### Independent and correlated readout errors

The tensor-product model assumes that individual qubit measurement errors are independent.

Real devices can exhibit correlated readout errors.

Examples include:

- Crosstalk between neighboring readout channels.
- Shared resonator effects.
- Correlated measurement electronics.
- Simultaneous-readout interference.

For correlated errors, a complete multi-qubit assignment matrix should be estimated directly.

The PostgreSQL implementation includes an `assignment_matrix_entries` table for storing these joint probabilities.

The Python, JavaScript, C++, and Java implementations use the tensor-product approximation.

## 5. Mathematical Correction

### 5.1 Direct matrix inversion

If the assignment matrix is invertible:

\[
p=A^{-1}q
\]

This provides a direct mathematical correction.

There are important limitations:

- The matrix may be singular.
- The matrix may be poorly conditioned.
- Statistical noise can be amplified.
- Corrected probabilities may become negative.
- Corrected probabilities may exceed one.

A direct inverse is therefore not always appropriate for experimental data.

### 5.2 Constrained least squares

The implementations use a constrained optimization approach:

\[
\min_p
\left\{
\|Ap-q\|_2^2+
\lambda\|p\|_2^2
\right\}
\]

subject to:

\[
p_i\geq 0
\]

and:

\[
\sum_i p_i=1
\]

Here:

- \(A\) is the assignment matrix.
- \(q\) is the observed distribution.
- \(p\) is the corrected distribution.
- \(\lambda\) is the regularization parameter.

Regularization reduces sensitivity to numerical instability.

The probability constraints preserve the interpretation of the corrected result as a probability distribution.

### 5.3 Projected-gradient optimization

The objective has gradient:

\[
\nabla f(p)=
2A^T(Ap-q)+2\lambda p
\]

A gradient-descent update is:

\[
p_{k+1}=
\Pi_{\Delta}
\left[
p_k-\eta\nabla f(p_k)
\right]
\]

where:

- \(\eta\) is the learning rate.
- \(\Pi_{\Delta}\) is projection onto the probability simplex.
- \(\Delta\) represents nonnegative distributions summing to one.

The implementation uses a row-sum bound on the regularized Gram matrix to select a conservative learning rate.

Convergence is evaluated through the maximum change between successive probability estimates.

The final residual is:

\[
r=\|Ap_{\text{corrected}}-q\|_2
\]

A small residual indicates that the corrected distribution reproduces the observed distribution under the calibrated assignment model.

A small residual does not independently establish that the calibration is accurate or that the correction is statistically reliable.

## 6. Python Implementation

### 6.1 Numerical experimentation

The Python script uses standard-library components and separates the principal operations into reusable functions and classes.

`ReadoutCalibration` represents the calibration data for an individual qubit.

`ReadoutMitigator` manages:

- Calibration validation.
- Assignment matrix construction.
- Multi-qubit tensor products.
- Measurement-count conversion.
- Constrained optimization.
- Residual calculation.
- Calibration persistence.

The `MitigationResult` dataclass separates raw and corrected probability distributions.

### 6.2 Simulation

The simulator generates observed measurement counts from a known probability distribution.

The workflow is:

\[
p_{\text{true}}
\rightarrow
Ap_{\text{true}}
\rightarrow
\text{Shot Sampling}
\rightarrow
q_{\text{observed}}
\]

The mitigation engine then estimates the original distribution.

A fixed random seed makes the example reproducible.

### 6.3 Bootstrap uncertainty

The bootstrap implementation resamples the observed measurement outcomes.

Each bootstrap sample is independently corrected.

For an observable with eigenvalues \(o_i\), its estimated expectation is:

\[
\langle O\rangle=
\sum_i p_i o_i
\]

The bootstrap procedure estimates the variation of this expectation across resampled experiments.

The reported standard deviation measures sampling variability under the resampling procedure. It does not include all systematic calibration uncertainties.

### 6.4 Persistence

Calibration information is stored in JSON.

The saved information includes:

- Qubit identifiers.
- Calibration shot counts.
- Conditional measurement probabilities.
- Regularization configuration.

Production systems should use controlled storage permissions, calibration timestamps, instrument identifiers, and immutable version records.

## 7. JavaScript Implementation

### 7.1 Event-driven architecture

The JavaScript implementation models calibration and measurement correction as an event-driven service.

The `ReadoutEngine` extends Node.js `EventEmitter`.

Its principal events are:

| Event | Meaning |
|---|---|
| `audit` | An operational event was recorded |
| `calibrated` | A new calibration became active |
| `mitigated` | A measurement correction completed |

This separation allows measurement processing and operational monitoring to use different event handlers.

### 7.2 Calibration versioning

Every successful calibration update increments the internal version.

Each correction result records the calibration version used.

This is important because a corrected measurement distribution must be traceable to the calibration that produced it.

### 7.3 Drift monitoring

The `detectDrift` method compares a new calibration with an existing baseline.

For each qubit:

\[
D=
\max(
|P_{\text{new}}(0|0)-P_{\text{old}}(0|0)|,
|P_{\text{new}}(1|1)-P_{\text{old}}(1|1)|
)
\]

If:

\[
D>\tau
\]

where \(\tau\) is the configured threshold, the engine reports calibration drift.

The drift indicator does not automatically establish a complete hardware failure. It identifies a change requiring investigation and potentially a new calibration.

### 7.4 Asynchronous processing

`processBatch` processes experiments through asynchronous promises.

The implementation preserves deterministic audit ordering and prevents calibration changes during a batch.

Production systems may distribute independent experiments across workers, provided every experiment retains its calibration version and execution context.

## 8. C++17 Implementation

### 8.1 Numerical engine

The C++ program emphasizes computational efficiency and explicit numerical operations.

The `MatrixOperations` class provides:

- Matrix transposition.
- Matrix multiplication.
- Matrix-vector multiplication.
- Tensor products.
- Simplex projection.
- Euclidean norm calculation.

`ReadoutGovernanceEngine` owns calibration state and performs correction.

### 8.2 Domain separation

The program separates:

| Structure | Responsibility |
|---|---|
| `Calibration` | Conditional measurement probabilities |
| `Measurement` | Observed bitstring counts |
| `MitigationResult` | Corrected distribution and diagnostics |
| `MatrixOperations` | Numerical computation |
| `ReadoutGovernanceEngine` | Calibration and correction lifecycle |

This organization keeps numerical operations separate from experiment state.

### 8.3 Memory and computational considerations

For \(n\) qubits, the full assignment matrix contains:

\[
4^n
\]

entries.

A dense matrix therefore becomes expensive as the qubit count increases.

For an assignment matrix of dimension \(d=2^n\):

- Storage complexity is \(O(d^2)\).
- Dense matrix multiplication is \(O(d^3)\).
- Matrix-vector multiplication is \(O(d^2)\).
- Each projected-gradient iteration requires approximately \(O(d^2)\) work.

The tensor-product construction avoids manually defining every multi-qubit transition but does not eliminate the exponential size of the resulting dense matrix.

Large systems require additional structure, including sparse representations, tensor-network methods, local approximations, or alternative correction techniques.

## 9. Java 17 Enterprise Implementation

### 9.1 Domain architecture

The Java implementation separates measurement correction from enterprise governance.

Its principal domain types include:

- `Calibration`
- `MitigationPolicy`
- `MitigationResult`
- `AuditEvent`
- `CalibrationState`
- `ExperimentState`

The use of records provides immutable representations of calibration and policy data.

### 9.2 Policy enforcement

`MitigationPolicy` defines:

| Parameter | Purpose |
|---|---|
| Regularization | Controls numerical stabilization |
| Tolerance | Defines convergence precision |
| Maximum iterations | Limits optimization execution |
| Minimum calibration shots | Rejects insufficient calibration data |
| Drift threshold | Defines calibration change sensitivity |

The service rejects calibration data that fails its minimum-shot requirement.

### 9.3 Service responsibilities

`ReadoutMitigationService` manages:

- Calibration activation.
- Assignment matrix construction.
- Experiment validation.
- Measurement correction.
- Calibration versioning.
- Drift detection.
- Audit records.

`CalibrationRepository` separates persistence from correction logic.

`ExperimentProcessor` uses an executor service to process independent experiments asynchronously.

### 9.4 Failure management

The enterprise implementation explicitly distinguishes:

- Missing calibration.
- Invalid measurement counts.
- Insufficient calibration samples.
- Invalid policy settings.
- Stale calibration.
- Optimization failure.
- Asynchronous execution failure.

These conditions should be recorded separately because they require different operational responses.

## 10. PostgreSQL Data Model

The database represents the experimental lifecycle and its governance records.

### 10.1 Relational entities

| Table | Responsibility |
|---|---|
| `laboratories` | Research organization |
| `instruments` | Quantum measurement hardware |
| `researchers` | Authorized personnel |
| `calibration_campaigns` | Versioned calibration executions |
| `qubit_calibrations` | Individual qubit calibration results |
| `assignment_matrix_entries` | Full correlated assignment matrices |
| `experiments` | Measurement experiments |
| `measurement_counts` | Observed computational basis counts |
| `corrected_probabilities` | Corrected measurement distributions |
| `experiment_diagnostics` | Optimization and numerical diagnostics |
| `mitigation_policies` | Operational correction requirements |
| `experiment_policy_assignments` | Policy applied to an experiment |
| `audit_events` | Historical operational events |

### 10.2 Relational workflow

The database follows this relationship:

Laboratory  
→ Instrument  
→ Calibration Campaign  
→ Qubit Calibration  
→ Assignment Matrix  
→ Experiment  
→ Measurement Counts  
→ Corrected Probabilities  
→ Experiment Diagnostics  
→ Audit Events

### 10.3 Data integrity

Primary keys identify individual records.

Foreign keys preserve relationships between instruments, calibration campaigns, researchers, and experiments.

Check constraints prevent invalid probability values, negative counts, invalid qubit numbers, and inconsistent calibration sample totals.

Generated columns calculate conditional probabilities directly from calibration counts.

Indexes support common access patterns, including:

- Instrument-specific calibration retrieval.
- Active calibration searches.
- Experiment status monitoring.
- Measurement count retrieval.
- Time-based audit reporting.

### 10.4 Calibration activation

The activation trigger validates that:

1. The calibration qubit count matches the instrument.
2. Every required qubit has calibration data.
3. Each qubit has sufficient calibration samples.

The activation audit trigger records successful activation.

The eligibility function also evaluates calibration age and minimum sample requirements.

A stale or incomplete calibration cannot be treated as eligible.

### 10.5 Experiment submission

The `submit_experiment` procedure validates the instrument, researcher, and calibration before creating an experiment.

It then stores the observed measurement counts, assigns an operational policy, records an audit event, and advances the experiment to its validated state.

### 10.6 Numerical processing boundary

The database records the results of numerical correction.

It does not perform the matrix optimization.

The numerical engine supplies:

- Raw probabilities.
- Corrected probabilities.
- Residual norm.
- Iteration count.
- Convergence state.
- Processing duration.

The SQL transaction verifies normalization before marking the experiment as corrected.

This separation prevents relational data management from being confused with numerical computation.

## 11. Distinctions Between Important Concepts

| Concept | Meaning | Function |
|---|---|---|
| Readout calibration | Measurement characterization | Estimates assignment probabilities |
| Assignment matrix | Conditional measurement model | Represents measurement errors |
| Raw distribution | Direct measurement result | Preserves observed frequencies |
| Corrected distribution | Estimated ideal distribution | Reduces characterized measurement bias |
| Regularization | Numerical stabilization | Controls sensitivity to noisy estimates |
| Simplex projection | Probability constraint enforcement | Maintains nonnegative normalized output |
| Residual | Model reconstruction error | Measures agreement with observations |
| Calibration drift | Change in measurement behavior | Indicates possible calibration obsolescence |
| Bootstrap uncertainty | Resampling-based variability | Evaluates statistical sensitivity |

Calibration and correction are related but different operations.

Calibration estimates the measurement model.

Correction uses that model to estimate the distribution before measurement errors.

A correction algorithm cannot compensate reliably for errors that are absent from its calibration model.

## 12. Practical Example

Consider a two-qubit experiment with an ideal distribution:

\[
p=
\begin{bmatrix}
0.70\\
0.10\\
0.15\\
0.05
\end{bmatrix}
\]

The total probability is:

\[
\sum_i p_i=1
\]

The processor produces observed counts after measurement errors affect the computational basis outcomes.

The experimental workflow is:

1. Prepare known zero and one states.
2. Measure calibration states repeatedly.
3. Estimate individual qubit assignment matrices.
4. Construct the multi-qubit assignment matrix.
5. Execute the quantum experiment.
6. Collect measurement counts.
7. Convert counts into observed probabilities.
8. Apply constrained least-squares correction.
9. Verify probability normalization.
10. Record residuals and convergence information.
11. Associate the result with its calibration version.
12. Evaluate calibration freshness before subsequent experiments.

The corrected distribution should be compared with the known distribution in simulation experiments.

For physical experiments, the ideal distribution is generally unknown. Independent validation and uncertainty analysis are therefore necessary.

## 13. Failure Modes and Controls

| Failure condition | Potential consequence | Control |
|---|---|---|
| Insufficient calibration shots | Noisy assignment matrix | Minimum-shot policy |
| Singular assignment matrix | Non-identifiable correction | Conditioning diagnostics |
| Poorly conditioned matrix | Amplified statistical noise | Regularization |
| Incorrect qubit ordering | Incorrect state mapping | Explicit indexing validation |
| Correlated readout errors | Independent model bias | Joint calibration |
| Calibration drift | Incorrect correction model | Periodic recalibration |
| Invalid measurement counts | Incorrect probability estimation | Input validation |
| Non-convergence | Unreliable optimization result | Iteration limit and convergence flag |
| Negative unconstrained estimates | Invalid probability interpretation | Simplex projection |
| Missing experiment provenance | Poor reproducibility | Versioned audit records |

## 14. Statistical and Numerical Limitations

Readout error mitigation is an estimation procedure, not a guarantee of recovering the exact original quantum state.

Several limitations must be considered.

### Finite sampling

Calibration and experiment counts are finite.

Their statistical uncertainty propagates into the corrected distribution.

Increasing shot counts can reduce sampling noise but increases experimental cost.

### Calibration uncertainty

The assignment matrix itself is estimated from samples.

Treating its entries as exact can underestimate uncertainty in corrected probabilities.

A more complete uncertainty analysis should resample both calibration measurements and experimental measurements.

### Model mismatch

An independent-qubit assignment matrix may not represent correlated measurement behavior.

The correction can then produce a mathematically valid but physically biased distribution.

### Regularization bias

Regularization improves stability but can introduce bias.

The regularization parameter should be evaluated against simulation, calibration uncertainty, and experimental objectives.

### Conditioning

An assignment matrix with nearly indistinguishable columns cannot reliably distinguish certain prepared states.

Increasing the number of measurements does not fully resolve a fundamentally ill-conditioned measurement model.

### Exponential scaling

Full assignment matrices scale exponentially with the number of qubits.

The implementations are intended for small and moderate calibration demonstrations rather than unrestricted large-scale quantum processors.

## 15. Security and Reproducibility

Calibration records and experimental outcomes should be protected as scientific data.

Important controls include:

- Restricting calibration activation permissions.
- Recording calibration timestamps and versions.
- Preserving original measurement counts.
- Separating raw and corrected results.
- Maintaining immutable audit histories.
- Validating experiment ownership.
- Protecting stored calibration files.
- Recording numerical algorithm parameters.
- Retaining convergence and residual diagnostics.

Corrected results should never silently replace original measurements.

Both distributions are necessary for reproducibility and independent verification.

## 16. Execution and Validation

| Implementation | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Standard library |
| C++17 | C++17 compiler | Standard library |
| Java | Java 17 | Standard library |
| PostgreSQL | PostgreSQL 15+ | PostgreSQL server |

The numerical examples use deterministic random seeds.

The programs validate:

- Calibration probability ranges.
- Measurement bitstring dimensions.
- Nonnegative measurement counts.
- Positive shot totals.
- Assignment matrix dimensions.
- Optimization configuration.
- Corrected probability normalization.
- Calibration version consistency.

The SQL implementation includes executable DDL, sample records, triggers, functions, procedures, indexes, views, transactions, and reporting queries.

## 17. Technical Performance Characteristics

Let \(n\) be the number of qubits and \(d=2^n\) the number of computational basis states.

| Operation | Approximate complexity |
|---|---|
| Single-qubit calibration storage | \(O(n)\) |
| Dense assignment matrix storage | \(O(d^2)\) |
| Tensor-product construction | \(O(d^2)\) output size |
| Matrix-vector multiplication | \(O(d^2)\) |
| Dense Gram matrix construction | \(O(d^3)\) |
| One projected-gradient iteration | \(O(d^2)\), excluding simplex sorting |
| Simplex projection | \(O(d\log d)\) |
| Measurement count aggregation | \(O(S)\), for \(S\) recorded outcomes |

The main computational limitation is the exponential growth of the complete multi-qubit assignment matrix.

For larger devices, structured measurement models and scalable correction methods become necessary.

## 18. Experimental Interpretation

Readout error mitigation estimates the probability distribution that would have been observed under the calibrated measurement model without the characterized measurement errors.

It does not reverse every source of quantum hardware noise.

It does not correct state-preparation errors, gate errors, decoherence, leakage, or errors that are absent from the calibration model.

The distinction between measurement correction and general quantum error correction is fundamental.

Measurement mitigation operates on classical measurement statistics after quantum measurements have been collected.

Its validity depends on calibration quality, model assumptions, statistical uncertainty, numerical stability, and experimental reproducibility.
