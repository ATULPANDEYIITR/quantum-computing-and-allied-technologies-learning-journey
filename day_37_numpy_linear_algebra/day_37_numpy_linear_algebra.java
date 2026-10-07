import java.util.Arrays;
import java.util.Objects;

public class LinearAlgebraEnterpriseDemo {

    enum MatrixRole {
        FEATURE_TRANSFORM,
        COVARIANCE,
        SYSTEM_MATRIX,
        PROJECTION
    }

    record VectorModel(String name, double[] values) {
        VectorModel {
            Objects.requireNonNull(name, "name");
            Objects.requireNonNull(values, "values");
            if (values.length == 0) {
                throw new IllegalArgumentException("Vector cannot be empty");
            }
            values = values.clone();
            for (double value : values) {
                if (!Double.isFinite(value)) {
                    throw new IllegalArgumentException(
                            "Vector contains a non-finite value"
                    );
                }
            }
        }

        @Override
        public double[] values() {
            return values.clone();
        }

        public int dimension() {
            return values.length;
        }
    }

    static final class MatrixModel {
        private final MatrixRole role;
        private final int rows;
        private final int columns;
        private final double[][] values;

        MatrixModel(MatrixRole role, double[][] source) {
            this.role = Objects.requireNonNull(role, "role");

            if (source == null || source.length == 0 ||
                    source[0] == null || source[0].length == 0) {
                throw new IllegalArgumentException("Matrix cannot be empty");
            }

            rows = source.length;
            columns = source[0].length;
            values = new double[rows][columns];

            for (int row = 0; row < rows; row++) {
                if (source[row] == null || source[row].length != columns) {
                    throw new IllegalArgumentException(
                            "Matrix must be rectangular"
                    );
                }

                for (int column = 0; column < columns; column++) {
                    if (!Double.isFinite(source[row][column])) {
                        throw new IllegalArgumentException(
                                "Matrix contains a non-finite value"
                        );
                    }
                    values[row][column] = source[row][column];
                }
            }
        }

        MatrixRole role() {
            return role;
        }

        int rows() {
            return rows;
        }

        int columns() {
            return columns;
        }

        double get(int row, int column) {
            if (row < 0 || row >= rows || column < 0 || column >= columns) {
                throw new IndexOutOfBoundsException("Matrix index out of range");
            }
            return values[row][column];
        }

        double[][] copyValues() {
            double[][] copy = new double[rows][columns];
            for (int row = 0; row < rows; row++) {
                copy[row] = values[row].clone();
            }
            return copy;
        }

        MatrixModel transpose() {
            double[][] result = new double[columns][rows];

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    result[column][row] = values[row][column];
                }
            }

