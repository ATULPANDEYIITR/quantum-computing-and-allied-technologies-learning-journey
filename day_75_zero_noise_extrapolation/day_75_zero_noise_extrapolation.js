"use strict";

/*
 * Zero-Noise Extrapolation: Event-Driven Error Mitigation
 *
 * Features:
 * - Gate-folding-inspired noise amplification
 * - Asynchronous measurement scheduling
 * - EventEmitter-based experiment lifecycle
 * - Polynomial interpolation
 * - Richardson extrapolation
 * - Measurement validation
 * - Shot-budget management
 * - Uncertainty and mitigation reporting
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const { writeFile, rename, unlink } = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");

class ZNEError extends Error {}

class ValidationError extends ZNEError {}

class ExperimentError extends ZNEError {}

const Method = Object.freeze({
    LINEAR: "linear",
    QUADRATIC: "quadratic",
    RICHARDSON: "richardson"
});

function validateFinite(value, name) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new ValidationError(`${name} must be finite.`);
    }
}

function validateScale(scale) {
    validateFinite(scale, "Noise scale");

    if (scale < 1) {
        throw new ValidationError("Noise scale must be >= 1.");
    }
}

function validateShots(shots) {
    if (!Number.isSafeInteger(shots) || shots < 2) {
        throw new ValidationError("Shots must be an integer >= 2.");
    }
}

/*
 * Solve a small linear system with partial pivoting.
 * Complexity: O(n^3).
 */
function solveLinearSystem(matrix, vector) {
    const n = vector.length;

    if (n === 0 || matrix.length !== n) {
        throw new ExperimentError("Invalid matrix dimensions.");
    }

    const a = matrix.map((row, i) => {
        if (row.length !== n) {
            throw new ExperimentError("Matrix must be square.");
        }
        return [...row, vector[i]];
    });

    for (let col = 0; col < n; col++) {
        let pivot = col;

        for (let row = col + 1; row < n; row++) {
            if (Math.abs(a[row][col]) > Math.abs(a[pivot][col])) {
                pivot = row;
            }
        }

        if (Math.abs(a[pivot][col]) < 1e-12) {
            throw new ExperimentError("Singular regression system.");
        }

        [a[col], a[pivot]] = [a[pivot], a[col]];

        const divisor = a[col][col];

        for (let j = col; j <= n; j++) {
            a[col][j] /= divisor;
        }

        for (let row = 0; row < n; row++) {
            if (row === col) continue;

            const factor = a[row][col];

            for (let j = col; j <= n; j++) {
                a[row][j] -= factor * a[col][j];
            }
        }
    }

    return a.map(row => row[n]);
}

function polynomialFit(points, degree) {
    if (!Number.isInteger(degree) || degree < 0) {
        throw new ValidationError("Invalid polynomial degree.");
    }

    if (points.length < degree + 1) {
        throw new ExperimentError("Insufficient observations.");
    }

    const xValues = points.map(p => p.scale);
    const yValues = points.map(p => p.mean);

    if (new Set(xValues).size < degree + 1) {
        throw new ExperimentError("Noise scales must be distinct.");
    }

    const powers = Array(2 * degree + 1).fill(0);

    for (const x of xValues) {
        for (let p = 0; p < powers.length; p++) {
            powers[p] += x ** p;
        }
    }

    const matrix = Array.from(
        { length: degree + 1 },
        (_, row) => Array.from(
            { length: degree + 1 },
            (_, col) => powers[row + col]
        )
    );

    const vector = Array.from(
        { length: degree + 1 },
        (_, power) => points.reduce(
            (sum, point) => sum + point.mean * point.scale ** power,
            0
        )
    );

    return solveLinearSystem(matrix, vector);
}

