/*
 * CNOT Gate: Entanglement and Computation
 * =======================================
 *
 * Self-contained JavaScript study implementation.
 *
 * Demonstrates:
 *   - classical XOR
 *   - qubits and amplitudes
 *   - complex arithmetic
 *   - state-vector simulation
 *   - tensor products
 *   - CNOT matrix and basis action
 *   - superposition
 *   - Bell-state generation
 *   - measurement
 *   - separability
 *   - density matrices
 *   - entanglement entropy
 *   - phase kickback
 *   - reversible computation
 *   - quantum teleportation state evolution
 *   - superdense coding
 *   - circuit composition
 *   - validation and numerical precision
 *
 * Run with:
 *   node cnot_entanglement.js
 *
 * No external packages are required.
 */


// ============================================================================
// 1. COMPLEX NUMBERS
// ============================================================================

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

    subtract(other) {
        return new Complex(
            this.real - other.real,
            this.imaginary - other.imaginary
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

    isApproximatelyZero(tolerance = 1e-10) {
        return this.magnitude() <= tolerance;
    }

    toString() {
        if (Math.abs(this.imaginary) < 1e-10) {
            return this.real.toFixed(4);
        }

        if (Math.abs(this.real) < 1e-10) {
            return `${this.imaginary.toFixed(4)}i`;
        }

        const sign = this.imaginary >= 0 ? "+" : "-";
        return (
            `${this.real.toFixed(4)} ${sign} ` +
            `${Math.abs(this.imaginary).toFixed(4)}i`
        );
    }
}

const ZERO = () => new Complex(0, 0);
const ONE = () => new Complex(1, 0);
const IMAGINARY_ONE = () => new Complex(0, 1);


// ============================================================================
// 2. VECTOR AND MATRIX OPERATIONS
// ============================================================================

function vectorNorm(state) {
    return Math.sqrt(
        state.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        )
    );
}

function normalize(state) {
    const norm = vectorNorm(state);

    if (norm === 0) {
        throw new Error("The zero vector cannot represent a quantum state.");
    }

    return state.map(amplitude => amplitude.scale(1 / norm));
}

function innerProduct(left, right) {
    if (left.length !== right.length) {
        throw new Error("Vector dimensions must match.");
    }

    return left.reduce(
        (sum, value, index) =>
            sum.add(value.conjugate().multiply(right[index])),
        ZERO()
    );
}

function matrixVectorMultiply(matrix, vector) {
    if (matrix.length === 0) {
        throw new Error("Matrix cannot be empty.");
    }

    const width = matrix[0].length;

    if (width !== vector.length) {
        throw new Error("Matrix and vector dimensions do not match.");
    }

    return matrix.map(row => {
        return row.reduce(
            (sum, value, column) =>
                sum.add(value.multiply(vector[column])),
            ZERO()
        );
    });
}

function matrixMultiply(left, right) {
    if (left.length === 0 || right.length === 0) {
        throw new Error("Matrices cannot be empty.");
    }

    const leftWidth = left[0].length;
    const rightWidth = right[0].length;

    if (leftWidth !== right.length) {
        throw new Error("Matrix dimensions do not match.");
    }

    return left.map((leftRow, row) => {
        return Array.from({ length: rightWidth }, (_, column) => {
            return leftRow.reduce(
                (sum, value, index) =>
                    sum.add(value.multiply(right[index][column])),
                ZERO()
            );
        });
    });
}

function dagger(matrix) {
    return matrix[0].map((_, column) => {
        return matrix.map(row => row[column].conjugate());
    });
}

function identityMatrix(size) {
    return Array.from({ length: size }, (_, row) => {
        return Array.from({ length: size }, (_, column) =>
            row === column ? ONE() : ZERO()
        );
    });
}

function matricesApproximatelyEqual(left, right, tolerance = 1e-10) {
    if (left.length !== right.length) {
        return false;
    }

    return left.every((row, r) => {
        if (row.length !== right[r].length) {
            return false;
        }

        return row.every((value, c) => {
            return value
                .subtract(right[r][c])
                .magnitude() <= tolerance;
        });
    });
}


// ============================================================================
// 3. BASIC QUANTUM GATES
// ============================================================================

