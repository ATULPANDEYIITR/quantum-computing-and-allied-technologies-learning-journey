DROP SCHEMA IF EXISTS numpy_linear_algebra CASCADE;
CREATE SCHEMA numpy_linear_algebra;
SET search_path TO numpy_linear_algebra;

-- PostgreSQL arrays provide a compact relational representation for vectors
-- and small tensors. The database still enforces dimensional rules explicitly
-- because PostgreSQL does not automatically understand application-level
-- linear-algebra semantics.

CREATE TABLE vector_dataset (
    vector_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    dimension INTEGER NOT NULL CHECK (dimension > 0),
    values DOUBLE PRECISION[] NOT NULL,
    CONSTRAINT vector_dimension_matches_values
        CHECK (array_length(values, 1) = dimension),
    CONSTRAINT vector_values_finite
        CHECK (
            NOT EXISTS (
                SELECT 1
                FROM unnest(values) AS value
                WHERE value IS NULL
                   OR value <> value
                   OR value = 'Infinity'::double precision
                   OR value = '-Infinity'::double precision
            )
        )
);

CREATE TABLE matrix_dataset (
    matrix_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (
        role IN (
            'FEATURE_TRANSFORM',
            'COVARIANCE',
            'SYSTEM_MATRIX',
            'PROJECTION'
        )
    ),
    row_count INTEGER NOT NULL CHECK (row_count > 0),
    column_count INTEGER NOT NULL CHECK (column_count > 0),
    values DOUBLE PRECISION[][] NOT NULL,
    CONSTRAINT matrix_shape_matches_values
        CHECK (
            array_length(values, 1) = row_count
            AND array_length(values, 2) = column_count
        )
);

CREATE TABLE tensor_dataset (
    tensor_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    rank INTEGER NOT NULL CHECK (rank >= 3),
    dimensions INTEGER[] NOT NULL,
    values DOUBLE PRECISION[] NOT NULL,
    CONSTRAINT tensor_dimension_count_matches_rank
        CHECK (cardinality(dimensions) = rank),
    CONSTRAINT tensor_dimensions_positive
        CHECK (
            NOT EXISTS (
                SELECT 1
                FROM unnest(dimensions) AS dimension
                WHERE dimension <= 0
            )
        ),
    CONSTRAINT tensor_element_count_matches_shape
        CHECK (
            cardinality(values) = (
                SELECT COALESCE(
                    product,
                    0
                )
                FROM (
                    SELECT exp(
                        sum(ln(dimension::double precision))
                    )::bigint AS product
                    FROM unnest(dimensions) AS dimension
                ) AS shape_product
            )
        )
);

