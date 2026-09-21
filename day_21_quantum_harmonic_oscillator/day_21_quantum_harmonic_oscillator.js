/*
 * Quantum Harmonic Oscillator
 * ===========================
 *
 * A self-contained JavaScript study of the quantum harmonic oscillator.
 *
 * Default units:
 *     hbar = 1
 *     mass = 1
 *     omega = 1
 *
 * In these units:
 *
 *     H = 1/2 (p^2 + x^2)
 *     E_n = n + 1/2
 *
 * The file uses only standard JavaScript and is executable with Node.js.
 *
 * It demonstrates:
 * - classical and quantum oscillator models
 * - energy quantization
 * - Hermite polynomials
 * - wavefunctions and normalization
 * - numerical integration
 * - expectation values
 * - ladder operators
 * - finite-dimensional operator matrices
 * - commutators
 * - coherent states
 * - time evolution
 * - thermal occupation
 * - measurement simulation
 * - perturbation theory
 * - validation and edge cases
 */


"use strict";


// ---------------------------------------------------------------------------
// Constants and numerical utilities
// ---------------------------------------------------------------------------

const HBAR = 1.0;
const MASS = 1.0;
const OMEGA = 1.0;
const SQRT_PI = Math.sqrt(Math.PI);


function assertCondition(condition, message) {
    if (!condition) {
        throw new Error(`Verification failed: ${message}`);
    }
}


function nearlyEqual(a, b, tolerance = 1e-9) {
    return Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(a), Math.abs(b));
}


function factorial(n) {
    if (!Number.isInteger(n)) {
        throw new TypeError("factorial requires an integer");
    }

    if (n < 0) {
        throw new RangeError("factorial requires n >= 0");
    }

    let result = 1;

    for (let value = 2; value <= n; value += 1) {
        result *= value;
    }

    return result;
}


// ---------------------------------------------------------------------------
// Classical oscillator
// ---------------------------------------------------------------------------

class ClassicalOscillator {
    constructor(mass, omega, amplitude, phase = 0) {
        if (mass <= 0 || omega <= 0 || amplitude < 0) {
            throw new RangeError("mass and omega must be positive; amplitude cannot be negative");
        }

        this.mass = mass;
        this.omega = omega;
        this.amplitude = amplitude;
        this.phase = phase;
    }

    position(time) {
        return this.amplitude * Math.cos(this.omega * time + this.phase);
    }

    velocity(time) {
        return -this.amplitude *
            this.omega *
            Math.sin(this.omega * time + this.phase);
    }

    momentum(time) {
        return this.mass * this.velocity(time);
    }

    energy(time) {
        const x = this.position(time);
        const v = this.velocity(time);

        return (
            0.5 * this.mass * v * v +
            0.5 * this.mass * this.omega ** 2 * x * x
        );
    }

    totalEnergy() {
        return 0.5 *
            this.mass *
            this.omega ** 2 *
            this.amplitude ** 2;
    }
}


// ---------------------------------------------------------------------------
// Quantum energy spectrum
// ---------------------------------------------------------------------------

function energyLevel(n, hbar = HBAR, omega = OMEGA) {
    if (!Number.isInteger(n) || n < 0) {
        throw new RangeError("n must be a non-negative integer");
    }

    if (hbar <= 0 || omega <= 0) {
        throw new RangeError("hbar and omega must be positive");
    }

    return hbar * omega * (n + 0.5);
}


function oscillatorLength(hbar = HBAR, mass = MASS, omega = OMEGA) {
    if (hbar <= 0 || mass <= 0 || omega <= 0) {
        throw new RangeError("hbar, mass, and omega must be positive");
    }

    return Math.sqrt(hbar / (mass * omega));
}


// ---------------------------------------------------------------------------
// Hermite polynomials
// ---------------------------------------------------------------------------

