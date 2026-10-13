import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeSet;

/**
 * Circuit Visualization and Analysis
 *
 * Enterprise-oriented DC circuit modeling with:
 * - Explicit component types and immutable component definitions.
 * - A service for circuit validation and nodal analysis.
 * - Electrical operating-limit policies.
 * - SVG schematic export and analysis reports.
 * - Power-conservation checks and structured exceptions.
 *
 * Requires Java 17 or later.
 * Run: javac CircuitVisualization.java && java CircuitVisualization
 */
public class CircuitVisualization {

    private static final double EPSILON = 1e-12;

    private CircuitVisualization() {
    }

    interface Component {
        String name();
        String firstNode();
        String secondNode();
    }

    record Resistor(String name, String firstNode, String secondNode,
                    double resistanceOhms) implements Component {

        Resistor {
            requireName(name);
            requireNode(firstNode);
            requireNode(secondNode);

            if (firstNode.equals(secondNode)) {
                throw new CircuitException(
                    name + ": terminals must refer to different nodes.");
            }
            if (!Double.isFinite(resistanceOhms) || resistanceOhms <= 0) {
                throw new CircuitException(
                    name + ": resistance must be finite and positive.");
            }
        }
    }

    record VoltageSource(String name, String firstNode, String secondNode,
                         double voltage) implements Component {

        VoltageSource {
            requireName(name);
            requireNode(firstNode);
            requireNode(secondNode);

            if (firstNode.equals(secondNode)) {
                throw new CircuitException(
                    name + ": terminals must refer to different nodes.");
            }
            if (!Double.isFinite(voltage)) {
                throw new CircuitException(name + ": invalid voltage.");
            }
        }
    }

    static final class CircuitException extends RuntimeException {
        CircuitException(String message) {
            super(message);
        }
    }

    record BranchMeasurement(
        String component,
        double voltage,
        double current,
        double power
    ) {
    }

    record AnalysisResult(
        Map<String, Double> nodeVoltages,
        List<BranchMeasurement> resistorMeasurements,
        List<BranchMeasurement> sourceMeasurements,
        double resistorPower,
        double sourcePower
    ) {
        AnalysisResult {
            nodeVoltages = Collections.unmodifiableMap(
                new LinkedHashMap<>(nodeVoltages));
            resistorMeasurements = List.copyOf(resistorMeasurements);
            sourceMeasurements = List.copyOf(sourceMeasurements);
        }
    }

    static final class CircuitModel {
        private final String name;
        private final String ground;
        private final List<Component> components = new ArrayList<>();

        CircuitModel(String name, String ground) {
            requireName(name);
            requireNode(ground);
            this.name = name;
            this.ground = ground;
        }

        CircuitModel add(Component component) {
            Objects.requireNonNull(component, "component");

            boolean duplicate = components.stream()
                .anyMatch(existing -> existing.name().equals(component.name()));

            if (duplicate) {
                throw new CircuitException(
                    "Duplicate component name: " + component.name());
            }

            components.add(component);
            return this;
        }

        String name() {
            return name;
        }

        String ground() {
            return ground;
        }

        List<Component> components() {
            return List.copyOf(components);
        }

        List<String> nodes() {
            TreeSet<String> result = new TreeSet<>();
            for (Component component : components) {
                result.add(component.firstNode());
                result.add(component.secondNode());
            }
            return List.copyOf(result);
        }
    }

    static final class CircuitAnalysisService {

