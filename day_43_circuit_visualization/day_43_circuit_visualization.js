"use strict";

/*
 * Circuit Visualization and Analysis
 *
 * Node.js implementation featuring:
 * - A typed-by-validation circuit component model.
 * - Kirchhoff-based DC analysis using nodal conductance equations.
 * - Interactive-ready SVG rendering with component selection metadata.
 * - Event-driven editing and automatic analysis refresh.
 * - Netlist validation, power balance, and JSON serialization.
 *
 * Run: node circuit_visualization.js
 */

const fs = require("node:fs/promises");

class CircuitError extends Error {
    constructor(message) {
        super(message);
        this.name = "CircuitError";
    }
}

function finiteNumber(value, label) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new CircuitError(`${label} must be a finite number.`);
    }
    return value;
}

class Resistor {
    constructor(name, a, b, resistance) {
        if (!name.trim() || !a || !b || a === b) {
            throw new CircuitError("Invalid resistor identity or terminals.");
        }
        finiteNumber(resistance, `${name} resistance`);
        if (resistance <= 0) {
            throw new CircuitError(`${name} resistance must be positive.`);
        }
        this.type = "resistor";
        this.name = name;
        this.a = a;
        this.b = b;
        this.resistance = resistance;
        Object.freeze(this);
    }
}

class VoltageSource {
    constructor(name, positive, negative, voltage) {
        if (!name.trim() || !positive || !negative || positive === negative) {
            throw new CircuitError("Invalid voltage-source identity or terminals.");
        }
        finiteNumber(voltage, `${name} voltage`);
        this.type = "voltage-source";
        this.name = name;
        this.positive = positive;
        this.negative = negative;
        this.voltage = voltage;
        Object.freeze(this);
    }
}

class Circuit {
    constructor(name = "DC Circuit", ground = "0") {
        this.name = name;
        this.ground = ground;
        this.components = [];
    }

    add(component) {
        if (!(component instanceof Resistor ||
              component instanceof VoltageSource)) {
            throw new CircuitError("Unsupported circuit component.");
        }
        if (this.components.some(item => item.name === component.name)) {
            throw new CircuitError(`Duplicate component: ${component.name}`);
        }
        this.components.push(component);
        return this;
    }

    get nodes() {
        const nodes = new Set();
        for (const component of this.components) {
            if (component.type === "resistor") {
                nodes.add(component.a);
                nodes.add(component.b);
            } else {
                nodes.add(component.positive);
                nodes.add(component.negative);
            }
        }
        return [...nodes].sort();
    }

    validate() {
        const nodes = this.nodes;
        if (!this.components.length) {
            throw new CircuitError("Cannot analyze an empty circuit.");
        }
        if (!nodes.includes(this.ground)) {
            throw new CircuitError("The ground node does not exist.");
        }

        const adjacency = new Map(nodes.map(node => [node, []]));
        for (const component of this.components) {
            const a = component.type === "resistor"
                ? component.a : component.positive;
            const b = component.type === "resistor"
                ? component.b : component.negative;
            adjacency.get(a).push(b);
            adjacency.get(b).push(a);
        }

        const visited = new Set([this.ground]);
        const queue = [this.ground];

        for (let head = 0; head < queue.length; head++) {
            const node = queue[head];
            for (const neighbor of adjacency.get(node)) {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    queue.push(neighbor);
                }
            }
        }

