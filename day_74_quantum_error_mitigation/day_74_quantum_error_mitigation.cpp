#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Quantum Error Mitigation Governance Engine.
 *
 * Models:
 * - Quantum experiments and noise channels.
 * - Measurement uncertainty.
 * - Zero-noise extrapolation.
 * - Readout mitigation.
 * - Probabilistic error cancellation overhead.
 * - Experiment quality and resource policies.
 * - Merge-like release eligibility for experiment results.
 *
 * Compile:
 * g++ -std=c++17 -O2 qem.cpp -o qem
 */

enum class NoiseModel {
    BitFlip,
    PhaseFlip,
    Depolarizing
};

enum class MitigationMethod {
    None,
    Readout,
    ZNE,
    PEC
};

enum class ExperimentStatus {
    Created,
    Running,
    Completed,
    Failed
};

std::string toString(MitigationMethod method) {
    switch (method) {
        case MitigationMethod::None: return "None";
        case MitigationMethod::Readout: return "Readout";
        case MitigationMethod::ZNE: return "ZNE";
        case MitigationMethod::PEC: return "PEC";
    }

    throw std::invalid_argument("Unknown mitigation method");
}

void validateProbability(double value, const std::string& name) {
    if (!std::isfinite(value) || value < 0.0 || value > 1.0) {
        throw std::invalid_argument(name + " must be in [0,1]");
    }
}

struct QubitState {
    double probabilityZero;
    double probabilityOne;

    QubitState(double p0, double p1)
        : probabilityZero(p0), probabilityOne(p1) {

        validateProbability(p0, "Probability zero");
        validateProbability(p1, "Probability one");

        if (std::abs(p0 + p1 - 1.0) > 1e-9) {
            throw std::invalid_argument("State is not normalized");
        }
    }

    double expectationZ() const {
        return probabilityZero - probabilityOne;
    }
};

class NoiseChannel {
private:
    NoiseModel model;
    double rate;

public:
    NoiseChannel(NoiseModel model, double rate)
        : model(model), rate(rate) {
        validateProbability(rate, "Noise rate");
    }

    double apply(double expectation, double scale = 1.0) const {
        if (!std::isfinite(scale) || scale <= 0.0) {
            throw std::invalid_argument("Invalid noise scale");
        }

        double p = rate * scale;

        if (p > 1.0) {
            throw std::invalid_argument("Scaled noise exceeds one");
        }

        switch (model) {
            case NoiseModel::BitFlip:
                return expectation * (1.0 - 2.0 * p);

            case NoiseModel::PhaseFlip:
                return expectation;

            case NoiseModel::Depolarizing:
                return expectation * (1.0 - 4.0 * p / 3.0);
        }

        throw std::invalid_argument("Unsupported noise model");
    }

    double getRate() const {
        return rate;
    }

    NoiseModel getModel() const {
        return model;
    }
};

struct Measurement {
    double estimate;
    double uncertainty;
    int shots;
    int plusCount;
};

class MeasurementEngine {
private:
    std::mt19937 generator;

public:
    explicit MeasurementEngine(unsigned int seed)
        : generator(seed) {}

    Measurement measure(
        double expectation,
        int shots,
        double readoutError
    ) {
        if (shots <= 0) {
            throw std::invalid_argument("Shots must be positive");
        }

        validateProbability(readoutError, "Readout error");

        double observed =
            expectation * (1.0 - 2.0 * readoutError);

        double pPlus = (1.0 + observed) / 2.0;

        std::bernoulli_distribution distribution(pPlus);

        int plus = 0;

        for (int i = 0; i < shots; ++i) {
            plus += distribution(generator);
        }

        double estimate = 2.0 * plus / shots - 1.0;

        double uncertainty = std::sqrt(
            std::max(0.0, 1.0 - estimate * estimate) / shots
        );

        return {
            estimate,
            uncertainty,
            shots,
            plus
        };
    }
};

class ReadoutMitigator {
public:
    static double correct(
        double observed,
        double error01,
        double error10
    ) {
        validateProbability(observed, "Observed probability");
        validateProbability(error01, "Error 01");
        validateProbability(error10, "Error 10");

        double denominator = 1.0 - error01 - error10;

        if (std::abs(denominator) < 1e-12) {
            throw std::runtime_error("Singular calibration matrix");
        }

        double result = (observed - error01) / denominator;

        return std::clamp(result, 0.0, 1.0);
    }

