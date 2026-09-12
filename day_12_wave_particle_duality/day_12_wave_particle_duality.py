"""
Wave-Particle Duality and Quantum Behavior
===========================================

A self-contained study script covering wave-particle duality from absolute
beginner level through advanced concepts.

The script uses only Python's standard library. Numerical experiments are
implemented with math and random so that the file can be executed without
installing external packages.

Main topics:
    1. Classical waves and particles
    2. Historical motivation for quantum theory
    3. Planck's quantum hypothesis
    4. Photons and the photoelectric effect
    5. de Broglie's matter waves
    6. Double-slit interference
    7. Single-particle interference
    8. Probability amplitudes and Born's rule
    9. Complementarity
    10. Which-path information
    11. Uncertainty and Fourier relationships
    12. Electron diffraction
    13. Davisson-Germer physics
    14. Compton scattering
    15. Phase velocity and group velocity
    16. Wave packets
    17. Dispersion
    18. Quantum states and observables
    19. Measurement and collapse
    20. Superposition and interference
    21. Entanglement-related distinctions
    22. Quantitative simulations
    23. Edge cases and common misconceptions
    24. Numerical limitations
    25. Testing and verification

The numerical values are educational approximations. They are intended to
illustrate physical relationships rather than replace precision laboratory
calculations.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple


# ============================================================================
# SECTION 1: FUNDAMENTAL CONSTANTS AND BASIC UTILITIES
# ============================================================================

# SI constants used throughout the examples.
PLANCK_CONSTANT = 6.62607015e-34          # J s
HBAR = PLANCK_CONSTANT / (2.0 * math.pi)  # J s
SPEED_OF_LIGHT = 299_792_458.0            # m/s
ELEMENTARY_CHARGE = 1.602176634e-19       # C
ELECTRON_MASS = 9.1093837139e-31          # kg
PROTON_MASS = 1.67262192369e-27           # kg
NEUTRON_MASS = 1.67492749804e-27          # kg
BOLTZMANN_CONSTANT = 1.380649e-23         # J/K


def joules_to_electron_volts(energy_joules: float) -> float:
    """Convert energy from joules to electron-volts."""
    return energy_joules / ELEMENTARY_CHARGE


def electron_volts_to_joules(energy_ev: float) -> float:
    """Convert energy from electron-volts to joules."""
    return energy_ev * ELEMENTARY_CHARGE


def frequency_from_wavelength(wavelength_m: float) -> float:
    """For electromagnetic radiation in vacuum, f = c / lambda."""
    if wavelength_m <= 0:
        raise ValueError("Wavelength must be positive.")
    return SPEED_OF_LIGHT / wavelength_m


def wavelength_from_frequency(frequency_hz: float) -> float:
    """For electromagnetic radiation in vacuum, lambda = c / f."""
    if frequency_hz <= 0:
        raise ValueError("Frequency must be positive.")
    return SPEED_OF_LIGHT / frequency_hz


def photon_energy_from_frequency(frequency_hz: float) -> float:
    """Photon energy E = h f."""
    if frequency_hz < 0:
        raise ValueError("Frequency cannot be negative.")
    return PLANCK_CONSTANT * frequency_hz


def photon_energy_from_wavelength(wavelength_m: float) -> float:
    """Photon energy E = h c / lambda."""
    return PLANCK_CONSTANT * SPEED_OF_LIGHT / wavelength_m


def de_broglie_wavelength(momentum_kg_m_s: float) -> float:
    """
    Calculate matter-wave wavelength.

    de Broglie's relation:
        lambda = h / p
    """
    if momentum_kg_m_s <= 0:
        raise ValueError("Momentum must be positive.")
    return PLANCK_CONSTANT / momentum_kg_m_s


def nonrelativistic_momentum(mass_kg: float, velocity_m_s: float) -> float:
    """Classical approximation p = m v."""
    if mass_kg <= 0:
        raise ValueError("Mass must be positive.")
    if velocity_m_s < 0:
        raise ValueError("This function expects a non-negative speed.")
    return mass_kg * velocity_m_s


def relativistic_momentum(mass_kg: float, velocity_m_s: float) -> float:
    """
    Relativistic momentum:
        p = gamma m v

    This becomes important when v is not small compared with c.
    """
    if mass_kg <= 0:
        raise ValueError("Mass must be positive.")
    if velocity_m_s < 0 or velocity_m_s >= SPEED_OF_LIGHT:
        raise ValueError("Speed must satisfy 0 <= v < c.")

    beta = velocity_m_s / SPEED_OF_LIGHT
    gamma = 1.0 / math.sqrt(1.0 - beta * beta)
    return gamma * mass_kg * velocity_m_s


def relativistic_energy(mass_kg: float, velocity_m_s: float) -> float:
    """Total relativistic energy E = gamma m c^2."""
    if mass_kg <= 0:
        raise ValueError("Mass must be positive.")
    if velocity_m_s < 0 or velocity_m_s >= SPEED_OF_LIGHT:
        raise ValueError("Speed must satisfy 0 <= v < c.")

    beta = velocity_m_s / SPEED_OF_LIGHT
    gamma = 1.0 / math.sqrt(1.0 - beta * beta)
    return gamma * mass_kg * SPEED_OF_LIGHT**2


def kinetic_energy_classical(mass_kg: float, velocity_m_s: float) -> float:
    """Classical kinetic energy K = 1/2 m v^2."""
    return 0.5 * mass_kg * velocity_m_s**2


def print_title(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subtitle(title: str) -> None:
    """Print a smaller subsection heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


# ============================================================================
# SECTION 2: WHAT WAVE-PARTICLE DUALITY MEANS
# ============================================================================

def explain_basic_duality() -> None:
    """
    Introduce the central conceptual distinction.

    Classical physics usually separates:
        wave  -> extended oscillation with interference/diffraction
        particle -> localized object with a trajectory

    Quantum objects do not fit cleanly into either classical category.
    """
    print_title("1. Wave-particle duality")

    print(
        """
Wave-particle duality is the experimentally established fact that quantum
systems display phenomena associated with both classical waves and classical
particles.

Examples of wave-like behavior:
    * interference
    * diffraction
    * superposition
    * phase
    * wavelength

Examples of particle-like behavior:
    * localized detection events
    * quantized energy transfer
    * photon counting
    * discrete detector clicks

The important point is not that an electron literally switches between being
a tiny classical ball and a classical wave. Quantum mechanics provides a more
general description in terms of a quantum state and probability amplitudes.

A measurement can reveal particle-like localized outcomes, while the
probability distribution for many such outcomes can display wave-like
interference.
"""
    )


# ============================================================================
# SECTION 3: CLASSICAL WAVE BASICS
# ============================================================================

def classical_wave_demo() -> None:
    """Demonstrate wavelength, frequency, period, and wave speed."""
    print_title("2. Classical wave foundations")

    wavelength = 2.0
    frequency = 3.0
    wave_speed = wavelength * frequency
    period = 1.0 / frequency

    print(f"Wavelength: {wavelength:.3f} m")
    print(f"Frequency:  {frequency:.3f} Hz")
    print(f"Period:     {period:.3f} s")
    print(f"Wave speed: {wave_speed:.3f} m/s")

    print(
        """
For a simple traveling wave:

    y(x, t) = A cos(kx - omega t + phi)

where:
    A      = amplitude
    k      = 2 pi / lambda, the wave number
    omega  = 2 pi f, angular frequency
    phi    = phase

The classical wave relation is:

    v = f lambda

For electromagnetic waves in vacuum:

    c = f lambda
"""
    )

    k = 2.0 * math.pi / wavelength
    omega = 2.0 * math.pi * frequency
    print(f"Wave number k:      {k:.6f} rad/m")
    print(f"Angular frequency:  {omega:.6f} rad/s")


# ============================================================================
# SECTION 4: PLANCK'S QUANTUM HYPOTHESIS
# ============================================================================

def planck_quantization_demo() -> None:
    """
    Demonstrate energy quantization using E = n h f.

    Planck's original blackbody work introduced energy elements proportional
    to frequency. Modern quantum theory interprets electromagnetic radiation
    in terms of photons with energy E = h f.
    """
    print_title("3. Energy quantization and Planck's relation")

    frequency = 5.0e14
    photon_energy = photon_energy_from_frequency(frequency)

    print(f"Frequency:       {frequency:.3e} Hz")
    print(f"Photon energy:   {photon_energy:.3e} J")
    print(f"Photon energy:   {joules_to_electron_volts(photon_energy):.3f} eV")

    print("\nEnergy values for integer photon counts:")
    for n in range(1, 6):
        energy = n * photon_energy
        print(f"n = {n}: {energy:.3e} J")


# ============================================================================
# SECTION 5: PHOTONS AND THE PHOTOELECTRIC EFFECT
# ============================================================================

