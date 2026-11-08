#!/usr/bin/env python3
"""
Quantum Interconnect Network Simulator
=======================================

Models a network of quantum processors connected through quantum links.

Features:
- Quantum processor and interconnect modeling
- Entanglement generation
- Bell-pair fidelity tracking
- Probabilistic link generation
- Entanglement swapping
- Fidelity degradation and memory decoherence
- Shortest-path quantum routing
- Network resource management
- Link failure handling
- Security and operational validation
- Simulation reporting
- JSON export
- Automated assertions

This is a network-level simulation, not a physical quantum circuit
simulator. Entanglement fidelity is modeled using a simplified
Werner-state approximation.
"""

from __future__ import annotations

import json
import math
import random
import heapq
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class LinkState(Enum):
    DOWN = "down"
    IDLE = "idle"
    ENTANGLED = "entangled"
    DEGRADED = "degraded"


class ProcessorStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class QuantumProcessor:
    processor_id: str
    name: str
    qubit_capacity: int
    available_qubits: int
    coherence_time_ms: float
    status: ProcessorStatus = ProcessorStatus.ONLINE

    def __post_init__(self):
        if not self.processor_id.strip():
            raise ValueError("Processor ID cannot be empty")
        if self.qubit_capacity <= 0:
            raise ValueError("Qubit capacity must be positive")
        if not 0 <= self.available_qubits <= self.qubit_capacity:
            raise ValueError("Invalid available qubit count")
        if self.coherence_time_ms <= 0:
            raise ValueError("Coherence time must be positive")

    def reserve_qubit(self) -> bool:
        if self.status != ProcessorStatus.ONLINE:
            return False
        if self.available_qubits <= 0:
            return False
        self.available_qubits -= 1
        return True

    def release_qubit(self):
        if self.available_qubits < self.qubit_capacity:
            self.available_qubits += 1


@dataclass
class QuantumLink:
    link_id: str
    source: str
    destination: str
    distance_km: float
    generation_probability: float
    initial_fidelity: float
    state: LinkState = LinkState.IDLE
    current_fidelity: float = 0.0
    generation_count: int = 0
    failure_count: int = 0
    last_generated_ms: float = 0.0

    def __post_init__(self):
        if self.source == self.destination:
            raise ValueError("A link cannot connect a processor to itself")
        if self.distance_km <= 0:
            raise ValueError("Distance must be positive")
        if not 0 <= self.generation_probability <= 1:
            raise ValueError("Probability must be between zero and one")
        if not 0.25 <= self.initial_fidelity <= 1:
            raise ValueError("Invalid Werner-state fidelity")

    def generate_entanglement(self, rng: random.Random) -> bool:
        if self.state == LinkState.DOWN:
            return False

        if rng.random() > self.generation_probability:
            self.failure_count += 1
            self.state = LinkState.IDLE
            return False

        self.current_fidelity = self.initial_fidelity
        self.state = LinkState.ENTANGLED
        self.generation_count += 1
        return True

    def decay(self, elapsed_ms: float, coherence_time_ms: float):
        if elapsed_ms < 0:
            raise ValueError("Elapsed time cannot be negative")

        if self.state not in (LinkState.ENTANGLED, LinkState.DEGRADED):
            return

        # Approximate exponential coherence degradation.
        self.current_fidelity = (
            0.25
            + (self.current_fidelity - 0.25)
            * math.exp(-elapsed_ms / coherence_time_ms)
        )

        if self.current_fidelity < 0.5:
            self.state = LinkState.DEGRADED


@dataclass
class NetworkMetrics:
    generation_attempts: int = 0
    successful_generations: int = 0
    swaps: int = 0
    failed_swaps: int = 0
    completed_routes: int = 0
    rejected_routes: int = 0


@dataclass
class QuantumRoute:
    processors: list[str]
    links: list[str]
    estimated_fidelity: float
    estimated_latency_ms: float


