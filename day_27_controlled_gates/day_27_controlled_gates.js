/*
 * Controlled Gates: Controlled-X and Controlled Operations
 * =========================================================
 *
 * Self-contained JavaScript study implementation.
 *
 * The program begins with classical conditional behavior and single-qubit
 * operations, then builds controlled-X, controlled-Z, controlled-phase,
 * Bell-state preparation, general controlled operations, SWAP decomposition,
 * Toffoli gates, measurement, validation, and a small circuit abstraction.
 *
 * No external packages are required.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. BASIC COMPLEX-NUMBER SUPPORT
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

    scale(value) {
        return new Complex(
            this.real * value,
            this.imaginary * value
        );
    }

    conjugate() {
        return new Complex(this.real, -this.imaginary);
    }

    magnitudeSquared() {
        return this.real * this.real + this.imaginary * this.imaginary;
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    toString() {
        const epsilon = 1e-10;
        const real = Math.abs(this.real) < epsilon ? 0 : this.real;
        const imaginary = Math.abs(this.imaginary) < epsilon ? 0 : this.imaginary;

        if (imaginary === 0) {
            return real.toFixed(6).replace(/\.?0+$/, "");
        }

        if (real === 0) {
            return `${imaginary.toFixed(6).replace(/\.?0+$/, "")}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";
        return (
            `${real.toFixed(6).replace(/\.?0+$/, "")}` +
            `${sign}${Math.abs(imaginary).toFixed(6).replace(/\.?0+$/, "")}i`
        );
    }
}

const ZERO_COMPLEX = () => new Complex(0, 0);
const ONE_COMPLEX = () => new Complex(1, 0);
const I_COMPLEX = () => new Complex(0, 1);

const EPSILON = 1e-10;


// ---------------------------------------------------------------------------
// 2. COMPLEX MATRIX OPERATIONS
// ---------------------------------------------------------------------------

function cloneMatrix(matrix) {
    return matrix.map(row => row.map(value => new Complex(value.real, value.imaginary)));
}

function matrixMultiply(left, right) {
    if (left.length === 0 || right.length === 0) {
        throw new Error("Matrices cannot be empty.");
    }

    if (left[0].length !== right.length) {
        throw new Error("Matrix dimensions are incompatible.");
    }

    const result = Array.from(
        { length: left.length },
        () => Array.from(
            { length: right[0].length },
            ZERO_COMPLEX
        )
    );

    for (let row = 0; row < left.length; row++) {
        for (let column = 0; column < right[0].length; column++) {
            let value = ZERO_COMPLEX();

            for (let k = 0; k < right.length; k++) {
                value = value.add(left[row][k].multiply(right[k][column]));
            }

            result[row][column] = value;
        }
    }

    return result;
}

function matrixVectorMultiply(matrix, vector) {
    if (matrix[0].length !== vector.length) {
        throw new Error("Matrix and vector dimensions are incompatible.");
    }

    return matrix.map(row => {
        let value = ZERO_COMPLEX();

        for (let column = 0; column < vector.length; column++) {
            value = value.add(row[column].multiply(vector[column]));
        }

        return value;
    });
}

function conjugateTranspose(matrix) {
    return Array.from(
        { length: matrix[0].length },
        (_, column) =>
            Array.from(
                { length: matrix.length },
                (_, row) => matrix[row][column].conjugate()
            )
    );
}

function isUnitary(matrix) {
    const product = matrixMultiply(
        conjugateTranspose(matrix),
        matrix
    );

    for (let row = 0; row < product.length; row++) {
        for (let column = 0; column < product.length; column++) {
            const expected = row === column ? 1 : 0;

            if (Math.abs(product[row][column].real - expected) > 1e-9) {
                return false;
            }

            if (Math.abs(product[row][column].imaginary) > 1e-9) {
                return false;
            }
        }
    }

    return true;
}


// ---------------------------------------------------------------------------
// 3. BASIC QUANTUM GATES
// ---------------------------------------------------------------------------

const I = [
    [new Complex(1), new Complex(0)],
    [new Complex(0), new Complex(1)]
];

const X = [
    [new Complex(0), new Complex(1)],
    [new Complex(1), new Complex(0)]
];

const Y = [
    [new Complex(0), new Complex(0, -1)],
    [new Complex(0, 1), new Complex(0)]
];

const Z = [
    [new Complex(1), new Complex(0)],
    [new Complex(0), new Complex(-1)]
];

const H = [
    [new Complex(1 / Math.sqrt(2)), new Complex(1 / Math.sqrt(2))],
    [new Complex(1 / Math.sqrt(2)), new Complex(-1 / Math.sqrt(2))]
];

function phaseGate(theta) {
    return [
        [new Complex(1), new Complex(0)],
        [new Complex(0), new Complex(Math.cos(theta), Math.sin(theta))]
    ];
}


// ---------------------------------------------------------------------------
// 4. BASIS STATES AND STATE UTILITIES
// ---------------------------------------------------------------------------

function basisState(bits) {
    if (!/^[01]+$/.test(bits)) {
        throw new Error("bits must contain only 0 and 1.");
    }

    const dimension = 2 ** bits.length;
    const state = Array.from({ length: dimension }, ZERO_COMPLEX);

    state[parseInt(bits, 2)] = ONE_COMPLEX();

    return state;
}

function numberOfQubits(state) {
    const qubits = Math.log2(state.length);

    if (!Number.isInteger(qubits)) {
        throw new Error("State length must be a power of two.");
    }

    return qubits;
}

function basisLabel(index, qubits) {
    return index.toString(2).padStart(qubits, "0");
}

function probabilities(state) {
    return state.map(amplitude => amplitude.magnitudeSquared());
}

function stateNorm(state) {
    return Math.sqrt(
        state.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        )
    );
}

function normalizeState(state) {
    const norm = stateNorm(state);

    if (norm < EPSILON) {
        throw new Error("Cannot normalize a zero vector.");
    }

    return state.map(amplitude => amplitude.scale(1 / norm));
}

function validateNormalizedState(state) {
    const total = probabilities(state).reduce(
        (sum, probability) => sum + probability,
        0
    );

    if (Math.abs(total - 1) > 1e-9) {
        throw new Error(
            `State is not normalized. Total probability = ${total}`
        );
    }
}

function printState(state, title = "") {
    if (title) {
        console.log(`\n${title}`);
    }

    const qubits = numberOfQubits(state);
    const terms = [];

    for (let index = 0; index < state.length; index++) {
        if (state[index].magnitude() > EPSILON) {
            terms.push(
                `(${state[index].toString()})|${basisLabel(index, qubits)}>`
            );
        }
    }

    console.log(terms.length > 0 ? terms.join(" + ") : "0");
}

function printMatrix(matrix, title = "") {
    if (title) {
        console.log(`\n${title}`);
    }

    for (const row of matrix) {
        console.log(
            `[ ${row.map(value => value.toString()).join(", ")} ]`
        );
    }
}


// ---------------------------------------------------------------------------
// 5. CONTROLLED MATRIX CONSTRUCTION
// ---------------------------------------------------------------------------

function controlledMatrix(operation) {
    if (
        operation.length !== 2 ||
        operation.some(row => row.length !== 2)
    ) {
        throw new Error("A controlled target operation must be 2x2.");
    }

    /*
     * Controlled-U has the block form:
     *
     *     [ I  0 ]
     *     [ 0  U ]
     *
     * in computational basis ordering |00>, |01>, |10>, |11>.
     */
    const result = Array.from(
        { length: 4 },
        () => Array.from({ length: 4 }, ZERO_COMPLEX)
    );

    result[0][0] = ONE_COMPLEX();
    result[1][1] = ONE_COMPLEX();

    result[2][2] = operation[0][0];
    result[2][3] = operation[0][1];
    result[3][2] = operation[1][0];
    result[3][3] = operation[1][1];

    return result;
}

