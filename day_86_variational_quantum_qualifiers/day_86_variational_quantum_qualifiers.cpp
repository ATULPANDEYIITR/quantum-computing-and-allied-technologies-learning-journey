#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

namespace vqc {

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 1e-10;

enum class Label {
    Negative = 0,
    Positive = 1
};

struct Sample {
    array<double, 2> features;
    Label label;

    void validate() const {
        for (double x : features) {
            if (!isfinite(x)) {
                throw invalid_argument("Non-finite feature.");
            }
        }
    }

    int target() const {
        return static_cast<int>(label);
    }
};

struct Metrics {
    double accuracy = 0.0;
    double loss = 0.0;
    double precision = 0.0;
    double recall = 0.0;

    int tp = 0;
    int fp = 0;
    int tn = 0;
    int fn = 0;
};

class QuantumState {
private:
    array<double, 4> amplitudes{1.0, 0.0, 0.0, 0.0};

public:
    void reset() {
        amplitudes = {1.0, 0.0, 0.0, 0.0};
    }

    void applyRY(int qubit, double theta) {
        if (qubit < 0 || qubit > 1 || !isfinite(theta)) {
            throw invalid_argument("Invalid RY operation.");
        }

        const double c = cos(theta / 2.0);
        const double s = sin(theta / 2.0);
        const int mask = 1 << qubit;

        auto next = amplitudes;

        for (int i = 0; i < 4; ++i) {
            if (i & mask) continue;

            const int j = i | mask;
            const double a = amplitudes[i];
            const double b = amplitudes[j];

            next[i] = c * a - s * b;
            next[j] = s * a + c * b;
        }

        amplitudes = next;
    }

    void applyCNOT(int control, int target) {
        if (
            control < 0 || control > 1 ||
            target < 0 || target > 1 ||
            control == target
        ) {
            throw invalid_argument("Invalid CNOT configuration.");
        }

        array<double, 4> next{};

        for (int i = 0; i < 4; ++i) {
            int destination = i;

            if (i & (1 << control)) {
                destination ^= (1 << target);
            }

            next[destination] = amplitudes[i];
        }

        amplitudes = next;
    }

    double expectationZ0() const {
        double result = 0.0;

        for (int i = 0; i < 4; ++i) {
            const double sign = (i & 1) ? -1.0 : 1.0;
            result += sign * amplitudes[i] * amplitudes[i];
        }

        return result;
    }

    void validate() const {
        const double norm = inner_product(
            amplitudes.begin(),
            amplitudes.end(),
            amplitudes.begin(),
            0.0
        );

        if (abs(norm - 1.0) > 1e-8) {
            throw runtime_error("Quantum state normalization failure.");
        }
    }
};

class VariationalCircuit {
public:
    static double evaluate(
        const array<double, 2>& features,
        const array<double, 4>& parameters
    ) {
        QuantumState state;

        // Classical-to-quantum feature encoding.
        state.applyRY(0, features[0]);
        state.applyRY(1, features[1]);

        // Entangling operation.
        state.applyCNOT(0, 1);

        // Trainable ansatz.
        state.applyRY(0, parameters[0]);
        state.applyRY(1, parameters[1]);

        state.applyCNOT(0, 1);

        state.applyRY(0, parameters[2]);
        state.applyRY(1, parameters[3]);

        state.validate();

        return state.expectationZ0();
    }
};

class Dataset {
private:
    vector<Sample> samples;

public:
    explicit Dataset(vector<Sample> input)
        : samples(move(input)) {

        if (samples.size() < 2) {
            throw invalid_argument("Dataset is too small.");
        }

        bool negative = false;
        bool positive = false;

        for (const auto& sample : samples) {
            sample.validate();

            if (sample.label == Label::Negative) negative = true;
            else positive = true;
        }

        if (!negative || !positive) {
            throw invalid_argument("Both classes are required.");
        }
    }

    const vector<Sample>& getSamples() const {
        return samples;
    }

    size_t size() const {
        return samples.size();
    }
};

class VQCClassifier {
private:
    array<double, 4> parameters{};
    vector<double> history;

    double expectation(
        const array<double, 2>& features
    ) const {
        return VariationalCircuit::evaluate(features, parameters);
    }

    static double probabilityFromExpectation(double expectation) {
        return clamp(
            (1.0 - expectation) / 2.0,
            EPSILON,
            1.0 - EPSILON
        );
    }

public:
    explicit VQCClassifier(unsigned seed = 42) {
        mt19937 generator(seed);
        uniform_real_distribution<double> distribution(-0.5, 0.5);

        for (double& parameter : parameters) {
            parameter = distribution(generator);
        }
    }

    double predictProbability(
        const array<double, 2>& features
    ) const {
        return probabilityFromExpectation(expectation(features));
    }

    int predict(const array<double, 2>& features) const {
        return predictProbability(features) >= 0.5 ? 1 : 0;
    }

    static double crossEntropy(double p, int target) {
        p = clamp(p, EPSILON, 1.0 - EPSILON);

        return -(
            target * log(p) +
            (1 - target) * log(1.0 - p)
        );
    }

    array<double, 4> parameterShiftGradient(
        const Sample& sample
    ) const {
        const double p = predictProbability(sample.features);

        const double lossDerivative =
            (p - sample.target()) / (p * (1.0 - p));

        array<double, 4> gradient{};

        for (int i = 0; i < 4; ++i) {
            auto plus = parameters;
            auto minus = parameters;

            plus[i] += PI / 2.0;
            minus[i] -= PI / 2.0;

            const double expPlus =
                VariationalCircuit::evaluate(sample.features, plus);

            const double expMinus =
                VariationalCircuit::evaluate(sample.features, minus);

            const double expectationDerivative =
                (expPlus - expMinus) / 2.0;

            const double probabilityDerivative =
                -expectationDerivative / 2.0;

            gradient[i] = lossDerivative * probabilityDerivative;
        }

        return gradient;
    }

