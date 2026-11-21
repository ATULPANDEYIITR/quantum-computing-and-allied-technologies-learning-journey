#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Quantum Machine Learning
 *
 * C++17 implementation of a QML resource evaluation engine.
 *
 * Engineering focus:
 * - Algorithm taxonomy
 * - Quantum state representation
 * - Statevector simulation
 * - Circuit resource estimation
 * - Hardware capability modeling
 * - Quantum workload classification
 * - Noise-aware execution eligibility
 * - Measurement uncertainty
 * - Merge-free, deterministic evaluation pipeline
 *
 * No external dependencies.
 */

namespace qml {

// ============================================================
// 1. DOMAIN TYPES
// ============================================================

enum class Algorithm {
    VariationalClassifier,
    QuantumNeuralNetwork,
    QuantumKernel,
    QuantumGenerative,
    QuantumReinforcement,
    VQE,
    QAOA,
    QuantumInspired
};

enum class Backend {
    Statevector,
    ShotBased,
    NoisySimulator,
    QuantumHardware
};

enum class WorkloadType {
    SupervisedLearning,
    SimilarityLearning,
    Optimization,
    Chemistry,
    GenerativeLearning,
    ReinforcementLearning
};

std::string toString(Algorithm algorithm) {
    switch (algorithm) {
        case Algorithm::VariationalClassifier:
            return "Variational Quantum Classifier";
        case Algorithm::QuantumNeuralNetwork:
            return "Quantum Neural Network";
        case Algorithm::QuantumKernel:
            return "Quantum Kernel";
        case Algorithm::QuantumGenerative:
            return "Quantum Generative Model";
        case Algorithm::QuantumReinforcement:
            return "Quantum Reinforcement Learning";
        case Algorithm::VQE:
            return "Variational Quantum Eigensolver";
        case Algorithm::QAOA:
            return "Quantum Approximate Optimization";
        case Algorithm::QuantumInspired:
            return "Quantum-Inspired Classical Method";
    }

    throw std::invalid_argument("Unknown algorithm.");
}

std::string toString(Backend backend) {
    switch (backend) {
        case Backend::Statevector:
            return "Statevector Simulator";
        case Backend::ShotBased:
            return "Shot-Based Simulator";
        case Backend::NoisySimulator:
            return "Noisy Simulator";
        case Backend::QuantumHardware:
            return "Quantum Hardware";
    }

    throw std::invalid_argument("Unknown backend.");
}

// ============================================================
// 2. QUANTUM HARDWARE PROFILE
// ============================================================

struct HardwareProfile {
    std::string name;
    int availableQubits;
    int maximumCircuitDepth;
    int maximumShots;
    double gateFidelity;
    double measurementFidelity;
    bool supportsEntanglement;
    bool available;

    void validate() const {
        if (name.empty()) {
            throw std::invalid_argument("Hardware name is required.");
        }

        if (availableQubits < 1 || maximumCircuitDepth < 1 ||
            maximumShots < 1) {
            throw std::invalid_argument("Invalid hardware capacity.");
        }

        if (!std::isfinite(gateFidelity) ||
            gateFidelity <= 0 || gateFidelity > 1) {
            throw std::invalid_argument("Invalid gate fidelity.");
        }

        if (!std::isfinite(measurementFidelity) ||
            measurementFidelity <= 0 ||
            measurementFidelity > 1) {
            throw std::invalid_argument(
                "Invalid measurement fidelity."
            );
        }
    }
};

// ============================================================
// 3. QML WORKLOAD
// ============================================================

struct QMLWorkload {
    std::string identifier;
    WorkloadType type;
    Algorithm algorithm;
    Backend backend;

    int qubits;
    int depth;
    int shots;
    int datasetSize;
    int trainableParameters;

    double minimumAcceptableFidelity;
    bool requiresEntanglement;
    bool containsSensitiveData;

