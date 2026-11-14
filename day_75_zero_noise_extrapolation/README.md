# Zero-Noise Extrapolation: Practical Quantum Error Mitigation

## Project Description

Zero-Noise Extrapolation (ZNE) is a quantum error mitigation technique that estimates the expectation value of an observable at zero noise by measuring the same computational task under several amplified noise conditions.

Quantum processors are affected by imperfect gates, decoherence, readout errors, calibration drift and environmental disturbances. These effects change measured expectation values and reduce the reliability of quantum computations.

ZNE attempts to estimate the result that would have been obtained in the absence of noise without requiring a fully fault-tolerant quantum computer.

This project implements an end-to-end educational ZNE workflow across Python, JavaScript, C++17, Java 17 and PostgreSQL.

The implementations use a simulated noise model. They demonstrate the numerical and engineering mechanisms of ZNE rather than claiming experimental results from physical quantum hardware.

## Learning Objectives

The project develops practical understanding of:

- Quantum noise and expectation values.
- Noise amplification and noise scaling.
- Gate folding as a noise-scaling technique.
- Measurement sampling and statistical uncertainty.
- Zero-noise extrapolation.
- Linear and polynomial regression.
- Richardson extrapolation.
- Shot allocation and experiment management.
- Error comparison and mitigation evaluation.
- Persistent experiment records and database integrity.

## 1. Quantum Noise and Observable Measurements

### Quantum expectation values

A quantum observable is represented by a Hermitian operator \(O\). Its expectation value for quantum state \(\rho\) is:

\[
\langle O\rangle = \operatorname{Tr}(\rho O)
\]

For a Pauli-Z measurement, individual measurement outcomes are either \(+1\) or \(-1\).

The expectation value is estimated from repeated measurements:

\[
\hat{O} = \frac{N_+ - N_-}{N}
\]

Where:

- \(N_+\) represents positive measurement outcomes.
- \(N_-\) represents negative measurement outcomes.
- \(N\) represents the total number of shots.

The estimate lies between \(-1\) and \(+1\).

### Noise effects

A simplified noise-dependent expectation model is:

\[
E(\lambda)=E_0+a\lambda+b\lambda^2
\]

Where:

| Symbol | Meaning |
|---|---|
| \(E_0\) | Ideal zero-noise expectation |
| \(\lambda\) | Noise-scaling factor |
| \(a\) | First-order noise coefficient |
| \(b\) | Second-order noise coefficient |

The observed expectation generally differs from the ideal expectation.

The simulated project uses:

\[
E(\lambda)=0.85-0.12\lambda-0.025\lambda^2
\]

The ideal reference is therefore:

\[
E(0)=0.85
\]

This mathematical model provides a controlled environment for evaluating extrapolation accuracy.

It is not a universal model of quantum hardware noise. Real devices can exhibit non-Markovian effects, coherent errors, leakage, correlated noise and time-dependent calibration changes.

## 2. Noise Scaling

### Purpose

ZNE requires measurements at different noise strengths.

The underlying quantum computation should remain equivalent while the effective noise is amplified.

A scaling factor of:

\[
\lambda=1
\]

represents the baseline noise condition.

Higher factors represent amplified noise conditions.

For example:

| Noise factor | Experimental condition |
|---:|---|
| 1.0 | Baseline noise |
| 1.5 | Moderately amplified noise |
| 2.0 | Doubled effective noise |
| 2.5 | Further amplified noise |

These factors describe the intended scaling and do not necessarily represent directly measured physical error probabilities.

### Gate folding

One practical approach is unitary folding.

For a unitary gate \(U\):

\[
U=UU^\dagger U
\]

Because:

\[
U^\dagger U=I
\]

The additional operations preserve the ideal computation.

The expanded gate sequence introduces additional opportunities for hardware errors.

Local folding expands selected gates. Global folding expands the circuit more broadly.

The actual relationship between folding factor and effective noise depends on the processor, native gates, compilation and calibration.

### Other scaling approaches

The implementations distinguish the conceptual scaling mechanisms:

- Gate folding: Adds operations that preserve the ideal unitary.
- Noise parameter control: Adjusts controllable noise parameters where supported.
- Calibration-based scaling: Uses calibrated device conditions to establish different effective noise levels.

