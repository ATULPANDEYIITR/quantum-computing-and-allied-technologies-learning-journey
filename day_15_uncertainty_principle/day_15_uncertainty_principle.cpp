/*
 * Quantum Uncertainty and the Heisenberg Uncertainty Principle
 * ===============================================================
 *
 * C++17 technical case study:
 *
 * A numerical laboratory for a one-dimensional quantum particle.
 *
 * The program models:
 *   1. A normalized Gaussian wave packet.
 *   2. Position expectation and variance.
 *   3. Momentum using the differential operator.
 *   4. The canonical commutator [x,p] = i*hbar.
 *   5. The Heisenberg uncertainty product.
 *   6. Free-particle wave-packet spreading.
 *   7. A simple measurement experiment.
 *   8. Numerical convergence as grid resolution changes.
 *
 * No external libraries are required.
 *
 * Compile:
 *   g++ -std=c++17 -O2 quantum_uncertainty.cpp -o quantum_uncertainty
 */

#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Complex = std::complex<double>;
using RealVector = std::vector<double>;
using ComplexVector = std::vector<Complex>;

constexpr double PI = 3.1415926535897932384626433832795;
constexpr double HBAR = 1.0;

// -----------------------------------------------------------------------------
// 1. Basic numerical utilities
// -----------------------------------------------------------------------------

double mean(const RealVector& values) {
    if (values.empty()) {
        throw std::invalid_argument("mean requires non-empty data");
    }

    double sum = 0.0;

    for (double value : values) {
        sum += value;
    }

    return sum / static_cast<double>(values.size());
}

double variance(const RealVector& values) {
    if (values.empty()) {
        throw std::invalid_argument(
            "variance requires non-empty data"
        );
    }

    const double average = mean(values);
    double total = 0.0;

    for (double value : values) {
        const double difference = value - average;
        total += difference * difference;
    }

    return total / static_cast<double>(values.size());
}

double standardDeviation(const RealVector& values) {
    return std::sqrt(variance(values));
}


// -----------------------------------------------------------------------------
// 2. Numerical grid
// -----------------------------------------------------------------------------

struct Grid {
    RealVector x;
    double dx;
};

Grid createGrid(
    double minimum,
    double maximum,
    std::size_t numberOfPoints
) {
    if (numberOfPoints < 2) {
        throw std::invalid_argument(
            "A grid requires at least two points"
        );
    }

    if (!(maximum > minimum)) {
        throw std::invalid_argument(
            "Maximum grid coordinate must exceed minimum"
        );
    }

    Grid grid;
    grid.x.resize(numberOfPoints);

    grid.dx =
        (maximum - minimum) /
        static_cast<double>(numberOfPoints - 1);

    for (std::size_t i = 0; i < numberOfPoints; ++i) {
        grid.x[i] =
            minimum +
            static_cast<double>(i) * grid.dx;
    }

    return grid;
}


// -----------------------------------------------------------------------------
// 3. Trapezoidal numerical integration
// -----------------------------------------------------------------------------

double integrate(
    const RealVector& x,
    const RealVector& values
) {
    if (x.size() != values.size()) {
        throw std::invalid_argument(
            "Integration arrays must have equal lengths"
        );
    }

    if (x.size() < 2) {
        throw std::invalid_argument(
            "Integration requires at least two points"
        );
    }

    double total = 0.0;

    for (std::size_t i = 0; i + 1 < x.size(); ++i) {
        const double dx = x[i + 1] - x[i];

        total +=
            0.5 *
            (values[i] + values[i + 1]) *
            dx;
    }

    return total;
}


// -----------------------------------------------------------------------------
// 4. Gaussian quantum state
// -----------------------------------------------------------------------------

struct GaussianPacket {
    double center;
    double sigmaX;
    double meanMomentum;
    double hbar;

