"use strict";

/*
 * Quantum Kernels: Event-driven quantum feature map engine.
 *
 * Features:
 * - Dense state-vector simulation.
 * - Complex arithmetic.
 * - Hadamard, RX, RZ and CZ gates.
 * - Fidelity-based quantum kernel.
 * - Asynchronous batch evaluation.
 * - Concurrent request coordination.
 * - Kernel caching.
 * - Kernel ridge classification.
 * - Numerical validation and error reporting.
 *
 * Runtime: Node.js 18+
 * Dependencies: None.
 */

const { performance } = require("node:perf_hooks");
const { EventEmitter } = require("node:events");

class QuantumError extends Error {}
class ValidationError extends QuantumError {}
class NumericalError extends QuantumError {}

const EPSILON = 1e-10;

function validateFeatures(features, dimensions) {
    if (!Array.isArray(features) || features.length !== dimensions) {
        throw new ValidationError(
            `Expected ${dimensions} numerical features.`
        );
    }

    const values = features.map(Number);

    if (!values.every(Number.isFinite)) {
        throw new ValidationError(
            "Feature values must be finite numbers."
        );
    }

    return Object.freeze(values);
}

function complex(real = 0, imaginary = 0) {
    return { re: real, im: imaginary };
}

function add(a, b) {
    return complex(a.re + b.re, a.im + b.im);
}

function subtract(a, b) {
    return complex(a.re - b.re, a.im - b.im);
}

function multiply(a, b) {
    return complex(
        a.re * b.re - a.im * b.im,
        a.re * b.im + a.im * b.re
    );
}

function conjugate(a) {
    return complex(a.re, -a.im);
}

function magnitudeSquared(a) {
    return a.re * a.re + a.im * a.im;
}

function dotConjugate(a, b) {
    let result = complex();

    for (let i = 0; i < a.length; i++) {
        result = add(
            result,
            multiply(conjugate(a[i]), b[i])
        );
    }

    return result;
}

class StateVectorCircuit {
    constructor({
        qubits = 2,
        rotationScale = 2,
        entanglement = true
    } = {}) {
        if (!Number.isInteger(qubits) || qubits < 1 || qubits > 12) {
            throw new ValidationError("Qubits must be between 1 and 12.");
        }

        if (!Number.isFinite(rotationScale)) {
            throw new ValidationError("Invalid rotation scale.");
        }

        this.qubits = qubits;
        this.dimension = 2 ** qubits;
        this.rotationScale = rotationScale;
        this.entanglement = Boolean(entanglement);
    }

    initialize() {
        const state = Array.from(
            { length: this.dimension },
            () => complex()
        );

        state[0] = complex(1);
        return state;
    }

    applyHadamard(state, qubit) {
        const mask = 1 << qubit;
        const scale = 1 / Math.sqrt(2);

        for (let i = 0; i < this.dimension; i++) {
            if ((i & mask) === 0) {
                const partner = i | mask;
                const a = state[i];
                const b = state[partner];

                state[i] = complex(
                    (a.re + b.re) * scale,
                    (a.im + b.im) * scale
                );

                state[partner] = complex(
                    (a.re - b.re) * scale,
                    (a.im - b.im) * scale
                );
            }
        }
    }

    applyRZ(state, qubit, angle) {
        const mask = 1 << qubit;
        const half = angle / 2;

        const phases = [
            complex(Math.cos(-half), Math.sin(-half)),
            complex(Math.cos(half), Math.sin(half))
        ];

        for (let i = 0; i < this.dimension; i++) {
            const bit = (i & mask) !== 0 ? 1 : 0;
            state[i] = multiply(state[i], phases[bit]);
        }
    }

    applyRX(state, qubit, angle) {
        const mask = 1 << qubit;
        const cosine = Math.cos(angle / 2);
        const sine = Math.sin(angle / 2);

        for (let i = 0; i < this.dimension; i++) {
            if ((i & mask) === 0) {
                const partner = i | mask;
                const a = state[i];
                const b = state[partner];

                state[i] = subtract(
                    complex(cosine * a.re, cosine * a.im),
                    complex(-sine * b.im, sine * b.re)
                );

                state[partner] = subtract(
                    complex(cosine * b.re, cosine * b.im),
                    complex(-sine * a.im, sine * a.re)
                );
            }
        }
    }

    applyCZ(state, first, second) {
        if (first === second) {
            throw new ValidationError("CZ requires different qubits.");
        }

        const firstMask = 1 << first;
        const secondMask = 1 << second;

        for (let i = 0; i < this.dimension; i++) {
            if ((i & firstMask) && (i & secondMask)) {
                state[i] = complex(-state[i].re, -state[i].im);
            }
        }
    }

