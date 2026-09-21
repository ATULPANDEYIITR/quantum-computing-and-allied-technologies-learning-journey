/*
 * Quantum Harmonic Oscillator
 * ===========================
 *
 * C++17 technical case study:
 *
 *     "A quantum oscillator engine for a nanoscale resonator"
 *
 * The program models a one-dimensional quantum harmonic oscillator using
 * the number-state basis. It demonstrates how the mathematical structure
 * of the oscillator can become a reusable computational component.
 *
 * The implementation includes:
 *
 *   - strongly typed physical parameters
 *   - number-state representation
 *   - Hamiltonian construction
 *   - ladder operators
 *   - position and momentum operators
 *   - matrix arithmetic
 *   - state normalization
 *   - expectation values
 *   - uncertainty relation
 *   - coherent states
 *   - time evolution
 *   - thermal occupation
 *   - quartic perturbation
 *   - measurement simulation
 *   - validation
 *   - performance discussion through complexity reporting
 *
 * Build:
 *
 *     g++ -std=c++17 -O2 quantum_harmonic_oscillator.cpp -o qho
 *
 * Run:
 *
 *     ./qho
 *
 * The program uses only the C++ standard library.
 */

#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>


using Complex = std::complex<double>;
using Matrix = std::vector<std::vector<Complex>>;
using State = std::vector<Complex>;


// ---------------------------------------------------------------------------
// Physical model
// ---------------------------------------------------------------------------

struct PhysicalParameters {
    double hbar;
    double mass;
    double omega;

    PhysicalParameters(double hbar_value = 1.0,
                       double mass_value = 1.0,
                       double omega_value = 1.0)
        : hbar(hbar_value),
          mass(mass_value),
          omega(omega_value) {
        validate();
    }

    void validate() const {
        if (hbar <= 0.0) {
            throw std::invalid_argument("hbar must be positive");
        }

        if (mass <= 0.0) {
            throw std::invalid_argument("mass must be positive");
        }

        if (omega <= 0.0) {
            throw std::invalid_argument("omega must be positive");
        }
    }

    double oscillatorLength() const {
        return std::sqrt(hbar / (mass * omega));
    }

    double groundStateEnergy() const {
        return 0.5 * hbar * omega;
    }

    double energy(int n) const {
        if (n < 0) {
            throw std::invalid_argument("quantum number cannot be negative");
        }

        return hbar * omega * (static_cast<double>(n) + 0.5);
    }
};


// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

void printSeparator(const std::string& title) {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n"
              << title
              << "\n"
              << std::string(78, '=')
              << "\n";
}


bool approximatelyEqual(double a,
                        double b,
                        double tolerance = 1e-9) {
    return std::abs(a - b) <=
           tolerance * std::max({1.0, std::abs(a), std::abs(b)});
}


double stateNorm(const State& state) {
    double squaredNorm = 0.0;

    for (const Complex& amplitude : state) {
        squaredNorm += std::norm(amplitude);
    }

    return std::sqrt(squaredNorm);
}


State normalizeState(const State& state) {
    const double norm = stateNorm(state);

    if (norm <= std::numeric_limits<double>::epsilon()) {
        throw std::invalid_argument("cannot normalize the zero state");
    }

    State result = state;

    for (Complex& amplitude : result) {
        amplitude /= norm;
    }

    return result;
}


// ---------------------------------------------------------------------------
// Matrix utilities
// ---------------------------------------------------------------------------

Matrix zeroMatrix(std::size_t size) {
    return Matrix(
        size,
        std::vector<Complex>(size, Complex(0.0, 0.0))
    );
}


Matrix identityMatrix(std::size_t size) {
    Matrix result = zeroMatrix(size);

    for (std::size_t index = 0; index < size; ++index) {
        result[index][index] = Complex(1.0, 0.0);
    }

    return result;
}


Matrix matrixAdd(const Matrix& A, const Matrix& B) {
    if (A.size() != B.size()) {
        throw std::invalid_argument("matrix sizes differ");
    }

    Matrix result = zeroMatrix(A.size());

    for (std::size_t row = 0; row < A.size(); ++row) {
        if (A[row].size() != B[row].size()) {
            throw std::invalid_argument("matrix row sizes differ");
        }

        for (std::size_t column = 0;
             column < A[row].size();
             ++column) {
            result[row][column] =
                A[row][column] + B[row][column];
        }
    }

    return result;
}


