#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

enum class QubitTechnology {
    Superconducting,
    TrappedIon,
    NeutralAtom,
    Photonic,
    Spin
};

enum class ProcessorState {
    Offline,
    Initializing,
    Ready,
    Running,
    Fault
};

struct Qubit {
    int id;
    QubitTechnology technology;
    double frequencyGHz;
    double coherenceUs;
    double gateFidelity;
    double readoutFidelity;

    void validate() const {
        if (id < 0) {
            throw std::invalid_argument("Qubit ID cannot be negative");
        }
        if (frequencyGHz < 0.0 || coherenceUs <= 0.0) {
            throw std::invalid_argument("Invalid qubit physical parameters");
        }
        if (gateFidelity <= 0.0 || gateFidelity > 1.0) {
            throw std::invalid_argument("Invalid gate fidelity");
        }
        if (readoutFidelity <= 0.0 || readoutFidelity > 1.0) {
            throw std::invalid_argument("Invalid readout fidelity");
        }
    }
};

struct HardwareSubsystem {
    std::string name;
    std::vector<std::string> components;
    std::vector<std::string> constraints;
};

struct GateSpecification {
    std::string name;
    double durationNs;
    double errorRate;

    void validate() const {
        if (durationNs <= 0.0) {
            throw std::invalid_argument("Gate duration must be positive");
        }
        if (errorRate < 0.0 || errorRate >= 1.0) {
            throw std::invalid_argument("Gate error rate must be in [0, 1)");
        }
    }
};

struct StatusMeasurement {
    double temperatureK;
    double pressurePa;
    double controlErrorRate;
    bool readoutReady;

    void validate() const {
        if (temperatureK < 0.0 || pressurePa < 0.0) {
            throw std::invalid_argument("Physical measurements cannot be negative");
        }
        if (controlErrorRate < 0.0 || controlErrorRate > 1.0) {
            throw std::invalid_argument("Invalid control error rate");
        }
    }
};

class QuantumProcessor {
private:
    std::string name_;
    QubitTechnology technology_;
    ProcessorState state_{ProcessorState::Offline};
    std::map<int, Qubit> qubits_;
    std::vector<HardwareSubsystem> subsystems_;
    std::vector<GateSpecification> gates_;
    StatusMeasurement status_{0.0, 0.0, 1.0, false};

    static double average(const std::vector<double>& values) {
        if (values.empty()) {
            throw std::logic_error("Cannot average an empty collection");
        }
        return std::accumulate(values.begin(), values.end(), 0.0) /
               static_cast<double>(values.size());
    }

public:
    QuantumProcessor(
        std::string name,
        QubitTechnology technology,
        std::vector<Qubit> qubits,
        std::vector<HardwareSubsystem> subsystems,
        std::vector<GateSpecification> gates
    )
        : name_(std::move(name)),
          technology_(technology),
          subsystems_(std::move(subsystems)),
          gates_(std::move(gates)) {

        if (name_.empty()) {
            throw std::invalid_argument("Processor name is required");
        }

        for (const auto& qubit : qubits) {
            qubit.validate();

            if (qubit.technology != technology_) {
                throw std::invalid_argument("Qubit technology does not match processor");
            }

            if (!qubits_.emplace(qubit.id, qubit).second) {
                throw std::invalid_argument("Duplicate qubit ID");
            }
        }

        if (qubits_.empty()) {
            throw std::invalid_argument("Processor requires at least one qubit");
        }

        for (const auto& gate : gates_) {
            gate.validate();
        }
    }

    void initialize(StatusMeasurement measurement) {
        measurement.validate();

        if (state_ != ProcessorState::Offline) {
            throw std::logic_error("Processor is not offline");
        }

        state_ = ProcessorState::Initializing;
        status_ = measurement;

        // A superconducting processor cannot operate if its thermal
        // environment is outside the configured operating envelope.
        if (technology_ == QubitTechnology::Superconducting &&
            status_.temperatureK > 0.1) {
            state_ = ProcessorState::Fault;
            throw std::runtime_error("Cryogenic temperature is outside operating envelope");
        }

        if (!status_.readoutReady) {
            state_ = ProcessorState::Fault;
            throw std::runtime_error("Readout chain is not ready");
        }

        state_ = ProcessorState::Ready;
    }

