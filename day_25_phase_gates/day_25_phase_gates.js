/*
 * Phase Gates: S, T, and Phase Operations
 * ========================================
 *
 * A self-contained JavaScript study file covering:
 * - Complex amplitudes
 * - Quantum state vectors
 * - Global and relative phase
 * - General P(theta) phase gates
 * - Z, S, and T gates
 * - Adjoint gates
 * - Gate powers
 * - Interference
 * - Controlled phase gates
 * - Tensor products
 * - Phase kickback
 * - QFT-style rotations
 * - Circuit composition
 * - Measurement simulation
 * - Validation
 * - Numerical precision
 * - Performance considerations
 *
 * The file uses only standard JavaScript and can run in Node.js.
 */


// ============================================================================
// 1. COMPLEX NUMBERS
// ============================================================================

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

    magnitudeSquared() {
        return (
            this.real * this.real +
            this.imaginary * this.imaginary
        );
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    phase() {
        return Math.atan2(this.imaginary, this.real);
    }

    toString(precision = 4) {
        const real = Math.abs(this.real) < 1e-12 ? 0 : this.real;
        const imaginary =
            Math.abs(this.imaginary) < 1e-12 ? 0 : this.imaginary;

        if (imaginary === 0) {
            return real.toFixed(precision);
        }

        if (real === 0) {
            return `${imaginary.toFixed(precision)}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";

        return (
            `${real.toFixed(precision)} ${sign} ` +
            `${Math.abs(imaginary).toFixed(precision)}i`
        );
    }

    static fromPolar(magnitude, angle) {
        return new Complex(
            magnitude * Math.cos(angle),
            magnitude * Math.sin(angle)
        );
    }
}


const ZERO = new Complex(0, 0);
const ONE = new Complex(1, 0);
const I = new Complex(0, 1);

const EPSILON = 1e-10;


// ============================================================================
// 2. COMPLEX AND VECTOR UTILITIES
// ============================================================================

function complex(value) {
    if (value instanceof Complex) {
        return value;
    }

    return new Complex(value, 0);
}


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

    if (norm < EPSILON) {
        throw new Error("Cannot normalize a zero vector.");
    }

    return state.map(
        amplitude => new Complex(
            amplitude.real / norm,
            amplitude.imaginary / norm
        )
    );
}


function validateState(state) {
    if (!Array.isArray(state) || state.length === 0) {
        throw new Error("A quantum state must be a non-empty array.");
    }

    const norm = vectorNorm(state);

    if (Math.abs(norm - 1) > 1e-9) {
        throw new Error(
            `State is not normalized. Norm = ${norm}`
        );
    }
}


function probabilities(state) {
    return state.map(amplitude => amplitude.magnitudeSquared());
}


function formatAngle(theta) {
    return (
        `${theta.toFixed(6)} rad ` +
        `(${(theta * 180 / Math.PI).toFixed(2)}°)`
    );
}


// ============================================================================
// 3. MATRIX OPERATIONS
// ============================================================================

function identityMatrix(size) {
    return Array.from(
        { length: size },
        (_, row) =>
            Array.from(
                { length: size },
                (_, column) =>
                    row === column ? new Complex(1, 0) : new Complex(0, 0)
            )
    );
}


function matrixMultiply(a, b) {
    if (
        !Array.isArray(a) ||
        !Array.isArray(b) ||
        a.length === 0 ||
        b.length === 0
    ) {
        throw new Error("Matrices cannot be empty.");
    }

    if (a[0].length !== b.length) {
        throw new Error("Matrix dimensions are incompatible.");
    }

    return a.map((row, rowIndex) =>
        b[0].map((_, columnIndex) => {
            let total = new Complex(0, 0);

            for (let k = 0; k < b.length; k++) {
                total = total.add(
                    row[k].multiply(b[k][columnIndex])
                );
            }

            return total;
        })
    );
}


function matrixVectorMultiply(matrix, vector) {
    if (matrix[0].length !== vector.length) {
        throw new Error("Matrix and vector dimensions are incompatible.");
    }

    return matrix.map(row => {
        let total = new Complex(0, 0);

        for (let column = 0; column < vector.length; column++) {
            total = total.add(
                row[column].multiply(vector[column])
            );
        }

        return total;
    });
}


function conjugateTranspose(matrix) {
    return matrix[0].map((_, column) =>
        matrix.map(
            (_, row) => matrix[row][column].conjugate()
        )
    );
}


function matricesClose(a, b, tolerance = 1e-9) {
    if (
        a.length !== b.length ||
        a[0].length !== b[0].length
    ) {
        return false;
    }

    for (let row = 0; row < a.length; row++) {
        for (let column = 0; column < a[0].length; column++) {
            const difference = a[row][column].subtract(
                b[row][column]
            );

            if (difference.magnitude() > tolerance) {
                return false;
            }
        }
    }

    return true;
}


function isUnitary(matrix) {
    if (
        matrix.length === 0 ||
        matrix.length !== matrix[0].length
    ) {
        return false;
    }

    const adjoint = conjugateTranspose(matrix);
    const product = matrixMultiply(adjoint, matrix);

    return matricesClose(
        product,
        identityMatrix(matrix.length)
    );
}


// ============================================================================
// 4. BASIC QUANTUM GATES
// ============================================================================

const INV_SQRT_2 = 1 / Math.sqrt(2);

const X_GATE = [
    [ZERO, ONE],
    [ONE, ZERO]
];

const Y_GATE = [
    [ZERO, new Complex(0, -1)],
    [I, ZERO]
];

const Z_GATE = [
    [ONE, ZERO],
    [ZERO, new Complex(-1, 0)]
];

const H_GATE = [
    [new Complex(INV_SQRT_2, 0), new Complex(INV_SQRT_2, 0)],
    [new Complex(INV_SQRT_2, 0), new Complex(-INV_SQRT_2, 0)]
];


function phaseGate(theta) {
    return [
        [ONE, ZERO],
        [ZERO, Complex.fromPolar(1, theta)]
    ];
}


function sGate() {
    return phaseGate(Math.PI / 2);
}


function tGate() {
    return phaseGate(Math.PI / 4);
}


function sDaggerGate() {
    return phaseGate(-Math.PI / 2);
}


function tDaggerGate() {
    return phaseGate(-Math.PI / 4);
}


// ============================================================================
// 5. STATE AND MATRIX DISPLAY
// ============================================================================

function applyGate(state, gate) {
    validateState(state);

    if (!isUnitary(gate)) {
        throw new Error("Gate is not unitary.");
    }

    return matrixVectorMultiply(gate, state);
}


function printMatrix(matrix, title) {
    console.log(`\n${title}`);

    for (const row of matrix) {
        console.log(
            "[ " +
            row.map(value => value.toString()).join(", ") +
            " ]"
        );
    }
}


function showState(label, state, basisLabels = null) {
    validateState(state);

    console.log(`\n${label}`);

    const labels = basisLabels ||
        state.map((_, index) => `|${index}>`);

    state.forEach((amplitude, index) => {
        console.log(
            `${labels[index].padStart(6)}: ` +
            `amplitude=${amplitude.toString()}, ` +
            `probability=${amplitude.magnitudeSquared().toFixed(6)}`
        );
    });
}


// ============================================================================
// 6. GLOBAL-PHASE EQUIVALENCE
// ============================================================================

function globalPhaseEquivalent(stateA, stateB, tolerance = 1e-9) {
    if (stateA.length !== stateB.length) {
        return false;
    }

    let ratio = null;

    for (let index = 0; index < stateA.length; index++) {
        const a = stateA[index];
        const b = stateB[index];

        if (a.magnitude() > tolerance) {
            if (b.magnitude() <= tolerance) {
                return false;
            }

            ratio = b.multiply(a.conjugate());

            const magnitude = ratio.magnitude();

            if (Math.abs(magnitude - a.magnitudeSquared()) > tolerance) {
                return false;
            }

            ratio = new Complex(
                ratio.real / a.magnitudeSquared(),
                ratio.imaginary / a.magnitudeSquared()
            );

            break;
        }
    }

    if (ratio === null) {
        return true;
    }

    if (Math.abs(ratio.magnitude() - 1) > tolerance) {
        return false;
    }

    for (let index = 0; index < stateA.length; index++) {
        const expected = stateA[index].multiply(ratio);

        if (
            expected.subtract(stateB[index]).magnitude() >
            tolerance
        ) {
            return false;
        }
    }

    return true;
}


// ============================================================================
// 7. INTEGER MATRIX POWERS
// ============================================================================

function matrixPower(matrix, exponent) {
    if (exponent < 0) {
        return matrixPower(
            conjugateTranspose(matrix),
            -exponent
        );
    }

    let result = identityMatrix(matrix.length);
    let base = matrix;

    while (exponent > 0) {
        if (exponent % 2 === 1) {
            result = matrixMultiply(result, base);
        }

        base = matrixMultiply(base, base);
        exponent = Math.floor(exponent / 2);
    }

    return result;
}


// ============================================================================
// 8. CONTROLLED PHASE
// ============================================================================

function controlledPhaseGate(theta) {
    return [
        [ONE, ZERO, ZERO, ZERO],
        [ZERO, ONE, ZERO, ZERO],
        [ZERO, ZERO, ONE, ZERO],
        [ZERO, ZERO, ZERO, Complex.fromPolar(1, theta)]
    ];
}


// ============================================================================
// 9. TENSOR PRODUCTS
// ============================================================================

function tensorProductVector(a, b) {
    const result = [];

    for (const valueA of a) {
        for (const valueB of b) {
            result.push(valueA.multiply(valueB));
        }
    }

    return result;
}


function tensorProductMatrix(a, b) {
    const result = [];

    for (const rowA of a) {
        for (const rowB of b) {
            const row = [];

            for (const valueA of rowA) {
                for (const valueB of rowB) {
                    row.push(valueA.multiply(valueB));
                }
            }

            result.push(row);
        }
    }

    return result;
}


// ============================================================================
// 10. MEASUREMENT SAMPLING
// ============================================================================

function sampleMeasurements(state, shots = 1000, seed = 12345) {
    validateState(state);

    if (shots <= 0) {
        throw new Error("shots must be positive.");
    }

    // A deterministic linear-congruential generator makes demonstrations
    // reproducible without external packages.
    let randomState = seed >>> 0;

    function random() {
        randomState = (
            (1664525 * randomState + 1013904223) >>> 0
        );

        return randomState / 4294967296;
    }

    const distribution = probabilities(state);
    const cumulative = [];

    let total = 0;

    for (const probability of distribution) {
        total += probability;
        cumulative.push(total);
    }

    const counts = Array.from(
        { length: state.length },
        () => 0
    );

    for (let shot = 0; shot < shots; shot++) {
        const randomValue = random();

        for (let index = 0; index < cumulative.length; index++) {
            if (randomValue < cumulative[index]) {
                counts[index]++;
                break;
            }
        }
    }

    return counts;
}


// ============================================================================
// 11. INTERFERENCE EXPERIMENT
// ============================================================================

function interferenceExperiment(theta) {
    let state = applyGate(
        [ONE, ZERO],
        H_GATE
    );

    state = applyGate(
        state,
        phaseGate(theta)
    );

    state = applyGate(
        state,
        H_GATE
    );

    return probabilities(state);
}


// ============================================================================
// 12. PARAMETERIZED CIRCUIT
// ============================================================================

class SingleQubitCircuit {
    constructor() {
        this.operations = [];
    }

    addGate(name, matrix) {
        if (
            matrix.length !== 2 ||
            matrix[0].length !== 2
        ) {
            throw new Error(
                "SingleQubitCircuit requires 2x2 matrices."
            );
        }

        if (!isUnitary(matrix)) {
            throw new Error(`${name} is not unitary.`);
        }

        this.operations.push({
            name,
            matrix
        });
    }

    addPhase(theta) {
        this.addGate(
            `P(${(theta * 180 / Math.PI).toFixed(2)}°)`,
            phaseGate(theta)
        );
    }

    run(initialState) {
        let state = [...initialState];

        validateState(state);

        for (const operation of this.operations) {
            state = applyGate(
                state,
                operation.matrix
            );
        }

        return state;
    }

    combinedMatrix() {
        let result = identityMatrix(2);

        for (const operation of this.operations) {
            result = matrixMultiply(
                operation.matrix,
                result
            );
        }

        return result;
    }

    describe() {
        console.log("\nCircuit:");

        this.operations.forEach(
            (operation, index) => {
                console.log(
                    `${index + 1}. ${operation.name}`
                );
            }
        );
    }
}


// ============================================================================
// 13. DEMONSTRATIONS
// ============================================================================

function demonstrateBasicPhaseGates() {
    console.log("\n" + "=".repeat(80));
    console.log("BASIC PHASE GATES");
    console.log("=".repeat(80));

    const gates = {
        Z: Z_GATE,
        S: sGate(),
        T: tGate(),
        "S†": sDaggerGate(),
        "T†": tDaggerGate()
    };

    for (const [name, gate] of Object.entries(gates)) {
        printMatrix(gate, name);
        console.log(`Unitary: ${isUnitary(gate)}`);
    }

    console.log("\nRelationships:");
    console.log("Z = P(pi)");
    console.log("S = P(pi/2)");
    console.log("T = P(pi/4)");
    console.log("S^2 = Z");
    console.log("T^2 = S");
    console.log("T^4 = Z");
    console.log("T^8 = I");
}


function demonstrateBasisStateAction() {
    console.log("\n" + "=".repeat(80));
    console.log("BASIS-STATE ACTION");
    console.log("=".repeat(80));

    const zero = [ONE, ZERO];
    const one = [ZERO, ONE];

    for (const [name, gate] of [
        ["Z", Z_GATE],
        ["S", sGate()],
        ["T", tGate()]
    ]) {
        showState(`${name}|0>`, applyGate(zero, gate));
        showState(`${name}|1>`, applyGate(one, gate));
    }
}


function demonstrateGlobalAndRelativePhase() {
    console.log("\n" + "=".repeat(80));
    console.log("GLOBAL AND RELATIVE PHASE");
    console.log("=".repeat(80));

    const plus = [
        new Complex(INV_SQRT_2, 0),
        new Complex(INV_SQRT_2, 0)
    ];

    const globalPhase = plus.map(
        amplitude => I.multiply(amplitude)
    );

    const relativePhase = [
        plus[0],
        new Complex(-INV_SQRT_2, 0)
    ];

    showState("|+>", plus);
    showState("i|+>", globalPhase);
    showState("|->", relativePhase);

    console.log(
        "Original and global-phase states equivalent:",
        globalPhaseEquivalent(plus, globalPhase)
    );

    console.log(
        "Original and relative-phase states equivalent:",
        globalPhaseEquivalent(plus, relativePhase)
    );
}


function demonstrateInterference() {
    console.log("\n" + "=".repeat(80));
    console.log("INTERFERENCE");
    console.log("=".repeat(80));

    const plus = applyGate([ONE, ZERO], H_GATE);
    const minus = applyGate(plus, Z_GATE);

    showState("|+>", plus);
    showState("|-> = Z|+>", minus);

    showState(
        "H|+>",
        applyGate(plus, H_GATE)
    );

    showState(
        "H|->",
        applyGate(minus, H_GATE)
    );
}


function demonstrateGatePowers() {
    console.log("\n" + "=".repeat(80));
    console.log("GATE POWERS");
    console.log("=".repeat(80));

    const sSquared = matrixPower(sGate(), 2);
    const tSquared = matrixPower(tGate(), 2);
    const tFourth = matrixPower(tGate(), 4);
    const tEighth = matrixPower(tGate(), 8);

    printMatrix(sSquared, "S^2");
    printMatrix(tSquared, "T^2");
    printMatrix(tFourth, "T^4");
    printMatrix(tEighth, "T^8");

    console.log(
        "S^2 = Z:",
        matricesClose(sSquared, Z_GATE)
    );

    console.log(
        "T^2 = S:",
        matricesClose(tSquared, sGate())
    );

    console.log(
        "T^4 = Z:",
        matricesClose(tFourth, Z_GATE)
    );

    console.log(
        "T^8 = I:",
        matricesClose(
            tEighth,
            identityMatrix(2)
        )
    );
}


function demonstrateControlledPhase() {
    console.log("\n" + "=".repeat(80));
    console.log("CONTROLLED PHASE");
    console.log("=".repeat(80));

    const basis = [
        ["|00>", [ONE, ZERO, ZERO, ZERO]],
        ["|01>", [ZERO, ONE, ZERO, ZERO]],
        ["|10>", [ZERO, ZERO, ONE, ZERO]],
        ["|11>", [ZERO, ZERO, ZERO, ONE]]
    ];

    const controlledT = controlledPhaseGate(
        Math.PI / 4
    );

    for (const [label, state] of basis) {
        showState(
            `Controlled-T ${label}`,
            applyGate(
                state,
                controlledT
            ),
            ["|00>", "|01>", "|10>", "|11>"]
        );
    }
}


function demonstrateTensorProducts() {
    console.log("\n" + "=".repeat(80));
    console.log("TENSOR PRODUCTS");
    console.log("=".repeat(80));

    const zero = [ONE, ZERO];
    const one = [ZERO, ONE];

    const state01 = tensorProductVector(zero, one);

    showState(
        "|01>",
        state01,
        ["|00>", "|01>", "|10>", "|11>"]
    );

    const localT = tensorProductMatrix(
        identityMatrix(2),
        tGate()
    );

    const transformed = matrixVectorMultiply(
        localT,
        state01
    );

    showState(
        "(I ⊗ T)|01>",
        transformed,
        ["|00>", "|01>", "|10>", "|11>"]
    );
}


function demonstratePhaseKickback() {
    console.log("\n" + "=".repeat(80));
    console.log("PHASE KICKBACK");
    console.log("=".repeat(80));

    const controlSuperposition = [
        new Complex(INV_SQRT_2, 0),
        ZERO,
        new Complex(INV_SQRT_2, 0),
        ZERO
    ];

    const cz = controlledPhaseGate(Math.PI);

    const result = applyGate(
        controlSuperposition,
        cz
    );

    showState(
        "CZ applied to control superposition",
        result,
        ["|00>", "|01>", "|10>", "|11>"]
    );
}


function demonstrateQFTPhases() {
    console.log("\n" + "=".repeat(80));
    console.log("QFT-STYLE PHASE ROTATIONS");
    console.log("=".repeat(80));

    for (let distance = 1; distance <= 4; distance++) {
        const theta =
            Math.PI / (2 ** (distance - 1));

        console.log(
            `R${distance}: ${formatAngle(theta)}, ` +
            `phase=${Complex.fromPolar(1, theta).toString()}`
        );
    }
}


function demonstrateCircuit() {
    console.log("\n" + "=".repeat(80));
    console.log("PARAMETERIZED CIRCUIT");
    console.log("=".repeat(80));

    const circuit = new SingleQubitCircuit();

    circuit.addGate("H", H_GATE);
    circuit.addGate("T", tGate());
    circuit.addPhase(Math.PI / 3);
    circuit.addGate("S†", sDaggerGate());
    circuit.addGate("H", H_GATE);

    circuit.describe();

    const finalState = circuit.run([
        ONE,
        ZERO
    ]);

    showState(
        "Final state",
        finalState
    );

    printMatrix(
        circuit.combinedMatrix(),
        "Combined circuit matrix"
    );

    console.log(
        "Combined matrix unitary:",
        isUnitary(circuit.combinedMatrix())
    );
}


function demonstrateMeasurement() {
    console.log("\n" + "=".repeat(80));
    console.log("MEASUREMENT SIMULATION");
    console.log("=".repeat(80));

    let state = applyGate(
        [ONE, ZERO],
        H_GATE
    );

    state = applyGate(
        state,
        tGate()
    );

    showState(
        "State before measurement",
        state
    );

    const counts = sampleMeasurements(
        state,
        2000,
        42
    );

    console.log(
        "Counts after 2000 simulated measurements:",
        counts
    );
}


function demonstratePhaseToProbabilityConversion() {
    console.log("\n" + "=".repeat(80));
    console.log("PHASE TO PROBABILITY THROUGH INTERFERENCE");
    console.log("=".repeat(80));

    for (const degrees of [0, 45, 90, 135, 180, 270, 360]) {
        const theta = degrees * Math.PI / 180;
        const [pZero, pOne] =
            interferenceExperiment(theta);

        console.log(
            `${degrees.toString().padStart(3)}°: ` +
            `P(0)=${pZero.toFixed(4)}, ` +
            `P(1)=${pOne.toFixed(4)}`
        );
    }
}


// ============================================================================
// 14. VALIDATION
// ============================================================================

function demonstrateValidation() {
    console.log("\n" + "=".repeat(80));
    console.log("VALIDATION");
    console.log("=".repeat(80));

    try {
        validateState([
            ONE,
            ONE
        ]);
    } catch (error) {
        console.log(
            "Invalid state rejected:",
            error.message
        );
    }

    const nonUnitary = [
        [ONE, ZERO],
        [ZERO, new Complex(2, 0)]
    ];

    try {
        applyGate(
            [ONE, ZERO],
            nonUnitary
        );
    } catch (error) {
        console.log(
            "Non-unitary gate rejected:",
            error.message
        );
    }
}


// ============================================================================
// 15. SELF-TESTS
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}


function runSelfTests() {
    console.log("\n" + "=".repeat(80));
    console.log("SELF-TESTS");
    console.log("=".repeat(80));

    assert(isUnitary(H_GATE), "H must be unitary.");
    assert(isUnitary(X_GATE), "X must be unitary.");
    assert(isUnitary(Y_GATE), "Y must be unitary.");
    assert(isUnitary(Z_GATE), "Z must be unitary.");
    assert(isUnitary(sGate()), "S must be unitary.");
    assert(isUnitary(tGate()), "T must be unitary.");

    assert(
        matricesClose(
            matrixPower(sGate(), 2),
            Z_GATE
        ),
        "S^2 = Z"
    );

    assert(
        matricesClose(
            matrixPower(tGate(), 2),
            sGate()
        ),
        "T^2 = S"
    );

    assert(
        matricesClose(
            matrixPower(tGate(), 4),
            Z_GATE
        ),
        "T^4 = Z"
    );

    assert(
        matricesClose(
            matrixPower(tGate(), 8),
            identityMatrix(2)
        ),
        "T^8 = I"
    );

    assert(
        matricesClose(
            matrixMultiply(
                sGate(),
                sDaggerGate()
            ),
            identityMatrix(2)
        ),
        "S S† = I"
    );

    const [pZero, pOne] =
        interferenceExperiment(Math.PI);

    assert(
        Math.abs(pZero) < 1e-9 &&
        Math.abs(pOne - 1) < 1e-9,
        "Phase π should transform |+> into |-> and yield P(1)=1 after H."
    );

    assert(
        isUnitary(controlledPhaseGate(Math.PI / 4)),
        "Controlled-T must be unitary."
    );

    console.log("All JavaScript self-tests passed.");
}


// ============================================================================
// 16. PERFORMANCE NOTES
// ============================================================================

function performanceNotes() {
    console.log("\n" + "=".repeat(80));
    console.log("PERFORMANCE CONSIDERATIONS");
    console.log("=".repeat(80));

    console.log(
        "An n-qubit state vector contains 2^n complex amplitudes."
    );

    console.log(
        "A naive dense matrix representation requires a 2^n × 2^n matrix."
    );

    console.log(
        "Local-gate simulation is normally much more efficient than "
        + "constructing a dense full-system matrix."
    );

    for (let qubits = 1; qubits <= 10; qubits++) {
        console.log(
            `${qubits.toString().padStart(2)} qubits -> ` +
            `${2 ** qubits} amplitudes`
        );
    }
}


// ============================================================================
// 17. MAIN
// ============================================================================

function main() {
    console.log("=".repeat(80));
    console.log("PHASE GATES: S, T, AND PHASE OPERATIONS");
    console.log("=".repeat(80));

    demonstrateBasicPhaseGates();
    demonstrateBasisStateAction();
    demonstrateGlobalAndRelativePhase();
    demonstrateInterference();
    demonstrateGatePowers();
    demonstrateControlledPhase();
    demonstrateTensorProducts();
    demonstratePhaseKickback();
    demonstrateQFTPhases();
    demonstrateCircuit();
    demonstrateMeasurement();
    demonstratePhaseToProbabilityConversion();
    demonstrateValidation();
    performanceNotes();
    runSelfTests();

    console.log("\n" + "=".repeat(80));
    console.log("END OF JAVASCRIPT PHASE-GATE STUDY");
    console.log("=".repeat(80));
}


main();
