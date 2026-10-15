#include <algorithm>
#include <cmath>
#include <complex>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository-grade quantum circuit execution case study.
 *
 * Scenario: a small research team validates a multi-qubit circuit before
 * submitting it to a backend. The program checks gate validity, records
 * circuit operations, simulates entanglement, estimates measurement
 * statistics, and rejects circuits that exceed resource constraints.
 *
 * Build:
 *   g++ -std=c++17 -O2 quantum_circuit.cpp -o quantum_circuit
 */

using Complex = std::complex<double>;
using StateVector = std::vector<Complex>;
using Matrix2 = std::array<std::array<Complex, 2>, 2>;

constexpr double EPSILON = 1e-10;
constexpr std::size_t MAX_QUBITS = 20;

Matrix2 identityGate() {
    return {{{Complex(1, 0), Complex(0, 0)},
             {Complex(0, 0), Complex(1, 0)}}};
}

Matrix2 pauliX() {
    return {{{Complex(0, 0), Complex(1, 0)},
             {Complex(1, 0), Complex(0, 0)}}};
}

Matrix2 pauliZ() {
    return {{{Complex(1, 0), Complex(0, 0)},
             {Complex(0, 0), Complex(-1, 0)}}};
}

Matrix2 hadamard() {
    const double s = 1.0 / std::sqrt(2.0);
    return {{{Complex(s, 0), Complex(s, 0)},
             {Complex(s, 0), Complex(-s, 0)}}};
}

Matrix2 rotationY(double theta) {
    const double c = std::cos(theta / 2.0);
    const double s = std::sin(theta / 2.0);
    return {{{Complex(c, 0), Complex(-s, 0)},
             {Complex(s, 0), Complex(c, 0)}}};
}

bool isUnitary(const Matrix2& matrix) {
    for (std::size_t row = 0; row < 2; ++row) {
        for (std::size_t column = 0; column < 2; ++column) {
            Complex inner(0, 0);
            for (std::size_t k = 0; k < 2; ++k) {
                inner += std::conj(matrix[k][row]) * matrix[k][column];
            }
            const Complex expected(row == column ? 1.0 : 0.0, 0.0);
            if (std::abs(inner - expected) > EPSILON) {
                return false;
            }
        }
    }
    return true;
}

std::string bitString(std::size_t index, std::size_t qubits) {
    std::string result(qubits, '0');
    for (std::size_t q = 0; q < qubits; ++q) {
        const std::size_t mask = std::size_t{1} << (qubits - q - 1);
        result[q] = (index & mask) ? '1' : '0';
    }
    return result;
}

struct Operation {
    std::string name;
    std::size_t target;
    std::vector<std::size_t> controls;
};

class QuantumCircuit {
public:
    explicit QuantumCircuit(std::size_t qubits, std::uint32_t seed = 17)
        : qubits_(qubits),
          state_(dimensionFor(qubits), Complex(0, 0)),
          rng_(seed) {
        state_[0] = Complex(1, 0);
    }

    std::size_t qubitCount() const {
        return qubits_;
    }

    const StateVector& state() const {
        return state_;
    }

    const std::vector<Operation>& operations() const {
        return operations_;
    }

    void applyGate(
        const std::string& name,
        std::size_t target,
        const Matrix2& matrix,
        std::vector<std::size_t> controls = {}) {
        validateQubits(target, controls);

        if (!isUnitary(matrix)) {
            throw std::invalid_argument("Gate matrix must be unitary.");
        }

        StateVector next = state_;
        const std::size_t targetMask =
            std::size_t{1} << (qubits_ - target - 1);
        std::size_t controlMask = 0;

        for (std::size_t control : controls) {
            controlMask |= std::size_t{1} << (qubits_ - control - 1);
        }

        // Each target-zero basis index defines one unique amplitude pair.
        // A controlled gate skips pairs whose control bits are not all one.
        for (std::size_t index = 0; index < state_.size(); ++index) {
            if ((index & targetMask) != 0) {
                continue;
            }
            if ((index & controlMask) != controlMask) {
                continue;
            }

            const std::size_t partner = index | targetMask;
            const Complex a0 = state_[index];
            const Complex a1 = state_[partner];

            next[index] = matrix[0][0] * a0 + matrix[0][1] * a1;
            next[partner] = matrix[1][0] * a0 + matrix[1][1] * a1;
        }

        state_ = std::move(next);
        operations_.push_back(
            Operation{name, target, std::move(controls)}
        );
        validateNorm();
    }

