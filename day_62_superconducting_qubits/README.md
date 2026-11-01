# Superconducting Qubits: Josephson Junctions and Circuits

## Scope

This project models the physical and computational foundations of superconducting qubits through Josephson-junction circuits, with emphasis on the transmon and rf-SQUID structures.

The five executable implementations use different engineering perspectives:

| Implementation | Primary perspective | Main focus |
|---|---|---|
| Python | Numerical physics model | Josephson relations, RCSJ dynamics, transmon spectrum, qubit state |
| JavaScript | Event-driven simulation | Circuit calculations, asynchronous measurement monitoring, state evaluation |
| C++17 | Numerical engineering | Repository-independent circuit engine, RCSJ trajectory simulation, state-vector sampling |
| Java 17 | Enterprise domain model | Explicit circuit types, validation, simulation service, measurement workflow |
| PostgreSQL | Relational model | Circuit inventory, measurement records, validation functions, workflow and governance |

The implementations are intentionally self-contained and use standard facilities rather than specialized external quantum-computing packages.

## Physical Model

A Josephson junction consists of two superconducting regions separated by a thin barrier. The junction supports a nondissipative supercurrent controlled by the superconducting phase difference.

The central current-phase relation is:

`I = I_c sin(phi)`

where:

- `I` is the Josephson supercurrent.
- `I_c` is the critical current.
- `phi` is the superconducting phase difference.

The Josephson voltage relation is:

`V = (Phi0 / 2pi) dphi/dt`

where `Phi0` is the superconducting flux quantum.

The flux quantum is:

`Phi0 = h / (2e)`

The factor of `2e` reflects the charge of a Cooper pair.

These two relations connect phase, current, voltage, and circuit dynamics.

## Josephson Energy

The Josephson energy is related to critical current by:

`E_J = Phi0 I_c / (2pi)`

The source implementations calculate this quantity directly from the junction parameters.

The quantity `E_J / h` expresses the Josephson energy as a frequency, which makes it easier to compare circuit energy scales with microwave transition frequencies.

A larger critical current produces a larger Josephson energy.

The junction also has a small-signal Josephson inductance near zero phase:

`L_J = Phi0 / (2pi I_c)`

This inductive interpretation is important because superconducting qubit circuits combine Josephson nonlinear elements with capacitive and inductive circuit components.

## Josephson Junction Parameters

The implementations use three primary junction parameters:

| Parameter | Symbol | Physical role |
|---|---|---|
| Critical current | `I_c` | Sets the strength of the Josephson nonlinear element |
| Junction capacitance | `C_J` | Stores electric energy and participates in plasma oscillations |
| Normal resistance | `R_N` | Represents dissipative conduction in the RCSJ model |

The validation layer rejects non-positive or non-finite values because such values do not represent the intended physical circuit model.

## RCSJ Circuit

The resistively and capacitively shunted junction model represents the junction as three parallel contributions:

1. Josephson supercurrent
2. Resistive current
3. Capacitive current

The governing equation can be written as:

`I_bias = I_c sin(phi) + V/R + C dV/dt`

Using the Josephson voltage relation gives a nonlinear differential equation for the phase.

The Python, JavaScript, C++17, and Java implementations contain numerical phase-dynamics models.

The numerical state contains:

- phase
- phase velocity
- time
- bias current

The Python implementation uses a fourth-order Runge-Kutta integration path. The JavaScript, C++17, and Java implementations use a compact semi-implicit Euler approach.

The difference is deliberate. The Runge-Kutta implementation provides a higher-order numerical reference, while the other implementations emphasize compact engineering simulation and explicit state management.

## Plasma Frequency

The small-signal plasma frequency is obtained from the effective Josephson inductance and junction capacitance.

The angular frequency is approximately:

`omega_p = 1 / sqrt(L_J C_J)`

The ordinary frequency is:

`f_p = omega_p / (2pi)`

The implementations expose the plasma frequency as a derived property rather than storing it as an independent parameter. This prevents inconsistent duplicated values.

## rf-SQUID Circuit

The rf-SQUID model combines a Josephson junction with a superconducting loop.

Its potential energy contains an inductive contribution and the Josephson contribution:

`U(phi) = (Phi0 / 2pi)^2 (phi - phi_ext)^2 / (2L) - E_J cos(phi)`

The normalized external phase is:

`phi_ext = 2pi Phi_ext / Phi0`

The dimensionless screening parameter is:

`beta_L = 2pi L I_c / Phi0`

The rf-SQUID model illustrates how a Josephson junction changes the potential landscape of a superconducting loop.

The source files evaluate the potential for supplied phase and external-flux values and reject invalid circuit parameters.

## Transmon Qubit

The transmon is a superconducting qubit derived from a Josephson junction and a capacitive energy scale.

A key design parameter is the ratio:

`E_J / E_C`

where:

- `E_J` is the Josephson energy.
- `E_C` is the charging energy.

The transmon operates in a regime where `E_J / E_C` is large enough to reduce sensitivity to charge noise while retaining sufficient anharmonicity for selective microwave control.

The leading approximation for the lowest transition is:

`f_01 ≈ sqrt(8 E_J E_C) / h - E_C / h`

The approximate anharmonicity is:

`alpha ≈ -E_C / h`

The negative anharmonicity means that successive transitions are not equally spaced.

This unequal spacing is essential. A harmonic oscillator would have equally spaced levels, making selective two-level control difficult. The Josephson junction supplies the required nonlinearity.

## Transmon Energy Levels

The implementations calculate approximate energy levels using:

`E_n ≈ -E_J + sqrt(8 E_J E_C)(n + 1/2) - E_C(6n^2 + 6n + 3)/12`

This approximation is useful for understanding the first few levels without solving the full circuit Hamiltonian numerically.

The source implementations calculate levels for `n = 0`, `1`, `2`, and `3`.

The approximation should not be interpreted as a complete device simulation. Real device analysis can require Hamiltonian diagonalization, electromagnetic modeling, calibration data, environmental coupling models, and experimentally measured parameters.

## Two-Level Qubit Representation

The source implementations separate circuit physics from the abstract computational state.

A two-level state is represented as:

`|psi> = alpha |0> + beta |1>`

with normalization:

`|alpha|^2 + |beta|^2 = 1`

The implementations provide:

- state normalization
- probability calculation
- a simple Y-axis rotation
- computational-basis measurement
- measurement sampling

A `pi/2` rotation from `|0>` produces an equal-probability state in the simplified real-amplitude model.

Measurement produces either `0` or `1`, after which the state is collapsed to the corresponding computational basis state.

This state-vector representation is intentionally distinct from the physical circuit model. The junction determines the energy structure and transition behavior, while the state vector represents an abstract two-level computational state.

## Python Implementation

The Python file provides the most complete numerical reference implementation.

Its main domain objects are:

- `JosephsonJunction`
- `Transmon`
- `RfSquid`
- `Qubit`

The `JosephsonJunction` class derives Josephson energy, Josephson inductance, plasma frequency, current, and voltage.

The `Transmon` class derives `E_J/E_C`, the `0 -> 1` transition, anharmonicity, and approximate energy levels.

The `RfSquid` class evaluates flux-dependent potential energy and generates sampled potential profiles.

The `Qubit` dataclass stores complex amplitudes and provides normalization, rotation, probability, and measurement behavior.

The RCSJ simulator provides a numerical trajectory containing time, phase, and phase velocity.

The script also exercises invalid parameters such as negative critical current, zero capacitance, negative charging energy, and negative loop inductance.

## JavaScript Implementation

The JavaScript implementation uses a different architecture.

It models the circuit using classes and uses `Map` and `Set` for event subscriptions.

The `CircuitMonitor` class provides an event-driven layer around measurement processing.

A `measurement-complete` event is emitted after a batch of measurements finishes. This separates circuit calculation from monitoring behavior.

The JavaScript implementation uses a semi-implicit Euler method for RCSJ simulation. The phase velocity is updated before the phase, which is a useful compact approach for dissipative nonlinear dynamics.

Complex amplitudes are represented as objects containing `re` and `im` fields rather than using an external complex-number library.

The implementation is suitable for execution in a Node.js runtime.

## C++17 Implementation

The C++17 implementation emphasizes deterministic numerical engineering.

The domain model uses:

- classes
- exception types
- STL vectors
- structured records
- standard random distributions
- explicit validation

The `JosephsonJunction` class owns the physical junction parameters.

`Transmon` and `RfSquid` hold references to the junction model so that derived properties always use the same physical source parameters.

The `StateVector` structure represents the computational state and performs normalization, rotation, and measurement.

The RCSJ simulation returns a vector of `PhasePoint` records.

The implementation also checks for numerical instability by rejecting non-finite phase or phase-rate values.

