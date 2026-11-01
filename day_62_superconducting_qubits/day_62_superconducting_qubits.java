import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Superconducting Qubits: Josephson Junctions and Circuits.
 *
 * Java 17 enterprise-style domain model covering:
 * - Josephson junction parameters
 * - Josephson energy and inductance
 * - RCSJ phase dynamics
 * - rf-SQUID potential
 * - transmon energy spectrum
 * - explicit qubit state representation
 * - validation and controlled state transitions
 * - measurement sampling
 */
public class SuperconductingQubitCircuit {

    private static final double E_CHARGE = 1.602176634e-19;
    private static final double PLANCK = 6.62607015e-34;
    private static final double PI = Math.PI;
    private static final double PHI0 =
            PLANCK / (2.0 * E_CHARGE);

    private static void requirePositiveFinite(
            double value,
            String field) {

        if (!Double.isFinite(value) || value <= 0.0) {
            throw new CircuitException(
                    field + " must be positive and finite."
            );
        }
    }

    private static void requireFinite(
            double value,
            String field) {

        if (!Double.isFinite(value)) {
            throw new CircuitException(
                    field + " must be finite."
            );
        }
    }

    private static String formatFrequency(double hz) {
        double magnitude = Math.abs(hz);

        if (magnitude >= 1e9) {
            return "%.6f GHz".formatted(hz / 1e9);
        }

        if (magnitude >= 1e6) {
            return "%.6f MHz".formatted(hz / 1e6);
        }

        if (magnitude >= 1e3) {
            return "%.6f kHz".formatted(hz / 1e3);
        }

        return "%.6f Hz".formatted(hz);
    }

    private static final class CircuitException
            extends RuntimeException {

        CircuitException(String message) {
            super(message);
        }
    }

    enum QubitLevel {
        ZERO,
        ONE
    }

    record PhasePoint(
            double time,
            double phase,
            double phaseRate
    ) {}

    static final class JosephsonJunction {

        private final double criticalCurrent;
        private final double capacitance;
        private final double resistance;

        JosephsonJunction(
                double criticalCurrent,
                double capacitance,
                double resistance) {

            requirePositiveFinite(
                    criticalCurrent,
                    "criticalCurrent"
            );

            requirePositiveFinite(
                    capacitance,
                    "capacitance"
            );

            requirePositiveFinite(
                    resistance,
                    "resistance"
            );

            this.criticalCurrent = criticalCurrent;
            this.capacitance = capacitance;
            this.resistance = resistance;
        }

        double criticalCurrent() {
            return criticalCurrent;
        }

        double capacitance() {
            return capacitance;
        }

        double resistance() {
            return resistance;
        }

        double josephsonEnergy() {
            return PHI0 * criticalCurrent
                    / (2.0 * PI);
        }

        double josephsonEnergyFrequency() {
            return josephsonEnergy() / PLANCK;
        }

        double josephsonInductance() {
            return PHI0
                    / (2.0 * PI * criticalCurrent);
        }

        double plasmaFrequency() {
            double omega = 1.0 / Math.sqrt(
                    josephsonInductance() * capacitance
            );

            return omega / (2.0 * PI);
        }

        double supercurrent(double phase) {
            requireFinite(phase, "phase");
            return criticalCurrent * Math.sin(phase);
        }

        double voltage(double phaseRate) {
            requireFinite(phaseRate, "phaseRate");

            return PHI0 * phaseRate
                    / (2.0 * PI);
        }

        double phaseAcceleration(
                double biasCurrent,
                double phase,
                double phaseRate) {

            requireFinite(biasCurrent, "biasCurrent");
            requireFinite(phase, "phase");
            requireFinite(phaseRate, "phaseRate");

            double voltage = voltage(phaseRate);

            double numerator =
                    biasCurrent
                    - supercurrent(phase)
                    - voltage / resistance;

            double denominator =
                    capacitance * PHI0
                    / (2.0 * PI);

            return numerator / denominator;
        }
    }

    static final class Transmon {

        private final JosephsonJunction junction;
        private final double chargingEnergy;

        Transmon(
                JosephsonJunction junction,
                double chargingEnergy) {

            if (junction == null) {
                throw new CircuitException(
                        "Junction cannot be null."
                );
            }

            requirePositiveFinite(
                    chargingEnergy,
                    "chargingEnergy"
            );

            this.junction = junction;
            this.chargingEnergy = chargingEnergy;
        }

