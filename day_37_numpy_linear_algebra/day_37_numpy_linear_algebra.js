"use strict";

/*
 * NumPy-style linear algebra concepts implemented with standard JavaScript.
 * JavaScript has no built-in NumPy equivalent, so this file uses ordinary
 * arrays and typed arrays while making shape and dimension rules explicit.
 */

function heading(title) {
    console.log(`\n${"=".repeat(78)}\n${title}\n${"=".repeat(78)}`);
}

function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

function isFiniteNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
}

function validateVector(vector, name = "vector") {
    assert(Array.isArray(vector), `${name} must be an array`);
    assert(vector.length > 0, `${name} must not be empty`);
    assert(vector.every(isFiniteNumber), `${name} must contain finite numbers`);
}

function validateMatrix(matrix, name = "matrix") {
    assert(Array.isArray(matrix), `${name} must be an array`);
    assert(matrix.length > 0, `${name} must contain rows`);
    const width = matrix[0].length;
    assert(width > 0, `${name} must contain columns`);
    assert(
        matrix.every(
            row =>
                Array.isArray(row) &&
                row.length === width &&
                row.every(isFiniteNumber)
        ),
        `${name} must be rectangular and numeric`
    );
}

function vectorAdd(a, b) {
    validateVector(a);
    validateVector(b);
    assert(a.length === b.length, "Vector dimensions must match");
    return a.map((value, i) => value + b[i]);
}

function vectorSubtract(a, b) {
    validateVector(a);
    validateVector(b);
    assert(a.length === b.length, "Vector dimensions must match");
    return a.map((value, i) => value - b[i]);
}

function scalarMultiply(scalar, vector) {
    validateVector(vector);
    assert(isFiniteNumber(scalar), "Scalar must be finite");
    return vector.map(value => scalar * value);
}

function dot(a, b) {
    validateVector(a);
    validateVector(b);
    assert(a.length === b.length, "Dot-product dimensions must match");
    return a.reduce((sum, value, i) => sum + value * b[i], 0);
}

function norm(vector, order = 2) {
    validateVector(vector);

    if (order === 1) {
        return vector.reduce((sum, value) => sum + Math.abs(value), 0);
    }

    if (order === 2) {
        return Math.sqrt(dot(vector, vector));
    }

    if (order === Infinity) {
        return Math.max(...vector.map(Math.abs));
    }

    throw new Error("Only L1, L2, and L-infinity norms are implemented");
}

function normalize(vector) {
    const length = norm(vector);
    if (length === 0) {
        throw new Error("The zero vector cannot be normalized");
    }
    return scalarMultiply(1 / length, vector);
}

function matrixShape(matrix) {
    validateMatrix(matrix);
    return [matrix.length, matrix[0].length];
}

function matrixTranspose(matrix) {
    const [rows, columns] = matrixShape(matrix);
    return Array.from({ length: columns }, (_, column) =>
        Array.from({ length: rows }, (_, row) => matrix[row][column])
    );
}

function matrixMultiply(a, b) {
    const [aRows, aColumns] = matrixShape(a);
    const [bRows, bColumns] = matrixShape(b);

    assert(
        aColumns === bRows,
        `Cannot multiply ${aRows}x${aColumns} by ${bRows}x${bColumns}`
    );

    return Array.from({ length: aRows }, (_, row) =>
        Array.from({ length: bColumns }, (_, column) => {
            let sum = 0;
            for (let k = 0; k < aColumns; k++) {
                sum += a[row][k] * b[k][column];
            }
            return sum;
        })
    );
}

function matrixVectorMultiply(matrix, vector) {
    validateMatrix(matrix);
    validateVector(vector);

    const [rows, columns] = matrixShape(matrix);
    assert(columns === vector.length, "Matrix columns must match vector length");

    return matrix.map(row =>
        row.reduce((sum, value, index) => sum + value * vector[index], 0)
    );
}

function matrixIdentity(size) {
    assert(Number.isInteger(size) && size > 0, "Size must be positive");
    return Array.from({ length: size }, (_, row) =>
        Array.from({ length: size }, (_, column) =>
            row === column ? 1 : 0
        )
    );
}

function matrixSubtract(a, b) {
    const [aRows, aColumns] = matrixShape(a);
    const [bRows, bColumns] = matrixShape(b);
    assert(aRows === bRows && aColumns === bColumns, "Matrix shapes differ");

    return a.map((row, i) =>
        row.map((value, j) => value - b[i][j])
    );
}