    void train(
        const Dataset& dataset,
        int epochs,
        double learningRate
    ) {
        if (epochs <= 0 || learningRate <= 0 || learningRate > 1) {
            throw invalid_argument("Invalid optimization configuration.");
        }

        const auto& samples = dataset.getSamples();

        for (int epoch = 0; epoch < epochs; ++epoch) {
            array<double, 4> accumulated{};
            double totalLoss = 0.0;

            for (const auto& sample : samples) {
                totalLoss += crossEntropy(
                    predictProbability(sample.features),
                    sample.target()
                );

                const auto gradient = parameterShiftGradient(sample);

                for (int i = 0; i < 4; ++i) {
                    accumulated[i] += gradient[i];
                }
            }

            const double averageLoss =
                totalLoss / static_cast<double>(samples.size());

            if (!isfinite(averageLoss)) {
                throw runtime_error("Non-finite training loss.");
            }

            auto updated = parameters;

            for (int i = 0; i < 4; ++i) {
                updated[i] = clamp(
                    parameters[i] -
                    learningRate * accumulated[i] / samples.size(),
                    -4.0 * PI,
                    4.0 * PI
                );
            }

            parameters = updated;
            history.push_back(averageLoss);

            if (epoch % 20 == 0) {
                cout << "Epoch " << setw(3) << epoch
                     << " | Loss: " << fixed << setprecision(6)
                     << averageLoss << '\n';
            }
        }
    }

    Metrics evaluate(const Dataset& dataset) const {
        Metrics metrics;

        for (const auto& sample : dataset.getSamples()) {
            const double p = predictProbability(sample.features);
            const int prediction = p >= 0.5 ? 1 : 0;
            const int actual = sample.target();

            metrics.loss += crossEntropy(p, actual);

            if (prediction == 1 && actual == 1) metrics.tp++;
            else if (prediction == 1) metrics.fp++;
            else if (actual == 0) metrics.tn++;
            else metrics.fn++;
        }

        const double count = static_cast<double>(dataset.size());

        metrics.accuracy = (metrics.tp + metrics.tn) / count;
        metrics.loss /= count;

        metrics.precision =
            metrics.tp + metrics.fp
            ? static_cast<double>(metrics.tp) /
              (metrics.tp + metrics.fp)
            : 0.0;

        metrics.recall =
            metrics.tp + metrics.fn
            ? static_cast<double>(metrics.tp) /
              (metrics.tp + metrics.fn)
            : 0.0;

        return metrics;
    }

    void displayMetrics(const string& name, const Metrics& m) const {
        cout << "\n" << name << '\n'
             << "Accuracy:  " << m.accuracy << '\n'
             << "Loss:      " << m.loss << '\n'
             << "Precision: " << m.precision << '\n'
             << "Recall:    " << m.recall << '\n'
             << "TP: " << m.tp << " FP: " << m.fp
             << " TN: " << m.tn << " FN: " << m.fn << '\n';
    }

    const vector<double>& getHistory() const {
        return history;
    }

    const array<double, 4>& getParameters() const {
        return parameters;
    }
};

vector<Sample> createSamples() {
    return {
        {{{0.15, 0.20}}, Label::Negative},
        {{{0.35, 0.25}}, Label::Negative},
        {{{0.20, 0.55}}, Label::Negative},
        {{{0.55, 0.30}}, Label::Negative},
        {{{0.40, 0.65}}, Label::Negative},

        {{{2.10, 2.00}}, Label::Positive},
        {{{2.40, 1.80}}, Label::Positive},
        {{{1.90, 2.45}}, Label::Positive},
        {{{2.65, 2.30}}, Label::Positive},
        {{{2.20, 2.70}}, Label::Positive}
    };
}

} // namespace vqc

int main() {
    using namespace vqc;

    try {
        cout << "VARIATIONAL QUANTUM CLASSIFIER\n";
        cout << "==============================\n";

        const auto all = createSamples();

        vector<Sample> trainingSamples;
        trainingSamples.insert(
            trainingSamples.end(), all.begin(), all.begin() + 4
        );
        trainingSamples.insert(
            trainingSamples.end(), all.begin() + 5, all.begin() + 9
        );

        Dataset training(move(trainingSamples));

        Dataset testing({
            all[4],
            all[9]
        });

        VQCClassifier classifier(42);

        cout << "\nTraining...\n";
        classifier.train(training, 120, 0.08);

        classifier.displayMetrics(
            "Training evaluation",
            classifier.evaluate(training)
        );

        classifier.displayMetrics(
            "Testing evaluation",
            classifier.evaluate(testing)
        );

        cout << "\nIndividual predictions:\n";

        for (const auto& sample : testing.getSamples()) {
            cout << "Features: ("
                 << sample.features[0] << ", "
                 << sample.features[1] << ")"
                 << " | Actual: " << sample.target()
                 << " | Predicted: "
                 << classifier.predict(sample.features)
                 << " | Probability: "
                 << classifier.predictProbability(sample.features)
                 << '\n';
        }

        cout << "\nOptimized parameters:\n";

        for (double parameter : classifier.getParameters()) {
            cout << parameter << ' ';
        }

        cout << "\nTraining epochs: "
             << classifier.getHistory().size() << '\n';

        cout << "\nQuantum state and optimization checks passed.\n";

    } catch (const exception& error) {
        cerr << "Execution failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
