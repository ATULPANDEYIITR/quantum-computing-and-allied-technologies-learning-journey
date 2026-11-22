'use strict';

/*
 * QUANTUM DATA ENCODING
 *
 * Node.js implementation of:
 * 1. Computational basis encoding
 * 2. RY angle encoding
 * 3. Amplitude encoding
 *
 * Engineering focus:
 * - Immutable state representations
 * - Event-driven encoding workflows
 * - Asynchronous processing
 * - Policy evaluation
 * - Measurement sampling
 * - Validation and resource estimation
 */

const { EventEmitter } = require('node:events');
const crypto = require('node:crypto');

class EncodingError extends Error {
    constructor(message) {
        super(message);
        this.name = 'EncodingError';
    }
}

const EncodingType = Object.freeze({
    BASIS: 'BASIS',
    ANGLE: 'ANGLE',
    AMPLITUDE: 'AMPLITUDE'
});

function validateVector(values) {
    if (!Array.isArray(values) || values.length === 0) {
        throw new EncodingError('A non-empty numerical array is required.');
    }

    return values.map((value, index) => {
        if (
            typeof value !== 'number' ||
            !Number.isFinite(value)
        ) {
            throw new EncodingError(
                `Invalid numerical feature at index ${index}.`
            );
        }

        return value;
    });
}

function requiredQubits(dimension) {
    if (!Number.isSafeInteger(dimension) || dimension <= 0) {
        throw new EncodingError('Dimension must be a positive integer.');
    }

    return Math.ceil(Math.log2(dimension));
}

function nextPowerOfTwo(dimension) {
    return 2 ** requiredQubits(dimension);
}

class QuantumState {
    constructor(type, numQubits, amplitudes, metadata = {}) {
        if (!Number.isInteger(numQubits) || numQubits < 0) {
            throw new EncodingError('Invalid qubit count.');
        }

        if (amplitudes.length !== 2 ** numQubits) {
            throw new EncodingError('State dimension mismatch.');
        }

        const norm = amplitudes.reduce(
            (sum, amplitude) => sum + amplitude * amplitude,
            0
        );

        if (Math.abs(norm - 1) > 1e-9) {
            throw new EncodingError('Quantum state is not normalized.');
        }

        this.type = type;
        this.numQubits = numQubits;
        this.amplitudes = Object.freeze([...amplitudes]);
        this.metadata = Object.freeze({ ...metadata });

        Object.freeze(this);
    }

    probabilities() {
        return this.amplitudes.map(amplitude => amplitude ** 2);
    }

    measurement(shots = 1000, seed = 12345) {
        if (!Number.isSafeInteger(shots) || shots <= 0) {
            throw new EncodingError('Measurement shots must be positive.');
        }

        const probabilities = this.probabilities();
        const counts = new Map();

        // Deterministic pseudo-random generator for reproducible tests.
        let state = seed >>> 0;

        const random = () => {
            state = (1664525 * state + 1013904223) >>> 0;
            return state / 4294967296;
        };

        const cumulative = [];
        let total = 0;

        for (const probability of probabilities) {
            total += probability;
            cumulative.push(total);
        }

        for (let shot = 0; shot < shots; shot++) {
            const sample = random();
            let index = cumulative.findIndex(value => sample < value);

            if (index === -1) {
                index = cumulative.length - 1;
            }

            const bitstring = index.toString(2)
                .padStart(this.numQubits, '0');

            counts.set(bitstring, (counts.get(bitstring) || 0) + 1);
        }

        return Object.fromEntries(counts);
    }
}

class QuantumEncoder {
    static basis(values) {
        if (!Array.isArray(values) || values.length === 0) {
            throw new EncodingError('Binary input cannot be empty.');
        }

        const bits = values.map((value, index) => {
            if (value !== 0 && value !== 1 && value !== false && value !== true) {
                throw new EncodingError(`Invalid bit at index ${index}.`);
            }

            return Number(value);
        });

        const bitstring = bits.join('');
        const basisIndex = Number.parseInt(bitstring, 2);

        const amplitudes = Array(2 ** bits.length).fill(0);
        amplitudes[basisIndex] = 1;

        return new QuantumState(
            EncodingType.BASIS,
            bits.length,
            amplitudes,
            { bitstring, basisIndex }
        );
    }

    static angle(values, minimum = 0, maximum = 1) {
        const features = validateVector(values);

        if (
            !Number.isFinite(minimum) ||
            !Number.isFinite(maximum) ||
            maximum <= minimum
        ) {
            throw new EncodingError('Invalid angle encoding range.');
        }

        const angles = features.map(value => {
            if (value < minimum || value > maximum) {
                throw new EncodingError('Feature is outside the input range.');
            }

            return Math.PI * (value - minimum) / (maximum - minimum);
        });

        // Each RY-encoded qubit contributes a cosine/sine pair.
        let amplitudes = [1];

        for (const theta of angles) {
            const zero = Math.cos(theta / 2);
            const one = Math.sin(theta / 2);

            const expanded = [];

            for (const amplitude of amplitudes) {
                expanded.push(amplitude * zero);
                expanded.push(amplitude * one);
            }

            amplitudes = expanded;
        }

        return new QuantumState(
            EncodingType.ANGLE,
            features.length,
            amplitudes,
            { features, angles, minimum, maximum }
        );
    }

