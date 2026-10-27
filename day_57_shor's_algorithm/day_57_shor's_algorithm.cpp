#include <algorithm>
#include <cmath>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using u64 = std::uint64_t;
using u128 = unsigned __int128;

struct FactorResult {
    u64 n{};
    std::vector<u64> factors;
    u64 base{};
    u64 period{};
    bool success{};
    std::string message;
};

u64 gcd_u64(u64 a, u64 b) {
    while (b != 0) {
        u64 remainder = a % b;
        a = b;
        b = remainder;
    }
    return a;
}

u64 modularMultiply(u64 a, u64 b, u64 modulus) {
    return static_cast<u64>((static_cast<u128>(a) * b) % modulus);
}

u64 modularPower(u64 base, u64 exponent, u64 modulus) {
    if (modulus == 0) {
        throw std::invalid_argument("Modulus cannot be zero.");
    }

    u64 result = 1 % modulus;
    base %= modulus;

    while (exponent > 0) {
        if (exponent & 1U) {
            result = modularMultiply(result, base, modulus);
        }

        base = modularMultiply(base, base, modulus);
        exponent >>= 1U;
    }

    return result;
}

bool isPrime(u64 n) {
    if (n < 2) {
        return false;
    }

    if (n % 2 == 0) {
        return n == 2;
    }

    for (u64 divisor = 3; divisor <= n / divisor; divisor += 2) {
        if (n % divisor == 0) {
            return false;
        }
    }

    return true;
}

std::vector<u64> trialFactorization(u64 n) {
    if (n < 2) {
        throw std::invalid_argument("n must be >= 2.");
    }

    std::vector<u64> factors;

    while (n % 2 == 0) {
        factors.push_back(2);
        n /= 2;
    }

    for (u64 divisor = 3; divisor <= n / divisor; divisor += 2) {
        while (n % divisor == 0) {
            factors.push_back(divisor);
            n /= divisor;
        }
    }

    if (n > 1) {
        factors.push_back(n);
    }

    return factors;
}

std::optional<u64> multiplicativeOrder(u64 a, u64 n) {
    if (n <= 1 || gcd_u64(a, n) != 1) {
        return std::nullopt;
    }

    u64 value = 1;

    for (u64 r = 1; r <= n; ++r) {
        value = modularMultiply(value, a, n);

        if (value == 1) {
            return r;
        }
    }

    return std::nullopt;
}

std::vector<std::pair<u64, u64>>
continuedFractionConvergents(u64 numerator, u64 denominator) {
    if (denominator == 0) {
        throw std::invalid_argument("Continued-fraction denominator is zero.");
    }

    std::vector<u64> quotients;

    while (denominator != 0) {
        const u64 quotient = numerator / denominator;
        const u64 remainder = numerator % denominator;
        quotients.push_back(quotient);
        numerator = denominator;
        denominator = remainder;
    }

    std::vector<std::pair<u64, u64>> result;

    u64 pMinus2 = 0;
    u64 pMinus1 = 1;
    u64 qMinus2 = 1;
    u64 qMinus1 = 0;

    for (u64 quotient : quotients) {
        const u64 p = quotient * pMinus1 + pMinus2;
        const u64 q = quotient * qMinus1 + qMinus2;

        result.emplace_back(p, q);

        pMinus2 = pMinus1;
        pMinus1 = p;
        qMinus2 = qMinus1;
        qMinus1 = q;
    }

    return result;
}

std::optional<u64> recoverPeriod(
    u64 measured,
    u64 registerSize,
    u64 a,
    u64 n
) {
    for (const auto& [numerator, denominator] :
         continuedFractionConvergents(measured, registerSize)) {
        static_cast<void>(numerator);

        if (denominator == 0 || denominator > n) {
            continue;
        }

        if (modularPower(a, denominator, n) == 1) {
            return denominator;
        }

        for (u64 multiplier = 2; multiplier <= n; ++multiplier) {
            if (denominator > (2 * n) / multiplier) {
                break;
            }

            const u64 candidate = denominator * multiplier;

            if (modularPower(a, candidate, n) == 1) {
                return candidate;
            }
        }
    }

    return std::nullopt;
}

std::optional<std::pair<u64, u64>>
deriveFactors(u64 n, u64 a, u64 period) {
    if (period == 0 || period % 2 != 0) {
        return std::nullopt;
    }

    const u64 halfPower = modularPower(a, period / 2, n);

    if (halfPower == n - 1) {
        return std::nullopt;
    }

    const u64 left = gcd_u64(halfPower - 1, n);
    const u64 right = gcd_u64(halfPower + 1, n);

    if (left > 1 && left < n &&
        right > 1 && right < n &&
        modularMultiply(left, right, n) == 0 &&
        left * right == n) {
        return std::make_pair(
            std::min(left, right),
            std::max(left, right)
        );
    }

    return std::nullopt;
}

/*
 * This engine deliberately separates:
 * - choosing a base,
 * - discovering the period,
 * - validating the period,
 * - extracting factors.
 *
 * A real quantum implementation would replace discoverPeriod() with
 * quantum phase estimation and QFT measurement.
 */
class ShorOrderEngine {
public:
    explicit ShorOrderEngine(std::uint64_t seed = 17)
        : rng_(seed) {}

