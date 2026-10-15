"use strict";

/*
 * Multi-qubit circuit laboratory for Node.js.
 *
 * This implementation emphasizes event-driven circuit construction,
 * immutable operation descriptions, controlled-gate execution, measurement
 * statistics, and policy-style validation of circuit resource limits.
 *
 * Run: node quantum-circuit.js
 */

const EPSILON = 1e-10;
const MAX_QUBITS = 18;

function complex(real, imag = 0) {
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

function magnitudeSquared(a) {
  return a.re * a.re + a.im * a.im;
}

function conjugate(a) {
  return complex(a.re, -a.im);
}

function normalize(amplitudes) {
  const normSquared = amplitudes.reduce(
    (sum, amplitude) => sum + magnitudeSquared(amplitude),
    0
  );

  if (normSquared <= EPSILON) {
    throw new RangeError("A state vector cannot have zero norm.");
  }

  const norm = Math.sqrt(normSquared);
  return amplitudes.map(amplitude => scale(amplitude, 1 / norm));
}

function matrixIsUnitary(matrix) {
  if (
    !Array.isArray(matrix) ||
    matrix.length !== 2 ||
    matrix.some(row => !Array.isArray(row) || row.length !== 2)
  ) {
    return false;
  }

  for (let row = 0; row < 2; row += 1) {
    for (let column = 0; column < 2; column += 1) {
      let inner = complex(0);
      for (let k = 0; k < 2; k += 1) {
        inner = add(
          inner,
          multiply(conjugate(matrix[k][row]), matrix[k][column])
        );
      }

      const expected = complex(row === column ? 1 : 0);
      if (
        Math.abs(inner.re - expected.re) > EPSILON ||
        Math.abs(inner.im - expected.im) > EPSILON
      ) {
        return false;
      }
    }
  }

  return true;
}

const GATES = Object.freeze({
  X: Object.freeze([
    Object.freeze([complex(0), complex(1)]),
    Object.freeze([complex(1), complex(0)])
  ]),
  Z: Object.freeze([
    Object.freeze([complex(1), complex(0)]),
    Object.freeze([complex(0), complex(-1)])
  ]),
  H: Object.freeze([
    Object.freeze([complex(1 / Math.sqrt(2)), complex(1 / Math.sqrt(2))]),
    Object.freeze([complex(1 / Math.sqrt(2)), complex(-1 / Math.sqrt(2))])
  ])
});

function rotationY(theta) {
  const c = Math.cos(theta / 2);
  const s = Math.sin(theta / 2);

  return [
    [complex(c), complex(-s)],
    [complex(s), complex(c)]
  ];
}

class CircuitValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "CircuitValidationError";
  }
}

class QuantumCircuit {
  constructor(qubitCount, seed = 41) {
    if (!Number.isInteger(qubitCount) || qubitCount < 1) {
      throw new CircuitValidationError(
        "Qubit count must be a positive integer."
      );
    }

    if (qubitCount > MAX_QUBITS) {
      throw new CircuitValidationError(
        `This simulator supports at most ${MAX_QUBITS} qubits.`
      );
    }

    this.qubitCount = qubitCount;
    this.state = Array.from(
      { length: 2 ** qubitCount },
      () => complex(0)
    );
    this.state[0] = complex(1);
    this.operations = [];
    this.seed = seed >>> 0;
    this.listeners = new Map();
    this._emit("initialized", { qubitCount });
  }