The PostgreSQL schema stores the selected scaling mechanism for each noise scale.

## 3. Measurement and Statistical Uncertainty

Each noise scale requires an observable estimate.

A finite number of shots introduces statistical uncertainty.

For independent Pauli-Z outcomes:

\[
SE(\hat{O}) =
\sqrt{\frac{1-\hat{O}^{2}}{N}}
\]

Where \(SE\) is the estimated standard error.

Increasing the shot count generally decreases statistical uncertainty.

The implementations enforce a minimum of two shots and validate measurement inputs.

The Python, JavaScript, C++17 and Java 17 implementations generate Bernoulli-distributed measurement outcomes.

The generated measurement records contain:

- Noise scale.
- Estimated observable.
- Shot count.
- Standard error.

The SQL implementation stores the measurement results and validates their ranges.

A crucial distinction is that the uncertainty of an extrapolated estimate is not necessarily equal to the standard error of any individual measurement. Extrapolation combines multiple measurements, and the uncertainty depends on their variances, covariance and extrapolation weights.

## 4. Zero-Noise Extrapolation

### Core mechanism

The ZNE workflow is:

1. Prepare the same logical quantum computation.
2. Execute it under baseline noise.
3. Amplify effective noise.
4. Repeat the computation at multiple noise scales.
5. Estimate the observable at each scale.
6. Fit an extrapolation model.
7. Evaluate the fitted model at zero noise.
8. Compare the estimate against the baseline measurement.

The mathematical objective is:

\[
E_{\mathrm{ZNE}} \approx E(0)
\]

Zero noise is an extrapolation target. It is not a condition that must physically exist on the quantum processor.

### Linear extrapolation

The linear model is:

\[
E(\lambda)=c_0+c_1\lambda
\]

The zero-noise estimate is:

\[
E(0)=c_0
\]

Two distinct noise scales are sufficient to determine a line.

Linear extrapolation is computationally inexpensive and can be useful when the noise response is approximately linear over the selected range.

It can introduce bias when significant nonlinear noise effects are present.

### Quadratic extrapolation

The quadratic model is:

\[
E(\lambda)=c_0+c_1\lambda+c_2\lambda^2
\]

The zero-noise estimate is:

\[
E(0)=c_0
\]

Three distinct noise scales are the minimum required for a quadratic fit.

The project uses four scales for the quadratic experiment, allowing a least-squares fit rather than exact interpolation through only three observations.

The fitted coefficients represent the estimated relationship between noise amplification and the measured observable.

Higher polynomial degrees are not automatically better. They can produce unstable extrapolations and amplify measurement uncertainty.

### Least-squares regression

The polynomial model is:

\[
y_i=\sum_{j=0}^{d}c_jx_i^j+\epsilon_i
\]

The coefficient vector is obtained by minimizing:

\[
\sum_{i=1}^{n}
\left(
y_i-\sum_{j=0}^{d}c_jx_i^j
\right)^2
\]

The normal equations are:

\[
(X^TX)c=X^Ty
\]

The implementations solve this small system using Gaussian elimination with partial pivoting.

This avoids requiring a third-party numerical library.

For production numerical work, QR decomposition or singular value decomposition is generally preferable to normal equations, particularly when polynomial degree or scale ranges increase.

## 5. Richardson Extrapolation

Richardson extrapolation is a specific extrapolation method that cancels leading-order error terms.

For two distinct noise scales:

\[
E(\lambda)=E_0+a\lambda
\]

The zero-noise estimate is:

\[
E(0)=
\frac{
\lambda_2E(\lambda_1)
-
\lambda_1E(\lambda_2)
}{
\lambda_2-\lambda_1
}
\]

For scales 1 and 2:

\[
E(0)=2E(1)-E(2)
\]

This cancels the first-order noise contribution under the assumed linear error model.

When the actual response contains higher-order terms, those terms remain.

Richardson extrapolation is therefore not interchangeable with an arbitrary quadratic least-squares fit.

The implementations explicitly separate Richardson extrapolation from linear and quadratic regression.

## 6. Mitigation Evaluation

