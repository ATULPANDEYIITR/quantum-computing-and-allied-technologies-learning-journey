"use strict";

const { EventEmitter } = require("node:events");

class Graph {
    constructor(adjacency) {
        if (!Array.isArray(adjacency) || adjacency.length === 0) {
            throw new Error("Graph must contain at least one vertex.");
        }

        const n = adjacency.length;

        for (const row of adjacency) {
            if (!Array.isArray(row) || row.length !== n) {
                throw new Error("Adjacency matrix must be square.");
            }
            if (row.some(value => value !== 0 && value !== 1)) {
                throw new Error("Adjacency values must be 0 or 1.");
            }
        }

        for (let i = 0; i < n; i++) {
            if (adjacency[i][i] !== 0) {
                throw new Error("Self-loops are not supported.");
            }
            for (let j = 0; j < n; j++) {
                if (adjacency[i][j] !== adjacency[j][i]) {
                    throw new Error("Graph must be undirected.");
                }
            }
        }

        this.adjacency = adjacency.map(row => [...row]);
    }

    get size() {
        return this.adjacency.length;
    }

    neighbors(vertex) {
        this.validateVertex(vertex);
        return this.adjacency[vertex]
            .map((connected, index) => connected ? index : -1)
            .filter(index => index >= 0);
    }

    validateVertex(vertex) {
        if (!Number.isInteger(vertex) || vertex < 0 || vertex >= this.size) {
            throw new RangeError(`Invalid vertex: ${vertex}`);
        }
    }
}

function complex(re, im = 0) {
    return { re, im };
}

function add(a, b) {
    return complex(a.re + b.re, a.im + b.im);
}

function multiply(a, b) {
    return complex(
        a.re * b.re - a.im * b.im,
        a.re * b.im + a.im * b.re
    );
}

function scale(a, value) {
    return complex(a.re * value, a.im * value);
}

function magnitudeSquared(a) {
    return a.re * a.re + a.im * a.im;
}

function normalize(state) {
    const norm = Math.sqrt(
        state.reduce((sum, amplitude) => sum + magnitudeSquared(amplitude), 0)
    );

    if (norm === 0) {
        throw new Error("Cannot normalize a zero state.");
    }

    return state.map(amplitude => scale(amplitude, 1 / norm));
}

function hadamard(a, b) {
    const factor = 1 / Math.sqrt(2);
    return [
        scale(add(a, b), factor),
        scale(add(a, scale(b, -1)), factor)
    ];
}

class QuantumWalkEngine extends EventEmitter {
    constructor(graph) {
        super();
        this.graph = graph;
        this.measurementCount = 0;
    }

    async runCoinedLineWalk(steps, initialCoin = [
        complex(1 / Math.sqrt(2)),
        complex(0, 1 / Math.sqrt(2))
    ]) {
        if (!Number.isInteger(steps) || steps < 0) {
            throw new Error("steps must be a non-negative integer.");
        }

        if (initialCoin.length !== 2) {
            throw new Error("A two-state coin is required.");
        }

        let state = new Map([
            ["0:0", initialCoin[0]],
            ["0:1", initialCoin[1]]
        ]);

        for (let step = 0; step < steps; step++) {
            const afterCoin = new Map();

            for (const [key, amplitude] of state) {
                const [position] = key.split(":").map(Number);
                const left = state.get(`${position}:0`) || complex(0);
                const right = state.get(`${position}:1`) || complex(0);
                const [newLeft, newRight] = hadamard(left, right);

                afterCoin.set(`${position}:0`, newLeft);
                afterCoin.set(`${position}:1`, newRight);
            }

            const next = new Map();

            for (const [key, amplitude] of afterCoin) {
                const [position, coin] = key.split(":").map(Number);
                const destination = coin === 0 ? position - 1 : position + 1;
                const destinationKey = `${destination}:${coin}`;
                const current = next.get(destinationKey) || complex(0);
                next.set(destinationKey, add(current, amplitude));
            }

            state = next;
            this.emit("step", { step: step + 1, states: state.size });

            // Yield to the event loop so the engine can participate in
            // larger asynchronous workflows without blocking observers.
            await new Promise(resolve => setImmediate(resolve));
        }

        const probabilities = new Map();

        for (const [key, amplitude] of state) {
            const [position] = key.split(":").map(Number);
            const probability = magnitudeSquared(amplitude);
            probabilities.set(
                position,
                (probabilities.get(position) || 0) + probability
            );
        }

        return new Map([...probabilities.entries()].sort((a, b) => a[0] - b[0]));
    }

