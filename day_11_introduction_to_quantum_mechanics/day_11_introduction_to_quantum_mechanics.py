"""
Introduction to Quantum Mechanics
Core principles and terminology

A self-contained study script covering quantum mechanics from beginner
foundations to important intermediate and advanced ideas.

The examples use only Python's standard library. Numerical demonstrations
are intentionally small and transparent so that the underlying physics and
mathematics remain visible.
"""

import cmath
import math
import random
from dataclasses import dataclass
from typing import Callable, List, Sequence, Tuple


# ============================================================================
# 1. PHYSICAL CONSTANTS AND BASIC TERMINOLOGY
# ============================================================================

# SI constants used throughout the examples.
H = 6.62607015e-34                  # Planck constant, J*s
HBAR = H / (2.0 * math.pi)         # Reduced Planck constant, J*s
C = 299_792_458.0                  # Speed of light, m/s
ELECTRON_MASS = 9.1093837015e-31   # kg
ELEMENTARY_CHARGE = 1.602176634e-19  # C
EV = ELEMENTARY_CHARGE             # 1 eV in joules

# A few additional constants.
K_B = 1.380649e-23                  # Boltzmann constant, J/K
EPSILON_0 = 8.8541878128e-12       # Vacuum permittivity, F/m


def print_header(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subheader(title: str) -> None:
    """Print a subsection heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def format_complex(z: complex, digits: int = 4) -> str:
    """Format a complex number for readable educational output."""
    return f"{z.real:.{digits}f} {z.imag:+.{digits}f}i"


def normalize_vector(values: Sequence[complex]) -> List[complex]:
    """
    Normalize a state vector.

    Quantum state vectors must satisfy:
        sum_i |c_i|^2 = 1

    The function raises ValueError for a zero vector because a zero vector
    cannot represent a physical normalized quantum state.
    """
    norm_squared = sum(abs(value) ** 2 for value in values)

    if norm_squared <= 0.0:
        raise ValueError("The zero vector cannot be normalized.")

    norm = math.sqrt(norm_squared)
    return [value / norm for value in values]


def probability_amplitudes(state: Sequence[complex]) -> List[float]:
    """
    Convert probability amplitudes into probabilities.

    Born's rule:
        P(i) = |c_i|^2
    """
    return [abs(amplitude) ** 2 for amplitude in state]


def check_normalized(state: Sequence[complex], tolerance: float = 1e-10) -> bool:
    """Check whether a quantum state is normalized."""
    return abs(sum(abs(value) ** 2 for value in state) - 1.0) <= tolerance


# ============================================================================
# 2. CLASSICAL PHYSICS VERSUS QUANTUM PHYSICS
# ============================================================================

def demonstrate_classical_and_quantum_descriptions() -> None:
    """
    Contrast the conceptual descriptions used in classical and quantum
    mechanics.

    Classical mechanics commonly describes a particle using a definite
    position and momentum at a given instant.

    Quantum mechanics instead represents a physical state by a state vector
    or wavefunction. Measurement outcomes are probabilistic, with the
    probabilities determined by the state.
    """
    print_header("1. Classical and quantum descriptions")

    position = 2.0
    momentum = 3.0

    print(f"Classical example: position = {position} m")
    print(f"Classical example: momentum = {momentum} kg*m/s")

    # A two-state quantum system can be represented by amplitudes.
    raw_state = [1.0 + 0.0j, 1.0 + 0.0j]
    state = normalize_vector(raw_state)
    probabilities = probability_amplitudes(state)

    print("\nQuantum two-state example:")
    print("State amplitudes:", [format_complex(x) for x in state])
    print("Measurement probabilities:", probabilities)

    print(
        "\nImportant distinction: a probability amplitude is generally "
        "complex, while a measurement probability is real and non-negative."
    )


# ============================================================================
# 3. QUANTIZATION AND PLANCK'S RELATION
# ============================================================================

def photon_energy_from_frequency(frequency_hz: float) -> float:
    """Calculate photon energy using E = h*f."""
    if frequency_hz < 0:
        raise ValueError("Frequency cannot be negative.")
    return H * frequency_hz


def wavelength_from_frequency(frequency_hz: float) -> float:
    """Calculate electromagnetic wavelength using lambda = c/f."""
    if frequency_hz <= 0:
        raise ValueError("Frequency must be positive.")
    return C / frequency_hz


def demonstrate_quantization() -> None:
    """Demonstrate photon energy quantization."""
    print_header("2. Quantization and Planck's relation")

    frequency = 5.0e14
    energy_joules = photon_energy_from_frequency(frequency)
    energy_ev = energy_joules / EV
    wavelength = wavelength_from_frequency(frequency)

    print(f"Frequency: {frequency:.3e} Hz")
    print(f"Photon energy: {energy_joules:.3e} J")
    print(f"Photon energy: {energy_ev:.3f} eV")
    print(f"Wavelength: {wavelength:.3e} m")

    print(
        "\nPlanck's relation states E = h*f. "
        "Energy is exchanged in discrete quanta in this description."
    )

    # Energy levels of a simple idealized two-level system.
    ground_state_energy = 0.0
    excited_state_energy = 2.0 * EV
    transition_energy = excited_state_energy - ground_state_energy
    transition_frequency = transition_energy / H

    print("\nTwo-level transition:")
    print(f"Energy difference: {transition_energy / EV:.2f} eV")
    print(f"Corresponding frequency: {transition_frequency:.3e} Hz")


# ============================================================================
# 4. WAVE-PARTICLE DUALITY AND DE BROGLIE WAVES
# ============================================================================

def de_broglie_wavelength(momentum: float) -> float:
    """
    Calculate the de Broglie wavelength:
        lambda = h / p
    """
    if momentum <= 0:
        raise ValueError("Momentum must be positive.")
    return H / momentum


def demonstrate_wave_particle_duality() -> None:
    """Demonstrate the de Broglie wavelength."""
    print_header("3. Wave-particle duality")

    electron_speed = 1.0e6
    electron_momentum = ELECTRON_MASS * electron_speed
    wavelength = de_broglie_wavelength(electron_momentum)

    print(f"Electron speed: {electron_speed:.3e} m/s")
    print(f"Electron momentum: {electron_momentum:.3e} kg*m/s")
    print(f"de Broglie wavelength: {wavelength:.3e} m")

    print(
        "\nThe de Broglie relation assigns a wavelength to a particle with "
        "momentum p. Wave-like behavior becomes especially important when "
        "the wavelength is comparable to physical dimensions of a system."
    )


# ============================================================================
# 5. COMPLEX NUMBERS AND PROBABILITY AMPLITUDES
# ============================================================================

def demonstrate_complex_amplitudes() -> None:
    """
    Show why complex numbers naturally appear in quantum mechanics.

    A quantum amplitude may have a phase:
        c = r * exp(i*theta)

    Probability is:
        |c|^2 = c*conjugate(c)
    """
    print_header("4. Complex probability amplitudes")

    magnitude = 1.0 / math.sqrt(2.0)
    phase = math.pi / 3.0

    amplitude = magnitude * cmath.exp(1j * phase)
    probability = abs(amplitude) ** 2

    print(f"Amplitude: {format_complex(amplitude)}")
    print(f"Magnitude: {abs(amplitude):.4f}")
    print(f"Phase: {cmath.phase(amplitude):.4f} radians")
    print(f"Probability: {probability:.4f}")

    # Demonstrate global phase.
    state = normalize_vector([1.0 + 0.0j, 1.0 + 0.0j])
    global_phase = cmath.exp(1j * 1.234)
    shifted_state = [global_phase * x for x in state]

    print("\nGlobal phase demonstration:")
    print("Original probabilities:", probability_amplitudes(state))
    print("After global phase:", probability_amplitudes(shifted_state))

    print(
        "\nA global phase does not change ordinary measurement probabilities. "
        "Relative phase between components can, in contrast, affect "
        "interference."
    )


# ============================================================================
# 6. SUPERPOSITION
# ============================================================================

@dataclass
class Qubit:
    """
    Minimal representation of a two-level quantum state.

    The computational basis is:
        |0> = [1, 0]
        |1> = [0, 1]

    A general pure qubit state is:
        |psi> = alpha|0> + beta|1>
    with:
        |alpha|^2 + |beta|^2 = 1
    """

    alpha: complex
    beta: complex

    def __post_init__(self) -> None:
        normalized = normalize_vector([self.alpha, self.beta])
        self.alpha, self.beta = normalized

    @property
    def probabilities(self) -> Tuple[float, float]:
        """Return probabilities for measuring |0> and |1>."""
        return abs(self.alpha) ** 2, abs(self.beta) ** 2

    def measure(self, rng: random.Random | None = None) -> int:
        """Perform a projective measurement in the computational basis."""
        if rng is None:
            rng = random.Random()

        probability_zero, _ = self.probabilities
        outcome = 0 if rng.random() < probability_zero else 1

        # Projective measurement leaves the state in the observed basis state.
        if outcome == 0:
            self.alpha, self.beta = 1.0 + 0.0j, 0.0 + 0.0j
        else:
            self.alpha, self.beta = 0.0 + 0.0j, 1.0 + 0.0j

        return outcome


def demonstrate_superposition() -> None:
    """Demonstrate superposition and repeated measurements."""
    print_header("5. Superposition and measurement")

    equal_superposition = Qubit(1.0, 1.0)
    print(
        "Normalized state: "
        f"{format_complex(equal_superposition.alpha)}|0> + "
        f"{format_complex(equal_superposition.beta)}|1>"
    )
    print("Probabilities:", equal_superposition.probabilities)

    rng = random.Random(42)
    counts = {0: 0, 1: 0}

    for _ in range(1000):
        qubit = Qubit(1.0, 1.0)
        outcome = qubit.measure(rng)
        counts[outcome] += 1

    print("1000 simulated measurements:", counts)

    print(
        "\nThe state is not simply classical ignorance about whether the "
        "system is already in |0> or |1>. Superposition also carries phase "
        "information, which can produce interference."
    )


# ============================================================================
# 7. INTERFERENCE
# ============================================================================

def two_path_probability(amplitude_a: complex, amplitude_b: complex) -> float:
    """
    Probability associated with two indistinguishable paths.

    Quantum amplitudes are added first:
        A_total = A_a + A_b

    Then Born's rule is applied:
        P = |A_total|^2

    This differs from simply adding |A_a|^2 and |A_b|^2.
    """
    total_amplitude = amplitude_a + amplitude_b
    return abs(total_amplitude) ** 2


def demonstrate_interference() -> None:
    """Demonstrate constructive and destructive interference."""
    print_header("6. Quantum interference")

    amplitude = 1.0 / math.sqrt(2.0)

    constructive = two_path_probability(
        amplitude + 0j,
        amplitude + 0j,
    )

    destructive = two_path_probability(
        amplitude + 0j,
        -amplitude + 0j,
    )

    quarter_phase = two_path_probability(
        amplitude + 0j,
        amplitude * cmath.exp(1j * math.pi / 2.0),
    )

    print(f"Constructive interference: {constructive:.4f}")
    print(f"Destructive interference: {destructive:.4f}")
    print(f"90-degree relative phase: {quarter_phase:.4f}")

    print(
        "\nThe cross terms in |A_a + A_b|^2 are responsible for interference. "
        "The relative phase, not merely the individual path probabilities, "
        "determines whether the contributions reinforce or cancel."
    )


# ============================================================================
# 8. THE WAVEFUNCTION
# ============================================================================

def gaussian_wavefunction(
    x: float,
    center: float = 0.0,
    width: float = 1.0,
    wave_number: float = 0.0,
) -> complex:
    """
    Evaluate a simple normalized Gaussian wave packet.

    This is a one-dimensional model:
        psi(x) proportional to exp(-(x-x0)^2/(4*sigma^2)) * exp(i*k*x)

    The normalization constant is chosen so that the continuous probability
    density integrates to approximately one.
    """
    if width <= 0:
        raise ValueError("Width must be positive.")

    normalization = (1.0 / (2.0 * math.pi * width**2)) ** 0.25
    envelope = math.exp(-((x - center) ** 2) / (4.0 * width**2))
    phase = cmath.exp(1j * wave_number * x)

    return normalization * envelope * phase


def numerical_integral(
    function: Callable[[float], float],
    lower: float,
    upper: float,
    intervals: int = 10_000,
) -> float:
    """Approximate an integral using the trapezoidal rule."""
    if intervals <= 0:
        raise ValueError("Number of intervals must be positive.")

    step = (upper - lower) / intervals
    total = 0.5 * (function(lower) + function(upper))

    for index in range(1, intervals):
        total += function(lower + index * step)

    return total * step


def demonstrate_wavefunction() -> None:
    """Show wavefunction probability density and normalization."""
    print_header("7. Wavefunction and probability density")

    center = 0.0
    width = 0.8

    density = lambda x: abs(
        gaussian_wavefunction(x, center=center, width=width)
    ) ** 2

    normalization = numerical_integral(density, -8.0, 8.0)

    print(f"Approximate integral of |psi(x)|^2: {normalization:.8f}")

    sample_positions = [-2.0, -1.0, 0.0, 1.0, 2.0]
    print("\nPosition -> probability density:")

    for x in sample_positions:
        print(f"{x:6.2f} -> {density(x):.6f}")

    print(
        "\nFor a position-space wavefunction psi(x), |psi(x)|^2 is a "
        "probability density. It is not itself the probability of every "
        "possible position. A probability for an interval requires "
        "integration over that interval."
    )


# ============================================================================
# 9. NORMALIZATION AND EXPECTATION VALUES
# ============================================================================

def expectation_value_discrete(
    eigenvalues: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """
    Calculate the expectation value:
        <A> = sum_i a_i P_i

    This is the statistical mean obtained over many identically prepared
    systems, not a guarantee that a single measurement equals the mean.
    """
    if len(eigenvalues) != len(probabilities):
        raise ValueError("Eigenvalues and probabilities must have equal length.")

    probability_sum = sum(probabilities)

    if not math.isclose(probability_sum, 1.0, abs_tol=1e-10):
        raise ValueError("Probabilities must sum to one.")

    return sum(value * probability for value, probability in zip(
        eigenvalues,
        probabilities,
    ))


def variance_discrete(
    eigenvalues: Sequence[float],
    probabilities: Sequence[float],
) -> float:
    """Calculate variance from a discrete probability distribution."""
    mean = expectation_value_discrete(eigenvalues, probabilities)
    second_moment = sum(
        value**2 * probability
        for value, probability in zip(eigenvalues, probabilities)
    )
    return second_moment - mean**2


def demonstrate_expectation_values() -> None:
    """Demonstrate expectation value and uncertainty."""
    print_header("8. Expectation values and uncertainty")

    outcomes = [1.0, 2.0, 5.0]
    probabilities = [0.2, 0.5, 0.3]

    mean = expectation_value_discrete(outcomes, probabilities)
    variance = variance_discrete(outcomes, probabilities)
    standard_deviation = math.sqrt(max(variance, 0.0))

    print("Measurement outcomes:", outcomes)
    print("Probabilities:", probabilities)
    print(f"Expectation value: {mean:.4f}")
    print(f"Variance: {variance:.4f}")
    print(f"Standard deviation: {standard_deviation:.4f}")

    print(
        "\nThe expectation value is a statistical property of repeated "
        "measurements. It is not necessarily one of the values that a "
        "single measurement can produce."
    )


# ============================================================================
# 10. OPERATORS
# ============================================================================

Matrix = List[List[complex]]


def matrix_vector_multiply(matrix: Matrix, vector: Sequence[complex]) -> List[complex]:
    """Multiply a square matrix by a vector."""
    if len(matrix) == 0:
        raise ValueError("Matrix cannot be empty.")

    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("Matrix dimensions do not match vector dimension.")

    return [
        sum(row[j] * vector[j] for j in range(len(vector)))
        for row in matrix
    ]


def inner_product(
    bra: Sequence[complex],
    ket: Sequence[complex],
) -> complex:
    """
    Calculate <bra|ket>.

    The bra is complex-conjugated before multiplication.
    """
    if len(bra) != len(ket):
        raise ValueError("Vectors must have equal dimensions.")

    return sum(
        bra_value.conjugate() * ket_value
        for bra_value, ket_value in zip(bra, ket)
    )


def expectation_operator(
    state: Sequence[complex],
    operator: Matrix,
) -> complex:
    """
    Calculate:
        <A> = <psi|A|psi>
    """
    transformed = matrix_vector_multiply(operator, state)
    return inner_product(state, transformed)


def demonstrate_operators() -> None:
    """Demonstrate quantum operators using a two-state system."""
    print_header("9. Operators and observables")

    # Pauli Z is an observable with eigenvalues +1 and -1.
    sigma_z: Matrix = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, -1.0 + 0j],
    ]

    state = normalize_vector([1.0, 1.0])

    transformed = matrix_vector_multiply(sigma_z, state)
    expectation = expectation_operator(state, sigma_z)

    print("State:", [format_complex(x) for x in state])
    print("Sigma_z |psi>:", [format_complex(x) for x in transformed])
    print(f"<sigma_z>: {expectation.real:.4f}")

    print(
        "\nIn the standard formulation, physical observables are represented "
        "by Hermitian operators. Their eigenvalues are possible measurement "
        "outcomes, and their expectation values describe averages over "
        "repeated measurements."
    )


# ============================================================================
# 11. EIGENVALUES AND EIGENSTATES
# ============================================================================

def demonstrate_eigenstate_measurement() -> None:
    """
    Demonstrate the simplest eigenstate principle.

    If:
        A|a> = a|a>

    then measuring A in eigenstate |a> produces the eigenvalue a with
    certainty.
    """
    print_header("10. Eigenvalues, eigenstates, and definite outcomes")

    sigma_z: Matrix = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, -1.0 + 0j],
    ]

    zero_state = [1.0 + 0j, 0.0 + 0j]
    one_state = [0.0 + 0j, 1.0 + 0j]

    zero_result = matrix_vector_multiply(sigma_z, zero_state)
    one_result = matrix_vector_multiply(sigma_z, one_state)

    print("Sigma_z |0> =", [format_complex(x) for x in zero_result])
    print("Sigma_z |1> =", [format_complex(x) for x in one_result])

    print(
        "\nThe states |0> and |1> are eigenstates of sigma_z with eigenvalues "
        "+1 and -1 respectively. Measuring sigma_z on either state therefore "
        "has a definite result."
    )


# ============================================================================
# 12. HERMITIAN OPERATORS
# ============================================================================

def is_hermitian(matrix: Matrix, tolerance: float = 1e-10) -> bool:
    """Check whether a matrix equals its conjugate transpose."""
    size = len(matrix)

    if size == 0 or any(len(row) != size for row in matrix):
        return False

    for i in range(size):
        for j in range(size):
            if abs(matrix[i][j] - matrix[j][i].conjugate()) > tolerance:
                return False

    return True


def demonstrate_hermitian_operator() -> None:
    """Demonstrate the Hermitian property of an observable."""
    print_header("11. Hermitian operators")

    sigma_x: Matrix = [
        [0.0 + 0j, 1.0 + 0j],
        [1.0 + 0j, 0.0 + 0j],
    ]

    sigma_y: Matrix = [
        [0.0 + 0j, -1.0j],
        [1.0j, 0.0 + 0j],
    ]

    sigma_z: Matrix = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, -1.0 + 0j],
    ]

    print("Sigma_x Hermitian:", is_hermitian(sigma_x))
    print("Sigma_y Hermitian:", is_hermitian(sigma_y))
    print("Sigma_z Hermitian:", is_hermitian(sigma_z))

    print(
        "\nHermitian operators have real eigenvalues. This is essential because "
        "measurement outcomes for ordinary observables must be real numbers."
    )


# ============================================================================
# 13. POSITION AND MOMENTUM OPERATORS
# ============================================================================

def demonstrate_position_momentum_operators() -> None:
    """
    Explain the position and momentum operators conceptually.

    In one-dimensional position representation:
        x_hat = x

    and:
        p_hat = -i*hbar*d/dx

    This section uses a numerical derivative to illustrate the momentum
    operator acting on a plane wave:
        psi(x) = exp(i*k*x)

    The analytical result is:
        p_hat psi = hbar*k*psi
    """
    print_header("12. Position and momentum operators")

    wave_number = 4.0e9
    expected_momentum = HBAR * wave_number

    x = 1.0e-9
    psi = cmath.exp(1j * wave_number * x)

    delta = 1.0e-13
    psi_plus = cmath.exp(1j * wave_number * (x + delta))
    psi_minus = cmath.exp(1j * wave_number * (x - delta))

    derivative = (psi_plus - psi_minus) / (2.0 * delta)
    momentum_result = -1j * HBAR * derivative

    print(f"Wave number k: {wave_number:.3e} 1/m")
    print(f"Expected momentum hbar*k: {expected_momentum:.3e} kg*m/s")
    print(f"Numerical operator result: {format_complex(momentum_result)}")

    print(
        "\nThe position and momentum operators do not generally commute. "
        "Their non-commutativity is central to the uncertainty principle."
    )


# ============================================================================
# 14. COMMUTATORS
# ============================================================================

def matrix_multiply(a: Matrix, b: Matrix) -> Matrix:
    """Multiply two square matrices."""
    n = len(a)

    if n == 0 or len(b) != n:
        raise ValueError("Matrices must have compatible square dimensions.")

    if any(len(row) != n for row in a + b):
        raise ValueError("Matrices must be square.")

    return [
        [
            sum(a[i][k] * b[k][j] for k in range(n))
            for j in range(n)
        ]
        for i in range(n)
    ]


def matrix_subtract(a: Matrix, b: Matrix) -> Matrix:
    """Subtract two matrices."""
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        raise ValueError("Matrix dimensions must match.")

    return [
        [x - y for x, y in zip(row_a, row_b)]
        for row_a, row_b in zip(a, b)
    ]


def demonstrate_commutator() -> None:
    """
    Demonstrate the commutator:
        [A, B] = AB - BA

    For Pauli matrices:
        [sigma_x, sigma_y] = 2i sigma_z
    """
    print_header("13. Commutators and non-commuting observables")

    sigma_x: Matrix = [
        [0.0 + 0j, 1.0 + 0j],
        [1.0 + 0j, 0.0 + 0j],
    ]

    sigma_y: Matrix = [
        [0.0 + 0j, -1.0j],
        [1.0j, 0.0 + 0j],
    ]

    sigma_z: Matrix = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, -1.0 + 0j],
    ]

    xy = matrix_multiply(sigma_x, sigma_y)
    yx = matrix_multiply(sigma_y, sigma_x)
    commutator = matrix_subtract(xy, yx)

    expected = [
        [2j * value for value in row]
        for row in sigma_z
    ]

    print("[sigma_x, sigma_y]:")
    for row in commutator:
        print([format_complex(x) for x in row])

    print("\n2i*sigma_z:")
    for row in expected:
        print([format_complex(x) for x in row])

    print(
        "\nA nonzero commutator indicates that the corresponding operators "
        "cannot generally be simultaneously diagonalized in the same basis."
    )


# ============================================================================
# 15. HEISENBERG UNCERTAINTY PRINCIPLE
# ============================================================================

def uncertainty_product_bound(
    commutator_expectation_magnitude: float,
) -> float:
    """
    Return the Robertson uncertainty lower bound:
        Delta A * Delta B >= 1/2 |<[A,B]>|
    """
    return 0.5 * commutator_expectation_magnitude


def demonstrate_uncertainty_principle() -> None:
    """
    Explain and numerically illustrate the structure of the uncertainty
    principle.

    For position and momentum:
        Delta x * Delta p >= hbar/2
    """
    print_header("14. Heisenberg uncertainty principle")

    position_uncertainty = 1.0e-10
    minimum_momentum_uncertainty = HBAR / (2.0 * position_uncertainty)

    product = position_uncertainty * minimum_momentum_uncertainty

    print(f"Assumed Delta x: {position_uncertainty:.3e} m")
    print(f"Minimum Delta p: {minimum_momentum_uncertainty:.3e} kg*m/s")
    print(f"Product Delta x * Delta p: {product:.3e} J*s")
    print(f"hbar / 2: {HBAR / 2.0:.3e} J*s")

    print(
        "\nThis is not simply an experimental imperfection. It follows from "
        "the mathematical structure of quantum states and non-commuting "
        "observables."
    )

    print(
        "\nA useful general form is:"
        "\nDelta A * Delta B >= (1/2) |< [A, B] >|."
    )


# ============================================================================
# 16. SCHRODINGER EQUATION
# ============================================================================

def demonstrate_schrodinger_equation() -> None:
    """
    Present the time-dependent and time-independent Schrodinger equations.

    Time-dependent:
        i*hbar*d|psi>/dt = H|psi>

    For an energy eigenstate:
        H|psi> = E|psi>

    The corresponding time evolution is:
        |psi(t)> = exp(-iEt/hbar)|psi(0)>
    """
    print_header("15. Schrodinger equation")

    energy_ev = 2.0
    energy_joules = energy_ev * EV
    time = 1.0e-15

    phase_angle = energy_joules * time / HBAR
    time_factor = cmath.exp(-1j * phase_angle)

    print("Time-dependent equation:")
    print("i*hbar*d|psi>/dt = H|psi>")

    print("\nEnergy eigenvalue equation:")
    print("H|psi> = E|psi>")

    print(f"\nEnergy: {energy_ev:.2f} eV")
    print(f"Time: {time:.3e} s")
    print(f"Phase angle: {phase_angle:.4f} rad")
    print(f"Time-evolution factor: {format_complex(time_factor)}")

    print(
        "\nThe Hamiltonian H is the energy operator and also generates "
        "time evolution in the standard formulation."
    )


# ============================================================================
# 17. TIME EVOLUTION OF A QUBIT
# ============================================================================

def evolve_energy_eigenstate(
    amplitude: complex,
    energy_joules: float,
    time_seconds: float,
) -> complex:
    """Evolve an energy eigenstate amplitude in time."""
    phase = cmath.exp(-1j * energy_joules * time_seconds / HBAR)
    return amplitude * phase


def demonstrate_time_evolution() -> None:
    """
    Demonstrate unitary phase evolution for a two-level energy system.
    """
    print_header("16. Unitary time evolution")

    energy_0 = 0.0
    energy_1 = 1.0 * EV

    state = normalize_vector([1.0, 1.0])
    time = 2.0e-15

    evolved = [
        evolve_energy_eigenstate(state[0], energy_0, time),
        evolve_energy_eigenstate(state[1], energy_1, time),
    ]

    print("Initial amplitudes:", [format_complex(x) for x in state])
    print("Evolved amplitudes:", [format_complex(x) for x in evolved])
    print("Initial probabilities:", probability_amplitudes(state))
    print("Evolved probabilities:", probability_amplitudes(evolved))

    print(
        "\nUnitary evolution preserves normalization. In this example the "
        "relative phase changes even though the probabilities in the energy "
        "basis remain unchanged."
    )


# ============================================================================
# 18. MEASUREMENT AND PROJECTION
# ============================================================================

def projective_measurement_probabilities(
    state: Sequence[complex],
    basis: Sequence[Sequence[complex]],
) -> List[float]:
    """
    Calculate probabilities for a measurement in an orthonormal basis.

    For basis state |b_i>:
        P(i) = |<b_i|psi>|^2
    """
    probabilities = []

    for basis_state in basis:
        amplitude = inner_product(basis_state, state)
        probabilities.append(abs(amplitude) ** 2)

    return probabilities


def demonstrate_measurement_bases() -> None:
    """Show that probabilities depend on the measurement basis."""
    print_header("17. Measurement basis")

    zero = [1.0 + 0j, 0.0 + 0j]
    one = [0.0 + 0j, 1.0 + 0j]

    plus = normalize_vector([1.0, 1.0])
    minus = normalize_vector([1.0, -1.0])

    state = plus

    computational_basis = [zero, one]
    x_basis = [plus, minus]

    z_probabilities = projective_measurement_probabilities(
        state,
        computational_basis,
    )
    x_probabilities = projective_measurement_probabilities(
        state,
        x_basis,
    )

    print("State: |+>")
    print("Measurement in computational basis:", z_probabilities)
    print("Measurement in X basis:", x_probabilities)

    print(
        "\nThe same physical state can have different probability distributions "
        "for different observables or measurement bases."
    )


# ============================================================================
# 19. SPIN-1/2 AND PAULI MATRICES
# ============================================================================

def demonstrate_spin_half() -> None:
    """Introduce spin-1/2 using Pauli matrices."""
    print_header("18. Spin-1/2")

    print("Pauli matrices:")

    matrices = {
        "sigma_x": [
            [0, 1],
            [1, 0],
        ],
        "sigma_y": [
            [0, -1j],
            [1j, 0],
        ],
        "sigma_z": [
            [1, 0],
            [0, -1],
        ],
    }

    for name, matrix in matrices.items():
        print(f"\n{name}")
        for row in matrix:
            print(row)

    print(
        "\nSpin is intrinsic angular momentum. A spin-1/2 particle has a "
        "two-dimensional Hilbert space, so a qubit provides a mathematically "
        "useful representation of its two-level spin degree of freedom."
    )

    print(
        "\nFor a spin-1/2 particle, measurement of spin along an axis has "
        "outcomes conventionally represented as +hbar/2 and -hbar/2."
    )


# ============================================================================
# 20. BRA-KET NOTATION
# ============================================================================

def demonstrate_bra_ket_notation() -> None:
    """
    Demonstrate Dirac notation.

    Ket:
        |psi>

    Bra:
        <psi|

    Inner product:
        <phi|psi>

    Outer product:
        |psi><phi|
    """
    print_header("19. Dirac bra-ket notation")

    ket = normalize_vector([1.0 + 0j, 1.0j])
    bra = [value.conjugate() for value in ket]

    inner = inner_product(ket, ket)

    print("Ket |psi>:", [format_complex(x) for x in ket])
    print("Bra <psi|:", [format_complex(x) for x in bra])
    print(f"<psi|psi> = {format_complex(inner)}")

    print(
        "\nFor a normalized pure state, <psi|psi> = 1. "
        "The inner product also provides probability amplitudes when a "
        "state is projected onto another state."
    )


# ============================================================================
# 21. DENSITY MATRICES AND PURE STATES
# ============================================================================

def outer_product(
    ket: Sequence[complex],
    bra: Sequence[complex],
) -> Matrix:
    """Construct |ket><bra|."""
    return [
        [
            ket_value * bra_value.conjugate()
            for bra_value in bra
        ]
        for ket_value in ket
    ]


def matrix_trace(matrix: Matrix) -> complex:
    """Calculate the trace of a square matrix."""
    if len(matrix) == 0 or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Matrix must be non-empty and square.")

    return sum(matrix[i][i] for i in range(len(matrix)))


def demonstrate_density_matrix() -> None:
    """
    Demonstrate the density matrix of a pure state:
        rho = |psi><psi|

    A density matrix is especially useful for mixed states and open systems.
    """
    print_header("20. Density matrix")

    state = normalize_vector([1.0, 1.0j])
    rho = outer_product(state, state)

    print("State:")
    print([format_complex(x) for x in state])

    print("\nDensity matrix rho = |psi><psi|:")
    for row in rho:
        print([format_complex(x) for x in row])

    print(f"\nTrace(rho): {matrix_trace(rho).real:.4f}")

    print(
        "\nFor a normalized quantum state, a valid density matrix has trace "
        "one. Pure states satisfy Tr(rho^2) = 1, while mixed states satisfy "
        "Tr(rho^2) < 1."
    )


def demonstrate_pure_and_mixed_states() -> None:
    """Compare a pure superposition with an incoherent mixture."""
    print_header("21. Pure state versus mixed state")

    pure_state = normalize_vector([1.0, 1.0])
    pure_density = outer_product(pure_state, pure_state)

    # Equal classical mixture of |0> and |1>.
    mixed_density: Matrix = [
        [0.5 + 0j, 0.0 + 0j],
        [0.0 + 0j, 0.5 + 0j],
    ]

    pure_squared = matrix_multiply(pure_density, pure_density)
    mixed_squared = matrix_multiply(mixed_density, mixed_density)

    pure_purity = matrix_trace(pure_squared).real
    mixed_purity = matrix_trace(mixed_squared).real

    print(f"Pure-state purity: {pure_purity:.4f}")
    print(f"Mixed-state purity: {mixed_purity:.4f}")

    print(
        "\nThe pure superposition contains off-diagonal coherence terms. "
        "The equal incoherent mixture has the same computational-basis "
        "populations but no corresponding phase coherence."
    )


# ============================================================================
# 22. TENSOR PRODUCTS AND COMPOSITE SYSTEMS
# ============================================================================

def tensor_product(
    vector_a: Sequence[complex],
    vector_b: Sequence[complex],
) -> List[complex]:
    """Construct the tensor product of two state vectors."""
    return [
        value_a * value_b
        for value_a in vector_a
        for value_b in vector_b
    ]


def demonstrate_tensor_products() -> None:
    """Demonstrate how Hilbert-space dimensions multiply."""
    print_header("22. Composite systems and tensor products")

    zero = [1.0 + 0j, 0.0 + 0j]
    one = [0.0 + 0j, 1.0 + 0j]

    two_qubit_state = tensor_product(zero, one)

    print("|0>:", zero)
    print("|1>:", one)
    print("|0> tensor |1>:", two_qubit_state)

    print(
        "\nA single qubit has dimension 2. Two qubits have dimension 2*2 = 4. "
        "For n qubits, the Hilbert-space dimension is 2^n."
    )

    for qubits in range(1, 11):
        print(f"{qubits:2d} qubits -> dimension {2**qubits}")


# ============================================================================
# 23. ENTANGLEMENT
# ============================================================================

def demonstrate_bell_state() -> None:
    """
    Construct the Bell state:
        |Phi+> = (|00> + |11>) / sqrt(2)

    This state cannot be written as a tensor product of two individual
    single-qubit pure states.
    """
    print_header("23. Quantum entanglement")

    bell_state = normalize_vector([1.0, 0.0, 0.0, 1.0])

    labels = ["|00>", "|01>", "|10>", "|11>"]

    print("Bell state |Phi+>:")
    for label, amplitude in zip(labels, bell_state):
        if abs(amplitude) > 1e-12:
            print(f"{label}: {format_complex(amplitude)}")

    probabilities = probability_amplitudes(bell_state)
    print("\nComputational-basis probabilities:", probabilities)

    print(
        "\nA measurement of the first qubit in the computational basis gives "
        "0 or 1 with equal probability. The corresponding measurement of the "
        "second qubit is perfectly correlated with it."
    )

    print(
        "\nEntanglement is a property of the joint state. It cannot generally "
        "be understood as two independent local states with ordinary classical "
        "correlations."
    )


# ============================================================================
# 24. THE BORN RULE
# ============================================================================

def born_probability(state: Sequence[complex], basis_state: Sequence[complex]) -> float:
    """Calculate P = |<basis_state|state>|^2."""
    amplitude = inner_product(basis_state, state)
    return abs(amplitude) ** 2


def demonstrate_born_rule() -> None:
    """Demonstrate the Born rule directly."""
    print_header("24. Born rule")

    state = normalize_vector([math.sqrt(0.8), math.sqrt(0.2)])
    zero = [1.0 + 0j, 0.0 + 0j]
    one = [0.0 + 0j, 1.0 + 0j]

    p_zero = born_probability(state, zero)
    p_one = born_probability(state, one)

    print("State amplitudes:", [format_complex(x) for x in state])
    print(f"P(0) = {p_zero:.4f}")
    print(f"P(1) = {p_one:.4f}")
    print(f"Probability sum = {p_zero + p_one:.4f}")

    print(
        "\nThe Born rule connects the mathematical state to experimentally "
        "observable probabilities."
    )


# ============================================================================
# 25. PARTICLE IN A ONE-DIMENSIONAL INFINITE WELL
# ============================================================================

def infinite_well_energy(n: int, width: float, mass: float) -> float:
    """
    Energy levels for an infinite square well:
        E_n = n^2*pi^2*hbar^2 / (2*m*L^2)
    """
    if n <= 0:
        raise ValueError("Quantum number n must be positive.")
    if width <= 0 or mass <= 0:
        raise ValueError("Width and mass must be positive.")

    return (n**2 * math.pi**2 * HBAR**2) / (2.0 * mass * width**2)


def infinite_well_wavefunction(
    n: int,
    x: float,
    width: float,
) -> float:
    """
    Position-space eigenfunction for an infinite square well:
        psi_n(x) = sqrt(2/L) * sin(n*pi*x/L)

    It is defined inside 0 <= x <= L and zero outside.
    """
    if n <= 0 or width <= 0:
        raise ValueError("n and width must be positive.")

    if x < 0.0 or x > width:
        return 0.0

    return math.sqrt(2.0 / width) * math.sin(n * math.pi * x / width)


def demonstrate_infinite_well() -> None:
    """Demonstrate quantized energy levels in an infinite well."""
    print_header("25. Particle in a one-dimensional infinite well")

    width = 1.0e-9
    mass = ELECTRON_MASS

    for n in range(1, 5):
        energy = infinite_well_energy(n, width, mass)
        print(
            f"n={n}: E={energy / EV:.4f} eV, "
            f"E/E1={energy / infinite_well_energy(1, width, mass):.1f}"
        )

    print("\nWavefunction samples for n=1:")
    for fraction in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x = fraction * width
        value = infinite_well_wavefunction(1, x, width)
        print(f"x/L={fraction:.2f}: psi={value:.3e}")

    print(
        "\nThe boundary conditions force only certain stationary wavefunctions "
        "to be allowed. Quantization emerges from the allowed solutions rather "
        "than being inserted as an arbitrary rule."
    )


# ============================================================================
# 26. QUANTUM NUMBERS
# ============================================================================

def demonstrate_quantum_numbers() -> None:
    """
    Introduce the standard quantum numbers for hydrogen-like atoms:

    n: principal quantum number
    l: orbital angular momentum quantum number
    m_l: magnetic quantum number
    m_s: spin projection quantum number
    """
    print_header("26. Quantum numbers")

    print("Example allowed combinations:")

    for n in range(1, 4):
        for l in range(n):
            magnetic_values = list(range(-l, l + 1))
            print(
                f"n={n}, l={l}, allowed m_l={magnetic_values}, "
                f"spin m_s=±1/2"
            )

    print(
        "\nFor the orbital quantum number, l ranges from 0 to n-1. "
        "For a given l, m_l ranges from -l to +l in integer steps."
    )


# ============================================================================
# 27. HYDROGEN ENERGY LEVELS
# ============================================================================

def hydrogen_energy_level(n: int) -> float:
    """
    Approximate non-relativistic hydrogen energy:
        E_n = -13.6 eV / n^2
    """
    if n <= 0:
        raise ValueError("n must be positive.")

    return -13.6 / (n**2)


def demonstrate_hydrogen_levels() -> None:
    """Demonstrate discrete hydrogen energy levels."""
    print_header("27. Hydrogen energy levels")

    for n in range(1, 6):
        energy = hydrogen_energy_level(n)
        print(f"n={n}: E={energy:.4f} eV")

    transition = hydrogen_energy_level(2) - hydrogen_energy_level(1)
    frequency = abs(transition) * EV / H

    print(
        f"\nEnergy difference for n=1 to n=2: {abs(transition):.4f} eV"
    )
    print(f"Photon frequency: {frequency:.3e} Hz")

    print(
        "\nAtomic spectra provide direct evidence of quantized energy levels. "
        "A photon emitted during a transition carries energy equal to the "
        "difference between the initial and final energy levels."
    )


# ============================================================================
# 28. TUNNELING
# ============================================================================

def tunneling_transmission_approximation(
    barrier_width: float,
    barrier_height_joules: float,
    particle_energy_joules: float,
    mass: float,
) -> float:
    """
    Estimate tunneling transmission using the simple WKB-style expression:

        T approximately exp(-2*kappa*a)

    where:
        kappa = sqrt(2*m*(V-E)) / hbar

    This is an approximation, not a universal exact formula.
    """
    if barrier_width <= 0:
        raise ValueError("Barrier width must be positive.")
    if barrier_height_joules <= particle_energy_joules:
        return 1.0
    if mass <= 0:
        raise ValueError("Mass must be positive.")

    kappa = math.sqrt(
        2.0 * mass * (barrier_height_joules - particle_energy_joules)
    ) / HBAR

    exponent = -2.0 * kappa * barrier_width

    # Prevent unnecessary floating-point underflow from producing confusing
    # intermediate behavior in the educational output.
    if exponent < -745:
        return 0.0

    return math.exp(exponent)


def demonstrate_tunneling() -> None:
    """Demonstrate exponential dependence of tunneling probability."""
    print_header("28. Quantum tunneling")

    mass = ELECTRON_MASS
    barrier_height = 1.0 * EV
    particle_energy = 0.5 * EV

    for width_nm in [0.05, 0.10, 0.20, 0.50]:
        width = width_nm * 1.0e-9
        transmission = tunneling_transmission_approximation(
            width,
            barrier_height,
            particle_energy,
            mass,
        )

        print(
            f"Barrier width={width_nm:.2f} nm -> "
            f"approximate transmission={transmission:.6e}"
        )

    print(
        "\nA classically forbidden region can have a nonzero quantum "
        "amplitude. Tunneling is important in alpha decay, scanning tunneling "
        "microscopy, semiconductor devices, and nuclear processes."
    )


# ============================================================================
# 29. HARMONIC OSCILLATOR
# ============================================================================

def harmonic_oscillator_energy(
    quantum_number: int,
    frequency_hz: float,
) -> float:
    """
    Harmonic oscillator energy:
        E_n = hbar*omega*(n + 1/2)
    """
    if quantum_number < 0:
        raise ValueError("Quantum number must be non-negative.")
    if frequency_hz <= 0:
        raise ValueError("Frequency must be positive.")

    omega = 2.0 * math.pi * frequency_hz
    return HBAR * omega * (quantum_number + 0.5)


def demonstrate_harmonic_oscillator() -> None:
    """Demonstrate zero-point energy and equally spaced oscillator levels."""
    print_header("29. Quantum harmonic oscillator")

    frequency = 1.0e13

    for n in range(5):
        energy = harmonic_oscillator_energy(n, frequency)
        print(f"n={n}: E={energy:.3e} J = {energy / EV:.5f} eV")

    print(
        "\nThe lowest energy is not zero. The ground-state energy "
        "E_0 = hbar*omega/2 is called zero-point energy."
    )


# ============================================================================
# 30. ZERO-POINT ENERGY
# ============================================================================

def demonstrate_zero_point_energy() -> None:
    """Explain why the oscillator ground state has nonzero energy."""
    print_header("30. Zero-point energy")

    frequency = 5.0e12
    zero_point = harmonic_oscillator_energy(0, frequency)

    print(f"Oscillator frequency: {frequency:.3e} Hz")
    print(f"Zero-point energy: {zero_point:.3e} J")
    print(f"Zero-point energy: {zero_point / EV:.6f} eV")

    print(
        "\nThe uncertainty principle prevents a bound harmonic oscillator "
        "from simultaneously having exactly zero position uncertainty and "
        "zero momentum uncertainty. The resulting ground state has finite "
        "energy."
    )


# ============================================================================
# 31. BOSONS AND FERMIONS
# ============================================================================

@dataclass(frozen=True)
class ParticleClassification:
    """Basic particle-statistics classification."""

    name: str
    spin_type: str
    statistics: str
    example: str


def demonstrate_bosons_and_fermions() -> None:
    """Introduce the distinction between bosons and fermions."""
    print_header("31. Bosons and fermions")

    particles = [
        ParticleClassification(
            "Electron",
            "half-integer spin",
            "Fermi-Dirac",
            "electron",
        ),
        ParticleClassification(
            "Photon",
            "integer spin",
            "Bose-Einstein",
            "photon",
        ),
        ParticleClassification(
            "Proton",
            "half-integer spin",
            "Fermi-Dirac",
            "proton",
        ),
        ParticleClassification(
            "Helium-4 atom",
            "integer total spin",
            "Bose-Einstein",
            "helium-4",
        ),
    ]

    for particle in particles:
        print(
            f"{particle.name}: {particle.spin_type}, "
            f"{particle.statistics}, example={particle.example}"
        )

    print(
        "\nFermions obey the Pauli exclusion principle. Bosons do not obey "
        "the same exclusion rule and can occupy the same single-particle "
        "quantum state under appropriate conditions."
    )


# ============================================================================
# 32. PAULI EXCLUSION PRINCIPLE
# ============================================================================

def demonstrate_pauli_exclusion() -> None:
    """Explain the Pauli exclusion principle."""
    print_header("32. Pauli exclusion principle")

    print(
        "For identical fermions, the total quantum state is antisymmetric "
        "under exchange of the particles."
    )

    print(
        "\nConsequences include the restriction that two identical electrons "
        "cannot occupy the same complete set of quantum numbers."
    )

    print(
        "\nThis principle is fundamental to atomic structure, the periodic "
        "table, chemical bonding, and the stability of ordinary matter."
    )


# ============================================================================
# 33. IDENTICAL PARTICLES
# ============================================================================

def demonstrate_exchange_symmetry() -> None:
    """
    Demonstrate symmetric and antisymmetric two-particle states.

    Symmetric:
        (|ab> + |ba>) / sqrt(2)

    Antisymmetric:
        (|ab> - |ba>) / sqrt(2)
    """
    print_header("33. Identical particles and exchange symmetry")

    symmetric = normalize_vector([1.0, 0.0, 0.0, 1.0])
    antisymmetric = normalize_vector([1.0, 0.0, 0.0, -1.0])

    print("Symmetric state amplitudes:")
    print([format_complex(x) for x in symmetric])

    print("\nAntisymmetric state amplitudes:")
    print([format_complex(x) for x in antisymmetric])

    print(
        "\nThe sign change under exchange distinguishes bosonic and fermionic "
        "exchange symmetry in the simplest two-particle setting."
    )


# ============================================================================
# 34. QUANTUM SUPERSELECTION OF STATES AND PHASE
# ============================================================================

def relative_phase_state(theta: float) -> Qubit:
    """Create (|0> + exp(i*theta)|1>)/sqrt(2)."""
    return Qubit(
        1.0 / math.sqrt(2.0),
        cmath.exp(1j * theta) / math.sqrt(2.0),
    )


def demonstrate_relative_phase() -> None:
    """Show that relative phase affects measurements in another basis."""
    print_header("34. Relative phase")

    plus = normalize_vector([1.0, 1.0])
    minus = normalize_vector([1.0, -1.0])

    for theta in [0.0, math.pi / 2.0, math.pi]:
        state = relative_phase_state(theta)
        p_plus = born_probability(state_vector(state), plus)
        p_minus = born_probability(state_vector(state), minus)

        print(
            f"theta={theta:.4f} rad -> "
            f"P(+)= {p_plus:.4f}, P(-)= {p_minus:.4f}"
        )

    print(
        "\nRelative phase cannot be detected through every measurement basis "
        "in the same way. It becomes observable when the state interferes "
        "with another amplitude or is measured in a suitable basis."
    )


def state_vector(qubit: Qubit) -> List[complex]:
    """Return the qubit as a state vector."""
    return [qubit.alpha, qubit.beta]


# ============================================================================
# 35. CLASSICAL PROBABILITY VERSUS QUANTUM SUPERPOSITION
# ============================================================================

def demonstrate_classical_mixture_vs_superposition() -> None:
    """Compare identical computational-basis probabilities."""
    print_header("35. Classical mixture versus quantum superposition")

    plus_state = normalize_vector([1.0, 1.0])
    mixture = [
        [0.5 + 0j, 0.0 + 0j],
        [0.0 + 0j, 0.5 + 0j],
    ]

    plus_density = outer_product(plus_state, plus_state)

    print("Superposition density matrix:")
    for row in plus_density:
        print([format_complex(x) for x in row])

    print("\nClassical mixture density matrix:")
    for row in mixture:
        print([format_complex(x) for x in row])

    print(
        "\nBoth have 50/50 probabilities in the computational basis. "
        "They are nevertheless physically different because the superposition "
        "contains off-diagonal coherence."
    )


# ============================================================================
# 36. DECOHERENCE
# ============================================================================

def dephase_density_matrix(
    density_matrix: Matrix,
    coherence_factor: float,
) -> Matrix:
    """
    Apply a simple phenomenological dephasing model.

    Diagonal populations remain unchanged while off-diagonal coherence
    is multiplied by a factor between zero and one.
    """
    if not 0.0 <= coherence_factor <= 1.0:
        raise ValueError("Coherence factor must lie between 0 and 1.")

    size = len(density_matrix)

    return [
        [
            density_matrix[i][j]
            if i == j
            else density_matrix[i][j] * coherence_factor
            for j in range(size)
        ]
        for i in range(size)
    ]


def demonstrate_decoherence() -> None:
    """Demonstrate gradual loss of coherence."""
    print_header("36. Decoherence")

    state = normalize_vector([1.0, 1.0])
    density = outer_product(state, state)

    for factor in [1.0, 0.75, 0.5, 0.25, 0.0]:
        result = dephase_density_matrix(density, factor)
        purity = matrix_trace(matrix_multiply(result, result)).real

        print(
            f"Coherence factor={factor:.2f}, "
            f"purity={purity:.4f}, "
            f"off-diagonal={format_complex(result[0][1])}"
        )

    print(
        "\nDecoherence describes the suppression of phase coherence through "
        "interaction with uncontrolled environmental degrees of freedom. "
        "It is not identical to a fundamental measurement postulate, although "
        "it helps explain why classical-looking behavior emerges in many "
        "macroscopic situations."
    )


# ============================================================================
# 37. UNITARY OPERATIONS
# ============================================================================

def conjugate_transpose(matrix: Matrix) -> Matrix:
    """Return the conjugate transpose of a matrix."""
    return [
        [matrix[j][i].conjugate() for j in range(len(matrix))]
        for i in range(len(matrix[0]))
    ]


def is_identity(matrix: Matrix, tolerance: float = 1e-10) -> bool:
    """Check whether a square matrix is approximately identity."""
    size = len(matrix)

    for i in range(size):
        for j in range(size):
            target = 1.0 if i == j else 0.0
            if abs(matrix[i][j] - target) > tolerance:
                return False

    return True


def demonstrate_unitary_operator() -> None:
    """
    Demonstrate the Hadamard gate:
        H = 1/sqrt(2) [[1,1],[1,-1]]

    It is unitary:
        H†H = I
    """
    print_header("37. Unitary transformations")

    scale = 1.0 / math.sqrt(2.0)

    hadamard: Matrix = [
        [scale + 0j, scale + 0j],
        [scale + 0j, -scale + 0j],
    ]

    product = matrix_multiply(
        conjugate_transpose(hadamard),
        hadamard,
    )

    print("H†H:")
    for row in product:
        print([format_complex(x) for x in row])

    print("Is approximately identity:", is_identity(product))

    state_zero = [1.0 + 0j, 0.0 + 0j]
    result = matrix_vector_multiply(hadamard, state_zero)

    print("\nH|0>:", [format_complex(x) for x in result])

    print(
        "\nUnitary transformations preserve inner products and normalization. "
        "They describe reversible closed-system quantum evolution and are "
        "central to quantum computing."
    )


# ============================================================================
# 38. QUANTUM GATES
# ============================================================================

def apply_operator(operator: Matrix, state: Sequence[complex]) -> List[complex]:
    """Apply a matrix operator to a state vector."""
    result = matrix_vector_multiply(operator, state)
    return normalize_vector(result)


def demonstrate_basic_quantum_gates() -> None:
    """Demonstrate X, Y, Z and Hadamard operations."""
    print_header("38. Basic quantum gates")

    identity = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, 1.0 + 0j],
    ]

    pauli_x = [
        [0.0 + 0j, 1.0 + 0j],
        [1.0 + 0j, 0.0 + 0j],
    ]

    pauli_y = [
        [0.0 + 0j, -1.0j],
        [1.0j, 0.0 + 0j],
    ]

    pauli_z = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, -1.0 + 0j],
    ]

    scale = 1.0 / math.sqrt(2.0)
    hadamard = [
        [scale + 0j, scale + 0j],
        [scale + 0j, -scale + 0j],
    ]

    state = [1.0 + 0j, 0.0 + 0j]

    gates = {
        "I": identity,
        "X": pauli_x,
        "Y": pauli_y,
        "Z": pauli_z,
        "H": hadamard,
    }

    for name, gate in gates.items():
        result = apply_operator(gate, state)
        print(f"{name}|0> -> {[format_complex(x) for x in result]}")


# ============================================================================
# 39. NO-CLONING THEOREM
# ============================================================================

def demonstrate_no_cloning_theorem() -> None:
    """
    Explain the no-cloning theorem.

    If a universal cloning operation U could clone every unknown state:
        U|psi>|0> = |psi>|psi>

    then applying it to two possible states and using linearity would produce
    contradictions for non-orthogonal states.
    """
    print_header("39. No-cloning theorem")

    print(
        "Suppose a cloning operation U satisfies:"
        "\nU(|psi>|0>) = |psi>|psi>"
    )

    print(
        "\nFor two states |a> and |b>, linearity requires:"
        "\nU((alpha|a> + beta|b>)|0>)"
        "\n= alpha|a>|a> + beta|b>|b>"
    )

    print(
        "\nA genuine clone of the superposition would instead be:"
        "\n(alpha|a> + beta|b>) (alpha|a> + beta|b>)"
    )

    print(
        "\nThese expressions are generally different. Therefore an unknown "
        "arbitrary quantum state cannot be perfectly copied by a universal "
        "physical operation."
    )


# ============================================================================
# 40. QUANTUM TELEPORTATION CONCEPT
# ============================================================================

def demonstrate_quantum_teleportation_concept() -> None:
    """
    Describe the conceptual ingredients of quantum teleportation.

    Teleportation transfers an unknown quantum state using:
        1. Shared entanglement
        2. A joint measurement
        3. Classical communication
        4. A conditional correction

    It does not transmit matter or usable information faster than light.
    """
    print_header("40. Quantum teleportation")

    steps = [
        "Alice and Bob share an entangled pair.",
        "Alice combines the unknown state with her entangled qubit.",
        "Alice performs a joint measurement.",
        "Alice sends classical measurement information to Bob.",
        "Bob applies a conditional quantum correction.",
        "Bob obtains the original state at his location.",
    ]

    for index, step in enumerate(steps, start=1):
        print(f"{index}. {step}")

    print(
        "\nTeleportation does not violate the no-cloning theorem because the "
        "original state is not retained after the protocol's measurement, "
        "and classical communication is required."
    )


# ============================================================================
# 41. QUANTUM ZENO EFFECT
# ============================================================================

def quantum_zeno_survival_probability(
    decay_rate: float,
    total_time: float,
    measurements: int,
) -> float:
    """
    Illustrative short-time survival approximation.

    For sufficiently short intervals:
        P_survival approximately [1 - Gamma*(t/N)]^N

    This simple expression is an educational approximation, not a universal
    description of every physical quantum Zeno experiment.
    """
    if decay_rate < 0 or total_time < 0 or measurements <= 0:
        raise ValueError("Arguments must have valid non-negative values.")

    interval = total_time / measurements
    single_survival = max(0.0, 1.0 - decay_rate * interval)

    return single_survival ** measurements


def demonstrate_quantum_zeno_effect() -> None:
    """Illustrate frequent measurement effects in a simple model."""
    print_header("41. Quantum Zeno effect")

    decay_rate = 1.0
    total_time = 1.0

    for measurements in [1, 2, 5, 10, 100, 1000]:
        survival = quantum_zeno_survival_probability(
            decay_rate,
            total_time,
            measurements,
        )

        print(
            f"Measurements={measurements:4d} -> "
            f"approximate survival={survival:.6f}"
        )

    print(
        "\nThe quantum Zeno effect refers to the inhibition or modification "
        "of evolution through sufficiently frequent measurements or strong "
        "coupling to a measurement-like environment. Its precise behavior "
        "depends on the physical system and measurement model."
    )


# ============================================================================
# 42. CLASSICAL LIMIT
# ============================================================================

def demonstrate_classical_limit() -> None:
    """
    Explain why quantum mechanics can reproduce classical behavior.

    Important mechanisms include:
        - Large quantum numbers
        - Short de Broglie wavelengths relative to system scale
        - Decoherence
        - Wave-packet localization
        - Correspondence between quantum and classical dynamics
    """
    print_header("42. Classical limit")

    masses = [
        ("electron", ELECTRON_MASS),
        ("1 gram object", 1.0e-3),
    ]

    speed = 1.0

    for name, mass in masses:
        wavelength = de_broglie_wavelength(mass * speed)
        print(f"{name}: lambda={wavelength:.3e} m")

    print(
        "\nFor macroscopic masses at ordinary speeds, de Broglie wavelengths "
        "are extraordinarily small compared with everyday length scales. "
        "This helps explain why classical trajectories are often excellent "
        "approximations."
    )


# ============================================================================
# 43. WAVE-PACKET DISPERSION
# ============================================================================

def free_particle_energy(momentum: float, mass: float) -> float:
    """Non-relativistic free-particle kinetic energy."""
    if mass <= 0:
        raise ValueError("Mass must be positive.")
    return momentum**2 / (2.0 * mass)


def demonstrate_wave_packet_dispersion() -> None:
    """
    Explain free-particle wave-packet dispersion.

    Because E depends nonlinearly on momentum for a non-relativistic free
    particle, different momentum components acquire different phases over
    time, causing a localized wave packet to spread.
    """
    print_header("43. Wave-packet dispersion")

    mass = ELECTRON_MASS
    momenta = [0.9e-24, 1.0e-24, 1.1e-24]

    for momentum in momenta:
        energy = free_particle_energy(momentum, mass)
        print(
            f"p={momentum:.3e} kg*m/s -> "
            f"E={energy:.3e} J"
        )

    print(
        "\nA localized wave packet contains a range of momentum components. "
        "Since those components generally evolve with different angular "
        "frequencies, the packet can broaden with time."
    )


# ============================================================================
# 44. PERTURBATION THEORY CONCEPT
# ============================================================================

def first_order_energy_shift(
    perturbation_expectation: float,
) -> float:
    """
    First-order perturbation theory:
        Delta E_n^(1) = <n|V|n>

    The function accepts the already-calculated expectation value of the
    perturbing Hamiltonian in the unperturbed state.
    """
    return perturbation_expectation


def demonstrate_perturbation_theory() -> None:
    """Introduce the basic idea of perturbation theory."""
    print_header("44. Perturbation theory")

    unperturbed_energy = -13.6 * EV
    perturbation = 0.10 * EV

    first_order_shift = first_order_energy_shift(perturbation)
    approximate_energy = unperturbed_energy + first_order_shift

    print(f"Unperturbed energy: {unperturbed_energy / EV:.4f} eV")
    print(f"First-order correction: {first_order_shift / EV:.4f} eV")
    print(f"Approximate corrected energy: {approximate_energy / EV:.4f} eV")

    print(
        "\nPerturbation theory is useful when a Hamiltonian can be separated "
        "into a solvable dominant part and a smaller correction. It produces "
        "a controlled approximation when the perturbation is sufficiently "
        "weak and the expansion remains well behaved."
    )


# ============================================================================
# 45. VARIATIONAL PRINCIPLE
# ============================================================================

def demonstrate_variational_principle() -> None:
    """
    Demonstrate the conceptual variational bound.

    For a normalized trial state |psi_trial>:
        E_trial = <psi_trial|H|psi_trial>

    For a Hamiltonian bounded from below:
        E_trial >= E_ground

    The example uses an abstract numerical ground-state estimate.
    """
    print_header("45. Variational principle")

    estimated_ground_energy = 1.234
    trial_energies = [2.1, 1.7, 1.5, 1.31, 1.25]

    print(f"Reference ground-state estimate: {estimated_ground_energy:.3f}")

    for energy in trial_energies:
        print(
            f"Trial expectation={energy:.3f}, "
            f"above reference={energy >= estimated_ground_energy}"
        )

    print(
        "\nThe variational method converts the search for a ground state into "
        "an optimization problem over a family of normalized trial states."
    )


# ============================================================================
# 46. APPROXIMATION, MODEL VALIDITY, AND NUMERICAL ISSUES
# ============================================================================

def demonstrate_numerical_considerations() -> None:
    """Show numerical precision and normalization issues."""
    print_header("46. Numerical considerations")

    tiny = 1.0e-300
    squared = tiny**2

    print(f"Very small amplitude: {tiny:.3e}")
    print(f"Squared magnitude: {squared:.3e}")

    try:
        normalize_vector([0.0 + 0j, 0.0 + 0j])
    except ValueError as error:
        print("Zero-state normalization error:", error)

    almost_normalized = [math.sqrt(0.5), math.sqrt(0.5) + 1e-12]
    almost_normalized = normalize_vector(almost_normalized)

    print(
        "Corrected normalized state:",
        [format_complex(x) for x in almost_normalized],
    )

    print(
        "\nNumerical quantum mechanics requires attention to normalization, "
        "floating-point rounding, matrix conditioning, discretization error, "
        "and underflow or overflow in exponentially small or large quantities."
    )


# ============================================================================
# 47. ERROR HANDLING AND PHYSICAL VALIDATION
# ============================================================================

def demonstrate_physical_validation() -> None:
    """Demonstrate defensive validation of physical inputs."""
    print_header("47. Validation and physical constraints")

    invalid_cases = [
        ("negative frequency", lambda: photon_energy_from_frequency(-1.0)),
        ("zero wavelength frequency", lambda: wavelength_from_frequency(0.0)),
        ("negative well width", lambda: infinite_well_energy(1, -1.0, 1.0)),
        ("invalid harmonic number", lambda: harmonic_oscillator_energy(-1, 1.0)),
    ]

    for name, operation in invalid_cases:
        try:
            operation()
        except ValueError as error:
            print(f"{name}: correctly rejected -> {error}")

    print(
        "\nPhysical formulas often have domains of validity. Input validation "
        "prevents a mathematically computable number from being mistaken for "
        "a physically meaningful result."
    )


# ============================================================================
# 48. COMMON CONCEPTUAL MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    """Print common misconceptions and their corrections."""
    print_header("48. Common conceptual mistakes")

    mistakes = [
        (
            "A particle is always literally a classical wave.",
            "Quantum states can exhibit wave-like interference, but the "
            "wavefunction is a quantum state description, not simply an "
            "ordinary classical material wave."
        ),
        (
            "Uncertainty only comes from bad instruments.",
            "The uncertainty relations arise from the structure of quantum "
            "states and non-commuting observables."
        ),
        (
            "A probability amplitude is itself a probability.",
            "Probabilities are obtained from squared magnitudes of amplitudes "
            "according to the Born rule."
        ),
        (
            "Measurement merely reveals a pre-existing classical value.",
            "Quantum measurement is described by a specific measurement "
            "formalism and can change the state."
        ),
        (
            "Entanglement allows faster-than-light messaging.",
            "Entanglement produces nonclassical correlations, but it does not "
            "by itself provide controllable faster-than-light communication."
        ),
        (
            "Quantum means anything is possible.",
            "Quantum theory imposes precise mathematical constraints on "
            "states, probabilities, observables, and dynamics."
        ),
        (
            "The uncertainty principle says position and momentum are both "
            "completely unknown.",
            "It constrains the product of their statistical uncertainties."
        ),
    ]

    for misconception, correction in mistakes:
        print(f"\nMisconception: {misconception}")
        print(f"Correction: {correction}")


# ============================================================================
# 49. MEASUREMENT POSTULATES IN COMPACT FORM
# ============================================================================

def demonstrate_measurement_postulates() -> None:
    """Present a compact operational form of the standard postulates."""
    print_header("49. Core quantum-mechanical postulates")

    postulates = [
        (
            "State",
            "A physical system is represented by a state vector in a "
            "Hilbert space, or more generally by a density operator."
        ),
        (
            "Observables",
            "Measurable quantities are represented by suitable Hermitian "
            "operators in the standard formulation."
        ),
        (
            "Born rule",
            "Measurement probabilities are determined from the state and "
            "the relevant projectors or measurement operators."
        ),
        (
            "Evolution",
            "Closed-system evolution is unitary and generated by the "
            "Hamiltonian through the Schrodinger equation."
        ),
        (
            "Composite systems",
            "The state space of a composite system is formed using tensor "
            "products of the subsystem Hilbert spaces."
        ),
        (
            "Measurement update",
            "A measurement outcome is associated with an update of the "
            "state according to the measurement formalism being used."
        ),
    ]

    for name, description in postulates:
        print(f"\n{name}:")
        print(f"  {description}")


# ============================================================================
# 50. GENERALIZED MEASUREMENTS
# ============================================================================

def demonstrate_povm_concept() -> None:
    """
    Introduce POVMs conceptually.

    A POVM consists of positive operators E_i satisfying:
        sum_i E_i = I

    Measurement probabilities are:
        P(i) = Tr(rho E_i)
    """
    print_header("50. Generalized measurements and POVMs")

    print("POVM conditions:")
    print("1. E_i is positive semidefinite.")
    print("2. Sum_i E_i = I.")
    print("3. P(i) = Tr(rho E_i).")

    print(
        "\nPOVMs generalize projective measurements and are useful when "
        "describing realistic measurement procedures, noisy detectors, "
        "quantum state discrimination, and quantum information protocols."
    )


# ============================================================================
# 51. OPEN QUANTUM SYSTEMS
# ============================================================================

def demonstrate_open_systems() -> None:
    """
    Explain why closed-system unitary evolution is not always enough.

    Real systems interact with environments. Density matrices and dynamical
    maps are therefore important for modeling noise and decoherence.
    """
    print_header("51. Open quantum systems")

    print(
        "Closed system:"
        "\n  rho(t) = U rho(0) U†"
    )

    print(
        "\nOpen system:"
        "\n  rho(t) is generally affected by environmental interaction."
    )

    print(
        "\nTypical effects include:"
        "\n  - dephasing"
        "\n  - relaxation"
        "\n  - thermalization"
        "\n  - amplitude damping"
        "\n  - loss of quantum coherence"
    )

    print(
        "\nA reduced system can undergo non-unitary evolution even when the "
        "larger combined system plus environment evolves unitarily."
    )


# ============================================================================
# 52. CONSERVATION LAWS AND SYMMETRY
# ============================================================================

def demonstrate_symmetry_and_conservation() -> None:
    """
    Explain the relationship between symmetries and conserved quantities.

    In quantum mechanics, a continuous symmetry is associated with a generator.
    When the relevant generator is compatible with the Hamiltonian, the
    corresponding observable can be conserved under appropriate conditions.
    """
    print_header("52. Symmetry and conservation")

    print(
        "Examples of important symmetry-conservation relationships:"
    )

    relationships = [
        ("Time-translation symmetry", "Energy"),
        ("Spatial translation symmetry", "Momentum"),
        ("Rotational symmetry", "Angular momentum"),
    ]

    for symmetry, conserved_quantity in relationships:
        print(f"{symmetry} -> {conserved_quantity}")

    print(
        "\nThe mathematical condition often appears through a commutator. "
        "For a time-independent observable A, a vanishing commutator "
        "[H, A] = 0 implies conservation of its expectation value under "
        "closed-system unitary evolution."
    )


# ============================================================================
# 53. ANGULAR MOMENTUM
# ============================================================================

def demonstrate_angular_momentum() -> None:
    """
    Introduce orbital angular momentum eigenvalues:

        L^2 |l,m> = hbar^2*l(l+1)|l,m>
        L_z |l,m> = hbar*m|l,m>
    """
    print_header("53. Angular momentum")

    for l in range(4):
        total_squared_factor = l * (l + 1)
        allowed_m = list(range(-l, l + 1))

        print(
            f"l={l}: L^2 eigenvalue factor={total_squared_factor}, "
            f"m={allowed_m}"
        )

    print(
        "\nAngular momentum is quantized. For a given orbital quantum number "
        "l, the z-component has discrete values hbar*m."
    )


# ============================================================================
# 54. HYDROGEN ORBITALS AS PROBABILITY DISTRIBUTIONS
# ============================================================================

def radial_probability_demo(
    radius: float,
    bohr_radius: float = 5.29177210903e-11,
) -> float:
    """
    Simple 1s hydrogen radial probability model.

    The exact radial probability density for 1s can be represented by:
        P(r) = 4*r^2/a0^3 * exp(-2r/a0)

    This function is normalized over r from 0 to infinity.
    """
    if radius < 0:
        raise ValueError("Radius cannot be negative.")

    a0 = bohr_radius
    return 4.0 * radius**2 / a0**3 * math.exp(-2.0 * radius / a0)


def demonstrate_hydrogen_probability_cloud() -> None:
    """Demonstrate probability density rather than classical orbit."""
    print_header("54. Atomic orbitals and probability distributions")

    a0 = 5.29177210903e-11

    print("1s radial probability model:")
    for multiplier in [0.0, 0.5, 1.0, 2.0, 3.0]:
        radius = multiplier * a0
        probability_density = radial_probability_demo(radius, a0)
        print(
            f"r/a0={multiplier:.1f} -> "
            f"P(r)={probability_density:.3e} 1/m"
        )

    print(
        "\nAn atomic orbital is a quantum state or wavefunction, not a "
        "classical planetary path. The squared wavefunction determines "
        "probability density."
    )


# ============================================================================
# 55. DIMENSIONAL ANALYSIS
# ============================================================================

def demonstrate_dimensions() -> None:
    """Demonstrate dimensional consistency of fundamental quantum equations."""
    print_header("55. Dimensional analysis")

    print("Planck relation:")
    print("E = h*f")
    print("[h] = J*s")
    print("[f] = 1/s")
    print("[h*f] = J")

    print("\nde Broglie relation:")
    print("lambda = h/p")
    print("[h] = kg*m^2/s")
    print("[p] = kg*m/s")
    print("[h/p] = m")

    print("\nUncertainty relation:")
    print("Delta x * Delta p >= hbar/2")
    print("[x*p] = m*(kg*m/s) = J*s")

    print(
        "\nDimensional analysis is a useful debugging technique. A formula "
        "with inconsistent physical dimensions cannot be correct as written."
    )


# ============================================================================
# 56. RELATIVISTIC CAVEAT
# ============================================================================

def demonstrate_nonrelativistic_limit() -> None:
    """
    Explain the domain of the non-relativistic Schrodinger equation.

    The non-relativistic kinetic energy:
        E = p^2/(2m)

    is an approximation to relativistic dynamics when speeds are much lower
    than c and kinetic energies are small compared with rest energy.
    """
    print_header("56. Non-relativistic approximation")

    speed = 0.01 * C
    kinetic_nonrelativistic = 0.5 * ELECTRON_MASS * speed**2
    rest_energy = ELECTRON_MASS * C**2

    ratio = kinetic_nonrelativistic / rest_energy

    print(f"Speed as fraction of c: {speed / C:.3f}")
    print(
        f"Non-relativistic kinetic energy / rest energy: "
        f"{ratio:.6e}"
    )

    print(
        "\nThe ordinary Schrodinger equation is non-relativistic. At speeds "
        "approaching c or when relativistic effects are essential, relativistic "
        "quantum theories such as the Dirac equation or quantum field theory "
        "become appropriate."
    )


# ============================================================================
# 57. QUANTUM FIELD THEORY CONTEXT
# ============================================================================

def demonstrate_quantum_field_theory_context() -> None:
    """
    Place ordinary quantum mechanics in the broader theoretical hierarchy.
    """
    print_header("57. Quantum mechanics and quantum field theory")

    print(
        "Non-relativistic quantum mechanics:"
        "\n  Useful for atoms, molecules, low-energy particles, and many "
        "condensed-matter models."
    )

    print(
        "\nRelativistic quantum mechanics:"
        "\n  Incorporates special relativity into quantum wave equations."
    )

    print(
        "\nQuantum field theory:"
        "\n  Treats fields as fundamental dynamical objects and naturally "
        "handles particle creation and annihilation."
    )

    print(
        "\nThe core quantum concepts introduced here, such as superposition, "
        "operators, commutators, Hilbert spaces, probability amplitudes, "
        "and unitary evolution, remain central in more advanced formulations."
    )


# ============================================================================
# 58. A SMALL QUANTUM STATE SIMULATOR
# ============================================================================

class QuantumStateSimulator:
    """
    Minimal state-vector simulator for educational two-level systems.

    This class is deliberately small. It demonstrates the linear algebra
    underlying a basic quantum circuit without pretending to model physical
    hardware noise, relativistic effects, or arbitrary many-body systems.
    """

    def __init__(self, state: Sequence[complex] | None = None) -> None:
        if state is None:
            state = [1.0 + 0j, 0.0 + 0j]

        self.state = normalize_vector(state)

    def apply(self, operator: Matrix) -> None:
        """Apply a linear operator and normalize the resulting state."""
        self.state = apply_operator(operator, self.state)

    def probabilities(self) -> List[float]:
        """Return computational-basis probabilities."""
        return probability_amplitudes(self.state)

    def measure(self, rng: random.Random | None = None) -> int:
        """Measure the simulated qubit and collapse its state."""
        qubit = Qubit(self.state[0], self.state[1])
        result = qubit.measure(rng)
        self.state = state_vector(qubit)
        return result

    def display(self) -> None:
        """Display the state amplitudes and probabilities."""
        print("State:", [format_complex(x) for x in self.state])
        print("Probabilities:", self.probabilities())


def demonstrate_small_quantum_simulator() -> None:
    """Build and measure a simple H-X-H circuit."""
    print_header("58. Small quantum state simulator")

    scale = 1.0 / math.sqrt(2.0)

    hadamard = [
        [scale + 0j, scale + 0j],
        [scale + 0j, -scale + 0j],
    ]

    pauli_x = [
        [0.0 + 0j, 1.0 + 0j],
        [1.0 + 0j, 0.0 + 0j],
    ]

    simulator = QuantumStateSimulator()

    print("Initial:")
    simulator.display()

    simulator.apply(hadamard)
    print("\nAfter H:")
    simulator.display()

    simulator.apply(pauli_x)
    print("\nAfter X:")
    simulator.display()

    simulator.apply(hadamard)
    print("\nAfter H again:")
    simulator.display()

    rng = random.Random(7)
    measurement = simulator.measure(rng)
    print(f"\nMeasurement result: {measurement}")
    simulator.display()


# ============================================================================
# 59. MULTIPLE MEASUREMENT EXPERIMENT
# ============================================================================

def run_measurement_experiment(
    state: Sequence[complex],
    trials: int = 10_000,
    seed: int = 123,
) -> Tuple[int, int]:
    """Repeatedly measure a fixed prepared qubit state."""
    if trials <= 0:
        raise ValueError("Trials must be positive.")

    normalized = normalize_vector(state)
    rng = random.Random(seed)

    counts = [0, 0]

    for _ in range(trials):
        qubit = Qubit(normalized[0], normalized[1])
        outcome = qubit.measure(rng)
        counts[outcome] += 1

    return counts[0], counts[1]


def demonstrate_statistical_predictions() -> None:
    """Compare theoretical probabilities with experimental frequencies."""
    print_header("59. Repeated measurements and statistical convergence")

    state = normalize_vector([
        math.sqrt(0.7),
        math.sqrt(0.3),
    ])

    theoretical = probability_amplitudes(state)
    counts = run_measurement_experiment(state, trials=10_000)

    experimental = [
        counts[0] / 10_000,
        counts[1] / 10_000,
    ]

    print("Theoretical probabilities:", theoretical)
    print("Experimental frequencies:", experimental)

    print(
        "\nQuantum theory predicts probability distributions. Individual "
        "measurements are random according to the measurement rule, while "
        "large samples tend to approach the theoretical probabilities."
    )


# ============================================================================
# 60. ENERGY-TIME RELATION CAVEAT
# ============================================================================

def demonstrate_energy_time_relation() -> None:
    """
    Explain the important distinction between the standard Robertson relation
    for two observables and energy-time uncertainty.

    Unlike position and momentum, time is not generally represented by a
    universal self-adjoint operator in ordinary non-relativistic quantum
    mechanics in the same way position is.
    """
    print_header("60. Energy-time uncertainty")

    energy_spread = 1.0 * EV
    characteristic_time = HBAR / (2.0 * energy_spread)

    print(f"Energy spread: {energy_spread / EV:.2f} eV")
    print(
        f"Characteristic timescale hbar/(2*Delta E): "
        f"{characteristic_time:.3e} s"
    )

    print(
        "\nEnergy-time uncertainty relations require careful interpretation. "
        "They are not simply identical to the position-momentum relation with "
        "time substituted for position."
    )


# ============================================================================
# 61. MEASUREMENT DISTURBANCE
# ============================================================================

def demonstrate_measurement_disturbance() -> None:
    """Explain why measurement and uncertainty should not be conflated."""
    print_header("61. Measurement disturbance versus uncertainty")

    print(
        "Uncertainty principle:"
        "\n  A statement about statistical spreads of quantum observables "
        "in a state."
    )

    print(
        "\nMeasurement disturbance:"
        "\n  A statement about how a particular measurement procedure changes "
        "the quantum state or affects subsequent measurements."
    )

    print(
        "\nThese concepts are related but not identical. A careful analysis "
        "must specify the quantum state, observables, and measurement model."
    )


# ============================================================================
# 62. QUANTUM STATE SPACE AND HILBERT SPACE
# ============================================================================

def demonstrate_hilbert_space() -> None:
    """
    Explain the basic mathematical structure.

    A Hilbert space is a complete inner-product vector space. Quantum states
    are represented by normalized vectors or density operators on such a
    space.
    """
    print_header("62. Hilbert space")

    state = normalize_vector([
        1.0,
        2.0,
        2.0,
    ])

    norm_squared = sum(abs(value) ** 2 for value in state)

    print("Example normalized state:")
    print([format_complex(x) for x in state])
    print(f"Norm squared: {norm_squared:.6f}")

    print(
        "\nImportant structures include:"
        "\n  - Vector addition"
        "\n  - Scalar multiplication"
        "\n  - Inner products"
        "\n  - Orthogonality"
        "\n  - Completeness"
        "\n  - Linear operators"
    )


# ============================================================================
# 63. ORTHONORMAL BASES
# ============================================================================

def demonstrate_orthonormal_basis() -> None:
    """Demonstrate expansion in an orthonormal basis."""
    zero = [1.0 + 0j, 0.0 + 0j]
    one = [0.0 + 0j, 1.0 + 0j]

    state = normalize_vector([1.0, 2.0])

    coefficient_zero = inner_product(zero, state)
    coefficient_one = inner_product(one, state)

    print_header("63. Orthonormal basis expansion")

    print(f"<0|psi> = {format_complex(coefficient_zero)}")
    print(f"<1|psi> = {format_complex(coefficient_one)}")

    reconstructed = [
        coefficient_zero * zero[i] + coefficient_one * one[i]
        for i in range(2)
    ]

    print(
        "Reconstructed state:",
        [format_complex(x) for x in reconstructed],
    )

    print(
        "\nA state can be represented using any complete orthonormal basis. "
        "Changing basis changes the coordinates used to describe the same "
        "abstract quantum state."
    )


# ============================================================================
# 64. PHASE, INTERFERENCE, AND GAUGE-LIKE REDUNDANCY
# ============================================================================

def demonstrate_phase_invariance() -> None:
    """Show global phase invariance numerically."""
    print_header("64. Global phase invariance")

    state = normalize_vector([1.0, 2.0j])
    phase = cmath.exp(1j * 2.0)

    transformed = [phase * x for x in state]

    print("Original probabilities:", probability_amplitudes(state))
    print("Phase-shifted probabilities:", probability_amplitudes(transformed))

    overlap_magnitude = abs(inner_product(state, transformed))
    print(f"|<psi|e^(i*phi)psi>| = {overlap_magnitude:.6f}")

    print(
        "\nMultiplication of every component by the same phase does not change "
        "physical measurement probabilities. Relative phases between components "
        "can be physically significant."
    )


# ============================================================================
# 65. COMPLETENESS RELATION
# ============================================================================

def demonstrate_completeness_relation() -> None:
    """
    For an orthonormal basis {|i>}:
        sum_i |i><i| = I
    """
    print_header("65. Completeness relation")

    basis = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, 1.0 + 0j],
    ]

    completeness: Matrix = [
        [0.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, 0.0 + 0j],
    ]

    for vector in basis:
        projector = outer_product(vector, vector)

        for i in range(2):
            for j in range(2):
                completeness[i][j] += projector[i][j]

    print("Sum of projectors:")
    for row in completeness:
        print([format_complex(x) for x in row])

    print("Identity:", is_identity(completeness))


# ============================================================================
# 66. EXPECTATION VALUES FROM DENSITY MATRICES
# ============================================================================

def demonstrate_density_matrix_expectation() -> None:
    """
    For a density matrix:
        <A> = Tr(rho A)
    """
    print_header("66. Expectation values with density matrices")

    rho: Matrix = [
        [0.75 + 0j, 0.0 + 0j],
        [0.0 + 0j, 0.25 + 0j],
    ]

    sigma_z: Matrix = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, -1.0 + 0j],
    ]

    rho_a = matrix_multiply(rho, sigma_z)
    expectation = matrix_trace(rho_a)

    print(f"Tr(rho): {matrix_trace(rho).real:.4f}")
    print(f"Tr(rho*sigma_z): {expectation.real:.4f}")

    print(
        "\nThe density-matrix formalism unifies pure states, statistical "
        "mixtures, subsystem states, and noisy quantum systems."
    )


# ============================================================================
# 67. ENTROPY
# ============================================================================

def von_neumann_entropy_from_probabilities(
    probabilities: Sequence[float],
) -> float:
    """
    Calculate Shannon entropy for a diagonal density matrix.

    For eigenvalues lambda_i:
        S = -sum_i lambda_i log2(lambda_i)

    For a diagonal density matrix this equals the von Neumann entropy.
    """
    entropy = 0.0

    for probability in probabilities:
        if probability < 0:
            raise ValueError("Probabilities cannot be negative.")
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy


def demonstrate_quantum_entropy() -> None:
    """Demonstrate entropy of pure and maximally mixed qubit states."""
    print_header("67. Quantum entropy")

    pure_entropy = von_neumann_entropy_from_probabilities([1.0, 0.0])
    mixed_entropy = von_neumann_entropy_from_probabilities([0.5, 0.5])

    print(f"Pure qubit entropy: {pure_entropy:.4f} bits")
    print(f"Maximally mixed qubit entropy: {mixed_entropy:.4f} bits")

    print(
        "\nVon Neumann entropy quantifies mixedness and uncertainty in a "
        "quantum state. It is zero for a pure state and reaches log2(d) "
        "for a maximally mixed state in a d-dimensional Hilbert space."
    )


# ============================================================================
# 68. QUANTUM VERSUS CLASSICAL INFORMATION
# ============================================================================

def demonstrate_quantum_information_concepts() -> None:
    """Introduce basic quantum-information terminology."""
    print_header("68. Quantum information terminology")

    concepts = {
        "Qubit": "A two-dimensional quantum information carrier.",
        "Superposition": "A linear combination of basis states.",
        "Entanglement": "Non-separable structure in a composite quantum state.",
        "Coherence": "Phase relationships between quantum amplitudes.",
        "Decoherence": "Loss of accessible coherence through environmental interaction.",
        "Measurement": "A physical process described by a specified quantum measurement model.",
        "Unitary": "A norm-preserving reversible transformation.",
        "Density matrix": "An operator describing pure or mixed quantum states.",
        "POVM": "A generalized measurement described by positive operators summing to identity.",
    }

    for name, definition in concepts.items():
        print(f"{name}: {definition}")


# ============================================================================
# 69. PRACTICAL APPLICATIONS
# ============================================================================

def demonstrate_applications() -> None:
    """List major real-world areas where quantum mechanics is essential."""
    print_header("69. Applications of quantum mechanics")

    applications = [
        "Atomic and molecular spectroscopy",
        "Lasers",
        "Semiconductor electronics",
        "Transistors",
        "LEDs",
        "Solar cells",
        "Magnetic resonance techniques",
        "Electron microscopy",
        "Scanning tunneling microscopy",
        "Nuclear magnetic resonance",
        "Nuclear energy and radioactive decay",
        "Quantum sensors",
        "Quantum communication",
        "Quantum information processing",
        "Superconducting systems",
        "Condensed-matter physics",
        "Materials science",
        "Nanotechnology",
    ]

    for application in applications:
        print(f"- {application}")

    print(
        "\nQuantum mechanics is not restricted to microscopic thought "
        "experiments. Modern electronic, optical, and materials technologies "
        "depend heavily on quantum phenomena."
    )


# ============================================================================
# 70. BEST PRACTICES FOR SOLVING BASIC QUANTUM PROBLEMS
# ============================================================================

def demonstrate_problem_solving_workflow() -> None:
    """Provide a practical workflow for solving introductory problems."""
    print_header("70. Problem-solving workflow")

    steps = [
        "Define the physical system and its assumptions.",
        "Identify the relevant degrees of freedom.",
        "Choose an appropriate representation or basis.",
        "Write the Hamiltonian or relevant observable.",
        "Check units and physical parameter ranges.",
        "Normalize the state when required.",
        "Solve analytically when an exact solution is available.",
        "Use an approximation only after identifying why it is valid.",
        "Calculate probabilities using the Born rule.",
        "Check limiting cases and conservation laws.",
        "Compare numerical results against known physical scales.",
        "Interpret the mathematical result physically.",
    ]

    for number, step in enumerate(steps, start=1):
        print(f"{number:2d}. {step}")


# ============================================================================
# 71. EDGE CASES AND LIMITATIONS
# ============================================================================

def demonstrate_limitations_and_edge_cases() -> None:
    """Demonstrate important boundaries of the examples in this script."""
    print_header("71. Edge cases and limitations")

    limitations = [
        (
            "Infinite-well model",
            "An idealized potential with infinitely high walls. Real "
            "materials have finite barriers."
        ),
        (
            "Gaussian wave packet",
            "The numerical representation uses finite integration limits "
            "and therefore approximates the infinite domain."
        ),
        (
            "Tunneling formula",
            "The exponential transmission expression is an approximation "
            "and does not replace exact scattering calculations in general."
        ),
        (
            "Hydrogen energy formula",
            "The simple -13.6 eV/n^2 result neglects many corrections such "
            "as reduced mass, fine structure, Lamb shifts, and external fields."
        ),
        (
            "Two-level qubit",
            "A two-dimensional model cannot represent every physical degree "
            "of freedom of a real particle."
        ),
        (
            "Numerical matrices",
            "Floating-point calculations introduce rounding and numerical "
            "conditioning issues."
        ),
    ]

    for model, limitation in limitations:
        print(f"\n{model}:")
        print(f"  {limitation}")


# ============================================================================
# 72. FINAL INTEGRATED DEMONSTRATION
# ============================================================================

def integrated_quantum_example() -> None:
    """
    Integrate state preparation, unitary evolution, measurement, and
    probability prediction in a small example.
    """
    print_header("72. Integrated quantum example")

    scale = 1.0 / math.sqrt(2.0)

    hadamard = [
        [scale + 0j, scale + 0j],
        [scale + 0j, -scale + 0j],
    ]

    phase_gate = [
        [1.0 + 0j, 0.0 + 0j],
        [0.0 + 0j, 1.0j],
    ]

    initial_state = [1.0 + 0j, 0.0 + 0j]

    state_after_h = apply_operator(hadamard, initial_state)
    state_after_phase = apply_operator(phase_gate, state_after_h)
    state_after_h2 = apply_operator(hadamard, state_after_phase)

    print("Initial state:")
    print([format_complex(x) for x in initial_state])

    print("\nAfter first H:")
    print([format_complex(x) for x in state_after_h])

    print("\nAfter phase gate:")
    print([format_complex(x) for x in state_after_phase])

    print("\nAfter second H:")
    print([format_complex(x) for x in state_after_h2])

    print(
        "\nFinal probabilities:",
        probability_amplitudes(state_after_h2),
    )

    print(
        "\nThis example illustrates a central quantum-information idea: "
        "unitary transformations manipulate amplitudes and relative phases, "
        "and a final measurement converts those amplitudes into observable "
        "probabilities."
    )


# ============================================================================
# 73. MAIN STUDY PROGRAM
# ============================================================================

def main() -> None:
    """
    Run the complete tutorial.

    The script is intentionally organized as a sequence of demonstrations.
    Each section can also be copied into a Python interpreter independently
    after importing or redefining the required functions.
    """

    demonstrate_classical_and_quantum_descriptions()
    demonstrate_quantization()
    demonstrate_wave_particle_duality()
    demonstrate_complex_amplitudes()
    demonstrate_superposition()
    demonstrate_interference()
    demonstrate_wavefunction()
    demonstrate_expectation_values()
    demonstrate_operators()
    demonstrate_eigenstate_measurement()
    demonstrate_hermitian_operator()
    demonstrate_position_momentum_operators()
    demonstrate_commutator()
    demonstrate_uncertainty_principle()
    demonstrate_schrodinger_equation()
    demonstrate_time_evolution()
    demonstrate_measurement_bases()
    demonstrate_spin_half()
    demonstrate_bra_ket_notation()
    demonstrate_density_matrix()
    demonstrate_pure_and_mixed_states()
    demonstrate_tensor_products()
    demonstrate_bell_state()
    demonstrate_born_rule()
    demonstrate_infinite_well()
    demonstrate_quantum_numbers()
    demonstrate_hydrogen_levels()
    demonstrate_tunneling()
    demonstrate_harmonic_oscillator()
    demonstrate_zero_point_energy()
    demonstrate_bosons_and_fermions()
    demonstrate_pauli_exclusion()
    demonstrate_exchange_symmetry()
    demonstrate_relative_phase()
    demonstrate_classical_mixture_vs_superposition()
    demonstrate_decoherence()
    demonstrate_unitary_operator()
    demonstrate_basic_quantum_gates()
    demonstrate_no_cloning_theorem()
    demonstrate_quantum_teleportation_concept()
    demonstrate_quantum_zeno_effect()
    demonstrate_classical_limit()
    demonstrate_wave_packet_dispersion()
    demonstrate_perturbation_theory()
    demonstrate_variational_principle()
    demonstrate_numerical_considerations()
    demonstrate_physical_validation()
    demonstrate_common_mistakes()
    demonstrate_measurement_postulates()
    demonstrate_povm_concept()
    demonstrate_open_systems()
    demonstrate_symmetry_and_conservation()
    demonstrate_angular_momentum()
    demonstrate_hydrogen_probability_cloud()
    demonstrate_dimensions()
    demonstrate_nonrelativistic_limit()
    demonstrate_quantum_field_theory_context()
    demonstrate_small_quantum_simulator()
    demonstrate_statistical_predictions()
    demonstrate_energy_time_relation()
    demonstrate_measurement_disturbance()
    demonstrate_hilbert_space()
    demonstrate_orthonormal_basis()
    demonstrate_phase_invariance()
    demonstrate_completeness_relation()
    demonstrate_density_matrix_expectation()
    demonstrate_quantum_entropy()
    demonstrate_quantum_information_concepts()
    demonstrate_applications()
    demonstrate_problem_solving_workflow()
    demonstrate_limitations_and_edge_cases()
    integrated_quantum_example()

    print_header("End of quantum mechanics study script")
    print(
        "The script covered the mathematical and physical vocabulary needed "
        "to begin studying quantum mechanics systematically."
    )


if __name__ == "__main__":
    main()
