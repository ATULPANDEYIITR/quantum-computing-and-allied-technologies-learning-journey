/*
 * SWAP and Controlled-SWAP (Fredkin) Gates
 * =========================================
 *
 * A self-contained JavaScript study of two important multi-qubit operations.
 *
 * The program starts with computational-basis states and develops:
 *   - state-vector representation
 *   - qubit indexing
 *   - complex amplitudes
 *   - SWAP
 *   - controlled-SWAP / Fredkin
 *   - superposition
 *   - measurement probabilities
 *   - entanglement examples
 *   - circuit composition
 *   - validation
 *   - performance considerations
 *
 * The implementation uses only standard JavaScript and runs in Node.js.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. Complex-number utilities
// ---------------------------------------------------------------------------

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

    scale(value) {
        return new Complex(
            this.real * value,
            this.imaginary * value
        );
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

    toString(precision = 3) {
        const real = Math.abs(this.real) < 1e-10 ? 0 : this.real;
        const imaginary =
            Math.abs(this.imaginary) < 1e-10 ? 0 : this.imaginary;

        if (imaginary === 0) {
            return real.toFixed(precision);
        }

        if (real === 0) {
            return `${imaginary.toFixed(precision)}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";
        return (
            `${real.toFixed(precision)}` +
            `${sign}${Math.abs(imaginary).toFixed(precision)}i`
        );
    }
}

const ZERO = () => new Complex(0, 0);
const ONE = () => new Complex(1, 0);

function stateNorm(state) {
    return Math.sqrt(
        state.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        )
    );
}

function normalize(state) {
    const norm = stateNorm(state);

    if (norm < 1e-12) {
        throw new Error("Cannot normalize the zero vector.");
    }

    return state.map(amplitude => amplitude.scale(1 / norm));
}

function validateState(state, qubitCount) {
    const expectedDimension = 2 ** qubitCount;

    if (state.length !== expectedDimension) {
        throw new Error(
            `${qubitCount} qubits require ${expectedDimension} amplitudes.`
        );
    }

    if (Math.abs(stateNorm(state) - 1) > 1e-10) {
        throw new Error("Quantum state is not normalized.");
    }
}

function basisState(bits) {
    if (!/^[01]+$/.test(bits)) {
        throw new Error("Basis state must contain only 0 and 1.");
    }

    const state = Array.from(
        { length: 2 ** bits.length },
        ZERO
    );

    state[parseInt(bits, 2)] = ONE();
    return state;
}

function uniformSuperposition(qubitCount) {
    const dimension = 2 ** qubitCount;
    const amplitude = 1 / Math.sqrt(dimension);

    return Array.from(
        { length: dimension },
        () => new Complex(amplitude, 0)
    );
}

function basisLabel(index, qubitCount) {
    return index.toString(2).padStart(qubitCount, "0");
}

function statesEqual(first, second, tolerance = 1e-10) {
    if (first.length !== second.length) {
        return false;
    }

    return first.every((amplitude, index) => {
        const other = second[index];

        return (
            Math.abs(amplitude.real - other.real) <= tolerance &&
            Math.abs(amplitude.imaginary - other.imaginary) <= tolerance
        );
    });
}

function printState(state, qubitCount, title) {
    validateState(state, qubitCount);

    console.log(`\n${title}`);

    const terms = [];

    state.forEach((amplitude, index) => {
        if (amplitude.magnitude() > 1e-9) {
            terms.push(
                `(${amplitude.toString()})|${basisLabel(index, qubitCount)}>`
            );
        }
    });

    console.log(terms.length ? terms.join(" + ") : "0");
}


// ---------------------------------------------------------------------------
// 2. Qubit indexing
// ---------------------------------------------------------------------------

function getBit(index, qubitCount, qubit) {
    if (qubit < 0 || qubit >= qubitCount) {
        throw new RangeError("Qubit index is outside the circuit.");
    }

    const shift = qubitCount - 1 - qubit;
    return (index >> shift) & 1;
}

function replaceBit(index, qubitCount, qubit, value) {
    if (value !== 0 && value !== 1) {
        throw new Error("A qubit value must be 0 or 1.");
    }

    const shift = qubitCount - 1 - qubit;
    const mask = 1 << shift;

    return value === 1
        ? index | mask
        : index & ~mask;
}

function swapBasisIndex(index, qubitCount, first, second) {
    if (first === second) {
        return index;
    }

    const firstValue = getBit(index, qubitCount, first);
    const secondValue = getBit(index, qubitCount, second);

    if (firstValue === secondValue) {
        return index;
    }

    let result = replaceBit(
        index,
        qubitCount,
        first,
        secondValue
    );

    result = replaceBit(
        result,
        qubitCount,
        second,
        firstValue
    );

    return result;
}


// ---------------------------------------------------------------------------
// 3. Generic permutation application
// ---------------------------------------------------------------------------

function applyPermutation(state, qubitCount, mapping) {
    validateState(state, qubitCount);

    const result = Array.from(
        { length: state.length },
        ZERO
    );

    state.forEach((amplitude, sourceIndex) => {
        const destinationIndex = mapping(sourceIndex);

        if (
            destinationIndex < 0 ||
            destinationIndex >= state.length
        ) {
            throw new Error("Gate produced an invalid state index.");
        }

        result[destinationIndex] =
            result[destinationIndex].add(amplitude);
    });

    return result;
}


// ---------------------------------------------------------------------------
// 4. SWAP
// ---------------------------------------------------------------------------

function swapGate(state, qubitCount, first, second) {
    if (
        first < 0 ||
        second < 0 ||
        first >= qubitCount ||
        second >= qubitCount
    ) {
        throw new RangeError("SWAP qubit index is invalid.");
    }

    return applyPermutation(
        state,
        qubitCount,
        index => swapBasisIndex(
            index,
            qubitCount,
            first,
            second
        )
    );
}

function demonstrateSwapTruthTable() {
    console.log("\n" + "=".repeat(70));
    console.log("SWAP TRUTH TABLE");
    console.log("=".repeat(70));

    ["00", "01", "10", "11"].forEach(bits => {
        const result = swapGate(
            basisState(bits),
            2,
            0,
            1
        );

        const destination = result.findIndex(
            amplitude => amplitude.magnitude() > 1e-9
        );

        console.log(
            `|${bits}> -> |${basisLabel(destination, 2)}>`
        );
    });
}


// ---------------------------------------------------------------------------
// 5. Controlled-SWAP / Fredkin
// ---------------------------------------------------------------------------

function controlledSwapGate(
    state,
    qubitCount,
    control,
    first,
    second
) {
    const distinct = new Set([control, first, second]);

    if (distinct.size !== 3) {
        throw new Error(
            "Controlled-SWAP requires three distinct qubits."
        );
    }

    return applyPermutation(
        state,
        qubitCount,
        index => {
            const controlValue =
                getBit(index, qubitCount, control);

            if (controlValue === 1) {
                return swapBasisIndex(
                    index,
                    qubitCount,
                    first,
                    second
                );
            }

            return index;
        }
    );
}

function demonstrateFredkinTruthTable() {
    console.log("\n" + "=".repeat(70));
    console.log("CONTROLLED-SWAP / FREDKIN TRUTH TABLE");
    console.log("=".repeat(70));

    [
        "000",
        "001",
        "010",
        "011",
        "100",
        "101",
        "110",
        "111"
    ].forEach(bits => {
        const result = controlledSwapGate(
            basisState(bits),
            3,
            0,
            1,
            2
        );

        const destination = result.findIndex(
            amplitude => amplitude.magnitude() > 1e-9
        );

        console.log(
            `|${bits}> -> |${basisLabel(destination, 3)}>`
        );
    });
}


// ---------------------------------------------------------------------------
// 6. Measurement
// ---------------------------------------------------------------------------

function measurementProbabilities(state, qubitCount) {
    validateState(state, qubitCount);

    return state.map(amplitude =>
        amplitude.magnitudeSquared()
    );
}

function measurementDistribution(state, qubitCount) {
    const probabilities =
        measurementProbabilities(state, qubitCount);

    const result = {};

    probabilities.forEach((probability, index) => {
        if (probability > 1e-10) {
            result[basisLabel(index, qubitCount)] = probability;
        }
    });

    return result;
}

function sampleMeasurement(state, qubitCount) {
    const probabilities =
        measurementProbabilities(state, qubitCount);

    const randomValue = Math.random();
    let cumulative = 0;

    for (let index = 0; index < probabilities.length; index++) {
        cumulative += probabilities[index];

        if (randomValue <= cumulative) {
            return basisLabel(index, qubitCount);
        }
    }

    return basisLabel(
        probabilities.length - 1,
        qubitCount
    );
}

function demonstrateMeasurement() {
    console.log("\n" + "=".repeat(70));
    console.log("MEASUREMENT PROBABILITIES");
    console.log("=".repeat(70));

    const state = normalize([
        new Complex(1, 0),
        new Complex(1, 1),
        new Complex(2, 0),
        new Complex(0, 0.5)
    ]);

    const result = swapGate(state, 2, 0, 1);

    console.log("Input:", measurementDistribution(state, 2));
    console.log("After SWAP:", measurementDistribution(result, 2));
    console.log(
        "Norm before:",
        stateNorm(state).toFixed(12)
    );
    console.log(
        "Norm after:",
        stateNorm(result).toFixed(12)
    );

    console.log(
        "Example measurement:",
        sampleMeasurement(result, 2)
    );
}


// ---------------------------------------------------------------------------
// 7. Superposition and coherent control
// ---------------------------------------------------------------------------

function demonstrateSuperposition() {
    console.log("\n" + "=".repeat(70));
    console.log("SUPERPOSITION AND COHERENT CONTROL");
    console.log("=".repeat(70));

    /*
     * Control qubit is q0.
     *
     * Input:
     *   (|001> + |101>) / sqrt(2)
     *
     * Fredkin:
     *   |001> -> |001>
     *   |101> -> |110>
     *
     * The control is in a coherent superposition, so the operation
     * creates a conditional transformation without measuring the control.
     */
    const amplitude = 1 / Math.sqrt(2);

    const state = Array.from(
        { length: 8 },
        ZERO
    );

    state[1] = new Complex(amplitude, 0);
    state[5] = new Complex(amplitude, 0);

    const result = controlledSwapGate(
        state,
        3,
        0,
        1,
        2
    );

    printState(state, 3, "Input");
    printState(result, 3, "After Fredkin");

    const expected = Array.from(
        { length: 8 },
        ZERO
    );

    expected[1] = new Complex(amplitude, 0);
    expected[6] = new Complex(amplitude, 0);

    console.log(
        "Matches expected state:",
        statesEqual(result, expected)
    );
}


