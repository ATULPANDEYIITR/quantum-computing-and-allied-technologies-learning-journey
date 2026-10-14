#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using Complex = std::complex<double>;
using State = std::vector<Complex>;
using Bindings = std::unordered_map<std::string, double>;

constexpr double PI = 3.14159265358979323846;

struct AngleExpression {
    enum class Kind { Constant, Parameter, Add, Multiply };

    Kind kind;
    double constant_value = 0.0;
    std::string parameter_name;
    std::shared_ptr<AngleExpression> left;
    std::shared_ptr<AngleExpression> right;

    static AngleExpression constant(double value) {
        validate(value);
        AngleExpression result;
        result.kind = Kind::Constant;
        result.constant_value = value;
        return result;
    }

    static AngleExpression parameter(const std::string& name) {
        if (name.empty()) {
            throw std::invalid_argument("Parameter name cannot be empty.");
        }
        AngleExpression result;
        result.kind = Kind::Parameter;
        result.parameter_name = name;
        return result;
    }

    static AngleExpression binary(
        Kind kind, const AngleExpression& left, const AngleExpression& right) {
        AngleExpression result;
        result.kind = kind;
        result.left = std::make_shared<AngleExpression>(left);
        result.right = std::make_shared<AngleExpression>(right);
        return result;
    }

    static void validate(double value) {
        if (!std::isfinite(value)) {
            throw std::invalid_argument("Angles must be finite.");
        }
    }

    double evaluate(const Bindings& bindings) const {
        switch (kind) {
            case Kind::Constant:
                return constant_value;
            case Kind::Parameter: {
                const auto found = bindings.find(parameter_name);
                if (found == bindings.end()) {
                    throw std::invalid_argument(
                        "Missing parameter binding: " + parameter_name);
                }
                validate(found->second);
                return found->second;
            }
            case Kind::Add:
                return checked(left->evaluate(bindings) + right->evaluate(bindings));
            case Kind::Multiply:
                return checked(left->evaluate(bindings) * right->evaluate(bindings));
        }
        throw std::logic_error("Unknown expression kind.");
    }

    static double checked(double value) {
        validate(value);
        return value;
    }
};

enum class GateType { H, RX, RY, RZ, CNOT };

struct Gate {
    GateType type;
    int qubit;
    AngleExpression angle = AngleExpression::constant(0.0);
    int target = -1;
    bool has_angle = false;
};

class CircuitTemplate {
public:
    explicit CircuitTemplate(int qubits, std::string name)
        : qubits_(qubits), name_(std::move(name)) {
        if (qubits < 1 || qubits > 12) {
            throw std::invalid_argument("Use 1 through 12 qubits.");
        }
    }

    AngleExpression parameter(const std::string& name) {
        parameters_.insert(name);
        return AngleExpression::parameter(name);
    }

    CircuitTemplate& h(int qubit) {
        check_qubit(qubit);
        gates_.push_back({GateType::H, qubit});
        return *this;
    }

    CircuitTemplate& rotation(
        GateType type, int qubit, const AngleExpression& angle) {
        check_qubit(qubit);
        if (type != GateType::RX && type != GateType::RY && type != GateType::RZ) {
            throw std::invalid_argument("Rotation must be RX, RY, or RZ.");
        }
        Gate gate{type, qubit};
        gate.angle = angle;
        gate.has_angle = true;
        gates_.push_back(gate);
        return *this;
    }

    CircuitTemplate& cnot(int control, int target) {
        check_qubit(control);
        check_qubit(target);
        if (control == target) {
            throw std::invalid_argument("CNOT qubits must differ.");
        }
        Gate gate{GateType::CNOT, control};
        gate.target = target;
        gates_.push_back(gate);
        return *this;
    }

    std::vector<Gate> bind(const Bindings& bindings) const {
        for (const auto& name : bindings) {
            if (parameters_.find(name.first) == parameters_.end()) {
                throw std::invalid_argument("Unknown parameter: " + name.first);
            }
            AngleExpression::validate(name.second);
        }

        for (const auto& name : parameters_) {
            if (bindings.find(name) == bindings.end()) {
                throw std::invalid_argument("Unbound parameter: " + name);
            }
        }

        std::vector<Gate> result = gates_;
        for (auto& gate : result) {
            if (gate.has_angle) {
                gate.angle = AngleExpression::constant(gate.angle.evaluate(bindings));
            }
        }
        return result;
    }

    int qubits() const { return qubits_; }
    const std::string& name() const { return name_; }

    void describe() const {
        std::cout << name_ << " (" << qubits_ << " qubits)\n";
        for (std::size_t i = 0; i < gates_.size(); ++i) {
            const auto& gate = gates_[i];
            std::cout << "  " << i << ": " << gate_name(gate.type)
                      << " q" << gate.qubit;
            if (gate.type == GateType::CNOT) {
                std::cout << " -> q" << gate.target;
            } else if (gate.has_angle) {
                std::cout << " [symbolic angle]";
            }
            std::cout << '\n';
        }
    }

private:
    int qubits_;
    std::string name_;
    std::vector<Gate> gates_;
    std::map<std::string, bool> parameters_;

    void check_qubit(int qubit) const {
        if (qubit < 0 || qubit >= qubits_) {
            throw std::out_of_range("Invalid qubit index.");
        }
    }

    static std::string gate_name(GateType type) {
        switch (type) {
            case GateType::H: return "H";
            case GateType::RX: return "RX";
            case GateType::RY: return "RY";
            case GateType::RZ: return "RZ";
            case GateType::CNOT: return "CNOT";
        }
        return "UNKNOWN";
    }
};