A mitigation method should be evaluated against an appropriate reference.

The project calculates:

\[
\text{Baseline Error}
=
|E_{\mathrm{baseline}}-E_{\mathrm{ideal}}|
\]

\[
\text{Mitigation Error}
=
|E_{\mathrm{ZNE}}-E_{\mathrm{ideal}}|
\]

Percentage error reduction is:

\[
R =
\left(
1-
\frac{\text{Mitigation Error}}
{\text{Baseline Error}}
\right)\times100
\]

A positive value indicates lower absolute error.

A negative value indicates that mitigation increased absolute error.

An error reduction of zero means there was no change.

This evaluation is possible in the simulation because the ideal reference is known.

For actual quantum hardware experiments, the ideal value may be unavailable. Evaluation then requires an independent reference, trusted classical calculation where feasible, benchmark instance or another defensible comparison method.

A ZNE estimate can be worse than the unmitigated result. Error mitigation is not guaranteed to improve every experiment.

## 7. Python Implementation

The Python implementation focuses on numerical modeling, validation and experiment reporting.

### Main components

| Component | Responsibility |
|---|---|
| `NoiseScale` | Validates noise amplification factors |
| `Measurement` | Stores observable and uncertainty |
| `QuantumNoiseSimulator` | Generates simulated noisy measurements |
| `polynomial_regression()` | Fits polynomial coefficients |
| `solve_linear_system()` | Solves the regression system |
| `ZeroNoiseExtrapolator` | Applies the selected extrapolation method |
| `ZNEExperiment` | Coordinates the experiment |
| `ZNEResult` | Stores the evaluation report |

### Important implementation decisions

The simulator uses the standard-library `random` module.

The measurement process samples positive and negative outcomes using a Bernoulli distribution.

The regression function supports linear and quadratic models.

The extrapolator separately implements first-order Richardson extrapolation.

The experiment returns both baseline and mitigated errors.

Results are written to JSON using a temporary file followed by replacement to reduce the risk of partially written reports.

Input validation rejects:

- Non-finite values.
- Noise factors below one.
- Duplicate scales.
- Insufficient observations.
- Invalid shot counts.
- Singular regression systems.

### Execution

Run:

`python zero_noise_extrapolation.py`

Run with a custom shot count:

`python zero_noise_extrapolation.py --shots 50000`

Specify a random seed:

`python zero_noise_extrapolation.py --seed 123`

Specify the report location:

`python zero_noise_extrapolation.py --output experiment.json`

No external Python packages are required.

## 8. JavaScript Implementation

The JavaScript implementation emphasizes asynchronous experiment orchestration, event-driven execution and resource management.

### Main components

| Component | Responsibility |
|---|---|
| `NoiseModel` | Models observable degradation |
| `RandomSource` | Provides reproducible sampling |
| `ShotBudget` | Enforces measurement limits |
| `ZNEEngine` | Coordinates asynchronous execution |
| `polynomialFit()` | Computes polynomial coefficients |
| `interpolateAtZero()` | Evaluates the extrapolation |
| `saveReport()` | Persists experiment results |

### Event-driven workflow

The `ZNEEngine` extends Node.js `EventEmitter`.

It exposes three important events:

- `experimentStarted`
- `measurementCompleted`
- `experimentCompleted`

It also emits `experimentFailed` when an execution fails.

This separates measurement acquisition from reporting and monitoring.

The asynchronous `execute()` method returns a Promise.

The implementation performs measurements sequentially because the deterministic random generator and shot budget are shared mutable resources.

The running-state guard prevents overlapping execution within the same engine instance.

### Resource management

The shot budget rejects requests that exceed the configured maximum.

Report persistence uses a temporary file and rename operation.

The report includes a unique experiment identifier and timestamp.

The JavaScript implementation uses only Node.js built-in modules.

### Execution

Run:

`node zero_noise_extrapolation.js`

The implementation generates `zne_results.json` in the current working directory.

## 9. C++17 Implementation

The C++17 implementation emphasizes explicit domain modeling, deterministic execution, numerical computation and controlled experiment state.

### Main components

