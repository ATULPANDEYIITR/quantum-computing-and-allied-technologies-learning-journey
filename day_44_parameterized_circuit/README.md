# Parameterized Quantum Circuits: Variables and Rotations

## Technical scope

A parameterized quantum circuit is a circuit template whose gate operations can depend on symbolic numerical variables. Instead of constructing a new circuit for every input, an application defines a reusable sequence of gates and supplies parameter values when evaluating it.

The distinction between a circuit definition and a particular circuit evaluation is central to variational quantum algorithms. A template may represent a family of quantum operations, while a binding assigns concrete values to its symbolic parameters. An optimizer can update trainable parameters without rebuilding the conceptual structure of the circuit.

This repository studies parameterized circuits through four connected mechanisms:

- **Parameterized rotations** define quantum operations whose angles are supplied numerically or symbolically.
- **Variables and expressions** represent inputs, trainable weights, calibration offsets, and relationships between gate angles.
- **Binding and evaluation** convert symbolic definitions into executable operations and produce state vectors, probabilities, or expectation values.
- **Parameter optimization** uses objective functions and gradients to identify parameter settings that improve a circuit's measured behavior.

The implementations use a small state-vector simulator and a relational representation of circuit definitions. They are educational models, not substitutes for hardware execution, noise modeling, or production quantum SDKs.

## Mathematical foundations

### Single-qubit rotation gates

Let \(X\), \(Y\), and \(Z\) denote the Pauli matrices. Rotation gates are defined by

\[
R_P(\theta)=e^{-i\theta P/2}, \qquad P\in\{X,Y,Z\}.
\]

Their matrices are

\[
R_X(\theta)=
\begin{pmatrix}
\cos(\theta/2)&-i\sin(\theta/2)\\
-i\sin(\theta/2)&\cos(\theta/2)
\end{pmatrix},
\]

\[
R_Y(\theta)=
\begin{pmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)&\cos(\theta/2)
\end{pmatrix},
\]

\[
R_Z(\theta)=
\begin{pmatrix}
e^{-i\theta/2}&0\\
0&e^{i\theta/2}
\end{pmatrix}.
\]

The angle \(\theta\) is measured in radians. The half-angle convention is part of the definition, not an implementation detail that can be changed without changing the gate.

A rotation around the X axis changes amplitudes using complex phase factors. A Y rotation mixes the computational-basis amplitudes using real sine and cosine terms. A Z rotation changes relative phase while leaving computational-basis probabilities unchanged when applied directly to a computational-basis measurement without later interference.

The distinction between phase and probability matters. An RZ gate can change a quantum state without immediately changing its probabilities in the computational basis. A later gate can transform that phase difference into an observable probability difference.

### Variables, bindings, and angle expressions

A symbolic parameter is a named value, such as `phase`, `weight`, or `offset`. It is not itself a quantum operation. A rotation gate references an expression that is evaluated when a parameter binding is applied.

For example,

\[
\theta_{\mathrm{effective}}=\phi+\frac{w}{2}
\]

can represent a compensated rotation. Here, \(\phi\) is a calibration offset and \(w\) is a trainable weight. The circuit definition remains unchanged when either variable changes.

A binding such as `phase = 0.65`, `drive = -0.35`, and `offset = 0.12` supplies concrete values. The binding process must reject missing variables, unknown variable names, non-finite values, and values outside any explicitly configured bounds.

Angle expressions also introduce a design choice. A circuit can preserve a symbolic expression until execution or evaluate it before sending the circuit to a simulator or quantum device. Early evaluation simplifies execution, while preserving the symbolic representation supports inspection, parameter sweeps, differentiation, and reusable circuit templates.

### Circuit state and measurement

For \(n\) qubits, a pure state is represented by \(2^n\) complex amplitudes:

\[
|\psi\rangle=\sum_{x=0}^{2^n-1}\alpha_x|x\rangle,
\qquad
\sum_x|\alpha_x|^2=1.
\]

The computational-basis probability of outcome \(x\) is \(|\alpha_x|^2\). The normalization condition is an important simulator invariant.

For a measurement of Pauli \(Z\) on qubit \(j\), the expectation value is