const I = [
    [ONE(), ZERO()],
    [ZERO(), ONE()]
];

const X = [
    [ZERO(), ONE()],
    [ONE(), ZERO()]
];

const Y = [
    [ZERO(), new Complex(0, -1)],
    [IMAGINARY_ONE(), ZERO()]
];

const Z = [
    [ONE(), ZERO()],
    [ZERO(), new Complex(-1, 0)]
];

const H = [
    [new Complex(1 / Math.sqrt(2), 0), new Complex(1 / Math.sqrt(2), 0)],
    [new Complex(1 / Math.sqrt(2), 0), new Complex(-1 / Math.sqrt(2), 0)]
];

/*
 * Computational basis ordering:
 *
 * |00> = [1,0,0,0]
 * |01> = [0,1,0,0]
 * |10> = [0,0,1,0]
 * |11> = [0,0,0,1]
 *
 * CNOT:
 *
 * |00> -> |00>
 * |01> -> |01>
 * |10> -> |11>
 * |11> -> |10>
 */
const CNOT = [
    [ONE(), ZERO(), ZERO(), ZERO()],
    [ZERO(), ONE(), ZERO(), ZERO()],
    [ZERO(), ZERO(), ZERO(), ONE()],
    [ZERO(), ZERO(), ONE(), ZERO()]
];

function tensorProduct(left, right) {
    return left.flatMap(leftValue =>
        right.map(rightValue => leftValue.multiply(rightValue))
    );
}

function tensorMatrix(left, right) {
    return left.flatMap(leftRow =>
        right.map(rightRow =>
            leftRow.flatMap(leftValue =>
                rightRow.map(rightValue =>
                    leftValue.multiply(rightValue)
                )
            )
        )
    );
}

function basisState(bits) {
    if (!/^[01]+$/.test(bits)) {
        throw new Error("Basis-state notation must contain only 0 and 1.");
    }

    const dimension = 2 ** bits.length;
    const state = Array.from({ length: dimension }, () => ZERO());
    state[parseInt(bits, 2)] = ONE();

    return state;
}

function printState(state, label = "state", tolerance = 1e-10) {
    const qubits = Math.log2(state.length);

    if (!Number.isInteger(qubits)) {
        throw new Error("State dimension must be a power of two.");
    }

    const terms = [];

    state.forEach((amplitude, index) => {
        if (amplitude.magnitude() > tolerance) {
            const bits = index.toString(2).padStart(qubits, "0");
            terms.push(`(${amplitude.toString()})|${bits}>`);
        }
    });

    console.log(`${label}: ${terms.length ? terms.join(" + ") : "0"}`);
}


// ============================================================================
// 4. CLASSICAL XOR AND CNOT
// ============================================================================

function xorBit(a, b) {
    if (![0, 1].includes(a) || ![0, 1].includes(b)) {
        throw new Error("XOR inputs must be binary.");
    }

    return a ^ b;
}

function classicalCNOT(control, target) {
    if (![0, 1].includes(control) || ![0, 1].includes(target)) {
        throw new Error("CNOT inputs must be binary.");
    }

    return [control, target ^ control];
}

function demonstrateTruthTable() {
    console.log("\n=== CNOT truth table ===");

    for (const control of [0, 1]) {
        for (const target of [0, 1]) {
            const output = classicalCNOT(control, target);
            console.log(
                `|${control}${target}> -> ` +
                `|${output[0]}${output[1]}>`
            );
        }
    }
}


// ============================================================================
// 5. SINGLE-QUBIT OPERATIONS
// ============================================================================

function applyOneQubitGateToTwoQubits(state, gate, qubit) {
    if (state.length !== 4) {
        throw new Error("Expected a two-qubit state.");
    }

    if (![0, 1].includes(qubit)) {
        throw new Error("Qubit must be 0 or 1.");
    }

    const operator = qubit === 0
        ? tensorMatrix(gate, I)
        : tensorMatrix(I, gate);

    return matrixVectorMultiply(operator, state);
}

function applyCNOT(state) {
    if (state.length !== 4) {
        throw new Error("This CNOT implementation expects two qubits.");
    }

    return matrixVectorMultiply(CNOT, state);
}


// ============================================================================
// 6. BELL STATES
// ============================================================================

