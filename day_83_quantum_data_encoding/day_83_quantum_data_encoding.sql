-- ============================================================
-- QUANTUM DATA ENCODING MANAGEMENT DATABASE
-- PostgreSQL 15+
--
-- Domain:
--   1. Basis encoding
--   2. Angle encoding
--   3. Amplitude encoding
--   4. Feature datasets
--   5. Encoding jobs
--   6. Quantum state representations
--   7. Resource governance
--   8. Measurement records
--   9. Validation and reporting
--
-- The database stores encoding metadata and numerical
-- representations. It does not execute quantum circuits.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_encoding;

SET search_path TO quantum_encoding, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE encoding_method AS ENUM (
    'BASIS',
    'ANGLE',
    'AMPLITUDE'
);

CREATE TYPE job_status AS ENUM (
    'SUBMITTED',
    'PROCESSING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE measurement_status AS ENUM (
    'COMPLETED',
    'FAILED'
);

-- ============================================================
-- 2. ORGANIZATIONAL AND DATASET MANAGEMENT
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    dataset_name VARCHAR(150) NOT NULL,

    description TEXT,

    feature_count INTEGER NOT NULL
        CHECK (feature_count > 0),

    source_format VARCHAR(30) NOT NULL
        CHECK (source_format IN (
            'CSV',
            'JSON',
            'NUMERIC_ARRAY',
            'DATABASE'
        )),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (organization_id, dataset_name)
);

CREATE TABLE dataset_features (
    feature_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id) ON DELETE CASCADE,

    feature_position INTEGER NOT NULL
        CHECK (feature_position >= 0),

    feature_name VARCHAR(100) NOT NULL,

    feature_value DOUBLE PRECISION NOT NULL,

    minimum_value DOUBLE PRECISION,

    maximum_value DOUBLE PRECISION,

    is_binary BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE (dataset_id, feature_position),
    UNIQUE (dataset_id, feature_name),

    CHECK (
        minimum_value IS NULL
        OR maximum_value IS NULL
        OR minimum_value <= maximum_value
    ),

    CHECK (
        NOT is_binary
        OR feature_value IN (0.0, 1.0)
    )
);

CREATE INDEX idx_dataset_features_dataset
    ON dataset_features(dataset_id, feature_position);

-- ============================================================
-- 3. QUANTUM ENCODING CONFIGURATION
-- ============================================================

CREATE TABLE encoding_configurations (
    configuration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    configuration_name VARCHAR(120) NOT NULL UNIQUE,

    method encoding_method NOT NULL,

    minimum_value DOUBLE PRECISION NOT NULL DEFAULT 0.0,

    maximum_value DOUBLE PRECISION NOT NULL DEFAULT 1.0,

    maximum_qubits INTEGER NOT NULL DEFAULT 16
        CHECK (maximum_qubits >= 0),

    maximum_memory_bytes BIGINT NOT NULL
        CHECK (maximum_memory_bytes > 0),

    allow_zero_padding BOOLEAN NOT NULL DEFAULT TRUE,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        method <> 'ANGLE'
        OR maximum_value > minimum_value
    )
);

-- ============================================================
-- 4. ENCODING JOBS
-- ============================================================

CREATE TABLE encoding_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_reference UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id),

    configuration_id BIGINT NOT NULL
        REFERENCES encoding_configurations(configuration_id),

    status job_status NOT NULL DEFAULT 'SUBMITTED',

    requested_by VARCHAR(120) NOT NULL,

    input_dimension INTEGER NOT NULL
        CHECK (input_dimension > 0),

    qubit_count INTEGER
        CHECK (qubit_count >= 0),

    state_dimension INTEGER
        CHECK (state_dimension > 0),

    original_norm DOUBLE PRECISION
        CHECK (original_norm IS NULL OR original_norm > 0),

    estimated_memory_bytes BIGINT
        CHECK (
            estimated_memory_bytes IS NULL
            OR estimated_memory_bytes > 0
        ),

    error_message TEXT,

    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CHECK (
        completed_at IS NULL
        OR started_at IS NOT NULL
    ),

    CHECK (
        status <> 'COMPLETED'
        OR (
            qubit_count IS NOT NULL
            AND state_dimension IS NOT NULL
            AND estimated_memory_bytes IS NOT NULL
            AND completed_at IS NOT NULL
        )
    ),

    CHECK (
        status <> 'FAILED'
        OR error_message IS NOT NULL
    )
);

