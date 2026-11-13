# Quantum Error Mitigation: Reducing Errors Without Full Quantum Error Correction

## Technical Overview

Quantum Error Mitigation (QEM) is a collection of techniques designed to reduce the effect of noise on quantum-computing results without implementing the complete encoding, syndrome measurement, and recovery procedures associated with full quantum error correction.

Quantum devices are affected by imperfect gates, environmental interactions, measurement errors, calibration drift, and limited coherence times. These effects cause measured observables to deviate from their ideal values.

QEM estimates more reliable expectation values by using additional measurements, calibrated noise information, statistical corrections, or controlled changes to experimental noise.

The central distinction is:

- **Quantum Error Correction (QEC):** Encodes logical quantum information into multiple physical qubits and uses error-detection and recovery mechanisms.
- **Quantum Error Mitigation (QEM):** Uses experimental and statistical techniques to improve estimates obtained from noisy quantum computations.

QEM does not generally restore an arbitrary corrupted quantum state. Its objective is to improve the accuracy of selected computational outputs.

## Mathematical Foundation

### Quantum states and expectation values

A single-qubit pure state is represented as:

\[
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle
\]

where:

\[
|\alpha|^2+|\beta|^2=1
\]

The computational-basis expectation value of the Pauli-Z observable is:

\[
\langle Z\rangle=|\alpha|^2-|\beta|^2
\]

The ideal value is compared against measurements collected from a noisy quantum circuit.

For a measurement producing outcomes \(+1\) and \(-1\), the empirical expectation is:

\[
\hat{E}=\frac{N_+-N_-}{N}
\]

where:

- \(N_+\) is the number of positive outcomes.
- \(N_-\) is the number of negative outcomes.
- \(N\) is the total number of shots.

For independent measurements, the approximate standard error is:

\[
SE(\hat{E})=
\sqrt{\frac{1-\hat{E}^{2}}{N}}
\]

Increasing the shot count generally decreases statistical uncertainty, but it does not automatically remove systematic noise.

### Density matrices and noise channels

A general quantum state can be represented by a density matrix:

\[
\rho=\sum_i p_i|\psi_i\rangle\langle\psi_i|
\]

A noisy quantum operation is represented using a completely positive trace-preserving map:

\[
\rho'=\mathcal{E}(\rho)
\]

The observable becomes:

\[
E_{\text{noisy}}=
\operatorname{Tr}(O\mathcal{E}(\rho))
\]

QEM attempts to estimate the corresponding ideal expectation:

\[
E_{\text{ideal}}=
\operatorname{Tr}(O\rho)
\]

without necessarily reconstructing the complete ideal state.

## Noise Models

The implementations distinguish three principal noise channels.

| Noise model | Mechanism | Effect |
|---|---|---|
| Bit-flip | Applies Pauli-X errors probabilistically | Exchanges computational-basis states |
| Phase-flip | Applies Pauli-Z errors probabilistically | Changes relative phase |
| Depolarizing | Introduces Pauli errors that reduce state polarization | Contracts the Bloch vector |

For a bit-flip channel with probability \(p\):

\[
\mathcal{E}(\rho)=
(1-p)\rho+pX\rho X
\]

For a phase-flip channel:

\[
\mathcal{E}(\rho)=
(1-p)\rho+pZ\rho Z
\]

For a depolarizing channel, the single-qubit model used by the implementations is:

\[
\mathcal{E}(\rho)=
(1-p)\rho+
\frac{p}{3}
(X\rho X+Y\rho Y+Z\rho Z)
\]

Under these definitions, the Pauli-Z expectation for a bit-flip channel is:

\[
E_{\text{noisy}}=(1-2p)E_{\text{ideal}}
\]

For the depolarizing channel:

\[
E_{\text{noisy}}=
\left(1-\frac{4p}{3}\right)E_{\text{ideal}}
\]

Phase-flip noise does not directly change computational-basis Pauli-Z statistics. It can still affect other observables, particularly those involving coherence.

The code uses analytical channel models rather than a complete hardware-level quantum simulator. Amplitude damping is represented in the SQL domain model but is not implemented as a numerical channel in the executable simulations.

## Zero-Noise Extrapolation

### Concept

Zero-Noise Extrapolation (ZNE) estimates an ideal observable by measuring a circuit at several noise levels and extrapolating the resulting observations toward zero noise.

The method does not require a perfectly noiseless quantum device.