const CX = controlledMatrix(X);
const CY = controlledMatrix(Y);
const CZ = controlledMatrix(Z);


// ---------------------------------------------------------------------------
// 6. DIRECT SINGLE-QUBIT OPERATION
// ---------------------------------------------------------------------------

function applySingleQubitGate(state, operation, targetQubit) {
    const qubits = numberOfQubits(state);

    if (targetQubit < 0 || targetQubit >= qubits) {
        throw new Error("Target qubit is outside the register.");
    }

    const result = state.map(value => new Complex(value.real, value.imaginary));

    /*
     * A qubit corresponds to one binary bit in the basis-state index.
     * Pairing target=0 and target=1 amplitudes lets us apply a local
     * 2x2 operation without constructing a huge full-register matrix.
     */
    const bitPosition = qubits - 1 - targetQubit;
    const mask = 1 << bitPosition;

    for (let baseIndex = 0; baseIndex < state.length; baseIndex++) {
        if ((baseIndex & mask) !== 0) {
            continue;
        }

        const zeroIndex = baseIndex;
        const oneIndex = baseIndex | mask;

        const zeroAmplitude = state[zeroIndex];
        const oneAmplitude = state[oneIndex];

        result[zeroIndex] =
            operation[0][0].multiply(zeroAmplitude)
                .add(operation[0][1].multiply(oneAmplitude));

        result[oneIndex] =
            operation[1][0].multiply(zeroAmplitude)
                .add(operation[1][1].multiply(oneAmplitude));
    }

    return result;
}


