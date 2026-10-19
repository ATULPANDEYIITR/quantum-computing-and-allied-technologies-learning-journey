# Bernstein-Vazirani Algorithm

## Scope

The Bernstein-Vazirani (BV) algorithm solves a specific oracle problem: an unknown binary string `s` is encoded in a function

`f_s(x) = s · x mod 2`

where the dot product is evaluated over the binary field GF(2).

The task is to discover `s` from oracle access to `f_s`.

For an `n`-bit hidden string, a classical strategy can determine the string with `n` carefully chosen queries. The BV quantum circuit determines the entire string with one quantum oracle query. The distinction is an oracle-query complexity result. It does not mean that the complete circuit contains only one operation.

The six deliverables model the same algorithm from different technical perspectives:

- Python provides a complete state-vector simulator and compares classical and quantum query behavior.
- JavaScript represents the oracle as an event-driven component and combines state-vector processing with asynchronous execution.
- C++ develops a repository-style experiment case study around an explicit oracle and state-vector engine.
- Java models the experiment as an enterprise service with typed states, policy evaluation, validation, and immutable result records.
- PostgreSQL stores experiments, oracle queries, circuit gates, baselines, results, and protected execution policies.
- This README connects the implementations to the underlying mathematics and circuit behavior.

## Hidden-string problem

Let the hidden string be

` s = s₀s₁...sₙ₋₁ `

and let the oracle accept an input

` x = x₀x₁...xₙ₋₁ `.

The oracle returns

` f_s(x) = s₀x₀ ⊕ s₁x₁ ⊕ ... ⊕ sₙ₋₁xₙ₋₁ `.

The operation is XOR-based rather than ordinary integer multiplication and addition.

For example, with

` s = 101101 `

and

` x = 100001 `,

the only contributing positions are the first and last positions, so the oracle returns

`1 ⊕ 1 = 0`.

A unit vector isolates one hidden bit. If `e_i` contains a single `1` at position `i`, then

` f_s(e_i) = s_i `.

That observation gives the classical baseline used by the implementations.

## Classical query strategy

The classical algorithm constructs one unit vector for every hidden-string position.

For a six-bit secret, the inputs are conceptually:

- `100000`
- `010000`
- `001000`
- `000100`
- `000010`
- `000001`

The corresponding oracle responses directly reveal the six hidden bits.

The Python implementation exposes this behavior through `discover_classically()`. The Java implementation uses the same mathematical baseline through its `HiddenStringOracle`, while the SQL model stores the resulting query count as a `classical_baselines` record.

The important complexity measure is the number of oracle calls:

| Input width | Classical oracle queries | BV quantum oracle queries |
|---:|---:|---:|
| `n` | `n` | `1` |

The classical algorithm still performs efficient computation. Its limitation is that each oracle invocation supplies only one scalar response.

## Quantum circuit

The standard BV circuit contains an `n`-qubit input register and one oracle-output qubit.

The initial state is

`|0...0>|1>`.

Hadamard gates transform it into

`|+>^n |->`

where

`|+> = (|0> + |1>) / sqrt(2)`

and

`|-> = (|0> - |1>) / sqrt(2)`.

The oracle implements

`|x>|y> -> |x>|y ⊕ f_s(x)>`.

Because the second register is in `|->`, the XOR operation produces phase kickback:

`|x>|-> -> (-1)^(f_s(x)) |x>|->`.

The input register therefore contains a phase pattern determined by the hidden string:

`(-1)^(s·x)`.

A final layer of Hadamards performs the Walsh-Hadamard transform. Orthogonality of the binary characters maps the phase pattern to the computational basis state `|s>`.

Consequently, measuring the input register returns the hidden string with probability one in the ideal noiseless circuit.

## Oracle construction

The oracle can be implemented with controlled-NOT gates.

For every position where the hidden bit is `1`, a CNOT connects the corresponding input qubit to the output qubit.

For a hidden string such as `101101`, the relevant controls are the positions containing `1`. A hidden `0` does not require a CNOT because that input bit does not contribute to the parity function.

This structure is represented explicitly by:

- Python's `oracle_circuit_description()`
- JavaScript's `describeOracle()`
- C++'s oracle-architecture output
- Java's `oracleGates()`
- PostgreSQL's `circuit_gates` table

This is a meaningful distinction between the mathematical oracle and its circuit realization. The BV algorithm assumes access to the oracle; constructing that oracle requires knowledge of the function being queried.