Noise amplification can be performed using techniques such as:

- Gate folding.
- Unitary folding.
- Controlled circuit transformations.
- Hardware-specific noise scaling.

For noise scale factors \(\lambda\):

\[
E(\lambda)=E_0+a\lambda
\]

where:

- \(E_0\) represents the extrapolated zero-noise estimate.
- \(a\) represents the fitted linear coefficient.

For two measured points:

\[
E_0=
E(\lambda_1)-
\lambda_1
\frac{E(\lambda_2)-E(\lambda_1)}
{\lambda_2-\lambda_1}
\]

This is the linear Richardson extrapolation used in the implementations.

### Workflow

1. Execute the same logical computation under multiple effective noise levels.
2. Collect measurement statistics at each noise level.
3. Calculate the expectation value for every experiment.
4. Fit an extrapolation model.
5. Evaluate the model at zero noise.
6. Report the estimate together with its statistical uncertainty.

The implementations use noise scales of 1.0, 1.5, and 2.0.

The linear model is deliberately selected to keep the calculations understandable. More advanced implementations can use higher-order Richardson extrapolation, polynomial regression, exponential fitting, or model-selection techniques.

### Important limitation

Noise amplification also amplifies sampling uncertainty and can increase circuit execution costs.

A poor extrapolation model can produce an estimate outside the physical range of an expectation value. Such a result should not automatically be clipped because it may indicate model misspecification or inadequate measurements.

ZNE performance depends on the quality of noise scaling and the stability of the extrapolation model.

## Readout Error Mitigation

### Concept

Readout errors occur when a quantum measurement reports an incorrect computational-basis outcome.

A binary measurement system can be represented by a confusion matrix:

\[
M=
\begin{bmatrix}
1-e_{01}&e_{10}\\
e_{01}&1-e_{10}
\end{bmatrix}
\]

where:

- \(e_{01}\) is the probability of reporting 1 when the actual state is 0.
- \(e_{10}\) is the probability of reporting 0 when the actual state is 1.

The observed probability vector is:

\[
p_{\text{observed}}=Mp_{\text{ideal}}
\]

The corrected probability is estimated by:

\[
p_{\text{ideal}}=M^{-1}p_{\text{observed}}
\]

For the probability of measuring 1:

\[
p_1=
\frac{p_{1,\text{observed}}-e_{01}}
{1-e_{01}-e_{10}}
\]

The corrected Pauli-Z expectation is:

\[
E_{\text{corrected}}=1-2p_1
\]

### Workflow

1. Prepare known computational-basis states.
2. Measure each state repeatedly.
3. Estimate the assignment error probabilities.
4. Construct the confusion matrix.
5. Measure the actual experiment.
6. Apply matrix inversion.
7. Calculate corrected expectation values.

The Python, JavaScript, C++17, and Java 17 implementations demonstrate binary readout calibration.

The SQL implementation stores calibration records with measurement counts, calibration timestamps, and researcher identities.

### Failure conditions

The calibration matrix becomes singular when:

\[
1-e_{01}-e_{10}=0
\]

Near-singular matrices are also problematic because inversion amplifies statistical errors.

Calibration must be repeated when hardware characteristics change significantly.

## Probabilistic Error Cancellation

### Concept

Probabilistic Error Cancellation (PEC) uses a quasi-probability representation of an inverse noisy operation.

Instead of directly applying an unavailable inverse physical channel, the method represents the desired operation as a weighted combination of implementable noisy operations.

The weights can be negative and therefore do not form an ordinary probability distribution.

For a noise channel:

\[
\mathcal{E}
\]

PEC seeks an effective representation:

\[
\mathcal{E}^{-1}
=
\sum_i q_i\mathcal{E}_i
\]

where the coefficients \(q_i\) can be positive or negative.

The sampling overhead is related to the quasi-probability norm:

\[
\gamma=\sum_i|q_i|
\]

The approximate sampling overhead scales as:

\[
\gamma^2
\]

This can become expensive when noise is high or many operations require cancellation.

### Implementation distinction

The Python implementation provides an explicitly simplified bit-flip channel inversion and reports the associated theoretical sampling overhead.

It is an educational model, not a complete gate-by-gate PEC implementation. A production PEC system must construct valid quasi-probability decompositions for the actual noisy operations and account for their sampling variance.

PEC is particularly important because it demonstrates that reducing systematic bias can require substantially more experimental resources.

