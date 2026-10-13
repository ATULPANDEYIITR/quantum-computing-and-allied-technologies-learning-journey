#!/usr/bin/env python3
"""
Circuit Visualization and Analysis
==================================

A self-contained circuit modeling, SVG drawing, and DC analysis toolkit.

Features:
- Electrical components and circuit connectivity.
- Resistor networks and independent DC voltage sources.
- Kirchhoff's current law and modified nodal analysis.
- Gaussian elimination with partial pivoting.
- Node voltages, branch currents, power, and energy checks.
- SVG schematic generation without external packages.
- JSON netlist export, validation, and automated tests.

Run:
    python circuit_visualization.py
"""

from __future__ import annotations

import json
import math
import unittest
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from typing import Iterable


TOLERANCE = 1e-10


class CircuitError(ValueError):
    """Raised when a circuit is invalid or cannot be analyzed."""


@dataclass(frozen=True)
class Resistor:
    name: str
    node_a: str
    node_b: str
    resistance: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CircuitError("A resistor must have a name.")
        if not self.node_a or not self.node_b:
            raise CircuitError(f"{self.name}: terminal names are required.")
        if self.node_a == self.node_b:
            raise CircuitError(f"{self.name}: both terminals cannot be identical.")
        if not math.isfinite(self.resistance) or self.resistance <= 0:
            raise CircuitError(f"{self.name}: resistance must be finite and positive.")

    @property
    def conductance(self) -> float:
        return 1.0 / self.resistance


@dataclass(frozen=True)
class VoltageSource:
    name: str
    positive: str
    negative: str
    voltage: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CircuitError("A voltage source must have a name.")
        if not self.positive or not self.negative:
            raise CircuitError(f"{self.name}: terminal names are required.")
        if self.positive == self.negative:
            raise CircuitError(f"{self.name}: terminals cannot be identical.")
        if not math.isfinite(self.voltage):
            raise CircuitError(f"{self.name}: voltage must be finite.")


@dataclass(frozen=True)
class CircuitResults:
    node_voltages: dict[str, float]
    source_currents: dict[str, float]
    resistor_currents: dict[str, float]
    resistor_powers: dict[str, float]
    total_resistor_power: float
    total_source_power: float


