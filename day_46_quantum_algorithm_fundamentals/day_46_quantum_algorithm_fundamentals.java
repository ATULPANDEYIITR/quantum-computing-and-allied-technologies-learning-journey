import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;

public final class QuantumAlgorithmGovernance {
    private static final double EPSILON = 1e-9;

    private QuantumAlgorithmGovernance() {
    }

    enum Gate {
        HADAMARD,
        PHASE_ORACLE,
        DIFFUSION,
        MEASUREMENT
    }

    enum ExperimentStatus {
        CREATED,
        PREPARED,
        EXECUTED,
        MEASURED,
        FAILED
    }

    record ExperimentPolicy(int maximumQubits, int maximumShots,
                            boolean requireOracleValidation) {
        ExperimentPolicy {
            if (maximumQubits < 1 || maximumQubits > 20) {
                throw new IllegalArgumentException(
                    "Maximum qubits must be between 1 and 20."
                );
            }
            if (maximumShots < 1) {
                throw new IllegalArgumentException("Maximum shots must be positive.");
            }
        }
    }

    record ExperimentResult(
        String algorithm,
        int qubits,
        int oracleQueries,
        int iterations,
        int measuredState,
        double targetProbability,
        ExperimentStatus status
    ) {
        ExperimentResult {
            Objects.requireNonNull(algorithm);
            Objects.requireNonNull(status);
            if (qubits < 1 || oracleQueries < 0 || iterations < 0) {
                throw new IllegalArgumentException("Invalid resource accounting.");
            }
            if (targetProbability < 0.0 || targetProbability > 1.0 + EPSILON) {
                throw new IllegalArgumentException("Invalid target probability.");
            }
        }
    }

    static final class StateVector {
        private final int qubits;
        private final double[] real;
        private final double[] imaginary;

        StateVector(int qubits, int basisIndex) {
            if (qubits < 1 || qubits > 20) {
                throw new IllegalArgumentException("Unsupported qubit count.");
            }
            int dimension = 1 << qubits;
            if (basisIndex < 0 || basisIndex >= dimension) {
                throw new IllegalArgumentException("Invalid basis state.");
            }
            this.qubits = qubits;
            this.real = new double[dimension];
            this.imaginary = new double[dimension];
            this.real[basisIndex] = 1.0;
        }

        private StateVector(int qubits, double[] real, double[] imaginary) {
            this.qubits = qubits;
            this.real = real;
            this.imaginary = imaginary;
            validateNormalized();
        }

        static StateVector uniform(int qubits) {
            StateVector state = new StateVector(qubits, 0);
            double amplitude = 1.0 / Math.sqrt(state.real.length);
            for (int index = 0; index < state.real.length; index++) {
                state.real[index] = amplitude;
            }
            return state;
        }

        int dimension() {
            return real.length;
        }

        int qubits() {
            return qubits;
        }

        StateVector hadamardAll() {
            double[] outputReal = real.clone();
            double[] outputImaginary = imaginary.clone();

            // A butterfly transform avoids allocating a dense 2^n by 2^n
            // gate matrix. Each stage doubles the distance between paired
            // amplitudes, requiring O(n * 2^n) arithmetic operations.
            for (int width = 1; width < real.length; width *= 2) {
                for (int start = 0; start < real.length; start += width * 2) {
                    for (int offset = 0; offset < width; offset++) {
                        int left = start + offset;
                        int right = left + width;

                        double lr = outputReal[left];
                        double li = outputImaginary[left];
                        double rr = outputReal[right];
                        double ri = outputImaginary[right];

                        outputReal[left] = (lr + rr) / Math.sqrt(2.0);
                        outputImaginary[left] = (li + ri) / Math.sqrt(2.0);
                        outputReal[right] = (lr - rr) / Math.sqrt(2.0);
                        outputImaginary[right] = (li - ri) / Math.sqrt(2.0);
                    }
                }
            }

            return new StateVector(qubits, outputReal, outputImaginary);
        }

        StateVector phaseOracle(Set<Integer> marked) {
            Objects.requireNonNull(marked);
            double[] outputReal = real.clone();
            double[] outputImaginary = imaginary.clone();

            for (int index : marked) {
                if (index < 0 || index >= real.length) {
                    throw new IllegalArgumentException(
                        "Oracle state lies outside the circuit."
                    );
                }
                outputReal[index] = -outputReal[index];
                outputImaginary[index] = -outputImaginary[index];
            }

            return new StateVector(qubits, outputReal, outputImaginary);
        }

        StateVector diffuse() {
            double meanReal = 0.0;
            double meanImaginary = 0.0;

            for (int index = 0; index < real.length; index++) {
                meanReal += real[index] / real.length;
                meanImaginary += imaginary[index] / real.length;
            }

            double[] outputReal = new double[real.length];
            double[] outputImaginary = new double[real.length];

            for (int index = 0; index < real.length; index++) {
                outputReal[index] = 2.0 * meanReal - real[index];
                outputImaginary[index] = 2.0 * meanImaginary - imaginary[index];
            }

            return new StateVector(qubits, outputReal, outputImaginary);
        }

