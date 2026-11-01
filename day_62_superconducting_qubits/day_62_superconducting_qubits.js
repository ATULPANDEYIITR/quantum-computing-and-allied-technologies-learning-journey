"use strict";

/*
 * Superconducting Qubits: Josephson Junctions and Circuits
 *
 * Node.js standard-library implementation.
 *
 * Models:
 * - Josephson current-phase relation
 * - Josephson energy and inductance
 * - junction plasma frequency
 * - RCSJ phase dynamics
 * - rf-SQUID potential
 * - transmon transition frequency and anharmonicity
 * - event-driven circuit monitoring
 * - two-level qubit state probabilities and measurement
 */

const PHI0 = 6.62607015e-34 / (2 * Math.PI * 1.602176634e-19);
const H = 6.62607015e-34;

class CircuitError extends Error {}

function assertFinitePositive(value, name) {
    if (!Number.isFinite(value) || value <= 0) {
        throw new CircuitError(`${name} must be positive and finite.`);
    }
}

function assertFinite(value, name) {
    if (!Number.isFinite(value)) {
        throw new CircuitError(`${name} must be finite.`);
    }
}

function formatFrequency(hz) {
    const absolute = Math.abs(hz);

    if (absolute >= 1e9) return `${(hz / 1e9).toFixed(6)} GHz`;
    if (absolute >= 1e6) return `${(hz / 1e6).toFixed(6)} MHz`;
    if (absolute >= 1e3) return `${(hz / 1e3).toFixed(6)} kHz`;
    return `${hz.toFixed(6)} Hz`;
}

class JosephsonJunction {
    constructor({ criticalCurrent, capacitance, normalResistance }) {
        assertFinitePositive(criticalCurrent, "criticalCurrent");
        assertFinitePositive(capacitance, "capacitance");
        assertFinitePositive(normalResistance, "normalResistance");

        this.Ic = criticalCurrent;
        this.C = capacitance;
        this.R = normalResistance;
    }

    get josephsonEnergy() {
        return PHI0 * this.Ic / (2 * Math.PI);
    }

    get josephsonEnergyFrequency() {
        return this.josephsonEnergy / H;
    }

    get josephsonInductance() {
        return PHI0 / (2 * Math.PI * this.Ic);
    }

    get plasmaFrequency() {
        const omega = 1 / Math.sqrt(this.josephsonInductance * this.C);
        return omega / (2 * Math.PI);
    }

    current(phase) {
        assertFinite(phase, "phase");
        return this.Ic * Math.sin(phase);
    }

    voltage(phaseRate) {
        assertFinite(phaseRate, "phaseRate");
        return PHI0 * phaseRate / (2 * Math.PI);
    }

    rcsjAcceleration(biasCurrent, phase, phaseRate) {
        assertFinite(biasCurrent, "biasCurrent");
        assertFinite(phase, "phase");
        assertFinite(phaseRate, "phaseRate");

        const v = this.voltage(phaseRate);
        const numerator =
            biasCurrent - this.current(phase) - v / this.R;

        return numerator / (this.C * PHI0 / (2 * Math.PI));
    }
}

class Transmon {
    constructor(junction, chargingEnergy) {
        if (!(junction instanceof JosephsonJunction)) {
            throw new CircuitError("A valid Josephson junction is required.");
        }

        assertFinitePositive(chargingEnergy, "chargingEnergy");

        this.junction = junction;
        this.EC = chargingEnergy;
    }

    get EJ() {
        return this.junction.josephsonEnergy;
    }

    get EJoverEC() {
        return this.EJ / this.EC;
    }

    get transition01() {
        return (
            Math.sqrt(8 * this.EJ * this.EC) / H -
            this.EC / H
        );
    }

    get anharmonicity() {
        return -this.EC / H;
    }

    levelEnergy(n) {
        if (!Number.isInteger(n) || n < 0) {
            throw new CircuitError("n must be a non-negative integer.");
        }

        return (
            -this.EJ +
            Math.sqrt(8 * this.EJ * this.EC) * (n + 0.5) -
            this.EC / 12 * (6 * n * n + 6 * n + 3)
        );
    }
}

