'use strict';

/**
 * NISQ Era: Event-driven quantum experiment scheduler.
 *
 * Features:
 * - Quantum device capability registration
 * - Gate and connectivity validation
 * - Calibration-aware device selection
 * - Noise and coherence budgeting
 * - Asynchronous job scheduling
 * - Concurrency control
 * - Cancellation and failure handling
 * - Reproducible shot estimates
 * - Structured experiment reporting
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require('node:events');
const { randomUUID } = require('node:crypto');
const fs = require('node:fs/promises');

class NISQError extends Error {
    constructor(message, code = 'NISQ_ERROR') {
        super(message);
        this.name = 'NISQError';
        this.code = code;
    }
}

const JobStatus = Object.freeze({
    QUEUED: 'QUEUED',
    RUNNING: 'RUNNING',
    COMPLETED: 'COMPLETED',
    FAILED: 'FAILED',
    CANCELLED: 'CANCELLED'
});

const GateType = Object.freeze({
    H: 'H',
    X: 'X',
    Y: 'Y',
    Z: 'Z',
    S: 'S',
    T: 'T',
    CNOT: 'CNOT',
    CZ: 'CZ'
});

class QuantumCircuit {
    constructor(name, qubitCount) {
        if (!Number.isInteger(qubitCount) ||
            qubitCount < 1 ||
            qubitCount > 100) {
            throw new NISQError(
                'Qubit count must be an integer between 1 and 100',
                'INVALID_QUBIT_COUNT'
            );
        }

        if (typeof name !== 'string' || !name.trim()) {
            throw new NISQError('Circuit name is required');
        }

        this.name = name.trim();
        this.qubitCount = qubitCount;
        this.gates = [];
    }

    addGate(type, ...qubits) {
        const twoQubitGates = new Set([
            GateType.CNOT,
            GateType.CZ
        ]);

        if (!Object.values(GateType).includes(type)) {
            throw new NISQError(`Unsupported gate: ${type}`);
        }

        const expected = twoQubitGates.has(type) ? 2 : 1;

        if (qubits.length !== expected ||
            new Set(qubits).size !== expected) {
            throw new NISQError(
                `${type} requires ${expected} distinct qubit(s)`
            );
        }

        for (const qubit of qubits) {
            if (!Number.isInteger(qubit) ||
                qubit < 0 ||
                qubit >= this.qubitCount) {
                throw new NISQError(
                    `Invalid qubit index: ${qubit}`
                );
            }
        }

        this.gates.push(Object.freeze({
            id: this.gates.length + 1,
            type,
            qubits: Object.freeze([...qubits])
        }));

        return this;
    }

    h(q) { return this.addGate(GateType.H, q); }
    x(q) { return this.addGate(GateType.X, q); }
    z(q) { return this.addGate(GateType.Z, q); }

    cnot(control, target) {
        return this.addGate(GateType.CNOT, control, target);
    }

    cz(control, target) {
        return this.addGate(GateType.CZ, control, target);
    }

    get depth() {
        const availability = Array(this.qubitCount).fill(0);

        for (const gate of this.gates) {
            const layer = Math.max(
                ...gate.qubits.map(q => availability[q])
            ) + 1;

            for (const q of gate.qubits) {
                availability[q] = layer;
            }
        }

        return Math.max(...availability);
    }

    get twoQubitGateCount() {
        return this.gates.filter(
            gate => gate.qubits.length === 2
        ).length;
    }

    validate() {
        if (this.gates.length === 0) {
            throw new NISQError('Empty circuits cannot be submitted');
        }

        return true;
    }

    snapshot() {
        return Object.freeze({
            name: this.name,
            qubitCount: this.qubitCount,
            gates: Object.freeze([...this.gates]),
            depth: this.depth,
            twoQubitGateCount: this.twoQubitGateCount
        });
    }
}

class QuantumDevice {
    constructor({
        id,
        name,
        qubitCount,
        topology,
        singleQubitError,
        twoQubitError,
        readoutError,
        coherenceTimeMicros,
        gateTimeMicros,
        available = true
    }) {
        if (!id || !name) {
            throw new NISQError('Device ID and name are required');
        }

        if (!Number.isInteger(qubitCount) || qubitCount < 1) {
            throw new NISQError('Invalid device qubit capacity');
        }

        for (const [field, value] of Object.entries({
            singleQubitError,
            twoQubitError,
            readoutError
        })) {
            if (!Number.isFinite(value) ||
                value < 0 || value > 1) {
                throw new NISQError(`Invalid ${field}`);
            }
        }

        if (!(coherenceTimeMicros > 0) ||
            !(gateTimeMicros > 0)) {
            throw new NISQError('Timing values must be positive');
        }

        this.id = id;
        this.name = name;
        this.qubitCount = qubitCount;
        this.topology = new Set(
            topology.map(pair => QuantumDevice.edgeKey(...pair))
        );

        this.singleQubitError = singleQubitError;
        this.twoQubitError = twoQubitError;
        this.readoutError = readoutError;
        this.coherenceTimeMicros = coherenceTimeMicros;
        this.gateTimeMicros = gateTimeMicros;
        this.available = available;
    }

    static edgeKey(a, b) {
        return [Math.min(a, b), Math.max(a, b)].join(':');
    }

    supports(circuit) {
        if (!this.available ||
            circuit.qubitCount > this.qubitCount) {
            return false;
        }

        return circuit.gates.every(gate => {
            if (gate.qubits.length === 1) {
                return true;
            }

            return this.topology.has(
                QuantumDevice.edgeKey(...gate.qubits)
            );
        });
    }

    estimate(circuit, shots) {
        const oneQubitCount =
            circuit.gates.length - circuit.twoQubitGateCount;

        const gateErrorProbability =
            Math.pow(
                1 - this.singleQubitError,
                oneQubitCount
            ) *
            Math.pow(
                1 - this.twoQubitError,
                circuit.twoQubitGateCount
            );

        const readoutProbability =
            Math.pow(
                1 - this.readoutError,
                circuit.qubitCount
            );

        const estimatedSuccess =
            gateErrorProbability * readoutProbability;

        const executionTime =
            circuit.depth * this.gateTimeMicros;

        const coherenceRatio =
            executionTime / this.coherenceTimeMicros;

        const coherencePenalty =
            Math.exp(-coherenceRatio);

        return {
            estimatedSuccess,
            estimatedExecutionMicros: executionTime,
            coherenceRatio,
            estimatedShotsWithinErrorBudget:
                Math.floor(shots * estimatedSuccess * coherencePenalty)
        };
    }
}

class DeviceRegistry {
    constructor() {
        this.devices = new Map();
    }

    register(device) {
        if (this.devices.has(device.id)) {
            throw new NISQError(
                `Duplicate device: ${device.id}`
            );
        }

        this.devices.set(device.id, device);
    }

    get(deviceId) {
        const device = this.devices.get(deviceId);

        if (!device) {
            throw new NISQError(
                `Unknown device: ${deviceId}`,
                'DEVICE_NOT_FOUND'
            );
        }

        return device;
    }

    select(circuit, shots, minimumSuccess = 0.5) {
        const candidates = [...this.devices.values()]
            .filter(device => device.supports(circuit))
            .map(device => ({
                device,
                estimate: device.estimate(circuit, shots)
            }))
            .filter(item =>
                item.estimate.estimatedSuccess >= minimumSuccess
            )
            .sort((a, b) =>
                b.estimate.estimatedSuccess -
                a.estimate.estimatedSuccess
            );

        if (candidates.length === 0) {
            throw new NISQError(
                'No compatible device satisfies the noise policy',
                'NO_ELIGIBLE_DEVICE'
            );
        }

        return candidates[0];
    }
}

class QuantumJob {
    constructor(circuit, device, shots, estimate) {
        this.id = randomUUID();
        this.circuit = circuit;
        this.device = device;
        this.shots = shots;
        this.estimate = estimate;
        this.status = JobStatus.QUEUED;
        this.createdAt = new Date();
        this.startedAt = null;
        this.finishedAt = null;
        this.error = null;
        this.result = null;
    }

    transition(nextStatus) {
        const allowed = {
            QUEUED: [
                JobStatus.RUNNING,
                JobStatus.CANCELLED
            ],
            RUNNING: [
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED
            ],
            COMPLETED: [],
            FAILED: [],
            CANCELLED: []
        };

        if (!allowed[this.status].includes(nextStatus)) {
            throw new NISQError(
                `Invalid transition ${this.status} -> ${nextStatus}`
            );
        }

        this.status = nextStatus;

        if (nextStatus === JobStatus.RUNNING) {
            this.startedAt = new Date();
        }

        if ([
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED
        ].includes(nextStatus)) {
            this.finishedAt = new Date();
        }
    }
}

class QuantumScheduler extends EventEmitter {
    constructor(registry, {
        concurrency = 2,
        minimumSuccess = 0.5
    } = {}) {
        super();

        if (!Number.isInteger(concurrency) || concurrency < 1) {
            throw new NISQError('Concurrency must be positive');
        }

        this.registry = registry;
        this.concurrency = concurrency;
        this.minimumSuccess = minimumSuccess;
        this.queue = [];
        this.jobs = new Map();
        this.activeCount = 0;
        this.cancelled = new Set();
    }

    submit(circuit, shots = 1000) {
        circuit.validate();

        if (!Number.isInteger(shots) ||
            shots < 1 ||
            shots > 10_000_000) {
            throw new NISQError('Invalid shot count');
        }

        const snapshot = circuit.snapshot();

        const selection = this.registry.select(
            snapshot,
            shots,
            this.minimumSuccess
        );

        const job = new QuantumJob(
            snapshot,
            selection.device,
            shots,
            selection.estimate
        );

        this.jobs.set(job.id, job);
        this.queue.push(job);

        this.emit('job:queued', job);

        this.pump();

        return job.id;
    }

    cancel(jobId) {
        const job = this.jobs.get(jobId);

        if (!job) {
            throw new NISQError('Job does not exist');
        }

        if (job.status === JobStatus.QUEUED) {
            job.transition(JobStatus.CANCELLED);
            this.queue = this.queue.filter(
                queued => queued.id !== jobId
            );

            this.emit('job:cancelled', job);
            return true;
        }

        if (job.status === JobStatus.RUNNING) {
            this.cancelled.add(jobId);
            return true;
        }

        return false;
    }

    pump() {
        while (
            this.activeCount < this.concurrency &&
            this.queue.length > 0
        ) {
            const job = this.queue.shift();

            if (job.status !== JobStatus.QUEUED) {
                continue;
            }

            this.activeCount++;

            this.execute(job)
                .catch(error => {
                    if (job.status === JobStatus.RUNNING) {
                        job.error = error.message;
                        job.transition(JobStatus.FAILED);
                        this.emit('job:failed', job);
                    }
                })
                .finally(() => {
                    this.activeCount--;
                    this.pump();
                });
        }
    }

    async execute(job) {
        job.transition(JobStatus.RUNNING);
        this.emit('job:started', job);

        try {
            const estimate = job.estimate;

            // Simulated hardware latency; no real quantum hardware is used.
            const delay = Math.min(
                1000,
                Math.max(10, estimate.estimatedExecutionMicros / 10)
            );

            await new Promise(resolve => setTimeout(resolve, delay));

            if (this.cancelled.has(job.id)) {
                this.cancelled.delete(job.id);
                job.transition(JobStatus.CANCELLED);
                this.emit('job:cancelled', job);
                return;
            }

            const probability = estimate.estimatedSuccess;
            const expectedSuccessfulShots =
                job.shots * probability;

            job.result = {
                totalShots: job.shots,
                estimatedSuccessfulShots:
                    Math.round(expectedSuccessfulShots),
                estimatedSuccessProbability: probability,
                estimatedExecutionMicros:
                    estimate.estimatedExecutionMicros,
                deviceId: job.device.id,
                circuitName: job.circuit.name,
                circuitDepth: job.circuit.depth,
                simulationOnly: true
            };

            job.transition(JobStatus.COMPLETED);
            this.emit('job:completed', job);

        } catch (error) {
            job.error = error.message;

            if (job.status === JobStatus.RUNNING) {
                job.transition(JobStatus.FAILED);
            }

            throw error;
        }
    }

    getReport() {
        const jobs = [...this.jobs.values()];

        return {
            total: jobs.length,
            completed: jobs.filter(
                j => j.status === JobStatus.COMPLETED
            ).length,
            failed: jobs.filter(
                j => j.status === JobStatus.FAILED
            ).length,
            cancelled: jobs.filter(
                j => j.status === JobStatus.CANCELLED
            ).length,
            queued: jobs.filter(
                j => j.status === JobStatus.QUEUED
            ).length,
            running: jobs.filter(
                j => j.status === JobStatus.RUNNING
            ).length
        };
    }
}

function createSampleRegistry() {
    const registry = new DeviceRegistry();

    registry.register(new QuantumDevice({
        id: 'device-alpha',
        name: 'Superconducting QPU Alpha',
        qubitCount: 5,
        topology: [
            [0, 1], [1, 2], [2, 3], [3, 4]
        ],
        singleQubitError: 0.001,
        twoQubitError: 0.008,
        readoutError: 0.02,
        coherenceTimeMicros: 100,
        gateTimeMicros: 0.05
    }));

    registry.register(new QuantumDevice({
        id: 'device-beta',
        name: 'Superconducting QPU Beta',
        qubitCount: 8,
        topology: [
            [0, 1], [1, 2], [2, 3],
            [3, 4], [4, 5], [5, 6], [6, 7]
        ],
        singleQubitError: 0.002,
        twoQubitError: 0.015,
        readoutError: 0.03,
        coherenceTimeMicros: 150,
        gateTimeMicros: 0.04
    }));

    return registry;
}

async function main() {
    const registry = createSampleRegistry();

    const scheduler = new QuantumScheduler(registry, {
        concurrency: 2,
        minimumSuccess: 0.5
    });

    scheduler.on('job:completed', job => {
        console.log(
            `Completed ${job.id}:`,
            job.result
        );
    });

    scheduler.on('job:failed', job => {
        console.error(`Failed ${job.id}: ${job.error}`);
    });

    scheduler.on('job:cancelled', job => {
        console.log(`Cancelled ${job.id}`);
    });

    const bell = new QuantumCircuit('Bell experiment', 2)
        .h(0)
        .cnot(0, 1);

    const ghz = new QuantumCircuit('GHZ experiment', 4)
        .h(0)
        .cnot(0, 1)
        .cnot(1, 2)
        .cnot(2, 3);

    const jobIds = [
        scheduler.submit(bell, 5000),
        scheduler.submit(ghz, 5000)
    ];

    console.log('Submitted jobs:', jobIds);

    while (
        scheduler.getReport().queued > 0 ||
        scheduler.getReport().running > 0
    ) {
        await new Promise(resolve => setTimeout(resolve, 20));
    }

    const report = scheduler.getReport();

    console.log('\nScheduler report:', report);

    const completedJobs = [...scheduler.jobs.values()]
        .filter(job => job.status === JobStatus.COMPLETED);

    const output = {
        generatedAt: new Date().toISOString(),
        report,
        jobs: completedJobs.map(job => ({
            id: job.id,
            circuit: job.circuit.name,
            device: job.device.name,
            result: job.result
        }))
    };

    await fs.writeFile(
        'nisq-experiment-report.json',
        JSON.stringify(output, null, 2),
        { encoding: 'utf8', mode: 0o600 }
    );

    console.log('Report written successfully.');
}

function runSelfTests() {
    const circuit = new QuantumCircuit('Test', 2)
        .h(0)
        .cnot(0, 1);

    if (circuit.depth !== 2) {
        throw new Error('Circuit depth test failed');
    }

    if (circuit.twoQubitGateCount !== 1) {
        throw new Error('Two-qubit gate test failed');
    }

    const invalid = () => circuit.addGate('UNKNOWN', 0);

    try {
        invalid();
        throw new Error('Unsupported gate was accepted');
    } catch (error) {
        if (!(error instanceof NISQError)) {
            throw error;
        }
    }

    const registry = createSampleRegistry();
    const selection = registry.select(circuit.snapshot(), 1000);

    if (!selection.device.supports(circuit.snapshot())) {
        throw new Error('Device compatibility test failed');
    }

    console.log('JavaScript self-tests passed.');
}

module.exports = {
    QuantumCircuit,
    QuantumDevice,
    DeviceRegistry,
    QuantumScheduler,
    JobStatus,
    NISQError,
    runSelfTests
};

if (require.main === module) {
    const testMode = process.argv.includes('--test');

    if (testMode) {
        runSelfTests();
    } else {
        main().catch(error => {
            console.error('Execution failed:', error);
            process.exitCode = 1;
        });
    }
}
