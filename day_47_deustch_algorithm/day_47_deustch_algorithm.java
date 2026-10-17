import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * Enterprise-oriented Deutsch algorithm model.
 *
 * The program represents the promised Boolean-function classification
 * as a quantum circuit service, then integrates its output into a
 * separate repository-policy demonstration.
 *
 * The repository policy remains a conventional deterministic service.
 * A Deutsch circuit does not replace access control, required reviews,
 * approval validation, or branch-protection enforcement.
 *
 * Compile: javac DeutschGovernance.java
 * Run:     java DeutschGovernance
 */
public final class DeutschGovernance {

    private static final double EPSILON = 1e-9;
    private static final double INV_SQRT_TWO = 1.0 / Math.sqrt(2.0);

    private DeutschGovernance() {
    }

    enum Classification {
        CONSTANT,
        BALANCED
    }

    enum ReviewState {
        COMMENTED,
        APPROVED,
        CHANGES_REQUESTED
    }

    enum CheckState {
        PENDING,
        PASSED,
        FAILED
    }

    record BooleanOracle(int outputZero, int outputOne, String name) {
        BooleanOracle {
            if (!isBit(outputZero) || !isBit(outputOne)) {
                throw new IllegalArgumentException(
                    "Boolean oracle outputs must be zero or one."
                );
            }
            Objects.requireNonNull(name, "Oracle name is required.");
            if (name.isBlank()) {
                throw new IllegalArgumentException("Oracle name cannot be blank.");
            }
        }

        int evaluate(int input) {
            if (!isBit(input)) {
                throw new IllegalArgumentException("Input must be a bit.");
            }
            return input == 0 ? outputZero : outputOne;
        }

        Classification classification() {
            return outputZero == outputOne
                ? Classification.CONSTANT
                : Classification.BALANCED;
        }

        private static boolean isBit(int value) {
            return value == 0 || value == 1;
        }
    }

    static final class QuantumState {
        private final double[] real;
        private final double[] imaginary;

        QuantumState(int dimension) {
            if (dimension < 2 || (dimension & (dimension - 1)) != 0) {
                throw new IllegalArgumentException(
                    "State dimension must be a power of two."
                );
            }
            this.real = new double[dimension];
            this.imaginary = new double[dimension];
        }

        private QuantumState(double[] real, double[] imaginary) {
            if (real.length != imaginary.length) {
                throw new IllegalArgumentException("Amplitude arrays differ.");
            }
            this.real = real.clone();
            this.imaginary = imaginary.clone();
        }

        static QuantumState zeroState(int qubits) {
            if (qubits < 1 || qubits > 20) {
                throw new IllegalArgumentException("Unsupported qubit count.");
            }
            QuantumState state = new QuantumState(1 << qubits);
            state.real[0] = 1.0;
            return state;
        }

        QuantumState copy() {
            return new QuantumState(real, imaginary);
        }

        int dimension() {
            return real.length;
        }

        double normSquared() {
            double total = 0.0;
            for (int index = 0; index < real.length; index++) {
                total += real[index] * real[index]
                    + imaginary[index] * imaginary[index];
            }
            return total;
        }

        void validate(int qubits) {
            if (dimension() != (1 << qubits)) {
                throw new IllegalStateException("Unexpected state dimension.");
            }

            for (int index = 0; index < dimension(); index++) {
                if (!Double.isFinite(real[index])
                    || !Double.isFinite(imaginary[index])) {
                    throw new IllegalStateException("Non-finite amplitude.");
                }
            }

            if (Math.abs(normSquared() - 1.0) > EPSILON) {
                throw new IllegalStateException("State is not normalized.");
            }
        }

