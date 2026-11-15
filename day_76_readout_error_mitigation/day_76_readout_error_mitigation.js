'use strict';

/*
 * Readout Error Mitigation
 *
 * Event-driven measurement correction engine.
 *
 * Features:
 * - Calibration experiment processing.
 * - Per-qubit assignment matrices.
 * - Multi-qubit tensor products.
 * - Measurement event processing.
 * - Constrained optimization.
 * - Calibration versioning.
 * - Drift detection.
 * - Asynchronous batch processing.
 * - Structured audit events.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library.
 */

const { EventEmitter } = require('node:events');
const fs = require('node:fs/promises');

class ValidationError extends Error {}
class CalibrationError extends Error {}
class MitigationError extends Error {}

function validateProbability(value, label) {
    if (
        typeof value !== 'number' ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 1
    ) {
        throw new ValidationError(`${label} must be in [0, 1].`);
    }
}

function normalize(values) {
    if (!Array.isArray(values) || values.length === 0) {
        throw new ValidationError('Invalid probability vector.');
    }

    if (values.some(x => !Number.isFinite(x) || x < 0)) {
        throw new ValidationError('Invalid probability values.');
    }

    const total = values.reduce((a, b) => a + b, 0);

    if (total <= 0) {
        throw new ValidationError('Zero probability mass.');
    }

    return values.map(x => x / total);
}

function transpose(matrix) {
    return matrix[0].map((_, column) =>
        matrix.map(row => row[column])
    );
}

function multiplyMatrixVector(matrix, vector) {
    return matrix.map(row =>
        row.reduce((sum, value, i) =>
            sum + value * vector[i], 0
        )
    );
}

function multiplyMatrices(a, b) {
    const bt = transpose(b);

    return a.map(row =>
        bt.map(column =>
            row.reduce((sum, value, i) =>
                sum + value * column[i], 0
            )
        )
    );
}

function tensorProduct(a, b) {
    const result = [];

    for (const rowA of a) {
        for (const rowB of b) {
            const row = [];

            for (const valueA of rowA) {
                for (const valueB of rowB) {
                    row.push(valueA * valueB);
                }
            }

            result.push(row);
        }
    }

    return result;
}

function projectSimplex(values) {
    const sorted = [...values].sort((a, b) => b - a);
    let cumulative = 0;
    let theta = 0;

    for (let i = 0; i < sorted.length; i++) {
        cumulative += sorted[i];
        const candidate = (cumulative - 1) / (i + 1);

        if (sorted[i] > candidate) {
            theta = candidate;
        }
    }

    return values.map(x => Math.max(0, x - theta));
}

class Calibration {
    constructor(qubit, p00, p11, shots) {
        if (!Number.isInteger(qubit) || qubit < 0) {
            throw new ValidationError('Invalid qubit index.');
        }

        if (!Number.isInteger(shots) || shots <= 0) {
            throw new ValidationError('Invalid calibration shots.');
        }

        validateProbability(p00, 'P(0|0)');
        validateProbability(p11, 'P(1|1)');

        this.qubit = qubit;
        this.p00 = p00;
        this.p11 = p11;
        this.shots = shots;
        Object.freeze(this);
    }

    get matrix() {
        return [
            [this.p00, 1 - this.p11],
            [1 - this.p00, this.p11]
        ];
    }
}

class ReadoutEngine extends EventEmitter {
    #calibrations = new Map();
    #assignment = [];
    #version = 0;
    #audit = [];
    #busy = false;

    constructor({ regularization = 1e-8, tolerance = 1e-10 } = {}) {
        super();

        if (
            !Number.isFinite(regularization) ||
            regularization < 0 ||
            !Number.isFinite(tolerance) ||
            tolerance <= 0
        ) {
            throw new ValidationError('Invalid engine configuration.');
        }

        this.regularization = regularization;
        this.tolerance = tolerance;
    }

    get version() {
        return this.#version;
    }

