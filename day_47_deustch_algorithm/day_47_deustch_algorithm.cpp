#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository governance case study:
 * Deutsch's algorithm is used as a small, verifiable quantum
 * subroutine in a hypothetical review-policy experiment.
 *
 * The quantum task is deliberately kept separate from repository
 * governance itself. The oracle represents a promised binary policy
 * classification, not an actual GitHub branch-protection API.
 *
 * The case study compares a deterministic classical oracle strategy
 * with the Deutsch circuit and validates the circuit's measurement.
 */

using Complex = std::complex<double>;
using State = std::array<Complex, 4>;

constexpr double EPSILON = 1e-9;
constexpr double INV_SQRT2 = 0.70710678118654752440;

struct BooleanOracle {
    int f0;
    int f1;
    std::string name;

    BooleanOracle(int first, int second, std::string label)
        : f0(first), f1(second), name(std::move(label)) {
        if ((f0 != 0 && f0 != 1) || (f1 != 0 && f1 != 1)) {
            throw std::invalid_argument("Oracle outputs must be bits.");
        }
    }

    int evaluate(int input) const {
        if (input != 0 && input != 1) {
            throw std::out_of_range("Oracle input must be zero or one.");
        }
        return input == 0 ? f0 : f1;
    }

    bool isConstant() const {
        return f0 == f1;
    }

    std::string classification() const {
        return isConstant() ? "constant" : "balanced";
    }
};

double normSquared(const State& state) {
    double result = 0.0;
    for (const auto& amplitude : state) {
        result += std::norm(amplitude);
    }
    return result;
}

void validateState(const State& state) {
    for (const auto& amplitude : state) {
        if (!std::isfinite(amplitude.real()) ||
            !std::isfinite(amplitude.imag())) {
            throw std::runtime_error("State contains non-finite amplitudes.");
        }
    }

    if (std::abs(normSquared(state) - 1.0) > EPSILON) {
        throw std::runtime_error("State vector is not normalized.");
    }
}

State basisZero() {
    State state{};
    state[0] = Complex(1.0, 0.0);
    return state;
}

State applySingleQubitGate(
    const State& state,
    int qubit,
    const std::array<std::array<double, 2>, 2>& gate
) {
    if (qubit < 0 || qubit > 1) {
        throw std::out_of_range("Deutsch circuit has two qubits.");
    }

    State result{};
    const int mask = 1 << qubit;

    for (int index = 0; index < 4; ++index) {
        if ((index & mask) != 0) {
            continue;
        }

        const int paired = index | mask;
        const Complex zero = state[index];
        const Complex one = state[paired];

        result[index] =
            gate[0][0] * zero + gate[0][1] * one;
        result[paired] =
            gate[1][0] * zero + gate[1][1] * one;
    }

    validateState(result);
    return result;
}

const std::array<std::array<double, 2>, 2> HADAMARD{{
    {{INV_SQRT2, INV_SQRT2}},
    {{INV_SQRT2, -INV_SQRT2}}
}};

const std::array<std::array<double, 2>, 2> PAULI_X{{
    {{0.0, 1.0}},
    {{1.0, 0.0}}
}};

State applyOracle(const State& state, const BooleanOracle& oracle) {
    State result{};

    for (int index = 0; index < 4; ++index) {
        const int input = index & 1;
        const int ancilla = (index >> 1) & 1;
        const int target = ancilla ^ oracle.evaluate(input);
        const int destination = input | (target << 1);

        // The XOR target operation is a permutation of basis states.
        // It therefore preserves amplitudes, norms, and reversibility.
        result[destination] += state[index];
    }

    validateState(result);
    return result;
}

struct CircuitResult {
    State finalState;
    double probabilityInputZero;
    double probabilityInputOne;
    std::string classification;
    int oracleCalls;
};

CircuitResult runDeutschCircuit(const BooleanOracle& oracle) {
    State state = basisZero();

    // The ancilla is flipped to |1>; Hadamards then create |+>|->.
    state = applySingleQubitGate(state, 1, PAULI_X);
    state = applySingleQubitGate(state, 0, HADAMARD);
    state = applySingleQubitGate(state, 1, HADAMARD);

    state = applyOracle(state, oracle);

    // Interference on the input qubit reveals the parity of the
    // two oracle outputs in one invocation of the black-box oracle.
    state = applySingleQubitGate(state, 0, HADAMARD);

    double probabilityZero = 0.0;
    double probabilityOne = 0.0;

    for (int index = 0; index < 4; ++index) {
        if ((index & 1) == 0) {
            probabilityZero += std::norm(state[index]);
        } else {
            probabilityOne += std::norm(state[index]);
        }
    }

    const std::string classification =
        probabilityZero > 0.5 ? "constant" : "balanced";

    return {
        state,
        probabilityZero,
        probabilityOne,
        classification,
        1
    };
}

