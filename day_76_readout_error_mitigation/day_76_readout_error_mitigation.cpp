#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Matrix = std::vector<std::vector<double>>;
using Vector = std::vector<double>;

enum class CheckStatus {
    PASS,
    FAIL,
    NOT_RUN
};

struct Calibration {
    int qubit;
    int shots;
    double p00;
    double p11;

    void validate() const {
        if (qubit < 0 || shots <= 0 ||
            !std::isfinite(p00) || !std::isfinite(p11) ||
            p00 < 0 || p00 > 1 ||
            p11 < 0 || p11 > 1) {
            throw std::invalid_argument("Invalid calibration.");
        }
    }

    Matrix assignmentMatrix() const {
        return {
            {p00, 1.0 - p11},
            {1.0 - p00, p11}
        };
    }
};

struct Measurement {
    std::map<std::string, int> counts;
    int totalShots() const {
        int total = 0;
        for (const auto& [state, count] : counts) {
            total += count;
        }
        return total;
    }
};

struct MitigationResult {
    Vector raw;
    Vector corrected;
    double residual = 0.0;
    int iterations = 0;
    bool converged = false;
};

class MatrixOperations {
public:
    static Matrix transpose(const Matrix& matrix) {
        Matrix result(
            matrix.front().size(),
            Vector(matrix.size())
        );

        for (std::size_t i = 0; i < matrix.size(); ++i) {
            for (std::size_t j = 0; j < matrix[i].size(); ++j) {
                result[j][i] = matrix[i][j];
            }
        }

        return result;
    }

    static Matrix multiply(const Matrix& a, const Matrix& b) {
        if (a.empty() || b.empty() ||
            a.front().size() != b.size()) {
            throw std::invalid_argument("Matrix dimension mismatch.");
        }

        Matrix result(
            a.size(),
            Vector(b.front().size(), 0.0)
        );

        for (std::size_t i = 0; i < a.size(); ++i) {
            for (std::size_t k = 0; k < b.size(); ++k) {
                for (std::size_t j = 0; j < b.front().size(); ++j) {
                    result[i][j] += a[i][k] * b[k][j];
                }
            }
        }

        return result;
    }

    static Vector multiply(const Matrix& a, const Vector& x) {
        Vector result(a.size(), 0.0);

        for (std::size_t i = 0; i < a.size(); ++i) {
            if (a[i].size() != x.size()) {
                throw std::invalid_argument("Dimension mismatch.");
            }

            for (std::size_t j = 0; j < x.size(); ++j) {
                result[i] += a[i][j] * x[j];
            }
        }

        return result;
    }

    static Matrix tensorProduct(const Matrix& a, const Matrix& b) {
        Matrix result(
            a.size() * b.size(),
            Vector(a.front().size() * b.front().size())
        );

        for (std::size_t i = 0; i < a.size(); ++i) {
            for (std::size_t j = 0; j < b.size(); ++j) {
                for (std::size_t k = 0; k < a[i].size(); ++k) {
                    for (std::size_t l = 0; l < b[j].size(); ++l) {
                        result[i * b.size() + j][
                            k * b.front().size() + l
                        ] = a[i][k] * b[j][l];
                    }
                }
            }
        }

        return result;
    }

    static Vector projectSimplex(const Vector& values) {
        Vector sorted = values;
        std::sort(sorted.begin(), sorted.end(), std::greater<double>());

        double cumulative = 0.0;
        double theta = 0.0;

        for (std::size_t i = 0; i < sorted.size(); ++i) {
            cumulative += sorted[i];
            const double candidate =
                (cumulative - 1.0) / static_cast<double>(i + 1);

            if (sorted[i] > candidate) {
                theta = candidate;
            }
        }

        Vector result;
        result.reserve(values.size());

        for (double value : values) {
            result.push_back(std::max(0.0, value - theta));
        }

        return result;
    }

    static double norm(const Vector& vector) {
        double total = 0.0;

        for (double value : vector) {
            total += value * value;
        }

        return std::sqrt(total);
    }
};

class ReadoutGovernanceEngine {
private:
    std::vector<Calibration> calibrations;
    Matrix assignment;
    int version = 0;
    double regularization;
    double tolerance;

