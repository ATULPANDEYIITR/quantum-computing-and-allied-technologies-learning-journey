import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;

/*
 * Hybrid Quantum-Classical Machine Learning
 *
 * Java 17 enterprise implementation.
 *
 * Components:
 * - Quantum backend interface
 * - State-vector simulation backend
 * - Quantum feature extraction
 * - Classical model training
 * - Experiment orchestration
 * - Model governance
 * - Approval and execution policies
 * - Immutable experiment records
 * - Failure handling
 */

public class HybridQuantumML {

    // -----------------------------------------------------
    // Domain exceptions
    // -----------------------------------------------------

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class BackendException extends RuntimeException {
        BackendException(String message) {
            super(message);
        }
    }

    // -----------------------------------------------------
    // Experiment lifecycle
    // -----------------------------------------------------

    enum ExperimentStatus {
        CREATED,
        VALIDATING,
        RUNNING,
        COMPLETED,
        FAILED,
        CANCELLED
    }

    enum ExecutionMode {
        SIMULATOR,
        HARDWARE,
        CLASSICAL_FALLBACK
    }

    enum ModelType {
        QUANTUM_KERNEL,
        VARIATIONAL_CLASSIFIER,
        HYBRID_FEATURE_CLASSIFIER
    }

    // -----------------------------------------------------
    // Immutable domain records
    // -----------------------------------------------------

    record Dataset(
        String datasetId,
        List<Sample> samples,
        int featureCount
    ) {
        Dataset {
            Objects.requireNonNull(datasetId);
            samples = List.copyOf(samples);

            if (datasetId.isBlank()) {
                throw new DomainException("Dataset ID is required");
            }

            if (samples.isEmpty()) {
                throw new DomainException("Dataset cannot be empty");
            }

            if (featureCount < 1) {
                throw new DomainException("Invalid feature count");
            }

            for (Sample sample : samples) {
                if (sample.features().size() != featureCount) {
                    throw new DomainException("Inconsistent feature dimensions");
                }
            }
        }
    }

    record Sample(List<Double> features, int label) {
        Sample {
            features = List.copyOf(features);

            if (features.isEmpty()) {
                throw new DomainException("Features cannot be empty");
            }

            if (label != 0 && label != 1) {
                throw new DomainException("Binary label required");
            }

            for (double value : features) {
                if (!Double.isFinite(value)) {
                    throw new DomainException("Non-finite feature");
                }
            }
        }
    }

    record BackendConfiguration(
        ExecutionMode mode,
        int qubits,
        int shots,
        long seed
    ) {
        BackendConfiguration {
            Objects.requireNonNull(mode);

            if (qubits < 1 || qubits > 12) {
                throw new DomainException("Qubits must be between 1 and 12");
            }

            if (shots <= 0) {
                throw new DomainException("Shots must be positive");
            }
        }
    }

    record TrainingPolicy(
        int epochs,
        double learningRate,
        double regularization,
        boolean allowFallback
    ) {
        TrainingPolicy {
            if (epochs <= 0) {
                throw new DomainException("Epochs must be positive");
            }

            if (!Double.isFinite(learningRate) || learningRate <= 0) {
                throw new DomainException("Invalid learning rate");
            }

            if (!Double.isFinite(regularization) || regularization <= 0) {
                throw new DomainException("Invalid regularization");
            }
        }
    }

    record Metrics(
        double accuracy,
        double precision,
        double recall,
        double f1,
        int truePositive,
        int trueNegative,
        int falsePositive,
        int falseNegative
    ) {}

    record ExperimentResult(
        String experimentId,
        ExperimentStatus status,
        ExecutionMode executionMode,
        ModelType modelType,
        double trainingLoss,
        Metrics metrics,
        long durationMillis
    ) {}

    // -----------------------------------------------------
    // Quantum backend contract
    // -----------------------------------------------------

    interface QuantumBackend {

        List<Double> execute(
            List<Double> features,
            List<Double> parameters
        );

        String backendName();

