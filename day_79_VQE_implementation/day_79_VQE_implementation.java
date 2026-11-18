import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/*
 * Java 17 Enterprise VQE Application
 *
 * Domain:
 * Molecular hydrogen ground-state energy optimization.
 *
 * Enterprise architecture:
 * Domain model
 *     -> Hamiltonian repository
 *     -> Quantum circuit service
 *     -> Energy evaluation service
 *     -> Optimization policy
 *     -> Experiment orchestration
 *     -> Result validation
 *
 * No third-party dependencies.
 */

public class VQEApplication {

    private static final double PI = Math.PI;
    private static final double TOLERANCE = 1e-9;

    public enum ExperimentStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    public enum PauliOperator {
        I, X, Y, Z
    }

    public static class VQEException extends RuntimeException {
        public VQEException(String message) {
            super(message);
        }
    }

    public record PauliTerm(
        double coefficient,
        String operators
    ) {
        public PauliTerm {
            if (!Double.isFinite(coefficient)) {
                throw new VQEException("Invalid Hamiltonian coefficient.");
            }

            if (operators == null ||
                !operators.matches("[IXYZ]{2}")) {
                throw new VQEException("Invalid two-qubit Pauli string.");
            }
        }
    }

    public record OptimizationPolicy(
        double learningRate,
        double beta1,
        double beta2,
        double epsilon,
        double tolerance,
        int maximumIterations
    ) {
        public OptimizationPolicy {
            if (learningRate <= 0 ||
                beta1 <= 0 || beta1 >= 1 ||
                beta2 <= 0 || beta2 >= 1 ||
                epsilon <= 0 ||
                tolerance <= 0 ||
                maximumIterations <= 0) {
                throw new VQEException("Invalid optimization policy.");
            }
        }

        public static OptimizationPolicy standard() {
            return new OptimizationPolicy(
                0.05, 0.9, 0.999, 1e-8, TOLERANCE, 2000
            );
        }
    }

    public record IterationRecord(
        int iteration,
        double energy,
        double gradientNorm,
        List<Double> parameters
    ) {
        public IterationRecord {
            parameters = List.copyOf(parameters);
        }
    }

    public record ExperimentResult(
        String molecule,
        double optimizedEnergy,
        double exactEnergy,
        double absoluteError,
        List<Double> parameters,
        int iterations,
        boolean converged,
        List<IterationRecord> history
    ) {
        public ExperimentResult {
            Objects.requireNonNull(molecule);
            parameters = List.copyOf(parameters);
            history = List.copyOf(history);
        }
    }

    public interface EnergyObjective {
        double evaluate(double[] parameters);

        double[] gradient(double[] parameters);
    }

    // -----------------------------------------------------
    // Hamiltonian domain service
    // -----------------------------------------------------

    public static final class Hamiltonian {

        private final List<PauliTerm> terms;

        private static final Complex[][][] PAULI = {
            {
                {new Complex(1, 0), new Complex(0, 0)},
                {new Complex(0, 0), new Complex(1, 0)}
            },
            {
                {new Complex(0, 0), new Complex(1, 0)},
                {new Complex(1, 0), new Complex(0, 0)}
            },
            {
                {new Complex(0, 0), new Complex(0, -1)},
                {new Complex(0, 1), new Complex(0, 0)}
            },
            {
                {new Complex(1, 0), new Complex(0, 0)},
                {new Complex(0, 0), new Complex(-1, 0)}
            }
        };

        public Hamiltonian(List<PauliTerm> terms) {
            if (terms == null || terms.isEmpty()) {
                throw new VQEException("Hamiltonian cannot be empty.");
            }

            this.terms = List.copyOf(terms);
        }

        private int operatorIndex(char operator) {
            return switch (operator) {
                case 'I' -> 0;
                case 'X' -> 1;
                case 'Y' -> 2;
                case 'Z' -> 3;
                default -> throw new VQEException("Unknown Pauli operator.");
            };
        }

        private Complex[] applyPauli(
            Complex[] state,
            String operators
        ) {
            Complex[] output = new Complex[4];

            for (int i = 0; i < 4; i++) {
                output[i] = Complex.ZERO;
            }

            int first = operatorIndex(operators.charAt(0));
            int second = operatorIndex(operators.charAt(1));

            for (int row = 0; row < 4; row++) {
                int row0 = (row >> 1) & 1;
                int row1 = row & 1;

                for (int column = 0; column < 4; column++) {
                    int col0 = (column >> 1) & 1;
                    int col1 = column & 1;

                    Complex factor = PAULI[first][row0][col0]
                        .multiply(PAULI[second][row1][col1]);

                    output[row] = output[row].add(
                        factor.multiply(state[column])
                    );
                }
            }

            return output;
        }

