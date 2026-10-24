#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

class SearchConfigurationError : public invalid_argument {
public:
    explicit SearchConfigurationError(const string& message)
        : invalid_argument(message) {}
};

enum class SearchStatus {
    Ready,
    Completed
};

struct SearchResult {
    int qubits;
    int iterations;
    vector<int> markedStates;
    vector<double> probabilities;
    double successProbability;
    int mostProbableState;
    SearchStatus status;
};

class GroverEngine {
private:
    int qubits_;
    size_t stateCount_;
    vector<int> markedStates_;

    // This simulator limits the state vector to 2^20 amplitudes.
    // A dense state-vector representation scales exponentially with qubits.
    static constexpr int MAX_QUBITS = 20;

    static size_t computeStateCount(int qubits) {
        if (qubits < 1 || qubits > MAX_QUBITS) {
            throw SearchConfigurationError(
                "Qubit count must be between 1 and 20."
            );
        }
        return size_t{1} << qubits;
    }

public:
    GroverEngine(int qubits, vector<int> markedStates)
        : qubits_(qubits),
          stateCount_(computeStateCount(qubits)),
          markedStates_(move(markedStates)) {

        if (markedStates_.empty()) {
            throw SearchConfigurationError(
                "At least one marked state is required."
            );
        }

        sort(markedStates_.begin(), markedStates_.end());
        markedStates_.erase(
            unique(markedStates_.begin(), markedStates_.end()),
            markedStates_.end()
        );

        for (int state : markedStates_) {
            if (state < 0 || static_cast<size_t>(state) >= stateCount_) {
                throw SearchConfigurationError(
                    "Marked state is outside the search space."
                );
            }
        }
    }

    int optimalIterations() const {
        const double marked =
            static_cast<double>(markedStates_.size());

        if (marked == static_cast<double>(stateCount_)) {
            return 0;
        }

        const double theta = asin(sqrt(marked / stateCount_));
        return max(0, static_cast<int>(
            floor(M_PI / (4.0 * theta) - 0.5)
        ));
    }

    SearchResult run(int iterations = -1) const {
        if (iterations == -1) {
            iterations = optimalIterations();
        }
        if (iterations < 0) {
            throw SearchConfigurationError(
                "Iterations must be nonnegative."
            );
        }

        vector<double> amplitudes(
            stateCount_,
            1.0 / sqrt(static_cast<double>(stateCount_))
        );

        set<int> markedSet(
            markedStates_.begin(), markedStates_.end()
        );

        for (int step = 0; step < iterations; ++step) {
            // The phase oracle changes amplitudes, not probabilities directly.
            for (int state : markedStates_) {
                amplitudes[state] = -amplitudes[state];
            }

            double sum = 0.0;
            for (double amplitude : amplitudes) {
                sum += amplitude;
            }
            const double twiceMean =
                2.0 * sum / static_cast<double>(stateCount_);

            // The diffusion operator performs an inversion about the mean.
            for (double& amplitude : amplitudes) {
                amplitude = twiceMean - amplitude;
            }
        }

        vector<double> probabilities(stateCount_);
        double norm = 0.0;
        double successProbability = 0.0;
        int mostProbableState = 0;

        for (size_t state = 0; state < stateCount_; ++state) {
            probabilities[state] =
                amplitudes[state] * amplitudes[state];
            norm += probabilities[state];

            if (markedSet.count(static_cast<int>(state))) {
                successProbability += probabilities[state];
            }

            if (probabilities[state] >
                probabilities[mostProbableState]) {
                mostProbableState = static_cast<int>(state);
            }
        }

        if (abs(norm - 1.0) > 1e-10) {
            throw runtime_error("Quantum state normalization failed.");
        }

        return SearchResult{
            qubits_,
            iterations,
            markedStates_,
            move(probabilities),
            successProbability,
            mostProbableState,
            SearchStatus::Completed
        };
    }
};

string binaryState(int state, int qubits) {
    string result(qubits, '0');
    for (int bit = qubits - 1; bit >= 0; --bit) {
        if (state & (1 << (qubits - bit - 1))) {
            result[bit] = '1';
        }
    }
    return result;
}

int main() {
    try {
        const int qubits = 4;
        GroverEngine engine(qubits, {5});
        const SearchResult result = engine.run();

        cout << fixed << setprecision(6);
        cout << "Grover quantum search\n";
        cout << "Qubits: " << result.qubits << '\n';
        cout << "Search space: "
             << result.probabilities.size() << '\n';
        cout << "Marked states: ";
        for (int state : result.markedStates) {
            cout << state << ' ';
        }
        cout << "\nIterations: " << result.iterations << '\n';
        cout << "Success probability: "
             << result.successProbability << '\n';
        cout << "Most probable state: "
             << binaryState(result.mostProbableState, qubits)
             << '\n';

        cout << "\nProbability distribution:\n";
        for (size_t state = 0;
             state < result.probabilities.size(); ++state) {
            cout << binaryState(static_cast<int>(state), qubits)
                 << " -> " << result.probabilities[state] << '\n';
        }

        if (result.mostProbableState != 5 ||
            result.successProbability < 0.9) {
            throw runtime_error("Search validation failed.");
        }

        GroverEngine allMarked(2, {0, 1, 2, 3});
        const auto allMarkedResult = allMarked.run();
        if (allMarkedResult.iterations != 0 ||
            abs(allMarkedResult.successProbability - 1.0) > 1e-10) {
            throw runtime_error("All-marked edge case failed.");
        }

        cout << "\nValidation checks passed.\n";
        return 0;
    } catch (const exception& error) {
        cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
