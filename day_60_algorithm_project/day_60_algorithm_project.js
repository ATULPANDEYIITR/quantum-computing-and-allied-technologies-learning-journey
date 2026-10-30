'use strict';

/*
 * Event-driven state-vector workbench.
 * Supported algorithms: Deutsch-Jozsa, Bernstein-Vazirani and Grover.
 * Qubit 0 is the least significant bit of each basis-state index.
 */

const { EventEmitter } = require('node:events');

const MAX_QUBITS = 16;
const MAX_SHOTS = 100000;

class QuantumValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'QuantumValidationError';
    }
}

class StateVector {
    constructor(qubits) {
        if (!Number.isInteger(qubits) || qubits < 1 || qubits > MAX_QUBITS) {
            throw new QuantumValidationError(
                `Qubit count must be between 1 and ${MAX_QUBITS}.`
            );
        }

        this.qubits = qubits;
        this.dimension = 2 ** qubits;

        // Interleaved real and imaginary amplitudes avoid per-amplitude objects.
        this.amplitudes = new Float64Array(this.dimension * 2);
        this.amplitudes[0] = 1;
    }

    hadamard(qubit) {
        this.validateQubit(qubit);
        const stride = 2 ** qubit;
        const scale = 1 / Math.sqrt(2);

        for (let block = 0; block < this.dimension; block += stride * 2) {
            for (let offset = 0; offset < stride; offset += 1) {
                const left = block + offset;
                const right = left + stride;
                const li = left * 2;
                const ri = right * 2;

                const aReal = this.amplitudes[li];
                const aImag = this.amplitudes[li + 1];
                const bReal = this.amplitudes[ri];
                const bImag = this.amplitudes[ri + 1];

                this.amplitudes[li] = (aReal + bReal) * scale;
                this.amplitudes[li + 1] = (aImag + bImag) * scale;
                this.amplitudes[ri] = (aReal - bReal) * scale;
                this.amplitudes[ri + 1] = (aImag - bImag) * scale;
            }
        }
    }

    phaseOracle(predicate) {
        if (typeof predicate !== 'function') {
            throw new QuantumValidationError('Oracle must be a function.');
        }

        for (let basis = 0; basis < this.dimension; basis += 1) {
            if (predicate(basis)) {
                const index = basis * 2;
                this.amplitudes[index] *= -1;
                this.amplitudes[index + 1] *= -1;
            }
        }
    }

    diffuse() {
        // Reflection around the uniform superposition.
        let meanReal = 0;
        let meanImag = 0;

        for (let basis = 0; basis < this.dimension; basis += 1) {
            meanReal += this.amplitudes[basis * 2];
            meanImag += this.amplitudes[basis * 2 + 1];
        }

        meanReal /= this.dimension;
        meanImag /= this.dimension;

        for (let basis = 0; basis < this.dimension; basis += 1) {
            const index = basis * 2;
            this.amplitudes[index] = 2 * meanReal - this.amplitudes[index];
            this.amplitudes[index + 1] =
                2 * meanImag - this.amplitudes[index + 1];
        }
    }

    probability(basis) {
        const index = basis * 2;
        const real = this.amplitudes[index];
        const imaginary = this.amplitudes[index + 1];
        return real * real + imaginary * imaginary;
    }

    probabilities() {
        const output = new Float64Array(this.dimension);

        for (let basis = 0; basis < this.dimension; basis += 1) {
            output[basis] = this.probability(basis);
        }

        return output;
    }

    sample(random) {
        const probabilities = this.probabilities();
        const threshold = random();
        let cumulative = 0;

        for (let basis = 0; basis < this.dimension; basis += 1) {
            cumulative += probabilities[basis];
            if (threshold < cumulative) {
                return basis;
            }
        }

        // Floating-point accumulation can finish a few ulps below one.
        return this.dimension - 1;
    }

    validateQubit(qubit) {
        if (!Number.isInteger(qubit) || qubit < 0 || qubit >= this.qubits) {
            throw new QuantumValidationError(`Invalid qubit index: ${qubit}.`);
        }
    }
}

function createRandom(seed) {
    let state = Number(seed) >>> 0;
    if (state === 0) {
        state = 0x6d2b79f5;
    }

    // A deterministic generator makes test cases and experiment records repeatable.
    return function random() {
        state = (Math.imul(1664525, state) + 1013904223) >>> 0;
        return state / 0x100000000;
    };
}

function parseBitString(bits, expectedLength) {
    if (
        typeof bits !== 'string' ||
        bits.length !== expectedLength ||
        !/^[01]+$/.test(bits)
    ) {
        throw new QuantumValidationError(
            `Expected a ${expectedLength}-bit binary string.`
        );
    }

    return Number.parseInt(bits, 2);
}

function formatBitString(value, width) {
    return value.toString(2).padStart(width, '0');
}

