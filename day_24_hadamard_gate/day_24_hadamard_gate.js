"use strict";

/*
 * Hadamard Gate: Creating Superposition
 * =====================================
 *
 * This file demonstrates:
 * - computational-basis states
 * - amplitudes and probabilities
 * - the Hadamard matrix
 * - H|0> and H|1>
 * - normalization
 * - measurement
 * - phase and interference
 * - H^2 = I
 * - multi-qubit state vectors
 * - two-qubit superposition
 * - Bell-state preparation with H + CNOT
 * - sampling
 * - validation
 * - state-vector simulation complexity
 *
 * Run with:
 *     node hadamard.js
 *
 * Complex numbers are represented by a small immutable Complex class because
 * JavaScript does not have a built-in complex-number primitive.
 */

const SQRT_TWO = Math.sqrt(2);
const H_SCALE = 1 / SQRT_TWO;
const EPSILON = 1e-12;

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
        if (typeof other === "number") {
            return new Complex(
                this.real * other,
                this.imaginary * other
            );
        }

        return new Complex(
            this.real * other.real - this.imaginary * other.imaginary,
            this.real * other.imaginary + this.imaginary * other.real
        );
    }

    magnitudeSquared() {
        return this.real * this.real + this.imaginary * this.imaginary;
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    equals(other, tolerance = EPSILON) {
        return (
            Math.abs(this.real - other.real) <= tolerance &&
            Math.abs(this.imaginary - other.imaginary) <= tolerance
        );
    }

    toString(digits = 4) {
        const real = Math.abs(this.real) < 10 ** -digits ? 0 : this.real;
        const imaginary =
            Math.abs(this.imaginary) < 10 ** -digits ? 0 : this.imaginary;

        const roundedReal = Number(real.toFixed(digits));
        const roundedImaginary = Number(imaginary.toFixed(digits));

        if (roundedImaginary === 0) {
            return String(roundedReal);
        }

        if (roundedReal === 0) {
            return `${roundedImaginary}i`;
        }

        const sign = roundedImaginary >= 0 ? "+" : "-";
        return `${roundedReal} ${sign} ${Math.abs(roundedImaginary)}i`;
    }
}

const ZERO = new Complex(0, 0);
const ONE = new Complex(1, 0);

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function assertClose(actual, expected, message, tolerance = 1e-10) {
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(
            `${message}: expected ${expected}, received ${actual}`
        );
    }
}

function assertComplexClose(actual, expected, message, tolerance = 1e-10) {
    if (!actual.equals(expected, tolerance)) {
        throw new Error(
            `${message}: expected ${expected.toString()}, received ${actual.toString()}`
        );
    }
}

function probability(amplitude) {
    return amplitude.magnitudeSquared();
}

class Qubit {
    constructor(alpha = ONE, beta = ZERO) {
        this.alpha = alpha;
        this.beta = beta;
        this.validate();
    }

    normSquared() {
        return probability(this.alpha) + probability(this.beta);
    }

    validate() {
        if (Math.abs(this.normSquared() - 1) > EPSILON) {
            throw new Error(
                "A qubit must be normalized: |alpha|^2 + |beta|^2 = 1."
            );
        }
    }

    probabilities() {
        return {
            "0": probability(this.alpha),
            "1": probability(this.beta)
        };
    }

    clone() {
        return new Qubit(this.alpha, this.beta);
    }

    hadamard() {
        // H transforms [alpha, beta] into:
        // [(alpha + beta)/sqrt(2), (alpha - beta)/sqrt(2)].
        const newAlpha = this.alpha.add(this.beta).multiply(H_SCALE);
        const newBeta = this.alpha.subtract(this.beta).multiply(H_SCALE);
        return new Qubit(newAlpha, newBeta);
    }

    pauliX() {
        return new Qubit(this.beta, this.alpha);
    }

    pauliZ() {
        return new Qubit(
            this.alpha,
            this.beta.multiply(-1)
        );
    }

    measure(randomSource = Math.random) {
        const outcome = randomSource() < this.probabilities()["0"] ? 0 : 1;

        if (outcome === 0) {
            this.alpha = ONE;
            this.beta = ZERO;
        } else {
            this.alpha = ZERO;
            this.beta = ONE;
        }

        return outcome;
    }

    describe() {
        return (
            `|psi> = (${this.alpha.toString()})|0> + ` +
            `(${this.beta.toString()})|1>`
        );
    }
}

function demonstrateBasics() {
    section("1. Basis states and amplitudes");

    const zero = new Qubit(ONE, ZERO);
    const one = new Qubit(ZERO, ONE);

    console.log("|0>:", zero.describe(), zero.probabilities());
    console.log("|1>:", one.describe(), one.probabilities());

    console.log(
        "\nA state is represented by amplitudes. Probabilities are " +
        "obtained from squared magnitudes."
    );
}

