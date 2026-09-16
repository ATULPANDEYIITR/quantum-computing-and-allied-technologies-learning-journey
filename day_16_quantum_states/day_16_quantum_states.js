/*
 * Quantum States: State Vectors and Notation
 * ===========================================
 *
 * A self-contained JavaScript study file covering:
 * - complex probability amplitudes
 * - ket and bra notation
 * - normalization
 * - measurement probabilities
 * - global and relative phase
 * - inner and outer products
 * - operators and expectation values
 * - tensor products
 * - two-qubit states
 * - product states and entanglement
 * - basis changes
 * - Bloch vectors
 * - measurement simulation
 * - validation and numerical precision
 *
 * No external packages are required.
 *
 * JavaScript has no built-in complex-number type, so a small Complex class
 * is implemented explicitly. This makes the mathematical operations visible.
 */


"use strict";


// ---------------------------------------------------------------------------
// Complex numbers
// ---------------------------------------------------------------------------

class Complex {
    constructor(real = 0, imaginary = 0) {
        this.real = Number(real);
        this.imaginary = Number(imaginary);
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

    scale(number) {
        return new Complex(
            this.real * number,
            this.imaginary * number
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

    phase() {
        return Math.atan2(this.imaginary, this.real);
    }

    equals(other, tolerance = 1e-10) {
        return (
            Math.abs(this.real - other.real) <= tolerance &&
            Math.abs(this.imaginary - other.imaginary) <= tolerance
        );
    }

    toString(digits = 5) {
        const real = Math.abs(this.real) < 1e-12 ? 0 : this.real;
        const imaginary =
            Math.abs(this.imaginary) < 1e-12 ? 0 : this.imaginary;

        if (Math.abs(imaginary) < 1e-12) {
            return real.toFixed(digits);
        }

        if (Math.abs(real) < 1e-12) {
            return `${imaginary.toFixed(digits)}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";

        return (
            `${real.toFixed(digits)}` +
            `${sign}${Math.abs(imaginary).toFixed(digits)}i`
        );
    }

    static fromPolar(magnitude, phase) {
        return new Complex(
            magnitude * Math.cos(phase),
            magnitude * Math.sin(phase)
        );
    }
}


const ZERO_COMPLEX = new Complex(0, 0);
const ONE_COMPLEX = new Complex(1, 0);
const IMAGINARY_UNIT = new Complex(0, 1);
const EPSILON = 1e-10;


// ---------------------------------------------------------------------------
// Vector operations
// ---------------------------------------------------------------------------

function vectorNormSquared(vector) {
    return vector.reduce(
        (sum, value) => sum + value.magnitudeSquared(),
        0
    );
}


function vectorNorm(vector) {
    return Math.sqrt(vectorNormSquared(vector));
}


function normalizeVector(vector) {
    const norm = vectorNorm(vector);

    if (norm < EPSILON) {
        throw new Error("The zero vector cannot represent a quantum state.");
    }

    return vector.map(value => value.scale(1 / norm));
}


function innerProduct(braVector, ketVector) {
    if (braVector.length !== ketVector.length) {
        throw new Error("Inner-product dimensions do not match.");
    }

    // <a|b> = sum conjugate(a_i) * b_i.
    return braVector.reduce(
        (sum, value, index) =>
            sum.add(value.conjugate().multiply(ketVector[index])),
        new Complex()
    );
}


function outerProduct(ket, bra) {
    return ket.map(
        ketValue =>
            bra.map(
                braValue => ketValue.multiply(braValue.conjugate())
            )
    );
}


function matrixVectorMultiply(matrix, vector) {
    if (matrix.length === 0) {
        throw new Error("Matrix cannot be empty.");
    }

    if (matrix.some(row => row.length !== vector.length)) {
        throw new Error("Matrix and vector dimensions do not match.");
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
    if (a.length === 0 || b.length === 0) {
        throw new Error("Matrices cannot be empty.");
    }

    const aColumns = a[0].length;
    const bColumns = b[0].length;

    if (a.some(row => row.length !== aColumns)) {
        throw new Error("Matrix A is not rectangular.");
    }

    if (b.some(row => row.length !== bColumns)) {
        throw new Error("Matrix B is not rectangular.");
    }

    if (aColumns !== b.length) {
        throw new Error("Matrix dimensions are incompatible.");
    }

    const result = [];

    for (let i = 0; i < a.length; i++) {
        const row = [];

        for (let j = 0; j < bColumns; j++) {
            let value = new Complex();

            for (let k = 0; k < aColumns; k++) {
                value = value.add(a[i][k].multiply(b[k][j]));
            }

            row.push(value);
        }

        result.push(row);
    }

    return result;
}


function adjoint(matrix) {
    const rows = matrix.length;
    const columns = matrix[0].length;

    return Array.from({ length: columns }, (_, column) =>
        Array.from(
            { length: rows },
            (_, row) => matrix[row][column].conjugate()
        )
    );
}


function isIdentity(matrix, tolerance = 1e-9) {
    if (matrix.length === 0 || matrix.length !== matrix[0].length) {
        return false;
    }

    for (let row = 0; row < matrix.length; row++) {
        for (let column = 0; column < matrix.length; column++) {
            const expected = row === column
                ? ONE_COMPLEX
                : ZERO_COMPLEX;

            if (!matrix[row][column].equals(expected, tolerance)) {
                return false;
            }
        }
    }

    return true;
}


function isUnitary(matrix, tolerance = 1e-9) {
    return isIdentity(
        matrixMultiply(adjoint(matrix), matrix),
        tolerance
    );
}


// ---------------------------------------------------------------------------
// Quantum state class
// ---------------------------------------------------------------------------

class QuantumState {
    constructor(amplitudes) {
        if (!Array.isArray(amplitudes) || amplitudes.length === 0) {
            throw new Error("A quantum state requires amplitudes.");
        }

        if (!amplitudes.every(value => value instanceof Complex)) {
            throw new TypeError(
                "Every amplitude must be represented by Complex."
            );
        }

        const dimension = amplitudes.length;

        // A qubit register has dimension 2^n.
        if ((dimension & (dimension - 1)) !== 0) {
            throw new Error(
                "State dimension must be a power of two."
            );
        }

        this.amplitudes = normalizeVector(amplitudes);
    }

    get dimension() {
        return this.amplitudes.length;
    }

    get qubitCount() {
        return Math.log2(this.dimension);
    }

    probability(index) {
        if (index < 0 || index >= this.dimension) {
            throw new RangeError("Basis index is outside the state.");
        }

        return this.amplitudes[index].magnitudeSquared();
    }

    probabilities() {
        return this.amplitudes.map(value => value.magnitudeSquared());
    }

    apply(operator) {
        if (
            operator.length !== this.dimension ||
            operator.some(row => row.length !== this.dimension)
        ) {
            throw new Error(
                "Operator dimension does not match state dimension."
            );
        }

        return new QuantumState(
            matrixVectorMultiply(operator, this.amplitudes)
        );
    }

    ket() {
        const terms = [];

        for (let index = 0; index < this.dimension; index++) {
            if (this.amplitudes[index].magnitude() > EPSILON) {
                const label = index
                    .toString(2)
                    .padStart(this.qubitCount, "0");

                terms.push(
                    `(${this.amplitudes[index].toString()})|${label}>`
                );
            }
        }

        return terms.length > 0 ? terms.join(" + ") : "0";
    }
}


// ---------------------------------------------------------------------------
// Basis states and standard operators
// ---------------------------------------------------------------------------

const ZERO = new QuantumState([
    new Complex(1, 0),
    new Complex(0, 0)
]);

const ONE = new QuantumState([
    new Complex(0, 0),
    new Complex(1, 0)
]);

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

const IDENTITY = [
    [new Complex(1), new Complex(0)],
    [new Complex(0), new Complex(1)]
];


// ---------------------------------------------------------------------------
// Basic examples
// ---------------------------------------------------------------------------

console.log("=".repeat(78));
console.log("QUANTUM STATES: STATE VECTORS AND NOTATION");
console.log("=".repeat(78));

console.log("\n1. Computational basis");
console.log("|0> =", ZERO.ket());
console.log("|1> =", ONE.ket());

const plus = new QuantumState([
    new Complex(1),
    new Complex(1)
]);

const minus = new QuantumState([
    new Complex(1),
    new Complex(-1)
]);

console.log("\n2. Superposition");
console.log("|+> =", plus.ket());
console.log("|-> =", minus.ket());
console.log("P(0 | +) =", plus.probability(0));
console.log("P(1 | +) =", plus.probability(1));


// ---------------------------------------------------------------------------
// Complex amplitudes and phase
// ---------------------------------------------------------------------------

const complexState = new QuantumState([
    new Complex(1),
    new Complex(0, 1)
]);

console.log("\n3. Complex amplitudes");
console.log(
    "(|0> + i|1>)/sqrt(2) =",
    complexState.ket()
);
console.log("Probabilities =", complexState.probabilities());


// ---------------------------------------------------------------------------
// Global phase
// ---------------------------------------------------------------------------

const globalPhaseState = new QuantumState([
    new Complex(0, 1),
    new Complex(0, 1)
]);

console.log("\n4. Global phase");
console.log("Original |+>:", plus.ket());
console.log("i|+>:", globalPhaseState.ket());
console.log(
    "Probabilities are equal:",
    JSON.stringify(plus.probabilities()) ===
    JSON.stringify(globalPhaseState.probabilities())
);


// ---------------------------------------------------------------------------
// Inner products and orthogonality
// ---------------------------------------------------------------------------

const plusMinusOverlap = innerProduct(
    plus.amplitudes,
    minus.amplitudes
);

console.log("\n5. Inner product");
console.log("<+|-> =", plusMinusOverlap.toString());
console.log(
    "Orthogonal:",
    plusMinusOverlap.magnitude() < EPSILON
);


// ---------------------------------------------------------------------------
// Operators
// ---------------------------------------------------------------------------

console.log("\n6. Operators");
console.log("X|0> =", ZERO.apply(X).ket());
console.log("X|1> =", ONE.apply(X).ket());
console.log("H|0> =", ZERO.apply(H).ket());
console.log("H|1> =", ONE.apply(H).ket());
console.log("Z|+> =", plus.apply(Z).ket());


// ---------------------------------------------------------------------------
// Expectation values
// ---------------------------------------------------------------------------

function expectationValue(state, observable) {
    const transformed = matrixVectorMultiply(
        observable,
        state.amplitudes
    );

    return innerProduct(
        state.amplitudes,
        transformed
    );
}


console.log("\n7. Expectation values");
console.log("<+|X|+> =", expectationValue(plus, X).toString());
console.log("<+|Y|+> =", expectationValue(plus, Y).toString());
console.log("<+|Z|+> =", expectationValue(plus, Z).toString());


// ---------------------------------------------------------------------------
// Bloch vector
// ---------------------------------------------------------------------------

function blochCoordinates(state) {
    if (state.dimension !== 2) {
        throw new Error(
            "Bloch coordinates require a single-qubit state."
        );
    }

    const alpha = state.amplitudes[0];
    const beta = state.amplitudes[1];

    const alphaConjugateBeta =
        alpha.conjugate().multiply(beta);

    return {
        x: 2 * alphaConjugateBeta.real,
        y: 2 * alphaConjugateBeta.imaginary,
        z:
            alpha.magnitudeSquared() -
            beta.magnitudeSquared()
    };
}


console.log("\n8. Bloch vector");
console.log("Bloch vector for |0>:", blochCoordinates(ZERO));
console.log("Bloch vector for |+>:", blochCoordinates(plus));
console.log(
    "Bloch vector for (|0> + i|1>)/sqrt(2):",
    blochCoordinates(complexState)
);


// ---------------------------------------------------------------------------
// Tensor products
// ---------------------------------------------------------------------------

function tensorProductVector(a, b) {
    const result = [];

    for (const left of a) {
        for (const right of b) {
            result.push(left.multiply(right));
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


const plusPlus = new QuantumState(
    tensorProductVector(
        plus.amplitudes,
        plus.amplitudes
    )
);

console.log("\n9. Tensor product");
console.log("|++> =", plusPlus.ket());
console.log("Dimension =", plusPlus.dimension);
console.log("Qubits =", plusPlus.qubitCount);


// ---------------------------------------------------------------------------
// Bell state and entanglement
// ---------------------------------------------------------------------------

const bellPhiPlus = new QuantumState([
    new Complex(1 / Math.sqrt(2)),
    new Complex(0),
    new Complex(0),
    new Complex(1 / Math.sqrt(2))
]);


function isProductTwoQubitState(state, tolerance = 1e-9) {
    if (state.dimension !== 4) {
        throw new Error(
            "The separability test expects two qubits."
        );
    }

    const [a00, a01, a10, a11] = state.amplitudes;

    // A 2x2 coefficient matrix has rank one when
    // a00*a11 - a01*a10 = 0.
    const determinant = a00
        .multiply(a11)
        .subtract(a01.multiply(a10));

    return determinant.magnitude() <= tolerance;
}


console.log("\n10. Product versus entangled states");
console.log("|++> is product:", isProductTwoQubitState(plusPlus));
console.log(
    "|Phi+> is product:",
    isProductTwoQubitState(bellPhiPlus)
);
console.log("|Phi+> =", bellPhiPlus.ket());


// ---------------------------------------------------------------------------
// Measurement simulation
// ---------------------------------------------------------------------------

function sampleMeasurement(state, trials = 1000, seed = null) {
    if (!Number.isInteger(trials) || trials <= 0) {
        throw new Error("Trials must be a positive integer.");
    }

    /*
     * Math.random() cannot be seeded directly in standard JavaScript.
     * For reproducibility, a tiny deterministic pseudo-random generator
     * is used when a numeric seed is supplied.
     */
    let random = Math.random;

    if (seed !== null) {
        let internalState = seed >>> 0;

        random = function () {
            internalState = (
                (1664525 * internalState + 1013904223) >>> 0
            );

            return internalState / 4294967296;
        };
    }

    const probabilities = state.probabilities();
    const counts = Array(state.dimension).fill(0);

    for (let trial = 0; trial < trials; trial++) {
        const target = random();
        let cumulative = 0;

        for (let index = 0; index < probabilities.length; index++) {
            cumulative += probabilities[index];

            if (target < cumulative) {
                counts[index]++;
                break;
            }
        }
    }

    return counts;
}


console.log("\n11. Measurement simulation");

const measurementCounts = sampleMeasurement(
    plus,
    10000,
    42
);

console.log("Theoretical probabilities:", plus.probabilities());
console.log("Observed counts:", measurementCounts);
console.log(
    "Observed frequencies:",
    measurementCounts.map(
        count => Number((count / 10000).toFixed(4))
    )
);


// ---------------------------------------------------------------------------
// Basis transformation
// ---------------------------------------------------------------------------

function changeBasis(state, basisMatrix) {
    if (basisMatrix.length !== state.dimension) {
        throw new Error("Basis dimension does not match state.");
    }

    return matrixVectorMultiply(
        adjoint(basisMatrix),
        state.amplitudes
    );
}


console.log("\n12. Change of basis");

const zeroInXBasis = changeBasis(ZERO, H);

console.log(
    "Coordinates of |0> in X basis:",
    zeroInXBasis.map(value => value.toString())
);

console.log(
    "Probabilities in X basis:",
    zeroInXBasis.map(value => value.magnitudeSquared())
);


// ---------------------------------------------------------------------------
// Density matrix
// ---------------------------------------------------------------------------

function densityMatrix(state) {
    return outerProduct(
        state.amplitudes,
        state.amplitudes
    );
}


function trace(matrix) {
    return matrix.reduce(
        (sum, row, index) => sum.add(row[index]),
        new Complex()
    );
}


function matrixSquare(matrix) {
    return matrixMultiply(matrix, matrix);
}


function purity(density) {
    return trace(matrixSquare(density)).real;
}


console.log("\n13. Density matrix");

const rhoPlus = densityMatrix(plus);

console.log(
    "Trace(rho) =",
    trace(rhoPlus).toString()
);

console.log(
    "Purity =",
    purity(rhoPlus)
);


// ---------------------------------------------------------------------------
// Pure-state fidelity
// ---------------------------------------------------------------------------

function pureStateFidelity(first, second) {
    if (first.dimension !== second.dimension) {
        throw new Error("States must have equal dimension.");
    }

    return innerProduct(
        first.amplitudes,
        second.amplitudes
    ).magnitudeSquared();
}


console.log("\n14. Pure-state fidelity");
console.log("F(|+>, |+>) =", pureStateFidelity(plus, plus));
console.log("F(|+>, |->) =", pureStateFidelity(plus, minus));
console.log("F(|+>, |0>) =", pureStateFidelity(plus, ZERO));


// ---------------------------------------------------------------------------
// Partial measurement probabilities
// ---------------------------------------------------------------------------

function firstQubitMarginal(state, value) {
    if (state.dimension !== 4) {
        throw new Error("This example expects two qubits.");
    }

    if (value !== 0 && value !== 1) {
        throw new Error("Qubit value must be 0 or 1.");
    }

    const indices = value === 0
        ? [0, 1]
        : [2, 3];

    return indices.reduce(
        (sum, index) => sum + state.probability(index),
        0
    );
}


console.log("\n15. Partial measurement");
console.log(
    "P(first qubit = 0) for |Phi+>:",
    firstQubitMarginal(bellPhiPlus, 0)
);
console.log(
    "P(first qubit = 1) for |Phi+>:",
    firstQubitMarginal(bellPhiPlus, 1)
);


// ---------------------------------------------------------------------------
// Operator sequences
// ---------------------------------------------------------------------------

function applyOperatorSequence(state, operators) {
    return operators.reduce(
        (currentState, operator) =>
            currentState.apply(operator),
        state
    );
}


const hThenZ = applyOperatorSequence(
    ZERO,
    [H, Z]
);

console.log("\n16. Sequential evolution");
console.log("Start: |0>");
console.log("H followed by Z:", hThenZ.ket());


// ---------------------------------------------------------------------------
// Unitarity
// ---------------------------------------------------------------------------

console.log("\n17. Unitary operators");

for (const [name, operator] of [
    ["I", IDENTITY],
    ["X", X],
    ["Y", Y],
    ["Z", Z],
    ["H", H]
]) {
    console.log(`${name} is unitary:`, isUnitary(operator));
}


// ---------------------------------------------------------------------------
// Numerical validation
// ---------------------------------------------------------------------------

function assertApproximatelyEqual(
    actual,
    expected,
    tolerance = 1e-9,
    message = "Values differ."
) {
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(
            `${message} Actual=${actual}, Expected=${expected}`
        );
    }
}


function runSelfTests() {
    assertApproximatelyEqual(
        vectorNormSquared(ZERO.amplitudes),
        1,
        1e-10,
        "|0> is not normalized."
    );

    assertApproximatelyEqual(
        innerProduct(
            ZERO.amplitudes,
            ONE.amplitudes
        ).magnitude(),
        0,
        1e-10,
        "|0> and |1> are not orthogonal."
    );

    assertApproximatelyEqual(
        pureStateFidelity(plus, plus),
        1,
        1e-10,
        "State fidelity with itself is not one."
    );

    assertApproximatelyEqual(
        pureStateFidelity(plus, minus),
        0,
        1e-10,
        "|+> and |-> should be orthogonal."
    );

    assertApproximatelyEqual(
        expectationValue(plus, X).real,
        1,
        1e-10,
        "Incorrect X expectation value."
    );

    assertApproximatelyEqual(
        expectationValue(plus, Z).real,
        0,
        1e-10,
        "Incorrect Z expectation value."
    );

    if (!isUnitary(H)) {
        throw new Error("Hadamard matrix should be unitary.");
    }

    if (isProductTwoQubitState(bellPhiPlus)) {
        throw new Error("Bell state should not be a product state.");
    }

    assertApproximatelyEqual(
        trace(rhoPlus).real,
        1,
        1e-10,
        "Density matrix trace should equal one."
    );

    assertApproximatelyEqual(
        purity(rhoPlus),
        1,
        1e-10,
        "Pure-state density matrix should have purity one."
    );

    console.log("\nSelf-tests: PASS");
}


runSelfTests();

console.log("\n" + "=".repeat(78));
console.log("END OF QUANTUM STATE VECTOR STUDY");
console.log("=".repeat(78));
