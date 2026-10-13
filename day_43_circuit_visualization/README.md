# Circuit Visualization and Analysis

## Technical scope

Circuit visualization represents electrical components, their terminals, and their connections in a readable schematic. Circuit analysis evaluates the electrical behavior implied by those connections and component properties.

These are related but distinct operations. A schematic can be visually attractive while electrically incorrect. A solver can calculate a valid operating point while the displayed component placement is confusing. A reliable circuit engineering workflow therefore maintains a structured electrical model and derives both numerical results and visual representations from that model.

This project implements a DC circuit workflow across Python, JavaScript, C++17, Java 17, and PostgreSQL. The examples concentrate on resistive networks and independent ideal DC voltage sources. They demonstrate connectivity validation, nodal analysis, branch measurements, power conservation, schematic rendering, and operating-limit checks.

## Electrical model

### Components and terminals

A circuit is represented as a graph. Electrical nodes represent connection points, and components connect pairs of nodes. A resistor has two terminals and a positive resistance. An ideal voltage source imposes a voltage difference between its positive and negative terminals.

The reference node, usually named `0`, defines zero volts. Every other node voltage is measured relative to this reference. Two component terminals with the same node identifier are electrically connected even when their symbols appear far apart in a schematic.

Component names identify parts in reports and exported netlists. They must be unique within a circuit so that a measurement can be traced to the correct component.

### Kirchhoff's current law

Kirchhoff's current law states that the algebraic sum of currents entering a node is zero. For a resistor connecting nodes \(a\) and \(b\), Ohm's law gives

\[
I_{ab}=\frac{V_a-V_b}{R}
\]

The current depends on the voltage difference and the resistance. A negative calculated current means that the actual current flows opposite to the selected reference direction.

For a resistor-only network, nodal analysis creates a system of linear equations. Each node contributes a current-balance equation. Resistors connecting two unknown nodes introduce negative off-diagonal conductance terms, while their conductance contributes positively to the corresponding diagonal entries.

### Modified nodal analysis

An ideal voltage source cannot be represented as an ordinary finite conductance. Modified nodal analysis introduces a current unknown for each independent voltage source and adds a voltage-constraint equation.

The resulting system has the form

\[
\begin{bmatrix}
G & B\\
B^T & 0
\end{bmatrix}
\begin{bmatrix}
v\\
i_s
\end{bmatrix}
=
\begin{bmatrix}
j\\
e
\end{bmatrix}
\]

Here, \(G\) is the nodal conductance matrix, \(B\) represents voltage-source connections, \(v\) contains unknown node voltages, \(i_s\) contains source currents, \(j\) represents current injections, and \(e\) contains source voltages.

The Python, JavaScript, C++, and Java programs assemble this system and solve it using Gaussian elimination with partial pivoting. Pivoting reduces numerical error compared with elimination that always selects the diagonal element. It does not make an ill-conditioned circuit accurate or resolve a physically underdetermined model.

## Circuit visualization

### Schematic representation

A useful schematic communicates component identity, terminal connectivity, values, and electrical reference directions. The Python, JavaScript, C++, and Java implementations produce schematic-oriented output in different forms.

The Python program writes an SVG drawing and a JSON netlist. The SVG uses named components and terminal labels, while the JSON preserves the circuit definition for inspection or further processing.

The JavaScript implementation renders SVG from the same component objects used by its solver. Component names are escaped before being inserted into SVG text or attributes. This prevents untrusted names from becoming executable markup.

The C++ program prints an ASCII schematic and pairs it with an electrical measurement report. This is useful in command-line engineering tools, automated diagnostics, and environments where graphical rendering is not available.

The Java implementation separates the circuit domain model, analysis service, operating-limit policy, and SVG renderer. This separation makes it possible to replace the rendering layer without changing the electrical solver.

The drawings in these examples are schematic overviews rather than geometrically accurate circuit diagrams. They do not guarantee that wire crossings, junction dots, symbol orientation, or physical placement meet an electrical drafting standard.

### Visual properties and electrical properties

Schematic coordinates are presentation data. Node identity and component connectivity are electrical data. Moving a resistor on the canvas must not change the circuit's resistance or connectivity unless the editing operation explicitly changes its terminal assignments.