        if (visited.size !== nodes.length) {
            throw new CircuitError("Some circuit nodes are disconnected from ground.");
        }
    }

    analyze() {
        this.validate();

        const resistors = this.components.filter(c => c.type === "resistor");
        const sources = this.components.filter(c => c.type === "voltage-source");
        const unknownNodes = this.nodes.filter(node => node !== this.ground);
        const index = new Map(unknownNodes.map((node, i) => [node, i]));
        const n = unknownNodes.length;
        const size = n + sources.length;
        const matrix = Array.from({ length: size }, () =>
            Array(size).fill(0));
        const rhs = Array(size).fill(0);

        const stampConductance = (a, b, conductance) => {
            if (a !== this.ground) matrix[index.get(a)][index.get(a)] += conductance;
            if (b !== this.ground) matrix[index.get(b)][index.get(b)] += conductance;
            if (a !== this.ground && b !== this.ground) {
                matrix[index.get(a)][index.get(b)] -= conductance;
                matrix[index.get(b)][index.get(a)] -= conductance;
            }
        };

        for (const resistor of resistors) {
            stampConductance(resistor.a, resistor.b, 1 / resistor.resistance);
        }

        sources.forEach((source, i) => {
            const currentIndex = n + i;
            if (source.positive !== this.ground) {
                const p = index.get(source.positive);
                matrix[p][currentIndex] += 1;
                matrix[currentIndex][p] += 1;
            }
            if (source.negative !== this.ground) {
                const m = index.get(source.negative);
                matrix[m][currentIndex] -= 1;
                matrix[currentIndex][m] -= 1;
            }
            rhs[currentIndex] = source.voltage;
        });

        const solution = solveLinearSystem(matrix, rhs);
        const voltages = { [this.ground]: 0 };
        unknownNodes.forEach((node, i) => {
            voltages[node] = solution[i];
        });

        const resistorResults = resistors.map(resistor => {
            const voltage = voltages[resistor.a] - voltages[resistor.b];
            const current = voltage / resistor.resistance;
            return {
                name: resistor.name,
                voltage,
                current,
                power: voltage * current
            };
        });

        const sourceResults = sources.map((source, i) => ({
            name: source.name,
            voltage: source.voltage,
            current: solution[n + i],
            power: source.voltage * solution[n + i]
        }));

        const resistorPower = resistorResults.reduce(
            (sum, item) => sum + item.power, 0);
        const sourcePower = sourceResults.reduce(
            (sum, item) => sum + item.power, 0);

        if (Math.abs(resistorPower + sourcePower) >
            1e-7 * Math.max(1, Math.abs(resistorPower))) {
            throw new CircuitError("Power conservation check failed.");
        }

        return { voltages, resistors: resistorResults,
            sources: sourceResults, resistorPower, sourcePower };
    }

    toJSON() {
        return {
            name: this.name,
            ground: this.ground,
            components: this.components.map(component => ({ ...component }))
        };
    }
}

function solveLinearSystem(inputMatrix, inputRhs) {
    const n = inputRhs.length;
    if (!n || inputMatrix.length !== n ||
        inputMatrix.some(row => row.length !== n)) {
        throw new CircuitError("The matrix must be non-empty and square.");
    }

    const a = inputMatrix.map((row, i) => [...row, inputRhs[i]]);

    for (let column = 0; column < n; column++) {
        let pivot = column;
        for (let row = column + 1; row < n; row++) {
            if (Math.abs(a[row][column]) > Math.abs(a[pivot][column])) {
                pivot = row;
            }
        }

        if (Math.abs(a[pivot][column]) < 1e-12) {
            throw new CircuitError("Singular circuit matrix.");
        }

        [a[column], a[pivot]] = [a[pivot], a[column]];

        const divisor = a[column][column];
        for (let j = column; j <= n; j++) {
            a[column][j] /= divisor;
        }

        for (let row = 0; row < n; row++) {
            if (row === column) continue;
            const factor = a[row][column];
            for (let j = column; j <= n; j++) {
                a[row][j] -= factor * a[column][j];
            }
        }
    }

    const solution = a.map(row => row[n]);
    if (solution.some(value => !Number.isFinite(value))) {
        throw new CircuitError("Non-finite solution.");
    }
    return solution;
}

function escapeXml(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&apos;"
    })[character]);
}

