'use strict';

/*
 * Bell States: Generate and Measure Bell Pairs
 *
 * This Node.js program uses JavaScript's event-driven and asynchronous
 * capabilities to model a stream of Bell-pair preparation and measurement.
 *
 * Bell states:
 *   |Phi+> = (|00> + |11>) / sqrt(2)
 *   |Phi-> = (|00> - |11>) / sqrt(2)
 *   |Psi+> = (|01> + |10>) / sqrt(2)
 *   |Psi-> = (|01> - |10>) / sqrt(2)
 *
 * No npm packages are required.
 */

const SQRT_HALF = 1 / Math.sqrt(2);
const EPSILON = 1e-12;

const BASIS = ['00', '01', '10', '11'];

const BELL_NAMES = Object.freeze({
    phiPlus: 'Phi+',
    phiMinus: 'Phi-',
    psiPlus: 'Psi+',
    psiMinus: 'Psi-'
});

function complex(real = 0, imaginary = 0) {
    return { real, imaginary };
}

function addComplex(a, b) {
    return complex(
        a.real + b.real,
        a.imaginary + b.imaginary
    );
}

function multiplyComplex(a, b) {
    return complex(
        a.real * b.real - a.imaginary * b.imaginary,
        a.real * b.imaginary + a.imaginary * b.real
    );
}

function conjugate(value) {
    return complex(value.real, -value.imaginary);
}

function magnitudeSquared(value) {
    return value.real * value.real + value.imaginary * value.imaginary;
}

function scaleComplex(value, factor) {
    return complex(
        value.real * factor,
        value.imaginary * factor
    );
}

function cloneState(state) {
    return Object.fromEntries(
        BASIS.map(basis => [
            basis,
            complex(state[basis].real, state[basis].imaginary)
        ])
    );
}

function normalizeState(state) {
    const normSquared = BASIS.reduce(
        (sum, basis) => sum + magnitudeSquared(state[basis]),
        0
    );

    if (normSquared <= EPSILON) {
        throw new Error('Cannot normalize a zero quantum state.');
    }

    const factor = 1 / Math.sqrt(normSquared);
    const normalized = {};

    for (const basis of BASIS) {
        normalized[basis] = scaleComplex(state[basis], factor);
    }

    return normalized;
}

function validateState(state) {
    for (const basis of BASIS) {
        if (!state[basis]) {
            throw new Error(`Missing amplitude for |${basis}>.`);
        }
    }

    const totalProbability = BASIS.reduce(
        (sum, basis) => sum + magnitudeSquared(state[basis]),
        0
    );

    if (Math.abs(totalProbability - 1) > 1e-10) {
        throw new Error(
            `State is not normalized: probability=${totalProbability}`
        );
    }
}

function basisState(bits) {
    if (!/^[01]{2}$/.test(bits)) {
        throw new Error('A two-qubit basis state must contain two bits.');
    }

    const state = Object.fromEntries(
        BASIS.map(basis => [basis, complex()])
    );

    state[bits] = complex(1);
    return state;
}

function applyHadamard(state, qubit) {
    if (qubit !== 0 && qubit !== 1) {
        throw new Error('Qubit must be 0 or 1.');
    }

    const result = Object.fromEntries(
        BASIS.map(basis => [basis, complex()])
    );

    /*
     * H maps one amplitude pair at a time:
     * a|0> + b|1> becomes
     * ((a+b)/sqrt(2))|0> + ((a-b)/sqrt(2))|1>.
     */
    for (const basis of BASIS) {
        const bit = Number(basis[qubit]);
        const partnerBits = basis.split('');
        partnerBits[qubit] = bit === 0 ? '1' : '0';
        const partner = partnerBits.join('');

        if (bit === 0) {
            const a = state[basis];
            const b = state[partner];

            result[basis] = addComplex(
                result[basis],
                scaleComplex(addComplex(a, b), SQRT_HALF)
            );

            result[partner] = addComplex(
                result[partner],
                scaleComplex(
                    {
                        real: a.real - b.real,
                        imaginary: a.imaginary - b.imaginary
                    },
                    SQRT_HALF
                )
            );
        }
    }

    return normalizeState(result);
}

function applyPauliX(state, qubit) {
    if (qubit !== 0 && qubit !== 1) {
        throw new Error('Qubit must be 0 or 1.');
    }

    const result = Object.fromEntries(
        BASIS.map(basis => [basis, complex()])
    );

    for (const basis of BASIS) {
        const bits = basis.split('');
        bits[qubit] = bits[qubit] === '0' ? '1' : '0';
        const target = bits.join('');

        result[target] = addComplex(
            result[target],
            state[basis]
        );
    }

    return normalizeState(result);
}

function applyPauliZ(state, qubit) {
    if (qubit !== 0 && qubit !== 1) {
        throw new Error('Qubit must be 0 or 1.');
    }

    const result = cloneState(state);

    for (const basis of BASIS) {
        if (basis[qubit] === '1') {
            result[basis] = scaleComplex(result[basis], -1);
        }
    }

    return normalizeState(result);
}