        ExecutionMode executionMode();
    }

    // -----------------------------------------------------
    // Quantum simulator
    // -----------------------------------------------------

    static final class StateVectorBackend implements QuantumBackend {

        private final int qubits;

        StateVectorBackend(int qubits) {
            if (qubits < 1 || qubits > 12) {
                throw new DomainException("Invalid qubit count");
            }

            this.qubits = qubits;
        }

        private record Complex(double real, double imaginary) {

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

            double magnitudeSquared() {
                return real * real + imaginary * imaginary;
            }
        }

        private static Complex[] initialState(int qubits) {
            Complex[] state = new Complex[1 << qubits];

            Arrays.fill(state, new Complex(0, 0));
            state[0] = new Complex(1, 0);

            return state;
        }

        private static void applyGate(
            Complex[] state,
            int qubits,
            int target,
            Complex[][] matrix
        ) {
            if (target < 0 || target >= qubits) {
                throw new BackendException("Invalid qubit");
            }

            int mask = 1 << target;

            for (int index = 0; index < state.length; index++) {
                if ((index & mask) != 0) continue;

                int paired = index | mask;

                Complex a = state[index];
                Complex b = state[paired];

                state[index] = matrix[0][0].multiply(a)
                    .add(matrix[0][1].multiply(b));

                state[paired] = matrix[1][0].multiply(a)
                    .add(matrix[1][1].multiply(b));
            }
        }

        private static void hadamard(
            Complex[] state,
            int qubits,
            int target
        ) {
            double c = 1 / Math.sqrt(2);

            applyGate(state, qubits, target, new Complex[][]{
                {
                    new Complex(c, 0),
                    new Complex(c, 0)
                },
                {
                    new Complex(c, 0),
                    new Complex(-c, 0)
                }
            });
        }

        private static void ry(
            Complex[] state,
            int qubits,
            int target,
            double theta
        ) {
            double c = Math.cos(theta / 2);
            double s = Math.sin(theta / 2);

            applyGate(state, qubits, target, new Complex[][]{
                {
                    new Complex(c, 0),
                    new Complex(-s, 0)
                },
                {
                    new Complex(s, 0),
                    new Complex(c, 0)
                }
            });
        }

        private static void cnot(
            Complex[] state,
            int qubits,
            int control,
            int target
        ) {
            if (control == target ||
                control < 0 ||
                target < 0 ||
                control >= qubits ||
                target >= qubits) {
                throw new BackendException("Invalid CNOT operation");
            }

            int cm = 1 << control;
            int tm = 1 << target;

            for (int index = 0; index < state.length; index++) {
                if ((index & cm) != 0 && (index & tm) == 0) {
                    int paired = index | tm;

                    Complex temporary = state[index];
                    state[index] = state[paired];
                    state[paired] = temporary;
                }
            }
        }

        @Override
        public List<Double> execute(
            List<Double> features,
            List<Double> parameters
        ) {
            if (features.size() != qubits ||
                parameters.size() != qubits * 2) {
                throw new BackendException("Circuit input dimension mismatch");
            }

            Complex[] state = initialState(qubits);

            for (int index = 0; index < qubits; index++) {
                hadamard(state, qubits, index);
                ry(state, qubits, index, features.get(index));
            }

            for (int index = 0; index < qubits; index++) {
                ry(state, qubits, index, parameters.get(index));
            }

            for (int index = 0; index < qubits - 1; index++) {
                cnot(state, qubits, index, index + 1);
            }

            List<Double> measurements = new ArrayList<>();

            for (int qubit = 0; qubit < qubits; qubit++) {
                double expectation = 0;
                int mask = 1 << qubit;

                for (int index = 0; index < state.length; index++) {
                    double probability =
                        state[index].magnitudeSquared();

                    expectation += (index & mask) != 0
                        ? -probability
                        : probability;
                }

                measurements.add(expectation);
            }

            return List.copyOf(measurements);
        }

        @Override
        public String backendName() {
            return "Java StateVector Simulator";
        }