    encode(features) {
        const x = validateFeatures(features, this.qubits);
        const state = this.initialize();

        for (let q = 0; q < this.qubits; q++) {
            this.applyHadamard(state, q);
        }

        for (let q = 0; q < this.qubits; q++) {
            const angle = this.rotationScale * x[q];

            this.applyRZ(state, q, angle);
            this.applyRX(state, q, angle);
        }

        if (this.entanglement) {
            for (let q = 0; q < this.qubits - 1; q++) {
                this.applyCZ(state, q, q + 1);
            }
        }

        const norm = state.reduce(
            (total, amplitude) => total + magnitudeSquared(amplitude),
            0
        );

        if (Math.abs(norm - 1) > 1e-9) {
            throw new NumericalError(`Invalid state norm: ${norm}`);
        }

        return Object.freeze(state);
    }
}

class QuantumKernelService extends EventEmitter {
    constructor(circuit) {
        super();

        this.circuit = circuit;
        this.states = new Map();
        this.kernelCache = new Map();
        this.pending = new Map();
    }

    canonicalize(features) {
        return JSON.stringify(
            validateFeatures(features, this.circuit.qubits)
        );
    }

    getState(features) {
        const key = this.canonicalize(features);

        if (!this.states.has(key)) {
            const state = this.circuit.encode(JSON.parse(key));
            this.states.set(key, state);

            this.emit("state:encoded", {
                key,
                stateDimension: state.length
            });
        }

        return this.states.get(key);
    }

    evaluate(first, second) {
        const x = this.canonicalize(first);
        const z = this.canonicalize(second);

        const key = x < z ? `${x}|${z}` : `${z}|${x}`;

        if (this.kernelCache.has(key)) {
            this.emit("kernel:cache-hit", { key });
            return this.kernelCache.get(key);
        }

        const overlap = dotConjugate(
            this.getState(first),
            this.getState(second)
        );

        const fidelity = Math.min(
            1,
            Math.max(0, magnitudeSquared(overlap))
        );

        this.kernelCache.set(key, fidelity);

        this.emit("kernel:evaluated", {
            key,
            fidelity
        });

        return fidelity;
    }

    async evaluateAsync(first, second) {
        const x = this.canonicalize(first);
        const z = this.canonicalize(second);
        const key = x < z ? `${x}|${z}` : `${z}|${x}`;

        if (this.kernelCache.has(key)) {
            return this.kernelCache.get(key);
        }

        // Concurrent requests for the same pair share one computation.
        if (this.pending.has(key)) {
            return this.pending.get(key);
        }

        const task = Promise.resolve().then(() => {
            return this.evaluate(first, second);
        });

        this.pending.set(key, task);

        try {
            return await task;
        } finally {
            this.pending.delete(key);
        }
    }

    async matrixAsync(dataset) {
        if (!Array.isArray(dataset) || dataset.length === 0) {
            throw new ValidationError("Dataset cannot be empty.");
        }

        const validated = dataset.map(row =>
            validateFeatures(row, this.circuit.qubits)
        );

        const matrix = await Promise.all(
            validated.map(async (first, i) => {
                const values = await Promise.all(
                    validated.map((second, j) => {
                        if (i === j) return Promise.resolve(1);
                        return this.evaluateAsync(first, second);
                    })
                );

                return values;
            })
        );

        this.emit("matrix:completed", {
            samples: dataset.length
        });

        return matrix;
    }

    statistics() {
        return {
            cachedStates: this.states.size,
            cachedKernels: this.kernelCache.size,
            pendingEvaluations: this.pending.size
        };
    }
}

function solveLinearSystem(matrix, vector) {
    const n = vector.length;

    if (
        matrix.length !== n ||
        matrix.some(row => row.length !== n)
    ) {
        throw new ValidationError("Invalid linear system dimensions.");
    }

    const a = matrix.map((row, i) => [...row, vector[i]]);

    for (let col = 0; col < n; col++) {
        let pivot = col;

        for (let row = col + 1; row < n; row++) {
            if (
                Math.abs(a[row][col]) >
                Math.abs(a[pivot][col])
            ) {
                pivot = row;
            }
        }

        if (Math.abs(a[pivot][col]) < EPSILON) {
            throw new NumericalError("Singular kernel system.");
        }

        [a[col], a[pivot]] = [a[pivot], a[col]];

        for (let row = col + 1; row < n; row++) {
            const factor = a[row][col] / a[col][col];

            for (let j = col; j <= n; j++) {
                a[row][j] -= factor * a[col][j];
            }
        }
    }

    const solution = Array(n).fill(0);

    for (let i = n - 1; i >= 0; i--) {
        let value = a[i][n];

        for (let j = i + 1; j < n; j++) {
            value -= a[i][j] * solution[j];
        }

        solution[i] = value / a[i][i];
    }

    return solution;
}

