import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;

/*
 * Enterprise-style neutral-atom facility model.
 *
 * The service separates immutable experimental configuration, safety rules,
 * audit records, loading observations, and rearrangement execution.
 *
 * It models laboratory workflow and planning. It is not a hardware driver
 * or a quantum-state simulator.
 *
 * Compile: javac NeutralAtomFacility.java
 * Run:     java NeutralAtomFacility
 */

public class NeutralAtomFacility {

    private static final double BOLTZMANN_CONSTANT = 1.380649e-23;
    private static final double RUBIDIUM_87_MASS_KG = 1.44316060e-25;
    private static final double PI = Math.PI;

    enum RunState {
        DRAFT,
        VALIDATED,
        LOADED,
        REARRANGED,
        READY,
        FAILED
    }

    record Vec2(double xUm, double yUm) {
        Vec2 {
            if (!Double.isFinite(xUm) || !Double.isFinite(yUm)) {
                throw new IllegalArgumentException("Coordinates must be finite.");
            }
        }

        double distanceTo(Vec2 other) {
            return Math.hypot(xUm - other.xUm, yUm - other.yUm);
        }
    }

    record Site(String id, int row, int column, Vec2 position) {
        Site {
            Objects.requireNonNull(id, "Site ID");
            Objects.requireNonNull(position, "Site position");

            if (id.isBlank() || row < 0 || column < 0) {
                throw new IllegalArgumentException("Invalid tweezer site.");
            }
        }
    }

    record TrapCalibration(
        String calibrationId,
        double wavelengthM,
        double waistM,
        double trapDepthJ,
        double atomicMassKg,
        double beamPowerW,
        Instant validUntil
    ) {
        TrapCalibration {
            Objects.requireNonNull(calibrationId, "Calibration ID");
            Objects.requireNonNull(validUntil, "Calibration expiry");

            if (calibrationId.isBlank()) {
                throw new IllegalArgumentException("Calibration ID is required.");
            }

            requirePositive(wavelengthM, "Wavelength");
            requirePositive(waistM, "Beam waist");
            requirePositive(trapDepthJ, "Trap depth");
            requirePositive(atomicMassKg, "Atomic mass");
            requirePositive(beamPowerW, "Beam power");
        }

        double rayleighRangeM() {
            return PI * waistM * waistM / wavelengthM;
        }

        double radialFrequencyHz() {
            double angularFrequency = Math.sqrt(
                4.0 * trapDepthJ / (atomicMassKg * waistM * waistM)
            );
            return angularFrequency / (2.0 * PI);
        }

        double axialFrequencyHz() {
            double rayleighRange = rayleighRangeM();
            double angularFrequency = Math.sqrt(
                2.0 * trapDepthJ /
                (atomicMassKg * rayleighRange * rayleighRange)
            );
            return angularFrequency / (2.0 * PI);
        }
    }

    record TweezerArray(
        String arrayId,
        int rows,
        int columns,
        double spacingUm,
        List<Site> sites
    ) {
        TweezerArray {
            Objects.requireNonNull(arrayId, "Array ID");
            Objects.requireNonNull(sites, "Sites");

            if (arrayId.isBlank() || rows <= 0 || columns <= 0) {
                throw new IllegalArgumentException("Invalid array dimensions or ID.");
            }
            requirePositive(spacingUm, "Tweezer spacing");

            sites = List.copyOf(sites);
            if (sites.size() != rows * columns) {
                throw new IllegalArgumentException(
                    "A rectangular array must contain rows multiplied by columns sites."
                );
            }

            Set<String> identifiers = new HashSet<>();
            for (Site site : sites) {
                if (!identifiers.add(site.id())) {
                    throw new IllegalArgumentException("Duplicate site ID: " + site.id());
                }
                if (site.row() >= rows || site.column() >= columns) {
                    throw new IllegalArgumentException("Site index is outside the array.");
                }

                double expectedX = site.column() * spacingUm;
                double expectedY = site.row() * spacingUm;

                if (Math.abs(site.position().xUm() - expectedX) > 1e-9 ||
                    Math.abs(site.position().yUm() - expectedY) > 1e-9) {
                    throw new IllegalArgumentException(
                        "Site position does not match the declared lattice."
                    );
                }
            }
        }

        static TweezerArray rectangular(
            String arrayId,
            int rows,
            int columns,
            double spacingUm
        ) {
            requirePositive(spacingUm, "Tweezer spacing");
            if (rows <= 0 || columns <= 0) {
                throw new IllegalArgumentException("Array dimensions must be positive.");
            }

            List<Site> sites = new ArrayList<>();
            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    sites.add(new Site(
                        "r" + row + "c" + column,
                        row,
                        column,
                        new Vec2(column * spacingUm, row * spacingUm)
                    ));
                }
            }

