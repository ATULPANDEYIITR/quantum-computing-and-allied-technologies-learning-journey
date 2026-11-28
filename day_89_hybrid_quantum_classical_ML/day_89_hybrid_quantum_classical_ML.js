"use strict";

/*
 * Hybrid Quantum-Classical Machine Learning
 *
 * Node.js implementation featuring:
 * - Complex-valued quantum state simulation
 * - Parameterized quantum circuits
 * - Quantum feature extraction
 * - Classical optimization
 * - Event-driven experiment execution
 * - Asynchronous training
 * - Circuit measurement
 * - Validation and failure handling
 *
 * Runtime: Node.js 18+
 */

const fs = require("node:fs/promises");
const crypto = require("node:crypto");
const { performance } = require("node:perf_hooks");


class ValidationError extends Error {}
class CircuitError extends Error {}
class ExperimentError extends Error {}


const ModelState = Object.freeze({
    CREATED: "CREATED",
    TRAINING: "TRAINING",
    COMPLETED: "COMPLETED",
    FAILED: "FAILED"
});


function validateNumber(value, name) {
    if (!Number.isFinite(value)) {
        throw new ValidationError(`${name} must be finite`);
    }
}


function validateArray(values, expected, name) {
    if (!Array.isArray(values) || values.length !== expected) {
        throw new ValidationError(
            `${name} must contain exactly ${expected} elements`
        );
    }

    values.forEach(value => validateNumber(value, name));
}


function sigmoid(value) {
    const bounded = Math.max(-500, Math.min(500, value));
    return 1 / (1 + Math.exp(-bounded));
}


function randomGenerator(seed) {
    let state = seed >>> 0;

    return function next() {
        state += 0x6D2B79F5;

        let value = state;
        value = Math.imul(value ^ (value >>> 15), value | 1);
        value ^= value + Math.imul(value ^ (value >>> 7), value | 61);

        return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
    };
}


class Complex {
    constructor(re = 0, im = 0) {
        this.re = re;
        this.im = im;
    }

    add(other) {
        return new Complex(
            this.re + other.re,
            this.im + other.im
        );
    }

    multiply(other) {
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
}


class QuantumRegister {
    constructor(qubits) {
        if (!Number.isInteger(qubits) || qubits < 1 || qubits > 12) {
            throw new ValidationError("Qubits must be between 1 and 12");
        }

        this.qubits = qubits;
        this.dimension = 2 ** qubits;
        this.state = Array.from(
            { length: this.dimension },
            () => new Complex()
        );

        this.state[0] = new Complex(1, 0);
    }

    applyGate(qubit, matrix) {
        if (!Number.isInteger(qubit) ||
            qubit < 0 ||
            qubit >= this.qubits) {
            throw new CircuitError("Invalid qubit index");
        }

        const mask = 1 << qubit;

        for (let index = 0; index < this.dimension; index++) {
            if ((index & mask) !== 0) continue;

            const paired = index | mask;
            const a = this.state[index];
            const b = this.state[paired];

            this.state[index] = matrix[0][0].multiply(a)
                .add(matrix[0][1].multiply(b));

            this.state[paired] = matrix[1][0].multiply(a)
                .add(matrix[1][1].multiply(b));
        }
    }

    hadamard(qubit) {
        const c = 1 / Math.sqrt(2);

        this.applyGate(qubit, [
            [new Complex(c), new Complex(c)],
            [new Complex(c), new Complex(-c)]
        ]);
    }

    ry(qubit, theta) {
        validateNumber(theta, "theta");

        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        this.applyGate(qubit, [
            [new Complex(c), new Complex(-s)],
            [new Complex(s), new Complex(c)]
        ]);
    }

    rz(qubit, theta) {
        validateNumber(theta, "theta");

        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        this.applyGate(qubit, [
            [new Complex(c, -s), new Complex()],
            [new Complex(), new Complex(c, s)]
        ]);
    }

