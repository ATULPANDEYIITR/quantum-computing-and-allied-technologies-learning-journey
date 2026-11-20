"use strict";

/*
 * QAOA MaxCut implementation.
 * Exact statevector simulation with asynchronous parameter evaluation.
 * Runtime: Node.js 18+
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");

class ValidationError extends Error {}
class SimulationError extends Error {}

class WeightedGraph {
    constructor(vertexCount, edges) {
        if (!Number.isInteger(vertexCount) ||
            vertexCount < 2 || vertexCount > 20) {
            throw new ValidationError("Invalid vertex count.");
        }

        if (!Array.isArray(edges) || edges.length === 0) {
            throw new ValidationError("Graph requires edges.");
        }

        this.vertexCount = vertexCount;
        this.edges = Object.freeze(edges.map(edge => {
            const { u, v, weight = 1 } = edge;

            if (!Number.isInteger(u) || !Number.isInteger(v) ||
                u < 0 || v < 0 ||
                u >= vertexCount || v >= vertexCount ||
                u === v) {
                throw new ValidationError("Invalid edge endpoints.");
            }

            if (!Number.isFinite(weight) || weight <= 0) {
                throw new ValidationError("Invalid edge weight.");
            }

            return Object.freeze({ u, v, weight });
        }));
    }

    cutValue(mask) {
        let total = 0;

        for (const edge of this.edges) {
            const a = (mask >> BigInt(edge.u)) & 1n;
            const b = (mask >> BigInt(edge.v)) & 1n;

            if (a !== b) total += edge.weight;
        }

        return total;
    }

    classicalOptimum() {
        const limit = 1n << BigInt(this.vertexCount);
        let best = -Infinity;
        let bestMask = 0n;

        // Complementary assignments have identical cut values.
        for (let mask = 0n; mask < limit / 2n; mask++) {
            const value = this.cutValue(mask);

            if (value > best) {
                best = value;
                bestMask = mask;
            }
        }

        return { value: best, mask: bestMask };
    }

    formatMask(mask) {
        return Array.from(
            { length: this.vertexCount },
            (_, i) => Number((mask >> BigInt(i)) & 1n)
        ).join("");
    }
}

class ComplexState {
    constructor(size) {
        this.real = new Float64Array(size);
        this.imag = new Float64Array(size);
    }

    get size() {
        return this.real.length;
    }

    norm() {
        let sum = 0;

        for (let i = 0; i < this.size; i++) {
            sum += this.real[i] ** 2 + this.imag[i] ** 2;
        }

        return sum;
    }
}

class QAOASimulator {
    constructor(graph) {
        this.graph = graph;
        this.n = graph.vertexCount;
        this.dimension = 2 ** this.n;

        if (!Number.isSafeInteger(this.dimension)) {
            throw new SimulationError("Statevector is too large.");
        }
    }

    initialState() {
        const state = new ComplexState(this.dimension);
        const amplitude = 1 / Math.sqrt(this.dimension);

        state.real.fill(amplitude);
        return state;
    }

    applyCost(state, gamma) {
        for (let mask = 0; mask < this.dimension; mask++) {
            const cost = this.graph.cutValue(BigInt(mask));
            const angle = -gamma * cost;

            const oldReal = state.real[mask];
            const oldImag = state.imag[mask];

            state.real[mask] =
                oldReal * Math.cos(angle) -
                oldImag * Math.sin(angle);

            state.imag[mask] =
                oldReal * Math.sin(angle) +
                oldImag * Math.cos(angle);
        }
    }

    applyMixer(state, beta) {
        const cosine = Math.cos(beta);
        const sine = Math.sin(beta);

        for (let qubit = 0; qubit < this.n; qubit++) {
            const mask = 1 << qubit;

            for (let i = 0; i < this.dimension; i++) {
                if ((i & mask) !== 0) continue;

                const j = i | mask;

                const ar = state.real[i];
                const ai = state.imag[i];
                const br = state.real[j];
                const bi = state.imag[j];

                // exp(-i beta X) = cos(beta)I - i sin(beta)X.
                state.real[i] = cosine * ar + sine * bi;
                state.imag[i] = cosine * ai - sine * br;

                state.real[j] = cosine * br + sine * ai;
                state.imag[j] = cosine * bi - sine * ar;
            }
        }
    }

    execute(gamma, beta) {
        if (!Number.isFinite(gamma) || !Number.isFinite(beta)) {
            throw new ValidationError("Parameters must be finite.");
        }

        const state = this.initialState();
        this.applyCost(state, gamma);
        this.applyMixer(state, beta);

        const norm = state.norm();

        if (Math.abs(norm - 1) > 1e-9) {
            throw new SimulationError(
                `State normalization failure: ${norm}`
            );
        }

        return state;
    }

    expectedCut(state) {
        let expected = 0;

        for (let i = 0; i < this.dimension; i++) {
            const probability =
                state.real[i] ** 2 + state.imag[i] ** 2;

            expected += probability *
                this.graph.cutValue(BigInt(i));
        }

        return expected;
    }

    mostProbable(state) {
        let bestIndex = 0;
        let bestProbability = -1;

        for (let i = 0; i < this.dimension; i++) {
            const probability =
                state.real[i] ** 2 + state.imag[i] ** 2;

            if (probability > bestProbability) {
                bestProbability = probability;
                bestIndex = i;
            }
        }

        return {
            bitstring: this.graph.formatMask(BigInt(bestIndex)),
            cut: this.graph.cutValue(BigInt(bestIndex)),
            probability: bestProbability
        };
    }
}

class QAOAExperiment extends EventEmitter {
    constructor(simulator, options = {}) {
        super();

        this.simulator = simulator;
        this.gammaSteps = options.gammaSteps ?? 40;
        this.betaSteps = options.betaSteps ?? 40;

        if (!Number.isInteger(this.gammaSteps) ||
            !Number.isInteger(this.betaSteps) ||
            this.gammaSteps < 2 ||
            this.betaSteps < 2) {
            throw new ValidationError("Invalid search resolution.");
        }

        this.state = "CREATED";
        this.evaluations = 0;
    }

    transition(nextState) {
        const allowed = {
            CREATED: ["RUNNING"],
            RUNNING: ["COMPLETED", "FAILED"],
            COMPLETED: [],
            FAILED: []
        };

        if (!allowed[this.state].includes(nextState)) {
            throw new Error(
                `Invalid transition: ${this.state} -> ${nextState}`
            );
        }

        this.state = nextState;
        this.emit("state", nextState);
    }

    async optimize() {
        this.transition("RUNNING");

        try {
            let best = {
                expected: -Infinity,
                gamma: 0,
                beta: 0,
                state: null
            };

            for (let i = 0; i < this.gammaSteps; i++) {
                const gamma = 2 * Math.PI * i / this.gammaSteps;

                for (let j = 0; j < this.betaSteps; j++) {
                    const beta = Math.PI * j / this.betaSteps;

                    const state = this.simulator.execute(gamma, beta);
                    const expected =
                        this.simulator.expectedCut(state);

                    this.evaluations++;

                    if (expected > best.expected) {
                        best = { expected, gamma, beta, state };
                    }
                }

                // Yield periodically to avoid monopolizing the event loop.
                if (i % 5 === 0) {
                    this.emit("progress", {
                        completed: this.evaluations,
                        total: this.gammaSteps * this.betaSteps
                    });

                    await new Promise(resolve => setImmediate(resolve));
                }
            }

            const observed =
                this.simulator.mostProbable(best.state);

            const classical =
                this.simulator.graph.classicalOptimum();

            const result = {
                status: "COMPLETED",
                gamma: best.gamma,
                beta: best.beta,
                expectedCut: best.expected,
                observedState: observed.bitstring,
                observedCut: observed.cut,
                observedProbability: observed.probability,
                classicalOptimum: classical.value,
                approximationRatio:
                    classical.value > 0
                        ? best.expected / classical.value
                        : 0,
                evaluations: this.evaluations
            };

            this.transition("COMPLETED");
            this.emit("completed", result);

            return Object.freeze(result);
        } catch (error) {
            this.transition("FAILED");
            this.emit("error", error);
            throw error;
        }
    }
}

async function main() {
    const graph = new WeightedGraph(6, [
        { u: 0, v: 1 },
        { u: 0, v: 2 },
        { u: 1, v: 2 },
        { u: 1, v: 3 },
        { u: 2, v: 4 },
        { u: 3, v: 4 },
        { u: 3, v: 5 },
        { u: 4, v: 5 },
        { u: 0, v: 5 }
    ]);

    const simulator = new QAOASimulator(graph);

    const experiment = new QAOAExperiment(simulator, {
        gammaSteps: 40,
        betaSteps: 40
    });

    experiment.on("state", state => {
        process.stdout.write(`Experiment state: ${state}\n`);
    });

    experiment.on("progress", progress => {
        process.stdout.write(
            `Evaluations: ${progress.completed}/${progress.total}\n`
        );
    });

    experiment.on("completed", result => {
        process.stdout.write(
            `Optimization completed: ${result.expectedCut.toFixed(6)}\n`
        );
    });

    const result = await experiment.optimize();

    console.log("\nQAOA MAX-CUT RESULTS");
    console.log("====================");
    console.log(JSON.stringify(result, null, 2));

    // Atomic-style replacement avoids exposing a partially written result.
    const temporary = "qaoa_result.json.tmp";

    try {
        await fs.writeFile(
            temporary,
            JSON.stringify(result, null, 2),
            { encoding: "utf8", mode: 0o600 }
        );

        await fs.rename(temporary, "qaoa_result.json");
    } catch (error) {
        await fs.rm(temporary, { force: true });
        throw error;
    }
}

main().catch(error => {
    console.error("QAOA execution failed:", error.message);
    process.exitCode = 1;
});