    void h(std::size_t target) {
        applyGate("H", target, hadamard());
    }

    void x(std::size_t target) {
        applyGate("X", target, pauliX());
    }

    void z(std::size_t target) {
        applyGate("Z", target, pauliZ());
    }

    void ry(std::size_t target, double theta) {
        if (!std::isfinite(theta)) {
            throw std::invalid_argument("Rotation angle must be finite.");
        }
        applyGate("RY", target, rotationY(theta));
    }

    void cx(std::size_t control, std::size_t target) {
        applyGate("CX", target, pauliX(), {control});
    }

    void mcx(
        const std::vector<std::size_t>& controls,
        std::size_t target) {
        applyGate("MCX", target, pauliX(), controls);
    }

    std::unordered_map<std::string, double> probabilities() const {
        std::unordered_map<std::string, double> result;
        for (std::size_t index = 0; index < state_.size(); ++index) {
            const double probability = std::norm(state_[index]);
            if (probability > EPSILON) {
                result[bitString(index, qubits_)] = probability;
            }
        }
        return result;
    }

    std::unordered_map<std::string, std::size_t> sampleShots(
        std::size_t shots) {
        if (shots == 0 || shots > 1'000'000) {
            throw std::invalid_argument(
                "Shots must be between 1 and 1,000,000."
            );
        }

        std::vector<double> cumulative;
        cumulative.reserve(state_.size());
        double total = 0.0;

        for (const Complex& amplitude : state_) {
            total += std::norm(amplitude);
            cumulative.push_back(total);
        }

        if (std::abs(total - 1.0) > 1e-8) {
            throw std::runtime_error("State is not normalized.");
        }

        // Sampling does not collapse the stored circuit state; every shot
        // models a fresh preparation of the same circuit.
        std::uniform_real_distribution<double> distribution(0.0, 1.0);
        std::unordered_map<std::string, std::size_t> counts;

        for (std::size_t shot = 0; shot < shots; ++shot) {
            const double draw = distribution(rng_);
            auto it = std::lower_bound(
                cumulative.begin(), cumulative.end(), draw
            );
            std::size_t index = static_cast<std::size_t>(
                std::distance(cumulative.begin(), it)
            );
            if (index >= state_.size()) {
                index = state_.size() - 1;
            }
            ++counts[bitString(index, qubits_)];
        }

        return counts;
    }

    int measure(std::size_t target) {
        if (target >= qubits_) {
            throw std::out_of_range("Measurement target is invalid.");
        }

        const std::size_t mask =
            std::size_t{1} << (qubits_ - target - 1);
        double pOne = 0.0;

        for (std::size_t index = 0; index < state_.size(); ++index) {
            if (index & mask) {
                pOne += std::norm(state_[index]);
            }
        }

        std::bernoulli_distribution chooseOne(pOne);
        const int outcome = chooseOne(rng_);
        const double selectedProbability = outcome ? pOne : 1.0 - pOne;

        if (selectedProbability <= EPSILON) {
            throw std::runtime_error("Impossible measurement outcome.");
        }

        const double scaleFactor = 1.0 / std::sqrt(selectedProbability);
        for (std::size_t index = 0; index < state_.size(); ++index) {
            if (static_cast<bool>(index & mask) != static_cast<bool>(outcome)) {
                state_[index] = Complex(0, 0);
            } else {
                state_[index] *= scaleFactor;
            }
        }

        return outcome;
    }

    void printCircuit() const {
        std::cout << "Recorded circuit operations\n";
        for (std::size_t index = 0; index < operations_.size(); ++index) {
            const auto& operation = operations_[index];
            std::cout << "  " << operation.name
                      << " target=q" << operation.target;
            if (!operation.controls.empty()) {
                std::cout << " controls=";
                for (std::size_t control : operation.controls) {
                    std::cout << "q" << control << " ";
                }
            }
            std::cout << '\n';
        }
    }

private:
    static std::size_t dimensionFor(std::size_t qubits) {
        if (qubits == 0 || qubits > MAX_QUBITS) {
            throw std::invalid_argument(
                "Qubit count must be between 1 and 20."
            );
        }
        return std::size_t{1} << qubits;
    }