// ---------------------------------------------------------------------------
// 7. GENERAL CONTROLLED OPERATION
// ---------------------------------------------------------------------------

function applyControlledOperation(
    state,
    controlQubit,
    targetQubit,
    operation
) {
    const qubits = numberOfQubits(state);

    if (controlQubit < 0 || controlQubit >= qubits) {
        throw new Error("Control qubit is outside the register.");
    }

    if (targetQubit < 0 || targetQubit >= qubits) {
        throw new Error("Target qubit is outside the register.");
    }

    if (controlQubit === targetQubit) {
        throw new Error("Control and target must be different qubits.");
    }

    if (
        operation.length !== 2 ||
        operation.some(row => row.length !== 2)
    ) {
        throw new Error("Target operation must be 2x2.");
    }

    const result = state.map(value => new Complex(value.real, value.imaginary));

    const controlPosition = qubits - 1 - controlQubit;
    const targetPosition = qubits - 1 - targetQubit;

    const controlMask = 1 << controlPosition;
    const targetMask = 1 << targetPosition;

    for (let baseIndex = 0; baseIndex < state.length; baseIndex++) {
        if ((baseIndex & targetMask) !== 0) {
            continue;
        }

        /*
         * Controlled-U acts as identity on branches where control = 0.
         */
        if ((baseIndex & controlMask) === 0) {
            continue;
        }

        const zeroIndex = baseIndex;
        const oneIndex = baseIndex | targetMask;

        const zeroAmplitude = state[zeroIndex];
        const oneAmplitude = state[oneIndex];

        result[zeroIndex] =
            operation[0][0].multiply(zeroAmplitude)
                .add(operation[0][1].multiply(oneAmplitude));

        result[oneIndex] =
            operation[1][0].multiply(zeroAmplitude)
                .add(operation[1][1].multiply(oneAmplitude));
    }

    return result;
}

function applyCX(state, controlQubit, targetQubit) {
    return applyControlledOperation(
        state,
        controlQubit,
        targetQubit,
        X
    );
}


// ---------------------------------------------------------------------------
// 8. BEGINNER: X AND H
// ---------------------------------------------------------------------------

function beginnerExample() {
    console.log("\n" + "=".repeat(72));
    console.log("BEGINNER: SINGLE-QUBIT OPERATIONS");
    console.log("=".repeat(72));

    printState(
        basisState("0"),
        "Initial state"
    );

    printState(
        matrixVectorMultiply(X, basisState("0")),
        "X|0>"
    );

    printState(
        matrixVectorMultiply(H, basisState("0")),
        "H|0> = |+>"
    );

    console.log(
        "Probabilities:",
        probabilities(matrixVectorMultiply(H, basisState("0")))
    );
}


// ---------------------------------------------------------------------------
// 9. CX TRUTH TABLE
// ---------------------------------------------------------------------------

function cxTruthTable() {
    console.log("\n" + "=".repeat(72));
    console.log("CONTROLLED-X TRUTH TABLE");
    console.log("=".repeat(72));

    console.log("Control Target -> Output");

    for (const control of ["0", "1"]) {
        for (const target of ["0", "1"]) {
            const input = basisState(control + target);
            const output = matrixVectorMultiply(CX, input);

            const index = output.findIndex(
                amplitude => amplitude.magnitude() > EPSILON
            );

            console.log(
                `${control}       ${target}      -> |${basisLabel(index, 2)}>`
            );
        }
    }

    console.log("\nCX rule: target_out = target XOR control.");
}


