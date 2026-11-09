#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Quantum Hardware Architecture Comparison Engine
 *
 * Standard: C++17
 * Dependencies: Standard Template Library only.
 *
 * Implements:
 * - Architecture domain modeling
 * - Weighted performance evaluation
 * - Application-specific suitability
 * - Repository of architecture profiles
 * - Pairwise comparison
 * - Merge-independent evaluation state
 */

enum class ArchitectureType {
    Superconducting,
    TrappedIon,
    NeutralAtom,
    Photonic,
    SemiconductorSpin,
    Topological
};

struct EvaluationCriteria {
    double gateSpeed;
    double coherence;
    double connectivity;
    double scalability;
    double engineeringMaturity;
    double controlIntegration;
    double errorCorrectionProgress;
};

struct ComparisonWeights {
    EvaluationCriteria weights{
        0.15, 0.15, 0.10, 0.20, 0.15, 0.10, 0.15
    };

    void validate() const {
        const auto& w = weights;

        const std::array<double, 7> values{
            w.gateSpeed,
            w.coherence,
            w.connectivity,
            w.scalability,
            w.engineeringMaturity,
            w.controlIntegration,
            w.errorCorrectionProgress
        };

        for (double value : values) {
            if (!std::isfinite(value) || value < 0.0) {
                throw std::invalid_argument(
                    "Weights must be finite and non-negative."
                );
            }
        }

        const double total = std::accumulate(
            values.begin(), values.end(), 0.0
        );

        if (std::abs(total - 1.0) > 1e-9) {
            throw std::invalid_argument(
                "Weights must sum to 1."
            );
        }
    }
};

struct Architecture {
    ArchitectureType type;
    std::string name;
    std::string physicalQubit;
    std::string environment;

    EvaluationCriteria scores;

    std::vector<std::string> strengths;
    std::vector<std::string> limitations;

    std::string evidenceStatus;

    void validate() const {
        if (name.empty() || physicalQubit.empty()) {
            throw std::invalid_argument(
                "Architecture identity cannot be empty."
            );
        }

        const std::array<double, 7> values{
            scores.gateSpeed,
            scores.coherence,
            scores.connectivity,
            scores.scalability,
            scores.engineeringMaturity,
            scores.controlIntegration,
            scores.errorCorrectionProgress
        };

        for (double value : values) {
            if (
                !std::isfinite(value) ||
                value < 1.0 ||
                value > 5.0
            ) {
                throw std::invalid_argument(
                    "Architecture scores must be between 1 and 5."
                );
            }
        }

        if (strengths.empty() || limitations.empty()) {
            throw std::invalid_argument(
                "Strengths and limitations are required."
            );
        }
    }
};

class ArchitectureRegistry {
private:
    std::map<std::string, Architecture> architectures;

public:
    void add(const Architecture& architecture) {
        architecture.validate();

        if (architectures.count(architecture.name)) {
            throw std::invalid_argument(
                "Duplicate architecture: " + architecture.name
            );
        }

        architectures.emplace(
            architecture.name,
            architecture
        );
    }

    const Architecture& get(const std::string& name) const {
        auto iterator = architectures.find(name);

        if (iterator == architectures.end()) {
            throw std::out_of_range(
                "Architecture not found: " + name
            );
        }

        return iterator->second;
    }

    std::vector<Architecture> all() const {
        std::vector<Architecture> result;

        for (const auto& [name, architecture] : architectures) {
            result.push_back(architecture);
        }

        return result;
    }

    std::size_t size() const {
        return architectures.size();
    }
};

class ComparisonEngine {
private:
    ComparisonWeights policy;

public:
    explicit ComparisonEngine(
        const ComparisonWeights& weights
    ) : policy(weights) {
        policy.validate();
    }

    double evaluate(const Architecture& architecture) const {
        const auto& s = architecture.scores;
        const auto& w = policy.weights;

        return
            s.gateSpeed * w.gateSpeed +
            s.coherence * w.coherence +
            s.connectivity * w.connectivity +
            s.scalability * w.scalability +
            s.engineeringMaturity * w.engineeringMaturity +
            s.controlIntegration * w.controlIntegration +
            s.errorCorrectionProgress *
                w.errorCorrectionProgress;
    }

    std::vector<std::pair<Architecture, double>> rank(
        const ArchitectureRegistry& registry
    ) const {
        std::vector<std::pair<Architecture, double>> results;

        for (const auto& architecture : registry.all()) {
            results.emplace_back(
                architecture,
                evaluate(architecture)
            );
        }

        std::sort(
            results.begin(),
            results.end(),
            [](const auto& first, const auto& second) {
                return first.second > second.second;
            }
        );

        return results;
    }

    void compare(
        const Architecture& first,
        const Architecture& second
    ) const {
        const double firstScore = evaluate(first);
        const double secondScore = evaluate(second);

        std::cout << "\nPAIRWISE COMPARISON\n";

        std::cout << first.name << ": "
                  << firstScore << "/5\n";

        std::cout << second.name << ": "
                  << secondScore << "/5\n";

        std::cout << "Difference: "
                  << firstScore - secondScore << "\n";
    }
};

class ApplicationEvaluator {
public:
    static std::string assess(
        const Architecture& architecture,
        const std::string& application
    ) {
        const auto& s = architecture.scores;

        double average = (
            s.gateSpeed +
            s.coherence +
            s.connectivity +
            s.scalability +
            s.errorCorrectionProgress
        ) / 5.0;

        std::string assessment =
            average >= 3.5
                ? "Potentially suitable"
                : "Requires further evaluation";

        return architecture.name + " for " +
               application + ": " + assessment;
    }
};

