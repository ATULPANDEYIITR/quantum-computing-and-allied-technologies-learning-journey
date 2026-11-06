"use strict";

/**
 * Topological Quantum Computing: Majorana-Based Concepts
 *
 * Event-driven experiment simulator featuring:
 * - Majorana parity and fusion channels
 * - Ising-anyon braid operations
 * - Complex-valued state evolution
 * - Braid-group relation verification
 * - Experimental policy evaluation
 * - Asynchronous experiment execution
 * - Audit events and JSON export
 *
 * Runtime: Node.js 18+
 */

const fs = require("node:fs/promises");
const crypto = require("node:crypto");

const EPSILON = 1e-9;

class QuantumError extends Error {}
class ValidationError extends QuantumError {}
class PolicyError extends QuantumError {}

const FusionChannel = Object.freeze({
    VACUUM: "1",
    FERMION: "psi"
});

const ExperimentStatus = Object.freeze({
    ACCEPTED: "ACCEPTED",
    REJECTED: "REJECTED",
    FAILED: "FAILED"
});

function assertFinite(value, name) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new ValidationError(`${name} must be finite.`);
    }
}

function complex(real, imag = 0) {
    return { re: real, im: imag };
}

function add(a, b) {
    return complex(a.re + b.re, a.im + b.im);
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

function scale(a, factor) {
    return complex(a.re * factor, a.im * factor);
}

function expImaginary(angle) {
    return complex(Math.cos(angle), Math.sin(angle));
}

function matrixMultiply(a, b) {
    return a.map((row, i) =>
        row.map((_, j) =>
            row.reduce(
                (sum, value, k) => add(sum, multiply(value, b[k][j])),
                complex(0)
            )
        )
    );
}

function matrixVectorMultiply(matrix, vector) {
    return matrix.map(row =>
        row.reduce(
            (sum, value, index) =>
                add(sum, multiply(value, vector[index])),
            complex(0)
        )
    );
}

function identityMatrix(size) {
    return Array.from({ length: size }, (_, i) =>
        Array.from({ length: size }, (_, j) =>
            complex(i === j ? 1 : 0)
        )
    );
}

function normalizeState(state) {
    if (!Array.isArray(state) || state.length !== 2) {
        throw new ValidationError("Expected a two-amplitude state.");
    }

    const norm = state.reduce(
        (sum, amplitude) => sum + magnitudeSquared(amplitude),
        0
    );

    if (!Number.isFinite(norm) || norm <= EPSILON) {
        throw new ValidationError("Invalid quantum-state norm.");
    }

    return state.map(amplitude => scale(amplitude, 1 / Math.sqrt(norm)));
}

function validateState(state) {
    const norm = state.reduce(
        (sum, amplitude) => sum + magnitudeSquared(amplitude),
        0
    );

    if (Math.abs(norm - 1) > EPSILON) {
        throw new ValidationError("State is not normalized.");
    }
}

function innerProduct(a, b) {
    return a.reduce(
        (sum, value, index) =>
            add(sum, multiply(conjugate(value), b[index])),
        complex(0)
    );
}

function fidelity(a, b) {
    return magnitudeSquared(innerProduct(a, b));
}

class ExperimentalPolicy {
    constructor({
        minimumGap = 0.1,
        maximumMeasurementError = 0.05
    } = {}) {
        assertFinite(minimumGap, "minimumGap");
        assertFinite(maximumMeasurementError, "maximumMeasurementError");

        if (minimumGap <= 0 ||
            maximumMeasurementError < 0 ||
            maximumMeasurementError > 1) {
            throw new ValidationError("Invalid policy thresholds.");
        }

        this.minimumGap = minimumGap;
        this.maximumMeasurementError = maximumMeasurementError;
        Object.freeze(this);
    }

    evaluate(conditions) {
        const failures = [];

        for (const key of [
            "energyGap",
            "temperature",
            "coherenceTime",
            "operationTime",
            "measurementError"
        ]) {
            assertFinite(conditions[key], key);
        }

        if (conditions.energyGap < this.minimumGap) {
            failures.push("Insufficient energy gap.");
        }

        if (conditions.temperature < 0) {
            failures.push("Negative temperature.");
        }

        if (conditions.coherenceTime <= 0 ||
            conditions.operationTime <= 0) {
            failures.push("Invalid operating times.");
        }

        if (conditions.operationTime >= conditions.coherenceTime) {
            failures.push("Operation exceeds coherence window.");
        }

        if (conditions.measurementError < 0 ||
            conditions.measurementError > 1) {
            failures.push("Invalid measurement error.");
        } else if (
            conditions.measurementError > this.maximumMeasurementError
        ) {
            failures.push("Parity measurement error exceeds policy.");
        }

        if (conditions.energyGap > 0 &&
            conditions.temperature > conditions.energyGap) {
            failures.push("Temperature exceeds energy-gap scale.");
        }

        return Object.freeze({
            accepted: failures.length === 0,
            failures: Object.freeze(failures)
        });
    }
}

class MajoranaDevice {
    #events = [];
    #state;
    #operationCount = 0;
    #maximumOperations;

    constructor({ majoranaCount = 4, maximumOperations = 10000 } = {}) {
        if (!Number.isInteger(majoranaCount) ||
            majoranaCount < 4 ||
            majoranaCount % 2 !== 0) {
            throw new ValidationError("Majorana count must be even and >= 4.");
        }

        if (!Number.isInteger(maximumOperations) ||
            maximumOperations < 1) {
            throw new ValidationError("Invalid operation limit.");
        }

        this.majoranaCount = majoranaCount;
        this.#maximumOperations = maximumOperations;

        const value = 1 / Math.sqrt(2);

        this.#state = [
            complex(value),
            complex(value)
        ];
    }

    get state() {
        return this.#state.map(value => ({ ...value }));
    }

    get events() {
        return this.#events.map(event => ({ ...event }));
    }

    static parity(occupation) {
        if (occupation !== 0 && occupation !== 1) {
            throw new ValidationError("Occupation must be binary.");
        }

        return occupation === 0 ? 1 : -1;
    }

    static fusionChannel(occupation) {
        return occupation === 0
            ? FusionChannel.VACUUM
            : FusionChannel.FERMION;
    }

    static braidMatrix(generator, orientation = 1) {
        if (![1, 2].includes(generator)) {
            throw new ValidationError("Supported generators are B1 and B2.");
        }

        if (![1, -1].includes(orientation)) {
            throw new ValidationError("Invalid braid orientation.");
        }

        const phase = expImaginary(-Math.PI / 4);
        const inversePhase = conjugate(phase);

        const first = [
            [phase, complex(0)],
            [complex(0), inversePhase]
        ];

        const average = scale(add(phase, inversePhase), 0.5);
        const difference = scale(add(phase, scale(inversePhase, -1)), 0.5);

        const second = [
            [average, difference],
            [difference, average]
        ];

        const selected = generator === 1 ? first : second;

        if (orientation === 1) {
            return selected;
        }

        return selected[0].map((_, column) =>
            selected.map(row => conjugate(row[column]))
        );
    }

    async braid(generator, orientation = 1) {
        if (this.#operationCount >= this.#maximumOperations) {
            throw new PolicyError("Operation limit exceeded.");
        }

        const matrix = MajoranaDevice.braidMatrix(
            generator,
            orientation
        );

        const nextState = normalizeState(
            matrixVectorMultiply(matrix, this.#state)
        );

        validateState(nextState);

        this.#state = nextState;
        this.#operationCount++;

        const event = Object.freeze({
            sequence: this.#operationCount,
            generator,
            orientation,
            timestamp: new Date().toISOString()
        });

        this.#events.push(event);

        // Yield to the event loop so long experiments do not monopolize it.
        await new Promise(resolve => setImmediate(resolve));

        return event;
    }

    async execute(sequence) {
        if (!Array.isArray(sequence)) {
            throw new ValidationError("Sequence must be an array.");
        }

        if (sequence.length + this.#operationCount >
            this.#maximumOperations) {
            throw new PolicyError("Sequence exceeds operation limit.");
        }

        for (const operation of sequence) {
            if (!Array.isArray(operation) || operation.length !== 2) {
                throw new ValidationError("Malformed braid operation.");
            }

            await this.braid(operation[0], operation[1]);
        }

        return this.state;
    }

    static braidRelationError() {
        const b1 = MajoranaDevice.braidMatrix(1);
        const b2 = MajoranaDevice.braidMatrix(2);

        const left = matrixMultiply(
            matrixMultiply(b1, b2),
            b1
        );

        const right = matrixMultiply(
            matrixMultiply(b2, b1),
            b2
        );

        let maximum = 0;

        for (let i = 0; i < 2; i++) {
            for (let j = 0; j < 2; j++) {
                const difference = add(
                    left[i][j],
                    scale(right[i][j], -1)
                );

                maximum = Math.max(
                    maximum,
                    Math.sqrt(magnitudeSquared(difference))
                );
            }
        }

        return maximum;
    }

    reset() {
        const value = 1 / Math.sqrt(2);

        this.#state = [
            complex(value),
            complex(value)
        ];

        this.#events = [];
        this.#operationCount = 0;
    }
}

