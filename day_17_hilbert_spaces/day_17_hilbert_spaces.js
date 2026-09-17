"use strict";

/*
 * Hilbert Spaces
 * Mathematical framework
 *
 * This JavaScript file complements the Python implementation by focusing on
 * executable numerical geometry, immutable-style transformations, classes,
 * functional programming patterns, asynchronous computation, and a
 * browser-compatible event model.
 *
 * JavaScript's built-in Number type uses IEEE-754 double precision, so all
 * numerical comparisons use tolerances where appropriate.
 */

// ============================================================================
// 1. BASIC VECTOR REPRESENTATION
// ============================================================================

function assertSameDimension(a, b) {
    if (a.length !== b.length) {
        throw new Error("Vectors must have the same dimension.");
    }
}

function addVectors(a, b) {
    assertSameDimension(a, b);
    return a.map((value, index) => value + b[index]);
}

function subtractVectors(a, b) {
    assertSameDimension(a, b);
    return a.map((value, index) => value - b[index]);
}

function scaleVector(scalar, vector) {
    return vector.map(value => scalar * value);
}

function realInnerProduct(a, b) {
    /*
     * For real vectors the standard Hilbert-space inner product is
     *
     *     <x,y> = sum x_i y_i.
     *
     * Complex numbers are not primitive JavaScript values, so complex
     * arithmetic is demonstrated separately below.
     */
    assertSameDimension(a, b);
    return a.reduce((sum, value, index) => sum + value * b[index], 0);
}

function vectorNorm(vector) {
    return Math.sqrt(realInnerProduct(vector, vector));
}

function vectorDistance(a, b) {
    return vectorNorm(subtractVectors(a, b));
}

function approximatelyEqual(a, b, tolerance = 1e-10) {
    return Math.abs(a - b) <= tolerance;
}

function vectorsApproximatelyEqual(a, b, tolerance = 1e-10) {
    assertSameDimension(a, b);
    return a.every((value, index) =>
        approximatelyEqual(value, b[index], tolerance)
    );
}

function normalizeVector(vector) {
    const length = vectorNorm(vector);

    if (length <= 1e-12) {
        throw new Error("The zero vector cannot be normalized.");
    }

    return scaleVector(1 / length, vector);
}


// ============================================================================
// 2. BASIC INNER-PRODUCT GEOMETRY
// ============================================================================

function demonstrateBasicGeometry() {
    console.log("\n=== BASIC INNER-PRODUCT GEOMETRY ===");

    const x = [3, 4];
    const y = [4, -3];

    console.log("x =", x);
    console.log("y =", y);
    console.log("<x,y> =", realInnerProduct(x, y));
    console.log("||x|| =", vectorNorm(x));
    console.log("||y|| =", vectorNorm(y));
    console.log("distance(x,y) =", vectorDistance(x, y));

    const orthogonal = approximatelyEqual(
        realInnerProduct(x, y),
        0
    );

    console.log("orthogonal =", orthogonal);

    if (orthogonal) {
        const left = vectorNorm(addVectors(x, y)) ** 2;
        const right = vectorNorm(x) ** 2 + vectorNorm(y) ** 2;
        console.log("Pythagorean identity:", left, right);
    }
}


// ============================================================================
// 3. COMPLEX INNER PRODUCTS
// ============================================================================

class Complex {
    constructor(real, imaginary = 0) {
        this.real = real;
        this.imaginary = imaginary;
    }

    add(other) {
        return new Complex(
            this.real + other.real,
            this.imaginary + other.imaginary
        );
    }

    multiply(other) {
        return new Complex(
            this.real * other.real - this.imaginary * other.imaginary,
            this.real * other.imaginary + this.imaginary * other.real
        );
    }

    conjugate() {
        return new Complex(this.real, -this.imaginary);
    }

    magnitude() {
        return Math.hypot(this.real, this.imaginary);
    }

    toString() {
        const sign = this.imaginary >= 0 ? "+" : "-";
        return `${this.real}${sign}${Math.abs(this.imaginary)}i`;
    }
}

function complexInnerProduct(a, b) {
    if (a.length !== b.length) {
        throw new Error("Vectors must have the same dimension.");
    }

    let result = new Complex(0, 0);

    for (let i = 0; i < a.length; i++) {
        // <x,y> = sum conjugate(x_i) y_i.
        result = result.add(
            a[i].conjugate().multiply(b[i])
        );
    }

    return result;
}