Matrix matrixSubtract(const Matrix& A, const Matrix& B) {
    if (A.size() != B.size()) {
        throw std::invalid_argument("matrix sizes differ");
    }

    Matrix result = zeroMatrix(A.size());

    for (std::size_t row = 0; row < A.size(); ++row) {
        for (std::size_t column = 0;
             column < A[row].size();
             ++column) {
            result[row][column] =
                A[row][column] - B[row][column];
        }
    }

    return result;
}


Matrix matrixScale(const Matrix& matrix, Complex scalar) {
    Matrix result = matrix;

    for (auto& row : result) {
        for (Complex& value : row) {
            value *= scalar;
        }
    }

    return result;
}


Matrix matrixMultiply(const Matrix& A, const Matrix& B) {
    if (A.empty() || B.empty()) {
        return {};
    }

    const std::size_t n = A.size();

    if (B.size() != n) {
        throw std::invalid_argument(
            "matrix multiplication requires compatible dimensions"
        );
    }

    Matrix result = zeroMatrix(n);

    /*
     * Dense matrix multiplication is O(N^3).
     *
     * The oscillator matrices are sparse in the number basis, but this
     * demonstration intentionally keeps a general matrix representation
     * because it makes the operator construction transparent.
     */
    for (std::size_t row = 0; row < n; ++row) {
        for (std::size_t middle = 0; middle < n; ++middle) {
            if (std::abs(A[row][middle]) == 0.0) {
                continue;
            }

            for (std::size_t column = 0; column < n; ++column) {
                result[row][column] +=
                    A[row][middle] * B[middle][column];
            }
        }
    }

    return result;
}


State matrixVectorMultiply(const Matrix& matrix,
                            const State& state) {
    if (matrix.size() != state.size()) {
        throw std::invalid_argument(
            "matrix and state dimensions differ"
        );
    }

    State result(
        state.size(),
        Complex(0.0, 0.0)
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0;
             column < state.size();
             ++column) {
            result[row] +=
                matrix[row][column] * state[column];
        }
    }

    return result;
}


Complex innerProduct(const State& bra,
                     const State& ket) {
    if (bra.size() != ket.size()) {
        throw std::invalid_argument(
            "states have different dimensions"
        );
    }

    Complex result(0.0, 0.0);

    for (std::size_t index = 0;
         index < bra.size();
         ++index) {
        result +=
            std::conj(bra[index]) * ket[index];
    }

    return result;
}


Complex expectationValue(const State& state,
                         const Matrix& operatorMatrix) {
    return innerProduct(
        state,
        matrixVectorMultiply(operatorMatrix, state)
    );
}


// ---------------------------------------------------------------------------
// Quantum harmonic oscillator
// ---------------------------------------------------------------------------

class QuantumHarmonicOscillator {
private:
    PhysicalParameters parameters_;
    std::size_t dimension_;

public:
    QuantumHarmonicOscillator(
        PhysicalParameters parameters,
        std::size_t dimension
    )
        : parameters_(std::move(parameters)),
          dimension_(dimension) {
        if (dimension_ == 0) {
            throw std::invalid_argument(
                "basis dimension must be positive"
            );
        }
    }

    std::size_t dimension() const {
        return dimension_;
    }

    const PhysicalParameters& parameters() const {
        return parameters_;
    }

    double energy(std::size_t n) const {
        if (n >= dimension_) {
            throw std::out_of_range(
                "quantum number exceeds finite basis"
            );
        }

        return parameters_.energy(
            static_cast<int>(n)
        );
    }

    State basisState(std::size_t n) const {
        if (n >= dimension_) {
            throw std::out_of_range(
                "basis-state index exceeds dimension"
            );
        }

        State state(
            dimension_,
            Complex(0.0, 0.0)
        );

        state[n] = Complex(1.0, 0.0);

        return state;
    }

    Matrix annihilationOperator() const {
        Matrix result = zeroMatrix(dimension_);

        /*
         * a|n> = sqrt(n)|n-1>
         *
         * Matrix convention:
         *
         * result[row][column] = <row|a|column>
         */
        for (std::size_t n = 1;
             n < dimension_;
             ++n) {
            result[n - 1][n] =
                Complex(std::sqrt(
                    static_cast<double>(n)
                ), 0.0);
        }

        return result;
    }

