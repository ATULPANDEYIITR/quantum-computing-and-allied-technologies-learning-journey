"use strict";

/**
 * Variational Quantum Classifier
 *
 * Event-driven JavaScript implementation of a two-qubit VQC.
 *
 * Architecture:
 * - Real-valued state-vector simulation
 * - RY feature encoding
 * - CNOT entanglement
 * - Parameterized quantum ansatz
 * - Pauli-Z expectation measurement
 * - Parameter-shift optimization
 * - Asynchronous training events
 * - Evaluation and model serialization
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const EPSILON = 1e-10;
const PARAMETER_SHIFT = Math.PI / 2;

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class QuantumState {
    constructor() {
        this.reset();
    }

    reset() {
        this.amplitudes = [1, 0, 0, 0];
    }

    applyRY(qubit, theta) {
        if (![0, 1].includes(qubit) || !Number.isFinite(theta)) {
            throw new ValidationError("Invalid rotation.");
        }

        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);
        const mask = 1 << qubit;
        const next = [...this.amplitudes];

        for (let i = 0; i < 4; i++) {
            if ((i & mask) !== 0) continue;

            const j = i | mask;
            const a = this.amplitudes[i];
            const b = this.amplitudes[j];

            next[i] = c * a - s * b;
            next[j] = s * a + c * b;
        }

        this.amplitudes = next;
    }

    applyCNOT(control, target) {
        if (
            ![0, 1].includes(control) ||
            ![0, 1].includes(target) ||
            control === target
        ) {
            throw new ValidationError("Invalid CNOT configuration.");
        }

        const next = [0, 0, 0, 0];

        for (let i = 0; i < 4; i++) {
            let destination = i;

            if ((i & (1 << control)) !== 0) {
                destination ^= 1 << target;
            }

            next[destination] = this.amplitudes[i];
        }

        this.amplitudes = next;
    }

    expectationZ0() {
        const p0 = this.amplitudes[0] ** 2;
        const p1 = this.amplitudes[1] ** 2;
        const p2 = this.amplitudes[2] ** 2;
        const p3 = this.amplitudes[3] ** 2;

        return p0 + p2 - p1 - p3;
    }

    validate() {
        const norm = this.amplitudes.reduce(
            (sum, amplitude) => sum + amplitude ** 2,
            0
        );

        if (Math.abs(norm - 1) > 1e-8) {
            throw new Error(`Quantum state normalization error: ${norm}`);
        }
    }
}

class VQCCircuit {
    static evaluate(features, parameters) {
        if (
            !Array.isArray(features) ||
            features.length !== 2 ||
            !features.every(Number.isFinite)
        ) {
            throw new ValidationError("Exactly two finite features required.");
        }

        if (
            !Array.isArray(parameters) ||
            parameters.length !== 4 ||
            !parameters.every(Number.isFinite)
        ) {
            throw new ValidationError("Exactly four finite parameters required.");
        }

        const state = new QuantumState();

        // Data encoding.
        state.applyRY(0, features[0]);
        state.applyRY(1, features[1]);

        // First entangling layer.
        state.applyCNOT(0, 1);

        // Variational parameters.
        state.applyRY(0, parameters[0]);
        state.applyRY(1, parameters[1]);

        state.applyCNOT(0, 1);

        state.applyRY(0, parameters[2]);
        state.applyRY(1, parameters[3]);

        state.validate();

        return state.expectationZ0();
    }
}

class Dataset {
    constructor(samples) {
        if (!Array.isArray(samples) || samples.length < 2) {
            throw new ValidationError("Dataset requires at least two samples.");
        }

        this.samples = samples.map((sample, index) => {
            if (
                !Array.isArray(sample.features) ||
                sample.features.length !== 2 ||
                !sample.features.every(Number.isFinite) ||
                ![0, 1].includes(sample.label)
            ) {
                throw new ValidationError(`Invalid sample at index ${index}.`);
            }

            return Object.freeze({
                features: Object.freeze([...sample.features]),
                label: sample.label
            });
        });

        if (new Set(this.samples.map(s => s.label)).size !== 2) {
            throw new ValidationError("Both binary classes are required.");
        }

        Object.freeze(this.samples);
    }

    get length() {
        return this.samples.length;
    }

    [Symbol.iterator]() {
        return this.samples[Symbol.iterator]();
    }
}

class VQCTrainer extends EventEmitter {
    constructor({ learningRate = 0.08, epochs = 120, seed = 42 } = {}) {
        super();

        if (
            !Number.isFinite(learningRate) ||
            learningRate <= 0 ||
            learningRate > 1 ||
            !Number.isInteger(epochs) ||
            epochs <= 0
        ) {
            throw new ValidationError("Invalid training configuration.");
        }

        this.learningRate = learningRate;
        this.epochs = epochs;

        // Deterministic initialization.
        let state = seed >>> 0;

        const random = () => {
            state = (1664525 * state + 1013904223) >>> 0;
            return state / 4294967296;
        };

        this.parameters = Array.from(
            { length: 4 },
            () => random() - 0.5
        );

        this.history = [];
        this.training = false;
    }

    expectation(features, parameters = this.parameters) {
        return VQCCircuit.evaluate(features, parameters);
    }

    probability(features) {
        const expectation = this.expectation(features);
        return Math.min(
            1 - EPSILON,
            Math.max(EPSILON, (1 - expectation) / 2)
        );
    }

    predict(features) {
        return Number(this.probability(features) >= 0.5);
    }

    static loss(probability, label) {
        const p = Math.min(1 - EPSILON, Math.max(EPSILON, probability));
        return -(
            label * Math.log(p) +
            (1 - label) * Math.log(1 - p)
        );
    }

    gradient(sample) {
        const probability = this.probability(sample.features);

        const chainRule = (
            probability - sample.label
        ) / (probability * (1 - probability));

        return this.parameters.map((_, index) => {
            const plus = [...this.parameters];
            const minus = [...this.parameters];

            plus[index] += PARAMETER_SHIFT;
            minus[index] -= PARAMETER_SHIFT;

            const derivative = (
                this.expectation(sample.features, plus) -
                this.expectation(sample.features, minus)
            ) / 2;

            return chainRule * (-derivative / 2);
        });
    }

    async train(dataset) {
        if (!(dataset instanceof Dataset)) {
            throw new ValidationError("Expected a validated Dataset.");
        }

        if (this.training) {
            throw new Error("Training is already in progress.");
        }

        this.training = true;

        try {
            for (let epoch = 0; epoch < this.epochs; epoch++) {
                const gradient = [0, 0, 0, 0];
                let totalLoss = 0;

                for (const sample of dataset) {
                    const p = this.probability(sample.features);
                    totalLoss += VQCTrainer.loss(p, sample.label);

                    const currentGradient = this.gradient(sample);

                    currentGradient.forEach((value, index) => {
                        gradient[index] += value;
                    });
                }

                const averageLoss = totalLoss / dataset.length;

                const updated = this.parameters.map(
                    (parameter, index) =>
                        Math.max(
                            -4 * Math.PI,
                            Math.min(
                                4 * Math.PI,
                                parameter -
                                this.learningRate *
                                gradient[index] /
                                dataset.length
                            )
                        )
                );

                if (!Number.isFinite(averageLoss) ||
                    !updated.every(Number.isFinite)) {
                    throw new Error("Non-finite optimization state.");
                }

                this.parameters = updated;
                this.history.push(averageLoss);

                this.emit("epoch", {
                    epoch,
                    loss: averageLoss,
                    parameters: [...this.parameters]
                });

                // Yield control to the event loop.
                if (epoch % 10 === 0) {
                    await new Promise(resolve => setImmediate(resolve));
                }
            }

            this.emit("training-complete", {
                epochs: this.epochs,
                finalLoss: this.history.at(-1)
            });

            return this;
        } catch (error) {
            this.emit("training-error", error);
            throw error;
        } finally {
            this.training = false;
        }
    }

    evaluate(dataset) {
        if (!(dataset instanceof Dataset)) {
            throw new ValidationError("Expected a validated Dataset.");
        }

        let correct = 0;
        let totalLoss = 0;
        let tp = 0;
        let fp = 0;
        let tn = 0;
        let fn = 0;

        for (const sample of dataset) {
            const p = this.probability(sample.features);
            const predicted = Number(p >= 0.5);

            correct += Number(predicted === sample.label);
            totalLoss += VQCTrainer.loss(p, sample.label);

            if (predicted === 1 && sample.label === 1) tp++;
            else if (predicted === 1) fp++;
            else if (sample.label === 0) tn++;
            else fn++;
        }

        return {
            accuracy: correct / dataset.length,
            loss: totalLoss / dataset.length,
            precision: tp + fp ? tp / (tp + fp) : 0,
            recall: tp + fn ? tp / (tp + fn) : 0,
            confusionMatrix: { tp, fp, tn, fn }
        };
    }

    async save(filepath) {
        if (this.training) {
            throw new Error("Cannot save during an optimization update.");
        }

        const model = {
            version: 1,
            qubits: 2,
            parameters: this.parameters,
            history: this.history
        };

        await fs.writeFile(
            filepath,
            JSON.stringify(model, null, 2),
            { encoding: "utf8", mode: 0o600 }
        );
    }

    async load(filepath) {
        if (this.training) {
            throw new Error("Cannot load during training.");
        }

        const raw = await fs.readFile(filepath, "utf8");
        const model = JSON.parse(raw);

        if (
            model.version !== 1 ||
            model.qubits !== 2 ||
            !Array.isArray(model.parameters) ||
            model.parameters.length !== 4 ||
            !model.parameters.every(Number.isFinite)
        ) {
            throw new ValidationError("Invalid model file.");
        }

        this.parameters = [...model.parameters];
        this.history = Array.isArray(model.history)
            ? model.history.filter(Number.isFinite)
            : [];

        return this;
    }
}

async function main() {
    const dataset = new Dataset([
        { features: [0.15, 0.20], label: 0 },
        { features: [0.35, 0.25], label: 0 },
        { features: [0.20, 0.55], label: 0 },
        { features: [0.55, 0.30], label: 0 },
        { features: [0.40, 0.65], label: 0 },
        { features: [2.10, 2.00], label: 1 },
        { features: [2.40, 1.80], label: 1 },
        { features: [1.90, 2.45], label: 1 },
        { features: [2.65, 2.30], label: 1 },
        { features: [2.20, 2.70], label: 1 }
    ]);

    const trainer = new VQCTrainer({
        learningRate: 0.08,
        epochs: 120,
        seed: 42
    });

    trainer.on("epoch", ({ epoch, loss }) => {
        if (epoch % 20 === 0) {
            console.log(
                `Epoch ${epoch}: loss=${loss.toFixed(6)}`
            );
        }
    });

    trainer.on("training-complete", result => {
        console.log("\nTraining completed:", result);
    });

    trainer.on("training-error", error => {
        console.error("Training failure:", error.message);
    });

    const training = new Dataset(dataset.samples.slice(0, 4).concat(
        dataset.samples.slice(5, 9)
    ));

    const testing = new Dataset([
        dataset.samples[4],
        dataset.samples[9]
    ]);

    await trainer.train(training);

    console.log("\nTraining metrics:");
    console.log(trainer.evaluate(training));

    console.log("\nTesting metrics:");
    console.log(trainer.evaluate(testing));

    console.log("\nPredictions:");

    for (const sample of testing) {
        console.log({
            features: sample.features,
            actual: sample.label,
            predicted: trainer.predict(sample.features),
            probability: trainer.probability(sample.features)
        });
    }

    await trainer.save("vqc_model.json");

    const restored = new VQCTrainer();
    await restored.load("vqc_model.json");

    if (
        JSON.stringify(restored.parameters) !==
        JSON.stringify(trainer.parameters)
    ) {
        throw new Error("Model persistence verification failed.");
    }

    console.log("\nModel persistence verified.");
}

main().catch(error => {
    console.error(error.name, error.message);
    process.exitCode = 1;
});
