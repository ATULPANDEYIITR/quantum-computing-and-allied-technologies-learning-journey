#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * NISQ Era: Quantum hardware governance and merge-free
 * experiment eligibility engine.
 *
 * Models:
 * - Quantum processors
 * - Qubit connectivity
 * - Gate calibration
 * - Readout errors
 * - Coherence constraints
 * - Circuit resource requirements
 * - Noise-aware device selection
 * - Error budget enforcement
 * - Shot allocation
 *
 * Compile: g++ -std=c++17 -O2 nisq.cpp -o nisq
 */

enum class GateType {
    H,
    X,
    Y,
    Z,
    S,
    T,
    CNOT,
    CZ
};

enum class DeviceStatus {
    ONLINE,
    MAINTENANCE,
    OFFLINE
};

enum class Eligibility {
    APPROVED,
    INSUFFICIENT_QUBITS,
    UNSUPPORTED_CONNECTIVITY,
    EXCESSIVE_GATE_ERROR,
    COHERENCE_LIMIT_EXCEEDED,
    DEVICE_UNAVAILABLE,
    INVALID_CIRCUIT
};

struct Gate {
    GateType type;
    std::vector<int> qubits;

    bool isTwoQubit() const {
        return qubits.size() == 2;
    }
};

struct Calibration {
    double singleQubitError;
    double twoQubitError;
    double readoutError;
    double coherenceTimeMicros;
    double gateTimeMicros;
    std::uint64_t calibrationVersion;
};

struct Circuit {
    std::string id;
    int qubitCount;
    std::vector<Gate> gates;

    void validate() const {
        if (id.empty()) {
            throw std::invalid_argument("Circuit ID is required");
        }

        if (qubitCount < 1 || qubitCount > 100) {
            throw std::invalid_argument("Invalid qubit count");
        }

        if (gates.empty()) {
            throw std::invalid_argument("Circuit has no gates");
        }

        for (const auto& gate : gates) {
            const std::size_t expected =
                (gate.type == GateType::CNOT ||
                 gate.type == GateType::CZ) ? 2 : 1;

            if (gate.qubits.size() != expected) {
                throw std::invalid_argument(
                    "Invalid gate arity"
                );
            }

            std::set<int> unique(
                gate.qubits.begin(),
                gate.qubits.end()
            );

            if (unique.size() != gate.qubits.size()) {
                throw std::invalid_argument(
                    "Repeated qubit in gate"
                );
            }

            for (int q : gate.qubits) {
                if (q < 0 || q >= qubitCount) {
                    throw std::invalid_argument(
                        "Invalid circuit qubit index"
                    );
                }
            }
        }
    }

    int depth() const {
        std::vector<int> availability(qubitCount, 0);

        for (const auto& gate : gates) {
            int layer = 1;

            for (int q : gate.qubits) {
                layer = std::max(
                    layer,
                    availability[q] + 1
                );
            }

            for (int q : gate.qubits) {
                availability[q] = layer;
            }
        }

        return *std::max_element(
            availability.begin(),
            availability.end()
        );
    }

    int twoQubitGateCount() const {
        return static_cast<int>(
            std::count_if(
                gates.begin(),
                gates.end(),
                [](const Gate& gate) {
                    return gate.isTwoQubit();
                }
            )
        );
    }
};

struct QuantumDevice {
    std::string id;
    std::string name;
    int qubitCapacity;
    std::set<std::pair<int, int>> connectivity;
    Calibration calibration;
    DeviceStatus status;

    static std::pair<int, int> edge(int a, int b) {
        return {
            std::min(a, b),
            std::max(a, b)
        };
    }

    bool supports(const Circuit& circuit) const {
        if (status != DeviceStatus::ONLINE) {
            return false;
        }

        if (circuit.qubitCount > qubitCapacity) {
            return false;
        }

        for (const auto& gate : circuit.gates) {
            if (gate.isTwoQubit()) {
                auto connection = edge(
                    gate.qubits[0],
                    gate.qubits[1]
                );

                if (connectivity.find(connection) ==
                    connectivity.end()) {
                    return false;
                }
            }
        }

        return true;
    }
};

struct NoiseEstimate {
    double gateSuccessProbability;
    double readoutSuccessProbability;
    double coherencePenalty;
    double combinedSuccessProbability;
    double estimatedDurationMicros;
};

struct EvaluationPolicy {
    double maximumGateError = 0.10;
    double minimumSuccessProbability = 0.50;
    double maximumCoherenceRatio = 0.50;
    int maximumCircuitDepth = 1000;
    int minimumCalibrationVersion = 1;
};

struct EvaluationResult {
    Eligibility eligibility;
    std::vector<std::string> reasons;
    NoiseEstimate estimate;
    std::string deviceId;

    bool approved() const {
        return eligibility == Eligibility::APPROVED;
    }
};

class GovernanceEngine {
private:
    EvaluationPolicy policy;

    static double clampProbability(double value) {
        return std::max(0.0, std::min(1.0, value));
    }