function hermite(n, x) {
    if (!Number.isInteger(n) || n < 0) {
        throw new RangeError("n must be a non-negative integer");
    }

    if (n === 0) {
        return 1;
    }

    if (n === 1) {
        return 2 * x;
    }

    let previous = 1;
    let current = 2 * x;

    for (let order = 1; order < n; order += 1) {
        const next = 2 * x * current - 2 * order * previous;
        previous = current;
        current = next;
    }

    return current;
}


function wavefunction(n, x, hbar = HBAR, mass = MASS, omega = OMEGA) {
    const length = oscillatorLength(hbar, mass, omega);
    const xi = x / length;

    /*
     * psi_n(x) =
     *   1 / sqrt(2^n n! sqrt(pi) x_osc)
     *   H_n(xi) exp(-xi^2/2)
     */
    const normalization =
        1 / Math.sqrt(
            Math.pow(2, n) *
            factorial(n) *
            SQRT_PI *
            length
        );

    return normalization *
        hermite(n, xi) *
        Math.exp(-0.5 * xi * xi);
}


function probabilityDensity(n, x) {
    const psi = wavefunction(n, x);
    return psi * psi;
}


// ---------------------------------------------------------------------------
// Numerical integration
// ---------------------------------------------------------------------------

function trapezoidalIntegral(fn, lower, upper, intervals = 10000) {
    if (intervals <= 0 || !Number.isInteger(intervals)) {
        throw new RangeError("intervals must be a positive integer");
    }

    if (upper <= lower) {
        throw new RangeError("upper must be greater than lower");
    }

    const width = (upper - lower) / intervals;

    let total = 0.5 * (fn(lower) + fn(upper));

    for (let i = 1; i < intervals; i += 1) {
        total += fn(lower + i * width);
    }

    return total * width;
}


// ---------------------------------------------------------------------------
// Expectation values and uncertainty
// ---------------------------------------------------------------------------

function expectationX(n) {
    void n;
    return 0;
}


function expectationP(n) {
    void n;
    return 0;
}


function expectationX2(n, hbar = HBAR, mass = MASS, omega = OMEGA) {
    return hbar / (mass * omega) * (n + 0.5);
}


function expectationP2(n, hbar = HBAR, mass = MASS, omega = OMEGA) {
    return mass * hbar * omega * (n + 0.5);
}


function positionUncertainty(n) {
    return Math.sqrt(expectationX2(n));
}


function momentumUncertainty(n) {
    return Math.sqrt(expectationP2(n));
}


function uncertaintyProduct(n) {
    return positionUncertainty(n) * momentumUncertainty(n);
}


// ---------------------------------------------------------------------------
// Complex numbers
// ---------------------------------------------------------------------------

function complex(real = 0, imaginary = 0) {
    return { real, imaginary };
}


function complexAdd(a, b) {
    return complex(a.real + b.real, a.imaginary + b.imaginary);
}


function complexMultiply(a, b) {
    return complex(
        a.real * b.real - a.imaginary * b.imaginary,
        a.real * b.imaginary + a.imaginary * b.real
    );
}


function complexScale(a, scalar) {
    return complex(a.real * scalar, a.imaginary * scalar);
}


function complexConjugate(a) {
    return complex(a.real, -a.imaginary);
}


function complexMagnitudeSquared(a) {
    return a.real * a.real + a.imaginary * a.imaginary;
}


function complexMagnitude(a) {
    return Math.sqrt(complexMagnitudeSquared(a));
}


function complexExp(theta) {
    return complex(Math.cos(theta), Math.sin(theta));
}


function formatComplex(value, digits = 5) {
    const real = value.real.toFixed(digits);
    const imaginary = Math.abs(value.imaginary).toFixed(digits);
    const sign = value.imaginary >= 0 ? "+" : "-";

    return `${real} ${sign} ${imaginary}i`;
}


// ---------------------------------------------------------------------------
// State-vector operations
// ---------------------------------------------------------------------------

