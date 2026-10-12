# Quantum Simulators: Statevector and Shot-Based Simulation

## Scope

Quantum simulation represents the evolution of a quantum system on a classical computer. Two closely related execution approaches are statevector simulation and shot-based simulation.

Statevector simulation calculates the complex amplitudes associated with the computational basis states of a quantum register. Shot-based simulation uses measurement probabilities to generate a finite collection of classical outcomes. These approaches answer different questions: the statevector describes the ideal mathematical state, while shot counts describe the statistical results expected from repeated measurements.

This repository implements both approaches through executable Python, JavaScript, C++, Java, and PostgreSQL examples. The implementations use small quantum circuits to demonstrate superposition, interference, entanglement, measurement probabilities, sampling variability, and computational resource limits.

The simulators are educational implementations. They do not model physical-device noise unless an extension explicitly introduces a noise model, and they are not intended to replace optimized simulation engines.

## Mathematical foundation

### Statevectors and basis states

A pure state of \(n\) qubits can be represented as

\[
|\psi\rangle =
\sum_{x=0}^{2^n-1} \alpha_x |x\rangle,
\]

where \(\alpha_x\) is a complex amplitude and \(|x\rangle\) denotes a computational basis state.

The normalization condition is

\[
\sum_{x=0}^{2^n-1} |\alpha_x|^2 = 1.
\]

The probability of observing basis state \(|x\rangle\) in a computational-basis measurement is

\[
P(x)=|\alpha_x|^2.
\]

Amplitudes are complex numbers, not probabilities. Their phases influence interference even though measurement probabilities depend on their squared magnitudes.

A dense statevector contains \(2^n\) amplitudes. With 16 bytes per double-precision complex number, the raw amplitude storage alone is approximately \(16 \times 2^n\) bytes. Programming-language objects, temporary arrays, indexing structures, and allocator overhead can increase actual memory consumption substantially.

### Quantum gates

An ideal quantum gate is represented by a unitary matrix \(U\). Applying a gate transforms the state according to

\[
|\psi'\rangle = U|\psi\rangle.
\]

Unitarity requires

\[
U^\dagger U=I.
\]

The implementations validate gate matrices where appropriate and preserve the state norm within floating-point tolerance.

The Hadamard gate prepares a balanced superposition from \(|0\rangle\):

\[
H|0\rangle=\frac{|0\rangle+|1\rangle}{\sqrt{2}}.
\]

A phase gate changes the phase of the \(|1\rangle\) component:

\[
P(\theta)=
\begin{pmatrix}
1&0\\
0&e^{i\theta}
\end{pmatrix}.
\]

Although a phase gate does not directly change computational-basis probabilities for an isolated qubit, it can change the probabilities obtained after subsequent gates.

### Controlled gates and entanglement

A controlled-X gate flips its target when its control is in state \(|1\rangle\). Applying a Hadamard gate to the first qubit and then a controlled-X gate produces a Bell state:

\[
|\Phi^+\rangle =
\frac{|00\rangle+|11\rangle}{\sqrt{2}}.
\]

Its ideal joint measurement distribution is

\[
P(00)=\frac12,\qquad P(11)=\frac12.
\]

The probabilities of \(01\) and \(10\) are zero in an ideal simulation. Each individual qubit nevertheless has a uniform marginal distribution. The joint correlations distinguish the entangled state from two independent uniform bits.

The five-qubit GHZ example extends this structure:

\[
|\mathrm{GHZ}_5\rangle =
\frac{|00000\rangle+|11111\rangle}{\sqrt{2}}.
\]

The ideal computational-basis measurement produces only all-zero and all-one outcomes.

## Statevector simulation versus shot-based simulation

| Property | Statevector simulation | Shot-based simulation |
|---|---|---|
| Main output | Complex amplitudes | Classical outcome counts |
| Probability calculation | Exact up to floating-point precision | Empirical frequencies approximate theoretical probabilities |
| Measurement randomness | Not needed to calculate the full ideal distribution | Required to generate sampled outcomes |
| Sampling error | Absent from the calculated distribution | Present because the number of observations is finite |
| Dense state storage | Generally exponential in qubit count | The implementation still constructs a statevector before sampling |
| Suitable analysis | Amplitudes, phase, interference, exact ideal probabilities | Histograms, observed frequencies, repeated-measurement statistics |
| Physical-device noise | Not automatically represented | Not automatically represented |
| Reproducibility | Deterministic for a fixed circuit and numerical implementation | Reproducible when the pseudorandom generator and seed are fixed |

