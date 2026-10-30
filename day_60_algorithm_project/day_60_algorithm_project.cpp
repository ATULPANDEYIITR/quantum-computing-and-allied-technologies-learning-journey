#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <functional>
#include <iomanip>
#include <iostream>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace quantum {

constexpr int MAX_QUBITS = 20;
using Complex = std::complex<double>;

class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message)
        : std::runtime_error(message) {}
};

class StateVector {
public:
    explicit StateVector(int qubits, std::uint64_t initialBasis = 0)
        : qubits_(qubits) {
        if (qubits < 1 || qubits > MAX_QUBITS) {
            throw ValidationError("Qubit count is outside the supported range.");
        }

        dimension_ = std::uint64_t{1} << qubits;

        if (initialBasis >= dimension_) {
            throw ValidationError("Initial basis state is outside the register.");
        }

        amplitudes_.assign(static_cast<std::size_t>(dimension_), Complex{0.0, 0.0});
        amplitudes_[static_cast<std::size_t>(initialBasis)] = Complex{1.0, 0.0};
    }

    int qubits() const {
        return qubits_;
    }

    std::uint64_t dimension() const {
        return dimension_;
    }

    const std::vector<Complex>& amplitudes() const {
        return amplitudes_;
    }

    void hadamard(int qubit) {
        validateQubit(qubit);

        const std::uint64_t stride = std::uint64_t{1} << qubit;
        const double scale = 1.0 / std::sqrt(2.0);

        for (std::uint64_t block = 0; block < dimension_; block += stride * 2) {
            for (std::uint64_t offset = 0; offset < stride; ++offset) {
                const std::uint64_t left = block + offset;
                const std::uint64_t right = left + stride;

                const Complex a = amplitudes_[static_cast<std::size_t>(left)];
                const Complex b = amplitudes_[static_cast<std::size_t>(right)];

                amplitudes_[static_cast<std::size_t>(left)] = (a + b) * scale;
                amplitudes_[static_cast<std::size_t>(right)] = (a - b) * scale;
            }
        }
    }

    void phaseOracle(const std::function<bool(std::uint64_t)>& predicate) {
        if (!predicate) {
            throw ValidationError("A phase oracle predicate is required.");
        }

        for (std::uint64_t basis = 0; basis < dimension_; ++basis) {
            if (predicate(basis)) {
                amplitudes_[static_cast<std::size_t>(basis)] *= -1.0;
            }
        }
    }

    void diffuse() {
        // The mean-amplitude form is the reflection 2|s><s| - I.
        Complex mean{0.0, 0.0};

        for (const Complex& amplitude : amplitudes_) {
            mean += amplitude;
        }
        mean /= static_cast<double>(dimension_);

        for (Complex& amplitude : amplitudes_) {
            amplitude = 2.0 * mean - amplitude;
        }
    }

    std::vector<double> probabilities() const {
        std::vector<double> output;
        output.reserve(amplitudes_.size());

        for (const Complex& amplitude : amplitudes_) {
            output.push_back(std::norm(amplitude));
        }

        return output;
    }

    double probability(std::uint64_t basis) const {
        if (basis >= dimension_) {
            throw ValidationError("Basis index is outside the register.");
        }
        return std::norm(amplitudes_[static_cast<std::size_t>(basis)]);
    }

    std::uint64_t measure(std::mt19937_64& generator) const {
        const std::vector<double> weights = probabilities();
        std::discrete_distribution<std::uint64_t> distribution(
            weights.begin(), weights.end()
        );
        return distribution(generator);
    }

private:
    int qubits_;
    std::uint64_t dimension_;
    std::vector<Complex> amplitudes_;

    void validateQubit(int qubit) const {
        if (qubit < 0 || qubit >= qubits_) {
            throw ValidationError("Invalid qubit index.");
        }
    }
};

bool oddParity(std::uint64_t value) {
    bool parity = false;

    while (value != 0) {
        parity = !parity;
        value &= value - 1;
    }

    return parity;
}

std::uint64_t parseBinary(const std::string& bits) {
    if (bits.empty() || bits.size() > MAX_QUBITS) {
        throw ValidationError("Binary string length is invalid.");
    }

    std::uint64_t value = 0;
    for (char bit : bits) {
        if (bit != '0' && bit != '1') {
            throw ValidationError("Binary strings may contain only 0 and 1.");
        }
        value = (value << 1) | static_cast<std::uint64_t>(bit - '0');
    }

    return value;
}

std::string toBinary(std::uint64_t value, int width) {
    if (width < 1 || width > MAX_QUBITS ||
        value >= (std::uint64_t{1} << width)) {
        throw ValidationError("Cannot format the requested binary value.");
    }

    std::string output(static_cast<std::size_t>(width), '0');

    for (int position = width - 1; position >= 0; --position) {
        output[static_cast<std::size_t>(position)] =
            ((value >> (width - 1 - position)) & 1U) ? '1' : '0';
    }

    return output;
}

struct AlgorithmResult {
    std::string algorithm;
    std::string measurement;
    std::string interpretation;
    double successProbability;
    int iterations;
};

