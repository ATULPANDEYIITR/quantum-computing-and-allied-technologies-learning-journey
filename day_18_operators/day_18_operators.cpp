#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Operators: Hermitian and Unitary Operators
 * ===========================================
 *
 * Industry-style case study:
 *
 * A small quantum state-vector engine for validating and executing a
 * variational quantum circuit.
 *
 * The implementation demonstrates:
 *   - complex arithmetic
 *   - vectors and dense matrices
 *   - conjugate transpose
 *   - Hermitian operators
 *   - unitary operators
 *   - observables and expectation values
 *   - tensor products
 *   - controlled operators
 *   - circuit composition
 *   - measurement sampling
 *   - numerical tolerances
 *   - validation and error handling
 *
 * C++17 or later is required.
 */

using Complex = std::complex<double>;
using Vector = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double PI = 3.141592653589793238462643383279502884;
constexpr double DEFAULT_TOLERANCE = 1e-10;


// ---------------------------------------------------------------------------
// 1. Matrix construction and validation
// ---------------------------------------------------------------------------

Matrix zeros(std::size_t rows, std::size_t columns) {
    return Matrix(rows, std::vector<Complex>(columns, Complex{0.0, 0.0}));
}

Matrix identity(std::size_t size) {
    Matrix result = zeros(size, size);

    for (std::size_t i = 0; i < size; ++i) {
        result[i][i] = Complex{1.0, 0.0};
    }

    return result;
}

void validateRectangular(const Matrix& matrix) {
    if (matrix.empty()) {
        throw std::invalid_argument("Matrix cannot be empty.");
    }

    const std::size_t columns = matrix.front().size();

    if (columns == 0) {
        throw std::invalid_argument("Matrix rows cannot be empty.");
    }

    for (const auto& row : matrix) {
        if (row.size() != columns) {
            throw std::invalid_argument("Matrix must be rectangular.");
        }
    }
}

std::pair<std::size_t, std::size_t> shape(const Matrix& matrix) {
    validateRectangular(matrix);
    return {matrix.size(), matrix.front().size()};
}

void validateSquare(const Matrix& matrix) {
    const auto [rows, columns] = shape(matrix);

    if (rows != columns) {
        throw std::invalid_argument("Operator matrix must be square.");
    }
}

Matrix add(const Matrix& a, const Matrix& b) {
    const auto [rowsA, columnsA] = shape(a);
    const auto [rowsB, columnsB] = shape(b);

    if (rowsA != rowsB || columnsA != columnsB) {
        throw std::invalid_argument("Matrix dimensions do not match.");
    }

    Matrix result = zeros(rowsA, columnsA);

    for (std::size_t i = 0; i < rowsA; ++i) {
        for (std::size_t j = 0; j < columnsA; ++j) {
            result[i][j] = a[i][j] + b[i][j];
        }
    }

    return result;
}

Matrix subtract(const Matrix& a, const Matrix& b) {
    const auto [rowsA, columnsA] = shape(a);
    const auto [rowsB, columnsB] = shape(b);

    if (rowsA != rowsB || columnsA != columnsB) {
        throw std::invalid_argument("Matrix dimensions do not match.");
    }

    Matrix result = zeros(rowsA, columnsA);

    for (std::size_t i = 0; i < rowsA; ++i) {
        for (std::size_t j = 0; j < columnsA; ++j) {
            result[i][j] = a[i][j] - b[i][j];
        }
    }

    return result;
}

Matrix scalarMultiply(const Complex& scalar, const Matrix& matrix) {
    const auto [rows, columns] = shape(matrix);
    Matrix result = zeros(rows, columns);

    for (std::size_t i = 0; i < rows; ++i) {
        for (std::size_t j = 0; j < columns; ++j) {
            result[i][j] = scalar * matrix[i][j];
        }
    }

    return result;
}