class Circuit:
    """Circuit whose components connect named electrical nodes."""

    def __init__(self, name: str = "DC Circuit") -> None:
        self.name = name
        self.resistors: list[Resistor] = []
        self.sources: list[VoltageSource] = []

    def add_resistor(
        self, name: str, node_a: str, node_b: str, resistance: float
    ) -> Resistor:
        component = Resistor(name, node_a, node_b, resistance)
        self._check_unique_name(name)
        self.resistors.append(component)
        return component

    def add_voltage_source(
        self, name: str, positive: str, negative: str, voltage: float
    ) -> VoltageSource:
        component = VoltageSource(name, positive, negative, voltage)
        self._check_unique_name(name)
        self.sources.append(component)
        return component

    def _check_unique_name(self, name: str) -> None:
        names = {item.name for item in self.resistors + self.sources}
        if name in names:
            raise CircuitError(f"Duplicate component name: {name}")

    @property
    def nodes(self) -> list[str]:
        return sorted({
            node
            for component in self.resistors
            for node in (component.node_a, component.node_b)
        } | {
            node
            for source in self.sources
            for node in (source.positive, source.negative)
        })

    def validate(self, ground: str = "0") -> None:
        if not self.resistors and not self.sources:
            raise CircuitError("The circuit contains no components.")

        if ground not in self.nodes:
            raise CircuitError(f"Ground node {ground!r} does not exist.")

        # A DC operating point requires every electrical node to have
        # a resistive or source-constrained path to the reference node.
        adjacency = {node: set() for node in self.nodes}
        for item in self.resistors:
            adjacency[item.node_a].add(item.node_b)
            adjacency[item.node_b].add(item.node_a)
        for item in self.sources:
            adjacency[item.positive].add(item.negative)
            adjacency[item.negative].add(item.positive)

        visited = {ground}
        stack = [ground]
        while stack:
            node = stack.pop()
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        missing = set(self.nodes) - visited
        if missing:
            raise CircuitError(
                f"Nodes are disconnected from ground: {sorted(missing)}"
            )

        # Reject a loop consisting exclusively of ideal voltage sources
        # when its voltage constraints are inconsistent.
        self._validate_source_constraints(ground)

    def _validate_source_constraints(self, ground: str) -> None:
        offsets: dict[str, float] = {}
        adjacency: dict[str, list[tuple[str, float]]] = {
            node: [] for node in self.nodes
        }

        for source in self.sources:
            # V(positive) - V(negative) = source.voltage.
            adjacency[source.negative].append(
                (source.positive, source.voltage)
            )
            adjacency[source.positive].append(
                (source.negative, -source.voltage)
            )

        for root in self.nodes:
            if root in offsets:
                continue
            offsets[root] = 0.0
            stack = [root]
            while stack:
                node = stack.pop()
                for neighbor, delta in adjacency[node]:
                    expected = offsets[node] + delta
                    if neighbor in offsets:
                        if not math.isclose(
                            offsets[neighbor], expected,
                            rel_tol=1e-8, abs_tol=1e-8
                        ):
                            raise CircuitError(
                                "Inconsistent ideal voltage-source constraints."
                            )
                    else:
                        offsets[neighbor] = expected
                        stack.append(neighbor)

    def netlist(self) -> dict:
        return {
            "name": self.name,
            "ground": "0",
            "resistors": [asdict(item) for item in self.resistors],
            "voltage_sources": [asdict(item) for item in self.sources],
        }

    def equivalent_resistance(
        self, start: str, end: str
    ) -> float:
        """Compute equivalent resistance for resistor-only networks."""
        if self.sources:
            raise CircuitError(
                "Equivalent resistance helper accepts resistor-only networks."
            )
        if start not in self.nodes or end not in self.nodes:
            raise CircuitError("Both requested terminals must exist.")
        if start == end:
            return 0.0

        nodes = [node for node in self.nodes if node != end]
        index = {node: position for position, node in enumerate(nodes)}
        matrix = [[0.0] * len(nodes) for _ in nodes]
        rhs = [0.0] * len(nodes)

        for resistor in self.resistors:
            a, b = resistor.node_a, resistor.node_b
            g = resistor.conductance

            if a != end:
                matrix[index[a]][index[a]] += g
            if b != end:
                matrix[index[b]][index[b]] += g
            if a != end and b != end:
                matrix[index[a]][index[b]] -= g
                matrix[index[b]][index[a]] -= g

        # Apply one ampere entering start and leaving end.
        rhs[index[start]] = 1.0
        solution = gaussian_elimination(matrix, rhs)
        return solution[index[start]]

    def analyze(self, ground: str = "0") -> CircuitResults:
        """Solve a linear DC circuit using modified nodal analysis."""
        self.validate(ground)

        unknown_nodes = [node for node in self.nodes if node != ground]
        node_index = {
            node: position for position, node in enumerate(unknown_nodes)
        }

        node_count = len(unknown_nodes)
        source_count = len(self.sources)
        size = node_count + source_count

        matrix = [[0.0] * size for _ in range(size)]
        rhs = [0.0] * size

        def add_conductance(a: str, b: str, conductance: float) -> None:
            if a != ground:
                ia = node_index[a]
                matrix[ia][ia] += conductance
            if b != ground:
                ib = node_index[b]
                matrix[ib][ib] += conductance
            if a != ground and b != ground:
                ia, ib = node_index[a], node_index[b]
                matrix[ia][ib] -= conductance
                matrix[ib][ia] -= conductance

        for resistor in self.resistors:
            add_conductance(
                resistor.node_a, resistor.node_b, resistor.conductance
            )

        # A source-current unknown is positive from the positive terminal
        # to the negative terminal of the voltage source.
        for source_number, source in enumerate(self.sources):
            source_index = node_count + source_number

            if source.positive != ground:
                p = node_index[source.positive]
                matrix[p][source_index] += 1.0
                matrix[source_index][p] += 1.0

            if source.negative != ground:
                n = node_index[source.negative]
                matrix[n][source_index] -= 1.0
                matrix[source_index][n] -= 1.0

            rhs[source_index] = source.voltage

        solution = gaussian_elimination(matrix, rhs)

        voltages = {ground: 0.0}
        for node, position in node_index.items():
            voltages[node] = solution[position]

        source_currents = {
            source.name: solution[node_count + position]
            for position, source in enumerate(self.sources)
        }

        resistor_currents: dict[str, float] = {}
        resistor_powers: dict[str, float] = {}

        for resistor in self.resistors:
            voltage = voltages[resistor.node_a] - voltages[resistor.node_b]
            current = voltage / resistor.resistance
            resistor_currents[resistor.name] = current
            resistor_powers[resistor.name] = voltage * current

        total_resistor_power = sum(resistor_powers.values())
        total_source_power = sum(
            source.voltage * source_currents[source.name]
            for source in self.sources
        )

        if not math.isclose(
            total_resistor_power + total_source_power,
            0.0,
            rel_tol=1e-7,
            abs_tol=1e-7,
        ):
            raise CircuitError(
                "Power balance failed; check component conventions or model."
            )

        return CircuitResults(
            node_voltages=voltages,
            source_currents=source_currents,
            resistor_currents=resistor_currents,
            resistor_powers=resistor_powers,
            total_resistor_power=total_resistor_power,
            total_source_power=total_source_power,
        )