    Complex evaluate(double x) const {
        if (!(sigmaX > 0.0)) {
            throw std::invalid_argument(
                "Gaussian width must be positive"
            );
        }

        /*
         * The probability density has the form
         *
         * |psi(x)|^2 =
         *   1/(sqrt(2*pi)*sigma)
         *   exp(-(x-x0)^2/(2*sigma^2))
         *
         * Therefore the position standard deviation is sigmaX.
         */
        const double normalization =
            std::pow(
                1.0 /
                (2.0 * PI * sigmaX * sigmaX),
                0.25
            );

        const double displacement =
            x - center;

        const double envelope =
            normalization *
            std::exp(
                -(displacement * displacement) /
                (4.0 * sigmaX * sigmaX)
            );

        const double phase =
            meanMomentum * x / hbar;

        return Complex(
            envelope * std::cos(phase),
            envelope * std::sin(phase)
        );
    }

    double analyticalMomentumUncertainty() const {
        return hbar / (2.0 * sigmaX);
    }
};


// -----------------------------------------------------------------------------
// 5. Wavefunction normalization
// -----------------------------------------------------------------------------

double normSquared(
    const Grid& grid,
    const ComplexVector& wavefunction
) {
    if (grid.x.size() != wavefunction.size()) {
        throw std::invalid_argument(
            "Grid and wavefunction must have equal lengths"
        );
    }

    RealVector probabilityDensity;
    probabilityDensity.reserve(wavefunction.size());

    for (const Complex& psi : wavefunction) {
        probabilityDensity.push_back(
            std::norm(psi)
        );
    }

    return integrate(
        grid.x,
        probabilityDensity
    );
}

void normalize(
    const Grid& grid,
    ComplexVector& wavefunction
) {
    const double norm = normSquared(
        grid,
        wavefunction
    );

    if (!(norm > 0.0) ||
        !std::isfinite(norm)) {
        throw std::runtime_error(
            "Wavefunction cannot be normalized"
        );
    }

    const double scale =
        1.0 / std::sqrt(norm);

    for (Complex& psi : wavefunction) {
        psi *= scale;
    }
}


// -----------------------------------------------------------------------------
// 6. Construct a wavefunction on a grid
// -----------------------------------------------------------------------------

ComplexVector buildWavefunction(
    const Grid& grid,
    const GaussianPacket& packet
) {
    ComplexVector wavefunction;
    wavefunction.reserve(grid.x.size());

    for (double x : grid.x) {
        wavefunction.push_back(
            packet.evaluate(x)
        );
    }

    normalize(
        grid,
        wavefunction
    );

    return wavefunction;
}


// -----------------------------------------------------------------------------
// 7. Position statistics
// -----------------------------------------------------------------------------

double expectationPosition(
    const Grid& grid,
    const ComplexVector& wavefunction
) {
    RealVector integrand;
    integrand.reserve(grid.x.size());

    for (std::size_t i = 0; i < grid.x.size(); ++i) {
        integrand.push_back(
            grid.x[i] *
            std::norm(wavefunction[i])
        );
    }

    return integrate(
        grid.x,
        integrand
    );
}

double expectationPositionSquared(
    const Grid& grid,
    const ComplexVector& wavefunction
) {
    RealVector integrand;
    integrand.reserve(grid.x.size());

    for (std::size_t i = 0; i < grid.x.size(); ++i) {
        const double x = grid.x[i];

        integrand.push_back(
            x * x *
            std::norm(wavefunction[i])
        );
    }

    return integrate(
        grid.x,
        integrand
    );
}

