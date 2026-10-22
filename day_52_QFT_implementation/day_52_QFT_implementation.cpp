#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * QFT Implementation: Build QFT circuits.
 *
 * This program implements a repository-independent quantum circuit engine
 * specialized for the Quantum Fourier Transform.
 *
 * The implementation deliberately uses a gate-level representation instead
 * of constructing the complete 2^n x 2^n QFT matrix. This keeps gate
 * application at O(n * 2^n), while an explicit matrix would require
 * O(4^n) storage.
 *
 * Qubit 0 is the least-significant bit.
 */

using Complex = std::complex<double>;

constexpr double PI = 3.141592653589793238462643383279502884;
constexpr double EPSILON = 1e-10;

enum class GateType {
    Hadamard,
    ControlledPhase,
    Swap
};

struct Gate {
    GateType type;
    int target;
    int control = -1;
    int second = -1;
    double angle = 0.0;
};

class QuantumState {
public:
    explicit QuantumState(std::vector<Complex> amplitudes)
        : amplitudes_(std::move(amplitudes)) {
        validateAndNormalize();
    }

    static QuantumState basis(int qubits, std::size_t index) {
        if (qubits < 1) {
            throw std::invalid_argument(
                "A quantum state requires at least one qubit."
            );
        }

        const std::size_t dimension = std::size_t{1} << qubits;

        if (index >= dimension) {
            throw std::out_of_range("Basis index is outside the state space.");
        }

        std::vector<Complex> amplitudes(dimension, Complex{0.0, 0.0});
        amplitudes[index] = Complex{1.0, 0.0};

        return QuantumState(std::move(amplitudes));
    }

    std::size_t dimension() const {
        return amplitudes_.size();
    }

    int qubits() const {
        int count = 0;
        std::size_t value = amplitudes_.size();

        while (value > 1) {
            value >>= 1;
            ++count;
        }

        return count;
    }

    std::vector<Complex>& amplitudes() {
        return amplitudes_;
    }

    const std::vector<Complex>& amplitudes() const {
        return amplitudes_;
    }

private:
    std::vector<Complex> amplitudes_;

    void validateAndNormalize() {
        if (amplitudes_.empty()) {
            throw std::invalid_argument("Quantum state cannot be empty.");
        }

        if ((amplitudes_.size() & (amplitudes_.size() - 1)) != 0) {
            throw std::invalid_argument(
                "Quantum state dimension must be a power of two."
            );
        }

        double normSquared = 0.0;

        for (const Complex& amplitude : amplitudes_) {
            normSquared += std::norm(amplitude);
        }

        if (normSquared < EPSILON) {
            throw std::invalid_argument(
                "Quantum state cannot have zero norm."
            );
        }

        const double norm = std::sqrt(normSquared);

        for (Complex& amplitude : amplitudes_) {
            amplitude /= norm;
        }
    }
};

class QFTCircuit {
public:
    explicit QFTCircuit(int qubits)
        : qubits_(qubits) {
        if (qubits < 1 || qubits > 20) {
            throw std::invalid_argument(
                "Supported simulation range is 1 through 20 qubits."
            );
        }

        build();
    }

    const std::vector<Gate>& gates() const {
        return gates_;
    }

    QuantumState execute(const QuantumState& input) const {
        if (input.qubits() != qubits_) {
            throw std::invalid_argument(
                "Circuit and state qubit counts do not match."
            );
        }

        QuantumState result = input;

        for (const Gate& gate : gates_) {
            applyGate(result.amplitudes(), gate);
        }

        return result;
    }

    QuantumState executeInverse(const QuantumState& input) const {
        if (input.qubits() != qubits_) {
            throw std::invalid_argument(
                "Circuit and state qubit counts do not match."
            );
        }

        QuantumState result = input;

        for (auto it = gates_.rbegin(); it != gates_.rend(); ++it) {
            Gate inverse = *it;

            if (inverse.type == GateType::ControlledPhase) {
                inverse.angle = -inverse.angle;
            }

            applyGate(result.amplitudes(), inverse);
        }

        return result;
    }

