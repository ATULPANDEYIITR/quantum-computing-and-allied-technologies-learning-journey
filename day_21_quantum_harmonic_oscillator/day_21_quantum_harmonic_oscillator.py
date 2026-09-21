"""
Quantum Harmonic Oscillator
===========================

A comprehensive computational study of the quantum harmonic oscillator,
from the classical model and Schrödinger equation to ladder operators,
energy quantization, wavefunctions, expectation values, uncertainty,
coherent states, thermal properties, and numerical verification.

The program uses only the Python standard library.
Numerical calculations use the built-in math module rather than NumPy so
that the file remains self-contained.

Physical conventions
---------------------
Unless otherwise stated:

    hbar = 1
    mass = 1
    angular_frequency = 1

In these dimensionless units:

    H = 1/2 (p^2 + x^2)

and the exact energy spectrum is:

    E_n = n + 1/2

The script also contains functions for arbitrary positive hbar, mass, and
angular frequency where useful.

The code is intended as an executable study file. Running it prints a
structured set of demonstrations and numerical checks.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# Physical constants and basic utilities
# ---------------------------------------------------------------------------

HBAR = 1.0
MASS = 1.0
OMEGA = 1.0

SQRT_PI = math.sqrt(math.pi)


def factorial(n: int) -> int:
    """Return n! with explicit validation."""
    if not isinstance(n, int):
        raise TypeError("factorial requires an integer")
    if n < 0:
        raise ValueError("factorial is undefined for negative integers")
    return math.factorial(n)


def double_factorial_odd(n: int) -> int:
    """
    Return n!! for odd non-negative n.

    This is useful for analytic Gaussian moments such as
        <x^(2k)> = (2k-1)!! / 2^k
    in the dimensionless ground state.
    """
    if n < 0 or n % 2 == 0:
        raise ValueError("n must be a non-negative odd integer")
    result = 1
    for value in range(n, 0, -2):
        result *= value
    return result


def nearly_equal(a: float, b: float, tolerance: float = 1e-9) -> bool:
    """Numerically compare two real values."""
    return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


def complex_nearly_equal(
    a: complex, b: complex, tolerance: float = 1e-9
) -> bool:
    """Numerically compare two complex values."""
    return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


# ---------------------------------------------------------------------------
# Classical harmonic oscillator
# ---------------------------------------------------------------------------

@dataclass
class ClassicalOscillator:
    """
    Classical one-dimensional harmonic oscillator.

    Equation of motion:
        m d²x/dt² + m omega² x = 0

    The solution can be written as:
        x(t) = A cos(omega t + phase)
    """

    mass: float
    omega: float
    amplitude: float
    phase: float = 0.0

    def __post_init__(self) -> None:
        if self.mass <= 0:
            raise ValueError("mass must be positive")
        if self.omega <= 0:
            raise ValueError("omega must be positive")
        if self.amplitude < 0:
            raise ValueError("amplitude cannot be negative")

    def position(self, time: float) -> float:
        return self.amplitude * math.cos(self.omega * time + self.phase)

    def velocity(self, time: float) -> float:
        return -self.amplitude * self.omega * math.sin(
            self.omega * time + self.phase
        )

    def momentum(self, time: float) -> float:
        return self.mass * self.velocity(time)

    def energy(self, time: float) -> float:
        x = self.position(time)
        v = self.velocity(time)
        return 0.5 * self.mass * v * v + 0.5 * self.mass * self.omega**2 * x * x

    def total_energy_from_amplitude(self) -> float:
        return 0.5 * self.mass * self.omega**2 * self.amplitude**2


# ---------------------------------------------------------------------------
# Quantum harmonic oscillator: exact energy spectrum
# ---------------------------------------------------------------------------

def energy_level(
    n: int,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> float:
    """
    Exact quantum harmonic oscillator energy.

        E_n = hbar * omega * (n + 1/2)

    n is the non-negative integer quantum number.
    """
    if not isinstance(n, int):
        raise TypeError("quantum number n must be an integer")
    if n < 0:
        raise ValueError("quantum number n must be non-negative")
    if hbar <= 0 or omega <= 0:
        raise ValueError("hbar and omega must be positive")
    return hbar * omega * (n + 0.5)


def energy_levels(
    number_of_levels: int,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> list[float]:
    """Return the first number_of_levels energies."""
    if number_of_levels <= 0:
        raise ValueError("number_of_levels must be positive")
    return [energy_level(n, hbar, omega) for n in range(number_of_levels)]


def energy_gap(
    n: int,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> float:
    """Energy difference E_(n+1) - E_n."""
    return energy_level(n + 1, hbar, omega) - energy_level(n, hbar, omega)


# ---------------------------------------------------------------------------
# Harmonic oscillator length and dimensionless coordinate
# ---------------------------------------------------------------------------

def oscillator_length(
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    Characteristic oscillator length:

        x0 = sqrt(hbar / (m omega))
    """
    if hbar <= 0 or mass <= 0 or omega <= 0:
        raise ValueError("hbar, mass, and omega must be positive")
    return math.sqrt(hbar / (mass * omega))


