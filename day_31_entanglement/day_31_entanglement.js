/*
 * Entanglement: Bell States and Non-Classical Correlations
 *
 * This Node.js-compatible program models two-qubit Bell states and uses
 * JavaScript's event-driven capabilities to represent a measurement stream.
 *
 * The implementation focuses on:
 *   - complex amplitudes represented explicitly
 *   - Bell-state construction
 *   - computational-basis measurement
 *   - relative phase
 *   - reduced density matrices
 *   - Pauli correlation observables
 *   - asynchronous measurement events
 *   - CHSH correlation evaluation
 *
 * Run with:
 *   node bell_states.js
 */

"use strict";

const EPSILON = 1e-10;

class Complex {
    constructor(real = 0, imaginary = 0) {
        this.re = real;
        this.im = imaginary;
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

    conjugate() {
        return new Complex(this.re, -this.im);
    }

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }

    toString() {
        if (Math.abs(this.im) < EPSILON) {
            return this.re.toFixed(4);
        }

        const sign = this.im >= 0 ? "+" : "-";
        return `${this.re.toFixed(4)} ${sign} ${Math.abs(this.im).toFixed(4)}i`;
    }
}

const C = (real, imaginary = 0) => new Complex(real, imaginary);

const BASIS_LABELS = ["00", "01", "10", "11"];

function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

function matrixMultiply(left, right) {
    assert(left.length > 0 && right.length > 0, "Matrices cannot be empty.");
    assert(
        left[0].length === right.length,
        "Matrix dimensions are incompatible."
    );

    const result = Array.from(
        { length: left.length },
        () => Array(right[0].length).fill(null).map(() => C(0))
    );

    for (let i = 0; i < left.length; i++) {
        for (let j = 0; j < right[0].length; j++) {
            let value = C(0);
            for (let k = 0; k < right.length; k++) {
                value = value.add(left[i][k].multiply(right[k][j]));
            }
            result[i][j] = value;
        }
    }

    return result;
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

function matrixVectorMultiply(matrix, vector) {
    return matrix.map(row => {
        let value = C(0);
        for (let index = 0; index < vector.length; index++) {
            value = value.add(row[index].multiply(vector[index]));
        }
        return value;
    });
}

function innerProduct(left, right) {
    let value = C(0);

    for (let index = 0; index < left.length; index++) {
        value = value.add(
            left[index].conjugate().multiply(right[index])
        );
    }

    return value;
}

function kronecker(left, right) {
    const result = [];

    for (const leftRow of left) {
        for (const rightRow of right) {
            const row = [];

            for (const leftValue of leftRow) {
                for (const rightValue of rightRow) {
                    row.push(leftValue.multiply(rightValue));
                }
            }

            result.push(row);
        }
    }

    return result;
}

function observableExpectation(state, observable) {
    const transformed = matrixVectorMultiply(observable, state.amplitudes);
    const value = innerProduct(state.amplitudes, transformed);

    assert(
        Math.abs(value.im) < 1e-8,
        "Expected a real value from a Hermitian observable."
    );

    return value.re;
}

function normalizeState(amplitudes) {
    const norm = Math.sqrt(
        amplitudes.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        )
    );

    assert(norm > EPSILON, "A quantum state cannot have zero norm.");

    return amplitudes.map(
        amplitude => C(amplitude.re / norm, amplitude.im / norm)
    );
}

class TwoQubitState {
    constructor(amplitudes, name = "unnamed state") {
        assert(
            amplitudes.length === 4,
            "A two-qubit state requires four amplitudes."
        );

        this.amplitudes = normalizeState(amplitudes);
        this.name = name;
    }

    probabilities() {
        return Object.fromEntries(
            BASIS_LABELS.map((label, index) => [
                label,
                this.amplitudes[index].magnitudeSquared()
            ])
        );
    }

    measure(rng = Math.random) {
        const probabilities = BASIS_LABELS.map(
            (_, index) => this.amplitudes[index].magnitudeSquared()
        );

        const threshold = rng();
        let cumulative = 0;

        for (let index = 0; index < probabilities.length; index++) {
            cumulative += probabilities[index];

            if (threshold < cumulative) {
                return BASIS_LABELS[index];
            }
        }

        return BASIS_LABELS[BASIS_LABELS.length - 1];
    }

    sample(shots, rng = Math.random) {
        assert(
            Number.isInteger(shots) && shots > 0,
            "shots must be a positive integer."
        );

        const counts = Object.fromEntries(
            BASIS_LABELS.map(label => [label, 0])
        );

        for (let index = 0; index < shots; index++) {
            counts[this.measure(rng)]++;
        }

        return counts;
    }

    densityMatrix() {
        return this.amplitudes.map(rowAmplitude =>
            this.amplitudes.map(columnAmplitude =>
                rowAmplitude.multiply(columnAmplitude.conjugate())
            )
        );
    }

