#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Hilbert Spaces
 * Mathematical framework
 *
 * Industry-style case study:
 * Signal reconstruction and denoising using orthogonal projection.
 *
 * A digital signal is represented as a vector in R^n. The standard Euclidean
 * inner product turns R^n into a finite-dimensional Hilbert space.
 *
 * The system progressively implements:
 *
 *   vectors
 *   inner products
 *   norms
 *   orthogonality
 *   Gram-Schmidt orthonormalization
 *   projection
 *   least-squares approximation
 *   Fourier-like basis functions
 *   signal generation
 *   noise
 *   reconstruction
 *   error metrics
 *   validation
 *   complexity analysis
 *
 * The implementation uses only the C++17 standard library.
 */

namespace hilbert {

using Vector = std::vector<double>;
using Matrix = std::vector<Vector>;

constexpr double EPSILON = 1e-10;


// ============================================================================
// 1. BASIC VECTOR OPERATIONS
// ============================================================================

void validateSameDimension(const Vector& a, const Vector& b) {
    if (a.size() != b.size()) {
        throw std::invalid_argument(
            "Vectors must have the same dimension."
        );
    }
}

Vector add(const Vector& a, const Vector& b) {
    validateSameDimension(a, b);

    Vector result(a.size());

    for (std::size_t i = 0; i < a.size(); ++i) {
        result[i] = a[i] + b[i];
    }

    return result;
}

Vector subtract(const Vector& a, const Vector& b) {
    validateSameDimension(a, b);

    Vector result(a.size());

    for (std::size_t i = 0; i < a.size(); ++i) {
        result[i] = a[i] - b[i];
    }

    return result;
}

Vector scale(double scalar, const Vector& vector) {
    Vector result = vector;

    for (double& value : result) {
        value *= scalar;
    }

    return result;
}


// ============================================================================
// 2. HILBERT-SPACE GEOMETRY
// ============================================================================

double innerProduct(const Vector& a, const Vector& b) {
    validateSameDimension(a, b);

    return std::inner_product(
        a.begin(),
        a.end(),
        b.begin(),
        0.0
    );
}

double squaredNorm(const Vector& vector) {
    return innerProduct(vector, vector);
}

double norm(const Vector& vector) {
    return std::sqrt(squaredNorm(vector));
}

double distance(const Vector& a, const Vector& b) {
    return norm(subtract(a, b));
}

bool approximatelyZero(double value, double tolerance = EPSILON) {
    return std::abs(value) <= tolerance;
}

bool orthogonal(
    const Vector& a,
    const Vector& b,
    double tolerance = EPSILON
) {
    return approximatelyZero(
        innerProduct(a, b),
        tolerance
    );
}

Vector normalize(const Vector& vector) {
    const double length = norm(vector);

    if (length <= EPSILON) {
        throw std::invalid_argument(
            "The zero vector cannot be normalized."
        );
    }

    return scale(1.0 / length, vector);
}


// ============================================================================
// 3. GRAM-SCHMIDT ORTHONORMALIZATION
// ============================================================================

std::vector<Vector> gramSchmidt(
    const std::vector<Vector>& vectors,
    double tolerance = EPSILON
) {
    if (vectors.empty()) {
        throw std::invalid_argument(
            "At least one vector is required."
        );
    }

    std::vector<Vector> basis;

    for (const Vector& vector : vectors) {
        Vector residual = vector;

        /*
         * Classical Gram-Schmidt:
         *
         *     u_k = v_k - sum_j <q_j,v_k> q_j
         *
         * followed by
         *
         *     q_k = u_k / ||u_k||.
         *
         * The residual must not vanish. If it does, the new vector is
         * linearly dependent on the previous vectors.
         */
        for (const Vector& q : basis) {
            const double coefficient =
                innerProduct(q, vector);

            residual = subtract(
                residual,
                scale(coefficient, q)
            );
        }

        const double residualNorm = norm(residual);

        if (residualNorm <= tolerance) {
            throw std::invalid_argument(
                "Input vectors are linearly dependent "
                "or numerically nearly dependent."
            );
        }

        basis.push_back(
            scale(1.0 / residualNorm, residual)
        );
    }

    return basis;
}


// ============================================================================
// 4. ORTHOGONAL PROJECTION
// ============================================================================

Vector projectOntoOrthonormalBasis(
    const Vector& vector,
    const std::vector<Vector>& basis
) {
    if (basis.empty()) {
        return Vector(vector.size(), 0.0);
    }

    Vector projection(vector.size(), 0.0);

    /*
     * If q_1,...,q_k is orthonormal, then
     *
     *     P_M x = sum_i <q_i,x> q_i.
     *
     * This is the unique best approximation to x from the closed subspace M
     * in a finite-dimensional Hilbert space.
     */
    for (const Vector& q : basis) {
        const double coefficient =
            innerProduct(q, vector);

        projection = add(
            projection,
            scale(coefficient, q)
        );
    }

    return projection;
}


// ============================================================================
// 5. MATRIX UTILITIES
// ============================================================================

Matrix transpose(const Matrix& matrix) {
    if (matrix.empty()) {
        return {};
    }

    const std::size_t rows = matrix.size();
    const std::size_t columns = matrix.front().size();

    for (const Vector& row : matrix) {
        if (row.size() != columns) {
            throw std::invalid_argument(
                "Matrix contains rows of different lengths."
            );
        }
    }

    Matrix result(columns, Vector(rows));

    for (std::size_t row = 0; row < rows; ++row) {
        for (std::size_t column = 0; column < columns; ++column) {
            result[column][row] = matrix[row][column];
        }
    }

    return result;
}

Vector matrixVectorMultiply(
    const Matrix& matrix,
    const Vector& vector
) {
    Vector result;
    result.reserve(matrix.size());

    for (const Vector& row : matrix) {
        if (row.size() != vector.size()) {
            throw std::invalid_argument(
                "Matrix and vector dimensions are incompatible."
            );
        }

        result.push_back(
            std::inner_product(
                row.begin(),
                row.end(),
                vector.begin(),
                0.0
            )
        );
    }

    return result;
}


// ============================================================================
// 6. FOURIER-LIKE ORTHONORMAL BASIS
// ============================================================================

Vector makeSineBasis(
    std::size_t frequency,
    std::size_t samples
) {
    if (samples < 2) {
        throw std::invalid_argument(
            "At least two signal samples are required."
        );
    }

    Vector basis(samples);

    /*
     * A normalized discrete sine-like vector.
     *
     * Continuous theory uses functions such as
     *
     *     q_k(t) = sqrt(2/L) sin(k*pi*t/L).
     *
     * In the digital case, sampled versions provide a finite-dimensional
     * approximation to a function-space Hilbert space.
     */
    for (std::size_t n = 0; n < samples; ++n) {
        const double t =
            static_cast<double>(n) /
            static_cast<double>(samples - 1);

        basis[n] =
            std::sqrt(2.0) *
            std::sin(
                frequency *
                M_PI *
                t
            );
    }

    /*
     * Normalize numerically because sampling and discretization alter exact
     * continuous orthonormality.
     */
    return normalize(basis);
}


// ============================================================================
// 7. SIGNAL MODEL
// ============================================================================

struct Signal {
    Vector samples;
    double sampleRate;

