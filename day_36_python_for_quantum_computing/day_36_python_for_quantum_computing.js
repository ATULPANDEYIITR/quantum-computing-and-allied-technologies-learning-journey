/**
 * Python for Quantum Computing: JavaScript Companion
 *
 * This file uses JavaScript to model quantum state vectors and provide
 * event-driven circuit behavior. It intentionally emphasizes JavaScript
 * features such as classes, Maps, callbacks, immutable-style state updates,
 * events, and asynchronous execution.
 *
 * Run with:
 *   node quantum_python_foundations.js
 */

"use strict";

// ---------------------------------------------------------------------------
// Numerical utilities
// ---------------------------------------------------------------------------

const TOLERANCE = 1e-10;

class Complex {
    constructor(real = 0, imaginary = 0) {
        this.real = real;
        this.imaginary = imaginary;
    }

    add(other) {
        return new Complex(
            this.real + other.real,
            this.imaginary + other.imaginary
        );
    }

    multiply(other) {
        return new Complex(
            this.real * other.real - this.imaginary * other.imaginary,
            this.real * other.imaginary + this.imaginary * other.real
        );
    }

    conjugate() {
        return new Complex(this.real, -this.imaginary);
    }

    magnitudeSquared() {
        return (
            this.real * this.real +
            this.imaginary * this.imaginary
        );
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    scale(value) {
        return new Complex(
            this.real * value,
            this.imaginary * value
        );
    }

    toString() {
        if (Math.abs(this.imaginary) < TOLERANCE) {
            return this.real.toFixed(4);
        }

        if (Math.abs(this.real) < TOLERANCE) {
            return `${this.imaginary.toFixed(4)}i`;
        }

        const sign = this.imaginary >= 0 ? "+" : "-";

        return (
            `${this.real.toFixed(4)} ${sign} ` +
            `${Math.abs(this.imaginary).toFixed(4)}i`
        );
    }
}

const C = (real, imaginary = 0) => new Complex(real, imaginary);

function vectorNorm(vector) {
    return Math.sqrt(
        vector.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        )
    );
}

function normalize(vector) {
    const norm = vectorNorm(vector);

    if (norm < TOLERANCE) {
        throw new Error("Cannot normalize the zero vector.");
    }

    return vector.map(amplitude => amplitude.scale(1 / norm));
}

function validateState(state) {
    if (!Array.isArray(state) || state.length === 0) {
        throw new Error("Quantum state must be a non-empty array.");
    }

    if ((state.length & (state.length - 1)) !== 0) {
        throw new Error("Quantum state length must be a power of two.");
    }

    const norm = vectorNorm(state);

    if (Math.abs(norm - 1) > TOLERANCE) {
        throw new Error(`Quantum state is not normalized: ${norm}`);
    }

    return state;
}

function basisState(bits) {
    if (!/^[01]+$/.test(bits)) {
        throw new Error("Basis state must contain only binary digits.");
    }

    const state = Array.from(
        { length: 2 ** bits.length },
        () => C(0)
    );

    state[parseInt(bits, 2)] = C(1);

    return state;
}

function formatState(state) {
    validateState(state);

    const qubits = Math.log2(state.length);
    const terms = [];

    state.forEach((amplitude, index) => {
        if (amplitude.magnitude() > TOLERANCE) {
            const bits = index.toString(2).padStart(qubits, "0");
            terms.push(`(${amplitude.toString()})|${bits}>`);
        }
    });

    return terms.join(" + ");
}

function probabilities(state) {
    validateState(state);

    return state.map(amplitude => amplitude.magnitudeSquared());
}

// ---------------------------------------------------------------------------
// Matrix operations
// ---------------------------------------------------------------------------

function matrixMultiply(matrix, vector) {
    if (matrix.length === 0 || matrix.length !== vector.length) {
        throw new Error("Matrix and vector dimensions do not match.");
    }

    return matrix.map(row => {
        if (row.length !== vector.length) {
            throw new Error("Matrix must be square.");
        }

        return row.reduce(
            (sum, value, column) => sum.add(value.multiply(vector[column])),
            C(0)
        );
    });
}

function matrixProduct(a, b) {
    if (a[0].length !== b.length) {
        throw new Error("Matrix dimensions are incompatible.");
    }

    return a.map(row =>
        b[0].map((_, column) =>
            row.reduce(
                (sum, value, index) =>
                    sum.add(value.multiply(b[index][column])),
                C(0)
            )
        )
    );
}

function conjugateTranspose(matrix) {
    return matrix[0].map((_, column) =>
        matrix.map(row => row[column].conjugate())
    );
}

function identity(size) {
    return Array.from(
        { length: size },
        (_, row) =>
            Array.from(
                { length: size },
                (_, column) => C(row === column ? 1 : 0)
            )
    );
}

