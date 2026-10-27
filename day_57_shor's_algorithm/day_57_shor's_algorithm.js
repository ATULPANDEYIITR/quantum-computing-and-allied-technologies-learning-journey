'use strict';

/*
 * Shor's algorithm: integer factorization concepts.
 *
 * This Node.js program models:
 *   1. classical preprocessing,
 *   2. modular arithmetic,
 *   3. multiplicative order,
 *   4. continued fractions,
 *   5. a small QFT state-vector simulation,
 *   6. factor extraction from an even period.
 *
 * The state-vector portion is intentionally small-scale because its
 * memory and computational cost grow exponentially with register size.
 */

const crypto = require('node:crypto');

class FactorizationError extends Error {}

function gcd(a, b) {
    a = Math.abs(a);
    b = Math.abs(b);

    while (b !== 0) {
        [a, b] = [b, a % b];
    }
    return a;
}

function extendedGcd(a, b) {
    let oldR = a;
    let r = b;
    let oldS = 1;
    let s = 0;
    let oldT = 0;
    let t = 1;

    while (r !== 0) {
        const q = Math.trunc(oldR / r);
        [oldR, r] = [r, oldR - q * r];
        [oldS, s] = [s, oldS - q * s];
        [oldT, t] = [t, oldT - q * t];
    }

    return { gcd: oldR, x: oldS, y: oldT };
}

function modInverse(a, modulus) {
    const result = extendedGcd(a, modulus);
    if (result.gcd !== 1) {
        throw new FactorizationError('Modular inverse does not exist.');
    }
    return ((result.x % modulus) + modulus) % modulus;
}

function modPow(base, exponent, modulus) {
    if (modulus <= 0) {
        throw new FactorizationError('Modulus must be positive.');
    }

    let b = BigInt(base);
    let e = BigInt(exponent);
    const m = BigInt(modulus);

    if (e < 0n) {
        b = BigInt(modInverse(Number(b), Number(m)));
        e = -e;
    }

    b %= m;
    let result = 1n;

    while (e > 0n) {
        if (e & 1n) {
            result = (result * b) % m;
        }
        b = (b * b) % m;
        e >>= 1n;
    }

    return Number(result);
}

function isPrime(n) {
    if (!Number.isSafeInteger(n) || n < 2) {
        return false;
    }

    if (n % 2 === 0) {
        return n === 2;
    }

    for (let d = 3; d * d <= n; d += 2) {
        if (n % d === 0) {
            return false;
        }
    }

    return true;
}

function trialFactorization(n) {
    if (!Number.isSafeInteger(n) || n < 2) {
        throw new FactorizationError('n must be an integer >= 2.');
    }

    const factors = [];
    let value = n;

    while (value % 2 === 0) {
        factors.push(2);
        value /= 2;
    }

    for (let divisor = 3; divisor * divisor <= value; divisor += 2) {
        while (value % divisor === 0) {
            factors.push(divisor);
            value /= divisor;
        }
    }

    if (value > 1) {
        factors.push(value);
    }

    return factors;
}

function multiplicativeOrder(a, n) {
    if (n <= 1 || gcd(a, n) !== 1) {
        return null;
    }

    let value = 1;

    for (let r = 1; r <= n; r++) {
        value = modPow(value * a, 1, n);
        if (value === 1) {
            return r;
        }
    }

    return null;
}

function continuedFractionConvergents(numerator, denominator) {
    if (denominator <= 0) {
        throw new FactorizationError('Denominator must be positive.');
    }

    const quotients = [];
    let a = numerator;
    let b = denominator;

    while (b !== 0) {
        const q = Math.floor(a / b);
        quotients.push(q);
        [a, b] = [b, a - q * b];
    }

    const results = [];
    let pMinus2 = 0;
    let pMinus1 = 1;
    let qMinus2 = 1;
    let qMinus1 = 0;

    for (const q of quotients) {
        const p = q * pMinus1 + pMinus2;
        const denominatorValue = q * qMinus1 + qMinus2;

        results.push([p, denominatorValue]);

        pMinus2 = pMinus1;
        pMinus1 = p;
        qMinus2 = qMinus1;
        qMinus1 = denominatorValue;
    }

    return results;
}

