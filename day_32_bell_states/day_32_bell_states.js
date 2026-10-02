'use strict';

/*
 * Bell States: Generate and Measure Bell Pairs
 *
 * A self-contained Node.js implementation focused on:
 * - Bell-state preparation
 * - Event-driven measurement experiments
 * - Reviewable state transitions
 * - Computational and X-basis measurement
 * - Correlation analysis
 * - Bell-state identification
 * - Noise experiments
 * - Asynchronous shot execution
 *
 * Run with:
 *   node bell_states.js
 *
 * No external npm packages are required.
 */

// ---------------------------------------------------------------------------
// Complex-number support
// ---------------------------------------------------------------------------

class Complex {
    constructor(real = 0, imaginary = 0) {
        this.real = real;
        this.imaginary = imaginary;
    }

    add(other) {
        return new Complex(
            this.real + other.real,
            this.imaginary + other.imaginary
        );
    }

    multiply(other) {
        return new Complex(
            this.real * other.real - this.imaginary * other.imaginary,
            this.real * other.imaginary + this.imaginary * other.real
        );
    }

    conjugate() {
        return new Complex(this.real, -this.imaginary);
    }

    scale(value) {
        return new Complex(
            this.real * value,
            this.imaginary * value
        );
    }

    magnitudeSquared() {
        return (
            this.real * this.real +
            this.imaginary * this.imaginary
        );
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    toString(precision = 4) {
        const r = Math.abs(this.real) < 10 ** (-precision)
            ? 0
            : this.real;
        const i = Math.abs(this.imaginary) < 10 ** (-precision)
            ? 0
            : this.imaginary;

        if (i === 0) {
            return r.toFixed(precision);
        }

        if (r === 0) {
            return `${i.toFixed(precision)}i`;
        }

        const sign = i >= 0 ? '+' : '-';
        return `${r.toFixed(precision)} ${sign} ${Math.abs(i).toFixed(precision)}i`;
    }
}

function complex(value) {
    return new Complex(value, 0);
}


// ---------------------------------------------------------------------------
// Vector and matrix helpers
// ---------------------------------------------------------------------------

function vectorNorm(state) {
    return Math.sqrt(
        state.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        )
    );
}

function normalizeState(state) {
    const norm = vectorNorm(state);

    if (norm === 0) {
        throw new Error('A quantum state cannot have zero norm.');
    }

    return state.map(amplitude => amplitude.scale(1 / norm));
}

function matrixVectorMultiply(matrix, vector) {
    if (matrix[0].length !== vector.length) {
        throw new Error('Matrix and vector dimensions do not match.');
    }

    return matrix.map(row =>
        row.reduce(
            (sum, value, index) =>
                sum.add(value.multiply(vector[index])),
            new Complex()
        )
    );
}

function matrixMultiply(a, b) {
    if (a[0].length !== b.length) {
        throw new Error('Matrices have incompatible dimensions.');
    }

    return a.map(row =>
        b[0].map((_, column) =>
            row.reduce(
                (sum, value, index) =>
                    sum.add(value.multiply(b[index][column])),
                new Complex()
            )
        )
    );
}

function tensorProductMatrix(a, b) {
    const result = [];

    for (const aRow of a) {
        for (const bRow of b) {
            const row = [];

            for (const aValue of aRow) {
                for (const bValue of bRow) {
                    row.push(aValue.multiply(bValue));
                }
            }

            result.push(row);
        }
    }

    return result;
}

