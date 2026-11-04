# Photonic Quantum Computing: Photons as Qubits

## 1. Domain and Physical Model

Photonic quantum computing uses individual photons or optical modes to represent, manipulate, transmit, and measure quantum information.

A photon is a quantum of electromagnetic radiation. Its physical properties provide different ways to encode quantum information.

Common photonic encoding methods include:

| Encoding | Qubit representation | Physical distinction |
|---|---|---|
| Polarization | Horizontal and vertical polarization | Orientation of the electric-field polarization |
| Path | Two spatial optical modes | Which optical path contains the photon |
| Time-bin | Early and late arrival times | Temporal mode |
| Frequency-bin | Two frequency modes | Optical frequency |
| Orbital angular momentum | Two selected angular-momentum modes | Spatial phase structure |

The five implementations use polarization encoding as the principal single-qubit model. They also introduce spatial optical modes, beam splitters, and two-photon interference.

A polarization qubit is represented as:

\[
|\psi\rangle=\alpha|H\rangle+\beta|V\rangle
\]

where:

- \(|H\rangle\) represents horizontal polarization.
- \(|V\rangle\) represents vertical polarization.
- \(\alpha\) and \(\beta\) are complex probability amplitudes.

The amplitudes must satisfy:

\[
|\alpha|^2+|\beta|^2=1
\]

The measurement probabilities in the horizontal/vertical basis are:

\[
P(H)=|\alpha|^2
\]

\[
P(V)=|\beta|^2
\]

The quantum state contains amplitude and phase information. A classical probability distribution contains probabilities but does not preserve the relative phase between amplitudes.

## 2. Photon Sources and State Preparation

A photonic experiment begins with a photon source.

Important source categories include:

- Attenuated laser sources.
- Spontaneous parametric down-conversion (SPDC).
- Spontaneous four-wave mixing.
- Quantum-dot single-photon emitters.
- Other engineered single-photon sources.

SPDC uses a nonlinear optical medium in which an incident pump photon can produce correlated signal and idler photons under suitable phase-matching conditions.

A heralded single-photon source uses the detection of one photon to indicate the likely presence of its partner.

The implementations provide four polarization states.

| State | Mathematical representation | Description |
|---|---|---|
| Horizontal | \(|H\rangle\) | Horizontal polarization |
| Vertical | \(|V\rangle\) | Vertical polarization |
| Diagonal | \((|H\rangle+|V\rangle)/\sqrt{2}\) | Equal real amplitudes |
| Right-circular | \((|H\rangle+i|V\rangle)/\sqrt{2}\) | Relative phase of \(\pi/2\) |

State preparation must produce a normalized quantum state. An invalid state cannot be passed into the simulation.

The Python, JavaScript, C++17, and Java implementations validate normalization at construction time.

## 3. Quantum State Representation

### 3.1 Complex amplitudes

Quantum amplitudes are complex numbers:

\[
\alpha=a+ib
\]

\[
\beta=c+id
\]

Their squared magnitudes determine measurement probabilities:

\[
|\alpha|^2=a^2+b^2
\]

\[
|\beta|^2=c^2+d^2
\]

The phase of each amplitude is also relevant because optical transformations can cause amplitudes to interfere.

### 3.2 Bloch sphere

A pure single-qubit polarization state can be represented using a Bloch vector:

\[
x=2\operatorname{Re}(\alpha^*\beta)
\]

\[
y=2\operatorname{Im}(\alpha^*\beta)
\]

\[
z=|\alpha|^2-|\beta|^2
\]

For a normalized pure state:

\[
x^2+y^2+z^2=1
\]

The Bloch representation is useful for understanding how polarization transformations change a qubit.

A global phase does not change physical measurement predictions. A relative phase between the horizontal and vertical amplitudes can change measurement outcomes in another polarization basis.

## 4. Optical Transformations and Quantum Gates

Optical components transform photon states.

The Jones-vector representation of a polarization qubit is:

\[
|\psi\rangle=
\begin{bmatrix}
\alpha\\
\beta
\end{bmatrix}
\]

An ideal polarization transformation is represented by a unitary matrix:

\[
|\psi'\rangle=U|\psi\rangle
\]

For a unitary transformation:

\[
U^\dagger U=I
\]

This preserves the norm of the state.

