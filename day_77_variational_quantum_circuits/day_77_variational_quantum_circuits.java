import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/*
 * Variational Quantum Circuits
 *
 * Enterprise-oriented parameterized quantum computation system.
 *
 * Java 17 features:
 * - Records
 * - Interfaces
 * - Enums
 * - Immutable domain objects
 * - Service-oriented architecture
 * - Policy validation
 * - State transitions
 * - Parameter-shift differentiation
 * - Adam optimization
 * - State-vector simulation
 * - Experiment lifecycle management
 *
 * Dependencies: Java 17 standard library only.
 */

public class VariationalQuantumEnterprise {

    // ========================================================
    // 1. Domain exceptions
    // ========================================================

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class CircuitExecutionException extends RuntimeException {
        CircuitExecutionException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 2. Domain enums
    // ========================================================

    enum GateType {
        RX, RY, RZ, CNOT
    }

    enum ExperimentStatus {
        CREATED,
        VALIDATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum OptimizationMethod {
        ADAM,
        GRADIENT_DESCENT
    }

    // ========================================================
    // 3. Immutable configuration
    // ========================================================

    record CircuitConfiguration(
        int qubits,
        int layers,
        int maximumParameters
    ) {
        CircuitConfiguration {
            if (qubits < 1 || qubits > 12) {
                throw new DomainException("Invalid qubit count.");
            }

            if (layers < 1 || layers > 20) {
                throw new DomainException("Invalid layer count.");
            }

            int expected = qubits * layers * 2;

            if (maximumParameters != expected) {
                throw new DomainException(
                    "Parameter capacity does not match circuit."
                );
            }
        }

        static CircuitConfiguration create(int qubits, int layers) {
            return new CircuitConfiguration(
                qubits,
                layers,
                qubits * layers * 2
            );
        }
    }

    record QuantumGate(
        GateType type,
        int target,
        int control,
        int parameterIndex
    ) {
        QuantumGate {
            Objects.requireNonNull(type);

            if (target < 0) {
                throw new DomainException("Invalid target qubit.");
            }

            if (type == GateType.CNOT && control < 0) {
                throw new DomainException("CNOT requires a control.");
            }

            if (type != GateType.CNOT && parameterIndex < 0) {
                throw new DomainException(
                    "Rotation gate requires a parameter."
                );
            }
        }
    }

    record OptimizationPolicy(
        OptimizationMethod method,
        double learningRate,
        int maximumIterations,
        double convergenceTolerance,
        boolean rejectIncreasingEnergy
    ) {
        OptimizationPolicy {
            Objects.requireNonNull(method);

            if (!Double.isFinite(learningRate) ||
                learningRate <= 0) {
                throw new DomainException("Invalid learning rate.");
            }

            if (maximumIterations <= 0) {
                throw new DomainException("Invalid iteration limit.");
            }

            if (convergenceTolerance <= 0 ||
                !Double.isFinite(convergenceTolerance)) {
                throw new DomainException("Invalid tolerance.");
            }
        }
    }

    record OptimizationResult(
        double initialEnergy,
        double finalEnergy,
        List<Double> parameters,
        List<Double> energyHistory,
        int iterations,
        boolean converged
    ) {
        OptimizationResult {
            parameters = List.copyOf(parameters);
            energyHistory = List.copyOf(energyHistory);
        }
    }

    // ========================================================
    // 4. Complex-number representation
    // ========================================================

    record Complex(double real, double imaginary) {

        Complex add(Complex other) {
            return new Complex(
                real + other.real,
                imaginary + other.imaginary
            );
        }

        Complex multiply(Complex other) {
            return new Complex(
                real * other.real - imaginary * other.imaginary,
                real * other.imaginary + imaginary * other.real
            );
        }

        Complex scale(double value) {
            return new Complex(
                real * value,
                imaginary * value
            );
        }

        double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }
    }

    // ========================================================
    // 5. State-vector abstraction
    // ========================================================

    interface QuantumRegister {
        void applyRX(int qubit, double theta);
        void applyRY(int qubit, double theta);
        void applyRZ(int qubit, double theta);
        void applyCNOT(int control, int target);

        double expectationZ(int qubit);
        double expectationZZ(int first, int second);

        double[] probabilities();
        int getQubitCount();
    }

    static final class StateVectorRegister
        implements QuantumRegister {

        private final int qubits;
        private final int dimension;
        private final Complex[] amplitudes;

        StateVectorRegister(int qubits) {
            if (qubits < 1 || qubits > 12) {
                throw new DomainException("Invalid register size.");
            }

            this.qubits = qubits;
            this.dimension = 1 << qubits;

            this.amplitudes = new Complex[dimension];

            for (int i = 0; i < dimension; i++) {
                amplitudes[i] = new Complex(0, 0);
            }

            amplitudes[0] = new Complex(1, 0);
        }

        @Override
        public int getQubitCount() {
            return qubits;
        }

        private void validateQubit(int qubit) {
            if (qubit < 0 || qubit >= qubits) {
                throw new DomainException("Invalid qubit index.");
            }
        }

        private void applyGate(
            int qubit,
            Complex m00,
            Complex m01,
            Complex m10,
            Complex m11
        ) {
            validateQubit(qubit);

            int mask = 1 << qubit;

            for (int index = 0; index < dimension; index++) {
                if ((index & mask) != 0) {
                    continue;
                }

                int partner = index | mask;

                Complex a = amplitudes[index];
                Complex b = amplitudes[partner];

                amplitudes[index] = m00.multiply(a)
                    .add(m01.multiply(b));

                amplitudes[partner] = m10.multiply(a)
                    .add(m11.multiply(b));
            }
        }

        @Override
        public void applyRX(int qubit, double theta) {
            validateAngle(theta);

            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);

            Complex imaginary = new Complex(0, -s);

            applyGate(
                qubit,
                new Complex(c, 0),
                imaginary,
                imaginary,
                new Complex(c, 0)
            );
        }

        @Override
        public void applyRY(int qubit, double theta) {
            validateAngle(theta);

            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);

            applyGate(
                qubit,
                new Complex(c, 0),
                new Complex(-s, 0),
                new Complex(s, 0),
                new Complex(c, 0)
            );
        }

