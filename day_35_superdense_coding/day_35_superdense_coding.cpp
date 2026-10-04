/*
 * Superdense Coding: repository-independent quantum communication case study.
 *
 * Scenario:
 * A communication subsystem has already distributed an entangled Bell pair
 * between Alice and Bob. Alice needs to communicate one of four two-bit
 * messages by sending only her half of the pair.
 *
 * The program models the complete protocol with complex state vectors and
 * matrices. It also includes a Pauli-channel noise model and a merge-like
 * "delivery eligibility" decision: Bob only accepts a decoded message when
 * the quantum state and measurement pipeline produce a valid two-bit result.
 *
 * Compile:
 *   g++ -std=c++17 -O2 superdense_coding.cpp -o superdense_coding
 */

#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Complex = std::complex<double>;
using State = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double EPSILON = 1e-10;

Matrix identity2() {
    return {
        {1.0, 0.0},
        {0.0, 1.0}
    };
}

Matrix pauliX() {
    return {
        {0.0, 1.0},
        {1.0, 0.0}
    };
}

Matrix pauliZ() {
    return {
        {1.0, 0.0},
        {0.0, -1.0}
    };
}

Matrix hadamard() {
    const double s = 1.0 / std::sqrt(2.0);
    return {
        {s, s},
        {s, -s}
    };
}

Matrix cnot() {
    return {
        {1.0, 0.0, 0.0, 0.0},
        {0.0, 1.0, 0.0, 0.0},
        {0.0, 0.0, 0.0, 1.0},
        {0.0, 0.0, 1.0, 0.0}
    };
}

Matrix multiply(const Matrix& a, const Matrix& b) {
    if (a.empty() || b.empty() || a.front().size() != b.size()) {
        throw std::invalid_argument("Incompatible matrix dimensions.");
    }

    Matrix result(a.size(), std::vector<Complex>(b.front().size(), 0.0));

    for (std::size_t i = 0; i < a.size(); ++i) {
        for (std::size_t j = 0; j < b.front().size(); ++j) {
            for (std::size_t k = 0; k < b.size(); ++k) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }

    return result;
}

Matrix tensorProduct(const Matrix& a, const Matrix& b) {
    Matrix result(
        a.size() * b.size(),
        std::vector<Complex>(a.front().size() * b.front().size(), 0.0)
    );

    for (std::size_t i = 0; i < a.size(); ++i) {
        for (std::size_t j = 0; j < a.front().size(); ++j) {
            for (std::size_t k = 0; k < b.size(); ++k) {
                for (std::size_t l = 0; l < b.front().size(); ++l) {
                    result[i * b.size() + k][j * b.front().size() + l] =
                        a[i][j] * b[k][l];
                }
            }
        }
    }

    return result;
}

State matrixVectorMultiply(const Matrix& matrix, const State& state) {
    if (matrix.empty() || matrix.front().size() != state.size()) {
        throw std::invalid_argument("Matrix/vector dimensions do not match.");
    }

    State result(matrix.size(), Complex{0.0, 0.0});

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0; column < state.size(); ++column) {
            result[row] += matrix[row][column] * state[column];
        }
    }

    return result;
}

double norm(const State& state) {
    double squared = 0.0;

    for (const auto& amplitude : state) {
        squared += std::norm(amplitude);
    }

    return std::sqrt(squared);
}

State normalize(const State& state) {
    const double stateNorm = norm(state);

    if (stateNorm < EPSILON) {
        throw std::invalid_argument("Cannot normalize a zero quantum state.");
    }

    State result = state;

    for (auto& amplitude : result) {
        amplitude /= stateNorm;
    }

    return result;
}

State basisState(const std::string& bits) {
    if (bits.size() != 2 || bits.find_first_not_of("01") != std::string::npos) {
        throw std::invalid_argument("Basis state must contain two binary digits.");
    }

    State state(4, Complex{0.0, 0.0});
    state[std::stoi(bits, nullptr, 2)] = 1.0;
    return state;
}

