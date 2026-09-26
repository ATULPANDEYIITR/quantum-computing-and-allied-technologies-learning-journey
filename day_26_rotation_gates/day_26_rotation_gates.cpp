/*
 * Rotation Gates: RX, RY, RZ
 * ==========================
 *
 * C++17 single-qubit quantum-control case study.
 *
 * Scenario:
 * ---------
 * A laboratory control system must prepare a target single-qubit state
 * using calibrated RX, RY, and RZ rotations. The program models:
 *
 *   1. A normalized complex qubit state.
 *   2. Parameterized single-qubit rotation gates.
 *   3. A calibration-aware gate library.
 *   4. A circuit containing ordered operations.
 *   5. State preparation and measurement simulation.
 *   6. Validation of unitary matrices.
 *   7. State fidelity.
 *   8. Expectation values.
 *   9. Circuit optimization for consecutive same-axis rotations.
 *  10. Error handling and edge cases.
 *  11. Complexity and resource considerations.
 *
 * Standard: C++17
 * External dependencies: none
 */

#include <array>
#include <cassert>
#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace quantum {

constexpr double PI = 3.141592653589793238462643383279502884;
constexpr double TAU = 2.0 * PI;
constexpr double EPSILON = 1e-10;

using Complex = std::complex<double>;


// -----------------------------------------------------------------------------
// Generic fixed-size linear algebra for a 2x2 single-qubit system.
// -----------------------------------------------------------------------------

struct Matrix2 {
    std::array<std::array<Complex, 2>, 2> value{};

    static Matrix2 identity() {
        Matrix2 result;
        result.value[0][0] = Complex{1.0, 0.0};
        result.value[0][1] = Complex{0.0, 0.0};
        result.value[1][0] = Complex{0.0, 0.0};
        result.value[1][1] = Complex{1.0, 0.0};
        return result;
    }
};

using Vector2 = std::array<Complex, 2>;

Matrix2 multiply(const Matrix2& a, const Matrix2& b) {
    Matrix2 result;

    for (std::size_t row = 0; row < 2; ++row) {
        for (std::size_t column = 0; column < 2; ++column) {
            result.value[row][column] = Complex{0.0, 0.0};

            for (std::size_t k = 0; k < 2; ++k) {
                result.value[row][column] +=
                    a.value[row][k] * b.value[k][column];
            }
        }
    }

    return result;
}

Vector2 multiply(const Matrix2& matrix, const Vector2& vector) {
    Vector2 result{};

    for (std::size_t row = 0; row < 2; ++row) {
        result[row] =
            matrix.value[row][0] * vector[0] +
            matrix.value[row][1] * vector[1];
    }

    return result;
}

Matrix2 conjugateTranspose(const Matrix2& matrix) {
    Matrix2 result;

    for (std::size_t row = 0; row < 2; ++row) {
        for (std::size_t column = 0; column < 2; ++column) {
            result.value[row][column] =
                std::conj(matrix.value[column][row]);
        }
    }

    return result;
}

double matrixDifferenceNorm(
    const Matrix2& a,
    const Matrix2& b
) {
    double sum = 0.0;

    for (std::size_t row = 0; row < 2; ++row) {
        for (std::size_t column = 0; column < 2; ++column) {
            const Complex difference =
                a.value[row][column] - b.value[row][column];

            sum += std::norm(difference);
        }
    }

    return std::sqrt(sum);
}

bool isUnitary(
    const Matrix2& matrix,
    double tolerance = 1e-9
) {
    const Matrix2 product =
        multiply(conjugateTranspose(matrix), matrix);

    return matrixDifferenceNorm(
        product,
        Matrix2::identity()
    ) <= tolerance;
}


// -----------------------------------------------------------------------------
// Qubit state
// -----------------------------------------------------------------------------