function basisState(n, dimension) {
    if (n < 0 || n >= dimension) {
        throw new RangeError("basis-state index is outside the finite basis");
    }

    const state = Array.from(
        { length: dimension },
        () => complex(0, 0)
    );

    state[n] = complex(1, 0);
    return state;
}


function stateNorm(state) {
    return Math.sqrt(
        state.reduce(
            (sum, amplitude) =>
                sum + complexMagnitudeSquared(amplitude),
            0
        )
    );
}


function normalizeState(state) {
    const norm = stateNorm(state);

    if (norm === 0) {
        throw new RangeError("cannot normalize a zero state");
    }

    return state.map(amplitude =>
        complexScale(amplitude, 1 / norm)
    );
}


function applyAnnihilation(state) {
    /*
     * a|n> = sqrt(n)|n-1>
     */
    const result = Array.from(
        { length: state.length },
        () => complex(0, 0)
    );

    for (let n = 1; n < state.length; n += 1) {
        result[n - 1] = complexAdd(
            result[n - 1],
            complexScale(state[n], Math.sqrt(n))
        );
    }

    return result;
}


function applyCreation(state) {
    /*
     * a†|n> = sqrt(n+1)|n+1>
     *
     * The finite array cannot represent a state above the cutoff.
     * That missing component is a truncation artifact.
     */
    const result = Array.from(
        { length: state.length },
        () => complex(0, 0)
    );

    for (let n = 0; n < state.length - 1; n += 1) {
        result[n + 1] = complexAdd(
            result[n + 1],
            complexScale(state[n], Math.sqrt(n + 1))
        );
    }

    return result;
}


// ---------------------------------------------------------------------------
// Matrix operations
// ---------------------------------------------------------------------------

function zeroMatrix(size) {
    return Array.from(
        { length: size },
        () => Array.from(
            { length: size },
            () => complex(0, 0)
        )
    );
}


function identityMatrix(size) {
    const matrix = zeroMatrix(size);

    for (let i = 0; i < size; i += 1) {
        matrix[i][i] = complex(1, 0);
    }

    return matrix;
}


function matrixMultiply(A, B) {
    const rows = A.length;
    const inner = B.length;
    const columns = B[0].length;

    if (A[0].length !== inner) {
        throw new RangeError("incompatible matrix dimensions");
    }

    const result = Array.from(
        { length: rows },
        () => Array.from(
            { length: columns },
            () => complex(0, 0)
        )
    );

    for (let row = 0; row < rows; row += 1) {
        for (let middle = 0; middle < inner; middle += 1) {
            for (let column = 0; column < columns; column += 1) {
                result[row][column] = complexAdd(
                    result[row][column],
                    complexMultiply(
                        A[row][middle],
                        B[middle][column]
                    )
                );
            }
        }
    }

    return result;
}


function matrixSubtract(A, B) {
    return A.map((row, i) =>
        row.map((value, j) =>
            complex(
                value.real - B[i][j].real,
                value.imaginary - B[i][j].imaginary
            )
        )
    );
}


function matrixScale(A, scalar) {
    return A.map(row =>
        row.map(value =>
            complexScale(value, scalar)
        )
    );
}


function commutator(A, B) {
    return matrixSubtract(
        matrixMultiply(A, B),
        matrixMultiply(B, A)
    );
}


function matrixVectorMultiply(A, vector) {
    return A.map(row =>
        row.reduce(
            (sum, value, index) =>
                complexAdd(
                    sum,
                    complexMultiply(value, vector[index])
                ),
            complex(0, 0)
        )
    );
}


function innerProduct(bra, ket) {
    return bra.reduce(
        (sum, value, index) =>
            complexAdd(
                sum,
                complexMultiply(
                    complexConjugate(value),
                    ket[index]
                )
            ),
        complex(0, 0)
    );
}


