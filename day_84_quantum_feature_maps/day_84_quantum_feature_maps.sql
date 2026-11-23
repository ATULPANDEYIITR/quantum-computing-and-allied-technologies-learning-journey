-- ============================================================
-- QUANTUM FEATURE MAPS
-- Classical Data Encoding into Quantum States
--
-- PostgreSQL 15+
--
-- Relational workflow:
-- Dataset -> Features -> Feature-map configuration
-- -> Encoding runs -> Quantum states -> Kernel evaluations
-- -> Experiment reports
--
-- Complex amplitudes are stored as separate real and
-- imaginary arrays. This schema stores experimental results;
-- it does not execute quantum circuits inside PostgreSQL.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum;

SET search_path TO quantum, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE encoding_type AS ENUM (
    'ANGLE',
    'ZZ',
    'IQP'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE state_status AS ENUM (
    'ENCODED',
    'VALIDATED',
    'REJECTED'
);

-- ------------------------------------------------------------
-- 2. DATASET MANAGEMENT
-- ------------------------------------------------------------

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    feature_count INTEGER NOT NULL CHECK (feature_count > 0),
    sample_count INTEGER NOT NULL DEFAULT 0 CHECK (sample_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dataset_samples (
    sample_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    sample_label VARCHAR(100) NOT NULL,
    features DOUBLE PRECISION[] NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dataset_id, sample_label),

    CHECK (cardinality(features) > 0)
);

CREATE INDEX idx_dataset_samples_dataset
    ON dataset_samples(dataset_id, sample_id);

-- ------------------------------------------------------------
-- 3. FEATURE-MAP CONFIGURATION
-- ------------------------------------------------------------

CREATE TABLE feature_maps (
    feature_map_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    map_name VARCHAR(150) NOT NULL UNIQUE,
    encoding encoding_type NOT NULL,
    repetitions INTEGER NOT NULL DEFAULT 1
        CHECK (repetitions > 0),
    entanglement_strength DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        entanglement_strength BETWEEN -1000 AND 1000
    )
);

-- ------------------------------------------------------------
-- 4. EXPERIMENT EXECUTION
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    feature_map_id BIGINT NOT NULL REFERENCES feature_maps(feature_map_id),

    experiment_name VARCHAR(150) NOT NULL UNIQUE,
    status experiment_status NOT NULL DEFAULT 'CREATED',

    normalization_lower DOUBLE PRECISION NOT NULL DEFAULT -3.141592653589793,
    normalization_upper DOUBLE PRECISION NOT NULL DEFAULT 3.141592653589793,

    requested_shots INTEGER NOT NULL DEFAULT 1000
        CHECK (requested_shots > 0),

    maximum_qubits INTEGER NOT NULL DEFAULT 20
        CHECK (maximum_qubits BETWEEN 1 AND 30),

    execution_started_at TIMESTAMPTZ,
    execution_completed_at TIMESTAMPTZ,

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (normalization_lower < normalization_upper),

    CHECK (
        execution_completed_at IS NULL
        OR execution_started_at IS NULL
        OR execution_completed_at >= execution_started_at
    )
);

CREATE INDEX idx_experiments_status
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_dataset
    ON experiments(dataset_id, feature_map_id);

-- ------------------------------------------------------------
-- 5. ENCODED QUANTUM STATES
-- ------------------------------------------------------------

CREATE TABLE quantum_states (
    state_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    sample_id BIGINT NOT NULL
        REFERENCES dataset_samples(sample_id),

    qubit_count INTEGER NOT NULL CHECK (qubit_count > 0),

    state_dimension INTEGER NOT NULL
        CHECK (state_dimension > 0),

    amplitude_real DOUBLE PRECISION[] NOT NULL,
    amplitude_imaginary DOUBLE PRECISION[] NOT NULL,

    norm_squared DOUBLE PRECISION NOT NULL
        CHECK (norm_squared >= 0),

    status state_status NOT NULL DEFAULT 'ENCODED',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(experiment_id, sample_id),

    CHECK (
        state_dimension::BIGINT = power(2::NUMERIC, qubit_count)
    ),

    CHECK (
        cardinality(amplitude_real) = state_dimension
    ),

    CHECK (
        cardinality(amplitude_imaginary) = state_dimension
    ),

    CHECK (
        norm_squared BETWEEN 0.999999 AND 1.000001
    )
);

CREATE INDEX idx_quantum_states_experiment
    ON quantum_states(experiment_id, state_id);

