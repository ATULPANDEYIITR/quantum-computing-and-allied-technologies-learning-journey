# Deutsch-Jozsa Algorithm: Oracle-Based Quantum Computation

## Problem definition

The Deutsch-Jozsa algorithm is an early quantum algorithm demonstrating how quantum interference can distinguish two classes of Boolean functions with fewer oracle queries than a deterministic classical algorithm.

Let

\[
f:\{0,1\}^{n}\rightarrow\{0,1\}.
\]

The input consists of an unknown function accessible through an oracle. The algorithm is promised that the function belongs to one of two classes:

- **Constant:** Every input produces the same output, either zero or one.
- **Balanced:** Exactly half of all possible inputs produce zero, and the other half produce one.

The task is to identify which class contains the function. The promise is essential. A function with an arbitrary number of ones may belong to neither class, and the standard algorithm does not provide the promised classification for such a function.

## Oracle model and phase kickback

A reversible quantum oracle for a Boolean function is conventionally represented as

\[
U_f|x,y\rangle=|x,y\oplus f(x)\rangle,
\]

where \(x\) is the input register, \(y\) is an ancilla qubit, and \(\oplus\) denotes XOR.

The ancilla is prepared in the state

\[
|-\rangle=\frac{|0\rangle-|1\rangle}{\sqrt{2}}.
\]

When the oracle acts on this state, the target-register operation produces a phase:

\[
U_f|x\rangle|-\rangle
=(-1)^{f(x)}|x\rangle|-\rangle.
\]

This effect is called **phase kickback**. The function value changes the phase of each input basis state rather than leaving a separately recorded output bit.

The Python, JavaScript, C++, and Java implementations use this equivalent phase-oracle representation. They simulate the input register directly and do not allocate a separate ancilla because its behavior is analytically known.

## Circuit structure

The algorithm starts with the input register in \(|0\rangle^{\otimes n}\). Hadamard gates create an equal superposition of all \(2^n\) input strings:

\[
H^{\otimes n}|0\rangle^{\otimes n}
=\frac{1}{\sqrt{2^n}}\sum_x|x\rangle.
\]

The oracle applies the phase \((-1)^{f(x)}\) to each component. A second layer of Hadamard gates combines the resulting amplitudes.

The amplitude of the all-zero state after the second Hadamard layer is

\[
\alpha_0=\frac{1}{2^n}\sum_x(-1)^{f(x)}.
\]

For a constant function, all terms have the same sign. Consequently, the magnitude of the zero-state amplitude is one, and measuring the input register returns the all-zero string with probability one.

For a balanced function, half of the terms are positive and half are negative. They cancel exactly, giving

\[
\alpha_0=0.
\]

The probability of measuring the all-zero string is therefore zero for a balanced oracle.

The classification follows from this interference pattern rather than from separately reading every oracle output.

## Quantum and classical query complexity

The ideal Deutsch-Jozsa circuit requires one oracle query, independently of the input width, provided the oracle is available as a quantum operation and the promise holds.

A deterministic classical algorithm can need

\[
2^{n-1}+1
\]

queries in the worst case. After observing \(2^{n-1}\) identical outputs, the function could still be constant or could have its remaining outputs set to the opposite value. One more query resolves that ambiguity.

This comparison concerns oracle queries, not total computation time. A classical simulator that explicitly stores all amplitudes requires exponential memory, so simulating the quantum circuit on a conventional computer does not inherit the algorithm's physical quantum resource requirements.

## Python implementation

The Python program defines `QuantumRegister`, a state-vector abstraction holding complex amplitudes for the input register. Its `hadamard_all` method performs a fast Walsh-Hadamard transform using pairs of amplitude updates. This reduces the transform work to \(O(n2^n)\) operations rather than applying each matrix entry independently.

`phase_oracle` negates amplitudes for inputs where the Boolean function returns one. It checks that the function returns binary values and that the register width matches the declared input width.

`validate_boolean_function` evaluates the complete truth table for the small simulated input space. `classify_promise` rejects a function that is neither constant nor balanced. This validation is useful in a simulator, although it uses exponentially many classical function evaluations and is not part of the one-query quantum circuit.

The `deutsch_jozsa` function prepares the superposition, applies the phase oracle, performs the final transform, calculates probabilities, and samples a computational-basis measurement. The test routine checks constant-zero, constant-one, parity, and invalid-promise cases.

## JavaScript implementation

The JavaScript version uses separate `Float64Array` instances for real and imaginary amplitude components. This representation avoids creating a separate complex-number object for each basis state and makes the transform operations explicit.

`StateVector` owns the circuit state and implements the global Hadamard transform, phase marking, probability calculation, and measurement. The measurement method samples the probability distribution with a cumulative sum. Its optional random-number function makes repeatable tests possible.

`makeBitParityOracle` constructs a balanced Boolean oracle by calculating the parity of selected input bits. The demonstration compares its results with a constant oracle and verifies that an invalid single-mark oracle is rejected.

