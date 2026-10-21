"use strict";

/*
 * Quantum Fourier Transform fundamentals.
 *
 * This Node.js program models a quantum register as a normalized array of
 * complex amplitudes. It uses JavaScript's event-driven runtime to execute
 * several QFT analyses asynchronously and demonstrates:
 *
 * - direct QFT evaluation
 * - inverse QFT
 * - probability extraction
 * - measurement sampling
 * - periodic-state Fourier structure
 * - unitary verification
 * - comparison with a classical normalized DFT
 *
 * No npm dependencies are required.
 */

const EPSILON = 1e-10;

class Complex {
    constructor(real = 0, imaginary = 0) {
        if (!Number.isFinite(real) || !Number.isFinite(imaginary)) {
            throw new TypeError("Complex components must be finite numbers.");
        }

        this.re = real;
        this.im = imaginary;
    }

    add(other) {
        return new Complex(this.re + other.re, this.im + other.im);
    }

    subtract(other) {
        return new Complex(this.re - other.re, this.im - other.im);
    }

    multiply(other) {
        return new Complex(
            this.re * other.re - this.im * other.im,
            this.re * other.im + this.im * other.re
        );
    }

    scale(factor) {
        return new Complex(this.re * factor, this.im * factor);
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

    static fromPolar(radius, angle) {
        return new Complex(
            radius * Math.cos(angle),
            radius * Math.sin(angle)
        );
    }

    toString() {
        const real = Math.abs(this.re) < 5e-12 ? 0 : this.re;
        const imaginary = Math.abs(this.im) < 5e-12 ? 0 : this.im;

        if (imaginary === 0) {
            return real.toFixed(5);
        }

        if (real === 0) {
            return `${imaginary.toFixed(5)}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";
        return `${real.toFixed(5)} ${sign} ${Math.abs(imaginary).toFixed(5)}i`;
    }
}

function validateState(state) {
    if (!Array.isArray(state) || state.length === 0) {
        throw new TypeError("A quantum state must be a non-empty array.");
    }

    const dimension = state.length;

    if ((dimension & (dimension - 1)) !== 0) {
        throw new RangeError("State dimension must be a power of two.");
    }

    if (!state.every((amplitude) => amplitude instanceof Complex)) {
        throw new TypeError("Every state amplitude must be a Complex object.");
    }

    const normSquared = state.reduce(
        (sum, amplitude) => sum + amplitude.magnitudeSquared(),
        0
    );

    if (Math.abs(normSquared - 1) > EPSILON) {
        throw new RangeError(
            `State is not normalized. Squared norm = ${normSquared}.`
        );
    }
}

function normalize(state) {
    if (!Array.isArray(state) || state.length === 0) {
        throw new TypeError("Cannot normalize an empty vector.");
    }

    const norm = Math.sqrt(
        state.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        )
    );

    if (norm <= EPSILON) {
        throw new RangeError("Cannot normalize the zero vector.");
    }

    return state.map((amplitude) => amplitude.scale(1 / norm));
}

function basisState(qubits, index) {
    if (!Number.isInteger(qubits) || qubits < 1) {
        throw new RangeError("Qubit count must be a positive integer.");
    }

    const dimension = 2 ** qubits;

    if (!Number.isInteger(index) || index < 0 || index >= dimension) {
        throw new RangeError("Basis index is outside the register.");
    }

    const state = Array.from(
        { length: dimension },
        () => new Complex()
    );

    state[index] = new Complex(1);
    return state;
}

function qft(state, inverse = false) {
    validateState(state);

    const n = state.length;
    const sign = inverse ? -1 : 1;
    const scale = 1 / Math.sqrt(n);
    const result = [];

    for (let k = 0; k < n; k += 1) {
        let accumulator = new Complex();

        for (let j = 0; j < n; j += 1) {
            const angle = sign * 2 * Math.PI * j * k / n;
            const phase = Complex.fromPolar(1, angle);

            accumulator = accumulator.add(
                state[j].multiply(phase)
            );
        }

        result.push(accumulator.scale(scale));
    }

    return result;
}

function probabilities(state) {
    validateState(state);

    return state.map((amplitude) => amplitude.magnitudeSquared());
}

function classicalDft(state) {
    if (!Array.isArray(state) || state.length === 0) {
        throw new TypeError("DFT input must be non-empty.");
    }

    const n = state.length;

    return Array.from({ length: n }, (_, k) => {
        let accumulator = new Complex();

        for (let j = 0; j < n; j += 1) {
            const phase = Complex.fromPolar(
                1,
                2 * Math.PI * j * k / n
            );

            accumulator = accumulator.add(
                state[j].multiply(phase)
            );
        }

        return accumulator;
    });
}

function maxError(first, second) {
    if (first.length !== second.length) {
        throw new RangeError("Vectors must have equal lengths.");
    }

    return Math.max(
        0,
        ...first.map((value, index) =>
            value.subtract(second[index]).magnitude()
        )
    );
}

function qftMatrix(qubits) {
    if (!Number.isInteger(qubits) || qubits < 1) {
        throw new RangeError("Qubit count must be positive.");
    }

    const n = 2 ** qubits;
    const scale = 1 / Math.sqrt(n);

    return Array.from({ length: n }, (_, row) =>
        Array.from({ length: n }, (_, column) =>
            Complex.fromPolar(
                scale,
                2 * Math.PI * row * column / n
            )
        )
    );
}

function verifyUnitary(matrix) {
    const n = matrix.length;
    let maximumError = 0;

    for (let row = 0; row < n; row += 1) {
        for (let column = 0; column < n; column += 1) {
            let value = new Complex();

            for (let k = 0; k < n; k += 1) {
                value = value.add(
                    matrix[row][k]
                        .conjugate()
                        .multiply(matrix[column][k])
                );
            }

            const expected = row === column
                ? new Complex(1)
                : new Complex();

            maximumError = Math.max(
                maximumError,
                value.subtract(expected).magnitude()
            );
        }
    }

    return maximumError;
}

function sampleMeasurement(state, shots, random = Math.random) {
    validateState(state);

    if (!Number.isInteger(shots) || shots <= 0) {
        throw new RangeError("Shots must be a positive integer.");
    }

    const distribution = probabilities(state);
    const cumulative = [];
    let running = 0;

    for (const probability of distribution) {
        running += probability;
        cumulative.push(running);
    }

    const counts = Array(state.length).fill(0);

    for (let shot = 0; shot < shots; shot += 1) {
        const value = random();
        const index = cumulative.findIndex(
            (boundary) => value < boundary
        );

        counts[index === -1 ? counts.length - 1 : index] += 1;
    }

    return counts;
}

function printState(title, state) {
    console.log(title);

    const width = Math.max(1, Math.ceil(Math.log2(state.length)));

    state.forEach((amplitude, index) => {
        const binary = index.toString(2).padStart(width, "0");
        console.log(`  |${binary}>: ${amplitude}`);
    });
}

function printProbabilities(state) {
    console.log(
        probabilities(state).map(
            (value) => Number(value.toFixed(6))
        )
    );
}

function periodicState() {
    return normalize([
        new Complex(1),
        new Complex(),
        new Complex(),
        new Complex(),
        new Complex(1),
        new Complex(),
        new Complex(),
        new Complex()
    ]);
}

function createAnalysisJob(name, operation) {
    return new Promise((resolve, reject) => {
        setImmediate(() => {
            try {
                resolve({ name, value: operation() });
            } catch (error) {
                reject(new Error(`${name}: ${error.message}`));
            }
        });
    });
}

async function run() {
    console.log("Quantum Fourier Transform fundamentals");
    console.log("======================================");

    const jobs = [
        createAnalysisJob("unitarity", () => {
            const matrix = qftMatrix(3);
            return verifyUnitary(matrix);
        }),

        createAnalysisJob("basis-state transform", () => {
            const state = basisState(3, 1);
            return qft(state);
        }),

        createAnalysisJob("periodic transform", () => {
            return qft(periodicState());
        }),

        createAnalysisJob("inverse transform", () => {
            const state = normalize([
                new Complex(1, 1),
                new Complex(2, -1),
                new Complex(-1, 0.5),
                new Complex(0.25, -2)
            ]);

            const transformed = qft(state);
            const recovered = qft(transformed, true);

            return {
                error: maxError(state, recovered),
                recovered
            };
        })
    ];

    const results = await Promise.all(jobs);

    const unitaryError = results.find(
        (result) => result.name === "unitarity"
    ).value;

    console.log(`QFT matrix unitarity error: ${unitaryError.toExponential(3)}`);

    const basis = results.find(
        (result) => result.name === "basis-state transform"
    ).value;

    printState("\nQFT(|001>):", basis);
    console.log("Measurement probabilities:");
    printProbabilities(basis);

    const periodic = results.find(
        (result) => result.name === "periodic transform"
    ).value;

    console.log("\nQFT of a periodic eight-state input:");
    printState("Fourier amplitudes:", periodic);
    console.log("Measurement probabilities:");
    printProbabilities(periodic);

    const inverse = results.find(
        (result) => result.name === "inverse transform"
    ).value;

    console.log(
        `\nInverse-QFT reconstruction error: ${
            inverse.error.toExponential(3)
        }`
    );

    const comparisonState = normalize([
        new Complex(1),
        new Complex(2),
        new Complex(0, 1),
        new Complex(-1)
    ]);

    const quantumResult = qft(comparisonState);
    const classicalResult = classicalDft(comparisonState)
        .map((value) => value.scale(1 / Math.sqrt(comparisonState.length)));

    console.log(
        `Normalized DFT comparison error: ${
            maxError(quantumResult, classicalResult).toExponential(3)
        }`
    );

    const counts = sampleMeasurement(
        periodicState(),
        2000
    );

    console.log("\nSimulated measurements from the periodic state:");
    counts.forEach((count, index) => {
        console.log(`  |${index.toString(2).padStart(3, "0")}>: ${count}`);
    });

    if (unitaryError > 1e-9 || inverse.error > 1e-9) {
        throw new Error("Numerical QFT verification failed.");
    }

    console.log("\nAll QFT checks completed successfully.");
}

run().catch((error) => {
    console.error(`Execution failed: ${error.message}`);
    process.exitCode = 1;
});