\[
\langle Z_j\rangle=
\sum_x(-1)^{x_j}|\alpha_x|^2.
\]

An expectation value lies between \(-1\) and \(1\) for a normalized state. It can serve as an objective function for calibration or variational optimization.

A controlled-NOT gate couples two qubits. It flips the target bit only when the control bit is one. In a state-vector simulator, that operation permutes amplitudes. In a quantum device, it is an entangling operation whose physical implementation depends on the hardware.

## Circuit architecture and lifecycle

A reusable parameterized circuit typically passes through the following conceptual stages:

- **Definition:** declare the qubit count, symbolic parameters, gate sequence, and angle expressions.
- **Binding:** validate a complete mapping from parameter names to finite numerical values and evaluate each gate expression.
- **Execution:** simulate the bound circuit or submit it to a compatible quantum execution service.
- **Measurement:** obtain samples, probabilities, or expectation values from the resulting quantum state.
- **Optimization or calibration:** update selected parameter values based on the measured objective and repeat the evaluation.

The distinction between definition and binding makes repeated experiments easier to manage. A circuit can be defined once and evaluated against a dataset or multiple candidate parameter vectors. The execution results must still be associated with the exact parameter values and circuit version that produced them.

## Python implementation

The Python script implements a small parameter-expression system using immutable `Parameter` and `Expression` objects. Addition and multiplication create expression trees rather than immediately calculating a numerical angle. This allows a gate to retain relationships between variables until binding.

`ParameterizedCircuit` records gates and parameter names. Its rotation methods accept symbolic expressions or numerical constants, while `bind` validates the complete binding and creates a `BoundCircuit` containing evaluated angles.

The state-vector implementation supports Hadamard, RX, RY, RZ, and CNOT operations. The rotation routines process pairs of amplitudes whose basis indices differ in the selected qubit bit. CNOT swaps amplitudes when the control bit is one and the target bit is zero.

`BoundCircuit` exposes basis-state probabilities and Z and ZZ expectation values. It also checks state normalization after execution. The demonstration builds a two-qubit feature circuit containing a data parameter, a trainable weight, and a calibration bias. The RZ angle combines the bias and half the weight, while a later RY gate uses twice the data parameter.

The gradient examples distinguish two methods. The parameter-shift helper applies the standard shift formula for a single direct occurrence of a parameter in a Pauli rotation. The finite-difference helper approximates a derivative using nearby evaluations. The parameter-shift helper deliberately rejects unsupported parameter-use patterns instead of presenting an invalid derivative as exact.

The script also exercises failure handling for missing bindings, unknown names, non-finite values, and invalid qubit indices. These checks demonstrate that parameter validation should occur before a circuit reaches execution.

## JavaScript implementation

The JavaScript file emphasizes event-driven parameter updates and reusable circuit templates. `AngleExpression` holds evaluators and parameter dependencies, while `CircuitTemplate` records the gate sequence independently of the current numerical configuration.

`ParameterEvaluationService` manages parameter values and publishes evaluation events after a proposed update has successfully passed binding validation. Each successful update increments a revision number. Subscribers receive an immutable event containing the parameter values and the resulting probability distribution.

This separation is useful for an interactive calibration interface or a parameter optimizer. A UI can change a slider value, request an evaluation, and update a chart without redefining the gate sequence. Invalid updates are rejected before the new values are published, preventing listeners from observing a partially applied configuration.

The implementation uses JavaScript arrays of real-imaginary pairs for complex amplitudes. This avoids an external complex-number dependency, but it also requires explicit helper functions for complex multiplication, addition, and scaling. The simulator remains limited to small state vectors and should not be used for large quantum workloads.

## C++ case study: sensor calibration

The C++ program models a two-qubit sensor calibration circuit. The input phase describes the signal, the drive parameter represents a trainable control setting, and the offset compensates for a device-specific phase shift.

The `AngleExpression` type represents constants, parameter references, addition, and multiplication. It evaluates expressions against a binding map and rejects missing or non-finite values. `CircuitTemplate` owns the symbolic gate sequence, validates qubit indices, and resolves expressions during binding.