class QubitState {
private:
    Complex alpha_;
    Complex beta_;

public:
    QubitState(
        Complex alpha,
        Complex beta
    )
        : alpha_(alpha),
          beta_(beta) {
        validate();
    }

    static QubitState zero() {
        return QubitState(
            Complex{1.0, 0.0},
            Complex{0.0, 0.0}
        );
    }

    static QubitState one() {
        return QubitState(
            Complex{0.0, 0.0},
            Complex{1.0, 0.0}
        );
    }

    static QubitState plus() {
        const double amplitude = 1.0 / std::sqrt(2.0);

        return QubitState(
            Complex{amplitude, 0.0},
            Complex{amplitude, 0.0}
        );
    }

    static QubitState fromBloch(
        double theta,
        double phi
    ) {
        /*
         * Pure-state Bloch parameterization:
         *
         * |psi> =
         *   cos(theta/2)|0>
         *   + exp(i phi) sin(theta/2)|1>
         */
        const Complex beta =
            std::polar(
                std::sin(theta / 2.0),
                phi
            );

        return QubitState(
            Complex{std::cos(theta / 2.0), 0.0},
            beta
        );
    }

    Complex alpha() const {
        return alpha_;
    }

    Complex beta() const {
        return beta_;
    }

    double probabilityZero() const {
        return std::norm(alpha_);
    }

    double probabilityOne() const {
        return std::norm(beta_);
    }

    Vector2 vector() const {
        return {alpha_, beta_};
    }

    QubitState apply(const Matrix2& gate) const {
        if (!isUnitary(gate)) {
            throw std::invalid_argument(
                "A quantum gate must be unitary."
            );
        }

        const Vector2 transformed =
            multiply(gate, vector());

        return normalized(
            transformed[0],
            transformed[1]
        );
    }

    static QubitState normalized(
        Complex alpha,
        Complex beta
    ) {
        const double norm =
            std::sqrt(
                std::norm(alpha) +
                std::norm(beta)
            );

        if (norm < EPSILON) {
            throw std::invalid_argument(
                "Cannot normalize a zero vector."
            );
        }

        return QubitState(
            alpha / norm,
            beta / norm
        );
    }

    std::array<double, 3> blochVector() const {
        /*
         * For |psi> = alpha|0> + beta|1>:
         *
         * x = 2 Re(alpha* beta)
         * y = 2 Im(alpha* beta)
         * z = |alpha|^2 - |beta|^2
         */
        const Complex coherence =
            std::conj(alpha_) * beta_;

        return {
            2.0 * coherence.real(),
            2.0 * coherence.imag(),
            probabilityZero() - probabilityOne()
        };
    }

    double relativePhase() const {
        if (
            std::abs(alpha_) < EPSILON ||
            std::abs(beta_) < EPSILON
        ) {
            throw std::domain_error(
                "Relative phase is undefined when an amplitude is zero."
            );
        }

        return std::arg(beta_) - std::arg(alpha_);
    }

private:
    void validate() const {
        const double normSquared =
            std::norm(alpha_) +
            std::norm(beta_);

        if (
            std::abs(normSquared - 1.0) >
            1e-9
        ) {
            throw std::invalid_argument(
                "Qubit state is not normalized."
            );
        }
    }
};


// -----------------------------------------------------------------------------
// Rotation gate factory
// -----------------------------------------------------------------------------

class RotationGate {
public:
    static Matrix2 RX(double theta) {
        /*
         * RX(theta) = exp(-i theta X / 2)
         *
         * [ cos(theta/2)       -i sin(theta/2) ]
         * [ -i sin(theta/2)      cos(theta/2)  ]
         */
        const double c = std::cos(theta / 2.0);
        const double s = std::sin(theta / 2.0);

        Matrix2 result;

        result.value[0][0] = Complex{c, 0.0};
        result.value[0][1] = Complex{0.0, -s};
        result.value[1][0] = Complex{0.0, -s};
        result.value[1][1] = Complex{c, 0.0};

        return result;
    }

