/*
 * Phase Gates: S, T, and Phase Operations
 * ========================================
 *
 * Modern C++17 case study: a compact quantum-state simulator for studying
 * phase operations in a realistic circuit-processing workflow.
 *
 * The implementation demonstrates:
 * - Complex amplitudes
 * - Quantum state vectors
 * - Matrix representation of gates
 * - P(theta), Z, S, T and inverse gates
 * - Unitary validation
 * - Matrix multiplication
 * - Circuit composition
 * - Controlled phase operations
 * - Measurement
 * - Phase-sensitive interference
 * - Multi-qubit state representation
 * - Input validation
 * - Error handling
 * - Complexity and memory considerations
 *
 * Compile:
 *   g++ -std=c++17 -O2 phase_gates.cpp -o phase_gates
 *
 * Run:
 *   ./phase_gates
 */

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

using Complex = std::complex<double>;
using State = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double PI = 3.1415926535897932384626433832795;
constexpr double EPSILON = 1e-10;


// ============================================================================
// 1. GENERAL MATRIX UTILITIES
// ============================================================================

Matrix identityMatrix(std::size_t size) {
    Matrix result(
        size,
        std::vector<Complex>(size, Complex(0.0, 0.0))
    );

    for (std::size_t i = 0; i < size; ++i) {
        result[i][i] = Complex(1.0, 0.0);
    }

    return result;
}


Matrix matrixMultiply(const Matrix& a, const Matrix& b) {
    if (a.empty() || b.empty()) {
        throw std::invalid_argument(
            "Matrices cannot be empty."
        );
    }

    if (a[0].size() != b.size()) {
        throw std::invalid_argument(
            "Matrix dimensions are incompatible."
        );
    }

    Matrix result(
        a.size(),
        std::vector<Complex>(b[0].size(), Complex(0.0, 0.0))
    );

    for (std::size_t row = 0; row < a.size(); ++row) {
        for (std::size_t column = 0; column < b[0].size(); ++column) {
            for (std::size_t k = 0; k < b.size(); ++k) {
                result[row][column] +=
                    a[row][k] * b[k][column];
            }
        }
    }

    return result;
}


State matrixVectorMultiply(
    const Matrix& matrix,
    const State& vector
) {
    if (matrix.empty()) {
        throw std::invalid_argument(
            "Matrix cannot be empty."
        );
    }

    if (matrix[0].size() != vector.size()) {
        throw std::invalid_argument(
            "Matrix and state dimensions are incompatible."
        );
    }

    State result(
        matrix.size(),
        Complex(0.0, 0.0)
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0; column < vector.size(); ++column) {
            result[row] +=
                matrix[row][column] * vector[column];
        }
    }

    return result;
}


Matrix conjugateTranspose(const Matrix& matrix) {
    if (matrix.empty()) {
        throw std::invalid_argument(
            "Matrix cannot be empty."
        );
    }

    Matrix result(
        matrix[0].size(),
        std::vector<Complex>(
            matrix.size(),
            Complex(0.0, 0.0)
        )
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0; column < matrix[0].size(); ++column) {
            result[column][row] =
                std::conj(matrix[row][column]);
        }
    }

    return result;
}


bool matricesClose(
    const Matrix& a,
    const Matrix& b,
    double tolerance = 1e-9
) {
    if (
        a.size() != b.size() ||
        a.empty() ||
        b.empty() ||
        a[0].size() != b[0].size()
    ) {
        return false;
    }

    for (std::size_t row = 0; row < a.size(); ++row) {
        for (std::size_t column = 0; column < a[0].size(); ++column) {
            if (
                std::abs(
                    a[row][column] - b[row][column]
                ) > tolerance
            ) {
                return false;
            }
        }
    }

    return true;
}


bool isUnitary(
    const Matrix& matrix,
    double tolerance = 1e-9
) {
    if (
        matrix.empty() ||
        matrix.size() != matrix[0].size()
    ) {
        return false;
    }

    Matrix product = matrixMultiply(
        conjugateTranspose(matrix),
        matrix
    );

    return matricesClose(
        product,
        identityMatrix(matrix.size()),
        tolerance
    );
}