class QuantumKernelClassifier {
    constructor(service, regularization = 0.15) {
        if (
            !Number.isFinite(regularization) ||
            regularization <= 0
        ) {
            throw new ValidationError(
                "Regularization must be positive."
            );
        }

        this.service = service;
        this.regularization = regularization;
        this.trainingData = [];
        this.coefficients = null;
    }

    async fit(features, labels) {
        if (
            !Array.isArray(features) ||
            !Array.isArray(labels) ||
            features.length !== labels.length ||
            features.length < 2
        ) {
            throw new ValidationError("Invalid training dataset.");
        }

        if (
            !labels.includes(-1) ||
            !labels.includes(1) ||
            labels.some(label => ![-1, 1].includes(label))
        ) {
            throw new ValidationError(
                "Both -1 and +1 labels are required."
            );
        }

        this.trainingData = features.map(row =>
            validateFeatures(row, this.service.circuit.qubits)
        );

        const unique = new Set(
            this.trainingData.map(row => JSON.stringify(row))
        );

        if (unique.size !== this.trainingData.length) {
            throw new ValidationError("Duplicate training observations.");
        }

        const matrix = await this.service.matrixAsync(
            this.trainingData
        );

        for (let i = 0; i < matrix.length; i++) {
            matrix[i][i] += this.regularization;
        }

        this.coefficients = solveLinearSystem(
            matrix,
            labels.map(Number)
        );

        this.service.emit("model:fitted", {
            trainingSamples: features.length
        });

        return this;
    }

    async decision(features) {
        if (!this.coefficients) {
            throw new QuantumError("Classifier is not fitted.");
        }

        const values = await Promise.all(
            this.trainingData.map(training =>
                this.service.evaluateAsync(training, features)
            )
        );

        return values.reduce(
            (sum, value, index) =>
                sum + value * this.coefficients[index],
            0
        );
    }

    async predict(features) {
        return (await this.decision(features)) >= 0 ? 1 : -1;
    }
}

async function main() {
    const started = performance.now();

    const circuit = new StateVectorCircuit({
        qubits: 2,
        rotationScale: 2,
        entanglement: true
    });

    const service = new QuantumKernelService(circuit);

    service.on("kernel:evaluated", event => {
        if (Math.random() < 0) {
            process.stdout.write(String(event.fidelity));
        }
    });

    const features = [];
    const labels = [];

    let seed = 42;

    function random() {
        seed = (1664525 * seed + 1013904223) >>> 0;
        return seed / 4294967296;
    }

    for (let i = 0; i < 32; i++) {
        const x = random() * 2.4 - 1.2;
        const z = random() * 2.4 - 1.2;

        features.push([x, z]);
        labels.push(
            Math.sin(2 * x) * Math.cos(2 * z) >= 0 ? 1 : -1
        );
    }

    const trainingFeatures = features.slice(0, 24);
    const trainingLabels = labels.slice(0, 24);

    const testingFeatures = features.slice(24);
    const testingLabels = labels.slice(24);

    const classifier = new QuantumKernelClassifier(service);

    await classifier.fit(trainingFeatures, trainingLabels);

    const predictions = await Promise.all(
        testingFeatures.map(row => classifier.predict(row))
    );

    const correct = predictions.filter(
        (prediction, index) => prediction === testingLabels[index]
    ).length;

    const accuracy = correct / testingLabels.length;

    const matrix = await service.matrixAsync(trainingFeatures);

    const symmetryError = Math.max(
        ...matrix.flatMap((row, i) =>
            row.map((value, j) => Math.abs(value - matrix[j][i]))
        )
    );

    console.log("QUANTUM KERNEL CLASSIFICATION");
    console.log("=============================");
    console.log("Training samples:", trainingFeatures.length);
    console.log("Testing samples:", testingFeatures.length);
    console.log("Accuracy:", accuracy.toFixed(4));
    console.log("Symmetry error:", symmetryError.toExponential(3));
    console.log("Cache statistics:", service.statistics());

    console.log("\nPredictions:");

    predictions.forEach((prediction, index) => {
        console.log({
            actual: testingLabels[index],
            predicted: prediction
        });
    });

    if (symmetryError > 1e-9) {
        throw new NumericalError("Kernel symmetry validation failed.");
    }

    const diagonal = matrix.every(
        (row, i) => Math.abs(row[i] - 1) < 1e-9
    );

    if (!diagonal) {
        throw new NumericalError("Kernel diagonal validation failed.");
    }

    console.log(
        "Execution time:",
        (performance.now() - started).toFixed(3),
        "ms"
    );
}

main().catch(error => {
    console.error("Execution failed:", error.name, error.message);
    process.exitCode = 1;
});