### 4.1 Pauli-X

\[
X=
\begin{bmatrix}
0&1\\
1&0
\end{bmatrix}
\]

The transformation exchanges horizontal and vertical polarization:

\[
X|H\rangle=|V\rangle
\]

\[
X|V\rangle=|H\rangle
\]

### 4.2 Pauli-Z

\[
Z=
\begin{bmatrix}
1&0\\
0&-1
\end{bmatrix}
\]

This transformation introduces a relative phase of \(\pi\).

\[
Z(\alpha|H\rangle+\beta|V\rangle)
=
\alpha|H\rangle-\beta|V\rangle
\]

### 4.3 Hadamard transformation

\[
H=\frac{1}{\sqrt{2}}
\begin{bmatrix}
1&1\\
1&-1
\end{bmatrix}
\]

Applied to horizontal polarization:

\[
H|H\rangle=
\frac{|H\rangle+|V\rangle}{\sqrt{2}}
\]

The output is an equal superposition.

### 4.4 Phase shifter

A relative phase shift can be represented as:

\[
P(\phi)=
\begin{bmatrix}
1&0\\
0&e^{i\phi}
\end{bmatrix}
\]

Its effect is:

\[
P(\phi)|\psi\rangle=
\alpha|H\rangle+
\beta e^{i\phi}|V\rangle
\]

The phase shift changes relative phase without changing the individual basis-state probabilities immediately.

It can change the probability distribution after a subsequent basis transformation.

### 4.5 Wave plates

A wave plate introduces a controlled phase difference between two orthogonal polarization components.

A quarter-wave plate ideally introduces a relative phase of \(\pi/2\) between its principal axes.

A half-wave plate ideally introduces a relative phase of \(\pi\).

The optical axis orientation determines the resulting polarization transformation.

The Python implementation includes a rotated quarter-wave-plate Jones matrix.

The other implementations focus on unitary circuit transformations and phase operations.

## 5. Photon Measurement

Measurement converts quantum information into a classical observation.

For horizontal/vertical polarization measurement:

\[
P(H)=|\alpha|^2
\]

\[
P(V)=|\beta|^2
\]

A measurement returns one outcome rather than both amplitudes.

For example, an ideal diagonal photon has:

\[
P(H)=0.5
\]

\[
P(V)=0.5
\]

Repeated measurements produce a statistical distribution.

For \(N\) independent measurements:

\[
\hat P(H)=\frac{N_H}{N}
\]

\[
\hat P(V)=\frac{N_V}{N}
\]

As the number of measurements increases, the observed frequencies tend to approach their theoretical probabilities.

The simulations use seeded pseudorandom generators to make experiments reproducible.

The random generators are suitable for educational simulations, not for physical quantum randomness or cryptographic key generation.

## 6. Optical Paths and Beam Splitters

A beam splitter is an optical component that distributes an incoming optical mode across output modes.

For a lossless beam splitter, one common unitary convention is:

\[
U_{BS}=
\begin{bmatrix}
\sqrt R&i\sqrt T\\
i\sqrt T&\sqrt R
\end{bmatrix}
\]

where:

\[
R+T=1
\]

Here:

- \(R\) is the reflectivity.
- \(T\) is the transmissivity.

For a balanced beam splitter:

\[
R=T=0.5
\]

The output amplitudes must be considered together with their relative phases.

The phase factor \(i\) represents a phase change associated with reflection under the selected convention.

Different beam-splitter conventions may place phase factors on different matrix elements. Physical predictions remain consistent when the convention is used consistently.

The implementations validate that the total output probability of an ideal single-photon beam splitter equals one.

A realistic beam splitter may also introduce absorption, imperfect mode matching, polarization dependence, and fabrication errors.

## 7. Hong-Ou-Mandel Interference

Hong-Ou-Mandel (HOM) interference is a two-photon quantum interference phenomenon.

Two photons enter opposite input ports of a beam splitter.

When they are indistinguishable in their relevant degrees of freedom and arrive with sufficient temporal overlap, their probability amplitudes interfere.

For a balanced beam splitter, ideal indistinguishable photons leave together through the same output port.

This is known as photon bunching.

The probability of detecting one photon in each output port is the coincidence probability.

For the idealized model implemented here:

\[
P_{\text{coincidence}}
=
4R(1-R)(1-\mu)
\]

where:

- \(R\) is the beam-splitter reflectivity.
- \(\mu\) is an effective indistinguishability parameter.
- \(0\leq\mu\leq1\).

For a balanced beam splitter:

\[
P_{\text{coincidence}}=1-\mu
\]

| Indistinguishability | Ideal coincidence probability |
|---|---:|
| 0 | 1.0 |
| 0.5 | 0.5 |
| 1 | 0.0 |

The complementary probability in this simplified model is:

\[
P_{\text{bunching}}=1-P_{\text{coincidence}}
\]

HOM interference is important in photonic quantum computing because two-photon interference is used in linear-optical quantum information processing.

The equation is an idealized model. Real experiments require consideration of spectral bandwidth, temporal delay, polarization mismatch, detector timing resolution, multiphoton contamination, and optical losses.

## 8. Optical Loss and Detector Efficiency

Photonic quantum systems are particularly sensitive to loss.

Photons can be lost during:

- Generation.
- Coupling into optical fibers.
- Propagation through waveguides.
- Optical-component transmission.
- Switching.
- Detection.

Transmission probability and detector efficiency are distinct quantities.

Let:

\[
\eta_t=\text{channel transmission}
\]

\[
\eta_d=\text{detector efficiency}
\]

The combined probability of successful detection in the simplified model is:

\[
P_{\text{detection}}=\eta_t\eta_d
\]

The probability of loss is:

\[
P_{\text{loss}}=1-\eta_t\eta_d
\]

For example:

\[
\eta_t=0.85
\]

\[
\eta_d=0.90
\]

Therefore:

\[
P_{\text{detection}}=0.765
\]

\[
P_{\text{loss}}=0.235
\]

The implementations separately record generated, detected, and lost photons.

This separation is important because a missing detection is not equivalent to a horizontal or vertical measurement result.

### 8.1 Dark counts

A real detector may produce a detection event without a corresponding signal photon.

These events are called dark counts.

The PostgreSQL model includes a dark-count-rate field for detector-channel characterization.

The basic simulation does not generate dark-count events. A realistic experiment simulator must model dark counts separately from successful photon detection.

### 8.2 Detector limitations

Practical detector characteristics include:

- Detection efficiency.
- Dark-count rate.
- Timing jitter.
- Dead time.
- Photon-number resolution.
- Afterpulsing.

The simplified implementations do not claim to model all these effects.

## 9. Photonic Quantum Computing Architectures

Photonic quantum computing is not restricted to one encoding or optical architecture.

### 9.1 Discrete-variable photonic computing

Discrete-variable systems encode quantum information in distinguishable optical modes.

Examples include:

- Polarization.
- Spatial paths.
- Time bins.
- Frequency bins.

A single photon can represent a qubit using two orthogonal modes.

### 9.2 Continuous-variable photonic computing

Continuous-variable systems use optical field quadratures.

The relevant observables are commonly represented by position-like and momentum-like quadratures:

\[
\hat x
\]

\[
\hat p
\]

These systems use optical states such as coherent states, squeezed states, and other engineered quantum states.

They are mathematically different from the two-level polarization-qubit model implemented in the source files.

### 9.3 Linear-optical quantum computing

Linear-optical quantum computing uses components such as:

- Beam splitters.
- Phase shifters.
- Polarization rotations.
- Photon sources.
- Single-photon detectors.
- Photon-number-resolving detectors.

Single-qubit transformations can be implemented using linear optical elements.

Two-photon interference provides important mechanisms for multi-photon operations.

Linear optics alone does not provide arbitrary deterministic two-qubit gates between independently encoded photonic qubits. Suitable nonlinear interactions, ancillary photons, measurement, and feed-forward can be required depending on the architecture.

## 10. Entanglement and Multi-Photon Systems

Entanglement is a central resource in photonic quantum computing.

For two polarization qubits, an example Bell state is:

\[
|\Phi^+\rangle=
\frac{
|HH\rangle+|VV\rangle
}{\sqrt{2}}
\]

This state cannot be expressed as a product of two independent single-photon polarization states.

Entangled photons are used in:

- Quantum teleportation.
- Quantum communication.
- Quantum key distribution.
- Entanglement swapping.
- Distributed quantum computing.
- Photonic quantum information processing.

