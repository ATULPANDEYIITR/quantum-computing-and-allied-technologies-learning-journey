# Superdense Coding and Quantum Communication

## Scope

This project studies **superdense coding** as a concrete quantum communication protocol. The central distinction is between the logical information Alice wants to communicate, the quantum resource shared before communication begins, the qubit physically transmitted during the protocol, and Bob's measurement process.

Superdense coding uses a pre-shared entangled Bell pair. Alice applies one of four local operations to her qubit to encode one of four possible two-bit messages. She then sends her qubit to Bob. Bob performs a Bell-basis decoding operation and measures the two-qubit system.

The protocol therefore demonstrates a specific relationship between entanglement and communication capacity:

- The logical payload contains two classical bits.
- There are four possible payloads: `00`, `01`, `10`, and `11`.
- Alice transmits one qubit during the communication stage.
- The second qubit is not created during transmission. It is part of the entangled resource established beforehand.
- Bob's decoding works because the four encoded messages correspond to four distinguishable Bell states.

The implementations model this protocol at several levels without treating quantum communication as ordinary classical message passing.

## Core Quantum Communication Model

A quantum communication system differs from a conventional bit channel because a qubit can exist in a superposition and multiple qubits can possess correlations that cannot be represented as independent classical probabilities.

For superdense coding, Alice and Bob initially share the Bell state

`|Φ+> = (|00> + |11>) / √2`.

Alice controls the first qubit and Bob controls the second.

The protocol uses four transformations:

| Alice's payload | Alice's operation | Resulting Bell state |
| --- | --- | --- |
| `00` | `I` | `|Φ+>` |
| `01` | `X` | `|Ψ+>` |
| `10` | `Z` | `|Φ->` |
| `11` | `ZX` | `|Ψ->` up to a physically irrelevant global phase |

The four states form an orthogonal Bell basis. Orthogonality is the critical property that allows Bob to distinguish the encoded messages after receiving Alice's qubit.

## Entanglement as a Communication Resource

Entanglement is not equivalent to a classical data channel.

The Bell pair must first be distributed between Alice and Bob. Once that shared resource exists, Alice can encode two classical bits by operating only on her half of the pair.

The communication phase still requires Alice's qubit to physically reach Bob. Superdense coding therefore does not allow Alice to communicate information instantaneously merely because the two parties share entanglement.

This resource accounting is important when evaluating claims about quantum communication. The result is a higher information capacity per transmitted qubit under the protocol's resource assumptions, not unlimited communication capacity.

## Encoding and Decoding Mechanics

Alice's four possible operations are represented by the identity and Pauli transformations.

`I` leaves the Bell pair unchanged.

`X` flips the computational basis value of Alice's qubit. Applied to `|Φ+>`, it produces `|Ψ+>`.

`Z` changes the phase associated with the `|11>` component. Applied to `|Φ+>`, it produces `|Φ->`.

`ZX` produces the fourth Bell state, differing from the conventional `Y` representation only by a global phase for measurement purposes.

Bob performs the inverse of Bell-state preparation:

`CNOT(q0 → q1)` followed by `H(q0)`.

This maps the Bell basis back into the computational basis. Measurement can then distinguish the four payloads.

The important mechanism is therefore not simply that Alice "sends two bits using one qubit." The protocol works because the pre-shared entangled state provides four orthogonal joint states that Alice can select using local operations.

## Python Implementation

The Python program implements a quantum-state simulator without requiring a quantum-computing package.

The state is represented as a four-element complex vector corresponding to `|00>`, `|01>`, `|10>`, and `|11>`. Matrices represent the quantum gates, and tensor products expand single-qubit operations into the two-qubit Hilbert space.

`create_bell_pair()` constructs the shared `|Φ+>` state by applying a Hadamard operation to Alice's qubit and then applying CNOT.

`alice_encode()` maps each two-bit message to its corresponding operation.

`bob_decode()` applies the Bell-basis decoding circuit.

`measure()` samples from the calculated probability distribution instead of simply returning the expected answer. This preserves the probabilistic nature of quantum measurement.

The program also verifies state normalization, which is an important debugging invariant because valid quantum evolution preserves total probability.

The noise simulation applies a simple Pauli-channel model to the transmitted qubit. Increasing the error probability reduces the observed decoding accuracy, demonstrating why real quantum communication requires physical error management rather than assuming ideal state transfer.

## JavaScript Implementation

The JavaScript implementation models superdense coding as an asynchronous communication service.

The state-vector operations use JavaScript arrays and complex-number objects. The protocol is organized around `QuantumChannel` and `SuperdenseCodingSession`.

