# Amplitude Amplification and Generalized Quantum Search

## Scope

This project models amplitude amplification as a generalized quantum-search mechanism in which a quantum state is rotated toward a marked subspace.

The central distinction is between the size of the search space and the number of valid answers:

- `N` is the total number of basis states.
- `M` is the number of marked states.
- The initial probability of observing a marked state is `M/N`.
- The marked and unmarked subspaces form a two-dimensional representation of the amplification process.
- If `theta` satisfies `sin²(theta) = M/N`, one amplification iteration rotates the state by `2theta`.
- After `k` iterations, the ideal marked-state probability is `sin²((2k+1)theta)`.

The generalized case is therefore not restricted to one solution. When several states satisfy the oracle, the iteration count scales approximately as `O(sqrt(N/M))`.

The five implementations approach the same subject from different engineering perspectives.

## Conceptual Model

A generalized search can be represented as:

`Uniform superposition → Oracle phase marking → Diffusion/reflection → Amplitude rotation → Measurement`

The implementation treats the oracle as a predicate that separates the Hilbert space into two subspaces:

```text
                    Full search space
                           |
             +-------------+-------------+
             |                           |
        Unmarked states             Marked states
             |                           |
          amplitude                  amplitude
             |                           |
             +-------------+-------------+
                           |
                    amplification
                           |
                    higher marked
                      probability
```

The relevant two-dimensional state can be written conceptually as:

`|psi> = sin(theta)|good> + cos(theta)|bad>`

The oracle changes the phase of the good component. The diffusion operation reflects amplitudes around their average. Their combination produces the rotation responsible for amplification.

## Standard and Generalized Search

| Property | Standard search | Generalized search |
|---|---|---|
| Marked states | Usually one | One or more |
| `M` | `1` | `M >= 1` |
| Initial success probability | `1/N` | `M/N` |
| Approximate iterations | `O(sqrt(N))` | `O(sqrt(N/M))` |
| Main input | One target predicate | Marked-state predicate |
| Practical issue | Target identification | Unknown or multiple solutions |

The implementations explicitly retain `M` rather than assuming it is one.

When `M = N`, every state is marked and no amplification is necessary. The initial measurement probability is already one. This is an important boundary condition because blindly applying the usual iteration estimate can produce an unnecessary rotation.

## Python Implementation

The Python program uses a domain-oriented model built from dataclasses, an enumeration for search mode, validation functions, and explicit exception handling.

`SearchProblem` stores the number of qubits, marked states, and desired success threshold. Validation ensures that marked states fit inside the search space.

`initial_angle()` calculates the two-dimensional rotation angle from `M/N`.

`success_probability()` implements the analytical amplification relation:

`P(k) = sin²((2k+1)theta)`

`optimal_iterations()` evaluates the integer candidates around the continuous optimum rather than assuming that rounding in one direction is always correct.

`simulate_amplification()` creates an explicit trajectory containing good-subspace amplitude, bad-subspace amplitude, and success probability.

The program also compares several values of `M` for a fixed `N`. This makes the generalized scaling visible without constructing an exponentially large state vector.

The measurement function is deliberately deterministic because this is a software model rather than a quantum-device execution. A physical measurement would sample from the final probability distribution.

### Python Edge Cases

The implementation checks:

- Invalid qubit counts.
- Empty marked sets.
- Marked states outside the search domain.
- Invalid probability thresholds.
- Negative iteration counts.
- The all-states-marked case.
- Generalized searches with several valid states.

The maximum simulated qubit count is restricted to 20 so that integer-based state indexing remains practical and unambiguous in a standard-library-only program.

## JavaScript Implementation

The JavaScript implementation uses an event-driven architecture.

`SearchProblem` validates the domain and stores marked states in a `Set`, providing efficient membership semantics.

`AmplitudeAmplifier` owns the mathematical model. It exposes:

- `probability()`
- `state()`
- `optimalIterations()`
- `firstThresholdIteration()`
- `trajectory()`

`SearchSession` separates execution from observation. Consumers can subscribe to `started`, `iteration`, and `completed` events.