function demonstrateComplexGeometry() {
    console.log("\n=== COMPLEX HILBERT-SPACE GEOMETRY ===");

    const x = [
        new Complex(1, 2),
        new Complex(2, -1)
    ];

    const y = [
        new Complex(3, -1),
        new Complex(-1, 4)
    ];

    const xy = complexInnerProduct(x, y);
    const yx = complexInnerProduct(y, x);

    console.log("<x,y> =", xy.toString());
    console.log("<y,x> =", yx.toString());
    console.log("conjugate(<y,x>) =", yx.conjugate().toString());

    console.log(
        "Conjugate symmetry:",
        xy.real === yx.real &&
        xy.imaginary === -yx.imaginary
    );
}


// ============================================================================
// 4. GRAM-SCHMIDT ORTHONORMALIZATION
// ============================================================================

function gramSchmidt(vectors, tolerance = 1e-12) {
    const orthonormalBasis = [];

    for (const vector of vectors) {
        let residual = [...vector];

        for (const basisVector of orthonormalBasis) {
            const coefficient = realInnerProduct(basisVector, vector);

            // Projection onto an already normalized basis vector:
            // <q,v> q
            residual = subtractVectors(
                residual,
                scaleVector(coefficient, basisVector)
            );
        }

        const residualNorm = vectorNorm(residual);

        if (residualNorm <= tolerance) {
            throw new Error(
                "Vectors are linearly dependent or numerically dependent."
            );
        }

        orthonormalBasis.push(
            scaleVector(1 / residualNorm, residual)
        );
    }

    return orthonormalBasis;
}

function demonstrateOrthonormalization() {
    console.log("\n=== ORTHONORMALIZATION ===");

    const vectors = [
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 1]
    ];

    const basis = gramSchmidt(vectors);

    basis.forEach((q, index) => {
        console.log(`q${index + 1} =`, q);
    });

    console.log("Gram matrix:");

    for (const q of basis) {
        console.log(
            basis.map(p => realInnerProduct(q, p).toFixed(8))
        );
    }
}


// ============================================================================
// 5. ORTHOGONAL PROJECTION
// ============================================================================

function projectOntoOrthonormalBasis(vector, basis) {
    let projection = new Array(vector.length).fill(0);

    for (const q of basis) {
        const coefficient = realInnerProduct(q, vector);

        projection = addVectors(
            projection,
            scaleVector(coefficient, q)
        );
    }

    return projection;
}

function projectOntoSubspace(vector, spanningVectors) {
    const basis = gramSchmidt(spanningVectors);

    return {
        projection: projectOntoOrthonormalBasis(vector, basis),
        basis
    };
}

function demonstrateProjection() {
    console.log("\n=== ORTHOGONAL PROJECTION ===");

    const target = [3, 1, 4];

    const generators = [
        [1, 0, 1],
        [0, 1, 1]
    ];

    const { projection, basis } =
        projectOntoSubspace(target, generators);

    const residual = subtractVectors(target, projection);

    console.log("target =", target);
    console.log("projection =", projection);
    console.log("residual =", residual);

    basis.forEach((q, index) => {
        console.log(
            `<q${index + 1}, residual> =`,
            realInnerProduct(q, residual)
        );
    });

    console.log(
        "Best approximation distance =",
        vectorNorm(residual)
    );
}


// ============================================================================
// 6. LEAST-SQUARES REGRESSION AS PROJECTION
// ============================================================================

function transpose(matrix) {
    if (matrix.length === 0) {
        return [];
    }

    return matrix[0].map((_, columnIndex) =>
        matrix.map(row => row[columnIndex])
    );
}

function matrixVectorMultiply(matrix, vector) {
    return matrix.map(row => {
        if (row.length !== vector.length) {
            throw new Error("Matrix/vector dimensions are incompatible.");
        }

        return row.reduce(
            (sum, value, index) => sum + value * vector[index],
            0
        );
    });
}

function matrixMultiply(a, b) {
    const bTransposed = transpose(b);

    return a.map(row =>
        bTransposed.map(column =>
            row.reduce(
                (sum, value, index) => sum + value * column[index],
                0
            )
        )
    );
}

function identityMatrix(size) {
    return Array.from({ length: size }, (_, row) =>
        Array.from({ length: size }, (_, column) =>
            row === column ? 1 : 0
        )
    );
}