    Signal(Vector samples, double sampleRate)
        : samples(std::move(samples)),
          sampleRate(sampleRate) {

        if (this->samples.empty()) {
            throw std::invalid_argument(
                "A signal must contain at least one sample."
            );
        }

        if (!std::isfinite(this->sampleRate) ||
            this->sampleRate <= 0.0) {
            throw std::invalid_argument(
                "Sample rate must be positive and finite."
            );
        }
    }

    std::size_t size() const {
        return samples.size();
    }

    double duration() const {
        return static_cast<double>(samples.size()) /
               sampleRate;
    }
};


// ============================================================================
// 8. SYNTHETIC SIGNAL GENERATION
// ============================================================================

Signal generateCleanSignal(
    std::size_t sampleCount,
    double sampleRate
) {
    Vector samples(sampleCount);

    const double frequencyOne = 3.0;
    const double frequencyTwo = 7.0;

    for (std::size_t i = 0; i < sampleCount; ++i) {
        const double time =
            static_cast<double>(i) /
            sampleRate;

        /*
         * The clean signal contains two known basis components.
         *
         *     s(t) = 1.4 sin(2*pi*f1*t)
         *          + 0.6 cos(2*pi*f2*t)
         */
        samples[i] =
            1.4 *
            std::sin(
                2.0 * M_PI *
                frequencyOne *
                time
            )
            +
            0.6 *
            std::cos(
                2.0 * M_PI *
                frequencyTwo *
                time
            );
    }

    return Signal(
        std::move(samples),
        sampleRate
    );
}

Signal addNoise(
    const Signal& clean,
    double amplitude,
    unsigned seed = 42
) {
    if (amplitude < 0.0 ||
        !std::isfinite(amplitude)) {
        throw std::invalid_argument(
            "Noise amplitude must be non-negative and finite."
        );
    }

    std::mt19937 generator(seed);

    std::uniform_real_distribution<double> distribution(
        -amplitude,
        amplitude
    );

    Vector noisy = clean.samples;

    for (double& value : noisy) {
        value += distribution(generator);
    }

    return Signal(
        std::move(noisy),
        clean.sampleRate
    );
}


// ============================================================================
// 9. BASIS CONSTRUCTION FOR THE SIGNAL
// ============================================================================

std::vector<Vector> buildSignalBasis(
    std::size_t sampleCount,
    const std::vector<std::size_t>& frequencies
) {
    std::vector<Vector> basis;

    for (std::size_t frequency : frequencies) {
        if (frequency == 0) {
            throw std::invalid_argument(
                "Frequency indices must be positive."
            );
        }

        Vector sine(sampleCount);
        Vector cosine(sampleCount);

        for (std::size_t i = 0; i < sampleCount; ++i) {
            const double time =
                static_cast<double>(i) /
                static_cast<double>(sampleCount);

            const double angle =
                2.0 *
                M_PI *
                static_cast<double>(frequency) *
                time;

            sine[i] = std::sin(angle);
            cosine[i] = std::cos(angle);
        }

        basis.push_back(normalize(sine));
        basis.push_back(normalize(cosine));
    }

    return basis;
}


// ============================================================================
// 10. LEAST-SQUARES SIGNAL RECONSTRUCTION
// ============================================================================

struct ReconstructionResult {
    Vector reconstructed;
    Vector residual;
    std::vector<double> coefficients;
};

ReconstructionResult reconstructSignal(
    const Signal& noisySignal,
    const std::vector<Vector>& rawBasis
) {
    if (rawBasis.empty()) {
        throw std::invalid_argument(
            "At least one basis vector is required."
        );
    }

    /*
     * Orthonormalizing the basis is important because the simple coefficient
     *
     *     c_i = <q_i,x>
     *
     * is valid only for an orthonormal basis.
     */
    const std::vector<Vector> orthonormalBasis =
        gramSchmidt(rawBasis);

    Vector reconstructed =
        projectOntoOrthonormalBasis(
            noisySignal.samples,
            orthonormalBasis
        );

    Vector residual =
        subtract(
            noisySignal.samples,
            reconstructed
        );

    /*
     * Coordinates relative to the orthonormal basis are the projection
     * coefficients.
     */
    std::vector<double> coefficients;

    coefficients.reserve(
        orthonormalBasis.size()
    );

    for (const Vector& q : orthonormalBasis) {
        coefficients.push_back(
            innerProduct(
                q,
                noisySignal.samples
            )
        );
    }

    return {
        std::move(reconstructed),
        std::move(residual),
        std::move(coefficients)
    };
}


// ============================================================================
// 11. ERROR METRICS
// ============================================================================

double meanSquaredError(
    const Vector& actual,
    const Vector& predicted
) {
    validateSameDimension(actual, predicted);

    if (actual.empty()) {
        throw std::invalid_argument(
            "Cannot calculate MSE for empty vectors."
        );
    }

    double total = 0.0;

    for (std::size_t i = 0; i < actual.size(); ++i) {
        const double error =
            actual[i] - predicted[i];

        total += error * error;
    }

    return total /
           static_cast<double>(actual.size());
}

double rootMeanSquaredError(
    const Vector& actual,
    const Vector& predicted
) {
    return std::sqrt(
        meanSquaredError(actual, predicted)
    );
}

double signalEnergy(const Vector& signal) {
    return squaredNorm(signal);
}


// ============================================================================
// 12. ENERGY-BASED HILBERT-SPACE ANALYSIS
// ============================================================================

void analyzeOrthogonalDecomposition(
    const Vector& original,
    const Vector& projection,
    const Vector& residual
) {
    const double originalEnergy =
        squaredNorm(original);

    const double projectionEnergy =
        squaredNorm(projection);

    const double residualEnergy =
        squaredNorm(residual);

    std::cout
        << "\nEnergy analysis\n"
        << "---------------\n"
        << "Original energy   = "
        << originalEnergy << '\n'
        << "Projection energy = "
        << projectionEnergy << '\n'
        << "Residual energy   = "
        << residualEnergy << '\n'
        << "Projection + residual = "
        << projectionEnergy + residualEnergy << '\n'
        << "Energy error = "
        << std::abs(
            originalEnergy -
            projectionEnergy -
            residualEnergy
        )
        << '\n';

    /*
     * Orthogonal decomposition gives the Pythagorean relation:
     *
     *     ||x||² = ||Px||² + ||x-Px||².
     *
     * This is the geometric foundation of least-squares approximation.
     */
}


// ============================================================================
// 13. SECURITY AND ROBUSTNESS VALIDATION
// ============================================================================

void validateSignalForProcessing(
    const Signal& signal
) {
    /*
     * Production numerical systems should not assume input is valid.
     * NaN and infinity can silently propagate through calculations and
     * corrupt downstream results.
     */
    for (double sample : signal.samples) {
        if (!std::isfinite(sample)) {
            throw std::invalid_argument(
                "Signal contains NaN or infinite values."
            );
        }
    }
}

void validateBasis(
    const std::vector<Vector>& basis,
    std::size_t expectedDimension
) {
    if (basis.empty()) {
        throw std::invalid_argument(
            "Basis cannot be empty."
        );
    }

    for (const Vector& vector : basis) {
        if (vector.size() != expectedDimension) {
            throw std::invalid_argument(
                "Basis dimension does not match signal dimension."
            );
        }

        if (!std::all_of(
                vector.begin(),
                vector.end(),
                [](double value) {
                    return std::isfinite(value);
                }
            )) {
            throw std::invalid_argument(
                "Basis contains a non-finite value."
            );
        }
    }
}


// ============================================================================
// 14. REPORTING
// ============================================================================

void printVector(
    const std::string& name,
    const Vector& vector,
    std::size_t maximumElements = 8
) {
    std::cout << name << " = [";

    const std::size_t count =
        std::min(
            maximumElements,
            vector.size()
        );

    for (std::size_t i = 0; i < count; ++i) {
        std::cout
            << std::fixed
            << std::setprecision(4)
            << vector[i];

        if (i + 1 < count) {
            std::cout << ", ";
        }
    }

    if (vector.size() > maximumElements) {
        std::cout << ", ...";
    }

    std::cout << "]\n";
}

void printCoefficients(
    const std::vector<double>& coefficients
) {
    std::cout
        << "\nProjection coefficients\n"
        << "-----------------------\n";

    for (std::size_t i = 0; i < coefficients.size(); ++i) {
        std::cout
            << "c[" << i << "] = "
            << std::fixed
            << std::setprecision(8)
            << coefficients[i]
            << '\n';
    }
}


// ============================================================================
// 15. CASE STUDY PIPELINE
// ============================================================================

void runCaseStudy() {
    std::cout
        << "============================================================\n"
        << "HILBERT-SPACE SIGNAL RECONSTRUCTION CASE STUDY\n"
        << "============================================================\n";

    /*
     * System requirements:
     *
     * - sample a clean signal;
     * - introduce bounded noise;
     * - model the useful signal using a known subspace;
     * - project the noisy signal onto that subspace;
     * - measure reconstruction quality;
     * - verify orthogonality and energy decomposition.
     */
    constexpr std::size_t SAMPLE_COUNT = 1000;
    constexpr double SAMPLE_RATE = 100.0;
    constexpr double NOISE_AMPLITUDE = 0.8;

    Signal clean =
        generateCleanSignal(
            SAMPLE_COUNT,
            SAMPLE_RATE
        );

    Signal noisy =
        addNoise(
            clean,
            NOISE_AMPLITUDE
        );

    validateSignalForProcessing(clean);
    validateSignalForProcessing(noisy);

    /*
     * The system assumes the useful signal is dominated by frequencies
     * represented by this model space.
     *
     * A larger basis can represent more signals but can also capture noise.
     * A smaller basis provides stronger compression but may discard genuine
     * information.
     */
    const std::vector<std::size_t> frequencies = {
        3,
        7
    };

    const std::vector<Vector> rawBasis =
        buildSignalBasis(
            SAMPLE_COUNT,
            frequencies
        );

    validateBasis(
        rawBasis,
        SAMPLE_COUNT
    );

    ReconstructionResult result =
        reconstructSignal(
            noisy,
            rawBasis
        );

    printVector(
        "Clean signal",
        clean.samples
    );

    printVector(
        "Noisy signal",
        noisy.samples
    );

    printVector(
        "Reconstructed signal",
        result.reconstructed
    );

    printVector(
        "Residual",
        result.residual
    );

    printCoefficients(
        result.coefficients
    );

    const double noisyError =
        rootMeanSquaredError(
            clean.samples,
            noisy.samples
        );

    const double reconstructedError =
        rootMeanSquaredError(
            clean.samples,
            result.reconstructed
        );

    std::cout
        << "\nSignal-quality metrics\n"
        << "----------------------\n"
        << "Noisy RMSE         = "
        << noisyError << '\n'
        << "Reconstructed RMSE = "
        << reconstructedError << '\n';

    analyzeOrthogonalDecomposition(
        noisy.samples,
        result.reconstructed,
        result.residual
    );

    /*
     * Projection property:
     *
     * The residual should be orthogonal to every basis vector in the model
     * subspace.
     */
    const std::vector<Vector> orthonormalBasis =
        gramSchmidt(rawBasis);

    std::cout
        << "\nResidual orthogonality checks\n"
        << "-----------------------------\n";

    for (std::size_t i = 0;
         i < orthonormalBasis.size();
         ++i) {

        const double value =
            innerProduct(
                orthonormalBasis[i],
                result.residual
            );

        std::cout
            << "<q[" << i << "], residual> = "
            << std::scientific
            << value
            << '\n';
    }

    /*
     * Bessel/Parseval interpretation:
     *
     * For an orthonormal basis that spans the complete finite-dimensional
     * space, coefficient energy equals vector energy.
     *
     * For a proper subspace, coefficient energy is less than or equal to
     * total energy. The missing energy is represented by the orthogonal
     * residual.
     */
    const double coefficientEnergy =
        std::accumulate(
            result.coefficients.begin(),
            result.coefficients.end(),
            0.0,
            [](double sum, double coefficient) {
                return sum + coefficient * coefficient;
            }
        );

    const double noisyEnergy =
        signalEnergy(noisy.samples);

    std::cout
        << "\nBessel inequality check\n"
        << "-----------------------\n"
        << "Coefficient energy = "
        << coefficientEnergy << '\n'
        << "Signal energy      = "
        << noisyEnergy << '\n'
        << "Inequality holds   = "
        << std::boolalpha
        << (coefficientEnergy <= noisyEnergy + 1e-8)
        << '\n';
}


// ============================================================================
// 16. EDGE-CASE TESTS
// ============================================================================

void runTests() {
    std::cout
        << "\n============================================================\n"
        << "SELF-TESTS\n"
        << "============================================================\n";

    {
        const Vector vector = {3.0, 4.0};

        if (std::abs(norm(vector) - 5.0) > EPSILON) {
            throw std::runtime_error(
                "Norm test failed."
            );
        }
    }

    {
        const Vector a = {1.0, 0.0};
        const Vector b = {0.0, 1.0};

        if (!orthogonal(a, b)) {
            throw std::runtime_error(
                "Orthogonality test failed."
            );
        }
    }

    {
        const Vector vector = normalize(
            Vector{3.0, 4.0}
        );

        if (std::abs(norm(vector) - 1.0) > EPSILON) {
            throw std::runtime_error(
                "Normalization test failed."
            );
        }
    }

    {
        const auto basis =
            gramSchmidt(
                std::vector<Vector>{
                    {1.0, 1.0},
                    {1.0, -1.0}
                }
            );

        if (!orthogonal(
                basis[0],
                basis[1]
            )) {
            throw std::runtime_error(
                "Gram-Schmidt test failed."
            );
        }
    }

    {
        bool failedCorrectly = false;

        try {
            normalize(
                Vector{0.0, 0.0}
            );
        } catch (const std::invalid_argument&) {
            failedCorrectly = true;
        }

        if (!failedCorrectly) {
            throw std::runtime_error(
                "Zero-vector validation test failed."
            );
        }
    }

    {
        bool failedCorrectly = false;

        try {
            gramSchmidt(
                std::vector<Vector>{
                    {1.0, 2.0},
                    {2.0, 4.0}
                }
            );
        } catch (const std::invalid_argument&) {
            failedCorrectly = true;
        }

        if (!failedCorrectly) {
            throw std::runtime_error(
                "Dependent-vector validation test failed."
            );
        }
    }

    {
        bool failedCorrectly = false;

        try {
            Signal invalid(
                Vector{1.0, std::numeric_limits<double>::quiet_NaN()},
                100.0
            );

            validateSignalForProcessing(invalid);
        } catch (const std::invalid_argument&) {
            failedCorrectly = true;
        }

        if (!failedCorrectly) {
            throw std::runtime_error(
                "NaN validation test failed."
            );
        }
    }

    std::cout
        << "All tests passed.\n";
}


// ============================================================================
// 17. COMPLEXITY AND DESIGN NOTES
// ============================================================================

void printDesignNotes() {
    std::cout
        << "\n============================================================\n"
        << "DESIGN AND COMPLEXITY NOTES\n"
        << "============================================================\n";

    std::cout
        << R"(
Vector addition:
    O(n) time, O(n) output space.

Inner product:
    O(n) time and O(1) auxiliary space.

Norm:
    O(n) time.

Projection onto k orthonormal vectors in R^n:
    O(nk) time.

Classical Gram-Schmidt for k vectors of dimension n:
    approximately O(nk^2).

Dense matrix-vector multiplication:
    O(n^2).

Signal reconstruction:
    approximately O(nk) once the orthonormal basis is available.

Important engineering trade-offs:

1. Classical Gram-Schmidt is simple and pedagogically useful, but can lose
   numerical orthogonality for ill-conditioned input.

2. Modified Gram-Schmidt generally improves numerical behavior.

3. Householder QR is preferred in many high-quality numerical linear-algebra
   implementations.

4. Dense vectors consume O(n) memory. Sparse signals or sparse operators can
   require substantially less storage.

5. Increasing the model-space dimension can reduce approximation error but
   may cause the model to represent noise as well.

6. Floating-point computations require tolerances rather than exact equality.

7. Production implementations should validate dimensions, finite values,
   resource limits, and algorithmic conditioning.

8. In infinite-dimensional Hilbert spaces, computational representations are
   necessarily approximations. Convergence and completeness are mathematical
   properties that must be reasoned about independently of a finite program.

9. The finite-dimensional system implemented here is a genuine Hilbert space:
   R^n with the Euclidean inner product is complete.

10. Projection is central to least squares, Fourier approximation, signal
    denoising, numerical PDE methods, statistics, optimization, and many
    inverse problems.
)";
}


// ============================================================================
// 18. MAIN
// ============================================================================

} // namespace hilbert

int main() {
    try {
        std::cout
            << std::fixed
            << std::setprecision(10);

        hilbert::runTests();
        hilbert::runCaseStudy();
        hilbert::printDesignNotes();

        std::cout
            << "\nProgram completed successfully.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "\nFatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