class ExperimentService {
    constructor(policy = new ExperimentalPolicy()) {
        this.policy = policy;
        this.auditLog = [];
        this.results = new Map();
    }

    async run({ id, sequence, conditions }) {
        if (typeof id !== "string" || !id.trim()) {
            throw new ValidationError("Experiment ID is required.");
        }

        if (this.results.has(id)) {
            throw new ValidationError("Experiment ID already exists.");
        }

        const evaluation = this.policy.evaluate(conditions);

        const experiment = new MajoranaDevice({
            majoranaCount: 4,
            maximumOperations: 10000
        });

        const initialState = experiment.state;

        if (!evaluation.accepted) {
            const result = Object.freeze({
                id,
                status: ExperimentStatus.REJECTED,
                failures: evaluation.failures,
                operations: 0,
                initialState,
                finalState: initialState
            });

            this.results.set(id, result);
            this.auditLog.push({
                id,
                event: "POLICY_REJECTION",
                timestamp: new Date().toISOString()
            });

            return result;
        }

        try {
            await experiment.execute(sequence);

            const finalState = experiment.state;

            const result = Object.freeze({
                id,
                status: ExperimentStatus.ACCEPTED,
                failures: [],
                operations: experiment.events.length,
                initialState,
                finalState,
                fidelity: fidelity(initialState, finalState),
                braidEvents: experiment.events
            });

            this.results.set(id, result);

            this.auditLog.push({
                id,
                event: "EXPERIMENT_COMPLETED",
                timestamp: new Date().toISOString()
            });

            return result;
        } catch (error) {
            const result = Object.freeze({
                id,
                status: ExperimentStatus.FAILED,
                failures: [error.message],
                operations: experiment.events.length,
                initialState,
                finalState: experiment.state
            });

            this.results.set(id, result);

            this.auditLog.push({
                id,
                event: "EXPERIMENT_FAILED",
                timestamp: new Date().toISOString()
            });

            return result;
        }
    }