function demonstrateLeastSquares() {
    console.log("\n=== LEAST SQUARES AS PROJECTION ===");

    const xValues = [0, 1, 2, 3, 4];
    const observed = [1.2, 2.9, 5.1, 6.8, 9.2];

    const columns = [
        new Array(xValues.length).fill(1),
        xValues
    ];

    const orthonormalBasis = gramSchmidt(columns);

    const projection = projectOntoOrthonormalBasis(
        observed,
        orthonormalBasis
    );

    console.log("Observed:", observed);
    console.log("Projected:", projection);

    const residual = vectorDistance(observed, projection);

    console.log("Residual norm:", residual);

    /*
     * This shows the geometric interpretation:
     *
     *     fitted data = orthogonal projection of observed data
     *                   onto the column space of the design matrix.
     */
}


// ============================================================================
// 7. PARSEVAL IDENTITY
// ============================================================================

function parsevalCheck(vector, completeOrthonormalBasis) {
    const vectorEnergy = vectorNorm(vector) ** 2;

    const coefficientEnergy =
        completeOrthonormalBasis.reduce(
            (sum, q) =>
                sum + realInnerProduct(q, vector) ** 2,
            0
        );

    return {
        vectorEnergy,
        coefficientEnergy,
        error: Math.abs(vectorEnergy - coefficientEnergy)
    };
}

function demonstrateParseval() {
    console.log("\n=== PARSEVAL IDENTITY ===");

    const basis = gramSchmidt([
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 0]
    ]);

    const vector = [2, -1, 4];

    const result = parsevalCheck(vector, basis);

    console.log(result);

    /*
     * For a complete orthonormal basis:
     *
     *     ||x||² = sum |<q_i,x>|².
     *
     * If the basis is incomplete, Bessel's inequality gives only <=.
     */
}


// ============================================================================
// 8. FUNCTION-SPACE DISCRETIZATION
// ============================================================================

function linspace(start, end, count) {
    if (count < 2) {
        throw new Error("At least two samples are required.");
    }

    const step = (end - start) / (count - 1);

    return Array.from(
        { length: count },
        (_, index) => start + index * step
    );
}

function trapezoidalInnerProduct(f, g, start, end, samples = 5001) {
    const points = linspace(start, end, samples);
    const step = (end - start) / (samples - 1);

    let total = 0;

    for (let i = 0; i < points.length; i++) {
        const weight =
            i === 0 || i === points.length - 1
                ? 0.5
                : 1;

        total += weight * f(points[i]) * g(points[i]);
    }

    return total * step;
}

function functionNorm(f, start, end, samples = 5001) {
    return Math.sqrt(
        Math.max(
            trapezoidalInnerProduct(
                f,
                f,
                start,
                end,
                samples
            ),
            0
        )
    );
}

function demonstrateFunctionSpace() {
    console.log("\n=== FUNCTION SPACE APPROXIMATION ===");

    const sine = x => Math.sin(x);
    const cosine = x => Math.cos(x);

    const innerProduct =
        trapezoidalInnerProduct(
            sine,
            cosine,
            0,
            Math.PI
        );

    console.log(
        "<sin,cos> on [0,pi] ≈",
        innerProduct
    );

    console.log(
        "||sin||₂ ≈",
        functionNorm(sine, 0, Math.PI)
    );

    /*
     * Mathematically this is an approximation to L²([0,π]).
     *
     *     <f,g> = integral_0^π f(x)g(x) dx
     *
     * A numerical grid converts a function-space problem into a
     * finite-dimensional approximation.
     */
}


// ============================================================================
// 9. SINE-BASIS EXPANSION
// ============================================================================

function normalizedSineBasis(n, x, length) {
    return Math.sqrt(2 / length) *
        Math.sin(n * Math.PI * x / length);
}

function sineExpansionCoefficients(
    f,
    length,
    count,
    samples = 5001
) {
    const coefficients = [];

    for (let n = 1; n <= count; n++) {
        const basisFunction =
            x => normalizedSineBasis(n, x, length);

        coefficients.push(
            trapezoidalInnerProduct(
                basisFunction,
                f,
                0,
                length,
                samples
            )
        );
    }

    return coefficients;
}

function reconstructSineExpansion(
    x,
    length,
    coefficients
) {
    return coefficients.reduce(
        (sum, coefficient, index) =>
            sum +
            coefficient *
            normalizedSineBasis(
                index + 1,
                x,
                length
            ),
        0
    );
}

