/*
 * Bloch Sphere C++17 Case Study
 *
 * Scenario:
 *   A laboratory control system models a single physical qubit used in a
 *   calibration experiment. The system prepares a state, applies a sequence
 *   of calibrated gates, records the Bloch-vector trajectory, performs
 *   measurements, reconstructs the state using tomography, and models
 *   decoherence.
 *
 * The implementation deliberately uses only the C++ standard library.
 *
 * Build:
 *   g++ -std=c++17 -O2 bloch_sphere.cpp -o bloch_sphere
 *
 * Run:
 *   ./bloch_sphere
 */

#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Complex = std::complex<double>;
using Matrix2 = std::array<std::array<Complex, 2>, 2>;
using State = std::array<Complex, 2>;

constexpr double PI = 3.141592653589793238462643383279502884;
constexpr double EPS = 1e-10;

// -----------------------------------------------------------------------------
// Basic complex-vector operations
// -----------------------------------------------------------------------------

double norm(const State& state) {
    return std::sqrt(
        std::norm(state[0]) +
        std::norm(state[1])
    );
}

State normalize(const State& state) {
    const double length = norm(state);

    if (length < EPS) {
        throw std::invalid_argument(
            "The zero vector cannot represent a quantum state."
        );
    }

    return {
        state[0] / length,
        state[1] / length
    };
}

Complex innerProduct(const State& a, const State& b) {
    return std::conj(a[0]) * b[0] +
           std::conj(a[1]) * b[1];
}

// -----------------------------------------------------------------------------
// Matrix operations
// -----------------------------------------------------------------------------

Matrix2 identityMatrix() {
    return {{
        {{Complex(1, 0), Complex(0, 0)}},
        {{Complex(0, 0), Complex(1, 0)}}
    }};
}

Matrix2 matrixAdd(const Matrix2& a, const Matrix2& b) {
    Matrix2 result{};

    for (int i = 0; i < 2; ++i) {
        for (int j = 0; j < 2; ++j) {
            result[i][j] = a[i][j] + b[i][j];
        }
    }

    return result;
}

Matrix2 matrixScale(double scalar, const Matrix2& matrix) {
    Matrix2 result{};

    for (int i = 0; i < 2; ++i) {
        for (int j = 0; j < 2; ++j) {
            result[i][j] = matrix[i][j] * scalar;
        }
    }

    return result;
}