    std::optional<u64> discoverPeriod(u64 a, u64 n) {
        return multiplicativeOrder(a, n);
    }

    u64 chooseBase(u64 n) {
        std::uniform_int_distribution<u64> distribution(2, n - 2);
        return distribution(rng_);
    }

private:
    std::mt19937_64 rng_;
};

FactorResult factorUsingShorStructure(
    u64 n,
    std::size_t attempts = 32
) {
    if (n < 2) {
        throw std::invalid_argument("n must be >= 2.");
    }

    if (isPrime(n)) {
        return {n, {n}, 0, 0, true, "Input is prime."};
    }

    if (n % 2 == 0) {
        return {
            n,
            {2, n / 2},
            0,
            0,
            true,
            "Even-number preprocessing found a factor."
        };
    }

    ShorOrderEngine engine(12345);

    for (std::size_t attempt = 0; attempt < attempts; ++attempt) {
        const u64 a = engine.chooseBase(n);
        const u64 commonFactor = gcd_u64(a, n);

        if (commonFactor > 1 && commonFactor < n) {
            return {
                n,
                {std::min(commonFactor, n / commonFactor),
                 std::max(commonFactor, n / commonFactor)},
                a,
                0,
                true,
                "Random base exposed a non-trivial gcd."
            };
        }

        if (commonFactor != 1) {
            continue;
        }

        const auto period = engine.discoverPeriod(a, n);

        if (!period || *period % 2 != 0) {
            continue;
        }

        if (modularPower(a, *period, n) != 1) {
            continue;
        }

        const auto factors = deriveFactors(n, a, *period);

        if (factors) {
            return {
                n,
                {factors->first, factors->second},
                a,
                *period,
                true,
                "Factors recovered from the even multiplicative order."
            };
        }
    }

    return {
        n,
        {},
        0,
        0,
        false,
        "No usable period was found within the attempt limit."
    };
}

void printFactors(const std::vector<u64>& factors) {
    if (factors.empty()) {
        std::cout << "none";
        return;
    }

    for (std::size_t i = 0; i < factors.size(); ++i) {
        if (i != 0) {
            std::cout << " x ";
        }
        std::cout << factors[i];
    }
}

void demonstrateOrder(u64 n, u64 a) {
    const auto order = multiplicativeOrder(a, n);

    if (!order) {
        std::cout
            << "a=" << a << ", n=" << n
            << ": a is not coprime to n.\n";
        return;
    }

    std::cout << "a=" << a << ", n=" << n << '\n';
    std::cout << "  sequence: ";

    for (u64 exponent = 0; exponent < *order; ++exponent) {
        std::cout << modularPower(a, exponent, n);
        if (exponent + 1 != *order) {
            std::cout << ", ";
        }
    }

    std::cout << '\n';
    std::cout << "  order r = " << *order << '\n';
    std::cout
        << "  a^r mod n = "
        << modularPower(a, *order, n)
        << '\n';

    if (*order % 2 == 0) {
        const auto factors = deriveFactors(n, a, *order);

        if (factors) {
            std::cout
                << "  factors = "
                << factors->first << " x "
                << factors->second << '\n';
        } else {
            std::cout << "  factor extraction requires another base.\n";
        }
    } else {
        std::cout << "  odd order: retry with another base.\n";
    }
}

int main() {
    try {
        std::cout
            << "Shor's Algorithm: Integer Factorization Case Study\n"
            << "=================================================\n\n";

        for (u64 n : {15, 21, 35, 77}) {
            const FactorResult result =
                factorUsingShorStructure(n, 40);

            std::cout
                << "n=" << result.n
                << ", success=" << std::boolalpha << result.success
                << ", factors=";
            printFactors(result.factors);

            std::cout
                << ", base=" << result.base
                << ", period=" << result.period
                << '\n'
                << "  " << result.message
                << "\n\n";
        }

        std::cout << "Order-finding examples\n";
        std::cout << "----------------------\n";
        demonstrateOrder(15, 2);
        demonstrateOrder(21, 2);

        std::cout << "\nClassical reference factorization\n";
        std::cout << "--------------------------------\n";

        for (u64 n : {15, 21, 35, 77, 84}) {
            const auto factors = trialFactorization(n);
            std::cout << n << " = ";
            printFactors(factors);
            std::cout << '\n';
        }

        // Mathematical invariants used as executable checks.
        if (gcd_u64(84, 30) != 6) {
            throw std::runtime_error("GCD validation failed.");
        }

        if (modularPower(7, 4, 15) != 1) {
            throw std::runtime_error("Modular exponentiation validation failed.");
        }

        if (!multiplicativeOrder(2, 15) ||
            *multiplicativeOrder(2, 15) != 4) {
            throw std::runtime_error("Order validation failed.");
        }

        const auto factors = deriveFactors(15, 2, 4);
        if (!factors || factors->first != 3 || factors->second != 5) {
            throw std::runtime_error("Factor extraction validation failed.");
        }

        std::cout << "\nValidation checks passed.\n";
    }
    catch (const std::exception& exception) {
        std::cerr
            << "Fatal error: "
            << exception.what()
            << '\n';
        return 1;
    }

    return 0;
}
