/*
 * Rotation Gates: RX, RY, RZ
 * ==========================
 *
 * A self-contained JavaScript study file for single-qubit rotation gates.
 *
 * This implementation emphasizes JavaScript-specific practical concerns:
 * - arrays and objects for complex vectors/matrices
 * - functional transformations
 * - classes for circuit modeling
 * - validation and exceptions
 * - deterministic measurement simulation
 * - asynchronous execution of parameterized circuit experiments
 * - JSON-compatible experiment results
 *
 * No external npm packages are required.
 */

"use strict";

// -----------------------------------------------------------------------------
// Numerical helpers
// -----------------------------------------------------------------------------

const EPSILON = 1e-10;
const PI = Math.PI;
const TAU = 2 * Math.PI;

function nearlyEqual(a, b, tolerance = EPSILON) {
    return Math.abs(a - b) <= tolerance;
}

function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
}

function wrapAngle(angle) {
    let wrapped = ((angle + PI) % TAU + TAU) % TAU - PI;
    if (wrapped === PI) {
        wrapped = -PI;
    }
    return wrapped;
}

// -----------------------------------------------------------------------------
// Complex-number representation
// -----------------------------------------------------------------------------

function complex(real = 0, imaginary = 0) {
    return { real, imaginary };
}

function addComplex(a, b) {
    return complex(a.real + b.real, a.imaginary + b.imaginary);
}

function subtractComplex(a, b) {
    return complex(a.real - b.real, a.imaginary - b.imaginary);
}

function multiplyComplex(a, b) {
    return complex(
        a.real * b.real - a.imaginary * b.imaginary,
        a.real * b.imaginary + a.imaginary * b.real
    );
}

function conjugateComplex(a) {
    return complex(a.real, -a.imaginary);
}

function scaleComplex(a, scalar) {
    return complex(a.real * scalar, a.imaginary * scalar);
}

function magnitudeSquared(a) {
    return a.real * a.real + a.imaginary * a.imaginary;
}

function magnitude(a) {
    return Math.sqrt(magnitudeSquared(a));
}

function complexExp(imaginaryAngle) {
    return complex(Math.cos(imaginaryAngle), Math.sin(imaginaryAngle));
}

function formatComplex(value, digits = 5) {
    const real = Math.abs(value.real) < 10 ** (-digits) ? 0 : value.real;
    const imaginary =
        Math.abs(value.imaginary) < 10 ** (-digits)
            ? 0
            : value.imaginary;

    if (imaginary === 0) {
        return real.toFixed(digits);
    }

    if (real === 0) {
        return `${imaginary.toFixed(digits)}i`;
    }

    const sign = imaginary >= 0 ? "+" : "-";
    return `${real.toFixed(digits)} ${sign} ${Math.abs(imaginary).toFixed(
        digits
    )}i`;
}

// -----------------------------------------------------------------------------
// 2x2 complex matrices
// -----------------------------------------------------------------------------

function matrix2x2(a00, a01, a10, a11) {
    return [
        [a00, a01],
        [a10, a11]
    ];
}

function identityMatrix() {
    return matrix2x2(
        complex(1),
        complex(0),
        complex(0),
        complex(1)
    );
}

function matrixMultiply(a, b) {
    return matrix2x2(
        addComplex(
            multiplyComplex(a[0][0], b[0][0]),
            multiplyComplex(a[0][1], b[1][0])
        ),
        addComplex(
            multiplyComplex(a[0][0], b[0][1]),
            multiplyComplex(a[0][1], b[1][1])
        ),
        addComplex(
            multiplyComplex(a[1][0], b[0][0]),
            multiplyComplex(a[1][1], b[1][0])
        ),
        addComplex(
            multiplyComplex(a[1][0], b[0][1]),
            multiplyComplex(a[1][1], b[1][1])
        )
    );
}

function matrixVectorMultiply(matrix, vector) {
    return [
        addComplex(
            multiplyComplex(matrix[0][0], vector[0]),
            multiplyComplex(matrix[0][1], vector[1])
        ),
        addComplex(
            multiplyComplex(matrix[1][0], vector[0]),
            multiplyComplex(matrix[1][1], vector[1])
        )
    ];
}

function conjugateTranspose(matrix) {
    return matrix2x2(
        conjugateComplex(matrix[0][0]),
        conjugateComplex(matrix[1][0]),
        conjugateComplex(matrix[0][1]),
        conjugateComplex(matrix[1][1])
    );
}