function demonstrateSineExpansion() {
    console.log("\n=== ORTHONORMAL FUNCTION EXPANSION ===");

    const length = Math.PI;
    const target = x => x;

    const coefficients =
        sineExpansionCoefficients(
            target,
            length,
            8
        );

    console.log("Coefficients:", coefficients);

    for (const x of [0.25, 0.75, 1.5, 2.25, 3.0]) {
        console.log(
            `x=${x.toFixed(2)}, target=${x.toFixed(6)}, ` +
            `approximation=${reconstructSineExpansion(
                x,
                length,
                coefficients
            ).toFixed(6)}`
        );
    }
}


// ============================================================================
// 10. HILBERT SPACE CLASS
// ============================================================================

class HilbertVector {
    constructor(values) {
        if (!Array.isArray(values) || values.length === 0) {
            throw new Error(
                "A Hilbert vector must contain at least one value."
            );
        }

        if (!values.every(Number.isFinite)) {
            throw new Error(
                "This educational class requires finite real values."
            );
        }

        this.values = [...values];
    }

    add(other) {
        return new HilbertVector(
            addVectors(this.values, other.values)
        );
    }

    subtract(other) {
        return new HilbertVector(
            subtractVectors(this.values, other.values)
        );
    }

    scale(scalar) {
        if (!Number.isFinite(scalar)) {
            throw new Error("Scalar must be finite.");
        }

        return new HilbertVector(
            scaleVector(scalar, this.values)
        );
    }

    inner(other) {
        return realInnerProduct(
            this.values,
            other.values
        );
    }

    norm() {
        return vectorNorm(this.values);
    }

    normalize() {
        return new HilbertVector(
            normalizeVector(this.values)
        );
    }

    distanceTo(other) {
        return vectorDistance(
            this.values,
            other.values
        );
    }

    isOrthogonalTo(other, tolerance = 1e-10) {
        return Math.abs(this.inner(other)) <= tolerance;
    }

    toString() {
        return `HilbertVector(${this.values.join(", ")})`;
    }
}

function demonstrateHilbertVectorClass() {
    console.log("\n=== OBJECT-ORIENTED HILBERT VECTOR ===");

    const x = new HilbertVector([3, 4]);
    const y = new HilbertVector([4, -3]);

    console.log(x.toString());
    console.log("norm =", x.norm());
    console.log("inner =", x.inner(y));
    console.log("orthogonal =", x.isOrthogonalTo(y));
}


// ============================================================================
// 11. VALIDATION AND FAILURE CONDITIONS
// ============================================================================

function demonstrateFailures() {
    console.log("\n=== FAILURE CONDITIONS ===");

    try {
        normalizeVector([0, 0]);
    } catch (error) {
        console.log("Zero-vector normalization:", error.message);
    }

    try {
        gramSchmidt([
            [1, 2],
            [2, 4]
        ]);
    } catch (error) {
        console.log("Dependent vectors:", error.message);
    }

    try {
        addVectors([1, 2], [3]);
    } catch (error) {
        console.log("Dimension mismatch:", error.message);
    }

    try {
        new HilbertVector([]);
    } catch (error) {
        console.log("Invalid HilbertVector:", error.message);
    }
}


// ============================================================================
// 12. PERFORMANCE CONSIDERATIONS
// ============================================================================

function benchmarkInnerProduct(size = 100000) {
    const a = Array.from(
        { length: size },
        (_, index) => Math.sin(index / 100)
    );

    const b = Array.from(
        { length: size },
        (_, index) => Math.cos(index / 100)
    );

    const start = performance.now();

    const value = realInnerProduct(a, b);

    const elapsed = performance.now() - start;

    return {
        value,
        milliseconds: elapsed
    };
}

function demonstratePerformance() {
    console.log("\n=== PERFORMANCE CONSIDERATIONS ===");

    const result = benchmarkInnerProduct(100000);

    console.log("Inner product:", result.value);
    console.log(
        "Elapsed time:",
        result.milliseconds.toFixed(3),
        "ms"
    );

    /*
     * Basic vector operations are O(n).
     *
     * Gram-Schmidt for n-dimensional vectors and k input vectors is roughly
     * O(n k²).
     *
     * Dense matrix-vector multiplication is O(n²).
     *
     * Dense matrix multiplication is O(n³) for n x n matrices using the
     * straightforward algorithm.
     *
     * Real applications often use optimized numerical libraries, typed
     * arrays, sparse representations, and BLAS/LAPACK-style algorithms.
     */
}