function zeroQubit() {
    return [ONE(), ZERO()];
}

function oneQubit() {
    return [ZERO(), ONE()];
}

function plusQubit() {
    return normalize([ONE(), ONE()]);
}

function minusQubit() {
    return normalize([ONE(), new Complex(-1, 0)]);
}

function bellPhiPlus() {
    /*
     * |00>
     *  H on the first qubit
     *  CNOT
     *
     * Result:
     * |Phi+> = (|00> + |11>) / sqrt(2)
     */
    const afterH = tensorProduct(plusQubit(), zeroQubit());
    return applyCNOT(afterH);
}

function bellPhiMinus() {
    const afterH = tensorProduct(minusQubit(), zeroQubit());
    return applyCNOT(afterH);
}

function bellPsiPlus() {
    const afterH = tensorProduct(plusQubit(), oneQubit());
    return applyCNOT(afterH);
}

function bellPsiMinus() {
    const afterH = tensorProduct(minusQubit(), oneQubit());
    return applyCNOT(afterH);
}

function demonstrateBellStates() {
    console.log("\n=== Bell states ===");

    const states = {
        "Phi+": bellPhiPlus(),
        "Phi-": bellPhiMinus(),
        "Psi+": bellPsiPlus(),
        "Psi-": bellPsiMinus()
    };

    for (const [name, state] of Object.entries(states)) {
        printState(state, name);
        console.log("  norm =", vectorNorm(state).toFixed(8));
    }
}


// ============================================================================
// 7. MEASUREMENT
// ============================================================================

function measurementProbabilities(state) {
    const norm = vectorNorm(state);

    if (Math.abs(norm - 1) > 1e-10) {
        throw new Error("Measurement requires a normalized state.");
    }

    return state.map(amplitude => amplitude.magnitudeSquared());
}

function sampleMeasurement(state, shots = 1000, randomFunction = Math.random) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new Error("Shots must be a positive integer.");
    }

    const probabilities = measurementProbabilities(state);
    const cumulative = [];
    let total = 0;

    for (const probability of probabilities) {
        total += probability;
        cumulative.push(total);
    }

    const counts = {};
    const qubits = Math.log2(state.length);

    for (let shot = 0; shot < shots; shot++) {
        const randomValue = randomFunction();
        const index = cumulative.findIndex(value => randomValue < value);
        const outcome = index === -1 ? probabilities.length - 1 : index;
        const bits = outcome.toString(2).padStart(qubits, "0");

        counts[bits] = (counts[bits] || 0) + 1;
    }

    return Object.fromEntries(
        Object.entries(counts).sort()
    );
}

function demonstrateMeasurement() {
    console.log("\n=== Bell-state measurement ===");

    const state = bellPhiPlus();
    const probabilities = measurementProbabilities(state);

    probabilities.forEach((probability, index) => {
        const bits = index.toString(2).padStart(2, "0");
        console.log(`P(|${bits}>) = ${probability.toFixed(3)}`);
    });

    console.log(
        "1000 simulated measurements:",
        sampleMeasurement(state, 1000)
    );
}


// ============================================================================
// 8. PURE-STATE SEPARABILITY
// ============================================================================

function isProductTwoQubitState(state, tolerance = 1e-10) {
    if (state.length !== 4) {
        throw new Error("Expected four amplitudes.");
    }

    const determinant = state[0]
        .multiply(state[3])
        .subtract(state[1].multiply(state[2]));

    return determinant.magnitude() <= tolerance;
}

function demonstrateSeparability() {
    console.log("\n=== Separability ===");

    const product = tensorProduct(plusQubit(), zeroQubit());
    const entangled = bellPhiPlus();

    printState(product, "Product state");
    console.log(
        "Product state separable:",
        isProductTwoQubitState(product)
    );

    printState(entangled, "Bell state");
    console.log(
        "Bell state separable:",
        isProductTwoQubitState(entangled)
    );
}


// ============================================================================
// 9. DENSITY MATRICES AND REDUCED STATES
// ============================================================================

function outerProduct(state) {
    return state.map(rowAmplitude =>
        state.map(columnAmplitude =>
            rowAmplitude.multiply(columnAmplitude.conjugate())
        )
    );
}