    void validateAssignment() const {
        if (assignment.empty()) {
            throw std::runtime_error("Missing assignment matrix.");
        }

        for (const auto& column :
             MatrixOperations::transpose(assignment)) {
            const double sum = std::accumulate(
                column.begin(), column.end(), 0.0
            );

            if (std::abs(sum - 1.0) > 1e-9) {
                throw std::runtime_error(
                    "Assignment matrix is not column stochastic."
                );
            }
        }
    }

public:
    explicit ReadoutGovernanceEngine(
        double lambda = 1e-8,
        double convergenceTolerance = 1e-10
    ) : regularization(lambda), tolerance(convergenceTolerance) {
        if (lambda < 0 || !std::isfinite(lambda) ||
            convergenceTolerance <= 0) {
            throw std::invalid_argument("Invalid engine parameters.");
        }
    }

    void calibrate(std::vector<Calibration> newCalibrations) {
        if (newCalibrations.empty()) {
            throw std::invalid_argument("No calibrations provided.");
        }

        std::sort(
            newCalibrations.begin(),
            newCalibrations.end(),
            [](const Calibration& a, const Calibration& b) {
                return a.qubit < b.qubit;
            }
        );

        for (std::size_t i = 0; i < newCalibrations.size(); ++i) {
            newCalibrations[i].validate();

            if (newCalibrations[i].qubit != static_cast<int>(i)) {
                throw std::invalid_argument(
                    "Missing or duplicate qubit calibration."
                );
            }
        }

        Matrix candidate = {{1.0}};

        for (const auto& calibration : newCalibrations) {
            candidate = MatrixOperations::tensorProduct(
                candidate,
                calibration.assignmentMatrix()
            );
        }

        // Commit only after all validations succeed.
        calibrations = std::move(newCalibrations);
        assignment = std::move(candidate);
        version++;

        validateAssignment();
    }

    Vector estimate(const Measurement& measurement) const {
        if (calibrations.empty()) {
            throw std::runtime_error("Calibration is required.");
        }

        const int qubits = static_cast<int>(calibrations.size());
        const int dimension = 1 << qubits;
        const int total = measurement.totalShots();

        if (total <= 0) {
            throw std::invalid_argument("No measurement shots.");
        }

        Vector probabilities(dimension, 0.0);

        for (const auto& [state, count] : measurement.counts) {
            if (static_cast<int>(state.size()) != qubits ||
                state.find_first_not_of("01") != std::string::npos ||
                count < 0) {
                throw std::invalid_argument(
                    "Invalid measurement bitstring or count."
                );
            }

            const int index = std::stoi(state, nullptr, 2);
            probabilities[index] +=
                static_cast<double>(count) / total;
        }

        return probabilities;
    }

    MitigationResult mitigate(
        const Measurement& measurement,
        int maxIterations = 10000
    ) const {
        if (maxIterations <= 0) {
            throw std::invalid_argument("Invalid iteration limit.");
        }

        const Vector observed = estimate(measurement);
        const Matrix at = MatrixOperations::transpose(assignment);

        Matrix ata = MatrixOperations::multiply(at, assignment);

        for (std::size_t i = 0; i < ata.size(); ++i) {
            ata[i][i] += regularization;
        }

        const Vector atq = MatrixOperations::multiply(at, observed);

        double lipschitz = 0.0;

        for (const auto& row : ata) {
            double sum = 0.0;

            for (double value : row) {
                sum += std::abs(value);
            }

            lipschitz = std::max(lipschitz, sum);
        }

        if (lipschitz <= 0) {
            throw std::runtime_error("Invalid optimization matrix.");
        }

        const double learningRate = 1.0 / lipschitz;

        Vector estimate = observed;
        bool converged = false;
        int iteration = 0;

        for (iteration = 1; iteration <= maxIterations; ++iteration) {
            Vector gradient =
                MatrixOperations::multiply(ata, estimate);

            for (std::size_t i = 0; i < gradient.size(); ++i) {
                gradient[i] -= atq[i];
            }

            Vector candidate = estimate;

            for (std::size_t i = 0; i < candidate.size(); ++i) {
                candidate[i] -= learningRate * gradient[i];
            }

            candidate = MatrixOperations::projectSimplex(candidate);

            double difference = 0.0;

            for (std::size_t i = 0; i < candidate.size(); ++i) {
                difference = std::max(
                    difference,
                    std::abs(candidate[i] - estimate[i])
                );
            }

            estimate = std::move(candidate);

            if (difference < tolerance) {
                converged = true;
                break;
            }
        }

        Vector predicted =
            MatrixOperations::multiply(assignment, estimate);

        Vector residual(observed.size());

        for (std::size_t i = 0; i < observed.size(); ++i) {
            residual[i] = predicted[i] - observed[i];
        }

        return {
            observed,
            estimate,
            MatrixOperations::norm(residual),
            std::min(iteration, maxIterations),
            converged
        };
    }

