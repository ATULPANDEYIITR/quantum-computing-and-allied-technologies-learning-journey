/**
 * Bernstein-Vazirani Algorithm
 * Event-driven JavaScript model of hidden-string discovery.
 *
 * This implementation focuses on JavaScript-specific behavior:
 * - typed arrays for probability storage
 * - event-driven oracle execution
 * - immutable experiment results
 * - asynchronous oracle simulation
 * - validation and policy-style experiment reporting
 * - phase-kickback represented explicitly at the state-vector level
 *
 * Run with:
 *   node bernstein-vazirani.js
 */

"use strict";

// ---------------------------------------------------------------------------
// Validation and GF(2) operations
// ---------------------------------------------------------------------------

function assertBitString(value, name = "bit string") {
    if (typeof value !== "string" || value.length === 0) {
        throw new TypeError(`${name} must be a non-empty string.`);
    }

    if (!/^[01]+$/.test(value)) {
        throw new TypeError(`${name} must contain only 0 and 1.`);
    }
}

function xorDotProduct(a, b) {
    if (a.length !== b.length) {
        throw new RangeError("Bit strings must have equal lengths.");
    }

    let parity = 0;

    for (let i = 0; i < a.length; i++) {
        parity ^= Number(a[i]) & Number(b[i]);
    }

    return parity;
}

// ---------------------------------------------------------------------------
// Event-driven oracle
// ---------------------------------------------------------------------------

class BernsteinVaziraniOracle extends EventTarget {
    constructor(hiddenString) {
        super();
        assertBitString(hiddenString, "hiddenString");
        this.hiddenString = hiddenString;
        this.queryCount = 0;
    }

    evaluate(input) {
        assertBitString(input, "input");

        if (input.length !== this.hiddenString.length) {
            throw new RangeError(
                `Expected ${this.hiddenString.length} input bits.`
            );
        }

        this.queryCount += 1;

        const value = xorDotProduct(this.hiddenString, input);

        this.dispatchEvent(
            new CustomEvent("query", {
                detail: {
                    input,
                    output: value,
                    queryCount: this.queryCount
                }
            })
        );

        return value;
    }

    resetQueryCount() {
        this.queryCount = 0;
    }
}

// ---------------------------------------------------------------------------
// Classical recovery used as a verification oracle
// ---------------------------------------------------------------------------

function discoverClassically(oracle) {
    const recovered = [];

    for (let i = 0; i < oracle.hiddenString.length; i++) {
        const input = Array(oracle.hiddenString.length).fill("0");
        input[i] = "1";
        recovered.push(String(oracle.evaluate(input.join(""))));
    }

    return recovered.join("");
}

// ---------------------------------------------------------------------------
// Complex-number helper
// ---------------------------------------------------------------------------

function complex(real, imaginary = 0) {
    return Object.freeze({ real, imaginary });
}

function addComplex(a, b) {
    return complex(a.real + b.real, a.imaginary + b.imaginary);
}

function multiplyComplex(a, b) {
    return complex(
        a.real * b.real - a.imaginary * b.imaginary,
        a.real * b.imaginary + a.imaginary * b.real
    );
}

function scaleComplex(a, scalar) {
    return complex(a.real * scalar, a.imaginary * scalar);
}

function probability(a) {
    return a.real * a.real + a.imaginary * a.imaginary;
}

// ---------------------------------------------------------------------------
// Quantum state-vector implementation
// ---------------------------------------------------------------------------

function applyHadamardToAll(state, qubitCount) {
    const size = 2 ** qubitCount;
    const result = Array.from({ length: size }, () => complex(0));

    const scale = 1 / Math.sqrt(size);

    for (let output = 0; output < size; output++) {
        let amplitude = complex(0);

        for (let source = 0; source < size; source++) {
            const parity = countSetBits(output & source) % 2;
            const sign = parity === 0 ? 1 : -1;

            amplitude = addComplex(
                amplitude,
                scaleComplex(state[source], sign)
            );
        }

        result[output] = scaleComplex(amplitude, scale);
    }

    return result;
}

function countSetBits(value) {
    let count = 0;

    while (value !== 0) {
        value &= value - 1;
        count++;
    }

    return count;
}

function applyOracle(state, hiddenString) {
    assertBitString(hiddenString, "hiddenString");

    const n = hiddenString.length;
    const expectedSize = 2 ** (n + 1);

    if (state.length !== expectedSize) {
        throw new RangeError("State vector has an invalid dimension.");
    }

    const result = Array.from({ length: expectedSize }, () => complex(0));

    for (let index = 0; index < state.length; index++) {
        if (probability(state[index]) < 1e-18) {
            continue;
        }

        const inputValue = index >> 1;
        const outputBit = index & 1;
        const input = inputValue.toString(2).padStart(n, "0");

        const oracleOutput = xorDotProduct(hiddenString, input);
        const transformedIndex = (inputValue << 1) | (outputBit ^ oracleOutput);

        result[transformedIndex] = addComplex(
            result[transformedIndex],
            state[index]
        );
    }

    return result;
}

function applyHadamardToInputRegister(state, inputQubits) {
    const inputSize = 2 ** inputQubits;
    const result = Array.from({ length: state.length }, () => complex(0));
    const scale = 1 / Math.sqrt(inputSize);

    for (let outputBit = 0; outputBit <= 1; outputBit++) {
        for (let outputInput = 0; outputInput < inputSize; outputInput++) {
            let amplitude = complex(0);

            for (let sourceInput = 0; sourceInput < inputSize; sourceInput++) {
                const parity = countSetBits(outputInput & sourceInput) % 2;
                const sign = parity === 0 ? 1 : -1;
                const sourceIndex = (sourceInput << 1) | outputBit;

                amplitude = addComplex(
                    amplitude,
                    scaleComplex(state[sourceIndex], sign)
                );
            }

            result[(outputInput << 1) | outputBit] =
                scaleComplex(amplitude, scale);
        }
    }

    return result;
}