function matrixDifferenceNorm(a, b) {
    let sum = 0;

    for (let row = 0; row < 2; row += 1) {
        for (let column = 0; column < 2; column += 1) {
            const difference = subtractComplex(
                a[row][column],
                b[row][column]
            );
            sum += magnitudeSquared(difference);
        }
    }

    return Math.sqrt(sum);
}

function isUnitary(matrix, tolerance = 1e-9) {
    const product = matrixMultiply(conjugateTranspose(matrix), matrix);
    return matrixDifferenceNorm(product, identityMatrix()) <= tolerance;
}

function printMatrix(matrix, name) {
    console.log(`\n${name}:`);

    for (const row of matrix) {
        console.log(
            "  [ " +
                row.map(value => formatComplex(value)).join(" , ") +
                " ]"
        );
    }
}

// -----------------------------------------------------------------------------
// Qubit class
// -----------------------------------------------------------------------------

class Qubit {
    /*
     * A pure single-qubit state:
     *
     *     |psi> = alpha|0> + beta|1>
     *
     * JavaScript does not have a built-in complex-number primitive, so this
     * example uses {real, imaginary} objects.
     */

    constructor(alpha, beta) {
        this.alpha = alpha;
        this.beta = beta;

        this.validateNormalization();
    }

    validateNormalization(tolerance = 1e-9) {
        const normSquared =
            magnitudeSquared(this.alpha) +
            magnitudeSquared(this.beta);

        if (Math.abs(normSquared - 1) > tolerance) {
            throw new Error(
                "Qubit amplitudes must be normalized: |alpha|^2 + |beta|^2 = 1."
            );
        }
    }

    static zero() {
        return new Qubit(complex(1), complex(0));
    }

    static one() {
        return new Qubit(complex(0), complex(1));
    }

    static plus() {
        const amplitude = 1 / Math.sqrt(2);
        return new Qubit(complex(amplitude), complex(amplitude));
    }

    static minus() {
        const amplitude = 1 / Math.sqrt(2);
        return new Qubit(complex(amplitude), complex(-amplitude));
    }

    static fromBloch(theta, phi) {
        const alpha = Math.cos(theta / 2);
        const beta = complexExp(phi);
        return new Qubit(
            complex(alpha),
            scaleComplex(beta, Math.sin(theta / 2))
        );
    }

    apply(gate) {
        if (!isUnitary(gate)) {
            throw new Error("Cannot apply a non-unitary matrix as a gate.");
        }

        const result = matrixVectorMultiply(gate, [
            this.alpha,
            this.beta
        ]);

        return Qubit.normalize(result[0], result[1]);
    }

    static normalize(alpha, beta) {
        const norm = Math.sqrt(
            magnitudeSquared(alpha) + magnitudeSquared(beta)
        );

        if (norm < EPSILON) {
            throw new Error("Cannot normalize a zero state vector.");
        }

        return new Qubit(
            scaleComplex(alpha, 1 / norm),
            scaleComplex(beta, 1 / norm)
        );
    }

    probabilityZero() {
        return magnitudeSquared(this.alpha);
    }

    probabilityOne() {
        return magnitudeSquared(this.beta);
    }

    blochVector() {
        const coherence = multiplyComplex(
            conjugateComplex(this.alpha),
            this.beta
        );

        return {
            x: 2 * coherence.real,
            y: 2 * coherence.imaginary,
            z: this.probabilityZero() - this.probabilityOne()
        };
    }

    relativePhase() {
        if (
            magnitude(this.alpha) < EPSILON ||
            magnitude(this.beta) < EPSILON
        ) {
            throw new Error(
                "Relative phase is undefined when one amplitude is zero."
            );
        }

        return (
            Math.atan2(this.beta.imaginary, this.beta.real) -
            Math.atan2(this.alpha.imaginary, this.alpha.real)
        );
    }

    withGlobalPhase(angle) {
        const phase = complexExp(angle);

        return new Qubit(
            multiplyComplex(this.alpha, phase),
            multiplyComplex(this.beta, phase)
        );
    }
}

function printState(state, label) {
    const bloch = state.blochVector();

    console.log(
        `\n${label}: ${formatComplex(state.alpha)}|0> + ` +
        `${formatComplex(state.beta)}|1>`
    );

    console.log(
        `  P(0) = ${state.probabilityZero().toFixed(6)}, ` +
        `P(1) = ${state.probabilityOne().toFixed(6)}`
    );

    console.log(
        `  Bloch vector = (${bloch.x.toFixed(6)}, ` +
        `${bloch.y.toFixed(6)}, ${bloch.z.toFixed(6)})`
    );
}