        double probabilityOfQubitZero(int qubit) {
            if (qubit < 0 || qubit >= Integer.numberOfTrailingZeros(
                    Integer.highestOneBit(dimension()))) {
                throw new IllegalArgumentException("Invalid qubit index.");
            }

            double probability = 0.0;
            int mask = 1 << qubit;

            for (int index = 0; index < dimension(); index++) {
                if ((index & mask) == 0) {
                    probability += real[index] * real[index]
                        + imaginary[index] * imaginary[index];
                }
            }

            return probability;
        }
    }

    @FunctionalInterface
    interface QuantumGate {
        QuantumState apply(QuantumState input);
    }

    static QuantumGate hadamard(int qubit, int qubits) {
        return state -> applySingleQubitGate(
            state,
            qubit,
            new double[][] {
                {INV_SQRT_TWO, INV_SQRT_TWO},
                {INV_SQRT_TWO, -INV_SQRT_TWO}
            },
            qubits
        );
    }

    static QuantumGate pauliX(int qubit, int qubits) {
        return state -> applySingleQubitGate(
            state,
            qubit,
            new double[][] {{0.0, 1.0}, {1.0, 0.0}},
            qubits
        );
    }

    static QuantumState applySingleQubitGate(
        QuantumState input,
        int qubit,
        double[][] gate,
        int qubits
    ) {
        if (qubit < 0 || qubit >= qubits) {
            throw new IllegalArgumentException("Qubit index is invalid.");
        }
        if (gate.length != 2 || gate[0].length != 2
            || gate[1].length != 2) {
            throw new IllegalArgumentException("Gate must be a 2x2 matrix.");
        }

        QuantumState output = new QuantumState(input.dimension());
        int mask = 1 << qubit;

        for (int index = 0; index < input.dimension(); index++) {
            if ((index & mask) != 0) {
                continue;
            }

            int paired = index | mask;
            output.real[index] =
                gate[0][0] * input.real[index]
                    + gate[0][1] * input.real[paired];
            output.imaginary[index] =
                gate[0][0] * input.imaginary[index]
                    + gate[0][1] * input.imaginary[paired];

            output.real[paired] =
                gate[1][0] * input.real[index]
                    + gate[1][1] * input.real[paired];
            output.imaginary[paired] =
                gate[1][0] * input.imaginary[index]
                    + gate[1][1] * input.imaginary[paired];
        }

        output.validate(qubits);
        return output;
    }

    static QuantumState applyOracle(
        QuantumState input,
        BooleanOracle oracle
    ) {
        if (input.dimension() != 4) {
            throw new IllegalArgumentException(
                "Deutsch oracle requires two qubits."
            );
        }

        QuantumState output = new QuantumState(4);

        for (int index = 0; index < 4; index++) {
            int x = index & 1;
            int y = (index >> 1) & 1;
            int newY = y ^ oracle.evaluate(x);
            int destination = x | (newY << 1);

            output.real[destination] += input.real[index];
            output.imaginary[destination] += input.imaginary[index];
        }

        output.validate(2);
        return output;
    }

    record CircuitResult(
        Classification classification,
        double probabilityZero,
        double probabilityOne,
        int oracleCalls,
        List<String> operations
    ) {
        CircuitResult {
            Objects.requireNonNull(classification);
            operations = List.copyOf(operations);

            if (Math.abs(probabilityZero + probabilityOne - 1.0) > EPSILON) {
                throw new IllegalArgumentException(
                    "Measurement probabilities must sum to one."
                );
            }
        }
    }

    static final class DeutschCircuitService {
        CircuitResult classify(BooleanOracle oracle) {
            Objects.requireNonNull(oracle, "Oracle is required.");

            List<String> operations = new ArrayList<>();
            QuantumState state = QuantumState.zeroState(2);

            // Prepare the target ancilla in |1> before phase kickback.
            state = pauliX(1, 2).apply(state);
            state = hadamard(0, 2).apply(state);
            state = hadamard(1, 2).apply(state);
            operations.add("Prepare |+>|->");

            state = applyOracle(state, oracle);
            operations.add("One reversible oracle invocation");

            state = hadamard(0, 2).apply(state);
            operations.add("Interfere with final input Hadamard");

            double probabilityZero = state.probabilityOfQubitZero(0);
            double probabilityOne = 1.0 - probabilityZero;

            Classification result = probabilityZero > 0.5
                ? Classification.CONSTANT
                : Classification.BALANCED;

            return new CircuitResult(
                result,
                probabilityZero,
                probabilityOne,
                1,
                operations
            );
        }
    }