    reducedDensityMatrixOfSecondQubit() {
        /*
         * rho_B[j,k] = sum_i a_ij * conjugate(a_ik).
         * The summation removes the first subsystem from the joint state.
         */
        const rho = [
            [C(0), C(0)],
            [C(0), C(0)]
        ];

        for (let first = 0; first < 2; first++) {
            for (let row = 0; row < 2; row++) {
                const rowIndex = first * 2 + row;

                for (let column = 0; column < 2; column++) {
                    const columnIndex = first * 2 + column;

                    rho[row][column] = rho[row][column].add(
                        this.amplitudes[rowIndex].multiply(
                            this.amplitudes[columnIndex].conjugate()
                        )
                    );
                }
            }
        }

        return rho;
    }
}

function bellStates() {
    const inverseSqrtTwo = 1 / Math.sqrt(2);

    return {
        PhiPlus: new TwoQubitState(
            [C(inverseSqrtTwo), C(0), C(0), C(inverseSqrtTwo)],
            "|Phi+> = (|00> + |11>)/sqrt(2)"
        ),

        PhiMinus: new TwoQubitState(
            [C(inverseSqrtTwo), C(0), C(0), C(-inverseSqrtTwo)],
            "|Phi-> = (|00> - |11>)/sqrt(2)"
        ),

        PsiPlus: new TwoQubitState(
            [C(0), C(inverseSqrtTwo), C(inverseSqrtTwo), C(0)],
            "|Psi+> = (|01> + |10>)/sqrt(2)"
        ),

        PsiMinus: new TwoQubitState(
            [C(0), C(inverseSqrtTwo), C(-inverseSqrtTwo), C(0)],
            "|Psi-> = (|01> - |10>)/sqrt(2)"
        )
    };
}

const PAULI_X = [
    [C(0), C(1)],
    [C(1), C(0)]
];

const PAULI_Y = [
    [C(0), C(0, -1)],
    [C(0, 1), C(0)]
];

const PAULI_Z = [
    [C(1), C(0)],
    [C(0), C(-1)]
];

const HADAMARD = [
    [C(1 / Math.sqrt(2)), C(1 / Math.sqrt(2))],
    [C(1 / Math.sqrt(2)), C(-1 / Math.sqrt(2))]
];

function bellCorrelations(state) {
    return {
        XX: observableExpectation(state, kronecker(PAULI_X, PAULI_X)),
        YY: observableExpectation(state, kronecker(PAULI_Y, PAULI_Y)),
        ZZ: observableExpectation(state, kronecker(PAULI_Z, PAULI_Z))
    };
}

function rotateBasisObservable(thetaDegrees, phiDegrees = 0) {
    const theta = thetaDegrees * Math.PI / 180;
    const phi = phiDegrees * Math.PI / 180;

    const x = Math.sin(theta) * Math.cos(phi);
    const y = Math.sin(theta) * Math.sin(phi);
    const z = Math.cos(theta);

    return [
        [C(z), C(x, -y)],
        [C(x, y), C(-z)]
    ];
}

function chsh(state, axes) {
    const eAB = observableExpectation(
        state,
        kronecker(axes.a, axes.b)
    );

    const eABPrime = observableExpectation(
        state,
        kronecker(axes.a, axes.bPrime)
    );

    const eAPrimeB = observableExpectation(
        state,
        kronecker(axes.aPrime, axes.b)
    );

    const eAPrimeBPrime = observableExpectation(
        state,
        kronecker(axes.aPrime, axes.bPrime)
    );

    return {
        correlations: {
            "E(a,b)": eAB,
            "E(a,b')": eABPrime,
            "E(a',b)": eAPrimeB,
            "E(a',b')": eAPrimeBPrime
        },
        S: eAB + eABPrime + eAPrimeB - eAPrimeBPrime
    };
}

function entropyOfDiagonalQubitState(rho) {
    const eigenvalues = [
        Math.max(0, rho[0][0].re),
        Math.max(0, rho[1][1].re)
    ];

    return eigenvalues.reduce((entropy, probability) => {
        if (probability <= EPSILON) {
            return entropy;
        }

        return entropy - probability * Math.log2(probability);
    }, 0);
}

function printStateDetails(name, state) {
    console.log(`\n${name}`);
    console.log(`  ${state.name}`);

    const probabilities = state.probabilities();

    for (const label of BASIS_LABELS) {
        console.log(
            `  P(${label}) = ${probabilities[label].toFixed(6)}`
        );
    }

    console.log("  Correlations:", bellCorrelations(state));
}

function demonstrateBellStates() {
    console.log("=== Bell-state catalogue ===");

    const states = bellStates();

    for (const [name, state] of Object.entries(states)) {
        printStateDetails(name, state);
    }
}

