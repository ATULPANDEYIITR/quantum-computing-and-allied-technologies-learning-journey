#include <algorithm>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Quantum simulator case study: validating a small quantum experiment.
 *
 * The simulated experiment prepares GHZ states and evaluates whether
 * observed shot counts agree with ideal statevector predictions.
 *
 * Compile:
 *   g++ -std=c++17 -O2 quantum_governance_simulator.cpp -o quantum_simulator
 *
 * This dense statevector implementation is suitable for small circuits.
 */

using Complex = std::complex<double>;
using StateVector = std::vector<Complex>;
using Counts = std::map<std::string, std::uint64_t>;

constexpr double EPSILON = 1e-10;
constexpr std::size_t MAX_QUBITS = 24;

class SimulationError : public std::runtime_error {
public:
    explicit SimulationError(const std::string& message)
        : std::runtime_error(message) {}
};

struct Matrix2 {
    Complex a00;
    Complex a01;
    Complex a10;
    Complex a11;

    bool isUnitary(double tolerance = EPSILON) const {
        const Complex columns[2][2] = {
            {a00, a10},
            {a01, a11}
        };

        for (int i = 0; i < 2; ++i) {
            for (int j = 0; j < 2; ++j) {
                Complex inner = 0.0;
                for (int k = 0; k < 2; ++k) {
                    inner += std::conj(columns[k][i]) * columns[k][j];
                }
                const Complex expected = (i == j) ? Complex(1.0, 0.0)
                                                   : Complex(0.0, 0.0);
                if (std::abs(inner - expected) > tolerance) {
                    return false;
                }
            }
        }
        return true;
    }
};

const Matrix2 X_GATE{0.0, 1.0, 1.0, 0.0};

Matrix2 hadamardGate() {
    const double value = 1.0 / std::sqrt(2.0);
    return {value, value, value, -value};
}

Matrix2 phaseGate(double theta) {
    if (!std::isfinite(theta)) {
        throw SimulationError("Phase angle must be finite.");
    }
    return {1.0, 0.0, 0.0, Complex(std::cos(theta), std::sin(theta))};
}

void validateQubitCount(std::size_t qubits) {
    if (qubits == 0 || qubits > MAX_QUBITS) {
        throw SimulationError("Qubit count is outside the configured range.");
    }
}

void validateQubit(std::size_t qubit, std::size_t qubits) {
    if (qubit >= qubits) {
        throw SimulationError("Qubit index is out of range.");
    }
}

std::string bitString(std::size_t value, std::size_t width) {
    std::string result(width, '0');
    for (std::size_t bit = 0; bit < width; ++bit) {
        if ((value >> bit) & 1U) {
            result[width - bit - 1] = '1';
        }
    }
    return result;
}

struct Gate {
    std::string name;
    std::size_t target;
    Matrix2 matrix;
    bool controlled;
    std::size_t control;

    Gate(
        std::string gateName,
        std::size_t targetQubit,
        Matrix2 unitary,
        bool hasControl = false,
        std::size_t controlQubit = 0
    )
        : name(std::move(gateName)),
          target(targetQubit),
          matrix(unitary),
          controlled(hasControl),
          control(controlQubit) {
        if (!matrix.isUnitary()) {
            throw SimulationError("Gate matrix is not unitary.");
        }
    }
};

class QuantumCircuit {
private:
    std::size_t qubits_;
    std::vector<Gate> gates_;
    std::vector<std::size_t> measured_;

public:
    explicit QuantumCircuit(std::size_t qubits) : qubits_(qubits) {
        validateQubitCount(qubits);
        for (std::size_t q = 0; q < qubits; ++q) {
            measured_.push_back(q);
        }
    }

    std::size_t qubits() const {
        return qubits_;
    }

    const std::vector<Gate>& gates() const {
        return gates_;
    }

    const std::vector<std::size_t>& measuredQubits() const {
        return measured_;
    }

    QuantumCircuit& addGate(const Gate& gate) {
        validateQubit(gate.target, qubits_);
        if (gate.controlled) {
            validateQubit(gate.control, qubits_);
            if (gate.control == gate.target) {
                throw SimulationError("Control and target must differ.");
            }
        }
        gates_.push_back(gate);
        return *this;
    }

    QuantumCircuit& h(std::size_t target) {
        return addGate(Gate("H", target, hadamardGate()));
    }

    QuantumCircuit& x(std::size_t target) {
        return addGate(Gate("X", target, X_GATE));
    }

    QuantumCircuit& phase(std::size_t target, double theta) {
        return addGate(Gate("P", target, phaseGate(theta)));
    }

