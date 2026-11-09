#!/usr/bin/env python3
"""
Quantum Hardware Architecture Comparison Engine

Compares major quantum computing hardware architectures using
transparent qualitative engineering criteria.

Architectures:
- Superconducting qubits
- Trapped-ion qubits
- Neutral-atom qubits
- Photonic quantum computing
- Semiconductor spin qubits
- Topological qubits

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import csv
import json
import logging
import argparse
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

LOGGER = logging.getLogger("quantum_hardware")


class ArchitectureType(Enum):
    SUPERCONDUCTING = "Superconducting"
    TRAPPED_ION = "Trapped Ion"
    NEUTRAL_ATOM = "Neutral Atom"
    PHOTONIC = "Photonic"
    SPIN = "Semiconductor Spin"
    TOPOLOGICAL = "Topological"


@dataclass(frozen=True)
class Architecture:
    name: str
    physical_qubit: str
    operating_environment: str
    gate_speed: int
    coherence: int
    connectivity: int
    scalability: int
    engineering_maturity: int
    control_integration: int
    error_correction_progress: int
    strengths: tuple[str, ...]
    limitations: tuple[str, ...]
    evidence_status: str

    def validate(self) -> None:
        scores = (
            self.gate_speed,
            self.coherence,
            self.connectivity,
            self.scalability,
            self.engineering_maturity,
            self.control_integration,
            self.error_correction_progress,
        )

        if not self.name.strip():
            raise ValueError("Architecture name cannot be empty.")

        if any(not isinstance(x, int) or not 1 <= x <= 5 for x in scores):
            raise ValueError("All comparison scores must be integers from 1 to 5.")

        if not self.strengths or not self.limitations:
            raise ValueError("Strengths and limitations are required.")


@dataclass(frozen=True)
class ComparisonWeights:
    gate_speed: float = 0.15
    coherence: float = 0.15
    connectivity: float = 0.10
    scalability: float = 0.20
    engineering_maturity: float = 0.15
    control_integration: float = 0.10
    error_correction_progress: float = 0.15

    def validate(self) -> None:
        values = asdict(self).values()

        if any(value < 0 for value in values):
            raise ValueError("Weights cannot be negative.")

        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("Comparison weights must sum to 1.0.")


class QuantumHardwareDatabase:
    """Stores architecture profiles and provides comparison operations."""

    def __init__(self) -> None:
        self._architectures: dict[str, Architecture] = {}

    def add(self, architecture: Architecture) -> None:
        architecture.validate()
        key = architecture.name.lower()

        if key in self._architectures:
            raise ValueError(f"Duplicate architecture: {architecture.name}")

        self._architectures[key] = architecture

    def get(self, name: str) -> Architecture:
        try:
            return self._architectures[name.lower()]
        except KeyError as exc:
            raise KeyError(f"Unknown architecture: {name}") from exc

    def all(self) -> list[Architecture]:
        return list(self._architectures.values())


class ComparisonEngine:
    """Calculates weighted qualitative architecture scores."""

    def __init__(
        self,
        database: QuantumHardwareDatabase,
        weights: ComparisonWeights
    ) -> None:
        weights.validate()
        self.database = database
        self.weights = weights

    def score(self, architecture: Architecture) -> float:
        values = asdict(self.weights)

        total = sum(
            getattr(architecture, criterion) * weight
            for criterion, weight in values.items()
        )

        return round(total, 3)

    def rank(self) -> list[dict]:
        results = [
            {
                "architecture": architecture.name,
                "score": self.score(architecture),
                "physical_qubit": architecture.physical_qubit,
                "evidence_status": architecture.evidence_status,
            }
            for architecture in self.database.all()
        ]

        return sorted(
            results,
            key=lambda item: item["score"],
            reverse=True
        )

    def compare(self, first: str, second: str) -> dict:
        a = self.database.get(first)
        b = self.database.get(second)

        return {
            "first": a.name,
            "second": b.name,
            "first_score": self.score(a),
            "second_score": self.score(b),
            "score_difference": round(
                self.score(a) - self.score(b), 3
            ),
            "first_advantages": list(a.strengths),
            "second_advantages": list(b.strengths),
        }

    def suitability(
        self,
        name: str,
        application: str
    ) -> dict:
        architecture = self.database.get(name)

        requirements = {
            "fast_gates": architecture.gate_speed,
            "long_coherence": architecture.coherence,
            "large_registers": architecture.scalability,
            "high_connectivity": architecture.connectivity,
            "error_correction": architecture.error_correction_progress,
            "engineering_readiness": architecture.engineering_maturity,
        }

        return {
            "architecture": architecture.name,
            "application": application,
            "criteria": requirements,
            "assessment": (
                "Potentially suitable"
                if sum(requirements.values()) / len(requirements) >= 3.5
                else "Requires application-specific evaluation"
            ),
        }


def build_database() -> QuantumHardwareDatabase:
    database = QuantumHardwareDatabase()

    profiles = [
        Architecture(
            "Superconducting",
            "Josephson-junction superconducting circuits",
            "Millikelvin dilution refrigerator",
            5, 2, 3, 4, 5, 4, 4,
            (
                "Fast microwave-controlled gates",
                "Established semiconductor fabrication ecosystem",
                "Strong integration with control electronics",
            ),
            (
                "Cryogenic infrastructure",
                "Shorter coherence relative to leading trapped-ion systems",
                "Calibration and frequency-crowding challenges",
            ),
            "Relatively mature experimental and commercial ecosystem",
        ),
        Architecture(
            "Trapped Ion",
            "Electromagnetically confined atomic ions",
            "Ultra-high vacuum and laser systems",
            2, 5, 4, 3, 4, 3, 4,
            (
                "Long coherence times",
                "High-fidelity operations",
                "Flexible ion-to-ion interactions",
            ),
            (
                "Relatively slow gates",
                "Laser and optical-system complexity",
                "Scaling large registers requires careful engineering",
            ),
            "Established experimental and commercial ecosystem",
        ),
        Architecture(
            "Neutral Atom",
            "Laser-trapped neutral atoms",
            "Ultra-high vacuum and optical trapping",
            3, 4, 5, 5, 3, 3, 3,
            (
                "Large programmable atom arrays",
                "Flexible interaction graphs",
                "Potential for high-density registers",
            ),
            (
                "Atom loss and rearrangement",
                "Rydberg-state sensitivity",
                "Gate fidelity and measurement engineering challenges",
            ),
            "Rapidly developing experimental ecosystem",
        ),
        Architecture(
            "Photonic",
            "Single photons and optical modes",
            "Optical systems; environment depends on platform",
            4, 4, 3, 4, 2, 3, 3,
            (
                "Potential room-temperature operation",
                "Natural compatibility with optical networking",
                "Low interaction with many environmental disturbances",
            ),
            (
                "Photon loss",
                "Probabilistic interactions in many approaches",
                "Photon-source and detector requirements",
            ),
            "Developing experimental and commercial ecosystem",
        ),
        Architecture(
            "Semiconductor Spin",
            "Electron or nuclear spins in solid-state devices",
            "Cryogenic and often magnetic-field-controlled",
            4, 4, 2, 4, 2, 4, 2,
            (
                "Potential compatibility with semiconductor fabrication",
                "Compact physical devices",
                "Potential integration with classical electronics",
            ),
            (
                "Device variability",
                "Control and calibration complexity",
                "Limited connectivity in many implementations",
            ),
            "Developing experimental ecosystem",
        ),
        Architecture(
            "Topological",
            "Proposed non-Abelian anyonic or protected states",
            "Platform-dependent specialized conditions",
            2, 5, 2, 3, 1, 1, 1,
            (
                "Potential intrinsic protection against certain local errors",
                "Potential reduction in error-correction overhead",
            ),
            (
                "Difficult experimental realization",
                "Limited demonstration of usable topological qubits",
                "Fault-tolerant operation remains unestablished",
            ),
            "Highly experimental; usable architecture remains unproven",
        ),
    ]

    for profile in profiles:
        database.add(profile)

    return database


def export_json(results: list[dict], filename: str) -> None:
    path = Path(filename)

    with path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    LOGGER.info("JSON report saved to %s", path)


def export_csv(results: list[dict], filename: str) -> None:
    if not results:
        raise ValueError("Cannot export an empty comparison.")

    path = Path(filename)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )
        writer.writeheader()
        writer.writerows(results)

    LOGGER.info("CSV report saved to %s", path)


def print_report(
    database: QuantumHardwareDatabase,
    engine: ComparisonEngine
) -> None:
    print("\nQUANTUM HARDWARE ARCHITECTURE COMPARISON")
    print("=" * 95)
    print("Scores are illustrative qualitative assessments, not measured benchmarks.")
    print("Higher scores indicate a more favorable relative assessment.")
    print("-" * 95)

    for position, result in enumerate(engine.rank(), start=1):
        architecture = database.get(result["architecture"])

        print(f"\n{position}. {architecture.name}")
        print(f"   Weighted score: {result['score']}/5")
        print(f"   Physical qubit: {architecture.physical_qubit}")
        print(f"   Environment: {architecture.operating_environment}")
        print(f"   Evidence: {architecture.evidence_status}")
        print("   Strengths:")
        for item in architecture.strengths:
            print(f"      + {item}")
        print("   Limitations:")
        for item in architecture.limitations:
            print(f"      - {item}")


def run_tests(engine: ComparisonEngine) -> None:
    """Basic integrity and edge-case tests."""

    assert len(engine.database.all()) == 6
    assert engine.score(engine.database.get("Trapped Ion")) > 0

    try:
        engine.database.get("Unknown Architecture")
    except KeyError:
        pass
    else:
        raise AssertionError("Unknown architecture should fail.")

    try:
        ComparisonWeights(
            gate_speed=0.5,
            coherence=0.5,
            connectivity=0.5
        ).validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid weights should fail.")

    LOGGER.info("All validation tests passed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare quantum hardware architectures."
    )

    parser.add_argument(
        "--json",
        default="quantum_comparison.json",
        help="JSON report destination"
    )

    parser.add_argument(
        "--csv",
        default="quantum_comparison.csv",
        help="CSV report destination"
    )

    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("ARCHITECTURE_A", "ARCHITECTURE_B"),
        help="Compare two architecture names"
    )

    args = parser.parse_args()

    database = build_database()
    weights = ComparisonWeights()
    engine = ComparisonEngine(database, weights)

    run_tests(engine)
    print_report(database, engine)

    results = engine.rank()

    export_json(results, args.json)
    export_csv(results, args.csv)

    if args.compare:
        result = engine.compare(*args.compare)
        print("\nPAIRWISE COMPARISON")
        print(json.dumps(result, indent=4))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        LOGGER.error("Execution failed: %s", error)
        raise SystemExit(1)