// -----------------------------------------------------------------------------
// Rotation gates
// -----------------------------------------------------------------------------

function RX(theta) {
    const c = Math.cos(theta / 2);
    const s = Math.sin(theta / 2);

    return matrix2x2(
        complex(c),
        complex(0, -s),
        complex(0, -s),
        complex(c)
    );
}

function RY(theta) {
    const c = Math.cos(theta / 2);
    const s = Math.sin(theta / 2);

    return matrix2x2(
        complex(c),
        complex(-s),
        complex(s),
        complex(c)
    );
}

function RZ(theta) {
    return matrix2x2(
        complexExp(-theta / 2),
        complex(0),
        complex(0),
        complexExp(theta / 2)
    );
}

function arbitraryAxisRotation(axis, angle) {
    let [x, y, z] = axis;

    const length = Math.sqrt(x * x + y * y + z * z);

    if (length < EPSILON) {
        throw new Error("The rotation axis cannot be the zero vector.");
    }

    x /= length;
    y /= length;
    z /= length;

    const c = Math.cos(angle / 2);
    const s = Math.sin(angle / 2);

    return matrix2x2(
        complex(c, -s * z),
        complex(-s * y, -s * x),
        complex(s * y, -s * x),
        complex(c, s * z)
    );
}

// -----------------------------------------------------------------------------
// Circuit class
// -----------------------------------------------------------------------------

class SingleQubitCircuit {
    constructor(initialState = Qubit.zero()) {
        this.initialState = initialState;
        this.operations = [];
    }

    addGate(name, matrix, angle = null) {
        if (!isUnitary(matrix)) {
            throw new Error(`Gate ${name} is not unitary.`);
        }

        this.operations.push({
            name,
            matrix,
            angle
        });

        return this;
    }

    rx(theta) {
        return this.addGate("RX", RX(theta), theta);
    }

    ry(theta) {
        return this.addGate("RY", RY(theta), theta);
    }

    rz(theta) {
        return this.addGate("RZ", RZ(theta), theta);
    }

    run() {
        let state = this.initialState;

        for (const operation of this.operations) {
            state = state.apply(operation.matrix);
        }

        return state;
    }

    combinedUnitary() {
        /*
         * If gates are applied as G1, G2, G3, the circuit is:
         *
         *     G3 G2 G1 |psi>
         *
         * Therefore each new gate multiplies the current matrix on the left.
         */
        let combined = identityMatrix();

        for (const operation of this.operations) {
            combined = matrixMultiply(operation.matrix, combined);
        }

        return combined;
    }

    describe() {
        console.log("\nCircuit:");

        this.operations.forEach((operation, index) => {
            if (operation.angle === null) {
                console.log(`  ${index + 1}. ${operation.name}`);
            } else {
                console.log(
                    `  ${index + 1}. ${operation.name}(` +
                    `${operation.angle.toFixed(6)} radians)`
                );
            }
        });
    }
}

// -----------------------------------------------------------------------------
// Fidelity and physical equivalence
// -----------------------------------------------------------------------------

function stateFidelity(a, b) {
    const innerProduct = addComplex(
        multiplyComplex(
            conjugateComplex(a.alpha),
            b.alpha
        ),
        multiplyComplex(
            conjugateComplex(a.beta),
            b.beta
        )
    );

    return magnitudeSquared(innerProduct);
}

function equivalentUpToGlobalPhase(a, b, tolerance = 1e-9) {
    return stateFidelity(a, b) >= 1 - tolerance;
}

// -----------------------------------------------------------------------------
// Measurement simulation
// -----------------------------------------------------------------------------

function createSeededRandom(seed) {
    /*
     * A small deterministic linear-congruential generator makes measurement
     * experiments reproducible without external libraries.
     */
    let state = seed >>> 0;

    return function random() {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 0x100000000;
    };
}

function sampleMeasurements(qubit, shots, seed = 12345) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new Error("shots must be a positive integer.");
    }

    const random = createSeededRandom(seed);
    const probabilityZero = qubit.probabilityZero();

    const counts = {
        0: 0,
        1: 0
    };

    for (let shot = 0; shot < shots; shot += 1) {
        if (random() < probabilityZero) {
            counts[0] += 1;
        } else {
            counts[1] += 1;
        }
    }

    return counts;
}

