"use strict";

/*
 * Shor circuit components:
 * QFT, phase estimation, modular periodicity, and factor recovery.
 *
 * This file uses Node.js standard-library features only. Complex amplitudes
 * are represented by a small immutable Complex class, while the period
 * finding stage uses exact integer arithmetic through BigInt.
 */

class QuantumCircuitError extends Error {}

class Complex {
    constructor(re = 0, im = 0) {
        this.re = re;
        this.im = im;
        Object.freeze(this);
    }

    add(other) {
        return new Complex(this.re + other.re, this.im + other.im);
    }

    multiply(other) {
        return new Complex(
            this.re * other.re - this.im * other.im,
            this.re * other.im + this.im * other.re
        );
    }

    scale(value) {
        return new Complex(this.re * value, this.im * value);
    }

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }
}

function assertPowerOfTwo(value, name = "value") {
    if (!Number.isInteger(value) || value <= 0 || (value & (value - 1)) !== 0) {
        throw new QuantumCircuitError(`${name} must be a positive power of two`);
    }
}

function qft(state) {
    const n = state.length;
    assertPowerOfTwo(n, "state dimension");

    const result = Array.from({ length: n }, () => new Complex());
    const normalization = Math.sqrt(n);

    for (let k = 0; k < n; k++) {
        let total = new Complex();

        for (let x = 0; x < n; x++) {
            const angle = (2 * Math.PI * k * x) / n;
            const root = new Complex(Math.cos(angle), Math.sin(angle));
            total = total.add(state[x].multiply(root));
        }

        result[k] = total.scale(1 / normalization);
    }

    return result;
}

function inverseQft(state) {
    const n = state.length;
    assertPowerOfTwo(n, "state dimension");

    const result = Array.from({ length: n }, () => new Complex());
    const normalization = Math.sqrt(n);

    for (let x = 0; x < n; x++) {
        let total = new Complex();

        for (let k = 0; k < n; k++) {
            const angle = (-2 * Math.PI * x * k) / n;
            const root = new Complex(Math.cos(angle), Math.sin(angle));
            total = total.add(state[k].multiply(root));
        }

        result[x] = total.scale(1 / normalization);
    }

    return result;
}

function probabilities(state) {
    const raw = state.map(value => value.magnitudeSquared());
    const total = raw.reduce((sum, value) => sum + value, 0);

    if (total <= Number.EPSILON) {
        throw new QuantumCircuitError("state has zero norm");
    }

    return raw.map(value => value / total);
}

class QuantumCircuit {
    constructor(qubits) {
        if (!Number.isInteger(qubits) || qubits <= 0) {
            throw new QuantumCircuitError("qubits must be positive");
        }

        this.qubits = qubits;
        this.gates = [];
    }

    add(name, qubits, angle = null) {
        if (!Array.isArray(qubits) || qubits.length === 0) {
            throw new QuantumCircuitError("gate requires qubits");
        }

        if (qubits.some(q => !Number.isInteger(q) || q < 0 || q >= this.qubits)) {
            throw new QuantumCircuitError("gate references an invalid qubit");
        }

        this.gates.push(Object.freeze({ name, qubits: [...qubits], angle }));
    }

    addQft(qubits) {
        const selected = [...qubits];

        if (selected.length === 0 || new Set(selected).size !== selected.length) {
            throw new QuantumCircuitError("QFT requires unique qubits");
        }

        for (let targetIndex = 0; targetIndex < selected.length; targetIndex++) {
            const target = selected[targetIndex];
            this.add("H", [target]);

            for (
                let controlIndex = targetIndex + 1;
                controlIndex < selected.length;
                controlIndex++
            ) {
                const control = selected[controlIndex];
                const angle =
                    Math.PI / (2 ** (controlIndex - targetIndex));
                this.add("CR", [control, target], angle);
            }
        }

        for (let i = 0; i < selected.length / 2; i++) {
            const left = selected[i];
            const right = selected[selected.length - 1 - i];
            this.add("SWAP", [left, right]);
        }
    }

