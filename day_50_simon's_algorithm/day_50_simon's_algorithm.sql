DROP SCHEMA IF EXISTS simon_algorithm CASCADE;
CREATE SCHEMA simon_algorithm;
SET search_path = simon_algorithm, public;

-- Simon's problem is represented relationally as a collection of
-- oracle instances, hidden periods, measurements, and GF(2) constraints.

CREATE TABLE problem (
    problem_id       BIGSERIAL PRIMARY KEY,
    problem_name     TEXT NOT NULL,
    n                INTEGER NOT NULL CHECK (n BETWEEN 1 AND 30),
    secret_period    TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(secret_period) = n),
    CHECK (secret_period ~ '^[01]+$'),
    CHECK (secret_period <> repeat('0', n))
);

CREATE TABLE oracle_input (
    problem_id       BIGINT NOT NULL REFERENCES problem(problem_id)
        ON DELETE CASCADE,
    input_value      INTEGER NOT NULL,
    output_value     INTEGER NOT NULL,
    PRIMARY KEY (problem_id, input_value),
    CHECK (input_value >= 0),
    CHECK (output_value >= 0)
);

CREATE TABLE measurement (
    measurement_id   BIGSERIAL PRIMARY KEY,
    problem_id       BIGINT NOT NULL REFERENCES problem(problem_id)
        ON DELETE CASCADE,
    measurement_bits TEXT NOT NULL,
    measured_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (measurement_bits ~ '^[01]+$')
);

CREATE TABLE status_check (
    status_check_id  BIGSERIAL PRIMARY KEY,
    problem_id       BIGINT NOT NULL REFERENCES problem(problem_id)
        ON DELETE CASCADE,
    check_name       TEXT NOT NULL,
    status           TEXT NOT NULL CHECK (
        status IN ('pending', 'passed', 'failed')
    ),
    detail           TEXT NOT NULL DEFAULT '',
    checked_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (problem_id, check_name)
);

CREATE INDEX measurement_problem_idx
    ON measurement(problem_id, measurement_id);

CREATE INDEX oracle_output_idx
    ON oracle_input(problem_id, output_value);

CREATE OR REPLACE FUNCTION bit_dot_mod2(
    left_bits TEXT,
    right_bits TEXT
)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    i INTEGER;
    result INTEGER := 0;
