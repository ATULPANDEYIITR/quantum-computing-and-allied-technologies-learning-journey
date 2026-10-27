import java.math.BigInteger;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Shor's algorithm: enterprise-oriented integer factorization model.
 *
 * The program separates:
 * - input validation,
 * - classical preprocessing,
 * - base selection,
 * - order discovery,
 * - period validation,
 * - factor extraction,
 * - workflow state transitions.
 *
 * A production quantum implementation would replace the classical
 * order-discovery service with a quantum phase-estimation/QFT circuit.
 */
public final class ShorsAlgorithm {

    private ShorsAlgorithm() {
    }

    enum FactorizationState {
        RECEIVED,
        PREPROCESSED,
        ORDER_SEARCH,
        PERIOD_FOUND,
        FACTORS_RECOVERED,
        RETRY_REQUIRED,
        PRIME
    }

    record FactorizationRequest(BigInteger n, int maxAttempts) {
        FactorizationRequest {
            Objects.requireNonNull(n, "n cannot be null");

            if (n.compareTo(BigInteger.TWO) < 0) {
                throw new IllegalArgumentException("n must be >= 2");
            }

            if (maxAttempts < 1) {
                throw new IllegalArgumentException(
                    "maxAttempts must be positive"
                );
            }
        }
    }

    record FactorizationResult(
        BigInteger n,
        List<BigInteger> factors,
        BigInteger base,
        BigInteger period,
        FactorizationState state,
        String message
    ) {
        FactorizationResult {
            Objects.requireNonNull(n);
            Objects.requireNonNull(factors);
            Objects.requireNonNull(state);
            Objects.requireNonNull(message);

            factors = List.copyOf(factors);
        }
    }

    interface OrderFindingService {
        Optional<BigInteger> findOrder(
            BigInteger base,
            BigInteger modulus
        );
    }

    /**
     * Classical order finder used to model the mathematical output
     * that Shor's quantum period-finding circuit would produce.
     */
    static final class ClassicalOrderFindingService
        implements OrderFindingService {

        @Override
        public Optional<BigInteger> findOrder(
            BigInteger base,
            BigInteger modulus
        ) {
            if (!base.gcd(modulus).equals(BigInteger.ONE)) {
                return Optional.empty();
            }

            BigInteger value = BigInteger.ONE;

            for (BigInteger r = BigInteger.ONE;
                 r.compareTo(modulus) <= 0;
                 r = r.add(BigInteger.ONE)) {

                value = value.multiply(base).mod(modulus);

                if (value.equals(BigInteger.ONE)) {
                    return Optional.of(r);
                }
            }

            return Optional.empty();
        }
    }

    /**
     * Demonstrates the factorization workflow as a state machine.
     */
    static final class FactorizationService {
        private final SecureRandom random;
        private final OrderFindingService orderFinder;

        FactorizationService(
            SecureRandom random,
            OrderFindingService orderFinder
        ) {
            this.random = Objects.requireNonNull(random);
            this.orderFinder = Objects.requireNonNull(orderFinder);
        }