function applyCnot(state, control, target) {
    if (![0, 1].includes(control) || ![0, 1].includes(target)) {
        throw new Error('Control and target must be qubit 0 or 1.');
    }

    if (control === target) {
        throw new Error('CNOT control and target must differ.');
    }

    const result = Object.fromEntries(
        BASIS.map(basis => [basis, complex()])
    );

    for (const basis of BASIS) {
        const bits = basis.split('');

        if (bits[control] === '1') {
            bits[target] = bits[target] === '0' ? '1' : '0';
        }

        const targetBasis = bits.join('');

        result[targetBasis] = addComplex(
            result[targetBasis],
            state[basis]
        );
    }

    return normalizeState(result);
}

function prepareBellState(name) {
    let state = basisState('00');

    /*
     * H followed by CNOT converts the separable |00> state into Phi+.
     */
    state = applyHadamard(state, 0);
    state = applyCnot(state, 0, 1);

    switch (name) {
        case 'phiPlus':
            break;

        case 'phiMinus':
            state = applyPauliZ(state, 0);
            break;

        case 'psiPlus':
            state = applyPauliX(state, 1);
            break;

        case 'psiMinus':
            state = applyPauliZ(state, 0);
            state = applyPauliX(state, 1);
            break;

        default:
            throw new Error(`Unknown Bell state: ${name}`);
    }

    return state;
}

function probabilityTable(state) {
    validateState(state);

    return Object.fromEntries(
        BASIS.map(basis => [
            basis,
            magnitudeSquared(state[basis])
        ])
    );
}

function measure(state, randomValue = Math.random()) {
    validateState(state);

    if (randomValue < 0 || randomValue >= 1) {
        throw new Error('Measurement random value must be in [0, 1).');
    }

    let cumulative = 0;

    for (const basis of BASIS) {
        cumulative += magnitudeSquared(state[basis]);

        if (randomValue < cumulative) {
            return {
                outcome: basis,
                collapsedState: basisState(basis)
            };
        }
    }

    throw new Error('Measurement failed because the state was invalid.');
}

function measureQubit(state, qubit, randomValue = Math.random()) {
    if (qubit !== 0 && qubit !== 1) {
        throw new Error('Qubit must be 0 or 1.');
    }

    const probabilitiesByValue = { '0': 0, '1': 0 };

    for (const basis of BASIS) {
        probabilitiesByValue[basis[qubit]] +=
            magnitudeSquared(state[basis]);
    }

    const value = randomValue < probabilitiesByValue['0'] ? '0' : '1';

    const collapsed = Object.fromEntries(
        BASIS.map(basis => [
            basis,
            basis[qubit] === value ? state[basis] : complex()
        ])
    );

    return {
        outcome: value,
        collapsedState: normalizeState(collapsed)
    };
}

function formatComplex(value) {
    const real = Math.abs(value.real) < EPSILON ? 0 : value.real;
    const imaginary =
        Math.abs(value.imaginary) < EPSILON ? 0 : value.imaginary;

    if (imaginary === 0) {
        return real.toFixed(4);
    }

    if (real === 0) {
        return `${imaginary.toFixed(4)}i`;
    }

    return `${real.toFixed(4)} ${imaginary >= 0 ? '+' : '-'} ` +
        `${Math.abs(imaginary).toFixed(4)}i`;
}

function printState(name, state) {
    console.log(`\n|${name}>`);

    for (const basis of BASIS) {
        if (magnitudeSquared(state[basis]) > EPSILON) {
            console.log(
                `  |${basis}>: ${formatComplex(state[basis])}`
            );
        }
    }
}

function printProbabilities(state) {
    for (const [basis, probability] of Object.entries(
        probabilityTable(state)
    )) {
        if (probability > EPSILON) {
            console.log(
                `  P(|${basis}>) = ${probability.toFixed(4)}`
            );
        }
    }
}

/*
 * An async generator models a stream of newly prepared Bell pairs.
 * A real service could use this pattern for a detector, experiment
 * controller, or measurement event pipeline.
 */
async function* bellPairStream(stateName, count) {
    for (let index = 0; index < count; index += 1) {
        await new Promise(resolve => setImmediate(resolve));

        yield {
            sequence: index + 1,
            stateName,
            state: prepareBellState(stateName)
        };
    }
}

async function collectMeasurements(stateName, count) {
    const counts = Object.fromEntries(
        BASIS.map(basis => [basis, 0])
    );

    /*
     * Each yielded pair is a fresh quantum state. Reusing a collapsed
     * state would incorrectly model repeated measurements of one pair.
     */
    for await (const pair of bellPairStream(stateName, count)) {
        const measurement = measure(pair.state);
        counts[measurement.outcome] += 1;
    }

    return counts;
}

function correlationForComputationalBasis(state) {
    /*
     * Z⊗Z has eigenvalue +1 for equal bits and -1 for different bits.
     */
    return BASIS.reduce((correlation, basis) => {
        const eigenvalue = basis[0] === basis[1] ? 1 : -1;
        return correlation +
            eigenvalue * magnitudeSquared(state[basis]);
    }, 0);
}