Shot-based simulation is not necessarily a more memory-efficient quantum simulator. In these implementations, the statevector is first calculated, and sampling then draws outcomes from its measurement distribution. A circuit with a million shots may still require the memory needed for its complete statevector.

Alternative methods, including stabilizer simulation, tensor-network simulation, matrix-product-state simulation, and decision-diagram approaches, can exploit particular circuit structures to reduce resource consumption. Their efficiency depends on the circuit, entanglement structure, supported operations, and desired observables.

## Computational conventions

The implementations use little-endian qubit indexing internally. Qubit zero corresponds to the least significant bit of the basis-state index.

For a two-qubit register, the internal basis indices represent

| Index | Basis state |
|---:|---|
| 0 | \(|00\rangle\) |
| 1 | \(|01\rangle\) |
| 2 | \(|10\rangle\) |
| 3 | \(|11\rangle\) |

A displayed bitstring can use a different convention depending on the simulator. The programs explicitly map selected qubits to output positions so that measurement formatting does not depend on assumptions about printed bit order.

The Python, JavaScript, C++, and Java programs store complex amplitudes and apply local gates to amplitude pairs. A target-qubit gate pairs basis indices whose target bit differs. For controlled gates, the pair is transformed only when the control bit is set.

This pairwise update avoids constructing a full \(2^n \times 2^n\) matrix for every gate. It does not eliminate exponential statevector storage.

## Python implementation

The Python script provides the most extensive analytical implementation.

### Circuit construction

`QuantumCircuit` validates qubit indices and builds a sequence of immutable gate descriptions. It supports Hadamard, Pauli-X, Pauli-Y, Pauli-Z, phase, rotation about the Y axis, and controlled-X operations.

The gate matrix validation checks column orthonormality. The circuit builder rejects invalid target indices and controlled gates whose control and target are identical.

### State evolution

`statevector_simulate` starts with the all-zero computational basis state unless an initial state is supplied. Initial amplitudes are checked and normalized. Each gate is then applied to the current vector.

The implementation checks the final norm to detect numerical or algorithmic errors. Floating-point tolerances are necessary because complex arithmetic is not exact.

### Exact and marginal distributions

`probabilities_from_state` calculates the squared magnitude of each amplitude. `marginal_probabilities` aggregates amplitudes over unmeasured qubits and constructs a distribution over selected qubits.

Marginalization is important when a circuit contains many qubits but the experiment measures only a subset. It avoids incorrectly treating the unmeasured subsystem as though it were part of the observed bitstring.

### Shot sampling and statistical analysis

`sample_shots` uses a seeded pseudorandom generator to draw measurement outcomes. `counts_to_probabilities` converts the resulting counts to empirical frequencies.

`total_variation_distance` measures the difference between two discrete distributions:

\[
D_{\mathrm{TV}}(P,Q)=
\frac12\sum_x |P(x)-Q(x)|.
\]

A distance of zero means the distributions are identical. A nonzero distance between a theoretical distribution and finite-shot data does not, by itself, establish a simulator defect.

The Bernoulli standard-error calculation illustrates the uncertainty associated with estimating a single outcome probability:

\[
\operatorname{SE}(\hat p)=
\sqrt{\frac{p(1-p)}{N}},
\]

where \(N\) is the number of independent shots and \(p\) is the theoretical probability.

The function uses the theoretical probability to calculate the expected sampling scale. An analysis of real observed data would ordinarily estimate uncertainty from the empirical proportion or use an appropriate confidence interval.

### Advanced demonstrations

The GHZ circuit illustrates multi-qubit correlations. The phase-interference experiment shows how a phase shift changes the result of a subsequent Hadamard gate. Validation examples demonstrate rejection of malformed circuits and invalid statevectors.

The resource estimator distinguishes raw amplitude storage from actual Python memory consumption. The benchmark measures execution time for one circuit, not a general performance guarantee.

## JavaScript implementation

The JavaScript program emphasizes event-driven execution and incremental shot-count aggregation.

### Complex arithmetic

JavaScript does not provide a built-in complex-number primitive, so the program represents each complex number as an object with real and imaginary components. Dedicated functions implement addition, multiplication, conjugation, scaling, and squared magnitude.

Gate matrices are validated before being inserted into a circuit. This keeps malformed unitary operations out of the simulation path.

### Event-driven simulation jobs

`QuantumJobRunner` separates simulation execution from progress reporting. Listeners subscribe to `started`, `progress`, `completed`, and `failed` events.

The runner processes shots in batches and yields to the Node.js event loop between batches. This allows progress observers to execute while a longer job is being processed. It does not make the numerical work parallel or remove its CPU cost.