        double ejOverEc() {
            return junction.josephsonEnergy()
                    / chargingEnergy;
        }

        double transition01() {
            double ej = junction.josephsonEnergy();
            double ec = chargingEnergy;

            return Math.sqrt(8.0 * ej * ec)
                    / PLANCK
                    - ec / PLANCK;
        }

        double anharmonicity() {
            return -chargingEnergy / PLANCK;
        }

        double levelEnergy(int n) {
            if (n < 0) {
                throw new CircuitException(
                        "Energy level cannot be negative."
                );
            }

            double ej = junction.josephsonEnergy();
            double ec = chargingEnergy;

            return -ej
                    + Math.sqrt(8.0 * ej * ec)
                    * (n + 0.5)
                    - ec / 12.0
                    * (6.0 * n * n + 6.0 * n + 3.0);
        }
    }

    static final class RfSquid {

        private final JosephsonJunction junction;
        private final double loopInductance;

        RfSquid(
                JosephsonJunction junction,
                double loopInductance) {

            if (junction == null) {
                throw new CircuitException(
                        "Junction cannot be null."
                );
            }

            requirePositiveFinite(
                    loopInductance,
                    "loopInductance"
            );

            this.junction = junction;
            this.loopInductance = loopInductance;
        }

        double betaL() {
            return 2.0 * PI
                    * loopInductance
                    * junction.criticalCurrent()
                    / PHI0;
        }

        double potential(
                double phase,
                double externalFlux) {

            requireFinite(phase, "phase");
            requireFinite(
                    externalFlux,
                    "externalFlux"
            );

            double phiExt =
                    2.0 * PI * externalFlux / PHI0;

            double phiScale =
                    PHI0 / (2.0 * PI);

            double inductive =
                    phiScale * phiScale
                    * Math.pow(
                            phase - phiExt,
                            2
                    )
                    / (2.0 * loopInductance);

            double josephson =
                    -junction.josephsonEnergy()
                    * Math.cos(phase);

            return inductive + josephson;
        }
    }

    static final class QubitState {

        private double alphaReal = 1.0;
        private double alphaImag = 0.0;
        private double betaReal = 0.0;
        private double betaImag = 0.0;

        QubitState() {
            normalize();
        }

        private double magnitudeSquared(
                double real,
                double imaginary) {

            return real * real + imaginary * imaginary;
        }

        void normalize() {
            double norm = Math.sqrt(
                    magnitudeSquared(
                            alphaReal,
                            alphaImag
                    )
                    +
                    magnitudeSquared(
                            betaReal,
                            betaImag
                    )
            );

            if (!Double.isFinite(norm) || norm <= 0.0) {
                throw new CircuitException(
                        "Invalid qubit-state norm."
                );
            }

            alphaReal /= norm;
            alphaImag /= norm;
            betaReal /= norm;
            betaImag /= norm;
        }

        double probabilityZero() {
            return magnitudeSquared(
                    alphaReal,
                    alphaImag
            );
        }

        double probabilityOne() {
            return magnitudeSquared(
                    betaReal,
                    betaImag
            );
        }

        void rotateY(double theta) {
            requireFinite(theta, "theta");

            double c = Math.cos(theta / 2.0);
            double s = Math.sin(theta / 2.0);

            double oldAlphaReal = alphaReal;
            double oldAlphaImag = alphaImag;
            double oldBetaReal = betaReal;
            double oldBetaImag = betaImag;

            alphaReal =
                    c * oldAlphaReal
                    - s * oldBetaReal;

            alphaImag =
                    c * oldAlphaImag
                    - s * oldBetaImag;

            betaReal =
                    s * oldAlphaReal
                    + c * oldBetaReal;

            betaImag =
                    s * oldAlphaImag
                    + c * oldBetaImag;

            normalize();
        }

        QubitLevel measure(Random random) {
            if (random == null) {
                throw new CircuitException(
                        "Random source cannot be null."
                );
            }

            if (random.nextDouble()
                    < probabilityZero()) {

                alphaReal = 1.0;
                alphaImag = 0.0;
                betaReal = 0.0;
                betaImag = 0.0;

                return QubitLevel.ZERO;
            }

            alphaReal = 0.0;
            alphaImag = 0.0;
            betaReal = 1.0;
            betaImag = 0.0;

            return QubitLevel.ONE;
        }
    }