double positionUncertainty(
    const Grid& grid,
    const ComplexVector& wavefunction
) {
    const double meanX =
        expectationPosition(
            grid,
            wavefunction
        );

    const double meanXSquared =
        expectationPositionSquared(
            grid,
            wavefunction
        );

    const double rawVariance =
        meanXSquared -
        meanX * meanX;

    /*
     * Floating-point subtraction can create a tiny negative variance even
     * when the mathematical value is zero or positive. A negative result
     * larger than numerical tolerance indicates a real implementation issue.
     */
    if (rawVariance < 0.0 &&
        std::abs(rawVariance) < 1e-12) {
        return 0.0;
    }

    if (rawVariance < 0.0) {
        throw std::runtime_error(
            "Significantly negative position variance"
        );
    }

    return std::sqrt(rawVariance);
}


// -----------------------------------------------------------------------------
// 8. Finite-difference derivatives
// -----------------------------------------------------------------------------

ComplexVector firstDerivative(
    const Grid& grid,
    const ComplexVector& values
) {
    if (values.size() != grid.x.size()) {
        throw std::invalid_argument(
            "Derivative input has wrong size"
        );
    }

    if (values.size() < 3) {
        throw std::invalid_argument(
            "At least three points are required"
        );
    }

    ComplexVector derivative(values.size());

    /*
     * Interior:
     *
     * f'(x) ~= [f(x+dx)-f(x-dx)]/(2dx)
     *
     * This is second-order accurate in dx.
     *
     * One-sided differences are used at boundaries because no points exist
     * beyond the domain.
     */
    derivative[0] =
        (values[1] - values[0]) /
        grid.dx;

    derivative.back() =
        (values.back() - values[values.size() - 2]) /
        grid.dx;

    for (std::size_t i = 1;
         i + 1 < values.size();
         ++i) {
        derivative[i] =
            (values[i + 1] - values[i - 1]) /
            (2.0 * grid.dx);
    }

    return derivative;
}

ComplexVector secondDerivative(
    const Grid& grid,
    const ComplexVector& values
) {
    ComplexVector first =
        firstDerivative(
            grid,
            values
        );

    return firstDerivative(
        grid,
        first
    );
}


// -----------------------------------------------------------------------------
// 9. Momentum operator
// -----------------------------------------------------------------------------

ComplexVector applyMomentum(
    const Grid& grid,
    const ComplexVector& wavefunction,
    double hbar
) {
    /*
     * In position representation:
     *
     * p_hat = -i*hbar*d/dx
     *
     * Multiplication by -i is equivalent to rotating a complex number:
     *
     * (a + ib)(-i) = b - ia.
     */
    ComplexVector derivative =
        firstDerivative(
            grid,
            wavefunction
        );

    ComplexVector result(
        derivative.size()
    );

    for (std::size_t i = 0;
         i < derivative.size();
         ++i) {
        result[i] =
            Complex(
                derivative[i].imag() * hbar,
                -derivative[i].real() * hbar
            );
    }

    return result;
}


// -----------------------------------------------------------------------------
// 10. Inner product
// -----------------------------------------------------------------------------

double realInnerProduct(
    const Grid& grid,
    const ComplexVector& left,
    const ComplexVector& right
) {
    if (left.size() != right.size() ||
        left.size() != grid.x.size()) {
        throw std::invalid_argument(
            "Inner-product vectors have incompatible sizes"
        );
    }

    RealVector integrand;
    integrand.reserve(left.size());

    for (std::size_t i = 0;
         i < left.size();
         ++i) {
        integrand.push_back(
            (std::conj(left[i]) * right[i]).real()
        );
    }

    return integrate(
        grid.x,
        integrand
    );
}


// -----------------------------------------------------------------------------
// 11. Momentum statistics
// -----------------------------------------------------------------------------

struct MomentumStatistics {
    double mean;
    double meanSquared;
    double uncertainty;
};