function partialTraceSecondQubit(state) {
    if (state.length !== 4) {
        throw new Error("Expected a two-qubit state.");
    }

    const [a, b, c, d] = state;

    return [
        [
            new Complex(
                a.magnitudeSquared() + b.magnitudeSquared(),
                0
            ),
            a.multiply(c.conjugate())
                .add(b.multiply(d.conjugate()))
        ],
        [
            c.multiply(a.conjugate())
                .add(d.multiply(b.conjugate())),
            new Complex(
                c.magnitudeSquared() + d.magnitudeSquared(),
                0
            )
        ]
    ];
}

function matrixTrace(matrix) {
    return matrix.reduce(
        (sum, row, index) => sum.add(row[index]),
        ZERO()
    );
}

function purity(densityMatrix) {
    const squared = matrixMultiply(densityMatrix, densityMatrix);
    return matrixTrace(squared).real;
}

function entropyOfTwoByTwoDensityMatrix(densityMatrix) {
    /*
     * For a trace-one 2x2 density matrix:
     *
     * lambda± = (1 ± sqrt(1 - 4 det(rho))) / 2
     *
     * S(rho) = -sum lambda log2(lambda)
     */
    const determinant = densityMatrix[0][0]
        .multiply(densityMatrix[1][1])
        .subtract(
            densityMatrix[0][1].multiply(densityMatrix[1][0])
        )
        .real;

    const safeDeterminant = Math.max(
        0,
        Math.min(0.25, determinant)
    );

    const root = Math.sqrt(
        Math.max(0, 1 - 4 * safeDeterminant)
    );

    const eigenvalues = [
        (1 + root) / 2,
        (1 - root) / 2
    ];

    return eigenvalues.reduce((entropy, value) => {
        if (value <= 1e-15) {
            return entropy;
        }

        return entropy - value * Math.log2(value);
    }, 0);
}

function demonstrateDensityMatrix() {
    console.log("\n=== Reduced density matrices ===");

    const product = tensorProduct(plusQubit(), zeroQubit());
    const bell = bellPhiPlus();

    const productReduced = partialTraceSecondQubit(product);
    const bellReduced = partialTraceSecondQubit(bell);

    console.log(
        "Product reduced purity:",
        purity(productReduced).toFixed(6)
    );

    console.log(
        "Bell reduced purity:",
        purity(bellReduced).toFixed(6)
    );

    console.log(
        "Bell reduced entropy:",
        entropyOfTwoByTwoDensityMatrix(bellReduced).toFixed(6)
    );
}


// ============================================================================
// 10. PHASE KICKBACK
// ============================================================================

function demonstratePhaseKickback() {
    console.log("\n=== Phase kickback ===");

    /*
     * X|-> = -|->.
     *
     * Therefore CNOT with |-> as the target can produce a phase
     * on the control component without changing the target's
     * observable computational-basis probabilities.
     */

    const input = tensorProduct(plusQubit(), minusQubit());
    const output = applyCNOT(input);

    printState(input, "Input");
    printState(output, "After CNOT");

    console.log(
        "This illustrates why controlled operations are useful in "
        + "interference-based quantum algorithms."
    );
}


// ============================================================================
// 11. THREE-QUBIT OPERATIONS FOR TELEPORTATION
// ============================================================================

function applySingleQubitGateToThreeQubits(state, gate, qubit) {
    if (state.length !== 8) {
        throw new Error("Expected an eight-amplitude three-qubit state.");
    }

    if (![0, 1, 2].includes(qubit)) {
        throw new Error("Qubit index must be 0, 1, or 2.");
    }

    const output = Array.from({ length: 8 }, () => ZERO());

    for (let index = 0; index < 8; index++) {
        const bits = index.toString(2).padStart(3, "0");
        const inputBit = Number(bits[qubit]);

        for (let outputBit = 0; outputBit < 2; outputBit++) {
            const coefficient = gate[outputBit][inputBit];
            const newBits = bits.split("");
            newBits[qubit] = String(outputBit);
            const newIndex = parseInt(newBits.join(""), 2);

            output[newIndex] = output[newIndex].add(
                coefficient.multiply(state[index])
            );
        }
    }

    return output;
}