    static final class CircuitSimulationService {

        List<PhasePoint> simulateRcsj(
                JosephsonJunction junction,
                double biasCurrent,
                double initialPhase,
                double initialRate,
                double dt,
                int steps) {

            if (junction == null) {
                throw new CircuitException(
                        "Junction cannot be null."
                );
            }

            requirePositiveFinite(dt, "dt");

            if (steps < 1 || steps > 1_000_000) {
                throw new CircuitException(
                        "steps must be in [1, 1000000]."
                );
            }

            List<PhasePoint> trace =
                    new ArrayList<>(steps + 1);

            double time = 0.0;
            double phase = initialPhase;
            double rate = initialRate;

            for (int i = 0; i <= steps; i++) {

                trace.add(
                        new PhasePoint(
                                time,
                                phase,
                                rate
                        )
                );

                double acceleration =
                        junction.phaseAcceleration(
                                biasCurrent,
                                phase,
                                rate
                        );

                /*
                 * Semi-implicit Euler is deliberately used for
                 * this compact service model. A production simulator
                 * can replace it with adaptive integration.
                 */
                rate += dt * acceleration;
                phase += dt * rate;
                time += dt;

                if (!Double.isFinite(phase)
                        || !Double.isFinite(rate)) {

                    throw new CircuitException(
                            "RCSJ simulation became unstable."
                    );
                }
            }

            return List.copyOf(trace);
        }

        MeasurementResult measure(
                QubitState state,
                int shots,
                long seed) {

            if (state == null) {
                throw new CircuitException(
                        "Qubit state cannot be null."
                );
            }

            if (shots < 1 || shots > 1_000_000) {
                throw new CircuitException(
                        "shots must be in [1, 1000000]."
                );
            }

            Random random = new Random(seed);
            int zero = 0;
            int one = 0;

            for (int i = 0; i < shots; i++) {
                QubitState copy = new QubitState();
                copy.rotateY(
                        Math.atan2(
                                Math.sqrt(state.probabilityOne()),
                                Math.sqrt(state.probabilityZero())
                        ) * 2.0
                );

                if (copy.measure(random) == QubitLevel.ZERO) {
                    zero++;
                } else {
                    one++;
                }
            }

            return new MeasurementResult(
                    shots,
                    zero,
                    one,
                    (double) zero / shots,
                    (double) one / shots
            );
        }
    }

    record MeasurementResult(
            int shots,
            int zero,
            int one,
            double zeroProbability,
            double oneProbability
    ) {}

    private static void validate(
            JosephsonJunction junction,
            Transmon transmon,
            RfSquid squid) {

        if (!(junction.josephsonEnergy() > 0.0)) {
            throw new CircuitException(
                    "Josephson energy is invalid."
            );
        }

        if (!(junction.josephsonInductance() > 0.0)) {
            throw new CircuitException(
                    "Josephson inductance is invalid."
            );
        }

        if (!(junction.plasmaFrequency() > 0.0)) {
            throw new CircuitException(
                    "Plasma frequency is invalid."
            );
        }

        if (!(transmon.ejOverEc() > 0.0)) {
            throw new CircuitException(
                    "EJ/EC is invalid."
            );
        }

        if (!(transmon.transition01() > 0.0)) {
            throw new CircuitException(
                    "Transmon transition is invalid."
            );
        }

        if (!(transmon.anharmonicity() < 0.0)) {
            throw new CircuitException(
                    "Transmon anharmonicity is expected to be negative."
            );
        }

        if (!(squid.betaL() > 0.0)) {
            throw new CircuitException(
                    "Beta_L is invalid."
            );
        }
    }

