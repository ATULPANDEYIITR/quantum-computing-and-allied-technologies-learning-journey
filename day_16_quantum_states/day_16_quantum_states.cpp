/*
 * Quantum States: State Vectors and Notation
 * ===========================================
 *
 * C++17 case study:
 *
 * A small quantum-state analysis engine for a two-qubit communication
 * scenario. The implementation begins with complex amplitudes and state
 * vectors and develops into:
 *
 * - normalized quantum states
 * - Dirac notation
 * - inner and outer products
 * - unitary operators
 * - single-qubit gates
 * - tensor products
 * - computational-basis measurement
 * - partial measurement
 * - product-state testing
 * - Bell-state entanglement
 * - expectation values
 * - density matrices
 * - pure-state fidelity
 * - basis changes
 *
 * The standard library is sufficient.
 *
 * Compile:
 *     g++ -std=c++17 -O2 quantum_states.cpp -o quantum_states
 *
 * Run:
 *     ./quantum_states
 */

#include <algorithm>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Complex = std::complex<double>;
using Vector = std::vector<Complex>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double EPSILON = 1e-10;


// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

std::string formatComplex(Complex value, int precision = 5) {
    if (std::abs(value.real()) < EPSILON) {
        value.real(0.0);
    }

    if (std::abs(value.imag()) < EPSILON) {
        value.imag(0.0);
    }

    std::ostringstream output;
    output << std::fixed << std::setprecision(precision);

    if (std::abs(value.imag()) < EPSILON) {
        output << value.real();
        return output.str();
    }

    if (std::abs(value.real()) < EPSILON) {
        output << value.imag() << "i";
        return output.str();
    }

    output << value.real();

    if (value.imag() >= 0.0) {
        output << "+";
    }

    output << value.imag() << "i";
    return output.str();
}


std::string basisLabel(std::size_t index, std::size_t qubits) {
    std::string label(qubits, '0');

    for (std::size_t bit = 0; bit < qubits; ++bit) {
        std::size_t position = qubits - 1 - bit;

        if (index & (static_cast<std::size_t>(1) << bit)) {
            label[position] = '1';
        }
    }

    return label;
}


bool approximatelyEqual(
    double first,
    double second,
    double tolerance = 1e-9
) {
    return std::abs(first - second) <= tolerance;
}


bool approximatelyEqual(
    Complex first,
    Complex second,
    double tolerance = 1e-9
) {
    return std::abs(first - second) <= tolerance;
}


// ---------------------------------------------------------------------------
// Vector operations
// ---------------------------------------------------------------------------

double normSquared(const Vector& vector) {
    double result = 0.0;

    for (const Complex& value : vector) {
        result += std::norm(value);
    }

    return result;
}


double norm(const Vector& vector) {
    return std::sqrt(normSquared(vector));
}


Vector normalize(Vector vector) {
    const double vectorNorm = norm(vector);

    if (vectorNorm < EPSILON) {
        throw std::invalid_argument(
            "The zero vector cannot represent a quantum state."
        );
    }

    for (Complex& value : vector) {
        value /= vectorNorm;
    }

    return vector;
}


/*
 * The inner product uses conjugation on the first vector:
 *
 *     <a|b> = sum_i conjugate(a_i) b_i
 *
 * Omitting conjugation is a common error when amplitudes are complex.
 */
Complex innerProduct(
    const Vector& bra,
    const Vector& ket
) {
    if (bra.size() != ket.size()) {
        throw std::invalid_argument(
            "Inner-product vectors must have equal dimensions."
        );
    }

    Complex result = 0.0;

    for (std::size_t i = 0; i < bra.size(); ++i) {
        result += std::conj(bra[i]) * ket[i];
    }

    return result;
}


Vector vectorAdd(
    const Vector& first,
    const Vector& second
) {
    if (first.size() != second.size()) {
        throw std::invalid_argument(
            "Vector dimensions do not match."
        );
    }

    Vector result(first.size());

    for (std::size_t i = 0; i < first.size(); ++i) {
        result[i] = first[i] + second[i];
    }

    return result;
}