`QuantumChannel` extends `EventTarget`, allowing transmission events to be observed independently of the protocol logic. The asynchronous `transmit()` method represents a channel boundary without claiming to reproduce physical propagation latency.

`SuperdenseCodingSession` separates the communication stages into shared-state creation, Alice's encoding, channel transmission, Bell-basis decoding, and measurement.

The event-driven design is useful for quantum communication software because a real communication system may need to record transmission initiation, channel completion, error information, decoding, and measurement results as separate operational events.

The implementation also models channel noise asynchronously. The noisy channel can apply an `X`, `Z`, or `XZ` error to the transmitted qubit.

## C++ Case Study

The C++ program treats superdense coding as a communication subsystem.

The state vector is represented by `std::vector<std::complex<double>>`, while matrices represent quantum transformations. The implementation uses explicit matrix multiplication and tensor products so that the relationship between single-qubit gates and the full two-qubit state remains visible.

The case study separates the following responsibilities:

- Bell-pair creation establishes the precondition for communication.
- Message validation prevents unsupported payloads from entering the protocol.
- `Encoding` associates a two-bit payload with the local gate Alice must apply.
- Channel noise is applied only during the simulated transmission stage.
- Bell-basis decoding reconstructs the computational representation.
- Measurement converts the quantum state into the received classical payload.
- `Transmission` records sent payload, encoding operation, received payload, and success.

This separation makes the physical stages of the protocol explicit rather than hiding the entire operation behind a single function.

The noise study evaluates the system at several error probabilities. The resulting accuracy is empirical because measurement and channel errors are sampled using a pseudorandom generator.

The implementation also checks invalid messages, zero states, and unnormalized states. These are useful failure conditions for a simulator because silently accepting an invalid quantum state can produce results that look plausible while violating the mathematical model.

## Java Enterprise-Oriented Model

The Java implementation represents the protocol through domain-oriented types.

`Message` is an enum containing the four valid two-bit payloads. This prevents arbitrary strings from being treated as valid protocol messages.

`Gate` represents the encoding operation as a domain value rather than a raw string.

`QuantumState` encapsulates amplitudes, normalization, probability calculation, and state description.

`QuantumChannel` owns the channel error policy and applies errors only during transmission.

`CommunicationService` coordinates the protocol while keeping the channel as a separate dependency. This separation makes channel behavior replaceable and makes reliability experiments possible without changing the encoding or decoding algorithm.

The `Transmission` record provides an immutable representation of a completed protocol attempt. Its fields make the distinction between the message Alice intended to send and the bits Bob actually measured explicit.

The Java model therefore represents quantum communication as a sequence of domain state transformations rather than as a collection of unrelated gate demonstrations.

## SQL Data Model

The PostgreSQL implementation models the communication domain relationally.

`communication_party` identifies the sender and receiver.

`entangled_pair` records the pre-shared Bell resource. Its sender and receiver relationships make the ownership of the two halves explicit.

`quantum_channel` records channel configuration and its modeled noise probability.

`logical_message` defines the four legal two-bit payloads and their encoding operations. The check constraint prevents values outside the superdense-coding message space.

`transmission` represents a communication attempt and connects the entangled resource, channel, payload, sender, and receiver.

`channel_error` records errors introduced during transmission.

`decoding_event` records Bob's Bell-basis decoding and observed measurement.

`communication_audit` stores an operational event trail using PostgreSQL's `JSONB` type for structured event details.

The schema uses foreign keys to preserve relationships and check constraints to enforce domain rules at the database layer.

The indexes on channel/time, message identifiers, measured values, and transmission audit history support common operational queries without indexing every column indiscriminately.

## Relational Representation of Noise

The SQL model intentionally separates the intended payload from the measured payload.

A transmission can contain message `01` while the decoding event records `11`. The difference is meaningful: it indicates that the communication system observed a result different from Alice's intended logical payload.

The `transmission_outcomes` view evaluates this relationship through `decoded_correctly`.

This avoids a common modeling error in which the database stores only the expected value and therefore cannot represent communication failures.

## Transactional Resource Handling

The SQL transaction demonstrates resource consumption for an entangled pair.

An entangled pair is a prerequisite resource rather than an unlimited reusable database record. The example updates `consumed_at` only for a completed decoded transmission.

This does not attempt to model every physical rule governing entanglement. Instead, it illustrates how a software system can distinguish an available communication resource from one that has already participated in a protocol transaction.

A production system would need stronger concurrency controls if multiple workers could attempt to consume the same quantum resource simultaneously. Row locking, idempotency keys, and explicit transaction isolation would become relevant at that boundary.