    describe() {
        const lines = [
            `Circuit: ${this.qubits} qubits, ${this.gates.length} gates`
        ];

        this.gates.forEach((gate, index) => {
            const angle =
                gate.angle === null ? "" : ` angle=${gate.angle.toFixed(8)}`;
            lines.push(
                `${String(index + 1).padStart(3, "0")}: ${gate.name} ` +
                `${gate.qubits.join(",")}${angle}`
            );
        });

        return lines.join("\n");
    }
}

function gcd(a, b) {
    a = BigInt(a);
    b = BigInt(b);

    while (b !== 0n) {
        [a, b] = [b, a % b];
    }

    return a < 0n ? -a : a;
}

function modularPower(base, exponent, modulus) {
    base = BigInt(base);
    exponent = BigInt(exponent);
    modulus = BigInt(modulus);

    if (modulus <= 1n) {
        throw new QuantumCircuitError("modulus must exceed one");
    }

    let result = 1n;
    base %= modulus;

    while (exponent > 0n) {
        if (exponent & 1n) {
            result = (result * base) % modulus;
        }

        base = (base * base) % modulus;
        exponent >>= 1n;
    }

    return result;
}

function modularOrder(a, n) {
    a = BigInt(a);
    n = BigInt(n);

    if (!(1n < a && a < n) || gcd(a, n) !== 1n) {
        throw new QuantumCircuitError(
            "require 1 < a < n and gcd(a, n) = 1"
        );
    }

    let value = 1n;

    for (let r = 1n; r <= n; r++) {
        value = (value * a) % n;

        if (value === 1n) {
            return r;
        }
    }

    return null;
}

function phaseEstimationPeaks(period, countingQubits) {
    if (period <= 0n || countingQubits <= 0) {
        throw new QuantumCircuitError("invalid phase-estimation parameters");
    }

    const q = 2 ** countingQubits;
    const result = [];

    for (let s = 0n; s < period; s++) {
        const phase = Number(s) / Number(period);
        const measurement = Math.round(q * phase) % q;

        result.push({
            measurement,
            measuredPhase: measurement / q,
            idealPhase: phase
        });
    }

    return result;
}

function continuedFractionApproximation(numerator, denominator, maxDenominator) {
    let n = numerator;
    let d = denominator;
    const terms = [];

    while (d !== 0) {
        const quotient = Math.floor(n / d);
        terms.push(quotient);
        [n, d] = [d, n % d];
    }

    let pMinus2 = 0;
    let pMinus1 = 1;
    let qMinus2 = 1;
    let qMinus1 = 0;

    let best = { numerator: 0, denominator: 1 };

    for (const term of terms) {
        const p = term * pMinus1 + pMinus2;
        const q = term * qMinus1 + qMinus2;

        if (q > maxDenominator) {
            break;
        }

        best = { numerator: p, denominator: q };
        [pMinus2, pMinus1] = [pMinus1, p];
        [qMinus2, qMinus1] = [qMinus1, q];
    }

    return best;
}