function recoverPeriod(measured, q, a, n) {
    for (const [, denominator] of continuedFractionConvergents(measured, q)) {
        if (denominator <= 0 || denominator > n) {
            continue;
        }

        if (modPow(a, denominator, n) === 1) {
            return denominator;
        }

        for (let multiplier = 2; multiplier <= n; multiplier++) {
            const candidate = denominator * multiplier;
            if (candidate > 2 * n) {
                break;
            }

            if (modPow(a, candidate, n) === 1) {
                return candidate;
            }
        }
    }

    return null;
}

function qft(state, inverse = false) {
    const size = state.length;

    if (size === 0 || (size & (size - 1)) !== 0) {
        throw new FactorizationError('QFT size must be a power of two.');
    }

    const output = new Array(size).fill(null).map(() => [0, 0]);
    const sign = inverse ? 1 : -1;
    const scale = 1 / Math.sqrt(size);

    for (let k = 0; k < size; k++) {
        let real = 0;
        let imaginary = 0;

        for (let j = 0; j < size; j++) {
            const angle = sign * 2 * Math.PI * j * k / size;
            const cos = Math.cos(angle);
            const sin = Math.sin(angle);
            const [sr, si] = state[j];

            real += sr * cos - si * sin;
            imaginary += sr * sin + si * cos;
        }

        output[k] = [real * scale, imaginary * scale];
    }

    return output;
}

function complexMagnitudeSquared(value) {
    return value[0] * value[0] + value[1] * value[1];
}

function randomIndex(probabilities) {
    let total = 0;
    for (const probability of probabilities) {
        total += probability;
    }

    if (!Number.isFinite(total) || Math.abs(total - 1) > 1e-8) {
        throw new FactorizationError('Invalid probability distribution.');
    }

    const randomBytes = crypto.randomBytes(8);
    const integer =
        Number(randomBytes.readBigUInt64BE(0) % 1000000n) / 1000000;

    let cumulative = 0;
    for (let index = 0; index < probabilities.length; index++) {
        cumulative += probabilities[index];
        if (integer <= cumulative) {
            return index;
        }
    }

    return probabilities.length - 1;
}

function simulateQFTPeriodMeasurement(n, a) {
    const order = multiplicativeOrder(a, n);

    if (order === null) {
        throw new FactorizationError('No multiplicative order exists.');
    }

    let size = 1;
    while (size < n * n) {
        size <<= 1;
    }

    if (size > 256) {
        throw new FactorizationError(
            'State-vector QFT simulation is limited to small inputs.'
        );
    }

    const targetExponent = Math.floor(Math.random() * order);
    const targetValue = modPow(a, targetExponent, n);

    const positions = [];
    for (let x = 0; x < size; x++) {
        if (modPow(a, x, n) === targetValue) {
            positions.push(x);
        }
    }

    const state = new Array(size).fill(null).map(() => [0, 0]);
    const amplitude = 1 / Math.sqrt(positions.length);

    for (const position of positions) {
        state[position] = [amplitude, 0];
    }

    const transformed = qft(state);
    const probabilities = transformed.map(complexMagnitudeSquared);

    const total = probabilities.reduce((sum, p) => sum + p, 0);
    const normalized = probabilities.map(p => p / total);
    const measured = randomIndex(normalized);

    return { measured, registerSize: size };
}

function deriveFactors(n, a, period) {
    if (period === null || period <= 0 || period % 2 !== 0) {
        return null;
    }

    const halfPower = modPow(a, period / 2, n);

    if (halfPower === n - 1) {
        return null;
    }

    const left = gcd(halfPower - 1, n);
    const right = gcd(halfPower + 1, n);

    if (
        left > 1 &&
        left < n &&
        right > 1 &&
        right < n &&
        left * right === n
    ) {
        return [Math.min(left, right), Math.max(left, right)];
    }

    return null;
}