The C++ design is appropriate for situations where explicit memory ownership, predictable runtime behavior, and low-level numerical control matter.

## Java 17 Implementation

The Java implementation uses explicit domain and service boundaries.

The principal domain types are:

- `JosephsonJunction`
- `Transmon`
- `RfSquid`
- `QubitState`
- `PhasePoint`
- `MeasurementResult`

Java records are used for immutable result structures.

`CircuitSimulationService` owns simulation and measurement operations rather than placing all workflow behavior inside the domain objects.

`CircuitException` provides a controlled failure path for invalid circuit parameters and unstable numerical states.

The implementation also uses `List.copyOf` when returning simulation results so callers receive an immutable view of the completed trajectory.

This structure separates physical-domain state from application-level services.

## PostgreSQL Implementation

The PostgreSQL implementation treats a superconducting-qubit project as a relational engineering system.

The central circuit relationship is:

`Repository -> Circuits -> Measurements`

The repository layer stores research and implementation context, while circuit tables store physical component parameters and states.

The `circuits` table supports:

- transmons
- rf-SQUIDs
- Josephson junction components
- control lines
- readout components

The circuit table stores physical parameters such as:

- critical current
- capacitance
- normal resistance
- loop inductance
- charging energy

Database constraints reject invalid positive physical parameters.

## Relational Workflow

The database also models engineering workflow around circuit changes.

The principal relationship is:

`Repository`
`    -> Branches`
`        -> Commits`
`            -> Pull Requests`
`                -> Reviews`
`                    -> Review Comments`
`                -> Status Checks`
`                -> Branch Protection`
`                    -> Approval Requirements`
`                -> Merge Eligibility`

This workflow is separate from the physical circuit equations.

A Pull Request represents a proposed change.

A Code Review represents evaluation of that proposed change.

An Approval represents a reviewer decision.

Branch Protection represents repository-level enforcement.

Merge Eligibility combines those conditions into a final decision.

These concepts are not interchangeable.

## Pull Request Lifecycle

A Pull Request connects a source branch containing proposed changes to a target branch.

The database stores:

- source branch
- target branch
- author
- title
- description
- draft state
- head commit
- base commit
- workflow state

The `pull_request_commits` table records the changeset associated with a Pull Request.

A Draft Pull Request can be used while implementation is still being developed. A non-draft Pull Request represents a change intended for formal review.

Synchronizing the base branch changes the relationship between the proposed head and target branch. This can affect conflicts and the validity of previously submitted review decisions.

A Pull Request can be open, eligible, blocked, merged, or closed.

Reopening a previously closed change is a workflow operation rather than a new physical circuit component.

## Code Review

Code Review evaluates the implementation contained in a Pull Request.

The database distinguishes review decisions using `review_state`.

The available states are:

- `COMMENTED`
- `APPROVED`
- `CHANGES_REQUESTED`
- `DISMISSED`

A review contains:

- reviewer identity
- Pull Request
- review state
- review text
- reviewed commit
- submission timestamp

This commit association is important because an approval of one revision does not necessarily represent approval of a later revision.

Review comments are stored separately so that individual issues can be tracked and resolved.

Each comment contains a file path, line number, body, and resolution state.

## Review Discussions

A review comment can remain unresolved while the Pull Request progresses through additional changes.

The database records both `resolved` and `resolved_at`.

This permits merge-eligibility logic to distinguish between:

- a review comment that was raised and resolved
- a review comment that remains open

A repository policy can require all review conversations to be resolved before merging.

This is an enforcement condition rather than a review decision itself.

## Approvals

An approval is represented by a review whose state is `APPROVED`.

The database also records the commit that the reviewer evaluated.

This allows eligibility queries to require approvals associated with the current Pull Request head commit.

A stale approval is therefore not treated as automatically equivalent to approval of a newer revision.

A dismissed review is excluded from active approval counting.

Reviewer eligibility is modeled through the `reviewers` table and contributor roles.

The sample policy requires both a senior engineer and a security reviewer.

This demonstrates that an approval count alone can be insufficient when repository policy requires specific reviewer roles.

## Branch Protection

Branch Protection operates at the target branch level.

The `branch_protection_policies` table stores:

- required review count
- stale-review behavior
- status-check requirements
- direct-push restrictions
- force-push restrictions
- branch-deletion restrictions
- conversation-resolution requirements
- linear-history requirements
- administrator bypass policy

The protected `main` branch in the sample data rejects direct pushes and force pushes.