    record ReviewRecord(
        String reviewer,
        ReviewState state,
        boolean eligibleReviewer,
        boolean stale
    ) {
        ReviewRecord {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer is required.");
            }
            Objects.requireNonNull(state);
        }
    }

    record BranchProtectionPolicy(
        int requiredApprovals,
        boolean requirePassingChecks,
        boolean requireResolvedConversations,
        boolean requireLinearHistory,
        boolean restrictDirectPushes,
        boolean preventForcePush,
        boolean preventDeletion,
        Set<String> allowedMergeStrategies
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0 || requiredApprovals > 20) {
                throw new IllegalArgumentException(
                    "Approval requirement must be between zero and twenty."
                );
            }

            allowedMergeStrategies = Set.copyOf(allowedMergeStrategies);

            if (allowedMergeStrategies.isEmpty()) {
                throw new IllegalArgumentException(
                    "At least one merge strategy must be permitted."
                );
            }
        }
    }

    record PullRequest(
        String id,
        String sourceBranch,
        String targetBranch,
        boolean draft,
        boolean open,
        boolean baseSynchronized,
        boolean conversationsResolved,
        boolean linearHistorySatisfied,
        String mergeStrategy,
        List<ReviewRecord> reviews,
        List<CheckState> requiredChecks
    ) {
        PullRequest {
            for (String value : List.of(id, sourceBranch, targetBranch,
                    mergeStrategy)) {
                if (value == null || value.isBlank()) {
                    throw new IllegalArgumentException(
                        "Pull request identifiers and branches are required."
                    );
                }
            }

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must differ."
                );
            }

            reviews = List.copyOf(reviews);
            requiredChecks = List.copyOf(requiredChecks);
        }
    }

    record MergeDecision(
        boolean eligible,
        List<String> blockingReasons,
        int eligibleApprovals
    ) {
        MergeDecision {
            blockingReasons = List.copyOf(blockingReasons);
        }
    }

    static final class MergeEligibilityService {
        MergeDecision evaluate(
            PullRequest pullRequest,
            BranchProtectionPolicy policy
        ) {
            Objects.requireNonNull(pullRequest);
            Objects.requireNonNull(policy);

            List<String> blockers = new ArrayList<>();
            int validApprovals = 0;

            if (!pullRequest.open()) {
                blockers.add("Pull request is not open.");
            }
            if (pullRequest.draft()) {
                blockers.add("Draft pull requests cannot be merged.");
            }
            if (!pullRequest.baseSynchronized()) {
                blockers.add("Source branch is not synchronized with the base.");
            }
            if (!policy.allowedMergeStrategies().contains(
                    pullRequest.mergeStrategy())) {
                blockers.add("Merge strategy is not permitted.");
            }

            for (ReviewRecord review : pullRequest.reviews()) {
                if (!review.eligibleReviewer() || review.stale()) {
                    continue;
                }

                if (review.state() == ReviewState.APPROVED) {
                    validApprovals++;
                } else if (review.state() == ReviewState.CHANGES_REQUESTED) {
                    blockers.add(
                        "An eligible reviewer has requested changes."
                    );
                }
            }

            if (validApprovals < policy.requiredApprovals()) {
                blockers.add("Required approval count has not been reached.");
            }

            if (policy.requirePassingChecks()) {
                for (CheckState check : pullRequest.requiredChecks()) {
                    if (check != CheckState.PASSED) {
                        blockers.add(
                            "A required status check is pending or failed."
                        );
                        break;
                    }
                }
            }

            if (policy.requireResolvedConversations()
                    && !pullRequest.conversationsResolved()) {
                blockers.add("Review conversations remain unresolved.");
            }

            if (policy.requireLinearHistory()
                    && !pullRequest.linearHistorySatisfied()) {
                blockers.add("Linear history requirement is not satisfied.");
            }

            return new MergeDecision(
                blockers.isEmpty(),
                blockers,
                validApprovals
            );
        }
    }

    static void demonstrateQuantumCircuit() {
        System.out.println("Deutsch circuit truth-table verification");

        List<BooleanOracle> oracles = List.of(
            new BooleanOracle(0, 0, "zero"),
            new BooleanOracle(0, 1, "identity"),
            new BooleanOracle(1, 0, "negation"),
            new BooleanOracle(1, 1, "one")
        );

        DeutschCircuitService service = new DeutschCircuitService();

        for (BooleanOracle oracle : oracles) {
            CircuitResult result = service.classify(oracle);

            if (result.classification() != oracle.classification()) {
                throw new IllegalStateException(
                    "Circuit misclassified " + oracle.name()
                );
            }

            System.out.printf(
                "%-10s expected=%-8s observed=%-8s P(0)=%.1f queries=%d%n",
                oracle.name(),
                oracle.classification(),
                result.classification(),
                result.probabilityZero(),
                result.oracleCalls()
            );
        }
    }

    static void demonstrateGovernancePolicy() {
        System.out.println("\nEnterprise pull request governance");

        BranchProtectionPolicy policy = new BranchProtectionPolicy(
            2,
            true,
            true,
            true,
            true,
            true,
            true,
            Set.of("squash", "rebase")
        );

        List<ReviewRecord> reviews = List.of(
            new ReviewRecord("reviewer-a", ReviewState.APPROVED, true, false),
            new ReviewRecord("reviewer-b", ReviewState.APPROVED, true, false),
            new ReviewRecord("reviewer-c", ReviewState.APPROVED, false, false),
            new ReviewRecord("reviewer-d", ReviewState.APPROVED, true, true)
        );

        PullRequest pullRequest = new PullRequest(
            "PR-482",
            "feature/payment-validation",
            "main",
            false,
            true,
            true,
            true,
            true,
            "squash",
            reviews,
            List.of(CheckState.PASSED, CheckState.PASSED)
        );

        MergeDecision decision = new MergeEligibilityService().evaluate(
            pullRequest,
            policy
        );

        System.out.println("Pull request: " + pullRequest.id());
        System.out.println("Eligible approvals: " + decision.eligibleApprovals());
        System.out.println("Merge eligible: " + decision.eligible());

        if (!decision.eligible() || decision.eligibleApprovals() != 2) {
            throw new IllegalStateException(
                "Expected eligible pull request with two valid approvals."
            );
        }

        PullRequest blocked = new PullRequest(
            "PR-483",
            "feature/payment-validation-v2",
            "main",
            false,
            true,
            false,
            false,
            true,
            "merge-commit",
            reviews,
            List.of(CheckState.PASSED, CheckState.FAILED)
        );

        MergeDecision blockedDecision =
            new MergeEligibilityService().evaluate(blocked, policy);

        if (blockedDecision.eligible()) {
            throw new IllegalStateException(
                "Unsynchronized, failing pull request was accepted."
            );
        }

        for (String reason : blockedDecision.blockingReasons()) {
            System.out.println("Blocked: " + reason);
        }

        // Required approvals are decisions from eligible, current reviewers.
        // Branch protection evaluates those decisions alongside independent
        // constraints; approval alone never grants merge eligibility.
    }

    public static void main(String[] args) {
        demonstrateQuantumCircuit();
        demonstrateGovernancePolicy();
        System.out.println("\nAll Java assertions passed.");
    }
}