function demonstrateLocalMixedness() {
    console.log("\n=== Local state of an entangled pair ===");

    const state = bellStates().PhiPlus;
    const rho = state.reducedDensityMatrixOfSecondQubit();

    console.log("Reduced density matrix of qubit B:");

    for (const row of rho) {
        console.log(
            "  ",
            row.map(value => value.toString()).join("    ")
        );
    }

    console.log(
        `Local diagonal entropy: ${entropyOfDiagonalQubitState(rho).toFixed(6)} bits`
    );

    console.log(
        "The subsystem has locally random statistics even though the joint state "
        + "contains strong correlations."
    );
}

function demonstrateRelativePhase() {
    console.log("\n=== Relative phase and observable correlations ===");

    const states = bellStates();

    for (const name of ["PhiPlus", "PhiMinus"]) {
        const state = states[name];

        console.log(
            `${name}:`,
            bellCorrelations(state)
        );
    }

    console.log(
        "Phi+ and Phi- have the same Z-basis outcome probabilities, "
        + "but their XX and YY correlations differ because of relative phase."
    );
}

function createMeasurementStream(state, totalShots, delayMs = 5) {
    /*
     * JavaScript's event-driven model makes an asynchronous measurement stream
     * useful for representing a sequence of experimental observations.
     * setTimeout yields control back to the event loop between measurements.
     */
    let completed = 0;

    return new Promise(resolve => {
        const counts = Object.fromEntries(
            BASIS_LABELS.map(label => [label, 0])
        );

        const emitMeasurement = () => {
            if (completed >= totalShots) {
                resolve(counts);
                return;
            }

            const outcome = state.measure();
            counts[outcome]++;
            completed++;

            setTimeout(emitMeasurement, delayMs);
        };

        emitMeasurement();
    });
}

async function demonstrateEventDrivenMeasurement() {
    console.log("\n=== Event-driven Bell-state measurements ===");

    const state = bellStates().PhiPlus;
    const shots = 200;

    const counts = await createMeasurementStream(state, shots, 1);

    console.log(`Asynchronously collected ${shots} measurements.`);

    for (const label of BASIS_LABELS) {
        console.log(`  ${label}: ${counts[label]}`);
    }

    const disagreementRate =
        (counts["01"] + counts["10"]) / shots;

    console.log(
        `Disagreement rate for Phi+ in Z basis: ${disagreementRate.toFixed(4)}`
    );
}

function demonstrateCHSH() {
    console.log("\n=== CHSH correlation calculation ===");

    const state = bellStates().PhiPlus;

    const axes = {
        a: rotateBasisObservable(0),
        aPrime: rotateBasisObservable(90),
        b: rotateBasisObservable(45),
        bPrime: rotateBasisObservable(-45)
    };

    const result = chsh(state, axes);

    for (const [label, value] of Object.entries(result.correlations)) {
        console.log(`  ${label} = ${value.toFixed(6)}`);
    }

    console.log(`  CHSH S = ${result.S.toFixed(6)}`);
    console.log("  Classical CHSH bound: |S| <= 2");
    console.log(
        `  Quantum Tsirelson bound: |S| <= ${(2 * Math.sqrt(2)).toFixed(6)}`
    );
}

function demonstrateHadamardMechanism() {
    console.log("\n=== Hadamard transformation and superposition ===");

    /*
     * Starting with |00>, applying H to the first qubit creates
     * (|00> + |10>)/sqrt(2). This is still separable. Entanglement requires
     * an interaction or an equivalent multi-qubit operation after the
     * superposition is created.
     */
    const initial = new TwoQubitState(
        [C(1), C(0), C(0), C(0)],
        "|00>"
    );

    const transformed = initial.amplitudes.map(() => C(0));

    for (let inputIndex = 0; inputIndex < 4; inputIndex++) {
        const firstBit = (inputIndex >> 1) & 1;
        const secondBit = inputIndex & 1;

        for (let outputBit = 0; outputBit < 2; outputBit++) {
            const outputIndex = outputBit * 2 + secondBit;

            transformed[outputIndex] = transformed[outputIndex].add(
                HADAMARD[outputBit][firstBit].multiply(
                    initial.amplitudes[inputIndex]
                )
            );
        }
    }

    const superposition = new TwoQubitState(
        transformed,
        "H on first qubit applied to |00>"
    );

    console.log(superposition.name);
    console.log(superposition.probabilities());

    console.log(
        "The result is a superposition but not yet an entangled state."
    );
}

async function main() {
    console.log("Entanglement: Bell States and Non-Classical Correlations");
    console.log("=".repeat(58));

    demonstrateHadamardMechanism();
    demonstrateBellStates();
    demonstrateLocalMixedness();
    demonstrateRelativePhase();
    demonstrateCHSH();
    await demonstrateEventDrivenMeasurement();

    console.log("\n=== Completed ===");
    console.log(
        "The program connects Bell-state amplitudes, measurement statistics, "
        + "relative phase, reduced states, event-driven sampling, and CHSH correlations."
    );
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
