"""
Time Evolution and Schrödinger Equation Concepts
=================================================

A self-contained computational study of non-relativistic quantum time evolution.

The script develops the subject from the time-dependent Schrödinger equation
through numerical propagation, stationary states, wave-packet motion,
probability conservation, expectation values, uncertainty, tunneling,
the infinite square well, harmonic oscillator, Fourier representations,
and a split-operator propagation method.

The numerical methods use only Python's standard library. Complex arithmetic,
arrays, linear algebra, and finite-difference operations are implemented
explicitly so that the underlying mathematics remains visible.

Units:
    Throughout most examples, dimensionless units with ħ = m = 1 are used.
    For a one-dimensional particle this gives

        i ħ ∂ψ/∂t = [-(ħ²/2m) ∂²/∂x² + V(x)] ψ

    and, when ħ = m = 1,

        i ∂ψ/∂t = [-1/2 ∂²/∂x² + V(x)] ψ.

This file is intended to be executed directly:

    python schrodinger_time_evolution.py
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Fundamental constants and utility functions
# ---------------------------------------------------------------------------

HBAR = 1.0
MASS = 1.0
EPSILON = 1e-12


def print_title(title: str) -> None:
    """Print a compact section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def linspace(start: float, stop: float, count: int) -> List[float]:
    """Equivalent of numpy.linspace for educational purposes."""
    if count < 2:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def max_abs(values: Sequence[complex]) -> float:
    return max((abs(value) for value in values), default=0.0)


def complex_vector_norm_squared(values: Sequence[complex]) -> float:
    return sum(abs(value) ** 2 for value in values)


# ---------------------------------------------------------------------------
# Numerical integration
# ---------------------------------------------------------------------------

def trapezoidal_integral(values: Sequence[float], dx: float) -> float:
    """Numerical integral using the trapezoidal rule."""
    if len(values) < 2:
        return 0.0
    return dx * (
        0.5 * values[0]
        + sum(values[1:-1])
        + 0.5 * values[-1]
    )


def complex_trapezoidal_integral(
    values: Sequence[complex], dx: float
) -> complex:
    """Complex-valued trapezoidal integration."""
    if len(values) < 2:
        return 0.0j
    return dx * (
        0.5 * values[0]
        + sum(values[1:-1])
        + 0.5 * values[-1]
    )


# ---------------------------------------------------------------------------
# Wave-function construction
# ---------------------------------------------------------------------------

def gaussian_wave_packet(
    x: Sequence[float],
    center: float,
    width: float,
    momentum: float,
    hbar: float = HBAR,
) -> List[complex]:
    """
    Construct a Gaussian wave packet.

    ψ(x,0) = A exp[-(x-x0)^2/(4σ^2)] exp(i k0 x)

    where k0 = p0 / ħ.

    The Gaussian envelope controls spatial localization while the phase
    factor determines the mean momentum.
    """
    k0 = momentum / hbar
    packet = [
        math.exp(-((position - center) ** 2) / (4.0 * width ** 2))
        * cmath.exp(1j * k0 * position)
        for position in x
    ]
    return normalize_wavefunction(packet, x[1] - x[0])


def standing_wave_infinite_well(
    x: Sequence[float],
    box_length: float,
    quantum_number: int,
) -> List[complex]:
    """
    nth stationary eigenfunction of an infinite square well on [0, L]:

        ψ_n(x) = sqrt(2/L) sin(nπx/L)
    """
    n = quantum_number
    amplitude = math.sqrt(2.0 / box_length)
    return [
        complex(
            amplitude * math.sin(n * math.pi * position / box_length),
            0.0,
        )
        for position in x
    ]


def normalize_wavefunction(
    wavefunction: Sequence[complex],
    dx: float,
) -> List[complex]:
    """Normalize ψ so that integral |ψ|² dx = 1."""
    probability_density = [abs(value) ** 2 for value in wavefunction]
    norm_squared = trapezoidal_integral(probability_density, dx)

    if norm_squared <= EPSILON:
        raise ValueError("Cannot normalize a wavefunction with zero norm.")

    normalization_factor = math.sqrt(norm_squared)
    return [value / normalization_factor for value in wavefunction]


# ---------------------------------------------------------------------------
# Probability and expectation values
# ---------------------------------------------------------------------------

def probability_density(
    wavefunction: Sequence[complex],
) -> List[float]:
    """Return |ψ(x)|²."""
    return [abs(value) ** 2 for value in wavefunction]


