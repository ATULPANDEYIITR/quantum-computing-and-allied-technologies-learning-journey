/**
 * Quantum Teleportation: Quantum Information Transfer
 *
 * A self-contained JavaScript implementation of the three-qubit
 * quantum-teleportation protocol.
 *
 * This file uses Node.js standard JavaScript only. It models:
 * - Complex amplitudes
 * - Single-qubit gates
 * - Multi-qubit state vectors
 * - Tensor products
 * - Bell-pair preparation
 * - Alice's Bell-basis measurement
 * - Classical measurement outcomes
 * - Bob's conditional correction
 * - Pure-state fidelity
 * - Event-driven protocol execution
 * - Validation and failure handling
 * - A stochastic Pauli noise model
 *
 * Run with:
 *   node quantum_teleportation.js
 *
 * The simulation is intentionally small enough to inspect directly.
 * A general n-qubit state-vector simulator requires 2^n amplitudes.
 */

"use strict";

// ---------------------------------------------------------------------------
// Complex-number representation
// ---------------------------------------------------------------------------

class Complex {
    constructor(real = 0, imaginary = 0) {
        this.re = real;
        this.im = imaginary;
    }

    add(other) {
        return new Complex(this.re + other.re, this.im + other.im);
    }

    subtract(other) {
        return new Complex(this.re - other.re, this.im - other.im);
    }

    multiply(other) {
        if (typeof other === "number") {
            return new Complex(this.re * other, this.im * other);
        }

        return new Complex(
            this.re * other.re - this.im * other.im,
            this.re * other.im + this.im * other.re
        );
    }

    conjugate() {
        return new Complex(this.re, -this.im);
    }

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    divide(scalar) {
        if (Math.abs(scalar) < 1e-12) {
            throw new Error("Cannot divide a complex value by zero.");
        }

        return new Complex(this.re / scalar, this.im / scalar);
    }

    toString(precision = 4) {
        const real = Number(this.re.toFixed(precision));
        const imaginary = Number(this.im.toFixed(precision));

        if (Math.abs(imaginary) < 10 ** (-precision)) {
            return `${real}`;
        }

        if (Math.abs(real) < 10 ** (-precision)) {
            return `${imaginary}i`;
        }

        return `${real}${imaginary >= 0 ? "+" : ""}${imaginary}i`;
    }
}

const ZERO = new Complex(0, 0);
const ONE = new Complex(1, 0);
const I_COMPLEX = new Complex(0, 1);

function complex(real, imaginary = 0) {
    return new Complex(real, imaginary);
}


// ---------------------------------------------------------------------------
// Vector and matrix operations
// ---------------------------------------------------------------------------

function vectorNorm(vector) {
    return Math.sqrt(
        vector.reduce((sum, value) => sum + value.magnitudeSquared(), 0)
    );
}

function normalize(vector) {
    const norm = vectorNorm(vector);

    if (norm < 1e-12) {
        throw new Error("A quantum state cannot be normalized.");
    }

    return vector.map(value => value.divide(norm));
}

function innerProduct(bra, ket) {
    if (bra.length !== ket.length) {
        throw new Error("Inner-product dimensions do not match.");
    }

    return bra.reduce(
        (sum, value, index) =>
            sum.add(value.conjugate().multiply(ket[index])),
        new Complex()
    );
}

function matrixVectorMultiply(matrix, vector) {
    if (matrix.length !== vector.length) {
        throw new Error("Matrix and vector dimensions do not match.");
    }

    return matrix.map(row => {
        if (row.length !== vector.length) {
            throw new Error("Quantum gate matrix must be square.");
        }

        return row.reduce(
            (sum, value, index) => sum.add(value.multiply(vector[index])),
            new Complex()
        );
    });
}

