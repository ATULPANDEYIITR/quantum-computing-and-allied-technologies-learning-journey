# Deutsch Algorithm: Quantum Oracle Interference

## Problem definition

The Deutsch algorithm solves a small promise problem involving a Boolean function

\[
f:\{0,1\}\rightarrow\{0,1\}.
\]

The function is promised to belong to one of two categories:

- **Constant:** \(f(0)=f(1)\). The possible functions are the all-zero function and the all-one function.
- **Balanced:** \(f(0)\ne f(1)\). The possible functions are the identity function and the negation function.

The objective is to determine the category without necessarily learning the complete truth table.

A deterministic classical algorithm must evaluate both inputs in the worst case. The first result alone cannot distinguish a constant function from a balanced function because either category can produce the same value at input zero.

Deutsch's algorithm resolves the classification with one invocation of an ideal quantum oracle. Its advantage is measured in **oracle-query complexity**. It does not establish that quantum computers are universally faster than classical computers, and it does not establish a practical wall-clock advantage for this two-input problem.

## Oracle model and reversible computation

The quantum circuit uses two qubits. The first holds the function input, and the second is an ancilla used to encode the function output.

The oracle is represented by the reversible transformation

\[
U_f|x,y\rangle=|x,y\oplus f(x)\rangle,
\]

where \(\oplus\) denotes exclusive OR.

A classical Boolean function does not itself need to be reversible. A quantum gate must be unitary, so the oracle preserves the original input and combines the function result with a target bit. The transformation is a permutation of computational-basis states and is therefore reversible.

The circuit uses the ancilla state \(|1\rangle\), followed by a Hadamard gate, to create

\[
|-\rangle=\frac{|0\rangle-|1\rangle}{\sqrt{2}}.
\]

When the oracle acts on this target state, its output is encoded as a phase:

\[
U_f|x\rangle|-\rangle
=(-1)^{f(x)}|x\rangle|-\rangle.
\]

This is phase kickback. The function output is not obtained by measuring the ancilla. Instead, the input register acquires a phase pattern that can be analyzed through interference.

## Circuit mechanics

The two-qubit state evolves through preparation, oracle evaluation, and interference.

The input register starts in \(|0\rangle\). The ancilla starts in \(|1\rangle\). Applying a Hadamard gate to both qubits produces

\[
|+\rangle|-\rangle,
\qquad
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt{2}}.
\]

The oracle then applies the phase factors determined by the two function values:

\[
\frac{(-1)^{f(0)}|0\rangle+
(-1)^{f(1)}|1\rangle}{\sqrt{2}}
\otimes |-\rangle.
\]

A final Hadamard gate acts on the input qubit. The probability of measuring zero is

\[
P(0)=
\frac{\left((-1)^{f(0)}+(-1)^{f(1)}\right)^2}{4}.
\]

Consequently,

\[
P(0)=
\begin{cases}
1,& f\text{ is constant},\\
0,& f\text{ is balanced}.
\end{cases}
\]

An ideal circuit therefore produces a deterministic classification measurement even though its intermediate state is a superposition.

## Truth-table verification

| Function | \(f(0)\) | \(f(1)\) | Classification | Input measurement |
|---|---:|---:|---|---|
| All-zero | 0 | 0 | Constant | 0 |
| Identity | 0 | 1 | Balanced | 1 |
| Negation | 1 | 0 | Balanced | 1 |
| All-one | 1 | 1 | Constant | 0 |

The algorithm distinguishes the categories, not necessarily the individual functions within each category. For example, the identity and negation functions produce the same classification result.

## Python implementation

The Python script builds a state-vector simulator using only the standard library. It represents a quantum state as a list of complex amplitudes and uses the computational-basis index convention

\[
i=x+2y,
\]

where \(x\) is the least significant bit and \(y\) is the ancilla.

The `apply_single_qubit_gate` function updates pairs of amplitudes associated with a selected qubit. It applies the matrix to each pair without constructing a full two-qubit gate matrix. This approach generalizes to larger state vectors, although the memory and processing costs still grow exponentially with the number of qubits.

The `OracleDescription` class stores the two truth-table outputs. Its validation prevents values outside the Boolean domain from entering the simulation. The `apply_deutsch_oracle` function implements the reversible XOR operation as a permutation of state-vector indices.