ArchitectureRegistry buildRegistry() {
    ArchitectureRegistry registry;

    registry.add({
        ArchitectureType::Superconducting,
        "Superconducting",
        "Josephson-junction circuit",
        "Millikelvin dilution refrigerator",
        {5, 2, 3, 4, 5, 4, 4},
        {
            "Fast microwave gates",
            "Established fabrication processes",
            "Strong control integration"
        },
        {
            "Cryogenic requirements",
            "Coherence limitations",
            "Calibration complexity"
        },
        "Relatively mature ecosystem"
    });

    registry.add({
        ArchitectureType::TrappedIon,
        "Trapped Ion",
        "Electromagnetically confined atomic ion",
        "Ultra-high vacuum and lasers",
        {2, 5, 4, 3, 4, 3, 4},
        {
            "Long coherence",
            "High-fidelity gates",
            "Flexible interactions"
        },
        {
            "Slow gate operations",
            "Optical engineering complexity"
        },
        "Established experimental ecosystem"
    });

    registry.add({
        ArchitectureType::NeutralAtom,
        "Neutral Atom",
        "Laser-trapped neutral atom",
        "Ultra-high vacuum and optical traps",
        {3, 4, 5, 5, 3, 3, 3},
        {
            "Large atom arrays",
            "Programmable interaction graphs",
            "Potential register scalability"
        },
        {
            "Atom loss",
            "Rydberg-state sensitivity",
            "Gate fidelity challenges"
        },
        "Rapidly developing ecosystem"
    });

    registry.add({
        ArchitectureType::Photonic,
        "Photonic",
        "Single photons and optical modes",
        "Optical systems",
        {4, 4, 3, 4, 2, 3, 3},
        {
            "Optical networking compatibility",
            "Potential room-temperature operation"
        },
        {
            "Photon loss",
            "Detector requirements",
            "Probabilistic operations in many designs"
        },
        "Developing ecosystem"
    });

    registry.add({
        ArchitectureType::SemiconductorSpin,
        "Semiconductor Spin",
        "Electron or nuclear spin",
        "Cryogenic solid-state device",
        {4, 4, 2, 4, 2, 4, 2},
        {
            "Semiconductor fabrication compatibility",
            "Compact device potential",
            "Electronic integration"
        },
        {
            "Device variability",
            "Control complexity",
            "Connectivity limitations"
        },
        "Developing experimental ecosystem"
    });

    registry.add({
        ArchitectureType::Topological,
        "Topological",
        "Proposed non-Abelian anyonic states",
        "Platform-dependent specialized conditions",
        {2, 5, 2, 3, 1, 1, 1},
        {
            "Potential protection against certain local errors"
        },
        {
            "Difficult experimental realization",
            "Usable topological qubits unproven",
            "Fault-tolerant operation unestablished"
        },
        "Highly experimental"
    });

    return registry;
}

void runTests(
    const ArchitectureRegistry& registry,
    const ComparisonEngine& engine
) {
    if (registry.size() != 6) {
        throw std::runtime_error(
            "Expected six architecture profiles."
        );
    }

    if (engine.evaluate(registry.get("Trapped Ion")) <= 0) {
        throw std::runtime_error("Invalid evaluation.");
    }

    bool unknownRejected = false;

    try {
        registry.get("Unknown");
    } catch (const std::out_of_range&) {
        unknownRejected = true;
    }

    if (!unknownRejected) {
        throw std::runtime_error(
            "Unknown architecture validation failed."
        );
    }

    std::cout << "Validation tests passed.\n";
}

int main() {
    try {
        std::cout << std::fixed << std::setprecision(3);

        const ArchitectureRegistry registry = buildRegistry();

        ComparisonWeights weights;
        const ComparisonEngine engine(weights);

        runTests(registry, engine);

        const auto rankings = engine.rank(registry);

        std::cout << "\nQUANTUM HARDWARE COMPARISON\n";
        std::cout << "Illustrative qualitative scores, not measured benchmarks.\n";

        int position = 1;

        for (const auto& [architecture, score] : rankings) {
            std::cout << "\n" << position++
                      << ". " << architecture.name << "\n";

            std::cout << "Score: " << score << "/5\n";
            std::cout << "Physical qubit: "
                      << architecture.physicalQubit << "\n";

            std::cout << "Environment: "
                      << architecture.environment << "\n";

            std::cout << "Evidence: "
                      << architecture.evidenceStatus << "\n";

            std::cout << "Strengths:\n";

            for (const auto& strength : architecture.strengths) {
                std::cout << "  + " << strength << "\n";
            }

            std::cout << "Limitations:\n";

            for (const auto& limitation : architecture.limitations) {
                std::cout << "  - " << limitation << "\n";
            }
        }

        engine.compare(
            registry.get("Superconducting"),
            registry.get("Trapped Ion")
        );

        std::cout << "\nAPPLICATION ASSESSMENT\n";

        std::cout << ApplicationEvaluator::assess(
            registry.get("Neutral Atom"),
            "Large-scale programmable quantum simulation"
        ) << "\n";

        return 0;

    } catch (const std::exception& exception) {
        std::cerr << "Execution error: "
                  << exception.what() << "\n";

        return 1;
    }
}