    QuantumCircuit& cx(std::size_t control, std::size_t target) {
        return addGate(Gate("CX", target, X_GATE, true, control));
    }

    QuantumCircuit& measure(std::vector<std::size_t> qubits) {
        if (qubits.empty()) {
            throw SimulationError("Measurement selection cannot be empty.");
        }

        std::vector<bool> seen(qubits_, false);
        for (std::size_t qubit : qubits) {
            validateQubit(qubit, qubits_);
            if (seen[qubit]) {
                throw SimulationError("Measurement qubits must be unique.");
            }
            seen[qubit] = true;
        }
        measured_ = std::move(qubits);
        return *this;
    }
};

StateVector applyGate(
    const StateVector& state,
    std::size_t qubits,
    const Gate& gate
) {
    validateQubit(gate.target, qubits);

    const std::size_t targetMask = std::size_t{1} << gate.target;
    const std::size_t controlMask = gate.controlled
        ? (std::size_t{1} << gate.control)
        : 0;

    StateVector result = state;

    for (std::size_t index = 0; index < state.size(); ++index) {
        if (index & targetMask) {
            continue;
        }

        const std::size_t partner = index | targetMask;
        if (controlMask && !(index & controlMask)) {
            continue;
        }

        const Complex a0 = state[index];
        const Complex a1 = state[partner];

        result[index] = gate.matrix.a00 * a0 + gate.matrix.a01 * a1;
        result[partner] = gate.matrix.a10 * a0 + gate.matrix.a11 * a1;
    }

    return result;
}

StateVector simulate(const QuantumCircuit& circuit) {
    const std::size_t dimension = std::size_t{1} << circuit.qubits();
    StateVector state(dimension, Complex(0.0, 0.0));
    state[0] = 1.0;

    for (const Gate& gate : circuit.gates()) {
        state = applyGate(state, circuit.qubits(), gate);
    }

    double norm = 0.0;
    for (const Complex amplitude : state) {
        norm += std::norm(amplitude);
    }

    if (std::abs(norm - 1.0) > 1e-8) {
        throw SimulationError("Statevector normalization invariant failed.");
    }

    return state;
}

std::vector<double> getMeasurementProbabilities(
    const StateVector& state,
    std::size_t qubits,
    const std::vector<std::size_t>& measured
) {
    if (state.size() != (std::size_t{1} << qubits)) {
        throw SimulationError("Statevector dimension mismatch.");
    }

    std::vector<double> probabilities(std::size_t{1} << measured.size(), 0.0);

    for (std::size_t basis = 0; basis < state.size(); ++basis) {
        std::size_t outcome = 0;

        for (std::size_t outputBit = 0; outputBit < measured.size(); ++outputBit) {
            if ((basis >> measured[outputBit]) & 1U) {
                outcome |= std::size_t{1} << outputBit;
            }
        }

        probabilities[outcome] += std::norm(state[basis]);
    }

    const double total = std::accumulate(
        probabilities.begin(), probabilities.end(), 0.0
    );

    if (!std::isfinite(total) || total <= 0.0) {
        throw SimulationError("Invalid measurement probability mass.");
    }

    for (double& probability : probabilities) {
        probability /= total;
    }

    return probabilities;
}

Counts runShots(
    const std::vector<double>& probabilities,
    std::size_t measuredWidth,
    std::uint64_t shots,
    std::uint64_t seed
) {
    if (shots == 0) {
        throw SimulationError("Shot count must be positive.");
    }

    std::mt19937_64 generator(seed);
    std::discrete_distribution<std::size_t> distribution(
        probabilities.begin(), probabilities.end()
    );

    Counts counts;
    for (std::uint64_t shot = 0; shot < shots; ++shot) {
        const std::size_t outcome = distribution(generator);
        ++counts[bitString(outcome, measuredWidth)];
    }

    return counts;
}

double totalVariationDistance(
    const std::map<std::string, double>& exact,
    const std::map<std::string, double>& observed
) {
    std::map<std::string, double> outcomes = exact;
    for (const auto& [key, value] : observed) {
        outcomes.emplace(key, 0.0);
    }

    double distance = 0.0;
    for (const auto& [key, unused] : outcomes) {
        const auto e = exact.find(key);
        const auto o = observed.find(key);

        const double p = e == exact.end() ? 0.0 : e->second;
        const double q = o == observed.end() ? 0.0 : o->second;
        distance += std::abs(p - q);
    }
    return distance / 2.0;
}