function interpolateAtZero(points, method) {
    if (method === Method.RICHARDSON) {
        if (points.length !== 2) {
            throw new ExperimentError(
                "Richardson extrapolation requires two observations."
            );
        }

        const [a, b] = points;

        if (a.scale === b.scale) {
            throw new ExperimentError("Scales must differ.");
        }

        return {
            estimate:
                (b.scale * a.mean - a.scale * b.mean) /
                (b.scale - a.scale),
            coefficients: []
        };
    }

    const degree = method === Method.LINEAR ? 1 : 2;

    if (method !== Method.LINEAR && method !== Method.QUADRATIC) {
        throw new ValidationError("Unsupported extrapolation method.");
    }

    const coefficients = polynomialFit(points, degree);

    return {
        estimate: coefficients[0],
        coefficients
    };
}

/*
 * A deterministic pseudo-random source makes runs reproducible.
 * The experiment uses Bernoulli sampling for +/-1 measurements.
 */
class RandomSource {
    constructor(seed) {
        this.state = seed >>> 0;
    }

    next() {
        this.state = (1664525 * this.state + 1013904223) >>> 0;
        return this.state / 4294967296;
    }
}

class NoiseModel {
    constructor({
        ideal = 0.85,
        linear = -0.12,
        quadratic = -0.025,
        seed = 42
    } = {}) {
        validateFinite(ideal, "Ideal observable");
        validateFinite(linear, "Linear coefficient");
        validateFinite(quadratic, "Quadratic coefficient");

        if (ideal < -1 || ideal > 1) {
            throw new ValidationError("Ideal observable must be in [-1, 1].");
        }

        this.ideal = ideal;
        this.linear = linear;
        this.quadratic = quadratic;
        this.random = new RandomSource(seed);
    }

    expectation(scale) {
        validateScale(scale);

        const value =
            this.ideal +
            this.linear * scale +
            this.quadratic * scale * scale;

        return Math.max(-1, Math.min(1, value));
    }

    async measure(scale, shots) {
        validateScale(scale);
        validateShots(shots);

        const probability = (1 + this.expectation(scale)) / 2;

        let positive = 0;

        for (let i = 0; i < shots; i++) {
            if (this.random.next() < probability) {
                positive++;
            }
        }

        const mean = 2 * positive / shots - 1;

        return Object.freeze({
            scale,
            mean,
            shots,
            standardError: Math.sqrt(
                Math.max(0, 1 - mean * mean) / shots
            )
        });
    }
}

class ShotBudget {
    constructor(maximum) {
        validateShots(maximum);
        this.maximum = maximum;
        this.consumed = 0;
    }

    reserve(shots) {
        validateShots(shots);

        if (this.consumed + shots > this.maximum) {
            throw new ExperimentError("Shot budget exceeded.");
        }

        this.consumed += shots;
    }

    get remaining() {
        return this.maximum - this.consumed;
    }
}

class ZNEEngine extends EventEmitter {
    constructor(model, scales, shotsPerScale, maximumShots = 1000000) {
        super();

        if (!Array.isArray(scales) || scales.length < 2) {
            throw new ValidationError("At least two scales are required.");
        }

        scales.forEach(validateScale);

        if (new Set(scales).size !== scales.length) {
            throw new ValidationError("Duplicate noise scales.");
        }

        validateShots(shotsPerScale);

        if (maximumShots < scales.length * shotsPerScale) {
            throw new ValidationError("Insufficient shot budget.");
        }

        this.model = model;
        this.scales = [...scales].sort((a, b) => a - b);
        this.shotsPerScale = shotsPerScale;
        this.budget = new ShotBudget(maximumShots);
        this.running = false;
    }