struct ClassicalResult {
    std::string classification;
    int oracleCalls;
};

ClassicalResult classifyClassically(const BooleanOracle& oracle) {
    // No deterministic classical strategy can infer the promised
    // category from one bit alone; the other input must be queried.
    const int first = oracle.evaluate(0);
    const int second = oracle.evaluate(1);

    return {
        first == second ? "constant" : "balanced",
        2
    };
}

struct RepositoryPolicyExperiment {
    std::string repository;
    std::string protectedBranch;
    int requiredApprovals;
    bool checksPassing;
    bool conversationsResolved;
    bool directPushAllowed;

    void validate() const {
        if (repository.empty() || protectedBranch.empty()) {
            throw std::invalid_argument(
                "Repository and protected branch are required."
            );
        }

        if (requiredApprovals < 0 || requiredApprovals > 20) {
            throw std::invalid_argument(
                "Required approvals must lie between zero and twenty."
            );
        }
    }

    bool mergeEligible(
        int validApprovals,
        bool hasStaleApproval,
        bool linearHistory
    ) const {
        validate();

        if (validApprovals < 0) {
            throw std::invalid_argument("Approval count cannot be negative.");
        }

        // These are ordinary deterministic policy checks. They are not
        // evaluated by Deutsch's quantum oracle.
        return validApprovals >= requiredApprovals
            && !hasStaleApproval
            && checksPassing
            && conversationsResolved
            && linearHistory;
    }
};

void printCircuitResult(const BooleanOracle& oracle) {
    const auto quantum = runDeutschCircuit(oracle);
    const auto classical = classifyClassically(oracle);

    std::cout << std::left << std::setw(12) << oracle.name
              << std::setw(12) << oracle.classification()
              << " quantum_calls=" << quantum.oracleCalls
              << " quantum_result=" << quantum.classification
              << " P(0)=" << std::fixed << std::setprecision(3)
              << quantum.probabilityInputZero
              << " classical_calls=" << classical.oracleCalls
              << '\n';

    if (quantum.classification != oracle.classification()) {
        throw std::runtime_error("Quantum classification failed.");
    }

    if (std::abs(
            quantum.probabilityInputZero
            + quantum.probabilityInputOne - 1.0
        ) > EPSILON) {
        throw std::runtime_error("Measurement probabilities do not sum to one.");
    }
}

void runGovernanceCaseStudy() {
    std::cout << "\nRepository policy case study\n";

    RepositoryPolicyExperiment policy{
        "payment-service",
        "main",
        2,
        true,
        true,
        false
    };

    policy.validate();

    const bool eligible = policy.mergeEligible(
        2,
        false,
        true
    );

    std::cout << "Repository: " << policy.repository << '\n';
    std::cout << "Protected branch: " << policy.protectedBranch << '\n';
    std::cout << "Required approvals: " << policy.requiredApprovals << '\n';
    std::cout << "Direct pushes allowed: "
              << std::boolalpha << policy.directPushAllowed << '\n';
    std::cout << "Pull request merge eligible: "
              << policy.mergeEligible(2, false, true) << '\n';

    // The algorithm's oracle speedup does not automatically accelerate
    // branch-protection enforcement. Policy evaluation remains classical.
    std::cout << "Deutsch result is a mathematical query-complexity "
                 "demonstration, not a repository security control.\n";

    if (!eligible) {
        throw std::runtime_error("Expected policy fixture to be eligible.");
    }

    const bool staleApprovalRejected =
        !policy.mergeEligible(2, true, true);
    const bool failedCheckRejected = [&policy]() {
        auto failing = policy;
        failing.checksPassing = false;
        return !failing.mergeEligible(2, false, true);
    }();

    const bool unresolvedConversationRejected = [&policy]() {
        auto unresolved = policy;
        unresolved.conversationsResolved = false;
        return !unresolved.mergeEligible(2, false, true);
    }();

    if (!staleApprovalRejected ||
        !failedCheckRejected ||
        !unresolvedConversationRejected) {
        throw std::runtime_error("Policy failure condition was not enforced.");
    }

    std::cout << "Stale approval, failed checks, and unresolved "
                 "conversations correctly block merging.\n";
}

int main() {
    try {
        std::cout << "DEUTSCH ALGORITHM: QUANTUM QUERY CASE STUDY\n";
        std::cout << "Truth-table classification\n";

        const std::vector<BooleanOracle> oracles{
            {0, 0, "zero"},
            {0, 1, "identity"},
            {1, 0, "negation"},
            {1, 1, "one"}
        };

        for (const auto& oracle : oracles) {
            printCircuitResult(oracle);
        }

        runGovernanceCaseStudy();

        std::cout << "\nAll circuit and policy assertions passed.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Execution failed: " << error.what() << '\n';
        return 1;
    }
}