The five source implementations concentrate on single-photon polarization states and idealized two-photon interference.

They do not implement a general multi-qubit state-vector or density-matrix simulator. Their HOM model is a separate probability model rather than a full entangled-state circuit engine.

## 11. Python Implementation

The Python file uses object-oriented modeling and standard-library facilities.

### Main components

| Class | Responsibility |
|---|---|
| `PhotonState` | Stores normalized complex polarization amplitudes |
| `PhotonSource` | Creates standard polarization states |
| `OpticalGates` | Applies unitary transformations |
| `PolarizationAnalyzer` | Samples measurement outcomes |
| `OpticalChannel` | Models transmission and detector efficiency |
| `BeamSplitter` | Calculates output-mode amplitudes |
| `HongOuMandelExperiment` | Calculates two-photon interference probabilities |
| `PhotonicExperiment` | Executes repeated experiments |
| `ExperimentReport` | Stores measurement and loss statistics |

### Engineering decisions

- Frozen dataclasses prevent accidental modification of state objects.
- Enumerations represent discrete polarization outcomes.
- Explicit exceptions distinguish invalid states and measurement errors.
- A seeded random generator enables reproducible experiments.
- Assertions validate normalization, photon accounting, and interference behavior.

The script has no external package dependencies.

## 12. JavaScript Implementation

The JavaScript implementation uses an event-driven architecture.

Its main components are:

| Class | Responsibility |
|---|---|
| `PolarizationQubit` | Immutable complex-amplitude state |
| `OpticalCircuit` | Ordered transformation sequence |
| `RandomGenerator` | Reproducible pseudorandom sampling |
| `PolarizationMeasurement` | Measurement and sampling |
| `OpticalChannel` | Loss model |
| `PhotonDetector` | Asynchronous detection events |
| `BeamSplitter` | Optical-mode transformation |
| `ExperimentManager` | Experiment orchestration |

The detector extends Node.js `EventEmitter`.

It emits separate events for successful detection and photon loss.

This provides a useful distinction between physical measurement outcomes and unsuccessful detection events.

The experiment manager aggregates the emitted events into a report.

The implementation uses native JavaScript complex-number helper functions because JavaScript does not have a built-in complex-number primitive.

The code uses Node.js standard-library modules and does not require npm dependencies.

## 13. C++17 Implementation

The C++ implementation uses strongly typed domain objects and standard-library containers.

| Component | Responsibility |
|---|---|
| `PhotonState` | Normalized qubit representation |
| `QuantumGate` | Matrix-based state transformations |
| `PhotonicCircuit` | Ordered gate execution |
| `PolarizationAnalyzer` | Measurement sampling |
| `OpticalChannel` | Detection probability |
| `BeamSplitter` | Spatial-mode amplitude calculation |
| `HongOuMandelExperiment` | Interference evaluation |
| `PhotonicExperiment` | Repeated experimental execution |

The program uses:

- `std::complex<double>` for amplitudes.
- `std::array` for fixed-size matrices.
- `std::vector` for circuit operations.
- `std::mt19937_64` for reproducible sampling.
- Exceptions for invalid configurations.

Fixed-size two-dimensional matrices avoid dynamic allocation for the basic polarization transformations.

The computational cost of a single-qubit gate is constant:

\[
O(1)
\]

For \(G\) gates, circuit execution is:

\[
O(G)
\]

For \(N\) simulated measurement shots:

\[
O(N)
\]

The implementation is a compact engineering simulation rather than a general-purpose photonic quantum simulator.

## 14. Java 17 Enterprise Implementation

The Java implementation emphasizes domain modeling, immutable records, interfaces, and validation.

### Main domain types

- `Complex`
- `PhotonState`
- `MeasurementResult`
- `OpticalChannel`
- `BeamSplitterOutput`
- `InterferenceResult`

### Service components

- `PhotonSource`
- `PolarizedPhotonSource`
- `QuantumGate`
- `OpticalCircuit`
- `PhotonMeasurement`
- `ExperimentService`
- `ExperimentReport`

### State management

The implementation separates:

1. Source configuration.
2. State preparation.
3. Circuit execution.
4. Channel transmission.
5. Detection.
6. Measurement.
7. Statistical reporting.