function gaussianElimination(matrix, rhs) {
    validateMatrix(matrix);
    validateVector(rhs);

    const [rows, columns] = matrixShape(matrix);
    assert(rows === columns, "Gaussian elimination requires a square matrix");
    assert(rhs.length === rows, "Right-hand side dimension mismatch");

    const augmented = matrix.map((row, i) => [...row, rhs[i]]);

    for (let pivot = 0; pivot < columns; pivot++) {
        let bestRow = pivot;
        for (let row = pivot + 1; row < rows; row++) {
            if (
                Math.abs(augmented[row][pivot]) >
                Math.abs(augmented[bestRow][pivot])
            ) {
                bestRow = row;
            }
        }

        if (Math.abs(augmented[bestRow][pivot]) < Number.EPSILON) {
            throw new Error("Matrix is singular or numerically singular");
        }

        [augmented[pivot], augmented[bestRow]] =
            [augmented[bestRow], augmented[pivot]];

        for (let row = pivot + 1; row < rows; row++) {
            const factor = augmented[row][pivot] / augmented[pivot][pivot];
            for (let column = pivot; column <= columns; column++) {
                augmented[row][column] -=
                    factor * augmented[pivot][column];
            }
        }
    }

    const solution = new Array(columns).fill(0);

    for (let row = rows - 1; row >= 0; row--) {
        let value = augmented[row][columns];

        for (let column = row + 1; column < columns; column++) {
            value -= augmented[row][column] * solution[column];
        }

        solution[row] = value / augmented[row][row];
    }

    return solution;
}

function determinant(matrix) {
    validateMatrix(matrix);
    const [rows, columns] = matrixShape(matrix);
    assert(rows === columns, "Determinant requires a square matrix");

    const working = matrix.map(row => [...row]);
    let result = 1;
    let sign = 1;

    for (let pivot = 0; pivot < columns; pivot++) {
        let bestRow = pivot;

        for (let row = pivot + 1; row < rows; row++) {
            if (
                Math.abs(working[row][pivot]) >
                Math.abs(working[bestRow][pivot])
            ) {
                bestRow = row;
            }
        }

        if (Math.abs(working[bestRow][pivot]) < Number.EPSILON) {
            return 0;
        }

        if (bestRow !== pivot) {
            [working[pivot], working[bestRow]] =
                [working[bestRow], working[pivot]];
            sign *= -1;
        }

        const pivotValue = working[pivot][pivot];
        result *= pivotValue;

        for (let row = pivot + 1; row < rows; row++) {
            const factor = working[row][pivot] / pivotValue;
            for (let column = pivot + 1; column < columns; column++) {
                working[row][column] -=
                    factor * working[pivot][column];
            }
        }
    }

    return sign * result;
}

function outerProduct(a, b) {
    validateVector(a);
    validateVector(b);

    return a.map(x => b.map(y => x * y));
}

function tensorShape(tensor) {
    if (!Array.isArray(tensor)) {
        return [];
    }

    if (tensor.length === 0) {
        return [0];
    }

    const childShape = tensorShape(tensor[0]);

    for (const item of tensor) {
        const currentShape = tensorShape(item);
        assert(
            JSON.stringify(currentShape) === JSON.stringify(childShape),
            "Tensor must be rectangular"
        );
    }

    return [tensor.length, ...childShape];
}

function flattenTensor(tensor, result = []) {
    if (!Array.isArray(tensor)) {
        result.push(tensor);
        return result;
    }

    for (const value of tensor) {
        flattenTensor(value, result);
    }

    return result;
}

function reshape(flatValues, shape) {
    const expectedSize = shape.reduce((product, dimension) => product * dimension, 1);
    assert(
        expectedSize === flatValues.length,
        `Cannot reshape ${flatValues.length} values into ${shape}`
    );

    let offset = 0;

    function build(depth) {
        if (depth === shape.length) {
            return flatValues[offset++];
        }

        return Array.from(
            { length: shape[depth] },
            () => build(depth + 1)
        );
    }

    return build(0);
}

function tensorSum(tensor, axis) {
    const shape = tensorShape(tensor);
    assert(shape.length > 0, "Tensor cannot be empty");

    if (axis === 0) {
        if (shape.length === 1) {
            return tensor.reduce((sum, value) => sum + value, 0);
        }

        const childShape = shape.slice(1);
        const result = Array.from(
            { length: childShape[0] },
            () => undefined
        );

        const partials = tensor.map(item => tensorSum(item, 0));

        function addNested(a, b) {
            if (!Array.isArray(a)) {
                return a + b;
            }
            return a.map((value, i) => addNested(value, b[i]));
        }

        return partials.reduce(addNested);
    }

    throw new Error(
        "This compact tensor demonstration supports reduction along axis 0"
    );
}

