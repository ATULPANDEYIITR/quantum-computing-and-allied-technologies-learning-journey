"use strict";

/*
 * Quantum circuit programming with an explicit complex state vector.
 * Run with Node.js. Qubit 0 is the least significant basis-state bit.
 */

const SQRT2 = Math.sqrt(2);

class Complex {
    constructor(re = 0, im = 0) {
        this.re = re;
        this.im = im;
    }

    add(other) {
        return new Complex(this.re + other.re, this.im + other.im);
    }

    sub(other) {
        return new Complex(this.re - other.re, this.im - other.im);
    }

    mul(other) {
        return new Complex(
            this.re * other.re - this.im * other.im,
            this.re * other.im + this.im * other.re
        );
    }

    scale(value) {
        return new Complex(this.re * value, this.im * value);
    }

    conjugate() {
        return new Complex(this.re, -this.im);
    }

    abs2() {
        return this.re * this.re + this.im * this.im;
    }

    toString() {
        return `${this.re.toFixed(5)}${this.im < 0 ? "" : "+"}${this.im.toFixed(5)}i`;
    }
}

const C = (re, im = 0) => new Complex(re, im);
const ZERO = C(0);
const ONE = C(1);
const IMAGINARY = C(0, 1);

const GATES = {
    I: [[ONE, ZERO], [ZERO, ONE]],
    X: [[ZERO, ONE], [ONE, ZERO]],
    Y: [[ZERO, C(0, -1)], [IMAGINARY, ZERO]],
    Z: [[ONE, ZERO], [ZERO, C(-1)]],
    H: [[C(1 / SQRT2), C(1 / SQRT2)], [C(1 / SQRT2), C(-1 / SQRT2)]]
};

function multiplyMatrices(a, b) {
    if (!a.length || !b.length || a[0].length !== b.length) {
        throw new Error("Incompatible matrix dimensions");
    }

    return a.map((row, i) => b[0].map((_, j) => {
        let result = ZERO;
        for (let k = 0; k < b.length; k++) {
            result = result.add(a[i][k].mul(b[k][j]));
        }
        return result;
    }));
}

function validateUnitary(matrix, tolerance = 1e-9) {
    if (!matrix.length || matrix.some(row => row.length !== matrix.length)) {
        throw new Error("Gate matrix must be square and nonempty");
    }

    const conjugateTranspose = matrix[0].map((_, j) =>
        matrix.map(row => row[j].conjugate())
    );
    const product = multiplyMatrices(conjugateTranspose, matrix);

    product.forEach((row, i) => row.forEach((value, j) => {
        const expected = i === j ? ONE : ZERO;
        if (value.sub(expected).abs2() > tolerance * tolerance) {
            throw new Error("Gate matrix is not unitary");
        }
    }));
}

class QuantumCircuit {
    constructor(qubits, seed = 42) {
        if (!Number.isInteger(qubits) || qubits < 1 || qubits > 20) {
            throw new RangeError("Qubit count must be between 1 and 20");
        }

        this.qubits = qubits;
        this.state = Array.from({ length: 2 ** qubits }, () => ZERO);
        this.state[0] = ONE;
        this.operations = [];
        this.randomState = seed >>> 0;
        this.collapsed = false;
    }

    // A deterministic pseudo-random generator makes simulation examples repeatable.
    random() {
        let x = this.randomState;
        x ^= x << 13;
        x ^= x >>> 17;
        x ^= x << 5;
        this.randomState = x >>> 0;
        return this.randomState / 0x100000000;
    }

    checkQubit(q) {
        if (!Number.isInteger(q) || q < 0 || q >= this.qubits) {
            throw new RangeError(`Invalid qubit index: ${q}`);
        }
    }

    append(name, targets, matrix, controls = []) {
        if (this.collapsed) {
            throw new Error("Cannot append gates after measurement collapse");
        }

        if (new Set(targets).size !== targets.length ||
            new Set(controls).size !== controls.length ||
            targets.length === 0) {
            throw new Error("Targets and controls must be nonempty and unique");
        }

        targets.forEach(q => this.checkQubit(q));
        controls.forEach(q => this.checkQubit(q));

        if (targets.some(q => controls.includes(q))) {
            throw new Error("Control and target qubits must differ");
        }
        if (matrix.length !== 2 ** targets.length ||
            matrix.some(row => row.length !== matrix.length)) {
            throw new Error("Gate dimensions do not match target qubits");
        }

        validateUnitary(matrix);
        this.operations.push({ name, targets: [...targets], controls: [...controls], matrix });
        return this;
    }

    gate(name, q) {
        if (!Object.hasOwn(GATES, name)) {
            throw new Error(`Unknown gate ${name}`);
        }
        return this.append(name, [q], GATES[name]);
    }

    h(q) { return this.gate("H", q); }
    x(q) { return this.gate("X", q); }
    z(q) { return this.gate("Z", q); }

    rx(theta, q) {
        const c = C(Math.cos(theta / 2));
        const s = C(0, -Math.sin(theta / 2));
        return this.append("RX", [q], [[c, s], [s, c]]);
    }

    ry(theta, q) {
        const c = C(Math.cos(theta / 2));
        const s = C(Math.sin(theta / 2));
        return this.append("RY", [q], [[c, C(-s.re)], [s, c]]);
    }

    rz(theta, q) {
        return this.append("RZ", [q], [
            [C(Math.cos(theta / 2), -Math.sin(theta / 2)), ZERO],
            [ZERO, C(Math.cos(theta / 2), Math.sin(theta / 2))]
        ]);
    }