function tensorProductVector(a, b) {
    const result = [];

    for (const aValue of a) {
        for (const bValue of b) {
            result.push(aValue.multiply(bValue));
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// Quantum gates
// ---------------------------------------------------------------------------

const SQRT_HALF = 1 / Math.sqrt(2);

const I = [
    [complex(1), complex(0)],
    [complex(0), complex(1)]
];

const X = [
    [complex(0), complex(1)],
    [complex(1), complex(0)]
];

const Z = [
    [complex(1), complex(0)],
    [complex(0), complex(-1)]
];

const H = [
    [complex(SQRT_HALF), complex(SQRT_HALF)],
    [complex(SQRT_HALF), complex(-SQRT_HALF)]
];

const CNOT = [
    [complex(1), complex(0), complex(0), complex(0)],
    [complex(0), complex(1), complex(0), complex(0)],
    [complex(0), complex(0), complex(0), complex(1)],
    [complex(0), complex(0), complex(1), complex(0)]
];

function applySingleQubitGate(state, gate, qubit) {
    if (state.length !== 4) {
        throw new Error('This simulator expects exactly two qubits.');
    }

    if (![0, 1].includes(qubit)) {
        throw new Error('Qubit must be 0 or 1.');
    }

    const result = Array.from(
        { length: 4 },
        () => new Complex()
    );

    for (let index = 0; index < 4; index++) {
        const bit = (index >> (1 - qubit)) & 1;

        for (let outputBit = 0; outputBit <= 1; outputBit++) {
            let sourceIndex = index;

            if (outputBit !== bit) {
                sourceIndex ^= (1 << (1 - qubit));
            }

            result[sourceIndex] = result[sourceIndex].add(
                gate[outputBit][bit].multiply(state[index])
            );
        }
    }

    return normalizeState(result);
}

function applyTwoQubitGate(state, gate) {
    if (state.length !== 4) {
        throw new Error('A two-qubit gate requires four amplitudes.');
    }

    return normalizeState(matrixVectorMultiply(gate, state));
}


// ---------------------------------------------------------------------------
// Bell-state preparation
// ---------------------------------------------------------------------------

const BELL_NAMES = ['Phi+', 'Phi-', 'Psi+', 'Psi-'];

function zeroState() {
    return [
        complex(1),
        complex(0),
        complex(0),
        complex(0)
    ];
}

function generateBellPair(name = 'Phi+') {
    if (!BELL_NAMES.includes(name)) {
        throw new Error(
            `Unknown Bell state: ${name}. Expected ${BELL_NAMES.join(', ')}.`
        );
    }

    let state = zeroState();

    // H creates the superposition required for entanglement.
    state = applySingleQubitGate(state, H, 0);

    // CNOT correlates the target with the control.
    state = applyTwoQubitGate(state, CNOT);

    if (name === 'Phi+') {
        return state;
    }

    if (name === 'Phi-') {
        return applySingleQubitGate(state, Z, 0);
    }

    if (name === 'Psi+') {
        return applySingleQubitGate(state, X, 1);
    }

    state = applySingleQubitGate(state, X, 1);
    state = applySingleQubitGate(state, Z, 0);

    return state;
}

function stateToString(state) {
    const labels = ['|00>', '|01>', '|10>', '|11>'];
    const terms = [];

    state.forEach((amplitude, index) => {
        if (amplitude.magnitude() > 1e-10) {
            terms.push(
                `(${amplitude.toString()})${labels[index]}`
            );
        }
    });

    return terms.join(' + ') || '0';
}


// ---------------------------------------------------------------------------
// Deterministic seeded random number generation
// ---------------------------------------------------------------------------

class SeededRandom {
    constructor(seed = 12345) {
        this.state = seed >>> 0;
    }

    next() {
        // Mulberry32 provides deterministic pseudo-randomness for repeatable
        // educational experiments. It is not cryptographically secure.
        let value = this.state + 0x6D2B79F5;
        this.state = value >>> 0;

        value = Math.imul(
            value ^ (value >>> 15),
            value | 1
        );

        value ^= value + Math.imul(
            value ^ (value >>> 7),
            value | 61
        );

        return (
            ((value ^ (value >>> 14)) >>> 0) /
            4294967296
        );
    }
}


// ---------------------------------------------------------------------------
// Measurement
// ---------------------------------------------------------------------------

function measurementProbabilities(state) {
    const probabilities = {};

    ['00', '01', '10', '11'].forEach((basis, index) => {
        probabilities[basis] = state[index].magnitudeSquared();
    });

    const total = Object.values(probabilities)
        .reduce((sum, probability) => sum + probability, 0);

    if (total <= 0) {
        throw new Error('State has no measurable probability.');
    }

    for (const basis of Object.keys(probabilities)) {
        probabilities[basis] /= total;
    }

    return probabilities;
}

function chooseOutcome(probabilities, random) {
    const value = random.next();
    let cumulative = 0;

    for (const [outcome, probability] of Object.entries(probabilities)) {
        cumulative += probability;

        if (value <= cumulative) {
            return outcome;
        }
    }

    return Object.keys(probabilities).at(-1);
}

function collapsedState(outcome) {
    const state = [
        complex(0),
        complex(0),
        complex(0),
        complex(0)
    ];

    state[parseInt(outcome, 2)] = complex(1);
    return state;
}

function measureZ(state, random) {
    const probabilities = measurementProbabilities(state);
    const outcome = chooseOutcome(probabilities, random);

    return {
        outcome,
        state: collapsedState(outcome)
    };
}

function measureX(state, random) {
    // X-basis measurement is implemented by changing from the X basis to
    // the computational basis with H on each qubit.
    let transformed = applySingleQubitGate(state, H, 0);
    transformed = applySingleQubitGate(transformed, H, 1);

    const measurement = measureZ(transformed, random);

    // Reversing H maps |0>, |1> back to |+>, |->.
    let collapsed = applySingleQubitGate(measurement.state, H, 0);
    collapsed = applySingleQubitGate(collapsed, H, 1);

    return {
        outcome: measurement.outcome,
        state: collapsed
    };
}

function sampleBellState(name, shots, basis, seed) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new Error('shots must be a positive integer.');
    }

    if (!['Z', 'X'].includes(basis)) {
        throw new Error('basis must be Z or X.');
    }

    const random = new SeededRandom(seed);
    const counts = {
        '00': 0,
        '01': 0,
        '10': 0,
        '11': 0
    };

    for (let shot = 0; shot < shots; shot++) {
        // A fresh Bell pair is required for each independent measurement.
        const state = generateBellPair(name);
        const measurement = basis === 'Z'
            ? measureZ(state, random)
            : measureX(state, random);

        counts[measurement.outcome]++;
    }

    return counts;
}


// ---------------------------------------------------------------------------
// Event-driven experiment engine
// ---------------------------------------------------------------------------

class BellExperiment extends EventTarget {
    constructor({ name, shots, seed = 123 }) {
        super();

        if (!BELL_NAMES.includes(name)) {
            throw new Error(`Unsupported Bell state: ${name}`);
        }

        if (!Number.isInteger(shots) || shots <= 0) {
            throw new Error('shots must be a positive integer.');
        }

        this.name = name;
        this.shots = shots;
        this.seed = seed;
    }

    async run() {
        this.dispatchEvent(new CustomEvent('prepared', {
            detail: {
                state: stateToString(generateBellPair(this.name))
            }
        }));

        await Promise.resolve();

        const zCounts = sampleBellState(
            this.name,
            this.shots,
            'Z',
            this.seed
        );

        this.dispatchEvent(new CustomEvent('measured', {
            detail: {
                basis: 'Z',
                counts: zCounts
            }
        }));

        await Promise.resolve();

        const xCounts = sampleBellState(
            this.name,
            this.shots,
            'X',
            this.seed + 1000
        );

        this.dispatchEvent(new CustomEvent('measured', {
            detail: {
                basis: 'X',
                counts: xCounts
            }
        }));

        const result = {
            name: this.name,
            zCounts,
            xCounts,
            zCorrelation: correlation(zCounts),
            xCorrelation: correlation(xCounts)
        };

        this.dispatchEvent(new CustomEvent('completed', {
            detail: result
        }));

        return result;
    }
}

function correlation(counts) {
    const total = Object.values(counts)
        .reduce((sum, value) => sum + value, 0);

    if (total === 0) {
        throw new Error('Cannot calculate correlation without observations.');
    }

    let score = 0;

    for (const [outcome, count] of Object.entries(counts)) {
        score += outcome[0] === outcome[1]
            ? count
            : -count;
    }

    return score / total;
}

function identifyBellState(zCounts, xCounts) {
    const zSame = correlation(zCounts) >= 0;
    const xSame = correlation(xCounts) >= 0;

    const key = `${zSame}:${xSame}`;

    const mapping = {
        'true:true': 'Phi+',
        'true:false': 'Phi-',
        'false:true': 'Psi+',
        'false:false': 'Psi-'
    };

    return mapping[key];
}


// ---------------------------------------------------------------------------
// Noise experiment
// ---------------------------------------------------------------------------

function noisyZMeasurement(name, shots, flipProbability, seed = 88) {
    if (flipProbability < 0 || flipProbability > 1) {
        throw new Error('flipProbability must be between 0 and 1.');
    }

    const random = new SeededRandom(seed);

    const counts = {
        '00': 0,
        '01': 0,
        '10': 0,
        '11': 0
    };

    for (let shot = 0; shot < shots; shot++) {
        let outcome = measureZ(
            generateBellPair(name),
            random
        ).outcome;

        let firstBit = outcome[0];
        let secondBit = outcome[1];

        if (random.next() < flipProbability) {
            firstBit = firstBit === '0' ? '1' : '0';
        }

        if (random.next() < flipProbability) {
            secondBit = secondBit === '0' ? '1' : '0';
        }

        outcome = firstBit + secondBit;
        counts[outcome]++;
    }

    return counts;
}


// ---------------------------------------------------------------------------
// Reduced-state and entanglement calculations
// ---------------------------------------------------------------------------

function densityMatrix(state) {
    return state.map(rowAmplitude =>
        state.map(columnAmplitude =>
            rowAmplitude.multiply(columnAmplitude.conjugate())
        )
    );
}

function partialTraceFirstQubit(rho) {
    if (rho.length !== 4 || rho[0].length !== 4) {
        throw new Error('Expected a 4x4 density matrix.');
    }

    return [
        [
            rho[0][0].add(rho[2][2]),
            rho[0][1].add(rho[2][3])
        ],
        [
            rho[1][0].add(rho[3][2]),
            rho[1][1].add(rho[3][3])
        ]
    ];
}

function matrixTrace(matrix) {
    return matrix.reduce(
        (sum, row, index) => sum.add(row[index]),
        new Complex()
    );
}

function pureStateConcurrence(state) {
    const [a, b, c, d] = state;

    return Math.min(
        1,
        2 * a.multiply(d)
            .add(b.multiply(c).scale(-1))
            .magnitude()
    );
}


// ---------------------------------------------------------------------------
// Demonstrations
// ---------------------------------------------------------------------------

function printBellStates() {
    console.log('='.repeat(72));
    console.log('BELL-STATE PREPARATION');
    console.log('='.repeat(72));

    for (const name of BELL_NAMES) {
        console.log(`${name.padEnd(6)} ${stateToString(generateBellPair(name))}`);
    }
}

function printProbabilities() {
    console.log('\n' + '='.repeat(72));
    console.log('COMPUTATIONAL-BASIS PROBABILITIES');
    console.log('='.repeat(72));

    for (const name of BELL_NAMES) {
        const probabilities = measurementProbabilities(
            generateBellPair(name)
        );

        console.log(`\n${name}`);

        for (const [basis, probability] of Object.entries(probabilities)) {
            console.log(
                `  P(${basis}) = ${probability.toFixed(4)}`
            );
        }
    }
}

function demonstrateCollapse() {
    console.log('\n' + '='.repeat(72));
    console.log('MEASUREMENT COLLAPSE');
    console.log('='.repeat(72));

    const random = new SeededRandom(42);
    const original = generateBellPair('Phi+');
    const result = measureZ(original, random);

    console.log(`Before: ${stateToString(original)}`);
    console.log(`Outcome: |${result.outcome}>`);
    console.log(`After:  ${stateToString(result.state)}`);
}

async function demonstrateEventDrivenWorkflow() {
    console.log('\n' + '='.repeat(72));
    console.log('EVENT-DRIVEN BELL EXPERIMENT');
    console.log('='.repeat(72));

    const experiment = new BellExperiment({
        name: 'Psi-',
        shots: 3000,
        seed: 500
    });

    experiment.addEventListener('prepared', event => {
        console.log(`Prepared: ${event.detail.state}`);
    });

    experiment.addEventListener('measured', event => {
        console.log(
            `Measured ${event.detail.basis}-basis:`,
            event.detail.counts
        );
    });

    experiment.addEventListener('completed', event => {
        console.log(
            `Correlations: Z=${event.detail.zCorrelation.toFixed(3)},`,
            `X=${event.detail.xCorrelation.toFixed(3)}`
        );
    });

    const result = await experiment.run();

    console.log(
        `Identified Bell state: ${
            identifyBellState(result.zCounts, result.xCounts)
        }`
    );
}

function demonstrateNoise() {
    console.log('\n' + '='.repeat(72));
    console.log('NOISE AND EMPIRICAL CORRELATION');
    console.log('='.repeat(72));

    for (const probability of [0, 0.01, 0.05, 0.15]) {
        const counts = noisyZMeasurement(
            'Phi+',
            4000,
            probability,
            900 + Math.floor(probability * 1000)
        );

        console.log(
            `noise=${(probability * 100).toFixed(1)}%`,
            `correlation=${correlation(counts).toFixed(3)}`,
            counts
        );
    }
}

function demonstrateReducedState() {
    console.log('\n' + '='.repeat(72));
    console.log('REDUCED STATE');
    console.log('='.repeat(72));

    const state = generateBellPair('Phi+');
    const rho = densityMatrix(state);
    const reduced = partialTraceFirstQubit(rho);

    console.log('Phi+ density matrix reduced to one qubit:');

    for (const row of reduced) {
        console.log(
            row.map(value => value.toString()).join('    ')
        );
    }

    console.log(
        'For a Bell pair, an individual qubit is maximally mixed even though',
        'the two-qubit system is a pure entangled state.'
    );

    console.log(
        `Concurrence of Phi+: ${pureStateConcurrence(state).toFixed(4)}`
    );

    console.log(
        `Trace of reduced state: ${matrixTrace(reduced).toString()}`
    );
}

function demonstrateValidation() {
    console.log('\n' + '='.repeat(72));
    console.log('VALIDATION');
    console.log('='.repeat(72));

    const invalidOperations = [
        () => generateBellPair('Unknown'),
        () => sampleBellState('Phi+', -1, 'Z', 1),
        () => sampleBellState('Phi+', 100, 'Y', 1),
        () => noisyZMeasurement('Phi+', 100, 2, 1)
    ];

    for (const operation of invalidOperations) {
        try {
            operation();
            console.log('ERROR: invalid input was accepted.');
        } catch (error) {
            console.log(`Rejected invalid input: ${error.message}`);
        }
    }
}


// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
    console.log('BELL STATES: GENERATE AND MEASURE BELL PAIRS');
    console.log('Self-contained Node.js state-vector simulator.');

    printBellStates();
    printProbabilities();
    demonstrateCollapse();
    await demonstrateEventDrivenWorkflow();
    demonstrateNoise();
    demonstrateReducedState();
    demonstrateValidation();

    console.log('\n' + '='.repeat(72));
    console.log('END OF BELL-STATE EXPERIMENT');
    console.log('='.repeat(72));
}

main().catch(error => {
    console.error(`Experiment failed: ${error.message}`);
    process.exitCode = 1;
});
