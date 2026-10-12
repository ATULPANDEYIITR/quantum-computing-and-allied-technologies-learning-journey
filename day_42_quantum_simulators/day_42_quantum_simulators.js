"use strict";

/*
 * Quantum simulators: statevector and shot-based simulation.
 *
 * Runtime: Node.js 18 or later.
 * No external dependencies.
 *
 * This implementation emphasizes JavaScript-specific event processing,
 * reproducible pseudo-random sampling, streaming count accumulation, and
 * asynchronous shot batches.
 */

const EPSILON = 1e-10;
const DEFAULT_MAX_QUBITS = 22;

class QuantumSimulationError extends Error {}
class CircuitValidationError extends QuantumSimulationError {}
class SimulationResourceError extends QuantumSimulationError {}

function validateQubitCount(qubits, maximum = DEFAULT_MAX_QUBITS) {
  if (!Number.isSafeInteger(qubits) || qubits < 1) {
    throw new CircuitValidationError("Qubit count must be a positive integer.");
  }
  if (qubits > maximum) {
    throw new SimulationResourceError(
      `Circuit has ${qubits} qubits; configured maximum is ${maximum}.`
    );
  }
}

function validateQubit(qubit, qubits) {
  if (!Number.isSafeInteger(qubit) || qubit < 0 || qubit >= qubits) {
    throw new CircuitValidationError(
      `Invalid qubit ${qubit}; valid indices are 0 through ${qubits - 1}.`
    );
  }
}