def photoelectric_effect_demo() -> None:
    """
    Simulate the main equations of the photoelectric effect.

    Einstein's equation:
        K_max = h f - phi

    The work function phi is the minimum energy needed to remove an electron.

    If hf < phi:
        no photoelectrons are emitted, regardless of intensity in the ideal
        one-photon picture.

    If hf >= phi:
        maximum kinetic energy is positive.
    """
    print_title("4. Photon behavior and the photoelectric effect")

    work_function_ev = 2.30
    work_function_j = electron_volts_to_joules(work_function_ev)

    frequencies = [
        4.0e14,
        5.0e14,
        6.0e14,
        7.0e14,
    ]

    for frequency in frequencies:
        photon_energy_j = photon_energy_from_frequency(frequency)
        kinetic_energy_j = photon_energy_j - work_function_j

        if kinetic_energy_j <= 0:
            print(
                f"f = {frequency:.2e} Hz -> below threshold: "
                "no photoelectron in this simple model"
            )
        else:
            stopping_voltage = kinetic_energy_j / ELEMENTARY_CHARGE
            print(
                f"f = {frequency:.2e} Hz -> "
                f"K_max = {joules_to_electron_volts(kinetic_energy_j):.3f} eV, "
                f"stopping voltage ≈ {stopping_voltage:.3f} V"
            )

    threshold_frequency = work_function_j / PLANCK_CONSTANT
    threshold_wavelength = SPEED_OF_LIGHT / threshold_frequency

    print(f"\nThreshold frequency: {threshold_frequency:.3e} Hz")
    print(f"Threshold wavelength: {threshold_wavelength:.3e} m")

    print(
        """
Important distinction:
    Frequency primarily determines the energy of each photon.
    Intensity changes the number of photons arriving per unit time, assuming
    the spectral frequency is unchanged.

This explains why increasing intensity below the threshold frequency does
not produce photoelectrons in the simple one-photon model.
"""
    )


# ============================================================================
# SECTION 6: DE BROGLIE MATTER WAVES
# ============================================================================

def matter_wave_demo() -> None:
    """Calculate de Broglie wavelengths for several objects."""
    print_title("5. de Broglie's matter-wave hypothesis")

    examples = [
        ("electron", ELECTRON_MASS, 1.0e6),
        ("proton", PROTON_MASS, 1.0e5),
        ("neutron", NEUTRON_MASS, 2.0e3),
        ("baseball-like object", 0.145, 40.0),
    ]

    for name, mass, velocity in examples:
        momentum = nonrelativistic_momentum(mass, velocity)
        wavelength = de_broglie_wavelength(momentum)
        print(
            f"{name:22s}: p = {momentum:.3e} kg m/s, "
            f"lambda = {wavelength:.3e} m"
        )

    print(
        """
de Broglie's proposal extended wave-particle duality to matter:

    lambda = h / p

For ordinary macroscopic objects, h is extremely small, so the wavelength
is usually far too small to observe directly.

For electrons and other microscopic particles, the wavelength can be large
enough to produce measurable diffraction.
"""
    )


# ============================================================================
# SECTION 7: RELATIVISTIC CORRECTION
# ============================================================================

def relativistic_de_broglie_demo() -> None:
    """
    Compare classical and relativistic momenta.

    At high speed, p = mv becomes inaccurate. The de Broglie relation itself
    remains lambda = h/p, but p must be calculated using the appropriate
    relativistic expression.
    """
    print_title("6. Relativistic momentum and matter waves")

    speed_fractions = [0.01, 0.1, 0.5, 0.9, 0.99]

    for fraction in speed_fractions:
        velocity = fraction * SPEED_OF_LIGHT
        classical_p = ELECTRON_MASS * velocity
        relativistic_p = relativistic_momentum(ELECTRON_MASS, velocity)

        classical_lambda = de_broglie_wavelength(classical_p)
        relativistic_lambda = de_broglie_wavelength(relativistic_p)

        ratio = relativistic_p / classical_p

        print(
            f"v/c={fraction:.2f}: "
            f"p_rel/p_classical={ratio:.4f}, "
            f"lambda_rel={relativistic_lambda:.3e} m, "
            f"lambda_classical={classical_lambda:.3e} m"
        )


# ============================================================================
# SECTION 8: DOUBLE-SLIT INTERFERENCE
# ============================================================================

def double_slit_amplitude(
    position: float,
    wavelength: float,
    slit_separation: float,
    screen_distance: float,
) -> float:
    """
    Approximate the phase difference for a two-slit experiment.

    For small angles:

        path difference ≈ d sin(theta)

    with:

        sin(theta) ≈ x / L

    so:

        delta ≈ 2 pi d x / (lambda L)

    The returned value is the interference amplitude factor cos(delta/2).
    """
    delta = (
        2.0
        * math.pi
        * slit_separation
        * position
        / (wavelength * screen_distance)
    )
    return math.cos(delta / 2.0)


def double_slit_intensity(
    position: float,
    wavelength: float,
    slit_separation: float,
    screen_distance: float,
) -> float:
    """
    Calculate a normalized ideal two-slit interference intensity.

    I is proportional to:

        |A1 + A2|^2

For equal amplitudes this gives a pattern proportional to:

        4 cos^2(delta/2)
    """
    amplitude_factor = double_slit_amplitude(
        position,
        wavelength,
        slit_separation,
        screen_distance,
    )
    return 4.0 * amplitude_factor**2


def ascii_interference_pattern(
    wavelength: float,
    slit_separation: float,
    screen_distance: float,
    points: int = 81,
) -> None:
    """Print a one-dimensional interference pattern using ASCII characters."""
    print_title("7. Double-slit interference pattern")

    x_min = -0.01
    x_max = 0.01

    intensities = []
    for index in range(points):
        x = x_min + (x_max - x_min) * index / (points - 1)
        intensity = double_slit_intensity(
            x,
            wavelength,
            slit_separation,
            screen_distance,
        )
        intensities.append(intensity)

    symbols = " .:-=+*#%@"

    for intensity in intensities:
        normalized = intensity / 4.0
        symbol_index = min(
            len(symbols) - 1,
            int(normalized * (len(symbols) - 1)),
        )
        print(symbols[symbol_index], end="")
    print()

    print(
        """
Bright regions occur where the two probability amplitudes reinforce each
other. Dark regions occur where they cancel.

For constructive interference:

    d sin(theta) = m lambda

For destructive interference:

    d sin(theta) = (m + 1/2) lambda

The experiment demonstrates that the wave-like structure appears in the
distribution of detection events.
"""
    )


# ============================================================================
# SECTION 9: SINGLE-PARTICLE INTERFERENCE
# ============================================================================

@dataclass
class DetectionEvent:
    """One localized detection event on a one-dimensional screen."""

    position: float
    probability_density: float


def normalized_probability_distribution(
    values: Sequence[float],
) -> List[float]:
    """
    Normalize non-negative weights so they sum to one.

    This corresponds to converting relative probability weights into a
    discrete probability distribution.
    """
    total = sum(values)
    if total <= 0:
        raise ValueError("Probability weights must have positive total.")
    return [value / total for value in values]


def cumulative_distribution(
    probabilities: Sequence[float],
) -> List[float]:
    """Construct a cumulative distribution for random sampling."""
    cumulative = []
    running_total = 0.0

    for probability in probabilities:
        running_total += probability
        cumulative.append(running_total)

    # Protect against tiny floating-point rounding errors.
    cumulative[-1] = 1.0
    return cumulative


def sample_discrete_distribution(
    probabilities: Sequence[float],
    rng: random.Random,
) -> int:
    """Sample one index according to a discrete probability distribution."""
    cumulative = cumulative_distribution(probabilities)
    random_value = rng.random()

    for index, threshold in enumerate(cumulative):
        if random_value <= threshold:
            return index

    return len(probabilities) - 1


def single_particle_double_slit_demo(
    shots: int = 5000,
    seed: int = 7,
) -> None:
    """
    Simulate individual particle detections.

    Each simulated event is a localized point. The distribution of many points
    approaches the interference probability distribution.
    """
    print_title("8. Single-particle detection and interference")

    rng = random.Random(seed)

    point_count = 101
    x_min = -0.01
    x_max = 0.01

    positions = [
        x_min + (x_max - x_min) * i / (point_count - 1)
        for i in range(point_count)
    ]

    raw_weights = [
        double_slit_intensity(
            x,
            wavelength=5.0e-7,
            slit_separation=2.0e-4,
            screen_distance=1.0,
        )
        for x in positions
    ]

    probabilities = normalized_probability_distribution(raw_weights)

    counts = [0] * point_count

    for _ in range(shots):
        index = sample_discrete_distribution(probabilities, rng)
        counts[index] += 1

    max_count = max(counts)

    print(f"Number of individual detection events: {shots}")
    print("\nApproximate accumulated pattern:")

    for index in range(0, point_count, 2):
        bar_length = int(45 * counts[index] / max_count) if max_count else 0
        print(f"{positions[index]: .5f} m | {'#' * bar_length}")

    print(
        """
Each detection is represented as a localized event rather than as a blurred
fraction of a particle.

The interference pattern is not obtained because each individual electron
splits into two classical half-electrons on the detector. Instead, quantum
mechanics assigns amplitudes to alternatives, calculates a probability
distribution, and individual measurements sample from that distribution.

As the number of detections increases, statistical fluctuations become less
important and the interference pattern becomes clearer.
"""
    )