## Measurement and Probability

For a normalized state vector with amplitudes `α_i`, the probability of measuring basis state `i` is `|α_i|²`.

The implementations calculate these probabilities explicitly before sampling a measurement result.

In the ideal superdense-coding circuit, the Bell-basis decoding produces a computational basis state with probability one for the intended message. Consequently, repeated ideal simulations recover the transmitted payload consistently.

When noise is introduced, multiple outcomes can become possible. The simulation then produces an empirical decoding accuracy rather than treating the expected payload as guaranteed.

## Quantum Communication Versus Classical Communication

Classical communication represents information through classical states such as zero and one. A classical channel can copy and inspect classical information without changing the information's physical representation in the way quantum measurement can disturb an unknown quantum state.

Quantum communication uses quantum states as communication resources. Superdense coding is a particularly useful example because the protocol's advantage depends on entanglement and joint-state measurement.

The protocol should not be described as ordinary compression. Alice is not taking an arbitrary two-bit classical file and losslessly compressing it into one independent qubit. Instead, the one transmitted qubit is combined with a second qubit that was already entangled with it.

## Noise and Failure Modes

The ideal protocol assumes perfect gates, perfect entanglement, perfect transmission, and perfect measurement.

Real quantum communication systems face substantially more difficult conditions.

Channel noise can alter the transmitted state.

Gate errors can change the encoded Bell state before transmission.

Measurement errors can cause Bob to infer the wrong classical payload even when the quantum state arriving at Bob is correct.

Loss can prevent a qubit from arriving at all.

Decoherence can destroy useful quantum correlations before decoding.

Entanglement distribution itself can fail before Alice has any payload to send.

The simulations model only a small subset of these effects. The Pauli-channel model is useful for demonstrating protocol sensitivity but should not be mistaken for a complete physical model of a quantum communication link.

## Security and Information-Theoretic Boundaries

Superdense coding is an information-capacity protocol, not by itself an encryption algorithm.

The fact that the transmitted object is a qubit does not mean the message automatically has confidentiality against every possible attacker.

A real quantum communication architecture requires explicit treatment of authentication, entanglement distribution, channel integrity, device trust, measurement assumptions, and the security model relevant to the application.

Entanglement also does not enable faster-than-light classical signalling. Bob cannot recover Alice's selected message until the appropriate quantum system reaches him and the joint decoding operation can be performed.

## Performance Characteristics

The educational simulators represent a two-qubit state using four amplitudes and a four-by-four matrix for two-qubit operations.

For this small system, direct matrix multiplication is simple and transparent.

State-vector simulation becomes expensive as the number of qubits increases because a general pure state requires `2^n` complex amplitudes for `n` qubits.

A direct dense matrix representation is even more expensive because an `n`-qubit operator can contain `2^n × 2^n` entries.

Real quantum software therefore uses specialized representations, circuit decompositions, sparse structures where applicable, tensor-network methods for suitable workloads, or actual quantum processors.

The code intentionally favors mathematical visibility over large-scale simulation performance.

## Common Modeling Mistakes

Treating entanglement as a classical shared secret misses the quantum nature of the protocol. The Bell pair is a joint quantum state.

Counting the pre-shared entangled qubit as though it were transmitted during Alice's communication step gives an incorrect description of the communication resource accounting.

Treating measurement as a deterministic database lookup hides the probabilistic nature of quantum mechanics.

Assuming that every transmitted qubit arrives unchanged ignores the distinction between an ideal protocol and a physical communication channel.

Assuming that superdense coding provides encryption confuses information capacity with confidentiality.

Assuming that entanglement alone provides classical communication ignores the requirement for the physical transmission stage.

## Practical Interpretation

Superdense coding is valuable as a systems model because it connects an abstract quantum protocol to concrete software responsibilities.

A complete implementation must track the initial resource, payload selection, local encoding, transmission, channel behavior, decoding, measurement, and observed outcome.

The six deliverables use different abstractions for that same technical boundary:

| Deliverable | Primary perspective |
| --- | --- |
| Python | Direct state-vector and matrix simulation |
| JavaScript | Event-driven and asynchronous communication workflow |
| C++ | Systems-oriented quantum communication case study |
| Java | Enterprise domain modeling and service separation |
| PostgreSQL | Relational resource, transmission, error, and measurement tracking |
| README | Technical relationship between the protocol mechanisms |

The implementations therefore preserve the central distinction between **superdense coding as a specific protocol** and **quantum communication as the broader communication domain in which that protocol operates**.