// ---------------------------------------------------------------------------
// 10. MATRIX VIEW
// ---------------------------------------------------------------------------

function controlledMatrixExample() {
    console.log("\n" + "=".repeat(72));
    console.log("MATRIX REPRESENTATION OF CX");
    console.log("=".repeat(72));

    printMatrix(CX, "CX");
    console.log("CX is unitary:", isUnitary(CX));

    console.log(
        "The upper 2x2 block is identity because control=0 does nothing."
    );
}


// ---------------------------------------------------------------------------
// 11. CONTROLLED-Z AND CONTROLLED-PHASE
// ---------------------------------------------------------------------------

function controlledZExample() {
    console.log("\n" + "=".repeat(72));
    console.log("CONTROLLED-Z");
    console.log("=".repeat(72));

    printMatrix(CZ, "CZ matrix");

    for (const bits of ["00", "01", "10", "11"]) {
        printState(
            matrixVectorMultiply(CZ, basisState(bits)),
            `CZ|${bits}>`
        );
    }
}

function controlledPhaseExample() {
    console.log("\n" + "=".repeat(72));
    console.log("CONTROLLED-PHASE");
    console.log("=".repeat(72));

    const theta = Math.PI / 2;
    const operation = controlledMatrix(phaseGate(theta));

    printMatrix(
        operation,
        "Controlled phase with theta = pi/2"
    );

    printState(
        matrixVectorMultiply(operation, basisState("11")),
        "Result on |11>"
    );
}


// ---------------------------------------------------------------------------
// 12. BELL STATE
// ---------------------------------------------------------------------------

function bellState() {
    /*
     * Bell-state preparation:
     *
     * |00>
     *  |
     * H on q0
     *  |
     * (|00> + |10>)/sqrt(2)
     *  |
     * CX q0 -> q1
     *  |
     * (|00> + |11>)/sqrt(2)
     */
    let state = basisState("00");

    state = applySingleQubitGate(
        state,
        H,
        0
    );

    state = applyCX(
        state,
        0,
        1
    );

    return state;
}

function bellStateExample() {
    console.log("\n" + "=".repeat(72));
    console.log("BELL STATE AND ENTANGLEMENT");
    console.log("=".repeat(72));

    const state = bellState();

    printState(
        state,
        "(|00> + |11>)/sqrt(2)"
    );

    console.log(
        "Probabilities:",
        probabilities(state)
    );

    return state;
}


// ---------------------------------------------------------------------------
// 13. MEASUREMENT
// ---------------------------------------------------------------------------

function measure(state, randomFunction = Math.random) {
    validateNormalizedState(state);

    const distribution = probabilities(state);
    const randomValue = randomFunction();

    let cumulative = 0;

    for (let index = 0; index < distribution.length; index++) {
        cumulative += distribution[index];

        if (randomValue <= cumulative) {
            const collapsed = state.map(() => ZERO_COMPLEX());
            collapsed[index] = ONE_COMPLEX();

            return {
                index,
                state: collapsed
            };
        }
    }

    const finalIndex = distribution.length - 1;
    const collapsed = state.map(() => ZERO_COMPLEX());
    collapsed[finalIndex] = ONE_COMPLEX();

    return {
        index: finalIndex,
        state: collapsed
    };
}

function measurementExample() {
    console.log("\n" + "=".repeat(72));
    console.log("MEASUREMENT AND COLLAPSE");
    console.log("=".repeat(72));

    const state = bellState();

    printState(
        state,
        "Before measurement"
    );

    const result = measure(
        state,
        () => 0.73
    );

    console.log(
        "Measured:",
        basisLabel(result.index, 2)
    );

    printState(
        result.state,
        "Collapsed state"
    );
}


// ---------------------------------------------------------------------------
// 14. MULTI-QUBIT CONTROLLED OPERATION
// ---------------------------------------------------------------------------

function multiQubitExample() {
    console.log("\n" + "=".repeat(72));
    console.log("THREE-QUBIT CONTROLLED OPERATION");
    console.log("=".repeat(72));

    let state = basisState("100");

    printState(
        state,
        "Initial |100>"
    );

    state = applyCX(
        state,
        0,
        2
    );

    printState(
        state,
        "After CX(q0 -> q2)"
    );

    state = applyControlledOperation(
        state,
        0,
        2,
        Z
    );

    printState(
        state,
        "After CZ(q0 -> q2)"
    );
}