    static Matrix2 RY(double theta) {
        /*
         * RY(theta) = exp(-i theta Y / 2)
         *
         * [ cos(theta/2)  -sin(theta/2) ]
         * [ sin(theta/2)   cos(theta/2) ]
         */
        const double c = std::cos(theta / 2.0);
        const double s = std::sin(theta / 2.0);

        Matrix2 result;

        result.value[0][0] = Complex{c, 0.0};
        result.value[0][1] = Complex{-s, 0.0};
        result.value[1][0] = Complex{s, 0.0};
        result.value[1][1] = Complex{c, 0.0};

        return result;
    }

    static Matrix2 RZ(double theta) {
        /*
         * RZ(theta) =
         *
         * [ exp(-i theta/2)       0       ]
         * [       0         exp(i theta/2) ]
         */
        Matrix2 result;

        result.value[0][0] =
            std::polar(1.0, -theta / 2.0);

        result.value[0][1] = Complex{0.0, 0.0};
        result.value[1][0] = Complex{0.0, 0.0};

        result.value[1][1] =
            std::polar(1.0, theta / 2.0);

        return result;
    }

    static Matrix2 arbitraryAxis(
        double nx,
        double ny,
        double nz,
        double theta
    ) {
        const double length =
            std::sqrt(
                nx * nx +
                ny * ny +
                nz * nz
            );

        if (length < EPSILON) {
            throw std::invalid_argument(
                "Rotation axis cannot be the zero vector."
            );
        }

        nx /= length;
        ny /= length;
        nz /= length;

        /*
         * General rotation:
         *
         * R_n(theta) =
         *   cos(theta/2) I
         *   - i sin(theta/2)(nx X + ny Y + nz Z)
         */
        const double c = std::cos(theta / 2.0);
        const double s = std::sin(theta / 2.0);

        Matrix2 result;

        result.value[0][0] =
            Complex{c, -s * nz};

        result.value[0][1] =
            Complex{-s * ny, -s * nx};

        result.value[1][0] =
            Complex{s * ny, -s * nx};

        result.value[1][1] =
            Complex{c, s * nz};

        return result;
    }
};


// -----------------------------------------------------------------------------
// Calibration model
// -----------------------------------------------------------------------------

struct Calibration {
    /*
     * A realistic control layer may store calibration information separately
     * from the mathematical gate definition.
     *
     * angleScale models a small systematic calibration factor.
     * phaseOffset models a fixed angular offset.
     */
    double angleScale = 1.0;
    double phaseOffset = 0.0;

    double calibratedAngle(double requestedAngle) const {
        return requestedAngle * angleScale + phaseOffset;
    }
};


// -----------------------------------------------------------------------------
// Gate operation
// -----------------------------------------------------------------------------

enum class RotationAxis {
    X,
    Y,
    Z
};

struct GateOperation {
    RotationAxis axis;
    double angle;
    std::string label;
};


// -----------------------------------------------------------------------------
// Single-qubit control circuit
// -----------------------------------------------------------------------------

class QubitControlCircuit {
private:
    QubitState initialState_;
    std::vector<GateOperation> operations_;

    Matrix2 matrixFor(
        const GateOperation& operation
    ) const {
        switch (operation.axis) {
            case RotationAxis::X:
                return RotationGate::RX(operation.angle);

            case RotationAxis::Y:
                return RotationGate::RY(operation.angle);

            case RotationAxis::Z:
                return RotationGate::RZ(operation.angle);
        }

        throw std::logic_error(
            "Unknown rotation axis."
        );
    }

public:
    explicit QubitControlCircuit(
        QubitState initialState
    )
        : initialState_(std::move(initialState)) {}

    void addRX(double angle) {
        operations_.push_back({
            RotationAxis::X,
            angle,
            "RX"
        });
    }