function histogramFor(state, shots, random, formatter) {
    const histogram = new Map();

    for (let shot = 0; shot < shots; shot += 1) {
        const outcome = formatter(state.sample(random));
        histogram.set(outcome, (histogram.get(outcome) || 0) + 1);
    }

    return Object.fromEntries(
        [...histogram.entries()].sort(([a], [b]) => a.localeCompare(b))
    );
}

function dominantEntry(histogram) {
    return Object.entries(histogram).sort(
        (a, b) => b[1] - a[1] || a[0].localeCompare(b[0])
    )[0];
}

function optimalGroverIterations(dimension, markedCount) {
    const theta = Math.asin(Math.sqrt(markedCount / dimension));
    return Math.max(0, Math.floor(Math.PI / (4 * theta) - 0.5));
}

class QuantumExperimentRunner extends EventEmitter {
    constructor({ maxQubits = MAX_QUBITS } = {}) {
        super();

        if (!Number.isInteger(maxQubits) || maxQubits < 1 || maxQubits > MAX_QUBITS) {
            throw new QuantumValidationError('Invalid runner qubit limit.');
        }

        this.maxQubits = maxQubits;
        this.completedExperiments = 0;
    }

    validateRequest(request) {
        if (!request || typeof request !== 'object') {
            throw new QuantumValidationError('An experiment request is required.');
        }

        const supported = new Set([
            'DEUTSCH_JOZSA',
            'BERNSTEIN_VAZIRANI',
            'GROVER',
        ]);

        if (!supported.has(request.algorithm)) {
            throw new QuantumValidationError('Unsupported quantum algorithm.');
        }

        if (
            !Number.isInteger(request.qubits) ||
            request.qubits < 1 ||
            request.qubits > this.maxQubits
        ) {
            throw new QuantumValidationError('Invalid qubit count.');
        }

        const shots = request.shots ?? 1000;
        if (!Number.isInteger(shots) || shots < 1 || shots > MAX_SHOTS) {
            throw new QuantumValidationError(
                `Shot count must be between 1 and ${MAX_SHOTS}.`
            );
        }

        const dimension = 2 ** request.qubits;

        if (request.algorithm === 'BERNSTEIN_VAZIRANI') {
            parseBitString(request.secret, request.qubits);
        }

        if (request.algorithm === 'DEUTSCH_JOZSA') {
            const allowed = new Set([
                'constant-zero',
                'constant-one',
                'balanced-parity',
            ]);

            const oracle = request.oracle ?? 'balanced-parity';
            if (!allowed.has(oracle)) {
                throw new QuantumValidationError('Invalid Deutsch-Jozsa oracle.');
            }

            if (oracle === 'balanced-parity') {
                const mask = request.balancedMask ?? 1;
                if (!Number.isInteger(mask) || mask <= 0 || mask >= dimension) {
                    throw new QuantumValidationError('Invalid balanced parity mask.');
                }
            }
        }

        if (request.algorithm === 'GROVER') {
            if (
                !Array.isArray(request.markedStates) ||
                request.markedStates.length === 0
            ) {
                throw new QuantumValidationError(
                    'Grover search requires marked states.'
                );
            }

            const unique = new Set(request.markedStates);
            if (unique.size !== request.markedStates.length) {
                throw new QuantumValidationError(
                    'Marked states must not contain duplicates.'
                );
            }

            for (const marked of unique) {
                if (!Number.isInteger(marked) || marked < 0 || marked >= dimension) {
                    throw new QuantumValidationError(
                        `Marked state ${marked} is outside the search space.`
                    );
                }
            }
        }

        return { ...request, shots, seed: request.seed ?? 1 };
    }

    async run(rawRequest, { signal } = {}) {
        const request = this.validateRequest(rawRequest);
        const experimentId = `qexp-${Date.now()}-${this.completedExperiments + 1}`;
        const random = createRandom(request.seed);

        this.emit('started', {
            experimentId,
            algorithm: request.algorithm,
            qubits: request.qubits,
            shots: request.shots,
        });

        try {
            if (signal?.aborted) {
                throw new Error('Experiment cancelled before execution.');
            }

            // Yield to the event loop so callers can process events and abort requests.
            await new Promise((resolve) => setImmediate(resolve));

            if (signal?.aborted) {
                throw new Error('Experiment cancelled before circuit execution.');
            }

            const result = this.execute(request, random);
            this.completedExperiments += 1;

            const completed = {
                experimentId,
                ...result,
                completedExperiments: this.completedExperiments,
            };

            this.emit('completed', completed);
            return completed;
        } catch (error) {
            this.emit('failed', {
                experimentId,
                algorithm: request.algorithm,
                message: error.message,
            });
            throw error;
        }
    }

