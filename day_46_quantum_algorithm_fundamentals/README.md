# Quantum Algorithm Fundamentals: Algorithmic Thinking

## Purpose and Scope

Quantum algorithms solve computational problems by manipulating probability amplitudes rather than directly processing a collection of classical candidate answers. Their behavior depends on how quantum states are prepared, how oracle operations encode problem information, how interference changes measurement probabilities, and how measurement converts a quantum state into a classical result.

This project examines three foundational algorithm families:

- **Deutsch's algorithm** distinguishes constant and balanced Boolean functions under a promise about the function.
- **Bernstein-Vazirani** identifies a hidden bit string using a parity oracle.
- **Grover search** amplifies the probability of measuring a state satisfying a specified predicate.

The implementations use idealized state-vector simulation. They make the mathematical mechanisms executable while exposing the difference between query complexity, classical verification, and the resources needed to simulate quantum systems.

## The Computational Model

An \(n\)-qubit register has \(2^n\) computational-basis states. A pure state is represented by complex amplitudes:

\[
|\psi\rangle = \sum_{x=0}^{2^n-1}\alpha_x|x\rangle
\]

The amplitudes satisfy the normalization condition

\[
\sum_x |\alpha_x|^2=1.
\]

A computational-basis measurement returns \(x\) with probability \(|\alpha_x|^2\). Measurement does not reveal all amplitudes in a single observation. Repeated measurements estimate a probability distribution, and the observed frequencies vary statistically.

A quantum algorithm therefore needs more than a search space. It requires a circuit whose transformations encode useful relationships between candidate states.

### Superposition and interference

A Hadamard gate transforms a single-qubit basis state as follows:

\[
H|0\rangle=\frac{|0\rangle+|1\rangle}{\sqrt{2}}
\]

\[
H|1\rangle=\frac{|0\rangle-|1\rangle}{\sqrt{2}}.
\]

Applying Hadamard gates to \(n\) zero-valued qubits produces a uniform superposition. Applying the transformation again restores the original basis state because \(H^2=I\).

The signs of amplitudes matter even when their immediate measurement probabilities are identical. Later transformations can make amplitudes reinforce or cancel one another. This interference is the mechanism behind the algorithms in this project.

### Oracle access and query complexity

An oracle represents a specific computational problem operation. It is not automatically a fast implementation of the underlying problem.

A reversible Boolean oracle may implement

\[
U_f|x,y\rangle=|x,y\oplus f(x)\rangle.
\]

When the target register is prepared in the state \(|-\rangle=(|0\rangle-|1\rangle)/\sqrt{2}\), the oracle induces a phase:

\[
U_f|x\rangle|-\rangle=(-1)^{f(x)}|x\rangle|-\rangle.
\]

Oracle query complexity counts calls to this operation. It does not include every gate required to construct the oracle, the cost of preparing its input, error correction, hardware execution time, or the classical cost of verifying the result.

## Algorithmic Thinking in Quantum Computing

Quantum algorithm design begins with a precise problem statement. The algorithm must identify the input representation, the promised structure of the input, the operation that encodes relevant information, and the measurement outcome that answers the problem.

A useful design separates the following concerns:

- **Problem contract:** Defines valid inputs, target states, and any promise that makes the algorithm correct.
- **State preparation:** Places the register into a state appropriate for the problem.
- **Information encoding:** Uses an oracle or circuit to introduce problem-dependent phases, correlations, or amplitudes.
- **Interference:** Transforms those differences into distinguishable outcome probabilities.
- **Measurement and verification:** Produces a classical observation and checks it against the problem contract.
- **Resource analysis:** Measures qubits, oracle calls, gates, circuit depth, shots, memory, and execution costs separately.

These concerns are related but not interchangeable. A circuit can be mathematically correct and still be impractical because its oracle is expensive or its physical error rate is too high.

## Deutsch's Algorithm: A Promise Problem

Deutsch's algorithm receives a Boolean function \(f:\{0,1\}\rightarrow\{0,1\}\). The input promise states that the function is either constant or balanced.

A constant function has \(f(0)=f(1)\). A balanced function has \(f(0)\ne f(1)\).

The circuit prepares the input and target registers, applies Hadamard transformations, queries the oracle, and applies interference to the input register. The final input measurement distinguishes the two classes in the ideal model.

The Python implementation evaluates the four possible one-bit Boolean functions and uses a reversible oracle mapping. Its classification is based on the final input bit, not on directly comparing the oracle's truth-table entries during the simulated algorithm.

This distinction matters. A classical implementation that inspects both values has already performed two evaluations. The quantum circuit models one oracle query under the promise and uses interference to extract the classification.

The result depends on the promise. The same circuit is not a general method for reconstructing arbitrary Boolean functions.

## Bernstein-Vazirani: Recovering a Hidden Bit String

