#!/usr/bin/env python3
"""
Quantum SDK Landscape
=====================

A dependency-free technical model of the major quantum SDK families:
Qiskit, Cirq, PennyLane, pytket/TKET, Amazon Braket, CUDA-Q, and
Microsoft QDK/Q#.

This program intentionally models SDK capabilities rather than requiring
live cloud credentials or vendor-specific packages. It demonstrates how
to compare quantum SDKs by abstraction level, circuit model, compilation,
simulation, differentiation, hardware access, interoperability, and
hybrid-computing characteristics.

The model also contains a small circuit intermediate representation and
a workload-to-SDK selection engine so the landscape can be explored
through executable behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, defaultdict
from typing import Callable, Iterable, Optional
import math
import random


class Abstraction(Enum):
    CIRCUIT = "gate-level circuit"
    DIFFERENTIABLE = "differentiable hybrid"
    COMPILER = "compiler/intermediate representation"
    CLOUD = "cloud orchestration"
    LANGUAGE = "quantum programming language"
    HYBRID = "hybrid CPU/GPU/QPU"


class WorkloadType(Enum):
    GENERAL_CIRCUITS = "general circuit development"
    HARDWARE_COMPILATION = "hardware-aware compilation"
    QML = "quantum machine learning"
    CLOUD_EXECUTION = "managed cloud execution"
    GPU_SIMULATION = "accelerated simulation"
    RESOURCE_ESTIMATION = "resource estimation"
    RESEARCH = "quantum research"


@dataclass(frozen=True)
class SDK:
    name: str
    organization: str
    primary_language: str
    abstractions: frozenset[Abstraction]
    workloads: frozenset[WorkloadType]
    circuit_model: str
    differentiable: bool
    compiler_focus: bool
    hardware_access: bool
    simulator_focus: bool
    cloud_orchestration: bool
    interoperability: tuple[str, ...]
    strengths: tuple[str, ...]
    tradeoffs: tuple[str, ...]
    typical_role: str


SDK_LANDSCAPE = (
    SDK(
        name="Qiskit",
        organization="IBM",
        primary_language="Python",
        abstractions=frozenset({Abstraction.CIRCUIT, Abstraction.CLOUD}),
        workloads=frozenset({
            WorkloadType.GENERAL_CIRCUITS,
            WorkloadType.CLOUD_EXECUTION,
            WorkloadType.RESEARCH,
            WorkloadType.HARDWARE_COMPILATION,
        }),
        circuit_model="QuantumCircuit plus transpilation and primitive-oriented execution",
        differentiable=False,
        compiler_focus=True,
        hardware_access=True,
        simulator_focus=True,
        cloud_orchestration=True,
        interoperability=("OpenQASM", "pytket", "Azure Quantum", "IBM Quantum"),
        strengths=(
            "mature circuit construction and transpilation",
            "strong IBM hardware integration",
            "primitive-oriented execution through Sampler and Estimator interfaces",
            "large ecosystem for quantum information and experiments",
        ),
        tradeoffs=(
            "provider-specific execution APIs can evolve independently of the core SDK",
            "hardware performance depends strongly on transpilation and backend topology",
        ),
        typical_role="general-purpose circuit development and IBM-oriented hardware workflows",
    ),
    SDK(
        name="Cirq",
        organization="Google Quantum AI",
        primary_language="Python",
        abstractions=frozenset({Abstraction.CIRCUIT}),
        workloads=frozenset({
            WorkloadType.GENERAL_CIRCUITS,
            WorkloadType.RESEARCH,
            WorkloadType.HARDWARE_COMPILATION,
        }),
        circuit_model="Moment-oriented circuit representation with explicit qubits and operations",
        differentiable=False,
        compiler_focus=True,
        hardware_access=True,
        simulator_focus=True,
        cloud_orchestration=False,
        interoperability=("OpenQASM", "Qsim", "Google Quantum AI"),
        strengths=(
            "fine-grained control of circuits and moments",
            "strong research-oriented representation",
            "natural fit for hardware-aware circuit experiments",
        ),
        tradeoffs=(
            "ecosystem emphasis differs from the broader application focus of Qiskit",
            "hardware workflows often depend on Google-specific components",
        ),
        typical_role="research and hardware-oriented circuit experimentation",
    ),
    SDK(
        name="PennyLane",
        organization="Xanadu",
        primary_language="Python",
        abstractions=frozenset({Abstraction.DIFFERENTIABLE, Abstraction.CIRCUIT}),
        workloads=frozenset({
            WorkloadType.QML,
            WorkloadType.RESEARCH,
            WorkloadType.GENERAL_CIRCUITS,
            WorkloadType.CLOUD_EXECUTION,
        }),
        circuit_model="device-independent quantum functions integrated with autodifferentiation",
        differentiable=True,
        compiler_focus=True,
        hardware_access=True,
        simulator_focus=True,
        cloud_orchestration=False,
        interoperability=("Qiskit", "Cirq", "Amazon Braket", "PyTorch", "JAX", "NumPy"),
        strengths=(
            "differentiable quantum programming",
            "variational algorithms and quantum machine learning",
            "device abstraction across multiple backends",
            "hybrid quantum-classical optimization",
        ),
        tradeoffs=(
            "automatic differentiation introduces execution and gradient-method considerations",
            "backend capabilities differ across devices",
        ),
        typical_role="variational algorithms, QML, and differentiable hybrid computation",
    ),
    SDK(
        name="pytket / TKET",
        organization="Quantinuum",
        primary_language="Python API with C++ compiler core",
        abstractions=frozenset({Abstraction.COMPILER, Abstraction.CIRCUIT}),
        workloads=frozenset({
            WorkloadType.HARDWARE_COMPILATION,
            WorkloadType.GENERAL_CIRCUITS,
            WorkloadType.RESEARCH,
        }),
        circuit_model="platform-agnostic circuit IR plus optimization and architecture-aware compilation",
        differentiable=False,
        compiler_focus=True,
        hardware_access=True,
        simulator_focus=True,
        cloud_orchestration=False,
        interoperability=("Qiskit", "Cirq", "pyQuil", "Braket", "QIR"),
        strengths=(
            "hardware-aware compilation",
            "placement and routing",
            "optimization passes",
            "broad interoperability through extensions",
        ),
        tradeoffs=(
            "best used as a compiler layer rather than as a complete ML framework",
            "provider integrations can have separate extension packages",
        ),
        typical_role="cross-platform compilation and circuit optimization",
    ),
    SDK(
        name="Amazon Braket SDK",
        organization="AWS",
        primary_language="Python",
        abstractions=frozenset({Abstraction.CLOUD, Abstraction.CIRCUIT}),
        workloads=frozenset({
            WorkloadType.CLOUD_EXECUTION,
            WorkloadType.GENERAL_CIRCUITS,
            WorkloadType.RESEARCH,
        }),
        circuit_model="provider-neutral circuits and managed quantum tasks",
        differentiable=False,
        compiler_focus=False,
        hardware_access=True,
        simulator_focus=True,
        cloud_orchestration=True,
        interoperability=("PennyLane", "OpenQASM", "AWS cloud devices"),
        strengths=(
            "managed multi-provider cloud execution",
            "hybrid jobs",
            "integration with AWS infrastructure",
            "common API for simulators and QPUs",
        ),
        tradeoffs=(
            "cloud execution introduces account, region, queue, and cost dependencies",
            "device capabilities differ substantially between providers",
        ),
        typical_role="cloud-based multi-provider quantum workloads",
    ),
    SDK(
        name="CUDA-Q",
        organization="NVIDIA",
        primary_language="C++ and Python",
        abstractions=frozenset({Abstraction.HYBRID, Abstraction.COMPILER}),
        workloads=frozenset({
            WorkloadType.GPU_SIMULATION,
            WorkloadType.HARDWARE_COMPILATION,
            WorkloadType.GENERAL_CIRCUITS,
            WorkloadType.RESEARCH,
        }),
        circuit_model="kernel-oriented hybrid quantum-classical programming",
        differentiable=False,
        compiler_focus=True,
        hardware_access=True,
        simulator_focus=True,
        cloud_orchestration=False,
        interoperability=("CUDA", "QIR", "multiple hardware backends"),
        strengths=(
            "GPU-accelerated simulation",
            "hybrid CPU/GPU/QPU workflows",
            "multiple simulator and hardware backends",
            "C++ and Python development",
        ),
        tradeoffs=(
            "best value appears in workloads that benefit from accelerated classical infrastructure",
            "hardware backend availability varies by environment",
        ),
        typical_role="high-performance hybrid quantum-classical computing",
    ),
    SDK(
        name="Microsoft QDK / Q#",
        organization="Microsoft",
        primary_language="Q# and Python",
        abstractions=frozenset({Abstraction.LANGUAGE, Abstraction.CLOUD}),
        workloads=frozenset({
            WorkloadType.RESOURCE_ESTIMATION,
            WorkloadType.CLOUD_EXECUTION,
            WorkloadType.GENERAL_CIRCUITS,
            WorkloadType.RESEARCH,
        }),
        circuit_model="hardware-agnostic quantum language and Python/Q# development model",
        differentiable=False,
        compiler_focus=True,
        hardware_access=True,
        simulator_focus=True,
        cloud_orchestration=True,
        interoperability=("OpenQASM", "Qiskit", "Cirq", "PennyLane", "Azure Quantum"),
        strengths=(
            "dedicated quantum language",
            "resource estimation",
            "simulation and debugging",
            "Azure Quantum integration",
        ),
        tradeoffs=(
            "Q# introduces a distinct language model that differs from Python-first SDKs",
            "execution depends on Azure Quantum workspace and target configuration for cloud workloads",
        ),
        typical_role="language-oriented quantum development and resource estimation",
    ),
)


@dataclass
class Gate:
    name: str
    qubits: tuple[int, ...]
    parameter: Optional[float] = None

    def __str__(self) -> str:
        parameter = "" if self.parameter is None else f"({self.parameter:.4f})"
        targets = ",".join(f"q{q}" for q in self.qubits)
        return f"{self.name}{parameter} [{targets}]"


@dataclass
class Circuit:
    qubits: int
    gates: list[Gate] = field(default_factory=list)

    def add(self, name: str, *qubits: int, parameter: Optional[float] = None) -> "Circuit":
        if not qubits:
            raise ValueError("At least one qubit is required")
        if any(q < 0 or q >= self.qubits for q in qubits):
            raise ValueError("Gate references a qubit outside the circuit")
        if len(set(qubits)) != len(qubits):
            raise ValueError("A gate cannot reference the same qubit twice")
        self.gates.append(Gate(name, tuple(qubits), parameter))
        return self

    def depth(self) -> int:
        """Compute a simple scheduling depth by tracking each qubit's last layer."""
        available = [0] * self.qubits
        for gate in self.gates:
            layer = max(available[q] for q in gate.qubits) + 1
            for q in gate.qubits:
                available[q] = layer
        return max(available, default=0)

    def two_qubit_gate_count(self) -> int:
        return sum(len(g.qubits) == 2 for g in self.gates)

    def parameter_count(self) -> int:
        return sum(g.parameter is not None for g in self.gates)

    def describe(self) -> str:
        return "\n".join(f"  {index:02d}: {gate}" for index, gate in enumerate(self.gates, 1))


