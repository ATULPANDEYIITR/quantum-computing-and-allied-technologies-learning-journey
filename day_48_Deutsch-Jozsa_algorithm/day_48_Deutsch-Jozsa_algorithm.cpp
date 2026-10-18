#include <cmath>
#include <cstdint>
#include <functional>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Repository-independent quantum case study:
 * a state-vector engine evaluates Boolean oracles using the
 * Deutsch-Jozsa circuit.
 *
 * The case study uses a diagnostic controller that receives a Boolean
 * specification and determines whether it is constant or balanced.
 * The oracle promise is validated before the circuit is executed.
 */

using Oracle = std::function<int(std::uint64_t)>;

class QuantumError : public std::runtime_error {
public:
    explicit QuantumError(const std::string& message)
        : std::runtime_error(message) {}
};

struct ComplexAmplitude {
    double real = 0.0;
    double imag = 0.0;

    double probability() const {
        return real * real + imag * imag;
    }

    void negate() {
        real = -real;
        imag = -imag;
    }
};

enum class OracleClass {
    Constant,
    Balanced
};

std::string toString(OracleClass value) {
    return value == OracleClass::Constant ? "constant" : "balanced";
}

class BooleanOracle {
private:
    unsigned width_;
    std::vector<int> truthTable_;

public:
    BooleanOracle(unsigned width, const Oracle& function)
        : width_(width) {
        if (width == 0 || width > 20) {
            throw QuantumError(
                "Simulation width must be between 1 and 20 qubits."
            );
        }

        const std::size_t dimension = std::size_t{1} << width_;
        truthTable_.reserve(dimension);

        for (std::size_t x = 0; x < dimension; ++x) {
            const int output = function(x);

            if (output != 0 && output != 1) {
                throw QuantumError("Oracle output must be binary.");
            }

            truthTable_.push_back(output);
        }

        const auto ones = static_cast<std::size_t>(
            std::count(truthTable_.begin(), truthTable_.end(), 1)
        );

        if (ones != 0 &&
            ones != dimension &&
            ones * 2 != dimension) {
            throw QuantumError(
                "Oracle violates the constant-or-balanced promise."
            );
        }
    }

    unsigned width() const {
        return width_;
    }

    std::size_t dimension() const {
        return truthTable_.size();
    }

    int operator()(std::size_t x) const {
        return truthTable_.at(x);
    }

    OracleClass classification() const {
        const auto ones = static_cast<std::size_t>(
            std::count(truthTable_.begin(), truthTable_.end(), 1)
        );

        return ones == 0 || ones == truthTable_.size()
            ? OracleClass::Constant
            : OracleClass::Balanced;
    }

    const std::vector<int>& truthTable() const {
        return truthTable_;
    }
};

class QuantumRegister {
private:
    unsigned width_;
    std::vector<ComplexAmplitude> state_;

public:
    explicit QuantumRegister(unsigned width)
        : width_(width), state_(std::size_t{1} << width) {
        if (width == 0 || width > 20) {
            throw QuantumError("Unsupported register width.");
        }

        state_[0].real = 1.0;
    }

    void hadamardAll() {
        std::size_t stride = 1;

        while (stride < state_.size()) {
            for (std::size_t base = 0;
                 base < state_.size();
                 base += 2 * stride) {
                for (std::size_t offset = 0;
                     offset < stride;
                     ++offset) {
                    auto& left = state_[base + offset];
                    auto& right = state_[base + offset + stride];

                    const ComplexAmplitude oldLeft = left;
                    const ComplexAmplitude oldRight = right;

                    left.real = oldLeft.real + oldRight.real;
                    left.imag = oldLeft.imag + oldRight.imag;
                    right.real = oldLeft.real - oldRight.real;
                    right.imag = oldLeft.imag - oldRight.imag;
                }
            }

            stride *= 2;
        }

        const double scale = 1.0 / std::sqrt(
            static_cast<double>(state_.size())
        );

        for (auto& amplitude : state_) {
            amplitude.real *= scale;
            amplitude.imag *= scale;
        }
    }

