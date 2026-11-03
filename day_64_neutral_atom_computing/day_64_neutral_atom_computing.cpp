#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Neutral-atom array planning using C++17.
 *
 * The program evaluates Gaussian tweezer characteristics, estimates
 * neighboring-beam intensity-envelope tails, and constructs an atom-to-target
 * assignment using minimum-cost maximum flow.
 *
 * The flow objective minimizes total squared grid displacement. It is a
 * planning objective, not a model of a physical transport trajectory.
 */

namespace physics {
constexpr double PI = 3.14159265358979323846;
constexpr double BOLTZMANN = 1.380649e-23;
constexpr double RUBIDIUM_87_MASS = 1.44316060e-25;
}

struct Point {
    double xUm{};
    double yUm{};

    double distanceTo(const Point& other) const {
        return std::hypot(xUm - other.xUm, yUm - other.yUm);
    }
};

struct TrapCalibration {
    double wavelengthM{};
    double waistM{};
    double depthJ{};
    double atomicMassKg{physics::RUBIDIUM_87_MASS};

    void validate() const {
        const double values[] = {
            wavelengthM, waistM, depthJ, atomicMassKg
        };

        for (double value : values) {
            if (!std::isfinite(value) || value <= 0.0) {
                throw std::invalid_argument(
                    "Trap calibration values must be positive and finite."
                );
            }
        }
    }

    double rayleighRangeM() const {
        return physics::PI * waistM * waistM / wavelengthM;
    }

    double radialFrequencyHz() const {
        const double omega = std::sqrt(
            4.0 * depthJ / (atomicMassKg * waistM * waistM)
        );
        return omega / (2.0 * physics::PI);
    }

    double axialFrequencyHz() const {
        const double zRayleigh = rayleighRangeM();
        const double omega = std::sqrt(
            2.0 * depthJ / (atomicMassKg * zRayleigh * zRayleigh)
        );
        return omega / (2.0 * physics::PI);
    }

    double potentialJ(double radialDistanceM, double axialDistanceM = 0.0) const {
        if (!std::isfinite(radialDistanceM) || radialDistanceM < 0.0 ||
            !std::isfinite(axialDistanceM)) {
            throw std::invalid_argument("Invalid trap evaluation coordinates.");
        }

        const double zRatio = axialDistanceM / rayleighRangeM();
        const double beamRadius = waistM * std::sqrt(1.0 + zRatio * zRatio);
        const double localDepth =
            depthJ / (1.0 + zRatio * zRatio) *
            std::exp(
                -2.0 * radialDistanceM * radialDistanceM /
                (beamRadius * beamRadius)
            );

        return -localDepth;
    }
};

struct Site {
    int id{};
    int row{};
    int column{};
    Point position;
};

struct Atom {
    int id{};
    int sourceSiteId{};
    Point position;
};

struct Target {
    int id{};
    Point position;
};

struct Move {
    int atomId{};
    int sourceSiteId{};
    int targetId{};
    double distanceUm{};
};

class TweezerArray {
public:
    TweezerArray(
        int rows,
        int columns,
        double spacingUm,
        TrapCalibration calibration
    ) : rows_(rows),
        columns_(columns),
        spacingUm_(spacingUm),
        calibration_(std::move(calibration)) {

        calibration_.validate();

        if (rows_ <= 0 || columns_ <= 0 ||
            !std::isfinite(spacingUm_) || spacingUm_ <= 0.0) {
            throw std::invalid_argument("Invalid tweezer array geometry.");
        }

        int nextId = 0;
        for (int row = 0; row < rows_; ++row) {
            for (int column = 0; column < columns_; ++column) {
                sites_.push_back({
                    nextId++,
                    row,
                    column,
                    {
                        column * spacingUm_,
                        row * spacingUm_
                    }
                });
            }
        }
    }

    const std::vector<Site>& sites() const {
        return sites_;
    }

    const TrapCalibration& calibration() const {
        return calibration_;
    }

