'use strict';

/**
 * Grover's quantum search algorithm.
 * Run with Node.js 18 or later: node grover_search.js
 *
 * This small state-vector simulator uses real amplitudes because the
 * standard Grover circuit here only needs real Hadamard, phase, and
 * diffusion operations. General quantum circuits may require complex values.
 */

class QuantumSearchError extends Error {}

class GroverSearch {
    constructor(qubits, markedStates) {
        if (!Number.isInteger(qubits) || qubits < 1 || qubits > 20) {
            throw new QuantumSearchError(
                'Qubit count must be an integer between 1 and 20.'
            );
        }
        if (!Array.isArray(markedStates) || markedStates.length === 0) {
            throw new QuantumSearchError(
                'At least one marked state is required.'
            );
        }

        this.qubits = qubits;
        this.size = 2 ** qubits;
        this.markedStates = [...new Set(markedStates)].sort((a, b) => a - b);

        for (const state of this.markedStates) {
            if (
                !Number.isInteger(state) ||
                state < 0 ||
                state >= this.size
            ) {
                throw new QuantumSearchError(
                    `Marked states must be integers from 0 to ${this.size - 1}.`
                );
            }
        }

        this.markedSet = new Set(this.markedStates);
    }

    get optimalIterations() {
        const n = this.size;
        const m = this.markedStates.length;

        if (m === n) return 0;

        const theta = Math.asin(Math.sqrt(m / n));
        return Math.max(0, Math.floor(Math.PI / (4 * theta) - 0.5));
    }

    run(iterations = this.optimalIterations) {
        if (!Number.isSafeInteger(iterations) || iterations < 0) {
            throw new QuantumSearchError(
                'Iterations must be a nonnegative safe integer.'
            );
        }

        const amplitudes = new Float64Array(this.size);
        amplitudes.fill(1 / Math.sqrt(this.size));

        for (let step = 0; step < iterations; step++) {
            // Oracle: reverse the phase of every marked basis state.
            for (const state of this.markedStates) {
                amplitudes[state] = -amplitudes[state];
            }

            // Diffusion: reflect all amplitudes around their mean.
            let sum = 0;
            for (const amplitude of amplitudes) sum += amplitude;
            const twiceMean = (2 * sum) / this.size;

            for (let state = 0; state < this.size; state++) {
                amplitudes[state] = twiceMean - amplitudes[state];
            }
        }

        const probabilities = Array.from(
            amplitudes,
            amplitude => amplitude * amplitude
        );

        let norm = 0;
        let successProbability = 0;
        let measuredState = 0;

        for (let state = 0; state < this.size; state++) {
            const probability = probabilities[state];
            norm += probability;

            if (this.markedSet.has(state)) {
                successProbability += probability;
            }

            if (probability > probabilities[measuredState]) {
                measuredState = state;
            }
        }

        if (Math.abs(norm - 1) > 1e-10) {
            throw new Error(`State normalization failed: ${norm}`);
        }

        return Object.freeze({
            qubits: this.qubits,
            markedStates: [...this.markedStates],
            iterations,
            probabilities,
            successProbability,
            mostProbableState: measuredState,
            oracleQueries: iterations
        });
    }
}

/**
 * Event-driven policy evaluation separates a proposed search from its
 * result. The event log records decisions without modifying past events.
 */
class SearchCoordinator {
    constructor() {
        this.listeners = new Map();
        this.events = [];
    }

    on(eventName, listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function.');
        }
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }
        this.listeners.get(eventName).add(listener);
        return () => this.listeners.get(eventName).delete(listener);
    }

    async emit(eventName, payload) {
        this.events.push(Object.freeze({
            eventName,
            timestamp: new Date().toISOString(),
            payload
        }));

        const listeners = [...(this.listeners.get(eventName) ?? [])];
        await Promise.all(listeners.map(listener => listener(payload)));
    }

    async search(qubits, markedStates) {
        const request = Object.freeze({
            qubits,
            markedStates: [...markedStates]
        });

        await this.emit('search.started', request);

        try {
            const engine = new GroverSearch(qubits, markedStates);
            const result = engine.run();

            await this.emit('search.completed', result);
            return result;
        } catch (error) {
            await this.emit('search.failed', {
                message: error.message
            });
            throw error;
        }
    }
}

async function main() {
    const coordinator = new SearchCoordinator();

    coordinator.on('search.started', request => {
        console.log(
            `Starting search with ${request.qubits} qubits.`
        );
    });

    coordinator.on('search.completed', result => {
        console.log(
            `Completed in ${result.iterations} iterations; ` +
            `success probability ${result.successProbability.toFixed(6)}.`
        );
    });

    coordinator.on('search.failed', failure => {
        console.error(`Search rejected: ${failure.message}`);
    });

    const result = await coordinator.search(4, [5]);

    console.log('\nState probabilities:');
    result.probabilities.forEach((probability, state) => {
        console.log(
            `${state.toString(2).padStart(result.qubits, '0')}: ` +
            probability.toFixed(6)
        );
    });

    if (result.mostProbableState !== 5) {
        throw new Error('Expected marked state 5 to be most probable.');
    }

    if (Math.abs(result.probabilities.reduce((a, b) => a + b, 0) - 1) > 1e-10) {
        throw new Error('Probabilities do not sum to one.');
    }

    // An unsubscribe function prevents unnecessary event processing.
    const unsubscribe = coordinator.on('audit', event => {
        console.log('Audit event:', event);
    });
    unsubscribe();

    console.log(`\nRecorded events: ${coordinator.events.length}`);
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
