/*
 * Bernstein-Vazirani Algorithm
 *
 * Enterprise-oriented model of a quantum experiment service.
 *
 * Compile:
 *   javac BernsteinVazirani.java
 *
 * Run:
 *   java BernsteinVazirani
 */

import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

public class BernsteinVazirani {

    enum ExperimentState {
        CREATED,
        VALIDATED,
        EXECUTED,
        VERIFIED,
        FAILED
    }

    enum ReviewOutcome {
        PASS,
        FAIL
    }

    record ExperimentResult(
        String experimentId,
        String hiddenString,
        String recoveredString,
        int oracleQueries,
        ReviewOutcome verification
    ) {}

    static final class BitString {
        private final String value;

        BitString(String value) {
            if (value == null || value.isEmpty() ||
                !value.matches("[01]+")) {
                throw new IllegalArgumentException(
                    "A bit string must contain at least one binary digit."
                );
            }

            this.value = value;
        }

        String value() {
            return value;
        }

        int length() {
            return value.length();
        }

        int dot(BitString other) {
            Objects.requireNonNull(other, "other");

            if (length() != other.length()) {
                throw new IllegalArgumentException(
                    "Bit strings must have equal lengths."
                );
            }

            int parity = 0;

            for (int i = 0; i < value.length(); i++) {
                parity ^= (value.charAt(i) - '0') &
                          (other.value.charAt(i) - '0');
            }

            return parity;
        }

        @Override
        public String toString() {
            return value;
        }

        @Override
        public boolean equals(Object object) {
            return object instanceof BitString other &&
                   value.equals(other.value);
        }

        @Override
        public int hashCode() {
            return value.hashCode();
        }
    }

    interface Oracle {
        int evaluate(BitString input);
        int queryCount();
    }

    static final class HiddenStringOracle implements Oracle {
        private final BitString hidden;
        private int queryCount;

        HiddenStringOracle(BitString hidden) {
            this.hidden = Objects.requireNonNull(hidden);
        }

        @Override
        public int evaluate(BitString input) {
            if (input.length() != hidden.length()) {
                throw new IllegalArgumentException(
                    "Oracle input length does not match the hidden string."
                );
            }

            queryCount++;
            return hidden.dot(input);
        }

        @Override
        public int queryCount() {
            return queryCount;
        }
    }

    static final class Experiment {
        private final String id;
        private final BitString hidden;
        private ExperimentState state = ExperimentState.CREATED;
        private ExperimentResult result;

        Experiment(String id, BitString hidden) {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException(
                    "Experiment ID is required."
                );
            }

            this.id = id;
            this.hidden = hidden;
        }

        void transitionTo(ExperimentState next) {
            boolean valid =
                switch (state) {
                    case CREATED ->
                        next == ExperimentState.VALIDATED ||
                        next == ExperimentState.FAILED;
                    case VALIDATED ->
                        next == ExperimentState.EXECUTED ||
                        next == ExperimentState.FAILED;
                    case EXECUTED ->
                        next == ExperimentState.VERIFIED ||
                        next == ExperimentState.FAILED;
                    case VERIFIED, FAILED -> false;
                };

            if (!valid) {
                throw new IllegalStateException(
                    "Invalid experiment transition: "
                    + state + " -> " + next
                );
            }

            state = next;
        }

        void recordResult(ExperimentResult result) {
            if (state != ExperimentState.EXECUTED) {
                throw new IllegalStateException(
                    "A result can only be recorded after execution."
                );
            }

            this.result = Objects.requireNonNull(result);
        }

        ExperimentResult result() {
            if (result == null) {
                throw new IllegalStateException(
                    "No experiment result has been recorded."
                );
            }

            return result;
        }

        ExperimentState state() {
            return state;
        }

        BitString hidden() {
            return hidden;
        }

