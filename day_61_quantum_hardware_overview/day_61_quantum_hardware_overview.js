'use strict';

const fs = require('node:fs/promises');

const QubitTechnology = Object.freeze({
    SUPERCONDUCTING: 'superconducting',
    TRAPPED_ION: 'trapped_ion',
    NEUTRAL_ATOM: 'neutral_atom',
    PHOTONIC: 'photonic',
    SPIN: 'spin'
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

class EventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }
        this.listeners.get(eventName).add(listener);
        return () => this.listeners.get(eventName)?.delete(listener);
    }

    emit(eventName, payload) {
        for (const listener of this.listeners.get(eventName) ?? []) {
            listener(payload);
        }
    }
}

class Qubit {
    constructor({ id, technology, coherenceUs, gateFidelity, readoutFidelity }) {
        this.id = id;
        this.technology = technology;
        this.coherenceUs = coherenceUs;
        this.gateFidelity = gateFidelity;
        this.readoutFidelity = readoutFidelity;
        this.validate();
    }

    validate() {
        if (!Number.isInteger(this.id) || this.id < 0) {
            throw new ValidationError('Qubit id must be a non-negative integer');
        }

        if (!Object.values(QubitTechnology).includes(this.technology)) {
            throw new ValidationError('Unknown qubit technology');
        }

        for (const [name, value] of [
            ['coherenceUs', this.coherenceUs],
            ['gateFidelity', this.gateFidelity],
            ['readoutFidelity', this.readoutFidelity]
        ]) {
            if (!Number.isFinite(value) || value <= 0) {
                throw new ValidationError(`${name} must be positive`);
            }
        }

        if (this.gateFidelity > 1 || this.readoutFidelity > 1) {
            throw new ValidationError('Fidelity cannot exceed 1');
        }
    }
}

class HardwareComponent {
    constructor(name, subsystem, constraints = []) {
        if (!name.trim()) {
            throw new ValidationError('Component name is required');
        }
        this.name = name;
        this.subsystem = subsystem;
        this.constraints = [...constraints];
    }
}

class QuantumProcessor {
    constructor({ name, technology, qubits, components }) {
        this.name = name;
        this.technology = technology;
        this.qubits = new Map(qubits.map(q => [q.id, q]));
        this.components = components;
        this.events = new EventBus();
        this.state = 'offline';
        this.validate();
    }

    validate() {
        if (!this.name.trim()) {
            throw new ValidationError('Processor name is required');
        }
        if (!this.qubits.size) {
            throw new ValidationError('Processor requires at least one qubit');
        }
        for (const qubit of this.qubits.values()) {
            if (qubit.technology !== this.technology) {
                throw new ValidationError(
                    `Qubit ${qubit.id} does not match processor technology`
                );
            }
        }
    }

    powerOn() {
        if (this.state !== 'offline') {
            throw new Error(`Cannot power on from state ${this.state}`);
        }
        this.state = 'warming';
        this.events.emit('stateChanged', { state: this.state });

        setTimeout(() => {
            this.state = 'ready';
            this.events.emit('stateChanged', { state: this.state });
        }, 10);
    }

    startExperiment(circuitDepth) {
        if (this.state !== 'ready') {
            throw new Error('Processor must be ready before an experiment');
        }

        if (!Number.isInteger(circuitDepth) || circuitDepth <= 0) {
            throw new ValidationError('Circuit depth must be a positive integer');
        }

        const coherenceBudget = Math.floor(
            [...this.qubits.values()]
                .reduce((sum, q) => sum + q.coherenceUs, 0) /
            this.qubits.size
        );

        const estimatedGateTimeUs = 0.22;
        const estimatedExecutionUs = circuitDepth * estimatedGateTimeUs;

        const withinCoherence =
            estimatedExecutionUs <= coherenceBudget;

        const result = {
            circuitDepth,
            coherenceBudgetUs: coherenceBudget,
            estimatedExecutionUs,
            withinCoherence,
            status: withinCoherence ? 'accepted' : 'rejected'
        };

        this.events.emit('experimentEvaluated', result);
        return result;
    }

