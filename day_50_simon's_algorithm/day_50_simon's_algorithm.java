import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Random;
import java.util.Set;

public final class SimonAlgorithm {

    record SimonProblem(int n, String secret) {
        SimonProblem {
            if (n <= 0) {
                throw new IllegalArgumentException("n must be positive");
            }
            if (secret == null || secret.length() != n
                    || !secret.matches("[01]+")
                    || secret.chars().allMatch(c -> c == '0')) {
                throw new IllegalArgumentException(
                        "secret must be a non-zero n-bit string");
            }
        }
    }

    enum ReviewState {
        UNOBSERVED,
        CONSTRAINED,
        DETERMINED
    }

    record Measurement(String bits) {
        Measurement {
            Objects.requireNonNull(bits);
            if (!bits.matches("[01]+")) {
                throw new IllegalArgumentException(
                        "measurement must be binary");
            }
        }
    }

    interface Oracle {
        int evaluate(int x);

        boolean satisfiesSimonPromise();
    }

    static final class PairOracle implements Oracle {
        private final int n;
        private final int secret;

        PairOracle(SimonProblem problem) {
            this.n = problem.n();
            this.secret = Integer.parseInt(problem.secret(), 2);
        }

        @Override
        public int evaluate(int x) {
            int domainSize = 1 << n;

            if (x < 0 || x >= domainSize) {
                throw new IllegalArgumentException(
                        "input is outside the oracle domain");
            }

            return Math.min(x, x ^ secret);
        }

        @Override
        public boolean satisfiesSimonPromise() {
            int domainSize = 1 << n;
            int[] frequency = new int[domainSize];

            for (int x = 0; x < domainSize; x++) {
                if (evaluate(x) != evaluate(x ^ secret)) {
                    return false;
                }
                frequency[evaluate(x)]++;
            }

            for (int count : frequency) {
                if (count != 0 && count != 2) {
                    return false;
                }
            }

            return true;
        }
    }

    static final class GF2Solver {

        private GF2Solver() {
        }

        static int rank(List<Measurement> measurements, int n) {
            List<int[]> matrix = toMatrix(measurements, n);
            return rank(matrix, n);
        }

        static int rank(List<int[]> matrix, int n) {
            if (matrix.isEmpty()) {
                return 0;
            }

            int[][] a = matrix.stream()
                    .map(int[]::clone)
                    .toArray(int[][]::new);

            int rank = 0;

            for (int column = 0; column < n; column++) {
                int pivot = -1;

                for (int row = rank; row < a.length; row++) {
                    if (a[row][column] == 1) {
                        pivot = row;
                        break;
                    }
                }

                if (pivot < 0) {
                    continue;
                }

                int[] temporary = a[rank];
                a[rank] = a[pivot];
                a[pivot] = temporary;

                for (int row = 0; row < a.length; row++) {
                    if (row != rank && a[row][column] == 1) {
                        xor(a[row], a[rank]);
                    }
                }

                rank++;

                if (rank == a.length) {
                    break;
                }
            }

            return rank;
        }

        static List<String> nullspace(
                List<Measurement> measurements,
                int n
        ) {
            int[][] matrix = toMatrix(measurements, n).toArray(int[][]::new);

            List<Integer> pivots = new ArrayList<>();
            int rank = 0;

            for (int column = 0; column < n; column++) {
                int pivot = -1;

                for (int row = rank; row < matrix.length; row++) {
                    if (matrix[row][column] == 1) {
                        pivot = row;
                        break;
                    }
                }

                if (pivot < 0) {
                    continue;
                }

                int[] temporary = matrix[rank];
                matrix[rank] = matrix[pivot];
                matrix[pivot] = temporary;

                for (int row = 0; row < matrix.length; row++) {
                    if (row != rank && matrix[row][column] == 1) {
                        xor(matrix[row], matrix[rank]);
                    }
                }

                pivots.add(column);
                rank++;
            }

            boolean[] isPivot = new boolean[n];
            for (int pivot : pivots) {
                isPivot[pivot] = true;
            }

            List<String> basis = new ArrayList<>();

            for (int free = 0; free < n; free++) {
                if (isPivot[free]) {
                    continue;
                }

                int[] vector = new int[n];
                vector[free] = 1;

                for (int row = 0; row < pivots.size(); row++) {
                    vector[pivots.get(row)] = matrix[row][free];
                }

                basis.add(toBits(vector));
            }

            return basis;
        }

