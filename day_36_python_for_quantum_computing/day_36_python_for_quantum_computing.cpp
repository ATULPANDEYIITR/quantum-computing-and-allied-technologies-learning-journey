#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Quantum state-vector case study:
 *
 * A small repository of quantum experiments is represented as a circuit
 * engine. The implementation emphasizes C++ ownership, value semantics,
 * vector-based numerical storage, matrix multiplication, validation,
 * controlled operations, measurement sampling, and computational scaling.
 *
 * Compile:
 *   g++ -std=c++17 -O2 quantum_case_study.cpp -o quantum_case_study
 */

using Complex = std::complex<double>;
using Vector = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double EPSILON = 1e-10;

void printHeading(const std::string& title) {
    std::cout << "\n" << std::string(78, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(78, '=') << "\n";
}

std::size_t qubitCount(const Vector& state) {
    if (state.empty()) {
        throw std::invalid_argument("State cannot be empty.");
    }

    std::size_t size = state.size();
    std::size_t qubits = 0;

    while (size > 1) {
        if (size % 2 != 0) {
            throw std::invalid_argument(
                "State dimension must be a power of two."
            );
        }

        size /= 2;
        ++qubits;
    }

    return qubits;
}

double norm(const Vector& state) {
    double squared = 0.0;

    for (const Complex& amplitude : state) {
        squared += std::norm(amplitude);
    }

    return std::sqrt(squared);
}

void validateState(const Vector& state) {
    qubitCount(state);

    if (std::abs(norm(state) - 1.0) > EPSILON) {
        throw std::invalid_argument("Quantum state is not normalized.");
    }
}

Vector normalize(Vector state) {
    const double stateNorm = norm(state);

    if (stateNorm < EPSILON) {
        throw std::invalid_argument(
            "Cannot normalize a zero vector."
        );
    }

    for (Complex& amplitude : state) {
        amplitude /= stateNorm;
    }

    return state;
}

Vector basisState(const std::string& bits) {
    if (bits.empty()) {
        throw std::invalid_argument("Basis label cannot be empty.");
    }

    for (char bit : bits) {
        if (bit != '0' && bit != '1') {
            throw std::invalid_argument(
                "Basis labels must contain only 0 and 1."
            );
        }
    }

    const std::size_t dimension = 1ULL << bits.size();
    Vector state(dimension, Complex{0.0, 0.0});

    const std::size_t index =
        static_cast<std::size_t>(std::stoull(bits, nullptr, 2));

    state[index] = Complex{1.0, 0.0};

    return state;
}

Matrix identity(std::size_t dimension) {
    Matrix result(
        dimension,
        std::vector<Complex>(
            dimension,
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t i = 0; i < dimension; ++i) {
        result[i][i] = Complex{1.0, 0.0};
    }

    return result;
}

Vector matrixVectorMultiply(
    const Matrix& matrix,
    const Vector& vector
) {
    if (matrix.size() != vector.size()) {
        throw std::invalid_argument(
            "Matrix and vector dimensions do not match."
        );
    }

    Vector result(vector.size(), Complex{0.0, 0.0});

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        if (matrix[row].size() != vector.size()) {
            throw std::invalid_argument("Matrix must be square.");
        }

        for (std::size_t column = 0; column < vector.size(); ++column) {
            result[row] += matrix[row][column] * vector[column];
        }
    }

    return result;
}

Matrix kron(const Matrix& left, const Matrix& right) {
    const std::size_t rows =
        left.size() * right.size();

    const std::size_t columns =
        left.front().size() * right.front().size();

    Matrix result(
        rows,
        std::vector<Complex>(
            columns,
            Complex{0.0, 0.0}
        )
    );

    for (std::size_t r1 = 0; r1 < left.size(); ++r1) {
        for (std::size_t c1 = 0; c1 < left[r1].size(); ++c1) {
            for (std::size_t r2 = 0; r2 < right.size(); ++r2) {
                for (std::size_t c2 = 0; c2 < right[r2].size(); ++c2) {
                    result[
                        r1 * right.size() + r2
                    ][
                        c1 * right[r2].size() + c2
                    ] = left[r1][c1] * right[r2][c2];
                }
            }
        }
    }

    return result;
}

Matrix pauliX() {
    return {
        {Complex{0, 0}, Complex{1, 0}},
        {Complex{1, 0}, Complex{0, 0}}
    };
}

Matrix pauliZ() {
    return {
        {Complex{1, 0}, Complex{0, 0}},
        {Complex{0, 0}, Complex{-1, 0}}
    };
}

Matrix hadamard() {
    const double scale = 1.0 / std::sqrt(2.0);

    return {
        {Complex{scale, 0}, Complex{scale, 0}},
        {Complex{scale, 0}, Complex{-scale, 0}}
    };
}

Matrix controlledX(
    std::size_t qubits,
    std::size_t control,
    std::size_t target
) {
    if (control == target) {
        throw std::invalid_argument(
            "Control and target must be different."
        );
    }

    if (control >= qubits || target >= qubits) {
        throw std::out_of_range(
            "Control or target is outside the circuit."
        );
    }

    const std::size_t dimension = 1ULL << qubits;
    Matrix result = identity(dimension);

    for (std::size_t column = 0; column < dimension; ++column) {
        const std::size_t controlBit =
            (column >> (qubits - 1 - control)) & 1ULL;

        if (controlBit == 1) {
            const std::size_t targetMask =
                1ULL << (qubits - 1 - target);

            const std::size_t row =
                column ^ targetMask;

            result[column][column] = Complex{0, 0};
            result[row][column] = Complex{1, 0};
        }
    }

    return result;
}

std::string bitString(
    std::size_t value,
    std::size_t width
) {
    std::string result(width, '0');

    for (std::size_t position = 0; position < width; ++position) {
        const std::size_t shift = width - 1 - position;

        if ((value >> shift) & 1ULL) {
            result[position] = '1';
        }
    }

    return result;
}

void printState(const Vector& state) {
    validateState(state);

    const std::size_t qubits = qubitCount(state);
    bool printed = false;

    for (std::size_t index = 0; index < state.size(); ++index) {
        if (std::abs(state[index]) > EPSILON) {
            if (printed) {
                std::cout << " + ";
            }

            std::cout
                << "("
                << std::fixed
                << std::setprecision(4)
                << state[index]
                << ")|"
                << bitString(index, qubits)
                << ">";

            printed = true;
        }
    }

    if (!printed) {
        std::cout << "0";
    }

    std::cout << "\n";
}

std::map<std::string, std::size_t> measure(
    const Vector& state,
    std::size_t shots,
    std::uint64_t seed
) {
    validateState(state);

    if (shots == 0) {
        throw std::invalid_argument("Shots must be positive.");
    }

    const std::size_t qubits = qubitCount(state);

    std::vector<double> weights;
    weights.reserve(state.size());

    for (const Complex& amplitude : state) {
        weights.push_back(std::norm(amplitude));
    }

    std::discrete_distribution<std::size_t> distribution(
        weights.begin(),
        weights.end()
    );

    std::mt19937_64 generator(seed);
    std::map<std::string, std::size_t> counts;

    for (std::size_t shot = 0; shot < shots; ++shot) {
        const std::size_t result = distribution(generator);
        ++counts[bitString(result, qubits)];
    }

    return counts;
}

class QuantumCircuit {
private:
    std::size_t qubits_;
    Vector state_;
    std::vector<std::string> history_;

public:
    explicit QuantumCircuit(std::size_t qubits)
        : qubits_(qubits),
          state_(basisState(std::string(qubits, '0'))) {
        if (qubits == 0 || qubits > 18) {
            throw std::invalid_argument(
                "Educational circuit size must be between 1 and 18."
            );
        }
    }

    void applySingleQubit(
        const Matrix& gate,
        std::size_t target,
        const std::string& name
    ) {
        if (target >= qubits_) {
            throw std::out_of_range(
                "Target qubit is outside the circuit."
            );
        }

        Matrix fullGate = gate;

        for (std::size_t position = 0; position < qubits_; ++position) {
            if (position == target) {
                if (position == 0) {
                    fullGate = gate;
                }
                continue;
            }

            const Matrix identityQubit = identity(2);

            if (position == 0 && target != 0) {
                fullGate = identityQubit;
            } else {
                fullGate = kron(fullGate, identityQubit);
            }
        }

        /*
         * The loop above is easiest to reason about by constructing the
         * tensor product explicitly. Rebuild it here to make the qubit
         * ordering unambiguous: q0 is the leftmost tensor factor.
         */
        std::vector<Matrix> factors;

        for (std::size_t position = 0; position < qubits_; ++position) {
            factors.push_back(
                position == target ? gate : identity(2)
            );
        }

        fullGate = factors.front();

        for (std::size_t index = 1; index < factors.size(); ++index) {
            fullGate = kron(fullGate, factors[index]);
        }

        state_ = matrixVectorMultiply(fullGate, state_);
        validateState(state_);
        history_.push_back(name);
    }

    void h(std::size_t target) {
        applySingleQubit(hadamard(), target, "H q" + std::to_string(target));
    }

    void x(std::size_t target) {
        applySingleQubit(pauliX(), target, "X q" + std::to_string(target));
    }

    void z(std::size_t target) {
        applySingleQubit(pauliZ(), target, "Z q" + std::to_string(target));
    }

    void cnot(std::size_t control, std::size_t target) {
        state_ = matrixVectorMultiply(
            controlledX(qubits_, control, target),
            state_
        );

        validateState(state_);

        history_.push_back(
            "CNOT q" +
            std::to_string(control) +
            " -> q" +
            std::to_string(target)
        );
    }

    const Vector& state() const {
        return state_;
    }

    void printHistory() const {
        std::cout << "Circuit history:\n";

        for (const auto& operation : history_) {
            std::cout << "  " << operation << "\n";
        }
    }
};

Complex expectation(
    const Vector& state,
    const Matrix& operatorMatrix
) {
    const Vector transformed =
        matrixVectorMultiply(operatorMatrix, state);

    Complex result{0, 0};

    for (std::size_t index = 0; index < state.size(); ++index) {
        result += std::conj(state[index]) * transformed[index];
    }

    return result;
}

void demonstrateBellState() {
    printHeading("Bell-State Governance Case Study");

    QuantumCircuit circuit(2);

    circuit.h(0);
    circuit.cnot(0, 1);

    circuit.printHistory();

    std::cout << "State: ";
    printState(circuit.state());

    const auto counts = measure(circuit.state(), 1000, 42);

    std::cout << "Measurement counts:\n";

    for (const auto& [bits, count] : counts) {
        std::cout << "  " << bits << ": " << count << "\n";
    }

    /*
     * A Bell state demonstrates a key distinction between individual
     * measurement probabilities and correlations. The only computational
     * basis outcomes are 00 and 11.
     */
    if (counts.contains("01") || counts.contains("10")) {
        throw std::runtime_error(
            "Bell-state simulation produced an impossible basis outcome."
        );
    }
}

void demonstrateNumericalOptimization() {
    printHeading("Numerical Energy Estimation");

    const Matrix z = pauliZ();
    const Matrix rotation = {
        {Complex{std::cos(0.25), 0},
         Complex{-std::sin(0.25), 0}},
        {Complex{std::sin(0.25), 0},
         Complex{std::cos(0.25), 0}}
    };

    const Vector state =
        matrixVectorMultiply(rotation, basisState("0"));

    const Complex energy = expectation(state, z);

    std::cout
        << "Expectation value <Z>: "
        << std::fixed
        << std::setprecision(6)
        << energy.real()
        << "\n";
}

void demonstrateScaling() {
    printHeading("State-Vector Scaling");

    for (std::size_t qubits = 1; qubits <= 12; ++qubits) {
        const std::size_t amplitudes = 1ULL << qubits;
        const std::size_t bytes =
            amplitudes * sizeof(Complex);

        std::cout
            << std::setw(2)
            << qubits
            << " qubits -> "
            << std::setw(5)
            << amplitudes
            << " amplitudes -> "
            << std::fixed
            << std::setprecision(4)
            << static_cast<double>(bytes) / (1024.0 * 1024.0)
            << " MiB\n";
    }
}

int main() {
    try {
        printHeading("C++ Quantum State-Vector Case Study");

        const Vector zero = basisState("0");
        const Matrix h = hadamard();

        const Vector plus =
            matrixVectorMultiply(h, zero);

        std::cout << "H|0> = ";
        printState(plus);

        const Complex zExpectation =
            expectation(plus, pauliZ());

        std::cout
            << "<Z> for |+> = "
            << zExpectation.real()
            << "\n";

        demonstrateBellState();
        demonstrateNumericalOptimization();
        demonstrateScaling();

        std::cout
            << "\nThe case study uses C++ value semantics and explicit "
               "matrix operations to make the cost of full state-vector "
               "simulation visible.\n";

    } catch (const std::exception& error) {
        std::cerr
            << "Experiment failed: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
