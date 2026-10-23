'use strict';

/*
 * Quantum Phase Estimation using a dependency-free Node.js state-vector model.
 *
 * The example uses a one-qubit phase unitary
 *
 *     U(theta) = diag(1, exp(2*pi*i*theta))
 *
 * with |1> as its eigenstate. Controlled powers of U encode theta into the
 * counting register, and the inverse QFT converts that phase into measurable
 * computational-basis probabilities.
 *
 * Runtime: Node.js 18+
 */

const TWO_PI = 2 * Math.PI;

class Complex {
    constructor(re = 0, im = 0) {
        this.re = re;
        this.im = im;
    }

    add(other) {
        return new Complex(this.re + other.re, this.im + other.im);
    }

    multiply(other) {
        return new Complex(
            this.re * other.re - this.im * other.im,
            this.re * other.im + this.im * other.re
        );
    }

    scale(value) {
        return new Complex(this.re * value, this.im * value);
    }

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }

    static fromPolar(radius, angle) {
        return new Complex(
            radius * Math.cos(angle),
            radius * Math.sin(angle)
        );
    }
}

function validateTheta(theta) {
    if (!Number.isFinite(theta) || theta < 0 || theta >= 1) {
        throw new RangeError('theta must be finite and satisfy 0 <= theta < 1');
    }
}

function validateQubits(qubits) {
    if (!Number.isInteger(qubits) || qubits < 1 || qubits > 20) {
        throw new RangeError('qubits must be an integer between 1 and 20');
    }
}

function validateSamples(samples) {
    if (!Number.isInteger(samples) || samples <= 0) {
        throw new RangeError('samples must be a positive integer');
    }
}

function normalizeState(state) {
    const norm = Math.sqrt(
        state.reduce((sum, amplitude) => sum + amplitude.magnitudeSquared(), 0)
    );

    if (norm < Number.EPSILON) {
        throw new Error('cannot normalize a zero state');
    }

    return state.map(amplitude => amplitude.scale(1 / norm));
}

function createPlusRegister(qubits) {
    const dimension = 2 ** qubits;
    const amplitude = 1 / Math.sqrt(dimension);

    return Array.from(
        { length: dimension },
        () => new Complex(amplitude, 0)
    );
}

function applyControlledPhasePower(state, theta, controlQubit) {
    const phase = Complex.fromPolar(
        1,
        TWO_PI * theta * (2 ** controlQubit)
    );

    const result = state.map(amplitude =>
        new Complex(amplitude.re, amplitude.im)
    );

    for (let index = 0; index < state.length; index++) {
        const controlBit = (index >> controlQubit) & 1;

        if (controlBit === 1) {
            result[index] = state[index].multiply(phase);
        }
    }

    return result;
}

function inverseQFT(state) {
    const dimension = state.length;

    if ((dimension & (dimension - 1)) !== 0) {
        throw new Error('inverse QFT requires a power-of-two dimension');
    }

    const scale = 1 / Math.sqrt(dimension);
    const result = Array.from(
        { length: dimension },
        () => new Complex()
    );

    for (let y = 0; y < dimension; y++) {
        let total = new Complex();

        for (let x = 0; x < dimension; x++) {
            const angle = -TWO_PI * x * y / dimension;
            const kernel = Complex.fromPolar(1, angle);
            total = total.add(state[x].multiply(kernel));
        }

        result[y] = total.scale(scale);
    }

    return normalizeState(result);
}

function probabilityDistribution(state) {
    const raw = state.map(amplitude => amplitude.magnitudeSquared());
    const total = raw.reduce((sum, value) => sum + value, 0);

    if (total <= Number.EPSILON) {
        throw new Error('state has zero probability mass');
    }

    return raw.map(value => value / total);
}

function createSeededRandom(seed) {
    let value = seed >>> 0;

    return () => {
        value = (1664525 * value + 1013904223) >>> 0;
        return value / 0x100000000;
    };
}

function sample(probabilities, count, seed = 7) {
    validateSamples(count);

    const random = createSeededRandom(seed);
    const cumulative = [];
    let running = 0;

    for (const probability of probabilities) {
        running += probability;
        cumulative.push(running);
    }

    cumulative[cumulative.length - 1] = 1;

    const results = [];

    for (let sampleIndex = 0; sampleIndex < count; sampleIndex++) {
        const draw = random();
        let selected = cumulative.length - 1;

        for (let index = 0; index < cumulative.length; index++) {
            if (draw <= cumulative[index]) {
                selected = index;
                break;
            }
        }

        results.push(selected);
    }

    return results;
}