    continuousTimeProbability(start, time) {
        this.graph.validateVertex(start);

        if (typeof time !== "number" || !Number.isFinite(time) || time < 0) {
            throw new Error("time must be a finite non-negative number.");
        }

        const n = this.graph.size;
        let result = Array.from({ length: n }, () => complex(0));
        let term = Array.from({ length: n }, () => complex(0));
        term[start] = complex(1);

        for (let i = 0; i < n; i++) {
            result[i] = term[i];
        }

        for (let k = 1; k < 80; k++) {
            const product = Array.from({ length: n }, () => complex(0));

            for (let i = 0; i < n; i++) {
                for (let j = 0; j < n; j++) {
                    if (this.graph.adjacency[i][j]) {
                        product[i] = add(product[i], term[j]);
                    }
                }
            }

            const factor = complex(0, -time / k);

            term = product.map(value => multiply(factor, value));

            for (let i = 0; i < n; i++) {
                result[i] = add(result[i], term[i]);
            }

            const largest = Math.max(...term.map(
                value => Math.sqrt(magnitudeSquared(value))
            ));

            if (largest < 1e-14) {
                break;
            }
        }

        return normalize(result).map(magnitudeSquared);
    }

    measure(probabilities) {
        if (!Array.isArray(probabilities) || probabilities.length === 0) {
            throw new Error("A non-empty probability vector is required.");
        }

        const total = probabilities.reduce((sum, p) => sum + p, 0);
        if (Math.abs(total - 1) > 1e-8) {
            throw new Error(`Invalid probability normalization: ${total}`);
        }

        const randomValue = Math.random();
        let cumulative = 0;

        for (let i = 0; i < probabilities.length; i++) {
            cumulative += probabilities[i];
            if (randomValue <= cumulative) {
                this.measurementCount++;
                this.emit("measurement", {
                    vertex: i,
                    measurementNumber: this.measurementCount
                });
                return i;
            }
        }

        return probabilities.length - 1;
    }
}

async function main() {
    const graph = new Graph([
        [0, 1, 0, 1],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 1, 0]
    ]);

    const engine = new QuantumWalkEngine(graph);

    engine.on("step", event => {
        if (event.step <= 3) {
            console.log(`completed quantum step ${event.step}`);
        }
    });

    engine.on("measurement", event => {
        console.log(
            `measurement ${event.measurementNumber}: vertex ${event.vertex}`
        );
    });

    const discrete = await engine.runCoinedLineWalk(8);

    console.log("\nDiscrete quantum walk:");
    for (const [position, probability] of discrete) {
        console.log(`position ${position}: ${probability.toFixed(8)}`);
    }

    const continuous = engine.continuousTimeProbability(0, 1.5);

    console.log("\nContinuous-time quantum walk:");
    continuous.forEach((probability, vertex) => {
        console.log(`vertex ${vertex}: ${probability.toFixed(8)}`);
    });

    const measuredVertex = engine.measure(continuous);
    console.log(`\nSampled measurement result: vertex ${measuredVertex}`);

    const total = continuous.reduce((sum, p) => sum + p, 0);
    if (Math.abs(total - 1) > 1e-8) {
        throw new Error("Probability conservation check failed.");
    }

    // Input validation also protects downstream policy code from malformed data.
    try {
        new Graph([[0, 1], [0, 0]]);
    } catch (error) {
        console.log(`\nValidation test passed: ${error.message}`);
    }
}

main().catch(error => {
    console.error(`Quantum walk execution failed: ${error.message}`);
    process.exitCode = 1;
});"use strict";

