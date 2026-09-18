/*
 * Operators: Hermitian and Unitary Operators
 * ===========================================
 *
 * A standalone JavaScript study file covering:
 *   - complex numbers
 *   - vectors and matrices
 *   - conjugate transpose
 *   - Hermitian operators
 *   - unitary operators
 *   - normal operators
 *   - expectation values
 *   - projectors
 *   - Pauli and quantum gates
 *   - tensor products
 *   - controlled operations
 *   - a small quantum-circuit simulation
 *
 * The file uses only standard JavaScript and is executable with Node.js.
 */

// ---------------------------------------------------------------------------
// 1. Complex numbers
// ---------------------------------------------------------------------------

class Complex {
    constructor(real = 0, imaginary = 0) {
        this.real = real;
        this.imaginary = imaginary;
    }

    add(other) {
        return new Complex(
            this.real + other.real,
            this.imaginary + other.imaginary
        );
    }

    subtract(other) {
        return new Complex(
            this.real - other.real,
            this.imaginary - other.imaginary
        );
    }

    multiply(other) {
        return new Complex(
            this.real * other.real - this.imaginary * other.imaginary,
            this.real * other.imaginary + this.imaginary * other.real
        );
    }

    scale(value) {
        return new Complex(
            this.real * value,
            this.imaginary * value
        );
    }

    conjugate() {
        return new Complex(this.real, -this.imaginary);
    }

    magnitudeSquared() {
        return (
            this.real * this.real +
            this.imaginary * this.imaginary
        );
    }

    magnitude() {
        return Math.sqrt(this.magnitudeSquared());
    }

    isCloseTo(other, tolerance = 1e-10) {
        return this.subtract(other).magnitude() <= tolerance;
    }

    toString(digits = 4) {
        const real = Math.abs(this.real) < 10 ** (-digits)
            ? 0
            : Number(this.real.toFixed(digits));

        const imaginary = Math.abs(this.imaginary) < 10 ** (-digits)
            ? 0
            : Number(this.imaginary.toFixed(digits));

        if (imaginary === 0) {
            return `${real}`;
        }

        if (real === 0) {
            return `${imaginary}i`;
        }

        const sign = imaginary >= 0 ? "+" : "-";
        return `${real}${sign}${Math.abs(imaginary)}i`;
    }
}

const C = (real, imaginary = 0) => new Complex(real, imaginary);
const ZERO = C(0);
const ONE = C(1);
const I = C(0, 1);


// ---------------------------------------------------------------------------
// 2. Matrix and vector operations
// ---------------------------------------------------------------------------

function assertRectangularMatrix(matrix) {
    if (!Array.isArray(matrix) || matrix.length === 0) {
        throw new Error("Matrix must be a non-empty array.");
    }

    const columns = matrix[0].length;

    if (columns === 0) {
        throw new Error("Matrix rows cannot be empty.");
    }

    for (const row of matrix) {
        if (!Array.isArray(row) || row.length !== columns) {
            throw new Error("Matrix must be rectangular.");
        }
    }
}

function matrixShape(matrix) {
    assertRectangularMatrix(matrix);
    return [matrix.length, matrix[0].length];
}

function cloneMatrix(matrix) {
    return matrix.map(row => row.slice());
}

function identityMatrix(size) {
    return Array.from({ length: size }, (_, row) =>
        Array.from(
            { length: size },
            (_, column) => row === column ? ONE : ZERO
        )
    );
}

function zeroMatrix(rows, columns) {
    return Array.from(
        { length: rows },
        () => Array.from({ length: columns }, () => ZERO)
    );
}

function matrixAdd(a, b) {
    const [rowsA, columnsA] = matrixShape(a);
    const [rowsB, columnsB] = matrixShape(b);

    if (rowsA !== rowsB || columnsA !== columnsB) {
        throw new Error("Matrices must have equal dimensions.");
    }

    return a.map((row, i) =>
        row.map((value, j) => value.add(b[i][j]))
    );
}