The session uses asynchronous event-loop yielding with `setImmediate`. This is useful when the same computational model is connected to telemetry, a user interface, a logging pipeline, or another asynchronous consumer.

The implementation does not require npm packages.

### JavaScript Design Decision

The event-driven layer is intentionally separate from the amplification mathematics. This avoids mixing policy, computation, and telemetry into one class.

A failed event listener is isolated from the main search operation. This prevents one observer from terminating the entire session.

Input validation also prevents invalid numeric states from silently entering the calculation.

## C++17 Implementation

The C++ program uses a technical case-study structure containing:

- Search parameters.
- A generalized amplitude-amplification engine.
- Amplification trajectory records.
- Repository-governance structures.
- Review states.
- Status checks.
- Branch protection policies.
- Merge eligibility evaluation.

The amplification engine validates the Hilbert-space dimension and computes the same two-dimensional rotation analytically.

The C++ implementation uses STL containers such as `std::set` and `std::vector`. `std::set` provides deterministic ordering for marked states and prevents duplicate targets.

The repository-governance portion is a separate engineering scenario illustrating how a repository can evaluate a proposed change through explicit conditions such as approvals, status checks, synchronization, conflicts, and unresolved conversations.

The two domains are deliberately not collapsed into one abstraction. The quantum engine computes search probabilities, while the governance engine demonstrates explicit rule evaluation.

### C++ Performance Considerations

The generalized search model does not allocate a vector of size `2^n`. Instead, it stores only `N`, `M`, and the analytical angle.

This makes the mathematical simulation effectively constant-space with respect to the full quantum state representation.

A real state-vector simulator would require memory proportional to `2^n` complex amplitudes. The analytical model avoids that cost because it exploits the symmetry of amplitude amplification.

## Java 17 Implementation

The Java implementation emphasizes enterprise domain modeling.

`SearchProblem` is a record that validates immutable search configuration.

`AmplificationStep`, `Review`, `StatusCheck`, and `BranchProtectionPolicy` are also modeled as records where immutable value semantics are appropriate.

The `PullRequest` class represents explicit mutable workflow state. It controls state transitions rather than allowing arbitrary external modification.

The `MergeEligibility` record captures both the final decision and the reasons for rejection. This is useful in operational systems because a Boolean result alone does not explain why a workflow cannot proceed.

### Approval Semantics

The Java model distinguishes several concepts:

- A review can be approved.
- A reviewer can be ineligible.
- An approval can become stale.
- A change request is not an approval.
- A dismissed review cannot satisfy an approval requirement.
- Distinct eligible reviewers are counted rather than counting duplicate review records.

The merge service also evaluates status checks, synchronization, conversations, conflicts, and linear-history requirements.

This makes approval one input to merge eligibility rather than treating approval as synonymous with permission to merge.

## PostgreSQL Implementation

The PostgreSQL schema stores both quantum-search data and an operational governance case.

The quantum portion contains:

`search_problem → marked_state → search_experiment → amplification_step`

This represents a problem definition, its oracle-marked states, an execution attempt, and the resulting amplification trajectory.

`search_problem` stores the number of qubits and search mode.

`marked_state` stores each valid marked basis state.

`search_experiment` represents execution state and requested iteration count.

`amplification_step` stores the analytical trajectory for each iteration.

`search_policy` stores operational probability and iteration limits.

### Database Constraints

The schema uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enum types.
- Indexes.
- Triggers.
- Views.
- A stored function.

The `validate_marked_state()` trigger prevents an oracle from marking a state outside the dimension represented by the configured qubit count.

For `n` qubits, valid basis-state indices are:

`0 <= state < 2^n`

The trigger enforces that invariant at the database boundary rather than depending exclusively on application validation.

### Stored Calculation

`calculate_optimal_iterations()` calculates the continuous optimum and evaluates the nearby integer candidates.

This is preferable to assuming that a floating-point estimate can simply be rounded in one fixed direction.

### Reporting Views

`problem_statistics` reports:

- Search dimension.
- Search mode.
- Number of marked states.
- Initial success probability.
- Optimal iteration count.

