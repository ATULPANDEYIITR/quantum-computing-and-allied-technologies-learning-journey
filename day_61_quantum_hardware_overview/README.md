# Quantum Hardware Overview: How Quantum Computers Are Built

## Scope

This project models the physical and control architecture required to construct and operate a quantum computer. The implementations focus on two representative hardware platforms:

- superconducting qubits
- trapped-ion qubits

The central engineering idea is that a quantum computer is not only a quantum processor. It is a coordinated stack of physical subsystems, measurement hardware, classical electronics, control software, calibration procedures, and environmental constraints.

A simplified system relationship is:

Processor
→ Qubits
→ Physical Control
→ Measurement
→ Classical Electronics
→ Calibration
→ Experiment Execution
→ Error Evaluation

The five implementations deliberately represent the same engineering domain from different perspectives rather than mechanically translating one program into another.

## Hardware Architecture

A useful hardware abstraction is:

Quantum processor
├── Qubit array
├── Control subsystem
├── Readout subsystem
├── Environmental subsystem
└── Classical control subsystem

The exact physical implementation depends on the qubit technology.

For superconducting hardware, the processor normally operates at extremely low temperatures. Microwave signals control the qubits, resonators participate in measurement, and cryogenic amplifiers help preserve weak readout signals.

For trapped-ion hardware, individual ions are confined using electromagnetic fields in an ultra-high-vacuum environment. Lasers perform state preparation, control, entangling operations, and measurement.

The common architecture is therefore conceptual rather than physically identical.

## Qubit Technologies

| Technology | Physical system | Main control mechanism | Important engineering constraint |
|---|---|---|---|
| Superconducting | Josephson-junction circuits | Microwave pulses | Cryogenic operation, crosstalk, coherence |
| Trapped ion | Atomic ions | Lasers and electromagnetic fields | Vacuum, laser stability, optical alignment |
| Neutral atom | Neutral atoms in optical traps | Laser and optical control | Trap stability and atom loss |
| Photonic | Individual or correlated photons | Optical components | Loss, source quality, detector efficiency |
| Spin | Electron or nuclear spin states | Magnetic, microwave, or optical control | Material defects and control precision |

No platform removes the need for classical infrastructure. Every practical quantum computer requires mechanisms for preparing states, applying operations, measuring results, calibrating hardware, and interpreting classical data.

## Building a Superconducting Quantum Computer

A superconducting processor starts with microscopic electrical circuits that behave as quantum systems. Josephson junctions provide the nonlinear element needed to form controllable qubits.

The physical stack can be represented as:

Chip fabrication
→ superconducting circuit
→ packaging
→ cryogenic refrigerator
→ microwave wiring
→ control electronics
→ readout electronics
→ classical software

### Chip

The chip contains qubits, coupling structures, resonators, and control/readout interfaces. Fabrication quality directly affects frequency variation, losses, defects, and device yield.

The Python implementation represents each qubit with:

- physical identifier
- operating frequency
- coherence time
- gate fidelity
- readout fidelity

These properties are not merely descriptive. They participate in validation and execution-budget calculations.

### Cryogenics

Superconducting processors operate at temperatures near the millikelvin range. A dilution refrigerator provides several thermal stages and progressively reduces the temperature toward the mixing chamber.

The relevant engineering problem is not simply reaching a low temperature. The system must maintain the required temperature while carrying thermal loads from wiring, amplifiers, packaging, radiation, and control infrastructure.

The PostgreSQL model stores:

- temperature
- pressure
- cooling capacity
- thermal load
- readout availability

A cooling-utilization query compares thermal load with available cooling capacity.

### Microwave Control

Microwave signals are used to manipulate superconducting qubits. A practical control chain can contain:

signal generation
→ attenuation
→ filtering
→ frequency conversion
→ amplification
→ chip input

Important error sources include phase noise, amplitude errors, pulse distortion, frequency drift, and crosstalk.

