"use strict";

/*
 * Quantum measurement with shots, counts, and probabilities.
 * Run with Node.js 18 or later. No external packages are required.
 *
 * This program models measurement of prepared states in the computational
 * basis. It does not simulate quantum circuit evolution or hardware noise.
 */

const assert = require("node:assert/strict");
const { randomUUID } = require("node:crypto");

function validateDistribution(distribution) {
  if (
    distribution === null ||
    typeof distribution !== "object" ||
    Array.isArray(distribution)
  ) {
    throw new TypeError("Distribution must be an outcome-probability object.");
  }

  const entries = Object.entries(distribution);
  if (entries.length === 0) {
    throw new RangeError("Distribution cannot be empty.");
  }

  const width = entries[0][0].length;
  if (width === 0) {
    throw new RangeError("Outcome labels cannot be empty.");
  }

  let total = 0;
  for (const [outcome, probability] of entries) {
    if (!/^[01]+$/.test(outcome) || outcome.length !== width) {
      throw new RangeError("Outcomes must be equal-width binary strings.");
    }
    if (
      typeof probability !== "number" ||
      !Number.isFinite(probability) ||
      probability < 0
    ) {
      throw new RangeError("Probabilities must be finite and non-negative.");
    }
    total += probability;
  }

  if (Math.abs(total - 1) > 1e-9) {
    throw new RangeError(`Probabilities must sum to one; received ${total}.`);
  }

  return Object.freeze(
    Object.fromEntries(entries.map(([outcome, p]) => [outcome, p / total]))
  );
}

function probabilitiesFromAmplitudes(amplitudes) {
  const weights = {};

  for (const [outcome, amplitude] of Object.entries(amplitudes)) {
    if (!/^[01]+$/.test(outcome)) {
      throw new RangeError(`Invalid basis outcome: ${outcome}`);
    }

    if (
      typeof amplitude !== "number" &&
      (typeof amplitude !== "object" || amplitude === null)
    ) {
      throw new TypeError("Amplitude must be a real number or { re, im }.");
    }

    const re = typeof amplitude === "number" ? amplitude : amplitude.re;
    const im = typeof amplitude === "number" ? 0 : amplitude.im;

    if (!Number.isFinite(re) || !Number.isFinite(im)) {
      throw new RangeError("Amplitudes must be finite.");
    }

    weights[outcome] = re * re + im * im;
  }

  const norm = Object.values(weights).reduce((sum, p) => sum + p, 0);
  if (Object.keys(weights).length === 0 || Math.abs(norm - 1) > 1e-9) {
    throw new RangeError(`Amplitude vector must be normalized; norm=${norm}.`);
  }

  return validateDistribution(weights);
}

