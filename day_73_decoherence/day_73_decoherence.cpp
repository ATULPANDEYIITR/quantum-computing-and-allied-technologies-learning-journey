#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

constexpr double EPSILON = 1e-12;

enum class Environment {
    Isolated,
    Thermal,
    MagneticNoise,
    ElectricNoise,
    Vibrational,
    Mixed
};

string environmentName(Environment environment) {
    switch (environment) {
        case Environment::Isolated: return "Isolated";
        case Environment::Thermal: return "Thermal";
        case Environment::MagneticNoise: return "Magnetic Noise";
        case Environment::ElectricNoise: return "Electric Noise";
        case Environment::Vibrational: return "Vibrational";
        case Environment::Mixed: return "Mixed";
    }

    throw runtime_error("Unknown environment.");
}

struct DecoherenceParameters {
    double t1;
    double t2;
    double temperature;
    double equilibriumPopulation;
    Environment environment;

    void validate() const {
        if (!isfinite(t1) || !isfinite(t2) || t1 <= 0 || t2 <= 0) {
            throw invalid_argument("T1 and T2 must be positive and finite.");
        }

        if (t2 > 2.0 * t1) {
            throw invalid_argument("Physical constraint violated: T2 <= 2*T1.");
        }

        if (!isfinite(temperature) || temperature < 0) {
            throw invalid_argument("Invalid environmental temperature.");
        }

        if (!isfinite(equilibriumPopulation) ||
            equilibriumPopulation < 0 ||
            equilibriumPopulation > 1) {
            throw invalid_argument("Invalid equilibrium population.");
        }
    }

    double pureDephasingTime() const {
        double inverse =
            1.0 / t2 - 1.0 / (2.0 * t1);

        return inverse <= EPSILON
            ? INFINITY
            : 1.0 / inverse;
    }
};

struct BlochVector {
    double x;
    double y;
    double z;

    void validate() const {
        if (!isfinite(x) || !isfinite(y) || !isfinite(z)) {
            throw invalid_argument("Non-finite Bloch coordinates.");
        }

        double radiusSquared =
            x * x + y * y + z * z;

        if (radiusSquared > 1.0 + 1e-9) {
            throw invalid_argument("Bloch vector outside unit sphere.");
        }
    }

    double coherence() const {
        return hypot(x, y);
    }

    double purity() const {
        return (1.0 + x*x + y*y + z*z) / 2.0;
    }

    double excitedProbability() const {
        return (1.0 - z) / 2.0;
    }

    double groundProbability() const {
        return (1.0 + z) / 2.0;
    }
};

struct Observation {
    double time;
    BlochVector state;
};

class DecoherenceEngine {
private:
    DecoherenceParameters parameters;

public:
    explicit DecoherenceEngine(
        const DecoherenceParameters& configuration
    ) : parameters(configuration) {
        parameters.validate();
    }

    BlochVector evolve(
        const BlochVector& initial,
        double elapsed
    ) const {
        initial.validate();

        if (!isfinite(elapsed) || elapsed < 0) {
            throw invalid_argument("Invalid elapsed time.");
        }

        double transverseDecay =
            exp(-elapsed / parameters.t2);

        double longitudinalDecay =
            exp(-elapsed / parameters.t1);

        double equilibriumZ =
            1.0 - 2.0 * parameters.equilibriumPopulation;

        BlochVector result {
            initial.x * transverseDecay,
            initial.y * transverseDecay,
            equilibriumZ +
                (initial.z - equilibriumZ) * longitudinalDecay
        };

        result.validate();

        return result;
    }

    vector<Observation> simulate(
        const BlochVector& initial,
        double duration,
        size_t steps
    ) const {
        initial.validate();

        if (!isfinite(duration) || duration < 0) {
            throw invalid_argument("Duration cannot be negative.");
        }

        if (steps == 0 || steps > 10000000) {
            throw invalid_argument("Invalid number of simulation steps.");
        }

        vector<Observation> observations;
        observations.reserve(steps + 1);

        for (size_t i = 0; i <= steps; ++i) {
            double time =
                duration * static_cast<double>(i) /
                static_cast<double>(steps);

            observations.push_back({
                time,
                evolve(initial, time)
            });
        }

        return observations;
    }

