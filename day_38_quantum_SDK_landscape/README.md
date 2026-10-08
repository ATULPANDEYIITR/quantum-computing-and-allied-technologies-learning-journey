# Quantum SDK Landscape: Qiskit, Cirq, PennyLane and Others

## Scope

Quantum software development is no longer represented by a single universal SDK. The modern landscape contains several overlapping but technically different layers: circuit construction, hardware-aware compilation, differentiable quantum programming, managed cloud execution, accelerated simulation, quantum programming languages, and resource estimation.

The principal SDK families examined here are:

| SDK or platform | Primary organization | Primary development model | Strongest architectural role |
|---|---|---|---|
| Qiskit | IBM | Python | General circuit development, transpilation, IBM quantum workflows |
| Cirq | Google Quantum AI | Python | Explicit circuit construction and hardware-oriented research |
| PennyLane | Xanadu | Python | Differentiable quantum programming, QML, variational algorithms |
| pytket / TKET | Quantinuum | Python API with C++ compiler technology | Compilation, routing, placement, optimization, interoperability |
| Amazon Braket SDK | AWS | Python | Managed cloud access to multiple quantum providers and simulators |
| CUDA-Q | NVIDIA | C++ and Python | Hybrid CPU/GPU/QPU programming and accelerated simulation |
| Microsoft QDK / Q# | Microsoft | Q# and Python | Quantum language development, simulation, resource estimation, Azure Quantum |

These systems should not be compared only by the number of gates they can express. Their most important differences occur at the abstraction level where they expect the developer to work.

## The Central Architectural Distinction

A quantum SDK normally sits between a high-level algorithm and an execution environment.

A simplified workflow is:

`algorithm -> circuit or quantum function -> compilation -> backend execution -> measurement/result`

The exact location of an SDK in this workflow determines its role.

Qiskit is strongly associated with circuit construction, transpilation, quantum information tooling, and IBM hardware execution. Cirq emphasizes explicit circuit and moment representations and is particularly useful when researchers need detailed control of circuit structure.

PennyLane changes the abstraction more substantially. A quantum computation can be treated as a differentiable function, allowing quantum circuits to participate in classical optimization and machine-learning workflows. This makes differentiation a central design concern rather than a secondary utility.

pytket/TKET is more compiler-centric. Its value appears when a logical circuit needs to become an efficient circuit for a particular device architecture. Placement, routing, gate decomposition, and optimization become first-class concerns.

Amazon Braket is primarily an execution and cloud-orchestration layer. The developer can construct workloads and submit quantum tasks or hybrid jobs through AWS infrastructure while targeting different supported devices and simulators.

CUDA-Q emphasizes hybrid classical and quantum computation, with strong attention to accelerated simulation and CPU/GPU/QPU workflows.

Microsoft's Quantum Development Kit and Q# provide a distinct language-oriented model. Resource estimation and quantum-program development are important parts of the platform, while Python and Azure Quantum provide additional integration paths.

## Quantum Circuits Are Not the Whole SDK

A circuit is a logical description of quantum operations. It does not automatically describe how those operations should be realized on a particular QPU.

A logical circuit might contain:

`H(q0)`

followed by:

`CX(q0, q4)`

A hardware device may not permit a direct interaction between `q0` and `q4`. The compiler must account for the device's coupling graph and may need to insert routing operations or choose a different physical placement.

This distinction explains why compiler-oriented systems such as TKET are important even when another SDK is used to construct the original circuit.

## Qiskit

Qiskit is a general-purpose quantum software framework with a strong circuit and transpilation model.

The Python implementation models Qiskit as a circuit-oriented SDK with explicit compilation and hardware access. The example Bell circuit contains an `H` gate followed by a two-qubit controlled operation. The program then measures circuit depth and two-qubit-gate count rather than pretending that the circuit representation itself is a complete execution environment.

A major Qiskit architectural concept is the primitive abstraction. Sampler-style workflows are centered on obtaining samples from circuit execution, while Estimator-style workflows focus on expectation values of observables. IBM's current documentation also distinguishes the client-side primitive interfaces from the historical V2 naming and documents an Executor interface for lower-level control.

The practical consequence is that Qiskit applications should distinguish:

- logical circuit construction
- transpilation
- backend selection
- primitive execution
- result interpretation

Those stages are related but are not interchangeable.

The current IBM Quantum Compute ecosystem also means that developers should verify package versions and provider-client compatibility rather than assuming that code written for an older Qiskit generation will remain unchanged.

## Cirq

