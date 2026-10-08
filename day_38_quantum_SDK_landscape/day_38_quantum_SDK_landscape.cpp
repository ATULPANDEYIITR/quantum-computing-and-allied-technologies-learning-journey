/*
 * Quantum SDK Landscape: C++ Case Study
 *
 * Scenario:
 * A research organization needs a small governance-neutral "SDK selection
 * engine" that can evaluate a quantum workload against different SDK
 * families before committing the application to a vendor or execution
 * environment.
 *
 * The program models:
 *   - circuit requirements
 *   - SDK capabilities
 *   - backend constraints
 *   - compilation requirements
 *   - simulation requirements
 *   - hybrid CPU/GPU requirements
 *   - cloud requirements
 *   - resource-estimation requirements
 *
 * It also performs a lightweight hardware-aware circuit analysis.
 *
 * Compile:
 *   g++ -std=c++17 -O2 quantum_sdk_landscape.cpp -o quantum_sdk_landscape
 */

#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

enum class WorkloadType {
    GeneralCircuit,
    HardwareCompilation,
    QML,
    CloudExecution,
    GPUSimulation,
    ResourceEstimation,
    Research
};

std::string toString(WorkloadType type) {
    switch (type) {
        case WorkloadType::GeneralCircuit:
            return "general circuit";
        case WorkloadType::HardwareCompilation:
            return "hardware compilation";
        case WorkloadType::QML:
            return "quantum machine learning";
        case WorkloadType::CloudExecution:
            return "cloud execution";
        case WorkloadType::GPUSimulation:
            return "GPU simulation";
        case WorkloadType::ResourceEstimation:
            return "resource estimation";
        case WorkloadType::Research:
            return "research";
    }
    return "unknown";
}

struct Workload {
    std::string name;
    WorkloadType type;
    bool needsDifferentiation = false;
    bool needsGPU = false;
    bool needsCloud = false;
    bool needsCompiler = false;
    bool needsResourceEstimation = false;
};

struct SDKProfile {
    std::string name;
    std::string organization;
    std::vector<std::string> languages;
    std::set<WorkloadType> workloads;
    bool differentiable = false;
    bool compiler = false;
    bool hardware = false;
    bool cloud = false;
    bool simulator = false;
    std::vector<std::string> strengths;
};

class SDKLandscape {
private:
    std::vector<SDKProfile> profiles;

public:
    SDKLandscape() {
        profiles = {
            {
                "Qiskit",
                "IBM",
                {"Python"},
                {
                    WorkloadType::GeneralCircuit,
                    WorkloadType::HardwareCompilation,
                    WorkloadType::CloudExecution,
                    WorkloadType::Research
                },
                false, true, true, true, true,
                {
                    "circuit construction",
                    "transpilation",
                    "IBM hardware integration",
                    "primitive-oriented execution"
                }
            },
            {
                "Cirq",
                "Google Quantum AI",
                {"Python"},
                {
                    WorkloadType::GeneralCircuit,
                    WorkloadType::HardwareCompilation,
                    WorkloadType::Research
                },
                false, true, true, false, true,
                {
                    "explicit circuit and moment representation",
                    "hardware-oriented research",
                    "circuit simulation"
                }
            },
            {
                "PennyLane",
                "Xanadu",
                {"Python"},
                {
                    WorkloadType::QML,
                    WorkloadType::GeneralCircuit,
                    WorkloadType::Research
                },
                true, true, true, false, true,
                {
                    "differentiable quantum programming",
                    "variational algorithms",
                    "quantum machine learning",
                    "hybrid optimization"
                }
            },
            {
                "pytket / TKET",
                "Quantinuum",
                {"Python API", "C++ core"},
                {
                    WorkloadType::HardwareCompilation,
                    WorkloadType::GeneralCircuit,
                    WorkloadType::Research
                },
                false, true, true, false, true,
                {
                    "routing",
                    "placement",
                    "optimization passes",
                    "cross-platform circuit compilation"
                }
            },
            {
                "Amazon Braket SDK",
                "AWS",
                {"Python"},
                {
                    WorkloadType::CloudExecution,
                    WorkloadType::GeneralCircuit,
                    WorkloadType::Research
                },
                false, false, true, true, true,
                {
                    "managed cloud execution",
                    "multi-provider access",
                    "hybrid jobs",
                    "AWS integration"
                }
            },
            {
                "CUDA-Q",
                "NVIDIA",
                {"C++", "Python"},
                {
                    WorkloadType::GPUSimulation,
                    WorkloadType::HardwareCompilation,
                    WorkloadType::GeneralCircuit,
                    WorkloadType::Research
                },
                false, true, true, false, true,
                {
                    "GPU-accelerated simulation",
                    "hybrid CPU/GPU/QPU programming",
                    "multiple simulator backends"
                }
            },
            {
                "Microsoft QDK / Q#",
                "Microsoft",
                {"Q#", "Python"},
                {
                    WorkloadType::ResourceEstimation,
                    WorkloadType::CloudExecution,
                    WorkloadType::GeneralCircuit,
                    WorkloadType::Research
                },
                false, true, true, true, true,
                {
                    "Q# language",
                    "resource estimation",
                    "simulation",
                    "Azure Quantum integration"
                }
            }
        };
    }

