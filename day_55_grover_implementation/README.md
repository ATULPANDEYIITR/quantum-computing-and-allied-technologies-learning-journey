# Grover Search: Implementation and Optimization

## Purpose

Grover's algorithm searches an unstructured space of \(N=2^n\) candidate states using quantum amplitude amplification. When the search oracle identifies \(M\) marked states, an appropriately chosen number of Grover iterations raises the probability of measuring a marked state.

The core distinction is between the number of oracle queries and the cost of implementing each query. Grover's algorithm uses \(O(\sqrt{N/M})\) oracle queries for a suitable marked-state count, but practical runtime also depends on oracle construction, circuit depth, hardware noise, and measurement repetition.

The implementations use state-vector simulation. They demonstrate amplitude amplification mathematically; they do not execute quantum circuits on physical quantum hardware.

## Mathematical Model

For \(n\) qubits, the computational basis contains \(N=2^n\) states. The initial uniform superposition is

\[
|s\rangle=\frac{1}{\sqrt{N}}\sum_{x=0}^{N-1}|x\rangle.
\]

Each basis state begins with amplitude \(1/\sqrt{N}\) and probability \(1/N\).

The algorithm applies two operations repeatedly.

### Phase oracle

The oracle marks states by changing their amplitude signs:

\[
O_f|x\rangle=(-1)^{f(x)}|x\rangle,
\]

where \(f(x)=1\) for a marked state and \(f(x)=0\) otherwise.

The oracle does not directly reveal which state is marked. Its implementation depends on the search predicate and can dominate practical circuit cost.

### Diffusion operator

The diffusion operator is

\[
D=2|s\rangle\langle s|-I.
\]

It reflects the amplitude vector about its mean amplitude. Combined with the phase oracle, this operation transfers probability mass toward marked states.

For a real amplitude vector, the diffusion update is

\[
a'_x=2\bar a-a_x,
\]

where \(\bar a\) is the mean of all amplitudes.

### Iteration count

Define

\[
\theta=\arcsin\sqrt{\frac{M}{N}}.
\]

A commonly used near-optimal iteration count is

\[
k\approx \operatorname{round}
\left(\frac{\pi}{4\theta}-\frac12\right).
\]

The success probability after \(k\) ideal iterations is

\[
P_{\mathrm{success}}=\sin^2((2k+1)\theta).
\]

For one marked state among sixteen candidates, three iterations yield a success probability of approximately \(0.9613\). A measurement can still return an unmarked state.

When \(M\) is unknown, selecting an iteration count from the formula is not possible without estimating the number of solutions. Adaptive or randomized iteration strategies can address this limitation.

## Algorithm Workflow

    Candidate space
          |
          v
    Uniform superposition
          |
          v
    Phase oracle
          |
          v
    Diffusion operator
          |
          v
    Repeat selected iterations
          |
          v
    Measure a basis state
          |
          v
    Verify candidate against the search predicate

Measurement converts a quantum state into a classical result. A production search system should verify the measured candidate independently when the predicate permits it. Failed measurements can require another execution.

## Python Implementation

The Python script defines an immutable `SearchResult` data class and a `GroverSearch` state-vector simulator.

Its principal mechanisms are:

- A list of floating-point amplitudes representing the computational basis.
- A phase oracle that negates amplitudes for marked integer states.
- A diffusion operation that reflects amplitudes about their mean.
- An iteration-selection function using the number of marked states.
- A probability calculation that sums squared amplitudes over marked states.
- A measurement routine that samples from the probability distribution using a seeded pseudorandom generator.

The script also provides a classical linear-search baseline. Assertions check the expected iteration count, success probability, and state normalization.

The simulator limits the qubit count to twenty. Its state vector contains \(2^n\) amplitudes, so memory and computation grow exponentially with qubit count. This restriction is a resource safeguard, not a theoretical limitation of Grover's algorithm.

The seeded random generator makes experiments reproducible. It is suitable for simulation, not cryptographic randomness or physical quantum measurement.

## JavaScript Implementation

The JavaScript version uses a `Float64Array` for amplitude storage. This provides compact, indexed numerical storage suitable for repeated updates.

A `Set` represents marked states, avoiding duplicate targets and providing efficient membership checks. The implementation separates oracle application, diffusion, probability evaluation, and measurement into distinct methods.

The batch runner performs repeated experiments in bounded batches and yields to the Node.js event loop with `setImmediate`. This allows other event-loop work to proceed between batches, although the numerical loops themselves execute synchronously.

The seeded linear congruential generator provides reproducible simulated measurements. It is not a cryptographically secure random generator. The imported Node.js cryptographic random utility is not required by the simulation and can be omitted without changing the algorithm.

Validation rejects invalid qubit counts, empty target sets, out-of-range states, and invalid iteration counts. Batch limits prevent an accidental request from launching an unbounded workload.

## C++17 Implementation

The C++ program treats the search engine as a dedicated numerical component. It uses a `std::vector<double>` to hold amplitudes and STL algorithms for summation, sorting, duplicate detection, and probability normalization.

The engine validates the marked-state list before executing the search. Sorting the targets enables duplicate detection and binary search during result verification. Invalid targets raise exceptions rather than silently accessing an invalid array position.

The implementation uses deterministic midpoint sampling instead of random measurement. This makes the example reproducible, but it is not a substitute for sampling from a physical quantum system. The reported measured state depends on the cumulative probability distribution and the fixed threshold.

The normalization check detects numerical errors or incorrect amplitude updates. For the supported ideal operations, the squared amplitudes should sum to one, subject to floating-point precision.

The C++ implementation illustrates how low-level numerical control and explicit resource limits can support a compact simulation engine. It still requires exponential memory and does not simulate gate-level noise.