A production visual editor should support:

- Explicit junctions so that wire crossings cannot be mistaken for electrical connections.
- Snap-to-grid placement and stable component orientation.
- Visible terminal names and component values.
- Selection and highlighting of individual components.
- Distinct representations for ground, voltage sources, resistors, and other supported parts.
- Separate indicators for warnings, invalid connectivity, and analysis results.

The sample renderers focus on basic readability. Their schematic layouts do not attempt automatic graph routing or sophisticated symbol placement.

## Python implementation

The Python script defines immutable `Resistor` and `VoltageSource` data classes. A `Circuit` object owns the component collections and provides validation, netlist export, analysis, and a resistor-network equivalent-resistance calculation.

The analysis routine constructs the modified nodal analysis matrix. The voltage-source current variables are appended after the unknown node voltages. Source polarity is represented by the signs of the corresponding matrix entries.

The Gaussian elimination function copies its input matrix before performing elimination. Partial pivoting selects the largest available absolute value in the current column. A nearly zero pivot causes a `CircuitError`, indicating that the equations do not provide a unique numerical solution under the chosen tolerance.

The program also calculates resistor currents and powers. Its source-current convention is positive from the positive terminal toward the negative terminal. Source power is calculated using the source voltage and that reference current. A negative source power therefore indicates power delivery.

The power-conservation check verifies that resistor dissipation and total source power approximately sum to zero. The tolerance allows for floating-point rounding rather than requiring exact binary equality.

The built-in tests check a voltage divider, parallel resistance, invalid resistance, a singular floating-source circuit, and conflicting ideal voltage-source constraints. These tests help distinguish ordinary input errors from systems that cannot produce a unique or consistent operating point.

### Equivalent resistance

The Python helper calculates equivalent resistance for resistor-only networks by injecting one ampere into a selected terminal and removing one ampere at the other. The resulting voltage difference, measured in volts, equals the equivalent resistance in ohms.

This method works for networks with series, parallel, and more complex resistive connections. The helper rejects circuits containing independent voltage sources because its implementation does not deactivate or otherwise transform those sources.

## JavaScript implementation

The JavaScript file uses Node.js file APIs to write the SVG and JSON artifacts. The `Circuit`, `Resistor`, and `VoltageSource` classes keep the component model separate from the rendering and reporting functions.

The `CircuitEditor` class demonstrates event-driven model updates. Adding a component emits a `component-added` event, followed by an `analysis-updated` event containing new measurements. A browser-based editor can use the same pattern to refresh numerical panels or redraw the schematic after an edit.

Event listeners receive explicit unsubscribe functions. This allows an interactive application to remove listeners when a panel is closed or a component is removed, avoiding unnecessary retained references.

JavaScript's single-threaded event loop does not eliminate the need to manage expensive calculations. Large circuits should be analyzed in a worker or separate process so that a browser interface remains responsive. The demonstration uses synchronous matrix calculations because the example is small.

SVG labels are escaped to protect the markup structure. A full web application should also validate any imported netlist, enforce size limits, and avoid evaluating user-supplied strings as code.

## C++ case study

The C++ program models a 24 V industrial sensor distribution panel. A supply feeds a shared bus through a line resistance. Several sensor and indicator loads connect from that bus to the reference node.

The `DistributionPanel` class owns the circuit model and performs connectivity validation before analysis. The solver uses standard library containers, including vectors for matrices, sets for node uniqueness, and maps for deterministic voltage reporting.

The implementation evaluates each resistor's voltage drop, current, and dissipation. It then applies an electrical operating-limit policy to flag branches whose currents or power exceed configured thresholds.

These thresholds are demonstration settings, not universal safety ratings. Real limits depend on component ratings, ambient temperature, cooling, wiring, supply tolerances, and applicable electrical standards. A solver warning cannot replace component selection or an independent safety assessment.

The case study emphasizes the difference between calculating a circuit's operating point and deciding whether that operating point is acceptable for a particular application.

## Java implementation

The Java program uses records to define immutable resistors, voltage sources, branch measurements, analysis results, and limit assessments. The `CircuitModel` manages component membership, while `CircuitAnalysisService` handles electrical validation and numerical analysis.