    double maximumGaussianTailFraction() const {
        double maximum = 0.0;
        const double waistUm = calibration_.waistM * 1e6;

        for (const Site& center : sites_) {
            double tailSum = 0.0;

            for (const Site& other : sites_) {
                if (center.id == other.id) {
                    continue;
                }

                const double distance = center.position.distanceTo(other.position);
                tailSum += std::exp(
                    -2.0 * distance * distance / (waistUm * waistUm)
                );
            }

            maximum = std::max(maximum, tailSum);
        }

        return maximum;
    }

private:
    int rows_;
    int columns_;
    double spacingUm_;
    TrapCalibration calibration_;
    std::vector<Site> sites_;
};

class MinimumCostFlow {
public:
    struct Edge {
        int to;
        int reverseIndex;
        int capacity;
        long long cost;
    };

    struct Result {
        int flow;
        long long cost;
    };

    explicit MinimumCostFlow(int vertexCount)
        : graph_(static_cast<std::size_t>(vertexCount)) {
        if (vertexCount <= 0) {
            throw std::invalid_argument("Flow graph must contain vertices.");
        }
    }

    int addEdge(int from, int to, int capacity, long long cost) {
        if (from < 0 || to < 0 ||
            from >= static_cast<int>(graph_.size()) ||
            to >= static_cast<int>(graph_.size()) ||
            capacity < 0 || cost < 0) {
            throw std::invalid_argument("Invalid flow edge.");
        }

        const int forwardIndex = static_cast<int>(graph_[from].size());
        const int reverseIndex = static_cast<int>(graph_[to].size());

        graph_[from].push_back({
            to, reverseIndex, capacity, cost
        });
        graph_[to].push_back({
            from, forwardIndex, 0, -cost
        });

        return forwardIndex;
    }

    const std::vector<Edge>& edgesFrom(int vertex) const {
        return graph_.at(static_cast<std::size_t>(vertex));
    }

    Result solve(int source, int sink, int requestedFlow) {
        const int vertexCount = static_cast<int>(graph_.size());

        if (source < 0 || sink < 0 ||
            source >= vertexCount || sink >= vertexCount ||
            requestedFlow < 0) {
            throw std::invalid_argument("Invalid flow request.");
        }

        constexpr long long INF = std::numeric_limits<long long>::max() / 4;

        std::vector<long long> potential(vertexCount, 0);
        std::vector<long long> distance(vertexCount);
        std::vector<int> parentVertex(vertexCount);
        std::vector<int> parentEdge(vertexCount);

        int totalFlow = 0;
        long long totalCost = 0;

        using QueueNode = std::pair<long long, int>;

        while (totalFlow < requestedFlow) {
            std::fill(distance.begin(), distance.end(), INF);
            std::fill(parentVertex.begin(), parentVertex.end(), -1);
            std::fill(parentEdge.begin(), parentEdge.end(), -1);

            std::priority_queue<
                QueueNode,
                std::vector<QueueNode>,
                std::greater<QueueNode>
            > queue;

            distance[source] = 0;
            queue.push({0, source});

            // Potentials keep residual reduced costs non-negative.
            while (!queue.empty()) {
                const auto [currentDistance, vertex] = queue.top();
                queue.pop();

                if (currentDistance != distance[vertex]) {
                    continue;
                }

                for (int edgeIndex = 0;
                     edgeIndex < static_cast<int>(graph_[vertex].size());
                     ++edgeIndex) {
                    const Edge& edge = graph_[vertex][edgeIndex];

                    if (edge.capacity <= 0) {
                        continue;
                    }

                    const long long reducedCost =
                        edge.cost + potential[vertex] - potential[edge.to];

                    if (reducedCost < 0) {
                        throw std::logic_error(
                            "Negative reduced cost violates flow invariant."
                        );
                    }

                    if (distance[vertex] > INF - reducedCost) {
                        continue;
                    }

                    const long long candidate =
                        distance[vertex] + reducedCost;

                    if (candidate < distance[edge.to]) {
                        distance[edge.to] = candidate;
                        parentVertex[edge.to] = vertex;
                        parentEdge[edge.to] = edgeIndex;
                        queue.push({candidate, edge.to});
                    }
                }
            }

            if (parentVertex[sink] == -1) {
                break;
            }

            for (int vertex = 0; vertex < vertexCount; ++vertex) {
                if (distance[vertex] < INF) {
                    potential[vertex] += distance[vertex];
                }
            }

            int augmentation = requestedFlow - totalFlow;
            for (int vertex = sink; vertex != source;
                 vertex = parentVertex[vertex]) {
                const Edge& edge =
                    graph_[parentVertex[vertex]][parentEdge[vertex]];
                augmentation = std::min(augmentation, edge.capacity);
            }

            for (int vertex = sink; vertex != source;
                 vertex = parentVertex[vertex]) {
                Edge& edge =
                    graph_[parentVertex[vertex]][parentEdge[vertex]];

                edge.capacity -= augmentation;
                graph_[vertex][edge.reverseIndex].capacity += augmentation;
                totalCost += static_cast<long long>(augmentation) * edge.cost;
            }

            totalFlow += augmentation;
        }

        return {totalFlow, totalCost};
    }

private:
    std::vector<std::vector<Edge>> graph_;
};