    const Matrix& getAssignment() const {
        return assignment;
    }

    int getVersion() const {
        return version;
    }
};

Measurement simulate(
    const Vector& trueDistribution,
    const Matrix& assignment,
    int shots,
    unsigned int seed = 42
) {
    if (shots <= 0 ||
        trueDistribution.size() != assignment.size()) {
        throw std::invalid_argument("Invalid simulation parameters.");
    }

    Vector observed =
        MatrixOperations::multiply(assignment, trueDistribution);

    std::mt19937 generator(seed);
    std::discrete_distribution<int> distribution(
        observed.begin(), observed.end()
    );

    const int qubits = static_cast<int>(
        std::log2(observed.size())
    );

    Measurement measurement;

    for (int i = 0; i < shots; ++i) {
        const int index = distribution(generator);

        std::string state;
        int value = index;

        for (int bit = 0; bit < qubits; ++bit) {
            state.push_back((value & 1) ? '1' : '0');
            value >>= 1;
        }

        std::reverse(state.begin(), state.end());
        measurement.counts[state]++;
    }

    return measurement;
}

int main() {
    try {
        std::cout << "READOUT ERROR MITIGATION ENGINE\n";
        std::cout << "========================================\n";

        ReadoutGovernanceEngine engine(1e-8);

        engine.calibrate({
            {0, 10000, 0.94, 0.91},
            {1, 10000, 0.96, 0.93}
        });

        const Vector trueDistribution = {
            0.70, 0.10, 0.15, 0.05
        };

        Measurement measurements = simulate(
            trueDistribution,
            engine.getAssignment(),
            50000
        );

        MitigationResult result = engine.mitigate(measurements);

        std::cout << "\nCalibration version: "
                  << engine.getVersion() << "\n";

        std::cout << "\nObserved counts:\n";

        for (const auto& [state, count] : measurements.counts) {
            std::cout << "|" << state << "> : "
                      << count << "\n";
        }

        std::cout << std::fixed << std::setprecision(6);

        std::cout << "\nCorrected distribution:\n";

        for (std::size_t i = 0; i < result.corrected.size(); ++i) {
            std::cout << i << ": "
                      << result.corrected[i] << "\n";
        }

        std::cout << "\nOptimization diagnostics:\n";
        std::cout << "Iterations: " << result.iterations << "\n";
        std::cout << "Converged: "
                  << (result.converged ? "YES" : "NO") << "\n";
        std::cout << "Residual: " << result.residual << "\n";

        const double probabilitySum = std::accumulate(
            result.corrected.begin(),
            result.corrected.end(),
            0.0
        );

        if (std::abs(probabilitySum - 1.0) > 1e-8) {
            throw std::runtime_error("Normalization failed.");
        }

        for (double probability : result.corrected) {
            if (probability < 0) {
                throw std::runtime_error(
                    "Negative probability detected."
                );
            }
        }

        std::cout << "\nProbability validation: PASS\n";

        // Demonstrate failure handling.
        try {
            Calibration invalid{0, 1000, 1.5, 0.9};
            invalid.validate();
        } catch (const std::invalid_argument& error) {
            std::cout << "Invalid calibration rejected: "
                      << error.what() << "\n";
        }

        std::cout << "\nExecution completed.\n";
    } catch (const std::exception& error) {
        std::cerr << "ENGINE FAILURE: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