// ---------------------------------------------------------------------------
// 15. GENERAL CONTROLLED UNITARY
// ---------------------------------------------------------------------------

function generalControlledUnitaryExample() {
    console.log("\n" + "=".repeat(72));
    console.log("GENERAL CONTROLLED UNITARY");
    console.log("=".repeat(72));

    const theta = Math.PI / 3;
    const U = phaseGate(theta);
    const controlledU = controlledMatrix(U);

    console.log("U is unitary:", isUnitary(U));
    console.log("Controlled-U is unitary:", isUnitary(controlledU));

    printMatrix(
        controlledU,
        "Controlled phase gate"
    );

    const state = matrixVectorMultiply(
        controlledU,
        basisState("11")
    );

    printState(
        state,
        "Controlled-U|11>"
    );
}


// ---------------------------------------------------------------------------
// 16. SWAP FROM THREE CX GATES
// ---------------------------------------------------------------------------

function swapUsingCX(state, firstQubit, secondQubit) {
    if (firstQubit === secondQubit) {
        throw new Error("SWAP requires two distinct qubits.");
    }

    state = applyCX(state, firstQubit, secondQubit);
    state = applyCX(state, secondQubit, firstQubit);
    state = applyCX(state, firstQubit, secondQubit);

    return state;
}

function swapExample() {
    console.log("\n" + "=".repeat(72));
    console.log("SWAP DECOMPOSED INTO THREE CX GATES");
    console.log("=".repeat(72));

    for (const bits of ["00", "01", "10", "11"]) {
        const result = swapUsingCX(
            basisState(bits),
            0,
            1
        );

        const index = result.findIndex(
            amplitude => amplitude.magnitude() > EPSILON
        );

        console.log(
            `|${bits}> -> |${basisLabel(index, 2)}>`
        );
    }

    console.log(
        "The identity CX(a,b) CX(b,a) CX(a,b) implements SWAP."
    );
}


// ---------------------------------------------------------------------------
// 17. TOFFOLI
// ---------------------------------------------------------------------------

function applyToffoli(state, firstControl, secondControl, target) {
    const qubits = numberOfQubits(state);

    if (
        new Set([firstControl, secondControl, target]).size !== 3
    ) {
        throw new Error("Toffoli requires three distinct qubits.");
    }

    for (const qubit of [firstControl, secondControl, target]) {
        if (qubit < 0 || qubit >= qubits) {
            throw new Error("Toffoli qubit index is invalid.");
        }
    }

    const result = state.map(
        amplitude => new Complex(amplitude.real, amplitude.imaginary)
    );

    const firstMask = 1 << (qubits - 1 - firstControl);
    const secondMask = 1 << (qubits - 1 - secondControl);
    const targetMask = 1 << (qubits - 1 - target);

    for (let baseIndex = 0; baseIndex < state.length; baseIndex++) {
        if ((baseIndex & targetMask) !== 0) {
            continue;
        }

        const bothControlsAreOne =
            (baseIndex & firstMask) !== 0 &&
            (baseIndex & secondMask) !== 0;

        if (!bothControlsAreOne) {
            continue;
        }

        const zeroIndex = baseIndex;
        const oneIndex = baseIndex | targetMask;

        result[zeroIndex] = state[oneIndex];
        result[oneIndex] = state[zeroIndex];
    }

    return result;
}

function toffoliExample() {
    console.log("\n" + "=".repeat(72));
    console.log("TOFFOLI: CONTROLLED-CONTROLLED-X");
    console.log("=".repeat(72));

    for (const bits of [
        "000", "001", "010", "011",
        "100", "101", "110", "111"
    ]) {
        const output = applyToffoli(
            basisState(bits),
            0,
            1,
            2
        );

        const index = output.findIndex(
            amplitude => amplitude.magnitude() > EPSILON
        );

        console.log(
            `|${bits}> -> |${basisLabel(index, 3)}>`
        );
    }
}


// ---------------------------------------------------------------------------
// 18. SMALL CIRCUIT ABSTRACTION
// ---------------------------------------------------------------------------

