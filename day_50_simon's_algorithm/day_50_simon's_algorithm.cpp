#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using BinaryVector = std::vector<int>;

class SimonOracle {
private:
    BinaryVector secret_;
    std::uint64_t secretValue_;

public:
    explicit SimonOracle(const std::string& secret)
        : secretValue_(0) {
        if (secret.empty()) {
            throw std::invalid_argument("secret cannot be empty");
        }

        bool nonZero = false;

        for (char bit : secret) {
            if (bit != '0' && bit != '1') {
                throw std::invalid_argument("secret must be binary");
            }

            secret_.push_back(bit - '0');
            secretValue_ = (secretValue_ << 1U) | static_cast<unsigned>(bit - '0');

            if (bit == '1') {
                nonZero = true;
            }
        }

        if (!nonZero) {
            throw std::invalid_argument("Simon secret must be non-zero");
        }
    }

    std::uint64_t evaluate(std::uint64_t x) const {
        const std::size_t n = secret_.size();

        if (n >= 63) {
            throw std::overflow_error(
                "demonstration oracle uses a bounded integer domain");
        }

        const std::uint64_t domainSize = 1ULL << n;

        if (x >= domainSize) {
            throw std::out_of_range("oracle input outside domain");
        }

        return std::min(x, x ^ secretValue_);
    }

    bool satisfiesPromise() const {
        const std::size_t n = secret_.size();

        if (n >= 63) {
            return false;
        }

        const std::uint64_t domainSize = 1ULL << n;
        std::unordered_map<std::uint64_t, std::size_t> frequencies;

        for (std::uint64_t x = 0; x < domainSize; ++x) {
            if (evaluate(x) != evaluate(x ^ secretValue_)) {
                return false;
            }

            ++frequencies[evaluate(x)];
        }

        return std::all_of(
            frequencies.begin(),
            frequencies.end(),
            [](const auto& entry) {
                return entry.second == 2;
            }
        );
    }

    const BinaryVector& secret() const {
        return secret_;
    }

    std::size_t width() const {
        return secret_.size();
    }
};

int dotMod2(const BinaryVector& a, const BinaryVector& b) {
    if (a.size() != b.size()) {
        throw std::invalid_argument("vector dimensions differ");
    }

    int result = 0;

    for (std::size_t i = 0; i < a.size(); ++i) {
        result ^= (a[i] & b[i]);
    }

    return result;
}

BinaryVector xorVectors(
    const BinaryVector& a,
    const BinaryVector& b
) {
    if (a.size() != b.size()) {
        throw std::invalid_argument("vector dimensions differ");
    }

    BinaryVector result(a.size());

    for (std::size_t i = 0; i < a.size(); ++i) {
        result[i] = a[i] ^ b[i];
    }

    return result;
}

std::size_t rankMod2(std::vector<BinaryVector> matrix) {
    if (matrix.empty()) {
        return 0;
    }

    const std::size_t columns = matrix.front().size();
    std::size_t rank = 0;

    for (std::size_t column = 0; column < columns; ++column) {
        std::size_t pivot = rank;

        while (
            pivot < matrix.size() &&
            matrix[pivot][column] == 0
        ) {
            ++pivot;
        }

        if (pivot == matrix.size()) {
            continue;
        }

        std::swap(matrix[rank], matrix[pivot]);

        for (std::size_t row = 0; row < matrix.size(); ++row) {
            if (row != rank && matrix[row][column]) {
                matrix[row] = xorVectors(matrix[row], matrix[rank]);
            }
        }

        ++rank;

        if (rank == matrix.size()) {
            break;
        }
    }

    return rank;
}