The Python and C++ implementations model gate duration and error rates. The Java implementation represents the same physical requirements through immutable domain records and policy validation.

### Readout

Quantum measurement must convert a fragile quantum state into a classical signal.

A superconducting readout path can involve resonators, amplifiers, digitizers, and classical signal processing. Measurement fidelity becomes a distinct engineering metric because a highly accurate gate system can still produce poor computational results if measurement is unreliable.

## Building a Trapped-Ion Quantum Computer

Trapped-ion systems use atomic ions as qubits.

A simplified architecture is:

Ion source
→ vacuum chamber
→ electromagnetic trap
→ laser cooling
→ state control
→ entangling operations
→ fluorescence detection
→ classical processing

The principal physical requirements differ from superconducting hardware.

### Ultra-High Vacuum

The ions must remain isolated from collisions with background gas. Vacuum quality therefore becomes a fundamental operating condition.

The JavaScript model represents hardware components and operating constraints as objects. A trapped-ion implementation in the Python model uses substantially longer coherence times and different gate durations to show why platform characteristics affect system-level execution.

### Electromagnetic Trapping

Electric and magnetic fields confine ions in controlled locations. The trapping potential must be stable enough to prevent unwanted motion and heating while allowing deliberate manipulation.

Control electronics must maintain field stability without introducing excessive noise.

### Optical Control

Lasers perform several important tasks:

- cooling
- state preparation
- single-qubit manipulation
- entangling operations
- state-dependent measurement

Laser frequency stability, beam alignment, intensity stability, optical-path drift, and detector performance all affect system reliability.

### Fluorescence Measurement

A trapped ion can be illuminated so that its internal state produces a measurable optical signal. Photodetectors convert the optical result into classical information.

The architecture therefore combines quantum physics with conventional optical, electronic, vacuum, and computing systems.

## Coherence and Gate Time

A central hardware constraint is the relationship between coherence and operation duration.

If a processor has an average coherence time `T` and an operation requires `t`, an approximate sequential operation budget is:

`N ≈ T / t`

The calculation is only an engineering approximation. Real circuits contain different gate types, parallel operations, idle periods, measurement operations, control latency, and correlated noise.

The implementations still use the relationship because it gives a concrete hardware-level constraint.

For superconducting hardware, the Python model uses microsecond-scale coherence values and nanosecond-scale gate durations. The C++ implementation converts nanoseconds into microseconds before comparing execution time with coherence.

## Gate Fidelity and Error Accumulation

A gate fidelity close to one does not mean that an entire circuit has the same fidelity.

The C++, Java, and PostgreSQL implementations use an independent-error approximation:

`P(error) = 1 - (1 - p)^n`

where `p` is an average gate error rate and `n` is the number of operations.

This is an engineering approximation rather than a complete quantum noise model. Real devices can exhibit correlated errors, leakage, drift, state-preparation errors, measurement errors, crosstalk, and non-Markovian behavior.

The approximation is useful for demonstrating why increasing circuit depth can rapidly reduce practical reliability.

## Classical Control

A quantum processor depends on classical infrastructure.

A typical control loop is:

Experiment request
→ circuit validation
→ pulse scheduling
→ hardware control
→ measurement
→ digitization
→ result processing
→ experiment record

Classical control systems provide timing, waveform generation, calibration data, feedback, experiment scheduling, and measurement processing.

The JavaScript implementation emphasizes event-driven state changes. The processor emits events when it moves through states such as `warming` and `ready`.

The Java implementation makes state transitions explicit through `ProcessorState`.

The PostgreSQL implementation records experiment state changes in `experiment_event`, providing an auditable history.

## Python Implementation

The Python program provides a compact hardware simulation.

### Main domain objects