        private static List<int[]> toMatrix(
                List<Measurement> measurements,
                int n
        ) {
            List<int[]> matrix = new ArrayList<>();

            for (Measurement measurement : measurements) {
                if (measurement.bits().length() != n) {
                    throw new IllegalArgumentException(
                            "measurement width does not match problem");
                }

                int[] row = new int[n];

                for (int i = 0; i < n; i++) {
                    row[i] = measurement.bits().charAt(i) - '0';
                }

                matrix.add(row);
            }

            return matrix;
        }

        private static void xor(int[] target, int[] source) {
            for (int i = 0; i < target.length; i++) {
                target[i] ^= source[i];
            }
        }

        private static String toBits(int[] vector) {
            StringBuilder builder = new StringBuilder(vector.length);

            for (int bit : vector) {
                builder.append(bit);
            }

            return builder.toString();
        }
    }

    static final class GovernanceService {
        private final SimonProblem problem;
        private final Oracle oracle;
        private final List<Measurement> measurements = new ArrayList<>();
        private ReviewState state = ReviewState.UNOBSERVED;

        GovernanceService(SimonProblem problem) {
            this.problem = problem;
            this.oracle = new PairOracle(problem);
        }

        void recordMeasurement(Measurement measurement) {
            if (measurement.bits().length() != problem.n()) {
                throw new IllegalArgumentException(
                        "measurement width must equal n");
            }

            measurements.add(measurement);

            int rank = GF2Solver.rank(measurements, problem.n());

            if (rank >= problem.n() - 1) {
                state = ReviewState.DETERMINED;
            } else {
                state = ReviewState.CONSTRAINED;
            }
        }

        String resolve() {
            if (state != ReviewState.DETERMINED) {
                throw new IllegalStateException(
                        "hidden period is not uniquely determined");
            }

            List<String> basis =
                    GF2Solver.nullspace(measurements, problem.n());

            if (basis.size() != 1) {
                throw new IllegalStateException(
                        "nullspace does not contain a unique secret");
            }

            return basis.getFirst();
        }

        ReviewState state() {
            return state;
        }

        Oracle oracle() {
            return oracle;
        }
    }

    static Measurement measure(
            String secret,
            Random random
    ) {
        int n = secret.length();
        int[] secretBits = secret.chars()
                .map(c -> c - '0')
                .toArray();

        while (true) {
            int[] vector = new int[n];

            for (int i = 0; i < n; i++) {
                vector[i] = random.nextBoolean() ? 1 : 0;
            }

            int dot = 0;

            for (int i = 0; i < n; i++) {
                dot ^= vector[i] & secretBits[i];
            }

            if (dot == 0) {
                StringBuilder builder = new StringBuilder(n);
                for (int bit : vector) {
                    builder.append(bit);
                }
                return new Measurement(builder.toString());
            }
        }
    }

    public static void main(String[] args) {
        SimonProblem problem = new SimonProblem(6, "101101");
        GovernanceService service = new GovernanceService(problem);

        if (!service.oracle().satisfiesSimonPromise()) {
            throw new IllegalStateException(
                    "oracle does not satisfy Simon's promise");
        }

        Random random = new Random(17);
        Set<String> uniqueMeasurements = new HashSet<>();

        while (service.state() != ReviewState.DETERMINED) {
            Measurement measurement = measure(
                    problem.secret(),
                    random
            );

            /*
             * Duplicate equations provide no new information, so the
             * enterprise service records only rank-increasing evidence.
             */
            if (uniqueMeasurements.add(measurement.bits())) {
                int oldRank = GF2Solver.rank(
                        service.measurements,
                        problem.n()
                );

                List<Measurement> candidate =
                        new ArrayList<>(service.measurements);
                candidate.add(measurement);

                int newRank = GF2Solver.rank(candidate, problem.n());

                if (newRank > oldRank) {
                    service.recordMeasurement(measurement);
                }
            }
        }

        String recovered = service.resolve();

        System.out.println("Simon hidden-period enterprise model");
        System.out.println("Problem width:       " + problem.n());
        System.out.println("Hidden period:       " + problem.secret());
        System.out.println("Review state:        " + service.state());
        System.out.println(
                "Independent equations: "
                        + GF2Solver.rank(
                                service.measurements,
                                problem.n()
                        )
        );
        System.out.println("Recovered period:    " + recovered);
        System.out.println(
                "Recovery successful: "
                        + recovered.equals(problem.secret())
        );

        /*
         * The model deliberately separates:
         * - domain validation,
         * - oracle behavior,
         * - measurement evidence,
         * - GF(2) linear algebra,
         * - state transitions,
         * - final resolution.
         *
         * This prevents the quantum promise from being hidden inside
         * the solver and makes failure states explicit.
         */
    }
}