Matrix multiply(const Matrix& a, const Matrix& b) {
    const auto [rowsA, columnsA] = shape(a);
    const auto [rowsB, columnsB] = shape(b);

    if (columnsA != rowsB) {
        throw std::invalid_argument(
            "Matrix dimensions are incompatible for multiplication."
        );
    }

    Matrix result = zeros(rowsA, columnsB);

    for (std::size_t i = 0; i < rowsA; ++i) {
        for (std::size_t j = 0; j < columnsB; ++j) {
            Complex sum{0.0, 0.0};

            for (std::size_t k = 0; k < columnsA; ++k) {
                sum += a[i][k] * b[k][j];
            }

            result[i][j] = sum;
        }
    }

    return result;
}

Vector multiply(const Matrix& matrix, const Vector& vector) {
    const auto [rows, columns] = shape(matrix);

    if (columns != vector.size()) {
        throw std::invalid_argument(
            "Matrix and vector dimensions are incompatible."
        );
    }

    Vector result(rows, Complex{0.0, 0.0});

    for (std::size_t i = 0; i < rows; ++i) {
        for (std::size_t j = 0; j < columns; ++j) {
            result[i] += matrix[i][j] * vector[j];
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// 2. Complex-vector mathematics
// ---------------------------------------------------------------------------

double vectorNorm(const Vector& vector) {
    double squaredNorm = 0.0;

    for (const auto& value : vector) {
        squaredNorm += std::norm(value);
    }

    return std::sqrt(squaredNorm);
}

Vector normalize(Vector vector) {
    const double norm = vectorNorm(vector);

    if (norm <= DEFAULT_TOLERANCE) {
        throw std::invalid_argument(
            "Cannot normalize the zero vector."
        );
    }

    for (auto& value : vector) {
        value /= norm;
    }

    return vector;
}

Complex innerProduct(const Vector& left, const Vector& right) {
    if (left.size() != right.size()) {
        throw std::invalid_argument(
            "Inner-product vectors must have equal dimensions."
        );
    }

    Complex result{0.0, 0.0};

    for (std::size_t i = 0; i < left.size(); ++i) {
        // std::conj(left[i]) implements the bra <left|.
        result += std::conj(left[i]) * right[i];
    }

    return result;
}

bool closeEnough(
    const Complex& a,
    const Complex& b,
    double tolerance = DEFAULT_TOLERANCE
) {
    return std::abs(a - b) <= tolerance;
}

bool matricesClose(
    const Matrix& a,
    const Matrix& b,
    double tolerance = DEFAULT_TOLERANCE
) {
    try {
        const auto [rowsA, columnsA] = shape(a);
        const auto [rowsB, columnsB] = shape(b);

        if (rowsA != rowsB || columnsA != columnsB) {
            return false;
        }

        for (std::size_t i = 0; i < rowsA; ++i) {
            for (std::size_t j = 0; j < columnsA; ++j) {
                if (!closeEnough(a[i][j], b[i][j], tolerance)) {
                    return false;
                }
            }
        }

        return true;
    } catch (...) {
        return false;
    }
}


// ---------------------------------------------------------------------------
// 3. Adjoint and operator classification
// ---------------------------------------------------------------------------

Matrix adjoint(const Matrix& operatorMatrix) {
    const auto [rows, columns] = shape(operatorMatrix);
    Matrix result = zeros(columns, rows);

    for (std::size_t row = 0; row < rows; ++row) {
        for (std::size_t column = 0; column < columns; ++column) {
            // The adjoint is the conjugate transpose, not merely transpose.
            result[column][row] = std::conj(operatorMatrix[row][column]);
        }
    }

    return result;
}

bool isHermitian(
    const Matrix& operatorMatrix,
    double tolerance = DEFAULT_TOLERANCE
) {
    try {
        validateSquare(operatorMatrix);
        return matricesClose(
            operatorMatrix,
            adjoint(operatorMatrix),
            tolerance
        );
    } catch (...) {
        return false;
    }
}

bool isUnitary(
    const Matrix& operatorMatrix,
    double tolerance = DEFAULT_TOLERANCE
) {
    try {
        validateSquare(operatorMatrix);

        const std::size_t size = operatorMatrix.size();
        const Matrix identityMatrix = identity(size);
        const Matrix operatorAdjoint = adjoint(operatorMatrix);

        const Matrix left =
            multiply(operatorAdjoint, operatorMatrix);

        const Matrix right =
            multiply(operatorMatrix, operatorAdjoint);

        return (
            matricesClose(left, identityMatrix, tolerance) &&
            matricesClose(right, identityMatrix, tolerance)
        );
    } catch (...) {
        return false;
    }
}

bool isNormal(
    const Matrix& operatorMatrix,
    double tolerance = DEFAULT_TOLERANCE
) {
    try {
        validateSquare(operatorMatrix);

        const Matrix operatorAdjoint = adjoint(operatorMatrix);

        return matricesClose(
            multiply(operatorAdjoint, operatorMatrix),
            multiply(operatorMatrix, operatorAdjoint),
            tolerance
        );
    } catch (...) {
        return false;
    }
}


// ---------------------------------------------------------------------------
// 4. Standard quantum operators
// ---------------------------------------------------------------------------

Matrix pauliX() {
    return {
        {Complex{0.0, 0.0}, Complex{1.0, 0.0}},
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}}
    };
}

Matrix pauliY() {
    return {
        {Complex{0.0, 0.0}, Complex{0.0, -1.0}},
        {Complex{0.0, 1.0}, Complex{0.0, 0.0}}
    };
}

Matrix pauliZ() {
    return {
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{-1.0, 0.0}}
    };
}

