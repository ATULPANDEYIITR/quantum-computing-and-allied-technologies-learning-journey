/*
 * Entanglement: Bell States and Non-Classical Correlations
 *
 * C++17 case study:
 * A repository-independent quantum correlation engine evaluates a two-qubit
 * Bell state as part of a hypothetical quantum-network verification service.
 *
 * The engine:
 *   - stores normalized two-qubit state vectors
 *   - represents complex amplitudes
 *   - constructs Pauli and rotated measurement observables
 *   - evaluates joint expectation values
 *   - evaluates the CHSH expression
 *   - validates state invariants
 *   - estimates correlations using finite-shot sampling
 *   - reports whether a selected configuration exceeds the classical CHSH bound
 *
 * Compile:
 *   g++ -std=c++17 -O2 bell_entanglement.cpp -o bell_entanglement
 *
 * Run:
 *   ./bell_entanglement
 */

#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

using Complex = std::complex<double>;

constexpr double EPSILON = 1e-10;
constexpr std::size_t QUBIT_DIMENSION = 2;
constexpr std::size_t TWO_QUBIT_DIMENSION = 4;

using Vector2 = std::array<Complex, 2>;
using Vector4 = std::array<Complex, 4>;
using Matrix2 = std::array<std::array<Complex, 2>, 2>;
using Matrix4 = std::array<std::array<Complex, 4>, 4>;

double probability(const Complex& amplitude) {
    return std::norm(amplitude);
}

Matrix2 pauliX() {
    return {{{Complex(0), Complex(1)},
             {Complex(1), Complex(0)}}};
}

Matrix2 pauliY() {
    return {{{Complex(0), Complex(0, -1)},
             {Complex(0, 1), Complex(0)}}};
}

Matrix2 pauliZ() {
    return {{{Complex(1), Complex(0)},
             {Complex(0), Complex(-1)}}};
}

Matrix4 kronecker(const Matrix2& left, const Matrix2& right) {
    Matrix4 result{};

    for (std::size_t leftRow = 0; leftRow < 2; ++leftRow) {
        for (std::size_t rightRow = 0; rightRow < 2; ++rightRow) {
            const std::size_t row = leftRow * 2 + rightRow;

            for (std::size_t leftColumn = 0; leftColumn < 2; ++leftColumn) {
                for (std::size_t rightColumn = 0; rightColumn < 2; ++rightColumn) {
                    const std::size_t column =
                        leftColumn * 2 + rightColumn;

                    result[row][column] =
                        left[leftRow][leftColumn] *
                        right[rightRow][rightColumn];
                }
            }
        }
    }

    return result;
}

Vector4 matrixVectorMultiply(
    const Matrix4& matrix,
    const Vector4& vector
) {
    Vector4 result{};

    for (std::size_t row = 0; row < 4; ++row) {
        for (std::size_t column = 0; column < 4; ++column) {
            result[row] += matrix[row][column] * vector[column];
        }
    }

    return result;
}

Complex innerProduct(
    const Vector4& left,
    const Vector4& right
) {
    Complex result{};

    for (std::size_t index = 0; index < 4; ++index) {
        result += std::conj(left[index]) * right[index];
    }

    return result;
}

double expectationValue(
    const Vector4& state,
    const Matrix4& observable
) {
    const Vector4 transformed = matrixVectorMultiply(observable, state);
    const Complex result = innerProduct(state, transformed);

    if (std::abs(result.imag()) > 1e-8) {
        throw std::runtime_error(
            "The observable produced a non-real expectation value."
        );
    }

    return result.real();
}

class BellState {
public:
    BellState(
        std::string name,
        Vector4 amplitudes
    )
        : name_(std::move(name)),
          amplitudes_(amplitudes) {
        validateNormalization();
    }

    const std::string& name() const {
        return name_;
    }

    const Vector4& amplitudes() const {
        return amplitudes_;
    }

    std::array<double, 4> computationalProbabilities() const {
        std::array<double, 4> result{};

        for (std::size_t index = 0; index < 4; ++index) {
            result[index] = probability(amplitudes_[index]);
        }

        return result;
    }