`best_experiment_results` identifies the highest observed ideal success probability for each experiment.

`merge_eligibility` demonstrates relational policy evaluation for the separate repository-governance scenario.

## Failure and Boundary Conditions

Several cases require special handling.

### No Marked States

Amplitude amplification requires a non-empty marked subspace. If `M = 0`, there is no target probability to amplify.

The source implementations reject this configuration.

### All States Marked

When `M = N`, the initial state is already entirely within the marked subspace.

Therefore:

`P(0) = 1`

No amplification iteration is required.

### Multiple Marked States

The generalized algorithm uses:

`theta = arcsin(sqrt(M/N))`

Increasing `M` increases the initial marked probability and reduces the number of iterations needed to reach a high probability.

### Overshooting

Amplitude amplification is oscillatory. Increasing the iteration count indefinitely does not monotonically increase the success probability.

The probability follows:

`P(k) = sin²((2k+1)theta)`

Consequently, an iteration count that is too large can move the state away from the marked subspace.

This is why the implementations calculate an approximately optimal iteration count rather than repeatedly amplifying until an arbitrary counter expires.

### Unknown Number of Solutions

The formulas assume that `M` is known when selecting the optimal iteration count.

If `M` is unknown, practical generalized-search algorithms need a strategy for estimating or adapting to the number of solutions. The five files model the known-`M` analytical case and do not claim to solve unknown-`M` search automatically.

## Complexity

For a search space of size `N` with `M` marked states, amplitude amplification requires approximately:

`O(sqrt(N/M))`

oracle applications in the ideal known-`M` setting.

For one marked state:

`M = 1`

so the complexity becomes:

`O(sqrt(N))`

Classical exhaustive search requires up to `O(N)` oracle evaluations in the worst case.

The implementations calculate the amplification trajectory without materializing all `N` amplitudes. Their analytical simulation therefore avoids the memory requirements of a full state-vector simulator.

The actual quantum algorithm's cost must still account for the cost of implementing the oracle and reflection operations. A theoretical reduction in query complexity does not automatically imply a lower end-to-end cost if the oracle is expensive.

## Security and Correctness Considerations

A quantum-search oracle is a critical component of the algorithm. Incorrect oracle construction changes the marked subspace and therefore changes the algorithm's result.

The implementations validate state boundaries before performing calculations.

For operational systems, important controls include:

- Strict validation of oracle inputs.
- Deterministic configuration records.
- Immutable problem definitions where practical.
- Explicit failure states.
- Separation of policy evaluation from computational state.
- Transactional persistence of experiment results.
- Database constraints for invariant enforcement.
- Audit-friendly experiment records.

The PostgreSQL transaction example demonstrates that execution-state changes can be committed atomically. The failure example is rolled back deliberately so the sample dataset remains repeatable.

## Relationship Between the Implementations

The common mathematical model is:

`M/N → theta → repeated reflection → amplitude rotation → measurement probability`

The engineering perspectives differ:

| Implementation | Primary perspective | Main mechanism |
|---|---|---|
| Python | Analytical simulation | Dataclasses, validation, trajectory generation |
| JavaScript | Event-driven execution | Classes, Sets, events, Promises |
| C++17 | Technical engine | STL, value structures, validation, policy evaluation |
| Java 17 | Enterprise domain model | Records, state transitions, immutable values, services |
| PostgreSQL | Persistent relational workflow | Constraints, triggers, functions, views, transactions |

## Practical Interpretation

Amplitude amplification is best understood as a probability-redistribution mechanism rather than a generic method for making every computation faster.

Its advantage arises from reducing the number of oracle queries required to locate a marked state in an unstructured search space.

The generalized form is particularly important because many practical problems have multiple acceptable answers. The relevant parameter is not only the search-space size `N`, but also the number of marked solutions `M`.

The key distinction is therefore:

`Classical exhaustive search: approximately N queries`

versus

`Amplitude amplification: approximately sqrt(N/M) queries`

under the appropriate oracle and quantum-operation assumptions.

The implementations preserve that distinction while handling validation, state transitions, failure conditions, database integrity, event processing, and realistic operational constraints.
