import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/*
 * QUANTUM NEURAL NETWORKS: FUNDAMENTALS
 *
 * Enterprise-oriented variational quantum learning model.
 *
 * Java 17 features:
 * - Records and enums
 * - Immutable domain objects
 * - Interfaces and generics
 * - Quantum state simulation
 * - Parameterized quantum circuits
 * - Feature encoding
 * - Parameter-shift optimization
 * - Training services
 * - Experiment policies
 * - Evaluation and validation
 *
 * Dependencies: Java 17 standard library only.
 */

public class QuantumNeuralNetwork {

    private static final double PI = Math.PI;
    private static final double EPSILON = 1e-9;

    enum ExperimentStatus {
        CREATED,
        VALIDATING,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum GateType {
        RY,
        RZ,
        CNOT
    }

    static class QuantumException extends RuntimeException {
        QuantumException(String message) {
            super(message);
        }
    }

    static class ValidationException extends QuantumException {
        ValidationException(String message) {
            super(message);
        }
    }

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

        Complex scale(double factor) {
            return new Complex(real * factor, imaginary * factor);
        }

        double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }
    }

    record FeatureVector(double first, double second) {

        FeatureVector {
            if (!Double.isFinite(first) ||
                !Double.isFinite(second)) {
                throw new ValidationException(
                    "Feature values must be finite."
                );
            }
        }

        double[] values() {
            return new double[]{first, second};
        }
    }

    record TrainingExample(
        FeatureVector features,
        int target
    ) {
        TrainingExample {
            Objects.requireNonNull(features);

            if (target != -1 && target != 1) {
                throw new ValidationException(
                    "Classification target must be -1 or +1."
                );
            }
        }
    }

    record TrainingPolicy(
        int epochs,
        double learningRate,
        double lossThreshold,
        int maximumExamples
    ) {
        TrainingPolicy {
            if (epochs <= 0 ||
                !Double.isFinite(learningRate) ||
                learningRate <= 0 ||
                learningRate > 1 ||
                lossThreshold < 0 ||
                maximumExamples <= 0) {

                throw new ValidationException(
                    "Invalid training policy."
                );
            }
        }
    }

    record TrainingMetrics(
        int epoch,
        double loss,
        double accuracy
    ) {}

    record ExperimentResult(
        ExperimentStatus status,
        int epochsExecuted,
        List<Double> parameters,
        double finalLoss,
        double accuracy
    ) {
        ExperimentResult {
            parameters = List.copyOf(parameters);
        }
    }

    interface QuantumModel {
        double forward(
            FeatureVector features,
            double[] parameters
        );
    }

    static class QuantumRegister {

        private final int qubits;
        private final Complex[] state;

        QuantumRegister(int qubits) {
            if (qubits < 1 || qubits > 20) {
                throw new ValidationException(
                    "Qubit count must be between 1 and 20."
                );
            }

            this.qubits = qubits;
            this.state = new Complex[1 << qubits];

            for (int i = 0; i < state.length; i++) {
                state[i] = new Complex(0, 0);
            }

            state[0] = new Complex(1, 0);
        }

        private void validateQubit(int qubit) {
            if (qubit < 0 || qubit >= qubits) {
                throw new ValidationException(
                    "Qubit index out of range."
                );
            }
        }

        private void applyGate(
            int qubit,
            Complex a,
            Complex b,
            Complex c,
            Complex d
        ) {
            validateQubit(qubit);

            int mask = 1 << qubit;

            for (int i = 0; i < state.length; i++) {
                if ((i & mask) != 0) continue;

                int j = i | mask;

                Complex alpha = state[i];
                Complex beta = state[j];

                state[i] = a.multiply(alpha)
                    .add(b.multiply(beta));

                state[j] = c.multiply(alpha)
                    .add(d.multiply(beta));
            }
        }

        void ry(int qubit, double angle) {
            if (!Double.isFinite(angle)) {
                throw new ValidationException("Invalid rotation angle.");
            }

            double c = Math.cos(angle / 2);
            double s = Math.sin(angle / 2);

            applyGate(
                qubit,
                new Complex(c, 0),
                new Complex(-s, 0),
                new Complex(s, 0),
                new Complex(c, 0)
            );
        }

        void rz(int qubit, double angle) {
            if (!Double.isFinite(angle)) {
                throw new ValidationException("Invalid rotation angle.");
            }

            double c = Math.cos(angle / 2);
            double s = Math.sin(angle / 2);

            applyGate(
                qubit,
                new Complex(c, -s),
                new Complex(0, 0),
                new Complex(0, 0),
                new Complex(c, s)
            );
        }

        void cnot(int control, int target) {
            validateQubit(control);
            validateQubit(target);

            if (control == target) {
                throw new ValidationException(
                    "CNOT control and target must differ."
                );
            }

            int controlMask = 1 << control;
            int targetMask = 1 << target;

            for (int i = 0; i < state.length; i++) {
                if ((i & controlMask) != 0 &&
                    (i & targetMask) == 0) {

                    int j = i | targetMask;

                    Complex temporary = state[i];
                    state[i] = state[j];
                    state[j] = temporary;
                }
            }
        }

        double[] probabilities() {
            double[] result = new double[state.length];

            for (int i = 0; i < state.length; i++) {
                result[i] = state[i].magnitudeSquared();
            }

            return result;
        }

        double expectationZ(int qubit) {
            validateQubit(qubit);

            double expectation = 0;
            int mask = 1 << qubit;

            for (int i = 0; i < state.length; i++) {
                double sign = (i & mask) != 0 ? -1 : 1;

                expectation +=
                    sign * state[i].magnitudeSquared();
            }

            return expectation;
        }

        void validateNormalization() {
            double norm = 0;

            for (Complex amplitude : state) {
                norm += amplitude.magnitudeSquared();
            }

            if (Math.abs(norm - 1.0) > EPSILON) {
                throw new QuantumException(
                    "Quantum state normalization failed."
                );
            }
        }
    }

    static class FeatureEncoder {

        void encode(
            QuantumRegister register,
            FeatureVector features
        ) {
            double[] values = features.values();

            register.ry(0, values[0]);
            register.ry(1, values[1]);
        }
    }

    static class VariationalQuantumClassifier
        implements QuantumModel {

        private static final int PARAMETER_COUNT = 4;

        private final FeatureEncoder encoder = new FeatureEncoder();

        @Override
        public double forward(
            FeatureVector features,
            double[] parameters
        ) {

            Objects.requireNonNull(features);

            if (parameters.length != PARAMETER_COUNT) {
                throw new ValidationException(
                    "Exactly four parameters are required."
                );
            }

            for (double parameter : parameters) {
                if (!Double.isFinite(parameter)) {
                    throw new ValidationException(
                        "Parameters must be finite."
                    );
                }
            }

            QuantumRegister register = new QuantumRegister(2);

            encoder.encode(register, features);

            // First trainable quantum layer.
            register.ry(0, parameters[0]);
            register.ry(1, parameters[1]);
            register.cnot(0, 1);

            // Second trainable quantum layer.
            register.ry(0, parameters[2]);
            register.ry(1, parameters[3]);
            register.cnot(1, 0);

            register.validateNormalization();

            return register.expectationZ(0);
        }

        int classify(
            FeatureVector features,
            double[] parameters
        ) {
            return forward(features, parameters) >= 0 ? 1 : -1;
        }
    }

    static class Dataset {

        private final List<TrainingExample> examples;

        Dataset(List<TrainingExample> examples) {
            if (examples == null || examples.isEmpty()) {
                throw new ValidationException(
                    "Training dataset cannot be empty."
                );
            }

            this.examples = List.copyOf(examples);
        }

        List<TrainingExample> examples() {
            return examples;
        }

        int size() {
            return examples.size();
        }
    }

    static class QuantumTrainingService {

        private final QuantumModel model;
        private final VariationalQuantumClassifier classifier;
        private final TrainingPolicy policy;

        private double[] parameters = {
            0.2, -0.3, 0.4, 0.1
        };

        QuantumTrainingService(
            TrainingPolicy policy
        ) {
            this.policy = Objects.requireNonNull(policy);
            this.classifier = new VariationalQuantumClassifier();
            this.model = classifier;
        }

        private void validateDataset(Dataset dataset) {
            Objects.requireNonNull(dataset);

            if (dataset.size() > policy.maximumExamples()) {
                throw new ValidationException(
                    "Dataset exceeds configured example limit."
                );
            }
        }

        double calculateLoss(Dataset dataset) {
            double total = 0;

            for (TrainingExample example : dataset.examples()) {
                double output = model.forward(
                    example.features(),
                    parameters
                );

                total += Math.pow(
                    output - example.target(),
                    2
                );
            }

            return total / dataset.size();
        }

        double[] calculateGradient(Dataset dataset) {
            double[] gradients = new double[parameters.length];

            /*
             * Parameter-shift gradient estimation.
             * Every trainable parameter appears in one RY gate.
             */

            for (int i = 0; i < parameters.length; i++) {
                double[] plus = parameters.clone();
                double[] minus = parameters.clone();

                plus[i] += PI / 2;
                minus[i] -= PI / 2;

                double originalLoss = calculateLoss(dataset);

                parameters = plus;
                double plusLoss = calculateLoss(dataset);

                parameters = minus;
                double minusLoss = calculateLoss(dataset);

                parameters = new double[]{
                    0.2, -0.3, 0.4, 0.1
                };

                // Restore the actual current parameter vector.
                parameters = currentParameters;

                gradients[i] = (plusLoss - minusLoss) / 2;
            }

            return gradients;
        }

        private double[] currentParameters;

        private double[] computeGradient(Dataset dataset) {
            double[] gradients = new double[parameters.length];

            double[] original = parameters.clone();

            for (int i = 0; i < parameters.length; i++) {
                double[] plus = original.clone();
                double[] minus = original.clone();

                plus[i] += PI / 2;
                minus[i] -= PI / 2;

                parameters = plus;
                double plusLoss = calculateLoss(dataset);

                parameters = minus;
                double minusLoss = calculateLoss(dataset);

                gradients[i] = (plusLoss - minusLoss) / 2;
            }

            parameters = original;
            return gradients;
        }

        double accuracy(Dataset dataset) {
            int correct = 0;

            for (TrainingExample example : dataset.examples()) {
                int prediction = classifier.classify(
                    example.features(),
                    parameters
                );

                if (prediction == example.target()) {
                    correct++;
                }
            }

            return (double) correct / dataset.size();
        }

        ExperimentResult train(Dataset dataset) {
            validateDataset(dataset);

            ExperimentStatus status = ExperimentStatus.VALIDATING;

            try {
                status = ExperimentStatus.RUNNING;

                List<TrainingMetrics> history = new ArrayList<>();

                int executedEpochs = 0;

                for (int epoch = 1; epoch <= policy.epochs(); epoch++) {

                    double[] gradients = computeGradient(dataset);

                    for (int i = 0; i < parameters.length; i++) {
                        parameters[i] -=
                            policy.learningRate() * gradients[i];
                    }

                    double loss = calculateLoss(dataset);
                    double accuracy = accuracy(dataset);

                    history.add(new TrainingMetrics(
                        epoch,
                        loss,
                        accuracy
                    ));

                    executedEpochs = epoch;

                    if (loss < policy.lossThreshold()) {
                        break;
                    }
                }

                status = ExperimentStatus.COMPLETED;

                List<Double> parameterList = new ArrayList<>();

                for (double parameter : parameters) {
                    parameterList.add(parameter);
                }

                return new ExperimentResult(
                    status,
                    executedEpochs,
                    parameterList,
                    calculateLoss(dataset),
                    accuracy(dataset)
                );

            } catch (RuntimeException exception) {
                status = ExperimentStatus.FAILED;
                throw new QuantumException(
                    "Training failed in state " + status +
                    ": " + exception.getMessage()
                );
            }
        }

        double[] getParameters() {
            return parameters.clone();
        }
    }

    static class ExperimentService {

        private final TrainingPolicy policy;

        ExperimentService(TrainingPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        ExperimentResult execute(Dataset dataset) {
            QuantumTrainingService training =
                new QuantumTrainingService(policy);

            return training.train(dataset);
        }
    }

    private static void runTests() {

        QuantumRegister register = new QuantumRegister(1);
        register.ry(0, PI / 2);

        if (Math.abs(register.expectationZ(0)) > EPSILON) {
            throw new QuantumException("RY validation failed.");
        }

        QuantumRegister bell = new QuantumRegister(2);
        bell.ry(0, PI / 2);
        bell.cnot(0, 1);

        double[] probabilities = bell.probabilities();

        if (Math.abs(probabilities[0] - 0.5) > EPSILON ||
            Math.abs(probabilities[3] - 0.5) > EPSILON) {

            throw new QuantumException("Bell-state validation failed.");
        }

        System.out.println("All Java 17 quantum tests passed.");
    }

    public static void main(String[] args) {

        try {
            runTests();

            System.out.println(
                "\nQUANTUM NEURAL NETWORK FUNDAMENTALS"
            );

            System.out.println(
                "==================================="
            );

            List<TrainingExample> examples = List.of(
                new TrainingExample(
                    new FeatureVector(0.2, 0.3), 1
                ),
                new TrainingExample(
                    new FeatureVector(0.3, 0.5), 1
                ),
                new TrainingExample(
                    new FeatureVector(2.8, 2.5), -1
                ),
                new TrainingExample(
                    new FeatureVector(2.5, 2.9), -1
                ),
                new TrainingExample(
                    new FeatureVector(0.5, 0.2), 1
                ),
                new TrainingExample(
                    new FeatureVector(2.9, 2.7), -1
                )
            );

            Dataset dataset = new Dataset(examples);

            TrainingPolicy policy = new TrainingPolicy(
                100,
                0.05,
                1e-7,
                10000
            );

            ExperimentService service =
                new ExperimentService(policy);

            ExperimentResult result = service.execute(dataset);

            System.out.println("\nExperiment result");
            System.out.println("Status: " + result.status());
            System.out.println("Epochs: " + result.epochsExecuted());
            System.out.println("Parameters: " + result.parameters());
            System.out.println("Final loss: " + result.finalLoss());
            System.out.println("Accuracy: " + result.accuracy());

            System.out.println("\nEnterprise training report");
            System.out.println("-----------------------------------");

            System.out.println(
                "Model: Two-qubit variational classifier"
            );

            System.out.println(
                "Feature encoder: Angle encoding using RY"
            );

            System.out.println(
                "Ansatz: Two entangling variational layers"
            );

            System.out.println(
                "Observable: Pauli-Z on qubit zero"
            );

            System.out.println(
                "Gradient: Parameter-shift rule"
            );

        } catch (QuantumException exception) {
            System.err.println(
                "Quantum experiment error: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