        public double energy(Complex[] state) {
            Complex total = Complex.ZERO;

            for (PauliTerm term : terms) {
                Complex[] transformed = applyPauli(
                    state,
                    term.operators()
                );

                Complex expectation = Complex.ZERO;

                for (int i = 0; i < 4; i++) {
                    expectation = expectation.add(
                        state[i].conjugate().multiply(transformed[i])
                    );
                }

                total = total.add(
                    expectation.multiply(term.coefficient())
                );
            }

            if (Math.abs(total.imaginary()) > 1e-8) {
                throw new VQEException("Energy is not real.");
            }

            return total.real();
        }

        public double[][] realMatrix() {
            double[][] matrix = new double[4][4];

            for (PauliTerm term : terms) {
                int p = operatorIndex(term.operators().charAt(0));
                int q = operatorIndex(term.operators().charAt(1));

                for (int row = 0; row < 4; row++) {
                    int r0 = (row >> 1) & 1;
                    int r1 = row & 1;

                    for (int column = 0; column < 4; column++) {
                        int c0 = (column >> 1) & 1;
                        int c1 = column & 1;

                        Complex value = PAULI[p][r0][c0]
                            .multiply(PAULI[q][r1][c1]);

                        if (Math.abs(value.imaginary()) > 1e-10) {
                            throw new VQEException(
                                "Hamiltonian is not real symmetric."
                            );
                        }

                        matrix[row][column] +=
                            term.coefficient() * value.real();
                    }
                }
            }

            return matrix;
        }

        public double exactGroundEnergy() {
            double[][] matrix = realMatrix();

            // Jacobi eigensolver for a real symmetric matrix.
            for (int iteration = 0; iteration < 1000; iteration++) {
                int p = 0;
                int q = 1;
                double maximum = 0;

                for (int i = 0; i < 4; i++) {
                    for (int j = i + 1; j < 4; j++) {
                        if (Math.abs(matrix[i][j]) > maximum) {
                            maximum = Math.abs(matrix[i][j]);
                            p = i;
                            q = j;
                        }
                    }
                }

                if (maximum < 1e-14) {
                    break;
                }

                double angle = 0.5 * Math.atan2(
                    2 * matrix[p][q],
                    matrix[q][q] - matrix[p][p]
                );

                double c = Math.cos(angle);
                double s = Math.sin(angle);

                double app = matrix[p][p];
                double aqq = matrix[q][q];
                double apq = matrix[p][q];

                matrix[p][p] = c * c * app
                    - 2 * s * c * apq
                    + s * s * aqq;

                matrix[q][q] = s * s * app
                    + 2 * s * c * apq
                    + c * c * aqq;

                matrix[p][q] = 0;
                matrix[q][p] = 0;

                for (int k = 0; k < 4; k++) {
                    if (k == p || k == q) continue;

                    double akp = matrix[k][p];
                    double akq = matrix[k][q];

                    matrix[k][p] = c * akp - s * akq;
                    matrix[p][k] = matrix[k][p];

                    matrix[k][q] = s * akp + c * akq;
                    matrix[q][k] = matrix[k][q];
                }
            }

            double minimum = matrix[0][0];

            for (int i = 1; i < 4; i++) {
                minimum = Math.min(minimum, matrix[i][i]);
            }

            return minimum;
        }
    }

    // -----------------------------------------------------
    // Complex arithmetic
    // -----------------------------------------------------

    public record Complex(double real, double imaginary) {

        public static final Complex ZERO = new Complex(0, 0);

        public Complex add(Complex other) {
            return new Complex(
                real + other.real,
                imaginary + other.imaginary
            );
        }

        public Complex multiply(Complex other) {
            return new Complex(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        public Complex multiply(double scalar) {
            return new Complex(
                real * scalar,
                imaginary * scalar
            );
        }

        public Complex conjugate() {
            return new Complex(real, -imaginary);
        }

        public double normSquared() {
            return real * real + imaginary * imaginary;
        }
    }

    // -----------------------------------------------------
    // Quantum circuit service
    // -----------------------------------------------------

    public static final class QuantumCircuit {

        public static Complex[] prepare(double[] parameters) {
            if (parameters == null || parameters.length != 2) {
                throw new VQEException("Exactly two parameters are required.");
            }

            for (double parameter : parameters) {
                if (!Double.isFinite(parameter)) {
                    throw new VQEException("Invalid circuit parameter.");
                }
            }

            Complex[] state = {
                new Complex(1, 0),
                Complex.ZERO,
                Complex.ZERO,
                Complex.ZERO
            };

            state = applyRY(state, parameters[0], 0);
            state = applyRY(state, parameters[1], 1);
            state = applyCNOT(state, 0, 1);

            return state;
        }

        private static Complex[] applyRY(
            Complex[] state,
            double theta,
            int qubit
        ) {
            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);

            Complex[] output = state.clone();

            for (int i = 0; i < 4; i++) {
                int bitPosition = 1 - qubit;

                if ((i & (1 << bitPosition)) != 0) {
                    continue;
                }

                int partner = i | (1 << bitPosition);

                output[i] = state[i].multiply(c)
                    .add(state[partner].multiply(-s));

                output[partner] = state[i].multiply(s)
                    .add(state[partner].multiply(c));
            }

            return output;
        }

        private static Complex[] applyCNOT(
            Complex[] state,
            int control,
            int target
        ) {
            if (control == target ||
                control < 0 || control > 1 ||
                target < 0 || target > 1) {
                throw new VQEException("Invalid CNOT gate.");
            }

            Complex[] output = new Complex[4];

            for (int i = 0; i < 4; i++) {
                int destination = i;

                if ((i & (1 << (1 - control))) != 0) {
                    destination ^= 1 << (1 - target);
                }

                output[destination] = state[i];
            }

            return output;
        }
    }