        double probability(int index) {
            if (index < 0 || index >= real.length) {
                throw new IllegalArgumentException("Invalid measurement index.");
            }
            return real[index] * real[index]
                + imaginary[index] * imaginary[index];
        }

        int mostProbableState() {
            int best = 0;
            for (int index = 1; index < real.length; index++) {
                if (probability(index) > probability(best)) {
                    best = index;
                }
            }
            return best;
        }

        private void validateNormalized() {
            double norm = 0.0;
            for (int index = 0; index < real.length; index++) {
                norm += real[index] * real[index]
                    + imaginary[index] * imaginary[index];
            }
            if (Math.abs(norm - 1.0) > EPSILON) {
                throw new IllegalStateException("Quantum state lost normalization.");
            }
        }
    }

    interface Oracle {
        boolean isMarked(int basisState);
    }

    static final class GroverService {
        private final ExperimentPolicy policy;

        GroverService(ExperimentPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        ExperimentResult execute(Oracle oracle, Set<Integer> knownMarkedStates,
                                 int qubits, int shots) {
            Objects.requireNonNull(oracle);
            Objects.requireNonNull(knownMarkedStates);

            if (qubits > policy.maximumQubits()) {
                throw new IllegalArgumentException("Qubit policy exceeded.");
            }
            if (shots < 1 || shots > policy.maximumShots()) {
                throw new IllegalArgumentException("Shot policy exceeded.");
            }

            int dimension = 1 << qubits;
            if (knownMarkedStates.isEmpty()) {
                throw new IllegalArgumentException("No marked states provided.");
            }
            if (knownMarkedStates.size() >= dimension) {
                throw new IllegalArgumentException("Search has no unmarked states.");
            }

            Set<Integer> marked = new TreeSet<>(knownMarkedStates);
            for (int index = 0; index < dimension; index++) {
                // Checking the executable oracle against the declared target
                // set catches disagreement before resource-intensive execution.
                if (oracle.isMarked(index) != marked.contains(index)) {
                    throw new IllegalArgumentException(
                        "Oracle disagrees with the declared target set."
                    );
                }
            }

            int iterations = Math.max(1, (int) Math.round(
                (Math.PI / 4.0) * Math.sqrt(
                    (double) dimension / marked.size()
                )
            ));

            StateVector state = StateVector.uniform(qubits);
            ExperimentStatus status = ExperimentStatus.PREPARED;

            try {
                for (int iteration = 0; iteration < iterations; iteration++) {
                    state = state.phaseOracle(marked);
                    state = state.diffuse();
                }
                status = ExperimentStatus.EXECUTED;

                int measured = state.mostProbableState();
                double targetProbability = 0.0;
                for (int target : marked) {
                    targetProbability += state.probability(target);
                }

                status = ExperimentStatus.MEASURED;
                return new ExperimentResult(
                    "Grover search",
                    qubits,
                    iterations,
                    iterations,
                    measured,
                    targetProbability,
                    status
                );
            } catch (RuntimeException exception) {
                status = ExperimentStatus.FAILED;
                throw new IllegalStateException(
                    "Experiment failed in state " + status,
                    exception
                );
            }
        }
    }

    private static String bits(int value, int width) {
        return String.format("%" + width + "s",
            Integer.toBinaryString(value)).replace(' ', '0');
    }

    public static void main(String[] args) {
        ExperimentPolicy policy = new ExperimentPolicy(12, 10_000, true);
        GroverService service = new GroverService(policy);

        Set<Integer> targets = Set.of(37, 91);
        Oracle buildFailureOracle = targets::contains;

        ExperimentResult result = service.execute(
            buildFailureOracle,
            targets,
            7,
            2_000
        );

        System.out.println("Enterprise Quantum Experiment Record");
        System.out.println("-------------------------------------");
        System.out.println("Algorithm: " + result.algorithm());
        System.out.println("Experiment status: " + result.status());
        System.out.println("Qubits: " + result.qubits());
        System.out.println("Oracle queries: " + result.oracleQueries());
        System.out.println("Iterations: " + result.iterations());
        System.out.println(
            "Most probable result: " + bits(result.measuredState(), result.qubits())
        );
        System.out.printf(
            "Probability of a declared target: %.4f%n",
            result.targetProbability()
        );

        StateVector reversible = new StateVector(2, 0).hadamardAll().hadamardAll();
        System.out.println(
            "Hadamard reversal returns to |00>: "
                + (reversible.mostProbableState() == 0)
        );

        try {
            service.execute(
                index -> index == 1,
                targets,
                7,
                2_000
            );
        } catch (IllegalArgumentException exception) {
            System.out.println("Rejected inconsistent oracle: " + exception.getMessage());
        }

        try {
            service.execute(buildFailureOracle, targets, 13, 100);
        } catch (IllegalArgumentException exception) {
            System.out.println("Rejected excessive resources: " + exception.getMessage());
        }

        List<Gate> circuit = List.of(
            Gate.HADAMARD,
            Gate.PHASE_ORACLE,
            Gate.DIFFUSION,
            Gate.MEASUREMENT
        );
        System.out.println("Logical circuit stages: " + circuit);
        System.out.println(
            "Production boundary: validate oracle reversibility, "
                + "hardware noise, shot budgets, and independent result verification."
        );
    }
}