# ============================================================================
# SECTION 10: PROBABILITY AMPLITUDES
# ============================================================================

@dataclass(frozen=True)
class ComplexAmplitude:
    """
    Minimal complex-number representation.

    Python already provides complex arithmetic. This class is included to
    make the physical meaning of magnitude and phase explicit.
    """

    real: float
    imaginary: float

    def __add__(self, other: "ComplexAmplitude") -> "ComplexAmplitude":
        return ComplexAmplitude(
            self.real + other.real,
            self.imaginary + other.imaginary,
        )

    def magnitude_squared(self) -> float:
        """Born-rule probability weight: |A|^2."""
        return self.real**2 + self.imaginary**2

    def phase(self) -> float:
        """Phase angle in radians."""
        return math.atan2(self.imaginary, self.real)


def probability_from_amplitudes(
    amplitude_1: complex,
    amplitude_2: complex,
) -> Tuple[float, float, float]:
    """
    Compare two ways of combining alternatives.

    Quantum:
        P = |A1 + A2|^2

    Classical exclusive alternatives:
        P = |A1|^2 + |A2|^2

    The difference is the interference term.
    """
    quantum_probability = abs(amplitude_1 + amplitude_2) ** 2
    classical_sum = abs(amplitude_1) ** 2 + abs(amplitude_2) ** 2
    interference_term = quantum_probability - classical_sum

    return quantum_probability, classical_sum, interference_term


def probability_amplitude_demo() -> None:
    """Show constructive, destructive, and partial interference."""
    print_title("9. Probability amplitudes and Born's rule")

    examples = [
        ("constructive", 1.0 + 0.0j, 1.0 + 0.0j),
        ("destructive", 1.0 + 0.0j, -1.0 + 0.0j),
        ("quadrature", 1.0 + 0.0j, 0.0 + 1.0j),
    ]

    for name, a1, a2 in examples:
        quantum, classical, interference = probability_from_amplitudes(a1, a2)
        print(
            f"{name:12s}: "
            f"|A1+A2|^2={quantum:.3f}, "
            f"|A1|^2+|A2|^2={classical:.3f}, "
            f"interference={interference:+.3f}"
        )

    print(
        """
Born's rule states that the probability density associated with a wave
function psi is proportional to:

    P(x) = |psi(x)|^2

The wave function itself is generally complex-valued. It is the squared
magnitude that gives an observable probability density.

The crucial quantum rule is:

    add amplitudes first
    then take the squared magnitude

This differs from simply adding classical probabilities when alternatives
remain coherent.
"""
    )


# ============================================================================
# SECTION 11: COMPLEMENTARITY
# ============================================================================

def complementarity_demo() -> None:
    """
    Explain complementarity without treating wave and particle as literal
    mutually exclusive substances.
    """
    print_title("10. Complementarity")

    print(
        """
Complementarity is associated especially with Bohr's interpretation of
quantum phenomena.

Different experimental arrangements can reveal different aspects of a
quantum system.

A two-slit arrangement with no usable which-path information can produce
interference.

An arrangement that determines which path was taken can destroy the
interference visibility.

The important principle is not:

    "The particle secretly chooses to become a wave."

A better description is:

    "The experimental arrangement determines which quantum properties can
     be observed together."

This is a statement about quantum measurement and incompatible experimental
contexts.
"""
    )


# ============================================================================
# SECTION 12: WHICH-PATH INFORMATION AND VISIBILITY
# ============================================================================

def duality_visibility_model(
    distinguishability: float,
) -> float:
    """
    Simplified idealized duality relation.

    For a balanced two-path system, an important complementarity relation is:

        D^2 + V^2 <= 1

    where:
        D = path distinguishability
        V = interference visibility

    This function uses the ideal equality case:

        V = sqrt(1 - D^2)
    """
    if not 0.0 <= distinguishability <= 1.0:
        raise ValueError("Distinguishability must lie between 0 and 1.")

    return math.sqrt(max(0.0, 1.0 - distinguishability**2))


def which_path_demo() -> None:
    """Calculate idealized interference visibility for different D values."""
    print_title("11. Which-path information and interference visibility")

    for distinguishability in [0.0, 0.25, 0.5, 0.75, 1.0]:
        visibility = duality_visibility_model(distinguishability)
        print(
            f"D = {distinguishability:.2f} -> "
            f"ideal V = {visibility:.3f}"
        )

    print(
        """
Visibility can be defined as:

    V = (I_max - I_min) / (I_max + I_min)

A perfectly visible ideal interference pattern has V = 1.
A pattern with no interference contrast has V = 0.

Path distinguishability D ranges from 0 to 1 in the simplified model.

For an ideal balanced two-path experiment:

    D^2 + V^2 <= 1

The inequality captures a trade-off: increasing usable path information can
reduce interference visibility.
"""
    )


# ============================================================================
# SECTION 13: PHOTON COUNTING AND SHOT NOISE
# ============================================================================

def poisson_like_counts_demo(
    expected_count: float,
    trials: int = 10000,
    seed: int = 11,
) -> None:
    """
    Demonstrate statistical fluctuations using a simple Poisson sampler.

    The standard deviation of Poisson counts is approximately sqrt(lambda).
    This illustrates why repeated quantum measurements produce statistical
    distributions rather than identical detector counts.
    """
    print_title("12. Quantum measurement statistics")

    if expected_count <= 0:
        raise ValueError("Expected count must be positive.")

    rng = random.Random(seed)

    # Knuth's algorithm is practical here for moderate expected_count values.
    def poisson_sample(lam: float) -> int:
        threshold = math.exp(-lam)
        product = 1.0
        count = 0

        while product > threshold:
            count += 1
            product *= rng.random()

        return count - 1

    samples = [poisson_sample(expected_count) for _ in range(trials)]

    mean = sum(samples) / trials
    variance = sum((x - mean) ** 2 for x in samples) / trials
    standard_deviation = math.sqrt(variance)

    print(f"Expected count:     {expected_count:.2f}")
    print(f"Measured mean:      {mean:.3f}")
    print(f"Measured std. dev.: {standard_deviation:.3f}")
    print(f"Theoretical sqrt(lambda): {math.sqrt(expected_count):.3f}")

    print(
        """
Quantum experiments frequently require repeated trials because individual
measurement outcomes are probabilistic.

A statistical pattern can be highly reproducible even though the outcome of
one individual measurement is not deterministic in the classical sense.
"""
    )


# ============================================================================
# SECTION 14: ELECTRON DIFFRACTION
# ============================================================================

def bragg_diffraction_angle(
    wavelength_m: float,
    lattice_spacing_m: float,
    order: int = 1,
) -> float:
    """
    Calculate Bragg angle from:

        n lambda = 2 d sin(theta)

    Returns theta in radians.
    """
    if wavelength_m <= 0 or lattice_spacing_m <= 0:
        raise ValueError("Wavelength and lattice spacing must be positive.")
    if order <= 0:
        raise ValueError("Diffraction order must be positive.")

    argument = order * wavelength_m / (2.0 * lattice_spacing_m)

    if argument > 1.0:
        raise ValueError("The selected diffraction order is not physically allowed.")

    return math.asin(argument)


def electron_acceleration_wavelength(
    accelerating_voltage: float,
) -> float:
    """
    Nonrelativistic electron de Broglie wavelength after acceleration through V.

    K = eV
    p = sqrt(2 m K)
    lambda = h / p

    This approximation becomes inaccurate at sufficiently high voltages,
    where relativistic corrections should be included.
    """
    if accelerating_voltage <= 0:
        raise ValueError("Accelerating voltage must be positive.")

    kinetic_energy = ELEMENTARY_CHARGE * accelerating_voltage
    momentum = math.sqrt(2.0 * ELECTRON_MASS * kinetic_energy)
    return de_broglie_wavelength(momentum)


def electron_diffraction_demo() -> None:
    """Show why electron wavelengths can be comparable to crystal spacings."""
    print_title("13. Electron diffraction")

    voltages = [10, 100, 1_000, 10_000]

    for voltage in voltages:
        wavelength = electron_acceleration_wavelength(voltage)
        print(
            f"Electron accelerated through {voltage:5d} V -> "
            f"lambda = {wavelength:.3e} m"
        )

    lattice_spacing = 2.0e-10
    wavelength = electron_acceleration_wavelength(150.0)

    print(f"\nExample lattice spacing: {lattice_spacing:.3e} m")
    print(f"Example electron wavelength: {wavelength:.3e} m")

    try:
        angle = bragg_diffraction_angle(
            wavelength,
            lattice_spacing,
            order=1,
        )
        print(f"First-order Bragg angle: {math.degrees(angle):.3f} degrees")
    except ValueError as error:
        print(f"Diffraction calculation: {error}")

    print(
        """
Electron diffraction is direct evidence that matter can exhibit wave-like
behavior.

A crystal provides a periodic structure that can act as a diffraction
system. When the de Broglie wavelength is comparable to atomic spacings,
strong diffraction features can occur.
"""
    )


