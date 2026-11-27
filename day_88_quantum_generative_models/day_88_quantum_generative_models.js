"use strict";

/*
 * Quantum Generative Models
 * Event-driven quantum generative learning with Node.js.
 *
 * Features:
 * - Complex statevector simulation
 * - Parameterized quantum circuits
 * - Born probability distributions
 * - SPSA optimization
 * - Measurement sampling
 * - KL divergence and total variation evaluation
 * - Asynchronous experiment events
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class ValidationError extends Error {}
class QuantumExecutionError extends Error {}

const ExperimentState = Object.freeze({
    CREATED: "CREATED",
    RUNNING: "RUNNING",
    COMPLETED: "COMPLETED",
    FAILED: "FAILED"
});

function assertFinite(value, name) {
    if (!Number.isFinite(value)) {
        throw new ValidationError(`${name} must be finite.`);
    }
}

function validateDistribution(distribution, dimension) {
    if (!Array.isArray(distribution) ||
        distribution.length !== dimension) {
        throw new ValidationError("Invalid distribution dimension.");
    }

    for (const probability of distribution) {
        assertFinite(probability, "Probability");

        if (probability < 0) {
            throw new ValidationError("Negative probability.");
        }
    }

    const total = distribution.reduce((a, b) => a + b, 0);

    if (total <= 1e-12) {
        throw new ValidationError("Zero probability mass.");
    }

    return distribution.map(value => value / total);
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

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }
}

class RandomGenerator {
    constructor(seed = 42) {
        this.state = seed >>> 0;
    }

    next() {
        this.state = (
            1664525 * this.state + 1013904223
        ) >>> 0;

        return this.state / 4294967296;
    }

    sign() {
        return this.next() < 0.5 ? -1 : 1;
    }
}

class QuantumCircuit {
    constructor(qubits) {
        if (!Number.isInteger(qubits) ||
            qubits < 1 || qubits > 12) {
            throw new ValidationError("Qubits must be between 1 and 12.");
        }

        this.qubits = qubits;
        this.dimension = 2 ** qubits;
    }

    applyRY(state, qubit, theta) {
        const mask = 1 << (this.qubits - 1 - qubit);
        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        for (let i = 0; i < this.dimension; i++) {
            if ((i & mask) !== 0) continue;

            const j = i | mask;
            const a = state[i];
            const b = state[j];

            state[i] = new Complex(
                c * a.re - s * b.re,
                c * a.im - s * b.im
            );

            state[j] = new Complex(
                s * a.re + c * b.re,
                s * a.im + c * b.im
            );
        }
    }

    applyCNOT(state, control, target) {
        if (control === target ||
            control < 0 || target < 0 ||
            control >= this.qubits ||
            target >= this.qubits) {
            throw new ValidationError("Invalid CNOT operation.");
        }

        const controlMask = 1 << (this.qubits - 1 - control);
        const targetMask = 1 << (this.qubits - 1 - target);

        for (let i = 0; i < this.dimension; i++) {
            if ((i & controlMask) !== 0 &&
                (i & targetMask) === 0) {
                const j = i | targetMask;
                [state[i], state[j]] = [state[j], state[i]];
            }
        }
    }

    execute(parameters) {
        if (!Array.isArray(parameters) ||
            parameters.length !== 2 * this.qubits) {
            throw new ValidationError("Incorrect parameter count.");
        }

        parameters.forEach((value, i) =>
            assertFinite(value, `Parameter ${i}`)
        );

        const state = Array.from(
            { length: this.dimension },
            () => new Complex()
        );

        state[0] = new Complex(1, 0);

        for (let q = 0; q < this.qubits; q++) {
            this.applyRY(state, q, parameters[q]);
        }

        for (let q = 0; q < this.qubits - 1; q++) {
            this.applyCNOT(state, q, q + 1);
        }

        for (let q = 0; q < this.qubits; q++) {
            this.applyRY(
                state,
                q,
                parameters[this.qubits + q]
            );
        }

        const probabilities = state.map(
            amplitude => amplitude.magnitudeSquared()
        );

        const total = probabilities.reduce((a, b) => a + b, 0);

        if (!Number.isFinite(total) || total <= 1e-12) {
            throw new QuantumExecutionError("State normalization failed.");
        }

        return probabilities.map(value => value / total);
    }
}

class BornMachine {
    constructor({
        qubits = 2,
        learningRate = 0.08,
        seed = 42
    } = {}) {
        this.circuit = new QuantumCircuit(qubits);
        this.learningRate = learningRate;
        this.random = new RandomGenerator(seed);
        this.parameters = Array.from(
            { length: 2 * qubits },
            () => this.random.next() * 1.6 - 0.8
        );
        this.history = [];
    }

    probabilities() {
        return this.circuit.execute(this.parameters);
    }

    static klDivergence(target, generated) {
        if (target.length !== generated.length) {
            throw new ValidationError("Dimension mismatch.");
        }

        return target.reduce((loss, p, i) => {
            if (p === 0) return loss;

            return loss + p * Math.log(
                p / Math.max(generated[i], 1e-12)
            );
        }, 0);
    }

    static totalVariation(target, generated) {
        return 0.5 * target.reduce(
            (total, p, i) => total + Math.abs(p - generated[i]),
            0
        );
    }

    loss(target) {
        return BornMachine.klDivergence(
            target,
            this.probabilities()
        );
    }

    async train(target, {
        iterations = 300,
        signal = null
    } = {}) {
        const dimension = this.circuit.dimension;

        target = validateDistribution(target, dimension);

        if (!Number.isInteger(iterations) || iterations <= 0) {
            throw new ValidationError("Invalid iteration count.");
        }

        this.history = [];

        const alpha = 0.602;
        const gamma = 0.101;
        const parameterCount = this.parameters.length;

        for (let iteration = 0; iteration < iterations; iteration++) {
            if (signal?.aborted) {
                throw new QuantumExecutionError("Training aborted.");
            }

            const ak = this.learningRate /
                Math.pow(iteration + 11, alpha);

            const ck = 0.12 /
                Math.pow(iteration + 1, gamma);

            const original = [...this.parameters];

            const perturbation = original.map(
                () => this.random.sign()
            );

            this.parameters = original.map(
                (value, i) => value + ck * perturbation[i]
            );

            const plus = this.loss(target);

            this.parameters = original.map(
                (value, i) => value - ck * perturbation[i]
            );

            const minus = this.loss(target);

            const gradient = (plus - minus) / (2 * ck);

            this.parameters = original.map((value, i) => {
                const updated = value -
                    ak * gradient / perturbation[i];

                return ((updated + Math.PI) %
                    (2 * Math.PI) + 2 * Math.PI) %
                    (2 * Math.PI) - Math.PI;
            });

            const currentLoss = this.loss(target);

            if (!Number.isFinite(currentLoss)) {
                throw new QuantumExecutionError("Non-finite loss.");
            }

            const record = Object.freeze({
                iteration: iteration + 1,
                loss: currentLoss,
                learningRate: ak
            });

            this.history.push(record);

            // Yield periodically to keep the Node.js event loop responsive.
            if ((iteration + 1) % 20 === 0) {
                await new Promise(resolve => setImmediate(resolve));
            }
        }

        return this.history;
    }

    sample(shots = 5000) {
        if (!Number.isInteger(shots) || shots <= 0) {
            throw new ValidationError("Shots must be positive.");
        }

        const probabilities = this.probabilities();
        const cumulative = [];

        let total = 0;

        for (const probability of probabilities) {
            total += probability;
            cumulative.push(total);
        }

        const counts = new Map(
            probabilities.map((_, index) => [
                index.toString(2).padStart(
                    this.circuit.qubits, "0"
                ),
                0
            ])
        );

        for (let shot = 0; shot < shots; shot++) {
            const randomValue = this.random.next();

            const index = cumulative.findIndex(
                threshold => randomValue <= threshold
            );

            const selected = index < 0
                ? probabilities.length - 1
                : index;

            const key = selected.toString(2).padStart(
                this.circuit.qubits, "0"
            );

            counts.set(key, counts.get(key) + 1);
        }

        return Object.fromEntries(counts);
    }
}

class ExperimentManager extends EventEmitter {
    constructor(model, target) {
        super();

        this.model = model;
        this.target = validateDistribution(
            target,
            model.circuit.dimension
        );

        this.state = ExperimentState.CREATED;
        this.startedAt = null;
        this.completedAt = null;
    }

    async run(iterations = 300) {
        if (this.state !== ExperimentState.CREATED) {
            throw new Error("Experiment cannot be executed twice.");
        }

        this.state = ExperimentState.RUNNING;
        this.startedAt = new Date().toISOString();

        this.emit("started", {
            timestamp: this.startedAt
        });

        try {
            const initialLoss = this.model.loss(this.target);

            const history = await this.model.train(
                this.target,
                { iterations }
            );

            const probabilities = this.model.probabilities();

            const evaluation = {
                klDivergence: BornMachine.klDivergence(
                    this.target,
                    probabilities
                ),
                totalVariation: BornMachine.totalVariation(
                    this.target,
                    probabilities
                ),
                probabilities,
                target: this.target
            };

            this.state = ExperimentState.COMPLETED;
            this.completedAt = new Date().toISOString();

            const result = {
                status: this.state,
                initialLoss,
                finalLoss: evaluation.klDivergence,
                evaluation,
                history,
                samples: this.model.sample(),
                parameters: [...this.model.parameters],
                startedAt: this.startedAt,
                completedAt: this.completedAt
            };

            this.emit("completed", result);

            return result;

        } catch (error) {
            this.state = ExperimentState.FAILED;
            this.emit("failed", error);
            throw error;
        }
    }
}

async function main() {
    const target = [0.40, 0.10, 0.10, 0.40];

    const model = new BornMachine({
        qubits: 2,
        learningRate: 0.08,
        seed: 42
    });

    const manager = new ExperimentManager(model, target);

    manager.on("started", event => {
        console.log("Experiment started:", event.timestamp);
    });

    manager.on("completed", result => {
        console.log("Experiment completed.");
        console.log("Initial loss:", result.initialLoss.toFixed(6));
        console.log("Final loss:", result.finalLoss.toFixed(6));
        console.log("Total variation:",
            result.evaluation.totalVariation.toFixed(6));
    });

    manager.on("failed", error => {
        console.error("Experiment failed:", error.message);
    });

    try {
        const result = await manager.run(300);

        console.log("\nGenerated distribution:");

        result.evaluation.probabilities.forEach((p, i) => {
            console.log(
                `|${i.toString(2).padStart(2, "0")}>: ${p.toFixed(6)}`
            );
        });

        console.log("\nMeasurement counts:", result.samples);

        const output = {
            ...result,
            history: result.history
        };

        await fs.writeFile(
            "quantum_experiment_js.json",
            JSON.stringify(output, null, 2),
            { encoding: "utf8", mode: 0o600, flag: "w" }
        );

        console.log("Results saved to quantum_experiment_js.json");

    } catch (error) {
        process.exitCode = 1;
        console.error(error.stack);
    }
}

async function runTests() {
    const circuit = new QuantumCircuit(2);
    const zeroState = circuit.execute([0, 0, 0, 0]);

    if (Math.abs(zeroState[0] - 1) > 1e-10) {
        throw new Error("Zero-state test failed.");
    }

    const model = new BornMachine({ qubits: 2, seed: 7 });

    const target = [0.25, 0.25, 0.25, 0.25];

    await model.train(target, { iterations: 20 });

    const samples = model.sample(1000);

    const total = Object.values(samples).reduce(
        (a, b) => a + b,
        0
    );

    if (total !== 1000) {
        throw new Error("Measurement count test failed.");
    }

    try {
        validateDistribution([0.5, 0.5], 4);
        throw new Error("Invalid distribution was accepted.");
    } catch (error) {
        if (!(error instanceof ValidationError)) throw error;
    }

    console.log("All JavaScript tests passed.");
}

if (require.main === module) {
    (async () => {
        await main();
        await runTests();
    })();
}

module.exports = {
    Complex,
    QuantumCircuit,
    BornMachine,
    ExperimentManager,
    validateDistribution
};
