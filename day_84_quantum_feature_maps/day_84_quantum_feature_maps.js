"use strict";

/*
 * Quantum Feature Maps
 *
 * Event-driven statevector simulator using JavaScript typed arrays.
 *
 * Features:
 * - Classical feature validation
 * - Angle encoding
 * - ZZ entanglement encoding
 * - IQP-inspired encoding
 * - Complex statevector operations
 * - Quantum fidelity kernels
 * - Pairwise kernel matrices
 * - Measurement sampling
 * - Asynchronous experiment execution
 * - Execution events and error handling
 *
 * Runtime: Node.js 18+
 */

const EPSILON = 1e-9;

class FeatureMapError extends Error {
    constructor(message) {
        super(message);
        this.name = "FeatureMapError";
    }
}

class ComplexVector {
    constructor(size) {
        this.real = new Float64Array(size);
        this.imag = new Float64Array(size);
    }

    get size() {
        return this.real.length;
    }

    multiply(index, real, imag) {
        const a = this.real[index];
        const b = this.imag[index];

        this.real[index] = a * real - b * imag;
        this.imag[index] = a * imag + b * real;
    }

    normSquared() {
        let result = 0;

        for (let i = 0; i < this.size; i++) {
            result +=
                this.real[i] ** 2 +
                this.imag[i] ** 2;
        }

        return result;
    }

    clone() {
        const copy = new ComplexVector(this.size);
        copy.real.set(this.real);
        copy.imag.set(this.imag);
        return copy;
    }
}

class FeatureDataset {
    constructor(samples) {
        if (!Array.isArray(samples) || samples.length === 0) {
            throw new FeatureMapError(
                "Dataset must contain at least one sample."
            );
        }

        const dimensions = samples[0].length;

        if (!Number.isInteger(dimensions) || dimensions < 1) {
            throw new FeatureMapError("Invalid feature dimension.");
        }

        this.samples = samples.map((sample, index) => {
            if (
                !Array.isArray(sample) ||
                sample.length !== dimensions
            ) {
                throw new FeatureMapError(
                    `Inconsistent dimensions at sample ${index}.`
                );
            }

            return sample.map(value => {
                if (
                    typeof value !== "number" ||
                    !Number.isFinite(value)
                ) {
                    throw new FeatureMapError(
                        "Features must be finite numbers."
                    );
                }

                return value;
            });
        });

        this.dimensions = dimensions;
    }

    normalize(lower = -Math.PI, upper = Math.PI) {
        if (
            !Number.isFinite(lower) ||
            !Number.isFinite(upper) ||
            lower >= upper
        ) {
            throw new FeatureMapError(
                "Invalid normalization bounds."
            );
        }

        const minima = new Array(this.dimensions).fill(Infinity);
        const maxima = new Array(this.dimensions).fill(-Infinity);

        for (const sample of this.samples) {
            sample.forEach((value, i) => {
                minima[i] = Math.min(minima[i], value);
                maxima[i] = Math.max(maxima[i], value);
            });
        }

        const normalized = this.samples.map(sample =>
            sample.map((value, i) => {
                if (maxima[i] === minima[i]) {
                    return (lower + upper) / 2;
                }

                return lower +
                    (value - minima[i]) *
                    (upper - lower) /
                    (maxima[i] - minima[i]);
            })
        );

        return new FeatureDataset(normalized);
    }
}

class QuantumCircuit {
    constructor(features, options = {}) {
        if (!Array.isArray(features) || features.length === 0) {
            throw new FeatureMapError("Features cannot be empty.");
        }

        if (features.length > 20) {
            throw new FeatureMapError(
                "Exact simulation supports at most 20 qubits."
            );
        }

        if (!features.every(Number.isFinite)) {
            throw new FeatureMapError(
                "All features must be finite."
            );
        }

        this.features = [...features];
        this.encoding = options.encoding || "ZZ";
        this.repetitions = options.repetitions ?? 1;
        this.entanglementStrength =
            options.entanglementStrength ?? 1;

        if (!["ANGLE", "ZZ", "IQP"].includes(this.encoding)) {
            throw new FeatureMapError("Unsupported feature map.");
        }

        if (
            !Number.isInteger(this.repetitions) ||
            this.repetitions < 1
        ) {
            throw new FeatureMapError(
                "Repetitions must be positive."
            );
        }

        if (!Number.isFinite(this.entanglementStrength)) {
            throw new FeatureMapError(
                "Invalid entanglement strength."
            );
        }
    }

