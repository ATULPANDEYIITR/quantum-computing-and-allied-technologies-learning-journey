"use strict";

/*
 * Quantum Machine Learning Landscape
 *
 * Event-driven QML experiment orchestration and policy evaluation.
 *
 * Covers:
 * - QML algorithm taxonomy
 * - Quantum data encoding
 * - Circuit configuration
 * - Hybrid quantum-classical execution
 * - Quantum kernel methods
 * - Backend selection
 * - Noise and shot-aware evaluation
 * - Experiment lifecycle
 * - Resource and governance policies
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");
const fs = require("node:fs/promises");

// ============================================================
// 1. QML DOMAIN TAXONOMY
// ============================================================

const AlgorithmFamily = Object.freeze({
    VQC: "variational_quantum_classifier",
    QNN: "quantum_neural_network",
    KERNEL: "quantum_kernel",
    GENERATIVE: "quantum_generative_model",
    REINFORCEMENT: "quantum_reinforcement_learning",
    VQE: "variational_quantum_eigensolver",
    QAOA: "quantum_approximate_optimization",
    INSPIRED: "quantum_inspired_classical"
});

const Backend = Object.freeze({
    STATEVECTOR: "statevector",
    SHOT: "shot_based",
    NOISY: "noisy_simulator",
    HARDWARE: "quantum_hardware"
});

const ExperimentState = Object.freeze({
    CREATED: "created",
    VALIDATED: "validated",
    QUEUED: "queued",
    RUNNING: "running",
    COMPLETED: "completed",
    FAILED: "failed",
    CANCELLED: "cancelled"
});

const ALGORITHM_CATALOG = Object.freeze({
    [AlgorithmFamily.VQC]: {
        description: "Parameterized circuits for supervised learning",
        training: "Hybrid optimization",
        strengths: ["Small circuits", "Trainable parameters"],
        limitations: ["Barren plateaus", "Noise sensitivity"]
    },
    [AlgorithmFamily.QNN]: {
        description: "Quantum circuits integrated into neural architectures",
        training: "Parameterized circuit optimization",
        strengths: ["Quantum feature transformations"],
        limitations: ["Limited hardware resources"]
    },
    [AlgorithmFamily.KERNEL]: {
        description: "Quantum feature maps and fidelity-based kernels",
        training: "Classical kernel learning",
        strengths: ["Nonlinear feature representations"],
        limitations: ["Kernel estimation cost"]
    },
    [AlgorithmFamily.GENERATIVE]: {
        description: "Quantum probability distribution generation",
        training: "Distribution matching",
        strengths: ["Quantum state sampling"],
        limitations: ["Sampling and optimization difficulty"]
    },
    [AlgorithmFamily.REINFORCEMENT]: {
        description: "Quantum parameterized policies and value models",
        training: "Reward-driven optimization",
        strengths: ["Hybrid policy representations"],
        limitations: ["Sampling overhead"]
    },
    [AlgorithmFamily.VQE]: {
        description: "Variational approximation of ground-state energy",
        training: "Energy minimization",
        strengths: ["Quantum chemistry applications"],
        limitations: ["Measurement cost"]
    },
    [AlgorithmFamily.QAOA]: {
        description: "Parameterized circuits for combinatorial optimization",
        training: "Alternating circuit optimization",
        strengths: ["Structured optimization"],
        limitations: ["Depth and hardware constraints"]
    },
    [AlgorithmFamily.INSPIRED]: {
        description: "Classical algorithms motivated by quantum methods",
        training: "Classical optimization",
        strengths: ["No quantum hardware requirement"],
        limitations: ["Not quantum computation"]
    }
});

// ============================================================
// 2. VALIDATION AND DOMAIN ERRORS
// ============================================================

class QMLError extends Error {
    constructor(message, code = "QML_ERROR") {
        super(message);
        this.name = "QMLError";
        this.code = code;
    }
}

function requireInteger(value, name, minimum, maximum) {
    if (
        !Number.isSafeInteger(value) ||
        value < minimum ||
        value > maximum
    ) {
        throw new QMLError(
            `${name} must be an integer between ${minimum} and ${maximum}.`,
            "INVALID_CONFIGURATION"
        );
    }
}

function validateFeatures(features) {
    if (!Array.isArray(features) || features.length === 0) {
        throw new QMLError("Features must be a non-empty array.");
    }

    if (features.some(
        value =>
            typeof value !== "number" ||
            !Number.isFinite(value) ||
            value < -1 ||
            value > 1
    )) {
        throw new QMLError("Features must be finite values in [-1, 1].");
    }

    return [...features];
}

// ============================================================
// 3. QUANTUM STATE AND CIRCUIT OPERATIONS
// ============================================================

class StateVector {
    constructor(qubits) {
        requireInteger(qubits, "Qubits", 1, 12);

        this.qubits = qubits;
        this.amplitudes = new Array(2 ** qubits).fill(null)
            .map(() => ({ re: 0, im: 0 }));

        this.amplitudes[0] = { re: 1, im: 0 };
    }

    applyRY(target, angle) {
        requireInteger(target, "Target", 0, this.qubits - 1);

        if (!Number.isFinite(angle)) {
            throw new QMLError("Rotation angle must be finite.");
        }

        const c = Math.cos(angle / 2);
        const s = Math.sin(angle / 2);
        const mask = 1 << target;

        for (let i = 0; i < this.amplitudes.length; i++) {
            if (i & mask) continue;

            const a = this.amplitudes[i];
            const b = this.amplitudes[i | mask];

            this.amplitudes[i] = {
                re: c * a.re - s * b.re,
                im: c * a.im - s * b.im
            };

            this.amplitudes[i | mask] = {
                re: s * a.re + c * b.re,
                im: s * a.im + c * b.im
            };
        }
    }

    applyCNOT(control, target) {
        requireInteger(control, "Control", 0, this.qubits - 1);
        requireInteger(target, "Target", 0, this.qubits - 1);

        if (control === target) {
            throw new QMLError("CNOT control and target must differ.");
        }

        const controlMask = 1 << control;
        const targetMask = 1 << target;

        for (let i = 0; i < this.amplitudes.length; i++) {
            if ((i & controlMask) && !(i & targetMask)) {
                const other = i | targetMask;

                [
                    this.amplitudes[i],
                    this.amplitudes[other]
                ] = [
                    this.amplitudes[other],
                    this.amplitudes[i]
                ];
            }
        }
    }

    expectationZ(target) {
        requireInteger(target, "Measurement target", 0, this.qubits - 1);

        const mask = 1 << target;

        return this.amplitudes.reduce((total, amplitude, index) => {
            const probability =
                amplitude.re ** 2 + amplitude.im ** 2;

            return total + ((index & mask) ? -1 : 1) * probability;
        }, 0);
    }

    probabilities() {
        return this.amplitudes.map(
            a => a.re ** 2 + a.im ** 2
        );
    }
}

// ============================================================
// 4. QUANTUM FEATURE MAP
// ============================================================

class FeatureMap {
    static encode(features) {
        const values = validateFeatures(features);
        const state = new StateVector(values.length);

        values.forEach((value, index) => {
            state.applyRY(index, Math.PI * value);
        });

        // Entanglement creates feature interactions.
        for (let index = 0; index < values.length - 1; index++) {
            state.applyCNOT(index, index + 1);
        }

        return state;
    }

    static fidelity(first, second) {
        const a = FeatureMap.encode(first);
        const b = FeatureMap.encode(second);

        if (a.qubits !== b.qubits) {
            throw new QMLError("Feature dimensions must match.");
        }

        let real = 0;
        let imaginary = 0;

        for (let i = 0; i < a.amplitudes.length; i++) {
            const x = a.amplitudes[i];
            const y = b.amplitudes[i];

            real += x.re * y.re + x.im * y.im;
            imaginary += x.re * y.im - x.im * y.re;
        }

        return real ** 2 + imaginary ** 2;
    }

    static kernelMatrix(dataset) {
        if (!Array.isArray(dataset) || dataset.length === 0) {
            throw new QMLError("Dataset cannot be empty.");
        }

        const dimensions = dataset[0].length;

        if (!dataset.every(row => row.length === dimensions)) {
            throw new QMLError("Dataset dimensions are inconsistent.");
        }

        return dataset.map((row, i) =>
            dataset.map((other, j) =>
                j < i
                    ? undefined
                    : FeatureMap.fidelity(row, other)
            )
        ).map((row, i, matrix) =>
            row.map((value, j) =>
                j < i ? matrix[j][i] : value
            )
        );
    }
}

// ============================================================
// 5. EXPERIMENT DEFINITION
// ============================================================

class QMLExperiment {
    constructor(configuration) {
        const {
            name,
            algorithm,
            qubits,
            depth,
            shots,
            backend,
            datasetSize,
            learningRate
        } = configuration;

        if (typeof name !== "string" || !name.trim()) {
            throw new QMLError("Experiment name is required.");
        }

        if (!Object.values(AlgorithmFamily).includes(algorithm)) {
            throw new QMLError("Unsupported QML algorithm.");
        }

        if (!Object.values(Backend).includes(backend)) {
            throw new QMLError("Unsupported backend.");
        }

        requireInteger(qubits, "Qubits", 1, 100);
        requireInteger(depth, "Depth", 1, 10000);
        requireInteger(shots, "Shots", 1, 10000000);
        requireInteger(datasetSize, "Dataset size", 1, 1000000);

        if (
            typeof learningRate !== "number" ||
            !Number.isFinite(learningRate) ||
            learningRate <= 0
        ) {
            throw new QMLError("Learning rate must be positive.");
        }

        this.id = crypto.randomUUID();
        this.name = name.trim();
        this.algorithm = algorithm;
        this.qubits = qubits;
        this.depth = depth;
        this.shots = shots;
        this.backend = backend;
        this.datasetSize = datasetSize;
        this.learningRate = learningRate;

        this.state = ExperimentState.CREATED;
        this.metrics = null;
        this.error = null;
        this.createdAt = new Date().toISOString();
    }

    transition(next) {
        const allowed = {
            created: ["validated", "cancelled"],
            validated: ["queued", "cancelled"],
            queued: ["running", "cancelled"],
            running: ["completed", "failed", "cancelled"],
            completed: [],
            failed: [],
            cancelled: []
        };

        if (!allowed[this.state].includes(next)) {
            throw new QMLError(
                `Invalid transition: ${this.state} -> ${next}`,
                "INVALID_STATE_TRANSITION"
            );
        }

        const previous = this.state;
        this.state = next;

        return { previous, next };
    }
}

// ============================================================
// 6. RESOURCE AND BACKEND POLICIES
// ============================================================

class ResourcePolicy {
    constructor({
        maximumQubits = 20,
        maximumDepth = 200,
        maximumShots = 100000,
        maximumDatasetSize = 10000,
        allowHardware = false
    } = {}) {
        this.maximumQubits = maximumQubits;
        this.maximumDepth = maximumDepth;
        this.maximumShots = maximumShots;
        this.maximumDatasetSize = maximumDatasetSize;
        this.allowHardware = allowHardware;
    }

    evaluate(experiment) {
        const failures = [];

        if (experiment.qubits > this.maximumQubits) {
            failures.push("Qubit budget exceeded.");
        }

        if (experiment.depth > this.maximumDepth) {
            failures.push("Circuit depth exceeds policy.");
        }

        if (experiment.shots > this.maximumShots) {
            failures.push("Measurement budget exceeded.");
        }

        if (experiment.datasetSize > this.maximumDatasetSize) {
            failures.push("Dataset budget exceeded.");
        }

        if (
            experiment.backend === Backend.HARDWARE &&
            !this.allowHardware
        ) {
            failures.push("Quantum hardware execution is prohibited.");
        }

        if (
            experiment.backend === Backend.STATEVECTOR &&
            experiment.qubits > 30
        ) {
            failures.push("Statevector memory requirement is excessive.");
        }

        return {
            allowed: failures.length === 0,
            failures
        };
    }
}

// ============================================================
// 7. EVENT-DRIVEN EXPERIMENT SERVICE
// ============================================================

class ExperimentService extends EventEmitter {
    constructor(policy) {
        super();

        this.policy = policy;
        this.experiments = new Map();
    }

    register(experiment) {
        if (this.experiments.has(experiment.id)) {
            throw new QMLError("Duplicate experiment identifier.");
        }

        this.experiments.set(experiment.id, experiment);

        this.emit("experiment:created", {
            id: experiment.id,
            name: experiment.name
        });

        return experiment.id;
    }

    async validate(id) {
        const experiment = this.get(id);
        const result = this.policy.evaluate(experiment);

        if (!result.allowed) {
            experiment.error = result.failures.join("; ");

            this.emit("experiment:rejected", {
                id,
                failures: result.failures
            });

            throw new QMLError(experiment.error, "POLICY_REJECTION");
        }

        experiment.transition(ExperimentState.VALIDATED);

        this.emit("experiment:validated", { id });

        return result;
    }

    get(id) {
        const experiment = this.experiments.get(id);

        if (!experiment) {
            throw new QMLError("Experiment not found.", "NOT_FOUND");
        }

        return experiment;
    }

    async execute(id, executor) {
        const experiment = this.get(id);

        try {
            if (experiment.state === ExperimentState.CREATED) {
                await this.validate(id);
            }

            experiment.transition(ExperimentState.QUEUED);

            this.emit("experiment:queued", { id });

            experiment.transition(ExperimentState.RUNNING);

            this.emit("experiment:started", { id });

            // Yield execution to the event loop.
            await new Promise(resolve => setImmediate(resolve));

            const result = await executor(experiment);

            if (
                !result ||
                typeof result !== "object" ||
                !Number.isFinite(result.accuracy) ||
                result.accuracy < 0 ||
                result.accuracy > 1
            ) {
                throw new QMLError("Executor returned invalid metrics.");
            }

            experiment.metrics = Object.freeze({
                ...result,
                completedAt: new Date().toISOString()
            });

            experiment.transition(ExperimentState.COMPLETED);

            this.emit("experiment:completed", {
                id,
                metrics: experiment.metrics
            });

            return experiment.metrics;

        } catch (error) {
            if (experiment.state === ExperimentState.RUNNING) {
                experiment.transition(ExperimentState.FAILED);
            } else if (
                experiment.state === ExperimentState.QUEUED
            ) {
                experiment.transition(ExperimentState.CANCELLED);
            }

            experiment.error = error.message;

            this.emit("experiment:failed", {
                id,
                message: error.message
            });

            throw error;
        }
    }

    cancel(id) {
        const experiment = this.get(id);

        experiment.transition(ExperimentState.CANCELLED);

        this.emit("experiment:cancelled", { id });
    }

    report() {
        return Array.from(this.experiments.values()).map(item => ({
            id: item.id,
            name: item.name,
            algorithm: item.algorithm,
            backend: item.backend,
            state: item.state,
            metrics: item.metrics,
            error: item.error
        }));
    }
}

// ============================================================
// 8. EXECUTION STRATEGY
// ============================================================

class QuantumExecutionStrategy {
    static async run(experiment) {
        const state = new StateVector(experiment.qubits);

        for (let index = 0; index < experiment.qubits; index++) {
            state.applyRY(
                index,
                Math.PI / (index + 2)
            );
        }

        for (let index = 0; index < experiment.qubits - 1; index++) {
            state.applyCNOT(index, index + 1);
        }

        const expectation = state.expectationZ(0);

        // Approximate shot-based uncertainty.
        const standardError = Math.sqrt(
            Math.max(0, 1 - expectation ** 2) / experiment.shots
        );

        return {
            accuracy: Math.max(
                0,
                Math.min(1, (expectation + 1) / 2)
            ),
            expectation,
            standardError,
            qubits: experiment.qubits,
            circuitDepth: experiment.depth,
            shots: experiment.shots
        };
    }
}

// ============================================================
// 9. QML LANDSCAPE DECISION SUPPORT
// ============================================================

function chooseQMLApproach({
    problem,
    datasetSize,
    qubitBudget,
    hardwareAvailable
}) {
    requireInteger(datasetSize, "Dataset size", 1, 100000000);
    requireInteger(qubitBudget, "Qubit budget", 1, 1000);

    const decisions = {
        supervised: qubitBudget <= 20
            ? AlgorithmFamily.VQC
            : AlgorithmFamily.QNN,

        similarity: datasetSize <= 5000
            ? AlgorithmFamily.KERNEL
            : AlgorithmFamily.INSPIRED,

        combinatorial: hardwareAvailable
            ? AlgorithmFamily.QAOA
            : AlgorithmFamily.INSPIRED,

        chemistry: qubitBudget >= 2
            ? AlgorithmFamily.VQE
            : AlgorithmFamily.INSPIRED,

        generative: qubitBudget >= 2
            ? AlgorithmFamily.GENERATIVE
            : AlgorithmFamily.INSPIRED,

        reinforcement: qubitBudget >= 2
            ? AlgorithmFamily.REINFORCEMENT
            : AlgorithmFamily.INSPIRED
    };

    if (!decisions[problem]) {
        throw new QMLError("Unknown problem category.");
    }

    return {
        selected: decisions[problem],
        problem,
        hardwareAvailable,
        datasetSize,
        qubitBudget,
        requiresEmpiricalBenchmarking: true
    };
}

// ============================================================
// 10. DEMONSTRATION
// ============================================================

async function main() {
    console.log("QUANTUM MACHINE LEARNING EXPERIMENT PLATFORM");

    console.log("\nALGORITHM LANDSCAPE");

    for (const [name, details] of Object.entries(ALGORITHM_CATALOG)) {
        console.log(`\n${name}`);
        console.log(details.description);
        console.log("Limitations:", details.limitations.join(", "));
    }

    console.log("\nQUANTUM FEATURE MAP");

    const fidelity = FeatureMap.fidelity(
        [-0.5, 0.4],
        [0.5, -0.4]
    );

    console.log("State fidelity:", fidelity.toFixed(6));

    console.log("\nQUANTUM KERNEL");

    const kernel = FeatureMap.kernelMatrix([
        [-0.8, 0.1],
        [-0.4, 0.3],
        [0.5, -0.2]
    ]);

    console.log(kernel.map(row =>
        row.map(value => Number(value.toFixed(4)))
    ));

    const policy = new ResourcePolicy({
        maximumQubits: 12,
        maximumDepth: 100,
        maximumShots: 50000,
        maximumDatasetSize: 10000,
        allowHardware: false
    });

    const service = new ExperimentService(policy);

    // Event-driven monitoring.
    const events = [
        "experiment:created",
        "experiment:validated",
        "experiment:queued",
        "experiment:started",
        "experiment:completed",
        "experiment:rejected",
        "experiment:failed"
    ];

    events.forEach(event => {
        service.on(event, payload => {
            console.log(`[EVENT] ${event}`, payload);
        });
    });

    const experiment = new QMLExperiment({
        name: "Quantum Feature Encoding Benchmark",
        algorithm: AlgorithmFamily.VQC,
        qubits: 3,
        depth: 4,
        shots: 2048,
        backend: Backend.STATEVECTOR,
        datasetSize: 100,
        learningRate: 0.01
    });

    service.register(experiment);

    console.log("\nEXECUTING EXPERIMENT");

    const metrics = await service.execute(
        experiment.id,
        QuantumExecutionStrategy.run
    );

    console.log("\nEXPERIMENT METRICS");
    console.log(metrics);

    console.log("\nAPPROACH SELECTION");

    console.log(chooseQMLApproach({
        problem: "supervised",
        datasetSize: 1000,
        qubitBudget: 8,
        hardwareAvailable: false
    }));

    console.log("\nEXPERIMENT REPORT");

    const report = service.report();

    console.log(JSON.stringify(report, null, 2));

    await fs.writeFile(
        "qml_platform_report.json",
        JSON.stringify(report, null, 2),
        { encoding: "utf8", mode: 0o600 }
    );

    console.log("\nReport saved to qml_platform_report.json");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