The `deutsch_circuit` function composes the circuit stages and validates the state after important transformations. Probability calculations use squared amplitude magnitudes. The measurement function samples the first qubit by summing probabilities over basis states whose least significant bit is zero or one.

Additional checks verify normalization, reversible oracle behavior, inner-product preservation, and agreement between the theoretical probability and simulated circuit. The readout-noise experiment introduces a classical bit-flip error after measurement. It illustrates that a noisy physical measurement can be wrong even when the ideal circuit is deterministic.

The classical comparison deliberately uses both truth-table entries. It therefore illustrates the deterministic worst-case requirement of two oracle calls rather than comparing the quantum algorithm with an unnecessarily inefficient classical implementation.

## JavaScript implementation

The JavaScript implementation uses separate `Float64Array` instances for real and imaginary amplitudes. This representation makes the state-vector storage explicit and avoids creating a large number of temporary complex-number objects.

`BooleanOracle` validates its truth table and exposes the promised classification. `CircuitRun` models the circuit as a sequence of operations. After each operation, it records the input-qubit marginal probabilities and the total state norm. The resulting event trace makes it possible to inspect when the phase information is created and when the final Hadamard converts that information into a measurable result.

The `QuantumState`-like data structure is represented by the paired typed arrays rather than a third-party quantum framework. The `applyGate` function is restricted to the real-valued gates used in this circuit, so it does not claim to be a general complex-matrix simulator.

`estimateWithReadoutNoise` separates ideal state evolution from a classical measurement error model. Its output reports measurement counts and the most frequent outcome. A repeated-shot estimate is useful for understanding readout uncertainty, but repetition does not remove the one-oracle-call advantage of an individual ideal circuit execution.

The implementation runs under Node.js without external packages. The same circuit operations could be connected to a real quantum SDK, but hardware-specific noise, calibration, transpilation, and device execution are outside the scope of this simulator.

## C++ case study

The C++ program uses a repository-governance scenario to distinguish mathematical query complexity from ordinary application policy evaluation.

`BooleanOracle` provides a validated, immutable-style representation of the promised Boolean function. The `State` alias fixes the simulation to the four amplitudes needed for two qubits. The gate application function pairs basis states according to the target qubit's bit mask, while the oracle maps each basis index to the destination index determined by XOR.

`runDeutschCircuit` executes the circuit and computes the marginal probabilities of the input qubit. The result includes the classification and oracle-call count. The classical comparison evaluates both possible inputs.

The repository-policy structure is intentionally separate. It evaluates approval counts, stale approvals, required checks, resolved review conversations, and linear-history requirements through deterministic conditions. The example demonstrates that a quantum oracle result is not a substitute for actual repository authorization or branch protection.

The C++ program also checks failure conditions. Invalid Boolean outputs and invalid qubit indices cause explicit exceptions. Invalid policy inputs are rejected, while stale approvals, failed checks, and unresolved conversations block the modeled merge.

For this fixed two-qubit circuit, state storage is constant-sized. A general state-vector simulator with \(n\) qubits requires \(2^n\) complex amplitudes, making memory consumption exponential in the number of qubits. The compact C++ implementation is therefore a case study in correctness and representation, not a large-scale quantum simulator.

## Java implementation

The Java program models the circuit through domain types and service boundaries.

`BooleanOracle` is a record whose constructor validates the truth table. `QuantumState` encapsulates the amplitude arrays and exposes operations for normalization checks and marginal probability calculations. `QuantumGate` provides a functional interface for the gate transformations, while `DeutschCircuitService` composes those transformations into a classification operation.

The resulting `CircuitResult` is an immutable record containing the category, measurement probabilities, oracle-call count, and circuit-operation trace. Its constructor verifies that the reported probabilities sum to one within the numerical tolerance.

The enterprise-oriented part uses separate records for reviews, branch protection, pull requests, and merge decisions. `MergeEligibilityService` counts only current approvals from eligible reviewers. It independently checks lifecycle state, draft status, synchronization with the base branch, permitted merge strategies, status checks, unresolved conversations, and linear-history requirements.

The sample includes approvals that should not count because the reviewer is ineligible or the approval is stale. It also includes a second pull request blocked by synchronization, status-check, and merge-strategy failures.

This domain separation is important. A mathematical classification service has a precisely defined oracle and output. Repository governance requires identity, authorization, policy enforcement, and state-transition controls. The example models selected governance rules but does not integrate with a real Git hosting provider or enforce server-side permissions.