def total_probability(
    wavefunction: Sequence[complex],
    dx: float,
) -> float:
    """Compute ∫ |ψ|² dx."""
    return trapezoidal_integral(probability_density(wavefunction), dx)


def expectation_position(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    dx: float,
) -> float:
    density = probability_density(wavefunction)
    return trapezoidal_integral(
        [position * probability for position, probability in zip(x, density)],
        dx,
    )


def expectation_position_squared(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    dx: float,
) -> float:
    density = probability_density(wavefunction)
    return trapezoidal_integral(
        [
            position * position * probability
            for position, probability in zip(x, density)
        ],
        dx,
    )


def expectation_momentum(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    dx: float,
    hbar: float = HBAR,
) -> float:
    """
    Compute <p> using

        p̂ = -i ħ d/dx

    with central finite differences in the interior.
    """
    if len(x) < 3:
        raise ValueError("At least three spatial points are required.")

    derivative = first_derivative(wavefunction, dx)
    integrand = [
        wavefunction[index].conjugate()
        * (-1j * hbar * derivative[index])
        for index in range(len(wavefunction))
    ]

    return complex_trapezoidal_integral(integrand, dx).real


def expectation_potential_energy(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    potential: Callable[[float], float],
    dx: float,
) -> float:
    density = probability_density(wavefunction)
    return trapezoidal_integral(
        [
            potential(position) * probability
            for position, probability in zip(x, density)
        ],
        dx,
    )


def uncertainty_position(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    dx: float,
) -> float:
    mean_x = expectation_position(x, wavefunction, dx)
    mean_x2 = expectation_position_squared(x, wavefunction, dx)
    variance = max(0.0, mean_x2 - mean_x ** 2)
    return math.sqrt(variance)


# ---------------------------------------------------------------------------
# Differential operators
# ---------------------------------------------------------------------------

def first_derivative(
    values: Sequence[complex],
    dx: float,
) -> List[complex]:
    """
    Second-order finite-difference first derivative.

    Interior:
        f'(x) ≈ [f(x+dx)-f(x-dx)]/(2dx)

    Boundary values use one-sided differences.
    """
    count = len(values)
    if count < 3:
        raise ValueError("At least three points are required.")

    derivative = [0j] * count
    derivative[0] = (values[1] - values[0]) / dx
    derivative[-1] = (values[-1] - values[-2]) / dx

    for index in range(1, count - 1):
        derivative[index] = (
            values[index + 1] - values[index - 1]
        ) / (2.0 * dx)

    return derivative


def second_derivative(
    values: Sequence[complex],
    dx: float,
) -> List[complex]:
    """
    Second-order finite-difference approximation to d²ψ/dx².

        ψ''(x) ≈ [ψ(x+dx)-2ψ(x)+ψ(x-dx)]/dx²
    """
    count = len(values)
    if count < 3:
        raise ValueError("At least three points are required.")

    derivative = [0j] * count

    derivative[0] = (
        values[2] - 2.0 * values[1] + values[0]
    ) / (dx * dx)

    derivative[-1] = (
        values[-1] - 2.0 * values[-2] + values[-3]
    ) / (dx * dx)

    for index in range(1, count - 1):
        derivative[index] = (
            values[index + 1]
            - 2.0 * values[index]
            + values[index - 1]
        ) / (dx * dx)

    return derivative


# ---------------------------------------------------------------------------
# Potential-energy functions
# ---------------------------------------------------------------------------

def free_particle_potential(_: float) -> float:
    return 0.0


def infinite_well_potential(
    x: float,
    left: float,
    right: float,
) -> float:
    """
    Conceptual infinite-wall potential.

    The numerical domain normally keeps the wavefunction at zero at the
    boundaries rather than storing an actual infinite floating-point value.
    """
    if left < x < right:
        return 0.0
    return math.inf


def harmonic_oscillator_potential(
    x: float,
    angular_frequency: float = 1.0,
    mass: float = MASS,
) -> float:
    return 0.5 * mass * angular_frequency ** 2 * x ** 2


def barrier_potential(
    x: float,
    barrier_start: float,
    barrier_end: float,
    height: float,
) -> float:
    return height if barrier_start <= x <= barrier_end else 0.0


def finite_square_well_potential(
    x: float,
    half_width: float,
    depth: float,
) -> float:
    """
    A finite attractive well:

        V(x) = -depth inside the well
               0 elsewhere
    """
    return -depth if abs(x) <= half_width else 0.0


