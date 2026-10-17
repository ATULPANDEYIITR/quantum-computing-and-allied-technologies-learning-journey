"use strict";

/*
 * Deutsch algorithm with an event-driven circuit execution model.
 *
 * The implementation uses typed arrays for complex state-vector
 * amplitudes and explicit circuit events for preparation, oracle
 * application, interference, and measurement.
 *
 * Basis convention:
 *   index = inputBit + 2 * ancillaBit
 *
 * This example is executable in Node.js without npm dependencies.
 */

const EPSILON = 1e-10;

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function complexVector(dimension) {
  return {
    real: new Float64Array(dimension),
    imag: new Float64Array(dimension),
  };
}

function basisState(index, qubits) {
  if (!Number.isInteger(qubits) || qubits < 1) {
    throw new RangeError("At least one qubit is required.");
  }

  const dimension = 2 ** qubits;
  if (!Number.isInteger(index) || index < 0 || index >= dimension) {
    throw new RangeError("Basis index is out of range.");
  }

  const state = complexVector(dimension);
  state.real[index] = 1;
  return state;
}

function cloneState(state) {
  return {
    real: new Float64Array(state.real),
    imag: new Float64Array(state.imag),
  };
}

function probabilityNorm(state) {
  let total = 0;

  for (let index = 0; index < state.real.length; index += 1) {
    total += state.real[index] ** 2 + state.imag[index] ** 2;
  }

  return total;
}

function validateState(state, qubits) {
  assert(
    state.real.length === state.imag.length,
    "Real and imaginary amplitude arrays must match."
  );

  assert(
    state.real.length === 2 ** qubits,
    "State dimension does not match qubit count."
  );

  for (let index = 0; index < state.real.length; index += 1) {
    assert(
      Number.isFinite(state.real[index]) &&
        Number.isFinite(state.imag[index]),
      "State amplitudes must be finite."
    );
  }

  assert(
    Math.abs(probabilityNorm(state) - 1) < EPSILON,
    "State must be normalized."
  );
}

function applyGate(state, qubit, matrix, qubits) {
  if (!Number.isInteger(qubit) || qubit < 0 || qubit >= qubits) {
    throw new RangeError("Qubit index is out of range.");
  }

  if (state.real.length !== 2 ** qubits) {
    throw new RangeError("State dimension is invalid.");
  }

  const result = cloneState(state);
  const mask = 1 << qubit;

  for (let index = 0; index < state.real.length; index += 1) {
    if ((index & mask) !== 0) continue;

    const paired = index | mask;
    const aReal = state.real[index];
    const aImag = state.imag[index];
    const bReal = state.real[paired];
    const bImag = state.imag[paired];

    // The gates used here have real matrix entries, so each output
    // amplitude is a real linear combination of complex amplitudes.
    result.real[index] =
      matrix[0][0] * aReal + matrix[0][1] * bReal;
    result.imag[index] =
      matrix[0][0] * aImag + matrix[0][1] * bImag;

    result.real[paired] =
      matrix[1][0] * aReal + matrix[1][1] * bReal;
    result.imag[paired] =
      matrix[1][0] * aImag + matrix[1][1] * bImag;
  }

  return result;
}

const H = (() => {
  const s = 1 / Math.sqrt(2);
  return [[s, s], [s, -s]];
})();

const X = [
  [0, 1],
  [1, 0],
];

class BooleanOracle {
  constructor(f0, f1, name = "custom") {
    for (const output of [f0, f1]) {
      if (output !== 0 && output !== 1) {
        throw new TypeError("Oracle outputs must be bits.");
      }
    }

    this.f0 = f0;
    this.f1 = f1;
    this.name = name;
    Object.freeze(this);
  }

  evaluate(input) {
    if (input !== 0 && input !== 1) {
      throw new RangeError("Oracle input must be a bit.");
    }

    return input === 0 ? this.f0 : this.f1;
  }

  get classification() {
    return this.f0 === this.f1 ? "constant" : "balanced";
  }

  get truthTable() {
    return [this.f0, this.f1];
  }
}

function applyOracle(state, oracle) {
  if (state.real.length !== 4) {
    throw new RangeError("Deutsch oracle requires two qubits.");
  }

  const result = complexVector(4);

  for (let index = 0; index < 4; index += 1) {
    const input = index & 1;
    const ancilla = (index >> 1) & 1;
    const newAncilla = ancilla ^ oracle.evaluate(input);
    const destination = input | (newAncilla << 1);

    // XOR makes the oracle reversible: the input is preserved and
    // the target bit records f(input) without destroying information.
    result.real[destination] += state.real[index];
    result.imag[destination] += state.imag[index];
  }

  validateState(result, 2);
  return result;
}

function marginalProbabilities(state, qubit, qubits) {
  validateState(state, qubits);

  if (!Number.isInteger(qubit) || qubit < 0 || qubit >= qubits) {
    throw new RangeError("Qubit index is out of range.");
  }

  const probabilities = [0, 0];
  const mask = 1 << qubit;

  for (let index = 0; index < state.real.length; index += 1) {
    const outcome = (index & mask) === 0 ? 0 : 1;
    probabilities[outcome] +=
      state.real[index] ** 2 + state.imag[index] ** 2;
  }

  return probabilities;
}