    applyRY(state, qubit, theta) {
        const mask = 1 << qubit;
        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        for (let i = 0; i < state.size; i++) {
            if (i & mask) continue;

            const j = i | mask;

            const ar = state.real[i];
            const ai = state.imag[i];
            const br = state.real[j];
            const bi = state.imag[j];

            state.real[i] = c * ar - s * br;
            state.imag[i] = c * ai - s * bi;

            state.real[j] = s * ar + c * br;
            state.imag[j] = s * ai + c * bi;
        }
    }

    applyRZ(state, qubit, theta) {
        const mask = 1 << qubit;

        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        for (let i = 0; i < state.size; i++) {
            const sign = i & mask ? 1 : -1;

            state.multiply(
                i,
                c,
                sign * s
            );
        }
    }

    applyZZ(state, first, second, theta) {
        if (first === second) {
            throw new FeatureMapError(
                "Entangling gate requires distinct qubits."
            );
        }

        const firstMask = 1 << first;
        const secondMask = 1 << second;

        for (let i = 0; i < state.size; i++) {
            const different =
                Boolean(i & firstMask) !==
                Boolean(i & secondMask);

            const sign = different ? 1 : -1;
            const angle = -theta * sign / 2;

            state.multiply(
                i,
                Math.cos(angle),
                Math.sin(angle)
            );
        }
    }

    encode() {
        const qubits = this.features.length;
        const state = new ComplexVector(2 ** qubits);

        state.real[0] = 1;

        for (let layer = 0; layer < this.repetitions; layer++) {
            this.features.forEach((value, qubit) => {
                if (this.encoding === "ANGLE") {
                    this.applyRY(state, qubit, value);
                } else if (this.encoding === "ZZ") {
                    this.applyRY(state, qubit, 2 * value);
                    this.applyRZ(state, qubit, value);
                } else {
                    this.applyRY(state, qubit, value);
                    this.applyRZ(state, qubit, 2 * value);
                }
            });

            if (this.encoding !== "ANGLE") {
                for (let i = 0; i < qubits; i++) {
                    for (let j = i + 1; j < qubits; j++) {
                        const theta =
                            this.encoding === "ZZ"
                                ? this.entanglementStrength *
                                  this.features[i] *
                                  this.features[j]
                                : 2 *
                                  this.features[i] *
                                  this.features[j];

                        this.applyZZ(state, i, j, theta);
                    }
                }
            }
        }

        const norm = state.normSquared();

        if (Math.abs(norm - 1) > EPSILON) {
            throw new FeatureMapError(
                `State normalization failure: ${norm}`
            );
        }

        return Object.freeze({
            qubits,
            dimension: state.size,
            state
        });
    }
}

class QuantumKernelService {
    static fidelity(first, second) {
        if (first.qubits !== second.qubits) {
            throw new FeatureMapError(
                "Quantum states have different dimensions."
            );
        }

        let real = 0;
        let imaginary = 0;

        for (let i = 0; i < first.dimension; i++) {
            const ar = first.state.real[i];
            const ai = first.state.imag[i];
            const br = second.state.real[i];
            const bi = second.state.imag[i];

            real += ar * br + ai * bi;
            imaginary += ar * bi - ai * br;
        }

        return Math.min(
            1,
            Math.max(0, real * real + imaginary * imaginary)
        );
    }

    static matrix(states) {
        const size = states.length;
        const result = Array.from(
            { length: size },
            () => new Float64Array(size)
        );

        for (let i = 0; i < size; i++) {
            for (let j = i; j < size; j++) {
                const value = this.fidelity(states[i], states[j]);

                result[i][j] = value;
                result[j][i] = value;
            }
        }

        return result;
    }