def bell_circuit() -> Circuit:
    """A minimal circuit used to compare how SDKs represent the same computation."""
    return Circuit(2).add("H", 0).add("CX", 0, 1)


def variational_circuit(theta: float) -> Circuit:
    """A tiny parameterized ansatz representative of VQE/QML workloads."""
    return (
        Circuit(3)
        .add("RY", 0, parameter=theta)
        .add("RY", 1, parameter=theta / 2)
        .add("RY", 2, parameter=-theta)
        .add("CX", 0, 1)
        .add("CX", 1, 2)
    )


@dataclass(frozen=True)
class Workload:
    name: str
    type: WorkloadType
    requires_differentiation: bool = False
    requires_gpu: bool = False
    requires_cloud: bool = False
    requires_hardware_compiler: bool = False
    requires_resource_estimation: bool = False


def score_sdk(sdk: SDK, workload: Workload) -> tuple[int, list[str]]:
    """Score an SDK against explicit technical requirements.

    This is a transparent heuristic, not a benchmark. Real selection should
    also account for target hardware, licensing, queue behavior, cost,
    version compatibility, and the exact algorithm.
    """
    score = 0
    reasons: list[str] = []

    if workload.type in sdk.workloads:
        score += 4
        reasons.append("workload matches the SDK's primary use")
    if workload.requires_differentiation:
        if sdk.differentiable:
            score += 5
            reasons.append("native differentiable-programming orientation")
        else:
            score -= 3
            reasons.append("no primary differentiable-programming model")
    if workload.requires_gpu:
        if sdk.name == "CUDA-Q":
            score += 6
            reasons.append("GPU-oriented hybrid execution and simulation")
        elif sdk.simulator_focus:
            score += 1
    if workload.requires_cloud:
        if sdk.cloud_orchestration:
            score += 4
            reasons.append("managed cloud execution model")
        else:
            score -= 1
    if workload.requires_hardware_compiler:
        if sdk.compiler_focus:
            score += 5
            reasons.append("explicit compilation focus")
    if workload.requires_resource_estimation:
        if sdk.name == "Microsoft QDK / Q#":
            score += 6
            reasons.append("dedicated resource-estimation workflow")
        else:
            score -= 1

    return score, reasons