    void validate() const {
        if (identifier.empty()) {
            throw std::invalid_argument(
                "Workload identifier is required."
            );
        }

        if (qubits < 1 || qubits > 1000) {
            throw std::invalid_argument("Invalid qubit count.");
        }

        if (depth < 1 || depth > 100000) {
            throw std::invalid_argument("Invalid circuit depth.");
        }

        if (shots < 1 || shots > 100000000) {
            throw std::invalid_argument("Invalid shot count.");
        }

        if (datasetSize < 1) {
            throw std::invalid_argument("Dataset cannot be empty.");
        }

        if (trainableParameters < 0) {
            throw std::invalid_argument(
                "Parameter count cannot be negative."
            );
        }

        if (!std::isfinite(minimumAcceptableFidelity) ||
            minimumAcceptableFidelity < 0 ||
            minimumAcceptableFidelity > 1) {
            throw std::invalid_argument(
                "Invalid minimum fidelity."
            );
        }
    }
};

// ============================================================
// 4. QUANTUM RESOURCE ESTIMATION
// ============================================================

struct ResourceEstimate {
    std::uint64_t statevectorElements;
    std::uint64_t memoryBytes;
    std::uint64_t approximateGateOperations;
    std::uint64_t measurementOperations;
};

ResourceEstimate estimateResources(const QMLWorkload& workload) {
    workload.validate();

    // Avoid integer overflow before calculating 2^n.
    if (workload.qubits > 30) {
        throw std::overflow_error(
            "Statevector estimation exceeds educational limit."
        );
    }

    const std::uint64_t elements =
        std::uint64_t{1} << workload.qubits;

    // std::complex<double> typically occupies 16 bytes.
    const std::uint64_t memory = elements * sizeof(
        std::complex<double>
    );

    const std::uint64_t gates =
        static_cast<std::uint64_t>(workload.depth) *
        workload.qubits;

    const std::uint64_t measurements =
        static_cast<std::uint64_t>(workload.shots) *
        workload.qubits;

    return {
        elements,
        memory,
        gates,
        measurements
    };
}

// ============================================================
// 5. STATEVECTOR QUANTUM SIMULATOR
// ============================================================

class QuantumRegister {
private:
    int qubits_;
    std::vector<std::complex<double>> amplitudes_;

public:
    explicit QuantumRegister(int qubits)
        : qubits_(qubits) {

        if (qubits < 1 || qubits > 20) {
            throw std::invalid_argument(
                "Simulator supports 1-20 qubits."
            );
        }

        amplitudes_.assign(
            std::size_t{1} << qubits,
            {0.0, 0.0}
        );

        amplitudes_[0] = {1.0, 0.0};
    }

    int qubits() const {
        return qubits_;
    }

    void applyRY(int target, double angle) {
        if (target < 0 || target >= qubits_) {
            throw std::out_of_range("Invalid target qubit.");
        }

        if (!std::isfinite(angle)) {
            throw std::invalid_argument("Angle must be finite.");
        }

        const double c = std::cos(angle / 2.0);
        const double s = std::sin(angle / 2.0);

        const std::size_t mask = std::size_t{1} << target;

        for (std::size_t i = 0; i < amplitudes_.size(); ++i) {
            if (i & mask) continue;

            const auto zero = amplitudes_[i];
            const auto one = amplitudes_[i | mask];

            amplitudes_[i] = c * zero - s * one;
            amplitudes_[i | mask] = s * zero + c * one;
        }
    }

    void hadamard(int target) {
        if (target < 0 || target >= qubits_) {
            throw std::out_of_range("Invalid target qubit.");
        }

        const double scale = 1.0 / std::sqrt(2.0);
        const std::size_t mask = std::size_t{1} << target;

        for (std::size_t i = 0; i < amplitudes_.size(); ++i) {
            if (i & mask) continue;

            const auto zero = amplitudes_[i];
            const auto one = amplitudes_[i | mask];

            amplitudes_[i] = scale * (zero + one);
            amplitudes_[i | mask] = scale * (zero - one);
        }
    }

    void cnot(int control, int target) {
        if (control < 0 || control >= qubits_ ||
            target < 0 || target >= qubits_ ||
            control == target) {
            throw std::invalid_argument(
                "Invalid CNOT control or target."
            );
        }

        const std::size_t controlMask =
            std::size_t{1} << control;

        const std::size_t targetMask =
            std::size_t{1} << target;

        for (std::size_t i = 0; i < amplitudes_.size(); ++i) {
            if ((i & controlMask) && !(i & targetMask)) {
                std::swap(
                    amplitudes_[i],
                    amplitudes_[i | targetMask]
                );
            }
        }
    }