MomentumStatistics calculateMomentumStatistics(
    const Grid& grid,
    const ComplexVector& wavefunction,
    double hbar
) {
    const ComplexVector momentumState =
        applyMomentum(
            grid,
            wavefunction,
            hbar
        );

    const ComplexVector secondDerivative =
        secondDerivative(
            grid,
            wavefunction
        );

    /*
     * p^2 = -hbar^2 d^2/dx^2
     */
    ComplexVector momentumSquaredState(
        secondDerivative.size()
    );

    for (std::size_t i = 0;
         i < secondDerivative.size();
         ++i) {
        momentumSquaredState[i] =
            -hbar * hbar *
            secondDerivative[i];
    }

    const double meanP =
        realInnerProduct(
            grid,
            wavefunction,
            momentumState
        );

    const double meanPSquared =
        realInnerProduct(
            grid,
            wavefunction,
            momentumSquaredState
        );

    const double rawVariance =
        meanPSquared -
        meanP * meanP;

    if (rawVariance < 0.0 &&
        std::abs(rawVariance) < 1e-10) {
        return {
            meanP,
            meanPSquared,
            0.0
        };
    }

    if (rawVariance < 0.0) {
        throw std::runtime_error(
            "Significantly negative momentum variance"
        );
    }

    return {
        meanP,
        meanPSquared,
        std::sqrt(rawVariance)
    };
}


// -----------------------------------------------------------------------------
// 12. Position operator
// -----------------------------------------------------------------------------

ComplexVector applyPosition(
    const Grid& grid,
    const ComplexVector& wavefunction
) {
    ComplexVector result(
        wavefunction.size()
    );

    for (std::size_t i = 0;
         i < wavefunction.size();
         ++i) {
        result[i] =
            grid.x[i] *
            wavefunction[i];
    }

    return result;
}


// -----------------------------------------------------------------------------
// 13. Commutator [x,p]
// -----------------------------------------------------------------------------

ComplexVector applyXP(
    const Grid& grid,
    const ComplexVector& state
) {
    return applyMomentum(
        grid,
        applyPosition(
            grid,
            state
        ),
        HBAR
    );
}

ComplexVector applyPX(
    const Grid& grid,
    const ComplexVector& state
) {
    return applyPosition(
        grid,
        applyMomentum(
            grid,
            state,
            HBAR
        )
    );
}

ComplexVector calculateCommutator(
    const Grid& grid,
    const ComplexVector& state
) {
    const ComplexVector xp =
        applyXP(
            grid,
            state
        );

    const ComplexVector px =
        applyPX(
            grid,
            state
        );

    ComplexVector result(
        state.size()
    );

    for (std::size_t i = 0;
         i < state.size();
         ++i) {
        result[i] =
            xp[i] - px[i];
    }

    return result;
}


// -----------------------------------------------------------------------------
// 14. Commutator error measurement
// -----------------------------------------------------------------------------

double commutatorError(
    const Grid& grid,
    const ComplexVector& state
) {
    const ComplexVector actual =
        calculateCommutator(
            grid,
            state
        );

    double maximumError = 0.0;

    /*
     * Boundary derivatives use a different stencil, so only interior
     * points are used for this consistency check.
     */
    for (std::size_t i = 5;
         i + 5 < state.size();
         ++i) {
        const Complex expected =
            Complex(0.0, HBAR) *
            state[i];

        maximumError =
            std::max(
                maximumError,
                std::abs(
                    actual[i] - expected
                )
            );
    }

    return maximumError;
}


// -----------------------------------------------------------------------------
// 15. Free-particle spreading
// -----------------------------------------------------------------------------

double freeParticleWidth(
    double initialSigma,
    double time,
    double mass,
    double hbar
) {
    if (!(initialSigma > 0.0)) {
        throw std::invalid_argument(
            "Initial width must be positive"
        );
    }

    if (!(mass > 0.0)) {
        throw std::invalid_argument(
            "Mass must be positive"
        );
    }

    const double factor =
        hbar * time /
        (2.0 * mass * initialSigma * initialSigma);

    return initialSigma *
        std::sqrt(
            1.0 + factor * factor
        );
}


// -----------------------------------------------------------------------------
// 16. Measurement simulation
// -----------------------------------------------------------------------------

