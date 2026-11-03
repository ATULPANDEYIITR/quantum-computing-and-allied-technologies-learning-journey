# Neutral-Atom Computing: Optical Trapping and Atom Arrays

## 1. Scope

Neutral-atom quantum computers use individually trapped neutral atoms as controllable physical systems. Optical tweezers are tightly focused laser beams that create localized potential wells. By controlling the positions and intensities of these traps, an experiment can capture atoms, arrange them into programmable geometries, and prepare arrays for later quantum operations.

This project concentrates on the optical trapping and array-formation stages:

- Gaussian optical tweezer potentials.
- Trap depth, beam waist, wavelength, and Rayleigh range.
- Radial and axial confinement.
- Rectangular arrays and lattice spacing.
- Probabilistic single-atom loading.
- Occupancy observations and vacancy identification.
- Atom-to-target rearrangement.
- Facility safety validation and experiment-state management.
- Relational storage and reporting for laboratory runs.

The implementations model planning and laboratory workflow. They do not constitute a full quantum-computing simulator or a real hardware controller.

## 2. Neutral Atoms and Optical Tweezers

### 2.1 Trapped neutral atoms

Neutral atoms have no net electric charge. Their interaction with an optical field depends on their atomic polarizability and the laser frequency relative to relevant atomic transitions.

A suitably detuned optical field produces a position-dependent potential. For a red-detuned trapping beam, the attractive potential is strongest near the intensity maximum. A tightly focused beam can therefore confine an atom near its focal point.

Common neutral-atom experimental platforms use alkali-metal atoms, including rubidium and cesium. The code examples use representative rubidium-87 parameters to make the calculations concrete.

An atom's location, internal state, and external motional state are distinct physical properties. These implementations primarily represent location and the classical occupancy of individual tweezer sites.

### 2.2 Gaussian beam model

A focused Gaussian beam has a transverse intensity profile that approximately follows a Gaussian distribution. Near the beam waist, a simplified potential-energy expression is:

\[
U(r)=-U_0\exp\left(-\frac{2r^2}{w_0^2}\right)
\]

where:

| Symbol | Meaning |
|---|---|
| \(U(r)\) | Potential energy at radial distance \(r\) |
| \(U_0\) | Positive magnitude of trap depth |
| \(r\) | Radial distance from the beam center |
| \(w_0\) | Beam waist |

The negative sign represents an attractive potential well. The trap depth is stored as a positive magnitude in the software, while the potential energy at the center is negative.

The beam radius changes along the propagation direction. For a Gaussian beam:

\[
w(z)=w_0\sqrt{1+\left(\frac{z}{z_R}\right)^2}
\]

The Rayleigh range is:

\[
z_R=\frac{\pi w_0^2}{\lambda}
\]

where \(\lambda\) is the laser wavelength.

A simplified three-dimensional potential is:

\[
U(r,z)=
-\frac{U_0}{1+(z/z_R)^2}
\exp\left(-\frac{2r^2}{w(z)^2}\right)
\]

The Python, JavaScript, and C++ implementations use this model to evaluate potential energy and derive trap characteristics.

### 2.3 Harmonic approximation and trap frequencies

Very close to the potential minimum, the Gaussian potential can be approximated by a harmonic oscillator. The angular confinement frequencies are:

\[
\omega_r=\sqrt{\frac{4U_0}{mw_0^2}}
\]

\[
\omega_z=\sqrt{\frac{2U_0}{mz_R^2}}
\]

The corresponding ordinary frequencies are:

\[
f_r=\frac{\omega_r}{2\pi}
\qquad
f_z=\frac{\omega_z}{2\pi}
\]

Here, \(m\) is the atomic mass. The radial and axial frequencies generally differ because the beam has different spatial curvature in the transverse and propagation directions.

These equations are local approximations near the trap minimum. They do not describe the full atomic motional spectrum, anharmonicity, heating, or escape dynamics.

### 2.4 Units and numerical stability

The implementations use SI units for optical and atomic parameters:

- Wavelength: metres.
- Beam waist: metres.
- Trap depth: joules.
- Atomic mass: kilograms.
- Frequency: hertz.
- Rayleigh range: metres.

Array coordinates and transport distances are expressed in micrometres because this scale is convenient for representing tweezer layouts.

Mixing micrometres and metres without explicit conversion can introduce errors of several orders of magnitude. Conversion occurs at the boundary between geometry and optical calculations.

All implementations validate positive physical parameters and reject non-finite numerical values.

## 3. Tweezer Arrays

### 3.1 Array geometry

A tweezer array is a collection of individually positioned optical traps. Each trap defines a potential well at a chosen location.

The project uses rectangular arrays represented by:

- Row index.
- Column index.
- Site identifier.
- Physical coordinates.
- Inter-site spacing.
- Shared trap calibration.

For a regular rectangular array with spacing \(d\), the coordinates of a site are:

\[
x_c=cd
\]

\[
y_r=rd
\]

where \(r\) and \(c\) are the row and column indices.

An array with \(R\) rows and \(C\) columns contains:

\[
N=RC
\]

potential trapping sites.

An array site is a potential location for an atom. Its existence does not imply that the site is occupied.

### 3.2 Lattice spacing and optical overlap

The spacing between tweezer sites influences several engineering decisions:

- Whether neighboring optical potentials are sufficiently separated.
- Whether individual sites can be addressed reliably.
- How much transport distance is required during rearrangement.
- Whether the selected geometry is compatible with the optical system.
- How much unwanted overlap occurs between neighboring intensity profiles.

The Python and C++ programs calculate a neighboring-beam intensity-envelope indicator:

\[
C_i=\sum_{j\ne i}
\exp\left(-\frac{2d_{ij}^2}{w_0^2}\right)
\]

where \(d_{ij}\) is the distance between tweezer centers.

This quantity is a geometric overlap indicator. It is not a measured optical interference pattern, a trap-depth correction, or a quantum-state fidelity.

The exact optical potential of an experimental array depends on beam coherence, polarization, optical aberrations, intensity calibration, and other apparatus-specific effects.

### 3.3 Array geometry versus occupancy

A rectangular array can be geometrically complete while containing vacancies.

The distinction is represented explicitly:

| Concept | Meaning |
|---|---|
| Array site | A configured optical trapping location |
| Occupied site | A site where an atom is detected |
| Vacant site | A configured site with no detected atom |
| Atom | A loaded neutral atom associated with a source location |
| Target site | A required final position in the intended geometry |

The array geometry is relatively static during an experiment. Occupancy is an observed result that can change between loading shots.

## 4. Probabilistic Atom Loading

### 4.1 Loading probability

Atom loading is not necessarily deterministic. A tweezer site may capture an atom, remain empty, or produce an outcome that requires imaging and classification.

A simplified model represents each site as an independent Bernoulli trial:

\[
X_i\sim\operatorname{Bernoulli}(p)
\]

where \(p\) is the probability of a site being occupied.

For an array with \(N\) independently loaded sites:

\[
E[\text{loaded atoms}]=Np
\]

The probability that every site is loaded under this simplified model is:

\[
P(\text{full array})=p^N
\]

For example, even a moderate individual-site loading probability can produce a much smaller probability of obtaining a completely occupied large array in one shot.

The Python and JavaScript implementations use seeded random number generators so that the loading simulation can be repeated.

The C++ and Java examples also include explicit occupancy observations. These allow rearrangement behavior to be tested independently of random loading outcomes.

### 4.2 Single-atom occupancy

Many tweezer-loading procedures use collisional blockade or related mechanisms to favor zero or one atom per site.

The Bernoulli occupancy model represents this simplified outcome. It does not simulate the collision process, loading sequence, temperature dependence, or probability of multiple occupancy.

An observed occupancy record should therefore be interpreted as a classified experimental result, not as a complete physical account of how the atom was loaded.

### 4.3 Imaging and occupancy classification

