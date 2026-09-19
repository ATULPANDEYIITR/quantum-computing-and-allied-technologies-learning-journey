/*
 * Time Evolution and Schrödinger Equation Concepts
 * =================================================
 *
 * C++17 case study:
 *
 *     One-dimensional quantum wave-packet laboratory
 *
 * The program models a particle initially represented by a Gaussian wave
 * packet and evolves it in several physical environments. The implementation
 * demonstrates:
 *
 *   - complex-valued quantum states
 *   - discretized position space
 *   - finite-difference derivatives
 *   - the Hamiltonian operator
 *   - the time-dependent Schrödinger equation
 *   - fourth-order Runge-Kutta propagation
 *   - probability normalization
 *   - expectation values
 *   - potential barriers
 *   - energy diagnostics
 *   - measurement sampling
 *   - stationary-state comparison
 *   - validation and numerical error handling
 *
 * Compile:
 *
 *     g++ -std=c++17 -O2 schrodinger_time_evolution.cpp -o schrodinger
 *
 * Run:
 *
 *     ./schrodinger
 */

#include <algorithm>
#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace quantum {

using Complex = std::complex<double>;
using Wavefunction = std::vector<Complex>;
using PotentialFunction = double (*)(double);

constexpr double HBAR = 1.0;
constexpr double MASS = 1.0;
constexpr double EPSILON = 1e-12;
constexpr double PI = 3.141592653589793238462643383279502884;

// ---------------------------------------------------------------------------
// Basic numerical utilities
// ---------------------------------------------------------------------------