State applySingleQubitGate(
    const State& state,
    const Matrix& gate,
    int qubit
) {
    const Matrix I = identity2();

    Matrix expanded;

    if (qubit == 0) {
        expanded = tensorProduct(gate, I);
    } else if (qubit == 1) {
        expanded = tensorProduct(I, gate);
    } else {
        throw std::invalid_argument("Qubit must be 0 or 1.");
    }

    return normalize(matrixVectorMultiply(expanded, state));
}

State createBellPair() {
    State state = basisState("00");

    state = applySingleQubitGate(state, hadamard(), 0);
    state = normalize(matrixVectorMultiply(cnot(), state));

    return state;
}

struct Encoding {
    Matrix gate;
    std::string name;
};

Encoding encodingFor(const std::string& message) {
    const Matrix X = pauliX();
    const Matrix Z = pauliZ();
    const Matrix I = identity2();

    if (message == "00") {
        return {I, "I"};
    }

    if (message == "01") {
        return {X, "X"};
    }

    if (message == "10") {
        return {Z, "Z"};
    }

    if (message == "11") {
        return {multiply(Z, X), "ZX"};
    }

    throw std::invalid_argument(
        "Superdense coding message must be 00, 01, 10, or 11."
    );
}

State encode(const State& sharedPair, const std::string& message) {
    const Encoding operation = encodingFor(message);
    return applySingleQubitGate(sharedPair, operation.gate, 0);
}

State decodeBellBasis(const State& encoded) {
    State result = normalize(matrixVectorMultiply(cnot(), encoded));
    result = applySingleQubitGate(result, hadamard(), 0);
    return result;
}

std::string measure(
    const State& state,
    std::mt19937_64& generator
) {
    const double stateNorm = norm(state);

    if (std::abs(stateNorm - 1.0) > 1e-9) {
        throw std::invalid_argument("Measurement requires a normalized state.");
    }

    std::array<double, 4> probabilities{};

    for (std::size_t i = 0; i < 4; ++i) {
        probabilities[i] = std::norm(state[i]);
    }

    std::uniform_real_distribution<double> distribution(0.0, 1.0);
    const double sample = distribution(generator);

    double cumulative = 0.0;

    for (std::size_t i = 0; i < probabilities.size(); ++i) {
        cumulative += probabilities[i];

        if (sample <= cumulative) {
            return std::string("0") + std::to_string(i).substr(0, 1);
        }
    }

    return "11";
}

State applyChannelNoise(
    const State& state,
    double probability,
    std::mt19937_64& generator
) {
    if (probability < 0.0 || probability > 1.0) {
        throw std::invalid_argument("Noise probability must be within [0, 1].");
    }

    std::uniform_real_distribution<double> randomUnit(0.0, 1.0);

    if (randomUnit(generator) >= probability) {
        return state;
    }

    std::uniform_int_distribution<int> errorSelector(0, 2);

    switch (errorSelector(generator)) {
        case 0:
            return applySingleQubitGate(state, pauliX(), 0);
        case 1:
            return applySingleQubitGate(state, pauliZ(), 0);
        default:
            // XZ differs from the conventional Y by only a global phase,
            // which does not affect computational measurement probabilities.
            return applySingleQubitGate(
                state,
                multiply(pauliX(), pauliZ()),
                0
            );
    }
}

std::string stateDescription(const State& state) {
    const std::array<std::string, 4> labels{
        "00", "01", "10", "11"
    };

    std::ostringstream output;

    bool first = true;

    for (std::size_t i = 0; i < state.size(); ++i) {
        if (std::abs(state[i]) > EPSILON) {
            if (!first) {
                output << " + ";
            }

            output << "(" << std::fixed << std::setprecision(4)
                   << state[i].real();

            if (state[i].imag() >= 0.0) {
                output << "+";
            }

            output << state[i].imag() << "i)|"
                   << labels[i] << ">";

            first = false;
        }
    }

    return first ? "0" : output.str();
}