After binding, the simulator executes a concrete sequence of Hadamard, rotation, and CNOT operations. Its state vector is a `std::vector<std::complex<double>>`. Each rotation updates paired amplitudes, while CNOT exchanges amplitudes selected by the control and target bits.

The calibration output contains a probability for every computational-basis state. The program verifies that the probabilities sum to one within a numerical tolerance and computes single-qubit Z expectation values.

C++ makes the memory and data representation explicit, which is useful when analyzing simulator costs. A state vector contains \(2^n\) amplitudes, so its memory requirement grows exponentially with qubit count. The implementation limits its supported width to avoid impractical allocations and to keep the case study focused on parameter binding and gate behavior.

## Java implementation: enterprise calibration service

The Java program models a parameterized calibration circuit using domain-oriented types. `CircuitParameter` records a parameter name and purpose. `RotationAxis`, `GateKind`, and `Gate` represent valid operations and their required attributes.

The `Angle` interface separates the definition of an expression from its evaluation. `ConstantAngle`, `ParameterAngle`, and `BinaryAngle` implement numerical constants, variable references, and arithmetic expressions. Parameter dependencies are collected explicitly, so a circuit can verify that every referenced parameter has been declared.

`CircuitTemplate.bind` checks for missing and unknown names, validates finite values, evaluates each gate angle, and returns a `BoundCircuit`. The bound circuit stores immutable copies of its gates and parameter bindings. This provides a clear boundary between a reusable circuit definition and one concrete evaluation request.

The simulation uses separate real and imaginary arrays. This representation is less convenient than a complex-number abstraction, but it illustrates how a numerical engine can avoid allocating a complex object for every intermediate amplitude. The simulator verifies normalization and calculates Z expectation values.

The domain model is designed to make invalid states difficult to construct. A rotation must have an axis and angle; a CNOT must have a target; gate qubit indices must fit the circuit width; and expressions must refer to declared variables. These rules make the program easier to extend into a service that records calibration runs, associates results with configurations, and reports validation failures clearly.

## SQL data model

The PostgreSQL script separates circuit definitions from execution requests and their results.

| Relation | Purpose |
|---|---|
| `circuit` | Stores circuit identity, width, and descriptive metadata. |
| `circuit_parameter` | Defines symbolic variables, their roles, and optional bounds. |
| `circuit_gate` | Records gate order, qubit operands, constant angles, or symbolic expressions. |
| `circuit_evaluation` | Tracks an evaluation request and its lifecycle state. |
| `parameter_binding` | Associates one concrete value with each parameter in an evaluation. |
| `evaluation_result` | Stores probabilities supplied by an execution runtime. |

Primary keys identify records, foreign keys maintain relationships, and unique constraints prevent duplicate parameter names or gate positions within a circuit. Check constraints validate basic row-level rules, including gate operand requirements, finite values, and evaluation timestamps.

Cross-table rules require triggers because a conventional `CHECK` constraint cannot query another table. The gate validation trigger ensures that a target or control qubit lies within the declared circuit width. The binding trigger ensures that the parameter and evaluation belong to the same circuit and that the numerical value respects the parameter's configured bounds.

The `evaluation_binding_completeness` view compares the declared parameter set with the bindings provided for each evaluation. The `check_evaluation_ready` function determines whether a queued evaluation has every required parameter. An evaluation with an incomplete binding must not be submitted for execution.

Indexes support ordered gate retrieval, queue processing, and parameter-value lookups. They are selected for those query patterns rather than added indiscriminately.

The SQL script stores angle expressions as text, but it does not parse or execute them. A quantum execution service must interpret those expressions, apply the numerical rotations, and produce the measurement distribution. This separation keeps the database responsible for durable configuration and integrity while leaving numerical quantum computation to an execution engine.

The sample probability rows illustrate result storage and aggregate normalization checks. Row-level constraints cannot by themselves ensure that all probabilities for an evaluation sum to one. That invariant must be checked across the complete result set, preferably within a transaction or through a controlled result-publication procedure.

## Parameter binding and validation

A reliable parameterized-circuit system distinguishes a variable declaration from a supplied value. The declaration identifies the variable and its intended role; the binding supplies the value for one evaluation.

