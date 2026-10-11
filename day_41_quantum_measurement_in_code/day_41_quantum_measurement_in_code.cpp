#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Repository-independent quantum measurement case study:
 * an experimental analysis service for computational-basis measurements.
 *
 * The service accepts a prepared state's probability distribution, samples
 * shots, records outcome counts, and evaluates observed frequencies.
 * It models measurement statistics rather than quantum circuit evolution.
 */

using Distribution = std::map<std::string, double>;
using Counts = std::map<std::string, std::size_t>;

class MeasurementError : public std::runtime_error {
public:
    explicit MeasurementError(const std::string& message)
        : std::runtime_error(message) {}
};

class MeasurementRun {
public:
    MeasurementRun(std::size_t shots, Distribution theoretical, Counts counts)
        : shots_(shots), theoretical_(std::move(theoretical)),
          counts_(std::move(counts)) {
        if (shots_ == 0) {
            throw MeasurementError("Shot count must be positive.");
        }

        std::size_t total = 0;
        for (const auto& [outcome, count] : counts_) {
            (void)outcome;
            total += count;
        }
        if (total != shots_) {
            throw MeasurementError("Counts must sum to the shot count.");
        }
    }

    double observedProbability(const std::string& outcome) const {
        const auto found = counts_.find(outcome);
        if (found == counts_.end()) {
            throw MeasurementError("Unknown measurement outcome.");
        }
        return static_cast<double>(found->second) /
               static_cast<double>(shots_);
    }

    double standardError(const std::string& outcome) const {
        const double p = observedProbability(outcome);
        return std::sqrt(p * (1.0 - p) / static_cast<double>(shots_));
    }

    double totalVariationDistance() const {
        double distance = 0.0;
        for (const auto& [outcome, expected] : theoretical_) {
            distance += std::abs(observedProbability(outcome) - expected);
        }
        return distance / 2.0;
    }

    void print() const {
        std::cout << "\nShots: " << shots_ << '\n';
        std::cout << std::left << std::setw(12) << "Outcome"
                  << std::right << std::setw(12) << "Expected"
                  << std::setw(10) << "Count"
                  << std::setw(12) << "Observed"
                  << std::setw(13) << "Std. error" << '\n';

        for (const auto& [outcome, expected] : theoretical_) {
            std::cout << std::left << std::setw(12) << outcome
                      << std::right << std::fixed << std::setprecision(4)
                      << std::setw(12) << expected
                      << std::setw(10) << counts_.at(outcome)
                      << std::setw(12) << observedProbability(outcome)
                      << std::setw(13) << standardError(outcome) << '\n';
        }

        std::cout << "Total variation distance: "
                  << totalVariationDistance() << '\n';
    }

    const Counts& counts() const {
        return counts_;
    }

private:
    std::size_t shots_;
    Distribution theoretical_;
    Counts counts_;
};

class MeasurementEngine {
public:
    explicit MeasurementEngine(Distribution probabilities,
                              unsigned int seed = 2026)
        : probabilities_(std::move(probabilities)), generator_(seed) {
        validateDistribution();
    }

    MeasurementRun execute(std::size_t shots) {
        if (shots == 0) {
            throw MeasurementError("Shot count must be positive.");
        }

        std::vector<std::string> outcomes;
        std::vector<double> weights;
        Counts counts;

        for (const auto& [outcome, probability] : probabilities_) {
            outcomes.push_back(outcome);
            weights.push_back(probability);
            counts.emplace(outcome, 0);
        }

        // std::discrete_distribution samples indices according to relative
        // weights. Reproducibility depends on the standard library and seed.
        std::discrete_distribution<std::size_t> sampler(
            weights.begin(), weights.end());

        for (std::size_t shot = 0; shot < shots; ++shot) {
            ++counts[outcomes[sampler(generator_)]];
        }

        return MeasurementRun(shots, probabilities_, std::move(counts));
    }

private:
    Distribution probabilities_;
    std::mt19937 generator_;