function estimatePhase(theta, qubits, samples = 1000, seed = 7) {
    validateTheta(theta);
    validateQubits(qubits);
    validateSamples(samples);

    /*
     * The target eigenstate is |1>. It does not need to be included in this
     * reduced model because U^k|1> = exp(2*pi*i*theta*k)|1>.
     */
    let state = createPlusRegister(qubits);

    for (let control = 0; control < qubits; control++) {
        state = applyControlledPhasePower(
            state,
            theta,
            control
        );
    }

    const transformed = inverseQFT(state);
    const probabilities = probabilityDistribution(transformed);

    let mostLikely = 0;

    for (let index = 1; index < probabilities.length; index++) {
        if (probabilities[index] > probabilities[mostLikely]) {
            mostLikely = index;
        }
    }

    const estimate = mostLikely / (2 ** qubits);

    return {
        theta,
        qubits,
        probabilities,
        mostLikely,
        estimate,
        absoluteError: Math.abs(theta - estimate),
        samples: sample(probabilities, samples, seed)
    };
}

function printDistribution(result, threshold = 1e-4) {
    const scale = 2 ** result.qubits;

    console.log('\nProbability distribution');

    result.probabilities.forEach((probability, integer) => {
        if (probability >= threshold) {
            console.log(
                `  ${integer.toString().padStart(3)} ` +
                `phase=${(integer / scale).toFixed(8)} ` +
                `probability=${probability.toFixed(8)}`
            );
        }
    });
}

function printHistogram(result) {
    const counts = new Map();

    for (const outcome of result.samples) {
        counts.set(outcome, (counts.get(outcome) || 0) + 1);
    }

    const scale = 2 ** result.qubits;

    console.log('\nSample histogram');

    [...counts.entries()]
        .sort(([left], [right]) => left - right)
        .forEach(([outcome, count]) => {
            console.log(
                `  ${outcome.toString().padStart(3)} ` +
                `phase=${(outcome / scale).toFixed(8)} ` +
                `count=${count}`
            );
        });
}

function demonstrateAsyncEvaluation() {
    /*
     * QPE itself is numerical, but a real application may evaluate several
     * circuits through an asynchronous quantum-service API. This function
     * models that event-driven orchestration without requiring a service.
     */
    const phases = [0.125, 0.3125, 0.37, 0.625];

    return Promise.all(
        phases.map(
            theta =>
                new Promise(resolve => {
                    setImmediate(() => {
                        resolve(estimatePhase(theta, 5, 500, 21));
                    });
                })
        )
    );
}

async function main() {
    console.log('Quantum Phase Estimation');
    console.log('========================');

    const exact = estimatePhase(0.625, 4, 1000, 11);

    console.log('\nExactly representable phase');
    console.log(`Target:       ${exact.theta}`);
    console.log(`Most likely:  ${exact.mostLikely}`);
    console.log(`Estimate:     ${exact.estimate}`);
    console.log(`Error:        ${exact.absoluteError}`);

    printDistribution(exact);

    const approximate = estimatePhase(0.37, 5, 2000, 31);

    console.log('\nNon-binary phase');
    console.log(`Target:       ${approximate.theta}`);
    console.log(`Estimate:     ${approximate.estimate}`);
    console.log(`Error:        ${approximate.absoluteError}`);

    printDistribution(approximate);
    printHistogram(approximate);

    console.log('\nAsynchronous batch evaluation');

    const results = await demonstrateAsyncEvaluation();

    for (const result of results) {
        console.log(
            `theta=${result.theta.toFixed(4)} ` +
            `estimate=${result.estimate.toFixed(6)} ` +
            `error=${result.absoluteError.toFixed(6)}`
        );
    }

    console.log('\nValidation example');

    try {
        estimatePhase(1.0, 4);
    } catch (error) {
        console.log(`Rejected invalid phase: ${error.message}`);
    }

    console.log('\nComplexity');
    console.log('State size is O(2^m) for m counting qubits.');
    console.log('The direct inverse QFT requires O(4^m) arithmetic operations.');
    console.log('Real quantum hardware implements QFT with a polynomial number of gates.');
}

main().catch(error => {
    console.error(`Execution failed: ${error.message}`);
    process.exitCode = 1;
});
