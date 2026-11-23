#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

using Complex = complex<double>;
using StateVector = vector<Complex>;

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 1e-9;

enum class EncodingType {
    ANGLE,
    ZZ,
    IQP
};

struct FeatureVector {
    vector<double> values;

    explicit FeatureVector(vector<double> input)
        : values(move(input)) {
        if (values.empty()) {
            throw invalid_argument("Feature vector cannot be empty.");
        }

        for (double value : values) {
            if (!isfinite(value)) {
                throw invalid_argument("Non-finite feature detected.");
            }
        }
    }

    FeatureVector normalize(
        double lower = -PI,
        double upper = PI
    ) const {
        if (lower >= upper) {
            throw invalid_argument("Invalid normalization bounds.");
        }

        auto [minimum, maximum] = minmax_element(
            values.begin(), values.end()
        );

        vector<double> result;
        result.reserve(values.size());

        for (double value : values) {
            if (*minimum == *maximum) {
                result.push_back((lower + upper) / 2);
            } else {
                result.push_back(
                    lower +
                    (value - *minimum) * (upper - lower) /
                    (*maximum - *minimum)
                );
            }
        }

        return FeatureVector(move(result));
    }
};

struct QuantumState {
    StateVector amplitudes;
    size_t qubits;

    QuantumState(StateVector state, size_t count)
        : amplitudes(move(state)), qubits(count) {
        validate();
    }

    double normSquared() const {
        double result = 0;

        for (const auto& amplitude : amplitudes) {
            result += norm(amplitude);
        }

        return result;
    }

    void validate() const {
        if (qubits == 0 || qubits >= 63) {
            throw invalid_argument("Invalid qubit count.");
        }

        if (amplitudes.size() != (1ULL << qubits)) {
            throw invalid_argument("Invalid statevector dimension.");
        }

        for (const auto& amplitude : amplitudes) {
            if (
                !isfinite(amplitude.real()) ||
                !isfinite(amplitude.imag())
            ) {
                throw runtime_error("Non-finite amplitude.");
            }
        }

        if (abs(normSquared() - 1.0) > EPSILON) {
            throw runtime_error("Quantum state is not normalized.");
        }
    }

    vector<double> probabilities() const {
        vector<double> result;
        result.reserve(amplitudes.size());

        for (const auto& amplitude : amplitudes) {
            result.push_back(norm(amplitude));
        }

        return result;
    }
};

struct CircuitConfig {
    EncodingType encoding = EncodingType::ZZ;
    int repetitions = 1;
    double entanglementStrength = 1.0;

    void validate() const {
        if (repetitions < 1) {
            throw invalid_argument("Repetitions must be positive.");
        }

        if (!isfinite(entanglementStrength)) {
            throw invalid_argument("Invalid entanglement strength.");
        }
    }
};

class QuantumFeatureMap {
private:
    CircuitConfig config;

    static void applyRY(
        StateVector& state,
        size_t qubit,
        double theta
    ) {
        size_t mask = 1ULL << qubit;

        double c = cos(theta / 2);
        double s = sin(theta / 2);

        for (size_t i = 0; i < state.size(); ++i) {
            if (i & mask) continue;

            size_t j = i | mask;

            Complex zero = state[i];
            Complex one = state[j];

            state[i] = c * zero - s * one;
            state[j] = s * zero + c * one;
        }
    }

    static void applyRZ(
        StateVector& state,
        size_t qubit,
        double theta
    ) {
        size_t mask = 1ULL << qubit;

        for (size_t i = 0; i < state.size(); ++i) {
            double sign = (i & mask) ? 1.0 : -1.0;

            state[i] *= exp(
                Complex(0, sign * theta / 2)
            );
        }
    }

    static void applyZZ(
        StateVector& state,
        size_t first,
        size_t second,
        double theta
    ) {
        if (first == second) {
            throw invalid_argument("ZZ gate requires distinct qubits.");
        }

        size_t firstMask = 1ULL << first;
        size_t secondMask = 1ULL << second;

        for (size_t i = 0; i < state.size(); ++i) {
            bool firstBit = i & firstMask;
            bool secondBit = i & secondMask;

            double eigenvalue =
                firstBit == secondBit ? 1.0 : -1.0;

            state[i] *= exp(
                Complex(0, -theta * eigenvalue / 2)
            );
        }
    }

public:
    explicit QuantumFeatureMap(CircuitConfig configuration)
        : config(configuration) {
        config.validate();
    }

    QuantumState encode(const FeatureVector& features) const {
        const size_t qubits = features.values.size();

        // A statevector requires exponential memory.
        if (qubits > 20) {
            throw invalid_argument(
                "Exact simulation is limited to 20 qubits."
            );
        }

        StateVector state(1ULL << qubits, Complex(0, 0));
        state[0] = Complex(1, 0);

        for (int layer = 0; layer < config.repetitions; ++layer) {
            for (size_t q = 0; q < qubits; ++q) {
                double value = features.values[q];

                switch (config.encoding) {
                    case EncodingType::ANGLE:
                        applyRY(state, q, value);
                        break;

                    case EncodingType::ZZ:
                        applyRY(state, q, 2 * value);
                        applyRZ(state, q, value);
                        break;

                    case EncodingType::IQP:
                        applyRY(state, q, value);
                        applyRZ(state, q, 2 * value);
                        break;
                }
            }

            if (config.encoding != EncodingType::ANGLE) {
                for (size_t i = 0; i < qubits; ++i) {
                    for (size_t j = i + 1; j < qubits; ++j) {
                        double theta;

                        if (config.encoding == EncodingType::ZZ) {
                            theta =
                                config.entanglementStrength *
                                features.values[i] *
                                features.values[j];
                        } else {
                            theta =
                                2 * features.values[i] *
                                features.values[j];
                        }

                        applyZZ(state, i, j, theta);
                    }
                }
            }
        }

        return QuantumState(move(state), qubits);
    }
};