function matrixSubtract(a, b) {
    const [rowsA, columnsA] = matrixShape(a);
    const [rowsB, columnsB] = matrixShape(b);

    if (rowsA !== rowsB || columnsA !== columnsB) {
        throw new Error("Matrices must have equal dimensions.");
    }

    return a.map((row, i) =>
        row.map((value, j) => value.subtract(b[i][j]))
    );
}

function matrixMultiply(a, b) {
    const [rowsA, columnsA] = matrixShape(a);
    const [rowsB, columnsB] = matrixShape(b);

    if (columnsA !== rowsB) {
        throw new Error(
            `Cannot multiply ${rowsA}x${columnsA} by ${rowsB}x${columnsB}.`
        );
    }

    const result = zeroMatrix(rowsA, columnsB);

    for (let row = 0; row < rowsA; row++) {
        for (let column = 0; column < columnsB; column++) {
            let sum = ZERO;

            for (let k = 0; k < columnsA; k++) {
                sum = sum.add(a[row][k].multiply(b[k][column]));
            }

            result[row][column] = sum;
        }
    }

    return result;
}

function matrixVectorMultiply(matrix, vector) {
    const [rows, columns] = matrixShape(matrix);

    if (columns !== vector.length) {
        throw new Error("Matrix and vector dimensions do not agree.");
    }

    return Array.from({ length: rows }, (_, row) => {
        let sum = ZERO;

        for (let column = 0; column < columns; column++) {
            sum = sum.add(matrix[row][column].multiply(vector[column]));
        }

        return sum;
    });
}

function vectorInnerProduct(left, right) {
    if (left.length !== right.length) {
        throw new Error("Vectors must have equal dimensions.");
    }

    let sum = ZERO;

    for (let index = 0; index < left.length; index++) {
        sum = sum.add(
            left[index].conjugate().multiply(right[index])
        );
    }

    return sum;
}

function vectorNorm(vector) {
    return Math.sqrt(vectorInnerProduct(vector, vector).real);
}

function normalizeVector(vector) {
    const norm = vectorNorm(vector);

    if (norm === 0) {
        throw new Error("The zero vector cannot be normalized.");
    }

    return vector.map(value => value.scale(1 / norm));
}

function conjugateTranspose(matrix) {
    const [rows, columns] = matrixShape(matrix);

    return Array.from({ length: columns }, (_, column) =>
        Array.from(
            { length: rows },
            (_, row) => matrix[row][column].conjugate()
        )
    );
}

function matrixMaxDifference(a, b) {
    const difference = matrixSubtract(a, b);

    let maximum = 0;

    for (const row of difference) {
        for (const value of row) {
            maximum = Math.max(maximum, value.magnitude());
        }
    }

    return maximum;
}

function matricesClose(a, b, tolerance = 1e-10) {
    try {
        return matrixMaxDifference(a, b) <= tolerance;
    } catch {
        return false;
    }
}

function vectorsClose(a, b, tolerance = 1e-10) {
    if (a.length !== b.length) {
        return false;
    }

    return a.every(
        (value, index) => value.isCloseTo(b[index], tolerance)
    );
}

function formatVector(vector) {
    return `[${vector.map(value => value.toString()).join(", ")}]`;
}

function formatMatrix(matrix) {
    return matrix
        .map(row => `[ ${row.map(value => value.toString().padStart(10)).join(" ")} ]`)
        .join("\n");
}


// ---------------------------------------------------------------------------
// 3. Operator predicates
// ---------------------------------------------------------------------------

function adjoint(operator) {
    return conjugateTranspose(operator);
}

function isHermitian(operator, tolerance = 1e-10) {
    const [rows, columns] = matrixShape(operator);

    if (rows !== columns) {
        return false;
    }

    return matricesClose(operator, adjoint(operator), tolerance);
}

function isUnitary(operator, tolerance = 1e-10) {
    const [rows, columns] = matrixShape(operator);

    if (rows !== columns) {
        return false;
    }

    const operatorAdjoint = adjoint(operator);
    const identity = identityMatrix(rows);

    const left = matrixMultiply(operatorAdjoint, operator);
    const right = matrixMultiply(operator, operatorAdjoint);

    return (
        matricesClose(left, identity, tolerance) &&
        matricesClose(right, identity, tolerance)
    );
}

