#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using Complex = std::complex<double>;

class QuantumCircuitError : public std::runtime_error {
public:
    explicit QuantumCircuitError(const std::string& message)
        : std::runtime_error(message) {}
};

void validatePowerOfTwo(std::size_t n, const std::string& name) {
    if (n == 0 || (n & (n - 1)) != 0) {
        throw QuantumCircuitError(name + " must be a positive power of two");
    }
}

std::vector<Complex> qft(const std::vector<Complex>& input) {
    const std::size_t n = input.size();
    validatePowerOfTwo(n, "state dimension");

    std::vector<Complex> output(n);
    const double normalization = 1.0 / std::sqrt(static_cast<double>(n));
    constexpr double pi = 3.14159265358979323846;

    for (std::size_t k = 0; k < n; ++k) {
        Complex total{0.0, 0.0};

        for (std::size_t x = 0; x < n; ++x) {
            const double angle =
                2.0 * pi * static_cast<double>(k * x) /
                static_cast<double>(n);

            total += input[x] * std::polar(1.0, angle);
        }

        output[k] = total * normalization;
    }

    return output;
}

std::vector<Complex> inverseQft(const std::vector<Complex>& input) {
    const std::size_t n = input.size();
    validatePowerOfTwo(n, "state dimension");

    std::vector<Complex> output(n);
    const double normalization = 1.0 / std::sqrt(static_cast<double>(n));
    constexpr double pi = 3.14159265358979323846;

    for (std::size_t x = 0; x < n; ++x) {
        Complex total{0.0, 0.0};

        for (std::size_t k = 0; k < n; ++k) {
            const double angle =
                -2.0 * pi * static_cast<double>(x * k) /
                static_cast<double>(n);

            total += input[k] * std::polar(1.0, angle);
        }

        output[x] = total * normalization;
    }

    return output;
}

enum class GateType {
    H,
    ControlledPhase,
    Swap,
    InverseControlledPhase
};

std::string gateName(GateType type) {
    switch (type) {
        case GateType::H:
            return "H";
        case GateType::ControlledPhase:
            return "CR";
        case GateType::Swap:
            return "SWAP";
        case GateType::InverseControlledPhase:
            return "CR†";
    }

    return "UNKNOWN";
}

struct Gate {
    GateType type;
    int first;
    int second;
    double angle;
};

class QuantumCircuit {
private:
    int qubits_;
    std::vector<Gate> gates_;

    void validateQubit(int qubit) const {
        if (qubit < 0 || qubit >= qubits_) {
            throw QuantumCircuitError("gate references invalid qubit");
        }
    }

public:
    explicit QuantumCircuit(int qubits)
        : qubits_(qubits) {
        if (qubits <= 0) {
            throw QuantumCircuitError("circuit must contain qubits");
        }
    }

    void addH(int qubit) {
        validateQubit(qubit);
        gates_.push_back({GateType::H, qubit, -1, 0.0});
    }

    void addControlledPhase(int control, int target, double angle) {
        validateQubit(control);
        validateQubit(target);

        if (control == target) {
            throw QuantumCircuitError("controlled phase needs two qubits");
        }

        gates_.push_back(
            {GateType::ControlledPhase, control, target, angle}
        );
    }

    void addSwap(int first, int second) {
        validateQubit(first);
        validateQubit(second);

        if (first == second) {
            throw QuantumCircuitError("SWAP requires distinct qubits");
        }

        gates_.push_back({GateType::Swap, first, second, 0.0});
    }

    void addQft(const std::vector<int>& qubits) {
        std::set<int> unique(qubits.begin(), qubits.end());

        if (qubits.empty() || unique.size() != qubits.size()) {
            throw QuantumCircuitError("QFT requires unique qubits");
        }

        for (std::size_t targetIndex = 0;
             targetIndex < qubits.size();
             ++targetIndex) {
            const int target = qubits[targetIndex];
            addH(target);

            for (std::size_t controlIndex = targetIndex + 1;
                 controlIndex < qubits.size();
                 ++controlIndex) {
                const int control = qubits[controlIndex];
                constexpr double pi = 3.14159265358979323846;

                const double angle =
                    pi / std::pow(
                        2.0,
                        static_cast<double>(
                            controlIndex - targetIndex
                        )
                    );

                addControlledPhase(control, target, angle);
            }
        }

        for (std::size_t i = 0; i < qubits.size() / 2; ++i) {
            addSwap(qubits[i], qubits[qubits.size() - 1 - i]);
        }
    }

    std::size_t gateCount() const {
        return gates_.size();
    }

