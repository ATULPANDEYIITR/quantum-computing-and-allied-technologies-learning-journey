'use strict';

/*
 * Simon's algorithm as an event-driven hidden-period simulator.
 *
 * The implementation models the information flow:
 *   oracle -> quantum measurement constraints -> classical GF(2) solver
 *
 * It does not allocate a 2^n state vector. Instead, the Hadamard/oracle/
 * interference stage is represented by its exact measurement constraint:
 * every observed y satisfies y · s = 0 (mod 2).
 */

class SimonOracle {
    constructor(secret) {
        if (!/^[01]+$/.test(secret) || /^0+$/.test(secret)) {
            throw new Error('secret must be a non-zero binary string');
        }

        this.secret = secret;
        this.n = secret.length;
        this.secretValue = Number.parseInt(secret, 2);
    }

    evaluate(x) {
        if (!Number.isSafeInteger(x) || x < 0 || x >= 2 ** this.n) {
            throw new RangeError('x is outside the oracle domain');
        }

        return Math.min(x, x ^ this.secretValue);
    }

    verifyPromise() {
        for (let x = 0; x < 2 ** this.n; x += 1) {
            if (this.evaluate(x) !== this.evaluate(x ^ this.secretValue)) {
                return false;
            }
        }

        const outputs = new Map();

        for (let x = 0; x < 2 ** this.n; x += 1) {
            const value = this.evaluate(x);
            outputs.set(value, (outputs.get(value) ?? 0) + 1);
        }

        return [...outputs.values()].every(count => count === 2);
    }
}

function dotMod2(a, b) {
    if (a.length !== b.length) {
        throw new Error('vectors must have equal length');
    }

    let result = 0;

    for (let i = 0; i < a.length; i += 1) {
        result ^= Number(a[i]) & Number(b[i]);
    }

    return result;
}

function randomUnitVector(length, random = Math.random) {
    const vector = Array(length).fill(0);
    vector[Math.floor(random() * length)] = 1;
    return vector;
}

function randomNonZeroVector(length, random = Math.random) {
    let vector;

    do {
        vector = Array.from(
            { length },
            () => random() < 0.5 ? 0 : 1
        );
    } while (vector.every(bit => bit === 0));

    return vector;
}

function xorVectors(a, b) {
    return a.map((value, index) => value ^ b[index]);
}

function vectorToString(vector) {
    return vector.join('');
}

function independentRank(rows) {
    if (rows.length === 0) {
        return 0;
    }

    const matrix = rows.map(row => [...row]);
    const columns = matrix[0].length;
    let rank = 0;

    for (let column = 0; column < columns; column += 1) {
        let pivot = -1;

        for (let row = rank; row < matrix.length; row += 1) {
            if (matrix[row][column] === 1) {
                pivot = row;
                break;
            }
        }

        if (pivot === -1) {
            continue;
        }

        [matrix[rank], matrix[pivot]] = [matrix[pivot], matrix[rank]];

        for (let row = 0; row < matrix.length; row += 1) {
            if (row !== rank && matrix[row][column] === 1) {
                matrix[row] = xorVectors(matrix[row], matrix[rank]);
            }
        }

        rank += 1;
    }

    return rank;
}

function nullspace(rows, n) {
    const matrix = rows.map(row => [...row]);
    const pivotColumns = [];
    let rank = 0;

    for (let column = 0; column < n; column += 1) {
        let pivot = -1;

        for (let row = rank; row < matrix.length; row += 1) {
            if (matrix[row][column] === 1) {
                pivot = row;
                break;
            }
        }

        if (pivot === -1) {
            continue;
        }

        [matrix[rank], matrix[pivot]] = [matrix[pivot], matrix[rank]];

        for (let row = 0; row < matrix.length; row += 1) {
            if (row !== rank && matrix[row][column] === 1) {
                matrix[row] = xorVectors(matrix[row], matrix[rank]);
            }
        }

        pivotColumns.push(column);
        rank += 1;
    }

    const pivotSet = new Set(pivotColumns);
    const freeColumns = Array.from(
        { length: n },
        (_, index) => index
    ).filter(column => !pivotSet.has(column));

    return freeColumns.map(freeColumn => {
        const vector = Array(n).fill(0);
        vector[freeColumn] = 1;

        for (let row = 0; row < pivotColumns.length; row += 1) {
            vector[pivotColumns[row]] = matrix[row][freeColumn];
        }

        return vector;
    });
}

class MeasurementStream {
    constructor(secret, seed = 0x9e3779b9) {
        this.secret = secret;
        this.n = secret.length;
        this.state = seed >>> 0;
    }

    nextRandom() {
        // Deterministic xorshift32 keeps the demonstration reproducible.
        let x = this.state;
        x ^= x << 13;
        x ^= x >>> 17;
        x ^= x << 5;
        this.state = x >>> 0;
        return this.state / 0x100000000;
    }

    measure() {
        /*
         * The allowed measurement space has dimension n-1.
         * Rejection sampling gives a uniform vector satisfying y·s=0.
         * This is practical for a teaching simulator, not a physical
         * quantum implementation.
         */
        let y;

        do {
            y = randomNonZeroVector(this.n, () => this.nextRandom());
        } while (dotMod2(y, [...this.secret].map(Number)) !== 0);

        return y;
    }
}

class SimonWorkflow {
    constructor(secret) {
        this.oracle = new SimonOracle(secret);
        this.measurements = [];
    }

    async collectIndependentMeasurements() {
        const targetRank = Math.max(this.oracle.n - 1, 0);
        const stream = new MeasurementStream(this.oracle.secret);

        return new Promise((resolve, reject) => {
            const collect = () => {
                try {
                    if (independentRank(this.measurements) >= targetRank) {
                        resolve(this.measurements);
                        return;
                    }

                    const measurement = stream.measure();
                    const candidate = [...measurement];

                    if (
                        independentRank([
                            ...this.measurements,
                            candidate
                        ]) > independentRank(this.measurements)
                    ) {
                        this.measurements.push(candidate);
                    }

                    setImmediate(collect);
                } catch (error) {
                    reject(error);
                }
            };

            collect();
        });
    }

    recoverSecret() {
        const basis = nullspace(this.measurements, this.oracle.n);

        if (basis.length !== 1) {
            throw new Error(
                `secret is not uniquely determined; nullity=${basis.length}`
            );
        }

        return vectorToString(basis[0]);
    }
}

async function main() {
    const secret = '101101';
    const workflow = new SimonWorkflow(secret);

    if (!workflow.oracle.verifyPromise()) {
        throw new Error('oracle violates Simon promise');
    }

    await workflow.collectIndependentMeasurements();

    const recovered = workflow.recoverSecret();

    console.log('Simon hidden-period simulation');
    console.log(`Hidden period:       ${secret}`);
    console.log(
        `Independent samples: ${workflow.measurements.length}`
    );
    console.log(
        `Measured constraints: ${workflow.measurements
            .map(vectorToString)
            .join(', ')}`
    );
    console.log(`Recovered period:    ${recovered}`);
    console.log(`Recovery successful: ${recovered === secret}`);
}

main().catch(error => {
    console.error(`Simulation failed: ${error.message}`);
    process.exitCode = 1;
});