    cnot(control, target) {
        if (control === target ||
            control < 0 ||
            target < 0 ||
            control >= this.qubits ||
            target >= this.qubits) {
            throw new CircuitError("Invalid CNOT operands");
        }

        const cm = 1 << control;
        const tm = 1 << target;

        for (let index = 0; index < this.dimension; index++) {
            if ((index & cm) !== 0 && (index & tm) === 0) {
                const paired = index | tm;

                [this.state[index], this.state[paired]] =
                    [this.state[paired], this.state[index]];
            }
        }
    }

    expectationZ(qubit) {
        if (qubit < 0 || qubit >= this.qubits) {
            throw new CircuitError("Invalid measurement qubit");
        }

        const mask = 1 << qubit;
        let result = 0;

        for (let index = 0; index < this.dimension; index++) {
            const probability = this.state[index].magnitudeSquared();

            result += (index & mask) ? -probability : probability;
        }

        return result;
    }

    probabilities() {
        return this.state.map(amplitude => amplitude.magnitudeSquared());
    }

    sample(shots, random = Math.random) {
        if (!Number.isInteger(shots) || shots <= 0) {
            throw new ValidationError("Shots must be positive");
        }

        const probabilities = this.probabilities();
        const cumulative = [];

        let total = 0;

        for (const probability of probabilities) {
            total += probability;
            cumulative.push(total);
        }

        const counts = new Map();

        for (let shot = 0; shot < shots; shot++) {
            const value = random();
            let low = 0;
            let high = cumulative.length - 1;

            while (low < high) {
                const middle = Math.floor((low + high) / 2);

                if (value <= cumulative[middle]) {
                    high = middle;
                } else {
                    low = middle + 1;
                }
            }

            const bitstring = low.toString(2).padStart(this.qubits, "0");

            counts.set(bitstring, (counts.get(bitstring) || 0) + 1);
        }

        return counts;
    }
}


class QuantumFeatureExtractor {
    constructor(qubits = 2) {
        this.qubits = qubits;
    }

    extract(features) {
        validateArray(features, this.qubits, "Features");

        const register = new QuantumRegister(this.qubits);

        features.forEach((value, index) => {
            register.hadamard(index);
            register.ry(index, value);
            register.rz(index, value * value);
        });

        for (let index = 0; index < this.qubits - 1; index++) {
            register.cnot(index, index + 1);
        }

        return Array.from(
            { length: this.qubits },
            (_, index) => register.expectationZ(index)
        );
    }
}


class VariationalCircuit {
    constructor(qubits = 2) {
        this.qubits = qubits;
    }

    forward(features, parameters) {
        validateArray(features, this.qubits, "Features");
        validateArray(parameters, 2 * this.qubits, "Parameters");

        const register = new QuantumRegister(this.qubits);

        features.forEach((value, index) => {
            register.hadamard(index);
            register.ry(index, value);
        });

        for (let index = 0; index < this.qubits; index++) {
            register.ry(index, parameters[index]);
        }

        for (let index = 0; index < this.qubits - 1; index++) {
            register.cnot(index, index + 1);
        }

        for (let index = 0; index < this.qubits; index++) {
            register.rz(index, parameters[this.qubits + index]);
        }

        return Array.from(
            { length: this.qubits },
            (_, index) => register.expectationZ(index)
        );
    }
}


class ClassicalOptimizer {
    constructor(inputSize, learningRate, random) {
        this.weights = Array.from(
            { length: inputSize },
            () => (random() - 0.5) * 0.2
        );

        this.bias = 0;
        this.learningRate = learningRate;
    }

    probability(features) {
        validateArray(features, this.weights.length, "Classical features");

        const z = features.reduce(
            (sum, value, index) => sum + value * this.weights[index],
            this.bias
        );

        return sigmoid(z);
    }

    update(features, label) {
        const error = this.probability(features) - label;

        for (let index = 0; index < this.weights.length; index++) {
            this.weights[index] -=
                this.learningRate * error * features[index];
        }

        this.bias -= this.learningRate * error;
    }
}


class EventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(event, listener) {
        if (typeof listener !== "function") {
            throw new ValidationError("Listener must be a function");
        }

        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }

        this.listeners.get(event).add(listener);