    static double correctExpectation(
        double expectation,
        double error01,
        double error10
    ) {
        double p1 = (1.0 - expectation) / 2.0;
        return 1.0 - 2.0 * correct(p1, error01, error10);
    }
};

class ZeroNoiseExtrapolator {
public:
    static double extrapolate(
        const std::vector<std::pair<double, double>>& points
    ) {
        if (points.size() < 2) {
            throw std::invalid_argument("At least two points required");
        }

        auto sorted = points;

        std::sort(
            sorted.begin(),
            sorted.end(),
            [](const auto& a, const auto& b) {
                return a.first < b.first;
            }
        );

        for (const auto& point : sorted) {
            if (
                !std::isfinite(point.first) ||
                !std::isfinite(point.second) ||
                point.first <= 0.0
            ) {
                throw std::invalid_argument("Invalid extrapolation point");
            }
        }

        double x1 = sorted[0].first;
        double y1 = sorted[0].second;
        double x2 = sorted[1].first;
        double y2 = sorted[1].second;

        if (std::abs(x2 - x1) < 1e-12) {
            throw std::invalid_argument("Duplicate noise scales");
        }

        return y1 - x1 * (y2 - y1) / (x2 - x1);
    }
};

struct Experiment {
    std::string id;
    std::string owner;
    QubitState state;
    NoiseChannel channel;
    int shots;
    double readoutError;
    ExperimentStatus status;

    Experiment(
        std::string id,
        std::string owner,
        QubitState state,
        NoiseChannel channel,
        int shots,
        double readoutError
    )
        : id(std::move(id)),
          owner(std::move(owner)),
          state(state),
          channel(channel),
          shots(shots),
          readoutError(readoutError),
          status(ExperimentStatus::Created) {

        if (this->id.empty() || this->owner.empty()) {
            throw std::invalid_argument("Experiment identity is required");
        }

        if (shots <= 0) {
            throw std::invalid_argument("Shots must be positive");
        }

        validateProbability(readoutError, "Readout error");
    }

    void transition(ExperimentStatus next) {
        bool valid =
            (status == ExperimentStatus::Created &&
             next == ExperimentStatus::Running) ||
            (status == ExperimentStatus::Running &&
             (next == ExperimentStatus::Completed ||
              next == ExperimentStatus::Failed));

        if (!valid) {
            throw std::logic_error("Invalid experiment transition");
        }

        status = next;
    }
};

struct MitigationResult {
    MitigationMethod method;
    double estimate;
    double uncertainty;
    double bias;
    int shots;
    bool eligible;
    std::vector<std::string> violations;
};

class GovernancePolicy {
private:
    double maximumNoise;
    int minimumShots;
    double maximumUncertainty;
    std::set<MitigationMethod> permittedMethods;

public:
    GovernancePolicy(
        double maximumNoise,
        int minimumShots,
        double maximumUncertainty,
        std::set<MitigationMethod> permittedMethods
    )
        : maximumNoise(maximumNoise),
          minimumShots(minimumShots),
          maximumUncertainty(maximumUncertainty),
          permittedMethods(std::move(permittedMethods)) {

        validateProbability(maximumNoise, "Maximum noise");

        if (minimumShots <= 0) {
            throw std::invalid_argument("Minimum shots must be positive");
        }

        if (
            !std::isfinite(maximumUncertainty) ||
            maximumUncertainty <= 0
        ) {
            throw std::invalid_argument("Invalid uncertainty threshold");
        }

        if (this->permittedMethods.empty()) {
            throw std::invalid_argument("No permitted mitigation methods");
        }
    }

    std::vector<std::string> evaluate(
        const Experiment& experiment,
        const MitigationResult& result
    ) const {
        std::vector<std::string> violations;

        if (experiment.channel.getRate() > maximumNoise) {
            violations.push_back("Noise threshold exceeded");
        }

        if (result.shots < minimumShots) {
            violations.push_back("Insufficient shot budget");
        }

        if (
            !permittedMethods.count(result.method)
        ) {
            violations.push_back("Mitigation method not permitted");
        }

        if (result.uncertainty > maximumUncertainty) {
            violations.push_back("Uncertainty threshold exceeded");
        }

        if (!std::isfinite(result.estimate)) {
            violations.push_back("Invalid numerical estimate");
        }

        return violations;
    }
};