struct MeasurementStatistics {
    double empiricalMean;
    double empiricalSigma;
};

MeasurementStatistics simulateTwoOutcomeMeasurement(
    double probabilityPositive,
    std::size_t numberOfMeasurements,
    unsigned seed
) {
    if (probabilityPositive < 0.0 ||
        probabilityPositive > 1.0) {
        throw std::invalid_argument(
            "Probability must lie between zero and one"
        );
    }

    if (numberOfMeasurements == 0) {
        throw std::invalid_argument(
            "Number of measurements must be positive"
        );
    }

    std::mt19937 generator(seed);

    std::bernoulli_distribution distribution(
        probabilityPositive
    );

    RealVector results;
    results.reserve(numberOfMeasurements);

    for (std::size_t i = 0;
         i < numberOfMeasurements;
         ++i) {
        /*
         * The observable is represented here by two possible outcomes:
         * -1 and +1.
         */
        results.push_back(
            distribution(generator)
                ? 1.0
                : -1.0
        );
    }

    return {
        mean(results),
        standardDeviation(results)
    };
}


// -----------------------------------------------------------------------------
// 17. Resolution convergence study
// -----------------------------------------------------------------------------

void convergenceStudy() {
    std::cout
        << "\nConvergence study\n"
        << "-----------------\n";

    const std::vector<std::size_t> resolutions = {
        201,
        401,
        801,
        1601
    };

    GaussianPacket packet{
        0.5,
        1.0,
        2.0,
        1.0
    };

    for (std::size_t numberOfPoints : resolutions) {
        const Grid grid =
            createGrid(
                -8.0,
                8.0,
                numberOfPoints
            );

        const ComplexVector state =
            buildWavefunction(
                grid,
                packet
            );

        const double sigmaX =
            positionUncertainty(
                grid,
                state
            );

        const MomentumStatistics momentum =
            calculateMomentumStatistics(
                grid,
                state,
                HBAR
            );

        const double product =
            sigmaX *
            momentum.uncertainty;

        std::cout
            << "N=" << std::setw(4)
            << numberOfPoints
            << "  dx="
            << std::scientific
            << std::setprecision(3)
            << grid.dx
            << "  Delta x="
            << std::fixed
            << std::setprecision(6)
            << sigmaX
            << "  Delta p="
            << momentum.uncertainty
            << "  product="
            << product
            << "\n";
    }

    std::cout << std::defaultfloat;
}


// -----------------------------------------------------------------------------
// 18. Validation helper
// -----------------------------------------------------------------------------

void requireNear(
    const std::string& name,
    double actual,
    double expected,
    double tolerance
) {
    if (std::abs(actual - expected) > tolerance) {
        throw std::runtime_error(
            name +
            " failed: actual=" +
            std::to_string(actual) +
            ", expected=" +
            std::to_string(expected)
        );
    }
}