    public static void main(String[] args) {

        try {
            JosephsonJunction junction =
                    new JosephsonJunction(
                            35e-9,
                            80e-15,
                            1500.0
                    );

            Transmon transmon =
                    new Transmon(
                            junction,
                            0.25
                                    * junction.josephsonEnergy()
                    );

            RfSquid squid =
                    new RfSquid(
                            junction,
                            12e-9
                    );

            validate(
                    junction,
                    transmon,
                    squid
            );

            System.out.println(
                    "SUPERCONDUCTING QUBIT / JOSEPHSON CIRCUIT MODEL"
            );
            System.out.println(
                    "================================================"
            );

            System.out.println("\nJunction");
            System.out.printf(
                    "Ic: %.6e A%n",
                    junction.criticalCurrent()
            );
            System.out.printf(
                    "Cj: %.6e F%n",
                    junction.capacitance()
            );
            System.out.printf(
                    "Rn: %.6e ohm%n",
                    junction.resistance()
            );
            System.out.printf(
                    "EJ: %.6e J%n",
                    junction.josephsonEnergy()
            );
            System.out.println(
                    "EJ/h: "
                            + formatFrequency(
                                    junction.josephsonEnergyFrequency()
                            )
            );
            System.out.printf(
                    "LJ: %.6e H%n",
                    junction.josephsonInductance()
            );
            System.out.println(
                    "Plasma: "
                            + formatFrequency(
                                    junction.plasmaFrequency()
                            )
            );

            double phase = PI / 3.0;

            System.out.println(
                    "\nJosephson current-phase relation"
            );
            System.out.printf(
                    "I(phi): %.6e A%n",
                    junction.supercurrent(phase)
            );

            System.out.println("\nTransmon");
            System.out.printf(
                    "EJ/EC: %.6f%n",
                    transmon.ejOverEc()
            );
            System.out.println(
                    "f01: "
                            + formatFrequency(
                                    transmon.transition01()
                            )
            );
            System.out.println(
                    "Anharmonicity: "
                            + formatFrequency(
                                    transmon.anharmonicity()
                            )
            );

            for (int n = 0; n < 4; n++) {
                System.out.printf(
                        "E%d: %.6e J%n",
                        n,
                        transmon.levelEnergy(n)
                );
            }

            System.out.println("\nrf-SQUID");
            System.out.printf(
                    "Beta_L: %.6f%n",
                    squid.betaL()
            );

            double externalFlux =
                    PHI0 / 2.0;

            System.out.printf(
                    "U(0, Phi0/2): %.6e J%n",
                    squid.potential(
                            0.0,
                            externalFlux
                    )
            );

            CircuitSimulationService service =
                    new CircuitSimulationService();

            System.out.println(
                    "\nRCSJ phase simulation"
            );

            List<PhasePoint> trace =
                    service.simulateRcsj(
                            junction,
                            0.55
                                    * junction.criticalCurrent(),
                            0.0,
                            0.0,
                            1e-14,
                            20
                    );

            for (int i = 0; i < trace.size(); i += 5) {
                PhasePoint point = trace.get(i);

                System.out.printf(
                        "t=%.3e s phi=%.6f phiDot=%.3e%n",
                        point.time(),
                        point.phase(),
                        point.phaseRate()
                );
            }

            System.out.println("\nQubit state");

            QubitState state = new QubitState();
            state.rotateY(PI / 2.0);

            System.out.printf(
                    "P(0): %.6f%n",
                    state.probabilityZero()
            );
            System.out.printf(
                    "P(1): %.6f%n",
                    state.probabilityOne()
            );

            MeasurementResult measurement =
                    service.measure(
                            state,
                            1000,
                            20261101L
                    );

            System.out.printf(
                    "1000 shots: zero=%d one=%d%n",
                    measurement.zero(),
                    measurement.one()
            );

            System.out.println("\nValidation");

            try {
                new JosephsonJunction(
                        -1e-9,
                        80e-15,
                        1000.0
                );
            } catch (CircuitException error) {
                System.out.println(
                        "Invalid critical current rejected."
                );
            }

            try {
                new Transmon(
                        junction,
                        -1e-24
                );
            } catch (CircuitException error) {
                System.out.println(
                        "Invalid charging energy rejected."
                );
            }

            System.out.println("\nComplexity");
            System.out.println(
                    "Circuit property calculations: O(1)"
            );
            System.out.println(
                    "RCSJ trajectory: O(N)"
            );
            System.out.println(
                    "Measurement sampling: O(M)"
            );

        } catch (RuntimeException error) {
            System.err.println(
                    "Circuit-model failure: "
                            + error.getMessage()
            );
            System.exit(1);
        }
    }
}