function isNormal(operator, tolerance = 1e-10) {
    const [rows, columns] = matrixShape(operator);

    if (rows !== columns) {
        return false;
    }

    const operatorAdjoint = adjoint(operator);

    return matricesClose(
        matrixMultiply(operatorAdjoint, operator),
        matrixMultiply(operator, operatorAdjoint),
        tolerance
    );
}


// ---------------------------------------------------------------------------
// 4. Standard quantum operators
// ---------------------------------------------------------------------------

const IDENTITY = [
    [ONE, ZERO],
    [ZERO, ONE]
];

const PAULI_X = [
    [ZERO, ONE],
    [ONE, ZERO]
];

const PAULI_Y = [
    [ZERO, C(0, -1)],
    [I, ZERO]
];

const PAULI_Z = [
    [ONE, ZERO],
    [ZERO, C(-1)]
];

const HADAMARD = [
    [C(1 / Math.sqrt(2)), C(1 / Math.sqrt(2))],
    [C(1 / Math.sqrt(2)), C(-1 / Math.sqrt(2))]
];

function phaseGate(theta) {
    return [
        [ONE, ZERO],
        [ZERO, C(Math.cos(theta), Math.sin(theta))]
    ];
}

function rotationX(theta) {
    const half = theta / 2;

    return [
        [C(Math.cos(half)), C(0, -Math.sin(half))],
        [C(0, -Math.sin(half)), C(Math.cos(half))]
    ];
}

function rotationY(theta) {
    const half = theta / 2;

    return [
        [C(Math.cos(half)), C(-Math.sin(half))],
        [C(Math.sin(half)), C(Math.cos(half))]
    ];
}

function rotationZ(theta) {
    const half = theta / 2;

    return [
        [C(Math.cos(half), -Math.sin(half)), ZERO],
        [ZERO, C(Math.cos(half), Math.sin(half))]
    ];
}


// ---------------------------------------------------------------------------
// 5. Quantum states and observables
// ---------------------------------------------------------------------------

function basisState(index, dimension) {
    if (index < 0 || index >= dimension) {
        throw new Error("Basis-state index is outside the dimension.");
    }

    return Array.from(
        { length: dimension },
        (_, position) => position === index ? ONE : ZERO
    );
}

function probabilitiesFromState(state) {
    const normalized = normalizeVector(state);
    return normalized.map(value => value.magnitudeSquared());
}

function expectationValue(state, operator) {
    const normalized = normalizeVector(state);
    const transformed = matrixVectorMultiply(operator, normalized);

    // <psi|A|psi>. The conjugation in <psi| is essential for complex states.
    return vectorInnerProduct(normalized, transformed);
}

function variance(state, operator) {
    const mean = expectationValue(state, operator);
    const squaredOperator = matrixMultiply(operator, operator);
    const secondMoment = expectationValue(state, squaredOperator);

    const varianceValue = secondMoment.subtract(
        mean.multiply(mean)
    );

    return Math.max(0, varianceValue.real);
}


// ---------------------------------------------------------------------------
// 6. Projectors
// ---------------------------------------------------------------------------

const PROJECTOR_0 = [
    [ONE, ZERO],
    [ZERO, ZERO]
];

const PROJECTOR_1 = [
    [ZERO, ZERO],
    [ZERO, ONE]
];

function isProjector(projector, tolerance = 1e-10) {
    return matricesClose(
        matrixMultiply(projector, projector),
        projector,
        tolerance
    );
}

function projectorProbability(state, projector) {
    const result = expectationValue(state, projector);

    if (Math.abs(result.imaginary) > 1e-9) {
        throw new Error("Projector probability should be real.");
    }

    return Math.max(0, Math.min(1, result.real));
}


// ---------------------------------------------------------------------------
// 7. Tensor products
// ---------------------------------------------------------------------------

