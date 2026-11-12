#!/usr/bin/env python3
"""
Quantum Decoherence Simulator
Topic: T1, T2 and Environmental Effects

Models:
- T1: Energy relaxation
- T2: Transverse coherence decay
- Pure dephasing
- Environmental noise
- Bloch-vector evolution
- Measurement probabilities
- Physical consistency validation
- Exponential decay fitting
- Experiment comparison
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class Environment(Enum):
    ISOLATED = "isolated"
    THERMAL = "thermal"
    MAGNETIC_NOISE = "magnetic_noise"
    ELECTRIC_NOISE = "electric_noise"
    VIBRATIONAL = "vibrational"
    MIXED = "mixed"


@dataclass(frozen=True)
class DecoherenceParameters:
    t1: float
    t2: float
    environment: Environment
    temperature_kelvin: float = 0.020
    noise_strength: float = 0.0
    equilibrium_excited_population: float = 0.0

    def __post_init__(self):
        if not math.isfinite(self.t1) or self.t1 <= 0:
            raise ValueError("T1 must be finite and positive.")

        if not math.isfinite(self.t2) or self.t2 <= 0:
            raise ValueError("T2 must be finite and positive.")

        if self.t2 > 2 * self.t1:
            raise ValueError("Physical consistency requires T2 <= 2*T1.")

        if self.temperature_kelvin < 0:
            raise ValueError("Temperature cannot be negative.")

        if not 0 <= self.noise_strength:
            raise ValueError("Noise strength cannot be negative.")

        if not 0 <= self.equilibrium_excited_population <= 1:
            raise ValueError("Equilibrium population must be between 0 and 1.")

    @property
    def pure_dephasing_time(self) -> float:
        """
        1/T2 = 1/(2*T1) + 1/T_phi
        """
        inverse_t_phi = 1 / self.t2 - 1 / (2 * self.t1)

        if inverse_t_phi <= 1e-15:
            return math.inf

        return 1 / inverse_t_phi


@dataclass
class QubitState:
    x: float
    y: float
    z: float

    def validate(self):
        values = (self.x, self.y, self.z)

        if not all(math.isfinite(v) for v in values):
            raise ValueError("Bloch coordinates must be finite.")

        radius_squared = sum(v * v for v in values)

        if radius_squared > 1 + 1e-9:
            raise ValueError("Invalid Bloch vector: state lies outside Bloch sphere.")

    @property
    def purity(self) -> float:
        return (1 + self.x**2 + self.y**2 + self.z**2) / 2

    @property
    def excited_probability(self) -> float:
        return (1 - self.z) / 2

    @property
    def ground_probability(self) -> float:
        return (1 + self.z) / 2


@dataclass
class Measurement:
    time: float
    x: float
    y: float
    z: float
    purity: float
    excited_probability: float
    coherence: float


class DecoherenceSimulator:
    def __init__(self, parameters: DecoherenceParameters):
        self.parameters = parameters

    def evolve(
        self,
        initial_state: QubitState,
        elapsed_time: float
    ) -> QubitState:
        """
        Apply amplitude damping and pure dephasing.

        The transverse components decay as exp(-t/T2).
        Population relaxation approaches thermal equilibrium.
        """

        initial_state.validate()

        if not math.isfinite(elapsed_time) or elapsed_time < 0:
            raise ValueError("Elapsed time must be finite and nonnegative.")

        p = self.parameters

        transverse_decay = math.exp(-elapsed_time / p.t2)
        longitudinal_decay = math.exp(-elapsed_time / p.t1)

        x = initial_state.x * transverse_decay
        y = initial_state.y * transverse_decay

        equilibrium_z = (
            1 - 2 * p.equilibrium_excited_population
        )

        z = (
            equilibrium_z
            + (initial_state.z - equilibrium_z) * longitudinal_decay
        )

        result = QubitState(x, y, z)
        result.validate()

        return result

    def measurement(self, state: QubitState, time: float) -> Measurement:
        state.validate()

        return Measurement(
            time=time,
            x=state.x,
            y=state.y,
            z=state.z,
            purity=state.purity,
            excited_probability=state.excited_probability,
            coherence=math.sqrt(state.x**2 + state.y**2)
        )

    def run_experiment(
        self,
        initial_state: QubitState,
        duration: float,
        steps: int
    ) -> list[Measurement]:

        if not math.isfinite(duration) or duration < 0:
            raise ValueError("Duration must be finite and nonnegative.")

        if steps < 1:
            raise ValueError("At least one measurement step is required.")

        initial_state.validate()

        results = []

        for index in range(steps + 1):
            time = duration * index / steps
            state = self.evolve(initial_state, time)
            results.append(self.measurement(state, time))

        return results


def fit_exponential_decay(
    measurements: list[Measurement],
    attribute: str
) -> Optional[float]:
    """
    Estimate decay time using linear regression:

    ln(signal) = ln(A) - time/T
    """

    if attribute not in {"coherence", "excited_probability"}:
        raise ValueError("Unsupported decay attribute.")

    points = []

    for measurement in measurements:
        signal = getattr(measurement, attribute)

        if signal > 1e-12:
            points.append((measurement.time, math.log(signal)))

    if len(points) < 2:
        return None

    mean_x = sum(x for x, _ in points) / len(points)
    mean_y = sum(y for _, y in points) / len(points)

    numerator = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in points
    )

    denominator = sum(
        (x - mean_x) ** 2
        for x, _ in points
    )

    if denominator == 0:
        return None

    slope = numerator / denominator

    if slope >= 0:
        return None

    return -1 / slope


def simulate_measurement_shots(
    excited_probability: float,
    shots: int,
    seed: int = 42
) -> dict:
    """
    Simulate projective measurements in the computational basis.
    """

    if not 0 <= excited_probability <= 1:
        raise ValueError("Probability must be between zero and one.")

    if shots <= 0:
        raise ValueError("Shots must be positive.")

    rng = random.Random(seed)

    excited = sum(
        rng.random() < excited_probability
        for _ in range(shots)
    )

    ground = shots - excited

    return {
        "shots": shots,
        "ground": ground,
        "excited": excited,
        "estimated_excited_probability": excited / shots
    }


def environmental_comparison():
    scenarios = [
        DecoherenceParameters(
            t1=100.0,
            t2=150.0,
            environment=Environment.ISOLATED
        ),
        DecoherenceParameters(
            t1=80.0,
            t2=60.0,
            environment=Environment.THERMAL,
            temperature_kelvin=0.050,
            equilibrium_excited_population=0.02
        ),
        DecoherenceParameters(
            t1=100.0,
            t2=25.0,
            environment=Environment.MAGNETIC_NOISE,
            noise_strength=0.8
        ),
        DecoherenceParameters(
            t1=70.0,
            t2=35.0,
            environment=Environment.ELECTRIC_NOISE,
            noise_strength=0.5
        ),
        DecoherenceParameters(
            t1=90.0,
            t2=20.0,
            environment=Environment.MIXED,
            noise_strength=0.9
        )
    ]

    initial = QubitState(1.0, 0.0, 0.0)
    results = []

    for parameters in scenarios:
        simulator = DecoherenceSimulator(parameters)

        measurements = simulator.run_experiment(
            initial,
            duration=200,
            steps=20
        )

        results.append({
            "environment": parameters.environment.value,
            "T1": parameters.t1,
            "T2": parameters.t2,
            "T_phi": parameters.pure_dephasing_time,
            "final_coherence": measurements[-1].coherence,
            "final_purity": measurements[-1].purity
        })

    return results


def save_results(results, filename="decoherence_results.json"):
    path = Path(filename)

    payload = json.dumps(results, indent=4, allow_nan=False)

    path.write_text(payload, encoding="utf-8")

    return path.resolve()


def main():
    parameters = DecoherenceParameters(
        t1=100.0,
        t2=60.0,
        environment=Environment.MIXED,
        temperature_kelvin=0.020,
        noise_strength=0.5,
        equilibrium_excited_population=0.01
    )

    simulator = DecoherenceSimulator(parameters)

    # Initial state: equal superposition on the equator.
    initial_state = QubitState(1.0, 0.0, 0.0)

    measurements = simulator.run_experiment(
        initial_state,
        duration=300,
        steps=30
    )

    print("QUANTUM DECOHERENCE EXPERIMENT")
    print("=" * 55)

    print(f"Environment: {parameters.environment.value}")
    print(f"T1: {parameters.t1:.2f}")
    print(f"T2: {parameters.t2:.2f}")
    print(f"T_phi: {parameters.pure_dephasing_time:.2f}")

    print("\nTIME EVOLUTION")

    for measurement in measurements[::5]:
        print(
            f"t={measurement.time:7.2f} | "
            f"Coherence={measurement.coherence:.5f} | "
            f"Purity={measurement.purity:.5f} | "
            f"P(excited)={measurement.excited_probability:.5f}"
        )

    estimated_t2 = fit_exponential_decay(
        measurements,
        "coherence"
    )

    print(f"\nEstimated T2: {estimated_t2:.4f}")

    final_state = simulator.evolve(initial_state, 100)

    print("\nPROJECTIVE MEASUREMENT")
    print(
        simulate_measurement_shots(
            final_state.excited_probability,
            shots=10000
        )
    )

    print("\nENVIRONMENTAL COMPARISON")

    comparison = environmental_comparison()

    for result in comparison:
        print(result)

    save_results(
        [asdict(m) for m in measurements]
    )

    # Physical consistency and edge-case checks.
    assert QubitState(0, 0, 1).purity == 1
    assert abs(measurements[0].coherence - 1.0) < 1e-12
    assert measurements[-1].coherence < measurements[0].coherence

    try:
        DecoherenceParameters(
            t1=10,
            t2=30,
            environment=Environment.MIXED
        )
    except ValueError:
        print("\nCorrectly rejected physically inconsistent T1/T2 values.")

    print("\nExperiment completed successfully.")


if __name__ == "__main__":
    main()
