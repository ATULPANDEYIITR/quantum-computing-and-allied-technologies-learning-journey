-- ============================================================
-- ZERO-NOISE EXTRAPOLATION
-- Practical Quantum Error Mitigation
-- PostgreSQL 14+
--
-- Models:
--   Experiments
--   Quantum circuits
--   Noise-scaling configurations
--   Measurement observations
--   Extrapolation methods
--   Shot budgets
--   Results and uncertainty
--   Experiment lifecycle
--
-- The dataset is a simulated experiment, not hardware output.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_zne;

SET search_path TO quantum_zne, public;

-- ------------------------------------------------------------
-- Domain types
-- ------------------------------------------------------------

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE extrapolation_method AS ENUM (
    'LINEAR',
    'QUADRATIC',
    'RICHARDSON'
);

CREATE TYPE measurement_status AS ENUM (
    'PENDING',
    'COMPLETED',
    'FAILED'
);

-- ------------------------------------------------------------
-- Quantum circuits
-- ------------------------------------------------------------

CREATE TABLE circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    qubit_count INTEGER NOT NULL CHECK (qubit_count > 0),
    gate_count INTEGER NOT NULL CHECK (gate_count > 0),
    observable_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (circuit_name, observable_name)
);

-- ------------------------------------------------------------
-- Experiments
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES circuits(circuit_id),
    experiment_name VARCHAR(180) NOT NULL,
    method extrapolation_method NOT NULL,
    status experiment_status NOT NULL DEFAULT 'CREATED',

    ideal_reference NUMERIC(12, 9)
        CHECK (
            ideal_reference IS NULL OR
            ideal_reference BETWEEN -1 AND 1
        ),

    requested_shots BIGINT NOT NULL CHECK (requested_shots >= 2),
    maximum_shots BIGINT NOT NULL CHECK (maximum_shots >= 2),

    random_seed BIGINT NOT NULL DEFAULT 42,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (requested_shots <= maximum_shots),

    CHECK (
        completed_at IS NULL OR
        started_at IS NOT NULL
    ),

    UNIQUE (experiment_name)
);

-- ------------------------------------------------------------
-- Noise scales
--
-- A scale factor describes the intended relative noise
-- amplification. It is not necessarily a physical noise rate.
-- ------------------------------------------------------------

CREATE TABLE noise_scales (
    scale_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    scale_factor NUMERIC(10, 5) NOT NULL
        CHECK (scale_factor >= 1.0),

    scale_order INTEGER NOT NULL CHECK (scale_order > 0),

    scaling_method VARCHAR(50) NOT NULL DEFAULT 'GATE_FOLDING'
        CHECK (
            scaling_method IN (
                'GATE_FOLDING',
                'NOISE_PARAMETER_CONTROL',
                'CALIBRATION_BASED'
            )
        ),

    status measurement_status NOT NULL DEFAULT 'PENDING',

    UNIQUE (experiment_id, scale_factor),
    UNIQUE (experiment_id, scale_order),
    UNIQUE (experiment_id, scale_id)
);

-- ------------------------------------------------------------
-- Measurements
-- ------------------------------------------------------------

CREATE TABLE measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL,
    scale_id BIGINT NOT NULL,

    observed_value NUMERIC(14, 10)
        CHECK (
            observed_value IS NULL OR
            observed_value BETWEEN -1 AND 1
        ),

    positive_count BIGINT CHECK (positive_count >= 0),
    negative_count BIGINT CHECK (negative_count >= 0),

    shot_count BIGINT NOT NULL CHECK (shot_count >= 2),

    standard_error NUMERIC(14, 10)
        CHECK (
            standard_error IS NULL OR
            standard_error >= 0
        ),

    status measurement_status NOT NULL DEFAULT 'PENDING',

    measured_at TIMESTAMPTZ,

    FOREIGN KEY (experiment_id, scale_id)
        REFERENCES noise_scales(experiment_id, scale_id),

    UNIQUE (experiment_id, scale_id),

    CHECK (
        positive_count IS NULL OR
        negative_count IS NULL OR
        positive_count + negative_count <= shot_count
    ),

    CHECK (
        status <> 'COMPLETED' OR
        (
            observed_value IS NOT NULL AND
            standard_error IS NOT NULL AND
            measured_at IS NOT NULL
        )
    )
);

-- ------------------------------------------------------------
-- Extrapolation results
-- ------------------------------------------------------------