        AnalysisResult analyze(CircuitModel circuit) {
            validateConnectivity(circuit);

            List<String> nodes = circuit.nodes();
            List<String> unknownNodes = nodes.stream()
                .filter(node -> !node.equals(circuit.ground()))
                .toList();

            List<Resistor> resistors = circuit.components().stream()
                .filter(Resistor.class::isInstance)
                .map(Resistor.class::cast)
                .toList();

            List<VoltageSource> sources = circuit.components().stream()
                .filter(VoltageSource.class::isInstance)
                .map(VoltageSource.class::cast)
                .toList();

            Map<String, Integer> index = new LinkedHashMap<>();
            for (int i = 0; i < unknownNodes.size(); i++) {
                index.put(unknownNodes.get(i), i);
            }

            int nodeCount = unknownNodes.size();
            int dimension = nodeCount + sources.size();
            double[][] matrix = new double[dimension][dimension];
            double[] rhs = new double[dimension];

            for (Resistor resistor : resistors) {
                stampConductance(
                    matrix, index, circuit.ground(),
                    resistor.firstNode(), resistor.secondNode(),
                    1.0 / resistor.resistanceOhms());
            }

            for (int i = 0; i < sources.size(); i++) {
                VoltageSource source = sources.get(i);
                int currentIndex = nodeCount + i;

                if (!source.firstNode().equals(circuit.ground())) {
                    int p = index.get(source.firstNode());
                    matrix[p][currentIndex] += 1;
                    matrix[currentIndex][p] += 1;
                }

                if (!source.secondNode().equals(circuit.ground())) {
                    int n = index.get(source.secondNode());
                    matrix[n][currentIndex] -= 1;
                    matrix[currentIndex][n] -= 1;
                }

                rhs[currentIndex] = source.voltage();
            }

            double[] solution = LinearSystem.solve(matrix, rhs);
            Map<String, Double> voltages = new LinkedHashMap<>();
            voltages.put(circuit.ground(), 0.0);

            for (int i = 0; i < nodeCount; i++) {
                voltages.put(unknownNodes.get(i), solution[i]);
            }

            List<BranchMeasurement> resistorMeasurements = new ArrayList<>();
            List<BranchMeasurement> sourceMeasurements = new ArrayList<>();
            double resistorPower = 0;
            double sourcePower = 0;

            for (Resistor resistor : resistors) {
                double voltage = voltages.get(resistor.firstNode())
                    - voltages.get(resistor.secondNode());
                double current = voltage / resistor.resistanceOhms();
                double power = voltage * current;

                resistorMeasurements.add(new BranchMeasurement(
                    resistor.name(), voltage, current, power));
                resistorPower += power;
            }

            for (int i = 0; i < sources.size(); i++) {
                VoltageSource source = sources.get(i);
                double current = solution[nodeCount + i];
                double power = source.voltage() * current;

                sourceMeasurements.add(new BranchMeasurement(
                    source.name(), source.voltage(), current, power));
                sourcePower += power;
            }

            double scale = Math.max(1.0, Math.abs(resistorPower));
            if (Math.abs(resistorPower + sourcePower) > 1e-7 * scale) {
                throw new CircuitException(
                    "Power balance failed. Verify circuit constraints.");
            }

            return new AnalysisResult(
                voltages, resistorMeasurements, sourceMeasurements,
                resistorPower, sourcePower);
        }

        private void validateConnectivity(CircuitModel circuit) {
            List<String> nodes = circuit.nodes();
            if (circuit.components().isEmpty()) {
                throw new CircuitException("The circuit is empty.");
            }
            if (!nodes.contains(circuit.ground())) {
                throw new CircuitException("Reference node is missing.");
            }

            Map<String, List<String>> adjacency = new LinkedHashMap<>();
            for (String node : nodes) {
                adjacency.put(node, new ArrayList<>());
            }

            for (Component component : circuit.components()) {
                adjacency.get(component.firstNode())
                    .add(component.secondNode());
                adjacency.get(component.secondNode())
                    .add(component.firstNode());
            }

            TreeSet<String> visited = new TreeSet<>();
            List<String> queue = new ArrayList<>();
            visited.add(circuit.ground());
            queue.add(circuit.ground());

            for (int head = 0; head < queue.size(); head++) {
                String current = queue.get(head);
                for (String next : adjacency.get(current)) {
                    if (visited.add(next)) {
                        queue.add(next);
                    }
                }
            }

            if (visited.size() != nodes.size()) {
                throw new CircuitException(
                    "Some nodes are disconnected from the reference node.");
            }
        }

        private void stampConductance(
            double[][] matrix,
            Map<String, Integer> index,
            String ground,
            String a,
            String b,
            double conductance
        ) {
            if (!a.equals(ground)) matrix[index.get(a)][index.get(a)] += conductance;
            if (!b.equals(ground)) matrix[index.get(b)][index.get(b)] += conductance;

            if (!a.equals(ground) && !b.equals(ground)) {
                int ia = index.get(a);
                int ib = index.get(b);
                matrix[ia][ib] -= conductance;
                matrix[ib][ia] -= conductance;
            }
        }
    }