        @Override
        public ExecutionMode executionMode() {
            return ExecutionMode.SIMULATOR;
        }
    }

    // -----------------------------------------------------
    // Classical prediction head
    // -----------------------------------------------------

    static final class LogisticHead {

        private final double[] weights;
        private double bias;
        private final double learningRate;

        LogisticHead(int inputs, double learningRate, long seed) {
            this.weights = new double[inputs];
            this.learningRate = learningRate;

            Random random = new Random(seed);

            for (int i = 0; i < inputs; i++) {
                weights[i] = (random.nextDouble() - 0.5) * 0.2;
            }
        }

        private double sigmoid(double value) {
            value = Math.max(-500, Math.min(500, value));
            return 1 / (1 + Math.exp(-value));
        }

        double probability(List<Double> features) {
            if (features.size() != weights.length) {
                throw new DomainException("Classifier input mismatch");
            }

            double result = bias;

            for (int i = 0; i < weights.length; i++) {
                result += weights[i] * features.get(i);
            }

            return sigmoid(result);
        }

        void update(List<Double> features, int label) {
            double error = probability(features) - label;

            for (int i = 0; i < weights.length; i++) {
                weights[i] -= learningRate * error * features.get(i);
            }

            bias -= learningRate * error;
        }
    }

    // -----------------------------------------------------
    // Hybrid model service
    // -----------------------------------------------------

    static final class HybridModelService {

        private final QuantumBackend backend;
        private final TrainingPolicy policy;
        private final LogisticHead classicalHead;
        private final List<Double> parameters;
        private final AtomicReference<ExperimentStatus> status;

        HybridModelService(
            QuantumBackend backend,
            TrainingPolicy policy,
            long seed
        ) {
            this.backend = backend;
            this.policy = policy;

            Random random = new Random(seed);

            List<Double> initialParameters = new ArrayList<>();

            for (int i = 0; i < backendQubits(backend); i++) {
                initialParameters.add((random.nextDouble() - 0.5) * 0.4);
            }

            for (int i = 0; i < backendQubits(backend); i++) {
                initialParameters.add((random.nextDouble() - 0.5) * 0.4);
            }

            this.parameters = initialParameters;

            this.classicalHead = new LogisticHead(
                backendQubits(backend),
                policy.learningRate(),
                seed
            );

            this.status = new AtomicReference<>(
                ExperimentStatus.CREATED
            );
        }

        private static int backendQubits(QuantumBackend backend) {
            if (!(backend instanceof StateVectorBackend simulator)) {
                throw new DomainException(
                    "This demonstration requires the state-vector backend"
                );
            }

            try {
                var field = StateVectorBackend.class.getDeclaredField("qubits");
                field.setAccessible(true);
                return field.getInt(simulator);
            } catch (ReflectiveOperationException error) {
                throw new DomainException("Backend configuration unavailable");
            }
        }

        private List<Double> quantumFeatures(Sample sample) {
            return backend.execute(
                sample.features(),
                parameters
            );
        }

        private double loss(Dataset dataset) {
            double total = 0;

            for (Sample sample : dataset.samples()) {
                double probability = classicalHead.probability(
                    quantumFeatures(sample)
                );

                probability = Math.max(
                    1e-12,
                    Math.min(1 - 1e-12, probability)
                );

                total -= sample.label() * Math.log(probability)
                    + (1 - sample.label()) * Math.log(1 - probability);
            }

            return total / dataset.samples().size();
        }

        private void updateQuantumParameters(Dataset dataset) {
            double shift = Math.PI / 2;
            double[] gradients = new double[parameters.size()];

            // Parameter-shift estimation for rotation parameters.
            for (int index = 0; index < parameters.size(); index++) {
                double original = parameters.get(index);

                parameters.set(index, original + shift);
                double positive = loss(dataset);

                parameters.set(index, original - shift);
                double negative = loss(dataset);

                parameters.set(index, original);

                gradients[index] = (positive - negative) / 2;
            }

            for (int index = 0; index < parameters.size(); index++) {
                parameters.set(
                    index,
                    parameters.get(index)
                        - policy.learningRate() * gradients[index]
                );
            }
        }