        @Override
        public void applyRZ(int qubit, double theta) {
            validateAngle(theta);

            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);

            applyGate(
                qubit,
                new Complex(c, -s),
                new Complex(0, 0),
                new Complex(0, 0),
                new Complex(c, s)
            );
        }

        @Override
        public void applyCNOT(int control, int target) {
            validateQubit(control);
            validateQubit(target);

            if (control == target) {
                throw new DomainException(
                    "Control and target must differ."
                );
            }

            int controlMask = 1 << control;
            int targetMask = 1 << target;

            for (int index = 0; index < dimension; index++) {
                if ((index & controlMask) != 0 &&
                    (index & targetMask) == 0) {

                    int partner = index | targetMask;

                    Complex temp = amplitudes[index];
                    amplitudes[index] = amplitudes[partner];
                    amplitudes[partner] = temp;
                }
            }
        }

        @Override
        public double expectationZ(int qubit) {
            validateQubit(qubit);

            int mask = 1 << qubit;
            double result = 0;

            for (int index = 0; index < dimension; index++) {
                double eigenvalue =
                    (index & mask) == 0 ? 1 : -1;

                result += eigenvalue *
                    amplitudes[index].magnitudeSquared();
            }

            return result;
        }

        @Override
        public double expectationZZ(int first, int second) {
            validateQubit(first);
            validateQubit(second);

            if (first == second) {
                throw new DomainException(
                    "ZZ requires different qubits."
                );
            }

            int firstMask = 1 << first;
            int secondMask = 1 << second;

            double result = 0;

            for (int index = 0; index < dimension; index++) {
                double a = (index & firstMask) != 0 ? 1 : -1;
                double b = (index & secondMask) != 0 ? 1 : -1;

                result += a * b *
                    amplitudes[index].magnitudeSquared();
            }

            return result;
        }

        @Override
        public double[] probabilities() {
            double[] result = new double[dimension];

            for (int i = 0; i < dimension; i++) {
                result[i] = amplitudes[i].magnitudeSquared();
            }

            return result;
        }

        private static void validateAngle(double theta) {
            if (!Double.isFinite(theta)) {
                throw new DomainException(
                    "Rotation angle must be finite."
                );
            }
        }
    }

    // ========================================================
    // 6. Circuit construction and execution
    // ========================================================

    static final class CircuitService {

        private final CircuitConfiguration configuration;
        private final List<QuantumGate> gates;

        CircuitService(CircuitConfiguration configuration) {
            this.configuration = configuration;
            this.gates = buildCircuit();
        }

        private List<QuantumGate> buildCircuit() {
            List<QuantumGate> result = new ArrayList<>();

            int parameterIndex = 0;

            for (int layer = 0;
                 layer < configuration.layers();
                 layer++) {

                for (int qubit = 0;
                     qubit < configuration.qubits();
                     qubit++) {

                    result.add(new QuantumGate(
                        GateType.RY,
                        qubit,
                        -1,
                        parameterIndex++
                    ));

                    result.add(new QuantumGate(
                        GateType.RZ,
                        qubit,
                        -1,
                        parameterIndex++
                    ));
                }

                for (int qubit = 0;
                     qubit < configuration.qubits() - 1;
                     qubit++) {

                    result.add(new QuantumGate(
                        GateType.CNOT,
                        qubit + 1,
                        qubit,
                        -1
                    ));
                }

                if (configuration.qubits() > 2) {
                    result.add(new QuantumGate(
                        GateType.CNOT,
                        0,
                        configuration.qubits() - 1,
                        -1
                    ));
                }
            }

            return List.copyOf(result);
        }

        public int parameterCount() {
            return configuration.maximumParameters();
        }

        public void validateParameters(List<Double> parameters) {
            if (parameters == null ||
                parameters.size() != parameterCount()) {
                throw new DomainException(
                    "Circuit parameter count mismatch."
                );
            }

            for (Double parameter : parameters) {
                if (parameter == null ||
                    !Double.isFinite(parameter)) {
                    throw new DomainException(
                        "Circuit parameters must be finite."
                    );
                }
            }
        }

        public QuantumRegister execute(List<Double> parameters) {
            validateParameters(parameters);

            QuantumRegister register =
                new StateVectorRegister(configuration.qubits());

            for (QuantumGate gate : gates) {
                switch (gate.type()) {

                    case RX -> register.applyRX(
                        gate.target(),
                        parameters.get(gate.parameterIndex())
                    );

                    case RY -> register.applyRY(
                        gate.target(),
                        parameters.get(gate.parameterIndex())
                    );

                    case RZ -> register.applyRZ(
                        gate.target(),
                        parameters.get(gate.parameterIndex())
                    );

                    case CNOT -> register.applyCNOT(
                        gate.control(),
                        gate.target()
                    );
                }
            }

            return register;
        }

        public double evaluateEnergy(List<Double> parameters) {
            QuantumRegister register = execute(parameters);

            double energy = 0;

            for (int qubit = 0;
                 qubit < configuration.qubits();
                 qubit++) {

                energy -= register.expectationZ(qubit);
            }

            if (configuration.qubits() > 1) {
                energy += 0.5 *
                    register.expectationZZ(0, 1);
            }

            return energy;
        }

        public CircuitConfiguration configuration() {
            return configuration;
        }
    }

    // ========================================================
    // 7. Differentiation service
    // ========================================================

    static final class GradientService {

        public List<Double> calculate(
            CircuitService circuit,
            List<Double> parameters
        ) {
            circuit.validateParameters(parameters);

            List<Double> gradient = new ArrayList<>();

            for (int i = 0; i < parameters.size(); i++) {
                List<Double> plus = new ArrayList<>(parameters);
                List<Double> minus = new ArrayList<>(parameters);

                plus.set(i, plus.get(i) + Math.PI / 2);
                minus.set(i, minus.get(i) - Math.PI / 2);

                double derivative = 0.5 * (
                    circuit.evaluateEnergy(plus) -
                    circuit.evaluateEnergy(minus)
                );

                gradient.add(derivative);
            }

            return List.copyOf(gradient);
        }
    }

    // ========================================================
    // 8. Optimization service
    // ========================================================

    static final class OptimizationService {

        private final OptimizationPolicy policy;
        private final GradientService gradientService;

        OptimizationService(
            OptimizationPolicy policy,
            GradientService gradientService
        ) {
            this.policy = policy;
            this.gradientService = gradientService;
        }

        public OptimizationResult optimize(
            CircuitService circuit,
            List<Double> initialParameters
        ) {
            circuit.validateParameters(initialParameters);

            List<Double> parameters =
                new ArrayList<>(initialParameters);

            double initialEnergy =
                circuit.evaluateEnergy(parameters);

            List<Double> history = new ArrayList<>();
            history.add(initialEnergy);

            List<Double> firstMoment =
                new ArrayList<>();

            List<Double> secondMoment =
                new ArrayList<>();

            for (int i = 0; i < parameters.size(); i++) {
                firstMoment.add(0.0);
                secondMoment.add(0.0);
            }

            int iterations = 0;
            boolean converged = false;
            double rate = policy.learningRate();

            for (int iteration = 1;
                 iteration <= policy.maximumIterations();
                 iteration++) {

                List<Double> gradient =
                    gradientService.calculate(circuit, parameters);

                double squaredNorm = gradient.stream()
                    .mapToDouble(value -> value * value)
                    .sum();

                if (Math.sqrt(squaredNorm) <
                    policy.convergenceTolerance()) {

                    converged = true;
                    break;
                }

                List<Double> candidate =
                    new ArrayList<>(parameters);

                for (int i = 0; i < parameters.size(); i++) {
                    double update;

                    if (policy.method() == OptimizationMethod.ADAM) {
                        double g = gradient.get(i);

                        double m = 0.9 * firstMoment.get(i) +
                            0.1 * g;

                        double v = 0.999 * secondMoment.get(i) +
                            0.001 * g * g;

                        firstMoment.set(i, m);
                        secondMoment.set(i, v);

                        double correctedM =
                            m / (1 - Math.pow(0.9, iteration));

                        double correctedV =
                            v / (1 - Math.pow(0.999, iteration));

                        update = rate * correctedM /
                            (Math.sqrt(correctedV) + 1e-8);

                    } else {
                        update = rate * gradient.get(i);
                    }

                    candidate.set(
                        i,
                        parameters.get(i) - update
                    );
                }

                double candidateEnergy =
                    circuit.evaluateEnergy(candidate);

                if (policy.rejectIncreasingEnergy() &&
                    candidateEnergy > history.get(history.size() - 1) + 1e-9) {

                    rate *= 0.5;

                    if (rate < 1e-8) {
                        break;
                    }

                    continue;
                }

                parameters = candidate;
                history.add(candidateEnergy);
                iterations++;

                int size = history.size();

                if (size >= 2 &&
                    Math.abs(
                        history.get(size - 1) -
                        history.get(size - 2)
                    ) < policy.convergenceTolerance()) {

                    converged = true;
                    break;
                }
            }

            return new OptimizationResult(
                initialEnergy,
                circuit.evaluateEnergy(parameters),
                parameters,
                history,
                iterations,
                converged
            );
        }
    }

    // ========================================================
    // 9. Experiment lifecycle and governance
    // ========================================================

    static final class Experiment {

        private final String id;
        private final CircuitConfiguration configuration;
        private ExperimentStatus status;
        private final List<Double> parameters;

        private OptimizationResult result;
        private String failureReason;

        Experiment(
            CircuitConfiguration configuration,
            List<Double> parameters
        ) {
            this.id = UUID.randomUUID().toString();
            this.configuration = configuration;
            this.parameters = List.copyOf(parameters);
            this.status = ExperimentStatus.CREATED;
        }

        public synchronized void transition(
            ExperimentStatus next
        ) {
            boolean valid = switch (status) {
                case CREATED -> next == ExperimentStatus.VALIDATED
                    || next == ExperimentStatus.FAILED;

                case VALIDATED -> next == ExperimentStatus.RUNNING
                    || next == ExperimentStatus.FAILED;

                case RUNNING -> next == ExperimentStatus.COMPLETED
                    || next == ExperimentStatus.FAILED;

                case COMPLETED, FAILED -> false;
            };

            if (!valid) {
                throw new DomainException(
                    "Invalid experiment state transition: " +
                    status + " -> " + next
                );
            }

            status = next;
        }

        public synchronized void complete(
            OptimizationResult result
        ) {
            if (status != ExperimentStatus.RUNNING) {
                throw new DomainException(
                    "Experiment is not running."
                );
            }

            this.result = Objects.requireNonNull(result);
            transition(ExperimentStatus.COMPLETED);
        }

        public synchronized void fail(String reason) {
            if (status == ExperimentStatus.COMPLETED ||
                status == ExperimentStatus.FAILED) {
                throw new DomainException(
                    "Terminal experiment cannot fail again."
                );
            }

            this.failureReason = reason;
            transition(ExperimentStatus.FAILED);
        }

        public String id() {
            return id;
        }

        public ExperimentStatus status() {
            return status;
        }

        public OptimizationResult result() {
            return result;
        }

        public String failureReason() {
            return failureReason;
        }

        public CircuitConfiguration configuration() {
            return configuration;
        }

        public List<Double> parameters() {
            return parameters;
        }
    }

    static final class ExperimentRepository {

        private final Map<String, Experiment> experiments =
            new HashMap<>();

        public synchronized void save(Experiment experiment) {
            if (experiments.putIfAbsent(
                experiment.id(),
                experiment
            ) != null) {
                throw new DomainException(
                    "Duplicate experiment."
                );
            }
        }

        public synchronized Experiment find(String id) {
            Experiment experiment = experiments.get(id);

            if (experiment == null) {
                throw new DomainException(
                    "Experiment not found."
                );
            }

            return experiment;
        }

        public synchronized List<Experiment> all() {
            return Collections.unmodifiableList(
                new ArrayList<>(experiments.values())
            );
        }
    }

    // ========================================================
    // 10. Enterprise experiment application service
    // ========================================================

    static final class ExperimentApplicationService {

        private final ExperimentRepository repository;
        private final OptimizationService optimizer;

        ExperimentApplicationService(
            ExperimentRepository repository,
            OptimizationService optimizer
        ) {
            this.repository = repository;
            this.optimizer = optimizer;
        }

        public Experiment execute(
            CircuitService circuit,
            List<Double> parameters
        ) {
            Experiment experiment = new Experiment(
                circuit.configuration(),
                parameters
            );

            repository.save(experiment);

            try {
                circuit.validateParameters(parameters);

                experiment.transition(
                    ExperimentStatus.VALIDATED
                );

                experiment.transition(
                    ExperimentStatus.RUNNING
                );

                OptimizationResult result = optimizer.optimize(
                    circuit,
                    parameters
                );

                experiment.complete(result);

                return experiment;

            } catch (RuntimeException error) {
                if (experiment.status() != ExperimentStatus.FAILED &&
                    experiment.status() != ExperimentStatus.COMPLETED) {
                    experiment.fail(error.getMessage());
                }

                throw error;
            }
        }
    }

    // ========================================================
    // 11. Verification
    // ========================================================

    static void verifyBellState() {
        QuantumRegister register = new StateVectorRegister(2);

        register.applyRY(0, Math.PI / 2);
        register.applyCNOT(0, 1);

        double[] probabilities = register.probabilities();

        if (Math.abs(probabilities[0] - 0.5) > 1e-9 ||
            Math.abs(probabilities[3] - 0.5) > 1e-9) {
            throw new DomainException("Bell-state test failed.");
        }

        if (Math.abs(register.expectationZZ(0, 1) - 1.0) > 1e-9) {
            throw new DomainException("ZZ test failed.");
        }
    }

    static void verifyGradient(
        CircuitService circuit,
        List<Double> parameters
    ) {
        List<Double> analytical =
            new GradientService().calculate(circuit, parameters);

        double epsilon = 1e-6;

        for (int i = 0; i < parameters.size(); i++) {
            List<Double> plus = new ArrayList<>(parameters);
            List<Double> minus = new ArrayList<>(parameters);

            plus.set(i, plus.get(i) + epsilon);
            minus.set(i, minus.get(i) - epsilon);

            double numerical = (
                circuit.evaluateEnergy(plus) -
                circuit.evaluateEnergy(minus)
            ) / (2 * epsilon);

            if (Math.abs(numerical - analytical.get(i)) > 1e-5) {
                throw new DomainException(
                    "Gradient verification failed at " + i
                );
            }
        }
    }

    // ========================================================
    // 12. Main execution
    // ========================================================

    public static void main(String[] args) {

        try {
            verifyBellState();

            CircuitConfiguration configuration =
                CircuitConfiguration.create(2, 2);

            CircuitService circuit =
                new CircuitService(configuration);

            List<Double> initialParameters = new ArrayList<>();

            for (int i = 0; i < circuit.parameterCount(); i++) {
                initialParameters.add(
                    0.25 * Math.sin(i + 1)
                );
            }

            verifyGradient(circuit, initialParameters);

            OptimizationPolicy policy = new OptimizationPolicy(
                OptimizationMethod.ADAM,
                0.04,
                150,
                1e-8,
                true
            );

            GradientService gradientService =
                new GradientService();

            OptimizationService optimizationService =
                new OptimizationService(
                    policy,
                    gradientService
                );

            ExperimentRepository repository =
                new ExperimentRepository();

            ExperimentApplicationService application =
                new ExperimentApplicationService(
                    repository,
                    optimizationService
                );

            Experiment experiment = application.execute(
                circuit,
                initialParameters
            );

            OptimizationResult result = experiment.result();

            System.out.println(
                "VARIATIONAL QUANTUM ENTERPRISE ENGINE"
            );

            System.out.println("Experiment ID: " + experiment.id());
            System.out.println("Status: " + experiment.status());
            System.out.println(
                "Qubits: " + configuration.qubits()
            );

            System.out.println(
                "Layers: " + configuration.layers()
            );

            System.out.println(
                "Parameters: " + circuit.parameterCount()
            );

            System.out.println(
                "Initial energy: " + result.initialEnergy()
            );

            System.out.println(
                "Final energy: " + result.finalEnergy()
            );

            System.out.println(
                "Iterations: " + result.iterations()
            );

            System.out.println(
                "Converged: " + result.converged()
            );

            System.out.println("\nOPTIMIZED PARAMETERS");

            for (int i = 0; i < result.parameters().size(); i++) {
                System.out.printf(
                    "theta[%d] = %.8f%n",
                    i,
                    result.parameters().get(i)
                );
            }

            QuantumRegister finalState =
                circuit.execute(result.parameters());

            System.out.println("\nFINAL PROBABILITIES");

            double[] probabilities = finalState.probabilities();

            for (int i = 0; i < probabilities.length; i++) {
                System.out.printf(
                    "%d : %.8f%n",
                    i,
                    probabilities[i]
                );
            }

            double total = 0;

            for (double probability : probabilities) {
                total += probability;
            }

            if (Math.abs(total - 1.0) > 1e-9) {
                throw new DomainException(
                    "Probability normalization failed."
                );
            }

            System.out.println("\nAll verification checks passed.");

        } catch (RuntimeException error) {
            System.err.println(
                "Application failure: " + error.getMessage()
            );

            System.exit(1);
        }
    }
}
