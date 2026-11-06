#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Majorana-Based Topological Quantum Computing
 *
 * C++17 simulation of:
 * - Majorana zero modes and fermion parity
 * - Ising-anyon fusion channels
 * - Non-Abelian braid transformations
 * - Braid-group relations
 * - Experimental operating constraints
 * - Quantum state normalization and fidelity
 * - Experiment audit records
 *
 * Mathematical simulation only. It does not model a physical
 * semiconductor-superconductor device or prove topological protection.
 */

using Complex = std::complex<double>;
using State = std::array<Complex, 2>;
using Matrix = std::array<std::array<Complex, 2>, 2>;

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 1e-9;

enum class FusionChannel {
    Vacuum,
    Fermion
};

enum class ExperimentStatus {
    Accepted,
    Rejected
};

struct ExperimentalConditions {
    double energyGap;
    double temperature;
    double coherenceTime;
    double operationTime;
    double measurementError;
    double minimumGap = 0.1;
};

struct BraidOperation {
    int generator;
    int orientation;

    void validate() const {
        if (generator != 1 && generator != 2) {
            throw std::invalid_argument(
                "Only B1 and B2 are supported."
            );
        }

        if (orientation != -1 && orientation != 1) {
            throw std::invalid_argument(
                "Invalid braid orientation."
            );
        }
    }
};

struct BraidEvent {
    int sequence;
    BraidOperation operation;
};

struct ExperimentResult {
    std::string id;
    ExperimentStatus status;
    State initialState;
    State finalState;
    int operations;
    double fidelity;
    std::vector<std::string> failures;
};

class MajoranaAlgebra {
public:
    static int anticommutator(int i, int j) {
        if (i < 1 || j < 1) {
            throw std::invalid_argument("Invalid Majorana index.");
        }

        return i == j ? 2 : 0;
    }

    static int square() {
        return 1;
    }

    static int parity(int occupation) {
        if (occupation != 0 && occupation != 1) {
            throw std::invalid_argument("Occupation must be binary.");
        }

        return occupation == 0 ? 1 : -1;
    }

    static FusionChannel fusion(int occupation) {
        if (occupation != 0 && occupation != 1) {
            throw std::invalid_argument("Occupation must be binary.");
        }

        return occupation == 0
            ? FusionChannel::Vacuum
            : FusionChannel::Fermion;
    }
};

class QuantumMath {
public:
    static State initialState() {
        const double value = 1.0 / std::sqrt(2.0);

        return {
            Complex(value, 0),
            Complex(value, 0)
        };
    }

    static double normSquared(const State& state) {
        return std::norm(state[0]) + std::norm(state[1]);
    }

    static State normalize(const State& state) {
        const double norm = std::sqrt(normSquared(state));

        if (!std::isfinite(norm) || norm < EPSILON) {
            throw std::invalid_argument("Invalid state norm.");
        }

        return {
            state[0] / norm,
            state[1] / norm
        };
    }

    static void validate(const State& state) {
        if (!std::isfinite(state[0].real()) ||
            !std::isfinite(state[0].imag()) ||
            !std::isfinite(state[1].real()) ||
            !std::isfinite(state[1].imag())) {
            throw std::invalid_argument(
                "Non-finite state amplitude."
            );
        }

        if (std::abs(normSquared(state) - 1.0) > EPSILON) {
            throw std::invalid_argument(
                "State is not normalized."
            );
        }
    }

    static Complex innerProduct(
        const State& first,
        const State& second
    ) {
        return std::conj(first[0]) * second[0]
             + std::conj(first[1]) * second[1];
    }

    static double fidelity(
        const State& first,
        const State& second
    ) {
        return std::norm(innerProduct(first, second));
    }

    static Matrix multiply(
        const Matrix& first,
        const Matrix& second
    ) {
        Matrix result{};

        for (int i = 0; i < 2; ++i) {
            for (int j = 0; j < 2; ++j) {
                for (int k = 0; k < 2; ++k) {
                    result[i][j] +=
                        first[i][k] * second[k][j];
                }
            }
        }

        return result;
    }

    static State apply(
        const Matrix& matrix,
        const State& state
    ) {
        State result{};

        for (int i = 0; i < 2; ++i) {
            for (int j = 0; j < 2; ++j) {
                result[i] += matrix[i][j] * state[j];
            }
        }

        return normalize(result);
    }
};

