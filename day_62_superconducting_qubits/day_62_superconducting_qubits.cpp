#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace physics {
constexpr double E_CHARGE = 1.602176634e-19;
constexpr double PLANCK = 6.62607015e-34;
constexpr double PI = 3.141592653589793238462643383279502884;
constexpr double PHI0 = PLANCK / (2.0 * E_CHARGE);
}

class CircuitError : public std::runtime_error {
public:
    explicit CircuitError(const std::string& message)
        : std::runtime_error(message) {}
};

class JosephsonJunction {
private:
    double criticalCurrent_;
    double capacitance_;
    double resistance_;

public:
    JosephsonJunction(double criticalCurrent,
                      double capacitance,
                      double resistance)
        : criticalCurrent_(criticalCurrent),
          capacitance_(capacitance),
          resistance_(resistance) {
        if (!std::isfinite(criticalCurrent_) || criticalCurrent_ <= 0.0)
            throw CircuitError("Critical current must be positive.");
        if (!std::isfinite(capacitance_) || capacitance_ <= 0.0)
            throw CircuitError("Capacitance must be positive.");
        if (!std::isfinite(resistance_) || resistance_ <= 0.0)
            throw CircuitError("Resistance must be positive.");
    }

    double criticalCurrent() const { return criticalCurrent_; }
    double capacitance() const { return capacitance_; }
    double resistance() const { return resistance_; }

    double josephsonEnergy() const {
        return physics::PHI0 * criticalCurrent_
               / (2.0 * physics::PI);
    }

    double josephsonEnergyFrequency() const {
        return josephsonEnergy() / physics::PLANCK;
    }

    double josephsonInductance() const {
        return physics::PHI0
               / (2.0 * physics::PI * criticalCurrent_);
    }

    double plasmaFrequency() const {
        const double omega =
            1.0 / std::sqrt(josephsonInductance() * capacitance_);
        return omega / (2.0 * physics::PI);
    }

    double supercurrent(double phase) const {
        if (!std::isfinite(phase))
            throw CircuitError("Phase is not finite.");

        return criticalCurrent_ * std::sin(phase);
    }

    double voltage(double phaseRate) const {
        if (!std::isfinite(phaseRate))
            throw CircuitError("Phase rate is not finite.");

        return physics::PHI0 * phaseRate
               / (2.0 * physics::PI);
    }

    double phaseAcceleration(double biasCurrent,
                             double phase,
                             double phaseRate) const {
        if (!std::isfinite(biasCurrent) ||
            !std::isfinite(phase) ||
            !std::isfinite(phaseRate)) {
            throw CircuitError("RCSJ state contains a non-finite value.");
        }

        const double resistive = voltage(phaseRate) / resistance_;

        const double numerator =
            biasCurrent - supercurrent(phase) - resistive;

        const double denominator =
            capacitance_ * physics::PHI0 / (2.0 * physics::PI);

        return numerator / denominator;
    }
};

class Transmon {
private:
    const JosephsonJunction& junction_;
    double chargingEnergy_;

public:
    Transmon(const JosephsonJunction& junction,
             double chargingEnergy)
        : junction_(junction),
          chargingEnergy_(chargingEnergy) {
        if (!std::isfinite(chargingEnergy_) ||
            chargingEnergy_ <= 0.0) {
            throw CircuitError("Charging energy must be positive.");
        }
    }

    double ejOverEc() const {
        return junction_.josephsonEnergy() / chargingEnergy_;
    }

    double transition01() const {
        const double ej = junction_.josephsonEnergy();
        const double ec = chargingEnergy_;

        return std::sqrt(8.0 * ej * ec) / physics::PLANCK
               - ec / physics::PLANCK;
    }

    double anharmonicity() const {
        return -chargingEnergy_ / physics::PLANCK;
    }

    double levelEnergy(int n) const {
        if (n < 0)
            throw CircuitError("Level index cannot be negative.");

        const double ej = junction_.josephsonEnergy();
        const double ec = chargingEnergy_;

        return -ej
            + std::sqrt(8.0 * ej * ec) * (n + 0.5)
            - ec / 12.0
              * (6.0 * n * n + 6.0 * n + 3.0);
    }
};

class RfSquid {
private:
    const JosephsonJunction& junction_;
    double loopInductance_;

public:
    RfSquid(const JosephsonJunction& junction,
            double loopInductance)
        : junction_(junction),
          loopInductance_(loopInductance) {
        if (!std::isfinite(loopInductance_) ||
            loopInductance_ <= 0.0) {
            throw CircuitError("Loop inductance must be positive.");
        }
    }

    double betaL() const {
        return 2.0 * physics::PI
               * loopInductance_
               * junction_.criticalCurrent()
               / physics::PHI0;
    }

