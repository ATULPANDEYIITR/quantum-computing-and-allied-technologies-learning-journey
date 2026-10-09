"use strict";

/*
 * Qiskit Fundamentals: Installation and First Circuit
 *
 * This Node.js program models the first-circuit workflow as an event-driven
 * experiment. It constructs a Hadamard circuit, simulates statevector
 * amplitudes, samples measurement outcomes, and compares a Bell circuit
 * with an independent-qubit experiment.
 *
 * Runtime: Node.js 18 or later.
 * Install Qiskit separately in Python with:
 *   python -m pip install qiskit qiskit-aer
 *
 * This JavaScript file does not invoke Python or require npm dependencies.
 */

const { randomUUID } = require("node:crypto");

function assertIntegerInRange(value, minimum, maximum, name) {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new RangeError(
      `${name} must be a safe integer between ${minimum} and ${maximum}.`
    );
  }
}

function complex(real, imaginary = 0) {
  return { re: real, im: imaginary };
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

function magnitudeSquared(value) {
  return value.re * value.re + value.im * value.im;
}

function validateState(state, qubitCount) {
  if (state.length !== 2 ** qubitCount) {
    throw new Error("Statevector length does not match qubit count.");
  }

  const norm = state.reduce((sum, amplitude) => {
    return sum + magnitudeSquared(amplitude);
  }, 0);

  if (Math.abs(norm - 1) > 1e-9) {
    throw new Error(`Invalid statevector normalization: ${norm}`);
  }
}

class QuantumCircuitModel {
  constructor(qubitCount, classicalBitCount = qubitCount) {
    assertIntegerInRange(qubitCount, 1, 12, "qubitCount");
    assertIntegerInRange(classicalBitCount, 1, 12, "classicalBitCount");

    this.qubitCount = qubitCount;
    this.classicalBitCount = classicalBitCount;
    this.operations = [];
    this.measurements = [];
  }

  h(target) {
    this.#validateQubit(target);
    this.operations.push({ name: "H", target });
    return this;
  }

  x(target) {
    this.#validateQubit(target);
    this.operations.push({ name: "X", target });
    return this;
  }

  cx(control, target) {
    this.#validateQubit(control);
    this.#validateQubit(target);

    if (control === target) {
      throw new Error("CNOT control and target must differ.");
    }

    this.operations.push({ name: "CX", control, target });
    return this;
  }

  measure(qubit, classicalBit) {
    this.#validateQubit(qubit);
    assertIntegerInRange(
      classicalBit,
      0,
      this.classicalBitCount - 1,
      "classicalBit"
    );

    this.measurements.push({ qubit, classicalBit });
    return this;
  }

  #validateQubit(qubit) {
    assertIntegerInRange(qubit, 0, this.qubitCount - 1, "qubit");
  }

  describe() {
    return {
      qubits: this.qubitCount,
      classicalBits: this.classicalBitCount,
      operations: this.operations.map((operation) => ({ ...operation })),
      measurements: this.measurements.map((measurement) => ({
        ...measurement
      }))
    };
  }

  simulateStatevector() {
    const dimension = 2 ** this.qubitCount;
    let state = Array.from({ length: dimension }, () => complex(0));
    state[0] = complex(1);

    const scale = 1 / Math.sqrt(2);

    for (const operation of this.operations) {
      if (operation.name === "H") {
        const mask = 1 << operation.target;
        const next = state.map(() => complex(0));

        for (let index = 0; index < dimension; index += 1) {
          if ((index & mask) !== 0) continue;

          const paired = index | mask;
          next[index] = multiply(
            add(state[index], state[paired]),
            complex(scale)
          );
          next[paired] = multiply(
            add(state[index], complex(-state[paired].re, -state[paired].im)),
            complex(scale)
          );
        }

        state = next;
      } else if (operation.name === "X") {
        const mask = 1 << operation.target;
        const next = Array.from({ length: dimension }, () => complex(0));

        for (let index = 0; index < dimension; index += 1) {
          next[index ^ mask] = state[index];
        }

        state = next;
      } else if (operation.name === "CX") {
        const controlMask = 1 << operation.control;
        const targetMask = 1 << operation.target;
        const next = Array.from({ length: dimension }, () => complex(0));

        for (let index = 0; index < dimension; index += 1) {
          const destination =
            (index & controlMask) !== 0 ? index ^ targetMask : index;
          next[destination] = state[index];
        }

        state = next;
      } else {
        throw new Error(`Unsupported operation: ${operation.name}`);
      }
    }

    validateState(state, this.qubitCount);
    return state;
  }
}

/*
 * Measurement is stochastic even for a perfectly specified statevector.
 * A seeded generator makes demonstrations reproducible without dependencies.
 */
function seededRandom(seed) {
  let value = seed >>> 0;

  return function nextRandom() {
    value = (value + 0x6D2B79F5) >>> 0;
    let mixed = value;
    mixed = Math.imul(mixed ^ (mixed >>> 15), mixed | 1);
    mixed ^= mixed + Math.imul(mixed ^ (mixed >>> 7), mixed | 61);
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296;
  };
}

