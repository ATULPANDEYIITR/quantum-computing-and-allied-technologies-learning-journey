"use strict";

/*
 * Quantum SDK Landscape
 *
 * This Node.js program models a quantum SDK selection and interoperability
 * layer. It deliberately avoids npm dependencies so that the architecture
 * can be executed locally while still representing distinctions between
 * Qiskit, Cirq, PennyLane, pytket/TKET, Amazon Braket, CUDA-Q, and Microsoft
 * QDK/Q#.
 *
 * The JavaScript-specific perspective is event-driven: a circuit execution
 * emits lifecycle events, and an asynchronous scheduler evaluates workloads
 * against SDK capabilities.
 */

const { EventEmitter } = require("node:events");

const SDK = Object.freeze({
  QISKIT: "Qiskit",
  CIRQ: "Cirq",
  PENNYLANE: "PennyLane",
  PYTKET: "pytket / TKET",
  BRAKET: "Amazon Braket SDK",
  CUDA_Q: "CUDA-Q",
  QDK: "Microsoft QDK / Q#"
});

const sdkCatalog = [
  {
    name: SDK.QISKIT,
    organization: "IBM",
    languages: ["Python"],
    abstractions: ["circuit", "transpilation", "cloud execution"],
    workloads: ["general circuits", "hardware compilation", "cloud execution", "research"],
    differentiable: false,
    compiler: true,
    hardware: true,
    cloud: true,
    simulation: true,
    strengths: [
      "circuit construction and transpilation",
      "IBM hardware integration",
      "primitive-oriented sampling and expectation-value workflows"
    ],
    tradeoffs: [
      "provider APIs and service packages evolve independently",
      "hardware results depend heavily on backend-aware compilation"
    ]
  },
  {
    name: SDK.CIRQ,
    organization: "Google Quantum AI",
    languages: ["Python"],
    abstractions: ["moment-oriented circuit"],
    workloads: ["general circuits", "hardware compilation", "research"],
    differentiable: false,
    compiler: true,
    hardware: true,
    cloud: false,
    simulation: true,
    strengths: [
      "explicit qubit and moment control",
      "research-oriented circuit representation",
      "hardware-aware experiments"
    ],
    tradeoffs: [
      "strongest fit is circuit research rather than generic cloud orchestration",
      "Google-specific hardware workflows may require additional components"
    ]
  },
  {
    name: SDK.PENNYLANE,
    organization: "Xanadu",
    languages: ["Python"],
    abstractions: ["quantum functions", "automatic differentiation"],
    workloads: ["QML", "variational algorithms", "research", "hybrid computing"],
    differentiable: true,
    compiler: true,
    hardware: true,
    cloud: false,
    simulation: true,
    strengths: [
      "differentiable quantum programming",
      "quantum machine learning",
      "hybrid optimization",
      "multi-backend device abstraction"
    ],
    tradeoffs: [
      "gradient execution cost depends on device and differentiation method",
      "device-specific features are not uniformly portable"
    ]
  },
  {
    name: SDK.PYTKET,
    organization: "Quantinuum",
    languages: ["Python API", "C++ compiler core"],
    abstractions: ["compiler", "intermediate representation"],
    workloads: ["hardware compilation", "optimization", "research"],
    differentiable: false,
    compiler: true,
    hardware: true,
    cloud: false,
    simulation: true,
    strengths: [
      "architecture-aware compilation",
      "routing and placement",
      "optimization passes",
      "interoperability extensions"
    ],
    tradeoffs: [
      "primarily a compilation and interoperability layer",
      "provider access may be supplied through extension packages"
    ]
  },
  {
    name: SDK.BRAKET,
    organization: "AWS",
    languages: ["Python"],
    abstractions: ["provider-neutral circuit", "cloud task", "hybrid job"],
    workloads: ["cloud execution", "general circuits", "research"],
    differentiable: false,
    compiler: false,
    hardware: true,
    cloud: true,
    simulation: true,
    strengths: [
      "managed multi-provider cloud access",
      "hybrid jobs",
      "AWS infrastructure integration"
    ],
    tradeoffs: [
      "cloud, region, queue, permissions, and cost affect execution",
      "target capabilities vary across providers"
    ]
  },
  {
    name: SDK.CUDA_Q,
    organization: "NVIDIA",
    languages: ["C++", "Python"],
    abstractions: ["hybrid kernel", "GPU/QPU execution"],
    workloads: ["GPU simulation", "hybrid computing", "hardware compilation", "research"],
    differentiable: false,
    compiler: true,
    hardware: true,
    cloud: false,
    simulation: true,
    strengths: [
      "GPU-accelerated simulation",
      "hybrid CPU/GPU/QPU execution",
      "multiple simulator and hardware backends"
    ],
    tradeoffs: [
      "benefits depend on access to suitable accelerated infrastructure",
      "backend feature coverage varies"
    ]
  },
  {
    name: SDK.QDK,
    organization: "Microsoft",
    languages: ["Q#", "Python"],
    abstractions: ["quantum language", "resource estimation", "cloud execution"],
    workloads: ["resource estimation", "cloud execution", "research", "general circuits"],
    differentiable: false,
    compiler: true,
    hardware: true,
    cloud: true,
    simulation: true,
    strengths: [
      "dedicated Q# programming language",
      "resource estimation",
      "simulation and debugging",
      "Azure Quantum integration"
    ],
    tradeoffs: [
      "Q# has a distinct programming model",
      "cloud execution requires target/workspace configuration"
    ]
  }
];