    cnot(control, target) {
        return this.append("X", [target], GATES.X, [control]);
    }

    apply(operation) {
        const { targets, controls, matrix } = operation;
        const dimension = this.state.length;
        const targetMask = targets.reduce((mask, q) => mask | (1 << q), 0);
        const controlMask = controls.reduce((mask, q) => mask | (1 << q), 0);
        const output = this.state.slice();
        const localDimension = 2 ** targets.length;

        for (let base = 0; base < dimension; base++) {
            if ((base & targetMask) !== 0 || (base & controlMask) !== controlMask) {
                continue;
            }

            const indices = Array.from({ length: localDimension }, (_, local) =>
                targets.reduce((index, q, position) =>
                    local & (1 << position) ? index | (1 << q) : index, base)
            );

            const old = indices.map(index => this.state[index]);

            indices.forEach((index, row) => {
                let value = ZERO;
                for (let column = 0; column < localDimension; column++) {
                    value = value.add(matrix[row][column].mul(old[column]));
                }
                output[index] = value;
            });
        }

        this.state = output;
    }

    run() {
        this.operations.forEach(operation => this.apply(operation));
        return this.state.slice();
    }

    probabilities() {
        this.run();
        return this.state
            .map((amplitude, index) => ({
                bits: index.toString(2).padStart(this.qubits, "0").split("").reverse().join(""),
                probability: amplitude.abs2()
            }))
            .filter(entry => entry.probability > 1e-12);
    }

    sample(shots = 1000) {
        if (!Number.isSafeInteger(shots) || shots <= 0) {
            throw new RangeError("Shots must be a positive integer");
        }

        this.run();
        const weights = this.state.map(amplitude => amplitude.abs2());
        const total = weights.reduce((sum, p) => sum + p, 0);
        if (Math.abs(total - 1) > 1e-8) {
            throw new Error(`State normalization error: ${total}`);
        }

        const counts = new Map();
        for (let shot = 0; shot < shots; shot++) {
            let threshold = this.random() * total;
            let selected = weights.length - 1;

            for (let index = 0; index < weights.length; index++) {
                threshold -= weights[index];
                if (threshold < 0) {
                    selected = index;
                    break;
                }
            }

            const bits = selected.toString(2)
                .padStart(this.qubits, "0").split("").reverse().join("");
            counts.set(bits, (counts.get(bits) || 0) + 1);
        }
        return Object.fromEntries([...counts.entries()].sort());
    }

    measureAll() {
        this.run();
        const weights = this.state.map(amplitude => amplitude.abs2());
        let threshold = this.random() * weights.reduce((sum, p) => sum + p, 0);
        let selected = weights.length - 1;

        for (let index = 0; index < weights.length; index++) {
            threshold -= weights[index];
            if (threshold < 0) {
                selected = index;
                break;
            }
        }

        this.state = this.state.map((_, index) => index === selected ? ONE : ZERO);
        this.collapsed = true;
        return selected.toString(2).padStart(this.qubits, "0").split("").reverse().join("");
    }
}

function estimateBernoulliProbability(counts, state) {
    const total = Object.values(counts).reduce((sum, value) => sum + value, 0);
    if (total === 0) {
        throw new Error("Cannot estimate probability from empty counts");
    }
    return (counts[state] || 0) / total;
}

function demonstrateInterference() {
    // H followed by Z and H transforms |0> into |1>.
    const circuit = new QuantumCircuit(1);
    circuit.h(0).z(0).h(0);

    const probabilities = circuit.probabilities();
    console.log("Interference circuit probabilities:", probabilities);

    if (Math.abs(probabilities[0].probability) > 1e-9 ||
        Math.abs(probabilities[1].probability - 1) > 1e-9) {
        throw new Error("Interference invariant failed");
    }
}

function demonstrateBellPair() {
    const circuit = new QuantumCircuit(2, 123);
    circuit.h(0).cnot(0, 1);

    const counts = circuit.sample(2000);
    console.log("Bell-pair counts:", counts);

    if (counts["01"] || counts["10"]) {
        throw new Error("Ideal Bell pair produced an impossible outcome");
    }
}

function demonstrateParameterizedCircuit() {
    // RY(theta)|0> gives P(1) = sin²(theta/2).
    const theta = Math.PI / 3;
    const circuit = new QuantumCircuit(1).ry(theta, 0);
    const probabilities = circuit.probabilities();
    const expected = Math.sin(theta / 2) ** 2;

    console.log("Parameterized circuit:", probabilities);
    if (Math.abs(probabilities.find(item => item.bits === "1").probability - expected) > 1e-9) {
        throw new Error("Rotation probability does not match the analytical result");
    }
}

function demonstrateSamplingStatistics() {
    const circuit = new QuantumCircuit(1, 9876).h(0);
    const counts = circuit.sample(10000);
    const observed = estimateBernoulliProbability(counts, "0");
    const standardError = Math.sqrt(0.25 / 10000);

    console.log("Observed P(0):", observed.toFixed(4));
    console.log("Ideal P(0):", 0.5);
    console.log("Approximate standard error:", standardError.toFixed(4));

    if (Math.abs(observed - 0.5) > 5 * standardError) {
        throw new Error("Sampling result deviates excessively from expectation");
    }
}

function main() {
    demonstrateInterference();
    demonstrateBellPair();
    demonstrateParameterizedCircuit();
    demonstrateSamplingStatistics();
    console.log("Quantum circuit demonstrations passed.");
}

main();