const { EventEmitter } = require("node:events");

class Graph {
    constructor(adjacency) {
        if (!Array.isArray(adjacency) || adjacency.length === 0) {
            throw new Error("Graph must contain at least one vertex.");
        }

        const n = adjacency.length;

        for (const row of adjacency) {
            if (!Array.isArray(row) || row.length !== n) {
                throw new Error("Adjacency matrix must be square.");
            }
            if (row.some(value => value !== 0 && value !== 1)) {
                throw new Error("Adjacency values must be 0 or 1.");
            }
        }

        for (let i = 0; i < n; i++) {
            if (adjacency[i][i] !== 0) {
                throw new Error("Self-loops are not supported.");
            }
            for (let j = 0; j < n; j++) {
                if (adjacency[i][j] !== adjacency[j][i]) {
                    throw new Error("Graph must be undirected.");
                }
            }
        }

        this.adjacency = adjacency.map(row => [...row]);
    }

    get size() {
        return this.adjacency.length;
    }

    neighbors(vertex) {
        this.validateVertex(vertex);
        return this.adjacency[vertex]
            .map((connected, index) => connected ? index : -1)
            .filter(index => index >= 0);
    }

    validateVertex(vertex) {
        if (!Number.isInteger(vertex) || vertex < 0 || vertex >= this.size) {
            throw new RangeError(`Invalid vertex: ${vertex}`);
        }
    }
}

function complex(re, im = 0) {
    return { re, im };
}

function add(a, b) {
    return complex(a.re + b.re, a.im + b.im);
}

function multiply(a, b) {
    return complex(
        a.re * b.re - a.im * b.im,
        a.re * b.im + a.im * b.re
    );
}

function scale(a, value) {
    return complex(a.re * value, a.im * value);
}

function magnitudeSquared(a) {
    return a.re * a.re + a.im * a.im;
}

function normalize(state) {
    const norm = Math.sqrt(
        state.reduce((sum, amplitude) => sum + magnitudeSquared(amplitude), 0)
    );

    if (norm === 0) {
        throw new Error("Cannot normalize a zero state.");
    }

    return state.map(amplitude => scale(amplitude, 1 / norm));
}

function hadamard(a, b) {
    const factor = 1 / Math.sqrt(2);
    return [
        scale(add(a, b), factor),
        scale(add(a, scale(b, -1)), factor)
    ];
}

class QuantumWalkEngine extends EventEmitter {
    constructor(graph) {
        super();
        this.graph = graph;
        this.measurementCount = 0;
    }

    async runCoinedLineWalk(steps, initialCoin = [
        complex(1 / Math.sqrt(2)),
        complex(0, 1 / Math.sqrt(2))
    ]) {
        if (!Number.isInteger(steps) || steps < 0) {
            throw new Error("steps must be a non-negative integer.");
        }

        if (initialCoin.length !== 2) {
            throw new Error("A two-state coin is required.");
        }

        let state = new Map([
            ["0:0", initialCoin[0]],
            ["0:1", initialCoin[1]]
        ]);

        for (let step = 0; step < steps; step++) {
            const afterCoin = new Map();

            for (const [key, amplitude] of state) {
                const [position] = key.split(":").map(Number);
                const left = state.get(`${position}:0`) || complex(0);
                const right = state.get(`${position}:1`) || complex(0);
                const [newLeft, newRight] = hadamard(left, right);

                afterCoin.set(`${position}:0`, newLeft);
                afterCoin.set(`${position}:1`, newRight);
            }

            const next = new Map();

            for (const [key, amplitude] of afterCoin) {
                const [position, coin] = key.split(":").map(Number);
                const destination = coin === 0 ? position - 1 : position + 1;
                const destinationKey = `${destination}:${coin}`;
                const current = next.get(destinationKey) || complex(0);
                next.set(destinationKey, add(current, amplitude));
            }

            state = next;
            this.emit("step", { step: step + 1, states: state.size });

            // Yield to the event loop so the engine can participate in
            // larger asynchronous workflows without blocking observers.
            await new Promise(resolve => setImmediate(resolve));
        }

        const probabilities = new Map();

        for (const [key, amplitude] of state) {
            const [position] = key.split(":").map(Number);
            const probability = magnitudeSquared(amplitude);
            probabilities.set(
                position,
                (probabilities.get(position) || 0) + probability
            );
        }

        return new Map([...probabilities.entries()].sort((a, b) => a[0] - b[0]));
    }