    double correlation(
        const Matrix2& firstObservable,
        const Matrix2& secondObservable
    ) const {
        return expectationValue(
            amplitudes_,
            kronecker(firstObservable, secondObservable)
        );
    }

private:
    std::string name_;
    Vector4 amplitudes_;

    void validateNormalization() const {
        double norm = 0.0;

        for (const Complex& amplitude : amplitudes_) {
            norm += probability(amplitude);
        }

        if (!std::isfinite(norm) ||
            std::abs(norm - 1.0) > EPSILON) {
            throw std::invalid_argument(
                "Quantum state is not normalized."
            );
        }
    }
};

BellState phiPlus() {
    const double s = 1.0 / std::sqrt(2.0);

    return BellState(
        "Phi+",
        {Complex(s), Complex(0), Complex(0), Complex(s)}
    );
}

BellState phiMinus() {
    const double s = 1.0 / std::sqrt(2.0);

    return BellState(
        "Phi-",
        {Complex(s), Complex(0), Complex(0), Complex(-s)}
    );
}

BellState psiPlus() {
    const double s = 1.0 / std::sqrt(2.0);

    return BellState(
        "Psi+",
        {Complex(0), Complex(s), Complex(s), Complex(0)}
    );
}

BellState psiMinus() {
    const double s = 1.0 / std::sqrt(2.0);

    return BellState(
        "Psi-",
        {Complex(0), Complex(s), Complex(-s), Complex(0)}
    );
}

Matrix2 rotatedObservable(
    double thetaDegrees,
    double phiDegrees = 0.0
) {
    const double pi = std::acos(-1.0);
    const double theta = thetaDegrees * pi / 180.0;
    const double phi = phiDegrees * pi / 180.0;

    const double x = std::sin(theta) * std::cos(phi);
    const double y = std::sin(theta) * std::sin(phi);
    const double z = std::cos(theta);

    return {{
        {Complex(z), Complex(x, -y)},
        {Complex(x, y), Complex(-z)}
    }};
}

struct ChshResult {
    double eAB;
    double eABPrime;
    double eAPrimeB;
    double eAPrimeBPrime;
    double S;
};

ChshResult calculateCHSH(
    const BellState& state,
    const Matrix2& a,
    const Matrix2& aPrime,
    const Matrix2& b,
    const Matrix2& bPrime
) {
    const double eAB = state.correlation(a, b);
    const double eABPrime = state.correlation(a, bPrime);
    const double eAPrimeB = state.correlation(aPrime, b);
    const double eAPrimeBPrime = state.correlation(aPrime, bPrime);

    const double S =
        eAB +
        eABPrime +
        eAPrimeB -
        eAPrimeBPrime;

    return {
        eAB,
        eABPrime,
        eAPrimeB,
        eAPrimeBPrime,
        S
    };
}

double estimateCorrelation(
    const BellState& state,
    const Matrix2& firstObservable,
    const Matrix2& secondObservable,
    std::size_t shots,
    std::mt19937& generator
) {
    if (shots == 0) {
        throw std::invalid_argument(
            "A finite-shot experiment requires at least one shot."
        );
    }

    const double expectedCorrelation =
        state.correlation(firstObservable, secondObservable);

    /*
     * For a binary observable with outcomes +/-1, an exact two-outcome
     * distribution can reproduce any target correlation E in [-1, 1].
     *
     * A random first detector result is followed by a conditional second
     * result whose probability of matching is (1 + E) / 2.
     *
     * This estimates the joint correlation rather than pretending that
     * independent local samples can reproduce quantum correlations.
     */
    std::bernoulli_distribution firstDetector(0.5);

    const double probabilitySame =
        (1.0 + expectedCorrelation) / 2.0;

    std::bernoulli_distribution sameDetector(probabilitySame);

    long long productSum = 0;

    for (std::size_t shot = 0; shot < shots; ++shot) {
        const int firstResult =
            firstDetector(generator) ? 1 : -1;

        const bool same = sameDetector(generator);

        const int secondResult =
            same ? firstResult : -firstResult;

        productSum += firstResult * secondResult;
    }

    return static_cast<double>(productSum) /
           static_cast<double>(shots);
}