Cirq is designed around explicit quantum circuit construction and provides a particularly useful model for research where the details of qubits, operations, moments, and circuit structure matter.

A moment-oriented representation is useful when temporal organization is itself important. Rather than viewing a circuit merely as a flat sequence of gates, operations can be organized according to execution moments.

This style is valuable for hardware-oriented experimentation because timing, qubit identity, operation placement, and circuit structure often affect the physical implementation.

Cirq should therefore not be treated simply as another spelling of a generic `QuantumCircuit` abstraction. Its design emphasizes explicit circuit structure and research control.

## PennyLane

PennyLane's defining distinction is differentiable quantum programming.

In a variational algorithm, a circuit can contain parameters such as:

`theta`

and produce an expectation value:

`f(theta)`

A classical optimizer can then update `theta` based on a gradient or another optimization rule.

The important architectural transition is:

`circuit -> measurement`

becoming conceptually:

`parameterized quantum function -> differentiable computational function`

This is particularly important for:

- quantum machine learning
- variational quantum eigensolvers
- quantum neural networks
- hybrid optimization
- parameterized quantum circuits

Gradient computation is not free. Depending on the device and differentiation method, evaluating gradients can require additional circuit executions. Hardware noise, finite shots, barren plateaus, parameter-shift rules, and optimizer behavior therefore become engineering concerns.

PennyLane also provides interfaces to classical numerical and machine-learning ecosystems and can target different quantum devices. That flexibility is useful, but portability does not mean every backend exposes identical capabilities.

## pytket and TKET

TKET is primarily a quantum compiler and circuit-optimization technology.

Its central problem is:

`How can a logical circuit be transformed into an efficient executable circuit for a constrained target architecture?`

Compilation can involve:

- gate-set conversion
- qubit placement
- routing
- decomposition
- circuit simplification
- architecture constraints
- optimization of the resulting implementation

This is particularly important on noisy quantum hardware because a logically equivalent circuit can have very different physical quality.

Additional gates increase opportunities for error. Poor routing can therefore reduce useful circuit fidelity even when the logical algorithm is mathematically correct.

pytket exposes TKET functionality through a Python interface and provides extension packages for interoperability with other quantum software systems. It can therefore operate as a layer between an application-oriented SDK and a hardware backend.

The C++ case study in this collection models this concern directly through a hardware topology. A circuit containing a non-native two-qubit interaction is identified as requiring compilation or routing.

## Amazon Braket SDK

Amazon Braket approaches the problem from a managed cloud perspective.

Instead of treating a single hardware vendor as the center of the development model, Braket provides a cloud environment through which quantum tasks, simulators, and hybrid jobs can be managed.

This creates a different engineering boundary.

A local circuit program may be conceptually simple:

`construct -> execute -> measure`

A managed cloud workflow also requires:

`authentication -> region -> device selection -> scheduling -> execution -> result storage/monitoring`

Amazon Braket Hybrid Jobs are particularly relevant for iterative algorithms where classical computation and quantum execution interact repeatedly. AWS documentation describes a workflow in which classical resources are provisioned for the hybrid computation and quantum tasks are executed against the selected device or simulator.

Cloud execution therefore introduces concerns that are not visible in a local circuit representation:

- account permissions
- region availability
- device availability
- queueing
- execution cost
- classical compute configuration
- result persistence
- provider-specific capabilities

## CUDA-Q

CUDA-Q addresses hybrid quantum-classical workloads with an emphasis on high-performance classical infrastructure.

Its backend model includes CPU simulators, GPU-accelerated simulators, tensor-network approaches, and hardware targets. This makes it particularly relevant when classical simulation or hybrid computation is itself a performance bottleneck.

A quantum algorithm is not necessarily dominated by the QPU. Many workflows spend substantial time on:

- state simulation
- tensor contractions
- parameter optimization
- classical preprocessing
- post-processing
- repeated circuit evaluation

GPU acceleration can therefore change the practical feasibility of a simulation workload.

CUDA-Q's C++ and Python support also makes it useful when a research or production environment needs stronger integration with high-performance classical software.

## Microsoft QDK and Q#

Microsoft's quantum development ecosystem provides a different abstraction through Q#, a dedicated quantum programming language, together with Python tooling, simulators, resource-estimation capabilities, and Azure Quantum integration.

A dedicated language can express quantum operations independently of a particular physical qubit layout. The compiler and runtime can then participate in mapping and execution.

Resource estimation is especially important when the question is not:

`Can this small circuit run today?`

but instead:

`What resources would this algorithm require on a fault-tolerant quantum computer?`

That requires a different analysis model involving logical operations, error-correction assumptions, physical resources, and execution-time estimates.

The current Microsoft QDK also supports Q# and OpenQASM development through its tooling and provides Python integration for broader workflows.

## SDK Selection Should Be Workload-Driven

A useful selection model is to begin with the actual computational requirement.

| Requirement | Strong candidates | Why |
|---|---|---|
| General circuit development | Qiskit, Cirq | Rich circuit abstractions and simulation |
| IBM hardware execution | Qiskit | Direct IBM ecosystem alignment |
| Google-oriented circuit research | Cirq | Explicit circuit and hardware-oriented model |
| Quantum machine learning | PennyLane | Differentiable quantum programming |
| Variational optimization | PennyLane, Qiskit | Strong parameterized and expectation-value workflows |
| Hardware-aware compilation | pytket/TKET, Qiskit | Compilation, routing, optimization |
| Multi-provider cloud execution | Amazon Braket | Managed cloud execution model |
| GPU-heavy simulation | CUDA-Q, PennyLane Lightning ecosystem | Accelerated simulation paths |
| Hybrid CPU/GPU/QPU workloads | CUDA-Q | Explicit hybrid computing architecture |
| Resource estimation | Microsoft QDK/Q# | Dedicated resource-estimation tooling |
| Cross-framework compilation | pytket/TKET | Interoperability and transformation layer |

The table is a decision aid, not a benchmark. A real architecture should also evaluate target hardware, supported gates, compiler quality, runtime behavior, pricing, queue characteristics, licensing, community maturity, package versions, and reproducibility.

## Compilation Is a Distinct Layer

The logical circuit and the physical circuit should be treated as different artifacts.

A logical algorithm may use:

`CX(q0, q4)`

while a hardware topology may allow only neighboring interactions.

The compiler must then solve a constrained graph-mapping problem.

This can introduce:

- SWAP operations
- additional two-qubit gates
- changes in depth
- altered scheduling
- gate decomposition
- physical-qubit remapping

The cost of compilation is therefore not merely computational time spent by the compiler. The compiler's output can change the quality of the quantum computation itself.

This is one reason TKET and Qiskit's transpilation system occupy an important position in the SDK landscape.

## Interoperability

Quantum software is increasingly heterogeneous.

A research workflow might use:

`PennyLane -> Qiskit backend`

or:

`Qiskit circuit -> pytket compilation -> hardware backend`

or:

`Python application -> Amazon Braket -> simulator/QPU`

Microsoft's current QDK documentation also supports submitting Q#, OpenQASM, Qiskit, Cirq, and PennyLane workloads through Azure Quantum workflows.

Interoperability should nevertheless be interpreted carefully.

A successful circuit translation does not guarantee preservation of every semantic feature. Potential losses include:

- provider-specific instructions
- pulse-level information
- dynamic-circuit features
- measurement semantics
- custom calibration data
- backend-specific optimization opportunities
- noise-model assumptions

An intermediate representation is useful only when the semantics needed by the application can be represented faithfully.

## Python Implementation

The Python implementation is intentionally dependency-free.

Its central structures are:

- `SDK`, which represents an SDK profile and its architectural capabilities
- `Circuit`, which provides a small logical circuit representation
- `Workload`, which expresses an application's technical requirements
- `score_sdk()`, which performs transparent workload-to-SDK matching

The circuit model supports validation of qubit references, duplicate targets, depth calculation, two-qubit gate counting, and parameter counting.

The Bell-state simulator is deliberately narrow. It handles one known circuit pattern rather than pretending to be a full quantum simulator. Unsupported circuits raise an explicit error.

That design demonstrates an important engineering principle: an educational abstraction should fail clearly when its implemented semantic scope has been exceeded.

The recommendation engine is also deliberately heuristic. It does not claim that a numerical score is a universal benchmark. Its purpose is to expose why a workload maps more naturally to one architectural family than another.

## JavaScript Implementation

The JavaScript implementation uses Node.js's built-in `EventEmitter`.

This provides an event-driven representation of execution states:

`created -> queued -> running -> completed`

The event model is relevant because cloud and hardware execution are asynchronous operations. A production application should not assume that a submission immediately produces a result.

The JavaScript circuit model also differs from the Python implementation. It emphasizes mutable object construction, asynchronous execution, event listeners, and promise-based control flow.

The execution object emits lifecycle events and returns a promise. This models an important practical distinction between local circuit construction and remote execution.