Matrix2 matrixMultiply(const Matrix2& a, const Matrix2& b) {
    Matrix2 result{};

    for (int i = 0; i < 2; ++i) {
        for (int j = 0; j < 2; ++j) {
            result[i][j] = Complex(0, 0);

            for (int k = 0; k < 2; ++k) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }

    return result;
}

Matrix2 dagger(const Matrix2& matrix) {
    Matrix2 result{};

    for (int i = 0; i < 2; ++i) {
        for (int j = 0; j < 2; ++j) {
            result[i][j] = std::conj(matrix[j][i]);
        }
    }

    return result;
}

Complex trace(const Matrix2& matrix) {
    return matrix[0][0] + matrix[1][1];
}

State matrixVectorMultiply(const Matrix2& matrix, const State& state) {
    return {
        matrix[0][0] * state[0] + matrix[0][1] * state[1],
        matrix[1][0] * state[0] + matrix[1][1] * state[1]
    };
}

Matrix2 outerProduct(const State& state) {
    Matrix2 result{};

    for (int i = 0; i < 2; ++i) {
        for (int j = 0; j < 2; ++j) {
            result[i][j] = state[i] * std::conj(state[j]);
        }
    }

    return result;
}

// -----------------------------------------------------------------------------
// Pauli matrices and standard gates
// -----------------------------------------------------------------------------

Matrix2 pauliX() {
    return {{
        {{Complex(0, 0), Complex(1, 0)}},
        {{Complex(1, 0), Complex(0, 0)}}
    }};
}

Matrix2 pauliY() {
    return {{
        {{Complex(0, 0), Complex(0, -1)}},
        {{Complex(0, 1), Complex(0, 0)}}
    }};
}

Matrix2 pauliZ() {
    return {{
        {{Complex(1, 0), Complex(0, 0)}},
        {{Complex(0, 0), Complex(-1, 0)}}
    }};
}

Matrix2 hadamard() {
    const double value = 1.0 / std::sqrt(2.0);

    return {{
        {{Complex(value, 0), Complex(value, 0)}},
        {{Complex(value, 0), Complex(-value, 0)}}
    }};
}

Matrix2 phaseGate() {
    return {{
        {{Complex(1, 0), Complex(0, 0)}},
        {{Complex(0, 0), Complex(0, 1)}}
    }};
}

Matrix2 rotationX(double theta) {
    const double c = std::cos(theta / 2.0);
    const double s = std::sin(theta / 2.0);

    return {{
        {{Complex(c, 0), Complex(0, -s)}},
        {{Complex(0, -s), Complex(c, 0)}}
    }};
}

Matrix2 rotationY(double theta) {
    const double c = std::cos(theta / 2.0);
    const double s = std::sin(theta / 2.0);

    return {{
        {{Complex(c, 0), Complex(-s, 0)}},
        {{Complex(s, 0), Complex(c, 0)}}
    }};
}

Matrix2 rotationZ(double theta) {
    return {{
        {{std::exp(Complex(0, -theta / 2.0)), Complex(0, 0)}},
        {{Complex(0, 0), std::exp(Complex(0, theta / 2.0))}}
    }};
}

// -----------------------------------------------------------------------------
// Bloch-vector model
// -----------------------------------------------------------------------------

struct BlochVector {
    double x{};
    double y{};
    double z{};

    double magnitude() const {
        return std::sqrt(x * x + y * y + z * z);
    }

    bool isValid() const {
        return magnitude() <= 1.0 + EPS;
    }

    bool isPure() const {
        return std::abs(magnitude() - 1.0) < 1e-8;
    }
};

std::ostream& operator<<(std::ostream& output, const BlochVector& vector) {
    output << std::fixed << std::setprecision(6)
           << "("
           << vector.x << ", "
           << vector.y << ", "
           << vector.z
           << ")";
    return output;
}

State stateFromBloch(double theta, double phi) {
    return {
        Complex(std::cos(theta / 2.0), 0),
        std::polar(std::sin(theta / 2.0), phi)
    };
}

BlochVector blochFromState(const State& rawState) {
    const State state = normalize(rawState);

    const Complex alpha = state[0];
    const Complex beta = state[1];

    const Complex crossTerm = std::conj(alpha) * beta;

    return {
        2.0 * crossTerm.real(),
        2.0 * crossTerm.imag(),
        std::norm(alpha) - std::norm(beta)
    };
}

Matrix2 densityMatrixFromState(const State& state) {
    return outerProduct(normalize(state));
}

Matrix2 densityMatrixFromBloch(const BlochVector& bloch) {
    if (!bloch.isValid()) {
        throw std::invalid_argument(
            "A Bloch vector must lie inside or on the unit sphere."
        );
    }

    Matrix2 result = matrixScale(0.5, identityMatrix());

    result = matrixAdd(
        result,
        matrixScale(0.5 * bloch.x, pauliX())
    );

    result = matrixAdd(
        result,
        matrixScale(0.5 * bloch.y, pauliY())
    );

    result = matrixAdd(
        result,
        matrixScale(0.5 * bloch.z, pauliZ())
    );

    return result;
}

BlochVector blochFromDensityMatrix(const Matrix2& rho) {
    return {
        trace(matrixMultiply(rho, pauliX())).real(),
        trace(matrixMultiply(rho, pauliY())).real(),
        trace(matrixMultiply(rho, pauliZ())).real()
    };
}

double purity(const Matrix2& rho) {
    return trace(matrixMultiply(rho, rho)).real();
}

// -----------------------------------------------------------------------------
// Measurement
// -----------------------------------------------------------------------------

struct MeasurementResult {
    int outcome;
    State collapsedState;
};

MeasurementResult measure(
    const State& state,
    std::mt19937& generator
) {
    const State normalizedState = normalize(state);

    const double probabilityZero = std::norm(normalizedState[0]);

    std::uniform_real_distribution<double> distribution(0.0, 1.0);

    if (distribution(generator) < probabilityZero) {
        return {
            0,
            {Complex(1, 0), Complex(0, 0)}
        };
    }

    return {
        1,
        {Complex(0, 0), Complex(1, 0)}
    };
}

std::pair<double, double> measurementProbabilities(const State& state) {
    const State normalizedState = normalize(state);

    return {
        std::norm(normalizedState[0]),
        std::norm(normalizedState[1])
    };
}

// -----------------------------------------------------------------------------
// Noise channels
// -----------------------------------------------------------------------------

Matrix2 conjugateByPauli(
    const Matrix2& rho,
    const Matrix2& pauli
) {
    return matrixMultiply(
        matrixMultiply(pauli, rho),
        pauli
    );
}

void validateProbability(double probability) {
    if (probability < 0.0 || probability > 1.0) {
        throw std::invalid_argument(
            "Probability must be in the interval [0, 1]."
        );
    }
}

Matrix2 bitFlipChannel(
    const Matrix2& rho,
    double probability
) {
    validateProbability(probability);

    return matrixAdd(
        matrixScale(1.0 - probability, rho),
        matrixScale(
            probability,
            conjugateByPauli(rho, pauliX())
        )
    );
}

Matrix2 phaseFlipChannel(
    const Matrix2& rho,
    double probability
) {
    validateProbability(probability);

    return matrixAdd(
        matrixScale(1.0 - probability, rho),
        matrixScale(
            probability,
            conjugateByPauli(rho, pauliZ())
        )
    );
}

Matrix2 depolarizingChannel(
    const Matrix2& rho,
    double probability
) {
    validateProbability(probability);

    Matrix2 result =
        matrixScale(1.0 - probability, rho);

    const std::array<Matrix2, 3> paulis = {
        pauliX(),
        pauliY(),
        pauliZ()
    };

    for (const Matrix2& pauli : paulis) {
        result = matrixAdd(
            result,
            matrixScale(
                probability / 3.0,
                conjugateByPauli(rho, pauli)
            )
        );
    }

    return result;
}

// -----------------------------------------------------------------------------
// Quantum-gate evolution
// -----------------------------------------------------------------------------

State applyGate(
    const State& state,
    const Matrix2& gate
) {
    return normalize(matrixVectorMultiply(gate, state));
}

Matrix2 evolveDensityMatrix(
    const Matrix2& rho,
    const Matrix2& gate
) {
    return matrixMultiply(
        matrixMultiply(gate, rho),
        dagger(gate)
    );
}

double stateFidelity(
    const State& a,
    const State& b
) {
    return std::norm(
        innerProduct(
            normalize(a),
            normalize(b)
        )
    );
}

// -----------------------------------------------------------------------------
// Tomography
// -----------------------------------------------------------------------------

struct TomographyEstimate {
    BlochVector estimate;
    std::size_t shots;
};

double exactPauliExpectation(
    const Matrix2& rho,
    const Matrix2& pauli
) {
    return trace(
        matrixMultiply(rho, pauli)
    ).real();
}

double samplePauliExpectation(
    double exactExpectation,
    std::size_t shots,
    std::mt19937& generator
) {
    if (shots == 0) {
        throw std::invalid_argument(
            "Tomography requires at least one shot."
        );
    }

    // For a Pauli observable with eigenvalues +/-1:
    // P(+1) = (1 + <P>) / 2.
    const double probabilityPlus =
        (1.0 + exactExpectation) / 2.0;

    std::bernoulli_distribution distribution(probabilityPlus);

    std::size_t plusCount = 0;

    for (std::size_t i = 0; i < shots; ++i) {
        if (distribution(generator)) {
            ++plusCount;
        }
    }

    const std::size_t minusCount =
        shots - plusCount;

    return static_cast<double>(plusCount - minusCount)
        / static_cast<double>(shots);
}

TomographyEstimate performTomography(
    const State& state,
    std::size_t shots,
    std::mt19937& generator
) {
    const Matrix2 rho =
        densityMatrixFromState(state);

    const double xExact =
        exactPauliExpectation(rho, pauliX());

    const double yExact =
        exactPauliExpectation(rho, pauliY());

    const double zExact =
        exactPauliExpectation(rho, pauliZ());

    return {
        {
            samplePauliExpectation(
                xExact, shots, generator
            ),
            samplePauliExpectation(
                yExact, shots, generator
            ),
            samplePauliExpectation(
                zExact, shots, generator
            )
        },
        shots
    };
}

// -----------------------------------------------------------------------------
// Laboratory calibration model
// -----------------------------------------------------------------------------

struct GateOperation {
    std::string name;
    Matrix2 matrix;
};

class QubitCalibrationExperiment {
private:
    State state_;
    std::vector<std::pair<std::string, BlochVector>> trajectory_;

public:
    explicit QubitCalibrationExperiment(
        const State& initialState
    )
        : state_(normalize(initialState)) {

        trajectory_.push_back({
            "initial",
            blochFromState(state_)
        });
    }

    void apply(
        const std::string& name,
        const Matrix2& gate
    ) {
        state_ = applyGate(state_, gate);

        trajectory_.push_back({
            name,
            blochFromState(state_)
        });
    }

    const State& state() const {
        return state_;
    }

    const std::vector<std::pair<std::string, BlochVector>>&
    trajectory() const {
        return trajectory_;
    }

    void printTrajectory() const {
        std::cout
            << "\nBloch-vector trajectory\n"
            << "----------------------\n";

        for (const auto& entry : trajectory_) {
            std::cout
                << std::left
                << std::setw(18)
                << entry.first
                << entry.second
                << '\n';
        }
    }
};

// -----------------------------------------------------------------------------
// Formatting helpers
// -----------------------------------------------------------------------------

void printState(
    const std::string& name,
    const State& state
) {
    std::cout
        << name
        << " = ["
        << state[0]
        << ", "
        << state[1]
        << "]\n";
}

void printMatrix(
    const std::string& name,
    const Matrix2& matrix
) {
    std::cout << name << " =\n";

    for (const auto& row : matrix) {
        std::cout
            << "  ["
            << row[0]
            << ", "
            << row[1]
            << "]\n";
    }
}

// -----------------------------------------------------------------------------
// Validation
// -----------------------------------------------------------------------------

void runValidation() {
    std::cout << "\n=== Validation ===\n";

    const std::vector<std::pair<double, double>> points = {
        {0.0, 0.0},
        {PI / 2.0, 0.0},
        {PI / 2.0, PI / 2.0},
        {PI, 0.0},
        {1.234, 4.321}
    };

    for (const auto& [theta, phi] : points) {
        const State state =
            stateFromBloch(theta, phi);

        const BlochVector bloch =
            blochFromState(state);

        if (std::abs(bloch.magnitude() - 1.0) > 1e-8) {
            throw std::runtime_error(
                "Pure state did not map to sphere surface."
            );
        }

        const Matrix2 original =
            densityMatrixFromState(state);

        const Matrix2 reconstructed =
            densityMatrixFromBloch(bloch);

        double maximumError = 0.0;

        for (int i = 0; i < 2; ++i) {
            for (int j = 0; j < 2; ++j) {
                maximumError = std::max(
                    maximumError,
                    std::abs(
                        original[i][j] -
                        reconstructed[i][j]
                    )
                );
            }
        }

        if (maximumError > 1e-8) {
            throw std::runtime_error(
                "State-to-Bloch reconstruction failed."
            );
        }
    }

    std::cout
        << "Pure-state and density-matrix "
        << "round-trip tests passed.\n";

    const Matrix2 identity = identityMatrix();

    const std::vector<Matrix2> gates = {
        pauliX(),
        pauliY(),
        pauliZ(),
        hadamard(),
        phaseGate(),
        rotationX(0.71),
        rotationY(1.17),
        rotationZ(2.03)
    };

    for (const Matrix2& gate : gates) {
        const Matrix2 product =
            matrixMultiply(dagger(gate), gate);

        double maximumError = 0.0;

        for (int i = 0; i < 2; ++i) {
            for (int j = 0; j < 2; ++j) {
                maximumError = std::max(
                    maximumError,
                    std::abs(product[i][j] - identity[i][j])
                );
            }
        }

        if (maximumError > 1e-8) {
            throw std::runtime_error(
                "A gate failed the unitarity test."
            );
        }
    }

    std::cout
        << "Unitary-gate tests passed.\n";

    try {
        densityMatrixFromBloch(
            {1.2, 0.0, 0.0}
        );

        throw std::runtime_error(
            "Invalid Bloch vector was accepted."
        );
    }
    catch (const std::invalid_argument&) {
        std::cout
            << "Invalid Bloch-vector test passed.\n";
    }
}

// -----------------------------------------------------------------------------
// Main industry-style case study
// -----------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "BLOCH SPHERE C++ QUBIT CALIBRATION CASE STUDY\n"
            << "============================================================\n";

        // ---------------------------------------------------------------------
        // Stage 1: prepare a calibrated qubit state
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 1: State preparation ===\n";

        State initialState =
            stateFromBloch(
                1.10,
                0.70
            );

        printState(
            "Initial state",
            initialState
        );

        std::cout
            << "Initial Bloch vector: "
            << blochFromState(initialState)
            << '\n';

        // ---------------------------------------------------------------------
        // Stage 2: apply a realistic pulse sequence
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 2: Gate sequence ===\n";

        QubitCalibrationExperiment experiment(
            initialState
        );

        experiment.apply(
            "Ry(pi/6)",
            rotationY(PI / 6.0)
        );

        experiment.apply(
            "Rz(pi/4)",
            rotationZ(PI / 4.0)
        );

        experiment.apply(
            "Rx(pi/3)",
            rotationX(PI / 3.0)
        );

        experiment.apply(
            "Hadamard",
            hadamard()
        );

        experiment.apply(
            "Phase S",
            phaseGate()
        );

        experiment.printTrajectory();

        const State finalState =
            experiment.state();

        printState(
            "\nFinal state",
            finalState
        );

        const BlochVector finalBloch =
            blochFromState(finalState);

        std::cout
            << "Final Bloch vector: "
            << finalBloch
            << '\n';

        // ---------------------------------------------------------------------
        // Stage 3: density-matrix representation
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 3: Density matrix ===\n";

        Matrix2 rho =
            densityMatrixFromState(finalState);

        printMatrix(
            "rho",
            rho
        );

        std::cout
            << "Recovered Bloch vector: "
            << blochFromDensityMatrix(rho)
            << '\n';

        std::cout
            << "Purity: "
            << std::setprecision(8)
            << purity(rho)
            << '\n';

        // ---------------------------------------------------------------------
        // Stage 4: measurement probabilities
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 4: Measurement probabilities ===\n";

        const auto [p0, p1] =
            measurementProbabilities(finalState);

        std::cout
            << "P(0) = "
            << p0
            << "\nP(1) = "
            << p1
            << "\nP(0)+P(1) = "
            << p0 + p1
            << '\n';

        // ---------------------------------------------------------------------
        // Stage 5: repeated measurement experiment
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 5: 10,000-shot measurement ===\n";

        std::mt19937 generator(20260922);

        constexpr std::size_t shots = 10000;

        std::size_t zeroCount = 0;
        std::size_t oneCount = 0;

        for (std::size_t shot = 0; shot < shots; ++shot) {
            const MeasurementResult result =
                measure(finalState, generator);

            if (result.outcome == 0) {
                ++zeroCount;
            }
            else {
                ++oneCount;
            }
        }

        std::cout
            << "Observed |0>: "
            << zeroCount
            << " ("
            << 100.0 * static_cast<double>(zeroCount) / shots
            << "%)\n";

        std::cout
            << "Observed |1>: "
            << oneCount
            << " ("
            << 100.0 * static_cast<double>(oneCount) / shots
            << "%)\n";

        // ---------------------------------------------------------------------
        // Stage 6: tomography
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 6: State tomography ===\n";

        const TomographyEstimate tomography =
            performTomography(
                finalState,
                5000,
                generator
            );

        std::cout
            << "Exact Bloch vector:     "
            << finalBloch
            << '\n';

        std::cout
            << "Tomography estimate:    "
            << tomography.estimate
            << '\n';

        std::cout
            << "Tomography shots:       "
            << tomography.shots
            << '\n';

        // ---------------------------------------------------------------------
        // Stage 7: model decoherence
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 7: Decoherence model ===\n";

        for (double probability : {0.05, 0.15, 0.30, 0.50}) {
            Matrix2 noisy =
                depolarizingChannel(
                    rho,
                    probability
                );

            std::cout
                << "Depolarizing p="
                << probability
                << " -> Bloch "
                << blochFromDensityMatrix(noisy)
                << ", purity="
                << purity(noisy)
                << '\n';
        }

        // ---------------------------------------------------------------------
        // Stage 8: phase noise
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 8: Phase noise ===\n";

        for (double probability : {0.10, 0.25, 0.50}) {
            Matrix2 noisy =
                phaseFlipChannel(
                    rho,
                    probability
                );

            std::cout
                << "Phase-flip p="
                << probability
                << " -> Bloch "
                << blochFromDensityMatrix(noisy)
                << '\n';
        }

        // ---------------------------------------------------------------------
        // Stage 9: gate fidelity check
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 9: Fidelity and calibration ===\n";

        State expected =
            applyGate(
                initialState,
                matrixMultiply(
                    matrixMultiply(
                        matrixMultiply(
                            matrixMultiply(
                                rotationY(PI / 6.0),
                                rotationZ(PI / 4.0)
                            ),
                            rotationX(PI / 3.0)
                        ),
                        hadamard()
                    ),
                    phaseGate()
                )
            );

        const double fidelity =
            stateFidelity(
                expected,
                finalState
            );

        std::cout
            << "Ideal-vs-simulated fidelity: "
            << fidelity
            << '\n';

        // ---------------------------------------------------------------------
        // Stage 10: geometric measurement relationship
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Stage 10: Geometric interpretation ===\n";

        const double geometricP0 =
            (1.0 + finalBloch.z) / 2.0;

        const double geometricP1 =
            (1.0 - finalBloch.z) / 2.0;

        std::cout
            << "From z coordinate:\n"
            << "P(0) = (1+z)/2 = "
            << geometricP0
            << "\n"
            << "P(1) = (1-z)/2 = "
            << geometricP1
            << '\n';

        // ---------------------------------------------------------------------
        // Stage 11: validation
        // ---------------------------------------------------------------------

        runValidation();

        // ---------------------------------------------------------------------
        // Final technical observations
        // ---------------------------------------------------------------------

        std::cout
            << "\n=== Case-study observations ===\n"
            << "1. Pure qubit states occupy the surface of the Bloch sphere.\n"
            << "2. Unitary single-qubit gates rotate the Bloch vector.\n"
            << "3. Computational-basis measurement depends on the z coordinate.\n"
            << "4. Relative phase determines the azimuthal position.\n"
            << "5. Global phase does not change the physical Bloch point.\n"
            << "6. Noise generally moves a state toward the interior.\n"
            << "7. Tomography reconstructs the Bloch vector statistically.\n"
            << "8. The density matrix represents both pure and mixed states.\n";

        std::cout
            << "\nProgram completed successfully.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "\nFatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
