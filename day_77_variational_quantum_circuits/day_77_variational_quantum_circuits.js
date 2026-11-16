"use strict";

/*
 * Variational Quantum Circuits
 * Event-driven parameterized quantum computation.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 *
 * Features:
 * - Circuit construction and immutable parameter snapshots
 * - Parameterized rotation gates
 * - State-vector simulation
 * - Observable evaluation
 * - Parameter-shift gradient calculation
 * - Adam optimization
 * - Event-driven experiment execution
 * - Measurement sampling
 * - JSON experiment persistence
 */

const fs = require("node:fs/promises");
const crypto = require("node:crypto");
const EventEmitter = require("node:events");

// ============================================================
// 1. Domain definitions
// ============================================================

const ExperimentStatus = Object.freeze({
    CREATED: "CREATED",
    RUNNING: "RUNNING",
    COMPLETED: "COMPLETED",
    FAILED: "FAILED"
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class QuantumStateError extends Error {
    constructor(message) {
        super(message);
        this.name = "QuantumStateError";
    }
}

function validateFiniteNumber(value, name) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new ValidationError(`${name} must be finite.`);
    }
}

function validateQubit(qubit, count) {
    if (!Number.isInteger(qubit) || qubit < 0 || qubit >= count) {
        throw new ValidationError("Invalid qubit index.");
    }
}

// ============================================================
// 2. Complex arithmetic
// ============================================================

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
        return new Complex(
            this.re * value,
            this.im * value
        );
    }

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }
}

// ============================================================
// 3. Quantum state-vector engine
// ============================================================

class StateVector {

    constructor(numQubits) {
        if (!Number.isInteger(numQubits) ||
            numQubits < 1 ||
            numQubits > 12) {
            throw new ValidationError(
                "Qubit count must be between 1 and 12."
            );
        }

        this.numQubits = numQubits;
        this.dimension = 2 ** numQubits;

        this.amplitudes = Array.from(
            { length: this.dimension },
            () => new Complex()
        );

        this.amplitudes[0] = new Complex(1, 0);
    }

    applyRotation(qubit, theta, axis) {
        validateQubit(qubit, this.numQubits);
        validateFiniteNumber(theta, "Rotation angle");

        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        let a00, a01, a10, a11;

        if (axis === "RY") {
            a00 = new Complex(c);
            a01 = new Complex(-s);
            a10 = new Complex(s);
            a11 = new Complex(c);
        } else if (axis === "RX") {
            a00 = new Complex(c);
            a01 = new Complex(0, -s);
            a10 = new Complex(0, -s);
            a11 = new Complex(c);
        } else if (axis === "RZ") {
            a00 = new Complex(c, -s);
            a01 = new Complex();
            a10 = new Complex();
            a11 = new Complex(c, s);
        } else {
            throw new ValidationError("Unsupported rotation axis.");
        }

        const mask = 1 << qubit;

        for (let i = 0; i < this.dimension; i++) {
            if ((i & mask) !== 0) continue;

            const j = i | mask;

            const a = this.amplitudes[i];
            const b = this.amplitudes[j];

            this.amplitudes[i] = a00.multiply(a).add(
                a01.multiply(b)
            );

            this.amplitudes[j] = a10.multiply(a).add(
                a11.multiply(b)
            );
        }
    }

    applyCNOT(control, target) {
        validateQubit(control, this.numQubits);
        validateQubit(target, this.numQubits);

        if (control === target) {
            throw new ValidationError(
                "CNOT control and target must differ."
            );
        }

        const controlMask = 1 << control;
        const targetMask = 1 << target;

        for (let i = 0; i < this.dimension; i++) {
            if ((i & controlMask) !== 0 &&
                (i & targetMask) === 0) {

                const j = i | targetMask;

                [
                    this.amplitudes[i],
                    this.amplitudes[j]
                ] = [
                    this.amplitudes[j],
                    this.amplitudes[i]
                ];
            }
        }
    }

    probabilities() {
        return this.amplitudes.map(
            amplitude => amplitude.magnitudeSquared()
        );
    }

    expectationZ(qubit) {
        validateQubit(qubit, this.numQubits);

        const mask = 1 << qubit;

        return this.amplitudes.reduce((total, amplitude, index) => {
            const eigenvalue = (index & mask) === 0 ? 1 : -1;

            return total + eigenvalue * amplitude.magnitudeSquared();
        }, 0);
    }