// ============================================================================
// 2. QUANTUM STATE UTILITIES
// ============================================================================

double stateNorm(const State& state) {
    double total = 0.0;

    for (const Complex& amplitude : state) {
        total += std::norm(amplitude);
    }

    return std::sqrt(total);
}


void validateState(const State& state) {
    if (state.empty()) {
        throw std::invalid_argument(
            "Quantum state cannot be empty."
        );
    }

    const double norm = stateNorm(state);

    if (std::abs(norm - 1.0) > 1e-9) {
        throw std::invalid_argument(
            "Quantum state is not normalized."
        );
    }
}


State normalizeState(const State& state) {
    const double norm = stateNorm(state);

    if (norm < EPSILON) {
        throw std::invalid_argument(
            "Cannot normalize a zero vector."
        );
    }

    State result = state;

    for (Complex& amplitude : result) {
        amplitude /= norm;
    }

    return result;
}


std::vector<double> probabilities(const State& state) {
    validateState(state);

    std::vector<double> result;

    for (const Complex& amplitude : state) {
        result.push_back(std::norm(amplitude));
    }

    return result;
}


// ============================================================================
// 3. STANDARD SINGLE-QUBIT GATES
// ============================================================================

Matrix XGate() {
    return {
        {Complex(0, 0), Complex(1, 0)},
        {Complex(1, 0), Complex(0, 0)}
    };
}


Matrix YGate() {
    return {
        {Complex(0, 0), Complex(0, -1)},
        {Complex(0, 1), Complex(0, 0)}
    };
}


Matrix ZGate() {
    return {
        {Complex(1, 0), Complex(0, 0)},
        {Complex(0, 0), Complex(-1, 0)}
    };
}


Matrix HGate() {
    const double inverseSqrtTwo =
        1.0 / std::sqrt(2.0);

    return {
        {
            Complex(inverseSqrtTwo, 0),
            Complex(inverseSqrtTwo, 0)
        },
        {
            Complex(inverseSqrtTwo, 0),
            Complex(-inverseSqrtTwo, 0)
        }
    };
}


// ============================================================================
// 4. GENERAL PHASE GATES
// ============================================================================

Matrix phaseGate(double theta) {
    /*
     * P(theta) = diag(1, exp(i theta)).
     *
     * This is the central operation in the case study.
     * It leaves |0> unchanged and changes the phase of |1>.
     */
    return {
        {
            Complex(1, 0),
            Complex(0, 0)
        },
        {
            Complex(0, 0),
            std::exp(Complex(0, theta))
        }
    };
}


Matrix SGate() {
    return phaseGate(PI / 2.0);
}


Matrix TGate() {
    return phaseGate(PI / 4.0);
}


Matrix SDaggerGate() {
    return phaseGate(-PI / 2.0);
}


Matrix TDaggerGate() {
    return phaseGate(-PI / 4.0);
}


// ============================================================================
// 5. CONTROLLED PHASE
// ============================================================================

Matrix controlledPhaseGate(double theta) {
    /*
     * Basis ordering:
     *
     * |00>
     * |01>
     * |10>
     * |11>
     *
     * Only |11> receives exp(i theta).
     */
    return {
        {
            Complex(1, 0), Complex(0, 0),
            Complex(0, 0), Complex(0, 0)
        },
        {
            Complex(0, 0), Complex(1, 0),
            Complex(0, 0), Complex(0, 0)
        },
        {
            Complex(0, 0), Complex(0, 0),
            Complex(1, 0), Complex(0, 0)
        },
        {
            Complex(0, 0), Complex(0, 0),
            Complex(0, 0),
            std::exp(Complex(0, theta))
        }
    };
}


// ============================================================================
// 6. TENSOR PRODUCT
// ============================================================================

State tensorProduct(
    const State& a,
    const State& b
) {
    State result;

    result.reserve(a.size() * b.size());

    for (const Complex& first : a) {
        for (const Complex& second : b) {
            result.push_back(first * second);
        }
    }

    return result;
}