function expectationMatrix(state, operator) {
    return innerProduct(
        state,
        matrixVectorMultiply(operator, state)
    );
}


// ---------------------------------------------------------------------------
// Ladder-operator matrices
// ---------------------------------------------------------------------------

function annihilationMatrix(dimension) {
    const matrix = zeroMatrix(dimension);

    for (let n = 1; n < dimension; n += 1) {
        matrix[n - 1][n] = complex(Math.sqrt(n), 0);
    }

    return matrix;
}


function creationMatrix(dimension) {
    const matrix = zeroMatrix(dimension);

    for (let n = 0; n < dimension - 1; n += 1) {
        matrix[n + 1][n] = complex(Math.sqrt(n + 1), 0);
    }

    return matrix;
}


// ---------------------------------------------------------------------------
// Position and momentum operators
// ---------------------------------------------------------------------------

function positionMatrix(dimension) {
    const a = annihilationMatrix(dimension);
    const adag = creationMatrix(dimension);

    return matrixScale(
        a.map((row, i) =>
            row.map((value, j) =>
                complexAdd(value, adag[i][j])
            )
        ),
        Math.sqrt(HBAR / (2 * MASS * OMEGA))
    );
}


function momentumMatrix(dimension) {
    const a = annihilationMatrix(dimension);
    const adag = creationMatrix(dimension);

    const difference = a.map((row, i) =>
        row.map((value, j) =>
            complex(
                value.real - adag[i][j].real,
                value.imaginary - adag[i][j].imaginary
            )
        )
    );

    return matrixScale(
        difference,
        complex(0, -Math.sqrt(MASS * HBAR * OMEGA / 2))
    );
}


// ---------------------------------------------------------------------------
// Coherent states
// ---------------------------------------------------------------------------

function coherentState(alpha, dimension) {
    /*
     * |alpha> =
     * exp(-|alpha|²/2) sum_n alpha^n/sqrt(n!) |n>
     */
    const magnitudeSquared =
        complexMagnitudeSquared(alpha);

    const prefactor =
        Math.exp(-0.5 * magnitudeSquared);

    const coefficients = [];

    for (let n = 0; n < dimension; n += 1) {
        const alphaPower = complexPowInteger(alpha, n);

        coefficients.push(
            complexScale(
                alphaPower,
                prefactor / Math.sqrt(factorial(n))
            )
        );
    }

    /*
     * A finite basis truncates the infinite coherent state, so normalize
     * the represented vector before using it in numerical experiments.
     */
    return normalizeState(coefficients);
}


function complexPowInteger(value, exponent) {
    let result = complex(1, 0);

    for (let i = 0; i < exponent; i += 1) {
        result = complexMultiply(result, value);
    }

    return result;
}


function coherentNumberProbability(alpha, n) {
    const mean = complexMagnitudeSquared(alpha);

    return Math.exp(-mean) *
        Math.pow(mean, n) /
        factorial(n);
}


function coherentMeanNumber(alpha) {
    return complexMagnitudeSquared(alpha);
}


function coherentPositionMean(alpha) {
    return Math.sqrt(2) * alpha.real;
}


function coherentMomentumMean(alpha) {
    return Math.sqrt(2) * alpha.imaginary;
}


// ---------------------------------------------------------------------------
// Time evolution
// ---------------------------------------------------------------------------

function evolveState(state, time) {
    return state.map((amplitude, n) => {
        const phaseAngle = -energyLevel(n) * time / HBAR;
        return complexMultiply(
            amplitude,
            complexExp(phaseAngle)
        );
    });
}


function coherentStateAtTime(alpha, time, dimension) {
    const rotation = complexExp(-OMEGA * time);
    const rotatedAlpha = complexMultiply(alpha, rotation);

    return coherentState(rotatedAlpha, dimension);
}


// ---------------------------------------------------------------------------
// Thermal oscillator
// ---------------------------------------------------------------------------