        return () => this.listeners.get(event)?.delete(listener);
    }

    emit(event, payload) {
        for (const listener of this.listeners.get(event) || []) {
            listener(payload);
        }
    }
}


class HybridExperiment {
    constructor(options = {}) {
        const qubits = options.qubits ?? 2;
        const learningRate = options.learningRate ?? 0.03;

        if (!Number.isInteger(qubits) || qubits < 1 || qubits > 12) {
            throw new ValidationError("Invalid qubit count");
        }

        if (!Number.isFinite(learningRate) || learningRate <= 0) {
            throw new ValidationError("Invalid learning rate");
        }

        this.qubits = qubits;
        this.learningRate = learningRate;

        this.random = randomGenerator(options.seed ?? 42);
        this.circuit = new VariationalCircuit(qubits);

        this.parameters = Array.from(
            { length: 2 * qubits },
            () => (this.random() - 0.5) * 0.4
        );

        this.optimizer = new ClassicalOptimizer(
            qubits,
            learningRate,
            this.random
        );

        this.state = ModelState.CREATED;
        this.events = new EventBus();
        this.history = [];
    }

    loss(dataset) {
        let total = 0;

        for (const sample of dataset) {
            const output = this.circuit.forward(
                sample.features,
                this.parameters
            );

            const probability = Math.max(
                1e-12,
                Math.min(1 - 1e-12, this.optimizer.probability(output))
            );

            total -= sample.label * Math.log(probability)
                + (1 - sample.label) * Math.log(1 - probability);
        }

        return total / dataset.length;
    }

    parameterShift(dataset) {
        const gradients = [];
        const shift = Math.PI / 2;

        for (let index = 0; index < this.parameters.length; index++) {
            const original = this.parameters[index];

            this.parameters[index] = original + shift;
            const positive = this.loss(dataset);

            this.parameters[index] = original - shift;
            const negative = this.loss(dataset);

            this.parameters[index] = original;

            gradients.push((positive - negative) / 2);
        }

        return gradients;
    }

    async train(dataset, epochs = 30) {
        if (this.state !== ModelState.CREATED) {
            throw new ExperimentError("Experiment cannot be retrained");
        }

        if (!Array.isArray(dataset) || dataset.length === 0) {
            throw new ValidationError("Training data cannot be empty");
        }

        if (!Number.isInteger(epochs) || epochs <= 0) {
            throw new ValidationError("Epochs must be positive");
        }

        for (const sample of dataset) {
            validateArray(sample.features, this.qubits, "Sample features");

            if (sample.label !== 0 && sample.label !== 1) {
                throw new ValidationError("Labels must be binary");
            }
        }

        this.state = ModelState.TRAINING;
        this.events.emit("training-started", { epochs });

        try {
            for (let epoch = 0; epoch < epochs; epoch++) {
                const gradients = this.parameterShift(dataset);

                this.parameters = this.parameters.map(
                    (parameter, index) =>
                        parameter - this.learningRate * gradients[index]
                );

                for (const sample of dataset) {
                    const output = this.circuit.forward(
                        sample.features,
                        this.parameters
                    );

                    this.optimizer.update(output, sample.label);
                }

                const currentLoss = this.loss(dataset);

                if (!Number.isFinite(currentLoss)) {
                    throw new ExperimentError("Training diverged");
                }

                const record = Object.freeze({
                    epoch: epoch + 1,
                    loss: currentLoss
                });

                this.history.push(record);
                this.events.emit("epoch-completed", record);

                // Yield to the Node.js event loop.
                await new Promise(resolve => setImmediate(resolve));
            }

            this.state = ModelState.COMPLETED;

            this.events.emit("training-completed", {
                finalLoss: this.history.at(-1).loss
            });

        } catch (error) {
            this.state = ModelState.FAILED;
            this.events.emit("training-failed", {
                message: error.message
            });

            throw error;
        }
    }

    predictProbability(features) {
        if (this.state !== ModelState.COMPLETED) {
            throw new ExperimentError("Model is not trained");
        }

        return this.optimizer.probability(
            this.circuit.forward(features, this.parameters)
        );
    }