Matrix hadamard() {
    const double value = 1.0 / std::sqrt(2.0);

    return {
        {Complex{value, 0.0}, Complex{value, 0.0}},
        {Complex{value, 0.0}, Complex{-value, 0.0}}
    };
}

Matrix phaseGate(double theta) {
    return {
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, std::exp(Complex{0.0, theta})}
    };
}

Matrix rotationX(double theta) {
    const double half = theta / 2.0;
    const double cosine = std::cos(half);
    const double sine = std::sin(half);

    return {
        {Complex{cosine, 0.0}, Complex{0.0, -sine}},
        {Complex{0.0, -sine}, Complex{cosine, 0.0}}
    };
}

Matrix rotationY(double theta) {
    const double half = theta / 2.0;
    const double cosine = std::cos(half);
    const double sine = std::sin(half);

    return {
        {Complex{cosine, 0.0}, Complex{-sine, 0.0}},
        {Complex{sine, 0.0}, Complex{cosine, 0.0}}
    };
}

Matrix rotationZ(double theta) {
    const double half = theta / 2.0;

    return {
        {std::exp(Complex{0.0, -half}), Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, std::exp(Complex{0.0, half})}
    };
}


// ---------------------------------------------------------------------------
// 5. Quantum-state and observable calculations
// ---------------------------------------------------------------------------

Vector basisState(std::size_t index, std::size_t dimension) {
    if (index >= dimension) {
        throw std::invalid_argument(
            "Basis-state index exceeds dimension."
        );
    }

    Vector state(dimension, Complex{0.0, 0.0});
    state[index] = Complex{1.0, 0.0};
    return state;
}

std::vector<double> probabilities(const Vector& state) {
    const Vector normalized = normalize(state);

    std::vector<double> result;
    result.reserve(normalized.size());

    for (const auto& amplitude : normalized) {
        result.push_back(std::norm(amplitude));
    }

    return result;
}

Complex expectationValue(
    const Vector& state,
    const Matrix& observable
) {
    const Vector normalized = normalize(state);
    const Vector transformed = multiply(observable, normalized);

    // For a Hermitian observable, this scalar should be real.
    return innerProduct(normalized, transformed);
}