function demonstrateHadamard() {
    section("2. H|0> and H|1>");

    const zero = new Qubit(ONE, ZERO);
    const one = new Qubit(ZERO, ONE);

    const plus = zero.hadamard();
    const minus = one.hadamard();

    console.log("H|0>:", plus.describe());
    console.log("Probabilities:", plus.probabilities());

    console.log("\nH|1>:", minus.describe());
    console.log("Probabilities:", minus.probabilities());
}

function demonstrateMatrix() {
    section("3. Explicit Hadamard matrix");

    const H = [
        [new Complex(H_SCALE, 0), new Complex(H_SCALE, 0)],
        [new Complex(H_SCALE, 0), new Complex(-H_SCALE, 0)]
    ];

    console.log("H =");
    for (const row of H) {
        console.log(
            `[ ${row[0].toString()}, ${row[1].toString()} ]`
        );
    }

    const input = [ONE, ZERO];
    const output = [
        H[0][0].multiply(input[0]).add(H[0][1].multiply(input[1])),
        H[1][0].multiply(input[0]).add(H[1][1].multiply(input[1]))
    ];

    console.log(
        "\nH|0> =",
        output.map(value => value.toString())
    );
}

function demonstrateNormalization() {
    section("4. Normalization");

    const plus = new Qubit(
        new Complex(H_SCALE, 0),
        new Complex(H_SCALE, 0)
    );

    console.log("State:", plus.describe());
    console.log("Norm squared:", plus.normSquared());
    console.log("Probabilities:", plus.probabilities());

    assertClose(plus.normSquared(), 1, "Normalization");
}

function demonstrateInverse() {
    section("5. H is self-inverse");

    const initial = new Qubit(ONE, ZERO);
    const final = initial.hadamard().hadamard();

    console.log("Initial:", initial.describe());
    console.log("After H:", initial.hadamard().describe());
    console.log("After H again:", final.describe());

    assertComplexClose(final.alpha, ONE, "H^2 should return alpha to 1");
    assertComplexClose(final.beta, ZERO, "H^2 should return beta to 0");
}

function demonstratePhaseAndInterference() {
    section("6. Phase and interference");

    const plus = new Qubit(
        new Complex(H_SCALE, 0),
        new Complex(H_SCALE, 0)
    );

    const minus = new Qubit(
        new Complex(H_SCALE, 0),
        new Complex(-H_SCALE, 0)
    );

    console.log("|+>:", plus.describe());
    console.log("|->:", minus.describe());

    console.log("\nBoth have:");
    console.log("|+> probabilities:", plus.probabilities());
    console.log("|-> probabilities:", minus.probabilities());

    console.log("\nAfter another H:");
    console.log("H|+>:", plus.hadamard().describe());
    console.log("H|->:", minus.hadamard().describe());

    console.log(
        "\nThe relative sign is invisible in one computational-basis " +
        "measurement but becomes important when amplitudes interfere."
    );
}

function demonstrateMeasurement(shots = 10000, seed = 42) {
    section("7. Measurement sampling");

    // A deterministic pseudo-random generator makes this demonstration
    // reproducible without an external package.
    let state = seed >>> 0;

    function seededRandom() {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 0x100000000;
    }

    const preparedState = new Qubit(ONE, ZERO).hadamard();
    const counts = { 0: 0, 1: 0 };

    for (let shot = 0; shot < shots; shot += 1) {
        const measured = preparedState.clone().measure(seededRandom);
        counts[measured] += 1;
    }

    console.log("Shots:", shots);
    console.log(
        `0: ${counts[0]} (${(counts[0] / shots * 100).toFixed(2)}%)`
    );
    console.log(
        `1: ${counts[1]} (${(counts[1] / shots * 100).toFixed(2)}%)`
    );
}

class QuantumRegister {
    constructor(numberOfQubits) {
        if (!Number.isInteger(numberOfQubits) || numberOfQubits < 1) {
            throw new Error("numberOfQubits must be a positive integer.");
        }

        if (numberOfQubits > 20) {
            throw new Error(
                "This educational state-vector simulator limits registers to 20 qubits."
            );
        }

        this.numberOfQubits = numberOfQubits;
        this.amplitudes = Array.from(
            { length: 2 ** numberOfQubits },
            () => new Complex(0, 0)
        );
        this.amplitudes[0] = ONE;
    }