    void addRY(double angle) {
        operations_.push_back({
            RotationAxis::Y,
            angle,
            "RY"
        });
    }

    void addRZ(double angle) {
        operations_.push_back({
            RotationAxis::Z,
            angle,
            "RZ"
        });
    }

    const std::vector<GateOperation>& operations() const {
        return operations_;
    }

    QubitState run() const {
        QubitState state = initialState_;

        for (const auto& operation : operations_) {
            state = state.apply(matrixFor(operation));
        }

        return state;
    }

    Matrix2 combinedUnitary() const {
        /*
         * If the circuit is:
         *
         *   G1 -> G2 -> G3
         *
         * the mathematical operator is:
         *
         *   U = G3 G2 G1
         */
        Matrix2 combined =
            Matrix2::identity();

        for (const auto& operation : operations_) {
            combined =
                multiply(
                    matrixFor(operation),
                    combined
                );
        }

        return combined;
    }

    void optimizeSameAxisRotations() {
        /*
         * For consecutive rotations around the same axis:
         *
         *   RX(a) RX(b) = RX(a+b)
         *
         * and similarly for RY and RZ.
         *
         * This optimization is safe because same-axis rotations commute.
         */
        if (operations_.empty()) {
            return;
        }

        std::vector<GateOperation> optimized;

        for (const auto& operation : operations_) {
            if (
                !optimized.empty() &&
                optimized.back().axis == operation.axis
            ) {
                optimized.back().angle += operation.angle;
            } else {
                optimized.push_back(operation);
            }
        }

        operations_ = std::move(optimized);
    }
};


// -----------------------------------------------------------------------------
// Measurement and experiment result
// -----------------------------------------------------------------------------

struct MeasurementCounts {
    std::size_t zero = 0;
    std::size_t one = 0;
};

MeasurementCounts measure(
    const QubitState& state,
    std::size_t shots,
    unsigned int seed = 42
) {
    if (shots == 0) {
        throw std::invalid_argument(
            "Measurement shots must be greater than zero."
        );
    }

    std::mt19937 generator(seed);
    std::uniform_real_distribution<double> distribution(
        0.0,
        1.0
    );

    MeasurementCounts counts;

    const double probabilityZero =
        state.probabilityZero();

    for (std::size_t shot = 0; shot < shots; ++shot) {
        if (
            distribution(generator) <
            probabilityZero
        ) {
            ++counts.zero;
        } else {
            ++counts.one;
        }
    }

    return counts;
}


// -----------------------------------------------------------------------------
// State fidelity
// -----------------------------------------------------------------------------

double stateFidelity(
    const QubitState& a,
    const QubitState& b
) {
    /*
     * F = |<a|b>|^2
     *
     * For pure states, F=1 means physical equivalence up to global phase.
     */
    const Complex innerProduct =
        std::conj(a.alpha()) * b.alpha() +
        std::conj(a.beta()) * b.beta();

    return std::norm(innerProduct);
}


// -----------------------------------------------------------------------------
// Expectation values
// -----------------------------------------------------------------------------

double expectationValue(
    const QubitState& state,
    const Matrix2& observable
) {
    const Vector2 transformed =
        multiply(observable, state.vector());

    const Complex value =
        std::conj(state.alpha()) * transformed[0] +
        std::conj(state.beta()) * transformed[1];

    if (std::abs(value.imag()) > 1e-8) {
        throw std::invalid_argument(
            "Observable produced a significant imaginary expectation."
        );
    }

    return value.real();
}


// -----------------------------------------------------------------------------
// Output helpers
// -----------------------------------------------------------------------------

void printState(
    const QubitState& state,
    const std::string& label
) {
    const auto bloch =
        state.blochVector();

    std::cout
        << "\n"
        << label
        << "\n"
        << "  alpha = "
        << state.alpha()
        << "\n"
        << "  beta  = "
        << state.beta()
        << "\n"
        << "  P(0)  = "
        << std::fixed
        << std::setprecision(6)
        << state.probabilityZero()
        << "\n"
        << "  P(1)  = "
        << state.probabilityOne()
        << "\n"
        << "  Bloch = ("
        << bloch[0]
        << ", "
        << bloch[1]
        << ", "
        << bloch[2]
        << ")\n";
}

