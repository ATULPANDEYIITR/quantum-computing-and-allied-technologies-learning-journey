# Quantum Measurement in Code: Shots, Counts, and Probabilities

## Scope

Quantum measurement converts a prepared quantum state into classical outcomes. A measurement experiment repeats the same preparation and measurement procedure to estimate the distribution of possible outcomes. The number of repetitions is called the **shot count**.

This project examines three quantities that must remain distinct:

- **Theoretical probability:** the probability assigned to an outcome by the prepared quantum state and measurement basis.
- **Observed count:** the number of shots that produced a particular classical outcome.
- **Empirical probability:** the observed count divided by the total number of shots.

The implementations use computational-basis measurements, including balanced qubit states and a two-qubit Bell state. They demonstrate probability validation, finite-sample variation, outcome aggregation, statistical uncertainty, and persistent measurement records.

The programs simulate measurements from known probability distributions. They do not implement quantum gate operations, density-matrix evolution, quantum error correction, or a physical quantum device.

## Mathematical foundation

### The Born rule

A pure quantum state expressed in the computational basis can be written as

\[
|\psi\rangle = \sum_x \alpha_x |x\rangle
\]

Here, \(x\) identifies a basis outcome and \(\alpha_x\) is its complex probability amplitude.

The Born rule gives the probability of observing outcome \(x\):

\[
p(x)=|\alpha_x|^2
\]

For an amplitude \(\alpha_x=a+ib\),

\[
p(x)=a^2+b^2
\]

A valid normalized state satisfies

\[
\sum_x |\alpha_x|^2=1
\]

Probabilities describe the measurement distribution before the outcomes of a particular experiment are known. They are not counts, and they are not guarantees about the exact composition of a finite sample.

### Shots, counts, and empirical probabilities

For \(N\) shots, let \(n_x\) denote the number of times outcome \(x\) occurs. Then

\[
\sum_x n_x=N
\]

The empirical probability is

\[
\hat p(x)=\frac{n_x}{N}
\]

Repeated independent measurements of an identically prepared state produce samples from the same distribution under the idealized model. The empirical probabilities fluctuate because \(N\) is finite.

For a single outcome with theoretical probability \(p\), its count follows a binomial distribution:

\[
n_x\sim\operatorname{Binomial}(N,p)
\]

Its expected count and variance are

\[
\mathbb E[n_x]=Np
\]

\[
\operatorname{Var}(n_x)=Np(1-p)
\]

The approximate standard error of the observed frequency is

\[
\operatorname{SE}(\hat p)
=\sqrt{\frac{\hat p(1-\hat p)}{N}}
\]

The implementations use this plug-in estimate to describe sampling uncertainty. It is not an exact confidence interval and can be misleading for very small samples or rare outcomes.

### Why more shots help

For a fixed probability distribution, sampling error generally decreases proportionally to \(1/\sqrt{N}\). Increasing the shot count by a factor of four typically reduces standard errors by approximately half.

This relationship is statistical rather than deterministic. A particular run with more shots can still have a larger deviation than a run with fewer shots.

## Measurement examples

### Balanced qubit

A qubit prepared by applying a Hadamard gate to the computational basis state \(|0\rangle\) has the state

\[
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt{2}}
\]

Its computational-basis probabilities are

\[
p(0)=p(1)=\frac12
\]

An experiment with 1,000 shots is expected to produce approximately 500 observations of each outcome. It is not required to produce exactly 500 of each.

The Python, JavaScript, C++, and Java programs sample from this distribution and report theoretical probabilities, counts, observed frequencies, and estimated standard errors.

### Biased qubit

A distribution with \(p(0)=0.8\) and \(p(1)=0.2\) illustrates that unequal probabilities lead to unequal expected counts. In 500 shots, the expected counts are 400 and 100, respectively.

An observed result such as 397 zeros and 103 ones is consistent with sampling variation. Comparing observed frequencies with expected probabilities is more informative than demanding exact equality.

### Bell-state correlations

Consider the Bell state

\[
|\Phi^+\rangle=\frac{|00\rangle+|11\rangle}{\sqrt{2}}
\]

Computational-basis measurement gives

\[
p(00)=\frac12,\quad p(11)=\frac12
\]

\[
p(01)=p(10)=0
\]

The allowed outcomes are correlated. Under the ideal state and measurement model, the outcomes `01` and `10` never occur. This is stronger than observing two independent balanced qubits, for which all four two-bit outcomes would have probability \(1/4\).

The examples test that impossible outcomes have zero counts. This check concerns the assumed ideal distribution; real hardware may produce unexpected outcomes because of noise, readout errors, state-preparation errors, or differences between the actual and modeled circuit.