    static sample(state, shots = 1000, seed = 12345) {
        if (!Number.isInteger(shots) || shots < 1) {
            throw new FeatureMapError("Invalid shot count.");
        }

        let randomState = seed >>> 0;

        const random = () => {
            randomState ^= randomState << 13;
            randomState ^= randomState >>> 17;
            randomState ^= randomState << 5;
            return (randomState >>> 0) / 4294967296;
        };

        const cumulative = [];
        let total = 0;

        for (let i = 0; i < state.dimension; i++) {
            total +=
                state.state.real[i] ** 2 +
                state.state.imag[i] ** 2;

            cumulative.push(total);
        }

        const counts = new Map();

        for (let shot = 0; shot < shots; shot++) {
            const target = random();
            let low = 0;
            let high = cumulative.length - 1;

            while (low < high) {
                const mid = (low + high) >> 1;

                if (target <= cumulative[mid]) {
                    high = mid;
                } else {
                    low = mid + 1;
                }
            }

            const key = low.toString(2).padStart(state.qubits, "0");
            counts.set(key, (counts.get(key) || 0) + 1);
        }

        return Object.fromEntries(counts);
    }
}

class ExperimentRunner extends EventTarget {
    constructor(dataset, options) {
        super();
        this.dataset = dataset;
        this.options = options;
        this.cancelled = false;
    }

    cancel() {
        this.cancelled = true;
        this.dispatchEvent(new Event("cancelled"));
    }

    async run() {
        this.cancelled = false;

        const normalized = this.dataset.normalize();
        const states = [];

        for (let index = 0; index < normalized.samples.length; index++) {
            if (this.cancelled) {
                return { status: "cancelled" };
            }

            const circuit = new QuantumCircuit(
                normalized.samples[index],
                this.options
            );

            states.push(circuit.encode());

            this.dispatchEvent(
                new CustomEvent("sampleencoded", {
                    detail: { index }
                })
            );

            // Yield control so event handlers and cancellation can run.
            await new Promise(resolve => setImmediate(resolve));
        }

        if (this.cancelled) {
            return { status: "cancelled" };
        }

        const kernel = QuantumKernelService.matrix(states);

        this.dispatchEvent(
            new CustomEvent("completed", {
                detail: { sampleCount: states.length }
            })
        );

        return {
            status: "completed",
            states,
            kernel
        };
    }
}

async function main() {
    const dataset = new FeatureDataset([
        [0.2, 0.4, 0.6],
        [0.3, 0.7, 0.5],
        [0.8, 0.2, 0.9],
        [0.9, 0.6, 0.1]
    ]);

    const runner = new ExperimentRunner(dataset, {
        encoding: "ZZ",
        repetitions: 2,
        entanglementStrength: 0.75
    });

    runner.addEventListener("sampleencoded", event => {
        console.log("Encoded sample:", event.detail.index);
    });

    runner.addEventListener("completed", event => {
        console.log(
            "Experiment completed:",
            event.detail.sampleCount,
            "samples"
        );
    });

    const result = await runner.run();

    if (result.status !== "completed") {
        console.log("Experiment cancelled.");
        return;
    }

    console.log("\nQuantum kernel matrix:");

    for (const row of result.kernel) {
        console.log(
            Array.from(row, value => value.toFixed(6)).join(" ")
        );
    }

    console.log("\nMeasurement distribution:");

    console.log(
        QuantumKernelService.sample(result.states[0], 1000)
    );

    const selfFidelity = QuantumKernelService.fidelity(
        result.states[0],
        result.states[0]
    );

    if (Math.abs(selfFidelity - 1) > EPSILON) {
        throw new FeatureMapError("Self-fidelity validation failed.");
    }

    console.log("\nSelf-fidelity:", selfFidelity);

    console.log("\nAll validations passed.");
}

main().catch(error => {
    console.error("Experiment failed:", error.message);
    process.exitCode = 1;
});