# ---------------------------------------------------------------------------
# Hamiltonian and energy calculations
# ---------------------------------------------------------------------------

def apply_hamiltonian(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    potential: Callable[[float], float],
    hbar: float = HBAR,
    mass: float = MASS,
) -> List[complex]:
    """
    Apply

        H = -(ħ²/2m) d²/dx² + V(x)

    to ψ.
    """
    dx = x[1] - x[0]
    second = second_derivative(wavefunction, dx)
    result = []

    for position, psi, curvature in zip(x, wavefunction, second):
        kinetic = -(hbar ** 2 / (2.0 * mass)) * curvature
        potential_term = potential(position) * psi
        result.append(kinetic + potential_term)

    return result


def expectation_energy(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    potential: Callable[[float], float],
    hbar: float = HBAR,
    mass: float = MASS,
) -> float:
    """Compute <H> = ∫ ψ* Hψ dx."""
    dx = x[1] - x[0]
    h_psi = apply_hamiltonian(
        x,
        wavefunction,
        potential,
        hbar,
        mass,
    )
    integrand = [
        psi.conjugate() * hpsi
        for psi, hpsi in zip(wavefunction, h_psi)
    ]
    return complex_trapezoidal_integral(integrand, dx).real


# ---------------------------------------------------------------------------
# Time-dependent Schrödinger equation
# ---------------------------------------------------------------------------

def schrodinger_rhs(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    potential: Callable[[float], float],
    hbar: float = HBAR,
    mass: float = MASS,
) -> List[complex]:
    """
    The time-dependent Schrödinger equation is

        i ħ ∂ψ/∂t = Hψ.

    Therefore

        ∂ψ/∂t = -(i/ħ) Hψ.
    """
    h_psi = apply_hamiltonian(
        x,
        wavefunction,
        potential,
        hbar,
        mass,
    )
    return [
        (-1j / hbar) * value
        for value in h_psi
    ]


def add_scaled(
    vector: Sequence[complex],
    derivative: Sequence[complex],
    scale: float,
) -> List[complex]:
    return [
        value + scale * slope
        for value, slope in zip(vector, derivative)
    ]


def rk4_step(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    dt: float,
    potential: Callable[[float], float],
    hbar: float = HBAR,
    mass: float = MASS,
) -> List[complex]:
    """
    Classical fourth-order Runge-Kutta integration applied to the complex
    Schrödinger equation.

    RK4 is useful pedagogically, but a generic RK method is not exactly
    unitary. A sufficiently small time step is therefore important.
    """
    k1 = schrodinger_rhs(x, wavefunction, potential, hbar, mass)

    state2 = add_scaled(wavefunction, k1, dt / 2.0)
    k2 = schrodinger_rhs(x, state2, potential, hbar, mass)

    state3 = add_scaled(wavefunction, k2, dt / 2.0)
    k3 = schrodinger_rhs(x, state3, potential, hbar, mass)

    state4 = add_scaled(wavefunction, k3, dt)
    k4 = schrodinger_rhs(x, state4, potential, hbar, mass)

    return [
        psi + (dt / 6.0) * (
            slope1 + 2.0 * slope2 + 2.0 * slope3 + slope4
        )
        for psi, slope1, slope2, slope3, slope4 in zip(
            wavefunction,
            k1,
            k2,
            k3,
            k4,
        )
    ]


def evolve_rk4(
    x: Sequence[float],
    initial_wavefunction: Sequence[complex],
    potential: Callable[[float], float],
    dt: float,
    steps: int,
    record_every: int = 1,
    renormalize: bool = False,
) -> List[Tuple[int, List[complex]]]:
    """
    Evolve a state using RK4.

    Boundary values are reset to zero after each step for a finite numerical
    box. This models hard-wall boundaries and prevents numerical leakage.
    """
    wavefunction = list(initial_wavefunction)
    dx = x[1] - x[0]
    history = [(0, list(wavefunction))]

    for step in range(1, steps + 1):
        wavefunction = rk4_step(
            x,
            wavefunction,
            dt,
            potential,
        )

        # Hard-wall boundary condition:
        wavefunction[0] = 0j
        wavefunction[-1] = 0j

        if renormalize:
            wavefunction = normalize_wavefunction(wavefunction, dx)

        if step % record_every == 0:
            history.append((step, list(wavefunction)))

    return history


# ---------------------------------------------------------------------------
# Exact stationary-state evolution
# ---------------------------------------------------------------------------

