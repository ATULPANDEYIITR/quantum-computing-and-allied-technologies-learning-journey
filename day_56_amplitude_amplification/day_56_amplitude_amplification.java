import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class GeneralizedQuantumSearch {

    enum ReviewState {
        PENDING,
        APPROVED,
        CHANGES_REQUESTED,
        DISMISSED
    }

    enum MergeState {
        OPEN,
        DRAFT,
        CLOSED,
        MERGED
    }

    record SearchProblem(
            int qubits,
            Set<Integer> markedStates,
            double targetProbability) {

        SearchProblem {
            if (qubits < 1 || qubits > 20) {
                throw new IllegalArgumentException(
                        "Qubit count must be between 1 and 20.");
            }

            int dimension = 1 << qubits;

            if (markedStates == null || markedStates.isEmpty()) {
                throw new IllegalArgumentException(
                        "At least one marked state is required.");
            }

            for (int state : markedStates) {
                if (state < 0 || state >= dimension) {
                    throw new IllegalArgumentException(
                            "Marked state is outside the search space.");
                }
            }

            if (!(targetProbability > 0.0 && targetProbability <= 1.0)) {
                throw new IllegalArgumentException(
                        "Target probability must be in (0,1].");
            }

            markedStates = Set.copyOf(markedStates);
        }

        int dimension() {
            return 1 << qubits;
        }

        double initialProbability() {
            return (double) markedStates.size() / dimension();
        }

        double theta() {
            return Math.asin(Math.sqrt(initialProbability()));
        }
    }

    record AmplificationStep(
            int iteration,
            double goodAmplitude,
            double badAmplitude,
            double successProbability) {
    }

    record Review(
            String reviewer,
            ReviewState state,
            boolean eligible,
            boolean stale) {
    }

    record StatusCheck(
            String name,
            boolean passed) {
    }

    record BranchProtectionPolicy(
            int requiredApprovals,
            boolean requirePassingChecks,
            boolean requireResolvedConversations,
            boolean prohibitDirectPush,
            boolean requireLinearHistory) {
    }

    static final class PullRequest {
        private final String id;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Review> reviews;
        private final List<StatusCheck> checks;
        private final BranchProtectionPolicy policy;
        private MergeState state;
        private boolean mergeConflict;
        private boolean synchronizedWithTarget;
        private boolean conversationsResolved;
        private boolean linearHistory;

        PullRequest(
                String id,
                String sourceBranch,
                String targetBranch,
                BranchProtectionPolicy policy) {

            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("PR id is required.");
            }

            if (sourceBranch == null || targetBranch == null ||
                    sourceBranch.isBlank() || targetBranch.isBlank() ||
                    sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                        "Source and target branches must be distinct.");
            }

            this.id = id;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.policy = policy;
            this.reviews = new ArrayList<>();
            this.checks = new ArrayList<>();
            this.state = MergeState.OPEN;
        }

        void addReview(Review review) {
            if (state == MergeState.CLOSED || state == MergeState.MERGED) {
                throw new IllegalStateException(
                        "Reviews cannot be changed after closure or merge.");
            }

            reviews.add(review);
        }

        void addStatusCheck(StatusCheck check) {
            checks.add(check);
        }

        void setMergeConflict(boolean value) {
            mergeConflict = value;
        }

        void setSynchronizedWithTarget(boolean value) {
            synchronizedWithTarget = value;
        }

        void setConversationsResolved(boolean value) {
            conversationsResolved = value;
        }

        void setLinearHistory(boolean value) {
            linearHistory = value;
        }

        void transitionTo(MergeState next) {
            if (next == MergeState.MERGED &&
                    evaluateEligibility().isRejected()) {
                throw new IllegalStateException(
                        "PR cannot transition to MERGED.");
            }

            if (state == MergeState.MERGED) {
                throw new IllegalStateException(
                        "A merged PR cannot change state.");
            }

            state = next;
        }

        MergeEligibility evaluateEligibility() {
            List<String> failures = new ArrayList<>();

            if (state == MergeState.DRAFT) {
                failures.add("Pull Request is still a draft.");
            }

            if (state == MergeState.CLOSED) {
                failures.add("Pull Request is closed.");
            }

            if (mergeConflict) {
                failures.add("Merge conflict exists.");
            }

            if (!synchronizedWithTarget) {
                failures.add("Source branch is not synchronized.");
            }

            if (policy.requireResolvedConversations() &&
                    !conversationsResolved) {
                failures.add("Review conversations are unresolved.");
            }

            if (policy.requireLinearHistory() && !linearHistory) {
                failures.add("Required linear history is absent.");
            }

            long approvals = reviews.stream()
                    .filter(Review::eligible)
                    .filter(review -> !review.stale())
                    .filter(review -> review.state() == ReviewState.APPROVED)
                    .map(Review::reviewer)
                    .distinct()
                    .count();

            if (approvals < policy.requiredApprovals()) {
                failures.add(
                        "Required eligible approvals are not satisfied.");
            }

            if (policy.requirePassingChecks()) {
                boolean allPassed = !checks.isEmpty() &&
                        checks.stream().allMatch(StatusCheck::passed);

                if (!allPassed) {
                    failures.add("Required status checks are not passing.");
                }
            }

            return failures.isEmpty()
                    ? MergeEligibility.approved()
                    : MergeEligibility.rejected(failures);
        }

        String id() {
            return id;
        }
    }

    record MergeEligibility(
            boolean eligible,
            List<String> reasons) {

        static MergeEligibility approved() {
            return new MergeEligibility(true, List.of());
        }

        static MergeEligibility rejected(List<String> reasons) {
            return new MergeEligibility(false, List.copyOf(reasons));
        }

        boolean isRejected() {
            return !eligible;
        }
    }

    static final class AmplificationService {
        private final SearchProblem problem;

        AmplificationService(SearchProblem problem) {
            this.problem = problem;
        }

        double probability(int iteration) {
            if (iteration < 0) {
                throw new IllegalArgumentException(
                        "Iteration cannot be negative.");
            }

            double angle =
                    (2.0 * iteration + 1.0) * problem.theta();

            return Math.pow(Math.sin(angle), 2);
        }

        int optimalIterations() {
            double estimate =
                    Math.PI / (4.0 * problem.theta()) - 0.5;

            int base = Math.max(0, (int) Math.floor(estimate));
            int best = base;

            for (int candidate : new int[] {base, base + 1}) {
                if (probability(candidate) > probability(best)) {
                    best = candidate;
                }
            }

            return best;
        }

        List<AmplificationStep> trajectory(int iterations) {
            if (iterations < 0) {
                throw new IllegalArgumentException(
                        "Iterations cannot be negative.");
            }

            List<AmplificationStep> result = new ArrayList<>();

            for (int k = 0; k <= iterations; k++) {
                double angle =
                        (2.0 * k + 1.0) * problem.theta();

                result.add(new AmplificationStep(
                        k,
                        Math.sin(angle),
                        Math.cos(angle),
                        Math.pow(Math.sin(angle), 2)));
            }

            return List.copyOf(result);
        }
    }

    public static void main(String[] args) {
        SearchProblem problem = new SearchProblem(
                8,
                Set.of(5, 44, 91, 177),
                0.90);

        AmplificationService service =
                new AmplificationService(problem);

        int optimal = service.optimalIterations();

        System.out.println("Generalized Amplitude Amplification");
        System.out.println("===================================");
        System.out.println("Search space: " + problem.dimension());
        System.out.println("Marked states: " + problem.markedStates());
        System.out.printf(
                "Initial probability: %.6f%n",
                problem.initialProbability());
        System.out.println("Optimal iterations: " + optimal);

        System.out.println("\nk\tgood\tbad\tprobability");

        for (AmplificationStep step : service.trajectory(optimal)) {
            System.out.printf(
                    "%d\t%.6f\t%.6f\t%.6f%n",
                    step.iteration(),
                    step.goodAmplitude(),
                    step.badAmplitude(),
                    step.successProbability());
        }

        BranchProtectionPolicy policy =
                new BranchProtectionPolicy(
                        2,
                        true,
                        true,
                        true,
                        true);

        PullRequest pullRequest = new PullRequest(
                "PR-2048",
                "feature/amplitude-search",
                "main",
                policy);

        pullRequest.addReview(
                new Review("alice", ReviewState.APPROVED, true, false));

        pullRequest.addReview(
                new Review("bob", ReviewState.APPROVED, true, false));

        pullRequest.addReview(
                new Review("former-reviewer",
                        ReviewState.APPROVED,
                        false,
                        false));

        pullRequest.addStatusCheck(
                new StatusCheck("unit-tests", true));

        pullRequest.addStatusCheck(
                new StatusCheck("quantum-regression", true));

        pullRequest.setSynchronizedWithTarget(true);
        pullRequest.setConversationsResolved(true);
        pullRequest.setLinearHistory(true);
        pullRequest.setMergeConflict(false);

        MergeEligibility eligibility =
                pullRequest.evaluateEligibility();

        System.out.println("\nEnterprise Merge Eligibility");
        System.out.println("============================");
        System.out.println("Pull Request: " + pullRequest.id());
        System.out.println("Eligible: " + eligibility.eligible());

        if (!eligibility.eligible()) {
            eligibility.reasons().forEach(
                    reason -> System.out.println("- " + reason));
        } else {
            pullRequest.transitionTo(MergeState.MERGED);
            System.out.println("State transition: OPEN -> MERGED");
        }

        /*
         * A stale approval demonstrates that approval existence alone does
         * not imply merge eligibility.
         */
        PullRequest staleApprovalExample = new PullRequest(
                "PR-2049",
                "feature/search-optimization",
                "main",
                policy);

        staleApprovalExample.addReview(
                new Review("alice", ReviewState.APPROVED, true, true));

        staleApprovalExample.addReview(
                new Review("bob",
                        ReviewState.CHANGES_REQUESTED,
                        true,
                        false));

        staleApprovalExample.addStatusCheck(
                new StatusCheck("unit-tests", true));

        staleApprovalExample.setSynchronizedWithTarget(true);
        staleApprovalExample.setConversationsResolved(true);
        staleApprovalExample.setLinearHistory(true);

        MergeEligibility rejected =
                staleApprovalExample.evaluateEligibility();

        System.out.println("\nStale Approval Scenario");
        System.out.println("=======================");
        System.out.println("Eligible: " + rejected.eligible());
        rejected.reasons().forEach(
                reason -> System.out.println("- " + reason));

        // Every state marked means no search amplification is necessary.
        SearchProblem trivial = new SearchProblem(
                3,
                Set.of(0, 1, 2, 3, 4, 5, 6, 7),
                0.99);

        AmplificationService trivialService =
                new AmplificationService(trivial);

        if (trivialService.optimalIterations() != 0 ||
                Math.abs(trivialService.probability(0) - 1.0) > 1e-12) {
            throw new IllegalStateException(
                    "All-marked search invariant failed.");
        }
    }
}
