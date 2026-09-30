/**
 * Quantum Circuits | Circuit Construction Fundamentals
 *
 * A dependency-free Node.js implementation that models circuit construction
 * as an event-driven workflow.
 *
 * This file emphasizes JavaScript-specific patterns:
 * - classes and immutable operation records
 * - event-driven circuit lifecycle
 * - asynchronous execution
 * - validation and policy checks
 * - state-vector simulation
 * - measurement sampling
 * - circuit serialization
 *
 * Run with:
 *   node quantum_circuit.js
 */

"use strict";

const TWO_PI = 2 * Math.PI;

function complex(real, imag = 0) {
    return { real, imag };
}

function add(a, b) {
    return complex(a.real + b.real, a.imag + b.imag);
}

function multiply(a, b) {
    return complex(
        a.real * b.real - a.imag * b.imag,
        a.real * b.imag + a.imag * b.real
    );
}

function scale(a, factor) {
    return complex(a.real * factor, a.imag * factor);
}

function magnitudeSquared(a) {
    return a.real * a.real + a.imag * a.imag;
}

function formatComplex(a) {
    const real = Math.abs(a.real) < 1e-10 ? 0 : a.real;
    const imag = Math.abs(a.imag) < 1e-10 ? 0 : a.imag;

    if (imag === 0) return real.toFixed(4);
    if (real === 0) return `${imag.toFixed(4)}i`;

    const sign = imag >= 0 ? "+" : "-";
    return `${real.toFixed(4)} ${sign} ${Math.abs(imag).toFixed(4)}i`;
}

function identity() {
    return [
        [complex(1), complex(0)],
        [complex(0), complex(1)]
    ];
}

function pauliX() {
    return [
        [complex(0), complex(1)],
        [complex(1), complex(0)]
    ];
}

function pauliZ() {
    return [
        [complex(1), complex(0)],
        [complex(0), complex(-1)]
    ];
}

function hadamard() {
    const value = 1 / Math.sqrt(2);
    return [
        [complex(value), complex(value)],
        [complex(value), complex(-value)]
    ];
}

function rotationY(theta) {
    const c = Math.cos(theta / 2);
    const s = Math.sin(theta / 2);

    return [
        [complex(c), complex(-s)],
        [complex(s), complex(c)]
    ];
}

function rotationZ(theta) {
    return [
        [
            complex(Math.cos(theta / 2), -Math.sin(theta / 2)),
            complex(0)
        ],
        [
            complex(0),
            complex(Math.cos(theta / 2), Math.sin(theta / 2))
        ]
    ];
}

function bitString(index, qubits) {
    return index.toString(2).padStart(qubits, "0");
}

function validateQubit(qubit, qubits) {
    if (!Number.isInteger(qubit)) {
        throw new TypeError("Qubit index must be an integer.");
    }
    if (qubit < 0 || qubit >= qubits) {
        throw new RangeError(
            `Qubit ${qubit} is outside the ${qubits}-qubit circuit.`
        );
    }
}

function validateDistinctQubits(control, target, qubits) {
    validateQubit(control, qubits);
    validateQubit(target, qubits);

    if (control === target) {
        throw new RangeError(
            "A controlled gate requires different control and target qubits."
        );
    }
}

function applySingleQubit(state, qubits, target, matrix) {
    validateQubit(target, qubits);

    const targetBit = 1 << (qubits - 1 - target);

    for (let index = 0; index < state.length; index++) {
        if ((index & targetBit) !== 0) continue;

        const zeroIndex = index;
        const oneIndex = index | targetBit;

        const a0 = state[zeroIndex];
        const a1 = state[oneIndex];

        state[zeroIndex] = add(
            multiply(matrix[0][0], a0),
            multiply(matrix[0][1], a1)
        );

        state[oneIndex] = add(
            multiply(matrix[1][0], a0),
            multiply(matrix[1][1], a1)
        );
    }
}