// -----------------------------------------------------------------------------
// Expectation values
// -----------------------------------------------------------------------------

const PAULI_X = matrix2x2(
    complex(0),
    complex(1),
    complex(1),
    complex(0)
);

const PAULI_Y = matrix2x2(
    complex(0),
    complex(0, -1),
    complex(0, 1),
    complex(0)
);

const PAULI_Z = matrix2x2(
    complex(1),
    complex(0),
    complex(0),
    complex(-1)
);

function expectationValue(qubit, observable) {
    const transformed = matrixVectorMultiply(observable, [
        qubit.alpha,
        qubit.beta
    ]);

    const first = multiplyComplex(
        conjugateComplex(qubit.alpha),
        transformed[0]
    );

    const second = multiplyComplex(
        conjugateComplex(qubit.beta),
        transformed[1]
    );

    const value = addComplex(first, second);

    if (Math.abs(value.imaginary) > 1e-8) {
        throw new Error(
            "Expectation value is significantly complex. " +
            "The observable may not be Hermitian."
        );
    }

    return value.real;
}

// -----------------------------------------------------------------------------
// Demonstration 1: basic gates
// -----------------------------------------------------------------------------

function demonstrateBasicGates() {
    console.log("\n" + "=".repeat(78));
    console.log("1. BASIC RX, RY, RZ GATES");
    console.log("=".repeat(78));

    printMatrix(RX(PI / 2), "RX(pi/2)");
    printMatrix(RY(PI / 2), "RY(pi/2)");
    printMatrix(RZ(PI / 2), "RZ(pi/2)");

    console.log("\nUnitarity:");
    console.log(`  RX: ${isUnitary(RX(PI / 2))}`);
    console.log(`  RY: ${isUnitary(RY(PI / 2))}`);
    console.log(`  RZ: ${isUnitary(RZ(PI / 2))}`);

    printState(Qubit.zero().apply(RX(PI)), "RX(pi)|0>");
    printState(Qubit.zero().apply(RY(PI)), "RY(pi)|0>");
    printState(Qubit.zero().apply(RZ(PI / 2)), "RZ(pi/2)|0>");
}

// -----------------------------------------------------------------------------
// Demonstration 2: RY probability control
// -----------------------------------------------------------------------------

function demonstrateRYProbabilities() {
    console.log("\n" + "=".repeat(78));
    console.log("2. RY AND COMPUTATIONAL-BASIS PROBABILITIES");
    console.log("=".repeat(78));

    const angles = [0, PI / 6, PI / 3, PI / 2, PI];

    for (const angle of angles) {
        const state = Qubit.zero().apply(RY(angle));

        console.log(
            `theta=${angle.toFixed(5)} | ` +
            `P(0)=${state.probabilityZero().toFixed(6)} | ` +
            `P(1)=${state.probabilityOne().toFixed(6)}`
        );
    }

    console.log(
        "\nFor RY(theta)|0>, P(0)=cos²(theta/2) and " +
        "P(1)=sin²(theta/2)."
    );
}

// -----------------------------------------------------------------------------
// Demonstration 3: RZ and relative phase
// -----------------------------------------------------------------------------

function demonstrateRZPhase() {
    console.log("\n" + "=".repeat(78));
    console.log("3. RZ AND RELATIVE PHASE");
    console.log("=".repeat(78));

    const state = Qubit.plus();
    const rotated = state.apply(RZ(PI / 2));

    printState(state, "|+>");
    printState(rotated, "RZ(pi/2)|+>");

    console.log(
        `\nRelative phase before: ${wrapAngle(
            state.relativePhase()
        ).toFixed(6)}`
    );

    console.log(
        `Relative phase after:  ${wrapAngle(
            rotated.relativePhase()
        ).toFixed(6)}`
    );

    console.log(
        "\nRZ changes the phase relationship between |0> and |1>. " +
        "It does not directly change computational-basis probabilities."
    );
}

// -----------------------------------------------------------------------------
// Demonstration 4: non-commutativity
// -----------------------------------------------------------------------------

