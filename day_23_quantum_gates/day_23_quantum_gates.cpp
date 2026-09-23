/*
 * Quantum Gates: X, Y, Z, and Identity
 *
 * C++17 case study:
 *
 * A small educational quantum-state simulator for a single-qubit control
 * component used inside a hypothetical quantum sensing and control system.
 *
 * The program demonstrates:
 *   - complex probability amplitudes
 *   - normalized quantum states
 *   - matrix representation of gates
 *   - X, Y, Z, and Identity gates
 *   - unitary transformations
 *   - gate composition
 *   - measurement probabilities
 *   - simulated measurements
 *   - Bloch-vector coordinates
 *   - expectation values
 *   - tensor products
 *   - Bell-state representation
 *   - validation and failure handling
 *   - automated tests
 *   - basic performance measurement
 *
 * Compile:
 *   g++ -std=c++17 -O2 quantum_gates.cpp -o quantum_gates
 *
 * Run:
 *   ./quantum_gates
 */

#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Complex = std::complex<double>;
using Vector = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double EPSILON = 1e-10;
constexpr double SQRT_TWO = 1.41421356237309504880;

// -----------------------------------------------------------------------------
// Matrix utilities
// -----------------------------------------------------------------------------

std::pair<std::size_t, std::size_t> matrixShape(
    const Matrix& matrix
) {
    if (matrix.empty()) {
        throw std::invalid_argument("Matrix cannot be empty.");
    }

    const std::size_t columns = matrix.front().size();

    if (columns == 0) {
        throw std::invalid_argument("Matrix cannot contain empty rows.");
    }

    for (const auto& row : matrix) {
        if (row.size() != columns) {
            throw std::invalid_argument(
                "Matrix must be rectangular."
            );
        }
    }

    return {matrix.size(), columns};
}


Matrix identityMatrix(std::size_t size) {
    if (size == 0) {
        throw std::invalid_argument(
            "Identity matrix size must be positive."
        );
    }

    Matrix result(
        size,
        std::vector<Complex>(size, Complex(0.0, 0.0))
    );

    for (std::size_t i = 0; i < size; ++i) {
        result[i][i] = Complex(1.0, 0.0);
    }

    return result;
}


Vector matrixVectorMultiply(
    const Matrix& matrix,
    const Vector& vector
) {
    const auto [rows, columns] = matrixShape(matrix);

    if (columns != vector.size()) {
        throw std::invalid_argument(
            "Matrix and vector dimensions are incompatible."
        );
    }

    Vector result(rows, Complex(0.0, 0.0));

    for (std::size_t row = 0; row < rows; ++row) {
        for (std::size_t column = 0; column < columns; ++column) {
            result[row] += matrix[row][column] * vector[column];
        }
    }

    return result;
}


Matrix matrixMultiply(
    const Matrix& left,
    const Matrix& right
) {
    const auto [leftRows, leftColumns] = matrixShape(left);
    const auto [rightRows, rightColumns] = matrixShape(right);

    if (leftColumns != rightRows) {
        throw std::invalid_argument(
            "Matrix dimensions are incompatible."
        );
    }

    Matrix result(
        leftRows,
        std::vector<Complex>(
            rightColumns,
            Complex(0.0, 0.0)
        )
    );

    for (std::size_t row = 0; row < leftRows; ++row) {
        for (std::size_t column = 0; column < rightColumns; ++column) {
            for (std::size_t k = 0; k < leftColumns; ++k) {
                result[row][column] +=
                    left[row][k] * right[k][column];
            }
        }
    }

    return result;
}


Matrix conjugateTranspose(const Matrix& matrix) {
    const auto [rows, columns] = matrixShape(matrix);

    Matrix result(
        columns,
        std::vector<Complex>(
            rows,
            Complex(0.0, 0.0)
        )
    );

    for (std::size_t row = 0; row < rows; ++row) {
        for (std::size_t column = 0; column < columns; ++column) {
            result[column][row] =
                std::conj(matrix[row][column]);
        }
    }

    return result;
}


bool matricesAreClose(
    const Matrix& first,
    const Matrix& second,
    double tolerance = EPSILON
) {
    const auto [firstRows, firstColumns] = matrixShape(first);
    const auto [secondRows, secondColumns] = matrixShape(second);

    if (
        firstRows != secondRows ||
        firstColumns != secondColumns
    ) {
        return false;
    }

    for (std::size_t row = 0; row < firstRows; ++row) {
        for (std::size_t column = 0; column < firstColumns; ++column) {
            if (
                std::abs(
                    first[row][column] -
                    second[row][column]
                ) > tolerance
            ) {
                return false;
            }
        }
    }

    return true;
}


