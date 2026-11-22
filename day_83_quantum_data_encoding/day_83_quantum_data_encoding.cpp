#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Complex = std::complex<double>;
using StateVector = std::vector<Complex>;

enum class EncodingType {
    BASIS,
    ANGLE,
    AMPLITUDE
};

std::string encodingName(EncodingType type) {
    switch (type) {
        case EncodingType::BASIS: return "BASIS";
        case EncodingType::ANGLE: return "ANGLE";
        case EncodingType::AMPLITUDE: return "AMPLITUDE";
    }

    throw std::invalid_argument("Unknown encoding type.");
}

struct EncodingMetadata {
    std::vector<double> originalFeatures;
    std::vector<double> angles;
    std::size_t originalDimension = 0;
    std::size_t encodedDimension = 0;
};

class QuantumState {
private:
    EncodingType type_;
    unsigned int qubits_;
    StateVector amplitudes_;
    EncodingMetadata metadata_;

public:
    QuantumState(
        EncodingType type,
        unsigned int qubits,
        StateVector amplitudes,
        EncodingMetadata metadata
    )
        : type_(type),
          qubits_(qubits),
          amplitudes_(std::move(amplitudes)),
          metadata_(std::move(metadata)) {

        if (qubits_ >= 63) {
            throw std::invalid_argument("Qubit count is too large.");
        }

        const std::size_t expected = std::size_t{1} << qubits_;

        if (amplitudes_.size() != expected) {
            throw std::invalid_argument("Invalid state dimension.");
        }

        double norm = 0.0;

        for (const auto& amplitude : amplitudes_) {
            norm += std::norm(amplitude);
        }

        if (std::abs(norm - 1.0) > 1e-9) {
            throw std::invalid_argument("Quantum state is not normalized.");
        }
    }

    unsigned int qubits() const {
        return qubits_;
    }

    EncodingType type() const {
        return type_;
    }

    const StateVector& amplitudes() const {
        return amplitudes_;
    }

    const EncodingMetadata& metadata() const {
        return metadata_;
    }

    std::vector<double> probabilities() const {
        std::vector<double> result;
        result.reserve(amplitudes_.size());

        for (const auto& amplitude : amplitudes_) {
            result.push_back(std::norm(amplitude));
        }

        return result;
    }

    std::map<std::string, std::size_t> measure(
        std::size_t shots,
        unsigned int seed = 42
    ) const {

        if (shots == 0) {
            throw std::invalid_argument("Measurement shots must be positive.");
        }

        const auto probs = probabilities();

        std::mt19937 generator(seed);
        std::discrete_distribution<std::size_t> distribution(
            probs.begin(), probs.end()
        );

        std::map<std::string, std::size_t> counts;

        for (std::size_t i = 0; i < shots; ++i) {
            const std::size_t outcome = distribution(generator);

            std::string bitstring(qubits_, '0');

            for (unsigned int bit = 0; bit < qubits_; ++bit) {
                if ((outcome >> bit) & 1U) {
                    bitstring[qubits_ - bit - 1] = '1';
                }
            }

            ++counts[bitstring];
        }

        return counts;
    }
};

class QuantumEncoder {
private:
    static void validateFeatures(const std::vector<double>& values) {
        if (values.empty()) {
            throw std::invalid_argument("Feature vector cannot be empty.");
        }

        for (double value : values) {
            if (!std::isfinite(value)) {
                throw std::invalid_argument("Non-finite feature detected.");
            }
        }
    }

public:
    static unsigned int requiredQubits(std::size_t dimension) {
        if (dimension == 0) {
            throw std::invalid_argument("Dimension must be positive.");
        }

        unsigned int qubits = 0;
        std::size_t capacity = 1;

        while (capacity < dimension) {
            capacity <<= 1;
            ++qubits;
        }

        return qubits;
    }

