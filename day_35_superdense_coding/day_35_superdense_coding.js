'use strict';

/*
 * Superdense Coding as an event-driven quantum communication simulation.
 *
 * This implementation deliberately uses JavaScript-specific structures:
 * typed arrays for compact state storage, Maps for gate selection, async
 * functions for a communication pipeline, and EventTarget for protocol events.
 *
 * Two-qubit basis ordering:
 *   |00>, |01>, |10>, |11>
 *
 * Alice owns qubit 0 and Bob owns qubit 1.
 */

const SQRT2_INV = 1 / Math.sqrt(2);

const I = [
    [1, 0],
    [0, 1]
];

const X = [
    [0, 1],
    [1, 0]
];

const Z = [
    [1, 0],
    [0, -1]
];

const H = [
    [SQRT2_INV, SQRT2_INV],
    [SQRT2_INV, -SQRT2_INV]
];

const CNOT_01 = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
];

function complex(real = 0, imaginary = 0) {
    return { real, imaginary };
}

function addComplex(a, b) {
    return complex(a.real + b.real, a.imaginary + b.imaginary);
}

function multiplyComplex(a, b) {
    return complex(
        a.real * b.real - a.imaginary * b.imaginary,
        a.real * b.imaginary + a.imaginary * b.real
    );
}

function scaleComplex(a, scalar) {
    return complex(a.real * scalar, a.imaginary * scalar);
}

function magnitudeSquared(a) {
    return a.real * a.real + a.imaginary * a.imaginary;
}

function vectorNorm(state) {
    return Math.sqrt(
        state.reduce((sum, amplitude) => sum + magnitudeSquared(amplitude), 0)
    );
}

function normalize(state) {
    const norm = vectorNorm(state);

    if (norm === 0) {
        throw new Error('A quantum state cannot have zero norm.');
    }

    return state.map(amplitude => scaleComplex(amplitude, 1 / norm));
}

function matrixVectorMultiply(matrix, state) {
    if (matrix.length !== state.length) {
        throw new Error('Matrix and vector dimensions do not match.');
    }

    return matrix.map(row => {
        if (row.length !== state.length) {
            throw new Error('Matrix must be square for this simulator.');
        }

        return row.reduce(
            (sum, value, index) =>
                addComplex(sum, scaleComplex(state[index], value)),
            complex()
        );
    });
}

function matrixMultiply(left, right) {
    if (left[0].length !== right.length) {
        throw new Error('Matrix dimensions are incompatible.');
    }

    return left.map((row, i) =>
        right[0].map((_, j) =>
            row.reduce(
                (sum, _, k) =>
                    addComplex(
                        sum,
                        complex(left[i][k] * right[k][j])
                    ),
                complex()
            )
        )
    );
}

function tensorProduct(left, right) {
    const result = [];

    for (const leftRow of left) {
        for (const rightRow of right) {
            const row = [];

            for (const leftValue of leftRow) {
                for (const rightValue of rightRow) {
                    row.push(leftValue * rightValue);
                }
            }

            result.push(row);
        }
    }

    return result;
}

function basisState(bits) {
    if (!/^[01]{2}$/.test(bits)) {
        throw new Error('A message state must contain exactly two bits.');
    }

    const state = Array.from({ length: 4 }, () => complex());
    state[Number.parseInt(bits, 2)] = complex(1);
    return state;
}

function applySingleQubitGate(state, gate, qubit) {
    if (qubit !== 0 && qubit !== 1) {
        throw new Error('Qubit index must be 0 or 1.');
    }

    const expanded = qubit === 0
        ? tensorProduct(gate, I)
        : tensorProduct(I, gate);

    return normalize(matrixVectorMultiply(expanded, state));
}

function createBellPair() {
    let state = basisState('00');

    state = matrixVectorMultiply(tensorProduct(H, I), state);
    state = matrixVectorMultiply(CNOT_01, state);

    return normalize(state);
}

const encodingOperations = new Map([
    ['00', { name: 'I', matrix: I }],
    ['01', { name: 'X', matrix: X }],
    ['10', { name: 'Z', matrix: Z }],
    ['11', { name: 'ZX', matrix: matrixMultiply(Z, X) }]
]);

function encodeMessage(sharedState, message) {
    const operation = encodingOperations.get(message);

    if (!operation) {
        throw new Error(
            `Unsupported message "${message}". Expected 00, 01, 10, or 11.`
        );
    }

    return {
        state: applySingleQubitGate(sharedState, operation.matrix, 0),
        operation: operation.name
    };
}

function decodeBellState(state) {
    let decoded = matrixVectorMultiply(CNOT_01, state);
    decoded = matrixVectorMultiply(tensorProduct(H, I), decoded);
    return normalize(decoded);
}

function probabilities(state) {
    const norm = vectorNorm(state);

    if (Math.abs(norm - 1) > 1e-9) {
        throw new Error(`Expected a normalized state, got norm ${norm}.`);
    }

    return state.map(magnitudeSquared);
}

function sampleMeasurement(state, random = Math.random) {
    const distribution = probabilities(state);
    const threshold = random();
    let cumulative = 0;

    for (let index = 0; index < distribution.length; index++) {
        cumulative += distribution[index];

        if (threshold <= cumulative) {
            return index.toString(2).padStart(2, '0');
        }
    }

    return '11';
}

function applyChannelNoise(state, probability, random = Math.random) {
    if (probability < 0 || probability > 1) {
        throw new Error('Noise probability must be between 0 and 1.');
    }

    if (random() >= probability) {
        return state;
    }

    const possibleErrors = [
        { name: 'X', matrix: X },
        { name: 'Z', matrix: Z },
        { name: 'Y-equivalent', matrix: matrixMultiply(X, Z) }
    ];

    const selected =
        possibleErrors[Math.floor(random() * possibleErrors.length)];

    return {
        state: applySingleQubitGate(state, selected.matrix, 0),
        error: selected.name
    };
}