function applyCNOTToThreeQubits(state, control, target) {
    if (state.length !== 8) {
        throw new Error("Expected a three-qubit state.");
    }

    if (control === target) {
        throw new Error("Control and target must differ.");
    }

    const output = Array.from({ length: 8 }, () => ZERO());

    for (let index = 0; index < 8; index++) {
        const bits = index.toString(2).padStart(3, "0");
        const newBits = bits.split("");

        if (bits[control] === "1") {
            newBits[target] = bits[target] === "0" ? "1" : "0";
        }

        const newIndex = parseInt(newBits.join(""), 2);
        output[newIndex] = output[newIndex].add(state[index]);
    }

    return output;
}

function demonstrateTeleportation() {
    console.log("\n=== Quantum teleportation ===");

    /*
     * Unknown state:
     *     |psi> = alpha|0> + beta|1>
     *
     * We choose a normalized example state with a complex beta.
     */
    const alpha = new Complex(1 / Math.sqrt(3), 0);
    const beta = new Complex(0, Math.sqrt(2 / 3));

    let state = tensorProduct(
        tensorProduct([alpha, beta], zeroQubit()),
        zeroQubit()
    );

    // Create an entangled Bell pair between qubits 1 and 2.
    state = applySingleQubitGateToThreeQubits(state, H, 1);
    state = applyCNOTToThreeQubits(state, 1, 2);

    // Alice performs the Bell-basis transformation.
    state = applyCNOTToThreeQubits(state, 0, 1);
    state = applySingleQubitGateToThreeQubits(state, H, 0);

    printState(
        state,
        "State immediately before Alice's measurement"
    );

    console.log(
        "The two measurement bits determine which Pauli correction "
        + "Bob must apply."
    );
}


// ============================================================================
// 12. SUPERDENSE CODING
// ============================================================================

function demonstrateSuperdenseCoding() {
    console.log("\n=== Superdense coding ===");

    /*
     * Alice and Bob share |Phi+>.
     *
     * Alice encodes:
     *   00 -> I
     *   01 -> X
     *   10 -> Z
     *   11 -> XZ
     *
     * Bob applies CNOT followed by H and measures both qubits.
     */
    const encodings = {
        "00": I,
        "01": X,
        "10": Z,
        "11": matrixMultiply(X, Z)
    };

    for (const [message, encoding] of Object.entries(encodings)) {
        let state = bellPhiPlus();

        state = applyOneQubitGateToTwoQubits(
            state,
            encoding,
            0
        );

        state = applyCNOT(state);

        state = applyOneQubitGateToTwoQubits(
            state,
            H,
            0
        );

        const probabilities = measurementProbabilities(state);

        const decodedIndex = probabilities.reduce(
            (best, probability, index) =>
                probability > probabilities[best] ? index : best,
            0
        );

        const decoded = decodedIndex
            .toString(2)
            .padStart(2, "0");

        console.log(
            `message=${message}, decoded=${decoded},`,
            probabilities
        );
    }
}


// ============================================================================
// 13. REVERSIBLE LOGIC
// ============================================================================

function reversibleAND(a, b, target = 0) {
    if (
        ![0, 1].includes(a) ||
        ![0, 1].includes(b) ||
        ![0, 1].includes(target)
    ) {
        throw new Error("Inputs must be binary.");
    }

    return [a, b, target ^ (a & b)];
}

function demonstrateReversibleLogic() {
    console.log("\n=== Reversible computation ===");

    for (const a of [0, 1]) {
        for (const b of [0, 1]) {
            console.log(
                `${a}${b}0 ->`,
                reversibleAND(a, b)
            );
        }
    }

    console.log(
        "CNOT performs reversible XOR into a target. "
        + "Reversible transformations are compatible with unitary "
        + "quantum evolution."
    );
}


// ============================================================================
// 14. CIRCUIT CLASS
// ============================================================================

class TwoQubitCircuit {
    constructor() {
        this.state = basisState("00");
    }

    applyH(qubit) {
        this.state = applyOneQubitGateToTwoQubits(
            this.state,
            H,
            qubit
        );
        return this;
    }

    applyX(qubit) {
        this.state = applyOneQubitGateToTwoQubits(
            this.state,
            X,
            qubit
        );
        return this;
    }