    void print() const {
        std::cout << "QFT circuit (" << qubits_ << " qubits)\n";

        for (std::size_t i = 0; i < gates_.size(); ++i) {
            const Gate& gate = gates_[i];

            std::cout << std::setw(2) << i + 1 << ". ";

            if (gate.type == GateType::Hadamard) {
                std::cout << "H(q" << gate.target << ")";
            } else if (gate.type == GateType::ControlledPhase) {
                std::cout << "CR(q" << gate.control
                          << ", q" << gate.target
                          << ", angle=" << std::setprecision(8)
                          << gate.angle << ")";
            } else {
                std::cout << "SWAP(q" << gate.target
                          << ", q" << gate.second << ")";
            }

            std::cout << '\n';
        }
    }

private:
    int qubits_;
    std::vector<Gate> gates_;

    void build() {
        /*
         * The controlled rotations establish relative phases required by
         * the Fourier basis. Reversing qubit order at the end implements
         * the conventional QFT output ordering.
         */
        for (int target = 0; target < qubits_; ++target) {
            gates_.push_back({
                GateType::Hadamard,
                target
            });

            for (int control = target + 1;
                 control < qubits_;
                 ++control) {
                const int distance = control - target;
                const double angle = PI / std::pow(2.0, distance);

                gates_.push_back({
                    GateType::ControlledPhase,
                    target,
                    control,
                    -1,
                    angle
                });
            }
        }

        for (int left = 0; left < qubits_ / 2; ++left) {
            const int right = qubits_ - 1 - left;

            gates_.push_back({
                GateType::Swap,
                left,
                -1,
                right
            });
        }
    }

    static void applyHadamard(
        std::vector<Complex>& amplitudes,
        int target
    ) {
        const std::size_t mask = std::size_t{1} << target;
        const double scale = 1.0 / std::sqrt(2.0);

        for (std::size_t base = 0;
             base < amplitudes.size();
             base += 2 * mask) {

            for (std::size_t offset = 0;
                 offset < mask;
                 ++offset) {

                const std::size_t i = base + offset;
                const std::size_t j = i + mask;

                const Complex a = amplitudes[i];
                const Complex b = amplitudes[j];

                amplitudes[i] = (a + b) * scale;
                amplitudes[j] = (a - b) * scale;
            }
        }
    }

    static void applyControlledPhase(
        std::vector<Complex>& amplitudes,
        int control,
        int target,
        double angle
    ) {
        if (control == target) {
            throw std::invalid_argument(
                "Controlled-phase control and target must differ."
            );
        }

        const std::size_t controlMask = std::size_t{1} << control;
        const std::size_t targetMask = std::size_t{1} << target;
        const Complex phase = std::polar(1.0, angle);

        for (std::size_t index = 0;
             index < amplitudes.size();
             ++index) {

            if ((index & controlMask) && (index & targetMask)) {
                amplitudes[index] *= phase;
            }
        }
    }

    static void applySwap(
        std::vector<Complex>& amplitudes,
        int first,
        int second
    ) {
        if (first == second) {
            return;
        }

        const std::size_t firstMask = std::size_t{1} << first;
        const std::size_t secondMask = std::size_t{1} << second;

        for (std::size_t index = 0;
             index < amplitudes.size();
             ++index) {

            const bool firstSet = (index & firstMask) != 0;
            const bool secondSet = (index & secondMask) != 0;

            if (firstSet != secondSet) {
                const std::size_t swapped =
                    index ^ firstMask ^ secondMask;

                if (index < swapped) {
                    std::swap(
                        amplitudes[index],
                        amplitudes[swapped]
                    );
                }
            }
        }
    }

    static void applyGate(
        std::vector<Complex>& amplitudes,
        const Gate& gate
    ) {
        switch (gate.type) {
            case GateType::Hadamard:
                applyHadamard(amplitudes, gate.target);
                break;

            case GateType::ControlledPhase:
                applyControlledPhase(
                    amplitudes,
                    gate.control,
                    gate.target,
                    gate.angle
                );
                break;

            case GateType::Swap:
                applySwap(
                    amplitudes,
                    gate.target,
                    gate.second
                );
                break;
        }
    }
};

