"use strict";

/*
 * Quantum Control Laboratory
 *
 * Node.js implementation of:
 * - Pulse construction and validation
 * - Bloch sphere rotations
 * - Rabi oscillation measurements
 * - Automated pi-pulse calibration
 * - Ramsey measurements
 * - Event-driven calibration workflows
 * - Calibration version management
 * - Hardware safety policies
 *
 * Run: node quantum_control.js
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const crypto = require("node:crypto");

class ControlError extends Error {}
class ValidationError extends ControlError {}
class SafetyError extends ControlError {}

const PulseType = Object.freeze({
    X: "X",
    Y: "Y",
    ARBITRARY: "ARBITRARY"
});

const CalibrationStatus = Object.freeze({
    PENDING: "PENDING",
    PASSED: "PASSED",
    FAILED: "FAILED"
});

class HardwarePolicy {
    constructor({
        maxAmplitude = 10,
        minDuration = 0.001,
        maxDuration = 100,
        maxDetuning = 5,
        maxPulses = 1000
    } = {}) {
        this.maxAmplitude = maxAmplitude;
        this.minDuration = minDuration;
        this.maxDuration = maxDuration;
        this.maxDetuning = maxDetuning;
        this.maxPulses = maxPulses;

        if (
            !Number.isFinite(maxAmplitude) || maxAmplitude <= 0 ||
            !Number.isFinite(minDuration) || minDuration <= 0 ||
            !Number.isFinite(maxDuration) || maxDuration < minDuration ||
            !Number.isFinite(maxDetuning) || maxDetuning < 0 ||
            !Number.isInteger(maxPulses) || maxPulses < 1
        ) {
            throw new ValidationError("Invalid hardware policy.");
        }
    }

    validate(pulse) {
        if (pulse.amplitude > this.maxAmplitude) {
            throw new SafetyError("Amplitude exceeds hardware limit.");
        }

        if (
            pulse.durationUs < this.minDuration ||
            pulse.durationUs > this.maxDuration
        ) {
            throw new SafetyError("Duration violates hardware limits.");
        }

        if (Math.abs(pulse.detuningMhz) > this.maxDetuning) {
            throw new SafetyError("Detuning exceeds hardware limit.");
        }
    }
}

class Qubit {
    constructor(id, frequencyGhz, t1Us, t2Us) {
        if (
            !id ||
            !Number.isFinite(frequencyGhz) ||
            !Number.isFinite(t1Us) ||
            !Number.isFinite(t2Us) ||
            frequencyGhz <= 0 ||
            t1Us <= 0 ||
            t2Us <= 0 ||
            t2Us > 2 * t1Us
        ) {
            throw new ValidationError("Invalid qubit configuration.");
        }

        Object.assign(this, {
            id,
            frequencyGhz,
            t1Us,
            t2Us
        });
    }
}

class Pulse {
    constructor({
        type = PulseType.X,
        amplitude,
        durationUs,
        phaseRad = 0,
        detuningMhz = 0,
        startUs = 0
    }) {
        if (!Object.values(PulseType).includes(type)) {
            throw new ValidationError("Unsupported pulse type.");
        }

        const values = [
            amplitude,
            durationUs,
            phaseRad,
            detuningMhz,
            startUs
        ];

        if (!values.every(Number.isFinite)) {
            throw new ValidationError("Pulse parameters must be finite.");
        }

        if (
            amplitude < 0 ||
            durationUs <= 0 ||
            startUs < 0
        ) {
            throw new ValidationError("Invalid pulse parameters.");
        }

        this.id = crypto.randomUUID();
        this.type = type;
        this.amplitude = amplitude;
        this.durationUs = durationUs;
        this.phaseRad = phaseRad;
        this.detuningMhz = detuningMhz;
        this.startUs = startUs;

        Object.freeze(this);
    }

    get endUs() {
        return this.startUs + this.durationUs;
    }
}

class BlochVector {
    constructor(x = 0, y = 0, z = 1) {
        if (![x, y, z].every(Number.isFinite)) {
            throw new ValidationError("Invalid Bloch vector.");
        }

        this.x = x;
        this.y = y;
        this.z = z;
    }

    get excitedProbability() {
        return Math.max(0, Math.min(1, (1 - this.z) / 2));
    }

    rotate(ax, ay, az, angle) {
        const norm = Math.hypot(ax, ay, az);

        if (norm < 1e-12) return;

        const ux = ax / norm;
        const uy = ay / norm;
        const uz = az / norm;

        const c = Math.cos(angle);
        const s = Math.sin(angle);

        const dot = ux * this.x + uy * this.y + uz * this.z;

        const cx = uy * this.z - uz * this.y;
        const cy = uz * this.x - ux * this.z;
        const cz = ux * this.y - uy * this.x;

        const oldX = this.x;
        const oldY = this.y;
        const oldZ = this.z;

        this.x = oldX * c + cx * s + ux * dot * (1 - c);
        this.y = oldY * c + cy * s + uy * dot * (1 - c);
        this.z = oldZ * c + cz * s + uz * dot * (1 - c);
    }

    snapshot() {
        return Object.freeze({
            x: this.x,
            y: this.y,
            z: this.z,
            excitedProbability: this.excitedProbability
        });
    }
}

class QuantumController extends EventEmitter {
    constructor(policy) {
        super();
        this.policy = policy;
        this.executionCount = 0;
    }

    execute(pulse, state = new BlochVector()) {
        this.policy.validate(pulse);

        if (this.executionCount >= this.policy.maxPulses) {
            throw new SafetyError("Pulse execution quota exceeded.");
        }

        const ax = pulse.amplitude * Math.cos(pulse.phaseRad);
        const ay = pulse.amplitude * Math.sin(pulse.phaseRad);
        const az = 2 * Math.PI * pulse.detuningMhz / 1000;

        const frequency = Math.hypot(ax, ay, az);
        const angle = frequency * pulse.durationUs;

        state.rotate(ax, ay, az, angle);

        this.executionCount++;

        this.emit("pulse:executed", {
            pulseId: pulse.id,
            state: state.snapshot(),
            executionCount: this.executionCount
        });

        return state;
    }
}

class PulseSchedule {
    constructor(policy) {
        this.policy = policy;
        this.pulses = [];
    }

    add(pulse) {
        this.policy.validate(pulse);

        const overlap = this.pulses.some(existing =>
            pulse.startUs < existing.endUs &&
            existing.startUs < pulse.endUs
        );

        if (overlap) {
            throw new ValidationError("Pulse schedule contains overlap.");
        }

        this.pulses.push(pulse);
        this.pulses.sort((a, b) => a.startUs - b.startUs);
    }

    async execute(controller, initialState = new BlochVector()) {
        let state = initialState;

        for (const pulse of this.pulses) {
            // Yield between operations to support event-loop monitoring.
            await Promise.resolve();
            state = controller.execute(pulse, state);
        }

        return state;
    }
}

class CalibrationService extends EventEmitter {
    constructor(controller) {
        super();
        this.controller = controller;
        this.records = new Map();
    }

    async measureRabi(amplitude, durationUs) {
        const pulse = new Pulse({
            type: PulseType.X,
            amplitude,
            durationUs
        });

        const state = this.controller.execute(
            pulse,
            new BlochVector()
        );

        return state.excitedProbability;
    }

    async calibrate(qubit, durationUs, maximumAmplitude, samples = 101) {
        if (
            !Number.isInteger(samples) ||
            samples < 3 ||
            samples > 10001
        ) {
            throw new ValidationError("Invalid sample count.");
        }

        if (
            maximumAmplitude <= 0 ||
            maximumAmplitude > this.controller.policy.maxAmplitude
        ) {
            throw new ValidationError("Invalid calibration amplitude.");
        }

        this.emit("calibration:started", { qubitId: qubit.id });

        let best = {
            amplitude: 0,
            probability: -1
        };

        for (let i = 1; i < samples; i++) {
            const amplitude = maximumAmplitude * i / (samples - 1);
            const probability = await this.measureRabi(
                amplitude,
                durationUs
            );

            if (probability > best.probability) {
                best = { amplitude, probability };
            }
        }

        const record = Object.freeze({
            id: crypto.randomUUID(),
            qubitId: qubit.id,
            type: "RABI",
            piAmplitude: best.amplitude,
            piOverTwoAmplitude: best.amplitude / 2,
            excitationError: 1 - best.probability,
            status: best.probability >= 0.95
                ? CalibrationStatus.PASSED
                : CalibrationStatus.FAILED,
            timestamp: new Date().toISOString()
        });

        this.records.set(record.id, record);

        this.emit("calibration:completed", record);

        return record;
    }

    static estimateRamseyDetuning(probabilities, delaysUs) {
        if (
            probabilities.length !== delaysUs.length ||
            probabilities.length < 3
        ) {
            throw new ValidationError("Insufficient Ramsey samples.");
        }

        if (
            probabilities.some(p => !Number.isFinite(p) || p < 0 || p > 1) ||
            delaysUs.some(t => !Number.isFinite(t) || t < 0)
        ) {
            throw new ValidationError("Invalid Ramsey measurements.");
        }

        for (let i = 1; i < delaysUs.length; i++) {
            if (delaysUs[i] <= delaysUs[i - 1]) {
                throw new ValidationError("Delays must increase.");
            }
        }

        const mean = probabilities.reduce((a, b) => a + b, 0)
            / probabilities.length;

        const centered = probabilities.map(p => p - mean);

        const phaseSteps = [];

        for (let i = 0; i < centered.length - 1; i++) {
            phaseSteps.push(Math.atan2(
                centered[i + 1],
                centered[i]
            ));
        }

        const meanPhase = phaseSteps.reduce((a, b) => a + b, 0)
            / phaseSteps.length;

        const intervals = delaysUs.slice(1).map(
            (t, i) => t - delaysUs[i]
        );

        const meanInterval = intervals.reduce((a, b) => a + b, 0)
            / intervals.length;

        return meanPhase / (2 * Math.PI * meanInterval) * 1000;
    }

    async save(filename = "quantum_calibrations.json") {
        const content = JSON.stringify(
            [...this.records.values()],
            null,
            2
        );

        await fs.writeFile(filename, content, {
            encoding: "utf8",
            mode: 0o600
        });
    }
}

async function runTests(policy) {
    const controller = new QuantumController(policy);

    const pi = new Pulse({
        amplitude: Math.PI,
        durationUs: 1
    });

    const result = controller.execute(pi);

    console.assert(
        Math.abs(result.excitedProbability - 1) < 1e-9,
        "Pi-pulse test failed."
    );

    const half = new Pulse({
        amplitude: Math.PI / 2,
        durationUs: 1
    });

    const superposition = controller.execute(
        half,
        new BlochVector()
    );

    console.assert(
        Math.abs(superposition.excitedProbability - 0.5) < 1e-9,
        "Pi/2-pulse test failed."
    );

    try {
        policy.validate(new Pulse({
            amplitude: 100,
            durationUs: 1
        }));

        throw new Error("Unsafe amplitude was accepted.");
    } catch (error) {
        if (!(error instanceof SafetyError)) throw error;
    }

    const schedule = new PulseSchedule(policy);

    schedule.add(new Pulse({
        amplitude: 1,
        durationUs: 2,
        startUs: 0
    }));

    try {
        schedule.add(new Pulse({
            amplitude: 1,
            durationUs: 2,
            startUs: 1
        }));

        throw new Error("Overlapping pulses were accepted.");
    } catch (error) {
        if (!(error instanceof ValidationError)) throw error;
    }

    console.log("All JavaScript quantum-control tests passed.");
}

async function main() {
    const policy = new HardwarePolicy();

    const qubit = new Qubit(
        "QUBIT-001",
        5.0,
        100,
        80
    );

    const controller = new QuantumController(policy);
    const calibration = new CalibrationService(controller);

    controller.on("pulse:executed", event => {
        if (event.state.excitedProbability > 0.999999) {
            console.log("Near-complete state inversion detected.");
        }
    });

    calibration.on("calibration:started", event => {
        console.log(`Calibration started for ${event.qubitId}`);
    });

    calibration.on("calibration:completed", event => {
        console.log(`Calibration status: ${event.status}`);
    });

    console.log("\nQUANTUM CONTROL LABORATORY");

    const record = await calibration.calibrate(
        qubit,
        1.0,
        Math.PI,
        101
    );

    console.log("Rabi calibration:", record);

    const schedule = new PulseSchedule(policy);

    schedule.add(new Pulse({
        amplitude: record.piAmplitude,
        durationUs: 1,
        startUs: 0
    }));

    const finalState = await schedule.execute(controller);

    console.log("Final state:", finalState.snapshot());

    await calibration.save();

    await runTests(policy);
}

main().catch(error => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