void printSection(const std::string& title) {
    std::cout << "\n" << std::string(78, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(78, '=') << "\n";
}

std::vector<double> createGrid(
    double start,
    double end,
    std::size_t count
) {
    if (count < 2) {
        throw std::invalid_argument(
            "A numerical grid needs at least two points."
        );
    }

    std::vector<double> grid(count);
    const double dx = (end - start) /
                      static_cast<double>(count - 1);

    for (std::size_t i = 0; i < count; ++i) {
        grid[i] = start + static_cast<double>(i) * dx;
    }

    return grid;
}

double trapezoidalIntegral(
    const std::vector<double>& values,
    double dx
) {
    if (values.size() < 2) {
        return 0.0;
    }

    double total =
        0.5 * values.front() +
        0.5 * values.back();

    for (std::size_t i = 1; i + 1 < values.size(); ++i) {
        total += values[i];
    }

    return total * dx;
}

// ---------------------------------------------------------------------------
// Wavefunction construction and normalization
// ---------------------------------------------------------------------------

Wavefunction normalize(
    const Wavefunction& state,
    double dx
) {
    std::vector<double> density;
    density.reserve(state.size());

    for (const Complex& value : state) {
        density.push_back(std::norm(value));
    }

    const double normSquared =
        trapezoidalIntegral(density, dx);

    if (normSquared <= EPSILON) {
        throw std::invalid_argument(
            "Cannot normalize a zero wavefunction."
        );
    }

    const double factor =
        1.0 / std::sqrt(normSquared);

    Wavefunction result = state;

    for (Complex& value : result) {
        value *= factor;
    }

    return result;
}

Wavefunction gaussianWavePacket(
    const std::vector<double>& x,
    double center,
    double width,
    double momentum
) {
    if (width <= 0.0) {
        throw std::invalid_argument(
            "Gaussian width must be positive."
        );
    }

    Wavefunction state;
    state.reserve(x.size());

    for (double position : x) {
        const double envelope =
            std::exp(
                -std::pow(position - center, 2) /
                (4.0 * width * width)
            );

        const Complex phase =
            std::exp(
                Complex(
                    0.0,
                    momentum * position / HBAR
                )
            );

        state.push_back(
            envelope * phase
        );
    }

    return normalize(
        state,
        x[1] - x[0]
    );
}

// ---------------------------------------------------------------------------
// Potentials
// ---------------------------------------------------------------------------

double freeParticle(double) {
    return 0.0;
}

double harmonicOscillator(double x) {
    const double omega = 1.0;
    return 0.5 * MASS * omega * omega * x * x;
}

struct BarrierParameters {
    double start;
    double end;
    double height;
};

BarrierParameters barrierParameters{
    -0.5,
    0.5,
    7.0
};

double finiteBarrier(double x) {
    if (
        x >= barrierParameters.start &&
        x <= barrierParameters.end
    ) {
        return barrierParameters.height;
    }

    return 0.0;
}

// ---------------------------------------------------------------------------
// Differential operators
// ---------------------------------------------------------------------------

Wavefunction firstDerivative(
    const Wavefunction& values,
    double dx
) {
    if (values.size() < 3) {
        throw std::invalid_argument(
            "At least three points are required."
        );
    }

    Wavefunction result(
        values.size(),
        Complex(0.0, 0.0)
    );

    result.front() =
        (values[1] - values[0]) / dx;

    result.back() =
        (values.back() - values[values.size() - 2]) /
        dx;

    for (std::size_t i = 1; i + 1 < values.size(); ++i) {
        result[i] =
            (values[i + 1] - values[i - 1]) /
            (2.0 * dx);
    }

    return result;
}

Wavefunction secondDerivative(
    const Wavefunction& values,
    double dx
) {
    if (values.size() < 3) {
        throw std::invalid_argument(
            "At least three points are required."
        );
    }

    Wavefunction result(
        values.size(),
        Complex(0.0, 0.0)
    );

    for (std::size_t i = 1; i + 1 < values.size(); ++i) {
        result[i] =
            (
                values[i + 1]
                - 2.0 * values[i]
                + values[i - 1]
            ) / (dx * dx);
    }

    // One-sided approximations at the two boundaries.
    result.front() =
        (
            values[2]
            - 2.0 * values[1]
            + values[0]
        ) / (dx * dx);

    const std::size_t last =
        values.size() - 1;

    result.back() =
        (
            values[last]
            - 2.0 * values[last - 1]
            + values[last - 2]
        ) / (dx * dx);

    return result;
}

// ---------------------------------------------------------------------------
// Hamiltonian
// ---------------------------------------------------------------------------

Wavefunction applyHamiltonian(
    const std::vector<double>& x,
    const Wavefunction& state,
    PotentialFunction potential
) {
    if (x.size() != state.size()) {
        throw std::invalid_argument(
            "Grid and wavefunction sizes must match."
        );
    }

    const double dx = x[1] - x[0];
    const Wavefunction curvature =
        secondDerivative(state, dx);

    Wavefunction result(state.size());

    for (std::size_t i = 0; i < state.size(); ++i) {
        const Complex kinetic =
            -(
                (HBAR * HBAR) /
                (2.0 * MASS)
            ) * curvature[i];

        const Complex potentialTerm =
            potential(x[i]) * state[i];

        result[i] =
            kinetic + potentialTerm;
    }

    return result;
}

// ---------------------------------------------------------------------------
// Observables
// ---------------------------------------------------------------------------

double totalProbability(
    const Wavefunction& state,
    double dx
) {
    std::vector<double> density;
    density.reserve(state.size());

    for (const Complex& value : state) {
        density.push_back(std::norm(value));
    }

    return trapezoidalIntegral(
        density,
        dx
    );
}

double expectationPosition(
    const std::vector<double>& x,
    const Wavefunction& state,
    double dx
) {
    std::vector<double> integrand;
    integrand.reserve(state.size());

    for (std::size_t i = 0; i < state.size(); ++i) {
        integrand.push_back(
            x[i] * std::norm(state[i])
        );
    }

    return trapezoidalIntegral(
        integrand,
        dx
    );
}

double expectationMomentum(
    const std::vector<double>& x,
    const Wavefunction& state,
    double dx
) {
    const Wavefunction derivative =
        firstDerivative(state, dx);

    std::vector<double> integrand;
    integrand.reserve(state.size());

    for (std::size_t i = 0; i < state.size(); ++i) {
        // p̂ψ = -iħ dψ/dx
        const Complex momentumPsi =
            Complex(0.0, -HBAR) *
            derivative[i];

        const Complex local =
            std::conj(state[i]) *
            momentumPsi;

        integrand.push_back(
            local.real()
        );
    }

    return trapezoidalIntegral(
        integrand,
        dx
    );
}

double expectationEnergy(
    const std::vector<double>& x,
    const Wavefunction& state,
    PotentialFunction potential
) {
    const double dx = x[1] - x[0];

    const Wavefunction hState =
        applyHamiltonian(
            x,
            state,
            potential
        );

    std::vector<double> integrand;
    integrand.reserve(state.size());

    for (std::size_t i = 0; i < state.size(); ++i) {
        integrand.push_back(
            (
                std::conj(state[i]) *
                hState[i]
            ).real()
        );
    }

    return trapezoidalIntegral(
        integrand,
        dx
    );
}

double expectationPotentialEnergy(
    const std::vector<double>& x,
    const Wavefunction& state,
    PotentialFunction potential,
    double dx
) {
    std::vector<double> integrand;
    integrand.reserve(state.size());

    for (std::size_t i = 0; i < state.size(); ++i) {
        integrand.push_back(
            potential(x[i]) *
            std::norm(state[i])
        );
    }

    return trapezoidalIntegral(
        integrand,
        dx
    );
}

// ---------------------------------------------------------------------------
// Schrödinger equation
// ---------------------------------------------------------------------------

Wavefunction schrodingerRHS(
    const std::vector<double>& x,
    const Wavefunction& state,
    PotentialFunction potential
) {
    const Wavefunction hState =
        applyHamiltonian(
            x,
            state,
            potential
        );

    Wavefunction derivative(
        state.size()
    );

    // iħ dψ/dt = Hψ
    // dψ/dt = -(i/ħ) Hψ
    for (std::size_t i = 0; i < state.size(); ++i) {
        derivative[i] =
            Complex(0.0, -1.0 / HBAR) *
            hState[i];
    }

    return derivative;
}

Wavefunction addScaled(
    const Wavefunction& state,
    const Wavefunction& derivative,
    double scale
) {
    if (state.size() != derivative.size()) {
        throw std::invalid_argument(
            "Vector sizes must match."
        );
    }

    Wavefunction result(state.size());

    for (std::size_t i = 0; i < state.size(); ++i) {
        result[i] =
            state[i] +
            scale * derivative[i];
    }

    return result;
}

// ---------------------------------------------------------------------------
// RK4 integrator
// ---------------------------------------------------------------------------

Wavefunction rk4Step(
    const std::vector<double>& x,
    const Wavefunction& state,
    double dt,
    PotentialFunction potential
) {
    const Wavefunction k1 =
        schrodingerRHS(
            x,
            state,
            potential
        );

    const Wavefunction state2 =
        addScaled(
            state,
            k1,
            dt / 2.0
        );

    const Wavefunction k2 =
        schrodingerRHS(
            x,
            state2,
            potential
        );

    const Wavefunction state3 =
        addScaled(
            state,
            k2,
            dt / 2.0
        );

    const Wavefunction k3 =
        schrodingerRHS(
            x,
            state3,
            potential
        );

    const Wavefunction state4 =
        addScaled(
            state,
            k3,
            dt
        );

    const Wavefunction k4 =
        schrodingerRHS(
            x,
            state4,
            potential
        );

    Wavefunction result(state.size());

    for (std::size_t i = 0; i < state.size(); ++i) {
        result[i] =
            state[i]
            + (dt / 6.0) *
                (
                    k1[i]
                    + 2.0 * k2[i]
                    + 2.0 * k3[i]
                    + k4[i]
                );
    }

    return result;
}

// ---------------------------------------------------------------------------
// Hard-wall boundary conditions
// ---------------------------------------------------------------------------

void applyHardWallBoundaries(
    Wavefunction& state
) {
    if (state.size() >= 2) {
        state.front() = Complex(0.0, 0.0);
        state.back() = Complex(0.0, 0.0);
    }
}

// ---------------------------------------------------------------------------
// Measurement simulation
// ---------------------------------------------------------------------------

double samplePosition(
    const std::vector<double>& x,
    const Wavefunction& state,
    std::mt19937& generator
) {
    const double dx = x[1] - x[0];

    std::vector<double> weights;
    weights.reserve(state.size());

    double total = 0.0;

    for (const Complex& value : state) {
        const double weight =
            std::norm(value) * dx;

        weights.push_back(weight);
        total += weight;
    }

    if (total <= EPSILON) {
        throw std::runtime_error(
            "Cannot sample a zero-probability state."
        );
    }

    std::uniform_real_distribution<double> distribution(
        0.0,
        total
    );

    const double target =
        distribution(generator);

    double cumulative = 0.0;

    for (std::size_t i = 0; i < weights.size(); ++i) {
        cumulative += weights[i];

        if (cumulative >= target) {
            return x[i];
        }
    }

    return x.back();
}

// ---------------------------------------------------------------------------
// Infinite square well reference state
// ---------------------------------------------------------------------------

Wavefunction infiniteWellState(
    const std::vector<double>& x,
    double length,
    int quantumNumber
) {
    if (quantumNumber <= 0) {
        throw std::invalid_argument(
            "Quantum number must be positive."
        );
    }

    const double amplitude =
        std::sqrt(2.0 / length);

    Wavefunction state;
    state.reserve(x.size());

    for (double position : x) {
        state.emplace_back(
            amplitude *
            std::sin(
                quantumNumber *
                PI *
                position /
                length
            ),
            0.0
        );
    }

    return state;
}

double infiniteWellEnergy(
    int quantumNumber,
    double length
) {
    return (
        quantumNumber *
        quantumNumber *
        PI *
        PI *
        HBAR *
        HBAR
    ) / (
        2.0 *
        MASS *
        length *
        length
    );
}

Wavefunction evolveStationaryState(
    const Wavefunction& state,
    double energy,
    double time
) {
    const Complex phase =
        std::exp(
            Complex(
                0.0,
                -energy * time / HBAR
            )
        );

    Wavefunction result = state;

    for (Complex& value : result) {
        value *= phase;
    }

    return result;
}

// ---------------------------------------------------------------------------
// Probability on a selected spatial interval
// ---------------------------------------------------------------------------

double intervalProbability(
    const std::vector<double>& x,
    const Wavefunction& state,
    double left,
    double right
) {
    const double dx = x[1] - x[0];

    std::vector<double> values(
        x.size(),
        0.0
    );

    for (std::size_t i = 0; i < x.size(); ++i) {
        if (x[i] >= left && x[i] <= right) {
            values[i] = std::norm(state[i]);
        }
    }

    return trapezoidalIntegral(
        values,
        dx
    );
}

// ---------------------------------------------------------------------------
// Case study
// ---------------------------------------------------------------------------

class QuantumWavePacketLab {
public:
    QuantumWavePacketLab(
        double minimum,
        double maximum,
        std::size_t gridPoints
    )
        : x_(createGrid(
              minimum,
              maximum,
              gridPoints
          )),
          dx_(x_[1] - x_[0]),
          state_(
              gaussianWavePacket(
                  x_,
                  -3.5,
                  0.7,
                  4.0
              )
          ) {}

    void printInitialDiagnostics() const {
        printSection(
            "Case study: initial quantum state"
        );

        std::cout
            << std::fixed
            << std::setprecision(8);

        std::cout
            << "Grid points: "
            << x_.size()
            << "\n";

        std::cout
            << "dx: "
            << dx_
            << "\n";

        std::cout
            << "Initial probability: "
            << totalProbability(
                   state_,
                   dx_
               )
            << "\n";

        std::cout
            << "Initial <x>: "
            << expectationPosition(
                   x_,
                   state_,
                   dx_
               )
            << "\n";

        std::cout
            << "Initial <p>: "
            << expectationMomentum(
                   x_,
                   state_,
                   dx_
               )
            << "\n";

        std::cout
            << "Initial free-particle energy: "
            << expectationEnergy(
                   x_,
                   state_,
                   freeParticle
               )
            << "\n";
    }

    void evolveFreeParticle(
        double dt,
        int steps,
        int reportEvery
    ) {
        printSection(
            "Free-particle time evolution"
        );

        for (int step = 0; step <= steps; ++step) {
            if (
                step % reportEvery == 0 ||
                step == steps
            ) {
                report(
                    step,
                    dt,
                    freeParticle
                );
            }

            if (step == steps) {
                break;
            }

            state_ =
                rk4Step(
                    x_,
                    state_,
                    dt,
                    freeParticle
                );

            applyHardWallBoundaries(
                state_
            );

            // Explicit normalization is a numerical safeguard. It should
            // not be confused with exact unitary time evolution.
            state_ =
                normalize(
                    state_,
                    dx_
                );
        }
    }

    void switchToBarrierState() {
        printSection(
            "Reinitialization for barrier experiment"
        );

        state_ =
            gaussianWavePacket(
                x_,
                -4.0,
                0.7,
                4.0
            );

        std::cout
            << "Barrier interval: ["
            << barrierParameters.start
            << ", "
            << barrierParameters.end
            << "]\n";

        std::cout
            << "Barrier height: "
            << barrierParameters.height
            << "\n";

        std::cout
            << "Initial energy estimate: "
            << expectationEnergy(
                   x_,
                   state_,
                   finiteBarrier
               )
            << "\n";
    }

    void evolveThroughBarrier(
        double dt,
        int steps,
        int reportEvery
    ) {
        printSection(
            "Barrier propagation and tunneling diagnostics"
        );

        for (int step = 0; step <= steps; ++step) {
            if (
                step % reportEvery == 0 ||
                step == steps
            ) {
                const double leftProbability =
                    intervalProbability(
                        x_,
                        state_,
                        x_.front(),
                        barrierParameters.start
                    );

                const double barrierProbability =
                    intervalProbability(
                        x_,
                        state_,
                        barrierParameters.start,
                        barrierParameters.end
                    );

                const double rightProbability =
                    intervalProbability(
                        x_,
                        state_,
                        barrierParameters.end,
                        x_.back()
                    );

                std::cout
                    << "step="
                    << std::setw(4)
                    << step
                    << ", t="
                    << std::setw(8)
                    << std::setprecision(5)
                    << step * dt
                    << ", left="
                    << std::setprecision(6)
                    << leftProbability
                    << ", barrier="
                    << barrierProbability
                    << ", right="
                    << rightProbability
                    << "\n";
            }

            if (step == steps) {
                break;
            }

            state_ =
                rk4Step(
                    x_,
                    state_,
                    dt,
                    finiteBarrier
                );

            applyHardWallBoundaries(
                state_
            );

            state_ =
                normalize(
                    state_,
                    dx_
                );
        }
    }

    void demonstrateMeasurementSampling(
        unsigned int seed
    ) const {
        printSection(
            "Position measurement simulation"
        );

        std::mt19937 generator(seed);

        std::cout
            << "Measured positions: ";

        for (int i = 0; i < 12; ++i) {
            std::cout
                << std::fixed
                << std::setprecision(3)
                << samplePosition(
                       x_,
                       state_,
                       generator
                   );

            if (i + 1 < 12) {
                std::cout << ", ";
            }
        }

        std::cout << "\n";
    }

    void demonstrateStationaryState() const {
        printSection(
            "Stationary-state reference calculation"
        );

        const double length = 10.0;
        const std::vector<double> wellGrid =
            createGrid(
                0.0,
                length,
                401
            );

        const int n = 3;

        const Wavefunction state =
            infiniteWellState(
                wellGrid,
                length,
                n
            );

        const double energy =
            infiniteWellEnergy(
                n,
                length
            );

        const Wavefunction evolved =
            evolveStationaryState(
                state,
                energy,
                2.5
            );

        const double initialProbability =
            totalProbability(
                state,
                wellGrid[1] - wellGrid[0]
            );

        const double evolvedProbability =
            totalProbability(
                evolved,
                wellGrid[1] - wellGrid[0]
            );

        double maximumDensityDifference = 0.0;

        for (std::size_t i = 0; i < state.size(); ++i) {
            maximumDensityDifference =
                std::max(
                    maximumDensityDifference,
                    std::abs(
                        std::norm(state[i])
                        - std::norm(evolved[i])
                    )
                );
        }

        std::cout
            << "n = "
            << n
            << "\n";

        std::cout
            << "E_n = "
            << energy
            << "\n";

        std::cout
            << "Initial probability = "
            << initialProbability
            << "\n";

        std::cout
            << "Evolved probability = "
            << evolvedProbability
            << "\n";

        std::cout
            << "Maximum probability-density change = "
            << maximumDensityDifference
            << "\n";
    }

private:
    void report(
        int step,
        double dt,
        PotentialFunction potential
    ) const {
        const double probability =
            totalProbability(
                state_,
                dx_
            );

        const double position =
            expectationPosition(
                x_,
                state_,
                dx_
            );

        const double momentum =
            expectationMomentum(
                x_,
                state_,
                dx_
            );

        const double energy =
            expectationEnergy(
                x_,
                state_,
                potential
            );

        std::cout
            << "step="
            << std::setw(4)
            << step
            << ", t="
            << std::setw(8)
            << std::setprecision(5)
            << step * dt
            << ", <x>="
            << std::setw(10)
            << std::setprecision(6)
            << position
            << ", <p>="
            << std::setw(10)
            << momentum
            << ", P="
            << probability
            << ", <H>="
            << energy
            << "\n";
    }

    std::vector<double> x_;
    double dx_;
    Wavefunction state_;
};

// ---------------------------------------------------------------------------
// Validation tests
// ---------------------------------------------------------------------------

void runValidationTests() {
    printSection(
        "Numerical validation checks"
    );

    const std::vector<double> x =
        createGrid(
            -8.0,
            8.0,
            401
        );

    const double dx =
        x[1] - x[0];

    const Wavefunction state =
        gaussianWavePacket(
            x,
            0.0,
            1.0,
            0.0
        );

    const double probability =
        totalProbability(
            state,
            dx
        );

    std::cout
        << std::setprecision(12)
        << "Normalization error: "
        << std::abs(
               probability - 1.0
           )
        << "\n";

    if (
        std::abs(
            probability - 1.0
        ) > 1e-8
    ) {
        throw std::runtime_error(
            "Normalization validation failed."
        );
    }

    const double energy =
        expectationEnergy(
            x,
            state,
            freeParticle
        );

    std::cout
        << "Zero-momentum Gaussian energy estimate: "
        << energy
        << "\n";

    if (!std::isfinite(energy)) {
        throw std::runtime_error(
            "Energy validation produced a non-finite value."
        );
    }

    std::cout
        << "Validation checks passed.\n";
}

} // namespace quantum