## Java 17 Implementation

The Java program separates execution policy from search behavior.

`SearchPolicy` is a record containing the maximum supported qubit count, iteration limit, and normalization tolerance. Its constructor validates the policy so invalid configurations cannot be created.

`SearchReport` is an immutable record containing the search dimensions, target states, iteration count, success probability, measured result, and execution status. The target list is defensively copied to prevent callers from modifying a completed report.

`SearchService` owns iteration selection, target validation, amplitude updates, normalization checks, and report creation. `SearchException` represents an execution failure that cannot be treated as a valid search result.

The implementation uses `Set<Integer>` for the requested targets and a `TreeSet` to produce a stable, sorted representation. The simulation uses a Java primitive array for amplitudes to avoid unnecessary object allocation in the numerical loop.

The enterprise-oriented policy boundary separates allowed execution parameters from algorithm mechanics. A deployed service could extend this boundary with authenticated requests, execution quotas, audit records, and hardware-specific configuration. Those services are not implemented in this standalone example.

The deterministic sampling method is intended for reproducibility. Real quantum hardware or a probabilistic simulator must supply measurements appropriate to its execution model.

## PostgreSQL Data Model

The PostgreSQL script records experiment configuration, marked states, execution results, and event history.

| Table | Purpose |
|---|---|
| `algorithms` | Identifies search algorithms and their stated query complexity |
| `experiments` | Stores qubit counts, state-space size, marked-state count, and requested iterations |
| `marked_states` | Records the target states for each experiment |
| `execution_runs` | Stores iteration counts, measured states, probabilities, normalization values, and outcomes |
| `execution_events` | Records execution lifecycle events and diagnostic details |

The generated `state_count` column derives the search-space size from the qubit count. Check constraints enforce valid qubit counts, target counts, iteration ranges, probability ranges, and execution statuses.

A trigger validates each marked state against its experiment's state-space size. Another trigger validates measured states and requires marked-state records for completed executions.

The `recommended_iterations` function implements the mathematical iteration formula. The `experiment_report` view combines experiment configuration with execution counts, failures, and average success probability.

The demonstration records are illustrative simulator data. They are not measurements obtained from quantum hardware.

The script creates indexes for experiment-specific execution history, event lookup, and failed-run investigation. These indexes support the reporting and diagnostic queries while adding storage and write overhead.

A transaction groups schema and sample-data changes. A savepoint demonstrates how an invalid target insertion can be rejected without invalidating the surrounding transaction. The trigger and table constraints enforce separate parts of the data-integrity contract.

The relational model stores reported success probabilities; it does not derive them from quantum state vectors inside SQL. Numerical simulation belongs in the application layer, while PostgreSQL preserves configurations, measurements, and audit evidence.

## Optimization Considerations

### Select an appropriate iteration count

Too few iterations leave substantial probability on unmarked states. Too many can reduce success probability because amplitude amplification is periodic rather than monotonically increasing.

The recommended count assumes an ideal oracle, a uniform initial state, and a known number of marked states. Hardware noise and imperfect gates can change the practical optimum.

### Reduce oracle cost

The theoretical query advantage does not guarantee a wall-clock speedup. An expensive oracle can require many gates, ancillas, and circuit layers. Oracle design should account for reversible computation, uncomputation, connectivity, and the cost of evaluating the marking predicate.

### Control simulation resources

A full state-vector simulator stores \(2^n\) amplitudes. Memory is \(O(2^n)\), and each Grover iteration takes \(O(2^n)\) time in these implementations. Repeated executions multiply the simulation cost.

Increasing the qubit limit without a resource estimate can cause excessive memory consumption or long runtimes.

### Account for measurement and noise

The ideal probability distribution assumes unitary operations and perfect measurement. On real devices, gate errors, decoherence, and readout errors can reduce the observed success rate.

Repeated measurements estimate success frequency. The number of shots should be chosen according to the required statistical precision and available execution budget.

### Verify results independently

A high success probability is not a guarantee that every measured state is correct. When the search predicate is available classically, verify the candidate after measurement. Record unsuccessful executions separately from invalid configurations and infrastructure failures.

## Validation and Failure Conditions

The source files reject invalid qubit counts, empty target sets, out-of-range target states, and invalid iteration counts. They also check probability normalization.

The database adds integrity constraints for experiment dimensions, marked states, execution status, measured-state bounds, and failure descriptions.

Important distinctions include:

- **Invalid configuration:** the requested search cannot be executed under the declared rules.
- **Numerical failure:** the simulated state does not satisfy the normalization tolerance.
- **Unsuccessful measurement:** execution completes, but the sampled state is not marked.
- **Low success probability:** the execution is valid, but the chosen iteration count or implementation does not provide the desired amplification.
- **Hardware failure:** a real device may fail or return noisy measurements independently of the ideal algorithm.

These conditions should remain distinct in operational reporting. A failed search outcome is not automatically evidence of a software defect.

## Limitations

The five implementations use ideal, real-valued amplitude vectors. They do not model complex-valued phase evolution, quantum gates at the circuit level, noise channels, physical qubit connectivity, transpilation, or device calibration.

Their deterministic or seeded measurement routines are simulation choices. They should not be interpreted as physical quantum measurements or security guarantees.

The iteration formula is an approximation for selecting a useful integer number of Grover iterations. It is not a universal optimizer for noisy hardware, expensive oracles, unknown target counts, or nonuniform initial states.

The implementations focus on amplitude amplification and experiment validation. They provide a foundation for studying the algorithm's mechanics, its computational scaling, and the engineering decisions needed to evaluate search performance.