struct ExperimentalCHSH {
    double eAB;
    double eABPrime;
    double eAPrimeB;
    double eAPrimeBPrime;
    double S;
};

ExperimentalCHSH runFiniteShotCHSH(
    const BellState& state,
    const Matrix2& a,
    const Matrix2& aPrime,
    const Matrix2& b,
    const Matrix2& bPrime,
    std::size_t shots,
    std::mt19937& generator
) {
    const double eAB =
        estimateCorrelation(state, a, b, shots, generator);

    const double eABPrime =
        estimateCorrelation(state, a, bPrime, shots, generator);

    const double eAPrimeB =
        estimateCorrelation(state, aPrime, b, shots, generator);

    const double eAPrimeBPrime =
        estimateCorrelation(state, aPrime, bPrime, shots, generator);

    return {
        eAB,
        eABPrime,
        eAPrimeB,
        eAPrimeBPrime,
        eAB + eABPrime + eAPrimeB - eAPrimeBPrime
    };
}

void printProbabilities(const BellState& state) {
    const auto probabilities = state.computationalProbabilities();

    std::cout << state.name() << " computational-basis probabilities\n";

    for (std::size_t index = 0; index < probabilities.size(); ++index) {
        const std::string label =
            (index == 0 ? "00" :
             index == 1 ? "01" :
             index == 2 ? "10" : "11");

        std::cout << "  P(" << label << ") = "
                  << std::fixed << std::setprecision(6)
                  << probabilities[index] << '\n';
    }
}

void compareBellCorrelationSignatures() {
    std::cout << "\n=== Bell-state correlation signatures ===\n";

    const auto x = pauliX();
    const auto y = pauliY();
    const auto z = pauliZ();

    const std::array<BellState, 4> states = {
        phiPlus(),
        phiMinus(),
        psiPlus(),
        psiMinus()
    };

    for (const BellState& state : states) {
        const double xx = state.correlation(x, x);
        const double yy = state.correlation(y, y);
        const double zz = state.correlation(z, z);

        std::cout
            << state.name()
            << ": <XX>=" << std::setw(8) << xx
            << ", <YY>=" << std::setw(8) << yy
            << ", <ZZ>=" << std::setw(8) << zz
            << '\n';
    }

    std::cout
        << "The sign pattern distinguishes Bell states through joint "
        << "observables even when some computational-basis probabilities "
        << "are identical.\n";
}

void demonstrateLocalVersusJointInformation() {
    std::cout << "\n=== Local information versus joint information ===\n";

    const BellState state = phiPlus();

    /*
     * For Phi+, tracing out either qubit produces I/2. The local Z
     * expectation therefore vanishes even though ZZ has expectation +1.
     *
     * This is the operational distinction between local randomness and
     * joint correlation.
     */
    const auto z = pauliZ();

    const double localLikeQuantity =
        expectationValue(
            state.amplitudes(),
            kronecker(z, Matrix2{{
                {Complex(1), Complex(0)},
                {Complex(0), Complex(1)}
            }})
        );

    const double jointCorrelation =
        state.correlation(z, z);

    std::cout
        << "Local Z expectation on the first subsystem: "
        << localLikeQuantity << '\n';

    std::cout
        << "Joint ZZ correlation: "
        << jointCorrelation << '\n';

    std::cout
        << "A local marginal can be unbiased while the pair has a "
        << "deterministic correlation relation.\n";
}

