# Quantum Control: Pulses, Calibration and Control

## 1. Domain Overview

Quantum control concerns the manipulation of quantum states through precisely timed electromagnetic signals. In superconducting-qubit systems, microwave pulses manipulate qubit states by applying controlled rotations around selected axes of the Bloch sphere.

The quality of these operations depends on pulse amplitude, duration, phase, frequency detuning, timing accuracy, and hardware stability.

This project implements a quantum-control simulation and calibration workflow in Python, JavaScript, C++17, Java 17, and PostgreSQL.

The implementations focus on:

- Qubit state representation.
- Microwave pulse parameters.
- X, Y, and arbitrary-axis rotations.
- Rabi oscillations.
- Pi and pi/2 pulse calibration.
- Ramsey measurement and detuning estimation.
- Pulse scheduling and validation.
- Hardware safety constraints.
- Calibration history and approval.
- Execution monitoring.

The numerical models are educational approximations. They do not replace experimentally validated quantum-control software or hardware-specific pulse-generation systems.

## 2. Quantum States and the Bloch Sphere

A single qubit has a state that can be expressed as:

\[
|\psi\rangle =
\alpha |0\rangle + \beta |1\rangle
\]

where:

\[
|\alpha|^2 + |\beta|^2 = 1
\]

Here:

- \(|0\rangle\) is the computational ground state.
- \(|1\rangle\) is the computational excited state.
- \(\alpha\) and \(\beta\) are complex probability amplitudes.

For a pure single-qubit state, the Bloch representation is:

\[
|\psi\rangle =
\cos\left(\frac{\theta}{2}\right)|0\rangle
+
e^{i\phi}
\sin\left(\frac{\theta}{2}\right)|1\rangle
\]

The corresponding Bloch vector is:

\[
\vec r =
\begin{bmatrix}
\sin\theta\cos\phi\\
\sin\theta\sin\phi\\
\cos\theta
\end{bmatrix}
\]

The computational basis states occupy opposite poles:

- Ground state: \((0,0,1)\)
- Excited state: \((0,0,-1)\)

The excited-state probability is:

\[
P(1)=\frac{1-z}{2}
\]

The implementations use three-dimensional Bloch vectors to represent the state and calculate control operations.

This representation is computationally efficient for single-qubit unitary operations. It does not represent general multi-qubit entanglement.

## 3. Pulse Fundamentals

A control pulse is a time-dependent signal applied to a physical qubit.

The principal pulse parameters are:

| Parameter | Meaning | Unit |
|---|---|---|
| Amplitude | Strength of the applied control field | Model-dependent |
| Duration | Time for which the pulse is applied | Microseconds |
| Phase | Direction of rotation in the XY plane | Radians |
| Detuning | Difference between drive and qubit frequencies | MHz |
| Start time | Scheduled beginning of the pulse | Microseconds |

The implementations use an idealized effective rotation model.

For a resonant pulse:

\[
\theta = \Omega t
\]

where:

- \(\theta\) is the rotation angle.
- \(\Omega\) is the effective angular Rabi frequency.
- \(t\) is pulse duration.

The rotation angle is controlled through amplitude and duration.

For a general drive phase:

\[
\Omega_x = \Omega\cos\phi
\]

\[
\Omega_y = \Omega\sin\phi
\]

Detuning introduces a component along the Z axis:

\[
\Delta = 2\pi \delta
\]

The effective rotation frequency is:

\[
\Omega_{\mathrm{eff}} =
\sqrt{\Omega_x^2+\Omega_y^2+\Delta^2}
\]

The implementations use consistent model units, converting MHz to angular frequency in radians per microsecond.

### Pulse rotation

A pulse can be represented as a rotation around an axis:

\[
\hat n =
\frac{(\Omega_x,\Omega_y,\Delta)}
{\Omega_{\mathrm{eff}}}
\]

The Bloch vector is updated using Rodrigues' rotation formula:

\[
\vec r' =
\vec r\cos\theta
+
(\hat n\times\vec r)\sin\theta
+
\hat n(\hat n\cdot\vec r)(1-\cos\theta)
\]

This calculation supports arbitrary rotation axes without repeatedly constructing matrix representations.

## 4. X, Y and Arbitrary-Axis Pulses

