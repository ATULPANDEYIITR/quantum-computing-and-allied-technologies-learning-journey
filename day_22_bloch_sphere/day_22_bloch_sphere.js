/*
 * Bloch Sphere: Single-Qubit Geometry, Gates, Measurement and Visualization
 *
 * This self-contained JavaScript file demonstrates the Bloch sphere using
 * native JavaScript only. It can run under Node.js and contains an optional
 * SVG generator that can be opened in a browser.
 *
 * Topics:
 *   - qubit state vectors
 *   - complex numbers
 *   - Bloch coordinates
 *   - density matrices
 *   - Pauli matrices
 *   - quantum gates
 *   - rotations
 *   - measurement
 *   - global and relative phase
 *   - mixed states
 *   - noise channels
 *   - fidelity and purity
 *   - a small single-qubit simulator
 *   - SVG visualization
 */

"use strict";

// -----------------------------------------------------------------------------
// Complex-number implementation
// -----------------------------------------------------------------------------

class Complex {
    constructor(real = 0, imaginary = 0) {
        this.re = real;
        this.im = imaginary;
    }

    add(other) {
        return new Complex(this.re + other.re, this.im + other.im);
    }

    sub(other) {
        return new Complex(this.re - other.re, this.im - other.im);
    }

    mul(other) {
        return new Complex(
            this.re * other.re - this.im * other.im,
            this.re * other.im + this.im * other.re
        );
    }

    scale(value) {
        return new Complex(this.re * value, this.im * value);
    }