## Relationship Between Mitigation Techniques

| Technique | Primary target | Additional resource | Main limitation |
|---|---|---|---|
| ZNE | Gate and circuit noise | Repeated noise-scaled circuits | Extrapolation instability |
| Readout mitigation | Measurement assignment errors | Calibration experiments | Calibration drift and matrix conditioning |
| PEC | General modeled operation noise | Increased sampling overhead | Potentially very high execution cost |

These techniques are not interchangeable.

Readout calibration addresses measurement errors. ZNE addresses noise-dependent changes in circuit expectation values. PEC attempts to statistically invert modeled noisy operations.

Multiple methods can be combined when their assumptions are compatible. Care must be taken to avoid double-counting errors or applying corrections based on inconsistent calibration data.

## Python Implementation

The Python script uses a simulation-oriented architecture.

### Main components

| Component | Responsibility |
|---|---|
| `QubitState` | Represents a normalized single-qubit state |
| `QuantumCircuit` | Calculates noisy expectation values and samples measurements |
| `NoiseModel` | Identifies the selected noise channel |
| `ZeroNoiseExtrapolator` | Implements linear extrapolation |
| `ReadoutMitigator` | Corrects binary measurement probabilities |
| `ProbabilisticErrorCanceller` | Demonstrates quasi-probability sampling overhead |
| `QuantumErrorMitigationExperiment` | Coordinates an experiment |
| `ExperimentResult` | Stores estimates, uncertainties, and bias |

### Execution workflow

The default experiment prepares a computational-basis zero state and applies a bit-flip channel with probability 0.08.

The readout error is set to 0.04, and the measurement budget is 30,000 shots.

The script produces four types of output:

- Unmitigated measurement estimate.
- Readout-calibrated estimate.
- Zero-noise extrapolation estimate.
- Simplified probabilistic error cancellation estimate.

The results are printed and stored in `qem_results.json`.

The script includes input validation, deterministic random-number initialization, edge-case assertions, and output-path validation.

The random-number generator is intended for reproducible simulation and is not suitable for cryptographic applications.

## JavaScript Implementation

The JavaScript implementation emphasizes event-driven experiment execution and policy evaluation.

### Architecture

| Component | Responsibility |
|---|---|
| `QuantumState` | Immutable quantum-state representation |
| `NoiseChannel` | Noise-dependent expectation transformation |
| `MeasurementEngine` | Measurement sampling |
| `ReadoutCalibration` | Confusion-matrix correction |
| `ZeroNoiseExtrapolation` | Linear extrapolation |
| `MitigationPolicy` | Determines whether an experiment satisfies operational limits |
| `QuantumExperiment` | Controls lifecycle and emits events |

### Event-driven lifecycle

The experiment follows these transitions:

CREATED → RUNNING → COMPLETED

If an execution operation fails:

RUNNING → FAILED

Terminal states cannot be reopened.

The implementation uses Node.js `EventEmitter` to publish state changes and completion notifications.

`Map` stores method-specific results, while `Set` stores authorized mitigation methods.

The asynchronous `execute()` method returns a Promise. Report writing uses the Node.js filesystem API.

The policy checks:

- Maximum permitted noise.
- Minimum measurement shots.
- Authorized mitigation methods.

This separates scientific computation from operational acceptance rules.

## C++17 Implementation

The C++ implementation focuses on numerical execution and experiment governance.

### Domain architecture

| Component | Responsibility |
|---|---|
| `QubitState` | Normalized computational-basis probabilities |
| `NoiseChannel` | Applies channel-specific noise transformations |
| `MeasurementEngine` | Uses seeded random sampling |
| `ReadoutMitigator` | Corrects binary assignment errors |
| `ZeroNoiseExtrapolator` | Evaluates linear extrapolation |
| `Experiment` | Maintains experiment identity and lifecycle |
| `GovernancePolicy` | Evaluates resource and quality restrictions |
| `ExperimentEngine` | Executes the mitigation workflow |

The governance engine evaluates each result using a combination of numerical and operational conditions.

These include noise limits, measurement budgets, uncertainty thresholds, and authorized mitigation methods.

The program uses STL containers for observations and method authorization.

Its numerical loops require linear time in the number of measurement shots:

\[
T(N)=O(N)
\]

The storage required for an individual measurement result is constant:

\[
S(N)=O(1)
\]

The implementation does not construct full density matrices or simulate multi-qubit entanglement.