function thermalOccupation(temperature) {
    if (temperature <= 0) {
        throw new RangeError("temperature must be positive");
    }

    const x = HBAR * OMEGA / temperature;

    if (x > 700) {
        return 0;
    }

    return 1 / Math.expm1(x);
}


function thermalMeanEnergy(temperature) {
    return HBAR * OMEGA *
        (0.5 + thermalOccupation(temperature));
}


function thermalPartitionFunction(temperature) {
    if (temperature <= 0) {
        throw new RangeError("temperature must be positive");
    }

    const x = HBAR * OMEGA / temperature;
    return Math.exp(-0.5 * x) /
        (1 - Math.exp(-x));
}


function thermalProbability(n, temperature) {
    if (n < 0) {
        throw new RangeError("n must be non-negative");
    }

    const q = Math.exp(-HBAR * OMEGA / temperature);
    return (1 - q) * Math.pow(q, n);
}


// ---------------------------------------------------------------------------
// Quartic perturbation
// ---------------------------------------------------------------------------

function quarticFirstOrderCorrection(n, lambdaStrength) {
    /*
     * For H' = lambda x^4:
     *
     * <n|x^4|n> =
     * 3 [hbar/(2m omega)]² (2n² + 2n + 1)
     */
    const scale = HBAR / (2 * MASS * OMEGA);

    return lambdaStrength *
        3 *
        scale ** 2 *
        (2 * n * n + 2 * n + 1);
}


// ---------------------------------------------------------------------------
// Measurement simulation
// ---------------------------------------------------------------------------

function seededRandom(seed) {
    /*
     * Small deterministic pseudo-random generator for reproducible
     * educational simulations. It is not cryptographically secure.
     */
    let state = seed >>> 0;

    return function random() {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 4294967296;
    };
}


function sampleNumberMeasurement(state, samples, seed = 42) {
    const probabilities = state.map(complexMagnitudeSquared);
    const total = probabilities.reduce(
        (sum, value) => sum + value,
        0
    );

    const normalized = probabilities.map(
        probability => probability / total
    );

    const cumulative = [];
    let running = 0;

    for (const probability of normalized) {
        running += probability;
        cumulative.push(running);
    }

    const random = seededRandom(seed);
    const outcomes = [];

    for (let sample = 0; sample < samples; sample += 1) {
        const target = random();

        for (let n = 0; n < cumulative.length; n += 1) {
            if (target < cumulative[n]) {
                outcomes.push(n);
                break;
            }
        }
    }

    return outcomes;
}


function empiricalDistribution(outcomes) {
    const counts = new Map();

    for (const outcome of outcomes) {
        counts.set(
            outcome,
            (counts.get(outcome) ?? 0) + 1
        );
    }

    const total = outcomes.length;
    const result = new Map();

    for (const [outcome, count] of counts.entries()) {
        result.set(outcome, count / total);
    }

    return result;
}


// ---------------------------------------------------------------------------
// Output helpers
// ---------------------------------------------------------------------------

function separator(title) {
    console.log(`\n${"=".repeat(76)}`);
    console.log(title);
    console.log("=".repeat(76));
}


function printState(state) {
    state.forEach((amplitude, n) => {
        const probability =
            complexMagnitudeSquared(amplitude);

        if (probability > 1e-10) {
            console.log(
                `|${n}>: ${formatComplex(amplitude)}, ` +
                `P=${probability.toFixed(6)}`
            );
        }
    });
}


// ---------------------------------------------------------------------------
// Demonstrations
// ---------------------------------------------------------------------------

function demonstrateClassicalModel() {
    separator("1. Classical harmonic oscillator");

    const oscillator =
        new ClassicalOscillator(1, 2, 3);

    console.log(
        `Classical total energy = ${oscillator.totalEnergy().toFixed(6)}`
    );

    for (const time of [0, 0.25, 0.5, 0.75]) {
        console.log(
            `t=${time.toFixed(2)} ` +
            `x=${oscillator.position(time).toFixed(5)} ` +
            `p=${oscillator.momentum(time).toFixed(5)} ` +
            `E=${oscillator.energy(time).toFixed(6)}`
        );
    }
}