Missing and unknown parameters are different errors. A missing parameter means that the circuit cannot be fully evaluated. An unknown parameter usually indicates a misspelled name, a stale configuration, or a binding created for another circuit. Both should be rejected rather than silently ignored.

Non-finite values require explicit validation. `NaN` and infinity can propagate through trigonometric operations and produce meaningless numerical results. Optional bounds can restrict calibration parameters to an experimentally meaningful range. Such bounds are application policies, not universal mathematical requirements for rotation angles.

Parameter names should be stable enough for circuit templates, saved configurations, and optimization histories to refer to them consistently. When a circuit definition changes, its version and the exact binding should be recorded with the resulting evaluation.

## Parameterized circuits and variational optimization

A variational quantum circuit contains adjustable parameters whose values influence an objective function. An optimization loop repeatedly binds a candidate parameter vector, executes the circuit, measures an observable or cost function, and proposes an updated vector.

For a cost function \(C(\theta)\), a numerical gradient estimate can be computed by central differences:

\[
\frac{\partial C}{\partial\theta}
\approx
\frac{C(\theta+h)-C(\theta-h)}{2h}.
\]

The step size \(h\) introduces a trade-off. A very large step introduces approximation error; an extremely small step can amplify floating-point error or sampling noise.

For a suitable expectation value of a gate containing a single parameterized Pauli rotation, the parameter-shift rule can provide an exact derivative:

\[
\frac{\partial C}{\partial\theta}
=
\frac{C(\theta+\pi/2)-C(\theta-\pi/2)}{2}.
\]

The rule must be applied according to the structure of the gate and objective. A parameter that appears in several gates, appears through a scaled expression, or enters a nonlinear transformation may require a more general derivative calculation. The Python implementation restricts its helper to a single direct occurrence to avoid implying that the simple formula applies universally.

On real quantum hardware, each expectation estimate may require many circuit shots. Consequently, gradient estimates have sampling uncertainty and incur execution costs. Parameter reuse reduces circuit-definition overhead, but it does not eliminate the physical cost of repeated measurements.

## Practical distinctions and limitations

**A symbolic parameter is not a rotation gate.** A parameter supplies a value to an expression, while the gate defines the operation applied to a qubit.

**Binding is not execution.** Binding evaluates the expressions and validates the configuration. A simulator or quantum processor must still execute the resulting operations.

**A rotation angle is not a measured probability.** Rotation angles influence amplitudes and phases. Probabilities arise from squared amplitude magnitudes after circuit execution and measurement in a specified basis.

**A valid binding does not guarantee a useful circuit.** The values may satisfy every validation rule while producing an uninformative measurement distribution or a poor optimization objective.

**A normalized simulated state is not evidence of hardware fidelity.** The supplied simulators model ideal unitary gates. They do not include decoherence, readout errors, gate noise, connectivity constraints, pulse calibration, or hardware scheduling.

**A database constraint does not validate quantum mathematics.** Relational integrity can protect configuration records, but a separate execution engine must validate expression semantics, gate compatibility, output normalization, and the correctness of computed observables.

## Performance and production considerations

State-vector simulation requires \(O(2^n)\) memory for \(n\) qubits. Applying a one-qubit gate to the full state vector requires \(O(2^n)\) arithmetic operations. Adding a symbolic expression introduces relatively small overhead compared with the state-vector simulation, but expression evaluation should still be kept separate from repeated numerical execution when practical.

For repeated evaluations, retain an immutable circuit template and bind new parameter vectors to it. Cache only when the cache key includes the circuit definition or version and the complete binding. A result associated with an old parameter vector must never be mistaken for a result from a newer evaluation.

Concurrent optimization runs should have separate evaluation identifiers and immutable parameter snapshots. Updating a shared mutable parameter map while a simulation is running can associate measurements with the wrong configuration.

A production system should also record circuit versions, parameter values, execution timestamps, device identifiers, shot counts, measurement results, and error information. Bounds and validation rules should reflect the intended experiment, while avoiding assumptions that every valid rotation angle must lie in a single universal interval.

The supplied programs provide a compact reference model for these responsibilities: symbolic definitions describe reusable quantum operations, bindings define concrete evaluations, rotation gates determine state evolution, and measured observables provide the values used to assess or optimize a circuit.
