/*
 * Time Evolution and Schrödinger Equation Concepts
 * =================================================
 *
 * A self-contained JavaScript study of quantum time evolution.
 *
 * The file emphasizes JavaScript-specific numerical patterns:
 *   - complex-number representation using objects
 *   - arrays for discretized wavefunctions
 *   - functional array operations
 *   - asynchronous time-evolution loops
 *   - browser-compatible execution
 *   - validation and numerical diagnostics
 *
 * Physical model:
 *
 *   i hbar dψ/dt = Hψ
 *
 * with
 *
 *   H = -(hbar² / 2m) d²/dx² + V(x,t).
 *
 * The numerical examples use hbar = m = 1.
 *
 * Run in Node.js:
 *
 *   node schrodinger_time_evolution.js
 *
 * The same core functions can also be adapted to browser applications.
 */

"use strict";

// ---------------------------------------------------------------------------
// Constants and complex arithmetic
// ---------------------------------------------------------------------------

const HBAR = 1.0;
const MASS = 1.0;
const EPSILON = 1e-12;

function complex(real = 0, imaginary = 0) {
    return { re: real, im: imaginary };
}

function complexAdd(a, b) {
    return complex(a.re + b.re, a.im + b.im);
}

function complexSubtract(a, b) {
    return complex(a.re - b.re, a.im - b.im);
}

function complexMultiply(a, b) {
    return complex(
        a.re * b.re - a.im * b.im,
        a.re * b.im + a.im * b.re
    );
}

function complexScale(a, scalar) {
    return complex(a.re * scalar, a.im * scalar);
}

function complexConjugate(a) {
    return complex(a.re, -a.im);
}

function complexMagnitudeSquared(a) {
    return a.re * a.re + a.im * a.im;
}

function complexMagnitude(a) {
    return Math.sqrt(complexMagnitudeSquared(a));
}

function complexExp(z) {
    const amplitude = Math.exp(z.re);
    return complex(
        amplitude * Math.cos(z.im),
        amplitude * Math.sin(z.im)
    );
}

function complexFromPolar(radius, angle) {
    return complex(
        radius * Math.cos(angle),
        radius * Math.sin(angle)
    );
}

// ---------------------------------------------------------------------------
// Grid and numerical integration
// ---------------------------------------------------------------------------

function createGrid(start, end, count) {
    if (count < 2) {
        throw new Error("A grid needs at least two points.");
    }

    const step = (end - start) / (count - 1);
    return Array.from(
        { length: count },
        (_, index) => start + index * step
    );
}

function trapezoidalIntegral(values, dx) {
    if (values.length < 2) {
        return 0;
    }

    let total = 0.5 * values[0] + 0.5 * values[values.length - 1];

    for (let index = 1; index < values.length - 1; index += 1) {
        total += values[index];
    }

    return total * dx;
}

// ---------------------------------------------------------------------------
// Wavefunctions
// ---------------------------------------------------------------------------

function normalizeWavefunction(wavefunction, dx) {
    const normSquared = trapezoidalIntegral(
        wavefunction.map(complexMagnitudeSquared),
        dx
    );

    if (normSquared <= EPSILON) {
        throw new Error("Cannot normalize a zero wavefunction.");
    }

    const factor = 1 / Math.sqrt(normSquared);

    return wavefunction.map(
        value => complexScale(value, factor)
    );
}

function gaussianWavePacket(x, center, width, momentum) {
    const wavefunction = x.map(position => {
        const envelope = Math.exp(
            -((position - center) ** 2) / (4 * width ** 2)
        );

        const phase = complexFromPolar(
            1,
            momentum * position / HBAR
        );

        return complexScale(phase, envelope);
    });

    return normalizeWavefunction(
        wavefunction,
        x[1] - x[0]
    );
}

function probabilityDensity(wavefunction) {
    return wavefunction.map(complexMagnitudeSquared);
}

function totalProbability(wavefunction, dx) {
    return trapezoidalIntegral(
        probabilityDensity(wavefunction),
        dx
    );
}

// ---------------------------------------------------------------------------
// Differential operators
// ---------------------------------------------------------------------------