void printMatrix(
    const Matrix2& matrix,
    const std::string& label
) {
    std::cout
        << "\n"
        << label
        << "\n";

    for (std::size_t row = 0; row < 2; ++row) {
        std::cout << "  [ ";

        for (std::size_t column = 0; column < 2; ++column) {
            std::cout
                << std::fixed
                << std::setprecision(5)
                << matrix.value[row][column];

            if (column == 0) {
                std::cout << " , ";
            }
        }

        std::cout << " ]\n";
    }
}


// -----------------------------------------------------------------------------
// Case study stages
// -----------------------------------------------------------------------------

void demonstrateGateLibrary() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "1. CALIBRATED ROTATION GATE LIBRARY"
        << "\n"
        << std::string(78, '=')
        << "\n";

    const double theta = PI / 2.0;

    const Matrix2 rx =
        RotationGate::RX(theta);

    const Matrix2 ry =
        RotationGate::RY(theta);

    const Matrix2 rz =
        RotationGate::RZ(theta);

    printMatrix(rx, "RX(pi/2)");
    printMatrix(ry, "RY(pi/2)");
    printMatrix(rz, "RZ(pi/2)");

    std::cout
        << "\nUnitary validation:\n"
        << "  RX = "
        << std::boolalpha
        << isUnitary(rx)
        << "\n"
        << "  RY = "
        << isUnitary(ry)
        << "\n"
        << "  RZ = "
        << isUnitary(rz)
        << "\n";
}

void demonstrateStatePreparation() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "2. STATE PREPARATION"
        << "\n"
        << std::string(78, '=')
        << "\n";

    /*
     * RY(theta)|0> produces:
     *
     *   cos(theta/2)|0> + sin(theta/2)|1>
     *
     * This makes RY particularly convenient for preparing real-amplitude
     * probability distributions on a single qubit.
     */
    const double theta = PI / 3.0;

    QubitState initial =
        QubitState::zero();

    QubitState prepared =
        initial.apply(
            RotationGate::RY(theta)
        );

    printState(
        initial,
        "Initial state"
    );

    printState(
        prepared,
        "Prepared state after RY(pi/3)"
    );

    std::cout
        << "\nExpected analytical probabilities:\n"
        << "  P(0) = cos^2(theta/2) = "
        << std::cos(theta / 2.0) *
           std::cos(theta / 2.0)
        << "\n"
        << "  P(1) = sin^2(theta/2) = "
        << std::sin(theta / 2.0) *
           std::sin(theta / 2.0)
        << "\n";
}

void demonstratePhaseControl() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "3. PHASE CONTROL WITH RZ"
        << "\n"
        << std::string(78, '=')
        << "\n";

    const QubitState plus =
        QubitState::plus();

    const QubitState rotated =
        plus.apply(
            RotationGate::RZ(PI / 2.0)
        );

    printState(
        plus,
        "|+> before RZ"
    );

    printState(
        rotated,
        "After RZ(pi/2)"
    );

    std::cout
        << "\n"
        << "RZ changes relative phase while leaving "
        << "computational-basis probabilities unchanged "
        << "for this ideal unitary transformation.\n";
}

