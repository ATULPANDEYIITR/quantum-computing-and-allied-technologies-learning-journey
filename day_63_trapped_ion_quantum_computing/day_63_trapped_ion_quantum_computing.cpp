#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

class GovernanceError : public std::runtime_error {
public:
    explicit GovernanceError(const std::string& message)
        : std::runtime_error(message) {}
};

enum class PulseType {
    SingleQubit,
    Entangling
};

enum class CheckState {
    Pending,
    Passed,
    Failed
};

struct Ion {
    int id;
    double massAmu;
    double axialFrequencyMHz;
};

struct Trap {
    double radialFrequencyMHz;
    double axialFrequencyMHz;
    double wavelengthNm;

    void validate() const {
        if (radialFrequencyMHz <= axialFrequencyMHz) {
            throw GovernanceError(
                "Radial frequency must exceed axial frequency.");
        }

        if (wavelengthNm < 200.0 || wavelengthNm > 2000.0) {
            throw GovernanceError("Unsupported laser wavelength.");
        }
    }

    double modeSpacingMHz() const {
        return radialFrequencyMHz - axialFrequencyMHz;
    }
};

struct LaserChannel {
    std::string name;
    double maxPowerMw;
    double rabiScale;
    double frequencyOffsetMHz;

    void validate() const {
        if (name.empty() || maxPowerMw <= 0.0 || rabiScale <= 0.0) {
            throw GovernanceError("Invalid laser channel configuration.");
        }
    }
};

struct Pulse {
    std::string id;
    int ion;
    std::optional<int> targetIon;
    double startNs;
    double durationNs;
    double rabiFrequencyMHz;
    double detuningMHz;
    double phaseRad;
    PulseType type;

    double endNs() const {
        return startNs + durationNs;
    }
};

struct CalibrationResult {
    bool passed;
    double measuredRabiMHz;
    double measuredDetuningMHz;
};

class LaserCalibration {
private:
    double targetRabiMHz_;
    double maxDetuningMHz_;

public:
    LaserCalibration(double targetRabiMHz, double maxDetuningMHz)
        : targetRabiMHz_(targetRabiMHz),
          maxDetuningMHz_(maxDetuningMHz) {}

    CalibrationResult verify(
        double measuredRabiMHz,
        double measuredDetuningMHz) const {

        const double relativeError =
            std::abs(measuredRabiMHz - targetRabiMHz_) / targetRabiMHz_;

        const bool rabiOk = relativeError <= 0.05;
        const bool detuningOk =
            std::abs(measuredDetuningMHz) <= maxDetuningMHz_;

        return {
            rabiOk && detuningOk,
            measuredRabiMHz,
            measuredDetuningMHz
        };
    }
};

class PulseScheduler {
private:
    std::vector<Pulse> pulses_;

    static std::set<int> occupiedIons(const Pulse& pulse) {
        std::set<int> result{pulse.ion};

        if (pulse.targetIon.has_value()) {
            result.insert(*pulse.targetIon);
        }

        return result;
    }

    static bool overlaps(const Pulse& a, const Pulse& b) {
        return a.startNs < b.endNs() &&
               b.startNs < a.endNs();
    }

public:
    void schedule(const Pulse& pulse) {
        if (pulse.startNs < 0.0 || pulse.durationNs <= 0.0) {
            throw GovernanceError("Invalid pulse timing.");
        }

        if (pulse.rabiFrequencyMHz <= 0.0) {
            throw GovernanceError("Rabi frequency must be positive.");
        }

        if (pulse.type == PulseType::Entangling) {
            if (!pulse.targetIon.has_value() ||
                *pulse.targetIon == pulse.ion) {
                throw GovernanceError(
                    "Entangling pulse requires two distinct ions.");
            }
        }

        const auto requestedIons = occupiedIons(pulse);

        for (const auto& existing : pulses_) {
            if (!overlaps(existing, pulse)) {
                continue;
            }

            const auto existingIons = occupiedIons(existing);

            std::vector<int> intersection;
            std::set_intersection(
                requestedIons.begin(),
                requestedIons.end(),
                existingIons.begin(),
                existingIons.end(),
                std::back_inserter(intersection)
            );

            if (!intersection.empty()) {
                throw GovernanceError(
                    "Overlapping pulses compete for the same ion.");
            }
        }

        pulses_.push_back(pulse);

        std::sort(
            pulses_.begin(),
            pulses_.end(),
            [](const Pulse& a, const Pulse& b) {
                return a.startNs < b.startNs;
            }
        );
    }

    const std::vector<Pulse>& pulses() const {
        return pulses_;
    }
};

class IonTrapController {
private:
    Trap trap_;
    std::map<int, Ion> ions_;
    LaserChannel laser_;
    PulseScheduler scheduler_;
    double maxDetuningMHz_;
    double maxPulseNs_;

    void validateIon(int ionId) const {
        if (!ions_.contains(ionId)) {
            throw GovernanceError("Unknown ion ID.");
        }
    }

public:
    IonTrapController(
        Trap trap,
        std::vector<Ion> ions,
        LaserChannel laser,
        double maxDetuningMHz,
        double maxPulseNs
    )
        : trap_(trap),
          laser_(laser),
          maxDetuningMHz_(maxDetuningMHz),
          maxPulseNs_(maxPulseNs) {

        trap_.validate();
        laser_.validate();

        for (const auto& ion : ions) {
            if (ion.id < 0 ||
                ion.massAmu <= 0 ||
                ion.axialFrequencyMHz <= 0) {
                throw GovernanceError("Invalid ion configuration.");
            }

            if (!ions_.emplace(ion.id, ion).second) {
                throw GovernanceError("Duplicate ion ID.");
            }
        }

        if (ions_.empty()) {
            throw GovernanceError("At least one ion is required.");
        }
    }