function densityMatrix(state) {
    /*
     * rho[i,j] = amplitude(i) * conjugate(amplitude(j)).
     * The matrix representation makes phase information explicit,
     * even though computational-basis measurement probabilities only
     * depend on diagonal magnitudes.
     */
    return BASIS.map(row =>
        BASIS.map(column =>
            multiplyComplex(
                state[row],
                conjugate(state[column])
            )
        )
    );
}

function reducedDensityMatrixOfSecondQubit(state) {
    const rho = densityMatrix(state);

    /*
     * With basis ordering |00>, |01>, |10>, |11>, trace out qubit 0:
     *
     * rho_B[0,0] = rho[00,00] + rho[10,10]
     * rho_B[0,1] = rho[00,01] + rho[10,11]
     * rho_B[1,0] = rho[01,00] + rho[11,10]
     * rho_B[1,1] = rho[01,01] + rho[11,11]
     */
    return [
        [
            addComplex(rho[0][0], rho[2][2]),
            addComplex(rho[0][1], rho[2][3])
        ],
        [
            addComplex(rho[1][0], rho[3][2]),
            addComplex(rho[1][1], rho[3][3])
        ]
    ];
}

function printReducedDensityMatrix(matrix) {
    for (const row of matrix) {
        console.log(
            '  [' +
            row.map(formatComplex).join(', ') +
            ']'
        );
    }
}

async function demonstrateEventDrivenMeasurements() {
    console.log('\n' + '='.repeat(72));
    console.log('EVENT-DRIVEN BELL-PAIR MEASUREMENT');
    console.log('='.repeat(72));

    const trials = 3000;

    for (const stateName of Object.keys(BELL_NAMES)) {
        const counts = await collectMeasurements(stateName, trials);

        console.log(`\n${BELL_NAMES[stateName]} over ${trials} fresh pairs:`);

        for (const basis of BASIS) {
            const frequency = counts[basis] / trials;

            if (counts[basis] > 0) {
                console.log(
                    `  |${basis}>: ${counts[basis]} ` +
                    `(${frequency.toFixed(4)})`
                );
            }
        }
    }
}

function demonstratePartialMeasurement() {
    console.log('\n' + '='.repeat(72));
    console.log('PARTIAL MEASUREMENT');
    console.log('='.repeat(72));

    const state = prepareBellState('phiPlus');
    const result = measureQubit(state, 0, 0.1);

    console.log('Prepared |Phi+>.');
    console.log(`Measured qubit 0 and observed ${result.outcome}.`);
    printState('Conditional post-measurement state', result.collapsedState);
}

function demonstratePhaseDifference() {
    console.log('\n' + '='.repeat(72));
    console.log('PHASE DIFFERENCE BETWEEN BELL STATES');
    console.log('='.repeat(72));

    const phiPlus = prepareBellState('phiPlus');
    const phiMinus = prepareBellState('phiMinus');

    console.log('Phi+ amplitudes:');
    printState('Phi+', phiPlus);

    console.log('Phi- amplitudes:');
    printState('Phi-', phiMinus);

    console.log(
        '\nTheir computational-basis probabilities are identical, ' +
        'but their relative phase differs.'
    );
}

function demonstrateReducedState() {
    console.log('\n' + '='.repeat(72));
    console.log('REDUCED DENSITY MATRIX');
    console.log('='.repeat(72));

    for (const stateName of Object.keys(BELL_NAMES)) {
        console.log(`\nReduced state of qubit 1 for ${BELL_NAMES[stateName]}:`);
        printReducedDensityMatrix(
            reducedDensityMatrixOfSecondQubit(
                prepareBellState(stateName)
            )
        );
    }
}

function demonstrateValidation() {
    console.log('\n' + '='.repeat(72));
    console.log('VALIDATION');
    console.log('='.repeat(72));

    const invalidCases = [
        () => prepareBellState('unknown'),
        () => applyHadamard(basisState('00'), 4),
        () => applyCnot(basisState('00'), 0, 0),
        () => normalizeState(
            Object.fromEntries(
                BASIS.map(basis => [basis, complex()])
            )
        )
    ];

    for (const operation of invalidCases) {
        try {
            operation();
        } catch (error) {
            console.log(`Rejected invalid operation: ${error.message}`);
        }
    }
}

async function main() {
    console.log('BELL STATES: GENERATE AND MEASURE BELL PAIRS');

    for (const stateName of Object.keys(BELL_NAMES)) {
        const state = prepareBellState(stateName);
        printState(BELL_NAMES[stateName], state);
        printProbabilities(state);

        console.log(
            `  <Z⊗Z> = ` +
            correlationForComputationalBasis(state).toFixed(4)
        );
    }

    demonstratePhaseDifference();
    demonstratePartialMeasurement();
    demonstrateReducedState();
    demonstrateValidation();

    await demonstrateEventDrivenMeasurements();

    console.log('\nSimulation complete.');
}

main().catch(error => {
    console.error(`Fatal simulation error: ${error.message}`);
    process.exitCode = 1;
});
