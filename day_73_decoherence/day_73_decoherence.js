"use strict";

/*
 * Quantum Decoherence Laboratory
 *
 * Event-driven T1/T2 simulation.
 * Implements:
 * - Bloch-vector evolution
 * - Energy relaxation
 * - Pure dephasing
 * - Thermal equilibrium
 * - Environmental profiles
 * - Measurement sampling
 * - Experiment event reporting
 * - Parameter validation
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const Environment = Object.freeze({
    ISOLATED: "isolated",
    THERMAL: "thermal",
    MAGNETIC: "magnetic_noise",
    ELECTRIC: "electric_noise",
    VIBRATIONAL: "vibrational",
    MIXED: "mixed"
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

function finitePositive(value, name) {
    if (!Number.isFinite(value) || value <= 0) {
        throw new ValidationError(`${name} must be finite and positive.`);
    }
}

class DecoherenceConfig {
    constructor({
        t1,
        t2,
        environment = Environment.ISOLATED,
        temperature = 0.020,
        equilibriumPopulation = 0,
        noiseStrength = 0
    }) {
        finitePositive(t1, "T1");
        finitePositive(t2, "T2");

        if (t2 > 2 * t1) {
            throw new ValidationError("T2 cannot exceed 2*T1.");
        }

        if (!Object.values(Environment).includes(environment)) {
            throw new ValidationError("Unknown environment.");
        }

        if (!Number.isFinite(temperature) || temperature < 0) {
            throw new ValidationError("Invalid temperature.");
        }

        if (
            !Number.isFinite(equilibriumPopulation) ||
            equilibriumPopulation < 0 ||
            equilibriumPopulation > 1
        ) {
            throw new ValidationError("Invalid equilibrium population.");
        }

        if (!Number.isFinite(noiseStrength) || noiseStrength < 0) {
            throw new ValidationError("Invalid noise strength.");
        }

        this.t1 = t1;
        this.t2 = t2;
        this.environment = environment;
        this.temperature = temperature;
        this.equilibriumPopulation = equilibriumPopulation;
        this.noiseStrength = noiseStrength;

        Object.freeze(this);
    }

    get tPhi() {
        const inverse = 1 / this.t2 - 1 / (2 * this.t1);

        return inverse <= 1e-15 ? Infinity : 1 / inverse;
    }
}

class BlochState {
    constructor(x, y, z) {
        this.x = x;
        this.y = y;
        this.z = z;

        this.validate();
    }

    validate() {
        if (![this.x, this.y, this.z].every(Number.isFinite)) {
            throw new ValidationError("Bloch coordinates must be finite.");
        }

        const radius = this.x ** 2 + this.y ** 2 + this.z ** 2;

        if (radius > 1 + 1e-9) {
            throw new ValidationError("State is outside the Bloch sphere.");
        }
    }

    get coherence() {
        return Math.hypot(this.x, this.y);
    }

    get purity() {
        return (
            1 + this.x ** 2 + this.y ** 2 + this.z ** 2
        ) / 2;
    }

    get excitedProbability() {
        return (1 - this.z) / 2;
    }

    get groundProbability() {
        return (1 + this.z) / 2;
    }
}

class DecoherenceExperiment extends EventEmitter {
    constructor(config) {
        super();

        if (!(config instanceof DecoherenceConfig)) {
            throw new ValidationError("A valid configuration is required.");
        }

        this.config = config;
        this.history = [];
        this.running = false;
    }

    evolve(state, time) {
        if (!(state instanceof BlochState)) {
            throw new ValidationError("Invalid initial state.");
        }

        if (!Number.isFinite(time) || time < 0) {
            throw new ValidationError("Time must be nonnegative.");
        }

        const p = this.config;

        const transverse = Math.exp(-time / p.t2);
        const longitudinal = Math.exp(-time / p.t1);

        const equilibriumZ = 1 - 2 * p.equilibriumPopulation;

        return new BlochState(
            state.x * transverse,
            state.y * transverse,
            equilibriumZ + (state.z - equilibriumZ) * longitudinal
        );
    }

    createObservation(state, time) {
        return Object.freeze({
            time,
            x: state.x,
            y: state.y,
            z: state.z,
            coherence: state.coherence,
            purity: state.purity,
            excitedProbability: state.excitedProbability,
            environment: this.config.environment
        });
    }

    async run({
        initialState,
        duration,
        steps
    }) {
        if (this.running) {
            throw new Error("Experiment is already running.");
        }

        if (!(initialState instanceof BlochState)) {
            throw new ValidationError("Initial state is required.");
        }

        if (!Number.isFinite(duration) || duration < 0) {
            throw new ValidationError("Invalid experiment duration.");
        }

        if (!Number.isInteger(steps) || steps < 1 || steps > 1000000) {
            throw new ValidationError("Steps must be between 1 and 1000000.");
        }

        this.running = true;
        this.history = [];

        try {
            for (let i = 0; i <= steps; i++) {
                const time = duration * i / steps;
                const state = this.evolve(initialState, time);

                const observation = this.createObservation(state, time);

                this.history.push(observation);

                this.emit("measurement", observation);

                // Yield periodically so other event-loop work can proceed.
                if (i % 1000 === 0) {
                    await new Promise(resolve => setImmediate(resolve));
                }
            }

            this.emit("completed", this.history.length);

            return this.history.slice();
        } catch (error) {
            this.emit("experimentError", error);
            throw error;
        } finally {
            this.running = false;
        }
    }

    estimateT2() {
        const valid = this.history.filter(
            point => point.coherence > 1e-12
        );

        if (valid.length < 2) {
            return null;
        }

        const meanX = valid.reduce(
            (sum, p) => sum + p.time, 0
        ) / valid.length;

        const meanY = valid.reduce(
            (sum, p) => sum + Math.log(p.coherence), 0
        ) / valid.length;

        let numerator = 0;
        let denominator = 0;

        for (const point of valid) {
            numerator += (
                (point.time - meanX) *
                (Math.log(point.coherence) - meanY)
            );

            denominator += (point.time - meanX) ** 2;
        }

        if (denominator === 0) {
            return null;
        }

        const slope = numerator / denominator;

        return slope < 0 ? -1 / slope : null;
    }

    sampleMeasurement(state, shots, seed = 42) {
        if (!Number.isInteger(shots) || shots <= 0) {
            throw new ValidationError("Shots must be a positive integer.");
        }

        // Seeded linear congruential generator for reproducibility.
        let randomState = seed >>> 0;

        const random = () => {
            randomState = (
                Math.imul(1664525, randomState) + 1013904223
            ) >>> 0;

            return randomState / 4294967296;
        };

        let excited = 0;

        for (let i = 0; i < shots; i++) {
            if (random() < state.excitedProbability) {
                excited++;
            }
        }

        return {
            shots,
            excited,
            ground: shots - excited,
            estimatedExcitedProbability: excited / shots
        };
    }

    async exportJSON(filename) {
        if (this.running) {
            throw new Error("Cannot export an active experiment.");
        }

        const payload = {
            configuration: {
                t1: this.config.t1,
                t2: this.config.t2,
                tPhi: this.config.tPhi,
                environment: this.config.environment,
                temperature: this.config.temperature
            },
            observations: this.history
        };

        await fs.writeFile(
            filename,
            JSON.stringify(payload, null, 2),
            { encoding: "utf8", flag: "w" }
        );
    }
}

async function main() {
    const config = new DecoherenceConfig({
        t1: 100,
        t2: 60,
        environment: Environment.MIXED,
        temperature: 0.020,
        equilibriumPopulation: 0.01,
        noiseStrength: 0.5
    });

    const experiment = new DecoherenceExperiment(config);

    experiment.on("measurement", observation => {
        if (Math.round(observation.time) % 50 === 0) {
            console.log(
                `t=${observation.time.toFixed(1)} ` +
                `coherence=${observation.coherence.toFixed(5)} ` +
                `purity=${observation.purity.toFixed(5)}`
            );
        }
    });

    experiment.on("completed", count => {
        console.log(`Completed ${count} observations.`);
    });

    experiment.on("experimentError", error => {
        console.error("Experiment failure:", error.message);
    });

    const initial = new BlochState(1, 0, 0);

    const history = await experiment.run({
        initialState: initial,
        duration: 300,
        steps: 300
    });

    const finalState = experiment.evolve(initial, 100);

    console.log("\nEXPERIMENT PARAMETERS");
    console.log(config);

    console.log("\nPURE DEPHASING TIME:", config.tPhi);
    console.log("ESTIMATED T2:", experiment.estimateT2());

    console.log("\nFINAL STATE:", finalState);

    console.log(
        "\nMEASUREMENT:",
        experiment.sampleMeasurement(finalState, 10000)
    );

    await experiment.exportJSON("decoherence_experiment.json");

    if (history.length !== 301) {
        throw new Error("Unexpected measurement count.");
    }

    if (Math.abs(experiment.estimateT2() - 60) > 1e-6) {
        throw new Error("T2 estimation failed.");
    }

    console.log("\nAll validation checks passed.");
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
