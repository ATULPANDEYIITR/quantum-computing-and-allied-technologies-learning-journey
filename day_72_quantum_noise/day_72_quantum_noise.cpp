#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Quantum Noise and Decoherence Modeling.
 *
 * Engineering focus:
 * - Bloch-sphere state representation
 * - Noise channel abstractions
 * - Physical parameter validation
 * - Noise composition
 * - Calibration from T1 and T2
 * - Measurement readout errors
 * - Merge-free numerical simulation
 */

constexpr double EPSILON = 1e-10;
constexpr double PI = 3.14159265358979323846;

struct BlochVector {
    double x = 0.0;
    double y = 0.0;
    double z = 1.0;

    double magnitude() const {
        return sqrt(x * x + y * y + z * z);
    }

    void validate() const {
        if (!isfinite(x) || !isfinite(y) || !isfinite(z)) {
            throw invalid_argument("Bloch coordinates must be finite");
        }

        if (magnitude() > 1.0 + EPSILON) {
            throw invalid_argument(
                "State lies outside the physical Bloch sphere"
            );
        }
    }

    double purity() const {
        validate();
        return (1.0 + magnitude() * magnitude()) / 2.0;
    }
};

enum class NoiseType {
    AmplitudeDamping,
    PureDephasing,
    Depolarizing,
    BitFlip,
    PhaseFlip,
    CoherentZ,
    ThermalRelaxation
};

string noiseName(NoiseType type) {
    static const map<NoiseType, string> names = {
        {NoiseType::AmplitudeDamping, "Amplitude damping"},
        {NoiseType::PureDephasing, "Pure dephasing"},
        {NoiseType::Depolarizing, "Depolarizing"},
        {NoiseType::BitFlip, "Bit flip"},
        {NoiseType::PhaseFlip, "Phase flip"},
        {NoiseType::CoherentZ, "Coherent Z rotation"},
        {NoiseType::ThermalRelaxation, "Thermal relaxation"}
    };

    return names.at(type);
}

void validateProbability(double p) {
    if (!isfinite(p) || p < 0.0 || p > 1.0) {
        throw invalid_argument("Probability must be in [0, 1]");
    }
}

class NoiseChannel {
private:
    string id;
    NoiseType type;
    double parameter;

public:
    NoiseChannel(
        string channelId,
        NoiseType channelType,
        double value
    ) : id(std::move(channelId)),
        type(channelType),
        parameter(value) {

        if (id.empty()) {
            throw invalid_argument("Channel ID cannot be empty");
        }

        if (!isfinite(parameter)) {
            throw invalid_argument("Channel parameter must be finite");
        }

        if (
            type != NoiseType::CoherentZ &&
            !(parameter >= 0.0 && parameter <= 1.0)
        ) {
            throw invalid_argument("Invalid channel probability");
        }

        if (
            type == NoiseType::PureDephasing &&
            parameter > 0.5
        ) {
            throw invalid_argument(
                "Pure dephasing probability cannot exceed 0.5"
            );
        }
    }

    string getId() const {
        return id;
    }

    NoiseType getType() const {
        return type;
    }

    BlochVector apply(const BlochVector& input) const {
        input.validate();

        BlochVector output = input;

        switch (type) {
            case NoiseType::AmplitudeDamping: {
                const double scale = sqrt(1.0 - parameter);

                output.x = scale * input.x;
                output.y = scale * input.y;
                output.z = parameter +
                    (1.0 - parameter) * input.z;
                break;
            }

            case NoiseType::PureDephasing: {
                const double scale = 1.0 - 2.0 * parameter;

                output.x = scale * input.x;
                output.y = scale * input.y;
                output.z = input.z;
                break;
            }

            case NoiseType::Depolarizing: {
                const double scale =
                    1.0 - (4.0 * parameter / 3.0);

                output.x = scale * input.x;
                output.y = scale * input.y;
                output.z = scale * input.z;
                break;
            }

            case NoiseType::BitFlip: {
                const double scale = 1.0 - 2.0 * parameter;

                output.x = input.x;
                output.y = scale * input.y;
                output.z = scale * input.z;
                break;
            }

            case NoiseType::PhaseFlip: {
                const double scale = 1.0 - 2.0 * parameter;

                output.x = scale * input.x;
                output.y = scale * input.y;
                output.z = input.z;
                break;
            }

            case NoiseType::CoherentZ: {
                const double c = cos(parameter);
                const double s = sin(parameter);

                output.x = c * input.x - s * input.y;
                output.y = s * input.x + c * input.y;
                output.z = input.z;
                break;
            }

            case NoiseType::ThermalRelaxation:
                throw logic_error(
                    "Use ThermalRelaxationChannel for thermal noise"
                );
        }

        output.validate();
        return output;
    }
};

class ThermalRelaxationChannel {
private:
    double gamma;
    double excitedPopulation;

public:
    ThermalRelaxationChannel(double g, double q)
        : gamma(g), excitedPopulation(q) {
        validateProbability(gamma);
        validateProbability(excitedPopulation);
    }