std::map<std::string, double> normalizedCounts(
    const Counts& counts,
    std::uint64_t shots
) {
    if (shots == 0) {
        throw SimulationError("Cannot normalize counts for zero shots.");
    }

    std::map<std::string, double> result;
    for (const auto& [outcome, count] : counts) {
        result[outcome] = static_cast<double>(count) /
                          static_cast<double>(shots);
    }
    return result;
}

QuantumCircuit makeGhzCircuit(std::size_t qubits) {
    QuantumCircuit circuit(qubits);
    circuit.h(0);
    for (std::size_t target = 1; target < qubits; ++target) {
        circuit.cx(0, target);
    }
    return circuit;
}

std::map<std::string, double> exactDistribution(
    const std::vector<double>& probabilities,
    std::size_t width
) {
    std::map<std::string, double> result;
    for (std::size_t index = 0; index < probabilities.size(); ++index) {
        result[bitString(index, width)] = probabilities[index];
    }
    return result;
}

void printDistribution(
    const std::map<std::string, double>& distribution,
    const std::string& label
) {
    std::cout << label << '\n';
    for (const auto& [outcome, probability] : distribution) {
        if (probability > 1e-12) {
            std::cout << "  " << outcome << " : "
                      << std::fixed << std::setprecision(6)
                      << probability << '\n';
        }
    }
}

void runGovernanceCaseStudy() {
    std::cout << "Quantum experiment: GHZ state validation\n";

    constexpr std::size_t qubits = 5;
    constexpr std::uint64_t shots = 20000;
    constexpr std::uint64_t seed = 20261012;

    const QuantumCircuit circuit = makeGhzCircuit(qubits);
    const StateVector state = simulate(circuit);
    const auto probabilities = getMeasurementProbabilities(
        state, qubits, circuit.measuredQubits()
    );

    const auto exact = exactDistribution(probabilities, qubits);
    const Counts counts = runShots(probabilities, qubits, shots, seed);
    const auto observed = normalizedCounts(counts, shots);

    printDistribution(exact, "\nIdeal statevector probabilities:");
    printDistribution(observed, "\nShot-based empirical probabilities:");

    const double distance = totalVariationDistance(exact, observed);
    std::cout << "\nTotal variation distance: "
              << std::fixed << std::setprecision(6) << distance << '\n';

    // GHZ measurement correlations permit only all-zero and all-one results.
    // A nonzero count elsewhere indicates a simulator or experiment issue.
    std::uint64_t invalidOutcomes = 0;
    for (const auto& [outcome, count] : counts) {
        if (outcome != std::string(qubits, '0') &&
            outcome != std::string(qubits, '1')) {
            invalidOutcomes += count;
        }
    }

    std::cout << "Invalid ideal-circuit outcomes: "
              << invalidOutcomes << '\n';

    if (invalidOutcomes != 0) {
        throw SimulationError("Ideal GHZ circuit produced forbidden outcomes.");
    }

    std::cout << "State norm squared: ";
    double norm = 0.0;
    for (const Complex amplitude : state) {
        norm += std::norm(amplitude);
    }
    std::cout << std::setprecision(12) << norm << '\n';
}

void runInterferenceCase() {
    std::cout << "\nPhase interference case\n";

    QuantumCircuit circuit(1);
    circuit.h(0).phase(0, std::acos(-1.0)).h(0);

    const StateVector state = simulate(circuit);
    const auto probabilities = getMeasurementProbabilities(
        state, 1, std::vector<std::size_t>{0}
    );

    std::cout << "|0>: " << probabilities[0] << '\n';
    std::cout << "|1>: " << probabilities[1] << '\n';
}

void demonstrateResourceBound() {
    std::cout << "\nDense statevector memory estimates\n";
    for (std::size_t qubits : {10U, 15U, 20U, 24U}) {
        const std::size_t amplitudes = std::size_t{1} << qubits;
        const long double bytes =
            static_cast<long double>(amplitudes) * sizeof(Complex);

        std::cout << qubits << " qubits: "
                  << amplitudes << " amplitudes, approximately "
                  << static_cast<double>(bytes / (1024.0L * 1024.0L))
                  << " MiB of raw amplitude storage\n";
    }
}

int main() {
    try {
        runGovernanceCaseStudy();
        runInterferenceCase();
        demonstrateResourceBound();

        std::cout << "\nValidation failure example\n";
        try {
            QuantumCircuit invalid(2);
            invalid.cx(1, 1);
        } catch (const SimulationError& error) {
            std::cout << "Rejected invalid gate: " << error.what() << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Simulation failed: " << error.what() << '\n';
        return 1;
    }
}