-- ------------------------------------------------------------
-- 6. KERNEL EVALUATIONS
-- ------------------------------------------------------------

CREATE TABLE kernel_evaluations (
    kernel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    first_state_id BIGINT NOT NULL
        REFERENCES quantum_states(state_id),

    second_state_id BIGINT NOT NULL
        REFERENCES quantum_states(state_id),

    fidelity DOUBLE PRECISION NOT NULL
        CHECK (fidelity BETWEEN 0 AND 1),

    evaluation_method VARCHAR(60) NOT NULL DEFAULT 'STATEVECTOR',

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (first_state_id <= second_state_id),

    UNIQUE(experiment_id, first_state_id, second_state_id)
);

CREATE INDEX idx_kernel_evaluations_experiment
    ON kernel_evaluations(experiment_id);

CREATE INDEX idx_kernel_evaluations_fidelity
    ON kernel_evaluations(fidelity);

-- ------------------------------------------------------------
-- 7. EXPERIMENT AUDIT LOG
-- ------------------------------------------------------------

CREATE TABLE experiment_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    event_type VARCHAR(80) NOT NULL,
    event_description TEXT NOT NULL,

    event_data JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_experiment_events
    ON experiment_events(experiment_id, created_at DESC);

-- ------------------------------------------------------------
-- 8. FEATURE VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_sample_features()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_dimensions INTEGER;
    actual_dimensions INTEGER;
    feature_value DOUBLE PRECISION;
BEGIN
    SELECT feature_count
    INTO expected_dimensions
    FROM datasets
    WHERE dataset_id = NEW.dataset_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dataset does not exist.';
    END IF;

    actual_dimensions := cardinality(NEW.features);

    IF actual_dimensions <> expected_dimensions THEN
        RAISE EXCEPTION
            'Feature dimension mismatch: expected %, received %.',
            expected_dimensions,
            actual_dimensions;
    END IF;

    FOREACH feature_value IN ARRAY NEW.features
    LOOP
        IF feature_value IS NULL
           OR feature_value = 'NaN'::DOUBLE PRECISION
           OR feature_value = 'Infinity'::DOUBLE PRECISION
           OR feature_value = '-Infinity'::DOUBLE PRECISION THEN

            RAISE EXCEPTION
                'Features must contain only finite values.';
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_sample_features
BEFORE INSERT OR UPDATE ON dataset_samples
FOR EACH ROW
EXECUTE FUNCTION validate_sample_features();

-- ------------------------------------------------------------
-- 9. SAMPLE COUNT MAINTENANCE
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_dataset_sample_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE datasets
        SET sample_count = sample_count + 1
        WHERE dataset_id = NEW.dataset_id;

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE datasets
        SET sample_count = sample_count - 1
        WHERE dataset_id = OLD.dataset_id;

        RETURN OLD;

    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.dataset_id <> OLD.dataset_id THEN
            UPDATE datasets
            SET sample_count = sample_count - 1
            WHERE dataset_id = OLD.dataset_id;

            UPDATE datasets
            SET sample_count = sample_count + 1
            WHERE dataset_id = NEW.dataset_id;
        END IF;

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_dataset_sample_count
AFTER INSERT OR UPDATE OR DELETE ON dataset_samples
FOR EACH ROW
EXECUTE FUNCTION update_dataset_sample_count();

-- ------------------------------------------------------------
-- 10. EXPERIMENT STATE TRANSITIONS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'CREATED'
            AND NEW.status IN ('VALIDATED', 'FAILED', 'CANCELLED'))
        OR
        (OLD.status = 'VALIDATED'
            AND NEW.status IN ('RUNNING', 'FAILED', 'CANCELLED'))
        OR
        (OLD.status = 'RUNNING'
            AND NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED'))
    ) THEN
        RAISE EXCEPTION
            'Invalid experiment transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    IF NEW.status = 'RUNNING'
       AND NEW.execution_started_at IS NULL THEN
        NEW.execution_started_at := CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED')
       AND NEW.execution_completed_at IS NULL THEN
        NEW.execution_completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- ------------------------------------------------------------
-- 11. QUANTUM STATE VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_quantum_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    actual_norm DOUBLE PRECISION;
    index_value INTEGER;
    experiment_dimensions INTEGER;
    sample_dimensions INTEGER;
    sample_dataset BIGINT;
    expected_dimension BIGINT;
