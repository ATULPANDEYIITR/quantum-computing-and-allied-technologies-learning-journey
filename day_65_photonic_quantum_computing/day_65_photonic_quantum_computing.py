#!/usr/bin/env python3
"""
Photonic Quantum Computing: Photons as Qubits

A self-contained educational simulation covering:
- Polarization-encoded photonic qubits
- Quantum state representation
- Normalization and validation
- Linear optical quantum gates
- Quantum measurement
- Beam splitters and phase shifters
- Hong-Ou-Mandel interference
- Photon loss and detector efficiency
- Repeated experiments and statistical analysis
- Basic security and experimental integrity checks

Uses only the Python standard library.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class QuantumError(Exception):
    """Base exception for quantum simulation errors."""


class InvalidStateError(QuantumError):
    """Raised when a quantum state is invalid."""


class MeasurementError(QuantumError):
    """Raised when measurement cannot be performed."""


class PhotonLossError(QuantumError):
    """Raised when a photon is lost before detection."""


class Polarization(Enum):
    HORIZONTAL = "H"
    VERTICAL = "V"


@dataclass(frozen=True)
class PhotonState:
    """
    A single-photon polarization qubit.

    |psi> = alpha|H> + beta|V>

    The amplitudes must satisfy:
        |alpha|² + |beta|² = 1
    """

    alpha: complex
    beta: complex

    def __post_init__(self) -> None:
        if not isinstance(self.alpha, (int, float, complex)):
            raise InvalidStateError("Invalid horizontal amplitude.")

        if not isinstance(self.beta, (int, float, complex)):
            raise InvalidStateError("Invalid vertical amplitude.")

        if not all(
            math.isfinite(value)
            for amplitude in (self.alpha, self.beta)
            for value in (amplitude.real, amplitude.imag)
        ):
            raise InvalidStateError("Amplitudes must be finite.")

        norm = abs(self.alpha) ** 2 + abs(self.beta) ** 2

        if not math.isclose(norm, 1.0, abs_tol=1e-9):
            raise InvalidStateError(
                f"State must be normalized; squared norm is {norm}."
            )

    @property
    def probability_h(self) -> float:
        return abs(self.alpha) ** 2

    @property
    def probability_v(self) -> float:
        return abs(self.beta) ** 2

    @property
    def bloch_coordinates(self) -> tuple[float, float, float]:
        """Return the Bloch vector for the pure polarization state."""
        a = self.alpha
        b = self.beta

        x = 2.0 * (a.conjugate() * b).real
        y = 2.0 * (a.conjugate() * b).imag
        z = abs(a) ** 2 - abs(b) ** 2

        return x, y, z

    def describe(self) -> str:
        return (
            f"|psi> = ({self.alpha:.4f})|H> "
            f"+ ({self.beta:.4f})|V>"
        )


class PhotonSource:
    """Generate photons in specified polarization states."""

    @staticmethod
    def horizontal() -> PhotonState:
        return PhotonState(1 + 0j, 0 + 0j)

    @staticmethod
    def vertical() -> PhotonState:
        return PhotonState(0 + 0j, 1 + 0j)

    @staticmethod
    def diagonal() -> PhotonState:
        return PhotonState(
            1 / math.sqrt(2),
            1 / math.sqrt(2)
        )

    @staticmethod
    def right_circular() -> PhotonState:
        return PhotonState(
            1 / math.sqrt(2),
            1j / math.sqrt(2)
        )

    @staticmethod
    def custom(alpha: complex, beta: complex) -> PhotonState:
        norm = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)

        if norm <= 0 or not math.isfinite(norm):
            raise InvalidStateError("Cannot normalize zero or invalid state.")

        return PhotonState(alpha / norm, beta / norm)


class OpticalGates:
    """
    Ideal polarization transformations.

    Every gate is unitary and preserves normalization.
    """

    @staticmethod
    def _apply(
        state: PhotonState,
        matrix: Sequence[Sequence[complex]]
    ) -> PhotonState:
        alpha = (
            matrix[0][0] * state.alpha
            + matrix[0][1] * state.beta
        )

        beta = (
            matrix[1][0] * state.alpha
            + matrix[1][1] * state.beta
        )

        return PhotonState(alpha, beta)

    @staticmethod
    def pauli_x(state: PhotonState) -> PhotonState:
        """Swap horizontal and vertical polarization."""
        return OpticalGates._apply(
            state,
            [[0, 1], [1, 0]]
        )

    @staticmethod
    def pauli_z(state: PhotonState) -> PhotonState:
        """Apply a relative phase of pi."""
        return OpticalGates._apply(
            state,
            [[1, 0], [0, -1]]
        )

    @staticmethod
    def hadamard(state: PhotonState) -> PhotonState:
        """Balanced polarization transformation."""
        scale = 1 / math.sqrt(2)

        return OpticalGates._apply(
            state,
            [
                [scale, scale],
                [scale, -scale]
            ]
        )

    @staticmethod
    def phase_shifter(
        state: PhotonState,
        phase: float
    ) -> PhotonState:
        if not math.isfinite(phase):
            raise ValueError("Phase must be finite.")

        return OpticalGates._apply(
            state,
            [
                [1, 0],
                [0, cmath.exp(1j * phase)]
            ]
        )

    @staticmethod
    def quarter_wave_plate(
        state: PhotonState,
        angle: float = 0.0
    ) -> PhotonState:
        """
        Model a quarter-wave plate using a rotated Jones matrix.

        The global phase is physically irrelevant.
        """
        c = math.cos(angle)
        s = math.sin(angle)

        q = cmath.exp(-1j * math.pi / 4)
        r = cmath.exp(1j * math.pi / 4)

        matrix = [
            [
                q * c * c + r * s * s,
                (q - r) * c * s
            ],
            [
                (q - r) * c * s,
                q * s * s + r * c * c
            ]
        ]

        return OpticalGates._apply(state, matrix)


@dataclass(frozen=True)
class MeasurementResult:
    outcome: Polarization
    probability: float


class PolarizationAnalyzer:
    """Projective measurement in the horizontal/vertical basis."""

    @staticmethod
    def measure(
        state: PhotonState,
        rng: random.Random | None = None
    ) -> MeasurementResult:
        generator = rng or random.Random()

        p_h = state.probability_h

        if generator.random() < p_h:
            return MeasurementResult(
                Polarization.HORIZONTAL,
                p_h
            )

        return MeasurementResult(
            Polarization.VERTICAL,
            1.0 - p_h
        )

    @staticmethod
    def measure_repeatedly(
        state: PhotonState,
        shots: int,
        seed: int = 42
    ) -> dict[str, int]:
        if shots <= 0:
            raise ValueError("Shots must be positive.")

        rng = random.Random(seed)

        counts = {"H": 0, "V": 0}

        for _ in range(shots):
            result = PolarizationAnalyzer.measure(state, rng)
            counts[result.outcome.value] += 1

        return counts


@dataclass
class OpticalChannel:
    """
    A lossy optical channel.

    Transmission and detector efficiency are independent
    probabilities.
    """

    transmission: float
    detector_efficiency: float

    def __post_init__(self) -> None:
        for value in (
            self.transmission,
            self.detector_efficiency
        ):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Efficiency values must be in [0, 1].")

    @property
    def total_detection_probability(self) -> float:
        return self.transmission * self.detector_efficiency

    def transmit(
        self,
        rng: random.Random | None = None
    ) -> bool:
        generator = rng or random.Random()

        return (
            generator.random()
            < self.total_detection_probability
        )


@dataclass(frozen=True)
class BeamSplitterResult:
    reflected_amplitude: complex
    transmitted_amplitude: complex

    @property
    def reflected_probability(self) -> float:
        return abs(self.reflected_amplitude) ** 2

    @property
    def transmitted_probability(self) -> float:
        return abs(self.transmitted_amplitude) ** 2


class BeamSplitter:
    """
    Ideal lossless beam splitter.

    Input is a single photon in one spatial input mode.
    The output amplitudes occupy two spatial modes.
    """

    @staticmethod
    def split(
        amplitude: complex = 1 + 0j,
        reflectivity: float = 0.5
    ) -> BeamSplitterResult:
        if not 0 <= reflectivity <= 1:
            raise ValueError("Reflectivity must be in [0, 1].")

        reflected = 1j * math.sqrt(reflectivity) * amplitude
        transmitted = (
            math.sqrt(1 - reflectivity) * amplitude
        )

        return BeamSplitterResult(reflected, transmitted)


@dataclass(frozen=True)
class InterferenceResult:
    coincidence_probability: float
    bunching_probability: float


class HongOuMandelExperiment:
    """
    Ideal two-photon Hong-Ou-Mandel interference model.

    For indistinguishable photons at a balanced beam splitter,
    the coincidence probability is zero.

    This model describes idealized two-photon interference,
    not a complete photonic circuit simulator.
    """

    @staticmethod
    def run(
        overlap: float,
        reflectivity: float = 0.5
    ) -> InterferenceResult:
        if not 0 <= overlap <= 1:
            raise ValueError("Overlap must be in [0, 1].")

        if not 0 <= reflectivity <= 1:
            raise ValueError("Reflectivity must be in [0, 1].")

        coincidence = (
            1 - overlap
        ) * 4 * reflectivity * (1 - reflectivity)

        bunching = 1 - coincidence

        return InterferenceResult(
            coincidence,
            bunching
        )


@dataclass
class ExperimentReport:
    shots: int
    detected: int
    lost: int
    horizontal: int
    vertical: int

    @property
    def detection_rate(self) -> float:
        return self.detected / self.shots

    @property
    def horizontal_fraction(self) -> float:
        if self.detected == 0:
            return 0.0

        return self.horizontal / self.detected


class PhotonicExperiment:
    """Run a polarization experiment through a lossy channel."""

    def __init__(
        self,
        state: PhotonState,
        channel: OpticalChannel,
        seed: int = 42
    ):
        self.state = state
        self.channel = channel
        self.rng = random.Random(seed)

    def run(self, shots: int) -> ExperimentReport:
        if shots <= 0:
            raise ValueError("Shots must be positive.")

        detected = 0
        lost = 0
        horizontal = 0
        vertical = 0

        for _ in range(shots):
            if not self.channel.transmit(self.rng):
                lost += 1
                continue

            detected += 1

            result = PolarizationAnalyzer.measure(
                self.state,
                self.rng
            )

            if result.outcome == Polarization.HORIZONTAL:
                horizontal += 1
            else:
                vertical += 1

        return ExperimentReport(
            shots,
            detected,
            lost,
            horizontal,
            vertical
        )


def demonstrate() -> None:
    print("=" * 65)
    print("PHOTONIC QUANTUM COMPUTING")
    print("=" * 65)

    # 1. Photon generation.
    source = PhotonSource.diagonal()
    print("\n1. Photon source")
    print(source.describe())

    # 2. Quantum gate.
    transformed = OpticalGates.hadamard(source)
    print("\n2. Hadamard transformation")
    print(transformed.describe())

    # 3. Phase shift.
    phased = OpticalGates.phase_shifter(
        source,
        math.pi / 2
    )

    print("\n3. Phase-shifted state")
    print(phased.describe())

    # 4. Bloch sphere representation.
    print("\n4. Bloch coordinates")
    print(phased.bloch_coordinates)

    # 5. Measurement.
    counts = PolarizationAnalyzer.measure_repeatedly(
        source,
        shots=10000,
        seed=42
    )

    print("\n5. Polarization measurement")
    print(counts)

    # 6. Beam splitter.
    split = BeamSplitter.split(
        amplitude=1 + 0j,
        reflectivity=0.5
    )

    print("\n6. Balanced beam splitter")
    print(
        f"Reflection probability: "
        f"{split.reflected_probability:.4f}"
    )
    print(
        f"Transmission probability: "
        f"{split.transmitted_probability:.4f}"
    )

    # 7. Hong-Ou-Mandel interference.
    print("\n7. Hong-Ou-Mandel experiment")

    for overlap in (0.0, 0.5, 1.0):
        result = HongOuMandelExperiment.run(overlap)

        print(
            f"Overlap={overlap:.1f}, "
            f"Coincidence={result.coincidence_probability:.4f}, "
            f"Bunching={result.bunching_probability:.4f}"
        )

    # 8. Lossy channel.
    print("\n8. Lossy photonic channel")

    channel = OpticalChannel(
        transmission=0.85,
        detector_efficiency=0.90
    )

    experiment = PhotonicExperiment(
        source,
        channel,
        seed=123
    )

    report = experiment.run(10000)

    print(f"Shots: {report.shots}")
    print(f"Detected: {report.detected}")
    print(f"Lost: {report.lost}")
    print(f"Detection rate: {report.detection_rate:.4f}")
    print(f"Horizontal: {report.horizontal}")
    print(f"Vertical: {report.vertical}")

    # 9. Automated validation.
    assert math.isclose(
        source.probability_h + source.probability_v,
        1.0
    )

    assert math.isclose(
        split.reflected_probability
        + split.transmitted_probability,
        1.0
    )

    assert report.detected + report.lost == report.shots

    assert math.isclose(
        report.horizontal + report.vertical,
        report.detected
    )

    assert math.isclose(
        HongOuMandelExperiment.run(1.0).coincidence_probability,
        0.0
    )

    print("\nAll validation checks passed.")


def run_tests() -> None:
    """Test normalization, gates, measurements, and edge cases."""

    horizontal = PhotonSource.horizontal()
    vertical = PhotonSource.vertical()
    diagonal = PhotonSource.diagonal()

    assert OpticalGates.pauli_x(horizontal) == vertical
    assert OpticalGates.pauli_x(vertical) == horizontal

    transformed = OpticalGates.hadamard(horizontal)

    assert math.isclose(
        transformed.probability_h,
        0.5
    )

    assert math.isclose(
        transformed.probability_v,
        0.5
    )

    assert math.isclose(
        OpticalGates.phase_shifter(
            horizontal,
            math.pi
        ).probability_h,
        1.0
    )

    assert math.isclose(
        diagonal.probability_h,
        0.5
    )

    try:
        PhotonState(1 + 0j, 1 + 0j)
        raise AssertionError("Invalid state was accepted.")
    except InvalidStateError:
        pass

    try:
        PolarizationAnalyzer.measure_repeatedly(
            horizontal,
            0
        )
        raise AssertionError("Invalid shot count was accepted.")
    except ValueError:
        pass

    try:
        OpticalChannel(1.5, 0.5)
        raise AssertionError("Invalid efficiency was accepted.")
    except ValueError:
        pass

    assert (
        HongOuMandelExperiment.run(0.0)
        .coincidence_probability
        == 1.0
    )

    print("Unit tests passed.")


if __name__ == "__main__":
    run_tests()
    demonstrate()