    // -----------------------------------------------------
    // Objective and optimization
    // -----------------------------------------------------

    public static final class MolecularObjective
        implements EnergyObjective {

        private final Hamiltonian hamiltonian;

        public MolecularObjective(Hamiltonian hamiltonian) {
            this.hamiltonian = Objects.requireNonNull(hamiltonian);
        }

        @Override
        public double evaluate(double[] parameters) {
            return hamiltonian.energy(
                QuantumCircuit.prepare(parameters)
            );
        }

        @Override
        public double[] gradient(double[] parameters) {
            double[] gradient = new double[parameters.length];

            for (int i = 0; i < parameters.length; i++) {
                double[] positive = parameters.clone();
                double[] negative = parameters.clone();

                positive[i] += PI / 2;
                negative[i] -= PI / 2;

                gradient[i] = 0.5 * (
                    evaluate(positive) - evaluate(negative)
                );
            }

            return gradient;
        }
    }

    public static final class OptimizationService {

        private final OptimizationPolicy policy;

        public OptimizationService(OptimizationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        public ExperimentResult optimize(
            String molecule,
            Hamiltonian hamiltonian,
            double[] initial
        ) {
            if (initial == null || initial.length != 2) {
                throw new VQEException("Invalid initial parameter vector.");
            }

            double[] parameters = initial.clone();
            double[] first = new double[2];
            double[] second = new double[2];

            EnergyObjective objective =
                new MolecularObjective(hamiltonian);

            List<IterationRecord> history = new ArrayList<>();

            double previousEnergy = objective.evaluate(parameters);
            boolean converged = false;

            for (int iteration = 1;
                 iteration <= policy.maximumIterations();
                 iteration++) {

                double[] gradient = objective.gradient(parameters);

                double gradientNorm = Math.hypot(
                    gradient[0], gradient[1]
                );

                for (int i = 0; i < 2; i++) {
                    first[i] = policy.beta1() * first[i]
                        + (1 - policy.beta1()) * gradient[i];

                    second[i] = policy.beta2() * second[i]
                        + (1 - policy.beta2()) * gradient[i] * gradient[i];

                    double correctedFirst = first[i] /
                        (1 - Math.pow(policy.beta1(), iteration));

                    double correctedSecond = second[i] /
                        (1 - Math.pow(policy.beta2(), iteration));

                    parameters[i] -= policy.learningRate()
                        * correctedFirst
                        / (Math.sqrt(correctedSecond) + policy.epsilon());

                    parameters[i] = Math.IEEEremainder(
                        parameters[i], 2 * PI
                    );
                }

                double energy = objective.evaluate(parameters);

                if (!Double.isFinite(energy)) {
                    throw new VQEException("Energy calculation failed.");
                }

                history.add(new IterationRecord(
                    iteration,
                    energy,
                    gradientNorm,
                    List.of(parameters[0], parameters[1])
                ));

                if (gradientNorm < policy.tolerance() &&
                    Math.abs(energy - previousEnergy) < policy.tolerance()) {
                    converged = true;
                    break;
                }

                previousEnergy = energy;
            }

            double finalEnergy = objective.evaluate(parameters);
            double exactEnergy = hamiltonian.exactGroundEnergy();

            return new ExperimentResult(
                molecule,
                finalEnergy,
                exactEnergy,
                Math.abs(finalEnergy - exactEnergy),
                List.of(parameters[0], parameters[1]),
                history.size(),
                converged,
                history
            );
        }
    }

    // -----------------------------------------------------
    // Experiment lifecycle and governance
    // -----------------------------------------------------

    public static final class ExperimentService {

        private ExperimentStatus status = ExperimentStatus.CREATED;

        private final OptimizationService optimizationService;