Counts are accumulated in a `Map` instead of retaining every sampled outcome. For \(N\) shots and \(K\) distinct observed outcomes, the count structure requires storage proportional to the number of observed outcomes rather than the number of individual measurement records.

The implementation uses `setImmediate` to yield between batches. It is designed for Node.js rather than a browser environment.

### Reproducibility and security

The seeded Mulberry32 pseudorandom generator makes demonstrations reproducible. It is not cryptographically secure and must not be used to generate cryptographic keys.

Reproducibility also depends on the circuit, sampling order, seed, and implementation. Changing batch sizes or sampling algorithms may change the generated sequence even when the underlying distribution is unchanged.

## C++ case study

The C++ program models a GHZ experiment validation pipeline.

### Architecture

The implementation separates the following responsibilities:

- `Matrix2` validates two-dimensional unitary gate matrices.
- `Gate` stores gate identity, target, optional control, and matrix data.
- `QuantumCircuit` validates gate placement and measurement selection.
- `simulate` executes the circuit and checks the state norm.
- `getMeasurementProbabilities` aggregates the probability distribution over measured qubits.
- `runShots` generates measurement counts with a seeded standard-library random engine.
- `totalVariationDistance` compares the theoretical and observed distributions.

This separation allows circuit validation, quantum-state evolution, measurement, and statistical evaluation to be tested independently.

### GHZ validation

The case study prepares a five-qubit GHZ state. The exact distribution assigns probability one half to `00000` and one half to `11111`.

The shot-based execution uses 20,000 samples. The resulting frequencies fluctuate around the theoretical values, while the ideal simulator must never generate any other bitstring with positive probability.

The invalid-outcome check is stronger than merely comparing aggregate frequencies. It detects outcomes forbidden by the ideal circuit. In a real noisy-device experiment, such outcomes could be legitimate evidence of noise, so the same rule would need to account for the experiment's noise model.

### Performance considerations

The statevector uses a `std::vector` of complex numbers, and gate application updates amplitude pairs. For \(n\) qubits, the vector contains \(2^n\) elements.

The code estimates raw storage using `sizeof(Complex)`. Actual memory usage also includes vector capacity and other implementation overhead. The configured qubit limit is a safety boundary, not a statement that every circuit below it will be fast.

## Java implementation

The Java program models a simulation service with typed requests, explicit job states, and immutable request and result records.

### Domain model

`SimulationMode` distinguishes `STATEVECTOR` from `SHOT_BASED`. `JobStatus` represents creation, validation, execution, completion, and failure. `JobRequest` validates the job identifier, simulation mode, and shot-count requirements before the service starts the computation.

A statevector request must use zero shots. A shot-based request must specify a positive count within the configured service limit.

The `Complex`, `Matrix2`, `Gate`, and `Circuit` records and classes represent the mathematical and circuit structures. Collection views prevent callers from modifying gate lists through the public API.

### Service behavior

`SimulationService` delegates numerical operations to `Simulator`. Exact jobs return statevector-derived probabilities without observed counts. Shot-based jobs return both theoretical probabilities and sampled counts, making the distinction between prediction and observation explicit in the result type.

The job-state representation describes the service workflow. The example is synchronous and does not implement a persistent job queue or concurrent worker pool.

The error boundary returns a failed result rather than allowing ordinary runtime exceptions to escape from the service. A production service would also need to retain the sanitized failure reason, record diagnostic identifiers, enforce resource quotas, and define cancellation and retry semantics.

## PostgreSQL relational model

The SQL script models experiment definitions, circuits, gates, execution jobs, exact outcomes, observed counts, and execution events.

### Experiments and circuits

`quantum_experiments` stores the purpose and lifecycle status of an experiment. `circuits` identifies the circuit, qubit count, gate count, and measured-qubit selection.

The `circuit_gates` table stores gates by circuit and position. Its primary key prevents duplicate positions within a circuit. Trigger validation ensures that target and control indices fall within the circuit's declared width.

The database stores gate parameters as JSONB because gate types can have different parameters. The schema validates the JSON structure but does not prove that every parameter corresponds to a mathematically valid unitary operation. That validation belongs in the simulation engine.

### Jobs and execution states

`simulation_jobs` distinguishes the execution mode, shot count, random seed, status, and timestamps. Check constraints prevent statevector jobs from declaring a positive shot count and prevent shot-based jobs from using zero shots.

The transition trigger rejects invalid state changes such as moving a completed job back to running. The audit trigger records accepted status changes in `execution_events`.