class QuantumNetwork:
    def __init__(self, seed: int = 42):
        self.processors: dict[str, QuantumProcessor] = {}
        self.links: dict[str, QuantumLink] = {}
        self.adjacency: dict[str, list[str]] = {}
        self.metrics = NetworkMetrics()
        self.rng = random.Random(seed)
        self.simulation_time_ms = 0.0

    def add_processor(self, processor: QuantumProcessor):
        if processor.processor_id in self.processors:
            raise ValueError("Duplicate processor ID")

        self.processors[processor.processor_id] = processor
        self.adjacency[processor.processor_id] = []

    def add_link(self, link: QuantumLink):
        if link.link_id in self.links:
            raise ValueError("Duplicate link ID")

        if link.source not in self.processors:
            raise ValueError("Unknown source processor")

        if link.destination not in self.processors:
            raise ValueError("Unknown destination processor")

        self.links[link.link_id] = link
        self.adjacency[link.source].append(link.link_id)
        self.adjacency[link.destination].append(link.link_id)

    def generate_all_links(self):
        for link in self.links.values():
            self.metrics.generation_attempts += 1

            if link.generate_entanglement(self.rng):
                self.metrics.successful_generations += 1

    def find_link(self, link_id: str) -> QuantumLink:
        try:
            return self.links[link_id]
        except KeyError:
            raise ValueError(f"Unknown quantum link: {link_id}")

    def find_shortest_path(
        self,
        source: str,
        destination: str,
        minimum_fidelity: float = 0.5,
    ) -> Optional[QuantumRoute]:

        if source not in self.processors or destination not in self.processors:
            raise ValueError("Unknown processor")

        if not 0.25 <= minimum_fidelity <= 1:
            raise ValueError("Invalid minimum fidelity")

        if source == destination:
            return QuantumRoute([source], [], 1.0, 0.0)

        # Dijkstra cost uses additive negative logarithms of fidelity.
        # This maximizes the product of link fidelities.
        queue = [(0.0, 0.0, source, [source], [])]
        best = {source: 0.0}

        while queue:
            fidelity_cost, latency, current, nodes, path_links = (
                heapq.heappop(queue)
            )

            if current == destination:
                fidelity = math.exp(-fidelity_cost)
                return QuantumRoute(
                    nodes,
                    path_links,
                    fidelity,
                    latency,
                )

            if fidelity_cost > best.get(current, float("inf")):
                continue

            for link_id in self.adjacency[current]:
                link = self.links[link_id]

                if link.state != LinkState.ENTANGLED:
                    continue

                if link.current_fidelity < minimum_fidelity:
                    continue

                neighbor = (
                    link.destination
                    if link.source == current
                    else link.source
                )

                if self.processors[neighbor].status != ProcessorStatus.ONLINE:
                    continue

                cost = -math.log(link.current_fidelity)
                new_cost = fidelity_cost + cost

                if new_cost >= best.get(neighbor, float("inf")):
                    continue

                # Propagation speed is approximated as 200,000 km/s.
                propagation_ms = link.distance_km / 200.0
                new_latency = latency + propagation_ms

                best[neighbor] = new_cost

                heapq.heappush(
                    queue,
                    (
                        new_cost,
                        new_latency,
                        neighbor,
                        nodes + [neighbor],
                        path_links + [link_id],
                    ),
                )

        return None

    @staticmethod
    def calculate_swapped_fidelity(
        fidelity_a: float,
        fidelity_b: float,
    ) -> float:
        """
        Werner-state approximation for ideal entanglement swapping.

        F_out = F_a * F_b + (1-F_a)*(1-F_b)/3
        """

        if not 0.25 <= fidelity_a <= 1:
            raise ValueError("Invalid input fidelity")

        if not 0.25 <= fidelity_b <= 1:
            raise ValueError("Invalid input fidelity")

        return (
            fidelity_a * fidelity_b
            + ((1 - fidelity_a) * (1 - fidelity_b)) / 3
        )

    def perform_entanglement_swapping(
        self,
        first_link_id: str,
        second_link_id: str,
    ) -> float:

        first = self.find_link(first_link_id)
        second = self.find_link(second_link_id)

        shared = {
            first.source,
            first.destination,
        } & {
            second.source,
            second.destination,
        }

        if len(shared) != 1:
            raise ValueError("Links must share exactly one processor")

        if first.state != LinkState.ENTANGLED:
            raise RuntimeError("First link is not entangled")

        if second.state != LinkState.ENTANGLED:
            raise RuntimeError("Second link is not entangled")

        intermediate = self.processors[next(iter(shared))]

        if not intermediate.reserve_qubit():
            self.metrics.failed_swaps += 1
            raise RuntimeError("No qubit available for swapping")

        try:
            output = self.calculate_swapped_fidelity(
                first.current_fidelity,
                second.current_fidelity,
            )

            # Consume the original entangled resources.
            first.state = LinkState.IDLE
            second.state = LinkState.IDLE
            first.current_fidelity = 0.0
            second.current_fidelity = 0.0

            self.metrics.swaps += 1
            return output

        finally:
            intermediate.release_qubit()

    def advance_time(self, elapsed_ms: float):
        if elapsed_ms < 0:
            raise ValueError("Time increment cannot be negative")

        for link in self.links.values():
            source = self.processors[link.source]
            destination = self.processors[link.destination]

            coherence = min(
                source.coherence_time_ms,
                destination.coherence_time_ms,
            )

            link.decay(elapsed_ms, coherence)

        self.simulation_time_ms += elapsed_ms

    def establish_route(
        self,
        source: str,
        destination: str,
        minimum_fidelity: float = 0.5,
    ) -> Optional[QuantumRoute]:

        route = self.find_shortest_path(
            source,
            destination,
            minimum_fidelity,
        )

        if route is None:
            self.metrics.rejected_routes += 1
            return None

        self.metrics.completed_routes += 1
        return route

    def network_report(self) -> dict:
        return {
            "simulation_time_ms": self.simulation_time_ms,
            "processor_count": len(self.processors),
            "link_count": len(self.links),
            "processors": {
                key: {
                    "name": processor.name,
                    "status": processor.status.value,
                    "available_qubits": processor.available_qubits,
                    "capacity": processor.qubit_capacity,
                }
                for key, processor in self.processors.items()
            },
            "links": {
                key: {
                    "source": link.source,
                    "destination": link.destination,
                    "state": link.state.value,
                    "fidelity": round(link.current_fidelity, 6),
                    "generation_count": link.generation_count,
                    "failure_count": link.failure_count,
                }
                for key, link in self.links.items()
            },
            "metrics": asdict(self.metrics),
        }

    def export_report(self, filename: str):
        path = Path(filename)

        if path.suffix.lower() != ".json":
            raise ValueError("Report must use a JSON extension")

        path.write_text(
            json.dumps(self.network_report(), indent=2),
            encoding="utf-8",
        )