function demonstrateSpectrum() {
    separator("2. Quantized spectrum");

    for (let n = 0; n < 8; n += 1) {
        console.log(
            `n=${n}, E_n=${energyLevel(n).toFixed(6)}`
        );
    }

    console.log(
        "Every adjacent energy level differs by hbar*omega = 1."
    );
}


function demonstrateWavefunctions() {
    separator("3. Hermite polynomials and wavefunctions");

    for (let n = 0; n < 5; n += 1) {
        const values = [-2, -1, 0, 1, 2].map(
            x => hermite(n, x)
        );

        console.log(`H_${n}(x) at [-2,-1,0,1,2]:`, values);
    }

    console.log("\nWavefunction samples:");

    for (let n = 0; n < 4; n += 1) {
        const values = [-2, -1, 0, 1, 2].map(
            x => wavefunction(n, x)
        );

        console.log(
            `psi_${n}:`,
            values.map(value => value.toFixed(5))
        );
    }
}


function demonstrateNormalization() {
    separator("4. Numerical normalization");

    for (let n = 0; n < 4; n += 1) {
        const integral = trapezoidalIntegral(
            x => probabilityDensity(n, x),
            -8,
            8,
            12000
        );

        console.log(
            `Integral |psi_${n}|² dx = ${integral.toFixed(10)}`
        );
    }
}


function demonstrateExpectationValues() {
    separator("5. Expectation values and uncertainty");

    for (let n = 0; n < 5; n += 1) {
        console.log(
            `n=${n} ` +
            `<x>=${expectationX(n)} ` +
            `<p>=${expectationP(n)} ` +
            `<x²>=${expectationX2(n).toFixed(4)} ` +
            `<p²>=${expectationP2(n).toFixed(4)} ` +
            `Delta x=${positionUncertainty(n).toFixed(4)} ` +
            `Delta p=${momentumUncertainty(n).toFixed(4)} ` +
            `product=${uncertaintyProduct(n).toFixed(4)}`
        );
    }
}


function demonstrateLadderOperators() {
    separator("6. Ladder operators");

    const state = basisState(3, 7);

    console.log("a|3>:");
    printState(applyAnnihilation(state));

    console.log("\na†|3>:");
    printState(applyCreation(state));

    console.log(
        "\nThe coefficient sqrt(n) controls lowering and sqrt(n+1) "
        + "controls raising."
    );
}


function demonstrateCommutator() {
    separator("7. Finite-basis commutator");

    const dimension = 8;
    const a = annihilationMatrix(dimension);
    const adag = creationMatrix(dimension);
    const commutatorMatrix = commutator(a, adag);

    console.log(
        "Diagonal entries of [a,a†] in an 8-state truncation:"
    );

    console.log(
        commutatorMatrix.map(
            (row, index) => row[index].real
        )
    );

    console.log(
        "The final boundary differs from one because a finite matrix "
        + "cannot represent the complete infinite oscillator Hilbert space."
    );
}


function demonstratePositionMomentum() {
    separator("8. Position and momentum operators");

    const xOperator = positionMatrix(5);
    const pOperator = momentumMatrix(5);

    console.log("Nonzero x matrix elements:");

    for (let row = 0; row < 5; row += 1) {
        for (let column = 0; column < 5; column += 1) {
            const value = xOperator[row][column];

            if (complexMagnitude(value) > 1e-10) {
                console.log(
                    `<${row}|x|${column}> = ${formatComplex(value)}`
                );
            }
        }
    }

    console.log("\nNonzero p matrix elements:");

    for (let row = 0; row < 5; row += 1) {
        for (let column = 0; column < 5; column += 1) {
            const value = pOperator[row][column];

            if (complexMagnitude(value) > 1e-10) {
                console.log(
                    `<${row}|p|${column}> = ${formatComplex(value)}`
                );
            }
        }
    }
}