function applyControlledGate(state, qubits, control, target, matrix) {
    validateDistinctQubits(control, target, qubits);

    const controlBit = 1 << (qubits - 1 - control);
    const targetBit = 1 << (qubits - 1 - target);

    for (let index = 0; index < state.length; index++) {
        if ((index & controlBit) === 0) continue;
        if ((index & targetBit) !== 0) continue;

        const zeroIndex = index;
        const oneIndex = index | targetBit;

        const a0 = state[zeroIndex];
        const a1 = state[oneIndex];

        state[zeroIndex] = add(
            multiply(matrix[0][0], a0),
            multiply(matrix[0][1], a1)
        );

        state[oneIndex] = add(
            multiply(matrix[1][0], a0),
            multiply(matrix[1][1], a1)
        );
    }
}

class CircuitEventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }
        this.listeners.get(eventName).push(listener);
        return this;
    }

    emit(eventName, payload) {
        const listeners = this.listeners.get(eventName) ?? [];
        for (const listener of listeners) {
            listener(payload);
        }
    }
}

class QuantumCircuit {
    constructor(qubits, name = "unnamed-circuit") {
        if (!Number.isInteger(qubits) || qubits <= 0) {
            throw new RangeError("A circuit must contain at least one qubit.");
        }

        // A state-vector simulator needs 2^n amplitudes. This bound keeps
        // accidental browser or Node.js memory exhaustion under control.
        if (qubits > 12) {
            throw new RangeError(
                "This educational state-vector simulator supports at most 12 qubits."
            );
        }

        this.qubits = qubits;
        this.name = name;
        this.operations = [];
        this.events = new CircuitEventBus();
    }

    on(eventName, listener) {
        this.events.on(eventName, listener);
        return this;
    }

    addOperation(operation) {
        this.operations.push(Object.freeze({ ...operation }));
        this.events.emit("operationAdded", operation);
        return this;
    }

    h(target) {
        validateQubit(target, this.qubits);
        return this.addOperation({
            type: "single",
            name: "H",
            target,
            matrix: hadamard()
        });
    }

    x(target) {
        validateQubit(target, this.qubits);
        return this.addOperation({
            type: "single",
            name: "X",
            target,
            matrix: pauliX()
        });
    }

    z(target) {
        validateQubit(target, this.qubits);
        return this.addOperation({
            type: "single",
            name: "Z",
            target,
            matrix: pauliZ()
        });
    }

    ry(target, theta) {
        validateQubit(target, this.qubits);

        if (!Number.isFinite(theta)) {
            throw new TypeError("Rotation angle must be finite.");
        }

        return this.addOperation({
            type: "single",
            name: "RY",
            target,
            theta,
            matrix: rotationY(theta)
        });
    }

    rz(target, theta) {
        validateQubit(target, this.qubits);

        if (!Number.isFinite(theta)) {
            throw new TypeError("Rotation angle must be finite.");
        }

        return this.addOperation({
            type: "single",
            name: "RZ",
            target,
            theta,
            matrix: rotationZ(theta)
        });
    }

    cx(control, target) {
        validateDistinctQubits(control, target, this.qubits);

        return this.addOperation({
            type: "controlled",
            name: "CX",
            control,
            target,
            matrix: pauliX()
        });
    }

    cz(control, target) {
        validateDistinctQubits(control, target, this.qubits);

        return this.addOperation({
            type: "controlled",
            name: "CZ",
            control,
            target,
            matrix: pauliZ()
        });
    }