void demonstrateCHSHCaseStudy() {
    std::cout << "\n=== Quantum-network CHSH verification case study ===\n";

    /*
     * Imagine two network endpoints receiving members of an entangled
     * pair. Each endpoint chooses between two measurement settings.
     *
     * The verification service does not inspect an individual bit and
     * declare entanglement from that bit alone. It aggregates correlations
     * under multiple measurement settings and compares the CHSH statistic
     * against the classical bound.
     */
    const BellState state = phiPlus();

    const Matrix2 a = rotatedObservable(0.0);
    const Matrix2 aPrime = rotatedObservable(90.0);
    const Matrix2 b = rotatedObservable(45.0);
    const Matrix2 bPrime = rotatedObservable(-45.0);

    const ChshResult exact =
        calculateCHSH(state, a, aPrime, b, bPrime);

    std::cout << "Exact theoretical correlations:\n";
    std::cout << "  E(a,b)     = " << exact.eAB << '\n';
    std::cout << "  E(a,b')    = " << exact.eABPrime << '\n';
    std::cout << "  E(a',b)    = " << exact.eAPrimeB << '\n';
    std::cout << "  E(a',b')   = " << exact.eAPrimeBPrime << '\n';
    std::cout << "  S          = " << exact.S << '\n';

    const std::size_t shotsPerSetting = 25'000;
    std::mt19937 generator(20261001);

    const ExperimentalCHSH observed =
        runFiniteShotCHSH(
            state,
            a,
            aPrime,
            b,
            bPrime,
            shotsPerSetting,
            generator
        );

    std::cout << "\nFinite-shot estimated correlations:\n";
    std::cout << "  E(a,b)     = " << observed.eAB << '\n';
    std::cout << "  E(a,b')    = " << observed.eABPrime << '\n';
    std::cout << "  E(a',b)    = " << observed.eAPrimeB << '\n';
    std::cout << "  E(a',b')   = " << observed.eAPrimeBPrime << '\n';
    std::cout << "  S          = " << observed.S << '\n';

    std::cout << "\nDecision boundary used by the model:\n";
    std::cout << "  Classical CHSH bound: |S| <= 2\n";
    std::cout
        << "  Tsirelson bound: |S| <= "
        << 2.0 * std::sqrt(2.0)
        << '\n';

    /*
     * This threshold comparison is a property of the modeled statistic,
     * not a proof that every physical implementation is loophole-free.
     * Real Bell tests must address locality, detector efficiency,
     * measurement independence, statistical significance, and experimental
     * systematics.
     */
    if (std::abs(exact.S) > 2.0) {
        std::cout
            << "The theoretical configuration exceeds the classical CHSH "
            << "bound.\n";
    }
}

void demonstrateRelativePhase() {
    std::cout << "\n=== Relative phase case ===\n";

    const BellState plus = phiPlus();
    const BellState minus = phiMinus();

    printProbabilities(plus);
    printProbabilities(minus);

    const auto x = pauliX();
    const auto z = pauliZ();

    std::cout
        << "Phi+ <XX> = "
        << plus.correlation(x, x)
        << '\n';

    std::cout
        << "Phi- <XX> = "
        << minus.correlation(x, x)
        << '\n';

    std::cout
        << "Phi+ <ZZ> = "
        << plus.correlation(z, z)
        << '\n';

    std::cout
        << "Phi- <ZZ> = "
        << minus.correlation(z, z)
        << '\n';

    std::cout
        << "The computational-basis probabilities are unchanged by the "
        << "relative sign, but a phase-sensitive joint measurement changes.\n";
}

void demonstrateFailureHandling() {
    std::cout << "\n=== State validation and failure handling ===\n";

    try {
        BellState invalid(
            "Invalid state",
            {Complex(1), Complex(1), Complex(0), Complex(0)}
        );

        (void)invalid;
    } catch (const std::invalid_argument& error) {
        std::cout
            << "Rejected invalid state: "
            << error.what()
            << '\n';
    }

    try {
        const BellState state = phiPlus();
        std::mt19937 generator(1);

        estimateCorrelation(
            state,
            pauliX(),
            pauliX(),
            0,
            generator
        );
    } catch (const std::invalid_argument& error) {
        std::cout
            << "Rejected invalid experiment: "
            << error.what()
            << '\n';
    }
}

int main() {
    try {
        std::cout
            << "Entanglement: Bell States and Non-Classical Correlations\n"
            << std::string(62, '=')
            << '\n';

        printProbabilities(phiPlus());
        printProbabilities(phiMinus());
        printProbabilities(psiPlus());
        printProbabilities(psiMinus());

        compareBellCorrelationSignatures();
        demonstrateLocalVersusJointInformation();
        demonstrateRelativePhase();
        demonstrateCHSHCaseStudy();
        demonstrateFailureHandling();

        std::cout
            << "\n=== Case study complete ===\n"
            << "The model separates Bell-state construction, local statistics, "
            << "joint correlations, relative phase, finite-shot estimation, "
            << "and CHSH analysis.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