def dimensionless_coordinate(
    x: float,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    Dimensionless coordinate:

        xi = x / sqrt(hbar / (m omega))
    """
    return x / oscillator_length(hbar, mass, omega)


# ---------------------------------------------------------------------------
# Hermite polynomials
# ---------------------------------------------------------------------------

def hermite_physicists(n: int, x: float) -> float:
    """
    Physicists' Hermite polynomial H_n(x).

    Recurrence:
        H_0(x) = 1
        H_1(x) = 2x
        H_(n+1)(x) = 2x H_n(x) - 2n H_(n-1)(x)

    These are the Hermite polynomials used by the harmonic oscillator
    eigenfunctions.
    """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")

    if n == 0:
        return 1.0
    if n == 1:
        return 2.0 * x

    h_previous = 1.0
    h_current = 2.0 * x

    for order in range(1, n):
        h_next = 2.0 * x * h_current - 2.0 * order * h_previous
        h_previous, h_current = h_current, h_next

    return h_current


def hermite_coefficients(n: int) -> list[float]:
    """
    Return coefficients of H_n(x) in ascending powers of x.

    This is mainly useful for studying the polynomial structure.
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    # H_0 = 1
    if n == 0:
        return [1.0]

    # H_1 = 2x
    if n == 1:
        return [0.0, 2.0]

    previous = [1.0]
    current = [0.0, 2.0]

    for order in range(1, n):
        # Multiply current polynomial by 2x.
        next_coefficients = [0.0] * (len(current) + 1)
        for power, coefficient in enumerate(current):
            next_coefficients[power + 1] += 2.0 * coefficient

        # Subtract 2*order*previous.
        for power, coefficient in enumerate(previous):
            next_coefficients[power] -= 2.0 * order * coefficient

        previous, current = current, next_coefficients

    return current


# ---------------------------------------------------------------------------
# Exact stationary-state wavefunctions
# ---------------------------------------------------------------------------

def normalization_constant(n: int) -> float:
    """
    Normalization factor for the dimensionless eigenfunction:

        1 / sqrt(2^n n! sqrt(pi))
    """
    return 1.0 / math.sqrt((2.0**n) * factorial(n) * SQRT_PI)


def dimensionless_wavefunction(n: int, xi: float) -> float:
    """
    Normalized dimensionless harmonic oscillator eigenfunction:

        psi_n(xi)
          = [1 / sqrt(2^n n! sqrt(pi))]
            H_n(xi) exp(-xi²/2)

    The physical coordinate version requires the additional factor
    1/sqrt(x_osc).
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    return (
        normalization_constant(n)
        * hermite_physicists(n, xi)
        * math.exp(-0.5 * xi * xi)
    )


def wavefunction(
    n: int,
    x: float,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    Normalized stationary-state wavefunction in physical coordinate x.
    """
    length = oscillator_length(hbar, mass, omega)
    xi = x / length
    return dimensionless_wavefunction(n, xi) / math.sqrt(length)


def probability_density(
    n: int,
    x: float,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """Return |psi_n(x)|²."""
    psi = wavefunction(n, x, hbar, mass, omega)
    return psi * psi


def stationary_state_time_factor(
    n: int,
    time: float,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> complex:
    """
    Time-dependent phase for a stationary energy eigenstate:

        exp(-i E_n t / hbar)

    For a single eigenstate, this phase does not change the probability
    density.
    """
    energy = energy_level(n, hbar, omega)
    return cmath.exp(-1j * energy * time / hbar)


def time_dependent_stationary_wavefunction(
    n: int,
    x: float,
    time: float,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> complex:
    """Return psi_n(x,t) for one energy eigenstate."""
    return wavefunction(n, x, hbar, mass, omega) * stationary_state_time_factor(
        n, time, hbar, omega
    )


# ---------------------------------------------------------------------------
# Numerical integration
# ---------------------------------------------------------------------------

def trapezoidal_integral(
    function: Callable[[float], float],
    lower: float,
    upper: float,
    intervals: int = 10000,
) -> float:
    """
    Numerical integral using the composite trapezoidal rule.

    For a smooth wavefunction, increasing intervals improves accuracy until
    floating-point and truncation limitations become important.
    """
    if intervals <= 0:
        raise ValueError("intervals must be positive")
    if upper <= lower:
        raise ValueError("upper must be greater than lower")

    width = (upper - lower) / intervals
    total = 0.5 * (function(lower) + function(upper))

    for index in range(1, intervals):
        total += function(lower + index * width)

    return total * width


def integrate_complex(
    function: Callable[[float], complex],
    lower: float,
    upper: float,
    intervals: int = 10000,
) -> complex:
    """Complex-valued trapezoidal integration."""
    real_part = trapezoidal_integral(
        lambda x: function(x).real,
        lower,
        upper,
        intervals,
    )
    imaginary_part = trapezoidal_integral(
        lambda x: function(x).imag,
        lower,
        upper,
        intervals,
    )
    return complex(real_part, imaginary_part)


def gaussian_weighted_moment(
    n: int,
    power: int,
    lower: float = -8.0,
    upper: float = 8.0,
) -> float:
    """Numerically evaluate integral x^power |psi_n(x)|² dx in dimensionless units."""
    return trapezoidal_integral(
        lambda x: (x**power) * dimensionless_wavefunction(n, x) ** 2,
        lower,
        upper,
        intervals=12000,
    )


# ---------------------------------------------------------------------------
# Expectation values and uncertainty
# ---------------------------------------------------------------------------

def expectation_x_squared(
    n: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    Exact result:

        <x²>_n = hbar/(m omega) * (n + 1/2)
    """
    return hbar / (mass * omega) * (n + 0.5)


def expectation_p_squared(
    n: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    Exact result:

        <p²>_n = m hbar omega * (n + 1/2)
    """
    return mass * hbar * omega * (n + 0.5)


def expectation_x(n: int) -> float:
    """Parity implies <x> = 0 for every number state."""
    _ = n
    return 0.0


def expectation_p(n: int) -> float:
    """Parity and stationarity imply <p> = 0 for every number state."""
    _ = n
    return 0.0


def position_uncertainty(
    n: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    return math.sqrt(expectation_x_squared(n, hbar, mass, omega))


def momentum_uncertainty(
    n: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    return math.sqrt(expectation_p_squared(n, hbar, mass, omega))


def uncertainty_product(
    n: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    return position_uncertainty(n, hbar, mass, omega) * momentum_uncertainty(
        n, hbar, mass, omega
    )


# ---------------------------------------------------------------------------
# Ladder operators
# ---------------------------------------------------------------------------

def ladder_annihilation_coefficient(n: int) -> float:
    """
    Matrix element:

        a |n> = sqrt(n) |n-1>
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return math.sqrt(n)


def ladder_creation_coefficient(n: int) -> float:
    """
    Matrix element:

        a† |n> = sqrt(n+1) |n+1>
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return math.sqrt(n + 1)


def apply_annihilation(state: Sequence[complex]) -> list[complex]:
    """
    Apply a to a finite number-state vector.

    If |psi> = sum_n c_n |n>, then

        a|psi> = sum_n sqrt(n) c_n |n-1>.

    The highest available basis component is therefore shifted downward.
    """
    result = [0j] * len(state)

    for n in range(1, len(state)):
        result[n - 1] += math.sqrt(n) * state[n]

    return result


def apply_creation(state: Sequence[complex]) -> list[complex]:
    """
    Apply a† within a finite truncated basis.

    The component that would move beyond the final basis state is discarded.
    This is a truncation artifact, not a property of the exact infinite
    Hilbert space.
    """
    result = [0j] * len(state)

    for n in range(len(state) - 1):
        result[n + 1] += math.sqrt(n + 1) * state[n]

    return result


def state_norm(state: Sequence[complex]) -> float:
    """Hilbert-space norm."""
    return math.sqrt(sum(abs(amplitude) ** 2 for amplitude in state))


def normalize_state(state: Sequence[complex]) -> list[complex]:
    """Normalize a finite state vector."""
    norm = state_norm(state)
    if norm == 0:
        raise ValueError("cannot normalize the zero vector")
    return [amplitude / norm for amplitude in state]


def basis_state(n: int, dimension: int) -> list[complex]:
    """Create |n> in a finite number-state basis."""
    if n < 0 or n >= dimension:
        raise ValueError("basis state index outside finite basis")
    state = [0j] * dimension
    state[n] = 1.0 + 0j
    return state


def state_add(a: Sequence[complex], b: Sequence[complex]) -> list[complex]:
    """Add two equal-size state vectors."""
    if len(a) != len(b):
        raise ValueError("state vectors must have equal dimensions")
    return [x + y for x, y in zip(a, b)]


def state_scale(state: Sequence[complex], scalar: complex) -> list[complex]:
    """Multiply a state vector by a scalar."""
    return [scalar * amplitude for amplitude in state]


# ---------------------------------------------------------------------------
# Operator matrices in the number basis
# ---------------------------------------------------------------------------

def zero_matrix(rows: int, columns: int) -> list[list[complex]]:
    return [[0j for _ in range(columns)] for _ in range(rows)]


def identity_matrix(size: int) -> list[list[complex]]:
    matrix = zero_matrix(size, size)
    for index in range(size):
        matrix[index][index] = 1.0 + 0j
    return matrix


def matrix_multiply(
    first: Sequence[Sequence[complex]],
    second: Sequence[Sequence[complex]],
) -> list[list[complex]]:
    """Multiply compatible dense matrices."""
    if not first or not second:
        return []

    rows = len(first)
    inner = len(first[0])
    if len(second) != inner:
        raise ValueError("matrix dimensions are incompatible")

    columns = len(second[0])
    result = zero_matrix(rows, columns)

    for row in range(rows):
        for middle in range(inner):
            if first[row][middle] == 0:
                continue
            for column in range(columns):
                result[row][column] += (
                    first[row][middle] * second[middle][column]
                )

    return result


def matrix_add(
    first: Sequence[Sequence[complex]],
    second: Sequence[Sequence[complex]],
) -> list[list[complex]]:
    """Add equal-size matrices."""
    if len(first) != len(second):
        raise ValueError("matrix dimensions differ")
    if not first:
        return []

    if len(first[0]) != len(second[0]):
        raise ValueError("matrix dimensions differ")

    return [
        [a + b for a, b in zip(row_a, row_b)]
        for row_a, row_b in zip(first, second)
    ]


def matrix_subtract(
    first: Sequence[Sequence[complex]],
    second: Sequence[Sequence[complex]],
) -> list[list[complex]]:
    """Subtract equal-size matrices."""
    if len(first) != len(second):
        raise ValueError("matrix dimensions differ")
    if not first:
        return []

    if len(first[0]) != len(second[0]):
        raise ValueError("matrix dimensions differ")

    return [
        [a - b for a, b in zip(row_a, row_b)]
        for row_a, row_b in zip(first, second)
    ]


def matrix_scale(
    matrix: Sequence[Sequence[complex]],
    scalar: complex,
) -> list[list[complex]]:
    return [[scalar * value for value in row] for row in matrix]


def annihilation_matrix(dimension: int) -> list[list[complex]]:
    """
    Number-basis representation of a.

    Matrix convention:
        matrix[row][column] = <row|a|column>

    Thus:
        <n-1|a|n> = sqrt(n)
    """
    if dimension <= 0:
        raise ValueError("dimension must be positive")

    matrix = zero_matrix(dimension, dimension)

    for n in range(1, dimension):
        matrix[n - 1][n] = math.sqrt(n)

    return matrix


def creation_matrix(dimension: int) -> list[list[complex]]:
    """Number-basis representation of a†."""
    if dimension <= 0:
        raise ValueError("dimension must be positive")

    matrix = zero_matrix(dimension, dimension)

    for n in range(dimension - 1):
        matrix[n + 1][n] = math.sqrt(n + 1)

    return matrix


def commutator(
    first: Sequence[Sequence[complex]],
    second: Sequence[Sequence[complex]],
) -> list[list[complex]]:
    """Return [A,B] = AB - BA."""
    return matrix_subtract(
        matrix_multiply(first, second),
        matrix_multiply(second, first),
    )


def diagonal_hamiltonian(
    dimension: int,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> list[list[complex]]:
    """Hamiltonian matrix in the exact number-state basis."""
    matrix = zero_matrix(dimension, dimension)

    for n in range(dimension):
        matrix[n][n] = energy_level(n, hbar, omega)

    return matrix


# ---------------------------------------------------------------------------
# Position and momentum operators from ladder operators
# ---------------------------------------------------------------------------

def position_matrix(
    dimension: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> list[list[complex]]:
    """
    x = sqrt(hbar/(2m omega)) (a + a†)
    """
    scale = math.sqrt(hbar / (2.0 * mass * omega))
    return matrix_scale(
        matrix_add(
            annihilation_matrix(dimension),
            creation_matrix(dimension),
        ),
        scale,
    )


def momentum_matrix(
    dimension: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> list[list[complex]]:
    """
    p = -i sqrt(m hbar omega / 2) (a - a†)
    """
    scale = -1j * math.sqrt(mass * hbar * omega / 2.0)
    return matrix_scale(
        matrix_subtract(
            annihilation_matrix(dimension),
            creation_matrix(dimension),
        ),
        scale,
    )


def matrix_vector_multiply(
    matrix: Sequence[Sequence[complex]],
    vector: Sequence[complex],
) -> list[complex]:
    """Multiply a dense matrix by a vector."""
    if len(matrix) != len(vector):
        raise ValueError("matrix and vector dimensions differ")

    result = [0j] * len(matrix)

    for row in range(len(matrix)):
        result[row] = sum(
            matrix[row][column] * vector[column]
            for column in range(len(vector))
        )

    return result


def inner_product(
    bra: Sequence[complex],
    ket: Sequence[complex],
) -> complex:
    """Return <bra|ket> using complex conjugation."""
    if len(bra) != len(ket):
        raise ValueError("states have different dimensions")
    return sum(
        complex(amplitude).conjugate() * value
        for amplitude, value in zip(bra, ket)
    )


def expectation_matrix(
    state: Sequence[complex],
    operator: Sequence[Sequence[complex]],
) -> complex:
    """Return <psi|A|psi>."""
    operated_state = matrix_vector_multiply(operator, state)
    return inner_product(state, operated_state)


# ---------------------------------------------------------------------------
# Finite-dimensional Hamiltonian from operators
# ---------------------------------------------------------------------------

def hamiltonian_from_xp(
    dimension: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> list[list[complex]]:
    """
    Construct

        H = p²/(2m) + 1/2 m omega² x²

    from finite matrices.

    In a truncated basis, x and p are approximate operators and can exhibit
    boundary artifacts near the highest basis state. The exact number-basis
    Hamiltonian is diagonal, so the comparison is an instructive lesson
    about finite-dimensional truncation.
    """
    x = position_matrix(dimension, hbar, mass, omega)
    p = momentum_matrix(dimension, hbar, mass, omega)

    p_squared = matrix_multiply(p, p)
    x_squared = matrix_multiply(x, x)

    kinetic = matrix_scale(p_squared, 1.0 / (2.0 * mass))
    potential = matrix_scale(x_squared, 0.5 * mass * omega**2)

    return matrix_add(kinetic, potential)


# ---------------------------------------------------------------------------
# Coherent states
# ---------------------------------------------------------------------------

def coherent_state(
    alpha: complex,
    dimension: int,
) -> list[complex]:
    """
    Construct a truncated coherent state.

        |alpha> =
            exp(-|alpha|²/2)
            sum_n alpha^n / sqrt(n!) |n>

    The finite vector is normalized after truncation. A sufficiently large
    dimension is needed when |alpha|² is large because the photon/phonon
    number distribution is Poissonian with mean |alpha|².
    """
    if dimension <= 0:
        raise ValueError("dimension must be positive")

    coefficients = []
    common_factor = math.exp(-0.5 * abs(alpha) ** 2)

    for n in range(dimension):
        coefficient = (
            common_factor
            * (alpha**n)
            / math.sqrt(factorial(n))
        )
        coefficients.append(coefficient)

    return normalize_state(coefficients)


def coherent_number_probability(
    alpha: complex,
    n: int,
) -> float:
    """
    Exact Poisson number distribution for a coherent state:

        P(n) = exp(-|alpha|²) |alpha|^(2n) / n!
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    mean = abs(alpha) ** 2
    return math.exp(-mean) * mean**n / factorial(n)


def coherent_mean_number(alpha: complex) -> float:
    return abs(alpha) ** 2


def coherent_position_mean(
    alpha: complex,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    <x> = sqrt(2 hbar/(m omega)) Re(alpha)
    """
    return math.sqrt(2.0 * hbar / (mass * omega)) * alpha.real


def coherent_momentum_mean(
    alpha: complex,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    <p> = sqrt(2 m hbar omega) Im(alpha)
    """
    return math.sqrt(2.0 * mass * hbar * omega) * alpha.imag


def coherent_position_uncertainty(
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """Coherent states have the ground-state position uncertainty."""
    return math.sqrt(hbar / (2.0 * mass * omega))


def coherent_momentum_uncertainty(
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """Coherent states have the ground-state momentum uncertainty."""
    return math.sqrt(mass * hbar * omega / 2.0)


# ---------------------------------------------------------------------------
# Thermal harmonic oscillator
# ---------------------------------------------------------------------------

def thermal_partition_function(
    temperature: float,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> float:
    """
    Canonical partition function:

        Z = exp(-beta hbar omega / 2) / (1 - exp(-beta hbar omega))

    where beta = 1/(k_B T).

    We use k_B = 1 in these dimensionless calculations.
    """
    if temperature <= 0:
        raise ValueError("temperature must be positive")

    beta = 1.0 / temperature
    x = beta * hbar * omega

    # expm1(-x) gives exp(-x)-1 accurately when x is small.
    denominator = -math.expm1(-x)

    return math.exp(-0.5 * x) / denominator


def thermal_mean_energy(
    temperature: float,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> float:
    """
    Mean energy:

        <E> = hbar omega [1/2 + 1/(exp(beta hbar omega)-1)]

    The second term is the thermal excitation energy.
    """
    if temperature <= 0:
        raise ValueError("temperature must be positive")

    x = hbar * omega / temperature

    if x > 700:
        occupation = 0.0
    else:
        occupation = 1.0 / math.expm1(x)

    return hbar * omega * (0.5 + occupation)


def thermal_mean_occupation(
    temperature: float,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> float:
    """Bose-Einstein occupation number for one harmonic mode."""
    if temperature <= 0:
        raise ValueError("temperature must be positive")

    x = hbar * omega / temperature

    if x > 700:
        return 0.0

    return 1.0 / math.expm1(x)


def thermal_probability(
    n: int,
    temperature: float,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> float:
    """
    Canonical probability:

        P_n = (1 - q) q^n

    with q = exp(-beta hbar omega).
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if temperature <= 0:
        raise ValueError("temperature must be positive")

    q = math.exp(-hbar * omega / temperature)
    return (1.0 - q) * q**n


# ---------------------------------------------------------------------------
# Numerical time evolution in the number basis
# ---------------------------------------------------------------------------

def evolve_number_state(
    state: Sequence[complex],
    time: float,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> list[complex]:
    """
    Exact time evolution for a state expressed in number states.

        c_n(t) = c_n(0) exp(-i E_n t/hbar)

    This works because the number states diagonalize the Hamiltonian.
    """
    evolved = []

    for n, coefficient in enumerate(state):
        phase = cmath.exp(-1j * energy_level(n, hbar, omega) * time / hbar)
        evolved.append(coefficient * phase)

    return evolved


def coherent_state_at_time(
    alpha: complex,
    time: float,
    dimension: int,
    omega: float = OMEGA,
) -> list[complex]:
    """
    For a harmonic oscillator, a coherent state remains coherent and its
    complex amplitude rotates approximately as:

        alpha(t) = alpha exp(-i omega t)

    The finite-dimensional construction is used to illustrate this.
    """
    rotated_alpha = alpha * cmath.exp(-1j * omega * time)
    return coherent_state(rotated_alpha, dimension)


# ---------------------------------------------------------------------------
# Perturbation: anharmonic quartic correction
# ---------------------------------------------------------------------------

def quartic_first_order_energy_shift(
    n: int,
    lambda_strength: float,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    First-order perturbation correction for

        H' = lambda x^4.

    The exact number-state matrix element is:

        <n|x^4|n>
          = 3 [hbar/(2m omega)]² (2n² + 2n + 1).

    Therefore:

        Delta E_n^(1)
          = lambda * 3 [hbar/(2m omega)]²
            (2n² + 2n + 1)

    This demonstrates how the exactly solvable harmonic oscillator is used
    as the reference system for more complicated potentials.
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    scale = hbar / (2.0 * mass * omega)
    return lambda_strength * 3.0 * scale**2 * (2 * n * n + 2 * n + 1)


def perturbed_energy_first_order(
    n: int,
    lambda_strength: float,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """Unperturbed energy plus first-order quartic correction."""
    return energy_level(n, hbar, omega) + quartic_first_order_energy_shift(
        n,
        lambda_strength,
        hbar,
        mass,
        omega,
    )


# ---------------------------------------------------------------------------
# WKB comparison
# ---------------------------------------------------------------------------

def classical_turning_point(
    n: int,
    hbar: float = HBAR,
    mass: float = MASS,
    omega: float = OMEGA,
) -> float:
    """
    Classical turning point for energy E_n:

        E_n = 1/2 m omega² x_turn²

    giving:

        x_turn = sqrt(2 E_n / (m omega²))
    """
    energy = energy_level(n, hbar, omega)
    return math.sqrt(2.0 * energy / (mass * omega**2))


def wkb_energy(
    n: int,
    hbar: float = HBAR,
    omega: float = OMEGA,
) -> float:
    """
    Leading-order WKB quantization reproduces the harmonic oscillator
    spectrum exactly:

        E_n = hbar omega (n + 1/2)

    This is a useful example where the semiclassical quantization rule
    agrees with the exact answer because the action integral is quadratic.
    """
    return hbar * omega * (n + 0.5)


# ---------------------------------------------------------------------------
# Measurement simulation
# ---------------------------------------------------------------------------

def sample_number_measurement(
    state: Sequence[complex],
    samples: int = 10000,
    seed: int = 42,
) -> list[int]:
    """
    Simulate projective measurements in the number basis.

    Probability of outcome n is |c_n|².

    The random number generator is seeded so the educational output is
    reproducible.
    """
    if samples <= 0:
        raise ValueError("samples must be positive")

    probabilities = [abs(amplitude) ** 2 for amplitude in state]
    total = sum(probabilities)

    if total <= 0:
        raise ValueError("state has zero probability mass")

    probabilities = [p / total for p in probabilities]

    cumulative = []
    running = 0.0
    for probability in probabilities:
        running += probability
        cumulative.append(running)

    rng = random.Random(seed)
    outcomes = []

    for _ in range(samples):
        target = rng.random()

        for index, boundary in enumerate(cumulative):
            if target < boundary:
                outcomes.append(index)
                break

    return outcomes


def empirical_distribution(outcomes: Iterable[int]) -> dict[int, float]:
    """Convert sampled outcomes into empirical frequencies."""
    counts: dict[int, int] = {}

    total = 0
    for outcome in outcomes:
        counts[outcome] = counts.get(outcome, 0) + 1
        total += 1

    if total == 0:
        return {}

    return {key: value / total for key, value in sorted(counts.items())}


# ---------------------------------------------------------------------------
# Demonstration helpers
# ---------------------------------------------------------------------------

def print_separator(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_state(state: Sequence[complex], threshold: float = 1e-10) -> None:
    """Print non-negligible number-state coefficients."""
    for n, amplitude in enumerate(state):
        if abs(amplitude) > threshold:
            print(
                f"|{n}>: coefficient = "
                f"{amplitude.real:+.6f}{amplitude.imag:+.6f}i, "
                f"probability = {abs(amplitude) ** 2:.6f}"
            )


# ---------------------------------------------------------------------------
# Fundamental demonstrations
# ---------------------------------------------------------------------------

def demonstrate_classical_oscillator() -> None:
    print_separator("1. Classical harmonic oscillator")

    oscillator = ClassicalOscillator(
        mass=1.0,
        omega=2.0,
        amplitude=3.0,
        phase=0.0,
    )

    expected_energy = oscillator.total_energy_from_amplitude()

    print("The classical equation is m*x'' + m*omega^2*x = 0.")
    print(f"Amplitude: {oscillator.amplitude}")
    print(f"Angular frequency: {oscillator.omega}")
    print(f"Classical total energy: {expected_energy:.6f}")

    for time in [0.0, 0.25, 0.50, 0.75]:
        print(
            f"t={time:4.2f}  "
            f"x={oscillator.position(time):+8.4f}  "
            f"p={oscillator.momentum(time):+8.4f}  "
            f"E={oscillator.energy(time):.6f}"
        )

    print(
        "Classically, energy can take a continuous range of values. "
        "The quantum oscillator instead has discrete stationary energies."
    )


def demonstrate_energy_quantization() -> None:
    print_separator("2. Quantized energy spectrum")

    print("Using hbar = m = omega = 1:")
    for n, energy in enumerate(energy_levels(8)):
        print(f"n={n:2d}  E_n={energy:.6f}")

    print("\nEvery adjacent level has the same spacing:")
    for n in range(5):
        print(f"E_{n+1} - E_{n} = {energy_gap(n):.6f}")

    print(
        "\nThe nonzero ground-state energy E_0 = hbar*omega/2 is the "
        "zero-point energy. It remains even when n = 0."
    )


def demonstrate_wavefunctions() -> None:
    print_separator("3. Hermite polynomials and stationary wavefunctions")

    print("First few physicists' Hermite polynomials:")
    for n in range(5):
        coefficients = hermite_coefficients(n)
        formatted = []
        for power, coefficient in enumerate(coefficients):
            if abs(coefficient) < 1e-12:
                continue
            formatted.append(f"{coefficient:+g}*x^{power}")
        expression = " ".join(formatted).replace("+", "+ ")
        print(f"H_{n}(x) = {expression.strip()}")

    print("\nDimensionless wavefunction values:")
    sample_positions = [-2.0, -1.0, 0.0, 1.0, 2.0]

    for n in range(4):
        values = [
            dimensionless_wavefunction(n, x)
            for x in sample_positions
        ]
        print(f"n={n}: " + " ".join(f"{value:+.5f}" for value in values))

    print("\nNode structure:")
    for n in range(5):
        print(
            f"n={n}: expected number of finite nodes = {n}, "
            f"parity = {'even' if n % 2 == 0 else 'odd'}"
        )


def demonstrate_normalization_and_orthogonality() -> None:
    print_separator("4. Normalization and orthogonality")

    domain = (-8.0, 8.0)

    for n in range(4):
        normalization = trapezoidal_integral(
            lambda x, n=n: dimensionless_wavefunction(n, x) ** 2,
            domain[0],
            domain[1],
            intervals=12000,
        )
        print(f"<{n}|{n}> ≈ {normalization:.10f}")

    print("\nSelected orthogonality integrals:")
    for n, m in [(0, 1), (0, 2), (1, 2), (2, 3)]:
        overlap = trapezoidal_integral(
            lambda x, n=n, m=m:
                dimensionless_wavefunction(n, x)
                * dimensionless_wavefunction(m, x),
            domain[0],
            domain[1],
            intervals=12000,
        )
        print(f"<{n}|{m}> ≈ {overlap:+.3e}")


def demonstrate_expectation_values() -> None:
    print_separator("5. Expectation values and uncertainty")

    print("Exact results:")
    print("    <x> = 0")
    print("    <p> = 0")
    print("    <x^2> = hbar/(m*omega) * (n + 1/2)")
    print("    <p^2> = m*hbar*omega * (n + 1/2)")
    print()

    for n in range(5):
        x2 = expectation_x_squared(n)
        p2 = expectation_p_squared(n)
        dx = position_uncertainty(n)
        dp = momentum_uncertainty(n)
        product = uncertainty_product(n)

        print(
            f"n={n}: "
            f"<x²>={x2:.4f}, "
            f"<p²>={p2:.4f}, "
            f"Δx={dx:.4f}, "
            f"Δp={dp:.4f}, "
            f"ΔxΔp={product:.4f}"
        )

    print(
        "\nThe uncertainty relation requires ΔxΔp >= hbar/2. "
        "The ground state saturates the bound."
    )

    assert nearly_equal(uncertainty_product(0), HBAR / 2.0)
    assert uncertainty_product(1) > HBAR / 2.0


def demonstrate_ladder_operators() -> None:
    print_separator("6. Ladder operators")

    print("The defining actions are:")
    print("    a|n>  = sqrt(n)|n-1>")
    print("    a†|n> = sqrt(n+1)|n+1>")
    print()

    for n in range(5):
        print(
            f"|{n}>: "
            f"annihilation coefficient = {ladder_annihilation_coefficient(n):.6f}, "
            f"creation coefficient = {ladder_creation_coefficient(n):.6f}"
        )

    state = basis_state(3, 7)
    lowered = apply_annihilation(state)
    raised = apply_creation(state)

    print("\nApplying a to |3>:")
    print_state(lowered)

    print("\nApplying a† to |3>:")
    print_state(raised)

    print(
        "\nThe annihilation operator lowers the quantum number, while the "
        "creation operator raises it."
    )


def demonstrate_commutation_relation() -> None:
    print_separator("7. Operator algebra and the commutator [a, a†]")

    dimension = 12
    a = annihilation_matrix(dimension)
    adag = creation_matrix(dimension)
    commutator_matrix = commutator(a, adag)

    print("The exact infinite-dimensional relation is [a, a†] = I.")
    print(
        "A finite truncated matrix cannot satisfy this relation exactly at "
        "the highest basis state because raising beyond the cutoff is removed."
    )

    print("\nDiagonal entries of [a, a†] in a 12-state truncation:")
    diagonal = [
        commutator_matrix[index][index].real
        for index in range(dimension)
    ]
    print(diagonal)

    print(
        "\nThe first several entries are 1, while the final boundary entry "
        "shows the finite-dimensional truncation artifact."
    )


def demonstrate_x_and_p_operators() -> None:
    print_separator("8. Position and momentum from ladder operators")

    dimension = 6
    x_operator = position_matrix(dimension)
    p_operator = momentum_matrix(dimension)

    print("Nonzero position matrix elements:")
    for row in range(dimension):
        for column in range(dimension):
            value = x_operator[row][column]
            if abs(value) > 1e-10:
                print(f"<{row}|x|{column}> = {value.real:+.6f}")

    print("\nNonzero momentum matrix elements:")
    for row in range(dimension):
        for column in range(dimension):
            value = p_operator[row][column]
            if abs(value) > 1e-10:
                print(
                    f"<{row}|p|{column}> = "
                    f"{value.real:+.6f}{value.imag:+.6f}i"
                )

    print(
        "\nSelection rule visible from these matrices: x and p connect "
        "number states differing by one quantum number."
    )


def demonstrate_hamiltonian_matrix() -> None:
    print_separator("9. Hamiltonian in the number basis")

    dimension = 8
    hamiltonian = diagonal_hamiltonian(dimension)

    print("The number-state Hamiltonian is diagonal:")
    for n in range(dimension):
        print(f"H[{n},{n}] = {hamiltonian[n][n].real:.6f}")

    print(
        "\nThis diagonal form means the energy eigenvalue problem is already "
        "solved when the number-state basis is used."
    )

    constructed = hamiltonian_from_xp(5)

    print(
        "\nHamiltonian constructed from finite x and p matrices "
        "(diagonal entries):"
    )
    for n in range(5):
        print(f"H_xp[{n},{n}] = {constructed[n][n].real:.6f}")

    print(
        "\nThe first few diagonal values agree with the exact spectrum. "
        "Near a finite cutoff, operator truncation can introduce boundary "
        "effects."
    )


def demonstrate_numerical_moments() -> None:
    print_separator("10. Numerical expectation values")

    for n in range(4):
        numerical_x2 = gaussian_weighted_moment(n, 2)
        exact_x2 = n + 0.5

        numerical_x4 = gaussian_weighted_moment(n, 4)
        exact_x4 = 0.75 * (2 * n * n + 2 * n + 1)

        print(
            f"n={n}: "
            f"<x²> numerical={numerical_x2:.8f}, exact={exact_x2:.8f}; "
            f"<x⁴> numerical={numerical_x4:.8f}, exact={exact_x4:.8f}"
        )


def demonstrate_time_evolution() -> None:
    print_separator("11. Time evolution")

    initial_state = normalize_state(
        [
            1.0 + 0j,
            0.8 + 0.2j,
            0.3 - 0.1j,
            0.15 + 0.05j,
        ]
    )

    print("Initial state:")
    print_state(initial_state)

    print("\nState at t = pi:")
    evolved = evolve_number_state(initial_state, math.pi)
    print_state(evolved)

    print(
        "\nThe magnitude of each number-state coefficient is unchanged "
        "under time evolution. Only its phase changes. Relative phases "
        "matter for superpositions and therefore can affect interference "
        "and position-space probability densities."
    )

    initial_norm = state_norm(initial_state)
    final_norm = state_norm(evolved)

    print(f"\nInitial norm = {initial_norm:.12f}")
    print(f"Final norm   = {final_norm:.12f}")

    assert nearly_equal(initial_norm, final_norm)


def demonstrate_coherent_state() -> None:
    print_separator("12. Coherent states")

    alpha = 1.5 + 0.75j
    dimension = 20

    state = coherent_state(alpha, dimension)

    print(f"alpha = {alpha}")
    print(f"|alpha|² = {abs(alpha) ** 2:.6f}")
    print(f"State norm = {state_norm(state):.12f}")

    print("\nLargest number-state probabilities:")
    probabilities = [
        (n, coherent_number_probability(alpha, n))
        for n in range(12)
    ]

    for n, probability in probabilities:
        print(f"P({n}) = {probability:.8f}")

    print("\nMean values predicted by the coherent-state formulas:")
    print(f"<n> = {coherent_mean_number(alpha):.6f}")
    print(f"<x> = {coherent_position_mean(alpha):.6f}")
    print(f"<p> = {coherent_momentum_mean(alpha):.6f}")
    print(f"Delta x = {coherent_position_uncertainty():.6f}")
    print(f"Delta p = {coherent_momentum_uncertainty():.6f}")
    print(
        f"Delta x Delta p = "
        f"{coherent_position_uncertainty() * coherent_momentum_uncertainty():.6f}"
    )

    print(
        "\nA coherent state has minimum uncertainty and behaves most like a "
        "classical oscillator while remaining fully quantum."
    )


def demonstrate_measurement_statistics() -> None:
    print_separator("13. Measurement statistics")

    alpha = 1.0 + 0.5j
    state = coherent_state(alpha, 15)

    outcomes = sample_number_measurement(state, samples=20000, seed=7)
    observed = empirical_distribution(outcomes)

    print("Theoretical versus simulated number probabilities:")
    for n in range(8):
        theoretical = coherent_number_probability(alpha, n)
        empirical = observed.get(n, 0.0)
        print(
            f"n={n}: theoretical={theoretical:.5f}, "
            f"sampled={empirical:.5f}"
        )

    print(
        "\nIndividual measurements produce definite number outcomes. "
        "The probability distribution emerges across repeated preparations."
    )


def demonstrate_thermal_physics() -> None:
    print_separator("14. Thermal harmonic oscillator")

    print("Units: k_B = hbar = omega = 1")
    print("Temperature      Z            <n>          <E>")

    for temperature in [0.1, 0.25, 0.5, 1.0, 2.0, 5.0]:
        partition = thermal_partition_function(temperature)
        occupation = thermal_mean_occupation(temperature)
        energy = thermal_mean_energy(temperature)

        print(
            f"{temperature:9.2f}  "
            f"{partition:10.6f}  "
            f"{occupation:10.6f}  "
            f"{energy:10.6f}"
        )

    print(
        "\nAt low temperature the oscillator approaches its ground-state "
        "energy. At high temperature, thermal excitation dominates and the "
        "mean energy approaches the classical equipartition behavior."
    )


def demonstrate_perturbation_theory() -> None:
    print_separator("15. Anharmonic perturbation")

    lambda_strength = 0.02

    print(
        "Consider H = H_0 + lambda*x^4 with a small positive lambda."
    )
    print("First-order perturbation theory gives:")

    for n in range(6):
        unperturbed = energy_level(n)
        correction = quartic_first_order_energy_shift(n, lambda_strength)
        corrected = perturbed_energy_first_order(n, lambda_strength)

        print(
            f"n={n}: "
            f"E0={unperturbed:.6f}, "
            f"DeltaE(1)={correction:.6f}, "
            f"E≈{corrected:.6f}"
        )

    print(
        "\nThe correction grows with n because higher oscillator states "
        "sample larger |x| values and therefore feel the quartic term more "
        "strongly."
    )


def demonstrate_wkb() -> None:
    print_separator("16. Semiclassical WKB comparison")

    print("Exact quantum energies versus leading-order WKB energies:")

    for n in range(8):
        exact = energy_level(n)
        semiclassical = wkb_energy(n)
        difference = semiclassical - exact

        print(
            f"n={n}: exact={exact:.6f}, "
            f"WKB={semiclassical:.6f}, "
            f"difference={difference:+.3e}"
        )

    print(
        "\nFor the harmonic oscillator, the WKB quantization condition "
        "reproduces the exact spectrum. This special agreement should not "
        "be generalized to arbitrary potentials."
    )


def demonstrate_edge_cases() -> None:
    print_separator("17. Edge cases and common programming errors")

    print("Ground state:")
    print(f"E_0 = {energy_level(0):.6f}")
    print(f"a|0> has norm = {state_norm(apply_annihilation(basis_state(0, 5))):.6f}")

    print("\nValidation examples:")

    invalid_operations = [
        ("negative quantum number", lambda: energy_level(-1)),
        ("zero mass", lambda: oscillator_length(mass=0.0)),
        ("negative temperature", lambda: thermal_mean_energy(-1.0)),
        ("normalizing zero state", lambda: normalize_state([0j, 0j])),
        ("invalid Hermite order", lambda: hermite_physicists(-2, 1.0)),
    ]

    for description, operation in invalid_operations:
        try:
            operation()
        except (TypeError, ValueError) as error:
            print(f"{description}: correctly rejected -> {error}")

    print(
        "\nImportant edge cases include the ground state, finite basis "
        "cutoffs, numerical integration limits, extremely low temperature, "
        "large quantum numbers, and invalid physical parameters."
    )


def demonstrate_parameter_scaling() -> None:
    print_separator("18. Physical parameter scaling")

    hbar = 1.054571817e-34
    mass = 9.1093837e-31
    omega = 2.0 * math.pi * 1.0e12

    length = oscillator_length(hbar, mass, omega)
    energy_ground = energy_level(0, hbar, omega)

    print("Example parameters resembling a microscopic oscillator:")
    print(f"hbar = {hbar:.6e} J*s")
    print(f"mass = {mass:.6e} kg")
    print(f"omega = {omega:.6e} rad/s")
    print(f"oscillator length = {length:.6e} m")
    print(f"ground-state energy = {energy_ground:.6e} J")

    print(
        "\nThe dimensionless implementation is not a loss of physics. "
        "It is a change of units that isolates the mathematical structure."
    )


def demonstrate_probability_current() -> None:
    print_separator("19. Probability current for stationary states")

    print(
        "For a real stationary eigenfunction in a one-dimensional oscillator, "
        "the probability current is zero:"
    )
    print(
        "    j(x) = (hbar/m) Im[psi*(x) dpsi/dx] = 0"
    )

    def derivative(function: Callable[[float], float], x: float) -> float:
        step = 1e-5
        return (function(x + step) - function(x - step)) / (2.0 * step)

    for n in range(3):
        x = 0.7
        psi = wavefunction(n, x)
        dpsi = derivative(lambda coordinate: wavefunction(n, coordinate), x)
        current = (HBAR / MASS) * (psi * dpsi).imag
        print(f"n={n}, x={x}: j≈{current:.3e}")


def demonstrate_density_symmetry() -> None:
    print_separator("20. Parity and probability density")

    for n in range(4):
        x = 1.25
        left = probability_density(n, -x)
        right = probability_density(n, x)
        print(
            f"n={n}: |psi(-x)|²={left:.8f}, "
            f"|psi(x)|²={right:.8f}, "
            f"difference={left-right:+.3e}"
        )

    print(
        "\nEvery number-state probability density is even because the "
        "wavefunction has definite parity and the sign disappears after "
        "taking the absolute square."
    )


# ---------------------------------------------------------------------------
# Automated verification
# ---------------------------------------------------------------------------

def run_verification_suite() -> None:
    print_separator("21. Automated mathematical checks")

    # Spectrum
    assert nearly_equal(energy_level(0), 0.5)
    assert nearly_equal(energy_level(4), 4.5)

    # Equal spacing
    gaps = [energy_gap(n) for n in range(5)]
    assert all(nearly_equal(gap, 1.0) for gap in gaps)

    # Wavefunction normalization
    for n in range(4):
        normalization = trapezoidal_integral(
            lambda x, n=n: dimensionless_wavefunction(n, x) ** 2,
            -8.0,
            8.0,
            intervals=10000,
        )
        assert abs(normalization - 1.0) < 2e-5

    # Orthogonality
    overlap = trapezoidal_integral(
        lambda x:
            dimensionless_wavefunction(0, x)
            * dimensionless_wavefunction(1, x),
        -8.0,
        8.0,
        intervals=10000,
    )
    assert abs(overlap) < 2e-5

    # Ladder operators
    state_2 = basis_state(2, 6)
    lowered = apply_annihilation(state_2)
    raised = apply_creation(state_2)

    assert nearly_equal(state_norm(lowered), math.sqrt(2.0))
    assert nearly_equal(state_norm(raised), math.sqrt(3.0))

    # Ground-state uncertainty relation.
    assert nearly_equal(
        uncertainty_product(0),
        HBAR / 2.0,
    )

    # Coherent state normalization.
    coherent = coherent_state(1.2 + 0.4j, 25)
    assert nearly_equal(state_norm(coherent), 1.0)

    # Time evolution preserves norm.
    evolved = evolve_number_state(coherent, 2.7)
    assert nearly_equal(state_norm(evolved), state_norm(coherent))

    # Thermal occupation positivity.
    for temperature in [0.1, 1.0, 10.0]:
        assert thermal_mean_occupation(temperature) >= 0.0

    # WKB agreement.
    for n in range(10):
        assert nearly_equal(wkb_energy(n), energy_level(n))

    print("All automated checks passed.")


# ---------------------------------------------------------------------------
# Educational reference table
# ---------------------------------------------------------------------------

def print_reference_table() -> None:
    print_separator("22. Compact reference table")

    rows = [
        ("Hamiltonian", "H = p²/(2m) + mω²x²/2"),
        ("Energy", "E_n = hbar*ω*(n + 1/2)"),
        ("Ground energy", "E_0 = hbar*ω/2"),
        ("Oscillator length", "sqrt(hbar/(mω))"),
        ("Dimensionless coordinate", "xi = x/sqrt(hbar/(mω))"),
        ("Annihilation", "a|n> = sqrt(n)|n-1>"),
        ("Creation", "a†|n> = sqrt(n+1)|n+1>"),
        ("Number operator", "N = a†a"),
        ("Hamiltonian ladder form", "H = hbar*ω*(N + 1/2)"),
        ("Position", "x = sqrt(hbar/(2mω))*(a+a†)"),
        ("Momentum", "p = -i*sqrt(m hbar ω/2)*(a-a†)"),
        ("Commutator", "[a,a†] = 1"),
        ("Position uncertainty", "Δx = sqrt(hbar/(mω)*(n+1/2))"),
        ("Momentum uncertainty", "Δp = sqrt(m hbar ω*(n+1/2))"),
        ("Ground uncertainty", "ΔxΔp = hbar/2"),
        ("Coherent number mean", "<N> = |alpha|²"),
        ("Thermal occupation", "<N> = 1/(exp(beta hbar ω)-1)"),
        ("Classical limit", "Large n or hbar*ω << thermal/other scales"),
    ]

    for concept, equation in rows:
        print(f"{concept:28s} : {equation}")


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> None:
    print("QUANTUM HARMONIC OSCILLATOR")
    print("Comprehensive computational study")
    print("Dimensionless default units: hbar = m = omega = 1")

    demonstrate_classical_oscillator()
    demonstrate_energy_quantization()
    demonstrate_wavefunctions()
    demonstrate_normalization_and_orthogonality()
    demonstrate_expectation_values()
    demonstrate_ladder_operators()
    demonstrate_commutation_relation()
    demonstrate_x_and_p_operators()
    demonstrate_hamiltonian_matrix()
    demonstrate_numerical_moments()
    demonstrate_time_evolution()
    demonstrate_coherent_state()
    demonstrate_measurement_statistics()
    demonstrate_thermal_physics()
    demonstrate_perturbation_theory()
    demonstrate_wkb()
    demonstrate_edge_cases()
    demonstrate_parameter_scaling()
    demonstrate_probability_current()
    demonstrate_density_symmetry()
    run_verification_suite()
    print_reference_table()

    print_separator("End of computational study")
    print(
        "The harmonic oscillator connects differential equations, Hilbert "
        "spaces, operator algebra, quantization, probability, measurement, "
        "semiclassical physics, statistical mechanics, and perturbation theory."
    )


if __name__ == "__main__":
    main()