def recommend(workload: Workload, limit: int = 4) -> list[tuple[SDK, int, list[str]]]:
    ranked = []
    for sdk in SDK_LANDSCAPE:
        score, reasons = score_sdk(sdk, workload)
        ranked.append((sdk, score, reasons))
    ranked.sort(key=lambda item: (-item[1], item[0].name))
    return ranked[:limit]


def simulate_measurement(circuit: Circuit, shots: int = 1024) -> Counter[str]:
    """Simulate the Bell circuit without a quantum SDK.

    This intentionally handles only the Bell-state pattern used here. It
    demonstrates why an SDK is needed for general circuits: a production
    simulator must implement a full state representation, gate matrices,
    measurement collapse, noise models, and device constraints.
    """
    if shots <= 0:
        raise ValueError("shots must be positive")

    if circuit.qubits == 2 and [g.name for g in circuit.gates] == ["H", "CX"]:
        rng = random.Random(42)
        counts = Counter()
        for _ in range(shots):
            counts[rng.choice(("00", "11"))] += 1
        return counts

    raise NotImplementedError(
        "The dependency-free simulator intentionally supports only the Bell circuit"
    )


def analyze_landscape() -> None:
    print("QUANTUM SDK LANDSCAPE")
    print("=" * 78)

    for sdk in SDK_LANDSCAPE:
        print(f"\n{sdk.name} | {sdk.organization}")
        print(f"  Language:       {sdk.primary_language}")
        print(f"  Circuit model:  {sdk.circuit_model}")
        print(f"  Differentiable: {sdk.differentiable}")
        print(f"  Compiler focus: {sdk.compiler_focus}")
        print(f"  Hardware:       {sdk.hardware_access}")
        print(f"  Cloud:          {sdk.cloud_orchestration}")
        print(f"  Simulator:      {sdk.simulator_focus}")
        print(f"  Typical role:   {sdk.typical_role}")
        print(f"  Interop:        {', '.join(sdk.interoperability)}")
        print("  Strengths:")
        for item in sdk.strengths:
            print(f"    - {item}")
        print("  Trade-offs:")
        for item in sdk.tradeoffs:
            print(f"    - {item}")