function demonstrateOperatorExpectation() {
    separator("9. Operator expectation values");

    const dimension = 10;
    const xOperator = positionMatrix(dimension);
    const pOperator = momentumMatrix(dimension);

    for (let n = 0; n < 4; n += 1) {
        const state = basisState(n, dimension);
        const x2Operator = matrixMultiply(xOperator, xOperator);
        const p2Operator = matrixMultiply(pOperator, pOperator);

        const x2 = expectationMatrix(state, x2Operator);
        const p2 = expectationMatrix(state, p2Operator);

        console.log(
            `n=${n}: ` +
            `<x²>=${x2.real.toFixed(6)}, ` +
            `<p²>=${p2.real.toFixed(6)}`
        );
    }
}


function demonstrateCoherentState() {
    separator("10. Coherent state");

    const alpha = complex(1.5, 0.75);
    const state = coherentState(alpha, 20);

    console.log(
        `alpha = ${formatComplex(alpha)}`
    );

    console.log(
        `|alpha|² = ${coherentMeanNumber(alpha).toFixed(6)}`
    );

    console.log(
        `finite-state norm = ${stateNorm(state).toFixed(12)}`
    );

    console.log("\nNumber probabilities:");

    for (let n = 0; n < 10; n += 1) {
        console.log(
            `P(${n}) = ${coherentNumberProbability(alpha, n).toFixed(8)}`
        );
    }

    console.log(
        `\n<x> = ${coherentPositionMean(alpha).toFixed(6)}`
    );

    console.log(
        `<p> = ${coherentMomentumMean(alpha).toFixed(6)}`
    );

    console.log(
        "A coherent state has the same Delta x and Delta p as the ground state."
    );
}


function demonstrateTimeEvolution() {
    separator("11. Time evolution");

    const initial = normalizeState([
        complex(1, 0),
        complex(0.6, 0.3),
        complex(0.2, -0.1),
        complex(0.1, 0.05)
    ]);

    const evolved = evolveState(initial, Math.PI);

    console.log("Initial state:");
    printState(initial);

    console.log("\nEvolved state:");
    printState(evolved);

    console.log(
        `\nInitial norm = ${stateNorm(initial).toFixed(12)}`
    );

    console.log(
        `Final norm = ${stateNorm(evolved).toFixed(12)}`
    );
}


function demonstrateThermalPhysics() {
    separator("12. Thermal oscillator");

    console.log("T        Z          <n>        <E>");

    for (const temperature of [0.1, 0.25, 0.5, 1, 2, 5]) {
        console.log(
            `${temperature.toFixed(2)} ` +
            `${thermalPartitionFunction(temperature).toFixed(6)} ` +
            `${thermalOccupation(temperature).toFixed(6)} ` +
            `${thermalMeanEnergy(temperature).toFixed(6)}`
        );
    }
}


function demonstrateMeasurement() {
    separator("13. Measurement simulation");

    const alpha = complex(1, 0.5);
    const state = coherentState(alpha, 15);

    const outcomes =
        sampleNumberMeasurement(state, 20000, 12345);

    const observed =
        empiricalDistribution(outcomes);

    for (let n = 0; n < 8; n += 1) {
        const theoretical =
            coherentNumberProbability(alpha, n);

        const sampled =
            observed.get(n) ?? 0;

        console.log(
            `n=${n}: theoretical=${theoretical.toFixed(5)}, ` +
            `sampled=${sampled.toFixed(5)}`
        );
    }

    console.log(
        "\nThe simulation illustrates Born probabilities in the number basis."
    );
}