function demonstrateNonCommutativity() {
    console.log("\n" + "=".repeat(78));
    console.log("4. ROTATION ORDER");
    console.log("=".repeat(78));

    const theta = PI / 3;
    const phi = PI / 4;

    const rxThenRy = Qubit.zero()
        .apply(RX(theta))
        .apply(RY(phi));

    const ryThenRx = Qubit.zero()
        .apply(RY(phi))
        .apply(RX(theta));

    printState(rxThenRy, "RX then RY");
    printState(ryThenRx, "RY then RX");

    console.log(
        `\nFidelity: ${stateFidelity(
            rxThenRy,
            ryThenRx
        ).toFixed(10)}`
    );

    console.log(
        "Different-axis rotations generally do not commute."
    );
}

// -----------------------------------------------------------------------------
// Demonstration 5: same-axis combination
// -----------------------------------------------------------------------------

function demonstrateSameAxisCombination() {
    console.log("\n" + "=".repeat(78));
    console.log("5. SAME-AXIS ROTATION COMBINATION");
    console.log("=".repeat(78));

    const a = 0.37;
    const b = -0.91;

    const separate = matrixMultiply(RX(b), RX(a));
    const combined = RX(a + b);

    console.log(
        `RX(a)RX(b) matrix difference: ` +
        `${matrixDifferenceNorm(separate, combined).toExponential(4)}`
    );

    console.log(
        "\nRotations about the same axis combine by adding angles."
    );
}

// -----------------------------------------------------------------------------
// Demonstration 6: Bloch sphere
// -----------------------------------------------------------------------------

function demonstrateBlochSphere() {
    console.log("\n" + "=".repeat(78));
    console.log("6. BLOCH-SPHERE REPRESENTATION");
    console.log("=".repeat(78));

    const states = [
        ["|0>", Qubit.zero()],
        ["|1>", Qubit.one()],
        ["|+>", Qubit.plus()],
        ["|->", Qubit.minus()],
        ["|+i>", Qubit.fromBloch(PI / 2, PI / 2)]
    ];

    for (const [name, state] of states) {
        const vector = state.blochVector();

        console.log(
            `${name.padEnd(5)} -> ` +
            `(${vector.x.toFixed(5)}, ` +
            `${vector.y.toFixed(5)}, ` +
            `${vector.z.toFixed(5)})`
        );
    }

    const initial = Qubit.fromBloch(1.1, 0.4);
    printState(initial, "Initial arbitrary state");

    printState(
        initial.apply(RX(PI / 4)),
        "After RX(pi/4)"
    );

    printState(
        initial.apply(RY(PI / 4)),
        "After RY(pi/4)"
    );

    printState(
        initial.apply(RZ(PI / 4)),
        "After RZ(pi/4)"
    );
}

// -----------------------------------------------------------------------------
// Demonstration 7: measurement
// -----------------------------------------------------------------------------

function demonstrateMeasurements() {
    console.log("\n" + "=".repeat(78));
    console.log("7. MEASUREMENT SIMULATION");
    console.log("=".repeat(78));

    const state = Qubit.zero().apply(RY(PI / 3));
    const shots = 10000;
    const counts = sampleMeasurements(state, shots, 42);

    printState(state, "RY(pi/3)|0>");

    console.log(`\nCounts after ${shots} shots:`);
    console.log(`  0: ${counts[0]}`);
    console.log(`  1: ${counts[1]}`);

    console.log(
        `\nEmpirical P(0): ${(counts[0] / shots).toFixed(6)}`
    );

    console.log(
        `Empirical P(1): ${(counts[1] / shots).toFixed(6)}`
    );
}

// -----------------------------------------------------------------------------
// Demonstration 8: expectation values
// -----------------------------------------------------------------------------

function demonstrateExpectationValues() {
    console.log("\n" + "=".repeat(78));
    console.log("8. EXPECTATION VALUES");
    console.log("=".repeat(78));

    const state = Qubit.fromBloch(1.2, 0.7);
    const bloch = state.blochVector();

    printState(state, "State");

    console.log("\nPauli expectations:");
    console.log(
        `  <X> = ${expectationValue(state, PAULI_X).toFixed(8)}`
    );
    console.log(
        `  <Y> = ${expectationValue(state, PAULI_Y).toFixed(8)}`
    );
    console.log(
        `  <Z> = ${expectationValue(state, PAULI_Z).toFixed(8)}`
    );

    console.log("\nBloch coordinates:");
    console.log(
        `  x = ${bloch.x.toFixed(8)}, ` +
        `y = ${bloch.y.toFixed(8)}, ` +
        `z = ${bloch.z.toFixed(8)}`
    );
}