The audit table records job-state transitions, not a complete cryptographic audit trail. A production audit system may require restricted update privileges, retention policies, and external immutable logging.

### Exact probabilities and observed counts

`exact_outcomes` stores the ideal probability associated with each measured bitstring. `observed_counts` stores the number of times each bitstring occurred in a shot-based run.

These tables have different meanings. A theoretical probability is a real-valued prediction, while an observed count is a nonnegative integer. The empirical probability is obtained by dividing the observed count by the requested shot count.

The `finalize_simulation_job` function verifies that exact probabilities sum to one, outcome widths match the measurement selection, and observed counts sum to the declared shot count. It then marks the job as completed within the same transaction.

The function cannot independently establish that the supplied probabilities were computed correctly from the gate sequence. That requires a trusted simulation engine or a separate verification process.

### Indexing and transactional behavior

The status-and-submission index supports queries that retrieve recent jobs by status. The circuit-and-submission index supports circuit-specific execution history.

The script inserts experiment definitions, circuits, gate sequences, and sample execution records inside a transaction. It finalizes both an exact Bell-state job and a shot-based Bell-state job. A failure in the transaction prevents a partially committed demonstration dataset.

The trigger-based state history and relational constraints provide a database-level foundation for execution auditing. They do not replace application-level numerical validation, authorization, or operational monitoring.

## Interpreting sampling results

Suppose an ideal circuit produces a binary outcome with probability \(p=0.5\). Across \(N\) independent shots, the count \(X\) of that outcome follows a binomial distribution:

\[
X\sim\operatorname{Binomial}(N,p).
\]

Its expected count is

\[
E[X]=Np,
\]

and its variance is

\[
\operatorname{Var}(X)=Np(1-p).
\]

Consequently, increasing the shot count reduces the standard error of the estimated probability at a rate proportional to \(1/\sqrt{N}\). Doubling the shot count does not halve the standard error; approximately quadrupling the shot count is required for that reduction under the same sampling assumptions.

Observed probabilities should not be expected to equal theoretical probabilities exactly. The correct evaluation considers statistical uncertainty, circuit semantics, numerical precision, and whether the sampling model matches the intended experiment.

## Numerical and implementation limitations

### Exponential state growth

The dense statevector representation scales exponentially with qubit count. Even when a circuit contains few gates, storing all amplitudes may become impractical as the register grows.

The implementations use configurable qubit limits to prevent accidental allocations that are excessive for their intended educational use. Those limits differ because Python, JavaScript, C++, and Java have different object, array, and runtime overheads.

### Floating-point behavior

Gate operations use double-precision floating-point arithmetic. Small deviations from normalization may accumulate during long circuits. A tolerance should accommodate ordinary rounding error without concealing substantive implementation defects.

Probability calculations should be checked for finite values, nonnegative values, and a total near one. Normalizing a probability vector can correct small numerical drift, but it must not be used to hide invalid amplitudes or a fundamentally incorrect simulation.

### Measurement conventions

The interpretation of a displayed bitstring depends on the ordering of measured qubits. Applications should explicitly document bit ordering when comparing output from different simulators or when connecting simulator results to external data.

Measuring only a subset of qubits requires summing probabilities over all basis states that agree on the measured positions. Selecting a subset of bitstring positions without aggregating their probabilities would produce incorrect marginal distributions.

### Pseudorandom sampling

A fixed seed provides repeatability for a given implementation. It does not make a pseudorandom sample equivalent to the complete probability distribution, nor does it establish cryptographic security.

Independent repeated runs should use appropriately chosen seeds when statistical independence is required. Statistical testing should account for the possibility of rare outcomes that may not appear in a finite sample.

### Ideal circuits and noise models

All five implementations assume ideal unitary gates and ideal computational-basis measurement. They do not include decoherence, readout errors, gate infidelity, crosstalk, or device calibration uncertainty.

A noise-aware simulator must represent non-unitary quantum channels or an appropriate stochastic approximation. Density-matrix simulation can represent mixed states directly but generally requires \(O(4^n)\) storage for a dense matrix. Trajectory-based methods can approximate noisy evolution through repeated stochastic pure-state simulations.

## Practical interpretation

Statevector simulation is appropriate when the full ideal state, relative phases, exact measurement distribution, or quantum-state observables are required for a tractable circuit.

Shot-based simulation is appropriate when the quantity of interest is a measurement histogram, an empirical expectation value, or the statistical behavior of repeated measurements.

Neither approach alone guarantees efficient simulation of arbitrary large quantum circuits. The correct choice depends on circuit structure, number of qubits, supported gates, measured observables, available memory, and the precision required by the experiment.