This separation supports clearer validation boundaries.

The `QuantumGate` constructor verifies that a supplied 2 × 2 transformation is unitary.

The `ExperimentReport` constructor verifies that detected and lost photon counts account for every shot.

Immutable records prevent callers from modifying the basic state representation after construction.

The implementation uses Java 17 records, switch expressions, streams, and immutable collection operations.

## 15. PostgreSQL Data Model

The PostgreSQL implementation provides a relational model for managing photonic experiments.

### Entity relationships

The principal relationship is:

Photon Sources
    |
    v
Experiments
    |
    +---- Experiment Components
    |
    +---- Optical Channels
    |
    +---- Experimental Runs
              |
              +---- Photon Events
              |        |
              |        +---- Polarization Measurements
              |
              +---- Interference Measurements

Experiments
    |
    +---- Experiment Audit

### Database entities

| Table | Purpose |
|---|---|
| `photon_sources` | Source type, wavelength, bandwidth, and repetition rate |
| `optical_components` | Optical component properties and calibration |
| `experiments` | Experimental configuration and initial quantum state |
| `experiment_components` | Ordered optical circuit components |
| `optical_channels` | Channel transmission and detector efficiency |
| `experiment_channels` | Channel assignment to experiments |
| `experimental_runs` | Repeated execution records |
| `photon_events` | Individual photon lifecycle |
| `polarization_measurements` | Recorded polarization outcomes |
| `interference_measurements` | HOM coincidence and bunching statistics |
| `experiment_audit` | Experiment state-change history |

### Integrity controls

The database enforces:

- Unique experiment names are not required, allowing repeatable experimental naming.
- Unique source names.
- Positive wavelengths.
- Valid reflectivity and transmission values.
- Normalized quantum states.
- Positive shot counts.
- Valid photon accounting.
- Valid experiment state transitions.
- Valid photon state transitions.
- Detector association for detected photons.
- Measurement records only for detected photons.

### Experiment state machine

The experiment lifecycle is:

CREATED
   |
   v
VALIDATED
   |
   v
RUNNING
   |
   +----> COMPLETED
   |
   +----> FAILED
   |
   +----> CANCELLED

A newly created experiment must pass source and component calibration checks before validation.

The database triggers reject invalid state transitions.

### Photon state machine

GENERATED
   |
   +----> LOST
   |
   v
TRANSMITTED
   |
   +----> LOST
   |
   v
DETECTED
   |
   v
POLARIZATION MEASUREMENT

A lost photon cannot be recorded as a successful polarization measurement.

### Analytical queries

The database includes:

- Source and experiment retrieval.
- Calibration eligibility determination.
- Polarization measurement aggregation.
- Photon-loss reporting.
- Detection-rate calculation.
- Hong-Ou-Mandel theoretical prediction.
- Ordered circuit-component retrieval.
- CTE-based experiment reporting.
- Quantum-state validation.
- Audit-history retrieval.

The SQL script includes sample records for successful experiments and an intentionally uncalibrated optical component.

The ineligible experiment remains unvalidated.

## 16. Experimental Validation and Reproducibility

A photonic quantum experiment should distinguish theoretical predictions from measured results.

A practical experiment record should preserve:

- Source identification.
- Photon wavelength.
- Optical bandwidth.
- Circuit configuration.
- Optical-component calibration.
- Channel characteristics.
- Detector configuration.
- Measurement basis.
- Number of shots.
- Randomization or experimental configuration identifiers.
- Detection count.
- Loss count.
- Measurement outcomes.
- Experimental timestamps.

A reproducible software simulation also requires a known pseudorandom seed.

A physical experiment requires additional calibration records, equipment metadata, environmental measurements, and acquisition-system configuration.

### Statistical uncertainty

For an observed binary outcome with probability \(p\), the approximate standard error of its measured frequency after \(N\) independent trials is:

\[
SE(\hat p)=
\sqrt{\frac{p(1-p)}{N}}
\]

The maximum standard error occurs at \(p=0.5\):

\[
SE_{\max}=\frac{1}{2\sqrt N}
\]

For 10,000 independent trials:

\[
SE_{\max}=0.005
\]

This describes sampling uncertainty only. It does not account for systematic experimental errors.

## 17. Security and Operational Considerations

