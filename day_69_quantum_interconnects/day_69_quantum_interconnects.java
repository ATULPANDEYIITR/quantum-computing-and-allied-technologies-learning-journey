import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * QuantumInterconnectEnterprise.java
 *
 * Enterprise-oriented quantum interconnect management system.
 *
 * Models:
 * - Quantum processing facilities
 * - Interconnect channels
 * - Entanglement generation
 * - Quantum memory coherence
 * - Fidelity-aware routing
 * - Entanglement swapping
 * - Resource reservations
 * - Network service policies
 * - Operational events
 * - Failure handling
 * - Performance reporting
 *
 * Fidelity uses a simplified Werner-state approximation.
 */

public class QuantumInterconnectEnterprise {

    enum ProcessorStatus {
        ONLINE,
        OFFLINE,
        MAINTENANCE
    }

    enum LinkStatus {
        IDLE,
        ENTANGLED,
        DEGRADED,
        DOWN
    }

    enum OperationStatus {
        ACCEPTED,
        REJECTED,
        COMPLETED,
        FAILED
    }

    record ProcessorConfiguration(
        String id,
        String name,
        int qubitCapacity,
        double coherenceTimeMs
    ) {
        ProcessorConfiguration {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);

            if (id.isBlank() || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Processor identity cannot be blank"
                );
            }