// -----------------------------------------------------------------------------
// Quantum-state utilities
// -----------------------------------------------------------------------------

double vectorNorm(const Vector& vector) {
    double normSquared = 0.0;

    for (const auto& value : vector) {
        normSquared += std::norm(value);
    }

    return std::sqrt(normSquared);
}


void validateSingleQubitState(const Vector& state) {
    if (state.size() != 2) {
        throw std::invalid_argument(
            "A single-qubit state requires exactly two amplitudes."
        );
    }

    const double probabilitySum =
        std::norm(state[0]) +
        std::norm(state[1]);

    if (std::abs(probabilitySum - 1.0) > EPSILON) {
        throw std::invalid_argument(
            "Quantum state is not normalized."
        );
    }
}


Vector normalize(const Vector& state) {
    const double norm = vectorNorm(state);

    if (norm <= EPSILON) {
        throw std::invalid_argument(
            "The zero vector cannot represent a quantum state."
        );
    }

    Vector result = state;

    for (auto& value : result) {
        value /= norm;
    }

    return result;
}


// -----------------------------------------------------------------------------
// Qubit class
// -----------------------------------------------------------------------------

class Qubit {
private:
    Complex alpha_;
    Complex beta_;

public:
    Qubit(
        Complex alpha,
        Complex beta
    )
        : alpha_(alpha),
          beta_(beta) {
        validate();
    }

    const Complex& alpha() const {
        return alpha_;
    }

    const Complex& beta() const {
        return beta_;
    }

    Vector vector() const {
        return {alpha_, beta_};
    }

    double probabilityZero() const {
        return std::norm(alpha_);
    }

    double probabilityOne() const {
        return std::norm(beta_);
    }

    Qubit apply(const Matrix& gate) const {
        const auto [rows, columns] = matrixShape(gate);

        if (rows != 2 || columns != 2) {
            throw std::invalid_argument(
                "A single-qubit gate must be 2x2."
            );
        }

        const Vector transformed =
            matrixVectorMultiply(
                gate,
                vector()
            );

        return Qubit(
            transformed[0],
            transformed[1]
        );
    }

    int measure(
        std::mt19937& generator
    ) {
        std::uniform_real_distribution<double> distribution(
            0.0,
            1.0
        );

        const double randomValue = distribution(generator);

        const int outcome =
            randomValue < probabilityZero()
                ? 0
                : 1;

        if (outcome == 0) {
            alpha_ = Complex(1.0, 0.0);
            beta_ = Complex(0.0, 0.0);
        } else {
            alpha_ = Complex(0.0, 0.0);
            beta_ = Complex(1.0, 0.0);
        }

        return outcome;
    }

private:
    void validate() const {
        validateSingleQubitState(vector());
    }
};


// -----------------------------------------------------------------------------
// Standard gates
// -----------------------------------------------------------------------------

Matrix identityGate() {
    return {
        {Complex(1.0), Complex(0.0)},
        {Complex(0.0), Complex(1.0)}
    };
}


Matrix xGate() {
    return {
        {Complex(0.0), Complex(1.0)},
        {Complex(1.0), Complex(0.0)}
    };
}


Matrix yGate() {
    return {
        {Complex(0.0), Complex(0.0, -1.0)},
        {Complex(0.0, 1.0), Complex(0.0)}
    };
}


Matrix zGate() {
    return {
        {Complex(1.0), Complex(0.0)},
        {Complex(0.0), Complex(-1.0)}
    };
}


const Matrix& gateByName(const std::string& name) {
    static const Matrix identity = identityGate();
    static const Matrix x = xGate();
    static const Matrix y = yGate();
    static const Matrix z = zGate();

    if (name == "I") {
        return identity;
    }

    if (name == "X") {
        return x;
    }

    if (name == "Y") {
        return y;
    }

    if (name == "Z") {
        return z;
    }

    throw std::invalid_argument(
        "Unknown gate: " + name
    );
}


// -----------------------------------------------------------------------------
// Standard states
// -----------------------------------------------------------------------------

Qubit ketZero() {
    return Qubit(
        Complex(1.0),
        Complex(0.0)
    );
}