### X pulses

An X pulse rotates the state around the Bloch sphere's X axis.

A resonant pi pulse transforms:

\[
|0\rangle \rightarrow |1\rangle
\]

The X pulse is useful for state inversion.

A pi/2 X pulse creates an equal superposition:

\[
|0\rangle
\rightarrow
\frac{|0\rangle-i|1\rangle}{\sqrt{2}}
\]

The relative phase depends on the rotation convention.

### Y pulses

A Y pulse rotates the qubit around the Y axis.

Its control phase is shifted by:

\[
\phi = \frac{\pi}{2}
\]

Y rotations are important in quantum gate construction and state preparation.

### Arbitrary-axis pulses

An arbitrary-axis pulse uses a configurable phase.

Its control components are determined by the selected phase and amplitude.

This permits rotations between X and Y directions without restricting the control operation to one fixed axis.

## 5. Rabi Oscillations and Calibration

Rabi oscillations describe the periodic transfer of population between two quantum states under resonant driving.

For an ideal resonant drive beginning in the ground state:

\[
P_1(t)=
\sin^2\left(\frac{\Omega t}{2}\right)
\]

The probability changes with the effective drive amplitude and pulse duration.

Important operating points include:

| Operation | Rotation angle | Result |
|---|---:|---|
| Identity | \(0\) | No state rotation |
| Pi/2 pulse | \(\pi/2\) | Equal superposition |
| Pi pulse | \(\pi\) | State inversion |
| Two pi pulses | \(2\pi\) | Return to initial Bloch vector |

### Calibration workflow

The calibration implementations perform an amplitude sweep.

The process is:

1. Select a qubit.
2. Select a pulse duration.
3. Define an allowed amplitude range.
4. Generate candidate amplitudes.
5. Simulate or evaluate each pulse.
6. Record excited-state probabilities.
7. Identify the amplitude with maximum excitation.
8. Calculate calibration error.
9. Record the calibration result.
10. Apply the acceptance threshold.

The estimated pi/2 amplitude is half the calibrated pi amplitude under the assumed linear amplitude-to-rotation relationship.

The calibration objective is:

\[
A_{\pi} =
\underset{A}{\operatorname{argmax}}
\ P_1(A,t)
\]

The reported excitation error is:

\[
E = 1-P_1
\]

The simulation uses a finite grid search rather than nonlinear parameter fitting. Its resolution depends on the number of amplitude samples.

A real experiment would require repeated measurements, statistical uncertainty estimation, readout calibration, and correction for hardware imperfections.

## 6. Ramsey Experiments and Frequency Detuning

Ramsey experiments characterize phase evolution and frequency mismatch.

A simplified Ramsey sequence consists of:

1. A pi/2 pulse.
2. A free-evolution interval.
3. A second pi/2 pulse.
4. Measurement of the resulting population.

During free evolution, the qubit accumulates relative phase.

For detuning \(\delta\):

\[
\varphi = 2\pi\delta t
\]

The resulting measurement follows an oscillatory relationship.

A simplified probability model is:

\[
P_1(t) =
\frac{1}{2}
\left[
1+\cos(2\pi\delta t+\varphi_0)
\right]
\]

The precise sign and phase depend on pulse conventions and measurement basis.

The Python, JavaScript, and Java implementations provide a basic phase-increment estimator using consecutive centered measurements.

This estimator assumes adequately sampled data and limited phase change between samples. It is not a substitute for robust sinusoidal fitting or a full Ramsey analysis.

The C++ implementation concentrates on pulse execution and calibration. Its core rotation engine can support Ramsey sequence construction through scheduled pulses.

## 7. Pulse Scheduling and Sequencing

Individual pulses are usually combined into control sequences.

A pulse sequence specifies:

- Pulse identity.
- Operation type.
- Amplitude.
- Duration.
- Phase.
- Detuning.
- Start time.

The implementations maintain a collection of pulse definitions and order them by start time.

A basic scheduling constraint is:

\[
t_{i+1}^{start}
\geq
t_i^{end}
\]

The current implementations reject overlapping pulses within one sequence.

This is a deliberately conservative scheduling policy. Real quantum-control hardware can support simultaneous operations on different channels, provided cross-talk, channel dependencies, timing alignment, and hardware constraints are satisfied.