The Bernstein-Vazirani problem defines a hidden bit string \(s\) and an oracle:

\[
f_s(x)=s\cdot x \pmod 2.
\]

The dot product is the parity of the bitwise products of \(s\) and \(x\). The algorithm prepares a superposition of input strings, encodes the parity into phase, and applies another Hadamard layer.

Interference concentrates the final input register on the hidden string. In the ideal model, one oracle query recovers \(s\).

The Python implementation validates the binary input, encodes the phase determined by the parity, and measures the transformed state. The example checks that the recovered bit string matches the supplied secret.

The Java and C++ files focus on different operational concerns rather than duplicating this implementation. The SQL schema records algorithm families, oracle contracts, resource limits, and experimental results that can be used to evaluate such algorithms consistently.

The query advantage relies on the oracle's specified structure. If the oracle does not implement the required parity function, the recovered string need not represent the intended secret.

## Grover Search: Amplitude Amplification

Grover search addresses an unstructured search space containing \(N\) candidates, of which \(M\) satisfy a Boolean predicate. The algorithm begins with a uniform superposition and alternates a phase oracle with a diffusion operation.

The phase oracle negates marked-state amplitudes. The diffusion operation reflects each amplitude about the mean:

\[
\alpha_x \longmapsto 2\bar{\alpha}-\alpha_x,
\qquad
\bar{\alpha}=\frac{1}{N}\sum_x\alpha_x.
\]

Repeated oracle and diffusion operations rotate the state toward the subspace containing marked candidates.

For an appropriate iteration count, the number of oracle calls is on the order of

\[
O\left(\sqrt{\frac{N}{M}}\right).
\]

When there is one marked item, this becomes \(O(\sqrt{N})\). A classical unstructured search requires \(O(N)\) evaluations in the worst case, or \(O(N/M)\) expected evaluations under a random-order model with multiple marked items.

The square-root relationship describes oracle queries, not total runtime. Too many Grover iterations can reduce the probability of measuring a marked state because the state continues rotating past the useful region. An unknown number of marked states also complicates the choice of iteration count.

### Python implementation

The Python script contains reusable state-vector operations, validation functions, measurement sampling, and three algorithm demonstrations.

Its Grover implementation uses a set of marked integer indices. The phase oracle negates their amplitudes, and the diffusion operator reflects the complete amplitude vector about its mean. A seeded random generator makes measurement sampling reproducible.

The state vector is normalized after operations, and invalid inputs raise a domain-specific exception. The script also reports logical resource estimates to distinguish the number of qubits and oracle queries from the number of amplitudes stored by the simulator.

A state-vector representation requires \(O(2^n)\) memory. Applying a full Hadamard layer with a butterfly transform requires \(O(n2^n)\) arithmetic operations. This exponential simulation cost makes the implementation useful for small circuits, not for simulating arbitrary large quantum computers.

### JavaScript implementation

The JavaScript file represents complex amplitudes as objects containing real and imaginary components. This makes the numerical operations explicit without relying on a third-party complex-number library.

Its event-driven `QuantumExperiment` class records preparation and measurement events. Consumers subscribe to event names, and the returned unsubscribe function removes a listener when it is no longer required.

The asynchronous experiment boundary is deliberately separate from the mathematical circuit. It illustrates how a simulation or remote execution service can publish structured experiment events without coupling the algorithm to reporting code.

The implementation includes phase-oracle operations, diffusion, probability validation, and Grover search. It uses idealized amplitudes and does not model gate noise, queue delays, hardware calibration, or actual remote quantum execution.

### C++ case study

The C++ program models a bounded diagnostic search over candidate software builds. Its `QuantumSearchEngine` owns the state-space dimension, creates a uniform initial state, applies a phase oracle and diffusion, and returns a `SearchReport`.

The report separates the number of qubits, search-space dimension, marked-state count, iteration count, most probable result, and total marked-state probability. This separation prevents the reported result from concealing the probability distribution or the resources used.

The state-vector size is limited before allocation. Invalid qubit counts, empty target sets, out-of-range target indices, and cases in which every candidate is marked are rejected explicitly.

The companion `RepositoryFaultDiagnosis` class evaluates a classical predicate over a collection of build identifiers. This provides an important engineering comparison: a classical predicate cannot be converted into a useful quantum oracle merely by labeling it a quantum operation. The predicate must be encoded as a reversible circuit with a cost that belongs in the resource analysis.

### Java enterprise model

The Java program treats quantum execution as a controlled experiment. `ExperimentPolicy` defines maximum qubit and shot counts. `Oracle` represents the marking predicate, while `StateVector` encapsulates state initialization, Hadamard transformations, phase changes, diffusion, probability calculations, and normalization checks.