    static final class LinearSystem {
        private LinearSystem() {
        }

        static double[] solve(double[][] input, double[] rightHandSide) {
            int n = rightHandSide.length;
            if (n == 0 || input.length != n) {
                throw new CircuitException("Invalid matrix dimensions.");
            }

            double[][] matrix = new double[n][n + 1];
            for (int i = 0; i < n; i++) {
                if (input[i].length != n) {
                    throw new CircuitException("Matrix must be square.");
                }
                System.arraycopy(input[i], 0, matrix[i], 0, n);
                matrix[i][n] = rightHandSide[i];
            }

            for (int column = 0; column < n; column++) {
                int pivot = column;
                for (int row = column + 1; row < n; row++) {
                    if (Math.abs(matrix[row][column]) >
                        Math.abs(matrix[pivot][column])) {
                        pivot = row;
                    }
                }

                if (Math.abs(matrix[pivot][column]) < EPSILON) {
                    throw new CircuitException(
                        "Singular matrix: operating point is not unique.");
                }

                double[] temporary = matrix[column];
                matrix[column] = matrix[pivot];
                matrix[pivot] = temporary;

                double divisor = matrix[column][column];
                for (int j = column; j <= n; j++) {
                    matrix[column][j] /= divisor;
                }

                for (int row = 0; row < n; row++) {
                    if (row == column) continue;
                    double factor = matrix[row][column];
                    for (int j = column; j <= n; j++) {
                        matrix[row][j] -= factor * matrix[column][j];
                    }
                }
            }

            double[] solution = new double[n];
            for (int i = 0; i < n; i++) {
                solution[i] = matrix[i][n];
                if (!Double.isFinite(solution[i])) {
                    throw new CircuitException("Non-finite solution.");
                }
            }
            return solution;
        }
    }

    enum Severity {
        NORMAL, WARNING, CRITICAL
    }

    record LimitAssessment(
        String component,
        Severity severity,
        String explanation
    ) {
    }

    static final class ElectricalPolicy {
        private final double maximumCurrent;
        private final double maximumDissipation;

        ElectricalPolicy(double maximumCurrent, double maximumDissipation) {
            if (!Double.isFinite(maximumCurrent) || maximumCurrent <= 0 ||
                !Double.isFinite(maximumDissipation) ||
                maximumDissipation <= 0) {
                throw new CircuitException("Invalid electrical limits.");
            }
            this.maximumCurrent = maximumCurrent;
            this.maximumDissipation = maximumDissipation;
        }

        List<LimitAssessment> evaluate(AnalysisResult result) {
            List<LimitAssessment> assessments = new ArrayList<>();

            for (BranchMeasurement measurement : result.resistorMeasurements()) {
                if (Math.abs(measurement.current()) > maximumCurrent ||
                    measurement.power() > maximumDissipation) {
                    assessments.add(new LimitAssessment(
                        measurement.component(), Severity.CRITICAL,
                        "Current or resistor dissipation exceeds the configured limit."));
                } else {
                    assessments.add(new LimitAssessment(
                        measurement.component(), Severity.NORMAL,
                        "Within configured model limits."));
                }
            }
            return List.copyOf(assessments);
        }
    }