    execute(request, random) {
        const state = new StateVector(request.qubits);
        const { qubits, shots, algorithm } = request;
        const dimension = state.dimension;

        for (let qubit = 0; qubit < qubits; qubit += 1) {
            state.hadamard(qubit);
        }

        let metadata = {};

        if (algorithm === 'DEUTSCH_JOZSA') {
            const oracle = request.oracle ?? 'balanced-parity';

            if (oracle === 'constant-one') {
                state.phaseOracle(() => true);
            } else if (oracle === 'balanced-parity') {
                const mask = request.balancedMask ?? 1;
                state.phaseOracle(
                    (basis) => parity(basis & mask) === 1
                );
            }

            for (let qubit = 0; qubit < qubits; qubit += 1) {
                state.hadamard(qubit);
            }

            const histogram = histogramFor(
                state,
                shots,
                random,
                (outcome) => formatBitString(outcome, qubits)
            );

            const zeroCount = histogram['0'.repeat(qubits)] || 0;
            const balancedCount = shots - zeroCount;
            const dominant = dominantEntry(histogram);

            metadata = {
                oracle,
                classification:
                    dominant[0] === '0'.repeat(qubits) ? 'constant' : 'balanced',
                zeroOutcomeFraction: zeroCount / shots,
            };

            return {
                algorithm,
                histogram,
                interpretation: metadata.classification,
                confidence: Math.max(zeroCount, balancedCount) / shots,
                metadata,
            };
        }

        if (algorithm === 'BERNSTEIN_VAZIRANI') {
            const secretValue = parseBitString(request.secret, qubits);

            state.phaseOracle(
                (basis) => parity(basis & secretValue) === 1
            );

            for (let qubit = 0; qubit < qubits; qubit += 1) {
                state.hadamard(qubit);
            }

            const histogram = histogramFor(
                state,
                shots,
                random,
                (outcome) => formatBitString(outcome, qubits)
            );

            const mostFrequent = dominantEntry(histogram);
            const recoveredSecret = mostFrequent[0];

            return {
                algorithm,
                histogram,
                interpretation:
                    recoveredSecret === request.secret
                        ? 'secret recovered'
                        : 'measurement mismatch',
                confidence: (histogram[request.secret] || 0) / shots,
                metadata: {
                    secret: request.secret,
                    recoveredSecret,
                    oracleQueries: 1,
                },
            };
        }

        const marked = new Set(request.markedStates);
        const iterations = optimalGroverIterations(dimension, marked.size);

        for (let iteration = 0; iteration < iterations; iteration += 1) {
            state.phaseOracle((basis) => marked.has(basis));
            state.diffuse();
        }

        let successProbability = 0;
        for (const basis of marked) {
            successProbability += state.probability(basis);
        }

        const histogram = histogramFor(
            state,
            shots,
            random,
            (outcome) => formatBitString(outcome, qubits)
        );

        const successfulShots = Object.entries(histogram)
            .filter(([bits]) => marked.has(Number.parseInt(bits, 2)))
            .reduce((total, [, count]) => total + count, 0);

        return {
            algorithm,
            histogram,
            interpretation:
                successfulShots > 0 ? 'marked state observed' : 'no marked state observed',
            confidence: successfulShots / shots,
            metadata: {
                markedStates: [...marked].sort((a, b) => a - b),
                searchSpaceSize: dimension,
                iterations,
                theoreticalSuccessProbability: successProbability,
            },
        };
    }
}

function parity(value) {
    let result = 0;

    while (value !== 0) {
        result ^= 1;
        value &= value - 1;
    }

    return result;
}

async function main() {
    const runner = new QuantumExperimentRunner({ maxQubits: 12 });

    runner.on('started', (event) => {
        process.stdout.write(
            `START ${event.experimentId}: ${event.algorithm}, ` +
            `${event.qubits} qubits, ${event.shots} shots\n`
        );
    });

    runner.on('completed', (event) => {
        process.stdout.write(`COMPLETE ${event.experimentId}\n`);
    });

    runner.on('failed', (event) => {
        process.stderr.write(`FAILED ${event.experimentId}: ${event.message}\n`);
    });

    const requests = [
        {
            algorithm: 'DEUTSCH_JOZSA',
            qubits: 3,
            oracle: 'balanced-parity',
            balancedMask: 1,
            shots: 32,
            seed: 21,
        },
        {
            algorithm: 'BERNSTEIN_VAZIRANI',
            qubits: 4,
            secret: '1011',
            shots: 32,
            seed: 22,
        },
        {
            algorithm: 'GROVER',
            qubits: 3,
            markedStates: [5],
            shots: 1000,
            seed: 23,
        },
    ];

    const results = await Promise.all(
        requests.map((request) => runner.run(request))
    );

    process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
}

if (require.main === module) {
    main().catch((error) => {
        process.stderr.write(`${error.name}: ${error.message}\n`);
        process.exitCode = 1;
    });
}

module.exports = {
    QuantumExperimentRunner,
    QuantumValidationError,
    StateVector,
    optimalGroverIterations,
};