    void applyPhaseOracle(const BooleanOracle& oracle) {
        if (oracle.width() != width_) {
            throw QuantumError("Oracle and register widths differ.");
        }

        for (std::size_t x = 0; x < state_.size(); ++x) {
            if (oracle(x) == 1) {
                state_[x].negate();
            }
        }
    }

    std::vector<double> probabilities() const {
        std::vector<double> result;
        result.reserve(state_.size());

        for (const auto& amplitude : state_) {
            result.push_back(amplitude.probability());
        }

        return result;
    }

    double zeroProbability() const {
        return state_.at(0).probability();
    }

    std::size_t mostLikelyOutcome() const {
        const auto probs = probabilities();
        return static_cast<std::size_t>(
            std::distance(
                probs.begin(),
                std::max_element(probs.begin(), probs.end())
            )
        );
    }
};

struct DiagnosticReport {
    OracleClass expectedClass;
    OracleClass inferredClass;
    double zeroProbability;
    std::size_t mostLikelyOutcome;
    std::size_t oracleQueries;
};

class DiagnosticController {
public:
    DiagnosticReport inspect(const BooleanOracle& oracle) const {
        QuantumRegister input(oracle.width());

        // The first Hadamard layer prepares a uniform superposition.
        input.hadamardAll();

        // The phase oracle marks inputs with f(x)=1 by a phase flip.
        input.applyPhaseOracle(oracle);

        // The final transform makes the constant/balanced distinction
        // observable in the all-zero input state.
        input.hadamardAll();

        const double pZero = input.zeroProbability();

        if (!std::isfinite(pZero) ||
            pZero < -1e-9 ||
            pZero > 1.0 + 1e-9) {
            throw QuantumError("Invalid measurement probability.");
        }

        const OracleClass inferred =
            std::abs(pZero - 1.0) < 1e-9
                ? OracleClass::Constant
                : OracleClass::Balanced;

        return {
            oracle.classification(),
            inferred,
            pZero,
            input.mostLikelyOutcome(),
            1
        };
    }
};

Oracle parityOracle(unsigned mask) {
    return [mask](std::uint64_t x) -> int {
        return __builtin_popcountll(x & mask) & 1;
    };
}

void printReport(
    const std::string& name,
    const BooleanOracle& oracle,
    const DiagnosticReport& report
) {
    std::cout << "\n" << name << '\n';
    std::cout << "Oracle class: " << toString(report.expectedClass) << '\n';
    std::cout << "Circuit class: " << toString(report.inferredClass) << '\n';
    std::cout << "P(|0...0>): "
              << std::fixed << std::setprecision(6)
              << report.zeroProbability << '\n';
    std::cout << "Oracle queries: " << report.oracleQueries << '\n';

    if (report.expectedClass != report.inferredClass) {
        throw QuantumError("Classification mismatch.");
    }

    if (report.expectedClass == OracleClass::Balanced &&
        report.zeroProbability > 1e-9) {
        throw QuantumError("Balanced oracle retained zero-state amplitude.");
    }
}

int main() {
    try {
        const DiagnosticController controller;

        const BooleanOracle constant(
            3,
            [](std::uint64_t) { return 1; }
        );

        const BooleanOracle balanced(
            3,
            parityOracle(0b111)
        );

        printReport(
            "Calibration oracle",
            constant,
            controller.inspect(constant)
        );

        printReport(
            "Parity diagnostic oracle",
            balanced,
            controller.inspect(balanced)
        );

        // The simulator refuses functions that violate the promise.
        try {
            const BooleanOracle invalid(
                3,
                [](std::uint64_t x) { return x == 0 ? 1 : 0; }
            );
            (void)invalid;
            throw QuantumError("Invalid oracle was not rejected.");
        } catch (const QuantumError& error) {
            std::cout << "\nInvalid specification rejected: "
                      << error.what() << '\n';
        }

        std::cout << "\nState-vector complexity: O(n * 2^n) time "
                     "for the transforms and O(2^n) memory.\n";
        std::cout << "The one-query claim concerns ideal oracle calls, "
                     "not total simulation time.\n";
    } catch (const std::exception& error) {
        std::cerr << "Simulation failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