  on(eventName, callback) {
    if (typeof callback !== "function") {
      throw new TypeError("Event listener must be a function.");
    }

    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, new Set());
    }

    this.listeners.get(eventName).add(callback);

    // Return an unsubscribe function to prevent leaked listeners.
    return () => this.listeners.get(eventName)?.delete(callback);
  }

  _emit(eventName, payload) {
    for (const listener of this.listeners.get(eventName) ?? []) {
      listener(Object.freeze({ ...payload }));
    }
  }

  _random() {
    // A deterministic linear congruential generator makes demonstrations
    // repeatable. It is not suitable for cryptographic randomness.
    this.seed = (1664525 * this.seed + 1013904223) >>> 0;
    return this.seed / 2 ** 32;
  }

  _validateTargets(target, controls) {
    if (!Number.isInteger(target) || target < 0 || target >= this.qubitCount) {
      throw new CircuitValidationError("Invalid target qubit.");
    }

    if (new Set(controls).size !== controls.length) {
      throw new CircuitValidationError("Control qubits must be distinct.");
    }

    for (const control of controls) {
      if (
        !Number.isInteger(control) ||
        control < 0 ||
        control >= this.qubitCount ||
        control === target
      ) {
        throw new CircuitValidationError("Invalid control qubit.");
      }
    }
  }

  applyGate(name, target, matrix, controls = []) {
    this._validateTargets(target, controls);

    if (!matrixIsUnitary(matrix)) {
      throw new CircuitValidationError("Gate matrix must be unitary.");
    }

    const next = this.state.map(amplitude => complex(amplitude.re, amplitude.im));
    const targetMask = 1 << (this.qubitCount - 1 - target);
    const controlMask = controls.reduce(
      (mask, control) => mask | (1 << (this.qubitCount - 1 - control)),
      0
    );

    for (let index = 0; index < this.state.length; index += 1) {
      if ((index & targetMask) !== 0) continue;
      if ((index & controlMask) !== controlMask) continue;

      const partner = index | targetMask;
      const a0 = this.state[index];
      const a1 = this.state[partner];

      next[index] = add(
        multiply(matrix[0][0], a0),
        multiply(matrix[0][1], a1)
      );
      next[partner] = add(
        multiply(matrix[1][0], a0),
        multiply(matrix[1][1], a1)
      );
    }

    this.state = normalize(next);
    const operation = Object.freeze({
      name,
      target,
      controls: Object.freeze([...controls])
    });
    this.operations.push(operation);
    this._emit("gate-applied", operation);
    return this;
  }

  h(target) {
    return this.applyGate("H", target, GATES.H);
  }

  x(target) {
    return this.applyGate("X", target, GATES.X);
  }

  z(target) {
    return this.applyGate("Z", target, GATES.Z);
  }

  ry(target, theta) {
    if (!Number.isFinite(theta)) {
      throw new CircuitValidationError("Rotation angle must be finite.");
    }
    return this.applyGate("RY", target, rotationY(theta));
  }

  cx(control, target) {
    return this.applyGate("CX", target, GATES.X, [control]);
  }

  mcx(controls, target) {
    return this.applyGate("MCX", target, GATES.X, controls);
  }

  probabilities() {
    return this.state.map(magnitudeSquared);
  }

  distribution() {
    const result = {};
    this.probabilities().forEach((probability, index) => {
      if (probability > EPSILON) {
        result[index.toString(2).padStart(this.qubitCount, "0")] = probability;
      }
    });
    return result;
  }

  sample() {
    const draw = this._random();
    let cumulative = 0;

    for (let index = 0; index < this.state.length; index += 1) {
      cumulative += magnitudeSquared(this.state[index]);
      if (draw < cumulative) {
        return index.toString(2).padStart(this.qubitCount, "0");
      }
    }

    return (this.state.length - 1).toString(2).padStart(this.qubitCount, "0");
  }

  runShots(shots = 1000) {
    if (!Number.isSafeInteger(shots) || shots < 1 || shots > 1_000_000) {
      throw new RangeError("Shots must be between 1 and 1,000,000.");
    }

    const counts = new Map();
    for (let shot = 0; shot < shots; shot += 1) {
      const bitstring = this.sample();
      counts.set(bitstring, (counts.get(bitstring) ?? 0) + 1);
    }

    this._emit("shots-completed", { shots, outcomes: counts.size });
    return Object.fromEntries([...counts.entries()].sort());
  }

  measure(target) {
    if (!Number.isInteger(target) || target < 0 || target >= this.qubitCount) {
      throw new CircuitValidationError("Invalid measurement target.");
    }

    const mask = 1 << (this.qubitCount - 1 - target);
    const pOne = this.state.reduce(
      (sum, amplitude, index) =>
        sum + ((index & mask) !== 0 ? magnitudeSquared(amplitude) : 0),
      0
    );

    const outcome = this._random() < pOne ? 1 : 0;
    const probability = outcome ? pOne : 1 - pOne;

    if (probability <= EPSILON) {
      throw new Error("Cannot collapse onto a zero-probability outcome.");
    }

    this.state = this.state.map((amplitude, index) => {
      if (Number(Boolean(index & mask)) !== outcome) return complex(0);
      return scale(amplitude, 1 / Math.sqrt(probability));
    });

    this._emit("measured", { target, outcome });
    return outcome;
  }
}

function demonstrateBellState() {
  const circuit = new QuantumCircuit(2, 2026);
  const auditLog = [];

  circuit.on("gate-applied", event => {
    auditLog.push(`${event.name}: q${event.target}`);
  });
  circuit.on("shots-completed", event => {
    auditLog.push(`Completed ${event.shots} measurement shots`);
  });

  circuit.h(0).cx(0, 1);

  console.log("Bell state probabilities:", circuit.distribution());
  console.log("Sampled outcomes:", circuit.runShots(2000));
  console.log("Audit events:", auditLog);

  const distribution = circuit.distribution();
  if (Math.abs(distribution["00"] - 0.5) > 1e-8) {
    throw new Error("Bell-state probability validation failed.");
  }
  if (Math.abs(distribution["11"] - 0.5) > 1e-8) {
    throw new Error("Bell-state probability validation failed.");
  }
}

function demonstrateControlledOperations() {
  const circuit = new QuantumCircuit(4);
  circuit.h(0);
  circuit.mcx([0, 1, 2], 3);

  console.log("Multi-controlled circuit:", circuit.distribution());
  console.log("Recorded operations:", circuit.operations);
}

function demonstrateParameterizedCircuit() {
  const circuit = new QuantumCircuit(2);
  circuit.ry(0, Math.PI / 3);
  circuit.cx(0, 1);

  console.log("Parameterized entangled state:", circuit.distribution());
}

function main() {
  demonstrateBellState();
  demonstrateControlledOperations();
  demonstrateParameterizedCircuit();

  try {
    new QuantumCircuit(0);
  } catch (error) {
    console.log("Expected validation failure:", error.message);
  }

  console.log("Multi-qubit circuit demonstrations completed.");
}

if (require.main === module) {
  main();
}

module.exports = {
  QuantumCircuit,
  CircuitValidationError,
  GATES,
  rotationY,
  normalize
};
