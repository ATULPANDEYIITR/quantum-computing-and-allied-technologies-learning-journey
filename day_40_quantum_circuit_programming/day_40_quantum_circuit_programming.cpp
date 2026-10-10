#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
#include <algorithm>

using Complex = std::complex<double>;
using Matrix = std::vector<std::vector<Complex>>;

constexpr double PI = 3.14159265358979323846;

Matrix identityMatrix(std::size_t n) {
    Matrix result(n, std::vector<Complex>(n, 0.0));
    for (std::size_t i = 0; i < n; ++i) result[i][i] = 1.0;
    return result;
}

Matrix multiply(const Matrix& a, const Matrix& b) {
    if (a.empty() || b.empty() || a.front().size() != b.size())
        throw std::invalid_argument("Incompatible matrix dimensions");

    Matrix result(a.size(), std::vector<Complex>(b.front().size(), 0.0));
    for (std::size_t i = 0; i < a.size(); ++i)
        for (std::size_t k = 0; k < b.size(); ++k)
            for (std::size_t j = 0; j < b.front().size(); ++j)
                result[i][j] += a[i][k] * b[k][j];
    return result;
}

void validateUnitary(const Matrix& gate, double tolerance = 1e-9) {
    if (gate.empty()) throw std::invalid_argument("Empty gate matrix");
    for (const auto& row : gate)
        if (row.size() != gate.size())
            throw std::invalid_argument("Gate matrix must be square");

    Matrix conjugateTranspose(gate.size(), std::vector<Complex>(gate.size()));
    for (std::size_t i = 0; i < gate.size(); ++i)
        for (std::size_t j = 0; j < gate.size(); ++j)
            conjugateTranspose[i][j] = std::conj(gate[j][i]);

    Matrix product = multiply(conjugateTranspose, gate);
    for (std::size_t i = 0; i < gate.size(); ++i)
        for (std::size_t j = 0; j < gate.size(); ++j) {
            Complex expected = i == j ? Complex(1.0, 0.0) : Complex(0.0, 0.0);
            if (std::abs(product[i][j] - expected) > tolerance)
                throw std::invalid_argument("Gate is not unitary");
        }
}

struct Operation {
    std::string name;
    std::vector<int> targets;
    std::vector<int> controls;
    Matrix matrix;
};

class StateVectorSimulator {
private:
    int qubits;
    std::vector<Complex> state;
    std::vector<Operation> operations;
    std::mt19937_64 generator;

    void checkQubit(int q) const {
        if (q < 0 || q >= qubits)
            throw std::out_of_range("Qubit index outside circuit");
    }

    void apply(const Operation& op) {
        const std::size_t dimension = state.size();
        std::size_t targetMask = 0, controlMask = 0;

        for (int q : op.targets) targetMask |= std::size_t(1) << q;
        for (int q : op.controls) controlMask |= std::size_t(1) << q;

        const std::size_t localDimension = std::size_t(1) << op.targets.size();
        std::vector<Complex> output = state;

        // Transform local amplitude blocks rather than constructing a dense
        // full-system matrix, which would require O(4^n) matrix storage.
        for (std::size_t base = 0; base < dimension; ++base) {
            if ((base & targetMask) != 0) continue;
            if ((base & controlMask) != controlMask) continue;

            std::vector<std::size_t> indices(localDimension);
            for (std::size_t local = 0; local < localDimension; ++local) {
                std::size_t index = base;
                for (std::size_t position = 0; position < op.targets.size(); ++position)
                    if (local & (std::size_t(1) << position))
                        index |= std::size_t(1) << op.targets[position];
                indices[local] = index;
            }

            std::vector<Complex> old(localDimension);
            for (std::size_t j = 0; j < localDimension; ++j)
                old[j] = state[indices[j]];

            for (std::size_t row = 0; row < localDimension; ++row) {
                Complex value = 0.0;
                for (std::size_t column = 0; column < localDimension; ++column)
                    value += op.matrix[row][column] * old[column];
                output[indices[row]] = value;
            }
        }
        state.swap(output);
    }

public:
    explicit StateVectorSimulator(int n, std::uint64_t seed = 2026)
        : qubits(n), generator(seed) {
        if (n < 1 || n > 20)
            throw std::invalid_argument("Qubit count must be between 1 and 20");
        state.assign(std::size_t(1) << n, Complex(0.0, 0.0));
        state[0] = 1.0;
    }

    void addGate(const std::string& name, std::vector<int> targets,
                 const Matrix& matrix, std::vector<int> controls = {}) {
        if (targets.empty()) throw std::invalid_argument("Gate requires target qubits");
        std::vector<int> all = targets;
        all.insert(all.end(), controls.begin(), controls.end());

        std::sort(all.begin(), all.end());
        if (std::adjacent_find(all.begin(), all.end()) != all.end())
            throw std::invalid_argument("Qubit cannot be repeated or be both control and target");

        for (int q : all) checkQubit(q);

        const std::size_t expected = std::size_t(1) << targets.size();
        if (matrix.size() != expected)
            throw std::invalid_argument("Gate dimension does not match targets");
        validateUnitary(matrix);
        operations.push_back({name, std::move(targets), std::move(controls), matrix});
    }