// -----------------------------------------------------------------------------
// Demonstration 9: arbitrary axis
// -----------------------------------------------------------------------------

function demonstrateArbitraryAxis() {
    console.log("\n" + "=".repeat(78));
    console.log("9. GENERAL AXIS ROTATION");
    console.log("=".repeat(78));

    const gate = arbitraryAxisRotation([1, 2, 3], PI / 3);

    printMatrix(gate, "Rotation around axis (1,2,3)");
    console.log(`\nUnitary: ${isUnitary(gate)}`);

    const state = Qubit.fromBloch(0.9, -0.5);

    printState(
        state.apply(gate),
        "State after arbitrary-axis rotation"
    );
}

// -----------------------------------------------------------------------------
// Demonstration 10: circuit execution
// -----------------------------------------------------------------------------

function demonstrateCircuit() {
    console.log("\n" + "=".repeat(78));
    console.log("10. PARAMETERIZED CIRCUIT");
    console.log("=".repeat(78));

    const circuit = new SingleQubitCircuit()
        .ry(PI / 3)
        .rz(PI / 5)
        .rx(-PI / 7)
        .ry(0.41);

    circuit.describe();

    const result = circuit.run();
    printState(result, "Circuit output");

    const combined = circuit.combinedUnitary();

    printMatrix(combined, "Combined unitary");

    console.log(`\nCombined unitary: ${isUnitary(combined)}`);

    const direct = Qubit.zero().apply(combined);

    console.log(
        `Direct-application fidelity: ` +
        `${stateFidelity(result, direct).toFixed(12)}`
    );
}

// -----------------------------------------------------------------------------
// Demonstration 11: asynchronous parameter sweep
// -----------------------------------------------------------------------------

async function runParameterSweep() {
    console.log("\n" + "=".repeat(78));
    console.log("11. ASYNCHRONOUS PARAMETER SWEEP");
    console.log("=".repeat(78));

    /*
     * JavaScript applications often perform quantum-circuit evaluations
     * asynchronously, especially when a circuit is submitted to a remote
     * simulator or hardware service.
     *
     * This local Promise-based example models that application pattern
     * without requiring an external service.
     */

    const angles = [0, PI / 6, PI / 3, PI / 2, (2 * PI) / 3];

    const experiments = angles.map(
        angle =>
            new Promise(resolve => {
                setTimeout(() => {
                    const state = Qubit.zero().apply(RY(angle));

                    resolve({
                        angle,
                        probabilityZero: state.probabilityZero(),
                        probabilityOne: state.probabilityOne()
                    });
                }, 0);
            })
    );

    const results = await Promise.all(experiments);

    for (const result of results) {
        console.log(
            `theta=${result.angle.toFixed(5)} | ` +
            `P(0)=${result.probabilityZero.toFixed(6)} | ` +
            `P(1)=${result.probabilityOne.toFixed(6)}`
        );
    }
}

// -----------------------------------------------------------------------------
// Edge cases and validation
// -----------------------------------------------------------------------------

function demonstrateEdgeCases() {
    console.log("\n" + "=".repeat(78));
    console.log("12. EDGE CASES AND VALIDATION");
    console.log("=".repeat(78));

    console.log(`RX(0) unitary: ${isUnitary(RX(0))}`);
    console.log(`RY(2pi) unitary: ${isUnitary(RY(TAU))}`);
    console.log(`RZ(-2pi) unitary: ${isUnitary(RZ(-TAU))}`);

    try {
        arbitraryAxisRotation([0, 0, 0], PI / 2);
    } catch (error) {
        console.log(`Zero-axis rejection: ${error.message}`);
    }

    try {
        new Qubit(complex(1), complex(1));
    } catch (error) {
        console.log(`Unnormalized state rejection: ${error.message}`);
    }

    try {
        sampleMeasurements(Qubit.zero(), 0);
    } catch (error) {
        console.log(`Invalid-shot rejection: ${error.message}`);
    }

    try {
        Qubit.zero().relativePhase();
    } catch (error) {
        console.log(`Undefined-relative-phase handling: ${error.message}`);
    }
}

// -----------------------------------------------------------------------------
// Global phase and inverse rotations
// -----------------------------------------------------------------------------