Matrix tensorProduct(
    const Matrix& a,
    const Matrix& b
) {
    Matrix result;

    for (const auto& rowA : a) {
        for (const auto& rowB : b) {
            std::vector<Complex> row;

            row.reserve(
                rowA.size() * rowB.size()
            );

            for (const Complex& valueA : rowA) {
                for (const Complex& valueB : rowB) {
                    row.push_back(
                        valueA * valueB
                    );
                }
            }

            result.push_back(std::move(row));
        }
    }

    return result;
}


// ============================================================================
// 7. MATRIX POWER
// ============================================================================

Matrix matrixPower(
    Matrix base,
    unsigned int exponent
) {
    Matrix result =
        identityMatrix(base.size());

    /*
     * Repeated squaring reduces the number of matrix multiplications
     * required compared with multiplying the same matrix exponent times.
     */
    while (exponent > 0) {
        if (exponent & 1U) {
            result = matrixMultiply(
                result,
                base
            );
        }

        base = matrixMultiply(
            base,
            base
        );

        exponent >>= 1U;
    }

    return result;
}


// ============================================================================
// 8. CIRCUIT ARCHITECTURE
// ============================================================================

struct GateOperation {
    std::string name;
    Matrix matrix;
};


class QuantumCircuit {
private:
    std::vector<GateOperation> operations_;

public:
    void addGate(
        const std::string& name,
        const Matrix& matrix
    ) {
        if (
            matrix.size() != 2 ||
            matrix[0].size() != 2
        ) {
            throw std::invalid_argument(
                "This circuit accepts 2x2 single-qubit gates."
            );
        }

        if (!isUnitary(matrix)) {
            throw std::invalid_argument(
                "A quantum gate must be unitary."
            );
        }

        operations_.push_back({
            name,
            matrix
        });
    }


    void addPhase(double theta) {
        std::ostringstream name;

        name << "P("
             << std::fixed
             << std::setprecision(2)
             << theta * 180.0 / PI
             << " deg)";

        addGate(
            name.str(),
            phaseGate(theta)
        );
    }


    State run(const State& initialState) const {
        State state = initialState;

        validateState(state);

        for (const auto& operation : operations_) {
            state = matrixVectorMultiply(
                operation.matrix,
                state
            );
        }

        return state;
    }


    Matrix combinedMatrix() const {
        Matrix result = identityMatrix(2);

        for (const auto& operation : operations_) {
            result = matrixMultiply(
                operation.matrix,
                result
            );
        }

        return result;
    }


    void printDescription() const {
        std::cout << "\nCircuit operations:\n";

        for (std::size_t i = 0; i < operations_.size(); ++i) {
            std::cout
                << "  "
                << i + 1
                << ". "
                << operations_[i].name
                << '\n';
        }
    }
};


// ============================================================================
// 9. OUTPUT HELPERS
// ============================================================================

void printComplex(
    const Complex& value,
    int precision = 4
) {
    std::cout
        << std::fixed
        << std::setprecision(precision)
        << value.real();

    if (value.imag() >= 0.0) {
        std::cout << " + ";
    } else {
        std::cout << " - ";
    }

    std::cout
        << std::fixed
        << std::setprecision(precision)
        << std::abs(value.imag())
        << "i";
}


void printMatrix(
    const Matrix& matrix,
    const std::string& title
) {
    std::cout << "\n" << title << '\n';

    for (const auto& row : matrix) {
        std::cout << "[ ";

        for (const auto& value : row) {
            printComplex(value);
            std::cout << "  ";
        }

        std::cout << "]\n";
    }
}


void printState(
    const State& state,
    const std::vector<std::string>& labels
) {
    validateState(state);

    const auto probabilityValues =
        probabilities(state);

    for (std::size_t i = 0; i < state.size(); ++i) {
        std::cout
            << std::setw(6)
            << labels[i]
            << ": ";

        printComplex(state[i]);

        std::cout
            << "  P="
            << std::fixed
            << std::setprecision(6)
            << probabilityValues[i]
            << '\n';
    }
}


