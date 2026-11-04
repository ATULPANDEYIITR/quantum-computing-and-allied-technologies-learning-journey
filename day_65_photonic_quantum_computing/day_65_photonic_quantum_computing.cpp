#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Complex = std::complex<double>;

constexpr double EPSILON = 1e-9;
constexpr double PI = 3.14159265358979323846;

enum class Polarization {
    Horizontal,
    Vertical
};

enum class GateType {
    PauliX,
    PauliZ,
    Hadamard,
    PhaseShift
};

class QuantumError : public std::runtime_error {
public:
    explicit QuantumError(const std::string& message)
        : std::runtime_error(message) {}
};

struct PhotonState {
    Complex alpha;
    Complex beta;

    PhotonState(Complex a, Complex b)
        : alpha(a), beta(b) {

        const double norm =
            std::norm(alpha) + std::norm(beta);

        if (!std::isfinite(norm) ||
            std::abs(norm - 1.0) > EPSILON) {
            throw QuantumError(
                "Photon state must be normalized."
            );
        }
    }

    double probabilityH() const {
        return std::norm(alpha);
    }

    double probabilityV() const {
        return std::norm(beta);
    }

    void display() const {
        std::cout
            << "|psi> = ("
            << alpha
            << ")|H> + ("
            << beta
            << ")|V>\n";
    }
};

class PhotonSource {
public:
    static PhotonState horizontal() {
        return PhotonState(1.0, 0.0);
    }

    static PhotonState vertical() {
        return PhotonState(0.0, 1.0);
    }

    static PhotonState diagonal() {
        const double s = 1.0 / std::sqrt(2.0);

        return PhotonState(s, s);
    }

    static PhotonState circular() {
        const double s = 1.0 / std::sqrt(2.0);

        return PhotonState(
            Complex(s, 0),
            Complex(0, s)
        );
    }
};

class QuantumGate {
public:
    using Matrix = std::array<
        std::array<Complex, 2>,
        2
    >;

    static PhotonState apply(
        const PhotonState& state,
        const Matrix& matrix
    ) {
        Complex a =
            matrix[0][0] * state.alpha +
            matrix[0][1] * state.beta;

        Complex b =
            matrix[1][0] * state.alpha +
            matrix[1][1] * state.beta;

        return PhotonState(a, b);
    }

    static PhotonState apply(
        const PhotonState& state,
        GateType gate,
        double phase = 0.0
    ) {
        switch (gate) {
            case GateType::PauliX:
                return apply(
                    state,
                    {{
                        {{0.0, 1.0}},
                        {{1.0, 0.0}}
                    }}
                );

            case GateType::PauliZ:
                return apply(
                    state,
                    {{
                        {{1.0, 0.0}},
                        {{0.0, -1.0}}
                    }}
                );

            case GateType::Hadamard: {
                const double s = 1.0 / std::sqrt(2.0);

                return apply(
                    state,
                    {{
                        {{s, s}},
                        {{s, -s}}
                    }}
                );
            }

            case GateType::PhaseShift:
                if (!std::isfinite(phase)) {
                    throw QuantumError("Invalid phase.");
                }

                return apply(
                    state,
                    {{
                        {{1.0, 0.0}},
                        {{0.0, std::exp(Complex(0, phase))}}
                    }}
                );
        }

        throw QuantumError("Unknown quantum gate.");
    }
};

struct Measurement {
    Polarization outcome;
    double probability;
};

class PolarizationAnalyzer {
private:
    std::mt19937_64 generator;
    std::uniform_real_distribution<double> distribution;

public:
    explicit PolarizationAnalyzer(
        std::uint64_t seed = 42
    )
        : generator(seed),
          distribution(0.0, 1.0) {}

    Measurement measure(const PhotonState& state) {
        const double pH = state.probabilityH();

        if (distribution(generator) < pH) {
            return {
                Polarization::Horizontal,
                pH
            };
        }

        return {
            Polarization::Vertical,
            1.0 - pH
        };
    }
};