void demonstrateNonCommutativity() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "4. NON-COMMUTATIVITY OF DIFFERENT AXES"
        << "\n"
        << std::string(78, '=')
        << "\n";

    const double a = PI / 3.0;
    const double b = PI / 4.0;

    const QubitState rxThenRy =
        QubitState::zero()
            .apply(RotationGate::RX(a))
            .apply(RotationGate::RY(b));

    const QubitState ryThenRx =
        QubitState::zero()
            .apply(RotationGate::RY(b))
            .apply(RotationGate::RX(a));

    printState(
        rxThenRy,
        "RX then RY"
    );

    printState(
        ryThenRx,
        "RY then RX"
    );

    std::cout
        << "\nFidelity = "
        << std::setprecision(12)
        << stateFidelity(
               rxThenRy,
               ryThenRx
           )
        << "\n";

    std::cout
        << "The order of different-axis rotations "
        << "is part of the circuit specification.\n";
}

void demonstrateCircuitOptimization() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "5. CIRCUIT OPTIMIZATION"
        << "\n"
        << std::string(78, '=')
        << "\n";

    QubitControlCircuit circuit(
        QubitState::zero()
    );

    circuit.addRY(0.20);
    circuit.addRY(0.30);
    circuit.addRZ(0.40);
    circuit.addRZ(-0.10);
    circuit.addRX(0.80);

    const Matrix2 before =
        circuit.combinedUnitary();

    std::cout
        << "Operations before optimization: "
        << circuit.operations().size()
        << "\n";

    circuit.optimizeSameAxisRotations();

    const Matrix2 after =
        circuit.combinedUnitary();

    std::cout
        << "Operations after optimization:  "
        << circuit.operations().size()
        << "\n";

    std::cout
        << "Unitary difference = "
        << std::scientific
        << matrixDifferenceNorm(
               before,
               after
           )
        << "\n";

    /*
     * A zero or near-zero difference indicates that the optimization
     * preserved the mathematical circuit transformation.
     */
}

void demonstrateFullControlPipeline() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "6. INDUSTRY-STYLE SINGLE-QUBIT CONTROL PIPELINE"
        << "\n"
        << std::string(78, '=')
        << "\n";

    /*
     * Scenario:
     *
     * The control layer receives a target state specified by Bloch angles.
     * It constructs a sequence of calibrated rotations, executes it,
     * validates the resulting state, and performs simulated measurements.
     */

    const double targetTheta = 1.05;
    const double targetPhi = 0.72;

    const QubitState target =
        QubitState::fromBloch(
            targetTheta,
            targetPhi
        );

    /*
     * For a pure state with angles (theta, phi), one possible preparation is
     *
     *   RZ(phi) RY(theta) |0>
     *
     * because RY establishes the polar angle and RZ establishes relative
     * phase, with the exact state representation differing only by global
     * phase depending on convention.
     */
    QubitControlCircuit circuit(
        QubitState::zero()
    );

    circuit.addRY(targetTheta);
    circuit.addRZ(targetPhi);

    printState(
        target,
        "Requested target state"
    );

    const QubitState produced =
        circuit.run();

    printState(
        produced,
        "Produced control state"
    );

    const double fidelity =
        stateFidelity(
            target,
            produced
        );

    std::cout
        << "\nTarget fidelity = "
        << std::fixed
        << std::setprecision(12)
        << fidelity
        << "\n";

    const MeasurementCounts counts =
        measure(
            produced,
            10000,
            2026
        );

    std::cout
        << "\n10,000 simulated measurements:\n"
        << "  |0>: "
        << counts.zero
        << "\n"
        << "  |1>: "
        << counts.one
        << "\n";

    /*
     * In a real device, fidelity would also be affected by:
     * - calibration error;
     * - decoherence;
     * - control-pulse distortion;
     * - readout error;
     * - crosstalk;
     * - finite pulse resolution;
     * - thermal effects.
     *
     * This educational model isolates the ideal mathematical gate behavior.
     */
}