class QuantumCircuit {
    constructor(numberOfQubits) {
        if (!Number.isInteger(numberOfQubits) || numberOfQubits <= 0) {
            throw new Error("numberOfQubits must be a positive integer.");
        }

        this.numberOfQubits = numberOfQubits;
        this.state = basisState("0".repeat(numberOfQubits));
        this.operations = [];
    }

    addSingleQubitGate(name, operation, target) {
        this.operations.push({
            name,
            apply: state => applySingleQubitGate(
                state,
                operation,
                target
            )
        });
    }

    addControlledGate(
        name,
        operation,
        control,
        target
    ) {
        this.operations.push({
            name,
            apply: state => applyControlledOperation(
                state,
                control,
                target,
                operation
            )
        });
    }

    run() {
        for (const operation of this.operations) {
            this.state = operation.apply(this.state);
        }

        return this.state;
    }

    describe() {
        console.log("\nCircuit:");

        this.operations.forEach(
            (operation, index) => {
                console.log(`${index + 1}. ${operation.name}`);
            }
        );
    }
}

function circuitExample() {
    console.log("\n" + "=".repeat(72));
    console.log("CIRCUIT ABSTRACTION");
    console.log("=".repeat(72));

    const circuit = new QuantumCircuit(2);

    circuit.addSingleQubitGate(
        "H(q0)",
        H,
        0
    );

    circuit.addControlledGate(
        "CX(q0 -> q1)",
        X,
        0,
        1
    );

    circuit.describe();

    printState(
        circuit.run(),
        "Circuit output"
    );
}


// ---------------------------------------------------------------------------
// 19. CONTROLLED SUPERPOSITION
// ---------------------------------------------------------------------------

function controlledSuperpositionExample() {
    console.log("\n" + "=".repeat(72));
    console.log("CONTROLLED-X ON A SUPERPOSITION");
    console.log("=".repeat(72));

    let state = basisState("00");

    state = applySingleQubitGate(
        state,
        H,
        0
    );

    printState(
        state,
        "Before CX"
    );

    state = applyCX(
        state,
        0,
        1
    );

    printState(
        state,
        "After CX"
    );

    console.log(
        "The control's two branches undergo different conditional "
        + "transformations."
    );
}


// ---------------------------------------------------------------------------
// 20. RELATIVE PHASE
// ---------------------------------------------------------------------------

function relativePhaseExample() {
    console.log("\n" + "=".repeat(72));
    console.log("CONTROLLED-Z AND RELATIVE PHASE");
    console.log("=".repeat(72));

    let state = basisState("10");

    state = applySingleQubitGate(
        state,
        H,
        1
    );

    printState(
        state,
        "Control=1, target=|+>"
    );

    state = applyControlledOperation(
        state,
        0,
        1,
        Z
    );

    printState(
        state,
        "After CZ"
    );

    state = applySingleQubitGate(
        state,
        H,
        1
    );

    printState(
        state,
        "After another H on target"
    );

    console.log(
        "Probabilities:",
        probabilities(state)
    );
}


// ---------------------------------------------------------------------------
// 21. EDGE CASES
// ---------------------------------------------------------------------------

function edgeCases() {
    console.log("\n" + "=".repeat(72));
    console.log("EDGE CASES AND VALIDATION");
    console.log("=".repeat(72));

    const tests = [
        [
            "Same control and target",
            () => applyCX(basisState("00"), 0, 0)
        ],
        [
            "Invalid control",
            () => applyCX(basisState("00"), 2, 1)
        ],
        [
            "Invalid target",
            () => applyCX(basisState("00"), 0, 2)
        ],
        [
            "Invalid basis state",
            () => basisState("012")
        ],
        [
            "Zero-vector normalization",
            () => normalizeState([
                new Complex(0),
                new Complex(0)
            ])
        ]
    ];

    for (const [description, action] of tests) {
        try {
            action();
            console.log(`${description}: ERROR, validation failed`);
        } catch (error) {
            console.log(
                `${description}: correctly rejected -> ${error.message}`
            );
        }
    }
}


// ---------------------------------------------------------------------------
// 22. SELF-INVERSE PROPERTY
// ---------------------------------------------------------------------------