struct Transmission {
    std::string sent;
    std::string operation;
    std::string received;
    bool successful;
};

Transmission runTransmission(
    const std::string& message,
    double channelNoise,
    std::mt19937_64& generator
) {
    const Encoding operation = encodingFor(message);

    State shared = createBellPair();
    State encoded = encode(shared, message);

    // The physical communication step is represented by noise applied to
    // Alice's transmitted half of the Bell pair.
    State transmitted = applyChannelNoise(
        encoded,
        channelNoise,
        generator
    );

    State decoded = decodeBellBasis(transmitted);
    std::string received = measure(decoded, generator);

    return {
        message,
        operation.name,
        received,
        received == message
    };
}

void printHeading(const std::string& title) {
    std::cout << "\n" << std::string(78, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(78, '=') << "\n";
}

void demonstrateProtocol() {
    printHeading("Bell-pair creation and deterministic decoding");

    for (const std::string& message : {"00", "01", "10", "11"}) {
        const Encoding operation = encodingFor(message);
        State shared = createBellPair();
        State encoded = encode(shared, message);
        State decoded = decodeBellBasis(encoded);

        std::cout << "\nMessage: " << message
                  << "\nAlice operation: " << operation.name
                  << "\nEncoded state: " << stateDescription(encoded)
                  << "\nDecoded state: " << stateDescription(decoded)
                  << "\nNorm after decoding: "
                  << std::fixed << std::setprecision(6)
                  << norm(decoded)
                  << "\n";
    }
}

void demonstrateNoisyChannel() {
    printHeading("Noisy-channel reliability study");

    std::mt19937_64 generator(20261005);

    for (double noise : {0.00, 0.05, 0.15, 0.30}) {
        constexpr int trials = 1000;
        int successes = 0;

        for (int trial = 0; trial < trials; ++trial) {
            const std::string message =
                std::array<std::string, 4>{"00", "01", "10", "11"}[
                    trial % 4
                ];

            Transmission transmission =
                runTransmission(message, noise, generator);

            if (transmission.successful) {
                ++successes;
            }
        }

        std::cout << "Noise " << std::fixed << std::setprecision(2)
                  << noise << ": accuracy "
                  << static_cast<double>(successes) / trials
                  << "\n";
    }
}

void demonstrateGovernanceOfQuantumResources() {
    printHeading("Protocol resource accounting");

    std::cout
        << "Precondition: Alice and Bob possess a shared Bell pair.\n"
        << "Classical payload: one of four messages.\n"
        << "Payload information: log2(4) = 2 classical bits.\n"
        << "Quantum communication phase: Alice transmits one qubit.\n"
        << "Bob performs a joint Bell-basis measurement after receiving it.\n"
        << "Security boundary: entanglement itself is not a classical channel.\n"
        << "Physical limitation: Alice still needs a channel to transmit her qubit.\n";
}

void demonstrateInvalidStates() {
    printHeading("Failure conditions");

    try {
        encodingFor("2");
    } catch (const std::exception& error) {
        std::cout << "Rejected invalid message: "
                  << error.what() << "\n";
    }

    try {
        normalize(State{0.0, 0.0});
    } catch (const std::exception& error) {
        std::cout << "Rejected zero state: "
                  << error.what() << "\n";
    }

    try {
        State invalid{1.0, 1.0, 0.0, 0.0};
        std::mt19937_64 generator(7);
        measure(invalid, generator);
    } catch (const std::exception& error) {
        std::cout << "Rejected unnormalized measurement state: "
                  << error.what() << "\n";
    }
}

int main() {
    try {
        demonstrateProtocol();
        demonstrateNoisyChannel();
        demonstrateGovernanceOfQuantumResources();
        demonstrateInvalidStates();

        printHeading("Case study completed");
        std::cout
            << "The model demonstrates how entanglement, local encoding, "
               "quantum transmission, Bell-basis decoding, and channel noise "
               "interact in superdense coding.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal protocol error: "
                  << error.what() << "\n";
        return 1;
    }
}
