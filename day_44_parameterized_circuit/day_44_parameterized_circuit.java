import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.HashSet;

/**
 * Enterprise-style parameterized quantum circuit configuration and evaluation.
 *
 * Java 17 or later. No external dependencies are required.
 */
public class ParameterizedCircuitEnterprise {

    enum RotationAxis {
        X, Y, Z
    }

    enum GateKind {
        HADAMARD, ROTATION, CNOT
    }

    record CircuitParameter(String name, String purpose) {
        CircuitParameter {
            if (name == null || !name.matches("[A-Za-z_][A-Za-z0-9_]*")) {
                throw new IllegalArgumentException("Invalid parameter name.");
            }
            if (purpose == null || purpose.isBlank()) {
                throw new IllegalArgumentException("Parameter purpose is required.");
            }
        }
    }

    interface Angle {
        double evaluate(Map<String, Double> bindings);

        Set<String> parameterNames();

        String describe();
    }

    record ConstantAngle(double value) implements Angle {
        ConstantAngle {
            requireFinite(value);
        }

        @Override
        public double evaluate(Map<String, Double> bindings) {
            return value;
        }

        @Override
        public Set<String> parameterNames() {
            return Set.of();
        }

        @Override
        public String describe() {
            return Double.toString(value);
        }
    }

    record ParameterAngle(String name) implements Angle {
        ParameterAngle {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Parameter name is required.");
            }
        }

        @Override
        public double evaluate(Map<String, Double> bindings) {
            Double value = bindings.get(name);
            if (value == null) {
                throw new IllegalArgumentException("Unbound parameter: " + name);
            }
            return requireFinite(value);
        }

        @Override
        public Set<String> parameterNames() {
            return Set.of(name);
        }