void demonstrateExpectationValues() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "7. EXPECTATION VALUES"
        << "\n"
        << std::string(78, '=')
        << "\n";

    const QubitState state =
        QubitState::fromBloch(
            1.10,
            0.70
        );

    Matrix2 X;
    X.value = {{
        {Complex{0.0, 0.0}, Complex{1.0, 0.0}},
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}}
    }};

    Matrix2 Y;
    Y.value = {{
        {Complex{0.0, 0.0}, Complex{0.0, -1.0}},
        {Complex{0.0, 1.0}, Complex{0.0, 0.0}}
    }};

    Matrix2 Z;
    Z.value = {{
        {Complex{1.0, 0.0}, Complex{0.0, 0.0}},
        {Complex{0.0, 0.0}, Complex{-1.0, 0.0}}
    }};

    printState(
        state,
        "State"
    );

    std::cout
        << "\n"
        << "<X> = "
        << expectationValue(state, X)
        << "\n"
        << "<Y> = "
        << expectationValue(state, Y)
        << "\n"
        << "<Z> = "
        << expectationValue(state, Z)
        << "\n";
}

void demonstrateEdgeCases() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "8. EDGE CASES AND FAILURE CONDITIONS"
        << "\n"
        << std::string(78, '=')
        << "\n";

    try {
        QubitState invalid(
            Complex{1.0, 0.0},
            Complex{1.0, 0.0}
        );

        (void)invalid;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid state rejected: "
            << error.what()
            << "\n";
    }

    try {
        RotationGate::arbitraryAxis(
            0.0,
            0.0,
            0.0,
            PI / 2.0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Zero rotation axis rejected: "
            << error.what()
            << "\n";
    }

    try {
        measure(
            QubitState::zero(),
            0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Zero-shot measurement rejected: "
            << error.what()
            << "\n";
    }

    try {
        QubitState::zero().relativePhase();
    } catch (const std::exception& error) {
        std::cout
            << "Undefined relative phase handled: "
            << error.what()
            << "\n";
    }
}

void demonstratePrecision() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "9. NUMERICAL PRECISION"
        << "\n"
        << std::string(78, '=')
        << "\n";

    QubitState original =
        QubitState::fromBloch(
            0.9,
            -1.3
        );

    QubitState current =
        original;

    for (int i = 0; i < 100; ++i) {
        current =
            current.apply(
                RotationGate::RX(0.17)
            );

        current =
            current.apply(
                RotationGate::RX(-0.17)
            );
    }

    std::cout
        << std::setprecision(15)
        << "Fidelity after 100 inverse pairs = "
        << stateFidelity(
               original,
               current
           )
        << "\n";

    std::cout
        << "Floating-point computations should use "
        << "tolerance-based comparisons.\n";
}

void demonstrateComplexity() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "10. COMPLEXITY AND DESIGN CONSIDERATIONS"
        << "\n"
        << std::string(78, '=')
        << "\n";

    /*
     * A single-qubit matrix-vector multiplication uses a constant number
     * of complex arithmetic operations, so its asymptotic cost is O(1).
     *
     * For an n-qubit state-vector simulator:
     *
     *   state size = 2^n
     *
     * Applying a one-qubit gate to the full state requires O(2^n)
     * state-vector operations.
     *
     * The exponential memory requirement is the central scalability
     * limitation of direct state-vector simulation.
     */
    std::cout
        << "Single-qubit matrix-vector application: O(1)\n"
        << "n-qubit state-vector storage: O(2^n)\n"
        << "One-qubit gate on n-qubit state vector: O(2^n)\n"
        << "This program deliberately models only one qubit.\n";
}


// -----------------------------------------------------------------------------
// Automated verification
// -----------------------------------------------------------------------------