| Object | Responsibility |
|---|---|
| `Qubit` | Stores physical qubit characteristics and validates them |
| `HardwareLayer` | Groups physical and classical hardware components |
| `Gate` | Represents operation duration and error rate |
| `QuantumDevice` | Aggregates qubits, layers, and gate specifications |
| `CoolingBudget` | Evaluates thermal load against cooling capacity |
| `ControlSignal` | Represents a validated control waveform |
| `HardwareBuilder` | Creates superconducting and trapped-ion configurations |

The program validates duplicate qubit identifiers, invalid physical values, invalid fidelities, invalid cooling capacities, and invalid control signals.

It also produces a hardware report containing system-level metrics.

### Design decision

The Python implementation uses dataclasses because the hardware model consists largely of structured domain data with explicit validation.

The `QuantumDevice` class then derives aggregate metrics from those structures. This separates individual physical parameters from system-level calculations.

## JavaScript Implementation

The JavaScript program models a processor as an event-driven system.

Its major components are:

- `Qubit`
- `HardwareComponent`
- `QuantumProcessor`
- `CalibrationScheduler`
- `EventBus`

The `Map` storing qubits makes identifier-based access explicit.

The `EventBus` represents asynchronous hardware state notifications. A processor can move from `offline` to `warming` and then to `ready`, while experiment evaluation generates another event.

The calibration scheduler uses priority ordering. Higher-priority calibration tasks are processed first.

The implementation also writes an operational JSON report using Node.js filesystem APIs.

### Failure handling

Invalid identifiers, unsupported technologies, invalid physical values, invalid priorities, and attempts to execute experiments before the processor is ready produce explicit errors.

The asynchronous state transition demonstrates a practical distinction between hardware state and experiment state.

## C++17 Implementation

The C++ program is structured as a hardware engineering case study.

The `QuantumProcessor` class owns:

- qubits
- hardware subsystems
- gate specifications
- environmental measurements
- processor state

The implementation uses `std::map` for qubit indexing and STL algorithms for aggregate calculations.

### Environmental gatekeeping

The processor refuses initialization when:

- the processor is not offline
- a superconducting processor exceeds its allowed temperature
- the readout subsystem is unavailable

This models an important physical principle: software should not treat a quantum processor as available merely because a circuit exists.

### Circuit eligibility

A circuit is accepted only when:

- the processor is ready
- the circuit has positive depth
- gate definitions exist
- estimated execution time fits the coherence budget

The program also estimates cumulative gate error.

This gives the C++ implementation a systems-engineering emphasis rather than a language-feature demonstration.

## Java 17 Implementation

The Java implementation models enterprise hardware governance.

It uses records for immutable domain values:

- `Qubit`
- `HardwareSubsystem`
- `GateProfile`
- `EnvironmentalState`
- `ExperimentRequest`
- `ExperimentDecision`

The `HardwarePolicy` interface separates hardware policy from processor implementation.

`DefaultHardwarePolicy` applies rules concerning processor readiness, circuit depth, and two-qubit-gate availability.

This separation allows policy evaluation to remain independent from the physical processor representation.

### State transitions

The processor explicitly moves through:

`OFFLINE → INITIALIZING → READY → RUNNING → READY`

A failed environmental validation transitions the processor into `FAULT`.

This is important for enterprise systems because a failed hardware initialization should not be represented as an ordinary successful state.

## PostgreSQL Implementation

The PostgreSQL model represents the hardware as a relational system.

The primary relationships are:

`processor`
→ `hardware_subsystem`
→ `subsystem_component`

and:

`processor`
→ `qubit`

`processor`
→ `gate_profile`

`processor`
→ `environment_measurement`

`processor`
→ `experiment`
→ `experiment_event`

### Constraints

Database constraints enforce:

- positive coherence time
- valid fidelity ranges
- valid gate durations
- valid error rates
- unique physical qubit indexes
- valid cooling capacity
- thermal load not exceeding cooling capacity
- valid experiment depth

A trigger also prevents a qubit from being assigned a technology different from the processor technology.

