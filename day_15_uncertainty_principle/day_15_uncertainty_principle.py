"""
Quantum Uncertainty and the Heisenberg Uncertainty Principle
=============================================================

A self-contained study and computational demonstration of quantum uncertainty.

The script develops the subject from basic probability and wavefunctions to:
- expectation values
- variance and standard deviation
- position and momentum uncertainty
- Fourier-transform relationship between x and p
- Heisenberg's uncertainty relation
- the commutator derivation
- Gaussian minimum-uncertainty wave packets
- numerical uncertainty calculations
- wave-packet spreading
- the uncertainty relation for arbitrary states
- Robertson's generalized relation
- the distinction between uncertainty and measurement error
- finite numerical grids and discretization effects
- statistical verification through repeated measurements

Only the Python standard library is used.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. Physical constants and elementary utilities
# ---------------------------------------------------------------------------

# SI constants. The reduced Planck constant is the natural constant for the
# uncertainty relation:
#
#     Δx Δp >= ħ / 2
#
HBAR = 1.054_571_817e-34       # J s
PLANCK = 2.0 * math.pi * HBAR  # J s
ELECTRON_MASS = 9.109_383_7139e-31  # kg


def square(value: float) -> float:
    return value * value


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean() requires at least one value")
    return sum(values) / len(values)


def variance(values: Sequence[float]) -> float:
    """
    Population variance.

    Quantum expectation values are mathematical expectations over a
    probability distribution, so division by N is appropriate here.
    """
    if not values:
        raise ValueError("variance() requires at least one value")
    average = mean(values)
    return sum(square(x - average) for x in values) / len(values)


def standard_deviation(values: Sequence[float]) -> float:
    return math.sqrt(variance(values))


# ---------------------------------------------------------------------------
# 2. Probability distributions and the meaning of uncertainty
# ---------------------------------------------------------------------------

def normalize_probability(probabilities: Sequence[float]) -> List[float]:
    total = sum(probabilities)

    if total <= 0.0:
        raise ValueError("Probability total must be positive")

    return [p / total for p in probabilities]


def expected_value(
    values: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    if len(values) != len(probabilities):
        raise ValueError("Values and probabilities must have equal lengths")

    probabilities = normalize_probability(probabilities)
    return sum(x * p for x, p in zip(values, probabilities))


def probability_variance(
    values: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    if len(values) != len(probabilities):
        raise ValueError("Values and probabilities must have equal lengths")

    probabilities = normalize_probability(probabilities)
    expectation = expected_value(values, probabilities)
    return sum(
        square(x - expectation) * p
        for x, p in zip(values, probabilities)
    )


print("=" * 78)
print("QUANTUM UNCERTAINTY PRINCIPLE")
print("=" * 78)

print("\n1. Classical statistical uncertainty")
classical_values = [1.0, 2.0, 3.0, 4.0]
classical_probabilities = [0.1, 0.2, 0.4, 0.3]

classical_mean = expected_value(classical_values, classical_probabilities)
classical_sigma = math.sqrt(
    probability_variance(classical_values, classical_probabilities)
)

print(f"Possible values: {classical_values}")
print(f"Probabilities:    {classical_probabilities}")
print(f"Expected value:   {classical_mean:.4f}")
print(f"Standard deviation: {classical_sigma:.4f}")

print(
    "\nA standard deviation measures the spread of outcomes. "
    "Quantum mechanics uses the same statistical concept, but the "
    "probability distribution comes from a quantum state."
)


# ---------------------------------------------------------------------------
# 3. Complex amplitudes and wavefunctions
# ---------------------------------------------------------------------------

def complex_probability_amplitude(amplitude: complex) -> float:
    """
    Born's rule:

        probability density = |psi|^2

    The absolute square of a complex amplitude is always real and
    non-negative.
    """
    return abs(amplitude) ** 2


def normalize_discrete_wavefunction(
    wavefunction: Sequence[complex],
) -> List[complex]:
    """
    Normalize a discretized wavefunction using the discrete Euclidean norm.

    For a grid with spacing dx, a physical discretization normally includes
    sqrt(dx) in the normalization. This simple function is useful for
    demonstrations where the grid spacing is handled separately.
    """
    norm_squared = sum(abs(psi) ** 2 for psi in wavefunction)

    if norm_squared <= 0.0:
        raise ValueError("Wavefunction cannot be identically zero")

    normalization = math.sqrt(norm_squared)
    return [psi / normalization for psi in wavefunction]


def gaussian_wavefunction(
    x: float,
    center: float,
    position_sigma: float,
    momentum: float,
    hbar: float = HBAR,
) -> complex:
    """
    A normalized Gaussian packet, up to the continuous normalization factor.

        psi(x) proportional to
            exp[-(x-x0)^2/(4 sigma_x^2)]
            exp[i p0 x / hbar]

    Its probability density has position standard deviation sigma_x.

    The momentum standard deviation is

        sigma_p = hbar / (2 sigma_x)

    so the packet saturates the Heisenberg bound.
    """
    if position_sigma <= 0.0:
        raise ValueError("Position sigma must be positive")

    normalization = (
        1.0 / (2.0 * math.pi * position_sigma**2)
    ) ** 0.25

    envelope = math.exp(
        -square(x - center) / (4.0 * square(position_sigma))
    )

    phase = cmath.exp(1j * momentum * x / hbar)

    return normalization * envelope * phase


# ---------------------------------------------------------------------------
# 4. Analytical Gaussian uncertainty
# ---------------------------------------------------------------------------

@dataclass
class GaussianPacket:
    center_x: float
    sigma_x: float
    mean_momentum: float
    hbar: float = HBAR

    @property
    def sigma_p(self) -> float:
        return self.hbar / (2.0 * self.sigma_x)

    @property
    def uncertainty_product(self) -> float:
        return self.sigma_x * self.sigma_p

    @property
    def lower_bound(self) -> float:
        return self.hbar / 2.0

    def verify_minimum_uncertainty(self) -> bool:
        return math.isclose(
            self.uncertainty_product,
            self.lower_bound,
            rel_tol=1e-12,
            abs_tol=0.0,
        )


print("\n2. Gaussian minimum-uncertainty wave packet")

packet = GaussianPacket(
    center_x=0.0,
    sigma_x=1.0e-10,
    mean_momentum=1.0e-24,
)

print(f"Position uncertainty Δx = {packet.sigma_x:.6e} m")
print(f"Momentum uncertainty Δp = {packet.sigma_p:.6e} kg m/s")
print(f"Δx Δp = {packet.uncertainty_product:.6e} J s")
print(f"ħ/2  = {packet.lower_bound:.6e} J s")
print(f"Saturates bound: {packet.verify_minimum_uncertainty()}")


# ---------------------------------------------------------------------------
# 5. Why localization increases momentum uncertainty
# ---------------------------------------------------------------------------

def gaussian_momentum_uncertainty(
    position_uncertainty: float,
    hbar: float = HBAR,
) -> float:
    if position_uncertainty <= 0.0:
        raise ValueError("Position uncertainty must be positive")

    return hbar / (2.0 * position_uncertainty)


print("\n3. Localization versus momentum spread")

for sigma_x in [1e-9, 1e-10, 1e-11, 1e-12]:
    sigma_p = gaussian_momentum_uncertainty(sigma_x)
    print(
        f"Δx = {sigma_x:.1e} m  ->  "
        f"minimum Gaussian Δp = {sigma_p:.3e} kg m/s"
    )

print(
    "\nThe relation is not saying that position and momentum cannot both "
    "have values. It says that a quantum state cannot have arbitrarily "
    "small standard deviations for both observables simultaneously."
)


# ---------------------------------------------------------------------------
# 6. Discrete numerical integration
# ---------------------------------------------------------------------------

def trapezoidal_integral(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> float:
    if len(x_values) != len(y_values):
        raise ValueError("Integration arrays must have equal lengths")

    if len(x_values) < 2:
        raise ValueError("At least two points are required")

    total = 0.0

    for i in range(len(x_values) - 1):
        dx = x_values[i + 1] - x_values[i]
        total += 0.5 * (y_values[i] + y_values[i + 1]) * dx

    return total


def normalize_wavefunction_on_grid(
    x_values: Sequence[float],
    wavefunction: Sequence[complex],
) -> List[complex]:
    probability_density = [
        abs(psi) ** 2 for psi in wavefunction
    ]

    norm = trapezoidal_integral(x_values, probability_density)

    if norm <= 0.0:
        raise ValueError("Wavefunction normalization is zero")

    scale = 1.0 / math.sqrt(norm)

    return [psi * scale for psi in wavefunction]


def expectation_from_wavefunction(
    x_values: Sequence[float],
    wavefunction: Sequence[complex],
    observable: Callable[[float], float],
) -> float:
    if len(x_values) != len(wavefunction):
        raise ValueError("Grid and wavefunction sizes must match")

    integrand = [
        abs(psi) ** 2 * observable(x)
        for x, psi in zip(x_values, wavefunction)
    ]

    return trapezoidal_integral(x_values, integrand)


def position_statistics(
    x_values: Sequence[float],
    wavefunction: Sequence[complex],
) -> Tuple[float, float]:
    mean_x = expectation_from_wavefunction(
        x_values,
        wavefunction,
        lambda x: x,
    )

    mean_x_squared = expectation_from_wavefunction(
        x_values,
        wavefunction,
        lambda x: x * x,
    )

    variance_x = max(0.0, mean_x_squared - mean_x * mean_x)

    return mean_x, math.sqrt(variance_x)


print("\n4. Numerical position statistics")

# We use normalized SI-scale-free coordinates here to avoid very small
# floating-point values. One coordinate unit can be interpreted as a
# convenient length scale.
grid = [
    -8.0 + 16.0 * i / 400
    for i in range(401)
]

numerical_wavefunction = [
    gaussian_wavefunction(
        x=x,
        center=0.8,
        position_sigma=1.25,
        momentum=2.0 * HBAR,
    )
    for x in grid
]

numerical_wavefunction = normalize_wavefunction_on_grid(
    grid,
    numerical_wavefunction,
)

numerical_mean_x, numerical_sigma_x = position_statistics(
    grid,
    numerical_wavefunction,
)

print(f"Numerical <x> = {numerical_mean_x:.6f}")
print(f"Numerical Δx  = {numerical_sigma_x:.6f}")
print("Analytical Δx = 1.250000")


# ---------------------------------------------------------------------------
# 7. Momentum from the derivative operator
# ---------------------------------------------------------------------------

def central_derivative(
    values: Sequence[complex],
    spacing: float,
) -> List[complex]:
    """
    Second-order central finite difference.

    Interior points:
        f'(x) ≈ [f(x+dx) - f(x-dx)] / (2dx)

    One-sided differences are used at the boundaries.
    """
    if len(values) < 3:
        raise ValueError("At least three points are required")

    derivative = [0j] * len(values)

    derivative[0] = (values[1] - values[0]) / spacing
    derivative[-1] = (values[-1] - values[-2]) / spacing

    for i in range(1, len(values) - 1):
        derivative[i] = (
            values[i + 1] - values[i - 1]
        ) / (2.0 * spacing)

    return derivative


def momentum_statistics(
    x_values: Sequence[float],
    wavefunction: Sequence[complex],
    hbar: float = 1.0,
) -> Tuple[float, float]:
    """
    Position-space momentum operator:

        p_hat = -i hbar d/dx

    The expectation value is

        <p> = integral psi* (-i hbar dpsi/dx) dx

    and

        <p^2> = integral psi* (-hbar^2 d^2psi/dx^2) dx.

    This function uses finite differences to approximate those derivatives.
    """
    if len(x_values) != len(wavefunction):
        raise ValueError("Grid and wavefunction sizes must match")

    if len(x_values) < 5:
        raise ValueError("A sufficiently large grid is required")

    dx = x_values[1] - x_values[0]

    first_derivative = central_derivative(
        wavefunction,
        dx,
    )

    second_derivative = central_derivative(
        first_derivative,
        dx,
    )

    mean_p_integrand = [
        psi.conjugate() * (-1j * hbar * derivative)
        for psi, derivative in zip(wavefunction, first_derivative)
    ]

    mean_p_squared_integrand = [
        psi.conjugate() * (-hbar * hbar * second)
        for psi, second in zip(wavefunction, second_derivative)
    ]

    mean_p_complex = trapezoidal_integral(
        x_values,
        [z.real for z in mean_p_integrand],
    )

    mean_p_squared_complex = trapezoidal_integral(
        x_values,
        [z.real for z in mean_p_squared_integrand],
    )

    variance_p = max(
        0.0,
        mean_p_squared_complex - mean_p_complex**2,
    )

    return mean_p_complex, math.sqrt(variance_p)


print("\n5. Numerical momentum uncertainty")

dimensionless_grid = [
    -12.0 + 24.0 * i / 1200
    for i in range(1201)
]

dimensionless_sigma_x = 1.0
dimensionless_momentum = 2.5

dimensionless_packet = [
    gaussian_wavefunction(
        x=x,
        center=-0.5,
        position_sigma=dimensionless_sigma_x,
        momentum=dimensionless_momentum,
        hbar=1.0,
    )
    for x in dimensionless_grid
]

dimensionless_packet = normalize_wavefunction_on_grid(
    dimensionless_grid,
    dimensionless_packet,
)

mean_p, sigma_p = momentum_statistics(
    dimensionless_grid,
    dimensionless_packet,
    hbar=1.0,
)

mean_x, sigma_x = position_statistics(
    dimensionless_grid,
    dimensionless_packet,
)

print(f"<x> = {mean_x:.6f}")
print(f"Δx = {sigma_x:.6f}")
print(f"<p> = {mean_p:.6f}")
print(f"Δp = {sigma_p:.6f}")
print(f"Δx Δp = {sigma_x * sigma_p:.6f}")
print(f"ħ/2 = {0.5:.6f}")


# ---------------------------------------------------------------------------
# 8. Fourier-transform relationship
# ---------------------------------------------------------------------------

def discrete_fourier_transform(
    signal: Sequence[complex],
) -> List[complex]:
    """
    Direct discrete Fourier transform.

    This implementation intentionally uses the O(N^2) definition instead
    of an FFT so that the mathematical transformation is transparent.

        F(k) = sum_x f(x) exp(-2π i kx/N)

    For large production computations an FFT is normally preferred because
    it reduces the computational cost to approximately O(N log N).
    """
    n = len(signal)

    if n == 0:
        raise ValueError("Signal must not be empty")

    transformed = []

    for k in range(n):
        total = 0j

        for j, value in enumerate(signal):
            angle = -2.0 * math.pi * k * j / n
            total += value * cmath.exp(1j * angle)

        transformed.append(total)

    return transformed


def inverse_discrete_fourier_transform(
    spectrum: Sequence[complex],
) -> List[complex]:
    n = len(spectrum)

    if n == 0:
        raise ValueError("Spectrum must not be empty")

    result = []

    for j in range(n):
        total = 0j

        for k, value in enumerate(spectrum):
            angle = 2.0 * math.pi * k * j / n
            total += value * cmath.exp(1j * angle)

        result.append(total / n)

    return result


print("\n6. Fourier-transform principle")

small_signal = [
    complex(math.exp(-((x - 4.0) ** 2) / 4.0))
    for x in range(16)
]

spectrum = discrete_fourier_transform(small_signal)
reconstructed = inverse_discrete_fourier_transform(spectrum)

maximum_reconstruction_error = max(
    abs(a - b)
    for a, b in zip(small_signal, reconstructed)
)

print(
    "Maximum reconstruction error after DFT followed by inverse DFT:",
    f"{maximum_reconstruction_error:.3e}",
)

print(
    "\nA narrow position-space wavefunction requires a broad range of "
    "spatial frequencies. Since momentum is related to wave number by "
    "p = ħk, localization and momentum spread are Fourier-dual effects."
)


# ---------------------------------------------------------------------------
# 9. A direct numerical position/momentum uncertainty experiment
# ---------------------------------------------------------------------------

def momentum_distribution_from_dft(
    wavefunction: Sequence[complex],
) -> List[float]:
    """
    Returns an uncalibrated discrete momentum-like probability distribution.

    For this educational demonstration, the Fourier index is used as a
    dimensionless wave-number coordinate. The important point is the
    reciprocal relationship between spatial width and spectral width.
    """
    spectrum = discrete_fourier_transform(wavefunction)
    probabilities = [abs(value) ** 2 for value in spectrum]

    return normalize_probability(probabilities)


def circular_frequency_indices(n: int) -> List[float]:
    """
    Return DFT frequency indices arranged around zero.

    For a discrete spectrum, indices greater than N/2 correspond to
    negative frequencies.
    """
    frequencies = []

    for index in range(n):
        if index <= n // 2:
            frequencies.append(float(index))
        else:
            frequencies.append(float(index - n))

    return frequencies


print("\n7. Position-space width versus momentum-space width")

sample_sizes = [32, 64, 128]

for size in sample_sizes:
    coordinates = [
        -8.0 + 16.0 * i / size
        for i in range(size)
    ]

    packet_values = [
        math.exp(-(x * x) / 2.0)
        for x in coordinates
    ]

    normalized_packet_values = normalize_probability(packet_values)

    x_mean = expected_value(
        coordinates,
        normalized_packet_values,
    )

    x_variance = probability_variance(
        coordinates,
        normalized_packet_values,
    )

    frequencies = circular_frequency_indices(size)
    momentum_probabilities = momentum_distribution_from_dft(
        [complex(value, 0.0) for value in packet_values]
    )

    k_mean = expected_value(
        frequencies,
        momentum_probabilities,
    )

    k_variance = probability_variance(
        frequencies,
        momentum_probabilities,
    )

    print(
        f"N={size:3d} | "
        f"Δx={math.sqrt(x_variance):.4f} | "
        f"Δk={math.sqrt(k_variance):.4f} | "
        f"ΔxΔk={math.sqrt(x_variance * k_variance):.4f}"
    )


# ---------------------------------------------------------------------------
# 10. Operator commutator: [x, p] = iħ
# ---------------------------------------------------------------------------

def position_operator(
    wavefunction: Sequence[complex],
    x_values: Sequence[float],
) -> List[complex]:
    return [
        x * psi
        for x, psi in zip(x_values, wavefunction)
    ]


def momentum_operator(
    wavefunction: Sequence[complex],
    x_values: Sequence[float],
    hbar: float = 1.0,
) -> List[complex]:
    dx = x_values[1] - x_values[0]
    derivative = central_derivative(wavefunction, dx)

    return [
        -1j * hbar * derivative_value
        for derivative_value in derivative
    ]


def apply_x_then_p(
    wavefunction: Sequence[complex],
    x_values: Sequence[float],
    hbar: float = 1.0,
) -> List[complex]:
    return momentum_operator(
        position_operator(wavefunction, x_values),
        x_values,
        hbar,
    )


def apply_p_then_x(
    wavefunction: Sequence[complex],
    x_values: Sequence[float],
    hbar: float = 1.0,
) -> List[complex]:
    return position_operator(
        momentum_operator(wavefunction, x_values, hbar),
        x_values,
    )


print("\n8. Numerical commutator demonstration")

commutator_grid = [
    -5.0 + 10.0 * i / 500
    for i in range(501)
]

commutator_state = [
    gaussian_wavefunction(
        x=x,
        center=0.2,
        position_sigma=0.9,
        momentum=1.5,
        hbar=1.0,
    )
    for x in commutator_grid
]

xp_state = apply_x_then_p(
    commutator_state,
    commutator_grid,
    hbar=1.0,
)

px_state = apply_p_then_x(
    commutator_state,
    commutator_grid,
    hbar=1.0,
)

commutator_state_numerical = [
    xp - px
    for xp, px in zip(xp_state, px_state)
]

expected_commutator_state = [
    1j * psi
    for psi in commutator_state
]

interior_error = max(
    abs(a - b)
    for a, b in zip(
        commutator_state_numerical[5:-5],
        expected_commutator_state[5:-5],
    )
)

print(
    "Interior numerical error in [x,p]psi ≈ i psi:",
    f"{interior_error:.3e}",
)

print(
    "\nThe canonical commutation relation is:"
    "\n    [x_hat, p_hat] = x_hat p_hat - p_hat x_hat = iħ"
    "\n"
    "\nThe nonzero commutator is the mathematical origin of the "
    "position-momentum uncertainty bound."
)


# ---------------------------------------------------------------------------
# 11. Deriving the Robertson uncertainty relation
# ---------------------------------------------------------------------------

def commutator_bound(
    commutator_expectation_magnitude: float,
) -> float:
    """
    Robertson's relation:

        ΔA ΔB >= |< [A,B] >| / 2

    For position and momentum:

        |<[x,p]>| / 2 = ħ/2.
    """
    return commutator_expectation_magnitude / 2.0


print("\n9. General uncertainty relation")

print("For observables A and B:")
print("    ΔA ΔB >= |<[A,B]>| / 2")
print("For x and p:")
print("    [x,p] = iħ")
print("Therefore:")
print("    Δx Δp >= ħ/2")
print(f"Numerical lower bound: {commutator_bound(HBAR):.6e} J s")


# ---------------------------------------------------------------------------
# 12. The stronger Schrödinger uncertainty relation
# ---------------------------------------------------------------------------

def schrodinger_uncertainty_lower_bound(
    commutator_expectation_magnitude: float,
    covariance: float,
) -> float:
    """
    Schrödinger's uncertainty relation:

        ΔA² ΔB² >=
            (1/4)|<[A,B]>|²
            + (1/4)|<{ΔA, ΔB}>|²

    For real-valued covariance represented here as C:

        ΔA² ΔB² >=
            (commutator_term / 2)² + C²

    The covariance term can make the bound stronger than the basic
    Robertson relation.
    """
    return (
        square(commutator_expectation_magnitude / 2.0)
        + square(covariance)
    )


print("\n10. Stronger uncertainty relation")

commutator_term = 1.0
covariance_example = 0.8

stronger_bound = schrodinger_uncertainty_lower_bound(
    commutator_term,
    covariance_example,
)

print(
    "Example with |<[A,B]>| = 1 and covariance = 0.8:"
)
print(
    f"ΔA² ΔB² >= {stronger_bound:.4f}"
)
print(
    "The covariance term matters for correlated or squeezed states."
)


# ---------------------------------------------------------------------------
# 13. Quantum versus classical uncertainty
# ---------------------------------------------------------------------------

@dataclass
class UncertaintyComparison:
    concept: str
    classical_description: str
    quantum_description: str


comparisons = [
    UncertaintyComparison(
        "Probability",
        "Often represents incomplete knowledge or random processes.",
        "Born-rule probabilities arise from the quantum state.",
    ),
    UncertaintyComparison(
        "Position and momentum",
        "A classical particle can be assigned simultaneous exact values.",
        "A quantum state can have nonzero spreads constrained by commutation.",
    ),
    UncertaintyComparison(
        "Standard deviation",
        "Statistical spread of repeated observations.",
        "Statistical spread of repeated measurements of an observable.",
    ),
    UncertaintyComparison(
        "Measurement error",
        "Instrument imperfection or experimental limitation.",
        "Distinct from intrinsic quantum variance.",
    ),
]

print("\n11. Classical and quantum uncertainty")

for comparison in comparisons:
    print(f"\n{comparison.concept}")
    print(f"  Classical: {comparison.classical_description}")
    print(f"  Quantum:   {comparison.quantum_description}")


# ---------------------------------------------------------------------------
# 14. Measurement error is not the uncertainty principle
# ---------------------------------------------------------------------------

def gaussian_measurement_noise(
    true_value: float,
    measurement_sigma: float,
    count: int,
    seed: int = 7,
) -> List[float]:
    if measurement_sigma < 0.0:
        raise ValueError("Measurement sigma cannot be negative")

    if count <= 0:
        raise ValueError("Count must be positive")

    generator = random.Random(seed)

    return [
        true_value + generator.gauss(0.0, measurement_sigma)
        for _ in range(count)
    ]


print("\n12. Measurement error versus quantum uncertainty")

measurements = gaussian_measurement_noise(
    true_value=10.0,
    measurement_sigma=0.25,
    count=1000,
)

print(f"Mean measured value: {mean(measurements):.4f}")
print(
    f"Experimental measurement spread: "
    f"{standard_deviation(measurements):.4f}"
)

print(
    "\nAn experimental instrument can have noise even for a classical "
    "quantity. Improving the instrument does not remove the quantum "
    "uncertainty of a state. Conversely, quantum uncertainty does not "
    "mean every experimental measurement has zero technical error."
)


# ---------------------------------------------------------------------------
# 15. Repeated measurements and Born statistics
# ---------------------------------------------------------------------------

def sample_discrete_distribution(
    outcomes: Sequence[float],
    probabilities: Sequence[float],
    count: int,
    seed: int = 42,
) -> List[float]:
    if len(outcomes) != len(probabilities):
        raise ValueError("Outcomes and probabilities must have equal lengths")

    if count <= 0:
        raise ValueError("Count must be positive")

    normalized = normalize_probability(probabilities)
    generator = random.Random(seed)

    cumulative = []
    running_total = 0.0

    for probability in normalized:
        running_total += probability
        cumulative.append(running_total)

    samples = []

    for _ in range(count):
        random_value = generator.random()

        for outcome, cumulative_probability in zip(
            outcomes,
            cumulative,
        ):
            if random_value <= cumulative_probability:
                samples.append(outcome)
                break

    return samples


print("\n13. Repeated quantum-style measurements")

spin_outcomes = [-1.0, 1.0]
spin_probabilities = [0.3, 0.7]

spin_samples = sample_discrete_distribution(
    spin_outcomes,
    spin_probabilities,
    count=10000,
)

empirical_mean = mean(spin_samples)
empirical_sigma = standard_deviation(spin_samples)

theoretical_mean = expected_value(
    spin_outcomes,
    spin_probabilities,
)

theoretical_sigma = math.sqrt(
    probability_variance(
        spin_outcomes,
        spin_probabilities,
    )
)

print(f"Theoretical <S> = {theoretical_mean:.4f}")
print(f"Empirical <S>   = {empirical_mean:.4f}")
print(f"Theoretical ΔS  = {theoretical_sigma:.4f}")
print(f"Empirical ΔS    = {empirical_sigma:.4f}")

print(
    "\nA single measurement produces one outcome. The expectation value "
    "and standard deviation describe the distribution obtained from "
    "many identically prepared systems."
)


# ---------------------------------------------------------------------------
# 16. Wave-packet spreading
# ---------------------------------------------------------------------------

def free_particle_sigma_x(
    initial_sigma_x: float,
    time: float,
    mass: float,
    hbar: float = HBAR,
) -> float:
    """
    Free-particle Gaussian wave-packet spreading:

        sigma_x(t)
          = sigma_x(0)
            sqrt(1 + [hbar t / (2 m sigma_x(0)^2)]^2)

    A narrower initial packet has a larger momentum spread and therefore
    generally spreads more rapidly.
    """
    if initial_sigma_x <= 0.0:
        raise ValueError("Initial sigma_x must be positive")

    if mass <= 0.0:
        raise ValueError("Mass must be positive")

    factor = hbar * time / (
        2.0 * mass * square(initial_sigma_x)
    )

    return initial_sigma_x * math.sqrt(
        1.0 + square(factor)
    )


print("\n14. Free-particle wave-packet spreading")

initial_width = 1.0e-10
mass = ELECTRON_MASS

for time in [0.0, 1e-16, 1e-15, 1e-14]:
    width = free_particle_sigma_x(
        initial_width,
        time,
        mass,
    )

    print(
        f"t={time:.1e} s -> "
        f"Δx(t)={width:.6e} m"
    )

print(
    "\nWave-packet spreading illustrates the dynamical consequence of "
    "momentum uncertainty. The uncertainty relation itself is a "
    "kinematic statement about a quantum state, while spreading is "
    "a consequence of time evolution under a Hamiltonian."
)


# ---------------------------------------------------------------------------
# 17. A useful timescale for quantum spreading
# ---------------------------------------------------------------------------

def spreading_timescale(
    sigma_x: float,
    mass: float,
    hbar: float = HBAR,
) -> float:
    """
    Characteristic spreading time obtained when

        hbar t / (2 m sigma_x^2) = 1.

    Therefore:

        t = 2 m sigma_x^2 / hbar.
    """
    if sigma_x <= 0.0 or mass <= 0.0:
        raise ValueError("Width and mass must be positive")

    return 2.0 * mass * square(sigma_x) / hbar


print("\n15. Characteristic spreading times")

for sigma in [1e-9, 1e-10, 1e-11]:
    print(
        f"Initial Δx={sigma:.1e} m -> "
        f"spreading time={spreading_timescale(sigma, mass):.3e} s"
    )


# ---------------------------------------------------------------------------
# 18. Edge cases and important limitations
# ---------------------------------------------------------------------------

print("\n16. Edge cases and limitations")

edge_cases = [
    (
        "Zero uncertainty in one observable",
        "An exact eigenstate of an observable can have zero variance "
        "for that observable, but a noncommuting observable can then "
        "have a large or undefined spread depending on the state."
    ),
    (
        "Infinite or non-normalizable idealizations",
        "Plane waves have perfectly definite momentum but are not "
        "normalizable position-space states and have completely "
        "delocalized position."
    ),
    (
        "Bounded observables",
        "Not every pair of observables obeys a position-momentum-style "
        "constant lower bound. The general bound depends on the "
        "commutator and state."
    ),
    (
        "Correlations",
        "Schrodinger's stronger relation includes covariance information "
        "that is absent from the simplest Heisenberg expression."
    ),
    (
        "Numerical derivatives",
        "Finite differences introduce truncation and boundary errors. "
        "Increasing resolution helps only until floating-point and "
        "other numerical effects become important."
    ),
]

for name, explanation in edge_cases:
    print(f"\n{name}:")
    print(f"  {explanation}")


# ---------------------------------------------------------------------------
# 19. Common misconceptions
# ---------------------------------------------------------------------------

print("\n17. Common misconceptions")

misconceptions = {
    "Measurement disturbance":
        "The uncertainty relation is not simply the statement that "
        "measuring position physically kicks a particle and changes "
        "its momentum. It is a property of quantum states and "
        "noncommuting observables.",
    "Poor instruments":
        "Quantum uncertainty is not merely a limitation of laboratory "
        "equipment.",
    "Particle has no state":
        "A quantum state is well-defined even though individual "
        "measurement outcomes are probabilistic.",
    "Everything is uncertain":
        "An observable can have zero variance in an eigenstate.",
    "Energy-time is identical to position-momentum":
        "Time is treated differently from ordinary observables in "
        "standard quantum mechanics, so energy-time relations require "
        "careful interpretation.",
}

for misconception, correction in misconceptions.items():
    print(f"\n{misconception}:")
    print(f"  {correction}")


# ---------------------------------------------------------------------------
# 20. Energy-time relation
# ---------------------------------------------------------------------------

print("\n18. Energy-time uncertainty")

print(
    "A commonly encountered form is:"
    "\n    ΔE Δt ≳ ħ/2"
)

print(
    "Unlike x and p, time is ordinarily a parameter in nonrelativistic "
    "Schrodinger quantum mechanics rather than an operator on the same "
    "footing as position. Consequently, Δt can represent a characteristic "
    "timescale such as a state lifetime, evolution time, or duration of "
    "a process, depending on the formulation."
)


# ---------------------------------------------------------------------------
# 21. Angular position and angular momentum
# ---------------------------------------------------------------------------

print("\n19. Other uncertainty relations")

print(
    "The same mathematical framework applies to many observables."
)
print(
    "For two Hermitian observables A and B:"
)
print(
    "    ΔA ΔB >= |<[A,B]>|/2"
)

print(
    "Examples include components of angular momentum:"
)
print(
    "    [Lx, Ly] = iħ Lz"
)
print(
    "so"
)
print(
    "    ΔLx ΔLy >= ħ |<Lz>| / 2"
)


# ---------------------------------------------------------------------------
# 22. Numerical verification of the Gaussian minimum relation
# ---------------------------------------------------------------------------

def gaussian_uncertainty_table(
    widths: Iterable[float],
    hbar: float = 1.0,
) -> List[Tuple[float, float, float]]:
    rows = []

    for width in widths:
        momentum_width = hbar / (2.0 * width)
        product = width * momentum_width
        rows.append((width, momentum_width, product))

    return rows


print("\n20. Minimum-uncertainty Gaussian table")

for width, momentum_width, product in gaussian_uncertainty_table(
    [0.25, 0.5, 1.0, 2.0, 4.0],
):
    print(
        f"Δx={width:5.2f} | "
        f"Δp={momentum_width:7.4f} | "
        f"ΔxΔp={product:7.4f}"
    )


# ---------------------------------------------------------------------------
# 23. Squeezed-state intuition
# ---------------------------------------------------------------------------

@dataclass
class SqueezedUncertaintyState:
    """
    A simplified uncertainty model.

    A squeezing factor r changes the two quadrature uncertainties as

        ΔX = base * exp(-r)
        ΔP = base * exp(+r)

    Their product remains fixed for an ideal minimum-uncertainty squeezed
    state.

    The variables X and P here represent canonically conjugate
    dimensionless quadratures rather than necessarily literal position
    and momentum.
    """

    base_uncertainty: float = 1.0 / math.sqrt(2.0)
    squeezing_parameter: float = 0.0

    @property
    def delta_x(self) -> float:
        return self.base_uncertainty * math.exp(
            -self.squeezing_parameter
        )

    @property
    def delta_p(self) -> float:
        return self.base_uncertainty * math.exp(
            self.squeezing_parameter
        )

    @property
    def product(self) -> float:
        return self.delta_x * self.delta_p


print("\n21. Squeezing intuition")

for r in [-1.0, 0.0, 1.0]:
    squeezed = SqueezedUncertaintyState(
        squeezing_parameter=r,
    )

    print(
        f"r={r:+.1f} | "
        f"ΔX={squeezed.delta_x:.4f} | "
        f"ΔP={squeezed.delta_p:.4f} | "
        f"product={squeezed.product:.4f}"
    )

print(
    "\nSqueezing redistributes uncertainty between conjugate variables "
    "without violating the uncertainty bound. This principle is important "
    "in quantum optics and precision measurement."
)


# ---------------------------------------------------------------------------
# 24. Numerical stability checks
# ---------------------------------------------------------------------------

def safe_variance(
    mean_square: float,
    square_mean: float,
) -> float:
    """
    Variance can be theoretically non-negative, but floating-point
    subtraction can produce a tiny negative number such as -1e-16.

    Clamping tiny negative values to zero prevents sqrt() from failing.
    """
    value = mean_square - square_mean

    if value < 0.0 and abs(value) < 1e-12:
        return 0.0

    if value < 0.0:
        raise ArithmeticError(
            "Variance became significantly negative; check the calculation."
        )

    return value


print("\n22. Numerical stability")

print(
    "Example safe variance:",
    safe_variance(
        mean_square=4.000000000000001,
        square_mean=4.0,
    ),
)


# ---------------------------------------------------------------------------
# 25. Final computational experiment
# ---------------------------------------------------------------------------

def run_uncertainty_experiment(
    sigma_x: float,
    hbar: float = 1.0,
) -> dict:
    """
    Return a compact set of quantities useful for automated checks.
    """
    sigma_p = hbar / (2.0 * sigma_x)
    product = sigma_x * sigma_p

    return {
        "delta_x": sigma_x,
        "delta_p": sigma_p,
        "product": product,
        "lower_bound": hbar / 2.0,
        "satisfies_uncertainty": product >= hbar / 2.0,
        "saturates_for_gaussian": math.isclose(
            product,
            hbar / 2.0,
            rel_tol=1e-12,
        ),
    }


print("\n23. Automated uncertainty check")

experiment = run_uncertainty_experiment(
    sigma_x=0.75,
    hbar=1.0,
)

for key, value in experiment.items():
    print(f"{key:28s}: {value}")


# ---------------------------------------------------------------------------
# 26. Compact conceptual reference
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("KEY EQUATIONS")
print("=" * 78)

equations = [
    ("Born rule", "P(x) = |ψ(x)|²"),
    ("Expectation", "<A> = ∫ ψ* A ψ dx"),
    ("Variance", "(ΔA)² = <A²> - <A>²"),
    ("Standard deviation", "ΔA = sqrt(<A²> - <A>²)"),
    ("Momentum operator", "p_hat = -iħ d/dx"),
    ("Canonical commutator", "[x_hat, p_hat] = iħ"),
    ("Heisenberg relation", "Δx Δp >= ħ/2"),
    ("Robertson relation", "ΔA ΔB >= |<[A,B]>|/2"),
    (
        "Schrodinger relation",
        "ΔA²ΔB² >= |<[A,B]>|²/4 + covariance_term²",
    ),
    ("de Broglie relation", "p = ħk"),
    (
        "Free Gaussian spreading",
        "σx(t)=σx(0)sqrt(1+[ħt/(2mσx(0)²)]²)",
    ),
]

for name, equation in equations:
    print(f"{name:28s}: {equation}")

print("\nThe script completed successfully.")