def demonstrate_circuit_model() -> None:
    print("\nCIRCUIT REPRESENTATION")
    print("=" * 78)

    bell = bell_circuit()
    print("\nBell circuit:")
    print(bell.describe())
    print(f"Qubits: {bell.qubits}")
    print(f"Gates: {len(bell.gates)}")
    print(f"Two-qubit gates: {bell.two_qubit_gate_count()}")
    print(f"Depth: {bell.depth()}")

    counts = simulate_measurement(bell, 1000)
    print(f"Bell measurement simulation: {dict(counts)}")

    ansatz = variational_circuit(math.pi / 3)
    print("\nParameterized variational circuit:")
    print(ansatz.describe())
    print(f"Parameters: {ansatz.parameter_count()}")
    print(f"Depth: {ansatz.depth()}")


def demonstrate_recommendations() -> None:
    print("\nWORKLOAD-DRIVEN SDK SELECTION")
    print("=" * 78)

    workloads = (
        Workload(
            name="Train a variational classifier",
            type=WorkloadType.QML,
            requires_differentiation=True,
        ),
        Workload(
            name="Optimize circuits for a constrained QPU topology",
            type=WorkloadType.HARDWARE_COMPILATION,
            requires_hardware_compiler=True,
        ),
        Workload(
            name="Run a managed multi-provider cloud experiment",
            type=WorkloadType.CLOUD_EXECUTION,
            requires_cloud=True,
        ),
        Workload(
            name="Simulate a hybrid workload across multiple GPUs",
            type=WorkloadType.GPU_SIMULATION,
            requires_gpu=True,
        ),
        Workload(
            name="Estimate resources for a future fault-tolerant algorithm",
            type=WorkloadType.RESOURCE_ESTIMATION,
            requires_resource_estimation=True,
        ),
    )

    for workload in workloads:
        print(f"\n{workload.name}")
        for sdk, score, reasons in recommend(workload):
            explanation = "; ".join(reasons) if reasons else "general compatibility"
            print(f"  {sdk.name:22} score={score:2d}  {explanation}")