        public ExperimentService(OptimizationService service) {
            this.optimizationService = Objects.requireNonNull(service);
        }

        public ExperimentResult execute(Hamiltonian hamiltonian) {
            if (status != ExperimentStatus.CREATED) {
                throw new VQEException("Invalid experiment state transition.");
            }

            status = ExperimentStatus.RUNNING;

            try {
                ExperimentResult result = optimizationService.optimize(
                    "H2",
                    hamiltonian,
                    new double[]{0.2, -0.4}
                );

                validateResult(result, hamiltonian);

                status = ExperimentStatus.COMPLETED;

                return result;

            } catch (RuntimeException error) {
                status = ExperimentStatus.FAILED;
                throw error;
            }
        }

        private void validateResult(
            ExperimentResult result,
            Hamiltonian hamiltonian
        ) {
            if (!Double.isFinite(result.optimizedEnergy()) ||
                result.absoluteError() < 0) {
                throw new VQEException("Invalid experiment result.");
            }

            if (result.optimizedEnergy() <
                hamiltonian.exactGroundEnergy() - 1e-7) {
                throw new VQEException(
                    "Variational lower-bound validation failed."
                );
            }
        }

        public ExperimentStatus status() {
            return status;
        }
    }

    // -----------------------------------------------------
    // Measurement service
    // -----------------------------------------------------

    public static Map<String, Integer> sample(
        Complex[] state,
        int shots,
        long seed
    ) {
        if (shots <= 0) {
            throw new VQEException("Shot count must be positive.");
        }

        double[] probabilities = new double[4];

        double total = 0;

        for (int i = 0; i < 4; i++) {
            probabilities[i] = state[i].normSquared();
            total += probabilities[i];
        }

        if (Math.abs(total - 1.0) > 1e-8) {
            throw new VQEException("Invalid state normalization.");
        }

        java.util.Random random = new java.util.Random(seed);

        Map<String, Integer> counts = new TreeMap<>();

        for (int shot = 0; shot < shots; shot++) {
            double value = random.nextDouble();
            double cumulative = 0;

            for (int i = 0; i < 4; i++) {
                cumulative += probabilities[i];

                if (value < cumulative || i == 3) {
                    String basis = String.format("%2s",
                        Integer.toBinaryString(i)).replace(' ', '0');

                    counts.merge(basis, 1, Integer::sum);
                    break;
                }
            }
        }

        return Collections.unmodifiableMap(counts);
    }

    // -----------------------------------------------------
    // Application entry point
    // -----------------------------------------------------

    public static void main(String[] args) {

        try {
            Hamiltonian hamiltonian = new Hamiltonian(List.of(
                new PauliTerm(-1.052373245772859, "II"),
                new PauliTerm(0.39793742484318045, "ZI"),
                new PauliTerm(-0.39793742484318045, "IZ"),
                new PauliTerm(-0.01128010425623538, "ZZ"),
                new PauliTerm(0.18093119978423156, "XX")
            ));

            OptimizationPolicy policy =
                OptimizationPolicy.standard();

            OptimizationService optimizer =
                new OptimizationService(policy);

            ExperimentService experiment =
                new ExperimentService(optimizer);

            ExperimentResult result =
                experiment.execute(hamiltonian);

            Complex[] finalState = QuantumCircuit.prepare(
                result.parameters().stream()
                    .mapToDouble(Double::doubleValue)
                    .toArray()
            );

            Map<String, Integer> counts =
                sample(finalState, 10000, 42L);

            System.out.println("\n========== JAVA 17 VQE ==========");
            System.out.println("Molecule: " + result.molecule());

            System.out.printf(
                "Optimized energy: %.12f Ha%n",
                result.optimizedEnergy()
            );

            System.out.printf(
                "Exact energy:     %.12f Ha%n",
                result.exactEnergy()
            );

            System.out.printf(
                "Absolute error:   %.12e Ha%n",
                result.absoluteError()
            );

            System.out.println("Parameters: " + result.parameters());
            System.out.println("Iterations: " + result.iterations());
            System.out.println("Converged: " + result.converged());
            System.out.println("Status: " + experiment.status());

            System.out.println("\nMeasurement counts:");
            counts.forEach(
                (basis, count) ->
                    System.out.println("|" + basis + "> = " + count)
            );

            System.out.println("\nOptimization history:");

            int step = Math.max(1, result.history().size() / 10);

            for (int i = 0; i < result.history().size(); i += step) {
                IterationRecord record = result.history().get(i);

                System.out.printf(
                    "%4d | %.10f Ha | Gradient %.4e%n",
                    record.iteration(),
                    record.energy(),
                    record.gradientNorm()
                );
            }

        } catch (VQEException error) {
            System.err.println("VQE application error: " + error.getMessage());
            System.exit(1);
        }
    }
}