Vector vectorScale(
    const Vector& vector,
    Complex scalar
) {
    Vector result = vector;

    for (Complex& value : result) {
        value *= scalar;
    }

    return result;
}


// ---------------------------------------------------------------------------
// Matrix operations
// ---------------------------------------------------------------------------

bool isRectangular(const Matrix& matrix) {
    if (matrix.empty()) {
        return false;
    }

    const std::size_t columns = matrix.front().size();

    return std::all_of(
        matrix.begin(),
        matrix.end(),
        [columns](const auto& row) {
            return row.size() == columns;
        }
    );
}


Matrix matrixMultiply(
    const Matrix& first,
    const Matrix& second
) {
    if (!isRectangular(first) || !isRectangular(second)) {
        throw std::invalid_argument(
            "Matrices must be non-empty and rectangular."
        );
    }

    const std::size_t firstColumns = first.front().size();
    const std::size_t secondColumns = second.front().size();

    if (firstColumns != second.size()) {
        throw std::invalid_argument(
            "Matrix dimensions are incompatible."
        );
    }

    Matrix result(
        first.size(),
        std::vector<Complex>(secondColumns, Complex(0.0))
    );

    for (std::size_t row = 0; row < first.size(); ++row) {
        for (std::size_t column = 0; column < secondColumns; ++column) {
            for (std::size_t k = 0; k < firstColumns; ++k) {
                result[row][column] +=
                    first[row][k] * second[k][column];
            }
        }
    }

    return result;
}


Vector matrixVectorMultiply(
    const Matrix& matrix,
    const Vector& vector
) {
    if (!isRectangular(matrix)) {
        throw std::invalid_argument(
            "Matrix must be non-empty and rectangular."
        );
    }

    if (matrix.front().size() != vector.size()) {
        throw std::invalid_argument(
            "Matrix and vector dimensions are incompatible."
        );
    }

    Vector result(
        matrix.size(),
        Complex(0.0)
    );

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0;
             column < vector.size();
             ++column) {
            result[row] +=
                matrix[row][column] * vector[column];
        }
    }

    return result;
}


Matrix adjoint(const Matrix& matrix) {
    if (!isRectangular(matrix)) {
        throw std::invalid_argument(
            "Matrix must be non-empty and rectangular."
        );
    }

    const std::size_t rows = matrix.size();
    const std::size_t columns = matrix.front().size();

    Matrix result(
        columns,
        std::vector<Complex>(rows)
    );

    for (std::size_t row = 0; row < rows; ++row) {
        for (std::size_t column = 0;
             column < columns;
             ++column) {
            result[column][row] =
                std::conj(matrix[row][column]);
        }
    }

    return result;
}


Matrix outerProduct(
    const Vector& ket,
    const Vector& bra
) {
    Matrix result(
        ket.size(),
        std::vector<Complex>(bra.size())
    );

    for (std::size_t row = 0; row < ket.size(); ++row) {
        for (std::size_t column = 0;
             column < bra.size();
             ++column) {
            result[row][column] =
                ket[row] * std::conj(bra[column]);
        }
    }

    return result;
}


Complex trace(const Matrix& matrix) {
    if (!isRectangular(matrix) ||
        matrix.size() != matrix.front().size()) {
        throw std::invalid_argument(
            "Trace requires a square matrix."
        );
    }

    Complex result = 0.0;

    for (std::size_t i = 0; i < matrix.size(); ++i) {
        result += matrix[i][i];
    }

    return result;
}