Fluorescence imaging can be used to distinguish occupied and vacant locations. The result can be represented as a mapping from site identifiers to occupancy states.

The PostgreSQL implementation stores:

- Run identifier.
- Array identifier.
- Site identifier.
- Occupancy observation.
- Detection-confidence value.
- Observation timestamp.

The confidence value records a classification-related measure. It should not be confused with atom survival probability, quantum-state fidelity, or the probability that a rearrangement succeeds.

## 5. Atom Rearrangement

### 5.1 Why rearrangement is required

Probabilistic loading generally produces an irregular occupancy pattern. A desired experiment may require a regular array with a specific number of atoms and a specific geometry.

Rearrangement uses movable optical traps to transport atoms from occupied source locations to selected target locations.

The objective is to create a target configuration while avoiding reuse of an atom or target position.

A simplified planning problem can be written as a bipartite assignment:

- One set contains the available atoms.
- The other set contains the desired target positions.
- Each possible atom-to-target pair has a transport cost.
- An atom can be assigned to at most one target.
- A target can receive at most one atom.

### 5.2 Distance-based assignment

For an atom at position \(a_i\) and target position \(t_j\), the Euclidean transport distance is:

\[
d_{ij}=
\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}
\]

The Python implementation uses a rectangular Hungarian algorithm to minimize total assigned distance.

Its assignment behavior depends on the number of available atoms:

| Condition | Assignment behavior |
|---|---|
| Atoms equal targets | All atoms are assigned to all targets |
| Atoms exceed targets | All targets are assigned; surplus atoms remain unused |
| Atoms fewer than targets | All available atoms are assigned, but some targets remain empty |
| No atoms or no targets | Planning is rejected |

The rectangular Hungarian implementation has time complexity \(O(n^2m)\), where \(n\) is the smaller partition and \(m\) is the larger partition.

### 5.3 Alternative optimization approaches

The other implementations use different engineering approaches.

**C++17 minimum-cost flow**

The C++ program constructs a residual network:

- Source to atom vertices.
- Atom vertices to target vertices.
- Target vertices to sink.

Every source-atom and target-sink edge has unit capacity. Atom-to-target edges carry a squared-displacement cost.

Successive shortest augmenting paths with reduced-cost potentials find a minimum-cost maximum matching.

If \(F\) assignments are made in a graph with \(V\) vertices and \(E\) edges, the implementation uses a priority-queue shortest-path procedure for each augmentation. Its approximate complexity is \(O(FE\log V)\) for the represented network.

The squared-displacement objective is a deliberate engineering choice. It penalizes long moves and gives integer costs for the selected half-spacing coordinate representation. It is not identical to minimizing the sum of Euclidean distances.

**JavaScript and Java priority-queue or sorted-edge heuristics**

The JavaScript and Java implementations generate candidate atom-target pairs, order them by distance, and accept the shortest pair when neither endpoint has already been assigned.

This approach is easier to integrate into an event-driven or enterprise workflow, but it is a heuristic. A locally shortest assignment does not necessarily produce the globally shortest total transport distance.

**PostgreSQL deterministic baseline**

The SQL procedure ranks observed source sites and target sites and pairs them in a reproducible order. This provides an auditable relational workflow, not an optimal transport solution.

The database approach deliberately separates the storage and validation of assignments from more sophisticated external optimization.

### 5.4 Planning is not physical transport

An assignment specifies which atom should reach which target. It does not define a safe physical trajectory.

A real transport system must also consider:

- The movement path of each atom.
- Trap depth during transport.
- Maximum acceleration and velocity.
- Motional excitation.
- Atom loss during movement.
- Interactions between simultaneously transported atoms.
- Trap crossing and collision avoidance.
- Acoustic-optic or spatial-light-modulator update rates.
- Optical power redistribution.
- Timing synchronization.

The calculated distance is therefore a planning metric, not an experimentally demonstrated transport result.

## 6. Python Implementation

The Python script provides a compact numerical and algorithmic model.

### Implemented components

