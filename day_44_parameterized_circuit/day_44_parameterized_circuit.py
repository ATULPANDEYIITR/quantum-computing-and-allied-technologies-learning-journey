#!/usr/bin/env python3
"""Parameterized quantum circuits: variables, rotation gates, and parameter binding.

This executable educational simulator uses state vectors and the standard library.
It demonstrates symbolic parameters, parameterized rotations, circuit composition,
parameter binding, expectation values, finite-difference gradients, and validation.
The simulator supports small circuits and is not intended to replace a production
quantum simulator.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Mapping, Sequence


EPSILON = 1e-10


def validate_angle(angle: float) -> float:
    """Reject invalid numerical rotation angles before simulation."""
    value = float(angle)
    if not math.isfinite(value):
        raise ValueError("Rotation angles must be finite real numbers.")
    return value


@dataclass(frozen=True)
class Parameter:
    """An immutable symbolic circuit parameter identified by its name."""

    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.isidentifier():
            raise ValueError(f"Invalid parameter name: {self.name!r}")


@dataclass(frozen=True)
class Expression:
    """A small expression tree for parameter-dependent gate angles."""

    operation: str
    operands: tuple[object, ...]

    @staticmethod
    def parameter(parameter: Parameter) -> "Expression":
        return Expression("parameter", (parameter,))

    @staticmethod
    def constant(value: float) -> "Expression":
        return Expression("constant", (validate_angle(value),))

    def evaluate(self, bindings: Mapping[str, float]) -> float:
        if self.operation == "parameter":
            parameter = self.operands[0]
            assert isinstance(parameter, Parameter)
            if parameter.name not in bindings:
                raise ValueError(f"Unbound parameter: {parameter.name}")
            return validate_angle(bindings[parameter.name])

        if self.operation == "constant":
            return float(self.operands[0])

        left = self.operands[0]
        right = self.operands[1]
        assert isinstance(left, Expression)
        assert isinstance(right, Expression)
        a = left.evaluate(bindings)
        b = right.evaluate(bindings)

        if self.operation == "add":
            return validate_angle(a + b)
        if self.operation == "multiply":
            return validate_angle(a * b)
        raise ValueError(f"Unsupported expression: {self.operation}")

    def __add__(self, other: "Expression | float") -> "Expression":
        right = other if isinstance(other, Expression) else Expression.constant(other)
        return Expression("add", (self, right))

    def __mul__(self, other: "Expression | float") -> "Expression":
        right = other if isinstance(other, Expression) else Expression.constant(other)
        return Expression("multiply", (self, right))


def parameter_expression(value: Parameter | Expression | float) -> Expression:
    if isinstance(value, Expression):
        return value
    if isinstance(value, Parameter):
        return Expression.parameter(value)
    return Expression.constant(value)


@dataclass(frozen=True)
class Gate:
    """A single-qubit operation with a symbolic or constant angle."""

    name: str
    qubit: int
    angle: Expression | None = None


class ParameterizedCircuit:
    """A compact state-vector circuit supporting RX, RY, RZ, and CNOT."""

    def __init__(self, num_qubits: int, name: str = "circuit") -> None:
        if not isinstance(num_qubits, int) or isinstance(num_qubits, bool):
            raise TypeError("num_qubits must be an integer.")
        if num_qubits < 1 or num_qubits > 16:
            raise ValueError("This educational simulator supports 1 to 16 qubits.")
        self.num_qubits = num_qubits
        self.name = name
        self.gates: list[Gate] = []
        self.parameters: dict[str, Parameter] = {}

    def parameter(self, name: str) -> Parameter:
        candidate = Parameter(name)
        existing = self.parameters.get(name)
        if existing is not None:
            return existing
        self.parameters[name] = candidate
        return candidate

    def _validate_qubit(self, qubit: int) -> None:
        if not isinstance(qubit, int) or isinstance(qubit, bool):
            raise TypeError("Qubit index must be an integer.")
        if not 0 <= qubit < self.num_qubits:
            raise IndexError(f"Qubit {qubit} is outside this circuit.")

    def _rotation(
        self, name: str, qubit: int, angle: Parameter | Expression | float
    ) -> "ParameterizedCircuit":
        self._validate_qubit(qubit)
        expression = parameter_expression(angle)
        for parameter in expression_parameters(expression):
            existing = self.parameters.get(parameter.name)
            if existing is not None and existing != parameter:
                raise ValueError("Parameter identity conflict.")
            self.parameters[parameter.name] = parameter
        self.gates.append(Gate(name, qubit, expression))
        return self

    def rx(self, qubit: int, angle: Parameter | Expression | float):
        return self._rotation("RX", qubit, angle)

    def ry(self, qubit: int, angle: Parameter | Expression | float):
        return self._rotation("RY", qubit, angle)

    def rz(self, qubit: int, angle: Parameter | Expression | float):
        return self._rotation("RZ", qubit, angle)

    def h(self, qubit: int):
        self._validate_qubit(qubit)
        self.gates.append(Gate("H", qubit))
        return self

    def cnot(self, control: int, target: int):
        self._validate_qubit(control)
        self._validate_qubit(target)
        if control == target:
            raise ValueError("CNOT control and target must differ.")
        self.gates.append(Gate("CNOT", control, Expression.constant(target)))
        return self

    def bind(self, bindings: Mapping[str, float]) -> "BoundCircuit":
        unknown = set(bindings) - set(self.parameters)
        if unknown:
            raise ValueError(f"Unknown parameter names: {sorted(unknown)}")

        normalized = {
            name: validate_angle(value) for name, value in bindings.items()
        }
        missing = set(self.parameters) - set(normalized)
        if missing:
            raise ValueError(f"Missing parameter values: {sorted(missing)}")

        evaluated: list[tuple[str, int, float | None]] = []
        for gate in self.gates:
            angle = gate.angle.evaluate(normalized) if gate.angle else None
            evaluated.append((gate.name, gate.qubit, angle))
        return BoundCircuit(self.num_qubits, self.name, evaluated, normalized)

    def draw(self) -> str:
        """Return a compact operation listing that preserves symbolic expressions."""
        lines = [f"{self.name}: {self.num_qubits} qubits"]
        for index, gate in enumerate(self.gates):
            if gate.name == "CNOT":
                target = int(gate.angle.operands[0]) if gate.angle else -1
                detail = f"control=q{gate.qubit}, target=q{target}"
            elif gate.angle is not None:
                detail = f"q{gate.qubit}, angle={gate.angle}"
            else:
                detail = f"q{gate.qubit}"
            lines.append(f"{index:02d} {gate.name} {detail}")
        return "\n".join(lines)


def expression_parameters(expression: Expression) -> set[Parameter]:
    if expression.operation == "parameter":
        parameter = expression.operands[0]
        assert isinstance(parameter, Parameter)
        return {parameter}
    result: set[Parameter] = set()
    for operand in expression.operands:
        if isinstance(operand, Expression):
            result.update(expression_parameters(operand))
    return result


class BoundCircuit:
    """A circuit with every symbolic angle evaluated."""

    def __init__(
        self,
        num_qubits: int,
        name: str,
        gates: Sequence[tuple[str, int, float | None]],
        bindings: Mapping[str, float],
    ) -> None:
        self.num_qubits = num_qubits
        self.name = name
        self.gates = tuple(gates)
        self.bindings = dict(bindings)

    def simulate(self) -> list[complex]:
        state = [0j] * (1 << self.num_qubits)
        state[0] = 1 + 0j

        for name, qubit, angle in self.gates:
            if name == "CNOT":
                assert angle is not None
                state = apply_cnot(state, qubit, int(angle), self.num_qubits)
            elif name == "H":
                state = apply_h(state, qubit, self.num_qubits)
            else:
                assert angle is not None
                state = apply_rotation(state, name, qubit, angle, self.num_qubits)

        norm = sum(abs(amplitude) ** 2 for amplitude in state)
        if not math.isclose(norm, 1.0, abs_tol=1e-8):
            raise ArithmeticError(f"State norm drifted to {norm}.")
        return state

    def probabilities(self) -> dict[str, float]:
        return {
            format(index, f"0{self.num_qubits}b"): abs(amplitude) ** 2
            for index, amplitude in enumerate(self.simulate())
        }

    def expectation_z(self, qubit: int) -> float:
        if not 0 <= qubit < self.num_qubits:
            raise IndexError("Invalid measurement qubit.")
        state = self.simulate()
        expectation = 0.0
        for index, amplitude in enumerate(state):
            bit = (index >> qubit) & 1
            expectation += (1.0 if bit == 0 else -1.0) * abs(amplitude) ** 2
        return expectation

    def expectation_zz(self, first: int, second: int) -> float:
        if first == second:
            raise ValueError("ZZ expectation requires distinct qubits.")
        if not (0 <= first < self.num_qubits and 0 <= second < self.num_qubits):
            raise IndexError("Invalid measurement qubit.")
        expectation = 0.0
        for index, amplitude in enumerate(self.simulate()):
            parity = ((index >> first) ^ (index >> second)) & 1
            expectation += (1.0 if parity == 0 else -1.0) * abs(amplitude) ** 2
        return expectation


def apply_rotation(
    state: list[complex], name: str, qubit: int, angle: float, num_qubits: int
) -> list[complex]:
    """Apply the standard half-angle single-qubit rotation convention."""
    c = math.cos(angle / 2)
    s = math.sin(angle / 2)
    result = state.copy()
    stride = 1 << qubit

    for base in range(0, len(state), stride * 2):
        for offset in range(stride):
            i0 = base + offset
            i1 = i0 + stride
            a, b = state[i0], state[i1]

            if name == "RX":
                result[i0] = c * a - 1j * s * b
                result[i1] = -1j * s * a + c * b
            elif name == "RY":
                result[i0] = c * a - s * b
                result[i1] = s * a + c * b
            elif name == "RZ":
                result[i0] = complex(math.cos(angle / 2), -math.sin(angle / 2)) * a
                result[i1] = complex(math.cos(angle / 2), math.sin(angle / 2)) * b
            else:
                raise ValueError(f"Unsupported rotation gate: {name}")

    return result


def apply_h(state: list[complex], qubit: int, num_qubits: int) -> list[complex]:
    result = state.copy()
    stride = 1 << qubit
    scale = 1 / math.sqrt(2)

    for base in range(0, len(state), stride * 2):
        for offset in range(stride):
            i0 = base + offset
            i1 = i0 + stride
            a, b = state[i0], state[i1]
            result[i0] = (a + b) * scale
            result[i1] = (a - b) * scale
    return result


def apply_cnot(
    state: list[complex], control: int, target: int, num_qubits: int
) -> list[complex]:
    result = state.copy()
    control_mask = 1 << control
    target_mask = 1 << target

    # Swap amplitudes only for control=1 and target=0 to avoid double-swapping.
    for index in range(len(state)):
        if index & control_mask and not index & target_mask:
            other = index | target_mask
            result[index], result[other] = state[other], state[index]
    return result


def parameter_shift_gradient(
    circuit: ParameterizedCircuit,
    bindings: Mapping[str, float],
    objective: Callable[[BoundCircuit], float],
    parameter_name: str,
) -> float:
    """Differentiate expectations of one occurrence of a standard rotation.

    The parameter-shift rule is exact for a single occurrence of a parameter
    in a Pauli rotation with angle equal to that parameter. For expressions
    such as 2 * theta, repeated occurrences, or nonlinear objectives, the
    simple rule below is not generally the full derivative.
    """
    if parameter_name not in bindings:
        raise ValueError("A bound value is required for differentiation.")
    occurrences = [
        gate
        for gate in circuit.gates
        if gate.angle is not None
        and gate.angle.operation == "parameter"
        and gate.angle.operands[0] == circuit.parameters.get(parameter_name)
    ]
    if len(occurrences) != 1:
        raise ValueError(
            "This helper requires exactly one direct occurrence of the parameter."
        )

    shifted_plus = dict(bindings)
    shifted_minus = dict(bindings)
    shifted_plus[parameter_name] += math.pi / 2
    shifted_minus[parameter_name] -= math.pi / 2

    return 0.5 * (
        objective(circuit.bind(shifted_plus))
        - objective(circuit.bind(shifted_minus))
    )


def finite_difference_gradient(
    circuit: ParameterizedCircuit,
    bindings: Mapping[str, float],
    objective: Callable[[BoundCircuit], float],
    parameter_name: str,
    step: float = 1e-6,
) -> float:
    if step <= 0 or not math.isfinite(step):
        raise ValueError("Finite-difference step must be finite and positive.")
    if parameter_name not in bindings:
        raise ValueError("Unknown or unbound parameter.")

    plus = dict(bindings)
    minus = dict(bindings)
    plus[parameter_name] += step
    minus[parameter_name] -= step
    return (
        objective(circuit.bind(plus)) - objective(circuit.bind(minus))
    ) / (2 * step)


def build_variational_classifier() -> ParameterizedCircuit:
    """Construct a small two-qubit parameterized feature circuit."""
    circuit = ParameterizedCircuit(2, "variational-feature-circuit")
    feature = circuit.parameter("feature")
    weight = circuit.parameter("weight")
    bias = circuit.parameter("bias")

    circuit.h(0)
    circuit.ry(0, feature)
    circuit.rx(1, weight)
    circuit.cnot(0, 1)
    circuit.rz(0, bias + weight * 0.5)
    circuit.ry(1, feature * 2.0)
    return circuit


def demonstrate_validation() -> None:
    circuit = ParameterizedCircuit(1, "validation")
    theta = circuit.parameter("theta")
    circuit.rx(0, theta)

    invalid_cases = [
        ("missing binding", lambda: circuit.bind({})),
        ("unknown binding", lambda: circuit.bind({"theta": 0.2, "extra": 1.0})),
        ("non-finite binding", lambda: circuit.bind({"theta": math.inf})),
        ("invalid qubit", lambda: circuit.ry(2, 0.1)),
    ]

    for description, operation in invalid_cases:
        try:
            operation()
        except (ValueError, IndexError, TypeError) as error:
            print(f"{description}: correctly rejected ({error})")
        else:
            raise AssertionError(f"Expected rejection: {description}")


def main() -> None:
    circuit = build_variational_classifier()
    bindings = {"feature": 0.7, "weight": -0.4, "bias": 0.2}

    print(circuit.draw())
    bound = circuit.bind(bindings)
    print("\nBound parameters:", bound.bindings)
    print("Basis-state probabilities:")
    for basis_state, probability in bound.probabilities().items():
        print(f"  |{basis_state}>: {probability:.6f}")

    print(f"\nExpectation Z(q0): {bound.expectation_z(0):.6f}")
    print(f"Expectation Z(q1): {bound.expectation_z(1):.6f}")
    print(f"Expectation ZZ(q0,q1): {bound.expectation_zz(0, 1):.6f}")

    # A single direct RY occurrence allows the standard parameter-shift rule.
    gradient_circuit = ParameterizedCircuit(1, "single-rotation-gradient")
    theta = gradient_circuit.parameter("theta")
    gradient_circuit.ry(0, theta)
    gradient_bindings = {"theta": 0.8}
    objective = lambda bound_circuit: bound_circuit.expectation_z(0)

    exact_rule = parameter_shift_gradient(
        gradient_circuit, gradient_bindings, objective, "theta"
    )
    numerical = finite_difference_gradient(
        gradient_circuit, gradient_bindings, objective, "theta"
    )
    print(f"\nParameter-shift gradient: {exact_rule:.8f}")
    print(f"Finite-difference gradient: {numerical:.8f}")

    demonstrate_validation()


if __name__ == "__main__":
    main()