## Python implementation

The Python program implements the complete state-vector workflow without third-party quantum libraries.

`HiddenStringOracle` validates the secret and evaluates the binary inner product. The classical discovery method uses unit vectors to establish the `n`-query baseline.

The quantum portion represents the full `n + 1` qubit state as a list of complex amplitudes. `apply_hadamard_all()` performs the Hadamard transform directly from the Walsh-Hadamard sign relationship rather than constructing a large dense matrix.

`apply_bv_oracle()` models the reversible transformation

`|x>|y> -> |x>|y XOR f_s(x)>`.

`apply_hadamard_to_input_register()` applies the final Hadamard layer only to the input register. `measure_input_register()` computes the marginal probability distribution of that register and samples it.

The final state support makes the algorithm's result observable at the circuit level. In an ideal BV experiment, the input portion is concentrated on the basis state representing the hidden string.

The Python program also includes a separate readout-noise model. This is intentionally not mixed into the ideal quantum circuit. An ideal BV circuit has deterministic input measurement, while a physical implementation may experience measurement or hardware errors.

Validation covers empty strings, non-binary strings, wrong-width oracle inputs, invalid noise probabilities, and invalid experiment sizes.

## JavaScript implementation

The JavaScript implementation uses a different architectural perspective.

`BernsteinVaziraniOracle` extends `EventTarget`. Each oracle evaluation dispatches a `query` event containing the input, output, and query count. This models an event-driven experiment service rather than a command-line-only algorithm.

The state-vector implementation uses JavaScript objects for complex amplitudes and `Float64Array` for marginal probabilities. The latter is appropriate for numerical storage because the probability array contains floating-point values with a fixed numeric representation.

`runQuantumExperiment()` uses a Promise and `setTimeout()` to represent an asynchronous experiment boundary. The asynchronous layer is deliberately separated from the mathematical transformation.

The file also demonstrates readout noise independently from the ideal oracle and exposes the CNOT structure through `describeOracle()`.

This separation is useful because quantum circuit semantics, experiment orchestration, and result collection are different concerns even when they participate in the same workflow.

## C++ case study

The C++ implementation treats the BV algorithm as a technical experiment service.

`HiddenStringOracle` owns and validates the hidden configuration. Its `evaluate()` method implements the GF(2) inner product.

The state-vector simulator uses a lightweight `Complex` structure. The program avoids external numerical libraries and directly implements the transformations required by the circuit.

The case-study layer is represented by `GovernanceExperiment`. It records an experiment identifier, the hidden configuration, the classical query count, and the quantum query count.

This separation demonstrates an important engineering boundary: the mathematical oracle does not need to know how experiment records are stored or reported.

The C++ program also prints the nonzero portion of the final state. In an ideal execution, the input register identifies the hidden string after the final Hadamard transform.

The program uses C++17 standard-library facilities and does not require third-party dependencies.

## Java enterprise model

The Java implementation focuses on explicit domain modeling.

`BitString` is an immutable value object. It validates the binary representation and provides the GF(2) dot product.

`Oracle` is an interface that separates the mathematical contract from the concrete hidden-string implementation.

`HiddenStringOracle` tracks query count so the experiment can distinguish a classical baseline from the quantum query requirement.

`ExperimentState` represents explicit lifecycle states:

`CREATED -> VALIDATED -> EXECUTED -> VERIFIED`

with `FAILED` available for execution or policy failures.

The transition method prevents invalid lifecycle changes instead of allowing arbitrary state mutation.

`ExperimentResult` is a Java record, which makes the final result immutable and compact.

`RepositoryQuantumPolicy` represents an enterprise-style policy boundary. It verifies that the result uses one quantum oracle query and passes verification. This is deliberately different from the Python implementation: the Java program treats the algorithm as a governed service operation rather than primarily as a numerical simulation.

## SQL data model

The PostgreSQL implementation stores the experiment domain relationally.

`repositories` and `protected_branches` identify where an experiment is governed.

`experiments` stores the hidden-string width, binary secret, lifecycle state, execution timestamps, and repository relationship. The database uses a regular expression and length constraint to prevent malformed hidden strings.

`oracle_queries` records individual oracle interactions and distinguishes `classical` from `quantum` queries.

`classical_baselines` records the result of the unit-vector strategy, including the number of oracle calls required.