| Component | Responsibility |
|---|---|
| `TrapCalibration` | Gaussian trap parameters and frequencies |
| `Point` | Two-dimensional position and distance calculations |
| `TweezerArray` | Array geometry, loading, occupancy, and optical overlap |
| `Atom` | Atom identifier and observed source location |
| `TargetSite` | Required final position |
| `rectangular_hungarian` | Rectangular minimum-cost assignment |
| `plan_rearrangement` | Atom-to-target move generation |
| `run_self_tests` | Validation of important numerical and assignment behavior |

The script includes an explicit imaging pattern with ten observed atoms and a nine-position target array. This separates the assignment example from the independent random-loading demonstration.

The `gaussian_tail_fraction` method returns a geometric overlap estimate. The combined-potential method sums the Gaussian potential contributions from the configured sites under an incoherent or time-averaged approximation.

Input validation rejects invalid array dimensions, duplicate site observations, unknown site identifiers, non-finite coordinates, and invalid loading probabilities.

The Hungarian algorithm handles rectangular problems by making the smaller partition the row dimension. This avoids padding the problem with artificial assignments.

## 7. JavaScript Implementation

The JavaScript file emphasizes asynchronous experiment orchestration and safety-policy evaluation.

### Implemented components

| Component | Responsibility |
|---|---|
| `TrapCalibration` | Optical calibration and harmonic frequencies |
| `TweezerArray` | Site construction and occupancy observations |
| `makeTargetGrid` | Target geometry |
| `greedyGlobalAssignment` | Distance-ranked assignment heuristic |
| `ExperimentController` | Experiment lifecycle and event reporting |
| `LabError` | Structured operational failures |

The controller follows an explicit state machine:

`IDLE -> PREFLIGHT -> VALIDATED -> LOADED -> REARRANGED -> READY`

A failed operation can move the active state to `ABORTED`.

The preflight policy considers:

- Calibration validity.
- Maximum beam power.
- Maximum array size.
- Minimum configured site spacing.
- Vacuum pressure.
- Laser interlock health.
- Emergency-stop state.
- Target geometry.

The controller emits events when the state changes, when occupancy is observed, when safety validation fails, and when a rearrangement plan is created.

The event log provides an operational audit trail. A caller can subscribe to events without needing to inspect the internal state of the controller.

The `busy` flag rejects concurrent execution through the same controller. The asynchronous boundaries represent imaging and control-system interactions, but no physical devices are accessed.

## 8. C++17 Implementation

The C++ program focuses on assignment optimization and numerical efficiency.

### Implemented components

| Component | Responsibility |
|---|---|
| `Point` | Position and Euclidean distance |
| `TrapCalibration` | Optical parameters and trap frequencies |
| `TweezerArray` | Rectangular geometry and overlap calculation |
| `MinimumCostFlow` | Residual graph and flow optimization |
| `Atom` | Source identity and position |
| `Target` | Requested destination |
| `Move` | Selected source-to-target assignment |

The flow algorithm uses edge capacities and reverse residual edges. Reverse edges allow earlier assignments to be revised while the algorithm searches for a better overall solution.

Reduced-cost potentials maintain non-negative edge costs for Dijkstra's shortest-path operation.

Integer squared-displacement costs avoid floating-point comparisons inside the optimization algorithm. The final physical travel distance is calculated separately in micrometres.

Validation occurs before the graph is constructed. Invalid calibration values, invalid geometry, impossible flow requests, and failed assignment extraction produce explicit errors.

The number of atom-target candidate edges grows as the product of the number of atoms and targets. This matters when planning substantially larger arrays.

## 9. Java 17 Implementation

The Java program models a facility-level experiment service.

### Domain model

The principal records represent immutable configuration or result data:

- `TrapCalibration`
- `TweezerArray`
- `Site`
- `Telemetry`
- `FacilityPolicy`
- `RunRequest`
- `Finding`
- `Move`
- `RunResult`
- `AuditEvent`