class Gate {
  constructor(name, qubits, parameter = null) {
    if (!name || !Array.isArray(qubits) || qubits.length === 0) {
      throw new TypeError("A gate requires a name and at least one target qubit");
    }
    this.name = name;
    this.qubits = Object.freeze([...qubits]);
    this.parameter = parameter;
  }

  toString() {
    const parameter = this.parameter === null ? "" : `(${this.parameter.toFixed(4)})`;
    return `${this.name}${parameter}[${this.qubits.map(q => `q${q}`).join(",")}]`;
  }
}

class Circuit {
  constructor(qubitCount) {
    if (!Number.isInteger(qubitCount) || qubitCount <= 0) {
      throw new RangeError("qubitCount must be a positive integer");
    }
    this.qubitCount = qubitCount;
    this.gates = [];
  }

  addGate(name, ...qubits) {
    const parameters =
      qubits.length > 0 && typeof qubits[qubits.length - 1] === "object"
        ? qubits.pop()
        : {};

    if (qubits.some(q => !Number.isInteger(q) || q < 0 || q >= this.qubitCount)) {
      throw new RangeError("Gate contains an invalid qubit index");
    }

    if (new Set(qubits).size !== qubits.length) {
      throw new Error("A gate cannot target the same qubit twice");
    }

    this.gates.push(new Gate(name, qubits, parameters.parameter ?? null));
    return this;
  }

  depth() {
    const availability = Array(this.qubitCount).fill(0);

    for (const gate of this.gates) {
      const layer = Math.max(...gate.qubits.map(q => availability[q])) + 1;
      for (const q of gate.qubits) {
        availability[q] = layer;
      }
    }

    return Math.max(0, ...availability);
  }

  twoQubitGateCount() {
    return this.gates.filter(gate => gate.qubits.length === 2).length;
  }

  parameterCount() {
    return this.gates.filter(gate => gate.parameter !== null).length;
  }

  describe() {
    return this.gates.map((gate, i) => `  ${String(i + 1).padStart(2, "0")}: ${gate}`).join("\n");
  }
}

class QuantumExecution extends EventEmitter {
  constructor(circuit, sdk) {
    super();
    this.circuit = circuit;
    this.sdk = sdk;
    this.status = "created";
    this.result = null;
  }

  async run(shots = 1000) {
    if (!Number.isInteger(shots) || shots <= 0) {
      throw new RangeError("shots must be a positive integer");
    }

    this.status = "queued";
    this.emit("queued", { sdk: this.sdk.name, shots });

    await new Promise(resolve => setTimeout(resolve, 10));

    this.status = "running";
    this.emit("running", {
      sdk: this.sdk.name,
      gateCount: this.circuit.gates.length
    });

    await new Promise(resolve => setTimeout(resolve, 10));

    if (
      this.circuit.qubitCount === 2 &&
      this.circuit.gates.map(g => g.name).join(",") === "H,CX"
    ) {
      const zeros = Math.floor(shots / 2);
      const ones = shots - zeros;
      this.result = { "00": zeros, "11": ones };
    } else {
      this.result = { unsupported: shots };
    }

    this.status = "completed";
    this.emit("completed", { result: this.result });
    return this.result;
  }
}

function bellCircuit() {
  return new Circuit(2)
    .addGate("H", 0)
    .addGate("CX", 0, 1);
}

function variationalCircuit(theta) {
  return new Circuit(3)
    .addGate("RY", 0, { parameter: theta })
    .addGate("RY", 1, { parameter: theta / 2 })
    .addGate("RY", 2, { parameter: -theta })
    .addGate("CX", 0, 1)
    .addGate("CX", 1, 2);
}

function workloadScore(sdk, workload) {
  let score = 0;
  const reasons = [];

  if (sdk.workloads.includes(workload.type)) {
    score += 4;
    reasons.push("workload alignment");
  }

  if (workload.differentiable) {
    score += sdk.differentiable ? 5 : -3;
    reasons.push(sdk.differentiable
      ? "native differentiable programming"
      : "not primarily differentiable");
  }

  if (workload.gpu) {
    if (sdk.name === SDK.CUDA_Q) {
      score += 6;
      reasons.push("GPU-oriented simulation/hybrid execution");
    }
  }

  if (workload.cloud) {
    score += sdk.cloud ? 4 : -1;
    reasons.push(sdk.cloud ? "managed cloud execution" : "no primary cloud orchestration layer");
  }

  if (workload.compiler) {
    score += sdk.compiler ? 5 : -1;
    reasons.push(sdk.compiler ? "compiler-oriented capabilities" : "not compiler-centric");
  }

  if (workload.resourceEstimation) {
    score += sdk.name === SDK.QDK ? 6 : -1;
    reasons.push(
      sdk.name === SDK.QDK
        ? "dedicated resource-estimation workflow"
        : "resource estimation is not the primary differentiator"
    );
  }

  return { score, reasons };
}