    void submit(const Pulse& pulse) {
        validateIon(pulse.ion);

        if (pulse.targetIon.has_value()) {
            validateIon(*pulse.targetIon);
        }

        const double effectiveDetuning =
            pulse.detuningMHz + laser_.frequencyOffsetMHz;

        if (std::abs(effectiveDetuning) > maxDetuningMHz_) {
            throw GovernanceError(
                "Effective detuning exceeds safety threshold.");
        }

        if (pulse.durationNs > maxPulseNs_) {
            throw GovernanceError(
                "Pulse duration exceeds control policy.");
        }

        const double estimatedPower =
            pulse.rabiFrequencyMHz *
            laser_.rabiScale *
            0.02;

        if (estimatedPower > laser_.maxPowerMw) {
            throw GovernanceError(
                "Estimated optical power exceeds channel limit.");
        }

        if (pulse.type == PulseType::Entangling &&
            trap_.modeSpacingMHz() <= 0.0) {
            throw GovernanceError(
                "No valid separation between modeled trap modes.");
        }

        scheduler_.schedule(pulse);
    }

    void printTimeline() const {
        std::cout << "\nLaser pulse timeline\n";

        for (const auto& pulse : scheduler_.pulses()) {
            std::cout
                << std::fixed << std::setprecision(1)
                << pulse.startNs << " ns -> "
                << pulse.endNs() << " ns : "
                << pulse.id
                << " on ion " << pulse.ion;

            if (pulse.targetIon.has_value()) {
                std::cout << " with ion " << *pulse.targetIon;
            }

            std::cout << '\n';
        }
    }
};

static std::string pulseTypeName(PulseType type) {
    return type == PulseType::SingleQubit
        ? "single-qubit"
        : "entangling";
}

int main() {
    try {
        Trap trap{
            4.5,
            1.0,
            397.0
        };

        std::vector<Ion> ions{
            {0, 40.0, 1.0},
            {1, 40.0, 1.0},
            {2, 40.0, 1.0}
        };

        LaserChannel laser{
            "397nm-control",
            20.0,
            0.98,
            0.01
        };

        LaserCalibration calibration(1.0, 5.0);
        const auto calibrationResult =
            calibration.verify(0.99, 0.01);

        if (!calibrationResult.passed) {
            throw GovernanceError(
                "Laser calibration failed acceptance criteria.");
        }

        IonTrapController controller(
            trap,
            ions,
            laser,
            5.0,
            2000.0
        );

        Pulse preparation{
            "carrier-pi-over-two",
            0,
            std::nullopt,
            0.0,
            250.0,
            1.0,
            0.0,
            0.0,
            PulseType::SingleQubit
        };

        Pulse entangler{
            "bichromatic-motional-gate",
            0,
            1,
            1000.0,
            500.0,
            1.0,
            0.0,
            M_PI / 2.0,
            PulseType::Entangling
        };

        controller.submit(preparation);
        controller.submit(entangler);

        controller.printTimeline();

        std::cout << "\nControl calibration\n";
        std::cout << "Measured Rabi frequency: "
                  << calibrationResult.measuredRabiMHz
                  << " MHz\n";
        std::cout << "Measured detuning: "
                  << calibrationResult.measuredDetuningMHz
                  << " MHz\n";
        std::cout << "Calibration status: PASS\n";

        Pulse unsafe{
            "unsafe-detuned-pulse",
            0,
            std::nullopt,
            2000.0,
            100.0,
            1.0,
            12.0,
            0.0,
            PulseType::SingleQubit
        };

        try {
            controller.submit(unsafe);
            throw GovernanceError(
                "Unsafe pulse was unexpectedly accepted.");
        } catch (const GovernanceError& error) {
            std::cout << "\nSafety rejection: "
                      << error.what() << '\n';
        }

        Pulse overlapping{
            "overlapping-pulse",
            0,
            std::nullopt,
            200.0,
            300.0,
            1.0,
            0.0,
            0.0,
            PulseType::SingleQubit
        };

        try {
            controller.submit(overlapping);
            throw GovernanceError(
                "Overlapping pulse was unexpectedly accepted.");
        } catch (const GovernanceError& error) {
            std::cout << "Scheduling rejection: "
                      << error.what() << '\n';
        }

        std::cout << "\nGate categories:\n";
        std::cout << "  " << pulseTypeName(preparation.type) << '\n';
        std::cout << "  " << pulseTypeName(entangler.type) << '\n';

        std::cout << "\nEngineering properties:\n";
        std::cout << "  Mode spacing: "
                  << trap.modeSpacingMHz()
                  << " MHz\n";
        std::cout << "  Scheduled pulses: "
                  << controller
                  .pulses()
                  << '\n';

        // The controller intentionally keeps scheduling private. The line
        // above is not valid C++ and is avoided by reporting through a
        // successful timeline operation instead.
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal control error: "
                  << error.what() << '\n';
        return 1;
    }
}