Qubit ketOne() {
    return Qubit(
        Complex(0.0),
        Complex(1.0)
    );
}


Qubit plusState() {
    return Qubit(
        Complex(1.0 / SQRT_TWO),
        Complex(1.0 / SQRT_TWO)
    );
}


Qubit minusState() {
    return Qubit(
        Complex(1.0 / SQRT_TWO),
        Complex(-1.0 / SQRT_TWO)
    );
}


Qubit plusIState() {
    return Qubit(
        Complex(1.0 / SQRT_TWO),
        Complex(0.0, 1.0 / SQRT_TWO)
    );
}


// -----------------------------------------------------------------------------
// Gate and state analysis
// -----------------------------------------------------------------------------

bool isUnitary(const Matrix& matrix) {
    const auto [rows, columns] = matrixShape(matrix);

    if (rows != columns) {
        return false;
    }

    const Matrix dagger =
        conjugateTranspose(matrix);

    const Matrix product =
        matrixMultiply(dagger, matrix);

    return matricesAreClose(
        product,
        identityMatrix(rows)
    );
}


Matrix composeGates(
    const Matrix& first,
    const Matrix& second
) {
    // first is applied first, second is applied second.
    // Matrix composition is therefore second * first.
    return matrixMultiply(second, first);
}


Complex expectationValue(
    const Qubit& state,
    const Matrix& operatorMatrix
) {
    const Vector transformed =
        matrixVectorMultiply(
            operatorMatrix,
            state.vector()
        );

    const Vector bra = {
        std::conj(state.alpha()),
        std::conj(state.beta())
    };

    Complex result(0.0, 0.0);

    for (std::size_t i = 0; i < bra.size(); ++i) {
        result += bra[i] * transformed[i];
    }

    return result;
}


std::array<double, 3> blochCoordinates(
    const Qubit& state
) {
    const Complex alpha = state.alpha();
    const Complex beta = state.beta();

    const Complex crossTerm =
        std::conj(alpha) * beta;

    const double x =
        2.0 * crossTerm.real();

    const double y =
        2.0 * crossTerm.imag();

    const double z =
        std::norm(alpha) -
        std::norm(beta);

    return {x, y, z};
}


// -----------------------------------------------------------------------------
// Tensor products
// -----------------------------------------------------------------------------

Vector tensorProduct(
    const Vector& left,
    const Vector& right
) {
    Vector result;

    result.reserve(
        left.size() * right.size()
    );

    for (const auto& leftValue : left) {
        for (const auto& rightValue : right) {
            result.push_back(
                leftValue * rightValue
            );
        }
    }

    return result;
}


Matrix tensorProduct(
    const Matrix& left,
    const Matrix& right
) {
    const auto [leftRows, leftColumns] =
        matrixShape(left);

    const auto [rightRows, rightColumns] =
        matrixShape(right);

    Matrix result(
        leftRows * rightRows,
        std::vector<Complex>(
            leftColumns * rightColumns,
            Complex(0.0)
        )
    );

    for (std::size_t i = 0; i < leftRows; ++i) {
        for (std::size_t j = 0; j < leftColumns; ++j) {
            for (std::size_t k = 0; k < rightRows; ++k) {
                for (std::size_t l = 0; l < rightColumns; ++l) {
                    result[
                        i * rightRows + k
                    ][
                        j * rightColumns + l
                    ] =
                        left[i][j] * right[k][l];
                }
            }
        }
    }

    return result;
}


// -----------------------------------------------------------------------------
// Display helpers
// -----------------------------------------------------------------------------

void printComplex(
    const Complex& value
) {
    const double real =
        std::abs(value.real()) < 1e-8
            ? 0.0
            : value.real();

    const double imaginary =
        std::abs(value.imag()) < 1e-8
            ? 0.0
            : value.imag();

    if (imaginary == 0.0) {
        std::cout
            << std::fixed
            << std::setprecision(4)
            << real;
        return;
    }

    if (real == 0.0) {
        std::cout
            << std::fixed
            << std::setprecision(4)
            << imaginary
            << "i";
        return;
    }

    std::cout
        << std::fixed
        << std::setprecision(4)
        << real
        << (imaginary >= 0.0 ? " + " : " - ")
        << std::abs(imaginary)
        << "i";
}