Pulse scheduling is distinct from physical execution. A valid schedule does not prove that the hardware successfully generated the intended waveform.

## 8. Calibration Quality and Hardware Safety

Calibration quality and hardware safety are separate concerns.

A calibration can have a good measured fidelity while a proposed pulse violates hardware limits.

The implementations enforce configurable boundaries.

| Control | Validation |
|---|---|
| Amplitude | Must remain within the hardware maximum |
| Duration | Must remain within supported limits |
| Detuning | Must remain within the configured frequency range |
| Pulse count | Must remain within execution quotas |
| Pulse timing | Must satisfy scheduling rules |
| Qubit configuration | Must satisfy physical consistency checks |
| Calibration | Must meet the configured quality threshold |

For a qubit with relaxation time \(T_1\) and coherence time \(T_2\), the physical constraint is:

\[
T_2 \leq 2T_1
\]

The programs validate this relationship during qubit configuration.

### Failure handling

The implementations distinguish:

- Invalid pulse definitions.
- Unsafe amplitudes.
- Unsupported durations.
- Excessive detuning.
- Overlapping pulses.
- Invalid calibration sample counts.
- Failed calibration quality.
- Invalid measurement data.

Safety failures are rejected before pulse-state modification.

A production system would also require independent hardware interlocks, waveform limits, emergency-stop handling, equipment health checks, and authorization controls.

## 9. Python Implementation

The Python implementation uses dataclasses and enumerations to define the quantum-control domain.

Its principal components are:

| Component | Responsibility |
|---|---|
| `Qubit` | Stores qubit frequency and coherence parameters |
| `Pulse` | Defines pulse properties |
| `BlochState` | Represents the single-qubit state |
| `PulseController` | Validates and executes pulses |
| `PulseSequence` | Schedules and executes pulse collections |
| `CalibrationEngine` | Performs Rabi calibration |
| `CalibrationResult` | Stores calibration measurements and decisions |

### Engineering decisions

- `dataclass` provides structured domain records.
- `Enum` prevents arbitrary pulse and status values.
- Type annotations clarify interfaces.
- Exceptions distinguish validation and safety failures.
- `uuid` provides unique calibration identifiers.
- JSON persistence supports calibration history.
- Assertions test expected pulse behavior.

The implementation uses the Python standard library and does not require external quantum-computing packages.

### Execution

Run:

`python quantum_control.py`

The program performs Rabi calibration, executes a calibrated pulse, prints the resulting Bloch state, saves calibration history, and runs validation tests.

## 10. JavaScript Implementation

The JavaScript implementation emphasizes event-driven control and asynchronous experiment workflows.

Its principal components are:

| Component | Responsibility |
|---|---|
| `HardwarePolicy` | Defines control boundaries |
| `Qubit` | Validates qubit configuration |
| `Pulse` | Provides immutable pulse definitions |
| `BlochVector` | Performs state rotations |
| `QuantumController` | Executes pulses and emits events |
| `PulseSchedule` | Maintains ordered pulse operations |
| `CalibrationService` | Runs asynchronous Rabi experiments |

### Event-driven behavior

The controller extends Node.js `EventEmitter`.

It publishes:

- `pulse:executed`
- `calibration:started`
- `calibration:completed`

This separates control operations from monitoring and reporting.

Asynchronous calibration allows other event-loop operations to run between measurement evaluations.

Calibration records are maintained in a `Map`, while the schedule uses an array with ordered pulse entries.

The implementation also supports JSON persistence using the Node.js filesystem API.

### Execution

Run:

`node quantum_control.js`

No external npm packages are required.

## 11. C++17 Implementation

The C++ implementation emphasizes numerical operations, explicit state management, and efficient data structures.

Its principal components are:

| Component | Responsibility |
|---|---|
| `Qubit` | Models qubit properties |
| `Pulse` | Represents a control operation |
| `BlochVector` | Calculates state rotations |
| `PulseController` | Enforces hardware limits |
| `PulseSchedule` | Maintains pulse order |
| `CalibrationEngine` | Performs amplitude-sweep calibration |
| `CalibrationRecord` | Stores calibration outcomes |

### Engineering decisions

The implementation uses:

- `struct` for compact domain records.
- `enum class` for strongly typed control states.
- `vector` for calibration and pulse collections.
- STL sorting for chronological scheduling.
- `clamp` for probability boundaries.
- Exceptions for invalid and unsafe operations.

The rotation algorithm performs a constant number of arithmetic operations per pulse.

For \(N\) pulses, sequence execution takes:

\[
O(N)
\]

Adding a pulse to the vector-based schedule requires an overlap scan and sorting. The implemented insertion strategy is approximately:

\[
O(N\log N)
\]

for sorting after insertion, plus \(O(N)\) overlap validation.

### Compilation

Compile with:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic quantum_control.cpp -o quantum_control`

Run:

`./quantum_control`

## 12. Java 17 Implementation

The Java implementation introduces an enterprise-oriented domain model.

Its design separates hardware validation, pulse execution, calibration policy, and calibration records.

| Component | Responsibility |
|---|---|
| `HardwareLimits` | Immutable hardware configuration |
| `Qubit` | Validated qubit record |
| `Pulse` | Immutable pulse definition |
| `BlochState` | Mutable simulation state |
| `HardwareSafetyPolicy` | Pulse validation |
| `QuantumController` | State-transition execution |
| `PulseSchedule` | Sequence management |
| `CalibrationPolicy` | Calibration acceptance criteria |
| `CalibrationService` | Calibration lifecycle and history |

Java records provide immutable configuration and measurement objects.

The `PulseValidator` interface separates hardware validation from controller implementation.

The calibration service uses a `Map` to organize calibration versions by qubit identifier.

The `latestApproved` method retrieves the most recent passing calibration without exposing mutable internal collections.

The design distinguishes a calibration result from the policy decision used to accept it.

### Execution

Compile:

`javac --release 17 QuantumControl.java`

Run:

`java QuantumControl`

The program requires no third-party dependencies.

## 13. PostgreSQL Implementation

The PostgreSQL implementation models a relational quantum-control operations database.

The schema separates physical equipment, pulse definitions, experimental measurements, calibration decisions, and execution records.

### Entity relationships

The principal relationships are:

| Entity | Relationship |
|---|---|
| `control_users` | Owns and reviews control operations |
| `qubits` | Identifies physical qubits |
| `hardware_configs` | Defines equipment constraints |
| `pulses` | Stores reusable pulse definitions |
| `pulse_sequences` | Groups pulses for a qubit |
| `sequence_steps` | Defines sequence order and timing |
| `calibration_experiments` | Tracks experiment lifecycle |
| `experiment_measurements` | Stores experimental observations |
| `calibration_records` | Stores calibration versions |
| `calibration_approvals` | Records review decisions |
| `pulse_executions` | Tracks execution requests |
| `control_audit_log` | Maintains operational audit events |

### Integrity enforcement

Primary keys identify records.

Foreign keys preserve relationships between equipment, experiments, measurements, calibration records, and execution requests.

Check constraints validate numerical ranges and physical consistency.

Unique constraints prevent duplicate experiment samples and duplicate calibration versions for a qubit.

Triggers enforce:

- Hardware amplitude limits.
- Duration restrictions.
- Detuning limits.
- Pulse overlap detection.
- Experiment completion before calibration.
- Reviewer authorization.
- Calibration approval decisions.
- Experiment lifecycle restrictions.

### Views and reporting

The database includes three reporting views.

`v_latest_calibrations` retrieves the latest calibration version for each qubit.

`v_experiment_summary` aggregates measurement statistics.

`v_execution_monitor` presents execution status alongside qubit and operator information.

Additional queries demonstrate:

- Rabi measurement aggregation.
- Calibration eligibility.
- Calibration version comparisons.
- Window-function analysis.
- Best-measurement selection using a CTE.
- Failed experiment investigation.

### Transaction handling

The `start_experiment` procedure uses row locking to protect experiment state transitions.

The execution example uses a transaction to check calibration eligibility and insert an execution request.

This prevents an execution request from being accepted based solely on a previously displayed calibration status.

Database eligibility is still not equivalent to hardware authorization. A real deployment must revalidate hardware state at the point of execution.

## 14. Calibration Governance

Calibration is not simply the calculation of a pulse amplitude.

A controlled calibration workflow must preserve measurement evidence, validation decisions, and version history.

The implemented workflow follows:

**Experiment creation**

A qubit and hardware configuration are selected.

**Experiment execution**

The experiment transitions through its lifecycle and produces measurement records.

**Parameter estimation**

The Rabi measurement sweep identifies a candidate operating amplitude.

**Quality evaluation**

The measured excitation probability is compared with a configured acceptance threshold.

**Approval**

An authorized reviewer records the calibration decision.

**Execution eligibility**

The calibration must have an accepted status, and the associated qubit must be available.

**Audit**

The calibration and execution records preserve operational history.

The Java implementation maintains calibration versions in memory. The PostgreSQL implementation stores versioned records and approval decisions.

These approaches demonstrate complementary application-level and database-level governance.

## 15. Distinctions Between Control Concepts

Several concepts must remain distinct when designing a quantum-control system.

| Concept | Primary purpose |
|---|---|
| Pulse generation | Creates the control waveform |
| Pulse scheduling | Determines when operations occur |
| Pulse execution | Applies operations to a quantum system |
| Rabi calibration | Determines appropriate drive parameters |
| Ramsey measurement | Characterizes phase evolution and detuning |
| State estimation | Infers the quantum state from measurements |
| Hardware validation | Prevents unsupported control operations |
| Calibration approval | Determines whether a calibration can be used |
| Execution monitoring | Tracks the outcome of control operations |

A mathematically valid pulse is not necessarily hardware-safe.

A hardware-safe pulse is not necessarily calibrated.

A calibrated pulse is not necessarily approved.

An approved calibration does not guarantee successful physical execution.

These distinctions are important for reliable experimental operation.

## 16. Limitations and Physical Considerations

The implementations use idealized single-qubit rotations.

They do not fully simulate:

- Decoherence during pulse execution.
- Thermal relaxation.
- Pure dephasing.
- Readout errors.
- Leakage into higher energy levels.
- Cross-talk between qubits.
- Pulse distortion.
- Frequency drift.
- Instrument latency.
- Nonlinear control response.
- Multi-qubit entanglement.
- Real-time feedback.
- Measurement backaction.

The qubit records include \(T_1\) and \(T_2\) parameters for domain validation, but the current rotation engines do not apply a complete open-system noise model.

A realistic experimental control stack would also need waveform sampling, digital-to-analog conversion, clock synchronization, instrument calibration, feedback control, and hardware-specific safety verification.

The amplitude calibration examples assume that effective Rabi frequency is proportional to the amplitude parameter. Actual systems require experimental characterization of this relationship.

## 17. Computational Complexity

| Operation | Complexity |
|---|---|
| Bloch-vector rotation | \(O(1)\) |
| Excited-state probability | \(O(1)\) |
| Single pulse validation | \(O(1)\) |
| Pulse execution | \(O(1)\) |
| Rabi amplitude sweep | \(O(S)\) |
| Pulse overlap validation | \(O(N)\) |
| Sorting a pulse schedule | \(O(N\log N)\) |
| Calibration history lookup | \(O(1)\) average in hash maps |
| JSON serialization | \(O(R)\) in record count |
| Database measurement aggregation | Depends on indexed measurement count |

Here:

- \(S\) represents calibration samples.
- \(N\) represents scheduled pulses.
- \(R\) represents stored calibration records.

The relational implementation uses indexes on frequently queried qubit identifiers, experiment states, sequence identifiers, and calibration versions.

## 18. Security and Production Controls

A production quantum-control environment should enforce strict separation between experiment design and physical execution.

Important controls include:

- Role-based access to calibration approval.
- Authentication of control operators.
- Hardware-level amplitude and duration limits.
- Immutable experimental evidence.
- Calibration version tracking.
- Execution authorization.
- Audit logging.
- Secure storage of hardware credentials.
- Input validation at application and database boundaries.
- Transactional updates.
- Independent emergency-stop mechanisms.
- Monitoring for abnormal control behavior.

Database roles should be granted only the permissions required by their responsibilities. Application credentials should not have unrestricted administrative access.

Pulse limits must also be enforced by the physical control system rather than relying exclusively on application validation.

The implementations establish a foundation for understanding these controls while keeping numerical simulation separate from real hardware operation.
