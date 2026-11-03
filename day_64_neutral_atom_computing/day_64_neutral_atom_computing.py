#!/usr/bin/env python3
"""Neutral-atom computing: optical tweezer traps, loading, and atom rearrangement.

The simulation models Gaussian optical traps, a two-dimensional tweezer array,
probabilistic single-atom loading, and minimum-distance rearrangement.

It does not simulate quantum gates, atom motion, or real laboratory hardware.
Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from typing import Sequence


BOLTZMANN_CONSTANT = 1.380649e-23
PLANCK_CONSTANT_REDUCED = 1.054571817e-34
RUBIDIUM_87_MASS_KG = 1.44316060e-25


class LabConfigurationError(ValueError):
    """Raised when an optical or array configuration is invalid."""


class RearrangementError(RuntimeError):
    """Raised when an atom rearrangement cannot be planned."""


@dataclass(frozen=True)
class Point:
    x_um: float
    y_um: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.x_um) or not math.isfinite(self.y_um):
            raise LabConfigurationError("Coordinates must be finite.")

    def distance_um(self, other: "Point") -> float:
        return math.hypot(self.x_um - other.x_um, self.y_um - other.y_um)


@dataclass(frozen=True)
class TrapCalibration:
    """Calibration for one Gaussian optical tweezer."""

    wavelength_m: float
    waist_m: float
    trap_depth_j: float
    atomic_mass_kg: float = RUBIDIUM_87_MASS_KG

    def __post_init__(self) -> None:
        values = (
            self.wavelength_m,
            self.waist_m,
            self.trap_depth_j,
            self.atomic_mass_kg,
        )
        if not all(math.isfinite(value) and value > 0 for value in values):
            raise LabConfigurationError(
                "Wavelength, waist, trap depth, and atomic mass must be positive."
            )

    @property
    def rayleigh_range_m(self) -> float:
        return math.pi * self.waist_m**2 / self.wavelength_m

    @property
    def radial_frequency_hz(self) -> float:
        # Harmonic approximation around the center of a Gaussian tweezer.
        angular_frequency = math.sqrt(
            4.0 * self.trap_depth_j
            / (self.atomic_mass_kg * self.waist_m**2)
        )
        return angular_frequency / (2.0 * math.pi)

    @property
    def axial_frequency_hz(self) -> float:
        angular_frequency = math.sqrt(
            2.0 * self.trap_depth_j
            / (self.atomic_mass_kg * self.rayleigh_range_m**2)
        )
        return angular_frequency / (2.0 * math.pi)

    def potential_j(self, radial_distance_m: float, axial_distance_m: float = 0.0) -> float:
        """Return the single-beam Gaussian potential energy.

        The potential is negative for a red-detuned attractive trap.
        """
        if not math.isfinite(radial_distance_m) or radial_distance_m < 0:
            raise ValueError("Radial distance must be finite and non-negative.")
        if not math.isfinite(axial_distance_m):
            raise ValueError("Axial distance must be finite.")

        z_ratio = axial_distance_m / self.rayleigh_range_m
        beam_radius = self.waist_m * math.sqrt(1.0 + z_ratio**2)
        depth = (
            self.trap_depth_j
            / (1.0 + z_ratio**2)
            * math.exp(-2.0 * radial_distance_m**2 / beam_radius**2)
        )
        return -depth


@dataclass(frozen=True)
class TweezerSite:
    site_id: str
    row: int
    column: int
    position: Point


@dataclass(frozen=True)
class Atom:
    atom_id: str
    source_site_id: str
    position: Point


@dataclass(frozen=True)
class TargetSite:
    target_id: str
    position: Point


@dataclass(frozen=True)
class AtomMove:
    atom_id: str
    source_site_id: str
    target_id: str
    distance_um: float


class TweezerArray:
    """Rectangular array of independently addressed optical tweezer sites."""

    def __init__(
        self,
        rows: int,
        columns: int,
        spacing_um: float,
        calibration: TrapCalibration,
    ) -> None:
        if rows <= 0 or columns <= 0:
            raise LabConfigurationError("Array dimensions must be positive.")
        if not math.isfinite(spacing_um) or spacing_um <= 0:
            raise LabConfigurationError("Site spacing must be positive and finite.")

        self.rows = rows
        self.columns = columns
        self.spacing_um = spacing_um
        self.calibration = calibration
        self.sites = tuple(
            TweezerSite(
                site_id=f"r{row}c{column}",
                row=row,
                column=column,
                position=Point(column * spacing_um, row * spacing_um),
            )
            for row in range(rows)
            for column in range(columns)
        )
        self._sites_by_id = {site.site_id: site for site in self.sites}

    def sample_loading(
        self,
        probability: float,
        seed: int = 2026,
    ) -> list[Atom]:
        """Sample single-atom occupancy independently at every site.

        This Bernoulli model approximates loading under a single-atom
        occupancy constraint. It does not model loading dynamics.
        """
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError("Loading probability must be between 0 and 1.")

        generator = random.Random(seed)
        atoms: list[Atom] = []

        for site in self.sites:
            if generator.random() < probability:
                atoms.append(
                    Atom(
                        atom_id=f"atom-{len(atoms) + 1}",
                        source_site_id=site.site_id,
                        position=site.position,
                    )
                )
        return atoms

    def atoms_from_site_ids(self, site_ids: Sequence[str]) -> list[Atom]:
        """Create an atom list from an observed occupancy measurement."""
        if len(set(site_ids)) != len(site_ids):
            raise ValueError("An occupied site may appear only once.")

        atoms: list[Atom] = []
        for site_id in site_ids:
            site = self._sites_by_id.get(site_id)
            if site is None:
                raise ValueError(f"Unknown tweezer site: {site_id}")
            atoms.append(
                Atom(
                    atom_id=f"atom-{len(atoms) + 1}",
                    source_site_id=site.site_id,
                    position=site.position,
                )
            )
        return atoms

    def gaussian_tail_fraction(self, site_id: str) -> float:
        """Estimate neighboring-beam intensity-envelope tails.

        This is a geometric overlap indicator, not a measured optical
        interference pattern or a trap-fidelity calculation.
        """
        site = self._sites_by_id.get(site_id)
        if site is None:
            raise ValueError(f"Unknown tweezer site: {site_id}")

        waist_um = self.calibration.waist_m * 1e6
        contributions = 0.0

        for other in self.sites:
            if other.site_id == site_id:
                continue
            distance_um = site.position.distance_um(other.position)
            contributions += math.exp(-2.0 * distance_um**2 / waist_um**2)

        return contributions

    def combined_potential_j(self, position: Point) -> float:
        """Sum Gaussian potential envelopes from the array's tweezers.

        This approximation treats the beams as incoherent or time-averaged.
        Coherent optical interference is not represented.
        """
        total = 0.0
        waist_um = self.calibration.waist_m * 1e6

        for site in self.sites:
            distance_m = position.distance_um(site.position) * 1e-6
            total += self.calibration.potential_j(distance_m)

        return total


def target_grid(
    rows: int,
    columns: int,
    spacing_um: float,
    offset_um: float = 0.0,
) -> list[TargetSite]:
    if rows <= 0 or columns <= 0:
        raise ValueError("Target dimensions must be positive.")
    if not math.isfinite(spacing_um) or spacing_um <= 0:
        raise ValueError("Target spacing must be positive and finite.")
    if not math.isfinite(offset_um):
        raise ValueError("Target offset must be finite.")

    return [
        TargetSite(
            target_id=f"target-r{row}c{column}",
            position=Point(
                offset_um + column * spacing_um,
                offset_um + row * spacing_um,
            ),
        )
        for row in range(rows)
        for column in range(columns)
    ]


def rectangular_hungarian(cost: Sequence[Sequence[float]]) -> list[int]:
    """Solve a rectangular assignment problem.

    Returns one selected column for each row. The number of rows must not
    exceed the number of columns. Runtime is O(n^2 * m).
    """
    row_count = len(cost)
    if row_count == 0:
        return []

    column_count = len(cost[0])
    if column_count == 0 or row_count > column_count:
        raise ValueError("Assignment requires 0 < rows <= columns.")

    if any(len(row) != column_count for row in cost):
        raise ValueError("Cost matrix must be rectangular.")

    if any(
        not math.isfinite(value)
        for row in cost
        for value in row
    ):
        raise ValueError("Assignment costs must be finite.")

    # Potentials and matching arrays use one-based indexing.
    u = [0.0] * (row_count + 1)
    v = [0.0] * (column_count + 1)
    p = [0] * (column_count + 1)
    previous = [0] * (column_count + 1)

    for row in range(1, row_count + 1):
        p[0] = row
        current_column = 0
        minimum = [math.inf] * (column_count + 1)
        used = [False] * (column_count + 1)

        while True:
            used[current_column] = True
            current_row = p[current_column]
            delta = math.inf
            next_column = 0

            for column in range(1, column_count + 1):
                if used[column]:
                    continue

                reduced_cost = (
                    cost[current_row - 1][column - 1]
                    - u[current_row]
                    - v[column]
                )

                if reduced_cost < minimum[column]:
                    minimum[column] = reduced_cost
                    previous[column] = current_column

                if minimum[column] < delta:
                    delta = minimum[column]
                    next_column = column

            if not math.isfinite(delta):
                raise RearrangementError("No feasible assignment exists.")

            for column in range(column_count + 1):
                if used[column]:
                    u[p[column]] += delta
                    v[column] -= delta
                else:
                    minimum[column] -= delta

            current_column = next_column
            if p[current_column] == 0:
                break

        while True:
            next_column = previous[current_column]
            p[current_column] = p[next_column]
            current_column = next_column
            if current_column == 0:
                break

    assignment = [-1] * row_count
    for column in range(1, column_count + 1):
        if p[column] != 0:
            assignment[p[column] - 1] = column - 1

    if any(column < 0 for column in assignment):
        raise RearrangementError("Assignment did not cover every row.")

    return assignment


def plan_rearrangement(
    atoms: Sequence[Atom],
    targets: Sequence[TargetSite],
) -> list[AtomMove]:
    """Assign atoms to targets with minimum total Euclidean travel distance.

    If there are more atoms than targets, every target is filled and some
    atoms remain unused. If there are fewer atoms than targets, every atom
    is assigned, but the target array remains incomplete.
    """
    if not atoms or not targets:
        raise RearrangementError("Atoms and targets must both be non-empty.")

    if len({atom.atom_id for atom in atoms}) != len(atoms):
        raise ValueError("Atom identifiers must be unique.")
    if len({target.target_id for target in targets}) != len(targets):
        raise ValueError("Target identifiers must be unique.")

    moves: list[AtomMove] = []

    if len(atoms) >= len(targets):
        # Each target is a row; each available atom is a candidate column.
        costs = [
            [target.position.distance_um(atom.position) for atom in atoms]
            for target in targets
        ]
        assignment = rectangular_hungarian(costs)

        for target_index, atom_index in enumerate(assignment):
            atom = atoms[atom_index]
            target = targets[target_index]
            moves.append(
                AtomMove(
                    atom_id=atom.atom_id,
                    source_site_id=atom.source_site_id,
                    target_id=target.target_id,
                    distance_um=atom.position.distance_um(target.position),
                )
            )
    else:
        # Each atom is a row; choose a distinct target for every atom.
        costs = [
            [atom.position.distance_um(target.position) for target in targets]
            for atom in atoms
        ]
        assignment = rectangular_hungarian(costs)

        for atom_index, target_index in enumerate(assignment):
            atom = atoms[atom_index]
            target = targets[target_index]
            moves.append(
                AtomMove(
                    atom_id=atom.atom_id,
                    source_site_id=atom.source_site_id,
                    target_id=target.target_id,
                    distance_um=atom.position.distance_um(target.position),
                )
            )

    return sorted(moves, key=lambda move: move.target_id)


def run_self_tests(calibration: TrapCalibration) -> None:
    array = TweezerArray(2, 2, 5.0, calibration)

    assert len(array.sample_loading(0.0, seed=1)) == 0
    assert len(array.sample_loading(1.0, seed=1)) == 4
    assert calibration.radial_frequency_hz > calibration.axial_frequency_hz
    assert calibration.potential_j(0.0) < 0.0

    assignment = rectangular_hungarian(
        [
            [4.0, 1.0, 8.0],
            [2.0, 5.0, 3.0],
        ]
    )
    assert len(assignment) == 2
    assert len(set(assignment)) == 2

    try:
        array.atoms_from_site_ids(["r0c0", "r0c0"])
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate occupied sites were not rejected.")


def build_demo(seed: int) -> dict[str, object]:
    calibration = TrapCalibration(
        wavelength_m=850e-9,
        waist_m=0.8e-6,
        trap_depth_j=BOLTZMANN_CONSTANT * 1e-3,
    )
    run_self_tests(calibration)

    array = TweezerArray(
        rows=4,
        columns=4,
        spacing_um=5.0,
        calibration=calibration,
    )

    # Explicit imaging result provides a repeatable rearrangement example.
    observed_occupied_sites = [
        "r0c1",
        "r0c3",
        "r1c0",
        "r1c2",
        "r2c1",
        "r2c3",
        "r3c0",
        "r3c2",
        "r3c3",
        "r1c3",
    ]
    atoms = array.atoms_from_site_ids(observed_occupied_sites)

    # A translated 3 x 3 target grid has nine requested final positions.
    targets = target_grid(
        rows=3,
        columns=3,
        spacing_um=5.0,
        offset_um=2.5,
    )
    moves = plan_rearrangement(atoms, targets)

    loading_probability = 0.55
    total_sites = len(array.sites)

    # A separate seeded shot illustrates probabilistic loading.
    sampled_atoms = array.sample_loading(loading_probability, seed=seed)

    total_distance = sum(move.distance_um for move in moves)
    occupied_tail_values = [
        array.gaussian_tail_fraction(site_id)
        for site_id in observed_occupied_sites
    ]

    return {
        "model": "Gaussian optical tweezer array",
        "units": {
            "position": "micrometers",
            "trap_depth": "joules",
            "frequency": "hertz",
        },
        "calibration": {
            "wavelength_m": calibration.wavelength_m,
            "waist_m": calibration.waist_m,
            "trap_depth_j": calibration.trap_depth_j,
            "rayleigh_range_m": calibration.rayleigh_range_m,
            "radial_frequency_hz": calibration.radial_frequency_hz,
            "axial_frequency_hz": calibration.axial_frequency_hz,
        },
        "array": {
            "rows": array.rows,
            "columns": array.columns,
            "site_count": total_sites,
            "spacing_um": array.spacing_um,
            "loading_probability": loading_probability,
            "expected_loaded_atoms": total_sites * loading_probability,
            "independent_loading_probability_of_full_array": (
                loading_probability**total_sites
            ),
            "sampled_atoms_for_seed": len(sampled_atoms),
        },
        "imaging_result": {
            "occupied_sites": observed_occupied_sites,
            "loaded_atoms": len(atoms),
        },
        "rearrangement": {
            "target_count": len(targets),
            "assigned_moves": len(moves),
            "complete_target_array": len(moves) == len(targets),
            "total_transport_distance_um": total_distance,
            "moves": [asdict(move) for move in moves],
        },
        "optical_geometry": {
            "maximum_neighbor_tail_fraction": max(occupied_tail_values),
            "potential_at_array_origin_j": array.combined_potential_j(Point(0, 0)),
        },
        "model_limits": [
            "Independent Bernoulli loading is an approximation.",
            "The harmonic trap frequencies describe motion near a trap minimum.",
            "Rearrangement distances do not model transport trajectories or heating.",
            "The overlap indicator is not a quantum-state fidelity measurement.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simulate optical tweezer arrays and atom rearrangement."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="Seed for the probabilistic loading example.",
    )
    args = parser.parse_args()

    try:
        result = build_demo(args.seed)
        print(json.dumps(result, indent=2))
        return 0
    except (LabConfigurationError, RearrangementError, ValueError) as error:
        print(f"Simulation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