BEGIN
    SELECT d.feature_count, s.dataset_id,
           cardinality(s.features)
    INTO experiment_dimensions, sample_dataset, sample_dimensions
    FROM experiments e
    JOIN datasets d ON d.dataset_id = e.dataset_id
    JOIN dataset_samples s ON s.sample_id = NEW.sample_id
    WHERE e.experiment_id = NEW.experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment or dataset sample does not exist.';
    END IF;

    IF sample_dataset <> (
        SELECT dataset_id
        FROM experiments
        WHERE experiment_id = NEW.experiment_id
    ) THEN
        RAISE EXCEPTION
            'Sample does not belong to experiment dataset.';
    END IF;

    IF NEW.qubit_count <> experiment_dimensions
       OR NEW.qubit_count <> sample_dimensions THEN
        RAISE EXCEPTION
            'Qubit count does not match feature dimension.';
    END IF;

    expected_dimension := power(2::NUMERIC, NEW.qubit_count);

    IF expected_dimension > 2147483647
       OR NEW.state_dimension <> expected_dimension THEN
        RAISE EXCEPTION
            'Invalid statevector dimension.';
    END IF;

    actual_norm := 0;

    FOR index_value IN 1..NEW.state_dimension
    LOOP
        IF NOT (
            isfinite(NEW.amplitude_real[index_value])
            AND isfinite(NEW.amplitude_imaginary[index_value])
        ) THEN
            RAISE EXCEPTION
                'Statevector contains non-finite amplitudes.';
        END IF;

        actual_norm :=
            actual_norm
            + NEW.amplitude_real[index_value] ^ 2
            + NEW.amplitude_imaginary[index_value] ^ 2;
    END LOOP;

    IF abs(actual_norm - 1.0) > 0.000001 THEN
        RAISE EXCEPTION
            'State normalization failed: %',
            actual_norm;
    END IF;

    NEW.norm_squared := actual_norm;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_quantum_state
BEFORE INSERT OR UPDATE ON quantum_states
FOR EACH ROW
EXECUTE FUNCTION validate_quantum_state();

-- ------------------------------------------------------------
-- 12. KERNEL OWNERSHIP AND SYMMETRY VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_kernel_ownership()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    first_experiment BIGINT;
    second_experiment BIGINT;
    first_qubits INTEGER;
    second_qubits INTEGER;
BEGIN
    SELECT experiment_id, qubit_count
    INTO first_experiment, first_qubits
    FROM quantum_states
    WHERE state_id = NEW.first_state_id;

    SELECT experiment_id, qubit_count
    INTO second_experiment, second_qubits
    FROM quantum_states
    WHERE state_id = NEW.second_state_id;

    IF first_experiment IS NULL OR second_experiment IS NULL THEN
        RAISE EXCEPTION 'Quantum state does not exist.';
    END IF;

    IF first_experiment <> NEW.experiment_id
       OR second_experiment <> NEW.experiment_id THEN
        RAISE EXCEPTION
            'Kernel states must belong to the same experiment.';
    END IF;

    IF first_qubits <> second_qubits THEN
        RAISE EXCEPTION
            'Kernel states must have equal qubit counts.';
    END IF;

    IF first_experiment <> second_experiment THEN
        RAISE EXCEPTION
            'Cross-experiment kernel evaluation is not permitted.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_kernel_ownership
BEFORE INSERT OR UPDATE ON kernel_evaluations
FOR EACH ROW
EXECUTE FUNCTION validate_kernel_ownership();