    expectationZZ(first, second) {
        validateQubit(first, this.numQubits);
        validateQubit(second, this.numQubits);

        if (first === second) {
            throw new ValidationError(
                "ZZ observable requires distinct qubits."
            );
        }

        const firstMask = 1 << first;
        const secondMask = 1 << second;

        return this.amplitudes.reduce((total, amplitude, index) => {
            const a = (index & firstMask) ? 1 : -1;
            const b = (index & secondMask) ? 1 : -1;

            return total + a * b * amplitude.magnitudeSquared();
        }, 0);
    }
}

// ============================================================
// 4. Parameterized circuit builder
// ============================================================

class ParameterizedCircuit {

    constructor({ numQubits = 2, layers = 2 } = {}) {
        if (!Number.isInteger(layers) || layers < 1 || layers > 20) {
            throw new ValidationError("Invalid layer count.");
        }

        if (!Number.isInteger(numQubits) ||
            numQubits < 1 ||
            numQubits > 12) {
            throw new ValidationError("Invalid qubit count.");
        }

        this.numQubits = numQubits;
        this.layers = layers;
        this.parameterCount = numQubits * layers * 2;

        this.gates = [];

        let parameterIndex = 0;

        for (let layer = 0; layer < layers; layer++) {
            for (let qubit = 0; qubit < numQubits; qubit++) {
                this.gates.push({
                    type: "RY",
                    qubit,
                    parameterIndex: parameterIndex++
                });

                this.gates.push({
                    type: "RZ",
                    qubit,
                    parameterIndex: parameterIndex++
                });
            }

            for (let qubit = 0; qubit < numQubits - 1; qubit++) {
                this.gates.push({
                    type: "CNOT",
                    control: qubit,
                    target: qubit + 1
                });
            }

            if (numQubits > 2) {
                this.gates.push({
                    type: "CNOT",
                    control: numQubits - 1,
                    target: 0
                });
            }
        }

        Object.freeze(this.gates);
    }

    validate(parameters) {
        if (!Array.isArray(parameters) ||
            parameters.length !== this.parameterCount) {
            throw new ValidationError(
                `Expected ${this.parameterCount} parameters.`
            );
        }

        parameters.forEach(
            (value, index) => validateFiniteNumber(
                value,
                `Parameter ${index}`
            )
        );
    }

    execute(parameters) {
        this.validate(parameters);

        const state = new StateVector(this.numQubits);

        for (const gate of this.gates) {
            if (gate.type === "CNOT") {
                state.applyCNOT(gate.control, gate.target);
            } else {
                state.applyRotation(
                    gate.qubit,
                    parameters[gate.parameterIndex],
                    gate.type
                );
            }
        }

        return state;
    }

    evaluate(parameters) {
        const state = this.execute(parameters);

        let energy = 0;

        for (let qubit = 0; qubit < this.numQubits; qubit++) {
            energy -= state.expectationZ(qubit);
        }

        if (this.numQubits > 1) {
            energy += 0.5 * state.expectationZZ(0, 1);
        }

        return energy;
    }
}

// ============================================================
// 5. Parameter-shift gradient
// ============================================================

function parameterShiftGradient(circuit, parameters) {
    circuit.validate(parameters);

    const gradient = new Array(parameters.length);

    for (let i = 0; i < parameters.length; i++) {
        const plus = [...parameters];
        const minus = [...parameters];

        plus[i] += Math.PI / 2;
        minus[i] -= Math.PI / 2;

        gradient[i] = 0.5 * (
            circuit.evaluate(plus) -
            circuit.evaluate(minus)
        );
    }

    return gradient;
}

// ============================================================
// 6. Adam optimizer
// ============================================================

class AdamOptimizer {

    constructor({
        learningRate = 0.04,
        beta1 = 0.9,
        beta2 = 0.999,
        epsilon = 1e-8
    } = {}) {
        if (learningRate <= 0 ||
            beta1 <= 0 || beta1 >= 1 ||
            beta2 <= 0 || beta2 >= 1 ||
            epsilon <= 0) {
            throw new ValidationError("Invalid Adam configuration.");
        }

        this.learningRate = learningRate;
        this.beta1 = beta1;
        this.beta2 = beta2;
        this.epsilon = epsilon;
    }