def infinite_well_energy(
    quantum_number: int,
    box_length: float,
    hbar: float = HBAR,
    mass: float = MASS,
) -> float:
    """
    Infinite-well energy:

        E_n = n²π²ħ² / (2mL²)
    """
    n = quantum_number
    return (
        n ** 2
        * math.pi ** 2
        * hbar ** 2
        / (2.0 * mass * box_length ** 2)
    )


def stationary_state_evolve(
    initial_state: Sequence[complex],
    energy: float,
    time: float,
    hbar: float = HBAR,
) -> List[complex]:
    """
    If Hψ = Eψ, then

        ψ(x,t) = ψ(x,0) exp(-iEt/ħ).

    This changes the global phase but leaves |ψ|² unchanged.
    """
    phase = cmath.exp(-1j * energy * time / hbar)
    return [value * phase for value in initial_state]


# ---------------------------------------------------------------------------
# Superposition of stationary states
# ---------------------------------------------------------------------------

def normalized_superposition(
    states: Sequence[Sequence[complex]],
    coefficients: Sequence[complex],
    dx: float,
) -> List[complex]:
    """
    Construct Σ c_n ψ_n and normalize it.

    If the supplied states are orthonormal and Σ|c_n|² = 1, normalization
    is already satisfied. Numerical discretization may introduce small
    deviations, so explicit normalization is useful.
    """
    if len(states) != len(coefficients):
        raise ValueError("States and coefficients must have equal lengths.")

    if not states:
        raise ValueError("At least one state is required.")

    count = len(states[0])
    result = [0j] * count

    for state, coefficient in zip(states, coefficients):
        if len(state) != count:
            raise ValueError("All states must have equal lengths.")
        for index in range(count):
            result[index] += coefficient * state[index]

    return normalize_wavefunction(result, dx)


# ---------------------------------------------------------------------------
# Fourier transform implementation
# ---------------------------------------------------------------------------

def discrete_fourier_transform(
    values: Sequence[complex],
) -> List[complex]:
    """
    Direct O(N²) discrete Fourier transform.

    This is intentionally not an FFT. The purpose is to make the
    position-momentum representation relationship explicit.

    Convention:
        F_k = Σ_n f_n exp(-2π i kn/N)
    """
    count = len(values)
    result = []

    for k in range(count):
        total = 0j
        for n, value in enumerate(values):
            angle = -2.0 * math.pi * k * n / count
            total += value * cmath.exp(1j * angle)
        result.append(total)

    return result


def discrete_inverse_fourier_transform(
    values: Sequence[complex],
) -> List[complex]:
    """Inverse of the direct discrete Fourier transform."""
    count = len(values)
    result = []

    for n in range(count):
        total = 0j
        for k, value in enumerate(values):
            angle = 2.0 * math.pi * k * n / count
            total += value * cmath.exp(1j * angle)
        result.append(total / count)

    return result


# ---------------------------------------------------------------------------
# Split-operator propagation
# ---------------------------------------------------------------------------