    double expectationZ(int target) const {
        if (target < 0 || target >= qubits_) {
            throw std::out_of_range("Invalid measurement target.");
        }

        const std::size_t mask = std::size_t{1} << target;

        double expectation = 0.0;

        for (std::size_t i = 0; i < amplitudes_.size(); ++i) {
            const double probability =
                std::norm(amplitudes_[i]);

            expectation += (i & mask)
                ? -probability
                : probability;
        }

        return expectation;
    }

    double norm() const {
        double total = 0.0;

        for (const auto& amplitude : amplitudes_) {
            total += std::norm(amplitude);
        }

        return total;
    }

    std::vector<double> probabilities() const {
        std::vector<double> result;

        for (const auto& amplitude : amplitudes_) {
            result.push_back(std::norm(amplitude));
        }

        return result;
    }
};

// ============================================================
// 6. QUANTUM FEATURE MAP
// ============================================================

class QuantumFeatureMap {
public:
    static QuantumRegister encode(
        const std::vector<double>& features
    ) {
        if (features.empty() || features.size() > 20) {
            throw std::invalid_argument(
                "Invalid feature dimensions."
            );
        }

        QuantumRegister state(
            static_cast<int>(features.size())
        );

        for (std::size_t i = 0; i < features.size(); ++i) {
            if (!std::isfinite(features[i]) ||
                features[i] < -1 || features[i] > 1) {
                throw std::invalid_argument(
                    "Features must be finite and in [-1, 1]."
                );
            }

            state.applyRY(
                static_cast<int>(i),
                M_PI * features[i]
            );
        }

        for (std::size_t i = 0; i + 1 < features.size(); ++i) {
            state.cnot(
                static_cast<int>(i),
                static_cast<int>(i + 1)
            );
        }

        return state;
    }

    static double fidelity(
        const std::vector<double>& first,
        const std::vector<double>& second
    ) {
        if (first.size() != second.size()) {
            throw std::invalid_argument(
                "Feature dimensions must match."
            );
        }

        auto a = encode(first).probabilities();
        auto stateA = encode(first);
        auto stateB = encode(second);

        (void)a;

        // Compute the complete complex inner product.
        std::complex<double> overlap{0.0, 0.0};

        // Statevector access is intentionally encapsulated.
        // The fidelity is computed using the probability-equivalent
        // real-amplitude representation of this RY/CNOT feature map.
        auto probabilitiesA = stateA.probabilities();
        auto probabilitiesB = stateB.probabilities();

        // All amplitudes remain real under RY and CNOT.
        for (std::size_t i = 0; i < probabilitiesA.size(); ++i) {
            const double amplitudeA =
                std::sqrt(probabilitiesA[i]);

            const double amplitudeB =
                std::sqrt(probabilitiesB[i]);

            // Sign information is recovered from the feature-map
            // basis transformations by using a direct overlap below.
            (void)amplitudeA;
            (void)amplitudeB;
        }

        // Reconstructing a direct feature-map overlap through
        // expectation values is unnecessary. This feature map uses
        // independent RY encoding followed by reversible CNOTs.
        // Its overlap equals the product of encoded single-qubit
        // overlaps before the common entangling transformation.
        double result = 1.0;

        for (std::size_t i = 0; i < first.size(); ++i) {
            const double angleDifference =
                M_PI * (first[i] - second[i]);

            result *= std::pow(
                std::cos(angleDifference / 2.0), 2
            );
        }

        (void)overlap;
        return result;
    }
};

// ============================================================
// 7. WORKLOAD POLICY ENGINE
// ============================================================

struct EvaluationResult {
    bool eligible;
    Algorithm selectedAlgorithm;
    std::vector<std::string> failures;
    ResourceEstimate resources;
    double estimatedCircuitFidelity;
    double measurementStandardError;
};

class GovernanceEngine {
private:
    HardwareProfile hardware_;

public:
    explicit GovernanceEngine(HardwareProfile hardware)
        : hardware_(std::move(hardware)) {
        hardware_.validate();
    }