struct EdgeReference {
    int atomIndex;
    int targetIndex;
    int graphEdgeIndex;
};

std::vector<Move> planMinimumCostMoves(
    const std::vector<Atom>& atoms,
    const std::vector<Target>& targets,
    long long& optimizationCost
) {
    if (atoms.empty() || targets.empty()) {
        throw std::invalid_argument(
            "Atom rearrangement needs at least one atom and one target."
        );
    }

    const int atomCount = static_cast<int>(atoms.size());
    const int targetCount = static_cast<int>(targets.size());

    const int source = 0;
    const int atomStart = 1;
    const int targetStart = atomStart + atomCount;
    const int sink = targetStart + targetCount;

    MinimumCostFlow flow(sink + 1);
    std::vector<EdgeReference> references;

    for (int atom = 0; atom < atomCount; ++atom) {
        flow.addEdge(source, atomStart + atom, 1, 0);
    }

    for (int target = 0; target < targetCount; ++target) {
        flow.addEdge(targetStart + target, sink, 1, 0);
    }

    /*
     * Coordinates are stored in half-spacing units. An atom at grid index
     * (r,c) is at (2c,2r); a centered target is at an odd half-grid position.
     * Squared integer displacement makes the objective exact in these units.
     */
    std::vector<EdgeReference> edgeReferences;

    for (int atom = 0; atom < atomCount; ++atom) {
        for (int target = 0; target < targetCount; ++target) {
            // Convert micrometers to half-spacing units for the objective.
            const double dx = atoms[atom].position.xUm - targets[target].position.xUm;
            const double dy = atoms[atom].position.yUm - targets[target].position.yUm;

            // The demo uses a 5 um spacing, so one half-spacing unit is 2.5 um.
            const long long dxUnits = std::llround(dx / 2.5);
            const long long dyUnits = std::llround(dy / 2.5);
            const long long squaredCost =
                dxUnits * dxUnits + dyUnits * dyUnits;

            const int edgeIndex = flow.addEdge(
                atomStart + atom,
                targetStart + target,
                1,
                squaredCost
            );

            edgeReferences.push_back({atom, target, edgeIndex});
        }
    }

    const int desiredFlow = std::min(atomCount, targetCount);
    const auto result = flow.solve(source, sink, desiredFlow);
    optimizationCost = result.cost;

    if (result.flow != desiredFlow) {
        throw std::runtime_error(
            "The assignment network could not match the available atoms."
        );
    }

    std::vector<Move> moves;

    for (const EdgeReference& reference : edgeReferences) {
        const int vertex = atomStart + reference.atomIndex;
        const auto& edge = flow.edgesFrom(vertex).at(
            static_cast<std::size_t>(reference.graphEdgeIndex)
        );

        if (edge.capacity == 0) {
            const Atom& atom = atoms[reference.atomIndex];
            const Target& target = targets[reference.targetIndex];

            moves.push_back({
                atom.id,
                atom.sourceSiteId,
                target.id,
                atom.position.distanceTo(target.position)
            });
        }
    }

    std::sort(
        moves.begin(),
        moves.end(),
        [](const Move& left, const Move& right) {
            return left.targetId < right.targetId;
        }
    );

    if (static_cast<int>(moves.size()) != desiredFlow) {
        throw std::logic_error("Assignment extraction failed.");
    }

    return moves;
}

