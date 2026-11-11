#!/usr/bin/env python3
"""
Quantum Noise: Sources, Mathematical Models, and Density-Matrix Simulation.

Implements:
- Amplitude damping (T1 relaxation)
- Pure dephasing (T2-related phase noise)
- Depolarizing noise
- Bit-flip noise
- Phase-flip noise
- Coherent Z rotation errors
- Thermal excitation
- Measurement readout errors
- Kraus operators and density-matrix validation

Dependencies: Python standard library only.
"""

from __future__ import annotations

import cmath
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Callable


class NoiseType(str, Enum):
    AMPLITUDE_DAMPING = "amplitude_damping"
    PURE_DEPHASING = "pure_dephasing"
    DEPOLARIZING = "depolarizing"
    BIT_FLIP = "bit_flip"
    PHASE_FLIP = "phase_flip"
    COHERENT_Z = "coherent_z"
    THERMAL_RELAXATION = "thermal_relaxation"


class QuantumNoiseError(Exception):
    """Base exception for quantum noise operations."""


@dataclass(frozen=True)
class NoiseParameters:
    probability: float = 0.0
    gamma: float = 0.0
    angle: float = 0.0
    duration: float = 0.0
    t1: float = 0.0
    t2: float = 0.0
    temperature_population: float = 0.0

    def validate(self) -> None:
        for name in ("probability", "gamma", "temperature_population"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        if self.duration < 0:
            raise ValueError("Duration cannot be negative")

        if self.t1 < 0 or self.t2 < 0:
            raise ValueError("Relaxation times cannot be negative")

        if self.t1 > 0 and self.t2 > 2 * self.t1:
            raise ValueError("Physical relaxation requires T2 <= 2*T1")


# Complex-valued 2x2 matrices.
Matrix = list[list[complex]]

I: Matrix = [
    [1 + 0j, 0j],
    [0j, 1 + 0j]
]

X: Matrix = [
    [0j, 1 + 0j],
    [1 + 0j, 0j]
]

Y: Matrix = [
    [0j, -1j],
    [1j, 0j]
]

Z: Matrix = [
    [1 + 0j, 0j],
    [0j, -1 + 0j]
]


def matrix_multiply(a: Matrix, b: Matrix) -> Matrix:
    return [
        [
            sum(a[i][k] * b[k][j] for k in range(2))
            for j in range(2)
        ]
        for i in range(2)
    ]


def conjugate_transpose(a: Matrix) -> Matrix:
    return [
        [a[j][i].conjugate() for j in range(2)]
        for i in range(2)
    ]


def matrix_add(a: Matrix, b: Matrix) -> Matrix:
    return [
        [a[i][j] + b[i][j] for j in range(2)]
        for i in range(2)
    ]


def matrix_scale(a: Matrix, value: complex) -> Matrix:
    return [[value * x for x in row] for row in a]


def trace(a: Matrix) -> complex:
    return a[0][0] + a[1][1]


def density_matrix(
    alpha: complex,
    beta: complex
) -> Matrix:
    norm = abs(alpha) ** 2 + abs(beta) ** 2

    if norm <= 0:
        raise ValueError("Quantum state cannot have zero norm")

    alpha /= math.sqrt(norm)
    beta /= math.sqrt(norm)

    return [
        [alpha * alpha.conjugate(),
         alpha * beta.conjugate()],
        [beta * alpha.conjugate(),
         beta * beta.conjugate()]
    ]


ZERO = density_matrix(1 + 0j, 0j)
ONE = density_matrix(0j, 1 + 0j)
PLUS = density_matrix(1 + 0j, 1 + 0j)


def validate_density_matrix(rho: Matrix, tolerance: float = 1e-9) -> None:
    if len(rho) != 2 or any(len(row) != 2 for row in rho):
        raise ValueError("Expected a 2x2 density matrix")

    if abs(trace(rho) - 1) > tolerance:
        raise QuantumNoiseError("Density matrix must have trace one")

    for i in range(2):
        for j in range(2):
            if abs(rho[i][j] - rho[j][i].conjugate()) > tolerance:
                raise QuantumNoiseError("Density matrix is not Hermitian")

    determinant = (
        rho[0][0] * rho[1][1]
        - rho[0][1] * rho[1][0]
    )

    if abs(determinant.imag) > tolerance or determinant.real < -tolerance:
        raise QuantumNoiseError("Density matrix is not positive semidefinite")

    if rho[0][0].real < -tolerance or rho[1][1].real < -tolerance:
        raise QuantumNoiseError("Negative density-matrix population")


def apply_kraus(rho: Matrix, operators: list[Matrix]) -> Matrix:
    """Apply a completely positive trace-preserving quantum channel."""

    validate_density_matrix(rho)

    if not operators:
        raise ValueError("At least one Kraus operator is required")

    result = [[0j, 0j], [0j, 0j]]

    for operator in operators:
        contribution = matrix_multiply(
            matrix_multiply(operator, rho),
            conjugate_transpose(operator)
        )
        result = matrix_add(result, contribution)

    validate_density_matrix(result)
    return result


def amplitude_damping(gamma: float) -> list[Matrix]:
    """Energy relaxation from |1> to |0>."""

    if not 0 <= gamma <= 1:
        raise ValueError("Gamma must be between 0 and 1")

    return [
        [
            [1, 0],
            [0, math.sqrt(1 - gamma)]
        ],
        [
            [0, math.sqrt(gamma)],
            [0, 0]
        ]
    ]


def pure_dephasing(probability: float) -> list[Matrix]:
    """Random phase-flip representation of pure dephasing."""

    if not 0 <= probability <= 0.5:
        raise ValueError("Dephasing probability must be between 0 and 0.5")

    return [
        matrix_scale(I, math.sqrt(1 - probability)),
        matrix_scale(Z, math.sqrt(probability))
    ]


def depolarizing(probability: float) -> list[Matrix]:
    """Pauli depolarizing channel."""

    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")

    return [
        matrix_scale(I, math.sqrt(1 - probability)),
        matrix_scale(X, math.sqrt(probability / 3)),
        matrix_scale(Y, math.sqrt(probability / 3)),
        matrix_scale(Z, math.sqrt(probability / 3))
    ]


def bit_flip(probability: float) -> list[Matrix]:
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")

    return [
        matrix_scale(I, math.sqrt(1 - probability)),
        matrix_scale(X, math.sqrt(probability))
    ]


def phase_flip(probability: float) -> list[Matrix]:
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")

    return [
        matrix_scale(I, math.sqrt(1 - probability)),
        matrix_scale(Z, math.sqrt(probability))
    ]


def coherent_z_rotation(angle: float) -> Matrix:
    """Unitary phase error, distinct from stochastic phase noise."""

    return [
        [cmath.exp(-0.5j * angle), 0j],
        [0j, cmath.exp(0.5j * angle)]
    ]


def thermal_relaxation(
    gamma: float,
    excited_population: float
) -> list[Matrix]:
    """
    Generalized amplitude damping.

    excited_population represents the equilibrium excited-state
    population of the environment.
    """

    if not 0 <= gamma <= 1:
        raise ValueError("Gamma must be between 0 and 1")

    if not 0 <= excited_population <= 1:
        raise ValueError("Excited population must be between 0 and 1")

    q = excited_population
    g = gamma

    return [
        matrix_scale(
            [[1, 0], [0, math.sqrt(1 - g)]],
            math.sqrt(1 - q)
        ),
        matrix_scale(
            [[0, math.sqrt(g)], [0, 0]],
            math.sqrt(1 - q)
        ),
        matrix_scale(
            [[math.sqrt(1 - g), 0], [0, 1]],
            math.sqrt(q)
        ),
        matrix_scale(
            [[0, 0], [math.sqrt(g), 0]],
            math.sqrt(q)
        )
    ]


def relaxation_probability(duration: float, t1: float) -> float:
    if duration < 0 or t1 <= 0:
        raise ValueError("Duration must be nonnegative and T1 positive")

    return 1 - math.exp(-duration / t1)


def dephasing_probability(
    duration: float,
    t1: float,
    t2: float
) -> float:
    """
    Derive pure-dephasing probability from T1 and T2.

    1/T2 = 1/(2*T1) + 1/T_phi
    """

    if duration < 0 or t1 <= 0 or t2 <= 0:
        raise ValueError("Invalid duration or coherence time")

    if t2 > 2 * t1:
        raise ValueError("T2 cannot exceed 2*T1")

    inverse_tphi = 1 / t2 - 1 / (2 * t1)

    if inverse_tphi < -1e-12:
        raise ValueError("Unphysical coherence parameters")

    inverse_tphi = max(0.0, inverse_tphi)

    if inverse_tphi == 0:
        return 0.0

    coherence = math.exp(-duration * inverse_tphi)
    return (1 - coherence) / 2


def measurement_probabilities(rho: Matrix) -> tuple[float, float]:
    validate_density_matrix(rho)
    return rho[0][0].real, rho[1][1].real


def measurement_with_readout_error(
    rho: Matrix,
    p_0_to_1: float,
    p_1_to_0: float
) -> tuple[float, float]:
    """
    Apply a classical measurement confusion matrix.

    p_0_to_1: report 1 when the actual result is 0.
    p_1_to_0: report 0 when the actual result is 1.
    """

    if not 0 <= p_0_to_1 <= 1 or not 0 <= p_1_to_0 <= 1:
        raise ValueError("Readout probabilities must be in [0, 1]")

    p0, p1 = measurement_probabilities(rho)

    observed_zero = p0 * (1 - p_0_to_1) + p1 * p_1_to_0
    observed_one = p0 * p_0_to_1 + p1 * (1 - p_1_to_0)

    return observed_zero, observed_one


def fidelity_pure_state(rho: Matrix, target: Matrix) -> float:
    """Fidelity against a pure target state."""

    validate_density_matrix(rho)
    validate_density_matrix(target)

    value = trace(matrix_multiply(rho, target)).real
    return min(1.0, max(0.0, value))


def bloch_vector(rho: Matrix) -> tuple[float, float, float]:
    validate_density_matrix(rho)

    return (
        2 * rho[0][1].real,
        -2 * rho[0][1].imag,
        rho[0][0].real - rho[1][1].real
    )


@dataclass
class NoiseExperiment:
    name: str
    source: NoiseType
    probability: float
    description: str

    def execute(self, initial_state: Matrix) -> Matrix:
        if self.source == NoiseType.AMPLITUDE_DAMPING:
            operators = amplitude_damping(self.probability)

        elif self.source == NoiseType.PURE_DEPHASING:
            operators = pure_dephasing(self.probability)

        elif self.source == NoiseType.DEPOLARIZING:
            operators = depolarizing(self.probability)

        elif self.source == NoiseType.BIT_FLIP:
            operators = bit_flip(self.probability)

        elif self.source == NoiseType.PHASE_FLIP:
            operators = phase_flip(self.probability)

        else:
            raise ValueError(f"Unsupported experiment: {self.source}")

        return apply_kraus(initial_state, operators)


def run_experiments() -> list[dict]:
    experiments = [
        NoiseExperiment(
            "Energy relaxation",
            NoiseType.AMPLITUDE_DAMPING,
            0.15,
            "Excited-state population decays"
        ),
        NoiseExperiment(
            "Pure dephasing",
            NoiseType.PURE_DEPHASING,
            0.20,
            "Quantum coherence decreases"
        ),
        NoiseExperiment(
            "Depolarizing channel",
            NoiseType.DEPOLARIZING,
            0.12,
            "Random Pauli errors"
        ),
        NoiseExperiment(
            "Bit flip",
            NoiseType.BIT_FLIP,
            0.10,
            "Bit-flip errors"
        ),
        NoiseExperiment(
            "Phase flip",
            NoiseType.PHASE_FLIP,
            0.10,
            "Phase-flip errors"
        )
    ]

    results = []

    for experiment in experiments:
        output = experiment.execute(PLUS)

        results.append({
            "experiment": experiment.name,
            "noise_type": experiment.source.value,
            "probability": experiment.probability,
            "bloch_vector": bloch_vector(output),
            "fidelity": fidelity_pure_state(output, PLUS),
            "measurement": measurement_probabilities(output)
        })

    return results


def save_results(results: list[dict], filename: str) -> None:
    path = Path(filename)

    # Restrict the output to a simple filename.
    if path.name != filename or path.suffix != ".json":
        raise ValueError("Use a simple JSON filename")

    serializable = []

    for result in results:
        item = dict(result)
        item["bloch_vector"] = list(item["bloch_vector"])
        item["measurement"] = list(item["measurement"])
        serializable.append(item)

    path.write_text(
        json.dumps(serializable, indent=2),
        encoding="utf-8"
    )


def main() -> None:
    results = run_experiments()

    print("QUANTUM NOISE SIMULATION")
    print("=" * 65)

    for result in results:
        print(f"\n{result['experiment']}")
        print(f"  Model: {result['noise_type']}")
        print(f"  Bloch vector: {result['bloch_vector']}")
        print(f"  Fidelity: {result['fidelity']:.6f}")
        print(f"  Measurement probabilities: {result['measurement']}")

    # Demonstrate time-dependent relaxation and coherence.
    t1 = 100e-6
    t2 = 70e-6
    duration = 20e-6

    gamma = relaxation_probability(duration, t1)
    phase_probability = dephasing_probability(duration, t1, t2)

    relaxed = apply_kraus(ZERO, amplitude_damping(gamma))
    dephased = apply_kraus(PLUS, pure_dephasing(phase_probability))

    print("\nTIME-DEPENDENT NOISE")
    print(f"T1: {t1:.2e} seconds")
    print(f"T2: {t2:.2e} seconds")
    print(f"Amplitude damping probability: {gamma:.6f}")
    print(f"Pure dephasing probability: {phase_probability:.6f}")
    print(f"Relaxed state: {bloch_vector(relaxed)}")
    print(f"Dephased state: {bloch_vector(dephased)}")

    # Measurement calibration example.
    observed = measurement_with_readout_error(
        PLUS,
        p_0_to_1=0.03,
        p_1_to_0=0.05
    )

    print("\nREADOUT CALIBRATION")
    print(f"Observed probabilities: {observed}")

    # Physical validity checks.
    for result in results:
        assert 0 <= result["fidelity"] <= 1

    assert abs(sum(observed) - 1.0) < 1e-9

    save_results(results, "quantum_noise_results.json")

    print("\nAll physical validity checks passed.")
    print("Results saved to quantum_noise_results.json")


if __name__ == "__main__":
    main()