## C++ Case Study

The C++ program models an SDK selection engine for an organization deciding which software layer should own a workload.

The `SDKProfile` structure captures capabilities such as:

- compiler orientation
- hardware access
- simulator support
- cloud orchestration
- differentiable programming
- supported workload classes

The `Workload` structure represents application requirements.

The selection engine then calculates an explainable score instead of using an opaque ranking.

The most technically important part is `HardwareAwareAnalyzer`.

It models a device as a connectivity graph. A logical two-qubit gate is valid only when its pair of qubits is directly connected by the topology.

This demonstrates the difference between:

`logical correctness`

and:

`hardware executability`

A production compiler would go beyond detection and perform placement, routing, decomposition, and optimization. The case study intentionally isolates the architectural decision that causes those compiler operations to be necessary.

## Java Implementation

The Java implementation uses records, enums, immutable collections, explicit domain classes, and a repository-style service.

`SdkProfile` represents an immutable SDK capability profile.

`WorkloadRequest` represents a business or research requirement.

`Recommendation` preserves both the score and the reason for the score, which is useful in enterprise environments where a technology decision needs to remain explainable.

`QuantumCircuit` represents the logical circuit and enforces qubit-index validation before a gate enters the model.

Java's type system is useful here because workload categories are represented by the `Workload` enum rather than unconstrained strings.

The `Repository` class centralizes the SDK catalog and recommendation logic. This separates domain data from the command-line demonstration.

The implementation also deliberately distinguishes structural validation from provider execution. A structurally valid circuit may still fail later because a backend lacks a required gate, topology, execution mode, dynamic-circuit feature, or quota.

## SQL Data Model

The PostgreSQL implementation models the landscape relationally.

The core entities are:

` sdk `

Stores the architectural capabilities of each SDK.

` sdk_strength `

Stores multiple strengths without embedding repeated text in the SDK row.

` sdk_tradeoff `

Stores limitations and engineering trade-offs.

` interoperability_target `

Represents external systems and formats with which an SDK can interoperate.

` workload `

Represents application requirements such as QML, cloud execution, GPU simulation, or resource estimation.

` sdk_workload `

Stores workload-specific suitability and rationale.

` quantum_circuit `

Stores circuit-level characteristics such as qubit count, depth, and two-qubit gate count.

` backend `

Represents simulator, QPU, cloud simulator, or hybrid execution targets.

` backend_gate `

Represents gates supported by a backend.

` sdk_backend `

Connects SDKs to execution environments and records the access mode.

This schema prevents a common modeling mistake: treating an SDK, a compiler, a cloud service, a simulator, and a QPU as the same object.

## Database-Level Integrity

The schema uses PostgreSQL constraints for rules that belong at the database layer.

Examples include:

- SDK names must be unique.
- Workload suitability must remain between 0 and 100.
- Circuit qubit counts must be positive.
- Gate counts cannot be negative.
- Circuit depth cannot exceed gate count.
- A backend must have a positive qubit capacity.
- Foreign keys preserve relationships between SDKs, workloads, circuits, and backends.

The workload ranking query uses `ROW_NUMBER()` to produce a deterministic ranking for a particular requirement.

The GPU query demonstrates capability discovery by joining SDK access paths with backend characteristics.

The circuit-capacity query identifies a fundamental execution failure: a circuit requiring more qubits than the target backend provides.

## Performance Considerations

Quantum SDK performance has several layers.

Classical preprocessing may involve circuit optimization, graph mapping, simulation, parameter optimization, and data processing.

Quantum execution introduces additional costs through queue time, shots, circuit repetitions, and hardware noise.

Simulation cost can grow exponentially with the number of qubits for full state-vector simulation. Tensor-network methods can provide different scaling behavior for circuits with exploitable structure, but they are not universally efficient.

Compiler optimization can reduce physical resource consumption, but aggressive optimization can also increase compilation time or interact with backend-specific constraints.

For QML workloads, gradient evaluation can multiply the number of circuit executions. The choice of differentiation method therefore affects both runtime and cost.

## Security and Operational Considerations

Quantum SDK applications often cross local, cloud, and hardware boundaries.

Cloud execution requires protection of credentials and careful separation between source code, configuration, and authentication secrets.

API tokens should not be embedded in source files.

Production systems should also log enough metadata to reproduce an experiment without recording secrets.

Useful metadata includes:

- SDK version
- provider client version
- backend identifier
- circuit or program version
- compiler configuration
- optimization level
- shot count
- parameter values where appropriate
- execution timestamp
- result metadata
- error information