    /*
     * Binary features directly select a computational basis state.
     *
     * The state contains exactly one non-zero amplitude.
     */
    static QuantumState basisEncode(const std::vector<int>& bits) {
        if (bits.empty()) {
            throw std::invalid_argument("Binary data cannot be empty.");
        }

        std::size_t index = 0;

        for (int bit : bits) {
            if (bit != 0 && bit != 1) {
                throw std::invalid_argument("Basis input must be binary.");
            }

            index = (index << 1) | static_cast<std::size_t>(bit);
        }

        const std::size_t dimension = std::size_t{1} << bits.size();

        StateVector amplitudes(dimension, Complex(0.0, 0.0));
        amplitudes[index] = Complex(1.0, 0.0);

        EncodingMetadata metadata;
        metadata.originalDimension = bits.size();
        metadata.encodedDimension = dimension;

        for (int bit : bits) {
            metadata.originalFeatures.push_back(static_cast<double>(bit));
        }

        return QuantumState(
            EncodingType::BASIS,
            static_cast<unsigned int>(bits.size()),
            std::move(amplitudes),
            std::move(metadata)
        );
    }

    /*
     * RY(theta) rotates each qubit around the Y axis.
     *
     * theta = pi * x for normalized input x in [0, 1].
     *
     * Tensor products construct the complete state vector.
     */
    static QuantumState angleEncode(
        const std::vector<double>& features
    ) {
        validateFeatures(features);

        StateVector state = {Complex(1.0, 0.0)};
        EncodingMetadata metadata;

        metadata.originalFeatures = features;
        metadata.originalDimension = features.size();

        for (double value : features) {
            if (value < 0.0 || value > 1.0) {
                throw std::invalid_argument(
                    "Angle feature must be within [0, 1]."
                );
            }

            const double theta = M_PI * value;

            metadata.angles.push_back(theta);

            const double zero = std::cos(theta / 2.0);
            const double one = std::sin(theta / 2.0);

            StateVector expanded;
            expanded.reserve(state.size() * 2);

            for (const auto& amplitude : state) {
                expanded.push_back(amplitude * zero);
                expanded.push_back(amplitude * one);
            }

            state = std::move(expanded);
        }

        metadata.encodedDimension = state.size();

        return QuantumState(
            EncodingType::ANGLE,
            static_cast<unsigned int>(features.size()),
            std::move(state),
            std::move(metadata)
        );
    }

    /*
     * Amplitude encoding normalizes the input vector and pads it
     * to the next power-of-two dimension.
     */
    static QuantumState amplitudeEncode(
        const std::vector<double>& features
    ) {
        validateFeatures(features);

        double squaredNorm = 0.0;

        for (double value : features) {
            squaredNorm += value * value;
        }

        const double norm = std::sqrt(squaredNorm);

        if (norm <= 1e-15) {
            throw std::invalid_argument(
                "Zero vector cannot be amplitude encoded."
            );
        }

        const unsigned int qubits = requiredQubits(features.size());
        const std::size_t dimension = std::size_t{1} << qubits;

        StateVector amplitudes(dimension, Complex(0.0, 0.0));

        for (std::size_t i = 0; i < features.size(); ++i) {
            amplitudes[i] = Complex(features[i] / norm, 0.0);
        }

        EncodingMetadata metadata;
        metadata.originalFeatures = features;
        metadata.originalDimension = features.size();
        metadata.encodedDimension = dimension;

        return QuantumState(
            EncodingType::AMPLITUDE,
            qubits,
            std::move(amplitudes),
            std::move(metadata)
        );
    }
};

class QuantumResourceManager {
private:
    unsigned int maximumQubits_;
    std::size_t maximumBytes_;

public:
    QuantumResourceManager(
        unsigned int maximumQubits,
        std::size_t maximumBytes
    )
        : maximumQubits_(maximumQubits),
          maximumBytes_(maximumBytes) {}

    void validate(const QuantumState& state) const {
        if (state.qubits() > maximumQubits_) {
            throw std::runtime_error("Qubit resource limit exceeded.");
        }

        // Each complex<double> occupies two double values.
        const std::size_t requiredBytes =
            state.amplitudes().size() * sizeof(Complex);

        if (requiredBytes > maximumBytes_) {
            throw std::runtime_error("Memory resource limit exceeded.");
        }
    }
};