    void validateDistribution() const {
        if (probabilities_.empty()) {
            throw MeasurementError("Distribution cannot be empty.");
        }

        const std::size_t width = probabilities_.begin()->first.size();
        if (width == 0) {
            throw MeasurementError("Outcomes cannot be empty.");
        }

        double total = 0.0;
        for (const auto& [outcome, probability] : probabilities_) {
            if (outcome.size() != width ||
                !std::all_of(outcome.begin(), outcome.end(),
                             [](char bit) { return bit == '0' || bit == '1'; })) {
                throw MeasurementError(
                    "Outcomes must be equal-width binary strings.");
            }
            if (!std::isfinite(probability) || probability < 0.0) {
                throw MeasurementError(
                    "Probabilities must be finite and non-negative.");
            }
            total += probability;
        }

        if (std::abs(total - 1.0) > 1e-9) {
            throw MeasurementError("Probabilities must sum to one.");
        }
    }
};

struct DetectorReport {
    std::string detector;
    std::size_t shots;
    double maximumDeviation;
    double tolerance;

    bool passes() const {
        return maximumDeviation <= tolerance;
    }
};

DetectorReport evaluateCalibration(const MeasurementRun& run,
                                   const std::string& detector,
                                   double maximumDeviation,
                                   double tolerance) {
    if (detector.empty() || !std::isfinite(maximumDeviation) ||
        !std::isfinite(tolerance) || maximumDeviation < 0.0 ||
        tolerance < 0.0) {
        throw MeasurementError("Invalid calibration report.");
    }

    // The caller supplies the largest deviation measured against a reference.
    return {detector, 0, maximumDeviation, tolerance};
}

int main() {
    try {
        std::cout << "Quantum detector measurement analysis\n";

        // Case study: calibration of a detector using a balanced qubit state.
        MeasurementEngine balancedQubit({{"0", 0.5}, {"1", 0.5}}, 17);
        const MeasurementRun calibration = balancedQubit.execute(5000);
        calibration.print();

        // A Bell state has correlated computational-basis outcomes. The
        // simulator samples 00 and 11 but never 01 or 10.
        MeasurementEngine bellState({{"00", 0.5}, {"11", 0.5}}, 81);
        const MeasurementRun correlatedRun = bellState.execute(3000);
        correlatedRun.print();

        if (correlatedRun.counts().at("01") != 0 ||
            correlatedRun.counts().at("10") != 0) {
            throw MeasurementError("Impossible Bell-state outcome observed.");
        }

        const DetectorReport report = evaluateCalibration(
            calibration, "detector-A", calibration.totalVariationDistance(),
            0.04);

        std::cout << "\nCalibration status: "
                  << (report.passes() ? "PASS" : "INVESTIGATE")
                  << "\nObserved distance: " << report.maximumDeviation
                  << "\nAllowed distance: " << report.tolerance << '\n';

        // Explicitly exercise invalid inputs rather than silently accepting
        // distributions that could make experimental statistics misleading.
        try {
            MeasurementEngine invalid({{"0", 0.4}, {"1", 0.4}});
            (void)invalid;
            throw std::logic_error("Invalid distribution was accepted.");
        } catch (const MeasurementError& error) {
            std::cout << "\nInvalid distribution rejected: "
                      << error.what() << '\n';
        }

        try {
            (void)balancedQubit.execute(0);
            throw std::logic_error("Zero shots were accepted.");
        } catch (const MeasurementError& error) {
            std::cout << "Invalid shot count rejected: "
                      << error.what() << '\n';
        }

        // Sampling requires O(shots) draws and O(outcomes) stored counts.
        // A real detector pipeline should also retain run IDs, timestamps,
        // calibration versions, and raw provider results for auditability.
    } catch (const std::exception& error) {
        std::cerr << "Measurement failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
