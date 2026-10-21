-- Quantum Fourier Transform fundamentals in PostgreSQL.
--
-- PostgreSQL is used here as an experimental data model for QFT states,
-- Fourier amplitudes, probability distributions, and verification results.
--
-- The database does not replace a numerical quantum simulator. It provides
-- persistent relational structures for reproducible QFT experiments,
-- normalized-state validation, measurement results, and analytical reports.

DROP VIEW IF EXISTS qft_measurement_report;
DROP VIEW IF EXISTS qft_experiment_report;
DROP FUNCTION IF EXISTS record_measurement(BIGINT, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS validate_quantum_state(BIGINT);
DROP FUNCTION IF EXISTS qft_amplitude(BIGINT, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS qft_phase(INTEGER, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS normalize_experiment(BIGINT);

DROP TABLE IF EXISTS measurement_result CASCADE;
DROP TABLE IF EXISTS qft_amplitude CASCADE;
DROP TABLE IF EXISTS qft_experiment CASCADE;

CREATE TABLE qft_experiment (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    qubits INTEGER NOT NULL,
    dimension INTEGER GENERATED ALWAYS AS (2 ^ qubits) STORED,
    direction TEXT NOT NULL DEFAULT 'forward',
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT qft_experiment_qubits_ck
        CHECK (qubits BETWEEN 1 AND 12),

    CONSTRAINT qft_experiment_direction_ck
        CHECK (direction IN ('forward', 'inverse'))
);

CREATE TABLE qft_amplitude (
    experiment_id BIGINT NOT NULL
        REFERENCES qft_experiment(experiment_id)
        ON DELETE CASCADE,

    basis_index INTEGER NOT NULL,

    real_part DOUBLE PRECISION NOT NULL,
    imaginary_part DOUBLE PRECISION NOT NULL,

    amplitude_probability DOUBLE PRECISION
        GENERATED ALWAYS AS (
            real_part * real_part
            + imaginary_part * imaginary_part
        ) STORED,

    PRIMARY KEY (experiment_id, basis_index),

    CONSTRAINT qft_amplitude_index_ck
        CHECK (basis_index >= 0),

    CONSTRAINT qft_amplitude_finite_ck
        CHECK (
            real_part = real_part
            AND imaginary_part = imaginary_part
        )
);

CREATE TABLE measurement_result (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES qft_experiment(experiment_id)
        ON DELETE CASCADE,

    basis_index INTEGER NOT NULL,
    shots INTEGER NOT NULL,
    observed_count INTEGER NOT NULL,

    probability_estimate DOUBLE PRECISION GENERATED ALWAYS AS (
        observed_count::DOUBLE PRECISION / NULLIF(shots, 0)
    ) STORED,

    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT measurement_shots_ck
        CHECK (shots > 0),

    CONSTRAINT measurement_count_ck
        CHECK (
            observed_count >= 0
            AND observed_count <= shots
        ),

    CONSTRAINT measurement_index_ck
        CHECK (basis_index >= 0)
);

CREATE INDEX qft_amplitude_probability_idx
    ON qft_amplitude (experiment_id, amplitude_probability DESC);

CREATE INDEX measurement_experiment_idx
    ON measurement_result (experiment_id, measured_at DESC);

COMMENT ON TABLE qft_experiment IS
    'Metadata for reproducible QFT state-vector experiments.';

COMMENT ON TABLE qft_amplitude IS
    'Complex computational-basis amplitudes and their Born probabilities.';

COMMENT ON COLUMN qft_amplitude.amplitude_probability IS
    'Squared complex magnitude |a|^2, representing measurement probability.';

COMMENT ON TABLE measurement_result IS
    'Observed computational-basis outcomes from repeated measurements.';


CREATE OR REPLACE FUNCTION qft_phase(
    p_index INTEGER,
    p_frequency INTEGER,
    p_dimension INTEGER
)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_dimension <= 0 THEN
        RAISE EXCEPTION 'QFT dimension must be positive';
    END IF;

    RETURN 2.0 * pi()
        * p_index::DOUBLE PRECISION
        * p_frequency::DOUBLE PRECISION
        / p_dimension::DOUBLE PRECISION;
END;
$$;


CREATE OR REPLACE FUNCTION qft_amplitude(
    p_experiment_id BIGINT,
    p_frequency INTEGER,
    p_dimension INTEGER
)
RETURNS TABLE (
    real_part DOUBLE PRECISION,
    imaginary_part DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        COALESCE(
            SUM(
                a.real_part * cos(
                    qft_phase(
                        a.basis_index,
                        p_frequency,
                        p_dimension
                    )
                )
                -
                a.imaginary_part * sin(
                    qft_phase(
                        a.basis_index,
                        p_frequency,
                        p_dimension
                    )
                )
            ),
            0.0
        ) / sqrt(p_dimension::DOUBLE PRECISION) AS real_part,

        COALESCE(
            SUM(
                a.real_part * sin(
                    qft_phase(
                        a.basis_index,
                        p_frequency,
                        p_dimension
                    )
                )
                +
                a.imaginary_part * cos(
                    qft_phase(
                        a.basis_index,
                        p_frequency,
                        p_dimension
                    )
                )
            ),
            0.0
        ) / sqrt(p_dimension::DOUBLE PRECISION) AS imaginary_part

    FROM qft_amplitude AS a
    WHERE a.experiment_id = p_experiment_id;
$$;


CREATE OR REPLACE FUNCTION validate_quantum_state(
    p_experiment_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    expected_dimension INTEGER;
    actual_dimension INTEGER;
    norm_squared DOUBLE PRECISION;
BEGIN
    SELECT dimension
    INTO expected_dimension
    FROM qft_experiment
    WHERE experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment % does not exist',
            p_experiment_id;
    END IF;

    SELECT COUNT(*)
    INTO actual_dimension
    FROM qft_amplitude
    WHERE experiment_id = p_experiment_id;

    IF actual_dimension <> expected_dimension THEN
        RETURN FALSE;
    END IF;

    SELECT COALESCE(SUM(amplitude_probability), 0.0)
    INTO norm_squared
    FROM qft_amplitude
    WHERE experiment_id = p_experiment_id;

    RETURN abs(norm_squared - 1.0) < 1e-10;
END;
$$;


CREATE OR REPLACE FUNCTION normalize_experiment(
    p_experiment_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    norm DOUBLE PRECISION;
BEGIN
    SELECT sqrt(
        COALESCE(SUM(amplitude_probability), 0.0)
    )
    INTO norm
    FROM qft_amplitude
    WHERE experiment_id = p_experiment_id;

    IF norm IS NULL OR norm = 0 THEN
        RAISE EXCEPTION
            'Experiment % has a zero norm',
            p_experiment_id;
    END IF;

    UPDATE qft_amplitude
    SET
        real_part = real_part / norm,
        imaginary_part = imaginary_part / norm
    WHERE experiment_id = p_experiment_id;
END;
$$;


CREATE OR REPLACE FUNCTION record_measurement(
    p_experiment_id BIGINT,
    p_basis_index INTEGER,
    p_count INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_shots INTEGER;
BEGIN
    SELECT COALESCE(MAX(shots), 0)
    INTO experiment_shots
    FROM measurement_result
    WHERE experiment_id = p_experiment_id;

    IF NOT EXISTS (
        SELECT 1
        FROM qft_experiment
        WHERE experiment_id = p_experiment_id
    ) THEN
        RAISE EXCEPTION
            'Experiment % does not exist',
            p_experiment_id;
    END IF;

    IF p_basis_index < 0 THEN
        RAISE EXCEPTION 'Basis index cannot be negative';
    END IF;

    IF p_count < 0 THEN
        RAISE EXCEPTION 'Observed count cannot be negative';
    END IF;

    IF p_count > experiment_shots AND experiment_shots > 0 THEN
        RAISE EXCEPTION
            'Observed count % exceeds recorded shots %',
            p_count,
            experiment_shots;
    END IF;

    INSERT INTO measurement_result (
        experiment_id,
        basis_index,
        shots,
        observed_count
    )
    VALUES (
        p_experiment_id,
        p_basis_index,
        GREATEST(experiment_shots, 1),
        p_count
    );
END;
$$;


-- A basis state |001> in a three-qubit register.
INSERT INTO qft_experiment (
    name,
    qubits,
    direction,
    description
)
VALUES (
    'basis_state_001',
    3,
    'forward',
    'Forward QFT of the computational basis state |001>.'
);

-- A periodic state proportional to |000> + |100>.
INSERT INTO qft_experiment (
    name,
    qubits,
    direction,
    description
)
VALUES (
    'periodic_state',
    3,
    'forward',
    'Forward QFT of a period-two state in an eight-dimensional register.'
);

-- A state used to verify inverse QFT behavior.
INSERT INTO qft_experiment (
    name,
    qubits,
    direction,
    description
)
VALUES (
    'inverse_reconstruction',
    2,
    'inverse',
    'Inverse-QFT reconstruction test for a normalized complex state.'
);


-- Store |001>.
INSERT INTO qft_amplitude (
    experiment_id,
    basis_index,
    real_part,
    imaginary_part
)
SELECT
    experiment_id,
    index,
    CASE WHEN index = 1 THEN 1.0 ELSE 0.0 END,
    0.0
FROM qft_experiment
CROSS JOIN generate_series(0, 7) AS series(index)
WHERE name = 'basis_state_001';


-- Store (|000> + |100>) / sqrt(2).
INSERT INTO qft_amplitude (
    experiment_id,
    basis_index,
    real_part,
    imaginary_part
)
SELECT
    experiment_id,
    index,
    CASE
        WHEN index IN (0, 4)
            THEN 1.0 / sqrt(2.0)
        ELSE 0.0
    END,
    0.0
FROM qft_experiment
CROSS JOIN generate_series(0, 7) AS series(index)
WHERE name = 'periodic_state';


-- Store a normalized complex four-dimensional state.
WITH raw AS (
    SELECT
        sqrt(
            (1.0 ^ 2 + 1.0 ^ 2)
            + (2.0 ^ 2 + (-1.0) ^ 2)
            + ((-1.0) ^ 2 + 0.5 ^ 2)
            + (0.25 ^ 2 + (-2.0) ^ 2)
        ) AS norm
)
INSERT INTO qft_amplitude (
    experiment_id,
    basis_index,
    real_part,
    imaginary_part
)
SELECT
    e.experiment_id,
    v.basis_index,
    v.real_part / raw.norm,
    v.imaginary_part / raw.norm
FROM qft_experiment AS e
CROSS JOIN raw
CROSS JOIN (
    VALUES
        (0, 1.0, 1.0),
        (1, 2.0, -1.0),
        (2, -1.0, 0.5),
        (3, 0.25, -2.0)
) AS v(basis_index, real_part, imaginary_part)
WHERE e.name = 'inverse_reconstruction';


-- Verify all stored states are normalized and dimensionally complete.
SELECT
    e.name,
    e.qubits,
    e.dimension,
    COUNT(a.basis_index) AS stored_amplitudes,
    ROUND(SUM(a.amplitude_probability)::NUMERIC, 12)
        AS norm_squared,
    validate_quantum_state(e.experiment_id)
        AS valid_state
FROM qft_experiment AS e
LEFT JOIN qft_amplitude AS a
    ON a.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.name,
    e.qubits,
    e.dimension
ORDER BY e.experiment_id;


-- Calculate the forward QFT of the periodic state directly in SQL.
WITH experiment AS (
    SELECT experiment_id, dimension
    FROM qft_experiment
    WHERE name = 'periodic_state'
),
frequencies AS (
    SELECT
        e.experiment_id,
        e.dimension,
        generate_series(0, e.dimension - 1) AS frequency
    FROM experiment AS e
),
transformed AS (
    SELECT
        f.frequency,
        q.real_part,
        q.imaginary_part,
        q.real_part * q.real_part
            + q.imaginary_part * q.imaginary_part
            AS probability
    FROM frequencies AS f
    CROSS JOIN LATERAL qft_amplitude(
        f.experiment_id,
        f.frequency,
        f.dimension
    ) AS q
)
SELECT
    frequency,
    ROUND(real_part::NUMERIC, 8) AS real_part,
    ROUND(imaginary_part::NUMERIC, 8) AS imaginary_part,
    ROUND(probability::NUMERIC, 8) AS probability
FROM transformed
ORDER BY frequency;


-- Transactional measurement recording.
BEGIN;

WITH target AS (
    SELECT experiment_id
    FROM qft_experiment
    WHERE name = 'periodic_state'
)
INSERT INTO measurement_result (
    experiment_id,
    basis_index,
    shots,
    observed_count
)
SELECT
    target.experiment_id,
    sample.basis_index,
    2000,
    sample.observed_count
FROM target
CROSS JOIN (
    VALUES
        (0, 1000),
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 1000),
        (5, 0),
        (6, 0),
        (7, 0)
) AS sample(basis_index, observed_count);

COMMIT;


-- Measurement report compares observed frequencies with stored probabilities.
CREATE OR REPLACE VIEW qft_measurement_report AS
SELECT
    e.name AS experiment,
    m.basis_index,
    m.shots,
    m.observed_count,
    ROUND(m.probability_estimate::NUMERIC, 6)
        AS observed_probability,
    ROUND(a.amplitude_probability::NUMERIC, 6)
        AS theoretical_probability,
    ROUND(
        (
            m.probability_estimate
            - a.amplitude_probability
        )::NUMERIC,
        6
    ) AS probability_error
FROM measurement_result AS m
JOIN qft_experiment AS e
    ON e.experiment_id = m.experiment_id
JOIN qft_amplitude AS a
    ON a.experiment_id = m.experiment_id
    AND a.basis_index = m.basis_index
ORDER BY
    e.name,
    m.basis_index;


CREATE OR REPLACE VIEW qft_experiment_report AS
SELECT
    e.experiment_id,
    e.name,
    e.qubits,
    e.dimension,
    e.direction,
    COUNT(a.basis_index) AS amplitude_count,
    ROUND(
        COALESCE(SUM(a.amplitude_probability), 0.0)::NUMERIC,
        12
    ) AS norm_squared,
    validate_quantum_state(e.experiment_id)
        AS normalized_and_complete
FROM qft_experiment AS e
LEFT JOIN qft_amplitude AS a
    ON a.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.name,
    e.qubits,
    e.dimension,
    e.direction
ORDER BY e.experiment_id;


-- Final analytical reports.
SELECT *
FROM qft_experiment_report;

SELECT *
FROM qft_measurement_report;


-- Demonstrate a rejected state without leaving a partial write.
BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM qft_amplitude
        WHERE experiment_id = (
            SELECT experiment_id
            FROM qft_experiment
            WHERE name = 'basis_state_001'
        )
        AND basis_index = 99
    ) THEN
        RAISE EXCEPTION 'Unexpected invalid basis index found';
    END IF;
END;
$$;

ROLLBACK;