// ---------------------------------------------------------------------------
// 8. Bell state and SWAP symmetry
// ---------------------------------------------------------------------------

function demonstrateEntangledState() {
    console.log("\n" + "=".repeat(70));
    console.log("SWAP ON ENTANGLED STATES");
    console.log("=".repeat(70));

    const amplitude = 1 / Math.sqrt(2);

    // |Phi+> = (|00> + |11>) / sqrt(2)
    const bellState = [
        new Complex(amplitude, 0),
        ZERO(),
        ZERO(),
        new Complex(amplitude, 0)
    ];

    const swappedBell = swapGate(
        bellState,
        2,
        0,
        1
    );

    printState(
        bellState,
        2,
        "Bell state |Phi+>"
    );

    console.log(
        "SWAP leaves |Phi+> unchanged:",
        statesEqual(bellState, swappedBell)
    );

    // The singlet is antisymmetric:
    // |Psi-> = (|01> - |10>) / sqrt(2)
    const singlet = [
        ZERO(),
        new Complex(amplitude, 0),
        new Complex(-amplitude, 0),
        ZERO()
    ];

    const swappedSinglet = swapGate(
        singlet,
        2,
        0,
        1
    );

    const expectedSinglet = singlet.map(
        amplitudeValue => amplitudeValue.scale(-1)
    );

    console.log(
        "SWAP gives the singlet a global phase of -1:",
        statesEqual(
            swappedSinglet,
            expectedSinglet
        )
    );
}