    async execute(method = Method.QUADRATIC) {
        if (this.running) {
            throw new ExperimentError("Experiment already running.");
        }

        this.running = true;
        this.emit("experimentStarted", { method });

        try {
            const scales = method === Method.RICHARDSON
                ? this.scales.slice(0, 2)
                : this.scales;

            const measurements = [];

            /*
             * Sequential acquisition avoids concurrent mutation of the
             * deterministic random generator and shot budget.
             */
            for (const scale of scales) {
                this.budget.reserve(this.shotsPerScale);

                const measurement = await this.model.measure(
                    scale,
                    this.shotsPerScale
                );

                measurements.push(measurement);

                this.emit("measurementCompleted", measurement);
            }

            const fitted = interpolateAtZero(measurements, method);

            const result = Object.freeze({
                id: crypto.randomUUID(),
                method,
                ideal: this.model.ideal,
                baseline: measurements[0].mean,
                estimate: fitted.estimate,
                baselineError: Math.abs(
                    measurements[0].mean - this.model.ideal
                ),
                mitigationError: Math.abs(
                    fitted.estimate - this.model.ideal
                ),
                coefficients: fitted.coefficients,
                measurements,
                shotsConsumed: this.budget.consumed
            });

            this.emit("experimentCompleted", result);

            return result;
        } catch (error) {
            this.emit("experimentFailed", error);
            throw error;
        } finally {
            this.running = false;
        }
    }
}

async function saveReport(filePath, results) {
    const destination = path.resolve(filePath);
    const temporary = `${destination}.tmp`;

    const report = {
        title: "Zero-Noise Extrapolation",
        generatedAt: new Date().toISOString(),
        results
    };

    try {
        await writeFile(
            temporary,
            JSON.stringify(report, null, 2),
            { encoding: "utf8", flag: "w" }
        );

        await rename(temporary, destination);
    } catch (error) {
        await unlink(temporary).catch(() => {});
        throw error;
    }
}

async function selfTest() {
    const points = [
        { scale: 1, mean: 0.8 },
        { scale: 2, mean: 0.5 },
        { scale: 3, mean: 0.15 }
    ];

    const coefficients = polynomialFit(points, 2);

    if (Math.abs(coefficients[0] - 1) > 1e-9) {
        throw new Error("Polynomial intercept test failed.");
    }

    const richardson = interpolateAtZero([
        { scale: 1, mean: 0.8 },
        { scale: 2, mean: 0.6 }
    ], Method.RICHARDSON);

    if (Math.abs(richardson.estimate - 1) > 1e-9) {
        throw new Error("Richardson test failed.");
    }

    const budget = new ShotBudget(100);

    budget.reserve(50);

    if (budget.remaining !== 50) {
        throw new Error("Shot budget test failed.");
    }

    console.log("All JavaScript self-tests passed.");
}

async function main() {
    await selfTest();

    const model = new NoiseModel({
        ideal: 0.85,
        linear: -0.12,
        quadratic: -0.025,
        seed: 42
    });

    const engine = new ZNEEngine(
        model,
        [1, 1.5, 2, 2.5],
        20000,
        1000000
    );

    engine.on("experimentStarted", event => {
        console.log(`Started: ${event.method}`);
    });

    engine.on("measurementCompleted", measurement => {
        console.log(
            `Scale=${measurement.scale}, ` +
            `Estimate=${measurement.mean.toFixed(6)}, ` +
            `SE=${measurement.standardError.toFixed(6)}`
        );
    });

    engine.on("experimentFailed", error => {
        console.error("Experiment failed:", error.message);
    });

    const results = [];

    for (const method of Object.values(Method)) {
        const result = await engine.execute(method);
        results.push(result);

        console.log(
            `${method}: ideal=${result.ideal.toFixed(6)}, ` +
            `baseline=${result.baseline.toFixed(6)}, ` +
            `mitigated=${result.estimate.toFixed(6)}`
        );
    }

    await saveReport("zne_results.json", results);

    console.log("Report saved to zne_results.json.");
}

if (require.main === module) {
    main().catch(error => {
        console.error(error);
        process.exitCode = 1;
    });
}

module.exports = {
    NoiseModel,
    ZNEEngine,
    ShotBudget,
    Method,
    polynomialFit,
    interpolateAtZero
};