function kroneckerProduct(a, b) {
    const result = [];

    for (const rowA of a) {
        for (const rowB of b) {
            const row = [];

            for (const valueA of rowA) {
                for (const valueB of rowB) {
                    row.push(valueA.multiply(valueB));
                }
            }

            result.push(row);
        }
    }

    return result;
}

// ---------------------------------------------------------------------------
// Quantum gates
// ---------------------------------------------------------------------------

const X = [
    [C(0), C(1)],
    [C(1), C(0)]
];

const Y = [
    [C(0), C(0, -1)],
    [C(0, 1), C(0)]
];

const Z = [
    [C(1), C(0)],
    [C(0), C(-1)]
];

const H = [
    [C(1 / Math.sqrt(2)), C(1 / Math.sqrt(2))],
    [C(1 / Math.sqrt(2)), C(-1 / Math.sqrt(2))]
];

const I = identity(2);

function applyGate(state, gate) {
    const result = matrixMultiply(gate, state);
    const norm = vectorNorm(result);

    if (Math.abs(norm - 1) > 1e-9) {
        throw new Error("Gate application changed state normalization.");
    }

    return result;
}

function probabilitiesToMap(state) {
    const probabilityMap = new Map();
    const qubits = Math.log2(state.length);

    probabilities(state).forEach((probability, index) => {
        if (probability > TOLERANCE) {
            probabilityMap.set(
                index.toString(2).padStart(qubits, "0"),
                probability
            );
        }
    });

    return probabilityMap;
}

// ---------------------------------------------------------------------------
// Measurement with cryptographically strong randomness where available
// ---------------------------------------------------------------------------

function randomUnitInterval() {
    if (
        typeof globalThis.crypto !== "undefined" &&
        typeof globalThis.crypto.getRandomValues === "function"
    ) {
        const values = new Uint32Array(1);
        globalThis.crypto.getRandomValues(values);
        return values[0] / 2 ** 32;
    }

    // Node.js can expose crypto.randomInt through require().
    try {
        const nodeCrypto = require("node:crypto");
        return nodeCrypto.randomInt(0, 2 ** 32) / 2 ** 32;
    } catch {
        return Math.random();
    }
}

function sampleMeasurement(state, shots = 1000) {
    validateState(state);

    if (!Number.isInteger(shots) || shots <= 0) {
        throw new Error("shots must be a positive integer.");
    }

    const probability = probabilities(state);
    const qubits = Math.log2(state.length);
    const counts = new Map();

    for (let shot = 0; shot < shots; shot += 1) {
        const random = randomUnitInterval();
        let cumulative = 0;
        let selected = probability.length - 1;

        for (let index = 0; index < probability.length; index += 1) {
            cumulative += probability[index];

            if (random <= cumulative) {
                selected = index;
                break;
            }
        }

        const bitstring = selected
            .toString(2)
            .padStart(qubits, "0");

        counts.set(
            bitstring,
            (counts.get(bitstring) ?? 0) + 1
        );
    }

    return Object.fromEntries(
        [...counts.entries()].sort()
    );
}

// ---------------------------------------------------------------------------
// Event-driven quantum circuit
// ---------------------------------------------------------------------------

class QuantumCircuit {
    constructor(qubits) {
        if (!Number.isInteger(qubits) || qubits <= 0) {
            throw new Error("Circuit size must be a positive integer.");
        }

        if (qubits > 16) {
            throw new Error(
                "This educational simulator limits circuits to 16 qubits."
            );
        }

        this.qubits = qubits;
        this.state = basisState("0".repeat(qubits));
        this.history = [];
        this.listeners = new Map();
    }