Photonic quantum systems require both physical and information-security controls.

### Equipment and configuration integrity

- Restrict access to experimental configuration.
- Preserve component calibration history.
- Record source and detector identifiers.
- Protect measurement datasets against unauthorized modification.
- Separate experiment execution permissions from reporting permissions.
- Maintain auditable state transitions.
- Validate experimental input parameters before execution.

### Data integrity

Measurement datasets should preserve raw detection events wherever possible.

Aggregated statistics should not replace the underlying records when detailed experimental verification is required.

Database permissions should follow least-privilege principles.

The SQL schema provides structural integrity and audit events, but production deployments must separately configure database roles, access control, backup policies, encryption, and operational monitoring.

### Quantum-security distinction

Photonic quantum computing and quantum cryptography are related but distinct fields.

Photonic quantum computing uses photons to process quantum information.

Quantum key distribution uses quantum states and measurement properties to establish cryptographic keys under specified security assumptions.

A photonic simulation does not automatically establish cryptographic security.

## 18. Limitations of the Implementations

The five implementations intentionally use a simplified physical model.

| Area | Implemented | Not fully modeled |
|---|---|---|
| Polarization | Two complex amplitudes | Full polarization tomography |
| Quantum gates | Ideal unitary transformations | Component imperfections |
| Phase shifts | Relative phase transformations | Phase drift and instability |
| Beam splitters | Ideal two-mode amplitudes | Absorption and mode-dependent imperfections |
| Measurement | Projective sampling | Detector timing and dark-count dynamics |
| Optical loss | Independent transmission and detection probabilities | Detailed propagation and loss mechanisms |
| HOM interference | Idealized coincidence formula | Full spectral and temporal wave-packet integration |
| Entanglement | Conceptual explanation | General multi-photon state simulation |
| Sources | Standard state preparation | Detailed SPDC and emitter physics |
| Detection | Binary detection outcomes | Photon-number resolution and detector dead time |

The single-photon polarization model is not sufficient to simulate every photonic quantum computing architecture.

A full physical simulation may require:

- Density matrices.
- Multi-photon Fock states.
- Creation and annihilation operators.
- Tensor-product Hilbert spaces.
- Bosonic mode transformations.
- Partial distinguishability.
- Detector POVMs.
- Optical loss channels.
- Feed-forward operations.
- Entangled-state generation.
- Multi-photon interference.

## 19. Execution and Technical Requirements

| Deliverable | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Node.js standard library |
| C++17 | C++17 compiler | Standard library |
| Java | Java 17 | Java standard library |
| PostgreSQL | PostgreSQL 15+ | PostgreSQL database |

### Execution commands

Python: `python photonic_quantum_computing.py`

JavaScript: `node photonic_quantum_computing.js`

C++17: `g++ -std=c++17 -O2 photonic_quantum_computing.cpp -o photonic_quantum_computing`

Java: `javac PhotonicQuantumComputing.java`

Java execution: `java PhotonicQuantumComputing`

PostgreSQL: execute the SQL file using a PostgreSQL client with permission to create schemas, tables, functions, procedures, and triggers.

The SQL script creates its own `photonics` schema and wraps its database changes in a transaction.

## 20. Core Technical Distinctions

| Concept | Meaning |
|---|---|
| Photon | Quantum of electromagnetic radiation |
| Qubit | Two-level quantum information system |
| Polarization encoding | Representation using orthogonal polarization modes |
| Complex amplitude | Probability amplitude containing magnitude and phase |
| Superposition | Coherent combination of quantum basis states |
| Unitary gate | Norm-preserving quantum transformation |
| Phase shifter | Optical component controlling relative phase |
| Wave plate | Optical component transforming polarization |
| Beam splitter | Optical element coupling spatial modes |
| Photon bunching | Two indistinguishable photons preferentially leaving through the same output |
| HOM interference | Two-photon interference at a beam splitter |
| Photon loss | Failure of a photon to reach successful detection |
| Detector efficiency | Probability of registering an incident photon |
| Entanglement | Nonseparable joint quantum state |
| Linear optics | Optical transformations based on linear interactions with optical modes |

The central engineering principle is that a photonic quantum system must preserve the distinction between quantum-state preparation, coherent optical evolution, probabilistic measurement, physical photon loss, and experimental data collection.```
