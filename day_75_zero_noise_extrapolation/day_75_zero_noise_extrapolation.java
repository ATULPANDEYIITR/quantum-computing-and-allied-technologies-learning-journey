import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/*
 * Zero-Noise Extrapolation: Enterprise Java 17 Model
 *
 * Enterprise-oriented design:
 * - Immutable experiment configuration
 * - Explicit domain records
 * - Typed extrapolation policies
 * - Measurement acquisition service
 * - Polynomial regression service
 * - Richardson extrapolation
 * - Shot-budget enforcement
 * - Experiment lifecycle management
 * - Validation and audit reporting
 */

public class ZeroNoiseExtrapolation {

    enum ExperimentStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED
    }

    enum ExtrapolationMethod {
        LINEAR,
        QUADRATIC,
        RICHARDSON
    }

    record NoiseConfiguration(
        double idealValue,
        double linearCoefficient,
        double quadraticCoefficient
    ) {
        NoiseConfiguration {
            if (!Double.isFinite(idealValue)
                    || idealValue < -1.0
                    || idealValue > 1.0) {
                throw new ValidationException(
                    "Ideal observable must be in [-1, 1]."
                );
            }

            if (!Double.isFinite(linearCoefficient)
                    || !Double.isFinite(quadraticCoefficient)) {
                throw new ValidationException(
                    "Noise coefficients must be finite."
                );
            }
        }
    }

    record Measurement(
        double scale,
        double observable,
        double standardError,
        int shots
    ) {
        Measurement {
            if (!Double.isFinite(scale) || scale < 1.0) {
                throw new ValidationException(
                    "Noise scale must be >= 1."
                );
            }

            if (!Double.isFinite(observable)
                    || observable < -1.0
                    || observable > 1.0) {
                throw new ValidationException(
                    "Observable must be in [-1, 1]."
                );
            }

            if (!Double.isFinite(standardError)
                    || standardError < 0.0) {
                throw new ValidationException(
                    "Invalid standard error."
                );
            }

            if (shots < 2) {
                throw new ValidationException(
                    "Shots must be >= 2."
                );
            }
        }
    }

    record ExperimentConfiguration(
        List<Double> noiseScales,
        int shotsPerScale,
        int maximumShots,
        ExtrapolationMethod method
    ) {
        ExperimentConfiguration {
            noiseScales = List.copyOf(noiseScales);

            if (noiseScales.size() < 2) {
                throw new ValidationException(
                    "At least two noise scales are required."
                );
            }

            if (noiseScales.stream().anyMatch(
                    scale -> scale == null
                            || !Double.isFinite(scale)
                            || scale < 1.0)) {
                throw new ValidationException(
                    "Invalid noise scale."
                );
            }

            if (new HashSet<>(noiseScales).size()
                    != noiseScales.size()) {
                throw new ValidationException(
                    "Noise scales must be unique."
                );
            }

            if (shotsPerScale < 2 || maximumShots < 2) {
                throw new ValidationException(
                    "Invalid shot budget."
                );
            }

            int requiredScales =
                method == ExtrapolationMethod.RICHARDSON
                    ? 2 : noiseScales.size();

            if ((long) requiredScales * shotsPerScale
                    > maximumShots) {
                throw new ValidationException(
                    "Maximum shot budget is insufficient."
                );
            }
        }
    }

    record RegressionResult(
        double intercept,
        List<Double> coefficients
    ) {
        RegressionResult {
            coefficients = List.copyOf(coefficients);
        }
    }

    record ExperimentResult(
        UUID experimentId,
        ExperimentStatus status,
        ExtrapolationMethod method,
        double idealValue,
        double noisyBaseline,
        double mitigatedEstimate,
        double baselineError,
        double mitigationError,
        int shotsConsumed,
        List<Measurement> measurements,
        List<Double> coefficients
    ) {
        ExperimentResult {
            measurements = List.copyOf(measurements);
            coefficients = List.copyOf(coefficients);
        }
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class ExperimentException extends RuntimeException {
        ExperimentException(String message) {
            super(message);
        }
    }

    interface MeasurementProvider {
        Measurement acquire(double scale, int shots);
    }

    interface ExtrapolationPolicy {
        RegressionResult extrapolate(
            List<Measurement> measurements
        );
    }

    static class ShotBudget {
        private final int maximum;
        private int consumed;

        ShotBudget(int maximum) {
            if (maximum < 2) {
                throw new ValidationException(
                    "Shot budget must be >= 2."
                );
            }

            this.maximum = maximum;
        }

        synchronized void reserve(int shots) {
            if (shots < 2) {
                throw new ValidationException(
                    "Invalid shot reservation."
                );
            }

            if (shots > maximum - consumed) {
                throw new ExperimentException(
                    "Shot budget exceeded."
                );
            }

            consumed += shots;
        }

        synchronized int consumed() {
            return consumed;
        }

        synchronized int remaining() {
            return maximum - consumed;
        }
    }

    static class SimulatedMeasurementProvider
            implements MeasurementProvider {

        private final NoiseConfiguration noise;
        private final Random random;

        SimulatedMeasurementProvider(
            NoiseConfiguration noise,
            long seed
        ) {
            this.noise = noise;
            this.random = new Random(seed);
        }

        private double expectation(double scale) {
            double value =
                noise.idealValue()
                + noise.linearCoefficient() * scale
                + noise.quadraticCoefficient() * scale * scale;

            return Math.max(-1.0, Math.min(1.0, value));
        }

        @Override
        public synchronized Measurement acquire(
            double scale,
            int shots
        ) {
            if (!Double.isFinite(scale) || scale < 1.0
                    || shots < 2) {
                throw new ValidationException(
                    "Invalid measurement request."
                );
            }

            double probability =
                (1.0 + expectation(scale)) / 2.0;

            int positive = 0;

            for (int i = 0; i < shots; i++) {
                if (random.nextDouble() < probability) {
                    positive++;
                }
            }

            double estimate =
                2.0 * positive / shots - 1.0;

            double standardError = Math.sqrt(
                Math.max(0.0, 1.0 - estimate * estimate) / shots
            );

            return new Measurement(
                scale,
                estimate,
                standardError,
                shots
            );
        }
    }

    static class PolynomialRegression {

        static RegressionResult fit(
            List<Measurement> measurements,
            int degree
        ) {
            if (degree < 1 || degree > 2) {
                throw new ValidationException(
                    "Only linear and quadratic fitting are supported."
                );
            }

            if (measurements.size() < degree + 1) {
                throw new ExperimentException(
                    "Insufficient observations."
                );
            }

            long distinct = measurements.stream()
                .map(Measurement::scale)
                .distinct()
                .count();

            if (distinct < degree + 1) {
                throw new ExperimentException(
                    "Insufficient distinct scales."
                );
            }

            int n = degree + 1;

            double[][] matrix = new double[n][n];
            double[] vector = new double[n];

            for (int row = 0; row < n; row++) {
                for (int col = 0; col < n; col++) {
                    final int power = row + col;

                    matrix[row][col] = measurements.stream()
                        .mapToDouble(m -> Math.pow(m.scale(), power))
                        .sum();
                }

                vector[row] = measurements.stream()
                    .mapToDouble(m ->
                        m.observable() *
                        Math.pow(m.scale(), row)
                    )
                    .sum();
            }

            double[] coefficients =
                solve(matrix, vector);

            List<Double> values = Arrays.stream(coefficients)
                .boxed()
                .toList();

            return new RegressionResult(
                coefficients[0],
                values
            );
        }

        private static double[] solve(
            double[][] matrix,
            double[] vector
        ) {
            int n = vector.length;

            for (int col = 0; col < n; col++) {
                int pivot = col;

                for (int row = col + 1; row < n; row++) {
                    if (Math.abs(matrix[row][col])
                            > Math.abs(matrix[pivot][col])) {
                        pivot = row;
                    }
                }

                if (Math.abs(matrix[pivot][col]) < 1e-12) {
                    throw new ExperimentException(
                        "Singular regression matrix."
                    );
                }

                double[] temporary = matrix[col];
                matrix[col] = matrix[pivot];
                matrix[pivot] = temporary;

                double value = vector[col];
                vector[col] = vector[pivot];
                vector[pivot] = value;

                double divisor = matrix[col][col];

                for (int j = col; j < n; j++) {
                    matrix[col][j] /= divisor;
                }

                vector[col] /= divisor;

                for (int row = 0; row < n; row++) {
                    if (row == col) continue;

                    double factor = matrix[row][col];

                    for (int j = col; j < n; j++) {
                        matrix[row][j] -=
                            factor * matrix[col][j];
                    }

                    vector[row] -= factor * vector[col];
                }
            }

            return vector;
        }
    }

    static class LinearPolicy implements ExtrapolationPolicy {
        @Override
        public RegressionResult extrapolate(
            List<Measurement> measurements
        ) {
            return PolynomialRegression.fit(measurements, 1);
        }
    }

    static class QuadraticPolicy implements ExtrapolationPolicy {
        @Override
        public RegressionResult extrapolate(
            List<Measurement> measurements
        ) {
            return PolynomialRegression.fit(measurements, 2);
        }
    }

    static class RichardsonPolicy implements ExtrapolationPolicy {
        @Override
        public RegressionResult extrapolate(
            List<Measurement> measurements
        ) {
            if (measurements.size() != 2) {
                throw new ExperimentException(
                    "Richardson requires two measurements."
                );
            }

            Measurement a = measurements.get(0);
            Measurement b = measurements.get(1);

            if (a.scale() == b.scale()) {
                throw new ValidationException(
                    "Noise scales must differ."
                );
            }

            double estimate =
                (b.scale() * a.observable()
                    - a.scale() * b.observable())
                / (b.scale() - a.scale());

            return new RegressionResult(
                estimate,
                List.of()
            );
        }
    }

    static class PolicyFactory {
        static ExtrapolationPolicy create(
            ExtrapolationMethod method
        ) {
            return switch (method) {
                case LINEAR -> new LinearPolicy();
                case QUADRATIC -> new QuadraticPolicy();
                case RICHARDSON -> new RichardsonPolicy();
            };
        }
    }

    static class ExperimentService {

        private final MeasurementProvider provider;
        private final AtomicLong executionCounter =
            new AtomicLong();

        ExperimentService(MeasurementProvider provider) {
            this.provider = Objects.requireNonNull(provider);
        }

        ExperimentResult execute(
            ExperimentConfiguration configuration,
            double idealReference
        ) {
            Objects.requireNonNull(configuration);

            if (!Double.isFinite(idealReference)
                    || idealReference < -1.0
                    || idealReference > 1.0) {
                throw new ValidationException(
                    "Invalid ideal reference."
                );
            }

            long executionId = executionCounter.incrementAndGet();

            ShotBudget budget = new ShotBudget(
                configuration.maximumShots()
            );

            List<Double> scales = configuration.noiseScales()
                .stream()
                .sorted()
                .collect(Collectors.toCollection(ArrayList::new));

            if (configuration.method()
                    == ExtrapolationMethod.RICHARDSON) {
                scales = new ArrayList<>(scales.subList(0, 2));
            }

            List<Measurement> measurements = new ArrayList<>();

            try {
                for (double scale : scales) {
                    budget.reserve(configuration.shotsPerScale());

                    measurements.add(
                        provider.acquire(
                            scale,
                            configuration.shotsPerScale()
                        )
                    );
                }

                ExtrapolationPolicy policy =
                    PolicyFactory.create(configuration.method());

                RegressionResult regression =
                    policy.extrapolate(measurements);

                double baseline =
                    measurements.get(0).observable();

                return new ExperimentResult(
                    UUID.randomUUID(),
                    ExperimentStatus.COMPLETED,
                    configuration.method(),
                    idealReference,
                    baseline,
                    regression.intercept(),
                    Math.abs(baseline - idealReference),
                    Math.abs(regression.intercept() - idealReference),
                    budget.consumed(),
                    measurements,
                    regression.coefficients()
                );

            } catch (RuntimeException exception) {
                throw new ExperimentException(
                    "Experiment " + executionId
                    + " failed: " + exception.getMessage()
                );
            }
        }
    }

    static void runTests() {
        List<Measurement> points = List.of(
            new Measurement(1.0, 0.8, 0.01, 10000),
            new Measurement(2.0, 0.5, 0.01, 10000),
            new Measurement(3.0, 0.15, 0.01, 10000)
        );

        RegressionResult result =
            PolynomialRegression.fit(points, 2);

        if (Math.abs(result.intercept() - 1.0) > 1e-9) {
            throw new AssertionError(
                "Quadratic regression test failed."
            );
        }

        RichardsonPolicy policy = new RichardsonPolicy();

        RegressionResult richardson = policy.extrapolate(
            List.of(
                new Measurement(1.0, 0.8, 0.01, 10000),
                new Measurement(2.0, 0.6, 0.01, 10000)
            )
        );

        if (Math.abs(richardson.intercept() - 1.0) > 1e-9) {
            throw new AssertionError(
                "Richardson test failed."
            );
        }

        System.out.println("All Java self-tests passed.");
    }

    public static void main(String[] args) {
        runTests();

        NoiseConfiguration noise = new NoiseConfiguration(
            0.85,
            -0.12,
            -0.025
        );

        List<Double> scales = List.of(
            1.0, 1.5, 2.0, 2.5
        );

        for (ExtrapolationMethod method :
                ExtrapolationMethod.values()) {

            MeasurementProvider provider =
                new SimulatedMeasurementProvider(noise, 42);

            ExperimentService service =
                new ExperimentService(provider);

            ExperimentConfiguration configuration =
                new ExperimentConfiguration(
                    scales,
                    20000,
                    1000000,
                    method
                );

            ExperimentResult result = service.execute(
                configuration,
                noise.idealValue()
            );

            System.out.println("\nMethod: " + result.method());
            System.out.printf(
                Locale.ROOT,
                "Ideal: %.6f%nBaseline: %.6f%nMitigated: %.6f%n",
                result.idealValue(),
                result.noisyBaseline(),
                result.mitigatedEstimate()
            );

            System.out.printf(
                Locale.ROOT,
                "Baseline error: %.6f%nMitigation error: %.6f%n",
                result.baselineError(),
                result.mitigationError()
            );

            System.out.println(
                "Shots consumed: " + result.shotsConsumed()
            );
        }
    }
}