function selfInverseExample() {
    console.log("\n" + "=".repeat(72));
    console.log("CX IS SELF-INVERSE");
    console.log("=".repeat(72));

    for (const bits of ["00", "01", "10", "11"]) {
        const once = applyCX(
            basisState(bits),
            0,
            1
        );

        const twice = applyCX(
            once,
            0,
            1
        );

        const index = twice.findIndex(
            amplitude => amplitude.magnitude() > EPSILON
        );

        console.log(
            `|${bits}> -> CX -> CX -> |${basisLabel(index, 2)}>`
        );
    }

    console.log("Therefore CX * CX = I.");
}


// ---------------------------------------------------------------------------
// 23. PERFORMANCE CONSIDERATIONS
// ---------------------------------------------------------------------------

function performanceExplanation() {
    console.log("\n" + "=".repeat(72));
    console.log("PERFORMANCE AND SCALING");
    console.log("=".repeat(72));

    console.log("Qubits | State amplitudes");

    for (let qubits = 1; qubits <= 12; qubits++) {
        console.log(
            `${String(qubits).padStart(6)} | ${(2 ** qubits)}`
        );
    }

    console.log(
        "\nA state-vector simulator requires O(2^n) storage."
    );

    console.log(
        "Direct local gate application processes O(2^n) amplitudes "
        + "without explicitly constructing a 2^n x 2^n matrix."
    );

    console.log(
        "Typed arrays and specialized numerical libraries can reduce "
        + "allocation overhead in production simulators."
    );
}


// ---------------------------------------------------------------------------
// 24. COMMON MISTAKES
// ---------------------------------------------------------------------------

function commonMistakes() {
    console.log("\n" + "=".repeat(72));
    console.log("COMMON MISTAKES");
    console.log("=".repeat(72));

    const mistakes = [
        "Assuming CX always flips the target. It acts conditionally.",
        "Confusing amplitudes with probabilities. Probability is |a|^2.",
        "Dropping complex phase information.",
        "Confusing CX with CZ.",
        "Ignoring control/target ordering.",
        "Assuming classical correlation and quantum entanglement are identical.",
        "Building enormous full matrices when direct state-vector updates are sufficient.",
        "Comparing floating-point amplitudes with exact equality."
    ];

    mistakes.forEach(
        (mistake, index) => console.log(`${index + 1}. ${mistake}`)
    );
}


// ---------------------------------------------------------------------------
// 25. APPLICATION CASE STUDY: REVERSIBLE CONDITIONAL DATA TRANSFORM
// ---------------------------------------------------------------------------

function reversibleDataTransform() {
    console.log("\n" + "=".repeat(72));
    console.log("CASE STUDY: REVERSIBLE CONDITIONAL TRANSFORM");
    console.log("=".repeat(72));

    /*
     * Suppose q0 stores a control condition and q1 stores a binary flag.
     * CX implements:
     *
     *     q1 <- q1 XOR q0
     *
     * Because XOR is reversible, applying the same transformation again
     * restores the original q1 value.
     */

    const records = [
        { control: 0, target: 0 },
        { control: 0, target: 1 },
        { control: 1, target: 0 },
        { control: 1, target: 1 }
    ];

    for (const record of records) {
        const result = record.target ^ record.control;

        console.log(
            `control=${record.control}, `
            + `target=${record.target} `
            + `-> newTarget=${result}`
        );
    }

    console.log(
        "This classical truth-table interpretation corresponds to CX "
        + "on computational-basis states."
    );
}


// ---------------------------------------------------------------------------
// 26. FULL PROGRAM
// ---------------------------------------------------------------------------

function main() {
    console.log("=".repeat(72));
    console.log("CONTROLLED GATES STUDY PROGRAM");
    console.log("Controlled-X and Controlled Quantum Operations");
    console.log("=".repeat(72));

    beginnerExample();
    cxTruthTable();
    controlledMatrixExample();
    controlledZExample();
    controlledPhaseExample();

    bellStateExample();
    measurementExample();

    multiQubitExample();
    generalControlledUnitaryExample();

    swapExample();
    toffoliExample();

    circuitExample();
    controlledSuperpositionExample();
    relativePhaseExample();

    edgeCases();
    selfInverseExample();

    reversibleDataTransform();
    performanceExplanation();
    commonMistakes();

    console.log("\n" + "=".repeat(72));
    console.log("END OF PROGRAM");
    console.log("=".repeat(72));
}

main();
