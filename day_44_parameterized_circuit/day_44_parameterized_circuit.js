"use strict";

/*
 * Parameterized quantum circuits in JavaScript.
 *
 * This implementation emphasizes event-driven parameter updates, immutable
 * circuit definitions, reusable gate templates, and batched evaluations.
 * The state-vector engine supports small circuits for educational experiments.
 */

const PI = Math.PI;

function finiteAngle(value, label = "angle") {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${label} must be a finite number.`);
  }
  return value;
}

class Parameter {
  constructor(name) {
    if (typeof name !== "string" || !/^[A-Za-z_]\w*$/.test(name)) {
      throw new TypeError("Parameter names must be valid identifiers.");
    }
    this.name = name;
    Object.freeze(this);
  }
}

class AngleExpression {
  constructor(evaluate, parameterNames, description) {
    this.evaluate = evaluate;
    this.parameterNames = new Set(parameterNames);
    this.description = description;
    Object.freeze(this);
  }

  static parameter(parameter) {
    return new AngleExpression(
      (bindings) => {
        if (!Object.hasOwn(bindings, parameter.name)) {
          throw new Error(`Unbound parameter: ${parameter.name}`);
        }
        return finiteAngle(bindings[parameter.name], parameter.name);
      },
      [parameter.name],
      parameter.name
    );
  }

  static constant(value) {
    const angle = finiteAngle(value);
    return new AngleExpression(() => angle, [], String(angle));
  }

  add(other) {
    const right = asExpression(other);
    return new AngleExpression(
      (bindings) => finiteAngle(this.evaluate(bindings) + right.evaluate(bindings)),
      [...this.parameterNames, ...right.parameterNames],
      `(${this.description} + ${right.description})`
    );
  }

  multiply(other) {
    const right = asExpression(other);
    return new AngleExpression(
      (bindings) => finiteAngle(this.evaluate(bindings) * right.evaluate(bindings)),
      [...this.parameterNames, ...right.parameterNames],
      `(${this.description} * ${right.description})`
    );
  }
}

function asExpression(value) {
  if (value instanceof AngleExpression) return value;
  if (value instanceof Parameter) return AngleExpression.parameter(value);
  return AngleExpression.constant(value);
}

class CircuitTemplate {
  constructor(qubits, name = "circuit-template") {
    if (!Number.isInteger(qubits) || qubits < 1 || qubits > 12) {
      throw new RangeError("Use an integer qubit count from 1 through 12.");
    }
    this.qubits = qubits;
    this.name = name;
    this.parameters = new Map();
    this.gates = [];
  }

  parameter(name) {
    if (!this.parameters.has(name)) {
      this.parameters.set(name, new Parameter(name));
    }
    return this.parameters.get(name);
  }

  checkQubit(qubit) {
    if (!Number.isInteger(qubit) || qubit < 0 || qubit >= this.qubits) {
      throw new RangeError(`Invalid qubit index: ${qubit}`);
    }
  }

  rotation(gate, qubit, angle) {
    this.checkQubit(qubit);
    const expression = asExpression(angle);
    for (const name of expression.parameterNames) {
      if (!this.parameters.has(name)) {
        this.parameters.set(name, new Parameter(name));
      }
    }
    this.gates.push(Object.freeze({ gate, qubit, expression }));
    return this;
  }

  rx(qubit, angle) {
    return this.rotation("RX", qubit, angle);
  }

  ry(qubit, angle) {
    return this.rotation("RY", qubit, angle);
  }

  rz(qubit, angle) {
    return this.rotation("RZ", qubit, angle);
  }

  h(qubit) {
    this.checkQubit(qubit);
    this.gates.push(Object.freeze({ gate: "H", qubit }));
    return this;
  }

  cnot(control, target) {
    this.checkQubit(control);
    this.checkQubit(target);
    if (control === target) {
      throw new RangeError("CNOT control and target must differ.");
    }
    this.gates.push(Object.freeze({ gate: "CNOT", control, target }));
    return this;
  }

  bind(values) {
    const names = new Set(this.parameters.keys());
    for (const name of Object.keys(values)) {
      if (!names.has(name)) throw new Error(`Unknown parameter: ${name}`);
      finiteAngle(values[name], name);
    }
    for (const name of names) {
      if (!Object.hasOwn(values, name)) throw new Error(`Missing parameter: ${name}`);
    }

    const boundGates = this.gates.map((gate) => {
      if (!gate.expression) return { ...gate };
      return {
        gate: gate.gate,
        qubit: gate.qubit,
        angle: finiteAngle(gate.expression.evaluate(values))
      };
    });

    return new BoundCircuit(this.qubits, boundGates, { ...values });
  }

  describe() {
    return this.gates.map((gate, index) => {
      if (gate.gate === "CNOT") {
        return `${index}: CNOT q${gate.control} -> q${gate.target}`;
      }
      const angle = gate.expression ? gate.expression.description : "";
      return `${index}: ${gate.gate} q${gate.qubit} ${angle}`.trim();
    }).join("\n");
  }
}

class BoundCircuit {
  constructor(qubits, gates, bindings) {
    this.qubits = qubits;
    this.gates = gates;
    this.bindings = bindings;
  }

  simulate() {
    let state = Array.from(
      { length: 2 ** this.qubits },
      (_, index) => index === 0 ? [1, 0] : [0, 0]
    );

    for (const gate of this.gates) {
      if (gate.gate === "CNOT") {
        state = applyCnot(state, gate.control, gate.target);
      } else if (gate.gate === "H") {
        state = applyHadamard(state, gate.qubit);
      } else {
        state = applyRotation(state, gate.gate, gate.qubit, gate.angle);
      }
    }
    return state;
  }

  probabilities() {
    return this.simulate().map(([real, imaginary]) => real * real + imaginary * imaginary);
  }

  expectationZ(qubit) {
    if (!Number.isInteger(qubit) || qubit < 0 || qubit >= this.qubits) {
      throw new RangeError("Invalid measurement qubit.");
    }
    return this.probabilities().reduce((sum, probability, index) => {
      const bit = (index >> qubit) & 1;
      return sum + (bit === 0 ? probability : -probability);
    }, 0);
  }
}

function multiplyComplex([ar, ai], [br, bi]) {
  return [ar * br - ai * bi, ar * bi + ai * br];
}

function addComplex([ar, ai], [br, bi]) {
  return [ar + br, ai + bi];
}

function scaleComplex([real, imaginary], scale) {
  return [real * scale, imaginary * scale];
}

function applyRotation(state, gate, qubit, angle) {
  const cosine = Math.cos(angle / 2);
  const sine = Math.sin(angle / 2);
  const output = state.map((amplitude) => [...amplitude]);
  const stride = 2 ** qubit;

  for (let base = 0; base < state.length; base += 2 * stride) {
    for (let offset = 0; offset < stride; offset++) {
      const first = base + offset;
      const second = first + stride;
      const [a, b] = [state[first], state[second]];

      if (gate === "RX") {
        output[first] = addComplex(scaleComplex(a, cosine),
          scaleComplex(multiplyComplex([0, -1], b), sine));
        output[second] = addComplex(
          scaleComplex(multiplyComplex([0, -1], a), sine),
          scaleComplex(b, cosine)
        );
      } else if (gate === "RY") {
        output[first] = addComplex(scaleComplex(a, cosine), scaleComplex(b, -sine));
        output[second] = addComplex(scaleComplex(a, sine), scaleComplex(b, cosine));
      } else if (gate === "RZ") {
        output[first] = multiplyComplex([cosine, -sine], a);
        output[second] = multiplyComplex([cosine, sine], b);
      } else {
        throw new Error(`Unsupported gate: ${gate}`);
      }
    }
  }
  return output;
}

function applyHadamard(state, qubit) {
  const output = state.map((amplitude) => [...amplitude]);
  const stride = 2 ** qubit;
  const scale = 1 / Math.sqrt(2);

  for (let base = 0; base < state.length; base += 2 * stride) {
    for (let offset = 0; offset < stride; offset++) {
      const first = base + offset;
      const second = first + stride;
      const a = state[first];
      const b = state[second];
      output[first] = scaleComplex(addComplex(a, b), scale);
      output[second] = scaleComplex(addComplex(a, scaleComplex(b, -1)), scale);
    }
  }
  return output;
}

function applyCnot(state, control, target) {
  const output = state.map((amplitude) => [...amplitude]);
  const controlMask = 1 << control;
  const targetMask = 1 << target;

  for (let index = 0; index < state.length; index++) {
    if ((index & controlMask) !== 0 && (index & targetMask) === 0) {
      const other = index | targetMask;
      output[index] = [...state[other]];
      output[other] = [...state[index]];
    }
  }
  return output;
}

/*
 * A parameter-update service emits evaluation events. In a UI, a slider or
 * optimization loop could update the values without rebuilding the template.
 */
class ParameterEvaluationService {
  constructor(template, initialValues) {
    this.template = template;
    this.values = { ...initialValues };
    this.listeners = new Set();
    this.revision = 0;
    this.evaluate();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  update(name, value) {
    if (!this.template.parameters.has(name)) {
      throw new Error(`Cannot update unknown parameter: ${name}`);
    }
    const next = { ...this.values, [name]: finiteAngle(value, name) };
    // Bind before publishing to prevent invalid parameter sets reaching listeners.
    const bound = this.template.bind(next);
    this.values = next;
    this.revision++;
    const event = Object.freeze({
      revision: this.revision,
      values: Object.freeze({ ...next }),
      probabilities: Object.freeze(bound.probabilities())
    });
    for (const listener of this.listeners) listener(event);
    return event;
  }

  evaluate() {
    return this.template.bind(this.values);
  }
}

function buildCircuit() {
  const circuit = new CircuitTemplate(2, "quantum-feature-map");
  const data = circuit.parameter("data");
  const theta = circuit.parameter("theta");
  const phi = circuit.parameter("phi");

  circuit.h(0)
    .ry(0, data)
    .rx(1, theta)
    .cnot(0, 1)
    .rz(0, phi.add(theta.multiply(0.5)))
    .ry(1, data.multiply(2));
  return circuit;
}

function assertClose(actual, expected, tolerance = 1e-8) {
  if (Math.abs(actual - expected) > tolerance) {
    throw new Error(`Expected ${expected}, received ${actual}`);
  }
}

function main() {
  const circuit = buildCircuit();
  const initial = { data: 0.7, theta: -0.4, phi: 0.2 };

  console.log(circuit.describe());
  const service = new ParameterEvaluationService(circuit, initial);

  const unsubscribe = service.subscribe((event) => {
    console.log(`\nEvaluation revision ${event.revision}`);
    console.log("Parameters:", event.values);
    console.log("Probabilities:", event.probabilities.map((p) => p.toFixed(6)));
  });

  service.update("theta", 0.15);
  service.update("data", 1.1);
  unsubscribe();

  const probabilities = service.evaluate().probabilities();
  assertClose(probabilities.reduce((sum, value) => sum + value, 0), 1);

  try {
    service.update("phi", Number.NaN);
  } catch (error) {
    console.log("\nRejected invalid update:", error.message);
  }

  try {
    circuit.bind({ data: 0.1, theta: 0.2 });
  } catch (error) {
    console.log("Rejected incomplete binding:", error.message);
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  Parameter,
  AngleExpression,
  CircuitTemplate,
  BoundCircuit,
  ParameterEvaluationService,
  buildCircuit
};