function firstDerivative(values, dx) {
    if (values.length < 3) {
        throw new Error("At least three points are required.");
    }

    const derivative = Array(values.length).fill(null).map(
        () => complex()
    );

    derivative[0] = complexScale(
        complexSubtract(values[1], values[0]),
        1 / dx
    );

    derivative[values.length - 1] = complexScale(
        complexSubtract(
            values[values.length - 1],
            values[values.length - 2]
        ),
        1 / dx
    );

    for (let index = 1; index < values.length - 1; index += 1) {
        derivative[index] = complexScale(
            complexSubtract(
                values[index + 1],
                values[index - 1]
            ),
            1 / (2 * dx)
        );
    }

    return derivative;
}

function secondDerivative(values, dx) {
    if (values.length < 3) {
        throw new Error("At least three points are required.");
    }

    const derivative = Array(values.length).fill(null).map(
        () => complex()
    );

    for (let index = 1; index < values.length - 1; index += 1) {
        const secondDifference = complexAdd(
            complexSubtract(
                values[index + 1],
                complexScale(values[index], 2)
            ),
            values[index - 1]
        );

        derivative[index] = complexScale(
            secondDifference,
            1 / (dx * dx)
        );
    }

    // One-sided approximations are used at the boundaries.
    derivative[0] = complexScale(
        complexAdd(
            complexSubtract(values[2], complexScale(values[1], 2)),
            values[0]
        ),
        1 / (dx * dx)
    );

    const last = values.length - 1;
    derivative[last] = complexScale(
        complexAdd(
            complexSubtract(
                values[last],
                complexScale(values[last - 1], 2)
            ),
            values[last - 2]
        ),
        1 / (dx * dx)
    );

    return derivative;
}

// ---------------------------------------------------------------------------
// Potentials
// ---------------------------------------------------------------------------

function freeParticlePotential(_) {
    return 0;
}

function harmonicPotential(x, angularFrequency = 1) {
    return 0.5 * MASS * angularFrequency ** 2 * x ** 2;
}

function squareBarrierPotential(
    x,
    start,
    end,
    height
) {
    return x >= start && x <= end ? height : 0;
}

// ---------------------------------------------------------------------------
// Hamiltonian and observables
// ---------------------------------------------------------------------------

function applyHamiltonian(
    x,
    wavefunction,
    potential
) {
    const dx = x[1] - x[0];
    const curvature = secondDerivative(
        wavefunction,
        dx
    );

    return wavefunction.map((psi, index) => {
        const kinetic = complexScale(
            curvature[index],
            -(HBAR ** 2) / (2 * MASS)
        );

        const potentialPart = complexScale(
            psi,
            potential(x[index])
        );

        return complexAdd(kinetic, potentialPart);
    });
}

function expectationEnergy(
    x,
    wavefunction,
    potential
) {
    const dx = x[1] - x[0];
    const hPsi = applyHamiltonian(
        x,
        wavefunction,
        potential
    );

    const integrand = wavefunction.map(
        (psi, index) =>
            complexMultiply(
                complexConjugate(psi),
                hPsi[index]
            )
    );

    const realValues = integrand.map(value => value.re);

    return trapezoidalIntegral(realValues, dx);
}

function expectationPosition(
    x,
    wavefunction
) {
    const dx = x[1] - x[0];
    const density = probabilityDensity(wavefunction);

    return trapezoidalIntegral(
        x.map((position, index) =>
            position * density[index]
        ),
        dx
    );
}

function expectationMomentum(
    x,
    wavefunction
) {
    const dx = x[1] - x[0];
    const derivative = firstDerivative(
        wavefunction,
        dx
    );

    const integrand = wavefunction.map(
        (psi, index) => {
            const momentumPsi = complexScale(
                derivative[index],
                -HBAR
            );

            // Multiplication by -i:
            const multiplied = complex(
                momentumPsi.im,
                -momentumPsi.re
            );

            return complexMultiply(
                complexConjugate(psi),
                multiplied
            );
        }
    );

    return trapezoidalIntegral(
        integrand.map(value => value.re),
        dx
    );
}

// ---------------------------------------------------------------------------
// Schrödinger equation and RK4
// ---------------------------------------------------------------------------

function schrodingerRHS(
    x,
    wavefunction,
    potential
) {
    const hPsi = applyHamiltonian(
        x,
        wavefunction,
        potential
    );

    // dψ/dt = -(i/hbar)Hψ.
    return hPsi.map(value => complex(
        value.im / HBAR,
        -value.re / HBAR
    ));
}

function addScaledVector(
    state,
    derivative,
    scale
) {
    return state.map(
        (value, index) =>
            complexAdd(
                value,
                complexScale(
                    derivative[index],
                    scale
                )
            )
    );
}