    predict(features) {
        return this.predictProbability(features) >= 0.5 ? 1 : 0;
    }

    evaluate(dataset) {
        if (!Array.isArray(dataset) || dataset.length === 0) {
            throw new ValidationError("Evaluation data cannot be empty");
        }

        let tp = 0;
        let tn = 0;
        let fp = 0;
        let fn = 0;

        for (const sample of dataset) {
            const predicted = this.predict(sample.features);

            if (predicted === 1 && sample.label === 1) tp++;
            else if (predicted === 0 && sample.label === 0) tn++;
            else if (predicted === 1) fp++;
            else fn++;
        }

        const precision = tp + fp ? tp / (tp + fp) : 0;
        const recall = tp + fn ? tp / (tp + fn) : 0;

        return Object.freeze({
            accuracy: (tp + tn) / dataset.length,
            precision,
            recall,
            f1: precision + recall
                ? 2 * precision * recall / (precision + recall)
                : 0,
            confusionMatrix: Object.freeze({ tp, tn, fp, fn })
        });
    }
}


function generateDataset(size = 120, seed = 42) {
    if (!Number.isInteger(size) || size < 20) {
        throw new ValidationError("Dataset size must be at least 20");
    }

    const random = randomGenerator(seed);

    const samples = Array.from({ length: size }, () => {
        const x = (random() * 2 - 1) * Math.PI;
        const y = (random() * 2 - 1) * Math.PI;

        return Object.freeze({
            features: Object.freeze([x, y]),
            label: Math.sin(x) * Math.cos(y) > 0 ? 1 : 0
        });
    });

    // Deterministic Fisher-Yates shuffle.
    for (let index = samples.length - 1; index > 0; index--) {
        const j = Math.floor(random() * (index + 1));
        [samples[index], samples[j]] = [samples[j], samples[index]];
    }

    return samples;
}


async function saveReport(report) {
    const filename = "hybrid_quantum_report.json";

    const contents = JSON.stringify(report, null, 2);

    await fs.writeFile(filename, contents, {
        encoding: "utf8",
        mode: 0o600,
        flag: "w"
    });

    return filename;
}


async function main() {
    const dataset = generateDataset(160);

    const split = Math.floor(dataset.length * 0.8);

    const training = dataset.slice(0, split);
    const testing = dataset.slice(split);

    const experiment = new HybridExperiment({
        qubits: 2,
        learningRate: 0.03,
        seed: 42
    });

    experiment.events.on("training-started", event => {
        process.stdout.write(`Training started: ${event.epochs} epochs\n`);
    });

    experiment.events.on("epoch-completed", event => {
        if (event.epoch % 10 === 0) {
            process.stdout.write(
                `Epoch ${event.epoch}: loss=${event.loss.toFixed(6)}\n`
            );
        }
    });

    experiment.events.on("training-completed", event => {
        process.stdout.write(
            `Training completed. Loss=${event.finalLoss.toFixed(6)}\n`
        );
    });

    const start = performance.now();

    await experiment.train(training, 40);

    const elapsed = performance.now() - start;
    const metrics = experiment.evaluate(testing);

    const report = {
        id: crypto.randomUUID(),
        experiment: "Hybrid Quantum-Classical Classification",
        runtime: "Node.js",
        qubits: experiment.qubits,
        trainingSamples: training.length,
        testingSamples: testing.length,
        executionMilliseconds: elapsed,
        finalLoss: experiment.history.at(-1).loss,
        metrics,
        history: experiment.history
    };

    const filename = await saveReport(report);

    console.log("\nEvaluation");
    console.log(JSON.stringify(metrics, null, 2));
    console.log(`Execution: ${elapsed.toFixed(2)} ms`);
    console.log(`Report saved: ${filename}`);

    const register = new QuantumRegister(2);
    register.hadamard(0);
    register.cnot(0, 1);

    console.log(
        "Bell-state measurement:",
        Object.fromEntries(register.sample(1000))
    );
}


main().catch(error => {
    console.error("Experiment failed:", error.message);
    process.exitCode = 1;
});
