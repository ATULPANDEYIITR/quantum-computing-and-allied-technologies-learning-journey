/*
 * Bernstein-Vazirani Algorithm
 *
 * Technical case study:
 * A quantum repository-integrated experiment service must determine an
 * unknown binary configuration encoded by an oracle. The program models
 * the oracle, compares classical and quantum query strategies, validates
 * circuit constraints, performs a state-vector simulation, and records
 * experiment results.
 *
 * C++17 compilation:
 *   g++ -std=c++17 -O2 bernstein_vazirani.cpp -o bernstein_vazirani
 */

#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

struct Complex {
    double real{};
    double imag{};

    Complex operator+(const Complex& other) const {
        return {real + other.real, imag + other.imag};
    }

    Complex operator*(double scalar) const {
        return {real * scalar, imag * scalar};
    }

    double probability() const {
        return real * real + imag * imag;
    }
};

class HiddenStringOracle {
private:
    std::string secret_;

    static void validateBits(const std::string& bits) {
        if (bits.empty()) {
            throw std::invalid_argument("Hidden string cannot be empty.");
        }

        for (char bit : bits) {
            if (bit != '0' && bit != '1') {
                throw std::invalid_argument(
                    "Hidden string must contain only binary digits."
                );
            }
        }
    }

public:
    explicit HiddenStringOracle(std::string secret)
        : secret_(std::move(secret)) {
        validateBits(secret_);
    }

    std::size_t width() const {
        return secret_.size();
    }

    int evaluate(const std::string& input) const {
        if (input.size() != secret_.size()) {
            throw std::invalid_argument(
                "Oracle input width does not match secret width."
            );
        }

        int parity = 0;

        for (std::size_t i = 0; i < secret_.size(); ++i) {
            parity ^= ((secret_[i] - '0') & (input[i] - '0'));
        }

        return parity;
    }

    const std::string& secret() const {
        return secret_;
    }
};

class GovernanceExperiment {
private:
    std::string experimentId_;
    std::string hiddenString_;
    std::size_t classicalQueries_{};
    std::size_t quantumQueries_{};

public:
    GovernanceExperiment(
        std::string experimentId,
        std::string hiddenString
    )
        : experimentId_(std::move(experimentId)),
          hiddenString_(std::move(hiddenString)) {}

    void recordClassical(std::size_t queries) {
        classicalQueries_ = queries;
    }

    void recordQuantum(std::size_t queries) {
        quantumQueries_ = queries;
    }

    void print() const {
        std::cout << "\nExperiment record\n";
        std::cout << "-----------------\n";
        std::cout << "ID: " << experimentId_ << '\n';
        std::cout << "Hidden configuration: " << hiddenString_ << '\n';
        std::cout << "Classical oracle calls: "
                  << classicalQueries_ << '\n';
        std::cout << "Quantum oracle calls: "
                  << quantumQueries_ << '\n';
    }
};

std::string toBinary(std::uint64_t value, std::size_t width) {
    std::string result(width, '0');

    for (std::size_t i = 0; i < width; ++i) {
        const std::size_t position = width - 1 - i;
        result[position] = ((value >> i) & 1U) ? '1' : '0';
    }

    return result;
}

std::string discoverClassically(const HiddenStringOracle& oracle) {
    std::string recovered;
    recovered.reserve(oracle.width());

    for (std::size_t position = 0; position < oracle.width(); ++position) {
        std::string unitVector(oracle.width(), '0');
        unitVector[position] = '1';

        const int response = oracle.evaluate(unitVector);
        recovered.push_back(static_cast<char>('0' + response));
    }

    return recovered;
}

std::size_t countSetBits(std::uint64_t value) {
    std::size_t count = 0;

    while (value != 0) {
        value &= value - 1;
        ++count;
    }

    return count;
}

std::vector<Complex> applyHadamardAll(
    const std::vector<Complex>& state,
    std::size_t qubits
) {
    const std::size_t size = std::size_t{1} << qubits;
    const double scale = 1.0 / std::sqrt(static_cast<double>(size));

    std::vector<Complex> result(size);

    for (std::size_t output = 0; output < size; ++output) {
        Complex amplitude{};

        for (std::size_t source = 0; source < size; ++source) {
            const bool negative =
                countSetBits(output & source) % 2 == 1;

            const double sign = negative ? -1.0 : 1.0;

            amplitude = amplitude + state[source] * sign;
        }

        result[output] = amplitude * scale;
    }

    return result;
}

std::vector<Complex> prepareInitialState(std::size_t inputQubits) {
    const std::size_t totalQubits = inputQubits + 1;
    const std::size_t size = std::size_t{1} << totalQubits;

    std::vector<Complex> state(size);
    state[1] = {1.0, 0.0};

    return applyHadamardAll(state, totalQubits);
}

std::vector<Complex> applyOracle(
    const std::vector<Complex>& state,
    const HiddenStringOracle& oracle
) {
    const std::size_t n = oracle.width();
    const std::size_t expectedSize = std::size_t{1} << (n + 1);

    if (state.size() != expectedSize) {
        throw std::invalid_argument("Invalid state-vector dimension.");
    }

    std::vector<Complex> result(expectedSize);

    for (std::size_t index = 0; index < state.size(); ++index) {
        if (state[index].probability() < 1e-18) {
            continue;
        }

        const std::size_t inputValue = index >> 1;
        const int outputBit = static_cast<int>(index & 1U);
        const std::string input = toBinary(inputValue, n);
        const int functionValue = oracle.evaluate(input);

        const std::size_t transformed =
            (inputValue << 1) |
            static_cast<std::size_t>(outputBit ^ functionValue);

        result[transformed] =
            result[transformed] + state[index];
    }

    return result;
}