    NoiseEstimate estimate(
        const Circuit& circuit,
        const QuantumDevice& device
    ) const {
        const auto& calibration = device.calibration;

        int twoQubit = circuit.twoQubitGateCount();
        int oneQubit =
            static_cast<int>(circuit.gates.size()) - twoQubit;

        double gateSuccess =
            std::pow(
                1.0 - calibration.singleQubitError,
                oneQubit
            ) *
            std::pow(
                1.0 - calibration.twoQubitError,
                twoQubit
            );

        double readoutSuccess = std::pow(
            1.0 - calibration.readoutError,
            circuit.qubitCount
        );

        double duration =
            circuit.depth() * calibration.gateTimeMicros;

        double coherencePenalty = std::exp(
            -duration / calibration.coherenceTimeMicros
        );

        return {
            gateSuccess,
            readoutSuccess,
            coherencePenalty,
            clampProbability(
                gateSuccess *
                readoutSuccess *
                coherencePenalty
            ),
            duration
        };
    }

public:
    explicit GovernanceEngine(EvaluationPolicy configuration)
        : policy(configuration) {

        if (policy.maximumGateError < 0 ||
            policy.maximumGateError > 1 ||
            policy.minimumSuccessProbability < 0 ||
            policy.minimumSuccessProbability > 1 ||
            policy.maximumCoherenceRatio < 0 ||
            policy.maximumCircuitDepth < 1 ||
            policy.minimumCalibrationVersion < 1) {
            throw std::invalid_argument(
                "Invalid governance policy"
            );
        }
    }

    EvaluationResult evaluate(
        const Circuit& circuit,
        const QuantumDevice& device
    ) const {
        circuit.validate();

        std::vector<std::string> reasons;

        if (device.status != DeviceStatus::ONLINE) {
            reasons.push_back("Device is unavailable");
        }

        if (circuit.qubitCount > device.qubitCapacity) {
            reasons.push_back(
                "Circuit exceeds device qubit capacity"
            );
        }

        if (!device.supports(circuit)) {
            reasons.push_back(
                "Circuit connectivity is unsupported"
            );
        }

        const auto& c = device.calibration;

        if (c.singleQubitError > policy.maximumGateError ||
            c.twoQubitError > policy.maximumGateError) {
            reasons.push_back(
                "Gate calibration exceeds error threshold"
            );
        }

        if (c.calibrationVersion <
            static_cast<std::uint64_t>(
                policy.minimumCalibrationVersion
            )) {
            reasons.push_back("Calibration version is outdated");
        }

        if (c.coherenceTimeMicros <= 0 ||
            c.gateTimeMicros <= 0) {
            reasons.push_back("Invalid timing calibration");
        }

        if (c.readoutError < 0 || c.readoutError > 1 ||
            c.singleQubitError < 0 ||
            c.singleQubitError > 1 ||
            c.twoQubitError < 0 ||
            c.twoQubitError > 1) {
            reasons.push_back("Invalid calibration probability");
        }

        if (c.coherenceTimeMicros <= 0 ||
            c.gateTimeMicros <= 0 ||
            c.readoutError < 0 || c.readoutError > 1 ||
            c.singleQubitError < 0 ||
            c.singleQubitError > 1 ||
            c.twoQubitError < 0 ||
            c.twoQubitError > 1) {
            return {
                Eligibility::EXCESSIVE_GATE_ERROR,
                reasons,
                {},
                device.id
            };
        }

        if (circuit.depth() > policy.maximumCircuitDepth) {
            reasons.push_back("Circuit depth exceeds policy");
        }

        NoiseEstimate noise = estimate(circuit, device);

        const double coherenceRatio =
            noise.estimatedDurationMicros /
            c.coherenceTimeMicros;

        if (coherenceRatio > policy.maximumCoherenceRatio) {
            reasons.push_back(
                "Circuit exceeds coherence budget"
            );
        }

        if (noise.combinedSuccessProbability <
            policy.minimumSuccessProbability) {
            reasons.push_back(
                "Estimated success probability is insufficient"
            );
        }

        if (!reasons.empty()) {
            Eligibility status =
                device.status != DeviceStatus::ONLINE
                    ? Eligibility::DEVICE_UNAVAILABLE
                    : circuit.qubitCount > device.qubitCapacity
                        ? Eligibility::INSUFFICIENT_QUBITS
                        : !device.supports(circuit)
                            ? Eligibility::UNSUPPORTED_CONNECTIVITY
                            : coherenceRatio >
                                policy.maximumCoherenceRatio
                                ? Eligibility::COHERENCE_LIMIT_EXCEEDED
                                : Eligibility::EXCESSIVE_GATE_ERROR;

            return {
                status,
                reasons,
                noise,
                device.id
            };
        }

        return {
            Eligibility::APPROVED,
            {},
            noise,
            device.id
        };
    }