The policy also requires status checks and resolved conversations.

The branch-protection layer does not perform the technical review itself. It defines the conditions that a Pull Request must satisfy before the repository permits a merge.

## Approval Requirements

The `approval_requirements` table adds role-specific requirements to branch protection.

The sample policy requires:

| Reviewer role | Required approvals |
|---|---:|
| Senior engineer | 1 |
| Security reviewer | 1 |

This prevents a situation where two approvals from the same role are incorrectly treated as satisfying a policy that requires independent technical and security review.

The distinction is important in engineering repositories containing hardware-control logic or experimental circuit parameters.

## Merge Eligibility

The PostgreSQL function `evaluate_merge_eligibility` combines the repository policy with the current Pull Request state.

It evaluates:

- current approvals
- approvals associated with the current head commit
- passing status checks
- unresolved review comments
- required review count
- conversation requirements
- status-check requirements

The result is stored in `merge_eligibility`.

The stored decision includes a human-readable reason, making blocked states auditable.

A Pull Request can therefore be blocked because:

- approvals are insufficient
- status checks are not passing
- review conversations remain unresolved
- the repository policy otherwise prohibits merging

## Status Checks

Automated checks are represented separately from human reviews.

The `status_checks` table records:

- check name
- state
- evaluated commit
- completion time
- details

The sample repository uses:

- `unit-tests`
- `numerical-stability`
- `security-scan`

This distinction matters because a Pull Request may have sufficient human approvals while still being blocked by an automated numerical or security check.

## Circuit Data Model

The physical circuit database records a different class of engineering state.

Circuit lifecycle values include:

- `DESIGNED`
- `FABRICATED`
- `COOLED`
- `CHARACTERIZED`
- `CALIBRATED`
- `FAILED`
- `RETIRED`

This represents a device lifecycle rather than a source-control lifecycle.

For example, a transmon can be `CALIBRATED` while a Pull Request modifying its calibration model is still `OPEN`.

The two states should not be conflated.

## Measurement Data

The `qubit_measurements` table records experimental or simulated measurement results.

Each measurement stores:

- circuit
- measurement basis
- shot count
- zero count
- one count
- measurement timestamp

The database enforces:

`zero_count + one_count = shots`

This is a database-level invariant rather than an application-only assumption.

The sample data contains 1000 measurements with approximately balanced computational-basis results.

## Database Physics Functions

The PostgreSQL script contains functions for:

- Josephson energy
- Josephson inductance
- approximate transmon `f01`
- Pull Request merge eligibility

The physical functions are immutable because their results depend only on their supplied arguments.

This makes them suitable for deterministic analytical queries.

For example, a circuit query can calculate `E_J` directly from the stored critical current rather than persisting a potentially inconsistent derived value.

## Validation Strategy

Validation exists at multiple layers.

### Application validation

Python, JavaScript, C++17, and Java reject invalid physical parameters before simulation.

Examples include:

- negative critical current
- zero capacitance
- negative resistance
- negative loop inductance
- negative charging energy
- invalid qubit-state normalization
- invalid simulation step counts

### Database validation

PostgreSQL uses:

- `CHECK` constraints
- `UNIQUE` constraints
- foreign keys
- enumerated types
- triggers
- transactional updates

This prevents invalid relational states even when data does not originate from the application layer.

## Failure Conditions

Important failure conditions include:

| Failure | Detection |
|---|---|
| Non-positive `I_c` | Parameter validation |
| Non-positive capacitance | Parameter validation |
| Non-positive resistance | Parameter validation |
| Invalid charging energy | Transmon validation |
| Invalid loop inductance | rf-SQUID validation |
| Non-finite numerical state | Simulation validation |
| Missing required approvals | Merge-eligibility evaluation |
| Failed status checks | Merge-eligibility evaluation |
| Unresolved review conversations | Merge-eligibility evaluation |
| Invalid measurement counts | PostgreSQL `CHECK` constraint |
| Unauthorized merge | PostgreSQL trigger |

The database trigger prevents a Pull Request from being moved to `MERGED` unless a recorded eligible decision exists.

## Security Considerations

Physical circuit parameters can influence calibration, control, and experimental behavior, so repository governance should not be treated as unrelated administrative metadata.

The model uses separate roles for engineering and security review.

Branch protection prevents direct pushes to the protected branch in the sample policy.

Force pushes are disabled.

Branch deletion is disabled.

Status checks provide an automated gate before merge.