This rule is enforced in the database because it represents an integrity condition rather than merely an application preference.

### Evaluation function

`evaluate_experiment()` calculates:

- processor readiness
- average coherence
- average gate duration
- average gate error
- two-qubit-gate availability
- estimated execution time
- estimated circuit error

The function returns an explicit acceptance decision and reason.

### Views

`processor_hardware_summary` provides system-level hardware metrics.

`experiment_eligibility_report` combines stored experiment information with current eligibility calculations.

### Transactional workflow

The final transaction evaluates requested experiments and updates their states.

The `experiment_event` trigger records each state transition. This creates an auditable sequence rather than retaining only the current state.

## Physical Control and Software Control

The hardware layers can be separated into two broad classes.

| Physical layer | Software-relevant responsibility |
|---|---|
| Qubit device | Defines available quantum states |
| Cryogenic or vacuum system | Maintains physical operating conditions |
| Microwave or optical control | Applies quantum operations |
| Readout system | Converts quantum states into measurements |
| Classical controller | Provides deterministic timing and feedback |
| Calibration system | Compensates for device variation and drift |
| Experiment software | Schedules and records workloads |

This separation prevents a common conceptual error: treating the quantum chip as the entire computer.

The chip is one subsystem inside a larger cyber-physical system.

## Calibration

Quantum hardware requires repeated calibration because physical parameters change with time and operating conditions.

Examples include:

- qubit frequency calibration
- pulse amplitude calibration
- pulse duration calibration
- readout calibration
- resonator calibration
- two-qubit coupling calibration
- laser frequency calibration
- optical alignment
- trap parameter calibration

The JavaScript implementation contains a priority-based calibration scheduler. Its purpose is to show that calibration is an operational workload rather than a one-time installation step.

## Error Sources

Important hardware error sources include:

| Error source | Example effect |
|---|---|
| Decoherence | Loss of quantum information |
| Control error | Incorrect gate rotation |
| Crosstalk | An operation affects neighboring qubits |
| Leakage | Population leaves the computational subspace |
| Readout error | Incorrect classical measurement |
| Frequency drift | Control pulse becomes detuned |
| Thermal noise | Increased physical noise |
| Amplifier noise | Reduced readout quality |
| Optical instability | Reduced trapped-ion control quality |
| Vacuum degradation | Increased collision probability |

The implementations model only selected parameters. A production-grade physical simulator would require substantially richer noise and device models.

## Security and Operational Controls

Quantum hardware is a cyber-physical system, so security applies to both software and physical control.

Important controls include:

- restrict hardware-control interfaces
- authenticate experiment requests
- authorize calibration changes
- separate research workloads from maintenance operations
- protect calibration data
- validate uploaded circuit descriptions
- record state transitions
- maintain audit logs
- isolate control networks
- monitor environmental anomalies
- prevent unsafe operating configurations

The PostgreSQL state history provides an audit mechanism for experiment transitions.

The software implementations validate hardware state before executing experiments. This reduces the risk of sending a valid computational request to an unsuitable physical state.

## Performance Considerations

Hardware modeling introduces several different performance dimensions.

### Classical computation

Aggregating metrics across `n` qubits is generally `O(n)`.

Sorting calibration tasks in the JavaScript scheduler is approximately `O(k log k)` for `k` queued tasks.

Map-based qubit lookup is expected `O(log n)` in the C++ implementation and average `O(1)` in the JavaScript `Map`.

### Database queries

The PostgreSQL indexes target common access paths:

- processor-to-qubit lookup
- processor environment history
- processor experiment state
- recent experiment requests

Indexes are not placed on every column because unnecessary indexes increase storage and write overhead.

### Physical execution

Classical calculation speed does not eliminate physical execution limits. A circuit can be computationally inexpensive to describe while exceeding a device's coherence, calibration, thermal, or control constraints.

## Edge Cases

The implementations explicitly handle several failure conditions:

- duplicate qubit identifiers
- unsupported qubit technology
- invalid fidelity values
- zero or negative coherence
- invalid gate duration
- excessive thermal load
- processor not ready
- missing readout
- missing two-qubit gate capability
- circuit depth outside allowed limits
- execution time exceeding coherence budget
- invalid calibration priorities
- invalid environmental measurements

These conditions are deliberately represented as operational failures rather than silently corrected.

## Important Distinctions

### Qubit versus processor

A qubit is an individual quantum information carrier. A processor combines many qubits with coupling, control, measurement, packaging, and environmental systems.

### Gate fidelity versus readout fidelity

Gate fidelity concerns the accuracy of an operation on quantum states. Readout fidelity concerns the accuracy with which the final state is converted into classical information.

A processor can have strong gate performance and still have weak end-to-end results because of measurement errors.

### Coherence versus gate duration

Coherence describes how long useful quantum information can remain available under specified conditions. Gate duration describes how long a particular operation takes.

Circuit execution depends on their relationship, not on either value independently.

### Quantum hardware versus classical control

Quantum hardware performs the physical quantum operation. Classical hardware generates control signals, coordinates timing, processes measurements, manages calibration, and schedules experiments.

## Practical Build Sequence

A realistic high-level construction workflow is:

Requirements
→ Qubit technology selection
→ Device fabrication
→ Packaging
→ Environmental infrastructure
→ Control hardware
→ Readout hardware
→ Classical controller
→ Initial calibration
→ Characterization
→ Error measurement
→ Circuit execution
→ Continuous recalibration

Each stage introduces different engineering constraints.

Technology selection determines the environmental and control architecture. Fabrication determines device characteristics. Packaging connects the processor to external systems. Calibration converts nominal hardware into usable operating parameters.

## Limitations

The project models hardware architecture rather than performing physical quantum simulation.

It does not simulate:

- full quantum state vectors
- density matrices
- detailed Hamiltonians
- microscopic device fabrication
- electromagnetic field distributions
- realistic cryogenic thermodynamics
- complete laser propagation
- correlated noise
- leakage dynamics
- quantum error-correction decoding
- fault-tolerant logical qubits

The error formulas are intentionally simplified engineering approximations.

The hardware metrics should therefore be interpreted as system-model values rather than measurements from a physical quantum processor.

## Cross-Implementation Mapping

| Engineering concept | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Qubit model | Dataclass | Class | Struct | Record | Table |
| Processor | `QuantumDevice` | `QuantumProcessor` | `QuantumProcessor` | `QuantumProcessor` | `processor` |
| Hardware layers | `HardwareLayer` | `HardwareComponent` | `HardwareSubsystem` | `HardwareSubsystem` | Subsystem tables |
| Gate model | `Gate` | Experiment timing | `GateSpecification` | `GateProfile` | `gate_profile` |
| State | Validation | Event-driven state | Enum state | Explicit state | PostgreSQL enum |
| Calibration | Control sequence | Priority scheduler | Hardware constraints | Policy-controlled workflow | Experiment records |
| Environment | `CoolingBudget` | Processor state | `StatusMeasurement` | `EnvironmentalState` | `environment_measurement` |
| Error model | Gate fidelity | Execution evaluation | Circuit error estimate | Policy evaluation | SQL function |
| Audit | Report file | JSON report | Console workflow | Service output | `experiment_event` |

## Engineering Interpretation

The central construction principle is integration.

A quantum computer requires a chain of mutually dependent systems:

`Quantum device + environment + control + readout + classical computation + calibration`

A qubit with excellent intrinsic properties is not sufficient if the control electronics introduce excessive noise. A powerful control system is not sufficient if the processor cannot remain within its operating environment. A stable processor is not sufficient if readout is inaccurate.

The source files therefore treat quantum computing hardware as an integrated engineered system rather than as an isolated collection of qubits.