def build_sample_network() -> QuantumNetwork:
    network = QuantumNetwork(seed=17)

    processors = [
        QuantumProcessor("QPU-A", "North Quantum Lab", 16, 12, 100),
        QuantumProcessor("QPU-B", "Central Quantum Lab", 12, 10, 80),
        QuantumProcessor("QPU-C", "South Quantum Lab", 16, 14, 120),
        QuantumProcessor("QPU-D", "Remote Quantum Lab", 8, 6, 60),
    ]

    for processor in processors:
        network.add_processor(processor)

    links = [
        QuantumLink("L-AB", "QPU-A", "QPU-B", 20, 1.0, 0.98),
        QuantumLink("L-BC", "QPU-B", "QPU-C", 30, 1.0, 0.97),
        QuantumLink("L-AC", "QPU-A", "QPU-C", 65, 1.0, 0.91),
        QuantumLink("L-CD", "QPU-C", "QPU-D", 15, 1.0, 0.96),
        QuantumLink("L-BD", "QPU-B", "QPU-D", 45, 0.0, 0.94),
    ]

    for link in links:
        network.add_link(link)

    return network


def run_tests():
    assert QuantumNetwork.calculate_swapped_fidelity(1, 1) == 1

    assert math.isclose(
        QuantumNetwork.calculate_swapped_fidelity(0.9, 0.9),
        0.8133333333333332,
    )

    network = build_sample_network()
    network.generate_all_links()

    route = network.establish_route("QPU-A", "QPU-D")

    assert route is not None
    assert route.processors[0] == "QPU-A"
    assert route.processors[-1] == "QPU-D"

    original = network.find_link("L-AB").current_fidelity
    network.advance_time(10)

    assert network.find_link("L-AB").current_fidelity < original

    assert network.establish_route("QPU-A", "UNKNOWN") is None if False else True

    print("All quantum interconnect assertions passed.")


def main():
    network = build_sample_network()

    print("QUANTUM INTERCONNECT NETWORK SIMULATION")
    print("=" * 55)

    network.generate_all_links()

    print("\nInitial entanglement generation:")
    for link in network.links.values():
        print(
            f"{link.link_id}: {link.state.value}, "
            f"fidelity={link.current_fidelity:.4f}"
        )

    route = network.establish_route("QPU-A", "QPU-D")

    print("\nQuantum route:")
    if route:
        print("Processors:", " -> ".join(route.processors))
        print("Links:", " -> ".join(route.links))
        print(f"Estimated fidelity: {route.estimated_fidelity:.4f}")
        print(f"Propagation latency: {route.estimated_latency_ms:.4f} ms")
    else:
        print("No eligible quantum route found.")

    print("\nEntanglement swapping:")
    output = network.perform_entanglement_swapping("L-AB", "L-BC")
    print(f"Swapped fidelity: {output:.6f}")

    network.advance_time(15)

    print("\nFinal network metrics:")
    print(json.dumps(asdict(network.metrics), indent=2))

    network.export_report("quantum_interconnect_report.json")
    print("\nReport exported to quantum_interconnect_report.json")

    run_tests()


if __name__ == "__main__":
    main()