    metrics() {
        const qubits = [...this.qubits.values()];
        return {
            processor: this.name,
            technology: this.technology,
            qubitCount: qubits.length,
            averageCoherenceUs:
                qubits.reduce((sum, q) => sum + q.coherenceUs, 0) / qubits.length,
            averageGateFidelity:
                qubits.reduce((sum, q) => sum + q.gateFidelity, 0) / qubits.length,
            averageReadoutFidelity:
                qubits.reduce((sum, q) => sum + q.readoutFidelity, 0) / qubits.length,
            state: this.state
        };
    }
}

class CalibrationScheduler {
    constructor(processor) {
        this.processor = processor;
        this.queue = [];
    }

    addTask(name, priority, durationMinutes) {
        if (!name.trim()) {
            throw new ValidationError('Calibration task name is required');
        }
        if (!Number.isInteger(priority) || priority < 1 || priority > 10) {
            throw new ValidationError('Priority must be between 1 and 10');
        }
        if (!Number.isFinite(durationMinutes) || durationMinutes <= 0) {
            throw new ValidationError('Duration must be positive');
        }

        this.queue.push({ name, priority, durationMinutes });
        this.queue.sort((a, b) => b.priority - a.priority);
    }

    nextTask() {
        return this.queue.shift() ?? null;
    }
}

function createSuperconductingProcessor() {
    const qubits = Array.from({ length: 6 }, (_, id) =>
        new Qubit({
            id,
            technology: QubitTechnology.SUPERCONDUCTING,
            coherenceUs: 80 - id * 2,
            gateFidelity: 0.999 - id * 0.00002,
            readoutFidelity: 0.985
        })
    );

    const components = [
        new HardwareComponent(
            'Dilution refrigerator',
            'cryogenics',
            ['millikelvin operating temperature', 'limited cooling power']
        ),
        new HardwareComponent(
            'Microwave control chain',
            'control',
            ['phase noise', 'pulse distortion', 'crosstalk']
        ),
        new HardwareComponent(
            'Quantum-limited amplifier',
            'readout',
            ['noise temperature', 'gain stability']
        ),
        new HardwareComponent(
            'FPGA controller',
            'classical control',
            ['timing latency', 'clock synchronization']
        )
    ];

    return new QuantumProcessor({
        name: 'Cryogenic Processor A',
        technology: QubitTechnology.SUPERCONDUCTING,
        qubits,
        components
    });
}

async function main() {
    const processor = createSuperconductingProcessor();

    processor.events.on('stateChanged', event => {
        console.log(`Processor state: ${event.state}`);
    });

    processor.events.on('experimentEvaluated', event => {
        console.log(
            `Experiment depth=${event.circuitDepth}, status=${event.status}`
        );
    });

    const scheduler = new CalibrationScheduler(processor);
    scheduler.addTask('Readout resonator calibration', 9, 20);
    scheduler.addTask('Single-qubit pulse calibration', 7, 35);
    scheduler.addTask('Two-qubit coupling calibration', 10, 45);

    console.log('Initial metrics:', processor.metrics());
    console.log('Next calibration:', scheduler.nextTask());

    processor.powerOn();

    await new Promise(resolve => setTimeout(resolve, 25));

    const experiment = processor.startExperiment(200);
    console.log('Experiment result:', experiment);

    const report = {
        metrics: processor.metrics(),
        experiment,
        remainingCalibrationTasks: scheduler.queue
    };

    await fs.writeFile(
        'quantum_hardware_report.json',
        JSON.stringify(report, null, 2),
        'utf8'
    );

    console.log('Report written to quantum_hardware_report.json');
}

main().catch(error => {
    console.error(`[ERROR] ${error.name}: ${error.message}`);
    process.exitCode = 1;
});