The `SafetyRule` interface separates the evaluation of individual policies from experiment orchestration.

The supplied rules cover vacuum pressure, laser interlock and emergency-stop state, calibration validity, beam power, and array geometry.

`ExperimentService` controls the state transitions and calls the rearrangement planner. It prevents a run from reaching `READY` unless all requested targets have assignments.

`RunLedger` separates audit persistence from experiment execution. The included in-memory implementation uses concurrent collections so that independent experiment records do not require one shared mutable event list.

`RunRejectedException` retains structured findings. This distinguishes a policy rejection from an unexpected software failure.

The priority-queue rearrangement heuristic is intentionally separate from the minimum-cost flow implementation in C++. This allows the enterprise-oriented workflow to be evaluated independently of the optimization algorithm.

## 10. PostgreSQL Implementation

The PostgreSQL script models the persistent relational workflow of a neutral-atom laboratory.

### 10.1 Relational entities

| Table | Purpose |
|---|---|
| `trap_calibration` | Optical calibration and validity period |
| `tweezer_array` | Array geometry and calibration association |
| `array_site` | Individual trapping positions |
| `lab_run` | Experiment identity, requested target count, and state |
| `run_environment` | Vacuum and interlock telemetry |
| `site_observation` | Measured site occupancy |
| `rearrangement_plan` | One planned arrangement per run |
| `transfer_move` | Individual source-to-target assignments |

Foreign keys prevent observations and movements from referencing sites belonging to another array.

The `site_observation` primary key ensures one occupancy result per site in a particular run. Composite foreign keys preserve the relationship between a run, its array, and its sites.

The transfer table uses two different uniqueness constraints:

- A source site can be used only once in one plan.
- A target site can receive only one atom in one plan.

The trigger on `transfer_move` verifies that the source site was observed as occupied and that the plan is still open for assignments.

### 10.2 Run lifecycle

The run lifecycle is:

`draft -> validated -> loaded -> rearranged -> ready`

A run may enter `failed` from a non-ready state.

The `enforce_run_state_transition` trigger rejects unsupported state transitions even when an update does not originate from the stored procedures.

The stored procedures have separate responsibilities:

| Procedure | Responsibility |
|---|---|
| `validate_run` | Evaluate preflight and validate the run |
| `mark_loaded` | Confirm occupancy observations are complete |
| `build_rearrangement_plan` | Create deterministic source-to-target assignments |
| `complete_rearrangement` | Verify move count and mark the run ready |

### 10.3 Preflight evaluation

The `run_preflight` function returns:

- Eligibility.
- Rejection reasons.
- Occupied-site count.
- Observed-site count.
- Total site capacity.

The sample policy requires a healthy laser interlock, no active emergency-stop condition, acceptable vacuum pressure, valid calibration, complete occupancy observations, and enough observed atoms to fill the requested targets.

The vacuum threshold is a configurable illustrative policy value, not a universal physical limit for neutral-atom experiments.

### 10.4 Trap-frequency calculation

The `trap_frequencies` function calculates Rayleigh range and harmonic confinement frequencies directly in PostgreSQL.

This permits calibration values to be inspected and evaluated without exporting the records to another application.

### 10.5 Reporting

The views provide distinct operational measurements:

- `v_run_occupancy` reports observed loading and vacancy counts.
- `v_rearrangement_report` reports assigned moves and transport distances.

The reporting queries distinguish occupancy from requested target capacity. They also distinguish assignment completion from quantum-state fidelity.

The sample transaction creates a valid run and an interlock-rejected run. The rejected case is caught in a controlled `DO` block so that the remaining reporting queries can execute.

## 11. Engineering Rules and Failure Conditions

The code implements common validation rules across the five source files.