# ============================================================================
# SECTION 15: COMPTON SCATTERING
# ============================================================================

def compton_wavelength_shift(
    scattering_angle_radians: float,
) -> float:
    """
    Compton wavelength shift:

        Delta lambda = h/(m_e c) * (1 - cos(theta))
    """
    if not 0.0 <= scattering_angle_radians <= math.pi:
        raise ValueError("Scattering angle must lie between 0 and pi.")

    electron_compton_wavelength = (
        PLANCK_CONSTANT / (ELECTRON_MASS * SPEED_OF_LIGHT)
    )

    return electron_compton_wavelength * (
        1.0 - math.cos(scattering_angle_radians)
    )


def compton_demo() -> None:
    """Calculate Compton wavelength shifts."""
    print_title("14. Compton scattering")

    print(
        """
Compton scattering demonstrates particle-like momentum and energy transfer
for electromagnetic radiation.

The wavelength shift is:

    Delta lambda = h/(m_e c) (1 - cos(theta))

where theta is the photon scattering angle.
"""
    )

    for degrees in [0, 45, 90, 135, 180]:
        angle = math.radians(degrees)
        shift = compton_wavelength_shift(angle)
        print(f"theta = {degrees:3d} degrees -> shift = {shift:.3e} m")


# ============================================================================
# SECTION 16: PHASE AND GROUP VELOCITY
# ============================================================================

def phase_velocity(
    angular_frequency: float,
    wave_number: float,
) -> float:
    """v_phase = omega / k."""
    if wave_number == 0:
        raise ValueError("Wave number cannot be zero.")
    return angular_frequency / wave_number


def group_velocity_from_samples(
    frequencies: Sequence[float],
    wave_numbers: Sequence[float],
) -> List[float]:
    """
    Estimate group velocity d omega / d k using finite differences.

    Here frequencies are ordinary frequencies f. Angular frequency is
    omega = 2 pi f.
    """
    if len(frequencies) != len(wave_numbers):
        raise ValueError("Input sequences must have equal length.")
    if len(frequencies) < 2:
        raise ValueError("At least two samples are required.")

    angular_frequencies = [2.0 * math.pi * f for f in frequencies]
    velocities = []

    for i in range(len(frequencies) - 1):
        delta_omega = angular_frequencies[i + 1] - angular_frequencies[i]
        delta_k = wave_numbers[i + 1] - wave_numbers[i]

        if delta_k == 0:
            raise ValueError("Wave-number samples must not be identical.")

        velocities.append(delta_omega / delta_k)

    return velocities


def velocity_demo() -> None:
    """Demonstrate phase and group velocity concepts."""
    print_title("15. Phase velocity and group velocity")

    wavelength = 600e-9
    frequency = frequency_from_wavelength(wavelength)
    k = 2.0 * math.pi / wavelength
    omega = 2.0 * math.pi * frequency

    v_phase = phase_velocity(omega, k)

    print(f"Electromagnetic frequency: {frequency:.3e} Hz")
    print(f"Wave number:              {k:.3e} rad/m")
    print(f"Phase velocity:            {v_phase:.3e} m/s")

    print(
        """
For a dispersion relation omega(k):

    phase velocity = omega / k
    group velocity = d omega / d k

A localized wave packet is associated more naturally with group velocity,
while the motion of individual phase fronts is described by phase velocity.

For electromagnetic waves in vacuum, the two velocities are both c.
In dispersive media they need not be equal.
"""
    )


# ============================================================================
# SECTION 17: WAVE PACKETS
# ============================================================================

def gaussian_wave_packet(
    position: float,
    center: float,
    width: float,
    wave_number: float,
) -> complex:
    """
    Construct a simple Gaussian-modulated complex wave.

    psi(x) = exp(-(x-x0)^2/(4 sigma^2)) exp(i k x)

    This is not a complete time-dependent solution of every physical system.
    It is a useful mathematical model for demonstrating localization plus
    oscillatory phase.
    """
    if width <= 0:
        raise ValueError("Width must be positive.")

    envelope = math.exp(
        -((position - center) ** 2) / (4.0 * width**2)
    )
    phase = wave_number * position
    return envelope * complex(math.cos(phase), math.sin(phase))


def wave_packet_demo() -> None:
    """Show amplitude localization and phase oscillation."""
    print_title("16. Wave packets and localization")

    center = 0.0
    width = 1.0
    wavelength = 0.8
    wave_number = 2.0 * math.pi / wavelength

    positions = [x / 4.0 for x in range(-16, 17)]

    print("x       |psi|       |psi|^2")
    for position in positions:
        amplitude = gaussian_wave_packet(
            position,
            center,
            width,
            wave_number,
        )
        magnitude = abs(amplitude)
        probability_density = magnitude**2
        print(
            f"{position:6.2f}  "
            f"{magnitude:8.4f}  "
            f"{probability_density:10.6f}"
        )

    print(
        """
A pure plane wave has a precisely defined wave number but is spread across
space.

A localized particle-like state can be represented by a wave packet, which
contains a range of wave numbers.

This connection leads naturally to uncertainty relations.
"""
    )


# ============================================================================
# SECTION 18: UNCERTAINTY PRINCIPLE
# ============================================================================

def uncertainty_lower_bound() -> float:
    """Return hbar/2, the position-momentum uncertainty lower bound."""
    return HBAR / 2.0


def uncertainty_demo() -> None:
    """
    Demonstrate the numerical lower bound:

        Delta x Delta p >= hbar / 2

    The inequality is not simply an error caused by poor instruments.
    It follows from the mathematical structure of quantum observables.
    """
    print_title("17. Position-momentum uncertainty")

    lower_bound = uncertainty_lower_bound()

    examples = [
        ("large position spread", 1e-9, 1e-25),
        ("near lower-bound example", 1e-9, lower_bound / 1e-9),
        ("localized state", 1e-12, 1e-22),
    ]

    for name, delta_x, delta_p in examples:
        product = delta_x * delta_p
        satisfies = product >= lower_bound
        print(
            f"{name:24s}: "
            f"Delta x Delta p = {product:.3e}, "
            f"bound = {lower_bound:.3e}, "
            f"satisfies={satisfies}"
        )

    print(
        """
Heisenberg's uncertainty relation is:

    Delta x Delta p >= hbar / 2

More generally, for two observables A and B:

    Delta A Delta B >= 1/2 |< [A, B] >|

where [A, B] = AB - BA is the commutator.

The position-momentum relation reflects the non-commuting structure of the
corresponding quantum operators.
"""
    )


# ============================================================================
# SECTION 19: FOURIER INTERPRETATION OF UNCERTAINTY
# ============================================================================

def discrete_fourier_transform(
    samples: Sequence[complex],
) -> List[complex]:
    """
    Compute a direct discrete Fourier transform.

    This intentionally uses the straightforward O(N^2) formula so the
    relationship between position-space and wave-number-space representations
    remains visible.

    X_k = sum_n x_n exp(-2 pi i k n / N)
    """
    n_samples = len(samples)

    if n_samples == 0:
        raise ValueError("At least one sample is required.")

    transformed = []

    for k in range(n_samples):
        total = 0.0 + 0.0j

        for n, sample in enumerate(samples):
            angle = -2.0 * math.pi * k * n / n_samples
            total += sample * complex(math.cos(angle), math.sin(angle))

        transformed.append(total)

    return transformed


def fourier_localization_demo() -> None:
    """
    Compare a broad and narrow Gaussian in position space.

    A narrow spatial wave packet requires a broader range of wave numbers.
    """
    print_title("18. Fourier viewpoint of wave-particle duality")

    sample_count = 32

    widths = [2.5, 0.7]

    for width in widths:
        samples = []

        for n in range(sample_count):
            x = n - sample_count / 2
            amplitude = math.exp(-(x**2) / (2.0 * width**2))
            samples.append(complex(amplitude, 0.0))

        spectrum = discrete_fourier_transform(samples)
        magnitudes = [abs(value) for value in spectrum]

        significant = [
            index
            for index, magnitude in enumerate(magnitudes)
            if magnitude > 0.10 * max(magnitudes)
        ]

        print(
            f"Position width={width:.2f} -> "
            f"significant Fourier bins={len(significant)}"
        )

    print(
        """
A wave packet is a superposition of many wave numbers.

Schematically:

    psi(x) = integral phi(k) exp(i k x) dk

A narrower psi(x) generally requires a broader distribution of k.

Since:

    p = hbar k

the spread in wave number corresponds directly to a spread in momentum.

This provides an intuitive mathematical route to:

    Delta x Delta p >= hbar / 2
"""
    )


# ============================================================================
# SECTION 20: QUANTUM STATES AS VECTORS
# ============================================================================