CREATE INDEX idx_encoding_jobs_status
    ON encoding_jobs(status, submitted_at DESC);

CREATE INDEX idx_encoding_jobs_dataset
    ON encoding_jobs(dataset_id, submitted_at DESC);

-- ============================================================
-- 5. QUANTUM STATE AMPLITUDES
-- ============================================================

CREATE TABLE quantum_states (
    state_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL UNIQUE
        REFERENCES encoding_jobs(job_id) ON DELETE CASCADE,

    state_dimension INTEGER NOT NULL
        CHECK (state_dimension > 0),

    normalization_norm DOUBLE PRECISION NOT NULL
        CHECK (normalization_norm > 0),

    normalization_error DOUBLE PRECISION NOT NULL
        CHECK (normalization_error >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE state_amplitudes (
    amplitude_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    state_id BIGINT NOT NULL
        REFERENCES quantum_states(state_id) ON DELETE CASCADE,

    basis_index INTEGER NOT NULL
        CHECK (basis_index >= 0),

    real_part DOUBLE PRECISION NOT NULL,

    imaginary_part DOUBLE PRECISION NOT NULL,

    probability DOUBLE PRECISION GENERATED ALWAYS AS (
        real_part * real_part
        + imaginary_part * imaginary_part
    ) STORED,

    UNIQUE (state_id, basis_index)
);

CREATE INDEX idx_state_amplitudes_probability
    ON state_amplitudes(state_id, probability DESC);

-- ============================================================
-- 6. ANGLE ENCODING ROTATIONS
-- ============================================================

CREATE TABLE angle_rotations (
    rotation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES encoding_jobs(job_id) ON DELETE CASCADE,

    qubit_index INTEGER NOT NULL
        CHECK (qubit_index >= 0),

    feature_id BIGINT NOT NULL
        REFERENCES dataset_features(feature_id),

    rotation_gate VARCHAR(10) NOT NULL DEFAULT 'RY'
        CHECK (rotation_gate = 'RY'),

    angle_radians DOUBLE PRECISION NOT NULL
        CHECK (angle_radians BETWEEN 0 AND pi()),

    UNIQUE (job_id, qubit_index)
);

-- ============================================================
-- 7. BRANCHLESS BASIS ENCODING METADATA
-- ============================================================

CREATE TABLE basis_encodings (
    basis_encoding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL UNIQUE
        REFERENCES encoding_jobs(job_id) ON DELETE CASCADE,

    bitstring VARCHAR(128) NOT NULL
        CHECK (bitstring ~ '^[01]+$'),

    basis_index BIGINT NOT NULL
        CHECK (basis_index >= 0),

    UNIQUE (job_id, bitstring)
);

-- ============================================================
-- 8. RESOURCE GOVERNANCE
-- ============================================================

CREATE TABLE resource_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(120) NOT NULL UNIQUE,

    maximum_qubits INTEGER NOT NULL
        CHECK (maximum_qubits >= 0),

    maximum_memory_bytes BIGINT NOT NULL
        CHECK (maximum_memory_bytes > 0),

    amplitude_encoding_allowed BOOLEAN NOT NULL DEFAULT TRUE,

    angle_encoding_allowed BOOLEAN NOT NULL DEFAULT TRUE,

    basis_encoding_allowed BOOLEAN NOT NULL DEFAULT TRUE,

    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE job_resource_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES encoding_jobs(job_id) ON DELETE CASCADE,

    policy_id BIGINT NOT NULL
        REFERENCES resource_policies(policy_id),

    eligible BOOLEAN NOT NULL,

    estimated_memory_bytes BIGINT NOT NULL
        CHECK (estimated_memory_bytes >= 0),

    evaluation_details JSONB NOT NULL DEFAULT '{}'::jsonb,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_resource_evaluations_job
    ON job_resource_evaluations(job_id, evaluated_at DESC);

-- ============================================================
-- 9. MEASUREMENT MANAGEMENT
-- ============================================================

CREATE TABLE measurement_runs (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES encoding_jobs(job_id) ON DELETE CASCADE,

    shots INTEGER NOT NULL
        CHECK (shots > 0),

    status measurement_status NOT NULL DEFAULT 'COMPLETED',

    random_seed BIGINT,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE measurement_outcomes (
    outcome_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    measurement_id BIGINT NOT NULL
        REFERENCES measurement_runs(measurement_id) ON DELETE CASCADE,

    bitstring VARCHAR(128) NOT NULL
        CHECK (bitstring ~ '^[01]+$'),

    occurrence_count INTEGER NOT NULL
        CHECK (occurrence_count >= 0),

    UNIQUE (measurement_id, bitstring)
);

-- ============================================================
-- 10. INTEGRITY TRIGGERS
-- ============================================================

CREATE OR REPLACE FUNCTION validate_dataset_feature_position()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
    current_count INTEGER;
BEGIN
    SELECT feature_count
    INTO expected_count
    FROM datasets
    WHERE dataset_id = NEW.dataset_id;

    SELECT COUNT(*)
    INTO current_count
    FROM dataset_features
    WHERE dataset_id = NEW.dataset_id
      AND feature_id <> COALESCE(NEW.feature_id, -1);

    IF current_count >= expected_count THEN
        RAISE EXCEPTION
            'Dataset feature capacity exceeded for dataset %',
            NEW.dataset_id;
    END IF;

    IF NEW.feature_position >= expected_count THEN
        RAISE EXCEPTION
            'Feature position exceeds declared dataset dimension.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_dataset_feature
BEFORE INSERT ON dataset_features
FOR EACH ROW
EXECUTE FUNCTION validate_dataset_feature_position();


CREATE OR REPLACE FUNCTION validate_state_amplitude()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_dimension INTEGER;
BEGIN
    SELECT state_dimension
    INTO expected_dimension
    FROM quantum_states
    WHERE state_id = NEW.state_id;

    IF NEW.basis_index >= expected_dimension THEN
        RAISE EXCEPTION
            'Amplitude basis index exceeds state dimension.';
    END IF;

    IF NEW.probability > 1.0000000001 THEN
        RAISE EXCEPTION
            'Individual amplitude probability cannot exceed one.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_state_amplitude
BEFORE INSERT OR UPDATE ON state_amplitudes
FOR EACH ROW
EXECUTE FUNCTION validate_state_amplitude();


CREATE OR REPLACE FUNCTION validate_measurement_outcome()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_qubits INTEGER;
    expected_shots INTEGER;
BEGIN
    SELECT j.qubit_count, m.shots
    INTO expected_qubits, expected_shots
    FROM measurement_runs m
    JOIN encoding_jobs j ON j.job_id = m.job_id
    WHERE m.measurement_id = NEW.measurement_id;

    IF expected_qubits IS NULL THEN
        RAISE EXCEPTION
            'Measurement requires a completed encoding job.';
    END IF;

    IF LENGTH(NEW.bitstring) <> expected_qubits THEN
        RAISE EXCEPTION
            'Measurement bitstring length must equal qubit count.';
    END IF;

    IF NEW.occurrence_count > expected_shots THEN
        RAISE EXCEPTION
            'Outcome count exceeds total measurement shots.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_measurement_outcome
BEFORE INSERT OR UPDATE ON measurement_outcomes
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_outcome();

-- ============================================================
-- 11. ENCODING RESOURCE ESTIMATION
-- ============================================================

CREATE OR REPLACE FUNCTION estimate_encoding_resources(
    p_method encoding_method,
    p_dimension INTEGER
)
RETURNS TABLE (
    required_qubits INTEGER,
    state_dimension BIGINT,
    estimated_memory_bytes BIGINT
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    q INTEGER := 0;
    d BIGINT := 1;
BEGIN
    IF p_dimension <= 0 THEN
        RAISE EXCEPTION 'Feature dimension must be positive.';
    END IF;

    IF p_method = 'BASIS' OR p_method = 'ANGLE' THEN
        q := p_dimension;
    ELSE
        WHILE d < p_dimension LOOP
            d := d * 2;
            q := q + 1;
        END LOOP;
    END IF;

    IF p_method = 'BASIS' OR p_method = 'ANGLE' THEN
        d := 1::BIGINT << q;
    END IF;

    -- Real and imaginary components each use 8 bytes.
    required_qubits := q;
    state_dimension := d;
    estimated_memory_bytes := d * 16;

    RETURN NEXT;
END;
$$;

-- ============================================================
-- 12. ENCODING JOB SUBMISSION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE submit_encoding_job(
    p_dataset_id BIGINT,
    p_configuration_id BIGINT,
    p_requested_by VARCHAR(120),
    OUT p_job_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_dimension INTEGER;
    v_method encoding_method;
    v_enabled BOOLEAN;
    v_estimate RECORD;
    v_max_qubits INTEGER;
    v_max_memory BIGINT;
    v_feature_count INTEGER;
BEGIN
    SELECT feature_count
    INTO v_dimension
    FROM datasets
    WHERE dataset_id = p_dataset_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dataset does not exist.';
    END IF;

    SELECT method, enabled, maximum_qubits, maximum_memory_bytes
    INTO v_method, v_enabled, v_max_qubits, v_max_memory
    FROM encoding_configurations
    WHERE configuration_id = p_configuration_id;

    IF NOT FOUND OR NOT v_enabled THEN
        RAISE EXCEPTION 'Encoding configuration is unavailable.';
    END IF;

    SELECT COUNT(*)
    INTO v_feature_count
    FROM dataset_features
    WHERE dataset_id = p_dataset_id;

    IF v_feature_count <> v_dimension THEN
        RAISE EXCEPTION
            'Dataset is incomplete: expected %, found %.',
            v_dimension, v_feature_count;
    END IF;

    IF v_method = 'BASIS' AND EXISTS (
        SELECT 1
        FROM dataset_features
        WHERE dataset_id = p_dataset_id
          AND feature_value NOT IN (0, 1)
    ) THEN
        RAISE EXCEPTION
            'Basis encoding requires binary feature values.';
    END IF;

    IF v_method = 'ANGLE' AND EXISTS (
        SELECT 1
        FROM dataset_features
        WHERE dataset_id = p_dataset_id
          AND (
              feature_value < (
                  SELECT minimum_value
                  FROM encoding_configurations
                  WHERE configuration_id = p_configuration_id
              )
              OR feature_value > (
                  SELECT maximum_value
                  FROM encoding_configurations
                  WHERE configuration_id = p_configuration_id
              )
          )
    ) THEN
        RAISE EXCEPTION
            'Angle encoding feature falls outside configured range.';
    END IF;

    SELECT *
    INTO v_estimate
    FROM estimate_encoding_resources(v_method, v_dimension);

    IF v_estimate.required_qubits > v_max_qubits THEN
        RAISE EXCEPTION 'Configured qubit limit exceeded.';
    END IF;

    IF v_estimate.estimated_memory_bytes > v_max_memory THEN
        RAISE EXCEPTION 'Configured memory limit exceeded.';
    END IF;

    INSERT INTO encoding_jobs (
        dataset_id,
        configuration_id,
        status,
        requested_by,
        input_dimension,
        qubit_count,
        state_dimension,
        estimated_memory_bytes
    )
    VALUES (
        p_dataset_id,
        p_configuration_id,
        'SUBMITTED',
        p_requested_by,
        v_dimension,
        v_estimate.required_qubits,
        v_estimate.state_dimension,
        v_estimate.estimated_memory_bytes
    )
    RETURNING job_id INTO p_job_id;
END;
$$;

-- ============================================================
-- 13. JOB PROCESSING AND STATE REGISTRATION
-- ============================================================

CREATE OR REPLACE PROCEDURE complete_encoding_job(
    p_job_id BIGINT,
    p_original_norm DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status job_status;
    v_method encoding_method;
    v_qubits INTEGER;
    v_dimension INTEGER;
    v_job_configuration BIGINT;
BEGIN
    IF p_original_norm IS NULL
       OR p_original_norm <= 0
       OR NOT isfinite(p_original_norm) THEN
        RAISE EXCEPTION 'Invalid normalization norm.';
    END IF;

    SELECT j.status, c.method, j.qubit_count,
           j.state_dimension, j.configuration_id
    INTO v_status, v_method, v_qubits,
         v_dimension, v_job_configuration
    FROM encoding_jobs j
    JOIN encoding_configurations c
      ON c.configuration_id = j.configuration_id
    WHERE j.job_id = p_job_id
    FOR UPDATE OF j;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Encoding job does not exist.';
    END IF;

    IF v_status NOT IN ('SUBMITTED', 'PROCESSING') THEN
        RAISE EXCEPTION 'Job cannot transition from status %.', v_status;
    END IF;

    IF v_status = 'SUBMITTED' THEN
        UPDATE encoding_jobs
        SET status = 'PROCESSING',
            started_at = CURRENT_TIMESTAMP
        WHERE job_id = p_job_id;
    END IF;

    INSERT INTO quantum_states (
        job_id,
        state_dimension,
        normalization_norm,
        normalization_error
    )
    VALUES (
        p_job_id,
        v_dimension,
        1.0,
        0.0
    );

    UPDATE encoding_jobs
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE job_id = p_job_id;
END;
$$;

CREATE OR REPLACE FUNCTION mark_encoding_failure(
    p_job_id BIGINT,
    p_error_message TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_error_message IS NULL OR LENGTH(TRIM(p_error_message)) = 0 THEN
        RAISE EXCEPTION 'Failure reason is required.';
    END IF;

    UPDATE encoding_jobs
    SET status = 'FAILED',
        error_message = p_error_message,
        completed_at = CURRENT_TIMESTAMP
    WHERE job_id = p_job_id
      AND status IN ('SUBMITTED', 'PROCESSING');

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job cannot be marked as failed.';
    END IF;
END;
$$;

-- ============================================================
-- 14. REPORTING VIEWS
-- ============================================================

CREATE OR REPLACE VIEW encoding_job_report AS
SELECT
    j.job_id,
    j.job_reference,
    d.dataset_name,
    c.configuration_name,
    c.method,
    j.status,
    j.input_dimension,
    j.qubit_count,
    j.state_dimension,
    j.estimated_memory_bytes,
    j.requested_by,
    j.submitted_at,
    j.completed_at,
    j.error_message
FROM encoding_jobs j
JOIN datasets d
    ON d.dataset_id = j.dataset_id
JOIN encoding_configurations c
    ON c.configuration_id = j.configuration_id;


CREATE OR REPLACE VIEW encoding_method_statistics AS
SELECT
    c.method,
    COUNT(*) AS total_jobs,
    COUNT(*) FILTER (
        WHERE j.status = 'COMPLETED'
    ) AS completed_jobs,
    COUNT(*) FILTER (
        WHERE j.status = 'FAILED'
    ) AS failed_jobs,
    ROUND(
        AVG(j.qubit_count)::NUMERIC,
        2
    ) AS average_qubits,
    ROUND(
        AVG(j.estimated_memory_bytes)::NUMERIC,
        2
    ) AS average_memory_bytes
FROM encoding_jobs j
JOIN encoding_configurations c
    ON c.configuration_id = j.configuration_id
GROUP BY c.method;

-- ============================================================
-- 15. SAMPLE ORGANIZATIONAL RECORDS
-- ============================================================

INSERT INTO organizations (organization_name)
VALUES
    ('Quantum Research Laboratory'),
    ('Computational Intelligence Division');

INSERT INTO datasets (
    organization_id,
    dataset_name,
    description,
    feature_count,
    source_format
)
VALUES
    (
        1,
        'Binary Classification Features',
        'Binary input for computational basis encoding.',
        4,
        'NUMERIC_ARRAY'
    ),
    (
        1,
        'Normalized Sensor Features',
        'Continuous features for angle encoding.',
        3,
        'NUMERIC_ARRAY'
    ),
    (
        2,
        'Amplitude Research Vector',
        'Numerical vector for amplitude encoding.',
        3,
        'NUMERIC_ARRAY'
    ),
    (
        2,
        'Invalid Binary Dataset',
        'Intentionally invalid data for validation testing.',
        2,
        'NUMERIC_ARRAY'
    );

INSERT INTO dataset_features (
    dataset_id,
    feature_position,
    feature_name,
    feature_value,
    is_binary
)
VALUES
    (1, 0, 'feature_1', 1, TRUE),
    (1, 1, 'feature_2', 0, TRUE),
    (1, 2, 'feature_3', 1, TRUE),
    (1, 3, 'feature_4', 1, TRUE),

    (2, 0, 'temperature', 0.2, FALSE),
    (2, 1, 'pressure', 0.5, FALSE),
    (2, 2, 'humidity', 0.8, FALSE),

    (3, 0, 'vector_x', 3.0, FALSE),
    (3, 1, 'vector_y', 4.0, FALSE),
    (3, 2, 'vector_z', 0.0, FALSE),

    (4, 0, 'invalid_feature_1', 0.5, FALSE),
    (4, 1, 'invalid_feature_2', 1.0, FALSE);

INSERT INTO encoding_configurations (
    configuration_name,
    method,
    minimum_value,
    maximum_value,
    maximum_qubits,
    maximum_memory_bytes,
    allow_zero_padding
)
VALUES
    (
        'Binary Basis Configuration',
        'BASIS',
        0,
        1,
        12,
        67108864,
        TRUE
    ),
    (
        'Sensor Angle Configuration',
        'ANGLE',
        0,
        1,
        12,
        67108864,
        TRUE
    ),
    (
        'Amplitude Vector Configuration',
        'AMPLITUDE',
        0,
        1,
        12,
        67108864,
        TRUE
    );

INSERT INTO resource_policies (
    policy_name,
    maximum_qubits,
    maximum_memory_bytes,
    amplitude_encoding_allowed,
    angle_encoding_allowed,
    basis_encoding_allowed
)
VALUES
    (
        'Research Standard Policy',
        12,
        67108864,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'Restricted Angle Policy',
        8,
        1048576,
        FALSE,
        TRUE,
        FALSE
    );

-- ============================================================
-- 16. SAMPLE JOB SUBMISSION
-- ============================================================

DO $$
DECLARE
    v_job_id BIGINT;
BEGIN
    CALL submit_encoding_job(
        1,
        1,
        'researcher_001',
        v_job_id
    );

    RAISE NOTICE 'Basis encoding job created: %', v_job_id;

    CALL complete_encoding_job(v_job_id, 1.0);

    INSERT INTO basis_encodings (
        job_id,
        bitstring,
        basis_index
    )
    VALUES (
        v_job_id,
        '1011',
        11
    );

    INSERT INTO job_resource_evaluations (
        job_id,
        policy_id,
        eligible,
        estimated_memory_bytes,
        evaluation_details
    )
    VALUES (
        v_job_id,
        1,
        TRUE,
        256,
        '{"method":"BASIS","qubits":4}'::jsonb
    );

END;
$$;

DO $$
DECLARE
    v_job_id BIGINT;
BEGIN
    CALL submit_encoding_job(
        2,
        2,
        'researcher_002',
        v_job_id
    );

    CALL complete_encoding_job(v_job_id, 1.0);

    INSERT INTO angle_rotations (
        job_id,
        qubit_index,
        feature_id,
        angle_radians
    )
    SELECT
        v_job_id,
        feature_position,
        feature_id,
        pi() * feature_value
    FROM dataset_features
    WHERE dataset_id = 2
    ORDER BY feature_position;

    INSERT INTO job_resource_evaluations (
        job_id,
        policy_id,
        eligible,
        estimated_memory_bytes,
        evaluation_details
    )
    VALUES (
        v_job_id,
        1,
        TRUE,
        128,
        '{"method":"ANGLE","qubits":3}'::jsonb
    );
END;
$$;

DO $$
DECLARE
    v_job_id BIGINT;
BEGIN
    CALL submit_encoding_job(
        3,
        3,
        'researcher_003',
        v_job_id
    );

    CALL complete_encoding_job(
        v_job_id,
        5.0
    );

    INSERT INTO state_amplitudes (
        state_id,
        basis_index,
        real_part,
        imaginary_part
    )
    SELECT
        s.state_id,
        x.basis_index,
        x.amplitude,
        0.0
    FROM quantum_states s
    CROSS JOIN (
        VALUES
            (0, 0.6),
            (1, 0.8),
            (2, 0.0),
            (3, 0.0)
    ) AS x(basis_index, amplitude)
    WHERE s.job_id = v_job_id;

    INSERT INTO job_resource_evaluations (
        job_id,
        policy_id,
        eligible,
        estimated_memory_bytes,
        evaluation_details
    )
    VALUES (
        v_job_id,
        1,
        TRUE,
        64,
        '{"method":"AMPLITUDE","qubits":2}'::jsonb
    );
END;
$$;

-- ============================================================
-- 17. SAMPLE MEASUREMENT RUN
-- ============================================================

DO $$
DECLARE
    v_job_id BIGINT;
    v_measurement_id BIGINT;
BEGIN
    SELECT job_id
    INTO v_job_id
    FROM encoding_jobs
    WHERE status = 'COMPLETED'
    ORDER BY job_id
    LIMIT 1;

    INSERT INTO measurement_runs (
        job_id,
        shots,
        random_seed
    )
    VALUES (
        v_job_id,
        1000,
        42
    )
    RETURNING measurement_id INTO v_measurement_id;

    INSERT INTO measurement_outcomes (
        measurement_id,
        bitstring,
        occurrence_count
    )
    VALUES
        (v_measurement_id, '1011', 1000);
END;
$$;

-- ============================================================
-- 18. VALIDATION AND EVALUATION QUERIES
-- ============================================================

-- Q1: Retrieve encoding jobs and their execution states.
SELECT *
FROM encoding_job_report
ORDER BY submitted_at DESC;

-- Q2: Compare resource requirements.
SELECT
    method,
    required_qubits,
    state_dimension,
    estimated_memory_bytes
FROM estimate_encoding_resources('AMPLITUDE', 5);

-- Q3: Evaluate method-level execution statistics.
SELECT *
FROM encoding_method_statistics
ORDER BY method;

-- Q4: Check amplitude normalization.
SELECT
    s.state_id,
    SUM(a.probability) AS total_probability,
    ABS(SUM(a.probability) - 1.0) AS normalization_error,
    CASE
        WHEN ABS(SUM(a.probability) - 1.0) < 0.000000001
        THEN 'VALID'
        ELSE 'INVALID'
    END AS validation_status
FROM quantum_states s
JOIN state_amplitudes a
    ON a.state_id = s.state_id
GROUP BY s.state_id;

-- Q5: Retrieve amplitude probabilities.
SELECT
    s.job_id,
    a.basis_index,
    a.real_part,
    a.imaginary_part,
    a.probability
FROM state_amplitudes a
JOIN quantum_states s
    ON s.state_id = a.state_id
ORDER BY s.job_id, a.basis_index;

-- Q6: Inspect angle rotations.
SELECT
    j.job_id,
    r.qubit_index,
    f.feature_name,
    f.feature_value,
    r.rotation_gate,
    r.angle_radians
FROM angle_rotations r
JOIN encoding_jobs j
    ON j.job_id = r.job_id
JOIN dataset_features f
    ON f.feature_id = r.feature_id
ORDER BY j.job_id, r.qubit_index;

-- Q7: Evaluate resource-policy compliance.
SELECT
    e.job_id,
    p.policy_name,
    e.eligible,
    e.estimated_memory_bytes,
    e.evaluation_details
FROM job_resource_evaluations e
JOIN resource_policies p
    ON p.policy_id = e.policy_id;

-- Q8: Aggregate measurement outcomes.
SELECT
    m.measurement_id,
    m.shots,
    SUM(o.occurrence_count) AS recorded_shots,
    ROUND(
        SUM(o.occurrence_count)::NUMERIC / m.shots,
        4
    ) AS recorded_fraction
FROM measurement_runs m
JOIN measurement_outcomes o
    ON o.measurement_id = m.measurement_id
GROUP BY m.measurement_id, m.shots;

-- Q9: Identify incomplete datasets.
SELECT
    d.dataset_id,
    d.dataset_name,
    d.feature_count,
    COUNT(f.feature_id) AS available_features,
    d.feature_count - COUNT(f.feature_id) AS missing_features
FROM datasets d
LEFT JOIN dataset_features f
    ON f.dataset_id = d.dataset_id
GROUP BY d.dataset_id, d.dataset_name, d.feature_count
HAVING COUNT(f.feature_id) <> d.feature_count;

-- Q10: Calculate feature-level dataset statistics.
SELECT
    dataset_id,
    COUNT(*) AS feature_count,
    MIN(feature_value) AS minimum_feature,
    MAX(feature_value) AS maximum_feature,
    AVG(feature_value) AS average_feature,
    SQRT(SUM(feature_value * feature_value)) AS vector_norm
FROM dataset_features
GROUP BY dataset_id;

-- Q11: Validate binary datasets.
SELECT
    d.dataset_id,
    d.dataset_name,
    BOOL_AND(f.feature_value IN (0.0, 1.0)) AS binary_compatible
FROM datasets d
JOIN dataset_features f
    ON f.dataset_id = d.dataset_id
GROUP BY d.dataset_id, d.dataset_name;

-- ============================================================
-- 19. CTE-BASED RESOURCE ANALYSIS
-- ============================================================

WITH feature_statistics AS (
    SELECT
        dataset_id,
        COUNT(*) AS feature_count,
        SUM(feature_value * feature_value) AS squared_norm,
        BOOL_AND(feature_value IN (0, 1)) AS binary_compatible
    FROM dataset_features
    GROUP BY dataset_id
),
encoding_candidates AS (
    SELECT
        d.dataset_id,
        d.dataset_name,
        s.feature_count,
        s.squared_norm,
        s.binary_compatible,
        CASE
            WHEN s.binary_compatible THEN 'BASIS'
            ELSE 'ANGLE_OR_AMPLITUDE'
        END AS recommended_input_compatibility
    FROM datasets d
    JOIN feature_statistics s
        ON s.dataset_id = d.dataset_id
)
SELECT *
FROM encoding_candidates
ORDER BY dataset_id;

-- ============================================================
-- 20. TRANSACTIONAL FAILURE HANDLING EXAMPLE
-- ============================================================

-- The following block demonstrates a rejected request.
-- The exception is caught, so the transaction remains usable.

DO $$
DECLARE
    v_job_id BIGINT;
BEGIN
    BEGIN
        CALL submit_encoding_job(
            4,
            1,
            'researcher_validation',
            v_job_id
        );

        RAISE EXCEPTION
            'Invalid binary dataset was unexpectedly accepted.';

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE
            'Expected validation rejection: %',
            SQLERRM;
    END;
END;
$$;

-- ============================================================
-- 21. DATABASE GOVERNANCE NOTES
-- ============================================================

-- Production deployment considerations:
--
-- 1. Restrict direct writes to state_amplitudes.
-- 2. Grant job submission through controlled procedures.
-- 3. Separate application roles from database administrators.
-- 4. Encrypt sensitive datasets at rest and in transit.
-- 5. Retain job and audit records according to organizational policy.
-- 6. Enforce maximum state dimensions before allocation.
-- 7. Validate complete measurement distributions before publication.
-- 8. Use partitioning for large measurement and amplitude tables.
-- 9. Do not assume stored amplitudes represent hardware execution.
-- 10. Use application-side transaction management for actual
--     quantum execution and database registration.

COMMIT;
