#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
 * Quantum Interconnect Routing and Resource Engine
 *
 * C++17 implementation of a quantum processor network.
 *
 * Includes:
 * - Processor and channel domain models
 * - Entanglement generation
 * - Fidelity-aware routing
 * - Werner-state entanglement swapping
 * - Quantum memory decay
 * - Resource reservations
 * - Network failure handling
 * - Route eligibility
 * - Network performance metrics
 */

enum class ProcessorState {
    Online,
    Offline,
    Maintenance
};

enum class LinkState {
    Idle,
    Entangled,
    Degraded,
    Down
};

struct Processor {
    std::string id;
    std::string name;
    int capacity;
    int available;
    double coherenceMs;
    ProcessorState state = ProcessorState::Online;

    Processor(
        std::string processorId,
        std::string processorName,
        int qubits,
        double coherence
    )
        : id(std::move(processorId)),
          name(std::move(processorName)),
          capacity(qubits),
          available(qubits),
          coherenceMs(coherence) {

        if (id.empty() || capacity <= 0 || coherenceMs <= 0) {
            throw std::invalid_argument("Invalid processor configuration");
        }
    }

    bool reserve(int count = 1) {
        if (state != ProcessorState::Online ||
            count <= 0 ||
            available < count) {
            return false;
        }

        available -= count;
        return true;
    }

    void release(int count = 1) {
        if (count <= 0 || available + count > capacity) {
            throw std::runtime_error("Invalid qubit release");
        }

        available += count;
    }
};

struct QuantumLink {
    std::string id;
    std::string source;
    std::string destination;
    double distanceKm;
    double generationProbability;
    double initialFidelity;
    double fidelity = 0.0;
    LinkState state = LinkState::Idle;
    int attempts = 0;
    int failures = 0;

    QuantumLink(
        std::string linkId,
        std::string from,
        std::string to,
        double distance,
        double probability,
        double initial
    )
        : id(std::move(linkId)),
          source(std::move(from)),
          destination(std::move(to)),
          distanceKm(distance),
          generationProbability(probability),
          initialFidelity(initial) {

        if (id.empty() || source.empty() || destination.empty() ||
            source == destination || distanceKm <= 0 ||
            probability < 0 || probability > 1 ||
            initial < 0.25 || initial > 1) {
            throw std::invalid_argument("Invalid quantum link");
        }
    }

    bool generate() {
        attempts++;

        if (state == LinkState::Down) {
            return false;
        }

        if (generationProbability < 1.0) {
            // Deterministic demonstration of probabilistic generation.
            // Production hardware adapters must use measured outcomes.
            failures++;
            state = LinkState::Idle;
            return false;
        }

        fidelity = initialFidelity;
        state = LinkState::Entangled;
        return true;
    }

    void decay(double elapsedMs, double coherenceMs) {
        if (elapsedMs < 0 || coherenceMs <= 0) {
            throw std::invalid_argument("Invalid decay parameters");
        }

        if (state != LinkState::Entangled &&
            state != LinkState::Degraded) {
            return;
        }

        fidelity =
            0.25 +
            (fidelity - 0.25) *
            std::exp(-elapsedMs / coherenceMs);

        if (fidelity < 0.5) {
            state = LinkState::Degraded;
        }
    }
};

struct Route {
    std::vector<std::string> processors;
    std::vector<std::string> links;
    double fidelity;
    double latencyMs;
};

struct Metrics {
    int generationAttempts = 0;
    int successfulGenerations = 0;
    int failedGenerations = 0;
    int swaps = 0;
    int rejectedRoutes = 0;
};

class QuantumNetwork {
private:
    std::unordered_map<std::string, Processor> processors;
    std::unordered_map<std::string, QuantumLink> links;

    std::unordered_map<std::string, std::vector<std::string>>
        adjacency;

    Metrics metrics;
    double currentTimeMs = 0.0;

public:
    void addProcessor(const Processor& processor) {
        if (processors.count(processor.id)) {
            throw std::invalid_argument("Duplicate processor ID");
        }

        processors.emplace(processor.id, processor);
        adjacency[processor.id] = {};
    }

    void addLink(const QuantumLink& link) {
        if (links.count(link.id)) {
            throw std::invalid_argument("Duplicate link ID");
        }

        if (!processors.count(link.source) ||
            !processors.count(link.destination)) {
            throw std::invalid_argument("Unknown processor endpoint");
        }

        links.emplace(link.id, link);
        adjacency[link.source].push_back(link.id);
        adjacency[link.destination].push_back(link.id);
    }