`circuit_gates` records Hadamard and CNOT operations. CNOT rows identify their control and target qubits, making the relationship between the hidden string and the oracle implementation queryable.

`experiment_results` records the recovered string, quantum query count, verification result, and policy decision.

The `protected_branches` table introduces a governance boundary around the experiment. A protected branch can require verified results and a single quantum oracle query. The `experiment_policy_report` view combines the stored result with those branch policies.

This is useful for demonstrating database-level policy evaluation rather than leaving every invariant to application code.

## State and policy relationships

The algorithm has several distinct layers that should not be collapsed into one concept.

The hidden-string oracle defines the mathematical problem.

The circuit defines how the oracle is queried quantum mechanically.

The measurement produces an observed candidate.

Verification determines whether the observed candidate equals the expected hidden string.

A policy decides whether the experiment satisfies an external operational rule.

The Java state machine and PostgreSQL policy view make those boundaries explicit.

This distinction matters in production systems because a mathematically correct result and a valid operational record are different properties.

## Complexity

For an `n`-bit hidden string:

| Component | Classical strategy | Bernstein-Vazirani circuit |
|---|---:|---:|
| Oracle queries | `n` | `1` |
| Input register | Not applicable | `n` qubits |
| Oracle-output register | Not applicable | `1` qubit |
| Final input measurement | Direct classical bits | `n` measured qubits |
| Main algorithmic advantage | None in query count | Single oracle query |

The state-vector simulators have an important limitation that is independent of the BV query complexity result.

An `n + 1` qubit state vector contains `2^(n+1)` complex amplitudes. Classical simulation therefore requires exponential memory and computation in the number of simulated qubits.

The quantum algorithm's query complexity is not the same thing as the computational cost of simulating a quantum computer on a classical machine.

## Edge cases

The all-zero hidden string is valid. Its oracle always returns zero, and the quantum circuit produces the all-zero input basis state.

A one-bit hidden string is also valid. The circuit reduces to a minimal instance in which the single hidden bit is recovered.

A malformed secret containing characters other than `0` and `1` is rejected by the application implementations and by the PostgreSQL constraint.

An oracle input whose width differs from the hidden string must be rejected. Without this validation, the dot product would no longer represent the intended Boolean function.

A readout error should not be confused with an oracle error. The Python and JavaScript implementations keep the ideal circuit separate from the noise model.

## Verification and failure handling

The expected invariant is:

`recovered_string = hidden_string`.

The experiment is successful only when that equality holds.

The Java implementation adds a second invariant: the experiment must be in an appropriate lifecycle state before a result can be recorded or verified.

The SQL implementation places format, width, uniqueness, referential-integrity, and state-related restrictions at the database layer.

These checks illustrate different kinds of correctness:

- Mathematical correctness concerns the oracle and circuit transformation.
- Measurement correctness concerns the observed output.
- Application correctness concerns state transitions.
- Data correctness concerns persistent representation.
- Policy correctness concerns whether the result satisfies an external requirement.

## Common implementation mistakes

A frequent mistake is to describe the BV advantage as simply "one operation." The actual claim is one quantum oracle query. The circuit still contains state preparation, Hadamard operations, the oracle's internal gates, and measurement.

Another mistake is to treat the oracle as an ordinary function call without recognizing that a quantum oracle must be reversible. The transformation must preserve quantum state information and therefore uses a form such as

`|x>|y> -> |x>|y ⊕ f(x)>`.

Another mistake is to use ordinary integer arithmetic for the hidden-string function. The BV problem uses a GF(2) inner product, where addition is XOR.

A final common mistake is to confuse state-vector simulation complexity with quantum algorithm complexity. The Python and C++ simulators are exponentially expensive for large `n` because they explicitly store every basis amplitude.

## Practical interpretation

The Bernstein-Vazirani algorithm is valuable as a compact demonstration of several fundamental quantum-computing mechanisms.

The hidden string is encoded into a phase pattern through phase kickback. The Hadamard transform then extracts the complete pattern into a computational-basis state.

The algorithm also provides a clean example of why query complexity is a useful way to compare classical and quantum algorithms. The quantum method does not eliminate all computation. It changes how information supplied by the oracle is extracted.

The implementations preserve that distinction across numerical simulation, event-driven JavaScript, systems-oriented C++, enterprise-style Java modeling, and relational database representation.