-- ------------------------------------------------------------
-- 13. EXPERIMENT ELIGIBILITY FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_experiment_eligibility(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT,
    dataset_samples BIGINT,
    encoded_samples BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_record RECORD;
    sample_total BIGINT;
    encoded_total BIGINT;
BEGIN
    SELECT e.status, e.maximum_qubits,
           d.feature_count, d.sample_count,
           fm.encoding
    INTO experiment_record
    FROM experiments e
    JOIN datasets d ON d.dataset_id = e.dataset_id
    JOIN feature_maps fm
        ON fm.feature_map_id = e.feature_map_id
    WHERE e.experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT false, 'Experiment not found'::TEXT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    SELECT count(*)
    INTO sample_total
    FROM dataset_samples s
    JOIN experiments e ON e.dataset_id = s.dataset_id
    WHERE e.experiment_id = p_experiment_id;

    SELECT count(*)
    INTO encoded_total
    FROM quantum_states
    WHERE experiment_id = p_experiment_id
      AND status IN ('ENCODED', 'VALIDATED');

    IF experiment_record.feature_count >
       experiment_record.maximum_qubits THEN

        RETURN QUERY
        SELECT false,
            'Feature dimension exceeds qubit policy'::TEXT,
            sample_total,
            encoded_total;

        RETURN;
    END IF;

    IF sample_total = 0 THEN
        RETURN QUERY
        SELECT false,
            'Dataset contains no samples'::TEXT,
            sample_total,
            encoded_total;

        RETURN;
    END IF;

    IF experiment_record.status NOT IN ('VALIDATED', 'RUNNING') THEN
        RETURN QUERY
        SELECT false,
            'Experiment is not in an executable state'::TEXT,
            sample_total,
            encoded_total;

        RETURN;
    END IF;

    RETURN QUERY
    SELECT true,
        'Experiment satisfies execution requirements'::TEXT,
        sample_total,
        encoded_total;
END;
$$;

-- ------------------------------------------------------------
-- 14. KERNEL REPORTING VIEW
-- ------------------------------------------------------------

CREATE VIEW experiment_kernel_report AS
SELECT
    e.experiment_id,
    e.experiment_name,
    fm.map_name,
    fm.encoding,
    e.status,
    count(k.kernel_id) AS evaluation_count,
    round(avg(k.fidelity)::NUMERIC, 6) AS mean_fidelity,
    round(min(k.fidelity)::NUMERIC, 6) AS minimum_fidelity,
    round(max(k.fidelity)::NUMERIC, 6) AS maximum_fidelity,
    round(
        avg(
            CASE
                WHEN k.first_state_id = k.second_state_id
                THEN k.fidelity
            END
        )::NUMERIC,
        6
    ) AS mean_self_fidelity
FROM experiments e
JOIN feature_maps fm
    ON fm.feature_map_id = e.feature_map_id
LEFT JOIN kernel_evaluations k
    ON k.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_name,
    fm.map_name,
    fm.encoding,
    e.status;

-- ------------------------------------------------------------
-- 15. DATASET AGGREGATION VIEW
-- ------------------------------------------------------------

CREATE VIEW dataset_quality_report AS
SELECT
    d.dataset_id,
    d.dataset_name,
    d.feature_count,
    count(s.sample_id) AS actual_samples,
    d.sample_count AS maintained_samples,
    CASE
        WHEN count(s.sample_id) = d.sample_count
        THEN 'CONSISTENT'
        ELSE 'INCONSISTENT'
    END AS integrity_status
FROM datasets d
LEFT JOIN dataset_samples s
    ON s.dataset_id = d.dataset_id
GROUP BY
    d.dataset_id,
    d.dataset_name,
    d.feature_count,
    d.sample_count;

-- ------------------------------------------------------------
-- 16. SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO datasets (
    dataset_name,
    description,
    feature_count
)
VALUES (
    'classification_dataset',
    'Four three-dimensional classical observations.',
    3
);

INSERT INTO dataset_samples (
    dataset_id,
    sample_label,
    features
)
SELECT
    d.dataset_id,
    sample.sample_label,
    sample.features
FROM datasets d
CROSS JOIN (
    VALUES
        ('sample_001', ARRAY[0.2, 0.4, 0.6]::DOUBLE PRECISION[]),
        ('sample_002', ARRAY[0.3, 0.7, 0.5]::DOUBLE PRECISION[]),
        ('sample_003', ARRAY[0.8, 0.2, 0.9]::DOUBLE PRECISION[]),
        ('sample_004', ARRAY[0.9, 0.6, 0.1]::DOUBLE PRECISION[])
) AS sample(sample_label, features)
WHERE d.dataset_name = 'classification_dataset';

INSERT INTO feature_maps (
    map_name,
    encoding,
    repetitions,
    entanglement_strength,
    description
)
VALUES
(
    'basic_angle_map',
    'ANGLE',
    2,
    1.0,
    'Independent single-qubit rotational encoding.'
),
(
    'zz_entangled_map',
    'ZZ',
    2,
    0.75,
    'Rotational encoding with pairwise ZZ interactions.'
),
(
    'iqp_feature_map',
    'IQP',
    2,
    1.0,
    'IQP-inspired diagonal interaction encoding.'
);

INSERT INTO experiments (
    dataset_id,
    feature_map_id,
    experiment_name,
    maximum_qubits,
    requested_shots
)
SELECT
    d.dataset_id,
    fm.feature_map_id,
    'experiment_' || lower(fm.encoding::TEXT),
    20,
    1000
FROM datasets d
CROSS JOIN feature_maps fm
WHERE d.dataset_name = 'classification_dataset';

-- ------------------------------------------------------------
-- 17. EXECUTION WORKFLOW
-- ------------------------------------------------------------

-- Validate all created experiments.
UPDATE experiments
SET status = 'VALIDATED'
WHERE status = 'CREATED';

-- Check execution eligibility before starting.
SELECT
    e.experiment_name,
    eligibility.*
FROM experiments e
CROSS JOIN LATERAL
    evaluate_experiment_eligibility(e.experiment_id) eligibility;

-- Start eligible experiments.
UPDATE experiments
SET status = 'RUNNING'
WHERE status = 'VALIDATED';

INSERT INTO experiment_events (
    experiment_id,
    event_type,
    event_description,
    event_data
)
SELECT
    experiment_id,
    'EXECUTION_STARTED',
    'Experiment passed validation and entered execution.',
    jsonb_build_object(
        'status', status,
        'started_at', execution_started_at
    )
FROM experiments
WHERE status = 'RUNNING';

-- ------------------------------------------------------------
-- 18. EXAMPLE QUANTUM STATE RECORDS
-- ------------------------------------------------------------
-- Three-qubit angle-encoded state for x = [0, 0, 0].
-- Each RY(0) gate preserves |000>.
--
-- Therefore:
-- amplitude_real      = [1,0,0,0,0,0,0,0]
-- amplitude_imaginary = [0,0,0,0,0,0,0,0]
-- norm squared        = 1.

WITH eligible_samples AS (
    SELECT
        e.experiment_id,
        s.sample_id
    FROM experiments e
    JOIN feature_maps fm
        ON fm.feature_map_id = e.feature_map_id
    JOIN dataset_samples s
        ON s.dataset_id = e.dataset_id
    WHERE e.experiment_name = 'experiment_angle'
      AND s.sample_label = 'sample_001'
)
INSERT INTO quantum_states (
    experiment_id,
    sample_id,
    qubit_count,
    state_dimension,
    amplitude_real,
    amplitude_imaginary,
    norm_squared,
    status
)
SELECT
    experiment_id,
    sample_id,
    3,
    8,
    ARRAY[
        1.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ]::DOUBLE PRECISION[],
    ARRAY[
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ]::DOUBLE PRECISION[],
    1.0,
    'VALIDATED'
FROM eligible_samples;

-- ------------------------------------------------------------
-- 19. SELF-KERNEL EVALUATION
-- ------------------------------------------------------------
-- The fidelity of a normalized quantum state with itself is 1.
-- This example is a valid identity evaluation.

INSERT INTO kernel_evaluations (
    experiment_id,
    first_state_id,
    second_state_id,
    fidelity
)
SELECT
    experiment_id,
    state_id,
    state_id,
    1.0
FROM quantum_states
WHERE status = 'VALIDATED';

-- ------------------------------------------------------------
-- 20. COMPLETION AND AUDIT
-- ------------------------------------------------------------

UPDATE experiments e
SET status = 'COMPLETED'
WHERE e.status = 'RUNNING'
  AND EXISTS (
      SELECT 1
      FROM quantum_states qs
      WHERE qs.experiment_id = e.experiment_id
  );

INSERT INTO experiment_events (
    experiment_id,
    event_type,
    event_description,
    event_data
)
SELECT
    experiment_id,
    'EXECUTION_COMPLETED',
    'Experiment completed with validated state records.',
    jsonb_build_object(
        'completed_at', execution_completed_at
    )
FROM experiments
WHERE status = 'COMPLETED';

COMMIT;

-- ============================================================
-- 21. RETRIEVAL QUERIES
-- ============================================================

-- Dataset metadata.
SELECT *
FROM datasets
ORDER BY dataset_id;

-- Original classical features.
SELECT
    d.dataset_name,
    s.sample_label,
    s.features
FROM dataset_samples s
JOIN datasets d ON d.dataset_id = s.dataset_id
ORDER BY s.sample_id;

-- Feature-map configurations.
SELECT *
FROM feature_maps
ORDER BY feature_map_id;

-- Experiment lifecycle.
SELECT
    experiment_name,
    status,
    execution_started_at,
    execution_completed_at
FROM experiments
ORDER BY experiment_id;

-- Encoded state metadata.
SELECT
    e.experiment_name,
    qs.state_id,
    qs.qubit_count,
    qs.state_dimension,
    qs.norm_squared,
    qs.status
FROM quantum_states qs
JOIN experiments e
    ON e.experiment_id = qs.experiment_id;

-- ============================================================
-- 22. VALIDATION QUERIES
-- ============================================================

-- Check state normalization.
SELECT
    state_id,
    norm_squared,
    abs(norm_squared - 1.0) <= 0.000001 AS normalized
FROM quantum_states;

-- Check dataset sample counts.
SELECT *
FROM dataset_quality_report;

-- Detect incomplete state encoding.
SELECT
    e.experiment_name,
    count(s.sample_id) AS expected_samples,
    count(qs.state_id) AS encoded_samples,
    count(s.sample_id) - count(qs.state_id) AS missing_states
FROM experiments e
JOIN dataset_samples s
    ON s.dataset_id = e.dataset_id
LEFT JOIN quantum_states qs
    ON qs.experiment_id = e.experiment_id
   AND qs.sample_id = s.sample_id
GROUP BY e.experiment_id, e.experiment_name;

-- Detect invalid or rejected states.
SELECT *
FROM quantum_states
WHERE status = 'REJECTED'
   OR abs(norm_squared - 1.0) > 0.000001;

-- ============================================================
-- 23. AGGREGATION AND EVALUATION
-- ============================================================

SELECT *
FROM experiment_kernel_report
ORDER BY experiment_id;

-- Mean fidelity by encoding type.
SELECT
    fm.encoding,
    count(k.kernel_id) AS evaluations,
    round(avg(k.fidelity)::NUMERIC, 6) AS average_fidelity
FROM feature_maps fm
JOIN experiments e
    ON e.feature_map_id = fm.feature_map_id
LEFT JOIN kernel_evaluations k
    ON k.experiment_id = e.experiment_id
GROUP BY fm.encoding
ORDER BY fm.encoding;

-- Identity kernel validation.
SELECT
    kernel_id,
    fidelity,
    fidelity = 1.0 AS identity_valid
FROM kernel_evaluations
WHERE first_state_id = second_state_id;

-- ============================================================
-- 24. FAILURE-CASE DEMONSTRATIONS
-- ============================================================

-- This statement is intentionally commented out because
-- the trigger must reject the incorrect feature dimension.
--
-- INSERT INTO dataset_samples (
--     dataset_id, sample_label, features
-- )
-- SELECT dataset_id, 'invalid_sample', ARRAY[0.1, 0.2]
-- FROM datasets
-- WHERE dataset_name = 'classification_dataset';

-- This statement is intentionally commented out because
-- the state validation trigger rejects a non-normalized state.
--
-- INSERT INTO quantum_states (
--     experiment_id, sample_id, qubit_count, state_dimension,
--     amplitude_real, amplitude_imaginary, norm_squared
-- )
-- SELECT
--     e.experiment_id, s.sample_id, 3, 8,
--     ARRAY[2.0,0,0,0,0,0,0,0]::DOUBLE PRECISION[],
--     ARRAY[0.0,0,0,0,0,0,0,0]::DOUBLE PRECISION[],
--     4.0
-- FROM experiments e
-- JOIN datasets d ON d.dataset_id = e.dataset_id
-- JOIN dataset_samples s ON s.dataset_id = d.dataset_id
-- WHERE e.experiment_name = 'experiment_angle'
-- LIMIT 1;

-- ============================================================
-- 25. OPERATIONAL REPORT
-- ============================================================

SELECT
    d.dataset_name,
    d.sample_count,
    fm.map_name,
    fm.encoding,
    e.experiment_name,
    e.status,
    (
        SELECT count(*)
        FROM quantum_states qs
        WHERE qs.experiment_id = e.experiment_id
    ) AS encoded_states,
    (
        SELECT count(*)
        FROM kernel_evaluations ke
        WHERE ke.experiment_id = e.experiment_id
    ) AS kernel_evaluations
FROM experiments e
JOIN datasets d
    ON d.dataset_id = e.dataset_id
JOIN feature_maps fm
    ON fm.feature_map_id = e.feature_map_id
ORDER BY e.experiment_id;

-- ============================================================
-- END OF QUANTUM FEATURE MAP DATABASE WORKFLOW
-- ============================================================