function demonstrateVectors() {
    heading("Vectors");

    const a = [3, 4, 0];
    const b = [1, 2, 5];

    console.log("a + b:", vectorAdd(a, b));
    console.log("a - b:", vectorSubtract(a, b));
    console.log("2.5a:", scalarMultiply(2.5, a));
    console.log("a dot b:", dot(a, b));
    console.log("L2 norm:", norm(a));
    console.log("unit vector:", normalize(a));

    const projectionScale = dot(a, b) / dot(b, b);
    console.log(
        "projection of a onto b:",
        scalarMultiply(projectionScale, b)
    );
}

function demonstrateMatrices() {
    heading("Matrices");

    const a = [
        [1, 2, 3],
        [4, 5, 6]
    ];

    const b = [
        [7, 8],
        [9, 10],
        [11, 12]
    ];

    console.log("A:", a);
    console.log("B:", b);
    console.log("A transpose:", matrixTranspose(a));
    console.log("A @ B:", matrixMultiply(a, b));
    console.log("A @ [10,20,30]:", matrixVectorMultiply(a, [10, 20, 30]));
}

function demonstrateLinearSystem() {
    heading("Linear System");

    const a = [
        [3, 2, -1],
        [2, -2, 4],
        [-1, 0.5, -1]
    ];
    const b = [1, -2, 0];

    const solution = gaussianElimination(a, b);

    console.log("solution:", solution);
    console.log("reconstructed b:", matrixVectorMultiply(a, solution));
    console.log("determinant:", determinant(a));

    try {
        gaussianElimination(
            [
                [1, 2],
                [2, 4]
            ],
            [3, 6]
        );
    } catch (error) {
        console.log("Expected singular-system failure:", error.message);
    }
}

function demonstrateTensorOperations() {
    heading("Tensor Operations");

    const tensor = reshape(
        Array.from({ length: 24 }, (_, index) => index),
        [2, 3, 4]
    );

    console.log("shape:", tensorShape(tensor));
    console.log("flattened:", flattenTensor(tensor));
    console.log("sum over first axis:", tensorSum(tensor, 0));

    const restored = reshape(flattenTensor(tensor), [2, 3, 4]);
    console.log(
        "reshape restores element count:",
        flattenTensor(restored).length === 24
    );

    const matrix = [
        [1, 2],
        [3, 4]
    ];
    const vector = [5, 6];

    console.log("outer product:", outerProduct(vector, vector));
    console.log("matrix-vector contraction:", matrixVectorMultiply(matrix, vector));
}

function demonstrateTypedArrays() {
    heading("Typed Arrays and Numeric Storage");

    const values = new Float64Array([1, 2, 3, 4]);

    console.log("typed array:", values);
    console.log("byte length:", values.byteLength);
    console.log("element count:", values.length);

    const doubled = new Float64Array(values.length);
    for (let i = 0; i < values.length; i++) {
        doubled[i] = values[i] * 2;
    }

    console.log("doubled:", doubled);

    // Typed arrays provide predictable numeric storage, but unlike NumPy they
    // do not intrinsically carry multidimensional shape metadata.
}

function demonstrateEdgeCases() {
    heading("Validation and Edge Cases");

    try {
        normalize([0, 0, 0]);
    } catch (error) {
        console.log("Zero-vector error:", error.message);
    }

    try {
        matrixMultiply([[1, 2]], [[1, 2]]);
    } catch (error) {
        console.log("Shape error:", error.message);
    }

    try {
        validateVector([1, Number.NaN]);
    } catch (error) {
        console.log("NaN validation:", error.message);
    }

    const closeA = 0.1 + 0.2;
    const closeB = 0.3;
    console.log("direct floating-point equality:", closeA === closeB);
    console.log(
        "tolerance comparison:",
        Math.abs(closeA - closeB) < 1e-12
    );
}

function main() {
    console.log("JavaScript Linear Algebra Companion");
    demonstrateVectors();
    demonstrateMatrices();
    demonstrateLinearSystem();
    demonstrateTensorOperations();
    demonstrateTypedArrays();
    demonstrateEdgeCases();

    heading("Completed");
    console.log(
        "The program demonstrated vector arithmetic, matrix products,",
        "linear-system solving, determinants, tensor shape/reshape operations,",
        "typed numeric storage, validation, and numerical edge cases."
    );
}

main();