## Python implementation

The Python script emphasizes mathematical validation and statistical interpretation.

`probability_from_amplitudes()` applies the Born rule to real or complex amplitudes and checks that their squared magnitudes sum to one. `validate_probabilities()` verifies that the supplied distribution is finite, non-negative, normalized, and consistently labeled.

`QuantumMeasurementSimulator` performs independent weighted sampling with a seeded pseudorandom generator. The seed makes the example reproducible within the same runtime and compatible random-number implementation. It does not provide cryptographic randomness or guarantee identical results across every language or library version.

`MeasurementResult` keeps the theoretical distribution and observed counts together. It computes empirical probabilities, estimated standard errors, and total variation distance:

\[
D_{\mathrm{TV}}(p,\hat p)
=\frac12\sum_x |p(x)-\hat p(x)|
\]

Total variation distance is zero when the distributions match exactly. It is one when the distributions have disjoint support. In finite experiments, a nonzero value is normal.

The validation checks exercise invalid distributions and invalid shot counts. The shot-budget comparison demonstrates how the observed distance changes across experiments with different sample sizes. Since each experiment has its own sampling variation, the distances need not decrease monotonically.

## JavaScript implementation

The JavaScript program focuses on outcome sampling, immutable results, and batch aggregation.

`MeasurementExperiment` constructs a cumulative probability distribution. Each pseudorandom draw is mapped to the first outcome whose cumulative probability exceeds that draw. This provides weighted sampling without requiring an external quantum library.

`probabilitiesFromAmplitudes()` accepts real amplitudes or objects containing real and imaginary components. It calculates squared magnitudes and rejects non-normalized amplitude vectors.

The result object records a run identifier, shot count, counts, theoretical probabilities, empirical probabilities, standard errors, and total variation distance. Freezing the result objects prevents accidental mutation of the reported data through ordinary object-property assignment.

`collectIndependentBatches()` illustrates aggregation across multiple measurement batches. Each batch produces its own counts, and the final empirical frequencies are calculated from the combined counts divided by the total shots. Frequencies should not be averaged without weighting when batch sizes differ.

The local asynchronous example is not a quantum-service client. Its random sampling is synchronous, and scheduling promises does not create independent hardware jobs or independent random-number streams. A real integration would need explicit job submission, result retrieval, timeout handling, and provider-specific execution metadata.

## C++ case study: detector calibration

The C++ implementation models a measurement analysis service used to evaluate a detector's output distribution.

`MeasurementEngine` validates the supplied distribution and samples outcomes through `std::discrete_distribution`. The generator is seeded with `std::mt19937`, making the run repeatable within a compatible implementation. Standard-library distribution algorithms are not required to produce identical sequences across different implementations.

`MeasurementRun` stores the shot count, expected probabilities, and observed counts. It verifies that the total number of observations equals the declared shot count. The report includes empirical probabilities, estimated standard errors, and total variation distance.

The balanced-qubit experiment represents a simple detector calibration. The Bell-state experiment checks a correlated distribution and rejects impossible outcomes in the ideal simulation.

The calibration report separates measurement from the decision rule. A quality-control threshold is a policy, not a physical law: its value should be justified by the expected sampling uncertainty, calibration procedure, and acceptable risk of false alarms.

The program uses a map to associate each bitstring with its probability or count. For \(K\) possible outcomes and \(N\) shots, sampling requires \(N\) draws and the count table requires \(O(K)\) entries. This is suitable for compact experiments, but storing a complete distribution for an \(n\)-qubit register can require \(O(2^n)\) entries. Sparse distributions or streaming aggregation may be preferable when only a small subset of outcomes is relevant.

## Java implementation: experiment governance

The Java program separates the prepared state, execution request, measurement result, measurement service, and quality policy.

`PreparedState` validates the outcome labels, register widths, probability bounds, and normalization before a measurement can run. Its probability map is immutable, preventing a caller from changing the distribution after validation.

`MeasurementRequest` captures the experiment name, positive shot count, and random seed. It rejects invalid requests before sampling begins.

`MeasurementResult` stores a unique run identifier and immutable count and probability maps. It verifies that counts are non-negative and sum to the requested number of shots. The standard-error and total-variation calculations are methods on the result because both depend on the recorded observation.

`QualityPolicy` expresses an explicit acceptance threshold. The policy evaluates the measured distribution against the theoretical one without changing the underlying measurements. This separation supports auditability: the same run can be evaluated under different policies without resampling the experiment.

The example uses Java 17 records for the small immutable policy object. The domain classes use explicit validation and controlled construction because invalid experimental records should not be allowed to enter the analysis workflow silently.