            return new TweezerArray(
                arrayId, rows, columns, spacingUm, sites
            );
        }

        Map<String, Site> siteIndex() {
            return sites.stream().collect(Collectors.toUnmodifiableMap(
                Site::id,
                site -> site
            ));
        }
    }

    record Telemetry(
        double vacuumPressurePa,
        boolean interlockHealthy,
        boolean emergencyStop
    ) {
        Telemetry {
            if (!Double.isFinite(vacuumPressurePa) || vacuumPressurePa < 0.0) {
                throw new IllegalArgumentException("Invalid vacuum pressure.");
            }
        }
    }

    record FacilityPolicy(
        double maximumVacuumPressurePa,
        double minimumSpacingUm,
        double maximumBeamPowerW,
        int maximumArraySites
    ) {
        FacilityPolicy {
            requirePositive(maximumVacuumPressurePa, "Vacuum limit");
            requirePositive(minimumSpacingUm, "Minimum spacing");
            requirePositive(maximumBeamPowerW, "Maximum beam power");

            if (maximumArraySites <= 0) {
                throw new IllegalArgumentException("Maximum site count must be positive.");
            }
        }
    }

    record RunRequest(
        TweezerArray array,
        TrapCalibration calibration,
        Telemetry telemetry,
        List<String> occupiedSiteIds,
        List<Vec2> targets
    ) {
        RunRequest {
            Objects.requireNonNull(array, "Array");
            Objects.requireNonNull(calibration, "Calibration");
            Objects.requireNonNull(telemetry, "Telemetry");
            Objects.requireNonNull(occupiedSiteIds, "Occupancy observations");
            Objects.requireNonNull(targets, "Target sites");

            occupiedSiteIds = List.copyOf(occupiedSiteIds);
            targets = List.copyOf(targets);

            if (targets.isEmpty()) {
                throw new IllegalArgumentException("At least one target is required.");
            }

            if (new HashSet<>(occupiedSiteIds).size() != occupiedSiteIds.size()) {
                throw new IllegalArgumentException("Duplicate occupied-site observation.");
            }
        }
    }

    record Finding(String ruleId, String message) {
        Finding {
            Objects.requireNonNull(ruleId);
            Objects.requireNonNull(message);
        }
    }

    record Atom(String atomId, String sourceSiteId, Vec2 position) {}

    record Move(
        String atomId,
        String sourceSiteId,
        int targetIndex,
        Vec2 targetPosition,
        double distanceUm
    ) {}

    record Candidate(Atom atom, int targetIndex, Vec2 target, double distanceUm) {}

    record AuditEvent(
        String runId,
        Instant timestamp,
        RunState state,
        String detail
    ) {}

    record RunResult(
        String runId,
        RunState state,
        int loadedAtoms,
        int requestedTargets,
        int unusedAtoms,
        double totalTransportDistanceUm,
        List<Move> moves,
        double radialTrapFrequencyHz,
        double axialTrapFrequencyHz,
        List<AuditEvent> auditTrail
    ) {
        RunResult {
            moves = List.copyOf(moves);
            auditTrail = List.copyOf(auditTrail);
        }
    }

    interface SafetyRule {
        Optional<Finding> evaluate(RunRequest request, FacilityPolicy policy, Instant now);
    }

    static class VacuumRule implements SafetyRule {
        @Override
        public Optional<Finding> evaluate(
            RunRequest request,
            FacilityPolicy policy,
            Instant now
        ) {
            if (request.telemetry().vacuumPressurePa() >
                policy.maximumVacuumPressurePa()) {
                return Optional.of(new Finding(
                    "VACUUM_LIMIT",
                    "Vacuum pressure exceeds the facility threshold."
                ));
            }
            return Optional.empty();
        }
    }

    static class InterlockRule implements SafetyRule {
        @Override
        public Optional<Finding> evaluate(
            RunRequest request,
            FacilityPolicy policy,
            Instant now
        ) {
            if (!request.telemetry().interlockHealthy()) {
                return Optional.of(new Finding(
                    "LASER_INTERLOCK",
                    "Laser interlock health check failed."
                ));
            }

            if (request.telemetry().emergencyStop()) {
                return Optional.of(new Finding(
                    "EMERGENCY_STOP",
                    "Emergency-stop condition is active."
                ));
            }

            return Optional.empty();
        }
    }

    static class CalibrationRule implements SafetyRule {
        @Override
        public Optional<Finding> evaluate(
            RunRequest request,
            FacilityPolicy policy,
            Instant now
        ) {
            if (!request.calibration().validUntil().isAfter(now)) {
                return Optional.of(new Finding(
                    "CALIBRATION_EXPIRED",
                    "Trap calibration is expired."
                ));
            }

            if (request.calibration().beamPowerW() >
                policy.maximumBeamPowerW()) {
                return Optional.of(new Finding(
                    "BEAM_POWER",
                    "Calibrated beam power exceeds the facility limit."
                ));
            }

            return Optional.empty();
        }
    }

    static class ArrayGeometryRule implements SafetyRule {
        @Override
        public Optional<Finding> evaluate(
            RunRequest request,
            FacilityPolicy policy,
            Instant now
        ) {
            TweezerArray array = request.array();

            if (array.sites().size() > policy.maximumArraySites()) {
                return Optional.of(new Finding(
                    "ARRAY_CAPACITY",
                    "Array exceeds the permitted site count."
                ));
            }

            if (array.spacingUm() < policy.minimumSpacingUm()) {
                return Optional.of(new Finding(
                    "ARRAY_SPACING",
                    "Tweezer separation is below the configured minimum."
                ));
            }

            if (request.targets().size() > array.sites().size()) {
                return Optional.of(new Finding(
                    "TARGET_CAPACITY",
                    "Requested targets exceed the number of available sites."
                ));
            }

            return Optional.empty();
        }
    }

    interface RunLedger {
        void append(AuditEvent event);
        List<AuditEvent> eventsFor(String runId);
    }

    static class InMemoryRunLedger implements RunLedger {
        private final Map<String, CopyOnWriteArrayList<AuditEvent>> events =
            new ConcurrentHashMap<>();

        @Override
        public void append(AuditEvent event) {
            events.computeIfAbsent(
                event.runId(),
                ignored -> new CopyOnWriteArrayList<>()
            ).add(event);
        }

        @Override
        public List<AuditEvent> eventsFor(String runId) {
            return List.copyOf(
                events.getOrDefault(runId, new CopyOnWriteArrayList<>())
            );
        }
    }

    static class RunRejectedException extends RuntimeException {
        private static final long serialVersionUID = 1L;

        private final List<Finding> findings;

        RunRejectedException(List<Finding> findings) {
            super(findings.stream()
                .map(finding -> finding.ruleId() + ": " + finding.message())
                .collect(Collectors.joining("; ")));
            this.findings = List.copyOf(findings);
        }

        List<Finding> findings() {
            return findings;
        }
    }

    static class ExperimentService {
        private final FacilityPolicy policy;
        private final List<SafetyRule> safetyRules;
        private final RunLedger ledger;

        private static final Map<RunState, Set<RunState>> TRANSITIONS = Map.of(
            RunState.DRAFT, Set.of(RunState.VALIDATED, RunState.FAILED),
            RunState.VALIDATED, Set.of(RunState.LOADED, RunState.FAILED),
            RunState.LOADED, Set.of(RunState.REARRANGED, RunState.FAILED),
            RunState.REARRANGED, Set.of(RunState.READY, RunState.FAILED),
            RunState.READY, Set.of(),
            RunState.FAILED, Set.of()
        );

        ExperimentService(FacilityPolicy policy, RunLedger ledger) {
            this.policy = Objects.requireNonNull(policy);
            this.ledger = Objects.requireNonNull(ledger);

            this.safetyRules = List.of(
                new VacuumRule(),
                new InterlockRule(),
                new CalibrationRule(),
                new ArrayGeometryRule()
            );
        }

        private RunState transition(
            String runId,
            RunState current,
            RunState next,
            String detail
        ) {
            if (!TRANSITIONS.getOrDefault(current, Set.of()).contains(next)) {
                throw new IllegalStateException(
                    "Invalid state transition: " + current + " -> " + next
                );
            }

            ledger.append(new AuditEvent(
                runId,
                Instant.now(),
                next,
                detail
            ));
            return next;
        }

        private List<Finding> evaluate(RunRequest request, Instant now) {
            return safetyRules.stream()
                .map(rule -> rule.evaluate(request, policy, now))
                .flatMap(Optional::stream)
                .toList();
        }

        private List<Atom> observeAtoms(RunRequest request) {
            Map<String, Site> siteIndex = request.array().siteIndex();

            List<Atom> atoms = new ArrayList<>();
            int nextId = 1;

            for (String siteId : request.occupiedSiteIds()) {
                Site site = siteIndex.get(siteId);

                if (site == null) {
                    throw new IllegalArgumentException(
                        "Occupancy observation references an unknown site: " + siteId
                    );
                }

                atoms.add(new Atom(
                    "atom-" + nextId++,
                    site.id(),
                    site.position()
                ));
            }

            return List.copyOf(atoms);
        }

        private List<Move> greedyRearrangement(
            List<Atom> atoms,
            List<Vec2> targets
        ) {
            /*
             * The priority queue selects the shortest available atom-target
             * pair, while sets prevent atom or target reuse. This is a
             * deterministic heuristic, not a global assignment algorithm.
             *
             * Time and memory: O(S*T log(S*T)) and O(S*T), respectively.
             */
            PriorityQueue<Candidate> candidates = new PriorityQueue<>(
                Comparator.comparingDouble(Candidate::distanceUm)
                    .thenComparing(candidate -> candidate.atom().atomId())
                    .thenComparingInt(Candidate::targetIndex)
            );

            for (Atom atom : atoms) {
                for (int targetIndex = 0; targetIndex < targets.size(); targetIndex++) {
                    Vec2 target = targets.get(targetIndex);
                    candidates.add(new Candidate(
                        atom,
                        targetIndex,
                        target,
                        atom.position().distanceTo(target)
                    ));
                }
            }

            Set<String> usedAtoms = new HashSet<>();
            Set<Integer> usedTargets = new HashSet<>();
            List<Move> moves = new ArrayList<>();

            int desiredMoves = Math.min(atoms.size(), targets.size());

            while (!candidates.isEmpty() && moves.size() < desiredMoves) {
                Candidate candidate = candidates.remove();

                if (usedAtoms.contains(candidate.atom().atomId()) ||
                    usedTargets.contains(candidate.targetIndex())) {
                    continue;
                }

                usedAtoms.add(candidate.atom().atomId());
                usedTargets.add(candidate.targetIndex());

                moves.add(new Move(
                    candidate.atom().atomId(),
                    candidate.atom().sourceSiteId(),
                    candidate.targetIndex(),
                    candidate.target(),
                    candidate.distanceUm()
                ));
            }

            return List.copyOf(moves);
        }

        RunResult execute(RunRequest request) {
            String runId = UUID.randomUUID().toString();
            RunState state = RunState.DRAFT;

            ledger.append(new AuditEvent(
                runId, Instant.now(), state, "Run created."
            ));

            try {
                List<Finding> findings = evaluate(request, Instant.now());

                if (!findings.isEmpty()) {
                    throw new RunRejectedException(findings);
                }

                state = transition(
                    runId, state, RunState.VALIDATED, "Safety policy passed."
                );

                List<Atom> atoms = observeAtoms(request);

                if (atoms.size() < request.targets().size()) {
                    throw new RunRejectedException(List.of(new Finding(
                        "INSUFFICIENT_ATOMS",
                        "Loaded atom count is smaller than the requested target count."
                    )));
                }

                state = transition(
                    runId,
                    state,
                    RunState.LOADED,
                    "Occupancy observations accepted: " + atoms.size()
                );

                List<Move> moves = greedyRearrangement(atoms, request.targets());

                if (moves.size() != request.targets().size()) {
                    throw new IllegalStateException(
                        "Rearrangement plan failed to fill every target."
                    );
                }

                state = transition(
                    runId,
                    state,
                    RunState.REARRANGED,
                    "Unique atom-to-target assignment created."
                );

                state = transition(
                    runId,
                    state,
                    RunState.READY,
                    "All requested target positions assigned."
                );

                double totalDistance = moves.stream()
                    .mapToDouble(Move::distanceUm)
                    .sum();

                TrapCalibration calibration = request.calibration();

                return new RunResult(
                    runId,
                    state,
                    atoms.size(),
                    request.targets().size(),
                    atoms.size() - moves.size(),
                    totalDistance,
                    moves,
                    calibration.radialFrequencyHz(),
                    calibration.axialFrequencyHz(),
                    ledger.eventsFor(runId)
                );
            } catch (RuntimeException error) {
                if (state != RunState.READY && state != RunState.FAILED) {
                    transition(
                        runId,
                        state,
                        RunState.FAILED,
                        "Run rejected: " + error.getMessage()
                    );
                }
                throw error;
            }
        }
    }

    private static void requirePositive(double value, String label) {
        if (!Double.isFinite(value) || value <= 0.0) {
            throw new IllegalArgumentException(
                label + " must be positive and finite."
            );
        }
    }

    private static List<Vec2> makeCenteredTargets(
        int rows,
        int columns,
        double spacingUm,
        double offsetUm
    ) {
        if (rows <= 0 || columns <= 0) {
            throw new IllegalArgumentException("Target dimensions must be positive.");
        }
        requirePositive(spacingUm, "Target spacing");

        List<Vec2> targets = new ArrayList<>();
        for (int row = 0; row < rows; row++) {
            for (int column = 0; column < columns; column++) {
                targets.add(new Vec2(
                    offsetUm + column * spacingUm,
                    offsetUm + row * spacingUm
                ));
            }
        }
        return List.copyOf(targets);
    }

    public static void main(String[] args) {
        Instant now = Instant.now();

        TrapCalibration calibration = new TrapCalibration(
            "RB87-850NM-CAL-001",
            850e-9,
            0.8e-6,
            BOLTZMANN_CONSTANT * 1e-3,
            RUBIDIUM_87_MASS_KG,
            0.003,
            now.plus(Duration.ofDays(365))
        );

        TweezerArray array = TweezerArray.rectangular(
            "ARRAY-4X4",
            4,
            4,
            5.0
        );

        List<String> observedOccupancy = List.of(
            "r0c1",
            "r0c3",
            "r1c0",
            "r1c2",
            "r2c1",
            "r2c3",
            "r3c0",
            "r3c2",
            "r3c3",
            "r1c3"
        );

        List<Vec2> targets = makeCenteredTargets(3, 3, 5.0, 2.5);

        FacilityPolicy policy = new FacilityPolicy(
            1e-7,
            3.5,
            0.01,
            256
        );

        InMemoryRunLedger ledger = new InMemoryRunLedger();
        ExperimentService service = new ExperimentService(policy, ledger);

        RunRequest validRequest = new RunRequest(
            array,
            calibration,
            new Telemetry(2e-8, true, false),
            observedOccupancy,
            targets
        );

        System.out.println("VALID FACILITY RUN");
        try {
            RunResult result = service.execute(validRequest);

            System.out.println("Run ID: " + result.runId());
            System.out.println("State: " + result.state());
            System.out.println("Loaded atoms: " + result.loadedAtoms());
            System.out.println("Requested targets: " + result.requestedTargets());
            System.out.println("Unused atoms: " + result.unusedAtoms());
            System.out.printf(
                "Total transport distance: %.4f um%n",
                result.totalTransportDistanceUm()
            );
            System.out.printf(
                "Radial trap frequency: %.2f Hz%n",
                result.radialTrapFrequencyHz()
            );
            System.out.printf(
                "Axial trap frequency: %.2f Hz%n",
                result.axialTrapFrequencyHz()
            );
            System.out.println("Audit events: " + result.auditTrail().size());

            for (Move move : result.moves()) {
                System.out.printf(
                    "%s: %s -> target-%d, distance %.3f um%n",
                    move.atomId(),
                    move.sourceSiteId(),
                    move.targetIndex(),
                    move.distanceUm()
                );
            }
        } catch (RuntimeException error) {
            System.err.println("Valid run failed: " + error.getMessage());
        }

        System.out.println("\nREJECTED FACILITY RUN");

        RunRequest unsafeRequest = new RunRequest(
            array,
            calibration,
            new Telemetry(5e-7, false, false),
            observedOccupancy,
            targets
        );

        try {
            service.execute(unsafeRequest);
            System.err.println("Unexpected result: unsafe run was accepted.");
        } catch (RunRejectedException error) {
            for (Finding finding : error.findings()) {
                System.out.println(
                    finding.ruleId() + ": " + finding.message()
                );
            }
        }
    }
}