        FactorizationResult factor(FactorizationRequest request) {
            BigInteger n = request.n();

            if (isPrime(n)) {
                return new FactorizationResult(
                    n,
                    List.of(n),
                    null,
                    null,
                    FactorizationState.PRIME,
                    "Input is prime."
                );
            }

            if (n.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
                return new FactorizationResult(
                    n,
                    List.of(BigInteger.TWO, n.divide(BigInteger.TWO)),
                    null,
                    null,
                    FactorizationState.PREPROCESSED,
                    "Even-number preprocessing found a factor."
                );
            }

            FactorizationState state = FactorizationState.RECEIVED;

            for (int attempt = 0;
                 attempt < request.maxAttempts();
                 attempt++) {

                state = FactorizationState.PREPROCESSED;

                BigInteger base = randomBase(n);
                BigInteger commonFactor = base.gcd(n);

                if (commonFactor.compareTo(BigInteger.ONE) > 0
                    && commonFactor.compareTo(n) < 0) {

                    List<BigInteger> factors =
                        sortedFactors(commonFactor, n.divide(commonFactor));

                    return new FactorizationResult(
                        n,
                        factors,
                        base,
                        null,
                        FactorizationState.FACTORS_RECOVERED,
                        "Random base exposed a non-trivial gcd."
                    );
                }

                if (!commonFactor.equals(BigInteger.ONE)) {
                    continue;
                }

                state = FactorizationState.ORDER_SEARCH;

                Optional<BigInteger> order =
                    orderFinder.findOrder(base, n);

                if (order.isEmpty()) {
                    state = FactorizationState.RETRY_REQUIRED;
                    continue;
                }

                BigInteger period = order.get();

                if (!period.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
                    state = FactorizationState.RETRY_REQUIRED;
                    continue;
                }

                if (!base.modPow(period, n).equals(BigInteger.ONE)) {
                    state = FactorizationState.RETRY_REQUIRED;
                    continue;
                }

                state = FactorizationState.PERIOD_FOUND;

                Optional<List<BigInteger>> factors =
                    extractFactors(n, base, period);

                if (factors.isPresent()) {
                    return new FactorizationResult(
                        n,
                        factors.get(),
                        base,
                        period,
                        FactorizationState.FACTORS_RECOVERED,
                        "Factors recovered from the even multiplicative order."
                    );
                }

                state = FactorizationState.RETRY_REQUIRED;
            }

            return new FactorizationResult(
                n,
                List.of(),
                null,
                null,
                state,
                "No usable period was found within the attempt limit."
            );
        }

        private BigInteger randomBase(BigInteger n) {
            BigInteger upper = n.subtract(BigInteger.TWO);

            while (true) {
                BigInteger candidate = new BigInteger(
                    n.bitLength(),
                    random
                );

                if (candidate.compareTo(BigInteger.TWO) >= 0
                    && candidate.compareTo(upper) <= 0) {
                    return candidate;
                }
            }
        }
    }

    static boolean isPrime(BigInteger n) {
        return n.isProbablePrime(50);
    }

    static List<BigInteger> sortedFactors(
        BigInteger left,
        BigInteger right
    ) {
        if (left.compareTo(right) <= 0) {
            return List.of(left, right);
        }

        return List.of(right, left);
    }

    static Optional<List<BigInteger>> extractFactors(
        BigInteger n,
        BigInteger base,
        BigInteger period
    ) {
        if (period.signum() <= 0
            || !period.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
            return Optional.empty();
        }

        BigInteger halfPower =
            base.modPow(period.divide(BigInteger.TWO), n);

        if (halfPower.equals(n.subtract(BigInteger.ONE))) {
            return Optional.empty();
        }

        BigInteger left =
            halfPower.subtract(BigInteger.ONE).gcd(n);

        BigInteger right =
            halfPower.add(BigInteger.ONE).gcd(n);

        if (left.compareTo(BigInteger.ONE) > 0
            && left.compareTo(n) < 0
            && right.compareTo(BigInteger.ONE) > 0
            && right.compareTo(n) < 0
            && left.multiply(right).equals(n)) {

            return Optional.of(sortedFactors(left, right));
        }

        return Optional.empty();
    }

    static List<BigInteger> trialFactorization(BigInteger input) {
        List<BigInteger> factors = new ArrayList<>();
        BigInteger n = input;

        while (n.mod(BigInteger.TWO).equals(BigInteger.ZERO)) {
            factors.add(BigInteger.TWO);
            n = n.divide(BigInteger.TWO);
        }

        BigInteger divisor = BigInteger.valueOf(3);

        while (divisor.multiply(divisor).compareTo(n) <= 0) {
            while (n.mod(divisor).equals(BigInteger.ZERO)) {
                factors.add(divisor);
                n = n.divide(divisor);
            }

            divisor = divisor.add(BigInteger.TWO);
        }

        if (n.compareTo(BigInteger.ONE) > 0) {
            factors.add(n);
        }

        return List.copyOf(factors);
    }