    const DecoherenceParameters& getParameters() const {
        return parameters;
    }
};

double estimateDecayTime(
    const vector<Observation>& data
) {
    vector<pair<double, double>> points;

    for (const auto& observation : data) {
        double signal = observation.state.coherence();

        if (signal > EPSILON) {
            points.emplace_back(
                observation.time,
                log(signal)
            );
        }
    }

    if (points.size() < 2) {
        throw runtime_error("Insufficient observations for fitting.");
    }

    double meanX = 0;
    double meanY = 0;

    for (const auto& point : points) {
        meanX += point.first;
        meanY += point.second;
    }

    meanX /= points.size();
    meanY /= points.size();

    double numerator = 0;
    double denominator = 0;

    for (const auto& point : points) {
        numerator +=
            (point.first - meanX) *
            (point.second - meanY);

        denominator +=
            pow(point.first - meanX, 2);
    }

    if (denominator < EPSILON) {
        throw runtime_error("Cannot fit constant time coordinates.");
    }

    double slope = numerator / denominator;

    if (slope >= 0) {
        throw runtime_error("Signal does not exhibit exponential decay.");
    }

    return -1.0 / slope;
}

void exportCSV(
    const vector<Observation>& data,
    const string& filename
) {
    ofstream file(filename);

    if (!file.is_open()) {
        throw runtime_error("Unable to open output file.");
    }

    file << "time,x,y,z,coherence,purity,excited_probability\n";

    file << setprecision(12);

    for (const auto& observation : data) {
        const auto& state = observation.state;

        file << observation.time << ","
             << state.x << ","
             << state.y << ","
             << state.z << ","
             << state.coherence() << ","
             << state.purity() << ","
             << state.excitedProbability() << "\n";
    }

    if (!file.good()) {
        throw runtime_error("Failed while writing CSV.");
    }
}

void printExperiment(
    const DecoherenceParameters& parameters,
    const vector<Observation>& data
) {
    cout << "\nENVIRONMENT: "
         << environmentName(parameters.environment) << "\n";

    cout << "T1: " << parameters.t1 << "\n";
    cout << "T2: " << parameters.t2 << "\n";

    cout << "T_phi: "
         << parameters.pureDephasingTime() << "\n";

    cout << "\nTIME EVOLUTION\n";

    for (size_t i = 0; i < data.size(); i += 20) {
        const auto& item = data[i];

        cout << fixed << setprecision(4)
             << "t=" << setw(8) << item.time
             << " coherence=" << item.state.coherence()
             << " purity=" << item.state.purity()
             << " P1=" << item.state.excitedProbability()
             << "\n";
    }
}

int main() {
    try {
        DecoherenceParameters parameters {
            100.0,
            60.0,
            0.020,
            0.01,
            Environment::Mixed
        };

        DecoherenceEngine engine(parameters);

        BlochVector initial {
            1.0,
            0.0,
            0.0
        };

        auto observations = engine.simulate(
            initial,
            300.0,
            300
        );

        printExperiment(parameters, observations);

        double estimatedT2 =
            estimateDecayTime(observations);

        cout << "\nESTIMATED T2: "
             << estimatedT2 << "\n";

        BlochVector finalState =
            engine.evolve(initial, 100.0);

        cout << "\nFINAL STATE\n";
        cout << "X: " << finalState.x << "\n";
        cout << "Y: " << finalState.y << "\n";
        cout << "Z: " << finalState.z << "\n";
        cout << "Purity: " << finalState.purity() << "\n";

        exportCSV(observations, "decoherence_results.csv");

        if (abs(estimatedT2 - parameters.t2) > 1e-6) {
            throw runtime_error("T2 regression validation failed.");
        }

        if (observations.front().state.coherence() != 1.0) {
            throw runtime_error("Initial coherence validation failed.");
        }

        cout << "\nCSV export successful.\n";
        cout << "All simulation checks passed.\n";

    } catch (const exception& error) {
        cerr << "ERROR: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
