#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository-style circuit analysis is not required here: this program
 * models a practical DC distribution panel and evaluates electrical
 * operating conditions before producing a schematic representation.
 *
 * C++17 case study:
 * - DC distribution panel feeding several loads.
 * - Modified nodal analysis with ideal voltage sources.
 * - Branch-current and power calculations.
 * - Electrical safety limits and power-conservation checks.
 * - ASCII schematic generation.
 */

class CircuitError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

struct Resistor {
    std::string name;
    std::string a;
    std::string b;
    double ohms;

    Resistor(std::string name_, std::string a_, std::string b_, double ohms_)
        : name(std::move(name_)), a(std::move(a_)),
          b(std::move(b_)), ohms(ohms_) {
        if (name.empty() || a.empty() || b.empty() || a == b)
            throw CircuitError("Invalid resistor name or terminals.");
        if (!std::isfinite(ohms) || ohms <= 0.0)
            throw CircuitError(name + ": resistance must be positive.");
    }
};

struct VoltageSource {
    std::string name;
    std::string positive;
    std::string negative;
    double volts;

    VoltageSource(std::string name_, std::string p_, std::string n_, double v_)
        : name(std::move(name_)), positive(std::move(p_)),
          negative(std::move(n_)), volts(v_) {
        if (name.empty() || positive.empty() || negative.empty() ||
            positive == negative || !std::isfinite(volts)) {
            throw CircuitError("Invalid voltage source.");
        }
    }
};

struct BranchResult {
    std::string name;
    double voltage;
    double current;
    double power;
};

struct Analysis {
    std::map<std::string, double> nodeVoltages;
    std::vector<BranchResult> resistors;
    std::vector<BranchResult> sources;
    double resistorPower = 0.0;
    double sourcePower = 0.0;
};

class LinearSolver {
public:
    static std::vector<double> solve(
        std::vector<std::vector<double>> matrix,
        std::vector<double> rhs) {

        const std::size_t n = rhs.size();
        if (n == 0 || matrix.size() != n)
            throw CircuitError("Invalid linear system.");

        for (const auto& row : matrix) {
            if (row.size() != n)
                throw CircuitError("Matrix must be square.");
        }

        for (std::size_t column = 0; column < n; ++column) {
            std::size_t pivot = column;
            for (std::size_t row = column + 1; row < n; ++row) {
                if (std::abs(matrix[row][column]) >
                    std::abs(matrix[pivot][column])) {
                    pivot = row;
                }
            }

            if (std::abs(matrix[pivot][column]) < 1e-12)
                throw CircuitError("Singular matrix: circuit is not uniquely solvable.");

            std::swap(matrix[column], matrix[pivot]);
            std::swap(rhs[column], rhs[pivot]);

            const double divisor = matrix[column][column];
            for (std::size_t j = column; j < n; ++j)
                matrix[column][j] /= divisor;
            rhs[column] /= divisor;

            for (std::size_t row = 0; row < n; ++row) {
                if (row == column) continue;
                const double factor = matrix[row][column];
                for (std::size_t j = column; j < n; ++j)
                    matrix[row][j] -= factor * matrix[column][j];
                rhs[row] -= factor * rhs[column];
            }
        }

        for (double value : rhs) {
            if (!std::isfinite(value))
                throw CircuitError("Non-finite circuit solution.");
        }
        return rhs;
    }
};

class DistributionPanel {
private:
    std::string name_;
    std::string ground_;
    std::vector<Resistor> resistors_;
    std::vector<VoltageSource> sources_;
    std::set<std::string> componentNames_;

    std::vector<std::string> nodes() const {
        std::set<std::string> unique;
        for (const auto& r : resistors_) {
            unique.insert(r.a);
            unique.insert(r.b);
        }
        for (const auto& s : sources_) {
            unique.insert(s.positive);
            unique.insert(s.negative);
        }
        return {unique.begin(), unique.end()};
    }

    void claimName(const std::string& name) {
        if (!componentNames_.insert(name).second)
            throw CircuitError("Duplicate component: " + name);
    }

    void validateConnectivity() const {
        const auto allNodes = nodes();
        if (allNodes.empty())
            throw CircuitError("Panel has no electrical components.");

        if (!std::binary_search(allNodes.begin(), allNodes.end(), ground_))
            throw CircuitError("Reference node does not exist.");

        std::unordered_map<std::string, std::vector<std::string>> graph;
        for (const auto& r : resistors_) {
            graph[r.a].push_back(r.b);
            graph[r.b].push_back(r.a);
        }
        for (const auto& s : sources_) {
            graph[s.positive].push_back(s.negative);
            graph[s.negative].push_back(s.positive);
        }

        std::set<std::string> visited{ground_};
        std::vector<std::string> pending{ground_};

        while (!pending.empty()) {
            const std::string current = pending.back();
            pending.pop_back();
            for (const auto& next : graph[current]) {
                if (visited.insert(next).second)
                    pending.push_back(next);
            }
        }

        if (visited.size() != allNodes.size())
            throw CircuitError("At least one node is disconnected from ground.");
    }

public:
    explicit DistributionPanel(std::string name, std::string ground = "0")
        : name_(std::move(name)), ground_(std::move(ground)) {}

    void addResistor(const std::string& name, const std::string& a,
                     const std::string& b, double ohms) {
        Resistor component(name, a, b, ohms);
        claimName(name);
        resistors_.push_back(component);
    }

    void addVoltageSource(const std::string& name, const std::string& positive,
                          const std::string& negative, double volts) {
        VoltageSource component(name, positive, negative, volts);
        claimName(name);
        sources_.push_back(component);
    }

