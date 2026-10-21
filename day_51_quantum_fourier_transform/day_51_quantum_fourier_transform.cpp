#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Quantum Fourier Transform fundamentals.
 *
 * This C++17 case study treats a quantum register as a state vector and
 * implements the QFT as a dense unitary transformation. It focuses on
 * numerical linear algebra, explicit matrix construction, periodicity,
 * inverse transformation, and measurement sampling.
 *
 * The direct implementation has O(N^2) time complexity and O(N) state
 * storage. A production-scale classical simulator would normally require
 * a much more specialized representation or an FFT-inspired approach.
 */

using Complex = std::complex<double>;
using State = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double PI = 3.141592653589793238462643383279502884;
constexpr double EPSILON = 1e-10;

bool isPowerOfTwo(std::size_t value) {
    return value > 0 && (value & (value - 1)) == 0;
}

void validateState(const State& state) {
    if (state.empty()) {
        throw std::invalid_argument("State vector cannot be empty.");
    }

    if (!isPowerOfTwo(state.size())) {
        throw std::invalid_argument(
            "State dimension must be a power of two."
        );
    }

    double normSquared = 0.0;

    for (const Complex& amplitude : state) {
        if (!std::isfinite(amplitude.real()) ||
            !std::isfinite(amplitude.imag())) {
            throw std::invalid_argument(
                "State contains a non-finite amplitude."
            );
        }

        normSquared += std::norm(amplitude);
    }

    if (std::abs(normSquared - 1.0) > EPSILON) {
        throw std::invalid_argument(
            "State vector must be normalized."
        );
    }
}

State normalize(const State& state) {
    if (state.empty()) {
        throw std::invalid_argument("Cannot normalize an empty state.");
    }

    double norm = std::sqrt(
        std::accumulate(
            state.begin(),
            state.end(),
            0.0,
            [](double sum, const Complex& value) {
                return sum + std::norm(value);
            }
        )
    );

    if (norm <= EPSILON) {
        throw std::invalid_argument(
            "Cannot normalize the zero vector."
        );
    }

    State result = state;

    for (Complex& amplitude : result) {
        amplitude /= norm;
    }

    return result;
}

State basisState(std::size_t qubits, std::size_t index) {
    if (qubits == 0) {
        throw std::invalid_argument(
            "A register must contain at least one qubit."
        );
    }

    if (qubits >= sizeof(std::size_t) * 8) {
        throw std::invalid_argument(
            "Requested register is too large for this simulator."
        );
    }

    const std::size_t dimension = std::size_t{1} << qubits;

    if (index >= dimension) {
        throw std::out_of_range(
            "Basis-state index is outside the register."
        );
    }

    State state(dimension, Complex{0.0, 0.0});
    state[index] = Complex{1.0, 0.0};

    return state;
}

State qft(const State& state, bool inverse = false) {
    validateState(state);

    const std::size_t n = state.size();
    const double sign = inverse ? -1.0 : 1.0;
    const double scale = 1.0 / std::sqrt(static_cast<double>(n));

    State result(n, Complex{0.0, 0.0});

    /*
     * The exponent is exp(+/- 2*pi*i*j*k/N).
     * The positive sign is used for the forward QFT here.
     */
    for (std::size_t k = 0; k < n; ++k) {
        Complex accumulator{0.0, 0.0};

        for (std::size_t j = 0; j < n; ++j) {
            const double angle =
                sign * 2.0 * PI *
                static_cast<double>(j * k) /
                static_cast<double>(n);

            const Complex phase{
                std::cos(angle),
                std::sin(angle)
            };

            accumulator += state[j] * phase;
        }

        result[k] = scale * accumulator;
    }

    return result;
}

Matrix qftMatrix(std::size_t qubits) {
    if (qubits == 0 ||
        qubits >= sizeof(std::size_t) * 8) {
        throw std::invalid_argument("Invalid qubit count.");
    }

    const std::size_t n = std::size_t{1} << qubits;
    const double scale = 1.0 / std::sqrt(static_cast<double>(n));

    Matrix matrix(
        n,
        std::vector<Complex>(n, Complex{0.0, 0.0})
    );

    for (std::size_t row = 0; row < n; ++row) {
        for (std::size_t column = 0; column < n; ++column) {
            const double angle =
                2.0 * PI *
                static_cast<double>(row * column) /
                static_cast<double>(n);

            matrix[row][column] =
                scale * Complex{
                    std::cos(angle),
                    std::sin(angle)
                };
        }
    }

    return matrix;
}

double unitarityError(const Matrix& matrix) {
    const std::size_t n = matrix.size();
    double maximumError = 0.0;

    for (std::size_t row = 0; row < n; ++row) {
        for (std::size_t column = 0; column < n; ++column) {
            Complex innerProduct{0.0, 0.0};

            for (std::size_t k = 0; k < n; ++k) {
                innerProduct +=
                    std::conj(matrix[row][k]) *
                    matrix[column][k];
            }

            const Complex expected =
                row == column
                    ? Complex{1.0, 0.0}
                    : Complex{0.0, 0.0};

            maximumError = std::max(
                maximumError,
                std::abs(innerProduct - expected)
            );
        }
    }

    return maximumError;
}

