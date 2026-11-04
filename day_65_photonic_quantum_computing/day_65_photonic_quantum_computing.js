"use strict";

/*
 * Photonic Quantum Computing: Photons as Qubits
 *
 * Node.js implementation featuring:
 * - Polarization qubit modeling
 * - Complex amplitudes
 * - Jones matrices
 * - Quantum gates
 * - Measurement sampling
 * - Optical channel simulation
 * - Event-driven photon detection
 * - Beam splitter transformations
 * - Hong-Ou-Mandel interference
 * - Experimental statistics
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");

class QuantumError extends Error {
    constructor(message) {
        super(message);
        this.name = "QuantumError";
    }
}

class ValidationError extends QuantumError {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class PhotonLostError extends QuantumError {
    constructor(message = "Photon was not detected.") {
        super(message);
        this.name = "PhotonLostError";
    }
}

function complex(re = 0, im = 0) {
    if (!Number.isFinite(re) || !Number.isFinite(im)) {
        throw new ValidationError("Complex components must be finite.");
    }

    return Object.freeze({ re, im });
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

function scale(a, factor) {
    return complex(a.re * factor, a.im * factor);
}

function magnitudeSquared(a) {
    return a.re * a.re + a.im * a.im;
}

function conjugate(a) {
    return complex(a.re, -a.im);
}

function expi(angle) {
    return complex(Math.cos(angle), Math.sin(angle));
}

class PolarizationQubit {
    constructor(alpha, beta) {
        const norm =
            magnitudeSquared(alpha) +
            magnitudeSquared(beta);

        if (Math.abs(norm - 1) > 1e-9) {
            throw new ValidationError(
                `State must be normalized. Squared norm: ${norm}`
            );
        }

        this.alpha = alpha;
        this.beta = beta;

        Object.freeze(this);
    }

    static horizontal() {
        return new PolarizationQubit(
            complex(1),
            complex(0)
        );
    }

    static vertical() {
        return new PolarizationQubit(
            complex(0),
            complex(1)
        );
    }

    static diagonal() {
        const s = 1 / Math.sqrt(2);

        return new PolarizationQubit(
            complex(s),
            complex(s)
        );
    }

    static circular() {
        const s = 1 / Math.sqrt(2);

        return new PolarizationQubit(
            complex(s),
            complex(0, s)
        );
    }

    static normalize(alpha, beta) {
        const norm = Math.sqrt(
            magnitudeSquared(alpha) +
            magnitudeSquared(beta)
        );

        if (!Number.isFinite(norm) || norm === 0) {
            throw new ValidationError(
                "Cannot normalize an invalid state."
            );
        }

        return new PolarizationQubit(
            scale(alpha, 1 / norm),
            scale(beta, 1 / norm)
        );
    }

    get probabilities() {
        return Object.freeze({
            H: magnitudeSquared(this.alpha),
            V: magnitudeSquared(this.beta)
        });
    }

    get blochVector() {
        const product = multiply(
            conjugate(this.alpha),
            this.beta
        );

        return Object.freeze({
            x: 2 * product.re,
            y: 2 * product.im,
            z:
                magnitudeSquared(this.alpha) -
                magnitudeSquared(this.beta)
        });
    }
}

class OpticalCircuit {
    constructor() {
        this.operations = [];
    }

    addGate(name, matrix) {
        if (!Array.isArray(matrix) || matrix.length !== 2) {
            throw new ValidationError("A 2x2 matrix is required.");
        }

        for (const row of matrix) {
            if (!Array.isArray(row) || row.length !== 2) {
                throw new ValidationError("Invalid matrix dimensions.");
            }
        }

        this.operations.push({
            name,
            matrix
        });

        return this;
    }

    hadamard() {
        const s = 1 / Math.sqrt(2);

        return this.addGate("Hadamard", [
            [complex(s), complex(s)],
            [complex(s), complex(-s)]
        ]);
    }

    bitFlip() {
        return this.addGate("Pauli-X", [
            [complex(0), complex(1)],
            [complex(1), complex(0)]
        ]);
    }

    phaseFlip() {
        return this.addGate("Pauli-Z", [
            [complex(1), complex(0)],
            [complex(0), complex(-1)]
        ]);
    }

    phaseShift(angle) {
        if (!Number.isFinite(angle)) {
            throw new ValidationError("Invalid phase.");
        }

        return this.addGate("Phase Shift", [
            [complex(1), complex(0)],
            [complex(0), expi(angle)]
        ]);
    }

    execute(initialState) {
        let state = initialState;

        for (const operation of this.operations) {
            const [[a, b], [c, d]] = operation.matrix;

            const alpha = add(
                multiply(a, state.alpha),
                multiply(b, state.beta)
            );

            const beta = add(
                multiply(c, state.alpha),
                multiply(d, state.beta)
            );

            state = new PolarizationQubit(alpha, beta);
        }

        return state;
    }
}

class RandomGenerator {
    constructor(seed = 123456789) {
        this.state = seed >>> 0;
    }

    next() {
        // Deterministic Mulberry32 generator for reproducible experiments.
        this.state += 0x6D2B79F5;

        let t = this.state;

        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);

        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
}

class PolarizationMeasurement {
    static measure(state, rng) {
        const pH = state.probabilities.H;

        return rng.next() < pH ? "H" : "V";
    }

    static sample(state, shots, rng) {
        if (!Number.isSafeInteger(shots) || shots <= 0) {
            throw new ValidationError(
                "Shots must be a positive safe integer."
            );
        }

        const counts = new Map([
            ["H", 0],
            ["V", 0]
        ]);

        for (let i = 0; i < shots; i++) {
            const outcome = this.measure(state, rng);

            counts.set(
                outcome,
                counts.get(outcome) + 1
            );
        }

        return counts;
    }
}

class OpticalChannel {
    constructor({
        transmission,
        detectorEfficiency
    }) {
        for (const [name, value] of Object.entries({
            transmission,
            detectorEfficiency
        })) {
            if (!Number.isFinite(value) || value < 0 || value > 1) {
                throw new ValidationError(
                    `${name} must be between zero and one.`
                );
            }
        }

        this.transmission = transmission;
        this.detectorEfficiency = detectorEfficiency;

        Object.freeze(this);
    }

    get detectionProbability() {
        return this.transmission * this.detectorEfficiency;
    }

    transmit(rng) {
        return rng.next() < this.detectionProbability;
    }
}

class PhotonDetector extends EventEmitter {
    constructor(channel, rng) {
        super();

        this.channel = channel;
        this.rng = rng;
        this.detected = 0;
        this.lost = 0;
    }

    async detect(state, photonId = randomUUID()) {
        // Event-driven detection permits asynchronous monitoring.
        await Promise.resolve();

        if (!this.channel.transmit(this.rng)) {
            this.lost++;

            const error = new PhotonLostError();

            this.emit("lost", {
                photonId,
                timestamp: Date.now()
            });

            throw error;
        }

        const outcome = PolarizationMeasurement.measure(
            state,
            this.rng
        );

        this.detected++;

        const event = Object.freeze({
            photonId,
            outcome,
            timestamp: Date.now()
        });

        this.emit("detected", event);

        return event;
    }
}

class BeamSplitter {
    static transform(reflectivity) {
        if (
            !Number.isFinite(reflectivity) ||
            reflectivity < 0 ||
            reflectivity > 1
        ) {
            throw new ValidationError(
                "Reflectivity must be between zero and one."
            );
        }

        const r = Math.sqrt(reflectivity);
        const t = Math.sqrt(1 - reflectivity);

        // Unitary transformation using a consistent phase convention.
        return [
            [complex(r), complex(0, t)],
            [complex(0, t), complex(r)]
        ];
    }
}

class HongOuMandelExperiment {
    static evaluate(overlap, reflectivity = 0.5) {
        if (
            !Number.isFinite(overlap) ||
            overlap < 0 ||
            overlap > 1
        ) {
            throw new ValidationError("Invalid photon overlap.");
        }

        if (
            !Number.isFinite(reflectivity) ||
            reflectivity < 0 ||
            reflectivity > 1
        ) {
            throw new ValidationError("Invalid reflectivity.");
        }

        const coincidence =
            4 *
            reflectivity *
            (1 - reflectivity) *
            (1 - overlap);

        return Object.freeze({
            coincidenceProbability: coincidence,
            bunchingProbability: 1 - coincidence
        });
    }
}

class ExperimentManager {
    constructor(state, channel, seed = 42) {
        this.state = state;
        this.rng = new RandomGenerator(seed);
        this.detector = new PhotonDetector(channel, this.rng);

        this.statistics = {
            shots: 0,
            detected: 0,
            lost: 0,
            H: 0,
            V: 0
        };

        this.detector.on("detected", event => {
            this.statistics.detected++;
            this.statistics[event.outcome]++;
        });

        this.detector.on("lost", () => {
            this.statistics.lost++;
        });
    }

    async run(shots) {
        if (!Number.isSafeInteger(shots) || shots <= 0) {
            throw new ValidationError("Invalid experiment size.");
        }

        for (let i = 0; i < shots; i++) {
            this.statistics.shots++;

            try {
                await this.detector.detect(this.state);
            } catch (error) {
                if (!(error instanceof PhotonLostError)) {
                    throw error;
                }
            }
        }

        return Object.freeze({
            ...this.statistics,
            detectionRate:
                this.statistics.detected /
                this.statistics.shots,
            horizontalFraction:
                this.statistics.detected === 0
                    ? 0
                    : this.statistics.H /
                      this.statistics.detected
        });
    }
}

async function runTests() {
    const horizontal = PolarizationQubit.horizontal();
    const vertical = PolarizationQubit.vertical();

    const flipped = new OpticalCircuit()
        .bitFlip()
        .execute(horizontal);

    if (
        Math.abs(flipped.probabilities.V - 1) > 1e-9
    ) {
        throw new Error("Pauli-X test failed.");
    }

    const diagonal = new OpticalCircuit()
        .hadamard()
        .execute(horizontal);

    if (
        Math.abs(diagonal.probabilities.H - 0.5) > 1e-9
    ) {
        throw new Error("Hadamard test failed.");
    }

    const counts = PolarizationMeasurement.sample(
        diagonal,
        1000,
        new RandomGenerator(10)
    );

    if (counts.get("H") + counts.get("V") !== 1000) {
        throw new Error("Measurement count test failed.");
    }

    if (
        HongOuMandelExperiment.evaluate(1)
            .coincidenceProbability !== 0
    ) {
        throw new Error("Interference test failed.");
    }

    if (
        OpticalChannel.prototype &&
        new OpticalChannel({
            transmission: 1,
            detectorEfficiency: 1
        }).detectionProbability !== 1
    ) {
        throw new Error("Channel test failed.");
    }

    let rejected = false;

    try {
        new PolarizationQubit(
            complex(2),
            complex(0)
        );
    } catch (error) {
        rejected = error instanceof ValidationError;
    }

    if (!rejected) {
        throw new Error("Invalid state was accepted.");
    }

    console.log("All JavaScript tests passed.");
}

async function main() {
    await runTests();

    console.log("\nPHOTONIC QUANTUM COMPUTING");
    console.log("==========================");

    const source = PolarizationQubit.diagonal();

    console.log("\nInitial photon probabilities:");
    console.log(source.probabilities);

    const circuit = new OpticalCircuit()
        .phaseShift(Math.PI / 2)
        .bitFlip();

    const output = circuit.execute(source);

    console.log("\nCircuit output:");
    console.log(output.probabilities);

    console.log("\nBloch vector:");
    console.log(output.blochVector);

    const channel = new OpticalChannel({
        transmission: 0.85,
        detectorEfficiency: 0.90
    });

    const experiment = new ExperimentManager(
        source,
        channel,
        2026
    );

    const report = await experiment.run(5000);

    console.log("\nExperimental report:");
    console.log(report);

    console.log("\nHong-Ou-Mandel interference:");

    for (const overlap of [0, 0.5, 1]) {
        console.log({
            overlap,
            ...HongOuMandelExperiment.evaluate(overlap)
        });
    }

    console.log("\nBeam splitter:");
    console.log(BeamSplitter.transform(0.5));
}

main().catch(error => {
    console.error("Experiment failed:", error.message);
    process.exitCode = 1;
});