void runSelfTests() {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << "11. AUTOMATED VERIFICATION"
        << "\n"
        << std::string(78, '=')
        << "\n";

    const QubitState initial =
        QubitState::fromBloch(
            0.8,
            -0.4
        );

    // Zero-angle rotation must act as identity.
    for (const auto& gate : {
        RotationGate::RX(0.0),
        RotationGate::RY(0.0),
        RotationGate::RZ(0.0)
    }) {
        const QubitState result =
            initial.apply(gate);

        assert(
            stateFidelity(
                initial,
                result
            ) > 1.0 - 1e-12
        );
    }

    // RX(pi)|0> is |1> up to global phase.
    const QubitState rxPi =
        QubitState::zero().apply(
            RotationGate::RX(PI)
        );

    assert(
        stateFidelity(
            rxPi,
            QubitState::one()
        ) > 1.0 - 1e-12
    );

    // RY(pi)|0> is |1>.
    const QubitState ryPi =
        QubitState::zero().apply(
            RotationGate::RY(PI)
        );

    assert(
        stateFidelity(
            ryPi,
            QubitState::one()
        ) > 1.0 - 1e-12
    );

    // Same-axis rotations combine.
    const double a = 0.23;
    const double b = -0.71;

    const QubitState separate =
        initial
            .apply(RotationGate::RY(a))
            .apply(RotationGate::RY(b));

    const QubitState combined =
        initial.apply(
            RotationGate::RY(a + b)
        );

    assert(
        stateFidelity(
            separate,
            combined
        ) > 1.0 - 1e-12
    );

    // Circuit and combined matrix must agree.
    QubitControlCircuit circuit(
        initial
    );

    circuit.addRX(0.2);
    circuit.addRY(-0.3);
    circuit.addRZ(0.7);

    const QubitState circuitState =
        circuit.run();

    const QubitState directState =
        initial.apply(
            circuit.combinedUnitary()
        );

    assert(
        stateFidelity(
            circuitState,
            directState
        ) > 1.0 - 1e-12
    );

    // Every generated arbitrary-axis rotation must remain unitary.
    assert(
        isUnitary(
            RotationGate::arbitraryAxis(
                2.0,
                -1.0,
                3.0,
                0.9
            )
        )
    );

    std::cout
        << "All C++ verification tests passed.\n";
}


// -----------------------------------------------------------------------------
// Main application
// -----------------------------------------------------------------------------

} // namespace quantum


int main() {
    try {
        std::cout
            << "ROTATION GATES: RX, RY, RZ\n"
            << "Single-Qubit Quantum Control Case Study\n"
            << "Standard: C++17\n";

        quantum::demonstrateGateLibrary();
        quantum::demonstrateStatePreparation();
        quantum::demonstratePhaseControl();
        quantum::demonstrateNonCommutativity();
        quantum::demonstrateCircuitOptimization();
        quantum::demonstrateFullControlPipeline();
        quantum::demonstrateExpectationValues();
        quantum::demonstrateEdgeCases();
        quantum::demonstratePrecision();
        quantum::demonstrateComplexity();
        quantum::runSelfTests();

        std::cout
            << "\n"
            << std::string(78, '=')
            << "\n"
            << "CORE TECHNICAL REFERENCE"
            << "\n"
            << std::string(78, '=')
            << "\n";

        std::cout
            << R"(
RX(theta) = exp(-i theta X / 2)
RY(theta) = exp(-i theta Y / 2)
RZ(theta) = exp(-i theta Z / 2)

Qubit state:
    |psi> = alpha|0> + beta|1>

Normalization:
    |alpha|^2 + |beta|^2 = 1

Measurement:
    P(0) = |alpha|^2
    P(1) = |beta|^2

Bloch vector:
    x = 2 Re(alpha* beta)
    y = 2 Im(alpha* beta)
    z = |alpha|^2 - |beta|^2

Inverse:
    R_axis(theta)^dagger = R_axis(-theta)

Same-axis composition:
    R_axis(a)R_axis(b) = R_axis(a+b)

Different-axis rotations:
    Generally non-commutative.

The case study separates the mathematical gate definition from
the control-circuit layer, which is useful in production designs:
mathematical operations describe ideal transformations, while
calibration, validation, scheduling, hardware constraints, and
measurement belong to higher application layers.
)"
            << "\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