    Matrix creationOperator() const {
        Matrix result = zeroMatrix(dimension_);

        /*
         * a†|n> = sqrt(n+1)|n+1>
         *
         * The final basis state cannot be raised inside the truncated
         * representation. That is a finite-basis boundary artifact.
         */
        for (std::size_t n = 0;
             n + 1 < dimension_;
             ++n) {
            result[n + 1][n] =
                Complex(std::sqrt(
                    static_cast<double>(n + 1)
                ), 0.0);
        }

        return result;
    }

    Matrix positionOperator() const {
        const Matrix a = annihilationOperator();
        const Matrix adag = creationOperator();

        const Matrix sum = matrixAdd(a, adag);

        const double scale =
            std::sqrt(
                parameters_.hbar /
                (2.0 * parameters_.mass * parameters_.omega)
            );

        return matrixScale(
            sum,
            Complex(scale, 0.0)
        );
    }

    Matrix momentumOperator() const {
        const Matrix a = annihilationOperator();
        const Matrix adag = creationOperator();

        /*
         * p = -i sqrt(m hbar omega / 2) (a - a†)
         */
        const Matrix difference =
            matrixSubtract(a, adag);

        const double scale =
            std::sqrt(
                parameters_.mass *
                parameters_.hbar *
                parameters_.omega /
                2.0
            );

        return matrixScale(
            difference,
            Complex(0.0, -scale)
        );
    }

    Matrix exactHamiltonian() const {
        Matrix result = zeroMatrix(dimension_);

        for (std::size_t n = 0;
             n < dimension_;
             ++n) {
            result[n][n] =
                Complex(energy(n), 0.0);
        }

        return result;
    }

    Matrix HamiltonianFromXP() const {
        const Matrix x = positionOperator();
        const Matrix p = momentumOperator();

        const Matrix xSquared =
            matrixMultiply(x, x);

        const Matrix pSquared =
            matrixMultiply(p, p);

        const double kineticScale =
            1.0 / (2.0 * parameters_.mass);

        const double potentialScale =
            0.5 *
            parameters_.mass *
            parameters_.omega *
            parameters_.omega;

        const Matrix kinetic =
            matrixScale(
                pSquared,
                Complex(kineticScale, 0.0)
            );

        const Matrix potential =
            matrixScale(
                xSquared,
                Complex(potentialScale, 0.0)
            );

        return matrixAdd(kinetic, potential);
    }

    State applyAnnihilation(const State& state) const {
        return matrixVectorMultiply(
            annihilationOperator(),
            state
        );
    }

    State applyCreation(const State& state) const {
        return matrixVectorMultiply(
            creationOperator(),
            state
        );
    }

    State evolve(const State& initialState,
                 double time) const {
        if (initialState.size() != dimension_) {
            throw std::invalid_argument(
                "state dimension does not match oscillator basis"
            );
        }

        /*
         * Because |n> is an energy eigenstate:
         *
         * c_n(t) =
         *     c_n(0) exp(-i E_n t / hbar)
         *
         * This avoids a general matrix exponential.
         */
        State result = initialState;

        for (std::size_t n = 0;
             n < dimension_;
             ++n) {
            const double phase =
                -energy(n) * time /
                parameters_.hbar;

            result[n] *=
                std::exp(Complex(0.0, phase));
        }

        return result;
    }

    double exactX2(std::size_t n) const {
        return parameters_.hbar /
               (parameters_.mass *
                parameters_.omega) *
               (static_cast<double>(n) + 0.5);
    }

    double exactP2(std::size_t n) const {
        return parameters_.mass *
               parameters_.hbar *
               parameters_.omega *
               (static_cast<double>(n) + 0.5);
    }

    double positionUncertainty(std::size_t n) const {
        return std::sqrt(exactX2(n));
    }

    double momentumUncertainty(std::size_t n) const {
        return std::sqrt(exactP2(n));
    }

    double uncertaintyProduct(std::size_t n) const {
        return positionUncertainty(n) *
               momentumUncertainty(n);
    }