CREATE TABLE extrapolation_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    method extrapolation_method NOT NULL,

    intercept NUMERIC(16, 12) NOT NULL,

    baseline_value NUMERIC(14, 10) NOT NULL,

    baseline_error NUMERIC(14, 10) NOT NULL
        CHECK (baseline_error >= 0),

    mitigated_error NUMERIC(14, 10) NOT NULL
        CHECK (mitigated_error >= 0),

    residual_sum_squares NUMERIC(20, 12)
        CHECK (
            residual_sum_squares IS NULL OR
            residual_sum_squares >= 0
        ),

    coefficient_data JSONB NOT NULL DEFAULT '{}'::jsonb,

    estimated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, method)
);

-- ------------------------------------------------------------
-- Audit events
-- ------------------------------------------------------------

CREATE TABLE experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    event_type VARCHAR(60) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------

CREATE INDEX idx_experiments_status_created
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_circuit
    ON experiments(circuit_id, created_at DESC);

CREATE INDEX idx_scales_experiment_order
    ON noise_scales(experiment_id, scale_order);

CREATE INDEX idx_measurements_experiment_status
    ON measurements(experiment_id, status);

CREATE INDEX idx_results_experiment
    ON extrapolation_results(experiment_id);

CREATE INDEX idx_audit_experiment_time
    ON experiment_audit(experiment_id, created_at DESC);

CREATE INDEX idx_audit_details
    ON experiment_audit USING GIN(event_details);