function kronVector(left, right) {
    const result = [];

    for (const a of left) {
        for (const b of right) {
            result.push(a.multiply(b));
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// Quantum gates
// ---------------------------------------------------------------------------

const X = [
    [ZERO, ONE],
    [ONE, ZERO]
];

const Y = [
    [ZERO, I_COMPLEX.multiply(-1)],
    [I_COMPLEX, ZERO]
];

const Z = [
    [ONE, ZERO],
    [ZERO, ONE.multiply(-1)]
];

const H = [
    [ONE.multiply(1 / Math.sqrt(2)), ONE.multiply(1 / Math.sqrt(2))],
    [ONE.multiply(1 / Math.sqrt(2)), ONE.multiply(-1 / Math.sqrt(2))]
];

const IDENTITY = [
    [ONE, ZERO],
    [ZERO, ONE]
];


// ---------------------------------------------------------------------------
// Computational basis and state construction
// ---------------------------------------------------------------------------

function basisState(bits) {
    if (!/^[01]+$/.test(bits)) {
        throw new Error("Basis state must contain only binary digits.");
    }

    const dimension = 2 ** bits.length;
    const state = Array.from({ length: dimension }, () => new Complex());

    state[parseInt(bits, 2)] = ONE;
    return state;
}

function qubitState(alpha, beta) {
    return normalize([
        alpha instanceof Complex ? alpha : complex(alpha),
        beta instanceof Complex ? beta : complex(beta)
    ]);
}

function bitAt(index, qubit, numberOfQubits) {
    const shift = numberOfQubits - 1 - qubit;
    return (index >> shift) & 1;
}

function replaceBit(index, qubit, value, numberOfQubits) {
    const shift = numberOfQubits - 1 - qubit;
    const mask = 1 << shift;

    return value === 1 ? (index | mask) : (index & ~mask);
}


// ---------------------------------------------------------------------------
// Gate application without constructing the full Kronecker matrix
// ---------------------------------------------------------------------------

function applySingleQubitGate(state, gate, targetQubit, numberOfQubits) {
    const dimension = 2 ** numberOfQubits;

    if (state.length !== dimension) {
        throw new Error("State dimension does not match qubit count.");
    }

    if (targetQubit < 0 || targetQubit >= numberOfQubits) {
        throw new Error("Target qubit is outside the register.");
    }

    const result = Array.from(
        { length: dimension },
        () => new Complex()
    );

    for (let index = 0; index < dimension; index += 1) {
        const oldBit = bitAt(index, targetQubit, numberOfQubits);
        const sourceIndex = replaceBit(
            index,
            targetQubit,
            oldBit,
            numberOfQubits
        );

        for (let newBit = 0; newBit < 2; newBit += 1) {
            const destinationIndex = replaceBit(
                index,
                targetQubit,
                newBit,
                numberOfQubits
            );

            result[destinationIndex] = result[destinationIndex].add(
                gate[newBit][oldBit].multiply(state[sourceIndex])
            );
        }
    }

    return normalize(result);
}

function applyCNOT(state, control, target, numberOfQubits) {
    if (control === target) {
        throw new Error("CNOT control and target must differ.");
    }

    const dimension = 2 ** numberOfQubits;

    if (state.length !== dimension) {
        throw new Error("State dimension does not match qubit count.");
    }

    const result = Array.from(
        { length: dimension },
        () => new Complex()
    );

    for (let index = 0; index < dimension; index += 1) {
        const controlBit = bitAt(index, control, numberOfQubits);
        let destination = index;

        if (controlBit === 1) {
            const targetBit = bitAt(index, target, numberOfQubits);
            destination = replaceBit(
                index,
                target,
                1 - targetBit,
                numberOfQubits
            );
        }

        result[destination] = result[destination].add(state[index]);
    }

    return normalize(result);
}


// ---------------------------------------------------------------------------
// Measurement
// ---------------------------------------------------------------------------

function measurementProbabilities(state, qubit, numberOfQubits) {
    const probabilities = [0, 0];

    state.forEach((amplitude, index) => {
        const bit = bitAt(index, qubit, numberOfQubits);
        probabilities[bit] += amplitude.magnitudeSquared();
    });

    return probabilities;
}

function collapseOnBits(
    state,
    qubits,
    expectedBits,
    numberOfQubits
) {
    const probabilities = new Map();

    for (let index = 0; index < state.length; index += 1) {
        const observed = qubits.map(
            qubit => bitAt(index, qubit, numberOfQubits)
        );

        const key = observed.join("");
        probabilities.set(
            key,
            (probabilities.get(key) || 0) +
                state[index].magnitudeSquared()
        );
    }

    const outcomeKey = expectedBits.join("");
    const probability = probabilities.get(outcomeKey) || 0;

    if (probability < 1e-12) {
        throw new Error("Cannot collapse onto an impossible outcome.");
    }

    return {
        state: normalize(
            state.map((amplitude, index) => {
                const observed = qubits.map(
                    qubit => bitAt(index, qubit, numberOfQubits)
                );

                return observed.join("") === outcomeKey
                    ? amplitude
                    : new Complex();
            })
        ),
        probability
    };
}

function measureQubits(
    state,
    qubits,
    numberOfQubits,
    randomSource = Math.random
) {
    const outcomes = [];

    for (let index = 0; index < state.length; index += 1) {
        const bits = qubits.map(
            qubit => bitAt(index, qubit, numberOfQubits)
        );
        const key = bits.join("");

        if (!outcomes.some(item => item.key === key)) {
            outcomes.push({
                key,
                probability: 0
            });
        }

        const record = outcomes.find(item => item.key === key);
        record.probability += state[index].magnitudeSquared();
    }

    let draw = randomSource();
    let selected = outcomes[outcomes.length - 1];

    for (const outcome of outcomes) {
        if (draw <= outcome.probability) {
            selected = outcome;
            break;
        }

        draw -= outcome.probability;
    }

    const bits = selected.key.split("").map(Number);
    const collapsed = collapseOnBits(
        state,
        qubits,
        bits,
        numberOfQubits
    );

    return {
        bits,
        probability: collapsed.probability,
        state: collapsed.state
    };
}


// ---------------------------------------------------------------------------
// Teleportation primitives
// ---------------------------------------------------------------------------

function prepareBellPair() {
    let state = basisState("00");

    state = applySingleQubitGate(state, H, 0, 2);
    state = applyCNOT(state, 0, 1, 2);

    return state;
}

function prepareTeleportationRegister(inputState) {
    if (inputState.length !== 2) {
        throw new Error("Teleportation requires exactly one input qubit.");
    }

    return kronVector(inputState, prepareBellPair());
}

function aliceBellMeasurement(state, randomSource) {
    // The CNOT and Hadamard transform the Bell basis into the computational
    // basis. Alice can then obtain the two classical measurement bits.
    let transformed = applyCNOT(state, 0, 1, 3);
    transformed = applySingleQubitGate(transformed, H, 0, 3);

    return measureQubits(
        transformed,
        [0, 1],
        3,
        randomSource
    );
}

function bobCorrection(state, classicalBits) {
    const [firstBit, secondBit] = classicalBits;
    let corrected = state;

    if (secondBit === 1) {
        corrected = applySingleQubitGate(
            corrected,
            X,
            2,
            3
        );
    }

    if (firstBit === 1) {
        corrected = applySingleQubitGate(
            corrected,
            Z,
            2,
            3
        );
    }

    return corrected;
}

function extractBobState(state, measurementBits) {
    const amplitudes = [
        new Complex(),
        new Complex()
    ];

    for (let index = 0; index < state.length; index += 1) {
        const aliceBits = [
            bitAt(index, 0, 3),
            bitAt(index, 1, 3)
        ];

        if (
            aliceBits[0] === measurementBits[0] &&
            aliceBits[1] === measurementBits[1]
        ) {
            const bobBit = bitAt(index, 2, 3);
            amplitudes[bobBit] = amplitudes[bobBit].add(
                state[index]
            );
        }
    }

    return normalize(amplitudes);
}


// ---------------------------------------------------------------------------
// Fidelity and inspection
// ---------------------------------------------------------------------------

function pureStateFidelity(actual, expected) {
    const overlap = innerProduct(expected, actual);
    return overlap.magnitudeSquared();
}

function formatState(state) {
    const terms = [];

    state.forEach((amplitude, index) => {
        if (amplitude.magnitude() > 1e-8) {
            terms.push(
                `${amplitude.toString()}|${index.toString(2).padStart(
                    Math.log2(state.length),
                    "0"
                )}>`
            );
        }
    });

    return terms.length ? terms.join(" + ") : "0";
}

function printState(label, state) {
    console.log(`${label}: ${formatState(state)}`);
}


// ---------------------------------------------------------------------------
// Event-driven protocol representation
// ---------------------------------------------------------------------------

class TeleportationProtocol extends EventTarget {
    constructor(randomSource = Math.random) {
        super();
        this.randomSource = randomSource;
        this.phase = "created";
        this.measurementBits = null;
    }

    emit(name, detail) {
        this.dispatchEvent(
            new CustomEvent(name, { detail })
        );
    }

    transition(nextPhase) {
        this.phase = nextPhase;

        this.emit("phase", {
            phase: nextPhase
        });
    }

    execute(inputState) {
        this.transition("entanglement-prepared");

        let register = prepareTeleportationRegister(inputState);

        this.emit("entanglement", {
            state: register
        });

        this.transition("alice-measuring");

        const measurement = aliceBellMeasurement(
            register,
            this.randomSource
        );

        this.measurementBits = measurement.bits;

        this.emit("classical-message", {
            bits: measurement.bits,
            probability: measurement.probability
        });

        const bobBeforeCorrection = extractBobState(
            measurement.state,
            measurement.bits
        );

        this.transition("classical-communication-complete");

        this.emit("bob-before-correction", {
            state: bobBeforeCorrection
        });

        const correctedRegister = bobCorrection(
            measurement.state,
            measurement.bits
        );

        const bobAfterCorrection = extractBobState(
            correctedRegister,
            measurement.bits
        );

        const fidelity = pureStateFidelity(
            bobAfterCorrection,
            inputState
        );

        this.transition("completed");

        this.emit("completed", {
            state: bobAfterCorrection,
            fidelity
        });

        return {
            measurementBits: measurement.bits,
            bobBeforeCorrection,
            bobAfterCorrection,
            fidelity
        };
    }
}


// ---------------------------------------------------------------------------
// Deterministic pseudo-random source for repeatable examples
// ---------------------------------------------------------------------------

function seededRandom(seed) {
    let value = seed >>> 0;

    return () => {
        value = (
            Math.imul(1664525, value) +
            1013904223
        ) >>> 0;

        return value / 4294967296;
    };
}


// ---------------------------------------------------------------------------
// Noise model
// ---------------------------------------------------------------------------

function applyPauliNoise(state, probability, randomSource) {
    if (probability < 0 || probability > 1) {
        throw new Error("Noise probability must be between 0 and 1.");
    }

    if (randomSource() >= probability) {
        return state;
    }

    const draw = randomSource();

    if (draw < 1 / 3) {
        return matrixVectorMultiply(X, state);
    }

    if (draw < 2 / 3) {
        return matrixVectorMultiply(Y, state);
    }

    return matrixVectorMultiply(Z, state);
}

function noisyTeleportationTrial(
    inputState,
    errorProbability,
    randomSource
) {
    let register = prepareTeleportationRegister(inputState);

    const measurement = aliceBellMeasurement(
        register,
        randomSource
    );

    let bob = extractBobState(
        measurement.state,
        measurement.bits
    );

    bob = applyPauliNoise(
        bob,
        errorProbability,
        randomSource
    );

    // Bob's classical control logic is represented explicitly on his
    // separated qubit after the noisy channel.
    if (measurement.bits[1] === 1) {
        bob = normalize(matrixVectorMultiply(X, bob));
    }

    if (measurement.bits[0] === 1) {
        bob = normalize(matrixVectorMultiply(Z, bob));
    }

    return pureStateFidelity(bob, inputState);
}


// ---------------------------------------------------------------------------
// Validation and demonstrations
// ---------------------------------------------------------------------------

function assertClose(actual, expected, tolerance, message) {
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(
            `${message}: expected ${expected}, received ${actual}`
        );
    }
}

function demonstrateProtocol() {
    console.log("\n" + "=".repeat(72));
    console.log("QUANTUM TELEPORTATION");
    console.log("=".repeat(72));

    const input = qubitState(
        complex(0.8, 0.15),
        complex(0.45, -0.2)
    );

    console.log(
        "\nInput state:",
        `${input[0].toString()}|0> + ${input[1].toString()}|1>`
    );

    const random = seededRandom(20261004);
    const protocol = new TeleportationProtocol(random);

    protocol.addEventListener("phase", event => {
        console.log(`  protocol phase -> ${event.detail.phase}`);
    });

    protocol.addEventListener("classical-message", event => {
        console.log(
            `  Alice sends classical bits: ${event.detail.bits.join("")}`
        );
    });

    protocol.addEventListener("bob-before-correction", event => {
        printState(
            "  Bob before correction",
            event.detail.state
        );
    });

    protocol.addEventListener("completed", event => {
        printState(
            "  Bob after correction",
            event.detail.state
        );

        console.log(
            `  Teleportation fidelity: ${event.detail.fidelity.toFixed(12)}`
        );
    });

    const result = protocol.execute(input);

    assertClose(
        result.fidelity,
        1,
        1e-10,
        "Ideal teleportation failed"
    );

    console.log(
        "\nThe protocol succeeds because Bob's correction uses the two classical"
        + " bits produced by Alice's measurement."
    );
}

function demonstrateDifferentStates() {
    console.log("\nRepresentative states:");

    const states = [
        ["|0>", qubitState(1, 0)],
        ["|1>", qubitState(0, 1)],
        ["|+>", qubitState(1, 1)],
        ["|->", qubitState(1, -1)],
        ["phase state", qubitState(1, complex(0, 1))],
        [
            "complex state",
            qubitState(
                complex(1, 0.5),
                complex(0.7, -0.2)
            )
        ]
    ];

    states.forEach(([name, state], index) => {
        const random = seededRandom(100 + index);
        const protocol = new TeleportationProtocol(random);
        const result = protocol.execute(state);

        console.log(
            `  ${name.padEnd(16)} `
            + `bits=${result.measurementBits.join("")} `
            + `fidelity=${result.fidelity.toFixed(12)}`
        );
    });
}

function demonstrateNoise() {
    console.log("\nStochastic Pauli noise experiment:");

    const input = qubitState(
        complex(0.7, 0.2),
        complex(0.4, -0.5)
    );

    for (const probability of [0, 0.01, 0.05, 0.1, 0.25]) {
        let totalFidelity = 0;
        const trials = 2000;

        for (let trial = 0; trial < trials; trial += 1) {
            const random = seededRandom(
                7000 + trial
            );

            totalFidelity += noisyTeleportationTrial(
                input,
                probability,
                random
            );
        }

        console.log(
            `  error=${probability.toFixed(2)} `
            + `average fidelity=${(totalFidelity / trials).toFixed(5)}`
        );
    }
}

function demonstrateInformationConstraints() {
    console.log("\nInformation-transfer constraints:");
    console.log(
        "  Alice performs a quantum measurement and obtains two classical bits."
    );
    console.log(
        "  Bob cannot apply the final correction until those bits are available."
    );
    console.log(
        "  The protocol therefore does not provide faster-than-light classical communication."
    );
    console.log(
        "  The original state is not preserved as a second independent copy."
    );
}

function demonstrateFailureHandling() {
    console.log("\nValidation checks:");

    const failures = [
        {
            name: "zero-norm qubit",
            action: () => qubitState(0, 0)
        },
        {
            name: "invalid teleportation dimension",
            action: () => prepareTeleportationRegister([ONE, ONE, ONE])
        },
        {
            name: "invalid noise probability",
            action: () => applyPauliNoise(
                [ONE, ZERO],
                2,
                Math.random
            )
        }
    ];

    failures.forEach(test => {
        try {
            test.action();
        } catch (error) {
            console.log(`  ${test.name}: rejected`);
            return;
        }

        throw new Error(
            `Invalid operation unexpectedly succeeded: ${test.name}`
        );
    });
}

function showSimulationScaling() {
    console.log("\nState-vector scaling:");

    [3, 10, 20, 30, 40].forEach(qubits => {
        const amplitudes = 2 ** qubits;

        console.log(
            `  ${qubits} qubits -> ${amplitudes.toLocaleString()} amplitudes`
        );
    });

    console.log(
        "  The teleportation protocol uses three qubits, but general state-vector"
        + " simulation scales exponentially with the number of qubits."
    );
}


// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
    demonstrateProtocol();
    demonstrateDifferentStates();
    demonstrateNoise();
    demonstrateInformationConstraints();
    demonstrateFailureHandling();
    showSimulationScaling();

    console.log("\nSimulation completed successfully.");
}

main();