Review decisions are associated with specific commits so that a review does not silently become approval of an unrelated revision.

The implementations also avoid executing arbitrary external commands, loading untrusted files, or requiring external network services.

## Numerical Considerations

The circuit equations are nonlinear.

For the RCSJ model, numerical stability depends on:

- capacitance
- resistance
- critical current
- time step
- bias current
- initial phase
- initial phase velocity

A time step that is too large can produce numerical instability even when the underlying physical system is well behaved.

The implementations explicitly check for non-finite numerical states.

The Python implementation uses fourth-order Runge-Kutta integration, which provides better local accuracy than first-order Euler integration at increased computational cost.

The other implementations use semi-implicit Euler for a compact and efficient engineering model.

## Complexity

The main operations have straightforward complexity.

| Operation | Complexity |
|---|---:|
| Junction property calculation | `O(1)` |
| Transmon level calculation | `O(1)` per level |
| rf-SQUID potential evaluation | `O(1)` |
| Potential profile with `N` points | `O(N)` |
| RCSJ simulation with `N` steps | `O(N)` |
| Measurement sampling with `M` shots | `O(M)` |
| Indexed Pull Request lookup | approximately `O(log N)` |
| Indexed review lookup | approximately `O(log N)` |

The physical models contain constant-size state for a single junction or two-level qubit.

Large-scale circuit simulation would require substantially different numerical and memory strategies because real devices can contain many interacting degrees of freedom.

## Important Distinctions

The project deliberately keeps several concepts separate.

### Josephson junction versus qubit

A Josephson junction is a nonlinear superconducting circuit element.

A superconducting qubit is a designed quantum system whose accessible energy levels form a computational subspace.

The junction supplies nonlinearity but is not itself equivalent to the complete qubit architecture.

### Transmon versus rf-SQUID

A transmon is optimized for qubit operation with reduced charge sensitivity and useful anharmonicity.

An rf-SQUID is a flux-sensitive superconducting loop containing a Josephson junction.

The two structures share Josephson physics but serve different circuit purposes.

### Circuit physics versus qubit state

Circuit parameters determine energy scales, transition frequencies, and potential landscapes.

The state vector describes the quantum state within a selected computational model.

### Pull Request versus Code Review

A Pull Request proposes a change.

Code Review evaluates that change.

### Code Review versus Approval

Code Review is the evaluation process.

Approval is one possible decision produced by that process.

### Approval versus Branch Protection

Approval represents a reviewer decision.

Branch Protection specifies repository-level conditions that determine whether a change may be merged.

### Branch Protection versus Merge Eligibility

Branch Protection defines the policy.

Merge Eligibility evaluates the current Pull Request against that policy and current repository state.

## End-to-End Technical Relationship

The physical and software models can be viewed as two connected engineering layers.

The circuit layer is:

`Josephson Junction`
`       |`
`       +--> E_J`
`       +--> L_J`
`       +--> Plasma Frequency`
`       |`
`       +--> Transmon`
`       |      +--> E_J / E_C`
`       |      +--> f_01`
`       |      +--> Anharmonicity`
`       |`
`       +--> rf-SQUID`
`              +--> Flux-dependent Potential`

The repository-governance layer is:

`Repository`
`    |`
`    +--> Branch`
`    |      +--> Commit`
`    |`
`    +--> Pull Request`
`           +--> Review`
`           |      +--> Review Comment`
`           +--> Status Checks`
`           +--> Branch Protection`
`                  +--> Approval Requirements`
`                  +--> Merge Eligibility`
`                         +--> Merge`

The first layer describes how Josephson circuits behave.

The second layer describes how changes to the corresponding engineering artifacts can be reviewed and controlled.

## Practical Engineering Interpretation

The central physical design idea is that the Josephson junction introduces controlled nonlinearity into a superconducting circuit.

The central transmon design idea is to combine that nonlinearity with a large capacitive energy scale ratio so that the device becomes less sensitive to charge fluctuations while retaining enough anharmonicity for microwave control.

The central rf-SQUID idea is to combine Josephson energy with loop inductive energy so that external magnetic flux modifies the circuit potential.

The central software design idea is to represent physical parameters, derived quantities, state transitions, measurements, and governance conditions as explicit entities rather than as unvalidated values.

The source implementations therefore cover the complete relationship from junction parameters to derived circuit properties, from circuit properties to simplified qubit-state behavior, and from engineering source changes to controlled merge eligibility.
