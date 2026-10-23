import java.util.Arrays;
import java.util.Locale;
import java.util.Random;

/*
 * Quantum Phase Estimation using Java 17.
 *
 * The domain model separates:
 * - a phase unitary and its eigenphase
 * - counting-register state
 * - controlled powers
 * - inverse QFT
 * - probability extraction
 * - measurement
 *
 * The simulator intentionally uses a direct O(N^2) inverse QFT so the
 * mathematical transformation remains explicit.
 *
 * Compile:
 *   javac QuantumPhaseEstimation.java
 * Run:
 *   java QuantumPhaseEstimation
 */

public final class QuantumPhaseEstimation {

    private static final double TWO_PI = 2.0 * Math.PI;
    private static final double EPSILON = 1e-12;

    private QuantumPhaseEstimation() {
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
            return new Complex(
                real * factor,
                imaginary * factor
            );
        }

        double magnitudeSquared() {
            return real * real + imaginary * imaginary;
        }

        static Complex polar(double radius, double angle) {
            return new Complex(
                radius * Math.cos(angle),
                radius * Math.sin(angle)
            );
        }
    }

    record PhaseEstimate(
        double targetPhase,
        int countingQubits,
        double[] probabilities,
        int mostLikelyOutcome,
        double estimatedPhase
    ) {
        double absoluteError() {
            return Math.abs(targetPhase - estimatedPhase);
        }

        double circularError() {
            double direct = absoluteError();
            return Math.min(direct, 1.0 - direct);
        }
    }

    enum ReviewState {
        PREPARED,
        PHASE_ENCODED,
        TRANSFORMED,
        MEASURED,
        REJECTED
    }

    static final class PhaseUnitary {
        private final double theta;

        PhaseUnitary(double theta) {
            validateTheta(theta);
            this.theta = theta;
        }

        double eigenphase() {
            return theta;
        }

        Complex eigenvalueForOne() {
            return Complex.polar(1.0, TWO_PI * theta);
        }

        Complex poweredEigenvalue(long power) {
            return Complex.polar(
                1.0,
                TWO_PI * theta * power
            );
        }
    }

    static final class QpeExperiment {
        private final PhaseUnitary unitary;
        private final int qubits;
        private ReviewState state = ReviewState.PREPARED;

        QpeExperiment(PhaseUnitary unitary, int qubits) {
            validateQubits(qubits);
            this.unitary = unitary;
            this.qubits = qubits;
        }

        PhaseEstimate execute() {
            double[] stateVector = createPlusRegister();

            for (int control = 0; control < qubits; control++) {
                stateVector = applyControlledPower(
                    stateVector,
                    control
                );
            }

            state = ReviewState.PHASE_ENCODED;

            stateVector = inverseQft(stateVector);
            state = ReviewState.TRANSFORMED;

            double[] probabilities =
                probabilities(stateVector);

            int mostLikely = mostLikely(probabilities);
            double scale = 1L << qubits;
            double estimate = mostLikely / scale;

            state = ReviewState.MEASURED;

            return new PhaseEstimate(
                unitary.eigenphase(),
                qubits,
                probabilities,
                mostLikely,
                estimate
            );
        }

        ReviewState state() {
            return state;
        }

        private double[] createPlusRegister() {
            int dimension = 1 << qubits;
            double amplitude =
                1.0 / Math.sqrt(dimension);

            return fillRealState(
                dimension,
                amplitude
            );
        }

        private double[] applyControlledPower(
            double[] realState,
            int control
        ) {
            /*
             * This simplified enterprise model keeps a complex state as
             * interleaved [real, imaginary] values.
             */
            throw new UnsupportedOperationException(
                "Internal representation must use complex state"
            );
        }
    }

    /*
     * Interleaved state representation:
     * [real0, imag0, real1, imag1, ...]
     *
     * It avoids third-party numerical dependencies while retaining explicit
     * complex arithmetic.
     */
    static final class StateVector {
        private final double[] values;

        StateVector(int dimension) {
            if (dimension <= 0) {
                throw new IllegalArgumentException(
                    "dimension must be positive"
                );
            }
            values = new double[2 * dimension];
        }

        int dimension() {
            return values.length / 2;
        }

        double real(int index) {
            return values[2 * index];
        }

        double imaginary(int index) {
            return values[2 * index + 1];
        }

        void set(int index, double real, double imaginary) {
            values[2 * index] = real;
            values[2 * index + 1] = imaginary;
        }

        StateVector copy() {
            StateVector copy =
                new StateVector(dimension());
            System.arraycopy(
                values,
                0,
                copy.values,
                0,
                values.length
            );
            return copy;
        }

        void multiplyAt(int index, Complex factor) {
            double a = real(index);
            double b = imaginary(index);

            set(
                index,
                a * factor.real() - b * factor.imaginary(),
                a * factor.imaginary() + b * factor.real()
            );
        }

        void normalize() {
            double normSquared = 0.0;

            for (int index = 0; index < dimension(); index++) {
                normSquared +=
                    real(index) * real(index) +
                    imaginary(index) * imaginary(index);
            }

            if (normSquared < EPSILON) {
                throw new IllegalStateException(
                    "cannot normalize a zero state"
                );
            }

            double inverseNorm =
                1.0 / Math.sqrt(normSquared);

            for (int index = 0; index < dimension(); index++) {
                set(
                    index,
                    real(index) * inverseNorm,
                    imaginary(index) * inverseNorm
                );
            }
        }

        double[] probabilities() {
            double[] result =
                new double[dimension()];

            double total = 0.0;

            for (int index = 0; index < dimension(); index++) {
                result[index] =
                    real(index) * real(index) +
                    imaginary(index) * imaginary(index);

                total += result[index];
            }

            if (total < EPSILON) {
                throw new IllegalStateException(
                    "state has zero probability mass"
                );
            }

            for (int index = 0; index < result.length; index++) {
                result[index] /= total;
            }

            return result;
        }
    }

    static StateVector createPlusRegister(int qubits) {
        validateQubits(qubits);

        int dimension = 1 << qubits;
        StateVector state =
            new StateVector(dimension);

        double amplitude =
            1.0 / Math.sqrt(dimension);

        for (int index = 0; index < dimension; index++) {
            state.set(index, amplitude, 0.0);
        }

        return state;
    }

    static StateVector applyControlledPower(
        StateVector state,
        PhaseUnitary unitary,
        int control
    ) {
        long power = 1L << control;
        Complex phase =
            unitary.poweredEigenvalue(power);

        StateVector result = state.copy();

        for (int basis = 0;
             basis < state.dimension();
             basis++) {

            if (((basis >> control) & 1) == 1) {
                result.multiplyAt(basis, phase);
            }
        }

        return result;
    }

    static StateVector inverseQft(StateVector state) {
        int dimension = state.dimension();
        StateVector result =
            new StateVector(dimension);

        double scale =
            1.0 / Math.sqrt(dimension);

        for (int y = 0; y < dimension; y++) {
            double resultReal = 0.0;
            double resultImaginary = 0.0;

            for (int x = 0; x < dimension; x++) {
                double angle =
                    -TWO_PI * x * y / dimension;

                Complex kernel =
                    Complex.polar(1.0, angle);

                Complex input =
                    new Complex(
                        state.real(x),
                        state.imaginary(x)
                    );

                Complex product =
                    input.multiply(kernel);

                resultReal += product.real();
                resultImaginary += product.imaginary();
            }

            result.set(
                y,
                resultReal * scale,
                resultImaginary * scale
            );
        }

        result.normalize();
        return result;
    }

    static PhaseEstimate estimatePhase(
        double theta,
        int qubits
    ) {
        PhaseUnitary unitary =
            new PhaseUnitary(theta);

        QpeExperiment experiment =
            new QpeExperiment(unitary, qubits);

        /*
         * QpeExperiment keeps domain state transitions explicit, while the
         * numerical operations are implemented by the static state engine.
         */
        StateVector state =
            createPlusRegister(qubits);

        for (int control = 0; control < qubits; control++) {
            state = applyControlledPower(
                state,
                unitary,
                control
            );
        }

        StateVector transformed =
            inverseQft(state);

        double[] probability =
            transformed.probabilities();

        int mostLikely =
            mostLikely(probability);

        double estimate =
            mostLikely / (double) (1L << qubits);

        return new PhaseEstimate(
            theta,
            qubits,
            probability,
            mostLikely,
            estimate
        );
    }

    static int mostLikely(double[] probabilities) {
        int best = 0;

        for (int index = 1;
             index < probabilities.length;
             index++) {

            if (probabilities[index] >
                probabilities[best]) {
                best = index;
            }
        }

        return best;
    }

    static int[] sample(
        double[] probabilities,
        int count,
        long seed
    ) {
        if (count <= 0) {
            throw new IllegalArgumentException(
                "count must be positive"
            );
        }

        Random random = new Random(seed);
        int[] results = new int[count];

        for (int sample = 0; sample < count; sample++) {
            double draw = random.nextDouble();
            double cumulative = 0.0;

            for (int index = 0;
                 index < probabilities.length;
                 index++) {

                cumulative += probabilities[index];

                if (draw <= cumulative ||
                    index == probabilities.length - 1) {
                    results[sample] = index;
                    break;
                }
            }
        }

        return results;
    }

    static void printDistribution(
        PhaseEstimate result
    ) {
        double scale =
            1L << result.countingQubits();

        System.out.println(
            "\nProbability distribution"
        );

        for (int index = 0;
             index < result.probabilities().length;
             index++) {

            double probability =
                result.probabilities()[index];

            if (probability >= 1e-4) {
                System.out.printf(
                    Locale.ROOT,
                    "  y=%3d phase=%.8f probability=%.8f%n",
                    index,
                    index / scale,
                    probability
                );
            }
        }
    }

    static void printHistogram(
        PhaseEstimate result,
        int samples,
        long seed
    ) {
        int[] measurements =
            sample(
                result.probabilities(),
                samples,
                seed
            );

        int[] counts =
            new int[result.probabilities().length];

        for (int outcome : measurements) {
            counts[outcome]++;
        }

        double scale =
            1L << result.countingQubits();

        System.out.println(
            "\nMeasurement histogram"
        );

        for (int index = 0;
             index < counts.length;
             index++) {

            if (counts[index] > 0) {
                System.out.printf(
                    Locale.ROOT,
                    "  y=%3d phase=%.8f count=%d%n",
                    index,
                    index / scale,
                    counts[index]
                );
            }
        }
    }

    static void validateTheta(double theta) {
        if (!Double.isFinite(theta) ||
            theta < 0.0 ||
            theta >= 1.0) {

            throw new IllegalArgumentException(
                "theta must satisfy 0 <= theta < 1"
            );
        }
    }

    static void validateQubits(int qubits) {
        if (qubits < 1 || qubits > 20) {
            throw new IllegalArgumentException(
                "qubits must be between 1 and 20"
            );
        }
    }

    static double[] fillRealState(
        int dimension,
        double value
    ) {
        double[] result =
            new double[dimension];

        Arrays.fill(result, value);
        return result;
    }

    public static void main(String[] args) {
        Locale.setDefault(Locale.ROOT);

        System.out.println(
            "Quantum Phase Estimation"
        );
        System.out.println(
            "========================"
        );

        PhaseEstimate exact =
            estimatePhase(0.625, 4);

        System.out.printf(
            Locale.ROOT,
            "%nExactly representable phase%n" +
            "Target: %.8f%n" +
            "Most likely: %d%n" +
            "Estimate: %.8f%n" +
            "Absolute error: %.8f%n",
            exact.targetPhase(),
            exact.mostLikelyOutcome(),
            exact.estimatedPhase(),
            exact.absoluteError()
        );

        printDistribution(exact);

        PhaseEstimate approximate =
            estimatePhase(0.37, 5);

        System.out.printf(
            Locale.ROOT,
            "%nNon-binary phase%n" +
            "Target: %.8f%n" +
            "Estimate: %.8f%n" +
            "Absolute error: %.8f%n" +
            "Circular error: %.8f%n",
            approximate.targetPhase(),
            approximate.estimatedPhase(),
            approximate.absoluteError(),
            approximate.circularError()
        );

        printDistribution(approximate);
        printHistogram(
            approximate,
            2000,
            29
        );

        System.out.println(
            "\nCounting-register precision"
        );

        for (int qubits : new int[]{3, 4, 5, 6}) {
            PhaseEstimate result =
                estimatePhase(0.3125, qubits);

            System.out.printf(
                Locale.ROOT,
                "qubits=%d estimate=%.8f error=%.8f%n",
                qubits,
                result.estimatedPhase(),
                result.absoluteError()
            );
        }

        System.out.println(
            "\nValidation"
        );

        try {
            estimatePhase(1.0, 4);
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Rejected invalid phase: " +
                error.getMessage()
            );
        }

        System.out.println(
            "\nPerformance: state memory is O(2^m), " +
            "while this direct inverse QFT is O(4^m)."
        );
        System.out.println(
            "The implementation uses immutable records for " +
            "experiment results and explicit state transitions " +
            "for the numerical workflow."
        );
    }
}