function tensorProduct(a, b) {
    const [rowsA, columnsA] = matrixShape(a);
    const [rowsB, columnsB] = matrixShape(b);

    const result = zeroMatrix(
        rowsA * rowsB,
        columnsA * columnsB
    );

    for (let i = 0; i < rowsA; i++) {
        for (let j = 0; j < columnsA; j++) {
            for (let k = 0; k < rowsB; k++) {
                for (let l = 0; l < columnsB; l++) {
                    result[i * rowsB + k][j * columnsB + l] =
                        a[i][j].multiply(b[k][l]);
                }
            }
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// 8. Controlled-U
// ---------------------------------------------------------------------------

function controlledUnitary(targetOperator) {
    const [rows, columns] = matrixShape(targetOperator);

    if (rows !== 2 || columns !== 2) {
        throw new Error("This educational controlled-U function requires 2x2 U.");
    }

    const result = zeroMatrix(4, 4);

    // When the control is |0>, identity acts on the target.
    result[0][0] = ONE;
    result[1][1] = ONE;

    // When the control is |1>, U acts on the target.
    for (let row = 0; row < 2; row++) {
        for (let column = 0; column < 2; column++) {
            result[row + 2][column + 2] = targetOperator[row][column];
        }
    }

    return result;
}


// ---------------------------------------------------------------------------
// 9. Measurement sampling
// ---------------------------------------------------------------------------

function sampleDiscrete(probabilities, randomFunction = Math.random) {
    const randomValue = randomFunction();
    let cumulative = 0;

    for (let index = 0; index < probabilities.length; index++) {
        cumulative += probabilities[index];

        if (randomValue < cumulative) {
            return index;
        }
    }

    return probabilities.length - 1;
}

function measureComputationalBasis(state, shots = 1000) {
    if (!Number.isInteger(shots) || shots <= 0) {
        throw new Error("shots must be a positive integer.");
    }

    const probabilities = probabilitiesFromState(state);
    const counts = Array.from(
        { length: probabilities.length },
        () => 0
    );

    for (let shot = 0; shot < shots; shot++) {
        const outcome = sampleDiscrete(probabilities);
        counts[outcome]++;
    }

    return counts;
}


// ---------------------------------------------------------------------------
// 10. A progressively developed quantum circuit
// ---------------------------------------------------------------------------

class QuantumCircuit {
    constructor(qubitCount) {
        if (!Number.isInteger(qubitCount) || qubitCount <= 0) {
            throw new Error("qubitCount must be a positive integer.");
        }

        if (qubitCount > 8) {
            throw new Error(
                "This educational dense simulator limits circuits to 8 qubits."
            );
        }

        this.qubitCount = qubitCount;
        this.dimension = 2 ** qubitCount;
        this.state = basisState(0, this.dimension);
        this.operations = [];
    }

    applySingleQubitGate(gate, qubitIndex) {
        if (qubitIndex < 0 || qubitIndex >= this.qubitCount) {
            throw new Error("Invalid qubit index.");
        }

        if (!isUnitary(gate)) {
            throw new Error(
                "A quantum circuit gate must be unitary in this simulator."
            );
        }

        let fullOperator = null;

        // Qubit 0 is treated as the most significant tensor-product position.
        for (let position = 0; position < this.qubitCount; position++) {
            const factor = position === qubitIndex
                ? gate
                : IDENTITY;

            fullOperator = fullOperator === null
                ? factor
                : tensorProduct(fullOperator, factor);
        }

        this.state = matrixVectorMultiply(
            fullOperator,
            this.state
        );

        this.operations.push({
            type: "single-qubit",
            qubitIndex
        });

        return this;
    }

    applyTwoQubitOperator(operator) {
        const expectedDimension = 2 ** this.qubitCount;

        const [rows, columns] = matrixShape(operator);

        if (
            rows !== expectedDimension ||
            columns !== expectedDimension
        ) {
            throw new Error("Operator dimension does not match circuit dimension.");
        }

        if (!isUnitary(operator)) {
            throw new Error("Circuit operators must be unitary.");
        }

        this.state = matrixVectorMultiply(
            operator,
            this.state
        );

        this.operations.push({
            type: "multi-qubit"
        });

        return this;
    }

    probabilities() {
        return probabilitiesFromState(this.state);
    }

    measure(shots = 1000) {
        return measureComputationalBasis(this.state, shots);
    }

    norm() {
        return vectorNorm(this.state);
    }

    printState() {
        console.log(formatVector(this.state));
    }
}


// ---------------------------------------------------------------------------
// 11. Demonstrations
// ---------------------------------------------------------------------------

function printSection(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function demonstrateOperatorProperties() {
    printSection("1. HERMITIAN, UNITARY, AND NORMAL OPERATORS");

    const examples = [
        ["Identity", IDENTITY],
        ["Pauli X", PAULI_X],
        ["Pauli Y", PAULI_Y],
        ["Pauli Z", PAULI_Z],
        ["Hadamard", HADAMARD],
        ["Phase", phaseGate(Math.PI / 3)],
        ["Hermitian but not unitary", [
            [C(2), ZERO],
            [ZERO, C(-3)]
        ]],
        ["Non-normal", [
            [ZERO, ONE],
            [ZERO, ZERO]
        ]]
    ];

    for (const [name, operator] of examples) {
        console.log(`\n${name}`);
        console.log(formatMatrix(operator));
        console.log("Hermitian:", isHermitian(operator));
        console.log("Unitary:", isUnitary(operator));
        console.log("Normal:", isNormal(operator));
    }
}

function demonstrateObservables() {
    printSection("2. EXPECTATION VALUES AND OBSERVABLES");

    const states = [
        ["|0>", basisState(0, 2)],
        ["|1>", basisState(1, 2)],
        ["|+>", normalizeVector([ONE, ONE])],
        ["(|0> + i|1>)/sqrt(2)", normalizeVector([ONE, I])]
    ];

    for (const [name, state] of states) {
        console.log(`\nState ${name}: ${formatVector(state)}`);

        for (const [operatorName, operator] of [
            ["X", PAULI_X],
            ["Y", PAULI_Y],
            ["Z", PAULI_Z]
        ]) {
            const mean = expectationValue(state, operator);
            const spread = variance(state, operator);

            console.log(
                `  <${operatorName}> = ${mean.toString()}, ` +
                `variance = ${spread.toFixed(6)}`
            );
        }
    }
}

function demonstrateProjectors() {
    printSection("3. PROJECTORS");

    console.log("P0 Hermitian:", isHermitian(PROJECTOR_0));
    console.log("P0² = P0:", isProjector(PROJECTOR_0));

    console.log("P1 Hermitian:", isHermitian(PROJECTOR_1));
    console.log("P1² = P1:", isProjector(PROJECTOR_1));

    const state = normalizeVector([
        C(Math.sqrt(0.8)),
        C(Math.sqrt(0.2), 0.3)
    ]);

    const normalizedState = normalizeVector(state);

    console.log("\nState:", formatVector(normalizedState));
    console.log(
        "P0 probability:",
        projectorProbability(normalizedState, PROJECTOR_0)
    );
    console.log(
        "P1 probability:",
        projectorProbability(normalizedState, PROJECTOR_1)
    );
}

function demonstrateUnitaryGeometry() {
    printSection("4. UNITARY OPERATORS PRESERVE NORMS AND INNER PRODUCTS");

    const first = normalizeVector([ONE, C(2, -1)]);
    const second = normalizeVector([C(2, 1), C(-1)]);

    for (const [name, operator] of [
        ["X", PAULI_X],
        ["Y", PAULI_Y],
        ["Z", PAULI_Z],
        ["H", HADAMARD],
        ["Rz(pi/3)", rotationZ(Math.PI / 3)]
    ]) {
        const transformedFirst = matrixVectorMultiply(operator, first);
        const transformedSecond = matrixVectorMultiply(operator, second);

        const before = vectorInnerProduct(first, second);
        const after = vectorInnerProduct(
            transformedFirst,
            transformedSecond
        );

        console.log(`\n${name}`);
        console.log("Unitary:", isUnitary(operator));
        console.log("Inner product before:", before.toString());
        console.log("Inner product after :", after.toString());
        console.log(
            "Norm after:",
            vectorNorm(transformedFirst).toFixed(12)
        );
    }
}

function demonstrateTensorProducts() {
    printSection("5. TENSOR PRODUCTS");

    const hh = tensorProduct(HADAMARD, HADAMARD);
    const xi = tensorProduct(PAULI_X, IDENTITY);

    console.log("H ⊗ H:");
    console.log(formatMatrix(hh));
    console.log("Unitary:", isUnitary(hh));

    console.log("\nX ⊗ I:");
    console.log(formatMatrix(xi));
    console.log("Unitary:", isUnitary(xi));

    const state00 = basisState(0, 4);
    const result = matrixVectorMultiply(hh, state00);

    console.log("\n(H ⊗ H)|00>:");
    console.log(formatVector(result));
    console.log("Probabilities:", probabilitiesFromState(result));
}

function demonstrateControlledGate() {
    printSection("6. CONTROLLED-X / CNOT");

    const cnot = controlledUnitary(PAULI_X);

    console.log(formatMatrix(cnot));
    console.log("Unitary:", isUnitary(cnot));

    for (let index = 0; index < 4; index++) {
        const state = basisState(index, 4);
        const output = matrixVectorMultiply(cnot, state);

        console.log(
            `Basis ${index}: ${formatVector(output)}`
        );
    }
}

function demonstrateCircuit() {
    printSection("7. TWO-QUBIT CIRCUIT");

    const circuit = new QuantumCircuit(2);

    console.log("Initial state:");
    circuit.printState();

    circuit.applySingleQubitGate(HADAMARD, 0);

    console.log("\nAfter H on qubit 0:");
    circuit.printState();

    const cnot = controlledUnitary(PAULI_X);
    circuit.applyTwoQubitOperator(cnot);

    console.log("\nAfter CNOT:");
    circuit.printState();

    console.log("\nProbabilities:");
    console.log(circuit.probabilities());

    console.log("\nState norm:");
    console.log(circuit.norm().toFixed(12));

    console.log("\nMeasurement counts:");
    console.log(circuit.measure(10000));

    console.log(
        "\nThe circuit produces the entangled Bell state "
        "(|00> + |11>)/sqrt(2), apart from numerical representation."
    );
}

function demonstrateComposition() {
    printSection("8. OPERATOR COMPOSITION AND ORDER");

    const hx = matrixMultiply(HADAMARD, PAULI_X);
    const xh = matrixMultiply(PAULI_X, HADAMARD);

    console.log("HX:");
    console.log(formatMatrix(hx));

    console.log("\nXH:");
    console.log(formatMatrix(xh));

    console.log("\nHX equals XH:", matricesClose(hx, xh));

    const xInverse = adjoint(PAULI_X);
    const hInverse = adjoint(HADAMARD);

    console.log(
        "\nX†X = I:",
        matricesClose(matrixMultiply(xInverse, PAULI_X), IDENTITY)
    );

    console.log(
        "H†H = I:",
        matricesClose(matrixMultiply(hInverse, HADAMARD), IDENTITY)
    );
}

function demonstrateNumericalIssues() {
    printSection("9. NUMERICAL PRECISION AND EDGE CASES");

    const nearlyIdentity = [
        [C(1, 1e-14), C(2e-14)],
        [ZERO, C(1, -1e-14)]
    ];

    console.log("Exact object equality is unsuitable for numerical mathematics.");
    console.log(
        "Tolerance-based identity test:",
        matricesClose(nearlyIdentity, IDENTITY, 1e-12)
    );

    try {
        normalizeVector([ZERO, ZERO]);
    } catch (error) {
        console.log("Zero-vector error:", error.message);
    }

    try {
        new QuantumCircuit(0);
    } catch (error) {
        console.log("Invalid circuit error:", error.message);
    }

    try {
        const circuit = new QuantumCircuit(9);
        console.log(circuit);
    } catch (error) {
        console.log("Dense-simulator constraint:", error.message);
    }
}

function main() {
    console.log("OPERATORS: HERMITIAN AND UNITARY OPERATORS");
    console.log("JavaScript implementation and quantum simulation case study.");

    demonstrateOperatorProperties();
    demonstrateObservables();
    demonstrateProjectors();
    demonstrateUnitaryGeometry();
    demonstrateTensorProducts();
    demonstrateControlledGate();
    demonstrateCircuit();
    demonstrateComposition();
    demonstrateNumericalIssues();

    printSection("END");
    console.log("All demonstrations completed.");
}

main();