    double potential(double phase,
                     double externalFlux) const {
        if (!std::isfinite(phase) ||
            !std::isfinite(externalFlux)) {
            throw CircuitError("Potential input is not finite.");
        }

        const double phiExt =
            2.0 * physics::PI * externalFlux / physics::PHI0;

        const double phiScale =
            physics::PHI0 / (2.0 * physics::PI);

        const double inductive =
            phiScale * phiScale
            * (phase - phiExt) * (phase - phiExt)
            / (2.0 * loopInductance_);

        const double josephson =
            -junction_.josephsonEnergy() * std::cos(phase);

        return inductive + josephson;
    }
};

struct StateVector {
    double alphaReal{1.0};
    double alphaImag{0.0};
    double betaReal{0.0};
    double betaImag{0.0};

    void normalize() {
        const double norm = std::sqrt(
            alphaReal * alphaReal +
            alphaImag * alphaImag +
            betaReal * betaReal +
            betaImag * betaImag
        );

        if (!std::isfinite(norm) || norm <= 0.0)
            throw CircuitError("Invalid qubit state norm.");

        alphaReal /= norm;
        alphaImag /= norm;
        betaReal /= norm;
        betaImag /= norm;
    }

    double probabilityZero() const {
        return alphaReal * alphaReal +
               alphaImag * alphaImag;
    }

    double probabilityOne() const {
        return betaReal * betaReal +
               betaImag * betaImag;
    }

    void rotateY(double theta) {
        if (!std::isfinite(theta))
            throw CircuitError("Rotation angle is not finite.");

        const double c = std::cos(theta / 2.0);
        const double s = std::sin(theta / 2.0);

        const double oldAR = alphaReal;
        const double oldAI = alphaImag;
        const double oldBR = betaReal;
        const double oldBI = betaImag;

        alphaReal = c * oldAR - s * oldBR;
        alphaImag = c * oldAI - s * oldBI;

        betaReal = s * oldAR + c * oldBR;
        betaImag = s * oldAI + c * oldBI;

        normalize();
    }

    int measure(std::mt19937_64& rng) {
        std::uniform_real_distribution<double> distribution(0.0, 1.0);

        const int result =
            distribution(rng) < probabilityZero() ? 0 : 1;

        if (result == 0) {
            alphaReal = 1.0;
            alphaImag = 0.0;
            betaReal = 0.0;
            betaImag = 0.0;
        } else {
            alphaReal = 0.0;
            alphaImag = 0.0;
            betaReal = 1.0;
            betaImag = 0.0;
        }

        return result;
    }
};

struct PhasePoint {
    double time;
    double phase;
    double phaseRate;
};

std::vector<PhasePoint> simulateRcsj(
    const JosephsonJunction& junction,
    double biasCurrent,
    double initialPhase,
    double initialRate,
    double dt,
    std::size_t steps) {

    if (!std::isfinite(dt) || dt <= 0.0)
        throw CircuitError("Time step must be positive.");

    std::vector<PhasePoint> trace;
    trace.reserve(steps + 1);

    double t = 0.0;
    double phase = initialPhase;
    double rate = initialRate;

    for (std::size_t i = 0; i <= steps; ++i) {
        trace.push_back({t, phase, rate});

        /*
         * Semi-implicit Euler:
         * first update the phase velocity, then integrate the phase.
         * This gives a useful stable baseline for a dissipative junction.
         */
        const double acceleration =
            junction.phaseAcceleration(
                biasCurrent,
                phase,
                rate
            );

        rate += dt * acceleration;
        phase += dt * rate;
        t += dt;

        if (!std::isfinite(phase) ||
            !std::isfinite(rate)) {
            throw CircuitError(
                "RCSJ simulation became numerically unstable."
            );
        }
    }

    return trace;
}

std::string formatFrequency(double hz) {
    std::ostringstream output;
    output << std::fixed << std::setprecision(6);

    if (std::abs(hz) >= 1e9)
        output << hz / 1e9 << " GHz";
    else if (std::abs(hz) >= 1e6)
        output << hz / 1e6 << " MHz";
    else if (std::abs(hz) >= 1e3)
        output << hz / 1e3 << " kHz";
    else
        output << hz << " Hz";

    return output.str();
}

void validateModel(const JosephsonJunction& junction,
                   const Transmon& transmon,
                   const RfSquid& squid) {
    if (!(junction.josephsonEnergy() > 0.0))
        throw CircuitError("Invalid Josephson energy.");

    if (!(junction.josephsonInductance() > 0.0))
        throw CircuitError("Invalid Josephson inductance.");

    if (!(junction.plasmaFrequency() > 0.0))
        throw CircuitError("Invalid plasma frequency.");

    if (!(transmon.ejOverEc() > 0.0))
        throw CircuitError("Invalid EJ/EC ratio.");

    if (!(transmon.transition01() > 0.0))
        throw CircuitError("Invalid transmon transition.");

    if (!(transmon.anharmonicity() < 0.0))
        throw CircuitError("Expected negative transmon anharmonicity.");

    if (!(squid.betaL() > 0.0))
        throw CircuitError("Invalid SQUID screening parameter.");
}