    applyZ(qubit) {
        this.state = applyOneQubitGateToTwoQubits(
            this.state,
            Z,
            qubit
        );
        return this;
    }

    applyCNOT(control, target) {
        if (control === 0 && target === 1) {
            this.state = applyCNOT(this.state);
            return this;
        }

        if (control === 1 && target === 0) {
            const output = Array.from(
                { length: 4 },
                () => ZERO()
            );

            for (let index = 0; index < 4; index++) {
                const bits = index
                    .toString(2)
                    .padStart(2, "0")
                    .split("");

                if (bits[control] === "1") {
                    bits[target] =
                        bits[target] === "0" ? "1" : "0";
                }

                const newIndex = parseInt(bits.join(""), 2);

                output[newIndex] = output[newIndex].add(
                    this.state[index]
                );
            }

            this.state = output;
            return this;
        }

        throw new Error(
            "Control and target must be different and within range."
        );
    }

    probabilities() {
        const probabilities = measurementProbabilities(this.state);

        return Object.fromEntries(
            probabilities.map((probability, index) => [
                index.toString(2).padStart(2, "0"),
                probability
            ])
        );
    }
}

function demonstrateCircuitClass() {
    console.log("\n=== Circuit abstraction ===");

    const circuit = new TwoQubitCircuit()
        .applyH(0)
        .applyCNOT(0, 1);

    printState(circuit.state, "Bell state");
    console.log("Probabilities:", circuit.probabilities());
}


// ============================================================================
// 15. GLOBAL PHASE
// ============================================================================

function statesDifferOnlyByGlobalPhase(
    left,
    right,
    tolerance = 1e-10
) {
    if (left.length !== right.length) {
        return false;
    }

    let phase = null;

    for (let index = 0; index < right.length; index++) {
        if (right[index].magnitude() > tolerance) {
            phase = left[index].multiply(
                right[index].conjugate()
            );

            const denominator = right[index].magnitudeSquared();

            phase = phase.scale(1 / denominator);
            break;
        }
    }

    if (phase === null) {
        return left.every(
            amplitude => amplitude.magnitude() <= tolerance
        );
    }

    if (Math.abs(phase.magnitude() - 1) > tolerance) {
        return false;
    }

    return left.every((amplitude, index) =>
        amplitude.subtract(
            phase.multiply(right[index])
        ).magnitude() <= tolerance
    );
}

function demonstratePhase() {
    console.log("\n=== Global versus relative phase ===");

    const state = plusQubit();

    const globalPhase = state.map(
        amplitude => IMAGINARY_ONE().multiply(amplitude)
    );

    const relativePhase = minusQubit();

    console.log(
        "Global-phase equivalent:",
        statesDifferOnlyByGlobalPhase(state, globalPhase)
    );

    console.log(
        "Relative-phase equivalent:",
        statesDifferOnlyByGlobalPhase(state, relativePhase)
    );
}


// ============================================================================
// 16. MEMORY SCALING
// ============================================================================

function estimatedStateVectorBytes(qubits) {
    if (!Number.isInteger(qubits) || qubits < 0) {
        throw new Error("Qubit count must be a non-negative integer.");
    }

    // 16 bytes is the compact size of one IEEE-style complex128 value.
    return 16 * 2 ** qubits;
}

function humanBytes(bytes) {
    const units = ["B", "KiB", "MiB", "GiB", "TiB"];
    let value = bytes;

    for (const unit of units) {
        if (value < 1024 || unit === units[units.length - 1]) {
            return `${value.toFixed(2)} ${unit}`;
        }

        value /= 1024;
    }

    return `${value.toFixed(2)} TiB`;
}

function demonstrateScaling() {
    console.log("\n=== State-vector scaling ===");

    for (const qubits of [1, 2, 10, 20, 30]) {
        const amplitudes = 2 ** qubits;
        const bytes = estimatedStateVectorBytes(qubits);

        console.log(
            `${qubits} qubits -> ${amplitudes.toLocaleString()} ` +
            `amplitudes -> ${humanBytes(bytes)} compact storage`
        );
    }
}


// ============================================================================
// 17. VALIDATION AND TESTS
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function approximatelyEqual(a, b, tolerance = 1e-10) {
    return Math.abs(a - b) <= tolerance;
}