`GroverService` validates the target set against the executable oracle before running the circuit. It rejects resource-policy violations and records an explicit `ExperimentStatus` in the result.

The model uses immutable result records and copies amplitude arrays when constructing transformed states. These choices help prevent unrelated service operations from modifying an existing experiment result.

The declared target set and executable oracle must agree. This validation catches a common source of misleading results: measuring a state that appears probable while the implemented predicate does not match the intended problem.

The program is a local ideal-state simulator. Its policy checks illustrate service boundaries, but they do not replace authorization, durable experiment storage, hardware-side enforcement, or independent scientific validation in a production service.

## Relational Experiment Model

The PostgreSQL script stores the information required to describe algorithms, circuits, oracle contracts, resource budgets, experiment states, and measured results.

| Table | Responsibility |
|---|---|
| `algorithms` | Stores the problem class, query model, complexity claims, and algorithm description. |
| `experiments` | Records qubit count, search-space size, shot budget, backend, and execution status. |
| `circuit_stages` | Records ordered circuit stages, target qubits, and estimated gate counts. |
| `oracle_contracts` | Records oracle type, reversibility, determinism, and verification evidence. |
| `resource_budgets` | Defines approved qubit, shot, and gate-count limits. |
| `experiment_results` | Stores measurement outcomes, target hits, query counts, duration, and verification status. |

Primary keys identify records, foreign keys maintain relationships, and check constraints reject invalid resource values and impossible measurement counts. A generated column derives the search-space dimension from the qubit count, while another generated column calculates the observed target-hit rate.

The `experiment_resource_report` view joins experiment metadata with circuit estimates and results. It provides a queryable record of measured performance without treating a high target probability as proof of algorithmic correctness.

### Database-enforced workflow

The experiment transition trigger prevents a terminal experiment from being silently restarted, requires oracle validation before the validated state, and restricts completion to an experiment that was running.

The result-validation trigger verifies that the measured basis index fits the experiment's state space, that observed shots remain within the approved budget, and that results are associated with an active execution state.

The demonstration transaction creates the schema, inserts an experiment and its circuit stages, validates the oracle record, starts execution, records a result, and marks the experiment completed. The result record is illustrative data from an idealized experiment, not a claim about measured quantum hardware.

The schema intentionally separates a recorded result from the verification decision. The application must still establish that the oracle, circuit, measurement procedure, and classical interpretation satisfy the problem contract.

## Interpreting Quantum Complexity Correctly

Quantum and classical complexity comparisons require matching assumptions. A query-complexity result assumes that access to the oracle is counted consistently and that the problem's input promise is respected.

A practical comparison should consider:

- **Oracle construction:** A complicated predicate may require many gates or substantial reversible computation.
- **Circuit depth:** Operations must be scheduled while respecting dependencies and hardware connectivity.
- **Measurement shots:** Finite sampling introduces uncertainty in estimated probabilities.
- **Noise and error correction:** Physical circuits can deviate from ideal unitary evolution.
- **Classical verification:** A measured candidate may require a separate classical check.
- **Simulation memory:** A state-vector simulator stores exponentially many amplitudes even when the quantum circuit uses a modest number of gates.

These costs explain why an improvement in oracle-query complexity does not guarantee a practical speedup for every search task.

## Edge Cases and Correctness Boundaries

A valid simulation must reject states that are not normalized, invalid basis indices, empty oracle target sets, and malformed bit strings. Resource limits must be checked before attempting exponential memory allocations.

A quantum oracle must implement the promised function. An incorrect predicate can produce a mathematically valid circuit whose output answers the wrong problem.

Grover search requires care when the number of marked states is unknown. The standard iteration formula assumes that this quantity is known or estimated. If the iteration count is poorly chosen, the target probability may be substantially lower than expected.

For noisy execution, a single measurement is not a reliable estimate of the output distribution. Repeated shots, uncertainty analysis, calibration, and independent verification are needed. A simulator's exact probabilities should not be confused with empirical hardware frequencies.

## Performance and Production Considerations

The provided simulators are designed for clarity and small problem instances. They use explicit state vectors, and the classical data structures hold candidate indices directly. This makes the oracle and diffusion mechanisms easy to inspect but places a strict limit on scalable simulation.

A production experiment system should record circuit versions, oracle verification results, backend identity, shot counts, calibration context, execution timestamps, resource estimates, and the method used to verify outputs. Failed and incomplete experiments should remain distinguishable from completed experiments.

The database triggers enforce selected integrity rules, but database constraints cannot prove that a submitted quantum circuit implements a correct oracle. That requires circuit-level verification or testing against a trusted specification.

The central technical distinction is between the mathematical algorithm, the oracle that encodes the problem, the circuit that realizes the algorithm, and the execution system that returns a classical result. Reliable quantum algorithm engineering requires all four to agree.