class RfSquid {
    constructor(junction, loopInductance) {
        if (!(junction instanceof JosephsonJunction)) {
            throw new CircuitError("A valid junction is required.");
        }

        assertFinitePositive(loopInductance, "loopInductance");

        this.junction = junction;
        this.L = loopInductance;
    }

    get betaL() {
        return 2 * Math.PI * this.L * this.junction.Ic / PHI0;
    }

    potential(phase, externalFlux) {
        assertFinite(phase, "phase");
        assertFinite(externalFlux, "externalFlux");

        const phiExt = 2 * Math.PI * externalFlux / PHI0;

        const inductive =
            Math.pow(PHI0 / (2 * Math.PI), 2) *
            Math.pow(phase - phiExt, 2) /
            (2 * this.L);

        const josephson =
            -this.junction.josephsonEnergy * Math.cos(phase);

        return inductive + josephson;
    }
}

class Qubit {
    constructor(alpha = { re: 1, im: 0 }, beta = { re: 0, im: 0 }) {
        this.alpha = { ...alpha };
        this.beta = { ...beta };
        this.normalize();
    }

    magnitudeSquared(z) {
        return z.re * z.re + z.im * z.im;
    }

    normalize() {
        const norm = Math.sqrt(
            this.magnitudeSquared(this.alpha) +
            this.magnitudeSquared(this.beta)
        );

        if (!Number.isFinite(norm) || norm <= 0) {
            throw new CircuitError("Qubit state has invalid norm.");
        }

        this.alpha.re /= norm;
        this.alpha.im /= norm;
        this.beta.re /= norm;
        this.beta.im /= norm;
    }

    get probabilityZero() {
        return this.magnitudeSquared(this.alpha);
    }

    get probabilityOne() {
        return this.magnitudeSquared(this.beta);
    }

    rotateY(theta) {
        assertFinite(theta, "theta");

        const c = Math.cos(theta / 2);
        const s = Math.sin(theta / 2);

        const a = this.alpha;
        const b = this.beta;

        this.alpha = {
            re: c * a.re - s * b.re,
            im: c * a.im - s * b.im
        };

        this.beta = {
            re: s * a.re + c * b.re,
            im: s * a.im + c * b.im
        };

        this.normalize();
    }

    measure(randomValue = Math.random()) {
        if (!Number.isFinite(randomValue) ||
            randomValue < 0 ||
            randomValue >= 1) {
            throw new CircuitError("Measurement random value must be in [0, 1).");
        }

        if (randomValue < this.probabilityZero) {
            this.alpha = { re: 1, im: 0 };
            this.beta = { re: 0, im: 0 };
            return 0;
        }

        this.alpha = { re: 0, im: 0 };
        this.beta = { re: 1, im: 0 };
        return 1;
    }
}

/*
 * Event-driven policy:
 * measurements, thermal alarms, and status changes are emitted as
 * asynchronous events instead of being tightly coupled to the model.
 */
class CircuitMonitor {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }

        this.listeners.get(eventName).add(listener);
    }

    emit(eventName, payload) {
        const listeners = this.listeners.get(eventName) || new Set();

        for (const listener of listeners) {
            listener(payload);
        }
    }

    async monitorMeasurement(qubit, shots) {
        if (!(qubit instanceof Qubit)) {
            throw new CircuitError("A Qubit instance is required.");
        }

        if (!Number.isInteger(shots) || shots <= 0 || shots > 1_000_000) {
            throw new CircuitError("shots must be between 1 and 1,000,000.");
        }

        let zero = 0;
        let one = 0;

        for (let i = 0; i < shots; i++) {
            const copy = new Qubit(qubit.alpha, qubit.beta);
            const result = copy.measure();

            if (result === 0) zero++;
            else one++;
        }

        const result = {
            shots,
            zero,
            one,
            zeroProbability: zero / shots,
            oneProbability: one / shots
        };

        this.emit("measurement-complete", result);

        return result;
    }
}