        @Override
        public String describe() {
            return name;
        }
    }

    record BinaryAngle(String operator, Angle left, Angle right) implements Angle {
        BinaryAngle {
            Objects.requireNonNull(left);
            Objects.requireNonNull(right);
            if (!operator.equals("+") && !operator.equals("*")) {
                throw new IllegalArgumentException("Unsupported angle operator.");
            }
        }

        @Override
        public double evaluate(Map<String, Double> bindings) {
            double a = left.evaluate(bindings);
            double b = right.evaluate(bindings);
            return requireFinite(operator.equals("+") ? a + b : a * b);
        }

        @Override
        public Set<String> parameterNames() {
            Set<String> names = new HashSet<>(left.parameterNames());
            names.addAll(right.parameterNames());
            return Collections.unmodifiableSet(names);
        }

        @Override
        public String describe() {
            return "(" + left.describe() + " " + operator + " " + right.describe() + ")";
        }
    }

    record Gate(
            GateKind kind,
            int qubit,
            RotationAxis axis,
            Angle angle,
            int target
    ) {
        Gate {
            Objects.requireNonNull(kind);
            if (qubit < 0) {
                throw new IllegalArgumentException("Qubit index cannot be negative.");
            }
            if (kind == GateKind.ROTATION && (axis == null || angle == null)) {
                throw new IllegalArgumentException("Rotation requires an axis and angle.");
            }
            if (kind == GateKind.CNOT && target < 0) {
                throw new IllegalArgumentException("CNOT requires a target qubit.");
            }
        }

        String describe() {
            return switch (kind) {
                case HADAMARD -> "H q" + qubit;
                case ROTATION -> "R" + axis + " q" + qubit + " " + angle.describe();
                case CNOT -> "CNOT q" + qubit + " -> q" + target;
            };
        }
    }

    static final class CircuitTemplate {
        private final String name;
        private final int qubitCount;
        private final Map<String, CircuitParameter> parameters = new LinkedHashMap<>();
        private final List<Gate> gates = new ArrayList<>();

        CircuitTemplate(String name, int qubitCount) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Circuit name is required.");
            }
            if (qubitCount < 1 || qubitCount > 12) {
                throw new IllegalArgumentException("Use 1 through 12 qubits.");
            }
            this.name = name;
            this.qubitCount = qubitCount;
        }

        Angle parameter(String name, String purpose) {
            CircuitParameter candidate = new CircuitParameter(name, purpose);
            CircuitParameter existing = parameters.putIfAbsent(name, candidate);
            if (existing != null && !existing.equals(candidate)) {
                throw new IllegalArgumentException(
                    "Parameter name reused with a different purpose: " + name);
            }
            return new ParameterAngle(name);
        }

        void hadamard(int qubit) {
            validateQubit(qubit);
            gates.add(new Gate(GateKind.HADAMARD, qubit, null, null, -1));
        }

        void rotate(RotationAxis axis, int qubit, Angle angle) {
            validateQubit(qubit);
            Objects.requireNonNull(axis);
            Objects.requireNonNull(angle);
            for (String name : angle.parameterNames()) {
                if (!parameters.containsKey(name)) {
                    throw new IllegalArgumentException(
                        "Declare parameter before use: " + name);
                }
            }
            gates.add(new Gate(GateKind.ROTATION, qubit, axis, angle, -1));
        }

        void cnot(int control, int target) {
            validateQubit(control);
            validateQubit(target);
            if (control == target) {
                throw new IllegalArgumentException("CNOT qubits must differ.");
            }
            gates.add(new Gate(GateKind.CNOT, control, null, null, target));
        }

        private void validateQubit(int qubit) {
            if (qubit < 0 || qubit >= qubitCount) {
                throw new IndexOutOfBoundsException("Invalid qubit: " + qubit);
            }
        }

        BoundCircuit bind(Map<String, Double> supplied) {
            Objects.requireNonNull(supplied);
            Set<String> unknown = new HashSet<>(supplied.keySet());
            unknown.removeAll(parameters.keySet());
            if (!unknown.isEmpty()) {
                throw new IllegalArgumentException("Unknown parameters: " + unknown);
            }

            Map<String, Double> values = new LinkedHashMap<>();
            for (String name : parameters.keySet()) {
                Double value = supplied.get(name);
                if (value == null) {
                    throw new IllegalArgumentException("Missing parameter: " + name);
                }
                values.put(name, requireFinite(value));
            }

            List<Gate> evaluated = new ArrayList<>();
            for (Gate gate : gates) {
                if (gate.kind() == GateKind.ROTATION) {
                    double angle = gate.angle().evaluate(values);
                    evaluated.add(new Gate(
                        GateKind.ROTATION, gate.qubit(), gate.axis(),
                        new ConstantAngle(angle), -1));
                } else {
                    evaluated.add(gate);
                }
            }
            return new BoundCircuit(name, qubitCount, evaluated, values);
        }

        List<String> describe() {
            List<String> descriptions = new ArrayList<>();
            for (int index = 0; index < gates.size(); index++) {
                descriptions.add(index + ": " + gates.get(index).describe());
            }
            return descriptions;
        }
    }

    record BoundCircuit(
            String name,
            int qubitCount,
            List<Gate> gates,
            Map<String, Double> bindings
    ) {
        BoundCircuit {
            gates = List.copyOf(gates);
            bindings = Map.copyOf(bindings);
        }

        double[] probabilities() {
            int dimension = 1 << qubitCount;
            double[] real = new double[dimension];
            double[] imaginary = new double[dimension];
            real[0] = 1.0;

            for (Gate gate : gates) {
                if (gate.kind() == GateKind.HADAMARD) {
                    applyHadamard(real, imaginary, gate.qubit());
                } else if (gate.kind() == GateKind.CNOT) {
                    applyCnot(real, imaginary, gate.qubit(), gate.target());
                } else {
                    double angle = gate.angle().evaluate(bindings);
                    applyRotation(real, imaginary, gate.axis(), gate.qubit(), angle);
                }
            }

            double[] probabilities = new double[dimension];
            double norm = 0.0;
            for (int index = 0; index < dimension; index++) {
                probabilities[index] = real[index] * real[index]
                    + imaginary[index] * imaginary[index];
                norm += probabilities[index];
            }
            if (Math.abs(norm - 1.0) > 1e-8) {
                throw new ArithmeticException("State normalization invariant failed.");
            }
            return probabilities;
        }

        double expectationZ(int qubit) {
            if (qubit < 0 || qubit >= qubitCount) {
                throw new IndexOutOfBoundsException("Invalid measurement qubit.");
            }
            double[] probabilities = probabilities();
            double result = 0.0;
            for (int index = 0; index < probabilities.length; index++) {
                result += (((index >> qubit) & 1) == 0 ? 1.0 : -1.0)
                    * probabilities[index];
            }
            return result;
        }
    }

    private static void applyHadamard(double[] real, double[] imaginary, int qubit) {
        int stride = 1 << qubit;
        double scale = 1.0 / Math.sqrt(2.0);
        for (int base = 0; base < real.length; base += 2 * stride) {
            for (int offset = 0; offset < stride; offset++) {
                int first = base + offset;
                int second = first + stride;
                double ar = real[first], ai = imaginary[first];
                double br = real[second], bi = imaginary[second];
                real[first] = (ar + br) * scale;
                imaginary[first] = (ai + bi) * scale;
                real[second] = (ar - br) * scale;
                imaginary[second] = (ai - bi) * scale;
            }
        }
    }

    private static void applyRotation(
            double[] real, double[] imaginary, RotationAxis axis,
            int qubit, double angle) {
        double c = Math.cos(angle / 2.0);
        double s = Math.sin(angle / 2.0);
        int stride = 1 << qubit;

        for (int base = 0; base < real.length; base += 2 * stride) {
            for (int offset = 0; offset < stride; offset++) {
                int first = base + offset;
                int second = first + stride;
                double ar = real[first], ai = imaginary[first];
                double br = real[second], bi = imaginary[second];

                switch (axis) {
                    case X -> {
                        real[first] = c * ar + s * bi;
                        imaginary[first] = c * ai - s * br;
                        real[second] = c * br + s * ai;
                        imaginary[second] = c * bi - s * ar;
                    }
                    case Y -> {
                        real[first] = c * ar - s * br;
                        imaginary[first] = c * ai - s * bi;
                        real[second] = s * ar + c * br;
                        imaginary[second] = s * ai + c * bi;
                    }
                    case Z -> {
                        real[first] = c * ar + s * ai;
                        imaginary[first] = c * ai - s * ar;
                        real[second] = c * br - s * bi;
                        imaginary[second] = c * bi + s * br;
                    }
                }
            }
        }
    }

    private static void applyCnot(
            double[] real, double[] imaginary, int control, int target) {
        int controlMask = 1 << control;
        int targetMask = 1 << target;
        for (int index = 0; index < real.length; index++) {
            if ((index & controlMask) != 0 && (index & targetMask) == 0) {
                int other = index | targetMask;
                double temporary = real[index];
                real[index] = real[other];
                real[other] = temporary;
                temporary = imaginary[index];
                imaginary[index] = imaginary[other];
                imaginary[other] = temporary;
            }
        }
    }

    private static double requireFinite(double value) {
        if (!Double.isFinite(value)) {
            throw new IllegalArgumentException("Expected a finite numeric value.");
        }
        return value;
    }

    public static void main(String[] args) {
        CircuitTemplate template = new CircuitTemplate("equipment-phase-calibration", 2);

        Angle sensorPhase = template.parameter("sensorPhase", "Measured input phase");
        Angle driveStrength = template.parameter("driveStrength", "Trainable drive");
        Angle compensation = template.parameter("compensation", "Calibration offset");

        template.hadamard(0);
        template.rotate(RotationAxis.Y, 0, sensorPhase);
        template.rotate(RotationAxis.X, 1, driveStrength);
        template.cnot(0, 1);
        template.rotate(
            RotationAxis.Z, 0,
            new BinaryAngle("+", compensation,
                new BinaryAngle("*", driveStrength, new ConstantAngle(0.5))));
        template.rotate(
            RotationAxis.Y, 1,
            new BinaryAngle("*", sensorPhase, new ConstantAngle(2.0)));

        System.out.println("Circuit: " + template.describe());

        Map<String, Double> calibration = Map.of(
            "sensorPhase", 0.65,
            "driveStrength", -0.35,
            "compensation", 0.12
        );

        BoundCircuit executable = template.bind(calibration);
        double[] probabilities = executable.probabilities();

        System.out.println("\nCalibrated output probabilities");
        for (int index = 0; index < probabilities.length; index++) {
            System.out.printf("Basis state %2s: %.6f%n",
                Integer.toBinaryString(index | (1 << template.qubits())),
                probabilities[index]);
        }
        System.out.printf("Expectation Z(q0): %.6f%n", executable.expectationZ(0));
        System.out.printf("Expectation Z(q1): %.6f%n", executable.expectationZ(1));

        try {
            template.bind(Map.of("sensorPhase", 0.2));
        } catch (IllegalArgumentException exception) {
            System.out.println("Rejected incomplete configuration: "
                + exception.getMessage());
        }

        try {
            template.bind(Map.of(
                "sensorPhase", 0.2,
                "driveStrength", 0.3,
                "compensation", Double.NaN
            ));
        } catch (IllegalArgumentException exception) {
            System.out.println("Rejected invalid configuration: "
                + exception.getMessage());
        }
    }
}
