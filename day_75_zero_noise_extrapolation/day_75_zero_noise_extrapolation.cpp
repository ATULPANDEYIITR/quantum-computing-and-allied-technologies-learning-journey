#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Zero-Noise Extrapolation: C++17 Implementation
 *
 * Models a quantum experiment as a collection of noise-scaled
 * observable measurements.
 *
 * Implements:
 * - Experiment and measurement domain types
 * - Noise scaling
 * - Linear and quadratic regression
 * - Richardson extrapolation
 * - Measurement uncertainty
 * - Shot-budget enforcement
 * - Merge-free experiment state management
 */

enum class ExtrapolationMethod {
    Linear,
    Quadratic,
    Richardson
};

enum class ExperimentState {
    Created,
    Running,
    Completed,
    Failed
};

struct Measurement {
    double scale;
    double observable;
    double standardError;
    std::size_t shots;
};

struct NoiseConfiguration {
    double idealValue;
    double linearCoefficient;
    double quadraticCoefficient;
};

struct ExtrapolationResult {
    double estimate;
    std::vector<double> coefficients;
};

struct ExperimentReport {
    ExperimentState state;
    double idealValue;
    double baseline;
    double mitigated;
    double baselineError;
    double mitigationError;
    std::vector<Measurement> measurements;
};

class ValidationError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class ExperimentError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class ShotBudget {
private:
    std::size_t maximum_;
    std::size_t consumed_ = 0;

public:
    explicit ShotBudget(std::size_t maximum)
        : maximum_(maximum) {
        if (maximum < 2) {
            throw ValidationError("Shot budget must be >= 2.");
        }
    }

    void reserve(std::size_t shots) {
        if (shots < 2) {
            throw ValidationError("Each measurement needs >= 2 shots.");
        }

        if (shots > maximum_ - consumed_) {
            throw ExperimentError("Shot budget exceeded.");
        }

        consumed_ += shots;
    }

    std::size_t consumed() const {
        return consumed_;
    }

    std::size_t remaining() const {
        return maximum_ - consumed_;
    }
};

class NoiseModel {
private:
    NoiseConfiguration configuration_;
    std::mt19937 generator_;

public:
    NoiseModel(
        NoiseConfiguration configuration,
        unsigned int seed = 42
    ) : configuration_(configuration), generator_(seed) {

        if (!std::isfinite(configuration.idealValue) ||
            configuration.idealValue < -1.0 ||
            configuration.idealValue > 1.0) {
            throw ValidationError("Ideal observable must be in [-1, 1].");
        }

        if (!std::isfinite(configuration.linearCoefficient) ||
            !std::isfinite(configuration.quadraticCoefficient)) {
            throw ValidationError("Noise coefficients must be finite.");
        }
    }

    double expectation(double scale) const {
        if (!std::isfinite(scale) || scale < 1.0) {
            throw ValidationError("Noise scale must be >= 1.");
        }

        double value =
            configuration_.idealValue +
            configuration_.linearCoefficient * scale +
            configuration_.quadraticCoefficient * scale * scale;

        return std::clamp(value, -1.0, 1.0);
    }

    Measurement measure(double scale, std::size_t shots) {
        if (!std::isfinite(scale) || scale < 1.0 || shots < 2) {
            throw ValidationError("Invalid measurement configuration.");
        }

        double probability =
            (1.0 + expectation(scale)) / 2.0;

        std::bernoulli_distribution distribution(probability);

        std::size_t positive = 0;

        for (std::size_t i = 0; i < shots; ++i) {
            positive += distribution(generator_) ? 1 : 0;
        }

        double estimate =
            2.0 * static_cast<double>(positive) /
            static_cast<double>(shots) - 1.0;

        double standardError = std::sqrt(
            std::max(0.0, 1.0 - estimate * estimate) /
            static_cast<double>(shots)
        );

        return {
            scale,
            estimate,
            standardError,
            shots
        };
    }

    double idealValue() const {
        return configuration_.idealValue;
    }
};

/*
 * Partial-pivoting Gaussian elimination.
 * Suitable for the small polynomial systems used in ZNE.
 */
