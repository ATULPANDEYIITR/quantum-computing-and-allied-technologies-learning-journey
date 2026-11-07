#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 1e-12;

class ControlException : public runtime_error {
public:
    using runtime_error::runtime_error;
};

class SafetyException : public ControlException {
public:
    using ControlException::ControlException;
};

class ValidationException : public ControlException {
public:
    using ControlException::ControlException;
};

enum class PulseType {
    X,
    Y,
    Arbitrary
};

enum class CalibrationStatus {
    Passed,
    Failed
};

string toString(PulseType type) {
    switch (type) {
        case PulseType::X: return "X";
        case PulseType::Y: return "Y";
        case PulseType::Arbitrary: return "ARBITRARY";
    }
    throw ValidationException("Unknown pulse type.");
}

struct Qubit {
    string id;
    double frequencyGHz;
    double t1Us;
    double t2Us;

    void validate() const {
        if (id.empty() || frequencyGHz <= 0 ||
            t1Us <= 0 || t2Us <= 0 ||
            t2Us > 2 * t1Us) {
            throw ValidationException("Invalid qubit parameters.");
        }
    }
};

struct HardwareLimits {
    double maxAmplitude = 10.0;
    double minDuration = 0.001;
    double maxDuration = 100.0;
    double maxDetuningMHz = 5.0;
    size_t maxPulses = 1000;
};

struct Pulse {
    string id;
    PulseType type;
    double amplitude;
    double durationUs;
    double phaseRad;
    double detuningMHz;
    double startUs;

    double endUs() const {
        return startUs + durationUs;
    }
};

struct BlochVector {
    double x = 0;
    double y = 0;
    double z = 1;

    double excitedProbability() const {
        return clamp((1.0 - z) / 2.0, 0.0, 1.0);
    }

    double norm() const {
        return sqrt(x*x + y*y + z*z);
    }

    void rotate(double ax, double ay, double az, double angle) {
        const double magnitude = sqrt(ax*ax + ay*ay + az*az);

        if (magnitude < EPSILON) return;

        const double ux = ax / magnitude;
        const double uy = ay / magnitude;
        const double uz = az / magnitude;

        const double c = cos(angle);
        const double s = sin(angle);

        const double dot = ux*x + uy*y + uz*z;

        const double cx = uy*z - uz*y;
        const double cy = uz*x - ux*z;
        const double cz = ux*y - uy*x;

        const double oldX = x;
        const double oldY = y;
        const double oldZ = z;

        x = oldX*c + cx*s + ux*dot*(1-c);
        y = oldY*c + cy*s + uy*dot*(1-c);
        z = oldZ*c + cz*s + uz*dot*(1-c);
    }
};

class PulseController {
private:
    HardwareLimits limits;
    size_t executionCount = 0;

public:
    explicit PulseController(HardwareLimits config)
        : limits(config) {
        if (limits.maxAmplitude <= 0 ||
            limits.minDuration <= 0 ||
            limits.maxDuration < limits.minDuration ||
            limits.maxDetuningMHz < 0 ||
            limits.maxPulses == 0) {
            throw ValidationException("Invalid hardware limits.");
        }
    }

    void validate(const Pulse& pulse) const {
        if (pulse.id.empty()) {
            throw ValidationException("Pulse ID is required.");
        }

        const double values[] = {
            pulse.amplitude,
            pulse.durationUs,
            pulse.phaseRad,
            pulse.detuningMHz,
            pulse.startUs
        };

        for (double value : values) {
            if (!isfinite(value)) {
                throw ValidationException("Non-finite pulse parameter.");
            }
        }

        if (pulse.amplitude < 0 ||
            pulse.durationUs < limits.minDuration ||
            pulse.durationUs > limits.maxDuration ||
            pulse.startUs < 0) {
            throw ValidationException("Invalid pulse parameters.");
        }

        if (pulse.amplitude > limits.maxAmplitude ||
            abs(pulse.detuningMHz) > limits.maxDetuningMHz) {
            throw SafetyException("Hardware safety limit exceeded.");
        }
    }

    BlochVector execute(
        const Pulse& pulse,
        BlochVector state = {}
    ) {
        validate(pulse);

        if (executionCount >= limits.maxPulses) {
            throw SafetyException("Pulse execution quota exceeded.");
        }

        const double ax = pulse.amplitude * cos(pulse.phaseRad);
        const double ay = pulse.amplitude * sin(pulse.phaseRad);
        const double az = 2 * PI * pulse.detuningMHz / 1000.0;

        const double frequency = sqrt(
            ax*ax + ay*ay + az*az
        );

        const double angle = frequency * pulse.durationUs;

        state.rotate(ax, ay, az, angle);

        ++executionCount;
        return state;
    }
};

class PulseSchedule {
private:
    vector<Pulse> pulses;
    const PulseController& controller;
    size_t maximumPulses;

public:
    PulseSchedule(
        const PulseController& control,
        size_t maxCount = 1000
    ) : controller(control), maximumPulses(maxCount) {}