std::vector<double> probabilities(const State& state) {
    validateState(state);

    std::vector<double> result;
    result.reserve(state.size());

    for (const Complex& amplitude : state) {
        result.push_back(std::norm(amplitude));
    }

    return result;
}

std::vector<std::size_t> sampleMeasurements(
    const State& state,
    std::size_t shots
) {
    validateState(state);

    if (shots == 0) {
        throw std::invalid_argument("Number of shots must be positive.");
    }

    const auto distribution = probabilities(state);

    /*
     * std::discrete_distribution performs weighted sampling according to
     * the Born probabilities without requiring manually constructed bins.
     */
    std::random_device device;
    std::mt19937 generator(device());
    std::discrete_distribution<std::size_t> sampler(
        distribution.begin(),
        distribution.end()
    );

    std::vector<std::size_t> counts(state.size(), 0);

    for (std::size_t shot = 0; shot < shots; ++shot) {
        ++counts[sampler(generator)];
    }

    return counts;
}

double maximumVectorError(
    const State& first,
    const State& second
) {
    if (first.size() != second.size()) {
        throw std::invalid_argument(
            "States must have equal dimensions."
        );
    }

    double maximumError = 0.0;

    for (std::size_t i = 0; i < first.size(); ++i) {
        maximumError = std::max(
            maximumError,
            std::abs(first[i] - second[i])
        );
    }

    return maximumError;
}

void printState(
    const std::string& title,
    const State& state
) {
    std::cout << title << '\n';

    std::size_t width = 0;
    std::size_t dimension = state.size();

    while (dimension > 1) {
        ++width;
        dimension >>= 1;
    }

    std::cout << std::fixed << std::setprecision(5);

    for (std::size_t index = 0; index < state.size(); ++index) {
        std::string binary;

        for (std::size_t bit = width; bit > 0; --bit) {
            binary += ((index >> (bit - 1)) & 1U) ? '1' : '0';
        }

        std::cout
            << "  |" << binary << ">: "
            << state[index]
            << '\n';
    }
}

State periodicState() {
    State state(8, Complex{0.0, 0.0});
    state[0] = Complex{1.0, 0.0};
    state[4] = Complex{1.0, 0.0};

    return normalize(state);
}

void demonstratePeriodicity() {
    const State input = periodicState();
    const State transformed = qft(input);

    printState(
        "QFT of normalized (|000> + |100>) state:",
        transformed
    );

    const auto p = probabilities(transformed);

    std::cout << "Probabilities:\n";
    for (std::size_t index = 0; index < p.size(); ++index) {
        std::cout
            << "  " << index
            << ": " << std::fixed
            << std::setprecision(6)
            << p[index] << '\n';
    }
}

void demonstrateInverse() {
    const State original = normalize({
        Complex{1.0, 1.0},
        Complex{2.0, -1.0},
        Complex{-1.0, 0.5},
        Complex{0.25, -2.0}
    });

    const State transformed = qft(original);
    const State recovered = qft(transformed, true);

    const double error =
        maximumVectorError(original, recovered);

    std::cout
        << "\nInverse-QFT reconstruction error: "
        << std::scientific << error << '\n';

    if (error > 1e-9) {
        throw std::runtime_error(
            "Inverse QFT failed numerical verification."
        );
    }
}

void demonstrateMeasurements() {
    const State state = periodicState();
    const auto counts = sampleMeasurements(state, 2000);

    std::cout << "\nMeasurement counts from 2000 shots:\n";

    for (std::size_t index = 0; index < counts.size(); ++index) {
        std::cout
            << "  |"
            << std::bitset<3>(index)
            << ">: "
            << counts[index]
            << '\n';
    }
}

int main() {
    try {
        std::cout << "Quantum Fourier Transform fundamentals\n";
        std::cout << "======================================\n\n";

        const Matrix matrix = qftMatrix(3);
        const double matrixError = unitarityError(matrix);

        std::cout
            << "3-qubit QFT matrix unitarity error: "
            << std::scientific
            << matrixError
            << "\n";

        if (matrixError > 1e-9) {
            throw std::runtime_error(
                "QFT matrix failed unitarity verification."
            );
        }

        const State basis = basisState(3, 1);
        const State transformed = qft(basis);

        printState("\nQFT(|001>):", transformed);

        std::cout << "Measurement probabilities:\n";
        const auto basisProbabilities = probabilities(transformed);

        for (std::size_t index = 0;
             index < basisProbabilities.size();
             ++index) {
            std::cout
                << "  |"
                << std::bitset<3>(index)
                << ">: "
                << std::fixed
                << std::setprecision(6)
                << basisProbabilities[index]
                << '\n';
        }

        demonstratePeriodicity();
        demonstrateInverse();
        demonstrateMeasurements();

        std::cout << "\nAll QFT checks completed successfully.\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Execution failed: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