-- ------------------------------------------------------------
-- Audit trigger
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_experiment_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO experiment_audit (
            experiment_id,
            event_type,
            event_details
        )
        VALUES (
            NEW.experiment_id,
            'STATUS_CHANGED',
            jsonb_build_object(
                'previous_status', OLD.status,
                'new_status', NEW.status
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_status_audit
AFTER UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION record_experiment_status_change();

-- ------------------------------------------------------------
-- Measurement integrity trigger
--
-- A measurement cannot consume more shots than the experiment
-- permits. The lock prevents concurrent overspending.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_measurement_budget()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_maximum BIGINT;
    v_consumed BIGINT;
BEGIN
    IF NEW.status <> 'COMPLETED' THEN
        RETURN NEW;
    END IF;

    SELECT maximum_shots
    INTO v_maximum
    FROM experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment % does not exist',
            NEW.experiment_id;
    END IF;

    SELECT COALESCE(SUM(shot_count), 0)
    INTO v_consumed
    FROM measurements
    WHERE experiment_id = NEW.experiment_id
      AND status = 'COMPLETED'
      AND measurement_id <> COALESCE(NEW.measurement_id, -1);

    IF v_consumed + NEW.shot_count > v_maximum THEN
        RAISE EXCEPTION
            'Shot budget exceeded: consumed %, requested %, maximum %',
            v_consumed,
            NEW.shot_count,
            v_maximum;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_measurement_budget
BEFORE INSERT OR UPDATE ON measurements
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_budget();

-- ------------------------------------------------------------
-- Measurement aggregation view
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW measurement_summary AS
SELECT
    e.experiment_id,
    e.experiment_name,
    ns.scale_factor,
    ns.scale_order,
    COUNT(m.measurement_id) AS measurement_records,
    SUM(
        CASE WHEN m.status = 'COMPLETED'
             THEN m.shot_count ELSE 0 END
    ) AS completed_shots,
    AVG(m.observed_value) AS average_observable,
    AVG(m.standard_error) AS average_standard_error
FROM experiments e
JOIN noise_scales ns
    ON ns.experiment_id = e.experiment_id
LEFT JOIN measurements m
    ON m.experiment_id = e.experiment_id
   AND m.scale_id = ns.scale_id
GROUP BY
    e.experiment_id,
    e.experiment_name,
    ns.scale_factor,
    ns.scale_order;

-- ------------------------------------------------------------
-- Eligibility determination
--
-- A completed experiment requires:
-- 1. Completed status.
-- 2. Sufficient completed measurement scales.
-- 3. Valid scale diversity.
-- 4. A completed measurement at every configured scale.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_experiment_eligible(
    p_experiment_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_method extrapolation_method;
    v_scale_count BIGINT;
    v_completed_count BIGINT;
    v_distinct_count BIGINT;
    v_status experiment_status;
BEGIN
    SELECT method, status
    INTO v_method, v_status
    FROM experiments
    WHERE experiment_id = p_experiment_id;

    IF NOT FOUND OR v_status <> 'COMPLETED' THEN
        RETURN FALSE;
    END IF;

    SELECT
        COUNT(*),
        COUNT(*) FILTER (
            WHERE ns.status = 'COMPLETED'
        ),
        COUNT(DISTINCT ns.scale_factor)
    INTO
        v_scale_count,
        v_completed_count,
        v_distinct_count
    FROM noise_scales ns
    WHERE ns.experiment_id = p_experiment_id;

    IF v_method = 'RICHARDSON' THEN
        RETURN v_scale_count >= 2
            AND v_completed_count >= 2
            AND v_distinct_count >= 2;
    ELSIF v_method = 'LINEAR' THEN
        RETURN v_scale_count >= 2
            AND v_completed_count >= 2
            AND v_distinct_count >= 2;
    ELSE
        RETURN v_scale_count >= 3
            AND v_completed_count >= 3
            AND v_distinct_count >= 3;
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- Workflow transition procedure
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE transition_experiment(
    p_experiment_id BIGINT,
    p_new_status experiment_status
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current experiment_status;
BEGIN
    SELECT status
    INTO v_current
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown experiment %', p_experiment_id;
    END IF;

    IF v_current IN ('COMPLETED', 'CANCELLED', 'FAILED') THEN
        RAISE EXCEPTION
            'Terminal experiment state cannot transition from %',
            v_current;
    END IF;

    IF p_new_status = 'RUNNING'
       AND v_current <> 'CREATED' THEN
        RAISE EXCEPTION 'Only CREATED experiments can start';
    END IF;

    IF p_new_status = 'COMPLETED'
       AND v_current <> 'RUNNING' THEN
        RAISE EXCEPTION 'Only RUNNING experiments can complete';
    END IF;

    IF p_new_status = 'CANCELLED'
       AND v_current NOT IN ('CREATED', 'RUNNING') THEN
        RAISE EXCEPTION 'Invalid cancellation transition';
    END IF;

    IF p_new_status = 'FAILED'
       AND v_current <> 'RUNNING' THEN
        RAISE EXCEPTION 'Only RUNNING experiments can fail';
    END IF;

    IF p_new_status = 'COMPLETED'
       AND NOT is_experiment_eligible(p_experiment_id) THEN
        RAISE EXCEPTION 'Experiment is not eligible for completion';
    END IF;

    UPDATE experiments
    SET
        status = p_new_status,
        started_at = CASE
            WHEN p_new_status = 'RUNNING'
            THEN CURRENT_TIMESTAMP
            ELSE started_at
        END,
        completed_at = CASE
            WHEN p_new_status IN ('COMPLETED', 'FAILED', 'CANCELLED')
            THEN CURRENT_TIMESTAMP
            ELSE NULL
        END
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- ------------------------------------------------------------
-- Sample circuit
-- ------------------------------------------------------------

INSERT INTO circuits (
    circuit_name,
    description,
    qubit_count,
    gate_count,
    observable_name
)
VALUES (
    'Single-Qubit-Expectation',
    'Single-qubit circuit measuring a Pauli-Z expectation value.',
    1,
    5,
    'PAULI_Z'
);

-- ------------------------------------------------------------
-- Experiment records
-- ------------------------------------------------------------

INSERT INTO experiments (
    circuit_id,
    experiment_name,
    method,
    status,
    ideal_reference,
    requested_shots,
    maximum_shots
)
VALUES
(
    1,
    'ZNE-Quadratic-Demo',
    'QUADRATIC',
    'CREATED',
    0.85,
    80000,
    100000
),
(
    1,
    'ZNE-Linear-Demo',
    'LINEAR',
    'CREATED',
    0.85,
    40000,
    60000
),
(
    1,
    'ZNE-Richardson-Demo',
    'RICHARDSON',
    'CREATED',
    0.85,
    40000,
    60000
);

-- ------------------------------------------------------------
-- Configure noise scales
-- ------------------------------------------------------------

INSERT INTO noise_scales (
    experiment_id,
    scale_factor,
    scale_order,
    scaling_method
)
VALUES
(1, 1.0, 1, 'GATE_FOLDING'),
(1, 1.5, 2, 'GATE_FOLDING'),
(1, 2.0, 3, 'GATE_FOLDING'),
(1, 2.5, 4, 'GATE_FOLDING'),

(2, 1.0, 1, 'GATE_FOLDING'),
(2, 2.0, 2, 'GATE_FOLDING'),

(3, 1.0, 1, 'GATE_FOLDING'),
(3, 2.0, 2, 'GATE_FOLDING');

-- ------------------------------------------------------------
-- Start experiments
-- ------------------------------------------------------------

CALL transition_experiment(1, 'RUNNING');
CALL transition_experiment(2, 'RUNNING');
CALL transition_experiment(3, 'RUNNING');

-- ------------------------------------------------------------
-- Insert simulated observations
--
-- Model:
-- E(lambda) = 0.85 - 0.12*lambda - 0.025*lambda^2
--
-- These are deterministic illustrative observations.
-- ------------------------------------------------------------

INSERT INTO measurements (
    experiment_id,
    scale_id,
    observed_value,
    positive_count,
    negative_count,
    shot_count,
    standard_error,
    status,
    measured_at
)
VALUES
-- Quadratic experiment
(1, 1, 0.705, 17050, 2950, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP),
(1, 2, 0.61375, 16138, 3862, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP),
(1, 3, 0.510, 15100, 4900, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP),
(1, 4, 0.39375, 13938, 6062, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP),

-- Linear experiment
(2, 5, 0.705, 17050, 2950, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP),
(2, 6, 0.510, 15100, 4900, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP),

-- Richardson experiment
(3, 7, 0.705, 17050, 2950, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP),
(3, 8, 0.510, 15100, 4900, 20000, 0.005, 'COMPLETED', CURRENT_TIMESTAMP);

-- ------------------------------------------------------------
-- Persist extrapolation outputs
--
-- The application performs the numerical fit. SQL stores the
-- resulting estimates and makes them available for auditing.
-- ------------------------------------------------------------

INSERT INTO extrapolation_results (
    experiment_id,
    method,
    intercept,
    baseline_value,
    baseline_error,
    mitigated_error,
    residual_sum_squares,
    coefficient_data
)
VALUES
(
    1,
    'QUADRATIC',
    0.850000000000,
    0.705,
    0.145,
    0.000,
    0.000000000000,
    '{"c0": 0.85, "c1": -0.12, "c2": -0.025}'::jsonb
),
(
    2,
    'LINEAR',
    0.802500000000,
    0.705,
    0.145,
    0.0475,
    0.000000000000,
    '{"c0": 0.8025, "c1": -0.0975}'::jsonb
),
(
    3,
    'RICHARDSON',
    0.900000000000,
    0.705,
    0.145,
    0.050,
    NULL,
    '{"scales": [1.0, 2.0]}'::jsonb
);

-- ------------------------------------------------------------
-- Complete eligible experiments
-- ------------------------------------------------------------

CALL transition_experiment(1, 'COMPLETED');
CALL transition_experiment(2, 'COMPLETED');
CALL transition_experiment(3, 'COMPLETED');

-- ------------------------------------------------------------
-- Query 1: Experiment retrieval
-- ------------------------------------------------------------

SELECT
    e.experiment_id,
    e.experiment_name,
    c.circuit_name,
    e.method,
    e.status,
    e.ideal_reference,
    e.requested_shots,
    e.maximum_shots
FROM experiments e
JOIN circuits c
    ON c.circuit_id = e.circuit_id
ORDER BY e.experiment_id;

-- ------------------------------------------------------------
-- Query 2: Noise-scale measurement retrieval
-- ------------------------------------------------------------

SELECT
    experiment_name,
    scale_factor,
    average_observable,
    average_standard_error,
    completed_shots
FROM measurement_summary
ORDER BY experiment_id, scale_order;

-- ------------------------------------------------------------
-- Query 3: Measurement validation
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    ns.scale_factor,
    m.observed_value,
    m.standard_error,
    m.shot_count,
    CASE
        WHEN m.measurement_id IS NULL
            THEN 'MISSING_MEASUREMENT'
        WHEN m.status <> 'COMPLETED'
            THEN 'INCOMPLETE'
        WHEN m.observed_value NOT BETWEEN -1 AND 1
            THEN 'INVALID_OBSERVABLE'
        WHEN m.standard_error < 0
            THEN 'INVALID_UNCERTAINTY'
        ELSE 'VALID'
    END AS validation_status
FROM experiments e
JOIN noise_scales ns
    ON ns.experiment_id = e.experiment_id
LEFT JOIN measurements m
    ON m.experiment_id = e.experiment_id
   AND m.scale_id = ns.scale_id
ORDER BY e.experiment_id, ns.scale_order;

-- ------------------------------------------------------------
-- Query 4: Shot consumption aggregation
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    e.maximum_shots,
    COALESCE(SUM(
        CASE WHEN m.status = 'COMPLETED'
             THEN m.shot_count ELSE 0 END
    ), 0) AS consumed_shots,
    e.maximum_shots - COALESCE(SUM(
        CASE WHEN m.status = 'COMPLETED'
             THEN m.shot_count ELSE 0 END
    ), 0) AS remaining_shots
FROM experiments e
LEFT JOIN measurements m
    ON m.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_name,
    e.maximum_shots
ORDER BY e.experiment_id;

-- ------------------------------------------------------------
-- Query 5: Mitigation performance comparison
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    r.method,
    r.baseline_value,
    r.intercept AS mitigated_estimate,
    r.baseline_error,
    r.mitigated_error,
    CASE
        WHEN r.baseline_error = 0 THEN NULL
        ELSE ROUND(
            (
                1.0 - r.mitigated_error / r.baseline_error
            ) * 100.0,
            2
        )
    END AS error_reduction_percent
FROM extrapolation_results r
JOIN experiments e
    ON e.experiment_id = r.experiment_id
ORDER BY r.mitigated_error;

-- ------------------------------------------------------------
-- Query 6: Eligibility report
-- ------------------------------------------------------------

SELECT
    experiment_id,
    experiment_name,
    method,
    status,
    is_experiment_eligible(experiment_id) AS eligible
FROM experiments
ORDER BY experiment_id;

-- ------------------------------------------------------------
-- Query 7: Window-based ranking
-- ------------------------------------------------------------

WITH ranked_results AS (
    SELECT
        e.experiment_name,
        r.method,
        r.mitigated_error,
        RANK() OVER (
            PARTITION BY e.circuit_id
            ORDER BY r.mitigated_error ASC
        ) AS error_rank
    FROM extrapolation_results r
    JOIN experiments e
        ON e.experiment_id = r.experiment_id
)
SELECT *
FROM ranked_results
ORDER BY error_rank, experiment_name;

-- ------------------------------------------------------------
-- Query 8: Audit history
-- ------------------------------------------------------------

SELECT
    experiment_id,
    event_type,
    event_details,
    created_at
FROM experiment_audit
ORDER BY created_at, audit_id;

-- ------------------------------------------------------------
-- Query 9: Detect incomplete experiment configurations
-- ------------------------------------------------------------

SELECT
    e.experiment_id,
    e.experiment_name,
    COUNT(ns.scale_id) AS configured_scales,
    COUNT(m.measurement_id) FILTER (
        WHERE m.status = 'COMPLETED'
    ) AS completed_measurements
FROM experiments e
LEFT JOIN noise_scales ns
    ON ns.experiment_id = e.experiment_id
LEFT JOIN measurements m
    ON m.experiment_id = e.experiment_id
   AND m.scale_id = ns.scale_id
GROUP BY e.experiment_id, e.experiment_name
HAVING COUNT(m.measurement_id) FILTER (
    WHERE m.status = 'COMPLETED'
) < COUNT(ns.scale_id);

-- ------------------------------------------------------------
-- Query 10: Experiment performance dashboard
-- ------------------------------------------------------------

SELECT
    e.method,
    COUNT(*) AS experiments,
    AVG(r.baseline_error) AS average_baseline_error,
    AVG(r.mitigated_error) AS average_mitigated_error,
    MIN(r.mitigated_error) AS best_mitigated_error,
    MAX(r.mitigated_error) AS worst_mitigated_error
FROM experiments e
JOIN extrapolation_results r
    ON r.experiment_id = e.experiment_id
GROUP BY e.method
ORDER BY average_mitigated_error;

COMMIT;

-- ------------------------------------------------------------
-- Example failure tests (execute separately in a transaction
-- that is rolled back):
--
-- 1. Invalid scale:
--    INSERT INTO noise_scales (...)
--    VALUES (..., 0.5, ...);
--
-- 2. Invalid observable:
--    INSERT INTO measurements (...)
--    VALUES (..., 1.5, ...);
--
-- 3. Exceed shot budget:
--    Insert a completed measurement exceeding maximum_shots.
--
-- 4. Invalid lifecycle transition:
--    CALL transition_experiment(1, 'RUNNING');
--
-- 5. Ineligible completion:
--    Attempt completion before all required scales are measured.
--
-- Database integrity controls are not a substitute for
-- authorization. Production deployments should use restricted
-- roles, schema privileges, connection encryption and audit access.
-- ------------------------------------------------------------
