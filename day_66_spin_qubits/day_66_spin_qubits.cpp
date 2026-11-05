/*
 * Spin Qubits in Semiconductor Quantum Systems
 *
 * C++17 implementation of a two-spin quantum-dot control and
 * gate-fidelity evaluation engine.
 *
 * Models:
 * - Bloch-vector state representation
 * - Single-spin rotations
 * - T1 relaxation and T2 dephasing
 * - Exchange interaction
 * - Two-spin singlet/triplet dynamics
 * - Control pulse validation
 * - Device constraints
 * - Measurement probabilities
 *
 * Compile: g++ -std=c++17 -O2 -Wall -Wextra spin_qubits.cpp -o spin_qubits
 */

#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace quantum {

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 1e-10;

enum class Material {
    Silicon,
    Germanium,
    GalliumArsenide
};

enum class Axis {
    X,
    Y,
    Z
};

struct Device {
    std::string id;
    Material material;
    double magneticFieldTesla;
    double temperatureMilliKelvin;
    double t1Microseconds;
    double t2Microseconds;
    double exchangeCouplingMHz;

    void validate() const {
        if (id.empty()) {
            throw std::invalid_argument("Device ID is required.");
        }

        if (magneticFieldTesla < 0 ||
            temperatureMilliKelvin <= 0 ||
            t1Microseconds <= 0 ||
            t2Microseconds <= 0 ||
            exchangeCouplingMHz < 0) {
            throw std::invalid_argument("Invalid device parameters.");
        }

        if (t2Microseconds > 2.0 * t1Microseconds) {
            throw std::invalid_argument("T2 cannot exceed 2*T1.");
        }
    }
};

struct BlochVector {
    double x = 0.0;
    double y = 0.0;
    double z = 1.0;

    double magnitude() const {
        return std::sqrt(x * x + y * y + z * z);
    }

    double purity() const {
        return (1.0 + magnitude() * magnitude()) / 2.0;
    }

    double probabilityZero() const {
        return (1.0 + z) / 2.0;
    }

    double probabilityOne() const {
        return (1.0 - z) / 2.0;
    }

    void validate() const {
        if (!std::isfinite(x) ||
            !std::isfinite(y) ||
            !std::isfinite(z)) {
            throw std::invalid_argument("Non-finite Bloch coordinate.");
        }

        if (magnitude() > 1.0 + EPSILON) {
            throw std::invalid_argument("Bloch vector exceeds unit sphere.");
        }
    }
};

struct ControlPulse {
    Axis axis;
    double angleRadians;
    double durationNanoseconds;
    std::string mechanism;

    void validate() const {
        if (!std::isfinite(angleRadians) ||
            !std::isfinite(durationNanoseconds) ||
            durationNanoseconds <= 0) {
            throw std::invalid_argument("Invalid control pulse.");
        }

        if (mechanism != "ESR" &&
            mechanism != "EDSR" &&
            mechanism != "VIRTUAL_Z") {
            throw std::invalid_argument("Unsupported control mechanism.");
        }

        if (mechanism == "VIRTUAL_Z" && axis != Axis::Z) {
            throw std::invalid_argument("Virtual-Z must rotate around Z.");
        }
    }
};

class SpinQubit {
private:
    std::string id;
    const Device& device;
    BlochVector state;
    std::size_t gateCount = 0;

public:
    SpinQubit(std::string qubitId, const Device& quantumDevice)
        : id(std::move(qubitId)), device(quantumDevice) {
        if (id.empty()) {
            throw std::invalid_argument("Qubit ID is required.");
        }

        device.validate();
    }

    const std::string& getId() const {
        return id;
    }

    const BlochVector& getState() const {
        return state;
    }

    std::size_t getGateCount() const {
        return gateCount;
    }

    void setState(const BlochVector& newState) {
        newState.validate();
        state = newState;
    }

    BlochVector rotate(Axis axis, double angle) const {
        if (!std::isfinite(angle)) {
            throw std::invalid_argument("Angle must be finite.");
        }

        const double c = std::cos(angle);
        const double s = std::sin(angle);

        BlochVector result;

        switch (axis) {
            case Axis::X:
                result = {
                    state.x,
                    state.y * c - state.z * s,
                    state.y * s + state.z * c
                };
                break;

            case Axis::Y:
                result = {
                    state.x * c + state.z * s,
                    state.y,
                    -state.x * s + state.z * c
                };
                break;

            case Axis::Z:
                result = {
                    state.x * c - state.y * s,
                    state.x * s + state.y * c,
                    state.z
                };
                break;
        }

        result.validate();
        return result;
    }