| Condition | Expected behavior |
|---|---|
| Non-positive wavelength or beam waist | Reject calibration |
| Non-positive trap depth or atomic mass | Reject calibration |
| Non-finite coordinates | Reject geometry |
| Non-positive site spacing | Reject array |
| Duplicate occupied-site identifiers | Reject occupancy input |
| Unknown source site | Reject occupancy input |
| More targets than available array sites | Reject facility configuration |
| Insufficient loaded atoms | Reject full target-array completion |
| Expired calibration | Reject experiment preflight |
| Unhealthy laser interlock | Reject experiment preflight |
| Excessive vacuum pressure | Reject experiment preflight |
| Reuse of an atom in one plan | Reject assignment or violate a database constraint |
| Reuse of a target in one plan | Reject assignment or violate a database constraint |
| Invalid experiment-state transition | Reject state update |

The examples use fixed safety thresholds for demonstration. A production facility should obtain these limits from approved laboratory procedures and apparatus-specific calibration records.

## 12. Performance and Scalability

The implementations illustrate several ways to manage the computational cost of array planning.

| Approach | Cost characteristic | Main trade-off |
|---|---|---|
| Bernoulli loading | \(O(N)\) | Simple independent-site approximation |
| Gaussian overlap calculation | \(O(N^2)\) | Directly compares every pair of sites |
| Hungarian assignment | \(O(n^2m)\) | Global minimum assignment |
| Sorted-edge heuristic | \(O(ST\log(ST))\) | Easier implementation but not globally optimal |
| Minimum-cost flow | Approximately \(O(FE\log V)\) | Flexible network optimization with residual edges |
| SQL scan-order assignment | Dominated by ranking and joining site records | Auditable baseline rather than optimized transport |

Here, \(N\) is the number of array sites, \(S\) is the number of loaded atoms, \(T\) is the number of targets, \(F\) is the number of assignments, and \(V\) and \(E\) are the flow-network vertex and edge counts.

For larger systems, the complete atom-target graph can become a memory bottleneck. A more scalable implementation can use geometric candidate restrictions, spatial indexing, target partitioning, or hierarchical planning.

The shortest-distance objective also does not account for every physical transport constraint. A physically useful planner may need to optimize path length, transport duration, congestion, trap crossings, loss risk, and heating together.

## 13. Physical Limitations

The following physical effects are outside the scope of these implementations:

**Trap lifetime and atom loss**

Atoms may leave a trap because of heating, collisions, background-gas interactions, or insufficient trap depth. A successful assignment does not establish that an atom survives transport.

**Motional excitation**

Moving an atom too quickly can excite its external motional state. A position-only plan does not calculate the atom's motional wavefunction or final temperature.

**Optical aberrations and calibration uncertainty**

The ideal Gaussian model does not include aberrations, power fluctuations, polarization variation, or spatially varying beam-waist errors.

**Optical interference**

The simple neighboring-beam overlap measure is not a complete treatment of coherent optical fields. A physical optical model may need to account for phase, polarization, and interference.

**Imaging errors**

The code accepts measured occupancy as input but does not implement a camera model, photon-count distribution, atom-loss detection, or false-positive and false-negative classification.

**Quantum-state evolution**

The programs do not simulate Rydberg excitation, blockade interactions, coherent gates, entanglement, measurement back-action, or error correction.

**Hardware synchronization**

No implementation controls actual lasers, shutters, cameras, vacuum equipment, acoustic-optic deflectors, or spatial light modulators.

## 14. Security, Integrity, and Operational Controls

The software examples emphasize validated input, explicit failure states, and traceable operations.

The JavaScript and Java controllers evaluate environmental and optical safety conditions before declaring a run ready.

The SQL design uses constraints, foreign keys, triggers, and stored procedures to prevent invalid relationships and unsupported state changes.

A production laboratory information system should also apply:

- Authenticated users and role-based permissions.
- Separation between experiment configuration and hardware-control privileges.
- Protected calibration and telemetry records.
- Timestamped audit events.
- Controlled changes to safety policies.
- Backup and recovery procedures.
- Transactional storage of occupancy and transfer records.
- Independent validation of any physical hardware command.

A database record saying that a rearrangement is complete must not be treated as proof that the physical movement occurred. Hardware telemetry and experimental verification must support that claim.