    struct Score {
        const SDKProfile* profile;
        int value;
        std::vector<std::string> reasons;
    };

    Score evaluate(const SDKProfile& sdk, const Workload& workload) const {
        int score = 0;
        std::vector<std::string> reasons;

        if (sdk.workloads.contains(workload.type)) {
            score += 4;
            reasons.push_back("workload alignment");
        }

        if (workload.needsDifferentiation) {
            if (sdk.differentiable) {
                score += 6;
                reasons.push_back("differentiable programming");
            } else {
                score -= 3;
            }
        }

        if (workload.needsGPU) {
            if (sdk.name == "CUDA-Q") {
                score += 7;
                reasons.push_back("GPU-oriented execution");
            } else if (sdk.simulator) {
                score += 1;
            }
        }

        if (workload.needsCloud) {
            if (sdk.cloud) {
                score += 5;
                reasons.push_back("managed cloud execution");
            } else {
                score -= 1;
            }
        }

        if (workload.needsCompiler) {
            if (sdk.compiler) {
                score += 5;
                reasons.push_back("compiler-oriented architecture");
            } else {
                score -= 2;
            }
        }

        if (workload.needsResourceEstimation) {
            if (sdk.name == "Microsoft QDK / Q#") {
                score += 7;
                reasons.push_back("dedicated resource estimation");
            } else {
                score -= 1;
            }
        }

        return {&sdk, score, reasons};
    }

    std::vector<Score> recommend(const Workload& workload) const {
        std::vector<Score> result;

        for (const auto& sdk : profiles) {
            result.push_back(evaluate(sdk, workload));
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const Score& left, const Score& right) {
                if (left.value != right.value) {
                    return left.value > right.value;
                }
                return left.profile->name < right.profile->name;
            }
        );

        return result;
    }

    void print() const {
        std::cout << "QUANTUM SDK LANDSCAPE\n";
        std::cout << std::string(78, '=') << "\n";

        for (const auto& sdk : profiles) {
            std::cout << "\n" << sdk.name << " | " << sdk.organization << "\n";
            std::cout << "Languages: ";

            for (std::size_t i = 0; i < sdk.languages.size(); ++i) {
                if (i > 0) std::cout << ", ";
                std::cout << sdk.languages[i];
            }

            std::cout << "\nDifferentiable: " << std::boolalpha << sdk.differentiable;
            std::cout << "\nCompiler: " << sdk.compiler;
            std::cout << "\nHardware: " << sdk.hardware;
            std::cout << "\nCloud: " << sdk.cloud;
            std::cout << "\nSimulator: " << sdk.simulator << "\n";
            std::cout << "Strengths:\n";

            for (const auto& strength : sdk.strengths) {
                std::cout << "  - " << strength << "\n";
            }
        }
    }
};

enum class GateType {
    H,
    RX,
    RY,
    CNOT
};

struct Gate {
    GateType type;
    std::vector<std::size_t> qubits;
    double parameter = 0.0;
};

class Circuit {
private:
    std::size_t qubitCount;
    std::vector<Gate> gates;

public:
    explicit Circuit(std::size_t qubits)
        : qubitCount(qubits) {
        if (qubits == 0) {
            throw std::invalid_argument("A circuit must contain at least one qubit");
        }
    }

    void add(GateType type, std::vector<std::size_t> qubits, double parameter = 0.0) {
        if (qubits.empty()) {
            throw std::invalid_argument("Gate requires at least one qubit");
        }

        std::set<std::size_t> unique(qubits.begin(), qubits.end());

        if (unique.size() != qubits.size()) {
            throw std::invalid_argument("A gate cannot target one qubit twice");
        }

        for (std::size_t qubit : qubits) {
            if (qubit >= qubitCount) {
                throw std::out_of_range("Gate references a non-existent qubit");
            }
        }

        gates.push_back({type, std::move(qubits), parameter});
    }

    std::size_t depth() const {
        std::vector<std::size_t> availability(qubitCount, 0);

        for (const auto& gate : gates) {
            std::size_t layer = 0;

            for (auto qubit : gate.qubits) {
                layer = std::max(layer, availability[qubit]);
            }

            ++layer;

            for (auto qubit : gate.qubits) {
                availability[qubit] = layer;
            }
        }

        return *std::max_element(
            availability.begin(),
            availability.end()
        );
    }

    std::size_t twoQubitGateCount() const {
        return std::count_if(
            gates.begin(),
            gates.end(),
            [](const Gate& gate) {
                return gate.qubits.size() == 2;
            }
        );
    }

    std::size_t gateCount() const {
        return gates.size();
    }

    const std::vector<Gate>& operations() const {
        return gates;
    }
};

struct HardwareTopology {
    std::set<std::pair<std::size_t, std::size_t>> edges;