// ============================================================================
// 10. MEASUREMENT SIMULATION
// ============================================================================

std::vector<std::size_t> measure(
    const State& state,
    std::size_t shots,
    unsigned int seed = 42
) {
    validateState(state);

    if (shots == 0) {
        throw std::invalid_argument(
            "Measurement shots must be positive."
        );
    }

    std::vector<double> probabilityValues =
        probabilities(state);

    std::vector<double> cumulative(
        probabilityValues.size()
    );

    double total = 0.0;

    for (std::size_t i = 0; i < probabilityValues.size(); ++i) {
        total += probabilityValues[i];
        cumulative[i] = total;
    }

    std::vector<std::size_t> counts(
        state.size(),
        0
    );

    std::mt19937 generator(seed);
    std::uniform_real_distribution<double> distribution(
        0.0,
        1.0
    );

    for (std::size_t shot = 0; shot < shots; ++shot) {
        const double randomValue =
            distribution(generator);

        for (std::size_t index = 0;
             index < cumulative.size();
             ++index) {
            if (randomValue < cumulative[index]) {
                ++counts[index];
                break;
            }
        }
    }

    return counts;
}


// ============================================================================
// 11. PHASE ORACLE
// ============================================================================

class TwoQubitPhaseOracle {
private:
    std::vector<double> phases_;

public:
    explicit TwoQubitPhaseOracle(
        std::vector<double> phases
    )
        : phases_(std::move(phases)) {
        if (phases_.size() != 4) {
            throw std::invalid_argument(
                "A two-qubit phase oracle needs four phases."
            );
        }
    }


    Matrix matrix() const {
        Matrix result =
            identityMatrix(4);

        for (std::size_t index = 0;
             index < phases_.size();
             ++index) {
            result[index][index] =
                std::exp(
                    Complex(0, phases_[index])
                );
        }

        return result;
    }


    State apply(const State& state) const {
        return matrixVectorMultiply(
            matrix(),
            state
        );
    }
};


// ============================================================================
// 12. INTERFERENCE EXPERIMENT
// ============================================================================

std::pair<double, double>
phaseInterferenceExperiment(
    double theta
) {
    State state = {
        Complex(1, 0),
        Complex(0, 0)
    };

    state = matrixVectorMultiply(
        HGate(),
        state
    );

    state = matrixVectorMultiply(
        phaseGate(theta),
        state
    );

    state = matrixVectorMultiply(
        HGate(),
        state
    );

    const auto probabilitiesValue =
        probabilities(state);

    return {
        probabilitiesValue[0],
        probabilitiesValue[1]
    };
}


// ============================================================================
// 13. EDUCATIONAL CASE STUDY
// ============================================================================