    validateQubit(qubit) {
        if (!Number.isInteger(qubit)) {
            throw new TypeError("Qubit index must be an integer.");
        }

        if (qubit < 0 || qubit >= this.numberOfQubits) {
            throw new RangeError(
                `Qubit index must be between 0 and ${this.numberOfQubits - 1}.`
            );
        }
    }

    label(index) {
        return index.toString(2).padStart(this.numberOfQubits, "0");
    }

    validateNormalization() {
        const total = this.amplitudes.reduce(
            (sum, amplitude) => sum + amplitude.magnitudeSquared(),
            0
        );

        assertClose(total, 1, "Register normalization", 1e-9);
    }

    hadamard(qubit) {
        this.validateQubit(qubit);

        const mask = 1 << qubit;
        const next = this.amplitudes.slice();

        for (let index = 0; index < this.amplitudes.length; index += 1) {
            if ((index & mask) !== 0) {
                continue;
            }

            const pairedIndex = index | mask;
            const a = this.amplitudes[index];
            const b = this.amplitudes[pairedIndex];

            next[index] = a.add(b).multiply(H_SCALE);
            next[pairedIndex] = a.subtract(b).multiply(H_SCALE);
        }

        this.amplitudes = next;
        this.validateNormalization();
    }

    pauliX(qubit) {
        this.validateQubit(qubit);

        const mask = 1 << qubit;

        for (let index = 0; index < this.amplitudes.length; index += 1) {
            if ((index & mask) !== 0) {
                continue;
            }

            const pairedIndex = index | mask;
            [this.amplitudes[index], this.amplitudes[pairedIndex]] = [
                this.amplitudes[pairedIndex],
                this.amplitudes[index]
            ];
        }

        this.validateNormalization();
    }

    cnot(control, target) {
        this.validateQubit(control);
        this.validateQubit(target);

        if (control === target) {
            throw new Error("CNOT control and target must differ.");
        }

        const controlMask = 1 << control;
        const targetMask = 1 << target;

        for (let index = 0; index < this.amplitudes.length; index += 1) {
            const controlIsOne = (index & controlMask) !== 0;
            const targetIsZero = (index & targetMask) === 0;

            if (controlIsOne && targetIsZero) {
                const pairedIndex = index | targetMask;

                [this.amplitudes[index], this.amplitudes[pairedIndex]] = [
                    this.amplitudes[pairedIndex],
                    this.amplitudes[index]
                ];
            }
        }

        this.validateNormalization();
    }

    probabilities() {
        const result = {};

        this.amplitudes.forEach((amplitude, index) => {
            result[this.label(index)] = amplitude.magnitudeSquared();
        });

        return result;
    }

    nonzeroStates(threshold = 1e-10) {
        const result = [];

        this.amplitudes.forEach((amplitude, index) => {
            if (amplitude.magnitude() > threshold) {
                result.push({
                    state: this.label(index),
                    amplitude,
                    probability: amplitude.magnitudeSquared()
                });
            }
        });

        return result;
    }

    measure(randomSource = Math.random) {
        const randomValue = randomSource();
        let cumulative = 0;

        for (let index = 0; index < this.amplitudes.length; index += 1) {
            cumulative += this.amplitudes[index].magnitudeSquared();

            if (randomValue < cumulative) {
                const outcome = this.label(index);

                this.amplitudes = this.amplitudes.map(
                    () => new Complex(0, 0)
                );
                this.amplitudes[index] = ONE;

                return outcome;
            }
        }

        const finalIndex = this.amplitudes.length - 1;
        this.amplitudes = this.amplitudes.map(
            () => new Complex(0, 0)
        );
        this.amplitudes[finalIndex] = ONE;

        return this.label(finalIndex);
    }
}

function printRegister(register) {
    for (const item of register.nonzeroStates()) {
        console.log(
            `|${item.state}> amplitude=${item.amplitude.toString().padStart(12)} ` +
            `probability=${item.probability.toFixed(4)}`
        );
    }
}

function demonstrateTwoQubitSuperposition() {
    section("8. Two-qubit superposition");

    const register = new QuantumRegister(2);

    register.hadamard(0);
    register.hadamard(1);

    printRegister(register);

    console.log(
        "\nThe state is (|00> + |01> + |10> + |11>) / 2."
    );
}

function demonstrateBellState() {
    section("9. Bell-state preparation");

    const register = new QuantumRegister(2);

    // H creates superposition in the control qubit.
    register.hadamard(0);

    // CNOT correlates the target with the control.
    register.cnot(0, 1);

    printRegister(register);

    console.log(
        "\nThe ideal state is (|00> + |11>) / sqrt(2)."
    );
}