struct BeamSplitterOutput {
    Complex reflected;
    Complex transmitted;

    double reflectionProbability() const {
        return std::norm(reflected);
    }

    double transmissionProbability() const {
        return std::norm(transmitted);
    }
};

class BeamSplitter {
public:
    static BeamSplitterOutput split(
        double reflectivity
    ) {
        if (
            !std::isfinite(reflectivity) ||
            reflectivity < 0.0 ||
            reflectivity > 1.0
        ) {
            throw QuantumError(
                "Reflectivity must be between zero and one."
            );
        }

        return {
            Complex(0, std::sqrt(reflectivity)),
            std::sqrt(1.0 - reflectivity)
        };
    }
};

class OpticalChannel {
private:
    double transmission;
    double detectorEfficiency;

public:
    OpticalChannel(
        double transmission,
        double detectorEfficiency
    )
        : transmission(transmission),
          detectorEfficiency(detectorEfficiency) {

        auto valid = [](double value) {
            return std::isfinite(value) &&
                   value >= 0.0 &&
                   value <= 1.0;
        };

        if (!valid(transmission) ||
            !valid(detectorEfficiency)) {
            throw QuantumError(
                "Invalid channel efficiency."
            );
        }
    }

    double detectionProbability() const {
        return transmission * detectorEfficiency;
    }
};

class HongOuMandelExperiment {
public:
    static double coincidenceProbability(
        double overlap,
        double reflectivity
    ) {
        if (
            !std::isfinite(overlap) ||
            overlap < 0.0 ||
            overlap > 1.0 ||
            !std::isfinite(reflectivity) ||
            reflectivity < 0.0 ||
            reflectivity > 1.0
        ) {
            throw QuantumError(
                "Invalid interference parameters."
            );
        }

        return 4.0 *
               reflectivity *
               (1.0 - reflectivity) *
               (1.0 - overlap);
    }

    static double bunchingProbability(
        double overlap,
        double reflectivity
    ) {
        return 1.0 -
               coincidenceProbability(
                   overlap,
                   reflectivity
               );
    }
};

struct ExperimentalReport {
    std::size_t shots = 0;
    std::size_t detected = 0;
    std::size_t lost = 0;
    std::size_t horizontal = 0;
    std::size_t vertical = 0;

    double detectionRate() const {
        return shots == 0
            ? 0.0
            : static_cast<double>(detected) / shots;
    }

    double horizontalFraction() const {
        return detected == 0
            ? 0.0
            : static_cast<double>(horizontal) / detected;
    }
};

class PhotonicExperiment {
private:
    PhotonState state;
    OpticalChannel channel;
    std::mt19937_64 generator;
    std::uniform_real_distribution<double> distribution;
    PolarizationAnalyzer analyzer;

public:
    PhotonicExperiment(
        PhotonState state,
        OpticalChannel channel,
        std::uint64_t seed
    )
        : state(std::move(state)),
          channel(std::move(channel)),
          generator(seed),
          distribution(0.0, 1.0),
          analyzer(seed + 1) {}

    ExperimentalReport run(std::size_t shots) {
        if (shots == 0) {
            throw QuantumError(
                "Experiment requires at least one shot."
            );
        }

        ExperimentalReport report;
        report.shots = shots;

        for (std::size_t i = 0; i < shots; ++i) {
            const bool detected =
                distribution(generator) <
                channel.detectionProbability();

            if (!detected) {
                report.lost++;
                continue;
            }

            report.detected++;

            const Measurement result =
                analyzer.measure(state);

            if (
                result.outcome ==
                Polarization::Horizontal
            ) {
                report.horizontal++;
            } else {
                report.vertical++;
            }
        }

        return report;
    }
};

class PhotonicCircuit {
private:
    std::vector<GateType> gates;

public:
    void add(GateType gate) {
        gates.push_back(gate);
    }