void caseStudy() {
    std::cout
        << "============================================================\n"
        << "PHASE GATES: S, T, AND PHASE OPERATIONS\n"
        << "============================================================\n";

    std::cout
        << "\nCASE STUDY:\n"
        << "A quantum signal-processing pipeline receives a qubit, applies\n"
        << "a Hadamard preparation, performs programmable phase rotations,\n"
        << "and converts the accumulated phase into measurement statistics.\n";

    // ------------------------------------------------------------------------
    // Stage 1: Validate foundational gates.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 1: Gate validation\n";

    std::cout
        << "H unitary: "
        << std::boolalpha
        << isUnitary(HGate())
        << '\n';

    std::cout
        << "Z unitary: "
        << isUnitary(ZGate())
        << '\n';

    std::cout
        << "S unitary: "
        << isUnitary(SGate())
        << '\n';

    std::cout
        << "T unitary: "
        << isUnitary(TGate())
        << '\n';

    // ------------------------------------------------------------------------
    // Stage 2: Show S and T powers.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 2: Phase-gate algebra\n";

    const Matrix sSquared =
        matrixPower(SGate(), 2);

    const Matrix tSquared =
        matrixPower(TGate(), 2);

    const Matrix tFourth =
        matrixPower(TGate(), 4);

    const Matrix tEighth =
        matrixPower(TGate(), 8);

    std::cout
        << "S^2 = Z: "
        << matricesClose(sSquared, ZGate())
        << '\n';

    std::cout
        << "T^2 = S: "
        << matricesClose(tSquared, SGate())
        << '\n';

    std::cout
        << "T^4 = Z: "
        << matricesClose(tFourth, ZGate())
        << '\n';

    std::cout
        << "T^8 = I: "
        << matricesClose(
            tEighth,
            identityMatrix(2)
        )
        << '\n';

    // ------------------------------------------------------------------------
    // Stage 3: Prepare a superposition.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 3: Prepare |+>\n";

    State zero = {
        Complex(1, 0),
        Complex(0, 0)
    };

    State plus =
        matrixVectorMultiply(
            HGate(),
            zero
        );

    printState(
        plus,
        {"|0>", "|1>"}
    );

    // ------------------------------------------------------------------------
    // Stage 4: Apply T and observe that probabilities do not immediately
    // change even though the state has changed.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 4: Apply T\n";

    State phaseShifted =
        matrixVectorMultiply(
            TGate(),
            plus
        );

    printState(
        phaseShifted,
        {"|0>", "|1>"}
    );

    // ------------------------------------------------------------------------
    // Stage 5: Use another Hadamard to expose the phase through interference.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 5: Convert phase into probability\n";

    State interfered =
        matrixVectorMultiply(
            HGate(),
            phaseShifted
        );

    printState(
        interfered,
        {"|0>", "|1>"}
    );

    // ------------------------------------------------------------------------
    // Stage 6: Build a realistic programmable circuit.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 6: Build programmable circuit\n";

    QuantumCircuit circuit;

    circuit.addGate(
        "H",
        HGate()
    );

    circuit.addGate(
        "T",
        TGate()
    );

    circuit.addPhase(
        PI / 3.0
    );

    circuit.addGate(
        "S-dagger",
        SDaggerGate()
    );

    circuit.addGate(
        "H",
        HGate()
    );

    circuit.printDescription();

    State circuitResult =
        circuit.run(zero);

    std::cout
        << "\nCircuit result:\n";

    printState(
        circuitResult,
        {"|0>", "|1>"}
    );

    printMatrix(
        circuit.combinedMatrix(),
        "Combined circuit matrix"
    );

    std::cout
        << "Combined matrix is unitary: "
        << isUnitary(
            circuit.combinedMatrix()
        )
        << '\n';

    // ------------------------------------------------------------------------
    // Stage 7: Controlled phase.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 7: Controlled phase\n";

    State basis11 = {
        Complex(0, 0),
        Complex(0, 0),
        Complex(0, 0),
        Complex(1, 0)
    };

    State controlledResult =
        matrixVectorMultiply(
            controlledPhaseGate(PI / 4.0),
            basis11
        );

    printState(
        controlledResult,
        {"|00>", "|01>", "|10>", "|11>"}
    );

    // ------------------------------------------------------------------------
    // Stage 8: Phase oracle.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 8: Two-qubit phase oracle\n";

    TwoQubitPhaseOracle oracle({
        0.0,
        PI / 4.0,
        PI / 2.0,
        PI
    });

    printMatrix(
        oracle.matrix(),
        "Oracle matrix"
    );

    State uniform({
        Complex(0.5, 0),
        Complex(0.5, 0),
        Complex(0.5, 0),
        Complex(0.5, 0)
    });

    State oracleResult =
        oracle.apply(uniform);

    printState(
        oracleResult,
        {"|00>", "|01>", "|10>", "|11>"}
    );

    // ------------------------------------------------------------------------
    // Stage 9: Measurement.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 9: Measurement simulation\n";

    const auto counts =
        measure(
            interfered,
            5000,
            1234
        );

    std::cout
        << "After 5000 shots:\n";

    for (std::size_t index = 0;
         index < counts.size();
         ++index) {
        std::cout
            << "  |"
            << index
            << ">: "
            << counts[index]
            << '\n';
    }

    // ------------------------------------------------------------------------
    // Stage 10: Parameter sweep.
    // ------------------------------------------------------------------------

    std::cout
        << "\nStage 10: Phase sweep\n";

    for (int degrees :
         {0, 45, 90, 135, 180, 270, 360}) {
        const double theta =
            degrees * PI / 180.0;

        const auto [pZero, pOne] =
            phaseInterferenceExperiment(
                theta
            );

        std::cout
            << std::setw(3)
            << degrees
            << " deg: "
            << "P(0)="
            << std::fixed
            << std::setprecision(4)
            << pZero
            << ", P(1)="
            << pOne
            << '\n';
    }
}