def demonstrate_interoperability() -> None:
    print("\nINTEROPERABILITY GRAPH")
    print("=" * 78)

    graph: dict[str, set[str]] = defaultdict(set)

    for sdk in SDK_LANDSCAPE:
        for target in sdk.interoperability:
            graph[sdk.name].add(target)

    for source, targets in graph.items():
        print(f"{source}: {', '.join(sorted(targets))}")

    print(
        "\nInteroperability should be treated as a design dimension rather than "
        "a promise that every feature is portable. A circuit may translate "
        "successfully while losing backend-specific controls, pulse behavior, "
        "noise semantics, measurements, or optimization opportunities."
    )


def demonstrate_failure_modes() -> None:
    print("\nVALIDATION AND FAILURE MODES")
    print("=" * 78)

    try:
        Circuit(2).add("CX", 0, 2)
    except ValueError as exc:
        print(f"Invalid qubit reference rejected: {exc}")

    try:
        Circuit(2).add("CX", 0, 0)
    except ValueError as exc:
        print(f"Duplicate qubit reference rejected: {exc}")

    try:
        simulate_measurement(Circuit(1).add("H", 0), 100)
    except NotImplementedError as exc:
        print(f"Unsupported simulation scope reported explicitly: {exc}")

    print(
        "\nProduction SDK code must also validate backend availability, "
        "supported gates, coupling maps, shot limits, parameter domains, "
        "authentication, quota, queue state, and version compatibility."
    )


def main() -> None:
    analyze_landscape()
    demonstrate_circuit_model()
    demonstrate_recommendations()
    demonstrate_interoperability()
    demonstrate_failure_modes()


if __name__ == "__main__":
    main()
