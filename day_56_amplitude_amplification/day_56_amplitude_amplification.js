'use strict';

/*
 * Generalized amplitude amplification implemented as a two-dimensional
 * rotation model. The implementation focuses on the probability geometry
 * rather than pretending to execute a physical quantum circuit.
 */

class SearchError extends Error {}

class SearchProblem {
    constructor(nQubits, markedStates, targetProbability = 0.99) {
        if (!Number.isInteger(nQubits) || nQubits < 1 || nQubits > 20) {
            throw new SearchError('nQubits must be an integer from 1 through 20.');
        }

        if (!Array.isArray(markedStates) || markedStates.length === 0) {
            throw new SearchError('At least one marked state is required.');
        }

        const dimension = 2 ** nQubits;
        this.markedStates = new Set(markedStates);

        if (this.markedStates.size === 0) {
            throw new SearchError('The oracle must mark at least one state.');
        }

        for (const state of this.markedStates) {
            if (!Number.isSafeInteger(state) || state < 0 || state >= dimension) {
                throw new SearchError(`Invalid marked state: ${state}`);
            }
        }

        if (!(targetProbability > 0 && targetProbability <= 1)) {
            throw new SearchError('targetProbability must be in (0, 1].');
        }

        this.nQubits = nQubits;
        this.dimension = dimension;
        this.targetProbability = targetProbability;
    }

    get markedCount() {
        return this.markedStates.size;
    }

    get initialProbability() {
        return this.markedCount / this.dimension;
    }

    get theta() {
        return Math.asin(Math.sqrt(this.initialProbability));
    }
}

class AmplitudeAmplifier {
    constructor(problem) {
        this.problem = problem;
    }

    probability(iteration) {
        if (!Number.isInteger(iteration) || iteration < 0) {
            throw new SearchError('Iteration must be a non-negative integer.');
        }

        const angle = (2 * iteration + 1) * this.problem.theta;
        return Math.sin(angle) ** 2;
    }

    state(iteration) {
        const angle = (2 * iteration + 1) * this.problem.theta;

        return Object.freeze({
            iteration,
            goodAmplitude: Math.sin(angle),
            badAmplitude: Math.cos(angle),
            successProbability: Math.sin(angle) ** 2
        });
    }

    optimalIterations() {
        const theta = this.problem.theta;
        const estimate = Math.PI / (4 * theta) - 0.5;

        const candidates = new Set([
            Math.max(0, Math.floor(estimate)),
            Math.max(0, Math.floor(estimate) + 1)
        ]);

        let bestIteration = 0;
        let bestProbability = -1;

        for (const candidate of candidates) {
            const probability = this.probability(candidate);

            if (probability > bestProbability) {
                bestProbability = probability;
                bestIteration = candidate;
            }
        }

        return bestIteration;
    }

    firstThresholdIteration() {
        for (let k = 0; k < 10000; k++) {
            if (this.probability(k) >= this.problem.targetProbability) {
                return k;
            }
        }

        throw new SearchError('Threshold was not reached in 10,000 iterations.');
    }

    trajectory(iterations) {
        if (!Number.isInteger(iterations) || iterations < 0) {
            throw new SearchError('iterations must be a non-negative integer.');
        }

        return Array.from(
            { length: iterations + 1 },
            (_, iteration) => this.state(iteration)
        );
    }
}

/*
 * An event-driven wrapper separates the search engine from consumers that
 * might display progress, collect telemetry, or enforce operational policy.
 */
class SearchSession {
    constructor(problem) {
        this.problem = problem;
        this.engine = new AmplitudeAmplifier(problem);
        this.listeners = new Map();
        this.sequence = 0;
    }

    on(eventName, listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('listener must be a function');
        }

        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }

        this.listeners.get(eventName).add(listener);

        return () => this.listeners.get(eventName)?.delete(listener);
    }

    emit(eventName, payload) {
        const listeners = this.listeners.get(eventName) ?? new Set();

        for (const listener of listeners) {
            try {
                listener(payload);
            } catch (error) {
                console.error(`Listener failure for ${eventName}:`, error.message);
            }
        }
    }

    async run(iterations = this.engine.optimalIterations()) {
        const history = [];

        this.emit('started', {
            sessionId: ++this.sequence,
            iterations
        });

        for (const state of this.engine.trajectory(iterations)) {
            history.push(state);

            this.emit('iteration', state);

            // Yield to the event loop so consumers can process telemetry.
            await new Promise(resolve => setImmediate(resolve));
        }

        const result = Object.freeze({
            iterations,
            successProbability: history.at(-1).successProbability,
            history
        });

        this.emit('completed', result);
        return result;
    }
}

function printReport(problem, result) {
    console.log('\nGeneralized Quantum Search');
    console.log('--------------------------');
    console.log(`N = ${problem.dimension}`);
    console.log(`M = ${problem.markedCount}`);
    console.log(`Initial P = ${problem.initialProbability.toFixed(6)}`);
    console.log(`Iterations = ${result.iterations}`);
    console.log(`Final ideal P = ${result.successProbability.toFixed(6)}`);

    console.log('\nIteration trajectory');
    console.log('k\tgood\tbad\tP');

    for (const state of result.history) {
        console.log(
            `${state.iteration}\t` +
            `${state.goodAmplitude.toFixed(6)}\t` +
            `${state.badAmplitude.toFixed(6)}\t` +
            `${state.successProbability.toFixed(6)}`
        );
    }
}

async function main() {
    const problem = new SearchProblem(
        5,
        [3, 11, 17, 29],
        0.90
    );

    const session = new SearchSession(problem);

    session.on('started', ({ sessionId, iterations }) => {
        console.log(`Session ${sessionId} started for ${iterations} iterations.`);
    });

    session.on('iteration', state => {
        if (state.successProbability >= 0.90) {
            console.log(
                `Threshold reached at iteration ${state.iteration}.`
            );
        }
    });

    session.on('completed', result => {
        console.log(
            `Completed with probability ${result.successProbability.toFixed(6)}.`
        );
    });

    const optimal = session.engine.optimalIterations();
    const threshold = session.engine.firstThresholdIteration();

    console.log(`Optimal iteration count: ${optimal}`);
    console.log(`First 90% threshold iteration: ${threshold}`);

    const result = await session.run(optimal);
    printReport(problem, result);

    // Generalized amplification becomes especially useful when M > 1.
    const scaling = [1, 2, 4, 8, 16, 32].map(markedCount => {
        const states = Array.from({ length: markedCount }, (_, i) => i);
        const p = new SearchProblem(10, states);
        const engine = new AmplitudeAmplifier(p);
        const k = engine.optimalIterations();

        return {
            markedCount,
            iterations: k,
            probability: engine.probability(k)
        };
    });

    console.log('\nScaling experiment');
    console.table(scaling);

    // Security and correctness validation.
    const allMarked = new SearchProblem(3, [0, 1, 2, 3, 4, 5, 6, 7]);
    const allMarkedEngine = new AmplitudeAmplifier(allMarked);

    if (allMarkedEngine.optimalIterations() !== 0) {
        throw new SearchError('All-marked search should require zero iterations.');
    }

    if (allMarkedEngine.probability(0) !== 1) {
        throw new SearchError('All-marked search must have probability one.');
    }
}

main().catch(error => {
    console.error(`Search failed: ${error.message}`);
    process.exitCode = 1;
});