## PostgreSQL data model

The SQL implementation provides a relational representation of both the mathematical truth tables and an independent repository-governance workflow.

### Oracle records

`deutsch_oracles` stores the two function outputs. Check constraints restrict each output to zero or one, and a unique constraint prevents duplicate oracle names.

The `deutsch_oracle_results` view derives the function category and the ideal input-qubit measurement probabilities. It also records the query-complexity comparison: one quantum oracle invocation versus two deterministic classical evaluations in the worst case.

The probabilities in this view are theoretical results from the promise problem. The SQL database does not simulate quantum amplitudes or execute a quantum circuit.

### Repository entities

`repositories` identifies the repository. `repository_branches` represents its branches and their protection status. `repository_members` records reviewer eligibility.

`branch_protection_policies` stores approval requirements, required checks, conversation-resolution rules, linear-history requirements, direct-push restrictions, force-push restrictions, deletion restrictions, stale-approval handling, administrator bypass settings, and allowed merge strategies.

`pull_requests` links source and target branches, the author, lifecycle state, synchronization state, conflict state, conversation status, linear-history status, and merge strategy. Its checks reject identical source and target branches and inconsistent closed-state timestamps.

`pull_request_commits` records commits associated with a pull request. Its primary key prevents the same commit from being recorded twice for the same pull request, while the SHA constraint validates the expected hexadecimal length.

`repository_reviews` stores reviewer decisions and stale status. The uniqueness constraint permits one current review record per reviewer and pull request in this simplified model. A production implementation would normally preserve review history as separate immutable events.

`required_status_checks` stores check names, states, commit associations, and completion timestamps. The constraints distinguish pending checks from completed checks.

### Merge eligibility

The `pull_request_merge_eligibility` view uses common table expressions to aggregate review decisions and status checks before applying policy conditions.

An approval counts only when the reviewer is active, eligible to review, and the approval is current under the selected stale-approval policy. An active request for changes blocks eligibility. The view separately evaluates required checks, source-branch synchronization, merge conflicts, resolved conversations, linear history, lifecycle state, and permitted merge strategies.

Indexes support common lookups by target branch and lifecycle state, review state, and status-check state.

The fixture first creates a pull request with two eligible approvals and passing checks. It then marks one approval stale and temporarily changes a status check to pending, exposing the effect of those states on merge eligibility.

The script uses a transaction and ends with `ROLLBACK`, leaving the demonstration data uncommitted. This makes the example repeatable when executed in a PostgreSQL session.

Database constraints enforce the stored data's shape, but they do not implement a complete branch-protection service. In particular, a production system must enforce direct-push restrictions, force-push restrictions, branch deletion rules, reviewer authorization, bypass permissions, and merge execution through controlled database procedures or the hosting platform's authorization layer.

## Classical and quantum query complexity

For the promised one-bit Deutsch problem, the deterministic classical worst case requires two oracle queries. A quantum circuit makes one oracle invocation because the input superposition allows the oracle to act on both possible inputs during the same unitary operation.

This comparison depends on the oracle abstraction. It does not imply that an arbitrary classical implementation must be slower in real time. The actual cost of preparing a quantum state, implementing the oracle, applying gates, measuring the result, and handling errors matters in practical systems.

The Deutsch algorithm is an introductory example of how interference can reveal a global property of a function. Its significance is conceptual: the quantum circuit uses the structure of a reversible oracle and phase interference to obtain a classification with fewer oracle invocations.

## Numerical and operational limitations

A state-vector simulator stores complex amplitudes as finite-precision numbers. Floating-point rounding can cause small deviations from exact normalization or zero probabilities. The programs use a numerical tolerance rather than exact floating-point equality.

The ideal algorithm assumes that the oracle implements the promised Boolean function correctly. If the oracle is faulty, or if gates and measurements are noisy, the classification guarantee no longer holds in the same form.

Readout repetition can help estimate the more likely result when measurement errors are present. Repetition does not by itself correct coherent gate errors, systematic oracle faults, or arbitrary noise. Error mitigation and quantum error correction require additional assumptions and mechanisms that are not modeled here.

The promise is also essential. If the function is not guaranteed to be constant or balanced, the circuit's measurement still reveals a property of the two outputs, but the interpretation as a valid solution to the promised classification task may not apply.