    EvaluationResult evaluate(
        const QMLWorkload& workload
    ) const {
        workload.validate();

        EvaluationResult result{};
        result.eligible = true;
        result.selectedAlgorithm = workload.algorithm;
        result.resources = estimateResources(workload);
        result.estimatedCircuitFidelity = 1.0;
        result.measurementStandardError = 0.0;

        auto reject = [&](const std::string& reason) {
            result.eligible = false;
            result.failures.push_back(reason);
        };

        if (workload.backend == Backend::QuantumHardware) {
            if (!hardware_.available) {
                reject("Quantum hardware is unavailable.");
            }

            if (workload.qubits > hardware_.availableQubits) {
                reject("Hardware qubit capacity exceeded.");
            }

            if (workload.depth > hardware_.maximumCircuitDepth) {
                reject("Hardware circuit depth exceeded.");
            }

            if (workload.shots > hardware_.maximumShots) {
                reject("Hardware shot budget exceeded.");
            }

            if (workload.requiresEntanglement &&
                !hardware_.supportsEntanglement) {
                reject("Required entanglement is unsupported.");
            }

            result.estimatedCircuitFidelity =
                std::pow(
                    hardware_.gateFidelity,
                    workload.depth * workload.qubits
                ) * hardware_.measurementFidelity;

            if (
                result.estimatedCircuitFidelity <
                workload.minimumAcceptableFidelity
            ) {
                reject("Estimated fidelity is below workload threshold.");
            }
        }

        if (workload.backend == Backend::Statevector) {
            if (workload.qubits > 30) {
                reject("Statevector workload exceeds memory limit.");
            }

            if (workload.qubits <= 30) {
                const std::uint64_t memory =
                    result.resources.memoryBytes;

                // Example memory budget: 8 GiB.
                if (memory > 8ULL * 1024 * 1024 * 1024) {
                    reject("Statevector memory budget exceeded.");
                }
            }
        }

        if (workload.backend == Backend::NoisySimulator) {
            result.estimatedCircuitFidelity =
                std::pow(0.995, workload.depth * workload.qubits);
        }

        if (workload.containsSensitiveData &&
            workload.backend == Backend::QuantumHardware) {
            reject(
                "Sensitive data requires an approved hardware data policy."
            );
        }

        result.measurementStandardError =
            1.0 / std::sqrt(
                static_cast<double>(workload.shots)
            );

        return result;
    }
};

// ============================================================
// 8. ALGORITHM SELECTION
// ============================================================

Algorithm selectAlgorithm(
    WorkloadType type,
    const HardwareProfile& hardware,
    int datasetSize
) {
    if (datasetSize < 1) {
        throw std::invalid_argument("Dataset must not be empty.");
    }

    switch (type) {
        case WorkloadType::SupervisedLearning:
            return hardware.availableQubits <= 20
                ? Algorithm::VariationalClassifier
                : Algorithm::QuantumNeuralNetwork;

        case WorkloadType::SimilarityLearning:
            return datasetSize <= 10000
                ? Algorithm::QuantumKernel
                : Algorithm::QuantumInspired;

        case WorkloadType::Optimization:
            return hardware.available
                ? Algorithm::QAOA
                : Algorithm::QuantumInspired;

        case WorkloadType::Chemistry:
            return hardware.available
                ? Algorithm::VQE
                : Algorithm::QuantumInspired;

        case WorkloadType::GenerativeLearning:
            return Algorithm::QuantumGenerative;

        case WorkloadType::ReinforcementLearning:
            return Algorithm::QuantumReinforcement;
    }

    throw std::invalid_argument("Unknown workload type.");
}

// ============================================================
// 9. LANDSCAPE REPORT
// ============================================================

void printLandscape() {
    const std::map<std::string, std::vector<std::string>> landscape = {
        {
            "Variational Quantum Algorithms",
            {
                "Variational Quantum Eigensolver",
                "Quantum Approximate Optimization",
                "Variational Quantum Classifier"
            }
        },
        {
            "Quantum Kernel Methods",
            {
                "Quantum Feature Maps",
                "Fidelity Kernel Estimation",
                "Kernel-Based Classification"
            }
        },
        {
            "Quantum Neural Networks",
            {
                "Parameterized Quantum Circuits",
                "Quantum Convolutional Circuits",
                "Hybrid Quantum-Classical Networks"
            }
        },
        {
            "Quantum Generative Learning",
            {
                "Circuit Born Machines",
                "Quantum Generative Adversarial Models"
            }
        },
        {
            "Quantum Reinforcement Learning",
            {
                "Quantum Policies",
                "Quantum Value Models"
            }
        },
        {
            "Quantum-Inspired Computing",
            {
                "Tensor Network Methods",
                "Classical Quantum-Inspired Optimization"
            }
        }
    };

    std::cout << "\nQML ALGORITHM LANDSCAPE\n";

    for (const auto& [category, algorithms] : landscape) {
        std::cout << "\n" << category << "\n";

        for (const auto& algorithm : algorithms) {
            std::cout << "  - " << algorithm << "\n";
        }
    }
}

// ============================================================
// 10. EXECUTION
// ============================================================

void runDemo() {
    HardwareProfile hardware{
        "Educational Quantum Backend",
        12,
        100,
        50000,
        0.999,
        0.995,
        true,
        true
    };

    GovernanceEngine engine(hardware);

    QMLWorkload workload{
        "QML-SUPERVISED-001",
        WorkloadType::SupervisedLearning,
        Algorithm::VariationalClassifier,
        Backend::QuantumHardware,
        4,
        12,
        2048,
        500,
        8,
        0.80,
        true,
        false
    };

    std::cout << std::fixed << std::setprecision(6);

    printLandscape();

    std::cout << "\nQUANTUM REGISTER SIMULATION\n";

    QuantumRegister state(2);
    state.hadamard(0);
    state.cnot(0, 1);

    std::cout << "State norm: " << state.norm() << "\n";
    std::cout << "Z0 expectation: "
              << state.expectationZ(0) << "\n";

    std::cout << "Basis probabilities:\n";

    for (std::size_t i = 0;
         i < state.probabilities().size(); ++i) {
        std::cout << "  |" << std::bitset<2>(i) << "> = "
                  << state.probabilities()[i] << "\n";
    }

    std::cout << "\nQUANTUM FEATURE MAP\n";

    const std::vector<double> first{-0.5, 0.4};
    const std::vector<double> second{0.5, -0.4};

    std::cout << "Fidelity kernel: "
              << QuantumFeatureMap::fidelity(first, second)
              << "\n";

    std::cout << "\nRESOURCE ESTIMATION\n";

    const auto resources = estimateResources(workload);

    std::cout << "Statevector elements: "
              << resources.statevectorElements << "\n";

    std::cout << "Memory bytes: "
              << resources.memoryBytes << "\n";

    std::cout << "Estimated gate operations: "
              << resources.approximateGateOperations << "\n";

    std::cout << "Measurement operations: "
              << resources.measurementOperations << "\n";

    std::cout << "\nGOVERNANCE EVALUATION\n";

    const auto result = engine.evaluate(workload);

    std::cout << "Eligible: "
              << std::boolalpha
              << result.eligible << "\n";

    std::cout << "Algorithm: "
              << toString(result.selectedAlgorithm) << "\n";

    std::cout << "Backend: "
              << toString(workload.backend) << "\n";

    std::cout << "Estimated fidelity: "
              << result.estimatedCircuitFidelity << "\n";

    std::cout << "Measurement standard error: "
              << result.measurementStandardError << "\n";

    for (const auto& failure : result.failures) {
        std::cout << "REJECTION: " << failure << "\n";
    }

    std::cout << "\nALGORITHM SELECTION\n";

    std::cout << toString(
        selectAlgorithm(
            WorkloadType::SimilarityLearning,
            hardware,
            500
        )
    ) << "\n";

    // Test workload rejection.
    QMLWorkload invalidWorkload = workload;
    invalidWorkload.qubits = 50;

    try {
        invalidWorkload.validate();
    } catch (const std::exception& error) {
        std::cout << "\nExpected validation failure: "
                  << error.what() << "\n";
    }

    if (!result.eligible) {
        throw std::runtime_error(
            "Demonstration workload unexpectedly rejected."
        );
    }
}

} // namespace qml

int main() {
    try {
        qml::runDemo();
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "QML execution error: "
                  << error.what() << "\n";

        return 1;
    }
}