    QuantumLink& getLink(const std::string& id) {
        auto it = links.find(id);

        if (it == links.end()) {
            throw std::out_of_range("Unknown quantum link");
        }

        return it->second;
    }

    void generateAll() {
        for (auto& entry : links) {
            QuantumLink& link = entry.second;
            metrics.generationAttempts++;

            if (link.generate()) {
                metrics.successfulGenerations++;
            } else {
                metrics.failedGenerations++;
            }
        }
    }

    static double swappedFidelity(double first, double second) {
        if (first < 0.25 || first > 1 ||
            second < 0.25 || second > 1) {
            throw std::invalid_argument("Invalid fidelity");
        }

        return first * second +
            ((1 - first) * (1 - second)) / 3.0;
    }

    double performSwap(
        const std::string& firstId,
        const std::string& secondId
    ) {
        QuantumLink& first = getLink(firstId);
        QuantumLink& second = getLink(secondId);

        std::unordered_set<std::string> firstNodes = {
            first.source,
            first.destination
        };

        std::vector<std::string> shared;

        for (const std::string& node : {
            second.source,
            second.destination
        }) {
            if (firstNodes.count(node)) {
                shared.push_back(node);
            }
        }

        if (shared.size() != 1) {
            throw std::runtime_error(
                "Entanglement swapping requires one common endpoint"
            );
        }

        if (first.state != LinkState::Entangled ||
            second.state != LinkState::Entangled) {
            throw std::runtime_error("Entanglement unavailable");
        }

        Processor& intermediate = processors.at(shared.front());

        if (!intermediate.reserve()) {
            throw std::runtime_error("Intermediate qubit unavailable");
        }

        try {
            double result = swappedFidelity(
                first.fidelity,
                second.fidelity
            );

            first.fidelity = 0;
            second.fidelity = 0;

            first.state = LinkState::Idle;
            second.state = LinkState::Idle;

            metrics.swaps++;

            intermediate.release();

            return result;
        } catch (...) {
            intermediate.release();
            throw;
        }
    }

    bool decayAll(double elapsedMs) {
        if (elapsedMs < 0) {
            throw std::invalid_argument("Negative time increment");
        }

        for (auto& entry : links) {
            QuantumLink& link = entry.second;

            const double coherence = std::min(
                processors.at(link.source).coherenceMs,
                processors.at(link.destination).coherenceMs
            );

            link.decay(elapsedMs, coherence);
        }

        currentTimeMs += elapsedMs;
        return true;
    }

    Route findRoute(
        const std::string& source,
        const std::string& destination,
        double minimumFidelity = 0.5
    ) {

        if (!processors.count(source) ||
            !processors.count(destination)) {
            throw std::invalid_argument("Unknown processor");
        }

        if (minimumFidelity < 0.25 || minimumFidelity > 1) {
            throw std::invalid_argument("Invalid fidelity threshold");
        }

        if (source == destination) {
            return {{source}, {}, 1.0, 0.0};
        }

        struct State {
            double cost;
            double latency;
            std::string node;
            std::vector<std::string> nodes;
            std::vector<std::string> path;
        };

        auto compare = [](const State& a, const State& b) {
            return a.cost > b.cost;
        };

        std::priority_queue<
            State,
            std::vector<State>,
            decltype(compare)
        > queue(compare);

        std::unordered_map<std::string, double> best;

        best[source] = 0;

        queue.push({
            0,
            0,
            source,
            {source},
            {}
        });

        while (!queue.empty()) {
            State current = queue.top();
            queue.pop();

            if (current.cost > best[current.node]) {
                continue;
            }

            if (current.node == destination) {
                return {
                    current.nodes,
                    current.path,
                    std::exp(-current.cost),
                    current.latency
                };
            }

            for (const std::string& linkId : adjacency[current.node]) {
                const QuantumLink& link = links.at(linkId);

                if (link.state != LinkState::Entangled ||
                    link.fidelity < minimumFidelity) {
                    continue;
                }

                std::string neighbor =
                    link.source == current.node
                        ? link.destination
                        : link.source;

                if (processors.at(neighbor).state !=
                    ProcessorState::Online) {
                    continue;
                }

                double cost = current.cost - std::log(link.fidelity);

                if (best.count(neighbor) &&
                    cost >= best[neighbor]) {
                    continue;
                }

                best[neighbor] = cost;

                State next = {
                    cost,
                    current.latency + link.distanceKm / 200.0,
                    neighbor,
                    current.nodes,
                    current.path
                };

                next.nodes.push_back(neighbor);
                next.path.push_back(linkId);

                queue.push(std::move(next));
            }
        }

        throw std::runtime_error("No eligible quantum route");
    }