    optimize(circuit, initialParameters, maxIterations = 150) {
        circuit.validate(initialParameters);

        if (!Number.isInteger(maxIterations) || maxIterations < 1) {
            throw new ValidationError("Invalid iteration count.");
        }

        let parameters = [...initialParameters];

        const firstMoment = parameters.map(() => 0);
        const secondMoment = parameters.map(() => 0);

        const history = [circuit.evaluate(parameters)];

        let converged = false;

        for (let iteration = 1;
             iteration <= maxIterations;
             iteration++) {

            const gradient = parameterShiftGradient(
                circuit,
                parameters
            );

            const gradientNorm = Math.sqrt(
                gradient.reduce(
                    (sum, value) => sum + value * value,
                    0
                )
            );

            if (gradientNorm < 1e-7) {
                converged = true;
                break;
            }

            const candidate = parameters.map((parameter, index) => {
                const g = gradient[index];

                firstMoment[index] =
                    this.beta1 * firstMoment[index] +
                    (1 - this.beta1) * g;

                secondMoment[index] =
                    this.beta2 * secondMoment[index] +
                    (1 - this.beta2) * g * g;

                const correctedFirst =
                    firstMoment[index] /
                    (1 - Math.pow(this.beta1, iteration));

                const correctedSecond =
                    secondMoment[index] /
                    (1 - Math.pow(this.beta2, iteration));

                return parameter -
                    this.learningRate *
                    correctedFirst /
                    (Math.sqrt(correctedSecond) + this.epsilon);
            });

            const candidateCost = circuit.evaluate(candidate);

            if (candidateCost > history[history.length - 1] + 1e-9) {
                // Reject an energy-increasing update.
                break;
            }

            parameters = candidate;
            history.push(candidateCost);

            if (Math.abs(
                history[history.length - 2] -
                history[history.length - 1]
            ) < 1e-8) {
                converged = true;
                break;
            }
        }

        return Object.freeze({
            initialCost: history[0],
            finalCost: circuit.evaluate(parameters),
            parameters: Object.freeze([...parameters]),
            iterations: history.length - 1,
            converged,
            history: Object.freeze([...history])
        });
    }
}

// ============================================================
// 7. Event-driven experiment controller
// ============================================================

class ExperimentController extends EventEmitter {

    constructor() {
        super();

        this.experiments = new Map();
    }

    create(circuit, parameters) {
        circuit.validate(parameters);

        const id = crypto.randomUUID();

        const experiment = {
            id,
            status: ExperimentStatus.CREATED,
            createdAt: new Date().toISOString(),
            startedAt: null,
            completedAt: null,
            configuration: {
                numQubits: circuit.numQubits,
                layers: circuit.layers,
                parameterCount: circuit.parameterCount
            },
            initialParameters: [...parameters],
            result: null,
            error: null
        };

        this.experiments.set(id, experiment);

        this.emit("experiment:created", { id });

        return id;
    }

    async run(id, circuit, optimizer) {
        const experiment = this.experiments.get(id);

        if (!experiment) {
            throw new ValidationError("Experiment not found.");
        }

        if (experiment.status !== ExperimentStatus.CREATED) {
            throw new ValidationError(
                "Experiment is not in a runnable state."
            );
        }

        experiment.status = ExperimentStatus.RUNNING;
        experiment.startedAt = new Date().toISOString();

        this.emit("experiment:started", { id });

        try {
            // Yield to the event loop before computation.
            await new Promise(resolve => setImmediate(resolve));

            const result = optimizer.optimize(
                circuit,
                experiment.initialParameters
            );

            const finalState = circuit.execute(result.parameters);

            experiment.result = {
                ...result,
                probabilities: finalState.probabilities()
            };

            experiment.status = ExperimentStatus.COMPLETED;
            experiment.completedAt = new Date().toISOString();

            this.emit("experiment:completed", {
                id,
                finalCost: result.finalCost
            });

            return experiment;

        } catch (error) {
            experiment.status = ExperimentStatus.FAILED;
            experiment.error = error.message;
            experiment.completedAt = new Date().toISOString();

            this.emit("experiment:failed", {
                id,
                error: error.message
            });

            throw error;
        }
    }

    async save(filename) {
        const records = Array.from(
            this.experiments.values()
        );

        const temporary = `${filename}.tmp`;

        await fs.writeFile(
            temporary,
            JSON.stringify(records, null, 2),
            { encoding: "utf8", flag: "w" }
        );

        await fs.rename(temporary, filename);
    }
}