    void h(int q) {
        const double s = 1.0 / std::sqrt(2.0);
        addGate("H", {q}, {{s, s}, {s, -s}});
    }

    void x(int q) {
        addGate("X", {q}, {{0.0, 1.0}, {1.0, 0.0}});
    }

    void z(int q) {
        addGate("Z", {q}, {{1.0, 0.0}, {0.0, -1.0}});
    }

    void cnot(int control, int target) {
        addGate("CNOT", {target}, {{0.0, 1.0}, {1.0, 0.0}}, {control});
    }

    void ry(int q, double theta) {
        double c = std::cos(theta / 2.0);
        double s = std::sin(theta / 2.0);
        addGate("RY", {q}, {{c, -s}, {s, c}});
    }

    void execute() {
        for (const auto& op : operations) apply(op);
        double norm = 0.0;
        for (Complex amplitude : state) norm += std::norm(amplitude);
        if (std::abs(norm - 1.0) > 1e-8)
            throw std::runtime_error("State normalization invariant violated");
    }

    std::vector<double> probabilities() {
        execute();
        std::vector<double> result(state.size());
        for (std::size_t i = 0; i < state.size(); ++i)
            result[i] = std::norm(state[i]);
        return result;
    }

    std::unordered_map<std::string, int> sample(int shots) {
        if (shots <= 0) throw std::invalid_argument("Shots must be positive");
        auto p = probabilities();
        std::discrete_distribution<std::size_t> distribution(p.begin(), p.end());
        std::unordered_map<std::string, int> counts;

        for (int shot = 0; shot < shots; ++shot) {
            std::size_t index = distribution(generator);
            std::string bits;
            for (int q = 0; q < qubits; ++q)
                bits.push_back((index & (std::size_t(1) << q)) ? '1' : '0');
            counts[bits]++;
        }
        return counts;
    }

    void printState() {
        execute();
        std::cout << std::fixed << std::setprecision(5);
        for (std::size_t i = 0; i < state.size(); ++i) {
            if (std::abs(state[i]) > 1e-10) {
                std::string bits;
                for (int q = 0; q < qubits; ++q)
                    bits.push_back((i & (std::size_t(1) << q)) ? '1' : '0');
                std::cout << "|" << bits << "> : " << state[i] << '\n';
            }
        }
    }
};

struct Calibration {
    double readoutError;
    double gateError;
};

class QuantumExperiment {
private:
    Calibration calibration;

public:
    explicit QuantumExperiment(Calibration c) : calibration(c) {
        if (c.readoutError < 0 || c.readoutError > 1 ||
            c.gateError < 0 || c.gateError > 1)
            throw std::invalid_argument("Error rates must lie between zero and one");
    }

    void reportIdealAndNoisy(const std::unordered_map<std::string, int>& ideal,
                             int shots, std::uint64_t seed = 77) const {
        if (shots <= 0) throw std::invalid_argument("Shots must be positive");
        std::mt19937_64 rng(seed);
        std::bernoulli_distribution readout(calibration.readoutError);
        std::bernoulli_distribution gate(calibration.gateError);

        auto noisy = ideal;
        for (auto& [bits, count] : noisy) {
            int flips = 0;
            for (int i = 0; i < count; ++i) {
                if (gate(rng)) ++flips;
                if (readout(rng)) ++flips;
            }
            // This aggregate illustration reports error events, not a full
            // physical noise channel or hardware-calibrated prediction.
            std::cout << "Outcome " << bits << ": ideal shots=" << count
                      << ", simulated error events=" << flips << '\n';
        }
    }
};

int main() {
    try {
        std::cout << "Bell-state circuit\n";
        StateVectorSimulator bell(2, 17);
        bell.h(0);
        bell.cnot(0, 1);
        bell.printState();

        const auto counts = bell.sample(2000);
        std::cout << "\nMeasured outcomes\n";
        for (const auto& [bits, count] : counts)
            std::cout << bits << ": " << count << '\n';

        std::cout << "\nParameterized rotation\n";
        StateVectorSimulator rotation(1);
        rotation.ry(0, PI / 3.0);
        rotation.printState();

        auto rotationProbabilities = rotation.probabilities();
        if (std::abs(rotationProbabilities[1] - 0.25) > 1e-9)
            throw std::runtime_error("RY probability check failed");

        std::cout << "\nIllustrative noise-event report\n";
        QuantumExperiment experiment({0.02, 0.01});
        experiment.reportIdealAndNoisy(counts, 2000);

        std::cout << "\nAll circuit invariants passed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Quantum simulation error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