    State coherentState(Complex alpha) const {
        /*
         * Infinite coherent state:
         *
         * |alpha> =
         * exp(-|alpha|²/2)
         * sum_n alpha^n / sqrt(n!) |n>
         *
         * The finite implementation is normalized after truncation.
         */
        State result(
            dimension_,
            Complex(0.0, 0.0)
        );

        const double magnitudeSquared =
            std::norm(alpha);

        const double prefactor =
            std::exp(-0.5 * magnitudeSquared);

        Complex alphaPower(1.0, 0.0);

        double factorialValue = 1.0;

        for (std::size_t n = 0;
             n < dimension_;
             ++n) {
            if (n > 0) {
                alphaPower *= alpha;
                factorialValue *=
                    static_cast<double>(n);
            }

            result[n] =
                prefactor *
                alphaPower /
                std::sqrt(factorialValue);
        }

        return normalizeState(result);
    }

    double thermalOccupation(double temperature) const {
        if (temperature <= 0.0) {
            throw std::invalid_argument(
                "temperature must be positive"
            );
        }

        const double x =
            parameters_.hbar *
            parameters_.omega /
            temperature;

        if (x > 700.0) {
            return 0.0;
        }

        return 1.0 / std::expm1(x);
    }

    double thermalMeanEnergy(double temperature) const {
        return parameters_.hbar *
               parameters_.omega *
               (0.5 + thermalOccupation(temperature));
    }

    double thermalPartitionFunction(
        double temperature
    ) const {
        if (temperature <= 0.0) {
            throw std::invalid_argument(
                "temperature must be positive"
            );
        }

        const double x =
            parameters_.hbar *
            parameters_.omega /
            temperature;

        return std::exp(-0.5 * x) /
               (1.0 - std::exp(-x));
    }

    double quarticFirstOrderCorrection(
        std::size_t n,
        double lambda
    ) const {
        /*
         * For H' = lambda x^4:
         *
         * Delta E_n^(1)
         * =
         * lambda * 3
         * [hbar/(2m omega)]^2
         * (2n^2 + 2n + 1)
         */
        const double scale =
            parameters_.hbar /
            (2.0 *
             parameters_.mass *
             parameters_.omega);

        const double nValue =
            static_cast<double>(n);

        return lambda *
               3.0 *
               scale *
               scale *
               (2.0 * nValue * nValue +
                2.0 * nValue +
                1.0);
    }

    double firstOrderPerturbedEnergy(
        std::size_t n,
        double lambda
    ) const {
        return energy(n) +
               quarticFirstOrderCorrection(
                   n,
                   lambda
               );
    }
};


// ---------------------------------------------------------------------------
// Probability measurement
// ---------------------------------------------------------------------------

std::vector<std::size_t> sampleMeasurements(
    const State& state,
    std::size_t sampleCount,
    unsigned int seed
) {
    if (state.empty()) {
        throw std::invalid_argument(
            "cannot measure an empty state"
        );
    }

    const double norm = stateNorm(state);

    if (norm <= 0.0) {
        throw std::invalid_argument(
            "cannot measure a zero state"
        );
    }

    std::vector<double> probabilities;

    probabilities.reserve(state.size());

    for (const Complex& amplitude : state) {
        probabilities.push_back(
            std::norm(amplitude) /
            (norm * norm)
        );
    }

    std::discrete_distribution<std::size_t>
        distribution(
            probabilities.begin(),
            probabilities.end()
        );

    std::mt19937 generator(seed);

    std::vector<std::size_t> outcomes;
    outcomes.reserve(sampleCount);

    for (std::size_t sample = 0;
         sample < sampleCount;
         ++sample) {
        outcomes.push_back(
            distribution(generator)
        );
    }

    return outcomes;
}


std::vector<double> empiricalProbabilities(
    const std::vector<std::size_t>& outcomes,
    std::size_t dimension
) {
    std::vector<double> frequencies(
        dimension,
        0.0
    );

    if (outcomes.empty()) {
        return frequencies;
    }

    for (std::size_t outcome : outcomes) {
        if (outcome >= dimension) {
            throw std::out_of_range(
                "measurement outcome outside basis"
            );
        }

        frequencies[outcome] += 1.0;
    }

    for (double& frequency : frequencies) {
        frequency /=
            static_cast<double>(outcomes.size());
    }

    return frequencies;
}


// ---------------------------------------------------------------------------
// Diagnostic output
// ---------------------------------------------------------------------------