The module exports its main classes and functions, allowing the state-vector engine to be imported into a separate test or simulation program. The simulator's state space remains exponential in the number of qubits.

## C++ case study

The C++ program models a diagnostic controller that receives a Boolean oracle specification, validates it, and executes a state-vector circuit.

`BooleanOracle` stores the truth table and verifies the constant-or-balanced promise. Its constructor limits the input width to keep memory consumption bounded. This is a practical constraint for a simulator because the number of basis states grows as \(2^n\).

`QuantumRegister` stores complex amplitudes in a structure containing real and imaginary components. The `hadamardAll` method performs the transform in place, while `applyPhaseOracle` implements phase kickback by negating the affected amplitudes.

`DiagnosticController` executes the circuit and produces a `DiagnosticReport` containing the expected class, inferred class, probability of the all-zero state, most likely basis outcome, and oracle-query count. The example checks both a constant calibration function and a three-bit parity function.

The controller separates oracle validation from circuit execution. That separation prevents an invalid specification from being silently classified as though it satisfied the algorithm's promise.

The program uses C++17-compatible language features and standard-library containers. Its simulation complexity is \(O(n2^n)\) time and \(O(2^n)\) memory. The query count of one refers to the abstract oracle circuit, not to the classical evaluations needed to construct and validate the truth table.

## Java enterprise implementation

The Java program separates the oracle specification, registry validation, quantum state, computation service, and computation report into explicit domain types.

`OracleSpecification` validates the identifier and input width when constructed. `OracleRegistry` evaluates the truth table and returns a `FunctionClass` only when the promise is satisfied. Invalid functions produce `OracleValidationException`.

`QuantumState` owns the amplitude arrays and implements the two Hadamard layers and phase-oracle operation. `ComputationService` orchestrates validation and execution, compares the circuit classification with the validated class, and returns an immutable `ComputationReport`.

The report includes the oracle identifier, expected and inferred classes, zero-state probability, oracle-query count, and a defensive immutable copy of the probability distribution. These choices separate computation state from its recorded result and make the simulation easier to integrate into a larger experiment-management service.

The service's validation is deliberately distinct from the quantum algorithm itself. The registry's complete truth-table inspection is a classical verification step; it must not be counted as part of the theoretical one-query quantum procedure.

## PostgreSQL experiment registry

The SQL script stores oracle specifications, their classical truth tables, and the outcomes reported by simulated or ideal circuit runs.

The `oracle_experiment` table records the input width, expected function class, and experiment description. The `oracle_truth_table` table associates each possible input with its Boolean output and uses a composite primary key to prevent duplicate input rows within an experiment.

The `circuit_run` table records the simulator identifier, oracle-query count, probability of the all-zero state, measured bitstring, and inferred classification. Check constraints reject invalid probability values, negative query counts, and unsupported classification labels.

The `oracle_validation` view checks whether the truth table contains exactly \(2^n\) rows and whether the number of ones agrees with the declared class. It distinguishes incomplete truth tables, valid constant or balanced functions, class mismatches, and promise violations.

The `experiment_audit` view compares the recorded circuit outcome with the validated specification. It flags incorrect classifications, inconsistent zero-state probabilities, and query counts that differ from the expected one-query model.

The database records and audits evidence. It does not implement Hadamard gates or perform quantum measurements. The circuit simulator remains responsible for generating quantum-state results, while PostgreSQL provides persistence, integrity constraints, and experiment-level traceability.

## Important implementation distinctions

| Mechanism | Purpose |
|---|---|
| Boolean oracle | Defines the unknown function whose class must be determined |
| Phase kickback | Encodes function outputs as relative phases |
| Hadamard transform | Creates superposition and recombines amplitudes |
| Interference | Cancels or reinforces amplitudes according to the function class |
| Computational-basis measurement | Converts the final state into a classical observation |
| Promise validation | Rejects functions outside the algorithm's stated domain |
| State-vector simulation | Reproduces circuit behavior using classical memory and computation |

## Limitations and practical considerations

A state-vector simulator calculates amplitudes explicitly. Its exponential memory requirement limits the number of qubits that can be simulated, even though the abstract circuit needs only one oracle query.

The standard Deutsch-Jozsa result assumes an ideal oracle, exact gates, and the constant-or-balanced promise. Real quantum hardware introduces noise, gate errors, and imperfect measurement. A practical hardware implementation may therefore produce outcomes inconsistent with the ideal distribution.

A single measured all-zero string indicates the constant class under the ideal promise, but a nonzero string does not distinguish one balanced function from another. The algorithm determines the class, not the complete truth table.

Classical promise validation in the examples requires examining all \(2^n\) inputs. That validation is suitable for controlled demonstrations and testing but would defeat the query advantage if performed on an unknown oracle before execution. In an actual quantum setting, the promise must be guaranteed by the problem specification or established through separate means.

The central technical distinction is between querying an oracle and simulating an oracle. The quantum algorithm queries the function once within its circuit, while the software examples reproduce the circuit by explicitly calculating all basis-state amplitudes and may evaluate the Boolean function many times.