class BraidEngine {
public:
    static Matrix generator(
        int index,
        int orientation = 1
    ) {
        if (index != 1 && index != 2) {
            throw std::invalid_argument("Invalid braid generator.");
        }

        if (orientation != -1 && orientation != 1) {
            throw std::invalid_argument("Invalid orientation.");
        }

        const Complex phase = std::polar(1.0, -PI / 4.0);
        const Complex inversePhase = std::conj(phase);

        const Matrix b1{{
            {phase, Complex(0, 0)},
            {Complex(0, 0), inversePhase}
        }};

        const Complex average =
            (phase + inversePhase) / 2.0;

        const Complex difference =
            (phase - inversePhase) / 2.0;

        const Matrix b2{{
            {average, difference},
            {difference, average}
        }};

        Matrix result = index == 1 ? b1 : b2;

        if (orientation == -1) {
            Matrix inverse{};

            for (int i = 0; i < 2; ++i) {
                for (int j = 0; j < 2; ++j) {
                    inverse[i][j] =
                        std::conj(result[j][i]);
                }
            }

            return inverse;
        }

        return result;
    }

    static double unitarityError(const Matrix& matrix) {
        double maximum = 0;

        for (int i = 0; i < 2; ++i) {
            for (int j = 0; j < 2; ++j) {
                Complex value = 0;

                for (int k = 0; k < 2; ++k) {
                    value += std::conj(matrix[k][i])
                           * matrix[k][j];
                }

                const Complex expected = i == j
                    ? Complex(1, 0)
                    : Complex(0, 0);

                maximum = std::max(
                    maximum,
                    std::abs(value - expected)
                );
            }
        }

        return maximum;
    }

    static double braidRelationError() {
        const Matrix b1 = generator(1);
        const Matrix b2 = generator(2);

        const Matrix left = QuantumMath::multiply(
            QuantumMath::multiply(b1, b2),
            b1
        );

        const Matrix right = QuantumMath::multiply(
            QuantumMath::multiply(b2, b1),
            b2
        );

        double maximum = 0;

        for (int i = 0; i < 2; ++i) {
            for (int j = 0; j < 2; ++j) {
                maximum = std::max(
                    maximum,
                    std::abs(left[i][j] - right[i][j])
                );
            }
        }

        return maximum;
    }
};

class ExperimentalPolicy {
public:
    static std::vector<std::string> evaluate(
        const ExperimentalConditions& conditions
    ) {
        const std::array<double, 6> values = {
            conditions.energyGap,
            conditions.temperature,
            conditions.coherenceTime,
            conditions.operationTime,
            conditions.measurementError,
            conditions.minimumGap
        };

        for (double value : values) {
            if (!std::isfinite(value)) {
                throw std::invalid_argument(
                    "Experimental values must be finite."
                );
            }
        }

        if (conditions.energyGap < 0 ||
            conditions.minimumGap <= 0 ||
            conditions.temperature < 0 ||
            conditions.coherenceTime <= 0 ||
            conditions.operationTime <= 0 ||
            conditions.measurementError < 0 ||
            conditions.measurementError > 1) {
            throw std::invalid_argument(
                "Invalid experimental conditions."
            );
        }

        std::vector<std::string> failures;

        if (conditions.energyGap < conditions.minimumGap) {
            failures.push_back("Energy gap below threshold.");
        }

        if (conditions.operationTime >= conditions.coherenceTime) {
            failures.push_back("Coherence window exceeded.");
        }

        if (conditions.measurementError > 0.05) {
            failures.push_back("Parity measurement error too high.");
        }

        if (conditions.temperature > conditions.energyGap) {
            failures.push_back("Temperature exceeds energy-gap scale.");
        }

        return failures;
    }
};

class MajoranaExperiment {
private:
    std::string id;
    State state;
    std::vector<BraidEvent> audit;
    int maximumOperations;

public:
    MajoranaExperiment(
        std::string experimentId,
        int maxOperations = 10000
    )
        : id(std::move(experimentId)),
          state(QuantumMath::initialState()),
          maximumOperations(maxOperations) {

        if (id.empty()) {
            throw std::invalid_argument("Experiment ID is required.");
        }

        if (maximumOperations <= 0) {
            throw std::invalid_argument("Invalid operation limit.");
        }
    }

    void execute(const std::vector<BraidOperation>& sequence) {
        if (sequence.size() > static_cast<std::size_t>(
            maximumOperations
        )) {
            throw std::runtime_error("Operation limit exceeded.");
        }

        for (const auto& operation : sequence) {
            operation.validate();

            const Matrix matrix = BraidEngine::generator(
                operation.generator,
                operation.orientation
            );

            State nextState = QuantumMath::apply(matrix, state);

            QuantumMath::validate(nextState);

            // Commit state only after successful mathematical validation.
            state = nextState;

            audit.push_back({
                static_cast<int>(audit.size()) + 1,
                operation
            });
        }
    }

    const State& getState() const {
        return state;
    }

    const std::vector<BraidEvent>& getAudit() const {
        return audit;
    }