def fft_recursive(values: Sequence[complex]) -> List[complex]:
    """
    Recursive radix-2 FFT.

    This implementation assumes a power-of-two length. It demonstrates why
    FFT-based propagation can be much faster than an O(N²) transform.
    """
    count = len(values)

    if count == 1:
        return [values[0]]

    if count % 2 != 0:
        raise ValueError("FFT input length must be a power of two.")

    even = fft_recursive(values[0::2])
    odd = fft_recursive(values[1::2])

    result = [0j] * count

    for k in range(count // 2):
        angle = -2.0 * math.pi * k / count
        twiddle = cmath.exp(1j * angle) * odd[k]

        result[k] = even[k] + twiddle
        result[k + count // 2] = even[k] - twiddle

    return result


def ifft_recursive(values: Sequence[complex]) -> List[complex]:
    """Inverse FFT using conjugation."""
    conjugated = [value.conjugate() for value in values]
    transformed = fft_recursive(conjugated)
    count = len(values)
    return [value.conjugate() / count for value in transformed]


def split_operator_step(
    wavefunction: Sequence[complex],
    x: Sequence[float],
    dt: float,
    potential: Callable[[float], float],
    hbar: float = HBAR,
    mass: float = MASS,
) -> List[complex]:
    """
    Second-order split-operator approximation.

    H = T + V

    The exact propagator is

        U(dt) = exp(-iHdt/ħ).

    Since T and V generally do not commute,

        [T,V] != 0,

    we cannot simply separate the exponent exactly.

    Strang splitting gives

        U(dt) ≈ exp(-iVdt/(2ħ))
                exp(-iTdt/ħ)
                exp(-iVdt/(2ħ))

    with local error of higher order than a first-order splitting.

    In momentum space, T is diagonal:

        T(p) = p²/(2m).

    The implementation uses the FFT to move between x and momentum-like
    grid representations.
    """
    count = len(wavefunction)
    if count & (count - 1):
        raise ValueError("Split-operator grid size must be a power of two.")

    dx = x[1] - x[0]

    # First half-step under the potential.
    half_potential = [
        cmath.exp(
            -1j * potential(position) * dt / (2.0 * hbar)
        )
        for position in x
    ]

    state = [
        psi * phase
        for psi, phase in zip(wavefunction, half_potential)
    ]

    # FFT from position representation to momentum-grid representation.
    momentum_state = fft_recursive(state)

    # Discrete momentum spacing. The shifted ordering is not necessary
    # for propagation because p² is periodic under the grid indexing.
    length = count * dx
    momentum_spacing = 2.0 * math.pi * hbar / length

    kinetic_phase = []
    for index in range(count):
        shifted_index = index if index < count // 2 else index - count
        momentum = shifted_index * momentum_spacing
        kinetic_energy = momentum ** 2 / (2.0 * mass)

        kinetic_phase.append(
            cmath.exp(-1j * kinetic_energy * dt / hbar)
        )

    momentum_state = [
        value * phase
        for value, phase in zip(momentum_state, kinetic_phase)
    ]

    # Return to position representation.
    state = ifft_recursive(momentum_state)

    # Second half-step under V.
    state = [
        psi * phase
        for psi, phase in zip(state, half_potential)
    ]

    # Remove tiny accumulated numerical drift from normalization.
    return normalize_wavefunction(state, dx)


def evolve_split_operator(
    x: Sequence[float],
    initial_wavefunction: Sequence[complex],
    potential: Callable[[float], float],
    dt: float,
    steps: int,
    record_every: int = 1,
) -> List[Tuple[int, List[complex]]]:
    """Propagate a state with the FFT split-operator method."""
    wavefunction = normalize_wavefunction(
        initial_wavefunction,
        x[1] - x[0],
    )
    history = [(0, list(wavefunction))]

    for step in range(1, steps + 1):
        wavefunction = split_operator_step(
            wavefunction,
            x,
            dt,
            potential,
        )

        if step % record_every == 0:
            history.append((step, list(wavefunction)))

    return history


# ---------------------------------------------------------------------------
# Measurement simulation
# ---------------------------------------------------------------------------

def sample_position(
    x: Sequence[float],
    wavefunction: Sequence[complex],
    rng: random.Random,
) -> float:
    """
    Draw one approximate position measurement from |ψ|².

    A discrete grid probability distribution is used. This is a computational
    sampling model rather than an exact continuous random-variable sampler.
    """
    dx = x[1] - x[0]
    weights = [abs(value) ** 2 * dx for value in wavefunction]
    total = sum(weights)

    if total <= EPSILON:
        raise ValueError("Cannot sample from a zero-probability state.")

    target = rng.random() * total
    cumulative = 0.0

    for position, weight in zip(x, weights):
        cumulative += weight
        if cumulative >= target:
            return position

    return x[-1]


# ---------------------------------------------------------------------------
# Numerical demonstrations
# ---------------------------------------------------------------------------

def demonstration_normalization() -> None:
    print_title("1. Normalization and probability density")

    x = linspace(-12.0, 12.0, 801)
    dx = x[1] - x[0]

    wavefunction = gaussian_wave_packet(
        x,
        center=-2.0,
        width=1.2,
        momentum=3.0,
    )

    probability = total_probability(wavefunction, dx)

    print(f"Grid points: {len(x)}")
    print(f"Grid spacing dx: {dx:.6f}")
    print(f"Total probability: {probability:.12f}")
    print(
        "Interpretation: a properly normalized quantum state satisfies "
        "integral |psi|^2 dx = 1."
    )


def demonstration_stationary_state() -> None:
    print_title("2. Stationary state and global phase evolution")

    box_length = 10.0
    x = linspace(0.0, box_length, 401)
    dx = x[1] - x[0]

    n = 3
    state = standing_wave_infinite_well(
        x,
        box_length,
        n,
    )
    energy = infinite_well_energy(n, box_length)

    evolved = stationary_state_evolve(
        state,
        energy,
        time=1.7,
    )

    initial_probability = probability_density(state)
    evolved_probability = probability_density(evolved)

    max_probability_difference = max(
        abs(a - b)
        for a, b in zip(initial_probability, evolved_probability)
    )

    print(f"Quantum number n: {n}")
    print(f"Energy E_n: {energy:.8f}")
    print(f"Initial normalization: {total_probability(state, dx):.12f}")
    print(f"Evolved normalization: {total_probability(evolved, dx):.12f}")
    print(
        f"Maximum change in |psi|^2: "
        f"{max_probability_difference:.3e}"
    )
    print(
        "A single energy eigenstate acquires only a phase factor, so its "
        "probability density remains stationary."
    )


def demonstration_superposition() -> None:
    print_title("3. Superposition of energy eigenstates")

    box_length = 10.0
    x = linspace(0.0, box_length, 401)
    dx = x[1] - x[0]

    state_1 = standing_wave_infinite_well(x, box_length, 1)
    state_2 = standing_wave_infinite_well(x, box_length, 2)

    initial = normalized_superposition(
        [state_1, state_2],
        [1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0)],
        dx,
    )

    energy_1 = infinite_well_energy(1, box_length)
    energy_2 = infinite_well_energy(2, box_length)

    time = 15.0
    evolved = [
        (
            state_1[index]
            * math.exp(-1j * energy_1 * time)
            + state_2[index]
            * math.exp(-1j * energy_2 * time)
        ) / math.sqrt(2.0)
        for index in range(len(x))
    ]
    evolved = normalize_wavefunction(evolved, dx)

    initial_mean_x = expectation_position(x, initial, dx)
    evolved_mean_x = expectation_position(x, evolved, dx)

    initial_peak = max(probability_density(initial))
    evolved_peak = max(probability_density(evolved))

    print(f"E1 = {energy_1:.8f}")
    print(f"E2 = {energy_2:.8f}")
    print(f"<x>(0) = {initial_mean_x:.8f}")
    print(f"<x>({time}) = {evolved_mean_x:.8f}")
    print(f"Maximum density at t=0: {initial_peak:.8f}")
    print(f"Maximum density at t={time}: {evolved_peak:.8f}")
    print(
        "Unlike a single stationary state, a superposition contains "
        "relative phases that evolve differently because E1 != E2."
    )


def demonstration_uncertainty() -> None:
    print_title("4. Position-momentum uncertainty")

    x = linspace(-12.0, 12.0, 801)
    dx = x[1] - x[0]

    wavefunction = gaussian_wave_packet(
        x,
        center=0.0,
        width=1.0,
        momentum=4.0,
    )

    delta_x = uncertainty_position(x, wavefunction, dx)
    mean_p = expectation_momentum(x, wavefunction, dx)

    print(f"<p> ≈ {mean_p:.8f}")
    print(f"Δx ≈ {delta_x:.8f}")

    # Estimate <p^2> using a second derivative:
    second = second_derivative(wavefunction, dx)
    p2_integrand = [
        psi.conjugate() * (-HBAR ** 2) * curvature
        for psi, curvature in zip(wavefunction, second)
    ]
    mean_p2 = complex_trapezoidal_integral(
        p2_integrand,
        dx,
    ).real

    delta_p = math.sqrt(max(0.0, mean_p2 - mean_p ** 2))
    product = delta_x * delta_p

    print(f"Δp ≈ {delta_p:.8f}")
    print(f"Δx Δp ≈ {product:.8f}")
    print(f"ħ/2 = {HBAR / 2.0:.8f}")
    print(
        "The numerical product should satisfy the uncertainty bound "
        "ΔxΔp >= ħ/2 up to discretization and boundary errors."
    )


def demonstration_rk4_time_evolution() -> None:
    print_title("5. Numerical time evolution with RK4")

    x = linspace(-10.0, 10.0, 401)
    dx = x[1] - x[0]

    initial = gaussian_wave_packet(
        x,
        center=-3.0,
        width=0.8,
        momentum=4.0,
    )

    initial_energy = expectation_energy(
        x,
        initial,
        free_particle_potential,
    )

    history = evolve_rk4(
        x,
        initial,
        free_particle_potential,
        dt=0.0005,
        steps=120,
        record_every=30,
        renormalize=False,
    )

    print(f"Initial energy estimate: {initial_energy:.8f}")

    for step, state in history:
        probability = total_probability(state, dx)
        position = expectation_position(x, state, dx)
        energy = expectation_energy(
            x,
            state,
            free_particle_potential,
        )

        print(
            f"step={step:4d}, "
            f"t={step * 0.0005:.4f}, "
            f"<x>={position:.6f}, "
            f"P={probability:.9f}, "
            f"<H>={energy:.8f}"
        )

    print(
        "RK4 is accurate for sufficiently small dt, but it is not exactly "
        "unitary. Long simulations may therefore accumulate normalization "
        "and energy errors."
    )


def demonstration_harmonic_oscillator() -> None:
    print_title("6. Harmonic oscillator and energy decomposition")

    x = linspace(-8.0, 8.0, 401)
    dx = x[1] - x[0]

    potential = lambda position: harmonic_oscillator_potential(
        position,
        angular_frequency=1.0,
    )

    initial = gaussian_wave_packet(
        x,
        center=0.0,
        width=1.0,
        momentum=2.0,
    )

    energy = expectation_energy(
        x,
        initial,
        potential,
    )
    potential_energy = expectation_potential_energy(
        x,
        initial,
        potential,
        dx,
    )

    kinetic_energy = energy - potential_energy

    print(f"Total energy: {energy:.8f}")
    print(f"Potential contribution: {potential_energy:.8f}")
    print(f"Kinetic contribution: {kinetic_energy:.8f}")
    print(
        "For a harmonic oscillator, the Hamiltonian contains both kinetic "
        "and quadratic potential terms. A displaced or momentum-shifted "
        "Gaussian is a useful approximate wave-packet state."
    )


def demonstration_tunneling() -> None:
    print_title("7. Barrier and tunneling model")

    x = linspace(-12.0, 12.0, 512)
    barrier_start = -0.5
    barrier_end = 0.5
    barrier_height = 8.0

    potential = lambda position: barrier_potential(
        position,
        barrier_start,
        barrier_end,
        barrier_height,
    )

    initial = gaussian_wave_packet(
        x,
        center=-5.0,
        width=0.7,
        momentum=5.0,
    )

    print(f"Barrier height: {barrier_height}")
    print(f"Barrier interval: [{barrier_start}, {barrier_end}]")
    print(
        "A wave packet with energy below the classical barrier can still "
        "develop amplitude on the other side because quantum evolution "
        "permits tunneling."
    )

    # Use a short split-operator evolution to illustrate the setup.
    history = evolve_split_operator(
        x,
        initial,
        potential,
        dt=0.002,
        steps=20,
        record_every=10,
    )

    for step, state in history:
        left_probability = trapezoidal_integral(
            [
                abs(psi) ** 2
                for position, psi in zip(x, state)
                if position < barrier_start
            ],
            x[1] - x[0],
        )
        right_probability = trapezoidal_integral(
            [
                abs(psi) ** 2
                for position, psi in zip(x, state)
                if position > barrier_end
            ],
            x[1] - x[0],
        )

        print(
            f"step={step:3d}, "
            f"left probability estimate={left_probability:.6f}, "
            f"right probability estimate={right_probability:.6f}"
        )


def demonstration_fourier_transform() -> None:
    print_title("8. Position and momentum representations")

    count = 16
    x = linspace(-4.0, 4.0, count)
    wavefunction = gaussian_wave_packet(
        x,
        center=0.0,
        width=0.9,
        momentum=2.0,
    )

    transformed = discrete_fourier_transform(wavefunction)
    reconstructed = discrete_inverse_fourier_transform(transformed)

    reconstruction_error = max(
        abs(original - recovered)
        for original, recovered in zip(
            wavefunction,
            reconstructed,
        )
    )

    print(f"Number of grid points: {count}")
    print(f"Maximum DFT reconstruction error: {reconstruction_error:.3e}")
    print(
        "The Fourier transform provides a bridge between position-space "
        "and momentum-space descriptions. The direct DFT costs O(N²), "
        "while an FFT reduces the transform cost to approximately O(N log N)."
    )


def demonstration_measurement_sampling() -> None:
    print_title("9. Simulated position measurements")

    x = linspace(-8.0, 8.0, 801)
    wavefunction = gaussian_wave_packet(
        x,
        center=1.5,
        width=0.8,
        momentum=2.0,
    )

    rng = random.Random(20260919)

    measurements = [
        sample_position(x, wavefunction, rng)
        for _ in range(20)
    ]

    print("Twenty simulated position measurements:")
    print(", ".join(f"{value:.3f}" for value in measurements))
    print(
        "Individual measurements are probabilistic. The distribution of "
        "many measurements approaches |ψ(x,t)|²."
    )


# ---------------------------------------------------------------------------
# Edge cases and validation demonstrations
# ---------------------------------------------------------------------------

def demonstration_edge_cases() -> None:
    print_title("10. Edge cases, numerical limitations, and validation")

    x = linspace(-5.0, 5.0, 201)
    dx = x[1] - x[0]

    try:
        normalize_wavefunction([0j for _ in x], dx)
    except ValueError as error:
        print(f"Zero-state validation: correctly rejected ({error})")

    try:
        fft_recursive([1.0 + 0j] * 6)
    except ValueError as error:
        print(f"Invalid FFT length: correctly rejected ({error})")

    wavefunction = gaussian_wave_packet(
        x,
        center=0.0,
        width=0.8,
        momentum=0.0,
    )

    probability = total_probability(wavefunction, dx)
    print(f"Normalized Gaussian probability: {probability:.12f}")

    # Ehrenfest-style diagnostic for a free particle.
    mean_x = expectation_position(x, wavefunction, dx)
    mean_p = expectation_momentum(x, wavefunction, dx)
    energy = expectation_energy(
        x,
        wavefunction,
        free_particle_potential,
    )

    print(f"Initial <x>: {mean_x:.8f}")
    print(f"Initial <p>: {mean_p:.8f}")
    print(f"Initial <H>: {energy:.8f}")

    print("\nImportant numerical constraints:")
    print("- A finite grid replaces continuous space with discrete samples.")
    print("- Boundary conditions affect the physical problem being simulated.")
    print("- Large momenta require sufficient spatial resolution.")
    print("- Rapid potentials require sufficiently small time steps.")
    print("- Generic explicit integrators are not exactly unitary.")
    print("- FFT methods require careful grid and boundary treatment.")


# ---------------------------------------------------------------------------
# Compact reference calculations
# ---------------------------------------------------------------------------

def print_reference_formulas() -> None:
    print_title("11. Mathematical reference")

    formulas = [
        "TDSE: i ħ ∂ψ/∂t = Hψ",
        "Hamiltonian: H = -(ħ²/2m)∂²/∂x² + V(x,t)",
        "Position probability density: ρ(x,t) = |ψ(x,t)|²",
        "Normalization: ∫ |ψ|² dx = 1",
        "Expectation: <A> = ∫ ψ* A ψ dx",
        "Time evolution: ψ(t) = U(t,t0) ψ(t0)",
        "Time-independent H: U(t) = exp[-iH(t-t0)/ħ]",
        "Energy eigenstate: Hφ_n = E_n φ_n",
        "Eigenstate evolution: φ_n(x,t)=φ_n(x)e^(-iE_n t/ħ)",
        "Superposition: ψ = Σ_n c_n φ_n",
        "Uncertainty: Δx Δp >= ħ/2",
        "Probability current in 1D: j = (ħ/m) Im(ψ* ∂ψ/∂x)",
        "Continuity equation: ∂ρ/∂t + ∂j/∂x = 0",
        "Ehrenfest relation: d<x>/dt = <p>/m",
        "Commutator rule: d<A>/dt = (i/ħ)<[H,A]> + <∂A/∂t>",
    ]

    for formula in formulas:
        print(formula)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run the complete educational sequence.

    The examples are intentionally moderate in size so that the program can
    run without external numerical libraries. Scientific production codes
    would normally use optimized linear algebra and FFT libraries.
    """
    print("TIME EVOLUTION AND SCHRÖDINGER EQUATION CONCEPTS")
    print("Dimensionless computational laboratory")
    print("Using ħ = 1 and m = 1 unless explicitly stated.")

    print_reference_formulas()
    demonstration_normalization()
    demonstration_stationary_state()
    demonstration_superposition()
    demonstration_uncertainty()
    demonstration_rk4_time_evolution()
    demonstration_harmonic_oscillator()
    demonstration_tunneling()
    demonstration_fourier_transform()
    demonstration_measurement_sampling()
    demonstration_edge_cases()

    print_title("12. Completed")
    print(
        "The demonstrations covered state normalization, stationary and "
        "non-stationary evolution, superposition, observables, uncertainty, "
        "numerical integration, harmonic motion, tunneling, Fourier methods, "
        "measurement sampling, and numerical edge cases."
    )


if __name__ == "__main__":
    main()
