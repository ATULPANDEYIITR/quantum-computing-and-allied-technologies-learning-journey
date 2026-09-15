/*
 * Quantum Uncertainty and the Heisenberg Uncertainty Principle
 * ===============================================================
 *
 * A self-contained JavaScript study file covering:
 * - probability and standard deviation
 * - complex probability amplitudes
 * - Gaussian quantum wave packets
 * - position and momentum uncertainty
 * - numerical derivatives
 * - Fourier transforms
 * - the commutator [x,p] = i*hbar
 * - the Robertson uncertainty relation
 * - measurement uncertainty versus quantum uncertainty
 * - repeated measurements
 * - wave-packet spreading
 * - numerical stability and performance considerations
 *
 * The file uses only standard JavaScript and can run in Node.js or
 * in a modern browser console.
 */

"use strict";

// -----------------------------------------------------------------------------
// 1. Constants and basic statistics
// -----------------------------------------------------------------------------

const HBAR = 1.054571817e-34;
const ELECTRON_MASS = 9.1093837139e-31;

function mean(values) {
    if (values.length === 0) {
        throw new Error("mean() requires at least one value");
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function variance(values) {
    if (values.length === 0) {
        throw new Error("variance() requires at least one value");
    }

    const average = mean(values);

    return values.reduce(
        (sum, value) => sum + (value - average) ** 2,
        0
    ) / values.length;
}

function standardDeviation(values) {
    return Math.sqrt(variance(values));
}

console.log("=".repeat(78));
console.log("QUANTUM UNCERTAINTY PRINCIPLE");
console.log("=".repeat(78));

const classicalMeasurements = [1, 2, 3, 4, 5];

console.log("\n1. Statistical spread");
console.log("Mean:", mean(classicalMeasurements));
console.log("Standard deviation:", standardDeviation(classicalMeasurements));


// -----------------------------------------------------------------------------
// 2. Complex numbers
// -----------------------------------------------------------------------------

/*
 * JavaScript does not have a built-in complex-number primitive.
 * A small class makes the quantum-amplitude mathematics explicit.
 */
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

    magnitudeSquared() {
        return this.real ** 2 + this.imaginary ** 2;
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    scale(factor) {
        return new Complex(
            this.real * factor,
            this.imaginary * factor
        );
    }

    static fromPolar(radius, angle) {
        return new Complex(
            radius * Math.cos(angle),
            radius * Math.sin(angle)
        );
    }
}

const amplitude = Complex.fromPolar(1 / Math.sqrt(2), Math.PI / 4);

console.log("\n2. Born-rule probability");
console.log(
    "Amplitude:",
    amplitude
);
console.log(
    "Probability from |amplitude|^2:",
    amplitude.magnitudeSquared()
);


// -----------------------------------------------------------------------------
// 3. Gaussian wavefunction
// -----------------------------------------------------------------------------

function gaussianWavefunction(
    x,
    center,
    sigmaX,
    momentum,
    hbar = 1
) {
    if (sigmaX <= 0) {
        throw new Error("sigmaX must be positive");
    }

    const normalization =
        (1 / (2 * Math.PI * sigmaX ** 2)) ** 0.25;

    const envelope =
        normalization *
        Math.exp(-((x - center) ** 2) / (4 * sigmaX ** 2));

    const phase = Complex.fromPolar(
        1,
        (momentum * x) / hbar
    );

    return phase.scale(envelope);
}

const sampleWavefunction = gaussianWavefunction(
    0,
    0,
    1,
    2,
    1
);

console.log("\n3. Gaussian wavefunction at x=0");
console.log(sampleWavefunction);
console.log(
    "Probability density:",
    sampleWavefunction.magnitudeSquared()
);


// -----------------------------------------------------------------------------
// 4. Grid creation and numerical normalization
// -----------------------------------------------------------------------------

function createGrid(start, end, numberOfPoints) {
    if (numberOfPoints < 2) {
        throw new Error("At least two grid points are required");
    }

    const grid = [];
    const spacing = (end - start) / (numberOfPoints - 1);

    for (let i = 0; i < numberOfPoints; i++) {
        grid.push(start + i * spacing);
    }

    return grid;
}

function trapezoidalIntegral(xValues, yValues) {
    if (xValues.length !== yValues.length) {
        throw new Error("Arrays must have equal lengths");
    }

    let total = 0;

    for (let i = 0; i < xValues.length - 1; i++) {
        const dx = xValues[i + 1] - xValues[i];

        total +=
            0.5 *
            (yValues[i] + yValues[i + 1]) *
            dx;
    }

    return total;
}

function normalizeWavefunction(xValues, wavefunction) {
    const probabilityDensity = wavefunction.map(
        amplitudeValue => amplitudeValue.magnitudeSquared()
    );

    const norm = trapezoidalIntegral(
        xValues,
        probabilityDensity
    );

    if (norm <= 0) {
        throw new Error("Wavefunction has zero norm");
    }

    const factor = 1 / Math.sqrt(norm);

    return wavefunction.map(
        amplitudeValue => amplitudeValue.scale(factor)
    );
}


// -----------------------------------------------------------------------------
// 5. Position expectation value and uncertainty
// -----------------------------------------------------------------------------

function expectationPosition(xValues, wavefunction) {
    const probabilityDensity = wavefunction.map(
        amplitudeValue => amplitudeValue.magnitudeSquared()
    );

    return trapezoidalIntegral(
        xValues,
        probabilityDensity.map(
            (probability, index) =>
                probability * xValues[index]
        )
    );
}

function positionVariance(xValues, wavefunction) {
    const meanX = expectationPosition(
        xValues,
        wavefunction
    );

    const probabilityDensity = wavefunction.map(
        amplitudeValue => amplitudeValue.magnitudeSquared()
    );

    const meanXSquared = trapezoidalIntegral(
        xValues,
        probabilityDensity.map(
            (probability, index) =>
                probability * xValues[index] ** 2
        )
    );

    return Math.max(
        0,
        meanXSquared - meanX ** 2
    );
}

function positionUncertainty(xValues, wavefunction) {
    return Math.sqrt(
        positionVariance(xValues, wavefunction)
    );
}

const grid = createGrid(-10, 10, 1001);

let wavefunction = grid.map(
    x => gaussianWavefunction(
        x,
        1.0,
        1.25,
        2.0,
        1.0
    )
);

wavefunction = normalizeWavefunction(
    grid,
    wavefunction
);

console.log("\n4. Numerical position uncertainty");
console.log(
    "Mean x:",
    expectationPosition(grid, wavefunction)
);
console.log(
    "Delta x:",
    positionUncertainty(grid, wavefunction)
);


// -----------------------------------------------------------------------------
// 6. Finite-difference derivatives
// -----------------------------------------------------------------------------

function centralDerivative(values, spacing) {
    if (values.length < 3) {
        throw new Error("At least three values are required");
    }

    const derivative = new Array(values.length);

    derivative[0] =
        values[1].subtract(values[0]).scale(1 / spacing);

    derivative[values.length - 1] =
        values[values.length - 1]
            .subtract(values[values.length - 2])
            .scale(1 / spacing);

    for (let i = 1; i < values.length - 1; i++) {
        derivative[i] =
            values[i + 1]
                .subtract(values[i - 1])
                .scale(1 / (2 * spacing));
    }

    return derivative;
}

function secondDerivative(values, spacing) {
    const first = centralDerivative(values, spacing);
    return centralDerivative(first, spacing);
}


// -----------------------------------------------------------------------------
// 7. Momentum operator
// -----------------------------------------------------------------------------

function momentumWavefunction(
    xValues,
    wavefunction,
    hbar = 1
) {
    const dx = xValues[1] - xValues[0];

    const derivative = centralDerivative(
        wavefunction,
        dx
    );

    return derivative.map(
        derivativeValue =>
            new Complex(
                derivativeValue.imaginary * hbar,
                -derivativeValue.real * hbar
            )
    );
}

function innerProduct(xValues, left, right) {
    const integrand = left.map(
        (leftValue, index) =>
            leftValue
                .conjugate()
                .multiply(right[index])
                .real
    );

    return trapezoidalIntegral(
        xValues,
        integrand
    );
}

function momentumStatistics(
    xValues,
    wavefunction,
    hbar = 1
) {
    const momentumState = momentumWavefunction(
        xValues,
        wavefunction,
        hbar
    );

    const second = secondDerivative(
        wavefunction,
        xValues[1] - xValues[0]
    );

    const secondMomentumState = second.map(
        value =>
            value.scale(-hbar ** 2)
    );

    const meanP = innerProduct(
        xValues,
        wavefunction,
        momentumState
    );

    const meanPSquared = innerProduct(
        xValues,
        wavefunction,
        secondMomentumState
    );

    const varianceP = Math.max(
        0,
        meanPSquared - meanP ** 2
    );

    return {
        meanP,
        uncertaintyP: Math.sqrt(varianceP)
    };
}

const momentumResults = momentumStatistics(
    grid,
    wavefunction,
    1
);

console.log("\n5. Numerical momentum uncertainty");
console.log("Mean p:", momentumResults.meanP);
console.log("Delta p:", momentumResults.uncertaintyP);
console.log(
    "Delta x Delta p:",
    positionUncertainty(grid, wavefunction) *
    momentumResults.uncertaintyP
);
console.log("Minimum bound:", 0.5);


// -----------------------------------------------------------------------------
// 8. Direct discrete Fourier transform
// -----------------------------------------------------------------------------

function discreteFourierTransform(values) {
    const n = values.length;
    const result = new Array(n);

    for (let k = 0; k < n; k++) {
        let sum = new Complex();

        for (let j = 0; j < n; j++) {
            const angle =
                -2 * Math.PI * k * j / n;

            const factor =
                Complex.fromPolar(1, angle);

            sum = sum.add(
                values[j].multiply(factor)
            );
        }

        result[k] = sum;
    }

    return result;
}

/*
 * The direct DFT is O(N^2).
 * Production scientific software generally uses an FFT with O(N log N)
 * complexity, but the direct form makes the Fourier relationship visible.
 */

function inverseDiscreteFourierTransform(values) {
    const n = values.length;
    const result = new Array(n);

    for (let j = 0; j < n; j++) {
        let sum = new Complex();

        for (let k = 0; k < n; k++) {
            const angle =
                2 * Math.PI * k * j / n;

            sum = sum.add(
                values[k].multiply(
                    Complex.fromPolar(1, angle)
                )
            );
        }

        result[j] = sum.scale(1 / n);
    }

    return result;
}

const shortSignal = createGrid(
    0,
    15,
    16
).map(
    x => new Complex(
        Math.exp(-((x - 7) ** 2) / 4),
        0
    )
);

const spectrum = discreteFourierTransform(
    shortSignal
);

const reconstructed = inverseDiscreteFourierTransform(
    spectrum
);

let reconstructionError = 0;

for (let i = 0; i < shortSignal.length; i++) {
    reconstructionError = Math.max(
        reconstructionError,
        shortSignal[i]
            .subtract(reconstructed[i])
            .magnitude()
    );
}

console.log("\n6. Fourier transform");
console.log(
    "Maximum reconstruction error:",
    reconstructionError
);


// -----------------------------------------------------------------------------
// 9. Commutator demonstration
// -----------------------------------------------------------------------------

function positionOperator(
    xValues,
    wavefunction
) {
    return wavefunction.map(
        (value, index) =>
            value.scale(xValues[index])
    );
}

function applyMomentumOperator(
    xValues,
    wavefunction,
    hbar = 1
) {
    return momentumWavefunction(
        xValues,
        wavefunction,
        hbar
    );
}

function applyXP(
    xValues,
    wavefunction,
    hbar = 1
) {
    return applyMomentumOperator(
        xValues,
        positionOperator(
            xValues,
            wavefunction
        ),
        hbar
    );
}

function applyPX(
    xValues,
    wavefunction,
    hbar = 1
) {
    return positionOperator(
        xValues,
        applyMomentumOperator(
            xValues,
            wavefunction,
            hbar
        )
    );
}

function commutator(
    xValues,
    wavefunction,
    hbar = 1
) {
    const xp = applyXP(
        xValues,
        wavefunction,
        hbar
    );

    const px = applyPX(
        xValues,
        wavefunction,
        hbar
    );

    return xp.map(
        (value, index) =>
            value.subtract(px[index])
    );
}

const commutatorState = commutator(
    grid,
    wavefunction,
    1
);

const expectedCommutatorState = wavefunction.map(
    value => new Complex(
        -value.imaginary,
        value.real
    )
);

let commutatorError = 0;

/*
 * Boundary points are excluded because one-sided finite differences
 * behave differently from the interior central-difference approximation.
 */
for (let i = 5; i < grid.length - 5; i++) {
    commutatorError = Math.max(
        commutatorError,
        commutatorState[i]
            .subtract(expectedCommutatorState[i])
            .magnitude()
    );
}

console.log("\n7. Commutator [x,p]");
console.log(
    "Interior numerical error:",
    commutatorError
);
console.log(
    "Expected mathematical result: [x,p]psi = i*hbar*psi"
);


// -----------------------------------------------------------------------------
// 10. Robertson uncertainty relation
// -----------------------------------------------------------------------------

function robertsonLowerBound(
    commutatorExpectationMagnitude
) {
    return commutatorExpectationMagnitude / 2;
}

console.log("\n8. Robertson relation");
console.log(
    "For arbitrary observables A and B:"
);
console.log(
    "Delta A Delta B >= |<[A,B]>| / 2"
);
console.log(
    "For position and momentum:",
    robertsonLowerBound(1)
);


// -----------------------------------------------------------------------------
// 11. Repeated measurements
// -----------------------------------------------------------------------------

function weightedRandomSample(
    outcomes,
    probabilities,
    count,
    randomFunction = Math.random
) {
    if (
        outcomes.length !== probabilities.length ||
        outcomes.length === 0
    ) {
        throw new Error(
            "Outcomes and probabilities must have matching nonzero lengths"
        );
    }

    const total = probabilities.reduce(
        (sum, value) => sum + value,
        0
    );

    if (total <= 0) {
        throw new Error("Probability total must be positive");
    }

    const normalized = probabilities.map(
        value => value / total
    );

    const cumulative = [];
    let runningTotal = 0;

    for (const probability of normalized) {
        runningTotal += probability;
        cumulative.push(runningTotal);
    }

    const samples = [];

    for (let i = 0; i < count; i++) {
        const randomValue = randomFunction();

        for (let j = 0; j < cumulative.length; j++) {
            if (randomValue <= cumulative[j]) {
                samples.push(outcomes[j]);
                break;
            }
        }
    }

    return samples;
}

const spinSamples = weightedRandomSample(
    [-1, 1],
    [0.25, 0.75],
    10000
);

console.log("\n9. Repeated quantum-style measurement");
console.log("Empirical mean:", mean(spinSamples));
console.log(
    "Empirical standard deviation:",
    standardDeviation(spinSamples)
);


// -----------------------------------------------------------------------------
// 12. Free-particle Gaussian wave-packet spreading
// -----------------------------------------------------------------------------

function freeParticleWidth(
    initialSigmaX,
    time,
    mass,
    hbar = HBAR
) {
    if (initialSigmaX <= 0) {
        throw new Error("Initial width must be positive");
    }

    if (mass <= 0) {
        throw new Error("Mass must be positive");
    }

    const factor =
        hbar * time /
        (2 * mass * initialSigmaX ** 2);

    return initialSigmaX *
        Math.sqrt(1 + factor ** 2);
}

console.log("\n10. Free-particle wave-packet spreading");

for (const time of [0, 1e-16, 1e-15, 1e-14]) {
    console.log(
        `t=${time.toExponential(1)} s`,
        "Delta x=",
        freeParticleWidth(
            1e-10,
            time,
            ELECTRON_MASS
        ).toExponential(6),
        "m"
    );
}


// -----------------------------------------------------------------------------
// 13. Squeezing
// -----------------------------------------------------------------------------

class SqueezedState {
    constructor(baseUncertainty, squeezingParameter) {
        this.baseUncertainty = baseUncertainty;
        this.squeezingParameter = squeezingParameter;
    }

    get deltaX() {
        return this.baseUncertainty *
            Math.exp(-this.squeezingParameter);
    }

    get deltaP() {
        return this.baseUncertainty *
            Math.exp(this.squeezingParameter);
    }

    get product() {
        return this.deltaX * this.deltaP;
    }
}

console.log("\n11. Squeezed-state intuition");

for (const r of [-1, 0, 1]) {
    const state = new SqueezedState(
        1 / Math.sqrt(2),
        r
    );

    console.log(
        `r=${r}`,
        `DeltaX=${state.deltaX.toFixed(5)}`,
        `DeltaP=${state.deltaP.toFixed(5)}`,
        `product=${state.product.toFixed(5)}`
    );
}


// -----------------------------------------------------------------------------
// 14. Validation and edge cases
// -----------------------------------------------------------------------------

console.log("\n12. Validation and edge cases");

function safeQuantumWidth(width) {
    if (!Number.isFinite(width)) {
        throw new Error("Width must be finite");
    }

    if (width <= 0) {
        throw new Error("Width must be positive");
    }

    return width;
}

for (const invalidWidth of [0, -1, NaN, Infinity]) {
    try {
        safeQuantumWidth(invalidWidth);
    } catch (error) {
        console.log(
            `Rejected invalid width ${invalidWidth}: ${error.message}`
        );
    }
}


// -----------------------------------------------------------------------------
// 15. Performance comparison: DFT operation count
// -----------------------------------------------------------------------------

function estimateDftOperations(n) {
    return n * n;
}

function estimateFftOperations(n) {
    return n * Math.log2(n);
}

console.log("\n13. Computational complexity");

for (const n of [64, 256, 1024]) {
    console.log(
        `N=${n}`,
        `direct DFT ~ ${estimateDftOperations(n).toLocaleString()} operations`,
        `FFT scale ~ ${estimateFftOperations(n).toFixed(0)}`
    );
}


// -----------------------------------------------------------------------------
// 16. Compact uncertainty experiment
// -----------------------------------------------------------------------------

function gaussianMinimumUncertainty(
    sigmaX,
    hbar = 1
) {
    if (sigmaX <= 0) {
        throw new Error("sigmaX must be positive");
    }

    const sigmaP = hbar / (2 * sigmaX);

    return {
        sigmaX,
        sigmaP,
        product: sigmaX * sigmaP,
        lowerBound: hbar / 2,
        satisfiesBound:
            sigmaX * sigmaP >= hbar / 2,
        minimumGaussian:
            Math.abs(
                sigmaX * sigmaP - hbar / 2
            ) < 1e-12
    };
}

console.log("\n14. Minimum-uncertainty Gaussian states");

for (const sigmaX of [0.25, 0.5, 1, 2, 4]) {
    console.log(
        gaussianMinimumUncertainty(sigmaX)
    );
}


// -----------------------------------------------------------------------------
// 17. Conceptual distinctions
// -----------------------------------------------------------------------------

console.log("\n15. Important distinctions");

const distinctions = {
    quantumVariance:
        "Intrinsic statistical spread of outcomes in a quantum state.",

    measurementError:
        "Experimental imperfection caused by detector, calibration, noise, or procedure.",

    statePreparation:
        "The physical procedure used to prepare a particular quantum state.",

    wavePacketSpreading:
        "Time evolution of a wave packet; not itself the definition of the uncertainty relation.",

    FourierDuality:
        "Narrow position-space distributions require broad momentum-space spectra.",

    nonCommutativity:
        "Nonzero commutators prevent arbitrary simultaneous sharpness of corresponding observables."
};

for (const [name, explanation] of Object.entries(distinctions)) {
    console.log(`${name}: ${explanation}`);
}


// -----------------------------------------------------------------------------
// 18. Final reference
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("KEY EQUATIONS");
console.log("=".repeat(78));

const equations = [
    ["Born rule", "P(x) = |psi(x)|^2"],
    ["Expectation", "<A> = integral psi* A psi dx"],
    ["Variance", "(Delta A)^2 = <A^2> - <A>^2"],
    ["Momentum operator", "p_hat = -i hbar d/dx"],
    ["Commutator", "[x_hat, p_hat] = i hbar"],
    ["Heisenberg", "Delta x Delta p >= hbar / 2"],
    ["Robertson", "Delta A Delta B >= |<[A,B]>| / 2"],
    ["de Broglie", "p = hbar k"],
    [
        "Free-particle spreading",
        "sigma(t)=sigma(0)sqrt(1+[hbar*t/(2*m*sigma(0)^2)]^2)"
    ]
];

for (const [name, equation] of equations) {
    console.log(`${name}: ${equation}`);
}

console.log("\nJavaScript quantum uncertainty study completed.");
