"use strict";

/*
 * Quantum Error Mitigation: event-driven experimental simulator.
 *
 * Features:
 * - Quantum measurement sampling.
 * - Bit-flip and depolarizing noise models.
 * - Measurement calibration.
 * - Zero-noise extrapolation.
 * - Shot-budget management.
 * - Experiment lifecycle and asynchronous event handling.
 * - Mitigation policy evaluation.
 *
 * Runtime: Node.js 18+
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");

class QEMError extends Error {}
class ValidationError extends QEMError {}
class ExperimentStateError extends QEMError {}

const ExperimentState = Object.freeze({
    CREATED: "CREATED",
    RUNNING: "RUNNING",
    COMPLETED: "COMPLETED",
    FAILED: "FAILED"
});

const NoiseType = Object.freeze({
    BIT_FLIP: "BIT_FLIP",
    PHASE_FLIP: "PHASE_FLIP",
    DEPOLARIZING: "DEPOLARIZING"
});

const MitigationType = Object.freeze({
    NONE: "NONE",
    READOUT: "READOUT",
    ZNE: "ZNE"
});

function probability(value, name) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 1
    ) {
        throw new ValidationError(`${name} must be between 0 and 1`);
    }
}

function positiveInteger(value, name) {
    if (!Number.isSafeInteger(value) || value <= 0) {
        throw new ValidationError(`${name} must be a positive integer`);
    }
}

class RandomSource {
    constructor(seed = 42) {
        this.state = seed >>> 0;
    }

    next() {
        // Deterministic linear congruential generator for reproducible
        // educational experiments, not cryptographic randomness.
        this.state = (
            Math.imul(1664525, this.state) + 1013904223
        ) >>> 0;

        return this.state / 4294967296;
    }
}

class QuantumState {
    constructor(alpha, beta) {
        this.alpha = alpha;
        this.beta = beta;

        const norm =
            alpha.real ** 2 +
            alpha.imag ** 2 +
            beta.real ** 2 +
            beta.imag ** 2;

        if (Math.abs(norm - 1) > 1e-9) {
            throw new ValidationError("State vector is not normalized");
        }

        Object.freeze(this);
    }

    static zero() {
        return new QuantumState(
            { real: 1, imag: 0 },
            { real: 0, imag: 0 }
        );
    }

    static plus() {
        const v = 1 / Math.sqrt(2);

        return new QuantumState(
            { real: v, imag: 0 },
            { real: v, imag: 0 }
        );
    }

    expectationZ() {
        const a = this.alpha.real ** 2 + this.alpha.imag ** 2;
        const b = this.beta.real ** 2 + this.beta.imag ** 2;
        return a - b;
    }
}

class NoiseChannel {
    constructor(type, rate) {
        probability(rate, "Noise rate");

        if (!Object.values(NoiseType).includes(type)) {
            throw new ValidationError("Unsupported noise type");
        }

        this.type = type;
        this.rate = rate;
        Object.freeze(this);
    }

    expectation(ideal, scale = 1) {
        if (!Number.isFinite(scale) || scale <= 0) {
            throw new ValidationError("Noise scale must be positive");
        }

        const p = this.rate * scale;

        if (p > 1) {
            throw new ValidationError("Scaled noise exceeds valid range");
        }

        switch (this.type) {
            case NoiseType.BIT_FLIP:
                return ideal * (1 - 2 * p);

            case NoiseType.PHASE_FLIP:
                return ideal;

            case NoiseType.DEPOLARIZING:
                return ideal * (1 - 4 * p / 3);

            default:
                throw new ValidationError("Unknown channel");
        }
    }
}

class MeasurementEngine {
    constructor(random) {
        this.random = random;
    }

    sample(expectation, shots, readoutError = 0) {
        positiveInteger(shots, "Shots");
        probability(readoutError, "Readout error");

        const observed = expectation * (1 - 2 * readoutError);
        const pPlus = (1 + observed) / 2;

        let plus = 0;

        for (let i = 0; i < shots; i++) {
            if (this.random.next() < pPlus) {
                plus++;
            }
        }

        const estimate = 2 * plus / shots - 1;

        return {
            estimate,
            standardError: Math.sqrt(
                Math.max(0, 1 - estimate ** 2) / shots
            ),
            counts: {
                plus,
                minus: shots - plus
            }
        };
    }
}

class ReadoutCalibration {
    constructor(error01, error10) {
        probability(error01, "Error 0 to 1");
        probability(error10, "Error 1 to 0");

        if (Math.abs(1 - error01 - error10) < 1e-10) {
            throw new ValidationError("Singular calibration matrix");
        }

        this.error01 = error01;
        this.error10 = error10;
        Object.freeze(this);
    }

    correct(probabilityOne) {
        probability(probabilityOne, "Measured probability");

        const corrected =
            (probabilityOne - this.error01) /
            (1 - this.error01 - this.error10);

        return Math.min(1, Math.max(0, corrected));
    }

    correctExpectation(expectation) {
        return 1 - 2 * this.correct((1 - expectation) / 2);
    }
}

class ZeroNoiseExtrapolation {
    static evaluate(observations, degree = 1) {
        if (!Array.isArray(observations) || observations.length < 2) {
            throw new ValidationError("At least two observations required");
        }

        if (degree !== 1) {
            throw new ValidationError("Only linear extrapolation is supported");
        }

        const points = observations.map(({ scale, value }) => {
            if (!Number.isFinite(scale) || scale <= 0) {
                throw new ValidationError("Invalid noise scale");
            }

            if (!Number.isFinite(value)) {
                throw new ValidationError("Invalid observation");
            }

            return { scale, value };
        }).sort((a, b) => a.scale - b.scale);

        if (points[0].scale === points[1].scale) {
            throw new ValidationError("Distinct noise scales required");
        }

        const { scale: x1, value: y1 } = points[0];
        const { scale: x2, value: y2 } = points[1];

        const estimate = y1 - x1 * (y2 - y1) / (x2 - x1);

        return {
            estimate,
            method: "linear Richardson extrapolation",
            observations: points
        };
    }
}

class MitigationPolicy {
    constructor({
        maximumNoise,
        minimumShots,
        allowedMethods
    }) {
        probability(maximumNoise, "Maximum noise");
        positiveInteger(minimumShots, "Minimum shots");

        if (
            !Array.isArray(allowedMethods) ||
            allowedMethods.length === 0
        ) {
            throw new ValidationError("At least one method is required");
        }

        this.maximumNoise = maximumNoise;
        this.minimumShots = minimumShots;
        this.allowedMethods = new Set(allowedMethods);
    }

    evaluate(experiment) {
        const failures = [];

        if (experiment.channel.rate > this.maximumNoise) {
            failures.push("Noise exceeds policy threshold");
        }

        if (experiment.shots < this.minimumShots) {
            failures.push("Insufficient measurement budget");
        }

        if (!this.allowedMethods.has(experiment.method)) {
            failures.push("Mitigation method not authorized");
        }

        return {
            eligible: failures.length === 0,
            failures
        };
    }
}

class QuantumExperiment extends EventEmitter {
    constructor({
        name,
        state,
        channel,
        shots,
        readoutError = 0,
        seed = 42
    }) {
        super();

        if (!name || typeof name !== "string") {
            throw new ValidationError("Experiment name is required");
        }

        positiveInteger(shots, "Shots");
        probability(readoutError, "Readout error");

        this.name = name;
        this.state = state;
        this.channel = channel;
        this.shots = shots;
        this.readoutError = readoutError;
        this.random = new RandomSource(seed);
        this.measurement = new MeasurementEngine(this.random);
        this.stateStatus = ExperimentState.CREATED;
        this.results = new Map();
    }

    transition(next) {
        const allowed = {
            CREATED: ["RUNNING"],
            RUNNING: ["COMPLETED", "FAILED"],
            COMPLETED: [],
            FAILED: []
        };

        if (!allowed[this.stateStatus].includes(next)) {
            throw new ExperimentStateError(
                `Invalid transition ${this.stateStatus} -> ${next}`
            );
        }

        this.stateStatus = next;
        this.emit("stateChanged", next);
    }

    async execute() {
        this.transition(ExperimentState.RUNNING);

        try {
            const ideal = this.state.expectationZ();

            const raw = this.measurement.sample(
                this.channel.expectation(ideal),
                this.shots,
                this.readoutError
            );

            this.results.set(MitigationType.NONE, raw);

            const calibration = new ReadoutCalibration(
                this.readoutError,
                this.readoutError
            );

            const corrected = calibration.correctExpectation(
                raw.estimate
            );

            this.results.set(MitigationType.READOUT, {
                estimate: corrected,
                standardError:
                    raw.standardError /
                    Math.abs(1 - 2 * this.readoutError)
            });

            const observations = [1, 1.5, 2].map(scale => ({
                scale,
                value: this.channel.expectation(ideal, scale)
            }));

            const zne = ZeroNoiseExtrapolation.evaluate(observations);

            this.results.set(MitigationType.ZNE, zne);

            this.transition(ExperimentState.COMPLETED);

            const report = {
                experiment: this.name,
                ideal,
                results: Object.fromEntries(this.results),
                state: this.stateStatus
            };

            this.emit("completed", report);
            return report;
        } catch (error) {
            this.transition(ExperimentState.FAILED);
            this.emit("failed", error);
            throw error;
        }
    }
}

async function writeReport(report, filename = "qem_report.json") {
    if (
        typeof filename !== "string" ||
        !/^[a-zA-Z0-9_-]+\.json$/.test(filename)
    ) {
        throw new ValidationError("Unsafe report filename");
    }

    await fs.writeFile(
        filename,
        JSON.stringify(report, null, 2),
        { encoding: "utf8", flag: "w" }
    );
}

async function main() {
    const policy = new MitigationPolicy({
        maximumNoise: 0.2,
        minimumShots: 1000,
        allowedMethods: [
            MitigationType.NONE,
            MitigationType.READOUT,
            MitigationType.ZNE
        ]
    });

    const experiment = new QuantumExperiment({
        name: "single-qubit-bit-flip-study",
        state: QuantumState.zero(),
        channel: new NoiseChannel(NoiseType.BIT_FLIP, 0.08),
        shots: 30000,
        readoutError: 0.04,
        seed: 42
    });

    experiment.on("stateChanged", state => {
        console.log(`Experiment state: ${state}`);
    });

    experiment.on("completed", report => {
        console.log("Experiment completed.");
    });

    const report = await experiment.execute();

    for (const method of Object.values(MitigationType)) {
        const decision = policy.evaluate({
            channel: experiment.channel,
            shots: experiment.shots,
            method
        });

        console.log(`${method}: ${decision.eligible ? "ELIGIBLE" : decision.failures.join(", ")}`);
    }

    console.log("\nMeasurement report:");

    for (const [method, result] of Object.entries(report.results)) {
        console.log(
            method,
            "estimate:",
            result.estimate.toFixed(6)
        );
    }

    await writeReport(report);
    console.log("\nSaved qem_report.json");
}

if (require.main === module) {
    main().catch(error => {
        console.error("Experiment failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    QuantumState,
    NoiseChannel,
    MeasurementEngine,
    ReadoutCalibration,
    ZeroNoiseExtrapolation,
    MitigationPolicy,
    QuantumExperiment
};