std::vector<BinaryVector> nullspaceMod2(
    std::vector<BinaryVector> matrix
) {
    if (matrix.empty()) {
        throw std::invalid_argument(
            "at least one equation is required for this solver");
    }

    const std::size_t n = matrix.front().size();
    std::vector<std::size_t> pivots;
    std::size_t rank = 0;

    for (std::size_t column = 0; column < n; ++column) {
        std::size_t pivot = rank;

        while (
            pivot < matrix.size() &&
            matrix[pivot][column] == 0
        ) {
            ++pivot;
        }

        if (pivot == matrix.size()) {
            continue;
        }

        std::swap(matrix[rank], matrix[pivot]);

        for (std::size_t row = 0; row < matrix.size(); ++row) {
            if (row != rank && matrix[row][column]) {
                matrix[row] = xorVectors(matrix[row], matrix[rank]);
            }
        }

        pivots.push_back(column);
        ++rank;
    }

    std::vector<bool> isPivot(n, false);

    for (std::size_t column : pivots) {
        isPivot[column] = true;
    }

    std::vector<BinaryVector> basis;

    for (std::size_t freeColumn = 0; freeColumn < n; ++freeColumn) {
        if (isPivot[freeColumn]) {
            continue;
        }

        BinaryVector vector(n, 0);
        vector[freeColumn] = 1;

        for (std::size_t row = 0; row < pivots.size(); ++row) {
            vector[pivots[row]] = matrix[row][freeColumn];
        }

        basis.push_back(vector);
    }

    return basis;
}

std::string toString(const BinaryVector& vector) {
    std::string result;
    result.reserve(vector.size());

    for (int bit : vector) {
        result.push_back(static_cast<char>('0' + bit));
    }

    return result;
}

BinaryVector measureAllowedVector(
    const BinaryVector& secret,
    std::mt19937_64& generator
) {
    std::uniform_int_distribution<int> bit(0, 1);
    BinaryVector measurement(secret.size());

    /*
     * Simon's circuit guarantees y·s = 0.
     * Rejection sampling reproduces the exact uniform distribution
     * over the allowed subspace without constructing amplitudes.
     */
    do {
        for (int& value : measurement) {
            value = bit(generator);
        }
    } while (dotMod2(measurement, secret) != 0);

    return measurement;
}

BinaryVector recoverSecret(
    const std::vector<BinaryVector>& observations
) {
    if (observations.empty()) {
        throw std::invalid_argument(
            "observations are required to recover a unique secret");
    }

    const std::size_t n = observations.front().size();
    auto basis = nullspaceMod2(observations);

    if (basis.size() != 1) {
        throw std::runtime_error(
            "observations do not uniquely determine the hidden period");
    }

    return basis.front();
}

class MergeEligibilityEngine {
public:
    static bool eligible(
        const std::vector<BinaryVector>& observations,
        std::size_t n
    ) {
        return !observations.empty() &&
               rankMod2(observations) == n - 1;
    }
};

int main() {
    try {
        const std::string secret = "110101";
        SimonOracle oracle(secret);

        if (!oracle.satisfiesPromise()) {
            throw std::runtime_error("oracle violates Simon's promise");
        }

        std::mt19937_64 generator(42);
        std::vector<BinaryVector> observations;

        /*
         * The hidden period is determined once n-1 independent
         * orthogonality equations have been collected.
         */
        while (!MergeEligibilityEngine::eligible(
            observations,
            oracle.width()
        )) {
            BinaryVector measurement =
                measureAllowedVector(oracle.secret(), generator);

            auto candidate = observations;
            candidate.push_back(measurement);

            if (rankMod2(candidate) > rankMod2(observations)) {
                observations.push_back(std::move(measurement));
            }
        }

        BinaryVector recovered = recoverSecret(observations);

        std::cout << "Simon hidden-period simulation\n";
        std::cout << "Hidden period:       " << secret << '\n';
        std::cout << "Independent samples: "
                  << observations.size() << '\n';

        std::cout << "Measured vectors:     ";
        for (std::size_t i = 0; i < observations.size(); ++i) {
            if (i > 0) {
                std::cout << ", ";
            }
            std::cout << toString(observations[i]);
        }
        std::cout << '\n';

        std::cout << "Recovered period:    "
                  << toString(recovered) << '\n';

        std::cout << "Recovery successful: "
                  << std::boolalpha
                  << (toString(recovered) == secret)
                  << '\n';

        /*
         * Complexity:
         * - Classical oracle verification is O(2^n).
         * - Gaussian elimination over m equations is O(m n^2).
         * - The real quantum circuit avoids explicitly enumerating 2^n
         *   states, which is the central algorithmic advantage.
         */
    } catch (const std::exception& error) {
        std::cerr << "Simulation failed: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