function runTests() {
    console.log("\n=== Tests ===");

    assert(
        JSON.stringify(classicalCNOT(0, 0)) === JSON.stringify([0, 0]),
        "CNOT 00"
    );

    assert(
        JSON.stringify(classicalCNOT(0, 1)) === JSON.stringify([0, 1]),
        "CNOT 01"
    );

    assert(
        JSON.stringify(classicalCNOT(1, 0)) === JSON.stringify([1, 1]),
        "CNOT 10"
    );

    assert(
        JSON.stringify(classicalCNOT(1, 1)) === JSON.stringify([1, 0]),
        "CNOT 11"
    );

    const unitaryCheck = matrixMultiply(
        dagger(CNOT),
        CNOT
    );

    assert(
        matricesApproximatelyEqual(
            unitaryCheck,
            identityMatrix(4)
        ),
        "CNOT must be unitary"
    );

    const inverseCheck = matrixMultiply(CNOT, CNOT);

    assert(
        matricesApproximatelyEqual(
            inverseCheck,
            identityMatrix(4)
        ),
        "CNOT must be self-inverse"
    );

    const bell = bellPhiPlus();

    assert(
        approximatelyEqual(vectorNorm(bell), 1),
        "Bell state must be normalized"
    );

    assert(
        !isProductTwoQubitState(bell),
        "Bell state must be entangled"
    );

    const probabilities = measurementProbabilities(bell);

    assert(
        approximatelyEqual(probabilities[0], 0.5),
        "P(00)"
    );

    assert(
        approximatelyEqual(probabilities[3], 0.5),
        "P(11)"
    );

    assert(
        approximatelyEqual(probabilities[1], 0),
        "P(01)"
    );

    assert(
        approximatelyEqual(probabilities[2], 0),
        "P(10)"
    );

    const bellReduced = partialTraceSecondQubit(bell);

    assert(
        approximatelyEqual(
            entropyOfTwoByTwoDensityMatrix(bellReduced),
            1
        ),
        "Bell-state entropy"
    );

    assert(
        statesDifferOnlyByGlobalPhase(
            bell,
            bell.map(amplitude =>
                IMAGINARY_ONE().multiply(amplitude)
            )
        ),
        "Global phase"
    );

    console.log("All tests passed.");
}


// ============================================================================
// 18. ERROR-HANDLING EXAMPLES
// ============================================================================

function demonstrateErrors() {
    console.log("\n=== Error handling ===");

    const operations = [
        [
            "Invalid basis state",
            () => basisState("012")
        ],
        [
            "Wrong CNOT dimension",
            () => applyCNOT([ONE(), ZERO()])
        ],
        [
            "Invalid XOR",
            () => xorBit(2, 1)
        ],
        [
            "Measurement of unnormalized state",
            () => measurementProbabilities([ONE(), ONE()])
        ]
    ];

    for (const [name, operation] of operations) {
        try {
            operation();
            console.log(name, "unexpectedly succeeded");
        } catch (error) {
            console.log(name, "->", error.message);
        }
    }
}


// ============================================================================
// 19. MAIN EXECUTION
// ============================================================================

function main() {
    console.log("=".repeat(72));
    console.log("CNOT GATE: ENTANGLEMENT AND COMPUTATION");
    console.log("=".repeat(72));

    console.log(
        "\nCNOT maps |c,t> to |c,t XOR c>. " +
        "It is reversible and unitary."
    );

    demonstrateTruthTable();
    demonstrateBellStates();
    demonstrateMeasurement();
    demonstrateSeparability();
    demonstrateDensityMatrix();
    demonstratePhaseKickback();
    demonstrateTeleportation();
    demonstrateSuperdenseCoding();
    demonstrateReversibleLogic();
    demonstrateCircuitClass();
    demonstratePhase();
    demonstrateScaling();
    demonstrateErrors();
    runTests();

    console.log("\n=== Key equations ===");
    console.log("CNOT |c,t> = |c,t XOR c>");
    console.log("|Phi+> = (|00> + |11>) / sqrt(2)");
    console.log("P(x) = |amplitude_x|^2");
    console.log("U†U = I");
    console.log("CNOT² = I");
    console.log("n-qubit state-vector dimension = 2^n");

    console.log("\nStudy complete.");
}


main();
