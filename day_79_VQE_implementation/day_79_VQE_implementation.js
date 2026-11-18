"use strict";

/*
 * Variational Quantum Eigensolver: Event-driven implementation.
 *
 * Molecular system: Reduced two-qubit H2 Hamiltonian.
 * Runtime: Node.js 18+
 *
 * Features:
 * - Complex statevector simulation.
 * - Parameterized quantum circuits.
 * - Pauli Hamiltonian expectation values.
 * - Parameter-shift gradients.
 * - Adam optimizer.
 * - Asynchronous experiment execution.
 * - Abort handling.
 * - Measurement sampling.
 * - JSON experiment persistence.
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

const PI = Math.PI;
const EPSILON = 1e-8;

class VQEError extends Error {
    constructor(message) {
        super(message);
        this.name = "VQEError";
    }
}

function assertFinite(value, label) {
    if (!Number.isFinite(value)) {
        throw new VQEError(`${label} must be finite.`);
    }
}

function validateParameters(parameters, expected = 2) {
    if (!Array.isArray(parameters) || parameters.length !== expected) {
        throw new VQEError(`Expected ${expected} circuit parameters.`);
    }

    parameters.forEach((value, index) =>
        assertFinite(value, `Parameter ${index}`)
    );
}

// Complex numbers are represented as [real, imaginary].
const C = {
    add: (a, b) => [a[0] + b[0], a[1] + b[1]],
    multiply: (a, b) => [
        a[0] * b[0] - a[1] * b[1],
        a[0] * b[1] + a[1] * b[0]
    ],
    conjugate: a => [a[0], -a[1]],
    magnitudeSquared: a => a[0] ** 2 + a[1] ** 2
};

class QuantumState {
    constructor(amplitudes) {
        this.amplitudes = amplitudes.map(a => [...a]);
        this.normalize();
    }

    normalize() {
        const norm = Math.sqrt(
            this.amplitudes.reduce(
                (sum, a) => sum + C.magnitudeSquared(a),
                0
            )
        );

        if (norm < EPSILON || !Number.isFinite(norm)) {
            throw new VQEError("Invalid quantum state norm.");
        }

        this.amplitudes = this.amplitudes.map(
            a => [a[0] / norm, a[1] / norm]
        );

        return this;
    }

    static zero() {
        return new QuantumState([
            [1, 0],
            [0, 0],
            [0, 0],
            [0, 0]
        ]);
    }

    applyRY(theta, qubit) {
        assertFinite(theta, "Rotation angle");

        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        const output = this.amplitudes.map(a => [...a]);

        for (let i = 0; i < 4; i++) {
            const bit = (i >> (1 - qubit)) & 1;

            if (bit !== 0) continue;

            const j = i | (1 << (1 - qubit));

            const a = this.amplitudes[i];
            const b = this.amplitudes[j];

            output[i] = [
                c * a[0] - s * b[0],
                c * a[1] - s * b[1]
            ];

            output[j] = [
                s * a[0] + c * b[0],
                s * a[1] + c * b[1]
            ];
        }

        this.amplitudes = output;
        return this;
    }

    applyCNOT(control, target) {
        if (control === target) {
            throw new VQEError("CNOT control and target must differ.");
        }

        const output = Array.from(
            { length: 4 },
            () => [0, 0]
        );

        for (let i = 0; i < 4; i++) {
            let destination = i;

            const controlBit = (i >> (1 - control)) & 1;

            if (controlBit === 1) {
                destination ^= 1 << (1 - target);
            }

            output[destination] = [...this.amplitudes[i]];
        }

        this.amplitudes = output;
        return this;
    }
}

// Pauli strings use the same left-to-right convention as the
// mathematical tensor product: first character acts on qubit 0.
const PAULI = {
    I: [[1, 0], [0, 1]],
    X: [[0, 0], [1, 0]],
    Y: [[0, -1], [1, 0]],
    Z: [[1, 0], [0, -1]]
};

class MolecularHamiltonian {
    constructor(terms) {
        if (!Array.isArray(terms) || terms.length === 0) {
            throw new VQEError("Hamiltonian cannot be empty.");
        }

        this.terms = terms.map(term => {
            if (
                !Number.isFinite(term.coefficient) ||
                typeof term.pauli !== "string" ||
                !/^[IXYZ]{2}$/.test(term.pauli)
            ) {
                throw new VQEError("Invalid Pauli Hamiltonian term.");
            }

            return Object.freeze({
                coefficient: term.coefficient,
                pauli: term.pauli
            });
        });

        Object.freeze(this.terms);
    }

    applyPauli(state, pauli) {
        const output = Array.from(
            { length: 4 },
            () => [0, 0]
        );

        for (let index = 0; index < 4; index++) {
            let destination = index;
            let phase = [1, 0];

            for (let qubit = 0; qubit < 2; qubit++) {
                const symbol = pauli[qubit];
                const bit = (index >> (1 - qubit)) & 1;

                if (symbol === "X") {
                    destination ^= 1 << (1 - qubit);
                } else if (symbol === "Y") {
                    phase = C.multiply(
                        phase,
                        bit === 0 ? [0, 1] : [0, -1]
                    );
                    destination ^= 1 << (1 - qubit);
                } else if (symbol === "Z" && bit === 1) {
                    phase = [-phase[0], -phase[1]];
                }
            }

            output[destination] = C.multiply(
                phase,
                state.amplitudes[index]
            );
        }

        return output;
    }

    energy(state) {
        let energy = 0;

        for (const term of this.terms) {
            const transformed = this.applyPauli(
                state,
                term.pauli
            );

            let expectation = [0, 0];

            for (let i = 0; i < 4; i++) {
                expectation = C.add(
                    expectation,
                    C.multiply(
                        C.conjugate(state.amplitudes[i]),
                        transformed[i]
                    )
                );
            }

            if (Math.abs(expectation[1]) > 1e-7) {
                throw new VQEError("Non-real Hamiltonian expectation.");
            }

            energy += term.coefficient * expectation[0];
        }

        return energy;
    }
}

function createHydrogenHamiltonian() {
    return new MolecularHamiltonian([
        { coefficient: -1.052373245772859, pauli: "II" },
        { coefficient: 0.39793742484318045, pauli: "ZI" },
        { coefficient: -0.39793742484318045, pauli: "IZ" },
        { coefficient: -0.01128010425623538, pauli: "ZZ" },
        { coefficient: 0.18093119978423156, pauli: "XX" }
    ]);
}

class HardwareEfficientAnsatz {
    constructor(hamiltonian) {
        this.hamiltonian = hamiltonian;
        this.parameterCount = 2;
    }

    state(parameters) {
        validateParameters(parameters, this.parameterCount);

        return QuantumState.zero()
            .applyRY(parameters[0], 0)
            .applyRY(parameters[1], 1)
            .applyCNOT(0, 1);
    }

    evaluate(parameters) {
        return this.hamiltonian.energy(this.state(parameters));
    }
}

class GradientCalculator {
    static parameterShift(objective, parameters) {
        const gradient = [];

        for (let i = 0; i < parameters.length; i++) {
            const positive = [...parameters];
            const negative = [...parameters];

            positive[i] += PI / 2;
            negative[i] -= PI / 2;

            gradient[i] = 0.5 * (
                objective(positive) - objective(negative)
            );
        }

        return gradient;
    }
}

class AdamOptimizer {
    constructor(options = {}) {
        this.learningRate = options.learningRate ?? 0.05;
        this.beta1 = options.beta1 ?? 0.9;
        this.beta2 = options.beta2 ?? 0.999;
        this.epsilon = options.epsilon ?? 1e-8;

        if (
            this.learningRate <= 0 ||
            this.beta1 <= 0 || this.beta1 >= 1 ||
            this.beta2 <= 0 || this.beta2 >= 1
        ) {
            throw new VQEError("Invalid Adam configuration.");
        }
    }

    async optimize(objective, initial, options = {}) {
        const maximumIterations = options.maxIterations ?? 2000;
        const tolerance = options.tolerance ?? 1e-9;
        const signal = options.signal;

        if (!Number.isInteger(maximumIterations) || maximumIterations < 1) {
            throw new VQEError("Invalid iteration limit.");
        }

        let parameters = [...initial];
        let first = parameters.map(() => 0);
        let second = parameters.map(() => 0);

        const history = [];
        let previousEnergy = objective(parameters);
        let converged = false;

        for (let iteration = 1; iteration <= maximumIterations; iteration++) {
            if (signal?.aborted) {
                const error = new Error("VQE experiment cancelled.");
                error.name = "AbortError";
                throw error;
            }

            const gradient = GradientCalculator.parameterShift(
                objective,
                parameters
            );

            const gradientNorm = Math.sqrt(
                gradient.reduce((sum, value) => sum + value ** 2, 0)
            );

            first = first.map(
                (value, i) =>
                    this.beta1 * value +
                    (1 - this.beta1) * gradient[i]
            );

            second = second.map(
                (value, i) =>
                    this.beta2 * value +
                    (1 - this.beta2) * gradient[i] ** 2
            );

            parameters = parameters.map((value, i) => {
                const m = first[i] / (1 - this.beta1 ** iteration);
                const v = second[i] / (1 - this.beta2 ** iteration);

                return value -
                    this.learningRate * m /
                    (Math.sqrt(v) + this.epsilon);
            });

            parameters = parameters.map(
                value => ((value + PI) % (2 * PI) + 2 * PI) % (2 * PI) - PI
            );

            const energy = objective(parameters);

            assertFinite(energy, "Calculated energy");

            history.push(Object.freeze({
                iteration,
                energy,
                gradientNorm,
                parameters: [...parameters]
            }));

            if (Math.abs(energy - previousEnergy) < tolerance &&
                gradientNorm < tolerance) {
                converged = true;
                break;
            }

            previousEnergy = energy;

            // Yield to the event loop to support cancellation and monitoring.
            if (iteration % 25 === 0) {
                await new Promise(resolve => setImmediate(resolve));
            }
        }

        return {
            parameters,
            history,
            converged
        };
    }
}

class MeasurementService {
    static sample(state, shots = 10000, seed = 42) {
        if (!Number.isInteger(shots) || shots <= 0) {
            throw new VQEError("Shots must be a positive integer.");
        }

        const probabilities = state.amplitudes.map(
            C.magnitudeSquared
        );

        const random = (() => {
            let x = seed >>> 0;
            return () => {
                x ^= x << 13;
                x ^= x >>> 17;
                x ^= x << 5;
                return (x >>> 0) / 4294967296;
            };
        })();

        const counts = new Map();

        for (let shot = 0; shot < shots; shot++) {
            const value = random();
            let cumulative = 0;
            let selected = 3;

            for (let i = 0; i < 4; i++) {
                cumulative += probabilities[i];

                if (value < cumulative) {
                    selected = i;
                    break;
                }
            }

            const basis = selected.toString(2).padStart(2, "0");

            counts.set(basis, (counts.get(basis) ?? 0) + 1);
        }

        return Object.fromEntries(counts);
    }
}

class VQEExperiment extends EventEmitter {
    constructor(hamiltonian, name = "H2") {
        super();

        this.name = name;
        this.ansatz = new HardwareEfficientAnsatz(hamiltonian);
        this.optimizer = new AdamOptimizer();
        this.status = "CREATED";
        this.result = null;
    }

    async run(options = {}) {
        if (this.status === "RUNNING") {
            throw new VQEError("Experiment is already running.");
        }

        this.status = "RUNNING";
        this.emit("started", { molecule: this.name });

        try {
            const initial = options.initialParameters ?? [0.2, -0.4];

            validateParameters(initial);

            const optimized = await this.optimizer.optimize(
                p => this.ansatz.evaluate(p),
                initial,
                options
            );

            const energy = this.ansatz.evaluate(
                optimized.parameters
            );

            this.result = Object.freeze({
                molecule: this.name,
                energy,
                parameters: optimized.parameters,
                iterations: optimized.history.length,
                converged: optimized.converged,
                history: optimized.history
            });

            this.status = "COMPLETED";

            this.emit("completed", this.result);

            return this.result;

        } catch (error) {
            this.status = error.name === "AbortError"
                ? "CANCELLED"
                : "FAILED";

            this.emit("failed", {
                status: this.status,
                message: error.message
            });

            throw error;
        }
    }
}

async function saveExperiment(result, filename = "vqe_h2_results.json") {
    if (path.basename(filename) !== filename ||
        !filename.endsWith(".json")) {
        throw new VQEError("Only a simple JSON filename is allowed.");
    }

    const temporary = `${filename}.tmp`;

    try {
        await fs.writeFile(
            temporary,
            JSON.stringify(result, null, 2),
            { encoding: "utf8", flag: "w" }
        );

        await fs.rename(temporary, filename);
    } catch (error) {
        await fs.rm(temporary, { force: true });
        throw error;
    }
}

async function main() {
    const hamiltonian = createHydrogenHamiltonian();
    const experiment = new VQEExperiment(hamiltonian);

    experiment.on("started", event => {
        console.log("Experiment started:", event.molecule);
    });

    experiment.on("completed", result => {
        console.log("Optimization completed.");
    });

    experiment.on("failed", error => {
        console.error("Experiment failure:", error.message);
    });

    const result = await experiment.run({
        initialParameters: [0.2, -0.4],
        learningRate: 0.05,
        maxIterations: 2000,
        tolerance: 1e-9
    });

    const exactEnergy = -1.8572750302023802;

    const finalState = experiment.ansatz.state(
        result.parameters
    );

    const counts = MeasurementService.sample(finalState, 10000);

    console.log("\n========== VQE RESULTS ==========");
    console.log("Molecule:", result.molecule);
    console.log("Optimized energy:", result.energy.toFixed(12), "Ha");
    console.log("Reference energy:", exactEnergy.toFixed(12), "Ha");
    console.log(
        "Absolute error:",
        Math.abs(result.energy - exactEnergy).toExponential(8)
    );
    console.log("Iterations:", result.iterations);
    console.log("Converged:", result.converged);
    console.log("Parameters:", result.parameters);
    console.log("Measurement counts:", counts);

    await saveExperiment(result);

    console.log("Experiment saved.");
}

if (require.main === module) {
    main().catch(error => {
        console.error(`${error.name}: ${error.message}`);
        process.exitCode = 1;
    });
}

module.exports = {
    QuantumState,
    MolecularHamiltonian,
    HardwareEfficientAnsatz,
    GradientCalculator,
    AdamOptimizer,
    MeasurementService,
    VQEExperiment,
    createHydrogenHamiltonian
};
