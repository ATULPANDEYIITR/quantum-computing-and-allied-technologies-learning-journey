#include <algorithm>
#include <cmath>
#include <cstddef>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class MergeDecision {
    Eligible,
    Rejected
};

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested,
    Dismissed
};

struct Review {
    std::string reviewer;
    ReviewState state;
    bool eligible;
};

struct StatusCheck {
    std::string name;
    bool passed;
};

struct BranchPolicy {
    std::size_t requiredApprovals;
    bool requireAllChecks;
    bool requireLinearHistory;
};

struct PullRequest {
    std::string id;
    std::string sourceBranch;
    std::string targetBranch;
    std::set<int> changedStates;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    bool draft;
    bool mergeConflict;
    bool conversationsResolved;
    bool branchSynchronized;
    bool closed;
};

struct SearchParameters {
    std::size_t qubits;
    std::set<int> markedStates;
    double targetProbability;
};

struct AmplificationPoint {
    std::size_t iteration;
    double goodAmplitude;
    double badAmplitude;
    double successProbability;
};

class SearchError : public std::runtime_error {
public:
    explicit SearchError(const std::string& message)
        : std::runtime_error(message) {}
};

class AmplitudeAmplificationEngine {
private:
    SearchParameters parameters_;

    double theta() const {
        const double n = static_cast<double>(std::size_t{1} << parameters_.qubits);
        const double m = static_cast<double>(parameters_.markedStates.size());
        return std::asin(std::sqrt(m / n));
    }

public:
    explicit AmplitudeAmplificationEngine(SearchParameters parameters)
        : parameters_(std::move(parameters)) {
        validate();
    }

    void validate() const {
        if (parameters_.qubits == 0 || parameters_.qubits > 20) {
            throw SearchError("Qubit count must be between 1 and 20.");
        }

        const std::size_t dimension = std::size_t{1} << parameters_.qubits;

        if (parameters_.markedStates.empty()) {
            throw SearchError("At least one marked state is required.");
        }

        for (int state : parameters_.markedStates) {
            if (state < 0 || static_cast<std::size_t>(state) >= dimension) {
                throw SearchError("A marked state is outside the search space.");
            }
        }

        if (!(parameters_.targetProbability > 0.0 &&
              parameters_.targetProbability <= 1.0)) {
            throw SearchError("Target probability must be in (0,1].");
        }
    }

    double probability(std::size_t iteration) const {
        const double angle =
            (2.0 * static_cast<double>(iteration) + 1.0) * theta();

        return std::pow(std::sin(angle), 2.0);
    }

    std::size_t optimalIterations() const {
        const double estimate =
            M_PI / (4.0 * theta()) - 0.5;

        const long long base =
            static_cast<long long>(std::floor(estimate));

        std::vector<std::size_t> candidates;
        candidates.push_back(
            static_cast<std::size_t>(std::max<long long>(0, base))
        );
        candidates.push_back(
            static_cast<std::size_t>(std::max<long long>(0, base + 1))
        );

        std::size_t best = candidates.front();

        for (std::size_t candidate : candidates) {
            if (probability(candidate) > probability(best)) {
                best = candidate;
            }
        }

        return best;
    }

    std::vector<AmplificationPoint> trajectory(
        std::size_t iterations
    ) const {
        std::vector<AmplificationPoint> result;
        result.reserve(iterations + 1);

        for (std::size_t k = 0; k <= iterations; ++k) {
            const double angle =
                (2.0 * static_cast<double>(k) + 1.0) * theta();

            result.push_back({
                k,
                std::sin(angle),
                std::cos(angle),
                std::pow(std::sin(angle), 2.0)
            });
        }

        return result;
    }
};

class RepositoryGovernanceEngine {
public:
    static bool hasRequiredApprovals(
        const PullRequest& pr,
        const BranchPolicy& policy
    ) {
        std::set<std::string> approvingReviewers;

        for (const Review& review : pr.reviews) {
            if (review.eligible &&
                review.state == ReviewState::Approved) {
                approvingReviewers.insert(review.reviewer);
            }
        }

        return approvingReviewers.size() >= policy.requiredApprovals;
    }

    static bool checksPass(
        const PullRequest& pr,
        const BranchPolicy& policy
    ) {
        if (!policy.requireAllChecks) {
            return true;
        }

        return std::all_of(
            pr.checks.begin(),
            pr.checks.end(),
            [](const StatusCheck& check) {
                return check.passed;
            }
        );
    }