| Component | Responsibility |
|---|---|
| `NoiseConfiguration` | Defines the noise model |
| `Measurement` | Represents a sampled observable |
| `NoiseModel` | Generates measurement outcomes |
| `ShotBudget` | Tracks measurement resource consumption |
| `PolynomialExtrapolator` | Performs regression and Richardson extrapolation |
| `ZNEEngine` | Coordinates the experiment |
| `ExperimentReport` | Stores final experiment metrics |

### State management

The experiment uses explicit states:

- `Created`
- `Running`
- `Completed`
- `Failed`

A completed experiment cannot be executed again through the same engine instance.

An exception during execution changes the state to `Failed`.

### Numerical implementation

The polynomial regression system uses partial-pivoting Gaussian elimination.

STL containers store measurements and coefficients.

The `std::bernoulli_distribution` class generates measurement outcomes.

`std::mt19937` provides reproducible random sequences when the seed is fixed.

### Performance characteristics

For \(n\) measurement scales and polynomial degree \(d\):

- Measurement simulation requires \(O(N)\) sampling operations per scale, where \(N\) is the shot count.
- Polynomial system construction requires approximately \(O(nd^2)\) operations.
- Gaussian elimination requires \(O(d^3)\) operations.

For the small polynomial degrees used in practical introductory ZNE experiments, measurement acquisition normally dominates computational cost.