AlgorithmResult deutschJozsa(
    int qubits,
    const std::string& oracleType,
    std::uint64_t balancedMask,
    std::mt19937_64& generator
) {
    const std::uint64_t dimension = std::uint64_t{1} << qubits;

    if (oracleType != "constant-zero" &&
        oracleType != "constant-one" &&
        oracleType != "balanced-parity") {
        throw ValidationError("Unsupported Deutsch-Jozsa oracle.");
    }

    if (oracleType == "balanced-parity" &&
        (balancedMask == 0 || balancedMask >= dimension)) {
        throw ValidationError("Balanced parity mask must be nonzero and fit the register.");
    }

    StateVector state(qubits);

    for (int qubit = 0; qubit < qubits; ++qubit) {
        state.hadamard(qubit);
    }

    if (oracleType == "constant-one") {
        state.phaseOracle([](std::uint64_t) { return true; });
    } else if (oracleType == "balanced-parity") {
        state.phaseOracle([balancedMask](std::uint64_t basis) {
            return oddParity(basis & balancedMask);
        });
    }

    for (int qubit = 0; qubit < qubits; ++qubit) {
        state.hadamard(qubit);
    }

    const std::uint64_t measured = state.measure(generator);
    const std::string bits = toBinary(measured, qubits);

    return {
        "Deutsch-Jozsa",
        bits,
        measured == 0 ? "constant" : "balanced",
        1.0,
        0
    };
}

AlgorithmResult bernsteinVazirani(
    const std::string& secret,
    std::mt19937_64& generator
) {
    const int qubits = static_cast<int>(secret.size());
    const std::uint64_t secretValue = parseBinary(secret);

    StateVector state(qubits);

    for (int qubit = 0; qubit < qubits; ++qubit) {
        state.hadamard(qubit);
    }

    // The phase oracle applies (-1)^(x dot secret).
    state.phaseOracle([secretValue](std::uint64_t basis) {
        return oddParity(basis & secretValue);
    });

    for (int qubit = 0; qubit < qubits; ++qubit) {
        state.hadamard(qubit);
    }

    const std::uint64_t measured = state.measure(generator);
    const std::string recovered = toBinary(measured, qubits);

    return {
        "Bernstein-Vazirani",
        recovered,
        recovered == secret ? "secret recovered" : "measurement mismatch",
        recovered == secret ? 1.0 : 0.0,
        0
    };
}

int optimalGroverIterations(int qubits, std::size_t markedCount) {
    if (qubits < 1 || qubits > MAX_QUBITS) {
        throw ValidationError("Invalid Grover register size.");
    }

    const double dimension = static_cast<double>(std::uint64_t{1} << qubits);

    if (markedCount == 0 || static_cast<double>(markedCount) > dimension) {
        throw ValidationError("Grover search requires valid marked states.");
    }

    const double theta = std::asin(std::sqrt(
        static_cast<double>(markedCount) / dimension
    ));

    return std::max(
        0,
        static_cast<int>(std::floor(
            std::acos(-1.0) / (4.0 * theta) - 0.5
        ))
    );
}

AlgorithmResult groverSearch(
    int qubits,
    const std::vector<std::uint64_t>& markedStates,
    std::mt19937_64& generator
) {
    const std::uint64_t dimension = std::uint64_t{1} << qubits;

    if (markedStates.empty()) {
        throw ValidationError("Grover search requires at least one target.");
    }

    const std::set<std::uint64_t> marked(
        markedStates.begin(), markedStates.end()
    );

    if (marked.size() != markedStates.size()) {
        throw ValidationError("Marked states must not contain duplicates.");
    }

    for (std::uint64_t value : marked) {
        if (value >= dimension) {
            throw ValidationError("A marked state is outside the search space.");
        }
    }

    StateVector state(qubits);

    for (int qubit = 0; qubit < qubits; ++qubit) {
        state.hadamard(qubit);
    }

    const int iterations = optimalGroverIterations(qubits, marked.size());

    for (int iteration = 0; iteration < iterations; ++iteration) {
        state.phaseOracle([&marked](std::uint64_t basis) {
            return marked.count(basis) > 0;
        });
        state.diffuse();
    }

    double successProbability = 0.0;
    for (std::uint64_t value : marked) {
        successProbability += state.probability(value);
    }

    const std::uint64_t measured = state.measure(generator);
    const bool found = marked.count(measured) > 0;

    return {
        "Grover",
        toBinary(measured, qubits),
        found ? "marked state found" : "unmarked state measured",
        successProbability,
        iterations
    };
}

}  // namespace quantum

int main() {
    try {
        std::mt19937_64 generator(20261030);

        const auto dj = quantum::deutschJozsa(
            3, "balanced-parity", 1, generator
        );

        const auto bv = quantum::bernsteinVazirani("1011", generator);

        const auto grover = quantum::groverSearch(
            3, {5}, generator
        );

        if (dj.measurement == "000") {
            throw std::runtime_error("Balanced Deutsch-Jozsa test failed.");
        }

        if (bv.measurement != "1011") {
            throw std::runtime_error("Bernstein-Vazirani test failed.");
        }

        if (grover.successProbability <= 0.75) {
            throw std::runtime_error("Grover amplitude amplification test failed.");
        }

        std::cout << std::fixed << std::setprecision(6);

        for (const auto& result : {dj, bv, grover}) {
            std::cout
                << result.algorithm
                << "\n  measurement: " << result.measurement
                << "\n  interpretation: " << result.interpretation
                << "\n  success probability: " << result.successProbability
                << "\n  Grover iterations: " << result.iterations
                << "\n\n";
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Quantum experiment error: " << error.what() << '\n';
        return 1;
    }
}