class QuantumKernel {
public:
    static double fidelity(
        const QuantumState& first,
        const QuantumState& second
    ) {
        if (first.qubits != second.qubits) {
            throw invalid_argument(
                "State dimensions must match."
            );
        }

        Complex overlap(0, 0);

        for (size_t i = 0; i < first.amplitudes.size(); ++i) {
            overlap +=
                conj(first.amplitudes[i]) *
                second.amplitudes[i];
        }

        return clamp(norm(overlap), 0.0, 1.0);
    }

    static vector<vector<double>> matrix(
        const vector<QuantumState>& states
    ) {
        size_t n = states.size();

        vector<vector<double>> result(
            n, vector<double>(n, 0)
        );

        // Symmetry avoids calculating both K(i,j) and K(j,i).
        for (size_t i = 0; i < n; ++i) {
            for (size_t j = i; j < n; ++j) {
                double value = fidelity(states[i], states[j]);

                result[i][j] = value;
                result[j][i] = value;
            }
        }

        return result;
    }
};

class MeasurementSimulator {
public:
    static vector<size_t> sample(
        const QuantumState& state,
        size_t shots,
        unsigned seed = 42
    ) {
        if (shots == 0) {
            throw invalid_argument("Shots must be positive.");
        }

        auto probabilities = state.probabilities();

        mt19937 generator(seed);

        discrete_distribution<size_t> distribution(
            probabilities.begin(),
            probabilities.end()
        );

        vector<size_t> counts(probabilities.size(), 0);

        for (size_t i = 0; i < shots; ++i) {
            counts[distribution(generator)]++;
        }

        return counts;
    }
};

string encodingName(EncodingType encoding) {
    switch (encoding) {
        case EncodingType::ANGLE:
            return "ANGLE";
        case EncodingType::ZZ:
            return "ZZ";
        case EncodingType::IQP:
            return "IQP";
    }

    return "UNKNOWN";
}

void printKernel(
    const vector<vector<double>>& matrix
) {
    for (const auto& row : matrix) {
        for (double value : row) {
            cout << setw(12) << fixed
                 << setprecision(6) << value;
        }
        cout << '\n';
    }
}

void runExperiment() {
    vector<FeatureVector> dataset = {
        FeatureVector({0.2, 0.4, 0.6}),
        FeatureVector({0.3, 0.7, 0.5}),
        FeatureVector({0.8, 0.2, 0.9}),
        FeatureVector({0.9, 0.6, 0.1})
    };

    cout << "QUANTUM FEATURE MAP EXPERIMENT\n";
    cout << "==============================\n";

    vector<FeatureVector> normalized;

    for (const auto& sample : dataset) {
        normalized.push_back(sample.normalize());
    }

    vector<EncodingType> encodings = {
        EncodingType::ANGLE,
        EncodingType::ZZ,
        EncodingType::IQP
    };

    for (EncodingType encoding : encodings) {
        cout << "\nFeature map: "
             << encodingName(encoding) << '\n';

        CircuitConfig config;
        config.encoding = encoding;
        config.repetitions = 2;
        config.entanglementStrength = 0.75;

        QuantumFeatureMap featureMap(config);

        vector<QuantumState> states;

        for (const auto& sample : normalized) {
            states.push_back(featureMap.encode(sample));
        }

        cout << "Statevector dimension: "
             << states[0].amplitudes.size() << '\n';

        cout << "State normalization: "
             << states[0].normSquared() << '\n';

        auto kernel = QuantumKernel::matrix(states);

        cout << "\nQuantum kernel matrix:\n";
        printKernel(kernel);

        cout << "\nMeasurement counts:\n";

        auto counts = MeasurementSimulator::sample(
            states[0], 1000
        );

        for (size_t i = 0; i < counts.size(); ++i) {
            if (counts[i] == 0) continue;

            string binary = "";

            for (size_t bit = 0; bit < states[0].qubits; ++bit) {
                binary +=
                    ((i >> (states[0].qubits - bit - 1)) & 1)
                    ? '1' : '0';
            }

            cout << binary << ": " << counts[i] << '\n';
        }

        if (abs(kernel[0][0] - 1.0) > EPSILON) {
            throw runtime_error("Self-fidelity test failed.");
        }
    }

    cout << "\nValidation tests:\n";

    try {
        FeatureVector invalid({0.1, numeric_limits<double>::quiet_NaN()});
    } catch (const invalid_argument& error) {
        cout << "Invalid input rejected: "
             << error.what() << '\n';
    }

    try {
        CircuitConfig invalid;
        invalid.repetitions = 0;
        invalid.validate();
    } catch (const invalid_argument& error) {
        cout << "Invalid circuit rejected: "
             << error.what() << '\n';
    }

    cout << "\nAll experiments completed.\n";
}

int main() {
    try {
        runExperiment();
        return 0;
    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';
        return 1;
    }
}
