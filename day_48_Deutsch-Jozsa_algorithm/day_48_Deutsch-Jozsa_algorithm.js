"use strict";

/*
 * Deutsch-Jozsa algorithm with a state-vector simulator.
 *
 * This implementation focuses on phase kickback, amplitude interference,
 * circuit execution, and repeated measurement. It requires Node.js and
 * uses no external dependencies.
 */

class QuantumCircuitError extends Error {}

function assertPositiveInteger(value, name) {
    if (!Number.isInteger(value) || value < 1) {
        throw new QuantumCircuitError(`${name} must be a positive integer.`);
    }
}

function validateOracle(oracle, numQubits) {
    assertPositiveInteger(numQubits, "numQubits");

    const dimension = 2 ** numQubits;
    const outputs = [];

    for (let x = 0; x < dimension; x += 1) {
        const result = oracle(x);

        if (result !== 0 && result !== 1) {
            throw new QuantumCircuitError(
                `Oracle output at ${x} must be exactly 0 or 1.`
            );
        }

        outputs.push(result);
    }

    const ones = outputs.reduce((sum, value) => sum + value, 0);

    if (ones !== 0 && ones !== dimension && ones * 2 !== dimension) {
        throw new QuantumCircuitError(
            "The oracle violates the constant-or-balanced promise."
        );
    }

    return {
        outputs,
        classification: ones === 0 || ones === dimension
            ? "constant"
            : "balanced",
    };
}

class StateVector {
    constructor(numQubits) {
        assertPositiveInteger(numQubits, "numQubits");

        this.numQubits = numQubits;
        this.dimension = 2 ** numQubits;
        this.real = new Float64Array(this.dimension);
        this.imaginary = new Float64Array(this.dimension);
        this.real[0] = 1;
    }

    applyHadamardToAll() {
        let stride = 1;

        while (stride < this.dimension) {
            for (let base = 0; base < this.dimension; base += 2 * stride) {
                for (let offset = 0; offset < stride; offset += 1) {
                    const a = base + offset;
                    const b = a + stride;

                    const realA = this.real[a];
                    const imagA = this.imaginary[a];
                    const realB = this.real[b];
                    const imagB = this.imaginary[b];

                    this.real[a] = realA + realB;
                    this.imaginary[a] = imagA + imagB;
                    this.real[b] = realA - realB;
                    this.imaginary[b] = imagA - imagB;
                }
            }

            stride *= 2;
        }

        const scale = 1 / Math.sqrt(this.dimension);

        for (let i = 0; i < this.dimension; i += 1) {
            this.real[i] *= scale;
            this.imaginary[i] *= scale;
        }
    }

    applyPhaseOracle(oracle) {
        for (let x = 0; x < this.dimension; x += 1) {
            if (oracle(x) === 1) {
                // Multiplication by -1 changes phase without changing
                // the basis state's probability.
                this.real[x] *= -1;
                this.imaginary[x] *= -1;
            }
        }
    }

    probabilities() {
        const probabilities = new Float64Array(this.dimension);

        for (let i = 0; i < this.dimension; i += 1) {
            probabilities[i] =
                this.real[i] ** 2 + this.imaginary[i] ** 2;
        }

        return probabilities;
    }

    measure(random = Math.random) {
        const probabilities = this.probabilities();
        const sample = random();
        let cumulative = 0;

        for (let i = 0; i < probabilities.length; i += 1) {
            cumulative += probabilities[i];

            if (sample < cumulative || i === probabilities.length - 1) {
                return {
                    integer: i,
                    bitstring: i.toString(2).padStart(this.numQubits, "0"),
                    probability: probabilities[i],
                };
            }
        }

        throw new QuantumCircuitError("Measurement distribution is invalid.");
    }
}

function runDeutschJozsa(oracle, numQubits, options = {}) {
    const { outputs, classification } = validateOracle(oracle, numQubits);
    const state = new StateVector(numQubits);

    state.applyHadamardToAll();
    state.applyPhaseOracle(oracle);
    state.applyHadamardToAll();

    const probabilities = Array.from(state.probabilities());
    const zeroProbability = probabilities[0];

    const inferredClass = Math.abs(zeroProbability - 1) < 1e-9
        ? "constant"
        : "balanced";

    if (inferredClass !== classification) {
        throw new QuantumCircuitError(
            "Unexpected interference result; check the simulator."
        );
    }

    const measurement = state.measure(options.random ?? Math.random);

    return Object.freeze({
        numQubits,
        oracleQueries: 1,
        outputs,
        classification,
        inferredClass,
        zeroProbability,
        measurement,
        probabilities,
    });
}

function makeBitParityOracle(mask) {
    if (!Number.isInteger(mask) || mask < 0) {
        throw new QuantumCircuitError("Mask must be a non-negative integer.");
    }

    return (x) => {
        let value = x & mask;
        let parity = 0;

        while (value !== 0) {
            parity ^= value & 1;
            value >>>= 1;
        }

        return parity;
    };
}

function runDemonstration() {
    const cases = [
        {
            name: "Constant oracle",
            oracle: () => 1,
            expected: "constant",
        },
        {
            name: "Two-bit parity",
            oracle: makeBitParityOracle(0b11),
            expected: "balanced",
        },
        {
            name: "Three-bit parity",
            oracle: makeBitParityOracle(0b111),
            expected: "balanced",
        },
    ];

    for (const testCase of cases) {
        const result = runDeutschJozsa(testCase.oracle, 3);

        if (result.inferredClass !== testCase.expected) {
            throw new Error(`Classification failed for ${testCase.name}.`);
        }

        console.log(`\n${testCase.name}`);
        console.log("Truth table:", result.outputs);
        console.log("Class:", result.inferredClass);
        console.log("Probability of |000>:", result.zeroProbability);
        console.log("Measured:", result.measurement.bitstring);
    }

    // A single marked input is neither constant nor balanced.
    try {
        runDeutschJozsa((x) => Number(x === 0), 3);
    } catch (error) {
        if (!(error instanceof QuantumCircuitError)) {
            throw error;
        }
        console.log("\nInvalid promise correctly rejected:", error.message);
    }
}

if (require.main === module) {
    runDemonstration();
}

module.exports = {
    QuantumCircuitError,
    StateVector,
    makeBitParityOracle,
    runDeutschJozsa,
    validateOracle,
};