    bool supports(std::size_t first, std::size_t second) const {
        return edges.contains({first, second}) ||
               edges.contains({second, first});
    }
};

class HardwareAwareAnalyzer {
public:
    static std::vector<std::string> unsupportedInteractions(
        const Circuit& circuit,
        const HardwareTopology& topology
    ) {
        std::vector<std::string> failures;

        for (const auto& gate : circuit.operations()) {
            if (gate.qubits.size() != 2) {
                continue;
            }

            if (!topology.supports(gate.qubits[0], gate.qubits[1])) {
                failures.push_back(
                    "two-qubit interaction q" +
                    std::to_string(gate.qubits[0]) +
                    "-q" +
                    std::to_string(gate.qubits[1]) +
                    " is not directly supported"
                );
            }
        }

        return failures;
    }
};

Circuit createBellCircuit() {
    Circuit circuit(2);
    circuit.add(GateType::H, {0});
    circuit.add(GateType::CNOT, {0, 1});
    return circuit;
}

Circuit createVariationalCircuit(double theta) {
    Circuit circuit(3);
    circuit.add(GateType::RY, {0}, theta);
    circuit.add(GateType::RY, {1}, theta / 2.0);
    circuit.add(GateType::RY, {2}, -theta);
    circuit.add(GateType::CNOT, {0, 1});
    circuit.add(GateType::CNOT, {1, 2});
    return circuit;
}

void demonstrateHardwareConstraint() {
    std::cout << "\nHARDWARE-AWARE CIRCUIT ANALYSIS\n";
    std::cout << std::string(78, '=') << "\n";

    Circuit circuit = createVariationalCircuit(3.141592653589793 / 3.0);

    HardwareTopology linearTopology{
        {
            {0, 1},
            {1, 2}
        }
    };

    const auto failures =
        HardwareAwareAnalyzer::unsupportedInteractions(circuit, linearTopology);

    std::cout << "Circuit depth: " << circuit.depth() << "\n";
    std::cout << "Two-qubit gates: " << circuit.twoQubitGateCount() << "\n";

    if (failures.empty()) {
        std::cout << "All two-qubit interactions are native to the topology.\n";
    } else {
        for (const auto& failure : failures) {
            std::cout << "Constraint: " << failure << "\n";
        }
    }

    /*
     * This is the architectural reason compiler-oriented SDKs matter.
     * A logical circuit can be correct while still being physically invalid
     * for a target device. Routing, SWAP insertion, gate decomposition,
     * scheduling, and optimization convert the logical representation into
     * an executable hardware representation.
     */
}

void demonstrateRecommendations() {
    SDKLandscape landscape;

    std::cout << "\nWORKLOAD-DRIVEN SDK SELECTION\n";
    std::cout << std::string(78, '=') << "\n";

    std::vector<Workload> workloads = {
        {
            "Train a parameterized quantum model",
            WorkloadType::QML,
            true, false, false, false, false
        },
        {
            "Optimize a circuit for a restricted device topology",
            WorkloadType::HardwareCompilation,
            false, false, false, true, false
        },
        {
            "Run a managed multi-provider experiment",
            WorkloadType::CloudExecution,
            false, false, true, false, false
        },
        {
            "Accelerate large simulation workloads with GPUs",
            WorkloadType::GPUSimulation,
            false, true, false, false, false
        },
        {
            "Estimate resources for a future algorithm",
            WorkloadType::ResourceEstimation,
            false, false, false, false, true
        }
    };

    for (const auto& workload : workloads) {
        std::cout << "\n" << workload.name << "\n";

        auto recommendations = landscape.recommend(workload);

        const std::size_t limit =
            std::min<std::size_t>(3, recommendations.size());

        for (std::size_t index = 0; index < limit; ++index) {
            const auto& recommendation = recommendations[index];

            std::cout
                << "  "
                << std::setw(24)
                << std::left
                << recommendation.profile->name
                << " score="
                << std::setw(3)
                << std::right
                << recommendation.value;

            if (!recommendation.reasons.empty()) {
                std::cout << "  " << recommendation.reasons.front();
            }

            std::cout << "\n";
        }
    }
}

int main() {
    try {
        SDKLandscape landscape;
        landscape.print();

        Circuit bell = createBellCircuit();

        std::cout << "\nBELL CIRCUIT METRICS\n";
        std::cout << std::string(78, '=') << "\n";
        std::cout << "Qubits: 2\n";
        std::cout << "Gates: " << bell.gateCount() << "\n";
        std::cout << "Depth: " << bell.depth() << "\n";
        std::cout << "Two-qubit gates: " << bell.twoQubitGateCount() << "\n";

        demonstrateHardwareConstraint();
        demonstrateRecommendations();

        std::cout << "\nSELECTION PRINCIPLE\n";
        std::cout << std::string(78, '=') << "\n";
        std::cout
            << "No SDK is universally best. The correct abstraction depends on "
               "whether the workload is primarily circuit construction, "
               "hardware compilation, differentiable programming, cloud "
               "orchestration, accelerated simulation, or resource estimation.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }
}