// ---------------------------------------------------------------------------
// 9. CNOT and SWAP decomposition
// ---------------------------------------------------------------------------

function cnotGate(
    state,
    qubitCount,
    control,
    target
) {
    if (control === target) {
        throw new Error(
            "CNOT control and target must differ."
        );
    }

    return applyPermutation(
        state,
        qubitCount,
        index => {
            if (getBit(index, qubitCount, control) === 1) {
                const targetValue =
                    getBit(index, qubitCount, target);

                return replaceBit(
                    index,
                    qubitCount,
                    target,
                    1 - targetValue
                );
            }

            return index;
        }
    );
}

function swapViaThreeCNOTs(
    state,
    qubitCount,
    first,
    second
) {
    let result = cnotGate(
        state,
        qubitCount,
        first,
        second
    );

    result = cnotGate(
        result,
        qubitCount,
        second,
        first
    );

    result = cnotGate(
        result,
        qubitCount,
        first,
        second
    );

    return result;
}

function demonstrateSwapDecomposition() {
    console.log("\n" + "=".repeat(70));
    console.log("SWAP AS THREE CNOT GATES");
    console.log("=".repeat(70));

    const state = normalize([
        new Complex(1, 0),
        new Complex(0, 2),
        new Complex(1, -1),
        new Complex(0.5, 0)
    ]);

    const direct = swapGate(
        state,
        2,
        0,
        1
    );

    const decomposed = swapViaThreeCNOTs(
        state,
        2,
        0,
        1
    );

    console.log(
        "Direct SWAP equals CNOT decomposition:",
        statesEqual(direct, decomposed)
    );
}


// ---------------------------------------------------------------------------
// 10. Circuit abstraction
// ---------------------------------------------------------------------------