It focuses on expectation-value mitigation and resource governance.

## Java 17 Implementation

The Java implementation models an enterprise research experiment service.

It emphasizes explicit domain types, immutable records, service boundaries, and policy evaluation.

### Domain model

| Type | Purpose |
|---|---|
| `QubitState` | Immutable state representation |
| `QuantumChannel` | Common interface for noise operations |
| `NoiseModel` | Implements supported noise channels |
| `MeasurementResult` | Stores measurement statistics |
| `CalibrationMatrix` | Represents measurement calibration |
| `Experiment` | Defines a research experiment |
| `ResultRecord` | Stores a mitigation result |
| `GovernancePolicy` | Defines acceptance conditions |
| `PolicyDecision` | Stores policy evaluation |
| `ExperimentService` | Executes experiment workflows |
| `GovernanceService` | Evaluates experimental compliance |

### Enterprise lifecycle

The Java service uses the following lifecycle:

CREATED → VALIDATING → RUNNING → COMPLETED

A runtime failure during validation or execution transitions the experiment to FAILED.

The service rejects invalid transitions and returns immutable result collections.

`GovernanceService` evaluates each result independently of the numerical execution process.

This is an important design decision: a statistically improved result does not automatically become an accepted research result.

The result must also satisfy the applicable governance requirements.

## PostgreSQL Implementation

The database implementation models the complete research experiment lifecycle.

It separates project information, experimental configuration, measurements, calibration data, mitigation methods, and governance decisions.

### Relational architecture

Repository-like experiment organization is represented through the following relationships:

Research Projects
→ Researchers
→ Quantum Circuits
→ Noise Channels
→ Experiments
→ Calibration Records
→ Experiment Results
→ Extrapolation Observations
→ Governance Policies
→ Eligibility Decisions
→ Audit Events

### Main tables

| Table | Purpose |
|---|---|
| `research_projects` | Research project ownership |
| `researchers` | User identities and operational roles |
| `quantum_circuits` | Circuit configuration |
| `noise_channels` | Noise models and calibrated probabilities |
| `experiments` | Experiment execution state |
| `mitigation_methods` | Available mitigation strategies |
| `calibration_records` | Measurement calibration information |
| `experiment_results` | Estimated observables and uncertainty |
| `extrapolation_observations` | Measurements at different noise scales |
| `governance_policies` | Operational acceptance rules |
| `policy_allowed_methods` | Permitted mitigation methods |
| `eligibility_decisions` | Recorded policy decisions |
| `audit_events` | Lifecycle and evaluation history |

### Integrity enforcement

The schema uses:

- Primary keys for record identity.
- Foreign keys for relational consistency.
- Unique constraints for experiment and method combinations.
- Check constraints for probability ranges and resource values.
- Enumerated types for controlled workflow states.
- Triggers for lifecycle auditing.
- Indexes for common retrieval and reporting patterns.

The database prevents singular calibration matrices from being stored.

It also prevents completed, failed, or rejected experiments from being transitioned into another state.

### Stored procedures and functions

`calculate_bias()` calculates the difference between an estimated and ideal expectation value.

`record_experiment_result()` validates and stores experimental observations.

`evaluate_eligibility()` determines whether a measurement satisfies a selected governance policy.

`evaluate_and_record()` evaluates a result and persists its decision with reviewer identity and audit information.

### Policy evaluation

The eligibility function evaluates:

1. Whether the mitigation method is permitted.
2. Whether the noise level satisfies the policy threshold.
3. Whether the measurement shot count is sufficient.
4. Whether the uncertainty is within the accepted limit.
5. Whether a sufficiently recent calibration record exists.

A result can therefore be scientifically valid as an observation but operationally ineligible for a particular benchmark policy.

### SQL reporting

The script demonstrates:

- Detailed experiment retrieval through a view.
- Validation through the eligibility function.
- Aggregation of bias and uncertainty.
- Experiment lifecycle reporting.
- Common table expressions.
- Window functions for ranking mitigation methods.
- Resource-overhead calculations.
- Transaction-controlled experiment processing.

The SQL transaction ensures that the sample experiment's processing operations are committed together.

## Experimental Interpretation

The sample bit-flip experiment uses:

| Parameter | Value |
|---|---:|
| Ideal Pauli-Z expectation | 1.0 |
| Bit-flip probability | 0.08 |
| Readout assignment error | 0.04 |
| Measurement shots | 30,000 |
| ZNE scales | 1.0, 1.5, 2.0 |