function demonstrateBellSampling(shots = 5000) {
    section("10. Bell-state sampling");

    const counts = {
        "00": 0,
        "01": 0,
        "10": 0,
        "11": 0
    };

    for (let shot = 0; shot < shots; shot += 1) {
        const register = new QuantumRegister(2);
        register.hadamard(0);
        register.cnot(0, 1);

        counts[register.measure()] += 1;
    }

    for (const state of Object.keys(counts)) {
        console.log(
            `${state}: ${counts[state]} (${(counts[state] / shots * 100).toFixed(2)}%)`
        );
    }

    console.log(
        "\nIdeal Bell-state sampling produces only 00 and 11."
    );
}

function demonstrateGateComposition() {
    section("11. Gate composition");

    const initial = new Qubit(ONE, ZERO);
    const afterX = initial.pauliX();
    const afterH = afterX.hadamard();
    const afterZ = afterH.pauliZ();
    const finalState = afterZ.hadamard();

    console.log("Initial:", initial.describe());
    console.log("X:", afterX.describe());
    console.log("H:", afterH.describe());
    console.log("Z:", afterZ.describe());
    console.log("H:", finalState.describe());
}

function demonstrateEdgeCases() {
    section("12. Edge cases and validation");

    try {
        new Qubit(
            new Complex(1, 0),
            new Complex(1, 0)
        );
    } catch (error) {
        console.log("Invalid qubit rejected:", error.message);
    }

    const register = new QuantumRegister(2);

    const invalidOperations = [
        () => register.hadamard(2),
        () => register.hadamard(-1),
        () => register.cnot(0, 0)
    ];

    for (const operation of invalidOperations) {
        try {
            operation();
            console.log("Unexpected success.");
        } catch (error) {
            console.log("Correctly rejected:", error.message);
        }
    }
}

function demonstrateGlobalAndRelativePhase() {
    section("13. Global versus relative phase");

    const stateA = new Qubit(
        new Complex(H_SCALE, 0),
        new Complex(H_SCALE, 0)
    );

    const stateB = new Qubit(
        new Complex(0, H_SCALE),
        new Complex(0, H_SCALE)
    );

    console.log("State A:", stateA.describe());
    console.log("State B:", stateB.describe());

    console.log("\nComputational probabilities:");
    console.log("A:", stateA.probabilities());
    console.log("B:", stateB.probabilities());

    console.log(
        "\nState B differs from A by a global phase of i, so their " +
        "measurement statistics are identical."
    );
}

function performanceNotes() {
    section("14. State-vector complexity");

    console.log(
        "One qubit -> 2 complex amplitudes."
    );
    console.log(
        "n qubits -> 2^n complex amplitudes."
    );
    console.log(
        "One-qubit gate on an n-qubit state vector -> O(2^n) updates."
    );
    console.log(
        "Memory requirement -> O(2^n)."
    );

    console.log(
        "\nThe mathematical circuit can remain compact while its classical " +
        "state-vector simulation grows exponentially."
    );
}

function runAssertions() {
    section("15. Executable correctness checks");

    const plus = new Qubit(ONE, ZERO).hadamard();

    assertClose(
        plus.probabilities()["0"],
        0.5,
        "H|0> probability of 0"
    );

    assertClose(
        plus.probabilities()["1"],
        0.5,
        "H|0> probability of 1"
    );

    const restored = plus.hadamard();

    assertComplexClose(
        restored.alpha,
        ONE,
        "H^2|0> alpha"
    );

    assertComplexClose(
        restored.beta,
        ZERO,
        "H^2|0> beta"
    );

    const bell = new QuantumRegister(2);
    bell.hadamard(0);
    bell.cnot(0, 1);

    const probabilities = bell.probabilities();

    assertClose(probabilities["00"], 0.5, "Bell probability 00");
    assertClose(probabilities["11"], 0.5, "Bell probability 11");
    assertClose(probabilities["01"], 0, "Bell probability 01");
    assertClose(probabilities["10"], 0, "Bell probability 10");

    console.log("All correctness checks passed.");
}

function main() {
    console.log("HADAMARD GATE — CREATING SUPERPOSITION");
    console.log("JavaScript state-vector study implementation");

    demonstrateBasics();
    demonstrateHadamard();
    demonstrateMatrix();
    demonstrateNormalization();
    demonstrateInverse();
    demonstratePhaseAndInterference();
    demonstrateMeasurement();
    demonstrateTwoQubitSuperposition();
    demonstrateBellState();
    demonstrateBellSampling();
    demonstrateGateComposition();
    demonstrateEdgeCases();
    demonstrateGlobalAndRelativePhase();
    performanceNotes();
    runAssertions();
}

main();
