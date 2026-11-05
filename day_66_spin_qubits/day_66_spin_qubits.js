"use strict";

/*
 * Spin Qubits: Semiconductor Quantum Device Control
 *
 * Event-driven simulation of:
 * - Semiconductor quantum-dot devices
 * - Electron spin states
 * - ESR and EDSR control pulses
 * - Exchange interaction scheduling
 * - Device calibration
 * - Coherence monitoring
 * - Experiment execution policies
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");

class ValidationError extends Error {}
class DeviceFault extends Error {}
class PolicyError extends Error {}

const Material = Object.freeze({
    SILICON: "silicon",
    GERMANIUM: "germanium",
    GAAS: "gaas"
});

const Architecture = Object.freeze({
    GATE_DEFINED: "gate-defined quantum dot",
    DONOR: "donor-bound electron",
    DOUBLE_DOT: "double quantum dot"
});

const DeviceStatus = Object.freeze({
    OFFLINE: "OFFLINE",
    INITIALIZING: "INITIALIZING",
    READY: "READY",
    RUNNING: "RUNNING",
    FAULT: "FAULT"
});

function requireFinite(value, name, minimum = -Infinity) {
    if (!Number.isFinite(value) || value < minimum) {
        throw new ValidationError(`${name} must be finite and >= ${minimum}`);
    }
}

class SemiconductorDevice {
    constructor(config) {
        this.id = config.id || randomUUID();
        this.material = config.material;
        this.architecture = config.architecture;
        this.temperatureMilliKelvin = config.temperatureMilliKelvin;
        this.magneticFieldTesla = config.magneticFieldTesla;
        this.t1Microseconds = config.t1Microseconds;
        this.t2Microseconds = config.t2Microseconds;
        this.exchangeCouplingMHz = config.exchangeCouplingMHz;

        this.status = DeviceStatus.OFFLINE;
        this.calibration = null;
        this.validate();
    }

    validate() {
        if (!Object.values(Material).includes(this.material)) {
            throw new ValidationError("Invalid semiconductor material.");
        }

        if (!Object.values(Architecture).includes(this.architecture)) {
            throw new ValidationError("Invalid quantum-dot architecture.");
        }

        requireFinite(this.temperatureMilliKelvin, "Temperature", 0.000001);
        requireFinite(this.magneticFieldTesla, "Magnetic field", 0);
        requireFinite(this.t1Microseconds, "T1", 0.000001);
        requireFinite(this.t2Microseconds, "T2", 0.000001);
        requireFinite(this.exchangeCouplingMHz, "Exchange coupling", 0);

        if (this.t2Microseconds > 2 * this.t1Microseconds) {
            throw new ValidationError("T2 cannot exceed 2*T1.");
        }
    }

    initialize() {
        if (this.status !== DeviceStatus.OFFLINE) {
            throw new DeviceFault("Device is not offline.");
        }

        this.status = DeviceStatus.INITIALIZING;
        this.status = DeviceStatus.READY;
    }

    calibrate(data) {
        if (this.status !== DeviceStatus.READY) {
            throw new DeviceFault("Device must be ready for calibration.");
        }

        requireFinite(data.fidelity, "Fidelity", 0);

        if (data.fidelity > 1) {
            throw new ValidationError("Fidelity cannot exceed one.");
        }

        if (data.fidelity < 0.95) {
            throw new PolicyError("Calibration fidelity is below threshold.");
        }

        this.calibration = Object.freeze({
            id: randomUUID(),
            fidelity: data.fidelity,
            calibratedAt: new Date().toISOString(),
            operator: data.operator
        });

        return this.calibration;
    }
}

class SpinState {
    constructor(x = 0, y = 0, z = 1) {
        this.x = x;
        this.y = y;
        this.z = z;
        this.validate();
    }

    validate() {
        [this.x, this.y, this.z].forEach((v) =>
            requireFinite(v, "Bloch coordinate")
        );

        const norm = Math.hypot(this.x, this.y, this.z);

        if (norm > 1 + 1e-9) {
            throw new ValidationError("Bloch vector exceeds unit sphere.");
        }
    }

    rotate(axis, angle) {
        requireFinite(angle, "Rotation angle");

        const c = Math.cos(angle);
        const s = Math.sin(angle);
        const { x, y, z } = this;

        switch (axis) {
            case "X":
                return new SpinState(x, y * c - z * s, y * s + z * c);
            case "Y":
                return new SpinState(x * c + z * s, y, -x * s + z * c);
            case "Z":
                return new SpinState(x * c - y * s, x * s + y * c, z);
            default:
                throw new ValidationError("Unsupported rotation axis.");
        }
    }

    get purity() {
        return (1 + this.x ** 2 + this.y ** 2 + this.z ** 2) / 2;
    }

    get probabilityZero() {
        return (1 + this.z) / 2;
    }

    toJSON() {
        return {
            x: this.x,
            y: this.y,
            z: this.z,
            purity: this.purity,
            probabilityZero: this.probabilityZero
        };
    }
}

class ControlPulse {
    constructor({ axis, angle, durationNs, mechanism }) {
        this.axis = axis;
        this.angle = angle;
        this.durationNs = durationNs;
        this.mechanism = mechanism;

        if (!["X", "Y", "Z"].includes(axis)) {
            throw new ValidationError("Invalid pulse axis.");
        }

        requireFinite(angle, "Pulse angle");
        requireFinite(durationNs, "Pulse duration", 0.000001);

        if (!["ESR", "EDSR", "VIRTUAL_Z"].includes(mechanism)) {
            throw new ValidationError("Unsupported control mechanism.");
        }

        if (mechanism === "VIRTUAL_Z" && axis !== "Z") {
            throw new ValidationError("Virtual-Z requires a Z rotation.");
        }
    }
}

class SpinQubit {
    constructor(id, device) {
        this.id = id;
        this.device = device;
        this.state = new SpinState();
        this.gateCount = 0;
    }

    execute(pulse) {
        if (this.device.status !== DeviceStatus.RUNNING) {
            throw new DeviceFault("Device must be running.");
        }

        if (!this.device.calibration) {
            throw new PolicyError("An active calibration is required.");
        }

        if (!(pulse instanceof ControlPulse)) {
            throw new ValidationError("Invalid control pulse.");
        }

        this.state = this.state.rotate(pulse.axis, pulse.angle);
        this.gateCount++;

        return {
            qubitId: this.id,
            mechanism: pulse.mechanism,
            gateCount: this.gateCount,
            state: this.state.toJSON()
        };
    }

    evolve(durationMicroseconds) {
        requireFinite(durationMicroseconds, "Evolution time", 0);

        const t1 = this.device.t1Microseconds;
        const t2 = this.device.t2Microseconds;

        const relaxation = Math.exp(-durationMicroseconds / t1);
        const dephasing = Math.exp(-durationMicroseconds / t2);

        this.state = new SpinState(
            this.state.x * Math.sqrt(relaxation) * dephasing,
            this.state.y * Math.sqrt(relaxation) * dephasing,
            1 - (1 - this.state.z) * relaxation
        );

        return this.state.toJSON();
    }
}

class ExchangeController {
    constructor(device) {
        this.device = device;
        this.reservations = new Map();
    }

    schedule(qubitA, qubitB, durationMicroseconds, startMicroseconds) {
        if (qubitA.id === qubitB.id) {
            throw new ValidationError("Exchange requires distinct qubits.");
        }

        if (qubitA.device !== this.device || qubitB.device !== this.device) {
            throw new ValidationError("Qubits must belong to the same device.");
        }

        requireFinite(durationMicroseconds, "Duration", 0.000001);
        requireFinite(startMicroseconds, "Start time", 0);

        const end = startMicroseconds + durationMicroseconds;

        for (const reservation of this.reservations.values()) {
            const overlaps =
                startMicroseconds < reservation.end &&
                end > reservation.start;

            if (overlaps) {
                throw new PolicyError("Exchange-control channel is occupied.");
            }
        }

        const id = randomUUID();

        const reservation = Object.freeze({
            id,
            qubits: [qubitA.id, qubitB.id],
            start: startMicroseconds,
            end,
            couplingMHz: this.device.exchangeCouplingMHz,
            relativePhase: 2 * Math.PI *
                this.device.exchangeCouplingMHz * durationMicroseconds
        });

        this.reservations.set(id, reservation);
        return reservation;
    }
}

class ExperimentManager extends EventEmitter {
    constructor(device) {
        super();
        this.device = device;
        this.qubits = new Map();
        this.measurements = [];
        this.auditLog = [];
    }

    registerQubit(qubit) {
        if (this.qubits.has(qubit.id)) {
            throw new ValidationError("Duplicate qubit identifier.");
        }

        if (qubit.device !== this.device) {
            throw new ValidationError("Device mismatch.");
        }

        this.qubits.set(qubit.id, qubit);
    }

    start() {
        if (this.device.status !== DeviceStatus.READY) {
            throw new DeviceFault("Device is not ready.");
        }

        if (!this.device.calibration) {
            throw new PolicyError("Calibration is mandatory.");
        }

        this.device.status = DeviceStatus.RUNNING;
        this.audit("EXPERIMENT_STARTED");
        this.emit("started", this.device.id);
    }

    stop() {
        if (this.device.status !== DeviceStatus.RUNNING) {
            throw new DeviceFault("No experiment is running.");
        }

        this.device.status = DeviceStatus.READY;
        this.audit("EXPERIMENT_STOPPED");
        this.emit("stopped", this.device.id);
    }

    measure(qubitId, shots = 1000) {
        const qubit = this.qubits.get(qubitId);

        if (!qubit) {
            throw new ValidationError("Unknown qubit.");
        }

        if (this.device.status !== DeviceStatus.RUNNING) {
            throw new DeviceFault("Measurement requires a running experiment.");
        }

        if (!Number.isInteger(shots) || shots <= 0 || shots > 10000000) {
            throw new ValidationError("Invalid measurement shot count.");
        }

        // Sample individual outcomes instead of exposing internal state
        // as a measurement result.
        let zeroCount = 0;

        for (let i = 0; i < shots; i++) {
            if (Math.random() < qubit.state.probabilityZero) {
                zeroCount++;
            }
        }

        const result = Object.freeze({
            id: randomUUID(),
            qubitId,
            shots,
            zeroCount,
            oneCount: shots - zeroCount,
            timestamp: new Date().toISOString()
        });

        this.measurements.push(result);
        this.audit("MEASUREMENT_RECORDED");
        this.emit("measurement", result);

        return result;
    }

    audit(action) {
        this.auditLog.push(Object.freeze({
            action,
            deviceId: this.device.id,
            timestamp: new Date().toISOString()
        }));
    }

    async runSequence(qubitId, pulses) {
        if (!Array.isArray(pulses)) {
            throw new ValidationError("Pulse sequence must be an array.");
        }

        const qubit = this.qubits.get(qubitId);

        if (!qubit) {
            throw new ValidationError("Unknown qubit.");
        }

        const results = [];

        for (const pulse of pulses) {
            await Promise.resolve();
            results.push(qubit.execute(pulse));
            this.emit("gateExecuted", results[results.length - 1]);
        }

        return results;
    }
}

async function main() {
    const device = new SemiconductorDevice({
        id: "SI-QD-001",
        material: Material.SILICON,
        architecture: Architecture.DOUBLE_DOT,
        temperatureMilliKelvin: 20,
        magneticFieldTesla: 0.5,
        t1Microseconds: 1000,
        t2Microseconds: 100,
        exchangeCouplingMHz: 5
    });

    device.initialize();

    device.calibrate({
        fidelity: 0.995,
        operator: "quantum-lab-operator"
    });

    const manager = new ExperimentManager(device);

    manager.on("measurement", (data) => {
        console.log("Measurement event:", data);
    });

    manager.on("gateExecuted", (data) => {
        console.log("Gate executed:", data.mechanism);
    });

    const q0 = new SpinQubit("Q0", device);
    const q1 = new SpinQubit("Q1", device);

    manager.registerQubit(q0);
    manager.registerQubit(q1);

    manager.start();

    const pulseSequence = [
        new ControlPulse({
            axis: "Y",
            angle: Math.PI / 2,
            durationNs: 50,
            mechanism: "ESR"
        }),
        new ControlPulse({
            axis: "Z",
            angle: Math.PI / 4,
            durationNs: 10,
            mechanism: "VIRTUAL_Z"
        })
    ];

    await manager.runSequence("Q0", pulseSequence);

    console.log("Coherence evolution:", q0.evolve(10));

    console.log("Measurement:", manager.measure("Q0", 1000));

    const exchange = new ExchangeController(device);

    console.log(
        "Exchange reservation:",
        exchange.schedule(q0, q1, 0.05, 0)
    );

    manager.stop();

    console.log("Audit records:", manager.auditLog.length);
}

main().catch((error) => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