    void add(const Pulse& pulse) {
        controller.validate(pulse);

        if (pulses.size() >= maximumPulses) {
            throw SafetyException("Schedule capacity exceeded.");
        }

        for (const auto& existing : pulses) {
            if (pulse.startUs < existing.endUs() &&
                existing.startUs < pulse.endUs()) {
                throw ValidationException("Pulse overlap detected.");
            }
        }

        pulses.push_back(pulse);

        sort(pulses.begin(), pulses.end(),
             [](const Pulse& a, const Pulse& b) {
                 return a.startUs < b.startUs;
             });
    }

    BlochVector run() const {
        BlochVector state;

        for (const auto& pulse : pulses) {
            state = controller.execute(pulse, state);
        }

        return state;
    }

    size_t size() const {
        return pulses.size();
    }
};

struct CalibrationRecord {
    string qubitId;
    double piAmplitude;
    double piOverTwoAmplitude;
    double excitationError;
    CalibrationStatus status;
};

class CalibrationEngine {
private:
    PulseController& controller;
    vector<CalibrationRecord> history;

public:
    explicit CalibrationEngine(PulseController& control)
        : controller(control) {}

    double measureRabi(double amplitude, double durationUs) {
        Pulse pulse{
            "RABI-MEASUREMENT",
            PulseType::X,
            amplitude,
            durationUs,
            0.0,
            0.0,
            0.0
        };

        return controller.execute(pulse).excitedProbability();
    }

    CalibrationRecord calibrate(
        const Qubit& qubit,
        double durationUs,
        double maxAmplitude,
        size_t samples = 101
    ) {
        qubit.validate();

        if (samples < 3 || samples > 10001) {
            throw ValidationException("Invalid sample count.");
        }

        if (maxAmplitude <= 0) {
            throw ValidationException("Amplitude must be positive.");
        }

        double bestAmplitude = 0;
        double bestProbability = -1;

        for (size_t i = 1; i < samples; ++i) {
            const double amplitude =
                maxAmplitude * i / (samples - 1);

            const double probability =
                measureRabi(amplitude, durationUs);

            if (probability > bestProbability) {
                bestProbability = probability;
                bestAmplitude = amplitude;
            }
        }

        CalibrationRecord result{
            qubit.id,
            bestAmplitude,
            bestAmplitude / 2,
            1.0 - bestProbability,
            bestProbability >= 0.95
                ? CalibrationStatus::Passed
                : CalibrationStatus::Failed
        };

        history.push_back(result);
        return result;
    }

    const vector<CalibrationRecord>& getHistory() const {
        return history;
    }
};

void runTests() {
    HardwareLimits limits;
    PulseController controller(limits);

    Pulse piPulse{
        "PI", PulseType::X, PI, 1.0, 0, 0, 0
    };

    auto result = controller.execute(piPulse);

    if (abs(result.excitedProbability() - 1.0) > 1e-9) {
        throw ControlException("Pi-pulse test failed.");
    }

    Pulse halfPulse{
        "PI-HALF", PulseType::X, PI/2, 1.0, 0, 0, 0
    };

    result = controller.execute(halfPulse);

    if (abs(result.excitedProbability() - 0.5) > 1e-9) {
        throw ControlException("Pi/2-pulse test failed.");
    }

    try {
        Pulse unsafe{
            "UNSAFE", PulseType::X, 100, 1, 0, 0, 0
        };
        controller.validate(unsafe);
        throw ControlException("Unsafe pulse was accepted.");
    } catch (const SafetyException&) {
        // Expected safety rejection.
    }

    cout << "All C++17 quantum-control tests passed.\n";
}

int main() {
    try {
        Qubit qubit{
            "QUBIT-001",
            5.0,
            100.0,
            80.0
        };

        qubit.validate();

        HardwareLimits limits;
        PulseController controller(limits);
        CalibrationEngine calibration(controller);

        cout << fixed << setprecision(6);
        cout << "\nQUANTUM CONTROL ENGINE\n";

        auto record = calibration.calibrate(
            qubit, 1.0, PI, 101
        );

        cout << "\nRABI CALIBRATION\n";
        cout << "Qubit: " << record.qubitId << '\n';
        cout << "Pi amplitude: " << record.piAmplitude << '\n';
        cout << "Pi/2 amplitude: "
             << record.piOverTwoAmplitude << '\n';
        cout << "Excitation error: "
             << record.excitationError << '\n';

        cout << "Status: "
             << (record.status == CalibrationStatus::Passed
                 ? "PASSED" : "FAILED") << '\n';

        PulseSchedule schedule(controller);

        schedule.add(Pulse{
            "CALIBRATED-PI",
            PulseType::X,
            record.piAmplitude,
            1.0,
            0,
            0,
            0
        });

        const auto state = schedule.run();

        cout << "\nEXECUTED PULSE SEQUENCE\n";
        cout << "Bloch X: " << state.x << '\n';
        cout << "Bloch Y: " << state.y << '\n';
        cout << "Bloch Z: " << state.z << '\n';
        cout << "Excited probability: "
             << state.excitedProbability() << '\n';

        runTests();

        return 0;

    } catch (const ControlException& error) {
        cerr << "CONTROL ERROR: " << error.what() << '\n';
        return 1;
    } catch (const exception& error) {
        cerr << "SYSTEM ERROR: " << error.what() << '\n';
        return 1;
    }
}