function demonstratePhaseAndInverse() {
    console.log("\n" + "=".repeat(78));
    console.log("13. GLOBAL PHASE AND INVERSE ROTATIONS");
    console.log("=".repeat(78));

    const original = Qubit.fromBloch(PI / 2, PI / 3);
    const shifted = original.withGlobalPhase(1.7);

    console.log(
        `Fidelity under global phase: ` +
        `${stateFidelity(original, shifted).toFixed(12)}`
    );

    const angle = 0.83;

    const restored = original
        .apply(RX(angle))
        .apply(RX(-angle));

    console.log(
        `Fidelity after RX(theta)RX(-theta): ` +
        `${stateFidelity(original, restored).toFixed(12)}`
    );

    console.log(
        "\nThe inverse of a rotation is the rotation with the negated angle."
    );
}

// -----------------------------------------------------------------------------
// Automated assertions
// -----------------------------------------------------------------------------

function assertCondition(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function runSelfTests() {
    console.log("\n" + "=".repeat(78));
    console.log("14. AUTOMATED SELF-TESTS");
    console.log("=".repeat(78));

    const initial = Qubit.fromBloch(0.8, -0.4);

    for (const gateFactory of [RX, RY, RZ]) {
        const result = initial.apply(gateFactory(0));
        assertCondition(
            stateFidelity(initial, result) > 1 - 1e-12,
            "Zero-angle rotation should be identity."
        );
    }

    assertCondition(
        stateFidelity(
            Qubit.zero().apply(RX(PI)),
            Qubit.one()
        ) > 1 - 1e-12,
        "RX(pi)|0> should equal |1> up to global phase."
    );

    assertCondition(
        stateFidelity(
            Qubit.zero().apply(RY(PI)),
            Qubit.one()
        ) > 1 - 1e-12,
        "RY(pi)|0> should equal |1>."
    );

    const a = 0.21;
    const b = -0.67;

    const separate = initial
        .apply(RY(a))
        .apply(RY(b));

    const combined = initial.apply(RY(a + b));

    assertCondition(
        stateFidelity(separate, combined) > 1 - 1e-12,
        "Same-axis rotations should combine."
    );

    const circuit = new SingleQubitCircuit(initial)
        .rx(0.2)
        .ry(-0.3)
        .rz(0.8);

    const circuitState = circuit.run();
    const directState = initial.apply(circuit.combinedUnitary());

    assertCondition(
        stateFidelity(circuitState, directState) > 1 - 1e-12,
        "Circuit and combined unitary should agree."
    );

    assertCondition(
        isUnitary(arbitraryAxisRotation([2, 3, 4], 0.8)),
        "Arbitrary-axis rotation must be unitary."
    );

    console.log("All JavaScript self-tests passed.");
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

async function main() {
    console.log("ROTATION GATES: RX, RY, RZ");
    console.log("Single-Qubit Quantum Computing Study Program");
    console.log("Angles are expressed in radians.");

    demonstrateBasicGates();
    demonstrateRYProbabilities();
    demonstrateRZPhase();
    demonstrateNonCommutativity();
    demonstrateSameAxisCombination();
    demonstrateBlochSphere();
    demonstrateMeasurements();
    demonstrateExpectationValues();
    demonstrateArbitraryAxis();
    demonstrateCircuit();
    await runParameterSweep();
    demonstrateEdgeCases();
    demonstratePhaseAndInverse();
    runSelfTests();

    console.log("\n" + "=".repeat(78));
    console.log("CORE FORMULAS");
    console.log("=".repeat(78));

    console.log(`
RX(theta) =
  [ cos(theta/2)      -i sin(theta/2) ]
  [ -i sin(theta/2)     cos(theta/2)  ]

RY(theta) =
  [ cos(theta/2)  -sin(theta/2) ]
  [ sin(theta/2)   cos(theta/2) ]

RZ(theta) =
  [ exp(-i theta/2)       0       ]
  [       0         exp(i theta/2) ]

State:
  |psi> = alpha|0> + beta|1>

Normalization:
  |alpha|^2 + |beta|^2 = 1

Measurement:
  P(0) = |alpha|^2
  P(1) = |beta|^2

Rotation generator:
  R_axis(theta) = exp(-i theta sigma_axis / 2)

Inverse:
  R_axis(theta)^dagger = R_axis(-theta)

Same-axis composition:
  R_axis(a)R_axis(b) = R_axis(a+b)

Different-axis rotations:
  Generally non-commutative.
`);
}

main().catch(error => {
    console.error("\nProgram terminated with an error:");
    console.error(error.message);
    process.exitCode = 1;
});