    bool hasRoute(
        const std::string& source,
        const std::string& destination
    ) {
        try {
            findRoute(source, destination);
            return true;
        } catch (const std::runtime_error&) {
            metrics.rejectedRoutes++;
            return false;
        }
    }

    void printReport() const {
        std::cout << "\nNETWORK REPORT\n";
        std::cout << "==============\n";

        std::cout << "Simulation time: "
                  << currentTimeMs << " ms\n";

        std::cout << "\nProcessors:\n";

        for (const auto& entry : processors) {
            const Processor& p = entry.second;

            std::cout << p.id
                      << " | " << p.name
                      << " | Qubits: " << p.available
                      << "/" << p.capacity
                      << '\n';
        }

        std::cout << "\nQuantum links:\n";

        for (const auto& entry : links) {
            const QuantumLink& link = entry.second;

            std::cout << link.id
                      << " | " << link.source
                      << " -> " << link.destination
                      << " | Fidelity: " << std::fixed
                      << std::setprecision(5)
                      << link.fidelity
                      << " | Attempts: " << link.attempts
                      << '\n';
        }

        std::cout << "\nMetrics:\n";
        std::cout << "Generation attempts: "
                  << metrics.generationAttempts << '\n';
        std::cout << "Successful generations: "
                  << metrics.successfulGenerations << '\n';
        std::cout << "Failed generations: "
                  << metrics.failedGenerations << '\n';
        std::cout << "Entanglement swaps: "
                  << metrics.swaps << '\n';
        std::cout << "Rejected routes: "
                  << metrics.rejectedRoutes << '\n';
    }
};

int main() {
    try {
        QuantumNetwork network;

        network.addProcessor(
            Processor("Q1", "North Quantum Center", 16, 100)
        );

        network.addProcessor(
            Processor("Q2", "Central Quantum Center", 12, 80)
        );

        network.addProcessor(
            Processor("Q3", "South Quantum Center", 16, 120)
        );

        network.addProcessor(
            Processor("Q4", "Remote Quantum Center", 8, 60)
        );

        network.addLink(
            QuantumLink("L12", "Q1", "Q2", 20, 1.0, 0.98)
        );

        network.addLink(
            QuantumLink("L23", "Q2", "Q3", 30, 1.0, 0.97)
        );

        network.addLink(
            QuantumLink("L13", "Q1", "Q3", 65, 1.0, 0.91)
        );

        network.addLink(
            QuantumLink("L34", "Q3", "Q4", 15, 1.0, 0.96)
        );

        network.addLink(
            QuantumLink("L24", "Q2", "Q4", 45, 0.0, 0.94)
        );

        std::cout << "QUANTUM INTERCONNECT ROUTING ENGINE\n";
        std::cout << "===================================\n";

        network.generateAll();

        std::cout << "\nSelected quantum route:\n";

        Route route = network.findRoute("Q1", "Q4");

        for (std::size_t i = 0; i < route.processors.size(); i++) {
            if (i) {
                std::cout << " -> ";
            }

            std::cout << route.processors[i];
        }

        std::cout << "\nLinks: ";

        for (const auto& id : route.links) {
            std::cout << id << " ";
        }

        std::cout << "\nEstimated fidelity: "
                  << route.fidelity << '\n';

        std::cout << "Estimated latency: "
                  << route.latencyMs << " ms\n";

        double swapped = network.performSwap("L12", "L23");

        std::cout << "\nSwapped fidelity: "
                  << swapped << '\n';

        network.decayAll(15);

        network.printReport();

        // Deterministic validation.
        if (QuantumNetwork::swappedFidelity(1, 1) != 1) {
            throw std::runtime_error("Fidelity validation failed");
        }

        std::cout << "\nAll core operations completed successfully.\n";

        return 0;

    } catch (const std::exception& error) {
        std::cerr << "Network error: "
                  << error.what() << '\n';

        return 1;
    }
}
