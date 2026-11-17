"use strict";

/*
 * Variational Quantum Eigensolver
 * JavaScript implementation with:
 * - Pauli Hamiltonian evaluation
 * - Parameterized quantum circuits
 * - Parameter-shift differentiation
 * - Finite-shot measurement
 * - Asynchronous experiment execution
 * - Event-driven progress monitoring
 * - Optimization and convergence policies
 * - Reproducible simulation
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

class VQEError extends Error {
    constructor(message, code = "VQE_ERROR") {
        super(message);
        this.name = "VQEError";
        this.code = code;
    }
}

const Pauli = Object.freeze({
    I: "I",
    X: "X",
    Y: "Y",
    Z: "Z"
});

const ExperimentStatus = Object.freeze({
    CREATED: "created",
    RUNNING: "running",
    COMPLETED: "completed",
    FAILED: "failed"
});

class Hamiltonian {
    constructor(terms) {
        if (!Array.isArray(terms) || terms.length === 0) {
            throw new VQEError("Hamiltonian requires terms.");
        }

        for (const term of terms) {
            if (!Number.isFinite(term.coefficient)) {
                throw new VQEError("Invalid Hamiltonian coefficient.");
            }

            if (!Object.values(Pauli).includes(term.operator)) {
                throw new VQEError("Invalid Pauli operator.");
            }
        }

        this.terms = Object.freeze(
            terms.map(term => Object.freeze({ ...term }))
        );
    }

    expectation(state) {
        let energy = 0;

        for (const term of this.terms) {
            energy += term.coefficient *
                PauliSimulator.expectation(state, term.operator);
        }

        return energy;
    }

    exactGroundEnergy() {
        const coefficients = new Map([
            ["I", 0],
            ["X", 0],
            ["Y", 0],
            ["Z", 0]
        ]);

        for (const term of this.terms) {
            coefficients.set(
                term.operator,
                coefficients.get(term.operator) + term.coefficient
            );
        }

        const identity = coefficients.get("I");
        const x = coefficients.get("X");
        const y = coefficients.get("Y");
        const z = coefficients.get("Z");

        return identity - Math.sqrt(x * x + y * y + z * z);
    }
}

class PauliSimulator {
    static ry(theta) {
        if (!Number.isFinite(theta)) {
            throw new VQEError("Circuit parameter must be finite.");
        }

        return [
            { re: Math.cos(theta / 2), im: 0 },
            { re: Math.sin(theta / 2), im: 0 }
        ];
    }

    static expectation(state, operator) {
        const [a, b] = state;

        switch (operator) {
            case "I":
                return a.re ** 2 + a.im ** 2 +
                    b.re ** 2 + b.im ** 2;

            case "X":
                return 2 * (a.re * b.re + a.im * b.im);

            case "Y":
                return 2 * (a.im * b.re - a.re * b.im);

            case "Z":
                return a.re ** 2 + a.im ** 2 -
                    b.re ** 2 - b.im ** 2;

            default:
                throw new VQEError("Unsupported Pauli operator.");
        }
    }
}

class SeededRandom {
    constructor(seed = 42) {
        this.state = seed >>> 0;
    }

    next() {
        this.state = (
            1664525 * this.state + 1013904223
        ) >>> 0;

        return this.state / 4294967296;
    }
}

class MeasurementService {
    constructor(seed = 42) {
        this.random = new SeededRandom(seed);
    }

    measure(expectation, shots) {
        if (!Number.isInteger(shots) || shots <= 0) {
            throw new VQEError("Shot count must be a positive integer.");
        }

        if (expectation < -1 || expectation > 1) {
            throw new VQEError("Invalid observable expectation.");
        }

        const probability = (1 + expectation) / 2;
        let positive = 0;

        for (let i = 0; i < shots; i++) {
            if (this.random.next() < probability) {
                positive++;
            }
        }

        return 2 * positive / shots - 1;
    }
}

class ConvergencePolicy {
    constructor({ tolerance = 1e-8, patience = 8 } = {}) {
        if (tolerance <= 0 || patience < 1) {
            throw new VQEError("Invalid convergence policy.");
        }

        this.tolerance = tolerance;
        this.patience = patience;
        this.stableIterations = 0;
        this.previousEnergy = null;
    }

    update(energy) {
        if (
            this.previousEnergy !== null &&
            Math.abs(energy - this.previousEnergy) < this.tolerance
        ) {
            this.stableIterations++;
        } else {
            this.stableIterations = 0;
        }

        this.previousEnergy = energy;

        return this.stableIterations >= this.patience;
    }
}

class VQEExperiment extends EventEmitter {
    constructor(hamiltonian, options = {}) {
        super();

        this.hamiltonian = hamiltonian;
        this.learningRate = options.learningRate ?? 0.15;
        this.maxIterations = options.maxIterations ?? 300;
        this.shots = options.shots ?? 0;
        this.seed = options.seed ?? 42;
        this.parameters = [...(options.initialParameters ?? [0.5])];

        if (
            this.learningRate <= 0 ||
            !Number.isFinite(this.learningRate)
        ) {
            throw new VQEError("Invalid learning rate.");
        }

        if (
            !Number.isInteger(this.maxIterations) ||
            this.maxIterations <= 0
        ) {
            throw new VQEError("Invalid iteration count.");
        }

        if (!this.parameters.length) {
            throw new VQEError("At least one parameter is required.");
        }

        if (this.shots < 0 || !Number.isInteger(this.shots)) {
            throw new VQEError("Invalid shot count.");
        }

        this.measurements = new MeasurementService(this.seed);
        this.convergence = new ConvergencePolicy({
            tolerance: options.tolerance ?? 1e-9,
            patience: options.patience ?? 10
        });

        this.history = [];
        this.status = ExperimentStatus.CREATED;
    }

    state(parameters) {
        if (parameters.length !== 1) {
            throw new VQEError(
                "This implementation uses a one-parameter ansatz."
            );
        }

        return PauliSimulator.ry(parameters[0]);
    }

    energy(parameters, noisy = true) {
        const state = this.state(parameters);

        if (!noisy || this.shots === 0) {
            return this.hamiltonian.expectation(state);
        }

        let total = 0;

        for (const term of this.hamiltonian.terms) {
            const expected = PauliSimulator.expectation(
                state,
                term.operator
            );

            total += term.coefficient *
                this.measurements.measure(expected, this.shots);
        }

        return total;
    }

    gradient(parameters) {
        const shift = Math.PI / 2;
        const plus = [...parameters];
        const minus = [...parameters];

        plus[0] += shift;
        minus[0] -= shift;

        return [
            (this.energy(plus, false) -
                this.energy(minus, false)) / 2
        ];
    }

    async execute() {
        if (this.status !== ExperimentStatus.CREATED) {
            throw new VQEError("Experiment cannot be executed twice.");
        }

        this.status = ExperimentStatus.RUNNING;
        this.emit("started", { status: this.status });

        try {
            for (let iteration = 0;
                iteration < this.maxIterations;
                iteration++) {

                const energy = this.energy(this.parameters, this.shots > 0);
                const gradients = this.gradient(this.parameters);

                const gradientNorm = Math.sqrt(
                    gradients.reduce(
                        (sum, value) => sum + value * value,
                        0
                    )
                );

                const record = Object.freeze({
                    iteration,
                    energy,
                    parameters: [...this.parameters],
                    gradientNorm
                });

                this.history.push(record);

                this.emit("iteration", record);

                if (gradientNorm < 1e-10) {
                    break;
                }

                if (this.convergence.update(energy)) {
                    break;
                }

                this.parameters = this.parameters.map(
                    (value, index) => {
                        const updated = value -
                            this.learningRate * gradients[index];

                        return Math.atan2(
                            Math.sin(updated),
                            Math.cos(updated)
                        );
                    }
                );

                // Yield control so monitoring listeners can process events.
                await new Promise(resolve => setImmediate(resolve));
            }

            this.status = ExperimentStatus.COMPLETED;

            const finalEnergy = this.energy(this.parameters, false);

            const report = Object.freeze({
                algorithm: "VQE",
                status: this.status,
                finalEnergy,
                exactGroundEnergy: this.hamiltonian.exactGroundEnergy(),
                absoluteError: Math.abs(
                    finalEnergy - this.hamiltonian.exactGroundEnergy()
                ),
                optimizedParameters: [...this.parameters],
                iterations: this.history.length,
                shots: this.shots,
                history: [...this.history]
            });

            this.emit("completed", report);
            return report;

        } catch (error) {
            this.status = ExperimentStatus.FAILED;

            this.emit("failed", {
                message: error.message,
                code: error.code ?? "UNEXPECTED_ERROR"
            });

            throw error;
        }
    }
}

async function saveReport(report, filename) {
    const temporary = `${filename}.tmp`;

    try {
        await fs.writeFile(
            temporary,
            JSON.stringify(report, null, 2),
            { encoding: "utf8", flag: "wx" }
        );

        await fs.rename(temporary, filename);
    } catch (error) {
        await fs.rm(temporary, { force: true }).catch(() => {});
        throw new VQEError(
            `Unable to save experiment report: ${error.message}`
        );
    }
}

async function main() {
    const hamiltonian = new Hamiltonian([
        { coefficient: -1.0, operator: "Z" },
        { coefficient: -0.5, operator: "X" }
    ]);

    const experiment = new VQEExperiment(hamiltonian, {
        learningRate: 0.15,
        maxIterations: 300,
        initialParameters: [0.5],
        tolerance: 1e-10,
        patience: 15,
        shots: 0,
        seed: 42
    });

    experiment.on("started", event => {
        console.log("Experiment started:", event.status);
    });

    experiment.on("iteration", record => {
        if (record.iteration % 25 === 0) {
            console.log(
                `Iteration ${record.iteration}: ` +
                `Energy=${record.energy.toFixed(10)}`
            );
        }
    });

    experiment.on("completed", report => {
        console.log("Experiment completed.");
        console.log("Final energy:", report.finalEnergy);
        console.log("Exact energy:", report.exactGroundEnergy);
    });

    const result = await experiment.execute();

    await saveReport(result, "vqe_results.json");

    console.log("Report saved successfully.");
}

if (require.main === module) {
    main().catch(error => {
        console.error("VQE execution failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    Hamiltonian,
    PauliSimulator,
    MeasurementService,
    ConvergencePolicy,
    VQEExperiment
};