std::vector<double> solveLinearSystem(
    std::vector<std::vector<double>> matrix,
    std::vector<double> vector
) {
    const std::size_t n = vector.size();

    if (n == 0 || matrix.size() != n) {
        throw ExperimentError("Invalid linear system.");
    }

    for (const auto& row : matrix) {
        if (row.size() != n) {
            throw ExperimentError("Matrix must be square.");
        }
    }

    for (std::size_t col = 0; col < n; ++col) {
        std::size_t pivot = col;

        for (std::size_t row = col + 1; row < n; ++row) {
            if (std::abs(matrix[row][col]) >
                std::abs(matrix[pivot][col])) {
                pivot = row;
            }
        }

        if (std::abs(matrix[pivot][col]) < 1e-12) {
            throw ExperimentError("Singular regression system.");
        }

        std::swap(matrix[col], matrix[pivot]);
        std::swap(vector[col], vector[pivot]);

        double divisor = matrix[col][col];

        for (std::size_t j = col; j < n; ++j) {
            matrix[col][j] /= divisor;
        }

        vector[col] /= divisor;

        for (std::size_t row = 0; row < n; ++row) {
            if (row == col) continue;

            double factor = matrix[row][col];

            for (std::size_t j = col; j < n; ++j) {
                matrix[row][j] -= factor * matrix[col][j];
            }

            vector[row] -= factor * vector[col];
        }
    }

    return vector;
}

class PolynomialExtrapolator {
public:
    static ExtrapolationResult fit(
        const std::vector<Measurement>& measurements,
        int degree
    ) {
        if (degree < 1 || degree > 2) {
            throw ValidationError("Supported degrees are 1 and 2.");
        }

        if (measurements.size() <
            static_cast<std::size_t>(degree + 1)) {
            throw ExperimentError("Insufficient measurements.");
        }

        std::vector<double> x;
        std::vector<double> y;

        for (const auto& measurement : measurements) {
            if (!std::isfinite(measurement.scale) ||
                measurement.scale < 1.0 ||
                !std::isfinite(measurement.observable)) {
                throw ValidationError("Invalid measurement.");
            }

            x.push_back(measurement.scale);
            y.push_back(measurement.observable);
        }

        std::sort(x.begin(), x.end());

        if (std::adjacent_find(x.begin(), x.end()) != x.end()) {
            throw ValidationError("Noise scales must be unique.");
        }

        const std::size_t n = degree + 1;

        std::vector<double> powers(2 * degree + 1, 0.0);

        for (double value : x) {
            double power = 1.0;

            for (int p = 0; p <= 2 * degree; ++p) {
                powers[p] += power;
                power *= value;
            }
        }

        std::vector<std::vector<double>> matrix(
            n, std::vector<double>(n, 0.0)
        );

        std::vector<double> vector(n, 0.0);

        for (std::size_t row = 0; row < n; ++row) {
            for (std::size_t col = 0; col < n; ++col) {
                matrix[row][col] = powers[row + col];
            }

            for (std::size_t i = 0; i < measurements.size(); ++i) {
                vector[row] +=
                    measurements[i].observable *
                    std::pow(measurements[i].scale, row);
            }
        }

        auto coefficients = solveLinearSystem(
            matrix,
            vector
        );

        return {coefficients[0], coefficients};
    }

    static double richardson(
        const std::vector<Measurement>& measurements
    ) {
        if (measurements.size() != 2) {
            throw ExperimentError(
                "Richardson extrapolation requires two measurements."
            );
        }

        const auto& a = measurements[0];
        const auto& b = measurements[1];

        if (a.scale == b.scale) {
            throw ValidationError("Noise scales must differ.");
        }

        return (
            b.scale * a.observable -
            a.scale * b.observable
        ) / (b.scale - a.scale);
    }
};

class ZNEEngine {
private:
    NoiseModel model_;
    ShotBudget budget_;
    std::size_t shotsPerScale_;
    ExperimentState state_ = ExperimentState::Created;

public:
    ZNEEngine(
        NoiseModel model,
        std::size_t shotsPerScale,
        std::size_t maximumShots
    )
        : model_(std::move(model)),
          budget_(maximumShots),
          shotsPerScale_(shotsPerScale) {

        if (shotsPerScale < 2) {
            throw ValidationError("Invalid shots per scale.");
        }
    }

    ExperimentState state() const {
        return state_;
    }