Reproducibility is particularly important because backend calibration and queue conditions can change.

## Versioning and Compatibility

Quantum SDK ecosystems evolve quickly.

The core SDK and provider-specific client are not necessarily released as one package. A stable application should therefore pin compatible versions and test upgrades against representative circuits.

Qiskit's provider ecosystem is a clear example of why this matters. IBM's current documentation distinguishes the Qiskit SDK from the IBM Quantum Compute client and documents evolving primitive interfaces.

The same principle applies to other ecosystems. A package that successfully constructs a circuit may still be incompatible with the installed provider plugin or target backend.

Compatibility should be tested at the complete workflow level rather than by checking only whether an import succeeds.

## Failure Modes

Important failure classes include:

### Logical circuit failure

The circuit contains an invalid qubit index, unsupported operation, or malformed parameter.

This should be detected before execution.

### Compilation failure

The logical circuit cannot be represented using the target backend's gate set, topology, or execution constraints.

A compiler or transpiler should expose the reason rather than silently producing a semantically different program.

### Backend capability mismatch

A selected device may not support a requested feature such as dynamic circuits, a specific gate, sufficient qubits, or a particular measurement mode.

### Cloud execution failure

Authentication, quota, region, scheduling, provider availability, or service configuration can prevent execution even when the circuit itself is valid.

### Numerical and optimization failure

Variational algorithms can suffer from poor parameter initialization, noisy gradients, barren plateaus, optimizer instability, or insufficient measurement shots.

### Simulation resource exhaustion

Increasing qubit count can make full state-vector simulation exceed available memory. GPU acceleration changes the practical limit but does not remove the underlying computational scaling.

## Choosing an SDK by Architectural Need

The most useful question is not:

`Which quantum SDK is best?`

It is:

`Which abstraction should be primary for this workload?`

A circuit-heavy hardware experiment may favor Qiskit or Cirq.

A differentiable hybrid algorithm may favor PennyLane.

A circuit that needs aggressive target-specific compilation may benefit from TKET.

A cloud application that needs managed access to several quantum providers may favor Amazon Braket.

A GPU-heavy simulation or hybrid HPC workflow may favor CUDA-Q.

A workflow centered on quantum programming language semantics and resource estimation may favor Microsoft's QDK and Q#.

These choices are not mutually exclusive. A production architecture can deliberately use several layers when their responsibilities remain clear.

## Practical Architecture

A mature quantum software stack can separate responsibilities as follows:

`Application`

handles domain logic, data, optimization objectives, and experiment configuration.

`Quantum algorithm layer`

defines the mathematical algorithm and parameterized circuit or quantum function.

`SDK layer`

provides circuit construction, differentiation, language abstractions, or algorithm primitives.

`Compilation layer`

maps the logical representation to a target instruction set and topology.

`Execution layer`

submits workloads to simulators or QPUs.

`Classical processing layer`

handles optimization, aggregation, statistical analysis, and experiment management.

This separation reduces vendor lock-in and makes it easier to change execution targets without rewriting the entire algorithm.

## Key Technical Distinctions

| Concept | Primary question |
|---|---|
| Circuit SDK | How should the quantum computation be represented? |
| Differentiable SDK | How can a quantum computation participate in classical optimization? |
| Compiler | How can the logical circuit become efficient and executable on a target architecture? |
| Cloud SDK | How should quantum workloads be submitted, scheduled, and managed remotely? |
| Simulator | How can quantum behavior be approximated or exactly simulated on classical hardware? |
| Quantum language | How should quantum and classical computation be expressed as a programming model? |
| Resource estimator | What resources would a quantum algorithm require under a specified computational model? |

Confusing these roles produces poor architecture decisions.

A compiler is not merely another circuit builder. A cloud service is not merely another simulator. A differentiable framework is not merely a gate library. A resource estimator answers a different question from a current-device execution API.

## Limitations of the Demonstrations

The Python, JavaScript, C++, Java, and SQL implementations are deliberately self-contained educational models.

They do not replace the actual vendor SDKs.

The circuit implementations do not attempt to implement complete quantum semantics, hardware calibration, pulse control, noise simulation, transpilation, automatic differentiation, or cloud authentication.

The workload recommendation scores are explainable heuristics rather than benchmark measurements.

The SQL suitability values are illustrative records and should not be interpreted as independent performance measurements.

The value of these implementations is architectural: they make the differences between SDK roles explicit without hiding those differences behind vendor-specific API calls.