    bool canRunCircuit(std::size_t circuitDepth) const {
        if (state_ != ProcessorState::Ready) {
            return false;
        }

        if (circuitDepth == 0 || gates_.empty()) {
            return false;
        }

        const double averageCoherenceUs =
            average([&]() {
                std::vector<double> result;
                result.reserve(qubits_.size());
                for (const auto& [id, q] : qubits_) {
                    result.push_back(q.coherenceUs);
                }
                return result;
            }());

        const double averageGateDurationNs =
            average([&]() {
                std::vector<double> result;
                result.reserve(gates_.size());
                for (const auto& gate : gates_) {
                    result.push_back(gate.durationNs);
                }
                return result;
            }());

        const double circuitTimeUs =
            static_cast<double>(circuitDepth) *
            averageGateDurationNs / 1000.0;

        return circuitTimeUs <= averageCoherenceUs;
    }

    double estimatedCircuitError(std::size_t gateCount) const {
        if (gates_.empty()) {
            throw std::logic_error("No gate specifications available");
        }

        const double averageError =
            average([&]() {
                std::vector<double> result;
                result.reserve(gates_.size());
                for (const auto& gate : gates_) {
                    result.push_back(gate.errorRate);
                }
                return result;
            }());

        // Independent-error approximation:
        // P(at least one error) = 1 - (1-p)^n.
        return 1.0 - std::pow(1.0 - averageError,
                              static_cast<double>(gateCount));
    }

    void runCircuit(std::size_t circuitDepth) {
        if (!canRunCircuit(circuitDepth)) {
            throw std::runtime_error(
                "Circuit rejected by processor state or coherence budget"
            );
        }

        state_ = ProcessorState::Running;
        const double error = estimatedCircuitError(circuitDepth);

        std::cout << "Running circuit\n"
                  << "  depth: " << circuitDepth << "\n"
                  << "  estimated circuit error: "
                  << std::fixed << std::setprecision(4)
                  << error << "\n";

        state_ = ProcessorState::Ready;
    }

    void printArchitecture() const {
        std::cout << "\nProcessor: " << name_ << "\n";
        std::cout << "Qubits: " << qubits_.size() << "\n";

        for (const auto& subsystem : subsystems_) {
            std::cout << "\n[" << subsystem.name << "]\n";
            std::cout << "Components: ";
            for (std::size_t i = 0; i < subsystem.components.size(); ++i) {
                if (i) std::cout << ", ";
                std::cout << subsystem.components[i];
            }

            std::cout << "\nConstraints: ";
            for (std::size_t i = 0; i < subsystem.constraints.size(); ++i) {
                if (i) std::cout << ", ";
                std::cout << subsystem.constraints[i];
            }
            std::cout << '\n';
        }
    }
};

int main() {
    try {
        std::vector<Qubit> qubits;

        for (int id = 0; id < 8; ++id) {
            qubits.push_back({
                id,
                QubitTechnology::Superconducting,
                5.0 + id * 0.03,
                85.0 - id * 2.0,
                0.9990 - id * 0.00002,
                0.985
            });
        }

        std::vector<HardwareSubsystem> subsystems = {
            {
                "Cryogenic system",
                {"dilution refrigerator", "mixing chamber", "thermal shielding"},
                {"limited cooling power", "vibration isolation", "thermalization"}
            },
            {
                "Microwave control",
                {"signal generators", "attenuators", "IQ mixers", "filters"},
                {"phase noise", "crosstalk", "pulse distortion"}
            },
            {
                "Readout",
                {"resonators", "quantum-limited amplifier", "digitizer"},
                {"amplifier saturation", "measurement noise"}
            },
            {
                "Classical control",
                {"FPGA controller", "clock source", "control software"},
                {"latency", "clock synchronization"}
            }
        };

        std::vector<GateSpecification> gates = {
            {"single-qubit gate", 25.0, 0.0009},
            {"two-qubit gate", 220.0, 0.008},
            {"measurement", 700.0, 0.015}
        };

        QuantumProcessor processor(
            "Cryogenic superconducting processor",
            QubitTechnology::Superconducting,
            qubits,
            subsystems,
            gates
        );

        processor.printArchitecture();

        StatusMeasurement healthyEnvironment{
            0.015,
            1e-7,
            0.001,
            true
        };

        processor.initialize(healthyEnvironment);

        std::cout << "\nCircuit eligibility:\n";
        for (std::size_t depth : {10, 100, 250, 500}) {
            std::cout << "  depth " << depth << ": "
                      << (processor.canRunCircuit(depth) ? "accepted" : "rejected")
                      << '\n';
        }

        processor.runCircuit(100);

        try {
            StatusMeasurement unsafeEnvironment{
                0.25,
                1e-7,
                0.001,
                true
            };
            QuantumProcessor unsafeProcessor(
                "Unsafe test processor",
                QubitTechnology::Superconducting,
                qubits,
                subsystems,
                gates
            );
            unsafeProcessor.initialize(unsafeEnvironment);
        } catch (const std::exception& error) {
            std::cout << "\nExpected initialization failure: "
                      << error.what() << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