function describeState(state) {
    const labels = ['00', '01', '10', '11'];
    const terms = [];

    state.forEach((amplitude, index) => {
        if (magnitudeSquared(amplitude) > 1e-9) {
            const real = amplitude.real.toFixed(4);
            const imaginary = amplitude.imaginary.toFixed(4);
            terms.push(`(${real}+${imaginary}i)|${labels[index]}>`);
        }
    });

    return terms.join(' + ') || '0';
}

class QuantumChannel extends EventTarget {
    constructor(noiseProbability = 0) {
        super();
        this.noiseProbability = noiseProbability;
    }

    async transmit(state) {
        this.dispatchEvent(new CustomEvent('transmissionStarted'));

        /*
         * setTimeout models an asynchronous channel boundary. It does not
         * simulate physical propagation speed or quantum hardware latency.
         */
        await new Promise(resolve => setTimeout(resolve, 10));

        const result = applyChannelNoise(
            state,
            this.noiseProbability
        );

        this.dispatchEvent(
            new CustomEvent('transmissionCompleted', {
                detail: {
                    error: result.error ?? null
                }
            })
        );

        return result.state ?? result;
    }
}

class SuperdenseCodingSession extends EventTarget {
    constructor(channel) {
        super();
        this.channel = channel;
        this.history = [];

        channel.addEventListener('transmissionStarted', () => {
            this.dispatchEvent(
                new CustomEvent('channelEvent', {
                    detail: 'Alice started transmission'
                })
            );
        });

        channel.addEventListener('transmissionCompleted', event => {
            this.dispatchEvent(
                new CustomEvent('channelEvent', {
                    detail: `Channel completed transmission; error=${event.detail.error ?? 'none'}`
                })
            );
        });
    }

    async send(message) {
        if (!/^[01]{2}$/.test(message)) {
            throw new Error('Superdense coding requires exactly two classical bits.');
        }

        this.dispatchEvent(
            new CustomEvent('encodingStarted', { detail: { message } })
        );

        const shared = createBellPair();
        const encoded = encodeMessage(shared, message);

        this.dispatchEvent(
            new CustomEvent('encoded', {
                detail: {
                    message,
                    operation: encoded.operation,
                    state: describeState(encoded.state)
                }
            })
        );

        const transmitted = await this.channel.transmit(encoded.state);
        const decoded = decodeBellState(transmitted);
        const measured = sampleMeasurement(decoded);

        const result = {
            message,
            operation: encoded.operation,
            measured,
            success: measured === message,
            decodedState: describeState(decoded)
        };

        this.history.push(result);

        this.dispatchEvent(
            new CustomEvent('decoded', { detail: result })
        );

        return result;
    }
}

async function demonstrateIdealProtocol() {
    console.log('\n=== Ideal event-driven protocol ===');

    const channel = new QuantumChannel(0);
    const session = new SuperdenseCodingSession(channel);

    session.addEventListener('channelEvent', event => {
        console.log(`[channel] ${event.detail}`);
    });

    session.addEventListener('encoded', event => {
        console.log(
            `[Alice] ${event.detail.message} encoded with ${event.detail.operation}`
        );
    });

    session.addEventListener('decoded', event => {
        console.log(
            `[Bob] measured ${event.detail.measured}; success=${event.detail.success}`
        );
    });

    for (const message of ['00', '01', '10', '11']) {
        await session.send(message);
    }
}

async function estimateNoisyAccuracy(noiseProbability, trials = 500) {
    const channel = new QuantumChannel(noiseProbability);
    let successes = 0;

    for (let i = 0; i < trials; i++) {
        const message = ['00', '01', '10', '11'][i % 4];
        const result = await new SuperdenseCodingSession(channel).send(message);

        if (result.success) {
            successes++;
        }
    }

    return successes / trials;
}

async function demonstrateNoise() {
    console.log('\n=== Noisy quantum channel ===');

    for (const probability of [0, 0.05, 0.15, 0.30]) {
        const accuracy = await estimateNoisyAccuracy(probability, 200);
        console.log(
            `noise=${probability.toFixed(2)}, ` +
            `decoding accuracy=${accuracy.toFixed(3)}`
        );
    }
}

function demonstrateStateInvariants() {
    console.log('\n=== State invariants ===');

    for (const message of ['00', '01', '10', '11']) {
        const shared = createBellPair();
        const encoded = encodeMessage(shared, message);
        const decoded = decodeBellState(encoded.state);

        console.log(
            `${message}: ` +
            `shared norm=${vectorNorm(shared).toFixed(6)}, ` +
            `encoded norm=${vectorNorm(encoded.state).toFixed(6)}, ` +
            `decoded norm=${vectorNorm(decoded).toFixed(6)}`
        );
    }
}

function demonstrateCommunicationAccounting() {
    console.log('\n=== Communication accounting ===');
    console.log('Logical messages: 4');
    console.log('Information represented: log2(4) = 2 classical bits');
    console.log('Qubits transmitted during the protocol: 1');
    console.log(
        'Resource prerequisite: Alice and Bob must already share an entangled pair.'
    );
    console.log(
        'Entanglement does not permit faster-than-light signalling because the '
        + 'physical qubit still has to reach Bob.'
    );
}

async function main() {
    demonstrateStateInvariants();
    demonstrateCommunicationAccounting();
    await demonstrateIdealProtocol();
    await demonstrateNoise();

    console.log('\n=== Simulation complete ===');
}

main().catch(error => {
    console.error(`Protocol failure: ${error.message}`);
    process.exitCode = 1;
});