@dataclass
class QubitState:
    """
    Minimal two-level quantum state.

    A normalized state has the form:

        |psi> = alpha |0> + beta |1>

    with:

        |alpha|^2 + |beta|^2 = 1
    """

    alpha: complex
    beta: complex

    def norm_squared(self) -> float:
        """Return the squared norm."""
        return abs(self.alpha) ** 2 + abs(self.beta) ** 2

    def normalize(self) -> "QubitState":
        """Return a normalized copy."""
        norm = math.sqrt(self.norm_squared())

        if norm == 0:
            raise ValueError("The zero vector cannot represent a quantum state.")

        return QubitState(
            self.alpha / norm,
            self.beta / norm,
        )

    def measurement_probabilities(self) -> Tuple[float, float]:
        """Born-rule probabilities for measurement in the computational basis."""
        normalized = self.normalize()
        return abs(normalized.alpha) ** 2, abs(normalized.beta) ** 2

    def measure(self, rng: random.Random) -> int:
        """
        Simulate a projective measurement in the {|0>, |1>} basis.

        The returned value is one definite outcome. Repeated measurements
        follow the Born probabilities.
        """
        p0, p1 = self.measurement_probabilities()
        value = rng.random()

        if value < p0:
            return 0
        return 1


def quantum_state_demo() -> None:
    """Demonstrate superposition and measurement probabilities."""
    print_title("19. Quantum states and superposition")

    state = QubitState(
        alpha=1.0 / math.sqrt(2.0),
        beta=1.0 / math.sqrt(2.0),
    )

    p0, p1 = state.measurement_probabilities()

    print(f"State alpha: {state.alpha}")
    print(f"State beta:  {state.beta}")
    print(f"P(0):        {p0:.3f}")
    print(f"P(1):        {p1:.3f}")

    rng = random.Random(19)
    trials = 10_000
    counts = [0, 0]

    for _ in range(trials):
        result = state.measure(rng)
        counts[result] += 1

    print(f"After {trials} simulated measurements:")
    print(f"Outcome 0: {counts[0]} ({counts[0] / trials:.3f})")
    print(f"Outcome 1: {counts[1]} ({counts[1] / trials:.3f})")

    print(
        """
A quantum state can be a coherent superposition of basis states.

The coefficients are probability amplitudes, not probabilities.

For:

    |psi> = alpha |0> + beta |1>

the probabilities are:

    P(0) = |alpha|^2
    P(1) = |beta|^2

provided the state is normalized.
"""
    )


# ============================================================================
# SECTION 21: RELATIVE PHASE
# ============================================================================

def relative_phase_demo() -> None:
    """
    Show that global phase does not affect measurement probabilities while
    relative phase can affect interference.
    """
    print_title("20. Global phase versus relative phase")

    magnitude = 1.0 / math.sqrt(2.0)

    state_a = QubitState(
        magnitude,
        magnitude,
    )

    state_b = QubitState(
        1j * magnitude,
        1j * magnitude,
    )

    state_c = QubitState(
        magnitude,
        -magnitude,
    )

    print("State A probabilities:", state_a.measurement_probabilities())
    print("State B probabilities:", state_b.measurement_probabilities())
    print("State C probabilities:", state_c.measurement_probabilities())

    print(
        """
Multiplying every component by the same phase factor:

    |psi> -> exp(i gamma) |psi>

does not change ordinary measurement probabilities. This is called a global
phase.

Changing the phase between components can change interference outcomes. This
is relative phase, and it is physically important.
"""
    )


# ============================================================================
# SECTION 22: TWO-PATH QUANTUM INTERFERENCE AS A QUBIT MODEL
# ============================================================================

def two_path_interference_probability(
    relative_phase_radians: float,
) -> float:
    """
    Probability for constructive/destructive interference in a simple balanced
    two-path model.

    P = cos^2(phi / 2)

    This is a normalized illustrative model.
    """
    return math.cos(relative_phase_radians / 2.0) ** 2


def phase_scan_demo() -> None:
    """Scan the interference probability over relative phase."""
    print_title("21. Relative phase controls interference")

    for degrees in range(0, 361, 30):
        phase = math.radians(degrees)
        probability = two_path_interference_probability(phase)
        bar = "#" * int(40 * probability)

        print(
            f"phase={degrees:3d} degrees | "
            f"P={probability:.3f} | {bar}"
        )

    print(
        """
A relative phase difference can continuously move a system between
constructive and destructive interference.

This is why phase is not merely mathematical decoration. It directly affects
observable probabilities.
"""
    )


# ============================================================================
# SECTION 23: QUANTUM MEASUREMENT AND STATE UPDATE
# ============================================================================

def projective_measurement_demo() -> None:
    """
    Demonstrate the idealized state-update rule for a two-level system.

    If measurement produces outcome 0, the state becomes |0>.
    If measurement produces outcome 1, the state becomes |1>.

    This is a simplified projective measurement model, not a universal model
    for every physical measurement.
    """
    print_title("22. Measurement and state update")

    state = QubitState(
        alpha=0.6 + 0.0j,
        beta=0.8 + 0.0j,
    )

    print("Initial probabilities:", state.measurement_probabilities())

    rng = random.Random(22)
    result = state.measure(rng)

    if result == 0:
        post_measurement = QubitState(1.0 + 0.0j, 0.0 + 0.0j)
    else:
        post_measurement = QubitState(0.0 + 0.0j, 1.0 + 0.0j)

    print(f"Measured outcome: {result}")
    print(
        "Post-measurement probabilities:",
        post_measurement.measurement_probabilities(),
    )

    print(
        """
In an ideal projective measurement, an initially superposed state can be
updated to an eigenstate corresponding to the observed result.

The phrase "wave-function collapse" is a shorthand for this state-update
aspect of standard measurement theory.

Different interpretations of quantum mechanics give different conceptual
accounts of what collapse means, but the mathematical predictions of the
standard measurement rule remain well defined for the situations modeled
here.
"""
    )


# ============================================================================
# SECTION 24: OBSERVABLES AND EIGENSTATES
# ============================================================================