    on(eventName, callback) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        this.listeners.get(eventName).push(callback);
    }

    emit(eventName, payload) {
        const callbacks = this.listeners.get(eventName) ?? [];

        for (const callback of callbacks) {
            callback(payload);
        }
    }

    record(name) {
        this.history.push({
            name,
            timestamp: new Date().toISOString()
        });

        this.emit("operation", {
            name,
            state: this.state
        });
    }

    applySingleQubitGate(gate, target, name) {
        if (!Number.isInteger(target) ||
            target < 0 ||
            target >= this.qubits) {
            throw new RangeError("Target qubit is outside the circuit.");
        }

        const operators = [];

        for (let index = 0; index < this.qubits; index += 1) {
            operators.push(index === target ? gate : I);
        }

        let fullGate = operators[0];

        for (let index = 1; index < operators.length; index += 1) {
            fullGate = kroneckerProduct(fullGate, operators[index]);
        }

        this.state = applyGate(this.state, fullGate);
        this.record(`${name} q${target}`);
    }

    h(target) {
        this.applySingleQubitGate(H, target, "H");
    }

    x(target) {
        this.applySingleQubitGate(X, target, "X");
    }

    z(target) {
        this.applySingleQubitGate(Z, target, "Z");
    }

    cnot(control, target) {
        if (control === target) {
            throw new Error("CNOT control and target must differ.");
        }

        if (
            control < 0 ||
            control >= this.qubits ||
            target < 0 ||
            target >= this.qubits
        ) {
            throw new RangeError("CNOT qubit is outside the circuit.");
        }

        const dimension = 2 ** this.qubits;
        const operation = Array.from(
            { length: dimension },
            () => Array.from({ length: dimension }, () => C(0))
        );

        for (let column = 0; column < dimension; column += 1) {
            const bits = column
                .toString(2)
                .padStart(this.qubits, "0");

            let output = bits;

            if (bits[control] === "1") {
                const characters = bits.split("");
                characters[target] =
                    characters[target] === "0" ? "1" : "0";
                output = characters.join("");
            }

            const row = parseInt(output, 2);
            operation[row][column] = C(1);
        }

        this.state = applyGate(this.state, operation);
        this.record(`CNOT q${control}->q${target}`);
    }

    measure(shots = 1000) {
        const counts = sampleMeasurement(this.state, shots);

        this.emit("measurement", {
            shots,
            counts
        });

        return counts;
    }
}

// ---------------------------------------------------------------------------
// Asynchronous workflow
// ---------------------------------------------------------------------------

async function runCircuitExperiment() {
    const circuit = new QuantumCircuit(2);

    circuit.on("operation", event => {
        console.log(
            `Operation: ${event.name}; state = ${formatState(event.state)}`
        );
    });

    circuit.on("measurement", event => {
        console.log(
            `Measurement completed with ${event.shots} shots:`,
            event.counts
        );
    });

    circuit.h(0);
    await Promise.resolve();

    circuit.cnot(0, 1);
    await Promise.resolve();

    return circuit.measure(1000);
}

// ---------------------------------------------------------------------------
// Numerical objective for a simple variational calculation
// ---------------------------------------------------------------------------

function ry(theta) {
    const half = theta / 2;

    return [
        [C(Math.cos(half)), C(-Math.sin(half))],
        [C(Math.sin(half)), C(Math.cos(half))]
    ];
}

function expectation(state, operator) {
    const transformed = matrixMultiply(operator, state);
    const conjugate = state.map(amplitude => amplitude.conjugate());

    return conjugate.reduce(
        (sum, amplitude, index) =>
            sum.add(amplitude.multiply(transformed[index])),
        C(0)
    );
}

function variationalEnergy(theta) {
    const state = applyGate(basisState("0"), ry(theta));
    return expectation(state, Z).real;
}

function gridSearch(objective, start, stop, samples) {
    let bestTheta = start;
    let bestValue = Infinity;

    for (let index = 0; index < samples; index += 1) {
        const fraction = index / (samples - 1);
        const theta = start + (stop - start) * fraction;
        const value = objective(theta);

        if (value < bestValue) {
            bestValue = value;
            bestTheta = theta;
        }
    }

    return {
        theta: bestTheta,
        value: bestValue
    };
}

// ---------------------------------------------------------------------------
// Executable demonstration
// ---------------------------------------------------------------------------

async function main() {
    console.log("Python for Quantum Computing: JavaScript Companion");
    console.log("Complex amplitude:", C(1, 0.5).toString());

    console.log("\nBasis state:");
    console.log(formatState(basisState("10")));

    console.log("\nHadamard superposition:");

    const plus = applyGate(
        basisState("0"),
        H
    );

    console.log(formatState(plus));
    console.log(probabilitiesToMap(plus));
    console.log(sampleMeasurement(plus, 1000));

    console.log("\nBell-state experiment:");

    const bellCircuit = new QuantumCircuit(2);
    bellCircuit.h(0);
    bellCircuit.cnot(0, 1);

    console.log(formatState(bellCircuit.state));
    console.log(sampleMeasurement(bellCircuit.state, 1000));

    console.log("\nEvent-driven circuit:");
    await runCircuitExperiment();

    console.log("\nVariational calculation:");

    const result = gridSearch(
        variationalEnergy,
        0,
        2 * Math.PI,
        1001
    );

    console.log(
        `Minimum sampled energy = ${result.value.toFixed(6)} ` +
        `at theta = ${result.theta.toFixed(6)}`
    );

    console.log("\nState-vector scaling:");

    for (let qubits = 1; qubits <= 10; qubits += 1) {
        const amplitudes = 2 ** qubits;
        const bytes = amplitudes * 16;

        console.log(
            `${qubits} qubits -> ${amplitudes} amplitudes -> ` +
            `${(bytes / 1024 / 1024).toFixed(4)} MiB`
        );
    }
}

main().catch(error => {
    console.error("Experiment failed:", error.message);
    process.exitCode = 1;
});