    std::pair<QuantumDevice, EvaluationResult> selectDevice(
        const Circuit& circuit,
        const std::vector<QuantumDevice>& devices
    ) const {
        bool found = false;

        QuantumDevice selected;
        EvaluationResult bestResult{};

        for (const auto& device : devices) {
            auto result = evaluate(circuit, device);

            if (!result.approved()) {
                continue;
            }

            if (!found ||
                result.estimate.combinedSuccessProbability >
                bestResult.estimate.combinedSuccessProbability) {
                selected = device;
                bestResult = result;
                found = true;
            }
        }

        if (!found) {
            throw std::runtime_error(
                "No quantum device satisfies the policy"
            );
        }

        return {selected, bestResult};
    }
};

std::vector<QuantumDevice> createDevices() {
    return {
        {
            "QPU-01",
            "Superconducting Processor Alpha",
            5,
            {
                {0, 1}, {1, 2}, {2, 3}, {3, 4}
            },
            {
                0.001,
                0.009,
                0.02,
                100.0,
                0.05,
                3
            },
            DeviceStatus::ONLINE
        },
        {
            "QPU-02",
            "Superconducting Processor Beta",
            8,
            {
                {0, 1}, {1, 2}, {2, 3},
                {3, 4}, {4, 5}, {5, 6}, {6, 7}
            },
            {
                0.002,
                0.015,
                0.03,
                150.0,
                0.04,
                4
            },
            DeviceStatus::ONLINE
        },
        {
            "QPU-03",
            "Maintenance Processor",
            10,
            {
                {0, 1}, {1, 2}, {2, 3}
            },
            {
                0.001,
                0.005,
                0.01,
                200.0,
                0.03,
                4
            },
            DeviceStatus::MAINTENANCE
        }
    };
}

Circuit createBellCircuit() {
    Circuit circuit{
        "BELL-EXPERIMENT",
        2,
        {
            {GateType::H, {0}},
            {GateType::CNOT, {0, 1}}
        }
    };

    return circuit;
}

Circuit createGHZCircuit() {
    Circuit circuit{
        "GHZ-EXPERIMENT",
        4,
        {
            {GateType::H, {0}},
            {GateType::CNOT, {0, 1}},
            {GateType::CNOT, {1, 2}},
            {GateType::CNOT, {2, 3}}
        }
    };

    return circuit;
}

void printEvaluation(
    const EvaluationResult& result
) {
    std::cout << "\nDevice: " << result.deviceId << '\n';
    std::cout << "Eligibility: "
              << (result.approved() ? "APPROVED" : "REJECTED")
              << '\n';

    std::cout << std::fixed << std::setprecision(6);

    std::cout << "Gate success: "
              << result.estimate.gateSuccessProbability
              << '\n';

    std::cout << "Readout success: "
              << result.estimate.readoutSuccessProbability
              << '\n';

    std::cout << "Combined success: "
              << result.estimate.combinedSuccessProbability
              << '\n';

    std::cout << "Estimated duration (microseconds): "
              << result.estimate.estimatedDurationMicros
              << '\n';

    for (const auto& reason : result.reasons) {
        std::cout << "  Rejection: " << reason << '\n';
    }
}

void runTests() {
    Circuit bell = createBellCircuit();
    bell.validate();

    if (bell.depth() != 2) {
        throw std::runtime_error("Circuit depth test failed");
    }

    if (bell.twoQubitGateCount() != 1) {
        throw std::runtime_error("Gate count test failed");
    }

    EvaluationPolicy policy;
    GovernanceEngine engine(policy);

    auto devices = createDevices();
    auto result = engine.evaluate(bell, devices.front());

    if (!result.approved()) {
        throw std::runtime_error(
            "Bell circuit should be eligible"
        );
    }

    Circuit invalid{
        "INVALID",
        2,
        {{GateType::CNOT, {0, 0}}}
    };

    try {
        invalid.validate();
        throw std::runtime_error(
            "Invalid circuit was accepted"
        );
    } catch (const std::invalid_argument&) {
        // Expected validation failure.
    }

    std::cout << "C++17 self-tests passed.\n";
}

int main() {
    try {
        runTests();

        EvaluationPolicy policy;
        policy.maximumGateError = 0.05;
        policy.minimumSuccessProbability = 0.50;
        policy.maximumCoherenceRatio = 0.50;
        policy.maximumCircuitDepth = 100;
        policy.minimumCalibrationVersion = 2;

        GovernanceEngine engine(policy);

        const auto devices = createDevices();

        const std::vector<Circuit> experiments = {
            createBellCircuit(),
            createGHZCircuit()
        };

        for (const auto& circuit : experiments) {
            std::cout << "\n================================\n";
            std::cout << "Experiment: " << circuit.id << '\n';
            std::cout << "Qubits: " << circuit.qubitCount << '\n';
            std::cout << "Gates: " << circuit.gates.size() << '\n';
            std::cout << "Depth: " << circuit.depth() << '\n';

            try {
                auto selection = engine.selectDevice(
                    circuit,
                    devices
                );

                printEvaluation(selection.second);

                std::cout << "Selected processor: "
                          << selection.first.name << '\n';

            } catch (const std::runtime_error& error) {
                std::cout << "Experiment rejected: "
                          << error.what() << '\n';
            }
        }

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "Fatal error: "
                  << error.what() << '\n';
        return 1;
    }
}