    static void demonstrateOrder(
        OrderFindingService service,
        BigInteger n,
        BigInteger base
    ) {
        Optional<BigInteger> order =
            service.findOrder(base, n);

        System.out.println("base=" + base + ", n=" + n);

        if (order.isEmpty()) {
            System.out.println("  no multiplicative order");
            return;
        }

        BigInteger r = order.get();
        List<BigInteger> sequence = new ArrayList<>();

        for (BigInteger exponent = BigInteger.ZERO;
             exponent.compareTo(r) < 0;
             exponent = exponent.add(BigInteger.ONE)) {

            sequence.add(base.modPow(exponent, n));
        }

        System.out.println("  periodic sequence: " + sequence);
        System.out.println("  order r: " + r);
        System.out.println("  base^r mod n: " + base.modPow(r, n));

        Optional<List<BigInteger>> factors =
            extractFactors(n, base, r);

        System.out.println(
            "  factor extraction: " +
            factors.map(Object::toString).orElse("retry")
        );
    }

    static void validate() {
        if (!BigInteger.valueOf(84)
            .gcd(BigInteger.valueOf(30))
            .equals(BigInteger.valueOf(6))) {
            throw new AssertionError("GCD validation failed.");
        }

        if (!BigInteger.valueOf(7)
            .modPow(BigInteger.valueOf(4), BigInteger.valueOf(15))
            .equals(BigInteger.ONE)) {
            throw new AssertionError("Modular power validation failed.");
        }

        ClassicalOrderFindingService service =
            new ClassicalOrderFindingService();

        Optional<BigInteger> order =
            service.findOrder(
                BigInteger.TWO,
                BigInteger.valueOf(15)
            );

        if (order.isEmpty() || !order.get().equals(BigInteger.valueOf(4))) {
            throw new AssertionError("Order validation failed.");
        }

        Optional<List<BigInteger>> factors =
            extractFactors(
                BigInteger.valueOf(15),
                BigInteger.TWO,
                BigInteger.valueOf(4)
            );

        if (factors.isEmpty()
            || !factors.get().equals(
                List.of(BigInteger.valueOf(3), BigInteger.valueOf(5))
            )) {
            throw new AssertionError("Factor extraction validation failed.");
        }
    }

    public static void main(String[] args) {
        SecureRandom random = new SecureRandom();

        OrderFindingService orderService =
            new ClassicalOrderFindingService();

        FactorizationService service =
            new FactorizationService(random, orderService);

        System.out.println(
            "Shor's Algorithm: Enterprise Integer-Factorization Model"
        );
        System.out.println(
            "=========================================================="
        );

        for (int n : new int[]{15, 21, 35, 77}) {
            FactorizationRequest request =
                new FactorizationRequest(
                    BigInteger.valueOf(n),
                    40
                );

            FactorizationResult result = service.factor(request);

            System.out.println(
                "n=" + result.n()
                + ", state=" + result.state()
                + ", factors=" + result.factors()
                + ", base=" + result.base()
                + ", period=" + result.period()
            );

            System.out.println("  " + result.message());
        }

        System.out.println("\nOrder-finding examples");
        System.out.println("----------------------");

        demonstrateOrder(
            orderService,
            BigInteger.valueOf(15),
            BigInteger.valueOf(2)
        );

        demonstrateOrder(
            orderService,
            BigInteger.valueOf(21),
            BigInteger.valueOf(2)
        );

        System.out.println("\nReference factorizations");
        System.out.println("------------------------");

        for (int n : new int[]{15, 21, 35, 77, 84}) {
            BigInteger value = BigInteger.valueOf(n);
            System.out.println(
                n + " = " + trialFactorization(value)
            );
        }

        validate();
        System.out.println("\nValidation checks passed.");
    }
}