BEGIN
    IF length(left_bits) <> length(right_bits) THEN
        RAISE EXCEPTION 'bit vectors must have equal length';
    END IF;

    FOR i IN 1..length(left_bits) LOOP
        result := result # (
            (substr(left_bits, i, 1)::INTEGER) *
            (substr(right_bits, i, 1)::INTEGER)
        );
    END LOOP;

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION xor_bit_strings(
    left_bits TEXT,
    right_bits TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    i INTEGER;
    result TEXT := '';
BEGIN
    IF length(left_bits) <> length(right_bits) THEN
        RAISE EXCEPTION 'bit vectors must have equal length';
    END IF;

    FOR i IN 1..length(left_bits) LOOP
        result := result ||
            (
                (substr(left_bits, i, 1)::INTEGER)
                #
                (substr(right_bits, i, 1)::INTEGER)
            )::TEXT;
    END LOOP;

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION oracle_value(
    input_value INTEGER,
    secret_period TEXT
)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    secret_value INTEGER;
BEGIN
    secret_value := secret_period::BIT(30)::INTEGER;

    IF input_value < 0
       OR input_value >= (2 ^ length(secret_period))::INTEGER THEN
        RAISE EXCEPTION 'oracle input % outside domain', input_value;
    END IF;

    RETURN LEAST(input_value, input_value # secret_value);
END;
$$;

CREATE OR REPLACE FUNCTION validate_measurement(
    p_problem_id BIGINT,
    p_measurement TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    expected_n INTEGER;
    secret TEXT;
BEGIN
    SELECT n, secret_period
    INTO expected_n, secret
    FROM problem
    WHERE problem_id = p_problem_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'problem % does not exist', p_problem_id;
    END IF;

    IF length(p_measurement) <> expected_n
       OR p_measurement !~ '^[01]+$' THEN
        RETURN FALSE;
    END IF;

    -- Every Simon measurement must satisfy y · s = 0 mod 2.
    RETURN bit_dot_mod2(p_measurement, secret) = 0;
END;
$$;

CREATE OR REPLACE FUNCTION enforce_valid_measurement()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT validate_measurement(
        NEW.problem_id,
        NEW.measurement_bits
    ) THEN
        RAISE EXCEPTION
            'measurement % violates Simon constraint for problem %',
            NEW.measurement_bits,
            NEW.problem_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER measurement_validation_trigger
BEFORE INSERT OR UPDATE ON measurement
FOR EACH ROW
EXECUTE FUNCTION enforce_valid_measurement();

CREATE OR REPLACE FUNCTION independent_measurement_count(
    p_problem_id BIGINT
)
RETURNS INTEGER
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    n INTEGER;
    rank INTEGER := 0;
    column_index INTEGER;
    row_index INTEGER;
    pivot_row INTEGER;
    matrix TEXT[];
    temporary TEXT;
BEGIN
    SELECT problem.n
    INTO n
    FROM problem
    WHERE problem_id = p_problem_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'problem % does not exist', p_problem_id;
    END IF;

    SELECT ARRAY_AGG(measurement_bits ORDER BY measurement_id)
    INTO matrix
    FROM measurement
    WHERE problem_id = p_problem_id;

    IF matrix IS NULL THEN
        RETURN 0;
    END IF;

    /*
     * This routine performs row reduction over GF(2).
     * PostgreSQL is used here to store and validate the evidence;
     * the explicit loop makes the algebra visible and deterministic.
     */
    FOR column_index IN 1..n LOOP
        pivot_row := NULL;

        FOR row_index IN rank + 1..COALESCE(array_length(matrix, 1), 0) LOOP
            IF substr(matrix[row_index], column_index, 1) = '1' THEN
                pivot_row := row_index;
                EXIT;
            END IF;
        END LOOP;

        IF pivot_row IS NOT NULL THEN
            rank := rank + 1;

            temporary := matrix[rank];
            matrix[rank] := matrix[pivot_row];
            matrix[pivot_row] := temporary;

            FOR row_index IN 1..COALESCE(array_length(matrix, 1), 0) LOOP
                IF row_index <> rank
                   AND substr(matrix[row_index], column_index, 1) = '1' THEN
                    matrix[row_index] :=
                        xor_bit_strings(
                            matrix[row_index],
                            matrix[rank]
                        );
                END IF;
            END LOOP;
        END IF;

        IF rank = COALESCE(array_length(matrix, 1), 0) THEN
            EXIT;
        END IF;
    END LOOP;

    RETURN rank;
END;
$$;

CREATE VIEW measurement_status AS
SELECT
    p.problem_id,
    p.problem_name,
    p.n,
    p.secret_period,
    COUNT(m.measurement_id) AS observations,
    independent_measurement_count(p.problem_id) AS independent_equations,
    GREATEST(p.n - 1, 0) AS equations_required,
    CASE
        WHEN independent_measurement_count(p.problem_id) >= GREATEST(p.n - 1, 0)
            THEN 'determined'
        WHEN COUNT(m.measurement_id) > 0
            THEN 'constrained'
        ELSE 'unobserved'
    END AS recovery_state
FROM problem p
LEFT JOIN measurement m
    ON m.problem_id = p.problem_id
GROUP BY p.problem_id, p.problem_name, p.n, p.secret_period;

CREATE VIEW oracle_collision_report AS
SELECT
    oi.problem_id,
    oi.output_value,
    COUNT(*) AS preimage_count,
    MIN(oi.input_value) AS first_input,
    MAX(oi.input_value) AS second_input,
    CASE
        WHEN COUNT(*) = 2 THEN 'valid Simon pair'
        ELSE 'promise violation'
    END AS collision_state
FROM oracle_input oi
GROUP BY oi.problem_id, oi.output_value;

CREATE VIEW problem_integrity_report AS
SELECT
    p.problem_id,
    p.problem_name,
    p.n,
    p.secret_period,
    COALESCE(
        BOOL_AND(
            oracle_value(x.input_value, p.secret_period)
            = x.output_value
        ),
        TRUE
    ) AS oracle_values_correct,
    COALESCE(
        BOOL_AND(
            x.output_value =
            oracle_value(x.input_value # p.secret_period, p.secret_period)
        ),
        TRUE
    ) AS period_property_holds
FROM problem p
LEFT JOIN oracle_input x
    ON x.problem_id = p.problem_id
GROUP BY
    p.problem_id,
    p.problem_name,
    p.n,
    p.secret_period;

BEGIN;

INSERT INTO problem (
    problem_name,
    n,
    secret_period
)
VALUES
    ('Simon demonstration', 4, '1011'),
    ('Simon enterprise simulation', 5, '11010');

INSERT INTO oracle_input (
    problem_id,
    input_value,
    output_value
)
SELECT
    p.problem_id,
    x,
    oracle_value(x, p.secret_period)
FROM problem p
CROSS JOIN LATERAL generate_series(
    0,
    (2 ^ p.n)::INTEGER - 1
) AS x;

INSERT INTO status_check (
    problem_id,
    check_name,
    status,
    detail
)
SELECT
    problem_id,
    'oracle-period-property',
    CASE
        WHEN period_property_holds THEN 'passed'
        ELSE 'failed'
    END,
    'Checks f(x) = f(x XOR s) across stored oracle inputs.'
FROM problem_integrity_report;

COMMIT;

-- Valid measurements are orthogonal to the hidden period.
INSERT INTO measurement (problem_id, measurement_bits)
SELECT problem_id, measurement_bits
FROM (
    VALUES
        (1::BIGINT, '0000'),
        (1::BIGINT, '0110'),
        (1::BIGINT, '1010'),
        (1::BIGINT, '1100'),
        (2::BIGINT, '00000'),
        (2::BIGINT, '00101'),
        (2::BIGINT, '01001'),
        (2::BIGINT, '10011')
) AS samples(problem_id, measurement_bits)
WHERE validate_measurement(problem_id, measurement_bits);

-- A failed validation is demonstrated without corrupting the table.
DO $$
BEGIN
    IF validate_measurement(1, '0001') THEN
        RAISE EXCEPTION
            'test failure: 0001 should not satisfy 0001 · 1011 = 0';
    END IF;
END;
$$;

-- Retrieval and evaluation of the hidden-period constraints.
SELECT
    problem_name,
    n,
    measurement_bits,
    bit_dot_mod2(measurement_bits, secret_period) AS dot_product_mod2
FROM problem
JOIN measurement USING (problem_id)
ORDER BY problem_id, measurement_id;

-- Recovery readiness: n-1 independent equations are sufficient.
SELECT
    problem_name,
    n,
    observations,
    independent_equations,
    equations_required,
    recovery_state
FROM measurement_status
ORDER BY problem_id;

-- Oracle integrity and the two-to-one promise.
SELECT *
FROM problem_integrity_report
ORDER BY problem_id;

SELECT
    problem_id,
    output_value,
    preimage_count,
    first_input,
    second_input,
    collision_state
FROM oracle_collision_report
ORDER BY problem_id, output_value;

-- A transactional example: an invalid measurement is rolled back.
BEGIN;

SAVEPOINT before_invalid_measurement;

DO $$
BEGIN
    BEGIN
        INSERT INTO measurement (
            problem_id,
            measurement_bits
        )
        VALUES (1, '0001');

        RAISE EXCEPTION
            'invalid measurement unexpectedly accepted';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Rejected invalid Simon measurement as expected: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT before_invalid_measurement;
COMMIT;

-- Reporting query for operational use.
SELECT
    p.problem_name,
    p.n,
    p.secret_period,
    COUNT(m.measurement_id) AS collected_measurements,
    independent_measurement_count(p.problem_id) AS rank,
    CASE
        WHEN independent_measurement_count(p.problem_id) >= p.n - 1
            THEN 'hidden period uniquely recoverable'
        ELSE 'more independent measurements required'
    END AS decision
FROM problem p
LEFT JOIN measurement m
    ON m.problem_id = p.problem_id
GROUP BY
    p.problem_id,
    p.problem_name,
    p.n,
    p.secret_period
ORDER BY p.problem_id;