function complex(real = 0, imag = 0) {
  if (!Number.isFinite(real) || !Number.isFinite(imag)) {
    throw new CircuitValidationError("Complex components must be finite.");
  }
  return { re: real, im: imag };
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

function scale(a, factor) {
  return complex(a.re * factor, a.im * factor);
}

function conjugate(a) {
  return complex(a.re, -a.im);
}

function magnitudeSquared(a) {
  return a.re * a.re + a.im * a.im;
}

function matrix2(rows) {
  if (
    !Array.isArray(rows) ||
    rows.length !== 2 ||
    rows.some((row) => !Array.isArray(row) || row.length !== 2)
  ) {
    throw new CircuitValidationError("A gate matrix must be 2 by 2.");
  }

  const copy = rows.map((row) =>
    row.map((value) => complex(value.re, value.im))
  );

  // Verify U†U = I before allowing the matrix into a circuit.
  for (let i = 0; i < 2; i += 1) {
    for (let j = 0; j < 2; j += 1) {
      let inner = complex();
      for (let k = 0; k < 2; k += 1) {
        inner = add(inner, multiply(conjugate(copy[k][i]), copy[k][j]));
      }
      const expected = i === j ? 1 : 0;
      if (Math.hypot(inner.re - expected, inner.im) > EPSILON) {
        throw new CircuitValidationError("Gate matrix must be unitary.");
      }
    }
  }
  return copy;
}

const I = matrix2([
  [complex(1), complex(0)],
  [complex(0), complex(1)],
]);

const X = matrix2([
  [complex(0), complex(1)],
  [complex(1), complex(0)],
]);

const H = matrix2([
  [complex(1 / Math.sqrt(2)), complex(1 / Math.sqrt(2))],
  [complex(1 / Math.sqrt(2)), complex(-1 / Math.sqrt(2))],
]);

function phaseGate(theta) {
  if (!Number.isFinite(theta)) {
    throw new CircuitValidationError("Phase angle must be finite.");
  }
  return matrix2([
    [complex(1), complex(0)],
    [complex(0), complex(Math.cos(theta), Math.sin(theta))],
  ]);
}

function ryGate(theta) {
  if (!Number.isFinite(theta)) {
    throw new CircuitValidationError("Rotation angle must be finite.");
  }
  const c = Math.cos(theta / 2);
  const s = Math.sin(theta / 2);
  return matrix2([
    [complex(c), complex(-s)],
    [complex(s), complex(c)],
  ]);
}

class QuantumCircuit {
  constructor(qubits, maximumQubits = DEFAULT_MAX_QUBITS) {
    validateQubitCount(qubits, maximumQubits);
    this.qubits = qubits;
    this.gates = [];
    this.measuredQubits = Array.from({ length: qubits }, (_, i) => i);
  }

  addGate(name, target, matrix, control = null) {
    validateQubit(target, this.qubits);
    if (control !== null) {
      validateQubit(control, this.qubits);
      if (control === target) {
        throw new CircuitValidationError("Control and target must differ.");
      }
    }

    this.gates.push(Object.freeze({
      name,
      target,
      control,
      matrix,
    }));
    return this;
  }

  h(target) {
    return this.addGate("H", target, H);
  }

  x(target) {
    return this.addGate("X", target, X);
  }

  phase(target, theta) {
    return this.addGate("P", target, phaseGate(theta));
  }

  ry(target, theta) {
    return this.addGate("RY", target, ryGate(theta));
  }

  cx(control, target) {
    return this.addGate("CX", target, X, control);
  }

  measure(...qubits) {
    const selected = qubits.length ? qubits : this.measuredQubits;
    if (
      selected.length === 0 ||
      new Set(selected).size !== selected.length
    ) {
      throw new CircuitValidationError(
        "Measurement requires distinct qubit indices."
      );
    }
    selected.forEach((q) => validateQubit(q, this.qubits));
    this.measuredQubits = [...selected];
    return this;
  }
}

function applyGate(state, qubits, gate) {
  const result = state.slice();
  const targetMask = 2 ** gate.target;
  const controlMask = gate.control === null ? 0 : 2 ** gate.control;
  const u = gate.matrix;

  for (let index = 0; index < state.length; index += 1) {
    if (Math.floor(index / targetMask) % 2 === 1) continue;

    const partner = index + targetMask;
    if (controlMask && Math.floor(index / controlMask) % 2 === 0) continue;

    const a0 = state[index];
    const a1 = state[partner];

    result[index] = add(multiply(u[0][0], a0), multiply(u[0][1], a1));
    result[partner] = add(
      multiply(u[1][0], a0),
      multiply(u[1][1], a1)
    );
  }

  return result;
}

function simulateStatevector(circuit) {
  const state = Array.from(
    { length: 2 ** circuit.qubits },
    () => complex()
  );
  state[0] = complex(1);

  let current = state;
  for (const gate of circuit.gates) {
    current = applyGate(current, circuit.qubits, gate);
  }

  const norm = current.reduce(
    (sum, amplitude) => sum + magnitudeSquared(amplitude),
    0
  );
  if (Math.abs(norm - 1) > 1e-8) {
    throw new QuantumSimulationError(`State norm is ${norm}, not one.`);
  }
  return current;
}

function measurementDistribution(state, qubits, measuredQubits) {
  const probabilities = Array(2 ** measuredQubits.length).fill(0);

  for (let basis = 0; basis < state.length; basis += 1) {
    let outcome = 0;
    measuredQubits.forEach((qubit, outputBit) => {
      if (Math.floor(basis / (2 ** qubit)) % 2 === 1) {
        outcome += 2 ** outputBit;
      }
    });
    probabilities[outcome] += magnitudeSquared(state[basis]);
  }

  const total = probabilities.reduce((sum, p) => sum + p, 0);
  if (!Number.isFinite(total) || total <= 0) {
    throw new QuantumSimulationError("Invalid probability distribution.");
  }
  return probabilities.map((p) => p / total);
}

function bitstring(index, width) {
  return index.toString(2).padStart(width, "0");
}

function exactDistribution(circuit, state = null) {
  const vector = state || simulateStatevector(circuit);
  if (vector.length !== 2 ** circuit.qubits) {
    throw new CircuitValidationError("State dimension mismatch.");
  }

  const probabilities = measurementDistribution(
    vector,
    circuit.qubits,
    circuit.measuredQubits
  );

  return new Map(
    probabilities.map((probability, index) => [
      bitstring(index, circuit.measuredQubits.length),
      probability,
    ])
  );
}

// Mulberry32 is used here as a deterministic educational PRNG.
// It is not cryptographically secure and must not be used for security keys.
function seededRandom(seed) {
  let value = seed >>> 0;
  return function random() {
    value += 0x6D2B79F5;
    let t = value;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function selectOutcome(distribution, random) {
  const threshold = random();
  let cumulative = 0;

  for (let index = 0; index < distribution.length; index += 1) {
    cumulative += distribution[index];
    if (threshold < cumulative || index === distribution.length - 1) {
      return index;
    }
  }

  throw new QuantumSimulationError("Sampling failed.");
}

function runShots(circuit, shots, seed = 42) {
  if (!Number.isSafeInteger(shots) || shots < 1 || shots > 10_000_000) {
    throw new CircuitValidationError("Invalid shot count.");
  }

  const vector = simulateStatevector(circuit);
  const distribution = measurementDistribution(
    vector,
    circuit.qubits,
    circuit.measuredQubits
  );
  const random = seededRandom(seed);
  const counts = new Map();

  // Counts are accumulated directly instead of retaining every shot result.
  for (let shot = 0; shot < shots; shot += 1) {
    const outcome = bitstring(
      selectOutcome(distribution, random),
      circuit.measuredQubits.length
    );
    counts.set(outcome, (counts.get(outcome) || 0) + 1);
  }

  return counts;
}

function probabilitiesFromCounts(counts, shots) {
  const total = [...counts.values()].reduce((sum, count) => sum + count, 0);
  if (shots <= 0 || total !== shots) {
    throw new CircuitValidationError("Shot count and counts disagree.");
  }

  return new Map(
    [...counts.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([outcome, count]) => [outcome, count / shots])
  );
}

class QuantumJobRunner {
  constructor(circuit) {
    this.circuit = circuit;
    this.listeners = new Map();
  }

  on(eventName, listener) {
    if (typeof listener !== "function") {
      throw new TypeError("Listener must be a function.");
    }
    const listeners = this.listeners.get(eventName) || new Set();
    listeners.add(listener);
    this.listeners.set(eventName, listeners);
    return () => listeners.delete(listener);
  }

  emit(eventName, payload) {
    for (const listener of this.listeners.get(eventName) || []) {
      listener(payload);
    }
  }

  async execute({ shots, batchSize = 1000, seed = 42 }) {
    if (
      !Number.isSafeInteger(shots) ||
      shots < 1 ||
      !Number.isSafeInteger(batchSize) ||
      batchSize < 1
    ) {
      throw new CircuitValidationError("Invalid execution parameters.");
    }

    this.emit("started", { shots, qubits: this.circuit.qubits });
    const counts = new Map();
    let completed = 0;
    let batchIndex = 0;

    try {
      // Batches yield to the event loop so progress observers can update.
      while (completed < shots) {
        const batchShots = Math.min(batchSize, shots - completed);
        const batchCounts = runShots(
          this.circuit,
          batchShots,
          (seed + batchIndex) >>> 0
        );

        for (const [outcome, count] of batchCounts) {
          counts.set(outcome, (counts.get(outcome) || 0) + count);
        }

        completed += batchShots;
        batchIndex += 1;
        this.emit("progress", {
          completed,
          total: shots,
          fraction: completed / shots,
        });

        await new Promise((resolve) => setImmediate(resolve));
      }

      this.emit("completed", { counts, shots });
      return counts;
    } catch (error) {
      this.emit("failed", { error, completed });
      throw error;
    }
  }
}

function totalVariationDistance(first, second) {
  const outcomes = new Set([...first.keys(), ...second.keys()]);
  let sum = 0;
  for (const outcome of outcomes) {
    sum += Math.abs(
      (first.get(outcome) || 0) - (second.get(outcome) || 0)
    );
  }
  return sum / 2;
}

async function main() {
  console.log("QUANTUM SIMULATORS: STATEVECTOR AND SHOT-BASED SIMULATION");

  const bell = new QuantumCircuit(2).h(0).cx(0, 1).measure(0, 1);
  const state = simulateStatevector(bell);
  const exact = exactDistribution(bell);
  const counts = runShots(bell, 5000, 1234);
  const empirical = probabilitiesFromCounts(counts, 5000);

  console.log("\nBell-state amplitudes:");
  state.forEach((amplitude, index) => {
    if (magnitudeSquared(amplitude) > EPSILON) {
      console.log(
        `|${bitstring(index, 2)}> = ${amplitude.re.toFixed(5)} ` +
        `${amplitude.im >= 0 ? "+" : "-"} ` +
        `${Math.abs(amplitude.im).toFixed(5)}i`
      );
    }
  });

  console.log("Exact probabilities:", Object.fromEntries(exact));
  console.log("Shot counts:", Object.fromEntries(counts));
  console.log("Empirical probabilities:", Object.fromEntries(empirical));
  console.log(
    "Total variation distance:",
    totalVariationDistance(exact, empirical).toFixed(5)
  );

  const phaseInterference = new QuantumCircuit(1)
    .h(0)
    .phase(0, Math.PI)
    .h(0)
    .measure(0);

  console.log(
    "\nInterference after a phase gate:",
    Object.fromEntries(exactDistribution(phaseInterference))
  );

  const runner = new QuantumJobRunner(bell);
  const unsubscribe = runner.on("progress", ({ completed, total }) => {
    if (completed === total || completed % 2000 === 0) {
      console.log(`Job progress: ${completed}/${total} shots`);
    }
  });

  runner.on("failed", ({ error }) => {
    console.error("Quantum job failed:", error.message);
  });

  const jobCounts = await runner.execute({
    shots: 5000,
    batchSize: 1000,
    seed: 987,
  });

  unsubscribe();
  console.log("Asynchronous job counts:", Object.fromEntries(jobCounts));

  try {
    new QuantumCircuit(1).h(2);
  } catch (error) {
    console.log("Expected validation failure:", error.message);
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}

module.exports = {
  QuantumCircuit,
  QuantumSimulationError,
  CircuitValidationError,
  simulateStatevector,
  exactDistribution,
  runShots,
  probabilitiesFromCounts,
  totalVariationDistance,
};