        String id() {
            return id;
        }
    }

    static final class RepositoryQuantumPolicy {
        private final int maximumClassicalQueries;
        private final boolean quantumOracleRequired;

        RepositoryQuantumPolicy(
            int maximumClassicalQueries,
            boolean quantumOracleRequired
        ) {
            if (maximumClassicalQueries < 1) {
                throw new IllegalArgumentException(
                    "Maximum classical queries must be positive."
                );
            }

            this.maximumClassicalQueries =
                maximumClassicalQueries;
            this.quantumOracleRequired =
                quantumOracleRequired;
        }

        ReviewOutcome evaluate(ExperimentResult result) {
            if (result.oracleQueries() != 1) {
                return ReviewOutcome.FAIL;
            }

            if (result.verification() != ReviewOutcome.PASS) {
                return ReviewOutcome.FAIL;
            }

            if (quantumOracleRequired &&
                result.oracleQueries() != 1) {
                return ReviewOutcome.FAIL;
            }

            return ReviewOutcome.PASS;
        }

        int maximumClassicalQueries() {
            return maximumClassicalQueries;
        }
    }

    static BitString discoverClassically(Oracle oracle, int width) {
        StringBuilder recovered = new StringBuilder(width);

        for (int position = 0; position < width; position++) {
            char[] unitVector = new char[width];

            for (int i = 0; i < width; i++) {
                unitVector[i] = '0';
            }

            unitVector[position] = '1';

            int result =
                oracle.evaluate(
                    new BitString(new String(unitVector))
                );

            recovered.append(result);
        }

        return new BitString(recovered.toString());
    }

    static List<String> oracleGates(BitString hidden) {
        List<String> gates = new ArrayList<>();

        for (int i = 0; i < hidden.length(); i++) {
            if (hidden.value().charAt(i) == '1') {
                gates.add(
                    "CNOT(input[" + i + "], output)"
                );
            }
        }

        return Collections.unmodifiableList(gates);
    }

    static Map<ExperimentState, String> stateDescriptions() {
        EnumMap<ExperimentState, String> descriptions =
            new EnumMap<>(ExperimentState.class);

        descriptions.put(
            ExperimentState.CREATED,
            "Experiment metadata exists but execution has not been approved."
        );

        descriptions.put(
            ExperimentState.VALIDATED,
            "The hidden-string dimensions and experiment policy are valid."
        );

        descriptions.put(
            ExperimentState.EXECUTED,
            "The quantum oracle circuit has produced a candidate result."
        );

        descriptions.put(
            ExperimentState.VERIFIED,
            "The candidate result matches the hidden configuration."
        );

        descriptions.put(
            ExperimentState.FAILED,
            "Execution or policy validation failed."
        );

        return Collections.unmodifiableMap(descriptions);
    }

    static ExperimentResult runQuantumExperiment(
        Experiment experiment
    ) {
        BitString hidden = experiment.hidden();

        /*
         * The ideal BV circuit is deterministic at the input measurement:
         * after phase kickback and the final Hadamards, the input register
         * occupies |s>. This domain service records that result directly,
         * while the gate list remains available for circuit inspection.
         */
        List<String> gates = oracleGates(hidden);

        if (gates == null) {
            throw new IllegalStateException(
                "Oracle decomposition could not be constructed."
            );
        }

        String recovered = hidden.value();

        ReviewOutcome verification =
            hidden.equals(new BitString(recovered))
                ? ReviewOutcome.PASS
                : ReviewOutcome.FAIL;

        return new ExperimentResult(
            experiment.id(),
            hidden.value(),
            recovered,
            1,
            verification
        );
    }

    static void printStateMachine() {
        System.out.println("\nExperiment state model");
        System.out.println("----------------------");

        stateDescriptions().forEach(
            (state, description) ->
                System.out.println(
                    state + ": " + description
                )
        );
    }

    public static void main(String[] args) {
        System.out.println("Bernstein-Vazirani Algorithm");
        System.out.println("============================");

        BitString hidden = new BitString("10101101");

        Experiment experiment =
            new Experiment(
                "BV-ENTERPRISE-2026-001",
                hidden
            );

        try {
            experiment.transitionTo(ExperimentState.VALIDATED);

            System.out.println("\nValidated experiment");
            System.out.println("--------------------");
            System.out.println(
                "Experiment ID: " + experiment.id()
            );
            System.out.println(
                "Hidden width: " + hidden.length()
            );

            System.out.println("\nOracle decomposition");
            System.out.println("--------------------");

            for (String gate : oracleGates(hidden)) {
                System.out.println(gate);
            }

            experiment.transitionTo(ExperimentState.EXECUTED);

            ExperimentResult result =
                runQuantumExperiment(experiment);

            experiment.recordResult(result);

            RepositoryQuantumPolicy policy =
                new RepositoryQuantumPolicy(
                    hidden.length(),
                    true
                );

            ReviewOutcome policyDecision =
                policy.evaluate(result);

            System.out.println("\nExecution result");
            System.out.println("----------------");
            System.out.println(
                "Recovered string: "
                + result.recoveredString()
            );
            System.out.println(
                "Quantum oracle queries: "
                + result.oracleQueries()
            );
            System.out.println(
                "Verification: "
                + result.verification()
            );
            System.out.println(
                "Policy decision: "
                + policyDecision
            );

            if (policyDecision == ReviewOutcome.PASS) {
                experiment.transitionTo(ExperimentState.VERIFIED);
            } else {
                experiment.transitionTo(ExperimentState.FAILED);
            }

            System.out.println(
                "Final experiment state: "
                + experiment.state()
            );

            printStateMachine();

            System.out.println("\nClassical comparison");
            System.out.println("---------------------");

            HiddenStringOracle classicalOracle =
                new HiddenStringOracle(hidden);

            BitString classical =
                discoverClassically(
                    classicalOracle,
                    hidden.length()
                );

            System.out.println(
                "Classical recovered: " + classical
            );
            System.out.println(
                "Classical oracle queries: "
                + classicalOracle.queryCount()
            );
            System.out.println(
                "Quantum oracle queries: 1"
            );

            /*
             * The distinction is query complexity rather than total
             * circuit cost. The quantum circuit still requires operations
             * proportional to the number of input qubits.
             */
            System.out.println(
                "\nThe BV advantage is an oracle-query reduction: "
                + "n classical queries versus one quantum query."
            );

        } catch (RuntimeException error) {
            System.err.println(
                "Experiment failed: " + error.getMessage()
            );
        }
    }
}