// ============================================================================
// 14. SELF-TESTS
// ============================================================================

void require(
    bool condition,
    const std::string& message
) {
    if (!condition) {
        throw std::runtime_error(
            "Self-test failed: " + message
        );
    }
}


void selfTests() {
    require(
        isUnitary(HGate()),
        "H must be unitary."
    );

    require(
        isUnitary(ZGate()),
        "Z must be unitary."
    );

    require(
        isUnitary(SGate()),
        "S must be unitary."
    );

    require(
        isUnitary(TGate()),
        "T must be unitary."
    );

    require(
        matricesClose(
            matrixPower(SGate(), 2),
            ZGate()
        ),
        "S^2 = Z"
    );

    require(
        matricesClose(
            matrixPower(TGate(), 2),
            SGate()
        ),
        "T^2 = S"
    );

    require(
        matricesClose(
            matrixPower(TGate(), 4),
            ZGate()
        ),
        "T^4 = Z"
    );

    require(
        matricesClose(
            matrixPower(TGate(), 8),
            identityMatrix(2)
        ),
        "T^8 = I"
    );

    require(
        matricesClose(
            matrixMultiply(
                SGate(),
                SDaggerGate()
            ),
            identityMatrix(2)
        ),
        "S S-dagger = I"
    );

    require(
        matricesClose(
            matrixMultiply(
                TGate(),
                TDaggerGate()
            ),
            identityMatrix(2)
        ),
        "T T-dagger = I"
    );

    const auto [pZero, pOne] =
        phaseInterferenceExperiment(PI);

    require(
        std::abs(pZero) < 1e-9 &&
        std::abs(pOne - 1.0) < 1e-9,
        "A phase of pi must produce complete interference reversal."
    );

    require(
        isUnitary(
            controlledPhaseGate(PI / 4.0)
        ),
        "Controlled phase must be unitary."
    );

    std::cout
        << "\nAll C++ self-tests passed.\n";
}


// ============================================================================
// 15. COMPLEXITY REPORT
// ============================================================================

void printComplexityReport() {
    std::cout
        << "\n============================================================\n"
        << "COMPLEXITY AND MEMORY REPORT\n"
        << "============================================================\n";

    std::cout
        << "For n qubits, a state vector contains 2^n amplitudes.\n"
        << "A dense full-system matrix contains 4^n complex values.\n"
        << "Naive dense matrix-vector multiplication is O(4^n).\n"
        << "Specialized local-gate simulation can avoid constructing\n"
        << "the complete dense matrix and is substantially cheaper.\n\n";

    for (int qubits = 1; qubits <= 12; ++qubits) {
        const std::size_t amplitudes =
            static_cast<std::size_t>(1ULL << qubits);

        std::cout
            << std::setw(2)
            << qubits
            << " qubits -> "
            << std::setw(5)
            << amplitudes
            << " amplitudes\n";
    }
}


// ============================================================================
// 16. MAIN
// ============================================================================

int main() {
    try {
        caseStudy();
        selfTests();
        printComplexityReport();

        std::cout
            << "\n============================================================\n"
            << "END OF C++ PHASE-GATE CASE STUDY\n"
            << "============================================================\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "ERROR: "
            << error.what()
            << '\n';

        return 1;
    }
}