    BlochVector apply(const BlochVector& input) const {
        input.validate();

        const double scale = sqrt(1.0 - gamma);
        const double equilibriumZ = 1.0 - 2.0 * excitedPopulation;

        BlochVector output {
            scale * input.x,
            scale * input.y,
            gamma * equilibriumZ + (1.0 - gamma) * input.z
        };

        output.validate();
        return output;
    }
};

class QuantumNoisePipeline {
private:
    vector<NoiseChannel> channels;

public:
    void add(const NoiseChannel& channel) {
        for (const auto& existing : channels) {
            if (existing.getId() == channel.getId()) {
                throw invalid_argument("Duplicate channel ID");
            }
        }

        channels.push_back(channel);
    }

    BlochVector execute(BlochVector state) const {
        state.validate();

        for (const auto& channel : channels) {
            state = channel.apply(state);
        }

        return state;
    }

    void report() const {
        cout << "\nREGISTERED CHANNELS\n";

        for (const auto& channel : channels) {
            cout << "  " << channel.getId() << '\n';
        }
    }
};

struct CoherenceCalibration {
    double t1;
    double t2;

    CoherenceCalibration(double relaxation, double coherence)
        : t1(relaxation), t2(coherence) {

        if (
            !isfinite(t1) ||
            !isfinite(t2) ||
            t1 <= 0.0 ||
            t2 <= 0.0 ||
            t2 > 2.0 * t1
        ) {
            throw invalid_argument(
                "Physical constraint requires 0 < T2 <= 2*T1"
            );
        }
    }

    double amplitudeProbability(double duration) const {
        if (duration < 0.0) {
            throw invalid_argument("Duration cannot be negative");
        }

        return 1.0 - exp(-duration / t1);
    }

    double dephasingProbability(double duration) const {
        if (duration < 0.0) {
            throw invalid_argument("Duration cannot be negative");
        }

        const double inverseTphi =
            max(0.0, 1.0 / t2 - 1.0 / (2.0 * t1));

        return (
            1.0 - exp(-duration * inverseTphi)
        ) / 2.0;
    }
};

struct MeasurementResult {
    double zero;
    double one;
};

MeasurementResult measure(
    const BlochVector& state,
    double p01,
    double p10
) {
    state.validate();
    validateProbability(p01);
    validateProbability(p10);

    const double actualZero = (1.0 + state.z) / 2.0;
    const double actualOne = (1.0 - state.z) / 2.0;

    return {
        actualZero * (1.0 - p01) + actualOne * p10,
        actualZero * p01 + actualOne * (1.0 - p10)
    };
}

double fidelity(
    const BlochVector& actual,
    const BlochVector& target
) {
    actual.validate();
    target.validate();

    const double dot =
        actual.x * target.x +
        actual.y * target.y +
        actual.z * target.z;

    return (1.0 + dot) / 2.0;
}

void printState(
    const string& label,
    const BlochVector& state
) {
    cout << fixed << setprecision(6);
    cout << label << ": ("
         << state.x << ", "
         << state.y << ", "
         << state.z << ")\n";

    cout << "  Purity: " << state.purity() << '\n';
}

int main() {
    try {
        const BlochVector initial {1.0, 0.0, 0.0};
        const BlochVector target {1.0, 0.0, 0.0};

        QuantumNoisePipeline pipeline;

        pipeline.add({
            "energy-relaxation",
            NoiseType::AmplitudeDamping,
            0.15
        });

        pipeline.add({
            "environmental-dephasing",
            NoiseType::PureDephasing,
            0.10
        });

        pipeline.add({
            "depolarizing-gate-error",
            NoiseType::Depolarizing,
            0.05
        });

        pipeline.add({
            "coherent-calibration-error",
            NoiseType::CoherentZ,
            0.04
        });

        pipeline.report();

        const BlochVector finalState =
            pipeline.execute(initial);

        cout << "\nQUANTUM STATE ANALYSIS\n";

        printState("Initial state", initial);
        printState("Final state", finalState);

        cout << "State fidelity: "
             << fidelity(finalState, target) << '\n';

        const CoherenceCalibration calibration(
            100e-6,
            70e-6
        );

        const double duration = 20e-6;

        const double gamma =
            calibration.amplitudeProbability(duration);

        const double phase =
            calibration.dephasingProbability(duration);

        cout << "\nT1/T2 CALIBRATION\n";
        cout << "T1: " << calibration.t1 << " seconds\n";
        cout << "T2: " << calibration.t2 << " seconds\n";
        cout << "Amplitude damping: " << gamma << '\n';
        cout << "Pure dephasing: " << phase << '\n';

        ThermalRelaxationChannel thermal(gamma, 0.08);

        const BlochVector thermalState =
            thermal.apply(initial);

        printState("Thermal relaxation output", thermalState);

        const MeasurementResult measurement =
            measure(finalState, 0.03, 0.05);

        cout << "\nMEASUREMENT READOUT\n";
        cout << "Reported zero: " << measurement.zero << '\n';
        cout << "Reported one: " << measurement.one << '\n';

        if (abs(measurement.zero + measurement.one - 1.0) > EPSILON) {
            throw runtime_error("Measurement probabilities do not sum to one");
        }

        cout << "\nAll physical validation checks passed.\n";

    } catch (const exception& error) {
        cerr << "Simulation error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