    ExperimentResult run(
        const std::vector<BraidOperation>& sequence,
        const ExperimentalConditions& conditions
    ) {
        const State initial = QuantumMath::initialState();

        const auto failures = ExperimentalPolicy::evaluate(
            conditions
        );

        if (!failures.empty()) {
            return {
                id,
                ExperimentStatus::Rejected,
                initial,
                initial,
                0,
                1.0,
                failures
            };
        }

        execute(sequence);

        return {
            id,
            ExperimentStatus::Accepted,
            initial,
            state,
            static_cast<int>(audit.size()),
            QuantumMath::fidelity(initial, state),
            {}
        };
    }
};

void printState(const State& state) {
    std::cout << std::fixed << std::setprecision(6);

    for (const auto& amplitude : state) {
        std::cout << "("
                  << amplitude.real()
                  << ", "
                  << amplitude.imag()
                  << ") ";
    }

    std::cout << '\n';
}

void runTests() {
    if (MajoranaAlgebra::anticommutator(1, 1) != 2) {
        throw std::runtime_error("Majorana square test failed.");
    }

    if (MajoranaAlgebra::anticommutator(1, 2) != 0) {
        throw std::runtime_error("Anticommutation test failed.");
    }

    if (MajoranaAlgebra::parity(0) != 1 ||
        MajoranaAlgebra::parity(1) != -1) {
        throw std::runtime_error("Parity test failed.");
    }

    if (BraidEngine::braidRelationError() > EPSILON) {
        throw std::runtime_error("Braid relation test failed.");
    }

    for (int index : {1, 2}) {
        if (BraidEngine::unitarityError(
            BraidEngine::generator(index)
        ) > EPSILON) {
            throw std::runtime_error("Unitarity test failed.");
        }
    }

    State initial = QuantumMath::initialState();

    const State restored = QuantumMath::apply(
        BraidEngine::generator(1, -1),
        QuantumMath::apply(
            BraidEngine::generator(1),
            initial
        )
    );

    if (QuantumMath::fidelity(initial, restored) < 1 - EPSILON) {
        throw std::runtime_error("Inverse braid test failed.");
    }

    bool invalidRejected = false;

    try {
        BraidEngine::generator(3);
    } catch (const std::invalid_argument&) {
        invalidRejected = true;
    }

    if (!invalidRejected) {
        throw std::runtime_error("Invalid generator test failed.");
    }

    std::cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        std::cout << "MAJORANA TOPOLOGICAL QUANTUM COMPUTING\n";
        std::cout << "======================================\n";

        std::cout << "\nMajorana algebra\n";
        std::cout << "gamma_i squared: "
                  << MajoranaAlgebra::square() << '\n';

        std::cout << "{gamma_1, gamma_1}: "
                  << MajoranaAlgebra::anticommutator(1, 1) << '\n';

        std::cout << "{gamma_1, gamma_2}: "
                  << MajoranaAlgebra::anticommutator(1, 2) << '\n';

        std::cout << "\nFusion channels\n";

        for (int occupation : {0, 1}) {
            const auto channel =
                MajoranaAlgebra::fusion(occupation);

            std::cout
                << (channel == FusionChannel::Vacuum ? "1" : "psi")
                << " parity=" << MajoranaAlgebra::parity(occupation)
                << '\n';
        }

        std::cout << "\nBraid-group relation error: "
                  << BraidEngine::braidRelationError() << '\n';

        ExperimentalConditions conditions{
            0.25,
            0.01,
            100.0,
            2.0,
            0.01,
            0.1
        };

        std::vector<BraidOperation> sequence = {
            {1, 1},
            {2, 1},
            {1, 1},
            {2, -1}
        };

        MajoranaExperiment experiment("CPP-EXP-001");

        const ExperimentResult result = experiment.run(
            sequence,
            conditions
        );

        std::cout << "\nExperiment: " << result.id << '\n';

        std::cout << "Status: "
                  << (result.status == ExperimentStatus::Accepted
                      ? "ACCEPTED"
                      : "REJECTED")
                  << '\n';

        std::cout << "Operations: " << result.operations << '\n';
        std::cout << "Fidelity: " << result.fidelity << '\n';

        std::cout << "Final state: ";
        printState(result.finalState);

        std::cout << "\nRejected-condition example\n";

        ExperimentalConditions invalidConditions{
            0.01,
            0.01,
            10.0,
            20.0,
            0.1,
            0.1
        };

        const auto rejected = ExperimentalPolicy::evaluate(
            invalidConditions
        );

        for (const auto& failure : rejected) {
            std::cout << "- " << failure << '\n';
        }

        std::cout << "\nRunning validation tests\n";
        runTests();

    } catch (const std::exception& error) {
        std::cerr << "Execution error: "
                  << error.what() << '\n';

        return 1;
    }

    return 0;
}
