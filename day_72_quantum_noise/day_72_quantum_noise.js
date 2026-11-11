"use strict";

/**
 * Quantum Noise Modeling and Simulation.
 *
 * Uses Bloch-vector transformations to model:
 * - Amplitude damping
 * - Pure dephasing
 * - Depolarizing noise
 * - Bit-flip and phase-flip noise
 * - Coherent rotation errors
 * - Thermal relaxation
 * - Measurement readout errors
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");

class QuantumNoiseError extends Error {
    constructor(message) {
        super(message);
        this.name = "QuantumNoiseError";
    }
}

const NoiseModel = Object.freeze({
    AMPLITUDE_DAMPING: "amplitude_damping",
    PURE_DEPHASING: "pure_dephasing",
    DEPOLARIZING: "depolarizing",
    BIT_FLIP: "bit_flip",
    PHASE_FLIP: "phase_flip",
    COHERENT_Z: "coherent_z",
    THERMAL_RELAXATION: "thermal_relaxation"
});

function probability(value, name = "probability") {
    if (!Number.isFinite(value) || value < 0 || value > 1) {
        throw new RangeError(`${name} must be in [0, 1]`);
    }
    return value;
}

function validateVector(vector) {
    if (!Array.isArray(vector) || vector.length !== 3) {
        throw new TypeError("Bloch vector must contain three numbers");
    }

    if (!vector.every(Number.isFinite)) {
        throw new TypeError("Bloch coordinates must be finite");
    }

    const magnitude = Math.hypot(...vector);

    if (magnitude > 1 + 1e-9) {
        throw new QuantumNoiseError(
            "Bloch vector lies outside the physical Bloch sphere"
        );
    }

    return [...vector];
}

function clamp(value) {
    return Math.max(-1, Math.min(1, value));
}

function amplitudeDamping(vector, gamma) {
    probability(gamma, "gamma");

    const [x, y, z] = validateVector(vector);
    const transverse = Math.sqrt(1 - gamma);

    return [
        transverse * x,
        transverse * y,
        gamma + (1 - gamma) * z
    ];
}

function pureDephasing(vector, p) {
    probability(p);

    if (p > 0.5) {
        throw new RangeError(
            "Pure dephasing probability must not exceed 0.5"
        );
    }

    const [x, y, z] = validateVector(vector);
    const coherence = 1 - 2 * p;

    return [coherence * x, coherence * y, z];
}

function depolarizing(vector, p) {
    probability(p);

    const [x, y, z] = validateVector(vector);
    const scale = 1 - 4 * p / 3;

    return [scale * x, scale * y, scale * z];
}

function bitFlip(vector, p) {
    probability(p);

    const [x, y, z] = validateVector(vector);
    const scale = 1 - 2 * p;

    return [x, scale * y, scale * z];
}

function phaseFlip(vector, p) {
    probability(p);

    const [x, y, z] = validateVector(vector);
    const scale = 1 - 2 * p;

    return [scale * x, scale * y, z];
}

function coherentZRotation(vector, angle) {
    if (!Number.isFinite(angle)) {
        throw new TypeError("Rotation angle must be finite");
    }

    const [x, y, z] = validateVector(vector);
    const c = Math.cos(angle);
    const s = Math.sin(angle);

    return [
        c * x - s * y,
        s * x + c * y,
        z
    ];
}

function thermalRelaxation(vector, gamma, excitedPopulation) {
    probability(gamma, "gamma");
    probability(excitedPopulation, "excitedPopulation");

    const [x, y, z] = validateVector(vector);
    const q = excitedPopulation;

    const equilibriumZ = 1 - 2 * q;
    const transverse = Math.sqrt(1 - gamma);

    return [
        transverse * x,
        transverse * y,
        gamma * equilibriumZ + (1 - gamma) * z
    ];
}

function relaxationProbability(duration, t1) {
    if (!Number.isFinite(duration) || duration < 0) {
        throw new RangeError("Duration must be nonnegative");
    }

    if (!Number.isFinite(t1) || t1 <= 0) {
        throw new RangeError("T1 must be positive");
    }

    return 1 - Math.exp(-duration / t1);
}

function pureDephasingProbability(duration, t1, t2) {
    if (
        !Number.isFinite(duration) ||
        duration < 0 ||
        !Number.isFinite(t1) ||
        !Number.isFinite(t2) ||
        t1 <= 0 ||
        t2 <= 0 ||
        t2 > 2 * t1
    ) {
        throw new RangeError("Invalid T1, T2, or duration");
    }

    const inverseTphi = Math.max(0, 1 / t2 - 1 / (2 * t1));

    return (1 - Math.exp(-duration * inverseTphi)) / 2;
}

function readoutMeasurement(vector, p01, p10) {
    probability(p01, "p01");
    probability(p10, "p10");

    const [, , z] = validateVector(vector);

    const p0 = (1 + z) / 2;
    const p1 = (1 - z) / 2;

    return {
        reportedZero: p0 * (1 - p01) + p1 * p10,
        reportedOne: p0 * p01 + p1 * (1 - p10)
    };
}

function statePurity(vector) {
    const [x, y, z] = validateVector(vector);
    return (1 + x * x + y * y + z * z) / 2;
}

function fidelityWithPureState(actual, target) {
    const a = validateVector(actual);
    const b = validateVector(target);

    const dot = a.reduce(
        (sum, coordinate, i) => sum + coordinate * b[i],
        0
    );

    return clamp((1 + dot) / 2);
}

class NoiseChannel {
    constructor({ id, model, parameters = {} }) {
        if (typeof id !== "string" || !id.trim()) {
            throw new TypeError("Channel ID is required");
        }

        if (!Object.values(NoiseModel).includes(model)) {
            throw new TypeError(`Unknown noise model: ${model}`);
        }

        this.id = id;
        this.model = model;
        this.parameters = Object.freeze({ ...parameters });
    }

    apply(state) {
        const p = this.parameters;

        switch (this.model) {
            case NoiseModel.AMPLITUDE_DAMPING:
                return amplitudeDamping(state, p.gamma);

            case NoiseModel.PURE_DEPHASING:
                return pureDephasing(state, p.probability);

            case NoiseModel.DEPOLARIZING:
                return depolarizing(state, p.probability);

            case NoiseModel.BIT_FLIP:
                return bitFlip(state, p.probability);

            case NoiseModel.PHASE_FLIP:
                return phaseFlip(state, p.probability);

            case NoiseModel.COHERENT_Z:
                return coherentZRotation(state, p.angle);

            case NoiseModel.THERMAL_RELAXATION:
                return thermalRelaxation(
                    state,
                    p.gamma,
                    p.excitedPopulation
                );

            default:
                throw new QuantumNoiseError("Unsupported channel");
        }
    }
}

class NoisePipeline extends EventEmitter {
    constructor() {
        super();
        this.channels = [];
        this.executions = 0;
    }

    add(channel) {
        if (!(channel instanceof NoiseChannel)) {
            throw new TypeError("Expected a NoiseChannel instance");
        }

        if (this.channels.some(c => c.id === channel.id)) {
            throw new QuantumNoiseError(
                `Duplicate channel ID: ${channel.id}`
            );
        }

        this.channels.push(channel);
        this.emit("channelAdded", channel.id);
    }

    remove(id) {
        const originalLength = this.channels.length;

        this.channels = this.channels.filter(
            channel => channel.id !== id
        );

        if (this.channels.length === originalLength) {
            throw new QuantumNoiseError(`Channel not found: ${id}`);
        }

        this.emit("channelRemoved", id);
    }

    execute(initialState) {
        let state = validateVector(initialState);
        const trace = [];

        for (const channel of this.channels) {
            state = channel.apply(state);

            const entry = Object.freeze({
                channelId: channel.id,
                model: channel.model,
                state: [...state],
                purity: statePurity(state)
            });

            trace.push(entry);
            this.emit("channelApplied", entry);
        }

        this.executions++;

        const result = Object.freeze({
            state,
            purity: statePurity(state),
            trace,
            executionNumber: this.executions
        });

        this.emit("executionCompleted", result);
        return result;
    }
}

class NoiseCalibration {
    constructor(t1, t2) {
        if (
            !Number.isFinite(t1) ||
            !Number.isFinite(t2) ||
            t1 <= 0 ||
            t2 <= 0 ||
            t2 > 2 * t1
        ) {
            throw new RangeError("Invalid coherence calibration");
        }

        this.t1 = t1;
        this.t2 = t2;
    }

    createChannels(duration) {
        const gamma = relaxationProbability(duration, this.t1);
        const phase = pureDephasingProbability(
            duration,
            this.t1,
            this.t2
        );

        return [
            new NoiseChannel({
                id: "calibrated-relaxation",
                model: NoiseModel.AMPLITUDE_DAMPING,
                parameters: { gamma }
            }),
            new NoiseChannel({
                id: "calibrated-dephasing",
                model: NoiseModel.PURE_DEPHASING,
                parameters: { probability: phase }
            })
        ];
    }
}

async function saveResults(results, filename) {
    if (!/^[a-zA-Z0-9_-]+\.json$/.test(filename)) {
        throw new Error("Invalid output filename");
    }

    await fs.writeFile(
        filename,
        JSON.stringify(results, null, 2),
        { encoding: "utf8", flag: "w" }
    );
}

async function main() {
    const initialState = [1, 0, 0];
    const targetState = [1, 0, 0];

    const pipeline = new NoisePipeline();

    pipeline.on("channelAdded", id => {
        console.log(`Registered channel: ${id}`);
    });

    pipeline.on("executionCompleted", result => {
        console.log(
            `Execution ${result.executionNumber} completed`
        );
    });

    pipeline.add(new NoiseChannel({
        id: "energy-relaxation",
        model: NoiseModel.AMPLITUDE_DAMPING,
        parameters: { gamma: 0.15 }
    }));

    pipeline.add(new NoiseChannel({
        id: "environmental-dephasing",
        model: NoiseModel.PURE_DEPHASING,
        parameters: { probability: 0.10 }
    }));

    pipeline.add(new NoiseChannel({
        id: "gate-error",
        model: NoiseModel.COHERENT_Z,
        parameters: { angle: 0.05 }
    }));

    const result = pipeline.execute(initialState);

    const report = {
        initialState,
        finalState: result.state,
        fidelity: fidelityWithPureState(
            result.state,
            targetState
        ),
        purity: result.purity,
        measurement: readoutMeasurement(
            result.state,
            0.03,
            0.05
        ),
        channelTrace: result.trace
    };

    const calibration = new NoiseCalibration(
        100e-6,
        70e-6
    );

    const calibratedPipeline = new NoisePipeline();

    for (const channel of calibration.createChannels(20e-6)) {
        calibratedPipeline.add(channel);
    }

    const calibratedResult = calibratedPipeline.execute(
        [1, 0, 0]
    );

    report.calibratedState = calibratedResult.state;

    console.log("\nQUANTUM NOISE REPORT");
    console.log(JSON.stringify(report, null, 2));

    await saveResults(report, "quantum_noise_report.json");

    console.log("\nReport saved successfully.");
}

main().catch(error => {
    console.error("Quantum simulation failed:", error.message);
    process.exitCode = 1;
});