// -----------------------------------------------------------------------------
// 19. Main technical case study
// -----------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "Quantum Uncertainty Technical Case Study\n"
            << "============================================================\n";

        /*
         * Scenario:
         *
         * A one-dimensional quantum particle is prepared as a localized
         * Gaussian wave packet. We want to determine:
         *
         *   - where the particle is statistically concentrated,
         *   - how broad its momentum distribution is,
         *   - whether the uncertainty product respects hbar/2,
         *   - whether the numerical position and momentum operators
         *     reproduce their canonical commutator,
         *   - and how the packet spreads during free evolution.
         *
         * Dimensionless units are used in the numerical grid:
         *
         *   hbar = 1
         *
         * This avoids unnecessary underflow/rounding problems while
         * preserving the mathematical structure of the quantum problem.
         */

        const Grid grid =
            createGrid(
                -10.0,
                10.0,
                1601
            );

        GaussianPacket packet{
            0.75,     // initial center
            1.20,     // position standard deviation
            2.50,     // average momentum
            HBAR
        };

        ComplexVector state =
            buildWavefunction(
                grid,
                packet
            );

        std::cout
            << "\n1. State preparation\n"
            << "--------------------\n";

        std::cout
            << "Grid points: "
            << grid.x.size()
            << "\n";

        std::cout
            << "Grid spacing: "
            << grid.dx
            << "\n";

        std::cout
            << "Numerical norm: "
            << normSquared(
                grid,
                state
            )
            << "\n";

        const double meanX =
            expectationPosition(
                grid,
                state
            );

        const double sigmaX =
            positionUncertainty(
                grid,
                state
            );

        std::cout
            << "\n2. Position statistics\n"
            << "----------------------\n";

        std::cout
            << "Expected <x>: "
            << meanX
            << "\n";

        std::cout
            << "Expected analytical center: "
            << packet.center
            << "\n";

        std::cout
            << "Numerical Delta x: "
            << sigmaX
            << "\n";

        std::cout
            << "Analytical Delta x: "
            << packet.sigmaX
            << "\n";

        const MomentumStatistics momentum =
            calculateMomentumStatistics(
                grid,
                state,
                HBAR
            );

        std::cout
            << "\n3. Momentum statistics\n"
            << "----------------------\n";

        std::cout
            << "Expected <p>: "
            << momentum.mean
            << "\n";

        std::cout
            << "Expected analytical <p>: "
            << packet.meanMomentum
            << "\n";

        std::cout
            << "Numerical Delta p: "
            << momentum.uncertainty
            << "\n";

        std::cout
            << "Analytical Gaussian Delta p: "
            << packet.analyticalMomentumUncertainty()
            << "\n";

        const double uncertaintyProduct =
            sigmaX *
            momentum.uncertainty;

        const double heisenbergBound =
            HBAR / 2.0;

        std::cout
            << "\n4. Heisenberg uncertainty test\n"
            << "-------------------------------\n";

        std::cout
            << "Delta x * Delta p: "
            << uncertaintyProduct
            << "\n";

        std::cout
            << "hbar / 2: "
            << heisenbergBound
            << "\n";

        std::cout
            << "Bound satisfied: "
            << std::boolalpha
            << (uncertaintyProduct >= heisenbergBound)
            << "\n";

        /*
         * For a perfect Gaussian on an infinite continuous domain:
         *
         *   Delta x Delta p = hbar/2.
         *
         * A finite grid and finite-difference momentum operator introduce
         * small numerical deviations.
         */
        requireNear(
            "Heisenberg lower-bound test",
            uncertaintyProduct,
            heisenbergBound,
            0.01
        );

        const double commutatorMaximumError =
            commutatorError(
                grid,
                state
            );

        std::cout
            << "\n5. Canonical commutator\n"
            << "-----------------------\n";

        std::cout
            << "[x,p]psi should equal i*hbar*psi.\n";

        std::cout
            << "Maximum interior numerical error: "
            << commutatorMaximumError
            << "\n";

        /*
         * The finite-difference boundary treatment makes the exact
         * continuum identity imperfect near the edges. The error should
         * be small in the region containing the Gaussian packet.
         */

        std::cout
            << "\n6. Robertson relation\n"
            << "---------------------\n";

        std::cout
            << "For arbitrary observables A and B:\n"
            << "Delta A Delta B >= |<[A,B]>|/2\n";

        std::cout
            << "For position and momentum:\n"
            << "[x,p] = i*hbar\n"
            << "therefore Delta x Delta p >= hbar/2.\n";

        std::cout
            << "\n7. Measurement simulation\n"
            << "-------------------------\n";

        const MeasurementStatistics measurements =
            simulateTwoOutcomeMeasurement(
                0.75,
                100000,
                12345
            );

        std::cout
            << "Two outcomes: -1 and +1\n"
            << "P(+1): 0.75\n"
            << "Number of measurements: 100000\n"
            << "Empirical mean: "
            << measurements.empiricalMean
            << "\n"
            << "Empirical standard deviation: "
            << measurements.empiricalSigma
            << "\n";

        /*
         * The expected mean for outcomes -1 and +1 is:
         *
         *   (-1)(0.25) + (+1)(0.75) = 0.5
         *
         * The variance is:
         *
         *   E[X^2] - E[X]^2 = 1 - 0.25 = 0.75.
         */
        requireNear(
            "Measurement mean",
            measurements.empiricalMean,
            0.5,
            0.03
        );

        std::cout
            << "\n8. Free-particle spreading\n"
            << "---------------------------\n";

        /*
         * A free Gaussian wave packet evolves according to:
         *
         * sigma_x(t) =
         *   sigma_x(0)
         *   sqrt(
         *      1 +
         *      [hbar*t/(2*m*sigma_x(0)^2)]^2
         *   )
         *
         * The physical electron mass is used here, while the uncertainty
         * simulation above used dimensionless hbar=1.
         */
        constexpr double electronMass =
            9.1093837139e-31;

        constexpr double physicalHbar =
            1.054571817e-34;

        constexpr double initialPhysicalWidth =
            1.0e-10;

        const std::vector<double> times = {
            0.0,
            1.0e-16,
            1.0e-15,
            1.0e-14
        };

        for (double time : times) {
            const double width =
                freeParticleWidth(
                    initialPhysicalWidth,
                    time,
                    electronMass,
                    physicalHbar
                );

            std::cout
                << "t="
                << std::scientific
                << time
                << " s -> Delta x="
                << width
                << " m\n";
        }

        std::cout
            << std::defaultfloat;

        std::cout
            << "\n9. Resolution study\n"
            << "--------------------\n";

        convergenceStudy();

        std::cout
            << "\n10. Important implementation trade-offs\n"
            << "----------------------------------------\n";

        std::cout
            << "Finite differences are simple and transparent, but they "
            << "have truncation and boundary errors.\n";

        std::cout
            << "A spectral/Fourier method can represent derivatives very "
            << "accurately for suitable periodic or carefully treated "
            << "domains, but it requires more mathematical and boundary "
            << "consideration.\n";

        std::cout
            << "A direct DFT has O(N^2) complexity. FFT algorithms reduce "
            << "this to approximately O(N log N), which is important for "
            << "large quantum simulations.\n";

        std::cout
            << "\n11. Security and reliability considerations\n"
            << "---------------------------------------------\n";

        std::cout
            << "Scientific numerical software should validate grid sizes, "
            << "physical parameters, normalization, finite floating-point "
            << "values, and array dimensions. Silent numerical corruption "
            << "can be more dangerous than an explicit failure.\n";

        std::cout
            << "\n12. Conceptual distinction\n"
            << "--------------------------\n";

        std::cout
            << "The uncertainty principle describes intrinsic statistical "
            << "constraints on quantum observables. It is not simply an "
            << "instrument-error statement and is not equivalent to the "
            << "claim that measurement mechanically disturbs a particle.\n";

        std::cout
            << "\n13. Key equations\n"
            << "-----------------\n";

        std::cout
            << "Born rule:                  P(x)=|psi(x)|^2\n"
            << "Expectation:               <A>=<psi|A|psi>\n"
            << "Variance:                  Delta A^2=<A^2>-<A>^2\n"
            << "Momentum operator:         p=-i*hbar*d/dx\n"
            << "Canonical commutator:      [x,p]=i*hbar\n"
            << "Heisenberg relation:       Delta x Delta p >= hbar/2\n"
            << "Robertson relation:        Delta A Delta B >= |<[A,B]>|/2\n"
            << "de Broglie relation:       p=hbar*k\n";

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    }
    catch (const std::exception& exception) {
        std::cerr
            << "\nFatal error: "
            << exception.what()
            << "\n";

        return 1;
    }
}