void displayState(const std::string& title, const QuantumState& state) {
    std::cout << "\n" << title << "\n";
    std::cout << std::string(60, '-') << "\n";

    std::cout << "Method: " << encodingName(state.type()) << "\n";
    std::cout << "Qubits: " << state.qubits() << "\n";
    std::cout << "Dimension: " << state.amplitudes().size() << "\n";

    std::cout << std::fixed << std::setprecision(6);

    for (std::size_t i = 0; i < state.amplitudes().size(); ++i) {
        const auto amplitude = state.amplitudes()[i];

        if (std::abs(amplitude) > 1e-10) {
            std::string bits(state.qubits(), '0');

            for (unsigned int j = 0; j < state.qubits(); ++j) {
                if ((i >> j) & 1U) {
                    bits[state.qubits() - j - 1] = '1';
                }
            }

            std::cout << "|" << bits << "> : "
                      << amplitude.real() << " + "
                      << amplitude.imag() << "i\n";
        }
    }

    std::cout << "\nMeasurement probabilities:\n";

    const auto probabilities = state.probabilities();

    for (std::size_t i = 0; i < probabilities.size(); ++i) {
        if (probabilities[i] > 1e-10) {
            std::cout << i << " : " << probabilities[i] << "\n";
        }
    }

    std::cout << "\nSampled outcomes (1000 shots):\n";

    for (const auto& [bitstring, count] : state.measure(1000)) {
        std::cout << bitstring << " : " << count << "\n";
    }
}

void runValidationTests() {
    std::cout << "\nVALIDATION TESTS\n";
    std::cout << std::string(60, '-') << "\n";

    auto expectFailure = [](const std::string& name, auto operation) {
        try {
            operation();
            throw std::runtime_error("Expected validation failure: " + name);
        } catch (const std::invalid_argument& error) {
            std::cout << name << " rejected: " << error.what() << "\n";
        }
    };

    expectFailure("Invalid basis input", [] {
        QuantumEncoder::basisEncode({1, 0, 2});
    });

    expectFailure("Invalid angle input", [] {
        QuantumEncoder::angleEncode({0.2, 1.5});
    });

    expectFailure("Zero amplitude vector", [] {
        QuantumEncoder::amplitudeEncode({0, 0, 0});
    });

    expectFailure("Empty feature vector", [] {
        QuantumEncoder::angleEncode({});
    });

    if (QuantumEncoder::requiredQubits(3) != 2) {
        throw std::runtime_error("Qubit calculation failed.");
    }

    const auto state = QuantumEncoder::amplitudeEncode({3, 4});

    if (std::abs(state.probabilities()[0] - 0.36) > 1e-9 ||
        std::abs(state.probabilities()[1] - 0.64) > 1e-9) {
        throw std::runtime_error("Amplitude probability test failed.");
    }

    std::cout << "All validation tests passed.\n";
}

int main() {
    try {
        std::cout << "QUANTUM DATA ENCODING ENGINE\n";
        std::cout << std::string(60, '=') << "\n";

        QuantumResourceManager resourceManager(
            12,
            64 * 1024 * 1024
        );

        const auto basis = QuantumEncoder::basisEncode({1, 0, 1, 1});

        const auto angle = QuantumEncoder::angleEncode({
            0.2, 0.5, 0.8
        });

        const auto amplitude = QuantumEncoder::amplitudeEncode({
            3.0, 4.0, 0.0
        });

        resourceManager.validate(basis);
        resourceManager.validate(angle);
        resourceManager.validate(amplitude);

        displayState("1. BASIS ENCODING", basis);
        displayState("2. ANGLE ENCODING", angle);
        displayState("3. AMPLITUDE ENCODING", amplitude);

        std::cout << "\nRESOURCE COMPARISON\n";
        std::cout << std::string(60, '-') << "\n";

        const std::vector<std::pair<std::string, const QuantumState*>> states = {
            {"Basis", &basis},
            {"Angle", &angle},
            {"Amplitude", &amplitude}
        };

        for (const auto& [name, state] : states) {
            std::cout << name
                      << " | Qubits: " << state->qubits()
                      << " | Dimension: " << state->amplitudes().size()
                      << " | Memory: "
                      << state->amplitudes().size() * sizeof(Complex)
                      << " bytes\n";
        }

        runValidationTests();

        std::cout << "\nExecution completed successfully.\n";

    } catch (const std::exception& error) {
        std::cerr << "Execution failed: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