function simulateRcsj(junction, biasCurrent, {
    phase = 0,
    phaseRate = 0,
    dt = 1e-14,
    steps = 100
} = {}) {
    if (!(junction instanceof JosephsonJunction)) {
        throw new CircuitError("A valid junction is required.");
    }

    assertFinitePositive(dt, "dt");

    if (!Number.isInteger(steps) || steps < 1 || steps > 1_000_000) {
        throw new CircuitError("steps must be between 1 and 1,000,000.");
    }

    const trace = [];
    let t = 0;

    for (let i = 0; i <= steps; i++) {
        trace.push({
            time: t,
            phase,
            phaseRate
        });

        const acceleration =
            junction.rcsjAcceleration(biasCurrent, phase, phaseRate);

        // Semi-implicit Euler is used here intentionally: phase velocity
        // is updated before phase, which improves stability over explicit
        // Euler for this simple dissipative oscillator.
        phaseRate += dt * acceleration;
        phase += dt * phaseRate;
        t += dt;
    }

    return trace;
}

function main() {
    const junction = new JosephsonJunction({
        criticalCurrent: 35e-9,
        capacitance: 80e-15,
        normalResistance: 1500
    });

    const transmon = new Transmon(
        junction,
        0.25 * junction.josephsonEnergy
    );

    const squid = new RfSquid(junction, 12e-9);

    console.log("SUPERCONDUCTING QUBIT / JOSEPHSON CIRCUIT MODEL");
    console.log("=".repeat(55));

    console.log("\nJunction");
    console.log(`Ic: ${junction.Ic.toExponential(6)} A`);
    console.log(`C:  ${junction.C.toExponential(6)} F`);
    console.log(`Rn: ${junction.R.toExponential(6)} ohm`);
    console.log(`EJ/h: ${formatFrequency(junction.josephsonEnergyFrequency)}`);
    console.log(`LJ: ${junction.josephsonInductance.toExponential(6)} H`);
    console.log(`Plasma: ${formatFrequency(junction.plasmaFrequency)}`);

    const phase = Math.PI / 3;

    console.log("\nJosephson relations");
    console.log(`Phase: ${phase.toFixed(6)} rad`);
    console.log(
        `Supercurrent: ${junction.current(phase).toExponential(6)} A`
    );

    console.log("\nTransmon");
    console.log(`EJ/EC: ${transmon.EJoverEC.toFixed(4)}`);
    console.log(`f01: ${formatFrequency(transmon.transition01)}`);
    console.log(`Anharmonicity: ${formatFrequency(transmon.anharmonicity)}`);

    for (let n = 0; n < 4; n++) {
        console.log(
            `E${n}: ${transmon.levelEnergy(n).toExponential(8)} J`
        );
    }

    console.log("\nrf-SQUID");
    console.log(`Beta_L: ${squid.betaL.toFixed(6)}`);

    const externalFlux = PHI0 / 2;
    const potential = squid.potential(0, externalFlux);
    console.log(
        `U(phi=0, Phi_ext=Phi0/2): ${potential.toExponential(8)} J`
    );

    console.log("\nRCSJ simulation");
    const trace = simulateRcsj(
        junction,
        0.55 * junction.Ic,
        {
            phase: 0,
            phaseRate: 0,
            dt: 1e-14,
            steps: 20
        }
    );

    for (const point of trace.filter(
        (_, index) => index % 5 === 0
    )) {
        console.log(
            `t=${point.time.toExponential(3)} s ` +
            `phi=${point.phase.toFixed(6)} ` +
            `phiDot=${point.phaseRate.toExponential(4)}`
        );
    }

    console.log("\nQubit state");
    const qubit = new Qubit();
    qubit.rotateY(Math.PI / 2);

    console.log(
        `P(0)=${qubit.probabilityZero.toFixed(4)}, ` +
        `P(1)=${qubit.probabilityOne.toFixed(4)}`
    );

    const monitor = new CircuitMonitor();

    monitor.on("measurement-complete", result => {
        console.log(
            `Measurement event: ${result.shots} shots, ` +
            `zero=${result.zero}, one=${result.one}`
        );
    });

    monitor.monitorMeasurement(qubit, 1000)
        .catch(error => {
            console.error(`Monitoring failure: ${error.message}`);
            process.exitCode = 1;
        });
}

main();