function demonstratePerturbation() {
    separator("14. Quartic perturbation");

    const lambdaStrength = 0.02;

    console.log(
        "For H = H0 + lambda*x^4, first-order perturbation theory gives:"
    );

    for (let n = 0; n < 6; n += 1) {
        const unperturbed = energyLevel(n);
        const correction =
            quarticFirstOrderCorrection(n, lambdaStrength);

        console.log(
            `n=${n}: E0=${unperturbed.toFixed(6)}, ` +
            `DeltaE=${correction.toFixed(6)}, ` +
            `E≈${(unperturbed + correction).toFixed(6)}`
        );
    }
}


function demonstrateEdgeCases() {
    separator("15. Edge cases");

    console.log(
        `Ground-state energy: ${energyLevel(0)}`
    );

    console.log(
        `Norm of a|0>: ${stateNorm(
            applyAnnihilation(basisState(0, 5))
        )}`
    );

    const invalidOperations = [
        [
            "negative quantum number",
            () => energyLevel(-1)
        ],
        [
            "zero mass",
            () => oscillatorLength(HBAR, 0, OMEGA)
        ],
        [
            "zero-dimensional basis",
            () => basisState(0, 0)
        ],
        [
            "zero-state normalization",
            () => normalizeState([
                complex(0, 0),
                complex(0, 0)
            ])
        ]
    ];

    for (const [name, operation] of invalidOperations) {
        try {
            operation();
        } catch (error) {
            console.log(`${name}: correctly rejected -> ${error.message}`);
        }
    }
}


// ---------------------------------------------------------------------------
// Automated verification
// ---------------------------------------------------------------------------

function verificationSuite() {
    separator("16. Automated verification");

    assertCondition(
        nearlyEqual(energyLevel(0), 0.5),
        "ground-state energy"
    );

    assertCondition(
        nearlyEqual(energyLevel(4), 4.5),
        "fifth energy level"
    );

    for (let n = 0; n < 5; n += 1) {
        assertCondition(
            nearlyEqual(
                energyLevel(n + 1) - energyLevel(n),
                1
            ),
            `constant energy gap at n=${n}`
        );
    }

    for (let n = 0; n < 4; n += 1) {
        const normalization = trapezoidalIntegral(
            x => probabilityDensity(n, x),
            -8,
            8,
            10000
        );

        assertCondition(
            Math.abs(normalization - 1) < 2e-5,
            `wavefunction normalization n=${n}`
        );
    }

    assertCondition(
        nearlyEqual(uncertaintyProduct(0), HBAR / 2),
        "ground-state uncertainty"
    );

    const coherent = coherentState(
        complex(1.2, 0.4),
        25
    );

    assertCondition(
        nearlyEqual(stateNorm(coherent), 1),
        "coherent state normalization"
    );

    const evolved = evolveState(coherent, 2.7);

    assertCondition(
        nearlyEqual(
            stateNorm(evolved),
            stateNorm(coherent)
        ),
        "unitary norm preservation"
    );

    console.log("All JavaScript verification checks passed.");
}


// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
    console.log("QUANTUM HARMONIC OSCILLATOR");
    console.log("Self-contained JavaScript computational study");
    console.log("Default units: hbar = mass = omega = 1");

    demonstrateClassicalModel();
    demonstrateSpectrum();
    demonstrateWavefunctions();
    demonstrateNormalization();
    demonstrateExpectationValues();
    demonstrateLadderOperators();
    demonstrateCommutator();
    demonstratePositionMomentum();
    demonstrateOperatorExpectation();
    demonstrateCoherentState();
    demonstrateTimeEvolution();
    demonstrateThermalPhysics();
    demonstrateMeasurement();
    demonstratePerturbation();
    demonstrateEdgeCases();
    verificationSuite();

    separator("End of study");

    console.log(
        "The oscillator provides a unified model for quantization, "
        + "operator algebra, wave mechanics, coherent states, and thermal physics."
    );
}


main();