        double train(Dataset dataset) {
            if (!status.compareAndSet(
                ExperimentStatus.CREATED,
                ExperimentStatus.VALIDATING
            )) {
                throw new DomainException("Invalid experiment transition");
            }

            try {
                if (dataset.featureCount() !=
                    backendQubits(backend)) {
                    throw new DomainException("Dataset/backend mismatch");
                }

                status.set(ExperimentStatus.RUNNING);

                for (int epoch = 0; epoch < policy.epochs(); epoch++) {
                    updateQuantumParameters(dataset);

                    for (Sample sample : dataset.samples()) {
                        classicalHead.update(
                            quantumFeatures(sample),
                            sample.label()
                        );
                    }

                    double currentLoss = loss(dataset);

                    if (!Double.isFinite(currentLoss)) {
                        throw new DomainException("Training diverged");
                    }
                }

                status.set(ExperimentStatus.COMPLETED);
                return loss(dataset);

            } catch (RuntimeException error) {
                status.set(ExperimentStatus.FAILED);
                throw error;
            }
        }

        int predict(Sample sample) {
            if (status.get() != ExperimentStatus.COMPLETED) {
                throw new DomainException("Model is not ready");
            }

            return classicalHead.probability(
                quantumFeatures(sample)
            ) >= 0.5 ? 1 : 0;
        }

        ExperimentStatus status() {
            return status.get();
        }

        Metrics evaluate(Dataset dataset) {
            if (status.get() != ExperimentStatus.COMPLETED) {
                throw new DomainException("Evaluation requires a trained model");
            }

            int tp = 0;
            int tn = 0;
            int fp = 0;
            int fn = 0;

            for (Sample sample : dataset.samples()) {
                int prediction = predict(sample);

                if (prediction == 1 && sample.label() == 1) tp++;
                else if (prediction == 0 && sample.label() == 0) tn++;
                else if (prediction == 1) fp++;
                else fn++;
            }

            double precision = tp + fp == 0
                ? 0
                : (double) tp / (tp + fp);

            double recall = tp + fn == 0
                ? 0
                : (double) tp / (tp + fn);

            double f1 = precision + recall == 0
                ? 0
                : 2 * precision * recall / (precision + recall);

            return new Metrics(
                (double) (tp + tn) / dataset.samples().size(),
                precision,
                recall,
                f1,
                tp,
                tn,
                fp,
                fn
            );
        }
    }

    // -----------------------------------------------------
    // Experiment orchestration
    // -----------------------------------------------------

    static final class ExperimentService {

        private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

        ExperimentResult execute(
            Dataset training,
            Dataset testing,
            BackendConfiguration configuration,
            TrainingPolicy policy
        ) throws Exception {

            long start = System.nanoTime();

            if (training.featureCount() != testing.featureCount()) {
                throw new DomainException("Dataset dimensions differ");
            }

            if (training.featureCount() != configuration.qubits()) {
                throw new DomainException("Feature/qubit mismatch");
            }

            if (configuration.mode() != ExecutionMode.SIMULATOR) {
                throw new DomainException(
                    "No physical hardware adapter is configured"
                );
            }

            QuantumBackend backend =
                new StateVectorBackend(configuration.qubits());

            HybridModelService model = new HybridModelService(
                backend,
                policy,
                configuration.seed()
            );

            Future<Double> trainingFuture = executor.submit(
                () -> model.train(training)
            );

            double finalLoss;

            try {
                finalLoss = trainingFuture.get(
                    120,
                    TimeUnit.SECONDS
                );
            } catch (TimeoutException error) {
                trainingFuture.cancel(true);
                throw new DomainException("Training timed out");
            } catch (ExecutionException error) {
                throw new DomainException(
                    "Training failed: " + error.getCause().getMessage()
                );
            }

            Metrics metrics = model.evaluate(testing);

            long duration =
                TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - start);