// ---------------------------------------------------------------------------
// Program entry point
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "TIME EVOLUTION AND SCHRODINGER EQUATION CONCEPTS\n";

        std::cout
            << "One-dimensional quantum wave-packet case study\n";

        std::cout
            << "Using dimensionless units hbar = 1 and m = 1\n";

        quantum::runValidationTests();

        quantum::QuantumWavePacketLab laboratory(
            -10.0,
            10.0,
            301
        );

        laboratory.printInitialDiagnostics();

        laboratory.evolveFreeParticle(
            0.0006,
            80,
            20
        );

        laboratory.switchToBarrierState();

        laboratory.evolveThroughBarrier(
            0.0005,
            60,
            15
        );

        laboratory.demonstrateMeasurementSampling(
            20260919
        );

        laboratory.demonstrateStationaryState();

        quantum::printSection(
            "Design and performance notes"
        );

        std::cout
            << "The wavefunction is stored as a contiguous vector of "
            << "std::complex<double> values.\n";

        std::cout
            << "Finite differences require O(N) work per Hamiltonian "
            << "application for a one-dimensional local potential.\n";

        std::cout
            << "A single RK4 step requires four Hamiltonian evaluations, "
            << "so its spatial work is O(N) for this discretization.\n";

        std::cout
            << "The time-step and spatial-grid choices are coupled: "
            << "a finer grid resolves shorter wavelengths but can impose "
            << "a stricter stability and accuracy requirement on explicit "
            << "time integration.\n";

        std::cout
            << "Production-scale simulations commonly replace the simple "
            << "explicit integrator with methods designed to preserve "
            << "unitarity or use sparse matrix, Krylov, Crank-Nicolson, "
            << "or split-operator techniques.\n";

        std::cout
            << "Completed successfully.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
