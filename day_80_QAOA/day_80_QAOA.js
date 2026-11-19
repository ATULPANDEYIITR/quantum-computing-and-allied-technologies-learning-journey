'use strict';

/*
 * Quantum Approximate Optimization Algorithm (QAOA)
 *
 * Event-driven QAOA experiment runner for weighted Max-Cut.
 *
 * Engineering features:
 * - Graph modeling and validation.
 * - Parameterized statevector simulation.
 * - Cost and mixer Hamiltonians.
 * - Asynchronous experiment execution.
 * - Event-driven experiment lifecycle.
 * - Parameter optimization.
 * - Shot-based measurement.
 * - Cancellation and failure handling.
 * - Experiment result tracking.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const { EventEmitter } = require('node:events');
const crypto = require('node:crypto');

const EPSILON = 1e-10;
const MAX_QUBITS = 18;

class QAOAError extends Error {
    constructor(message) {
        super(message);
        this.name = 'QAOAError';
    }
}

class Graph {
    constructor(vertexCount, edges) {
        if (
            !Number.isInteger(vertexCount) ||
            vertexCount < 1 ||
            vertexCount > MAX_QUBITS
        ) {
            throw new QAOAError(
                `Vertex count must be between 1 and ${MAX_QUBITS}.`
            );
        }

        if (!Array.isArray(edges)) {
            throw new QAOAError('Edges must be an array.');
        }

        const seen = new Set();

        this.vertexCount = vertexCount;

        this.edges = edges.map(edge => {
            const { u, v, weight = 1 } = edge;

            if (
                !Number.isInteger(u) ||
                !Number.isInteger(v) ||
                u < 0 ||
                v < 0 ||
                u >= vertexCount ||
                v >= vertexCount ||
                u === v
            ) {
                throw new QAOAError('Invalid graph edge.');
            }

            if (!Number.isFinite(weight) || weight <= 0) {
                throw new QAOAError(
                    'Edge weight must be positive and finite.'
                );
            }

            const key = `${Math.min(u, v)}:${Math.max(u, v)}`;

            if (seen.has(key)) {
                throw new QAOAError('Duplicate edge detected.');
            }

            seen.add(key);

            return Object.freeze({ u, v, weight });
        });

        Object.freeze(this.edges);
    }

    cutValue(bits) {
        if (
            typeof bits !== 'string' ||
            bits.length !== this.vertexCount ||
            !/^[01]+$/.test(bits)
        ) {
            throw new QAOAError('Invalid bitstring.');
        }

        return this.edges.reduce(
            (total, edge) => {
                return bits[edge.u] !== bits[edge.v]
                    ? total + edge.weight
                    : total;
            },
            0
        );
    }

    enumerateOptimum() {
        let best = -Infinity;
        const solutions = [];

        for (let state = 0; state < 2 ** this.vertexCount; state++) {
            const bits = state
                .toString(2)
                .padStart(this.vertexCount, '0');

            const value = this.cutValue(bits);

            if (value > best + EPSILON) {
                best = value;
                solutions.length = 0;
                solutions.push(bits);
            } else if (Math.abs(value - best) <= EPSILON) {
                solutions.push(bits);
            }
        }

        return { value: best, solutions };
    }
}

class StateVector {
    constructor(qubitCount) {
        this.qubitCount = qubitCount;
        this.size = 2 ** qubitCount;
        this.amplitudes = new Array(this.size).fill(0);

        const amplitude = 1 / Math.sqrt(this.size);

        this.amplitudes.fill({
            re: amplitude,
            im: 0
        });
    }

    applyCost(graph, gamma) {
        for (let state = 0; state < this.size; state++) {
            const bits = state
                .toString(2)
                .padStart(this.qubitCount, '0');

            const phase = -gamma * graph.cutValue(bits);
            const cosine = Math.cos(phase);
            const sine = Math.sin(phase);

            const amplitude = this.amplitudes[state];

            this.amplitudes[state] = {
                re: amplitude.re * cosine - amplitude.im * sine,
                im: amplitude.re * sine + amplitude.im * cosine
            };
        }
    }

    applyMixer(beta) {
        const cosine = Math.cos(beta);
        const sine = Math.sin(beta);

        for (let qubit = 0; qubit < this.qubitCount; qubit++) {
            const mask = 1 << qubit;

            for (let state = 0; state < this.size; state++) {
                if ((state & mask) !== 0) continue;

                const partner = state | mask;

                const a = this.amplitudes[state];
                const b = this.amplitudes[partner];

                this.amplitudes[state] = {
                    re: cosine * a.re + sine * b.im,
                    im: cosine * a.im - sine * b.re
                };

                this.amplitudes[partner] = {
                    re: cosine * b.re + sine * a.im,
                    im: cosine * b.im - sine * a.re
                };
            }
        }
    }

    probabilities() {
        return this.amplitudes.map(
            amplitude =>
                amplitude.re ** 2 + amplitude.im ** 2
        );
    }

    validate() {
        const total = this.probabilities().reduce(
            (sum, probability) => sum + probability,
            0
        );

        if (Math.abs(total - 1) > 1e-8) {
            throw new QAOAError(
                `Statevector normalization failed: ${total}`
            );
        }
    }
}

class QAOACircuit {
    constructor(graph, depth = 1) {
        if (
            !Number.isInteger(depth) ||
            depth < 1 ||
            depth > 8
        ) {
            throw new QAOAError('Invalid circuit depth.');
        }

        this.graph = graph;
        this.depth = depth;
    }

    validateParameters(gamma, beta) {
        if (
            !Array.isArray(gamma) ||
            !Array.isArray(beta) ||
            gamma.length !== this.depth ||
            beta.length !== this.depth
        ) {
            throw new QAOAError('Invalid parameter dimensions.');
        }

        if (
            [...gamma, ...beta].some(
                value => !Number.isFinite(value)
            )
        ) {
            throw new QAOAError('Parameters must be finite.');
        }
    }

    simulate(gamma, beta) {
        this.validateParameters(gamma, beta);

        const state = new StateVector(
            this.graph.vertexCount
        );

        for (let layer = 0; layer < this.depth; layer++) {
            state.applyCost(this.graph, gamma[layer]);
            state.applyMixer(beta[layer]);
        }

        state.validate();
        return state;
    }

    expectation(gamma, beta) {
        const state = this.simulate(gamma, beta);
        const probabilities = state.probabilities();

        return probabilities.reduce(
            (expected, probability, index) => {
                const bits = index
                    .toString(2)
                    .padStart(this.graph.vertexCount, '0');

                return expected +
                    probability * this.graph.cutValue(bits);
            },
            0
        );
    }

    optimize({
        iterations = 100,
        initialGamma = [0.7],
        initialBeta = [0.3],
        stepSize = 0.15
    } = {}) {
        if (
            !Number.isInteger(iterations) ||
            iterations < 1 ||
            !Number.isFinite(stepSize) ||
            stepSize <= 0
        ) {
            throw new QAOAError('Invalid optimizer configuration.');
        }

        let gamma = [...initialGamma];
        let beta = [...initialBeta];

        this.validateParameters(gamma, beta);

        let best = this.expectation(gamma, beta);
        const history = [best];

        for (let iteration = 0; iteration < iterations; iteration++) {
            let improved = false;

            for (const [parameters, maximum] of [
                [gamma, Math.PI],
                [beta, Math.PI / 2]
            ]) {
                for (let index = 0; index < this.depth; index++) {
                    const original = parameters[index];
                    let candidateBest = original;
                    let localBest = best;

                    for (const direction of [-1, 1]) {
                        parameters[index] = Math.max(
                            0,
                            Math.min(
                                maximum,
                                original + direction * stepSize
                            )
                        );

                        const value = this.expectation(gamma, beta);

                        if (value > localBest + EPSILON) {
                            localBest = value;
                            candidateBest = parameters[index];
                        }
                    }

                    parameters[index] = candidateBest;

                    if (localBest > best + EPSILON) {
                        best = localBest;
                        improved = true;
                    }
                }
            }

            history.push(best);

            if (!improved) stepSize *= 0.5;
            if (stepSize < 1e-5) break;
        }

        return Object.freeze({
            gamma: Object.freeze(gamma),
            beta: Object.freeze(beta),
            expectation: best,
            history: Object.freeze(history),
            iterations: history.length - 1
        });
    }

    sample(gamma, beta, shots = 1000, seed = 42) {
        if (
            !Number.isInteger(shots) ||
            shots < 1 ||
            shots > 1000000
        ) {
            throw new QAOAError('Invalid shot count.');
        }

        const state = this.simulate(gamma, beta);
        const probabilities = state.probabilities();

        const cumulative = [];
        let total = 0;

        for (const probability of probabilities) {
            total += probability;
            cumulative.push(total);
        }

        // Deterministic pseudorandom generator for reproducible tests.
        let randomState = seed >>> 0;

        const random = () => {
            randomState = (
                1664525 * randomState + 1013904223
            ) >>> 0;

            return randomState / 4294967296;
        };

        const counts = new Map();

        for (let shot = 0; shot < shots; shot++) {
            const target = random();
            let low = 0;
            let high = cumulative.length - 1;

            while (low < high) {
                const middle = Math.floor((low + high) / 2);

                if (target <= cumulative[middle]) {
                    high = middle;
                } else {
                    low = middle + 1;
                }
            }

            const bits = low
                .toString(2)
                .padStart(this.graph.vertexCount, '0');

            counts.set(bits, (counts.get(bits) || 0) + 1);
        }

        return counts;
    }
}

class ExperimentRunner extends EventEmitter {
    constructor(circuit) {
        super();

        this.circuit = circuit;
        this.experiments = new Map();
        this.active = new Set();
    }

    async run(configuration = {}) {
        const id = crypto.randomUUID();

        const experiment = {
            id,
            status: 'QUEUED',
            createdAt: new Date().toISOString(),
            result: null,
            error: null
        };

        this.experiments.set(id, experiment);
        this.active.add(id);

        this.emit('queued', { id });

        try {
            experiment.status = 'RUNNING';
            this.emit('started', { id });

            // Yield control so event consumers can process lifecycle events.
            await new Promise(resolve => setImmediate(resolve));

            const result = this.circuit.optimize(configuration);

            if (!this.active.has(id)) {
                experiment.status = 'CANCELLED';
                this.emit('cancelled', { id });
                return experiment;
            }

            const samples = this.circuit.sample(
                result.gamma,
                result.beta,
                configuration.shots ?? 1000
            );

            const optimum = this.circuit.graph.enumerateOptimum();

            const experimentResult = {
                ...result,
                optimum: optimum.value,
                approximationRatio:
                    optimum.value > 0
                        ? result.expectation / optimum.value
                        : 1,
                samples: Object.fromEntries(samples)
            };

            experiment.result = Object.freeze(experimentResult);
            experiment.status = 'COMPLETED';

            this.emit('completed', {
                id,
                result: experiment.result
            });

        } catch (error) {
            experiment.status = 'FAILED';
            experiment.error = error.message;

            this.emit('failed', {
                id,
                error: error.message
            });

        } finally {
            this.active.delete(id);
        }

        return Object.freeze({ ...experiment });
    }

    cancel(id) {
        if (!this.active.has(id)) {
            return false;
        }

        this.active.delete(id);
        this.emit('cancellation-requested', { id });
        return true;
    }

    getExperiment(id) {
        const experiment = this.experiments.get(id);

        if (!experiment) {
            throw new QAOAError('Experiment not found.');
        }

        return Object.freeze({ ...experiment });
    }
}

async function main() {
    const graph = new Graph(4, [
        { u: 0, v: 1 },
        { u: 0, v: 2 },
        { u: 1, v: 2 },
        { u: 1, v: 3 },
        { u: 2, v: 3 }
    ]);

    const circuit = new QAOACircuit(graph, 1);
    const runner = new ExperimentRunner(circuit);

    runner.on('queued', ({ id }) => {
        console.log(`Experiment queued: ${id}`);
    });

    runner.on('started', ({ id }) => {
        console.log(`Experiment started: ${id}`);
    });

    runner.on('completed', ({ id, result }) => {
        console.log(`Experiment completed: ${id}`);
        console.log(
            `Expected cut: ${result.expectation.toFixed(6)}`
        );
        console.log(
            `Approximation ratio: ${result.approximationRatio.toFixed(6)}`
        );
    });

    runner.on('failed', ({ id, error }) => {
        console.error(`Experiment ${id} failed: ${error}`);
    });

    const optimum = graph.enumerateOptimum();

    console.log('Classical optimum:', optimum.value);
    console.log('Optimal assignments:', optimum.solutions);

    const experiment = await runner.run({
        iterations: 100,
        initialGamma: [0.7],
        initialBeta: [0.3],
        stepSize: 0.15,
        shots: 2000
    });

    console.log('\nExperiment status:', experiment.status);

    if (experiment.result) {
        console.log('Measurement counts:');

        console.log(
            Object.entries(experiment.result.samples)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8)
        );
    }

    if (experiment.status !== 'COMPLETED') {
        process.exitCode = 1;
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error(error);
        process.exitCode = 1;
    });
}

module.exports = {
    Graph,
    StateVector,
    QAOACircuit,
    ExperimentRunner,
    QAOAError
};