CREATE TABLE matrix_vector_operation (
    operation_id BIGSERIAL PRIMARY KEY,
    matrix_id BIGINT NOT NULL REFERENCES matrix_dataset(matrix_id),
    vector_id BIGINT NOT NULL REFERENCES vector_dataset(vector_id),
    operation_name TEXT NOT NULL CHECK (
        operation_name IN ('MATRIX_VECTOR_PRODUCT', 'PROJECTION_INPUT')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE linear_system (
    system_id BIGSERIAL PRIMARY KEY,
    matrix_id BIGINT NOT NULL REFERENCES matrix_dataset(matrix_id),
    rhs_vector_id BIGINT NOT NULL REFERENCES vector_dataset(vector_id),
    solution_vector_id BIGINT REFERENCES vector_dataset(vector_id),
    residual_norm DOUBLE PRECISION,
    solved_at TIMESTAMPTZ,
    CONSTRAINT residual_norm_nonnegative
        CHECK (residual_norm IS NULL OR residual_norm >= 0)
);

CREATE INDEX idx_matrix_role
    ON matrix_dataset(role);

CREATE INDEX idx_operation_matrix
    ON matrix_vector_operation(matrix_id);

CREATE INDEX idx_operation_vector
    ON matrix_vector_operation(vector_id);

INSERT INTO vector_dataset (name, dimension, values)
VALUES
    ('customer_metrics', 3, ARRAY[3.0, 4.0, 12.0]),
    ('risk_weights', 3, ARRAY[0.5, 0.25, 0.75]),
    ('system_rhs', 3, ARRAY[1.0, -2.0, 0.0]),
    ('system_solution', 3, ARRAY[1.0, -2.0, -2.0]);

INSERT INTO matrix_dataset (
    name,
    role,
    row_count,
    column_count,
    values
)
VALUES
(
    'feature_transform',
    'FEATURE_TRANSFORM',
    3,
    3,
    ARRAY[
        ARRAY[1.0, 0.2, 0.0],
        ARRAY[0.0, 1.0, 0.5],
        ARRAY[0.1, 0.0, 1.0]
    ]
),
(
    'linear_system_matrix',
    'SYSTEM_MATRIX',
    3,
    3,
    ARRAY[
        ARRAY[3.0, 2.0, -1.0],
        ARRAY[2.0, -2.0, 4.0],
        ARRAY[-1.0, 0.5, -1.0]
    ]
),
(
    'covariance_matrix',
    'COVARIANCE',
    3,
    3,
    ARRAY[
        ARRAY[2.5, 2.5, 3.0],
        ARRAY[2.5, 2.5, 2.75],
        ARRAY[3.0, 2.75, 5.3]
    ]
);

INSERT INTO tensor_dataset (
    name,
    rank,
    dimensions,
    values
)
VALUES (
    'batch_feature_tensor',
    3,
    ARRAY[2, 3, 4],
    ARRAY[
        0, 1, 2, 3,
        4, 5, 6, 7,
        8, 9, 10, 11,
        12, 13, 14, 15,
        16, 17, 18, 19,
        20, 21, 22, 23
    ]
);

INSERT INTO matrix_vector_operation (
    matrix_id,
    vector_id,
    operation_name
)
SELECT
    m.matrix_id,
    v.vector_id,
    'MATRIX_VECTOR_PRODUCT'
FROM matrix_dataset AS m
CROSS JOIN vector_dataset AS v
WHERE m.name = 'feature_transform'
  AND v.name = 'customer_metrics';

INSERT INTO linear_system (
    matrix_id,
    rhs_vector_id,
    solution_vector_id,
    residual_norm,
    solved_at
)
SELECT
    m.matrix_id,
    rhs.vector_id,
    solution.vector_id,
    0.0,
    CURRENT_TIMESTAMP
FROM matrix_dataset AS m
CROSS JOIN vector_dataset AS rhs
CROSS JOIN vector_dataset AS solution
WHERE m.name = 'linear_system_matrix'
  AND rhs.name = 'system_rhs'
  AND solution.name = 'system_solution';

-- Vector dot product using PostgreSQL array subscripting. The dimensions are
-- validated before the operation is recorded.
SELECT
    a.name AS left_vector,
    b.name AS right_vector,
    SUM(a.values[i] * b.values[i]) AS dot_product
FROM vector_dataset AS a
JOIN vector_dataset AS b
    ON a.dimension = b.dimension
CROSS JOIN LATERAL generate_series(1, a.dimension) AS indexes(i)
WHERE a.name = 'customer_metrics'
  AND b.name = 'risk_weights'
GROUP BY a.name, b.name;

-- Vector L2 norm.
SELECT
    name,
    sqrt(
        SUM(value * value)
    ) AS l2_norm
FROM vector_dataset
CROSS JOIN LATERAL unnest(values) AS elements(value)
WHERE name = 'customer_metrics'
GROUP BY name;

-- Normalize a vector by dividing each element by its L2 norm.
WITH vector_norm AS (
    SELECT
        vector_id,
        name,
        sqrt(
            SUM(value * value)
        ) AS l2_norm
    FROM vector_dataset
    CROSS JOIN LATERAL unnest(values) AS elements(value)
    WHERE name = 'customer_metrics'
    GROUP BY vector_id, name
)
SELECT
    v.name,
    ARRAY(
        SELECT value / NULLIF(n.l2_norm, 0)
        FROM unnest(v.values) AS elements(value)
    ) AS normalized_vector
FROM vector_dataset AS v
JOIN vector_norm AS n
    ON n.vector_id = v.vector_id;

-- Matrix trace demonstrates diagonal extraction from a square matrix.
SELECT
    name,
    (
        SELECT SUM(m.values[i][i])
        FROM generate_series(1, row_count) AS indexes(i)
    ) AS matrix_trace
FROM matrix_dataset AS m
WHERE row_count = column_count
  AND name = 'linear_system_matrix';

-- Matrix row sums demonstrate reduction along one matrix axis.
SELECT
    m.name,
    row_number,
    (
        SELECT SUM(value)
        FROM unnest(m.values[row_number]) AS row_values(value)
    ) AS row_sum
FROM matrix_dataset AS m
CROSS JOIN LATERAL generate_series(1, m.row_count) AS rows(row_number)
WHERE m.name = 'feature_transform';

-- Matrix column sums demonstrate reduction along the other axis.
SELECT
    m.name,
    column_number,
    (
        SELECT SUM(m.values[row_number][column_number])
        FROM generate_series(1, m.row_count) AS rows(row_number)
    ) AS column_sum
FROM matrix_dataset AS m
CROSS JOIN LATERAL generate_series(1, m.column_count) AS columns(column_number)
WHERE m.name = 'feature_transform';

-- Retrieve tensor metadata without expanding all tensor elements.
SELECT
    name,
    rank,
    dimensions,
    cardinality(values) AS element_count
FROM tensor_dataset
WHERE name = 'batch_feature_tensor';

-- Tensor reduction along the last logical dimension. The flattened storage
-- follows row-major order for the [2,3,4] example.
SELECT
    tensor.name,
    batch_index,
    row_index,
    SUM(tensor.values[offset_value + element_offset]) AS slice_sum
FROM tensor_dataset AS tensor
CROSS JOIN LATERAL generate_series(1, tensor.dimensions[1]) AS batch(batch_index)
CROSS JOIN LATERAL generate_series(1, tensor.dimensions[2]) AS row(row_index)
CROSS JOIN LATERAL generate_series(0, tensor.dimensions[3] - 1) AS element(element_offset)
CROSS JOIN LATERAL (
    SELECT
        (
            (batch_index - 1)
            * tensor.dimensions[2]
            * tensor.dimensions[3]
            +
            (row_index - 1)
            * tensor.dimensions[3]
            + 1
        ) AS offset_value
) AS offsets
WHERE tensor.name = 'batch_feature_tensor'
GROUP BY tensor.name, batch_index, row_index, offsets.offset_value
ORDER BY batch_index, row_index;

-- A relational view summarizes the dimensions of every stored linear-algebra
-- object and makes shape inspection convenient for data-quality checks.
CREATE VIEW linear_algebra_shapes AS
SELECT
    'VECTOR' AS object_type,
    name,
    ARRAY[dimension] AS dimensions
FROM vector_dataset
UNION ALL
SELECT
    'MATRIX' AS object_type,
    name,
    ARRAY[row_count, column_count] AS dimensions
FROM matrix_dataset
UNION ALL
SELECT
    'TENSOR' AS object_type,
    name,
    dimensions
FROM tensor_dataset;

SELECT *
FROM linear_algebra_shapes
ORDER BY object_type, name;

-- Dimension compatibility can be checked before a matrix-vector operation.
SELECT
    m.name AS matrix_name,
    v.name AS vector_name,
    m.row_count,
    m.column_count,
    v.dimension,
    (m.column_count = v.dimension) AS multiplication_is_valid
FROM matrix_dataset AS m
CROSS JOIN vector_dataset AS v
WHERE m.name = 'feature_transform'
  AND v.name = 'customer_metrics';

-- The database transaction demonstrates atomic recording of an operation.
BEGIN;

INSERT INTO matrix_vector_operation (
    matrix_id,
    vector_id,
    operation_name
)
SELECT
    m.matrix_id,
    v.vector_id,
    'PROJECTION_INPUT'
FROM matrix_dataset AS m
CROSS JOIN vector_dataset AS v
WHERE m.name = 'feature_transform'
  AND v.name = 'risk_weights';

COMMIT;

-- Invalid dimensional data is intentionally not inserted. The following
-- statements are examples of database-enforced failures and should be run
-- separately when testing constraint behavior:
--
-- INSERT INTO vector_dataset (name, dimension, values)
-- VALUES ('invalid_vector', 3, ARRAY[1.0, 2.0]);
--
-- INSERT INTO matrix_dataset
--     (name, role, row_count, column_count, values)
-- VALUES
--     ('invalid_matrix', 'SYSTEM_MATRIX', 2, 3,
--      ARRAY[ARRAY[1.0, 2.0], ARRAY[3.0, 4.0]]);
--
-- PostgreSQL rejects both statements because the declared shape does not
-- match the stored array shape.