function measureState(state, qubitCount, shots, seed = 42) {
  assertIntegerInRange(shots, 1, 10_000_000, "shots");
  validateState(state, qubitCount);

  const probabilities = state.map(magnitudeSquared);
  const cumulative = [];
  let running = 0;

  for (const probability of probabilities) {
    running += probability;
    cumulative.push(running);
  }

  const random = seededRandom(seed);
  const counts = Object.create(null);

  for (let shot = 0; shot < shots; shot += 1) {
    const sample = random();
    let index = cumulative.findIndex((threshold) => sample < threshold);

    if (index === -1) index = cumulative.length - 1;

    const bitString = index.toString(2).padStart(qubitCount, "0");
    counts[bitString] = (counts[bitString] || 0) + 1;
  }

  if (Object.values(counts).reduce((sum, count) => sum + count, 0) !== shots) {
    throw new Error("Measurement accounting failed.");
  }

  return { shots, counts };
}

class ExperimentRunner {
  constructor() {
    this.listeners = new Map();
    this.history = [];
  }

  on(eventName, listener) {
    if (typeof listener !== "function") {
      throw new TypeError("Event listener must be a function.");
    }

    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, new Set());
    }

    this.listeners.get(eventName).add(listener);

    return () => this.listeners.get(eventName)?.delete(listener);
  }

  emit(eventName, payload) {
    this.history.push({
      eventId: randomUUID(),
      eventName,
      timestamp: new Date().toISOString(),
      payload
    });

    for (const listener of this.listeners.get(eventName) || []) {
      listener(payload);
    }
  }

  async run(circuit, shots, seed) {
    this.emit("experiment:started", {
      circuit: circuit.describe(),
      shots
    });

    // The microtask boundary models asynchronous execution in an experiment
    // pipeline without claiming that JavaScript runs on a quantum processor.
    await Promise.resolve();

    try {
      const state = circuit.simulateStatevector();
      const result = measureState(state, circuit.qubitCount, shots, seed);

      this.emit("experiment:completed", { result, state });
      return { state, result };
    } catch (error) {
      this.emit("experiment:failed", {
        message: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }
}

function displayExperiment(name, circuit, execution) {
  console.log(`\n${name}`);
  console.log(JSON.stringify(circuit.describe(), null, 2));

  console.log("Statevector:");
  execution.state.forEach((amplitude, index) => {
    console.log(
      `  |${index.toString(2).padStart(circuit.qubitCount, "0")}> ` +
      `${amplitude.re.toFixed(4)} ${amplitude.im >= 0 ? "+" : "-"} ` +
      `${Math.abs(amplitude.im).toFixed(4)}i`
    );
  });

  console.log("Measurement counts:", execution.result.counts);
}

async function main() {
  console.log("Node.js:", process.version);
  console.log("Qiskit installation command: python -m pip install qiskit qiskit-aer");

  const runner = new ExperimentRunner();

  runner.on("experiment:started", (event) => {
    console.log(`Starting experiment with ${event.shots} shots.`);
  });

  runner.on("experiment:completed", ({ result }) => {
    console.log(`Completed ${result.shots} measurements.`);
  });

  runner.on("experiment:failed", ({ message }) => {
    console.error("Experiment failed:", message);
  });

  const hadamardCircuit = new QuantumCircuitModel(1)
    .h(0)
    .measure(0, 0);

  const hadamardExecution = await runner.run(hadamardCircuit, 4096, 42);
  displayExperiment("Hadamard superposition", hadamardCircuit, hadamardExecution);

  const deterministicCircuit = new QuantumCircuitModel(1)
    .x(0)
    .measure(0, 0);

  const deterministicExecution = await runner.run(
    deterministicCircuit,
    128,
    42
  );

  displayExperiment(
    "Deterministic X-gate experiment",
    deterministicCircuit,
    deterministicExecution
  );

  if (deterministicExecution.result.counts["1"] !== 128) {
    throw new Error("The X-gate experiment should always return 1.");
  }

  const bellCircuit = new QuantumCircuitModel(2)
    .h(0)
    .cx(0, 1)
    .measure(0, 0)
    .measure(1, 1);

  const bellExecution = await runner.run(bellCircuit, 2048, 17);
  displayExperiment("Bell-state experiment", bellCircuit, bellExecution);

  const invalidCircuit = new QuantumCircuitModel(1);

  try {
    invalidCircuit.cx(0, 0);
  } catch (error) {
    console.log("\nCorrectly rejected invalid circuit:", error.message);
  }

  const bellOutcomes = Object.keys(bellExecution.result.counts);
  if (bellOutcomes.some((outcome) => !["00", "11"].includes(outcome))) {
    throw new Error("Bell-state simulation produced an invalid outcome.");
  }

  console.log(`Recorded events: ${runner.history.length}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