    std::string describe() const {
        std::ostringstream output;

        output << "Circuit: " << qubits_
               << " qubits, " << gates_.size() << " gates\n";

        for (std::size_t i = 0; i < gates_.size(); ++i) {
            const auto& gate = gates_[i];

            output << std::setw(3) << i + 1
                   << ": " << gateName(gate.type)
                   << "(" << gate.first;

            if (gate.second >= 0) {
                output << "," << gate.second;
            }

            output << ")";

            if (gate.type == GateType::ControlledPhase) {
                output << " angle=" << std::setprecision(8)
                       << gate.angle;
            }

            output << "\n";
        }

        return output.str();
    }
};

std::uint64_t gcd64(std::uint64_t a, std::uint64_t b) {
    while (b != 0) {
        const std::uint64_t remainder = a % b;
        a = b;
        b = remainder;
    }

    return a;
}

std::uint64_t modularMultiply(
    std::uint64_t a,
    std::uint64_t b,
    std::uint64_t modulus
) {
    /*
     * This educational implementation uses unsigned __int128 for the
     * intermediate product, preventing overflow for 64-bit operands.
     */
    using Wide = unsigned __int128;
    return static_cast<std::uint64_t>(
        (static_cast<Wide>(a) * static_cast<Wide>(b)) % modulus
    );
}

std::uint64_t modularPower(
    std::uint64_t base,
    std::uint64_t exponent,
    std::uint64_t modulus
) {
    if (modulus <= 1) {
        throw QuantumCircuitError("modulus must exceed one");
    }

    std::uint64_t result = 1 % modulus;
    base %= modulus;

    while (exponent > 0) {
        if (exponent & 1ULL) {
            result = modularMultiply(result, base, modulus);
        }

        base = modularMultiply(base, base, modulus);
        exponent >>= 1ULL;
    }

    return result;
}

std::optional<std::uint64_t> modularOrder(
    std::uint64_t a,
    std::uint64_t n
) {
    if (!(1 < a && a < n) || gcd64(a, n) != 1) {
        throw QuantumCircuitError(
            "require 1 < a < n and gcd(a,n) = 1"
        );
    }

    std::uint64_t value = 1;

    for (std::uint64_t r = 1; r <= n; ++r) {
        value = modularMultiply(value, a, n);

        if (value == 1) {
            return r;
        }
    }

    return std::nullopt;
}

struct PhaseMeasurement {
    std::uint64_t measurement;
    double measuredPhase;
    double idealPhase;
};

std::vector<PhaseMeasurement> phaseEstimation(
    std::uint64_t period,
    unsigned countingQubits
) {
    if (period == 0 || countingQubits == 0 || countingQubits >= 63) {
        throw QuantumCircuitError("invalid phase-estimation parameters");
    }

    const std::uint64_t q = 1ULL << countingQubits;
    std::vector<PhaseMeasurement> result;

    for (std::uint64_t s = 0; s < period; ++s) {
        const double phase =
            static_cast<double>(s) / static_cast<double>(period);

        const auto measurement = static_cast<std::uint64_t>(
            std::llround(static_cast<double>(q) * phase)
        ) % q;

        result.push_back({
            measurement,
            static_cast<double>(measurement) /
                static_cast<double>(q),
            phase
        });
    }

    return result;
}

std::uint64_t nearestPeriodCandidate(
    const PhaseMeasurement& measurement,
    unsigned countingQubits,
    std::uint64_t maxDenominator
) {
    const std::uint64_t q = 1ULL << countingQubits;

    double bestError = std::numeric_limits<double>::infinity();
    std::uint64_t bestDenominator = 1;

    /*
     * Search rational denominators rather than relying on a floating-point
     * continued-fraction library. This keeps the case study deterministic.
     */
    for (std::uint64_t denominator = 1;
         denominator <= maxDenominator;
         ++denominator) {
        const double predicted =
            static_cast<double>(measurement.measurement) *
            static_cast<double>(denominator) /
            static_cast<double>(q);

        const auto numerator =
            static_cast<std::uint64_t>(std::llround(predicted));

        if (numerator == 0) {
            continue;
        }

        const double error =
            std::abs(
                static_cast<double>(measurement.measurement) /
                    static_cast<double>(q) -
                static_cast<double>(numerator) /
                    static_cast<double>(denominator)
            );

        if (error < bestError) {
            bestError = error;
            bestDenominator = denominator;
        }
    }

    return bestDenominator;
}

struct FactorizationResult {
    std::string status;
    std::uint64_t period = 0;
    std::set<std::uint64_t> factors;
    std::uint64_t measurement = 0;
    double phase = 0.0;
};