class QuantumCircuit {
    constructor(qubitCount) {
        if (!Number.isInteger(qubitCount) || qubitCount <= 0) {
            throw new Error(
                "Circuit must contain at least one qubit."
            );
        }

        this.qubitCount = qubitCount;
        this.operations = [];
    }

    validateQubits(qubits) {
        qubits.forEach(qubit => {
            if (
                !Number.isInteger(qubit) ||
                qubit < 0 ||
                qubit >= this.qubitCount
            ) {
                throw new RangeError(
                    `Qubit ${qubit} is outside the circuit.`
                );
            }
        });
    }

    addSwap(first, second) {
        this.validateQubits([first, second]);

        this.operations.push({
            name: "SWAP",
            qubits: [first, second]
        });
    }

    addControlledSwap(control, first, second) {
        this.validateQubits([
            control,
            first,
            second
        ]);

        if (
            new Set([
                control,
                first,
                second
            ]).size !== 3
        ) {
            throw new Error(
                "Fredkin qubits must be distinct."
            );
        }

        this.operations.push({
            name: "CSWAP",
            qubits: [
                control,
                first,
                second
            ]
        });
    }

    run(initialState) {
        let state = normalize(initialState);

        for (const operation of this.operations) {
            if (operation.name === "SWAP") {
                state = swapGate(
                    state,
                    this.qubitCount,
                    operation.qubits[0],
                    operation.qubits[1]
                );
            } else if (operation.name === "CSWAP") {
                state = controlledSwapGate(
                    state,
                    this.qubitCount,
                    operation.qubits[0],
                    operation.qubits[1],
                    operation.qubits[2]
                );
            } else {
                throw new Error(
                    `Unknown operation: ${operation.name}`
                );
            }
        }

        return state;
    }

    describe() {
        console.log("\nCircuit:");

        this.operations.forEach(
            (operation, index) => {
                console.log(
                    `  ${index + 1}. ` +
                    `${operation.name}(` +
                    `${operation.qubits.join(", ")})`
                );
            }
        );
    }
}

function demonstrateCircuit() {
    console.log("\n" + "=".repeat(70));
    console.log("MULTI-OPERATION CIRCUIT");
    console.log("=".repeat(70));

    const circuit = new QuantumCircuit(3);

    circuit.addSwap(0, 2);
    circuit.addControlledSwap(1, 0, 2);
    circuit.addSwap(0, 1);

    circuit.describe();

    const initial = uniformSuperposition(3);
    const final = circuit.run(initial);

    printState(
        initial,
        3,
        "Initial uniform state"
    );

    printState(
        final,
        3,
        "Final state"
    );
}


// ---------------------------------------------------------------------------
// 11. Edge cases
// ---------------------------------------------------------------------------

function demonstrateEdgeCases() {
    console.log("\n" + "=".repeat(70));
    console.log("EDGE CASES AND VALIDATION");
    console.log("=".repeat(70));

    const state = basisState("101");

    // SWAP(q, q) is the identity permutation.
    const sameQubit = swapGate(
        state,
        3,
        1,
        1
    );

    console.log(
        "SWAP(q, q) is identity:",
        statesEqual(state, sameQubit)
    );

    try {
        controlledSwapGate(
            state,
            3,
            0,
            0,
            2
        );
    } catch (error) {
        console.log(
            "Invalid Fredkin gate rejected:",
            error.message
        );
    }

    try {
        swapGate(
            state,
            3,
            0,
            3
        );
    } catch (error) {
        console.log(
            "Invalid qubit rejected:",
            error.message
        );
    }

    try {
        validateState(
            [
                ONE(),
                ONE()
            ],
            1
        );
    } catch (error) {
        console.log(
            "Unnormalized state rejected:",
            error.message
        );
    }
}


// ---------------------------------------------------------------------------
// 12. Main
// ---------------------------------------------------------------------------

function main() {
    console.log("=".repeat(70));
    console.log(
        "SWAP & CONTROLLED-SWAP: MULTI-QUBIT OPERATIONS"
    );
    console.log("=".repeat(70));

    demonstrateSwapTruthTable();
    demonstrateFredkinTruthTable();
    demonstrateMeasurement();
    demonstrateSuperposition();
    demonstrateEntangledState();
    demonstrateSwapDecomposition();
    demonstrateCircuit();
    demonstrateEdgeCases();

    console.log("\n" + "=".repeat(70));
    console.log("PERFORMANCE");
    console.log("=".repeat(70));
    console.log(
        "An n-qubit state vector contains 2^n amplitudes."
    );
    console.log(
        "A direct permutation-based SWAP or Fredkin simulation " +
        "therefore processes O(2^n) amplitudes."
    );
    console.log(
        "The classical simulator has exponential memory growth, " +
        "while the physical quantum operation acts locally on qubits."
    );

    console.log("\nProgram completed successfully.");
}

main();