std::vector<Complex> directQFT(
    const std::vector<Complex>& input
) {
    const std::size_t dimension = input.size();

    if (dimension == 0 ||
        (dimension & (dimension - 1)) != 0) {
        throw std::invalid_argument(
            "Direct QFT requires a power-of-two dimension."
        );
    }

    std::vector<Complex> output(dimension, Complex{0.0, 0.0});
    const double scale = 1.0 / std::sqrt(
        static_cast<double>(dimension)
    );

    for (std::size_t k = 0; k < dimension; ++k) {
        for (std::size_t x = 0; x < dimension; ++x) {
            const double angle =
                2.0 * PI *
                static_cast<double>(x * k) /
                static_cast<double>(dimension);

            output[k] +=
                input[x] * std::polar(1.0, angle);
        }

        output[k] *= scale;
    }

    return output;
}

double maxDifference(
    const std::vector<Complex>& first,
    const std::vector<Complex>& second
) {
    if (first.size() != second.size()) {
        throw std::invalid_argument(
            "Compared states must have equal dimensions."
        );
    }

    double maximum = 0.0;

    for (std::size_t i = 0; i < first.size(); ++i) {
        maximum = std::max(
            maximum,
            std::abs(first[i] - second[i])
        );
    }

    return maximum;
}

void printState(const QuantumState& state) {
    std::cout << std::fixed << std::setprecision(6);

    for (std::size_t index = 0;
         index < state.dimension();
         ++index) {

        const Complex amplitude = state.amplitudes()[index];

        if (std::abs(amplitude) <= 1e-8) {
            continue;
        }

        std::cout << "|" << std::bitset<1>(0);

        std::string bits;
        for (int bit = state.qubits() - 1; bit >= 0; --bit) {
            bits += ((index >> bit) & 1) ? '1' : '0';
        }

        std::cout << bits << ">: "
                  << amplitude.real()
                  << (amplitude.imag() >= 0 ? "+" : "")
                  << amplitude.imag()
                  << "i, probability="
                  << std::norm(amplitude)
                  << '\n';
    }
}

void validateCircuit() {
    for (int qubits = 1; qubits <= 5; ++qubits) {
        QFTCircuit circuit(qubits);
        const std::size_t dimension = std::size_t{1} << qubits;

        for (std::size_t basis = 0;
             basis < dimension;
             ++basis) {

            QuantumState input =
                QuantumState::basis(qubits, basis);

            QuantumState transformed =
                circuit.execute(input);

            std::vector<Complex> reference =
                directQFT(input.amplitudes());

            const double qftError =
                maxDifference(
                    transformed.amplitudes(),
                    reference
                );

            if (qftError > 1e-9) {
                throw std::runtime_error(
                    "Gate decomposition failed direct-QFT validation."
                );
            }

            QuantumState recovered =
                circuit.executeInverse(transformed);

            const double inverseError =
                maxDifference(
                    recovered.amplitudes(),
                    input.amplitudes()
                );

            if (inverseError > 1e-9) {
                throw std::runtime_error(
                    "Inverse QFT validation failed."
                );
            }
        }
    }
}

int main() {
    try {
        validateCircuit();

        std::cout << "QFT validation passed for 1 through 5 qubits.\n\n";

        QFTCircuit circuit(3);
        circuit.print();

        QuantumState input =
            QuantumState::basis(3, 3);

        std::cout << "\nInput state:\n";
        printState(input);

        QuantumState transformed =
            circuit.execute(input);

        std::cout << "\nQFT state:\n";
        printState(transformed);

        std::vector<Complex> direct =
            directQFT(input.amplitudes());

        std::cout << "\nCircuit/direct error: "
                  << std::scientific
                  << maxDifference(
                         transformed.amplitudes(),
                         direct
                     )
                  << '\n';

        QuantumState recovered =
            circuit.executeInverse(transformed);

        std::cout << "Inverse-QFT recovery error: "
                  << maxDifference(
                         recovered.amplitudes(),
                         input.amplitudes()
                     )
                  << '\n';

        /*
         * State-vector simulation grows exponentially in qubit count.
         * Limiting the circuit size is an operational safeguard against
         * accidental memory exhaustion when this engine is exposed to
         * externally supplied circuit specifications.
         */
        std::cout << "\nSimulation memory model: O(2^n) amplitudes.\n";
        std::cout << "Gate application complexity: O(n * 2^n).\n";
        std::cout << "Direct Fourier reference complexity: O(4^n).\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "QFT execution failed: "
                  << error.what() << '\n';
        return 1;
    }
}