    void execute(const ControlPulse& pulse) {
        pulse.validate();

        state = rotate(pulse.axis, pulse.angleRadians);
        ++gateCount;
    }

    void relax(double durationMicroseconds) {
        if (!std::isfinite(durationMicroseconds) ||
            durationMicroseconds < 0) {
            throw std::invalid_argument("Invalid relaxation duration.");
        }

        const double decay =
            std::exp(-durationMicroseconds / device.t1Microseconds);

        state.x *= std::sqrt(decay);
        state.y *= std::sqrt(decay);
        state.z = 1.0 - (1.0 - state.z) * decay;

        state.validate();
    }

    void dephase(double durationMicroseconds) {
        if (!std::isfinite(durationMicroseconds) ||
            durationMicroseconds < 0) {
            throw std::invalid_argument("Invalid dephasing duration.");
        }

        const double decay =
            std::exp(-durationMicroseconds / device.t2Microseconds);

        state.x *= decay;
        state.y *= decay;

        state.validate();
    }

    void evolve(double durationMicroseconds) {
        relax(durationMicroseconds);
        dephase(durationMicroseconds);
    }

    double precessionAngle(double durationMicroseconds) const {
        if (!std::isfinite(durationMicroseconds) ||
            durationMicroseconds < 0) {
            throw std::invalid_argument("Invalid evolution duration.");
        }

        constexpr double gamma = 1.76085963023e11;

        const double angle = gamma *
            device.magneticFieldTesla *
            durationMicroseconds * 1e-6;

        return std::fmod(angle, 2.0 * PI);
    }
};

/*
 * Two-spin state vector:
 *
 * |psi> = a|00> + b|01> + c|10> + d|11>
 *
 * Complex amplitudes are represented using pairs of doubles.
 */
struct Complex {
    double real = 0;
    double imag = 0;

    Complex operator+(const Complex& other) const {
        return {real + other.real, imag + other.imag};
    }

    Complex operator*(const Complex& other) const {
        return {
            real * other.real - imag * other.imag,
            real * other.imag + imag * other.real
        };
    }

    Complex operator*(double scalar) const {
        return {real * scalar, imag * scalar};
    }

    double normSquared() const {
        return real * real + imag * imag;
    }
};

class TwoSpinSystem {
private:
    // Basis order: |00>, |01>, |10>, |11>.
    std::array<Complex, 4> amplitudes{};

public:
    TwoSpinSystem() {
        amplitudes[0] = {1, 0};
    }

    void setState(const std::array<Complex, 4>& newState) {
        double norm = 0;

        for (const auto& amplitude : newState) {
            if (!std::isfinite(amplitude.real) ||
                !std::isfinite(amplitude.imag)) {
                throw std::invalid_argument("Invalid complex amplitude.");
            }

            norm += amplitude.normSquared();
        }

        if (std::abs(norm - 1.0) > 1e-8) {
            throw std::invalid_argument("Two-spin state must be normalized.");
        }

        amplitudes = newState;
    }

    void applyExchange(double couplingMHz, double durationMicroseconds) {
        if (couplingMHz < 0 || durationMicroseconds < 0 ||
            !std::isfinite(couplingMHz) ||
            !std::isfinite(durationMicroseconds)) {
            throw std::invalid_argument("Invalid exchange parameters.");
        }

        /*
         * H = J/4 (sigma_x sigma_x +
         *          sigma_y sigma_y +
         *          sigma_z sigma_z)
         *
         * The |01>, |10> subspace evolves by exchanging amplitudes.
         * The parallel-spin states acquire a common phase.
         *
         * J is interpreted as an energy-equivalent frequency.
         */
        const double phase = 2.0 * PI *
            couplingMHz * durationMicroseconds;

        const Complex phaseFactor = {
            std::cos(-phase / 4.0),
            std::sin(-phase / 4.0)
        };

        const Complex mixingFactor = {
            std::cos(phase / 2.0),
            std::sin(phase / 2.0)
        };

        Complex newA = amplitudes[0] * phaseFactor;
        Complex newD = amplitudes[3] * phaseFactor;

        const Complex sum = amplitudes[1] + amplitudes[2];
        const Complex difference = amplitudes[1] + amplitudes[2] * -1.0;

        const Complex symmetric = sum * phaseFactor;
        const Complex antisymmetric = difference * mixingFactor;

        Complex newB = (symmetric + antisymmetric) * 0.5;
        Complex newC = (symmetric + antisymmetric * -1.0) * 0.5;

        amplitudes = {newA, newB, newC, newD};
    }