The model returns copies of its component collection rather than exposing its internal mutable list. `AnalysisResult` also creates immutable copies of its voltage map and measurement lists. These decisions reduce accidental changes to a completed analysis result.

`ElectricalPolicy` represents operating-limit rules separately from the solver. This keeps numerical analysis independent of application-specific acceptance criteria. The same calculated result can be assessed under different policies without rebuilding the circuit.

The Java implementation uses explicit exception types for invalid models and singular systems. In a larger enterprise application, these exceptions can be translated into structured validation messages for the schematic editor or engineering review interface.

## PostgreSQL data model

The SQL script stores circuit definitions separately from their analysis results.

| Table | Purpose |
|---|---|
| `circuits` | Identifies circuit designs and their revisions. |
| `circuit_nodes` | Stores electrical node identity, ground status, and schematic coordinates. |
| `components` | Stores component type, terminal references, values, and presentation properties. |
| `analysis_runs` | Records solver type, software version, status, timestamps, and failure information. |
| `node_measurements` | Stores calculated node voltages for a specific run. |
| `branch_measurements` | Stores component voltage, current, and power measurements. |
| `schematic_exports` | Records generated SVG, JSON, or netlist artifacts. |
| `electrical_limits` | Stores configurable current, voltage, and dissipation thresholds. |

Foreign keys prevent components from referencing missing nodes or nodes belonging to a different circuit. Unique constraints prevent duplicate component names within a circuit. Check constraints reject invalid values and inconsistent analysis states that can be checked within a single row.

The partial unique index on `circuit_nodes` permits at most one node marked as ground per circuit. A trigger verifies that the ground node's name agrees with the circuit configuration, because a standard row-level check constraint cannot directly compare values in another table.

The analysis tables preserve results from different circuit revisions. This supports comparison between revisions without overwriting historical measurements. A solver application should capture the exact circuit revision used for a run and insert all associated measurements in a single transaction.

The reporting views expose the component inventory, latest analysis status, and resistor power measurements. The power-report view compares recorded resistor dissipation with the stored component rating when a rating is available.

The database schema does not implement the complete electrical solver. It stores definitions and calculated results, while the Python, JavaScript, C++, or Java analysis service can perform the numerical calculations. The application must ensure that stored results correspond to the correct circuit revision and satisfy the relevant electrical equations.

## Numerical limitations and validation

Gaussian elimination has cubic time complexity, approximately \(O(n^3)\), and dense matrix storage requires \(O(n^2)\) memory for a system with \(n\) unknowns. This is acceptable for small demonstrations but inefficient for large sparse circuit networks.

A practical circuit simulator should use sparse matrix representations, appropriate numerical factorization methods, and residual checks. The matrix condition number is also important: a mathematically solvable circuit can still produce inaccurate numerical results when its equations are poorly conditioned.

The examples primarily target linear DC resistive circuits. Capacitors and inductors are represented in the SQL component vocabulary, but the provided solvers do not implement their full behavior. AC analysis requires frequency-dependent impedances, while transient analysis requires time-dependent equations and suitable integration methods. Nonlinear devices such as diodes require iterative nonlinear solution techniques.

Connectivity alone is insufficient to guarantee a valid operating point. Conflicting ideal voltage sources can impose inconsistent constraints, while ideal source configurations may produce non-unique source currents. A complete validator must check the actual equation system, not just whether all nodes appear connected.

## Production engineering considerations

A production implementation should treat the circuit definition as the source of truth and derive drawings, netlists, reports, and simulation results from that definition. It should also distinguish design revisions, solver versions, analysis configurations, and exported artifact versions.

Circuit imports require validation of component values, terminal references, duplicate identifiers, file sizes, and supported component types. SVG output must escape untrusted text. Exported files should be associated with the exact revision that produced them.

Numerical validation should include matrix residuals, current balance at each node, voltage-source constraint checks, and power conservation. Tolerances should be selected for the scale and conditioning of the circuit rather than chosen as arbitrary universal constants.

Finally, the distinction between a schematic, an electrical simulation, and a physical implementation must remain explicit. A drawing communicates the model. A solver predicts its behavior under defined assumptions. Hardware validation establishes whether the physical circuit performs safely and reliably under real operating conditions.