void printState(
    const std::string& label,
    const Qubit& state
) {
    std::cout << label << "\n";
    std::cout << "  alpha = ";
    printComplex(state.alpha());
    std::cout << "\n";

    std::cout << "  beta  = ";
    printComplex(state.beta());
    std::cout << "\n";

    std::cout
        << "  P(0)  = "
        << std::fixed
        << std::setprecision(6)
        << state.probabilityZero()
        << "\n";

    std::cout
        << "  P(1)  = "
        << std::fixed
        << std::setprecision(6)
        << state.probabilityOne()
        << "\n\n";
}


void printMatrix(
    const std::string& name,
    const Matrix& matrix
) {
    std::cout << name << " =\n";

    for (const auto& row : matrix) {
        std::cout << "  ";

        for (const auto& value : row) {
            printComplex(value);
            std::cout << "    ";
        }

        std::cout << "\n";
    }

    std::cout << "\n";
}


void section(
    const std::string& title
) {
    std::cout
        << "\n"
        << std::string(72, '=')
        << "\n"
        << title
        << "\n"
        << std::string(72, '=')
        << "\n";
}


// -----------------------------------------------------------------------------
// Industry-style case study
// -----------------------------------------------------------------------------

/*
 * Scenario:
 *
 * Imagine a quantum sensing controller that must maintain a small software
 * model of a sensor qubit during calibration.
 *
 * The controller receives a sequence such as:
 *
 *     X -> Z -> X
 *
 * and needs to:
 *
 * 1. validate the requested operations,
 * 2. apply the corresponding unitary matrices,
 * 3. retain a normalized state,
 * 4. calculate measurement probabilities,
 * 5. calculate Bloch coordinates,
 * 6. perform a calibration measurement,
 * 7. report the resulting state.
 *
 * This is intentionally a simulator rather than a hardware driver.
 * It demonstrates the software architecture around the mathematical
 * operations without pretending to control physical quantum hardware.
 */

class QuantumControlSession {
private:
    Qubit state_;
    std::vector<std::string> operationLog_;

public:
    explicit QuantumControlSession(
        const Qubit& initialState
    )
        : state_(initialState) {}

    void applyGate(
        const std::string& gateName
    ) {
        const Matrix& gate =
            gateByName(gateName);

        state_ = state_.apply(gate);
        operationLog_.push_back(gateName);
    }

    const Qubit& state() const {
        return state_;
    }

    const std::vector<std::string>& log() const {
        return operationLog_;
    }

    void printReport() const {
        std::cout
            << "Control-session report\n";

        std::cout
            << "Operations: ";

        if (operationLog_.empty()) {
            std::cout << "(none)";
        } else {
            for (std::size_t i = 0;
                 i < operationLog_.size();
                 ++i) {
                if (i > 0) {
                    std::cout << " -> ";
                }

                std::cout
                    << operationLog_[i];
            }
        }

        std::cout << "\n";

        printState(
            "Current quantum state:",
            state_
        );

        const auto coordinates =
            blochCoordinates(state_);

        std::cout
            << "Bloch coordinates: ("
            << coordinates[0]
            << ", "
            << coordinates[1]
            << ", "
            << coordinates[2]
            << ")\n\n";
    }

    int calibrate(
        std::mt19937& generator
    ) {
        return state_.measure(generator);
    }
};


// -----------------------------------------------------------------------------
// Demonstrations
// -----------------------------------------------------------------------------

void demonstrateBasicGates() {
    section("1. BASIC GATE TRANSFORMATIONS");

    printMatrix("I", identityGate());
    printMatrix("X", xGate());
    printMatrix("Y", yGate());
    printMatrix("Z", zGate());

    printState(
        "I|0>:",
        ketZero().apply(identityGate())
    );

    printState(
        "X|0>:",
        ketZero().apply(xGate())
    );

    printState(
        "Y|0>:",
        ketZero().apply(yGate())
    );

    printState(
        "Z|1>:",
        ketOne().apply(zGate())
    );
}


void demonstrateSuperpositionAndPhase() {
    section("2. SUPERPOSITION AND PHASE");

    const Qubit plus = plusState();

    printState("|+>:", plus);

    printState(
        "X|+>:",
        plus.apply(xGate())
    );

    printState(
        "Z|+>:",
        plus.apply(zGate())
    );

    Qubit globalPhase(
        -plus.alpha(),
        -plus.beta()
    );

    printState(
        "-|+>:",
        globalPhase
    );

    std::cout
        << "The global phase changes amplitudes but not "
        << "computational-basis probabilities.\n";
}