function recommend(workload) {
  return sdkCatalog
    .map(sdk => ({ sdk, ...workloadScore(sdk, workload) }))
    .sort((a, b) => b.score - a.score || a.sdk.name.localeCompare(b.sdk.name));
}

async function demonstrateEventDrivenExecution() {
  console.log("\nEVENT-DRIVEN CIRCUIT EXECUTION");
  console.log("=".repeat(78));

  const circuit = bellCircuit();
  const execution = new QuantumExecution(circuit, sdkCatalog.find(s => s.name === SDK.QISKIT));

  execution.on("queued", event => {
    console.log(`queued -> ${event.sdk}, shots=${event.shots}`);
  });

  execution.on("running", event => {
    console.log(`running -> ${event.gateCount} gates`);
  });

  execution.on("completed", event => {
    console.log(`completed -> ${JSON.stringify(event.result)}`);
  });

  await execution.run(1000);
}

function printLandscape() {
  console.log("QUANTUM SDK LANDSCAPE");
  console.log("=".repeat(78));

  for (const sdk of sdkCatalog) {
    console.log(`\n${sdk.name} | ${sdk.organization}`);
    console.log(`Languages: ${sdk.languages.join(", ")}`);
    console.log(`Abstractions: ${sdk.abstractions.join(", ")}`);
    console.log(`Workloads: ${sdk.workloads.join(", ")}`);
    console.log(`Differentiable: ${sdk.differentiable}`);
    console.log(`Compiler: ${sdk.compiler}`);
    console.log(`Hardware: ${sdk.hardware}`);
    console.log(`Cloud: ${sdk.cloud}`);
    console.log(`Simulation: ${sdk.simulation}`);
    console.log("Strengths:");
    sdk.strengths.forEach(item => console.log(`  - ${item}`));
    console.log("Trade-offs:");
    sdk.tradeoffs.forEach(item => console.log(`  - ${item}`));
  }
}

function printCircuitExamples() {
  console.log("\nCIRCUIT MODELS");
  console.log("=".repeat(78));

  const bell = bellCircuit();
  console.log("\nBell circuit:");
  console.log(bell.describe());
  console.log(`Depth: ${bell.depth()}`);
  console.log(`Two-qubit gates: ${bell.twoQubitGateCount()}`);

  const ansatz = variationalCircuit(Math.PI / 3);
  console.log("\nParameterized variational circuit:");
  console.log(ansatz.describe());
  console.log(`Depth: ${ansatz.depth()}`);
  console.log(`Parameterized gates: ${ansatz.parameterCount()}`);
}

function printRecommendations() {
  console.log("\nWORKLOAD SELECTION");
  console.log("=".repeat(78));

  const workloads = [
    {
      name: "Variational quantum machine learning",
      type: "QML",
      differentiable: true
    },
    {
      name: "Architecture-aware circuit optimization",
      type: "hardware compilation",
      compiler: true
    },
    {
      name: "Managed multi-provider execution",
      type: "cloud execution",
      cloud: true
    },
    {
      name: "GPU-accelerated simulation",
      type: "GPU simulation",
      gpu: true
    },
    {
      name: "Fault-tolerant resource estimation",
      type: "resource estimation",
      resourceEstimation: true
    }
  ];

  for (const workload of workloads) {
    console.log(`\n${workload.name}`);
    for (const recommendation of recommend(workload).slice(0, 3)) {
      console.log(
        `  ${recommendation.sdk.name.padEnd(24)} ` +
        `score=${String(recommendation.score).padStart(2)} ` +
        recommendation.reasons.join("; ")
      );
    }
  }
}

function demonstrateValidation() {
  console.log("\nVALIDATION AND FAILURE MODES");
  console.log("=".repeat(78));

  try {
    new Circuit(2).addGate("CX", 0, 2);
  } catch (error) {
    console.log(`Invalid qubit rejected: ${error.message}`);
  }

  try {
    new Circuit(2).addGate("CX", 1, 1);
  } catch (error) {
    console.log(`Duplicate target rejected: ${error.message}`);
  }

  try {
    new QuantumExecution(bellCircuit(), sdkCatalog[0]).run(0);
  } catch (error) {
    console.log(`Invalid shot count rejected: ${error.message}`);
  }
}

async function main() {
  printLandscape();
  printCircuitExamples();
  printRecommendations();
  demonstrateValidation();
  await demonstrateEventDrivenExecution();
}

main().catch(error => {
  console.error(`Execution failed: ${error.message}`);
  process.exitCode = 1;
});