function rk4Step(
    x,
    wavefunction,
    dt,
    potential
) {
    const k1 = schrodingerRHS(
        x,
        wavefunction,
        potential
    );

    const state2 = addScaledVector(
        wavefunction,
        k1,
        dt / 2
    );

    const k2 = schrodingerRHS(
        x,
        state2,
        potential
    );

    const state3 = addScaledVector(
        wavefunction,
        k2,
        dt / 2
    );

    const k3 = schrodingerRHS(
        x,
        state3,
        potential
    );

    const state4 = addScaledVector(
        wavefunction,
        k3,
        dt
    );

    const k4 = schrodingerRHS(
        x,
        state4,
        potential
    );

    return wavefunction.map((psi, index) => {
        const weighted = complexAdd(
            complexAdd(
                k1[index],
                complexScale(k2[index], 2)
            ),
            complexAdd(
                complexScale(k3[index], 2),
                k4[index]
            )
        );

        return complexAdd(
            psi,
            complexScale(weighted, dt / 6)
        );
    });
}

function evolveRK4(
    x,
    initialWavefunction,
    potential,
    dt,
    steps
) {
    let state = [...initialWavefunction];
    const dx = x[1] - x[0];
    const records = [];

    for (let step = 0; step <= steps; step += 1) {
        if (step % Math.max(1, Math.floor(steps / 5)) === 0) {
            records.push({
                step,
                time: step * dt,
                state: [...state]
            });
        }

        if (step === steps) {
            break;
        }

        state = rk4Step(
            x,
            state,
            dt,
            potential
        );

        // Hard-wall numerical boundaries.
        state[0] = complex();
        state[state.length - 1] = complex();

        // RK4 is not inherently unitary. Explicit normalization is useful
        // when the goal is a stable educational simulation.
        state = normalizeWavefunction(
            state,
            dx
        );
    }

    return records;
}

// ---------------------------------------------------------------------------
// Asynchronous evolution
// ---------------------------------------------------------------------------

async function evolveWithProgress(
    x,
    initialWavefunction,
    potential,
    dt,
    steps,
    progressCallback
) {
    let state = [...initialWavefunction];
    const dx = x[1] - x[0];

    for (let step = 0; step < steps; step += 1) {
        state = rk4Step(
            x,
            state,
            dt,
            potential
        );

        state[0] = complex();
        state[state.length - 1] = complex();

        state = normalizeWavefunction(
            state,
            dx
        );

        if (
            typeof progressCallback === "function" &&
            (
                step === 0 ||
                step === steps - 1 ||
                step % Math.max(1, Math.floor(steps / 10)) === 0
            )
        ) {
            progressCallback({
                step: step + 1,
                totalSteps: steps,
                probability: totalProbability(
                    state,
                    dx
                ),
                meanPosition: expectationPosition(
                    x,
                    state
                )
            });

            // Yield control. In a browser this prevents a long numerical
            // loop from blocking rendering and input handling.
            await Promise.resolve();
        }
    }

    return state;
}

// ---------------------------------------------------------------------------
// Finite square-well eigenstate
// ---------------------------------------------------------------------------

function infiniteWellState(
    x,
    length,
    quantumNumber
) {
    const amplitude = Math.sqrt(2 / length);

    return x.map(position =>
        complex(
            amplitude *
            Math.sin(
                quantumNumber *
                Math.PI *
                position /
                length
            ),
            0
        )
    );
}

function infiniteWellEnergy(
    quantumNumber,
    length
) {
    return (
        quantumNumber ** 2 *
        Math.PI ** 2 *
        HBAR ** 2 /
        (2 * MASS * length ** 2)
    );
}

function evolveStationaryState(
    state,
    energy,
    time
) {
    const phase = complexFromPolar(
        1,
        -energy * time / HBAR
    );

    return state.map(
        value => complexMultiply(
            value,
            phase
        )
    );
}

// ---------------------------------------------------------------------------
// Discrete Fourier transform
// ---------------------------------------------------------------------------

function dft(values) {
    /*
     * Direct DFT:
     *
     * X[k] = Σ x[n] exp(-2πikn/N)
     *
     * Complexity: O(N²).
     */
    const N = values.length;
    const result = [];

    for (let k = 0; k < N; k += 1) {
        let sum = complex();

        for (let n = 0; n < N; n += 1) {
            const phase = complexFromPolar(
                1,
                -2 * Math.PI * k * n / N
            );

            sum = complexAdd(
                sum,
                complexMultiply(
                    values[n],
                    phase
                )
            );
        }

        result.push(sum);
    }

    return result;
}