### Execution

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic zero_noise_extrapolation.cpp -o zne`

Run:

`./zne`

## 10. Java 17 Implementation

The Java implementation models ZNE as an enterprise-oriented service with explicit domain types, measurement interfaces and interchangeable extrapolation policies.

### Domain records

Java records provide immutable representations for:

- `NoiseConfiguration`
- `Measurement`
- `ExperimentConfiguration`
- `RegressionResult`
- `ExperimentResult`

These types prevent unnecessary mutation of experiment configuration and result data.

Lists are copied when records are constructed.

### Service architecture

| Component | Responsibility |
|---|---|
| `MeasurementProvider` | Defines the measurement acquisition contract |
| `SimulatedMeasurementProvider` | Implements simulated acquisition |
| `ExtrapolationPolicy` | Defines extrapolation behavior |
| `LinearPolicy` | Applies linear regression |
| `QuadraticPolicy` | Applies quadratic regression |
| `RichardsonPolicy` | Applies first-order Richardson extrapolation |
| `PolicyFactory` | Selects an extrapolation strategy |
| `ExperimentService` | Coordinates experiment execution |
| `ShotBudget` | Controls resource consumption |

### Policy separation

The `ExtrapolationPolicy` interface separates the mathematical method from experiment orchestration.

A new implementation can supply a different extrapolation method without changing the measurement service.

The factory maps an explicit method enumeration to its corresponding policy.

### Enterprise validation

The configuration record checks:

- Scale validity.
- Scale uniqueness.
- Shot-count constraints.
- Maximum resource allocation.
- Method-specific minimum measurement requirements.

The experiment service rejects invalid reference values and wraps execution failures with experiment execution context.

The measurement provider synchronizes access to its shared random generator.

### Execution

Compile:

`javac --release 17 ZeroNoiseExtrapolation.java`

Run:

`java ZeroNoiseExtrapolation`

No third-party dependencies are required.

## 11. PostgreSQL Data Architecture

The PostgreSQL implementation provides a persistent relational model for ZNE experiments.

### Entity relationships

    CIRCUITS
       |
       | 1:N
       v
    EXPERIMENTS
       |
       | 1:N
       v
    NOISE_SCALES
       |
       | 1:1
       v
    MEASUREMENTS

    EXPERIMENTS
       |
       +------> EXTRAPOLATION_RESULTS
       |
       +------> EXPERIMENT_AUDIT

### Table responsibilities

| Table | Purpose |
|---|---|
| `circuits` | Stores quantum circuit metadata |
| `experiments` | Stores experiment configuration and lifecycle |
| `noise_scales` | Stores configured amplification factors |
| `measurements` | Stores observable measurements |
| `extrapolation_results` | Stores calculated estimates and errors |
| `experiment_audit` | Records experiment status transitions |

### Integrity mechanisms

Primary keys identify each record.

Foreign keys enforce relationships between circuits, experiments, noise scales and measurements.

Unique constraints prevent duplicate scale factors and duplicate measurements for the same experiment and scale.

Check constraints enforce valid observable ranges, scale factors and shot counts.

The measurement trigger locks the parent experiment while checking the aggregate shot budget. This protects the budget against concurrent measurement inserts when all writes use the defined trigger.

The status trigger records lifecycle changes in the audit table.

### Workflow procedure

The `transition_experiment()` procedure manages experiment state transitions.

Supported transitions include:

- `CREATED` to `RUNNING`.
- `RUNNING` to `COMPLETED`.
- `RUNNING` to `FAILED`.
- `CREATED` or `RUNNING` to `CANCELLED`.

Terminal states cannot be reopened through this procedure.

Completion requires the experiment to satisfy its method-specific measurement eligibility conditions.

### Analytical queries

The SQL script includes queries for:

- Experiment retrieval.
- Noise-scale measurement retrieval.
- Measurement validation.
- Shot consumption.
- Mitigation error comparison.
- Experiment eligibility.
- Ranking extrapolation methods.
- Audit history.
- Incomplete configurations.
- Performance reporting.

### Numerical computation boundary

PostgreSQL stores and validates numerical experiment results.

The actual polynomial fitting is performed by the application implementations.

The database does not claim to calculate an extrapolation merely because measurement rows exist.

This separation allows numerical processing and persistence to evolve independently.

### Execution

Run the SQL file using:

`psql -U postgres -d quantum_db -f zero_noise_extrapolation.sql`

The database must already exist, and the executing database role must have permission to create the schema, types, tables, functions, triggers and procedures.

## 12. Practical Experimental Workflow

A hardware-oriented ZNE experiment requires more than evaluating a polynomial.

The following workflow identifies the important operational stages.

    Circuit preparation
           |
           v
    Select observable
           |
           v
    Establish baseline execution
           |
           v
    Select noise-scaling technique
           |
           v
    Generate folded or scaled circuits
           |
           v
    Execute at multiple noise scales
           |
           v
    Collect measurement outcomes
           |
           v
    Calculate observable estimates
           |
           v
    Evaluate statistical uncertainty
           |
           v
    Select extrapolation model
           |
           v
    Estimate zero-noise intercept
           |
           v
    Compare with baseline
           |
           v
    Record experiment and results

### Important experimental controls

A practical implementation should control:

- Circuit equivalence across noise scales.
- Measurement basis consistency.
- Shot allocation.
- Device calibration changes.
- Compilation and transpilation differences.
- Measurement grouping.
- Noise amplification accuracy.
- Statistical uncertainty.
- Extrapolation model selection.
- Reproducibility and audit records.

The circuit should preserve its intended ideal operation when noise is amplified.

Changing the circuit in a way that changes its ideal observable invalidates the extrapolation assumption.

## 13. Edge Cases and Failure Modes

| Condition | Potential consequence | Implemented control |
|---|---|---|
| Duplicate noise scales | Singular regression system | Unique-scale validation |
| Fewer than required measurements | Underdetermined model | Minimum observation checks |
| Noise scale below one | Invalid scaling configuration | Input validation |
| Excessive shot allocation | Resource exhaustion | Shot-budget enforcement |
| Singular regression matrix | Unreliable coefficients | Pivot checks |
| Non-finite measurement | Invalid extrapolation | Finite-value validation |
| Concurrent engine execution | Shared-state inconsistency | Execution-state guard |
| Incomplete database measurements | Invalid experiment completion | Eligibility procedure |
| Measurement budget exceeded | Resource-policy violation | Database trigger |
| Excessive polynomial degree | Numerical instability | Degree restriction |

## 14. Limitations of the Implementations

The implementations deliberately use a simplified noise model.

They do not implement:

- A full quantum state-vector simulator.
- Density-matrix evolution.
- Real quantum hardware communication.
- Physical gate-level folding.
- Device-specific calibration acquisition.
- Readout mitigation.
- Correlated noise estimation.
- Non-Markovian noise modeling.
- Bayesian extrapolation.
- Cross-validation of extrapolation models.
- Full covariance-aware uncertainty propagation.
- Automatic optimal shot allocation.

The polynomial model assumes a reasonably smooth relationship between effective noise and the observable.

Real quantum devices may violate this assumption.

High noise scales can move measurements outside the useful regime of the extrapolation model.

Polynomial extrapolation can amplify statistical noise, particularly when the fitted model is poorly conditioned.

The quadratic model in this project is an educational example, not a universal prescription for selecting an extrapolation degree.

## 15. Performance, Security and Reliability

### Performance

Measurement acquisition usually dominates the computational cost.

Polynomial fitting is inexpensive for the small number of noise scales used in ordinary ZNE experiments.

Production implementations should consider:

- Parallel acquisition when hardware and measurement interfaces permit it.
- Per-scale shot allocation.
- Numerical conditioning.
- Confidence intervals.
- Repeated independent experiment runs.
- Hardware calibration windows.
- Measurement-data retention.

### Security

Quantum experiment records can contain sensitive research data and hardware configuration information.

Production systems should use:

- Restricted database roles.
- Encrypted database connections.
- Parameterized SQL statements.
- Controlled experiment ownership.
- Audit-log access restrictions.
- Input validation.
- Safe handling of measurement files.
- Explicit authorization for experiment execution.

Random seeds should be retained for reproducibility, but they do not establish scientific validity.

### Reliability

A production ZNE pipeline should distinguish between:

- Measurement failure.
- Hardware execution failure.
- Noise-scaling failure.
- Numerical fitting failure.
- Statistical quality failure.
- Persistence failure.

These conditions should be independently recorded rather than collapsed into a single generic experiment error.

## 16. Implementation Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Primary focus | Numerical modeling | Event-driven orchestration | Governance and computation | Enterprise service design | Persistent data integrity |
| Noise model | Yes | Yes | Yes | Yes | Stored experiment metadata |
| Measurement sampling | Yes | Yes | Yes | Yes | Stored observations |
| Linear extrapolation | Yes | Yes | Yes | Yes | Result persistence |
| Quadratic extrapolation | Yes | Yes | Yes | Yes | Result persistence |
| Richardson | Yes | Yes | Yes | Yes | Result persistence |
| Shot management | Yes | Yes | Yes | Yes | Trigger enforcement |
| Lifecycle management | Experiment object | Event-driven engine | Explicit state enum | Service result states | Procedures and triggers |
| Report generation | JSON | JSON | Console | Console | Analytical queries |

## 17. Validation Scenarios

The implementations include numerical tests for polynomial recovery and Richardson extrapolation.

The principal expected mathematical relationships are:

| Test | Input | Expected result |
|---|---|---|
| Linear regression | Distinct scales | Finite intercept |
| Quadratic regression | Three or more distinct scales | Recovered polynomial intercept |
| Richardson extrapolation | Two distinct scales | First-order zero-noise estimate |
| Invalid scale | Factor below 1 | Validation failure |
| Insufficient data | Too few observations | Experiment failure |
| Shot-budget violation | Requested shots exceed limit | Resource failure |
| Duplicate scales | Repeated factor | Validation failure |

For the controlled polynomial:

\[
E(\lambda)=1-0.15\lambda
\]

Measurements at \(\lambda=1\) and \(\lambda=2\) produce:

\[
E(1)=0.85
\]

\[
E(2)=0.70
\]

Richardson extrapolation gives:

\[
E(0)=2(0.85)-0.70=1
\]

This provides an exact analytical validation case independent of sampling noise.

## 18. Scientific Interpretation

ZNE is an error mitigation strategy, not quantum error correction.

Quantum error correction uses encoded logical information and error-detection and recovery mechanisms to suppress errors.

ZNE instead estimates an ideal observable using controlled changes to the effective noise level and classical extrapolation.

Its practical value depends on the quality of the noise-scaling procedure, the stability of the observable response, the number of measurements and the uncertainty introduced by extrapolation.

A technically valid ZNE experiment must report the noise-scaling procedure, selected measurement scales, shot counts, fitting model, estimated uncertainty and limitations of the resulting estimate.

The most important experimental question is not simply whether the extrapolated result is closer to an expected value, but whether the estimate is statistically defensible under the actual noise conditions and scaling assumptions.
