/*
 * Qubits: Practical JavaScript Study and Simulation
 *
 * This self-contained file demonstrates qubits from elementary concepts
 * through multi-qubit simulation, entanglement, measurement, expectation
 * values, density matrices, circuit execution, noise, and a small BB84-style
 * educational protocol.
 *
 * Runtime: modern Node.js or a browser supporting standard JavaScript.
 * No external packages are required.
 */

"use strict";

// ---------------------------------------------------------------------------
// Section 1: Complex numbers
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

    subtract(other) {
        return new Complex(
            this.real - other.real,
            this.imaginary - other.imaginary
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

    scale(factor) {
        return new Complex(
            this.real * factor,
            this.imaginary * factor
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

    toString() {
        const real = Math.abs(this.real) < 1e-12 ? 0 : this.real;
        const imaginary =
            Math.abs(this.imaginary) < 1e-12 ? 0 : this.imaginary;

        if (imaginary === 0) {
            return real.toFixed(6);
        }

        if (real === 0) {
            return `${imaginary.toFixed(6)}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";

        return `${real.toFixed(6)}${sign}${Math.abs(imaginary).toFixed(6)}i`;
    }

    static fromPolar(magnitude, angle) {
        return new Complex(
            magnitude * Math.cos(angle),
            magnitude * Math.sin(angle)
        );
    }
}

const C0 = new Complex(0, 0);
const C1 = new Complex(1, 0);
const CI = new Complex(0, 1);
const CNEGATIVE_I = new Complex(0, -1);

const SQRT2_INV = 1 / Math.sqrt(2);

// ---------------------------------------------------------------------------
// Section 2: Vector and matrix operations
// ---------------------------------------------------------------------------

function cloneVector(vector) {
    return vector.map(
        value => new Complex(value.real, value.imaginary)
    );
}

function vectorNorm(vector) {
    return Math.sqrt(
        vector.reduce(
            (sum, value) => sum + value.magnitudeSquared(),
            0
        )
    );
}

function normalizeState(state) {
    const norm = vectorNorm(state);

    if (norm < 1e-12) {
        throw new Error("The zero vector cannot represent a qubit state.");
    }

    return state.map(value => value.scale(1 / norm));
}

function validateNormalizedState(state) {
    const probability = state.reduce(
        (sum, amplitude) => sum + amplitude.magnitudeSquared(),
        0
    );

    if (Math.abs(probability - 1) > 1e-9) {
        throw new Error(
            `State is not normalized. Probability sum=${probability}`
        );
    }
}

function matrixVectorMultiply(matrix, vector) {
    if (matrix.length !== vector.length) {
        throw new Error("Matrix and vector dimensions do not match.");
    }

    return matrix.map(row => {
        if (row.length !== vector.length) {
            throw new Error("Matrix must be square.");
        }

        return row.reduce(
            (sum, matrixValue, column) =>
                sum.add(matrixValue.multiply(vector[column])),
            new Complex()
        );
    });
}

function matrixMultiply(left, right) {
    if (left[0].length !== right.length) {
        throw new Error("Matrix dimensions do not match.");
    }

    return left.map(leftRow =>
        right[0].map((_, column) =>
            leftRow.reduce(
                (sum, value, index) =>
                    sum.add(value.multiply(right[index][column])),
                new Complex()
            )
        )
    );
}

function conjugateTranspose(matrix) {
    return matrix[0].map((_, column) =>
        matrix.map(row => row[column].conjugate())
    );
}

function isUnitary(matrix) {
    const product = matrixMultiply(
        conjugateTranspose(matrix),
        matrix
    );

    for (let row = 0; row < product.length; row++) {
        for (let column = 0; column < product.length; column++) {
            const expected = row === column ? C1 : C0;
            const error = product[row][column].subtract(expected).magnitude();

            if (error > 1e-9) {
                return false;
            }
        }
    }

    return true;
}

// ---------------------------------------------------------------------------
// Section 3: Common quantum gates
// ---------------------------------------------------------------------------

const I = [
    [C1, C0],
    [C0, C1]
];

const X = [
    [C0, C1],
    [C1, C0]
];

const Y = [
    [C0, CNEGATIVE_I],
    [CI, C0]
];

const Z = [
    [C1, C0],
    [C0, new Complex(-1, 0)]
];

const H = [
    [new Complex(SQRT2_INV, 0), new Complex(SQRT2_INV, 0)],
    [new Complex(SQRT2_INV, 0), new Complex(-SQRT2_INV, 0)]
];

const S = [
    [C1, C0],
    [C0, CI]
];

const T = [
    [C1, C0],
    [C0, Complex.fromPolar(1, Math.PI / 4)]
];

const CNOT = [
    [C1, C0, C0, C0],
    [C0, C1, C0, C0],
    [C0, C0, C0, C1],
    [C0, C0, C1, C0]
];

const SWAP = [
    [C1, C0, C0, C0],
    [C0, C0, C1, C0],
    [C0, C1, C0, C0],
    [C0, C0, C0, C1]
];

function rx(theta) {
    const c = Math.cos(theta / 2);
    const s = Math.sin(theta / 2);

    return [
        [new Complex(c, 0), new Complex(0, -s)],
        [new Complex(0, -s), new Complex(c, 0)]
    ];
}

function ry(theta) {
    const c = Math.cos(theta / 2);
    const s = Math.sin(theta / 2);

    return [
        [new Complex(c, 0), new Complex(-s, 0)],
        [new Complex(s, 0), new Complex(c, 0)]
    ];
}

function rz(theta) {
    return [
        [Complex.fromPolar(1, -theta / 2), C0],
        [C0, Complex.fromPolar(1, theta / 2)]
    ];
}

function applyGate(state, gate) {
    if (!isUnitary(gate)) {
        throw new Error("Quantum gates must be unitary.");
    }

    const result = matrixVectorMultiply(gate, state);
    validateNormalizedState(result);

    return result;
}

// ---------------------------------------------------------------------------
// Section 4: Basis states
// ---------------------------------------------------------------------------

function basisState(bit) {
    if (bit === 0) {
        return [C1, C0];
    }

    if (bit === 1) {
        return [C0, C1];
    }

    throw new Error("A basis state requires bit 0 or 1.");
}

function computationalBasisState(bitString) {
    if (
        bitString.length === 0 ||
        !/^[01]+$/.test(bitString)
    ) {
        throw new Error("bitString must contain only 0 and 1.");
    }

    const dimension = 2 ** bitString.length;
    const state = Array.from(
        { length: dimension },
        () => new Complex()
    );

    state[parseInt(bitString, 2)] = C1;

    return state;
}

function tensorProduct(left, right) {
    const result = [];

    for (const leftValue of left) {
        for (const rightValue of right) {
            result.push(leftValue.multiply(rightValue));
        }
    }

    return result;
}

function tensorMany(states) {
    if (states.length === 0) {
        throw new Error("At least one state is required.");
    }

    return states.reduce(
        (current, next) => tensorProduct(current, next)
    );
}

// ---------------------------------------------------------------------------
// Section 5: Generic n-qubit gates
// ---------------------------------------------------------------------------

function applySingleQubitGate(
    state,
    gate,
    targetQubit,
    numberOfQubits
) {
    const expectedDimension = 2 ** numberOfQubits;

    if (state.length !== expectedDimension) {
        throw new Error("State dimension does not match qubit count.");
    }

    if (
        targetQubit < 0 ||
        targetQubit >= numberOfQubits
    ) {
        throw new Error("Target qubit is out of range.");
    }

    const result = Array.from(
        { length: state.length },
        () => new Complex()
    );

    // Big-endian convention:
    // q0 is the leftmost displayed bit.
    const bitPosition = numberOfQubits - 1 - targetQubit;
    const mask = 1 << bitPosition;

    for (let index = 0; index < state.length; index++) {
        if ((index & mask) !== 0) {
            continue;
        }

        const partner = index | mask;

        const first = state[index];
        const second = state[partner];

        result[index] = gate[0][0]
            .multiply(first)
            .add(gate[0][1].multiply(second));

        result[partner] = gate[1][0]
            .multiply(first)
            .add(gate[1][1].multiply(second));
    }

    validateNormalizedState(result);

    return result;
}

function applyCNOT(
    state,
    controlQubit,
    targetQubit,
    numberOfQubits
) {
    if (controlQubit === targetQubit) {
        throw new Error("Control and target must be different.");
    }

    const result = Array.from(
        { length: state.length },
        () => new Complex()
    );

    const controlPosition =
        numberOfQubits - 1 - controlQubit;

    const targetPosition =
        numberOfQubits - 1 - targetQubit;

    const controlMask = 1 << controlPosition;
    const targetMask = 1 << targetPosition;

    for (let index = 0; index < state.length; index++) {
        const destination =
            index & controlMask
                ? index ^ targetMask
                : index;

        result[destination] =
            result[destination].add(state[index]);
    }

    validateNormalizedState(result);

    return result;
}

// ---------------------------------------------------------------------------
// Section 6: Measurement
// ---------------------------------------------------------------------------

function probabilities(state) {
    validateNormalizedState(state);

    return state.map(amplitude =>
        amplitude.magnitudeSquared()
    );
}

function measureState(state, numberOfQubits, random = Math.random) {
    const probabilityList = probabilities(state);
    const randomValue = random();

    let cumulative = 0;

    for (let index = 0; index < probabilityList.length; index++) {
        cumulative += probabilityList[index];

        if (
            randomValue <= cumulative ||
            index === probabilityList.length - 1
        ) {
            const outcome = index
                .toString(2)
                .padStart(numberOfQubits, "0");

            const collapsed = Array.from(
                { length: state.length },
                () => new Complex()
            );

            collapsed[index] = C1;

            return {
                outcome,
                collapsed
            };
        }
    }

    throw new Error("Measurement failed unexpectedly.");
}

function sampleMeasurements(
    state,
    numberOfQubits,
    shots = 1000,
    random = Math.random
) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new Error("shots must be a positive integer.");
    }

    const counts = new Map();

    for (let shot = 0; shot < shots; shot++) {
        const result = measureState(
            state,
            numberOfQubits,
            random
        );

        counts.set(
            result.outcome,
            (counts.get(result.outcome) || 0) + 1
        );
    }

    return Object.fromEntries(
        [...counts.entries()].sort(
            ([a], [b]) => a.localeCompare(b)
        )
    );
}

// ---------------------------------------------------------------------------
// Section 7: Circuit abstraction
// ---------------------------------------------------------------------------

class QuantumCircuit {
    constructor(numberOfQubits) {
        if (!Number.isInteger(numberOfQubits) || numberOfQubits <= 0) {
            throw new Error("Circuit needs at least one qubit.");
        }

        this.numberOfQubits = numberOfQubits;
        this.operations = [];
        this.reset();
    }

    reset() {
        this.state = computationalBasisState(
            "0".repeat(this.numberOfQubits)
        );
    }

    addGate(name, gate, targetQubit) {
        this.operations.push({
            name,
            execute: state =>
                applySingleQubitGate(
                    state,
                    gate,
                    targetQubit,
                    this.numberOfQubits
                )
        });
    }

    addCNOT(controlQubit, targetQubit) {
        this.operations.push({
            name: `CNOT q${controlQubit}->q${targetQubit}`,
            execute: state =>
                applyCNOT(
                    state,
                    controlQubit,
                    targetQubit,
                    this.numberOfQubits
                )
        });
    }

    run() {
        this.reset();

        for (const operation of this.operations) {
            this.state = operation.execute(this.state);
        }

        return this.state;
    }

    measure(shots = 1000) {
        const state = this.run();

        return sampleMeasurements(
            state,
            this.numberOfQubits,
            shots
        );
    }

    describe() {
        console.log(
            `Circuit: ${this.numberOfQubits} qubits`
        );

        this.operations.forEach(
            (operation, index) => {
                console.log(
                    `  ${index + 1}. ${operation.name}`
                );
            }
        );
    }
}

// ---------------------------------------------------------------------------
// Section 8: Bloch sphere and observables
// ---------------------------------------------------------------------------

function blochVector(state) {
    if (state.length !== 2) {
        throw new Error("Bloch vectors require one qubit.");
    }

    validateNormalizedState(state);

    const alpha = state[0];
    const beta = state[1];

    const product = alpha
        .conjugate()
        .multiply(beta);

    return {
        x: 2 * product.real,
        y: 2 * product.imaginary,
        z:
            alpha.magnitudeSquared() -
            beta.magnitudeSquared()
    };
}

function expectationValue(state, operator) {
    const transformed = matrixVectorMultiply(
        operator,
        state
    );

    return state.reduce(
        (sum, amplitude, index) =>
            sum.add(
                amplitude
                    .conjugate()
                    .multiply(transformed[index])
            ),
        new Complex()
    );
}

// ---------------------------------------------------------------------------
// Section 9: Density matrices
// ---------------------------------------------------------------------------

function outerProduct(ket, bra) {
    return ket.map(ketValue =>
        bra.map(braValue =>
            ketValue.multiply(braValue.conjugate())
        )
    );
}

function trace(matrix) {
    if (
        matrix.length === 0 ||
        matrix.some(row => row.length !== matrix.length)
    ) {
        throw new Error("Trace requires a square matrix.");
    }

    return matrix.reduce(
        (sum, row, index) =>
            sum.add(row[index]),
        new Complex()
    );
}

function mixDensityMatrices(first, second, probability) {
    if (probability < 0 || probability > 1) {
        throw new Error("Probability must be between 0 and 1.");
    }

    const result = [];

    for (let row = 0; row < first.length; row++) {
        result[row] = [];

        for (let column = 0; column < first.length; column++) {
            const value = first[row][column]
                .scale(probability)
                .add(
                    second[row][column]
                        .scale(1 - probability)
                );

            result[row][column] = value;
        }
    }

    return result;
}

// ---------------------------------------------------------------------------
// Section 10: Noise
// ---------------------------------------------------------------------------

function applyBitFlipNoise(state, probability, random = Math.random) {
    if (probability < 0 || probability > 1) {
        throw new Error("Noise probability must be between 0 and 1.");
    }

    return random() < probability
        ? applyGate(state, X)
        : cloneVector(state);
}

// ---------------------------------------------------------------------------
// Section 11: Educational BB84-style example
// ---------------------------------------------------------------------------

function prepareBB84State(bit, basis) {
    if (![0, 1].includes(bit)) {
        throw new Error("BB84 bit must be 0 or 1.");
    }

    if (![0, 1].includes(basis)) {
        throw new Error("BB84 basis must be 0 or 1.");
    }

    let state = basisState(bit);

    if (basis === 1) {
        state = applyGate(state, H);
    }

    return state;
}

function measureBB84State(state, basis, random = Math.random) {
    let stateToMeasure = cloneVector(state);

    // X-basis measurement becomes computational measurement after H.
    if (basis === 1) {
        stateToMeasure = applyGate(
            stateToMeasure,
            H
        );
    }

    return Number(
        measureState(
            stateToMeasure,
            1,
            random
        ).outcome
    );
}

// ---------------------------------------------------------------------------
// Section 12: Demonstrations
// ---------------------------------------------------------------------------

function printState(state, label) {
    validateNormalizedState(state);

    console.log(`\n${label}`);

    state.forEach((amplitude, index) => {
        if (amplitude.magnitude() > 1e-10) {
            console.log(
                `  |${index}> amplitude=${amplitude.toString()} ` +
                `probability=${amplitude.magnitudeSquared().toFixed(6)}`
            );
        }
    });
}

function demonstrateBasics() {
    console.log("\n=== QUBIT BASICS ===");

    printState(
        basisState(0),
        "|0>"
    );

    printState(
        basisState(1),
        "|1>"
    );

    const plus = applyGate(
        basisState(0),
        H
    );

    printState(
        plus,
        "H|0> = |+>"
    );

    console.log(
        "Measurement statistics:",
        sampleMeasurements(
            plus,
            1,
            2000
        )
    );
}

function demonstrateInterference() {
    console.log("\n=== INTERFERENCE ===");

    let state = basisState(0);

    state = applyGate(state, H);
    state = applyGate(state, H);

    printState(
        state,
        "H followed by H"
    );

    state = basisState(0);
    state = applyGate(state, H);
    state = applyGate(state, Z);
    state = applyGate(state, H);

    printState(
        state,
        "H-Z-H"
    );
}

function demonstratePhase() {
    console.log("\n=== PHASE ===");

    const plus = applyGate(
        basisState(0),
        H
    );

    const minus = applyGate(
        plus,
        Z
    );

    printState(
        plus,
        "|+>"
    );

    printState(
        minus,
        "|->"
    );

    console.log(
        "The computational-basis probabilities alone do not reveal " +
        "all phase information."
    );
}

function demonstrateBlochSphere() {
    console.log("\n=== BLOCH SPHERE ===");

    const states = {
        "|0>": basisState(0),
        "|1>": basisState(1),
        "|+>": applyGate(basisState(0), H),
        "|->": applyGate(basisState(1), H)
    };

    for (const [name, state] of Object.entries(states)) {
        console.log(
            name,
            blochVector(state)
        );
    }
}

function demonstrateEntanglement() {
    console.log("\n=== ENTANGLEMENT ===");

    let state = computationalBasisState("00");

    state = applySingleQubitGate(
        state,
        H,
        0,
        2
    );

    state = applyCNOT(
        state,
        0,
        1,
        2
    );

    printState(
        state,
        "Bell state"
    );

    console.log(
        "Measurement statistics:",
        sampleMeasurements(
            state,
            2,
            2000
        )
    );
}

function demonstrateExpectationValues() {
    console.log("\n=== EXPECTATION VALUES ===");

    const plus = applyGate(
        basisState(0),
        H
    );

    for (const [name, operator] of [
        ["X", X],
        ["Y", Y],
        ["Z", Z]
    ]) {
        console.log(
            `<${name}> =`,
            expectationValue(
                plus,
                operator
            ).toString()
        );
    }
}

function demonstrateDensityMatrices() {
    console.log("\n=== DENSITY MATRICES ===");

    const zeroDensity = outerProduct(
        basisState(0),
        basisState(0)
    );

    const oneDensity = outerProduct(
        basisState(1),
        basisState(1)
    );

    const mixed = mixDensityMatrices(
        zeroDensity,
        oneDensity,
        0.5
    );

    console.log(
        "Trace:",
        trace(mixed).toString()
    );

    mixed.forEach(row => {
        console.log(
            row.map(value => value.toString()).join("    ")
        );
    });
}

function demonstrateNoise() {
    console.log("\n=== NOISE ===");

    let flips = 0;
    const trials = 1000;
    const random = createSeededRandom(2026);

    for (let i = 0; i < trials; i++) {
        const state = applyBitFlipNoise(
            basisState(0),
            0.10,
            random
        );

        if (state[1].magnitudeSquared() > 0.5) {
            flips++;
        }
    }

    console.log(
        `Observed bit flips: ${flips}/${trials}`
    );
}

function demonstrateCircuit() {
    console.log("\n=== QUANTUM CIRCUIT ===");

    const circuit = new QuantumCircuit(3);

    circuit.addGate(
        "H q0",
        H,
        0
    );

    circuit.addGate(
        "H q1",
        H,
        1
    );

    circuit.addCNOT(
        0,
        2
    );

    circuit.addGate(
        "Ry(pi/4) q1",
        ry(Math.PI / 4),
        1
    );

    circuit.addCNOT(
        1,
        2
    );

    circuit.describe();

    const finalState = circuit.run();

    printState(
        finalState,
        "Final three-qubit state"
    );

    console.log(
        "Measurement histogram:",
        circuit.measure(3000)
    );
}

function demonstrateBB84() {
    console.log("\n=== EDUCATIONAL BB84-STYLE SIMULATION ===");

    const random = createSeededRandom(77);

    const aliceBits = [];
    const aliceBases = [];
    const bobBases = [];
    const bobResults = [];

    for (let index = 0; index < 16; index++) {
        const bit = random() < 0.5 ? 0 : 1;
        const aliceBasis = random() < 0.5 ? 0 : 1;
        const bobBasis = random() < 0.5 ? 0 : 1;

        const state = prepareBB84State(
            bit,
            aliceBasis
        );

        const result = measureBB84State(
            state,
            bobBasis,
            random
        );

        aliceBits.push(bit);
        aliceBases.push(aliceBasis);
        bobBases.push(bobBasis);
        bobResults.push(result);
    }

    const aliceKey = [];
    const bobKey = [];

    for (let index = 0; index < aliceBits.length; index++) {
        if (aliceBases[index] === bobBases[index]) {
            aliceKey.push(aliceBits[index]);
            bobKey.push(bobResults[index]);
        }
    }

    console.log("Alice bits:", aliceBits);
    console.log("Alice bases:", aliceBases);
    console.log("Bob bases:", bobBases);
    console.log("Bob results:", bobResults);
    console.log("Alice sifted key:", aliceKey);
    console.log("Bob sifted key:", bobKey);

    const mismatches = aliceKey.filter(
        (bit, index) => bit !== bobKey[index]
    ).length;

    console.log(
        `Sifted mismatches: ${mismatches}/${aliceKey.length}`
    );
}

// ---------------------------------------------------------------------------
// Section 13: Deterministic pseudo-random generator
// ---------------------------------------------------------------------------

function createSeededRandom(seed) {
    let state = seed >>> 0;

    return function random() {
        state += 0x6D2B79F5;

        let value = state;
        value = Math.imul(
            value ^ (value >>> 15),
            value | 1
        );

        value ^= value +
            Math.imul(
                value ^ (value >>> 7),
                value | 61
            );

        return (
            (value ^ (value >>> 14)) >>> 0
        ) / 4294967296;
    };
}

// ---------------------------------------------------------------------------
// Section 14: Edge cases and gate checks
// ---------------------------------------------------------------------------

function demonstrateValidation() {
    console.log("\n=== VALIDATION AND EDGE CASES ===");

    const tests = [
        [
            "Invalid basis bit",
            () => basisState(3)
        ],
        [
            "Zero-vector normalization",
            () => normalizeState([C0, C0])
        ],
        [
            "Invalid CNOT",
            () => applyCNOT(
                computationalBasisState("00"),
                0,
                0,
                2
            )
        ],
        [
            "Invalid measurement count",
            () => sampleMeasurements(
                basisState(0),
                1,
                0
            )
        ]
    ];

    for (const [description, test] of tests) {
        try {
            test();
            console.log(
                `${description}: unexpectedly accepted`
            );
        } catch (error) {
            console.log(
                `${description}: correctly rejected -> ${error.message}`
            );
        }
    }
}

function demonstrateGateProperties() {
    console.log("\n=== GATE UNITARITY ===");

    const gates = {
        I,
        X,
        Y,
        Z,
        H,
        S,
        T,
        "Rx(pi/3)": rx(Math.PI / 3),
        "Ry(pi/3)": ry(Math.PI / 3),
        "Rz(pi/3)": rz(Math.PI / 3),
        CNOT,
        SWAP
    };

    for (const [name, gate] of Object.entries(gates)) {
        console.log(
            `${name.padEnd(10)} -> unitary=${isUnitary(gate)}`
        );
    }
}

function demonstrateScaling() {
    console.log("\n=== STATE-VECTOR SCALING ===");

    for (const numberOfQubits of [
        1,
        2,
        4,
        8,
        12,
        16,
        20
    ]) {
        console.log(
            `${numberOfQubits} qubits -> ` +
            `${2 ** numberOfQubits} amplitudes`
        );
    }

    console.log(
        "A dense classical state-vector simulator therefore has " +
        "exponential memory growth with qubit count."
    );
}

// ---------------------------------------------------------------------------
// Section 15: Main
// ---------------------------------------------------------------------------

function main() {
    console.log(
        "============================================================"
    );
    console.log(
        "QUBITS: JAVASCRIPT QUANTUM STATE-VECTOR STUDY"
    );
    console.log(
        "============================================================"
    );

    demonstrateBasics();
    demonstrateInterference();
    demonstratePhase();
    demonstrateBlochSphere();
    demonstrateEntanglement();
    demonstrateExpectationValues();
    demonstrateDensityMatrices();
    demonstrateNoise();
    demonstrateCircuit();
    demonstrateBB84();
    demonstrateValidation();
    demonstrateGateProperties();
    demonstrateScaling();

    console.log(
        "\n=== END OF QUBIT STUDY ==="
    );
}

main();