    get auditLog() {
        return structuredClone(this.#audit);
    }

    record(event, details = {}) {
        const entry = Object.freeze({
            event,
            timestamp: new Date().toISOString(),
            version: this.#version,
            details
        });

        this.#audit.push(entry);
        this.emit('audit', entry);
    }

    calibrate(calibrations) {
        if (!Array.isArray(calibrations) || calibrations.length === 0) {
            throw new CalibrationError('Calibration list is empty.');
        }

        const candidate = new Map();

        for (const item of calibrations) {
            const calibration = item instanceof Calibration
                ? item
                : new Calibration(
                    item.qubit,
                    item.p00,
                    item.p11,
                    item.shots
                );

            if (candidate.has(calibration.qubit)) {
                throw new CalibrationError('Duplicate qubit calibration.');
            }

            candidate.set(calibration.qubit, calibration);
        }

        const size = candidate.size;

        for (let i = 0; i < size; i++) {
            if (!candidate.has(i)) {
                throw new CalibrationError('Missing qubit calibration.');
            }
        }

        let matrix = [[1]];

        for (let i = 0; i < size; i++) {
            matrix = tensorProduct(matrix, candidate.get(i).matrix);
        }

        this.#calibrations = candidate;
        this.#assignment = matrix;
        this.#version++;

        this.record('CALIBRATION_UPDATED', {
            qubits: size,
            dimension: matrix.length
        });

        this.emit('calibrated', {
            version: this.#version,
            qubits: size
        });

        return this.#version;
    }

    getAssignmentMatrix() {
        return this.#assignment.map(row => [...row]);
    }

    estimate(counts) {
        const qubits = this.#calibrations.size;

        if (qubits === 0) {
            throw new CalibrationError('Engine is not calibrated.');
        }

        if (!counts || typeof counts !== 'object') {
            throw new ValidationError('Counts must be an object.');
        }

        const dimension = 2 ** qubits;
        const probabilities = Array(dimension).fill(0);
        let total = 0;

        for (const [state, count] of Object.entries(counts)) {
            if (
                state.length !== qubits ||
                !/^[01]+$/.test(state) ||
                !Number.isSafeInteger(count) ||
                count < 0
            ) {
                throw new ValidationError(`Invalid measurement: ${state}`);
            }

            probabilities[parseInt(state, 2)] += count;
            total += count;
        }

        if (total <= 0) {
            throw new ValidationError('No measurement shots.');
        }

        return probabilities.map(x => x / total);
    }

    mitigate(counts, options = {}) {
        if (this.#busy) {
            throw new MitigationError('Engine is already processing.');
        }

        const maxIterations = options.maxIterations ?? 10000;

        if (!Number.isInteger(maxIterations) || maxIterations <= 0) {
            throw new ValidationError('Invalid iteration count.');
        }

        const observed = this.estimate(counts);
        const a = this.#assignment;
        const at = transpose(a);
        const ata = multiplyMatrices(at, a);

        for (let i = 0; i < ata.length; i++) {
            ata[i][i] += this.regularization;
        }

        const atq = multiplyMatrixVector(at, observed);

        const lipschitz = Math.max(
            ...ata.map(row =>
                row.reduce((sum, x) => sum + Math.abs(x), 0)
            )
        );

        if (lipschitz <= 0) {
            throw new MitigationError('Invalid optimization matrix.');
        }

        const rate = 1 / lipschitz;
        let estimate = [...observed];
        let converged = false;
        let iterations = 0;

        for (iterations = 1; iterations <= maxIterations; iterations++) {
            const gradient = multiplyMatrixVector(ata, estimate)
                .map((x, i) => x - atq[i]);

            const next = projectSimplex(
                estimate.map((x, i) => x - rate * gradient[i])
            );

            const difference = Math.max(
                ...next.map((x, i) => Math.abs(x - estimate[i]))
            );

            estimate = next;

            if (difference < this.tolerance) {
                converged = true;
                break;
            }
        }

        const predicted = multiplyMatrixVector(a, estimate);

        const residual = Math.sqrt(
            predicted.reduce((sum, x, i) =>
                sum + (x - observed[i]) ** 2, 0
            )
        );

        const result = Object.freeze({
            version: this.#version,
            raw: [...observed],
            corrected: [...estimate],
            residual,
            iterations: Math.min(iterations, maxIterations),
            converged
        });

        this.record('MITIGATION_COMPLETED', {
            residual,
            converged,
            iterations: result.iterations
        });

        this.emit('mitigated', result);

        return result;
    }

    async processBatch(experiments) {
        if (!Array.isArray(experiments)) {
            throw new ValidationError('Batch must be an array.');
        }

        if (this.#busy) {
            throw new MitigationError('Concurrent batch not permitted.');
        }

        this.#busy = true;

        try {
            const version = this.#version;
            const results = [];

            // Sequential processing preserves deterministic audit order.
            for (const experiment of experiments) {
                if (this.#version !== version) {
                    throw new CalibrationError(
                        'Calibration changed during batch processing.'
                    );
                }

                results.push(await Promise.resolve().then(
                    () => this.mitigate(experiment)
                ));
            }

            return results;
        } finally {
            this.#busy = false;
        }
    }

    detectDrift(newCalibration, threshold = 0.03) {
        validateProbability(threshold, 'Drift threshold');

        if (this.#calibrations.size === 0) {
            throw new CalibrationError('No baseline calibration.');
        }

        const current = newCalibration instanceof Calibration
            ? newCalibration
            : new Calibration(
                newCalibration.qubit,
                newCalibration.p00,
                newCalibration.p11,
                newCalibration.shots
            );

        const baseline = this.#calibrations.get(current.qubit);

        if (!baseline) {
            throw new CalibrationError('Unknown qubit.');
        }

        const deviation = Math.max(
            Math.abs(current.p00 - baseline.p00),
            Math.abs(current.p11 - baseline.p11)
        );

        const drifted = deviation > threshold;

        this.record('DRIFT_EVALUATED', {
            qubit: current.qubit,
            deviation,
            threshold,
            drifted
        });

        return { deviation, threshold, drifted };
    }

    async save(filename) {
        const payload = {
            version: this.#version,
            regularization: this.regularization,
            tolerance: this.tolerance,
            calibrations: [...this.#calibrations.values()]
        };

        await fs.writeFile(
            filename,
            JSON.stringify(payload, null, 2),
            { encoding: 'utf8', mode: 0o600 }
        );
    }

    async load(filename) {
        const payload = JSON.parse(
            await fs.readFile(filename, 'utf8')
        );

        if (!Array.isArray(payload.calibrations)) {
            throw new CalibrationError('Invalid calibration file.');
        }

        this.regularization = payload.regularization;
        this.tolerance = payload.tolerance;
        this.calibrate(payload.calibrations);

        return this.#version;
    }
}

function simulateCounts(trueDistribution, matrix, shots, seed = 42) {
    const distribution = normalize(trueDistribution);

    if (
        distribution.length !== matrix.length ||
        !Number.isSafeInteger(shots) ||
        shots <= 0
    ) {
        throw new ValidationError('Invalid simulation inputs.');
    }

    const observed = normalize(
        multiplyMatrixVector(matrix, distribution)
    );

    let randomState = seed >>> 0;

    function random() {
        randomState = (
            Math.imul(1664525, randomState) + 1013904223
        ) >>> 0;

        return randomState / 4294967296;
    }

    const qubits = Math.log2(observed.length);
    const counts = {};

    for (let i = 0; i < observed.length; i++) {
        counts[i.toString(2).padStart(qubits, '0')] = 0;
    }

    for (let shot = 0; shot < shots; shot++) {
        const value = random();
        let cumulative = 0;

        for (let i = 0; i < observed.length; i++) {
            cumulative += observed[i];

            if (value <= cumulative) {
                const state = i.toString(2).padStart(qubits, '0');
                counts[state]++;
                break;
            }
        }
    }

    return counts;
}

async function main() {
    const engine = new ReadoutEngine();

    engine.on('audit', event => {
        console.log(`[AUDIT] ${event.event}`);
    });

    engine.on('mitigated', result => {
        console.log(
            `[EVENT] Correction completed; residual=${result.residual.toFixed(6)}`
        );
    });

    engine.calibrate([
        new Calibration(0, 0.94, 0.91, 10000),
        new Calibration(1, 0.96, 0.93, 10000)
    ]);

    const trueDistribution = [0.70, 0.10, 0.15, 0.05];

    const counts = simulateCounts(
        trueDistribution,
        engine.getAssignmentMatrix(),
        50000
    );

    const result = engine.mitigate(counts);

    console.log('\nRaw probabilities:', result.raw);
    console.log('Corrected probabilities:', result.corrected);
    console.log('Converged:', result.converged);
    console.log('Calibration version:', result.version);

    const drift = engine.detectDrift(
        new Calibration(0, 0.85, 0.84, 10000)
    );

    console.log('\nDrift assessment:', drift);

    const batch = await engine.processBatch([counts, counts]);
    console.log('Batch results:', batch.length);

    await engine.save('readout-calibration.json');

    const restored = new ReadoutEngine();
    await restored.load('readout-calibration.json');

    console.log('Restored calibration version:', restored.version);

    if (
        Math.abs(
            result.corrected.reduce((a, b) => a + b, 0) - 1
        ) > 1e-8
    ) {
        throw new MitigationError('Normalization assertion failed.');
    }

    console.log('\nAll validation checks passed.');
}

main().catch(error => {
    console.error('Execution failed:', error.message);
    process.exitCode = 1;
});