            return new MatrixModel(role, result);
        }

        VectorModel multiply(VectorModel vector) {
            if (columns != vector.dimension()) {
                throw new IllegalArgumentException(
                        "Matrix columns must equal vector dimension"
                );
            }

            double[] result = new double[rows];
            double[] input = vector.values();

            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    result[row] += values[row][column] * input[column];
                }
            }

            return new VectorModel(
                    role + " result",
                    result
            );
        }

        MatrixModel multiply(MatrixModel other) {
            if (columns != other.rows()) {
                throw new IllegalArgumentException(
                        "Matrix dimensions are incompatible"
                );
            }

            double[][] result = new double[rows][other.columns()];

            for (int row = 0; row < rows; row++) {
                for (int middle = 0; middle < columns; middle++) {
                    double left = values[row][middle];

                    for (int column = 0; column < other.columns(); column++) {
                        result[row][column] +=
                                left * other.get(middle, column);
                    }
                }
            }

            return new MatrixModel(role, result);
        }

        void print() {
            System.out.println(role + " [" + rows + "x" + columns + "]");
            for (double[] row : values) {
                System.out.println("  " + Arrays.toString(row));
            }
        }
    }

    static final class LinearSystemService {

        private LinearSystemService() {
        }

        static VectorModel solve(MatrixModel source, VectorModel rhs) {
            if (source.rows() != source.columns()) {
                throw new IllegalArgumentException(
                        "A linear system requires a square coefficient matrix"
                );
            }

            if (rhs.dimension() != source.rows()) {
                throw new IllegalArgumentException(
                        "Right-hand side has the wrong dimension"
                );
            }

            int n = source.rows();
            double[][] matrix = source.copyValues();
            double[] target = rhs.values();

            for (int pivot = 0; pivot < n; pivot++) {
                int bestRow = pivot;

                for (int row = pivot + 1; row < n; row++) {
                    if (Math.abs(matrix[row][pivot]) >
                            Math.abs(matrix[bestRow][pivot])) {
                        bestRow = row;
                    }
                }

                if (Math.abs(matrix[bestRow][pivot]) < 1e-12) {
                    throw new IllegalArgumentException(
                            "System is singular or numerically unstable"
                    );
                }

                if (bestRow != pivot) {
                    double[] temporaryRow = matrix[pivot];
                    matrix[pivot] = matrix[bestRow];
                    matrix[bestRow] = temporaryRow;

                    double temporaryValue = target[pivot];
                    target[pivot] = target[bestRow];
                    target[bestRow] = temporaryValue;
                }

                for (int row = pivot + 1; row < n; row++) {
                    double factor =
                            matrix[row][pivot] / matrix[pivot][pivot];

                    matrix[row][pivot] = 0.0;

                    for (int column = pivot + 1; column < n; column++) {
                        matrix[row][column] -=
                                factor * matrix[pivot][column];
                    }

                    target[row] -= factor * target[pivot];
                }
            }

            double[] solution = new double[n];

            for (int row = n - 1; row >= 0; row--) {
                double value = target[row];

                for (int column = row + 1; column < n; column++) {
                    value -= matrix[row][column] * solution[column];
                }

                solution[row] = value / matrix[row][row];
            }

            return new VectorModel("System solution", solution);
        }
    }

    static final class VectorService {

        private VectorService() {
        }

        static double dot(VectorModel first, VectorModel second) {
            requireSameDimension(first, second);

            double result = 0.0;
            double[] a = first.values();
            double[] b = second.values();

            for (int i = 0; i < a.length; i++) {
                result += a[i] * b[i];
            }

            return result;
        }

        static double norm(VectorModel vector) {
            return Math.sqrt(dot(vector, vector));
        }

        static VectorModel normalize(VectorModel vector) {
            double length = norm(vector);

            if (length < 1e-12) {
                throw new IllegalArgumentException(
                        "The zero vector cannot be normalized"
                );
            }

            double[] values = vector.values();
            for (int i = 0; i < values.length; i++) {
                values[i] /= length;
            }

            return new VectorModel(
                    vector.name() + " normalized",
                    values
            );
        }

        static VectorModel scale(VectorModel vector, double scalar) {
            if (!Double.isFinite(scalar)) {
                throw new IllegalArgumentException("Scalar must be finite");
            }

            double[] values = vector.values();
            for (int i = 0; i < values.length; i++) {
                values[i] *= scalar;
            }

            return new VectorModel(
                    vector.name() + " scaled",
                    values
            );
        }

        private static void requireSameDimension(
                VectorModel first,
                VectorModel second
        ) {
            if (first.dimension() != second.dimension()) {
                throw new IllegalArgumentException(
                        "Vector dimensions must match"
                );
            }
        }
    }

    static final class CovarianceService {

        private CovarianceService() {
        }

        static MatrixModel covariance(double[][] observations) {
            if (observations == null || observations.length < 2) {
                throw new IllegalArgumentException(
                        "At least two observations are required"
                );
            }

            int features = observations[0].length;
            if (features == 0) {
                throw new IllegalArgumentException(
                        "Observations must contain features"
                );
            }

            for (double[] observation : observations) {
                if (observation == null || observation.length != features) {
                    throw new IllegalArgumentException(
                            "All observations must have equal dimensions"
                    );
                }
            }

            double[] mean = new double[features];

            for (double[] observation : observations) {
                for (int feature = 0; feature < features; feature++) {
                    mean[feature] += observation[feature];
                }
            }

            for (int feature = 0; feature < features; feature++) {
                mean[feature] /= observations.length;
            }

            double[][] result = new double[features][features];

            for (double[] observation : observations) {
                double[] centered = new double[features];

                for (int feature = 0; feature < features; feature++) {
                    centered[feature] =
                            observation[feature] - mean[feature];
                }

                for (int row = 0; row < features; row++) {
                    for (int column = 0; column < features; column++) {
                        result[row][column] +=
                                centered[row] * centered[column];
                    }
                }
            }

            double denominator = observations.length - 1.0;

            for (int row = 0; row < features; row++) {
                for (int column = 0; column < features; column++) {
                    result[row][column] /= denominator;
                }
            }

            return new MatrixModel(
                    MatrixRole.COVARIANCE,
                    result
            );
        }
    }

    static void printVector(VectorModel vector) {
        System.out.println(
                vector.name() + " " + Arrays.toString(vector.values())
        );
    }

    public static void main(String[] args) {
        System.out.println("=== Enterprise Analytics Linear Algebra Model ===");

        VectorModel customerMetrics = new VectorModel(
                "Customer metrics",
                new double[]{3.0, 4.0, 12.0}
        );

        VectorModel riskWeights = new VectorModel(
                "Risk weights",
                new double[]{0.5, 0.25, 0.75}
        );

        printVector(customerMetrics);
        printVector(riskWeights);

        double score = VectorService.dot(customerMetrics, riskWeights);
        System.out.println("Weighted score: " + score);
        System.out.println(
                "Metric norm: " + VectorService.norm(customerMetrics)
        );

        printVector(VectorService.normalize(customerMetrics));

        MatrixModel featureTransform = new MatrixModel(
                MatrixRole.FEATURE_TRANSFORM,
                new double[][]{
                        {1.0, 0.2, 0.0},
                        {0.0, 1.0, 0.5},
                        {0.1, 0.0, 1.0}
                }
        );

        featureTransform.print();

        VectorModel transformed =
                featureTransform.multiply(customerMetrics);

        printVector(transformed);

        MatrixModel system = new MatrixModel(
                MatrixRole.SYSTEM_MATRIX,
                new double[][]{
                        {3.0, 2.0, -1.0},
                        {2.0, -2.0, 4.0},
                        {-1.0, 0.5, -1.0}
                }
        );

        VectorModel target = new VectorModel(
                "Target",
                new double[]{1.0, -2.0, 0.0}
        );

        VectorModel solution =
                LinearSystemService.solve(system, target);

        printVector(solution);
        printVector(system.multiply(solution));

        MatrixModel transpose = featureTransform.transpose();
        transpose.print();

        MatrixModel gram =
                featureTransform.multiply(transpose);

        gram.print();

        double[][] observations = {
                {2.0, 1.0, 4.0},
                {3.0, 2.0, 5.0},
                {4.0, 3.0, 7.0},
                {5.0, 4.0, 8.0},
                {6.0, 5.0, 10.0}
        };

        MatrixModel covariance =
                CovarianceService.covariance(observations);

        covariance.print();

        System.out.println("=== Failure-state demonstrations ===");

        try {
            VectorService.normalize(
                    new VectorModel("Zero", new double[]{0.0, 0.0})
            );
        } catch (IllegalArgumentException error) {
            System.out.println("Zero-vector failure: " + error.getMessage());
        }

        try {
            LinearSystemService.solve(
                    new MatrixModel(
                            MatrixRole.SYSTEM_MATRIX,
                            new double[][]{
                                    {1.0, 2.0},
                                    {2.0, 4.0}
                            }
                    ),
                    new VectorModel("RHS", new double[]{3.0, 6.0})
            );
        } catch (IllegalArgumentException error) {
            System.out.println("Singular-system failure: " + error.getMessage());
        }

        try {
            featureTransform.multiply(
                    new VectorModel("Invalid", new double[]{1.0, 2.0})
            );
        } catch (IllegalArgumentException error) {
            System.out.println("Dimension failure: " + error.getMessage());
        }

        /*
         * The domain types separate vectors from matrices and assign matrices
         * a semantic role. This prevents a matrix representing covariance data
         * from being silently treated as a feature transform in higher-level
         * services. Defensive copies also prevent callers from mutating the
         * model after validation.
         *
         * The handwritten solver is educational. Production numerical systems
         * normally delegate large dense problems to optimized native numerical
         * libraries rather than implementing all decomposition algorithms in
         * application-level Java.
         */

        System.out.println("=== Enterprise model completed ===");
    }
}