double variance(
    const Vector& state,
    const Matrix& observable
) {
    const Complex mean = expectationValue(state, observable);

    const Matrix squaredObservable =
        multiply(observable, observable);

    const Complex secondMoment =
        expectationValue(state, squaredObservable);

    const double value =
        (secondMoment - mean * mean).real();

    return std::max(0.0, value);
}


// ---------------------------------------------------------------------------
// 6. Projectors
// ---------------------------------------------------------------------------

Matrix projectorZero() {
    return {
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{0.0, 0.0}}
    };
}

Matrix projectorOne() {
    return {
        {Complex{0.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{1.0, 0.0}}
    };
}

bool isProjector(
    const Matrix& matrix,
    double tolerance = DEFAULT_TOLERANCE
) {
    return matricesClose(
        multiply(matrix, matrix),
        matrix,
        tolerance
    );
}


// ---------------------------------------------------------------------------
// 7. Tensor products
// ---------------------------------------------------------------------------

Matrix tensorProduct(
    const Matrix& a,
    const Matrix& b
) {
    const auto [rowsA, columnsA] = shape(a);
    const auto [rowsB, columnsB] = shape(b);

    Matrix result = zeros(
        rowsA * rowsB,
        columnsA * columnsB
    );

    for (std::size_t i = 0; i < rowsA; ++i) {
        for (std::size_t j = 0; j < columnsA; ++j) {
            for (std::size_t k = 0; k < rowsB; ++k) {
                for (std::size_t l = 0; l < columnsB; ++l) {
                    result[i * rowsB + k][j * columnsB + l] =
                        a[i][j] * b[k][l];
                }
            }
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// 8. Controlled-U
// ---------------------------------------------------------------------------

Matrix controlledUnitary(const Matrix& target) {
    const auto [rows, columns] = shape(target);

    if (rows != 2 || columns != 2) {
        throw std::invalid_argument(
            "This implementation expects a 2x2 target operator."
        );
    }

    Matrix result = zeros(4, 4);

    // Basis ordering:
    // |00>, |01>, |10>, |11>
    //
    // Control = 0 -> I
    // Control = 1 -> U

    result[0][0] = Complex{1.0, 0.0};
    result[1][1] = Complex{1.0, 0.0};

    for (std::size_t row = 0; row < 2; ++row) {
        for (std::size_t column = 0; column < 2; ++column) {
            result[row + 2][column + 2] = target[row][column];
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// 9. Measurement sampling
// ---------------------------------------------------------------------------

std::size_t sampleOutcome(
    const std::vector<double>& probabilities,
    std::mt19937& generator
) {
    std::uniform_real_distribution<double> distribution(0.0, 1.0);
    const double randomValue = distribution(generator);

    double cumulative = 0.0;

    for (std::size_t index = 0; index < probabilities.size(); ++index) {
        cumulative += probabilities[index];

        if (randomValue < cumulative) {
            return index;
        }
    }

    // Handles the rare floating-point case where cumulative is just below 1.
    return probabilities.size() - 1;
}

std::vector<std::size_t> measure(
    const Vector& state,
    std::size_t shots,
    unsigned seed = 42
) {
    if (shots == 0) {
        throw std::invalid_argument("shots must be positive.");
    }

    const std::vector<double> probabilityValues =
        probabilities(state);

    std::mt19937 generator(seed);

    std::vector<std::size_t> outcomes;
    outcomes.reserve(shots);

    for (std::size_t shot = 0; shot < shots; ++shot) {
        outcomes.push_back(
            sampleOutcome(probabilityValues, generator)
        );
    }

    return outcomes;
}

std::map<std::size_t, std::size_t> countOutcomes(
    const std::vector<std::size_t>& outcomes
) {
    std::map<std::size_t, std::size_t> counts;

    for (const auto outcome : outcomes) {
        ++counts[outcome];
    }

    return counts;
}


// ---------------------------------------------------------------------------
// 10. Quantum circuit abstraction
// ---------------------------------------------------------------------------

class QuantumCircuit {
private:
    std::size_t qubitCount_;
    std::size_t dimension_;
    Vector state_;

public:
    explicit QuantumCircuit(std::size_t qubitCount)
        : qubitCount_(qubitCount),
          dimension_(static_cast<std::size_t>(1ULL << qubitCount)),
          state_(basisState(0, dimension_)) {

        if (qubitCount == 0) {
            throw std::invalid_argument(
                "A circuit must contain at least one qubit."
            );
        }

        // Dense state-vector storage uses 2^n amplitudes. A limit is enforced
        // here because this is a teaching implementation rather than a
        // sparse/high-performance simulator.
        if (qubitCount > 8) {
            throw std::invalid_argument(
                "This dense educational simulator supports at most 8 qubits."
            );
        }
    }

    const Vector& state() const {
        return state_;
    }

    double norm() const {
        return vectorNorm(state_);
    }

    void applySingleQubitGate(
        const Matrix& gate,
        std::size_t targetQubit
    ) {
        if (targetQubit >= qubitCount_) {
            throw std::out_of_range("Target qubit index is invalid.");
        }

        if (!isUnitary(gate)) {
            throw std::invalid_argument(
                "Quantum gates must be unitary."
            );
        }

        Matrix fullOperator;

        // Qubit 0 is the most significant tensor-product position.
        for (std::size_t position = 0;
             position < qubitCount_;
             ++position) {

            const Matrix& factor =
                position == targetQubit
                    ? gate
                    : identity(2);

            if (position == 0) {
                fullOperator = factor;
            } else {
                fullOperator =
                    tensorProduct(fullOperator, factor);
            }
        }

        state_ = multiply(fullOperator, state_);

        // Defensive numerical normalization keeps tiny accumulated errors
        // from growing during long simulations.
        state_ = normalize(state_);
    }

    void applyFullOperator(const Matrix& operatorMatrix) {
        const auto [rows, columns] = shape(operatorMatrix);

        if (rows != dimension_ || columns != dimension_) {
            throw std::invalid_argument(
                "Operator dimension does not match circuit dimension."
            );
        }

        if (!isUnitary(operatorMatrix)) {
            throw std::invalid_argument(
                "A full circuit transformation must be unitary."
            );
        }

        state_ = multiply(operatorMatrix, state_);
        state_ = normalize(state_);
    }

    std::vector<double> probabilities() const {
        return ::probabilities(state_);
    }

    std::map<std::size_t, std::size_t> measure(
        std::size_t shots,
        unsigned seed = 42
    ) const {
        return countOutcomes(
            ::measure(state_, shots, seed)
        );
    }
};


// ---------------------------------------------------------------------------
// 11. Display utilities
// ---------------------------------------------------------------------------

void printComplex(const Complex& value) {
    const double real = std::abs(value.real()) < 1e-10
        ? 0.0
        : value.real();

    const double imaginary = std::abs(value.imag()) < 1e-10
        ? 0.0
        : value.imag();

    std::cout << std::fixed << std::setprecision(5);

    if (imaginary == 0.0) {
        std::cout << real;
    } else if (real == 0.0) {
        std::cout << imaginary << "i";
    } else {
        std::cout << real
                  << (imaginary >= 0.0 ? "+" : "")
                  << imaginary
                  << "i";
    }
}

void printMatrix(const Matrix& matrix) {
    for (const auto& row : matrix) {
        std::cout << "[ ";

        for (const auto& value : row) {
            printComplex(value);
            std::cout << " ";
        }

        std::cout << "]\n";
    }
}

void printVector(const Vector& vector) {
    std::cout << "[ ";

    for (const auto& value : vector) {
        printComplex(value);
        std::cout << " ";
    }

    std::cout << "]\n";
}

void printProbabilities(
    const std::vector<double>& values
) {
    for (std::size_t index = 0; index < values.size(); ++index) {
        std::cout
            << "  |" << index << "> : "
            << std::fixed
            << std::setprecision(6)
            << values[index]
            << "\n";
    }
}


// ---------------------------------------------------------------------------
// 12. Operator analysis
// ---------------------------------------------------------------------------

void analyzeOperator(
    const std::string& name,
    const Matrix& operatorMatrix
) {
    std::cout << "\n" << name << "\n";
    std::cout << std::string(name.size(), '-') << "\n";

    printMatrix(operatorMatrix);

    std::cout
        << "Hermitian: "
        << std::boolalpha
        << isHermitian(operatorMatrix)
        << "\n";

    std::cout
        << "Unitary:   "
        << std::boolalpha
        << isUnitary(operatorMatrix)
        << "\n";

    std::cout
        << "Normal:    "
        << std::boolalpha
        << isNormal(operatorMatrix)
        << "\n";
}


// ---------------------------------------------------------------------------
// 13. Case study: variational quantum circuit
// ---------------------------------------------------------------------------

class VariationalCircuit {
private:
    QuantumCircuit circuit_;
    double theta_;

public:
    explicit VariationalCircuit(double theta)
        : circuit_(1),
          theta_(theta) {}

    void prepare() {
        // H prepares a superposition.
        circuit_.applySingleQubitGate(hadamard(), 0);

        // RY(theta) is a unitary rotation generated by a Hermitian
        // Pauli-Y operator.
        circuit_.applySingleQubitGate(rotationY(theta_), 0);
    }

    Complex energy(const Matrix& hamiltonian) const {
        return expectationValue(
            circuit_.state(),
            hamiltonian
        );
    }

    const Vector& state() const {
        return circuit_.state();
    }
};


// ---------------------------------------------------------------------------
// 14. Demonstrations
// ---------------------------------------------------------------------------

void demonstrateFundamentals() {
    std::cout
        << "\n============================================================\n"
        << "1. OPERATOR CLASSIFICATION\n"
        << "============================================================\n";

    analyzeOperator("Pauli X", pauliX());
    analyzeOperator("Pauli Y", pauliY());
    analyzeOperator("Pauli Z", pauliZ());
    analyzeOperator("Hadamard", hadamard());
    analyzeOperator("Phase gate", phaseGate(PI / 3.0));

    Matrix hermitianNotUnitary = {
        {Complex{2.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{-3.0, 0.0}}
    };

    Matrix nonNormal = {
        {Complex{0.0, 0.0}, Complex{1.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{0.0, 0.0}}
    };

    analyzeOperator(
        "Hermitian but not unitary",
        hermitianNotUnitary
    );

    analyzeOperator(
        "Non-normal operator",
        nonNormal
    );
}

void demonstrateObservables() {
    std::cout
        << "\n============================================================\n"
        << "2. OBSERVABLES AND EXPECTATION VALUES\n"
        << "============================================================\n";

    const Matrix x = pauliX();
    const Matrix z = pauliZ();

    Vector zeroState = basisState(0, 2);
    Vector plusState = normalize({
        Complex{1.0, 0.0},
        Complex{1.0, 0.0}
    });

    std::cout << "\nState |0>:\n";
    printVector(zeroState);

    std::cout << "<X> = ";
    printComplex(expectationValue(zeroState, x));
    std::cout << "\n";

    std::cout << "<Z> = ";
    printComplex(expectationValue(zeroState, z));
    std::cout << "\n";

    std::cout
        << "Var(Z) = "
        << variance(zeroState, z)
        << "\n";

    std::cout << "\nState |+>:\n";
    printVector(plusState);

    std::cout << "<X> = ";
    printComplex(expectationValue(plusState, x));
    std::cout << "\n";

    std::cout << "<Z> = ";
    printComplex(expectationValue(plusState, z));
    std::cout << "\n";

    std::cout
        << "Var(X) = "
        << variance(plusState, x)
        << "\n";
}

void demonstrateUnitaryPreservation() {
    std::cout
        << "\n============================================================\n"
        << "3. UNITARY PRESERVATION OF NORM\n"
        << "============================================================\n";

    Vector state = normalize({
        Complex{1.0, 0.0},
        Complex{2.0, -1.0}
    });

    const Matrix gates[] = {
        pauliX(),
        pauliY(),
        pauliZ(),
        hadamard(),
        rotationZ(PI / 4.0)
    };

    const std::string names[] = {
        "X",
        "Y",
        "Z",
        "H",
        "Rz(pi/4)"
    };

    for (std::size_t i = 0; i < 5; ++i) {
        const Vector transformed =
            multiply(gates[i], state);

        std::cout
            << names[i]
            << ": before = "
            << vectorNorm(state)
            << ", after = "
            << vectorNorm(transformed)
            << "\n";
    }
}

void demonstrateTensorProduct() {
    std::cout
        << "\n============================================================\n"
        << "4. TWO-QUBIT TENSOR PRODUCTS\n"
        << "============================================================\n";

    const Matrix h = hadamard();

    const Matrix hh =
        tensorProduct(h, h);

    const Matrix xi =
        tensorProduct(pauliX(), identity(2));

    std::cout << "\nH tensor H:\n";
    printMatrix(hh);

    std::cout
        << "Unitary: "
        << isUnitary(hh)
        << "\n";

    std::cout << "\nX tensor I:\n";
    printMatrix(xi);

    std::cout
        << "Unitary: "
        << isUnitary(xi)
        << "\n";

    const Vector state00 =
        basisState(0, 4);

    const Vector result =
        multiply(hh, state00);

    std::cout << "\n(H tensor H)|00>:\n";
    printVector(result);

    std::cout << "\nProbabilities:\n";
    printProbabilities(probabilities(result));
}

void demonstrateCnot() {
    std::cout
        << "\n============================================================\n"
        << "5. CONTROLLED UNITARY / CNOT\n"
        << "============================================================\n";

    const Matrix cnot =
        controlledUnitary(pauliX());

    std::cout << "CNOT matrix:\n";
    printMatrix(cnot);

    std::cout
        << "Hermitian: "
        << isHermitian(cnot)
        << "\n";

    std::cout
        << "Unitary: "
        << isUnitary(cnot)
        << "\n";

    for (std::size_t index = 0; index < 4; ++index) {
        const Vector input =
            basisState(index, 4);

        const Vector output =
            multiply(cnot, input);

        std::cout
            << "\nBasis state "
            << index
            << " -> ";

        printVector(output);
    }
}

void demonstrateBellStateCircuit() {
    std::cout
        << "\n============================================================\n"
        << "6. INDUSTRY-STYLE STATE-VECTOR CIRCUIT\n"
        << "============================================================\n";

    QuantumCircuit circuit(2);

    std::cout << "\nInitial state:\n";
    printVector(circuit.state());

    circuit.applySingleQubitGate(
        hadamard(),
        0
    );

    std::cout << "\nAfter H on qubit 0:\n";
    printVector(circuit.state());

    circuit.applyFullOperator(
        controlledUnitary(pauliX())
    );

    std::cout << "\nAfter CNOT:\n";
    printVector(circuit.state());

    std::cout
        << "\nState norm: "
        << circuit.norm()
        << "\n";

    std::cout << "\nFinal probabilities:\n";
    printProbabilities(circuit.probabilities());

    const auto counts =
        circuit.measure(10000, 123);

    std::cout << "\n10,000 deterministic-seed measurement samples:\n";

    for (const auto& [basisIndex, count] : counts) {
        std::cout
            << "  basis "
            << basisIndex
            << " -> "
            << count
            << "\n";
    }
}

void demonstrateVariationalCaseStudy() {
    std::cout
        << "\n============================================================\n"
        << "7. VARIATIONAL OBSERVABLE MEASUREMENT CASE STUDY\n"
        << "============================================================\n";

    /*
     * Suppose a physical or optimization problem produces a one-qubit
     * Hamiltonian:
     *
     *     H = 0.8 Z + 0.3 X
     *
     * Because X and Z are Hermitian and the coefficients are real,
     * H is Hermitian and therefore represents a valid observable.
     */

    const Matrix hamiltonian =
        add(
            scalarMultiply(
                Complex{0.8, 0.0},
                pauliZ()
            ),
            scalarMultiply(
                Complex{0.3, 0.0},
                pauliX()
            )
        );

    std::cout << "\nHamiltonian:\n";
    printMatrix(hamiltonian);

    std::cout
        << "Hermitian: "
        << isHermitian(hamiltonian)
        << "\n";

    /*
     * A variational circuit prepares a parameterized state.
     * Its objective value is <psi(theta)|H|psi(theta)>.
     */
    VariationalCircuit circuit(PI / 5.0);
    circuit.prepare();

    std::cout << "\nParameterized state:\n";
    printVector(circuit.state());

    const Complex energy =
        circuit.energy(hamiltonian);

    std::cout
        << "\nEnergy expectation: ";
    printComplex(energy);
    std::cout << "\n";

    std::cout
        << "The expectation is real up to floating-point error because "
        << "the Hamiltonian is Hermitian.\n";
}

void demonstrateValidationFailures() {
    std::cout
        << "\n============================================================\n"
        << "8. VALIDATION AND FAILURE CONDITIONS\n"
        << "============================================================\n";

    try {
        normalize({
            Complex{0.0, 0.0},
            Complex{0.0, 0.0}
        });
    } catch (const std::exception& error) {
        std::cout
            << "Zero-state validation: "
            << error.what()
            << "\n";
    }

    try {
        QuantumCircuit invalidCircuit(0);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid circuit validation: "
            << error.what()
            << "\n";
    }

    try {
        QuantumCircuit oversizedCircuit(9);
    } catch (const std::exception& error) {
        std::cout
            << "Dense-memory constraint: "
            << error.what()
            << "\n";
    }

    try {
        Matrix invalidGate = {
            {Complex{1.0, 0.0}, Complex{1.0, 0.0}},
            {Complex{0.0, 0.0}, Complex{1.0, 0.0}}
        };

        QuantumCircuit circuit(1);
        circuit.applySingleQubitGate(
            invalidGate,
            0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Non-unitary gate rejection: "
            << error.what()
            << "\n";
    }
}

void demonstrateOperatorOrder() {
    std::cout
        << "\n============================================================\n"
        << "9. OPERATOR ORDER\n"
        << "============================================================\n";

    const Matrix hx =
        multiply(hadamard(), pauliX());

    const Matrix xh =
        multiply(pauliX(), hadamard());

    std::cout
        << "HX equals XH: "
        << std::boolalpha
        << matricesClose(hx, xh)
        << "\n";

    std::cout
        << "This illustrates that operator composition is generally "
        << "non-commutative.\n";

    const Matrix xInverse =
        adjoint(pauliX());

    const Matrix hInverse =
        adjoint(hadamard());

    std::cout
        << "X^dagger X = I: "
        << matricesClose(
            multiply(xInverse, pauliX()),
            identity(2)
        )
        << "\n";

    std::cout
        << "H^dagger H = I: "
        << matricesClose(
            multiply(hInverse, hadamard()),
            identity(2)
        )
        << "\n";
}


// ---------------------------------------------------------------------------
// 15. Main
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "OPERATORS: HERMITIAN AND UNITARY OPERATORS\n"
            << "C++17 quantum operator and circuit case study\n";

        demonstrateFundamentals();
        demonstrateObservables();
        demonstrateUnitaryPreservation();
        demonstrateTensorProduct();
        demonstrateCnot();
        demonstrateBellStateCircuit();
        demonstrateVariationalCaseStudy();
        demonstrateValidationFailures();
        demonstrateOperatorOrder();

        std::cout
            << "\n============================================================\n"
            << "CASE STUDY COMPLETE\n"
            << "============================================================\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