    void validateQubits(
        std::size_t target,
        const std::vector<std::size_t>& controls) const {
        if (target >= qubits_) {
            throw std::out_of_range("Target qubit is invalid.");
        }

        std::vector<std::size_t> sorted = controls;
        std::sort(sorted.begin(), sorted.end());

        if (std::adjacent_find(sorted.begin(), sorted.end()) != sorted.end()) {
            throw std::invalid_argument("Duplicate control qubits.");
        }

        for (std::size_t control : controls) {
            if (control >= qubits_ || control == target) {
                throw std::invalid_argument("Invalid control qubit.");
            }
        }
    }

    void validateNorm() const {
        const double norm = std::accumulate(
            state_.begin(), state_.end(), 0.0,
            [](double total, const Complex& amplitude) {
                return total + std::norm(amplitude);
            }
        );

        if (std::abs(norm - 1.0) > 1e-8) {
            throw std::runtime_error("Gate execution broke normalization.");
        }
    }

    std::size_t qubits_;
    StateVector state_;
    std::vector<Operation> operations_;
    std::mt19937 rng_;
};

void printDistribution(
    const std::unordered_map<std::string, double>& distribution) {
    std::vector<std::pair<std::string, double>> ordered(
        distribution.begin(), distribution.end()
    );
    std::sort(ordered.begin(), ordered.end());

    for (const auto& [bits, probability] : ordered) {
        std::cout << "  |" << bits << "> : "
                  << std::fixed << std::setprecision(4)
                  << probability << '\n';
    }
}

void printCounts(
    const std::unordered_map<std::string, std::size_t>& counts) {
    std::vector<std::pair<std::string, std::size_t>> ordered(
        counts.begin(), counts.end()
    );
    std::sort(ordered.begin(), ordered.end());

    for (const auto& [bits, count] : ordered) {
        std::cout << "  " << bits << " -> " << count << '\n';
    }
}

void validateBellCircuit() {
    QuantumCircuit circuit(2, 101);
    circuit.h(0);
    circuit.cx(0, 1);

    const auto probabilities = circuit.probabilities();
    if (std::abs(probabilities.at("00") - 0.5) > 1e-8 ||
        std::abs(probabilities.at("11") - 0.5) > 1e-8) {
        throw std::runtime_error("Bell-state validation failed.");
    }

    if (probabilities.count("01") || probabilities.count("10")) {
        throw std::runtime_error("Unexpected Bell-state basis amplitude.");
    }
}

int main() {
    try {
        validateBellCircuit();

        std::cout << "Quantum repository validation case study\n";
        std::cout << "\nBell-state circuit\n";

        QuantumCircuit bell(2, 2026);
        bell.h(0);
        bell.cx(0, 1);
        bell.printCircuit();

        std::cout << "\nExact state-vector distribution\n";
        printDistribution(bell.probabilities());

        std::cout << "\nMeasurement statistics from 4000 shots\n";
        printCounts(bell.sampleShots(4000));

        std::cout << "\nFour-qubit GHZ preparation\n";
        QuantumCircuit ghz(4, 77);
        ghz.h(0);
        ghz.cx(0, 1);
        ghz.cx(1, 2);
        ghz.cx(2, 3);
        printDistribution(ghz.probabilities());

        std::cout << "\nParameterized entangling circuit\n";
        QuantumCircuit parameterized(3, 88);
        parameterized.ry(0, std::acos(-1.0) / 3.0);
        parameterized.cx(0, 1);
        parameterized.cx(1, 2);
        printDistribution(parameterized.probabilities());

        std::cout << "\nValidation failure example\n";
        try {
            bell.cx(0, 0);
        } catch (const std::exception& error) {
            std::cout << "Rejected invalid gate: " << error.what() << '\n';
        }

        std::cout << "\nState-vector memory model\n";
        std::cout << "Qubits: " << ghz.qubitCount()
                  << ", amplitudes: " << ghz.state().size()
                  << ", approximate amplitude storage: "
                  << ghz.state().size() * sizeof(Complex)
                  << " bytes\n";

        std::cout << "\nAll circuit checks passed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Circuit execution failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
