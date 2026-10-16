"use strict";

/*
 * Quantum algorithm fundamentals through event-driven simulation.
 * The model emphasizes query oracles, amplitude interference, measurement,
 * and algorithmic cost. It uses only the Node.js standard runtime.
 */

const EPSILON = 1e-9;

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function normalizeState(state) {
  const normSquared = state.reduce(
    (total, amplitude) => total + amplitude.re ** 2 + amplitude.im ** 2,
    0
  );
  assert(normSquared > EPSILON, "Cannot normalize a zero state.");
  const norm = Math.sqrt(normSquared);
  return state.map(({ re, im }) => ({ re: re / norm, im: im / norm }));
}

function basisState(qubits, index = 0) {
  assert(Number.isInteger(qubits) && qubits >= 0, "Invalid qubit count.");
  const dimension = 2 ** qubits;
  assert(Number.isSafeInteger(dimension), "State space is too large.");
  assert(Number.isInteger(index) && index >= 0 && index < dimension,
    "Invalid basis index.");

  return Array.from({ length: dimension }, (_, position) => ({
    re: position === index ? 1 : 0,
    im: 0
  }));
}

function hadamard(state) {
  const dimension = state.length;
  assert(
    Number.isInteger(Math.log2(dimension)),
    "Dimension must be a power of two."
  );

  const output = state.map(({ re, im }) => ({ re, im }));
  const scale = Math.SQRT1_2;

  // In-place butterflies implement H tensor n without constructing a matrix.
  for (let width = 1; width < dimension; width *= 2) {
    for (let start = 0; start < dimension; start += width * 2) {
      for (let offset = 0; offset < width; offset++) {
        const left = output[start + offset];
        const right = output[start + offset + width];
        output[start + offset] = {
          re: (left.re + right.re) * scale,
          im: (left.im + right.im) * scale
        };
        output[start + offset + width] = {
          re: (left.re - right.re) * scale,
          im: (left.im - right.im) * scale
        };
      }
    }
  }

  return output;
}

function probabilities(state) {
  const raw = state.map(({ re, im }) => re * re + im * im);
  const total = raw.reduce((sum, value) => sum + value, 0);
  assert(Math.abs(total - 1) < EPSILON, "State is not normalized.");
  return raw;
}

function measure(state, random = Math.random) {
  const distribution = probabilities(state);
  const draw = random();
  let cumulative = 0;

  for (let index = 0; index < distribution.length; index++) {
    cumulative += distribution[index];
    if (draw < cumulative) return index;
  }
  return distribution.length - 1;
}

function phaseOracle(state, predicate) {
  // A phase oracle preserves probabilities immediately but changes later
  // interference, which is the essential resource used by Grover search.
  return state.map((amplitude, index) =>
    predicate(index)
      ? { re: -amplitude.re, im: -amplitude.im }
      : { ...amplitude }
  );
}

function diffuse(state) {
  const mean = state.reduce(
    (accumulator, amplitude) => ({
      re: accumulator.re + amplitude.re / state.length,
      im: accumulator.im + amplitude.im / state.length
    }),
    { re: 0, im: 0 }
  );

  return state.map(({ re, im }) => ({
    re: 2 * mean.re - re,
    im: 2 * mean.im - im
  }));
}

function groverSearch(qubits, markedPredicate) {
  assert(Number.isInteger(qubits) && qubits > 0, "Invalid qubit count.");
  assert(typeof markedPredicate === "function", "Oracle must be callable.");

  const dimension = 2 ** qubits;
  let state = hadamard(basisState(qubits));
  const markedCount = Array.from(
    { length: dimension },
    (_, index) => index
  ).filter(markedPredicate).length;

  assert(markedCount > 0, "Oracle has no marked states.");
  assert(markedCount < dimension, "Every state is marked.");

  // The iteration count depends on the fraction of marked states.
  const iterations = Math.max(
    1,
    Math.round((Math.PI / 4) * Math.sqrt(dimension / markedCount))
  );

  for (let iteration = 0; iteration < iterations; iteration++) {
    state = phaseOracle(state, markedPredicate);
    state = diffuse(state);
  }

  return { state, iterations, markedCount };
}

class QuantumExperiment {
  #listeners = new Map();
  #events = [];

  on(eventName, listener) {
    assert(typeof listener === "function", "Listener must be a function.");
    const listeners = this.#listeners.get(eventName) ?? [];
    listeners.push(listener);
    this.#listeners.set(eventName, listeners);

    // Return an unsubscribe function so long-lived experiments do not retain
    // listeners that are no longer needed.
    return () => {
      this.#listeners.set(
        eventName,
        (this.#listeners.get(eventName) ?? []).filter(
          candidate => candidate !== listener
        )
      );
    };
  }

  emit(eventName, payload) {
    const event = Object.freeze({
      eventName,
      payload: Object.freeze({ ...payload }),
      timestamp: new Date().toISOString()
    });
    this.#events.push(event);

    for (const listener of this.#listeners.get(eventName) ?? []) {
      listener(event);
    }
  }

  get history() {
    return this.#events.map(event => ({
      eventName: event.eventName,
      payload: { ...event.payload },
      timestamp: event.timestamp
    }));
  }
}

async function executeExperiment() {
  const experiment = new QuantumExperiment();

  experiment.on("circuit.prepared", event => {
    console.log("Prepared:", event.payload.algorithm);
  });

  experiment.on("circuit.measured", event => {
    console.log(
      `Measurement: |${event.payload.bitstring}> ` +
      `(probability ${event.payload.probability.toFixed(4)})`
    );
  });

  const qubits = 5;
  const marked = 19;
  const result = groverSearch(qubits, index => index === marked);
  const distribution = probabilities(result.state);
  const outcome = distribution.indexOf(Math.max(...distribution));

  experiment.emit("circuit.prepared", {
    algorithm: "Grover search",
    qubits,
    markedState: marked,
    iterations: result.iterations
  });

  // Async iteration allows results from a real remote quantum job to be
  // integrated later without changing the event consumers.
  await Promise.resolve();

  experiment.emit("circuit.measured", {
    bitstring: outcome.toString(2).padStart(qubits, "0"),
    probability: distribution[outcome]
  });

  console.log("Oracle iterations:", result.iterations);
  console.log("Marked-state probability:", distribution[marked].toFixed(4));
  console.log("Recorded events:", experiment.history.length);

  const uniform = hadamard(basisState(2));
  console.log("Uniform distribution:", probabilities(uniform).map(
    value => Number(value.toFixed(3))
  ));

  const restored = hadamard(hadamard(basisState(1)));
  console.log("H squared restores |0>:", measure(restored, () => 0.1) === 0);

  try {
    probabilities([{ re: 0.5, im: 0 }]);
  } catch (error) {
    console.log("Invalid-state rejection:", error.message);
  }
}

executeExperiment().catch(error => {
  console.error("Experiment failed:", error.message);
  process.exitCode = 1;
});