The theoretical unmitigated expectation before readout error is:

\[
E_{\text{noisy}}=1-2(0.08)=0.84
\]

After symmetric readout error:

\[
E_{\text{observed}}=
0.84(1-2(0.04))
\]

\[
E_{\text{observed}}=0.7728
\]

The readout correction attempts to recover the expectation before measurement assignment errors.

The ZNE procedure attempts to estimate the zero-noise limit from measurements at amplified noise levels.

The exact observed values depend on finite-shot sampling.

The SQL sample records are illustrative database observations and are not required to match the random simulation outputs.

## Performance and Resource Considerations

Quantum error mitigation trades experimental resources for improved estimates.

### Shot complexity

For independent measurements, statistical uncertainty generally decreases as:

\[
SE\propto\frac{1}{\sqrt{N}}
\]

Reducing uncertainty by a factor of two requires approximately four times as many independent shots under comparable conditions.

### ZNE overhead

ZNE requires multiple circuit executions.

Its practical cost depends on the number of noise scales, shots per scale, circuit depth, and noise-amplification technique.

Higher-order extrapolation can reduce certain model biases but may increase variance.

### Readout mitigation overhead

Calibration requires additional measurements of known states.

For multi-qubit systems, the complete measurement assignment matrix can grow exponentially with qubit count.

Large systems therefore require structured calibration, tensor-product approximations, local correction methods, or alternative scalable approaches.

### PEC overhead

PEC sampling overhead can grow rapidly with circuit size and noise strength.

The theoretical sampling cost is related to the square of the quasi-probability norm.

This makes PEC potentially impractical for large, highly noisy circuits without careful optimization.

## Security, Reliability, and Research Integrity

Although quantum error mitigation is primarily a numerical methodology, production research platforms require operational safeguards.

Important controls include:

- Restricting experiment creation and policy modification to authorized identities.
- Recording calibration provenance and timestamps.
- Keeping raw measurements separate from corrected measurements.
- Preserving the original shot count and measurement configuration.
- Recording the exact mitigation method and its parameters.
- Retaining uncertainty estimates alongside corrected values.
- Maintaining audit trails for policy evaluations.
- Avoiding silent replacement of historical experiment results.
- Validating numerical inputs before performing matrix inversion.
- Monitoring calibration drift and hardware changes.

Random generators in these simulations are deterministic for reproducibility. Real experimental measurement systems must use the quantum hardware's actual measurement process.

Database roles in the sample schema model authorization identities. A deployed system must enforce permissions through PostgreSQL grants, row-level security where appropriate, and authenticated application services.

## Limitations

The implementations intentionally use a single-qubit expectation-value model.

They do not implement:

- Multi-qubit entanglement simulation.
- Full density-matrix simulation.
- General quantum circuit compilation.
- Hardware-specific gate folding.
- Full gate-level probabilistic error cancellation.
- Complete quantum state tomography.
- Dynamical decoupling.
- Clifford data regression.
- Learning-based noise characterization.
- Hardware execution through a quantum provider.
- Full uncertainty propagation for nonlinear mitigation models.

The simplified PEC model is illustrative rather than a complete general-purpose implementation.

The ZNE implementations use linear extrapolation. Real experiments may require nonlinear models and statistical model selection.

Readout correction uses binary measurement calibration. Multi-qubit calibration introduces additional computational and statistical challenges.

These limitations distinguish an educational mitigation workflow from a production quantum-computing research platform.

## Key Technical Distinctions

| Concept | Main question answered |
|---|---|
| Noise characterization | What errors affect the quantum device? |
| Noise mitigation | How can the effect of those errors on results be reduced? |
| Quantum error correction | How can encoded quantum information be protected and recovered? |
| Readout calibration | How frequently are measurement outcomes incorrectly assigned? |
| Zero-noise extrapolation | What observable would be estimated at zero noise under the selected model? |
| Probabilistic error cancellation | How can an inverse noisy operation be represented statistically? |
| Statistical uncertainty | How much sampling variability remains in the estimate? |
| Governance evaluation | Does the experimental result satisfy defined research requirements? |

The central engineering principle is that a mitigated estimate, its uncertainty, the underlying noisy observations, and the policy decision are separate pieces of information. Keeping them separate supports reproducibility, transparent comparisons, and defensible interpretation of quantum experiments.