function factorWithShorStructure(
    n,
    { attempts = 32, useQFTSimulation = false } = {}
) {
    if (!Number.isSafeInteger(n) || n < 2) {
        throw new FactorizationError('n must be a safe integer >= 2.');
    }

    if (isPrime(n)) {
        return {
            n,
            factors: [n],
            status: 'prime',
            message: 'Input is prime.'
        };
    }

    if (n % 2 === 0) {
        return {
            n,
            factors: [2, n / 2],
            status: 'factored',
            message: 'Even-number preprocessing found a factor.'
        };
    }

    for (let attempt = 0; attempt < attempts; attempt++) {
        const a = 2 + Math.floor(Math.random() * (n - 2));
        const commonFactor = gcd(a, n);

        if (commonFactor > 1 && commonFactor < n) {
            return {
                n,
                factors: [commonFactor, n / commonFactor].sort((x, y) => x - y),
                base: a,
                period: null,
                status: 'factored',
                message: 'Random base exposed a non-trivial gcd.'
            };
        }

        if (commonFactor !== 1) {
            continue;
        }

        let period;

        if (useQFTSimulation) {
            try {
                const measurement = simulateQFTPeriodMeasurement(n, a);
                period = recoverPeriod(
                    measurement.measured,
                    measurement.registerSize,
                    a,
                    n
                );
            } catch {
                period = null;
            }
        } else {
            period = multiplicativeOrder(a, n);
        }

        if (period === null || period % 2 !== 0) {
            continue;
        }

        const factors = deriveFactors(n, a, period);

        if (factors) {
            return {
                n,
                factors,
                base: a,
                period,
                status: 'factored',
                message: 'Factors recovered from the even multiplicative order.'
            };
        }
    }

    return {
        n,
        factors: [],
        status: 'retry',
        message: 'No usable period was obtained within the attempt limit.'
    };
}

function validate(result) {
    if (result.status !== 'factored') {
        return;
    }

    if (result.factors.length !== 2) {
        throw new Error('Expected two non-trivial factors.');
    }

    if (result.factors[0] * result.factors[1] !== result.n) {
        throw new Error('Factorization product is incorrect.');
    }
}

function demonstrateOrder(n, a) {
    const order = multiplicativeOrder(a, n);

    if (order === null) {
        console.log(`a=${a}, n=${n}: a is not coprime to n.`);
        return;
    }

    const sequence = [];
    for (let exponent = 0; exponent < order; exponent++) {
        sequence.push(modPow(a, exponent, n));
    }

    console.log(`a=${a}, n=${n}`);
    console.log(`  periodic sequence: ${sequence.join(', ')}`);
    console.log(`  order r: ${order}`);
    console.log(`  a^r mod n: ${modPow(a, order, n)}`);

    if (order % 2 === 0) {
        console.log(`  factors: ${deriveFactors(n, a, order) ?? 'retry'}`);
    } else {
        console.log('  odd order: retry with another base.');
    }
}

function main() {
    console.log("Shor's Algorithm: Small-Integer Demonstration");
    console.log('='.repeat(48));

    for (const n of [15, 21, 35]) {
        const result = factorWithShorStructure(n, {
            attempts: 40,
            useQFTSimulation: false
        });

        validate(result);

        console.log(
            `n=${n}: status=${result.status}, ` +
            `factors=${result.factors.join(' × ') || 'none'}, ` +
            `base=${result.base ?? 'n/a'}, ` +
            `period=${result.period ?? 'n/a'}`
        );
        console.log(`  ${result.message}`);
    }

    console.log('\nOrder-finding examples');
    console.log('-'.repeat(48));
    demonstrateOrder(15, 2);
    demonstrateOrder(21, 2);

    console.log('\nQFT state-vector example');
    console.log('-'.repeat(48));

    const qftResult = factorWithShorStructure(15, {
        attempts: 40,
        useQFTSimulation: true
    });

    validate(qftResult);

    console.log(
        `QFT-simulated path: factors=${qftResult.factors.join(' × ') || 'none'}, ` +
        `base=${qftResult.base ?? 'n/a'}, ` +
        `period=${qftResult.period ?? 'n/a'}`
    );

    console.log('\nReference factorization');
    console.log('-'.repeat(48));

    for (const n of [15, 21, 35, 77]) {
        console.log(`${n} = ${trialFactorization(n).join(' × ')}`);
    }

    if (gcd(84, 30) !== 6) throw new Error('gcd test failed.');
    if (modPow(7, 4, 15) !== 1) throw new Error('modPow test failed.');
    if (multiplicativeOrder(2, 15) !== 4) {
        throw new Error('order test failed.');
    }
    if (JSON.stringify(deriveFactors(15, 2, 4)) !== JSON.stringify([3, 5])) {
        throw new Error('factor extraction test failed.');
    }

    console.log('\nValidation checks passed.');
}

main();