    Analysis analyze() const {
        validateConnectivity();

        std::vector<std::string> unknown;
        for (const auto& node : nodes()) {
            if (node != ground_) unknown.push_back(node);
        }

        std::unordered_map<std::string, std::size_t> index;
        for (std::size_t i = 0; i < unknown.size(); ++i)
            index[unknown[i]] = i;

        const std::size_t n = unknown.size();
        const std::size_t size = n + sources_.size();
        std::vector<std::vector<double>> matrix(
            size, std::vector<double>(size, 0.0));
        std::vector<double> rhs(size, 0.0);

        auto stamp = [&](const std::string& a, const std::string& b,
                         double conductance) {
            if (a != ground_) matrix[index.at(a)][index.at(a)] += conductance;
            if (b != ground_) matrix[index.at(b)][index.at(b)] += conductance;
            if (a != ground_ && b != ground_) {
                matrix[index.at(a)][index.at(b)] -= conductance;
                matrix[index.at(b)][index.at(a)] -= conductance;
            }
        };

        for (const auto& r : resistors_)
            stamp(r.a, r.b, 1.0 / r.ohms);

        for (std::size_t i = 0; i < sources_.size(); ++i) {
            const auto& source = sources_[i];
            const std::size_t sourceIndex = n + i;

            if (source.positive != ground_) {
                const auto p = index.at(source.positive);
                matrix[p][sourceIndex] += 1.0;
                matrix[sourceIndex][p] += 1.0;
            }
            if (source.negative != ground_) {
                const auto m = index.at(source.negative);
                matrix[m][sourceIndex] -= 1.0;
                matrix[sourceIndex][m] -= 1.0;
            }
            rhs[sourceIndex] = source.volts;
        }

        const auto solution = LinearSolver::solve(matrix, rhs);
        Analysis result;
        result.nodeVoltages[ground_] = 0.0;

        for (std::size_t i = 0; i < n; ++i)
            result.nodeVoltages[unknown[i]] = solution[i];

        for (const auto& r : resistors_) {
            const double voltage =
                result.nodeVoltages.at(r.a) - result.nodeVoltages.at(r.b);
            const double current = voltage / r.ohms;
            const double power = voltage * current;
            result.resistors.push_back({r.name, voltage, current, power});
            result.resistorPower += power;
        }

        for (std::size_t i = 0; i < sources_.size(); ++i) {
            const auto& s = sources_[i];
            const double current = solution[n + i];
            const double power = s.volts * current;
            result.sources.push_back({s.name, s.volts, current, power});
            result.sourcePower += power;
        }

        const double scale = std::max(1.0, std::abs(result.resistorPower));
        if (std::abs(result.resistorPower + result.sourcePower) > 1e-7 * scale)
            throw CircuitError("Power balance does not satisfy conservation.");

        return result;
    }

    void drawAscii(const Analysis& result) const {
        std::cout << "\nSCHEMATIC: " << name_ << "\n";
        std::cout << "Reference node: " << ground_ << "\n";
        std::cout << "------------------------------------------------\n";

        for (const auto& s : sources_) {
            std::cout << "[" << s.name << " " << s.volts << " V] "
                      << s.positive << " ---- " << s.negative << "\n";
        }
        for (const auto& r : resistors_) {
            std::cout << r.a << " ----[ " << r.name << " "
                      << r.ohms << " ohm ]---- " << r.b << "\n";
        }

        std::cout << "\nNode voltage report\n";
        for (const auto& [node, voltage] : result.nodeVoltages) {
            std::cout << std::setw(12) << node << " : "
                      << std::fixed << std::setprecision(4)
                      << voltage << " V\n";
        }
    }
};

class SafetyMonitor {
public:
    static void inspect(const Analysis& result, double maximumCurrent,
                        double maximumPower) {
        std::cout << "\nElectrical operating limits\n";

        for (const auto& branch : result.resistors) {
            const bool currentExceeded =
                std::abs(branch.current) > maximumCurrent;
            const bool powerExceeded = branch.power > maximumPower;

            std::cout << branch.name << ": ";
            if (currentExceeded || powerExceeded) {
                std::cout << "LIMIT EXCEEDED";
                if (currentExceeded) std::cout << " [current]";
                if (powerExceeded) std::cout << " [power]";
            } else {
                std::cout << "within configured limits";
            }
            std::cout << "\n";
        }
    }
};

int main() {
    try {
        DistributionPanel panel("24 V Industrial Sensor Distribution");

        panel.addVoltageSource("PS1", "bus_24v", "0", 24.0);
        panel.addResistor("R_LINE", "bus_24v", "sensor_bus", 2.0);
        panel.addResistor("R_SENSOR_A", "sensor_bus", "0", 120.0);
        panel.addResistor("R_SENSOR_B", "sensor_bus", "0", 240.0);
        panel.addResistor("R_INDICATOR", "sensor_bus", "0", 1000.0);

        const Analysis result = panel.analyze();
        panel.drawAscii(result);

        std::cout << "\nBranch electrical measurements\n";
        for (const auto& branch : result.resistors) {
            std::cout << std::setw(16) << branch.name
                      << " | V=" << std::setw(9) << branch.voltage
                      << " V | I=" << std::setw(9) << branch.current
                      << " A | P=" << std::setw(9) << branch.power << " W\n";
        }

        std::cout << "\nPower balance\n"
                  << "Resistor dissipation: " << result.resistorPower << " W\n"
                  << "Source power: " << result.sourcePower << " W\n";

        SafetyMonitor::inspect(result, 1.0, 5.0);

        std::cout << "\nThe numerical model represents ideal DC components. "
                     "Physical designs require component tolerances, thermal "
                     "derating, transient analysis, and independent safety review.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Circuit analysis failed: " << error.what() << "\n";
        return 1;
    }
}
