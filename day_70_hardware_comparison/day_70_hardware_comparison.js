"use strict";

/*
 * Quantum Hardware Architecture Evaluation System
 *
 * Node.js 18+
 * No external dependencies.
 *
 * Uses:
 * - Immutable architecture profiles
 * - Map-based architecture registry
 * - Event-driven comparison notifications
 * - Asynchronous evaluation
 * - Application-specific evaluation policies
 * - JSON report generation
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");

const CRITERIA = Object.freeze([
    "gateSpeed",
    "coherence",
    "connectivity",
    "scalability",
    "engineeringMaturity",
    "controlIntegration",
    "errorCorrectionProgress"
]);

const DEFAULT_WEIGHTS = Object.freeze({
    gateSpeed: 0.15,
    coherence: 0.15,
    connectivity: 0.10,
    scalability: 0.20,
    engineeringMaturity: 0.15,
    controlIntegration: 0.10,
    errorCorrectionProgress: 0.15
});

function validateWeights(weights) {
    let total = 0;

    for (const criterion of CRITERIA) {
        const weight = weights[criterion];

        if (
            typeof weight !== "number" ||
            !Number.isFinite(weight) ||
            weight < 0
        ) {
            throw new TypeError(`Invalid weight: ${criterion}`);
        }

        total += weight;
    }

    if (Math.abs(total - 1) > 1e-9) {
        throw new RangeError("Weights must sum to 1.");
    }
}

function createArchitecture(data) {
    if (!data.name || typeof data.name !== "string") {
        throw new TypeError("Architecture name is required.");
    }

    for (const criterion of CRITERIA) {
        const score = data[criterion];

        if (
            !Number.isInteger(score) ||
            score < 1 ||
            score > 5
        ) {
            throw new RangeError(
                `${criterion} must be an integer from 1 to 5.`
            );
        }
    }

    if (
        !Array.isArray(data.strengths) ||
        !Array.isArray(data.limitations)
    ) {
        throw new TypeError("Strengths and limitations must be arrays.");
    }

    return Object.freeze({
        ...data,
        strengths: Object.freeze([...data.strengths]),
        limitations: Object.freeze([...data.limitations])
    });
}

class ArchitectureRegistry {
    #architectures = new Map();

    register(data) {
        const architecture = createArchitecture(data);
        const key = architecture.name.toLowerCase();

        if (this.#architectures.has(key)) {
            throw new Error(`Duplicate architecture: ${data.name}`);
        }

        this.#architectures.set(key, architecture);
    }

    get(name) {
        const result = this.#architectures.get(
            String(name).toLowerCase()
        );

        if (!result) {
            throw new Error(`Unknown architecture: ${name}`);
        }

        return result;
    }

    values() {
        return [...this.#architectures.values()];
    }
}

class EvaluationPolicy {
    constructor(weights = DEFAULT_WEIGHTS) {
        validateWeights(weights);
        this.weights = Object.freeze({ ...weights });
    }

    evaluate(architecture) {
        return Number(
            CRITERIA.reduce(
                (sum, criterion) =>
                    sum +
                    architecture[criterion] *
                    this.weights[criterion],
                0
            ).toFixed(3)
        );
    }
}

class QuantumHardwareService extends EventEmitter {
    constructor(registry, policy) {
        super();
        this.registry = registry;
        this.policy = policy;
        this.history = [];
    }

    async evaluateAll() {
        // Yield between evaluation batches to support asynchronous consumers.
        const architectures = this.registry.values();

        const results = await Promise.all(
            architectures.map(async architecture => {
                await Promise.resolve();

                return Object.freeze({
                    name: architecture.name,
                    physicalQubit: architecture.physicalQubit,
                    score: this.policy.evaluate(architecture),
                    evidenceStatus: architecture.evidenceStatus
                });
            })
        );

        results.sort((a, b) => b.score - a.score);

        this.history.push({
            evaluatedAt: new Date().toISOString(),
            count: results.length
        });

        this.emit("evaluationCompleted", results);

        return results;
    }

    compare(firstName, secondName) {
        const first = this.registry.get(firstName);
        const second = this.registry.get(secondName);

        const firstScore = this.policy.evaluate(first);
        const secondScore = this.policy.evaluate(second);

        const result = Object.freeze({
            first: first.name,
            second: second.name,
            firstScore,
            secondScore,
            difference: Number(
                (firstScore - secondScore).toFixed(3)
            )
        });

        this.emit("pairwiseComparison", result);

        return result;
    }

    assessApplication(name, application) {
        const architecture = this.registry.get(name);

        const requirements = {
            simulation: architecture.scalability,
            operation: architecture.gateSpeed,
            coherence: architecture.coherence,
            connectivity: architecture.connectivity,
            faultTolerance: architecture.errorCorrectionProgress
        };

        const average = Object.values(requirements)
            .reduce((sum, value) => sum + value, 0) /
            Object.keys(requirements).length;

        return {
            architecture: architecture.name,
            application,
            requirements,
            assessment:
                average >= 3.5
                    ? "Potentially suitable"
                    : "Requires further technical evaluation"
        };
    }
}

function loadArchitectures() {
    const registry = new ArchitectureRegistry();

    const profiles = [
        {
            name: "Superconducting",
            physicalQubit: "Josephson-junction circuit",
            environment: "Millikelvin cryogenic system",
            gateSpeed: 5,
            coherence: 2,
            connectivity: 3,
            scalability: 4,
            engineeringMaturity: 5,
            controlIntegration: 4,
            errorCorrectionProgress: 4,
            evidenceStatus: "Relatively mature",
            strengths: [
                "Fast gate operations",
                "Established fabrication processes",
                "Strong control integration"
            ],
            limitations: [
                "Dilution refrigerator requirements",
                "Coherence and calibration challenges"
            ]
        },
        {
            name: "Trapped Ion",
            physicalQubit: "Electromagnetically confined atomic ion",
            environment: "Ultra-high vacuum and lasers",
            gateSpeed: 2,
            coherence: 5,
            connectivity: 4,
            scalability: 3,
            engineeringMaturity: 4,
            controlIntegration: 3,
            errorCorrectionProgress: 4,
            evidenceStatus: "Established experimental ecosystem",
            strengths: [
                "Long coherence",
                "High-fidelity operations",
                "Flexible interactions"
            ],
            limitations: [
                "Slower gates",
                "Optical engineering complexity"
            ]
        },
        {
            name: "Neutral Atom",
            physicalQubit: "Laser-trapped neutral atom",
            environment: "Ultra-high vacuum and optical trapping",
            gateSpeed: 3,
            coherence: 4,
            connectivity: 5,
            scalability: 5,
            engineeringMaturity: 3,
            controlIntegration: 3,
            errorCorrectionProgress: 3,
            evidenceStatus: "Rapidly developing",
            strengths: [
                "Large atom arrays",
                "Flexible interaction geometry",
                "Potential register scalability"
            ],
            limitations: [
                "Atom loss",
                "Rydberg-state sensitivity",
                "Gate fidelity challenges"
            ]
        },
        {
            name: "Photonic",
            physicalQubit: "Single photons and optical modes",
            environment: "Optical systems; platform-dependent",
            gateSpeed: 4,
            coherence: 4,
            connectivity: 3,
            scalability: 4,
            engineeringMaturity: 2,
            controlIntegration: 3,
            errorCorrectionProgress: 3,
            evidenceStatus: "Developing",
            strengths: [
                "Optical networking compatibility",
                "Potential room-temperature operation",
                "Low environmental interaction in suitable modes"
            ],
            limitations: [
                "Photon loss",
                "Detector requirements",
                "Probabilistic operations in many designs"
            ]
        },
        {
            name: "Semiconductor Spin",
            physicalQubit: "Electron or nuclear spin",
            environment: "Cryogenic solid-state device",
            gateSpeed: 4,
            coherence: 4,
            connectivity: 2,
            scalability: 4,
            engineeringMaturity: 2,
            controlIntegration: 4,
            errorCorrectionProgress: 2,
            evidenceStatus: "Developing",
            strengths: [
                "Semiconductor fabrication compatibility",
                "Compact devices",
                "Potential electronic integration"
            ],
            limitations: [
                "Device variability",
                "Control complexity",
                "Connectivity constraints"
            ]
        },
        {
            name: "Topological",
            physicalQubit: "Proposed non-Abelian anyonic states",
            environment: "Platform-dependent specialized conditions",
            gateSpeed: 2,
            coherence: 5,
            connectivity: 2,
            scalability: 3,
            engineeringMaturity: 1,
            controlIntegration: 1,
            errorCorrectionProgress: 1,
            evidenceStatus: "Highly experimental; usable qubit unproven",
            strengths: [
                "Potential intrinsic protection from certain local errors"
            ],
            limitations: [
                "Experimental realization remains difficult",
                "Fault-tolerant operation unestablished"
            ]
        }
    ];

    for (const profile of profiles) {
        registry.register(profile);
    }

    return registry;
}

async function exportReport(results, filename) {
    const serialized = JSON.stringify(results, null, 2);

    await fs.writeFile(filename, serialized, {
        encoding: "utf8",
        flag: "w"
    });
}

async function main() {
    const registry = loadArchitectures();
    const policy = new EvaluationPolicy();
    const service = new QuantumHardwareService(registry, policy);

    service.on("evaluationCompleted", results => {
        console.log(`Evaluated ${results.length} architectures.`);
    });

    service.on("pairwiseComparison", result => {
        console.log(
            `Compared ${result.first} with ${result.second}.`
        );
    });

    const results = await service.evaluateAll();

    console.log("\nQUANTUM HARDWARE RANKING");
    console.log("Qualitative scores, not measured performance benchmarks.\n");

    results.forEach((item, index) => {
        console.log(
            `${index + 1}. ${item.name.padEnd(22)} ` +
            `Score: ${item.score}/5`
        );
        console.log(`   Physical qubit: ${item.physicalQubit}`);
        console.log(`   Evidence: ${item.evidenceStatus}`);
    });

    console.log("\nPAIRWISE COMPARISON");

    console.log(
        service.compare("Superconducting", "Trapped Ion")
    );

    console.log("\nAPPLICATION ASSESSMENT");

    console.log(
        service.assessApplication(
            "Neutral Atom",
            "Large programmable quantum simulation"
        )
    );

    await exportReport(
        results,
        "quantum_hardware_report.json"
    );

    console.log("\nReport exported successfully.");

    // Validate failure behavior.
    try {
        registry.get("Unknown Architecture");
    } catch (error) {
        console.log(`Expected validation: ${error.message}`);
    }

    try {
        new EvaluationPolicy({
            ...DEFAULT_WEIGHTS,
            gateSpeed: 5
        });
    } catch (error) {
        console.log(`Expected policy rejection: ${error.message}`);
    }
}

main().catch(error => {
    console.error("Evaluation failed:", error.message);
    process.exitCode = 1;
});