def gaussian_elimination(
    matrix: list[list[float]], rhs: list[float]
) -> list[float]:
    """Solve Ax=b using partial pivoting without mutating the caller's data."""
    n = len(rhs)
    if n == 0 or len(matrix) != n or any(len(row) != n for row in matrix):
        raise CircuitError("The linear system must be a non-empty square matrix.")

    a = [list(map(float, row)) + [float(rhs[i])] for i, row in enumerate(matrix)]

    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(a[row][column]))

        if abs(a[pivot][column]) < TOLERANCE:
            raise CircuitError(
                "The circuit matrix is singular or the operating point is undefined."
            )

        a[column], a[pivot] = a[pivot], a[column]
        pivot_value = a[column][column]

        for j in range(column, n + 1):
            a[column][j] /= pivot_value

        for row in range(n):
            if row == column:
                continue
            factor = a[row][column]
            if factor == 0.0:
                continue
            for j in range(column, n + 1):
                a[row][j] -= factor * a[column][j]

    solution = [a[i][n] for i in range(n)]
    if any(not math.isfinite(value) for value in solution):
        raise CircuitError("The solution contains non-finite values.")
    return solution


def draw_svg(circuit: Circuit, output: str | Path) -> None:
    """
    Draw a readable schematic using a deterministic schematic layout.

    The drawing is a visual representation of component connectivity.
    It is not a physical PCB layout or a simulation waveform.
    """
    components = circuit.resistors + circuit.sources
    if not components:
        raise CircuitError("Cannot draw an empty circuit.")

    width = 900
    row_height = 105
    height = max(210, 115 + row_height * len(components))
    left, right = 190, 650

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#101820"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#f2f5f7}'
        '.wire{stroke:#8dd9ff;stroke-width:2.5;fill:none}'
        '.component{stroke:#ffc857;stroke-width:3;fill:none}'
        '.node{fill:#f2f5f7}</style>',
        f'<text x="30" y="38" font-size="23">{escape(circuit.name)}</text>',
    ]

    for index, component in enumerate(components):
        y = 90 + index * row_height
        parts.append(
            f'<text x="30" y="{y + 5}" font-size="15">'
            f'{escape(component.name)}</text>'
        )

        if isinstance(component, Resistor):
            parts.extend([
                f'<line class="wire" x1="{left}" y1="{y}" x2="{left + 80}" y2="{y}"/>',
                f'<rect class="component" x="{left + 80}" y="{y - 15}" '
                'width="200" height="30" rx="3"/>',
                f'<line class="wire" x1="{left + 280}" y1="{y}" x2="{right}" y2="{y}"/>',
                f'<text x="{left + 180}" y="{y - 24}" text-anchor="middle" font-size="14">'
                f'{component.resistance:g} Ω</text>',
            ])
        else:
            cx = (left + right) / 2
            parts.extend([
                f'<line class="wire" x1="{left}" y1="{y}" x2="{cx - 32}" y2="{y}"/>',
                f'<circle class="component" cx="{cx}" cy="{y}" r="32"/>',
                f'<line class="wire" x1="{cx + 32}" y1="{y}" x2="{right}" y2="{y}"/>',
                f'<text x="{cx}" y="{y + 5}" text-anchor="middle" font-size="13">'
                f'{component.voltage:g} V</text>',
            ])

        parts.extend([
            f'<circle class="node" cx="{left}" cy="{y}" r="4"/>',
            f'<circle class="node" cx="{right}" cy="{y}" r="4"/>',
            f'<text x="{left - 12}" y="{y + 24}" font-size="12" text-anchor="end">'
            f'{escape(component.node_a if isinstance(component, Resistor) else component.positive)}'
            '</text>',
            f'<text x="{right + 12}" y="{y + 24}" font-size="12">'
            f'{escape(component.node_b if isinstance(component, Resistor) else component.negative)}'
            '</text>',
        ])

    parts.append("</svg>")
    Path(output).write_text("\n".join(parts), encoding="utf-8")