function shorPeriodPipeline(a, n, countingQubits = 8) {
    a = BigInt(a);
    n = BigInt(n);

    if (n % 2n === 0n) {
        return { status: "trivial_factor", factor: 2n };
    }

    const commonFactor = gcd(a, n);

    if (commonFactor > 1n) {
        return { status: "trivial_factor", factor: commonFactor };
    }

    const period = modularOrder(a, n);

    if (period === null) {
        return { status: "period_not_found" };
    }

    const peaks = phaseEstimationPeaks(period, countingQubits);
    const peak = peaks.find(item => item.measurement > 0) || peaks[0];
    const q = 2 ** countingQubits;

    const approximation = continuedFractionApproximation(
        peak.measurement,
        q,
        Number(n)
    );

    const candidatePeriods = new Set([
        approximation.denominator
    ]);

    for (let delta = 1; delta <= 3; delta++) {
        if (approximation.denominator - delta > 0) {
            candidatePeriods.add(approximation.denominator - delta);
        }

        candidatePeriods.add(approximation.denominator + delta);
    }

    const factors = new Set();

    for (const candidate of candidatePeriods) {
        if (candidate <= 0 || candidate % 2 !== 0) {
            continue;
        }

        const x = modularPower(a, BigInt(candidate / 2), n);

        if (x === 1n || x === n - 1n) {
            continue;
        }

        const left = gcd(x - 1n, n);
        const right = gcd(x + 1n, n);

        if (left > 1n && left < n) {
            factors.add(left);
        }

        if (right > 1n && right < n) {
            factors.add(right);
        }
    }

    return {
        status: "complete",
        a,
        n,
        period,
        countingQubits,
        measurement: peak.measurement,
        measuredPhase: peak.measuredPhase,
        idealPhase: peak.idealPhase,
        candidatePeriods: [...candidatePeriods].sort((x, y) => x - y),
        factors: [...factors].sort((x, y) => (x < y ? -1 : 1))
    };
}

async function evaluateMeasurementStream(period, countingQubits) {
    /*
     * Async iteration models a measurement pipeline. Real hardware would
     * produce observations asynchronously; this model keeps the same
     * separation between measurement acquisition and classical analysis.
     */
    const peaks = phaseEstimationPeaks(period, countingQubits);

    async function* measurements() {
        for (const peak of peaks) {
            await Promise.resolve();
            yield peak;
        }
    }

    const results = [];

    for await (const measurement of measurements()) {
        results.push(measurement);
    }

    return results;
}

async function main() {
    console.log("=== QFT ===");

    const initial = [
        new Complex(0.5),
        new Complex(0.5),
        new Complex(),
        new Complex()
    ];

    const transformed = qft(initial);
    const restored = inverseQft(transformed);
    const distribution = probabilities(transformed);

    transformed.forEach((value, index) => {
        console.log(
            `|${index.toString(2).padStart(2, "0")}> ` +
            `amplitude=${value.re.toFixed(6)}${value.im >= 0 ? "+" : ""}` +
            `${value.im.toFixed(6)}i ` +
            `probability=${distribution[index].toFixed(6)}`
        );
    });

    const reconstructionError = Math.max(
        ...initial.map((value, index) => {
            const dr = restored[index].re - value.re;
            const di = restored[index].im - value.im;
            return Math.hypot(dr, di);
        })
    );

    console.log(`Inverse-QFT error: ${reconstructionError.toExponential(3)}`);

    const circuit = new QuantumCircuit(4);
    circuit.addQft([0, 1, 2, 3]);
    console.log(circuit.describe());

    console.log("\n=== Phase estimation and period finding ===");

    const result = shorPeriodPipeline(2n, 15n, 8);

    for (const [key, value] of Object.entries(result)) {
        console.log(`${key}:`, value);
    }

    if (result.status !== "complete") {
        throw new Error("period finding failed");
    }

    if (result.period !== 4n) {
        throw new Error("unexpected period");
    }

    const measurements = await evaluateMeasurementStream(
        result.period,
        result.countingQubits
    );

    console.log(`Asynchronous measurement records: ${measurements.length}`);

    console.log("\n=== Failure handling ===");

    try {
        qft([new Complex(1), new Complex(2), new Complex(3)]);
    } catch (error) {
        console.log(`Invalid QFT rejected: ${error.message}`);
    }

    const earlyFactor = shorPeriodPipeline(6n, 15n);
    console.log("Early GCD factor:", earlyFactor.factor.toString());

    console.log("\n=== Complexity ===");
    console.log("Direct QFT simulation: O(N^2).");
    console.log("QFT decomposition: O(q^2) elementary gates.");
    console.log("Modular exponentiation uses repeated squaring.");
    console.log("Exact period and factor arithmetic uses BigInt.");
}

main().catch(error => {
    console.error(`Execution failed: ${error.message}`);
    process.exitCode = 1;
});