    ExperimentReport execute(
        const std::vector<double>& scales,
        ExtrapolationMethod method
    ) {
        if (state_ == ExperimentState::Running) {
            throw ExperimentError("Experiment already running.");
        }

        if (state_ == ExperimentState::Completed) {
            throw ExperimentError("Completed experiment cannot be rerun.");
        }

        state_ = ExperimentState::Running;

        try {
            if (scales.size() < 2) {
                throw ValidationError("At least two scales are required.");
            }

            std::vector<double> ordered = scales;

            for (double scale : ordered) {
                if (!std::isfinite(scale) || scale < 1.0) {
                    throw ValidationError("Invalid noise scale.");
                }
            }

            std::sort(ordered.begin(), ordered.end());

            if (std::adjacent_find(
                ordered.begin(), ordered.end()
            ) != ordered.end()) {
                throw ValidationError("Duplicate noise scales.");
            }

            if (method == ExtrapolationMethod::Richardson) {
                ordered.resize(2);
            }

            std::vector<Measurement> measurements;

            for (double scale : ordered) {
                budget_.reserve(shotsPerScale_);

                measurements.push_back(
                    model_.measure(scale, shotsPerScale_)
                );
            }

            double estimate = 0.0;

            if (method == ExtrapolationMethod::Richardson) {
                estimate = PolynomialExtrapolator::richardson(
                    measurements
                );
            } else {
                int degree =
                    method == ExtrapolationMethod::Linear ? 1 : 2;

                estimate = PolynomialExtrapolator::fit(
                    measurements,
                    degree
                ).estimate;
            }

            double baseline = measurements.front().observable;
            double ideal = model_.idealValue();

            state_ = ExperimentState::Completed;

            return {
                state_,
                ideal,
                baseline,
                estimate,
                std::abs(baseline - ideal),
                std::abs(estimate - ideal),
                measurements
            };
        } catch (...) {
            state_ = ExperimentState::Failed;
            throw;
        }
    }
};

void printReport(
    const std::string& method,
    const ExperimentReport& report
) {
    std::cout << "\nMethod: " << method << "\n"
              << "Ideal reference: " << report.idealValue << "\n"
              << "Noisy baseline: " << report.baseline << "\n"
              << "Mitigated estimate: " << report.mitigated << "\n"
              << "Baseline error: " << report.baselineError << "\n"
              << "Mitigation error: " << report.mitigationError << "\n";

    std::cout << "Measurements:\n";

    for (const auto& measurement : report.measurements) {
        std::cout
            << "  Scale=" << measurement.scale
            << ", Observable=" << measurement.observable
            << ", SE=" << measurement.standardError
            << ", Shots=" << measurement.shots
            << "\n";
    }
}

void runTests() {
    std::vector<Measurement> points = {
        {1.0, 0.8, 0.01, 10000},
        {2.0, 0.5, 0.01, 10000},
        {3.0, 0.15, 0.01, 10000}
    };

    auto fitted = PolynomialExtrapolator::fit(points, 2);

    if (std::abs(fitted.estimate - 1.0) > 1e-9) {
        throw ExperimentError("Quadratic regression test failed.");
    }

    double richardson = PolynomialExtrapolator::richardson({
        {1.0, 0.8, 0.01, 10000},
        {2.0, 0.6, 0.01, 10000}
    });

    if (std::abs(richardson - 1.0) > 1e-9) {
        throw ExperimentError("Richardson test failed.");
    }

    std::cout << "All C++ self-tests passed.\n";
}

int main() {
    try {
        std::cout << std::fixed << std::setprecision(6);

        runTests();

        NoiseConfiguration configuration{
            0.85,
            -0.12,
            -0.025
        };

        NoiseModel model(configuration, 42);

        ZNEEngine engine(
            std::move(model),
            20000,
            1000000
        );

        const std::vector<double> scales{
            1.0, 1.5, 2.0, 2.5
        };

        const std::map<
            ExtrapolationMethod,
            std::string
        > methods{
            {ExtrapolationMethod::Linear, "Linear"},
            {ExtrapolationMethod::Quadratic, "Quadratic"},
            {ExtrapolationMethod::Richardson, "Richardson"}
        };

        for (const auto& [method, name] : methods) {
            NoiseModel experimentModel(configuration, 42);

            ZNEEngine experiment(
                std::move(experimentModel),
                20000,
                1000000
            );

            auto report = experiment.execute(scales, method);
            printReport(name, report);
        }

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "Experiment error: "
                  << error.what() << "\n";
        return 1;
    }
}