void printState(
    const State& state,
    double probabilityThreshold = 1e-10
) {
    for (std::size_t n = 0;
         n < state.size();
         ++n) {
        const double probability =
            std::norm(state[n]);

        if (probability > probabilityThreshold) {
            std::cout
                << "|" << n << "> "
                << "coefficient=("
                << std::fixed
                << std::setprecision(6)
                << state[n].real()
                << ", "
                << state[n].imag()
                << ") "
                << "P="
                << probability
                << "\n";
        }
    }
}


// ---------------------------------------------------------------------------
// Case study
// ---------------------------------------------------------------------------

class ResonatorAnalysis {
private:
    QuantumHarmonicOscillator oscillator_;

public:
    explicit ResonatorAnalysis(
        QuantumHarmonicOscillator oscillator
    )
        : oscillator_(std::move(oscillator)) {}

    void run() const {
        printSeparator(
            "CASE STUDY: QUANTUM NANOMECHANICAL RESONATOR"
        );

        explainSystem();

        energyAnalysis();
        ladderAnalysis();
        operatorAnalysis();
        stateAnalysis();
        timeEvolutionAnalysis();
        thermalAnalysis();
        perturbationAnalysis();
        measurementAnalysis();
        numericalValidation();
        performanceAnalysis();
        failureAnalysis();
    }

private:
    void explainSystem() const {
        std::cout
            << "System model:\n"
            << "A single vibrational mode is approximated as a one-dimensional\n"
            << "quantum harmonic oscillator. The mode is represented in a finite\n"
            << "number-state basis for computational experiments.\n\n";

        std::cout
            << "Physical parameters:\n"
            << "hbar = "
            << oscillator_.parameters().hbar
            << "\n"
            << "mass = "
            << oscillator_.parameters().mass
            << "\n"
            << "omega = "
            << oscillator_.parameters().omega
            << "\n"
            << "basis dimension = "
            << oscillator_.dimension()
            << "\n"
            << "oscillator length = "
            << oscillator_.parameters().oscillatorLength()
            << "\n";
    }

    void energyAnalysis() const {
        printSeparator("Energy spectrum");

        for (std::size_t n = 0;
             n < 8 && n < oscillator_.dimension();
             ++n) {
            std::cout
                << "n=" << n
                << "  E_n="
                << oscillator_.energy(n)
                << "\n";
        }

        std::cout
            << "\nThe spacing is exactly hbar*omega.\n"
            << "The ground state retains the zero-point energy hbar*omega/2.\n";
    }

    void ladderAnalysis() const {
        printSeparator("Ladder operators");

        const State state =
            oscillator_.basisState(3);

        const State lowered =
            oscillator_.applyAnnihilation(state);

        const State raised =
            oscillator_.applyCreation(state);

        std::cout << "a|3>:\n";
        printState(lowered);

        std::cout << "\na^dagger|3>:\n";
        printState(raised);

        const State ground =
            oscillator_.basisState(0);

        const State destroyed =
            oscillator_.applyAnnihilation(ground);

        std::cout
            << "\nNorm of a|0> = "
            << stateNorm(destroyed)
            << "\n";
    }

    void operatorAnalysis() const {
        printSeparator("Position, momentum, and Hamiltonian");

        const Matrix x =
            oscillator_.positionOperator();

        const Matrix p =
            oscillator_.momentumOperator();

        const Matrix xSquared =
            matrixMultiply(x, x);

        const Matrix pSquared =
            matrixMultiply(p, p);

        for (std::size_t n = 0;
             n < 4 && n < oscillator_.dimension();
             ++n) {
            const State state =
                oscillator_.basisState(n);

            const Complex x2 =
                expectationValue(
                    state,
                    xSquared
                );

            const Complex p2 =
                expectationValue(
                    state,
                    pSquared
                );

            std::cout
                << "n=" << n
                << "  <x^2>="
                << x2.real()
                << "  <p^2>="
                << p2.real()
                << "\n";
        }

        const Matrix H =
            oscillator_.exactHamiltonian();

        std::cout
            << "\nHamiltonian diagonal entries:\n";

        for (std::size_t n = 0;
             n < 6 && n < oscillator_.dimension();
             ++n) {
            std::cout
                << "H[" << n << "][" << n << "] = "
                << H[n][n].real()
                << "\n";
        }
    }