    continuousTimeProbability(start, time) {
        this.graph.validateVertex(start);

        if (typeof time !== "number" || !Number.isFinite(time) || time < 0) {
            throw new Error("time must be a finite non-negative number.");
        }

        const n = this.graph.size;
        let result = Array.from({ length: n }, () => complex(0));
        let term = Array.from({ length: n }, () => complex(0));
        term[start] = complex(1);

        for (let i = 0; i < n; i++) {
            result[i] = term[i];
        }

        for (let k = 1; k < 80; k++) {
            const product = Array.from({ length: n }, () => complex(0));

            for (let i = 0; i < n; i++) {
                for (let j = 0; j < n; j++) {
                    if (this.graph.adjacency[i][j]) {
                        product[i] = add(product[i], term[j]);
                    }
                }
            }

            const factor = complex(0, -time / k);

            term = product.map(value => multiply(factor, value));

            for (let i = 0; i < n; i++) {
                result[i] = add(result[i], term[i]);
            }

            const largest = Math.max(...term.map(
                value => Math.sqrt(magnitudeSquared(value))
            ));

            if (largest < 1e-14) {
                break;
            }
        }

        return normalize(result).map(magnitudeSquared);
    }

    measure(probabilities) {
        if (!Array.isArray(probabilities) || probabilities.length === 0) {
            throw new Error("A non-empty probability vector is required.");
        }

        const total = probabilities.reduce((sum, p) => sum + p, 0);
        if (Math.abs(total - 1) > 1e-8) {
            throw new Error(`Invalid probability normalization: ${total}`);
        }

        const randomValue = Math.random();
        let cumulative = 0;

        for (let i = 0; i < probabilities.length; i++) {
            cumulative += probabilities[i];
            if (randomValue <= cumulative) {
                this.measurementCount++;
                this.emit("measurement", {
                    vertex: i,
                    measurementNumber: this.measurementCount
                });
                return i;
            }
        }

        return probabilities.length - 1;
    }
}

async function main() {
    const graph = new Graph([
        [0, 1, 0, 1],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 1, 0]
    ]);

    const engine = new QuantumWalkEngine(graph);

    engine.on("step", event => {
        if (event.step <= 3) {
            console.log(`completed quantum step ${event.step}`);
        }
    });

    engine.on("measurement", event => {
        console.log(
            `measurement ${event.measurementNumber}: vertex ${event.vertex}`
        );
    });

    const discrete = await engine.runCoinedLineWalk(8);

    console.log("\nDiscrete quantum walk:");
    for (const [position, probability] of discrete) {
        console.log(`position ${position}: ${probability.toFixed(8)}`);
    }

    const continuous = engine.continuousTimeProbability(0, 1.5);

    console.log("\nContinuous-time quantum walk:");
    continuous.forEach((probability, vertex) => {
        console.log(`vertex ${vertex}: ${probability.toFixed(8)}`);
    });

    const measuredVertex = engine.measure(continuous);
    console.log(`\nSampled measurement result: vertex ${measuredVertex}`);

    const total = continuous.reduce((sum, p) => sum + p, 0);
    if (Math.abs(total - 1) > 1e-8) {
        throw new Error("Probability conservation check failed.");
    }

    // Input validation also protects downstream policy code from malformed data.
    try {
        new Graph([[0, 1], [0, 0]]);
    } catch (error) {
        console.log(`\nValidation test passed: ${error.message}`);
    }
}

main().catch(error => {
    console.error(`Quantum walk execution failed: ${error.message}`);
    process.exitCode = 1;
});