void apply_h(State& state, int qubit) {
    const std::size_t stride = std::size_t{1} << qubit;
    const double scale = 1.0 / std::sqrt(2.0);

    for (std::size_t base = 0; base < state.size(); base += stride * 2) {
        for (std::size_t offset = 0; offset < stride; ++offset) {
            const auto first = base + offset;
            const auto second = first + stride;
            const Complex a = state[first];
            const Complex b = state[second];
            state[first] = (a + b) * scale;
            state[second] = (a - b) * scale;
        }
    }
}

void apply_rotation(State& state, GateType type, int qubit, double angle) {
    AngleExpression::validate(angle);
    const double c = std::cos(angle / 2.0);
    const double s = std::sin(angle / 2.0);
    const std::size_t stride = std::size_t{1} << qubit;

    for (std::size_t base = 0; base < state.size(); base += stride * 2) {
        for (std::size_t offset = 0; offset < stride; ++offset) {
            const auto first = base + offset;
            const auto second = first + stride;
            const Complex a = state[first];
            const Complex b = state[second];

            if (type == GateType::RX) {
                state[first] = c * a - Complex(0, s) * b;
                state[second] = -Complex(0, s) * a + c * b;
            } else if (type == GateType::RY) {
                state[first] = c * a - s * b;
                state[second] = s * a + c * b;
            } else if (type == GateType::RZ) {
                state[first] = Complex(c, -s) * a;
                state[second] = Complex(c, s) * b;
            } else {
                throw std::invalid_argument("Unsupported rotation gate.");
            }
        }
    }
}

void apply_cnot(State& state, int control, int target) {
    const std::size_t control_mask = std::size_t{1} << control;
    const std::size_t target_mask = std::size_t{1} << target;

    for (std::size_t index = 0; index < state.size(); ++index) {
        if ((index & control_mask) != 0 && (index & target_mask) == 0) {
            const std::size_t other = index | target_mask;
            std::swap(state[index], state[other]);
        }
    }
}

State simulate(int qubits, const std::vector<Gate>& gates) {
    State state(std::size_t{1} << qubits, Complex(0, 0));
    state[0] = Complex(1, 0);

    for (const auto& gate : gates) {
        switch (gate.type) {
            case GateType::H:
                apply_h(state, gate.qubit);
                break;
            case GateType::RX:
            case GateType::RY:
            case GateType::RZ:
                apply_rotation(state, gate.type, gate.qubit,
                               gate.angle.evaluate({}));
                break;
            case GateType::CNOT:
                apply_cnot(state, gate.qubit, gate.target);
                break;
        }
    }
    return state;
}

double expectation_z(const State& state, int qubit) {
    double result = 0.0;
    for (std::size_t index = 0; index < state.size(); ++index) {
        const double probability = std::norm(state[index]);
        result += ((index >> qubit) & 1U) ? -probability : probability;
    }
    return result;
}

int main() {
    try {
        // A calibration circuit models a two-qubit sensor whose response depends
        // on an input phase and two trainable device-control parameters.
        CircuitTemplate calibration(2, "sensor-calibration");
        const auto phase = calibration.parameter("phase");
        const auto drive = calibration.parameter("drive");
        const auto offset = calibration.parameter("offset");

        calibration.h(0)
            .rotation(GateType::RY, 0, phase)
            .rotation(GateType::RX, 1, drive)
            .cnot(0, 1)
            .rotation(
                GateType::RZ, 0,
                AngleExpression::binary(
                    AngleExpression::Kind::Add,
                    offset,
                    AngleExpression::binary(
                        AngleExpression::Kind::Multiply,
                        drive,
                        AngleExpression::constant(0.5))))
            .rotation(
                GateType::RY, 1,
                AngleExpression::binary(
                    AngleExpression::Kind::Multiply,
                    phase,
                    AngleExpression::constant(2.0)));

        calibration.describe();

        const Bindings settings{
            {"phase", 0.65},
            {"drive", -0.35},
            {"offset", 0.12}
        };

        const auto executable = calibration.bind(settings);
        const State output = simulate(calibration.qubits(), executable);

        double norm = 0.0;
        std::cout << std::fixed << std::setprecision(6);
        std::cout << "\nMeasurement distribution\n";
        for (std::size_t index = 0; index < output.size(); ++index) {
            const double probability = std::norm(output[index]);
            norm += probability;
            std::cout << "  |" << ((index >> 1U) & 1U)
                      << ((index >> 0U) & 1U) << "> = "
                      << probability << '\n';
        }

        if (std::abs(norm - 1.0) > 1e-9) {
            throw std::runtime_error("State normalization invariant failed.");
        }

        std::cout << "Expectation Z(q0): " << expectation_z(output, 0) << '\n';
        std::cout << "Expectation Z(q1): " << expectation_z(output, 1) << '\n';

        try {
            calibration.bind({{"phase", 0.3}});
        } catch (const std::invalid_argument& error) {
            std::cout << "\nRejected incomplete calibration: "
                      << error.what() << '\n';
        }

        try {
            calibration.bind({
                {"phase", 0.3}, {"drive", 0.2},
                {"offset", 0.1}, {"unexpected", 4.0}
            });
        } catch (const std::invalid_argument& error) {
            std::cout << "Rejected unknown calibration value: "
                      << error.what() << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << "Circuit execution failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