int main() {
    try {
        const TrapCalibration calibration{
            850e-9,
            0.8e-6,
            physics::BOLTZMANN * 1e-3,
            physics::RUBIDIUM_87_MASS
        };

        TweezerArray array(4, 4, 5.0, calibration);

        // Example of a measured occupancy pattern after fluorescence imaging.
        const std::vector<int> occupiedSiteIds{
            1, 3, 4, 6, 9, 11, 12, 14, 15, 7
        };

        std::vector<Atom> atoms;
        for (std::size_t index = 0; index < occupiedSiteIds.size(); ++index) {
            const int requestedId = occupiedSiteIds[index];

            const auto site = std::find_if(
                array.sites().begin(),
                array.sites().end(),
                [requestedId](const Site& candidate) {
                    return candidate.id == requestedId;
                }
            );

            if (site == array.sites().end()) {
                throw std::invalid_argument("Observed site identifier is invalid.");
            }

            atoms.push_back({
                static_cast<int>(index + 1),
                site->id,
                site->position
            });
        }

        // A centered 3 x 3 target grid, shifted by half a lattice spacing.
        std::vector<Target> targets;
        int targetId = 1;

        for (int row = 0; row < 3; ++row) {
            for (int column = 0; column < 3; ++column) {
                targets.push_back({
                    targetId++,
                    {
                        2.5 + column * 5.0,
                        2.5 + row * 5.0
                    }
                });
            }
        }

        long long optimizationCost = 0;
        const std::vector<Move> moves = planMinimumCostMoves(
            atoms,
            targets,
            optimizationCost
        );

        const double requestedLoadingProbability = 0.55;
        const double fullInitialLoadingProbability =
            std::pow(requestedLoadingProbability,
                     static_cast<double>(array.sites().size()));

        double totalDistanceUm = 0.0;
        for (const Move& move : moves) {
            totalDistanceUm += move.distanceUm;
        }

        std::cout << std::fixed << std::setprecision(6);
        std::cout << "NEUTRAL-ATOM TWEEZER ARRAY ANALYSIS\n";
        std::cout << "-----------------------------------\n";
        std::cout << "Array sites: " << array.sites().size() << '\n';
        std::cout << "Lattice spacing: 5.0 um\n";
        std::cout << "Observed atoms: " << atoms.size() << '\n';
        std::cout << "Target sites: " << targets.size() << '\n';
        std::cout << "Assigned atoms: " << moves.size() << '\n';
        std::cout << "Unassigned atoms: "
                  << atoms.size() - moves.size() << '\n';
        std::cout << "Target array complete: "
                  << (moves.size() == targets.size() ? "yes" : "no") << '\n';

        std::cout << "\nGAUSSIAN TRAP CHARACTERISTICS\n";
        std::cout << "Rayleigh range: "
                  << calibration.rayleighRangeM() * 1e6 << " um\n";
        std::cout << "Trap depth: " << calibration.depthJ << " J\n";
        std::cout << "Radial frequency: "
                  << calibration.radialFrequencyHz() << " Hz\n";
        std::cout << "Axial frequency: "
                  << calibration.axialFrequencyHz() << " Hz\n";
        std::cout << "Potential at trap center: "
                  << calibration.potentialJ(0.0) << " J\n";

        std::cout << "\nARRAY OPTICAL GEOMETRY\n";
        std::cout << "Maximum neighboring intensity-tail sum: "
                  << array.maximumGaussianTailFraction() << '\n';
        std::cout << "Independent full-array loading probability at p=0.55: "
                  << fullInitialLoadingProbability << '\n';

        std::cout << "\nMINIMUM-COST REARRANGEMENT\n";
        std::cout << "Squared-displacement objective: "
                  << optimizationCost << " half-spacing units squared\n";
        std::cout << "Total transport distance: "
                  << totalDistanceUm << " um\n";

        for (const Move& move : moves) {
            std::cout << "Atom " << move.atomId
                      << " from site " << move.sourceSiteId
                      << " to target " << move.targetId
                      << " | distance " << move.distanceUm << " um\n";
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Simulation error: " << error.what() << '\n';
        return 1;
    }
}
