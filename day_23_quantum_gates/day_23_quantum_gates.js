/*
 * Quantum Gates: X, Y, Z, and Identity
 *
 * A self-contained JavaScript study program covering the practical
 * representation and manipulation of single-qubit quantum states.
 *
 * The implementation uses only standard JavaScript features and can be
 * executed with Node.js.
 *
 * The program emphasizes:
 *   - complex amplitudes
 *   - state vectors
 *   - matrix multiplication
 *   - X, Y, Z, and Identity gates
 *   - unitary transformations
 *   - measurement probabilities
 *   - measurement simulation
 *   - global and relative phase
 *   - Bloch-sphere coordinates
 *   - gate composition
 *   - tensor products
 *   - two-qubit Bell states
 *   - validation and testing
 */

// -----------------------------------------------------------------------------
// Complex numbers
// -----------------------------------------------------------------------------

class Complex {
    constructor(real = 0, imaginary = 0) {
        if (!Number.isFinite(real) || !Number.isFinite(imaginary)) {
            throw new TypeError("Complex components must be finite numbers.");
        }

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

    magnitudeSquared() {
        return (
            this.real * this.real +
            this.imaginary * this.imaginary
        );
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    scale(value) {
        return new Complex(
            this.real * value,
            this.imaginary * value
        );
    }

    equals(other, tolerance = 1e-10) {
        return (
            Math.abs(this.real - other.real) <= tolerance &&
            Math.abs(this.imaginary - other.imaginary) <= tolerance
        );
    }

    toString(digits = 4) {
        const clean = value =>
            Math.abs(value) < 10 ** (-digits) ? 0 : value;

        const real = clean(this.real);
        const imaginary = clean(this.imaginary);

        if (imaginary === 0) {
            return real.toFixed(digits);
        }

        if (real === 0) {
            return `${imaginary.toFixed(digits)}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";

        return (
            `${real.toFixed(digits)} ${sign} ` +
            `${Math.abs(imaginary).toFixed(digits)}i`
        );
    }
}


const ZERO_COMPLEX = new Complex(0, 0);
const ONE_COMPLEX = new Complex(1, 0);
const I_COMPLEX = new Complex(0, 1);

const EPSILON = 1e-10;
const SQRT_TWO = Math.sqrt(2);


// -----------------------------------------------------------------------------
// Vector utilities
// -----------------------------------------------------------------------------

function vectorNorm(vector) {
    return Math.sqrt(
        vector.reduce(
            (sum, value) => sum + value.magnitudeSquared(),
            0
        )
    );
}


function normalizeVector(vector) {
    const norm = vectorNorm(vector);

    if (norm <= EPSILON) {
        throw new Error("The zero vector cannot represent a quantum state.");
    }

    return vector.map(value => value.scale(1 / norm));
}


function validateSingleQubitVector(vector) {
    if (!Array.isArray(vector) || vector.length !== 2) {
        throw new Error(
            "A single-qubit state must contain exactly two amplitudes."
        );
    }

    if (!vector.every(value => value instanceof Complex)) {
        throw new TypeError(
            "Every state amplitude must be a Complex number."
        );
    }

    const probabilitySum = vector.reduce(
        (sum, value) => sum + value.magnitudeSquared(),
        0
    );

    if (Math.abs(probabilitySum - 1) > EPSILON) {
        throw new Error(
            `State is not normalized. Probability sum = ${probabilitySum}`
        );
    }
}


// -----------------------------------------------------------------------------
// Matrix utilities
// -----------------------------------------------------------------------------

function matrixDimensions(matrix) {
    if (!Array.isArray(matrix) || matrix.length === 0) {
        throw new Error("Matrix cannot be empty.");
    }

    const columns = matrix[0].length;

    if (columns === 0) {
        throw new Error("Matrix cannot contain empty rows.");
    }

    for (const row of matrix) {
        if (!Array.isArray(row) || row.length !== columns) {
            throw new Error("Matrix must be rectangular.");
        }
    }

    return {
        rows: matrix.length,
        columns
    };
}


function matrixVectorMultiply(matrix, vector) {
    const { columns } = matrixDimensions(matrix);

    if (columns !== vector.length) {
        throw new Error(
            "Matrix and vector dimensions are incompatible."
        );
    }

    return matrix.map(row => {
        return row.reduce(
            (sum, value, index) =>
                sum.add(value.multiply(vector[index])),
            new Complex(0, 0)
        );
    });
}


function matrixMultiply(left, right) {
    const leftDimensions = matrixDimensions(left);
    const rightDimensions = matrixDimensions(right);

    if (leftDimensions.columns !== rightDimensions.rows) {
        throw new Error(
            "Matrix dimensions are incompatible for multiplication."
        );
    }

    const result = [];

    for (let row = 0; row < leftDimensions.rows; row++) {
        const outputRow = [];

        for (let column = 0; column < rightDimensions.columns; column++) {
            let value = new Complex(0, 0);

            for (let k = 0; k < leftDimensions.columns; k++) {
                value = value.add(
                    left[row][k].multiply(right[k][column])
                );
            }

            outputRow.push(value);
        }

        result.push(outputRow);
    }

    return result;
}


function conjugateTranspose(matrix) {
    const { rows, columns } = matrixDimensions(matrix);

    const result = [];

    for (let column = 0; column < columns; column++) {
        const row = [];

        for (let sourceRow = 0; sourceRow < rows; sourceRow++) {
            row.push(matrix[sourceRow][column].conjugate());
        }

        result.push(row);
    }

    return result;
}


function matricesAreClose(first, second, tolerance = EPSILON) {
    const firstDimensions = matrixDimensions(first);
    const secondDimensions = matrixDimensions(second);

    if (
        firstDimensions.rows !== secondDimensions.rows ||
        firstDimensions.columns !== secondDimensions.columns
    ) {
        return false;
    }

    for (let row = 0; row < firstDimensions.rows; row++) {
        for (let column = 0; column < firstDimensions.columns; column++) {
            if (
                !first[row][column].equals(
                    second[row][column],
                    tolerance
                )
            ) {
                return false;
            }
        }
    }

    return true;
}


function identityMatrix(size) {
    if (size <= 0) {
        throw new Error("Identity matrix size must be positive.");
    }

    return Array.from(
        { length: size },
        (_, row) =>
            Array.from(
                { length: size },
                (_, column) =>
                    new Complex(row === column ? 1 : 0, 0)
            )
    );
}


// -----------------------------------------------------------------------------
// Standard quantum gates
// -----------------------------------------------------------------------------

const IDENTITY = [
    [new Complex(1), new Complex(0)],
    [new Complex(0), new Complex(1)]
];

const X_GATE = [
    [new Complex(0), new Complex(1)],
    [new Complex(1), new Complex(0)]
];

const Y_GATE = [
    [new Complex(0), new Complex(0, -1)],
    [new Complex(0, 1), new Complex(0)]
];

const Z_GATE = [
    [new Complex(1), new Complex(0)],
    [new Complex(0), new Complex(-1)]
];

const GATES = {
    I: IDENTITY,
    X: X_GATE,
    Y: Y_GATE,
    Z: Z_GATE
};


// -----------------------------------------------------------------------------
// Qubit class
// -----------------------------------------------------------------------------

class Qubit {
    constructor(alpha, beta) {
        this.alpha = alpha;
        this.beta = beta;

        validateSingleQubitVector(this.vector);
    }

    get vector() {
        return [this.alpha, this.beta];
    }

    probabilityZero() {
        return this.alpha.magnitudeSquared();
    }

    probabilityOne() {
        return this.beta.magnitudeSquared();
    }

    applyGate(gate) {
        const dimensions = matrixDimensions(gate);

        if (
            dimensions.rows !== 2 ||
            dimensions.columns !== 2
        ) {
            throw new Error(
                "A single-qubit gate must be a 2x2 matrix."
            );
        }

        const transformed = matrixVectorMultiply(
            gate,
            this.vector
        );

        return new Qubit(
            transformed[0],
            transformed[1]
        );
    }

    measure(randomValue = Math.random()) {
        if (randomValue < 0 || randomValue > 1) {
            throw new RangeError(
                "Measurement random value must be between 0 and 1."
            );
        }

        const outcome =
            randomValue < this.probabilityZero() ? 0 : 1;

        if (outcome === 0) {
            this.alpha = new Complex(1);
            this.beta = new Complex(0);
        } else {
            this.alpha = new Complex(0);
            this.beta = new Complex(1);
        }

        return outcome;
    }

    toString() {
        return (
            `${this.alpha.toString()}|0> + ` +
            `(${this.beta.toString()})|1>`
        );
    }
}


// -----------------------------------------------------------------------------
// Standard states
// -----------------------------------------------------------------------------

function ketZero() {
    return new Qubit(
        new Complex(1),
        new Complex(0)
    );
}


function ketOne() {
    return new Qubit(
        new Complex(0),
        new Complex(1)
    );
}


function plusState() {
    return new Qubit(
        new Complex(1 / SQRT_TWO),
        new Complex(1 / SQRT_TWO)
    );
}


function minusState() {
    return new Qubit(
        new Complex(1 / SQRT_TWO),
        new Complex(-1 / SQRT_TWO)
    );
}


function plusIState() {
    return new Qubit(
        new Complex(1 / SQRT_TWO),
        new Complex(0, 1 / SQRT_TWO)
    );
}


// -----------------------------------------------------------------------------
// Gate helpers
// -----------------------------------------------------------------------------

function applyNamedGate(state, gateName) {
    const name = gateName.toUpperCase();

    if (!(name in GATES)) {
        throw new Error(`Unknown gate: ${gateName}`);
    }

    return state.applyGate(GATES[name]);
}


function composeGates(first, second) {
    // If first is applied and then second is applied,
    // the resulting matrix is second * first.
    return matrixMultiply(second, first);
}


function isUnitary(matrix) {
    const dimensions = matrixDimensions(matrix);

    if (dimensions.rows !== dimensions.columns) {
        return false;
    }

    const dagger = conjugateTranspose(matrix);
    const product = matrixMultiply(dagger, matrix);
    const identity = identityMatrix(dimensions.rows);

    return matricesAreClose(product, identity);
}


// -----------------------------------------------------------------------------
// Bloch sphere
// -----------------------------------------------------------------------------

function blochCoordinates(state) {
    const alpha = state.alpha;
    const beta = state.beta;

    // x = 2 Re(alpha* beta)
    // y = 2 Im(alpha* beta)
    // z = |alpha|^2 - |beta|^2
    const crossTerm = alpha.conjugate().multiply(beta);

    return {
        x: 2 * crossTerm.real,
        y: 2 * crossTerm.imaginary,
        z:
            alpha.magnitudeSquared() -
            beta.magnitudeSquared()
    };
}


// -----------------------------------------------------------------------------
// Expectation values
// -----------------------------------------------------------------------------

function expectationValue(state, operator) {
    const transformed = matrixVectorMultiply(
        operator,
        state.vector
    );

    const bra = [
        state.alpha.conjugate(),
        state.beta.conjugate()
    ];

    return bra.reduce(
        (sum, value, index) =>
            sum.add(value.multiply(transformed[index])),
        new Complex(0, 0)
    );
}


// -----------------------------------------------------------------------------
// Measurement simulation
// -----------------------------------------------------------------------------

function createSeededRandom(seed) {
    // A small deterministic generator is sufficient for a reproducible
    // educational simulation. It is not cryptographically secure.
    let state = seed >>> 0;

    return function random() {
        state = (
            Math.imul(1664525, state) +
            1013904223
        ) >>> 0;

        return state / 4294967296;
    };
}


function simulateMeasurements(state, shots = 10000, seed = 42) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new Error("shots must be a positive integer.");
    }

    const random = createSeededRandom(seed);

    let zeros = 0;
    let ones = 0;

    for (let i = 0; i < shots; i++) {
        if (random() < state.probabilityZero()) {
            zeros++;
        } else {
            ones++;
        }
    }

    return {
        zeros,
        ones,
        probabilityZero: zeros / shots,
        probabilityOne: ones / shots
    };
}


// -----------------------------------------------------------------------------
// Tensor products
// -----------------------------------------------------------------------------

function tensorProduct(left, right) {
    const result = [];

    for (const leftValue of left) {
        for (const rightValue of right) {
            result.push(leftValue.multiply(rightValue));
        }
    }

    return result;
}


function tensorMatrix(left, right) {
    const leftDimensions = matrixDimensions(left);
    const rightDimensions = matrixDimensions(right);

    const rows =
        leftDimensions.rows * rightDimensions.rows;

    const columns =
        leftDimensions.columns * rightDimensions.columns;

    const result = Array.from(
        { length: rows },
        () =>
            Array.from(
                { length: columns },
                () => new Complex(0)
            )
    );

    for (let i = 0; i < leftDimensions.rows; i++) {
        for (let j = 0; j < leftDimensions.columns; j++) {
            for (let k = 0; k < rightDimensions.rows; k++) {
                for (let l = 0; l < rightDimensions.columns; l++) {
                    result[
                        i * rightDimensions.rows + k
                    ][
                        j * rightDimensions.columns + l
                    ] = left[i][j].multiply(right[k][l]);
                }
            }
        }
    }

    return result;
}


// -----------------------------------------------------------------------------
// Display helpers
// -----------------------------------------------------------------------------

function printState(label, state) {
    console.log(label);
    console.log(`  State: ${state}`);
    console.log(
        `  P(0): ${state.probabilityZero().toFixed(6)}`
    );
    console.log(
        `  P(1): ${state.probabilityOne().toFixed(6)}`
    );
    console.log();
}


function printMatrix(name, matrix) {
    console.log(`${name} =`);

    for (const row of matrix) {
        console.log(
            "  " +
            row
                .map(value =>
                    value.toString().padStart(15)
                )
                .join("  ")
        );
    }

    console.log();
}


function section(title) {
    console.log("=".repeat(72));
    console.log(title);
    console.log("=".repeat(72));
}


// -----------------------------------------------------------------------------
// Demonstrations
// -----------------------------------------------------------------------------

function demonstrateBasisStates() {
    section("1. BASIS STATES");

    printState("|0>:", ketZero());
    printState("|1>:", ketOne());
}


function demonstrateGateMatrices() {
    section("2. STANDARD GATE MATRICES");

    printMatrix("I", IDENTITY);
    printMatrix("X", X_GATE);
    printMatrix("Y", Y_GATE);
    printMatrix("Z", Z_GATE);
}


function demonstrateGateTransformations() {
    section("3. X, Y, Z, AND IDENTITY TRANSFORMATIONS");

    const states = {
        "|0>": ketZero(),
        "|1>": ketOne()
    };

    for (const gateName of ["I", "X", "Y", "Z"]) {
        console.log(`${gateName} gate:`);

        for (const [stateName, state] of Object.entries(states)) {
            const transformed = applyNamedGate(
                state,
                gateName
            );

            console.log(
                `  ${stateName} -> ${transformed}`
            );
        }

        console.log();
    }
}


function demonstrateSuperposition() {
    section("4. SUPERPOSITION");

    const plus = plusState();
    const minus = minusState();

    printState("|+>:", plus);
    printState("|->:", minus);

    console.log("X|+>:");
    console.log(applyNamedGate(plus, "X").toString());
    console.log();

    console.log("Z|+>:");
    console.log(applyNamedGate(plus, "Z").toString());
    console.log();
}


function demonstratePhase() {
    section("5. GLOBAL PHASE AND RELATIVE PHASE");

    const plus = plusState();

    const globalPhase = new Qubit(
        plus.alpha.scale(-1),
        plus.beta.scale(-1)
    );

    console.log("Original |+>:");
    console.log(plus.toString());
    console.log();

    console.log("Global phase -1 applied:");
    console.log(globalPhase.toString());
    console.log();

    console.log(
        "Original probabilities:",
        plus.probabilityZero(),
        plus.probabilityOne()
    );

    console.log(
        "Global-phase probabilities:",
        globalPhase.probabilityZero(),
        globalPhase.probabilityOne()
    );

    console.log();
}


function demonstrateComposition() {
    section("6. GATE COMPOSITION");

    const state = ketZero();

    const sequential = applyNamedGate(
        applyNamedGate(state, "X"),
        "Z"
    );

    const combinedGate = composeGates(
        X_GATE,
        Z_GATE
    );

    const combined = state.applyGate(combinedGate);

    console.log("X followed by Z:");
    console.log(`Sequential: ${sequential}`);
    console.log(`Combined:   ${combined}`);
    console.log();
}


function demonstrateNonCommutativity() {
    section("7. NON-COMMUTATIVITY");

    const firstOrder = applyNamedGate(
        applyNamedGate(plusState(), "X"),
        "Y"
    );

    const secondOrder = applyNamedGate(
        applyNamedGate(plusState(), "Y"),
        "X"
    );

    console.log("Y(X|+>):");
    console.log(firstOrder.toString());
    console.log();

    console.log("X(Y|+>):");
    console.log(secondOrder.toString());
    console.log();

    const yx = composeGates(X_GATE, Y_GATE);
    const xy = composeGates(Y_GATE, X_GATE);

    console.log(
        "Do XY and YX have the same matrix?",
        matricesAreClose(xy, yx)
    );

    console.log();
}


function demonstrateUnitarity() {
    section("8. UNITARITY AND INVERSES");

    for (const name of ["I", "X", "Y", "Z"]) {
        console.log(
            `${name} is unitary:`,
            isUnitary(GATES[name])
        );
    }

    console.log();

    for (const name of ["X", "Y", "Z"]) {
        const square = matrixMultiply(
            GATES[name],
            GATES[name]
        );

        console.log(
            `${name}² = I:`,
            matricesAreClose(square, IDENTITY)
        );
    }

    console.log();
}


function demonstrateBlochSphere() {
    section("9. BLOCH-SPHERE COORDINATES");

    const states = {
        "|0>": ketZero(),
        "|1>": ketOne(),
        "|+>": plusState(),
        "|->": minusState(),
        "|+i>": plusIState()
    };

    for (const [name, state] of Object.entries(states)) {
        const coordinates = blochCoordinates(state);

        console.log(
            `${name}: ` +
            `x=${coordinates.x.toFixed(4)}, ` +
            `y=${coordinates.y.toFixed(4)}, ` +
            `z=${coordinates.z.toFixed(4)}`
        );
    }

    console.log();
}


function demonstrateMeasurement() {
    section("10. MEASUREMENT SIMULATION");

    const state = plusState();

    const result = simulateMeasurements(
        state,
        10000,
        12345
    );

    console.log("State: |+>");
    console.log("Theoretical P(0):", state.probabilityZero());
    console.log("Theoretical P(1):", state.probabilityOne());
    console.log();
    console.log("Observed zeros:", result.zeros);
    console.log("Observed ones:", result.ones);
    console.log(
        "Observed P(0):",
        result.probabilityZero.toFixed(4)
    );
    console.log(
        "Observed P(1):",
        result.probabilityOne.toFixed(4)
    );

    console.log();
}


function demonstrateExpectationValues() {
    section("11. PAULI EXPECTATION VALUES");

    const states = {
        "|0>": ketZero(),
        "|1>": ketOne(),
        "|+>": plusState(),
        "|->": minusState(),
        "|+i>": plusIState()
    };

    for (const [name, state] of Object.entries(states)) {
        const x = expectationValue(state, X_GATE);
        const y = expectationValue(state, Y_GATE);
        const z = expectationValue(state, Z_GATE);

        console.log(
            `${name}: ` +
            `<X>=${x.real.toFixed(4)}, ` +
            `<Y>=${y.real.toFixed(4)}, ` +
            `<Z>=${z.real.toFixed(4)}`
        );
    }

    console.log();
}


function demonstrateTwoQubitSystems() {
    section("12. TWO-QUBIT TENSOR PRODUCTS");

    const zeroZero = tensorProduct(
        ketZero().vector,
        ketZero().vector
    );

    const plusPlus = tensorProduct(
        plusState().vector,
        plusState().vector
    );

    console.log("|00> amplitudes:");
    console.log(
        zeroZero.map(value => value.toString())
    );
    console.log();

    console.log("|++> amplitudes:");
    console.log(
        plusPlus.map(value => value.toString())
    );
    console.log();

    const identityTwoQubit = tensorMatrix(
        IDENTITY,
        IDENTITY
    );

    console.log(
        "I ⊗ I has dimensions:",
        identityTwoQubit.length,
        "x",
        identityTwoQubit[0].length
    );

    console.log();
}


function demonstrateBellState() {
    section("13. BELL STATE");

    const bellState = [
        new Complex(1 / SQRT_TWO),
        new Complex(0),
        new Complex(0),
        new Complex(1 / SQRT_TWO)
    ];

    const labels = [
        "|00>",
        "|01>",
        "|10>",
        "|11>"
    ];

    for (let i = 0; i < bellState.length; i++) {
        console.log(
            `${labels[i]}: ` +
            `amplitude=${bellState[i].toString()}, ` +
            `probability=${bellState[i].magnitudeSquared().toFixed(4)}`
        );
    }

    console.log();
}


function demonstrateValidation() {
    section("14. VALIDATION AND EDGE CASES");

    const tests = [
        {
            name: "Unnormalized state",
            action: () =>
                new Qubit(
                    new Complex(1),
                    new Complex(1)
                )
        },
        {
            name: "Unknown gate",
            action: () =>
                applyNamedGate(ketZero(), "H")
        },
        {
            name: "Invalid matrix",
            action: () =>
                matrixVectorMultiply(
                    [[new Complex(1)]],
                    [new Complex(1), new Complex(0)]
                )
        },
        {
            name: "Invalid measurement value",
            action: () =>
                ketZero().measure(2)
        }
    ];

    for (const test of tests) {
        try {
            test.action();
            console.log(
                `${test.name}: unexpectedly succeeded`
            );
        } catch (error) {
            console.log(
                `${test.name}: correctly rejected`
            );
            console.log(
                `  Reason: ${error.message}`
            );
        }
    }

    console.log();
}


// -----------------------------------------------------------------------------
// Automated tests
// -----------------------------------------------------------------------------

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}


function assertStateClose(actual, expected) {
    assert(
        actual.alpha.equals(expected.alpha),
        `alpha differs: ${actual.alpha} vs ${expected.alpha}`
    );

    assert(
        actual.beta.equals(expected.beta),
        `beta differs: ${actual.beta} vs ${expected.beta}`
    );
}


function runTests() {
    section("15. AUTOMATED TESTS");

    assertStateClose(
        applyNamedGate(ketZero(), "I"),
        ketZero()
    );

    assertStateClose(
        applyNamedGate(ketZero(), "X"),
        ketOne()
    );

    assertStateClose(
        applyNamedGate(ketOne(), "X"),
        ketZero()
    );

    assertStateClose(
        applyNamedGate(ketZero(), "Y"),
        new Qubit(
            new Complex(0),
            new Complex(0, 1)
        )
    );

    assertStateClose(
        applyNamedGate(ketOne(), "Y"),
        new Qubit(
            new Complex(0, -1),
            new Complex(0)
        )
    );

    assertStateClose(
        applyNamedGate(ketOne(), "Z"),
        new Qubit(
            new Complex(0),
            new Complex(-1)
        )
    );

    for (const name of ["I", "X", "Y", "Z"]) {
        assert(
            isUnitary(GATES[name]),
            `${name} must be unitary`
        );
    }

    for (const name of ["X", "Y", "Z"]) {
        const square = matrixMultiply(
            GATES[name],
            GATES[name]
        );

        assert(
            matricesAreClose(square, IDENTITY),
            `${name} squared must equal identity`
        );
    }

    const plus = plusState();

    assert(
        Math.abs(
            plus.probabilityZero() -
            0.5
        ) <= EPSILON,
        "|+> must have P(0)=0.5"
    );

    assert(
        Math.abs(
            plus.probabilityOne() -
            0.5
        ) <= EPSILON,
        "|+> must have P(1)=0.5"
    );

    const xExpectation = expectationValue(
        plus,
        X_GATE
    );

    assert(
        Math.abs(xExpectation.real - 1) <= EPSILON,
        "<+|X|+> must equal 1"
    );

    console.log("All JavaScript quantum-gate tests passed.");
    console.log();
}


// -----------------------------------------------------------------------------
// Performance experiment
// -----------------------------------------------------------------------------

function benchmark() {
    section("16. PERFORMANCE EXPERIMENT");

    const iterations = 100000;
    let state = plusState();

    const start = process.hrtime.bigint();

    for (let i = 0; i < iterations; i++) {
        state = state.applyGate(X_GATE);
    }

    const end = process.hrtime.bigint();

    const seconds =
        Number(end - start) / 1_000_000_000;

    console.log(
        `Operations: ${iterations.toLocaleString()}`
    );

    console.log(
        `Elapsed time: ${seconds.toFixed(6)} seconds`
    );

    console.log(
        `Operations/second: ` +
        `${Math.round(iterations / seconds).toLocaleString()}`
    );

    console.log();

    console.log(
        "A dense state-vector simulator requires memory that grows "
        + "exponentially as the number of qubits increases."
    );

    console.log();
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

function main() {
    console.log();
    console.log("#".repeat(72));
    console.log("QUANTUM GATES: X, Y, Z, AND IDENTITY");
    console.log("#".repeat(72));
    console.log();

    demonstrateBasisStates();
    demonstrateGateMatrices();
    demonstrateGateTransformations();
    demonstrateSuperposition();
    demonstratePhase();
    demonstrateComposition();
    demonstrateNonCommutativity();
    demonstrateUnitarity();
    demonstrateBlochSphere();
    demonstrateMeasurement();
    demonstrateExpectationValues();
    demonstrateTwoQubitSystems();
    demonstrateBellState();
    demonstrateValidation();
    runTests();
    benchmark();

    console.log("END OF JAVASCRIPT STUDY PROGRAM");
}


if (typeof require !== "undefined" && require.main === module) {
    main();
}