function renderSvg(circuit, results) {
    const width = 960;
    const height = Math.max(260, 150 + circuit.components.length * 95);
    const rows = circuit.components.map((component, index) => {
        const y = 105 + index * 95;
        const left = 210;
        const right = 690;
        const label = component.type === "resistor"
            ? `${component.resistance} Ω`
            : `${component.voltage} V`;

        const symbol = component.type === "resistor"
            ? `<rect x="370" y="${y - 14}" width="160" height="28"
                      fill="#162a3a" stroke="#ffca66" stroke-width="3"/>`
            : `<circle cx="450" cy="${y}" r="30" fill="#162a3a"
                       stroke="#ffca66" stroke-width="3"/>
               <text x="450" y="${y + 6}" text-anchor="middle"
                     fill="#ffffff" font-size="15">DC</text>`;

        const a = component.type === "resistor"
            ? component.a : component.positive;
        const b = component.type === "resistor"
            ? component.b : component.negative;
        const voltage = component.type === "resistor"
            ? results.voltages[a] - results.voltages[b]
            : component.voltage;

        return `
          <g data-component="${escapeXml(component.name)}">
            <text x="35" y="${y + 5}" fill="#ffffff" font-size="16">
              ${escapeXml(component.name)}</text>
            <line x1="${left}" y1="${y}" x2="${component.type === "resistor" ? 370 : 420}"
                  y2="${y}" stroke="#86d8ff" stroke-width="2.5"/>
            ${symbol}
            <line x1="${component.type === "resistor" ? 530 : 480}"
                  y1="${y}" x2="${right}" y2="${y}"
                  stroke="#86d8ff" stroke-width="2.5"/>
            <text x="450" y="${y - 23}" text-anchor="middle"
                  fill="#ffffff" font-size="13">${escapeXml(label)}</text>
            <text x="${left}" y="${y + 23}" fill="#b8c9d6" font-size="12">
              ${escapeXml(a)}</text>
            <text x="${right}" y="${y + 23}" fill="#b8c9d6" font-size="12">
              ${escapeXml(b)}</text>
            <text x="735" y="${y + 4}" fill="#9fe7c3" font-size="13">
              ΔV = ${voltage.toFixed(3)} V</text>
          </g>`;
    }).join("\n");

    return `<svg xmlns="http://www.w3.org/2000/svg"
      width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
      <rect width="100%" height="100%" fill="#0b1722"/>
      <text x="35" y="42" fill="#ffffff" font-size="24">
        ${escapeXml(circuit.name)}</text>
      <text x="35" y="68" fill="#b8c9d6" font-size="13">
        DC operating point | Ground: ${escapeXml(circuit.ground)}</text>
      ${rows}
      <text x="35" y="${height - 20}" fill="#b8c9d6" font-size="12">
        Schematic overview; lines represent terminal connectivity, not physical layout.
      </text>
    </svg>`;
}

/*
 * CircuitEditor separates user actions from model updates.
 * A browser UI can subscribe to the same events and redraw only when needed.
 */
class CircuitEditor {
    constructor(circuit) {
        this.circuit = circuit;
        this.listeners = new Map();
    }

    on(eventName, callback) {
        if (typeof callback !== "function") {
            throw new CircuitError("Event listener must be a function.");
        }
        if (!this.listeners.has(eventName)) this.listeners.set(eventName, new Set());
        this.listeners.get(eventName).add(callback);
        return () => this.listeners.get(eventName).delete(callback);
    }

    emit(eventName, payload) {
        for (const callback of this.listeners.get(eventName) || []) {
            callback(payload);
        }
    }

    addResistor(name, a, b, resistance) {
        const component = new Resistor(name, a, b, resistance);
        this.circuit.add(component);
        this.emit("component-added", component);
        this.emit("analysis-updated", this.circuit.analyze());
    }

    addSource(name, positive, negative, voltage) {
        const component = new VoltageSource(name, positive, negative, voltage);
        this.circuit.add(component);
        this.emit("component-added", component);
        this.emit("analysis-updated", this.circuit.analyze());
    }
}

async function main() {
    const circuit = new Circuit("Battery-Powered Sensor", "0");
    const editor = new CircuitEditor(circuit);

    editor.on("component-added", component => {
        console.log(`Added ${component.name} (${component.type}).`);
    });

    editor.on("analysis-updated", results => {
        console.log("Updated node voltages:", results.voltages);
    });

    editor.addSource("V1", "supply", "0", 9);
    editor.addResistor("R1", "supply", "sensor", 1000);
    editor.addResistor("R2", "sensor", "0", 2000);

    const results = circuit.analyze();
    console.log("\nBranch analysis");
    console.table(results.resistors);
    console.table(results.sources);
    console.log("Resistor power:", results.resistorPower.toFixed(6), "W");
    console.log("Source power:", results.sourcePower.toFixed(6), "W");

    await fs.writeFile("circuit_schematic.svg",
        renderSvg(circuit, results), "utf8");
    await fs.writeFile("circuit_netlist.json",
        JSON.stringify(circuit.toJSON(), null, 2), "utf8");

    console.log("Generated circuit_schematic.svg and circuit_netlist.json");

    const dividerVoltage = results.voltages.sensor;
    if (Math.abs(dividerVoltage - 6) > 1e-8) {
        throw new Error("Voltage-divider verification failed.");
    }

    console.log("Voltage-divider verification passed.");
}

main().catch(error => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