    static final class SvgRenderer {
        String render(CircuitModel circuit, AnalysisResult result) {
            StringBuilder svg = new StringBuilder();
            int rowHeight = 90;
            int height = Math.max(200, 110 + rowHeight * circuit.components().size());

            svg.append("<svg xmlns=\"http://www.w3.org/2000/svg\" ")
               .append("width=\"900\" height=\"").append(height)
               .append("\" viewBox=\"0 0 900 ").append(height).append("\">")
               .append("<rect width=\"100%\" height=\"100%\" fill=\"#101820\"/>")
               .append("<style>text{font-family:Arial;fill:#fff}")
               .append(".wire{stroke:#85d9ff;stroke-width:2.5;fill:none}")
               .append(".part{stroke:#ffc857;stroke-width:3;fill:none}")
               .append("</style>")
               .append("<text x=\"25\" y=\"35\" font-size=\"22\">")
               .append(xml(circuit.name())).append("</text>");

            int row = 0;
            for (Component component : circuit.components()) {
                int y = 80 + row++ * rowHeight;
                String a = component.firstNode();
                String b = component.secondNode();

                svg.append("<text x=\"25\" y=\"").append(y + 5)
                   .append("\" font-size=\"15\">").append(xml(component.name()))
                   .append("</text>")
                   .append("<line class=\"wire\" x1=\"170\" y1=\"").append(y)
                   .append("\" x2=\"340\" y2=\"").append(y).append("\"/>");

                if (component instanceof Resistor resistor) {
                    svg.append("<rect class=\"part\" x=\"340\" y=\"")
                       .append(y - 14).append("\" width=\"180\" height=\"28\"/>")
                       .append("<text x=\"430\" y=\"").append(y - 21)
                       .append("\" text-anchor=\"middle\" font-size=\"13\">")
                       .append(resistor.resistanceOhms()).append(" Ω</text>");
                } else if (component instanceof VoltageSource source) {
                    svg.append("<circle class=\"part\" cx=\"430\" cy=\"")
                       .append(y).append("\" r=\"28\"/>")
                       .append("<text x=\"430\" y=\"").append(y + 5)
                       .append("\" text-anchor=\"middle\" font-size=\"13\">")
                       .append(source.voltage()).append(" V</text>");
                }

                svg.append("<line class=\"wire\" x1=\"520\" y1=\"").append(y)
                   .append("\" x2=\"690\" y2=\"").append(y).append("\"/>")
                   .append("<text x=\"170\" y=\"").append(y + 22)
                   .append("\" font-size=\"12\">").append(xml(a)).append("</text>")
                   .append("<text x=\"690\" y=\"").append(y + 22)
                   .append("\" font-size=\"12\">").append(xml(b)).append("</text>");
            }

            svg.append("</svg>");
            return svg.toString();
        }

        private String xml(String value) {
            return value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&apos;");
        }
    }

    private static void requireName(String value) {
        if (value == null || value.isBlank()) {
            throw new CircuitException("Names cannot be empty.");
        }
    }

    private static void requireNode(String value) {
        if (value == null || value.isBlank()) {
            throw new CircuitException("Node identifiers cannot be empty.");
        }
    }

    public static void main(String[] args) throws Exception {
        CircuitModel circuit = new CircuitModel(
            "Enterprise Building Sensor Circuit", "0");

        circuit.add(new VoltageSource("V_SUPPLY", "bus", "0", 12.0))
            .add(new Resistor("R_FEED", "bus", "sense", 1000.0))
            .add(new Resistor("R_SENSOR", "sense", "0", 2000.0))
            .add(new Resistor("R_INPUT", "sense", "0", 10000.0));

        CircuitAnalysisService service = new CircuitAnalysisService();
        AnalysisResult result = service.analyze(circuit);

        System.out.println("Circuit: " + circuit.name());
        System.out.println("\nNode voltages");
        result.nodeVoltages().forEach((node, voltage) ->
            System.out.printf("%-12s %.5f V%n", node, voltage));

        System.out.println("\nResistor measurements");
        result.resistorMeasurements().forEach(branch ->
            System.out.printf("%-14s V=%9.5f V I=%9.5f A P=%9.5f W%n",
                branch.component(), branch.voltage(),
                branch.current(), branch.power()));

        System.out.printf("%nResistor power: %.6f W%n", result.resistorPower());
        System.out.printf("Source power:   %.6f W%n", result.sourcePower());

        ElectricalPolicy policy = new ElectricalPolicy(0.02, 0.25);
        System.out.println("\nLimit assessment");
        for (LimitAssessment assessment : policy.evaluate(result)) {
            System.out.printf("%-14s %-8s %s%n",
                assessment.component(), assessment.severity(),
                assessment.explanation());
        }

        java.nio.file.Files.writeString(
            java.nio.file.Path.of("circuit_schematic.svg"),
            new SvgRenderer().render(circuit, result));

        System.out.println("\nGenerated circuit_schematic.svg");
    }
}