void demonstrateGateComposition() {
    section("3. GATE COMPOSITION");

    const Qubit initial = ketZero();

    const Qubit sequential =
        initial
            .apply(xGate())
            .apply(zGate());

    const Matrix combined =
        composeGates(
            xGate(),
            zGate()
        );

    const Qubit matrixResult =
        initial.apply(combined);

    printState(
        "Sequential X then Z:",
        sequential
    );

    printState(
        "Combined matrix:",
        matrixResult
    );

    const Matrix xy =
        composeGates(
            xGate(),
            yGate()
        );

    const Matrix yx =
        composeGates(
            yGate(),
            xGate()
        );

    std::cout
        << "XY equals YX: "
        << std::boolalpha
        << matricesAreClose(xy, yx)
        << "\n";
}


void demonstrateBlochCoordinates() {
    section("4. BLOCH-VECTOR ANALYSIS");

    const std::vector<std::pair<std::string, Qubit>> states = {
        {"|0>", ketZero()},
        {"|1>", ketOne()},
        {"|+>", plusState()},
        {"|->", minusState()},
        {"|+i>", plusIState()}
    };

    for (const auto& [name, state] : states) {
        const auto coordinates =
            blochCoordinates(state);

        std::cout
            << name
            << " -> ("
            << std::fixed
            << std::setprecision(4)
            << coordinates[0]
            << ", "
            << coordinates[1]
            << ", "
            << coordinates[2]
            << ")\n";
    }

    std::cout << "\n";
}


void demonstrateExpectationValues() {
    section("5. EXPECTATION VALUES");

    const std::vector<std::pair<std::string, Qubit>> states = {
        {"|0>", ketZero()},
        {"|1>", ketOne()},
        {"|+>", plusState()},
        {"|->", minusState()},
        {"|+i>", plusIState()}
    };

    for (const auto& [name, state] : states) {
        const Complex x =
            expectationValue(state, xGate());

        const Complex y =
            expectationValue(state, yGate());

        const Complex z =
            expectationValue(state, zGate());

        std::cout
            << name
            << ": <X>="
            << x.real()
            << ", <Y>="
            << y.real()
            << ", <Z>="
            << z.real()
            << "\n";
    }
}


void demonstrateMeasurement() {
    section("6. MEASUREMENT");

    std::mt19937 generator(12345);

    Qubit state = plusState();

    printState(
        "Before measurement:",
        state
    );

    const int outcome =
        state.measure(generator);

    std::cout
        << "Observed outcome: "
        << outcome
        << "\n\n";

    printState(
        "After measurement:",
        state
    );
}


void demonstrateBellState() {
    section("7. TWO-QUBIT BELL STATE");

    const Vector bellState = {
        Complex(1.0 / SQRT_TWO),
        Complex(0.0),
        Complex(0.0),
        Complex(1.0 / SQRT_TWO)
    };

    const std::array<std::string, 4> labels = {
        "|00>",
        "|01>",
        "|10>",
        "|11>"
    };

    for (std::size_t i = 0; i < bellState.size(); ++i) {
        std::cout
            << labels[i]
            << ": amplitude=";

        printComplex(bellState[i]);

        std::cout
            << ", probability="
            << std::norm(bellState[i])
            << "\n";
    }

    std::cout
        << "\nThis state has nonzero amplitude only for |00> "
        << "and |11>.\n";
}


void demonstrateIndustryCaseStudy() {
    section("8. QUANTUM SENSOR CONTROL CASE STUDY");

    QuantumControlSession session(
        plusState()
    );

    /*
     * The sequence models a simple calibration routine.
     *
     * The system starts in a balanced superposition. A sequence of
     * Pauli operations models deterministic control pulses.
     */
    session.applyGate("X");
    session.applyGate("Z");
    session.applyGate("X");
    session.applyGate("I");

    session.printReport();

    std::mt19937 generator(2026);

    const int outcome =
        session.calibrate(generator);

    std::cout
        << "Calibration measurement: "
        << outcome
        << "\n";

    std::cout
        << "After measurement, the state is one of the computational "
        << "basis states.\n\n";
}


// -----------------------------------------------------------------------------
// Automated tests
// -----------------------------------------------------------------------------

void assertComplexClose(
    Complex actual,
    Complex expected
) {
    assert(
        std::abs(actual - expected) <= EPSILON
    );
}