function initialBernsteinVaziraniState(inputQubits) {
    // |0...0>|1> has integer basis index 1 when the output qubit is the
    // least-significant qubit.
    const state = Array.from(
        { length: 2 ** (inputQubits + 1) },
        () => complex(0)
    );

    state[1] = complex(1);
    return applyHadamardToAll(state, inputQubits + 1);
}

function measureInputRegister(state, inputQubits, random = Math.random) {
    const inputSize = 2 ** inputQubits;
    const marginal = new Float64Array(inputSize);

    for (let index = 0; index < state.length; index++) {
        const inputValue = index >> 1;
        marginal[inputValue] += probability(state[index]);
    }

    const sample = random();
    let cumulative = 0;

    for (let inputValue = 0; inputValue < inputSize; inputValue++) {
        cumulative += marginal[inputValue];

        if (sample <= cumulative) {
            return inputValue.toString(2).padStart(inputQubits, "0");
        }
    }

    return (inputSize - 1).toString(2).padStart(inputQubits, "0");
}

// ---------------------------------------------------------------------------
// Asynchronous quantum-oracle experiment
// ---------------------------------------------------------------------------

function runQuantumExperiment(hiddenString, options = {}) {
    assertBitString(hiddenString, "hiddenString");

    const delay = options.delayMs ?? 5;

    if (!Number.isInteger(delay) || delay < 0) {
        throw new RangeError("delayMs must be a non-negative integer.");
    }

    return new Promise((resolve) => {
        const oracle = new BernsteinVaziraniOracle(hiddenString);

        oracle.addEventListener("query", (event) => {
            console.log(
                `[oracle event] query=${event.detail.queryCount}, ` +
                `input=${event.detail.input}, output=${event.detail.output}`
            );
        });

        setTimeout(() => {
            let state = initialBernsteinVaziraniState(hiddenString.length);

            // The oracle is represented by a reversible state transformation.
            // The event-driven oracle object records the logical query.
            oracle.evaluate("0".repeat(hiddenString.length));

            state = applyOracle(state, hiddenString);
            state = applyHadamardToInputRegister(state, hiddenString.length);

            const recovered = measureInputRegister(
                state,
                hiddenString.length
            );

            resolve(
                Object.freeze({
                    hiddenString,
                    recovered,
                    quantumOracleQueries: 1,
                    correct: recovered === hiddenString
                })
            );
        }, delay);
    });
}

// ---------------------------------------------------------------------------
// Circuit representation
// ---------------------------------------------------------------------------

function describeOracle(hiddenString) {
    assertBitString(hiddenString, "hiddenString");

    return hiddenString
        .split("")
        .map((bit, index) =>
            bit === "1"
                ? `CNOT(input[${index}], output)`
                : null
        )
        .filter(Boolean);
}

// ---------------------------------------------------------------------------
// Noise model
// ---------------------------------------------------------------------------

function applyReadoutNoise(bitString, errorProbability, random = Math.random) {
    assertBitString(bitString, "bitString");

    if (
        typeof errorProbability !== "number" ||
        errorProbability < 0 ||
        errorProbability > 1
    ) {
        throw new RangeError(
            "errorProbability must be between 0 and 1."
        );
    }

    return bitString
        .split("")
        .map((bit) => {
            if (random() < errorProbability) {
                return bit === "0" ? "1" : "0";
            }

            return bit;
        })
        .join("");
}

// ---------------------------------------------------------------------------
// Main experiment
// ---------------------------------------------------------------------------

async function main() {
    const hiddenString = "110101";

    console.log("Bernstein-Vazirani Algorithm");
    console.log("============================");
    console.log(`Hidden string: ${hiddenString}`);

    const verificationOracle = new BernsteinVaziraniOracle(hiddenString);

    console.log("\nClassical verification");
    console.log("----------------------");

    const classical = discoverClassically(verificationOracle);

    console.log(`Recovered: ${classical}`);
    console.log(`Oracle calls: ${verificationOracle.queryCount}`);

    console.log("\nQuantum oracle structure");
    console.log("------------------------");

    for (const gate of describeOracle(hiddenString)) {
        console.log(gate);
    }

    console.log("\nAsynchronous quantum experiment");
    console.log("--------------------------------");

    const result = await runQuantumExperiment(hiddenString);

    console.log(`Recovered: ${result.recovered}`);
    console.log(`Quantum oracle calls: ${result.quantumOracleQueries}`);
    console.log(`Correct: ${result.correct}`);

    console.log("\nReadout-noise example");
    console.log("---------------------");

    const noisy = applyReadoutNoise(
        result.recovered,
        0.05,
        () => 0.03
    );

    console.log(`Ideal result: ${result.recovered}`);
    console.log(`Observed result: ${noisy}`);

    console.log("\nJavaScript-specific implementation properties");
    console.log("---------------------------------------------");
    console.log(
        "The experiment uses EventTarget for oracle-query events, " +
        "Promises for asynchronous execution, and Float64Array for " +
        "marginal probability storage."
    );
}

main().catch((error) => {
    console.error(`Experiment failed: ${error.message}`);
    process.exitCode = 1;
});