def expectation_value(
    probabilities: Sequence[float],
    values: Sequence[float],
) -> float:
    """Calculate an expectation value sum(P_i * value_i)."""
    if len(probabilities) != len(values):
        raise ValueError("Probabilities and values must have equal length.")

    if any(probability < 0 for probability in probabilities):
        raise ValueError("Probabilities cannot be negative.")

    total_probability = sum(probabilities)

    if not math.isclose(total_probability, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("Probabilities must sum to 1.")

    return sum(p * value for p, value in zip(probabilities, values))


def variance(
    probabilities: Sequence[float],
    values: Sequence[float],
) -> float:
    """Calculate variance from a discrete probability distribution."""
    mean = expectation_value(probabilities, values)
    return sum(
        p * (value - mean) ** 2
        for p, value in zip(probabilities, values)
    )


def observables_demo() -> None:
    """Demonstrate expectation values and uncertainty."""
    print_title("23. Observables, expectation values, and variance")

    probabilities = [0.25, 0.50, 0.25]
    values = [-1.0, 0.0, 1.0]

    mean = expectation_value(probabilities, values)
    spread = math.sqrt(variance(probabilities, values))

    print(f"Possible outcomes: {values}")
    print(f"Probabilities:      {probabilities}")
    print(f"Expectation value:  {mean:.3f}")
    print(f"Standard deviation: {spread:.3f}")

    print(
        """
A quantum observable is represented mathematically by an operator.

Measurement outcomes correspond to allowed eigenvalues of that operator.
The expectation value predicts the average result of many identically
prepared measurements.

For a discrete probability model:

    <A> = sum_i P_i a_i

The quantum operator formulation generalizes this idea and accounts for
superposition, non-commuting observables, and state-dependent probabilities.
"""
    )


# ============================================================================
# SECTION 25: CLASSICAL PROBABILITY VERSUS QUANTUM AMPLITUDE
# ============================================================================

def classical_vs_quantum_demo() -> None:
    """
    Give a concrete numerical comparison between classical alternatives and
    coherent quantum alternatives.
    """
    print_title("24. Classical probability versus quantum amplitudes")

    p_a = 0.5
    p_b = 0.5

    classical_total = p_a + p_b

    amplitude_a = math.sqrt(p_a)
    amplitude_b = math.sqrt(p_b)

    constructive = abs(amplitude_a + amplitude_b) ** 2
    destructive = abs(amplitude_a - amplitude_b) ** 2

    print(f"Classical exclusive probability: {classical_total:.3f}")
    print(f"Constructive quantum combination: {constructive:.3f}")
    print(f"Destructive quantum combination:  {destructive:.3f}")

    print(
        """
Classical mutually exclusive alternatives are normally combined as
probabilities.

Quantum coherent alternatives are combined as amplitudes.

For amplitudes A and B:

    |A + B|^2
      = |A|^2 + |B|^2 + 2 Re(A* B)

The last term is the interference term.

If coherence is lost, the cross term can disappear from the experimentally
observable statistics, leading to behavior resembling classical probability
addition.
"""
    )


# ============================================================================
# SECTION 26: DECOHERENCE
# ============================================================================

def decoherence_visibility(
    coherence_factor: float,
) -> float:
    """
    Simple phenomenological visibility model.

    coherence_factor = 1 means full coherence.
    coherence_factor = 0 means no observable interference in this model.
    """
    if not 0.0 <= coherence_factor <= 1.0:
        raise ValueError("Coherence factor must be between 0 and 1.")

    return coherence_factor


def decoherence_demo() -> None:
    """Show how loss of coherence reduces interference visibility."""
    print_title("25. Decoherence")

    for coherence in [1.0, 0.8, 0.5, 0.2, 0.0]:
        visibility = decoherence_visibility(coherence)
        print(
            f"Coherence factor={coherence:.1f} -> "
            f"modeled visibility={visibility:.1f}"
        )

    print(
        """
Decoherence occurs when a quantum system becomes correlated with uncontrolled
degrees of freedom in its environment.

The system's phase relationships become inaccessible when the environment
effectively records information about alternatives.

Decoherence helps explain why interference is difficult to observe for large,
strongly interacting systems.

It is important not to equate decoherence automatically with every meaning of
wave-function collapse. Decoherence describes the suppression of observable
interference through environmental entanglement; interpretations of quantum
measurement may assign different meanings to the remaining state description.
"""
    )


# ============================================================================
# SECTION 27: ENTANGLEMENT AND A COMMON DISTINCTION
# ============================================================================

def entanglement_demo() -> None:
    """
    Illustrate the structure of a Bell-like two-qubit state without implementing
    a full quantum-computing framework.

    |Psi> = (|00> + |11>) / sqrt(2)

    This state is entangled because it cannot be factored into one independent
    single-qubit state for each subsystem.
    """
    print_title("26. Entanglement versus ordinary wave-particle duality")

    coefficient = 1.0 / math.sqrt(2.0)

    amplitudes = {
        "00": coefficient,
        "01": 0.0,
        "10": 0.0,
        "11": coefficient,
    }

    probabilities = {
        state: abs(amplitude) ** 2
        for state, amplitude in amplitudes.items()
    }

    for state, probability in probabilities.items():
        print(f"P({state}) = {probability:.3f}")

    print(
        """
Entanglement is related to superposition and quantum amplitudes, but it is
not identical to wave-particle duality.

A two-particle entangled state can contain correlations that cannot be
represented as a product of independent states.

For the Bell-like state:

    |Psi> = (|00> + |11>) / sqrt(2)

measurement of both particles gives matching outcomes in this basis.

Entanglement concerns the structure of composite quantum states. Wave-particle
duality concerns the wave-like and particle-like behavior seen in quantum
phenomena.
"""
    )


# ============================================================================
# SECTION 28: DOUBLE-SLIT LIMITS
# ============================================================================

def slit_spacing_and_fringe_demo() -> None:
    """
    Calculate approximate fringe spacing.

    For small angles:

        x_m ≈ m lambda L / d

    Therefore adjacent bright-fringe spacing is approximately:

        Delta x ≈ lambda L / d
    """
    print_title("27. Fringe spacing and experimental design")

    wavelength = 500e-9
    screen_distance = 2.0
    slit_separation = 0.2e-3

    fringe_spacing = wavelength * screen_distance / slit_separation

    print(f"Wavelength:       {wavelength:.3e} m")
    print(f"Screen distance:  {screen_distance:.3f} m")
    print(f"Slit separation:  {slit_separation:.3e} m")
    print(f"Fringe spacing:   {fringe_spacing:.3e} m")

    print(
        """
The small-angle approximation gives:

    Delta x ≈ lambda L / d

Consequences:
    * increasing wavelength increases fringe spacing
    * increasing screen distance increases fringe spacing
    * increasing slit separation decreases fringe spacing

These relationships are useful when designing an interference experiment.
"""
    )


# ============================================================================
# SECTION 29: SINGLE-SLIT DIFFRACTION
# ============================================================================

def single_slit_first_minimum_angle(
    wavelength: float,
    slit_width: float,
) -> float:
    """
    First minimum of a single-slit diffraction pattern:

        a sin(theta) = lambda

    for the first minimum.
    """
    if wavelength <= 0 or slit_width <= 0:
        raise ValueError("Wavelength and slit width must be positive.")

    argument = wavelength / slit_width

    if argument > 1.0:
        raise ValueError("No first minimum exists at a real angle in this model.")

    return math.asin(argument)


def diffraction_demo() -> None:
    """Demonstrate the role of aperture width in diffraction."""
    print_title("28. Diffraction")

    wavelength = 600e-9

    for slit_width in [1e-3, 1e-4, 1e-5]:
        angle = single_slit_first_minimum_angle(
            wavelength,
            slit_width,
        )

        print(
            f"slit width={slit_width:.1e} m -> "
            f"first minimum={math.degrees(angle):.5f} degrees"
        )

    print(
        """
Diffraction becomes significant when the wavelength is not negligible
compared with the relevant aperture or structural scale.

For a single slit of width a, the first minimum approximately satisfies:

    a sin(theta) = lambda

This provides another route to observing wave behavior.
"""
    )


# ============================================================================
# SECTION 30: PHOTON MOMENTUM
# ============================================================================

def photon_momentum_from_wavelength(wavelength_m: float) -> float:
    """
    Photon momentum:

        p = h / lambda = E / c
    """
    if wavelength_m <= 0:
        raise ValueError("Wavelength must be positive.")
    return PLANCK_CONSTANT / wavelength_m


def photon_momentum_demo() -> None:
    """Demonstrate photon energy and momentum together."""
    print_title("29. Photon energy and momentum")

    wavelength = 500e-9

    energy = photon_energy_from_wavelength(wavelength)
    momentum = photon_momentum_from_wavelength(wavelength)

    print(f"Wavelength: {wavelength:.3e} m")
    print(f"Energy:     {energy:.3e} J")
    print(f"Energy:     {joules_to_electron_volts(energy):.3f} eV")
    print(f"Momentum:   {momentum:.3e} kg m/s")
    print(f"E / p:      {energy / momentum:.3e} m/s")

    print(
        """
For a photon:

    E = h f
    p = h / lambda
    E = p c

The photon has zero rest mass but carries energy and momentum.

This is one reason electromagnetic radiation cannot be adequately described
as a purely classical continuous wave when considering interactions at the
quantum level.
"""
    )


# ============================================================================
# SECTION 31: PARTICLE-LIKE DETECTION VERSUS WAVE-LIKE PROPAGATION
# ============================================================================

def conceptual_comparison() -> None:
    """Present a compact comparison of the two experimentally visible aspects."""
    print_title("30. Wave-like versus particle-like behavior")

    comparison = [
        ("Interference", "Characteristic wave phenomenon"),
        ("Diffraction", "Characteristic wave phenomenon"),
        ("Localized detector click", "Particle-like measurement outcome"),
        ("Photon energy hf", "Quantized energy transfer"),
        ("de Broglie wavelength h/p", "Matter-wave relation"),
        ("Photoelectric threshold", "Particle-like photon energy"),
        ("Compton shift", "Particle-like momentum transfer"),
        ("Probability amplitude", "Quantum wave description"),
    ]

    width = max(len(left) for left, _ in comparison)

    for left, right in comparison:
        print(f"{left:<{width}} : {right}")


# ============================================================================
# SECTION 32: LIMITS OF THE CLASSICAL APPROXIMATION
# ============================================================================

def classical_limit_demo() -> None:
    """
    Compare matter wavelengths with a characteristic scale.

    A wave effect is difficult to resolve when lambda is much smaller than
    the experimental length scale.
    """
    print_title("31. Why macroscopic objects usually look classical")

    characteristic_scale = 1.0e-3

    objects = [
        ("electron", ELECTRON_MASS, 1e6),
        ("dust particle", 1e-15, 1.0),
        ("small grain", 1e-12, 1.0),
        ("1 kg object", 1.0, 1.0),
    ]

    for name, mass, velocity in objects:
        wavelength = de_broglie_wavelength(
            nonrelativistic_momentum(mass, velocity)
        )
        ratio = wavelength / characteristic_scale

        print(
            f"{name:15s}: "
            f"lambda={wavelength:.3e} m, "
            f"lambda/scale={ratio:.3e}"
        )

    print(
        """
The smallness of a de Broglie wavelength alone is not the complete
explanation of classical behavior.

Large systems also interact strongly with their environments, making
decoherence important.

The classical limit therefore involves several connected effects:
    * action scales much larger than hbar
    * very small relevant de Broglie wavelengths
    * environmental decoherence
    * coarse-grained measurements
    * large numbers of degrees of freedom
"""
    )


# ============================================================================
# SECTION 33: ACTION AND THE CLASSICAL LIMIT
# ============================================================================

def action_phase_demo() -> None:
    """
    Show the dimensionless phase scale S/hbar.

    Quantum path amplitudes often contain phases related to:

        exp(i S / hbar)

When actions are very large compared with hbar, phases can vary rapidly and
destructive interference tends to suppress many non-classical paths, leaving
the classical stationary-action paths especially important.
    """
    print_title("32. Action, phase, and the classical limit")

    actions = [
        ("microscopic example", 1e-34),
        ("moderate action", 1e-30),
        ("macroscopic action", 1e-20),
    ]

    for name, action in actions:
        phase_scale = action / HBAR
        print(
            f"{name:22s}: S/hbar = {phase_scale:.3e}"
        )

    print(
        """
Quantum amplitudes can contain phases of the form:

    exp(i S / hbar)

where S is an action.

When S is comparable to hbar, quantum phase effects are readily relevant.

When S is enormously larger than hbar, phase variations can become extremely
rapid. Interference between many contributions can then strongly favor paths
near stationary action, providing a connection between quantum mechanics and
classical mechanics.
"""
    )


# ============================================================================
# SECTION 34: EDGE CASES AND EXCEPTIONS
# ============================================================================

def edge_cases_demo() -> None:
    """Demonstrate important mathematical and physical edge cases."""
    print_title("33. Edge cases and exceptions")

    cases = [
        ("zero wavelength", lambda: frequency_from_wavelength(0.0)),
        ("negative wavelength", lambda: frequency_from_wavelength(-1.0)),
        ("zero momentum", lambda: de_broglie_wavelength(0.0)),
        ("superluminal speed", lambda: relativistic_momentum(
            ELECTRON_MASS,
            SPEED_OF_LIGHT,
        )),
        ("invalid probability", lambda: duality_visibility_model(1.5)),
    ]

    for name, operation in cases:
        try:
            operation()
        except ValueError as error:
            print(f"{name:22s}: correctly rejected -> {error}")

    print(
        """
Important physical edge cases:

1. A photon cannot be treated as an ordinary massive particle moving below c.
2. The simple nonrelativistic de Broglie expression using p = mv fails at
   sufficiently high speeds.
3. A probability distribution must be normalized.
4. A wave function is not itself a probability density; its squared magnitude
   provides the probability density.
5. Not every quantum state produces visible interference in every measurement.
6. Decoherence can suppress interference without changing the underlying
   quantum formalism into classical mechanics at the fundamental level.
7. Wave-particle duality does not imply that all waves are quantum particles.
"""
    )


# ============================================================================
# SECTION 35: COMMON MISCONCEPTIONS
# ============================================================================

def misconceptions_demo() -> None:
    """Print corrections to common conceptual mistakes."""
    print_title("34. Common misconceptions")

    misconceptions = [
        (
            "An electron is literally a classical wave and a classical ball.",
            "Quantum states are not required to fit either classical category."
        ),
        (
            "The wave function is a physical material wave in ordinary space.",
            "Its interpretation depends on the system and representation; "
            "in standard nonrelativistic QM, |psi|^2 gives position probability density."
        ),
        (
            "A detector sees half a particle at each slit.",
            "A detector records localized outcomes; amplitudes determine their distribution."
        ),
        (
            "Increasing light intensity always increases photoelectron energy.",
            "For fixed frequency, photon energy remains hf; intensity mainly "
            "changes photon flux."
        ),
        (
            "The uncertainty principle is just bad experimental equipment.",
            "The position-momentum relation follows from non-commuting operators "
            "and the Fourier structure of quantum states."
        ),
        (
            "Quantum randomness means the theory has no mathematical structure.",
            "Quantum probabilities are calculated from precisely defined states "
            "and operators."
        ),
        (
            "Wave-particle duality means quantum objects physically transform "
            "from one substance into another.",
            "The observed behavior depends on the quantum state and measurement arrangement."
        ),
    ]

    for misconception, correction in misconceptions:
        print(f"\nMisconception: {misconception}")
        print(f"Correction:    {correction}")


# ============================================================================
# SECTION 36: EXPERIMENTAL PARAMETERS
# ============================================================================

@dataclass
class DoubleSlitExperiment:
    """
    Parameterized idealized double-slit experiment.

    Attributes:
        wavelength: wavelength of the relevant quantum wave
        slit_separation: distance between slit centers
        screen_distance: source-to-screen distance
    """

    wavelength: float
    slit_separation: float
    screen_distance: float

    def fringe_spacing(self) -> float:
        """Small-angle approximation for adjacent bright fringes."""
        if self.wavelength <= 0:
            raise ValueError("Wavelength must be positive.")
        if self.slit_separation <= 0:
            raise ValueError("Slit separation must be positive.")
        if self.screen_distance <= 0:
            raise ValueError("Screen distance must be positive.")

        return (
            self.wavelength
            * self.screen_distance
            / self.slit_separation
        )

    def first_bright_fringe_position(self) -> float:
        """Approximate m=1 bright-fringe position."""
        return self.fringe_spacing()


def parameterized_experiment_demo() -> None:
    """Use an experiment object to demonstrate reusable modeling."""
    print_title("35. Parameterized quantum experiment")

    experiment = DoubleSlitExperiment(
        wavelength=450e-9,
        slit_separation=0.15e-3,
        screen_distance=1.5,
    )

    print(f"Fringe spacing: {experiment.fringe_spacing():.3e} m")
    print(
        "First-order bright fringe position:",
        f"{experiment.first_bright_fringe_position():.3e} m",
    )


# ============================================================================
# SECTION 37: NUMERICAL PRECISION AND MODEL LIMITATIONS
# ============================================================================

def numerical_limitations_demo() -> None:
    """Explain limitations of the simplified calculations."""
    print_title("36. Numerical and physical limitations")

    print(
        """
This educational script intentionally uses simple models.

Numerical limitations:
    * direct Fourier transformation is O(N^2)
    * floating-point arithmetic introduces rounding error
    * ASCII patterns have low spatial resolution
    * Monte Carlo simulations contain statistical noise

Physical-model limitations:
    * the nonrelativistic electron wavelength formula fails at high energy
    * ideal two-slit formulas use approximations such as small angles
    * real slits have finite width and produce envelope effects
    * real detectors have finite efficiency and resolution
    * real sources may have finite coherence length
    * environmental interactions can produce decoherence
    * real quantum systems may require spin, relativistic quantum mechanics,
      quantum field theory, or many-body theory

The calculations therefore illustrate principles rather than reproduce every
detail of an experimental apparatus.
"""
    )


# ============================================================================
# SECTION 38: PERFORMANCE CONSIDERATIONS
# ============================================================================

def performance_demo() -> None:
    """Explain algorithmic complexity relevant to the educational code."""
    print_title("37. Performance considerations")

    print(
        """
The script intentionally favors transparency over maximum performance.

Examples:

1. Discrete Fourier transform
       Complexity: O(N^2)

   A Fast Fourier Transform can reduce the typical complexity to O(N log N).

2. Monte Carlo measurement simulation
       Complexity: O(N)

   N is the number of simulated measurement events.

3. Double-slit pattern generation
       Complexity: O(M)

   M is the number of screen positions.

4. Poisson sampling
       The simple Knuth algorithm is convenient for moderate event rates.
       Specialized algorithms are preferable for very large rates.

For scientific production code, vectorized numerical libraries and validated
scientific routines would generally be preferred.
"""
    )


# ============================================================================
# SECTION 39: SECURITY CONSIDERATIONS
# ============================================================================

def security_considerations_demo() -> None:
    """Discuss security in the context of a self-contained scientific script."""
    print_title("38. Security considerations")

    print(
        """
This script performs local mathematical calculations and does not:
    * access a network
    * execute shell commands
    * read arbitrary files
    * accept untrusted executable code
    * dynamically import user-provided modules

That makes the basic example relatively low risk.

When adapting scientific scripts for production systems, security concerns
can become relevant if the program:
    * accepts arbitrary formulas from users
    * evaluates expressions dynamically
    * loads serialized objects from untrusted sources
    * reads experimental files supplied by unknown parties
    * exposes calculations through a network service

Avoid unrestricted eval() or exec() for user-controlled expressions. Use a
restricted parser or an explicitly defined grammar instead.
"""
    )


# ============================================================================
# SECTION 40: DEBUGGING AND VALIDATION
# ============================================================================

def validation_demo() -> None:
    """Run physical sanity checks on important equations."""
    print_title("39. Debugging and validation")

    wavelength = 500e-9
    frequency = frequency_from_wavelength(wavelength)

    # For vacuum electromagnetic radiation, f * lambda should equal c.
    calculated_speed = frequency * wavelength
    assert math.isclose(
        calculated_speed,
        SPEED_OF_LIGHT,
        rel_tol=1e-12,
    )

    # Photon energy must be positive for positive frequency.
    energy = photon_energy_from_frequency(frequency)
    assert energy > 0.0

    # A normalized qubit must have total probability one.
    state = QubitState(3.0 + 0.0j, 4.0 + 0.0j).normalize()
    p0, p1 = state.measurement_probabilities()

    assert math.isclose(p0 + p1, 1.0, rel_tol=1e-12)
    assert 0.0 <= p0 <= 1.0
    assert 0.0 <= p1 <= 1.0

    # Complementarity model should remain inside [0, 1].
    for distinguishability in [0.0, 0.3, 0.7, 1.0]:
        visibility = duality_visibility_model(distinguishability)
        assert 0.0 <= visibility <= 1.0

    print("All validation checks passed.")

    print(
        """
Scientific debugging should test both software behavior and physical
consistency.

Useful checks include:
    * dimensional consistency
    * limiting cases
    * conservation laws
    * normalization
    * symmetry
    * known analytical results
    * parameter ranges
    * comparison against independent calculations
"""
    )


# ============================================================================
# SECTION 41: UNIT TESTS
# ============================================================================

def run_unit_tests() -> None:
    """Run lightweight tests using only Python's standard assert mechanism."""
    print_title("40. Automated tests")

    # Fundamental electromagnetic relation.
    assert math.isclose(
        frequency_from_wavelength(1.0),
        SPEED_OF_LIGHT,
        rel_tol=1e-15,
    )

    assert math.isclose(
        wavelength_from_frequency(SPEED_OF_LIGHT),
        1.0,
        rel_tol=1e-15,
    )

    # Photon energy.
    frequency = 1.0e14
    expected_energy = PLANCK_CONSTANT * frequency
    assert math.isclose(
        photon_energy_from_frequency(frequency),
        expected_energy,
        rel_tol=1e-15,
    )

    # de Broglie relation.
    momentum = 2.0e-24
    expected_lambda = PLANCK_CONSTANT / momentum
    assert math.isclose(
        de_broglie_wavelength(momentum),
        expected_lambda,
        rel_tol=1e-15,
    )

    # Probability normalization.
    probabilities = normalized_probability_distribution([1.0, 2.0, 3.0])
    assert math.isclose(sum(probabilities), 1.0, rel_tol=1e-12)

    # Qubit normalization.
    state = QubitState(3.0 + 0.0j, 4.0 + 0.0j).normalize()
    assert math.isclose(state.norm_squared(), 1.0, rel_tol=1e-12)

    # Expectation value.
    mean = expectation_value(
        probabilities=[0.25, 0.5, 0.25],
        values=[-1.0, 0.0, 1.0],
    )
    assert math.isclose(mean, 0.0, abs_tol=1e-12)

    # Compton shift is zero for forward scattering.
    assert math.isclose(
        compton_wavelength_shift(0.0),
        0.0,
        abs_tol=1e-40,
    )

    # 180-degree scattering gives twice the Compton wavelength.
    compton_lambda = PLANCK_CONSTANT / (
        ELECTRON_MASS * SPEED_OF_LIGHT
    )
    assert math.isclose(
        compton_wavelength_shift(math.pi),
        2.0 * compton_lambda,
        rel_tol=1e-12,
    )

    # Input validation.
    invalid_functions: List[Callable[[], object]] = [
        lambda: frequency_from_wavelength(0.0),
        lambda: de_broglie_wavelength(-1.0),
        lambda: duality_visibility_model(2.0),
        lambda: QubitState(0.0j, 0.0j).normalize(),
    ]

    for function in invalid_functions:
        try:
            function()
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid input was not rejected.")

    print("All unit tests passed.")


# ============================================================================
# SECTION 42: ADVANCED SYNTHESIS
# ============================================================================

def advanced_synthesis() -> None:
    """
    Connect the main mathematical relationships.

    The goal is to show that wave-particle duality is not a collection of
    unrelated facts. Several equations describe different manifestations of
    the same quantum structure.
    """
    print_title("41. Advanced synthesis")

    print(
        """
The central relationships can be connected as follows:

Electromagnetic radiation:
    E = h f
    p = h / lambda
    E = p c

Matter:
    lambda = h / p

Wave description:
    k = 2 pi / lambda
    omega = 2 pi f

Quantum mechanics:
    p = hbar k
    E = hbar omega

Wave function:
    P(x) = |psi(x)|^2

Superposition:
    psi = c1 psi1 + c2 psi2

Interference:
    P = |A1 + A2|^2

Uncertainty:
    Delta x Delta p >= hbar / 2

The same quantum formalism therefore links:
    * wavelength
    * momentum
    * energy
    * phase
    * interference
    * probability
    * localization
    * measurement statistics

This is why wave-particle duality is better understood as a limitation of
classical categories than as a literal alternation between two classical
identities.
"""
    )


# ============================================================================
# SECTION 43: REAL-WORLD APPLICATIONS
# ============================================================================

def real_world_applications_demo() -> None:
    """List applications where quantum wave behavior has practical relevance."""
    print_title("42. Real-world applications")

    applications = [
        (
            "Electron microscopy",
            "Electron wavelengths enable spatial resolution far beyond "
            "ordinary visible-light microscopy."
        ),
        (
            "Electron diffraction",
            "Crystal structures can be investigated through matter-wave diffraction."
        ),
        (
            "Neutron diffraction",
            "Neutron wavelengths allow investigation of crystal and magnetic structures."
        ),
        (
            "Electron crystallography",
            "Electron scattering and diffraction provide structural information."
        ),
        (
            "Semiconductor physics",
            "Quantum states and wave behavior are fundamental to nanoscale devices."
        ),
        (
            "Quantum tunneling devices",
            "Wave-function behavior permits transmission through classically "
            "forbidden barriers."
        ),
        (
            "Scanning tunneling microscopy",
            "Quantum tunneling produces a measurable current sensitive to surface structure."
        ),
        (
            "Laser technology",
            "Quantized energy levels and coherent electromagnetic fields are central "
            "to laser operation."
        ),
        (
            "Quantum information",
            "Superposition, relative phase, measurement, and entanglement form "
            "the mathematical basis of quantum information processing."
        ),
    ]

    for name, explanation in applications:
        print(f"\n{name}:")
        print(f"    {explanation}")


# ============================================================================
# SECTION 44: TOPIC-SPECIFIC STUDY QUESTIONS
# ============================================================================

def study_questions() -> None:
    """Print questions that can be answered from the demonstrations."""
    print_title("43. Conceptual and quantitative study questions")

    questions = [
        "Why does a two-slit experiment produce an interference pattern?",
        "Why does increasing photon intensity not change photon energy at fixed frequency?",
        "How does de Broglie's relation connect momentum and wavelength?",
        "Why are electron diffraction effects easier to observe than diffraction "
        "of ordinary macroscopic objects?",
        "What is the difference between a wave function and a probability density?",
        "Why must quantum amplitudes be added before taking their squared magnitude?",
        "What is the role of relative phase in interference?",
        "What is the difference between global and relative phase?",
        "How does which-path information affect interference?",
        "What does the uncertainty relation actually state?",
        "How does Fourier analysis connect localization and momentum spread?",
        "Why is decoherence relevant to the classical limit?",
        "Why is entanglement not synonymous with wave-particle duality?",
        "When must relativistic momentum replace p = mv?",
        "Which approximations are used by the idealized double-slit model?",
    ]

    for number, question in enumerate(questions, start=1):
        print(f"{number:2d}. {question}")


# ============================================================================
# SECTION 45: COMPLETE DEMONSTRATION RUNNER
# ============================================================================

def run_all_demonstrations() -> None:
    """Execute the entire educational sequence."""
    explain_basic_duality()
    classical_wave_demo()
    planck_quantization_demo()
    photoelectric_effect_demo()
    matter_wave_demo()
    relativistic_de_broglie_demo()
    ascii_interference_pattern(
        wavelength=5.0e-7,
        slit_separation=2.0e-4,
        screen_distance=1.0,
    )
    single_particle_double_slit_demo()
    probability_amplitude_demo()
    complementarity_demo()
    which_path_demo()
    poisson_like_counts_demo(expected_count=25.0)
    electron_diffraction_demo()
    compton_demo()
    velocity_demo()
    wave_packet_demo()
    uncertainty_demo()
    fourier_localization_demo()
    quantum_state_demo()
    relative_phase_demo()
    phase_scan_demo()
    projective_measurement_demo()
    observables_demo()
    classical_vs_quantum_demo()
    decoherence_demo()
    entanglement_demo()
    slit_spacing_and_fringe_demo()
    diffraction_demo()
    photon_momentum_demo()
    conceptual_comparison()
    classical_limit_demo()
    action_phase_demo()
    edge_cases_demo()
    misconceptions_demo()
    parameterized_experiment_demo()
    numerical_limitations_demo()
    performance_demo()
    security_considerations_demo()
    validation_demo()
    run_unit_tests()
    advanced_synthesis()
    real_world_applications_demo()
    study_questions()


# ============================================================================
# SECTION 46: MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print_title("Wave-Particle Duality and Quantum Behavior")
    print(
        """
This program is an executable study guide.

It moves from classical wave and particle concepts to:
    photon quantization
    matter waves
    interference
    diffraction
    probability amplitudes
    uncertainty
    measurement
    decoherence
    and the quantum-to-classical transition.

All calculations use Python's standard library.
"""
    )

    run_all_demonstrations()