    conjugate() {
        return new Complex(this.re, -this.im);
    }

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    toString(precision = 5) {
        const real = Math.abs(this.re) < 1e-10 ? 0 : this.re;
        const imaginary = Math.abs(this.im) < 1e-10 ? 0 : this.im;

        if (imaginary === 0) {
            return real.toFixed(precision);
        }

        if (real === 0) {
            return `${imaginary.toFixed(precision)}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";
        return `${real.toFixed(precision)} ${sign} ${Math.abs(imaginary).toFixed(precision)}i`;
    }

    static fromPolar(radius, angle) {
        return new Complex(
            radius * Math.cos(angle),
            radius * Math.sin(angle)
        );
    }
}

const C = (real, imaginary = 0) => new Complex(real, imaginary);

const ZERO = C(0);
const ONE = C(1);
const I = C(0, 1);

function vectorNorm(vector) {
    return Math.sqrt(
        vector.reduce((sum, value) => sum + value.magnitudeSquared(), 0)
    );
}

function normalizeState(state) {
    if (state.length !== 2) {
        throw new Error("A single-qubit state must contain two amplitudes.");
    }

    const norm = vectorNorm(state);

    if (norm < 1e-12) {
        throw new Error("The zero vector cannot represent a quantum state.");
    }

    return state.map(value => value.scale(1 / norm));
}

function innerProduct(a, b) {
    if (a.length !== b.length) {
        throw new Error("Vectors must have equal dimensions.");
    }

    return a.reduce(
        (sum, value, index) => sum.add(value.conjugate().mul(b[index])),
        C(0)
    );
}

function matrixVectorMultiply(matrix, vector) {
    return matrix.map(row =>
        row.reduce(
            (sum, value, index) => sum.add(value.mul(vector[index])),
            C(0)
        )
    );
}

function matrixMultiply(a, b) {
    if (a[0].length !== b.length) {
        throw new Error("Matrix dimensions do not match.");
    }

    return a.map((row, i) =>
        b[0].map((_, j) =>
            row.reduce(
                (sum, value, k) => sum.add(value.mul(b[k][j])),
                C(0)
            )
        )
    );
}

function dagger(matrix) {
    return matrix[0].map((_, column) =>
        matrix.map(row => row[column].conjugate())
    );
}

function trace(matrix) {
    return matrix.reduce(
        (sum, row, index) => sum.add(row[index]),
        C(0)
    );
}

function outerProduct(state) {
    return state.map(a =>
        state.map(b => a.mul(b.conjugate()))
    );
}

function matrixAdd(a, b) {
    return a.map((row, i) =>
        row.map((value, j) => value.add(b[i][j]))
    );
}

function matrixScale(scalar, matrix) {
    return matrix.map(row => row.map(value => value.scale(scalar)));
}

// -----------------------------------------------------------------------------
// Pauli matrices and standard gates
// -----------------------------------------------------------------------------

const Identity = [
    [ONE, ZERO],
    [ZERO, ONE]
];

const X = [
    [ZERO, ONE],
    [ONE, ZERO]
];

const Y = [
    [ZERO, C(0, -1)],
    [I, ZERO]
];

const Z = [
    [ONE, ZERO],
    [ZERO, C(-1)]
];

const H = [
    [C(1 / Math.sqrt(2)), C(1 / Math.sqrt(2))],
    [C(1 / Math.sqrt(2)), C(-1 / Math.sqrt(2))]
];

const S = [
    [ONE, ZERO],
    [ZERO, I]
];

const T = [
    [ONE, ZERO],
    [ZERO, Complex.fromPolar(1, Math.PI / 4)]
];

function Rx(theta) {
    const c = Math.cos(theta / 2);
    const s = Math.sin(theta / 2);

    return [
        [C(c), C(0, -s)],
        [C(0, -s), C(c)]
    ];
}

function Ry(theta) {
    const c = Math.cos(theta / 2);
    const s = Math.sin(theta / 2);

    return [
        [C(c), C(-s)],
        [C(s), C(c)]
    ];
}

function Rz(theta) {
    return [
        [Complex.fromPolar(1, -theta / 2), ZERO],
        [ZERO, Complex.fromPolar(1, theta / 2)]
    ];
}

// -----------------------------------------------------------------------------
// Bloch-sphere representation
// -----------------------------------------------------------------------------

class BlochVector {
    constructor(x, y, z) {
        this.x = x;
        this.y = y;
        this.z = z;
    }

    norm() {
        return Math.sqrt(this.x ** 2 + this.y ** 2 + this.z ** 2);
    }

    isValid() {
        return this.norm() <= 1 + 1e-10;
    }

    isPure() {
        return Math.abs(this.norm() - 1) < 1e-8;
    }

    sphericalCoordinates() {
        const r = this.norm();

        if (r < 1e-12) {
            return { theta: 0, phi: 0 };
        }

        const theta = Math.acos(Math.max(-1, Math.min(1, this.z / r)));
        let phi = Math.atan2(this.y, this.x);

        if (phi < 0) {
            phi += 2 * Math.PI;
        }

        return { theta, phi };
    }

    toString() {
        return `(${this.x.toFixed(6)}, ${this.y.toFixed(6)}, ${this.z.toFixed(6)})`;
    }
}

function stateFromBloch(theta, phi) {
    return [
        C(Math.cos(theta / 2)),
        Complex.fromPolar(Math.sin(theta / 2), phi)
    ];
}

function blochFromState(state) {
    const [alpha, beta] = normalizeState(state);
    const crossTerm = alpha.conjugate().mul(beta);

    return new BlochVector(
        2 * crossTerm.re,
        2 * crossTerm.im,
        alpha.magnitudeSquared() - beta.magnitudeSquared()
    );
}

function densityMatrixFromState(state) {
    return outerProduct(normalizeState(state));
}

function densityMatrixFromBloch(bloch) {
    if (!bloch.isValid()) {
        throw new Error("Bloch vectors must lie inside or on the unit sphere.");
    }

    let result = matrixScale(0.5, Identity);
    result = matrixAdd(result, matrixScale(0.5 * bloch.x, X));
    result = matrixAdd(result, matrixScale(0.5 * bloch.y, Y));
    result = matrixAdd(result, matrixScale(0.5 * bloch.z, Z));

    return result;
}

function blochFromDensityMatrix(rho) {
    return new BlochVector(
        trace(matrixMultiply(rho, X)).re,
        trace(matrixMultiply(rho, Y)).re,
        trace(matrixMultiply(rho, Z)).re
    );
}

// -----------------------------------------------------------------------------
// Measurement and quantum-state operations
// -----------------------------------------------------------------------------

function measurementProbabilities(state) {
    const normalized = normalizeState(state);

    let p0 = normalized[0].magnitudeSquared();
    let p1 = normalized[1].magnitudeSquared();

    p0 = Math.max(0, Math.min(1, p0));
    p1 = Math.max(0, Math.min(1, p1));

    return { p0, p1 };
}

function measure(state, randomValue = Math.random()) {
    const { p0 } = measurementProbabilities(state);

    if (randomValue < p0) {
        return {
            outcome: 0,
            state: [ONE, ZERO]
        };
    }

    return {
        outcome: 1,
        state: [ZERO, ONE]
    };
}

function applyGate(state, gate) {
    return normalizeState(matrixVectorMultiply(gate, state));
}

function purity(rho) {
    return trace(matrixMultiply(rho, rho)).re;
}

function fidelityPureStates(a, b) {
    return innerProduct(normalizeState(a), normalizeState(b))
        .magnitudeSquared();
}

function validateProbability(probability) {
    if (probability < 0 || probability > 1) {
        throw new Error("Probability must be between 0 and 1.");
    }
}

// -----------------------------------------------------------------------------
// Noise channels
// -----------------------------------------------------------------------------

function conjugateByPauli(rho, pauli) {
    return matrixMultiply(
        matrixMultiply(pauli, rho),
        pauli
    );
}

function bitFlipChannel(rho, probability) {
    validateProbability(probability);

    return matrixAdd(
        matrixScale(1 - probability, rho),
        matrixScale(probability, conjugateByPauli(rho, X))
    );
}

function phaseFlipChannel(rho, probability) {
    validateProbability(probability);

    return matrixAdd(
        matrixScale(1 - probability, rho),
        matrixScale(probability, conjugateByPauli(rho, Z))
    );
}

function depolarizingChannel(rho, probability) {
    validateProbability(probability);

    let result = matrixScale(1 - probability, rho);

    for (const pauli of [X, Y, Z]) {
        result = matrixAdd(
            result,
            matrixScale(
                probability / 3,
                conjugateByPauli(rho, pauli)
            )
        );
    }

    return result;
}

// -----------------------------------------------------------------------------
// Single-qubit simulator
// -----------------------------------------------------------------------------

class QubitSimulator {
    constructor(initialState = [ONE, ZERO]) {
        this.state = normalizeState(initialState);
        this.history = [
            {
                operation: "initial",
                bloch: blochFromState(this.state)
            }
        ];
    }

    applyGate(name, gate) {
        this.state = applyGate(this.state, gate);

        this.history.push({
            operation: name,
            bloch: blochFromState(this.state)
        });

        return this;
    }

    measure(randomValue = Math.random()) {
        const result = measure(this.state, randomValue);

        this.state = result.state;

        this.history.push({
            operation: `measure -> ${result.outcome}`,
            bloch: blochFromState(this.state)
        });

        return result.outcome;
    }

    currentBloch() {
        return blochFromState(this.state);
    }

    printHistory() {
        for (const entry of this.history) {
            console.log(
                `${entry.operation.padEnd(18)} ${entry.bloch.toString()}`
            );
        }
    }
}

// -----------------------------------------------------------------------------
// SVG visualization
// -----------------------------------------------------------------------------

function projectBlochVector(bloch, width = 700, height = 500) {
    /*
     * This is an orthographic educational projection rather than a full
     * perspective renderer. The x and y components form the horizontal and
     * vertical coordinates while z provides depth through a small offset.
     */
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.32;

    const projectedX = centerX + radius * (bloch.x - 0.45 * bloch.z);
    const projectedY = centerY - radius * (bloch.y + 0.25 * bloch.z);

    return {
        x: projectedX,
        y: projectedY
    };
}

function createBlochSphereSVG(bloch, width = 700, height = 500) {
    const point = projectBlochVector(bloch, width, height);
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.32;

    const axes = `
        <line x1="${centerX - radius}" y1="${centerY}"
              x2="${centerX + radius}" y2="${centerY}"
              stroke="#777" stroke-width="1.5"/>
        <line x1="${centerX}" y1="${centerY - radius}"
              x2="${centerX}" y2="${centerY + radius}"
              stroke="#777" stroke-width="1.5"/>
    `;

    const sphere = `
        <circle cx="${centerX}" cy="${centerY}" r="${radius}"
                fill="none" stroke="#333" stroke-width="2"/>
        <ellipse cx="${centerX}" cy="${centerY}"
                 rx="${radius}" ry="${radius * 0.35}"
                 fill="none" stroke="#999" stroke-width="1"/>
    `;

    const labels = `
        <text x="${centerX + radius + 10}" y="${centerY + 5}"
              font-size="16">+X</text>
        <text x="${centerX - radius - 35}" y="${centerY + 5}"
              font-size="16">-X</text>
        <text x="${centerX + 8}" y="${centerY - radius - 10}"
              font-size="16">+Z |0&gt;</text>
        <text x="${centerX + 8}" y="${centerY + radius + 20}"
              font-size="16">-Z |1&gt;</text>
        <text x="${centerX + radius * 0.5}" y="${centerY - radius * 0.25}"
              font-size="16">+Y</text>
    `;

    const vector = `
        <line x1="${centerX}" y1="${centerY}"
              x2="${point.x}" y2="${point.y}"
              stroke="#174d2c" stroke-width="4"/>
        <circle cx="${point.x}" cy="${point.y}" r="8"
                fill="#174d2c"/>
    `;

    return `
<svg xmlns="http://www.w3.org/2000/svg"
     width="${width}" height="${height}"
     viewBox="0 0 ${width} ${height}">
    <rect width="100%" height="100%" fill="white"/>
    <text x="${width / 2}" y="28"
          text-anchor="middle"
          font-size="22"
          font-family="Arial">
        Bloch Sphere
    </text>
    ${sphere}
    ${axes}
    ${labels}
    ${vector}
</svg>`;
}

// -----------------------------------------------------------------------------
// Demonstrations
// -----------------------------------------------------------------------------

function printState(label, state) {
    console.log(label, state.map(value => value.toString()));
}

function demonstrateBasics() {
    console.log("\n=== 1. Basic qubit states ===");

    const zero = [ONE, ZERO];
    const one = [ZERO, ONE];

    printState("|0>", zero);
    console.log("Bloch(|0>) =", blochFromState(zero).toString());

    printState("|1>", one);
    console.log("Bloch(|1>) =", blochFromState(one).toString());

    const plus = applyGate(zero, H);
    const minus = applyGate(one, H);

    printState("|+>", plus);
    console.log("Bloch(|+>) =", blochFromState(plus).toString());

    printState("|->", minus);
    console.log("Bloch(|->) =", blochFromState(minus).toString());
}

function demonstrateSphericalCoordinates() {
    console.log("\n=== 2. Spherical coordinates ===");

    const examples = [
        ["north pole", 0, 0],
        ["equator +X", Math.PI / 2, 0],
        ["equator +Y", Math.PI / 2, Math.PI / 2],
        ["south pole", Math.PI, 0]
    ];

    for (const [name, theta, phi] of examples) {
        const state = stateFromBloch(theta, phi);
        const bloch = blochFromState(state);

        console.log(
            `${name}: theta=${theta.toFixed(4)}, phi=${phi.toFixed(4)},`,
            `Bloch=${bloch.toString()}`
        );
    }
}

function demonstrateGates() {
    console.log("\n=== 3. Quantum gates as rotations ===");

    const zero = [ONE, ZERO];

    const gates = [
        ["X", X],
        ["Y", Y],
        ["Z", Z],
        ["H", H],
        ["S", S],
        ["T", T]
    ];

    for (const [name, gate] of gates) {
        const state = applyGate(zero, gate);
        console.log(`${name}|0> -> ${blochFromState(state).toString()}`);
    }

    const plus = applyGate(zero, H);
    console.log(
        "Rz(pi/2)|+> ->",
        blochFromState(applyGate(plus, Rz(Math.PI / 2))).toString()
    );
}

function demonstratePhases() {
    console.log("\n=== 4. Global phase and relative phase ===");

    const state = stateFromBloch(Math.PI / 3, Math.PI / 5);
    const globalPhase = Complex.fromPolar(1, 1.7);

    const globallyPhased = state.map(value => value.mul(globalPhase));

    console.log(
        "Original:",
        blochFromState(state).toString()
    );

    console.log(
        "Global phase applied:",
        blochFromState(globallyPhased).toString()
    );

    console.log(
        "Fidelity:",
        fidelityPureStates(state, globallyPhased).toFixed(8)
    );

    for (const phi of [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2]) {
        const relativeState = stateFromBloch(Math.PI / 2, phi);

        console.log(
            `Relative phase ${phi.toFixed(3)} ->`,
            blochFromState(relativeState).toString()
        );
    }
}

function demonstrateDensityMatrices() {
    console.log("\n=== 5. Density matrices and mixed states ===");

    const state = stateFromBloch(Math.PI / 2, Math.PI / 4);
    const rho = densityMatrixFromState(state);
    const bloch = blochFromDensityMatrix(rho);

    console.log("Pure-state Bloch vector:", bloch.toString());
    console.log("Pure-state purity:", purity(rho).toFixed(8));

    const mixed = densityMatrixFromBloch(new BlochVector(0.3, 0.4, 0.2));

    console.log(
        "Mixed-state Bloch vector:",
        blochFromDensityMatrix(mixed).toString()
    );

    console.log(
        "Mixed-state purity:",
        purity(mixed).toFixed(8)
    );

    const maximallyMixed = densityMatrixFromBloch(
        new BlochVector(0, 0, 0)
    );

    console.log(
        "Maximally mixed purity:",
        purity(maximallyMixed).toFixed(8)
    );
}

function demonstrateNoise() {
    console.log("\n=== 6. Noise channels ===");

    const state = stateFromBloch(1.1, 2.2);
    const rho = densityMatrixFromState(state);

    for (const probability of [0.1, 0.25, 0.5]) {
        const noisy = depolarizingChannel(rho, probability);

        console.log(
            `Depolarizing p=${probability}:`,
            blochFromDensityMatrix(noisy).toString(),
            "purity=",
            purity(noisy).toFixed(6)
        );
    }

    const dephased = phaseFlipChannel(rho, 0.25);

    console.log(
        "Phase-flip p=0.25:",
        blochFromDensityMatrix(dephased).toString()
    );
}

function demonstrateMeasurement() {
    console.log("\n=== 7. Measurement statistics ===");

    const state = stateFromBloch(Math.PI / 3, 1.2);
    const probabilities = measurementProbabilities(state);

    console.log(
        "P(0) =",
        probabilities.p0.toFixed(6),
        "P(1) =",
        probabilities.p1.toFixed(6)
    );

    let counts = { 0: 0, 1: 0 };

    for (let shot = 0; shot < 10000; shot++) {
        counts[measure(state).outcome]++;
    }

    console.log("10000-shot sample:", counts);
}

function demonstrateSimulator() {
    console.log("\n=== 8. Gate-sequence simulator ===");

    const simulator = new QubitSimulator();

    simulator
        .applyGate("H", H)
        .applyGate("S", S)
        .applyGate("Rx(pi/3)", Rx(Math.PI / 3))
        .applyGate("Rz(pi/5)", Rz(Math.PI / 5));

    simulator.printHistory();

    const outcome = simulator.measure(0.2);

    console.log("Measurement outcome:", outcome);
    console.log(
        "Post-measurement Bloch:",
        simulator.currentBloch().toString()
    );
}

function demonstrateRotationTable() {
    console.log("\n=== 9. Continuous Z rotations ===");

    const initial = stateFromBloch(Math.PI / 2, 0);

    for (const degrees of [0, 45, 90, 135, 180, 270]) {
        const angle = degrees * Math.PI / 180;
        const rotated = applyGate(initial, Rz(angle));

        console.log(
            `${degrees.toString().padStart(3)}° ->`,
            rotated ? blochFromState(rotated).toString() : ""
        );
    }
}

function demonstrateSVG() {
    console.log("\n=== 10. SVG visualization ===");

    const state = stateFromBloch(1.0, 0.9);
    const bloch = blochFromState(state);
    const svg = createBlochSphereSVG(bloch);

    console.log("SVG generated for Bloch vector:", bloch.toString());
    console.log("To save it, write the returned SVG string to a .svg file.");
    return svg;
}

function runValidation() {
    console.log("\n=== 11. Validation ===");

    const testStates = [
        stateFromBloch(0, 0),
        stateFromBloch(Math.PI / 2, 0),
        stateFromBloch(Math.PI / 2, Math.PI / 2),
        stateFromBloch(Math.PI, 0),
        stateFromBloch(1.234, 4.321)
    ];

    for (const state of testStates) {
        const normalized = normalizeState(state);
        const norm = vectorNorm(normalized);

        if (Math.abs(norm - 1) > 1e-10) {
            throw new Error("State normalization failed.");
        }

        const bloch = blochFromState(normalized);

        if (Math.abs(bloch.norm() - 1) > 1e-8) {
            throw new Error("Pure state did not map to sphere surface.");
        }
    }

    console.log("Pure-state normalization tests passed.");

    const invalid = new BlochVector(1.2, 0, 0);

    try {
        densityMatrixFromBloch(invalid);
        throw new Error("Invalid Bloch vector was incorrectly accepted.");
    } catch (error) {
        if (!error.message.includes("Bloch vectors")) {
            throw error;
        }
    }

    console.log("Invalid-state validation passed.");
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

function main() {
    console.log("=".repeat(78));
    console.log("BLOCH SPHERE: JAVASCRIPT SINGLE-QUBIT STUDY");
    console.log("=".repeat(78));

    demonstrateBasics();
    demonstrateSphericalCoordinates();
    demonstrateGates();
    demonstratePhases();
    demonstrateDensityMatrices();
    demonstrateNoise();
    demonstrateMeasurement();
    demonstrateSimulator();
    demonstrateRotationTable();
    demonstrateSVG();
    runValidation();

    console.log("\nProgram completed successfully.");
}

if (require.main === module) {
    main();
}