## SQL data model and integrity

The PostgreSQL script persists experiments, prepared states, possible outcomes, measurement runs, and observed counts.

| Relation | Purpose |
|---|---|
| `quantum_experiments` | Identifies experiments and describes their purpose. |
| `prepared_states` | Associates a named state with an experiment and register width. |
| `quantum_outcomes` | Stores each possible bitstring and its theoretical probability. |
| `measurement_runs` | Records the requested shot count, execution status, and timestamps. |
| `measurement_counts` | Stores the observed count for each outcome in a run. |

Foreign keys establish relationships between experiments, states, outcomes, and runs. Unique constraints prevent duplicate experiment names, duplicate state names within an experiment, duplicate outcome labels within a state, and duplicate run labels within a state.

Row-level checks enforce non-negative probabilities, valid bitstrings, positive shot counts, and valid run statuses. A trigger verifies that a count references an outcome belonging to the run's prepared state.

Probability normalization and count totals are cross-row conditions. A normal `CHECK` constraint cannot reliably enforce these conditions across a changing set of rows. The script uses a deferred constraint trigger to validate the outcome probabilities at transaction commit, allowing a distribution to be inserted as a complete transaction.

The completion trigger requires every possible outcome to have a count row and requires the sum of counts to equal the declared shot count before a run transitions to `completed`. Pending and failed runs remain distinguishable from successful runs.

The reporting view calculates empirical probabilities and plug-in standard errors for completed runs. The aggregate query computes total variation distance, while the Bell-state query searches for observations assigned zero theoretical probability.

The example counts are simulated records, not observations from quantum hardware. In a production system, additional metadata would be needed to identify the circuit, measurement basis, device, calibration version, execution job, and provenance of the probability distribution.

## Distinguishing probabilities from observed frequencies

Theoretical and empirical distributions serve different purposes.

| Property | Theoretical probability | Empirical probability |
|---|---|---|
| Origin | Prepared state and measurement model | Recorded outcomes |
| Value | Specified before sampling in the model | Calculated after sampling |
| Depends on shot count | Not directly | Yes |
| Subject to finite-sample variation | No, within the assumed model | Yes |
| Primary role | Predicts the distribution | Estimates the distribution |

A zero empirical count does not establish that an outcome has zero physical probability. Rare events may not occur in a finite sample. Likewise, an outcome that appears only once can have a small empirical frequency without being physically impossible.

For a categorical distribution, the counts across outcomes are jointly multinomial. Individual outcome counts are not independent because their sum is fixed at the shot count. The per-outcome standard errors in these implementations are useful marginal estimates, not a complete description of all correlations between frequency estimates.

## Edge cases and limitations

- **Zero shots:** No empirical probability can be estimated from an empty experiment. The implementations reject non-positive shot counts.
- **Invalid normalization:** A distribution whose probabilities do not sum to one must be rejected or explicitly normalized under a documented tolerance. Silent normalization can hide errors in amplitude construction or data ingestion.
- **Zero-probability outcomes:** These should remain visible in the theoretical distribution even when their observed counts are zero. Keeping them in reports helps distinguish a valid impossible outcome from a missing measurement category.
- **Small sample sizes:** Normal approximations to sampling uncertainty can be poor when expected counts are small or probabilities are near zero or one. Exact binomial methods or suitable multinomial intervals may be necessary.
- **Finite precision:** Floating-point calculations can introduce tiny normalization discrepancies. Validation tolerances should be small enough to catch real mistakes without rejecting harmless rounding differences.
- **Reproducibility:** A seed helps reproduce a software simulation, but a seed alone does not establish scientific provenance. The distribution, software version, sampling algorithm, and execution metadata also matter.
- **Ideal-state assumptions:** The simulation samples the distribution provided to it. It does not discover whether that distribution accurately represents a real device. Hardware noise and measurement error must be modeled or estimated separately.

## Performance and production considerations

A complete probability table for \(n\) qubits can have up to \(2^n\) outcomes. The exponential size of the full computational basis can make exhaustive distribution storage impractical for large registers.

For a limited set of measured observables, streaming counts can reduce memory requirements. For large experiments, data systems should preserve raw provider results or sufficient immutable execution records so that downstream analyses can be reproduced.

Statistical quality thresholds should account for the number of shots and the number of outcomes being tested. Testing many outcomes independently can increase the probability of false alarms. Calibration decisions should therefore use a documented statistical procedure rather than interpreting every deviation as evidence of a faulty device.

The central analytical distinction remains essential: probabilities describe the modeled measurement distribution, shots define the amount of sampling, and counts record the outcomes actually observed.