    void stateAnalysis() const {
        printSeparator("State properties and uncertainty");

        for (std::size_t n = 0;
             n < 5 && n < oscillator_.dimension();
             ++n) {
            const double dx =
                oscillator_.positionUncertainty(n);

            const double dp =
                oscillator_.momentumUncertainty(n);

            std::cout
                << "n=" << n
                << "  Delta x=" << dx
                << "  Delta p=" << dp
                << "  Delta x Delta p="
                << dx * dp
                << "\n";
        }

        std::cout
            << "\nThe ground state satisfies Delta x Delta p = hbar/2.\n";
    }

    void timeEvolutionAnalysis() const {
        printSeparator("Time evolution");

        State state(
            oscillator_.dimension(),
            Complex(0.0, 0.0)
        );

        state[0] = Complex(1.0, 0.0);
        state[1] = Complex(0.7, 0.2);
        state[2] = Complex(0.3, -0.1);
        state[3] = Complex(0.1, 0.05);

        state = normalizeState(state);

        const double initialNorm =
            stateNorm(state);

        const State evolved =
            oscillator_.evolve(
                state,
                3.141592653589793
            );

        const double evolvedNorm =
            stateNorm(evolved);

        std::cout
            << "Initial norm = "
            << initialNorm
            << "\n"
            << "Evolved norm = "
            << evolvedNorm
            << "\n";

        std::cout
            << "\nInitial state:\n";

        printState(state);

        std::cout
            << "\nState after t=pi:\n";

        printState(evolved);

        std::cout
            << "\nOnly phases change for each number-state component. "
            << "The probabilities |c_n|^2 remain constant.\n";
    }

    void thermalAnalysis() const {
        printSeparator("Thermal occupation");

        std::cout
            << "Temperature       Z          <n>          <E>\n";

        for (double temperature :
             {0.1, 0.25, 0.5, 1.0, 2.0, 5.0}) {
            std::cout
                << std::fixed
                << std::setprecision(4)
                << std::setw(10)
                << temperature
                << std::setw(13)
                << oscillator_.thermalPartitionFunction(
                       temperature
                   )
                << std::setw(13)
                << oscillator_.thermalOccupation(
                       temperature
                   )
                << std::setw(13)
                << oscillator_.thermalMeanEnergy(
                       temperature
                   )
                << "\n";
        }

        std::cout
            << "\nAt low temperature, thermal excitation is suppressed and "
            << "the zero-point contribution remains. At high temperature, "
            << "the mean excitation approaches the classical regime.\n";
    }

    void perturbationAnalysis() const {
        printSeparator("Anharmonic correction");

        const double lambda = 0.02;

        std::cout
            << "Perturbation: H' = lambda*x^4, lambda = "
            << lambda
            << "\n\n";

        for (std::size_t n = 0;
             n < 6 && n < oscillator_.dimension();
             ++n) {
            const double correction =
                oscillator_.quarticFirstOrderCorrection(
                    n,
                    lambda
                );

            const double corrected =
                oscillator_.firstOrderPerturbedEnergy(
                    n,
                    lambda
                );

            std::cout
                << "n=" << n
                << "  DeltaE(1)="
                << correction
                << "  E_perturbed≈"
                << corrected
                << "\n";
        }

        std::cout
            << "\nThe correction grows with n because higher oscillator "
            << "states have larger position-space moments.\n";
    }

    void measurementAnalysis() const {
        printSeparator("Measurement statistics");

        const Complex alpha(
            1.0,
            0.5
        );

        const State coherent =
            oscillator_.coherentState(alpha);

        constexpr std::size_t sampleCount = 20000;

        const auto outcomes =
            sampleMeasurements(
                coherent,
                sampleCount,
                2026
            );

        const auto empirical =
            empiricalProbabilities(
                outcomes,
                oscillator_.dimension()
            );

        std::cout
            << "Coherent-state number statistics:\n";

        for (std::size_t n = 0;
             n < 8 && n < oscillator_.dimension();
             ++n) {
            const double meanNumber =
                std::norm(alpha);

            const double theoretical =
                std::exp(-meanNumber) *
                std::pow(meanNumber,
                         static_cast<double>(n)) /
                std::tgamma(
                    static_cast<double>(n) + 1.0
                );

            std::cout
                << "n=" << n
                << "  theoretical="
                << theoretical
                << "  measured="
                << empirical[n]
                << "\n";
        }

        std::cout
            << "\nRepeated measurements reproduce the probability "
            << "distribution statistically rather than deterministically.\n";
    }