    static MergeDecision evaluate(
        const PullRequest& pr,
        const BranchPolicy& policy
    ) {
        if (pr.closed || pr.draft) {
            return MergeDecision::Rejected;
        }

        if (pr.sourceBranch.empty() ||
            pr.targetBranch.empty() ||
            pr.sourceBranch == pr.targetBranch) {
            return MergeDecision::Rejected;
        }

        if (pr.mergeConflict ||
            !pr.branchSynchronized ||
            !pr.conversationsResolved) {
            return MergeDecision::Rejected;
        }

        if (!hasRequiredApprovals(pr, policy)) {
            return MergeDecision::Rejected;
        }

        if (!checksPass(pr, policy)) {
            return MergeDecision::Rejected;
        }

        return MergeDecision::Eligible;
    }
};

static void printQuantumReport(
    const AmplitudeAmplificationEngine& engine
) {
    const std::size_t optimal = engine.optimalIterations();
    const auto trajectory = engine.trajectory(optimal);

    std::cout << "\nGeneralized Amplitude Amplification\n";
    std::cout << "==================================\n";
    std::cout << "Optimal iterations: " << optimal << "\n";
    std::cout << "k\tgood\tbad\tprobability\n";

    std::cout << std::fixed << std::setprecision(6);

    for (const auto& point : trajectory) {
        std::cout
            << point.iteration << '\t'
            << point.goodAmplitude << '\t'
            << point.badAmplitude << '\t'
            << point.successProbability << '\n';
    }
}

static void printGovernanceReport(
    const PullRequest& pr,
    const BranchPolicy& policy
) {
    const MergeDecision decision =
        RepositoryGovernanceEngine::evaluate(pr, policy);

    std::cout << "\nRepository Merge Eligibility\n";
    std::cout << "============================\n";
    std::cout
        << "PR " << pr.id << ": "
        << (decision == MergeDecision::Eligible
                ? "ELIGIBLE"
                : "REJECTED")
        << '\n';
}

int main() {
    try {
        /*
         * The quantum model treats the marked subspace as the "good" state.
         * Each Grover iteration rotates the state by 2*theta.
         */
        SearchParameters parameters{
            10,
            {17, 211, 512, 777},
            0.90
        };

        AmplitudeAmplificationEngine engine(parameters);
        printQuantumReport(engine);

        /*
         * A generalized search can represent multiple valid answers.
         * The complexity is approximately O(sqrt(N/M)) oracle applications.
         */
        for (std::size_t markedCount : {1U, 2U, 4U, 8U, 16U, 32U}) {
            std::set<int> states;

            for (std::size_t i = 0; i < markedCount; ++i) {
                states.insert(static_cast<int>(i));
            }

            SearchParameters experiment{
                10,
                states,
                0.90
            };

            AmplitudeAmplificationEngine experimentEngine(experiment);

            std::cout
                << "M=" << markedCount
                << ", k=" << experimentEngine.optimalIterations()
                << ", P="
                << std::fixed << std::setprecision(6)
                << experimentEngine.probability(
                    experimentEngine.optimalIterations())
                << '\n';
        }

        BranchPolicy policy{
            2,
            true,
            true
        };

        PullRequest pr{
            "PR-1042",
            "feature/generalized-search",
            "main",
            {17, 211, 512},
            {
                {"alice", ReviewState::Approved, true},
                {"bob", ReviewState::Approved, true},
                {"carol", ReviewState::Approved, false}
            },
            {
                {"unit-tests", true},
                {"security-scan", true},
                {"quantum-regression", true}
            },
            false,
            false,
            true,
            true,
            false
        };

        printGovernanceReport(pr, policy);

        // Stale or ineligible approval cannot satisfy the required count.
        pr.reviews[0].eligible = false;
        printGovernanceReport(pr, policy);

        // The edge case M=N requires no amplification.
        SearchParameters allMarked{
            3,
            {0, 1, 2, 3, 4, 5, 6, 7},
            0.99
        };

        AmplitudeAmplificationEngine trivial(allMarked);

        if (trivial.optimalIterations() != 0 ||
            std::abs(trivial.probability(0) - 1.0) > 1e-12) {
            throw SearchError("All-marked search invariant failed.");
        }

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr << "Execution failure: "
                  << error.what()
                  << '\n';
        return 1;
    }
}
