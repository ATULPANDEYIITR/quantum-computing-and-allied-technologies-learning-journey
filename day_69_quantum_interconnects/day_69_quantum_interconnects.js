"use strict";

/*
 * Quantum Interconnect Network
 * ----------------------------
 * Event-driven quantum network simulator.
 *
 * Features:
 * - Quantum processor registry
 * - Quantum channel configuration
 * - Asynchronous entanglement generation
 * - Fidelity-aware routing
 * - Entanglement swapping
 * - Quantum memory decoherence
 * - Network policy evaluation
 * - Resource allocation
 * - Event history
 * - Failure recovery
 * - JSON reporting
 *
 * Uses a simplified Werner-state model.
 * It does not simulate quantum circuits or physical hardware.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const LinkStatus = Object.freeze({
    IDLE: "IDLE",
    ENTANGLED: "ENTANGLED",
    DEGRADED: "DEGRADED",
    DOWN: "DOWN"
});

const ProcessorStatus = Object.freeze({
    ONLINE: "ONLINE",
    OFFLINE: "OFFLINE",
    MAINTENANCE: "MAINTENANCE"
});

class QuantumNetworkError extends Error {
    constructor(message, code) {
        super(message);
        this.name = "QuantumNetworkError";
        this.code = code;
    }
}

class QuantumProcessor {
    constructor({
        id,
        name,
        qubitCapacity,
        coherenceTimeMs
    }) {
        if (!id || !name) {
            throw new TypeError("Processor identity is required");
        }

        if (!Number.isInteger(qubitCapacity) || qubitCapacity <= 0) {
            throw new RangeError("Invalid qubit capacity");
        }

        if (!Number.isFinite(coherenceTimeMs) || coherenceTimeMs <= 0) {
            throw new RangeError("Invalid coherence time");
        }

        this.id = id;
        this.name = name;
        this.qubitCapacity = qubitCapacity;
        this.availableQubits = qubitCapacity;
        this.coherenceTimeMs = coherenceTimeMs;
        this.status = ProcessorStatus.ONLINE;
    }

    reserve(count = 1) {
        if (!Number.isInteger(count) || count <= 0) {
            throw new RangeError("Reservation count must be positive");
        }

        if (this.status !== ProcessorStatus.ONLINE) {
            return false;
        }

        if (this.availableQubits < count) {
            return false;
        }

        this.availableQubits -= count;
        return true;
    }

    release(count = 1) {
        if (!Number.isInteger(count) || count <= 0) {
            throw new RangeError("Release count must be positive");
        }

        if (this.availableQubits + count > this.qubitCapacity) {
            throw new QuantumNetworkError(
                "Qubit release exceeds capacity",
                "RESOURCE_OVERFLOW"
            );
        }

        this.availableQubits += count;
    }
}

class QuantumLink {
    constructor({
        id,
        source,
        destination,
        distanceKm,
        generationProbability,
        fidelity
    }) {
        if (!id || !source || !destination || source === destination) {
            throw new TypeError("Invalid quantum link endpoints");
        }

        if (!Number.isFinite(distanceKm) || distanceKm <= 0) {
            throw new RangeError("Distance must be positive");
        }

        if (
            !Number.isFinite(generationProbability) ||
            generationProbability < 0 ||
            generationProbability > 1
        ) {
            throw new RangeError("Invalid generation probability");
        }

        if (!Number.isFinite(fidelity) || fidelity < 0.25 || fidelity > 1) {
            throw new RangeError("Invalid initial fidelity");
        }

        this.id = id;
        this.source = source;
        this.destination = destination;
        this.distanceKm = distanceKm;
        this.generationProbability = generationProbability;
        this.initialFidelity = fidelity;
        this.currentFidelity = 0;
        this.status = LinkStatus.IDLE;
        this.attempts = 0;
        this.failures = 0;
    }

    generate(random = Math.random) {
        this.attempts++;

        if (this.status === LinkStatus.DOWN) {
            return false;
        }

        if (random() > this.generationProbability) {
            this.failures++;
            this.status = LinkStatus.IDLE;
            return false;
        }

        this.currentFidelity = this.initialFidelity;
        this.status = LinkStatus.ENTANGLED;
        return true;
    }

    decay(elapsedMs, coherenceTimeMs) {
        if (!Number.isFinite(elapsedMs) || elapsedMs < 0) {
            throw new RangeError("Invalid elapsed time");
        }

        if (
            this.status !== LinkStatus.ENTANGLED &&
            this.status !== LinkStatus.DEGRADED
        ) {
            return;
        }

        this.currentFidelity =
            0.25 +
            (this.currentFidelity - 0.25) *
            Math.exp(-elapsedMs / coherenceTimeMs);

        if (this.currentFidelity < 0.5) {
            this.status = LinkStatus.DEGRADED;
        }
    }
}

class QuantumNetwork extends EventEmitter {
    constructor({ seed = 2026 } = {}) {
        super();

        this.processors = new Map();
        this.links = new Map();
        this.adjacency = new Map();
        this.events = [];
        this.timeMs = 0;

        this.metrics = {
            generationAttempts: 0,
            successfulGenerations: 0,
            failedGenerations: 0,
            swaps: 0,
            failedSwaps: 0,
            routes: 0,
            rejectedRoutes: 0
        };

        this.seed = seed >>> 0;
    }

    // Seeded pseudo-random source provides reproducible experiments.
    random() {
        this.seed = (
            Math.imul(this.seed, 1664525) + 1013904223
        ) >>> 0;

        return this.seed / 4294967296;
    }

    record(type, details) {
        const event = {
            timestampMs: this.timeMs,
            type,
            details
        };

        this.events.push(event);
        this.emit(type, event);
    }

    addProcessor(processor) {
        if (this.processors.has(processor.id)) {
            throw new QuantumNetworkError(
                "Duplicate processor",
                "DUPLICATE_PROCESSOR"
            );
        }

        this.processors.set(processor.id, processor);
        this.adjacency.set(processor.id, []);
    }

    addLink(link) {
        if (this.links.has(link.id)) {
            throw new QuantumNetworkError(
                "Duplicate link",
                "DUPLICATE_LINK"
            );
        }

        if (
            !this.processors.has(link.source) ||
            !this.processors.has(link.destination)
        ) {
            throw new QuantumNetworkError(
                "Unknown link endpoint",
                "UNKNOWN_ENDPOINT"
            );
        }

        this.links.set(link.id, link);

        this.adjacency.get(link.source).push(link.id);
        this.adjacency.get(link.destination).push(link.id);
    }

    async generateEntanglement(linkId) {
        const link = this.links.get(linkId);

        if (!link) {
            throw new QuantumNetworkError(
                "Quantum link not found",
                "LINK_NOT_FOUND"
            );
        }

        // Asynchronous scheduling allows independent link attempts.
        await Promise.resolve();

        this.metrics.generationAttempts++;

        const success = link.generate(() => this.random());

        if (success) {
            this.metrics.successfulGenerations++;
            this.record("entanglement-created", {
                linkId,
                fidelity: link.currentFidelity
            });
        } else {
            this.metrics.failedGenerations++;
            this.record("entanglement-failed", { linkId });
        }

        return success;
    }

    async generateAll() {
        const results = await Promise.all(
            [...this.links.keys()].map(id =>
                this.generateEntanglement(id)
            )
        );

        return results;
    }

    findRoute(source, destination, minimumFidelity = 0.5) {
        if (
            !this.processors.has(source) ||
            !this.processors.has(destination)
        ) {
            throw new QuantumNetworkError(
                "Unknown processor",
                "UNKNOWN_PROCESSOR"
            );
        }

        if (
            !Number.isFinite(minimumFidelity) ||
            minimumFidelity < 0.25 ||
            minimumFidelity > 1
        ) {
            throw new RangeError("Invalid fidelity threshold");
        }

        if (source === destination) {
            return {
                processors: [source],
                links: [],
                fidelity: 1,
                latencyMs: 0
            };
        }

        // Dijkstra's algorithm with negative logarithmic fidelity cost.
        const queue = [{
            node: source,
            cost: 0,
            latency: 0,
            processors: [source],
            links: []
        }];

        const best = new Map([[source, 0]]);

        while (queue.length) {
            queue.sort((a, b) => a.cost - b.cost);

            const current = queue.shift();

            if (current.cost > best.get(current.node)) {
                continue;
            }

            if (current.node === destination) {
                return {
                    processors: current.processors,
                    links: current.links,
                    fidelity: Math.exp(-current.cost),
                    latencyMs: current.latency
                };
            }

            for (const linkId of this.adjacency.get(current.node)) {
                const link = this.links.get(linkId);

                if (
                    link.status !== LinkStatus.ENTANGLED ||
                    link.currentFidelity < minimumFidelity
                ) {
                    continue;
                }

                const neighbor =
                    link.source === current.node
                        ? link.destination
                        : link.source;

                if (
                    this.processors.get(neighbor).status !==
                    ProcessorStatus.ONLINE
                ) {
                    continue;
                }

                const newCost =
                    current.cost - Math.log(link.currentFidelity);

                if (newCost >= (best.get(neighbor) ?? Infinity)) {
                    continue;
                }

                best.set(neighbor, newCost);

                queue.push({
                    node: neighbor,
                    cost: newCost,
                    latency:
                        current.latency + link.distanceKm / 200,
                    processors: [...current.processors, neighbor],
                    links: [...current.links, linkId]
                });
            }
        }

        return null;
    }

    static swappedFidelity(first, second) {
        for (const value of [first, second]) {
            if (!Number.isFinite(value) || value < 0.25 || value > 1) {
                throw new RangeError("Invalid Werner-state fidelity");
            }
        }

        return (
            first * second +
            ((1 - first) * (1 - second)) / 3
        );
    }

    swap(firstId, secondId) {
        const first = this.links.get(firstId);
        const second = this.links.get(secondId);

        if (!first || !second) {
            throw new QuantumNetworkError(
                "Link unavailable",
                "LINK_NOT_FOUND"
            );
        }

        const shared = [
            first.source,
            first.destination
        ].filter(node =>
            node === second.source || node === second.destination
        );

        if (shared.length !== 1) {
            throw new QuantumNetworkError(
                "Links must share exactly one endpoint",
                "INVALID_SWAP_TOPOLOGY"
            );
        }

        if (
            first.status !== LinkStatus.ENTANGLED ||
            second.status !== LinkStatus.ENTANGLED
        ) {
            this.metrics.failedSwaps++;
            throw new QuantumNetworkError(
                "Both links must be entangled",
                "ENTANGLEMENT_UNAVAILABLE"
            );
        }

        const intermediate = this.processors.get(shared[0]);

        if (!intermediate.reserve()) {
            this.metrics.failedSwaps++;
            throw new QuantumNetworkError(
                "Intermediate processor has no free qubit",
                "RESOURCE_EXHAUSTED"
            );
        }

        try {
            const result = QuantumNetwork.swappedFidelity(
                first.currentFidelity,
                second.currentFidelity
            );

            first.currentFidelity = 0;
            second.currentFidelity = 0;
            first.status = LinkStatus.IDLE;
            second.status = LinkStatus.IDLE;

            this.metrics.swaps++;

            this.record("entanglement-swapped", {
                firstId,
                secondId,
                intermediate: shared[0],
                outputFidelity: result
            });

            return result;
        } finally {
            intermediate.release();
        }
    }

    advanceTime(elapsedMs) {
        if (!Number.isFinite(elapsedMs) || elapsedMs < 0) {
            throw new RangeError("Invalid time increment");
        }

        for (const link of this.links.values()) {
            const first = this.processors.get(link.source);
            const second = this.processors.get(link.destination);

            link.decay(
                elapsedMs,
                Math.min(
                    first.coherenceTimeMs,
                    second.coherenceTimeMs
                )
            );
        }

        this.timeMs += elapsedMs;
        this.record("clock-advanced", { elapsedMs });
    }

    evaluateRoute(source, destination, minimumFidelity = 0.5) {
        const route = this.findRoute(
            source,
            destination,
            minimumFidelity
        );

        if (!route) {
            this.metrics.rejectedRoutes++;
            this.record("route-rejected", { source, destination });
            return null;
        }

        this.metrics.routes++;
        this.record("route-established", route);
        return route;
    }

    setLinkStatus(linkId, status) {
        const link = this.links.get(linkId);

        if (!link) {
            throw new QuantumNetworkError(
                "Link not found",
                "LINK_NOT_FOUND"
            );
        }

        if (!Object.values(LinkStatus).includes(status)) {
            throw new RangeError("Invalid link status");
        }

        link.status = status;

        if (status !== LinkStatus.ENTANGLED) {
            link.currentFidelity = 0;
        }

        this.record("link-status-changed", { linkId, status });
    }

    report() {
        return {
            simulationTimeMs: this.timeMs,
            processors: [...this.processors.values()].map(p => ({
                id: p.id,
                name: p.name,
                status: p.status,
                capacity: p.qubitCapacity,
                available: p.availableQubits
            })),
            links: [...this.links.values()].map(l => ({
                id: l.id,
                source: l.source,
                destination: l.destination,
                status: l.status,
                fidelity: Number(l.currentFidelity.toFixed(6)),
                attempts: l.attempts,
                failures: l.failures
            })),
            metrics: { ...this.metrics },
            events: [...this.events]
        };
    }

    async exportReport(filename) {
        if (!filename.endsWith(".json")) {
            throw new TypeError("Report must use JSON extension");
        }

        await fs.writeFile(
            filename,
            JSON.stringify(this.report(), null, 2),
            { encoding: "utf8", mode: 0o600 }
        );
    }
}

function buildNetwork() {
    const network = new QuantumNetwork({ seed: 77 });

    const processors = [
        new QuantumProcessor({
            id: "Q1",
            name: "North Quantum Center",
            qubitCapacity: 16,
            coherenceTimeMs: 100
        }),
        new QuantumProcessor({
            id: "Q2",
            name: "Central Quantum Center",
            qubitCapacity: 12,
            coherenceTimeMs: 80
        }),
        new QuantumProcessor({
            id: "Q3",
            name: "South Quantum Center",
            qubitCapacity: 16,
            coherenceTimeMs: 120
        }),
        new QuantumProcessor({
            id: "Q4",
            name: "Remote Quantum Center",
            qubitCapacity: 8,
            coherenceTimeMs: 60
        })
    ];

    processors.forEach(p => network.addProcessor(p));

    const links = [
        new QuantumLink({
            id: "L12",
            source: "Q1",
            destination: "Q2",
            distanceKm: 20,
            generationProbability: 1,
            fidelity: 0.98
        }),
        new QuantumLink({
            id: "L23",
            source: "Q2",
            destination: "Q3",
            distanceKm: 30,
            generationProbability: 1,
            fidelity: 0.97
        }),
        new QuantumLink({
            id: "L13",
            source: "Q1",
            destination: "Q3",
            distanceKm: 65,
            generationProbability: 1,
            fidelity: 0.91
        }),
        new QuantumLink({
            id: "L34",
            source: "Q3",
            destination: "Q4",
            distanceKm: 15,
            generationProbability: 1,
            fidelity: 0.96
        }),
        new QuantumLink({
            id: "L24",
            source: "Q2",
            destination: "Q4",
            distanceKm: 45,
            generationProbability: 0,
            fidelity: 0.94
        })
    ];

    links.forEach(link => network.addLink(link));

    return network;
}

async function main() {
    const network = buildNetwork();

    network.on("entanglement-created", event => {
        console.log(
            `EVENT: ${event.details.linkId} entanglement created`
        );
    });

    network.on("route-established", event => {
        console.log("EVENT: Quantum route established");
    });

    console.log("QUANTUM INTERCONNECT EVENT SIMULATOR");
    console.log("====================================");

    await network.generateAll();

    console.log("\nRoute evaluation:");

    const route = network.evaluateRoute("Q1", "Q4");

    if (route) {
        console.log("Path:", route.processors.join(" -> "));
        console.log("Links:", route.links.join(", "));
        console.log("Fidelity:", route.fidelity.toFixed(6));
        console.log("Latency:", route.latencyMs.toFixed(4), "ms");
    } else {
        console.log("No eligible route.");
    }

    console.log("\nEntanglement swapping:");

    const fidelity = network.swap("L12", "L23");
    console.log("Output fidelity:", fidelity.toFixed(6));

    network.advanceTime(15);

    console.log("\nNetwork metrics:");
    console.log(JSON.stringify(network.metrics, null, 2));

    await network.exportReport("quantum_interconnect_report.json");

    console.log("\nReport exported successfully.");

    console.assert(
        QuantumNetwork.swappedFidelity(1, 1) === 1,
        "Perfect input fidelity should remain perfect"
    );

    console.assert(
        network.processors.get("Q2").availableQubits === 12,
        "Intermediate qubit must be released after swapping"
    );

    console.log("Assertions completed.");
}

main().catch(error => {
    console.error("Simulation failed:", error.message);
    process.exitCode = 1;
});