class ExperimentEngine {
private:
    MeasurementEngine measurement;

public:
    explicit ExperimentEngine(unsigned int seed)
        : measurement(seed) {}

    std::vector<MitigationResult> execute(Experiment& experiment) {
        experiment.transition(ExperimentStatus::Running);

        try {
            double ideal = experiment.state.expectationZ();

            double noisy = experiment.channel.apply(ideal);

            Measurement raw = measurement.measure(
                noisy,
                experiment.shots,
                experiment.readoutError
            );

            std::vector<MitigationResult> results;

            results.push_back({
                MitigationMethod::None,
                raw.estimate,
                raw.uncertainty,
                raw.estimate - ideal,
                raw.shots,
                false,
                {}
            });

            double corrected = ReadoutMitigator::correctExpectation(
                raw.estimate,
                experiment.readoutError,
                experiment.readoutError
            );

            double correctedUncertainty =
                raw.uncertainty /
                std::abs(1.0 - 2.0 * experiment.readoutError);

            results.push_back({
                MitigationMethod::Readout,
                corrected,
                correctedUncertainty,
                corrected - ideal,
                experiment.shots,
                false,
                {}
            });

            std::vector<std::pair<double, double>> observations;

            for (double scale : {1.0, 1.5, 2.0}) {
                observations.push_back({
                    scale,
                    experiment.channel.apply(ideal, scale)
                });
            }

            double zne = ZeroNoiseExtrapolator::extrapolate(
                observations
            );

            results.push_back({
                MitigationMethod::ZNE,
                zne,
                raw.uncertainty * 1.5,
                zne - ideal,
                experiment.shots * 3,
                false,
                {}
            });

            experiment.transition(ExperimentStatus::Completed);
            return results;

        } catch (...) {
            experiment.transition(ExperimentStatus::Failed);
            throw;
        }
    }
};

void printResults(
    const std::vector<MitigationResult>& results,
    const Experiment& experiment,
    const GovernancePolicy& policy
) {
    std::cout << "\nQUANTUM ERROR MITIGATION GOVERNANCE\n";
    std::cout << std::string(84, '=') << "\n";

    std::cout
        << std::left << std::setw(14) << "Method"
        << std::right << std::setw(14) << "Estimate"
        << std::setw(14) << "Uncertainty"
        << std::setw(14) << "Bias"
        << std::setw(14) << "Decision"
        << "\n";

    for (const auto& result : results) {
        auto violations = policy.evaluate(experiment, result);
        bool eligible = violations.empty();

        std::cout
            << std::left << std::setw(14)
            << toString(result.method)
            << std::right << std::fixed << std::setprecision(6)
            << std::setw(14) << result.estimate
            << std::setw(14) << result.uncertainty
            << std::setw(14) << result.bias
            << std::setw(14) << (eligible ? "ACCEPT" : "REJECT")
            << "\n";

        for (const auto& violation : violations) {
            std::cout << "  - " << violation << "\n";
        }
    }
}

int main() {
    try {
        Experiment experiment(
            "QEM-2026-001",
            "research-team",
            QubitState(1.0, 0.0),
            NoiseChannel(NoiseModel::BitFlip, 0.08),
            30000,
            0.04
        );

        GovernancePolicy policy(
            0.20,
            1000,
            0.10,
            {
                MitigationMethod::None,
                MitigationMethod::Readout,
                MitigationMethod::ZNE
            }
        );

        ExperimentEngine engine(42);

        auto results = engine.execute(experiment);

        printResults(results, experiment, policy);

        std::cout << "\nExperiment status: "
                  << (experiment.status == ExperimentStatus::Completed
                      ? "COMPLETED"
                      : "NOT COMPLETED")
                  << "\n";

        // A singular calibration matrix must be rejected.
        try {
            ReadoutMitigator::correct(0.5, 0.5, 0.5);
            throw std::runtime_error("Expected singular matrix rejection");
        } catch (const std::runtime_error& error) {
            std::cout << "Calibration edge-case test: "
                      << error.what() << "\n";
        }

    } catch (const std::exception& error) {
        std::cerr << "Experiment error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