            return new ExperimentResult(
                UUID.randomUUID().toString(),
                model.status(),
                backend.executionMode(),
                ModelType.HYBRID_FEATURE_CLASSIFIER,
                finalLoss,
                metrics,
                duration
            );
        }

        void shutdown() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException error) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }

    // -----------------------------------------------------
    // Dataset generation
    // -----------------------------------------------------

    static Dataset generateDataset(
        String id,
        int size,
        long seed
    ) {
        if (size < 20) {
            throw new DomainException("Dataset must contain at least 20 rows");
        }

        Random random = new Random(seed);

        List<Sample> samples = new ArrayList<>();

        for (int index = 0; index < size; index++) {
            double x = (random.nextDouble() * 2 - 1) * Math.PI;
            double y = (random.nextDouble() * 2 - 1) * Math.PI;

            int label = Math.sin(x) * Math.cos(y) > 0 ? 1 : 0;

            samples.add(
                new Sample(List.of(x, y), label)
            );
        }

        Collections.shuffle(samples, random);

        return new Dataset(id, samples, 2);
    }

    // -----------------------------------------------------
    // Validation tests
    // -----------------------------------------------------

    static void runTests() {
        QuantumBackend backend = new StateVectorBackend(2);

        List<Double> output = backend.execute(
            List.of(0.5, 0.7),
            List.of(0.1, 0.2, 0.3, 0.4)
        );

        if (output.size() != 2) {
            throw new AssertionError("Measurement dimension failure");
        }

        for (double value : output) {
            if (Math.abs(value) > 1.000001) {
                throw new AssertionError("Invalid expectation value");
            }
        }

        try {
            new BackendConfiguration(
                ExecutionMode.SIMULATOR,
                0,
                100,
                42
            );

            throw new AssertionError("Invalid configuration accepted");

        } catch (DomainException expected) {
            // Expected validation failure.
        }
    }

    // -----------------------------------------------------
    // Main
    // -----------------------------------------------------

    public static void main(String[] args) {
        runTests();

        Dataset complete = generateDataset(
            "training-dataset-001",
            100,
            42
        );

        int split = 80;

        Dataset training = new Dataset(
            "training-001",
            complete.samples().subList(0, split),
            2
        );

        Dataset testing = new Dataset(
            "testing-001",
            complete.samples().subList(split, complete.samples().size()),
            2
        );

        BackendConfiguration configuration =
            new BackendConfiguration(
                ExecutionMode.SIMULATOR,
                2,
                1000,
                42
            );

        TrainingPolicy policy = new TrainingPolicy(
            30,
            0.03,
            0.1,
            true
        );

        ExperimentService service = new ExperimentService();

        try {
            ExperimentResult result = service.execute(
                training,
                testing,
                configuration,
                policy
            );

            System.out.println("HYBRID QUANTUM-CLASSICAL ML");
            System.out.println("---------------------------");
            System.out.println("Experiment ID: " + result.experimentId());
            System.out.println("Status: " + result.status());
            System.out.println("Execution mode: " + result.executionMode());
            System.out.println("Model: " + result.modelType());
            System.out.printf(
                Locale.ROOT,
                "Training loss: %.6f%n",
                result.trainingLoss()
            );

            System.out.println("\nEvaluation metrics");

            Metrics metrics = result.metrics();

            System.out.printf(
                Locale.ROOT,
                "Accuracy: %.4f%n",
                metrics.accuracy()
            );

            System.out.printf(
                Locale.ROOT,
                "Precision: %.4f%n",
                metrics.precision()
            );

            System.out.printf(
                Locale.ROOT,
                "Recall: %.4f%n",
                metrics.recall()
            );

            System.out.printf(
                Locale.ROOT,
                "F1 score: %.4f%n",
                metrics.f1()
            );

            System.out.println(
                "Execution time: " + result.durationMillis() + " ms"
            );

        } finally {
            service.shutdown();
        }
    }
}