    PhotonState execute(
        PhotonState initial,
        double phase = 0.0
    ) const {
        for (const auto gate : gates) {
            initial = QuantumGate::apply(
                initial,
                gate,
                phase
            );
        }

        return initial;
    }

    std::size_t size() const {
        return gates.size();
    }
};

void validate() {
    const auto h = PhotonSource::horizontal();
    const auto v = PhotonSource::vertical();

    const auto flipped = QuantumGate::apply(
        h,
        GateType::PauliX
    );

    if (
        std::abs(flipped.probabilityV() - 1.0)
        > EPSILON
    ) {
        throw QuantumError("Pauli-X validation failed.");
    }

    const auto diagonal = QuantumGate::apply(
        h,
        GateType::Hadamard
    );

    if (
        std::abs(diagonal.probabilityH() - 0.5)
        > EPSILON
    ) {
        throw QuantumError("Hadamard validation failed.");
    }

    const auto split = BeamSplitter::split(0.5);

    if (
        std::abs(
            split.reflectionProbability() +
            split.transmissionProbability() -
            1.0
        ) > EPSILON
    ) {
        throw QuantumError("Beam splitter validation failed.");
    }

    if (
        HongOuMandelExperiment::coincidenceProbability(
            1.0,
            0.5
        ) > EPSILON
    ) {
        throw QuantumError("Interference validation failed.");
    }

    if (
        std::abs(
            h.probabilityH() +
            h.probabilityV() - 1.0
        ) > EPSILON
    ) {
        throw QuantumError("Normalization validation failed.");
    }

    (void)v;
}

void demonstrate() {
    std::cout
        << std::fixed
        << std::setprecision(4);

    std::cout
        << "PHOTONIC QUANTUM COMPUTING\n"
        << "==========================\n";

    const auto initial = PhotonSource::horizontal();

    std::cout << "\nInitial photon:\n";
    initial.display();

    PhotonicCircuit circuit;

    circuit.add(GateType::Hadamard);
    circuit.add(GateType::PhaseShift);
    circuit.add(GateType::PauliX);

    const auto output = circuit.execute(
        initial,
        PI / 2.0
    );

    std::cout << "\nCircuit output:\n";
    output.display();

    std::cout
        << "P(H): "
        << output.probabilityH()
        << "\nP(V): "
        << output.probabilityV()
        << "\n";

    const auto splitter = BeamSplitter::split(0.5);

    std::cout << "\nBalanced beam splitter:\n";
    std::cout
        << "Reflection: "
        << splitter.reflectionProbability()
        << "\nTransmission: "
        << splitter.transmissionProbability()
        << "\n";

    std::cout << "\nHong-Ou-Mandel interference:\n";

    for (double overlap : {0.0, 0.5, 1.0}) {
        std::cout
            << "Overlap=" << overlap
            << ", coincidence="
            << HongOuMandelExperiment::coincidenceProbability(
                overlap,
                0.5
            )
            << "\n";
    }

    OpticalChannel channel(0.85, 0.90);

    PhotonicExperiment experiment(
        PhotonSource::diagonal(),
        channel,
        2026
    );

    const auto report = experiment.run(10000);

    std::cout << "\nExperiment report:\n";
    std::cout << "Shots: " << report.shots << "\n";
    std::cout << "Detected: " << report.detected << "\n";
    std::cout << "Lost: " << report.lost << "\n";
    std::cout
        << "Detection rate: "
        << report.detectionRate()
        << "\n";
    std::cout
        << "Horizontal fraction: "
        << report.horizontalFraction()
        << "\n";

    if (
        report.detected + report.lost != report.shots ||
        report.horizontal + report.vertical != report.detected
    ) {
        throw QuantumError(
            "Experimental accounting inconsistency."
        );
    }
}

int main() {
    try {
        validate();
        std::cout << "All C++17 validation checks passed.\n";
        demonstrate();
    } catch (const std::exception& error) {
        std::cerr
            << "Execution failed: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