FactorizationResult runShorModel(
    std::uint64_t a,
    std::uint64_t n,
    unsigned countingQubits
) {
    if (n <= 1) {
        throw QuantumCircuitError("N must exceed one");
    }

    if (n % 2 == 0) {
        return {"trivial_factor", 0, {2}, 0, 0.0};
    }

    const auto commonFactor = gcd64(a, n);

    if (commonFactor > 1) {
        return {"trivial_factor", 0, {commonFactor}, 0, 0.0};
    }

    const auto order = modularOrder(a, n);

    if (!order.has_value()) {
        return {"period_not_found", 0, {}, 0, 0.0};
    }

    const auto measurements =
        phaseEstimation(*order, countingQubits);

    const auto measurement = std::find_if(
        measurements.begin(),
        measurements.end(),
        [](const PhaseMeasurement& item) {
            return item.measurement > 0;
        }
    );

    if (measurement == measurements.end()) {
        return {"zero_phase", *order, {}, 0, 0.0};
    }

    const auto candidate = nearestPeriodCandidate(
        *measurement,
        countingQubits,
        n
    );

    FactorizationResult result{
        "complete",
        *order,
        {},
        measurement->measurement,
        measurement->measuredPhase
    };

    if (candidate % 2 == 0) {
        const auto x =
            modularPower(a, candidate / 2, n);

        if (x != 1 && x != n - 1) {
            const auto left = gcd64(x - 1, n);
            const auto right = gcd64(x + 1, n);

            if (left > 1 && left < n) {
                result.factors.insert(left);
            }

            if (right > 1 && right < n) {
                result.factors.insert(right);
            }
        }
    }

    return result;
}

int main() {
    try {
        std::cout << "=== QFT state transformation ===\n";

        std::vector<Complex> state = {
            {0.5, 0.0},
            {0.5, 0.0},
            {0.0, 0.0},
            {0.0, 0.0}
        };

        const auto transformed = qft(state);
        const auto restored = inverseQft(transformed);

        double maxError = 0.0;

        for (std::size_t i = 0; i < transformed.size(); ++i) {
            const double probability =
                std::norm(transformed[i]);

            std::cout << "|" << std::bitset<2>(i) << "> "
                      << "amplitude=("
                      << std::fixed << std::setprecision(6)
                      << transformed[i].real() << ","
                      << transformed[i].imag() << ") "
                      << "probability=" << probability << "\n";

            maxError = std::max(
                maxError,
                std::abs(restored[i] - state[i])
            );
        }

        std::cout << "Inverse-QFT reconstruction error: "
                  << std::scientific << maxError << "\n";

        std::cout << "\n=== QFT circuit decomposition ===\n";

        QuantumCircuit circuit(4);
        circuit.addQft({0, 1, 2, 3});

        std::cout << circuit.describe();

        std::cout << "\n=== Shor period-finding engine ===\n";

        const auto result = runShorModel(2, 15, 8);

        std::cout << "status: " << result.status << "\n";
        std::cout << "period: " << result.period << "\n";
        std::cout << "measurement: " << result.measurement << "\n";
        std::cout << "phase: " << result.phase << "\n";

        std::cout << "factors:";
        for (const auto factor : result.factors) {
            std::cout << " " << factor;
        }
        std::cout << "\n";

        if (result.period != 4 ||
            result.factors != std::set<std::uint64_t>{3, 5}) {
            throw QuantumCircuitError(
                "unexpected period-finding result"
            );
        }

        std::cout << "\n=== Modular exponentiation trace ===\n";

        for (std::uint64_t exponent = 0; exponent <= 4; ++exponent) {
            std::cout << "2^" << exponent
                      << " mod 15 = "
                      << modularPower(2, exponent, 15)
                      << "\n";
        }

        std::cout << "\n=== Edge-case handling ===\n";

        try {
            qft({Complex{1.0}, Complex{2.0}, Complex{3.0}});
        } catch (const QuantumCircuitError& error) {
            std::cout << "Rejected invalid QFT dimension: "
                      << error.what() << "\n";
        }

        const auto earlyFactor = runShorModel(6, 15, 8);
        std::cout << "Early GCD factor: "
                  << *earlyFactor.factors.begin() << "\n";

        std::cout << "\nComplexity:\n";
        std::cout << "- Direct QFT simulation: O(N^2).\n";
        std::cout << "- QFT circuit decomposition: O(q^2) gates.\n";
        std::cout << "- Modular exponentiation: O(log exponent) multiplications.\n";
        std::cout << "- Real Shor implementations obtain the period from\n"
                  << "  quantum phase estimation instead of enumerating it.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Execution failed: "
                  << error.what() << "\n";
        return 1;
    }
}