bool isIdentity(
    const Matrix& matrix,
    double tolerance = 1e-9
) {
    if (!isRectangular(matrix) ||
        matrix.size() != matrix.front().size()) {
        return false;
    }

    for (std::size_t row = 0; row < matrix.size(); ++row) {
        for (std::size_t column = 0;
             column < matrix.size();
             ++column) {
            const Complex expected =
                row == column ? Complex(1.0) : Complex(0.0);

            if (!approximatelyEqual(
                    matrix[row][column],
                    expected,
                    tolerance)) {
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
    if (!isRectangular(matrix) ||
        matrix.size() != matrix.front().size()) {
        return false;
    }

    Matrix product =
        matrixMultiply(adjoint(matrix), matrix);

    return isIdentity(product, tolerance);
}


// ---------------------------------------------------------------------------
// Tensor products
// ---------------------------------------------------------------------------

Vector tensorProduct(
    const Vector& first,
    const Vector& second
) {
    Vector result;
    result.reserve(first.size() * second.size());

    /*
     * Basis ordering:
     *
     * |00>, |01>, |10>, |11>
     *
     * for two qubits.
     */
    for (const Complex& left : first) {
        for (const Complex& right : second) {
            result.push_back(left * right);
        }
    }

    return result;
}


Matrix tensorProduct(
    const Matrix& first,
    const Matrix& second
) {
    if (!isRectangular(first) ||
        !isRectangular(second)) {
        throw std::invalid_argument(
            "Tensor-product matrices must be rectangular."
        );
    }

    const std::size_t firstRows = first.size();
    const std::size_t firstColumns = first.front().size();
    const std::size_t secondRows = second.size();
    const std::size_t secondColumns = second.front().size();

    Matrix result(
        firstRows * secondRows,
        std::vector<Complex>(
            firstColumns * secondColumns,
            Complex(0.0)
        )
    );

    for (std::size_t i = 0; i < firstRows; ++i) {
        for (std::size_t j = 0; j < firstColumns; ++j) {
            for (std::size_t k = 0; k < secondRows; ++k) {
                for (std::size_t l = 0; l < secondColumns; ++l) {
                    result[
                        i * secondRows + k
                    ][
                        j * secondColumns + l
                    ] =
                        first[i][j] * second[k][l];
                }
            }
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// Quantum state abstraction
// ---------------------------------------------------------------------------

class QuantumState {
private:
    Vector amplitudes_;

public:
    explicit QuantumState(Vector amplitudes)
        : amplitudes_(normalize(std::move(amplitudes))) {

        const std::size_t dimension = amplitudes_.size();

        /*
         * A register of n qubits has exactly 2^n basis states.
         */
        if ((dimension & (dimension - 1)) != 0) {
            throw std::invalid_argument(
                "Quantum-state dimension must be a power of two."
            );
        }
    }

    const Vector& amplitudes() const {
        return amplitudes_;
    }

    std::size_t dimension() const {
        return amplitudes_.size();
    }

    std::size_t qubitCount() const {
        std::size_t qubits = 0;
        std::size_t dimension = amplitudes_.size();

        while (dimension > 1) {
            dimension /= 2;
            ++qubits;
        }

        return qubits;
    }

    double probability(std::size_t index) const {
        if (index >= dimension()) {
            throw std::out_of_range(
                "Measurement basis index is outside the state."
            );
        }

        return std::norm(amplitudes_[index]);
    }

    std::vector<double> probabilities() const {
        std::vector<double> result;

        for (const Complex& amplitude : amplitudes_) {
            result.push_back(std::norm(amplitude));
        }

        return result;
    }

    QuantumState apply(const Matrix& operatorMatrix) const {
        if (
            operatorMatrix.size() != dimension() ||
            !isRectangular(operatorMatrix) ||
            operatorMatrix.front().size() != dimension()
        ) {
            throw std::invalid_argument(
                "Operator dimension does not match state."
            );
        }

        Vector result =
            matrixVectorMultiply(
                operatorMatrix,
                amplitudes_
            );

        return QuantumState(std::move(result));
    }

    std::string ket() const {
        std::ostringstream output;
        bool firstTerm = true;

        for (std::size_t index = 0;
             index < amplitudes_.size();
             ++index) {

            if (std::abs(amplitudes_[index]) < EPSILON) {
                continue;
            }

            if (!firstTerm) {
                output << " + ";
            }

            output
                << "("
                << formatComplex(amplitudes_[index])
                << ")|"
                << basisLabel(index, qubitCount())
                << ">";

            firstTerm = false;
        }

        return firstTerm ? "0" : output.str();
    }
};


// ---------------------------------------------------------------------------
// Standard one-qubit operators
// ---------------------------------------------------------------------------

const Matrix I = {
    {Complex(1), Complex(0)},
    {Complex(0), Complex(1)}
};

const Matrix X = {
    {Complex(0), Complex(1)},
    {Complex(1), Complex(0)}
};

const Matrix Y = {
    {Complex(0), Complex(0, -1)},
    {Complex(0, 1), Complex(0)}
};

const Matrix Z = {
    {Complex(1), Complex(0)},
    {Complex(0), Complex(-1)}
};

const Matrix H = {
    {
        Complex(1.0 / std::sqrt(2.0)),
        Complex(1.0 / std::sqrt(2.0))
    },
    {
        Complex(1.0 / std::sqrt(2.0)),
        Complex(-1.0 / std::sqrt(2.0))
    }
};


// ---------------------------------------------------------------------------
// Quantum observables
// ---------------------------------------------------------------------------

Complex expectationValue(
    const QuantumState& state,
    const Matrix& observable
) {
    Vector transformed =
        matrixVectorMultiply(
            observable,
            state.amplitudes()
        );

    return innerProduct(
        state.amplitudes(),
        transformed
    );
}


double variance(
    const QuantumState& state,
    const Matrix& observable
) {
    Complex mean =
        expectationValue(state, observable);

    Matrix squared =
        matrixMultiply(observable, observable);

    Complex secondMoment =
        expectationValue(state, squared);

    const double result =
        (secondMoment - mean * mean).real();

    return std::max(0.0, result);
}


// ---------------------------------------------------------------------------
// Measurement engine
// ---------------------------------------------------------------------------

std::size_t sampleMeasurement(
    const QuantumState& state,
    std::mt19937& generator
) {
    const std::vector<double> probabilities =
        state.probabilities();

    std::uniform_real_distribution<double> distribution(
        0.0,
        1.0
    );

    const double target = distribution(generator);

    double cumulative = 0.0;

    for (std::size_t index = 0;
         index < probabilities.size();
         ++index) {

        cumulative += probabilities[index];

        if (target < cumulative) {
            return index;
        }
    }

    /*
     * Floating-point round-off can theoretically leave target just above
     * the final cumulative value. Returning the final valid outcome keeps
     * the simulation total.
     */
    return probabilities.size() - 1;
}


std::vector<std::size_t> repeatedMeasurements(
    const QuantumState& state,
    std::size_t trials,
    unsigned seed
) {
    if (trials == 0) {
        throw std::invalid_argument(
            "Number of measurement trials must be positive."
        );
    }

    std::mt19937 generator(seed);

    std::vector<std::size_t> counts(
        state.dimension(),
        0
    );

    for (std::size_t trial = 0;
         trial < trials;
         ++trial) {

        ++counts[
            sampleMeasurement(state, generator)
        ];
    }

    return counts;
}


// ---------------------------------------------------------------------------
// Partial measurement
// ---------------------------------------------------------------------------

double firstQubitProbability(
    const QuantumState& state,
    int measuredValue
) {
    if (state.dimension() != 4) {
        throw std::invalid_argument(
            "This demonstration expects exactly two qubits."
        );
    }

    if (measuredValue != 0 &&
        measuredValue != 1) {
        throw std::invalid_argument(
            "Measured qubit value must be zero or one."
        );
    }

    /*
     * Basis ordering:
     *
     * index 0 = |00>
     * index 1 = |01>
     * index 2 = |10>
     * index 3 = |11>
     *
     * Therefore:
     * first qubit = 0 -> indices 0 and 1
     * first qubit = 1 -> indices 2 and 3
     */
    const std::size_t start =
        measuredValue == 0 ? 0 : 2;

    return state.probability(start) +
           state.probability(start + 1);
}


// ---------------------------------------------------------------------------
// Pure-state fidelity
// ---------------------------------------------------------------------------

double pureStateFidelity(
    const QuantumState& first,
    const QuantumState& second
) {
    if (first.dimension() != second.dimension()) {
        throw std::invalid_argument(
            "Fidelity requires equal-dimensional states."
        );
    }

    return std::norm(
        innerProduct(
            first.amplitudes(),
            second.amplitudes()
        )
    );
}


// ---------------------------------------------------------------------------
// Product-state test for two qubits
// ---------------------------------------------------------------------------

bool isProductTwoQubitState(
    const QuantumState& state,
    double tolerance = 1e-9
) {
    if (state.dimension() != 4) {
        throw std::invalid_argument(
            "Two-qubit separability test requires dimension four."
        );
    }

    const Vector& a = state.amplitudes();

    /*
     * Write the state as:
     *
     * a00|00> + a01|01> + a10|10> + a11|11>
     *
     * It is separable if the coefficient matrix
     *
     *     [a00 a01]
     *     [a10 a11]
     *
     * has rank one.
     *
     * For a 2x2 matrix this means:
     *
     *     a00*a11 - a01*a10 = 0.
     */
    Complex determinant =
        a[0] * a[3] -
        a[1] * a[2];

    return std::abs(determinant) <= tolerance;
}


// ---------------------------------------------------------------------------
// Density matrices
// ---------------------------------------------------------------------------

Matrix densityMatrix(const QuantumState& state) {
    return outerProduct(
        state.amplitudes(),
        state.amplitudes()
    );
}


double purity(const Matrix& density) {
    Matrix squared =
        matrixMultiply(density, density);

    return trace(squared).real();
}


// ---------------------------------------------------------------------------
// Basis transformation
// ---------------------------------------------------------------------------

Vector coordinatesInBasis(
    const QuantumState& state,
    const Matrix& basis
) {
    if (
        basis.size() != state.dimension() ||
        !isRectangular(basis) ||
        basis.front().size() != state.dimension()
    ) {
        throw std::invalid_argument(
            "Basis dimension does not match state."
        );
    }

    /*
     * If the columns of U are the new basis vectors,
     * then the new coordinate vector is:
     *
     *     U† |psi>
     */
    return matrixVectorMultiply(
        adjoint(basis),
        state.amplitudes()
    );
}


// ---------------------------------------------------------------------------
// Output helpers
// ---------------------------------------------------------------------------

void printProbabilities(
    const QuantumState& state
) {
    const auto probabilities =
        state.probabilities();

    for (std::size_t index = 0;
         index < probabilities.size();
         ++index) {

        std::cout
            << "  P(|"
            << basisLabel(index, state.qubitCount())
            << ">) = "
            << std::fixed
            << std::setprecision(6)
            << probabilities[index]
            << '\n';
    }
}


void printMatrix(
    const Matrix& matrix,
    const std::string& title
) {
    std::cout << title << '\n';

    for (const auto& row : matrix) {
        std::cout << "  [ ";

        for (const Complex& value : row) {
            std::cout
                << std::setw(18)
                << formatComplex(value)
                << " ";
        }

        std::cout << "]\n";
    }
}


// ---------------------------------------------------------------------------
// Main industry-style case study
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "QUANTUM STATE VECTOR CASE STUDY\n"
            << "============================================================\n\n";

        /*
         * Scenario
         * --------
         *
         * We model the state of a small quantum communication register.
         * The register begins in |00>, is transformed using unitary
         * operations, and is later measured.
         *
         * The example is deliberately small because a general n-qubit
         * state vector contains 2^n complex amplitudes.
         */

        std::cout << "1. Initialize a two-qubit register\n";
        std::cout << "-----------------------------------\n";

        QuantumState zero(
            {Complex(1), Complex(0)}
        );

        QuantumState one(
            {Complex(0), Complex(1)}
        );

        QuantumState initialRegister(
            tensorProduct(
                zero.amplitudes(),
                zero.amplitudes()
            )
        );

        std::cout
            << "Initial state: "
            << initialRegister.ket()
            << '\n';

        std::cout
            << "Dimension: "
            << initialRegister.dimension()
            << '\n';

        std::cout
            << "Qubits: "
            << initialRegister.qubitCount()
            << "\n\n";


        /*
         * Stage 2: Create a product superposition.
         *
         * H|0> = (|0> + |1>) / sqrt(2)
         *
         * Applying H independently to two qubits gives:
         *
         * |++> =
         * 1/2 |00> + 1/2 |01> + 1/2 |10> + 1/2 |11>
         */
        std::cout
            << "2. Create a two-qubit product superposition\n"
            << "---------------------------------------------\n";

        QuantumState plus(
            {Complex(1), Complex(1)}
        );

        QuantumState productState(
            tensorProduct(
                plus.amplitudes(),
                plus.amplitudes()
            )
        );

        std::cout
            << "Product state: "
            << productState.ket()
            << '\n';

        printProbabilities(productState);


        /*
         * Stage 3: Construct a Bell state.
         *
         * The Bell state
         *
         *     |Phi+> = (|00> + |11>) / sqrt(2)
         *
         * is entangled because it cannot be represented as
         * |a> tensor |b>.
         */
        std::cout
            << "\n3. Construct an entangled Bell state\n"
            << "-------------------------------------\n";

        QuantumState bellState(
            {
                Complex(1.0 / std::sqrt(2.0)),
                Complex(0),
                Complex(0),
                Complex(1.0 / std::sqrt(2.0))
            }
        );

        std::cout
            << "Bell state: "
            << bellState.ket()
            << '\n';

        printProbabilities(bellState);

        std::cout
            << "Product state? "
            << (isProductTwoQubitState(bellState)
                ? "yes"
                : "no")
            << '\n';


        /*
         * Stage 4: Partial measurement.
         *
         * Measuring only the first qubit of |Phi+> gives:
         *
         * P(first = 0) = 1/2
         * P(first = 1) = 1/2
         */
        std::cout
            << "\n4. Partial measurement\n"
            << "----------------------\n";

        const double firstZero =
            firstQubitProbability(bellState, 0);

        const double firstOne =
            firstQubitProbability(bellState, 1);

        std::cout
            << "P(first qubit = 0): "
            << firstZero
            << '\n';

        std::cout
            << "P(first qubit = 1): "
            << firstOne
            << '\n';


        /*
         * Stage 5: Repeated measurement.
         *
         * Individual outcomes are probabilistic. Repeated experiments
         * approach the Born-rule probabilities.
         */
        std::cout
            << "\n5. Simulate repeated measurements\n"
            << "---------------------------------\n";

        constexpr std::size_t trials = 10000;

        const auto counts =
            repeatedMeasurements(
                bellState,
                trials,
                42
            );

        for (std::size_t index = 0;
             index < counts.size();
             ++index) {

            const double frequency =
                static_cast<double>(counts[index]) /
                static_cast<double>(trials);

            std::cout
                << "|"
                << basisLabel(
                    index,
                    bellState.qubitCount()
                )
                << ">: "
                << counts[index]
                << " observations, frequency = "
                << std::fixed
                << std::setprecision(4)
                << frequency
                << '\n';
        }


        /*
         * Stage 6: Operators.
         *
         * For a single qubit:
         *
         * X|0> = |1>
         * X|1> = |0>
         *
         * H transforms computational basis states into superpositions.
         */
        std::cout
            << "\n6. Apply single-qubit operators\n"
            << "--------------------------------\n";

        QuantumState flipped =
            zero.apply(X);

        QuantumState hadamardState =
            zero.apply(H);

        std::cout
            << "X|0> = "
            << flipped.ket()
            << '\n';

        std::cout
            << "H|0> = "
            << hadamardState.ket()
            << '\n';


        /*
         * Stage 7: Expectation values.
         *
         * For an observable A:
         *
         *     <A> = <psi|A|psi>
         *
         * The result is real for a Hermitian observable, apart from
         * numerical round-off.
         */
        std::cout
            << "\n7. Observable expectation values\n"
            << "---------------------------------\n";

        std::cout
            << "<+|X|+> = "
            << formatComplex(
                expectationValue(plus, X)
            )
            << '\n';

        std::cout
            << "<+|Y|+> = "
            << formatComplex(
                expectationValue(plus, Y)
            )
            << '\n';

        std::cout
            << "<+|Z|+> = "
            << formatComplex(
                expectationValue(plus, Z)
            )
            << '\n';

        std::cout
            << "Var(X) for |+> = "
            << variance(plus, X)
            << '\n';

        std::cout
            << "Var(Z) for |+> = "
            << variance(plus, Z)
            << '\n';


        /*
         * Stage 8: Unitarity.
         *
         * Closed-system quantum evolution is represented by unitary
         * operators. If U is unitary:
         *
         *     U†U = I
         *
         * and state normalization is preserved.
         */
        std::cout
            << "\n8. Validate quantum evolution operators\n"
            << "-----------------------------------------\n";

        std::cout
            << "X unitary: "
            << (isUnitary(X) ? "true" : "false")
            << '\n';

        std::cout
            << "Y unitary: "
            << (isUnitary(Y) ? "true" : "false")
            << '\n';

        std::cout
            << "Z unitary: "
            << (isUnitary(Z) ? "true" : "false")
            << '\n';

        std::cout
            << "H unitary: "
            << (isUnitary(H) ? "true" : "false")
            << '\n';


        /*
         * Stage 9: Basis change.
         *
         * The same physical state can have different coordinates in
         * different bases.
         *
         * The columns of H are the X-basis vectors |+> and |->.
         */
        std::cout
            << "\n9. Express a state in a different basis\n"
            << "-----------------------------------------\n";

        const Vector xCoordinates =
            coordinatesInBasis(
                zero,
                H
            );

        std::cout
            << "Coordinates of |0> in X basis:\n";

        for (std::size_t i = 0;
             i < xCoordinates.size();
             ++i) {

            std::cout
                << "  coordinate "
                << i
                << " = "
                << formatComplex(
                    xCoordinates[i]
                )
                << '\n';
        }


        /*
         * Stage 10: Density matrix.
         *
         * A pure state |psi> can be represented by:
         *
         *     rho = |psi><psi|
         *
         * For a normalized pure state:
         *
         *     Tr(rho) = 1
         *     Tr(rho^2) = 1
         */
        std::cout
            << "\n10. Density matrix representation\n"
            << "----------------------------------\n";

        const Matrix bellDensity =
            densityMatrix(bellState);

        printMatrix(
            bellDensity,
            "rho_Bell = |Phi+><Phi+|:"
        );

        std::cout
            << "Trace(rho) = "
            << formatComplex(
                trace(bellDensity)
            )
            << '\n';

        std::cout
            << "Purity = "
            << purity(bellDensity)
            << '\n';


        /*
         * Stage 11: Fidelity.
         *
         * For pure states:
         *
         *     F(|a>, |b>) = |<a|b>|^2
         *
         * A value of 1 means the pure states differ by at most a
         * physically irrelevant global phase.
         */
        std::cout
            << "\n11. Pure-state fidelity\n"
            << "-----------------------\n";

        std::cout
            << "F(|0>, |0>) = "
            << pureStateFidelity(
                zero,
                zero
            )
            << '\n';

        std::cout
            << "F(|0>, |1>) = "
            << pureStateFidelity(
                zero,
                one
            )
            << '\n';

        std::cout
            << "F(|0>, |+>) = "
            << pureStateFidelity(
                zero,
                plus
            )
            << '\n';


        /*
         * Stage 12: Tensor-product operator.
         *
         * To act on two qubits with separate single-qubit operations,
         * tensor the operators:
         *
         *     U_total = U1 tensor U2
         *
         * The resulting matrix is 4x4 for two qubits.
         */
        std::cout
            << "\n12. Two-qubit operator construction\n"
            << "------------------------------------\n";

        Matrix hadamardOnBoth =
            tensorProduct(H, H);

        std::cout
            << "H tensor H is unitary: "
            << (
                isUnitary(hadamardOnBoth)
                ? "true"
                : "false"
            )
            << '\n';

        QuantumState transformedRegister =
            initialRegister.apply(
                hadamardOnBoth
            );

        std::cout
            << "(H tensor H)|00> = "
            << transformedRegister.ket()
            << '\n';


        /*
         * Stage 13: Performance considerations.
         *
         * An n-qubit state vector contains 2^n complex values.
         * This is exponential in n.
         *
         * Dense matrices are even more expensive:
         * a general operator has 2^n x 2^n entries = 4^n entries.
         */
        std::cout
            << "\n13. State-vector scaling\n"
            << "------------------------\n";

        for (std::size_t qubits = 1;
             qubits <= 12;
             ++qubits) {

            const std::size_t dimension =
                static_cast<std::size_t>(1) << qubits;

            std::cout
                << qubits
                << " qubits -> "
                << dimension
                << " amplitudes\n";
        }


        /*
         * Self-validation.
         *
         * These checks represent invariants expected from the mathematics.
         * They also illustrate why production numerical code should validate
         * assumptions instead of silently accepting invalid states.
         */
        std::cout
            << "\n14. Internal validation\n"
            << "-----------------------\n";

        if (!approximatelyEqual(
                normSquared(zero.amplitudes()),
                1.0
            )) {
            throw std::runtime_error(
                "|0> is not normalized."
            );
        }

        if (!approximatelyEqual(
                normSquared(bellState.amplitudes()),
                1.0
            )) {
            throw std::runtime_error(
                "Bell state is not normalized."
            );
        }

        if (!approximatelyEqual(
                std::abs(
                    innerProduct(
                        zero.amplitudes(),
                        one.amplitudes()
                    )
                ),
                0.0
            )) {
            throw std::runtime_error(
                "Computational basis states should be orthogonal."
            );
        }

        if (!approximatelyEqual(
                pureStateFidelity(
                    zero,
                    zero
                ),
                1.0
            )) {
            throw std::runtime_error(
                "State fidelity with itself should be one."
            );
        }

        if (isProductTwoQubitState(bellState)) {
            throw std::runtime_error(
                "Bell state should not be separable."
            );
        }

        if (!approximatelyEqual(
                std::abs(
                    trace(bellDensity)
                ),
                1.0
            )) {
            throw std::runtime_error(
                "Density matrix must have unit trace."
            );
        }

        std::cout
            << "All mathematical consistency checks passed.\n";


        /*
         * Failure-condition demonstrations.
         *
         * The errors are caught locally so that the case study can continue.
         */
        std::cout
            << "\n15. Failure-condition examples\n"
            << "------------------------------\n";

        try {
            QuantumState invalid(
                {Complex(0), Complex(0)}
            );
        }
        catch (const std::exception& error) {
            std::cout
                << "Zero-vector rejection: "
                << error.what()
                << '\n';
        }

        try {
            QuantumState invalidDimension(
                {
                    Complex(1),
                    Complex(0),
                    Complex(0)
                }
            );
        }
        catch (const std::exception& error) {
            std::cout
                << "Invalid dimension rejection: "
                << error.what()
                << '\n';
        }

        try {
            zero.probability(5);
        }
        catch (const std::exception& error) {
            std::cout
                << "Invalid measurement index rejection: "
                << error.what()
                << '\n';
        }


        std::cout
            << "\n============================================================\n"
            << "CASE STUDY COMPLETE\n"
            << "============================================================\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