            if (qubitCapacity <= 0 || coherenceTimeMs <= 0) {
                throw new IllegalArgumentException(
                    "Invalid processor configuration"
                );
            }
        }
    }

    record LinkConfiguration(
        String id,
        String source,
        String destination,
        double distanceKm,
        double generationProbability,
        double fidelity
    ) {
        LinkConfiguration {
            Objects.requireNonNull(id);
            Objects.requireNonNull(source);
            Objects.requireNonNull(destination);

            if (id.isBlank() || source.equals(destination)) {
                throw new IllegalArgumentException(
                    "Invalid link endpoints"
                );
            }

            if (distanceKm <= 0 ||
                generationProbability < 0 ||
                generationProbability > 1 ||
                fidelity < 0.25 ||
                fidelity > 1) {
                throw new IllegalArgumentException(
                    "Invalid link parameters"
                );
            }
        }
    }

    record Route(
        List<String> processors,
        List<String> links,
        double fidelity,
        double latencyMs
    ) {
        Route {
            processors = List.copyOf(processors);
            links = List.copyOf(links);
        }
    }

    record NetworkEvent(
        long sequence,
        long timestampMs,
        String eventType,
        String description
    ) {}

    record NetworkPolicy(
        double minimumFidelity,
        double maximumDistanceKm,
        boolean requireOnlineProcessors
    ) {
        NetworkPolicy {
            if (minimumFidelity < 0.25 ||
                minimumFidelity > 1 ||
                maximumDistanceKm <= 0) {
                throw new IllegalArgumentException(
                    "Invalid network policy"
                );
            }
        }
    }

    static class NetworkException extends RuntimeException {
        NetworkException(String message) {
            super(message);
        }
    }

    static class QuantumProcessor {

        private final ProcessorConfiguration configuration;

        private int availableQubits;
        private ProcessorStatus status = ProcessorStatus.ONLINE;

        QuantumProcessor(ProcessorConfiguration configuration) {
            this.configuration = configuration;
            this.availableQubits = configuration.qubitCapacity();
        }

        String id() {
            return configuration.id();
        }

        double coherenceTime() {
            return configuration.coherenceTimeMs();
        }

        ProcessorStatus status() {
            return status;
        }

        void setStatus(ProcessorStatus status) {
            this.status = Objects.requireNonNull(status);
        }

        synchronized boolean reserve(int count) {
            if (count <= 0 ||
                status != ProcessorStatus.ONLINE ||
                availableQubits < count) {
                return false;
            }

            availableQubits -= count;
            return true;
        }

        synchronized void release(int count) {
            if (count <= 0 ||
                availableQubits + count >
                    configuration.qubitCapacity()) {
                throw new NetworkException(
                    "Invalid qubit resource release"
                );
            }

            availableQubits += count;
        }

        synchronized int availableQubits() {
            return availableQubits;
        }
    }

    static class QuantumLink {

        private final LinkConfiguration configuration;

        private LinkStatus status = LinkStatus.IDLE;
        private double currentFidelity;
        private long attempts;
        private long failures;

        QuantumLink(LinkConfiguration configuration) {
            this.configuration = configuration;
        }

        String id() {
            return configuration.id();
        }

        String source() {
            return configuration.source();
        }

        String destination() {
            return configuration.destination();
        }

        double distanceKm() {
            return configuration.distanceKm();
        }

        double fidelity() {
            return currentFidelity;
        }

        LinkStatus status() {
            return status;
        }

        synchronized boolean generate() {
            attempts++;

            if (status == LinkStatus.DOWN) {
                failures++;
                return false;
            }

            // The deterministic demonstration uses probability thresholds.
            if (configuration.generationProbability() < 1.0) {
                failures++;
                status = LinkStatus.IDLE;
                return false;
            }

            currentFidelity = configuration.fidelity();
            status = LinkStatus.ENTANGLED;

            return true;
        }

        synchronized void consume() {
            currentFidelity = 0;
            status = LinkStatus.IDLE;
        }

        synchronized void decay(double elapsedMs, double coherenceMs) {
            if (elapsedMs < 0 || coherenceMs <= 0) {
                throw new IllegalArgumentException(
                    "Invalid decoherence parameters"
                );
            }

            if (status != LinkStatus.ENTANGLED &&
                status != LinkStatus.DEGRADED) {
                return;
            }

            currentFidelity =
                0.25 +
                (currentFidelity - 0.25) *
                Math.exp(-elapsedMs / coherenceMs);

            if (currentFidelity < 0.5) {
                status = LinkStatus.DEGRADED;
            }
        }
    }

    static class NetworkMetrics {

        private final AtomicLong generationAttempts =
            new AtomicLong();

        private final AtomicLong successfulGenerations =
            new AtomicLong();

        private final AtomicLong failedGenerations =
            new AtomicLong();

        private final AtomicLong swaps =
            new AtomicLong();

        private final AtomicLong acceptedRoutes =
            new AtomicLong();

        private final AtomicLong rejectedRoutes =
            new AtomicLong();

        Map<String, Long> snapshot() {
            Map<String, Long> result = new LinkedHashMap<>();

            result.put("generationAttempts",
                generationAttempts.get());

            result.put("successfulGenerations",
                successfulGenerations.get());

            result.put("failedGenerations",
                failedGenerations.get());

            result.put("swaps", swaps.get());

            result.put("acceptedRoutes",
                acceptedRoutes.get());

            result.put("rejectedRoutes",
                rejectedRoutes.get());

            return Collections.unmodifiableMap(result);
        }
    }

    static class QuantumInterconnectService {

        private final Map<String, QuantumProcessor> processors =
            new ConcurrentHashMap<>();

        private final Map<String, QuantumLink> links =
            new ConcurrentHashMap<>();

        private final Map<String, List<String>> adjacency =
            new ConcurrentHashMap<>();

        private final Queue<NetworkEvent> events =
            new ConcurrentLinkedQueue<>();

        private final AtomicLong eventSequence =
            new AtomicLong();

        private final NetworkMetrics metrics =
            new NetworkMetrics();

        private final NetworkPolicy policy;

        private volatile long currentTimeMs;

        QuantumInterconnectService(NetworkPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void addProcessor(QuantumProcessor processor) {
            if (processors.putIfAbsent(
                processor.id(),
                processor
            ) != null) {
                throw new NetworkException(
                    "Duplicate processor"
                );
            }

            adjacency.put(processor.id(),
                new CopyOnWriteArrayList<>());
        }

        void addLink(QuantumLink link) {
            if (!processors.containsKey(link.source()) ||
                !processors.containsKey(link.destination())) {
                throw new NetworkException(
                    "Unknown link endpoint"
                );
            }

            if (links.putIfAbsent(link.id(), link) != null) {
                throw new NetworkException(
                    "Duplicate link"
                );
            }

            adjacency.get(link.source()).add(link.id());
            adjacency.get(link.destination()).add(link.id());
        }

        void recordEvent(String type, String description) {
            events.add(new NetworkEvent(
                eventSequence.incrementAndGet(),
                currentTimeMs,
                type,
                description
            ));
        }

        CompletableFuture<Boolean> generateEntanglement(
            String linkId,
            Executor executor
        ) {
            QuantumLink link = links.get(linkId);

            if (link == null) {
                throw new NetworkException("Unknown quantum link");
            }

            return CompletableFuture.supplyAsync(() -> {
                metrics.generationAttempts.incrementAndGet();

                boolean success = link.generate();

                if (success) {
                    metrics.successfulGenerations.incrementAndGet();

                    recordEvent(
                        "ENTANGLEMENT_CREATED",
                        linkId
                    );
                } else {
                    metrics.failedGenerations.incrementAndGet();

                    recordEvent(
                        "ENTANGLEMENT_FAILED",
                        linkId
                    );
                }

                return success;
            }, executor);
        }

        List<Boolean> generateAll() {
            ExecutorService executor =
                Executors.newFixedThreadPool(4);

            try {
                List<CompletableFuture<Boolean>> tasks =
                    links.keySet()
                        .stream()
                        .map(id ->
                            generateEntanglement(id, executor)
                        )
                        .toList();

                return tasks.stream()
                    .map(CompletableFuture::join)
                    .toList();

            } finally {
                executor.shutdown();
            }
        }

        static double calculateSwappedFidelity(
            double first,
            double second
        ) {
            if (first < 0.25 || first > 1 ||
                second < 0.25 || second > 1) {
                throw new IllegalArgumentException(
                    "Invalid fidelity"
                );
            }

            return first * second +
                ((1 - first) * (1 - second)) / 3.0;
        }

        double performSwap(String firstId, String secondId) {
            QuantumLink first = links.get(firstId);
            QuantumLink second = links.get(secondId);

            if (first == null || second == null) {
                throw new NetworkException(
                    "Unknown quantum link"
                );
            }

            Set<String> shared = new HashSet<>(
                Arrays.asList(
                    first.source(),
                    first.destination()
                )
            );

            shared.retainAll(Arrays.asList(
                second.source(),
                second.destination()
            ));

            if (shared.size() != 1) {
                throw new NetworkException(
                    "Links must share exactly one processor"
                );
            }

            QuantumProcessor intermediate =
                processors.get(shared.iterator().next());

            synchronized (intermediate) {
                synchronized (first) {
                    synchronized (second) {
                        if (first.status() != LinkStatus.ENTANGLED ||
                            second.status() != LinkStatus.ENTANGLED) {
                            throw new NetworkException(
                                "Entangled links required"
                            );
                        }

                        if (!intermediate.reserve(1)) {
                            throw new NetworkException(
                                "Insufficient qubit resources"
                            );
                        }

                        try {
                            double result =
                                calculateSwappedFidelity(
                                    first.fidelity(),
                                    second.fidelity()
                                );

                            first.consume();
                            second.consume();

                            metrics.swaps.incrementAndGet();

                            recordEvent(
                                "ENTANGLEMENT_SWAPPED",
                                firstId + " + " + secondId
                            );

                            return result;

                        } finally {
                            intermediate.release(1);
                        }
                    }
                }
            }
        }

        Route findRoute(
            String source,
            String destination
        ) {
            if (!processors.containsKey(source) ||
                !processors.containsKey(destination)) {
                throw new NetworkException(
                    "Unknown processor"
                );
            }

            if (source.equals(destination)) {
                return new Route(
                    List.of(source),
                    List.of(),
                    1,
                    0
                );
            }

            record State(
                String node,
                double cost,
                double latency,
                List<String> nodes,
                List<String> links
            ) {}

            PriorityQueue<State> queue =
                new PriorityQueue<>(
                    Comparator.comparingDouble(State::cost)
                );

            Map<String, Double> best = new HashMap<>();

            queue.add(new State(
                source,
                0,
                0,
                List.of(source),
                List.of()
            ));

            best.put(source, 0.0);

            while (!queue.isEmpty()) {
                State current = queue.poll();

                if (current.cost() > best.getOrDefault(
                    current.node(),
                    Double.POSITIVE_INFINITY
                )) {
                    continue;
                }

                if (current.node().equals(destination)) {
                    return new Route(
                        current.nodes(),
                        current.links(),
                        Math.exp(-current.cost()),
                        current.latency()
                    );
                }

                for (String linkId :
                    adjacency.get(current.node())) {

                    QuantumLink link = links.get(linkId);

                    if (link.status() != LinkStatus.ENTANGLED ||
                        link.fidelity() <
                            policy.minimumFidelity() ||
                        link.distanceKm() >
                            policy.maximumDistanceKm()) {
                        continue;
                    }

                    String neighbor =
                        link.source().equals(current.node())
                            ? link.destination()
                            : link.source();

                    QuantumProcessor processor =
                        processors.get(neighbor);

                    if (policy.requireOnlineProcessors() &&
                        processor.status() != ProcessorStatus.ONLINE) {
                        continue;
                    }

                    double cost =
                        current.cost() - Math.log(link.fidelity());

                    if (cost >= best.getOrDefault(
                        neighbor,
                        Double.POSITIVE_INFINITY
                    )) {
                        continue;
                    }

                    best.put(neighbor, cost);

                    List<String> nextNodes =
                        new ArrayList<>(current.nodes());

                    nextNodes.add(neighbor);

                    List<String> nextLinks =
                        new ArrayList<>(current.links());

                    nextLinks.add(linkId);

                    queue.add(new State(
                        neighbor,
                        cost,
                        current.latency() +
                            link.distanceKm() / 200.0,
                        List.copyOf(nextNodes),
                        List.copyOf(nextLinks)
                    ));
                }
            }

            throw new NetworkException(
                "No route satisfies network policy"
            );
        }

        Route requestRoute(
            String source,
            String destination
        ) {
            try {
                Route route = findRoute(source, destination);

                metrics.acceptedRoutes.incrementAndGet();

                recordEvent(
                    "ROUTE_ACCEPTED",
                    source + " -> " + destination
                );

                return route;

            } catch (NetworkException exception) {
                metrics.rejectedRoutes.incrementAndGet();

                recordEvent(
                    "ROUTE_REJECTED",
                    exception.getMessage()
                );

                throw exception;
            }
        }

        void advanceTime(long elapsedMs) {
            if (elapsedMs < 0) {
                throw new IllegalArgumentException(
                    "Time cannot move backwards"
                );
            }

            for (QuantumLink link : links.values()) {
                QuantumProcessor first =
                    processors.get(link.source());

                QuantumProcessor second =
                    processors.get(link.destination());

                link.decay(
                    elapsedMs,
                    Math.min(
                        first.coherenceTime(),
                        second.coherenceTime()
                    )
                );
            }

            currentTimeMs += elapsedMs;

            recordEvent(
                "CLOCK_ADVANCED",
                elapsedMs + " ms"
            );
        }

        void printReport() {
            System.out.println("\nPROCESSOR INVENTORY");

            processors.values().stream()
                .sorted(Comparator.comparing(QuantumProcessor::id))
                .forEach(p ->
                    System.out.printf(
                        "%s | %s | Available qubits: %d%n",
                        p.id(),
                        p.status(),
                        p.availableQubits()
                    )
                );

            System.out.println("\nLINK INVENTORY");

            links.values().stream()
                .sorted(Comparator.comparing(QuantumLink::id))
                .forEach(link ->
                    System.out.printf(
                        "%s | %s -> %s | %s | Fidelity %.5f%n",
                        link.id(),
                        link.source(),
                        link.destination(),
                        link.status(),
                        link.fidelity()
                    )
                );

            System.out.println("\nMETRICS");

            metrics.snapshot().forEach(
                (key, value) ->
                    System.out.println(key + ": " + value)
            );

            System.out.println("\nRECENT EVENTS");

            events.stream()
                .skip(Math.max(0, events.size() - 10))
                .forEach(System.out::println);
        }
    }

    private static QuantumInterconnectService buildNetwork() {
        NetworkPolicy policy = new NetworkPolicy(
            0.5,
            100,
            true
        );

        QuantumInterconnectService service =
            new QuantumInterconnectService(policy);

        List<QuantumProcessor> processors = List.of(
            new QuantumProcessor(
                new ProcessorConfiguration(
                    "Q1", "North Quantum Center", 16, 100
                )
            ),
            new QuantumProcessor(
                new ProcessorConfiguration(
                    "Q2", "Central Quantum Center", 12, 80
                )
            ),
            new QuantumProcessor(
                new ProcessorConfiguration(
                    "Q3", "South Quantum Center", 16, 120
                )
            ),
            new QuantumProcessor(
                new ProcessorConfiguration(
                    "Q4", "Remote Quantum Center", 8, 60
                )
            )
        );

        processors.forEach(service::addProcessor);

        List<QuantumLink> links = List.of(
            new QuantumLink(
                new LinkConfiguration(
                    "L12", "Q1", "Q2", 20, 1, 0.98
                )
            ),
            new QuantumLink(
                new LinkConfiguration(
                    "L23", "Q2", "Q3", 30, 1, 0.97
                )
            ),
            new QuantumLink(
                new LinkConfiguration(
                    "L13", "Q1", "Q3", 65, 1, 0.91
                )
            ),
            new QuantumLink(
                new LinkConfiguration(
                    "L34", "Q3", "Q4", 15, 1, 0.96
                )
            ),
            new QuantumLink(
                new LinkConfiguration(
                    "L24", "Q2", "Q4", 45, 0, 0.94
                )
            )
        );

        links.forEach(service::addLink);

        return service;
    }

    public static void main(String[] args) {
        QuantumInterconnectService network = buildNetwork();

        System.out.println(
            "QUANTUM INTERCONNECT ENTERPRISE MANAGEMENT"
        );

        System.out.println(
            "==========================================="
        );

        try {
            network.generateAll();

            Route route = network.requestRoute("Q1", "Q4");

            System.out.println("\nSELECTED ROUTE");

            System.out.println(
                String.join(" -> ", route.processors())
            );

            System.out.println("Links: " + route.links());

            System.out.printf(
                "Fidelity: %.6f%n",
                route.fidelity()
            );

            System.out.printf(
                "Latency: %.4f ms%n",
                route.latencyMs()
            );

            double swapped =
                network.performSwap("L12", "L23");

            System.out.printf(
                "\nSwapped fidelity: %.6f%n",
                swapped
            );

            network.advanceTime(15);

            network.printReport();

            if (QuantumInterconnectService
                .calculateSwappedFidelity(1, 1) != 1) {
                throw new AssertionError(
                    "Perfect fidelity assertion failed"
                );
            }

            System.out.println(
                "\nEnterprise network simulation completed."
            );

        } catch (RuntimeException exception) {
            System.err.println(
                "Network operation failed: " +
                exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