int main() {
    try {
        JosephsonJunction junction(
            35e-9,
            80e-15,
            1500.0
        );

        Transmon transmon(
            junction,
            0.25 * junction.josephsonEnergy()
        );

        RfSquid squid(
            junction,
            12e-9
        );

        validateModel(junction, transmon, squid);

        std::cout << std::scientific
                  << std::setprecision(6);

        std::cout
            << "SUPERCONDUCTING QUBIT / JOSEPHSON CIRCUIT MODEL\n"
            << "================================================\n";

        std::cout << "\nJosephson junction\n";
        std::cout << "Ic: "
                  << junction.criticalCurrent() << " A\n";
        std::cout << "Cj: "
                  << junction.capacitance() << " F\n";
        std::cout << "Rn: "
                  << junction.resistance() << " ohm\n";
        std::cout << "EJ: "
                  << junction.josephsonEnergy() << " J\n";
        std::cout << "EJ/h: "
                  << formatFrequency(
                         junction.josephsonEnergyFrequency())
                  << '\n';
        std::cout << "LJ: "
                  << junction.josephsonInductance() << " H\n";
        std::cout << "Plasma: "
                  << formatFrequency(junction.plasmaFrequency())
                  << '\n';

        const double phase = physics::PI / 3.0;

        std::cout << "\nJosephson current-phase relation\n";
        std::cout << "Phase: "
                  << phase << " rad\n";
        std::cout << "Current: "
                  << junction.supercurrent(phase)
                  << " A\n";

        std::cout << "\nTransmon\n";
        std::cout << "EJ/EC: "
                  << transmon.ejOverEc() << '\n';
        std::cout << "f01: "
                  << formatFrequency(transmon.transition01())
                  << '\n';
        std::cout << "Anharmonicity: "
                  << formatFrequency(transmon.anharmonicity())
                  << '\n';

        for (int n = 0; n < 4; ++n) {
            std::cout << "E[" << n << "]: "
                      << transmon.levelEnergy(n)
                      << " J\n";
        }

        std::cout << "\nrf-SQUID\n";
        std::cout << "Beta_L: "
                  << squid.betaL() << '\n';

        const double externalFlux = physics::PHI0 / 2.0;
        std::cout << "U(0, Phi0/2): "
                  << squid.potential(0.0, externalFlux)
                  << " J\n";

        std::cout << "\nRCSJ simulation\n";

        const auto trace = simulateRcsj(
            junction,
            0.55 * junction.criticalCurrent(),
            0.0,
            0.0,
            1e-14,
            20
        );

        for (std::size_t i = 0; i < trace.size(); i += 5) {
            const auto& point = trace[i];

            std::cout
                << "t=" << point.time
                << " s, phi=" << point.phase
                << ", phi_dot=" << point.phaseRate
                << '\n';
        }

        std::cout << "\nQubit state\n";

        StateVector state;
        state.rotateY(physics::PI / 2.0);

        std::cout << "P(0): "
                  << state.probabilityZero() << '\n';
        std::cout << "P(1): "
                  << state.probabilityOne() << '\n';

        std::mt19937_64 rng(20261101);

        constexpr int shots = 1000;
        int zeroCount = 0;
        int oneCount = 0;

        for (int i = 0; i < shots; ++i) {
            StateVector measurementState = state;

            if (measurementState.measure(rng) == 0)
                ++zeroCount;
            else
                ++oneCount;
        }

        std::cout
            << "Measurement results: zero="
            << zeroCount
            << ", one="
            << oneCount
            << '\n';

        std::cout << "\nValidation\n";

        try {
            JosephsonJunction invalid(
                -1e-9,
                80e-15,
                1000.0
            );
        } catch (const CircuitError&) {
            std::cout << "Negative Ic rejected.\n";
        }

        try {
            RfSquid invalid(
                junction,
                -1e-9
            );
        } catch (const CircuitError&) {
            std::cout << "Negative loop inductance rejected.\n";
        }

        std::cout << "\nComplexity\n";
        std::cout << "Circuit properties: O(1)\n";
        std::cout << "RCSJ trajectory with N steps: O(N)\n";
        std::cout << "Measurement sampling with M shots: O(M)\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Simulation failure: "
            << error.what()
            << '\n';
        return 1;
    }

    return 0;
}