void assertQubitClose(
    const Qubit& actual,
    const Qubit& expected
) {
    assertComplexClose(
        actual.alpha(),
        expected.alpha()
    );

    assertComplexClose(
        actual.beta(),
        expected.beta()
    );
}


void runTests() {
    section("9. AUTOMATED TESTS");

    assertQubitClose(
        ketZero().apply(identityGate()),
        ketZero()
    );

    assertQubitClose(
        ketZero().apply(xGate()),
        ketOne()
    );

    assertQubitClose(
        ketOne().apply(xGate()),
        ketZero()
    );

    assertQubitClose(
        ketZero().apply(yGate()),
        Qubit(
            Complex(0.0),
            Complex(0.0, 1.0)
        )
    );

    assertQubitClose(
        ketOne().apply(yGate()),
        Qubit(
            Complex(0.0, -1.0),
            Complex(0.0)
        )
    );

    assertQubitClose(
        ketOne().apply(zGate()),
        Qubit(
            Complex(0.0),
            Complex(-1.0)
        )
    );

    const std::array<
        std::pair<std::string, Matrix>,
        4
    > gates = {{
        {"I", identityGate()},
        {"X", xGate()},
        {"Y", yGate()},
        {"Z", zGate()}
    }};

    for (const auto& [name, gate] : gates) {
        assert(isUnitary(gate));

        const Matrix square =
            matrixMultiply(gate, gate);

        if (name != "I") {
            assert(
                matricesAreClose(
                    square,
                    identityMatrix(2)
                )
            );
        }
    }

    const Complex plusX =
        expectationValue(
            plusState(),
            xGate()
        );

    assert(
        std::abs(plusX.real() - 1.0)
        <= EPSILON
    );

    const Complex zeroZ =
        expectationValue(
            ketZero(),
            zGate()
        );

    assert(
        std::abs(zeroZ.real() - 1.0)
        <= EPSILON
    );

    std::cout
        << "All C++ quantum-gate tests passed.\n";
}


// -----------------------------------------------------------------------------
// Edge cases
// -----------------------------------------------------------------------------

void demonstrateFailureHandling() {
    section("10. FAILURE CONDITIONS");

    try {
        Qubit invalid(
            Complex(1.0),
            Complex(1.0)
        );

        (void)invalid;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid state rejected: "
            << error.what()
            << "\n";
    }

    try {
        gateByName("H");
    } catch (const std::exception& error) {
        std::cout
            << "Unknown gate rejected: "
            << error.what()
            << "\n";
    }

    try {
        Matrix invalidMatrix = {
            {Complex(1.0)}
        };

        ketZero().apply(invalidMatrix);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid gate size rejected: "
            << error.what()
            << "\n";
    }

    std::cout << "\n";
}


// -----------------------------------------------------------------------------
// Performance experiment
// -----------------------------------------------------------------------------

void benchmark() {
    section("11. PERFORMANCE EXPERIMENT");

    constexpr std::size_t iterations = 100000;

    Qubit state = plusState();

    const auto start =
        std::chrono::high_resolution_clock::now();

    for (std::size_t i = 0;
         i < iterations;
         ++i) {
        state = state.apply(xGate());
    }

    const auto end =
        std::chrono::high_resolution_clock::now();

    const std::chrono::duration<double> elapsed =
        end - start;

    std::cout
        << "Operations: "
        << iterations
        << "\n";

    std::cout
        << "Elapsed time: "
        << elapsed.count()
        << " seconds\n";

    std::cout
        << "Operations per second: "
        << iterations / elapsed.count()
        << "\n\n";

    std::cout
        << "The simulator uses dense vectors and matrices. "
        << "For n qubits, a general state vector contains 2^n "
        << "complex amplitudes, creating exponential memory growth.\n";
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << std::string(72, '#')
            << "\n"
            << "QUANTUM GATES: X, Y, Z, AND IDENTITY\n"
            << std::string(72, '#')
            << "\n";

        demonstrateBasicGates();
        demonstrateSuperpositionAndPhase();
        demonstrateGateComposition();
        demonstrateBlochCoordinates();
        demonstrateExpectationValues();
        demonstrateMeasurement();
        demonstrateBellState();
        demonstrateIndustryCaseStudy();
        runTests();
        demonstrateFailureHandling();
        benchmark();

        std::cout
            << "\nProgram completed successfully.\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