    std::array<double, 4> measurementProbabilities() const {
        std::array<double, 4> probabilities{};

        for (std::size_t i = 0; i < amplitudes.size(); ++i) {
            probabilities[i] = amplitudes[i].normSquared();
        }

        return probabilities;
    }

    double singletProbability() const {
        const Complex difference =
            amplitudes[1] + amplitudes[2] * -1.0;

        return difference.normSquared() / 2.0;
    }
};

class ExchangeScheduler {
private:
    struct Reservation {
        double start;
        double end;
        std::string first;
        std::string second;
    };

    std::vector<Reservation> reservations;

public:
    void reserve(
        const SpinQubit& first,
        const SpinQubit& second,
        double start,
        double duration
    ) {
        if (first.getId() == second.getId()) {
            throw std::invalid_argument("Exchange requires distinct qubits.");
        }

        if (start < 0 || duration <= 0 ||
            !std::isfinite(start) || !std::isfinite(duration)) {
            throw std::invalid_argument("Invalid reservation interval.");
        }

        const double end = start + duration;

        for (const auto& reservation : reservations) {
            if (start < reservation.end && end > reservation.start) {
                throw std::runtime_error("Exchange channel conflict.");
            }
        }

        reservations.push_back({
            start, end, first.getId(), second.getId()
        });
    }

    std::size_t reservationCount() const {
        return reservations.size();
    }
};

void printState(const BlochVector& state) {
    std::cout << std::fixed << std::setprecision(6)
              << "Bloch vector: ("
              << state.x << ", "
              << state.y << ", "
              << state.z << ")\n"
              << "Purity: " << state.purity() << '\n'
              << "P(0): " << state.probabilityZero() << '\n'
              << "P(1): " << state.probabilityOne() << '\n';
}

} // namespace quantum

int main() {
    using namespace quantum;

    try {
        Device device{
            "SI-QD-001",
            Material::Silicon,
            0.5,
            20.0,
            1000.0,
            100.0,
            5.0
        };

        device.validate();

        SpinQubit q0("Q0", device);
        SpinQubit q1("Q1", device);

        std::cout << "INITIAL STATE\n";
        printState(q0.getState());

        ControlPulse hadamardEquivalent{
            Axis::Y,
            PI / 2.0,
            50.0,
            "ESR"
        };

        q0.execute(hadamardEquivalent);

        std::cout << "\nAFTER CONTROL PULSE\n";
        printState(q0.getState());

        q0.evolve(10.0);

        std::cout << "\nAFTER RELAXATION AND DEPHASING\n";
        printState(q0.getState());

        std::cout << "\nMAGNETIC PRECESSION ANGLE\n";
        std::cout << q0.precessionAngle(0.001) << " radians\n";

        TwoSpinSystem pair;

        const double invSqrtTwo = 1.0 / std::sqrt(2.0);

        // Prepare the singlet state (|01> - |10>)/sqrt(2).
        pair.setState({
            Complex{0, 0},
            Complex{invSqrtTwo, 0},
            Complex{-invSqrtTwo, 0},
            Complex{0, 0}
        });

        std::cout << "\nINITIAL SINGLET PROBABILITY\n";
        std::cout << pair.singletProbability() << '\n';

        pair.applyExchange(5.0, 0.05);

        std::cout << "\nAFTER EXCHANGE INTERACTION\n";

        const auto probabilities = pair.measurementProbabilities();

        for (std::size_t i = 0; i < probabilities.size(); ++i) {
            std::cout << "P(" << i << "): "
                      << probabilities[i] << '\n';
        }

        std::cout << "Singlet probability: "
                  << pair.singletProbability() << '\n';

        ExchangeScheduler scheduler;
        scheduler.reserve(q0, q1, 0.0, 0.05);

        std::cout << "\nEXCHANGE RESERVATIONS\n";
        std::cout << scheduler.reservationCount() << '\n';

        std::cout << "\nGATES EXECUTED: "
                  << q0.getGateCount() << '\n';

    } catch (const std::exception& error) {
        std::cerr << "Quantum system error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