// ============================================================
// 8. Deterministic measurement sampling
// ============================================================

function sampleMeasurements(probabilities, shots, seed = 42) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new ValidationError("Shots must be positive.");
    }

    const total = probabilities.reduce(
        (sum, value) => sum + value,
        0
    );

    if (Math.abs(total - 1) > 1e-8) {
        throw new QuantumStateError(
            "Probabilities must sum to one."
        );
    }

    // Small deterministic pseudo-random generator for reproducibility.
    let state = seed >>> 0;

    function random() {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 4294967296;
    }

    const counts = new Map();

    const cumulative = [];
    let running = 0;

    for (const probability of probabilities) {
        if (probability < 0 || !Number.isFinite(probability)) {
            throw new QuantumStateError("Invalid probability.");
        }

        running += probability;
        cumulative.push(running);
    }

    for (let shot = 0; shot < shots; shot++) {
        const value = random();

        let low = 0;
        let high = cumulative.length - 1;

        while (low < high) {
            const middle = Math.floor((low + high) / 2);

            if (cumulative[middle] < value) {
                low = middle + 1;
            } else {
                high = middle;
            }
        }

        const bitstring = low.toString(2).padStart(
            Math.log2(probabilities.length),
            "0"
        );

        counts.set(
            bitstring,
            (counts.get(bitstring) || 0) + 1
        );
    }

    return Object.fromEntries(counts);
}

// ============================================================
// 9. Verification
// ============================================================

function verifyStateVector() {
    const state = new StateVector(2);

    state.applyRotation(0, Math.PI / 2, "RY");
    state.applyCNOT(0, 1);

    const probabilities = state.probabilities();

    if (Math.abs(probabilities[0] - 0.5) > 1e-9 ||
        Math.abs(probabilities[3] - 0.5) > 1e-9) {
        throw new Error("Bell-state verification failed.");
    }

    if (Math.abs(state.expectationZZ(0, 1) - 1) > 1e-9) {
        throw new Error("Entanglement observable verification failed.");
    }
}

function verifyGradient(circuit, parameters) {
    const gradient = parameterShiftGradient(
        circuit,
        parameters
    );

    const epsilon = 1e-6;

    for (let i = 0; i < parameters.length; i++) {
        const plus = [...parameters];
        const minus = [...parameters];

        plus[i] += epsilon;
        minus[i] -= epsilon;

        const numerical = (
            circuit.evaluate(plus) -
            circuit.evaluate(minus)
        ) / (2 * epsilon);

        if (Math.abs(numerical - gradient[i]) > 1e-5) {
            throw new Error(`Gradient mismatch at index ${i}.`);
        }
    }
}

// ============================================================
// 10. Main application
// ============================================================

async function main() {
    verifyStateVector();

    const circuit = new ParameterizedCircuit({
        numQubits: 2,
        layers: 2
    });

    const parameters = Array.from(
        { length: circuit.parameterCount },
        (_, index) => 0.25 * Math.sin(index + 1)
    );

    verifyGradient(circuit, parameters);

    const controller = new ExperimentController();

    controller.on("experiment:created", event => {
        console.log("Created:", event.id);
    });

    controller.on("experiment:started", event => {
        console.log("Started:", event.id);
    });

    controller.on("experiment:completed", event => {
        console.log("Completed:", event.id);
        console.log("Final energy:", event.finalCost.toFixed(8));
    });

    controller.on("experiment:failed", event => {
        console.error("Experiment failed:", event.error);
    });

    const optimizer = new AdamOptimizer({
        learningRate: 0.04
    });

    const id = controller.create(circuit, parameters);

    const experiment = await controller.run(
        id,
        circuit,
        optimizer
    );

    const measurements = sampleMeasurements(
        experiment.result.probabilities,
        1000,
        42
    );

    console.log("\nOPTIMIZATION RESULTS");
    console.log("Initial energy:", experiment.result.initialCost);
    console.log("Final energy:", experiment.result.finalCost);
    console.log("Iterations:", experiment.result.iterations);
    console.log("Converged:", experiment.result.converged);

    console.log("\nMEASUREMENTS");
    console.log(measurements);

    await controller.save("vqc_experiments_js.json");

    console.log("\nExperiment saved successfully.");
}

main().catch(error => {
    console.error("Execution error:", error.message);
    process.exitCode = 1;
});