    validate() {
        const errors = [];

        if (this.operations.length === 0) {
            errors.push("Circuit contains no operations.");
        }

        for (const [index, operation] of this.operations.entries()) {
            try {
                if (operation.type === "single") {
                    validateQubit(operation.target, this.qubits);
                } else if (operation.type === "controlled") {
                    validateDistinctQubits(
                        operation.control,
                        operation.target,
                        this.qubits
                    );
                } else {
                    errors.push(`Operation ${index} has an unknown type.`);
                }
            } catch (error) {
                errors.push(`Operation ${index}: ${error.message}`);
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    execute() {
        const validation = this.validate();

        // Empty circuits can legitimately represent |00...0>, so validation
        // errors are checked separately from the mathematical execution.
        if (validation.errors.some(error => !error.includes("no operations"))) {
            throw new Error(validation.errors.join(" "));
        }

        const state = Array.from(
            { length: 2 ** this.qubits },
            () => complex(0)
        );
        state[0] = complex(1);

        this.events.emit("executionStarted", {
            circuit: this.name,
            operationCount: this.operations.length
        });

        for (const operation of this.operations) {
            if (operation.type === "single") {
                applySingleQubit(
                    state,
                    this.qubits,
                    operation.target,
                    operation.matrix
                );
            } else {
                applyControlledGate(
                    state,
                    this.qubits,
                    operation.control,
                    operation.target,
                    operation.matrix
                );
            }
        }

        this.events.emit("executionFinished", {
            circuit: this.name,
            state
        });

        return state;
    }

    probabilities() {
        const state = this.execute();
        const probabilities = new Map();

        let total = 0;
        for (const amplitude of state) {
            total += magnitudeSquared(amplitude);
        }

        if (Math.abs(total - 1) > 1e-9) {
            throw new Error(`State normalization failure: ${total}`);
        }

        state.forEach((amplitude, index) => {
            probabilities.set(
                bitString(index, this.qubits),
                magnitudeSquared(amplitude)
            );
        });

        return probabilities;
    }

    draw() {
        const lines = Array.from(
            { length: this.qubits },
            (_, q) => [`q${q}`]
        );

        for (const operation of this.operations) {
            for (let q = 0; q < this.qubits; q++) {
                if (operation.type === "controlled") {
                    if (q === operation.control) {
                        lines[q].push("─●─");
                    } else if (q === operation.target) {
                        lines[q].push("─X─");
                    } else {
                        lines[q].push("───");
                    }
                } else if (q === operation.target) {
                    lines[q].push(`-${operation.name.padStart(2, " ").slice(0, 3)}-`);
                } else {
                    lines[q].push("───");
                }
            }
        }

        return lines.map(parts => `${parts[0]}: ${parts.slice(1).join("")}`).join("\n");
    }

    serialize() {
        // Serialization deliberately excludes complex matrix objects. The
        // operation type and parameters are enough to reconstruct the circuit.
        return JSON.stringify({
            name: this.name,
            qubits: this.qubits,
            operations: this.operations.map(operation => ({
                type: operation.type,
                name: operation.name,
                target: operation.target,
                control: operation.control,
                theta: operation.theta
            }))
        }, null, 2);
    }

    async executeAsync() {
        // Yielding to the event loop models a real asynchronous execution
        // boundary, useful when a circuit is sent to a remote backend.
        await new Promise(resolve => setTimeout(resolve, 0));
        return this.execute();
    }
}

function printNonZeroState(state, qubits) {
    state.forEach((amplitude, index) => {
        if (magnitudeSquared(amplitude) > 1e-10) {
            console.log(
                `  |${bitString(index, qubits)}> = ${formatComplex(amplitude)}`
            );
        }
    });
}

function sample(probabilities, shots = 1000) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new RangeError("shots must be a positive integer.");
    }

    const entries = [...probabilities.entries()];
    const counts = new Map(entries.map(([state]) => [state, 0]));

    // Math.random is adequate for demonstrating probability sampling but
    // should not be treated as a cryptographic random source.
    for (let shot = 0; shot < shots; shot++) {
        const randomValue = Math.random();
        let cumulative = 0;

        for (const [state, probability] of entries) {
            cumulative += probability;

            if (randomValue <= cumulative) {
                counts.set(state, counts.get(state) + 1);
                break;
            }
        }
    }

    return counts;
}

async function bellCircuitDemo() {
    console.log("\n=== Event-driven Bell circuit ===");

    const circuit = new QuantumCircuit(2, "bell-state");

    circuit
        .on("operationAdded", operation => {
            console.log(
                `Added ${operation.name} on ${operation.control !== undefined
                    ? `q${operation.control},q${operation.target}`
                    : `q${operation.target}`}`
            );
        })
        .on("executionStarted", info => {
            console.log(
                `Executing ${info.circuit} with ${info.operationCount} operations`
            );
        })
        .on("executionFinished", () => {
            console.log("Execution completed.");
        });

    circuit.h(0).cx(0, 1);

    console.log(circuit.draw());

    const state = await circuit.executeAsync();
    printNonZeroState(state, circuit.qubits);

    console.log("Measurement probabilities:");
    for (const [basis, probability] of circuit.probabilities()) {
        if (probability > 1e-10) {
            console.log(`  ${basis}: ${probability.toFixed(3)}`);
        }
    }

    console.log("Serialized circuit:");
    console.log(circuit.serialize());
}

function parameterizedCircuitDemo() {
    console.log("\n=== Parameterized construction ===");

    const circuit = new QuantumCircuit(2, "parameterized-rotation");
    circuit
        .ry(0, Math.PI / 4)
        .ry(1, Math.PI / 3)
        .cx(0, 1)
        .rz(1, Math.PI / 5);

    const probabilities = circuit.probabilities();

    for (const [basis, probability] of probabilities) {
        if (probability > 1e-10) {
            console.log(`  |${basis}>: ${probability.toFixed(6)}`);
        }
    }
}

function validationDemo() {
    console.log("\n=== Circuit validation ===");

    try {
        new QuantumCircuit(2).cx(0, 0);
    } catch (error) {
        console.log(`Rejected invalid controlled gate: ${error.message}`);
    }

    try {
        new QuantumCircuit(1).ry(0, Number.NaN);
    } catch (error) {
        console.log(`Rejected invalid rotation: ${error.message}`);
    }

    const emptyCircuit = new QuantumCircuit(2);
    console.log("Empty circuit validation:", emptyCircuit.validate());
}

function scalingDemo() {
    console.log("\n=== State-vector scaling ===");

    for (let qubits = 1; qubits <= 8; qubits++) {
        const amplitudes = 2 ** qubits;
        const approximateBytes = amplitudes * 16;
        console.log(
            `${qubits} qubits -> ${amplitudes} amplitudes -> ` +
            `~${(approximateBytes / 1024).toFixed(1)} KiB`
        );
    }

    console.log(
        "The state-vector representation grows exponentially with qubit count."
    );
}

function runAssertions() {
    const xCircuit = new QuantumCircuit(1, "x-test").x(0);
    const xProbabilities = xCircuit.probabilities();

    if (xProbabilities.get("1") < 1 - 1e-9) {
        throw new Error("X gate test failed.");
    }

    const bell = new QuantumCircuit(2, "bell-test").h(0).cx(0, 1);
    const bellProbabilities = bell.probabilities();

    if (
        Math.abs(bellProbabilities.get("00") - 0.5) > 1e-9 ||
        Math.abs(bellProbabilities.get("11") - 0.5) > 1e-9
    ) {
        throw new Error("Bell-state probability test failed.");
    }

    console.log("JavaScript circuit tests passed.");
}

async function main() {
    console.log("QUANTUM CIRCUITS: CIRCUIT CONSTRUCTION FUNDAMENTALS");
    console.log("==================================================");

    runAssertions();
    await bellCircuitDemo();
    parameterizedCircuitDemo();
    validationDemo();
    scalingDemo();
}

main().catch(error => {
    console.error(`Execution failed: ${error.message}`);
    process.exitCode = 1;
});