// ============================================================================
// 13. ASYNCHRONOUS LARGE-DATA COMPUTATION
// ============================================================================

function asynchronousInnerProduct(a, b) {
    return new Promise((resolve, reject) => {
        if (a.length !== b.length) {
            reject(
                new Error("Vectors must have equal dimensions.")
            );
            return;
        }

        /*
         * setTimeout demonstrates how a CPU-bound calculation can be
         * scheduled away from the immediate call stack. It does not make
         * the arithmetic intrinsically faster and does not replace Web
         * Workers for genuinely heavy computation.
         */
        setTimeout(() => {
            try {
                resolve(realInnerProduct(a, b));
            } catch (error) {
                reject(error);
            }
        }, 0);
    });
}

async function demonstrateAsyncComputation() {
    console.log("\n=== ASYNCHRONOUS COMPUTATION ===");

    const x = [1, 2, 3, 4];
    const y = [5, 6, 7, 8];

    try {
        const result =
            await asynchronousInnerProduct(x, y);

        console.log("Asynchronous inner product =", result);
    } catch (error) {
        console.error(error.message);
    }
}


// ============================================================================
// 14. EVENT-DRIVEN BROWSER DEMONSTRATION
// ============================================================================

function createBrowserDemo() {
    /*
     * This function is safe in Node.js because it checks whether document
     * exists before using browser APIs.
     *
     * In a browser, it creates a small interactive projection calculator.
     */
    if (typeof document === "undefined") {
        console.log(
            "\nBrowser UI demonstration skipped: document is unavailable."
        );
        return;
    }

    const container = document.createElement("section");

    const title = document.createElement("h2");
    title.textContent =
        "Hilbert-space projection demonstration";

    const button = document.createElement("button");
    button.textContent = "Project [3,1,4]";

    const output = document.createElement("pre");

    button.addEventListener("click", () => {
        const result = projectOntoSubspace(
            [3, 1, 4],
            [
                [1, 0, 1],
                [0, 1, 1]
            ]
        );

        output.textContent =
            "Projection: " +
            JSON.stringify(result.projection) +
            "\nResidual: " +
            JSON.stringify(
                subtractVectors(
                    [3, 1, 4],
                    result.projection
                )
            );
    });

    container.appendChild(title);
    container.appendChild(button);
    container.appendChild(output);

    document.body.appendChild(container);
}


// ============================================================================
// 15. UNIT TESTS
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function runTests() {
    console.log("\n=== SELF-TESTS ===");

    assert(
        approximatelyEqual(
            vectorNorm([3, 4]),
            5
        ),
        "3-4-5 norm"
    );

    assert(
        approximatelyEqual(
            realInnerProduct(
                [1, 0],
                [0, 1]
            ),
            0
        ),
        "orthogonality"
    );

    assert(
        approximatelyEqual(
            vectorNorm(
                normalizeVector([3, 4])
            ),
            1
        ),
        "normalization"
    );

    const basis = gramSchmidt([
        [1, 1],
        [1, -1]
    ]);

    assert(
        approximatelyEqual(
            realInnerProduct(
                basis[0],
                basis[1]
            ),
            0
        ),
        "orthonormality"
    );

    const projection =
        projectOntoSubspace(
            [3, 4],
            [[1, 0]]
        ).projection;

    assert(
        vectorsApproximatelyEqual(
            projection,
            [3, 0]
        ),
        "projection"
    );

    console.log("All JavaScript tests passed.");
}


// ============================================================================
// 16. MAIN EXECUTION
// ============================================================================

async function main() {
    console.log(
        "HILBERT SPACES: JAVASCRIPT NUMERICAL STUDY"
    );

    demonstrateBasicGeometry();
    demonstrateComplexGeometry();
    demonstrateOrthonormalization();
    demonstrateProjection();
    demonstrateLeastSquares();
    demonstrateParseval();
    demonstrateFunctionSpace();
    demonstrateSineExpansion();
    demonstrateHilbertVectorClass();
    demonstrateFailures();
    demonstratePerformance();
    await demonstrateAsyncComputation();
    createBrowserDemo();
    runTests();

    console.log("\nStudy program completed.");
}

if (typeof module !== "undefined" && require.main === module) {
    main().catch(error => {
        console.error("Program failed:", error);
        process.exitCode = 1;
    });
}