def print_results(results: CircuitResults) -> None:
    print("\nNode voltages")
    for node, voltage in sorted(results.node_voltages.items()):
        print(f"  {node:>8}: {voltage:10.5f} V")

    print("\nResistor branches")
    for name, current in results.resistor_currents.items():
        power = results.resistor_powers[name]
        print(f"  {name}: I={current:9.5f} A, P={power:9.5f} W")

    print("\nVoltage-source currents")
    for name, current in results.source_currents.items():
        print(f"  {name}: {current:9.5f} A")

    print(f"\nTotal resistor dissipation: {results.total_resistor_power:.6f} W")
    print(f"Total source power:         {results.total_source_power:.6f} W")


class CircuitTests(unittest.TestCase):
    def test_voltage_divider(self) -> None:
        circuit = Circuit("Voltage Divider")
        circuit.add_voltage_source("V1", "in", "0", 12.0)
        circuit.add_resistor("R1", "in", "out", 1000.0)
        circuit.add_resistor("R2", "out", "0", 2000.0)
        result = circuit.analyze()
        self.assertAlmostEqual(result.node_voltages["out"], 8.0)
        self.assertAlmostEqual(result.resistor_currents["R1"], 0.004)
        self.assertAlmostEqual(result.resistor_currents["R2"], 0.004)

    def test_parallel_equivalent_resistance(self) -> None:
        circuit = Circuit("Parallel Network")
        circuit.add_resistor("R1", "a", "b", 1000.0)
        circuit.add_resistor("R2", "a", "b", 1000.0)
        self.assertAlmostEqual(circuit.equivalent_resistance("a", "b"), 500.0)

    def test_invalid_resistance(self) -> None:
        with self.assertRaises(CircuitError):
            Resistor("Rbad", "a", "b", 0.0)

    def test_singular_circuit(self) -> None:
        circuit = Circuit("Floating Voltage Source")
        circuit.add_voltage_source("V1", "a", "b", 5.0)
        with self.assertRaises(CircuitError):
            circuit.analyze(ground="a")

    def test_inconsistent_voltage_loop(self) -> None:
        circuit = Circuit("Conflicting Sources")
        circuit.add_voltage_source("V1", "a", "0", 5.0)
        circuit.add_voltage_source("V2", "a", "0", 9.0)
        circuit.add_resistor("R1", "a", "0", 1000.0)
        with self.assertRaises(CircuitError):
            circuit.analyze()


def build_example() -> Circuit:
    circuit = Circuit("12 V Sensor Interface")
    circuit.add_voltage_source("V_SUPPLY", "vin", "0", 12.0)
    circuit.add_resistor("R_PULLUP", "vin", "sense", 1000.0)
    circuit.add_resistor("R_SENSOR", "sense", "0", 2000.0)
    circuit.add_resistor("R_LOAD", "sense", "0", 10000.0)
    return circuit


def main() -> None:
    circuit = build_example()
    results = circuit.analyze()
    print_results(results)

    draw_svg(circuit, "circuit_schematic.svg")
    Path("circuit_netlist.json").write_text(
        json.dumps(circuit.netlist(), indent=2),
        encoding="utf-8",
    )
    print("\nGenerated circuit_schematic.svg and circuit_netlist.json")

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CircuitTests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    if not outcome.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