std::vector<Complex> applyHadamardToInputRegister(
    const std::vector<Complex>& state,
    std::size_t inputQubits
) {
    const std::size_t inputSize = std::size_t{1} << inputQubits;
    const double scale =
        1.0 / std::sqrt(static_cast<double>(inputSize));

    std::vector<Complex> result(state.size());

    for (int outputBit = 0; outputBit <= 1; ++outputBit) {
        for (std::size_t outputInput = 0;
             outputInput < inputSize;
             ++outputInput) {

            Complex amplitude{};

            for (std::size_t sourceInput = 0;
                 sourceInput < inputSize;
                 ++sourceInput) {

                const bool negative =
                    countSetBits(outputInput & sourceInput) % 2 == 1;

                const double sign = negative ? -1.0 : 1.0;
                const std::size_t sourceIndex =
                    (sourceInput << 1) |
                    static_cast<std::size_t>(outputBit);

                amplitude =
                    amplitude + state[sourceIndex] * sign;
            }

            result[(outputInput << 1) |
                   static_cast<std::size_t>(outputBit)] =
                amplitude * scale;
        }
    }

    return result;
}

std::string measureInputRegister(
    const std::vector<Complex>& state,
    std::size_t inputQubits,
    std::mt19937_64& generator
) {
    const std::size_t inputSize = std::size_t{1} << inputQubits;
    std::vector<double> marginal(inputSize, 0.0);

    for (std::size_t index = 0; index < state.size(); ++index) {
        marginal[index >> 1] += state[index].probability();
    }

    std::uniform_real_distribution<double> distribution(0.0, 1.0);
    const double sample = distribution(generator);

    double cumulative = 0.0;

    for (std::size_t input = 0; input < inputSize; ++input) {
        cumulative += marginal[input];

        if (sample <= cumulative) {
            return toBinary(input, inputQubits);
        }
    }

    return toBinary(inputSize - 1, inputQubits);
}

void printOracleArchitecture(const std::string& hidden) {
    std::cout << "\nOracle architecture\n";
    std::cout << "-------------------\n";

    for (std::size_t i = 0; i < hidden.size(); ++i) {
        if (hidden[i] == '1') {
            std::cout
                << "CNOT(input[" << i << "], output)\n";
        }
    }

    if (hidden.find('1') == std::string::npos) {
        std::cout << "Identity oracle: no controlled operations.\n";
    }
}

void printFinalState(
    const std::vector<Complex>& state,
    std::size_t qubits
) {
    std::cout << "\nFinal state support\n";
    std::cout << "-------------------\n";

    std::cout << std::fixed << std::setprecision(6);

    for (std::size_t index = 0; index < state.size(); ++index) {
        if (state[index].probability() > 1e-10) {
            std::cout
                << "|" << toBinary(index, qubits) << "> "
                << "amplitude=("
                << state[index].real << ", "
                << state[index].imag << "), "
                << "probability="
                << state[index].probability()
                << '\n';
        }
    }
}

int main() {
    try {
        const std::string hidden = "101101";

        HiddenStringOracle oracle(hidden);

        std::cout << "Bernstein-Vazirani Algorithm\n";
        std::cout << "============================\n";
        std::cout << "Hidden string: "
                  << oracle.secret() << '\n';

        const std::string classical =
            discoverClassically(oracle);

        GovernanceExperiment experiment(
            "BV-REPOSITORY-GOVERNANCE-001",
            hidden
        );

        experiment.recordClassical(hidden.size());

        std::cout << "\nClassical baseline\n";
        std::cout << "------------------\n";
        std::cout << "Recovered: " << classical << '\n';
        std::cout << "Queries: " << hidden.size() << '\n';

        printOracleArchitecture(hidden);

        /*
         * The output qubit begins in |1>. Hadamard transforms it into
         * |-> = (|0> - |1>) / sqrt(2). The oracle then changes the
         * amplitude phase according to (-1)^(s·x), which is phase kickback.
         */
        std::vector<Complex> state =
            prepareInitialState(hidden.size());

        state = applyOracle(state, oracle);
        state = applyHadamardToInputRegister(
            state,
            hidden.size()
        );

        std::mt19937_64 generator(20261019);
        const std::string quantum =
            measureInputRegister(
                state,
                hidden.size(),
                generator
            );

        experiment.recordQuantum(1);

        std::cout << "\nQuantum result\n";
        std::cout << "--------------\n";
        std::cout << "Recovered: " << quantum << '\n';
        std::cout << "Queries: 1\n";
        std::cout << "Correct: "
                  << std::boolalpha
                  << (quantum == hidden)
                  << '\n';

        printFinalState(state, hidden.size() + 1);
        experiment.print();

        std::cout << "\nComplexity interpretation\n";
        std::cout << "--------------------------\n";
        std::cout
            << "Classical unit-vector strategy uses O(n) oracle queries.\n"
            << "The ideal Bernstein-Vazirani circuit uses one oracle query.\n"
            << "The quantum circuit still requires O(n) Hadamard gates and "
               "an oracle whose implementation depends on the hidden string.\n";

    } catch (const std::exception& error) {
        std::cerr << "Experiment failure: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