function sample(probabilities, random = Math.random) {
  const value = random();
  if (!(value >= 0 && value < 1)) {
    throw new RangeError("Random source must return a value in [0, 1).");
  }

  return value < probabilities[0] ? 0 : 1;
}

class CircuitRun {
  constructor(oracle) {
    this.oracle = oracle;
    this.events = [];
    this.state = basisState(0, 2);
  }

  record(operation, state) {
    validateState(state, 2);
    this.state = state;
    this.events.push({
      operation,
      probabilities: marginalProbabilities(state, 0, 2),
      norm: probabilityNorm(state),
    });
  }

  prepare() {
    let state = applyGate(this.state, 1, X, 2);
    state = applyGate(state, 0, H, 2);
    state = applyGate(state, 1, H, 2);
    this.record("Prepare |+>|->", state);
  }

  queryOracle() {
    this.record("Apply one oracle invocation", applyOracle(this.state, this.oracle));
  }

  interfere() {
    this.record(
      "Final Hadamard on input qubit",
      applyGate(this.state, 0, H, 2)
    );
  }

  run() {
    this.prepare();
    this.queryOracle();
    this.interfere();

    const probabilities = marginalProbabilities(this.state, 0, 2);
    const classification = probabilities[0] > 0.5
      ? "constant"
      : "balanced";

    return {
      oracle: this.oracle.name,
      truthTable: this.oracle.truthTable,
      classification,
      expectedClassification: this.oracle.classification,
      probabilities,
      events: this.events,
      oracleCalls: 1,
    };
  }
}

function estimateWithReadoutNoise(
  probabilities,
  shots,
  flipProbability,
  random = Math.random
) {
  if (!Number.isInteger(shots) || shots <= 0) {
    throw new RangeError("shots must be a positive integer.");
  }

  if (
    !Number.isFinite(flipProbability) ||
    flipProbability < 0 ||
    flipProbability > 1
  ) {
    throw new RangeError("flipProbability must be in [0, 1].");
  }

  const counts = [0, 0];

  for (let shot = 0; shot < shots; shot += 1) {
    let outcome = sample(probabilities, random);

    // This models a classical measurement-bit error, not full
    // quantum-device noise or faulty oracle execution.
    if (random() < flipProbability) outcome ^= 1;

    counts[outcome] += 1;
  }

  return {
    counts,
    mostFrequentOutcome: counts[0] >= counts[1] ? 0 : 1,
    estimatedClassification: counts[0] >= counts[1]
      ? "constant"
      : "balanced",
  };
}

function demonstrateQueryComplexity(oracle) {
  // A deterministic classical algorithm cannot decide the category
  // from f(0) alone, because both categories can share that value.
  const classicalObservations = [
    oracle.evaluate(0),
    oracle.evaluate(1),
  ];

  return {
    classicalQueries: classicalObservations.length,
    classicalClassification:
      classicalObservations[0] === classicalObservations[1]
        ? "constant"
        : "balanced",
    quantumQueries: 1,
  };
}

function verifyAllTruthTables() {
  const oracles = [
    new BooleanOracle(0, 0, "zero"),
    new BooleanOracle(0, 1, "identity"),
    new BooleanOracle(1, 0, "negation"),
    new BooleanOracle(1, 1, "one"),
  ];

  for (const oracle of oracles) {
    const result = new CircuitRun(oracle).run();

    assert(
      result.classification === oracle.classification,
      `Misclassified oracle ${oracle.name}.`
    );

    assert(
      Math.abs(result.probabilities[0] - 1) < EPSILON ||
        Math.abs(result.probabilities[1] - 1) < EPSILON,
      "Ideal Deutsch circuit must produce a deterministic input outcome."
    );

    console.log(
      `${oracle.name.padEnd(10)} truth=${oracle.truthTable.join("")} ` +
        `category=${result.classification.padEnd(8)} ` +
        `P(0)=${result.probabilities[0].toFixed(3)}`
    );
  }
}

function main() {
  console.log("DEUTSCH ALGORITHM: EVENT-DRIVEN CIRCUIT SIMULATION");
  console.log("Oracle truth tables and classifications");
  verifyAllTruthTables();

  const oracle = new BooleanOracle(0, 1, "identity");
  const run = new CircuitRun(oracle).run();

  console.log("\nCircuit events");
  for (const event of run.events) {
    console.log(
      `${event.operation}: ` +
        `P(input=0)=${event.probabilities[0].toFixed(3)}, ` +
        `norm=${event.norm.toFixed(6)}`
    );
  }

  console.log("\nQuery comparison");
  console.log(demonstrateQueryComplexity(oracle));

  console.log("\nNoisy readout simulation");
  console.log(
    estimateWithReadoutNoise(run.probabilities, 1000, 0.02)
  );

  console.log(
    "\nThe one-query result is an oracle-complexity advantage. " +
      "It does not imply that every quantum circuit runs faster " +
      "than its classical counterpart."
  );
}

main();
