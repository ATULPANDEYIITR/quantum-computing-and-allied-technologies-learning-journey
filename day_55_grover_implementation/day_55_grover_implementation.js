"use strict";

/**
 * Grover search simulator using JavaScript state vectors.
 * Run with Node.js 18 or later.
 */

const { randomInt } = require("node:crypto");

class GroverSearch {
  constructor(qubits, seed = 17) {
    if (!Number.isInteger(qubits) || qubits < 1 || qubits > 20) {
      throw new RangeError("Qubits must be an integer from 1 through 20.");
    }
    if (!Number.isInteger(seed)) {
      throw new TypeError("Seed must be an integer.");
    }

    this.qubits = qubits;
    this.size = 2 ** qubits;
    this.seed = seed;
    this.amplitudes = new Float64Array(this.size);
    this.initialize();
  }

  initialize() {
    this.amplitudes.fill(1 / Math.sqrt(this.size));
  }

  static optimalIterations(size, markedCount) {
    if (!Number.isInteger(markedCount) ||
        markedCount < 0 || markedCount > size) {
      throw new RangeError("Invalid number of marked states.");
    }
    if (markedCount === 0 || markedCount === size) return 0;

    const theta = Math.asin(Math.sqrt(markedCount / size));
    return Math.max(0, Math.round(Math.PI / (4 * theta) - 0.5));
  }

  validateMarked(markedStates) {
    if (!(markedStates instanceof Set) || markedStates.size === 0) {
      throw new TypeError("markedStates must be a nonempty Set.");
    }
    for (const state of markedStates) {
      if (!Number.isInteger(state) ||
          state < 0 || state >= this.size) {
        throw new RangeError(`Invalid marked state: ${state}`);
      }
    }
  }

  applyOracle(markedStates) {
    for (const state of markedStates) {
      this.amplitudes[state] *= -1;
    }
  }

  applyDiffusion() {
    let sum = 0;
    for (const amplitude of this.amplitudes) sum += amplitude;
    const mean = sum / this.size;

    for (let i = 0; i < this.size; i++) {
      this.amplitudes[i] = 2 * mean - this.amplitudes[i];
    }
  }

  successProbability(markedStates) {
    let probability = 0;
    for (const state of markedStates) {
      probability += this.amplitudes[state] ** 2;
    }
    return probability;
  }

  measure() {
    let total = 0;
    for (const amplitude of this.amplitudes) {
      total += amplitude * amplitude;
    }
    if (Math.abs(total - 1) > 1e-8) {
      throw new Error(`State normalization failed: ${total}`);
    }

    // Seeded linear congruential generator for repeatable simulation.
    this.seed = (Math.imul(this.seed, 1664525) + 1013904223) >>> 0;
    const threshold = (this.seed / 4294967296) * total;
    let cumulative = 0;

    for (let i = 0; i < this.size; i++) {
      cumulative += this.amplitudes[i] ** 2;
      if (threshold <= cumulative) return i;
    }
    return this.size - 1;
  }

  search(markedStates, iterations = null) {
    this.validateMarked(markedStates);

    if (iterations === null) {
      iterations = GroverSearch.optimalIterations(
        this.size, markedStates.size
      );
    }
    if (!Number.isInteger(iterations) ||
        iterations < 0 || iterations > 100000) {
      throw new RangeError("Iterations must be an integer from 0 to 100000.");
    }

    this.initialize();
    for (let i = 0; i < iterations; i++) {
      this.applyOracle(markedStates);
      this.applyDiffusion();
    }

    return Object.freeze({
      qubits: this.qubits,
      stateCount: this.size,
      markedStates: [...markedStates].sort((a, b) => a - b),
      iterations,
      successProbability: this.successProbability(markedStates),
      measuredState: this.measure()
    });
  }
}

async function runBatch(qubits, markedStates, trials = 1000) {
  if (!Number.isInteger(trials) || trials < 1 || trials > 100000) {
    throw new RangeError("Trials must be between 1 and 100000.");
  }

  // Bounded, asynchronous batches avoid blocking a larger Node.js workflow.
  let hits = 0;
  const batchSize = 100;
  for (let start = 0; start < trials; start += batchSize) {
    const end = Math.min(start + batchSize, trials);
    for (let seed = start; seed < end; seed++) {
      const result = new GroverSearch(qubits, seed).search(markedStates);
      if (markedStates.has(result.measuredState)) hits++;
    }
    await new Promise(resolve => setImmediate(resolve));
  }

  return { trials, hits, empiricalSuccessRate: hits / trials };
}

async function main() {
  const qubits = 4;
  const markedStates = new Set([11]);

  const result = new GroverSearch(qubits, 42).search(markedStates);
  console.log("Grover search result");
  console.log(JSON.stringify(result, null, 2));

  const statistics = await runBatch(qubits, markedStates);
  console.log("Batch measurement statistics");
  console.log(JSON.stringify(statistics, null, 2));

  if (result.iterations !== 3 || result.successProbability < 0.96) {
    throw new Error("Grover search validation failed.");
  }

  const emptySearch = new GroverSearch(3);
  let rejected = false;
  try {
    emptySearch.search(new Set());
  } catch (error) {
    rejected = error instanceof TypeError;
  }
  if (!rejected) throw new Error("Empty marked set was not rejected.");

  console.log("Validation checks passed.");
}

main().catch(error => {
  console.error(`Execution failed: ${error.message}`);
  process.exitCode = 1;
});