function idft(values) {
    const N = values.length;
    const result = [];

    for (let n = 0; n < N; n += 1) {
        let sum = complex();

        for (let k = 0; k < N; k += 1) {
            const phase = complexFromPolar(
                1,
                2 * Math.PI * k * n / N
            );

            sum = complexAdd(
                sum,
                complexMultiply(
                    values[k],
                    phase
                )
            );
        }

        result.push(
            complexScale(sum, 1 / N)
        );
    }

    return result;
}

// ---------------------------------------------------------------------------
// Diagnostics
// ---------------------------------------------------------------------------

function maximumDifference(first, second) {
    let maximum = 0;

    for (let index = 0; index < first.length; index += 1) {
        maximum = Math.max(
            maximum,
            complexMagnitude(
                complexSubtract(
                    first[index],
                    second[index]
                )
            )
        );
    }

    return maximum;
}

function printSection(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

// ---------------------------------------------------------------------------
// Demonstrations
// ---------------------------------------------------------------------------

function demonstrateNormalization() {
    printSection("1. Normalization");

    const x = createGrid(-10, 10, 401);
    const state = gaussianWavePacket(
        x,
        -2,
        1,
        3
    );

    const probability = totalProbability(
        state,
        x[1] - x[0]
    );

    console.log(
        `Grid points: ${x.length}`
    );

    console.log(
        `Total probability: ${probability.toFixed(12)}`
    );

    console.log(
        "A normalized state has integral |ψ|² dx = 1."
    );
}

function demonstrateStationaryState() {
    printSection("2. Stationary state");

    const length = 10;
    const x = createGrid(
        0,
        length,
        401
    );

    const state = infiniteWellState(
        x,
        length,
        2
    );

    const energy = infiniteWellEnergy(
        2,
        length
    );

    const evolved = evolveStationaryState(
        state,
        energy,
        3
    );

    const initialDensity = probabilityDensity(
        state
    );

    const evolvedDensity = probabilityDensity(
        evolved
    );

    const densityDifference = Math.max(
        ...initialDensity.map(
            (value, index) =>
                Math.abs(
                    value -
                    evolvedDensity[index]
                )
        )
    );

    console.log(`Energy E₂: ${energy}`);
    console.log(
        `Maximum |ψ|² change: ${densityDifference}`
    );
    console.log(
        "The phase changes while the probability density remains unchanged."
    );
}

function demonstrateSuperposition() {
    printSection("3. Superposition and interference");

    const length = 10;
    const x = createGrid(
        0,
        length,
        401
    );

    const first = infiniteWellState(
        x,
        length,
        1
    );

    const second = infiniteWellState(
        x,
        length,
        2
    );

    const coefficient = 1 / Math.sqrt(2);

    const state = first.map(
        (value, index) =>
            complexScale(
                complexAdd(
                    value,
                    second[index]
                ),
                coefficient
            )
    );

    const time = 20;
    const energy1 = infiniteWellEnergy(
        1,
        length
    );
    const energy2 = infiniteWellEnergy(
        2,
        length
    );

    const phase1 = complexFromPolar(
        1,
        -energy1 * time
    );

    const phase2 = complexFromPolar(
        1,
        -energy2 * time
    );

    const evolved = first.map(
        (value, index) =>
            complexScale(
                complexAdd(
                    complexMultiply(
                        value,
                        phase1
                    ),
                    complexMultiply(
                        second[index],
                        phase2
                    )
                ),
                coefficient
            )
    );

    console.log(
        `Initial probability: ${totalProbability(
            state,
            x[1] - x[0]
        ).toFixed(8)}`
    );

    console.log(
        `Evolved probability: ${totalProbability(
            evolved,
            x[1] - x[0]
        ).toFixed(8)}`
    );

    console.log(
        "Relative phases between different energies create time-dependent interference."
    );
}

function demonstrateRK4() {
    printSection("4. Free-particle RK4 evolution");

    const x = createGrid(
        -8,
        8,
        201
    );

    const state = gaussianWavePacket(
        x,
        -2,
        0.8,
        4
    );

    const records = evolveRK4(
        x,
        state,
        freeParticlePotential,
        0.0008,
        60
    );

    for (const record of records) {
        const probability = totalProbability(
            record.state,
            x[1] - x[0]
        );

        const position = expectationPosition(
            x,
            record.state
        );

        const energy = expectationEnergy(
            x,
            record.state,
            freeParticlePotential
        );

        console.log(
            `step=${record.step}, ` +
            `t=${record.time.toFixed(4)}, ` +
            `<x>=${position.toFixed(5)}, ` +
            `P=${probability.toFixed(8)}, ` +
            `<H>=${energy.toFixed(6)}`
        );
    }
}

function demonstrateHarmonicOscillator() {
    printSection("5. Harmonic oscillator");

    const x = createGrid(
        -8,
        8,
        301
    );

    const state = gaussianWavePacket(
        x,
        1.5,
        1,
        2
    );

    const potential = position =>
        harmonicPotential(
            position,
            1
        );

    const energy = expectationEnergy(
        x,
        state,
        potential
    );

    console.log(
        `Initial harmonic-oscillator energy: ${energy.toFixed(8)}`
    );

    console.log(
        "The Hamiltonian combines kinetic energy with V(x)=mω²x²/2."
    );
}

function demonstrateBarrier() {
    printSection("6. Potential barrier and tunneling");

    const x = createGrid(
        -10,
        10,
        256
    );

    const potential = position =>
        squareBarrierPotential(
            position,
            -0.5,
            0.5,
            7
        );

    const state = gaussianWavePacket(
        x,
        -4,
        0.7,
        4
    );

    const energy = expectationEnergy(
        x,
        state,
        potential
    );

    console.log(
        `Initial total energy estimate: ${energy.toFixed(6)}`
    );

    console.log(
        "A finite barrier does not impose ψ=0 throughout the barrier. "
        + "The wavefunction can have nonzero amplitude there and beyond it."
    );
}

function demonstrateFourierRepresentation() {
    printSection("7. Fourier representation");

    const x = createGrid(
        -4,
        4,
        16
    );

    const state = gaussianWavePacket(
        x,
        0,
        0.9,
        2
    );

    const transformed = dft(state);
    const reconstructed = idft(transformed);

    console.log(
        `DFT reconstruction error: ${
            maximumDifference(
                state,
                reconstructed
            ).toExponential(3)
        }`
    );

    console.log(
        "The DFT exposes the discrete momentum-like spectral content of the state."
    );
}

async function demonstrateAsyncEvolution() {
    printSection("8. Asynchronous numerical evolution");

    const x = createGrid(
        -7,
        7,
        151
    );

    const initial = gaussianWavePacket(
        x,
        -2,
        0.9,
        3
    );

    const finalState = await evolveWithProgress(
        x,
        initial,
        freeParticlePotential,
        0.0005,
        20,
        progress => {
            console.log(
                `progress ${progress.step}/${progress.totalSteps}: ` +
                `<x>=${progress.meanPosition.toFixed(5)}, ` +
                `P=${progress.probability.toFixed(8)}`
            );
        }
    );

    console.log(
        `Final probability: ${totalProbability(
            finalState,
            x[1] - x[0]
        ).toFixed(10)}`
    );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
    console.log(
        "TIME EVOLUTION AND SCHRÖDINGER EQUATION CONCEPTS"
    );

    console.log(
        "Dimensionless units: ħ = 1, m = 1"
    );

    demonstrateNormalization();
    demonstrateStationaryState();
    demonstrateSuperposition();
    demonstrateRK4();
    demonstrateHarmonicOscillator();
    demonstrateBarrier();
    demonstrateFourierRepresentation();
    await demonstrateAsyncEvolution();

    printSection("9. Important JavaScript implementation observations");

    console.log(
        "Complex arithmetic must be represented explicitly because JavaScript "
        + "does not provide a built-in scalar complex-number type."
    );

    console.log(
        "Array-based wavefunctions make discretized quantum states easy to "
        + "inspect, transform, validate, and connect to browser interfaces."
    );

    console.log(
        "Asynchronous evolution can yield control to a browser event loop, "
        + "which is useful when numerical propagation is part of an interactive UI."
    );

    console.log(
        "For large production simulations, typed arrays, optimized FFT "
        + "implementations, Web Workers, WebAssembly, or native numerical "
        + "libraries can substantially improve performance."
    );
}

main().catch(error => {
    console.error("Simulation failed:", error);
    process.exitCode = 1;
});