    async exportResults(filename, id) {
        const result = this.results.get(id);

        if (!result) {
            throw new ValidationError("Experiment not found.");
        }

        const document = {
            exportedAt: new Date().toISOString(),
            checksum: crypto
                .createHash("sha256")
                .update(JSON.stringify(result))
                .digest("hex"),
            experiment: result
        };

        // Exclusive file creation prevents accidental overwriting.
        await fs.writeFile(
            filename,
            JSON.stringify(document, null, 2),
            {
                encoding: "utf8",
                flag: "wx",
                mode: 0o600
            }
        );
    }
}

async function runTests() {
    const assert = require("node:assert/strict");

    assert.equal(MajoranaDevice.parity(0), 1);
    assert.equal(MajoranaDevice.parity(1), -1);

    assert.equal(
        MajoranaDevice.fusionChannel(0),
        FusionChannel.VACUUM
    );

    assert.equal(
        MajoranaDevice.fusionChannel(1),
        FusionChannel.FERMION
    );

    assert.ok(
        MajoranaDevice.braidRelationError() < EPSILON
    );

    const device = new MajoranaDevice();

    const original = device.state;

    await device.execute([
        [1, 1],
        [1, -1]
    ]);

    assert.ok(fidelity(original, device.state) > 1 - EPSILON);

    assert.throws(
        () => MajoranaDevice.braidMatrix(3),
        ValidationError
    );

    const service = new ExperimentService();

    const accepted = await service.run({
        id: "JS-EXP-001",
        sequence: [[1, 1], [2, 1], [1, -1]],
        conditions: {
            energyGap: 0.25,
            temperature: 0.01,
            coherenceTime: 100,
            operationTime: 2,
            measurementError: 0.01
        }
    });

    assert.equal(accepted.status, ExperimentStatus.ACCEPTED);

    const rejected = await service.run({
        id: "JS-EXP-002",
        sequence: [[1, 1]],
        conditions: {
            energyGap: 0.01,
            temperature: 0.01,
            coherenceTime: 10,
            operationTime: 2,
            measurementError: 0.1
        }
    });

    assert.equal(rejected.status, ExperimentStatus.REJECTED);

    console.log("All JavaScript tests passed.");
}

async function main() {
    console.log("MAJORANA TOPOLOGICAL QUANTUM COMPUTING");
    console.log("--------------------------------------");

    const device = new MajoranaDevice();

    console.log("Initial state:", device.state);

    const service = new ExperimentService();

    const result = await service.run({
        id: "MAJORANA-JS-001",
        sequence: [
            [1, 1],
            [2, 1],
            [1, 1],
            [2, -1]
        ],
        conditions: {
            energyGap: 0.25,
            temperature: 0.01,
            coherenceTime: 100,
            operationTime: 2,
            measurementError: 0.01
        }
    });

    console.log("\nExperiment:", result.status);
    console.log("Operations:", result.operations);
    console.log("Final state:", result.finalState);
    console.log("Fidelity:", result.fidelity);

    console.log(
        "\nBraid relation error:",
        MajoranaDevice.braidRelationError()
    );

    await runTests();

    console.log("\nAudit entries:", service.auditLog.length);
}

if (require.main === module) {
    main().catch(error => {
        console.error("Execution failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    MajoranaDevice,
    ExperimentalPolicy,
    ExperimentService,
    FusionChannel,
    ExperimentStatus
};