    void numericalValidation() const {
        printSeparator("Numerical validation");

        const Matrix HExact =
            oscillator_.exactHamiltonian();

        const Matrix HFromXP =
            oscillator_.HamiltonianFromXP();

        std::cout
            << "Comparing exact diagonal Hamiltonian with H constructed "
            << "from x and p:\n";

        for (std::size_t n = 0;
             n < 5 && n < oscillator_.dimension();
             ++n) {
            std::cout
                << "n=" << n
                << "  exact="
                << HExact[n][n].real()
                << "  x/p="
                << HFromXP[n][n].real()
                << "\n";
        }

        /*
         * Check normalization and orthogonality indirectly using the
         * number-basis representation. Number states are orthonormal by
         * construction.
         */
        for (std::size_t n = 0;
             n < 5 && n < oscillator_.dimension();
             ++n) {
            const State state =
                oscillator_.basisState(n);

            const Complex norm =
                innerProduct(state, state);

            if (!approximatelyEqual(
                    norm.real(),
                    1.0
                )) {
                throw std::runtime_error(
                    "number-state normalization failed"
                );
            }
        }

        std::cout
            << "Number-state normalization checks passed.\n";
    }

    void performanceAnalysis() const {
        printSeparator("Performance and design considerations");

        const std::size_t N =
            oscillator_.dimension();

        std::cout
            << "Basis dimension: N = "
            << N
            << "\n"
            << "Dense matrix multiplication: O(N^3)\n"
            << "Dense matrix-vector multiplication: O(N^2)\n"
            << "Ladder operators themselves are sparse: O(N) nonzero entries\n"
            << "Exact diagonal Hamiltonian storage: O(N)\n";

        std::cout
            << "\nFor large oscillator simulations, sparse matrices or direct "
            << "number-basis formulas are preferable to dense matrix algebra. "
            << "The present dense implementation is deliberately educational "
            << "and transparent.\n";
    }

    void failureAnalysis() const {
        printSeparator("Failure conditions and validation");

        try {
            QuantumHarmonicOscillator invalid(
                PhysicalParameters(1.0, 1.0, 1.0),
                0
            );

            (void)invalid;
        } catch (const std::exception& error) {
            std::cout
                << "Zero-dimensional basis rejected: "
                << error.what()
                << "\n";
        }

        try {
            PhysicalParameters invalidParameters(
                1.0,
                -1.0,
                1.0
            );

            (void)invalidParameters;
        } catch (const std::exception& error) {
            std::cout
                << "Negative mass rejected: "
                << error.what()
                << "\n";
        }

        try {
            oscillator_.thermalOccupation(-1.0);
        } catch (const std::exception& error) {
            std::cout
                << "Negative temperature rejected: "
                << error.what()
                << "\n";
        }
    }
};


// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

int main() {
    try {
        /*
         * In this case study we use dimensionless parameters.
         *
         * This is common in theoretical and computational physics because
         * it exposes the universal structure without carrying physical
         * units through every intermediate calculation.
         *
         * The same class accepts physical values in SI units.
         */
        PhysicalParameters parameters(
            1.0,   // hbar
            1.0,   // mass
            1.0    // angular frequency
        );

        QuantumHarmonicOscillator oscillator(
            parameters,
            24
        );

        ResonatorAnalysis analysis(
            oscillator
        );

        analysis.run();

        printSeparator(
            "FINAL VERIFICATION"
        );

        const double groundEnergy =
            oscillator.energy(0);

        if (!approximatelyEqual(
                groundEnergy,
                0.5
            )) {
            throw std::runtime_error(
                "incorrect ground-state energy"
            );
        }

        if (!approximatelyEqual(
                oscillator.uncertaintyProduct(0),
                parameters.hbar / 2.0
            )) {
            throw std::runtime_error(
                "ground-state uncertainty relation failed"
            );
        }

        std::cout
            << "Ground-state energy check: PASS\n"
            << "Ground-state uncertainty check: PASS\n"
            << "Quantum harmonic oscillator case study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