// A small deterministic generator makes experiments reproducible.
// It is not a cryptographic random generator.
function seededRandom(seed) {
  let state = seed >>> 0;
  return function next() {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

class MeasurementExperiment {
  constructor(distribution, seed = 12345) {
    this.distribution = validateDistribution(distribution);
    this.outcomes = Object.keys(this.distribution);
    this.cumulative = [];
    let cumulativeProbability = 0;

    for (const outcome of this.outcomes) {
      cumulativeProbability += this.distribution[outcome];
      this.cumulative.push([cumulativeProbability, outcome]);
    }

    // Avoid cumulative floating-point rounding that leaves the final outcome
    // unreachable when a random draw is extremely close to one.
    this.cumulative[this.cumulative.length - 1][0] = 1;
    this.random = seededRandom(seed);
  }

  sampleOne() {
    const draw = this.random();
    for (const [threshold, outcome] of this.cumulative) {
      if (draw < threshold) return outcome;
    }
    return this.outcomes[this.outcomes.length - 1];
  }

  measure(shots) {
    if (!Number.isSafeInteger(shots) || shots <= 0) {
      throw new RangeError("Shots must be a positive safe integer.");
    }

    const counts = Object.fromEntries(this.outcomes.map((outcome) => [outcome, 0]));

    for (let shot = 0; shot < shots; shot++) {
      counts[this.sampleOne()]++;
    }

    const observed = {};
    const standardErrors = {};

    for (const outcome of this.outcomes) {
      const frequency = counts[outcome] / shots;
      observed[outcome] = frequency;
      standardErrors[outcome] = Math.sqrt(
        frequency * (1 - frequency) / shots
      );
    }

    const totalVariationDistance = this.outcomes.reduce(
      (distance, outcome) =>
        distance +
        Math.abs(observed[outcome] - this.distribution[outcome]),
      0
    ) / 2;

    return Object.freeze({
      experimentId: randomUUID(),
      shots,
      counts: Object.freeze(counts),
      theoretical: this.distribution,
      observed: Object.freeze(observed),
      standardErrors: Object.freeze(standardErrors),
      totalVariationDistance,
    });
  }
}

function printExperiment(result) {
  console.log(`\nExperiment ${result.experimentId}`);
  console.log(`Shots: ${result.shots}`);
  console.table(
    Object.keys(result.theoretical).map((outcome) => ({
      outcome,
      theoretical: result.theoretical[outcome].toFixed(4),
      count: result.counts[outcome],
      observed: result.observed[outcome].toFixed(4),
      standardError: result.standardErrors[outcome].toFixed(4),
    }))
  );
  console.log(
    `Total variation distance: ${result.totalVariationDistance.toFixed(4)}`
  );
}

async function collectIndependentBatches(experiment, batchCount, shotsPerBatch) {
  if (
    !Number.isSafeInteger(batchCount) ||
    batchCount <= 0 ||
    !Number.isSafeInteger(shotsPerBatch) ||
    shotsPerBatch <= 0
  ) {
    throw new RangeError("Batch count and shots per batch must be positive integers.");
  }

  // Promise scheduling is useful for an asynchronous API wrapper. The local
  // sampler itself is synchronous and these batches share one PRNG instance.
  // A real hardware service should use independent job IDs and provider results.
  const results = await Promise.all(
    Array.from({ length: batchCount }, async () => experiment.measure(shotsPerBatch))
  );

  const aggregateCounts = Object.fromEntries(
    experiment.outcomes.map((outcome) => [outcome, 0])
  );

  for (const result of results) {
    for (const outcome of experiment.outcomes) {
      aggregateCounts[outcome] += result.counts[outcome];
    }
  }

  const totalShots = batchCount * shotsPerBatch;
  const aggregateFrequencies = Object.fromEntries(
    experiment.outcomes.map((outcome) => [
      outcome,
      aggregateCounts[outcome] / totalShots,
    ])
  );

  return {
    batchCount,
    shotsPerBatch,
    totalShots,
    aggregateCounts,
    aggregateFrequencies,
  };
}

async function main() {
  const qubit = new MeasurementExperiment({ 0: 0.5, 1: 0.5 }, 41);
  printExperiment(qubit.measure(1000));

  const bellState = new MeasurementExperiment({ 00: 0.5, 11: 0.5 }, 42);
  const bellResult = bellState.measure(2000);
  printExperiment(bellResult);
  assert.equal(bellResult.counts["01"], 0);
  assert.equal(bellResult.counts["10"], 0);

  const complexState = probabilitiesFromAmplitudes({
    "0": { re: 1 / Math.sqrt(2), im: 0 },
    "1": { re: 0, im: 1 / Math.sqrt(2) },
  });
  assert.ok(Math.abs(complexState["0"] - 0.5) < 1e-9);

  const batches = await collectIndependentBatches(
    new MeasurementExperiment({ 0: 0.8, 1: 0.2 }, 99),
    5,
    500
  );
  console.log("\nAggregated batches");
  console.log(JSON.stringify(batches, null, 2));

  for (const invalid of [
    {},
    { 0: 0.4, 1: 0.4 },
    { 0: -0.1, 1: 1.1 },
    { 0: 0.5, 10: 0.5 },
  ]) {
    assert.throws(() => new MeasurementExperiment(invalid));
  }

  assert.throws(() => qubit.measure(0));
  assert.throws(() => qubit.measure(2.5));
  console.log("\nValidation tests passed.");
}

main().catch((error) => {
  console.error("Measurement demonstration failed:", error.message);
  process.exitCode = 1;
});