    static amplitude(values) {
        const features = validateVector(values);

        const norm = Math.sqrt(
            features.reduce((sum, value) => sum + value ** 2, 0)
        );

        if (norm === 0) {
            throw new EncodingError('Zero vectors cannot be amplitude encoded.');
        }

        const numQubits = requiredQubits(features.length);
        const dimension = nextPowerOfTwo(features.length);

        const amplitudes = features.map(value => value / norm);

        // Padding preserves the original normalized amplitudes.
        while (amplitudes.length < dimension) {
            amplitudes.push(0);
        }

        return new QuantumState(
            EncodingType.AMPLITUDE,
            numQubits,
            amplitudes,
            {
                originalDimension: features.length,
                encodedDimension: dimension,
                originalNorm: norm
            }
        );
    }
}

/*
 * Resource policy prevents exponential state-vector allocation.
 * A real hardware backend would use its own device-specific limits.
 */
class EncodingPolicy {
    constructor({ maxQubits = 16, maxStateBytes = 64 * 1024 * 1024 } = {}) {
        this.maxQubits = maxQubits;
        this.maxStateBytes = maxStateBytes;
    }

    evaluate(state) {
        const dimension = 2 ** state.numQubits;
        const estimatedBytes = dimension * 16;

        const violations = [];

        if (state.numQubits > this.maxQubits) {
            violations.push('Qubit limit exceeded.');
        }

        if (estimatedBytes > this.maxStateBytes) {
            violations.push('State-vector memory budget exceeded.');
        }

        return Object.freeze({
            accepted: violations.length === 0,
            estimatedBytes,
            violations
        });
    }
}

/*
 * Event-driven service separates encoding from workflow orchestration.
 */
class EncodingService extends EventEmitter {
    constructor(policy = new EncodingPolicy()) {
        super();
        this.policy = policy;
        this.jobs = new Map();
    }

    async process(jobId, type, input, options = {}) {
        if (typeof jobId !== 'string' || jobId.trim() === '') {
            throw new EncodingError('A valid job identifier is required.');
        }

        if (this.jobs.has(jobId)) {
            throw new EncodingError('Duplicate job identifier.');
        }

        const job = {
            id: jobId,
            status: 'PROCESSING',
            createdAt: new Date().toISOString()
        };

        this.jobs.set(jobId, job);
        this.emit('job:started', Object.freeze({ ...job }));

        try {
            // Yield execution so multiple jobs can be scheduled.
            await new Promise(resolve => setImmediate(resolve));

            let quantumState;

            switch (type) {
                case EncodingType.BASIS:
                    quantumState = QuantumEncoder.basis(input);
                    break;

                case EncodingType.ANGLE:
                    quantumState = QuantumEncoder.angle(
                        input,
                        options.minimum ?? 0,
                        options.maximum ?? 1
                    );
                    break;

                case EncodingType.AMPLITUDE:
                    quantumState = QuantumEncoder.amplitude(input);
                    break;

                default:
                    throw new EncodingError('Unsupported encoding method.');
            }

            const evaluation = this.policy.evaluate(quantumState);

            if (!evaluation.accepted) {
                throw new EncodingError(
                    evaluation.violations.join(' ')
                );
            }

            const result = Object.freeze({
                jobId,
                state: quantumState,
                policy: evaluation,
                completedAt: new Date().toISOString()
            });

            this.jobs.set(jobId, {
                ...job,
                status: 'COMPLETED'
            });

            this.emit('job:completed', result);

            return result;

        } catch (error) {
            this.jobs.set(jobId, {
                ...job,
                status: 'FAILED',
                error: error.message
            });

            this.emit('job:failed', {
                jobId,
                error: error.message
            });

            throw error;
        }
    }

    getJob(jobId) {
        const job = this.jobs.get(jobId);

        if (!job) {
            throw new EncodingError('Job does not exist.');
        }

        return Object.freeze({ ...job });
    }
}

async function main() {
    const service = new EncodingService(
        new EncodingPolicy({ maxQubits: 12 })
    );

    service.on('job:started', job => {
        console.log(`[STARTED] ${job.id}`);
    });

    service.on('job:completed', result => {
        console.log(
            `[COMPLETED] ${result.jobId}:`,
            result.state.numQubits,
            'qubits'
        );
    });

    service.on('job:failed', failure => {
        console.error(`[FAILED] ${failure.jobId}: ${failure.error}`);
    });

    const jobs = [
        service.process(
            'BASIS-001',
            EncodingType.BASIS,
            [1, 0, 1, 1]
        ),
        service.process(
            'ANGLE-001',
            EncodingType.ANGLE,
            [0.2, 0.5, 0.8]
        ),
        service.process(
            'AMPLITUDE-001',
            EncodingType.AMPLITUDE,
            [3, 4, 0]
        )
    ];

    const results = await Promise.allSettled(jobs);

    for (const result of results) {
        if (result.status === 'fulfilled') {
            const state = result.value.state;

            console.log('\nMeasurement probabilities:');
            console.log(state.probabilities());

            console.log('Sampled measurements:');
            console.log(state.measurement(1000, 42));
        }
    }

    // Demonstrate rejection of invalid input.
    try {
        await service.process(
            'INVALID-001',
            EncodingType.AMPLITUDE,
            [0, 0, 0]
        );
    } catch (error) {
        console.log('\nExpected validation failure:', error.message);
    }

    // Demonstrate deterministic identifier generation.
    const auditId = crypto.randomUUID();

    console.log('\nAudit identifier:', auditId);
    console.log('Completed workflow.');
}

main().catch(error => {
    console.error('Fatal execution error:', error.message);
    process.exitCode = 1;
});
